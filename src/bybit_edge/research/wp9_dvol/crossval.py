"""WP-9 -- REST vs. harvest DVOL cross-validation (KAPITALFREI).

Answers F2 (``WP9_SPEZIFIKATION.md`` sections 1 and 2): is the public
Deribit REST daily close the SAME quantity as the harvested
``deribit/dvol`` stream's daily close, within the H-26 materiality band
derived there (0.3 vol points on the 90-day premium mean)?

Criterion (verbatim, spec section 2): ``|mean(REST - Harvest)|`` over the
overlap <= 0.3 vol points AND the 95% bootstrap CI of that mean lies
inside ``[-0.3, +0.3]``.

Reachability FIRST (spec section 2, non-negotiable ordering): the daily-
difference distribution (p5/p50/p95, lag-1 autocorrelation) is ALWAYS
computed and reported before the criterion is applied. When the daily
differences are so dispersed that no CI achievable at ``n`` overlap days
could EVER fit inside the +-0.3 band -- regardless of where the true mean
sits -- the verdict is "nicht entscheidbar bei n", never verdict (b). This
is checked by bootstrapping the CENTRED series (H0: mean=0 imposed) and
comparing ITS 95% half-width against the band: that half-width is a
location-invariant floor on how tight any CI from this sample can be.

Bootstrap: stationary (fixed-length, circular) block bootstrap, block
length 5 calendar days, 1000 replicates, RNG seeded and the seed always
stored in the output (DEC-53) -- the same block-resampling family as
``c11_anen.stats.block_bootstrap_p``, generalised here from a one-sided
DM-style p-value to a two-sided percentile CI of the mean.
"""
from __future__ import annotations

from typing import Any

import numpy as np

__all__ = [
    "MATERIALITY_BAND_VOLPTS", "BLOCK_LEN_DAYS", "N_BOOTSTRAP", "DEFAULT_SEED",
    "CrossvalError", "daily_differences", "autocorr_lag1",
    "distribution_report", "stationary_block_bootstrap_mean_ci", "evaluate",
]

#: H-26-derived band (spec section 2): "MATERIAL, wenn ... um >= 10% der
#: Schwelle (0.3 Vol-Punkte) verschieben kann" -- the criterion band itself.
MATERIALITY_BAND_VOLPTS = 0.3

#: Repo block-bootstrap convention (c11_anen.stats / c22_l2tilt): 5-day
#: blocks, 1000 replicates. Spec section 4 pins the same numbers for WP-9.
BLOCK_LEN_DAYS = 5
N_BOOTSTRAP = 1000

#: Arbitrary but fixed default; DEC-53 requires the ACTUAL seed used be
#: stored in the output, not that it equal this particular value.
DEFAULT_SEED = 53

_ALPHA = 0.05  # 95% CI


class CrossvalError(RuntimeError):
    """Loud failure: crossval cannot support a bootstrap CI on this input."""


