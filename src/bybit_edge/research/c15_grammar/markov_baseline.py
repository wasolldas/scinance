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

#: Chunk size (elements) for the vectorised count lookups. A single
#: full-width lookup on a ~30M-token surrogate materialises FOUR ~230-MiB
#: int64 temporaries at once (searchsorted idx, clipped idx, found mask,
#: where-result); chunking caps the transient footprint at ~30 MB while
#: staying BIT-IDENTICAL (every lookup is element-wise independent — no
#: float accumulation crosses a chunk boundary).
_LOOKUP_CHUNK = 4_000_000


class MarkovError(ValueError):
    """Raised on malformed Markov-model usage."""


def _as_token_array(tokens: np.ndarray) -> np.ndarray:
    """Integer token array WITHOUT forcing an int64 copy.

    Token ids fit in int16 for the registered vocabs (<= 256); every
    context/pair-code computation upcasts to int64 AT THE POINT OF USE
    (``_context_codes`` / the explicit ``.astype(np.int64)`` on next-token
    slices), so small-dtype STORAGE is bit-identical to int64 storage while
    using 4-8x less RAM on multi-hundred-million-token folds. Non-integer
    input keeps the old behaviour (cast to int64).
    """
    arr = np.asarray(tokens)
    if arr.dtype.kind not in "iu":
        arr = arr.astype(np.int64)
    return arr


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


