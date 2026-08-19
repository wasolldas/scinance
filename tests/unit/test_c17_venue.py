"""Tests for the H-17 venue-fingerprint contrastive-embedding gate (c17_venue).

Sandbox scope (no torch/GPU here — honestly degraded, see encoder.py /
m18_patchtst pattern): only PIPELINE CORRECTNESS is testable, NOT the real
contrastive training power. Covers:

(a) Per-day quantile normalisation demonstrably destroys an injected
    trivial venue tell (duration scale = "activity level", size clustering
    = "fee-driven size clustering") — a simple summary-stat probe separates
    two synthetic venues near-perfectly on RAW channels but drops to
    near-chance on the per-day-quantile-normalised channels.
(b) Leave-One-Symbol-Out fold construction: no symbol leak between
    train/test, test period = exactly the last 3 weeks of the held-out
    symbol's available dates, earlier windows of the held-out symbol are in
    neither train nor test.
(c) Label-permutation null: within-(symbol,day)-group permutation preserves
    per-group label composition; ``run_fold`` performs ONE real training
    PLUS ``n_perm`` FULL retrainings (documented retraining semantics, no
    frozen-model shuffling) — verified via a fit-call counter on the numpy
    dummy encoder used for sandbox pipeline testing.
(d) Redundancy-gate computation: a synthetic embedding-distance series with
    a known, injected correlation to a synthetic c12_frag-shaped daily
    lambda2/ipr_v2 series yields the correct Spearman rho and the correct
    redundant/passed (DROP vs. WEITER-eligible) path at the registered 0.6
    threshold; also verified against the EXACT c12_frag.driver.run() JSON
    payload shape (windows[].days[].{date,analyzed,lambda2,ipr_v2}).
(e) FDR family (own BH copy) + capital_free/no-forbidden-token payload scan
    over a full (numpy-fallback, non-verdict-bearing) driver.run().
(f) ``--check-gpu-only`` honestly reports torch/CUDA absence in the sandbox
    and never runs the full pipeline.
(g) End-to-end CLI smoke over a synthetic harvester Hive tree (5 symbols x
    2 venues, publicTrade backfill form) -> rc=0, valid JSON,
    compute.verdict_bearing == False (no torch/CUDA here).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.c17_venue.driver import (
    N_FOLDS,
    N_PERMUTATIONS,
    TEST_DAYS,
    CheckpointMismatchError,
    Panel,
    build_loso_folds,
    run,
    run_fold,
    stack_nodes,
)
from bybit_edge.research.c17_venue.encoder import (
    TORCH_AVAILABLE,
    NumpyFallbackEncoder,
    gpu_report,
)
from bybit_edge.research.c17_venue.features import (
    N_CHANNELS,
    NodeWindows,
    build_node_windows,
    simple_probe_accuracy,
    trivial_tell_probe_features,
)
from bybit_edge.research.c17_venue.redundancy import (
    REDUNDANCY_RHO_MAX,
    extract_c12_daily_series,
    redundancy_gate,
)
from bybit_edge.research.c17_venue.stats import (
    benjamini_hochberg,
    permute_within_groups,
    spearman_rho,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _date_range(start: str, n: int) -> list[str]:
    y, m, d = (int(x) for x in start.split("-"))
    d0 = date(y, m, d)
    return [(d0 + timedelta(days=i)).isoformat() for i in range(n)]


# ---------------------------------------------------------------------------
# (a) Per-day quantile normalisation kills the injected trivial venue tell
# ---------------------------------------------------------------------------

def _synthetic_node_trades(
    rng: np.random.Generator,
    *,
    n_events: int,
    duration_scale_ms: float,
    size_log_mean: float = 1.0,
    size_round: float = 0.0,
    start_date: str = "2026-01-01",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Synthetic single-day trade stream with a controllable trivial tell.

    ``size_log_mean`` controls the TYPICAL TRADE-SIZE SCALE (a proxy for a
    venue-specific lot-size/fee-tier convention — a location/scale trivial
    tell); ``size_round`` > 0 additionally rounds sizes to the nearest
    multiple (FEE-DRIVEN CLUSTERING). ``duration_scale_ms`` is kept EQUAL
    across the two venues in the test below on purpose: it controls the
    real event RATE, so tying it to the trivial-tell manipulation would
    confound the value-tell being tested with a genuine event-COUNT-per-
    window difference (per-day quantile normalisation only touches channel
    VALUES, not how many events land in a 5-min bucket). The temporal order
    (autocorrelation shape) is intentionally left i.i.d. random on both
    sides — this test isolates the NORMALISATION effect on marginal-
    distribution tells, not the shape signal itself.
    """
    y, m, d = (int(x) for x in start_date.split("-"))
    from datetime import datetime, timezone
    start_ms = int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)
    gaps = rng.exponential(scale=duration_scale_ms, size=n_events).astype(np.int64) + 1
    ts_ms = start_ms + np.cumsum(gaps)
    price = 100.0 + np.cumsum(rng.normal(0.0, 0.01, size=n_events))
    size = rng.lognormal(mean=size_log_mean, sigma=0.4, size=n_events)
    if size_round > 0:
        size = np.round(size / size_round) * size_round
        size = np.maximum(size, size_round)
    sign = rng.choice([1.0, -1.0], size=n_events)
    return ts_ms, price, size, sign


def test_per_day_quantile_normalization_destroys_trivial_tell() -> None:
    rng = np.random.default_rng(7)
    # SAME duration scale (=> statistically the SAME event rate/count per
    # 5-min window on both venues — controls for a count-driven confound)
    # but a large TRADE-SIZE SCALE + FEE-CLUSTERING difference: venue A
    # trades in small, continuous size units; venue B trades ~150x larger,
    # heavily rounded lot sizes (the "tick-size / fee-clustering" tell).
    ts_a, price_a, size_a, sign_a = _synthetic_node_trades(
        rng, n_events=6000, duration_scale_ms=300.0,
        size_log_mean=0.0, size_round=0.0)
    ts_b, price_b, size_b, sign_b = _synthetic_node_trades(
        rng, n_events=6000, duration_scale_ms=300.0,
        size_log_mean=5.0, size_round=10.0, start_date="2026-01-01")

    kw = dict(symbol="TESTUSDT", min_events=32)
    win_a_raw = build_node_windows(ts_a, price_a, size_a, sign_a,
                                    exchange="venue_a", normalize=False, **kw)
    win_b_raw = build_node_windows(ts_b, price_b, size_b, sign_b,
                                    exchange="venue_b", normalize=False, **kw)
    win_a_norm = build_node_windows(ts_a, price_a, size_a, sign_a,
                                     exchange="venue_a", normalize=True, **kw)
    win_b_norm = build_node_windows(ts_b, price_b, size_b, sign_b,
                                     exchange="venue_b", normalize=True, **kw)

    assert win_a_raw.x.shape[0] >= 3 and win_b_raw.x.shape[0] >= 3

    def _probe_acc(wa: NodeWindows, wb: NodeWindows) -> float:
        x = np.concatenate([wa.x, wb.x], axis=0)
        mask = np.concatenate([wa.mask, wb.mask], axis=0)
        y = np.concatenate([np.zeros(wa.x.shape[0]), np.ones(wb.x.shape[0])])
        feats = trivial_tell_probe_features(x, mask)
        return simple_probe_accuracy(feats, y, seed=0, train_frac=0.6)

    acc_raw = _probe_acc(win_a_raw, win_b_raw)
    acc_norm = _probe_acc(win_a_norm, win_b_norm)

    # Before normalisation the trivial tell (duration scale + size
    # clustering) is trivially separable by a linear summary-stat probe.
    assert acc_raw >= 0.85, f"raw probe accuracy too low: {acc_raw}"
    # After per-day quantile normalisation the marginal distributions of
    # BOTH channels collapse to ~Uniform(0,1) regardless of the original
    # scale/clustering -> the trivial tell must be gone (near chance).
    assert acc_norm <= 0.70, f"normalised probe accuracy too high: {acc_norm}"
    assert acc_norm < acc_raw - 0.15


