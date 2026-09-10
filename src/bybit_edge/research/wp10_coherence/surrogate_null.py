"""WP-10(A) -- structural null effect of the STRESS_ABS coherence cell
(PRD 4.3 Teil A "Struktureller Nulleffekt (C.4)", DEC-62).

**Why this module exists.** Correlations rise MECHANICALLY in extreme
sub-samples (selection on common magnitude) -- a stress-cell rho next to
a quiet-cell rho is not by itself evidence of a genuine regime-dependent
co-movement; some of the "lift" is baked in by the selection alone. The
PRD names the fix explicitly: "Der Nulleffekt wird per Block-Bootstrap
aus unkorrelierten Surrogaten mit identischer Randverteilung erzeugt,
nicht mit 0 angesetzt." This module builds exactly that -- TWO surrogate
null variants, reported side by side, never as a threshold/gate.

**(1) ``independent_blocks`` -- the baseline sampling-noise null.** Each
series is resampled SEPARATELY by a circular moving-block bootstrap
(``block_bootstrap_resample``, block_len=5 days -- the repo's standard
block convention, matching ``portfolio_null.BLOCK_LEN_DAYS``/
``c17_venue.stats``/``c11_anen.stats``/``wp9_dvol.crossval``): this
preserves each series' own marginal distribution EXACTLY (a pure
reordering/repetition of its own observed values) and its short-range
(within-block) autocorrelation, while the TWO series' resamples are drawn
from independently seeded generators -- so by construction the surrogate
pair carries ZERO true cross-series dependence. The REAL STRESS_ABS mask
(fixed calendar-day positions) is then applied to this synthetic-but-
otherwise-realistic pair, exactly as it is applied to the real data, and
the null distribution of ``rho_stress - rho_quiet`` (the "lift") answers:
how much lift would ONLY finite-sample noise at these specific stress-day
positions produce even with genuinely uncorrelated series?

**(2) ``selection_on_common_size`` -- the mechanical-selection null.**
Stricter: instead of the fixed real mask, EACH surrogate draw re-derives
its OWN stress mask from its OWN joint magnitude (the top-``q`` days of
``|x_surrogate| + |y_surrogate|``, ``q = n_stress / n`` so the selected
count matches the real stress cell exactly). This is precisely the
"Selektion auf gemeinsame Groesse" mechanism the PRD names: choosing
WHICH days count as "stress" from the same data the correlation is then
measured on.

**On the SIGN of this variant's bias (deliberately not assumed).** For
two GENUINELY independent series, re-deriving the mask from joint
magnitude reliably produces a lift distribution that is NOT centred on
the fixed-mask (``independent_blocks``) null -- but the DIRECTION of that
shift is a property of the data's marginal shape, not a fixed sign this
module can promise. Two regimes are both real and both reproducible here:
(i) sign-symmetric marginals (e.g. Gaussian/Student-t innovations, with
or without shared heteroskedasticity) leave BOTH variants centred near
zero -- selecting on ``|x|+|y|`` alone cannot manufacture a mean bias out
of pure noise when negating either series leaves the selection event and
the marginal law unchanged (an exact symmetry, not an approximation);
(ii) one-sided/skewed marginals (e.g. independent negative-only "crash"
spikes on each series, plausible for a premium-proxy PnL) DO shift the
``selection_on_common_size`` lift away from zero -- empirically, in this
module's own adversarial test fixture, NEGATIVE (a "conditioning on a
large joint sum anti-correlates the addends" effect, the same mechanism
behind the classic result that conditioning two independent variables on
an extreme SUM induces negative correlation between them). Either
direction is exactly the point: a magnitude-re-derived mask is NOT a safe
zero-effect null to assume, which is why this variant exists and is
reported NEXT TO, never instead of, the fixed-mask baseline.

Reported for BOTH variants: mean/sd/p5/p95 of the null ``rho_stress``,
``rho_quiet`` and ``lift`` distributions, plus the REAL lift's percentile
rank within each null lift distribution -- purely DESCRIPTIVE placement,
never a p-value gate and never compared against a threshold.

**Own local Spearman-rho copy.** ``coherence.py`` already carries one and
documents the repo's "own copy, no cross-import between packages"
convention; importing it HERE would create a circular WITHIN-package
import (``coherence`` would need to import this module for the wiring in
``pairwise_regime_result``, and this module would import back from
``coherence`` for ``spearman_rho``). Rather than restructure the existing
module boundary, this module keeps its OWN tiny copy -- same convention,
applied one level down to break the cycle.

**DEC-53 (b) extension (spec item 5).** ``surrogate_generator_fingerprint``
hashes the first 100 draws of a null distribution (SHA-256 over the raw
float64 bytes) -- together with the stored ``seed``/``n_surrogates``/
``block_len``, sufficient for ``report.py`` to pin that a re-run
reproduces the SAME surrogate draws bit-identically, exactly as the
existing coherence/portfolio-null bootstrap entries already do.

KAPITALFREI: pure statistics. No cost quantity, no PASS/FAIL, no
threshold word applied to any of these numbers.
"""
from __future__ import annotations

