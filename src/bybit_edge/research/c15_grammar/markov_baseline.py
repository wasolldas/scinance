"""Variable-order Markov baselines (k <= 4, KT-smoothed) for H-15 (CPU/numpy).

Registry H-15 (pre-fixed): "Baseline: interpoliertes/KT-geglaettetes
Variable-Order-Markov-Modell k<=4, gleicher Train-Fold". This module is the
deliberately CPU-cheap comparison arm — pure numpy, no torch.

Two baseline forms, both fitted on the SAME train fold as the transformer:

  * ``MarkovKT(order=k)`` — fixed-order Markov model with the
    Krichevsky-Trofimov (add-1/2) estimator:
        p(x | ctx) = (c(ctx, x) + 1/2) / (c(ctx) + V/2).
    An unseen context degrades to the uniform 1/V (honest, never a crash).
  * ``InterpolatedMarkov(max_order=4)`` — recursive KT-style backoff
    interpolation over orders k..0:
        p_k(x | ctx_k) = (c_k(ctx_k, x) + beta * p_{k-1}(x | ctx_{k-1}))
                         / (c_k(ctx_k) + beta),   beta = V/2,
    base case p_{-1} = 1/V. For an unseen context this reduces exactly to
    the next-lower order (consistent backoff); for order 0 with beta = V/2
    it reduces to the KT estimator.

The registered gate compares the transformer against the BEST of these
baselines on the OOS fold (lowest OOS CE over {KT k=0..4, interpolated k=4}),
i.e. the baseline choice always FAVOURS the null — conservative by design.

Cross-entropy convention (binding for every model in this package, including
the transformer): mean NEGATIVE NATURAL log-likelihood per token (nats),
averaged over positions ``t >= CE_WARMUP`` of the standalone evaluation
stream. ``CE_WARMUP = 4`` (= max Markov order) makes every model — all Markov
orders AND the transformer — score exactly the same token positions, so the
CE gap is never an artefact of differing evaluation supports. The gate's 2%
threshold is RELATIVE, hence unit-invariant (nats vs bits cancels).

Counting/evaluation is fully vectorised (sorted-key binary-search lookups) —
the >= 200 surrogate CE evaluations per fold (registry null) stay CPU-cheap
even on multi-million-token test folds.

KAPITALFREI: pure sequence statistics. No capital metric anywhere.
"""
from __future__ import annotations

import numpy as np

#: Maximum registered Markov order (registry H-15: k <= 4).
MAX_ORDER = 4

#: Shared evaluation warm-up: the first CE_WARMUP positions of an OOS stream
#: are excluded from CE for EVERY model (see module docstring).
CE_WARMUP = MAX_ORDER


class MarkovError(ValueError):
    """Raised on malformed Markov-model usage."""


def _context_codes(tokens: np.ndarray, order: int, vocab_size: int,
                   start: int) -> np.ndarray:
    """Integer context codes for positions ``start..n-1`` (``start >= order``).

    code(t) = sum_{j=1..order} tokens[t-j] * V^(j-1)  (order 0 -> zeros).
    Fits in int64 for V=256, order 4 (256^4 * V < 2^63 for the pair code too).
    """
    n = tokens.size
    if start < order:
        raise MarkovError("start must be >= order")
    if n <= start:
        return np.zeros(0, dtype=np.int64)
    codes = np.zeros(n - start, dtype=np.int64)
    mult = 1
    for j in range(1, order + 1):
        codes += tokens[start - j: n - j].astype(np.int64) * mult
        mult *= vocab_size
    return codes