def daily_differences(rest_rows: list[dict[str, Any]],
                       harvest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Per-day (REST - Harvest) close difference over the date overlap.

    Both inputs are ``{"date": iso, "close": float, ...}`` rows (REST:
    ``rest_client.rows_to_daily``; harvest: ``harvest_close.daily_close``,
    pre-filtered by the caller to rows that actually carry ``close``).
    Deterministic: sorted by date, exactly one row per date present in
    BOTH inputs (no partial-day guessing).
    """
    rest_by_date = {r["date"]: r["close"] for r in rest_rows}
    harv_by_date = {r["date"]: r["close"] for r in harvest_rows if "close" in r}
    dates = sorted(set(rest_by_date) & set(harv_by_date))
    return [{"date": d, "rest_close": rest_by_date[d],
             "harvest_close": harv_by_date[d],
             "diff": rest_by_date[d] - harv_by_date[d]} for d in dates]


def autocorr_lag1(x: np.ndarray) -> float | None:
    """Pearson lag-1 autocorrelation; None when undefined (n<3 or zero var)."""
    x = np.asarray(x, dtype=np.float64)
    x = x[np.isfinite(x)]
    if x.size < 3:
        return None
    a, b = x[:-1] - x[:-1].mean(), x[1:] - x[1:].mean()
    denom = np.sqrt(np.sum(a * a) * np.sum(b * b))
    if denom == 0:
        return None
    return float(np.sum(a * b) / denom)


def distribution_report(d: np.ndarray) -> dict[str, Any]:
    """p5/p50/p95, sample SD, lag-1 autocorrelation -- reported BEFORE any
    verdict is drawn (spec section 2, "Erreichbarkeitspruefung ZUERST")."""
    x = np.asarray(d, dtype=np.float64)
    x = x[np.isfinite(x)]
    n = int(x.size)
    if n == 0:
        return {"n": 0, "p5": None, "p50": None, "p95": None, "sd": None,
                "autocorr_lag1": None}
    return {
        "n": n,
        "p5": float(np.quantile(x, 0.05)), "p50": float(np.quantile(x, 0.50)),
        "p95": float(np.quantile(x, 0.95)),
        "sd": float(np.std(x, ddof=1)) if n > 1 else 0.0,
        "autocorr_lag1": autocorr_lag1(x),
    }


def stationary_block_bootstrap_mean_ci(
    d: np.ndarray, *, block_len: int = BLOCK_LEN_DAYS,
    n_bootstrap: int = N_BOOTSTRAP, seed: int = DEFAULT_SEED, alpha: float = _ALPHA,
) -> dict[str, Any]:
    """Circular fixed-block bootstrap CI of ``mean(d)``.

    Repo block-bootstrap convention (``c11_anen.stats.block_bootstrap_p``):
    contiguous ``block_len``-day blocks drawn with circular wraparound,
    concatenated and truncated back to length ``n`` per replicate --
    preserves short-range autocorrelation instead of an i.i.d. resample.
    Percentile CI of the (uncentred) bootstrap mean distribution. Loud-fail
    on degenerate input (fewer than 2 finite differences) rather than a
    fabricated CI.
    """
    x = np.asarray(d, dtype=np.float64)
    x = x[np.isfinite(x)]
    n = x.size
    if n < 2 or n_bootstrap < 1:
        raise CrossvalError(
            f"cannot bootstrap a CI from {n} finite difference(s) "
            f"(need >= 2) or n_bootstrap={n_bootstrap} (need >= 1)")
    observed = float(np.mean(x))
    bs = max(1, min(int(block_len), n))
    n_blocks = int(np.ceil(n / bs))
    rng = np.random.default_rng(seed)
    offsets = np.arange(bs)
    means = np.empty(n_bootstrap, dtype=np.float64)
    for i in range(n_bootstrap):
        starts = rng.integers(0, n, size=n_blocks)
        idx = (starts[:, None] + offsets[None, :]) % n
        means[i] = float(np.mean(x[idx.reshape(-1)][:n]))
    lo = float(np.quantile(means, alpha / 2))
    hi = float(np.quantile(means, 1 - alpha / 2))
    return {"mean": observed, "ci_lo": lo, "ci_hi": hi, "alpha": alpha,
            "block_len": int(bs), "n_bootstrap": int(n_bootstrap),
            "seed": int(seed), "n": int(n)}


def _achievable_half_width(
    d: np.ndarray, *, block_len: int, n_bootstrap: int, seed: int, alpha: float,
) -> float:
    """95% half-width of the CENTRED (H0: mean=0) bootstrap distribution.

    Location-invariant: bootstrapping the demeaned series answers "how
    wide would ANY CI from this n and this dispersion be", independent of
    where the observed mean actually sits. That is exactly the
    reachability question (spec section 2): if this floor already exceeds
    the band, no true mean could ever produce a CI that fits inside it.
    """
    x = np.asarray(d, dtype=np.float64)
    x = x[np.isfinite(x)]
    centered = x - float(np.mean(x))
    boot = stationary_block_bootstrap_mean_ci(
        centered, block_len=block_len, n_bootstrap=n_bootstrap, seed=seed, alpha=alpha)
    return 0.5 * (boot["ci_hi"] - boot["ci_lo"])


def evaluate(
    rest_rows: list[dict[str, Any]], harvest_rows: list[dict[str, Any]], *,
    band: float = MATERIALITY_BAND_VOLPTS, block_len: int = BLOCK_LEN_DAYS,
    n_bootstrap: int = N_BOOTSTRAP, seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """Full F2 verdict pipeline: differences -> distribution -> reachability
    -> bootstrap CI -> verdict ``"a"`` / ``"b"`` / ``"nicht entscheidbar bei n"``.

    DEC-53 artefact requirement satisfied here: the returned dict always
    carries ``daily_differences`` (the judgment-bearing per-day series) and
    ``bootstrap["seed"]`` (+ block_len/n_bootstrap -- the generator
    fingerprint a caller needs to reproduce the replicates bit-identically
    via ``numpy.random.default_rng(seed)``).
    """
    diffs = daily_differences(rest_rows, harvest_rows)
    d = np.array([r["diff"] for r in diffs], dtype=np.float64)
    dist = distribution_report(d)

    base = {
        "n_overlap_days": dist["n"], "distribution": dist,
        "materiality_band_volpts": band, "daily_differences": diffs,
    }
    if dist["n"] < 2:
        return {**base, "bootstrap": None, "half_width": None,
                "reachable": False, "verdict": "nicht entscheidbar bei n",
                "reason": f"n={dist['n']} < 2 -- kein Bootstrap moeglich"}
    if dist["n"] <= block_len:
        # n <= block_len means every circular block bootstrap replicate is
        # ONE full-length block: a cyclic shift of the whole series, whose
        # mean is invariant to the shift -- the bootstrap distribution
        # degenerates to a point regardless of the data's actual dispersion
        # (it would silently report a zero-width CI that is not real). At
        # n this small the pre-registered 5-day block bootstrap cannot say
        # anything meaningful, so this IS the "nicht entscheidbar bei n"
        # case, decided WITHOUT running a bootstrap that would lie.
        return {**base, "bootstrap": None, "half_width": None,
                "reachable": False, "verdict": "nicht entscheidbar bei n",
                "reason": (f"n={dist['n']} <= block_len={block_len} -- der "
                          "5-Tage-Block-Bootstrap braucht mehr als einen "
                          "vollen Block, um Streuung ueberhaupt abzubilden "
                          "(sonst waere jede Ziehung ein blosser Ring-Shift "
                          "mit invariantem Mittel, ein Scheinergebnis).")}

    half_width = _achievable_half_width(
        d, block_len=block_len, n_bootstrap=n_bootstrap, seed=seed, alpha=_ALPHA)
    reachable = half_width <= band
    boot = stationary_block_bootstrap_mean_ci(
        d, block_len=block_len, n_bootstrap=n_bootstrap, seed=seed, alpha=_ALPHA)

    if not reachable:
        verdict = "nicht entscheidbar bei n"
        reason = (f"Erreichbarkeits-Check zuerst: 95%-CI-Halbbreite bei n="
                  f"{dist['n']} ({half_width:.4f}) > Band ({band}) -- kein CI "
                  f"koennte hier je ins Band passen, unabhaengig vom Mittel.")
    else:
        mean_ok = abs(boot["mean"]) <= band
        ci_ok = boot["ci_lo"] >= -band and boot["ci_hi"] <= band
        if mean_ok and ci_ok:
            verdict, reason = "a", "austauschbar: |Mittel| und 95%-CI innerhalb des Bands."
        else:
            verdict, reason = "b", "nicht austauschbar: |Mittel| oder 95%-CI ausserhalb des Bands."

    return {**base, "bootstrap": boot, "half_width": half_width,
            "reachable": reachable, "verdict": verdict, "reason": reason}