import hashlib
from typing import Any

import numpy as np

__all__ = [
    "SurrogateNullError", "BLOCK_LEN_DAYS", "N_SURROGATES",
    "spearman_rho", "block_bootstrap_resample", "pair_surrogate_null",
    "surrogate_generator_fingerprint",
]

#: Repo's standard block-bootstrap block length (5 calendar days -- matches
#: ``portfolio_null.BLOCK_LEN_DAYS``; kept as an own local constant here to
#: avoid a needless cross-module import for a single integer).
BLOCK_LEN_DAYS = 5
#: Spec: "B = 1000".
N_SURROGATES = 1000


class SurrogateNullError(RuntimeError):
    """Loud failure: cannot build a surrogate null from this input."""


# ------------------------------------------------------- own Spearman copy

def _rankdata_average(v: np.ndarray) -> np.ndarray:
    """Average ranks for ties (own copy -- see module docstring)."""
    v = np.asarray(v, dtype=np.float64)
    n = v.size
    order = np.argsort(v, kind="mergesort")
    sv = v[order]
    inv = np.empty(n, dtype=np.int64)
    inv[order] = np.arange(n)
    obs = np.concatenate(([True], sv[1:] != sv[:-1]))
    dense = np.cumsum(obs)[inv]
    bounds = np.concatenate((np.nonzero(obs)[0], [n]))
    return 0.5 * (bounds[dense - 1] + bounds[dense] + 1).astype(np.float64)


