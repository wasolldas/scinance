"""Unit tests for the H-16 Time-Arrow-CNN mess-gate (c16_arrow, KAPITALFREI,
GPU, F-ARROW).

The sandbox has NEITHER torch NOR a GPU — only PIPELINE CORRECTNESS is
testable here, NOT the actual CNN training power. Covers the registered
H-16 requirements the sandbox CAN verify:

  (a) CWT correctness: a pure sine tone at a known period peaks at the
      expected scale of the scalogram.
  (b) Forward/reversed label construction is correct AND the reversal
      demonstrably happens BEFORE the CWT (general non-commutation of
      reversal and the complex CWT; the log-power image coincides under
      flip only because of the SYMMETRIC reflect padding — documented
      distinction, both checked explicitly).
  (c) IAAFT surrogate generation demonstrably preserves the amplitude
      spectrum (|FFT|) of the original series within tolerance, while
      randomising the phase (and, for a nonlinear/skewed process, the
      autocorrelation-relevant *higher-order* structure).
  (d) BH-FDR family / capital_free token scan.
  (e) ``--check-gpu-only`` honestly reports the (torch-less) sandbox status.
  (f) The methodically-invalid state (leak control > 0.52) is marked in the
      payload as a DISTINCT state, NOT a DROP.

Plus: data loading against a synthetic harvester tree, day-level split
determinism, stats primitives (BH-FDR, Mann-Whitney AUC, exact paired sign
test), sentinel-cell family-size discipline, and honest ComputeError
degradation of the CNN/driver entry points without torch.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest
import pyarrow as pa
import pyarrow.parquet as pq

from bybit_edge.research.c16_arrow import cnn as cnn_mod
from bybit_edge.research.c16_arrow.driver import (
    DIFFERENTIATION_NOTE,
    HYPOTHESIS_ID,
    ComputeError,
    check_gpu,
    list_available_dates,
    load_day_imbalance,
    load_symbol_days,
    split_days_chronological,
    windows_for_days,
)
from bybit_edge.research.c16_arrow.driver import run as driver_run
from bybit_edge.research.c16_arrow.iaaft import iaaft
from bybit_edge.research.c16_arrow.scalogram import (
    STRIDE_S,
    WINDOW_S,
    cwt_complex,
    cwt_logpower,
    extract_windows,
    fourier_periods,
    scalogram_pair,
    verify_torch_parity,
)
from bybit_edge.research.c16_arrow.stats import (
    FAMILY_SIZE,
    LEAK_AUC_MAX,
    STATUS_MEASURED,
    STATUS_METHOD_INVALID,
    benjamini_hochberg,
    evaluate_gate,
    mann_whitney_auc,
    paired_sign_test_p,
    sentinel_cell,
    surrogate_percentile_95,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MODULE_DIR = REPO_ROOT / "src" / "bybit_edge" / "research" / "c16_arrow"


# ----------------------------------------------------------------------------
# (a) CWT correctness: pure sine tone peaks at the expected scale
# ----------------------------------------------------------------------------


def test_cwt_sine_peaks_at_expected_scale():
    period_s = 16.0
    t = np.arange(WINDOW_S)
    x = np.sin(2.0 * np.pi * t / period_s)
    img = cwt_logpower(x)
    assert img.shape == (64, WINDOW_S)

    periods = fourier_periods()
    # mean power per scale (time-average, avoiding edge/COI columns)
    core = img[:, WINDOW_S // 4 : 3 * WINDOW_S // 4]
    mean_power = core.mean(axis=1)
    peak_idx = int(np.argmax(mean_power))
    peak_period = float(periods[peak_idx])
    # within one scale-bin of the true period (log-spaced 64 scales over
    # 2..256s -> adjacent-bin ratio ~= 2^(1/9) ~= 1.08)
    assert abs(math.log(peak_period / period_s)) < math.log(1.3), (
        f"expected scale peak near {period_s}s, got {peak_period}s"
    )


def test_cwt_rejects_non_1d_input():
    with pytest.raises(ValueError):
        cwt_complex(np.zeros((2, WINDOW_S)))


# ----------------------------------------------------------------------------
# (b) Forward/reversed construction happens BEFORE the CWT
# ----------------------------------------------------------------------------


def test_reversal_precedes_cwt_general_noncommutation():
    """cwt_complex(x[::-1]) != flip(cwt_complex(x)) in general (complex).

    This is the general-case inequality the registry warns about: reversing
    the FINISHED complex transform is NOT the same operation as reversing
    the raw series first. The exact algebraic relation for this admissible
    (real-signal) Morlet CWT with symmetric reflect padding is the
    conjugate-flip identity, checked in the second assertion — but a naive
    "just flip the array" implementation would be WRONG (this is exactly
    the bug class registry H-16 requires ruling out).
    """
    rng = np.random.default_rng(0)
    x = rng.standard_normal(WINDOW_S)

    w_fwd = cwt_complex(x)
    w_of_reversed_series = cwt_complex(x[::-1])
    naive_flip_of_forward = np.flip(w_fwd, axis=1)

    assert not np.allclose(w_of_reversed_series, naive_flip_of_forward), (
        "CWT(reversed(x)) must NOT equal a naive flip of CWT(x) in general "
        "(complex coefficients) — a pipeline that flips the finished image "
        "instead of reversing the raw series would silently pass this only "
        "by accident."
    )
    # documented exact relation (real signal, symmetric padding):
    assert np.allclose(w_of_reversed_series, np.conj(naive_flip_of_forward), atol=1e-9)


def test_scalogram_pair_reverses_raw_series_not_finished_image():
    """scalogram_pair's REVERSED half is cwt_logpower(window[::-1]), full stop."""
    rng = np.random.default_rng(1)
    window = rng.standard_normal(WINDOW_S) * 3.0 + 0.5

    fwd, rev = scalogram_pair(window)
    expected_rev = cwt_logpower(window[::-1])
    assert np.allclose(rev, expected_rev, atol=1e-10)
    assert np.allclose(fwd, cwt_logpower(window), atol=1e-10)

    # For THIS representation (log power, symmetric reflect padding) the
    # reversed image happens to equal np.flip(fwd) too — documented in the
    # module docstring — but that coincidence must never be relied upon by
    # the implementation: scalogram_pair must call cwt_logpower on the
    # reversed raw series independently. Verify with an asymmetric series
    # where a naive same-object flip could subtly diverge from a fresh CWT
    # call (guards against future refactors reintroducing a shortcut).
    fresh_rev = cwt_logpower(np.array(window[::-1]))
    assert np.array_equal(rev, fresh_rev)


