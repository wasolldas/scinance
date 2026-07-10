"""Orchestration + gate-neutral payload for the H-15 grammar gate (F-GRAMMAR).

Pipeline (registry H-15, pre-fixed):
  1. Load the per-symbol Bybit publicTrade stream over the ~100-day grid
     (read-only harvester tree), 5 perp symbols.
  2. Purged walk-forward: 4 folds, 1-day embargo (``stats.walk_forward_folds``).
  3. Per fold: fit the tokenizer (Side x Signed-Size-Quantile-8 x Log-IAT-8,
     vocab 128) on the TRAIN fold ONLY (leak discipline), tokenize train/test.
  4. Baseline arm (CPU): KT-smoothed Markov k=0..4 + interpolated k=4 on the
     SAME train fold; best (lowest OOS CE) baseline per fold.
  5. Transformer arm (GPU): decoder-only causal transformer (~2-4M params,
     context 1024), 3 seeds per fold, OOS CE = mean over seeds.
  6. Null: >= 200 within-hour-of-day block-shuffle surrogates (block 256
     events) of the TEST stream; both trained arms are RE-EVALUATED (never
     re-trained) on each surrogate -> null of the CE-gap distribution.
  7. Per symbol: token-weighted pooling over the 4 folds; one-sided empirical
     p of the pooled gap vs. the pooled surrogate gaps; BH-FDR alpha=0.10
     over F-GRAMMAR (5 symbols).

The driver renders NO overall verdict — the gate-auditor adjudicates against
the registered H-15 gate. ``symbol_pass`` / ``family_pass_geq_4of5`` are
gate-neutral observations.

COMPUTE GATE (binding, task spec): a verdict-bearing run REQUIRES torch with
a real CUDA device. ``mode="full"`` refuses to start without CUDA
(``ComputeUnavailableError``). ``mode="mechanics"`` runs whatever is
CPU-possible (tokenizer, folds, Markov, surrogates; transformer only if torch
happens to be present) and ALWAYS stamps ``gate_valid: false`` and
``ran_on_gpu: false`` — its output can never carry a verdict.

Documented pre-fixed implementation decisions (registry is silent, fixed here
BEFORE any run; see README_H15.md):
  * D1 aggregation: per-symbol CE = test-token-weighted mean over the 4 folds
    (transformer CE per fold = mean over the 3 seeds first); the surrogate
    null is pooled the same way (surrogate r's pooled gap = token-weighted
    mean of the per-fold gap_r), so observed statistic and null are computed
    by the identical functional.
  * D2 surrogate scoring: surrogates are EVALUATED with the already-trained
    models (best-on-observed Markov baseline fixed per fold; transformer =
    mean over all 3 seed models) — the registered ">= 200
    Surrogat-Evaluierungen" are forward passes, never re-trainings.
  * D3 evaluation support: every model scores positions >= CE_WARMUP = 4 of
    the standalone OOS stream (see ``markov_baseline``), test streams are
    never conditioned on train/embargo tokens (causality by construction).
  * D4 vocab: registered base vocab 128 (tick-direction extension to 256 is
    OFF by default and would be flagged in the payload if enabled).

DIFFERENZIERUNG (Pflicht, Registry H-15 Selbstkill — woertlich):
"Differenzierung zu den gesperrten Informationstheorie-Clustern (PE/TE,
H-06/H-04) ist konzeptionell sauber (Event-Stream statt Renditen, CE als
Scoring-Rule statt Entropie-Schaetzer, kein rho/Trading-Gate)." H-15 misst
den TOKENISIERTEN EVENT-STREAM (Side/Size/Inter-Arrival), NICHT Renditen;
die Statistik ist die Next-Token-CROSS-ENTROPY zweier expliziter Modelle
(eine Scoring-Rule), KEIN Permutations-/Transfer-Entropie-SCHAETZER; und es
gibt KEIN rho-/Tradability-/Trading-Gate — reine kapitalfreie
Existence-of-Structure-Messung.

KAPITALFREI: ``capital_free: true`` — no capital metric of any kind anywhere.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .markov_baseline import CE_WARMUP, best_baseline_ce, fit_all_baselines
from .stats import (
    BLOCK_LEN_EVENTS,
    EMBARGO_DAYS,
    FAMILY_SIZE,
    FDR_ALPHA,
    FDR_FAMILY,
    Fold,
    N_FOLDS,
    N_SEEDS,
    N_SURROGATES_DEFAULT,
    REL_CE_GAP_MIN,
    SURROGATE_PERCENTILE,
    SYMBOLS_PASS_MIN,
    benjamini_hochberg,
    hour_block_shuffle,
    relative_ce_gap,
    surrogate_gap_p,
    walk_forward_folds,
)
from .tokenizer import (
    TokenizerSpec,
    derive_event_features,
    fit_tokenizer,
    tokenize,
)
from .transformer import (
    ComputeUnavailableError,
    GrammarTransformerConfig,
    evaluate_ce,
    num_parameters,
    torch_cuda_status,
    train_transformer,
)

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-15"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"

#: Registry H-15 data binding: Basis-Bestand 2026-03-27..Cutoff, ~100 days.
#: 2026-03-27..2026-07-04 = exactly 100 calendar days (same cutoff as the
#: Wave-4 grids).
DEFAULT_DATA_START = "2026-03-27"
DEFAULT_DATA_END = "2026-07-04"

#: Program-standard 5-symbol Bybit perp panel (registry H-15: F, 5 Symbole).
DEFAULT_SYMBOLS: tuple[str, ...] = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT")

#: Registered 3 seeds per fold (pre-fixed values, documented).
DEFAULT_SEEDS: tuple[int, ...] = (42, 43, 44)

#: Mandatory differentiation note (registry H-15 Selbstkill — see docstring).
DIFFERENTIATION_NOTE = (
    "Differenzierung zu den gesperrten Informationstheorie-Clustern (PE/TE, "
    "H-06/H-04) ist konzeptionell sauber: (1) EVENT-STREAM statt Renditen — "
    "tokenisiert wird der publicTrade-Fluss (Side x Signed-Size-Quantil x "
    "Log-Inter-Arrival), keine Preis-/Rendite-Serie; (2) CROSS-ENTROPY als "
    "SCORING-RULE zweier expliziter Modelle (Causal-Transformer vs. "
    "Variable-Order-Markov) statt eines Entropie-SCHAETZERS (keine "
    "Permutations-Entropie, keine Transfer-Entropie); (3) KEIN rho-/Trading-"
    "Gate — reine kapitalfreie Existence-of-Structure-Messung. Eine "
    "Handelsfolge waere NEUE H-15b, NICHT impliziert."
)

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9_]+$")

_MS_PER_DAY = 86_400_000
_MS_PER_HOUR = 3_600_000


class DataError(RuntimeError):
    """Raised when a harvester stream cannot be loaded."""


# ----------------------------------------------------------------------------
# Event stream container + read-only harvester loader
# ----------------------------------------------------------------------------

@dataclass
class EventStream:
    """One symbol's trade-event stream (time-ordered, strictly causal layout)."""

    symbol: str
    ts_ms: np.ndarray   # int64, non-decreasing
    price: np.ndarray   # float64, > 0
    size: np.ndarray    # float64, > 0
    side: np.ndarray    # int64: 1 = taker Buy, 0 = taker Sell

    def __post_init__(self) -> None:
        n = self.ts_ms.size
        if not (self.price.size == n and self.size.size == n and self.side.size == n):
            raise DataError(f"{self.symbol}: array length mismatch")
        if n and np.any(np.diff(self.ts_ms) < 0):
            raise DataError(f"{self.symbol}: timestamps not sorted")

    @property
    def n_events(self) -> int:
        return int(self.ts_ms.size)

    def epoch_days(self) -> np.ndarray:
        return (self.ts_ms // _MS_PER_DAY).astype(np.int64)

    def hours_of_day(self) -> np.ndarray:
        return ((self.ts_ms // _MS_PER_HOUR) % 24).astype(np.int64)


def daily_grid(start_date: str, end_date: str) -> list[str]:
    """Inclusive ISO-day grid (same convention as the Wave-4 packages)."""
    for d in (start_date, end_date):
        if not _DATE_RE.match(d):
            raise DataError(f"invalid date (want YYYY-MM-DD): {d!r}")
    d0 = _iso(start_date)
    d1 = _iso(end_date)
    if d1 < d0:
        raise DataError(f"end_date {end_date} before start_date {start_date}")
    return [(d0 + timedelta(days=i)).isoformat() for i in range((d1 - d0).days + 1)]


def _iso(d: str) -> date:
    y, m, dd = (int(x) for x in d.split("-"))
    return date(y, m, dd)


def _iso_to_epoch_day(d: str) -> int:
    return (_iso(d) - date(1970, 1, 1)).days


def load_trade_events(
    base_dir: Path | str,
    symbol: str,
    days: list[str],
    *,
    exchange: str = "bybit",
    stream: str = "publicTrade",
    max_events_per_day: int = 0,
) -> EventStream:
    """Load the full publicTrade stream for one symbol (read-only DuckDB).

    Same Hive-glob + payload-field convention as
    ``c01_ofi_sign.oos.load_harvest_window`` (backfill keys ``side``/``price``
    /``size``, live keys ``S``/``p``/``v``); side normalised to int in SQL
    (1 = Buy, 0 = Sell). Results ordered by exchange timestamp.
    ``max_events_per_day`` > 0 caps events per day (FIRST events of the day)
    — a mechanics/testing convenience that is flagged by the caller and voids
    ``gate_valid`` (it changes the registered data binding).
    """
    import duckdb

    if not _SYMBOL_RE.match(symbol):
        raise DataError(f"invalid symbol: {symbol!r}")
    base = Path(base_dir)
    globs = [
        str(base / "raw" / exchange / stream / f"symbol={symbol}" / f"date={d}" / "*.parquet")
        for d in days
    ]
    present = [g for g in globs if list(Path(g).parent.glob("*.parquet"))]
    if not present:
        raise DataError(
            f"no parquet for {exchange}/{stream}/{symbol} in "
            f"{days[0]}..{days[-1]} under {base}"
        )
    file_list = "[" + ", ".join("'" + g.replace("'", "''") + "'" for g in present) + "]"
    per_day_limit = ""
    inner = f"""
        SELECT ts_exchange_ms AS ts,
               CASE WHEN lower(COALESCE(json_extract_string(payload_json,'$.side'),
                                        json_extract_string(payload_json,'$.S'))) = 'buy'
                    THEN 1 ELSE 0 END AS side,
               CAST(COALESCE(json_extract_string(payload_json,'$.price'),
                             json_extract_string(payload_json,'$.p')) AS DOUBLE) AS price,
               CAST(COALESCE(json_extract_string(payload_json,'$.size'),
                             json_extract_string(payload_json,'$.v')) AS DOUBLE) AS size
        FROM read_parquet({file_list}, hive_partitioning=1, union_by_name=1)
        WHERE ts_exchange_ms IS NOT NULL
          AND (json_extract_string(payload_json,'$.side') IS NOT NULL
               OR json_extract_string(payload_json,'$.S') IS NOT NULL)
    """
    if max_events_per_day and max_events_per_day > 0:
        per_day_limit = f"""
            QUALIFY row_number() OVER (
                PARTITION BY ts // {_MS_PER_DAY} ORDER BY ts
            ) <= {int(max_events_per_day)}
        """
    sql = f"SELECT ts, side, price, size FROM ({inner}) {per_day_limit} ORDER BY ts"
    con = duckdb.connect()
    try:
        arrs = con.execute(sql).fetchnumpy()
    finally:
        con.close()
    ts = np.asarray(arrs["ts"], dtype=np.int64)
    side = np.asarray(arrs["side"], dtype=np.int64)
    price = np.asarray(arrs["price"], dtype=np.float64)
    size = np.asarray(arrs["size"], dtype=np.float64)
    good = np.isfinite(price) & np.isfinite(size) & (price > 0) & (size > 0)
    n_bad = int((~good).sum())
    if n_bad:
        print(f"[c15_grammar] {symbol}: dropped {n_bad} malformed rows",
              file=sys.stderr, flush=True)
        ts, side, price, size = ts[good], side[good], price[good], size[good]
    if ts.size == 0:
        raise DataError(f"{symbol}: 0 usable trade events in {days[0]}..{days[-1]}")
    print(f"[c15_grammar] {symbol}: {ts.size} events "
          f"({days[0]}..{days[-1]})", file=sys.stderr, flush=True)
    return EventStream(symbol=symbol, ts_ms=ts, price=price, size=size, side=side)


# ----------------------------------------------------------------------------
# Per-fold preparation (the leak-critical step)
# ----------------------------------------------------------------------------

def prepare_fold(
    events: EventStream,
    fold: Fold,
    *,
    use_tick_direction: bool = False,
) -> tuple[TokenizerSpec, np.ndarray, np.ndarray, np.ndarray]:
    """Tokenize one fold: spec fitted on TRAIN events ONLY (leak discipline).

    Returns ``(spec, train_tokens, test_tokens, test_hours)``. The tokenizer
    quantile boundaries are computed exclusively from train-fold events;
    embargo-day events belong to NEITHER side. Features (IAT, tick direction)
    are derived on the full stream — each is strictly causal (position t uses
    only data <= t), so a test event's IAT referencing the previous
    (embargo) event's timestamp is past information, not leakage.
    """
    feats = derive_event_features(events.ts_ms, events.price, events.size, events.side)
    ev_days = events.epoch_days()
    train_days = np.array([_iso_to_epoch_day(d) for d in fold.train_days], dtype=np.int64)
    test_days = np.array([_iso_to_epoch_day(d) for d in fold.test_days], dtype=np.int64)
    train_mask = np.isin(ev_days, train_days)
    test_mask = np.isin(ev_days, test_days)
    if not train_mask.any():
        raise DataError(f"{events.symbol} fold {fold.index}: empty train fold")
    if not test_mask.any():
        raise DataError(f"{events.symbol} fold {fold.index}: empty test fold")

    spec = fit_tokenizer(
        feats["signed_size"][train_mask],
        feats["log_iat"][train_mask],
        use_tick_direction=use_tick_direction,
    )
    train_tokens = tokenize(
        spec, feats["side"][train_mask], feats["signed_size"][train_mask],
        feats["log_iat"][train_mask],
        feats["tick_dir"][train_mask] if use_tick_direction else None,
    )
    test_tokens = tokenize(
        spec, feats["side"][test_mask], feats["signed_size"][test_mask],
        feats["log_iat"][test_mask],
        feats["tick_dir"][test_mask] if use_tick_direction else None,
    )
    test_hours = events.hours_of_day()[test_mask]
    return spec, train_tokens, test_tokens, test_hours


# ----------------------------------------------------------------------------
# Per-symbol checkpointing (atomic write, resume by skip)
#
# A full T3 run trains 5 symbols x 4 folds x 3 seeds sequentially and can
# take HOURS on the 12h runner timeout budget (see run_h15.sh/.ps1). Without
# checkpointing, a timeout/crash after N of 5 symbols loses ALL of them —
# including the already-finished ones (see audit_h15.md Bug #3). Each
# completed symbol's AGGREGATED result (the same dict that lands in
# ``per_symbol`` below) is atomically written to
# ``<ckpt_dir>/<symbol>.json``; a re-run with the SAME ``ckpt_dir`` loads it
# back and skips re-training that symbol entirely. A ``fingerprint`` of the
# registered run parameters is stored alongside the result and re-checked on
# load — a checkpoint from a run with different folds/seeds/surrogates/
# architecture/data-grid is treated as stale (recomputed, never silently
# reused) so resume can never mix results from two different configurations.
# ----------------------------------------------------------------------------

def _run_fingerprint(
    *,
    cfg: GrammarTransformerConfig,
    n_folds: int,
    embargo_days: int,
    seeds: tuple[int, ...],
    n_surrogates: int,
    block_len: int,
    use_tick_direction: bool,
    days: list[str],
) -> dict[str, Any]:
    return {
        "n_folds": int(n_folds),
        "embargo_days": int(embargo_days),
        "seeds": list(seeds),
        "n_surrogates": int(n_surrogates),
        "block_len": int(block_len),
        "use_tick_direction": bool(use_tick_direction),
        "data_start": days[0],
        "data_end": days[-1],
        "n_days": len(days),
        "model_config": {
            "vocab_size": cfg.vocab_size,
            "context_len": cfg.context_len,
            "d_model": cfg.d_model,
            "n_heads": cfg.n_heads,
            "n_layers": cfg.n_layers,
            "dropout": cfg.dropout,
            "lr": cfg.lr,
            "batch_size": cfg.batch_size,
            "epochs": cfg.epochs,
            "grad_clip": cfg.grad_clip,
        },
    }


def _ckpt_clean(v: Any) -> Any:
    """Recursively swap non-finite floats for JSON-null (round-trips via _f)."""
    if isinstance(v, float) and not math.isfinite(v):
        return None
    if isinstance(v, dict):
        return {k: _ckpt_clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_ckpt_clean(x) for x in v]
    return v


def _symbol_ckpt_path(ckpt_dir: Path | str, symbol: str) -> Path:
    return Path(ckpt_dir) / f"{symbol}.json"


def _write_symbol_checkpoint(
    path: Path, symbol_result: dict[str, Any], fingerprint: dict[str, Any],
) -> None:
    """Atomic tmp+rename write (H-14 checkpoint pattern, see ablation.py)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    payload = {"fingerprint": fingerprint, "result": symbol_result}
    tmp.write_text(json.dumps(_ckpt_clean(payload), indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _load_symbol_checkpoint(
    path: Path, fingerprint: dict[str, Any],
) -> dict[str, Any] | None:
    """Return the cached aggregated symbol result iff the fingerprint matches.

    A missing file, unreadable/corrupt JSON, or a fingerprint mismatch (run
    parameters changed since the checkpoint was written) all return ``None``
    — the caller then recomputes the symbol from scratch rather than risking
    a resumed run that silently mixes two different configurations.
    """
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or "result" not in payload:
        return None
    if payload.get("fingerprint") != fingerprint:
        return None
    return payload["result"]


# ----------------------------------------------------------------------------
# Main run
# ----------------------------------------------------------------------------

def run(
    symbol_events: dict[str, EventStream],
    days: list[str],
    *,
    mode: str = "full",
    config: GrammarTransformerConfig | None = None,
    n_folds: int = N_FOLDS,
    embargo_days: int = EMBARGO_DAYS,
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
    n_surrogates: int = N_SURROGATES_DEFAULT,
    block_len: int = BLOCK_LEN_EVENTS,
    use_tick_direction: bool = False,
    surrogate_seed: int = 20260709,
    events_capped: bool = False,
    source: str = "",
    ckpt_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Run the H-15 grammar gate; return the gate-neutral payload.

    ``mode="full"``: verdict-capable — REFUSES to start without torch+CUDA
    (``ComputeUnavailableError``); trains on ``cuda``.
    ``mode="mechanics"``: pipeline-mechanics only — never verdict-bearing
    (``gate_valid: false``, ``ran_on_gpu: false`` ALWAYS); transformer arm
    runs on CPU if torch is present, else is skipped (CEs NaN).

    ``ckpt_dir``: if given, EVERY completed symbol is atomically checkpointed
    to ``<ckpt_dir>/<symbol>.json`` (fingerprinted against the run's
    registered parameters); re-calling ``run()`` with the SAME ``ckpt_dir``
    resumes by skipping already-checkpointed symbols instead of re-training
    them — a timeout/crash loses at most the symbol that was in flight, not
    the whole multi-hour run (see audit_h15.md Bug #3).
    """
    if mode not in ("full", "mechanics"):
        raise ValueError(f"unknown mode {mode!r}")
    cfg = config or GrammarTransformerConfig()
    compute = torch_cuda_status()
    gate_valid_reasons: list[str] = []

    if mode == "full":
        if not compute["torch_available"]:
            raise ComputeUnavailableError(
                "H-15 full run refused: torch not installed (registry: GPU, "
                "zwingend). Use --check-gpu-only / mechanics mode."
            )
        if not compute["cuda_available"]:
            raise ComputeUnavailableError(
                "H-15 full run refused: no CUDA device (registry: GPU, "
                "zwingend). A CPU run would silently shrink the registered "
                "seed/fold/surrogate discipline."
            )
        device = "cuda"
        ran_on_gpu = True
        transformer_arm = True
    else:
        device = "cpu"
        ran_on_gpu = False
        transformer_arm = bool(compute["torch_available"])
        gate_valid_reasons.append("mechanics mode — never verdict-bearing")
        if not transformer_arm:
            gate_valid_reasons.append("torch unavailable — transformer arm skipped")

    # Deviation-from-registered-design checks (full mode -> gate_valid gates)
    if n_folds != N_FOLDS:
        gate_valid_reasons.append(f"n_folds={n_folds} != registered {N_FOLDS}")
    if embargo_days != EMBARGO_DAYS:
        gate_valid_reasons.append(f"embargo_days={embargo_days} != registered {EMBARGO_DAYS}")
    if len(seeds) != N_SEEDS:
        gate_valid_reasons.append(f"{len(seeds)} seeds != registered {N_SEEDS}")
    if n_surrogates < N_SURROGATES_DEFAULT:
        gate_valid_reasons.append(
            f"n_surrogates={n_surrogates} < registered minimum {N_SURROGATES_DEFAULT}")
    if block_len != BLOCK_LEN_EVENTS:
        gate_valid_reasons.append(f"block_len={block_len} != registered {BLOCK_LEN_EVENTS}")
    if events_capped:
        gate_valid_reasons.append("per-day event cap active — data binding changed")
    if use_tick_direction:
        gate_valid_reasons.append(
            "tick-direction vocab extension (256) enabled — registered base is 128")
    _default_cfg = GrammarTransformerConfig()
    for field in ("context_len", "d_model", "n_heads", "n_layers", "epochs",
                  "batch_size", "lr", "dropout", "grad_clip"):
        if getattr(cfg, field) != getattr(_default_cfg, field):
            gate_valid_reasons.append(
                f"{field}={getattr(cfg, field)} != registered default "
                f"{getattr(_default_cfg, field)}")

    folds = walk_forward_folds(days, n_folds=n_folds, embargo_days=embargo_days)
    symbols = list(symbol_events.keys())
    if tuple(sorted(symbols)) != tuple(sorted(DEFAULT_SYMBOLS)):
        gate_valid_reasons.append(
            f"symbols {symbols} != registered 5-symbol panel {DEFAULT_SYMBOLS}")

    ckpt_fingerprint = _run_fingerprint(
        cfg=cfg, n_folds=n_folds, embargo_days=embargo_days, seeds=seeds,
        n_surrogates=n_surrogates, block_len=block_len,
        use_tick_direction=use_tick_direction, days=days,
    )

    per_symbol: list[dict[str, Any]] = []
    for symbol in symbols:
        if ckpt_dir is not None:
            cached = _load_symbol_checkpoint(
                _symbol_ckpt_path(ckpt_dir, symbol), ckpt_fingerprint)
            if cached is not None:
                print(f"[c15_grammar] {symbol}: RESUMED from checkpoint "
                      f"({_symbol_ckpt_path(ckpt_dir, symbol)}) — skipping "
                      f"training", file=sys.stderr, flush=True)
                per_symbol.append(cached)
                continue

        events = symbol_events[symbol]
        print(f"[c15_grammar] === {symbol}: {events.n_events} events, "
              f"{len(folds)} folds ===", file=sys.stderr, flush=True)
        fold_rows: list[dict[str, Any]] = []
        fold_gap_matrix: list[np.ndarray] = []  # per fold: (n_surrogates,)
        for fold in folds:
            row = _run_fold(
                events, fold, cfg,
                seeds=seeds, n_surrogates=n_surrogates, block_len=block_len,
                use_tick_direction=use_tick_direction, device=device,
                transformer_arm=transformer_arm,
                surrogate_seed=surrogate_seed + 7919 * fold.index,
            )
            fold_rows.append(row["public"])
            fold_gap_matrix.append(row["surrogate_gaps"])

        symbol_result = _aggregate_symbol(symbol, fold_rows, fold_gap_matrix,
                                           n_surrogates)
        per_symbol.append(symbol_result)
        if ckpt_dir is not None:
            _write_symbol_checkpoint(
                _symbol_ckpt_path(ckpt_dir, symbol), symbol_result,
                ckpt_fingerprint)
            print(f"[c15_grammar] {symbol}: checkpointed to "
                  f"{_symbol_ckpt_path(ckpt_dir, symbol)}",
                  file=sys.stderr, flush=True)

    # BH-FDR over the F-GRAMMAR family (one p per symbol).
    p_for_bh = [
        s["surrogate_p"] if np.isfinite(_f(s["surrogate_p"])) else 1.0
        for s in per_symbol
    ]
    rejected, p_crit = benjamini_hochberg([float(p) for p in p_for_bh], FDR_ALPHA)
    for s, p, rej in zip(per_symbol, p_for_bh, rejected):
        s["p_for_fdr"] = float(p)
        s["fdr_significant"] = bool(rej)
        s["symbol_pass"] = bool(
            rej
            and np.isfinite(_f(s["relative_ce_gap"]))
            and _f(s["relative_ce_gap"]) >= REL_CE_GAP_MIN
            and bool(s["gap_above_surrogate_p95"])
        )

    n_pass = sum(1 for s in per_symbol if s["symbol_pass"])
    family_complete = len(per_symbol) >= FAMILY_SIZE
    if not family_complete:
        gate_valid_reasons.append(
            f"only {len(per_symbol)} symbols (< registered family of {FAMILY_SIZE})")
    # A verdict-bearing gate needs every symbol's statistic to be DEFINED.
    for s in per_symbol:
        if not (np.isfinite(_f(s["transformer_ce"]))
                and np.isfinite(_f(s["best_markov_ce"]))
                and np.isfinite(_f(s["surrogate_p"]))):
            gate_valid_reasons.append(
                f"{s['symbol']}: undefined CE/p — gate cannot be adjudicated")

    gate_valid = mode == "full" and ran_on_gpu and not gate_valid_reasons

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "mode": mode,
        "ran_on_gpu": bool(ran_on_gpu),
        "gate_valid": bool(gate_valid),
        "gate_valid_reasons": gate_valid_reasons,
        "compute": compute,
        "device": device,
        "data_start": days[0],
        "data_end": days[-1],
        "n_days": len(days),
        "symbols": symbols,
        "n_folds": int(n_folds),
        "embargo_days": int(embargo_days),
        "folds": [
            {
                "index": f.index,
                "train_start": f.train_days[0], "train_end": f.train_days[-1],
                "n_train_days": len(f.train_days),
                "embargo": list(f.embargo),
                "test_start": f.test_days[0], "test_end": f.test_days[-1],
                "n_test_days": len(f.test_days),
            }
            for f in folds
        ],
        "seeds": list(seeds),
        "n_surrogates": int(n_surrogates),
        "surrogate_block_len_events": int(block_len),
        "surrogate_kind": "within-hour-of-day block shuffle (registry H-15)",
        "use_tick_direction": bool(use_tick_direction),
        "vocab_size": int(cfg.vocab_size),
        "events_capped": bool(events_capped),
        "model_config": {
            "context_len": cfg.context_len,
            "d_model": cfg.d_model,
            "n_heads": cfg.n_heads,
            "n_layers": cfg.n_layers,
            "dropout": cfg.dropout,
            "lr": cfg.lr,
            "batch_size": cfg.batch_size,
            "epochs": cfg.epochs,
        },
        "ce_unit": "nats (natural log); gate threshold is RELATIVE (unit-invariant)",
        "ce_warmup_positions": CE_WARMUP,
        "gate_thresholds": {
            "rel_ce_gap_min": REL_CE_GAP_MIN,
            "surrogate_percentile": SURROGATE_PERCENTILE,
            "symbols_pass_min": SYMBOLS_PASS_MIN,
            "family_size": FAMILY_SIZE,
            "fdr_alpha": FDR_ALPHA,
            "hard_one_window_drop": True,
        },
        "fdr_alpha": FDR_ALPHA,
        "fdr_family": FDR_FAMILY,
        "fdr_p_crit": _f(p_crit),
        "n_fdr_significant": int(sum(1 for s in per_symbol if s["fdr_significant"])),
        # Gate-neutral family-level observation (gate-auditor adjudicates):
        "n_symbols_pass": int(n_pass),
        "family_complete": bool(family_complete),
        "family_pass_geq_4of5": bool(family_complete and n_pass >= SYMBOLS_PASS_MIN),
        "differentiation_note": DIFFERENTIATION_NOTE,
        "per_symbol": per_symbol,
    }


def _run_fold(
    events: EventStream,
    fold: Fold,
    cfg: GrammarTransformerConfig,
    *,
    seeds: tuple[int, ...],
    n_surrogates: int,
    block_len: int,
    use_tick_direction: bool,
    device: str,
    transformer_arm: bool,
    surrogate_seed: int,
) -> dict[str, Any]:
    """One (symbol, fold) cell: tokenize, both arms, surrogate gap null."""
    spec, train_tokens, test_tokens, test_hours = prepare_fold(
        events, fold, use_tick_direction=use_tick_direction,
    )
    n_scored = max(0, test_tokens.size - CE_WARMUP)

    # Baseline arm (CPU) — fixed BEFORE surrogates: best on the observed OOS.
    baselines = fit_all_baselines(train_tokens, spec.vocab_size)
    best_name, best_ce, all_ces = best_baseline_ce(baselines, test_tokens)
    best_model = baselines.get(best_name)

    # Transformer arm — 3 seeds, OOS CE = mean over seeds (registry).
    seed_models: list[Any] = []
    seed_ces: list[float] = []
    if transformer_arm:
        for seed in seeds:
            model = train_transformer(train_tokens, cfg, seed=seed, device=device)
            ce = evaluate_ce(model, test_tokens, cfg, device=device)
            seed_models.append(model)
            seed_ces.append(float(ce))
            print(f"[c15_grammar] {events.symbol} fold {fold.index} seed {seed}: "
                  f"transformer_ce={ce:.4f} (params={num_parameters(model)})",
                  file=sys.stderr, flush=True)
    trans_ce = float(np.mean(seed_ces)) if seed_ces else float("nan")

    # Surrogate null: re-EVALUATE both trained arms on each surrogate (D2).
    rng = np.random.default_rng(surrogate_seed)
    surr_gaps = np.full(n_surrogates, np.nan, dtype=np.float64)
    for r in range(n_surrogates):
        surr = hour_block_shuffle(test_tokens, test_hours,
                                  block_len=block_len, rng=rng)
        m_ce = best_model.cross_entropy(surr) if best_model is not None else float("nan")
        if seed_models:
            t_ces = [evaluate_ce(m, surr, cfg, device=device) for m in seed_models]
            t_ce = float(np.mean(t_ces))
        else:
            t_ce = float("nan")
        surr_gaps[r] = m_ce - t_ce

    obs_gap = best_ce - trans_ce if np.isfinite(best_ce) and np.isfinite(trans_ce) \
        else float("nan")
    print(f"[c15_grammar] {events.symbol} fold {fold.index}: "
          f"markov[{best_name}]={best_ce:.4f} transformer={trans_ce:.4f} "
          f"gap={obs_gap:.5f} (n_test_tokens={test_tokens.size})",
          file=sys.stderr, flush=True)

    public = {
        "fold": fold.index,
        "n_train_events": int(train_tokens.size),
        "n_test_events": int(test_tokens.size),
        "n_scored_test_tokens": int(n_scored),
        "tokenizer_size_edges": list(spec.size_edges),
        "tokenizer_iat_edges": list(spec.iat_edges),
        "tokenizer_fit_on": "train fold ONLY (leak discipline, registry H-15)",
        "best_markov_name": best_name,
        "best_markov_ce": _f(best_ce),
        "markov_ces": {k: _f(v) for k, v in all_ces.items()},
        "transformer_ces_per_seed": [_f(c) for c in seed_ces],
        "transformer_ce_mean_seeds": _f(trans_ce),
        "observed_gap": _f(obs_gap),
        "n_surrogates": int(n_surrogates),
        "surrogate_gap_p95": _f(np.nanpercentile(surr_gaps, SURROGATE_PERCENTILE))
        if np.isfinite(surr_gaps).any() else float("nan"),
    }
    return {"public": public, "surrogate_gaps": surr_gaps}


def _aggregate_symbol(
    symbol: str,
    fold_rows: list[dict[str, Any]],
    fold_gap_matrix: list[np.ndarray],
    n_surrogates: int,
) -> dict[str, Any]:
    """Token-weighted pooling over folds (documented decision D1)."""
    w = np.array([max(0, r["n_scored_test_tokens"]) for r in fold_rows],
                 dtype=np.float64)
    if w.sum() <= 0:
        w = np.ones(len(fold_rows), dtype=np.float64)
    w = w / w.sum()
    markov = np.array([_f(r["best_markov_ce"]) for r in fold_rows])
    trans = np.array([_f(r["transformer_ce_mean_seeds"]) for r in fold_rows])
    markov_sym = float(np.sum(w * markov)) if np.all(np.isfinite(markov)) else float("nan")
    trans_sym = float(np.sum(w * trans)) if np.all(np.isfinite(trans)) else float("nan")
    obs_gap = markov_sym - trans_sym if np.isfinite(markov_sym) and np.isfinite(trans_sym) \
        else float("nan")
    rel_gap = relative_ce_gap(markov_sym, trans_sym)

    # Pooled surrogate gaps: same functional as the observed statistic (D1).
    gaps = np.vstack(fold_gap_matrix)  # (n_folds, n_surrogates)
    pooled = np.full(n_surrogates, np.nan, dtype=np.float64)
    finite_rows = np.all(np.isfinite(gaps), axis=0)
    pooled[finite_rows] = np.einsum("f,fr->r", w, gaps[:, finite_rows]) \
        if finite_rows.any() else pooled[finite_rows]
    p95 = float(np.nanpercentile(pooled, SURROGATE_PERCENTILE)) \
        if np.isfinite(pooled).any() else float("nan")
    p_val = surrogate_gap_p(obs_gap, pooled)
    above = bool(np.isfinite(obs_gap) and np.isfinite(p95) and obs_gap > p95)

    return {
        "symbol": symbol,
        "n_folds": len(fold_rows),
        "fold_weights_scored_tokens": [float(x) for x in w],
        "best_markov_ce": _f(markov_sym),
        "transformer_ce": _f(trans_sym),
        "observed_gap": _f(obs_gap),
        "relative_ce_gap": _f(rel_gap),
        "rel_gap_threshold_met": bool(np.isfinite(rel_gap) and rel_gap >= REL_CE_GAP_MIN),
        "surrogate_gap_p95": _f(p95),
        "gap_above_surrogate_p95": above,
        "surrogate_p": _f(p_val),
        "n_surrogates_finite": int(np.isfinite(pooled).sum()),
        "folds": fold_rows,
    }


def _f(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


# ----------------------------------------------------------------------------
# Report (Deutsch)
# ----------------------------------------------------------------------------

def _fmt(v: Any, nd: int = 4) -> str:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "n/a"
    if not np.isfinite(x):
        return "n/a"
    return f"{x:.{nd}f}"


def render_markdown(payload: dict[str, Any]) -> str:
    L: list[str] = []
    L.append("# C-15 Trade-Tape-Event-Grammatik — H-15 Mess-Gate (KAPITALFREI)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}`")
    L.append(f"- **Modus:** {payload['mode']} · **ran_on_gpu:** "
             f"{'ja' if payload['ran_on_gpu'] else 'NEIN'} · **gate_valid:** "
             f"{'ja' if payload['gate_valid'] else 'NEIN'}")
    if payload["gate_valid_reasons"]:
        for r in payload["gate_valid_reasons"]:
            L.append(f"  - gate_valid-Grund: {r}")
    L.append(f"- **Raster:** {payload['data_start']}..{payload['data_end']} "
             f"({payload['n_days']} Tage) · Purged Walk-Forward "
             f"{payload['n_folds']} Folds, {payload['embargo_days']}-Tag-Embargo, "
             f"Seeds {payload['seeds']}")
    mc = payload["model_config"]
    L.append(f"- **Transformer (vorab fixiert):** Decoder-only causal, "
             f"d_model={mc['d_model']}, layers={mc['n_layers']}, heads={mc['n_heads']}, "
             f"Kontext {mc['context_len']}, Vocab {payload['vocab_size']}")
    L.append(f"- **Baseline:** KT-geglaettetes Variable-Order-Markov k<=4 + "
             f"interpoliert (beste je Fold), GLEICHER Train-Fold")
    L.append(f"- **Null:** {payload['n_surrogates']} Within-Hour-of-Day-Block-Shuffle-"
             f"Surrogate (Blocklaenge {payload['surrogate_block_len_events']} Events)")
    L.append(f"- **FDR-Familie:** {payload['fdr_family']} ({len(payload['per_symbol'])} "
             f"Symbole) · **BH-FDR alpha:** {payload['fdr_alpha']} · "
             f"**p_crit:** {_fmt(payload['fdr_p_crit'])}")
    L.append("- **KAPITALFREI:** ja — reine Existence-of-Structure-Messung, "
             "keine Kapital-Metriken.")
    L.append("")
    L.append("> Gate-Urteil faellt der gate-auditor gegen H-15. WEITER verlangt: "
             "OOS-Token-CE des Transformers >=2% relativ niedriger als die beste "
             "Markov-k-(k<=4)-Baseline bei >=4/5 Symbolen UND CE-Luecke ueber dem "
             "95. Perzentil der Surrogat-Luecken-Verteilung, nach BH-FDR alpha=0.10 "
             "ueber F-GRAMMAR. Hartes Kriterium, kein GRAUBEREICH, kein Vocab-/"
             "Kontext-/Architektur-Nachjustieren.")
    L.append("")
    L.append("## Differenzierung zum gesperrten Informationstheorie-Cluster (Pflicht)")
    L.append("")
    L.append(f"> {payload['differentiation_note']}")
    L.append("")
    L.append("## F-GRAMMAR je Symbol (Gate-Kern)")
    L.append("")
    L.append("| Symbol | Markov-CE (beste) | Transformer-CE | rel. Luecke | >=2%? | "
             "Surrogat-p95 | Luecke>p95? | p | FDR-sig | Symbol besteht |")
    L.append("|---|---:|---:|---:|:---:|---:|:---:|---:|:---:|:---:|")
    for s in payload["per_symbol"]:
        L.append(
            f"| {s['symbol']} | {_fmt(s['best_markov_ce'])} | "
            f"{_fmt(s['transformer_ce'])} | {_fmt(s['relative_ce_gap'])} | "
            f"{'ja' if s['rel_gap_threshold_met'] else 'nein'} | "
            f"{_fmt(s['surrogate_gap_p95'], 5)} | "
            f"{'ja' if s['gap_above_surrogate_p95'] else 'nein'} | "
            f"{_fmt(s['surrogate_p'])} | "
            f"{'ja' if s['fdr_significant'] else 'nein'} | "
            f"{'JA' if s['symbol_pass'] else 'nein'} |")
    L.append("")
    L.append(f"**Symbole bestehen:** {payload['n_symbols_pass']} von "
             f"{len(payload['per_symbol'])} · **>=4/5 (gate-neutral):** "
             f"{'JA' if payload['family_pass_geq_4of5'] else 'nein'}")
    L.append("")
    L.append("## Fold-Detail")
    for s in payload["per_symbol"]:
        L.append("")
        L.append(f"### {s['symbol']}")
        L.append("")
        L.append("| Fold | Train-Events | Test-Events | beste Baseline | Markov-CE | "
                 "Transformer-CE (Seeds) | Luecke |")
        L.append("|---:|---:|---:|---|---:|---|---:|")
        for fr in s["folds"]:
            seeds_str = ", ".join(_fmt(c) for c in fr["transformer_ces_per_seed"]) or "n/a"
            L.append(
                f"| {fr['fold']} | {fr['n_train_events']} | {fr['n_test_events']} | "
                f"{fr['best_markov_name'] or 'n/a'} | {_fmt(fr['best_markov_ce'])} | "
                f"{seeds_str} | {_fmt(fr['observed_gap'], 5)} |")
    L.append("")
    L.append("*Erzeugt von `c15_grammar/driver.py` (read-only Harvester-Baum). "
             "capital_free=true. Endgueltiges Gate-Urteil: gate-auditor gegen H-15.*")
    return "\n".join(L)


__all__ = [
    "DEFAULT_DATA_END",
    "DEFAULT_DATA_START",
    "DEFAULT_SEEDS",
    "DEFAULT_SYMBOLS",
    "DIFFERENTIATION_NOTE",
    "DataError",
    "EventStream",
    "HYPOTHESIS_ID",
    "REGISTRY_PATH",
    "SCHEMA_VERSION",
    "daily_grid",
    "load_trade_events",
    "prepare_fold",
    "render_markdown",
    "run",
]
