"""Orchestration + gate-neutral payload for the H-17 venue-fingerprint gate.

Runs the registered measurement (registry H-17, Welle 5):

  * 10 nodes = 5 symbols x {bybit, binance}, publicTrade only, 5-minute
    event windows with 4 per-day-quantile-normalised channels (features.py),
  * Leave-One-Symbol-Out, 5 folds: train on the 8 nodes of the other 4
    symbols, test on the held-out symbol restricted to the LAST 3 WEEKS of
    its available window dates (registry: Test-Zeitraum je Fold = letzte
    3 Wochen des ausgelassenen Symbols),
  * per fold: fresh InfoNCE contrastive training (positives = same node,
    negatives = full batch, batch >= 2048), frozen linear probe for the
    venue label, held-out BALANCED accuracy,
  * NULL (verdict-bearing): within-symbol-within-day permutation of the
    TRAIN venue labels, then FULL RETRAINING of encoder + probe per
    replicate (20 retrainings per fold — registry: KEIN Frozen-Model-
    Shuffling; the permuted venue labels also re-define the node identity
    used for the contrastive positives, so the whole representation is
    retrained under the null). Held-out accuracy is always measured
    against the TRUE test labels; fold p = add-one empirical p of the
    observed accuracy against the 20 null accuracies,
  * ONE F-VENUE BH-FDR family over the 5 fold p-values (alpha = 0.10),
  * secondary (NOT verdict-bearing as a series, but input to a binding
    gate): daily cross-venue embedding-distance series from the held-out
    test embeddings (redundancy.py),
  * PRE-REGISTERED NON-REDUNDANCY GATE against c12_frag/H-12:
    |Spearman rho| < 0.6 vs. the c12 daily lambda2/IPR series on
    overlapping days; |rho| >= 0.6 = REDUNDANT = DROP regardless of
    accuracy (redundancy.redundancy_gate),
  * COMPUTE GATE (binding): a full run WITHOUT a real CUDA device is NEVER
    verdict-bearing — the payload carries ``compute.verdict_bearing`` and
    ``weiter_indication`` is forced False (with reason) when it is not.

GATE-NEUTRAL payload (c12_frag/H-04b convention): every criterion is
reported individually plus a ``weiter_indication`` flag — the driver
renders NO overall verdict; the gate-auditor adjudicates against H-17.

KAPITALFREI: pure structure/existence question, ``capital_free: true``;
no friction, bps, PnL, Sharpe field anywhere. A trading consequence would
be a NEW H-17b, NOT implied.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import numpy as np

from .contrastive import BATCH_SIZE_MIN, probe_predict, train_linear_probe
from .encoder import NumpyFallbackEncoder
from .features import NodeWindows
from .redundancy import (
    REDUNDANCY_RHO_MAX,
    daily_embedding_distance_series,
    redundancy_gate,
)
from .stats import (
    FDR_ALPHA,
    balanced_accuracy,
    benjamini_hochberg,
    empirical_p_ge,
    permute_within_groups,
)

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-17"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"
FDR_FAMILY = "F-VENUE"

#: Registered gate thresholds (registry H-17, verbatim):
BALANCED_ACC_MIN = 0.60        # per-fold held-out balanced accuracy floor
MIN_PASSING_FOLDS = 4          # >= 4 of 5 LOSO folds
N_FOLDS = 5
POOLED_ACC_MIN = 0.55          # hard DROP below (pooled over all test windows)
N_PERMUTATIONS = 20            # retrainings per fold (registered null)
TEST_WEEKS = 3                 # last 3 weeks of the held-out symbol
TEST_DAYS = TEST_WEEKS * 7

COMPUTE_NOTE = (
    "Compute-Gate (verbindlich): Batch >= 2048 ist Teil der registrierten "
    "Methode; ein voller Lauf ohne echtes CUDA-Device ist NIEMALS "
    "verdikt-tragend (Pipeline-Smoke), weiter_indication wird dann "
    "erzwungen False."
)


# ---------------------------------------------------------------------------
# Panel stacking + LOSO folds
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Panel:
    """All node windows stacked: parallel arrays over windows."""

    x: np.ndarray          # (N, 4, L) float32
    mask: np.ndarray       # (N, L) bool
    dates: np.ndarray      # (N,) object 'YYYY-MM-DD'
    symbols: np.ndarray    # (N,) object
    venues: np.ndarray     # (N,) object (exchange)


def stack_nodes(nodes: list[NodeWindows]) -> Panel:
    """Stack per-node window sets into one panel."""
    if not nodes:
        raise ValueError("empty node list")
    x = np.concatenate([n.x for n in nodes], axis=0)
    mask = np.concatenate([n.mask for n in nodes], axis=0)
    dates = np.concatenate([n.dates for n in nodes], axis=0)
    symbols = np.concatenate(
        [np.array([n.symbol] * n.x.shape[0], dtype=object) for n in nodes], axis=0)
    venues = np.concatenate(
        [np.array([n.exchange] * n.x.shape[0], dtype=object) for n in nodes], axis=0)
    return Panel(x=x, mask=mask, dates=dates, symbols=symbols, venues=venues)


@dataclass(slots=True)
class Fold:
    """One Leave-One-Symbol-Out fold."""

    held_out_symbol: str
    train_idx: np.ndarray
    test_idx: np.ndarray
    test_start_date: str
    test_end_date: str


def _iso_to_date(s: str) -> datetime:
    return datetime.strptime(str(s), "%Y-%m-%d").replace(tzinfo=timezone.utc)


def build_loso_folds(panel: Panel, symbols: tuple[str, ...]) -> list[Fold]:
    """Leave-One-Symbol-Out folds (registry H-17, 5 folds).

    Train = ALL windows of the other symbols (both venues). Test = windows
    of the held-out symbol whose date lies in the LAST ``TEST_DAYS`` days of
    that symbol's available dates (both venues). Windows of the held-out
    symbol BEFORE its test period are used NOWHERE (strict symbol
    exclusion — no leak of the held-out symbol into training).
    """
    folds: list[Fold] = []
    for sym in symbols:
        sym_sel = panel.symbols == sym
        if not np.any(sym_sel):
            raise ValueError(f"no windows for symbol {sym!r}")
        sym_dates = panel.dates[sym_sel]
        max_d = max(_iso_to_date(d) for d in np.unique(sym_dates))
        cutoff = max_d - timedelta(days=TEST_DAYS - 1)
        in_test = np.array(
            [_iso_to_date(d) >= cutoff for d in panel.dates], dtype=bool)
        train_idx = np.nonzero(~sym_sel)[0]
        test_idx = np.nonzero(sym_sel & in_test)[0]
        if test_idx.size == 0:
            raise ValueError(f"empty test period for held-out symbol {sym!r}")
        folds.append(Fold(
            held_out_symbol=str(sym),
            train_idx=train_idx,
            test_idx=test_idx,
            test_start_date=cutoff.strftime("%Y-%m-%d"),
            test_end_date=max_d.strftime("%Y-%m-%d"),
        ))
    return folds


# ---------------------------------------------------------------------------
# One fold: real training + registered permutation null (full retraining)
# ---------------------------------------------------------------------------

def _venue_to_int(venues: np.ndarray, venue_order: tuple[str, ...]) -> np.ndarray:
    lut = {v: i for i, v in enumerate(venue_order)}
    return np.array([lut[str(v)] for v in venues], dtype=np.int64)


def _node_ids(venues: np.ndarray, symbols: np.ndarray) -> np.ndarray:
    return np.array([f"{v}:{s}" for v, s in zip(venues, symbols)], dtype=object)


def run_fold(
    panel: Panel,
    fold: Fold,
    *,
    encoder_factory: Callable[[int], Any],
    venue_order: tuple[str, ...],
    fit_kwargs: dict[str, Any] | None = None,
    n_perm: int = N_PERMUTATIONS,
    seed: int = 42,
    fold_index: int = 0,
) -> dict[str, Any]:
    """Run one LOSO fold: real training + n_perm FULL null retrainings.

    Null semantics (registered, binding): per replicate the TRAIN venue
    labels are permuted within each (symbol, UTC day) cell; the permuted
    venue labels re-define BOTH the contrastive node identities AND the
    probe targets; encoder + probe are retrained FROM SCRATCH (fresh
    encoder from the factory — no frozen-model shuffling); the held-out
    balanced accuracy is measured against the TRUE test labels.
    """
    fit_kwargs = dict(fit_kwargs or {})
    tr, te = fold.train_idx, fold.test_idx
    x_tr, m_tr = panel.x[tr], panel.mask[tr]
    x_te, m_te = panel.x[te], panel.mask[te]
    y_tr = _venue_to_int(panel.venues[tr], venue_order)
    y_te = _venue_to_int(panel.venues[te], venue_order)
    groups_tr = np.array(
        [f"{s}|{d}" for s, d in zip(panel.symbols[tr], panel.dates[tr])],
        dtype=object)

    # --- real training ----------------------------------------------------
    enc = encoder_factory(seed * 1000 + fold_index)
    fit_info = enc.fit(x_tr, m_tr, _node_ids(panel.venues[tr], panel.symbols[tr]),
                       **fit_kwargs)
    emb_tr = enc.embed(x_tr, m_tr)
    emb_te = enc.embed(x_te, m_te)
    probe = train_linear_probe(emb_tr, y_tr, seed=seed)
    pred_te = probe_predict(emb_te, probe)
    acc = balanced_accuracy(y_te, pred_te)

    # --- registered permutation null (FULL retraining per replicate) ------
    null_accs: list[float] = []
    for r in range(n_perm):
        rng = np.random.default_rng((seed, fold_index, r))
        y_perm = permute_within_groups(y_tr, groups_tr, rng)
        venues_perm = np.array([venue_order[int(v)] for v in y_perm], dtype=object)
        enc_r = encoder_factory(seed * 1000 + fold_index * 100 + r + 1)
        enc_r.fit(x_tr, m_tr, _node_ids(venues_perm, panel.symbols[tr]),
                  **fit_kwargs)
        emb_tr_r = enc_r.embed(x_tr, m_tr)
        emb_te_r = enc_r.embed(x_te, m_te)
        probe_r = train_linear_probe(emb_tr_r, y_perm, seed=seed)
        pred_r = probe_predict(emb_te_r, probe_r)
        null_accs.append(balanced_accuracy(y_te, pred_r))
        print(f"[c17_venue] fold {fold.held_out_symbol}: null retraining "
              f"{r + 1}/{n_perm} acc={null_accs[-1]:.4f}",
              file=sys.stderr, flush=True)

    p_value = empirical_p_ge(np.array(null_accs), acc)
    return {
        "held_out_symbol": fold.held_out_symbol,
        "test_start_date": fold.test_start_date,
        "test_end_date": fold.test_end_date,
        "n_train_windows": int(tr.size),
        "n_test_windows": int(te.size),
        "balanced_accuracy": float(acc),
        "acc_threshold": BALANCED_ACC_MIN,
        "acc_threshold_met": bool(acc >= BALANCED_ACC_MIN),
        "null_accuracies": [float(a) for a in null_accs],
        "n_null_retrainings": int(n_perm),
        "null_semantics": (
            "Within-Symbol-Within-Day-Permutation der TRAIN-Venue-Labels; "
            "Encoder+Probe je Replikat VOLL neu trainiert (kein Frozen-"
            "Model-Shuffling); Accuracy stets gegen die WAHREN Test-Labels."
        ),
        "p_value": float(p_value),
        "fit_info": fit_info,
        # carried for pooled accuracy + daily distance series (stripped
        # from the JSON payload by run()):
        "_y_true": y_te,
        "_y_pred": pred_te,
        "_emb_test": emb_te,
        "_test_idx": te,
    }


# ---------------------------------------------------------------------------
# Full run
# ---------------------------------------------------------------------------

def run(
    nodes: list[NodeWindows],
    *,
    encoder_factory: Callable[[int], Any] | None = None,
    fit_kwargs: dict[str, Any] | None = None,
    n_perm: int = N_PERMUTATIONS,
    seed: int = 42,
    c12_payload: dict[str, Any] | None = None,
    cuda_used: bool = False,
    torch_available: bool = False,
    batch_size: int = BATCH_SIZE_MIN,
    source: str = "",
) -> dict[str, Any]:
    """Run the full H-17 measurement; returns the gate-neutral payload.

    ``encoder_factory(seed) -> encoder`` must yield a FRESH encoder with
    ``fit(x, mask, node_ids, **fit_kwargs)`` and ``embed(x, mask)`` (the
    real torch VenueEncoder or the sandbox NumpyFallbackEncoder). Compute
    gating: ``cuda_used`` must reflect a REAL CUDA device; otherwise the
    payload is marked non-verdict-bearing and ``weiter_indication`` is
    forced False.
    """
    if encoder_factory is None:
        encoder_factory = lambda s: NumpyFallbackEncoder(seed=s)  # noqa: E731

    panel = stack_nodes(nodes)
    symbols = tuple(sorted({str(n.symbol) for n in nodes}))
    venue_order = tuple(sorted({str(n.exchange) for n in nodes}))
    if len(venue_order) != 2:
        raise ValueError(f"H-17 needs exactly 2 venues, got {venue_order}")
    if len(symbols) != N_FOLDS:
        print(f"[c17_venue] WARNING: {len(symbols)} symbols != registered "
              f"{N_FOLDS} — fold count follows the data (dev/smoke runs only; "
              f"a verdict-bearing run needs the registered 5-symbol panel)",
              file=sys.stderr, flush=True)
    folds = build_loso_folds(panel, symbols)

    # probe encoder verdict capability (fallback encoders are never capable)
    probe_enc = encoder_factory(seed)
    encoder_verdict_capable = bool(getattr(probe_enc, "verdict_bearing", False))
    del probe_enc

    fold_records = [
        run_fold(panel, fold, encoder_factory=encoder_factory,
                 venue_order=venue_order, fit_kwargs=fit_kwargs,
                 n_perm=n_perm, seed=seed, fold_index=fi)
        for fi, fold in enumerate(folds)
    ]

    # ONE F-VENUE BH-FDR family over the fold p-values.
    p_values = [r["p_value"] for r in fold_records]
    rejected, p_crit = benjamini_hochberg(p_values, FDR_ALPHA)
    for r, rej in zip(fold_records, rejected):
        r["fdr_significant"] = bool(rej)
        r["passed"] = bool(r["acc_threshold_met"] and rej)

    # pooled balanced accuracy over ALL held-out test windows.
    y_true_all = np.concatenate([r["_y_true"] for r in fold_records])
    y_pred_all = np.concatenate([r["_y_pred"] for r in fold_records])
    pooled_acc = balanced_accuracy(y_true_all, y_pred_all)

    # secondary: daily cross-venue embedding-distance series (held-out only).
    emb_all = np.concatenate([r["_emb_test"] for r in fold_records], axis=0)
    idx_all = np.concatenate([r["_test_idx"] for r in fold_records])
    distance = daily_embedding_distance_series(
        emb_all, panel.dates[idx_all], panel.symbols[idx_all],
        panel.venues[idx_all])

    # pre-registered non-redundancy gate against c12_frag/H-12.
    redundancy = redundancy_gate(distance["daily"], c12_payload)

    # gate arithmetic (gate-neutral — the gate-auditor adjudicates).
    n_folds_passed = sum(1 for r in fold_records if r["passed"])
    folds_ok = bool(n_folds_passed >= MIN_PASSING_FOLDS)
    pooled_ok = bool(pooled_acc >= POOLED_ACC_MIN)
    redundancy_ok = bool(redundancy["passed"])

    # compute gate (binding): no real CUDA => never verdict-bearing.
    verdict_bearing = bool(cuda_used and encoder_verdict_capable
                           and batch_size >= BATCH_SIZE_MIN)
    blocked_reasons: list[str] = []
    if not cuda_used:
        blocked_reasons.append("kein echtes CUDA-Device")
    if not encoder_verdict_capable:
        blocked_reasons.append("Nicht-Torch-Fallback-Encoder (Pipeline-Smoke)")
    if batch_size < BATCH_SIZE_MIN:
        blocked_reasons.append(
            f"Batch {batch_size} < registriertes Minimum {BATCH_SIZE_MIN}")
    if len(symbols) != N_FOLDS:
        verdict_bearing = False
        blocked_reasons.append(
            f"{len(symbols)} Symbole statt registrierter {N_FOLDS}")

    weiter_indication = bool(verdict_bearing and folds_ok and pooled_ok
                             and redundancy_ok)

    for r in fold_records:  # strip non-JSON internals
        for k in ("_y_true", "_y_pred", "_emb_test", "_test_idx"):
            r.pop(k, None)

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbols": list(symbols),
        "venues": list(venue_order),
        "n_windows_total": int(panel.x.shape[0]),
        "seed": int(seed),
        "method": {
            "panel": "10 Nodes = 5 Symbole x {Bybit, Binance}, publicTrade "
                     "only, 5-Min-Event-Fenster, 4 Kanaele (Inter-Trade-"
                     "Dauer, Log-Trade-Size, Aggressor-Sign, Tick-Direction)",
            "normalisation": "Pro-Tag-Quantil-Normalisierung je Kanal/Node "
                             "(Rang -> Uniform) — zerstoert triviale Venue-"
                             "Tells (Tick-Size, Fee-Size-Clustering, "
                             "Aktivitaetslevel); Diagnostik-Test in "
                             "tests/unit/test_c17_venue.py",
            "encoder": "Temporal-CNN (dilatiert) + Masked-Mean-Pool "
                       "(count-invariant) + Projection-Head",
            "training": "InfoNCE (Positive = Fenster desselben Nodes zu "
                        "anderen Zeiten, Negative = voller Batch, "
                        f"Batch >= {BATCH_SIZE_MIN}), Frozen-Linear-Probe "
                        "fuer Venue-Identitaet",
            "folds": f"Leave-One-Symbol-Out, {N_FOLDS} Folds, Test = letzte "
                     f"{TEST_WEEKS} Wochen des ausgelassenen Symbols",
            "null": f"Within-Symbol-Within-Day-Label-Permutation, {n_perm} "
                    "VOLLE Retrainings je Fold (kein Frozen-Model-Shuffling)",
        },
        "compute": {
            "torch_available": bool(torch_available),
            "cuda_used": bool(cuda_used),
            "encoder_verdict_capable": encoder_verdict_capable,
            "batch_size": int(batch_size),
            "batch_size_registered_min": BATCH_SIZE_MIN,
            "verdict_bearing": verdict_bearing,
            "blocked_reasons": blocked_reasons,
            "note": COMPUTE_NOTE,
        },
        "fdr_alpha": FDR_ALPHA,
        "fdr_family": FDR_FAMILY,
        "fdr_family_size": len(p_values),
        "fdr_p_crit": float(p_crit),
        "n_fdr_significant": sum(1 for r in fold_records if r["fdr_significant"]),
        "gate_thresholds": {
            "balanced_acc_min": BALANCED_ACC_MIN,
            "min_passing_folds": MIN_PASSING_FOLDS,
            "n_folds": N_FOLDS,
            "pooled_acc_min": POOLED_ACC_MIN,
            "n_permutations": N_PERMUTATIONS,
            "redundancy_rho_max": REDUNDANCY_RHO_MAX,
        },
        "folds": fold_records,
        "n_folds_passed": int(n_folds_passed),
        "folds_criterion_met": folds_ok,
        "pooled_balanced_accuracy": float(pooled_acc),
        "pooled_acc_ok": pooled_ok,
        "embedding_distance": distance,
        "redundancy_gate": redundancy,
        # Gate-neutral observation flag (the gate-auditor adjudicates):
        "weiter_indication": weiter_indication,
    }


# ---------------------------------------------------------------------------
# Report (Deutsch)
# ---------------------------------------------------------------------------

def _fmt(v: Any, nd: int = 4) -> str:
    if v is None:
        return "n/a"
    if isinstance(v, bool):
        return "ja" if v else "nein"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    if not np.isfinite(x):
        return "n/a"
    return f"{x:.{nd}f}"


def render_markdown(payload: dict[str, Any]) -> str:
    """German Markdown report — folds, null, redundancy gate, compute gate."""
    L: list[str] = []
    L.append("# H-17 · Venue-Fingerprint Mess-Gate (Contrastive-Embedding, "
             "F-VENUE, KAPITALFREI, GPU)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — "
             f"`{payload['hypothesis_registry']}` (Welle 5)")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}`")
    m = payload["method"]
    L.append(f"- **Panel:** {m['panel']}")
    L.append(f"- **Normalisierung:** {m['normalisation']}")
    L.append(f"- **Encoder/Training:** {m['encoder']} · {m['training']}")
    L.append(f"- **Folds:** {m['folds']}")
    L.append(f"- **Null:** {m['null']} · Seed: {payload['seed']}")
    L.append(f"- **FDR-Familie:** {payload['fdr_family']} "
             f"({payload['fdr_family_size']} Fold-Tests) · BH-FDR alpha "
             f"{payload['fdr_alpha']} · p_crit {_fmt(payload['fdr_p_crit'])} · "
             f"FDR-signifikant: {payload['n_fdr_significant']}")
    L.append("- **KAPITALFREI:** ja — reine Struktur-/Existenzfrage. "
             "Eine Handelsfolge waere NEUE H-17b, NICHT impliziert.")
    c = payload["compute"]
    L.append(f"- **Compute-Gate:** torch={_fmt(c['torch_available'])} · "
             f"CUDA={_fmt(c['cuda_used'])} · Batch {c['batch_size']} "
             f"(Min {c['batch_size_registered_min']}) · "
             f"**verdikt-tragend: {_fmt(c['verdict_bearing'])}**"
             + (f" · blockiert: {'; '.join(c['blocked_reasons'])}"
                if c["blocked_reasons"] else ""))
    L.append("")
    L.append("> Gate-Urteil faellt der gate-auditor gegen H-17. WEITER "
             "verlangt: Held-out-Balanced-Accuracy >= 0,60 in >= 4/5 "
             "Leave-One-Symbol-Out-Folds gegen die 20-Retrainings-"
             "Permutations-Null nach BH-FDR alpha=0,10 ueber F-VENUE UND "
             "Non-Redundanz-Gate |Spearman rho| < 0,6 gegen die c12_frag-"
             "Tages-lambda2/IPR-Serie. DROP: Pooled-Accuracy < 0,55 ODER "
             "< 4/5 Folds ODER |rho| >= 0,6 (REDUNDANT zu H-12, DROP "
             "unabhaengig von der Accuracy). Kein Graubereich.")
    L.append("")
    L.append(f"**WEITER-Indikation:** {_fmt(payload['weiter_indication'])} · "
             f"Folds bestanden: {payload['n_folds_passed']}/{payload['fdr_family_size']} "
             f"({_fmt(payload['folds_criterion_met'])}) · "
             f"Pooled-Balanced-Accuracy: {_fmt(payload['pooled_balanced_accuracy'])} "
             f"(>= {payload['gate_thresholds']['pooled_acc_min']}: "
             f"{_fmt(payload['pooled_acc_ok'])})")
    L.append("")
    L.append("## Folds (Gate-Kern)")
    L.append("")
    L.append("| Fold (Symbol out) | Test-Zeitraum | Train/Test-Fenster | "
             "Balanced Acc (>= 0,60) | Null (min..max) | p | FDR-sig | bestanden |")
    L.append("|---|---|---:|---:|---|---:|:---:|:---:|")
    for r in payload["folds"]:
        nulls = r["null_accuracies"]
        nul = f"{min(nulls):.3f}..{max(nulls):.3f}" if nulls else "n/a"
        L.append(
            f"| {r['held_out_symbol']} | {r['test_start_date']}.."
            f"{r['test_end_date']} | {r['n_train_windows']}/{r['n_test_windows']} "
            f"| {_fmt(r['balanced_accuracy'])} ({_fmt(r['acc_threshold_met'])}) "
            f"| {nul} | {_fmt(r['p_value'])} | {_fmt(r['fdr_significant'])} "
            f"| {_fmt(r['passed'])} |"
        )
    L.append("")
    L.append("## Non-Redundanz-Gate gegen c12_frag/H-12 (vorregistriert, bindend)")
    L.append("")
    rg = payload["redundancy_gate"]
    L.append(f"- c12-Payload vorhanden: {_fmt(rg['c12_payload_present'])} · "
             f"ueberlappende Tage: {rg['n_overlap_days']} "
             f"(techn. Floor {rg['min_overlap_days_technical']})")
    L.append(f"- Spearman rho vs. lambda2: {_fmt(rg['rho_lambda2'])} · "
             f"vs. IPR(v2): {_fmt(rg['rho_ipr_v2'])} · "
             f"max|rho|: {_fmt(rg['max_abs_rho'])} "
             f"(Schwelle {rg['rho_max_registered']})")
    L.append(f"- auswertbar: {_fmt(rg['evaluable'])} · "
             f"**REDUNDANT (DROP): {_fmt(rg['redundant'])}** · "
             f"bestanden: {_fmt(rg['passed'])}")
    L.append("")
    L.append("## Taegliche Cross-Venue-Embedding-Distance-Serie "
             "(sekundaer, nicht-urteilstragend)")
    L.append("")
    daily = payload["embedding_distance"]["daily"]
    L.append(f"- Tage: {len(daily)}")
    if daily:
        vals = list(daily.values())
        L.append(f"- Median: {_fmt(float(np.median(vals)))} · "
                 f"Min: {_fmt(min(vals))} · Max: {_fmt(max(vals))}")
    L.append("")
    L.append("*Erzeugt von `scripts/c17_venue.py` (Welle 5, read-only "
             "Harvester). capital_free=true. Endgueltiges Gate-Urteil: "
             "gate-auditor gegen H-17.*")
    L.append("")
    return "\n".join(L)


__all__ = [
    "BALANCED_ACC_MIN",
    "FDR_FAMILY",
    "HYPOTHESIS_ID",
    "MIN_PASSING_FOLDS",
    "N_FOLDS",
    "N_PERMUTATIONS",
    "POOLED_ACC_MIN",
    "REGISTRY_PATH",
    "SCHEMA_VERSION",
    "TEST_DAYS",
    "TEST_WEEKS",
    "Fold",
    "Panel",
    "build_loso_folds",
    "render_markdown",
    "run",
    "run_fold",
    "stack_nodes",
]