def _context_codes_at(tokens: np.ndarray, order: int, vocab_size: int,
                      positions: np.ndarray) -> np.ndarray:
    """Context codes at SELECTED positions (each ``>= order``).

    Elementwise identical to ``_context_codes(tokens, order, ...)`` restricted
    to ``positions`` — same gather ``tokens[t-j]``, same int64 upcast, same
    multiplier accumulation order, hence bit-identical codes.
    """
    pos = np.asarray(positions, dtype=np.int64)
    if pos.size and int(pos.min()) < order:
        raise MarkovError("positions must be >= order")
    codes = np.zeros(pos.size, dtype=np.int64)
    mult = 1
    for j in range(1, order + 1):
        codes += tokens[pos - j].astype(np.int64) * mult
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
        """Counts for ``queries`` (0 where absent), vectorised.

        Chunked over ``_LOOKUP_CHUNK`` elements to cap peak temporaries
        (see the constant's comment) — bit-identical to the unchunked
        formulation since every element's lookup is independent.
        """
        if self.keys.size == 0:
            return np.zeros(queries.size, dtype=np.int64)
        out = np.empty(queries.size, dtype=np.int64)
        for s in range(0, queries.size, _LOOKUP_CHUNK):
            q = queries[s: s + _LOOKUP_CHUNK]
            idx = np.searchsorted(self.keys, q)
            idx_c = np.clip(idx, 0, self.keys.size - 1)
            found = self.keys[idx_c] == q
            out[s: s + _LOOKUP_CHUNK] = np.where(found, self.vals[idx_c], 0)
        return out


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
        tokens = _as_token_array(train_tokens)
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
        tokens = _as_token_array(tokens)
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

    def log_probs_at(self, tokens: np.ndarray, positions: np.ndarray) -> np.ndarray:
        """Log-probs at SELECTED positions (each ``>= CE_WARMUP``).

        Bit-identical to ``log_probs(tokens)[positions - CE_WARMUP]``: every
        per-position operation (context-code gather, count lookup, the
        ``log((c+alpha)/(C+alpha*V))`` float arithmetic) is elementwise
        independent, so restricting to a position subset never changes any
        value. Used by ``surrogate_cross_entropy`` to recompute only the
        few positions a block shuffle actually disturbs.
        """
        if self._pair is None or self._ctx is None:
            raise MarkovError("fit() before log_probs_at()")
        tokens = _as_token_array(tokens)
        _check_tokens(tokens, self.vocab_size)
        pos = np.asarray(positions, dtype=np.int64)
        if pos.size and (int(pos.min()) < CE_WARMUP or int(pos.max()) >= tokens.size):
            raise MarkovError("positions must be in [CE_WARMUP, n)")
        V = self.vocab_size
        ctx = _context_codes_at(tokens, self.order, V, pos)
        nxt = tokens[pos].astype(np.int64)
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
        tokens = _as_token_array(train_tokens)
        _check_tokens(tokens, self.vocab_size)
        self._pair, self._ctx = [], []
        for k in range(self.max_order + 1):
            p, c = _fit_order_counts(tokens, k, self.vocab_size)
            self._pair.append(p)
            self._ctx.append(c)
        return self

    def fit_from_counts(
        self,
        pair: list[_SortedCounts],
        ctx: list[_SortedCounts],
    ) -> "InterpolatedMarkov":
        """Adopt per-order count tables fitted elsewhere (SHARED, not copied).

        Bit-identical to ``fit(tokens)`` iff the tables are the
        ``_fit_order_counts(tokens, k, vocab_size)`` results for
        k = 0..max_order on the same stream — ``fit`` computes exactly those
        tables. Used by ``fit_all_baselines`` so the interpolated model
        re-uses the fixed-order models' tables instead of holding a second,
        duplicate copy (halves baseline RAM on multi-hundred-M-token folds).
        """
        if len(pair) != self.max_order + 1 or len(ctx) != self.max_order + 1:
            raise MarkovError(
                f"fit_from_counts needs {self.max_order + 1} pair/ctx tables, "
                f"got {len(pair)}/{len(ctx)}"
            )
        self._pair = list(pair)
        self._ctx = list(ctx)
        return self

    def log_probs(self, tokens: np.ndarray) -> np.ndarray:
        """Natural-log probabilities for positions ``CE_WARMUP..n-1``."""
        if not self._pair:
            raise MarkovError("fit() before log_probs()")
        tokens = _as_token_array(tokens)
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

    def log_probs_at(self, tokens: np.ndarray, positions: np.ndarray) -> np.ndarray:
        """Log-probs at SELECTED positions (each ``>= CE_WARMUP``).

        Bit-identical to ``log_probs(tokens)[positions - CE_WARMUP]`` — the
        backoff recursion is elementwise over positions (per-order lookups,
        the ``(num + beta*p)/(den + beta)`` update and the final ``log`` are
        all per-element float ops), so a position subset yields the exact
        same values as the full pass restricted to that subset.
        """
        if not self._pair:
            raise MarkovError("fit() before log_probs_at()")
        tokens = _as_token_array(tokens)
        _check_tokens(tokens, self.vocab_size)
        pos = np.asarray(positions, dtype=np.int64)
        if pos.size and (int(pos.min()) < CE_WARMUP or int(pos.max()) >= tokens.size):
            raise MarkovError("positions must be in [CE_WARMUP, n)")
        V = self.vocab_size
        beta = self.beta
        nxt = tokens[pos].astype(np.int64)
        p = np.full(pos.size, 1.0 / V, dtype=np.float64)  # base case p_{-1}
        for k in range(self.max_order + 1):
            ctx = _context_codes_at(tokens, k, V, pos)
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

    Memory note: the interpolated model SHARES the fixed-order models'
    count tables via ``fit_from_counts`` (bit-identical to an independent
    ``fit`` on the same stream — see there) instead of re-fitting a
    duplicate set, which would double the baseline arm's resident RAM.
    """
    tokens = _as_token_array(train_tokens)
    models: dict[str, MarkovKT | InterpolatedMarkov] = {}
    for k in range(MAX_ORDER + 1):
        models[f"kt_k{k}"] = MarkovKT(order=k, vocab_size=vocab_size).fit(tokens)
    interp = InterpolatedMarkov(max_order=MAX_ORDER, vocab_size=vocab_size)
    _check_tokens(tokens, vocab_size)  # same validation fit() would run
    interp.fit_from_counts(
        [models[f"kt_k{k}"]._pair for k in range(MAX_ORDER + 1)],
        [models[f"kt_k{k}"]._ctx for k in range(MAX_ORDER + 1)],
    )
    models[f"interp_k{MAX_ORDER}"] = interp
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


def surrogate_cross_entropy(
    model: MarkovKT | InterpolatedMarkov,
    surr_tokens: np.ndarray,
    src: np.ndarray,
    base_log_probs: np.ndarray,
) -> float:
    """CE of a permutation surrogate via log-prob REUSE — bit-identical.

    ``surr_tokens`` must be ``original[src]`` for the SAME original stream
    on which ``base_log_probs = model.log_probs(original)`` was computed
    once per fold. Key observation for the registered block-shuffle null
    (block length 256 >> max order 4): a Markov log-prob at position ``t``
    depends only on the ``(CE_WARMUP+1)``-gram ``surr[t-CE_WARMUP .. t]``.
    Wherever the shuffle maps that whole window contiguously
    (``src[t-j] == src[t]-j`` for j=1..CE_WARMUP — everywhere except the
    first CE_WARMUP positions after a block/hour seam, ~4 of every 256
    positions), the value is EXACTLY ``base_log_probs[src[t]-CE_WARMUP]``;
    only the seam positions are recomputed via ``log_probs_at`` (same
    elementwise arithmetic — see there).

    Bit-identity to the direct path ``model.cross_entropy(surr_tokens)``:
    the assembled per-position array equals ``model.log_probs(surr_tokens)``
    element for element (reused entries by the contiguity argument above,
    recomputed entries by ``log_probs_at``'s elementwise identity), and the
    final ``-np.mean`` runs over the same float64 array in the same stream
    order — identical pairwise summation, identical bits. Regression test:
    ``test_markov_surrogate_fastpath_equals_direct`` asserts exact equality.

    Cost: O(n) gather + O(n/block_len * CE_WARMUP) lookups instead of O(n)
    lookups per surrogate — the ~200-surrogate Markov arm drops from
    minutes to seconds per surrogate on ~30M-token folds.
    """
    surr = _as_token_array(surr_tokens)
    src = np.asarray(src, dtype=np.int64)
    if surr.size != src.size:
        raise MarkovError("surr_tokens and src must share length")
    n = src.size
    if n <= CE_WARMUP:
        return float("nan")
    if base_log_probs.size != n - CE_WARMUP:
        raise MarkovError(
            f"base_log_probs has {base_log_probs.size} entries, "
            f"expected {n - CE_WARMUP}"
        )
    # contig[t]: surrogate position t continues the SAME original run as t-1.
    contig = np.empty(n, dtype=bool)
    contig[0] = False
    contig[1:] = src[1:] == src[:-1] + 1
    # clean[i] (position t = i + CE_WARMUP): the whole context window
    # src[t-CE_WARMUP..t] maps contiguously -> src[t] >= CE_WARMUP holds
    # automatically (src[t] = src[t-CE_WARMUP] + CE_WARMUP >= CE_WARMUP).
    clean = contig[CE_WARMUP:]
    for j in range(1, CE_WARMUP):
        clean = clean & contig[CE_WARMUP - j: n - j]
    lp = np.empty(n - CE_WARMUP, dtype=np.float64)
    lp[clean] = base_log_probs[src[CE_WARMUP:][clean] - CE_WARMUP]
    dirty = np.nonzero(~clean)[0]
    if dirty.size:
        lp[dirty] = model.log_probs_at(surr, dirty + CE_WARMUP)
    return float(-np.mean(lp))


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
    "surrogate_cross_entropy",
]
