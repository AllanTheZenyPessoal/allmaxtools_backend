"""
Lightweight in-memory event bus for trade and balance events.

After a successful trade commit the service publishes structured events here.
Handlers receive the event synchronously (still within the request lifetime)
so they must be fast — for side-effects that can block (e.g. external HTTP
calls) register an async handler and schedule it as a background task.

Usage
-----
    from services.events import publish, subscribe, TradeExecutedEvent

    # Register a handler (at startup or module import):
    subscribe(TradeExecutedEvent, lambda e: logger.info("trade: %s", e))

    # Publish after a successful commit:
    publish(TradeExecutedEvent(...))
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Type

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------

@dataclass
class TradeExecutedEvent:
    trade_id: int
    user_id: int
    trade_type: str       # "buy" | "sell"
    symbol: str
    trade_mode: str       # "live" | "paper"
    quantity: float
    unit_price_usdt: float
    total_usdt: float
    executed_at: datetime


@dataclass
class BalanceUpdatedEvent:
    user_id: int
    trade_mode: str       # "live" | "paper"
    balance_usdt: float
    previous_balance_usdt: float
    change_usdt: float    # negative = debit, positive = credit
    reason: str           # e.g. "BUY BTC", "SELL ETH", "deposit", "withdraw"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_handlers: Dict[Type, List[Callable]] = {}


def subscribe(event_type: Type, handler: Callable) -> None:
    """Register *handler* to be called whenever *event_type* is published."""
    _handlers.setdefault(event_type, []).append(handler)


def publish(event: Any) -> None:
    """Dispatch *event* to all registered handlers.

    Handler exceptions are caught and logged; they never abort the caller.
    """
    for handler in _handlers.get(type(event), []):
        try:
            handler(event)
        except Exception as exc:
            logger.error(
                "[EventBus] Handler %s failed for %s: %s",
                getattr(handler, "__name__", repr(handler)),
                type(event).__name__,
                exc,
            )

    # Built-in structured audit log for every event
    logger.info("[Audit] %s | %s", type(event).__name__, event)
