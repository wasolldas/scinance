"""Pipeline-mechanics tests for H-15 (C-15 trade-tape event grammar).

This sandbox has NEITHER torch NOR a GPU — only pipeline CORRECTNESS is
testable here (tokenisation incl. leak discipline, walk-forward fold/embargo
construction, the Markov baseline's statistical correctness, the
seasonality-preserving block-shuffle null, honest ``--check-gpu-only``
reporting, and the capital-free token scan). The actual transformer
training power is NOT exercised (no torch in this environment) — that is
exclusively a T3 LOCAL_LONG concern on the user's RTX machine.
"""
from __future__ import annotations

import gc
import json
import subprocess
import sys
import weakref
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.c15_grammar import driver as c15_driver
from bybit_edge.research.c15_grammar import markov_baseline as c15_markov
from bybit_edge.research.c15_grammar import stats as c15_stats
from bybit_edge.research.c15_grammar import tokenizer as c15_tok
from bybit_edge.research.c15_grammar import transformer as c15_transformer

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_SCRIPT = REPO_ROOT / "scripts" / "c15_grammar.py"


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------

def _iso_day(d: date) -> str:
    return d.isoformat()


def _day_grid(start: str, n: int) -> list[str]:
    d0 = date.fromisoformat(start)
    return [_iso_day(d0 + timedelta(days=i)) for i in range(n)]


def _epoch_day(iso: str) -> int:
    return (date.fromisoformat(iso) - date(1970, 1, 1)).days


_MS_PER_DAY = 86_400_000


def _make_stream(symbol: str, days: list[str], events_per_day: int, *,
                 seed: int = 0, size_scale: float = 1.0) -> c15_driver.EventStream:
    """Synthetic, deterministic multi-day trade stream (uniform intraday)."""
    rng = np.random.default_rng(seed)
    ts_list: list[np.ndarray] = []
    for d in days:
        base = _epoch_day(d) * _MS_PER_DAY
        offsets = np.sort(rng.integers(0, _MS_PER_DAY, size=events_per_day))
        ts_list.append(base + offsets)
    ts = np.concatenate(ts_list).astype(np.int64)
    n = ts.size
    price = 100.0 + np.cumsum(rng.normal(0, 0.01, size=n))
    price = np.clip(price, 1.0, None)
    size = rng.lognormal(mean=0.0, sigma=1.0, size=n) * size_scale
    side = rng.integers(0, 2, size=n).astype(np.int64)
    return c15_driver.EventStream(symbol=symbol, ts_ms=ts, price=price, size=size, side=side)


def _make_fold(train_days: list[str], test_days: list[str],
               embargo: list[str] | None = None) -> c15_stats.Fold:
    return c15_stats.Fold(
        index=0, train_days=tuple(train_days),
        embargo=tuple(embargo or []), test_days=tuple(test_days),
    )


FORBIDDEN_TOKENS = ("bps", "edge_", "friction", "pnl", "sharpe", "tradab", " roi ")


# ----------------------------------------------------------------------------
# (a) Tokenisation correctness + leak test (quantile edges TRAIN-fold only)
# ----------------------------------------------------------------------------

class TestTokenizer:
    def test_derive_event_features_known_values(self) -> None:
        ts = np.array([0, 1000, 1500, 4500], dtype=np.int64)
        price = np.array([100.0, 100.0, 101.0, 100.5], dtype=np.float64)
        size = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
        side = np.array([1, 0, 1, 0], dtype=np.int64)  # Buy, Sell, Buy, Sell
        feats = c15_tok.derive_event_features(ts, price, size, side)
        np.testing.assert_allclose(feats["signed_size"], [1.0, -2.0, 3.0, -4.0])
        # IAT: first=0, then 1000, 500, 3000 ms -> log1p
        np.testing.assert_allclose(
            feats["log_iat"], np.log1p([0, 1000, 500, 3000]), rtol=1e-10,
        )
        # tick_dir: event0 "up" by convention; event1 price flat (100->100,
        # carries forward "up"); event2 price rises (100->101) -> up;
        # event3 price falls (101->100.5) -> down.
        np.testing.assert_array_equal(feats["tick_dir"], [1, 1, 1, 0])

    def test_fit_tokenizer_vocab_and_bucket_ranges(self) -> None:
        rng = np.random.default_rng(1)
        ssz = rng.normal(size=5000)
        lia = rng.normal(size=5000)
        spec = c15_tok.fit_tokenizer(ssz, lia)
        assert spec.vocab_size == c15_tok.VOCAB_BASE == 128
        side = rng.integers(0, 2, size=2000).astype(np.int64)
        ssz2 = rng.normal(size=2000)
        lia2 = rng.normal(size=2000)
        tokens = c15_tok.tokenize(spec, side, ssz2, lia2)
        assert tokens.dtype == np.int64
        assert tokens.min() >= 0
        assert tokens.max() < spec.vocab_size

    def test_tokenize_decompose_roundtrip(self) -> None:
        rng = np.random.default_rng(2)
        spec = c15_tok.fit_tokenizer(rng.normal(size=1000), rng.normal(size=1000))
        side = np.array([0, 1, 0, 1])
        ssz = np.array([-5.0, 5.0, 0.0, 100.0])
        lia = np.array([0.0, 1.0, 2.0, 10.0])
        tokens = c15_tok.tokenize(spec, side, ssz, lia)
        for i, t in enumerate(tokens):
            d = c15_tok.decompose_token(spec, int(t))
            assert d["side"] == int(side[i])

    def test_tickdir_vocab_extension(self) -> None:
        rng = np.random.default_rng(3)
        spec = c15_tok.fit_tokenizer(
            rng.normal(size=1000), rng.normal(size=1000), use_tick_direction=True,
        )
        assert spec.vocab_size == c15_tok.VOCAB_TICKDIR == 256
        side = np.array([0, 1])
        ssz = np.array([-1.0, 1.0])
        lia = np.array([0.0, 1.0])
        with pytest.raises(c15_tok.TokenizerError):
            c15_tok.tokenize(spec, side, ssz, lia)  # missing tick_dir
        tokens = c15_tok.tokenize(spec, side, ssz, lia, tick_dir=np.array([0, 1]))
        assert tokens.max() < 256

    def test_fit_tokenizer_rejects_empty(self) -> None:
        with pytest.raises(c15_tok.TokenizerError):
            c15_tok.fit_tokenizer(np.array([]), np.array([]))

    def test_leak_test_boundaries_fitted_train_fold_only(self) -> None:
        """CORE LEAK TEST: perturbing test-fold data must NEVER move edges."""
        train_days = _day_grid("2026-01-01", 10)
        test_days = _day_grid("2026-01-11", 5)
        fold = _make_fold(train_days, test_days)

        stream_a = _make_stream("BTCUSDT", train_days, 200, seed=11)
        stream_a_test = _make_stream("BTCUSDT", test_days, 200, seed=22, size_scale=1.0)
        # Build combined stream A: normal train + normal test.
        events_a = c15_driver.EventStream(
            symbol="BTCUSDT",
            ts_ms=np.concatenate([stream_a.ts_ms, stream_a_test.ts_ms]),
            price=np.concatenate([stream_a.price, stream_a_test.price]),
            size=np.concatenate([stream_a.size, stream_a_test.size]),
            side=np.concatenate([stream_a.side, stream_a_test.side]),
        )
        # Stream B: IDENTICAL train events, but test-fold events replaced
        # with wild outliers (1e6x size, huge IAT) — a leak would move the
        # quantile edges; correct code must be blind to this.
        stream_b_test = _make_stream("BTCUSDT", test_days, 200, seed=22, size_scale=1e6)
        events_b = c15_driver.EventStream(
            symbol="BTCUSDT",
            ts_ms=np.concatenate([stream_a.ts_ms, stream_b_test.ts_ms]),
            price=np.concatenate([stream_a.price, stream_b_test.price]),
            size=np.concatenate([stream_a.size, stream_b_test.size * 1e6]),
            side=np.concatenate([stream_a.side, stream_b_test.side]),
        )

        spec_a, train_tok_a, test_tok_a, _ = c15_driver.prepare_fold(events_a, fold)
        spec_b, train_tok_b, test_tok_b, _ = c15_driver.prepare_fold(events_b, fold)

        # Train-fold events identical -> tokenizer boundaries MUST be identical.
        assert spec_a.size_edges == spec_b.size_edges
        assert spec_a.iat_edges == spec_b.iat_edges
        np.testing.assert_array_equal(train_tok_a, train_tok_b)
        # Test-fold tokens legitimately differ (different underlying data),
        # but must still respect the SAME (train-fitted) vocab.
        assert test_tok_a.max() < spec_a.vocab_size
        assert test_tok_b.max() < spec_b.vocab_size
        # And the huge-outlier test stream must NOT have escaped the
        # frozen bucket edges (extreme values clip into the top bucket,
        # never crash, never grow the vocab).
        assert test_tok_b.max() < c15_tok.VOCAB_BASE