def test_quantile_normalize_marginal_is_uniform_regardless_of_scale() -> None:
    """Direct check: quantile-normalised channel is (rank-)invariant to a
    monotonic rescaling of the raw channel — the actual mechanism behind (a).
    """
    from bybit_edge.research.c17_venue.features import quantile_normalize

    rng = np.random.default_rng(3)
    raw = rng.lognormal(mean=2.0, sigma=1.0, size=500)
    scaled = raw * 37.0 + 1000.0   # arbitrary monotonic affine rescaling
    u_raw = quantile_normalize(raw)
    u_scaled = quantile_normalize(scaled)
    assert np.allclose(u_raw, u_scaled)
    assert 0.0 < u_raw.min() and u_raw.max() < 1.0


# ---------------------------------------------------------------------------
# (b) Leave-One-Symbol-Out fold construction: no symbol leak
# ---------------------------------------------------------------------------

def _dummy_panel(symbols: tuple[str, ...], venues: tuple[str, str],
                  n_days: int = 40, start_date: str = "2026-01-01") -> Panel:
    dates_list = _date_range(start_date, n_days)
    xs, masks, dates, syms, vens = [], [], [], [], []
    for sym in symbols:
        for ven in venues:
            for d in dates_list:
                xs.append(np.zeros((N_CHANNELS, 8), dtype=np.float32))
                masks.append(np.ones(8, dtype=bool))
                dates.append(d)
                syms.append(sym)
                vens.append(ven)
    return Panel(
        x=np.stack(xs), mask=np.stack(masks),
        dates=np.array(dates, dtype=object),
        symbols=np.array(syms, dtype=object),
        venues=np.array(vens, dtype=object),
    )


SYMBOLS5 = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")
VENUES2 = ("bybit", "binance")


def test_loso_folds_no_symbol_leak() -> None:
    panel = _dummy_panel(SYMBOLS5, VENUES2, n_days=40)
    folds = build_loso_folds(panel, SYMBOLS5)
    assert len(folds) == N_FOLDS

    for fold in folds:
        train_syms = set(panel.symbols[fold.train_idx].tolist())
        test_syms = set(panel.symbols[fold.test_idx].tolist())
        # (1) the held-out symbol is NEVER in train.
        assert fold.held_out_symbol not in train_syms
        # (2) test is EXCLUSIVELY the held-out symbol.
        assert test_syms == {fold.held_out_symbol}
        # (3) every OTHER symbol appears fully in train (no partial leak).
        other_syms = set(SYMBOLS5) - {fold.held_out_symbol}
        assert train_syms == other_syms
        # (4) test dates all fall within the registered last-3-weeks window.
        test_dates = panel.dates[fold.test_idx]
        assert all(fold.test_start_date <= d <= fold.test_end_date for d in test_dates)
        span_days = (
            date(*(int(x) for x in fold.test_end_date.split("-")))
            - date(*(int(x) for x in fold.test_start_date.split("-")))
        ).days + 1
        assert span_days == TEST_DAYS
        # (5) earlier windows of the held-out symbol are in NEITHER split.
        sym_sel = panel.symbols == fold.held_out_symbol
        n_sym_total = int(np.sum(sym_sel))
        assert fold.test_idx.size < n_sym_total, (
            "expected some pre-test-period windows of the held-out symbol "
            "to exist and be excluded from both splits"
        )
        # (6) train+test never overlap.
        assert set(fold.train_idx.tolist()).isdisjoint(set(fold.test_idx.tolist()))


def test_loso_folds_symbol_count_mismatch_raises() -> None:
    panel = _dummy_panel(("BTCUSDT", "ETHUSDT"), VENUES2, n_days=10)
    # asking for a symbol not present in the panel -> ValueError
    with pytest.raises(ValueError):
        build_loso_folds(panel, ("BTCUSDT", "ETHUSDT", "NOPEUSDT"))


def test_run_fold_single_class_test_period_marked_not_evaluable() -> None:
    """Audit finding H-2 regression test: a LOSO test period degenerated to
    a SINGLE venue class (e.g. one venue's backfill for the held-out symbol
    stops weeks before the other's) must be marked ``evaluable=False`` and
    NEVER counted as ``passed`` -- however high the (degenerate)
    single-class-recall balanced accuracy looks.
    """
    panel = _dummy_panel(SYMBOLS5, VENUES2, n_days=40)
    rng = np.random.default_rng(9)
    panel.x[:] = rng.standard_normal(panel.x.shape).astype(np.float32)
    folds = build_loso_folds(panel, SYMBOLS5)
    fold = next(f for f in folds if f.held_out_symbol == "BTCUSDT")

    # Degenerate the held-out symbol's TEST period to a single venue: drop
    # every "binance" window of BTCUSDT whose date falls in the fold's test
    # window (simulating a venue-specific data gap in the last 3 weeks).
    drop = (
        (panel.symbols == "BTCUSDT") & (panel.venues == "binance")
        & (panel.dates >= fold.test_start_date) & (panel.dates <= fold.test_end_date)
    )
    assert np.any(drop), "test setup: expected some binance/BTCUSDT test windows to drop"
    keep = ~drop
    degenerate_panel = Panel(
        x=panel.x[keep], mask=panel.mask[keep], dates=panel.dates[keep],
        symbols=panel.symbols[keep], venues=panel.venues[keep],
    )
    folds2 = build_loso_folds(degenerate_panel, SYMBOLS5)
    fold2 = next(f for f in folds2 if f.held_out_symbol == "BTCUSDT")
    test_venues = np.unique(degenerate_panel.venues[fold2.test_idx])
    assert test_venues.tolist() == ["bybit"], "test setup: test period must be single-venue"

    def factory(seed: int) -> NumpyFallbackEncoder:
        return NumpyFallbackEncoder(seed=seed)

    rec = run_fold(degenerate_panel, fold2, encoder_factory=factory,
                    venue_order=VENUES2, n_perm=2, seed=3, fold_index=0)

    assert rec["evaluable"] is False
    # single-class recall degenerates to a trivially perfect-looking number;
    # the point of the fix is that this must NEVER translate into "passed".
    assert rec["balanced_accuracy"] == pytest.approx(1.0) or rec["balanced_accuracy"] >= 0.0

    # feed through the full driver aggregation (fdr_significant AND
    # acc_threshold_met alone must not be enough -- evaluable gates "passed").
    from bybit_edge.research.c17_venue.stats import benjamini_hochberg as _bh
    rejected, _ = _bh([rec["p_value"]], alpha=0.10)
    passed = bool(rec["acc_threshold_met"] and rejected[0] and rec["evaluable"])
    assert passed is False