def test_windows_never_cross_synthetic_day_boundary():
    n = WINDOW_S * 3 + 17
    series = np.arange(n, dtype=np.float64)
    windows = extract_windows(series, WINDOW_S, STRIDE_S)
    starts = np.arange(0, n - WINDOW_S + 1, STRIDE_S)
    assert windows.shape == (starts.size, WINDOW_S)
    for w, s in zip(windows, starts):
        assert np.array_equal(w, series[s : s + WINDOW_S])


# ----------------------------------------------------------------------------
# (c) IAAFT: preserves amplitude spectrum, randomises phase
# ----------------------------------------------------------------------------


def test_iaaft_preserves_amplitude_spectrum_linear_process():
    rng = np.random.default_rng(3)
    n = 4000
    eps = rng.standard_normal(n)
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.6 * x[i - 1] + eps[i]

    s, info = iaaft(x, np.random.default_rng(5))
    amp_x = np.abs(np.fft.rfft(x))
    amp_s = np.abs(np.fft.rfft(s))
    rel_err = float(np.linalg.norm(amp_x - amp_s) / np.linalg.norm(amp_x))

    assert rel_err < 0.05, f"IAAFT amplitude-spectrum relative error too high: {rel_err}"
    assert info["spectrum_rel_err"] == pytest.approx(rel_err, abs=1e-9)
    assert info["end"] == "amplitude"
    # marginal distribution is EXACT when end="amplitude"
    assert np.allclose(np.sort(s), np.sort(x))


