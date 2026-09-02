"""
Trainings-Skript für M1/M18/M19/M20.

CLI:
    python scripts/train_models.py --module patchtst --epochs 20 \
        --symbol BTCUSDT --interval 5 --months 6 --device auto

    python scripts/train_models.py --module all --epochs 20 \
        --batch-size 32 --device cuda

Speichert Checkpoints nach ``data/models/{module}_{symbol}_{interval}.pt``.
Loggt VRAM-Auslastung wenn CUDA aktiv ist.

VRAM-Reihenfolge bei ``--module all``:
    patchtst (~10 MB)  ->  timesnet (~5 MB)  ->  moment-base+LoRA
        (-> ~10 GB im echten Fine-Tune) -> spikewav (~3 MB).
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from bybit_edge.config import (
    M1_WEIGHTS_PATH,
    M18_WEIGHTS_PATH,
    M19_WEIGHTS_PATH,
    M20_WEIGHTS_PATH,
    MODELS_DIR,
    PRIMARY_SYMBOL,
    TRAIN_DEFAULT_BATCH_SIZE,
    TRAIN_DEFAULT_EPOCHS,
    TRAIN_DEFAULT_HORIZON,
    TRAIN_DEFAULT_LOOKBACK,
    TRAIN_DEFAULT_LR,
    TRAIN_VAL_FRACTION,
)
from bybit_edge.layers.l1_ingestion.m1_spikewavformer import M1SpikeWavformer
from bybit_edge.layers.l4_pattern.m18_patchtst import M18PatchTST
from bybit_edge.layers.l4_pattern.m19_timesnet import M19TimesNet
from bybit_edge.layers.l4_pattern.m20_moment import M20MOMENT
from bybit_edge.training.dataset import (
    KlineDataset,
    TickDataset,
    chronological_split,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
LOG = logging.getLogger("train_models")


# ══════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════


def _try_torch():
    try:
        import torch

        return torch
    except Exception:
        return None


def _log_gpu_mem(prefix: str = "") -> None:
    t = _try_torch()
    if t is None or not t.cuda.is_available():
        return
    alloc = t.cuda.memory_allocated() / 1024 ** 3
    reserved = t.cuda.memory_reserved() / 1024 ** 3
    LOG.info("[GPU] %s alloc=%.2f GB reserved=%.2f GB", prefix, alloc, reserved)


def _load_kline_series(symbol: str, interval: str, months: int) -> np.ndarray:
    """Lade die Close-Preis-Reihe via REST-Backfill (cached)."""
    from scripts.backtest import backfill_klines

    df = backfill_klines(symbol, interval, months)
    return np.asarray(df["close"].to_numpy(), dtype=np.float64)


def _normalize_per_sample(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Apply RevIN per sample to X and y (gemeinsame mu/sigma aus X)."""
    eps = 1e-6
    mu = X.mean(axis=1, keepdims=True)
    sigma = X.std(axis=1, keepdims=True) + eps
    return (X - mu) / sigma, (y - mu) / sigma


# ══════════════════════════════════════════════════════════════════════
# Trainings-Funktionen pro Modul
# ══════════════════════════════════════════════════════════════════════


def train_patchtst(args: argparse.Namespace) -> dict[str, Any]:
    LOG.info("Training M18 PatchTST ...")
    series = _load_kline_series(args.symbol, args.interval, args.months)
    LOG.info("  Klines geladen: %d Bars", len(series))

    from bybit_edge.training.dataset import build_windows

    X, y = build_windows(series, args.lookback, args.horizon)
    if len(X) < 50:
        LOG.warning("Zu wenig Trainings-Samples (%d).", len(X))
        return {"status": "skip"}

    X_n, y_n = _normalize_per_sample(X, y)
    X_tr, X_va, y_tr, y_va = chronological_split(X_n, y_n, TRAIN_VAL_FRACTION)

    model = M18PatchTST(
        lookback=args.lookback,
        forecast_horizon=args.horizon,
        device=args.device,
    )
    LOG.info("  Params: %d   device=%s", model.num_parameters(), model.device)

    _log_gpu_mem("M18 vor fit")
    result = model.fit(
        X_tr,
        y_tr,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        val_data=X_va,
        val_targets=y_va,
        verbose=True,
    )
    _log_gpu_mem("M18 nach fit")

    out_path = MODELS_DIR / f"m18_patchtst_{args.symbol}_{args.interval}.pt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(out_path))
    LOG.info("M18 gespeichert -> %s  (train_mse=%.6f)", out_path, result["train_mse"])
    return {"status": "ok", "path": str(out_path), **result}


def train_timesnet(args: argparse.Namespace) -> dict[str, Any]:
    LOG.info("Training M19 TimesNet ...")
    series = _load_kline_series(args.symbol, args.interval, args.months)
    LOG.info("  Klines geladen: %d Bars", len(series))

    from bybit_edge.training.dataset import build_windows

    X, y = build_windows(series, args.lookback, args.horizon)
    if len(X) < 50:
        LOG.warning("Zu wenig Trainings-Samples (%d).", len(X))
        return {"status": "skip"}
    X_n, y_n = _normalize_per_sample(X, y)
    X_tr, X_va, y_tr, y_va = chronological_split(X_n, y_n, TRAIN_VAL_FRACTION)

    model = M19TimesNet(
        lookback=args.lookback,
        forecast_horizon=args.horizon,
        device=args.device,
    )
    LOG.info("  Params: %d   device=%s", model.num_parameters(), model.device)

    _log_gpu_mem("M19 vor fit")
    result = model.fit(
        X_tr,
        y_tr,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        verbose=True,
    )
    _log_gpu_mem("M19 nach fit")

    out_path = MODELS_DIR / f"m19_timesnet_{args.symbol}_{args.interval}.pt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(out_path))
    LOG.info("M19 gespeichert -> %s  (train_mse=%.6f)", out_path, result["train_mse"])
    return {"status": "ok", "path": str(out_path), **result}


