"""Net-edge statistics + bootstrap/surrogate significance + BH-FDR for H-04b.

The registry H-04b gate (DEC-13) asks whether the NET edge per round-trip — the
latency-haircut ETH capture move minus the 11 bps friction wall minus slippage —
is **> 0 AND statistically > 0** (bootstrap/surrogate ``p <= 0.05`` after BH-FDR
alpha = 0.10 over the F-LEADLAG-TRADE family) on ``>= 2`` disjoint windows.

Two complementary nulls are reported per (window, lag) variant:

* **Bootstrap** (primary, registry "Bootstrap/Surrogate"): a one-sided
  stationary/iid bootstrap of the per-round-trip net edges. The p-value is the
  fraction of bootstrap resample means ``<= 0`` (plus the ``(+1)/(N+1)``
  add-one correction), i.e. "is the mean net edge significantly > 0?". N >= 200,
  seed-fixed (registry "Bootstrap-N>=200, seed-fix").
* **Surrogate** (secondary, diagnostic): a sign-permutation null that destroys
  the BTC->ETH directional link by randomising the position sign, recomputing
  the mean net edge. Reported alongside so the gate-auditor sees both.

BH-FDR (Benjamini-Hochberg, alpha = 0.10) is applied across the WHOLE
F-LEADLAG-TRADE family (all lag x window variants — registry H-04b Z.134).
Identical FDR contract to the C-31 / C-17 / C-01 implementations (§8.2; each
research package keeps its own copy, no cross-import of the FDR helper).

NON-KAPITALFREI: this is the net-edge / bps logic that H-04 deliberately omitted.
Still a historical backtest with a cost model — NO live orders (CLAUDE.md §4).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: BH-FDR level for the F-LEADLAG-TRADE family (registry H-04b Z.134).
FDR_ALPHA = 0.10

#: Registered net-edge significance threshold (DEC-13): p <= 0.05.
NET_EDGE_P_MAX = 0.05

#: Minimum bootstrap resamples (registry: Bootstrap-N >= 200).
DEFAULT_BOOTSTRAP = 200


@dataclass(slots=True)
class NetEdgeResult:
    """Net-edge statistics for one (window, lag) variant."""

    lag: int
    horizon: int
    n_trips: int
    gross_capture_bps_mean: float   # mean directional captured ETH move in bps
    gross_full_bps_mean: float      # mean full (no-haircut) move in bps (diag)
    wall_bps: float                 # friction + slippage charged
    net_edge_bps_mean: float        # mean per-round-trip net edge in bps
    bootstrap_p: float              # P(mean net edge <= 0) under bootstrap
    surrogate_p: float              # sign-permutation null p (diagnostic)
    n_bootstrap: int

    def as_dict(self) -> dict[str, object]:
        return {
            "lag": int(self.lag),
            "horizon": int(self.horizon),
            "n_trips": int(self.n_trips),
            "gross_capture_bps_mean": float(self.gross_capture_bps_mean),
            "gross_full_bps_mean": float(self.gross_full_bps_mean),
            "wall_bps": float(self.wall_bps),
            "net_edge_bps_mean": float(self.net_edge_bps_mean),
            "bootstrap_p": float(self.bootstrap_p),
            "surrogate_p": float(self.surrogate_p),
            "n_bootstrap": int(self.n_bootstrap),
        }


def bootstrap_mean_le_zero_p(
    net_edges_bps: np.ndarray,
    *,
    n_bootstrap: int = DEFAULT_BOOTSTRAP,
    seed: int = 42,
) -> float:
    """One-sided bootstrap p for ``H0: mean net edge <= 0`` vs ``H1: > 0``.

    Resamples the per-round-trip net edges with replacement ``n_bootstrap``
    times and returns ``(#{resample_mean <= 0} + 1) / (N + 1)`` — a small p
    means the mean net edge is robustly positive. Seed-fixed, reproducible.
    Returns 1.0 (cannot reject) when there are too few round-trips.
    """
    x = np.asarray(net_edges_bps, dtype=np.float64)
    n = x.size
    if n < 4 or n_bootstrap < 1:
        return 1.0
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_bootstrap, n))
    means = x[idx].mean(axis=1)
    n_le = int(np.sum(means <= 0.0))
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
    """Sign-permutation surrogate p for the directional net edge (diagnostic).

    The null randomises the position SIGN (destroying the BTC->ETH directional
    link while preserving the magnitude distribution of the ETH moves). The
    statistic is the mean net edge; ``p = (#{surrogate_mean >= observed} + 1)
    / (N + 1)`` is the chance of seeing this directional net edge under random
    entries. ``captured_moves_logret`` are the RAW (unsigned-by-position) ETH
    moves; ``position_signs`` the actual +/-1 signals.
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
    """Benjamini-Hochberg FDR over a family of p-values.

    Returns ``(rejected, p_crit)``: ``rejected[i]`` True if hypothesis ``i`` is
    significant at FDR ``alpha`` and ``p_crit`` the largest passing p-value
    (0.0 if none). Input order preserved. Identical contract to the C-31 / C-17 /
    C-01 implementations (registry §8.2 convention; each research package keeps
    its own copy — no cross-import between research packages).
    """
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
