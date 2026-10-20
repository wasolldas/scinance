"""Positive control in production configuration (``--positive-control``, B-4, ERSTFASSUNG 4, Review B-4/B-9, PRD 3.3.8,
DEC-94 (5)).  Runs only if at least one variant was handed over, ALONE and BEFORE the test, with the registered YAML and
the pilot result (both sha256-locked by the CLI), on the real week shape of W1 and W2 (weeks, PIT masks, K_t,
``returns_valid``; panel cut <= 2026-06-28) and SYNTHETIC returns only -- :func:`run_positive_control` has no ``returns``
parameter.

**World per window** (:func:`synthesize_world`): the stress calibration of the window from the YAML (``rho_f``,
``beta_sd``, ``null_scales``), market column = factor, drift 0, plus 8 sector blocks with the shock ``sigma_g``.
``sigma_g`` is found by bisection (seeds 2000..2049) so that the weekly SD of the fm8 IC of the variant in the negative
control hits ``sqrt(v_fm8_W + max(F2_null_W,v, F2_real,v))`` within +-5 % (``F2_null = sd_week^2 - v_fm8`` from v6,
``F2_real`` from the pilot); if ``F2_real <= F2_null``, ``sigma_g = 0`` (Review B-9: the realism check is done by
``F2_real``, not by the power SD itself; the world calibration is a fork towards testability against the literal PRD
sector world, labelled so).

**Injection** (Review B-4): the PRD positive fixture generalised to the variant -- the next-week return carries
``s * c * z(characteristic_t)`` (z-score over the members of the week) -- with ``c`` scaled so that the REALISED effect
(mean of positive minus negative control of the fm8 statistic, common random numbers, seeds 1000..1049) in the binding
window equals ``z_krit * SE_T,W + 0.8416 * SD_T,W`` within +-5 % (MDE80 without credit; the credit is carried by the null).

**Judgement** seeds 53..252, positive and negative, gate chain = conditions (1a)-(1c) and (4b) of the test with the frozen
constants.  BESTANDEN iff for every handed variant (a) the weekly SD of the control world <= 1.10 x the weekly SD of the
power line in each window, (b) the PASS share in the binding window >= 0.734, (c) the false PASS rate of the negative
control <= 0.086 in each window, (d) the realised injection effect on the judgement seeds within +-10 % of the target.
Report-only: the same control in the literal PRD sector world (shock 0.375 sigma_e) and the joint C10 share.
"""
from __future__ import annotations

import math
from typing import Any, Callable

import numpy as np

from ..wp13_xsec import characteristics, ic, nulls, prelaunch
from ..wp13_xsec import run as wp13_run
from . import artifacts, checks, gate, handover, schema
from . import constants as C
from . import estimators as est
from .errors import PositiveControlAbort

__all__ = ["synthesize_world", "eval_world", "run_positive_control", "render_pc_markdown", "write_pc_artifacts",
           "build_shape", "PASS_LINE", "FAIL_LINE", "world_params"]

PASS_LINE = "Positivkontrolle BESTANDEN"
FAIL_LINE = "Positivkontrolle NICHT BESTANDEN"
MARKET = C.MARKET_SYMBOL
FORK_LABEL = ("Etikett (A-7): die Welt-Kalibrierung an F2_real statt der woertlichen PRD-Sektorwelt ist eine Gabelung "
              "Richtung Testbarkeit; die Realismuspruefung leistet F2_real aus dem Pilot; die PRD-Sektorwelt (0,375 sigma_e) "
              "ist report-only.")


def build_shape(panel: dict[str, Any], cut_date: str) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    """Week grid, PIT alive mask and ``returns_valid`` of the CUT panel (the real weekly returns are computed inside
    ``panel_load`` and dropped here; they never reach the control).  Returns ``(shape, symbols, cut_report)``."""
    from . import panel_cut
    from ..wp7_universe import panel_load
    cut, rep = panel_cut.cut_panel_days(panel, cut_date, limit=C.CUT_TEST)
    panel_cut.assert_panel_max_date(cut, cut_date)
    last_alive = cut.get("last_alive_day") or [None] * len(cut["symbols"])
    weekly = panel_load.weekly_returns_and_mask_union(cut, last_alive)
    panel_cut.assert_weeks_end_by(weekly["weeks"], cut_date)
    shape = {"weeks": list(weekly["weeks"]), "alive": np.asarray(weekly["alive"], dtype=bool),
             "returns_valid": np.asarray(weekly["returns_valid"], dtype=bool)}
    return shape, list(cut["symbols"]), rep