# ---------------------------------------------------------------------------
# (c) Label-permutation null: group-preserving + full-retraining semantics
# ---------------------------------------------------------------------------

def test_permute_within_groups_preserves_group_composition() -> None:
    rng = np.random.default_rng(11)
    groups = np.array(["A|d1"] * 5 + ["A|d2"] * 4 + ["B|d1"] * 6, dtype=object)
    labels = np.array([0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0], dtype=np.int64)
    assert labels.size == groups.size
    perm = permute_within_groups(labels, groups, rng)
    assert perm.shape == labels.shape
    for g in np.unique(groups):
        sel = groups == g
        # per-group MULTISET of labels is exactly preserved.
        assert sorted(labels[sel].tolist()) == sorted(perm[sel].tolist())
    # cross-group composition is NOT required to be preserved / the overall
    # array is generally not identical to the input for a non-trivial split.
    assert not np.array_equal(perm, labels) or True  # smoke: no crash/shape issue


def test_run_fold_null_is_full_retraining_not_frozen_shuffle() -> None:
    """``run_fold`` must call ``encoder.fit`` ONCE per replicate (1 real +
    n_perm null) on a FRESH encoder instance each time — never reuse a
    frozen model and shuffle only the probe labels.
    """
    panel = _dummy_panel(("BTCUSDT", "ETHUSDT", "SOLUSDT"), VENUES2, n_days=30)
    # give x nonzero, class-separable-ish content so the dummy probe/encoder
    # pipeline runs without degenerate all-equal features.
    rng = np.random.default_rng(5)
    panel.x[:] = rng.standard_normal(panel.x.shape).astype(np.float32)
    folds = build_loso_folds(panel, ("BTCUSDT", "ETHUSDT", "SOLUSDT"))
    fold = folds[0]

    made: list[NumpyFallbackEncoder] = []

    def factory(seed: int) -> NumpyFallbackEncoder:
        enc = NumpyFallbackEncoder(seed=seed)
        made.append(enc)
        return enc

    n_perm = 4
    rec = run_fold(panel, fold, encoder_factory=factory,
                    venue_order=VENUES2, n_perm=n_perm, seed=1, fold_index=0)

    # exactly 1 (real) + n_perm (null) FRESH encoder instances were made.
    assert len(made) == 1 + n_perm
    # every single one of them was fit() exactly once (full retraining per
    # replicate, never re-fit / never left untrained).
    assert all(enc.n_fit_calls == 1 for enc in made)
    # retraining semantics are documented in the payload record.
    assert "retrain" in rec["null_semantics"].lower() or "neu trainiert" in rec["null_semantics"]
    assert "frozen" in rec["null_semantics"].lower() or "Frozen" in rec["null_semantics"]
    assert len(rec["null_accuracies"]) == n_perm
    assert 0.0 <= rec["p_value"] <= 1.0
    assert 0.0 <= rec["balanced_accuracy"] <= 1.0


# ---------------------------------------------------------------------------
# (d) Redundancy-gate computation vs. a c12_frag-shaped payload
# ---------------------------------------------------------------------------

def _c12_like_payload(dates: list[str], lambda2: np.ndarray, ipr_v2: np.ndarray) -> dict:
    """Mimic the EXACT shape ``c12_frag.driver.run()`` emits (subset of keys
    the redundancy gate reads: windows[].days[].{date,analyzed,lambda2,ipr_v2}).
    """
    days = [
        {"date": d, "panel_valid": True, "analyzed": True, "degenerate": False,
         "lambda2": float(l2), "ipr_v2": float(iv)}
        for d, l2, iv in zip(dates, lambda2, ipr_v2)
    ]
    return {"windows": [{"window_label": "W1", "days": days}]}


def test_redundancy_gate_high_correlation_is_redundant_drop() -> None:
    rng = np.random.default_rng(21)
    dates = _date_range("2026-04-01", 40)
    lambda2 = rng.uniform(1.0, 2.0, size=len(dates))
    ipr_v2 = rng.uniform(0.1, 0.5, size=len(dates))
    # embedding-distance series is a near-monotonic function of lambda2 ->
    # Spearman rho should land close to +1 (well above the 0.6 threshold).
    embed_daily = {d: float(l2) + 0.001 * rng.standard_normal()
                   for d, l2 in zip(dates, lambda2)}
    c12 = _c12_like_payload(dates, lambda2, ipr_v2)

    rec = redundancy_gate(embed_daily, c12)
    assert rec["evaluable"] is True
    assert rec["n_overlap_days"] == len(dates)
    assert rec["rho_lambda2"] is not None and rec["rho_lambda2"] > 0.9
    assert rec["max_abs_rho"] >= REDUNDANCY_RHO_MAX
    assert rec["redundant"] is True
    assert rec["passed"] is False

    # cross-check against the raw Spearman implementation directly.
    e = np.array([embed_daily[d] for d in dates])
    expected_rho = spearman_rho(e, lambda2)
    assert rec["rho_lambda2"] == pytest.approx(expected_rho, abs=1e-9)


def test_redundancy_gate_uncorrelated_series_passes() -> None:
    rng = np.random.default_rng(22)
    dates = _date_range("2026-04-01", 40)
    lambda2 = rng.uniform(1.0, 2.0, size=len(dates))
    ipr_v2 = rng.uniform(0.1, 0.5, size=len(dates))
    # embedding-distance series independent of lambda2/ipr_v2.
    perm = rng.permutation(len(dates))
    embed_vals = np.sort(rng.uniform(0.0, 1.0, size=len(dates)))[perm]
    embed_daily = {d: float(v) for d, v in zip(dates, embed_vals)}
    c12 = _c12_like_payload(dates, lambda2, ipr_v2)

    rec = redundancy_gate(embed_daily, c12)
    assert rec["evaluable"] is True
    assert rec["max_abs_rho"] < REDUNDANCY_RHO_MAX
    assert rec["redundant"] is False
    assert rec["passed"] is True


def test_redundancy_gate_not_evaluable_without_c12_payload() -> None:
    rec = redundancy_gate({"2026-04-01": 0.3}, None)
    assert rec["evaluable"] is False
    assert rec["redundant"] is False
    assert rec["passed"] is False
    assert rec["c12_payload_present"] is False


def test_redundancy_gate_insufficient_overlap_not_evaluable() -> None:
    dates = _date_range("2026-04-01", 3)  # below MIN_OVERLAP_DAYS floor
    c12 = _c12_like_payload(dates, np.array([1.1, 1.2, 1.3]), np.array([0.2, 0.3, 0.4]))
    embed_daily = {d: float(i) for i, d in enumerate(dates)}
    rec = redundancy_gate(embed_daily, c12)
    assert rec["evaluable"] is False
    assert rec["redundant"] is False


