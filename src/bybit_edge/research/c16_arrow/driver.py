"""H-16 orchestration: data, day split, C2ST trainings, controls, F-ARROW rollup.

Pipeline per symbol (registry H-16, pre-fixed):
  1. 1 s signed trade-imbalance series (buy minus sell taker volume) per UTC
     day from the read-only Bybit ``publicTrade`` harvester tree.
  2. Held-out-day split — CHRONOLOGICAL, day-level (documented split
     procedure, see :func:`split_days_chronological`): the LAST 20% of valid
     days (rounded, >= 1) are the held-out test days, all earlier valid days
     train. No W1/W2; windows never cross day boundaries, so no further
     purging is needed.
  3. Main C2ST: ResNet-18 classifies FORWARD vs TIME-REVERSED Morlet-CWT
     log-power scalograms (reversal on the RAW series BEFORE the CWT);
     ``n_seeds`` = 5 full trainings; gate statistic = seed-median held-out
     AUC; per-symbol p-value = exact paired sign test of the median-AUC seed
     (operationalisation fixed here, before any run).
  4. Mandatory control (a), pipeline-leak: ``n_surrogates`` = 20 FULL
     retrainings on day-wise IAAFT surrogates. leak_auc := MEAN of the 20
     surrogate held-out AUCs (must stay <= 0.52, else METHODICALLY INVALID,
     no verdict); surrogate_p95 := 95th percentile (must stay < 0.53).
     Both operationalisations fixed here before any run.
  5. Mandatory control (b), volatility-asymmetry ablation: identical
     pipeline on |imbalance| (unsigned), ``ablation_seeds`` trainings,
     report-only (non-verdict-bearing, registry).

Compute gating (binding): a verdict-bearing run REQUIRES torch + a real
CUDA device (``cnn.gpu_status()["verdict_capable"]``). Without it
:func:`run` raises :class:`cnn.ComputeError` (CLI exit 2 = SKIP) unless
``allow_cpu=True`` is passed explicitly — and then the payload is stamped
``verdict_bearing = False`` and may NEVER be adjudicated. On the GPU the
torch scalogram path is cross-checked against the numpy reference at run
start (:func:`scalogram.verify_torch_parity`) before anything trains.

DIFFERENTIATION (registry-mandated, verbatim below in
``DIFFERENTIATION_NOTE``): this is NOT a duplicate of the locked
information-theory / nonlinear-dynamics cluster.

KAPITALFREI: pure structure/existence question, no cost/return accounting.
Read-only harvester access (Schutzgut). Reports in German (repo convention).
"""
from __future__ import annotations

import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .cnn import (
    BATCH_SIZE_DEFAULT,
    ComputeError,
    EPOCHS_DEFAULT,
    LR_DEFAULT,
    gpu_status,
    train_forward_reverse_classifier,
)
from .iaaft import iaaft
from .scalogram import (
    MORLET_OMEGA0,
    N_SCALES,
    PERIOD_MAX_S,
    PERIOD_MIN_S,
    STRIDE_S,
    WINDOW_S,
    extract_windows,
    verify_torch_parity,
)
from .stats import (
    AUC_MIN,
    FDR_ALPHA,
    LEAK_AUC_MAX,
    N_SYMBOLS_MIN,
    SURROGATE_P95_MAX,
    evaluate_gate,
    sentinel_cell,
    surrogate_percentile_95,
)

SCHEMA_VERSION = 1
HYPOTHESIS_ID = "H-16"
FDR_FAMILY = "F-ARROW"
REGISTRY_PATH = "scinance2-impl/state/hypothesis_registry.md"

#: Registered 5-symbol Bybit perp set (Welle-5 convention, run_wave4 order).
SYMBOLS_DEFAULT: tuple[str, ...] = (
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
)
#: Registered data binding start (Basis-Bestand 2026-03-27..Cutoff).
BASE_START_DATE = "2026-03-27"

#: Seconds per UTC day (the 1 s analysis grid).
SECONDS_PER_DAY = 86_400
#: Data-hygiene floor (builder-fixed BEFORE any run, documented in
#: README_H16): a day is VALID iff >= 10% of its seconds saw >= 1 trade.
#: This is a data-quality parameter, not a gate parameter.
MIN_ACTIVE_SECONDS_FRAC = 0.10
#: Minimum number of valid days for a measurable symbol cell (>= 2 train +
#: >= 1 held-out day would be degenerate; require a sane floor).
MIN_VALID_DAYS = 10
#: Held-out fraction of the chronological day split.
TEST_DAY_FRAC = 0.20