# ----------------------------------------------------------------------------
# (b) Purged walk-forward folds + 1-day embargo, no train/test overlap
# ----------------------------------------------------------------------------

class TestWalkForwardFolds:
    def test_four_folds_no_overlap_and_embargo_gap(self) -> None:
        days = _day_grid("2026-01-01", 100)
        folds = c15_stats.walk_forward_folds(days, n_folds=4, embargo_days=1)
        assert len(folds) == 4
        for f in folds:
            train_set = set(f.train_days)
            test_set = set(f.test_days)
            embargo_set = set(f.embargo)
            # no overlap anywhere
            assert train_set & test_set == set()
            assert train_set & embargo_set == set()
            assert test_set & embargo_set == set()
            # embargo is exactly 1 day (registry: 1-Tag-Embargo)
            assert len(f.embargo) == 1
            # calendar continuity: train ends, THEN embargo, THEN test
            last_train = date.fromisoformat(f.train_days[-1])
            embargo_day = date.fromisoformat(f.embargo[0])
            first_test = date.fromisoformat(f.test_days[0])
            assert embargo_day == last_train + timedelta(days=1)
            assert first_test == embargo_day + timedelta(days=1)
            # causal ordering
            assert last_train < embargo_day < first_test

    def test_expanding_train_window(self) -> None:
        days = _day_grid("2026-01-01", 100)
        folds = c15_stats.walk_forward_folds(days, n_folds=4, embargo_days=1)
        sizes = [len(f.train_days) for f in folds]
        assert sizes == sorted(sizes)  # strictly non-decreasing (expanding)
        assert sizes[0] < sizes[-1]

    def test_folds_cover_disjoint_test_segments(self) -> None:
        days = _day_grid("2026-01-01", 100)
        folds = c15_stats.walk_forward_folds(days, n_folds=4, embargo_days=1)
        all_test: list[str] = []
        for f in folds:
            all_test.extend(f.test_days)
        assert len(all_test) == len(set(all_test))  # no test day reused

    def test_grid_too_short_raises(self) -> None:
        days = _day_grid("2026-01-01", 5)
        with pytest.raises(c15_stats.FoldError):
            c15_stats.walk_forward_folds(days, n_folds=4, embargo_days=1)

    def test_unsorted_days_raises(self) -> None:
        days = _day_grid("2026-01-01", 100)
        days[0], days[1] = days[1], days[0]
        with pytest.raises(c15_stats.FoldError):
            c15_stats.walk_forward_folds(days, n_folds=4, embargo_days=1)

    def test_prepare_fold_no_event_overlap(self) -> None:
        """End-to-end: tokenised train/test events never share a day."""
        days = _day_grid("2026-01-01", 100)
        folds = c15_stats.walk_forward_folds(days, n_folds=4, embargo_days=1)
        events = _make_stream("ETHUSDT", days, 50, seed=5)
        for f in folds:
            spec, train_tok, test_tok, test_hours = c15_driver.prepare_fold(events, f)
            assert train_tok.size > 0
            assert test_tok.size > 0
            assert test_hours.size == test_tok.size


# ----------------------------------------------------------------------------
# (c) Markov-k baseline correctness on a KNOWN synthetic Markov process
# ----------------------------------------------------------------------------

