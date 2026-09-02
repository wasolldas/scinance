# DEPRECATED (2026-06-23): Scinance-1.0-Legacy.
# Siehe scinance2-impl/state/CLEANUP_PLAN.md - Live-Pipeline gestoppt (TODO-2),
# Strategien S1-S5 sind empirisch DROP (WAVE1_FINAL_REPORT.md), Modul folgt der
# LiveRunner-Deprecation. Aufruf gilt als Anti-Pattern; Code bleibt nur als
# Audit-Trail im Repo. Reaktivierung ware eine neue, vorregistrierte Hypothese.

"""
Live-Risiko-Budget — Max-DD-Stop, Daily-Loss-Limit, Vol-Scaling.

Diese Schicht greift VOR jeder Order-Ausführung und hat drei Aufgaben
(in Prioritäts-Reihenfolge):

1. **Daily-Loss-Limit:**
   Wenn ``equity - daily_start_equity < RISK_DAILY_LOSS_PCT * daily_start_equity``,
   werden alle neuen Entries blockiert. Offene Positionen werden NICHT
   zwangsgeschlossen — ein erholter Markt soll nicht durch Knee-Jerk-
   Verkäufe vernichtet werden.

2. **Max-Drawdown-Stop:**
   Wenn ``equity / peak_equity - 1 < RISK_MAX_DRAWDOWN_PCT``, werden alle
   neuen Entries blockiert UND die offene Position wird per
   ``executor.close_position()`` geschlossen.

3. **Vol-Scaling** (optional, ``RISK_VOL_SCALING_ENABLED``):
   Aus den letzten ``RISK_VOL_LOOKBACK_BARS`` Preisen wird die realisierte
   Stdev der Log-Returns bestimmt. Die Order-Größe wird mit
   ``RISK_VOL_TARGET_BPS / realized_vol_bps`` skaliert (gedeckelt auf 2×
   und untergrenze 0.1× des Originals). Kein Block, nur Skalierung.

**Recovery-Regel:**
Daily-Loss- und Max-DD-Sperren bleiben blockierend, bis entweder
(a) ein manueller Reset über ``RISK_BUDGET_RESET=true`` gesetzt wird
(``reset_if_recovered`` löscht dann ``blocked_reason``), oder (b) ein
neuer UTC-Tag begonnen hat UND die aktuelle Equity wieder mindestens
95 % des Peaks erreicht.

**Persistenz:**
Der State (`daily_start_equity`, `daily_start_utc_date`, `peak_equity`,
`realized_pnl_today`, `blocked_reason`) wird in ``RISK_STATE_PATH``
(JSON) gehalten. Beim Start wird er eingelesen; existiert er nicht,
initialisiert er sich aus der aktuellen Equity.
"""
from __future__ import annotations

import json
import logging
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

import numpy as np


@dataclass
class RiskState:
    """Persistierter Zustand des Risiko-Budgets."""

    daily_start_equity: float
    daily_start_utc_date: str  # YYYY-MM-DD
    peak_equity: float
    realized_pnl_today: float
    blocked_reason: str = ""  # "" | "daily_loss" | "max_drawdown"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RiskState":
        return cls(
            daily_start_equity=float(data.get("daily_start_equity", 0.0)),
            daily_start_utc_date=str(data.get("daily_start_utc_date", "")),
            peak_equity=float(data.get("peak_equity", 0.0)),
            realized_pnl_today=float(data.get("realized_pnl_today", 0.0)),
            blocked_reason=str(data.get("blocked_reason", "")),
        )