# ----------------------------------------------------------------------------
# the synthetic world
# ----------------------------------------------------------------------------

def world_params(registered: dict[str, Any], wn: str) -> dict[str, float]:
    """Scales of the control world of window ``wn`` from the registered YAML only (stress calibration + null scales)."""
    w = registered["windows"][wn]
    st = w["calibration"]["stress"]
    sc = w["null_scales"]
    sigma_f, sigma_e = float(sc["sigma_f"]), float(sc["sigma_e_used"])
    beta_sd = float(st["beta_sd_calibrated"])
    return {"rho_f": float(st["rho_f"]), "beta_sd": beta_sd, "sigma_f": sigma_f, "sigma_e": sigma_e,
            "target_factor_share": float(st["target_factor_share"]), "drift_f": nulls.DRIFT_F_DRIFTFREE}


def _zscore_members(row: np.ndarray, members: np.ndarray) -> np.ndarray:
    out = np.zeros_like(row)
    if int(members.sum()) >= 2:
        x = row[members]
        sd = float(x.std(ddof=1))
        out[members] = (x - x.mean()) / (sd if sd > 0.0 else 1.0)
    return out


def _char_row(variant: str, r: np.ndarray, t: int) -> np.ndarray | None:
    """Characteristic of week t from the (unmasked) synthetic returns up to week t -- the definitions of
    ``characteristics.momentum_characteristic`` (partial sums at the start) and ``reversal_gap_characteristic``."""
    if variant == "rev_gap":
        return r[t - 1] if t >= 1 else None
    n = int(variant[-1])
    return r[max(0, t - n + 1):t + 1].sum(axis=0)


def synthesize_world(alive_ext: np.ndarray, valid_ext: np.ndarray, symbols: list[str], world: dict[str, float], *, seed: int,
                     window_index: int, variant: str, signal_ic: float, sigma_g: float) -> dict[str, Any]:
    """Synthetic weekly returns over ``8 lead weeks + window`` on the REAL masks.  ``signal_ic = 0`` is the negative
    control and consumes the random stream identically (common random numbers with the positive control).  Returns
    ``returns`` (zero where no return is computable), ``returns_est`` (NaN there), ``coefficient``."""
    n_ext, n_sym = alive_ext.shape
    if MARKET not in symbols:
        raise PositiveControlAbort(f"{MARKET} missing from the symbols (the market column is the factor)")
    m_idx = symbols.index(MARKET)
    rng = np.random.default_rng([int(seed), int(window_index)])
    sim = nulls.simulate_factor_panel(n_ext, n_sym, sigma_f=world["sigma_f"], sigma_e=world["sigma_e"], rho_f=world["rho_f"],
                                      drift_f=world["drift_f"], rng=rng, beta_sd=world["beta_sd"], market_index=m_idx)
    base, f = sim["returns"].copy(), sim["f"]
    non_market = np.array([j for j in range(n_sym) if j != m_idx])
    sector = np.full(n_sym, -1, dtype=np.int64)
    sector[non_market] = np.arange(non_market.size) % C.PC_N_SECTORS
    g = float(sigma_g) * rng.standard_normal((n_ext, C.PC_N_SECTORS))
    base += np.where(sector[None, :] >= 0, g[:, np.maximum(sector, 0)], 0.0)
    base[:, m_idx] = f
    members = np.asarray(alive_ext, dtype=bool) & np.asarray(valid_ext, dtype=bool)
    members[:, m_idx] = False
    sigma_tot = math.sqrt(world["sigma_e"] ** 2 + float(sigma_g) ** 2 + (world["beta_sd"] * world["sigma_f"]) ** 2)
    sgn = float(C.SIGN[C.DIRECTION[variant]])
    coefficient = (signal_ic / math.sqrt(1.0 - signal_ic ** 2)) * sigma_tot if signal_ic else 0.0
    r = np.empty_like(base)
    z_prev: np.ndarray | None = None
    for t in range(n_ext):
        row = base[t].copy()
        if coefficient and z_prev is not None:
            row += sgn * coefficient * z_prev
        row[m_idx] = f[t]
        r[t] = row
        ch = _char_row(variant, r, t)
        z_prev = _zscore_members(ch, members[t]) if ch is not None else None
    valid_b = np.asarray(valid_ext, dtype=bool)
    return {"returns": np.where(valid_b, r, 0.0), "returns_est": np.where(valid_b, r, np.nan), "coefficient": float(coefficient)}


