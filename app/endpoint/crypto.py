import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, cast
import json

import httpx
from fastapi import HTTPException, WebSocket
from sqlalchemy.orm import Session
import websockets

from database import db_models, base_models
from database.database import get_session_local
from services.events import BalanceUpdatedEvent, TradeExecutedEvent, publish
from services.trading.trade_guards import (
    assert_exchange_healthy,
    check_rate_limit,
    validate_price_against_market,
    validate_symbol_limits,
)


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

        dead: List[WebSocket] = []
        for connection in connections:
            try:
                await asyncio.wait_for(connection.send_json(payload), timeout=5.0)
            except Exception:
                dead.append(connection)

        for connection in dead:
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
        self._interval_seconds = 1
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
        self._state_lock = asyncio.Lock()
        # Shared buffer: último preço conhecido por símbolo, atualizado pelo receiver
        self._price_cache: Dict[str, Dict] = {}

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
            btc=self._to_price_item(btc),
            eth=self._to_price_item(eth),
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

        # Strip timezone info so comparisons work with naive MySQL/SQLite datetimes
        start_date = start_date.replace(tzinfo=None)
        end_date = end_date.replace(tzinfo=None)

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

        items: List[base_models.CryptoPriceItem] = []
        for item in rows:
            parsed = self._to_price_item(item)
            if parsed is not None:
                items.append(parsed)

        return base_models.CryptoHistoryByDateResponse(items=items)

    def register_trade(
        self,
        db: Session,
        trade_type: str,
        payload: base_models.CryptoTradeCreateRequest,
        user_id: int,
        trade_mode: str = "live",
        binance_order_id: Optional[str] = None,
    ) -> base_models.CryptoTradeResponse:
        normalized_type = trade_type.lower()
        if normalized_type not in ["buy", "sell"]:
            raise HTTPException(status_code=400, detail="trade_type must be buy or sell")

        normalized_symbol = payload.symbol.upper()
        if normalized_symbol not in ["BTC", "ETH"]:
            raise HTTPException(status_code=400, detail="symbol must be BTC or ETH")

        if payload.unit_price_usdt <= 0:
            raise HTTPException(status_code=400, detail="unit_price_usdt must be greater than 0")

        quantity = payload.quantity if payload.quantity is not None else 1.0
        if quantity <= 0:
            raise HTTPException(status_code=400, detail="quantity must be greater than 0")

        # Symbol quantity limits (apply to both modes)
        validate_symbol_limits(normalized_symbol, quantity)

        # Live-only operational guards
        if trade_mode == "live":
            assert_exchange_healthy()
            check_rate_limit(user_id, normalized_symbol)
            # Skip price deviation check when the order was already filled by Binance
            # (fill price IS the market price; our snapshot check would be redundant)
            if binance_order_id is None:
                validate_price_against_market(db, normalized_symbol, payload.unit_price_usdt)

        executed_at = (payload.executed_at or datetime.utcnow()).replace(tzinfo=None)
        total_usdt = quantity * payload.unit_price_usdt

        try:
            # Verify user exists before acquiring any locks
            if db.query(db_models.User).filter(db_models.User.id_user == user_id).first() is None:
                raise HTTPException(status_code=404, detail="user not found")

            if trade_mode == "live":
                # Acquire row-level locks on account and holding before reading balances.
                # Prevents two concurrent orders from reading the same balance and both passing.
                account = (
                    db.query(db_models.UserAccount)
                    .filter(db_models.UserAccount.user_id == user_id)
                    .with_for_update()
                    .first()
                )
                if account is None:
                    account = db_models.UserAccount(user_id=user_id)
                    db.add(account)
                    db.flush()

                holding = (
                    db.query(db_models.UserHolding)
                    .filter(db_models.UserHolding.user_id == user_id)
                    .filter(db_models.UserHolding.symbol == normalized_symbol)
                    .with_for_update()
                    .first()
                )
                if holding is None:
                    holding = db_models.UserHolding(
                        user_id=user_id,
                        symbol=normalized_symbol,
                        quantity=0,
                        avg_cost_usdt=0,
                        current_value_usdt=0,
                    )
                    db.add(holding)
                    db.flush()
            else:
                # Paper mode: no row-level locks needed
                account = (
                    db.query(db_models.PaperBalance)
                    .filter(db_models.PaperBalance.user_id == user_id)
                    .first()
                )
                if account is None:
                    account = db_models.PaperBalance(user_id=user_id)
                    db.add(account)
                    db.flush()

                holding = (
                    db.query(db_models.PaperHolding)
                    .filter(db_models.PaperHolding.user_id == user_id)
                    .filter(db_models.PaperHolding.symbol == normalized_symbol)
                    .first()
                )
                if holding is None:
                    holding = db_models.PaperHolding(
                        user_id=user_id,
                        symbol=normalized_symbol,
                        quantity=0,
                        avg_cost_usdt=0,
                        current_value_usdt=0,
                    )
                    db.add(holding)
                    db.flush()

            # Validate wallet balances immediately after acquiring locks
            if normalized_type == "buy":
                if account.balance_usdt < total_usdt:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"saldo insuficiente para esta compra: "
                            f"disponivel ${account.balance_usdt:.2f} USD, "
                            f"necessario ${total_usdt:.2f} USD"
                        ),
                    )

                previous_qty = holding.quantity or 0
                new_qty = previous_qty + quantity
                total_cost_basis = (holding.avg_cost_usdt or 0) * previous_qty + total_usdt

                holding.quantity = new_qty
                holding.avg_cost_usdt = total_cost_basis / new_qty if new_qty > 0 else 0
                holding.current_value_usdt = new_qty * payload.unit_price_usdt
                prev_balance = float(account.balance_usdt)
                account.balance_usdt -= total_usdt
            else:
                available_qty = holding.quantity or 0
                if available_qty < quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"saldo insuficiente de {normalized_symbol} para esta venda: "
                            f"disponivel {available_qty:.8f}, "
                            f"necessario {quantity:.8f}"
                        ),
                    )

                new_qty = available_qty - quantity
                holding.quantity = new_qty
                holding.avg_cost_usdt = holding.avg_cost_usdt if new_qty > 0 else 0
                holding.current_value_usdt = new_qty * payload.unit_price_usdt
                prev_balance = float(account.balance_usdt)
                account.balance_usdt += total_usdt

            trade = db_models.CryptoTradeHistory(
                user_id=user_id,
                trade_type=normalized_type,
                symbol=normalized_symbol,
                trade_mode=trade_mode,
                quantity=quantity,
                unit_price_usdt=payload.unit_price_usdt,
                total_usdt=total_usdt,
                executed_at=executed_at,
                binance_order_id=binance_order_id,
            )
            db.add(trade)
            db.flush()

            self._append_account_transaction(
                db,
                user_id=user_id,
                transaction_type=normalized_type,
                amount_usdt=total_usdt,
                symbol=normalized_symbol,
                quantity=quantity,
                description=f"{normalized_type.upper()} {normalized_symbol}",
                reference_trade_id=trade.id_trade,
                trade_mode=trade_mode,
            )

            db.commit()
            db.refresh(trade)
            db.refresh(account)
            db.refresh(holding)

        except HTTPException:
            db.rollback()
            raise
        except Exception as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail="erro interno ao processar a ordem") from exc

        change = -total_usdt if normalized_type == "buy" else total_usdt
        publish(TradeExecutedEvent(
            trade_id=int(cast(Any, trade).id_trade),
            user_id=user_id,
            trade_type=normalized_type,
            symbol=normalized_symbol,
            trade_mode=trade_mode,
            quantity=quantity,
            unit_price_usdt=payload.unit_price_usdt,
            total_usdt=total_usdt,
            executed_at=cast(datetime, cast(Any, trade).executed_at),
        ))
        publish(BalanceUpdatedEvent(
            user_id=user_id,
            trade_mode=trade_mode,
            balance_usdt=float(cast(Any, account).balance_usdt),
            previous_balance_usdt=prev_balance,
            change_usdt=change,
            reason=f"{normalized_type.upper()} {normalized_symbol}",
        ))

        return self._to_trade_response(trade, account, holding, trade_mode)

    def trade_history(
        self,
        db: Session,
        start_date: datetime,
        end_date: datetime,
        user_id: int,
        symbol: Optional[str] = None,
        trade_type: Optional[str] = None,
        trade_mode: Optional[str] = None,
    ) -> base_models.CryptoTradeHistoryResponse:
        # Strip timezone info so comparisons work with naive MySQL/SQLite datetimes
        start_date = start_date.replace(tzinfo=None)
        end_date = end_date.replace(tzinfo=None)

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

        normalized_mode = None
        if trade_mode:
            normalized_mode = trade_mode.lower()
            if normalized_mode not in ["live", "paper"]:
                raise HTTPException(status_code=400, detail="trade_mode must be live or paper")
            query = query.filter(db_models.CryptoTradeHistory.trade_mode == normalized_mode)

        rows = query.order_by(db_models.CryptoTradeHistory.executed_at.asc()).all()
        items = [self._to_trade_history_item(row) for row in rows]

        return base_models.CryptoTradeHistoryResponse(items=items)

    def get_account_balance(self, db: Session, user_id: int, trade_mode: str = "live") -> base_models.UserAccountResponse:
        account = self._get_or_create_account(db, user_id, trade_mode)
        db.commit()
        db.refresh(account)
        return self._to_account_response(account, trade_mode)

    def deposit_balance(
        self,
        db: Session,
        acting_user: Dict[str, Any],
        payload: base_models.AccountMutationRequest,
        trade_mode: str = "live",
    ) -> base_models.UserAccountResponse:
        user_id = self._resolve_target_user_id(acting_user, payload.user_id)
        if payload.amount_usdt <= 0:
            raise HTTPException(status_code=400, detail="amount_usdt must be greater than 0")

        account = self._get_or_create_account(db, user_id, trade_mode)
        account.balance_usdt += payload.amount_usdt
        account.total_deposited_usdt += payload.amount_usdt

        self._append_account_transaction(
            db,
            user_id=user_id,
            transaction_type="deposit",
            amount_usdt=payload.amount_usdt,
            description=payload.description or "Account deposit",
            trade_mode=trade_mode,
        )

        db.commit()
        db.refresh(account)
        return self._to_account_response(account, trade_mode)

    def withdraw_balance(
        self,
        db: Session,
        acting_user: Dict[str, Any],
        payload: base_models.AccountMutationRequest,
        trade_mode: str = "live",
    ) -> base_models.UserAccountResponse:
        user_id = self._resolve_target_user_id(acting_user, payload.user_id)
        if payload.amount_usdt <= 0:
            raise HTTPException(status_code=400, detail="amount_usdt must be greater than 0")

        account = self._get_or_create_account(db, user_id, trade_mode)
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
            trade_mode=trade_mode,
        )

        db.commit()
        db.refresh(account)
        return self._to_account_response(account, trade_mode)

    def get_holdings(self, db: Session, user_id: int, trade_mode: str = "live") -> base_models.UserHoldingsResponse:
        account = self._get_or_create_account(db, user_id, trade_mode)
        if trade_mode == "paper":
            holdings = (
                db.query(db_models.PaperHolding)
                .filter(db_models.PaperHolding.user_id == user_id)
                .order_by(db_models.PaperHolding.symbol.asc())
                .all()
            )
        else:
            holdings = (
                db.query(db_models.UserHolding)
                .filter(db_models.UserHolding.user_id == user_id)
                .order_by(db_models.UserHolding.symbol.asc())
                .all()
            )

        items = [self._sync_holding_value(db, holding) for holding in holdings if (holding.quantity or 0) > 0]
        db.commit()
        return base_models.UserHoldingsResponse(
            user_id=int(cast(Any, account).user_id),
            holdings=[self._to_holding_response(item, trade_mode) for item in items],
        )

    def get_portfolio(self, db: Session, user_id: int, trade_mode: str = "live") -> base_models.PortfolioResponse:
        account = self._get_or_create_account(db, user_id, trade_mode)
        if trade_mode == "paper":
            holdings = (
                db.query(db_models.PaperHolding)
                .filter(db_models.PaperHolding.user_id == user_id)
                .order_by(db_models.PaperHolding.symbol.asc())
                .all()
            )
        else:
            holdings = (
                db.query(db_models.UserHolding)
                .filter(db_models.UserHolding.user_id == user_id)
                .order_by(db_models.UserHolding.symbol.asc())
                .all()
            )

        synced_holdings = [self._sync_holding_value(db, holding) for holding in holdings if (holding.quantity or 0) > 0]
        total_holdings_value = sum((holding.current_value_usdt or 0) for holding in synced_holdings)
        db.commit()

        acct = cast(Any, account)
        return base_models.PortfolioResponse(
            user_id=int(acct.user_id),
            trade_mode=trade_mode,
            balance_usdt=float(acct.balance_usdt),
            total_holdings_value_usdt=total_holdings_value,
            total_portfolio_value_usdt=float(acct.balance_usdt) + total_holdings_value,
            holdings=[self._to_holding_response(item, trade_mode) for item in synced_holdings],
        )

    async def _run_loop(self) -> None:
        SessionLocal = get_session_local()
        reconnect_delay = 1.0
        print("[Collector] Loop started", flush=True)

        while self._is_running:
            try:
                print(f"[Collector] Connecting to Kraken WebSocket... (retry delay={reconnect_delay}s)", flush=True)
                kraken_symbols = [p.replace("USDT", "/USD") for p in self._pairs]
                async with websockets.connect(
                    self._market_client.KRAKEN_WS_URL,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=5,
                ) as ws:
                    await ws.send(json.dumps({
                        "method": "subscribe",
                        "params": {"channel": "ticker", "symbol": kraken_symbols},
                    }))
                    print("[Collector] Connected and subscribed to Kraken stream", flush=True)
                    reconnect_delay = 1.0  # reset backoff após conexão bem-sucedida

                    receiver = asyncio.create_task(self._kraken_receiver(ws))
                    tick = asyncio.create_task(self._tick_loop(SessionLocal))
                    try:
                        done, pending = await asyncio.wait(
                            {receiver, tick},
                            return_when=asyncio.FIRST_COMPLETED,
                        )
                        for t in pending:
                            t.cancel()
                            try:
                                await t
                            except (asyncio.CancelledError, Exception):
                                pass
                        # Propaga exceção do receiver (erro de stream) para forçar reconexão
                        for t in done:
                            if not t.cancelled() and t.exception():
                                raise t.exception()  # type: ignore[misc]
                    except asyncio.CancelledError:
                        receiver.cancel()
                        tick.cancel()
                        raise

            except asyncio.CancelledError:
                print("[Collector] Loop cancelled", flush=True)
                raise
            except Exception as e:
                print(
                    f"[Collector] Stream error: {type(e).__name__}: {e} "
                    f"— fallback REST, reconectando em {reconnect_delay}s",
                    flush=True,
                )
                if self._is_running:
                    await self._run_rest_polling_once(SessionLocal)
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, 30.0)  # backoff exponencial, máx 30s

    async def _kraken_receiver(self, ws: Any) -> None:
        """Lê mensagens do Kraken e mantém o último preço por símbolo em _price_cache."""
        while self._is_running:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=30)
            except asyncio.TimeoutError:
                print("[Collector] Kraken recv() timeout — reconectando", flush=True)
                return  # sai para forçar reconexão no _run_loop

            tickers = self._market_client.parse_trade_message(cast(str, raw))
            if tickers:
                for ticker in tickers:
                    if ticker["symbol"] in ["BTC", "ETH"]:
                        self._price_cache[ticker["symbol"]] = ticker

    async def _tick_loop(self, SessionLocal: Any) -> None:
        """A cada interval_seconds, persiste o cache no DB e faz broadcast para clientes WS."""
        while self._is_running:
            tick_start = asyncio.get_event_loop().time()

            if self._price_cache:
                db = SessionLocal()
                snapshots = []
                try:
                    for ticker in list(self._price_cache.values()):
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

                    for s in snapshots:
                        print(
                            f"[Collector] {s.symbol} @ {s.price_usdt} "
                            f"(interval={self._interval_seconds}s)",
                            flush=True,
                        )

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
                                "created_at": (cast(Any, s).created_at or datetime.utcnow()).isoformat(),
                            }
                            for s in snapshots
                        ],
                    }
                    await self._websocket_manager.broadcast(payload)
                except Exception as db_err:
                    print(f"[Collector] Tick DB error: {db_err}", flush=True)
                    db.rollback()
                finally:
                    db.close()

            # Dorme o tempo restante do intervalo compensando o tempo de processamento
            elapsed = asyncio.get_event_loop().time() - tick_start
            await asyncio.sleep(max(0.0, self._interval_seconds - elapsed))

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
        trade_mode: str = "live",
    ) -> None:
        tx = db_models.AccountTransaction(
            user_id=user_id,
            transaction_type=transaction_type,
            trade_mode=trade_mode,
            symbol=symbol,
            amount_usdt=amount_usdt,
            quantity=quantity,
            description=description,
            reference_trade_id=reference_trade_id,
        )
        db.add(tx)

    @staticmethod
    def _get_or_create_account(
        db: Session, user_id: int, trade_mode: str = "live"
    ) -> Union[db_models.UserAccount, db_models.PaperBalance]:
        user = db.query(db_models.User).filter(db_models.User.id_user == user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="user not found")

        if trade_mode == "paper":
            account = (
                db.query(db_models.PaperBalance)
                .filter(db_models.PaperBalance.user_id == user_id)
                .first()
            )
            if account is None:
                account = db_models.PaperBalance(user_id=user_id)
                db.add(account)
                db.flush()
        else:
            account = (
                db.query(db_models.UserAccount)
                .filter(db_models.UserAccount.user_id == user_id)
                .first()
            )
            if account is None:
                account = db_models.UserAccount(user_id=user_id)
                db.add(account)
                db.flush()
        return account

    @staticmethod
    def _get_or_create_holding(
        db: Session, user_id: int, symbol: str, trade_mode: str = "live"
    ) -> Union[db_models.UserHolding, db_models.PaperHolding]:
        if trade_mode == "paper":
            holding = (
                db.query(db_models.PaperHolding)
                .filter(db_models.PaperHolding.user_id == user_id)
                .filter(db_models.PaperHolding.symbol == symbol)
                .first()
            )
            if holding is None:
                holding = db_models.PaperHolding(
                    user_id=user_id, symbol=symbol, quantity=0, avg_cost_usdt=0, current_value_usdt=0
                )
                db.add(holding)
                db.flush()
        else:
            holding = (
                db.query(db_models.UserHolding)
                .filter(db_models.UserHolding.user_id == user_id)
                .filter(db_models.UserHolding.symbol == symbol)
                .first()
            )
            if holding is None:
                holding = db_models.UserHolding(
                    user_id=user_id, symbol=symbol, quantity=0, avg_cost_usdt=0, current_value_usdt=0
                )
                db.add(holding)
                db.flush()
        return holding

    def _sync_holding_value(
        self,
        db: Session,
        holding: Union[db_models.UserHolding, db_models.PaperHolding],
    ) -> Union[db_models.UserHolding, db_models.PaperHolding]:
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

    def _to_account_response(
        self,
        row: Union[db_models.UserAccount, db_models.PaperBalance],
        trade_mode: str = "live",
    ) -> base_models.UserAccountResponse:
        row_any = cast(Any, row)
        return base_models.UserAccountResponse(
            balance_usdt=cast(float, row_any.balance_usdt),
        )

    def _to_holding_response(
        self,
        row: Union[db_models.UserHolding, db_models.PaperHolding],
        trade_mode: str = "live",
    ) -> base_models.UserHoldingResponse:
        row_any = cast(Any, row)
        current_price = 0.0
        quantity = cast(float, row_any.quantity)
        current_value = cast(float, row_any.current_value_usdt)
        if quantity > 0:
            current_price = current_value / quantity
        return base_models.UserHoldingResponse(
            symbol=cast(str, row_any.symbol),
            trade_mode=trade_mode,
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
    def _to_price_item(row: Optional[db_models.CryptoPriceSnapshot]) -> Optional[base_models.CryptoPriceItem]:
        if row is None:
            return None
        row_any = cast(Any, row)
        return base_models.CryptoPriceItem(
            price_usdt=cast(float, row_any.price_usdt),
            created_at=cast(datetime, row_any.created_at),
        )

    @staticmethod
    def _to_trade_history_item(row: db_models.CryptoTradeHistory) -> base_models.CryptoTradeHistoryItem:
        row_any = cast(Any, row)
        return base_models.CryptoTradeHistoryItem(
            symbol=cast(str, row_any.symbol),
            trade_type=cast(str, row_any.trade_type),
            unit_price_usdt=cast(float, row_any.unit_price_usdt),
            quantity=cast(float, row_any.quantity),
            executed_at=cast(datetime, row_any.executed_at),
        )

    @staticmethod
    def _to_trade_response(
        row: db_models.CryptoTradeHistory,
        account: Optional[Union[db_models.UserAccount, db_models.PaperBalance]] = None,
        holding: Optional[Union[db_models.UserHolding, db_models.PaperHolding]] = None,
        trade_mode: Optional[str] = None,
    ) -> base_models.CryptoTradeResponse:
        row_any = cast(Any, row)
        effective_mode = trade_mode or cast(str, getattr(row_any, "trade_mode", "live")) or "live"
        return base_models.CryptoTradeResponse(
            id_trade=cast(int, row_any.id_trade),
            user_id=cast(int, row_any.user_id),
            trade_type=cast(str, row_any.trade_type),
            symbol=cast(str, row_any.symbol),
            trade_mode=effective_mode,
            quantity=cast(float, row_any.quantity),
            unit_price_usdt=cast(float, row_any.unit_price_usdt),
            total_usdt=cast(float, row_any.total_usdt),
            executed_at=cast(datetime, row_any.executed_at),
            created_at=cast(datetime, row_any.created_at),
            balance_usdt=cast(Optional[float], getattr(account, "balance_usdt", None)),
            holding_quantity=cast(Optional[float], getattr(holding, "quantity", None)),
            holding_value_usdt=cast(Optional[float], getattr(holding, "current_value_usdt", None)),
            avg_cost_usdt=cast(Optional[float], getattr(holding, "avg_cost_usdt", None)),
            binance_order_id=cast(Optional[str], getattr(row_any, "binance_order_id", None)),
        )


websocket_manager = WebSocketConnectionManager()
crypto_collector_service = CryptoCollectorService(websocket_manager)
