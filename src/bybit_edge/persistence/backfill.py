"""
REST-Backfill-Driver — historische Bybit-V5-Daten in DuckDB persistieren.

Backfillbare Datenarten (öffentliche Bybit-V5-REST):
    * Klines (OHLCV+turnover)  → ``/v5/market/kline``
    * Funding-Rate-History     → ``/v5/market/funding/history``
    * Open-Interest            → ``/v5/market/open-interest``
    * Long/Short-Account-Ratio → ``/v5/market/account-ratio``

NICHT backfillbar (nur durch Live-Sammlung sinnvoll erhebbar):
    * L2-Orderbook-Tiefe       (Historie nicht öffentlich)
    * Tick-Trades              (nur die letzten ~1000 Trades)
    * Tickers-Snapshots        (nur aktueller Wert)

Implementiert ist eine synchrone, ``urllib.request``-basierte Pagination
analog zu ``scripts/backtest.py`` — das vermeidet die ``aiohttp``-Komplexität
und ist für CLI-Backfills mehr als schnell genug. Sleeps zwischen den
Requests respektieren das 120 req/min Limit für nicht-authentifizierte
Calls (PRD Abschnitt 3).

Die bestehende asynchrone ``PersistenceLayer.backfill_kline``-Methode bleibt
unverändert (Live-Use-Case). Neue Aufrufe sollten ``BackfillManager``
verwenden.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.parse
import urllib.request
from typing import Any, Optional

from bybit_edge.config import (
    MULTI_SYMBOL_UNIVERSE,
    REST_FUNDING_HISTORY,
    REST_KLINE,
    REST_LONG_SHORT_RATIO,
    REST_OPEN_INTEREST,
    REST_RATE_LIMIT_UNAUTH,
    rest_base_url,
)
from bybit_edge.persistence.db import PersistenceLayer

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Konstanten
# ------------------------------------------------------------------
_MS_DAY: int = 24 * 3600 * 1000
_KLINE_LIMIT: int = 1000
_FUNDING_LIMIT: int = 200
_OI_LIMIT: int = 200
_LS_LIMIT: int = 500
_BATCH_SIZE: int = 500
# 120 req/min → 0.5 s/req + Puffer. PRD Sektion 3.
_SLEEP_SECONDS: float = max(60.0 / REST_RATE_LIMIT_UNAUTH, 0.25) + 0.05

# Wie viele Millisekunden überspannt ein Kline-Intervall?
_KLINE_INTERVAL_MS: dict[str, int] = {
    "1": 60_000,
    "3": 3 * 60_000,
    "5": 5 * 60_000,
    "15": 15 * 60_000,
    "30": 30 * 60_000,
    "60": 60 * 60_000,
    "120": 120 * 60_000,
    "240": 240 * 60_000,
    "360": 360 * 60_000,
    "720": 720 * 60_000,
    "D": _MS_DAY,
    "W": 7 * _MS_DAY,
    "M": 30 * _MS_DAY,
}


def _http_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    """Einfacher GET-Request gegen Bybit-V5-REST.

    ``urllib.request`` ist absichtlich gewählt (gleiches Muster wie
    ``scripts/backtest.py``) — kein ``aiohttp``-Overhead nötig, und der
    Patch-Punkt ist trivial monkey-patchbar in den Tests.
    """
    url = f"{rest_base_url()}{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=15) as resp:  # noqa: S310
        return json.loads(resp.read().decode())


class BackfillManager:
    """Synchroner Multi-Source-Backfill-Driver für Bybit-V5-Daten."""

    def __init__(self, persist: Optional[PersistenceLayer] = None) -> None:
        if persist is None:
            self.persist = PersistenceLayer()
            self._owns_persist = True
        else:
            self.persist = persist
            self._owns_persist = False

    def close(self) -> None:
        """Schließt die DB-Verbindung — nur, wenn wir sie selbst geöffnet haben."""
        if self._owns_persist:
            self.persist.close()

    # ------------------------------------------------------------------
    # Klines
    # ------------------------------------------------------------------

    def backfill_klines(
        self,
        symbol: str,
        interval: str = "1",
        months: int = 6,
        skip_if_exists: bool = True,
    ) -> int:
        """Lädt OHLCV-Klines paginiert rückwärts und schreibt sie in DuckDB.

        Returns die Anzahl neu eingefügter Zeilen. Bei ``skip_if_exists`` und
        bereits vorhandenen Klines für ``symbol`` werden 0 Calls ausgeführt.
        """
        if skip_if_exists and self.persist.count_klines(symbol, interval) > 0:
            logger.info("Klines %s/%s bereits vorhanden – skip.", symbol, interval)
            return 0

        target_start = int(time.time() * 1000) - months * 30 * _MS_DAY
        end = int(time.time() * 1000)
        step_ms = _KLINE_INTERVAL_MS.get(interval, 60_000)
        total = 0
        batch: list[dict] = []
        seen_ts: set[int] = set()

        while True:
            body = _http_get(REST_KLINE, {
                "category": "linear",
                "symbol": symbol,
                "interval": interval,
                "end": end,
                "limit": _KLINE_LIMIT,
            })
            lst = body.get("result", {}).get("list", [])
            if not lst:
                break

            new_rows = 0
            for c in lst:
                ts_i = int(c[0])
                if ts_i in seen_ts:
                    continue
                seen_ts.add(ts_i)
                batch.append({
                    "ts": ts_i,
                    "symbol": symbol,
                    "open": float(c[1]),
                    "high": float(c[2]),
                    "low": float(c[3]),
                    "close": float(c[4]),
                    "volume": float(c[5]),
                    "turnover": float(c[6]),
                })
                new_rows += 1
                if len(batch) >= _BATCH_SIZE:
                    total += self.persist.write_klines_batch(batch)
                    batch = []

            oldest = min(int(c[0]) for c in lst)
            if oldest <= target_start or len(lst) < _KLINE_LIMIT or new_rows == 0:
                break
            end = oldest - 1
            time.sleep(_SLEEP_SECONDS)
            # Sicherheits-Stopp falls Cursor sich nicht bewegt
            if end < target_start - step_ms:
                break

        if batch:
            total += self.persist.write_klines_batch(batch)

        logger.info("Backfill Klines %s/%s: %d Zeilen", symbol, interval, total)
        return total

    # ------------------------------------------------------------------
    # Funding-History
    # ------------------------------------------------------------------

    def backfill_funding(
        self,
        symbol: str,
        months: int = 6,
        skip_if_exists: bool = True,
    ) -> int:
        """Lädt Funding-Rate-History paginiert rückwärts.

        Bybit V5: ``fundingRateTimestamp`` (ms) und ``fundingRate`` (float).
        """
        if skip_if_exists and self.persist.count_funding(symbol) > 0:
            logger.info("Funding %s bereits vorhanden – skip.", symbol)
            return 0

        target_start = int(time.time() * 1000) - months * 30 * _MS_DAY
        end = int(time.time() * 1000)
        total = 0
        batch: list[dict] = []
        seen_ts: set[int] = set()

        while True:
            body = _http_get(REST_FUNDING_HISTORY, {
                "category": "linear",
                "symbol": symbol,
                "endTime": end,
                "limit": _FUNDING_LIMIT,
            })
            lst = body.get("result", {}).get("list", [])
            if not lst:
                break

            new_rows = 0
            for item in lst:
                ts_i = int(item["fundingRateTimestamp"])
                if ts_i in seen_ts:
                    continue
                seen_ts.add(ts_i)
                batch.append({
                    "ts": ts_i,
                    "symbol": symbol,
                    "funding_rate": float(item["fundingRate"]),
                })
                new_rows += 1
                if len(batch) >= _BATCH_SIZE:
                    total += self.persist.write_funding_history_batch(batch)
                    batch = []

            oldest = min(int(it["fundingRateTimestamp"]) for it in lst)
            if oldest <= target_start or len(lst) < _FUNDING_LIMIT or new_rows == 0:
                break
            end = oldest - 1
            time.sleep(_SLEEP_SECONDS)

        if batch:
            total += self.persist.write_funding_history_batch(batch)

        logger.info("Backfill Funding %s: %d Zeilen", symbol, total)
        return total

    # ------------------------------------------------------------------
    # Open-Interest
    # ------------------------------------------------------------------

    def backfill_open_interest(
        self,
        symbol: str,
        interval_tag: str = "5min",
        months: int = 6,
        skip_if_exists: bool = True,
    ) -> int:
        """Lädt Open-Interest-Historie paginiert rückwärts.

        Bybit V5: Parameter heißt ``intervalTime`` (nicht ``interval``!),
        Response liefert ``openInterest`` (string) und ``timestamp`` (ms).
        Gültige Intervalle: ``5min, 15min, 30min, 1h, 4h, 1d``.
        """
        if skip_if_exists and self.persist.count_open_interest(symbol, interval_tag) > 0:
            logger.info(
                "Open-Interest %s/%s bereits vorhanden – skip.",
                symbol, interval_tag,
            )
            return 0

        target_start = int(time.time() * 1000) - months * 30 * _MS_DAY
        end = int(time.time() * 1000)
        total = 0
        batch: list[dict] = []
        seen_ts: set[int] = set()

        # Bybit nutzt für OI einen ``cursor``-Mechanismus. Wir bedienen
        # beide Varianten: solange ``cursor`` mitgegeben wird, paginieren
        # wir damit; sonst über ``endTime`` (älteste Page → noch ältere).
        cursor: Optional[str] = None

        while True:
            params: dict[str, Any] = {
                "category": "linear",
                "symbol": symbol,
                "intervalTime": interval_tag,
                "endTime": end,
                "limit": _OI_LIMIT,
            }
            if cursor:
                params["cursor"] = cursor

            body = _http_get(REST_OPEN_INTEREST, params)
            result = body.get("result", {})
            lst = result.get("list", [])
            if not lst:
                break

            new_rows = 0
            for item in lst:
                ts_i = int(item["timestamp"])
                if ts_i in seen_ts:
                    continue
                seen_ts.add(ts_i)
                batch.append({
                    "ts": ts_i,
                    "symbol": symbol,
                    "open_interest": float(item["openInterest"]),
                    "interval_tag": interval_tag,
                })
                new_rows += 1
                if len(batch) >= _BATCH_SIZE:
                    total += self.persist.write_open_interest_batch(batch)
                    batch = []

            oldest = min(int(it["timestamp"]) for it in lst)
            next_cursor = result.get("nextPageCursor") or ""
            cursor = next_cursor if next_cursor else None
            if (
                oldest <= target_start
                or new_rows == 0
                or (not cursor and len(lst) < _OI_LIMIT)
            ):
                break
            if not cursor:
                end = oldest - 1
            time.sleep(_SLEEP_SECONDS)

        if batch:
            total += self.persist.write_open_interest_batch(batch)

        logger.info(
            "Backfill Open-Interest %s/%s: %d Zeilen",
            symbol, interval_tag, total,
        )
        return total

    # ------------------------------------------------------------------
    # Long/Short-Account-Ratio
    # ------------------------------------------------------------------

    def backfill_long_short_ratio(
        self,
        symbol: str,
        period: str = "5min",
        months: int = 6,
        skip_if_exists: bool = True,
    ) -> int:
        """Lädt Long/Short-Account-Ratio paginiert rückwärts.

        Bybit V5: Parameter heißt ``period``, Response liefert ``buyRatio``,
        ``sellRatio`` und ``timestamp`` (ms). Gültige Perioden:
        ``5min, 15min, 30min, 1h, 4h, 1d``.
        """
        if skip_if_exists and self.persist.count_long_short(symbol, period) > 0:
            logger.info(
                "Long/Short %s/%s bereits vorhanden – skip.", symbol, period,
            )
            return 0

        target_start = int(time.time() * 1000) - months * 30 * _MS_DAY
        end = int(time.time() * 1000)
        total = 0
        batch: list[dict] = []
        seen_ts: set[int] = set()

        while True:
            body = _http_get(REST_LONG_SHORT_RATIO, {
                "category": "linear",
                "symbol": symbol,
                "period": period,
                "endTime": end,
                "limit": _LS_LIMIT,
            })
            lst = body.get("result", {}).get("list", [])
            if not lst:
                break

            new_rows = 0
            for item in lst:
                ts_i = int(item["timestamp"])
                if ts_i in seen_ts:
                    continue
                seen_ts.add(ts_i)
                batch.append({
                    "ts": ts_i,
                    "symbol": symbol,
                    "buy_ratio": float(item["buyRatio"]),
                    "sell_ratio": float(item["sellRatio"]),
                    "period_tag": period,
                })
                new_rows += 1
                if len(batch) >= _BATCH_SIZE:
                    total += self.persist.write_long_short_ratio_batch(batch)
                    batch = []

            oldest = min(int(it["timestamp"]) for it in lst)
            if oldest <= target_start or len(lst) < _LS_LIMIT or new_rows == 0:
                break
            end = oldest - 1
            time.sleep(_SLEEP_SECONDS)

        if batch:
            total += self.persist.write_long_short_ratio_batch(batch)

        logger.info(
            "Backfill Long/Short %s/%s: %d Zeilen", symbol, period, total,
        )
        return total

    # ------------------------------------------------------------------
    # All-in-one
    # ------------------------------------------------------------------

    def backfill_all(
        self,
        symbol: str,
        months: int = 6,
        kline_interval: str = "5",
        oi_interval: str = "5min",
        ls_period: str = "5min",
        skip_if_exists: bool = True,
    ) -> dict[str, int]:
        """Backfillt alle vier Datenarten für ein einzelnes Symbol."""
        return {
            "klines": self.backfill_klines(
                symbol, kline_interval, months, skip_if_exists,
            ),
            "funding": self.backfill_funding(
                symbol, months, skip_if_exists,
            ),
            "open_interest": self.backfill_open_interest(
                symbol, oi_interval, months, skip_if_exists,
            ),
            "long_short_ratio": self.backfill_long_short_ratio(
                symbol, ls_period, months, skip_if_exists,
            ),
        }

    def backfill_universe(
        self,
        symbols: list[str],
        months: int = 6,
        kline_interval: str = "5",
        oi_interval: str = "5min",
        ls_period: str = "5min",
        skip_if_exists: bool = True,
    ) -> dict[str, dict[str, int]]:
        """Backfillt eine Liste von Symbolen sequenziell.

        Default-Universum aus ``config.MULTI_SYMBOL_UNIVERSE`` kann über
        ``symbols`` gezielt überschrieben werden.
        """
        out: dict[str, dict[str, int]] = {}
        for sym in symbols:
            try:
                out[sym] = self.backfill_all(
                    sym,
                    months=months,
                    kline_interval=kline_interval,
                    oi_interval=oi_interval,
                    ls_period=ls_period,
                    skip_if_exists=skip_if_exists,
                )
            except Exception as exc:  # noqa: BLE001 — wir wollen das Universum nicht hart abbrechen
                logger.exception("Backfill %s failed: %s", sym, exc)
                out[sym] = {
                    "klines": 0, "funding": 0,
                    "open_interest": 0, "long_short_ratio": 0,
                    "error": 1,
                }
        return out


__all__ = ["BackfillManager", "MULTI_SYMBOL_UNIVERSE"]
