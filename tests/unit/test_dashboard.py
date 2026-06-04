"""Tests für die Dashboard-Daten-Schicht (``bybit_edge.dashboard.data``).

Streamlit darf NICHT importiert werden — die Datenfunktionen sind bewusst
ohne UI-Deps gehalten. Wir nutzen ausschließlich Pandas und eine In-Memory-
DuckDB.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import duckdb
import pandas as pd
import pytest

from bybit_edge.dashboard.data import (
    JOURNAL_COLUMNS,
    load_account_status,
    load_coverage,
    load_heartbeat_file,
    load_journal,
    load_journal_aggregated,
    load_recent_liquidations,
    load_replay_results,
    load_row_counts,
    ms_to_iso,
)


# --------------------------------------------------------------------------
# Trade-Journal CSV
# --------------------------------------------------------------------------

def test_load_journal_returns_dataframe(tmp_path: Path) -> None:
    path = tmp_path / "trades_journal.csv"
    df = pd.DataFrame(
        [
            {
                "ts_iso": "2026-05-30T12:00:00Z", "ts_unix": 1748606400,
                "symbol": "BTCUSDT", "strategy_id": "S3", "action": "OPEN",
                "side": "Buy", "qty": 0.001, "price": 70000.0,
                "confidence": 0.8, "ret_code": 0, "order_id": "abc",
            },
            {
                "ts_iso": "2026-05-30T12:01:00Z", "ts_unix": 1748606460,
                "symbol": "BTCUSDT", "strategy_id": "S2", "action": "CLOSE",
                "side": "Sell", "qty": 0.001, "price": 70010.0,
                "confidence": 0.6, "ret_code": 0, "order_id": "def",
            },
        ]
    )
    df.to_csv(path, index=False)

    out = load_journal(path, n=50)
    assert isinstance(out, pd.DataFrame)
    assert len(out) == 2
    # Sortiert nach ts_unix desc — neuester Trade zuerst
    assert int(out.iloc[0]["ts_unix"]) == 1748606460
    # Erwartete Spalten vorhanden
    for col in JOURNAL_COLUMNS:
        assert col in out.columns


def test_load_journal_handles_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "does_not_exist.csv"
    out = load_journal(path, n=50)
    assert isinstance(out, pd.DataFrame)
    assert out.empty
    for col in JOURNAL_COLUMNS:
        assert col in out.columns


def test_load_journal_respects_n_limit(tmp_path: Path) -> None:
    path = tmp_path / "trades_journal.csv"
    rows = [
        {
            "ts_iso": f"2026-05-30T12:{i:02d}:00Z", "ts_unix": 1748606400 + i,
            "symbol": "BTCUSDT", "strategy_id": "S3", "action": "OPEN",
            "side": "Buy", "qty": 0.001, "price": 70000.0 + i,
            "confidence": 0.5, "ret_code": 0, "order_id": f"id{i}",
        }
        for i in range(10)
    ]
    pd.DataFrame(rows).to_csv(path, index=False)
    out = load_journal(path, n=3)
    assert len(out) == 3
    # Erste Zeile = höchster ts_unix = i=9
    assert int(out.iloc[0]["ts_unix"]) == 1748606400 + 9


# --------------------------------------------------------------------------
# DuckDB-Reads
# --------------------------------------------------------------------------

def _make_duckdb_with_liquidations(n: int = 5, symbol: str = "BTCUSDT"):
    conn = duckdb.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE liquidations (
            ts BIGINT NOT NULL,
            symbol VARCHAR NOT NULL,
            side VARCHAR,
            volume DOUBLE,
            price DOUBLE,
            usd_value DOUBLE
        )
        """
    )
    base_ts = 1_700_000_000_000
    for i in range(n):
        conn.execute(
            "INSERT INTO liquidations VALUES (?, ?, ?, ?, ?, ?)",
            [base_ts + i * 1000, symbol, "Buy" if i % 2 == 0 else "Sell",
             1.0 + i, 70000.0 + i, 70000.0 * (1.0 + i)],
        )
    return conn


