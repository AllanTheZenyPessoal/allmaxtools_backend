import traceback
from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from database import base_models
from dependencies import get_db
from endpoint.crypto import crypto_collector_service, websocket_manager
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


@router.post("/play")
async def play_collector(
    payload: base_models.CryptoCollectorPlayRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    return await crypto_collector_service.play(db, payload.interval_seconds)


@router.post("/stop")
async def stop_collector(
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    return await crypto_collector_service.stop(db)


@router.get("/status", response_model=base_models.CryptoCollectorStatusResponse)
async def collector_status(db: Session = Depends(get_db)):
    return crypto_collector_service.status(db)


@router.get("/prices/latest", response_model=base_models.CryptoLatestResponse)
async def latest_prices(db: Session = Depends(get_db)):
    return crypto_collector_service.latest(db)


@router.post("/prices/history/range", response_model=base_models.CryptoHistoryByDateResponse)
async def price_history_by_date_range(
    payload: base_models.CryptoPriceHistoryRangeRequest,
    db: Session = Depends(get_db),
):
    return crypto_collector_service.history_by_date_range(db, payload.symbol, payload.start_date, payload.end_date)


@router.get("/prices/history/{symbol}", response_model=base_models.CryptoHistoryResponse)
async def price_history(symbol: str, limit: int = 100, db: Session = Depends(get_db)):
    return crypto_collector_service.history(db, symbol, limit)


@router.post("/trades/buy", response_model=base_models.CryptoTradeResponse)
async def create_buy_trade(
    payload: base_models.CryptoTradeCreateRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
    mode: str = Query("live", pattern="^(paper|live)$"),
):
    _assert_mode_matches_token(token, mode)
    return crypto_collector_service.register_trade(db, "buy", payload, token["id_user"], mode)


@router.post("/trades/sell", response_model=base_models.CryptoTradeResponse)
async def create_sell_trade(
    payload: base_models.CryptoTradeCreateRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
    mode: str = Query("live", pattern="^(paper|live)$"),
):
    _assert_mode_matches_token(token, mode)
    return crypto_collector_service.register_trade(db, "sell", payload, token["id_user"], mode)


@router.post("/trades/history", response_model=base_models.CryptoTradeHistoryResponse)
async def trades_history(
    payload: base_models.CryptoTradeHistoryRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
    mode: str = Query("live", pattern="^(paper|live)$"),
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
