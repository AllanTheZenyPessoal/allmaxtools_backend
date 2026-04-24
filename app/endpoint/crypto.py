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
    # Binance blocks US-hosted servers (HTTP 451). Using Kraken (WS) + CoinGecko (REST).
    KRAKEN_WS_URL = "wss://ws.kraken.com/v2"
    COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"

    _KRAKEN_SYMBOL_MAP: Dict[str, Dict[str, str]] = {
        "BTC/USD": {"symbol": "BTC", "pair": "BTCUSDT"},
        "ETH/USD": {"symbol": "ETH", "pair": "ETHUSDT"},
    }
    _PAIR_TO_COINGECKO: Dict[str, str] = {
        "BTCUSDT": "bitcoin",
        "ETHUSDT": "ethereum",
    }

    async def fetch_ticker_24h(self, pair: str) -> Dict:
        cg_id = self._PAIR_TO_COINGECKO.get(pair)
        if not cg_id:
            raise ValueError(f"Unknown pair: {pair}")
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                self.COINGECKO_MARKETS_URL,
                params={"vs_currency": "usd", "ids": cg_id},
            )
            response.raise_for_status()
            data = response.json()
        if not data:
            raise ValueError(f"No data returned for {pair}")
        item = data[0]
        return {
            "pair": pair,
            "symbol": pair.replace("USDT", ""),
            "price_usdt": float(item["current_price"]),
            "price_change_percent_24h": float(item.get("price_change_percentage_24h") or 0),
            "high_24h": float(item["high_24h"]) if item.get("high_24h") else None,
            "low_24h": float(item["low_24h"]) if item.get("low_24h") else None,
            "volume_quote_24h": float(item["total_volume"]) if item.get("total_volume") else None,
        }

    async def connect_trade_stream(self, pairs: List[str]):
        kraken_symbols = [p.replace("USDT", "/USD") for p in pairs]
        ws = await websockets.connect(self.KRAKEN_WS_URL, ping_interval=20, ping_timeout=20)
        await ws.send(json.dumps({
            "method": "subscribe",
            "params": {"channel": "ticker", "symbol": kraken_symbols},
        }))
        return ws

    @classmethod
    def parse_trade_message(cls, raw_message: str) -> Optional[List[Dict]]:
        try:
            message = json.loads(raw_message)
        except Exception:
            return None
        if not isinstance(message, dict):
            return None
        if message.get("channel") != "ticker":
            return None
        if message.get("type") not in ("snapshot", "update"):
            return None
        data = message.get("data")
        if not isinstance(data, list):
            return None
        results = []
        for item in data:
            info = cls._KRAKEN_SYMBOL_MAP.get(item.get("symbol", ""))
            if not info:
                continue
            price = item.get("last")
            if price is None:
                continue
            results.append({
                "pair": info["pair"],
                "symbol": info["symbol"],
                "price_usdt": float(price),
                "price_change_percent_24h": float(item.get("change_pct") or 0),
                "high_24h": float(item["high"]) if item.get("high") else None,
                "low_24h": float(item["low"]) if item.get("low") else None,
                "volume_quote_24h": float(item["volume"]) if item.get("volume") else None,
            })
        return results if results else None


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

    def history_by_date_range(
        self,
        db: Session,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
    ) -> base_models.CryptoHistoryByDateResponse:
        normalized = symbol.upper()
        if normalized not in ["BTC", "ETH"]:
            raise HTTPException(status_code=400, detail="symbol must be BTC or ETH")

        if end_date < start_date:
            raise HTTPException(status_code=400, detail="end_date must be greater than or equal to start_date")

        rows = (
            db.query(db_models.CryptoPriceSnapshot)
            .filter(db_models.CryptoPriceSnapshot.symbol == normalized)
            .filter(db_models.CryptoPriceSnapshot.created_at >= start_date)
            .filter(db_models.CryptoPriceSnapshot.created_at <= end_date)
            .order_by(db_models.CryptoPriceSnapshot.created_at.asc())
            .all()
        )

        items: List[base_models.CryptoTickerResponse] = []
        for item in rows:
            parsed = self._to_ticker_response(item)
            if parsed is not None:
                items.append(parsed)

        return base_models.CryptoHistoryByDateResponse(
            symbol=normalized,
            start_date=start_date,
            end_date=end_date,
            items=items,
        )

    def register_trade(
        self,
        db: Session,
        trade_type: str,
        payload: base_models.CryptoTradeCreateRequest,
        user_id: int,
    ) -> base_models.CryptoTradeResponse:
        normalized_type = trade_type.lower()
        if normalized_type not in ["buy", "sell"]:
            raise HTTPException(status_code=400, detail="trade_type must be buy or sell")

        normalized_symbol = payload.symbol.upper()
        if normalized_symbol not in ["BTC", "ETH"]:
            raise HTTPException(status_code=400, detail="symbol must be BTC or ETH")

        if payload.quantity <= 0:
            raise HTTPException(status_code=400, detail="quantity must be greater than 0")

        if payload.unit_price_usdt <= 0:
            raise HTTPException(status_code=400, detail="unit_price_usdt must be greater than 0")

        executed_at = payload.executed_at or datetime.utcnow()
        total_usdt = payload.quantity * payload.unit_price_usdt

        account = self._get_or_create_account(db, user_id)
        holding = self._get_or_create_holding(db, user_id, normalized_symbol)

        if normalized_type == "buy":
            if account.balance_usdt < total_usdt:
                raise HTTPException(status_code=400, detail="insufficient saldo for this buy order")

            previous_qty = holding.quantity or 0
            new_qty = previous_qty + payload.quantity
            total_cost_basis = (holding.avg_cost_usdt or 0) * previous_qty + total_usdt

            holding.quantity = new_qty
            holding.avg_cost_usdt = total_cost_basis / new_qty if new_qty > 0 else 0
            holding.current_value_usdt = new_qty * payload.unit_price_usdt
            account.balance_usdt -= total_usdt
        else:
            available_qty = holding.quantity or 0
            if available_qty < payload.quantity:
                raise HTTPException(status_code=400, detail="insufficient coin saldo for this sell order")

            new_qty = available_qty - payload.quantity
            holding.quantity = new_qty
            holding.avg_cost_usdt = holding.avg_cost_usdt if new_qty > 0 else 0
            holding.current_value_usdt = new_qty * payload.unit_price_usdt
            account.balance_usdt += total_usdt

        trade = db_models.CryptoTradeHistory(
            user_id=user_id,
            trade_type=normalized_type,
            symbol=normalized_symbol,
            quantity=payload.quantity,
            unit_price_usdt=payload.unit_price_usdt,
            total_usdt=total_usdt,
            executed_at=executed_at,
        )
        db.add(trade)
        db.flush()

        self._append_account_transaction(
            db,
            user_id=user_id,
            transaction_type=normalized_type,
            amount_usdt=total_usdt,
            symbol=normalized_symbol,
            quantity=payload.quantity,
            description=f"{normalized_type.upper()} {normalized_symbol}",
            reference_trade_id=trade.id_trade,
        )

        db.commit()
        db.refresh(trade)
        db.refresh(account)
        db.refresh(holding)

        return self._to_trade_response(trade, account, holding)

    def trade_history(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        user_id: int,
        symbol: Optional[str] = None,
        trade_type: Optional[str] = None,
    ) -> base_models.CryptoTradeHistoryResponse:
        if end_date < start_date:
            raise HTTPException(status_code=400, detail="end_date must be greater than or equal to start_date")

        query = (
            db.query(db_models.CryptoTradeHistory)
            .filter(db_models.CryptoTradeHistory.user_id == user_id)
            .filter(db_models.CryptoTradeHistory.executed_at >= start_date)
            .filter(db_models.CryptoTradeHistory.executed_at <= end_date)
        )

        normalized_symbol = None
        if symbol:
            normalized_symbol = symbol.upper()
            if normalized_symbol not in ["BTC", "ETH"]:
                raise HTTPException(status_code=400, detail="symbol must be BTC or ETH")
            query = query.filter(db_models.CryptoTradeHistory.symbol == normalized_symbol)

        normalized_trade_type = None
        if trade_type:
            normalized_trade_type = trade_type.lower()
            if normalized_trade_type not in ["buy", "sell"]:
                raise HTTPException(status_code=400, detail="trade_type must be buy or sell")
            query = query.filter(db_models.CryptoTradeHistory.trade_type == normalized_trade_type)

        rows = query.order_by(db_models.CryptoTradeHistory.executed_at.asc()).all()
        items = [self._to_trade_response(row) for row in rows]

        return base_models.CryptoTradeHistoryResponse(
            start_date=start_date,
            end_date=end_date,
            symbol=normalized_symbol,
            trade_type=normalized_trade_type,
            items=items,
        )

    def get_account_balance(self, db: Session, user_id: int) -> base_models.UserAccountResponse:
        account = self._get_or_create_account(db, user_id)
        db.commit()
        db.refresh(account)
        return self._to_account_response(account)

    def deposit_balance(
        self,
        db: Session,
        acting_user: Dict[str, Any],
        payload: base_models.AccountMutationRequest,
    ) -> base_models.UserAccountResponse:
        user_id = self._resolve_target_user_id(acting_user, payload.user_id)
        if payload.amount_usdt <= 0:
            raise HTTPException(status_code=400, detail="amount_usdt must be greater than 0")

        account = self._get_or_create_account(db, user_id)
        account.balance_usdt += payload.amount_usdt
        account.total_deposited_usdt += payload.amount_usdt

        self._append_account_transaction(
            db,
            user_id=user_id,
            transaction_type="deposit",
            amount_usdt=payload.amount_usdt,
            description=payload.description or "Account deposit",
        )

        db.commit()
        db.refresh(account)
        return self._to_account_response(account)

    def withdraw_balance(
        self,
        db: Session,
        acting_user: Dict[str, Any],
        payload: base_models.AccountMutationRequest,
    ) -> base_models.UserAccountResponse:
        user_id = self._resolve_target_user_id(acting_user, payload.user_id)
        if payload.amount_usdt <= 0:
            raise HTTPException(status_code=400, detail="amount_usdt must be greater than 0")

        account = self._get_or_create_account(db, user_id)
        if account.balance_usdt < payload.amount_usdt:
            raise HTTPException(status_code=400, detail="insufficient saldo for withdrawal")

        account.balance_usdt -= payload.amount_usdt
        account.total_withdrawn_usdt += payload.amount_usdt

        self._append_account_transaction(
            db,
            user_id=user_id,
            transaction_type="withdraw",
            amount_usdt=payload.amount_usdt,
            description=payload.description or "Account withdrawal",
        )

        db.commit()
        db.refresh(account)
        return self._to_account_response(account)

    def get_holdings(self, db: Session, user_id: int) -> base_models.UserHoldingsResponse:
        account = self._get_or_create_account(db, user_id)
        holdings = (
            db.query(db_models.UserHolding)
            .filter(db_models.UserHolding.user_id == user_id)
            .order_by(db_models.UserHolding.symbol.asc())
            .all()
        )

        items = [self._sync_holding_value(db, holding) for holding in holdings if (holding.quantity or 0) > 0]
        db.commit()
        return base_models.UserHoldingsResponse(
            user_id=account.user_id,
            holdings=[self._to_holding_response(item) for item in items],
        )

    def get_portfolio(self, db: Session, user_id: int) -> base_models.PortfolioResponse:
        account = self._get_or_create_account(db, user_id)
        holdings = (
            db.query(db_models.UserHolding)
            .filter(db_models.UserHolding.user_id == user_id)
            .order_by(db_models.UserHolding.symbol.asc())
            .all()
        )

        synced_holdings = [self._sync_holding_value(db, holding) for holding in holdings if (holding.quantity or 0) > 0]
        total_holdings_value = sum((holding.current_value_usdt or 0) for holding in synced_holdings)
        db.commit()

        return base_models.PortfolioResponse(
            user_id=account.user_id,
            balance_usdt=account.balance_usdt,
            total_holdings_value_usdt=total_holdings_value,
            total_portfolio_value_usdt=account.balance_usdt + total_holdings_value,
            holdings=[self._to_holding_response(item) for item in synced_holdings],
        )

    async def _run_loop(self) -> None:
        SessionLocal = get_session_local()
        print("[Collector] Loop started", flush=True)
        while self._is_running:
            try:
                print("[Collector] Connecting to Kraken stream...", flush=True)
                kraken_symbols = [p.replace("USDT", "/USD") for p in self._pairs]
                async with websockets.connect(
                    self._market_client.KRAKEN_WS_URL,
                    ping_interval=20,
                    ping_timeout=20,
                ) as ws:
                    await ws.send(json.dumps({
                        "method": "subscribe",
                        "params": {"channel": "ticker", "symbol": kraken_symbols},
                    }))
                    print("[Collector] Connected and subscribed to Kraken stream", flush=True)
                    while self._is_running:
                        try:
                            raw_message = await asyncio.wait_for(ws.recv(), timeout=60)
                        except asyncio.TimeoutError:
                            print("[Collector] recv() timeout — reconnecting", flush=True)
                            break

                        tickers = self._market_client.parse_trade_message(cast(str, raw_message))

                        if not tickers:
                            continue

                        for ticker in tickers:
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

                                snapshot_created_at = cast(Any, snapshot).created_at

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
                                            "created_at": snapshot_created_at.isoformat() if snapshot_created_at else datetime.utcnow().isoformat(),
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
                print(f"[Collector] Kraken stream error: {type(e).__name__}: {e} — falling back to REST", flush=True)
                await self._run_rest_polling_once(SessionLocal)
                await asyncio.sleep(max(self._interval_seconds, 5))

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
    def _resolve_target_user_id(acting_user: Dict[str, Any], requested_user_id: Optional[int]) -> int:
        role = str(acting_user.get("role") or "user").lower()
        token_user_id = acting_user.get("id_user")
        if requested_user_id and role in ["admin", "superadmin"]:
            return requested_user_id
        return int(token_user_id)

    @staticmethod
    def _append_account_transaction(
        db: Session,
        user_id: int,
        transaction_type: str,
        amount_usdt: float,
        symbol: Optional[str] = None,
        quantity: Optional[float] = None,
        description: Optional[str] = None,
        reference_trade_id: Optional[int] = None,
    ) -> None:
        tx = db_models.AccountTransaction(
            user_id=user_id,
            transaction_type=transaction_type,
            symbol=symbol,
            amount_usdt=amount_usdt,
            quantity=quantity,
            description=description,
            reference_trade_id=reference_trade_id,
        )
        db.add(tx)

    @staticmethod
    def _get_or_create_account(db: Session, user_id: int) -> db_models.UserAccount:
        user = db.query(db_models.User).filter(db_models.User.id_user == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")

        account = db.query(db_models.UserAccount).filter(db_models.UserAccount.user_id == user_id).first()
        if account is None:
            account = db_models.UserAccount(user_id=user_id)
            db.add(account)
            db.flush()
        return account

    @staticmethod
    def _get_or_create_holding(db: Session, user_id: int, symbol: str) -> db_models.UserHolding:
        holding = (
            db.query(db_models.UserHolding)
            .filter(db_models.UserHolding.user_id == user_id)
            .filter(db_models.UserHolding.symbol == symbol)
            .first()
        )
        if holding is None:
            holding = db_models.UserHolding(user_id=user_id, symbol=symbol, quantity=0, avg_cost_usdt=0, current_value_usdt=0)
            db.add(holding)
            db.flush()
        return holding

    def _sync_holding_value(self, db: Session, holding: db_models.UserHolding) -> db_models.UserHolding:
        price = self._get_latest_price_usdt(db, holding.symbol) or holding.avg_cost_usdt or 0
        holding.current_value_usdt = (holding.quantity or 0) * price
        return holding

    @staticmethod
    def _get_latest_price_usdt(db: Session, symbol: str) -> Optional[float]:
        row = (
            db.query(db_models.CryptoPriceSnapshot)
            .filter(db_models.CryptoPriceSnapshot.symbol == symbol)
            .order_by(db_models.CryptoPriceSnapshot.created_at.desc())
            .first()
        )
        if row is None:
            return None
        row_any = cast(Any, row)
        return cast(Optional[float], row_any.price_usdt)

    def _to_account_response(self, row: db_models.UserAccount) -> base_models.UserAccountResponse:
        row_any = cast(Any, row)
        return base_models.UserAccountResponse(
            user_id=cast(int, row_any.user_id),
            balance_usdt=cast(float, row_any.balance_usdt),
            total_deposited_usdt=cast(float, row_any.total_deposited_usdt),
            total_withdrawn_usdt=cast(float, row_any.total_withdrawn_usdt),
            updated_at=cast(datetime, row_any.updated_at),
        )

    def _to_holding_response(self, row: db_models.UserHolding) -> base_models.UserHoldingResponse:
        row_any = cast(Any, row)
        current_price = 0.0
        quantity = cast(float, row_any.quantity)
        current_value = cast(float, row_any.current_value_usdt)
        if quantity > 0:
            current_price = current_value / quantity
        return base_models.UserHoldingResponse(
            symbol=cast(str, row_any.symbol),
            quantity=quantity,
            avg_cost_usdt=cast(float, row_any.avg_cost_usdt),
            current_price_usdt=current_price,
            current_value_usdt=current_value,
            updated_at=cast(datetime, row_any.updated_at),
        )

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

    @staticmethod
    def _to_trade_response(
        row: db_models.CryptoTradeHistory,
        account: Optional[db_models.UserAccount] = None,
        holding: Optional[db_models.UserHolding] = None,
    ) -> base_models.CryptoTradeResponse:
        row_any = cast(Any, row)
        return base_models.CryptoTradeResponse(
            id_trade=cast(int, row_any.id_trade),
            user_id=cast(int, row_any.user_id),
            trade_type=cast(str, row_any.trade_type),
            symbol=cast(str, row_any.symbol),
            quantity=cast(float, row_any.quantity),
            unit_price_usdt=cast(float, row_any.unit_price_usdt),
            total_usdt=cast(float, row_any.total_usdt),
            executed_at=cast(datetime, row_any.executed_at),
            created_at=cast(datetime, row_any.created_at),
            balance_usdt=cast(Optional[float], getattr(account, "balance_usdt", None)),
            holding_quantity=cast(Optional[float], getattr(holding, "quantity", None)),
            holding_value_usdt=cast(Optional[float], getattr(holding, "current_value_usdt", None)),
            avg_cost_usdt=cast(Optional[float], getattr(holding, "avg_cost_usdt", None)),
        )


websocket_manager = WebSocketConnectionManager()
crypto_collector_service = CryptoCollectorService(websocket_manager)
