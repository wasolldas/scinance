"""WP-13 -- RUN MODE (DEC-75 Entscheidung 1 (1)-(7), Entscheidung 2 last
sentence: "Der Lauf-Modus wird im selben Bau angelegt, aber mit
Startsperre").

**START LOCK (the whole point of this module's CLI wiring,
``scripts/wp13_xsec.py --run``).** The run mode computes REAL
characteristic-vs-real-outcome ICs -- THE thing ``--prelaunch`` is
structurally forbidden from ever doing (see ``ic.py``'s module
docstring, "THE SEAL"). It may therefore ONLY run against a
``--registered`` YAML file (the Drittfassung's threshold block:
``ic_min_capped`` per variant/window, ``W_judged``, rules) whose
sha256 matches an explicit ``--registered-sha256`` the caller supplies.
This module itself never checks the hash -- that is the CLI's job
(``scripts/wp13_xsec.py``'s ``cmd_run``) so the check happens BEFORE a
single byte of real panel data is touched; :func:`load_registered_yaml`
here is a plain, hash-agnostic YAML loader used only AFTER the CLI's
lock has already passed.

**DEC-75 (8) / task brief item 8: characteristics-on-full-panel-first.**
Every variant's characteristic is built ONCE on the FULL panel (all
weeks, all symbols, via ``characteristics.compute_all_characteristics``),
THEN sliced to a window -- the IDENTICAL path ``prelaunch.py``'s
``vol_rv``/``turnover_trail`` construction already uses (see that
module's ``assemble_prelaunch_report``). :func:`build_all_characteristics_full_panel`
is the single, shared entry point both modes use.

**Module layout.** Every numbered DEC-75 Entscheidung 1 (1)-(7) run-mode
component is its OWN pure, independently-testable function below
(``se_of_mean_ic``, ``moving_block_bootstrap_ci``,
``liquidity_decile_sensitivity``, ``bounce_fixture_ic``, ``lag_profile``,
``benjamini_hochberg``); :func:`variant_window_payload` assembles ONE
variant/window's numbers into exactly the shape ``gates.evaluate``
expects; :func:`run_hypothesis` calls it for both judgement windows and
hands the assembled payload to ``gates.evaluate``; :func:`run_full` is
the top-level orchestrator (panel -> per-hypothesis verdicts + DEC-53
artifacts). The CLI (``scripts/wp13_xsec.py``) owns I/O and the START
LOCK; nothing in this module reads a file or a CLI flag.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from ..wp7_universe import panel_load
from . import characteristics, gates, ic, nulls

__all__ = [
    "REGISTERED_SCHEMA_HINT", "load_registered_yaml", "sha256_of_file",
    "build_all_characteristics_full_panel", "se_of_mean_ic",
    "moving_block_bootstrap_ci", "max_p_over_windows", "liquidity_decile_sensitivity",
    "bounce_fixture_ic", "lag_profile", "benjamini_hochberg", "assert_null_calibration",
    "NullCalibrationError", "NULL_CALIBRATION_REL_TOL",
    "variant_window_payload", "run_hypothesis", "run_full", "write_run_artifacts",
]

#: DEC-76 Entscheidung 1 (b)/Task A item 3: +/-10% tolerance between the
#: run's own recomputed null constant (real K series, real W_judged) and
#: the value FROZEN in the registered YAML.
NULL_CALIBRATION_REL_TOL = 0.10

REGISTERED_SCHEMA_HINT = (
    "hypotheses: {H-xx: {variant: str, direction: positive|negative, outcome?: vol_weighted}}; "
    "windows: {W1: {start, end, ic_min_capped: {variant: float}, w_judged: int, "
    "res_quantile_drifting: {variant: float}, ceiling_driftfree_res: float}, W2: {...}, L?: {start, end}}; "
    "beta_control: {method: str (one of ic.BETA_CONTROL_METHODS, REQUIRED, non-empty -- DEC-77 "
    "Entscheidung 2, loud fail otherwise), beta_window_weeks: int|None (must match the trailing "
    "window ic.beta_control_trail_weeks(method) implies)}; "
    "calibration?: {sigma_f: float, sigma_e: float, stress_multiplier: float (default 2), "
    "measured: {rho_f: float, factor_share: float, beta_sd_analytic_first_guess: float, "
    "beta_sd_calibrated: float, achieved_share: float, true_share: float, converged: bool}, "
    "stress: {rho_f: float, factor_share: float, beta_sd_analytic_first_guess: float, "
    "beta_sd_calibrated: float, achieved_share: float, true_share: float, converged: bool}} "
    "(DEC-78 Entscheidung 1, revised by its Nachtrag: OPTIONAL for backward compatibility with "
    "a pre-DEC-78 registered file -- the SINGLE, global block --emit-registered-template takes "
    "from the prelaunch artifact's W1 factor_calibration/beta_control_method_study, applied "
    "identically to BOTH windows' null recomputation below, the SAME single-global-constant "
    "convention DEC-75's own rho_f=0.2 used. `beta_sd_calibrated` is the BISECTION-CALIBRATED "
    "value (nulls.calibrate_beta_sd_to_observed_share, DEC-78 Nachtrag) that made the Gegenprobe "
    "pass in the prelaunch artifact -- run_full reads it DIRECTLY, NO re-search at run time; "
    "`beta_sd_analytic_first_guess` (the OLD closed-form nulls.true_beta_sd_from_factor_share "
    "value) is carried along report-only, never used); "
    "rules: {seed: 53, n_reps: >=1000 (bootstrap/permutation/factor-null reps; legacy "
    "n_reps_bootstrap/n_reps_permutation/n_reps_factor_null still read if n_reps is absent), "
    "block_len: 4 (DEC-75 Entscheidung 1 (1): a FIXED registered constant, recorded here "
    "for audit -- run_full's block-bootstrap/-permutation helpers hardcode block_size=4 "
    "directly, per DEC-75, rather than reading this key back), "
    "level: 0.9936, bh_alpha: 0.10}. "
    "DEC-76 Entscheidung 1(b)/(c) / DEC-77 Entscheidung 2 / DEC-78 Entscheidung 1/Nachtrag: "
    "windows.<W>.res_quantile_drifting[variant] and windows.<W>.ceiling_driftfree_res are the "
    "FROZEN Drittfassung constants -- run_full recomputes both via nulls.beta_controlled_"
    "factor_null (registered beta_control.method, driftfree, seed 53, rules.n_reps reps) under "
    "the 'stress' null: rho_f = calibration.stress.rho_f, beta_sd = calibration.stress."
    "beta_sd_calibrated -- READ DIRECTLY, no re-search/re-derivation at run time -- IF "
    "`calibration` is present; absent (pre-DEC-78 file) falls back to the OLD hardcoded stress "
    "null (rho_f=0.2, beta drawn U(0.5, 2.0), documented, not a registered Drittfassung run) -- "
    "and asserts the recomputed values are within +/-NULL_CALIBRATION_REL_TOL of the FROZEN "
    "res_quantile_drifting/ceiling_driftfree_res values, else loud fail ('Null-Kalibrierung "
    "weicht ab', NullCalibrationError, no verdict); the gate itself always judges against the "
    "FROZEN (registered) value, never the recomputed one. res_quantile_drifting/"
    "ceiling_driftfree_res are OPTIONAL for backward compatibility with a pre-DEC-76 registered "
    "file -- if absent for a window, run_full falls back to the recomputed value with no "
    "calibration check (documented, not a registered Drittfassung run)."
)


def sha256_of_file(path: Path | str) -> str:
    """Thin re-export of ``panel_load.sha256_file`` under the name the
    START-LOCK docstring above uses -- the CLI hashes the registered YAML
    with this exact function, so ``--registered-sha256`` is checked
    against the SAME hash this module would compute, never a
    differently-normalised one."""
    return panel_load.sha256_file(path)


def load_registered_yaml(path: Path | str) -> dict[str, Any]:
    """Plain YAML load -- the CLI's START LOCK (sha256 match) MUST already
    have passed before this is ever called (see module docstring)."""
    text = Path(path).read_text(encoding="utf-8")
    payload = yaml.safe_load(text)
    if not isinstance(payload, dict) or "hypotheses" not in payload or "windows" not in payload:
        raise ValueError(f"registered YAML at {path} missing required top-level keys "
                          f"(expected shape: {REGISTERED_SCHEMA_HINT})")
    return payload


class NullCalibrationError(RuntimeError):
    """DEC-76 Entscheidung 1 (b)/Task A item 3, C.14 loud fail: the run's
    own recomputed null constant (real K series/W_judged, seed 53) drifted
    more than :data:`NULL_CALIBRATION_REL_TOL` from the value frozen in the
    registered YAML -- raised BEFORE any ``gates.evaluate`` call, so no
    hypothesis in the run gets a verdict."""


def assert_null_calibration(recomputed: float, registered: float | None, *, label: str,
                             rel_tol: float = NULL_CALIBRATION_REL_TOL,
                             abs_tol_if_zero: float = 1e-4) -> None:
    """DEC-76 Entscheidung 1 (b)/Task A item 3: asserts ``recomputed`` (this
    run's own re-derivation of a DEC-76 null constant, real K series/real
    W_judged, seed 53, ``rules.n_reps`` reps) is within ``rel_tol`` of
    ``registered`` (the Drittfassung's FROZEN value for the SAME constant)
    -- a documented safeguard: a real run's panel can differ from the
    Vorlauf's (more symbols delisted since, a later ``as_of``), and this
    assertion is what catches a registration that has quietly gone stale
    BEFORE it can silently gate a verdict. ``registered is None`` is a
    no-op (a pre-DEC-76 registered file that never carried this key --
    documented backward-compat, see :data:`REGISTERED_SCHEMA_HINT`) --
    only a PRESENT-but-drifted value raises. ``registered == 0`` (or very
    close to it) uses an ABSOLUTE tolerance (``abs_tol_if_zero``) instead
    of a relative one, since a relative tolerance around exactly 0 is
    degenerate."""
    if registered is None:
        return
    if recomputed is None or math.isnan(recomputed) or math.isnan(registered):
        raise NullCalibrationError(
            f"Null-Kalibrierung weicht ab ({label}): recomputed={recomputed!r}, "
            f"registered={registered!r} -- nicht vergleichbar (NaN/None), kein Verdikt.")
    if abs(registered) < 1e-12:
        ok = abs(recomputed - registered) <= abs_tol_if_zero
    else:
        ok = abs(recomputed - registered) <= rel_tol * abs(registered)
    if not ok:
        raise NullCalibrationError(
            f"Null-Kalibrierung weicht ab ({label}): recomputed={recomputed:.6f} vs. "
            f"registered={registered:.6f} (Toleranz +/-{rel_tol:.0%}) -- kein Verdikt.")


# ----------------------------------------------------------------------------
# DEC-75 (8): characteristics on the FULL panel, sliced afterward
# ----------------------------------------------------------------------------

def build_all_characteristics_full_panel(
    returns: np.ndarray, panel: dict[str, Any], weeks: list[str], symbols: list[str],
) -> dict[str, np.ndarray]:
    """The ONE place run mode builds the 7 F-XSEC1 characteristics --
    thin passthrough to ``characteristics.compute_all_characteristics``
    (never reimplemented), called ONCE on the FULL panel; callers slice
    the returned arrays to a window afterward (DEC-75 (8))."""
    return characteristics.compute_all_characteristics(returns, panel, weeks, symbols)


# ----------------------------------------------------------------------------
# DEC-75 Entscheidung 1 (1): SE + moving-block bootstrap CI
# ----------------------------------------------------------------------------

def se_of_mean_ic(ic_weekly: np.ndarray, floor: float, w_judged: int) -> dict[str, Any]:
    """DEC-75 Entscheidung 1 (1), verbatim: ``SE = max(floor, SD(IC_t)) /
    sqrt(W_judged)``. ``ic_weekly`` is the per-week IC series (NaN
    entries excluded from ``SD``)."""
    finite = ic_weekly[~np.isnan(ic_weekly)]
    sd_ic = float(finite.std(ddof=1)) if finite.size > 1 else float("nan")
    sd_component = sd_ic if not math.isnan(sd_ic) else 0.0
    dispersion = max(floor, sd_component)
    se = dispersion / math.sqrt(w_judged) if w_judged > 0 else float("nan")
    return {"floor": floor, "sd_ic": sd_ic, "dispersion_used": dispersion, "w_judged": w_judged, "se": se}


def moving_block_bootstrap_ci(
    ic_weekly: np.ndarray, *, direction: str, block_size: int = 4,
    n_reps: int = 1000, seed: int = 53, level: float = 1.0 - 0.0064,
) -> dict[str, Any]:
    """DEC-75 Entscheidung 1 (1): moving-block bootstrap OVER WEEKS
    (block ``block_size``, ``>= 1000`` reps, seed 53) of the per-week IC
    series' MEAN, then the one-sided CI bound FACING the registered
    ``direction`` at ``level`` (default ``1 - 0.0064``): for
    ``"positive"`` the LOWER percentile-method bound (``quantile(1 -
    level)``, must be ``> 0`` to pass); for ``"negative"`` the UPPER bound
    (``quantile(level)``, must be ``< 0``). NaN weeks are dropped before
    resampling (a block is drawn from the finite series only -- a short
    finite series is a legitimate, if under-powered, input)."""
    finite = ic_weekly[~np.isnan(ic_weekly)]
    n = finite.size
    if n < 2:
        return {"ci_bound_toward_sign": float("nan"), "n_reps": n_reps, "level": level,
                "direction": direction, "n_weeks_finite": n}
    rng = np.random.default_rng(seed)
    n_blocks_needed = math.ceil(n / block_size)
    means = np.empty(n_reps, dtype=np.float64)
    starts_max = max(n - block_size, 0)
    for i in range(n_reps):
        starts = rng.integers(0, starts_max + 1, size=n_blocks_needed)
        sample = np.concatenate([finite[s:s + block_size] for s in starts])[:n]
        means[i] = sample.mean()
    if direction == "positive":
        bound = float(np.quantile(means, 1.0 - level))
    elif direction == "negative":
        bound = float(np.quantile(means, level))
    else:
        raise ValueError(f"direction must be 'positive' or 'negative', got {direction!r}")
    return {"ci_bound_toward_sign": bound, "n_reps": n_reps, "level": level,
            "direction": direction, "n_weeks_finite": n, "block_size": block_size, "seed": seed}


# ----------------------------------------------------------------------------
# DEC-75 Entscheidung 1 (2): Max-p over windows
# ----------------------------------------------------------------------------

def max_p_over_windows(p_by_window: dict[str, float]) -> float:
    """DEC-74 (e) / DEC-75, unchanged convention: the WORSE (larger)
    per-window permutation p-value is the one that is judged ("Max-p")."""
    finite = [p for p in p_by_window.values() if p is not None and not math.isnan(p)]
    return max(finite) if finite else float("nan")


# ----------------------------------------------------------------------------
# DEC-75 Entscheidung 1's A3-R liquidity-decile sensitivity
# ----------------------------------------------------------------------------

def liquidity_decile_sensitivity(
    characteristic: np.ndarray, returns: np.ndarray, alive: np.ndarray, turnover_trail: np.ndarray, *,
    convention: ic.Convention = "close_at_last", min_universe: int = 10,
) -> dict[str, Any]:
    """DEC-74 (f) / PRD 5.3 Gate-Text (4): the mean IC with the LOWEST
    trailing-turnover DECILE (D1, PIT) excluded each week -- everything
    else (mask, convention) identical to the unrestricted estimator, so
    the ONLY difference between this and the headline IC is D1's absence.
    Label rule (``gates.evaluate``): ``IC_ohne_D1 <= -0.5*IC_min`` ->
    illiquidity-artifact label, verdict unchanged."""
    n_weeks = alive.shape[0]
    alive_no_d1 = alive.copy()
    for t in range(n_weeks):
        mask = alive[t]
        if int(mask.sum()) < min_universe:
            continue
        buckets = characteristics.decile_bucket(turnover_trail[t], mask)
        alive_no_d1[t] = mask & (buckets != 1)
    res = ic.weekly_ic_series(characteristic, returns, alive_no_d1, convention=convention, min_universe=min_universe)
    return {"mean_ic_without_d1": res["mean_ic"], "n_weeks_used": res["n_weeks_used"]}


# ----------------------------------------------------------------------------
# DEC-75 Entscheidung 1's H-29 bounce fixture
# ----------------------------------------------------------------------------

def bounce_fixture_ic(
    n_weeks: int, n_symbols: int, *, spread: float = 0.003, sigma_true: float = 0.03,
    seed: int = 53, convention: ic.Convention = "close_at_last",
) -> dict[str, Any]:
    """DEC-75 Entscheidung 1 (5) / task brief: a synthetic panel sized
    like the window, TRUE mid-price a random walk (``sigma_true`` weekly
    log-return SD, NO true reversion anywhere), OBSERVED close bouncing
    between bid/ask each week (independent Bernoulli(0.5) side draw per
    symbol-week, half-``spread`` offset) -- purely MECHANICAL bid-ask
    bounce, so any reversal IC this fixture shows is 100% microstructure
    artifact, never economics. Returns the REV-GAP characteristic's mean
    IC on this bounce-only panel (``ic_bounce``) for comparison against
    the REAL rev_gap IC (the caller compares ``|ic_bounce| >= |ic_real|``
    -- H-29's label rule, ``gates.evaluate``)."""
    rng = np.random.default_rng(seed)
    true_log_ret = rng.normal(0.0, sigma_true, size=(n_weeks, n_symbols))
    true_log_price = np.cumsum(true_log_ret, axis=0)
    side = rng.integers(0, 2, size=(n_weeks, n_symbols))       # 0 = bid, 1 = ask
    half_spread_log = math.log(1.0 + spread / 2.0)
    observed_log_price = true_log_price + np.where(side == 1, half_spread_log, -half_spread_log)
    observed_ret = np.diff(observed_log_price, axis=0, prepend=observed_log_price[[0]])
    observed_ret[0] = 0.0
    alive = np.ones((n_weeks, n_symbols), dtype=bool)
    rev_char = characteristics.reversal_gap_characteristic(observed_ret)
    res = ic.weekly_ic_series(rev_char, observed_ret, alive, convention=convention, min_universe=5)
    return {"ic_bounce": res["mean_ic"], "n_weeks": n_weeks, "n_symbols": n_symbols,
            "spread": spread, "sigma_true": sigma_true, "seed": seed}


# ----------------------------------------------------------------------------
# lag profile -1..+2
# ----------------------------------------------------------------------------

def lag_profile(
    characteristic: np.ndarray, returns: np.ndarray, alive: np.ndarray, *,
    lags: tuple[int, ...] = (-1, 0, 1, 2), convention: ic.Convention = "close_at_last",
    min_universe: int = 10,
) -> dict[int, float]:
    """Mean IC of ``characteristic[t]`` against ``returns[t + 1 + lag]``
    for each ``lag`` in ``lags`` -- ``lag=0`` is the REGISTERED
    ``t -> t+1`` relationship every other estimator in this package uses;
    ``lag=-1`` looks one week EARLIER than registered (``t -> t``, i.e.
    same-week, a look-ahead direction never used for a real PASS
    condition), ``lag=1``/``lag=2`` one/two weeks LATER. Implemented by
    shifting ``returns`` (never the characteristic), reusing
    ``ic.weekly_ic_series`` unchanged for every lag."""
    n_weeks = returns.shape[0]
    out: dict[int, float] = {}
    for lag in lags:
        # ic.weekly_ic_series ALREADY does its own t -> t+1 lookup on whatever "returns" array
        # it is given; to make characteristic[t] land on ORIGINAL returns[t+1+lag] we therefore
        # hand it a `shifted` array with shifted[s] = returns[s+lag] (shift = lag, not 1+lag --
        # the "+1" is weekly_ic_series's own, applied AFTER this shift).
        shift = lag
        shifted = np.full_like(returns, np.nan)
        if shift >= 0:
            if shift < n_weeks:
                shifted[:n_weeks - shift] = returns[shift:]
        else:
            shifted[-shift:] = returns[:n_weeks + shift]
        res = ic.weekly_ic_series(characteristic, shifted, alive, convention=convention, min_universe=min_universe)
        out[lag] = res["mean_ic"]
    return out


# ----------------------------------------------------------------------------
# DEC-75 Entscheidung 1 (6): BH within family, report-only
# ----------------------------------------------------------------------------

def benjamini_hochberg(p_by_variant: dict[str, float], *, alpha: float = 0.10) -> dict[str, Any]:
    """Standard Benjamini-Hochberg step-up procedure over the K=7
    variants' Max-p p-values (DEC-74 (e)'s unit). REPORT-ONLY (DEC-75
    Entscheidung 1 (6)): the returned ``reject`` booleans are never fed
    into ``gates.evaluate`` as a gate input, only attached as a label."""
    items = sorted(((v, p) for v, p in p_by_variant.items() if p is not None and not math.isnan(p)),
                    key=lambda vp: vp[1])
    m = len(items)
    reject: dict[str, bool] = {v: False for v in p_by_variant}
    if m == 0:
        return {"alpha": alpha, "m": 0, "reject": reject, "largest_rejected_rank": None}
    largest_rank = None
    for rank, (variant, p) in enumerate(items, start=1):
        if p <= (rank / m) * alpha:
            largest_rank = rank
    if largest_rank is not None:
        for rank, (variant, _p) in enumerate(items, start=1):
            if rank <= largest_rank:
                reject[variant] = True
    return {"alpha": alpha, "m": m, "reject": reject, "largest_rejected_rank": largest_rank}


# ----------------------------------------------------------------------------
# DEC-75 Entscheidung 1 (4): H-30's vol-weighted, drag-adjusted outcome,
# substituted for the raw next-week return before the SAME (1)/(2) machinery
# every other variant uses.
# ----------------------------------------------------------------------------

def prealigned_outcome_to_returns_like(prealigned_outcome: np.ndarray) -> np.ndarray:
    """``ic.vol_weighted_outcome_with_drag``'s output has row ``t`` ALREADY
    representing week ``t``'s formation view of week ``t+1``'s (weighted,
    drag-adjusted) outcome -- but ``ic.weekly_ic_series`` (and every
    function built on it: SE, the bootstrap, the permutation null) does
    its OWN ``returns[t+1]`` lookup internally. This shifts the
    pre-aligned array back by one week (``shifted[t+1] = prealigned[t]``,
    ``shifted[0] = NaN``) so it can be handed to ``ic.weekly_ic_series``
    (or any of this module's functions that take a ``returns``-shaped
    array) as a drop-in replacement for the raw return panel -- the SAME
    trick :func:`lag_profile` uses for its own (documented) shift."""
    n_weeks = prealigned_outcome.shape[0]
    shifted = np.full_like(prealigned_outcome, np.nan)
    shifted[1:] = prealigned_outcome[:-1]
    return shifted


def h30_outcome_for_window(returns: np.ndarray, vol_rv: np.ndarray) -> np.ndarray:
    """DEC-75 Entscheidung 1 (4): the ``returns``-shaped array H-30's
    variant (whichever ``vol_*`` variant the registration names) is
    judged against, in place of the raw next-week return -- vol-weighted
    (``target_vol/vol_rv[t]``, PIT), drag-adjusted (`sigma_w[t]^2/2`
    subtracted from the UNWEIGHTED outcome first). See
    :func:`prealigned_outcome_to_returns_like` for the shift this needs.
    **Documented composition choice (orchestrator confirmation needed):**
    DEC-75 does not spell out how the beta-control PASS component
    (Entscheidung 1 (3)) composes with H-30's vol-weighted outcome;
    :func:`run_full` applies the SAME uniform beta-residualisation to
    whichever ``returns``-shaped array a hypothesis is judged on --
    for H-30 that is THIS function's output, residualised against the
    RAW ``beta * r_BTC`` control every other variant uses. This is the
    simplest defensible uniform treatment, not a re-derivation of (3) for
    the vol-weighted case specifically."""
    vw = ic.vol_weighted_outcome_with_drag(returns, vol_rv, weight_source="pit")
    return prealigned_outcome_to_returns_like(vw["weighted_outcome"])


# ----------------------------------------------------------------------------
# per-variant/window payload assembly (feeds gates.evaluate)
# ----------------------------------------------------------------------------

def variant_window_payload(
    characteristic: np.ndarray, returns: np.ndarray, alive: np.ndarray, symbols: list[str], *,
    variant: str, direction: str, ic_min_capped: float, w_judged: int,
    floor: float, selection_ceiling_mean_of_max: float,
    beta_8w_pit: np.ndarray | None = None, market_symbol: str = "BTCUSDT",
    convention: ic.Convention = "close_at_last",
    n_reps_bootstrap: int = 1000, n_reps_permutation: int = 1000, seed: int = 53,
    block_size: int = 4, ci_level: float = 1.0 - 0.0064,
    report_drop_convention: bool = True, report_lag_profile: bool = True,
    report_beta_calibration: bool = True,
    res_quantile_drifting: float | None = None,
    beta_control_method: str | None = None, beta_control_pit: np.ndarray | None = None,
) -> dict[str, Any]:
    """Assembles ONE window's numbers for ``gates.evaluate`` -- the real
    IC series, SE (item 1), bootstrap CI bound (item 1), block-permutation
    p-value (item 2, ``nulls.block_permutation_pvalue`` reused unchanged),
    and the beta-control residualised IC (item 3, ``ic.residualize_
    outcome`` reused unchanged) -- plus the REPORT-ONLY task-brief items:
    the ``"drop"``-convention sensitivity mean IC, the ``-1..+2`` lag
    profile (:func:`lag_profile`), and (when ``beta_8w_pit`` is given) the
    PURE beta-characteristic's own calibration IC against the SAME
    outcome (never a gate input, purely descriptive: how much of a raw IC
    a symbol's beta ALONE would explain). This is the REAL
    characteristic-vs-REAL-outcome computation THE SEAL forbids in
    ``--prelaunch`` -- this function is run-mode-only, never called from
    ``prelaunch.py``.

    **DEC-77 Entscheidung 2, additive:** ``beta_control_method`` (one of
    :data:`ic.BETA_CONTROL_METHODS`, ``None`` by default) selects HOW
    ``residualized_mean_ic`` is computed, via :func:`ic.apply_beta_control`
    -- the SAME dispatcher the calibration study uses, so a real run's
    beta control behaves IDENTICALLY to how it was calibrated.
    ``beta_control_pit`` must be the matching trailing-window PIT beta
    (unused for ``method in (None, "none")``). **Backward compatible:**
    leaving ``beta_control_method`` at its default ``None`` falls back to
    the EXACT pre-DEC-77 behaviour (``ic.residualize_outcome`` with
    ``beta_8w_pit`` directly, fixed 8-week) -- every caller that predates
    DEC-77 is unaffected.

    ``res_quantile_drifting`` (DEC-76 Entscheidung 1 (b), additive): the
    FROZEN registered-YAML constant for THIS hypothesis/window -- the
    drifting factor null's residualised-mean-IC one-sided quantile
    (``nulls.factor_preserving_null(..., drift_f=nulls.DRIFT_F_DRIFTING)``'s
    ``variants[variant]["quantile_one_sided_residualized"]``). This
    function does NOT compute it (that is :func:`run_full`'s job, ONCE per
    window, shared across all 7 variants, plus the +/-10% calibration
    assertion against the registered value) -- it only carries the number
    through into the payload ``gates.evaluate`` reads. ``None`` (the
    default) means "not supplied" -- ``gates._window_pass`` treats that as
    the component being trivially satisfied (backward compatible with
    every pre-DEC-76 caller of this function)."""
    res = ic.weekly_ic_series(characteristic, returns, alive, convention=convention)
    ic_weekly = np.array([w["ic"] for w in res["weekly"]], dtype=np.float64)
    se_info = se_of_mean_ic(ic_weekly, floor, w_judged)
    ci_info = moving_block_bootstrap_ci(ic_weekly, direction=direction, block_size=block_size,
                                         n_reps=n_reps_bootstrap, seed=seed, level=ci_level)
    perm = nulls.block_permutation_pvalue(res["mean_ic"], characteristic, returns, alive,
                                           direction=direction, convention=convention,
                                           block_size=block_size, n_reps=n_reps_permutation, seed=seed)

    residualized_mean_ic = None
    beta_control_coverage = None
    if beta_control_method is None:
        # Pre-DEC-77 fallback, UNCHANGED: fixed 8-week ic.residualize_outcome.
        if beta_8w_pit is not None and market_symbol in symbols:
            r_btc = returns[:, symbols.index(market_symbol)]
            resid = ic.residualize_outcome(returns, beta_8w_pit, r_btc)
            res_resid = ic.weekly_ic_series(characteristic, resid, alive, convention=convention)
            residualized_mean_ic = res_resid["mean_ic"]
    elif beta_control_method != "none":
        applied = ic.apply_beta_control(beta_control_method, characteristic, returns, alive,
                                         beta_pit=beta_control_pit, symbols=symbols, market_symbol=market_symbol)
        res_resid = ic.weekly_ic_series(applied["characteristic"], applied["returns"], alive, convention=convention)
        residualized_mean_ic = res_resid["mean_ic"]
        beta_control_coverage = applied["coverage"]

    mean_ic_drop_convention = None
    if report_drop_convention and convention != "drop":
        mean_ic_drop_convention = ic.weekly_ic_series(characteristic, returns, alive, convention="drop")["mean_ic"]

    lag_profile_result = (lag_profile(characteristic, returns, alive, convention=convention)
                           if report_lag_profile else None)

    beta_calibration_mean_ic = None
    if report_beta_calibration and beta_8w_pit is not None:
        beta_calibration_mean_ic = ic.weekly_ic_series(beta_8w_pit, returns, alive, convention=convention)["mean_ic"]

    return {
        "mean_ic": res["mean_ic"], "ic_weekly": ic_weekly.tolist(), "se": se_info["se"],
        "se_detail": se_info, "ci_bound_toward_sign": ci_info["ci_bound_toward_sign"], "ci_detail": ci_info,
        "block_permutation_p": perm["p_value"], "block_permutation_detail": perm,
        "ic_min_capped": ic_min_capped, "residualized_mean_ic": residualized_mean_ic,
        "res_quantile_drifting": res_quantile_drifting,      # DEC-76 Entscheidung 1 (b), frozen registered value
        "beta_control_method": beta_control_method, "beta_control_coverage": beta_control_coverage,
        "mean_ic_drop_convention": mean_ic_drop_convention, "lag_profile": lag_profile_result,
        "beta_calibration_mean_ic": beta_calibration_mean_ic,
        "selection_ceiling_mean_of_max": selection_ceiling_mean_of_max,
        "n_weeks_used": res["n_weeks_used"], "variant": variant, "convention": convention,
    }


def run_hypothesis(
    hypothesis: str, variant: str, direction: str,
    char_by_window: dict[str, np.ndarray], returns_by_window: dict[str, np.ndarray],
    alive_by_window: dict[str, np.ndarray], symbols: list[str],
    ic_min_capped_by_window: dict[str, float], w_judged_by_window: dict[str, int],
    floor_by_window: dict[str, float], selection_ceiling_by_window: dict[str, float], *,
    beta_8w_pit_by_window: dict[str, np.ndarray] | None = None,
    liquidity_ic_without_d1: float | None = None, bounce_ic: float | None = None,
    persistence_null_pass: bool | None = None, bh_fdr_pass: bool | None = None,
    convention: ic.Convention = "close_at_last",
    n_reps_bootstrap: int = 1000, n_reps_permutation: int = 1000, seed: int = 53,
    res_quantile_drifting_by_window: dict[str, float] | None = None,
    beta_control_method: str | None = None,
    beta_control_pit_by_window: dict[str, np.ndarray] | None = None,
) -> dict[str, Any]:
    """One hypothesis, BOTH judgement windows (C.10 hard) -> the full
    ``gates.evaluate`` payload + verdict. Windows are keyed ``"W1"``/
    ``"W2"`` throughout. ``res_quantile_drifting_by_window`` (DEC-76
    Entscheidung 1 (b), additive, ``None`` by default) carries the FROZEN
    registered per-window beta-control quantile through to each window's
    payload -- see :func:`variant_window_payload`'s docstring.
    ``beta_control_method``/``beta_control_pit_by_window`` (DEC-77
    Entscheidung 2, additive, ``None`` by default -- exact pre-DEC-77
    fallback via ``beta_8w_pit_by_window``) select the registered
    beta-control method, see :func:`variant_window_payload`'s docstring."""
    windows_payload: dict[str, Any] = {}
    for wname in ("W1", "W2"):
        beta_8w = beta_8w_pit_by_window.get(wname) if beta_8w_pit_by_window else None
        rqd = res_quantile_drifting_by_window.get(wname) if res_quantile_drifting_by_window else None
        beta_control_pit = beta_control_pit_by_window.get(wname) if beta_control_pit_by_window else None
        windows_payload[wname] = variant_window_payload(
            char_by_window[wname], returns_by_window[wname], alive_by_window[wname], symbols,
            variant=variant, direction=direction, ic_min_capped=ic_min_capped_by_window[wname],
            w_judged=w_judged_by_window[wname], floor=floor_by_window[wname],
            selection_ceiling_mean_of_max=selection_ceiling_by_window[wname],
            beta_8w_pit=beta_8w, convention=convention,
            n_reps_bootstrap=n_reps_bootstrap, n_reps_permutation=n_reps_permutation, seed=seed,
            res_quantile_drifting=rqd,
            beta_control_method=beta_control_method, beta_control_pit=beta_control_pit)

    payload = {
        "hypothesis": hypothesis, "variant": variant, "direction": direction,
        "windows": windows_payload,
        "persistence_null_pass": persistence_null_pass, "bh_fdr_pass": bh_fdr_pass,
        "liquidity_ic_without_d1": liquidity_ic_without_d1, "bounce_ic": bounce_ic,
    }
    verdict = gates.evaluate(payload)
    return {"payload": payload, "verdict": verdict}


# ----------------------------------------------------------------------------
# top-level orchestrator
# ----------------------------------------------------------------------------

def run_full(
    panel: dict[str, Any], weekly: dict[str, Any], registered: dict[str, Any], *,
    convention: ic.Convention = "close_at_last",
) -> dict[str, Any]:
    """Panel + registered YAML -> every hypothesis's verdict. Builds all 7
    characteristics ONCE on the full panel (DEC-75 (8)), slices to W1/W2/L,
    computes the DEC-77/DEC-78 beta-controlled null ONCE per window (shared
    across all 7 variants: the GL-012 ceiling and the beta-control PASS
    quantile per variant, :func:`nulls.beta_controlled_factor_null`, ONE
    call per window under the REGISTERED ``beta_control.method``, driftfree
    -- DEC-77 Entscheidung 1 (c)'s "rho als Stress-Variante behalten").

    **DEC-78 Entscheidung 1, revised by its Nachtrag, "stress" null's
    construction:** ``rho_f``/``beta_sd`` for this null come DIRECTLY from
    ``registered["calibration"]["stress"]`` (see :data:`REGISTERED_
    SCHEMA_HINT`) -- ``rho_f = calibration.stress.rho_f``, ``beta_sd =
    calibration.stress.beta_sd_calibrated`` -- the SAME pair for BOTH
    windows (a single global calibration, same convention as DEC-75's own
    ``rho_f=0.2``). **No re-search/re-derivation happens at run time**
    (DEC-78 Nachtrag, orchestrator decision): ``beta_sd_calibrated`` is
    read exactly as the prelaunch artifact's bisection search
    (:func:`nulls.calibrate_beta_sd_to_observed_share`) already produced
    it. ``registered["calibration"]`` ABSENT (a pre-DEC-78 registered
    file) falls back to the OLD hardcoded stress null (``rho_f=0.2``,
    beta drawn ``U(0.5, 2.0)`` via ``beta_sd=None``), documented, not a
    registered Drittfassung run -- the used pair and its source are
    echoed in the return value's ``calibration_used_for_stress_null``.
    Either way, the recomputed null is asserted within +/-10% of the
    registered YAML's FROZEN values (:func:`assert_null_calibration`,
    loud fail ``NullCalibrationError`` otherwise, BEFORE any verdict),
    then runs each registered hypothesis via :func:`run_hypothesis`
    against the FROZEN (registered) values. L is computed for
    descriptive/sealed purposes only (never enters a verdict).

    **DEC-77 Entscheidung 2, C.14 loud fail:** ``registered["beta_control"]``
    (``{"method": <one of ic.BETA_CONTROL_METHODS>, "beta_window_weeks":
    <int|None>}``) is REQUIRED -- a missing key, an empty/unrecognised
    ``method``, or a ``beta_window_weeks`` that does not match the
    method's own implied trailing window all raise :class:`ValueError`
    BEFORE any panel arithmetic runs, so a registered file emitted by
    ``--emit-registered-template`` (``method: ""``) can never silently
    reach a verdict without the orchestrator filling it in."""
    from . import prelaunch  # local import: prelaunch.slice_window, avoids a module cycle at import time

    rules = registered.get("rules", {})
    seed = int(rules.get("seed", 53))
    n_reps_bootstrap = int(rules.get("n_reps_bootstrap", 1000))
    n_reps_permutation = int(rules.get("n_reps_permutation", 1000))
    # DEC-76 Task A item 4: the canonical rules key is `n_reps` (>= 1000); the legacy
    # `n_reps_factor_null` (DEC-75) is still read as a fallback for a pre-DEC-76 registered file.
    n_reps_factor_null = int(rules.get("n_reps", rules.get("n_reps_factor_null", 1000)))
    null_quantile_level = float(rules.get("level", nulls.SELECTION_CEILING_ONE_SIDED_QUANTILE))
    bh_alpha = float(rules.get("bh_alpha", 0.10))

    # DEC-77 Entscheidung 2: the registered beta-control method -- C.14 loud fail, no fallback.
    beta_control_cfg = registered.get("beta_control")
    if not isinstance(beta_control_cfg, dict) or not beta_control_cfg.get("method"):
        raise ValueError(
            "registered YAML fehlt beta_control.method (DEC-77 Entscheidung 2) oder es ist leer -- "
            "kein Lauf ohne vom Orchestrator gewaehlte Beta-Kontroll-Methode (loud fail, kein "
            "Verdikt). --emit-registered-template schreibt method:\"\" als Platzhalter; die "
            "Drittfassung muss ihn vor der Registrierung fuellen.")
    beta_control_method = beta_control_cfg["method"]
    beta_control_trail_win = ic.beta_control_trail_weeks(beta_control_method)   # raises on an unknown method
    reg_beta_window = beta_control_cfg.get("beta_window_weeks")
    if beta_control_trail_win is not None and reg_beta_window != beta_control_trail_win:
        raise ValueError(
            f"registered beta_control.beta_window_weeks ({reg_beta_window!r}) passt nicht zum "
            f"von beta_control.method={beta_control_method!r} implizierten Fenster "
            f"({beta_control_trail_win}) -- loud fail, kein Verdikt.")

    weeks = weekly["weeks"]
    symbols = panel["symbols"]
    returns, alive = weekly["returns"], weekly["alive"]
    all_char = build_all_characteristics_full_panel(returns, panel, weeks, symbols)
    turnover_weekly = characteristics.weekly_turnover(panel, weeks)
    turnover_trail = characteristics.trailing_median_turnover(turnover_weekly)
    beta_8w_pit = all_char["vol_beta"]
    # DEC-77 Entscheidung 2: the registered method's OWN trailing-window PIT beta, built on the
    # FULL panel first (DEC-75 (8) discipline), sliced per window below -- "none" needs none.
    beta_control_pit_full = None
    if beta_control_trail_win is not None:
        beta_control_pit_full = characteristics.beta_characteristic(
            returns, symbols, market_symbol="BTCUSDT", trail_win=beta_control_trail_win,
            min_weeks=beta_control_trail_win)

    windows: dict[str, dict[str, Any]] = {}
    for wname in ("W1", "W2", "L"):
        wcfg = registered["windows"].get(wname)
        if wcfg is None:
            continue
        window = prelaunch.slice_window(weeks, wcfg["start"], wcfg["end"], returns, alive)
        lo, hi = window["lo"], window["hi"]
        window["characteristics"] = {v: arr[lo:hi] for v, arr in all_char.items()}
        window["turnover_trail"] = turnover_trail[lo:hi]
        window["symbols"] = symbols
        window["beta_control_pit"] = beta_control_pit_full[lo:hi] if beta_control_pit_full is not None else None
        windows[wname] = window

    # DEC-78 Entscheidung 1/Nachtrag: the "stress" null's (rho_f, beta_sd_calibrated) -- a
    # SINGLE global pair, read DIRECTLY from registered["calibration"]["stress"] (--emit-
    # registered-template's W1-sourced block, REGISTERED_SCHEMA_HINT) when present, applied
    # IDENTICALLY to both windows below (the same single-global-constant convention DEC-75's
    # own rho_f=0.2 used). NO re-search/re-derivation at run time (DEC-78 Nachtrag): beta_sd is
    # whatever the prelaunch artifact's bisection search already calibrated. Absent (pre-DEC-78
    # registered file): falls back to the OLD hardcoded stress null (rho_f=0.2, beta drawn
    # U(0.5, 2.0) via beta_sd=None) -- documented, not a registered Drittfassung run.
    calibration_cfg = registered.get("calibration")
    if isinstance(calibration_cfg, dict) and isinstance(calibration_cfg.get("stress"), dict):
        stress_block = calibration_cfg["stress"]
        stress_rho_f = float(stress_block["rho_f"])
        stress_beta_sd = float(stress_block["beta_sd_calibrated"])
        calibration_source = "registered.calibration.stress (DEC-78 Nachtrag, bisection-calibrated, kein Re-Search)"
    else:
        stress_rho_f, stress_beta_sd = 0.2, None
        calibration_source = "pre-DEC-78-Nachtrag Fallback (rho_f=0.2, beta ~ U(0.5, 2.0), kein calibration-Block)"

    floor_by_window, wjudged_by_window, ceiling_by_window = {}, {}, {}
    res_quantile_drifting_by_window: dict[str, dict[str, float]] = {}
    beta_control_pit_by_window: dict[str, np.ndarray | None] = {}
    null_calibration_report: dict[str, Any] = {}
    for wname in ("W1", "W2"):
        w = windows[wname]
        f = nulls.analytic_permutation_floor(w["alive"], w["weeks"])
        floor_by_window[wname] = f["e_floor"]
        wjudged_by_window[wname] = f["w_judged"]
        beta_control_pit_by_window[wname] = w["beta_control_pit"]

        # DEC-77 Entscheidung 2, "stress" calibration revised by DEC-78 Entscheidung 1: ONE
        # beta-controlled null per window (registered method, driftfree -- DEC-77's own
        # "Anlass": rho_f alone, no drift, already produces the artifact) gives BOTH the
        # GL-012 ceiling and the per-variant beta-control PASS quantile, shared across all 7
        # variants. rho_f/beta_sd come from calibration_source above (SAME pair for both
        # windows).
        bcn = nulls.beta_controlled_factor_null(
            w["returns"], w["alive"], symbols, method=beta_control_method,
            variants=characteristics.VARIANT_NAMES, convention=convention,
            n_reps=n_reps_factor_null, seed=seed, quantile=null_quantile_level,
            rho_f=stress_rho_f, drift_f=nulls.DRIFT_F_DRIFTFREE, beta_sd=stress_beta_sd)

        recomputed_ceiling_res = bcn["ceiling_mean_of_max"]
        recomputed_quantiles = {v: bcn["variants"][v]["quantile_one_sided"]
                                 for v in characteristics.VARIANT_NAMES}

        reg_window_cfg = registered["windows"].get(wname, {})
        reg_ceiling_res = reg_window_cfg.get("ceiling_driftfree_res")
        reg_quantiles = reg_window_cfg.get("res_quantile_drifting") or {}

        # C.14 loud fail: a present-but-drifted registered constant aborts the WHOLE run,
        # before any hypothesis gets a verdict -- see assert_null_calibration's docstring.
        assert_null_calibration(recomputed_ceiling_res, reg_ceiling_res,
                                 label=f"ceiling_driftfree_res[{wname}]")
        ceiling_by_window[wname] = reg_ceiling_res if reg_ceiling_res is not None else recomputed_ceiling_res

        res_quantile_drifting_by_window[wname] = {}
        for v in characteristics.VARIANT_NAMES:
            reg_q = reg_quantiles.get(v) if isinstance(reg_quantiles, dict) else None
            assert_null_calibration(recomputed_quantiles[v], reg_q,
                                     label=f"res_quantile_drifting[{wname}][{v}]")
            res_quantile_drifting_by_window[wname][v] = reg_q if reg_q is not None else recomputed_quantiles[v]

        null_calibration_report[wname] = {
            "ceiling_driftfree_res_recomputed": recomputed_ceiling_res,
            "ceiling_driftfree_res_registered": reg_ceiling_res,
            "res_quantile_drifting_recomputed": recomputed_quantiles,
            "res_quantile_drifting_registered": dict(reg_quantiles) if isinstance(reg_quantiles, dict) else {},
        }

    results: dict[str, Any] = {}
    p_by_variant: dict[str, float] = {}
    for hyp, hcfg in registered["hypotheses"].items():
        variant, direction = hcfg["variant"], hcfg["direction"]
        is_vol_weighted = hcfg.get("outcome") == "vol_weighted"
        char_by_window = {wn: windows[wn]["characteristics"][variant] for wn in ("W1", "W2")}
        if is_vol_weighted:
            # DEC-75 Entscheidung 1 (4): H-30 is judged against the vol-weighted,
            # drag-adjusted outcome, not the raw next-week return.
            returns_by_window = {
                wn: h30_outcome_for_window(windows[wn]["returns"], windows[wn]["characteristics"]["vol_rv"])
                for wn in ("W1", "W2")
            }
        else:
            returns_by_window = {wn: windows[wn]["returns"] for wn in ("W1", "W2")}
        alive_by_window = {wn: windows[wn]["alive"] for wn in ("W1", "W2")}
        ic_min_by_window = {wn: registered["windows"][wn]["ic_min_capped"][variant] for wn in ("W1", "W2")}
        # NOTE (documented interpretation, orchestrator confirmation needed before a real
        # Drittfassung run cites it): the beta-control (DEC-75 (3)) is applied to whichever
        # `returns_by_window` array this hypothesis is judged on -- for `outcome: vol_weighted`
        # (H-30) that is the ALREADY vol-weighted/drag-adjusted/shifted array, residualised
        # against the SAME raw beta*r_BTC control every other variant uses. DEC-75 does not
        # spell out how (3) and (4) compose; this is the simplest uniform treatment, not a
        # re-derivation.
        beta_by_window = {wn: windows[wn]["characteristics"]["vol_beta"] for wn in ("W1", "W2")}

        liquidity = None
        if variant == "rev_gap":
            liq = liquidity_decile_sensitivity(char_by_window["W1"], returns_by_window["W1"],
                                                alive_by_window["W1"], windows["W1"]["turnover_trail"],
                                                convention=convention)
            liquidity = liq["mean_ic_without_d1"]

        bounce_ic_val = None
        if hyp == "H-29" or variant == "rev_gap":
            k_median = int(np.median(alive_by_window["W1"].sum(axis=1)))
            bf = bounce_fixture_ic(alive_by_window["W1"].shape[0], max(k_median, 10), seed=seed,
                                    convention=convention)
            bounce_ic_val = bf["ic_bounce"]

        pnull = nulls.persistence_null(windows["W1"]["returns"], windows["W1"]["alive"], windows["W1"]["weeks"],
                                        variants=(variant,), convention=convention, n_sims=200, seed=seed)
        real_mean_ic_w1 = ic.weekly_ic_series(char_by_window["W1"], returns_by_window["W1"],
                                               alive_by_window["W1"], convention=convention)["mean_ic"]
        q = pnull["variants"][variant]["quantile95_registered_direction"]
        persistence_pass = (real_mean_ic_w1 > q) if direction == "positive" else (real_mean_ic_w1 < q)

        rqd_by_window = {wn: res_quantile_drifting_by_window[wn][variant] for wn in ("W1", "W2")}
        run_res = run_hypothesis(
            hyp, variant, direction, char_by_window, returns_by_window, alive_by_window, symbols,
            ic_min_by_window, wjudged_by_window, floor_by_window, ceiling_by_window,
            beta_8w_pit_by_window=beta_by_window, liquidity_ic_without_d1=liquidity, bounce_ic=bounce_ic_val,
            persistence_null_pass=bool(persistence_pass), bh_fdr_pass=None,
            convention=convention, n_reps_bootstrap=n_reps_bootstrap, n_reps_permutation=n_reps_permutation,
            seed=seed, res_quantile_drifting_by_window=rqd_by_window,
            beta_control_method=beta_control_method, beta_control_pit_by_window=beta_control_pit_by_window)
        results[hyp] = run_res
        p_by_variant[variant] = max_p_over_windows({
            wn: run_res["payload"]["windows"][wn]["block_permutation_p"] for wn in ("W1", "W2")})

    bh = benjamini_hochberg(p_by_variant, alpha=bh_alpha)
    for hyp, hcfg in registered["hypotheses"].items():
        results[hyp]["payload"]["bh_fdr_pass"] = bh["reject"].get(hcfg["variant"])
        results[hyp]["verdict"] = gates.evaluate(results[hyp]["payload"])

    windows_meta = {wn: {"weeks": windows[wn]["weeks"], "n_weeks": len(windows[wn]["weeks"])}
                     for wn in windows}
    l_window_sealed = windows_meta.pop("L", None)     # DEC-74 (k)/DEC-75 (8): L stays sealed, never in the open report
    if l_window_sealed is not None:
        windows_meta["L"] = {"available": True, "note": "siehe l_window_sealed_json (DEC-74 (k))"}

    return {
        "wp": "WP-13", "mode": "run", "results": results, "bh": bh,
        "windows_meta": windows_meta, "_l_window_sealed": l_window_sealed,
        "seed": seed, "convention": convention,
        "n_reps_bootstrap": n_reps_bootstrap, "n_reps_permutation": n_reps_permutation,
        "n_reps_factor_null": n_reps_factor_null,
        "null_calibration": null_calibration_report,   # DEC-76 Task A item 3: recomputed vs. registered
        "beta_control": {"method": beta_control_method, "beta_window_weeks": beta_control_trail_win},
        "calibration_used_for_stress_null": {   # DEC-78 Entscheidung 1/Nachtrag: audit trail
            "rho_f": stress_rho_f, "beta_sd_calibrated": stress_beta_sd, "source": calibration_source},
    }


def write_run_artifacts(out_dir: Path | str, report: dict[str, Any]) -> dict[str, Any]:
    """DEC-53 artifacts for the run report: per-hypothesis/window weekly IC
    series as CSV (the real series, sha256'd), the main JSON (L window
    sealed into its own file, same discipline as ``prelaunch.
    write_prelaunch_artifacts``), and a fingerprint file for the
    bootstrap/permutation replicates (seed + sha256 of the concatenated
    draws, per DEC-53's "Cluster-Serie + Bootstrap-Replikate/Seed"
    requirement -- the raw 1000-replicate arrays themselves are not
    re-dumped here, only their seed and a content fingerprint, which is
    sufficient for a byte-exact re-derivation given this module's
    determinism)."""
    out_dir = Path(out_dir)
    if "data/harvest" in out_dir.as_posix():
        raise ValueError(f"refusing to write under data/harvest: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, Any] = {}

    for hyp, res in report["results"].items():
        for wname, w in res["payload"]["windows"].items():
            csv_path = out_dir / f"wp13_run_{hyp}_{wname}_ic_weekly.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                writer.writerow(["t", "ic"])
                for t, val in enumerate(w["ic_weekly"]):
                    writer.writerow([t, val])
            artifacts[csv_path.name] = {"path": str(csv_path), "sha256": panel_load.sha256_file(csv_path)}

    main_report = dict(report)
    main_report["results"] = {
        hyp: {"payload": {k: v for k, v in res["payload"].items()}, "verdict": res["verdict"]}
        for hyp, res in report["results"].items()
    }
    l_window_sealed = main_report.pop("_l_window_sealed", None)   # never goes into the open JSON
    main_json = out_dir / "wp13_run.json"
    main_json.write_text(json.dumps(main_report, indent=1, default=str), encoding="utf-8")
    artifacts["wp13_run_json"] = {"path": str(main_json), "sha256": panel_load.sha256_file(main_json)}

    if l_window_sealed is not None:
        l_path = out_dir / "wp13_run_L_window_sealed.json"
        l_path.write_text(json.dumps(l_window_sealed, indent=1, default=str), encoding="utf-8")
        artifacts["l_window_sealed_json"] = {"path": str(l_path), "sha256": panel_load.sha256_file(l_path)}

    return {"out_dir": str(out_dir), "artifacts": artifacts}
