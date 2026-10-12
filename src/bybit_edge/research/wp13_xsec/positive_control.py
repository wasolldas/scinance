"""WP-13 -- POSITIVE CONTROL in production configuration (DEC-89 Entscheidung 2, PRD 3.3.8).

**What it is.** PRD 3.3.8: when a run takes longer than an hour the positive control runs FIRST and ALONE and its
PASS is the precondition of the run. DEC-87 had only a unit-test version (K 200, 60 null replicates). DEC-89 (2)
fixes the production-size version, ``scripts/wp13_xsec.py --positive-control``: the registered YAML (the same START
LOCK as ``--run``), the REAL week grid, PIT alive masks and K_t of the loaded union panel (shape only), SYNTHETIC
weekly returns as the only outcome, the FROZEN constants of the YAML (the nulls do not depend on the outcome, so they
are NOT recomputed -- the ~2 h of the factor-null replicates stay in ``--run``), and the complete gate evaluation of
the run (:func:`run.evaluate_entry`, the very code ``run_full`` uses: IC series, SE, moving-block bootstrap CI,
``fm_neutral_8w`` beta control with betas estimated on the SYNTHETIC returns, comparison with the frozen
ceiling/quantiles/IC_min, bounce fixture with the registered parameters, liquidity and survivorship labels).

**What it never touches.** The real returns. :func:`run_positive_control` takes only ``shape`` (``weeks``, ``alive``,
``returns_valid`` -- labels and booleans) and ``symbols``; it has no ``returns`` argument at all (tested). The turnover
the liquidity-decile label needs is synthetic as well. No file under ``data/harvest`` is written.

**The synthetic world, per window and seed** (:func:`synthesize_window_returns`): the factor structure of the
calibrated null -- :func:`nulls.simulate_factor_panel` with the window's STRESS calibration read from the YAML
(``rho_f``, ``beta_sd_calibrated``; the market column IS the factor, DEC-85 (i); drift 0) -- PLUS the PRD 5.3
positive-control fixture generalised to a masked panel (the unit-test fixture ``_prd_positive_panel`` in
``tests/unit/test_wp13_run.py`` is its ancestor): sector blocks (a common weekly shock per sector) and an injected
cross-sectional signal of IC ~ 0.06, independent of beta by construction::

    r[t] = beta f[t] + sector[t] + e[t] + c1 z(r[t-1]) - c2 z(r[t-2]),     c = IC / sqrt(1 - IC^2) * sigma_tot

with ``z`` the cross-sectional z-score over the MEMBERS (alive AND a computable return, market column excluded) of
the earlier week. ``mom1`` (this week's return, positive) and ``rev_gap`` (the return two weeks back, negative, the
one-week gap design of DEC-87 (B)) both carry the signal. The scale parameters come ONLY from the registered YAML:
``sigma_e`` = the window's ``bounce_sigma_true`` (the measured median weekly symbol vol), ``sigma_f`` implied by the
stress ``target_factor_share`` (``sqrt(share/(1-share)) * sigma_e / beta_sd``, the inversion of the share formula
documented in :func:`nulls.true_beta_sd_from_factor_share`); sector shock (0.03/0.08 = 0.375 of ``sigma_e``) and sector
count (8) are the PRD fixture's. No number is taken from real returns.

**Negative control** = the identical world (same random stream, same base panel) with injected IC 0: only the
injection differs.

**PASS criterion (fixed before, DEC-89 E2):** ``H-28_mom1`` and ``H-29_rev_gap`` are PASS in ALL three seeds
(53, 54, 55) and the negative control gives NO PASS in any of the three seeds; locked (``gl012_pre_run``) entries are
skipped. The output line reads ``Positivkontrolle BESTANDEN`` / ``Positivkontrolle NICHT BESTANDEN``; a failed control
means no run (root-cause analysis, new DEC). ``bestanden`` is True only if every criterion holds.

Not computed here (report-only nulls, runtime): the block-permutation p-value and the BH flag, the persistence null.
Neither is a gate input (``gates.evaluate``); the report lists them under ``not_computed``.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from . import characteristics, ic, nulls, prelaunch, run

__all__ = [
    "PC_SEEDS", "INJECTED_IC", "N_SECTORS", "SECTOR_SHOCK_REL", "REQUIRED_ENTRIES", "PASS_LINE", "FAIL_LINE",
    "window_world", "synthesize_window_returns", "synthetic_turnover_trail", "run_positive_control",
    "render_positive_control_markdown", "write_positive_control_artifacts",
]

#: DEC-89 E2: the three seeds of the control (53 = the registered seed).
PC_SEEDS: tuple[int, ...] = (53, 54, 55)

#: PRD 5.3 positive-control fixture: the injected cross-sectional IC of mom1 (positive) and rev_gap (negative).
INJECTED_IC = 0.06

#: PRD 5.3 positive-control fixture: number of sector blocks and the sector shock relative to ``sigma_e``
#: (the fixture's ``sigma_g / sigma_e = 0.03 / 0.08``).
N_SECTORS = 8
SECTOR_SHOCK_REL = 0.03 / 0.08

#: The factor drift of the control's world: 0 (the driftfree cell; the injection must not hide behind a drift).
POSITIVE_CONTROL_DRIFT_F = nulls.DRIFT_F_DRIFTFREE

MARKET_SYMBOL = "BTCUSDT"

#: DEC-89 E2: the entries the criterion is about: entry id -> (hypothesis, variant, direction).
REQUIRED_ENTRIES: dict[str, tuple[str, str, str]] = {
    "H-28_mom1": ("H-28", "mom1", "positive"),
    "H-29_rev_gap": ("H-29", "rev_gap", "negative"),
}

PASS_LINE = "Positivkontrolle BESTANDEN"
FAIL_LINE = "Positivkontrolle NICHT BESTANDEN"

#: Report-only nulls that the control does not recompute (listed in the report).
NOT_COMPUTED = ("block_permutation_p", "bh_fdr", "persistence_null", "factor_null_replicates (frozen constants used)")


def _finite(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


# ----------------------------------------------------------------------------
# the synthetic world
# ----------------------------------------------------------------------------

def window_world(registered: dict[str, Any], wn: str) -> dict[str, float]:
    """The scale parameters of window ``wn``'s synthetic world, ALL from the registered YAML: the stress
    calibration (``rho_f``, ``beta_sd`` = ``beta_sd_calibrated``, ``share`` = ``target_factor_share``, report-only
    here) and -- DEC-89 E2 Nachtrag -- the calibrated null world's own scales ``null_scales.sigma_f`` (measured
    market vol) and ``null_scales.sigma_e_used`` (measured idiosyncratic vol), i.e. exactly the world the stress
    calibration's ``beta_sd`` was searched in; ``sigma_g = SECTOR_SHOCK_REL * sigma_e`` and ``sigma_tot =
    sqrt(sigma_e^2 + sigma_g^2 + (beta_sd sigma_f)^2)`` (the cross-sectional SD the injection is scaled to). A missing
    or out-of-range value is a :class:`run.RegisteredSchemaError` (C.14)."""
    wcfg = registered["windows"][wn]
    stress = ((wcfg.get("calibration") or {}).get("stress")) or {}
    rho_f, beta_sd, share = stress.get("rho_f"), stress.get("beta_sd_calibrated"), stress.get("target_factor_share")
    scales = wcfg.get("null_scales") or {}
    sigma_e, sigma_f = scales.get("sigma_e_used"), scales.get("sigma_f")
    if not (_finite(rho_f) and _finite(beta_sd) and float(beta_sd) > 0.0):
        raise run.RegisteredSchemaError(f"windows.{wn}.calibration.stress.{{rho_f, beta_sd_calibrated}} fehlen/ungueltig "
                                        "(Positivkontrolle DEC-89 E2)")
    if not (_finite(share) and 0.0 < float(share) < 1.0):
        raise run.RegisteredSchemaError(f"windows.{wn}.calibration.stress.target_factor_share={share!r} fehlt oder liegt "
                                        "nicht in (0, 1) (Positivkontrolle DEC-89 E2: sigma_f wird daraus abgeleitet)")
    if not (_finite(sigma_e) and float(sigma_e) > 0.0 and _finite(sigma_f) and float(sigma_f) > 0.0):
        raise run.RegisteredSchemaError(f"windows.{wn}.null_scales.{{sigma_f, sigma_e_used}} fehlen/ungueltig "
                                        "(Positivkontrolle DEC-89 E2: Welt der kalibrierten stress-Null)")
    rho_f, beta_sd, share = float(rho_f), float(beta_sd), float(share)
    sigma_e, sigma_f = float(sigma_e), float(sigma_f)
    sigma_g = SECTOR_SHOCK_REL * sigma_e
    sigma_tot = math.sqrt(sigma_e ** 2 + sigma_g ** 2 + (beta_sd * sigma_f) ** 2)
    return {"rho_f": rho_f, "beta_sd": beta_sd, "target_factor_share": share, "sigma_e": sigma_e, "sigma_f": sigma_f,
            "sigma_g": sigma_g, "sigma_tot": sigma_tot, "drift_f": POSITIVE_CONTROL_DRIFT_F}


def _zscore_members(row: np.ndarray, members: np.ndarray) -> np.ndarray:
    """Cross-sectional z-score of ``row`` over ``members`` (0 elsewhere); fewer than 2 members -> all zeros."""
    out = np.zeros_like(row)
    if int(members.sum()) >= 2:
        x = row[members]
        sd = float(x.std(ddof=1))
        out[members] = (x - x.mean()) / (sd if sd > 0.0 else 1.0)
    return out


def synthesize_window_returns(
    alive: np.ndarray, valid: np.ndarray, symbols: list[str], world: dict[str, float], *,
    seed: int, window_index: int, signal_ic: float,
) -> dict[str, Any]:
    """One window's synthetic weekly returns on the FULL real week grid (``alive``/``valid`` are the REAL masks,
    shape ``[n_weeks, n_symbols]``; the characteristics and the beta control are built on the full grid and sliced
    afterwards, as in the run, DEC-75 (8)). See the module docstring for the construction. ``signal_ic = 0`` is the
    negative control: the random stream is consumed identically (the injection draws nothing), so positive and
    negative control share the same base panel and differ ONLY by the injection.

    Returns ``returns`` (zero where no return is computable, like the real zero-filled array), ``returns_est`` (NaN
    there, the DEC-85 (iii) estimation array), ``factor`` (the market column), ``beta`` (the true loadings),
    ``coefficient`` (the injection coefficient ``c``)."""
    n_weeks, n_sym = alive.shape
    if MARKET_SYMBOL not in symbols:
        raise ValueError(f"{MARKET_SYMBOL} fehlt im Symbol-Universum (die Marktspalte ist der Faktor, DEC-85 (i))")
    m_idx = symbols.index(MARKET_SYMBOL)
    rng = np.random.default_rng([int(seed), int(window_index)])
    sim = nulls.simulate_factor_panel(
        n_weeks, n_sym, sigma_f=world["sigma_f"], sigma_e=world["sigma_e"], rho_f=world["rho_f"],
        drift_f=world["drift_f"], rng=rng, beta_sd=world["beta_sd"], market_index=m_idx)
    base, f, beta = sim["returns"].copy(), sim["f"], sim["beta"]
    non_market = np.array([j for j in range(n_sym) if j != m_idx])
    sector = np.full(n_sym, -1, dtype=np.int64)
    sector[non_market] = np.arange(non_market.size) % N_SECTORS
    g = world["sigma_g"] * rng.standard_normal((n_weeks, N_SECTORS))
    base += np.where(sector[None, :] >= 0, g[:, np.maximum(sector, 0)], 0.0)
    base[:, m_idx] = f

    members = np.asarray(alive, dtype=bool) & np.asarray(valid, dtype=bool)
    members[:, m_idx] = False
    coefficient = (signal_ic / math.sqrt(1.0 - signal_ic ** 2)) * world["sigma_tot"] if signal_ic else 0.0
    r = np.empty_like(base)
    z_rows: list[np.ndarray] = []
    for t in range(n_weeks):
        row = base[t].copy()
        if coefficient:
            if t >= 1:
                row += coefficient * z_rows[t - 1]
            if t >= 2:
                row -= coefficient * z_rows[t - 2]
        row[m_idx] = f[t]
        r[t] = row
        z_rows.append(_zscore_members(row, members[t]))
    valid_b = np.asarray(valid, dtype=bool)
    return {"returns": np.where(valid_b, r, 0.0), "returns_est": np.where(valid_b, r, np.nan),
            "factor": f, "beta": beta, "coefficient": float(coefficient)}


def synthetic_turnover_trail(alive: np.ndarray, *, seed: int, window_index: int) -> np.ndarray:
    """The trailing 8-week median turnover the liquidity-decile label (rev_gap) needs, SYNTHETIC: a persistent
    log-normal symbol level (SD 1.5, so the deciles are meaningful) times week noise (SD 0.5), zero where a symbol is
    not alive, independent of every synthetic return -- so removing the lowest decile removes no signal by
    construction. Own random stream (never the returns' stream)."""
    n_weeks, n_sym = alive.shape
    rng = np.random.default_rng([int(seed), int(window_index), 17])
    level = np.exp(1.5 * rng.standard_normal(n_sym))
    weekly = level[None, :] * np.exp(0.5 * rng.standard_normal((n_weeks, n_sym)))
    weekly = np.where(np.asarray(alive, dtype=bool), weekly, 0.0)
    return characteristics.trailing_median_turnover(weekly)


# ----------------------------------------------------------------------------
# the control
# ----------------------------------------------------------------------------

def _summarize_entry(res: dict[str, Any]) -> dict[str, Any]:
    """The reportable core of one evaluated entry: verdict, labels, gate flags, and per window the IC, SE, CI bound,
    IC_min, the beta-controlled IC with the binding null quantile, the ceiling, the bounce IC and the liquidity IC."""
    v, payload = res["verdict"], res["payload"]
    per_window: dict[str, Any] = {}
    for wn, w in payload["windows"].items():
        pw = v["per_window"][wn]
        per_window[wn] = {
            "mean_ic": w["mean_ic"], "se": w["se"], "ci_bound_toward_sign": w["ci_bound_toward_sign"],
            "ic_min_capped": w["ic_min_capped"], "residualized_mean_ic": w["residualized_mean_ic"],
            "res_quantile_binding": w["res_quantile_binding"],
            "selection_ceiling_mean_of_max": w["selection_ceiling_mean_of_max"], "n_weeks_used": w["n_weeks_used"],
            "gates": {k: pw[k] for k in ("sign_ok", "magnitude_ok", "ci_ok", "ic_min_ok", "beta_control_sign_ok",
                                         "beta_control_magnitude_ok", "beta_control_beyond_drifting_null_ok",
                                         "gate5_ok", "window_pass")},
            "bounce_ic": (payload["bounce_ic"] or {}).get(wn) if isinstance(payload.get("bounce_ic"), dict) else None,
            "ic_without_d1": (payload["liquidity_ic_without_d1"] or {}).get(wn)
            if isinstance(payload.get("liquidity_ic_without_d1"), dict) else None,
        }
    return {"verdict": v["verdict"], "labels": list(v["labels"]), "gl012_kill": v["gl012_kill"],
            "bounce_kill": v["bounce_kill"], "liquidity_label": v["liquidity_label"],
            "survivorship_label": v.get("survivorship_label", False),
            "survivorship_ic_min_units": v.get("survivorship_ic_min_units", {}), "windows": per_window}


def _canonical_sha256(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str, allow_nan=True).encode("utf-8")).hexdigest()


