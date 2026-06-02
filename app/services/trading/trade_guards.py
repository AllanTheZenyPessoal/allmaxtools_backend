"""
Operational guards for trade execution.

Provides:
- Symbol quantity limits (min/max per symbol, hardcoded initial values).
- Price deviation validation against the latest DB snapshot (live mode only).
- Sliding-window rate limiter per (user_id, symbol).
- Three-state circuit breaker for the price provider.

All singletons are module-level so they persist across requests within the same
process.  Tests should call ``reset_for_testing()`` between runs.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from database import db_models

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Symbol quantity limits
# ---------------------------------------------------------------------------
SYMBOL_LIMITS: Dict[str, Dict[str, float]] = {
    "BTC": {"min_qty": 0.0001, "max_qty": 100.0},
    "ETH": {"min_qty": 0.001,  "max_qty": 10_000.0},
}

# ---------------------------------------------------------------------------
# Price deviation
# ---------------------------------------------------------------------------
MAX_PRICE_DEVIATION_PCT: float = 1.0        # 1.0 %
MARKET_PRICE_STALE_SECONDS: int = 900       # ignore snapshots older than 15 min

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
RATE_LIMIT_MAX_ORDERS: int = 10
RATE_LIMIT_WINDOW_SECONDS: int = 60

# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------
CB_MAX_CONSECUTIVE_FAILURES: int = 3
CB_MAX_LATENCY_SECONDS: float = 1.0
CB_COOLDOWN_SECONDS: int = 60


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

class _RateLimiter:
    """In-memory sliding-window rate limiter keyed on (user_id, symbol)."""

    def __init__(self) -> None:
        self._windows: Dict[str, deque] = defaultdict(deque)

    def check(self, user_id: int, symbol: str) -> None:
        key = f"{user_id}:{symbol}"
        now = time.monotonic()
        window = self._windows[key]
        cutoff = now - RATE_LIMIT_WINDOW_SECONDS

        # Evict timestamps outside the window
        while window and window[0] < cutoff:
            window.popleft()

        if len(window) >= RATE_LIMIT_MAX_ORDERS:
            oldest = window[0]
            retry_after = int(RATE_LIMIT_WINDOW_SECONDS - (now - oldest)) + 1
            raise HTTPException(
                status_code=429,
                detail=(
                    f"too many orders for {symbol}: limit is {RATE_LIMIT_MAX_ORDERS} "
                    f"per {RATE_LIMIT_WINDOW_SECONDS}s. Retry in {retry_after}s."
                ),
                headers={"Retry-After": str(retry_after)},
            )

        window.append(now)

    def clear(self) -> None:
        self._windows.clear()


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------

class _CircuitBreaker:
    """
    Three-state circuit breaker: CLOSED → OPEN → HALF_OPEN → CLOSED.

    CLOSED  : normal operation
    OPEN    : blocking all requests (provider considered down)
    HALF_OPEN: one probe request allowed; success → CLOSED, failure → OPEN
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self) -> None:
        self._state: str = self.CLOSED
        self._failures: int = 0
        self._opened_at: Optional[float] = None

    # ------------------------------------------------------------------
    # Internal state transitions
    # ------------------------------------------------------------------

    def _maybe_half_open(self) -> None:
        """Transition OPEN → HALF_OPEN when cooldown has elapsed."""
        if self._state == self.OPEN and self._opened_at is not None:
            if time.monotonic() - self._opened_at >= CB_COOLDOWN_SECONDS:
                self._state = self.HALF_OPEN
                logger.info("[CircuitBreaker] Entering HALF_OPEN state for probe.")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def record_success(self) -> None:
        self._failures = 0
        if self._state != self.CLOSED:
            logger.info("[CircuitBreaker] CLOSED after successful probe.")
        self._state = self.CLOSED

    def record_failure(self) -> None:
        self._failures += 1
        if self._state == self.HALF_OPEN or self._failures >= CB_MAX_CONSECUTIVE_FAILURES:
            self._state = self.OPEN
            self._opened_at = time.monotonic()
            logger.warning(
                "[CircuitBreaker] OPENED after %d consecutive failures.", self._failures
            )

    def assert_closed(self) -> None:
        """Raise HTTP 503 if the circuit is open."""
        self._maybe_half_open()
        if self._state == self.OPEN:
            raise HTTPException(
                status_code=503,
                detail=(
                    "exchange provider temporarily unavailable (circuit breaker open). "
                    "Please retry in a few seconds."
                ),
            )

    def reset(self) -> None:
        self._state = self.CLOSED
        self._failures = 0
        self._opened_at = None


# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

rate_limiter = _RateLimiter()
circuit_breaker = _CircuitBreaker()


# ---------------------------------------------------------------------------
# Public guard functions
# ---------------------------------------------------------------------------

def validate_symbol_limits(symbol: str, quantity: float) -> None:
    """Raise 400 if *quantity* is outside the allowed min/max for *symbol*."""
    limits = SYMBOL_LIMITS.get(symbol)
    if limits is None:
        return  # skip for unknown symbols (already validated upstream)

    if quantity < limits["min_qty"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"quantity {quantity:.8f} is below minimum for {symbol}: "
                f"min={limits['min_qty']}"
            ),
        )
    if quantity > limits["max_qty"]:
        raise HTTPException(
            status_code=400,
            detail=(
                f"quantity {quantity:.8f} exceeds maximum for {symbol}: "
                f"max={limits['max_qty']}"
            ),
        )


def validate_price_against_market(
    db: Session, symbol: str, submitted_price: float
) -> None:
    """
    Reject the order when *submitted_price* deviates more than
    MAX_PRICE_DEVIATION_PCT from the most recent DB snapshot.

    The check is silently skipped when:
    - No snapshot exists (price collector not running yet).
    - The most recent snapshot is older than MARKET_PRICE_STALE_SECONDS.
    """
    row = (
        db.query(db_models.CryptoPriceSnapshot)
        .filter(db_models.CryptoPriceSnapshot.symbol == symbol)
        .order_by(db_models.CryptoPriceSnapshot.created_at.desc())
        .first()
    )
    if row is None:
        logger.info("[PriceGuard] No snapshot for %s — skipping price check.", symbol)
        return

    snapshot_age = (datetime.utcnow() - row.created_at).total_seconds()
    if snapshot_age > MARKET_PRICE_STALE_SECONDS:
        logger.info(
            "[PriceGuard] Snapshot for %s is %.0fs old (stale) — skipping.", symbol, snapshot_age
        )
        return

    market_price = float(row.price_usdt)
    if market_price <= 0:
        return

    deviation_pct = abs(submitted_price - market_price) / market_price * 100.0
    if deviation_pct > MAX_PRICE_DEVIATION_PCT:
        raise HTTPException(
            status_code=400,
            detail=(
                f"price deviation too high for {symbol}: "
                f"submitted=${submitted_price:.2f}, "
                f"market=${market_price:.2f}, "
                f"deviation={deviation_pct:.2f}% "
                f"(max allowed={MAX_PRICE_DEVIATION_PCT}%)"
            ),
        )


def check_rate_limit(user_id: int, symbol: str) -> None:
    """Raise 429 if the user has exceeded the order rate for *symbol*."""
    rate_limiter.check(user_id, symbol)


def assert_exchange_healthy() -> None:
    """Raise 503 if the circuit breaker is open."""
    circuit_breaker.assert_closed()


def report_exchange_success() -> None:
    """Signal a healthy provider response to the circuit breaker."""
    circuit_breaker.record_success()


def report_exchange_failure() -> None:
    """Signal a failed provider call to the circuit breaker."""
    circuit_breaker.record_failure()


def reset_for_testing() -> None:
    """Reset all in-memory guard state.  Call only from tests."""
    rate_limiter.clear()
    circuit_breaker.reset()