def test_load_recent_liquidations() -> None:
    conn = _make_duckdb_with_liquidations(n=5)
    try:
        out = load_recent_liquidations(conn, "BTCUSDT", n=30)
        assert isinstance(out, list)
        assert len(out) == 5
        # Sortiert ts DESC
        ts_list = [r["ts"] for r in out]
        assert ts_list == sorted(ts_list, reverse=True)
        # Felder vorhanden
        assert {"ts", "side", "volume", "price", "usd_value"}.issubset(out[0].keys())
        # Limit respektiert
        limited = load_recent_liquidations(conn, "BTCUSDT", n=2)
        assert len(limited) == 2
        # Anderes Symbol → leer
        assert load_recent_liquidations(conn, "ETHUSDT", n=10) == []
    finally:
        conn.close()


def test_load_recent_liquidations_none_persist() -> None:
    assert load_recent_liquidations(None, "BTCUSDT", n=10) == []


def test_load_row_counts_includes_all_tables() -> None:
    """``load_row_counts`` muss alle bekannten Tabellen liefern, selbst wenn
    eine fehlt (Fallback-Pfad → Wert 0)."""
    conn = duckdb.connect(":memory:")
    # Wir bauen NUR drei Tabellen — für die restlichen liefert der Fallback 0
    conn.execute("CREATE TABLE tickers (ts BIGINT, symbol VARCHAR)")
    conn.execute("CREATE TABLE trades (ts BIGINT, symbol VARCHAR)")
    conn.execute("CREATE TABLE liquidations (ts BIGINT, symbol VARCHAR)")
    # Restliche Tabellen müssen ebenfalls existieren, sonst meldet der
    # Fallback 0. Wir legen sie minimal an.
    for t in ("kline_1min", "orderbook_snapshots",
              "open_interest", "long_short_ratio", "funding_history"):
        conn.execute(f"CREATE TABLE {t} (ts BIGINT, symbol VARCHAR)")
    conn.execute("INSERT INTO trades VALUES (1, 'BTCUSDT')")
    conn.execute("INSERT INTO trades VALUES (2, 'BTCUSDT')")
    try:
        counts = load_row_counts(conn)
        assert "tickers" in counts
        assert "trades" in counts
        assert "liquidations" in counts
        assert "orderbook_snapshots" in counts
        assert counts["trades"] == 2
        assert counts["tickers"] == 0
    finally:
        conn.close()


def test_load_row_counts_uses_persist_method() -> None:
    """Wenn das übergebene Objekt eine ``row_counts()``-Methode hat, wird sie
    bevorzugt verwendet."""

    class FakePersist:
        def row_counts(self) -> dict[str, int]:
            return {"tickers": 7, "trades": 3}

    counts = load_row_counts(FakePersist())
    assert counts == {"tickers": 7, "trades": 3}


# --------------------------------------------------------------------------
# Heartbeat-File
# --------------------------------------------------------------------------