class RiskBudget:
    """Live-Risiko-Budget mit persistentem Zustand."""

    # Untere/obere Skalierungs-Grenze für Vol-Scaling.
    _VOL_SCALE_MIN: float = 0.1
    _VOL_SCALE_MAX: float = 2.0
    # Numerische Stabilität für Realized-Vol.
    _VOL_EPS: float = 1e-9
    # Recovery-Schwelle: equity >= peak * (1 - dieser Wert).
    _RECOVERY_PEAK_RATIO: float = 0.95
    # Minimale Preis-Series-Länge für Vol-Scaling.
    _MIN_VOL_SERIES: int = 10

    def __init__(
        self,
        daily_loss_pct: float,
        max_dd_pct: float,
        vol_scaling_enabled: bool,
        vol_target_bps: float,
        state_path: Path,
        vol_lookback_bars: int = 60,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        # daily_loss_pct/max_dd_pct werden in der "negativ"-Konvention
        # entgegengenommen (z. B. -0.03 für -3 %). Wir normalisieren,
        # damit Sign-Verwirrungen ausgeschlossen sind.
        self.daily_loss_pct = -abs(float(daily_loss_pct))
        self.max_dd_pct = -abs(float(max_dd_pct))
        self.vol_scaling_enabled = bool(vol_scaling_enabled)
        self.vol_target_bps = float(vol_target_bps)
        self.state_path = Path(state_path)
        self.vol_lookback_bars = int(vol_lookback_bars)
        self.logger = logger or logging.getLogger(__name__)

        self.state: Optional[RiskState] = None
        self._loaded: bool = False

    # ------------------------------------------------------------------
    # Persistenz
    # ------------------------------------------------------------------

    def load(self, current_equity: float) -> None:
        """Lädt den State aus JSON, oder initialisiert ihn aus der Equity.

        Bei einer beschädigten/leeren Datei wird ebenfalls neu initialisiert.
        """
        equity = max(float(current_equity), 0.0)
        today = self._utc_today_iso()

        if self.state_path.exists():
            try:
                with self.state_path.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                self.state = RiskState.from_dict(data)
                # Robustheit: Wenn peak_equity 0 oder Equity > Peak, anpassen.
                if self.state.peak_equity <= 0 and equity > 0:
                    self.state.peak_equity = equity
                if equity > self.state.peak_equity:
                    self.state.peak_equity = equity
                self.logger.info(
                    "RiskBudget: State geladen (peak=%.2f, day=%s, blocked=%s)",
                    self.state.peak_equity,
                    self.state.daily_start_utc_date,
                    self.state.blocked_reason or "no",
                )
                self._loaded = True
                return
            except (json.JSONDecodeError, OSError, ValueError, TypeError):
                self.logger.exception(
                    "RiskBudget: State-Datei %s unlesbar — initialisiere neu.",
                    self.state_path,
                )

        # Neu initialisieren.
        self.state = RiskState(
            daily_start_equity=equity,
            daily_start_utc_date=today,
            peak_equity=equity,
            realized_pnl_today=0.0,
            blocked_reason="",
        )
        self._loaded = True
        self.save()
        self.logger.info(
            "RiskBudget: State initialisiert (equity=%.2f, day=%s)",
            equity,
            today,
        )

    def save(self) -> None:
        """Schreibt den aktuellen State atomar als JSON."""
        if self.state is None:
            return
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
            with tmp.open("w", encoding="utf-8") as fh:
                json.dump(self.state.to_dict(), fh)
            tmp.replace(self.state_path)
        except OSError:
            self.logger.exception(
                "RiskBudget: State konnte nicht geschrieben werden (%s).",
                self.state_path,
            )

    # ------------------------------------------------------------------
    # Equity-Updates / Block-Logik
    # ------------------------------------------------------------------

    def on_equity_update(
        self,
        equity: float,
        now_utc: Optional[datetime] = None,
    ) -> None:
        """Aktualisiert Peak, Tagesrollover und prüft die Block-Trigger."""
        if self.state is None:
            self.load(equity)
            assert self.state is not None  # nosec: für mypy
        equity = float(equity)
        if equity <= 0 or not math.isfinite(equity):
            return

        # 1) Tagesrollover (UTC).
        today = self._utc_today_iso(now_utc)
        if today != self.state.daily_start_utc_date:
            self.logger.info(
                "RiskBudget: UTC-Tagesrollover %s -> %s (daily_start=%.2f)",
                self.state.daily_start_utc_date, today, equity,
            )
            self.state.daily_start_utc_date = today
            self.state.daily_start_equity = equity
            self.state.realized_pnl_today = 0.0

        # 2) Peak aktualisieren.
        if equity > self.state.peak_equity:
            self.state.peak_equity = equity

        # 3) Realized-PnL aktualisieren (PnL seit Tagesbeginn).
        if self.state.daily_start_equity > 0:
            self.state.realized_pnl_today = equity - self.state.daily_start_equity

        # 4) Block-Checks. Sobald ein Block einmal gesetzt ist, bleibt er
        #    bestehen, bis Recovery / Reset ihn löscht.
        already_blocked = self.state.blocked_reason != ""

        # Daily-Loss (Priorität 1).
        if not already_blocked and self.state.daily_start_equity > 0:
            loss = equity - self.state.daily_start_equity
            limit = self.daily_loss_pct * self.state.daily_start_equity
            if loss < limit:
                self.state.blocked_reason = "daily_loss"
                already_blocked = True
                self.logger.warning(
                    "RISK BLOCK: daily loss limit hit "
                    "(equity=%.2f start=%.2f loss=%.2f limit=%.2f)",
                    equity, self.state.daily_start_equity, loss, limit,
                )

        # Max-DD (Priorität 2, kann Daily-Loss überschreiben).
        if self.state.peak_equity > 0:
            dd = equity / self.state.peak_equity - 1.0
            if dd < self.max_dd_pct:
                if self.state.blocked_reason != "max_drawdown":
                    self.state.blocked_reason = "max_drawdown"
                    self.logger.warning(
                        "RISK BLOCK: max drawdown reached "
                        "(equity=%.2f peak=%.2f dd=%.2f%% limit=%.2f%%)",
                        equity, self.state.peak_equity, dd * 100,
                        self.max_dd_pct * 100,
                    )

        self.save()

    # ------------------------------------------------------------------
    # Entry-Checks
    # ------------------------------------------------------------------

    def check_entry_allowed(self, intended_qty: float) -> tuple[bool, str]:
        """Prüft, ob ein neuer Entry zulässig ist."""
        if self.state is None:
            return True, ""
        if intended_qty <= 0:
            return False, "qty<=0"
        if self.state.blocked_reason:
            return False, self.state.blocked_reason
        return True, ""

    def should_force_close(self) -> bool:
        """True, wenn der Max-DD-Stop greift und Position geschlossen werden muss."""
        if self.state is None:
            return False
        return self.state.blocked_reason == "max_drawdown"

    # ------------------------------------------------------------------
    # Vol-Scaling
    # ------------------------------------------------------------------

    def adjust_qty(
        self,
        qty: float,
        recent_prices: Union[list[float], np.ndarray],
    ) -> float:
        """Skaliert ``qty`` anhand der realisierten Vol über die letzten Bars.

        Wenn Vol-Scaling deaktiviert ist oder die Preis-Series zu kurz/
        ungültig, wird ``qty`` unverändert zurückgegeben.
        """
        if not self.vol_scaling_enabled:
            return float(qty)
        if qty <= 0:
            return float(qty)

        prices = np.asarray(recent_prices, dtype=np.float64).ravel()
        # Vorsicht vor NaN/Inf und Nicht-positiven Preisen.
        prices = prices[np.isfinite(prices) & (prices > 0)]
        if prices.size < self._MIN_VOL_SERIES:
            return float(qty)

        prices = prices[-self.vol_lookback_bars:]
        log_rets = np.diff(np.log(prices))
        if log_rets.size == 0:
            return float(qty)

        # Realized-Vol in Basispunkten.
        realized_vol_bps = float(np.std(log_rets) * 10_000.0)
        if not math.isfinite(realized_vol_bps) or realized_vol_bps <= 0:
            return float(qty)

        scale = self.vol_target_bps / (realized_vol_bps + self._VOL_EPS)
        scale = max(self._VOL_SCALE_MIN, min(self._VOL_SCALE_MAX, scale))
        return float(qty) * scale

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------

    def reset_if_recovered(self, current_equity: float) -> bool:
        """Setzt ``blocked_reason`` zurück, wenn Recovery-Bedingung erfüllt.

        Bedingung: neuer UTC-Tag UND ``equity >= peak * 0.95``. Wird die
        Recovery erfolgreich angewandt, gibt die Methode True zurück und
        speichert den State.
        """
        if self.state is None or not self.state.blocked_reason:
            return False

        equity = float(current_equity)
        if equity <= 0 or self.state.peak_equity <= 0:
            return False

        today = self._utc_today_iso()
        new_day = today != self.state.daily_start_utc_date
        recovered = equity >= self.state.peak_equity * self._RECOVERY_PEAK_RATIO

        if new_day and recovered:
            old_reason = self.state.blocked_reason
            self.state.blocked_reason = ""
            self.state.daily_start_utc_date = today
            self.state.daily_start_equity = equity
            self.state.realized_pnl_today = 0.0
            self.save()
            self.logger.info(
                "RiskBudget: Recovery erfolgreich — Block '%s' aufgehoben "
                "(equity=%.2f peak=%.2f)",
                old_reason, equity, self.state.peak_equity,
            )
            return True
        return False

    def manual_reset(self, current_equity: float) -> None:
        """Einmal-Reset-Knopf (durch ``RISK_BUDGET_RESET=true`` ausgelöst)."""
        if self.state is None:
            self.load(current_equity)
            return
        old_reason = self.state.blocked_reason
        self.state.blocked_reason = ""
        equity = max(float(current_equity), 0.0)
        if equity > 0:
            self.state.daily_start_equity = equity
            self.state.daily_start_utc_date = self._utc_today_iso()
            self.state.realized_pnl_today = 0.0
            if equity > self.state.peak_equity:
                self.state.peak_equity = equity
        self.save()
        self.logger.warning(
            "RiskBudget: manueller Reset (vorher blocked='%s', equity=%.2f).",
            old_reason, equity,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _utc_today_iso(now_utc: Optional[datetime] = None) -> str:
        if now_utc is None:
            now_utc = datetime.now(timezone.utc)
        elif now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)
        return now_utc.astimezone(timezone.utc).date().isoformat()
