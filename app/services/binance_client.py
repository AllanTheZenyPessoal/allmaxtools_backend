"""
Thin async Binance REST client using HMAC-SHA256 signing.

Supports both production (api.binance.com) and testnet (testnet.binance.vision).
Uses httpx (already a project dependency) — no extra packages needed.
"""
from __future__ import annotations

import hashlib
import hmac
import time
import urllib.parse
from typing import Any, Dict

import httpx
from fastapi import HTTPException

BINANCE_BASE_URL = "https://api.binance.com"
BINANCE_TESTNET_URL = "https://testnet.binance.vision"

_SYMBOL_MAP: Dict[str, str] = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
}


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._base = BINANCE_TESTNET_URL if testnet else BINANCE_BASE_URL
        self._headers = {"X-MBX-APIKEY": api_key}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> str:
        query = urllib.parse.urlencode(params)
        return hmac.new(
            self._api_secret.encode(), query.encode(), hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _ts() -> int:
        return int(time.time() * 1000)

    @staticmethod
    def _binance_symbol(symbol: str) -> str:
        mapped = _SYMBOL_MAP.get(symbol.upper())
        if not mapped:
            raise HTTPException(status_code=400, detail=f"Unsupported symbol for Binance: {symbol}")
        return mapped

    @staticmethod
    def _raise_binance_error(resp: httpx.Response) -> None:
        try:
            msg = resp.json().get("msg", resp.text)
        except Exception:
            msg = resp.text
        raise HTTPException(
            status_code=502,
            detail=f"Binance API error ({resp.status_code}): {msg}",
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        """Returns True if Binance is reachable."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self._base}/api/v3/ping")
        return resp.status_code == 200

    async def get_account(self) -> Dict:
        """
        Returns account info including balances and trading permissions.
        Raises 502 if the API key is invalid or the request fails.
        """
        params: Dict[str, Any] = {"timestamp": self._ts(), "recvWindow": 5000}
        params["signature"] = self._sign(params)
        async with httpx.AsyncClient(timeout=10.0, headers=self._headers) as client:
            resp = await client.get(f"{self._base}/api/v3/account", params=params)
        if resp.status_code != 200:
            self._raise_binance_error(resp)
        return resp.json()

    async def market_order(self, side: str, symbol: str, quantity: float) -> Dict:
        """
        Execute a MARKET order on Binance.

        side     : 'BUY' or 'SELL'
        symbol   : 'BTC' or 'ETH' (mapped to BTCUSDT / ETHUSDT)
        quantity : base-asset quantity (e.g. 0.001 BTC)

        Returns a dict with:
            order_id, symbol, side, executed_qty, avg_price,
            total_usdt, fees_usdt, status
        """
        binance_symbol = self._binance_symbol(symbol)
        params: Dict[str, Any] = {
            "symbol": binance_symbol,
            "side": side.upper(),
            "type": "MARKET",
            "quantity": f"{quantity:.8f}",
            "timestamp": self._ts(),
            "recvWindow": 5000,
        }
        params["signature"] = self._sign(params)

        async with httpx.AsyncClient(timeout=15.0, headers=self._headers) as client:
            resp = await client.post(f"{self._base}/api/v3/order", params=params)

        if resp.status_code != 200:
            self._raise_binance_error(resp)

        data = resp.json()
        status = data.get("status", "")
        if status not in ("FILLED", "PARTIALLY_FILLED"):
            raise HTTPException(
                status_code=502,
                detail=f"Binance order did not fill: status={status}",
            )

        return self._parse_fill(data)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_fill(data: Dict) -> Dict:
        fills = data.get("fills", [])
        total_qty = sum(float(f["qty"]) for f in fills) or float(data.get("executedQty", 0))
        total_quote = sum(float(f["price"]) * float(f["qty"]) for f in fills)
        avg_price = total_quote / total_qty if total_qty > 0 else 0.0

        fees_usdt = 0.0
        for f in fills:
            commission = float(f.get("commission", 0))
            asset = f.get("commissionAsset", "")
            if asset == "USDT":
                fees_usdt += commission
            elif asset in ("BTC", "ETH") and avg_price > 0:
                fees_usdt += commission * avg_price

        return {
            "order_id": str(data["orderId"]),
            "symbol": data["symbol"],
            "side": data["side"],
            "executed_qty": total_qty,
            "avg_price": avg_price,
            "total_usdt": float(data.get("cummulativeQuoteQty", total_quote)),
            "fees_usdt": fees_usdt,
            "status": data["status"],
        }
