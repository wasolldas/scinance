"""
Bybit V5 REST Executor — signed trading endpoints.

Funktioniert mit Demo- (``api-demo.bybit.com``) und Testnet-
(``api-testnet.bybit.com``) Konten. Aus Sicherheitsgründen verweigert der
Executor das Senden von Orders im LIVE-Modus, sofern nicht explizit
``allow_live=True`` gesetzt wird.

Signierung (Bybit V5):
    sign = HMAC_SHA256(secret, timestamp + api_key + recv_window + payload)
    Header: X-BAPI-API-KEY, X-BAPI-TIMESTAMP, X-BAPI-RECV-WINDOW, X-BAPI-SIGN
    payload = query-string (GET) bzw. raw JSON body (POST)
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from typing import Any, Optional
from urllib.parse import urlencode

import aiohttp

from bybit_edge.config import (
    BYBIT_API_KEY,
    BYBIT_API_SECRET,
    BYBIT_DEMO,
    BYBIT_RECV_WINDOW_MS,
    BYBIT_TESTNET,
    REST_INSTRUMENTS,
    REST_ORDER_CREATE,
    REST_POSITION_LIST,
    REST_SET_LEVERAGE,
    REST_WALLET_BALANCE,
    rest_base_url,
)

logger = logging.getLogger(__name__)


class BybitExecutor:
    """Async REST client for Bybit V5 signed trading endpoints."""

    def __init__(
        self,
        symbol: str,
        api_key: str = BYBIT_API_KEY,
        api_secret: str = BYBIT_API_SECRET,
        allow_live: bool = False,
    ) -> None:
        self.symbol = symbol
        self._api_key = api_key
        self._api_secret = api_secret
        self._base = rest_base_url()
        self._recv_window = str(BYBIT_RECV_WINDOW_MS)
        self._allow_live = allow_live
        self._session: Optional[aiohttp.ClientSession] = None
        self._qty_step: float = 0.001  # konservativer Default für BTCUSDT
        self._min_qty: float = 0.001
        self._instrument_loaded = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "BybitExecutor":
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    @property
    def is_live(self) -> bool:
        """True wenn weder Demo noch Testnet aktiv ist (= echtes Geld)."""
        return not (BYBIT_DEMO or BYBIT_TESTNET)

    def _safety_check(self) -> None:
        """Verhindert versehentliche Orders auf einem LIVE-Konto."""
        if self.is_live and not self._allow_live:
            raise RuntimeError(
                "LIVE-Modus erkannt (BYBIT_DEMO=false, BYBIT_TESTNET=false). "
                "Order-Ausführung blockiert. Setze allow_live=True nur, wenn "
                "du wirklich mit echtem Geld handeln willst."
            )
        if not self._api_key or not self._api_secret:
            raise RuntimeError("Kein API-Key/Secret gesetzt — Order nicht möglich.")

    # ------------------------------------------------------------------
    # Signing
    # ------------------------------------------------------------------

    def _sign(self, timestamp: str, payload: str) -> str:
        param = timestamp + self._api_key + self._recv_window + payload
        return hmac.new(
            self._api_secret.encode(),
            param.encode(),
            hashlib.sha256,
        ).hexdigest()

    def _headers(self, payload: str) -> dict[str, str]:
        ts = str(int(time.time() * 1000))
        return {
            "X-BAPI-API-KEY": self._api_key,
            "X-BAPI-TIMESTAMP": ts,
            "X-BAPI-RECV-WINDOW": self._recv_window,
            "X-BAPI-SIGN": self._sign(ts, payload),
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Generic request helpers
    # ------------------------------------------------------------------

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        query = urlencode(params)
        headers = self._headers(query)
        url = f"{self._base}{path}?{query}"
        session = self._ensure_session()
        async with session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            return await resp.json()

    async def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        raw = json.dumps(body, separators=(",", ":"))
        headers = self._headers(raw)
        url = f"{self._base}{path}"
        session = self._ensure_session()
        async with session.post(
            url, data=raw, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            return await resp.json()

    # ------------------------------------------------------------------
    # Instrument metadata (qty step / min qty)
    # ------------------------------------------------------------------

    async def load_instrument(self) -> None:
        """Lädt qtyStep und minOrderQty für das Symbol (unsigniert)."""
        try:
            session = self._ensure_session()
            url = f"{self._base}{REST_INSTRUMENTS}"
            params = {"category": "linear", "symbol": self.symbol}
            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                body = await resp.json()
            lst = body.get("result", {}).get("list", [])
            if lst:
                lot = lst[0].get("lotSizeFilter", {})
                self._qty_step = float(lot.get("qtyStep", self._qty_step))
                self._min_qty = float(lot.get("minOrderQty", self._min_qty))
                self._instrument_loaded = True
                logger.info(
                    "Instrument %s: qtyStep=%s minQty=%s",
                    self.symbol, self._qty_step, self._min_qty,
                )
        except Exception:
            logger.exception("Instrument-Info konnte nicht geladen werden — Defaults aktiv.")

    def round_qty(self, raw_qty: float) -> float:
        """Rundet eine Order-Größe auf das qtyStep-Raster ab."""
        if self._qty_step <= 0:
            return max(raw_qty, self._min_qty)
        steps = int(raw_qty / self._qty_step)
        qty = steps * self._qty_step
        if qty < self._min_qty:
            return 0.0
        # Auf sinnvolle Dezimalstellen runden (Float-Artefakte vermeiden)
        decimals = max(0, len(str(self._qty_step).split(".")[-1]))
        return round(qty, decimals)

    # ------------------------------------------------------------------
    # Trading
    # ------------------------------------------------------------------

    async def set_leverage(self, leverage: int) -> dict[str, Any]:
        self._safety_check()
        body = {
            "category": "linear",
            "symbol": self.symbol,
            "buyLeverage": str(leverage),
            "sellLeverage": str(leverage),
        }
        result = await self._post(REST_SET_LEVERAGE, body)
        # retCode 110043 = leverage not modified (kein Fehler)
        if result.get("retCode") not in (0, 110043):
            logger.warning("set_leverage: %s", result.get("retMsg"))
        return result

    async def place_market_order(
        self, side: str, qty: float, reduce_only: bool = False
    ) -> dict[str, Any]:
        """Sendet eine Market-Order. ``side`` ist ``"Buy"`` oder ``"Sell"``."""
        self._safety_check()
        if qty <= 0:
            return {"retCode": -1, "retMsg": "qty <= 0 — übersprungen"}
        body = {
            "category": "linear",
            "symbol": self.symbol,
            "side": side,
            "orderType": "Market",
            "qty": str(qty),
            "reduceOnly": reduce_only,
        }
        result = await self._post(REST_ORDER_CREATE, body)
        if result.get("retCode") == 0:
            logger.info(
                "ORDER OK: %s %s %s (orderId=%s)",
                side, qty, self.symbol,
                result.get("result", {}).get("orderId", "?"),
            )
        else:
            logger.warning("ORDER FEHLER: %s — %s", result.get("retCode"), result.get("retMsg"))
        return result

    async def get_position(self) -> dict[str, Any]:
        """Aktuelle Position für das Symbol (size, side, unrealisedPnl)."""
        self._safety_check()
        params = {"category": "linear", "symbol": self.symbol}
        body = await self._get(REST_POSITION_LIST, params)
        lst = body.get("result", {}).get("list", [])
        if lst:
            p = lst[0]
            return {
                "size": float(p.get("size", 0) or 0),
                "side": p.get("side", ""),
                "avg_price": float(p.get("avgPrice", 0) or 0),
                "unrealised_pnl": float(p.get("unrealisedPnl", 0) or 0),
            }
        return {"size": 0.0, "side": "", "avg_price": 0.0, "unrealised_pnl": 0.0}

    async def get_equity(self) -> float:
        """Gesamt-Equity (USDT) des Unified-Accounts."""
        self._safety_check()
        params = {"accountType": "UNIFIED"}
        body = await self._get(REST_WALLET_BALANCE, params)
        lst = body.get("result", {}).get("list", [])
        if lst:
            return float(lst[0].get("totalEquity", 0) or 0)
        return 0.0

    async def close_position(self) -> dict[str, Any]:
        """Schließt eine offene Position per reduce-only Market-Order."""
        pos = await self.get_position()
        size = pos["size"]
        if size <= 0:
            return {"retCode": 0, "retMsg": "keine offene Position"}
        # Gegenseite zum Schließen
        close_side = "Sell" if pos["side"] == "Buy" else "Buy"
        return await self.place_market_order(close_side, size, reduce_only=True)