def eval_world(world_returns: dict[str, Any], alive_ext: np.ndarray, symbols: list[str], variant: str, lead: int = C.LEAD_WEEKS) -> list[float]:
    """Weekly fm8 IC of ``variant`` on a synthetic world (judged weeks), through the same functions as the test
    (``beta_characteristic`` on the estimation array, ``fm_neutralize_outcome``, ``weekly_ic_series``)."""
    r, est_r = world_returns["returns"], world_returns["returns_est"]
    beta = characteristics.beta_characteristic(est_r, symbols, market_symbol=MARKET, trail_win=C.BETA_WINDOW_WEEKS,
                                               min_weeks=C.BETA_WINDOW_WEEKS)
    alive_w = alive_ext[lead:]
    resid = ic.fm_neutralize_outcome(r[lead:], beta[lead:], alive_w)
    if variant == "rev_gap":
        char = characteristics.reversal_gap_characteristic(r)[lead:]
    else:
        char = characteristics.momentum_characteristic(r, trail_win=int(variant[-1]))[lead:]
    res = ic.weekly_ic_series(char, resid, alive_w, convention=C.CONVENTION)
    return [float(w["ic"]) for w in res["weekly"]]


def _pooled_sd(series: list[list[float]]) -> float:
    pool = np.concatenate([np.asarray(s, dtype=np.float64)[np.isfinite(s)] for s in series])
    return float(pool.std(ddof=1)) if pool.size > 1 else float("nan")


def _mean_y(ics: list[float], sign: int) -> float:
    a = np.asarray(ics, dtype=np.float64)
    a = a[np.isfinite(a)]
    return float(sign * a.mean()) if a.size else float("nan")


# ----------------------------------------------------------------------------
# calibrations
# ----------------------------------------------------------------------------

def _calibrate_sigma_g(geom: dict[str, Any], symbols: list[str], world: dict[str, float], variant: str, widx: int, target_sd: float,
                       *, f2_real: float, f2_null: float, seeds: tuple[int, ...]) -> dict[str, Any]:
    """sigma_g so that the weekly SD of the fm8 IC of the negative control hits ``target_sd`` within +-5 %.  0 if
    ``F2_real <= F2_null``."""
    if f2_real <= f2_null:
        return {"sigma_g": 0.0, "reason": "F2_real <= F2_null: sigma_g = 0", "target_sd": target_sd, "achieved_sd": None,
                "n_iter": 0, "rel_error": None}

    def sd_at(g: float) -> float:
        runs = []
        for s in seeds:
            w = synthesize_world(geom["alive_ext"], geom["valid_ext"], symbols, world, seed=s, window_index=widx, variant=variant,
                                 signal_ic=0.0, sigma_g=g)
            runs.append(eval_world(w, geom["alive_ext"], symbols, variant))
        return _pooled_sd(runs)

    lo, hi = 0.0, world["sigma_e"]
    sd_hi = sd_at(hi)
    grow = 0
    while sd_hi < target_sd and grow < 6:
        lo, hi = hi, hi * 2.0
        sd_hi = sd_at(hi)
        grow += 1
    if sd_hi < target_sd:
        raise PositiveControlAbort(f"window {geom['name']} {variant}: the sector shock cannot lift the weekly SD to {target_sd:.5f}")
    mid, sd_mid, it = hi, sd_hi, 0
    for it in range(1, 41):
        mid = 0.5 * (lo + hi)
        sd_mid = sd_at(mid)
        if abs(sd_mid / target_sd - 1.0) <= 0.01:
            break
        if sd_mid < target_sd:
            lo = mid
        else:
            hi = mid
    rel = sd_mid / target_sd - 1.0
    if abs(rel) > C.PC_WORLD_SD_TOL:
        raise PositiveControlAbort(f"window {geom['name']} {variant}: sigma_g bisection ended at relative SD error {rel:+.3f}")
    return {"sigma_g": float(mid), "reason": "bisection on the weekly SD (seeds " + f"{seeds[0]}..{seeds[-1]})", "target_sd": target_sd,
            "achieved_sd": sd_mid, "n_iter": it, "rel_error": rel}


