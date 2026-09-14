"""WP-12 -- survivorship fixture: momentum weekly-IC bias from omitting
delisted symbols (PRD 4.1 B3, DEC-67 Entscheidung 5), KAPITALFREI, PURE
(no network anywhere in this module).

Measures ``bias = IC_with - IC_without`` -- the pooled momentum-IC
(``wp7_universe.pit_universe.momentum_ic_series``/``pooled_momentum_ic``,
read-only import) computed WITH the delisted symbols' return paths added
as extra panel columns, minus the SAME statistic computed WITHOUT them --
together with a week-cluster bootstrap CI (weeks resampled with
replacement, the paired "with" and "without" pooled correlations recomputed
on the SAME resampled week list each draw so the CI is over the BIAS
itself, not over each side independently).

**The registered threshold is not yet set.** PRD 4.1 B3, verbatim:
"Klasse W laeuft nur, wenn das Survivorship-Fixture eine Verzerrung
kleiner als die halbe registrierte Schwelle zeigt; sonst nicht
registrierbar." A3 (the only candidate this fixture gates) has not been
registered (DEC-67 Entscheidung 1: "der Lauf ist bis zum
Survivorship-Fixture ... gesperrt") -- there is therefore NO threshold
number to compare the measured bias against yet. This module NEVER prints
PASS/FAIL; it prints the measured bias, its CI, and
``THRESHOLD_NOT_REGISTERED_NOTE`` verbatim.

Two delisted-symbol data sources, selected by the caller (task brief item
3, ``--mode fixture``):

  * REAL, from whatever ``kline_probe.probe_register`` retrieved
    (``delisted_klines_to_weekly`` aligns those real daily closes onto the
    SAME week axis the surviving-symbol panel uses).
  * SYNTHETIC, if zero real delisted histories were available
    (``make_synthetic_delisted_panel``) -- symbols with a forced -30%
    cumulative (log-return-exact) drawdown over their LAST 8 weeks before
    a randomised delisting week, clearly labelled ``SYNTHETIC*USDT`` in
    every symbol name this module manufactures, so the pipeline is
    exercised end-to-end even with no real delisted history. A NEUTRAL
    (signal-free, ``terminal_drawdown=0.0``) variant of the same generator
    is the adversarial-test's null comparison (DEC-39 trio, task brief
    item 5): its bias CI must cover 0, while the drawdown-biased set's
    bias must be negative (a vanished, badly-performing symbol dragging
    the naive "IC_with" cross-section's momentum signal down when it is
    included and its bad recent momentum/bad next return pair is counted).
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from ..wp7_universe import pit_universe

__all__ = [
    "THRESHOLD_NOT_REGISTERED_NOTE", "SYNTHETIC_SYMBOL_PREFIX",
    "weekly_signal_outcome_pairs", "pooled_rho", "per_week_rho_series",
    "cluster_bootstrap_bias", "make_synthetic_delisted_panel",
    "delisted_klines_to_weekly", "run_fixture_measurement",
    "artifact_fingerprint", "write_artifacts", "write_ic_series_csv",
]

_EPOCH = date(1970, 1, 1)

#: PRD 4.1 B3 + DEC-67 Entscheidung 1, said in the report every time this
#: module measures a bias -- never a threshold comparison, never PASS/FAIL.
THRESHOLD_NOT_REGISTERED_NOTE = (
    "Die registrierte Schwelle (PRD 4.1 B3: 'kleiner als die halbe "
    "registrierte Schwelle') ist noch NICHT gesetzt -- A3 ist nicht "
    "registriert (DEC-67 Entscheidung 1: der A3-Lauf ist bis zum "
    "Survivorship-Fixture gesperrt). Diese Messung berichtet ausschliesslich "
    "die gemessene Verzerrung (IC_with - IC_without) und ihr Cluster-"
    "Bootstrap-CI -- KEIN PASS/FAIL, KEIN VERDIKT.")

SYNTHETIC_SYMBOL_PREFIX = "SYNTHETIC"


# ----------------------------------------------------------------------------
# pooled/per-week momentum-IC pairs (mirrors pit_universe.momentum_ic_series'
# trailing-signal construction exactly, so pooled_rho() on the FULL,
# unresampled pair list reproduces pit_universe.momentum_ic_series()["rho"]
# bit-for-bit -- see the determinism test)
# ----------------------------------------------------------------------------

def weekly_signal_outcome_pairs(
    returns: np.ndarray, alive: np.ndarray, *, trail_win: int = 4,
    min_start: int | None = None, min_universe: int = 10,
) -> list[dict[str, Any]]:
    """Per-week ``{week, k, sig, out}`` -- trailing ``trail_win``-week
    signal and next-week outcome, restricted to ``alive[t] & alive[t+1]``,
    for every week with at least ``min_universe`` such symbols. Exposed
    per-week (rather than pre-pooled, unlike
    ``pit_universe.momentum_ic_series``) so ``cluster_bootstrap_bias`` can
    resample WEEKS."""
    n_weeks, n_symbols = returns.shape
    if min_start is None:
        min_start = trail_win
    trail = np.full((n_weeks, n_symbols), np.nan)
    for t in range(n_weeks):
        lo = max(0, t - trail_win + 1)
        trail[t] = returns[lo:t + 1].sum(axis=0)
    pairs: list[dict[str, Any]] = []
    for t in range(min_start, n_weeks - 1):
        mask = alive[t] & alive[t + 1]
        k = int(mask.sum())
        if k < min_universe:
            continue
        pairs.append({"week": t, "k": k, "sig": trail[t, mask], "out": returns[t + 1, mask]})
    return pairs


def pooled_rho(pairs: list[dict[str, Any]]) -> float:
    """Spearman IC pooled across every ``(sig, out)`` pair in ``pairs`` --
    0.0 for an empty list (no usable weeks), same convention as
    ``pit_universe.spearman_rank_ic``'s degenerate-input handling."""
    if not pairs:
        return 0.0
    sig = np.concatenate([p["sig"] for p in pairs])
    out = np.concatenate([p["out"] for p in pairs])
    return pit_universe.spearman_rank_ic(sig, out)