def spearman_rho(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation (average ranks + Pearson on ranks).
    NaN if degenerate (constant series or < 2 points). Own copy of
    ``coherence.spearman_rho`` -- see module docstring for why."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if x.size != y.size or x.size < 2:
        return float("nan")
    rx = _rankdata_average(x) - _rankdata_average(x).mean()
    ry = _rankdata_average(y) - _rankdata_average(y).mean()
    denom = float(np.sqrt(np.sum(rx ** 2) * np.sum(ry ** 2)))
    if denom <= 0.0 or not np.isfinite(denom):
        return float("nan")
    return float(np.sum(rx * ry) / denom)


# --------------------------------------------------------- block bootstrap

def block_bootstrap_resample(v: np.ndarray, rng: np.random.Generator, *,
                             block_len: int = BLOCK_LEN_DAYS) -> np.ndarray:
    """Circular moving-block bootstrap resample of ``v`` (length n): draw
    ``ceil(n / block_len)`` block START positions i.i.d. with replacement,
    uniform over ``0..n-1``, WRAPPING circularly (so every start position
    is equally likely regardless of proximity to the array end -- the
    standard fix for the edge-bias of a plain, non-wrapping moving-block
    bootstrap), concatenate the resulting blocks, and truncate to length n.

    Preserves ``v``'s marginal distribution EXACTLY (a pure reordering/
    repetition of its own observed values -- no new values are invented)
    and its short-range (within-block) autocorrelation structure, since
    each block of ``block_len`` CONSECUTIVE (circularly) observations is
    carried over intact.
    """
    if block_len < 1:
        raise SurrogateNullError(f"block_len must be >= 1, got {block_len}")
    v = np.asarray(v, dtype=np.float64)
    n = v.size
    if n == 0:
        return np.empty(0, dtype=np.float64)
    n_blocks = int(np.ceil(n / block_len))
    starts = rng.integers(0, n, size=n_blocks)
    idx = np.concatenate([np.arange(s, s + block_len) % n for s in starts])[:n]
    return v[idx]


# ------------------------------------------------------------ fingerprint

def surrogate_generator_fingerprint(draws: np.ndarray, *, n_head: int = 100) -> str:
    """SHA-256 over the raw float64 bytes of the first ``n_head`` draws of
    a null distribution (DEC-53 (b) extension, spec item 5) -- see module
    docstring."""
    draws = np.asarray(draws, dtype=np.float64)
    head = np.ascontiguousarray(draws[:n_head])
    return hashlib.sha256(head.tobytes()).hexdigest()


def _summarize(arr: np.ndarray) -> dict[str, float]:
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return {"mean": float("nan"), "sd": float("nan"), "p5": float("nan"), "p95": float("nan")}
    sd = float(np.std(finite, ddof=1)) if finite.size > 1 else 0.0
    p5, p95 = (float(v) for v in np.quantile(finite, [0.05, 0.95]))
    return {"mean": float(np.mean(finite)), "sd": sd, "p5": p5, "p95": p95}


def _rank_pct(real: float, null_draws: np.ndarray) -> float:
    """Percentile rank of ``real`` within ``null_draws`` -- purely
    DESCRIPTIVE placement (fraction of null draws <= real, as a percent),
    never a p-value gate. NaN if either side is degenerate."""
    finite = null_draws[np.isfinite(null_draws)]
    if finite.size == 0 or not np.isfinite(real):
        return float("nan")
    return float(np.mean(finite <= real) * 100.0)


def _variant_result(real_lift: float, rho_stress: np.ndarray, rho_quiet: np.ndarray,
                    lift: np.ndarray) -> dict[str, Any]:
    return {
        "rho_stress": _summarize(rho_stress), "rho_quiet": _summarize(rho_quiet),
        "lift": _summarize(lift), "real_lift_rank_pct": _rank_pct(real_lift, lift),
        "lift_fingerprint_sha256": surrogate_generator_fingerprint(lift),
    }


def pair_surrogate_null(x: np.ndarray, y: np.ndarray, stress_mask: np.ndarray, *,
                        n_surrogates: int = N_SURROGATES, seed: int,
                        block_len: int = BLOCK_LEN_DAYS) -> dict[str, Any]:
    """The structural null effect (PRD C.4) for ONE pair's stress cell.

    ``x``/``y`` are the SAME (first-differenced) aligned overlap arrays
    ``coherence.differenced_pair_overlap`` produces; ``stress_mask`` is the
    matching boolean STRESS_ABS mask over that overlap. Needs >= 4 stress
    AND >= 4 quiet observations (same floor as
    ``coherence.cluster_bootstrap_rho_ci``) to compute a Spearman rho on
    either regime -- else ``{"status": "TOO_FEW"}``, mirroring the pair's
    own "stress" cell TOO_FEW status.

    Deterministic for a given ``(x, y, stress_mask, seed, n_surrogates,
    block_len)`` -- two independently seeded generators (tagged ``(seed,
    0)``/``(seed, 1)``) drive ``x``'s and ``y``'s block-bootstrap draws
    respectively, consumed sequentially over ``n_surrogates`` iterations.
    """
    if n_surrogates < 1:
        raise SurrogateNullError(f"n_surrogates must be >= 1, got {n_surrogates}")
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    mask = np.asarray(stress_mask, dtype=bool)
    n = x.size
    if x.shape != y.shape or mask.shape != x.shape:
        raise SurrogateNullError(
            f"x/y/stress_mask must share one shape, got {x.shape}/{y.shape}/{mask.shape}")
    n_stress = int(mask.sum())
    n_quiet = int(n - n_stress)
    if n_stress < 4 or n_quiet < 4:
        return {"status": "TOO_FEW", "n_stress": n_stress, "n_quiet": n_quiet}

    real_rho_stress = spearman_rho(x[mask], y[mask])
    real_rho_quiet = spearman_rho(x[~mask], y[~mask])
    real_lift = real_rho_stress - real_rho_quiet

    rng_x = np.random.default_rng((int(seed), 0))
    rng_y = np.random.default_rng((int(seed), 1))

    rho_stress = np.empty(n_surrogates, dtype=np.float64)
    rho_quiet = np.empty(n_surrogates, dtype=np.float64)
    lift = np.empty(n_surrogates, dtype=np.float64)
    rho_stress_sel = np.empty(n_surrogates, dtype=np.float64)
    rho_quiet_sel = np.empty(n_surrogates, dtype=np.float64)
    lift_sel = np.empty(n_surrogates, dtype=np.float64)

    for b in range(n_surrogates):
        xs = block_bootstrap_resample(x, rng_x, block_len=block_len)
        ys = block_bootstrap_resample(y, rng_y, block_len=block_len)

        # (1) independent_blocks: the REAL, fixed stress mask.
        rs = spearman_rho(xs[mask], ys[mask])
        rq = spearman_rho(xs[~mask], ys[~mask])
        rho_stress[b], rho_quiet[b], lift[b] = rs, rq, rs - rq

        # (2) selection_on_common_size: mask re-derived from THIS
        # surrogate's own joint magnitude, top-q days, q = n_stress/n.
        joint_mag = np.abs(xs) + np.abs(ys)
        top_idx = np.argsort(-joint_mag, kind="mergesort")[:n_stress]
        sel_mask = np.zeros(n, dtype=bool)
        sel_mask[top_idx] = True
        rs2 = spearman_rho(xs[sel_mask], ys[sel_mask])
        rq2 = spearman_rho(xs[~sel_mask], ys[~sel_mask])
        rho_stress_sel[b], rho_quiet_sel[b], lift_sel[b] = rs2, rq2, rs2 - rq2

    return {
        "status": "OK", "n_stress": n_stress, "n_quiet": n_quiet,
        "n_surrogates": int(n_surrogates), "seed": int(seed), "block_len": int(block_len),
        "real": {"rho_stress": real_rho_stress, "rho_quiet": real_rho_quiet, "lift": real_lift},
        "independent_blocks": _variant_result(real_lift, rho_stress, rho_quiet, lift),
        "selection_on_common_size": _variant_result(real_lift, rho_stress_sel, rho_quiet_sel, lift_sel),
    }