def test_iaaft_randomises_phase_not_just_amplitude():
    """The surrogate's Fourier PHASES differ substantially from the original.

    Mean absolute wrapped phase difference of a fully phase-randomised
    signal against the original is E[|Uniform(-pi, pi)|] = pi/2 ~= 1.5708.
    A pipeline bug that accidentally returned the (unrandomised) original
    series, or one that preserved phase instead of amplitude, would show a
    near-zero mean phase difference here.
    """
    rng = np.random.default_rng(7)
    n = 4000
    eps = rng.standard_normal(n)
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = 0.6 * x[i - 1] + eps[i]

    s, _info = iaaft(x, np.random.default_rng(11))
    ph_x = np.angle(np.fft.rfft(x))
    ph_s = np.angle(np.fft.rfft(s))
    wrapped_diff = np.abs(np.angle(np.exp(1j * (ph_x - ph_s))))
    mean_diff = float(wrapped_diff.mean())

    assert mean_diff > 1.2, f"phase differences too small (not randomised): {mean_diff}"
    assert not np.allclose(s, x)


def test_iaaft_end_spectrum_variant_is_exact_in_spectrum():
    rng = np.random.default_rng(13)
    n = 2000
    x = np.cumsum(rng.standard_normal(n))  # nonstationary-ish, still fine for a shape check
    s, info = iaaft(x, np.random.default_rng(17), end="spectrum")
    assert info["end"] == "spectrum"
    amp_x = np.abs(np.fft.rfft(x))
    amp_s = np.abs(np.fft.rfft(s))
    rel_err = float(np.linalg.norm(amp_x - amp_s) / np.linalg.norm(amp_x))
    assert rel_err < 1e-6


def test_iaaft_degenerate_constant_series_is_honest_noop():
    x = np.full(50, 3.0)
    s, info = iaaft(x, np.random.default_rng(0))
    assert np.array_equal(s, x)
    assert info["n_iter"] == 0
    assert info["converged"] is True


def test_iaaft_rejects_non_1d():
    with pytest.raises(ValueError):
        iaaft(np.zeros((2, 10)), np.random.default_rng(0))


# ----------------------------------------------------------------------------
# stats primitives
# ----------------------------------------------------------------------------


def test_benjamini_hochberg_matches_known_case():
    # classic textbook example: 5 p-values, alpha=0.10
    p = [0.01, 0.04, 0.03, 0.20, 0.50]
    rejected, p_crit = benjamini_hochberg(p, alpha=0.10)
    # sorted: 0.01(1),0.03(2),0.04(3),0.20(4),0.50(5); thresholds i/5*0.10
    # = .02,.04,.06,.08,.10 -> 0.01<=.02 ok, 0.03<=.04 ok, 0.04<=.06 ok,
    # 0.20>.08 fail -> largest k with all preceding true is k=3 -> p_crit=0.04
    assert p_crit == pytest.approx(0.04)
    # input order: [0.01(rank1), 0.04(rank3), 0.03(rank2), 0.20(rank4), 0.50(rank5)]
    assert rejected == [True, True, True, False, False]


def test_benjamini_hochberg_empty():
    assert benjamini_hochberg([]) == ([], 0.0)


def test_mann_whitney_auc_separable_and_overlapping():
    pos = np.array([5.0, 6.0, 7.0])
    neg = np.array([1.0, 2.0, 3.0])
    assert mann_whitney_auc(pos, neg) == pytest.approx(1.0)
    assert mann_whitney_auc(neg, pos) == pytest.approx(0.0)

    same = np.array([1.0, 2.0, 3.0, 4.0])
    assert mann_whitney_auc(same, same) == pytest.approx(0.5)


def test_paired_sign_test_p_exact_small_n():
    # n=10, all forward > reversed -> p = P(Bin(10,.5)>=10) = (1/2)^10
    fwd = np.arange(10.0) + 10.0
    rev = np.arange(10.0)
    p, counts = paired_sign_test_p(fwd, rev)
    assert counts == {"n_pairs": 10, "n_greater": 10, "n_ties": 0}
    assert p == pytest.approx(0.5 ** 10, rel=1e-9)


def test_paired_sign_test_p_null_case_near_half():
    rng = np.random.default_rng(42)
    n = 400
    fwd = rng.standard_normal(n)
    rev = rng.standard_normal(n)  # independent -> null true
    p, counts = paired_sign_test_p(fwd, rev)
    # not a tight bound (stochastic), just sanity: p should not be tiny
    assert p > 0.01
    assert counts["n_pairs"] == n


def test_paired_sign_test_p_all_ties_returns_one():
    fwd = np.ones(5)
    rev = np.ones(5)
    p, counts = paired_sign_test_p(fwd, rev)
    assert p == 1.0
    assert counts["n_ties"] == 5