def run_positive_control(
    shape: dict[str, Any], symbols: list[str], registered: dict[str, Any], *,
    seeds: tuple[int, ...] = PC_SEEDS, signal_ic: float = INJECTED_IC, convention: ic.Convention = "close_at_last",
    observed_fingerprints: dict[str, Any] | None = None, registered_sha256: str | None = None,
    log: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """DEC-89 E2: the positive control in production configuration (see the module docstring).

    ``shape`` is ``{"weeks": [...], "alive": bool[n_weeks, n_symbols], "returns_valid": bool[...]}`` -- the real
    week grid and PIT masks of the union panel; ``symbols`` its column order. **There is no ``returns`` parameter:**
    nothing real is an outcome. ``registered`` is the parsed registered YAML (the CLI has already passed the START
    LOCK on its sha256).

    Order of loud fails (before any synthetic arithmetic): ``beta_control``, :func:`run.validate_registered` with
    ``require_frozen_constants=True`` (every frozen null constant, the DEC-89 fields), the data fingerprints against the
    loaded panel (V9), :func:`run.resolve_rules` / :func:`run.registered_window_constants` (T5 pins: ``block_len``,
    ``level``, ``w_judged``), the synthetic-world parameters. Entries: ``status: gl012_pre_run`` entries are SKIPPED
    (listed under ``skipped``); the criterion needs ``H-28_mom1`` and ``H-29_rev_gap`` as computed entries (an absent or
    locked one fails the control); any other computed entry cannot be injected and is listed under ``uncovered``.

    Returns the report: ``runs[seed]["positive" | "negative"][entry]`` (:func:`_summarize_entry`), ``criteria``,
    ``bestanden`` and ``line`` (``PASS_LINE`` / ``FAIL_LINE``), ``result_sha256`` (over everything but the runtime).
    Deterministic: the same inputs give the same ``result_sha256``."""
    t0 = time.perf_counter()
    say = log or (lambda _msg: None)
    method, trail_win = run.resolve_beta_control(registered)
    run.validate_registered(registered, require_frozen_constants=True)
    if observed_fingerprints is not None or "data_fingerprints" in registered:
        run.check_data_fingerprints(registered, observed_fingerprints)
    rr = run.resolve_rules(registered)

    weeks = list(shape["weeks"])
    alive_full = np.asarray(shape["alive"], dtype=bool)
    valid_full = np.asarray(shape["returns_valid"], dtype=bool)
    if alive_full.shape != valid_full.shape or alive_full.shape != (len(weeks), len(symbols)):
        raise ValueError(f"shape inkonsistent: alive {alive_full.shape}, returns_valid {valid_full.shape}, "
                         f"{len(weeks)} Wochen x {len(symbols)} Symbole")
    if MARKET_SYMBOL not in symbols:
        raise ValueError(f"{MARKET_SYMBOL} fehlt im Symbol-Universum")

    names = ("W1", "W2")
    # window geometry + frozen registered constants (floor from the REAL K_t series; no outcome involved)
    geom: dict[str, dict[str, Any]] = {}
    wconst: dict[str, dict[str, Any]] = {}
    worlds: dict[str, dict[str, float]] = {}
    for wn in names:
        wcfg = registered["windows"][wn]
        sl = prelaunch.slice_window(weeks, wcfg["start"], wcfg["end"])           # lo/hi/weeks only
        alive_w = alive_full[sl["lo"]:sl["hi"]]
        geom[wn] = {"lo": sl["lo"], "hi": sl["hi"], "weeks": sl["weeks"], "alive": alive_w}
        wconst[wn] = run.registered_window_constants(registered, wn, alive_w, sl["weeks"])
        worlds[wn] = window_world(registered, wn)
        if wconst[wn]["ceiling"] is None:
            raise run.RegisteredSchemaError(f"windows.{wn}.ceiling_method_stress fehlt (eingefrorene Konstante)")

    entries_cfg = registered["hypotheses"]
    skipped = {e: str(h.get("reason")) for e, h in entries_cfg.items() if h.get("status") == run.GL012_PRE_RUN}
    to_run: dict[str, dict[str, Any]] = {}
    missing: list[str] = []
    for eid, (_grp, variant, direction) in REQUIRED_ENTRIES.items():
        h = entries_cfg.get(eid)
        if h is None or h.get("status") == run.GL012_PRE_RUN or h.get("variant") != variant \
                or h.get("direction") != direction:
            missing.append(eid)
        else:
            to_run[eid] = h
    uncovered = [e for e, h in entries_cfg.items()
                 if e not in REQUIRED_ENTRIES and h.get("status") != run.GL012_PRE_RUN]

    survivorship_reg = {wn: dict(registered["windows"][wn].get("survivorship") or {}) for wn in names}
    bounce_sigma = {wn: registered["windows"][wn].get("bounce_sigma_true") for wn in names}

    runs: dict[str, Any] = {}
    for seed in seeds:
        runs[str(seed)] = {"positive": {}, "negative": {}}
        panels: dict[str, dict[str, Any]] = {}
        for widx, wn in enumerate(names):
            turnover = synthetic_turnover_trail(alive_full, seed=seed, window_index=widx)
            for cond, sic in (("positive", signal_ic), ("negative", 0.0)):
                synth = synthesize_window_returns(alive_full, valid_full, symbols, worlds[wn], seed=seed,
                                                  window_index=widx, signal_ic=sic)
                ret, est = synth["returns"], synth["returns_est"]
                pit = (characteristics.beta_characteristic(est, symbols, market_symbol=MARKET_SYMBOL,
                                                           trail_win=trail_win, min_weeks=trail_win)
                       if trail_win is not None else None)
                chars = {"mom1": characteristics.momentum_characteristic(ret, trail_win=1),
                         "rev_gap": characteristics.reversal_gap_characteristic(ret)}
                g = geom[wn]
                lo, hi = g["lo"], g["hi"]
                panels.setdefault(cond, {})[wn] = {
                    "characteristics": {v: a[lo:hi] for v, a in chars.items()}, "returns": ret[lo:hi],
                    "returns_est": est[lo:hi], "alive": g["alive"], "weeks": g["weeks"],
                    "turnover_trail": turnover[lo:hi], "day_count": None,
                    "beta_control_pit": pit[lo:hi] if pit is not None else None,
                    "coefficient": synth["coefficient"]}
        for cond in ("positive", "negative"):
            ctx = run.EntryContext(
                windows={wn: panels[cond][wn] for wn in names}, symbols=symbols,
                ic_min={wn: dict(registered["windows"][wn]["ic_min_capped"]) for wn in names},
                floor={wn: wconst[wn]["floor"] for wn in names}, w_judged={wn: wconst[wn]["w_judged"] for wn in names},
                ceiling={wn: wconst[wn]["ceiling"] for wn in names},
                q_driftfree={wn: wconst[wn]["q_driftfree"] for wn in names},
                q_drifting={wn: wconst[wn]["q_drifting"] for wn in names},
                beta_control_method=method, beta_control_pit={wn: panels[cond][wn]["beta_control_pit"] for wn in names},
                bounce_spread=rr["bounce_spread"], bounce_sigma_true=bounce_sigma, survivorship=survivorship_reg,
                convention=convention, seed=rr["seed"], n_reps_bootstrap=rr["n_reps_bootstrap"], n_reps_permutation=0,
                block_size=rr["block_len"], ci_level=rr["level"], persistence_n_sims=None)
            for eid, hcfg in to_run.items():
                res = run.evaluate_entry(eid, hcfg, ctx)
                runs[str(seed)][cond][eid] = _summarize_entry(res)
                say(f"  Seed {seed} {cond:8s} {eid}: {res['verdict']['verdict']}")

    crit = _criteria(runs, seeds, list(REQUIRED_ENTRIES), missing)
    crit["seeds_registered"] = tuple(seeds) == PC_SEEDS
    if not crit["seeds_registered"]:
        # DEC-89 E2 names the seeds 53, 54, 55: a control over other seeds is an exploration, never a PASS.
        crit["bestanden"] = False
        crit["note"] = f"Seeds {list(seeds)} weichen von den registrierten {list(PC_SEEDS)} ab -- kein BESTANDEN moeglich"
    bestanden = bool(crit["bestanden"])
    core = {
        "schema": "DEC-89 E2 positive control", "seeds": list(seeds), "injected_ic": signal_ic,
        "registered_sha256": registered_sha256, "data_fingerprints": observed_fingerprints,
        "convention": convention, "beta_control": {"method": method, "beta_window_weeks": trail_win},
        "worlds": worlds, "skipped": skipped, "uncovered": uncovered, "not_computed": list(NOT_COMPUTED),
        "runs": runs, "criteria": crit, "bestanden": bestanden, "line": PASS_LINE if bestanden else FAIL_LINE,
    }
    core["result_sha256"] = _canonical_sha256(core)
    core["code"] = run.code_fingerprint()
    core["runtime_seconds"] = round(time.perf_counter() - t0, 3)
    return core


def _criteria(runs: dict[str, Any], seeds: tuple[int, ...], required: list[str], missing: list[str]) -> dict[str, Any]:
    """DEC-89 E2: ``H-28_mom1`` and ``H-29_rev_gap`` PASS in every seed (positive control) AND no PASS in any seed of
    the negative control. An entry that is absent/locked/mismatching in the YAML (``missing``) fails the control."""
    positive = {e: {str(s): runs[str(s)]["positive"].get(e, {}).get("verdict") for s in seeds} for e in required}
    negative = {e: {str(s): runs[str(s)]["negative"].get(e, {}).get("verdict") for s in seeds} for e in required}
    pos_ok = not missing and all(v == "PASS" for e in required for v in positive[e].values())
    neg_ok = not missing and all(v is not None and v != "PASS" for e in required for v in negative[e].values())
    return {"required_entries": required, "missing_or_locked_required_entries": missing,
            "positive_verdicts": positive, "negative_verdicts": negative,
            "positive_all_pass": bool(pos_ok), "negative_no_pass": bool(neg_ok),
            "bestanden": bool(pos_ok and neg_ok)}


# ----------------------------------------------------------------------------
# report
# ----------------------------------------------------------------------------

def render_positive_control_markdown(report: dict[str, Any]) -> str:
    """ASCII Markdown report of the control: the verdict line first, the criterion table (entry x seed x
    positive/negative), the synthetic worlds, then per seed/condition/entry/window the figures behind the verdict."""
    fmt = run._fmt
    crit = report["criteria"]
    lines = [report["line"], "", "# WP-13 Positivkontrolle in Produktionskonfiguration (DEC-89 E2)", "",
             f"- registrierte Datei sha256: `{report.get('registered_sha256')}`",
             f"- Seeds: {report['seeds']}, injizierte IC: {report['injected_ic']}, Konvention `{report['convention']}`, "
             f"Beta-Kontrolle `{report['beta_control']['method']}`",
             f"- Daten-Fingerprints (V9): `{report.get('data_fingerprints')}`",
             f"- result_sha256: `{report['result_sha256']}`, Laufzeit {report['runtime_seconds']} s",
             f"- nicht gerechnet (report-only / eingefrorene Werte): {', '.join(report['not_computed'])}",
             f"- uebersprungen (gesperrt, gl012_pre_run): {', '.join(report['skipped']) or '-'}",
             f"- nicht abgedeckt (kein injizierbares Signal): {', '.join(report['uncovered']) or '-'}", "",
             "## Kriterium (vorab, DEC-89 E2)", "",
             "H-28_mom1 und H-29_rev_gap in allen drei Seeds PASS UND Negativkontrolle in allen drei Seeds kein PASS.", "",
             f"- Positivkontrolle alle PASS: {crit['positive_all_pass']}",
             f"- Negativkontrolle kein PASS: {crit['negative_no_pass']}"]
    if crit["missing_or_locked_required_entries"]:
        lines.append(f"- FEHLT / gesperrt / abweichend registriert: {crit['missing_or_locked_required_entries']}")
    if crit.get("note"):
        lines.append(f"- {crit['note']}")
    lines += ["", "| Eintrag | Bedingung | " + " | ".join(f"Seed {s}" for s in report["seeds"]) + " |",
              "|---|---|" + "---|" * len(report["seeds"])]
    for e in crit["required_entries"]:
        for cond, key in (("positiv", "positive_verdicts"), ("negativ", "negative_verdicts")):
            lines.append(f"| {e} | {cond} | " + " | ".join(str(crit[key][e].get(str(s))) for s in report["seeds"]) + " |")
    lines += ["", "## Synthetische Welten (aus der YAML abgeleitet)", "",
              "| Fenster | rho_f | beta_sd | Faktoranteil | sigma_e | sigma_f | sigma_g | sigma_tot |", "|---|---|---|---|---|---|---|---|"]
    for wn, w in report["worlds"].items():
        lines.append(f"| {wn} | {fmt(w['rho_f'])} | {fmt(w['beta_sd'])} | {fmt(w['target_factor_share'])} | "
                     f"{fmt(w['sigma_e'])} | {fmt(w['sigma_f'])} | {fmt(w['sigma_g'])} | {fmt(w['sigma_tot'])} |")
    lines += ["", "## Kennzahlen je Seed, Bedingung, Eintrag, Fenster", "",
              "| Seed | Bedingung | Eintrag | Verdikt | Fenster | IC | CI-Grenze | IC_min | IC_res | Quantil | Decke | "
              "Bounce-IC | Fenster PASS |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for seed, by_cond in report["runs"].items():
        for cond, entries in by_cond.items():
            for eid, ent in entries.items():
                for wn, w in ent["windows"].items():
                    lines.append(
                        f"| {seed} | {cond} | {eid} | {ent['verdict']} | {wn} | {fmt(w['mean_ic'])} | "
                        f"{fmt(w['ci_bound_toward_sign'])} | {fmt(w['ic_min_capped'])} | {fmt(w['residualized_mean_ic'])} | "
                        f"{fmt(w['res_quantile_binding'])} | {fmt(w['selection_ceiling_mean_of_max'])} | "
                        f"{fmt(w['bounce_ic'])} | {w['gates']['window_pass']} |")
    lines += ["", "## Etiketten (je Seed, Bedingung, Eintrag)", ""]
    for seed, by_cond in report["runs"].items():
        for cond, entries in by_cond.items():
            for eid, ent in entries.items():
                lines.append(f"- Seed {seed} {cond} {eid}: " + (" / ".join(ent["labels"]) or "-"))
    lines += ["", report["line"], ""]
    return "\n".join(lines)


def write_positive_control_artifacts(out_dir: Path | str, report: dict[str, Any]) -> dict[str, Any]:
    """Writes ``wp13_positive_control.json`` and ``wp13_positive_control.md`` into ``out_dir`` (created; refused under
    ``data/harvest``). Returns ``{"out_dir", "artifacts": {name: {"path", "sha256"}}}`` (sha256 via
    ``panel_load.sha256_file``, the hash the rest of the package uses)."""
    from ..wp7_universe import panel_load

    out_dir = Path(out_dir)
    if "data/harvest" in out_dir.as_posix():
        raise ValueError(f"refusing to write under data/harvest: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = out_dir / "wp13_positive_control.json", out_dir / "wp13_positive_control.md"
    json_path.write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    md_path.write_text(render_positive_control_markdown(report), encoding="utf-8")
    return {"out_dir": str(out_dir), "artifacts": {
        "wp13_positive_control_json": {"path": str(json_path), "sha256": panel_load.sha256_file(json_path)},
        "wp13_positive_control_md": {"path": str(md_path), "sha256": panel_load.sha256_file(md_path)}}}
