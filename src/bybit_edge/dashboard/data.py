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

try:
    from bybit_edge.config import DASHBOARD_SNAPSHOT_DIR as _DEFAULT_SNAPSHOT_DIR
except Exception:  # pragma: no cover — config-Import sollte funktionieren
    _DEFAULT_SNAPSHOT_DIR = Path("data/dashboard")

logger = logging.getLogger(__name__)


def _snapshot_path(name: str, snapshot_dir: Optional[Path] = None) -> Path:
    """Resolve a snapshot Parquet file path inside the dashboard snapshot dir."""
    base = Path(snapshot_dir) if snapshot_dir is not None else Path(_DEFAULT_SNAPSHOT_DIR)
    return base / name


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
    persist: Any = None,
    symbol: Optional[str] = None,
    n: int = 30,
    snapshot_dir: Optional[Path] = None,
) -> list[dict]:
    """Lade die letzten ``n`` Liquidationen.

    Bevorzugt liest die Funktion aus dem Parquet-Snapshot
    ``<snapshot_dir>/liquidations_recent.parquet`` (vom LiveRunner
    geschrieben). Existiert die Datei nicht oder ist sie defekt, fällt die
    Funktion auf den direkten DuckDB-Pfad zurück — das funktioniert, solange
    KEIN anderer Prozess gerade in dieselbe DuckDB schreibt.

    Parameters
    ----------
    persist
        Objekt mit ``conn`` (DuckDB-Connection) für den Fallback-Pfad.
        Üblicherweise ein ``PersistenceLayer``; akzeptiert auch direkt eine
        Connection (Duck-Typing über ``execute``).
    symbol
        Wenn gesetzt, werden nur Liquidationen dieses Symbols zurückgegeben.
        ``None`` → alle Symbole.
    n
        Maximale Anzahl Zeilen.
    snapshot_dir
        Optional ein abweichendes Verzeichnis für Tests.
    """
    path = _snapshot_path("liquidations_recent.parquet", snapshot_dir)
    if path.exists():
        try:
            df = pd.read_parquet(path)
            if symbol is not None and "symbol" in df.columns:
                df = df[df["symbol"] == symbol]
            if "ts" in df.columns and len(df) > 0:
                df = df.sort_values("ts", ascending=False, kind="stable")
            if n is not None and n > 0:
                df = df.head(int(n))
            return [
                {
                    "ts": int(row.get("ts", 0) or 0),
                    "side": str(row.get("side", "") or ""),
                    "volume": float(row.get("volume", 0.0) or 0.0),
                    "price": float(row.get("price", 0.0) or 0.0),
                    "usd_value": float(row.get("usd_value", 0.0) or 0.0),
                }
                for row in df.to_dict(orient="records")
            ]
        except Exception:
            logger.exception(
                "Snapshot liquidations_recent.parquet konnte nicht gelesen werden — "
                "fallback auf DuckDB."
            )

    # ---- Fallback: direkter DuckDB-Read (nur OK ohne parallelen Writer) ----
    if persist is None:
        return []
    conn = getattr(persist, "conn", persist)
    try:
        if symbol is not None:
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
        else:
            rows = conn.execute(
                """
                SELECT ts, side, volume, price, usd_value
                FROM liquidations
                ORDER BY ts DESC
                LIMIT ?
                """,
                [int(n)],
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


def load_row_counts(
    persist: Any = None,
    snapshot_dir: Optional[Path] = None,
) -> dict[str, int]:
    """Liefere Row-Counts pro Tabelle.

    Bevorzugt liest die Funktion aus dem Parquet-Snapshot
    ``<snapshot_dir>/row_counts.parquet``. Existiert die Datei nicht, wird
    versucht ``persist.row_counts()`` zu nutzen, andernfalls direkt per
    DuckDB-Query zu zählen. Bei jeder Stufe gilt: Fehler werden geloggt
    und führen zu einem leeren bzw. teilweise gefüllten Dict — die UI darf
    nicht crashen.
    """
    path = _snapshot_path("row_counts.parquet", snapshot_dir)
    if path.exists():
        try:
            df = pd.read_parquet(path)
            if "table_name" in df.columns and "row_count" in df.columns:
                return {
                    str(row["table_name"]): int(row["row_count"])
                    for row in df.to_dict(orient="records")
                }
        except Exception:
            logger.exception(
                "Snapshot row_counts.parquet konnte nicht gelesen werden — "
                "fallback auf DuckDB."
            )

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


def load_coverage(
    persist: Any = None,
    snapshot_dir: Optional[Path] = None,
) -> dict[str, dict[str, Any]]:
    """Liefere pro Tabelle eine Übersicht ``{min_ts, max_ts, count, hours}``.

    Bevorzugt aus dem Parquet-Snapshot
    ``<snapshot_dir>/coverage.parquet``. Fallback: direkter DuckDB-Query.
    Bei leeren Tabellen ist ``min_ts``/``max_ts`` ``None`` und ``hours`` ``0.0``.
    """
    path = _snapshot_path("coverage.parquet", snapshot_dir)
    out: dict[str, dict[str, Any]] = {}
    if path.exists():
        try:
            df = pd.read_parquet(path)
            for row in df.to_dict(orient="records"):
                table = str(row.get("table_name", ""))
                if not table:
                    continue
                mn = row.get("min_ts")
                mx = row.get("max_ts")
                cnt = int(row.get("row_count", 0) or 0)
                mn_i = int(mn) if mn is not None and pd.notna(mn) else None
                mx_i = int(mx) if mx is not None and pd.notna(mx) else None
                hours = (
                    (mx_i - mn_i) / 1000.0 / 3600.0
                    if (mn_i is not None and mx_i is not None and mx_i > mn_i)
                    else 0.0
                )
                out[table] = {
                    "min_ts": mn_i,
                    "max_ts": mx_i,
                    "count": cnt,
                    "hours": round(hours, 4),
                }
            return out
        except Exception:
            logger.exception(
                "Snapshot coverage.parquet konnte nicht gelesen werden — "
                "fallback auf DuckDB."
            )

    if persist is None:
        return {}
    conn = getattr(persist, "conn", persist)
    for table in (
        "tickers", "trades", "liquidations", "kline_1min",
        "orderbook_snapshots",
        "open_interest", "long_short_ratio", "funding_history",
    ):
        try:
            r = conn.execute(
                f"SELECT MIN(ts), MAX(ts), COUNT(*) FROM {table}"
            ).fetchone()
        except Exception:
            continue
        if not r:
            continue
        mn = int(r[0]) if r[0] is not None else None
        mx = int(r[1]) if r[1] is not None else None
        cnt = int(r[2]) if r[2] is not None else 0
        hours = (
            (mx - mn) / 1000.0 / 3600.0
            if (mn is not None and mx is not None and mx > mn)
            else 0.0
        )
        out[table] = {
            "min_ts": mn,
            "max_ts": mx,
            "count": cnt,
            "hours": round(hours, 4),
        }
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