def test_surrogate_percentile_95_basic():
    aucs = [0.50 + 0.001 * i for i in range(20)]  # 0.500..0.519
    p95 = surrogate_percentile_95(aucs)
    assert 0.515 <= p95 <= 0.520


def test_sentinel_cell_p_value_is_one_and_unmeasured():
    c = sentinel_cell("BTCUSDT", "no data")
    assert c["measured"] is False
    assert c["p_value"] == 1.0
    assert math.isnan(c["auc"])


def test_evaluate_gate_family_size_padding_never_shrinks():
    cells = [sentinel_cell(f"SYM{i}", "no data") for i in range(FAMILY_SIZE)]
    gate = evaluate_gate(cells)
    assert gate["family_size"] == FAMILY_SIZE
    assert gate["n_cells_measured"] == 0
    assert gate["n_cells_sentinel"] == FAMILY_SIZE
    # an all-sentinel family can never be gate-met
    assert gate["n_symbols_gate_met"] == 0
    assert gate["status"] == STATUS_MEASURED  # no measured symbol -> nothing invalid


# ----------------------------------------------------------------------------
# (f) methodically-invalid state is DISTINCT from a DROP
# ----------------------------------------------------------------------------


def _measured_cell(symbol: str, *, auc: float, p_value: float,
                    surrogate_p95: float, leak_auc: float) -> dict:
    return {
        "symbol": symbol, "measured": True, "auc": auc, "p_value": p_value,
        "surrogate_p95": surrogate_p95, "leak_auc": leak_auc,
        "surrogate_aucs": [], "ablation_auc_unsigned": 0.5,
    }


def test_leak_control_failure_marks_method_invalid_not_drop():
    cells = [
        _measured_cell("BTCUSDT", auc=0.70, p_value=1e-6, surrogate_p95=0.51,
                        leak_auc=0.60),  # > 0.52 -> leak control fails
    ] + [sentinel_cell(f"SYM{i}", "not run") for i in range(FAMILY_SIZE - 1)]
    gate = evaluate_gate(cells)

    assert gate["status"] == STATUS_METHOD_INVALID
    assert gate["status"] != "DROP"
    assert gate["method_invalid"] is True
    assert "BTCUSDT" in gate["method_invalid_symbols"]
    assert gate["leak_control_passed"] is False
    # the criterion is still visible per-cell for the audit trail:
    assert cells[0]["leak_ok"] is False
    assert cells[0]["method_invalid"] is True
    # a method-invalid symbol cannot count as a met gate even with AUC/FDR ok:
    assert cells[0]["symbol_gate_met"] is False
    # gate_quorum_met must never be True under method invalidity
    assert gate["gate_quorum_met"] is False


def test_passing_cell_meets_gate_when_all_criteria_hold():
    cells = [
        _measured_cell("BTCUSDT", auc=0.65, p_value=1e-9, surrogate_p95=0.51,
                        leak_auc=0.50),
        _measured_cell("ETHUSDT", auc=0.62, p_value=1e-9, surrogate_p95=0.50,
                        leak_auc=0.49),
        _measured_cell("SOLUSDT", auc=0.61, p_value=1e-9, surrogate_p95=0.52,
                        leak_auc=0.51),
        _measured_cell("BNBUSDT", auc=0.63, p_value=1e-9, surrogate_p95=0.49,
                        leak_auc=0.48),
        sentinel_cell("XRPUSDT", "not run"),
    ]
    gate = evaluate_gate(cells)
    assert gate["status"] == STATUS_MEASURED
    assert gate["method_invalid"] is False
    assert gate["leak_control_passed"] is True
    assert gate["n_symbols_gate_met"] >= 4
    assert gate["gate_quorum_met"] is True
    assert LEAK_AUC_MAX == 0.52


# ----------------------------------------------------------------------------
# (d) capital_free flag + no cost-model identifiers
# ----------------------------------------------------------------------------


