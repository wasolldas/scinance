"""
Tests für :class:`bybit_edge._legacy_v1.multi_runner.MultiSymbolRunner`.

Alle Tests sind netzwerk-frei — wir testen Orchestrierung und Lebenszyklus,
nicht echte WS-Connections. Wo nötig wird die ``run``/``stop``-Methode der
einzelnen :class:`LiveRunner` gemockt.
"""
from __future__ import annotations

import asyncio
import pathlib
from unittest.mock import AsyncMock, patch

import pytest

from bybit_edge._legacy_v1.live_runner import LiveRunner
from bybit_edge._legacy_v1.multi_runner import MultiSymbolRunner
from bybit_edge.persistence.db import PersistenceLayer


# ──────────────────────────────────────────────────────────────────
# Konstruktor-Validierung
# ──────────────────────────────────────────────────────────────────


class TestMultiSymbolRunnerInit:
    def test_init_validates_non_empty_symbols(self, monkeypatch):
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", False)
        with pytest.raises(ValueError):
            MultiSymbolRunner([])

    def test_init_validates_unique_symbols(self, monkeypatch):
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", False)
        with pytest.raises(ValueError):
            MultiSymbolRunner(["BTCUSDT", "ETHUSDT", "BTCUSDT"])

    def test_init_rejects_empty_symbol_entry(self, monkeypatch):
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", False)
        with pytest.raises(ValueError):
            MultiSymbolRunner(["BTCUSDT", "  "])

    def test_creates_one_liverunner_per_symbol(self, monkeypatch):
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", False)
        m = MultiSymbolRunner(["BTCUSDT", "ETHUSDT", "SOLUSDT"])
        assert len(m.runners) == 3
        assert all(isinstance(r, LiveRunner) for r in m.runners)
        assert [r.symbol for r in m.runners] == ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


# ──────────────────────────────────────────────────────────────────
# Geteilte Persistenz
# ──────────────────────────────────────────────────────────────────


class TestSharedPersistence:
    def test_shared_persist_layer_when_enabled(self, monkeypatch):
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", True)
        # In-Memory-DuckDB, damit der Test keine Disk-IO braucht.
        with patch(
            "bybit_edge._legacy_v1.multi_runner.PersistenceLayer",
            lambda: PersistenceLayer(db_path=pathlib.Path(":memory:")),
        ):
            m = MultiSymbolRunner(["BTCUSDT", "ETHUSDT"])
            assert m.persist is not None
            # Alle Runner zeigen identisch auf die gemeinsame Schicht.
            for r in m.runners:
                assert r._shared_persist is m.persist
                assert r._owns_persist is False
            m.persist.close()

    def test_no_persist_when_disabled(self, monkeypatch):
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", False)
        m = MultiSymbolRunner(["BTCUSDT", "ETHUSDT"])
        assert m.persist is None
        for r in m.runners:
            assert r._shared_persist is None
            # Ownership-Flag liegt beim Runner selbst (würde in run() Persistenz öffnen).
            assert r._owns_persist is True


# ──────────────────────────────────────────────────────────────────
# Execution-Auflösung
# ──────────────────────────────────────────────────────────────────