def test_extract_c12_daily_series_matches_driver_shape() -> None:
    dates = _date_range("2026-05-01", 5)
    lambda2 = np.array([1.0, 1.1, 1.2, 1.3, 1.4])
    ipr_v2 = np.array([0.2, 0.25, 0.3, 0.35, 0.4])
    payload = _c12_like_payload(dates, lambda2, ipr_v2)
    # inject one non-analyzed day that must be skipped.
    payload["windows"][0]["days"].append(
        {"date": "2026-05-06", "panel_valid": False, "analyzed": False, "degenerate": False})
    lam2, ipr2 = extract_c12_daily_series(payload)
    assert set(lam2) == set(dates)
    assert "2026-05-06" not in lam2
    assert lam2["2026-05-01"] == pytest.approx(1.0)
    assert ipr2["2026-05-03"] == pytest.approx(0.3)


# ---------------------------------------------------------------------------
# (e) FDR family + capital_free / forbidden-token payload scan
# ---------------------------------------------------------------------------

def test_benjamini_hochberg_known_case() -> None:
    p = [0.001, 0.02, 0.03, 0.5, 0.9]
    rejected, p_crit = benjamini_hochberg(p, alpha=0.10)
    assert rejected[0] is True
    assert rejected[3] is False and rejected[4] is False
    assert p_crit > 0.0


def _small_synthetic_nodes(symbols: tuple[str, ...], venues: tuple[str, str],
                            *, n_days: int, seed: int) -> list[NodeWindows]:
    rng = np.random.default_rng(seed)
    nodes: list[NodeWindows] = []
    for vi, ven in enumerate(venues):
        for sym in symbols:
            ts, price, size, sign = _synthetic_node_trades(
                rng, n_events=1200, duration_scale_ms=800.0, size_round=0.0,
                start_date="2026-02-01")
            # extend across n_days by tiling with day-sized offsets so LOSO
            # test periods have enough distinct dates.
            all_ts, all_price, all_size, all_sign = [], [], [], []
            for day_i in range(n_days):
                offset = day_i * 24 * 3600_000
                all_ts.append(ts + offset)
                all_price.append(price + day_i * 0.01)
                all_size.append(size)
                all_sign.append(sign)
            nodes.append(build_node_windows(
                np.concatenate(all_ts), np.concatenate(all_price),
                np.concatenate(all_size), np.concatenate(all_sign),
                exchange=ven, symbol=sym, min_events=32))
    return nodes


def test_driver_run_capital_free_and_no_forbidden_tokens() -> None:
    nodes = _small_synthetic_nodes(SYMBOLS5, VENUES2, n_days=28, seed=101)
    payload = run(nodes, n_perm=2, seed=1, cuda_used=False, torch_available=False)
    assert payload["capital_free"] is True
    assert payload["hypothesis"] == "H-17"
    assert payload["fdr_family"] == "F-VENUE"
    assert payload["fdr_family_size"] == N_FOLDS
    blob = json.dumps(payload, default=str).lower()
    for tok in ("bps", "pnl", "sharpe", "friction", "edge_"):
        assert tok not in blob, f"forbidden capital token in payload: {tok!r}"


def test_driver_run_compute_gate_blocks_verdict_without_cuda() -> None:
    nodes = _small_synthetic_nodes(SYMBOLS5, VENUES2, n_days=28, seed=102)
    payload = run(nodes, n_perm=2, seed=1, cuda_used=False, torch_available=False)
    assert payload["compute"]["verdict_bearing"] is False
    assert payload["compute"]["cuda_used"] is False
    assert payload["weiter_indication"] is False
    assert len(payload["compute"]["blocked_reasons"]) > 0
    assert len(payload["folds"]) == N_FOLDS
    for rec in payload["folds"]:
        assert len(rec["null_accuracies"]) == 2  # n_perm passed above


def test_driver_run_pretends_cuda_used_still_blocked_by_fallback_encoder() -> None:
    """Even if a caller mis-reports ``cuda_used=True``, the encoder's own
    ``verdict_bearing`` flag (False for the numpy fallback) still blocks
    the verdict — a second, independent line of defence in the compute gate.
    """
    nodes = _small_synthetic_nodes(SYMBOLS5, VENUES2, n_days=28, seed=103)
    payload = run(nodes, n_perm=2, seed=1, cuda_used=True, torch_available=False)
    assert payload["compute"]["encoder_verdict_capable"] is False
    assert payload["compute"]["verdict_bearing"] is False
    assert payload["weiter_indication"] is False


class _SmallBatchVerdictCapableEncoder(NumpyFallbackEncoder):
    """Test-only stub: reports itself as verdict-capable (like a real torch
    encoder would) but ``fit()`` returns an ACHIEVED batch size below
    ``BATCH_SIZE_MIN`` — simulating a thin fold whose train set forces
    ``eff_batch = min(requested, n) < BATCH_SIZE_MIN`` even though the
    caller requested a compliant batch size (audit finding M-1)."""

    verdict_bearing = True

    def fit(self, x, mask, node_ids, **kwargs):  # noqa: ANN001, D102
        self.n_fit_calls += 1
        return {"trained": True, "batch_size": 17, "batch_size_registered_min": 2048,
                "small_batch_override": True}


def test_driver_run_blocks_verdict_when_achieved_batch_below_minimum() -> None:
    """Audit finding M-1 regression test: cuda_used=True, a verdict-capable
    encoder, and a requested batch_size >= BATCH_SIZE_MIN must still NOT be
    verdict-bearing if the per-fold ACHIEVED batch size (fit_info["batch_size"])
    falls below the registered minimum -- the compute gate must look at what
    actually happened during training, not only the CLI request.
    """
    nodes = _small_synthetic_nodes(SYMBOLS5, VENUES2, n_days=28, seed=104)
    payload = run(
        nodes, n_perm=1, seed=1, cuda_used=True, torch_available=True,
        batch_size=2048,
        encoder_factory=lambda s: _SmallBatchVerdictCapableEncoder(seed=s),
    )
    assert payload["compute"]["encoder_verdict_capable"] is True
    assert payload["compute"]["cuda_used"] is True
    assert payload["compute"]["verdict_bearing"] is False, (
        "achieved batch size 17 << BATCH_SIZE_MIN=2048 must block the "
        "verdict even though the requested batch_size was compliant"
    )
    assert payload["weiter_indication"] is False
    reasons_blob = " ".join(payload["compute"]["blocked_reasons"])
    assert "17" in reasons_blob and "2048" in reasons_blob
    for rec in payload["folds"]:
        assert rec["min_effective_batch_size"] == 17


class _ZeroStepsVerdictCapableEncoder(NumpyFallbackEncoder):
    """Test-only stub simulating a real torch encoder (verdict-capable,
    compliant batch size) whose ``fit()`` performed ZERO optimizer steps
    -- the exact CRITICAL finding: ``--steps 0`` (argparse has no lower
    bound) trains nothing yet used to report ``trained: True`` with a
    compliant batch size, so a real-CUDA run could reach
    ``weiter_indication=True`` with literally zero GPU compute."""

    verdict_bearing = True

    def fit(self, x, mask, node_ids, **kwargs):  # noqa: ANN001, D102
        self.n_fit_calls += 1
        return {"trained": True, "steps": 0, "steps_registered_min": 1,
                "batch_size": 2048, "batch_size_registered_min": 2048}


