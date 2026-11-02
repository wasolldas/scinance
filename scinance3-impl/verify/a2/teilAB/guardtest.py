"""Probe the derivation's key guards with location-type key names (no data involved)."""
import sys
sys.path.insert(0, "/tmp/claude-0/-home-user-scinance/632fbebe-92f6-553b-ba2e-14f1a2521e17/scratchpad/a2_vorarbeit")
import a2v_common as c
for k in ("median", "r_pre_median", "q50", "loc", "center", "mu", "mean", "avg_bp", "signed_q50",
          "r_post_level", "diff", "contrast_bp", "event_minus_placebo", "Mean", "means_by_class"):
    try:
        c.check_out({k: 1.0})
        print(f"{k!r:24s} PASSES guard")
    except RuntimeError as e:
        print(f"{k!r:24s} refused")