def _effect_at(signal_ic: float, geom: dict[str, Any], symbols: list[str], world: dict[str, float], variant: str, widx: int,
               sigma_g: float, seeds: tuple[int, ...], sign: int) -> float:
    eff = []
    for s in seeds:
        pos = synthesize_world(geom["alive_ext"], geom["valid_ext"], symbols, world, seed=s, window_index=widx, variant=variant,
                               signal_ic=signal_ic, sigma_g=sigma_g)
        neg = synthesize_world(geom["alive_ext"], geom["valid_ext"], symbols, world, seed=s, window_index=widx, variant=variant,
                               signal_ic=0.0, sigma_g=sigma_g)
        eff.append(_mean_y(eval_world(pos, geom["alive_ext"], symbols, variant), sign)
                   - _mean_y(eval_world(neg, geom["alive_ext"], symbols, variant), sign))
    return float(np.mean(eff))


def _calibrate_injection(geom: dict[str, Any], symbols: list[str], world: dict[str, float], variant: str, widx: int, sigma_g: float,
                         target_effect: float, sign: int, seeds: tuple[int, ...]) -> dict[str, Any]:
    """Amplitude (injected IC) so that the REALISED effect equals ``target_effect`` within +-5 % (proportional update;
    the effect is ~linear through the origin, fm8 damping ~0.75)."""
    s = min(0.5, target_effect / 0.75)
    trace = []
    eff = float("nan")
    for it in range(1, 16):
        eff = _effect_at(s, geom, symbols, world, variant, widx, sigma_g, seeds, sign)
        trace.append({"signal_ic": s, "effect": eff})
        if math.isfinite(eff) and eff > 0.0 and abs(eff / target_effect - 1.0) <= 0.02:
            break
        if not (math.isfinite(eff) and eff > 0.0):
            s = min(0.9, s * 2.0)
            continue
        s = min(0.9, s * target_effect / eff)
    rel = eff / target_effect - 1.0 if math.isfinite(eff) else float("nan")
    if not (math.isfinite(rel) and abs(rel) <= C.PC_INJECT_TOL):
        raise PositiveControlAbort(f"window {geom['name']} {variant}: injection calibration ended at relative error {rel!r}")
    return {"signal_ic": float(s), "realized_effect": eff, "target_effect": target_effect, "rel_error": rel, "n_iter": len(trace),
            "trace": trace}


# ----------------------------------------------------------------------------
# the judgement
# ----------------------------------------------------------------------------

def _window_pass(ics: list[float], wn: str, variant: str, sign: int, consts: dict[str, Any], bounce: float | None) -> dict[str, Any]:
    fz = consts["frozen"][wn]
    se = est.se_rule(ics, fz["floor_fm8"], consts["w_judged"][wn], mean_block=consts["mean_block"], n_boot=consts["n_boot"],
                     seed=consts["seed"])
    a = np.asarray(ics, dtype=np.float64)
    a = a[np.isfinite(a)]
    mean_ic = float(a.mean()) if a.size else float("nan")
    y = sign * mean_ic if math.isfinite(mean_ic) else float("nan")
    cond = gate.window_conditions({"y": y, "se_w": se["se"], "q95": fz["q95"][variant]}, float(C.Z_KRIT))
    bounce_kill = bool(bounce is not None and math.isfinite(mean_ic) and abs(bounce) >= abs(mean_ic))
    return {"y": y, "mean_ic": mean_ic, "se_w": se["se"], "window_pass": bool(cond["window_pass"] and not bounce_kill),
            "conditions_pass": bool(cond["window_pass"]), "bounce_kill": bounce_kill}