def test_load_heartbeat_file_valid_json(tmp_path: Path) -> None:
    path = tmp_path / "dashboard_state.json"
    payload = {
        "ts": 1748606400.0,
        "symbol": "BTCUSDT",
        "msgs": 42,
        "last_price": 70000.5,
        "mid_price": 70000.7,
        "trade_buffer_len": 10,
        "liq_buffer_len": 1,
        "persisted": 100,
        "position_side": "",
        "mode": "DEMO",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    out = load_heartbeat_file(path)
    assert out is not None
    assert out["symbol"] == "BTCUSDT"
    assert out["msgs"] == 42
    assert out["mode"] == "DEMO"


def test_load_heartbeat_file_missing_returns_none(tmp_path: Path) -> None:
    out = load_heartbeat_file(tmp_path / "no_such.json")
    assert out is None


def test_load_heartbeat_file_invalid_json_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("not valid json{{", encoding="utf-8")
    out = load_heartbeat_file(path)
    assert out is None


# --------------------------------------------------------------------------
# Account-Status (async wrapper, hier mit Stub-Executor)
# --------------------------------------------------------------------------

class _StubExecutor:
    def __init__(self, equity: float = 1234.56) -> None:
        self._equity = equity

    async def get_equity(self) -> float:
        return self._equity

    async def get_position(self) -> dict:
        return {
            "size": 0.01, "side": "Buy",
            "avg_price": 70000.0, "unrealised_pnl": 1.23,
        }


def test_load_account_status_with_stub_executor() -> None:
    out = load_account_status(_StubExecutor(equity=999.99))
    assert out["connected"] is True
    assert out["equity"] == pytest.approx(999.99)
    assert out["position"]["side"] == "Buy"
    assert out["position"]["size"] == pytest.approx(0.01)


def test_load_account_status_with_none() -> None:
    out = load_account_status(None)
    assert out["connected"] is False
    assert out["equity"] == 0.0
    assert "Executor" in out["error"]


def test_load_account_status_handles_executor_error() -> None:
    class _BadExecutor:
        async def get_equity(self) -> float:
            raise RuntimeError("Kein API-Key/Secret gesetzt")

        async def get_position(self) -> dict:
            return {}

    out = load_account_status(_BadExecutor())
    assert out["connected"] is False
    assert "API-Key" in out["error"]


# --------------------------------------------------------------------------
# Regression: "Event loop is closed" beim Streamlit-Auto-Refresh
# --------------------------------------------------------------------------
#
# Bug: Streamlit cachte ``BybitExecutor`` via ``@st.cache_resource`` über
# Reruns hinweg. ``load_account_status`` rief intern ``asyncio.run(...)`` auf;
# der erste Aufruf erzeugte einen ``aiohttp.ClientSession`` gebunden an Loop
# L1, danach wurde L1 geschlossen. Beim nächsten Refresh lief ``asyncio.run``
# in Loop L2, traf aber auf die alte L1-gebundene Session → RuntimeError
# "Event loop is closed".
#
# Der Fix muss garantieren: bei einem ``BybitExecutor`` als Argument wird die
# loop-gebundene Session NICHT über ``asyncio.run``-Iterationen hinweg
# wiederverwendet — pro Aufruf wird ein frischer Executor + Session im selben
# Loop erstellt und sauber geschlossen.


class _FakeBybitExecutor:
    """Emuliert das Loop-Binding-Verhalten von ``aiohttp.ClientSession``.

    Beim ersten Async-Call merkt sich die Instanz den aktuellen Event-Loop.
    Wird sie in einem späteren Aufruf aus einem anderen Loop heraus genutzt,
    wirft sie ``RuntimeError("Event loop is closed")`` — exakt der Live-Fehler.
    """

    instances: list["_FakeBybitExecutor"] = []

    def __init__(self, symbol: str = "BTCUSDT", *_a, **_kw) -> None:
        self.symbol = symbol
        self._bound_loop: asyncio.AbstractEventLoop | None = None
        self.closed = False
        _FakeBybitExecutor.instances.append(self)

    def _check_loop(self) -> None:
        current = asyncio.get_event_loop()
        if self._bound_loop is None:
            self._bound_loop = current
            return
        if self._bound_loop is not current or self._bound_loop.is_closed():
            raise RuntimeError("Event loop is closed")

    async def get_equity(self) -> float:
        self._check_loop()
        return 1234.56

    async def get_position(self) -> dict:
        self._check_loop()
        return {
            "size": 0.0, "side": "",
            "avg_price": 0.0, "unrealised_pnl": 0.0,
        }

    async def close(self) -> None:
        self.closed = True


def test_load_account_status_multiple_refreshes_no_loop_error(monkeypatch) -> None:
    """Simuliert mehrere Streamlit-Reruns (jeweils neues ``asyncio.run``).

    RED vor dem Fix: Wenn die App den gecachten Executor (loop-gebunden an
    den ersten Run) wiederverwendet, schlägt der zweite Refresh mit
    "Event loop is closed" fehl → ``connected=False`` und Error im Result.

    GREEN nach dem Fix: ``load_account_status`` erstellt pro Aufruf einen
    frischen ``BybitExecutor`` im aktuellen Loop, sodass alle 3 Refreshes
    sauber durchlaufen.
    """
    _FakeBybitExecutor.instances.clear()
    monkeypatch.setattr(
        "bybit_edge.dashboard.data.BybitExecutor", _FakeBybitExecutor
    )

    # Erster (cached) Executor — wie ihn ``@st.cache_resource`` in der App
    # liefern würde. Den binden wir bewusst an einen *vorherigen* Loop.
    cached = _FakeBybitExecutor("BTCUSDT")
    prev_loop = asyncio.new_event_loop()
    try:
        prev_loop.run_until_complete(cached.get_equity())
    finally:
        prev_loop.close()
    # Jetzt ist ``cached._bound_loop`` geschlossen — würde direkter Reuse
    # in einer neuen ``asyncio.run``-Iteration den Live-Bug auslösen.

    results = []
    for _ in range(3):
        out = load_account_status(cached)
        results.append(out)

    for out in results:
        assert out["connected"] is True, f"Refresh schlug fehl: {out['error']}"
        assert out["equity"] == pytest.approx(1234.56)
        assert "Event loop is closed" not in out.get("error", "")

    # Pro Refresh wurde ein frischer Executor erzeugt und geschlossen.
    # (cached ist Instanz 0; danach mindestens 3 frische Instanzen.)
    fresh = _FakeBybitExecutor.instances[1:]
    assert len(fresh) >= 3
    assert all(inst.closed for inst in fresh)


def test_load_account_status_closes_fresh_executor_on_error(monkeypatch) -> None:
    """Auch bei Fehlern (z. B. fehlendem API-Key) muss die frische
    Executor-Session geschlossen werden, damit keine offenen aiohttp-
    Sessions zurückbleiben."""

    class _ExplodingExec(_FakeBybitExecutor):
        async def get_equity(self) -> float:
            raise RuntimeError("boom")

    _FakeBybitExecutor.instances.clear()
    monkeypatch.setattr(
        "bybit_edge.dashboard.data.BybitExecutor", _ExplodingExec
    )

    cached = _FakeBybitExecutor("BTCUSDT")
    out = load_account_status(cached)

    assert out["connected"] is False
    assert "boom" in out["error"]
    # Frische Instanz wurde trotz Fehler geschlossen
    fresh = [i for i in _FakeBybitExecutor.instances if i is not cached]
    assert len(fresh) >= 1
    assert all(inst.closed for inst in fresh)


# --------------------------------------------------------------------------
# Hilfsfunktionen
# --------------------------------------------------------------------------

def test_ms_to_iso_handles_none() -> None:
    assert ms_to_iso(None) == ""


def test_ms_to_iso_formats_timestamp() -> None:
    # 2024-01-01T00:00:00Z entspricht 1704067200000 ms
    s = ms_to_iso(1704067200000)
    assert s.startswith("2024-01-01")


# --------------------------------------------------------------------------
# Parquet-Snapshots (Bugfix: DuckDB-Lock-Konflikt mit LiveRunner)
# --------------------------------------------------------------------------

def test_load_row_counts_from_parquet_snapshot(tmp_path: Path) -> None:
    """Wenn ``row_counts.parquet`` existiert, wird es bevorzugt gelesen."""
    df = pd.DataFrame(
        [
            {"table_name": "tickers", "row_count": 42, "exported_at": "2026-06-03"},
            {"table_name": "trades", "row_count": 17, "exported_at": "2026-06-03"},
        ]
    )
    df.to_parquet(tmp_path / "row_counts.parquet")

    out = load_row_counts(persist=None, snapshot_dir=tmp_path)
    assert out == {"tickers": 42, "trades": 17}


def test_load_row_counts_falls_back_to_duckdb(tmp_path: Path) -> None:
    """Existiert KEIN Snapshot, wird der DuckDB-Pfad genutzt."""
    conn = duckdb.connect(":memory:")
    for t in ("tickers", "trades", "liquidations", "kline_1min",
              "orderbook_snapshots", "open_interest",
              "long_short_ratio", "funding_history"):
        conn.execute(f"CREATE TABLE {t} (ts BIGINT, symbol VARCHAR)")
    conn.execute("INSERT INTO trades VALUES (1, 'BTCUSDT')")
    try:
        out = load_row_counts(persist=conn, snapshot_dir=tmp_path)
        assert out["trades"] == 1
        assert out["tickers"] == 0
        # Sanity: kein Snapshot wurde versehentlich geschrieben
        assert not (tmp_path / "row_counts.parquet").exists()
    finally:
        conn.close()


def test_load_recent_liquidations_from_parquet(tmp_path: Path) -> None:
    df = pd.DataFrame(
        [
            {"ts": 1_700_000_002_000, "symbol": "BTCUSDT", "side": "Buy",
             "volume": 1.5, "price": 70000.0, "usd_value": 105000.0},
            {"ts": 1_700_000_001_000, "symbol": "BTCUSDT", "side": "Sell",
             "volume": 0.5, "price": 69990.0, "usd_value": 34995.0},
            {"ts": 1_700_000_003_000, "symbol": "ETHUSDT", "side": "Buy",
             "volume": 10.0, "price": 3000.0, "usd_value": 30000.0},
        ]
    )
    df.to_parquet(tmp_path / "liquidations_recent.parquet")

    # Symbol-Filter respektieren
    out = load_recent_liquidations(persist=None, symbol="BTCUSDT", n=10,
                                   snapshot_dir=tmp_path)
    assert len(out) == 2
    # Sortiert ts DESC
    ts_list = [r["ts"] for r in out]
    assert ts_list == sorted(ts_list, reverse=True)
    assert out[0]["side"] == "Buy"
    assert out[0]["price"] == pytest.approx(70000.0)

    # Limit
    limited = load_recent_liquidations(persist=None, symbol="BTCUSDT", n=1,
                                       snapshot_dir=tmp_path)
    assert len(limited) == 1

    # Alle Symbole
    all_out = load_recent_liquidations(persist=None, symbol=None, n=10,
                                       snapshot_dir=tmp_path)
    assert len(all_out) == 3


def test_load_coverage_returns_per_table_stats(tmp_path: Path) -> None:
    df = pd.DataFrame(
        [
            {"table_name": "tickers", "min_ts": 1_700_000_000_000,
             "max_ts": 1_700_003_600_000, "row_count": 100},
            {"table_name": "trades", "min_ts": None, "max_ts": None,
             "row_count": 0},
        ]
    )
    df.to_parquet(tmp_path / "coverage.parquet")

    out = load_coverage(persist=None, snapshot_dir=tmp_path)
    assert "tickers" in out
    assert out["tickers"]["count"] == 100
    # 3600 seconds = 1 hour
    assert out["tickers"]["hours"] == pytest.approx(1.0)
    assert out["trades"]["count"] == 0
    assert out["trades"]["hours"] == pytest.approx(0.0)
    assert out["trades"]["min_ts"] is None


def test_load_coverage_falls_back_to_duckdb(tmp_path: Path) -> None:
    conn = duckdb.connect(":memory:")
    conn.execute(
        "CREATE TABLE tickers (ts BIGINT, symbol VARCHAR)"
    )
    conn.execute("INSERT INTO tickers VALUES (1700000000000, 'BTCUSDT')")
    conn.execute("INSERT INTO tickers VALUES (1700003600000, 'BTCUSDT')")
    try:
        out = load_coverage(persist=conn, snapshot_dir=tmp_path)
        assert "tickers" in out
        assert out["tickers"]["count"] == 2
        assert out["tickers"]["hours"] == pytest.approx(1.0)
    finally:
        conn.close()


# --------------------------------------------------------------------------
# LiveRunner Dashboard-Snapshot-Export
# --------------------------------------------------------------------------

def test_liverunner_exports_dashboard_snapshots_on_flush(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Beim Flush exportiert der LiveRunner row_counts/liquidations/coverage
    als Parquet — damit das Dashboard ohne DuckDB-Lock-Konflikt liest.
    """
    from bybit_edge import live_runner as lr_mod
    from bybit_edge.persistence.db import PersistenceLayer
    from bybit_edge.state.liquidation_buffer import LiquidationEvent

    # In-Memory-Persistenz + Snapshot-Dir auf tmp_path umlenken
    monkeypatch.setattr(lr_mod, "DASHBOARD_SNAPSHOT_DIR", tmp_path)

    runner = lr_mod.LiveRunner(symbol="BTCUSDT")
    runner.persist = PersistenceLayer(db_path=Path(":memory:"))
    try:
        # Ein paar Liquidationen ins DuckDB schreiben
        evt = LiquidationEvent(
            timestamp_ms=1_700_000_000_000,
            symbol="BTCUSDT",
            side="Buy",
            volume=1.0,
            price=70_000.0,
            usd_value=70_000.0,
        )
        runner._buf_liqs = [evt]

        runner._flush_persist()

        # Snapshots müssen existieren
        for name in ("row_counts.parquet", "liquidations_recent.parquet",
                     "coverage.parquet"):
            assert (tmp_path / name).exists(), f"Snapshot fehlt: {name}"

        # Inhalt grob prüfen
        rc = pd.read_parquet(tmp_path / "row_counts.parquet")
        rc_map = dict(zip(rc["table_name"], rc["row_count"]))
        assert rc_map.get("liquidations", 0) == 1

        liq = pd.read_parquet(tmp_path / "liquidations_recent.parquet")
        assert len(liq) == 1
        assert liq.iloc[0]["symbol"] == "BTCUSDT"
    finally:
        runner.persist.close()


# --------------------------------------------------------------------------
# Strategie-Performance Tab — Replay-Results + Journal-Aggregation
# --------------------------------------------------------------------------

def _wf_payload(symbol: str = "BTCUSDT") -> dict:
    return {
        "symbol": symbol,
        "interval_seconds": 1.0,
        "n_events": 5000,
        "mode": "walkforward",
        "walkforward": {
            "train_days": 7,
            "test_days": 1,
            "embargo_minutes": 30,
            "n_folds_executed": 3,
        },
        "results": [
            {
                "strategy": "S1", "sharpe": 1.42, "win_rate": 0.55,
                "max_dd": 0.08, "total_return": 0.12, "n_trades": 21,
                "data_limited": False,
            },
            {
                "strategy": "S3", "sharpe": 0.80, "win_rate": 0.50,
                "max_dd": 0.04, "total_return": 0.03, "n_trades": 7,
                "data_limited": False,
            },
            {
                "strategy": "S2", "sharpe": 0.0, "win_rate": 0.0,
                "max_dd": 0.0, "total_return": 0.0, "n_trades": 0,
                "data_limited": True,
            },
        ],
    }


def _single_pass_payload(symbol: str = "BTCUSDT") -> dict:
    return {
        "symbol": symbol,
        "interval_seconds": 1.0,
        "n_events": 1234,
        "mode": "single_pass",
        "results": [
            {
                "strategy": "S1", "sharpe": 0.45, "win_rate": 0.51,
                "max_dd": 0.03, "total_return": 0.02, "n_trades": 8,
                "data_limited": False,
            },
        ],
    }


def test_load_replay_results_prefers_walkforward(tmp_path: Path) -> None:
    """Beide JSONs vorhanden → Walk-Forward gewinnt."""
    (tmp_path / "walkforward_results.json").write_text(
        json.dumps(_wf_payload()), encoding="utf-8"
    )
    (tmp_path / "replay_backtest_results.json").write_text(
        json.dumps(_single_pass_payload()), encoding="utf-8"
    )

    out = load_replay_results(results_dir=tmp_path)
    assert out is not None
    assert out["source"] == "walkforward"
    assert out["path"].endswith("walkforward_results.json")
    assert out["symbol"] == "BTCUSDT"
    assert out["n_events"] == 5000
    assert out["walkforward"]["n_folds_executed"] == 3
    # per_strategy enthält alle drei Strategien mit den richtigen Feldern
    assert set(out["per_strategy"].keys()) == {"S1", "S2", "S3"}
    s1 = out["per_strategy"]["S1"]
    assert s1["sharpe"] == pytest.approx(1.42)
    assert s1["win_rate"] == pytest.approx(0.55)
    assert s1["max_drawdown"] == pytest.approx(0.08)
    assert s1["total_return"] == pytest.approx(0.12)
    assert s1["n_trades"] == 21
    assert s1["data_limited"] is False
    assert out["per_strategy"]["S2"]["data_limited"] is True


def test_load_replay_results_fallback_single_pass(tmp_path: Path) -> None:
    """Nur Single-Pass JSON vorhanden → wird genommen, source = single_pass."""
    (tmp_path / "replay_backtest_results.json").write_text(
        json.dumps(_single_pass_payload()), encoding="utf-8"
    )

    out = load_replay_results(results_dir=tmp_path)
    assert out is not None
    assert out["source"] == "single_pass"
    assert out["path"].endswith("replay_backtest_results.json")
    assert out["walkforward"] is None
    assert "S1" in out["per_strategy"]
    assert out["per_strategy"]["S1"]["n_trades"] == 8


def test_load_replay_results_none_when_missing(tmp_path: Path) -> None:
    """Verzeichnis existiert, aber keine JSON drin → None."""
    out = load_replay_results(results_dir=tmp_path)
    assert out is None
    # Auch nicht existierendes Verzeichnis darf nicht crashen
    out2 = load_replay_results(results_dir=tmp_path / "does_not_exist")
    assert out2 is None


def test_load_replay_results_handles_malformed_json(tmp_path: Path) -> None:
    """Kaputte JSON → logging + None, kein Crash."""
    (tmp_path / "walkforward_results.json").write_text(
        "{not valid json,,", encoding="utf-8"
    )
    out = load_replay_results(results_dir=tmp_path)
    assert out is None


def test_load_journal_aggregated_groups_by_strategy(tmp_path: Path) -> None:
    """CSV mit gemischten strategy_ids → korrekt aggregiert pro sid."""
    path = tmp_path / "trades_journal.csv"
    rows = [
        # S1: 3 Trades — 2 enter, 1 exit, 2 erfolgreich (ret_code=0), 1 Fehler
        {"ts_iso": "2026-05-30T12:00:00Z", "ts_unix": 1, "symbol": "BTCUSDT",
         "strategy_id": "S1", "action": "enter", "side": "Buy", "qty": 0.01,
         "price": 70000.0, "confidence": 0.8, "ret_code": 0, "order_id": "a"},
        {"ts_iso": "2026-05-30T12:01:00Z", "ts_unix": 2, "symbol": "BTCUSDT",
         "strategy_id": "S1", "action": "enter", "side": "Buy", "qty": 0.01,
         "price": 70010.0, "confidence": 0.7, "ret_code": 0, "order_id": "b"},
        {"ts_iso": "2026-05-30T12:02:00Z", "ts_unix": 3, "symbol": "BTCUSDT",
         "strategy_id": "S1", "action": "exit", "side": "Sell", "qty": 0.02,
         "price": 70020.0, "confidence": 0.6, "ret_code": 110007,
         "order_id": "c"},
        # S3: 2 Trades — 1 enter, 1 risk_block, 1 erfolgreich
        {"ts_iso": "2026-05-30T12:03:00Z", "ts_unix": 4, "symbol": "BTCUSDT",
         "strategy_id": "S3", "action": "enter", "side": "Sell", "qty": 0.005,
         "price": 70030.0, "confidence": 0.9, "ret_code": 0, "order_id": "d"},
        {"ts_iso": "2026-05-30T12:04:00Z", "ts_unix": 5, "symbol": "BTCUSDT",
         "strategy_id": "S3", "action": "risk_block", "side": "", "qty": 0.0,
         "price": 0.0, "confidence": 0.0, "ret_code": -1, "order_id": ""},
    ]
    pd.DataFrame(rows).to_csv(path, index=False)

    agg = load_journal_aggregated(path)
    assert set(agg.keys()) == {"S1", "S3"}
    assert agg["S1"]["n_total"] == 3
    assert agg["S1"]["n_enter"] == 2
    assert agg["S1"]["n_exit"] == 1
    assert agg["S1"]["n_risk_block"] == 0
    assert agg["S1"]["n_success"] == 2
    assert agg["S3"]["n_total"] == 2
    assert agg["S3"]["n_enter"] == 1
    assert agg["S3"]["n_risk_block"] == 1
    assert agg["S3"]["n_exit"] == 0
    assert agg["S3"]["n_success"] == 1


def test_load_journal_aggregated_empty_csv(tmp_path: Path) -> None:
    """Leeres oder fehlendes CSV → leeres dict."""
    # Pfad None
    assert load_journal_aggregated(None) == {}
    # Datei existiert nicht
    assert load_journal_aggregated(tmp_path / "no.csv") == {}
    # Datei existiert aber ist leer (nur Header)
    p = tmp_path / "empty.csv"
    pd.DataFrame(columns=JOURNAL_COLUMNS).to_csv(p, index=False)
    assert load_journal_aggregated(p) == {}