class _SortedCounts:
    """Sorted-key count table with vectorised binary-search lookup."""

    __slots__ = ("keys", "vals")

    def __init__(self, keys: np.ndarray, vals: np.ndarray) -> None:
        self.keys = keys  # sorted int64
        self.vals = vals  # int64 counts

    @classmethod
    def from_codes(cls, codes: np.ndarray) -> "_SortedCounts":
        keys, vals = np.unique(codes, return_counts=True)
        return cls(keys.astype(np.int64), vals.astype(np.int64))

    def lookup(self, queries: np.ndarray) -> np.ndarray:
        """Counts for ``queries`` (0 where absent), vectorised."""
        if self.keys.size == 0:
            return np.zeros(queries.size, dtype=np.int64)
        idx = np.searchsorted(self.keys, queries)
        idx_c = np.clip(idx, 0, self.keys.size - 1)
        found = self.keys[idx_c] == queries
        return np.where(found, self.vals[idx_c], 0)


def _fit_order_counts(tokens: np.ndarray, order: int, vocab_size: int
                      ) -> tuple[_SortedCounts, _SortedCounts]:
    """(pair_counts, ctx_counts) for one order from one contiguous stream."""
    n = tokens.size
    if n <= order:
        empty = _SortedCounts(np.zeros(0, dtype=np.int64), np.zeros(0, dtype=np.int64))
        return empty, empty
    ctx = _context_codes(tokens, order, vocab_size, order)
    nxt = tokens[order:].astype(np.int64)
    pair = ctx * vocab_size + nxt
    return _SortedCounts.from_codes(pair), _SortedCounts.from_codes(ctx)


class MarkovKT:
    """Fixed-order Markov model with KT (add-1/2) smoothing."""

    def __init__(self, order: int, vocab_size: int, alpha: float = 0.5) -> None:
        if not 0 <= order <= MAX_ORDER:
            raise MarkovError(f"order must be 0..{MAX_ORDER}, got {order}")
        if vocab_size < 2:
            raise MarkovError("vocab_size must be >= 2")
        self.order = int(order)
        self.vocab_size = int(vocab_size)
        self.alpha = float(alpha)
        self._pair: _SortedCounts | None = None
        self._ctx: _SortedCounts | None = None

    def fit(self, train_tokens: np.ndarray) -> "MarkovKT":
        tokens = np.asarray(train_tokens, dtype=np.int64)
        _check_tokens(tokens, self.vocab_size)
        self._pair, self._ctx = _fit_order_counts(tokens, self.order, self.vocab_size)
        return self

    def log_probs(self, tokens: np.ndarray) -> np.ndarray:
        """Natural-log probabilities for positions ``CE_WARMUP..n-1``.

        The stream is evaluated STANDALONE (context comes only from the
        stream itself — no cross-fold conditioning; causal by construction:
        position t is predicted from tokens < t only).
        """
        if self._pair is None or self._ctx is None:
            raise MarkovError("fit() before log_probs()")
        tokens = np.asarray(tokens, dtype=np.int64)
        _check_tokens(tokens, self.vocab_size)
        n = tokens.size
        if n <= CE_WARMUP:
            return np.zeros(0, dtype=np.float64)
        V = self.vocab_size
        ctx = _context_codes(tokens, self.order, V, CE_WARMUP)
        nxt = tokens[CE_WARMUP:].astype(np.int64)
        num = self._pair.lookup(ctx * V + nxt).astype(np.float64) + self.alpha
        den = self._ctx.lookup(ctx).astype(np.float64) + self.alpha * V
        return np.log(num / den)

    def cross_entropy(self, tokens: np.ndarray) -> float:
        """Mean OOS CE in nats over positions >= CE_WARMUP."""
        lp = self.log_probs(tokens)
        if lp.size == 0:
            return float("nan")
        return float(-np.mean(lp))


