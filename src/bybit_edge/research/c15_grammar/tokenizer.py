"""Trade-tape event tokenizer for the H-15 grammar gate (KAPITALFREI).

Registry H-15 (``scinance2-impl/state/hypothesis_registry.md``, Methodik,
pre-fixed): tokenisation = Side (2) x Signed-Size-Quantil-Bucket (8, fitted
ON THE TRAIN FOLD ONLY) x Log-Inter-Arrival-Bucket (8) = vocab 128
(optionally x Tick-Direction -> 256; the registered BASE vocabulary is 128,
tick direction is OFF by default and only reported as a variant if enabled).

Leak discipline (registry "Selbstkill-/Restrisiko"): the quantile bucket
boundaries are fitted EXCLUSIVELY on train-fold events — ``fit_tokenizer``
takes train-fold feature arrays only and ``tokenize`` never re-estimates
anything. Feeding test-fold data into ``fit_tokenizer`` would be a leak; the
driver's ``prepare_fold`` enforces the split and the unit tests assert that
perturbing test-fold data cannot move the boundaries.

Token layout (deterministic, documented):
    token = side * (S * I) + size_bucket * I + iat_bucket            (vocab 128)
    token = tick_dir * 128 + side * 64 + size_bucket * 8 + iat_bucket (vocab 256)
with side in {0=Sell, 1=Buy}, S = 8 signed-size buckets, I = 8 log-IAT
buckets, tick_dir in {0=down/flat-carry, 1=up}.

Feature definitions (causal, per-event):
  * signed size   = trade size * (+1 for taker Buy, -1 for taker Sell).
  * log IAT       = log1p(inter-arrival time in ms to the PREVIOUS event);
                    the first event of a stream gets IAT 0 (documented edge).
  * tick direction= sign of the last non-zero trade-to-trade price change,
                    carried forward over zero-changes; the first event is
                    assigned "up" (deterministic convention). Strictly causal
                    (uses only past prices).

KAPITALFREI: pure representation code. numpy only — no torch anywhere here.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

#: Registered bucket counts (registry H-15, pre-fixed — NOT tunable post hoc).
N_SIZE_BUCKETS = 8
N_IAT_BUCKETS = 8
N_SIDES = 2

#: Registered base vocabulary (2 x 8 x 8).
VOCAB_BASE = N_SIDES * N_SIZE_BUCKETS * N_IAT_BUCKETS  # 128

#: Optional tick-direction extension (registry: "optional x Tick-Direction").
VOCAB_TICKDIR = 2 * VOCAB_BASE  # 256


class TokenizerError(ValueError):
    """Raised on malformed tokenizer inputs."""


@dataclass(frozen=True)
class TokenizerSpec:
    """Frozen, train-fold-fitted bucket boundaries.

    ``size_edges`` / ``iat_edges`` are the 7 interior quantile boundaries
    (quantiles 1/8..7/8) of the TRAIN-fold signed-size / log-IAT
    distributions. Bucket index = ``np.searchsorted(edges, x, side="right")``
    which maps x into 0..7. The spec is immutable — tokenising test data can
    never update it.
    """

    size_edges: tuple[float, ...]
    iat_edges: tuple[float, ...]
    use_tick_direction: bool = False
    n_train_events: int = 0
    vocab_size: int = field(default=VOCAB_BASE)

    def __post_init__(self) -> None:
        if len(self.size_edges) != N_SIZE_BUCKETS - 1:
            raise TokenizerError(
                f"size_edges needs {N_SIZE_BUCKETS - 1} boundaries, got {len(self.size_edges)}"
            )
        if len(self.iat_edges) != N_IAT_BUCKETS - 1:
            raise TokenizerError(
                f"iat_edges needs {N_IAT_BUCKETS - 1} boundaries, got {len(self.iat_edges)}"
            )
        expected = VOCAB_TICKDIR if self.use_tick_direction else VOCAB_BASE
        object.__setattr__(self, "vocab_size", expected)


def derive_event_features(
    ts_ms: np.ndarray,
    price: np.ndarray,
    size: np.ndarray,
    side: np.ndarray,
) -> dict[str, np.ndarray]:
    """Derive the per-event tokenizer features from a raw trade stream.

    ``ts_ms``: exchange timestamps (ms, non-decreasing); ``price`` > 0;
    ``size`` > 0; ``side``: int array with 1 = taker Buy, 0 = taker Sell.
    Returns ``signed_size``, ``log_iat``, ``tick_dir`` and pass-through
    ``side`` — all strictly causal (position t uses only data at <= t).
    """
    ts = np.asarray(ts_ms, dtype=np.int64)
    px = np.asarray(price, dtype=np.float64)
    sz = np.asarray(size, dtype=np.float64)
    sd = np.asarray(side, dtype=np.int64)
    n = ts.size
    if not (px.size == n and sz.size == n and sd.size == n):
        raise TokenizerError("ts/price/size/side length mismatch")
    if n == 0:
        raise TokenizerError("empty event stream")
    if np.any(np.diff(ts) < 0):
        raise TokenizerError("timestamps must be non-decreasing")
    if not np.all((sd == 0) | (sd == 1)):
        raise TokenizerError("side must be 0 (Sell) or 1 (Buy)")

    signed_size = np.where(sd == 1, sz, -sz)

    iat = np.zeros(n, dtype=np.float64)
    if n > 1:
        iat[1:] = (ts[1:] - ts[:-1]).astype(np.float64)
    log_iat = np.log1p(iat)

    # Tick direction: sign of last non-zero price change, carried forward.
    tick_dir = np.ones(n, dtype=np.int64)  # first event: "up" by convention
    if n > 1:
        dpx = np.sign(np.diff(px))  # -1 / 0 / +1
        # carry forward the last non-zero sign (vectorised forward-fill)
        raw = dpx.copy()
        nz = raw != 0
        idx = np.where(nz, np.arange(1, n), 0)
        idx = np.maximum.accumulate(idx)
        filled = np.where(idx > 0, np.sign(px[idx] - px[idx - 1]), 1.0)
        tick_dir[1:] = (filled > 0).astype(np.int64)
    return {
        "signed_size": signed_size,
        "log_iat": log_iat,
        "tick_dir": tick_dir,
        "side": sd,
    }


def fit_tokenizer(
    train_signed_size: np.ndarray,
    train_log_iat: np.ndarray,
    *,
    use_tick_direction: bool = False,
) -> TokenizerSpec:
    """Fit quantile bucket boundaries on TRAIN-FOLD features ONLY.

    The caller MUST pass train-fold arrays exclusively (leak discipline,
    registry H-15). Boundaries are the 7 interior quantiles (1/8..7/8) of
    each feature; degenerate distributions (fewer distinct values than
    buckets) still yield valid, monotone-non-decreasing edges via
    ``np.quantile`` (buckets then simply stay unused — honest degradation,
    never a crash).
    """
    ssz = np.asarray(train_signed_size, dtype=np.float64)
    lia = np.asarray(train_log_iat, dtype=np.float64)
    if ssz.size == 0 or lia.size == 0:
        raise TokenizerError("cannot fit tokenizer on an empty train fold")
    if not (np.all(np.isfinite(ssz)) and np.all(np.isfinite(lia))):
        raise TokenizerError("non-finite feature values in train fold")
    qs = np.arange(1, N_SIZE_BUCKETS) / N_SIZE_BUCKETS  # 1/8 .. 7/8
    size_edges = tuple(float(v) for v in np.quantile(ssz, qs))
    iat_edges = tuple(float(v) for v in np.quantile(lia, qs))
    return TokenizerSpec(
        size_edges=size_edges,
        iat_edges=iat_edges,
        use_tick_direction=bool(use_tick_direction),
        n_train_events=int(ssz.size),
    )


def tokenize(
    spec: TokenizerSpec,
    side: np.ndarray,
    signed_size: np.ndarray,
    log_iat: np.ndarray,
    tick_dir: np.ndarray | None = None,
) -> np.ndarray:
    """Map events to token ids using a FROZEN spec (no re-fitting, ever).

    Returns int64 tokens in ``[0, spec.vocab_size)``. ``tick_dir`` is
    required iff ``spec.use_tick_direction``.
    """
    sd = np.asarray(side, dtype=np.int64)
    ssz = np.asarray(signed_size, dtype=np.float64)
    lia = np.asarray(log_iat, dtype=np.float64)
    if not (sd.size == ssz.size == lia.size):
        raise TokenizerError("side/signed_size/log_iat length mismatch")
    if not np.all((sd == 0) | (sd == 1)):
        raise TokenizerError("side must be 0 or 1")
    size_b = np.searchsorted(np.asarray(spec.size_edges), ssz, side="right")
    iat_b = np.searchsorted(np.asarray(spec.iat_edges), lia, side="right")
    size_b = np.clip(size_b, 0, N_SIZE_BUCKETS - 1)
    iat_b = np.clip(iat_b, 0, N_IAT_BUCKETS - 1)
    tokens = sd * (N_SIZE_BUCKETS * N_IAT_BUCKETS) + size_b * N_IAT_BUCKETS + iat_b
    if spec.use_tick_direction:
        if tick_dir is None:
            raise TokenizerError("spec.use_tick_direction=True needs tick_dir")
        td = np.asarray(tick_dir, dtype=np.int64)
        if td.size != sd.size:
            raise TokenizerError("tick_dir length mismatch")
        if not np.all((td == 0) | (td == 1)):
            raise TokenizerError("tick_dir must be 0 or 1")
        tokens = td * VOCAB_BASE + tokens
    return tokens.astype(np.int64)


def decompose_token(spec: TokenizerSpec, token: int) -> dict[str, int]:
    """Inverse of the token layout (for tests / diagnostics)."""
    t = int(token)
    if not 0 <= t < spec.vocab_size:
        raise TokenizerError(f"token {t} outside vocab {spec.vocab_size}")
    out: dict[str, int] = {}
    if spec.use_tick_direction:
        out["tick_dir"] = t // VOCAB_BASE
        t = t % VOCAB_BASE
    out["side"] = t // (N_SIZE_BUCKETS * N_IAT_BUCKETS)
    rem = t % (N_SIZE_BUCKETS * N_IAT_BUCKETS)
    out["size_bucket"] = rem // N_IAT_BUCKETS
    out["iat_bucket"] = rem % N_IAT_BUCKETS
    return out


__all__ = [
    "N_IAT_BUCKETS",
    "N_SIDES",
    "N_SIZE_BUCKETS",
    "TokenizerError",
    "TokenizerSpec",
    "VOCAB_BASE",
    "VOCAB_TICKDIR",
    "decompose_token",
    "derive_event_features",
    "fit_tokenizer",
    "tokenize",
]
