"""WP-13 -- RUN MODE (DEC-75 Entscheidung 1 (1)-(7), Entscheidung 2 last
sentence: "Der Lauf-Modus wird im selben Bau angelegt, aber mit
Startsperre"; reworked for the Drittfassung H-28..H-30 by DEC-87).

**START LOCK (the whole point of this module's CLI wiring,
``scripts/wp13_xsec.py --run``).** The run mode computes REAL
characteristic-vs-real-outcome ICs -- THE thing ``--prelaunch`` is
structurally forbidden from ever doing (see ``ic.py``'s module docstring,
"THE SEAL"). It may therefore ONLY run against a ``--registered`` YAML file
(the Drittfassung's threshold block: ``ic_min_capped`` per variant/window,
``W_judged``, rules) whose sha256 matches an explicit ``--registered-sha256``
the caller supplies. This module itself never checks the hash -- that is the
CLI's job (``scripts/wp13_xsec.py``'s ``cmd_run``) so the check happens BEFORE
a single byte of real panel data is touched; :func:`load_registered_yaml` here
is a plain, hash-agnostic YAML loader used only AFTER the CLI's lock has
already passed.

**DEC-75 (8) / task brief item 8: characteristics-on-full-panel-first.**
Every variant's characteristic is built ONCE on the FULL panel (all weeks, all
symbols, via ``characteristics.compute_all_characteristics``), THEN sliced to a
window -- the IDENTICAL path ``prelaunch.py``'s ``vol_rv``/``turnover_trail``
construction already uses. :func:`build_all_characteristics_full_panel` is the
single, shared entry point both modes use.

**Module layout.** Every numbered DEC-75 Entscheidung 1 (1)-(7) run-mode
component is its OWN pure, independently-testable function below
(``se_of_mean_ic``, ``moving_block_bootstrap_ci``,
``liquidity_decile_sensitivity``, ``bounce_fixture_ic``, ``lag_profile``,
``benjamini_hochberg``); :func:`variant_window_payload` assembles ONE
variant/window's numbers into exactly the shape ``gates.evaluate`` expects;
:func:`run_hypothesis` calls it for both judgement windows and hands the
assembled payload to ``gates.evaluate``; :func:`run_full` is the top-level
orchestrator (panel -> per-entry verdicts + per-hypothesis aggregation). The CLI
(``scripts/wp13_xsec.py``) owns I/O and the START LOCK; nothing in this module
reads a CLI flag, and the only file I/O is :func:`write_run_artifacts`/
:func:`verify_run_artifacts` (DEC-53) and :func:`load_registered_yaml`.

**DEC-87 (Drittfassung H-28..H-30), what changed here.**
  (D) calibration is read PER WINDOW (``windows.<W>.calibration``); the old
      global ``calibration`` block is refused loudly (C.14).
  (A) the GL-012-binding ceiling is the registered method's stress ceiling of
      the window (``windows.<W>.ceiling_method_stress``), recomputed (+-10 %).
  (E) the beta-control quantile is the more extreme of the driftfree and the
      drifting (0.002/week) stress-null quantile, both frozen and re-checked.
  (G) H-30: weekly vol ``sigma_w = sqrt(n_t) * vol_rv``, outcome ``r_log +
      sigma_w^2/2`` (``ic.vol_weighted_outcome_with_drag``).
  (I) Gate (4): bounce kills the PASS per window, liquidity label per window
      (``gates.evaluate``); Gate (5) feeds ``gates.evaluate`` for H-30.
  (J) one ENTRY per variant (``H-28_mom1`` ... ``H-30_vol_beta``); a hypothesis
      is PASS iff at least one of its variants is; the BH denominator is fixed 7
      (variants not computed or locked, ``status: gl012_pre_run``, count with
      p = 1).
  (V7) DEC-53: the raw AND the residualised weekly IC series per entry/window,
      bootstrap/permutation replicate fingerprints + seed and a generator
      fingerprint (code hash, commit, data fingerprints, parameters) are
      written; a missing/inconsistent mandatory artifact aborts loudly -- KEIN
      VERDIKT (:class:`RunArtifactError`). (V9) the union-range fingerprint and
      the ``delisting_dates.json`` sha256 are checked against the YAML's
      ``data_fingerprints`` (:class:`DataFingerprintError`).

**T3 (checkpoint round trip).** The run is a single pass without checkpoint or
resume state, so there is nothing to round-trip; the persisted state IS the
artifact set, whose round trip is T7 (:func:`verify_run_artifacts` re-derives the
gate estimators from the written files bit for bit). Adding a checkpoint later
requires a real T3 (``tests/unit/test_wp13_run.py::test_dec87_t3_*`` pins this).
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
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
    "RunAbort", "NullCalibrationError", "DataFingerprintError", "RunArtifactError",
    "RegisteredSchemaError", "NULL_CALIBRATION_REL_TOL", "GL012_PRE_RUN",
    "validate_registered", "check_data_fingerprints", "hypothesis_group", "h30_outcome_for_window",
    "aggregate_hypotheses",
    "variant_window_payload", "run_hypothesis", "run_full", "registered_constants_pin",
    "code_fingerprint", "result_fingerprint", "write_run_artifacts", "verify_run_artifacts",
]

#: DEC-76 Entscheidung 1 (b)/Task A item 3: +/-10% tolerance between the
#: run's own recomputed null constant (real K series, real W_judged) and
#: the value FROZEN in the registered YAML.
NULL_CALIBRATION_REL_TOL = 0.10

#: DEC-87 (J): the ``status`` of a hypothesis ENTRY that is locked by GL-012 BEFORE the run
#: (feasibility, power or structural neutralisation decided mechanically in the Vorlauf); the
#: run does not compute it, it counts with p = 1 in the fixed-7 BH denominator.
GL012_PRE_RUN = "gl012_pre_run"

REGISTERED_SCHEMA_HINT = (
    "hypotheses: {<entry id, e.g. H-28_mom1>: {hypothesis?: H-28 (default: id prefix), variant: str, "
    "direction: positive|negative, outcome?: vol_weighted (required for H-30), "
    "status?: gl012_pre_run + reason: str (DEC-87 (J): locked, not computed, p = 1)}} -- one entry per "
    "variant, each variant at most once; a hypothesis is PASS iff at least one of its variants is; "
    "windows: {W1: {start, end, ic_min_capped: {variant: float}, w_judged: int, "
    "calibration: {measured: {rho_f, beta_sd_calibrated, target_factor_share}, stress: {...}, zero: {...}} "
    "(DEC-87 (D): PER WINDOW, `stress` REQUIRED; a top-level `calibration` block is refused loudly), "
    "ceiling_method_stress: float (DEC-87 (A): the registered method's mean-of-max ceiling under the "
    "window's stress calibration, driftfree, seed 53 -- GL-012-binding; renamed from the pre-DEC-87 "
    "`ceiling_driftfree_res`, which is refused), "
    "res_quantile_driftfree: {variant: float}, res_quantile_drifting: {variant: float} (DEC-87 (E): "
    "99.36 % quantile of the residualised mean IC under the stress null with drift 0 / 0.002 per week, "
    "both frozen; the binding one is the more extreme in the hypothesis direction)}, W2: {...}, "
    "L?: {start, end}}; "
    "beta_control: {method: str (one of ic.BETA_CONTROL_METHODS, REQUIRED, non-empty -- DEC-77 "
    "Entscheidung 2, loud fail otherwise), beta_window_weeks: int|None (must match the trailing "
    "window ic.beta_control_trail_weeks(method) implies)}; "
    "data_fingerprints: {union_range_fingerprint: sha256, delisting_dates_sha256: sha256} (DEC-87 V9: "
    "checked against the panel actually loaded; mismatch = KEIN VERDIKT); "
    "rules: {seed: 53, n_reps: >=1000 (factor-null replicates -- must equal the Vorlauf's "
    "n_reps_beta_control_winner that froze the constants; n_reps_bootstrap/n_reps_permutation default "
    "1000), block_len: 4 (FIXED DEC-75 constant, recorded for audit; code hardcodes 4), "
    "level: 0.9936, bh_alpha: 0.10}. "
    "run_full recomputes ceiling and both quantiles per window via nulls.run_configuration_null (registered "
    "beta_control.method, the window's calibration.stress read DIRECTLY -- no re-search --, seed 53, "
    "rules.n_reps reps) and asserts each is within +/-NULL_CALIBRATION_REL_TOL of the FROZEN value, else "
    "loud fail ('Null-Kalibrierung weicht ab', NullCalibrationError, no verdict); the gate itself always "
    "judges against the FROZEN (registered) value, never the recomputed one. The three frozen keys are "
    "OPTIONAL only for hand-built unit-test files (absent -> the recomputed value is used, flagged "
    "`frozen_constants_complete: false` in the report); a registered Drittfassung file carries them all."
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


class RunAbort(RuntimeError):
    """Base of every loud abort that means KEIN VERDIKT (C.14): the run produces no verdict file."""


class NullCalibrationError(RunAbort):
    """DEC-76 Entscheidung 1 (b)/Task A item 3, C.14 loud fail: the run's
    own recomputed null constant (real K series/W_judged, seed 53) drifted
    more than :data:`NULL_CALIBRATION_REL_TOL` from the value frozen in the
    registered YAML -- raised BEFORE any ``gates.evaluate`` call, so no
    hypothesis in the run gets a verdict."""


class DataFingerprintError(RunAbort):
    """DEC-87 (V9): the panel the run loaded does not match ``data_fingerprints`` of the registered
    YAML (union range fingerprint / sha256 of ``delisting_dates.json``) -- or the YAML carries no
    fingerprints at all. Raised before anything is computed."""


class RunArtifactError(RunAbort):
    """DEC-87 (V7)/DEC-53: a mandatory artifact (raw/residualised weekly IC series, bootstrap/permutation
    fingerprints + seed, generator fingerprint) is missing or does not reproduce the gate estimators
    bit for bit -- KEIN VERDIKT."""


class RegisteredSchemaError(ValueError):
    """The registered YAML does not follow the DEC-87 schema (C.14 loud fail, before any panel arithmetic)."""


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
    no-op (an unregistered unit-test file that never carried this key) --
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
    finite series is a legitimate, if under-powered, input).

    DEC-87 (V7)/DEC-53: ``means_sha256`` is the sha256 of the ``n_reps``
    bootstrap means (little-endian float64) -- the content fingerprint of the
    replicates that, with the seed, re-derives them byte for byte."""
    finite = ic_weekly[~np.isnan(ic_weekly)]
    n = finite.size
    if n < 2:
        return {"ci_bound_toward_sign": float("nan"), "n_reps": n_reps, "level": level,
                "direction": direction, "n_weeks_finite": n, "means_sha256": None}
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
            "direction": direction, "n_weeks_finite": n, "block_size": block_size, "seed": seed,
            "means_sha256": hashlib.sha256(np.ascontiguousarray(means, dtype="<f8").tobytes()).hexdigest()}


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
    Label rule (``gates.evaluate``, DEC-87 (I)): ``IC_ohne_D1`` not beyond
    half of that window's ``IC_min`` (for H-29: ``> -0.5*IC_min``) in at least
    one window -> illiquidity-artifact label, verdict unchanged."""
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
    the REAL rev_gap IC (``gates.evaluate``, DEC-87 (I): ``|ic_bounce,W| >=
    |ic_real,W|`` in any window -> no PASS). With the one-week gap formation
    and outcome share no close, so ``ic_bounce`` is ~0 by construction."""
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

