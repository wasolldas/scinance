"""Daten-Beschaffung für das Dashboard — Streamlit-frei testbar.

Alle Funktionen sind **read-only**, defensiv (keine Crashes bei fehlenden
Daten) und benötigen nur ``pandas``/``duckdb``. Insbesondere importiert
dieses Modul kein Streamlit, damit die Funktionen ohne optionale Deps
getestet werden können.
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Trade-Journal (CSV)
# --------------------------------------------------------------------------

JOURNAL_COLUMNS: list[str] = [
    "ts_iso", "ts_unix", "symbol", "strategy_id", "action",
    "side", "qty", "price", "confidence", "ret_code", "order_id",
]


def load_journal(path: Path, n: int = 50) -> pd.DataFrame:
    """Lade die letzten ``n`` Zeilen aus dem Trade-Journal CSV.

    Returns
    -------
    pd.DataFrame
        Sortiert nach ``ts_unix`` absteigend. Bei fehlender Datei oder
        Fehler wird ein leeres DataFrame mit den erwarteten Spalten
        zurückgegeben.
    """
    if path is None or not Path(path).exists():
        return pd.DataFrame(columns=JOURNAL_COLUMNS)
    try:
        df = pd.read_csv(path)
    except Exception:
        logger.exception("Trade-Journal CSV konnte nicht gelesen werden: %s", path)
        return pd.DataFrame(columns=JOURNAL_COLUMNS)
    # Fehlende Spalten ergänzen, damit das DataFrame stabil bleibt
    for col in JOURNAL_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    if "ts_unix" in df.columns and len(df) > 0:
        df = df.sort_values("ts_unix", ascending=False, kind="stable")
    if n is not None and n > 0:
        df = df.head(n)
    return df.reset_index(drop=True)


# --------------------------------------------------------------------------
# Persistenz (DuckDB) — Liquidationen, Row-Counts, DB-Statistik
# --------------------------------------------------------------------------

def load_recent_liquidations(
    persist: Any,
    symbol: str,
    n: int = 30,
) -> list[dict]:
    """Lade die letzten ``n`` Liquidationen aus DuckDB.

    Parameters
    ----------
    persist
        Objekt mit ``conn`` (DuckDB-Connection). Üblicherweise ein
        ``PersistenceLayer``; im Dashboard nutzen wir eine read-only-Verbindung
        und übergeben einen leichten Wrapper. Wir akzeptieren auch direkt
        eine Connection (Duck-Typing über ``execute``).
    """
    if persist is None:
        return []
    conn = getattr(persist, "conn", persist)
    try:
        rows = conn.execute(
            """
            SELECT ts, side, volume, price, usd_value
            FROM liquidations
            WHERE symbol = ?
            ORDER BY ts DESC
            LIMIT ?
            """,
            [symbol, int(n)],
        ).fetchall()
    except Exception:
        logger.exception("Liquidations-Query fehlgeschlagen")
        return []
    return [
        {
            "ts": int(r[0]),
            "side": str(r[1] or ""),
            "volume": float(r[2] or 0.0),
            "price": float(r[3] or 0.0),
            "usd_value": float(r[4] or 0.0),
        }
        for r in rows
    ]


def load_row_counts(persist: Any) -> dict[str, int]:
    """Gibt ``row_counts()`` zurück oder ein leeres Dict bei Fehlern."""
    if persist is None:
        return {}
    # Wenn das Objekt eine row_counts()-Methode hat, bevorzugt nutzen
    fn = getattr(persist, "row_counts", None)
    if callable(fn):
        try:
            return dict(fn())
        except Exception:
            logger.exception("row_counts() fehlgeschlagen")
            return {}
    # Fallback: direkt zählen über die bekannten Tabellen
    conn = getattr(persist, "conn", persist)
    out: dict[str, int] = {}
    for table in (
        "tickers", "trades", "liquidations", "kline_1min",
        "orderbook_snapshots",
        "open_interest", "long_short_ratio", "funding_history",
    ):
        try:
            r = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            out[table] = int(r[0]) if r else 0
        except Exception:
            out[table] = 0
    return out


def load_table_time_range(
    persist: Any,
    table: str,
) -> Optional[tuple[int, int]]:
    """Min/Max ``ts`` einer Tabelle (in ms). ``None`` falls leer/Fehler."""
    if persist is None:
        return None
    conn = getattr(persist, "conn", persist)
    try:
        r = conn.execute(f"SELECT MIN(ts), MAX(ts) FROM {table}").fetchone()
    except Exception:
        return None
    if not r or r[0] is None or r[1] is None:
        return None
    return int(r[0]), int(r[1])


# --------------------------------------------------------------------------
# Account-Status (Executor REST)
# --------------------------------------------------------------------------

async def _fetch_account_status(executor: Any) -> dict[str, Any]:
    equity = await executor.get_equity()
    pos = await executor.get_position()
    return {
        "connected": True,
        "equity": float(equity),
        "position": {
            "size": float(pos.get("size", 0.0)),
            "side": str(pos.get("side", "")),
            "avg_price": float(pos.get("avg_price", 0.0)),
            "unrealised_pnl": float(pos.get("unrealised_pnl", 0.0)),
        },
        "error": "",
    }


def load_account_status(executor: Any) -> dict[str, Any]:
    """Synchrone Wrapper für ``get_equity`` + ``get_position`` des Executors.

    Im Dashboard wird das pro Refresh in einem frischen Event-Loop ausgeführt,
    damit Streamlits Sync-Rendering nicht blockiert wird.

    Returns
    -------
    dict
        Bei Erfolg: ``{connected: True, equity, position, error: ""}``.
        Bei Fehler: ``{connected: False, equity: 0.0, position: {...},
        error: <str>}``.
    """
    if executor is None:
        return {
            "connected": False,
            "equity": 0.0,
            "position": {"size": 0.0, "side": "", "avg_price": 0.0, "unrealised_pnl": 0.0},
            "error": "kein Executor",
        }
    try:
        return asyncio.run(_fetch_account_status(executor))
    except Exception as exc:  # noqa: BLE001 — UI darf nicht crashen
        logger.warning("Account-Status fehlgeschlagen: %s", exc)
        return {
            "connected": False,
            "equity": 0.0,
            "position": {"size": 0.0, "side": "", "avg_price": 0.0, "unrealised_pnl": 0.0},
            "error": str(exc),
        }


# --------------------------------------------------------------------------
# Heartbeat-File (vom LiveRunner)
# --------------------------------------------------------------------------

def load_heartbeat_file(path: Path) -> Optional[dict]:
    """Liest die optionale Heartbeat-Datei des LiveRunners.

    Returns ``None`` wenn die Datei nicht existiert oder kein gültiges JSON ist.
    """
    if path is None or not Path(path).exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        logger.warning("Heartbeat-Datei konnte nicht geparst werden: %s", path)
        return None
    if not isinstance(data, dict):
        return None
    return data


# --------------------------------------------------------------------------
# Hilfen für die UI
# --------------------------------------------------------------------------

def ms_to_iso(ts_ms: int | float | None) -> str:
    """Bequeme Konvertierung von ms-Timestamp -> ISO-String (UTC)."""
    if ts_ms is None:
        return ""
    try:
        return (
            pd.Timestamp(int(ts_ms), unit="ms", tz="UTC")
            .strftime("%Y-%m-%d %H:%M:%S")
        )
    except Exception:
        return ""