class TestMarkovBaseline:
    @staticmethod
    def _stationary_entropy_rate(P: np.ndarray) -> float:
        """True entropy rate (nats) of an order-1 Markov chain with matrix P."""
        # power iteration for the stationary distribution
        pi = np.ones(P.shape[0]) / P.shape[0]
        for _ in range(10_000):
            pi_next = pi @ P
            if np.allclose(pi_next, pi, atol=1e-14):
                pi = pi_next
                break
            pi = pi_next
        h_rows = -np.sum(np.where(P > 0, P * np.log(P), 0.0), axis=1)
        return float(np.sum(pi * h_rows))

    @staticmethod
    def _simulate_markov1(P: np.ndarray, n: int, seed: int) -> np.ndarray:
        rng = np.random.default_rng(seed)
        v = P.shape[0]
        out = np.empty(n, dtype=np.int64)
        out[0] = rng.integers(0, v)
        for t in range(1, n):
            out[t] = rng.choice(v, p=P[out[t - 1]])
        return out

    def test_order1_markov_kt_recovers_true_entropy_rate(self) -> None:
        # A clearly non-uniform, non-trivial order-1 chain over 4 symbols.
        P = np.array([
            [0.70, 0.10, 0.10, 0.10],
            [0.10, 0.70, 0.10, 0.10],
            [0.10, 0.10, 0.70, 0.10],
            [0.10, 0.10, 0.10, 0.70],
        ])
        true_h = self._stationary_entropy_rate(P)
        tokens = self._simulate_markov1(P, 220_000, seed=7)
        train, test = tokens[:170_000], tokens[170_000:]

        m1 = c15_markov.MarkovKT(order=1, vocab_size=4).fit(train)
        ce1 = m1.cross_entropy(test)
        assert abs(ce1 - true_h) < 0.02, f"order-1 CE {ce1} vs true H {true_h}"

        # Order-0 (marginal-only) model MUST do materially worse: it cannot
        # see the strong diagonal dependency at all.
        m0 = c15_markov.MarkovKT(order=0, vocab_size=4).fit(train)
        ce0 = m0.cross_entropy(test)
        assert ce0 > ce1 + 0.05

    def test_interpolated_backoff_close_to_fixed_order(self) -> None:
        P = np.array([
            [0.70, 0.10, 0.10, 0.10],
            [0.10, 0.70, 0.10, 0.10],
            [0.10, 0.10, 0.70, 0.10],
            [0.10, 0.10, 0.10, 0.70],
        ])
        tokens = self._simulate_markov1(P, 220_000, seed=8)
        train, test = tokens[:170_000], tokens[170_000:]
        m1 = c15_markov.MarkovKT(order=1, vocab_size=4).fit(train)
        interp = c15_markov.InterpolatedMarkov(max_order=4, vocab_size=4).fit(train)
        ce1 = m1.cross_entropy(test)
        ce_interp = interp.cross_entropy(test)
        # interpolated k<=4 should be close to (not much worse than) the
        # true generating order (data has no order>1 structure to exploit).
        assert ce_interp < ce1 + 0.05

    def test_best_baseline_ce_picks_lowest(self) -> None:
        P = np.array([
            [0.70, 0.10, 0.10, 0.10],
            [0.10, 0.70, 0.10, 0.10],
            [0.10, 0.10, 0.70, 0.10],
            [0.10, 0.10, 0.10, 0.70],
        ])
        tokens = self._simulate_markov1(P, 60_000, seed=9)
        train, test = tokens[:45_000], tokens[45_000:]
        models = c15_markov.fit_all_baselines(train, vocab_size=4)
        name, ce, all_ces = c15_markov.best_baseline_ce(models, test)
        assert name in models
        assert ce == min(v for v in all_ces.values() if np.isfinite(v))

    def test_kt_unseen_context_degrades_to_uniform(self) -> None:
        # order=4 with tiny training data -> most test contexts unseen.
        rng = np.random.default_rng(4)
        train = rng.integers(0, 8, size=50)
        test = rng.integers(0, 8, size=200)
        m = c15_markov.MarkovKT(order=4, vocab_size=8).fit(train)
        ce = m.cross_entropy(test)
        assert np.isfinite(ce)
        assert ce > 0  # never crashes, honest positive CE near log(8)

    def test_markov_rejects_out_of_vocab_tokens(self) -> None:
        m = c15_markov.MarkovKT(order=1, vocab_size=4)
        with pytest.raises(c15_markov.MarkovError):
            m.fit(np.array([0, 1, 5, 2]))


# ----------------------------------------------------------------------------
# (d) Seasonality-preserving within-hour-of-day block-shuffle null
# ----------------------------------------------------------------------------

class TestBlockShuffleNull:
    def test_marginal_preserved_per_hour(self) -> None:
        rng = np.random.default_rng(0)
        n = 5000
        hours = rng.integers(0, 24, size=n).astype(np.int64)
        tokens = rng.integers(0, 128, size=n).astype(np.int64)
        surr = c15_stats.hour_block_shuffle(
            tokens, hours, block_len=32, rng=np.random.default_rng(1),
        )
        for h in range(24):
            idx = hours == h
            assert np.array_equal(
                np.sort(tokens[idx]), np.sort(surr[idx])
            ), f"hour {h}: marginal distribution changed"

    def test_sequence_structure_destroyed_beyond_block_len(self) -> None:
        # Single hour-of-day group: tokens are STRICTLY increasing
        # (perfect long-range order-correlation with position).
        n = 4000
        hours = np.zeros(n, dtype=np.int64)
        tokens = np.arange(n, dtype=np.int64) % 128
        # use signed rank surrogate for correlation (values wrap mod 128,
        # so correlate against the ORIGINAL positions instead of values)
        positions = np.arange(n)
        surr = c15_stats.hour_block_shuffle(
            tokens, hours, block_len=32, rng=np.random.default_rng(2),
        )
        # find, for the surrogate, which original position each token
        # came from (bijective since tokens are a repeating ramp — use the
        # index array construction directly instead for an exact test)
        idx_positions = np.arange(n, dtype=np.int64)
        surr_positions = c15_stats.hour_block_shuffle(
            idx_positions, hours, block_len=32, rng=np.random.default_rng(2),
        )
        corr = float(np.corrcoef(positions, surr_positions)[0, 1])
        assert corr < 0.9, f"block shuffle did not destroy long-range order (corr={corr})"
        assert not np.array_equal(surr_positions, idx_positions)

    def test_local_structure_within_block_preserved(self) -> None:
        # Adjacent-pair "+1" continuity should mostly survive INSIDE a
        # block (only broken at the (few) block boundaries).
        n = 3200
        hours = np.zeros(n, dtype=np.int64)
        idx_positions = np.arange(n, dtype=np.int64)
        block_len = 64
        surr_positions = c15_stats.hour_block_shuffle(
            idx_positions, hours, block_len=block_len, rng=np.random.default_rng(3),
        )
        n_blocks = n // block_len
        adjacent_plus1 = np.sum(np.diff(surr_positions) == 1)
        # at most n_blocks - 1 breaks possible from reordering; almost all
        # of the (n-1) adjacent pairs must still be "+1" (within-block).
        min_expected = (n - 1) - n_blocks
        assert adjacent_plus1 >= min_expected

    def test_degenerate_group_smaller_than_block_is_identity(self) -> None:
        n = 50
        hours = np.zeros(n, dtype=np.int64)
        tokens = np.arange(n, dtype=np.int64)
        surr = c15_stats.hour_block_shuffle(
            tokens, hours, block_len=256, rng=np.random.default_rng(5),
        )
        np.testing.assert_array_equal(surr, tokens)

    def test_rejects_shape_mismatch_and_bad_hours(self) -> None:
        with pytest.raises(c15_stats.FoldError):
            c15_stats.hour_block_shuffle(
                np.zeros(5, dtype=np.int64), np.zeros(4, dtype=np.int64),
                rng=np.random.default_rng(0),
            )
        with pytest.raises(c15_stats.FoldError):
            c15_stats.hour_block_shuffle(
                np.zeros(5, dtype=np.int64), np.full(5, 99, dtype=np.int64),
                rng=np.random.default_rng(0),
            )


# ----------------------------------------------------------------------------
# (e) --check-gpu-only honesty (compute gate)
# ----------------------------------------------------------------------------