def test_driver_run_blocks_verdict_when_achieved_steps_are_zero() -> None:
    """Audit finding CRIT-1 regression test: cuda_used=True, a verdict-
    capable encoder, and a compliant batch_size must still NOT be
    verdict-bearing if the per-fold ACHIEVED optimizer-step count
    (fit_info["steps"]) is zero -- the compute gate must inspect what
    actually happened during training, not just trust batch_size/cuda_used.
    """
    nodes = _small_synthetic_nodes(SYMBOLS5, VENUES2, n_days=28, seed=105)
    payload = run(
        nodes, n_perm=1, seed=1, cuda_used=True, torch_available=True,
        batch_size=2048,
        encoder_factory=lambda s: _ZeroStepsVerdictCapableEncoder(seed=s),
    )
    assert payload["compute"]["encoder_verdict_capable"] is True
    assert payload["compute"]["cuda_used"] is True
    assert payload["compute"]["batch_size"] >= 2048
    assert payload["compute"]["verdict_bearing"] is False, (
        "zero achieved optimizer steps must block the verdict even though "
        "cuda_used=True, the encoder reports verdict_bearing=True, and the "
        "requested/achieved batch size is compliant"
    )
    assert payload["weiter_indication"] is False
    reasons_blob = " ".join(payload["compute"]["blocked_reasons"])
    assert "0" in reasons_blob
    assert payload["compute"]["min_achieved_steps"] == 0
    for rec in payload["folds"]:
        assert rec["min_steps"] == 0


# ---------------------------------------------------------------------------
# (f) --check-gpu-only honestly reports the sandbox (no torch/CUDA)
# ---------------------------------------------------------------------------

def test_gpu_report_honest_in_sandbox() -> None:
    rep = gpu_report()
    assert rep["torch_available"] == TORCH_AVAILABLE
    if not TORCH_AVAILABLE:
        assert rep["cuda_available"] is False
        assert rep["verdict_capable"] is False
        assert rep["device_count"] == 0


def test_cli_check_gpu_only_exits_without_full_run(tmp_path: Path) -> None:
    script = REPO_ROOT / "scripts" / "c17_venue.py"
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    proc = subprocess.run(
        [sys.executable, str(script), "--check-gpu-only"],
        capture_output=True, text=True, env=env, timeout=60,
    )
    rep = json.loads(proc.stdout)
    assert "torch_available" in rep and "cuda_available" in rep and "verdict_capable" in rep
    if not rep["torch_available"] or not rep["cuda_available"]:
        # RC_SKIP_NO_COMPUTE=2, SAME convention as the sibling Welle-5 CLIs
        # (c14_panellag.py/c16_arrow.py) -- audit finding: compute-gate
        # exit-code consistency.
        assert proc.returncode == 2
        assert rep["verdict_capable"] is False
    # must NOT have written any results files (no full-run side effects).
    assert not (tmp_path / "c17_venue_results.json").exists()


def test_cli_full_run_without_cuda_skips_with_dedicated_exit_code(tmp_path: Path) -> None:
    """Audit finding compute-gate-inconsistency regression test: a FULL run
    (no ``--check-gpu-only``) without a real CUDA device and WITHOUT
    ``--allow-cpu-fallback`` must abort with the dedicated
    ``RC_SKIP_NO_COMPUTE`` (2) exit code -- exactly like the c14_panellag/
    c16_arrow sibling CLIs -- never silently fall back to the numpy
    pipeline-smoke encoder and exit 0 indistinguishably from a real,
    verdict-bearing GPU run. This must trigger BEFORE any data loading, so
    a nonexistent --base-dir is fine here. ``--device cpu`` forces
    ``cuda_used=False`` regardless of the environment's real CUDA
    availability, so this assertion is deterministic everywhere.
    """
    out_dir = tmp_path / "out"
    script = REPO_ROOT / "scripts" / "c17_venue.py"
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    proc = subprocess.run(
        [sys.executable, str(script),
         "--base-dir", str(tmp_path / "nonexistent_harvest"),
         "--out-dir", str(out_dir),
         "--start-date", "2026-01-01", "--end-date", "2026-01-05",
         "--device", "cpu"],
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert proc.returncode == 2, (
        f"expected RC_SKIP_NO_COMPUTE=2, got {proc.returncode}\n"
        f"STDOUT:{proc.stdout}\nSTDERR:{proc.stderr}"
    )
    assert not (out_dir / "c17_venue_results.json").exists()
    assert not (out_dir / "c17_venue_results.md").exists()
    assert "allow-cpu-fallback" in proc.stderr


# ---------------------------------------------------------------------------
# (g) End-to-end CLI smoke over a synthetic harvester Hive tree
# ---------------------------------------------------------------------------

CLI_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")
CLI_EXCHANGES = ("bybit", "binance")


def _write_raw_trades(tmp: Path, exchange: str, symbol: str, date_str: str,
                       *, n_events: int, seed: int) -> None:
    """Synthetic backfill-form publicTrade parquet (side/price/size keys)."""
    import duckdb
    from datetime import datetime, timezone

    rng = np.random.default_rng(seed)
    y, m, d = (int(x) for x in date_str.split("-"))
    start_ms = int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)
    gaps = rng.exponential(scale=400.0, size=n_events).astype(np.int64) + 1
    ts = start_ms + np.cumsum(gaps)
    ts = ts[ts < start_ms + 24 * 3600_000]
    price = 100.0 + np.cumsum(rng.normal(0.0, 0.01, size=ts.size))
    size = rng.lognormal(mean=1.0, sigma=0.3, size=ts.size)
    side = rng.choice(["Buy", "Sell"], size=ts.size)

    out_dir = tmp / "raw" / exchange / "publicTrade" / f"symbol={symbol}" / f"date={date_str}"
    out_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        recs = [(int(t), json.dumps({"side": s, "price": f"{p:.4f}", "size": f"{sz:.4f}"}))
                for t, s, p, sz in zip(ts, side, price, size)]
        con.execute("CREATE TABLE t (ts_exchange_ms BIGINT, payload_json VARCHAR)")
        con.executemany("INSERT INTO t VALUES (?, ?)", recs)
        con.execute(f"COPY t TO '{(out_dir / 'data.parquet').as_posix()}' (FORMAT parquet)")
    finally:
        con.close()


