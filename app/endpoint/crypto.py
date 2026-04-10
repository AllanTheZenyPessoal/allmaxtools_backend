import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, cast
import json

import httpx
from fastapi import HTTPException, WebSocket
from sqlalchemy.orm import Session
import websockets

from database import db_models, base_models
from database.database import get_session_local


class WebSocketConnectionManager:
    def __init__(self) -> None:
        self._connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)

    async def broadcast(self, payload: Dict) -> None:
        async with self._lock:
            connections = list(self._connections)

        for connection in connections:
            try:
                await connection.send_json(payload)
            except Exception:
                await self.disconnect(connection)


class BinanceMarketClient:
    BASE_URL = "https://api.binance.com/api/v3"
    BASE_WS_URL = "wss://stream.binance.com:9443"

    async def fetch_ticker_24h(self, pair: str) -> Dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{self.BASE_URL}/ticker/24hr", params={"symbol": pair})
            response.raise_for_status()
            data = response.json()

        return {
            "pair": pair,
            "symbol": pair.replace("USDT", ""),
            "price_usdt": float(data["lastPrice"]),
            "price_change_percent_24h": float(data["priceChangePercent"]),
            "high_24h": float(data["highPrice"]),
            "low_24h": float(data["lowPrice"]),
            "volume_quote_24h": float(data["quoteVolume"]),
        }

    async def connect_trade_stream(self, pairs: List[str]):
        streams = "/".join([f"{pair.lower()}@trade" for pair in pairs])
        stream_url = f"{self.BASE_WS_URL}/stream?streams={streams}"
        return await websockets.connect(stream_url, ping_interval=20, ping_timeout=20)

    @staticmethod
    def parse_trade_message(raw_message: str) -> Optional[Dict]:
        message = json.loads(raw_message)
        data = message.get("data") if isinstance(message, dict) else None
        if not isinstance(data, dict):
            return None

        pair = data.get("s")
        if not pair:
            return None

        price = data.get("p")
        quantity = data.get("q")

        if price is None or quantity is None:
            return None

        price_float = float(price)
        qty_float = float(quantity)

        return {
            "pair": pair,
            "symbol": pair.replace("USDT", ""),
            "price_usdt": price_float,
            "price_change_percent_24h": None,
            "high_24h": None,
            "low_24h": None,
            # Trade stream does not include 24h quote volume; store trade notional as best-effort.
            "volume_quote_24h": price_float * qty_float,
        }