class TestComputeGate:
    def test_torch_cuda_status_shape_and_honesty(self) -> None:
        status = c15_transformer.torch_cuda_status()
        assert set(status) >= {
            "torch_available", "torch_version", "cuda_available",
            "cuda_device_count", "cuda_device_name",
        }
        assert isinstance(status["torch_available"], bool)
        assert isinstance(status["cuda_available"], bool)
        if not status["torch_available"]:
            # This sandbox has no torch -> honest, fully-degraded report.
            assert status["cuda_available"] is False
            assert status["cuda_device_count"] == 0
            assert status["cuda_device_name"] is None

    def test_cli_check_gpu_only_exits_zero_and_reports_honestly(self) -> None:
        env = {"PYTHONPATH": str(REPO_ROOT / "src")}
        import os
        full_env = {**os.environ, **env}
        result = subprocess.run(
            [sys.executable, str(CLI_SCRIPT), "--check-gpu-only"],
            capture_output=True, text=True, timeout=60, env=full_env,
        )
        assert result.returncode == 0, result.stderr
        status = json.loads(result.stdout)
        assert "torch_available" in status
        assert "cuda_available" in status
        if not status["torch_available"]:
            assert status["cuda_available"] is False

    def test_full_mode_refuses_without_cuda(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            c15_driver, "torch_cuda_status",
            lambda: {"torch_available": False, "torch_version": None,
                     "cuda_available": False, "cuda_device_count": 0,
                     "cuda_device_name": None},
        )
        days = _day_grid("2026-01-01", 30)
        events = {"BTCUSDT": _make_stream("BTCUSDT", days, 20, seed=1)}
        with pytest.raises(c15_transformer.ComputeUnavailableError):
            c15_driver.run(events, days, mode="full")

    def test_mechanics_mode_never_verdict_bearing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            c15_driver, "torch_cuda_status",
            lambda: {"torch_available": False, "torch_version": None,
                     "cuda_available": False, "cuda_device_count": 0,
                     "cuda_device_name": None},
        )
        days = _day_grid("2026-01-01", 20)
        events = {"BTCUSDT": _make_stream("BTCUSDT", days, 30, seed=1)}
        payload = c15_driver.run(
            events, days, mode="mechanics", n_folds=2, embargo_days=1,
            seeds=(42,), n_surrogates=3,
        )
        assert payload["mode"] == "mechanics"
        assert payload["ran_on_gpu"] is False
        assert payload["gate_valid"] is False


# ----------------------------------------------------------------------------
# (f) capital_free token scan
# ----------------------------------------------------------------------------

class TestCapitalFree:
    def _run_small_mechanics_payload(self) -> dict:
        days = _day_grid("2026-01-01", 20)
        events = {
            "BTCUSDT": _make_stream("BTCUSDT", days, 30, seed=1),
            "ETHUSDT": _make_stream("ETHUSDT", days, 30, seed=2),
        }
        return c15_driver.run(
            events, days, mode="mechanics", n_folds=2, embargo_days=1,
            seeds=(42,), n_surrogates=3,
        )

    def test_capital_free_flag_true(self) -> None:
        payload = self._run_small_mechanics_payload()
        assert payload["capital_free"] is True

    def test_no_forbidden_capital_tokens_in_payload(self) -> None:
        payload = self._run_small_mechanics_payload()
        blob = json.dumps(payload, default=str).lower()
        for tok in FORBIDDEN_TOKENS:
            assert tok not in blob, f"forbidden capital token found: {tok!r}"

    def test_no_forbidden_capital_tokens_in_markdown(self) -> None:
        payload = self._run_small_mechanics_payload()
        md = c15_driver.render_markdown(payload).lower()
        for tok in FORBIDDEN_TOKENS:
            assert tok not in md, f"forbidden capital token found in markdown: {tok!r}"

    def test_differentiation_note_present_and_verbatim_markers(self) -> None:
        payload = self._run_small_mechanics_payload()
        note = payload["differentiation_note"]
        assert "Event-Stream" in note or "EVENT-STREAM" in note
        assert "Scoring-Rule" in note or "SCORING-RULE" in note
        assert "H-15b" in note
        md = c15_driver.render_markdown(payload)
        assert "Differenzierung" in md


# ----------------------------------------------------------------------------
# (g) gate_valid deviation checks: architecture drift (Bug #1) + symbol-panel
# identity (Bug #2) — audit_h15.md findings, regression-locked here.
# ----------------------------------------------------------------------------