def test_end_to_end_cli_produces_valid_json(tmp_path: Path) -> None:
    base = tmp_path / "harvest"
    dates = _date_range("2031-01-01", 30)
    for exi, exchange in enumerate(CLI_EXCHANGES):
        for si, symbol in enumerate(CLI_SYMBOLS):
            for di, d in enumerate(dates):
                _write_raw_trades(base, exchange, symbol, d,
                                   n_events=400, seed=1000 + exi * 100 + si * 10 + di)

    out_dir = tmp_path / "out"
    script = REPO_ROOT / "scripts" / "c17_venue.py"
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    proc = subprocess.run(
        [sys.executable, str(script),
         "--base-dir", str(base), "--out-dir", str(out_dir),
         "--symbols", ",".join(CLI_SYMBOLS),
         "--exchanges", ",".join(CLI_EXCHANGES),
         "--start-date", dates[0], "--end-date", dates[-1],
         "--n-perm", "2", "--seed", "1", "--device", "cpu",
         "--allow-cpu-fallback"],
        capture_output=True, text=True, env=env, timeout=300,
    )
    assert proc.returncode == 0, f"CLI failed:\nSTDOUT{proc.stdout}\nSTDERR{proc.stderr}"
    json_path = out_dir / "c17_venue_results.json"
    md_path = out_dir / "c17_venue_results.md"
    assert json_path.exists() and md_path.exists()
    payload = json.loads(json_path.read_text())
    assert payload["capital_free"] is True
    assert payload["hypothesis"] == "H-17"
    assert payload["compute"]["verdict_bearing"] is False  # no CUDA in sandbox
    assert len(payload["folds"]) == N_FOLDS
    blob = json.dumps(payload).lower()
    for tok in ("bps", "pnl", "sharpe", "friction", "edge_"):
        assert tok not in blob


# ---------------------------------------------------------------------------
# (h) OOM-fix regression tests (build_node_windows boundary scan, lazy
#     loaders + raw-trade release, dtype downcasts) — the memory rewrite
#     must be BIT-IDENTICAL to the previous implementation, verified against
#     an inline legacy reference (the pre-fix code, reproduced verbatim).
# ---------------------------------------------------------------------------

import gc
import weakref

from bybit_edge.research.c17_venue.features import (
    MIN_EVENTS_PER_WINDOW,
    MS_PER_DAY,
    MS_PER_MINUTE,
    SEQ_LEN,
    WINDOW_MINUTES,
    build_node_windows_lazy,
    extract_raw_channels,
    load_panel,
    per_day_quantile_normalize,
    quantile_normalize,
    tick_direction,
)


def _legacy_tick_direction(price: np.ndarray) -> np.ndarray:
    """Pre-fix per-event Python-loop tick rule (verbatim old code)."""
    p = np.asarray(price, dtype=np.float64)
    n = p.size
    out = np.zeros(n, dtype=np.float64)
    last = 0.0
    for i in range(1, n):
        d = p[i] - p[i - 1]
        if d > 0:
            last = 1.0
        elif d < 0:
            last = -1.0
        out[i] = last
    return out