def benjamini_hochberg(p_by_variant: dict[str, float], *, alpha: float = 0.10,
                        m_total: int = nulls.REGISTERED_K) -> dict[str, Any]:
    """Standard Benjamini-Hochberg step-up procedure over the K=7
    variants' Max-p p-values (DEC-74 (e)'s unit). REPORT-ONLY (DEC-75
    Entscheidung 1 (6)): the returned ``reject`` booleans are never fed
    into ``gates.evaluate`` as a gate input, only attached as a label.

    **DEC-87 (J): the denominator is FIXED at ``m_total`` (K = 7).** A variant
    that was not computed (locked by GL-012 before the run) or whose p-value is
    NaN enters with p = 1 -- it can never be rejected but it keeps ``m`` at 7
    (``m = max(m_total, len(p_by_variant))``)."""
    items = sorted(((v, p) for v, p in p_by_variant.items() if p is not None and not math.isnan(p)),
                    key=lambda vp: vp[1])
    m = max(int(m_total), len(p_by_variant))
    reject: dict[str, bool] = {v: False for v in p_by_variant}
    if not items:
        return {"alpha": alpha, "m": m, "reject": reject, "largest_rejected_rank": None}
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
# DEC-75 Entscheidung 1 (4) + DEC-87 (G): H-30's vol-weighted, drag-adjusted
# outcome, substituted for the raw next-week return before the SAME (1)/(2)
# machinery every other variant uses.
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