#: Registered run sizes (registry H-16: ~145 trainings on the RTX card).
N_SEEDS_DEFAULT = 5
N_SURROGATES_DEFAULT = 20
ABLATION_SEEDS_DEFAULT = 3

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SYMBOL_RE = re.compile(r"^[A-Za-z0-9_\-]+$")

#: Registry-mandated differentiation paragraph (verbatim duty: README/Runner
#: MUST carry this to rule out confusion with the locked cluster).
DIFFERENTIATION_NOTE = (
    "KEIN Duplikat des gesperrten Informationstheorie-/Nichtlineare-Dynamik-"
    "Clusters (PE/TE/RQA/MFDFA/TDA, H-04/H-06-Linie): H-16 verwendet NIRGENDS "
    "einen Entropie-Schaetzer; gemessen wird eine ANDERE Eigenschaft — "
    "Zeit-IRREVERSIBILITAET (richtungsabhaengige Asymmetrie des Prozessgesetzes "
    "unter Zeitumkehr t -> -t) statt Komplexitaet/Vorhersagbarkeit; und die "
    "Null ist die EXAKTE Bayes-optimale AUC = 0,5 des Classifier-Two-Sample-"
    "Tests (Lopez-Paz & Oquab 2017) fuer reversible Prozesse — ein exakter, "
    "vorab spezifizierbarer Wert, KEIN geschaetzter Schwellenwert aus einer "
    "surrogat-kalibrierten Entropie-Statistik."
)


class DataError(RuntimeError):
    """Raised when a harvester window cannot be loaded for a symbol."""


# ----------------------------------------------------------------------------
# Data loading (read-only harvester tree)
# ----------------------------------------------------------------------------


def list_available_dates(
    base_dir: Path | str,
    symbol: str,
    start_date: str,
    end_date: str,
    *,
    exchange: str = "bybit",
    stream: str = "publicTrade",
) -> list[str]:
    """Sorted ``YYYY-MM-DD`` partitions with parquet inside [start, end]."""
    for s in (start_date, end_date):
        if not _DATE_RE.match(s):
            raise DataError(f"invalid date (want YYYY-MM-DD): {s!r}")
    root = Path(base_dir) / "raw" / exchange / stream / f"symbol={symbol}"
    if not root.is_dir():
        return []
    out: list[str] = []
    for d in sorted(root.iterdir()):
        name = d.name
        if not name.startswith("date="):
            continue
        day = name[len("date="):]
        if not _DATE_RE.match(day) or not (start_date <= day <= end_date):
            continue
        if any(d.glob("*.parquet")):
            out.append(day)
    return out