class TestExecutionAssignment:
    def test_execution_only_on_execution_symbol(self, monkeypatch):
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", False)
        m = MultiSymbolRunner(["BTCUSDT", "ETHUSDT"], execution_symbol="BTCUSDT")
        assert m.execution_symbol == "BTCUSDT"
        runners_by_sym = {r.symbol: r for r in m.runners}
        # None (not True!) for the execution_symbol: a hardcoded True would
        # bypass the EXECUTION_ENABLED master switch entirely, since
        # LiveRunner._execution_active() only consults EXECUTION_ENABLED when
        # the override is None. False for every other symbol hard-disables
        # them regardless of EXECUTION_ENABLED (only one symbol may ever
        # execute).
        assert runners_by_sym["BTCUSDT"]._execution_override is None
        assert runners_by_sym["ETHUSDT"]._execution_override is False

    def test_execution_symbol_still_gated_by_execution_enabled(self, monkeypatch):
        """Regression test for the critical bypass found by the second
        adversarial review round: even the designated execution_symbol's
        runner must stay OFF when the global EXECUTION_ENABLED master switch
        is False -- MultiSymbolRunner must never force execution on."""
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", False)
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ENABLED", False)
        m = MultiSymbolRunner(["BTCUSDT", "ETHUSDT"], execution_symbol="BTCUSDT")
        runners_by_sym = {r.symbol: r for r in m.runners}
        assert runners_by_sym["BTCUSDT"]._execution_active() is False
        assert runners_by_sym["ETHUSDT"]._execution_active() is False

    def test_execution_symbol_active_when_execution_enabled_true(self, monkeypatch):
        """Complementary case: with the master switch ON, exactly the
        execution_symbol's runner is active, no other."""
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", False)
        monkeypatch.setattr("bybit_edge._legacy_v1.live_runner.EXECUTION_ENABLED", True)
        m = MultiSymbolRunner(["BTCUSDT", "ETHUSDT"], execution_symbol="BTCUSDT")
        runners_by_sym = {r.symbol: r for r in m.runners}
        assert runners_by_sym["BTCUSDT"]._execution_active() is True
        assert runners_by_sym["ETHUSDT"]._execution_active() is False

    def test_execution_symbol_not_in_list_logs_warning_and_no_execution(
        self, monkeypatch, caplog
    ):
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", False)
        with caplog.at_level("WARNING", logger="bybit_edge._legacy_v1.multi_runner"):
            m = MultiSymbolRunner(
                ["BTCUSDT", "ETHUSDT"], execution_symbol="DOGEUSDT"
            )
        assert m.execution_symbol is None
        for r in m.runners:
            assert r._execution_override is False
        assert any("DOGEUSDT" in rec.message for rec in caplog.records)

    def test_default_execution_falls_back_to_primary(self, monkeypatch):
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", False)
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PRIMARY_SYMBOL", "BTCUSDT")
        m = MultiSymbolRunner(["BTCUSDT", "ETHUSDT"])
        assert m.execution_symbol == "BTCUSDT"

    def test_default_execution_none_if_primary_missing(self, monkeypatch):
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", False)
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PRIMARY_SYMBOL", "BTCUSDT")
        m = MultiSymbolRunner(["ETHUSDT", "SOLUSDT"])
        assert m.execution_symbol is None
        for r in m.runners:
            assert r._execution_override is False


# ──────────────────────────────────────────────────────────────────
# Lebenszyklus
# ──────────────────────────────────────────────────────────────────


class TestLifecycle:
    def test_stop_closes_shared_persist_only_once(self, monkeypatch):
        """Geteilte DuckDB-Connection darf in stop() genau einmal geschlossen werden."""
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", True)

        with patch(
            "bybit_edge._legacy_v1.multi_runner.PersistenceLayer",
            lambda: PersistenceLayer(db_path=pathlib.Path(":memory:")),
        ):
            m = MultiSymbolRunner(["BTCUSDT", "ETHUSDT"])

            shared = m.persist
            assert shared is not None
            close_calls = {"n": 0}
            original_close = shared.close

            def _counted_close():
                close_calls["n"] += 1
                original_close()

            shared.close = _counted_close  # type: ignore[method-assign]

            # Die Runner haben noch nichts gestartet → ihre persist-Attribute
            # sind None. Wir markieren _running, damit stop() echten Pfad nimmt.
            m._running = True
            for r in m.runners:
                r._running = False  # disconnect() läuft trotzdem ok
                # Sicherstellen, dass kein Runner doppelt schließt:
                r.persist = None  # nichts zum lokalen Flush

            asyncio.run(m.stop())
            assert close_calls["n"] == 1
            assert m.persist is None

    def test_run_dispatches_to_all_runners(self, monkeypatch):
        monkeypatch.setattr("bybit_edge._legacy_v1.multi_runner.PERSIST_ENABLED", False)
        m = MultiSymbolRunner(["BTCUSDT", "ETHUSDT"])

        # Jeder LiveRunner.run wird durch einen sofort-fertigen Coroutine ersetzt,
        # stop ebenso. Wir prüfen nur, dass die Orchestrierung greift.
        for r in m.runners:
            r.run = AsyncMock(return_value=None)  # type: ignore[method-assign]
            r.stop = AsyncMock(return_value=None)  # type: ignore[method-assign]

        asyncio.run(m.run())
        for r in m.runners:
            r.run.assert_awaited_once()
            r.stop.assert_awaited_once()


# ──────────────────────────────────────────────────────────────────
# Backward-Kompatibilität des LiveRunner-Defaults
# ──────────────────────────────────────────────────────────────────


class TestLiveRunnerBackwardCompat:
    def test_default_liverunner_unchanged_without_args(self):
        """``LiveRunner("BTCUSDT")`` ohne neue Args muss bit-identisch sein."""
        r = LiveRunner("BTCUSDT")
        assert r._shared_persist is None
        assert r._owns_persist is True
        assert r._execution_override is None
        # Symbol-Pfad unverändert:
        assert r.symbol == "BTCUSDT"
        assert r.persist is None