def per_week_rho_series(pairs: list[dict[str, Any]], week_labels: list[str] | None = None
                         ) -> list[dict[str, Any]]:
    """One row per week: its OWN (unpooled) Spearman IC -- the DEC-53
    "per-week IC series" artifact (descriptive; the pooled statistic, not
    this per-week average, is what the bias/CI is computed on, same
    discipline as ``pit_universe.momentum_ic_series``'s docstring notes
    for the WP-7 headline number)."""
    out = []
    for p in pairs:
        label = week_labels[p["week"]] if week_labels is not None else str(p["week"])
        out.append({"week": label, "k": p["k"], "rho": pit_universe.spearman_rank_ic(p["sig"], p["out"])})
    return out


# ----------------------------------------------------------------------------
# week-cluster bootstrap of the BIAS (paired resample of "with"/"without")
# ----------------------------------------------------------------------------

def cluster_bootstrap_bias(
    pairs_with: list[dict[str, Any]], pairs_without: list[dict[str, Any]], *,
    seed: int, n_boot: int = 1000, ci: float = 0.95,
) -> dict[str, Any]:
    """Cluster (week) bootstrap CI of ``bias = rho_with - rho_without``.

    Clusters are WEEKS common to both pair lists (a week must qualify --
    ``min_universe`` alive pairs -- under BOTH the with- and without-panel
    to be resampled; since "without" is always a column-subset of "with",
    every week qualifying for "without" also qualifies for "with", so this
    is simply the "without" week set in practice). Each of ``n_boot``
    draws resamples that week list WITH REPLACEMENT (a real cluster
    bootstrap, not an i.i.d. resample of individual symbol-weeks) and
    recomputes BOTH pooled correlations on the SAME resampled week list --
    a paired draw, so the resulting distribution is directly over the bias,
    not the difference of two independently-resampled quantities.
    Deterministic given ``seed`` (DEC-53 mandatory artifact).
    """
    by_week_with = {p["week"]: p for p in pairs_with}
    by_week_without = {p["week"]: p for p in pairs_without}
    common = sorted(set(by_week_with) & set(by_week_without))
    point = pooled_rho([by_week_with[w] for w in common]) - pooled_rho([by_week_without[w] for w in common])
    if not common:
        return {"seed": int(seed), "n_boot": 0, "n_weeks": 0, "ci": ci,
                "point": point, "ci_lo": point, "ci_hi": point,
                "note": "no common qualifying weeks between with/without panels -- CI degenerates to the point"}

    rng = np.random.default_rng(seed)
    n = len(common)
    common_arr = np.array(common)
    draws = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        chosen = common_arr[idx].tolist()
        rho_w = pooled_rho([by_week_with[w] for w in chosen])
        rho_wo = pooled_rho([by_week_without[w] for w in chosen])
        draws[i] = rho_w - rho_wo
    alpha = 1.0 - ci
    lo = float(np.quantile(draws, alpha / 2))
    hi = float(np.quantile(draws, 1.0 - alpha / 2))
    return {"seed": int(seed), "n_boot": n_boot, "n_weeks": n, "ci": ci,
            "point": point, "ci_lo": lo, "ci_hi": hi,
            "bootstrap_mean": float(draws.mean()), "bootstrap_sd": float(draws.std(ddof=1))}


