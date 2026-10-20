"""Fixture panels for the H-32 tests (synthetic, in memory): a daily union panel on the real calendar (2021-10 .. 2026-09)
with a factor structure, optional injected signal (mom1/mom2/mom4 positive, rev_gap negative via the lag-2 reversal),
delisted and late-listed symbols and -- optionally -- violent shocks AFTER the cut date (so that a leak is visible).

The weekly returns are generated first and the daily closes interpolate them (the weekly close is the Sunday close), so
every weekly statistic of ``panel_load`` reproduces the generated weekly returns exactly.
"""
from __future__ import annotations

import atexit
import copy
import functools
import math
import shutil
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml

from bybit_edge.research.h32_fm8 import artifacts, checks, pilot as pilot_mod, pnull, testrun, vorlauf
from bybit_edge.research.h32_fm8 import constants as C

START = date(2021, 10, 4)               # a Monday
END = date(2026, 9, 27)                 # a Sunday, after the test cut (2026-06-28)
FAKE_FINGERPRINTS = {"union_range_fingerprint": "ab" * 32, "delisting_dates_sha256": "cd" * 32, "delisting_register_sha256": "ef" * 32}


def _zscore(x: np.ndarray, members: np.ndarray) -> np.ndarray:
    out = np.zeros_like(x)
    if int(members.sum()) >= 2:
        v = x[members]
        sd = float(v.std(ddof=1))
        out[members] = (v - v.mean()) / (sd if sd > 0 else 1.0)
    return out


def make_panel(*, seed: int = 7, k: int = 160, n_late: int = 10, signal: float = 0.0, sigma_f: float = 0.06, sigma_e: float = 0.09,
               rho_f: float = 0.1, beta_sd: float = 0.4, post_cut_shock: bool = True, delist_weeks: tuple[int, ...] = (60, 90, 150, 170, 200, 230),
               start: date = START, end: date = END) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    n_days = (end - start).days + 1
    n_weeks = n_days // 7
    syms = ["BTCUSDT"] + [f"S{j:03d}USDT" for j in range(1, k)]
    n_sym = len(syms)
    list_week = np.zeros(n_sym, dtype=int)
    last_week = np.full(n_sym, n_weeks - 1, dtype=int)
    for i, j in enumerate(range(n_sym - n_late, n_sym)):
        list_week[j] = 150 + 4 * i
    for i, w in enumerate(delist_weeks):
        last_week[1 + 3 * i] = w
    # factor and idiosyncratic weekly returns
    f = np.empty(n_weeks)
    f[0] = sigma_f * rng.standard_normal()
    for t in range(1, n_weeks):
        f[t] = rho_f * f[t - 1] + sigma_f * rng.standard_normal()
    beta = 1.0 + beta_sd * rng.standard_normal(n_sym)
    beta[0] = 1.0
    base = beta[None, :] * f[:, None] + sigma_e * rng.standard_normal((n_weeks, n_sym))
    base[:, 0] = f
    sigma_tot = math.sqrt(sigma_e ** 2 + (beta_sd * sigma_f) ** 2)
    c = (signal / math.sqrt(1.0 - signal ** 2)) * sigma_tot if signal else 0.0
    members_t = [((list_week <= t) & (last_week >= t)) for t in range(n_weeks)]
    r = np.empty_like(base)
    z_hist: list[np.ndarray] = []
    for t in range(n_weeks):
        row = base[t].copy()
        if c:
            if t >= 1:
                row += c * z_hist[t - 1]
            if t >= 2:
                row -= c * z_hist[t - 2]
        row[0] = f[t]
        r[t] = row
        mem = members_t[t].copy()
        mem[0] = False
        z_hist.append(_zscore(row, mem))
    cut_week = (date.fromisoformat(C.CUT_TEST) - start).days // 7        # week index of the cut week (complete)
    if post_cut_shock:
        r[cut_week + 1:] += 0.6 * rng.standard_normal((n_weeks - cut_week - 1, n_sym))
        r[cut_week + 1, 0] += 1.0
    # daily closes
    dates = [(start + timedelta(days=d)).isoformat() for d in range(n_days)]
    close = np.full((n_days, n_sym), np.nan)
    turnover = np.full((n_days, n_sym), np.nan)
    level = np.exp(1.5 * rng.standard_normal(n_sym))
    delist_day = {}
    for j in range(n_sym):
        logp = 0.0
        for t in range(list_week[j], last_week[j] + 1):
            days_in_week = 7
            if t == last_week[j] and last_week[j] < n_weeks - 1:
                days_in_week = 3                               # delisted on the Wednesday of its last week
            for d in range(days_in_week):
                idx = t * 7 + d
                if t == list_week[j]:
                    lp = 0.0
                else:
                    lp = logp + (d + 1) / 7.0 * r[t, j]
                close[idx, j] = 100.0 * math.exp(lp)
                turnover[idx, j] = level[j] * math.exp(0.5 * rng.standard_normal())
            if t > list_week[j]:
                logp += r[t, j]
            if t == last_week[j] and last_week[j] < n_weeks - 1:
                delist_day[j] = dates[t * 7 + 2]
    last_alive = [delist_day.get(j) for j in range(n_sym)]
    is_del = np.array([j in delist_day for j in range(n_sym)])
    panel = {"symbols": syms, "dates": dates, "day_index": list(range(n_days)), "close": close, "turnover": turnover,
             "funding_n": np.zeros_like(close), "funding_sum": np.zeros_like(close), "last_alive_day": last_alive,
             "is_delisted": is_del, "delisted_symbols": [s for s, d in zip(syms, is_del) if d],
             "relisted_gaps": {}, "n_symbols_survivors": int((~is_del).sum()), "n_symbols_delisted": int(is_del.sum()),
             "as_of": end.isoformat()}
    return panel


