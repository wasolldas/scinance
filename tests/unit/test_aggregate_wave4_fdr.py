"""Tests for the F-XDOM1 two-stage BH-FDR aggregator
(``scinance2-impl/handoff_local/aggregate_wave4_fdr.py``).

Stage 1 is computed inside each driver (F-BUNCH / F-POINTER / F-FRAG, each
BH-FDR alpha=0.10). Stage 2 is the Welle-4 ueber-family F-XDOM1: BH-FDR
alpha=0.10 over all Stage-1-survivor p-values from H-09 + H-10 + H-12
combined. A cell counts as PASSED only if it survives BOTH stages - this is
the F-XDOM1 pre-registration (DEC-22) in
``scinance2-impl/state/hypothesis_registry.md``.

The aggregator must be:
  * correct on Stage 2 (BH-FDR over combined survivors), including the case
    where Stage-1 survivors lose in Stage 2;
  * faithful to the driver Stage-1 flags (never recompute Stage 1);
  * deterministic (bit-identical markdown for identical input);
  * schema-robust (missing/malformed driver output is a recorded gap, never
    an exception);
  * neutral on the non-p-value gate parts (H-09 anti-gaming, H-10 N-floor,
    H-12 validity precondition / criteria (b)/(c) - reported separately,
    never in F-XDOM1).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
AGG_PATH = REPO_ROOT / "scinance2-impl" / "handoff_local" / "aggregate_wave4_fdr.py"


def _load_aggregator():
    spec = importlib.util.spec_from_file_location("aggregate_wave4_fdr", AGG_PATH)
    assert spec and spec.loader, AGG_PATH
    mod = importlib.util.module_from_spec(spec)
    sys.modules["aggregate_wave4_fdr"] = mod
    spec.loader.exec_module(mod)
    return mod


AGG = _load_aggregator()


# ---------------------------------------------------------------------------
# Tiny fixture builders for fabricated driver payloads (schemas mirror the
# real run() outputs of c09_bunch / c10_pointer / c12_frag).
# ---------------------------------------------------------------------------

def _h09_cell(symbol: str, wi: int, p: float, fdr: bool, *,
              valid: bool = True, sentinel: bool = False,
              passed: bool = False) -> Dict[str, Any]:
    return {
        "symbol": symbol, "window_index": wi,
        "window_label": f"W{wi + 1}@2026",
        "b_minus": 1.2, "b_plus": 0.3, "b_asymmetry": 0.9,
        "b_placebo_max": 0.4,
        "bootstrap_p": float(p),
        "cell_valid": bool(valid),
        "sentinel_missing_data": bool(sentinel),
        "kink_is_placeholder": False,
        "fdr_significant": bool(fdr),
        "passed": bool(passed),
    }


def _h09_payload(cells: List[Dict[str, Any]], **flags: Any) -> Dict[str, Any]:
    payload = {
        "hypothesis": "H-09", "fdr_family": "F-BUNCH", "fdr_alpha": 0.10,
        "fdr_p_crit": 0.05,
        "gate_valid_assumptions": True, "family_size_deviation": False,
        "n_sentinel_cells": 0, "any_window_truncated": False,
        "kink_placeholder_symbols": [], "placeholder_driven_pass_only": False,
        "cells": cells,
    }
    payload.update(flags)
    return payload


def _h10_cell(stage: int, label: str, p: float, fdr: bool, *,
              n_pointer: int = 4, floor: bool = True,
              cell_pass: bool = False) -> Dict[str, Any]:
    c: Dict[str, Any] = {
        "stage": stage, "window_label": label,
        "n_pointer_floor_met": bool(floor),
        "p_for_fdr": float(p),
        "fdr_significant": bool(fdr),
        "cell_pass": bool(cell_pass),
    }
    if stage == 1:
        c["n_pointer"] = n_pointer
        c["surrogate_p"] = float(p)
    else:
        c["n_pointer_in_window"] = n_pointer
        c["permutation_p_two_sided"] = float(p)
    return c


def _h10_payload(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "hypothesis": "H-10", "fdr_family": "F-POINTER", "fdr_alpha": 0.10,
        "fdr_p_crit": 0.05, "all_four_cells_pass": False,
        "cells": cells,
    }


def _h12_day(date: str, p: float, fdr: bool, *, ipr_v2: float = 0.5,
             exch: str = "deribit", analyzed: bool = True) -> Dict[str, Any]:
    if not analyzed:
        return {"date": date, "panel_valid": False, "analyzed": False,
                "degenerate": False}
    return {
        "date": date, "panel_valid": True, "analyzed": True,
        "degenerate": False, "lambda2": 1.3, "ipr_v2": float(ipr_v2),
        "dominant_exchange_v2": exch,
        "p_lambda2_one_factor": float(p),
        "fdr_significant": bool(fdr),
    }


def _h12_window(label: str, days: List[Dict[str, Any]], *,
                window_valid: bool = True) -> Dict[str, Any]:
    analyzed = [d for d in days if d.get("analyzed")]
    sig = [d for d in analyzed if d.get("fdr_significant")]
    return {
        "window_label": label,
        "n_days_valid": len(analyzed),
        "n_days_fdr_significant": len(sig),
        "days": days,
        "validity": {"window_valid": bool(window_valid),
                     "ipr_v1_ok_share": 1.0},
        "criteria": {
            "a_sig_day_share": (len(sig) / len(analyzed)) if analyzed else None,
            "a_met": bool(analyzed) and len(sig) / max(len(analyzed), 1) >= 0.20,
            "b_median_ipr_v2_sig": 0.5 if sig else None,
            "b_met": bool(sig),
            "c_dominant_exchange": "deribit" if sig else None,
            "c_dominant_exchange_share": 1.0 if sig else None,
            "c_met": bool(sig),
        },
        "all_criteria_met": bool(sig),
    }


def _h12_payload(windows: List[Dict[str, Any]]) -> Dict[str, Any]:
    n_tests = sum(1 for w in windows for d in w["days"] if d.get("analyzed"))
    return {
        "hypothesis": "H-12", "fdr_family": "F-FRAG", "fdr_alpha": 0.10,
        "fdr_p_crit": 0.05, "fdr_family_size": n_tests,
        "validity_status": "gueltig", "all_windows_valid": True,
        "all_criteria_met_all_windows": False,
        "windows": windows,
    }


# ---------------------------------------------------------------------------
# 1. No-survivors case: Stage 2 must be a clean no-op.
# ---------------------------------------------------------------------------

def test_no_stage1_survivors_stage2_is_empty() -> None:
    """All drivers present, no cell FDR-significant in Stage 1 -> Stage-2
    input empty, p_crit 0.0, markdown says Stage 2 entfaellt."""
    h09 = _h09_payload([_h09_cell("BTCUSDT", 0, 0.30, False),
                        _h09_cell("BTCUSDT", 1, 0.50, False)])
    h10 = _h10_payload([_h10_cell(1, "W1", 0.40, False),
                        _h10_cell(2, "W1", 0.90, False)])
    h12 = _h12_payload([_h12_window("W1", [_h12_day("2026-04-01", 0.70, False)])])
    agg = AGG.aggregate(h09, h10, h12)
    assert agg["stage2_input_n"] == 0
    assert agg["stage2_p_crit"] == 0.0
    assert agg["stage2_survivors"] == []
    for t in agg["stage1_per_family"].values():
        assert t["n_stage1_survivors"] == 0
        assert t["n_stage2_survivors"] == 0
        assert t["n_lost_in_stage2"] == 0
    md = AGG.render_markdown(agg)
    assert "(keine Stage-1-Survivor - Stage 2 entfaellt.)" in md


# ---------------------------------------------------------------------------
# 2. All-survive case: BH correctness when every Stage-1 survivor also
#    survives Stage 2.
# ---------------------------------------------------------------------------

def test_all_stage1_survivors_survive_stage2() -> None:
    """3 Stage-1 survivors with p = [0.001, 0.01, 0.02] (one per family).
    BH at alpha=0.10, m=3 -> thresholds [0.0333, 0.0667, 0.10]. All pass
    (0.02 <= 0.10 at rank 3 -> k_max=3, p_crit=0.02)."""
    h09 = _h09_payload([_h09_cell("BTCUSDT", 0, 0.001, True, passed=True)])
    h10 = _h10_payload([_h10_cell(1, "W1", 0.01, True, cell_pass=True)])
    h12 = _h12_payload([_h12_window("W1", [_h12_day("2026-04-01", 0.02, True)])])
    agg = AGG.aggregate(h09, h10, h12)
    assert agg["stage2_input_n"] == 3
    assert agg["stage2_p_crit"] == pytest.approx(0.02)
    assert all(v["f_xdom1_significant"] for v in agg["stage1_survivors_all"])
    for t in agg["stage1_per_family"].values():
        assert t["n_stage1_survivors"] == 1
        assert t["n_stage2_survivors"] == 1
        assert t["n_lost_in_stage2"] == 0


# ---------------------------------------------------------------------------
# 3. Partial survive: a Stage-1 survivor LOSES in Stage 2 (the audit case).
# ---------------------------------------------------------------------------

def test_stage1_survivor_can_lose_in_stage2_cross_family() -> None:
    """Stage-1 survivors p = [0.005 (H-09), 0.09 (H-10), 0.20 (H-12)].
    BH m=3, alpha=0.1 -> thresholds [0.0333, 0.0667, 0.10]. Sorted:
    0.005 (rank 1, passes), 0.09 (rank 2, 0.09 > 0.0667 fails),
    0.20 (rank 3, fails). k_max=1, p_crit=0.005 -> only the H-09 cell
    survives Stage 2; H-10 and H-12 LOSE what they had in Stage 1."""
    h09 = _h09_payload([_h09_cell("BTCUSDT", 0, 0.005, True, passed=True)])
    h10 = _h10_payload([_h10_cell(1, "W1", 0.09, True, cell_pass=True)])
    h12 = _h12_payload([_h12_window("W1", [_h12_day("2026-04-01", 0.20, True)])])
    agg = AGG.aggregate(h09, h10, h12)
    assert agg["stage2_input_n"] == 3
    assert agg["stage2_p_crit"] == pytest.approx(0.005)
    by_label = {v["label"]: v["f_xdom1_significant"]
                for v in agg["stage1_survivors_all"]}
    assert by_label == {"BTCUSDT/w0": True, "S1/W1": False,
                        "W1/2026-04-01": False}

    tally = agg["stage1_per_family"]
    assert tally["F-BUNCH (H-09)"]["n_lost_in_stage2"] == 0
    assert tally["F-POINTER (H-10)"]["n_stage1_survivors"] == 1
    assert tally["F-POINTER (H-10)"]["n_stage2_survivors"] == 0
    assert tally["F-POINTER (H-10)"]["n_lost_in_stage2"] == 1
    assert tally["F-FRAG (H-12)"]["n_lost_in_stage2"] == 1
    md = AGG.render_markdown(agg)
    assert "F-XDOM1-Ueber-Familie greift" in md


def test_stage2_only_uses_stage1_survivors_not_all_variants() -> None:
    """The aggregator must NOT recompute Stage 1 - it must honour the
    driver's fdr_significant flag verbatim. Feed an H-09 cell with a tiny
    p=0.0001 marked fdr_significant=False (counter-factual) and an H-10
    cell with p=0.01 marked True. Stage-2 input must be 1, not 2."""
    h09 = _h09_payload([_h09_cell("BTCUSDT", 0, 0.0001, False)])
    h10 = _h10_payload([_h10_cell(1, "W1", 0.01, True)])
    agg = AGG.aggregate(h09, h10, None)
    assert agg["stage2_input_n"] == 1
    assert [v["label"] for v in agg["stage1_survivors_all"]] == ["S1/W1"]


def test_h12_unanalyzed_days_and_h10_undefined_p_are_handled() -> None:
    """Non-analyzed H-12 days carry no p and must be excluded from the
    family; an H-10 cell whose p_for_fdr is missing falls back to the
    stage field, and a fully undefined p becomes the driver's worst-case
    1.0 (never a survivor)."""
    h12 = _h12_payload([_h12_window("W1", [
        _h12_day("2026-04-01", 0.01, True),
        _h12_day("2026-04-02", 0.0, False, analyzed=False),
    ])])
    h10_cell = {  # p_for_fdr and permutation p both missing (cleaned NaN)
        "stage": 2, "window_label": "W2", "n_pointer_in_window": 0,
        "n_pointer_floor_met": False, "p_for_fdr": None,
        "permutation_p_two_sided": None,
        "fdr_significant": False, "cell_pass": False,
    }
    agg = AGG.aggregate(None, _h10_payload([h10_cell]), h12)
    assert agg["stage1_per_family"]["F-FRAG (H-12)"]["n_variants_total"] == 1
    h10_entries = agg["all_variants"]["H-10"]
    assert len(h10_entries) == 1
    assert h10_entries[0]["p_value"] == 1.0
    assert agg["stage2_input_n"] == 1  # only the H-12 survivor


# ---------------------------------------------------------------------------
# 4. Missing-driver-output case: recorded gap, never an exception.
# ---------------------------------------------------------------------------

def test_missing_driver_dir_is_tolerated(tmp_path: Path) -> None:
    """If a driver dir is missing/empty or its JSON is malformed, the
    aggregator records the gap and continues. CLI exit code stays 0."""
    h09_dir = tmp_path / "h09"; h09_dir.mkdir()
    h10_dir = tmp_path / "h10"; h10_dir.mkdir()
    h12_dir = tmp_path / "h12"; h12_dir.mkdir()
    # Only H-10 has a payload; H-09 dir empty; H-12 has malformed JSON.
    (h10_dir / "c10_pointer_results.json").write_text(
        json.dumps(_h10_payload([_h10_cell(1, "W1", 0.01, True)])),
        encoding="utf-8",
    )
    (h12_dir / "c12_frag_results.json").write_text("{this is not json",
                                                   encoding="utf-8")
    out_md = tmp_path / "WAVE4_SUMMARY.md"
    rc = AGG.main([
        "--h09", str(h09_dir), "--h10", str(h10_dir), "--h12", str(h12_dir),
        "--out", str(out_md),
    ])
    assert rc == 0
    text = out_md.read_text(encoding="utf-8")
    assert "H-09 (F-BUNCH) | nein" in text
    assert "H-10 (F-POINTER) | ja" in text
    assert "H-12 (F-FRAG) | nein" in text


# ---------------------------------------------------------------------------
# 5. Determinism: same input twice -> bit-identical markdown.
# ---------------------------------------------------------------------------

def test_render_markdown_is_deterministic() -> None:
    """Same input -> identical markdown body (no wall-clock timestamp)."""
    h09 = _h09_payload([
        _h09_cell("BTCUSDT", 0, 0.01, True, passed=True),
        _h09_cell("BTCUSDT", 1, 0.40, False),
        _h09_cell("ETHUSDT", 0, 0.02, True),
    ])
    h10 = _h10_payload([
        _h10_cell(1, "W1", 0.03, True), _h10_cell(1, "W2", 0.20, False),
        _h10_cell(2, "W1", 0.60, False), _h10_cell(2, "W2", 0.70, False),
    ])
    h12 = _h12_payload([
        _h12_window("W1", [_h12_day("2026-04-01", 0.005, True),
                           _h12_day("2026-04-02", 0.90, False)]),
        _h12_window("W2", [_h12_day("2026-06-01", 0.04, True)]),
    ])
    agg1 = AGG.aggregate(h09, h10, h12)
    agg2 = AGG.aggregate(h09, h10, h12)
    md1 = AGG.render_markdown(agg1, run_label="x")
    md2 = AGG.render_markdown(agg2, run_label="x")
    assert md1 == md2
    # The body must not embed today's date / clock.
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc)
    assert now.strftime("%Y-%m-%d %H:%M") not in md1


# ---------------------------------------------------------------------------
# 6. Non-p-value gate parts stay out of F-XDOM1 but ARE reported.
# ---------------------------------------------------------------------------

def test_non_p_value_gate_parts_reported_separately() -> None:
    """H-09 anti-gaming flags, H-10 N-floor and H-12 validity precondition
    must be surfaced in the report but never change Stage-2 membership."""
    h09 = _h09_payload(
        [_h09_cell("BTCUSDT", 0, 0.01, True)],
        gate_valid_assumptions=False, family_size_deviation=True,
        n_sentinel_cells=2,
    )
    h10 = _h10_payload([_h10_cell(1, "W1", 0.02, True, n_pointer=1,
                                  floor=False)])
    h12 = _h12_payload([_h12_window("W1", [_h12_day("2026-04-01", 0.03, True)],
                                    window_valid=False)])
    h12["validity_status"] = "ungueltig"
    h12["all_windows_valid"] = False
    agg = AGG.aggregate(h09, h10, h12)
    # All three Stage-1 survivors enter Stage 2 regardless of the flags.
    assert agg["stage2_input_n"] == 3
    md = AGG.render_markdown(agg)
    assert "gate_valid_assumptions=nein" in md
    assert "NICHT in F-XDOM1" in md
    assert "UNGUELTIG" in md
    assert "N_pointer-Floor" in md


# ---------------------------------------------------------------------------
# 7. CLI end-to-end smoke (writes md + json sidecar).
# ---------------------------------------------------------------------------

def test_cli_writes_markdown_and_json_sidecar(tmp_path: Path) -> None:
    h09_dir = tmp_path / "h09"; h09_dir.mkdir()
    h10_dir = tmp_path / "h10"; h10_dir.mkdir()
    h12_dir = tmp_path / "h12"; h12_dir.mkdir()
    (h09_dir / "c09_bunch_results.json").write_text(json.dumps(
        _h09_payload([_h09_cell("BTCUSDT", 0, 0.01, True)])), encoding="utf-8")
    (h10_dir / "c10_pointer_results.json").write_text(json.dumps(
        _h10_payload([_h10_cell(1, "W1", 0.02, True)])), encoding="utf-8")
    (h12_dir / "c12_frag_results.json").write_text(json.dumps(
        _h12_payload([_h12_window("W1", [_h12_day("2026-04-01", 0.03, True)])])),
        encoding="utf-8")
    out_md = tmp_path / "WAVE4_SUMMARY.md"
    out_json = tmp_path / "wave4_summary.json"
    rc = AGG.main([
        "--h09", str(h09_dir), "--h10", str(h10_dir), "--h12", str(h12_dir),
        "--out", str(out_md), "--json", str(out_json),
    ])
    assert rc == 0
    assert out_md.is_file()
    assert out_md.read_text(encoding="utf-8").startswith("# F-XDOM1")
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert "stage1_per_family" in data and "stage2_survivors" in data


# ---------------------------------------------------------------------------
# 8. Runner static lint: BOM + ASCII body + balance, no interactive prompts
#    (same constraints test_aggregate_wave2_fdr.py enforces for run_wave2).
# ---------------------------------------------------------------------------

HANDOFF_DIR = REPO_ROOT / "scinance2-impl" / "handoff_local"


def test_run_wave4_ps1_is_utf8_bom_and_ascii_body() -> None:
    """run_wave4.ps1 must start with a UTF-8 BOM and contain no non-ASCII
    bytes in its body - the PowerShell 5.1 parser depends on it."""
    ps1 = HANDOFF_DIR / "run_wave4.ps1"
    data = ps1.read_bytes()
    assert data.startswith(b"\xef\xbb\xbf"), "run_wave4.ps1 missing UTF-8 BOM"
    body = data[3:]
    bad = [(i, b) for i, b in enumerate(body) if b > 0x7F]
    assert not bad, f"non-ASCII bytes in run_wave4.ps1 body: {bad[:5]}"


def test_run_wave4_sh_is_ascii_body() -> None:
    """run_wave4.sh must be pure ASCII (no BOM, no UTF-8 dashes)."""
    sh = HANDOFF_DIR / "run_wave4.sh"
    data = sh.read_bytes()
    assert not data.startswith(b"\xef\xbb\xbf"), "run_wave4.sh has unexpected BOM"
    bad = [(i, b) for i, b in enumerate(data) if b > 0x7F]
    assert not bad, f"non-ASCII bytes in run_wave4.sh: {bad[:5]}"


def test_run_wave4_ps1_brace_and_paren_balance() -> None:
    """Strip comments and string literals, then check brace/paren balance."""
    import re
    ps1 = HANDOFF_DIR / "run_wave4.ps1"
    text = ps1.read_bytes()[3:].decode("ascii")  # strip BOM
    no_comments = re.sub(r"(?m)#.*$", "", text)
    no_strings = re.sub(r"'(?:[^'\\]|\\.)*'", "''", no_comments)
    no_strings = re.sub(r'"(?:[^"\\]|\\.)*"', '""', no_strings)
    assert no_strings.count("{") == no_strings.count("}"), "PS1 brace imbalance"
    assert no_strings.count("(") == no_strings.count(")"), "PS1 paren imbalance"


def test_run_wave4_runners_have_no_interactive_prompts() -> None:
    """T3-Regel: a runner must NEVER block on user input."""
    for name in ("run_wave4.ps1", "run_wave4.sh"):
        text = (HANDOFF_DIR / name).read_bytes().decode("ascii", errors="ignore")
        for forbidden in ("Read-Host", "input(", "\nPause\n", "Pause "):
            assert forbidden not in text, (
                f"{name} contains interactive prompt token '{forbidden}'"
            )


def test_run_wave4_sh_passes_bash_n() -> None:
    """`bash -n run_wave4.sh` must succeed (syntactic-only check)."""
    import subprocess
    sh = HANDOFF_DIR / "run_wave4.sh"
    r = subprocess.run(["bash", "-n", str(sh)], capture_output=True, text=True)
    assert r.returncode == 0, f"bash -n failed: {r.stderr}"


def test_run_wave4_checks_unlock_gates_and_runs_cohort() -> None:
    """The consolidated runner must (a) check the H-11/H-13 unlock gates via
    --check-unlock-only, (b) invoke the three cohort CLIs directly (NOT the
    individual run_h0X wrappers), and (c) end with the F-XDOM1 aggregation."""
    for name in ("run_wave4.ps1", "run_wave4.sh"):
        text = (HANDOFF_DIR / name).read_bytes().decode("ascii", errors="ignore")
        assert text.count("--check-unlock-only") >= 2, (
            f"{name} must check BOTH data-gated modules (H-11 + H-13)"
        )
        for script in ("c09_bunch.py", "c10_pointer.py", "c12_frag.py",
                       "c11_anen.py", "c13_tailshape.py",
                       "aggregate_wave4_fdr.py"):
            assert script in text, f"{name} missing invocation of {script}"
        for wrapper in ("run_h09.", "run_h10.", "run_h11.", "run_h12.",
                        "run_h13."):
            assert wrapper not in text, (
                f"{name} must not re-invoke the individual wrapper {wrapper}*"
            )
        assert "WAVE4_SUMMARY.md" in text, f"{name} missing WAVE4_SUMMARY.md"
