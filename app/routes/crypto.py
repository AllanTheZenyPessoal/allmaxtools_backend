import traceback
from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from database import base_models, db_models
from dependencies import get_db
from endpoint.crypto import crypto_collector_service, websocket_manager
from services.binance_client import BinanceClient
from services.encryption import decrypt
from token_utils.apikey_generator import verify_token

router = APIRouter(tags=["crypto"], prefix="/crypto")


def _assert_mode_matches_token(token: dict, mode: str) -> None:
    """Raise 403 when the token's trade_mode claim disagrees with the request mode."""
    token_mode = token.get("trade_mode", "live")
    if token_mode != mode:
        raise HTTPException(
            status_code=403,
            detail=f"token is bound to '{token_mode}' mode; request uses '{mode}' mode",
        )


def _get_binance_client(db: Session, user_id: int) -> Optional[BinanceClient]:
    """Return a BinanceClient if the user has stored credentials, else None."""
    creds = (
        db.query(db_models.BinanceCredentials)
        .filter(db_models.BinanceCredentials.user_id == user_id)
        .first()
    )
    if creds is None:
        return None
    return BinanceClient(
        api_key=decrypt(creds.api_key_encrypted),
        api_secret=decrypt(creds.api_secret_encrypted),
        testnet=bool(creds.testnet),
    )


@router.post("/play", summary="Iniciar coletor de preços", include_in_schema=False)
async def play_collector(
    payload: base_models.CryptoCollectorPlayRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    return await crypto_collector_service.play(db, payload.interval_seconds)


@router.post("/stop", summary="Parar coletor de preços", include_in_schema=False)
async def stop_collector(
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    return await crypto_collector_service.stop(db)


@router.get("/status", response_model=base_models.CryptoCollectorStatusResponse, include_in_schema=False)
async def collector_status(db: Session = Depends(get_db)):
    return crypto_collector_service.status(db)


@router.get(
    "/prices/latest",
    response_model=base_models.CryptoLatestResponse,
    summary="Último preço de BTC e ETH",
    description="Retorna o preço mais recente coletado para BTC e ETH.",
)
async def latest_prices(db: Session = Depends(get_db)):
    return crypto_collector_service.latest(db)


@router.post(
    "/prices/history/range",
    response_model=base_models.CryptoHistoryByDateResponse,
    summary="Histórico de preços por intervalo de datas",
    description="Retorna todos os preços registrados de um símbolo (BTC ou ETH) dentro do intervalo informado.",
)
async def price_history_by_date_range(
    payload: base_models.CryptoPriceHistoryRangeRequest,
    db: Session = Depends(get_db),
):
    return crypto_collector_service.history_by_date_range(db, payload.symbol, payload.start_date, payload.end_date)


@router.get("/prices/history/{symbol}", response_model=base_models.CryptoHistoryResponse, include_in_schema=False)
async def price_history(symbol: str, limit: int = 100, db: Session = Depends(get_db)):
    return crypto_collector_service.history(db, symbol, limit)


@router.post(
    "/trades/buy",
    response_model=base_models.CryptoTradeResponse,
    summary="Registrar ordem de compra",
    description=(
        "Registra uma compra de criptomoeda. "
        "Se o usuário tiver credenciais Binance cadastradas e `mode=live`, executa uma ordem "
        "MARKET real na Binance antes de atualizar o saldo interno. "
        "Use `?mode=paper` para operar em modo 100% simulado (sem tocar na Binance)."
    ),
)
async def create_buy_trade(
    payload: base_models.CryptoTradeCreateRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
    mode: str = Query("live", pattern="^(paper|live)$", description="Modo de operação: `live` (real) ou `paper` (simulado)."),
):
    _assert_mode_matches_token(token, mode)

    binance_order_id: Optional[str] = None

    if mode == "live":
        client = _get_binance_client(db, token["id_user"])
        if client is not None:
            if payload.quantity is None:
                raise HTTPException(status_code=400, detail="quantity is required for Binance live orders.")
            fill = await client.market_order("BUY", payload.symbol, payload.quantity)
            binance_order_id = fill["order_id"]
            payload = payload.model_copy(update={
                "unit_price_usdt": fill["avg_price"],
                "quantity": fill["executed_qty"],
            })

    return crypto_collector_service.register_trade(
        db, "buy", payload, token["id_user"], mode, binance_order_id=binance_order_id
    )


@router.post(
    "/trades/sell",
    response_model=base_models.CryptoTradeResponse,
    summary="Registrar ordem de venda",
    description=(
        "Registra uma venda de criptomoeda. "
        "Se o usuário tiver credenciais Binance cadastradas e `mode=live`, executa uma ordem "
        "MARKET real na Binance antes de atualizar o saldo interno. "
        "Use `?mode=paper` para operar em modo 100% simulado (sem tocar na Binance)."
    ),
)
async def create_sell_trade(
    payload: base_models.CryptoTradeCreateRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
    mode: str = Query("live", pattern="^(paper|live)$", description="Modo de operação: `live` (real) ou `paper` (simulado)."),
):
    _assert_mode_matches_token(token, mode)

    binance_order_id: Optional[str] = None

    if mode == "live":
        client = _get_binance_client(db, token["id_user"])
        if client is not None:
            if payload.quantity is None:
                raise HTTPException(status_code=400, detail="quantity is required for Binance live orders.")
            fill = await client.market_order("SELL", payload.symbol, payload.quantity)
            binance_order_id = fill["order_id"]
            payload = payload.model_copy(update={
                "unit_price_usdt": fill["avg_price"],
                "quantity": fill["executed_qty"],
            })

    return crypto_collector_service.register_trade(
        db, "sell", payload, token["id_user"], mode, binance_order_id=binance_order_id
    )


@router.post(
    "/trades/history",
    response_model=base_models.CryptoTradeHistoryResponse,
    summary="Histórico de trades do usuário",
    description=(
        "Retorna os trades do usuário autenticado dentro do intervalo de datas. "
        "`symbol` e `trade_type` são filtros opcionais."
    ),
)
async def trades_history(
    payload: base_models.CryptoTradeHistoryRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
    mode: str = Query("live", pattern="^(paper|live)$", description="Modo de operação: `live` (real) ou `paper` (simulado)."),
):
    _assert_mode_matches_token(token, mode)
    try:
        return crypto_collector_service.trade_history(
            db,
            payload.start_date,
            payload.end_date,
            token["id_user"],
            payload.symbol,
            payload.trade_type,
            mode,
        )
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))


@router.websocket("/ws/prices")
async def prices_websocket(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception:
        await websocket_manager.disconnect(websocket)