def relabel_prices(panel: dict[str, Any], seed: int) -> dict[str, Any]:
    """Same NaN pattern (listing / delisting), completely different prices -- masks identical, returns unrelated."""
    rng = np.random.default_rng(seed)
    out = dict(panel)
    close = panel["close"].copy()
    fin = np.isfinite(close)
    close[fin] = 100.0 * np.exp(0.05 * rng.standard_normal(int(fin.sum())))
    out["close"] = close
    return out


def small_params() -> dict[str, Any]:
    """Replicate counts for fixture runs (the registered pins are patched to these by ``shrink_constants``)."""
    return {"n_reps": 24, "n_boot": 60, "n_perm": 80}


def calibration_kwargs() -> dict[str, Any]:
    """Relaxed Gegenprobe / search knobs for tiny synthetic panels (same discipline as the wp13 tests)."""
    return dict(search_n_reps=10, search_rel_tol=10.0, search_max_iter=6, gegenprobe_n_reps=10, gegenprobe_rel_tol=10.0,
                gegenprobe_z_max=1e9, gegenprobe_market_check=False)


def shrink_constants(monkeypatch, *, n_reps: int = 24, n_boot: int = 60, n_perm: int = 80, pc_judge: int = 16, pc_sigma: int = 4,
                     pc_inject: int = 5) -> None:
    """Shrink the registered replicate counts / seeds / criteria of a FIXTURE run.  The pin checks keep comparing the YAML
    with these (patched) code constants, so a YAML written by the emitter stays valid."""
    monkeypatch.setattr(C, "N_REPS_MIN", n_reps)
    monkeypatch.setattr(C, "N_BOOT_MIN", n_boot)
    monkeypatch.setattr(C, "N_PERM", n_perm)
    monkeypatch.setattr(C, "PC_SEEDS_JUDGE", tuple(range(53, 53 + pc_judge)))
    monkeypatch.setattr(C, "PC_SEEDS_SIGMA_G", tuple(range(2000, 2000 + pc_sigma)))
    monkeypatch.setattr(C, "PC_SEEDS_INJECT", tuple(range(1000, 1000 + pc_inject)))
    monkeypatch.setattr(C, "PC_PASS_SHARE_MIN", 0.30)
    monkeypatch.setattr(C, "PC_NEG_PASS_MAX", 0.45)
    monkeypatch.setattr(C, "PC_INJECT_JUDGE_TOL", 0.60)
    monkeypatch.setattr(C, "PC_SD_RATIO_MAX", 1.30)
    monkeypatch.setattr(C, "PC_WORLD_SD_TOL", 0.10)
    monkeypatch.setattr(C, "PC_INJECT_TOL", 0.25)


def prelaunch_report(panel: dict[str, Any], **kw: Any) -> dict[str, Any]:
    args = dict(cut_date=C.CUT_TEST, n_reps=C.N_REPS_MIN, n_boot=C.N_BOOT_MIN, calibration_kwargs=calibration_kwargs())
    args.update(kw)
    return vorlauf.assemble_prelaunch(panel, dict(FAKE_FINGERPRINTS), **args)


def registered_from_report(report: dict[str, Any], *, bounce_spread: float = 0.003621) -> dict[str, Any]:
    """The YAML dict a template emitter writes (round-tripped through YAML text, like the registered file on disk)."""
    tpl = vorlauf.build_template(report, bounce_spread=bounce_spread)
    return yaml.safe_load(vorlauf.template_yaml_text(tpl, report))


def deep(d: Any) -> Any:
    return copy.deepcopy(d)


REGISTERED_SHA = "9" * 64


@functools.lru_cache(maxsize=None)
def get_bundle(kind: str) -> dict[str, Any]:
    """Expensive objects shared by the test modules, built once per process with the shrunk constants:
    ``kind`` = ``"signal"`` (injected signal 0.15: mom1 and rev_gap are handed over) or ``"null"`` (signal-free panel)."""
    sig = {"signal": 0.15, "null": 0.0}[kind]
    with pytest.MonkeyPatch.context() as mp:
        shrink_constants(mp)
        panel = make_panel(seed=7 if kind == "signal" else 11, signal=sig)
        report = prelaunch_report(panel)
        registered = registered_from_report(report)
        registered["data_fingerprints"] = dict(FAKE_FINGERPRINTS)
        tmp = Path(tempfile.mkdtemp(prefix=f"h32_{kind}_"))
        atexit.register(shutil.rmtree, tmp, True)
        pr = pilot_mod.run_pilot(panel, registered, dict(FAKE_FINGERPRINTS), registered_sha256=REGISTERED_SHA)
        lock = checks.check_rerun_lock(tmp / "pilot", registered, None)
        pilot_mod.write_pilot_artifacts(tmp / "pilot", pr, registered, lock)
        pj = tmp / "pilot" / "h32_pilot.json"
        pil = testrun.load_pilot_result(pj, artifacts.sha256_file(pj), registered, REGISTERED_SHA)
        (tmp / "prelaunch").mkdir()
        pp = tmp / "prelaunch" / C.P_REPLICATES_FILE
        artifacts.write_json(pp, report["_p_payload"])
        p_rep = pnull.load_replicates(pp, registered)
    return {"panel": panel, "report": report, "registered": registered, "pilot_report": pr, "pilot": pil, "pilot_json": pj,
            "pilot_sha": artifacts.sha256_file(pj), "tmp": tmp, "p_rep": p_rep, "p_rep_path": pp}


@pytest.fixture
def shrunk(monkeypatch):
    """Function-scoped shrink of the registered replicate counts / PC seeds / criteria (see :func:`shrink_constants`)."""
    shrink_constants(monkeypatch)
    return monkeypatch
