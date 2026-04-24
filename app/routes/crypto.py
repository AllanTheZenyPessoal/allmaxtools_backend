from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from database import base_models
from dependencies import get_db
from endpoint.crypto import crypto_collector_service, websocket_manager
from token_utils.apikey_generator import verify_token

router = APIRouter(tags=["crypto"], prefix="/crypto")


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
):
    return crypto_collector_service.register_trade(db, "buy", payload, token["id_user"])


@router.post("/trades/sell", response_model=base_models.CryptoTradeResponse)
async def create_sell_trade(
    payload: base_models.CryptoTradeCreateRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    return crypto_collector_service.register_trade(db, "sell", payload, token["id_user"])


@router.post("/trades/history", response_model=base_models.CryptoTradeHistoryResponse)
async def trades_history(
    payload: base_models.CryptoTradeHistoryRequest,
    token: Annotated[dict, Depends(verify_token)],
    db: Session = Depends(get_db),
):
    return crypto_collector_service.trade_history(db, payload.start_date, payload.end_date, token["id_user"], payload.symbol, payload.trade_type)


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