class CryptoCollectorService:
    def __init__(self, websocket_manager: WebSocketConnectionManager) -> None:
        self._websocket_manager = websocket_manager
        self._market_client = BinanceMarketClient()
        self._pairs = ["BTCUSDT", "ETHUSDT"]
        self._interval_seconds = 2
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._state_lock = asyncio.Lock()

    async def play(self, db: Session, interval_seconds: int) -> Dict:
        if interval_seconds < 1:
            raise HTTPException(status_code=400, detail="interval_seconds must be >= 1")

        async with self._state_lock:
            if self._is_running:
                return {"status": "already_running", "interval_seconds": self._interval_seconds}

            self._interval_seconds = interval_seconds
            self._is_running = True
            self._task = asyncio.create_task(self._run_loop())

            now = datetime.utcnow()
            state = self._get_or_create_state(db)
            setattr(state, "is_running", True)
            setattr(state, "interval_seconds", interval_seconds)
            setattr(state, "started_at", now)
            setattr(state, "updated_at", now)
            db.commit()

        return {
            "status": "running",
            "interval_seconds": self._interval_seconds,
            "started_at": datetime.utcnow().isoformat(),
        }

    async def stop(self, db: Session) -> Dict:
        async with self._state_lock:
            if not self._is_running:
                return {"status": "already_stopped"}

            self._is_running = False
            task = self._task
            self._task = None

            now = datetime.utcnow()
            state = self._get_or_create_state(db)
            setattr(state, "is_running", False)
            setattr(state, "stopped_at", now)
            setattr(state, "updated_at", now)
            db.commit()

        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        return {"status": "stopped", "stopped_at": datetime.utcnow().isoformat()}

    def status(self, db: Session) -> base_models.CryptoCollectorStatusResponse:
        state = self._get_or_create_state(db)
        return base_models.CryptoCollectorStatusResponse(
            is_running=bool(self._is_running),
            interval_seconds=cast(int, getattr(state, "interval_seconds")),
            started_at=cast(Optional[datetime], getattr(state, "started_at")),
            stopped_at=cast(Optional[datetime], getattr(state, "stopped_at")),
        )

    def latest(self, db: Session) -> base_models.CryptoLatestResponse:
        btc = (
            db.query(db_models.CryptoPriceSnapshot)
            .filter(db_models.CryptoPriceSnapshot.symbol == "BTC")
            .order_by(db_models.CryptoPriceSnapshot.created_at.desc())
            .first()
        )
        eth = (
            db.query(db_models.CryptoPriceSnapshot)
            .filter(db_models.CryptoPriceSnapshot.symbol == "ETH")
            .order_by(db_models.CryptoPriceSnapshot.created_at.desc())
            .first()
        )

        return base_models.CryptoLatestResponse(
            btc=self._to_ticker_response(btc),
            eth=self._to_ticker_response(eth),
        )

    def history(self, db: Session, symbol: str, limit: int) -> base_models.CryptoHistoryResponse:
        normalized = symbol.upper()
        if normalized not in ["BTC", "ETH"]:
            raise HTTPException(status_code=400, detail="symbol must be BTC or ETH")

        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")

        rows = (
            db.query(db_models.CryptoPriceSnapshot)
            .filter(db_models.CryptoPriceSnapshot.symbol == normalized)
            .order_by(db_models.CryptoPriceSnapshot.created_at.desc())
            .limit(limit)
            .all()
        )

        rows = list(reversed(rows))
        items: List[base_models.CryptoTickerResponse] = []
        for item in rows:
            parsed = self._to_ticker_response(item)
            if parsed is not None:
                items.append(parsed)

        return base_models.CryptoHistoryResponse(symbol=normalized, items=items)

    async def _run_loop(self) -> None:
        SessionLocal = get_session_local()
        print("[Collector] Loop started", flush=True)
        while self._is_running:
            try:
                print("[Collector] Connecting to Binance stream...", flush=True)
                async with websockets.connect(
                    f"{self._market_client.BASE_WS_URL}/stream?streams="
                    + "/".join([f"{p.lower()}@trade" for p in self._pairs]),
                    ping_interval=20,
                    ping_timeout=20,
                ) as ws:
                    print("[Collector] Connected to Binance stream", flush=True)
                    while self._is_running:
                        try:
                            raw_message = await asyncio.wait_for(ws.recv(), timeout=60)
                        except asyncio.TimeoutError:
                            print("[Collector] recv() timeout — reconnecting", flush=True)
                            break

                        ticker = self._market_client.parse_trade_message(cast(str, raw_message))

                        if not ticker:
                            continue

                        if ticker["symbol"] not in ["BTC", "ETH"]:
                            continue

                        db = SessionLocal()
                        try:
                            snapshot = db_models.CryptoPriceSnapshot(
                                symbol=ticker["symbol"],
                                pair=ticker["pair"],
                                price_usdt=ticker["price_usdt"],
                                price_change_percent_24h=ticker["price_change_percent_24h"],
                                high_24h=ticker["high_24h"],
                                low_24h=ticker["low_24h"],
                                volume_quote_24h=ticker["volume_quote_24h"],
                            )
                            db.add(snapshot)

                            state = self._get_or_create_state(db)
                            setattr(state, "updated_at", datetime.utcnow())
                            db.commit()

                            print(f"[Collector] Saved {ticker['symbol']} @ {ticker['price_usdt']}", flush=True)

                            payload = {
                                "type": "price_update",
                                "data": [
                                    {
                                        "symbol": snapshot.symbol,
                                        "pair": snapshot.pair,
                                        "price_usdt": snapshot.price_usdt,
                                        "price_change_percent_24h": snapshot.price_change_percent_24h,
                                        "high_24h": snapshot.high_24h,
                                        "low_24h": snapshot.low_24h,
                                        "volume_quote_24h": snapshot.volume_quote_24h,
                                        "created_at": snapshot.created_at.isoformat() if snapshot.created_at else datetime.utcnow().isoformat(),
                                    }
                                ],
                            }
                            await self._websocket_manager.broadcast(payload)
                        except Exception as db_err:
                            print(f"[Collector] DB error: {db_err}", flush=True)
                            db.rollback()
                        finally:
                            db.close()
            except asyncio.CancelledError:
                print("[Collector] Loop cancelled", flush=True)
                raise
            except Exception as e:
                print(f"[Collector] Stream error: {type(e).__name__}: {e} — falling back to REST", flush=True)
                await self._run_rest_polling_once(SessionLocal)
                await asyncio.sleep(max(self._interval_seconds, 2))

    async def _run_rest_polling_once(self, SessionLocal) -> None:
        print("[Collector] REST fallback polling...", flush=True)
        db = SessionLocal()
        try:
            snapshots = []
            for pair in self._pairs:
                ticker = await self._market_client.fetch_ticker_24h(pair)
                snapshot = db_models.CryptoPriceSnapshot(
                    symbol=ticker["symbol"],
                    pair=ticker["pair"],
                    price_usdt=ticker["price_usdt"],
                    price_change_percent_24h=ticker["price_change_percent_24h"],
                    high_24h=ticker["high_24h"],
                    low_24h=ticker["low_24h"],
                    volume_quote_24h=ticker["volume_quote_24h"],
                )
                db.add(snapshot)
                snapshots.append(snapshot)

            state = self._get_or_create_state(db)
            setattr(state, "updated_at", datetime.utcnow())
            db.commit()

            payload = {
                "type": "price_update",
                "data": [
                    {
                        "symbol": s.symbol,
                        "pair": s.pair,
                        "price_usdt": s.price_usdt,
                        "price_change_percent_24h": s.price_change_percent_24h,
                        "high_24h": s.high_24h,
                        "low_24h": s.low_24h,
                        "volume_quote_24h": s.volume_quote_24h,
                        "created_at": s.created_at.isoformat() if s.created_at else datetime.utcnow().isoformat(),
                    }
                    for s in snapshots
                ],
            }
            await self._websocket_manager.broadcast(payload)
        except httpx.HTTPError as e:
            print(f"[Collector] REST HTTP error: {e}", flush=True)
            db.rollback()
        except Exception as e:
            print(f"[Collector] REST unexpected error: {type(e).__name__}: {e}", flush=True)
            db.rollback()
        finally:
            db.close()

    @staticmethod
    def _get_or_create_state(db: Session) -> db_models.CryptoCollectorState:
        state = db.query(db_models.CryptoCollectorState).first()
        if state is None:
            state = db_models.CryptoCollectorState(is_running=False, interval_seconds=2)
            db.add(state)
            db.flush()
        return state

    @staticmethod
    def _to_ticker_response(row: Optional[db_models.CryptoPriceSnapshot]) -> Optional[base_models.CryptoTickerResponse]:
        if row is None:
            return None

        row_any = cast(Any, row)

        return base_models.CryptoTickerResponse(
            symbol=cast(str, row_any.symbol),
            pair=cast(str, row_any.pair),
            price_usdt=cast(float, row_any.price_usdt),
            price_change_percent_24h=cast(Optional[float], row_any.price_change_percent_24h),
            high_24h=cast(Optional[float], row_any.high_24h),
            low_24h=cast(Optional[float], row_any.low_24h),
            volume_quote_24h=cast(Optional[float], row_any.volume_quote_24h),
            created_at=cast(datetime, row_any.created_at),
        )


websocket_manager = WebSocketConnectionManager()
crypto_collector_service = CryptoCollectorService(websocket_manager)
