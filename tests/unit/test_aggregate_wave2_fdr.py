"""Tests for the F-WAVE2 two-stage BH-FDR aggregator
(``scinance2-impl/handoff_local/aggregate_wave2_fdr.py``).

Stage 1 is computed inside each driver (F-LEADLAG / F-OFI / F-ENTROPY each
BH-FDR alpha=0.10). Stage 2 is the Welle-2 ueber-family F-WAVE2: BH-FDR
alpha=0.10 over all Stage-1-survivor p-values from H-04 + H-05 + H-06
combined. A variant counts as PASSED only if it survives BOTH stages -
this is the registry-disziplin-nachtrag from
``scinance2-impl/state/hypothesis_registry.md``.

The aggregator must be:
  * correct on Stage 2 (the Welle-2-ueber-family BH-FDR over combined
    survivors), including the case where Stage 1 survivors lose in Stage 2;
  * deterministic (bit-identical markdown for identical input);
  * schema-robust (an H-06 driver dir that lacks main-gate variants because
    every window failed PRE-Gate is not an error - the aggregator skips
    cleanly);
  * neutral on PRE-Gate and inverse_significant (those are reported
    separately and never enter F-WAVE2).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
AGG_PATH = REPO_ROOT / "scinance2-impl" / "handoff_local" / "aggregate_wave2_fdr.py"


def _load_aggregator():
    spec = importlib.util.spec_from_file_location("aggregate_wave2_fdr", AGG_PATH)
    assert spec and spec.loader, AGG_PATH
    mod = importlib.util.module_from_spec(spec)
    sys.modules["aggregate_wave2_fdr"] = mod
    spec.loader.exec_module(mod)
    return mod


AGG = _load_aggregator()


# ---------------------------------------------------------------------------
# Tiny fixture builders for fabricated driver payloads.
# ---------------------------------------------------------------------------

def _h04_variant(label: str, p: float, fdr: bool, *, axis: str = "TE",
                 source: str = "BTCUSDT") -> Dict[str, Any]:
    return {
        "axis": axis, "label": label, "lag": 1, "lag_ms": 1000.0,
        "source": source, "target": "ETHUSDT",
        "surrogate": {"observed_stat": 0.5, "p_value": float(p)},
        "fdr_significant": bool(fdr),
    }


def _h04_payload(window_variants: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    return {
        "hypothesis": "H-04",
        "n_windows": len(window_variants),
        "windows": [
            {"index": i, "n_bars": 100, "t0_ms": 0, "t1_ms": 0,
             "best_variant": v[0]["label"] if v else None,
             "criteria": {},
             "variants": v}
            for i, v in enumerate(window_variants)
        ],
    }


def _h05_variant(label: str, p: float, fdr: bool, *, sign: int = 1,
                 inverse: bool = False) -> Dict[str, Any]:
    return {
        "label": label, "delta_s": 1, "corr": 0.05 * sign,
        "sign_direction": int(sign), "abs_corr": 0.05, "hit_rate": 0.55,
        "surrogate_p": float(p),
        "fdr_significant": bool(fdr),
        "h05_positive_consistent": bool(fdr and sign > 0 and not inverse),
        "inverse_significant": bool(inverse),
    }


def _h05_payload(per_symbol_windows: Dict[str, List[List[Dict[str, Any]]]]) -> Dict[str, Any]:
    results = []
    for sym, windows in per_symbol_windows.items():
        for wi, variants in enumerate(windows):
            results.append({
                "symbol": sym, "window_index": wi,
                "t0_ms": 0, "t1_ms": 0, "variants": variants,
            })
    return {"hypothesis": "H-05", "symbols": list(per_symbol_windows),
            "results": results, "n_windows": max(len(v) for v in per_symbol_windows.values())}


def _h06_payload(per_symbol_windows: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """``per_symbol_windows[sym]`` = list of {pre_gate, variants} dicts."""
    results = []
    for sym, windows in per_symbol_windows.items():
        for wi, w in enumerate(windows):
            results.append({
                "symbol": sym, "window_index": wi,
                "t0_ms": 0, "t1_ms": 0,
                "pre_gate": w["pre_gate"],
                "variants": w["variants"],
            })
    return {"hypothesis": "H-06", "symbols": list(per_symbol_windows),
            "results": results,
            "n_windows": max(len(v) for v in per_symbol_windows.values())}


# ---------------------------------------------------------------------------
# 1. Stage-2 correctness: drives the BH-FDR over combined Stage-1 survivors.
# ---------------------------------------------------------------------------

def test_stage2_bh_fdr_combined_survivors_correctness() -> None:
    """5 Stage-1 survivors with p = [0.001, 0.05, 0.06, 0.08, 0.15].
    BH at alpha=0.10, m=5 -> thresholds k/m*alpha = [0.02, 0.04, 0.06, 0.08, 0.10].
    Sorted survivor p's: 0.001 (rank 1), 0.05 (rank 2), 0.06 (rank 3),
    0.08 (rank 4), 0.15 (rank 5).
    Largest k with p_k <= k/m*alpha: k=4 (0.08 <= 0.08). p_crit = 0.08.
    -> p=0.15 must NOT be in stage-2 survivors. The other four MUST be."""
    h05 = _h05_payload({
        "BTCUSDT": [
            [_h05_variant("v1", 0.001, True),
             _h05_variant("v2", 0.05, True),
             _h05_variant("v3", 0.06, True),
             _h05_variant("v4", 0.08, True),
             _h05_variant("v5", 0.15, True)],
        ],
    })
    agg = AGG.aggregate(None, h05, None)
    assert agg["stage2_input_n"] == 5
    assert agg["stage2_p_crit"] == pytest.approx(0.08)
    survivors = {v["label"]: v["f_wave2_significant"]
                 for v in agg["stage1_survivors_all"]}
    assert survivors == {"v1": True, "v2": True, "v3": True, "v4": True, "v5": False}


def test_stage2_can_lose_what_stage1_had_cross_family() -> None:
    """One H-04 + two H-05 survivors, with p that BH at m=3 only partially
    accepts. Specifically the Stage-1 survivors are p = [0.005, 0.09, 0.20]
    (from H-04, H-05, H-05). At m=3, alpha=0.1, thresholds = [1/30, 2/30, 3/30]
    = [0.0333, 0.0667, 0.1]. Sorted: 0.005 (rank 1 -> 0.005<=0.0333 yes),
    0.09 (rank 2 -> 0.09<=0.0667 no), 0.20 (rank 3 -> 0.20<=0.1 no).
    Largest k with pass = 1. p_crit=0.005. Only p=0.005 survives stage 2.
    -> the H-05 survivor with p=0.09 LOST in stage 2 (audit case)."""
    h04 = _h04_payload([[_h04_variant("h04_v0", 0.005, True)]])
    h05 = _h05_payload({"BTCUSDT": [
        [_h05_variant("h05_v0", 0.09, True),
         _h05_variant("h05_v1", 0.20, True)],
    ]})
    agg = AGG.aggregate(h04, h05, None)
    assert agg["stage2_input_n"] == 3
    assert agg["stage2_p_crit"] == pytest.approx(0.005)
    by_label = {v["label"]: v["f_wave2_significant"]
                for v in agg["stage1_survivors_all"]}
    assert by_label == {"h04_v0": True, "h05_v0": False, "h05_v1": False}

    # The audit tally must flag the H-05 loss in stage 2.
    tally = agg["stage1_per_family"]
    assert tally["F-LEADLAG (H-04)"]["n_stage1_survivors"] == 1
    assert tally["F-LEADLAG (H-04)"]["n_stage2_survivors"] == 1
    assert tally["F-LEADLAG (H-04)"]["n_lost_in_stage2"] == 0
    assert tally["F-OFI (H-05)"]["n_stage1_survivors"] == 2
    assert tally["F-OFI (H-05)"]["n_stage2_survivors"] == 0
    assert tally["F-OFI (H-05)"]["n_lost_in_stage2"] == 2


def test_stage2_only_uses_stage1_survivors_not_all_variants() -> None:
    """The aggregator must NOT recompute Stage 1 - it must use the driver's
    family_fdr_significant flag verbatim and run Stage 2 only on the
    survivors. To prove it: feed an H-04 with a tiny p=0.0001 that the
    driver marked as fdr_significant=False (counter-factual), and an H-05
    with a moderate p=0.01 that the driver marked fdr_significant=True.
    Stage-2 input must be 1 (just the H-05 entry), NOT 2."""
    h04 = _h04_payload([[_h04_variant("phantom", 0.0001, False)]])
    h05 = _h05_payload({"BTCUSDT": [[_h05_variant("real", 0.01, True)]]})
    agg = AGG.aggregate(h04, h05, None)
    assert agg["stage2_input_n"] == 1
    labels = [v["label"] for v in agg["stage1_survivors_all"]]
    assert labels == ["real"]


# ---------------------------------------------------------------------------
# 2. Determinism: same input -> bit-identical markdown.
# ---------------------------------------------------------------------------

def test_render_markdown_is_deterministic() -> None:
    """Same input -> identical markdown body. (The body must not embed a
    wall-clock timestamp; only the input must determine it.)"""
    h04 = _h04_payload([
        [_h04_variant("a", 0.01, True), _h04_variant("b", 0.40, False)],
        [_h04_variant("c", 0.02, True)],
    ])
    h05 = _h05_payload({"BTCUSDT": [[_h05_variant("o1", 0.03, True)]]})
    h06 = _h06_payload({"BTCUSDT": [
        {"pre_gate": {"rho": 0.4, "n_pairs": 100, "rho_floor_met": True},
         "variants": [{"label": "p1", "delta_min": 1, "mi": 0.1,
                       "auc_lift": 0.05, "n_g1": 30, "surrogate_p": 0.04,
                       "fdr_significant": True,
                       "auc_lift_floor_met": True,
                       "main_gate_variant_met": True}]},
    ]})
    agg1 = AGG.aggregate(h04, h05, h06)
    agg2 = AGG.aggregate(h04, h05, h06)
    md1 = AGG.render_markdown(agg1, run_label="x")
    md2 = AGG.render_markdown(agg2, run_label="x")
    assert md1 == md2
    # The body must not embed today's date / clock.
    import datetime as dt
    assert dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M") not in md1


# ---------------------------------------------------------------------------
# 3. Schema robustness: missing/malformed driver dirs must not crash.
# ---------------------------------------------------------------------------

def test_h06_pre_gate_failer_payload_does_not_break_aggregator() -> None:
    """H-06 PRE-Gate failure does NOT zero out the main-gate variants in the
    driver output - the driver still runs MI/AUC and reports them, plus
    pre_gate.rho_floor_met=False per window. The aggregator must:
      * report the failing rho rows in the dedicated PRE-Gate section;
      * still include any main-gate variants in F-ENTROPY (Stage 1) - even
        though the gate-auditor will DROP H-06 on the PRE-Gate floor.
    PRE-Gate must NEVER enter F-WAVE2 (it is not a p-value test)."""
    h06 = _h06_payload({"BTCUSDT": [
        {"pre_gate": {"rho": 0.10, "n_pairs": 100, "rho_floor_met": False},
         "variants": [{"label": "main_v", "delta_min": 1, "mi": 0.05,
                       "auc_lift": 0.01, "n_g1": 20, "surrogate_p": 0.02,
                       "fdr_significant": True, "auc_lift_floor_met": False,
                       "main_gate_variant_met": False}]},
    ]})
    agg = AGG.aggregate(None, None, h06)
    assert agg["h06_pre_gate"][0]["rho_floor_met"] is False
    # Stage-1 survivor exists (driver flag honored); PRE-Gate is NOT in F-WAVE2.
    assert agg["stage1_per_family"]["F-ENTROPY (H-06)"]["n_stage1_survivors"] == 1
    # The markdown must mention the PRE-Gate section.
    md = AGG.render_markdown(agg)
    assert "H-06 PRE-Gate" in md
    assert "nicht in F-WAVE2" in md.lower() or "NICHT in F-WAVE2" in md


def test_missing_driver_dir_is_tolerated(tmp_path: Path) -> None:
    """If a driver dir is missing or its JSON is malformed, the aggregator
    records the gap and continues. The CLI exit code is 0 (run survives)."""
    h04_dir = tmp_path / "h04"; h04_dir.mkdir()
    h05_dir = tmp_path / "h05"; h05_dir.mkdir()
    h06_dir = tmp_path / "h06"; h06_dir.mkdir()
    # Only H-05 has a payload; H-04 dir empty; H-06 has a malformed JSON.
    (h05_dir / "c01_ofi_sign_results.json").write_text(
        json.dumps(_h05_payload({"BTC": [[_h05_variant("only", 0.01, True)]]})),
        encoding="utf-8",
    )
    (h06_dir / "c07_pe_results.json").write_text("{this is not json", encoding="utf-8")
    out_md = tmp_path / "WAVE2_SUMMARY.md"
    rc = AGG.main([
        "--h04", str(h04_dir), "--h05", str(h05_dir), "--h06", str(h06_dir),
        "--out", str(out_md),
    ])
    assert rc == 0
    text = out_md.read_text(encoding="utf-8")
    assert "H-04 (F-LEADLAG) | nein" in text
    assert "H-05 (F-OFI) | ja" in text
    assert "H-06 (F-ENTROPY) | nein" in text


# ---------------------------------------------------------------------------
# 4. H-05 inverse_significant: reported separately (NOT a pass), and must
#    appear in the H-05b-trigger section.
# ---------------------------------------------------------------------------

def test_h05_inverse_significant_is_reported_separately() -> None:
    """An H-05 variant with sign_direction=-1 + driver-fdr_sig + inverse_sig
    flag is an H-05b trigger, NOT an H-05 pass. The aggregator does not
    re-judge - it surfaces the flag in the dedicated section."""
    h05 = _h05_payload({"BTCUSDT": [[
        _h05_variant("inv", 0.001, True, sign=-1, inverse=True),
    ]]})
    agg = AGG.aggregate(None, h05, None)
    assert len(agg["h05_inverse_flags"]) == 1
    flag = agg["h05_inverse_flags"][0]
    assert flag["symbol"] == "BTCUSDT"
    assert flag["p_value"] == pytest.approx(0.001)
    md = AGG.render_markdown(agg)
    assert "inverse_significant" in md
    assert "H-05b" in md


# ---------------------------------------------------------------------------
# 5. CLI end-to-end smoke (writes md + json sidecar).
# ---------------------------------------------------------------------------

def test_cli_writes_markdown_and_json_sidecar(tmp_path: Path) -> None:
    h04_dir = tmp_path / "h04"; h04_dir.mkdir()
    h05_dir = tmp_path / "h05"; h05_dir.mkdir()
    h06_dir = tmp_path / "h06"; h06_dir.mkdir()
    (h04_dir / "c17_c41_results.json").write_text(json.dumps(
        _h04_payload([[_h04_variant("a", 0.01, True)]])), encoding="utf-8")
    (h05_dir / "c01_ofi_sign_results.json").write_text(json.dumps(
        _h05_payload({"BTC": [[_h05_variant("o", 0.02, True)]]})), encoding="utf-8")
    (h06_dir / "c07_pe_results.json").write_text(json.dumps(
        _h06_payload({"BTC": [
            {"pre_gate": {"rho": 0.4, "n_pairs": 100, "rho_floor_met": True},
             "variants": [{"label": "m", "delta_min": 1, "mi": 0.1,
                           "auc_lift": 0.05, "n_g1": 30, "surrogate_p": 0.03,
                           "fdr_significant": True,
                           "auc_lift_floor_met": True,
                           "main_gate_variant_met": True}]},
        ]})), encoding="utf-8")
    out_md = tmp_path / "WAVE2_SUMMARY.md"
    out_json = tmp_path / "wave2_summary.json"
    rc = AGG.main([
        "--h04", str(h04_dir), "--h05", str(h05_dir), "--h06", str(h06_dir),
        "--out", str(out_md), "--json", str(out_json),
    ])
    assert rc == 0
    assert out_md.is_file() and out_md.read_text(encoding="utf-8").startswith("# F-WAVE2")
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert "stage1_per_family" in data and "stage2_survivors" in data


# ---------------------------------------------------------------------------
# 6. Runner static lint: BOM + ASCII body + balance, no interactive prompts.
# ---------------------------------------------------------------------------

HANDOFF_DIR = REPO_ROOT / "scinance2-impl" / "handoff_local"


def test_run_wave2_ps1_is_utf8_bom_and_ascii_body() -> None:
    """run_wave2.ps1 must start with a UTF-8 BOM and contain no non-ASCII
    bytes in its body - the PowerShell 5.1 parser depends on it (mirrors the
    constraint enforced for run_cfar_only.ps1 in test_c31_cfar.py)."""
    ps1 = HANDOFF_DIR / "run_wave2.ps1"
    data = ps1.read_bytes()
    assert data.startswith(b"\xef\xbb\xbf"), "run_wave2.ps1 missing UTF-8 BOM"
    body = data[3:]
    bad = [(i, b) for i, b in enumerate(body) if b > 0x7F]
    assert not bad, f"non-ASCII bytes in run_wave2.ps1 body: {bad[:5]}"


def test_run_wave2_sh_is_ascii_body() -> None:
    """run_wave2.sh must be pure ASCII (no BOM, no UTF-8 dashes)."""
    sh = HANDOFF_DIR / "run_wave2.sh"
    data = sh.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf"), "run_wave2.sh has unexpected BOM"
    bad = [(i, b) for i, b in enumerate(data) if b > 0x7F]
    assert not bad, f"non-ASCII bytes in run_wave2.sh: {bad[:5]}"


def test_run_wave2_ps1_brace_and_paren_balance() -> None:
    """Strip comments and string literals, then check brace/paren balance.
    Mirrors the lint the Welle-1 runners passed during WP-5 hardening."""
    import re
    ps1 = HANDOFF_DIR / "run_wave2.ps1"
    text = ps1.read_bytes()[3:].decode("ascii")  # strip BOM
    no_comments = re.sub(r"(?m)#.*$", "", text)
    no_strings = re.sub(r"'(?:[^'\\]|\\.)*'", "''", no_comments)
    no_strings = re.sub(r'"(?:[^"\\]|\\.)*"', '""', no_strings)
    assert no_strings.count("{") == no_strings.count("}"), "PS1 brace imbalance"
    assert no_strings.count("(") == no_strings.count(")"), "PS1 paren imbalance"


def test_runners_have_no_interactive_prompts() -> None:
    """T3-Regel: a runner must NEVER block on user input. The Welle-1
    overnight runner survived a 2026-06-13 incident by being interaction-
    free; the Welle-2 runners must hold the same rule."""
    for name in ("run_wave2.ps1", "run_wave2.sh"):
        text = (HANDOFF_DIR / name).read_bytes().decode("ascii", errors="ignore")
        for forbidden in ("Read-Host", "input(", "\nPause\n", "Pause "):
            assert forbidden not in text, (
                f"{name} contains interactive prompt token '{forbidden}'"
            )


def test_run_wave2_sh_passes_bash_n() -> None:
    """`bash -n run_wave2.sh` must succeed (syntactic-only check)."""
    import subprocess
    sh = HANDOFF_DIR / "run_wave2.sh"
    r = subprocess.run(["bash", "-n", str(sh)], capture_output=True, text=True)
    assert r.returncode == 0, f"bash -n failed: {r.stderr}"


# ---------------------------------------------------------------------------
# 7. H-04b runner static lint (run_h04b.{ps1,sh}, T2 Tradability handoff).
#    Same constraints as the Welle-2 runners: PS1 needs a UTF-8 BOM + ASCII
#    body so the PowerShell 5.1 parser is happy; SH stays pure ASCII; both
#    must balance braces/parens, never block on input, and pass `bash -n`.
# ---------------------------------------------------------------------------


def test_run_h04b_ps1_is_utf8_bom_and_ascii_body() -> None:
    """run_h04b.ps1 must start with a UTF-8 BOM and contain no non-ASCII
    bytes in its body (PowerShell 5.1 parser depends on it; mirrors the
    constraint enforced for run_wave2.ps1 / run_cfar_only.ps1)."""
    ps1 = HANDOFF_DIR / "run_h04b.ps1"
    data = ps1.read_bytes()
    assert data.startswith(b"\xef\xbb\xbf"), "run_h04b.ps1 missing UTF-8 BOM"
    body = data[3:]
    bad = [(i, b) for i, b in enumerate(body) if b > 0x7F]
    assert not bad, f"non-ASCII bytes in run_h04b.ps1 body: {bad[:5]}"


def test_run_h04b_sh_is_ascii_body() -> None:
    """run_h04b.sh must be pure ASCII (no BOM, no UTF-8 dashes/paragraph signs)."""
    sh = HANDOFF_DIR / "run_h04b.sh"
    data = sh.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf"), "run_h04b.sh has unexpected BOM"
    bad = [(i, b) for i, b in enumerate(data) if b > 0x7F]
    assert not bad, f"non-ASCII bytes in run_h04b.sh: {bad[:5]}"


def test_run_h04b_ps1_brace_and_paren_balance() -> None:
    """Strip comments and string literals, then check brace/paren balance.
    Mirrors the lint the Welle-1/Welle-2 runners passed during hardening."""
    import re
    ps1 = HANDOFF_DIR / "run_h04b.ps1"
    text = ps1.read_bytes()[3:].decode("ascii")  # strip BOM
    no_comments = re.sub(r"(?m)#.*$", "", text)
    no_strings = re.sub(r"'(?:[^'\\]|\\.)*'", "''", no_comments)
    no_strings = re.sub(r'"(?:[^"\\]|\\.)*"', '""', no_strings)
    assert no_strings.count("{") == no_strings.count("}"), "PS1 brace imbalance"
    assert no_strings.count("(") == no_strings.count(")"), "PS1 paren imbalance"


def test_run_h04b_runners_have_no_interactive_prompts() -> None:
    """A handoff runner must NEVER block on user input (T2/T3 rule, same
    interaction-free guarantee the overnight runner relies on)."""
    for name in ("run_h04b.ps1", "run_h04b.sh"):
        text = (HANDOFF_DIR / name).read_bytes().decode("ascii", errors="ignore")
        for forbidden in ("Read-Host", "input(", "\nPause\n", "Pause "):
            assert forbidden not in text, (
                f"{name} contains interactive prompt token '{forbidden}'"
            )


def test_run_h04b_sh_passes_bash_n() -> None:
    """`bash -n run_h04b.sh` must succeed (syntactic-only check)."""
    import subprocess
    sh = HANDOFF_DIR / "run_h04b.sh"
    r = subprocess.run(["bash", "-n", str(sh)], capture_output=True, text=True)
    assert r.returncode == 0, f"bash -n failed: {r.stderr}"


def test_run_h04b_primary_is_judgment_bearing_and_sensitivity_is_marked() -> None:
    """Anti-Gaming-Klausel: the urteilstragende run is the 300ms/11bps/Taker
    H04B_PRIMARY block; the latency-sensitivity and maker runs must be present
    AND explicitly marked as NICHT urteilstragend in both runners."""
    for name in ("run_h04b.ps1", "run_h04b.sh"):
        text = (HANDOFF_DIR / name).read_bytes().decode("ascii", errors="ignore")
        # The four named blocks all exist.
        for block in ("H04B_PRIMARY", "H04B_LAT100", "H04B_LAT500", "H04B_MAKER"):
            assert block in text, f"{name} missing block {block}"
        # The judgment-bearing defaults (300ms latency, 11bps wall) are present.
        assert "300" in text and "11" in text, f"{name} missing 300ms/11bps defaults"
        # The maker secondary flag is wired.
        assert "--maker-secondary" in text, f"{name} missing --maker-secondary"
        # Sensitivity runs are flagged as not judgment-bearing (Anti-Gaming).
        assert "NICHT urteilstragend" in text, (
            f"{name} does not mark sensitivity/maker runs as NICHT urteilstragend"
        )