def test_capital_free_and_no_cost_identifiers():
    forbidden = ("bps", "pnl", "sharpe", "friction", "edge_")
    for py in sorted(MODULE_DIR.glob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        idents: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                idents.add(node.id)
            elif isinstance(node, ast.Attribute):
                idents.add(node.attr)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                idents.add(node.name)
            elif isinstance(node, ast.arg):
                idents.add(node.arg)
            elif isinstance(node, ast.keyword) and node.arg:
                idents.add(node.arg)
        for ident in idents:
            low = ident.lower()
            for bad in forbidden:
                assert bad not in low, (
                    f"{py.name}: identifier {ident!r} suggests cost-model code "
                    f"(H-16 is KAPITALFREI)"
                )


def test_differentiation_note_present_and_nonempty():
    assert "Entropie" in DIFFERENTIATION_NOTE
    assert "AUC" in DIFFERENTIATION_NOTE
    assert len(DIFFERENTIATION_NOTE) > 100


# ----------------------------------------------------------------------------
# (e) --check-gpu-only honestly reports the (torch-less) sandbox
# ----------------------------------------------------------------------------


def test_gpu_status_honest_without_torch():
    status = cnn_mod.gpu_status()
    if not cnn_mod._TORCH_AVAILABLE:  # sandbox: torch genuinely absent
        assert status["torch_available"] is False
        assert status["cuda_available"] is False
        assert status["verdict_capable"] is False
    else:  # pragma: no cover - only true on a machine with torch installed
        assert status["torch_available"] is True


def test_check_gpu_driver_wrapper():
    status = check_gpu()
    assert status["hypothesis"] == HYPOTHESIS_ID
    assert "note" in status


def _cli_main():
    spec = importlib.util.spec_from_file_location(
        "c16_arrow_cli", REPO_ROOT / "scripts" / "c16_arrow.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main


def test_cli_check_gpu_only_writes_honest_report(tmp_path):
    main = _cli_main()
    out_dir = tmp_path / "out"
    rc = main(["--check-gpu-only", "--out-dir", str(out_dir)])
    payload = json.loads((out_dir / "c16_gpu_check.json").read_text())
    if not cnn_mod._TORCH_AVAILABLE:
        assert rc == 2  # SKIP: no verdict-capable compute in the sandbox
        assert payload["torch_available"] is False
        assert payload["verdict_capable"] is False
    else:  # pragma: no cover
        assert payload["torch_available"] is True


def test_cli_full_run_without_compute_gate_is_clean_skip(tmp_path):
    """Without torch (sandbox), a full-run CLI invocation must SKIP (rc=2),
    never silently produce a verdict-shaped payload."""
    if cnn_mod._TORCH_AVAILABLE:  # pragma: no cover - only true with torch installed
        pytest.skip("torch is available in this environment; skip-path not exercised")
    main = _cli_main()
    rc = main([
        "--base-dir", str(tmp_path / "nonexistent"),
        "--end-date", "2026-04-01",
        "--out-dir", str(tmp_path / "out2"),
    ])
    assert rc == 2


# ----------------------------------------------------------------------------
# torch-optional degradation of the CNN / driver entry points
# ----------------------------------------------------------------------------


def test_require_torch_raises_compute_error_without_torch():
    if cnn_mod._TORCH_AVAILABLE:  # pragma: no cover
        pytest.skip("torch available; ComputeError path not exercised")
    with pytest.raises(cnn_mod.ComputeError):
        cnn_mod.require_torch("test context")


def test_train_classifier_raises_compute_error_without_torch():
    if cnn_mod._TORCH_AVAILABLE:  # pragma: no cover
        pytest.skip("torch available; ComputeError path not exercised")
    dummy = np.zeros((4, WINDOW_S), dtype=np.float32)
    with pytest.raises(cnn_mod.ComputeError):
        cnn_mod.train_forward_reverse_classifier(dummy, dummy, seed=0, device="cpu")


def test_driver_run_raises_compute_error_without_torch(tmp_path):
    if cnn_mod._TORCH_AVAILABLE:  # pragma: no cover
        pytest.skip("torch available; ComputeError path not exercised")
    with pytest.raises(ComputeError):
        driver_run(tmp_path, ("BTCUSDT",), end_date="2026-04-01")


def test_verify_torch_parity_reports_unchecked_without_torch():
    if cnn_mod._TORCH_AVAILABLE:  # pragma: no cover
        pytest.skip("torch available; unchecked-path not exercised")
    result = verify_torch_parity()
    assert result["checked"] is False


# ----------------------------------------------------------------------------
# Data loading against a synthetic harvester tree + day-level split
# ----------------------------------------------------------------------------


def _write_parquet(d: Path, ts_list: list[int], payload_list: list[str]) -> None:
    d.mkdir(parents=True, exist_ok=True)
    table = pa.table({
        "ts_exchange_ms": pa.array(ts_list, pa.int64()),
        "payload_json": pa.array(payload_list, pa.string()),
    })
    pq.write_table(table, d / "data.parquet")


def _day_ms(day: str) -> int:
    y, m, d = (int(x) for x in day.split("-"))
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


def _build_bybit_day(base: Path, symbol: str, day: str, rows: list[tuple[int, str, float]]) -> None:
    """rows: list of (second_of_day, side, size)."""
    day_ms = _day_ms(day)
    ts_list, payloads = [], []
    for sec, side, size in rows:
        ts_list.append(day_ms + sec * 1000 + 100)
        payloads.append(json.dumps({"side": side, "price": "50000", "size": str(size)}))
    part = base / "raw" / "bybit" / "publicTrade" / f"symbol={symbol}" / f"date={day}"
    _write_parquet(part, ts_list, payloads)


def test_load_day_imbalance_aggregates_signed_volume_per_second():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        rows = [(0, "Buy", 5.0), (0, "Sell", 2.0), (1, "Buy", 1.0)]
        _build_bybit_day(base, "BTCUSDT", "2026-04-01", rows)
        series, n_active, n_trades = load_day_imbalance(base, "BTCUSDT", "2026-04-01")
        assert series.shape == (86_400,)
        assert series[0] == pytest.approx(3.0)
        assert series[1] == pytest.approx(1.0)
        assert series[2] == pytest.approx(0.0)
        assert n_active == 2
        assert n_trades == 3


def test_list_available_dates_filters_range_and_requires_parquet():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        for day in ("2026-03-30", "2026-04-01", "2026-04-05"):
            _build_bybit_day(base, "BTCUSDT", day, [(0, "Buy", 1.0)])
        dates = list_available_dates(base, "BTCUSDT", "2026-03-31", "2026-04-04")
        assert dates == ["2026-04-01"]


def test_load_symbol_days_marks_low_activity_day_invalid():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        # active day: enough distinct active seconds (>10% of 86400 = 8640)
        active_rows = [(sec, "Buy", 1.0) for sec in range(0, 86_400, 5)]  # 17280 active secs
        _build_bybit_day(base, "BTCUSDT", "2026-04-01", active_rows)
        # near-empty day: 1 trade only -> invalid
        _build_bybit_day(base, "BTCUSDT", "2026-04-02", [(0, "Buy", 1.0)])

        days, series_by_day, info = load_symbol_days(base, "BTCUSDT", "2026-04-01", "2026-04-02")
        assert days == ["2026-04-01"]
        assert info["n_days_valid"] == 1
        assert info["n_days_invalid"] == 1
        assert "2026-04-01" in series_by_day


def test_split_days_chronological_is_deterministic_and_tail_biased():
    days = [f"2026-04-{d:02d}" for d in range(1, 11)]  # 10 days
    train, test = split_days_chronological(days, test_frac=0.20)
    assert train == days[:8]
    assert test == days[8:]
    # re-run: identical (no randomness anywhere)
    train2, test2 = split_days_chronological(list(reversed(days)) and days, test_frac=0.20)
    assert train2 == train and test2 == test


def test_split_days_chronological_keeps_at_least_one_train_day():
    days = ["2026-04-01", "2026-04-02"]
    train, test = split_days_chronological(days, test_frac=0.9)
    assert len(train) >= 1
    assert len(test) >= 1
    assert set(train) | set(test) == set(days)


def test_split_days_chronological_requires_two_days():
    from bybit_edge.research.c16_arrow.driver import DataError
    with pytest.raises(DataError):
        split_days_chronological(["2026-04-01"])


def test_windows_for_days_unsigned_ablation_applies_abs_to_raw_series():
    series_by_day = {"d1": np.concatenate([np.full(WINDOW_S, -2.0), np.zeros(10)])}
    signed = windows_for_days(series_by_day, ["d1"])
    unsigned = windows_for_days(series_by_day, ["d1"], unsigned=True)
    assert np.all(signed[0] == -2.0)
    assert np.all(unsigned[0] == 2.0)