def load_day_imbalance(
    base_dir: Path | str,
    symbol: str,
    day: str,
    *,
    exchange: str = "bybit",
    stream: str = "publicTrade",
) -> tuple[np.ndarray, int, int]:
    """1 s signed trade-imbalance series for one UTC day (read-only DuckDB).

    imbalance[t] = sum(taker-BUY size) - sum(taker-SELL size) over second
    ``t`` of the day; seconds without trades are 0 (no flow = zero
    imbalance — natural for a flow series, documented). Payload keys follow
    the c01_ofi_sign loader: backfill form ``side``/``size`` with live-form
    fallback ``S``/``v``. Returns ``(series[86400], n_active_seconds,
    n_trades)``. Never writes into the harvester tree (Schutzgut).
    """
    import duckdb

    if not _SYMBOL_RE.match(symbol):
        raise DataError(f"invalid symbol: {symbol!r}")
    if not _DATE_RE.match(day):
        raise DataError(f"invalid date (want YYYY-MM-DD): {day!r}")
    part = Path(base_dir) / "raw" / exchange / stream / f"symbol={symbol}" / f"date={day}"
    files = sorted(part.glob("*.parquet"))
    if not files:
        raise DataError(f"no parquet for {exchange}/{stream}/{symbol} date={day}")
    y, m, d = (int(x) for x in day.split("-"))
    day_ms = int(datetime(y, m, d, tzinfo=timezone.utc).timestamp() * 1000)
    file_list = "[" + ", ".join("'" + str(f).replace("'", "''") + "'" for f in files) + "]"
    sql = f"""
        WITH t AS (
            SELECT (ts_exchange_ms - {day_ms}) // 1000 AS sec,
                   lower(COALESCE(json_extract_string(payload_json,'$.side'),
                                  json_extract_string(payload_json,'$.S'))) AS side,
                   CAST(COALESCE(json_extract_string(payload_json,'$.size'),
                                 json_extract_string(payload_json,'$.v')) AS DOUBLE) AS vol
            FROM read_parquet({file_list}, hive_partitioning=1, union_by_name=1)
            WHERE ts_exchange_ms IS NOT NULL
              AND ts_exchange_ms >= {day_ms}
              AND ts_exchange_ms < {day_ms + SECONDS_PER_DAY * 1000}
        )
        SELECT CAST(sec AS BIGINT) AS sec,
               SUM(CASE WHEN side = 'buy' THEN vol ELSE -vol END) AS imb,
               COUNT(*) AS n_trades
        FROM t
        WHERE side IN ('buy', 'sell') AND vol IS NOT NULL AND isfinite(vol)
        GROUP BY 1
        ORDER BY 1
    """
    con = duckdb.connect()
    try:
        rows = con.execute(sql).fetchall()
    finally:
        con.close()
    series = np.zeros(SECONDS_PER_DAY, dtype=np.float64)
    n_active = 0
    n_trades = 0
    for sec, imb, n in rows:
        s = int(sec)
        if 0 <= s < SECONDS_PER_DAY and imb is not None and math.isfinite(imb):
            series[s] = float(imb)
            n_active += 1
            n_trades += int(n)
    return series, n_active, n_trades


def load_symbol_days(
    base_dir: Path | str,
    symbol: str,
    start_date: str,
    end_date: str,
    *,
    max_days: int | None = None,
) -> tuple[list[str], dict[str, np.ndarray], dict[str, Any]]:
    """All VALID days with their 1 s imbalance series for one symbol.

    A day is valid iff ``n_active_seconds >= MIN_ACTIVE_SECONDS_FRAC *
    86400`` (data hygiene, fixed above). ``max_days`` (smoke runs only,
    stamps the payload non-verdict-bearing) keeps the LAST ``max_days``
    valid days.
    """
    dates = list_available_dates(base_dir, symbol, start_date, end_date)
    if not dates:
        raise DataError(
            f"no parquet days for {symbol} in {start_date}..{end_date} under {base_dir}"
        )
    valid_days: list[str] = []
    series_by_day: dict[str, np.ndarray] = {}
    n_invalid = 0
    min_active = int(MIN_ACTIVE_SECONDS_FRAC * SECONDS_PER_DAY)
    for day in dates:
        series, n_active, n_trades = load_day_imbalance(base_dir, symbol, day)
        if n_active < min_active:
            n_invalid += 1
            print(f"[c16] {symbol} {day}: INVALID ({n_active}/{SECONDS_PER_DAY} "
                  f"active seconds < {min_active})", file=sys.stderr, flush=True)
            continue
        valid_days.append(day)
        series_by_day[day] = series
    if max_days is not None and len(valid_days) > max_days:
        dropped = valid_days[:-max_days]
        valid_days = valid_days[-max_days:]
        for day in dropped:
            series_by_day.pop(day, None)
    info = {
        "n_days_scanned": len(dates),
        "n_days_valid": len(valid_days),
        "n_days_invalid": n_invalid,
        "min_active_seconds": min_active,
        "first_day": valid_days[0] if valid_days else None,
        "last_day": valid_days[-1] if valid_days else None,
    }
    return valid_days, series_by_day, info


# ----------------------------------------------------------------------------
# Day split + windowing
# ----------------------------------------------------------------------------


def split_days_chronological(
    days: list[str], test_frac: float = TEST_DAY_FRAC
) -> tuple[list[str], list[str]]:
    """THE registered held-out-day split procedure (documented, binding).

    Days sorted chronologically; the LAST ``round(test_frac * n)`` days
    (at least 1) are the held-out TEST days, all earlier days TRAIN. Purely
    deterministic — no shuffle, no discretion. Windows never cross a day
    boundary (built per day), so train and test never share a second of
    data; day-level separation is the registered unit (no W1/W2).
    """
    days = sorted(days)
    n = len(days)
    if n < 2:
        raise DataError(f"need >= 2 valid days for a day-level split, got {n}")
    n_test = max(1, int(round(test_frac * n)))
    n_test = min(n_test, n - 1)  # keep >= 1 train day
    return days[:n - n_test], days[n - n_test:]