def train_moment(args: argparse.Namespace) -> dict[str, Any]:
    LOG.info("Training/Loading M20 MOMENT ...")
    model = M20MOMENT(forecast_horizon=args.horizon, device=args.device)
    repo = "AutonLab/MOMENT-1-base"
    ok = model.load_pretrained(repo, model_size="base")
    if not ok:
        LOG.warning(
            "MOMENT-Pretrained nicht ladbar (momentfm fehlt?). "
            "Fallback bleibt aktiv — kein Speicher-Schritt."
        )
        return {"status": "skip"}

    LOG.info("MOMENT geladen (zero-shot ready).")

    if args.lora and getattr(model, "_moment_model", None) is not None:
        ok = model.enable_lora()
        if ok:
            LOG.info("LoRA aktiv — Fine-Tune möglich.")
            # Lightweight Fine-Tune-Pass auf Klines würde hier folgen.
            # Beispiel-Stub: nur Adapter speichern.
            out = MODELS_DIR / f"m20_moment_{args.symbol}_{args.interval}.pt"
            out.parent.mkdir(parents=True, exist_ok=True)
            model.save(str(out))
            LOG.info("MOMENT-LoRA-Adapter -> %s", out)
            return {"status": "ok", "path": str(out)}
        else:
            LOG.warning("LoRA nicht möglich — peft fehlt?")
    return {"status": "loaded"}


def train_spikewav(args: argparse.Namespace) -> dict[str, Any]:
    LOG.info("Training M1 SpikeWavformer ...")
    try:
        ds = TickDataset(
            db_path=Path("data") / "bybit_edge.duckdb",
            lookback_ticks=256,
            horizon_ticks=60,
        )
    except RuntimeError as exc:
        LOG.warning("M1 Skip: %s", exc)
        return {"status": "skip", "reason": str(exc)}

    # Flatten Channels → in_features
    X = ds._X.reshape(len(ds), -1).astype(np.float32)
    y = ds._y.astype(np.int64)

    n_train = int(len(X) * (1.0 - TRAIN_VAL_FRACTION))
    X_tr, y_tr = X[:n_train], y[:n_train]
    in_features = X.shape[1]

    model = M1SpikeWavformer(device=args.device)
    LOG.info("  Params: %d   device=%s", model.num_parameters(), model.device)
    LOG.info("  Hinweis: in_features=%d — passe ggf. Channel-Layer an.", in_features)

    _log_gpu_mem("M1 vor fit")
    result = model.fit(
        X_tr,
        y_tr,
        epochs=args.epochs,
        batch_size=min(args.batch_size, 16),
        lr=args.lr,
        verbose=True,
    )
    _log_gpu_mem("M1 nach fit")

    out_path = MODELS_DIR / f"m1_spikewav_{args.symbol}.pt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(out_path))
    LOG.info("M1 gespeichert -> %s", out_path)
    return {"status": "ok", "path": str(out_path), **result}


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════


_MODULES = ("patchtst", "timesnet", "moment", "spikewav", "all")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train Bybit Edge ML modules")
    p.add_argument("--module", choices=_MODULES, required=True)
    p.add_argument("--symbol", default=PRIMARY_SYMBOL)
    p.add_argument("--interval", default="5", help="Kline-Intervall (1, 5, 15 ...)")
    p.add_argument("--months", type=int, default=6)
    p.add_argument("--epochs", type=int, default=TRAIN_DEFAULT_EPOCHS)
    p.add_argument("--batch-size", type=int, default=TRAIN_DEFAULT_BATCH_SIZE)
    p.add_argument("--lookback", type=int, default=TRAIN_DEFAULT_LOOKBACK)
    p.add_argument("--horizon", type=int, default=TRAIN_DEFAULT_HORIZON)
    p.add_argument("--lr", type=float, default=TRAIN_DEFAULT_LR)
    p.add_argument("--device", choices=("auto", "cuda", "cpu"), default="auto")
    p.add_argument("--lora", action="store_true", help="MOMENT LoRA aktivieren")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    t0 = time.time()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    LOG.info("Models-Dir: %s", MODELS_DIR.resolve())

    if args.module == "all":
        # Reihenfolge VRAM-aware: leichte erst, dann MOMENT
        for sub in ("patchtst", "timesnet", "moment", "spikewav"):
            args.module = sub
            _run_single(args)
    else:
        _run_single(args)

    LOG.info("Fertig nach %.1fs", time.time() - t0)
    return 0


def _run_single(args: argparse.Namespace) -> None:
    mod = args.module
    if mod == "patchtst":
        train_patchtst(args)
    elif mod == "timesnet":
        train_timesnet(args)
    elif mod == "moment":
        train_moment(args)
    elif mod == "spikewav":
        train_spikewav(args)


if __name__ == "__main__":
    sys.exit(main())