# ----------------------------------------------------------------------------
# delisted-symbol return paths: REAL (from kline_probe) or SYNTHETIC
# ----------------------------------------------------------------------------

def delisted_klines_to_weekly(probe_results: list[dict[str, Any]], week_labels: list[str]
                               ) -> dict[str, Any]:
    """Real probed delisted daily klines (``kline_probe.probe_register()
    ["results"]``, entries carrying ``rows``) -> ``[n_weeks, n_symbols]``
    ``returns``/``alive`` aligned onto ``week_labels`` -- the SAME week
    axis the surviving-symbol base panel uses. Only entries with
    ``available=True`` contribute a column. A delisted symbol's calendar
    week that falls OUTSIDE ``week_labels`` (base panel's span) is dropped,
    never extrapolated -- same "a gap never manufactures a return"
    discipline as ``panel_read.weekly_returns_and_alive``.
    """
    week_pos = {w: i for i, w in enumerate(week_labels)}
    n_weeks = len(week_labels)
    available = [r for r in probe_results if r.get("available") and r.get("rows")]
    n_symbols = len(available)
    returns = np.zeros((n_weeks, n_symbols), dtype=np.float64)
    alive = np.zeros((n_weeks, n_symbols), dtype=bool)
    symbols: list[str] = []
    for j, r in enumerate(available):
        symbols.append(r["symbol"])
        dates = [(_EPOCH + timedelta(days=row["start_ms"] // 86_400_000)).isoformat()
                 for row in r["rows"]]
        closes = [float(row["close"]) for row in r["rows"]]
        wc = pit_universe.weekly_close_from_daily(dates, closes)
        idx_present = sorted(week_pos[w] for w in wc if w in week_pos)
        for i in idx_present:
            alive[i, j] = True
        for k in range(1, len(idx_present)):
            t0, t1 = idx_present[k - 1], idx_present[k]
            if t1 - t0 != 1:
                continue
            c0, c1 = wc[week_labels[t0]], wc[week_labels[t1]]
            if c0 > 0 and c1 > 0:
                returns[t1, j] = math.log(c1 / c0)
    return {"returns": returns, "alive": alive, "symbols": symbols}


def make_synthetic_delisted_panel(
    n_weeks: int, *, n_symbols: int = 30, seed: int, base_vol: float = 0.08,
    terminal_drawdown: float = -0.30, drawdown_weeks: int = 8,
    min_life_weeks: int = 12, up_len: int = 3, down_len: int = 1, up_mult: float = 1.0,
    dd_noise_mult: float = 0.02,
) -> dict[str, Any]:
    """``[n_weeks, n_symbols]`` SYNTHETIC delisted-symbol ``returns``/
    ``alive`` on the caller's week axis (task brief item 3).

    Every symbol is alive from week 0 up to a randomised delisting week
    (``>= min_life_weeks``, ``< n_weeks``, so it always vanishes strictly
    before the panel's last week -- the point of the fixture). Its weekly
    returns are Gaussian noise (``base_vol``) EXCEPT for its final
    ``drawdown_weeks`` weeks, whose log-returns are forced to sum EXACTLY
    to ``log(1 + terminal_drawdown)`` (an exact, deterministic -30%
    cumulative terminal drawdown at the default) regardless of the noise
    draw.

    **Shape of the drawdown window (why it is adversarial, not just a
    decline).** The forced total is NOT spread evenly or laid out as a
    single monotonic slide -- both of those turn out to leave the
    momentum estimator's trailing-signal/next-return PAIRS mostly
    CONCORDANT (empirically verified: a smooth decline pairs "recent
    losses" with "more losses", which is exactly the true-momentum
    pattern the estimator is built to detect, so it does not stress
    anything). Instead the window tiles an ``up_len``-up /
    ``down_len``-down cycle (default 3-up-1-down, twice over an 8-week
    window): a symbol looks like it has POSITIVE recent momentum for
    ``up_len`` weeks (a real, currently-observed "reason to go long" by
    the estimator's own signal), immediately followed by a sharp
    single-week reversal. Because the reversal week's magnitude carries
    the periods's ENTIRE forced net decline, its down-leg return is much
    larger in magnitude than the up-leg -- exactly the recurring
    high-trailing-signal / catastrophic-next-return mismatch a
    survivorship-omitted "death spiral" name actually produces, and the
    one shape that reliably drags the pooled momentum IC DOWN when these
    symbols are added (see the adversarial unit test: the required
    negative bias is a property of THIS shape, not of "a -30% drawdown"
    in general).

    ``terminal_drawdown=0.0`` (no forcing, pure noise throughout) is the
    NEUTRAL/signal-free comparison set the adversarial test needs -- its
    bias must have a bootstrap CI covering 0.
    """
    rng = np.random.default_rng(seed)
    returns = np.zeros((n_weeks, n_symbols), dtype=np.float64)
    alive = np.zeros((n_weeks, n_symbols), dtype=bool)
    symbols = [f"{SYNTHETIC_SYMBOL_PREFIX}{i:03d}USDT" for i in range(n_symbols)]
    delist_weeks: list[int] = []
    lo_life = min(min_life_weeks, max(1, n_weeks - 1))
    hi_life = max(lo_life + 1, n_weeks - 1)
    cycle_len = up_len + down_len
    cycle_pattern = np.array(([True] * up_len + [False] * down_len), dtype=bool)
    for j in range(n_symbols):
        delist_week = int(rng.integers(lo_life, hi_life))
        delist_weeks.append(delist_week)
        alive[0:delist_week + 1, j] = True
        noise = rng.normal(0.0, base_vol, size=delist_week + 1)
        returns[0:delist_week + 1, j] = noise
        if terminal_drawdown != 0.0 and delist_week + 1 >= drawdown_weeks:
            dd_lo = delist_week - drawdown_weeks + 1
            target_total = math.log(1.0 + terminal_drawdown)
            n_full_cycles = -(-drawdown_weeks // cycle_len)  # ceil
            is_up = np.tile(cycle_pattern, n_full_cycles)[:drawdown_weeks]
            n_up, n_down = int(is_up.sum()), int((~is_up).sum())
            up_ret = base_vol * up_mult
            down_ret = (target_total - up_ret * n_up) / n_down if n_down > 0 else 0.0
            path = np.where(is_up, up_ret, down_ret)
            dd_noise = rng.normal(0.0, base_vol * dd_noise_mult, size=drawdown_weeks)
            dd_noise -= dd_noise.mean()  # exact zero-sum perturbation
            returns[dd_lo:delist_week + 1, j] = path + dd_noise
    return {"returns": returns, "alive": alive, "symbols": symbols,
            "delist_weeks": delist_weeks, "seed": int(seed),
            "terminal_drawdown": terminal_drawdown, "label": SYNTHETIC_SYMBOL_PREFIX}


# ----------------------------------------------------------------------------
# end-to-end measurement + DEC-53 artifacts
# ----------------------------------------------------------------------------

def run_fixture_measurement(
    base_returns: np.ndarray, base_alive: np.ndarray, delisted_returns: np.ndarray,
    delisted_alive: np.ndarray, *, trail_win: int = 4, min_universe: int = 10,
    seed: int, n_boot: int = 1000, week_labels: list[str] | None = None,
    mode_label: str,
) -> dict[str, Any]:
    """WITH (base + delisted columns) vs. WITHOUT (base only) pooled
    momentum IC, their difference, and its week-cluster bootstrap CI.
    ``mode_label`` is stored verbatim in the result (e.g. ``"REAL"`` or
    ``"SYNTHETIC"``) so the report never lets a synthetic run look real.
    """
    if base_returns.shape[0] != delisted_returns.shape[0]:
        raise ValueError(
            f"base panel has {base_returns.shape[0]} weeks but the delisted panel has "
            f"{delisted_returns.shape[0]} -- both must share the SAME week axis")
    returns_with = np.hstack([base_returns, delisted_returns])
    alive_with = np.hstack([base_alive, delisted_alive])

    pairs_with = weekly_signal_outcome_pairs(
        returns_with, alive_with, trail_win=trail_win, min_universe=min_universe)
    pairs_without = weekly_signal_outcome_pairs(
        base_returns, base_alive, trail_win=trail_win, min_universe=min_universe)

    rho_with = pooled_rho(pairs_with)
    rho_without = pooled_rho(pairs_without)
    boot = cluster_bootstrap_bias(pairs_with, pairs_without, seed=seed, n_boot=n_boot)

    return {
        "mode_label": mode_label, "trail_win": trail_win, "min_universe": min_universe,
        "n_symbols_without": int(base_returns.shape[1]),
        "n_symbols_delisted_added": int(delisted_returns.shape[1]),
        "n_symbols_with": int(returns_with.shape[1]),
        "n_weeks_used_with": len(pairs_with), "n_weeks_used_without": len(pairs_without),
        "rho_with": rho_with, "rho_without": rho_without, "bias_point": rho_with - rho_without,
        "bootstrap": boot,
        "per_week_rho_with": per_week_rho_series(pairs_with, week_labels),
        "per_week_rho_without": per_week_rho_series(pairs_without, week_labels),
        "threshold_note": THRESHOLD_NOT_REGISTERED_NOTE,
    }


def artifact_fingerprint(result: dict[str, Any]) -> str:
    """SHA-256 over the seed + rounded point/CI values -- same discipline
    as ``wp7_universe.pair_corr._fingerprint`` (citable without storing
    every bootstrap draw)."""
    h = hashlib.sha256()
    h.update(str(result["bootstrap"]["seed"]).encode("ascii"))
    h.update(str(result["bootstrap"]["n_boot"]).encode("ascii"))
    h.update(repr(round(result["rho_with"], 12)).encode("ascii"))
    h.update(repr(round(result["rho_without"], 12)).encode("ascii"))
    h.update(repr(round(result["bias_point"], 12)).encode("ascii"))
    h.update(repr(round(result["bootstrap"]["ci_lo"], 12)).encode("ascii"))
    h.update(repr(round(result["bootstrap"]["ci_hi"], 12)).encode("ascii"))
    h.update(result["mode_label"].encode("utf-8"))
    return h.hexdigest()


def write_artifacts(out_dir: Path | str, result: dict[str, Any]) -> dict[str, Any]:
    """Write the DEC-53 mandatory artifact (seed + bias point/CI + mode
    label) to ``<out_dir>/survivorship_bias_<mode_label>.json``. Never
    under ``data/harvest``."""
    out_dir = Path(out_dir)
    if "data/harvest" in out_dir.as_posix():
        raise ValueError(f"refusing to write survivorship-fixture artifacts under data/harvest: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    lean = {k: v for k, v in result.items()
            if k not in ("per_week_rho_with", "per_week_rho_without")}
    fp = artifact_fingerprint(result)
    payload = {**lean, "sha256": fp}
    path = out_dir / f"survivorship_bias_{result['mode_label']}.json"
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return {"path": str(path), "sha256": fp}


def write_ic_series_csv(out_dir: Path | str, result: dict[str, Any]) -> dict[str, dict[str, str]]:
    """Write the per-week IC series WITH and WITHOUT (task brief item 4:
    "per-week IC series with/without CSV") as two CSVs. Never under
    ``data/harvest``."""
    import csv

    out_dir = Path(out_dir)
    if "data/harvest" in out_dir.as_posix():
        raise ValueError(f"refusing to write IC-series CSVs under data/harvest: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, dict[str, str]] = {}
    for side, key in (("with", "per_week_rho_with"), ("without", "per_week_rho_without")):
        path = out_dir / f"ic_series_{side}_{result['mode_label']}.csv"
        with path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["week", "k", "rho"])
            for row in result[key]:
                w.writerow([row["week"], row["k"], repr(row["rho"])])
        written[side] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return written