def windows_for_days(
    series_by_day: dict[str, np.ndarray],
    days: list[str],
    *,
    unsigned: bool = False,
) -> np.ndarray:
    """Stacked ``(N, WINDOW_S)`` float32 raw windows over the given days.

    ``unsigned=True`` applies ``abs`` to the RAW day series first
    (volatility-asymmetry ablation, registry control (b)).
    """
    parts: list[np.ndarray] = []
    for day in days:
        s = series_by_day[day]
        if unsigned:
            s = np.abs(s)
        w = extract_windows(s, WINDOW_S, STRIDE_S)
        if w.shape[0]:
            parts.append(w)
    if not parts:
        return np.zeros((0, WINDOW_S), dtype=np.float32)
    return np.concatenate(parts).astype(np.float32)


def surrogate_series_by_day(
    series_by_day: dict[str, np.ndarray],
    days: list[str],
    *,
    seed: int,
    symbol_index: int,
    surrogate_index: int,
) -> dict[str, np.ndarray]:
    """Day-wise IAAFT surrogates of the raw series (deterministic seeding).

    Each UTC day is surrogated INDEPENDENTLY (the day is the analysis unit;
    windows never cross days). rng per day from
    ``SeedSequence([seed, symbol_index, surrogate_index, day_index])``.
    """
    out: dict[str, np.ndarray] = {}
    for di, day in enumerate(days):
        rng = np.random.default_rng(
            np.random.SeedSequence([seed, symbol_index, surrogate_index, di])
        )
        out[day], _info = iaaft(series_by_day[day], rng)
    return out


# ----------------------------------------------------------------------------
# Compute gate
# ----------------------------------------------------------------------------


def check_gpu() -> dict[str, Any]:
    """Compute-gate report for ``--check-gpu-only`` (honest, never guesses)."""
    status = gpu_status()
    status["hypothesis"] = HYPOTHESIS_ID
    status["note"] = (
        "verdict_capable=True erfordert torch UND ein echtes CUDA-Device. "
        "Ein voller Lauf ohne CUDA ist NIEMALS verdikt-tragend (Registry "
        "H-16: GPU zwingend, ~145 CNN-Trainings)."
    )
    return status


# ----------------------------------------------------------------------------
# Per-symbol measurement
# ----------------------------------------------------------------------------


