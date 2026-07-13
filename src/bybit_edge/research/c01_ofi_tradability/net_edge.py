"""Net-edge statistics + bootstrap/surrogate significance + BH-FDR for H-05c.

The registry H-05c gate (DEC-16) asks whether the NET edge per round-trip — the
latency-haircut SOL fade-capture minus the 11 bps friction wall minus slippage —
is **> 0 AND statistically > 0** (bootstrap ``p <= 0.05`` after BH-FDR alpha=0.10
over the F-OFI-INV-TRADE family) on ``>= 2`` disjoint windows, for at least one
of the GL-010 pass-cells {SOL-δ1s, SOL-δ5s}.

Two nulls per (window, delta) variant, identical contract to H-04b net_edge:
* **Bootstrap** (primary): one-sided **circular block** resample of the
  per-round-trip net edges (repo convention: contiguous-block bootstrap,
  same construction as ``c11_anen.stats.block_bootstrap_p`` /
  ``c06_xmr.stats.block_bootstrap_ci``);
  ``p = (#{resample_mean <= 0} + 1) / (N + 1)`` — small p => mean net edge > 0.
  Consecutive round-trips share overlapping forward-return windows whenever
  ``delta_s * 1000 > grid_ms`` (e.g. ~80% overlap at delta_s=5/grid_ms=1000),
  so i.i.d. resampling of single round-trips understates the true sampling
  variance of the mean and yields anti-conservative p-values. The block
  length is sized to the overlap (``ceil(delta_s * 1000 / grid_ms)``
  round-trips, see :mod:`driver`) so each resampled block spans roughly one
  independent forward-return horizon.
* **Surrogate** (diagnostic): a fade-sign permutation null (randomises the
  position sign) recomputing the mean net edge.

BH-FDR (alpha=0.10) over the WHOLE F-OFI-INV-TRADE family (all delta x window).
Own copy of the FDR helper (registry §8.2 — no cross-import between packages).

NON-KAPITALFREI: net-edge / bps logic H-05b deliberately omitted. Still a
historical backtest with a cost model — NO live orders (CLAUDE.md §4).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: BH-FDR level for the F-OFI-INV-TRADE family (registry H-05c).
FDR_ALPHA = 0.10

#: Registered net-edge significance threshold (DEC-16): p <= 0.05.
NET_EDGE_P_MAX = 0.05

#: Minimum bootstrap resamples (registry: Bootstrap-N >= 200).
DEFAULT_BOOTSTRAP = 200


@dataclass(slots=True)
class NetEdgeResult:
    """Net-edge statistics for one (window, delta) variant."""

    delta_s: int
    n_trips: int
    gross_capture_bps_mean: float   # mean directional (fade-signed) captured SOL move in bps
    gross_full_bps_mean: float      # mean full (no-haircut) move in bps (diag)
    wall_bps: float                 # friction + slippage charged
    net_edge_bps_mean: float        # mean per-round-trip net edge in bps
    bootstrap_p: float              # P(mean net edge <= 0) under bootstrap
    surrogate_p: float              # fade-sign-permutation null p (diagnostic)
    n_bootstrap: int

    def as_dict(self) -> dict[str, object]:
        return {
            "delta_s": int(self.delta_s),
            "n_trips": int(self.n_trips),
            "gross_capture_bps_mean": float(self.gross_capture_bps_mean),
            "gross_full_bps_mean": float(self.gross_full_bps_mean),
            "wall_bps": float(self.wall_bps),
            "net_edge_bps_mean": float(self.net_edge_bps_mean),
            "bootstrap_p": float(self.bootstrap_p),
            "surrogate_p": float(self.surrogate_p),
            "n_bootstrap": int(self.n_bootstrap),
        }


def block_len_for_overlap(delta_s: int, grid_ms: float) -> int:
    """Bootstrap block length (in round-trips) sized to the forward-window overlap.

    Consecutive round-trips are spaced ``grid_ms`` apart but each looks
    ``delta_s * 1000`` ms forward, so they share overlapping return windows
    whenever ``delta_s * 1000 > grid_ms``. ``ceil(delta_s * 1000 / grid_ms)``
    round-trips is the smallest block that spans one full non-overlapping
    forward-return horizon (e.g. 5 round-trips at delta_s=5s/grid_ms=1000ms,
    where ~80% of consecutive returns overlap). Returns >= 1 (1 = no overlap,
    degenerates to i.i.d. resampling).
    """
    if grid_ms <= 0:
        return 1
    return max(1, int(np.ceil(delta_s * 1000.0 / grid_ms)))


def bootstrap_mean_le_zero_p(
    net_edges_bps: np.ndarray,
    *,
    n_bootstrap: int = DEFAULT_BOOTSTRAP,
    block_len: int = 1,
    seed: int = 42,
) -> float:
    """One-sided **circular block** bootstrap p for ``H0: mean net edge <= 0`` vs ``H1: > 0``.

    Resamples in contiguous, circularly-wrapped blocks of ``block_len``
    consecutive round-trips (repo convention: same construction as
    ``c11_anen.stats.block_bootstrap_p`` / ``c06_xmr.stats.block_bootstrap_ci``)
    instead of single i.i.d. observations, so the resample preserves the
    short-range autocorrelation induced by overlapping forward-return
    windows (see :func:`block_len_for_overlap`). ``block_len=1`` degenerates
    to the original i.i.d. bootstrap (used only where there is no overlap,
    e.g. delta_s * 1000 <= grid_ms).
    """
    x = np.asarray(net_edges_bps, dtype=np.float64)
    n = x.size
    if n < 4 or n_bootstrap < 1:
        return 1.0
    bs = max(1, min(int(block_len), n))
    n_blocks = int(np.ceil(n / bs))
    rng = np.random.default_rng(seed)
    offsets = np.arange(bs)
    n_le = 0
    for _ in range(n_bootstrap):
        starts = rng.integers(0, n, size=n_blocks)
        idx = (starts[:, None] + offsets[None, :]) % n  # circular contiguous blocks
        resample = x[idx.reshape(-1)][:n]
        if float(np.mean(resample)) <= 0.0:
            n_le += 1
    return (n_le + 1) / (n_bootstrap + 1)


def sign_permutation_p(
    captured_moves_logret: np.ndarray,
    position_signs: np.ndarray,
    wall_bps: float,
    *,
    bps_per_logret: float,
    n_surrogates: int = DEFAULT_BOOTSTRAP,
    seed: int = 42,
) -> float:
    """Fade-sign-permutation surrogate p for the directional net edge (diagnostic).

    The null randomises the position SIGN (destroying the OFI->inverse-move link
    while preserving the SOL-move magnitude distribution). ``captured_moves_logret``
    are the RAW (unsigned-by-position) SOL moves; ``position_signs`` the actual
    fade +/-1 signals. ``p = (#{surrogate_mean >= observed} + 1)/(N + 1)``.
    """
    cm = np.asarray(captured_moves_logret, dtype=np.float64)
    sg = np.asarray(position_signs, dtype=np.float64)
    n = min(cm.size, sg.size)
    if n < 4 or n_surrogates < 1:
        return 1.0
    cm, sg = cm[:n], sg[:n]
    observed = float(np.mean(sg * cm) * bps_per_logret - wall_bps)
    rng = np.random.default_rng(seed)
    stats = np.empty(n_surrogates, dtype=np.float64)
    for k in range(n_surrogates):
        flip = rng.choice(np.array([-1.0, 1.0]), size=n)
        stats[k] = float(np.mean(flip * cm) * bps_per_logret - wall_bps)
    n_ge = int(np.sum(stats >= observed))
    return (n_ge + 1) / (n_surrogates + 1)


def benjamini_hochberg(
    p_values: list[float], alpha: float = FDR_ALPHA
) -> tuple[list[bool], float]:
    """Benjamini-Hochberg FDR over a family of p-values (own copy, §8.2)."""
    m = len(p_values)
    if m == 0:
        return [], 0.0
    order = sorted(range(m), key=lambda i: p_values[i])
    p_crit = 0.0
    k_max = -1
    for rank, idx in enumerate(order, start=1):
        if p_values[idx] <= (rank / m) * alpha:
            k_max = rank
            p_crit = p_values[idx]
    rejected = [False] * m
    if k_max >= 0:
        for rank, idx in enumerate(order, start=1):
            if rank <= k_max:
                rejected[idx] = True
    return rejected, p_crit