class TestGateDeviationChecks:
    def _small_payload(self, **run_kwargs) -> dict:
        days = _day_grid("2026-01-01", 20)
        events = {
            "BTCUSDT": _make_stream("BTCUSDT", days, 30, seed=1),
            "ETHUSDT": _make_stream("ETHUSDT", days, 30, seed=2),
        }
        kwargs = dict(mode="mechanics", n_folds=2, embargo_days=1,
                      seeds=(42,), n_surrogates=3)
        kwargs.update(run_kwargs)
        return c15_driver.run(events, days, **kwargs)

    def test_architecture_drift_voids_gate_valid(self) -> None:
        """Bug #1: cfg.n_layers deviating from the registered default MUST
        surface as a gate_valid_reasons entry (previously silently ignored:
        only n_folds/embargo/seeds/surrogates/block_len/tick-dir were
        checked, never context_len/d_model/n_heads/n_layers/epochs/
        batch_size/lr/dropout/grad_clip)."""
        drifted_cfg = c15_transformer.GrammarTransformerConfig(n_layers=8)
        payload = self._small_payload(config=drifted_cfg)
        assert payload["gate_valid"] is False
        reasons = payload["gate_valid_reasons"]
        assert any("n_layers=8" in r and "!= registered default" in r
                    for r in reasons), reasons

    def test_default_architecture_has_no_drift_reason(self) -> None:
        """Sanity counterpart: the registered-default config must NOT trip
        the new architecture-drift check (only mechanics-mode reasons)."""
        payload = self._small_payload()
        reasons = payload["gate_valid_reasons"]
        assert not any("!= registered default" in r for r in reasons), reasons

    def test_each_architecture_field_individually_flagged(self) -> None:
        """Every field in the drift check trips its own reason string."""
        deviations = {
            "context_len": 512, "d_model": 128, "n_heads": 2, "n_layers": 8,
            "epochs": 1, "batch_size": 16, "lr": 1e-3, "dropout": 0.5,
            "grad_clip": 2.0,
        }
        for field, value in deviations.items():
            cfg = c15_transformer.GrammarTransformerConfig(**{field: value})
            payload = self._small_payload(config=cfg)
            reasons = payload["gate_valid_reasons"]
            assert any(r.startswith(f"{field}={value}") for r in reasons), \
                f"{field}: no drift reason found in {reasons}"

    def test_wrong_symbol_panel_same_length_voids_gate_valid(self) -> None:
        """Bug #2: a same-LENGTH but wrong-IDENTITY 5-symbol panel must be
        flagged (previously only len(per_symbol) >= FAMILY_SIZE was
        checked — a same-length wrong panel slipped through silently)."""
        days = _day_grid("2026-01-01", 20)
        wrong_panel = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "DOGEUSDT")
        events = {
            sym: _make_stream(sym, days, 30, seed=i)
            for i, sym in enumerate(wrong_panel)
        }
        payload = c15_driver.run(
            events, days, mode="mechanics", n_folds=2, embargo_days=1,
            seeds=(42,), n_surrogates=3,
        )
        assert payload["gate_valid"] is False
        reasons = payload["gate_valid_reasons"]
        assert any("!= registered 5-symbol panel" in r for r in reasons), reasons

    def test_correct_symbol_panel_no_identity_reason(self) -> None:
        days = _day_grid("2026-01-01", 20)
        events = {
            sym: _make_stream(sym, days, 30, seed=i)
            for i, sym in enumerate(c15_driver.DEFAULT_SYMBOLS)
        }
        payload = c15_driver.run(
            events, days, mode="mechanics", n_folds=2, embargo_days=1,
            seeds=(42,), n_surrogates=3,
        )
        reasons = payload["gate_valid_reasons"]
        assert not any("registered 5-symbol panel" in r for r in reasons), reasons

    def test_wrong_seed_values_same_count_voids_gate_valid(self) -> None:
        """Bug #4 (CRITICAL_REVIEW_2): only len(seeds) was checked against
        N_SEEDS, never the registered seed VALUES (42, 43, 44). Seed-shopping
        (--seeds 7,8,9) or degenerate duplicate seeds (--seeds 42,42,42) must
        both be flagged even though the count matches."""
        payload = self._small_payload(seeds=(7, 8, 9))
        assert payload["gate_valid"] is False
        reasons = payload["gate_valid_reasons"]
        assert any("!= registered seed values" in r for r in reasons), reasons

    def test_duplicate_seed_values_same_count_voids_gate_valid(self) -> None:
        payload = self._small_payload(seeds=(42, 42, 42))
        reasons = payload["gate_valid_reasons"]
        assert any("!= registered seed values" in r for r in reasons), reasons

    def test_correct_seed_values_no_identity_reason(self) -> None:
        payload = self._small_payload(seeds=c15_driver.DEFAULT_SEEDS)
        reasons = payload["gate_valid_reasons"]
        assert not any("registered seed values" in r for r in reasons), reasons

    def test_wrong_data_window_voids_gate_valid(self) -> None:
        """Bug #3 (CRITICAL_REVIEW_2): the registered ~100-day window
        (DEFAULT_DATA_START..DEFAULT_DATA_END) was never checked in the
        gate_valid deviation check — free --data-start/--data-end CLI flags
        allowed silent post-hoc window-shopping. Any window other than the
        ONE registered window must be flagged."""
        days = _day_grid("2026-05-01", 20)  # >= 15 days, inside registry grid
        events = {
            "BTCUSDT": _make_stream("BTCUSDT", days, 30, seed=1),
            "ETHUSDT": _make_stream("ETHUSDT", days, 30, seed=2),
        }
        payload = c15_driver.run(
            events, days, mode="mechanics", n_folds=2, embargo_days=1,
            seeds=(42,), n_surrogates=3,
        )
        assert payload["gate_valid"] is False
        reasons = payload["gate_valid_reasons"]
        assert any("data window" in r and "!= registered" in r for r in reasons), reasons

    def test_registered_data_window_no_window_reason(self) -> None:
        days = c15_driver.daily_grid(
            c15_driver.DEFAULT_DATA_START, c15_driver.DEFAULT_DATA_END)
        events = {
            "BTCUSDT": _make_stream("BTCUSDT", days, 30, seed=1),
            "ETHUSDT": _make_stream("ETHUSDT", days, 30, seed=2),
        }
        payload = c15_driver.run(
            events, days, mode="mechanics", n_folds=2, embargo_days=1,
            seeds=(42,), n_surrogates=3,
        )
        reasons = payload["gate_valid_reasons"]
        assert not any("data window" in r for r in reasons), reasons


# ----------------------------------------------------------------------------
# (h) per-symbol checkpoint/resume (Bug #3, option b) — a timeout/crash must
# lose at most the in-flight symbol, not already-finished ones.
# ----------------------------------------------------------------------------