def _median_seed_result(results: list[dict[str, Any]]) -> tuple[float, dict[str, Any]]:
    """Seed-median AUC and the result of the median-AUC seed (fixed rule).

    For even counts the LOWER median seed is taken for the p-value
    (deterministic); the reported ``auc`` is the true median of the AUCs.
    """
    aucs = np.asarray([r["auc"] for r in results], dtype=np.float64)
    order = np.argsort(aucs, kind="stable")
    med_idx = int(order[(len(results) - 1) // 2])
    return float(np.median(aucs)), results[med_idx]


def measure_symbol(
    base_dir: Path | str,
    symbol: str,
    symbol_index: int,
    *,
    start_date: str,
    end_date: str,
    n_seeds: int,
    n_surrogates: int,
    ablation_seeds: int,
    seed: int,
    device: str,
    epochs: int,
    batch_size: int,
    lr: float,
    max_days: int | None,
) -> dict[str, Any]:
    """One F-ARROW cell: main C2ST + both mandatory controls for one symbol."""
    days, series_by_day, day_info = load_symbol_days(
        base_dir, symbol, start_date, end_date, max_days=max_days
    )
    if len(days) < MIN_VALID_DAYS:
        raise DataError(
            f"{symbol}: only {len(days)} valid days (< {MIN_VALID_DAYS}) in "
            f"{start_date}..{end_date}"
        )
    train_days, test_days = split_days_chronological(days)
    xtr = windows_for_days(series_by_day, train_days)
    xte = windows_for_days(series_by_day, test_days)
    print(f"[c16] {symbol}: {len(train_days)} train days / {len(test_days)} "
          f"held-out days -> {xtr.shape[0]} train / {xte.shape[0]} test windows",
          file=sys.stderr, flush=True)

    # --- main C2ST: n_seeds full trainings -------------------------------
    seed_results: list[dict[str, Any]] = []
    for si in range(n_seeds):
        res = train_forward_reverse_classifier(
            xtr, xte, seed=seed + 1000 * symbol_index + si, device=device,
            epochs=epochs, batch_size=batch_size, lr=lr,
        )
        print(f"[c16] {symbol} seed {si + 1}/{n_seeds}: auc={res['auc']:.4f} "
              f"p_sign={res['p_value_sign_test']:.3e}", file=sys.stderr, flush=True)
        seed_results.append(res)
    auc_median, median_res = _median_seed_result(seed_results)

    # --- control (a): pipeline-leak / surrogate null (full retrainings) ---
    surrogate_aucs: list[float] = []
    for gi in range(n_surrogates):
        sur = surrogate_series_by_day(
            series_by_day, days, seed=seed, symbol_index=symbol_index,
            surrogate_index=gi,
        )
        res = train_forward_reverse_classifier(
            windows_for_days(sur, train_days),
            windows_for_days(sur, test_days),
            seed=seed + 1000 * symbol_index + 100 + gi, device=device,
            epochs=epochs, batch_size=batch_size, lr=lr,
        )
        print(f"[c16] {symbol} surrogate {gi + 1}/{n_surrogates}: "
              f"auc={res['auc']:.4f}", file=sys.stderr, flush=True)
        surrogate_aucs.append(float(res["auc"]))
    leak_auc = float(np.mean(surrogate_aucs)) if surrogate_aucs else float("nan")
    p95 = surrogate_percentile_95(surrogate_aucs)

    # --- control (b): volatility-asymmetry ablation on |imbalance| --------
    xtr_u = windows_for_days(series_by_day, train_days, unsigned=True)
    xte_u = windows_for_days(series_by_day, test_days, unsigned=True)
    ablation_aucs: list[float] = []
    for si in range(ablation_seeds):
        res = train_forward_reverse_classifier(
            xtr_u, xte_u, seed=seed + 1000 * symbol_index + 500 + si,
            device=device, epochs=epochs, batch_size=batch_size, lr=lr,
        )
        print(f"[c16] {symbol} ablation seed {si + 1}/{ablation_seeds}: "
              f"auc={res['auc']:.4f}", file=sys.stderr, flush=True)
        ablation_aucs.append(float(res["auc"]))

    return {
        "symbol": symbol,
        "measured": True,
        "days": day_info,
        "train_days": train_days,
        "test_days": test_days,
        "n_train_windows": int(xtr.shape[0]),
        "n_test_windows": int(xte.shape[0]),
        "auc_seeds": [float(r["auc"]) for r in seed_results],
        "auc": auc_median,
        "p_value": float(median_res["p_value_sign_test"]),
        "p_value_sign_counts": median_res["sign_counts"],
        "surrogate_aucs": surrogate_aucs,
        "surrogate_p95": p95,
        "leak_auc": leak_auc,
        "ablation_auc_seeds": ablation_aucs,
        "ablation_auc_unsigned": (
            float(np.median(ablation_aucs)) if ablation_aucs else float("nan")
        ),
    }


# ----------------------------------------------------------------------------
# Full run
# ----------------------------------------------------------------------------


def run(
    base_dir: Path | str,
    symbols: tuple[str, ...] = SYMBOLS_DEFAULT,
    *,
    start_date: str = BASE_START_DATE,
    end_date: str,
    n_seeds: int = N_SEEDS_DEFAULT,
    n_surrogates: int = N_SURROGATES_DEFAULT,
    ablation_seeds: int = ABLATION_SEEDS_DEFAULT,
    seed: int = 42,
    device: str = "cuda",
    allow_cpu: bool = False,
    epochs: int = EPOCHS_DEFAULT,
    batch_size: int = BATCH_SIZE_DEFAULT,
    lr: float = LR_DEFAULT,
    max_days: int | None = None,
    source: str = "",
) -> dict[str, Any]:
    """Full H-16 run over the F-ARROW family. Gate-neutral payload.

    Raises :class:`ComputeError` when the compute gate fails (no torch /
    no CUDA) and ``allow_cpu`` is False — the CLI maps that to exit 2
    (SKIP), so a missing GPU can never silently produce a verdict-shaped
    payload. With ``allow_cpu=True`` (explicit smoke escape hatch) or with
    ``max_days`` set the payload is stamped ``verdict_bearing = False``.
    """
    compute = check_gpu()
    if not compute["torch_available"]:
        raise ComputeError(
            "H-16 full run needs torch (not installed here). "
            "Use --check-gpu-only for the honest compute report."
        )
    if not compute["verdict_capable"] and not allow_cpu:
        raise ComputeError(
            "H-16 full run needs a real CUDA device (registry: GPU zwingend, "
            "~145 CNN-Trainings). Pass --allow-cpu ONLY for a non-verdict "
            "smoke run."
        )
    if device == "cuda" and not compute["cuda_available"]:
        device = "cpu"  # only reachable with allow_cpu=True

    verdict_bearing = bool(compute["verdict_capable"]) and device.startswith("cuda")
    non_verdict_reasons: list[str] = []
    if not verdict_bearing:
        non_verdict_reasons.append("kein CUDA-Device (CPU-Smoke, --allow-cpu)")
    if max_days is not None:
        verdict_bearing = False
        non_verdict_reasons.append(
            f"max_days={max_days} verletzt die registrierte Datenbindung "
            f"(Basis-Bestand {BASE_START_DATE}..Cutoff) — nur Smoke"
        )

    parity = verify_torch_parity(device=device)
    print(f"[c16] torch/numpy scalogram parity: {parity}", file=sys.stderr, flush=True)

    cells: list[dict[str, Any]] = []
    cell_errors: list[dict[str, str]] = []
    for symbol_index, symbol in enumerate(symbols):
        try:
            cells.append(measure_symbol(
                base_dir, symbol, symbol_index,
                start_date=start_date, end_date=end_date,
                n_seeds=n_seeds, n_surrogates=n_surrogates,
                ablation_seeds=ablation_seeds, seed=seed, device=device,
                epochs=epochs, batch_size=batch_size, lr=lr, max_days=max_days,
            ))
        except DataError as exc:
            print(f"[c16] {symbol} FAILED: {exc}", file=sys.stderr, flush=True)
            cell_errors.append({"symbol": symbol, "error": str(exc)})
            cells.append(sentinel_cell(symbol, str(exc)))

    gate = evaluate_gate(cells)
    if not verdict_bearing:
        # a non-verdict payload may never look adjudicable:
        gate["status"] = "NOT_VERDICT_BEARING"
        gate["status_note"] = (
            "Lauf NICHT verdikt-tragend: " + "; ".join(non_verdict_reasons)
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "hypothesis": HYPOTHESIS_ID,
        "hypothesis_registry": REGISTRY_PATH,
        "capital_free": True,
        "gpu_required": True,
        "verdict_bearing": verdict_bearing,
        "non_verdict_reasons": non_verdict_reasons,
        "compute": compute,
        "scalogram_parity_check": parity,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "symbols": list(symbols),
        "start_date": start_date,
        "end_date": end_date,
        "seed": int(seed),
        "n_seeds": int(n_seeds),
        "n_surrogates": int(n_surrogates),
        "ablation_seeds": int(ablation_seeds),
        "fdr_family": FDR_FAMILY,
        "fdr_alpha": FDR_ALPHA,
        "differentiation_note": DIFFERENTIATION_NOTE,
        "methodology": {
            "series": "1s signed trade imbalance (buy - sell taker volume), "
                      "bybit publicTrade",
            "window_s": WINDOW_S,
            "stride_s": STRIDE_S,
            "n_scales": N_SCALES,
            "period_min_s": PERIOD_MIN_S,
            "period_max_s": PERIOD_MAX_S,
            "morlet_omega0": MORLET_OMEGA0,
            "reversal": "auf der Roh-Serie VOR der CWT (scalogram_pair)",
            "padding": "reflect auf 2x Fensterlaenge, zentrale 512 Spalten; "
                       "COI-Diskussion in scalogram.py / README_H16",
            "cnn": "ResNet-18, Single-Channel, 1 Logit, BCE, AdamW, "
                   f"epochs={epochs}, batch={batch_size}, lr={lr}",
            "split": "chronologischer Day-Level-Split, letzte "
                     f"{int(TEST_DAY_FRAC * 100)}% der validen Tage held-out "
                     "(split_days_chronological)",
            "min_active_seconds_frac": MIN_ACTIVE_SECONDS_FRAC,
            "min_valid_days": MIN_VALID_DAYS,
            "p_value": "exakter gepaarter Sign-Test des Median-AUC-Seeds "
                       "gegen die exakte Bayes-Null AUC=0.5",
            "leak_auc": "MITTELWERT der Surrogat-Held-out-AUCs (<= "
                        f"{LEAK_AUC_MAX} Pflicht)",
            "surrogate_p95": "95. Perzentil (linear interpoliert) der "
                             f"Surrogat-AUCs (< {SURROGATE_P95_MAX} Pflicht)",
            "auc_min": AUC_MIN,
            "n_symbols_min": N_SYMBOLS_MIN,
            "iaaft": "Schreiber & Schmitz 1996, day-wise, Ende auf "
                     "Amplituden-Schritt (exakte Marginalverteilung)",
        },
        "cells": cells,
        "cell_errors": cell_errors,
        "gate": gate,
    }


# ----------------------------------------------------------------------------
# Report (German, repo convention)
# ----------------------------------------------------------------------------


def render_markdown(payload: dict[str, Any]) -> str:
    """German gate-neutral report for the morning evaluation."""
    L: list[str] = []
    L.append("# C-16 Time-Arrow-CNN — H-16 Mess-Gate (KAPITALFREI, GPU)")
    L.append("")
    L.append(f"- **Hypothese:** {payload['hypothesis']} — `{payload['hypothesis_registry']}`")
    L.append(f"- **Erzeugt:** {payload['generated_at']} (UTC)")
    L.append(f"- **Quelle:** `{payload['source']}` (Symbole: {', '.join(payload['symbols'])}, "
             f"{payload['start_date']}..{payload['end_date']})")
    m = payload["methodology"]
    L.append(f"- **Methodik (vorregistriert):** {m['series']}; Morlet-CWT-Log-Power-"
             f"Scalogram {m['n_scales']} Skalen {m['period_min_s']:.0f}s-"
             f"{m['period_max_s']:.0f}s x {m['window_s']} Zeit-Bins, Stride {m['stride_s']}s; "
             f"Reversal {m['reversal']}; {m['cnn']}; Split: {m['split']}; "
             f"Seeds {payload['n_seeds']}, Surrogate {payload['n_surrogates']}, Seed {payload['seed']}.")
    L.append(f"- **FDR-Familie:** {payload['fdr_family']} · BH-FDR alpha = {payload['fdr_alpha']}")
    L.append("- **KAPITALFREI:** ja — reine Struktur-/Existenzfrage, keine Kosten-/Ertragsrechnung.")
    L.append(f"- **Verdikt-tragend:** {'JA' if payload['verdict_bearing'] else 'NEIN'}"
             + ("" if payload["verdict_bearing"] else
                f" ({'; '.join(payload['non_verdict_reasons'])})"))
    L.append(f"- **Compute:** torch={payload['compute']['torch_available']} "
             f"cuda={payload['compute']['cuda_available']} "
             f"device={payload['compute']['device_name'] or '—'}")
    L.append("")
    L.append(f"- **Differenzierung (Registry-Pflicht):** {payload['differentiation_note']}")
    L.append("")
    L.append("## F-ARROW-Zellen (fixe 5er-Familie)")
    L.append("")
    L.append("| Symbol | AUC (Median) | p (Sign-Test) | FDR-sig | AUC>=0.60 | "
             "Surr-p95 (<0.53) | Leak-AUC (<=0.52) | Ablation \\|imb\\| | Symbol-Gate |")
    L.append("|---|---:|---:|:---:|:---:|---:|---:|---:|:---:|")
    for c in payload["cells"]:
        if not c.get("measured", True):
            L.append(f"| {c['symbol']} | — (Sentinel) | {c['p_value']:.4f} | nein | nein "
                     f"| — | — | — | nein |")
            continue
        L.append(
            f"| {c['symbol']} | {c['auc']:.4f} | {c['p_value']:.3e} | "
            f"{'ja' if c.get('fdr_significant') else 'nein'} | "
            f"{'ja' if c.get('auc_floor_met') else 'nein'} | "
            f"{c['surrogate_p95']:.4f} | {c['leak_auc']:.4f} | "
            f"{c['ablation_auc_unsigned']:.4f} | "
            f"{'JA' if c.get('symbol_gate_met') else 'nein'} |"
        )
    sentinels = [c for c in payload["cells"] if not c.get("measured", True)]
    if sentinels:
        L.append("")
        L.append("*Sentinel-Zellen (nicht gemessen, p=1.0, konservativ in der "
                 "fixen BH-Familie):*")
        for c in sentinels:
            L.append(f"- {c['symbol']}: {c.get('sentinel_reason', '')}")
    g = payload["gate"]
    L.append("")
    L.append("## Gate-Kern (gate-neutral — gate-auditor urteilt)")
    L.append("")
    L.append(f"- **Status:** `{g['status']}` — {g['status_note']}")
    L.append(f"- **BH-Familie (fix):** {g['family_size']} Zellen "
             f"({g['n_cells_measured']} gemessen, {g['n_cells_sentinel']} Sentinel) · "
             f"p_crit = {g['fdr_p_crit']:.4g} · FDR-signifikant: {g['n_fdr_significant']}")
    L.append(f"- **Symbol-Gates erfuellt:** {g['n_symbols_gate_met']} / {g['family_size']} "
             f"(Quorum >= {g['n_symbols_min']})")
    L.append(f"- **Leak-Kontrolle bestanden (alle gemessenen Symbole <= "
             f"{g['leak_auc_max']}):** {'ja' if g['leak_control_passed'] else 'NEIN'}")
    if g["method_invalid"]:
        L.append(f"- **METHODISCH INVALIDE — KEIN VERDIKT** (Symbole: "
                 f"{', '.join(g['method_invalid_symbols'])}). Dies ist ein eigener "
                 "Zustand, KEIN DROP: aus diesem Lauf darf in keiner Richtung "
                 "ein Verdikt abgeleitet werden.")
    L.append("")
    L.append("- **Ablation (nicht urteils-tragend, Pflicht-Report):** AUC auf "
             "|Imbalance| (unsigned) trennt Leverage-/Vol-Asymmetrie von "
             "Flow-Richtungs-Asymmetrie: bleibt die unsigned-AUC nahe 0.5, "
             "traegt die RICHTUNG des Flows die Zeitpfeil-Information; ist sie "
             "aehnlich hoch wie die signed-AUC, dominiert die Vol-Asymmetrie.")
    if payload.get("cell_errors"):
        L.append("")
        L.append("## Zell-Fehler")
        for e in payload["cell_errors"]:
            L.append(f"- {e['symbol']}: {e['error']}")
    L.append("")
    L.append("*Erzeugt von `c16_arrow/driver.py` (read-only Harvester-Baum). "
             "capital_free=true, gpu_required=true. WEITER verlangt (registriert, "
             "woertlich): Held-out-Day-Forward-vs-Reversed-AUC >= 0.60 MIT "
             "IAAFT-Surrogat-Null-95.-Perzentil < 0.53, bei >= 4/5 Symbolen nach "
             "BH-FDR alpha = 0.10 ueber F-ARROW, UND Leak-Kontrolle <= 0.52 "
             "(sonst methodisch invalide, KEIN Verdikt). DROP: AUC < 0.60 bei "
             "< 4/5 Symbolen. Kein Graubereich, keine nachtraegliche Skalen-/ "
             "Fenster-Anpassung. Endgueltiges Urteil: gate-auditor gegen H-16.*")
    return "\n".join(L)


__all__ = [
    "ABLATION_SEEDS_DEFAULT",
    "BASE_START_DATE",
    "DIFFERENTIATION_NOTE",
    "FDR_FAMILY",
    "HYPOTHESIS_ID",
    "MIN_ACTIVE_SECONDS_FRAC",
    "MIN_VALID_DAYS",
    "N_SEEDS_DEFAULT",
    "N_SURROGATES_DEFAULT",
    "SECONDS_PER_DAY",
    "SYMBOLS_DEFAULT",
    "TEST_DAY_FRAC",
    "ComputeError",
    "DataError",
    "check_gpu",
    "list_available_dates",
    "load_day_imbalance",
    "load_symbol_days",
    "measure_symbol",
    "render_markdown",
    "run",
    "split_days_chronological",
    "surrogate_series_by_day",
    "windows_for_days",
]
