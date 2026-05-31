"""Tests für die Live-Risiko-Budget-Schicht (``bybit_edge.risk.budget``).

Alle Tests sind netzwerkfrei und schreiben in ``tmp_path``.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest

from bybit_edge.risk.budget import RiskBudget, RiskState


def _make_budget(
    tmp_path,
    *,
    daily_loss_pct: float = -0.03,
    max_dd_pct: float = -0.15,
    vol_scaling_enabled: bool = False,
    vol_target_bps: float = 50.0,
    vol_lookback_bars: int = 60,
) -> RiskBudget:
    return RiskBudget(
        daily_loss_pct=daily_loss_pct,
        max_dd_pct=max_dd_pct,
        vol_scaling_enabled=vol_scaling_enabled,
        vol_target_bps=vol_target_bps,
        state_path=tmp_path / "risk_state.json",
        vol_lookback_bars=vol_lookback_bars,
    )


class TestLoadSave:
    def test_load_initializes_from_equity(self, tmp_path):
        rb = _make_budget(tmp_path)
        rb.load(current_equity=1000.0)
        assert rb.state is not None
        assert rb.state.daily_start_equity == 1000.0
        assert rb.state.peak_equity == 1000.0
        assert rb.state.realized_pnl_today == 0.0
        assert rb.state.blocked_reason == ""
        assert rb.state.daily_start_utc_date == datetime.now(timezone.utc).date().isoformat()
        # save() wurde automatisch aufgerufen
        assert (tmp_path / "risk_state.json").exists()

    def test_load_existing_state(self, tmp_path):
        state_path = tmp_path / "risk_state.json"
        payload = {
            "daily_start_equity": 900.0,
            "daily_start_utc_date": datetime.now(timezone.utc).date().isoformat(),
            "peak_equity": 1200.0,
            "realized_pnl_today": -50.0,
            "blocked_reason": "",
        }
        state_path.write_text(json.dumps(payload), encoding="utf-8")
        rb = _make_budget(tmp_path)
        rb.load(current_equity=1100.0)
        assert rb.state is not None
        # peak bleibt (1200 > 1100), daily_start unverändert
        assert rb.state.peak_equity == 1200.0
        assert rb.state.daily_start_equity == 900.0
        assert rb.state.realized_pnl_today == -50.0

    def test_save_writes_json(self, tmp_path):
        rb = _make_budget(tmp_path)
        rb.load(current_equity=500.0)
        # mutieren und erneut speichern
        rb.state.peak_equity = 1500.0
        rb.save()
        loaded = json.loads((tmp_path / "risk_state.json").read_text(encoding="utf-8"))
        assert loaded["peak_equity"] == 1500.0
        # Round-Trip via RiskState
        rs = RiskState.from_dict(loaded)
        assert rs.peak_equity == 1500.0


class TestDayRollover:
    def test_daily_rollover_resets_daily_start_only(self, tmp_path):
        rb = _make_budget(tmp_path)
        rb.load(current_equity=1000.0)
        # Peak höher setzen + Vortag eintragen
        rb.state.peak_equity = 1500.0
        rb.state.daily_start_utc_date = "2000-01-01"
        rb.state.realized_pnl_today = -120.0
        rb.save()

        # heute = jetzt; on_equity_update sollte rollovern
        rb.on_equity_update(equity=1100.0, now_utc=datetime(2099, 6, 1, 12, 0, tzinfo=timezone.utc))
        assert rb.state.daily_start_utc_date == "2099-06-01"
        assert rb.state.daily_start_equity == 1100.0
        assert rb.state.realized_pnl_today == 0.0
        # peak unverändert
        assert rb.state.peak_equity == 1500.0


class TestEntryBlocks:
    def test_daily_loss_limit_blocks_entries(self, tmp_path):
        rb = _make_budget(tmp_path, daily_loss_pct=-0.03)
        rb.load(current_equity=1000.0)
        # Verlust 4% > 3%
        rb.on_equity_update(equity=960.0)
        assert rb.state.blocked_reason == "daily_loss"
        allowed, reason = rb.check_entry_allowed(0.1)
        assert allowed is False
        assert reason == "daily_loss"
        # Max-DD greift hier NICHT
        assert rb.should_force_close() is False

    def test_max_dd_blocks_and_force_close(self, tmp_path):
        rb = _make_budget(tmp_path, daily_loss_pct=-0.50, max_dd_pct=-0.15)
        rb.load(current_equity=1000.0)
        # Peak hochziehen
        rb.on_equity_update(equity=2000.0)
        # Drop > 15% vom Peak
        rb.on_equity_update(equity=1600.0)
        assert rb.state.blocked_reason == "max_drawdown"
        assert rb.should_force_close() is True
        allowed, reason = rb.check_entry_allowed(0.1)
        assert allowed is False
        assert reason == "max_drawdown"


class TestRecovery:
    def test_recovery_resets_block(self, tmp_path):
        rb = _make_budget(tmp_path, daily_loss_pct=-0.03)
        rb.load(current_equity=1000.0)
        rb.state.peak_equity = 1000.0
        # Block setzen
        rb.on_equity_update(equity=950.0)
        assert rb.state.blocked_reason == "daily_loss"

        # Recovery: neuer Tag + equity >= 0.95 * peak
        rb.state.daily_start_utc_date = "2000-01-01"
        ok = rb.reset_if_recovered(current_equity=970.0)
        assert ok is True
        assert rb.state.blocked_reason == ""
        # Daily-Start wurde auf neue Equity gesetzt
        assert rb.state.daily_start_equity == 970.0
        assert rb.state.realized_pnl_today == 0.0

    def test_recovery_requires_new_day(self, tmp_path):
        rb = _make_budget(tmp_path, daily_loss_pct=-0.03)
        rb.load(current_equity=1000.0)
        rb.on_equity_update(equity=950.0)
        assert rb.state.blocked_reason == "daily_loss"
        # Selber Tag → keine Recovery, auch wenn Equity wieder hoch ist
        ok = rb.reset_if_recovered(current_equity=1000.0)
        assert ok is False
        assert rb.state.blocked_reason == "daily_loss"


class TestVolScaling:
    def test_vol_scaling_increases_qty_in_calm(self, tmp_path):
        rb = _make_budget(
            tmp_path,
            vol_scaling_enabled=True,
            vol_target_bps=50.0,
        )
        rb.load(current_equity=1000.0)
        # Ruhige Phase: Preis ~ konstant, sehr kleine Returns
        rng = np.random.default_rng(0)
        # ~1 bp Vol pro Step
        rets = rng.normal(scale=1e-4, size=120)
        prices = 100.0 * np.exp(np.cumsum(rets))
        out = rb.adjust_qty(1.0, prices.tolist())
        # Skala > 1 (Vol unter Target), gedeckelt auf 2.0
        assert out > 1.0
        assert out <= 2.0 + 1e-9

    def test_vol_scaling_decreases_qty_in_chaos(self, tmp_path):
        rb = _make_budget(
            tmp_path,
            vol_scaling_enabled=True,
            vol_target_bps=50.0,
        )
        rb.load(current_equity=1000.0)
        # Chaos: sehr volatile Returns ~ 200 bps
        rng = np.random.default_rng(1)
        rets = rng.normal(scale=0.02, size=120)
        prices = 100.0 * np.exp(np.cumsum(rets))
        out = rb.adjust_qty(1.0, prices.tolist())
        assert out < 1.0
        # Untergrenze 0.1
        assert out >= 0.1 - 1e-9

    def test_vol_scaling_handles_short_series(self, tmp_path):
        rb = _make_budget(tmp_path, vol_scaling_enabled=True)
        rb.load(current_equity=1000.0)
        # < 10 Preise → identity
        out = rb.adjust_qty(0.42, [100.0, 100.5, 99.5])
        assert out == 0.42
        # Leere Liste → identity
        out2 = rb.adjust_qty(0.42, [])
        assert out2 == 0.42

    def test_vol_scaling_disabled_is_identity(self, tmp_path):
        rb = _make_budget(tmp_path, vol_scaling_enabled=False)
        rb.load(current_equity=1000.0)
        prices = list(np.linspace(100, 105, 100))
        assert rb.adjust_qty(0.42, prices) == 0.42


class TestCheckEntryAllowed:
    def test_unblocked_allowed(self, tmp_path):
        rb = _make_budget(tmp_path)
        rb.load(current_equity=1000.0)
        allowed, reason = rb.check_entry_allowed(0.5)
        assert allowed is True
        assert reason == ""

    def test_zero_qty_blocked(self, tmp_path):
        rb = _make_budget(tmp_path)
        rb.load(current_equity=1000.0)
        allowed, reason = rb.check_entry_allowed(0.0)
        assert allowed is False
        assert reason == "qty<=0"


class TestManualReset:
    def test_manual_reset_clears_block(self, tmp_path):
        rb = _make_budget(tmp_path, daily_loss_pct=-0.03)
        rb.load(current_equity=1000.0)
        rb.on_equity_update(equity=950.0)
        assert rb.state.blocked_reason == "daily_loss"
        rb.manual_reset(current_equity=970.0)
        assert rb.state.blocked_reason == ""
        assert rb.state.daily_start_equity == 970.0
