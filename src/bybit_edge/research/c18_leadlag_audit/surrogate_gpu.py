"""Surrogate generation as tensor batches for the H-18 resolution audit.

VERDICT-CARRYING NULL (byte-identical to GL-006): the circular block shift of
the source series, exactly as in ``c17_c41_lead_lag.surrogate._circular_shift``.
The random shift OFFSETS are always drawn on the CPU with the SAME sequential
``np.random.default_rng(seed).integers(lo, hi)`` consumption as the original
serial loop, so at equal ``n_surrogates`` the surrogate ensemble is
bit-identical to the original pipeline regardless of the compute backend
(numpy / torch-cpu / torch-cuda). Only the *statistic evaluation* over the
ensemble is batched.

REGISTRY-NAMED GPU PRIMITIVES (H-18 Methodik): phase-shuffle surrogates via
``rfft``/``irfft`` with randomised phases (amplitude spectrum preserved) and
permutation surrogates via argsort of uniform random keys. These are provided
as DIAGNOSTIC generators only — they are NOT the GL-006 null and are never
verdict-carrying for the audit (using them for T1/T2 would break the
byte-identical-pipeline clause of registry H-18).

The module imports WITHOUT torch (honest numpy degradation); torch is loaded
lazily and only when a torch backend is requested/available.

KAPITALFREI: no tradability logic anywhere here.
"""
from __future__ import annotations

import numpy as np

# Same constant as the original module — re-exported from there so the two
# pipelines can never drift apart silently.
from bybit_edge.research.c17_c41_lead_lag.surrogate import MIN_SHIFT_FRACTION

#: Backends in "honesty order". ``torch-cuda`` is the only backend on which a
#: full-resolution (>= 100k surrogates) run may carry the audit claims.
BACKENDS = ("torch-cuda", "torch-cpu", "numpy")


def _try_import_torch():
    """Return the torch module or ``None`` (import must never hard-fail)."""
    try:
        import torch  # noqa: PLC0415

        return torch
    except Exception:  # pragma: no cover - depends on environment
        return None


def torch_cuda_available() -> bool:
    """True iff torch is importable AND reports a usable CUDA device."""
    torch = _try_import_torch()
    if torch is None:
        return False
    try:
        return bool(torch.cuda.is_available())
    except Exception:  # pragma: no cover - driver-level breakage
        return False


def resolve_backend(requested: str = "auto") -> str:
    """Resolve ``requested`` in {auto, cuda, cpu, numpy} to an actual backend.

    ``auto`` -> torch-cuda > torch-cpu > numpy (best available, honestly
    degraded). ``cuda``/``cpu`` demand torch and raise ``RuntimeError`` when
    it (or the CUDA device) is missing — no silent downgrade of an explicit
    request.
    """
    req = (requested or "auto").lower()
    torch = _try_import_torch()
    if req == "numpy":
        return "numpy"
    if req == "cuda":
        if torch is None:
            raise RuntimeError("backend 'cuda' angefordert, aber torch fehlt")
        if not torch_cuda_available():
            raise RuntimeError("backend 'cuda' angefordert, aber kein CUDA-Device verfuegbar")
        return "torch-cuda"
    if req == "cpu":
        if torch is None:
            raise RuntimeError("backend 'cpu' (torch) angefordert, aber torch fehlt")
        return "torch-cpu"
    if req != "auto":
        raise RuntimeError(f"unbekanntes backend '{requested}' (auto|cuda|cpu|numpy)")
    if torch is None:
        return "numpy"
    return "torch-cuda" if torch_cuda_available() else "torch-cpu"


def backend_device(backend: str):
    """Return ``(torch_module_or_None, device_str_or_None)`` for a backend."""
    if backend == "numpy":
        return None, None
    torch = _try_import_torch()
    if torch is None:
        raise RuntimeError(f"backend '{backend}' braucht torch, das nicht importierbar ist")
    return torch, ("cuda" if backend == "torch-cuda" else "cpu")


# ---------------------------------------------------------------------------
# Verdict-carrying null: circular shift, EXACT original RNG consumption
# ---------------------------------------------------------------------------

