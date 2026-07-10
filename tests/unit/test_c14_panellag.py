"""Tests for the H-14 conditional cross-venue lead-lag graph (c14_panellag).

Sandbox has NO torch/CUDA, so these tests cover PIPELINE CORRECTNESS only
(registry H-14 is GPU-gated — the actual ~226-training retrain power is not
sandbox-testable, only the plumbing around it):

(a) 12-node panel loading/synchronisation from a synthetic 1s-grid harvester
    Hive tree (``panel.build_window``).
(b) causality / no-lookahead in the window+target construction
    (``panel.valid_sample_indices`` / ``panel.target_sign_labels``).
(c) edge-statistic computation AND BH-FDR family construction (~110/99
    non-BTC-source edges) via a deterministic fake loss function
    (``driver.compute_window_edges`` / ``driver.assemble_payload``), plus
    full orchestration with checkpoint/resume
    (``ablation.run_window_plan`` / ``driver.run``).
(d) ``--check-gpu-only`` honesty and compute-gating: a run without real CUDA
    is NEVER verdict-bearing (``weiter_indication`` is ``None``/``null``,
    ``gate_valid`` is False), exercised both at the module level
    (``driver.make_compute_info`` / ``build_compute_gating``) and over the
    full CLI (``scripts/c14_panellag.py``).
(e) capital_free token scan (no bps/pnl/sharpe/friction/edge_ anywhere).
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

from bybit_edge.research.c14_panellag.ablation import (
    DEFAULT_N_NULL,
    build_task_plan,
    draw_shifts,
    make_dummy_train_fn,
    run_window_plan,
)
from bybit_edge.research.c14_panellag.driver import (
    assemble_payload,
    compute_window_edges,
    make_compute_info,
    render_markdown,
    run as driver_run,
)
from bybit_edge.research.c14_panellag.encoder import check_gpu
from bybit_edge.research.c14_panellag.panel import (
    DEFAULT_NODES,
    PanelWindow,
    ffill_seconds_capped,
    map_exchange_symbol,
    target_sign_labels,
    train_oos_split,
    valid_sample_indices,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
N_NODES = len(DEFAULT_NODES)
NODE_LABELS = tuple(
    f"{ex}:{map_exchange_symbol(ex, sym)}" for ex, sym in DEFAULT_NODES
)
NODE_BASES = tuple(sym[:-4] for _ex, sym in DEFAULT_NODES)  # BTCUSDT -> BTC
BTC_SOURCE_IDX = tuple(i for i, b in enumerate(NODE_BASES) if b == "BTC")
ETH_TARGET_IDX = tuple(i for i, b in enumerate(NODE_BASES) if b == "ETH")


# ---------------------------------------------------------------------------
# (a) synthetic 1s-grid harvester Hive tree + panel loading/sync
# ---------------------------------------------------------------------------

def _midnight_ms(date_str: str) -> int:
    y, m, d = (int(x) for x in date_str.split("-"))
    return int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)


def _write_raw_backfill(tmp: Path, exchange: str, storage_symbol: str,
                         date_str: str, rows: list[tuple[int, float]]) -> None:
    """One raw-form parquet partition (COALESCE($.price,$.p) backfill form)."""
    import duckdb

    d = tmp / "raw" / exchange / "publicTrade" / f"symbol={storage_symbol}" / f"date={date_str}"
    d.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        recs = [
            (int(ts), json.dumps({"side": "Buy", "price": f"{price:.4f}",
                                   "size": "0.10", "symbol": storage_symbol}))
            for ts, price in rows
        ]
        con.execute("CREATE TABLE t (ts_exchange_ms BIGINT, payload_json VARCHAR)")
        con.executemany("INSERT INTO t VALUES (?, ?)", recs)
        con.execute(f"COPY t TO '{(d / 'data.parquet').as_posix()}' (FORMAT parquet)")
    finally:
        con.close()


def _write_full_day(tmp: Path, exchange: str, symbol: str, date_str: str,
                     seed: int, trade_every_s: int = 15) -> None:
    """Sparse but gap-capped (<=ffill cap) trades for one UTC day, one node."""
    rng = np.random.default_rng(seed)
    storage_symbol = map_exchange_symbol(exchange, symbol)
    start_ms = _midnight_ms(date_str)
    price = 100.0 + seed
    rows: list[tuple[int, float]] = []
    for sec in range(0, 86_400, trade_every_s):
        price *= (1.0 + rng.normal(0.0, 0.0005))
        rows.append((start_ms + sec * 1_000 + 250, price))
    _write_raw_backfill(tmp, exchange, storage_symbol, date_str, rows)


def _build_synthetic_tree(tmp: Path, dates: list[str], trade_every_s: int = 15) -> Path:
    base = tmp / "harvest"
    for ni, (ex, sym) in enumerate(DEFAULT_NODES):
        for d in dates:
            _write_full_day(base, ex, sym, d, seed=100 + ni, trade_every_s=trade_every_s)
    return base


def test_panel_build_window_loads_and_synchronises_all_12_nodes(tmp_path: Path) -> None:
    base = _build_synthetic_tree(tmp_path, ["2031-01-01"])
    from bybit_edge.research.c14_panellag.panel import build_window

    win = build_window(base, "2031-01-01", "2031-01-01", label="W1")
    assert win.n_nodes == N_NODES
    assert win.node_labels == NODE_LABELS
    assert win.returns.shape == (N_NODES, 86_400)
    # trades every 15s, ffill cap 60s -> essentially full coverage after t=1
    for cov in win.coverage:
        assert cov > 0.95
    # Deribit storage symbols use the hyphen form, not BTCUSDT/ETHUSDT.
    assert "deribit:BTC-PERPETUAL" in win.node_labels
    assert "deribit:ETH-PERPETUAL" in win.node_labels
    assert "deribit:SOL-PERPETUAL" not in win.node_labels  # SOL not on deribit


def test_ffill_seconds_capped_respects_gap_cap() -> None:
    x = np.full(200, np.nan)
    x[0] = 1.0
    x[70] = 2.0  # gap of 69 > cap 60 -> stays NaN until here
    x[90] = 3.0  # gap of 19 <= cap -> fillable from index 70
    out = ffill_seconds_capped(x, max_gap=60)
    assert np.isnan(out[61])  # beyond cap from index 0
    assert out[69] != out[69]  # still NaN (np.nan != np.nan)
    assert out[70] == 2.0
    assert out[89] == 2.0  # filled from index 70 (gap=19<=60)
    assert out[90] == 3.0


# ---------------------------------------------------------------------------
# (b) causality / no-lookahead
# ---------------------------------------------------------------------------

def test_valid_sample_indices_excludes_incomplete_windows() -> None:
    rng = np.random.default_rng(1)
    n_nodes, t_total = 4, 500
    r = rng.standard_normal((n_nodes, t_total)).astype(np.float64)
    r[:, 0] = np.nan  # log_returns always has a NaN first sample
    lookback, horizon = 50, 10
    anchors = valid_sample_indices(r, lookback, horizon)
    assert anchors.min() >= lookback - 1
    assert anchors.max() <= t_total - horizon - 1
    # Punch a hole inside a candidate's input window -> that anchor must
    # disappear, but anchors whose window does not touch the hole must not.
    hole_t = 200
    r2 = r.copy()
    r2[2, hole_t] = np.nan
    anchors2 = valid_sample_indices(r2, lookback, horizon)
    # anchors covering the hole in their [t-lookback+1, t] input window:
    touched = {t for t in anchors if hole_t <= t <= hole_t + lookback - 1}
    assert touched, "test setup: hole should invalidate some input windows"
    assert not (touched & set(anchors2.tolist()))
    # anchors whose target horizon [t+1, t+horizon] touches the hole:
    touched_target = {t for t in anchors if t + 1 <= hole_t <= t + horizon}
    assert not (touched_target & set(anchors2.tolist()))
    # anchors far away from the hole are unaffected:
    untouched = [t for t in anchors if t < hole_t - lookback and t > hole_t + horizon]
    assert set(untouched).issubset(set(anchors2.tolist()))


def test_target_sign_labels_use_only_strictly_future_data() -> None:
    rng = np.random.default_rng(2)
    n_nodes, t_total = 3, 300
    r = rng.standard_normal((n_nodes, t_total)) * 0.01
    horizon = 10
    anchors = np.array([50, 100, 150, 200], dtype=np.int64)
    labels_a, mask_a = target_sign_labels(r, anchors, horizon)

    # Mutating everything AT OR BEFORE an anchor must not change ITS OWN
    # label/mask (no lookahead into the past is trivial, but this also
    # catches an off-by-one that would leak anchor t's own return into the
    # "future" sum). Each anchor is tested in ISOLATION (fresh copy, single
    # anchor) so one anchor's past-mutation cannot bleed into another
    # anchor's forward window (anchors are only horizon=10 apart in effect,
    # but their gaps here are 50 — a shared cumulative mutation would
    # otherwise contaminate a smaller anchor's own forward window).
    for k, t in enumerate(anchors):
        r2 = r.copy()
        r2[:, : t + 1] = rng.standard_normal((n_nodes, t + 1)) * 5.0  # blow up the past
        lab, msk = target_sign_labels(r2, anchors[k: k + 1], horizon)
        np.testing.assert_array_equal(lab[0], labels_a[k])
        np.testing.assert_array_equal(msk[0], mask_a[k])

    # Mutating strictly AFTER an anchor's horizon window must not change ITS
    # OWN label (again isolated per anchor, same rationale as above).
    for k, t in enumerate(anchors):
        r3 = r.copy()
        tail = t_total - (t + horizon + 1)
        if tail > 0:
            r3[:, t + horizon + 1:] = rng.standard_normal((n_nodes, tail)) * 5.0
        lab, _ = target_sign_labels(r3, anchors[k: k + 1], horizon)
        np.testing.assert_array_equal(lab[0], labels_a[k])

    # But mutating INSIDE the horizon window (t+1..t+horizon) MUST change it
    # (sanity check the boundary is not accidentally a no-op).
    r4 = r.copy()
    r4[:, anchors[0] + 1: anchors[0] + horizon + 1] = 10.0  # huge positive returns
    labels_d, _ = target_sign_labels(r4, anchors, horizon)
    assert labels_d[0, :].sum() == n_nodes  # all-positive forward sum -> all 1


def test_target_sign_labels_masks_exact_zero_forward_return() -> None:
    n_nodes, t_total = 1, 50
    r = np.zeros((n_nodes, t_total))
    horizon = 5
    anchors = np.array([10], dtype=np.int64)
    labels, mask = target_sign_labels(r, anchors, horizon)
    assert mask[0, 0] == 0.0  # exact zero forward return -> masked out


def test_train_oos_split_embargo_prevents_overlap() -> None:
    (tr_lo, tr_hi), (oo_lo, oo_hi) = train_oos_split((0, 999), train_frac=0.7, embargo=15)
    assert tr_hi < oo_lo
    assert oo_lo - tr_hi - 1 == 15
    assert oo_hi == 999


# ---------------------------------------------------------------------------
# (c) edge-statistic computation + BH-FDR family construction (fake losses)
# ---------------------------------------------------------------------------

def _fake_results(n_null: int, edge_boost: dict[tuple[int, int], float]) -> dict[str, dict]:
    """Craft a deterministic per-node loss result set for all tasks.

    ``edge_boost[(j, i)]`` adds a positive amount to the ablation loss of
    target i when source j is ablated (a genuine j->i edge signal).
    """
    rng = np.random.default_rng(7)
    base = 0.6931  # ln(2), a "no information" BCE baseline
    full = base + rng.normal(0.0, 1e-4, size=N_NODES)
    results = {"full": {"per_node_log_loss": full.tolist()}}
    for j in range(N_NODES):
        abl = full.copy()
        for i in range(N_NODES):
            if i == j:
                continue
            abl[i] = full[i] + edge_boost.get((j, i), 0.0) + rng.normal(0.0, 1e-5)
        results[f"ablate/{j:02d}"] = {"per_node_log_loss": abl.tolist()}
    for k in range(n_null):
        nullk = full + rng.normal(0.0, 2e-4, size=N_NODES)
        results[f"null/{k:03d}"] = {"per_node_log_loss": nullk.tolist()}
    return results


def test_compute_window_edges_family_size_and_positive_control() -> None:
    j_src, i_tgt = 6, 7  # bybit:SOL -> binance:SOL, a genuine non-BTC edge
    edge_boost = {(j_src, i_tgt): 0.05}
    for j in BTC_SOURCE_IDX:  # positive control: BTC -> ETH boosted
        for i in ETH_TARGET_IDX:
            edge_boost[(j, i)] = 0.05
    results = _fake_results(n_null=60, edge_boost=edge_boost)
    stats = compute_window_edges(results, NODE_LABELS, NODE_BASES, n_null=60)

    n_btc_source = len(BTC_SOURCE_IDX)
    assert len(stats["family_edges"]) == (N_NODES - n_btc_source) * (N_NODES - 1)
    assert len(stats["btc_source_edges"]) == n_btc_source * (N_NODES - 1)
    assert stats["positive_control"]["ok"] is True

    fam = {(e["source"], e["target"]): e for e in stats["family_edges"]}
    boosted = fam[(j_src, i_tgt)]
    assert boosted["delta_log_loss"] > boosted["null_delta_q95"]
    assert boosted["over_null_q95"] is True
    assert boosted["p_value"] < 0.05
    # an un-boosted edge should NOT clear the null threshold:
    j_other = next(j for j in range(N_NODES) if j not in BTC_SOURCE_IDX and j != j_src)
    i_other = next(i for i in range(N_NODES) if i != j_other and (j_other, i) not in edge_boost)
    unboosted = fam[(j_other, i_other)]
    assert unboosted["over_null_q95"] is False


def test_assemble_payload_fdr_family_and_gate_neutral_fields() -> None:
    j_src, i_tgt = 6, 7
    edge_boost = {(j_src, i_tgt): 0.08}
    for j in BTC_SOURCE_IDX:
        for i in ETH_TARGET_IDX:
            edge_boost[(j, i)] = 0.05
    window_stats = []
    for wlabel, start, end in (("W1", "2030-01-01", "2030-02-01"),
                                ("W2", "2030-03-01", "2030-04-01")):
        results = _fake_results(n_null=60, edge_boost=edge_boost)
        stats = compute_window_edges(results, NODE_LABELS, NODE_BASES, n_null=60)
        stats.update({
            "window_label": wlabel, "start_date": start, "end_date": end,
            "node_labels": NODE_LABELS, "node_bases": NODE_BASES,
            "coverage": [1.0] * N_NODES,
        })
        window_stats.append(stats)

    n_family_per_window = (N_NODES - len(BTC_SOURCE_IDX)) * (N_NODES - 1)
    assert n_family_per_window == 99  # registry's "~110" estimate, exact count here

    # (i) synthetic / not-verdict-bearing compute info:
    ci_bad = make_compute_info(ran_on_gpu=False, synthetic_train_fn_used=True)
    payload_bad = assemble_payload(
        window_stats, n_null=60, seed=1, source="unit-test", compute_info=ci_bad,
    )
    assert payload_bad["fdr_family_size"] == 2 * n_family_per_window
    assert payload_bad["compute_gating"]["gpu_required"] is True
    assert payload_bad["compute_gating"]["gate_valid"] is False
    assert payload_bad["weiter_indication"] is None  # non-verdict-bearing
    assert payload_bad["positive_control_ok_all_windows"] is True
    assert payload_bad["hypothesis"] == "H-14"
    assert payload_bad["capital_free"] is True
    for w in payload_bad["windows"]:
        assert w["any_family_survivor"] is True

    # (ii) simulated real-GPU compute info -> verdict-bearing bool:
    ci_good = make_compute_info(ran_on_gpu=True)
    payload_good = assemble_payload(
        window_stats, n_null=60, seed=1, source="unit-test", compute_info=ci_good,
    )
    assert payload_good["compute_gating"]["gate_valid"] is True
    assert isinstance(payload_good["weiter_indication"], bool)
    assert payload_good["weiter_indication"] is True

    md = render_markdown(payload_good)
    assert "H-14" in md
    assert "F-PANELLAG" in md


def test_assemble_payload_requires_two_windows() -> None:
    results = _fake_results(n_null=10, edge_boost={})
    stats = compute_window_edges(results, NODE_LABELS, NODE_BASES, n_null=10)
    stats.update({"window_label": "W1", "start_date": "2030-01-01",
                  "end_date": "2030-01-02", "node_labels": NODE_LABELS,
                  "node_bases": NODE_BASES, "coverage": [1.0] * N_NODES})
    with pytest.raises(ValueError):
        assemble_payload([stats], n_null=10, seed=1, source="x",
                          compute_info=make_compute_info(ran_on_gpu=False))


def test_positive_control_failure_marks_run_invalid_not_drop() -> None:
    # No BTC->ETH edge boosted anywhere -> positive control fails.
    window_stats = []
    for wlabel in ("W1", "W2"):
        results = _fake_results(n_null=40, edge_boost={})
        stats = compute_window_edges(results, NODE_LABELS, NODE_BASES, n_null=40)
        stats.update({
            "window_label": wlabel, "start_date": "2030-01-01",
            "end_date": "2030-01-02", "node_labels": NODE_LABELS,
            "node_bases": NODE_BASES, "coverage": [1.0] * N_NODES,
        })
        window_stats.append(stats)
    payload = assemble_payload(
        window_stats, n_null=40, seed=1, source="x",
        compute_info=make_compute_info(ran_on_gpu=True),
    )
    assert payload["positive_control_ok_all_windows"] is False
    assert payload["validity_status"] == "ungueltig"
    assert payload["validity_status"] != "drop"


# ---------------------------------------------------------------------------
# (c-continued) full orchestration: task plan + checkpoint/resume
# ---------------------------------------------------------------------------

def _tiny_window(label: str, t_total: int = 3000, seed: int = 3) -> PanelWindow:
    rng = np.random.default_rng(seed)
    returns = (rng.standard_normal((N_NODES, t_total)) * 0.001).astype(np.float32)
    returns[:, 0] = np.nan
    return PanelWindow(
        label=label, start_date="2030-01-01", end_date="2030-01-01",
        node_labels=NODE_LABELS, node_exchanges=tuple(ex for ex, _ in DEFAULT_NODES),
        node_bases=NODE_BASES, returns=returns, coverage=tuple([1.0] * N_NODES),
    )


def test_build_task_plan_size_and_determinism() -> None:
    tasks = build_task_plan("W1", N_NODES, n_null=5, seed=42)
    assert len(tasks) == 1 + N_NODES + 5
    ids = [t.task_id for t in tasks]
    assert ids[0] == "full"
    assert ids.count("ablate/00") == 1
    assert "null/004" in ids
    tasks2 = build_task_plan("W1", N_NODES, n_null=5, seed=42)
    assert [t.seed for t in tasks] == [t.seed for t in tasks2]  # deterministic
    tasks_other_seed = build_task_plan("W1", N_NODES, n_null=5, seed=43)
    assert [t.seed for t in tasks] != [t.seed for t in tasks_other_seed]


def test_draw_shifts_within_bounds_and_deterministic() -> None:
    tasks = build_task_plan("W1", N_NODES, n_null=3, seed=1)
    ablate_task = next(t for t in tasks if t.kind == "ablate" and t.ablate_node == 2)
    shifts_a = draw_shifts(ablate_task, t_total=100_000)
    shifts_b = draw_shifts(ablate_task, t_total=100_000)
    assert shifts_a == shifts_b  # deterministic given the task seed
    assert set(shifts_a.keys()) == {2}
    assert 0 < shifts_a[2] < 100_000


def test_run_window_plan_executes_and_checkpoints(tmp_path: Path) -> None:
    win = _tiny_window("W1")
    tasks = build_task_plan(win.label, N_NODES, n_null=4, seed=5)
    calls = {"n": 0}

    def counting_train_fn(returns, meta):
        calls["n"] += 1
        return make_dummy_train_fn(N_NODES)(returns, meta)

    ckpt = tmp_path / "ckpt"
    results = run_window_plan(win, tasks, ckpt, counting_train_fn, log=False)
    assert len(results) == len(tasks)
    assert calls["n"] == len(tasks)
    for t in tasks:
        p = ckpt / win.label / f"{t.task_id.replace('/', '_')}.json"
        assert p.exists()
        payload = json.loads(p.read_text())
        assert "per_node_log_loss" in payload
        assert len(payload["per_node_log_loss"]) == N_NODES

    # resume: same ckpt dir -> zero new training calls.
    calls["n"] = 0
    results2 = run_window_plan(win, tasks, ckpt, counting_train_fn, log=False)
    assert calls["n"] == 0
    assert results2.keys() == results.keys()

    # delete one checkpoint -> exactly one retrain on the next call.
    victim = ckpt / win.label / "ablate_03.json"
    victim.unlink()
    calls["n"] = 0
    run_window_plan(win, tasks, ckpt, counting_train_fn, log=False)
    assert calls["n"] == 1


def test_driver_run_end_to_end_with_dummy_train_fn(tmp_path: Path) -> None:
    win_a = _tiny_window("W1", seed=11)
    win_b = _tiny_window("W2", seed=12)
    ckpt = tmp_path / "ckpt"
    train_fn = make_dummy_train_fn(N_NODES)
    compute_info = make_compute_info(ran_on_gpu=False, synthetic_train_fn_used=True)
    payload = driver_run(
        [win_a, win_b], ckpt, n_null=5, seed=1, source="unit-test",
        train_fn=train_fn, compute_info=compute_info,
    )
    assert payload["hypothesis"] == "H-14"
    assert payload["n_windows"] == 2
    assert payload["fdr_family_size"] == 2 * 99
    assert payload["compute_gating"]["gate_valid"] is False
    assert payload["weiter_indication"] is None
    # checkpoints exist for both windows, all tasks:
    for label in ("W1", "W2"):
        files = list((ckpt / label).glob("*.json"))
        assert len(files) == 1 + N_NODES + 5


# ---------------------------------------------------------------------------
# (d) compute gating honesty
# ---------------------------------------------------------------------------

def test_check_gpu_reports_honestly_without_attempting_a_run() -> None:
    info = check_gpu()
    assert info["torch_available"] is False  # sandbox has no torch
    assert info["cuda_available"] is False
    assert info["gpu_ready"] is False
    assert info["torch_version"] is None


def test_make_compute_info_gate_valid_only_for_real_gpu_run() -> None:
    assert make_compute_info(ran_on_gpu=True)["gate_valid"] is True
    assert make_compute_info(ran_on_gpu=False)["gate_valid"] is False
    assert make_compute_info(ran_on_gpu=True, cpu_fallback_used=True)["gate_valid"] is False
    assert make_compute_info(
        ran_on_gpu=True, synthetic_train_fn_used=True
    )["gate_valid"] is False


def test_cli_check_gpu_only_reports_and_exits_compute_required(tmp_path: Path) -> None:
    import os

    script = REPO_ROOT / "scripts" / "c14_panellag.py"
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    proc = subprocess.run(
        [sys.executable, str(script), "--check-gpu-only", "--out-dir", str(tmp_path)],
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert proc.returncode == 2, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    out = json.loads((tmp_path / "c14_gpu_check.json").read_text())
    assert out["torch_available"] is False
    assert out["gpu_ready"] is False
    assert out["hypothesis"] == "H-14"
    assert out["capital_free"] is True


def test_cli_full_run_without_gpu_or_fallback_aborts_before_any_run(tmp_path: Path) -> None:
    import os

    script = REPO_ROOT / "scripts" / "c14_panellag.py"
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    proc = subprocess.run(
        [sys.executable, str(script), "--base-dir", str(tmp_path / "nonexistent"),
         "--out-dir", str(tmp_path)],
        capture_output=True, text=True, env=env, timeout=60,
    )
    assert proc.returncode == 2, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "GPU erforderlich" in proc.stderr
    assert not (tmp_path / "c14_panellag_results.json").exists()


def test_cli_allow_cpu_fallback_end_to_end_not_verdict_bearing(tmp_path: Path) -> None:
    import os

    dates = ["2031-06-01"]
    base = _build_synthetic_tree(tmp_path, dates, trade_every_s=20)
    out_dir = tmp_path / "out"
    script = REPO_ROOT / "scripts" / "c14_panellag.py"
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
    proc = subprocess.run(
        [sys.executable, str(script),
         "--base-dir", str(base), "--out-dir", str(out_dir),
         "--window-a-start", dates[0], "--window-a-end", dates[0],
         "--window-b-start", dates[0], "--window-b-end", dates[0],
         "--n-null", "3", "--seed", "1", "--allow-cpu-fallback"],
        capture_output=True, text=True, env=env, timeout=300,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    json_path = out_dir / "c14_panellag_results.json"
    md_path = out_dir / "c14_panellag_results.md"
    assert json_path.exists() and md_path.exists()
    payload = json.loads(json_path.read_text())
    assert payload["hypothesis"] == "H-14"
    assert payload["capital_free"] is True
    assert payload["compute_gating"]["gpu_required"] is True
    assert payload["compute_gating"]["ran_on_gpu"] is False
    assert payload["compute_gating"]["gate_valid"] is False
    assert payload["weiter_indication"] is None  # JSON null: not verdict-bearing
    assert "H-14" in md_path.read_text(encoding="utf-8")
    # checkpoints persisted (resume-capable):
    assert (out_dir / "c14_checkpoints" / "W1" / "full.json").exists()
    assert (out_dir / "c14_checkpoints" / "W2" / "full.json").exists()


# ---------------------------------------------------------------------------
# (e) capital_free token scan
# ---------------------------------------------------------------------------

def test_capital_free_and_no_forbidden_tokens() -> None:
    j_src, i_tgt = 6, 7
    edge_boost = {(j_src, i_tgt): 0.05}
    for j in BTC_SOURCE_IDX:
        for i in ETH_TARGET_IDX:
            edge_boost[(j, i)] = 0.05
    window_stats = []
    for wlabel in ("W1", "W2"):
        results = _fake_results(n_null=30, edge_boost=edge_boost)
        stats = compute_window_edges(results, NODE_LABELS, NODE_BASES, n_null=30)
        stats.update({
            "window_label": wlabel, "start_date": "2030-01-01",
            "end_date": "2030-01-02", "node_labels": NODE_LABELS,
            "node_bases": NODE_BASES, "coverage": [1.0] * N_NODES,
        })
        window_stats.append(stats)
    payload = assemble_payload(
        window_stats, n_null=30, seed=1, source="unit-test",
        compute_info=make_compute_info(ran_on_gpu=True),
    )
    assert payload["capital_free"] is True
    blob = json.dumps(payload).lower()
    for tok in ("bps", "pnl", "sharpe", "friction", "edge_"):
        assert tok not in blob, f"forbidden capital token in payload: {tok!r}"