def _judge_world(geoms: dict[str, dict[str, Any]], symbols: list[str], worlds: dict[str, dict[str, float]], variant: str,
                 sigma_g: dict[str, float], signal_ic: float, seeds: tuple[int, ...], consts: dict[str, Any], bounce: dict[str, float | None],
                 sign: int) -> dict[str, Any]:
    out: dict[str, Any] = {"pos": {wn: [] for wn in geoms}, "neg": {wn: [] for wn in geoms}, "neg_ics": {wn: [] for wn in geoms}}
    for s in seeds:
        for widx, wn in enumerate(geoms):
            for cond, sic in (("pos", signal_ic), ("neg", 0.0)):
                w = synthesize_world(geoms[wn]["alive_ext"], geoms[wn]["valid_ext"], symbols, worlds[wn], seed=s, window_index=widx,
                                     variant=variant, signal_ic=sic, sigma_g=sigma_g[wn])
                ics = eval_world(w, geoms[wn]["alive_ext"], symbols, variant)
                out[cond][wn].append(_window_pass(ics, wn, variant, sign, consts, bounce.get(wn)))
                if cond == "neg":
                    out["neg_ics"][wn].append(ics)
    return out


def _summarize_world(judged: dict[str, Any], binding: str, target: float, sd_power_line: dict[str, float]) -> dict[str, Any]:
    wns = list(judged["pos"])
    n = len(judged["pos"][wns[0]])
    pass_share = {wn: sum(r["window_pass"] for r in judged["pos"][wn]) / n for wn in wns}
    neg_rate = {wn: sum(r["window_pass"] for r in judged["neg"][wn]) / n for wn in wns}
    joint_pos = sum(all(judged["pos"][wn][i]["window_pass"] for wn in wns) for i in range(n)) / n
    joint_neg = sum(all(judged["neg"][wn][i]["window_pass"] for wn in wns) for i in range(n)) / n
    sd_world = {wn: _pooled_sd(judged["neg_ics"][wn]) for wn in wns}
    effect = float(np.mean([judged["pos"][binding][i]["y"] - judged["neg"][binding][i]["y"] for i in range(n)]))
    return {"n_seeds": n, "pass_share_by_window": pass_share, "pass_share_binding": pass_share[binding],
            "false_pass_rate_by_window": neg_rate, "joint_c10_share_positive": joint_pos, "joint_c10_false_pass_rate": joint_neg,
            "weekly_sd_world": sd_world, "weekly_sd_power_line": dict(sd_power_line),
            "sd_ratio": {wn: sd_world[wn] / sd_power_line[wn] for wn in wns},
            "realized_effect_binding": effect, "target_effect": target, "effect_rel_error": effect / target - 1.0}


def _criteria(summary: dict[str, Any]) -> dict[str, Any]:
    wns = list(summary["pass_share_by_window"])
    a = {wn: bool(summary["sd_ratio"][wn] <= C.PC_SD_RATIO_MAX) for wn in wns}
    b = bool(summary["pass_share_binding"] >= C.PC_PASS_SHARE_MIN)
    c = {wn: bool(summary["false_pass_rate_by_window"][wn] <= C.PC_NEG_PASS_MAX) for wn in wns}
    d = bool(abs(summary["effect_rel_error"]) <= C.PC_INJECT_JUDGE_TOL)
    return {"a_sd_ratio": a, "b_pass_share": b, "c_false_pass": c, "d_injection": d,
            "passed": bool(all(a.values()) and b and all(c.values()) and d)}