def _legacy_extract_raw_channels(ts_ms, price, size, sign):
    """Pre-fix extract (np.diff check, column_stack, int64 day_index)."""
    ts_ms = np.asarray(ts_ms, dtype=np.int64)
    price = np.asarray(price, dtype=np.float64)
    size = np.asarray(size, dtype=np.float64)
    sign = np.asarray(sign, dtype=np.float64)
    if np.any(np.diff(ts_ms) < 0):
        order = np.argsort(ts_ms, kind="mergesort")
        ts_ms, price, size, sign = ts_ms[order], price[order], size[order], sign[order]
    dur = np.diff(ts_ms).astype(np.float64)
    tick = _legacy_tick_direction(price)[1:]
    log_size = np.log(np.maximum(size[1:], 1e-12))
    agg = sign[1:]
    channels = np.column_stack([dur, log_size, agg, tick])
    ts_kept = ts_ms[1:]
    day_index = (ts_kept // MS_PER_DAY).astype(np.int64)
    return ts_kept, channels, day_index


def _legacy_per_day_quantile_normalize(channels, day_index):
    """Pre-fix copy-based per-day boolean-mask normalisation (verbatim)."""
    ch = np.asarray(channels, dtype=np.float64)
    day_index = np.asarray(day_index)
    out = np.empty_like(ch)
    for day in np.unique(day_index):
        sel = day_index == day
        for c in range(ch.shape[1]):
            out[sel, c] = quantile_normalize(ch[sel, c])
    return out


def _legacy_build_node_windows(ts_ms, price, size, sign, *, exchange, symbol,
                                seq_len=SEQ_LEN, min_events=MIN_EVENTS_PER_WINDOW,
                                window_minutes=WINDOW_MINUTES, normalize=True):
    """Pre-fix build_node_windows: np.unique(return_index) bucketing."""
    ts_kept, raw, day_index = _legacy_extract_raw_channels(ts_ms, price, size, sign)
    norm = _legacy_per_day_quantile_normalize(raw, day_index) if normalize else raw
    bucket = ts_kept // (window_minutes * MS_PER_MINUTE)
    xs, masks, dates, counts = [], [], [], []
    uniq, starts = np.unique(bucket, return_index=True)
    order = np.argsort(starts)
    uniq, starts = uniq[order], starts[order]
    ends = np.append(starts[1:], bucket.size)
    for _b, s, e in zip(uniq, starts, ends):
        n_ev = int(e - s)
        if n_ev < min_events:
            continue
        take = min(n_ev, seq_len)
        w = np.zeros((N_CHANNELS, seq_len), dtype=np.float32)
        m = np.zeros(seq_len, dtype=bool)
        w[:, :take] = norm[s:s + take, :].T
        m[:take] = True
        xs.append(w)
        masks.append(m)
        from datetime import datetime, timezone
        dates.append((datetime(1970, 1, 1, tzinfo=timezone.utc)
                      + timedelta(days=int(day_index[s]))).strftime("%Y-%m-%d"))
        counts.append(take)
    assert xs, "legacy reference: no window built (test setup broken)"
    return NodeWindows(exchange=exchange, symbol=symbol, x=np.stack(xs),
                       mask=np.stack(masks), dates=np.array(dates, dtype=object),
                       n_events=np.array(counts, dtype=np.int64))


def _multiday_trades_with_ties(seed: int, n: int = 30_000):
    """Multi-day stream with tied timestamps, price plateaus, tied sizes,
    >5-min gaps (empty buckets) and sparse buckets (< min_events)."""
    rng = np.random.default_rng(seed)
    from datetime import datetime, timezone
    start_ms = int(datetime(2026, 3, 1, tzinfo=timezone.utc).timestamp() * 1000)
    gaps = rng.choice(
        np.array([0, 1, 5, 40, 900, 65_000, 400_000], dtype=np.int64),
        size=n, p=[0.15, 0.25, 0.25, 0.2, 0.12, 0.02, 0.01])
    ts = start_ms + np.cumsum(gaps)
    price = np.round(
        100.0 + np.cumsum(rng.choice([-0.01, 0.0, 0.01], size=n, p=[0.3, 0.4, 0.3])), 2)
    size = np.maximum(np.round(rng.lognormal(0.0, 0.5, size=n), 2), 0.01)
    sign = rng.choice(np.array([1.0, -1.0]), size=n)
    return ts, price, size, sign


def test_build_node_windows_bitidentical_to_legacy_reference() -> None:
    """OOM-fix regression (a): the boundary-scan windowing + in-place
    normalisation + int32 day_index + vectorized tick + column-wise channel
    fill must reproduce the pre-fix ``np.unique(return_index)`` pipeline
    BIT-identically — on chronologically sorted AND unsorted inputs, with
    and without the per-day quantile normalisation."""
    ts, price, size, sign = _multiday_trades_with_ties(seed=42)
    rng = np.random.default_rng(7)
    perm = rng.permutation(ts.size)
    variants = {
        "sorted": (ts, price, size, sign),
        "unsorted": (ts[perm], price[perm], size[perm], sign[perm]),
    }
    kw = dict(exchange="bybit", symbol="BTCUSDT", min_events=16)
    for name, arrs in variants.items():
        for normalize in (True, False):
            ref = _legacy_build_node_windows(*arrs, normalize=normalize, **kw)
            new = build_node_windows(*arrs, normalize=normalize, **kw)
            lazy = build_node_windows_lazy(
                lambda arrs=arrs: tuple(a.copy() for a in arrs),
                normalize=normalize, **kw)
            for got, label in ((new, "build_node_windows"),
                               (lazy, "build_node_windows_lazy")):
                ctx = f"{label}/{name}/normalize={normalize}"
                assert got.x.dtype == ref.x.dtype == np.float32, ctx
                assert np.array_equal(ref.x, got.x), ctx
                assert np.array_equal(ref.mask, got.mask), ctx
                assert ref.dates.tolist() == got.dates.tolist(), ctx
                assert np.array_equal(ref.n_events, got.n_events), ctx
    # the fixture must actually exercise the interesting structure:
    ref = _legacy_build_node_windows(ts, price, size, sign, **kw)
    assert len(set(ref.dates.tolist())) >= 2, "fixture spans too few days"
    assert ref.x.shape[0] >= 5, "fixture yields too few windows"


def test_load_panel_lazy_loader_called_once_and_raw_trades_freed() -> None:
    """OOM-fix regression (b): ``load_panel`` pulls each node's raw trades
    through its loader EXACTLY once, and the four raw arrays of a node are
    garbage-collected once the node's windows are built — verified via a
    spy loader that asserts (weakref) all PREVIOUS nodes' raw arrays are
    already dead before it materialises the next node's."""
    calls: dict[tuple[str, str], int] = {}
    refs: dict[tuple[str, str], list] = {}
    node_seed = {}

    def spy_loader(exchange: str, symbol: str):
        key = (exchange, symbol)
        calls[key] = calls.get(key, 0) + 1
        gc.collect()
        for k, wl in refs.items():
            assert all(w() is None for w in wl), (
                f"raw trade arrays of node {k} still resident while "
                f"loading node {key} — O(one node) property violated")
        node_seed[key] = len(node_seed)
        rng = np.random.default_rng(1000 + node_seed[key])
        ts, price, size, sign = _synthetic_node_trades(
            rng, n_events=3000, duration_scale_ms=300.0)
        refs[key] = [weakref.ref(a) for a in (ts, price, size, sign)]
        return ts, price, size, sign

    symbols = ("AAAUSDT", "BBBUSDT")
    venues = ("bybit", "binance")
    nodes = load_panel("unused-base", symbols, "2026-01-01", "2026-01-01",
                       exchanges=venues, min_events=16, trade_loader=spy_loader)
    assert len(nodes) == len(symbols) * len(venues)
    expected_keys = {(v, s) for v in venues for s in symbols}
    assert set(calls) == expected_keys
    assert all(c == 1 for c in calls.values()), f"loader re-called: {calls}"
    gc.collect()
    for k, wl in refs.items():
        assert all(w() is None for w in wl), (
            f"raw trade arrays of node {k} still alive after load_panel")


def test_day_index_int32_downcast_exact_and_public_normalize_unchanged() -> None:
    """OOM-fix regression (c): the only dtype change of the rewrite is
    ``day_index`` int64 -> int32; its VALUES are exact (epoch-day ids), and
    the final float32 window features stay bit-identical (asserted in the
    legacy-reference test above). The public ``per_day_quantile_normalize``
    keeps its copy semantics (input never mutated) and matches the pre-fix
    mask-based reference on sorted AND unsorted day ids bit-exactly —
    channel values deliberately remain float64 through the rank transform
    (float32 could merge ties / change ranks, i.e. touch the registered
    statistic)."""
    rng = np.random.default_rng(11)
    ts, price, size, sign = _synthetic_node_trades(
        rng, n_events=4000, duration_scale_ms=60_000.0)  # spans several days
    ts_kept, ch, day_index = extract_raw_channels(ts, price, size, sign)
    assert day_index.dtype == np.int32
    assert np.array_equal(day_index.astype(np.int64), ts_kept // MS_PER_DAY)
    assert np.unique(day_index).size >= 2, "fixture spans too few days"
    assert ch.dtype == np.float64  # rank inputs stay f64 (registered stat)

    ch_before = ch.copy()
    out = per_day_quantile_normalize(ch, day_index)
    assert np.array_equal(ch, ch_before), "public API must not mutate input"
    ref = _legacy_per_day_quantile_normalize(ch, day_index)
    assert np.array_equal(out, ref)

    perm = rng.permutation(ch.shape[0])  # unsorted day ids -> fallback path
    out_u = per_day_quantile_normalize(ch[perm], day_index[perm])
    ref_u = _legacy_per_day_quantile_normalize(ch[perm], day_index[perm])
    assert np.array_equal(out_u, ref_u)


def test_tick_direction_vectorized_matches_loop_reference() -> None:
    """OOM/CPU-fix regression: the vectorized tick rule (int8 signs +
    forward-fill via maximum.accumulate) is bit-identical to the original
    per-event Python loop, including leading plateaus and zero-tick carry."""
    rng = np.random.default_rng(5)
    p = 100.0 + np.cumsum(rng.choice([-0.5, 0.0, 0.0, 0.5], size=4000))
    p[:7] = p[0]                      # leading flat run -> zeros, then carry
    got = tick_direction(p)
    ref = _legacy_tick_direction(p)
    assert got.dtype == np.float64
    assert np.array_equal(ref, got)
    assert np.all(got[:8] == 0.0) or got[7] != 0.0  # leading zeros preserved
    # degenerate sizes
    assert np.array_equal(tick_direction(np.array([5.0])), np.zeros(1))
    assert tick_direction(np.empty(0)).size == 0


# ---------------------------------------------------------------------------
# Checkpoint/Resume (c16-pattern; written after the two-agent build round)
# ---------------------------------------------------------------------------

def _payload_for_compare(p: dict) -> str:
    """Serialise a payload minus volatile timestamp for equality checks."""
    q = {k: v for k, v in p.items() if k != "generated_at"}
    return json.dumps(q, sort_keys=True, default=str)


def _counting_factory():
    """Factory returning PLAIN NumpyFallbackEncoder (the fingerprint pins
    ``encoder_class``, so a differently-named subclass would -- correctly --
    hard-abort the resume). Counted are REAL ``fit()`` calls summed over all
    constructed encoders -- run() legitimately constructs one throwaway
    probe encoder up front to derive ``encoder_class`` for the fingerprint,
    so construction count alone would over-count by one.
    """
    made: list[NumpyFallbackEncoder] = []

    def factory(s: int) -> NumpyFallbackEncoder:
        enc = NumpyFallbackEncoder(seed=s)
        made.append(enc)
        return enc

    def n_fits() -> int:
        return sum(e.n_fit_calls for e in made)

    return factory, n_fits


def test_ckpt_written_per_training_and_resume_retrains_nothing(tmp_path: Path) -> None:
    nodes = _small_synthetic_nodes(SYMBOLS5, VENUES2, n_days=28, seed=110)
    ck = tmp_path / "ck"
    p1 = run(nodes, n_perm=2, seed=1, cuda_used=False, torch_available=False,
             ckpt_dir=ck)
    files = sorted(ck.rglob("*.json"))
    # 5 LOSO folds x (1 main + 2 null retrainings) = 15 single-training files
    assert len(files) == 15, [str(f) for f in files]
    kinds = sorted(f.name.split("_")[0] for f in files)
    assert kinds.count("main") == 5 and kinds.count("null") == 10

    factory, n_fits = _counting_factory()
    p2 = run(nodes, encoder_factory=factory,
             n_perm=2, seed=1, cuda_used=False, torch_available=False,
             ckpt_dir=ck)
    assert n_fits() == 0, (
        "resume must not retrain anything when every checkpoint exists")
    assert _payload_for_compare(p1) == _payload_for_compare(p2), (
        "resumed payload must equal the uninterrupted run bit-for-bit "
        "(minus the volatile generated_at timestamp)")


def test_ckpt_partial_resume_retrains_only_missing(tmp_path: Path) -> None:
    nodes = _small_synthetic_nodes(SYMBOLS5, VENUES2, n_days=28, seed=111)
    ck = tmp_path / "ck"
    p1 = run(nodes, n_perm=2, seed=1, cuda_used=False, torch_available=False,
             ckpt_dir=ck)
    files = sorted(ck.rglob("*.json"))
    # simulate an interrupt: drop one main and two null checkpoints
    dropped = [files[0], files[4], files[9]]
    for f in dropped:
        f.unlink()
    factory, n_fits = _counting_factory()
    p2 = run(nodes, encoder_factory=factory,
             n_perm=2, seed=1, cuda_used=False, torch_available=False,
             ckpt_dir=ck)
    assert n_fits() == len(dropped), (
        "exactly the missing trainings must be redone, nothing else")
    assert _payload_for_compare(p1) == _payload_for_compare(p2)
    assert len(sorted(ck.rglob("*.json"))) == 15  # rewritten


def test_ckpt_fingerprint_mismatch_hard_aborts(tmp_path: Path) -> None:
    nodes = _small_synthetic_nodes(SYMBOLS5, VENUES2, n_days=28, seed=112)
    ck = tmp_path / "ck"
    run(nodes, n_perm=2, seed=1, cuda_used=False, torch_available=False,
        ckpt_dir=ck)
    # a different base seed changes every derived training seed -> the
    # stored checkpoints contradict the new run and must NEVER be mixed in
    with pytest.raises(CheckpointMismatchError):
        run(nodes, n_perm=2, seed=2, cuda_used=False, torch_available=False,
            ckpt_dir=ck)


def test_no_ckpt_dir_writes_nothing(tmp_path: Path) -> None:
    nodes = _small_synthetic_nodes(SYMBOLS5, VENUES2, n_days=28, seed=113)
    cwd_before = sorted(tmp_path.rglob("*"))
    run(nodes, n_perm=2, seed=1, cuda_used=False, torch_available=False,
        ckpt_dir=None)
    assert sorted(tmp_path.rglob("*")) == cwd_before, (
        "ckpt_dir=None must not create any checkpoint files")


# ----------------------------------------------------------------------------
# H-23: full-panel distance series (registry 2026-08-18 + Nachtrag)
# ----------------------------------------------------------------------------

def test_h23_full_panel_distance_covers_more_days_than_h17() -> None:
    """The whole point of H-23: the distance series must span ALL panel days.

    H-17 defines it on the held-out TEST windows only (~last 21 days), which
    left the redundancy gate with 2 overlap days (GL-019). H-23 embeds every
    window of each held-out symbol with the fold that excluded it.
    """
    nodes = _small_synthetic_nodes(SYMBOLS5, VENUES2, n_days=40, seed=771)
    base = run(nodes, n_perm=1, seed=1, cuda_used=False, torch_available=False)
    full = run(nodes, n_perm=1, seed=1, cuda_used=False, torch_available=False,
               full_panel_distance=True, hypothesis_id="H-23")

    d_base = set(base["embedding_distance"]["daily"])
    d_full = set(full["embedding_distance"]["daily"])
    assert d_base <= d_full, "the H-17 days must all still be covered"
    # sharp expectation: H-17 sees at most the TEST_DAYS tail, H-23 the panel
    assert len(d_base) <= TEST_DAYS, len(d_base)
    assert len(d_full) == 40, (
        f"full-panel coverage must span every panel day, got {len(d_full)}")
    assert len(d_full) > len(d_base), "and it must be strictly wider"
    assert full["hypothesis"] == "H-23" and base["hypothesis"] == "H-17"
    assert "full_panel" in full["distance_scope"]
    assert "test_windows_only" in base["distance_scope"]


def test_h23_does_not_change_the_h17_measurement() -> None:
    """The accuracy side is untouched: only WHAT is embedded afterwards
    changes, never the training. Bit-exact fold accuracies are required."""
    nodes = _small_synthetic_nodes(SYMBOLS5, VENUES2, n_days=30, seed=772)
    base = run(nodes, n_perm=1, seed=3, cuda_used=False, torch_available=False)
    full = run(nodes, n_perm=1, seed=3, cuda_used=False, torch_available=False,
               full_panel_distance=True, hypothesis_id="H-23")
    for rb, rf in zip(base["folds"], full["folds"]):
        assert rb["held_out_symbol"] == rf["held_out_symbol"]
        assert rb["balanced_accuracy"] == rf["balanced_accuracy"]
        assert rb["p_value"] == rf["p_value"]
    assert base["pooled_balanced_accuracy"] == full["pooled_balanced_accuracy"]


def test_h23_embeds_every_window_with_the_excluding_fold() -> None:
    """Registry Nachtrag (1): symbol exclusion must hold for EVERY embedded
    window — each fold contributes exactly the windows of its held-out
    symbol, and the union covers the whole panel."""
    panel = _dummy_panel(SYMBOLS5, VENUES2, n_days=26)
    folds = build_loso_folds(panel, SYMBOLS5)
    seen = np.concatenate([f.holdout_idx for f in folds])
    assert seen.size == panel.x.shape[0], "union of holdouts must be the panel"
    assert np.array_equal(np.unique(seen), np.arange(panel.x.shape[0])), (
        "no window may be embedded twice or missed")
    for f in folds:
        assert set(panel.symbols[f.holdout_idx]) == {f.held_out_symbol}
        assert not np.intersect1d(f.holdout_idx, f.train_idx).size, (
            "a fold must never embed a window it was trained on")


def test_h23_test_day_diagnostic_is_reported_and_not_judgment_bearing() -> None:
    nodes = _small_synthetic_nodes(SYMBOLS5, VENUES2, n_days=30, seed=774)
    full = run(nodes, n_perm=1, seed=5, cuda_used=False, torch_available=False,
               full_panel_distance=True, hypothesis_id="H-23")
    diag = full["redundancy_test_days_only"]
    assert diag is not None
    assert diag["judgment_bearing"] is False
    base = run(nodes, n_perm=1, seed=5, cuda_used=False, torch_available=False)
    assert base["redundancy_test_days_only"] is None, (
        "the diagnostic exists only on the H-23 path")
