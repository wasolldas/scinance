"""Bandt-Pompe Permutation Entropy on log-returns for the C-07 PE mess-gate
(Welle-2 WP, H-06, KAPITALFREI).

H-06 tests one thing: does the Permutation Entropy (Bandt-Pompe, m/tau PRE-FIXED)
of the close-price log-returns carry conditional predictive information about
future returns / realized vol beyond what random surrogates give, and is the
PE-drop -> vol-cluster association large enough (rho >= 0.3) to clear the PRD-§4
pre-condition? This module builds the estimator; ``pre_gate.py`` / ``info_test.py``
run the two gate stages; the GATE VERDICT is the gate-auditor's call.

The embedding parameters are PRE-FIXED and intentionally NOT exposed as CLI flags
(claims_register §C-07: "Embedding-Parameter m=4, tau=1 ist fuer Bybit-Perp-Daten
optimal"; verdict.md §1f: "m/tau vorab fixiert sonst DROP"). They live here as
read-only module constants. Any deviation requires a NEW H-06 registry line, NOT
a variation inside this run (DEC-12).

PE definition (normalised Shannon entropy of ordinal patterns):

    For an embedding dimension m and delay tau, each length-m window
    ``x[i], x[i+tau], ..., x[i+(m-1)tau]`` is mapped to the permutation pi that
    sorts it (its ordinal pattern). The relative frequencies p(pi) of the m!
    possible patterns give H = -sum p(pi) log p(pi), normalised by log(m!) to
    [0, 1]. Low PE = ordered / low-complexity (a complexity collapse), high PE =
    disordered / random.

A "PE-drop" is a fall in the rolling PE series (complexity collapse -> precursor
of a volatility cluster, claims_register §C-07). It is measured as ``-diff(PE)``
so positive values denote a drop.

KAPITALFREI: pure information / complexity measurement. No friction, edge, bps,
PnL or Sharpe logic anywhere. numpy only.
"""
from __future__ import annotations

from math import factorial, log

import numpy as np

#: Bandt-Pompe embedding dimension — PRE-FIXED (claims_register §C-07). NOT a CLI
#: flag. Any deviation = NEW H-06 registry line (verdict.md §1f), see DEC-12.
PE_M = 4

#: Bandt-Pompe embedding delay — PRE-FIXED (claims_register §C-07). NOT a CLI flag.
PE_TAU = 1

#: Default rolling PE window in bars (DEC-12). 240 1-min bars = 4h — long enough
#: for a stable ordinal-pattern histogram over m! = 24 patterns, short enough to
#: track regime-local complexity. CLI ``--pe-window``.
DEFAULT_PE_WINDOW = 240


def log_returns(close: np.ndarray) -> np.ndarray:
    """Log-returns of a strictly positive close-price series.

    Returns ``log(close[i] / close[i-1])`` (length ``len(close) - 1``). Non-finite
    / non-positive prices are guarded: the corresponding returns are set to 0.0
    so the ordinal patterns stay well defined.
    """
    close = np.asarray(close, dtype=np.float64)
    if close.size < 2:
        return np.zeros(0, dtype=np.float64)
    prev = close[:-1]
    cur = close[1:]
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.log(cur / prev)
    r[~np.isfinite(r)] = 0.0
    return r


def _ordinal_pattern_codes(x: np.ndarray, m: int, tau: int) -> np.ndarray:
    """Encode each length-m (delay tau) embedding window of ``x`` as an int code.

    The code is the lexicographic index of the argsort permutation, in
    ``[0, m!)``. Vectorised over all windows. Returns an empty array when ``x``
    is too short to form a single embedding vector.
    """
    n = x.size
    span = (m - 1) * tau
    n_vec = n - span
    if n_vec <= 0:
        return np.zeros(0, dtype=np.int64)
    # Build the (n_vec, m) embedding matrix.
    idx = np.arange(n_vec)[:, None] + (np.arange(m) * tau)[None, :]
    emb = x[idx]
    # argsort each row -> the ordinal pattern (ties broken by index, stable).
    perms = np.argsort(emb, axis=1, kind="stable")
    # Encode each permutation as a unique integer via a factorial (Lehmer) code.
    weights = np.array([factorial(m - 1 - k) for k in range(m)], dtype=np.int64)
    codes = np.zeros(n_vec, dtype=np.int64)
    for k in range(m):
        # number of later elements smaller than perms[:, k]
        smaller = np.zeros(n_vec, dtype=np.int64)
        for j in range(k + 1, m):
            smaller += (perms[:, j] < perms[:, k]).astype(np.int64)
        codes += smaller * weights[k]
    return codes


def permutation_entropy(x: np.ndarray, m: int = PE_M, tau: int = PE_TAU) -> float:
    """Normalised Bandt-Pompe permutation entropy of ``x`` in ``[0, 1]``.

    ``m`` / ``tau`` default to the pre-fixed PE_M / PE_TAU; callers should not
    override them for the H-06 run (DEC-12). Returns 0.0 for series too short to
    embed.
    """
    codes = _ordinal_pattern_codes(np.asarray(x, dtype=np.float64), m, tau)
    if codes.size == 0:
        return 0.0
    counts = np.bincount(codes, minlength=factorial(m)).astype(np.float64)
    total = counts.sum()
    if total <= 0:
        return 0.0
    p = counts[counts > 0] / total
    h = -float(np.sum(p * np.log(p)))
    norm = log(factorial(m))
    if norm <= 0:
        return 0.0
    return max(0.0, min(1.0, h / norm))


def rolling_permutation_entropy(
    returns: np.ndarray,
    window: int = DEFAULT_PE_WINDOW,
    m: int = PE_M,
    tau: int = PE_TAU,
) -> np.ndarray:
    """Rolling permutation entropy over ``returns`` with the given bar ``window``.

    ``pe[i]`` is the PE of ``returns[i - window + 1 : i + 1]`` and is aligned to
    the RIGHT edge of its window (so it uses only past/current returns — causal).
    The leading ``window - 1`` positions are NaN. Output length == len(returns).
    """
    returns = np.asarray(returns, dtype=np.float64)
    n = returns.size
    out = np.full(n, np.nan, dtype=np.float64)
    span = (m - 1) * tau
    if window < span + 2 or n < window:
        return out
    for i in range(window - 1, n):
        seg = returns[i - window + 1 : i + 1]
        out[i] = permutation_entropy(seg, m, tau)
    return out


def pe_drop(pe_series: np.ndarray) -> np.ndarray:
    """PE-drop series: ``-diff(PE)`` aligned to the LATER bar (positive = drop).

    ``drop[i]`` corresponds to ``pe[i]`` and equals ``pe[i-1] - pe[i]`` (a fall in
    complexity at bar ``i``). The first position and any position touching a NaN
    PE value are NaN. Output length == len(pe_series).
    """
    pe = np.asarray(pe_series, dtype=np.float64)
    n = pe.size
    out = np.full(n, np.nan, dtype=np.float64)
    if n < 2:
        return out
    diff = pe[:-1] - pe[1:]  # pe[i-1] - pe[i]
    out[1:] = diff
    return out
