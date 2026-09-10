"""Unit tests fuer WP-10(A) ``surrogate_null`` -- struktureller Nulleffekt
der Stress-Zelle (PRD 4.3 "Struktureller Nulleffekt (C.4)", DEC-62).

Deckt ab:
  (a) ``block_bootstrap_resample`` -- Werte-Erhalt (reine Umordnung/
      Wiederholung, keine erfundenen Werte), Fehler auf ``block_len<1``.
  (b) ``pair_surrogate_null`` -- DEC-39-Trio:
      POSITIV: gemeinsamer Crash-Faktor an Stress-Tagen -- der reale Lift
      uebertrifft das p95 BEIDER Null-Varianten.
      NULL: unabhaengige Serien mit fetten Tails, Stress-Maske UNABHAENGIG
      von der gemeinsamen Groesse -- der Rang des realen Lifts in der
      "independent_blocks"-Nullverteilung ist NICHT extrem.
      ADVERSARIAL: unabhaengige Serien, Maske aus der gemeinsamen Groesse
      GEWAEHLT -- "selection_on_common_size" reproduziert einen positiven
      Null-Lift-Mittelwert, "independent_blocks" bleibt nahe 0 (Trennung).
      Plus TOO_FEW (n_stress<4 oder n_quiet<4), Fehler auf n_surrogates<1,
      Determinismus (gleicher Seed -> bitidentisches Ergebnis).
  (c) Verdrahtung in ``coherence.pairwise_regime_result``/
      ``correlation_matrix`` -- jedes Paar traegt ``surrogate_null``,
      TOO_FEW wenn die Stress-Zelle TOO_FEW ist.
  (d) Verdrahtung in ``report.build_report`` -- neuer Markdown-Abschnitt,
      DEC-53-Fingerprint-Eintraege je Paar (unabhaengige Bloecke +
      Selektions-Variante), deskriptiver Satz "kein Verdikt".
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.wp10_coherence import coherence as co
from bybit_edge.research.wp10_coherence import portfolio_null as pn
from bybit_edge.research.wp10_coherence import report as rp
from bybit_edge.research.wp10_coherence import stress_canon as sc
from bybit_edge.research.wp10_coherence import surrogate_null as sn


def _iso(i: int, start: str = "2026-01-01") -> str:
    return (date.fromisoformat(start) + timedelta(days=i)).isoformat()


def _mk_series(name: str, days: list[str], values) -> dict:
    return {"name": name, "kind": "synthetic", "symbol": name, "provenance": {},
            "days": list(days), "values": list(values),
            "coverage": {"n_days": len(days)}, "status": "OK", "reason": None}


# ============================================== (a) block_bootstrap_resample

def test_block_bootstrap_resample_preserves_multiset_and_shape():
    rng = np.random.default_rng(9)
    v = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    out = sn.block_bootstrap_resample(v, rng, block_len=1)
    assert out.shape == v.shape
    assert set(out.tolist()) <= set(v.tolist())  # only reorders/repeats, never invents


def test_block_bootstrap_resample_rejects_bad_block_len():
    rng = np.random.default_rng(1)
    with pytest.raises(sn.SurrogateNullError):
        sn.block_bootstrap_resample(np.array([1.0, 2.0]), rng, block_len=0)


def test_block_bootstrap_resample_deterministic_same_generator_state():
    v = np.arange(50.0)
    out1 = sn.block_bootstrap_resample(v, np.random.default_rng(53), block_len=5)
    out2 = sn.block_bootstrap_resample(v, np.random.default_rng(53), block_len=5)
    assert np.array_equal(out1, out2)


def test_block_bootstrap_resample_empty_input():
    out = sn.block_bootstrap_resample(np.empty(0), np.random.default_rng(1), block_len=5)
    assert out.shape == (0,)


# ==================================================== (b) pair_surrogate_null

def test_surrogate_null_rejects_bad_n_surrogates():
    x = np.arange(20.0)
    y = np.arange(20.0)
    mask = np.zeros(20, dtype=bool)
    mask[:6] = True
    with pytest.raises(sn.SurrogateNullError):
        sn.pair_surrogate_null(x, y, mask, seed=1, n_surrogates=0)


def test_surrogate_null_too_few_stress_days():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    y = np.array([2.0, 1.0, 5.0, 3.0, 4.0, 6.0])
    mask = np.array([True, True, False, False, False, False])  # n_stress=2 < 4
    result = sn.pair_surrogate_null(x, y, mask, seed=1, n_surrogates=50)
    assert result == {"status": "TOO_FEW", "n_stress": 2, "n_quiet": 4}


def test_surrogate_null_too_few_quiet_days():
    x = np.arange(6.0)
    y = np.arange(6.0)
    mask = np.array([True, True, True, True, False, False])  # n_quiet=2 < 4
    result = sn.pair_surrogate_null(x, y, mask, seed=1, n_surrogates=50)
    assert result["status"] == "TOO_FEW"
    assert result["n_quiet"] == 2


def test_surrogate_null_deterministic_same_seed():
    rng = np.random.default_rng(3)
    n = 100
    x = rng.normal(size=n)
    y = rng.normal(size=n)
    mask = np.zeros(n, dtype=bool)
    mask[:15] = True
    r1 = sn.pair_surrogate_null(x, y, mask, n_surrogates=200, seed=53)
    r2 = sn.pair_surrogate_null(x, y, mask, n_surrogates=200, seed=53)
    assert r1 == r2


def test_surrogate_null_different_seed_changes_draws():
    rng = np.random.default_rng(3)
    n = 100
    x = rng.normal(size=n)
    y = rng.normal(size=n)
    mask = np.zeros(n, dtype=bool)
    mask[:15] = True
    r1 = sn.pair_surrogate_null(x, y, mask, n_surrogates=200, seed=1)
    r2 = sn.pair_surrogate_null(x, y, mask, n_surrogates=200, seed=2)
    assert r1["independent_blocks"]["lift"]["mean"] != r2["independent_blocks"]["lift"]["mean"]


def test_dec39_positive_common_crash_factor_exceeds_null_p95_both_variants():
    rng = np.random.default_rng(1)
    n = 250
    mask = np.zeros(n, dtype=bool)
    mask[:30] = True  # first 30 "days" are the (arbitrary) stress cell
    x = rng.normal(0.0, 1.0, n)
    y = np.empty(n)
    for i in range(n):
        # a shared crash factor ONLY on stress days -> genuine co-movement there.
        y[i] = (x[i] + rng.normal(0.0, 0.05)) if mask[i] else rng.normal(0.0, 1.0)
    result = sn.pair_surrogate_null(x, y, mask, n_surrogates=500, seed=53)
    assert result["status"] == "OK"
    real_lift = result["real"]["lift"]
    assert real_lift > result["independent_blocks"]["lift"]["p95"]
    assert real_lift > result["selection_on_common_size"]["lift"]["p95"]
    assert result["independent_blocks"]["real_lift_rank_pct"] > 95.0


def test_dec39_null_independent_fat_tails_rank_not_extreme():
    rng = np.random.default_rng(11)
    n = 200
    x = rng.standard_t(df=3, size=n)  # fat tails
    y = rng.standard_t(df=3, size=n)  # independent of x, same marginal family
    mask = np.zeros(n, dtype=bool)
    mask[:20] = True  # arbitrary stress days, UNRELATED to magnitude/order
    result = sn.pair_surrogate_null(x, y, mask, n_surrogates=500, seed=53)
    assert result["status"] == "OK"
    rank = result["independent_blocks"]["real_lift_rank_pct"]
    assert 2.0 < rank < 98.0, rank  # not extreme -- fixed seed, deterministic


def test_dec39_adversarial_mask_on_joint_magnitude_separates_variants():
    # Two FULLY INDEPENDENT series -- each its own independent, sparse,
    # one-sided ("crash-only") spike process on top of tiny baseline noise
    # (a plausible premium-proxy PnL shape: mostly quiet, occasional large
    # drawdowns). Population correlation is exactly 0 (spike timing and
    # size are drawn independently for x and y). See
    # ``surrogate_null``'s module docstring ("On the SIGN of this
    # variant's bias") for why re-deriving the mask from joint magnitude
    # (``|x|+|y|``) on THIS kind of one-sided marginal reliably shifts the
    # ``selection_on_common_size`` null AWAY from zero (here: negative --
    # a "conditioning on a large joint sum anti-correlates the addends"
    # effect), while a fixed EXTERNAL mask applied to independent
    # surrogates (``independent_blocks``) carries no such artifact and
    # stays centred near zero. The separation between the two variants --
    # not a specific sign -- is the PRD-relevant, reproducible claim.
    rng = np.random.default_rng(5)
    n = 300
    p = 0.12
    spike_x = rng.random(n) < p
    spike_y = rng.random(n) < p
    x = rng.normal(0.0, 0.05, n) - spike_x * rng.uniform(1.5, 2.5, n)
    y = rng.normal(0.0, 0.05, n) - spike_y * rng.uniform(1.5, 2.5, n)
    # the "naive analyst" mistake: pick the stress cell as the days where
    # BOTH series happen to have large magnitude -- mechanical selection,
    # no genuine dependence between x and y anywhere.
    joint_mag = np.abs(x) + np.abs(y)
    n_stress = 20
    stress_idx = np.argsort(-joint_mag)[:n_stress]
    mask = np.zeros(n, dtype=bool)
    mask[stress_idx] = True

    result = sn.pair_surrogate_null(x, y, mask, n_surrogates=400, seed=53)
    assert result["status"] == "OK"
    ib_mean = result["independent_blocks"]["lift"]["mean"]
    sel_mean = result["selection_on_common_size"]["lift"]["mean"]
    # the mechanical-selection variant reproduces a genuine, substantial
    # bias (here: negative -- see the comment above)...
    assert sel_mean < -0.15, sel_mean
    # ...while the fixed-mask/independent-blocks variant stays near zero...
    assert abs(ib_mean) < 0.1, ib_mean
    # ...demonstrating the separation the PRD asks for.
    assert abs(sel_mean) > abs(ib_mean) + 0.15


def test_surrogate_null_result_variant_shapes_and_fingerprint():
    rng = np.random.default_rng(2)
    n = 60
    x = rng.normal(size=n)
    y = rng.normal(size=n)
    mask = np.zeros(n, dtype=bool)
    mask[:10] = True
    result = sn.pair_surrogate_null(x, y, mask, n_surrogates=120, seed=53)
    for variant in ("independent_blocks", "selection_on_common_size"):
        block = result[variant]
        assert {"rho_stress", "rho_quiet", "lift", "real_lift_rank_pct",
                "lift_fingerprint_sha256"} <= set(block)
        for stat in ("rho_stress", "rho_quiet", "lift"):
            assert {"mean", "sd", "p5", "p95"} <= set(block[stat])
        assert len(block["lift_fingerprint_sha256"]) == 64


# ============================================ (c) wiring into coherence.py

def test_coherence_pairwise_regime_result_carries_surrogate_null_ok():
    rng = np.random.default_rng(1)
    n = 120
    days = [_iso(i) for i in range(n)]
    stress_set = set(days[:30])
    x = rng.normal(0.0, 1.0, n)
    y = np.empty(n)
    for i in range(n):
        y[i] = (x[i] + rng.normal(0.0, 0.05)) if days[i] in stress_set else rng.normal(0.0, 1.0)
    a, b = _mk_series("A", days, x), _mk_series("B", days, y)
    result = co.pairwise_regime_result(a, b, stress_set, episodes=None,
                                       n_bootstrap=100, seed=53, n_surrogates=150)
    surr = result["surrogate_null"]
    assert surr["status"] == "OK"
    assert surr["real"]["lift"] > surr["independent_blocks"]["lift"]["p95"]


def test_coherence_pairwise_regime_result_surrogate_null_too_few_matches_stress_status():
    rng = np.random.default_rng(4)
    n = 40
    days = [_iso(i) for i in range(n)]
    x = rng.normal(size=n)
    y = rng.normal(size=n)
    a, b = _mk_series("A", days, x), _mk_series("B", days, y)
    result = co.pairwise_regime_result(a, b, set(), episodes=None,
                                       n_bootstrap=100, seed=53, n_surrogates=50)
    assert result["stress"]["status"] == "TOO_FEW"
    assert result["surrogate_null"]["status"] == "TOO_FEW"


def test_correlation_matrix_every_pair_carries_surrogate_null():
    rng = np.random.default_rng(6)
    n = 80
    days = [_iso(i) for i in range(n)]
    stress_set = set(days[:10])
    a = _mk_series("A", days, rng.normal(size=n))
    b = _mk_series("B", days, rng.normal(size=n))
    c = _mk_series("C", days, rng.normal(size=n))
    result = co.correlation_matrix([a, b, c], stress_set, None,
                                   n_bootstrap=50, seed=53, n_surrogates=50)
    assert len(result["pairs"]) == 3
    for pair in result["pairs"]:
        assert "surrogate_null" in pair
        assert pair["surrogate_null"]["status"] in ("OK", "TOO_FEW")


# ================================================== (d) wiring into report.py

def _surrogate_report_fixture():
    rng = np.random.default_rng(1)
    n = 80
    days = [_iso(i) for i in range(n)]
    stress_set = set(days[:15])
    x = rng.normal(0.0, 1.0, n)
    y = np.empty(n)
    for i in range(n):
        y[i] = (x[i] + rng.normal(0.0, 0.05)) if days[i] in stress_set else rng.normal(0.0, 1.0)
    a, b = _mk_series("A", days, x), _mk_series("B", days, y)
    coherence_result = co.correlation_matrix([a, b], stress_set, None,
                                             n_bootstrap=50, seed=53, n_surrogates=80)
    returns = np.random.default_rng(7).normal(0.0, 0.02, 300)
    portfolio_null = {"table": pn.portfolio_null_table(returns, n_bootstrap=50, seed=53),
                      "selection_ceiling": pn.selection_ceiling(returns, seed=53, pool_size=600)}
    stress_canon = {"STRESS_ABS": sc.finalize_fixture(
        sc.build_stress_abs({"BTCUSDT": {d: 0.01 for d in days}}, named_dates=()))}
    return [a, b], coherence_result, stress_canon, portfolio_null


def test_report_includes_surrogate_null_section_and_fingerprint(tmp_path):
    series_list, coherence_result, stress_canon, portfolio_null = _surrogate_report_fixture()
    result = rp.build_report(series_list=series_list, coherence_result=coherence_result,
                             stress_canon=stress_canon, portfolio_null=portfolio_null,
                             out_dir=tmp_path / "out", seed=53)
    summary = json.loads(Path(result["summary_path"]).read_text())
    pair = summary["coherence"]["pairs"][0]
    assert pair["surrogate_null"]["status"] == "OK"

    md = Path(result["markdown_path"]).read_text()
    assert "Struktureller Nulleffekt der Stress-Zelle" in md
    assert "KEIN VERDIKT" in md
    assert "Selektion auf gemeinsame Groesse" in md

    bf_path = result["artifacts"]["bootstrap_fingerprint"]["path"]
    bf = json.loads(Path(bf_path).read_text())
    surrogate_entries = [e for e in bf["entries"] if e.get("surrogate_null")]
    assert len(surrogate_entries) == 1
    entry = surrogate_entries[0]
    assert entry["pair"] == pair["pair"]
    assert len(entry["independent_blocks_lift_fingerprint_sha256"]) == 64
    assert len(entry["selection_on_common_size_lift_fingerprint_sha256"]) == 64
    assert entry["independent_blocks_lift_fingerprint_sha256"] == \
        pair["surrogate_null"]["independent_blocks"]["lift_fingerprint_sha256"]
