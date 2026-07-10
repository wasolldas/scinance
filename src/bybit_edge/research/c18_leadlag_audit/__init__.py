"""H-18 · GL-006/H-04 lead-lag high-N surrogate RESOLUTION AUDIT (Welle 5).

This package re-executes the byte-identical, already-adjudicated F-LEADLAG
pipeline from GL-006 (H-04, WEITER kapitalfrei) with EXACTLY ONE pre-declared
change: ``n_surrogates`` 200 -> 100_000 (registry H-18). It is NOT a new
hypothesis about the world and it NEVER changes the GL-006 verdict — any
drifting result only marks the standing Messungen-WEITER as
"aufloesungsbedingt fragil" (audit finding). This package does NOT write
``gate_log.md``; a new, separate GL entry (GL-014ff.) is created manually by
the gate-auditor from the payload/report produced here.

KAPITALFREI: identical to GL-006 — pure measurement-existence audit, no
tradability logic anywhere (H-04b stays the separate, PARK-adjudicated
follow-up).

Modules:

* ``surrogate_gpu``  — surrogate generation as tensor batches (torch when
  available, honest numpy fallback): circular-shift offsets with the EXACT
  RNG consumption of the original ``c17_c41_lead_lag.surrogate`` module
  (verdict-carrying null), plus the registry-named phase-shuffle
  (``rfft``/``irfft``) and argsort-permutation primitives (diagnostic only).
* ``te_batched``     — batched Shannon Transfer Entropy via batched 3D
  histograms (scatter_add on torch, bincount on numpy).
* ``wcoh_batched``   — batched Morlet CWT wavelet-coherence phase-lead via
  FFT convolution.
* ``stats``          — GL-006 baseline constants, MC standard error, and the
  pre-registered partial claims T1 / T2.
* ``driver``         — orchestration, payload + German Markdown report,
  self-test (equivalence against the original pipeline).
"""
from __future__ import annotations

from .driver import (  # noqa: F401
    AUDIT_ID,
    BASE_GATE,
    GL006_SPAN_MS,
    gpu_status,
    run,
    run_equivalence_selftest,
    write_outputs,
)
from .stats import (  # noqa: F401
    GL006_BASELINE,
    STAGE1_SURVIVORS,
    T2_CELLS,
    evaluate_t1,
    evaluate_t2,
    mc_standard_error,
)
from .surrogate_gpu import (  # noqa: F401
    batch_circular_shift,
    generate_shift_offsets,
    permutation_surrogates,
    phase_shuffle_surrogates,
    resolve_backend,
)
from .te_batched import surrogate_test_te_batched, transfer_entropy_batch  # noqa: F401
from .wcoh_batched import (  # noqa: F401
    surrogate_test_wcoh_batched,
    wavelet_coherence_lead_batch,
)