class TestSymbolCheckpointResume:
    def _events(self) -> tuple[list[str], dict]:
        days = _day_grid("2026-01-01", 20)
        events = {
            "BTCUSDT": _make_stream("BTCUSDT", days, 30, seed=1),
            "ETHUSDT": _make_stream("ETHUSDT", days, 30, seed=2),
        }
        return days, events

    def test_checkpoint_written_per_symbol(self, tmp_path: Path) -> None:
        days, events = self._events()
        ckpt_dir = tmp_path / "ckpt"
        c15_driver.run(
            events, days, mode="mechanics", n_folds=2, embargo_days=1,
            seeds=(42,), n_surrogates=3, ckpt_dir=ckpt_dir,
        )
        assert (ckpt_dir / "BTCUSDT.json").exists()
        assert (ckpt_dir / "ETHUSDT.json").exists()

    def test_resume_skips_completed_symbols(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        days, events = self._events()
        ckpt_dir = tmp_path / "ckpt"
        run_kwargs = dict(
            mode="mechanics", n_folds=2, embargo_days=1,
            seeds=(42,), n_surrogates=3, ckpt_dir=ckpt_dir,
        )
        first = c15_driver.run(events, days, **run_kwargs)

        calls: list[str] = []
        real_run_fold = c15_driver._run_fold

        def counting_run_fold(ev, fold, cfg, **kw):
            calls.append(ev.symbol)
            return real_run_fold(ev, fold, cfg, **kw)

        monkeypatch.setattr(c15_driver, "_run_fold", counting_run_fold)
        second = c15_driver.run(events, days, **run_kwargs)

        assert calls == [], f"resume must not retrain any symbol, got {calls}"
        first_syms = {s["symbol"]: s["best_markov_ce"] for s in first["per_symbol"]}
        second_syms = {s["symbol"]: s["best_markov_ce"] for s in second["per_symbol"]}
        assert first_syms == second_syms

    def test_stale_fingerprint_forces_recompute(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A checkpoint written under different registered parameters must
        NOT be silently reused (would risk mixing two configurations within
        one family)."""
        days, events = self._events()
        ckpt_dir = tmp_path / "ckpt"
        c15_driver.run(
            events, days, mode="mechanics", n_folds=2, embargo_days=1,
            seeds=(42,), n_surrogates=3, ckpt_dir=ckpt_dir,
        )

        calls: list[str] = []
        real_run_fold = c15_driver._run_fold

        def counting_run_fold(ev, fold, cfg, **kw):
            calls.append(ev.symbol)
            return real_run_fold(ev, fold, cfg, **kw)

        monkeypatch.setattr(c15_driver, "_run_fold", counting_run_fold)
        # Different seeds -> different fingerprint -> stale checkpoint.
        c15_driver.run(
            events, days, mode="mechanics", n_folds=2, embargo_days=1,
            seeds=(42, 43), n_surrogates=3, ckpt_dir=ckpt_dir,
        )
        assert set(calls) == {"BTCUSDT", "ETHUSDT"}, calls

    def test_events_capped_mismatch_forces_recompute(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """HIGH (CRITICAL_REVIEW_2 Bug #2): the fingerprint used to omit
        events_capped/max_events_per_day. An uncapped run must NOT silently
        adopt a per-day-capped run's checkpoints -- the resulting payload
        would stamp gate_valid: true while every statistic underneath was
        computed on capped, non-registered data."""
        days, events = self._events()
        ckpt_dir = tmp_path / "ckpt"
        # 1) a per-day-capped debug run populates the shared checkpoint dir.
        c15_driver.run(
            events, days, mode="mechanics", n_folds=2, embargo_days=1,
            seeds=(42,), n_surrogates=3, ckpt_dir=ckpt_dir,
            events_capped=True, max_events_per_day=5,
        )

        calls: list[str] = []
        real_run_fold = c15_driver._run_fold

        def counting_run_fold(ev, fold, cfg, **kw):
            calls.append(ev.symbol)
            return real_run_fold(ev, fold, cfg, **kw)

        monkeypatch.setattr(c15_driver, "_run_fold", counting_run_fold)
        # 2) a later uncapped run against the SAME ckpt_dir must recompute
        # every symbol, not resume from the capped checkpoints.
        c15_driver.run(
            events, days, mode="mechanics", n_folds=2, embargo_days=1,
            seeds=(42,), n_surrogates=3, ckpt_dir=ckpt_dir,
            events_capped=False, max_events_per_day=0,
        )
        assert set(calls) == {"BTCUSDT", "ETHUSDT"}, (
            f"uncapped run resumed from capped checkpoints instead of "
            f"retraining: {calls}")

    def test_mode_mismatch_resume_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """CRITICAL (CRITICAL_REVIEW_2 Bug #1): the fingerprint used to omit
        mode/device/ran_on_gpu. A `full` GPU run must NEVER silently adopt a
        `mechanics` (CPU) run's checkpoints -- doing so would stamp
        gate_valid: true / ran_on_gpu: true on a result with zero GPU
        training behind it, a direct Wave-5 compute-gate violation."""
        days, events = self._events()
        ckpt_dir = tmp_path / "ckpt"
        run_kwargs = dict(n_folds=2, embargo_days=1, seeds=(42,),
                           n_surrogates=3, ckpt_dir=ckpt_dir)

        # 1) a mechanics (CPU) run populates the shared checkpoint dir.
        c15_driver.run(events, days, mode="mechanics", **run_kwargs)

        # 2) fake a CUDA device so `full` mode is permitted to start, and
        # stub _run_fold so the test never needs a real GPU/torch -- the
        # only thing under test is whether run() RESUMES (bug) or
        # RETRAINS (fix) when only mode/device/ran_on_gpu differ.
        monkeypatch.setattr(
            c15_driver, "torch_cuda_status",
            lambda: {"torch_available": True, "torch_version": "fake",
                      "cuda_available": True, "cuda_device_count": 1,
                      "cuda_device_name": "fake-gpu"},
        )
        calls: list[str] = []

        def fake_run_fold(ev, fold, cfg, **kw):
            calls.append(ev.symbol)
            public = {
                "fold_index": fold.index,
                "n_scored_test_tokens": 100,
                "best_markov_ce": 1.0,
                "transformer_ce_mean_seeds": 0.8,
            }
            surrogate_gaps = np.full(kw["n_surrogates"], 0.05)
            return {"public": public, "surrogate_gaps": surrogate_gaps}

        monkeypatch.setattr(c15_driver, "_run_fold", fake_run_fold)
        c15_driver.run(events, days, mode="full", **run_kwargs)
        assert set(calls) == {"BTCUSDT", "ETHUSDT"}, (
            f"full-mode (GPU) run resumed from mechanics (CPU) checkpoints "
            f"instead of retraining: {calls}")


# ----------------------------------------------------------------------------
# (i) benjamini_hochberg — dedicated unit test (Bug #4), own BH-FDR copy.
# ----------------------------------------------------------------------------

class TestBenjaminiHochberg:
    def test_all_p_one_never_rejects(self) -> None:
        rejected, p_crit = c15_stats.benjamini_hochberg([1.0] * 5, alpha=0.10)
        assert rejected == [False] * 5
        assert p_crit == 0.0

    def test_all_p_zero_rejects_all(self) -> None:
        rejected, p_crit = c15_stats.benjamini_hochberg([0.0] * 5, alpha=0.10)
        assert rejected == [True] * 5
        assert p_crit == 0.0

    def test_empty_input(self) -> None:
        rejected, p_crit = c15_stats.benjamini_hochberg([], alpha=0.10)
        assert rejected == []
        assert p_crit == 0.0

    def test_known_f_grammar_m5_case(self) -> None:
        # m=5, alpha=0.10 -> BH thresholds (rank/m)*alpha = 0.02, 0.04,
        # 0.06, 0.08, 0.10. Sorted p = [0.01, 0.03, 0.20, 0.40, 0.50].
        # Largest k with p_(k) <= (k/5)*0.10: k=2 (p=0.03 <= 0.04); k=3
        # (0.20 <= 0.06) fails, and no larger k passes either -> reject
        # ranks 1,2 only.
        p = [0.50, 0.01, 0.40, 0.03, 0.20]
        rejected, p_crit = c15_stats.benjamini_hochberg(p, alpha=0.10)
        # indices of the two smallest p-values (0.01 at idx1, 0.03 at idx3)
        assert rejected[1] is True
        assert rejected[3] is True
        assert rejected[0] is False
        assert rejected[2] is False
        assert rejected[4] is False
        assert p_crit == pytest.approx(0.03)

    def test_ties_at_boundary(self) -> None:
        # m=4, alpha=0.10, thresholds 0.025/0.05/0.075/0.10. Two tied
        # p-values at the k=2 threshold.
        p = [0.05, 0.05, 0.5, 0.9]
        rejected, p_crit = c15_stats.benjamini_hochberg(p, alpha=0.10)
        assert rejected[0] is True
        assert rejected[1] is True
        assert rejected[2] is False
        assert rejected[3] is False
        assert p_crit == pytest.approx(0.05)

    def test_no_rejection_when_all_p_above_thresholds(self) -> None:
        p = [0.5, 0.6, 0.7, 0.8, 0.9]
        rejected, p_crit = c15_stats.benjamini_hochberg(p, alpha=0.10)
        assert rejected == [False] * 5
        assert p_crit == 0.0

    def test_input_order_preserved(self) -> None:
        p = [0.9, 0.001, 0.5]
        rejected, _ = c15_stats.benjamini_hochberg(p, alpha=0.10)
        assert len(rejected) == 3
        # only the smallest p-value (idx 1) can plausibly reject here
        assert rejected[1] is True
        assert rejected[0] is False


# ----------------------------------------------------------------------------
# (j) memory discipline (Wave-2 T3-OOM fixes) — structural + bit-identity
# regressions: lazy per-symbol loading (peak event-RAM = O(one symbol)),
# chunked count lookups, shared interp count tables, small-dtype token
# storage. NONE of these may change any statistic — every test here asserts
# either structure (loader lifetimes) or EXACT numerical identity.
# ----------------------------------------------------------------------------


class TestMemoryDiscipline:
    def _days(self) -> list[str]:
        return _day_grid("2026-01-01", 20)

    def test_lazy_loader_called_once_and_events_released(self) -> None:
        """run() with loader callables: each loader fires exactly once, the
        previous symbol's EventStream is ALREADY freed when the next symbol
        loads (peak = one symbol), and nothing survives run()."""
        days = self._days()
        calls = {"BTCUSDT": 0, "ETHUSDT": 0}
        refs: dict[str, weakref.ref] = {}

        def make_loader(sym: str, seed: int):
            def load() -> c15_driver.EventStream:
                if sym == "ETHUSDT":
                    gc.collect()
                    assert refs["BTCUSDT"]() is None, (
                        "BTCUSDT events still alive while ETHUSDT loads — "
                        "peak event-RAM is not O(one symbol)")
                calls[sym] += 1
                ev = _make_stream(sym, days, 30, seed=seed)
                refs[sym] = weakref.ref(ev)
                return ev
            return load

        loaders = {
            "BTCUSDT": make_loader("BTCUSDT", 1),
            "ETHUSDT": make_loader("ETHUSDT", 2),
        }
        payload = c15_driver.run(
            loaders, days, mode="mechanics", n_folds=2, embargo_days=1,
            seeds=(42,), n_surrogates=3,
        )
        assert calls == {"BTCUSDT": 1, "ETHUSDT": 1}
        gc.collect()
        assert refs["BTCUSDT"]() is None
        assert refs["ETHUSDT"]() is None
        assert [s["symbol"] for s in payload["per_symbol"]] == \
            ["BTCUSDT", "ETHUSDT"]

    def test_lazy_and_eager_payloads_identical(self) -> None:
        """Loader-based run must be statistically indistinguishable from the
        old eager-dict run on identical streams (pure lifetime change)."""
        days = self._days()

        def streams() -> dict[str, c15_driver.EventStream]:
            return {
                "BTCUSDT": _make_stream("BTCUSDT", days, 30, seed=1),
                "ETHUSDT": _make_stream("ETHUSDT", days, 30, seed=2),
            }

        kwargs = dict(mode="mechanics", n_folds=2, embargo_days=1,
                      seeds=(42,), n_surrogates=3)
        eager = c15_driver.run(streams(), days, **kwargs)
        lazy = c15_driver.run(
            {sym: (lambda s=sym: streams()[s]) for sym in streams()},
            days, **kwargs,
        )
        for se, sl in zip(eager["per_symbol"], lazy["per_symbol"]):
            assert se["symbol"] == sl["symbol"]
            assert se["best_markov_ce"] == sl["best_markov_ce"]
            assert se["fold_weights_scored_tokens"] == sl["fold_weights_scored_tokens"]
            for fe, fl in zip(se["folds"], sl["folds"]):
                assert fe["markov_ces"] == fl["markov_ces"]
                assert fe["tokenizer_size_edges"] == fl["tokenizer_size_edges"]
                assert fe["tokenizer_iat_edges"] == fl["tokenizer_iat_edges"]
                assert fe["surrogate_gap_p95"] == fl["surrogate_gap_p95"] or (
                    np.isnan(_nan(fe["surrogate_gap_p95"]))
                    and np.isnan(_nan(fl["surrogate_gap_p95"])))

    def test_resume_never_invokes_loader(self, tmp_path: Path) -> None:
        """Checkpoint-resumed symbols must be skipped WITHOUT loading their
        events at all (with lazy loaders a resume costs ~zero RAM/time)."""
        days = self._days()
        ckpt_dir = tmp_path / "ckpt"
        kwargs = dict(mode="mechanics", n_folds=2, embargo_days=1,
                      seeds=(42,), n_surrogates=3, ckpt_dir=ckpt_dir)
        events = {
            "BTCUSDT": _make_stream("BTCUSDT", days, 30, seed=1),
            "ETHUSDT": _make_stream("ETHUSDT", days, 30, seed=2),
        }
        c15_driver.run(events, days, **kwargs)

        def poisoned_loader() -> c15_driver.EventStream:
            raise AssertionError("loader invoked despite valid checkpoint")

        second = c15_driver.run(
            {"BTCUSDT": poisoned_loader, "ETHUSDT": poisoned_loader},
            days, **kwargs,
        )
        assert [s["symbol"] for s in second["per_symbol"]] == \
            ["BTCUSDT", "ETHUSDT"]

    def test_prepare_fold_small_dtype_storage(self) -> None:
        """Fold token/hour arrays are stored int16/int8 (vocab <= 256,
        hours 0..23) — 4-8x less resident RAM than the old int64 arrays."""
        days = self._days()
        fold = _make_fold(days[:10], days[12:], days[10:12])
        events = _make_stream("BTCUSDT", days, 30, seed=3)
        spec, train_tok, test_tok, test_hours = c15_driver.prepare_fold(events, fold)
        assert train_tok.dtype == np.int16
        assert test_tok.dtype == np.int16
        assert test_hours.dtype == np.int8
        assert int(train_tok.min()) >= 0
        assert int(train_tok.max()) < spec.vocab_size

    def test_lookup_chunking_bitidentical(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Chunked _SortedCounts.lookup must be BIT-identical to the old
        single-shot formulation (element-wise independent, no float path)."""
        rng = np.random.default_rng(0)
        codes = rng.integers(0, 500, size=20_000)
        sc = c15_markov._SortedCounts.from_codes(codes)
        queries = rng.integers(0, 700, size=10_000)  # includes absent keys
        # reference: the pre-fix unchunked formulation, verbatim
        idx = np.searchsorted(sc.keys, queries)
        idx_c = np.clip(idx, 0, sc.keys.size - 1)
        found = sc.keys[idx_c] == queries
        expected = np.where(found, sc.vals[idx_c], 0)
        # force many, unevenly-cut chunks
        monkeypatch.setattr(c15_markov, "_LOOKUP_CHUNK", 997)
        got = sc.lookup(queries)
        assert got.dtype == np.int64
        np.testing.assert_array_equal(got, expected)

    def test_interp_shares_tables_and_is_bitidentical(self) -> None:
        """fit_all_baselines: the interpolated model must (a) SHARE the
        fixed-order models' count tables (no duplicate copy) and (b) produce
        BIT-identical log-probs to an independent fit()."""
        rng = np.random.default_rng(1)
        train = rng.integers(0, 8, size=30_000)
        test = rng.integers(0, 8, size=5_000)
        models = c15_markov.fit_all_baselines(train, vocab_size=8)
        shared = models[f"interp_k{c15_markov.MAX_ORDER}"]
        for k in range(c15_markov.MAX_ORDER + 1):
            assert shared._pair[k] is models[f"kt_k{k}"]._pair, k
            assert shared._ctx[k] is models[f"kt_k{k}"]._ctx, k
        direct = c15_markov.InterpolatedMarkov(
            max_order=c15_markov.MAX_ORDER, vocab_size=8).fit(train)
        np.testing.assert_array_equal(
            direct.log_probs(test), shared.log_probs(test))

    def test_markov_small_dtype_bitidentical(self) -> None:
        """int16 token storage must give BIT-identical log-probs/CE to int64
        storage for both baseline families (all code arithmetic upcasts)."""
        rng = np.random.default_rng(5)
        train64 = rng.integers(0, 128, size=50_000).astype(np.int64)
        test64 = rng.integers(0, 128, size=8_000).astype(np.int64)
        train16 = train64.astype(np.int16)
        test16 = test64.astype(np.int16)
        for order in (0, 2, 4):
            m64 = c15_markov.MarkovKT(order=order, vocab_size=128).fit(train64)
            m16 = c15_markov.MarkovKT(order=order, vocab_size=128).fit(train16)
            np.testing.assert_array_equal(
                m64.log_probs(test64), m16.log_probs(test16))
        i64 = c15_markov.InterpolatedMarkov(max_order=4, vocab_size=128).fit(train64)
        i16 = c15_markov.InterpolatedMarkov(max_order=4, vocab_size=128).fit(train16)
        np.testing.assert_array_equal(i64.log_probs(test64), i16.log_probs(test16))

    def test_hour_block_shuffle_preserves_dtype_and_values(self) -> None:
        """Surrogates keep the input dtype (no int64 blow-up copy) and the
        int16 path permutes EXACTLY like the int64 path (same rng seed)."""
        rng = np.random.default_rng(9)
        n = 4000
        tokens64 = rng.integers(0, 128, size=n).astype(np.int64)
        hours64 = rng.integers(0, 24, size=n).astype(np.int64)
        surr64 = c15_stats.hour_block_shuffle(
            tokens64, hours64, block_len=16, rng=np.random.default_rng(7))
        surr16 = c15_stats.hour_block_shuffle(
            tokens64.astype(np.int16), hours64.astype(np.int8),
            block_len=16, rng=np.random.default_rng(7))
        assert surr64.dtype == np.int64
        assert surr16.dtype == np.int16
        np.testing.assert_array_equal(surr64, surr16.astype(np.int64))


def _nan(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


# ----------------------------------------------------------------------------
# (k) count_trade_events — the CLI's cheap fail-fast pre-pass must agree with
# the real loader on the usable-event count (same predicates, no arrays).
# ----------------------------------------------------------------------------


class TestCountTradeEvents:
    @staticmethod
    def _write_day(base: Path, symbol: str, day: str, rows: list[tuple]) -> None:
        pa = pytest.importorskip("pyarrow")
        pq = pytest.importorskip("pyarrow.parquet")
        d = base / "raw" / "bybit" / "publicTrade" / f"symbol={symbol}" / f"date={day}"
        d.mkdir(parents=True, exist_ok=True)
        table = pa.table({
            "ts_exchange_ms": pa.array([r[0] for r in rows], type=pa.int64()),
            "payload_json": pa.array([r[1] for r in rows], type=pa.string()),
        })
        pq.write_table(table, d / "part-0.parquet")

    def _populate(self, base: Path, symbol: str, days: list[str]) -> None:
        for i, day in enumerate(days):
            t0 = _epoch_day(day) * _MS_PER_DAY
            rows = [
                # good rows: backfill keys and live keys, strictly rising ts
                (t0 + 10, '{"side": "Buy", "price": "100.5", "size": "0.5"}'),
                (t0 + 20, '{"S": "Sell", "p": "99.1", "v": "1.2"}'),
                (t0 + 30, '{"side": "Sell", "price": "98.7", "size": "2.0"}'),
                (t0 + 40, '{"S": "Buy", "p": "101.0", "v": "0.1"}'),
                (t0 + 50, '{"side": "Buy", "price": "100.0", "size": "3.5"}'),
                # malformed: non-positive price/size -> dropped by BOTH paths
                (t0 + 60, '{"side": "Buy", "price": "0", "size": "1.0"}'),
                (t0 + 70, '{"side": "Sell", "price": "100.0", "size": "-3"}'),
                # missing side/S key -> dropped by the shared inner SQL
                (t0 + 80, '{"price": "100.0", "size": "1.0"}'),
                # NULL exchange timestamp -> dropped by the shared inner SQL
                (None, '{"side": "Buy", "price": "100.0", "size": "1.0"}'),
            ]
            self._write_day(base, symbol, day, rows)

    def test_count_matches_load_with_and_without_cap(self, tmp_path: Path) -> None:
        pytest.importorskip("duckdb")
        days = ["2026-01-01", "2026-01-02"]
        self._populate(tmp_path, "TESTUSDT", days)
        for cap in (0, 3):
            n = c15_driver.count_trade_events(
                tmp_path, "TESTUSDT", days, max_events_per_day=cap)
            ev = c15_driver.load_trade_events(
                tmp_path, "TESTUSDT", days, max_events_per_day=cap)
            assert n == ev.n_events, f"cap={cap}: count {n} != load {ev.n_events}"
        # uncapped: exactly the 5 good rows per day survive
        assert c15_driver.count_trade_events(tmp_path, "TESTUSDT", days) == 10

    def test_count_missing_symbol_raises_dataerror(self, tmp_path: Path) -> None:
        pytest.importorskip("duckdb")
        days = ["2026-01-01"]
        self._populate(tmp_path, "TESTUSDT", days)
        with pytest.raises(c15_driver.DataError):
            c15_driver.count_trade_events(tmp_path, "NOPEUSDT", days)


# ----------------------------------------------------------------------------
# Module-level sanity (registered constants match the registry, verbatim)
# ----------------------------------------------------------------------------

class TestRegisteredConstants:
    def test_vocab_base_128(self) -> None:
        assert c15_tok.VOCAB_BASE == 128
        assert c15_tok.N_SIDES == 2
        assert c15_tok.N_SIZE_BUCKETS == 8
        assert c15_tok.N_IAT_BUCKETS == 8

    def test_markov_max_order_4(self) -> None:
        assert c15_markov.MAX_ORDER == 4

    def test_walk_forward_design(self) -> None:
        assert c15_stats.N_FOLDS == 4
        assert c15_stats.EMBARGO_DAYS == 1
        assert c15_stats.N_SEEDS == 3

    def test_null_design(self) -> None:
        assert c15_stats.N_SURROGATES_DEFAULT == 200
        assert c15_stats.BLOCK_LEN_EVENTS == 256

    def test_gate_thresholds(self) -> None:
        assert c15_stats.REL_CE_GAP_MIN == pytest.approx(0.02)
        assert c15_stats.SURROGATE_PERCENTILE == pytest.approx(95.0)
        assert c15_stats.SYMBOLS_PASS_MIN == 4
        assert c15_stats.FAMILY_SIZE == 5
        assert c15_stats.FDR_ALPHA == pytest.approx(0.10)
        assert c15_stats.FDR_FAMILY == "F-GRAMMAR"
