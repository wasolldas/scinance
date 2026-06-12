"""
WP-3-VERIFY (T0, SANDBOX) — tests for the C-31 cyclostationary CFAR module.

Covers ``src/bybit_edge/research/c31_cfar/`` (H-03, registry:
``scinance2-impl/state/hypothesis_registry.md``):

1. False-positive control (the most important test): pure Poisson
   inter-arrivals must NOT yield a significant surrogate p — parametrised
   over three seeds so a lucky seed cannot carry the suite.
2. Detection power: Poisson background + injected 100 ms periodicity
   (alpha = 10 Hz) -> surrogate p < 0.05 and a CFAR peak near 10 Hz.
3. No-Lookahead (forensic discipline): (a) mutating/appending FUTURE ticks
   never changes a past phase estimate; (b) a constructed lookahead case
   (negative forward horizon => forward return read from the past) raises
   ``LookaheadError``.
4. CA-CFAR mechanics: a known synthetic SCD peak is found exactly;
   threshold-factor monotonicity (higher factor -> fewer peaks).
5. Surrogate-p exactness ((#>=SNR + 1)/(N + 1)) and BH-FDR rejection sets
   on hand-computed p-families.
6. Window disjointness of the driver split (chronological, no overlap).
7. Driver E2E on a mini tick-CSV fixture -> JSON + MD report with the H-03
   reference and every gate criterion (p, lead, edge) per window.
8. Determinism: same seed -> identical JSON payload (registry
   reproducibility duty).

Runtime budget: surrogate N is kept small (50 for the statistical tests,
20 for the driver E2E); seeds are fixed; everything is T0/SANDBOX. The
binding H-03 run on real ticks is T3 (handoff_local), not this file.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pytest

import scripts.c31_cfar as c31_cli
from bybit_edge.research.c31_cfar import (
    CfarConfig,
    CyclicSpectrum,
    DataError,
    LookaheadError,
    benjamini_hochberg,
    detect_peaks,
    measure_lead_edge,
    run,
    split_windows,
    surrogate_test,
)
from bybit_edge.research.c31_cfar import surrogate as surrogate_mod
from bybit_edge.research.c31_cfar.lead_edge import _phase_at

T0_MS = 1_700_000_000_000.0  # fixed epoch anchor for all synthetic timelines

# Detection-power tolerance (documented): the alpha grid is
# linspace(0, fs/4, n_alpha) = linspace(0, 25 Hz, 26) -> 1.0 Hz spacing, and
# the FFT bin width is fs / segment_len = 100 / 100 = 1.0 Hz. The injected
# cyclic frequency can therefore be located no better than +- 1 grid step.
ALPHA_TOL_HZ = 1.0
INJECTED_PERIOD_MS = 100.0
INJECTED_ALPHA_HZ = 1000.0 / INJECTED_PERIOD_MS  # 10 Hz


# ---------------------------------------------------------------------------
# Synthetic timelines
# ---------------------------------------------------------------------------

def _poisson_ts(seed: int, n: int = 2500, mean_gap_ms: float = 20.0) -> np.ndarray:
    """Pure Poisson process: exponential inter-arrivals, no cyclic structure."""
    rng = np.random.default_rng(seed)
    return T0_MS + np.cumsum(rng.exponential(mean_gap_ms, size=n))


def _cyclic_ts(
    seed: int,
    duration_ms: float = 60_000.0,
    period_ms: float = INJECTED_PERIOD_MS,
    jitter_ms: float = 2.0,
    n_poisson: int = 600,
) -> np.ndarray:
    """Poisson background + injected periodic train (a TWAP-bot footprint)."""
    rng = np.random.default_rng(seed)
    k = np.arange(int(duration_ms // period_ms))
    periodic = T0_MS + k * period_ms + rng.normal(0.0, jitter_ms, size=k.size)
    background = T0_MS + np.sort(rng.uniform(0.0, duration_ms, size=n_poisson))
    return np.sort(np.concatenate([periodic, background]))


def _ticks_with_prices(
    seed: int, n: int = 1200, span_ms: float = 60_000.0
) -> tuple[np.ndarray, np.ndarray]:
    """Random tick timeline + random-walk prices (for lead/edge + driver)."""
    rng = np.random.default_rng(seed)
    ts = T0_MS + np.sort(rng.uniform(0.0, span_ms, size=n))
    px = 50_000.0 * np.exp(np.cumsum(rng.normal(0.0, 1e-4, size=n)))
    return ts, px


# ---------------------------------------------------------------------------
# 1. False-positive control (most important): Poisson must stay null
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("seed", [7, 23, 1337])
def test_false_positive_control_poisson_not_significant(seed: int) -> None:
    """Pure Poisson inter-arrivals must NOT pass the surrogate gate (p > 0.05).

    This is the H-03 falsification anchor: if the pipeline manufactured
    significance out of structureless noise, every downstream gate number
    would be worthless. Three fixed seeds so no single lucky draw decides.
    """
    ts = _poisson_ts(seed)
    result = surrogate_test(
        ts,
        bin_dt_ms=10.0,
        cfar=CfarConfig(threshold_factor=6.0),
        n_surrogates=50,
        seed=seed,
        segment_len=128,
        n_alpha=32,
    )
    assert result.n_surrogates == 50
    assert result.p_value > 0.05, (
        f"false positive on pure Poisson (seed={seed}): p={result.p_value}"
    )


# ---------------------------------------------------------------------------
# 2. Detection power: injected 100 ms periodicity must be found
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("seed", [7, 23, 1337])
def test_detection_power_injected_100ms_periodicity(seed: int) -> None:
    """Poisson + injected 100 ms cycle -> p < 0.05 and a peak near 10 Hz.

    Grid-aligned spectral parameters (bin 10 ms -> fs 100 Hz, segment 100 ->
    df 1 Hz, n_alpha 26 -> alpha step 1 Hz) so 10 Hz sits exactly on both
    grids; ``min_alpha_hz=2.0`` excludes the adjacent-FFT-bin leakage band
    (alpha < 2*df) that is an estimator artefact, not bot cadence.
    Tolerance: +- ALPHA_TOL_HZ = 1 grid step (documented above). An impulse
    train carries harmonics, so the GLOBAL top peak may sit on a multiple of
    the injected alpha; the injected line itself must also be detected.
    """
    ts = _cyclic_ts(seed)
    cfar = CfarConfig(threshold_factor=6.0, min_alpha_hz=2.0)

    result = surrogate_test(
        ts,
        bin_dt_ms=10.0,
        cfar=cfar,
        n_surrogates=50,
        seed=seed,
        segment_len=100,
        n_alpha=26,
    )
    assert result.p_value < 0.05, (
        f"injected periodicity not significant (seed={seed}): p={result.p_value}"
    )

    from bybit_edge.research.c31_cfar import bin_counts, spectral_correlation_density

    counts, fs_hz = bin_counts(ts, 10.0)
    spectrum = spectral_correlation_density(counts, fs_hz, segment_len=100, n_alpha=26)
    peaks = detect_peaks(spectrum, cfar)
    assert peaks, f"no CFAR peaks on injected periodicity (seed={seed})"

    alphas_found = np.array([p.alpha_hz for p in peaks])
    assert np.any(np.abs(alphas_found - INJECTED_ALPHA_HZ) <= ALPHA_TOL_HZ), (
        f"no peak within {ALPHA_TOL_HZ} Hz of injected {INJECTED_ALPHA_HZ} Hz "
        f"(seed={seed}); found alphas: {sorted(set(np.round(alphas_found, 1)))}"
    )
    # Top peak must be the injected line or one of its harmonics.
    top_alpha = peaks[0].alpha_hz
    distance_to_harmonic = min(
        abs(top_alpha - k * INJECTED_ALPHA_HZ) for k in (1, 2, 3)
    )
    assert distance_to_harmonic <= ALPHA_TOL_HZ, (
        f"top peak at {top_alpha} Hz is not the injected line or a harmonic"
    )


# ---------------------------------------------------------------------------
# 3. No-Lookahead (forensic discipline)
# ---------------------------------------------------------------------------

def test_no_lookahead_future_tick_mutation_does_not_change_phase() -> None:
    """Mutating or appending FUTURE ticks must not alter a past phase estimate.

    The builder claims ``_phase_at`` only ever reads ticks with ``ts <= t``
    (closed past window). We verify the claim behaviourally: phases at several
    detection instants strictly between ticks are bit-identical after the
    entire future (ts > t) is shifted around and after extra future ticks are
    injected.
    """
    rng = np.random.default_rng(99)
    ts = T0_MS + np.cumsum(rng.exponential(20.0, size=400))
    alpha_hz = 10.0
    lookback_ms = 400.0

    # Detection instants strictly BETWEEN ticks -> non-trivial phases.
    instants = [float(ts[i]) + 7.3 for i in (120, 200, 310)]
    baseline = [_phase_at(ts, t, alpha_hz, lookback_ms) for t in instants]
    assert all(p is not None and p > 0.0 for p in baseline)

    for t in instants:
        # (i) shift every future tick by random positive offsets (stays future)
        mutated = ts.copy()
        future = mutated > t
        mutated[future] += rng.uniform(1.0, 500.0, size=int(future.sum()))
        mutated = np.sort(mutated)
        # (ii) additionally inject brand-new future ticks
        injected = np.sort(
            np.concatenate([mutated, t + rng.uniform(0.5, 300.0, size=50)])
        )
        expected = _phase_at(ts, t, alpha_hz, lookback_ms)
        assert _phase_at(mutated, t, alpha_hz, lookback_ms) == expected
        assert _phase_at(injected, t, alpha_hz, lookback_ms) == expected


def test_no_lookahead_constructed_case_raises_lookahead_error() -> None:
    """A constructed lookahead (negative forward horizon) raises LookaheadError.

    With ``forward_horizon_ms < 0`` the 'forward' return would be read from
    ticks BEFORE the detection instant — exactly the leak the re-validation in
    ``measure_lead_edge`` must catch instead of silently producing a phantom
    edge.
    """
    ts, px = _ticks_with_prices(seed=99, n=400, span_ms=8000.0)
    with pytest.raises(LookaheadError):
        measure_lead_edge(ts, px, alpha_hz=10.0, forward_horizon_ms=-50.0)


def test_lookahead_error_is_assertion_error_subclass() -> None:
    """LookaheadError must stay an AssertionError (forensic test contract)."""
    assert issubclass(LookaheadError, AssertionError)


# ---------------------------------------------------------------------------
# 4. CA-CFAR mechanics on synthetic SCD matrices
# ---------------------------------------------------------------------------

def _make_spectrum(scd: np.ndarray, fs_hz: float = 100.0) -> CyclicSpectrum:
    n_alpha, n_freq = scd.shape
    return CyclicSpectrum(
        scd=scd.astype(np.float64),
        alphas=np.linspace(0.0, fs_hz / 4.0, n_alpha),
        freqs=np.linspace(0.0, fs_hz / 2.0, n_freq),
        bin_dt_ms=1000.0 / fs_hz,
        n_bins=1024,
    )


def test_cfar_detects_exactly_the_known_peak() -> None:
    """Flat noise floor + one injected cell -> exactly that one detection."""
    scd = np.ones((16, 9), dtype=np.float64)
    peak_alpha_idx, peak_freq_idx, peak_value = 5, 3, 25.0
    scd[peak_alpha_idx, peak_freq_idx] = peak_value
    spectrum = _make_spectrum(scd)

    peaks = detect_peaks(spectrum, CfarConfig(threshold_factor=6.0))

    assert len(peaks) == 1, f"expected exactly 1 peak, got {len(peaks)}"
    peak = peaks[0]
    assert peak.alpha_idx == peak_alpha_idx
    assert peak.freq_idx == peak_freq_idx
    assert peak.alpha_hz == pytest.approx(float(spectrum.alphas[peak_alpha_idx]))
    assert peak.freq_hz == pytest.approx(float(spectrum.freqs[peak_freq_idx]))
    # Training cells around the CUT are all 1.0 -> noise floor 1.0, SNR 25.
    assert peak.noise_floor == pytest.approx(1.0)
    assert peak.snr == pytest.approx(peak_value)


def test_cfar_never_detects_in_alpha_zero_psd_row() -> None:
    """The alpha = 0 row is the plain PSD and must never produce detections."""
    scd = np.ones((16, 9), dtype=np.float64)
    scd[0, 4] = 1e6  # monster peak in the PSD row
    peaks = detect_peaks(_make_spectrum(scd), CfarConfig(threshold_factor=6.0))
    assert all(p.alpha_idx != 0 for p in peaks)
    assert len(peaks) == 0


def test_cfar_threshold_factor_monotonicity() -> None:
    """Higher threshold factor -> never more peaks (CFAR false-alarm knob)."""
    rng = np.random.default_rng(4242)
    scd = rng.exponential(1.0, size=(32, 17))
    # A few moderate bumps so low thresholds find plenty.
    for ai, fj in ((6, 4), (15, 9), (24, 13)):
        scd[ai, fj] *= 12.0
    spectrum = _make_spectrum(scd)

    counts = [
        len(detect_peaks(spectrum, CfarConfig(threshold_factor=t)))
        for t in (2.0, 4.0, 8.0)
    ]
    assert counts[0] >= counts[1] >= counts[2], f"not monotone: {counts}"
    assert counts[0] > counts[2], (
        f"degenerate fixture: same peak count at T=2 and T=8 ({counts})"
    )
    assert counts[0] > 0


# ---------------------------------------------------------------------------
# 5. Surrogate-p exactness + BH-FDR hand computations
# ---------------------------------------------------------------------------

def test_surrogate_p_value_exact_formula(monkeypatch: pytest.MonkeyPatch) -> None:
    """p must be exactly (#{surrogate >= observed} + 1) / (N + 1).

    The pipeline statistic is scripted: first call returns the observed SNR,
    the next N calls return a constructed surrogate SNR distribution. With
    observed 5.0 and surrogates [6, 4, 5, 1, 7, 2, 5, 0.5, 3, 8] exactly five
    are >= 5.0 (6, 5, 7, 5, 8) -> p = (5 + 1) / (10 + 1) = 6/11.
    """
    scripted = [5.0, 6.0, 4.0, 5.0, 1.0, 7.0, 2.0, 5.0, 0.5, 3.0, 8.0]
    calls: list[float] = []

    def fake_pipeline_top_snr(*args, **kwargs) -> float:
        calls.append(scripted[len(calls)])
        return calls[-1]

    monkeypatch.setattr(surrogate_mod, "_pipeline_top_snr", fake_pipeline_top_snr)

    ts = T0_MS + np.arange(16, dtype=np.float64) * 10.0  # >= 4 gaps required
    result = surrogate_test(
        ts, bin_dt_ms=10.0, cfar=CfarConfig(), n_surrogates=10, seed=1
    )

    assert len(calls) == 11  # 1 observed + 10 surrogates
    assert result.observed_snr == pytest.approx(5.0)
    assert result.p_value == pytest.approx(6.0 / 11.0)
    assert result.n_surrogates == 10


def test_surrogate_degenerate_input_returns_p_one() -> None:
    """Fewer than 4 gaps -> no test, p = 1.0 (never spuriously significant)."""
    ts = T0_MS + np.array([0.0, 10.0, 20.0])
    result = surrogate_test(ts, bin_dt_ms=10.0, cfar=CfarConfig(), n_surrogates=10)
    assert result.p_value == 1.0
    assert result.n_surrogates == 0


def test_benjamini_hochberg_hand_computed_rejections() -> None:
    """BH at alpha=0.10, m=4: thresholds k/m*alpha = .025/.05/.075/.10.

    p = [0.02, 0.5, 0.03, 0.9] sorted -> .02 <= .025 (k=1 ok), .03 <= .05
    (k=2 ok), .5 > .075, .9 > .10 -> k_max = 2: reject exactly {0.02, 0.03},
    p_crit = 0.03. Input order must be preserved in the output mask.
    """
    rejected, p_crit = benjamini_hochberg([0.02, 0.5, 0.03, 0.9], alpha=0.10)
    assert rejected == [True, False, True, False]
    assert p_crit == pytest.approx(0.03)


def test_benjamini_hochberg_step_up_property() -> None:
    """BH is step-UP: a failing low rank is rescued by a passing higher rank.

    alpha=0.10, m=3: thresholds .0333/.0667/.10. p = [0.04, 0.9, 0.045]:
    rank 1 (.04 > .0333) fails, rank 2 (.045 <= .0667) passes -> k_max = 2
    rejects BOTH 0.04 and 0.045.
    """
    rejected, p_crit = benjamini_hochberg([0.04, 0.9, 0.045], alpha=0.10)
    assert rejected == [True, False, True]
    assert p_crit == pytest.approx(0.045)


def test_benjamini_hochberg_edge_cases() -> None:
    """Empty family and an all-null family."""
    assert benjamini_hochberg([], alpha=0.10) == ([], 0.0)
    rejected, p_crit = benjamini_hochberg([0.5, 0.61], alpha=0.10)
    assert rejected == [False, False]
    assert p_crit == 0.0


# ---------------------------------------------------------------------------
# 6. Window disjointness (H-03: >= 2 disjoint chronological windows)
# ---------------------------------------------------------------------------

def test_split_windows_disjoint_and_chronological() -> None:
    """Driver split: >= 2 windows, chronological, zero timestamp overlap."""
    ts, px = _ticks_with_prices(seed=11, n=900)
    assert np.unique(ts).size == ts.size  # unique stamps -> strict disjointness

    windows = split_windows(ts, px, n_windows=3)

    assert len(windows) >= 2
    assert sum(w_ts.size for w_ts, _ in windows) == ts.size
    for w_ts, w_px in windows:
        assert w_ts.size > 0
        assert w_ts.size == w_px.size
        assert np.all(np.diff(w_ts) >= 0)  # chronological inside the window
    for (a_ts, _), (b_ts, _) in zip(windows, windows[1:]):
        assert float(a_ts[-1]) < float(b_ts[0]), (
            "windows overlap: "
            f"prev ends {a_ts[-1]}, next starts {b_ts[0]}"
        )


def test_split_windows_rejects_fewer_than_two_windows() -> None:
    """H-03 demands >= 2 disjoint windows — 1 window must be a DataError."""
    ts, px = _ticks_with_prices(seed=11, n=900)
    with pytest.raises(DataError):
        split_windows(ts, px, n_windows=1)


# ---------------------------------------------------------------------------
# 7. Driver E2E on a CSV fixture
# ---------------------------------------------------------------------------

def _write_tick_csv(path: Path, seed: int = 5, n: int = 1200) -> None:
    ts, px = _ticks_with_prices(seed=seed, n=n)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["ts", "price"])
        for t, p in zip(ts, px):
            writer.writerow([f"{t:.3f}", f"{p:.2f}"])


def test_driver_e2e_csv_fixture_writes_json_and_md(tmp_path: Path) -> None:
    """CLI on a mini tick-CSV -> JSON + MD with H-03 reference and ALL gate
    criteria (surrogate p, lead, edge) reported individually per window."""
    csv_path = tmp_path / "ticks.csv"
    out_dir = tmp_path / "out"
    _write_tick_csv(csv_path)

    rc = c31_cli.main([
        "--file", str(csv_path),
        "--windows", "2",
        "--surrogates", "20",
        "--segment-len", "64",
        "--n-alpha", "16",
        "--seed", "42",
        "--out", str(out_dir),
    ])
    assert rc == 0

    json_path = out_dir / "c31_cfar_results.json"
    md_path = out_dir / "c31_cfar_results.md"
    assert json_path.exists() and md_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    # H-03 reference + registered gate thresholds.
    assert payload["hypothesis"] == "H-03"
    assert "hypothesis_registry" in payload
    assert payload["hypothesis_registry"].endswith("hypothesis_registry.md")
    assert payload["gate_thresholds"] == {
        "surrogate_p_max": 0.05,
        "lead_min_ms": 50.0,
        "edge_min_bps": 11.0,
        "min_windows": 2,
    }
    # Every gate criterion individually, per window.
    assert payload["n_windows"] == 2
    assert len(payload["windows"]) == 2
    assert len(payload["per_window_pass"]) == 2
    for window in payload["windows"]:
        criteria = window["criteria"]
        for name in ("surrogate_p", "lead_ms", "edge_bps"):
            criterion = criteria[name]
            assert "value" in criterion
            assert "threshold" in criterion
            assert isinstance(criterion["passed"], bool)

    md = md_path.read_text(encoding="utf-8")
    assert "H-03" in md
    assert "hypothesis_registry.md" in md
    for window_index in (0, 1):
        assert f"## Fenster {window_index}" in md
    for criterion_label in ("Surrogate p", "Lead", "Edge"):
        assert criterion_label in md


def test_driver_cli_missing_file_exits_nonzero(tmp_path: Path) -> None:
    """Data defect (missing input) -> exit code 1, no crash."""
    rc = c31_cli.main([
        "--file", str(tmp_path / "does_not_exist.csv"),
        "--out", str(tmp_path / "out"),
    ])
    assert rc == 1
    assert not (tmp_path / "out" / "c31_cfar_results.json").exists()


# ---------------------------------------------------------------------------
# 9. Regression: corrupt timestamps must fail fast, never allocate TiBs
#    (T3 crash 2026-06-11: ts=0 row in the trades table -> 1.3 TiB bin grid)
# ---------------------------------------------------------------------------

def test_run_corrupt_zero_timestamp_raises_dataerror_fast() -> None:
    """One ts=0 row among epoch-ms ticks: run() must raise DataError BEFORE
    binning (regression for the 1.3 TiB _ArrayMemoryError on all 5 symbols)."""
    ts, px = _ticks_with_prices(seed=5)
    ts = ts.copy()
    ts[0] = 0.0  # corrupt row, sorts first -> window 0 spans the whole epoch
    order = np.argsort(ts)
    with pytest.raises(DataError, match="corrupt timestamps"):
        run(ts[order], px[order], n_windows=2, n_surrogates=5,
            segment_len=64, n_alpha=8)


def test_bin_counts_rejects_absurd_bin_grid() -> None:
    """bin_counts must refuse grids beyond MAX_BINS with a clear ValueError
    instead of attempting a terabyte-scale histogram allocation."""
    from bybit_edge.research.c31_cfar.cyclic_spectrum import MAX_BINS, bin_counts

    ts = np.array([0.0, 1.78e12])  # epoch-span at dt=10ms -> 1.78e11 bins
    with pytest.raises(ValueError, match="MAX_BINS"):
        bin_counts(ts, 10.0)
    assert MAX_BINS >= 600_000_000  # 60d at 10ms (legit T3 windows) stay legal


def test_load_trades_duckdb_filters_implausible_timestamps(tmp_path: Path) -> None:
    """The DuckDB loader drops ts=0 / seconds-epoch / far-future rows and
    keeps the plausible epoch-ms rows (read-only on the trades schema)."""
    import duckdb

    from bybit_edge.research.c31_cfar.driver import load_trades_duckdb

    db_path = tmp_path / "trades.duckdb"
    conn = duckdb.connect(str(db_path))
    conn.execute(
        "CREATE TABLE trades (ts BIGINT NOT NULL, symbol VARCHAR NOT NULL, "
        "price DOUBLE, volume DOUBLE, side VARCHAR, is_block BOOLEAN, "
        "recv_ts DOUBLE)"
    )
    good_ts = [1_780_000_000_000 + i * 100 for i in range(20)]
    rows = [(t, "BTCUSDT", 50_000.0 + i, 1.0, "Buy", False, 0.0)
            for i, t in enumerate(good_ts)]
    rows += [
        (0, "BTCUSDT", 1.0, 1.0, "Buy", False, 0.0),               # ts=0 default
        (1_780_000_000, "BTCUSDT", 2.0, 1.0, "Buy", False, 0.0),   # seconds epoch
        (9_999_999_999_999, "BTCUSDT", 3.0, 1.0, "Buy", False, 0.0),  # far future
    ]
    conn.executemany("INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    conn.close()

    ts, px = load_trades_duckdb(db_path, "BTCUSDT")
    assert ts.size == len(good_ts)
    assert float(ts[0]) == float(good_ts[0])
    assert float(ts[-1]) == float(good_ts[-1])
    assert not np.any(ts < 1_262_304_000_000)

    with pytest.raises(DataError, match="plausible"):
        load_trades_duckdb(db_path, "NOSYMBOL")


# ---------------------------------------------------------------------------
# 8. Determinism (registry reproducibility duty)
# ---------------------------------------------------------------------------

def test_run_same_seed_identical_json_payload() -> None:
    """Same input + same seed -> bit-identical JSON (minus the timestamp)."""
    ts, px = _ticks_with_prices(seed=5)
    kwargs = dict(
        n_windows=2,
        n_surrogates=10,
        seed=42,
        segment_len=64,
        n_alpha=16,
        source="determinism-fixture",
        symbol="TEST",
    )
    payload_a = run(ts, px, **kwargs)
    payload_b = run(ts, px, **kwargs)
    payload_a.pop("generated_at")
    payload_b.pop("generated_at")
    assert json.dumps(payload_a, sort_keys=True) == json.dumps(payload_b, sort_keys=True)