def generate_shift_offsets(n: int, n_surrogates: int, seed: int) -> np.ndarray:
    """Draw the circular-shift offsets EXACTLY like the original serial loop.

    The original ``surrogate_test_te``/``surrogate_test_wcoh`` create
    ``rng = np.random.default_rng(seed)`` and call
    ``int(rng.integers(lo, hi))`` once per surrogate inside
    ``_circular_shift`` (with ``lo = max(1, int(MIN_SHIFT_FRACTION*n))``,
    ``hi = n - lo``); when ``hi <= lo`` (degenerate tiny series) NO random
    number is consumed and the roll is ``max(1, n // 2)``. This function
    replicates that consumption call-by-call (a deliberate Python loop — a
    vectorised ``rng.integers(lo, hi, size=N)`` is NOT guaranteed to be
    stream-identical to N sequential draws), so at equal N the offsets are
    bit-identical to the original pipeline.
    """
    lo = max(1, int(MIN_SHIFT_FRACTION * n))
    hi = n - lo
    if hi <= lo:
        return np.full(n_surrogates, max(1, n // 2), dtype=np.int64)
    rng = np.random.default_rng(seed)
    return np.array(
        [int(rng.integers(lo, hi)) for _ in range(n_surrogates)], dtype=np.int64
    )


def batch_circular_shift(x: np.ndarray, offsets: np.ndarray, *, backend: str = "numpy"):
    """Batched ``np.roll``: row ``i`` equals ``np.roll(x, offsets[i])``.

    ``np.roll(x, s)[t] == x[(t - s) % n]`` — implemented as a gather so it
    maps 1:1 onto GPU tensor indexing. Returns a ``(B, n)`` array/tensor on
    the requested backend (float64 either way).
    """
    x = np.asarray(x, dtype=np.float64)
    offsets = np.asarray(offsets, dtype=np.int64)
    n = x.size
    if backend == "numpy":
        idx = (np.arange(n, dtype=np.int64)[None, :] - offsets[:, None]) % n
        return x[idx]
    torch, device = backend_device(backend)
    xt = torch.as_tensor(x, dtype=torch.float64, device=device)
    off = torch.as_tensor(offsets, dtype=torch.int64, device=device)
    idx = (torch.arange(n, dtype=torch.int64, device=device)[None, :] - off[:, None]) % n
    return xt[idx]


# ---------------------------------------------------------------------------
# Registry-named DIAGNOSTIC generators (NOT the GL-006 null — never
# verdict-carrying; see module docstring)
# ---------------------------------------------------------------------------

def phase_shuffle_surrogates(
    x: np.ndarray, n_surrogates: int, seed: int, *, backend: str = "numpy"
) -> np.ndarray:
    """Phase-randomised surrogates via ``rfft``/``irfft`` (registry H-18).

    Each surrogate keeps the EXACT amplitude spectrum of ``x`` and replaces
    the phases of all strictly-positive, non-Nyquist frequencies with iid
    Uniform[0, 2*pi) draws (DC — and Nyquist for even n — stay real, as
    required for a real-valued inverse). Diagnostic generator only.
    Returns a ``(B, n)`` float64 numpy array (torch backends compute on
    device and transfer back — the caller-facing contract stays numpy).
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    rng = np.random.default_rng(seed)
    n_freq = n // 2 + 1
    # Random phases on CPU for cross-backend determinism at equal seed.
    phases = rng.uniform(0.0, 2.0 * np.pi, size=(n_surrogates, n_freq))
    phases[:, 0] = 0.0                    # DC stays real/untouched
    if n % 2 == 0:
        phases[:, -1] = 0.0               # Nyquist stays real for even n
    if backend == "numpy":
        spec = np.fft.rfft(x)
        amp = np.abs(spec)
        surr_spec = amp[None, :] * np.exp(1j * phases)
        # Keep the original DC/Nyquist coefficients exactly (sign included).
        surr_spec[:, 0] = spec[0]
        if n % 2 == 0:
            surr_spec[:, -1] = spec[-1]
        return np.fft.irfft(surr_spec, n=n, axis=1)
    torch, device = backend_device(backend)
    xt = torch.as_tensor(x, dtype=torch.float64, device=device)
    spec = torch.fft.rfft(xt)
    amp = torch.abs(spec)
    ph = torch.as_tensor(phases, dtype=torch.float64, device=device)
    surr_spec = amp[None, :] * torch.exp(1j * ph)
    surr_spec[:, 0] = spec[0]
    if n % 2 == 0:
        surr_spec[:, -1] = spec[-1]
    out = torch.fft.irfft(surr_spec, n=n, dim=1)
    return out.cpu().numpy()


def permutation_surrogates(
    x: np.ndarray, n_surrogates: int, seed: int, *, backend: str = "numpy"
) -> np.ndarray:
    """Permutation surrogates via argsort of uniform random keys (registry).

    Destroys ALL temporal structure while preserving the marginal exactly.
    Diagnostic generator only (the GL-006 null preserves autocorrelation via
    circular shift — a permutation null is deliberately harsher and would be
    a methodology change). Returns ``(B, n)`` float64 numpy array.
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.size
    rng = np.random.default_rng(seed)
    keys = rng.uniform(0.0, 1.0, size=(n_surrogates, n))
    if backend == "numpy":
        order = np.argsort(keys, axis=1)
        return x[order]
    torch, device = backend_device(backend)
    kt = torch.as_tensor(keys, dtype=torch.float64, device=device)
    xt = torch.as_tensor(x, dtype=torch.float64, device=device)
    order = torch.argsort(kt, dim=1)
    return xt[order].cpu().numpy()