class InterpolatedMarkov:
    """Recursive KT-style backoff interpolation over orders max_order..0."""

    def __init__(self, max_order: int = MAX_ORDER, vocab_size: int = 128,
                 alpha: float = 0.5) -> None:
        if not 0 <= max_order <= MAX_ORDER:
            raise MarkovError(f"max_order must be 0..{MAX_ORDER}, got {max_order}")
        if vocab_size < 2:
            raise MarkovError("vocab_size must be >= 2")
        self.max_order = int(max_order)
        self.vocab_size = int(vocab_size)
        self.alpha = float(alpha)
        self.beta = self.alpha * self.vocab_size  # V/2 for alpha = 1/2
        self._pair: list[_SortedCounts] = []
        self._ctx: list[_SortedCounts] = []

    def fit(self, train_tokens: np.ndarray) -> "InterpolatedMarkov":
        tokens = np.asarray(train_tokens, dtype=np.int64)
        _check_tokens(tokens, self.vocab_size)
        self._pair, self._ctx = [], []
        for k in range(self.max_order + 1):
            p, c = _fit_order_counts(tokens, k, self.vocab_size)
            self._pair.append(p)
            self._ctx.append(c)
        return self

    def log_probs(self, tokens: np.ndarray) -> np.ndarray:
        """Natural-log probabilities for positions ``CE_WARMUP..n-1``."""
        if not self._pair:
            raise MarkovError("fit() before log_probs()")
        tokens = np.asarray(tokens, dtype=np.int64)
        _check_tokens(tokens, self.vocab_size)
        n = tokens.size
        if n <= CE_WARMUP:
            return np.zeros(0, dtype=np.float64)
        V = self.vocab_size
        beta = self.beta
        nxt = tokens[CE_WARMUP:].astype(np.int64)
        p = np.full(nxt.size, 1.0 / V, dtype=np.float64)  # base case p_{-1}
        for k in range(self.max_order + 1):
            ctx = _context_codes(tokens, k, V, CE_WARMUP)
            num = self._pair[k].lookup(ctx * V + nxt).astype(np.float64)
            den = self._ctx[k].lookup(ctx).astype(np.float64)
            p = (num + beta * p) / (den + beta)
        return np.log(p)

    def cross_entropy(self, tokens: np.ndarray) -> float:
        lp = self.log_probs(tokens)
        if lp.size == 0:
            return float("nan")
        return float(-np.mean(lp))


def fit_all_baselines(train_tokens: np.ndarray, vocab_size: int
                      ) -> dict[str, MarkovKT | InterpolatedMarkov]:
    """Fit the full registered baseline family on ONE train fold.

    Returns {"kt_k0".."kt_k4", "interp_k4"} — all Markov with k <= 4.
    """
    models: dict[str, MarkovKT | InterpolatedMarkov] = {}
    for k in range(MAX_ORDER + 1):
        models[f"kt_k{k}"] = MarkovKT(order=k, vocab_size=vocab_size).fit(train_tokens)
    models[f"interp_k{MAX_ORDER}"] = InterpolatedMarkov(
        max_order=MAX_ORDER, vocab_size=vocab_size,
    ).fit(train_tokens)
    return models


def best_baseline_ce(models: dict[str, MarkovKT | InterpolatedMarkov],
                     test_tokens: np.ndarray) -> tuple[str, float, dict[str, float]]:
    """OOS CE of every baseline; returns (best_name, best_ce, all_ces).

    "Best" = LOWEST OOS CE (registry: "beste Markov-k-(k<=4)-Baseline") —
    the strongest opponent for the transformer, favouring the null.
    """
    ces = {name: m.cross_entropy(test_tokens) for name, m in models.items()}
    finite = {k: v for k, v in ces.items() if np.isfinite(v)}
    if not finite:
        return "", float("nan"), ces
    best_name = min(finite, key=lambda k: finite[k])
    return best_name, float(finite[best_name]), ces


def _check_tokens(tokens: np.ndarray, vocab_size: int) -> None:
    if tokens.ndim != 1:
        raise MarkovError("tokens must be 1-D")
    if tokens.size and (int(tokens.min()) < 0 or int(tokens.max()) >= vocab_size):
        raise MarkovError(
            f"token ids outside [0, {vocab_size}): "
            f"min={int(tokens.min())} max={int(tokens.max())}"
        )


__all__ = [
    "CE_WARMUP",
    "InterpolatedMarkov",
    "MAX_ORDER",
    "MarkovError",
    "MarkovKT",
    "best_baseline_ce",
    "fit_all_baselines",
]
