# DEPRECATED (2026-06-23): Scinance-1.0-Legacy.
# Siehe scinance2-impl/state/CLEANUP_PLAN.md - Live-Pipeline gestoppt (TODO-2),
# Strategien S1-S5 sind empirisch DROP (WAVE1_FINAL_REPORT.md), Modul folgt der
# LiveRunner-Deprecation. Aufruf gilt als Anti-Pattern; Code bleibt nur als
# Audit-Trail im Repo. Reaktivierung ware eine neue, vorregistrierte Hypothese.

"""
Training-Datasets für M1/M18/M19/M20.

Designprinzipien
----------------
* Strikte Kausalität: Sliding-Window-Generator produziert (X, y) so, dass
  X strikt vor y liegt. Kein Random-Shuffle vor dem Split — der Split ist
  chronologisch.
* RevIN per Sample (Normalisierung pro Window, nicht global). Das
  entkoppelt Mean/Var und verhindert Train/Test-Leakage über
  Vollserien-Statistiken.
* Kein zwingender PyTorch-Import: das ``Dataset``-Interface wird nur
  exportiert wenn ``torch`` verfügbar ist. Die reinen Helper
  (``build_windows``, ``chronological_split``, RevIN) sind torch-frei.

Die Klassen können von dem Trainings-Script (``scripts/train_models.py``)
oder direkt im Test verwendet werden.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

_LOG = logging.getLogger(__name__)

try:
    import torch
    from torch.utils.data import Dataset

    _TORCH_AVAILABLE = True
except Exception:  # pragma: no cover
    torch = None  # type: ignore[assignment]
    Dataset = object  # type: ignore[assignment, misc]
    _TORCH_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# Reine Helper (torch-frei)
# ══════════════════════════════════════════════════════════════════════


def revin_normalize_sample(x: np.ndarray, eps: float = 1e-6) -> tuple[np.ndarray, float, float]:
    """RevIN auf einem einzelnen 1D-Sample."""
    mu = float(np.mean(x))
    sigma = float(np.std(x) + eps)
    return (x - mu) / sigma, mu, sigma


def revin_denormalize_sample(x: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    return x * sigma + mu


def build_windows(
    series: np.ndarray,
    lookback: int,
    horizon: int,
    stride: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Erzeuge (X, y) Sliding-Windows aus einer 1D-Serie.

    X[i] = series[t : t + lookback]
    y[i] = series[t + lookback : t + lookback + horizon]

    Strikt kausal: y ist immer NACH dem letzten X-Element.

    Returns
    -------
    (X, y) : shapes (n, lookback), (n, horizon)
    """
    series = np.asarray(series, dtype=np.float64)
    n_total = len(series)
    last_start = n_total - lookback - horizon
    if last_start < 0:
        return np.empty((0, lookback)), np.empty((0, horizon))
    starts = list(range(0, last_start + 1, stride))
    X = np.array([series[s : s + lookback] for s in starts])
    y = np.array(
        [series[s + lookback : s + lookback + horizon] for s in starts]
    )
    return X, y