def h30_outcome_for_window(returns: np.ndarray, vol_rv: np.ndarray, day_count: np.ndarray) -> np.ndarray:
    """DEC-75 Entscheidung 1 (4), precised by DEC-87 (G): the ``returns``-shaped
    array H-30's variant is judged against, in place of the raw next-week
    return -- vol-weighted (``target_vol/sigma_w[t]``, PIT) and drag-adjusted
    (``+ sigma_w[t]^2/2`` ADDED to the log outcome, then weighted), with the
    WEEKLY vol ``sigma_w[t] = sqrt(n_t) * vol_rv[t]``: ``vol_rv`` is the SD of
    the week's DAILY log returns and ``day_count`` the ``n_t`` valid daily
    returns of week ``t`` (``characteristics.weekly_valid_day_count``,
    required -- no daily-unit fallback). See
    :func:`prealigned_outcome_to_returns_like` for the shift this needs.
    **Documented composition choice (registered with the Drittfassung):**
    DEC-75 does not spell out how the beta-control PASS component
    (Entscheidung 1 (3)) composes with H-30's vol-weighted outcome;
    :func:`run_full` applies the SAME beta-neutralisation (registered
    ``beta_control.method``) to whichever ``returns``-shaped array a
    hypothesis is judged on -- for H-30 that is THIS function's output."""
    vw = ic.vol_weighted_outcome_with_drag(returns, vol_rv, weight_source="pit", day_count=day_count)
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
    res_quantile_drifting: float | None = None, res_quantile_driftfree: float | None = None,
    gate5_median_spearman: float | None = None,
    beta_control_method: str | None = None, beta_control_pit: np.ndarray | None = None,
) -> dict[str, Any]:
    """Assembles ONE window's numbers for ``gates.evaluate`` -- the real
    IC series, SE (item 1), bootstrap CI bound (item 1), block-permutation
    p-value (item 2, ``nulls.block_permutation_pvalue`` reused unchanged),
    and the beta-control residualised IC (item 3) -- plus the REPORT-ONLY
    task-brief items: the ``"drop"``-convention sensitivity mean IC, the
    ``-1..+2`` lag profile (:func:`lag_profile`), and (when ``beta_8w_pit``
    is given) the PURE beta-characteristic's own calibration IC against the
    SAME outcome. This is the REAL characteristic-vs-REAL-outcome computation
    THE SEAL forbids in ``--prelaunch`` -- run-mode-only, never called from
    ``prelaunch.py``.

    **DEC-77 Entscheidung 2, additive:** ``beta_control_method`` (one of
    :data:`ic.BETA_CONTROL_METHODS`, ``None`` by default) selects HOW
    ``residualized_mean_ic`` is computed, via :func:`ic.apply_beta_control`
    -- the SAME dispatcher the calibration study uses. ``beta_control_pit``
    must be the matching trailing-window PIT beta (unused for ``method in
    (None, "none")``). Leaving it at ``None`` falls back to the EXACT
    pre-DEC-77 behaviour (``ic.residualize_outcome`` with ``beta_8w_pit``).

    **Beta-control quantile (DEC-76 (b), DEC-87 (E)).** ``res_quantile_drifting``
    and ``res_quantile_driftfree`` are the FROZEN registered constants for THIS
    variant/window (the 99.36 % one-sided quantile of the residualised mean IC
    under the stress null with drift 0.002/week resp. 0). This function does NOT
    compute them (:func:`run_full` does, once per window, plus the +-10 %
    assertion) -- it carries them into the payload and adds
    ``res_quantile_binding`` = the one MORE EXTREME in the hypothesis direction
    (``nulls.binding_quantile``), the value ``gates.evaluate`` judges against.
    Both ``None`` = "not supplied" (older callers): the component is trivially
    satisfied.

    ``gate5_median_spearman`` (DEC-87 Gate (5), H-30 only): the window's median
    Spearman(characteristic rank, turnover rank), carried into the payload for
    ``gates.evaluate``.

    DEC-87 (V7): the payload also carries the weekly residualised IC series
    (``ic_residualized_weekly``) and the bootstrap/permutation replicate
    fingerprints (inside ``ci_detail``/``block_permutation_detail``)."""
    res = ic.weekly_ic_series(characteristic, returns, alive, convention=convention)
    ic_weekly = np.array([w["ic"] for w in res["weekly"]], dtype=np.float64)
    se_info = se_of_mean_ic(ic_weekly, floor, w_judged)
    ci_info = moving_block_bootstrap_ci(ic_weekly, direction=direction, block_size=block_size,
                                         n_reps=n_reps_bootstrap, seed=seed, level=ci_level)
    perm = nulls.block_permutation_pvalue(res["mean_ic"], characteristic, returns, alive,
                                           direction=direction, convention=convention,
                                           block_size=block_size, n_reps=n_reps_permutation, seed=seed)

    residualized_mean_ic = None
    ic_residualized_weekly = None
    beta_control_coverage = None
    if beta_control_method is None:
        # Pre-DEC-77 fallback, UNCHANGED: fixed 8-week ic.residualize_outcome.
        if beta_8w_pit is not None and market_symbol in symbols:
            r_btc = returns[:, symbols.index(market_symbol)]
            resid = ic.residualize_outcome(returns, beta_8w_pit, r_btc)
            res_resid = ic.weekly_ic_series(characteristic, resid, alive, convention=convention)
            residualized_mean_ic = res_resid["mean_ic"]
            ic_residualized_weekly = [float(w["ic"]) for w in res_resid["weekly"]]
    elif beta_control_method != "none":
        applied = ic.apply_beta_control(beta_control_method, characteristic, returns, alive,
                                         beta_pit=beta_control_pit, symbols=symbols, market_symbol=market_symbol)
        res_resid = ic.weekly_ic_series(applied["characteristic"], applied["returns"], alive, convention=convention)
        residualized_mean_ic = res_resid["mean_ic"]
        ic_residualized_weekly = [float(w["ic"]) for w in res_resid["weekly"]]
        beta_control_coverage = applied["coverage"]

    mean_ic_drop_convention = None
    if report_drop_convention and convention != "drop":
        mean_ic_drop_convention = ic.weekly_ic_series(characteristic, returns, alive, convention="drop")["mean_ic"]

    lag_profile_result = (lag_profile(characteristic, returns, alive, convention=convention)
                           if report_lag_profile else None)

    beta_calibration_mean_ic = None
    if report_beta_calibration and beta_8w_pit is not None:
        beta_calibration_mean_ic = ic.weekly_ic_series(beta_8w_pit, returns, alive, convention=convention)["mean_ic"]

    res_quantile_binding = nulls.binding_quantile(res_quantile_driftfree, res_quantile_drifting, direction)

    return {
        "mean_ic": res["mean_ic"], "ic_weekly": ic_weekly.tolist(), "se": se_info["se"],
        "se_detail": se_info, "ci_bound_toward_sign": ci_info["ci_bound_toward_sign"], "ci_detail": ci_info,
        "block_permutation_p": perm["p_value"], "block_permutation_detail": perm,
        "ic_min_capped": ic_min_capped, "residualized_mean_ic": residualized_mean_ic,
        "ic_residualized_weekly": ic_residualized_weekly,
        "res_quantile_drifting": res_quantile_drifting,      # DEC-87 (E): frozen, drift 0.002/week
        "res_quantile_driftfree": res_quantile_driftfree,    # DEC-87 (E): frozen, drift 0
        "res_quantile_binding": res_quantile_binding,        # DEC-87 (E): the more extreme -- what the gate judges
        "gate5_median_spearman": gate5_median_spearman,      # DEC-87 Gate (5), H-30 only
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
    liquidity_ic_without_d1: float | dict[str, float] | None = None,
    bounce_ic: float | dict[str, float] | None = None,
    persistence_null_pass: bool | None = None, bh_fdr_pass: bool | None = None,
    convention: ic.Convention = "close_at_last",
    n_reps_bootstrap: int = 1000, n_reps_permutation: int = 1000, seed: int = 53,
    res_quantile_drifting_by_window: dict[str, float] | None = None,
    res_quantile_driftfree_by_window: dict[str, float] | None = None,
    gate5_by_window: dict[str, float] | None = None,
    beta_control_method: str | None = None,
    beta_control_pit_by_window: dict[str, np.ndarray] | None = None,
) -> dict[str, Any]:
    """One hypothesis variant, BOTH judgement windows (C.10 hard) -> the full
    ``gates.evaluate`` payload + verdict. Windows are keyed ``"W1"``/``"W2"``
    throughout. ``res_quantile_drifting_by_window``/
    ``res_quantile_driftfree_by_window`` (DEC-76 (b)/DEC-87 (E), additive,
    ``None`` by default) carry the FROZEN registered per-window beta-control
    quantiles through to each window's payload; ``gate5_by_window`` (DEC-87
    Gate (5)) the H-30 turnover-Spearman medians;
    ``liquidity_ic_without_d1``/``bounce_ic`` are floats (same number in
    every window) or ``{window: float}`` (DEC-87 (I), per window).
    ``beta_control_method``/``beta_control_pit_by_window`` (DEC-77
    Entscheidung 2, additive, ``None`` by default -- exact pre-DEC-77
    fallback via ``beta_8w_pit_by_window``) select the registered
    beta-control method, see :func:`variant_window_payload`'s docstring."""
    windows_payload: dict[str, Any] = {}
    for wname in ("W1", "W2"):
        beta_8w = beta_8w_pit_by_window.get(wname) if beta_8w_pit_by_window else None
        rqd = res_quantile_drifting_by_window.get(wname) if res_quantile_drifting_by_window else None
        rqf = res_quantile_driftfree_by_window.get(wname) if res_quantile_driftfree_by_window else None
        g5 = gate5_by_window.get(wname) if gate5_by_window else None
        beta_control_pit = beta_control_pit_by_window.get(wname) if beta_control_pit_by_window else None
        windows_payload[wname] = variant_window_payload(
            char_by_window[wname], returns_by_window[wname], alive_by_window[wname], symbols,
            variant=variant, direction=direction, ic_min_capped=ic_min_capped_by_window[wname],
            w_judged=w_judged_by_window[wname], floor=floor_by_window[wname],
            selection_ceiling_mean_of_max=selection_ceiling_by_window[wname],
            beta_8w_pit=beta_8w, convention=convention,
            n_reps_bootstrap=n_reps_bootstrap, n_reps_permutation=n_reps_permutation, seed=seed,
            res_quantile_drifting=rqd, res_quantile_driftfree=rqf, gate5_median_spearman=g5,
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
# DEC-87: registered-schema validation, data fingerprints, hypothesis grouping
# ----------------------------------------------------------------------------

def hypothesis_group(entry_id: str, hcfg: dict[str, Any]) -> str:
    """DEC-87 (J): the hypothesis an ENTRY belongs to -- its explicit
    ``hypothesis`` field, else the ``H-nn`` prefix of the entry id
    (``H-28_mom1`` -> ``H-28``), else the id itself (the pre-DEC-87 one-entry-
    per-hypothesis shape ``H-28``)."""
    explicit = hcfg.get("hypothesis")
    if explicit:
        return str(explicit)
    m = re.match(r"^(H-\d+)(?:_.+)?$", str(entry_id))
    return m.group(1) if m else str(entry_id)


def _is_finite_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def validate_registered(registered: dict[str, Any], *, require_frozen_constants: bool = False) -> None:
    """DEC-87 (C.14 loud fail, before any panel arithmetic): the registered YAML
    must follow the Drittfassung schema (:data:`REGISTERED_SCHEMA_HINT`).
    ``require_frozen_constants`` (the CLI's ``--run`` passes ``True``) additionally
    demands the three frozen null constants of EVERY judged window -- finite
    ``ceiling_method_stress`` and finite ``res_quantile_driftfree``/
    ``res_quantile_drifting`` for all seven variants -- so a registered run can never
    silently fall back to its own recomputation (a template emitted without a
    confirmed method carries ``None`` placeholders and is refused here). Hand-built
    unit-test files leave it ``False``.

    Refused with :class:`RegisteredSchemaError`: a top-level ``calibration`` block
    (the old GLOBAL W1-sourced form, DEC-87 (D) -- the calibration is per window);
    a window carrying the pre-DEC-87 ``ceiling_driftfree_res`` key (renamed
    ``ceiling_method_stress``, DEC-87 (A)); a W1/W2 without
    ``calibration.stress.{rho_f, beta_sd_calibrated}``; an entry with an unknown
    variant/direction/status, a locked entry without a ``reason``, an H-30 entry
    without ``outcome: vol_weighted``, or one variant registered twice (K = 7 is
    a family of seven DISTINCT variants)."""
    hyps = registered.get("hypotheses")
    if not isinstance(hyps, dict) or not hyps:
        raise RegisteredSchemaError("registered YAML: 'hypotheses' fehlt oder ist leer")
    if "calibration" in registered:
        raise RegisteredSchemaError(
            "registered YAML traegt einen GLOBALEN 'calibration'-Block (alte W1-Form) -- DEC-87 (D)/DEC-86: die "
            "Kalibrierung gilt JE FENSTER (windows.<W>.calibration.{measured,stress,zero}); kein Lauf, kein Verdikt "
            "(C.14). Mit --emit-registered-template neu erzeugen.")
    seen: dict[str, str] = {}
    for entry_id, hcfg in hyps.items():
        if not isinstance(hcfg, dict):
            raise RegisteredSchemaError(f"hypotheses[{entry_id!r}] ist kein Mapping")
        variant, direction = hcfg.get("variant"), hcfg.get("direction")
        if variant not in characteristics.VARIANT_NAMES:
            raise RegisteredSchemaError(f"hypotheses[{entry_id!r}].variant={variant!r} unbekannt "
                                        f"(erlaubt: {characteristics.VARIANT_NAMES})")
        if direction not in ("positive", "negative"):
            raise RegisteredSchemaError(f"hypotheses[{entry_id!r}].direction={direction!r} (positive|negative)")
        status = hcfg.get("status")
        if status not in (None, "", GL012_PRE_RUN):
            raise RegisteredSchemaError(f"hypotheses[{entry_id!r}].status={status!r} unbekannt "
                                        f"(erlaubt: nicht gesetzt oder {GL012_PRE_RUN!r})")
        if status == GL012_PRE_RUN and not str(hcfg.get("reason") or "").strip():
            raise RegisteredSchemaError(f"hypotheses[{entry_id!r}] ist {GL012_PRE_RUN} ohne 'reason' (Grund Pflicht)")
        if hypothesis_group(entry_id, hcfg) == "H-30" and hcfg.get("outcome") != "vol_weighted":
            raise RegisteredSchemaError(f"hypotheses[{entry_id!r}]: H-30 braucht outcome: vol_weighted (DEC-75 (4))")
        if variant in seen:
            raise RegisteredSchemaError(f"Variante {variant!r} ist doppelt registriert ({seen[variant]!r} und "
                                        f"{entry_id!r}); K = 7 sind sieben verschiedene Varianten")
        seen[variant] = entry_id
    windows = registered.get("windows")
    if not isinstance(windows, dict):
        raise RegisteredSchemaError("registered YAML: 'windows' fehlt")
    for wn in ("W1", "W2"):
        wcfg = windows.get(wn)
        if not isinstance(wcfg, dict):
            raise RegisteredSchemaError(f"windows.{wn} fehlt")
        if "ceiling_driftfree_res" in wcfg:
            raise RegisteredSchemaError(
                f"windows.{wn}.ceiling_driftfree_res ist der VOR-DEC-87-Schluessel der TS-Residualisierungs-Decke "
                "(historisch, nicht bindend) -- bindend ist windows.<W>.ceiling_method_stress (DEC-87 (A)); "
                "kein Lauf (C.14).")
        cal = wcfg.get("calibration")
        stress = cal.get("stress") if isinstance(cal, dict) else None
        if not isinstance(stress, dict) or not _is_finite_number(stress.get("rho_f")) \
                or not _is_finite_number(stress.get("beta_sd_calibrated")):
            raise RegisteredSchemaError(
                f"windows.{wn}.calibration.stress.{{rho_f, beta_sd_calibrated}} fehlt oder ist nicht endlich "
                "(DEC-87 (D): Kalibrierung je Fenster, kein Rueckfall auf rho_f 0,2)")
        for entry_id, hcfg in hyps.items():
            if hcfg.get("status") == GL012_PRE_RUN:
                continue
            ic_min = (wcfg.get("ic_min_capped") or {}).get(hcfg["variant"])
            if not _is_finite_number(ic_min):
                raise RegisteredSchemaError(f"windows.{wn}.ic_min_capped[{hcfg['variant']!r}] fehlt "
                                            f"(Eintrag {entry_id!r})")
        if require_frozen_constants:
            if not _is_finite_number(wcfg.get("ceiling_method_stress")):
                raise RegisteredSchemaError(f"windows.{wn}.ceiling_method_stress fehlt oder ist nicht endlich "
                                            "(eingefrorene Konstante, DEC-87 (A)) -- kein Lauf, kein Verdikt")
            for key in ("res_quantile_driftfree", "res_quantile_drifting"):
                qs = wcfg.get(key)
                missing = [v for v in characteristics.VARIANT_NAMES
                           if not isinstance(qs, dict) or not _is_finite_number(qs.get(v))]
                if missing:
                    raise RegisteredSchemaError(f"windows.{wn}.{key} fehlt oder ist nicht endlich fuer {missing} "
                                                "(eingefrorene Konstante, DEC-87 (E)) -- kein Lauf, kein Verdikt")


def check_data_fingerprints(registered: dict[str, Any], observed: dict[str, Any] | None) -> None:
    """DEC-87 (V9): the panel actually loaded must be the one the Vorlauf froze the constants on.
    ``registered["data_fingerprints"]`` carries ``union_range_fingerprint`` and ``delisting_dates_sha256``;
    ``observed`` is what the CLI measured on the loaded panel. A missing section, a section that cannot
    be checked (``observed`` is ``None``) or any mismatch is a :class:`DataFingerprintError` -- no verdict."""
    reg = registered.get("data_fingerprints")
    if not isinstance(reg, dict):
        raise DataFingerprintError("registered YAML fehlt data_fingerprints (DEC-87 V9: union_range_fingerprint, "
                                   "delisting_dates_sha256) -- kein Lauf, kein Verdikt.")
    if observed is None:
        raise DataFingerprintError("registered YAML traegt data_fingerprints, die Fingerprints des geladenen Panels "
                                   "wurden aber nicht uebergeben -- nicht pruefbar, kein Verdikt.")
    for key in ("union_range_fingerprint", "delisting_dates_sha256"):
        if key not in reg:
            raise DataFingerprintError(f"data_fingerprints.{key} fehlt im registered YAML (DEC-87 V9)")
        if str(observed.get(key)).lower() != str(reg[key]).lower():      # hex digests: case-insensitive
            raise DataFingerprintError(
                f"Daten-Fingerprint {key} weicht ab: Panel {observed.get(key)!r} vs. registriert {reg[key]!r} "
                "-- anderes Panel als im Vorlauf, kein Verdikt (DEC-87 V9).")


def _locked_result(entry_id: str, group: str, variant: str, direction: str, reason: str) -> dict[str, Any]:
    """DEC-87 (J): a locked (``status: gl012_pre_run``) entry is NOT computed: no payload, verdict
    DROP with the GL-012 label and the registered reason, p = 1 in the BH family."""
    verdict = {
        "verdict": "DROP", "hypothesis": group, "variant": variant, "direction": direction,
        "labels": [f"GL-012 vorab (gesperrt, nicht gerechnet, p=1 im BH-Nenner 7): {reason}"],
        "gl012_kill": True, "gl012_pre_run": True, "computed": False, "bounce_kill": False,
        "bounce_windows": [], "liquidity_label": False, "liquidity_windows": [],
        "per_window": {}, "c10_hard": True,
    }
    return {"entry": entry_id, "hypothesis": group, "variant": variant, "payload": None,
            "computed": False, "verdict": verdict}


# ----------------------------------------------------------------------------
# top-level orchestrator
# ----------------------------------------------------------------------------

def run_full(
    panel: dict[str, Any], weekly: dict[str, Any], registered: dict[str, Any], *,
    convention: ic.Convention = "close_at_last",
    observed_fingerprints: dict[str, Any] | None = None, registered_sha256: str | None = None,
) -> dict[str, Any]:
    """Panel + registered YAML -> every entry's verdict (and every hypothesis'
    aggregate). Builds all 7 characteristics ONCE on the full panel (DEC-75
    (8)), slices to W1/W2/L, and per window recomputes the DEC-87 null
    configuration ONCE (shared across all variants:
    :func:`nulls.run_configuration_null` -- the registered
    ``beta_control.method`` under the window's OWN stress calibration
    (``windows.<W>.calibration.stress``, read DIRECTLY, no re-search), seed 53,
    ``rules.n_reps`` replicates, driftfree AND drift 0.002) and asserts the
    ceiling and both quantile sets within +-10 % of the FROZEN registered
    values (:func:`assert_null_calibration`, loud fail ``NullCalibrationError``,
    BEFORE any verdict). The gate itself judges against the FROZEN values. L is
    computed for descriptive/sealed purposes only (never enters a verdict).

    **Order of loud fails (C.14, all before any panel arithmetic):** the
    ``beta_control`` block (DEC-77 Entscheidung 2: missing/empty/unknown method,
    mismatching window), :func:`validate_registered` (DEC-87 schema),
    :func:`check_data_fingerprints` (if ``observed_fingerprints`` is given or the
    YAML carries ``data_fingerprints``), and ``weekly["returns_valid"]`` (DEC-85
    (iii): the real PIT betas and the null's ``sigma_f``/``sigma_e`` come from
    ``returns_est``; IC outcomes and characteristics keep the zero-filled
    ``returns``).

    **Entries (DEC-87 (J)).** ``registered["hypotheses"]`` has one entry per
    variant; ``results[entry_id]`` = ``{"payload", "verdict", ...}`` and
    ``report["hypothesis_verdicts"]`` aggregates by hypothesis (PASS iff at
    least one of its variants is PASS). A ``status: gl012_pre_run`` entry is not
    computed (:func:`_locked_result`). The BH family has the fixed denominator 7.

    **H-30 / Gate (5) / Gate (4).** An H-30 entry is judged against
    :func:`h30_outcome_for_window` and carries the per-window Gate (5) median
    Spearman; an ``rev_gap`` entry gets the bounce fixture and the liquidity
    sensitivity in EACH window."""
    from . import prelaunch  # local import: prelaunch.slice_window, avoids a module cycle at import time

    # DEC-77 Entscheidung 2: the registered beta-control method -- C.14 loud fail, no fallback.
    beta_control_cfg = registered.get("beta_control")
    if not isinstance(beta_control_cfg, dict) or not beta_control_cfg.get("method"):
        raise ValueError(
            "registered YAML fehlt beta_control.method (DEC-77 Entscheidung 2) oder es ist leer -- "
            "kein Lauf ohne vom Orchestrator gewaehlte Beta-Kontroll-Methode (loud fail, kein "
            "Verdikt). --emit-registered-template fuellt method nur aus einer BESTAETIGTEN "
            "Empfehlung (DEC-87); sonst bleibt es leer und die Drittfassung muss es vor der "
            "Registrierung fuellen.")
    beta_control_method = beta_control_cfg["method"]
    beta_control_trail_win = ic.beta_control_trail_weeks(beta_control_method)   # raises on an unknown method
    reg_beta_window = beta_control_cfg.get("beta_window_weeks")
    if beta_control_trail_win is not None and reg_beta_window != beta_control_trail_win:
        raise ValueError(
            f"registered beta_control.beta_window_weeks ({reg_beta_window!r}) passt nicht zum "
            f"von beta_control.method={beta_control_method!r} implizierten Fenster "
            f"({beta_control_trail_win}) -- loud fail, kein Verdikt.")

    validate_registered(registered)
    if observed_fingerprints is not None or "data_fingerprints" in registered:
        check_data_fingerprints(registered, observed_fingerprints)

    rules = registered.get("rules", {})
    seed = int(rules.get("seed", 53))
    n_reps_bootstrap = int(rules.get("n_reps_bootstrap", 1000))
    n_reps_permutation = int(rules.get("n_reps_permutation", 1000))
    # DEC-76 Task A item 4: the canonical rules key is `n_reps` (>= 1000); the legacy
    # `n_reps_factor_null` (DEC-75) is still read as a fallback for a pre-DEC-76 registered file.
    n_reps_factor_null = int(rules.get("n_reps", rules.get("n_reps_factor_null", 1000)))
    null_quantile_level = float(rules.get("level", nulls.SELECTION_CEILING_ONE_SIDED_QUANTILE))
    bh_alpha = float(rules.get("bh_alpha", 0.10))

    weeks = weekly["weeks"]
    symbols = panel["symbols"]
    returns, alive = weekly["returns"], weekly["alive"]
    # DEC-85 (iii): not-trading symbol-weeks are NaN for every beta / vol ESTIMATE (loud
    # ValueError without weekly["returns_valid"]); IC outcomes/characteristics keep `returns`.
    returns_est = nulls.estimation_returns(weekly)
    all_char = build_all_characteristics_full_panel(returns, panel, weeks, symbols)
    turnover_weekly = characteristics.weekly_turnover(panel, weeks)
    turnover_trail = characteristics.trailing_median_turnover(turnover_weekly)
    day_count_full = characteristics.weekly_valid_day_count(panel, weeks)      # DEC-87 (G): n_t
    # DEC-77 Entscheidung 2: the registered method's OWN trailing-window PIT beta, built on the
    # FULL panel first (DEC-75 (8) discipline), sliced per window below -- "none" needs none.
    # DEC-85 (iii): estimated from returns_est -> a symbol needs the method's FULL window of
    # valid returns (the real PIT beta ic.apply_beta_control uses).
    beta_control_pit_full = None
    if beta_control_trail_win is not None:
        beta_control_pit_full = characteristics.beta_characteristic(
            returns_est, symbols, market_symbol="BTCUSDT", trail_win=beta_control_trail_win,
            min_weeks=beta_control_trail_win)

    windows: dict[str, dict[str, Any]] = {}
    for wname in ("W1", "W2", "L"):
        wcfg = registered["windows"].get(wname)
        if wcfg is None:
            continue
        window = prelaunch.slice_window(weeks, wcfg["start"], wcfg["end"], returns, alive)
        lo, hi = window["lo"], window["hi"]
        window["returns_est"] = returns_est[lo:hi]      # DEC-85 (iii)
        window["characteristics"] = {v: arr[lo:hi] for v, arr in all_char.items()}
        window["turnover_trail"] = turnover_trail[lo:hi]
        window["day_count"] = day_count_full[lo:hi]
        window["symbols"] = symbols
        window["beta_control_pit"] = beta_control_pit_full[lo:hi] if beta_control_pit_full is not None else None
        windows[wname] = window

    floor_by_window, wjudged_by_window, ceiling_by_window = {}, {}, {}
    q_driftfree_by_window: dict[str, dict[str, float]] = {}
    q_drifting_by_window: dict[str, dict[str, float]] = {}
    beta_control_pit_by_window: dict[str, np.ndarray | None] = {}
    null_calibration_report: dict[str, Any] = {}
    calibration_used: dict[str, Any] = {}
    frozen_complete = True
    for wname in ("W1", "W2"):
        w = windows[wname]
        f = nulls.analytic_permutation_floor(w["alive"], w["weeks"])
        floor_by_window[wname] = f["e_floor"]
        wjudged_by_window[wname] = f["w_judged"]
        beta_control_pit_by_window[wname] = w["beta_control_pit"]

        reg_window_cfg = registered["windows"][wname]
        stress_block = reg_window_cfg["calibration"]["stress"]       # validated above (DEC-87 (D))
        stress_rho_f = float(stress_block["rho_f"])
        stress_beta_sd = float(stress_block["beta_sd_calibrated"])
        calibration_used[wname] = {
            "rho_f": stress_rho_f, "beta_sd_calibrated": stress_beta_sd,
            "source": f"registered.windows.{wname}.calibration.stress (DEC-87 (D), je Fenster, kein Re-Search)"}

        # DEC-87 (A)/(E): THE null configuration of the Lauf -- registered method, this window's stress
        # calibration, driftfree AND drifting, all variants (K stays 7) -- shared across the entries.
        cfg = nulls.run_configuration_null(
            w["returns_est"], w["alive"], symbols, method=beta_control_method, convention=convention,
            n_reps=n_reps_factor_null, seed=seed, quantile=null_quantile_level,
            rho_f=stress_rho_f, beta_sd=stress_beta_sd)
        recomputed = cfg["constants"]

        reg_ceiling = reg_window_cfg.get("ceiling_method_stress")
        reg_q_free = reg_window_cfg.get("res_quantile_driftfree") or {}
        reg_q_drift = reg_window_cfg.get("res_quantile_drifting") or {}

        # C.14 loud fail: a present-but-drifted registered constant aborts the WHOLE run,
        # before any hypothesis gets a verdict -- see assert_null_calibration's docstring.
        assert_null_calibration(recomputed["ceiling_method_stress"], reg_ceiling,
                                 label=f"ceiling_method_stress[{wname}]")
        ceiling_by_window[wname] = reg_ceiling if reg_ceiling is not None else recomputed["ceiling_method_stress"]
        frozen_complete = frozen_complete and reg_ceiling is not None

        q_driftfree_by_window[wname], q_drifting_by_window[wname] = {}, {}
        for v in characteristics.VARIANT_NAMES:
            rq_free = reg_q_free.get(v) if isinstance(reg_q_free, dict) else None
            rq_drift = reg_q_drift.get(v) if isinstance(reg_q_drift, dict) else None
            assert_null_calibration(recomputed["res_quantile_driftfree"][v], rq_free,
                                     label=f"res_quantile_driftfree[{wname}][{v}]")
            assert_null_calibration(recomputed["res_quantile_drifting"][v], rq_drift,
                                     label=f"res_quantile_drifting[{wname}][{v}]")
            q_driftfree_by_window[wname][v] = rq_free if rq_free is not None else recomputed["res_quantile_driftfree"][v]
            q_drifting_by_window[wname][v] = rq_drift if rq_drift is not None else recomputed["res_quantile_drifting"][v]
            frozen_complete = frozen_complete and rq_free is not None and rq_drift is not None

        null_calibration_report[wname] = {
            "ceiling_method_stress_recomputed": recomputed["ceiling_method_stress"],
            "ceiling_method_stress_registered": reg_ceiling,
            "res_quantile_driftfree_recomputed": recomputed["res_quantile_driftfree"],
            "res_quantile_driftfree_registered": dict(reg_q_free) if isinstance(reg_q_free, dict) else {},
            "res_quantile_drifting_recomputed": recomputed["res_quantile_drifting"],
            "res_quantile_drifting_registered": dict(reg_q_drift) if isinstance(reg_q_drift, dict) else {},
            "res_quantile_binding_recomputed": recomputed["res_quantile_binding"],
            "method": beta_control_method, "n_reps": n_reps_factor_null, "seed": seed,
            "rho_f": stress_rho_f, "beta_sd_calibrated": stress_beta_sd,
        }

    results: dict[str, Any] = {}
    p_by_variant: dict[str, float] = {v: 1.0 for v in characteristics.VARIANT_NAMES}   # DEC-87 (J): fixed 7
    for entry_id, hcfg in registered["hypotheses"].items():
        variant, direction = hcfg["variant"], hcfg["direction"]
        group = hypothesis_group(entry_id, hcfg)
        if hcfg.get("status") == GL012_PRE_RUN:
            results[entry_id] = _locked_result(entry_id, group, variant, direction, str(hcfg["reason"]))
            continue
        is_vol_weighted = hcfg.get("outcome") == "vol_weighted"
        char_by_window = {wn: windows[wn]["characteristics"][variant] for wn in ("W1", "W2")}
        if is_vol_weighted:
            # DEC-75 Entscheidung 1 (4) + DEC-87 (G): H-30 is judged against the vol-weighted,
            # drag-adjusted outcome (weekly sigma_w, +sigma_w^2/2), not the raw next-week return.
            returns_by_window = {
                wn: h30_outcome_for_window(windows[wn]["returns"], windows[wn]["characteristics"]["vol_rv"],
                                            windows[wn]["day_count"])
                for wn in ("W1", "W2")
            }
        else:
            returns_by_window = {wn: windows[wn]["returns"] for wn in ("W1", "W2")}
        alive_by_window = {wn: windows[wn]["alive"] for wn in ("W1", "W2")}
        ic_min_by_window = {wn: registered["windows"][wn]["ic_min_capped"][variant] for wn in ("W1", "W2")}
        # NOTE (registered composition, DEC-87 1.6): the beta-control (DEC-75 (3)) is applied to whichever
        # `returns_by_window` array this entry is judged on -- for H-30 the vol-weighted, drag-adjusted,
        # shifted array, neutralised with the SAME registered method as every other variant.
        beta_by_window = {wn: windows[wn]["characteristics"]["vol_beta"] for wn in ("W1", "W2")}

        # DEC-87 (I): the H-29 sensitivities in EACH window (not W1 only).
        liquidity: dict[str, float] | None = None
        bounce_ic_val: dict[str, float] | None = None
        if variant == "rev_gap":
            liquidity = {}
            for wn in ("W1", "W2"):
                liq = liquidity_decile_sensitivity(char_by_window[wn], returns_by_window[wn],
                                                    alive_by_window[wn], windows[wn]["turnover_trail"],
                                                    convention=convention)
                liquidity[wn] = liq["mean_ic_without_d1"]
        if group == "H-29" or variant == "rev_gap":
            bounce_ic_val = {}
            for wn in ("W1", "W2"):
                k_median = int(np.median(alive_by_window[wn].sum(axis=1)))
                bf = bounce_fixture_ic(alive_by_window[wn].shape[0], max(k_median, 10), seed=seed,
                                        convention=convention)
                bounce_ic_val[wn] = bf["ic_bounce"]

        # DEC-87 Gate (5), H-30 only: median Spearman(characteristic rank, turnover rank) per window.
        gate5_by_window: dict[str, float] | None = None
        if is_vol_weighted or group == "H-30":
            gate5_by_window = {}
            for wn in ("W1", "W2"):
                g5 = characteristics.characteristic_turnover_spearman(
                    char_by_window[wn], windows[wn]["turnover_trail"], alive_by_window[wn], windows[wn]["weeks"])
                gate5_by_window[wn] = float("nan") if g5["median"] is None else g5["median"]

        # DEC-87 (item 10): the AR(1) persistence fits are ESTIMATES -> returns_est.
        pnull = nulls.persistence_null(windows["W1"]["returns_est"], windows["W1"]["alive"], windows["W1"]["weeks"],
                                        variants=(variant,), convention=convention, n_sims=200, seed=seed)
        real_mean_ic_w1 = ic.weekly_ic_series(char_by_window["W1"], returns_by_window["W1"],
                                               alive_by_window["W1"], convention=convention)["mean_ic"]
        q = pnull["variants"][variant]["quantile95_registered_direction"]
        persistence_pass = (real_mean_ic_w1 > q) if direction == "positive" else (real_mean_ic_w1 < q)

        run_res = run_hypothesis(
            group, variant, direction, char_by_window, returns_by_window, alive_by_window, symbols,
            ic_min_by_window, wjudged_by_window, floor_by_window, ceiling_by_window,
            beta_8w_pit_by_window=beta_by_window, liquidity_ic_without_d1=liquidity, bounce_ic=bounce_ic_val,
            persistence_null_pass=bool(persistence_pass), bh_fdr_pass=None,
            convention=convention, n_reps_bootstrap=n_reps_bootstrap, n_reps_permutation=n_reps_permutation,
            seed=seed,
            res_quantile_drifting_by_window={wn: q_drifting_by_window[wn][variant] for wn in ("W1", "W2")},
            res_quantile_driftfree_by_window={wn: q_driftfree_by_window[wn][variant] for wn in ("W1", "W2")},
            gate5_by_window=gate5_by_window,
            beta_control_method=beta_control_method, beta_control_pit_by_window=beta_control_pit_by_window)
        run_res.update({"entry": entry_id, "hypothesis": group, "variant": variant, "computed": True})
        results[entry_id] = run_res
        p_max = max_p_over_windows({
            wn: run_res["payload"]["windows"][wn]["block_permutation_p"] for wn in ("W1", "W2")})
        p_by_variant[variant] = 1.0 if math.isnan(p_max) else p_max

    bh = benjamini_hochberg(p_by_variant, alpha=bh_alpha, m_total=len(characteristics.VARIANT_NAMES))
    for entry_id, hcfg in registered["hypotheses"].items():
        res = results[entry_id]
        if not res["computed"]:
            continue
        res["payload"]["bh_fdr_pass"] = bh["reject"].get(hcfg["variant"])
        res["verdict"] = gates.evaluate(res["payload"])

    hypothesis_verdicts = aggregate_hypotheses(results)

    windows_meta = {wn: {"weeks": windows[wn]["weeks"], "n_weeks": len(windows[wn]["weeks"])}
                     for wn in windows}
    l_window_sealed = windows_meta.pop("L", None)     # DEC-74 (k)/DEC-75 (8): L stays sealed, never in the open report
    if l_window_sealed is not None:
        windows_meta["L"] = {"available": True, "note": "siehe l_window_sealed_json (DEC-74 (k))"}

    return {
        "wp": "WP-13", "mode": "run", "results": results, "hypothesis_verdicts": hypothesis_verdicts, "bh": bh,
        "windows_meta": windows_meta, "_l_window_sealed": l_window_sealed,
        "seed": seed, "convention": convention,
        "n_reps_bootstrap": n_reps_bootstrap, "n_reps_permutation": n_reps_permutation,
        "n_reps_factor_null": n_reps_factor_null,
        "null_calibration": null_calibration_report,   # DEC-87 (A)/(E): recomputed vs. registered, per window
        "frozen_constants_complete": frozen_complete,
        "beta_control": {"method": beta_control_method, "beta_window_weeks": beta_control_trail_win},
        "calibration_used_for_stress_null": calibration_used,   # DEC-87 (D): per window, audit trail
        "observed_fingerprints": observed_fingerprints, "registered_sha256": registered_sha256,
        "parameters": {"rules": dict(rules), "bh_alpha": bh_alpha, "null_quantile_level": null_quantile_level,
                        "convention": convention, "block_size": 4,
                        "variants": list(characteristics.VARIANT_NAMES)},
    }


def aggregate_hypotheses(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """DEC-87 (J): a hypothesis is PASS iff AT LEAST ONE of its variants (entries) is PASS; every variant stays
    individually reported (``entries``, ``variants_pass``) and a locked (not computed) variant is listed in
    ``variants_locked``. ``results[entry_id]`` needs ``hypothesis``, ``variant``, ``computed`` and
    ``verdict["verdict"]``. A PASS carries the label "vorlaeufig bis F-WEEK geschlossen" (DEC-74 (e))."""
    out: dict[str, Any] = {}
    for entry_id, res in results.items():
        g = out.setdefault(res["hypothesis"], {"entries": [], "variants_pass": [], "variants_locked": []})
        g["entries"].append(entry_id)
        if res["verdict"]["verdict"] == "PASS":
            g["variants_pass"].append(res["variant"])
        if not res["computed"]:
            g["variants_locked"].append(res["variant"])
    for g in out.values():
        g["verdict"] = "PASS" if g["variants_pass"] else "DROP"
        g["label"] = "vorlaeufig bis F-WEEK geschlossen (DEC-74 (e))" if g["variants_pass"] else None
    return out


def registered_constants_pin(registered: dict[str, Any]) -> dict[str, Any]:
    """DEC-87 T5 (constants pin): the flat set of numbers the Drittfassung FREEZES, read from the
    registered YAML -- ``ic_min_capped``, ``ceiling_method_stress``, both frozen quantile sets and the
    stress calibration pair, per window. A test (or the Orchestrator's sha256 pin) compares this with
    what actually flowed into every payload."""
    out: dict[str, Any] = {}
    for wn in ("W1", "W2"):
        wcfg = registered["windows"][wn]
        out[wn] = {
            "ic_min_capped": dict(wcfg.get("ic_min_capped") or {}),
            "w_judged": wcfg.get("w_judged"),
            "ceiling_method_stress": wcfg.get("ceiling_method_stress"),
            "res_quantile_driftfree": dict(wcfg.get("res_quantile_driftfree") or {}),
            "res_quantile_drifting": dict(wcfg.get("res_quantile_drifting") or {}),
            "calibration_stress": dict(((wcfg.get("calibration") or {}).get("stress")) or {}),
        }
    return out


# ----------------------------------------------------------------------------
# DEC-53 / DEC-87 (V7): artifacts, generator fingerprint, round trip
# ----------------------------------------------------------------------------

def code_fingerprint() -> dict[str, Any]:
    """DEC-87 (V7) generator fingerprint, code part: sha256 of every ``*.py`` of the ``wp13_xsec`` and
    ``wp7_universe`` packages (+ ``scripts/wp13_xsec.py`` if present), per file and aggregated, the
    python/numpy versions, the bit generator, and -- best effort -- the repository commit
    (``null`` if git is unavailable). Deterministic for one checkout."""
    pkg = Path(__file__).resolve().parent
    research = pkg.parent
    repo = research.parents[2]
    files: dict[str, str] = {}
    for base, label in ((pkg, "wp13_xsec"), (research / "wp7_universe", "wp7_universe")):
        for f in sorted(base.glob("*.py")):
            files[f"{label}/{f.name}"] = hashlib.sha256(f.read_bytes()).hexdigest()
    script = repo / "scripts" / "wp13_xsec.py"
    if script.is_file():
        files["scripts/wp13_xsec.py"] = hashlib.sha256(script.read_bytes()).hexdigest()
    h = hashlib.sha256()
    for name in sorted(files):
        h.update(name.encode("utf-8"))
        h.update(files[name].encode("ascii"))
    commit: str | None = None
    try:
        out = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                              timeout=10, check=False)
        if out.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", out.stdout.strip() or ""):
            commit = out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        commit = None
    return {"code_sha256": h.hexdigest(), "files": files, "git_commit": commit,
            "python": sys.version.split()[0], "numpy": np.__version__,
            "bit_generator": type(np.random.default_rng(0).bit_generator).__name__}


def result_fingerprint(report: dict[str, Any]) -> str:
    """sha256 of the canonical JSON of everything a verdict rests on (every computed entry's payload
    and verdict, the hypothesis aggregation, the null re-computation) -- T2: N identical runs give N
    identical fingerprints. The sealed L window is not part of it."""
    core = {
        "results": {eid: {"payload": r.get("payload"), "verdict": r["verdict"]} for eid, r in report["results"].items()},
        "hypothesis_verdicts": report["hypothesis_verdicts"], "bh": report["bh"],
        "null_calibration": report["null_calibration"], "beta_control": report["beta_control"],
    }
    blob = json.dumps(core, sort_keys=True, default=str, allow_nan=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _series_sha256(series: list[float]) -> str:
    return hashlib.sha256(np.ascontiguousarray(np.array(series, dtype=np.float64), dtype="<f8").tobytes()).hexdigest()


def _write_series_csv(path: Path, series: list[float]) -> dict[str, str]:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["t", "ic"])
        for t, val in enumerate(series):
            writer.writerow([t, repr(float(val))])      # repr round-trips a float exactly (NaN -> 'nan')
    return {"path": str(path), "sha256": panel_load.sha256_file(path)}


def _read_series_csv(path: Path) -> list[float]:
    with path.open("r", newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    if not rows or rows[0] != ["t", "ic"]:
        raise RunArtifactError(f"KEIN VERDIKT: {path.name} hat keinen gueltigen Kopf ['t', 'ic']")
    return [float(r[1]) for r in rows[1:]]


def _build_fingerprint(report: dict[str, Any]) -> dict[str, Any]:
    draws: dict[str, Any] = {}
    series: dict[str, Any] = {}
    for eid, res in report["results"].items():
        if res.get("payload") is None:
            continue
        for wn, w in res["payload"]["windows"].items():
            key = f"{eid}/{wn}"
            draws[key] = {
                "bootstrap_n_reps": w["ci_detail"].get("n_reps"), "bootstrap_seed": w["ci_detail"].get("seed"),
                "bootstrap_means_sha256": w["ci_detail"].get("means_sha256"),
                "permutation_n_reps": w["block_permutation_detail"].get("n_reps"),
                "permutation_seed": w["block_permutation_detail"].get("seed"),
                "permutation_draws_sha256": w["block_permutation_detail"].get("draws_sha256"),
            }
            series[key] = {
                "ic_weekly_sha256": _series_sha256(w["ic_weekly"]),
                "ic_residualized_weekly_sha256": (None if w.get("ic_residualized_weekly") is None
                                                  else _series_sha256(w["ic_residualized_weekly"])),
            }
    return {
        "schema": "DEC-87 V7 / DEC-53 generator fingerprint",
        "seed": report["seed"], "convention": report["convention"],
        "code": code_fingerprint(),
        "data_fingerprints": report.get("observed_fingerprints"),
        "registered_sha256": report.get("registered_sha256"),
        "parameters": report["parameters"],
        "beta_control": report["beta_control"],
        "draws": draws, "series": series,
        "result_sha256": result_fingerprint(report),
    }


def verify_run_artifacts(out_dir: Path | str, report: dict[str, Any], *,
                          require_data_fingerprints: bool = False) -> dict[str, Any]:
    """DEC-87 (V7) / T7 artifact round trip -- the KEIN-VERDIKT guard. Re-reads what
    :func:`write_run_artifacts` wrote and checks, for EVERY computed entry and judged window:
    the raw and (if a beta-control method is registered) the residualised weekly IC series exist and
    equal the payload bit for bit; the gate estimators recomputed FROM THE FILES (mean IC, SE, moving-block
    bootstrap bound + replicate fingerprint, residualised mean IC) equal the payload bit for bit; the
    generator fingerprint file exists with seed, code hash, parameters, the bootstrap/permutation
    fingerprints and a ``result_sha256`` equal to the report's. Anything missing or different raises
    :class:`RunArtifactError` ("KEIN VERDIKT: ...")."""
    out_dir = Path(out_dir)
    fp_path = out_dir / "wp13_run_fingerprint.json"
    if not fp_path.is_file():
        raise RunArtifactError("KEIN VERDIKT: Pflicht-Artefakt wp13_run_fingerprint.json fehlt (Generator-Fingerprint)")
    fp = json.loads(fp_path.read_text(encoding="utf-8"))
    for key in ("seed", "code", "parameters", "draws", "series", "result_sha256", "data_fingerprints"):
        if key not in fp:
            raise RunArtifactError(f"KEIN VERDIKT: Generator-Fingerprint ohne Feld {key!r}")
    if not fp["code"].get("code_sha256"):
        raise RunArtifactError("KEIN VERDIKT: Generator-Fingerprint ohne Code-Hash")
    if require_data_fingerprints and not fp["data_fingerprints"]:
        raise RunArtifactError("KEIN VERDIKT: Generator-Fingerprint ohne Daten-Fingerprints")
    if fp["result_sha256"] != result_fingerprint(report):
        raise RunArtifactError("KEIN VERDIKT: result_sha256 des Fingerprints weicht vom Bericht ab")

    n_checked = 0
    for eid, res in report["results"].items():
        if res.get("payload") is None:
            continue
        for wn, w in res["payload"]["windows"].items():
            key = f"{eid}/{wn}"
            raw_path = out_dir / f"wp13_run_{eid}_{wn}_ic_weekly.csv"
            if not raw_path.is_file():
                raise RunArtifactError(f"KEIN VERDIKT: Pflicht-Artefakt {raw_path.name} (rohe Wochen-IC-Serie) fehlt")
            raw = _read_series_csv(raw_path)
            if raw != w["ic_weekly"] and not np.array_equal(np.array(raw), np.array(w["ic_weekly"]), equal_nan=True):
                raise RunArtifactError(f"KEIN VERDIKT: {raw_path.name} weicht von der Payload-Serie ab")
            arr = np.array(raw, dtype=np.float64)
            finite = arr[~np.isnan(arr)]
            mean = float(finite.mean()) if finite.size else float("nan")
            if not (mean == w["mean_ic"] or (math.isnan(mean) and math.isnan(w["mean_ic"]))):
                raise RunArtifactError(f"KEIN VERDIKT: Mittel-IC aus {raw_path.name} ({mean!r}) != Payload ({w['mean_ic']!r})")
            sd = w["se_detail"]
            se = se_of_mean_ic(arr, sd["floor"], sd["w_judged"])["se"]
            if not (se == w["se"] or (math.isnan(se) and math.isnan(w["se"]))):
                raise RunArtifactError(f"KEIN VERDIKT: SE aus {raw_path.name} ({se!r}) != Payload ({w['se']!r})")
            cd = w["ci_detail"]
            ci = moving_block_bootstrap_ci(arr, direction=cd["direction"], block_size=cd.get("block_size", 4),
                                            n_reps=cd["n_reps"], seed=cd.get("seed", report["seed"]), level=cd["level"])
            same_bound = (ci["ci_bound_toward_sign"] == w["ci_bound_toward_sign"]
                          or (math.isnan(ci["ci_bound_toward_sign"]) and math.isnan(w["ci_bound_toward_sign"])))
            if not same_bound or ci.get("means_sha256") != cd.get("means_sha256"):
                raise RunArtifactError(f"KEIN VERDIKT: Bootstrap-Grenze/-Replikate aus {raw_path.name} reproduzieren die Payload nicht")
            if fp["draws"].get(key, {}).get("bootstrap_means_sha256") != cd.get("means_sha256") \
                    or fp["draws"].get(key, {}).get("permutation_draws_sha256") != w["block_permutation_detail"].get("draws_sha256"):
                raise RunArtifactError(f"KEIN VERDIKT: Replikat-Fingerprint {key} fehlt/weicht ab")
            if fp["series"].get(key, {}).get("ic_weekly_sha256") != _series_sha256(raw):
                raise RunArtifactError(f"KEIN VERDIKT: Serien-Fingerprint {key} weicht ab")
            if w.get("residualized_mean_ic") is not None or w.get("ic_residualized_weekly") is not None:
                res_path = out_dir / f"wp13_run_{eid}_{wn}_ic_weekly_residualized.csv"
                if not res_path.is_file():
                    raise RunArtifactError(f"KEIN VERDIKT: Pflicht-Artefakt {res_path.name} (residualisierte Wochenserie) fehlt")
                rs = _read_series_csv(res_path)
                if not np.array_equal(np.array(rs), np.array(w["ic_residualized_weekly"]), equal_nan=True):
                    raise RunArtifactError(f"KEIN VERDIKT: {res_path.name} weicht von der Payload-Serie ab")
                rarr = np.array(rs, dtype=np.float64)
                rfin = rarr[~np.isnan(rarr)]
                rmean = float(rfin.mean()) if rfin.size else float("nan")
                if not (rmean == w["residualized_mean_ic"]
                        or (math.isnan(rmean) and math.isnan(w["residualized_mean_ic"]))):
                    raise RunArtifactError(f"KEIN VERDIKT: IC_res aus {res_path.name} ({rmean!r}) != Payload "
                                           f"({w['residualized_mean_ic']!r})")
            n_checked += 1
    return {"n_entry_windows_checked": n_checked, "result_sha256": fp["result_sha256"]}


def write_run_artifacts(out_dir: Path | str, report: dict[str, Any], *,
                         require_data_fingerprints: bool = False) -> dict[str, Any]:
    """DEC-53 / DEC-87 (V7) artifacts for the run report, in this order:

      1. per computed entry and judged window the RAW weekly IC series
         (``wp13_run_<entry>_<W>_ic_weekly.csv``) and, when a beta-control method is
         registered, the RESIDUALISED weekly IC series
         (``..._ic_weekly_residualized.csv``, the (3b) series), each sha256'd;
      2. ``wp13_run_fingerprint.json`` -- seed, bit generator, code hash + commit,
         data fingerprints, parameters, bootstrap/permutation replicate fingerprints
         (seed + sha256 of the draws: with the determinism of the generators a
         byte-exact re-derivation), series fingerprints, ``result_sha256``;
      3. :func:`verify_run_artifacts` -- if anything mandatory is missing or does not
         reproduce the gate estimators, :class:`RunArtifactError` is raised and NO
         verdict file is written (KEIN VERDIKT);
      4. only then the main JSON (the verdicts) and the L window in its own sealed
         file (DEC-74 (k)).

    Locked (``gl012_pre_run``) entries have no series (not computed) and are
    exempt. Never writes under ``data/harvest``."""
    out_dir = Path(out_dir)
    if "data/harvest" in out_dir.as_posix():
        raise ValueError(f"refusing to write under data/harvest: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, Any] = {}

    for eid, res in report["results"].items():
        if res.get("payload") is None:
            continue
        for wname, w in res["payload"]["windows"].items():
            art = _write_series_csv(out_dir / f"wp13_run_{eid}_{wname}_ic_weekly.csv", w["ic_weekly"])
            artifacts[Path(art["path"]).name] = art
            if w.get("ic_residualized_weekly") is not None:
                art = _write_series_csv(out_dir / f"wp13_run_{eid}_{wname}_ic_weekly_residualized.csv",
                                         w["ic_residualized_weekly"])
                artifacts[Path(art["path"]).name] = art

    fp_path = out_dir / "wp13_run_fingerprint.json"
    fp_path.write_text(json.dumps(_build_fingerprint(report), indent=1, sort_keys=True, default=str), encoding="utf-8")
    artifacts["wp13_run_fingerprint_json"] = {"path": str(fp_path), "sha256": panel_load.sha256_file(fp_path)}

    verify_run_artifacts(out_dir, report, require_data_fingerprints=require_data_fingerprints)   # may raise: KEIN VERDIKT

    main_report = dict(report)
    l_window_sealed = main_report.pop("_l_window_sealed", None)   # never goes into the open JSON
    main_json = out_dir / "wp13_run.json"
    main_json.write_text(json.dumps(main_report, indent=1, default=str), encoding="utf-8")
    artifacts["wp13_run_json"] = {"path": str(main_json), "sha256": panel_load.sha256_file(main_json)}

    if l_window_sealed is not None:
        l_path = out_dir / "wp13_run_L_window_sealed.json"
        l_path.write_text(json.dumps(l_window_sealed, indent=1, default=str), encoding="utf-8")
        artifacts["l_window_sealed_json"] = {"path": str(l_path), "sha256": panel_load.sha256_file(l_path)}

    return {"out_dir": str(out_dir), "artifacts": artifacts}