def run_positive_control(
    shape: dict[str, Any], symbols: list[str], registered: dict[str, Any], pilot: dict[str, Any], *,
    observed_fingerprints: dict[str, Any] | None = None, registered_sha256: str | None = None, pilot_sha256: str | None = None,
    log: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """The control (see the module docstring).  ``shape`` = ``{"weeks", "alive", "returns_valid"}`` of the CUT panel (no
    returns), ``symbols`` its column order, ``pilot`` the lock-verified pilot result.  Loud fails: schema, data
    fingerprints, pins, no handed-over variant, a world that cannot reach its target."""
    say = log or (lambda _m: None)
    schema.validate_registered(registered)
    if observed_fingerprints is not None or registered.get("data_fingerprints"):
        checks.check_data_fingerprints(registered, observed_fingerprints)
    handed = [v for v in C.VARIANTS if pilot["variants"][v]["handover"]["handed_over"]]
    if not handed:
        raise PositiveControlAbort("no variant was handed over: no positive control, no test (GL-012 (Pilot))")
    weeks = list(shape["weeks"])
    alive_full = np.asarray(shape["alive"], dtype=bool)
    valid_full = np.asarray(shape["returns_valid"], dtype=bool)
    if alive_full.shape != valid_full.shape or alive_full.shape != (len(weeks), len(symbols)):
        raise ValueError(f"shape inconsistent: alive {alive_full.shape}, returns_valid {valid_full.shape}, {len(weeks)} weeks x {len(symbols)} symbols")
    rules = registered["rules"]
    base_consts = {"mean_block": float(rules["mean_block"]), "n_boot": int(rules["n_boot"]), "seed": int(rules["seed"]),
                   "w_judged": {wn: int(registered["windows"][wn]["w_judged"]) for wn in ("W1", "W2")},
                   "frozen": {wn: {"floor_fm8": float(registered["windows"][wn]["frozen_v6"]["floor_fm8"]),
                                   "q95": {v: float(registered["windows"][wn]["frozen_v6"]["q95"][v]) for v in C.VARIANTS}}
                              for wn in ("W1", "W2")}}
    geoms: dict[str, dict[str, Any]] = {}
    worlds: dict[str, dict[str, float]] = {}
    lead = C.LEAD_WEEKS
    for wn in ("W1", "W2"):
        start, end = registered["windows"][wn]["start"], registered["windows"][wn]["end"]
        sl = prelaunch.slice_window(weeks, start, end)
        lo, hi = sl["lo"], sl["hi"]
        if lo < lead:
            raise PositiveControlAbort(f"window {wn}: fewer than {lead} lead weeks in the week grid")
        n_w = hi - lo
        if n_w - 1 != C.W_JUDGED[wn] or n_w - 1 != base_consts["w_judged"][wn]:
            raise PositiveControlAbort(f"window {wn}: w_judged {n_w - 1} differs from the registered {C.W_JUDGED[wn]} (T5)")
        geoms[wn] = {"name": wn, "alive_ext": alive_full[lo - lead:hi], "valid_ext": valid_full[lo - lead:hi], "n_weeks": n_w,
                     "k_median": int(np.median(alive_full[lo:hi].sum(axis=1)))}
        worlds[wn] = world_params(registered, wn)
    bounce_spread = float(rules["bounce_spread"])
    bounce = {wn: float(wp13_run.bounce_fixture_ic(geoms[wn]["n_weeks"], max(geoms[wn]["k_median"], 10), spread=bounce_spread,
                                                    sigma_true=float(registered["windows"][wn]["bounce_sigma_true"]),
                                                    seed=int(rules["seed"]), convention=C.CONVENTION)["ic_bounce"]) for wn in geoms}
    out_variants: dict[str, Any] = {}
    for v in handed:
        sign = C.SIGN[C.DIRECTION[v]]
        ho = pilot["variants"][v]["handover"]
        f2_real = float(ho["f2_real"])
        target_by_w = {wn: C.Z_KRIT * ho["per_window"][wn]["se_t"] + C.Z_POWER * ho["per_window"][wn]["sd_t"] for wn in geoms}
        binding = max(target_by_w, key=lambda w_: target_by_w[w_])
        target = target_by_w[binding]
        sd_line: dict[str, float] = {}
        f2_null: dict[str, float] = {}
        sig_g: dict[str, Any] = {}
        for widx, wn in enumerate(geoms):
            fz = registered["windows"][wn]["frozen_v6"]
            f2_null[wn] = max(0.0, float(fz["sd_week"][v]) ** 2 - float(fz["v_fm8"]))
            sd_line[wn] = math.sqrt(float(fz["v_fm8"]) + max(f2_null[wn], f2_real))
            sig_g[wn] = _calibrate_sigma_g(geoms[wn], symbols, worlds[wn], v, widx, sd_line[wn], f2_real=f2_real, f2_null=f2_null[wn],
                                           seeds=C.PC_SEEDS_SIGMA_G)
            say(f"  {v} {wn}: sigma_g {sig_g[wn]['sigma_g']:.5f} ({sig_g[wn]['reason']})")
        bidx = list(geoms).index(binding)
        inj = _calibrate_injection(geoms[binding], symbols, worlds[binding], v, bidx, sig_g[binding]["sigma_g"], target, sign, C.PC_SEEDS_INJECT)
        say(f"  {v}: injection {inj['signal_ic']:.5f} -> realised effect {inj['realized_effect']:.5f} (target {target:.5f}, binding {binding})")
        consts = dict(base_consts)
        judged = _judge_world(geoms, symbols, worlds, v, {wn: sig_g[wn]["sigma_g"] for wn in geoms}, inj["signal_ic"], C.PC_SEEDS_JUDGE,
                              consts, bounce if v == "rev_gap" else {}, sign)
        summ = _summarize_world(judged, binding, target, sd_line)
        crit = _criteria(summ)
        prd_g = {wn: C.PC_PRD_SECTOR_REL * worlds[wn]["sigma_e"] for wn in geoms}
        judged_prd = _judge_world(geoms, symbols, worlds, v, prd_g, inj["signal_ic"], C.PC_SEEDS_JUDGE, consts,
                                  bounce if v == "rev_gap" else {}, sign)
        summ_prd = _summarize_world(judged_prd, binding, target, sd_line)
        say(f"  {v}: PASS share {summ['pass_share_binding']:.3f}, false PASS {summ['false_pass_rate_by_window']}, criteria passed {crit['passed']}")
        out_variants[v] = {"entry": C.ENTRY[v], "binding_window": binding, "target_effect": target, "target_by_window": target_by_w,
                           "f2_real": f2_real, "f2_null": f2_null, "weekly_sd_power_line": sd_line, "sigma_g": sig_g,
                           "injection": {k: inj[k] for k in ("signal_ic", "realized_effect", "target_effect", "rel_error", "n_iter")},
                           "judgement": summ, "criteria": crit, "prd_sector_world_report_only": {"sigma_g_rel_sigma_e": C.PC_PRD_SECTOR_REL,
                                                                                               "summary": summ_prd},
                           "passed": crit["passed"]}
    passed = all(x["passed"] for x in out_variants.values())
    core: dict[str, Any] = {
        "schema": C.PC_SCHEMA, "mode": "positive_control", "registered_sha256": registered_sha256, "pilot_sha256": pilot_sha256,
        "data_fingerprints": observed_fingerprints, "handed": handed,
        "seeds": {"judgement": [min(C.PC_SEEDS_JUDGE), max(C.PC_SEEDS_JUDGE), len(C.PC_SEEDS_JUDGE)],
                  "injection": [min(C.PC_SEEDS_INJECT), max(C.PC_SEEDS_INJECT)], "world": [min(C.PC_SEEDS_SIGMA_G), max(C.PC_SEEDS_SIGMA_G)]},
        "criteria_constants": {"sd_ratio_max": C.PC_SD_RATIO_MAX, "pass_share_min": C.PC_PASS_SHARE_MIN, "neg_pass_max": C.PC_NEG_PASS_MAX,
                               "injection_tolerance": C.PC_INJECT_JUDGE_TOL},
        "worlds": worlds, "bounce_ic": bounce if "rev_gap" in handed else None, "variants": out_variants,
        "bestanden": bool(passed), "line": PASS_LINE if passed else FAIL_LINE, "label": FORK_LABEL,
        "not_computed": ["real returns (none passed)", "raw_ic", "lag_profile", "beta_calibration_ic"],
    }
    core["result_sha256"] = artifacts.canonical_sha256(core)
    core["code"] = artifacts.code_fingerprint()
    return core


def render_pc_markdown(report: dict[str, Any]) -> str:
    f = lambda x, nd=5: ("-" if x is None else ("nan" if x != x else f"{float(x):.{nd}f}"))   # noqa: E731
    lines = [report["line"], "", "# H-32 Positivkontrolle (PRD 3.3.8, DEC-94 (5))", "", f"- result_sha256: `{report['result_sha256']}`",
             f"- registrierte Datei sha256: `{report.get('registered_sha256')}`; Pilot-Ergebnis sha256: `{report.get('pilot_sha256')}`",
             f"- Seeds: Urteil {report['seeds']['judgement']}, Injektion {report['seeds']['injection']}, Welt {report['seeds']['world']}",
             f"- {report['label']}", "", "## Kriterien je Variante (vorab fixiert)", "",
             "(a) Wochen-SD der Kontrollwelt <= 1,10 x Wochen-SD der Power-Zeile je Fenster; (b) PASS-Anteil im bindenden Fenster >= "
             f"{report['criteria_constants']['pass_share_min']}; (c) falsche PASS-Quote je Fenster <= {report['criteria_constants']['neg_pass_max']}; "
             f"(d) realisierter Injektionseffekt innerhalb +-{report['criteria_constants']['injection_tolerance']:.0%} des Ziels.", "",
             "| Variante | bindend | Ziel | injizierte IC | realisiert (Urteil) | PASS-Anteil | falsche PASS W1/W2 | SD-Verhaeltnis W1/W2 | (a) | (b) | (c) | (d) | bestanden |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for v, x in report["variants"].items():
        j, c = x["judgement"], x["criteria"]
        fp = j["false_pass_rate_by_window"]
        sr = j["sd_ratio"]
        lines.append(f"| {v} | {x['binding_window']} | {f(x['target_effect'])} | {f(x['injection']['signal_ic'])} | {f(j['realized_effect_binding'])} | "
                     f"{f(j['pass_share_binding'], 3)} | {f(fp.get('W1'), 3)} / {f(fp.get('W2'), 3)} | {f(sr.get('W1'), 3)} / {f(sr.get('W2'), 3)} | "
                     f"{all(c['a_sd_ratio'].values())} | {c['b_pass_share']} | {all(c['c_false_pass'].values())} | {c['d_injection']} | {c['passed']} |")
    lines += ["", "## Report-only: woertliche PRD-Sektorwelt (Schock 0,375 sigma_e) und gemeinsame C10-Quote", "",
              "| Variante | PASS-Anteil bindend | falsche PASS W1/W2 | SD-Verhaeltnis W1/W2 | C10-Quote positiv (Welt F2_real / PRD) |", "|---|---|---|---|---|"]
    for v, x in report["variants"].items():
        p = x["prd_sector_world_report_only"]["summary"]
        lines.append(f"| {v} | {f(p['pass_share_binding'], 3)} | {f(p['false_pass_rate_by_window'].get('W1'), 3)} / "
                     f"{f(p['false_pass_rate_by_window'].get('W2'), 3)} | {f(p['sd_ratio'].get('W1'), 3)} / {f(p['sd_ratio'].get('W2'), 3)} | "
                     f"{f(x['judgement']['joint_c10_share_positive'], 3)} / {f(p['joint_c10_share_positive'], 3)} |")
    lines += ["", report["line"], ""]
    return "\n".join(lines)


def write_pc_artifacts(out_dir, report: dict[str, Any]) -> dict[str, Any]:
    from pathlib import Path
    out = Path(out_dir)
    artifacts.refuse_unsafe_path(out / "x", writing=True)
    out.mkdir(parents=True, exist_ok=True)
    j = artifacts.write_json(out / "h32_positive_control.json", report)
    md = out / "h32_positive_control.md"
    md.write_text(render_pc_markdown(report), encoding="utf-8")
    return {"out_dir": str(out), "artifacts": {"json": j, "md": {"file": md.name, "sha256": artifacts.sha256_file(md)}}}