def chronological_split(
    X: np.ndarray,
    y: np.ndarray,
    val_fraction: float = 0.2,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Chronologischer Train/Val-Split: erstes Stück = Train, letztes = Val.

    KEIN Random-Shuffle.
    """
    n = len(X)
    n_train = int(n * (1.0 - val_fraction))
    n_train = max(1, min(n_train, n - 1))
    return X[:n_train], X[n_train:], y[:n_train], y[n_train:]


# ══════════════════════════════════════════════════════════════════════
# KlineDataset (PyTorch)
# ══════════════════════════════════════════════════════════════════════


class KlineDataset(Dataset):
    """PyTorch-Dataset über REST-Backfill-Klines.

    Lädt Klines via ``scripts.backtest.backfill_klines`` (REST, paginiert,
    Cache als Parquet), baut Sliding-Window-Sequenzen, RevIN per Sample.

    Parameters
    ----------
    symbol : "BTCUSDT" etc.
    interval : "5" (5-Minuten-Klines).
    months : Anzahl Monate Historie.
    lookback : Länge des Input-Fensters.
    horizon : Länge des Forecast-Fensters.
    field : "close" | "open" | "high" | "low" | "volume"
    cached_klines : optional ein vorgeladener Polars-DataFrame
        (für Tests/Unit ohne Netzwerk).
    """

    def __init__(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "5",
        months: int = 6,
        lookback: int = 128,
        horizon: int = 12,
        field: str = "close",
        revin: bool = True,
        cached_klines: Any | None = None,
        cached_series: np.ndarray | None = None,
    ) -> None:
        if not _TORCH_AVAILABLE:
            raise RuntimeError("torch fehlt — KlineDataset benötigt PyTorch.")

        self.symbol = symbol
        self.interval = interval
        self.months = months
        self.lookback = lookback
        self.horizon = horizon
        self.field = field
        self.revin = revin

        if cached_series is not None:
            series = np.asarray(cached_series, dtype=np.float64)
        elif cached_klines is not None:
            series = np.asarray(cached_klines[field].to_numpy(), dtype=np.float64)
        else:
            series = self._load_series_from_rest()

        self._series = series
        self._X, self._y = build_windows(series, lookback, horizon, stride=1)

    def _load_series_from_rest(self) -> np.ndarray:
        from scripts.backtest import backfill_klines  # late import

        df = backfill_klines(self.symbol, self.interval, self.months)
        return np.asarray(df[self.field].to_numpy(), dtype=np.float64)

    # ------------------------------------------------------------------
    # Dataset protocol
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self._X.shape[0]

    def __getitem__(self, idx: int) -> tuple[Any, Any]:
        x = self._X[idx]
        y = self._y[idx]
        if self.revin:
            x_n, mu, sigma = revin_normalize_sample(x)
            y_n = (y - mu) / sigma
            x_out, y_out = x_n, y_n
        else:
            x_out, y_out = x, y
        return (
            torch.from_numpy(x_out.astype(np.float32)),
            torch.from_numpy(y_out.astype(np.float32)),
        )

    # ------------------------------------------------------------------
    # Convenience für Tests
    # ------------------------------------------------------------------

    def raw_windows(self) -> tuple[np.ndarray, np.ndarray]:
        """Liefert (X, y) unnormalisiert für Tests / Walk-Forward."""
        return self._X, self._y


# ══════════════════════════════════════════════════════════════════════
# TickDataset (für M1, brauchen persistierte Ticks)
# ══════════════════════════════════════════════════════════════════════


class TickDataset(Dataset):
    """PyTorch-Dataset über persistierte Ticks (DuckDB).

    Erwartet eine DuckDB-Datenbank mit den Tabellen ``ticks_trades``
    (Spalten: ts, symbol, side, price, volume) und ``ticks_orderbook``
    (mid, imbalance) — siehe ``persistence/duckdb_writer.py``.

    Wenn die DB nicht existiert oder zu wenige Rows hat, wird beim Aufruf
    ein RuntimeError geworfen und das Training-CLI sollte sauber
    überspringen.

    Parameters
    ----------
    db_path : Pfad zur DuckDB.
    lookback_ticks : Anzahl Ticks pro Input-Fenster.
    horizon_ticks : Anzahl Ticks für Label.
    label_quantile : Volatility-Spike-Label = future_abs_return > q_quantile.
    """

    def __init__(
        self,
        db_path: Path | str,
        lookback_ticks: int = 256,
        horizon_ticks: int = 60,
        label_quantile: float = 0.95,
        min_rows: int = 5000,
    ) -> None:
        if not _TORCH_AVAILABLE:
            raise RuntimeError("torch fehlt — TickDataset benötigt PyTorch.")
        self.db_path = Path(db_path)
        self.lookback_ticks = lookback_ticks
        self.horizon_ticks = horizon_ticks
        self.label_quantile = label_quantile
        self.min_rows = min_rows
        self._X, self._y = self._load_or_raise()

    def _load_or_raise(self) -> tuple[np.ndarray, np.ndarray]:
        if not self.db_path.exists():
            raise RuntimeError(
                f"TickDataset: DB {self.db_path} existiert nicht — "
                f"M1-Training braucht persistierte Ticks "
                f"(PERSIST_ENABLED=true)."
            )
        try:
            import duckdb
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"duckdb missing: {exc}") from exc
        try:
            con = duckdb.connect(str(self.db_path), read_only=True)
            rows = con.execute(
                "SELECT ts, price, volume FROM ticks_trades ORDER BY ts"
            ).fetchnumpy()
            con.close()
        except Exception as exc:
            raise RuntimeError(f"TickDataset: load failed: {exc}") from exc

        n = len(rows["ts"]) if rows else 0
        if n < max(self.min_rows, self.lookback_ticks + self.horizon_ticks + 1):
            raise RuntimeError(
                f"TickDataset: zu wenig Tick-Daten ({n} Zeilen) — "
                f"min benötigt {self.min_rows}."
            )
        prices = np.asarray(rows["price"], dtype=np.float64)
        # Channels: log-return, abs-return als Proxy für die 3 SpikeWav-Channels
        ret = np.diff(np.log(prices + 1e-9))
        abs_ret = np.abs(ret)
        L = self.lookback_ticks
        H = self.horizon_ticks
        starts = range(0, len(ret) - L - H)
        X = np.array(
            [
                np.stack(
                    [
                        ret[s : s + L],
                        abs_ret[s : s + L],
                        ret[s : s + L] ** 2,
                    ],
                    axis=0,
                )
                for s in starts
            ]
        )
        future_vol = np.array(
            [np.std(ret[s + L : s + L + H]) for s in starts]
        )
        threshold = float(np.quantile(future_vol, self.label_quantile))
        y = (future_vol > threshold).astype(np.int64)
        return X, y

    def __len__(self) -> int:
        return self._X.shape[0]

    def __getitem__(self, idx: int) -> tuple[Any, Any]:
        return (
            torch.from_numpy(self._X[idx].astype(np.float32)),
            torch.tensor(int(self._y[idx]), dtype=torch.int64),
        )
