"""
Unit-Tests für ``persistence/backfill.py`` (BackfillManager).

Alle Tests sind netzwerkfrei: ``urllib.request.urlopen`` wird via
Monkey-Patch durch eine sequenzielle Mock-Response ersetzt. Damit lassen
sich Bybit-V5-Payloads exakt simulieren (Pagination, leere Responses,
Feldnamen wie ``fundingRateTimestamp``, ``intervalTime``-Parameter usw.).
"""
from __future__ import annotations

import io
import json
import time
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qs, urlparse

import pytest

from bybit_edge._legacy_v1.persistence import backfill as backfill_mod
from bybit_edge._legacy_v1.persistence.backfill import BackfillManager
from bybit_edge.persistence.db import PersistenceLayer


# ----------------------------------------------------------------------
# Mock-Helper
# ----------------------------------------------------------------------

class _FakeResp:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._buf = io.BytesIO(json.dumps(payload).encode())

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self._buf.close()

    def read(self) -> bytes:
        return self._buf.getvalue()


def make_urlopen_mock(
    responses: Iterable[dict[str, Any]],
    capture: list[str] | None = None,
):
    """Liefert eine Mock-``urlopen``-Funktion.

    ``responses`` ist eine Sequenz von Bybit-V5-konformen Body-Dicts. Sie
    werden in Reihenfolge bei jedem Call zurückgegeben. Sobald die Liste
    leer ist, wird eine leere ``result.list`` Response zurückgegeben — das
    löst alle "natural stop"-Bedingungen aus.

    Optional sammelt ``capture`` die aufgerufenen URLs als Strings.
    """
    queue = list(responses)

    def _urlopen(url: str, timeout: int = 15) -> _FakeResp:  # noqa: ARG001
        if capture is not None:
            capture.append(url)
        if queue:
            return _FakeResp(queue.pop(0))
        return _FakeResp({"result": {"list": []}})

    return _urlopen


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Schaltet die Rate-Limit-Sleeps für die Tests aus."""
    monkeypatch.setattr(time, "sleep", lambda _s: None)


@pytest.fixture()
def mem_db() -> Iterable[PersistenceLayer]:
    db = PersistenceLayer(db_path=Path(":memory:"))
    try:
        yield db
    finally:
        db.close()


# ----------------------------------------------------------------------
# Synthetische Bybit-V5-Payloads
# ----------------------------------------------------------------------

def _kline_page(start_ts: int, n: int, step_ms: int = 60_000) -> dict[str, Any]:
    """Bybit liefert DESC. ``start_ts`` = ältester Bar in der Page."""
    rows = []
    for i in range(n):
        ts = start_ts + i * step_ms
        rows.append([
            str(ts),
            "100.0", "101.0", "99.0", "100.5",
            "1.5", "150.0",
        ])
    rows.reverse()  # DESC (neuester zuerst)
    return {"result": {"list": rows}}


def _funding_page(start_ts: int, n: int, step_ms: int = 8 * 3600 * 1000) -> dict[str, Any]:
    items = []
    for i in range(n):
        ts = start_ts + i * step_ms
        items.append({
            "symbol": "BTCUSDT",
            "fundingRate": "0.0001",
            "fundingRateTimestamp": str(ts),
        })
    items.reverse()
    return {"result": {"list": items}}


def _oi_page(start_ts: int, n: int, step_ms: int = 5 * 60 * 1000) -> dict[str, Any]:
    items = []
    for i in range(n):
        ts = start_ts + i * step_ms
        items.append({
            "openInterest": "12345.6",
            "timestamp": str(ts),
        })
    items.reverse()
    return {"result": {"list": items, "nextPageCursor": ""}}


def _ls_page(start_ts: int, n: int, step_ms: int = 5 * 60 * 1000) -> dict[str, Any]:
    items = []
    for i in range(n):
        ts = start_ts + i * step_ms
        items.append({
            "buyRatio": "0.55",
            "sellRatio": "0.45",
            "timestamp": str(ts),
        })
    items.reverse()
    return {"result": {"list": items}}


# ======================================================================
# Tests
# ======================================================================

class TestKlineBackfill:

    def test_backfill_klines_writes_rows(
        self, mem_db: PersistenceLayer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Ein-Seiten-Mock → DB enthält genau die erwartete Zeilenzahl."""
        now_ms = int(time.time() * 1000)
        # One small page below the limit => loop terminates after one call
        page = _kline_page(now_ms - 5 * 60_000, n=5)
        monkeypatch.setattr(
            backfill_mod.urllib.request, "urlopen",
            make_urlopen_mock([page]),
        )
        mgr = BackfillManager(persist=mem_db)
        n = mgr.backfill_klines("BTCUSDT", interval="1", months=1)
        assert n == 5
        assert mem_db.count_klines("BTCUSDT") == 5

    def test_backfill_klines_pagination_walks_back(
        self, mem_db: PersistenceLayer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Drei Seiten à 1000 Klines → alle 3000 in DB, korrekte Cursor-Rückwärts-Logik."""
        now_ms = int(time.time() * 1000)
        # Make sure each page is full (1000 rows) so pagination continues.
        page1 = _kline_page(now_ms - 1000 * 60_000, 1000)
        page2 = _kline_page(now_ms - 2000 * 60_000, 1000)
        page3 = _kline_page(now_ms - 3000 * 60_000, 500)  # last page < limit
        monkeypatch.setattr(
            backfill_mod.urllib.request, "urlopen",
            make_urlopen_mock([page1, page2, page3]),
        )
        mgr = BackfillManager(persist=mem_db)
        n = mgr.backfill_klines("BTCUSDT", interval="1", months=6)
        assert n == 2500
        assert mem_db.count_klines("BTCUSDT") == 2500

    def test_backfill_klines_skip_if_exists(
        self, mem_db: PersistenceLayer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Backfill für (symbol, interval) bereits im Manifest als
        abgeschlossen markiert → keine API-Calls, return 0."""
        mem_db.write_kline(
            ts=1, symbol="BTCUSDT", open_=1.0, high=1.0, low=1.0,
            close=1.0, volume=1.0, turnover=1.0,
        )
        mem_db.record_kline_backfill("BTCUSDT", "1", row_count=1)
        called: list[str] = []
        monkeypatch.setattr(
            backfill_mod.urllib.request, "urlopen",
            make_urlopen_mock([], capture=called),
        )
        mgr = BackfillManager(persist=mem_db)
        n = mgr.backfill_klines("BTCUSDT", interval="1", months=1)
        assert n == 0
        assert called == []  # kein einziger Call

    def test_backfill_klines_different_interval_not_skipped(
        self, mem_db: PersistenceLayer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Regression: ein Backfill von Intervall '5' (5-Minuten-Klines) darf
        einen SPÄTEREN Backfill von Intervall '1' für dasselbe Symbol NICHT
        als "bereits vorhanden" überspringen — ``kline_1min`` hat keine
        Interval-Spalte, ein reiner Row-Count wäre granularitäts-blind
        (silent-data-loss-wrong-granularity, CRITICAL_REVIEW_2_2026-07-13.md).
        """
        now_ms = int(time.time() * 1000)
        # Erster Lauf: Intervall "5" -> Manifest-Eintrag für ("BTCUSDT", "5").
        page5 = _kline_page(now_ms - 5 * 5 * 60_000, n=5, step_ms=5 * 60_000)
        monkeypatch.setattr(
            backfill_mod.urllib.request, "urlopen",
            make_urlopen_mock([page5]),
        )
        mgr = BackfillManager(persist=mem_db)
        n5 = mgr.backfill_klines("BTCUSDT", interval="5", months=1)
        assert n5 == 5
        assert mem_db.kline_backfill_complete("BTCUSDT", "5") is True
        assert mem_db.kline_backfill_complete("BTCUSDT", "1") is False

        # Zweiter Lauf: Intervall "1" für dasselbe Symbol -> MUSS echte
        # API-Calls auslösen (nicht durch den "5"-Manifest-Eintrag skippen).
        called: list[str] = []
        page1 = _kline_page(now_ms - 5 * 60_000, n=5, step_ms=60_000)
        monkeypatch.setattr(
            backfill_mod.urllib.request, "urlopen",
            make_urlopen_mock([page1], capture=called),
        )
        n1 = mgr.backfill_klines("BTCUSDT", interval="1", months=1)
        assert n1 == 5
        assert called, "Intervall '1' wurde fälschlich durch '5' geskippt"
        assert mem_db.kline_backfill_complete("BTCUSDT", "1") is True

    def test_backfill_klines_not_recorded_complete_on_exception(
        self, mem_db: PersistenceLayer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Bricht der HTTP-Call mit einer Exception ab, darf der Backfill
        NICHT im Manifest als abgeschlossen markiert werden (sonst würde ein
        späterer Retry fälschlich übersprungen)."""

        def _boom(url: str, timeout: int = 15):  # noqa: ARG001
            raise TimeoutError("simulated network failure")

        monkeypatch.setattr(backfill_mod.urllib.request, "urlopen", _boom)
        mgr = BackfillManager(persist=mem_db)
        with pytest.raises(TimeoutError):
            mgr.backfill_klines("BTCUSDT", interval="1", months=1)
        assert mem_db.kline_backfill_complete("BTCUSDT", "1") is False


class TestFundingBackfill:

    def test_backfill_funding_field_names(
        self, mem_db: PersistenceLayer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``fundingRateTimestamp`` und ``fundingRate`` müssen korrekt geparst werden."""
        now_ms = int(time.time() * 1000)
        page = _funding_page(now_ms - 8 * 3600 * 1000, n=3)
        monkeypatch.setattr(
            backfill_mod.urllib.request, "urlopen",
            make_urlopen_mock([page]),
        )
        mgr = BackfillManager(persist=mem_db)
        n = mgr.backfill_funding("BTCUSDT", months=1)
        assert n == 3
        rows = mem_db.conn.execute(
            "SELECT ts, funding_rate FROM funding_history WHERE symbol = ? ORDER BY ts",
            ["BTCUSDT"],
        ).fetchall()
        assert len(rows) == 3
        assert all(abs(r[1] - 0.0001) < 1e-12 for r in rows)


class TestOpenInterestBackfill:

    def test_backfill_open_interest_uses_intervalTime_param(
        self, mem_db: PersistenceLayer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Die URL muss den Parameter ``intervalTime`` enthalten (nicht ``interval``)."""
        now_ms = int(time.time() * 1000)
        page = _oi_page(now_ms - 5 * 60_000, n=4)
        captured: list[str] = []
        monkeypatch.setattr(
            backfill_mod.urllib.request, "urlopen",
            make_urlopen_mock([page], capture=captured),
        )
        mgr = BackfillManager(persist=mem_db)
        n = mgr.backfill_open_interest("BTCUSDT", interval_tag="5min", months=1)
        assert n == 4
        assert captured, "Es wurde mindestens ein HTTP-Call erwartet."
        qs = parse_qs(urlparse(captured[0]).query)
        assert "intervalTime" in qs
        assert qs["intervalTime"] == ["5min"]
        assert "interval" not in qs  # Bybit V5 unterscheidet hier!


class TestLongShortBackfill:

    def test_backfill_long_short_uses_period_param(
        self, mem_db: PersistenceLayer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Der URL-Parameter muss ``period`` heißen."""
        now_ms = int(time.time() * 1000)
        page = _ls_page(now_ms - 5 * 60_000, n=6)
        captured: list[str] = []
        monkeypatch.setattr(
            backfill_mod.urllib.request, "urlopen",
            make_urlopen_mock([page], capture=captured),
        )
        mgr = BackfillManager(persist=mem_db)
        n = mgr.backfill_long_short_ratio("BTCUSDT", period="5min", months=1)
        assert n == 6
        assert captured
        qs = parse_qs(urlparse(captured[0]).query)
        assert qs.get("period") == ["5min"]
        # Werte korrekt persistiert?
        rows = mem_db.conn.execute(
            "SELECT buy_ratio, sell_ratio, period_tag FROM long_short_ratio",
        ).fetchall()
        assert len(rows) == 6
        assert all(abs(r[0] - 0.55) < 1e-9 for r in rows)
        assert all(abs(r[1] - 0.45) < 1e-9 for r in rows)
        assert all(r[2] == "5min" for r in rows)


class TestBackfillAll:

    def test_backfill_all_returns_dict_per_source(
        self, mem_db: PersistenceLayer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``backfill_all`` liefert Counts pro Source und füllt jeweils die DB."""
        now_ms = int(time.time() * 1000)
        # In dieser Reihenfolge: klines, funding, oi, ls
        pages = [
            _kline_page(now_ms - 3 * 60_000, n=3),
            _funding_page(now_ms - 8 * 3600 * 1000, n=2),
            _oi_page(now_ms - 5 * 60_000, n=4),
            _ls_page(now_ms - 5 * 60_000, n=5),
        ]
        monkeypatch.setattr(
            backfill_mod.urllib.request, "urlopen",
            make_urlopen_mock(pages),
        )
        mgr = BackfillManager(persist=mem_db)
        result = mgr.backfill_all("BTCUSDT", months=1)
        assert set(result.keys()) == {
            "klines", "funding", "open_interest", "long_short_ratio",
        }
        assert result["klines"] == 3
        assert result["funding"] == 2
        assert result["open_interest"] == 4
        assert result["long_short_ratio"] == 5

    def test_backfill_universe_iterates_symbols(
        self, mem_db: PersistenceLayer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Universum mit 2 Symbolen → beide werden befragt und persistiert."""
        now_ms = int(time.time() * 1000)
        # 2 Symbole × 4 Sources = 8 Pages.
        pages: list[dict[str, Any]] = []
        for _ in range(2):
            pages.extend([
                _kline_page(now_ms - 60_000, n=1),
                _funding_page(now_ms - 8 * 3600 * 1000, n=1),
                _oi_page(now_ms - 5 * 60_000, n=1),
                _ls_page(now_ms - 5 * 60_000, n=1),
            ])
        captured: list[str] = []
        monkeypatch.setattr(
            backfill_mod.urllib.request, "urlopen",
            make_urlopen_mock(pages, capture=captured),
        )
        mgr = BackfillManager(persist=mem_db)
        result = mgr.backfill_universe(["BTCUSDT", "ETHUSDT"], months=1)
        assert set(result.keys()) == {"BTCUSDT", "ETHUSDT"}
        # Jedes Symbol hat alle 4 Sources mit je 1 Zeile.
        for sym in ("BTCUSDT", "ETHUSDT"):
            assert result[sym]["klines"] == 1
            assert result[sym]["funding"] == 1
            assert result[sym]["open_interest"] == 1
            assert result[sym]["long_short_ratio"] == 1
        # Mindestens ein Call pro Symbol erkennbar.
        joined = "\n".join(captured)
        assert "BTCUSDT" in joined
        assert "ETHUSDT" in joined


class TestEdgeCases:

    def test_backfill_handles_empty_response(
        self, mem_db: PersistenceLayer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Leere Response (``result.list = []``) → 0, kein Crash."""
        monkeypatch.setattr(
            backfill_mod.urllib.request, "urlopen",
            make_urlopen_mock([{"result": {"list": []}}]),
        )
        mgr = BackfillManager(persist=mem_db)
        assert mgr.backfill_klines("BTCUSDT", months=1) == 0
        assert mgr.backfill_funding("BTCUSDT", months=1) == 0
        assert mgr.backfill_open_interest("BTCUSDT", months=1) == 0
        assert mgr.backfill_long_short_ratio("BTCUSDT", months=1) == 0

    def test_row_counts_includes_new_tables(self, mem_db: PersistenceLayer) -> None:
        """``row_counts()`` listet die neuen Tabellen mit auf."""
        counts = mem_db.row_counts()
        assert "open_interest" in counts
        assert "long_short_ratio" in counts
        assert "funding_history" in counts
        # Initial alle 0.
        assert counts["open_interest"] == 0
        assert counts["long_short_ratio"] == 0
        assert counts["funding_history"] == 0

        # Nach einem Insert hochzählen.
        mem_db.write_funding_history_batch([
            {"ts": 1_700_000_000_000, "symbol": "BTCUSDT", "funding_rate": 0.0001},
        ])
        mem_db.write_open_interest_batch([
            {"ts": 1_700_000_000_000, "symbol": "BTCUSDT",
             "open_interest": 1000.0, "interval_tag": "5min"},
        ])
        mem_db.write_long_short_ratio_batch([
            {"ts": 1_700_000_000_000, "symbol": "BTCUSDT",
             "buy_ratio": 0.6, "sell_ratio": 0.4, "period_tag": "5min"},
        ])
        counts = mem_db.row_counts()
        assert counts["funding_history"] == 1
        assert counts["open_interest"] == 1
        assert counts["long_short_ratio"] == 1


# ======================================================================
# scripts/backfill.py CLI — per-Symbol Resilienz
# ======================================================================
#
# Regression für silent-data-loss-partial-backfill (CRITICAL_REVIEW_2_
# 2026-07-13.md, scripts/backfill.py:134): main()'s Symbol-Schleife hatte
# nur try/finally (kein except) um den Runner-Call — ein Netzwerkfehler bei
# EINEM Symbol brach das gesamte Script ab und die restlichen Symbole
# wurden nie verarbeitet.

class TestBackfillCLIResilience:
    def test_main_continues_after_per_symbol_failure(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture,
    ) -> None:
        """Ein fehlschlagendes Symbol darf die übrigen Symbole nicht
        verhindern; der Exit-Code muss den Teil-Fehlschlag widerspiegeln."""
        import sys
        from types import SimpleNamespace

        import archive.v1_scripts.backfill as backfill_cli

        attempted: list[str] = []

        class _FakeMgr:
            def __init__(self) -> None:
                self.persist = SimpleNamespace(row_counts=lambda: {"kline_1min": 0})

            def backfill_all(self, sym: str, **_kwargs: Any) -> dict[str, int]:
                attempted.append(sym)
                if sym == "ETHUSDT":
                    raise TimeoutError("simulated network failure")
                return {
                    "klines": 1, "funding": 1,
                    "open_interest": 1, "long_short_ratio": 1,
                }

            def close(self) -> None:
                pass

        monkeypatch.setattr(backfill_cli, "BackfillManager", lambda: _FakeMgr())
        monkeypatch.setattr(
            sys, "argv",
            ["backfill.py", "--symbols", "BTCUSDT,ETHUSDT,SOLUSDT", "--what", "all"],
        )
        rc = backfill_cli.main()

        # Alle drei Symbole wurden versucht — ETHUSDT's Fehler hat die
        # Schleife NICHT abgebrochen.
        assert attempted == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        # Teil-Fehlschlag -> abweichender Exit-Code (nicht rc=0 wie bei einem
        # vollständigen Lauf).
        assert rc == 1
        captured = capsys.readouterr()
        assert "ETHUSDT" in captured.out
        assert "FEHLER" in captured.out

    def test_main_returns_zero_when_all_symbols_succeed(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Kein Fehlschlag -> rc=0 (Backcompat mit bisherigem Verhalten)."""
        import sys
        from types import SimpleNamespace

        import archive.v1_scripts.backfill as backfill_cli

        class _FakeMgr:
            def __init__(self) -> None:
                self.persist = SimpleNamespace(row_counts=lambda: {"kline_1min": 0})

            def backfill_all(self, sym: str, **_kwargs: Any) -> dict[str, int]:
                return {
                    "klines": 1, "funding": 1,
                    "open_interest": 1, "long_short_ratio": 1,
                }

            def close(self) -> None:
                pass

        monkeypatch.setattr(backfill_cli, "BackfillManager", lambda: _FakeMgr())
        monkeypatch.setattr(
            sys, "argv",
            ["backfill.py", "--symbols", "BTCUSDT,ETHUSDT", "--what", "all"],
        )
        rc = backfill_cli.main()
        assert rc == 0
