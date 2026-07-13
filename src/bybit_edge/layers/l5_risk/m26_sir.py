"""
M26 — SIR-Kompartiment-Liquidations-Contagion [L5]

Formeln (PRD):
    dS/dt = -β · S · I
    dI/dt =  β · S · I - γ · I
    dR/dt =  γ · I
    R₀ = β · S₀ / γ

Modelliert Liquidationskaskaden als epidemische Ausbreitung:
    S = Susceptible (offene Positionen, die liquidiert werden könnten)
    I = Infected (aktive Liquidationsevents)
    R = Recovered (abgeschlossene Liquidationen)

R₀ > 1 → selbstverstärkende Kaskade.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any

import numpy as np
from scipy.integrate import odeint

from bybit_edge.config import SIR_R0_CASCADE_THRESHOLD, SIR_RECAL_DAYS
from bybit_edge.layers.base import BaseModule

# Forward-Simulation Horizont: 30 Minuten in Sekunden
_FORWARD_HORIZON_S: float = 30.0 * 60.0
_FORWARD_STEPS: int = 180  # 10-s-Auflösung

# Kalibrierungsfenster-Limit (siehe CRITICAL_REVIEW_2 M26-Finding):
# compute() erhält nur das AKTUELLE Open-Interest, keine historische
# OI-Zeitreihe. `oi_history = [open_interest] * n` approximiert S(t) daher
# für JEDES historische Event mit dem heutigen OI — für frühe Events einer
# laufenden Kaskade (OI progressiv gefallen) ist das massiv falsch. Eine
# echte historische OI-Serie ist ohne größere Änderungen am Aufrufer
# (compute()-Signatur, Upstream-Datenfluss) hier nicht rekonstruierbar.
# Als Milderung beschränken wir das Kalibrierungsfenster auf die jüngsten
# Events, für die die Annahme "OI ≈ aktuelles OI" am wenigsten falsch ist,
# statt das gesamte (potenziell sehr lange) liq_events-Fenster zu nutzen.
_CALIBRATION_WINDOW_MAX_EVENTS: int = 20


class M26SIR(BaseModule):
    """SIR-Kompartiment-Liquidations-Contagion Modul.

    Kalibriert β und γ aus historischen Liquidationsevents und
    Open-Interest-Daten, berechnet R₀ und simuliert Kaskaden vorwärts.
    """

    def __init__(self) -> None:
        self._beta: float = 0.001  # Fallback
        self._gamma: float = 0.1  # Fallback
        self._calibrated: bool = False
        # Rolling-Buffer für Re-Kalibrierung (30d)
        self._recal_buffer: deque[dict[str, Any]] = deque(
            maxlen=SIR_RECAL_DAYS * 24 * 60  # ~1 Eintrag/min über 30 Tage
        )

    # ------------------------------------------------------------------
    # ODE-System
    # ------------------------------------------------------------------

    def _sir_ode(
        self,
        y: list[float],
        t: float,
        beta: float,
        gamma: float,
    ) -> list[float]:
        """SIR-ODE-System für scipy.integrate.odeint.

        Parameters
        ----------
        y : [S, I, R]
        t : Zeitpunkt (unused, aber von odeint benötigt)
        beta : Infektionsrate
        gamma : Recoveryrate

        Returns
        -------
        [dS/dt, dI/dt, dR/dt]
        """
        s, i, r = y
        ds_dt = -beta * s * i
        di_dt = beta * s * i - gamma * i
        dr_dt = gamma * i
        return [ds_dt, di_dt, dr_dt]

    # ------------------------------------------------------------------
    # Kalibrierung
    # ------------------------------------------------------------------

    def _calibrate(
        self,
        liq_events: list[dict[str, Any]],
        open_interest_history: list[float],
    ) -> tuple[float, float]:
        """Kalibriere β und γ aus historischen Daten via OLS.

        S ≈ OI - kumuliertes Liq-Volumen
        I = laufende Liq-Rate (Events/Zeiteinheit)
        OLS: dI/dt ≈ β·S·I - γ·I  → regressiere dI/dt auf [S·I, -I]

        LIMITATION: `open_interest_history` muss den zum jeweiligen
        historischen Event-Zeitpunkt tatsächlich geltenden OI enthalten,
        damit S(t) korrekt ist. Der einzige aktuelle Aufrufer
        (`compute()`) kennt nur das AKTUELLE OI und approximiert die
        gesamte Historie damit — siehe dortiger Kommentar zur
        Fenster-Beschränkung.

        Returns
        -------
        (beta, gamma) — kalibrierte Parameter.
        """
        if len(liq_events) < 10 or len(open_interest_history) < 10:
            return 0.001, 0.1  # Fallback

        n = min(len(liq_events), len(open_interest_history))
        liq_events_trimmed = liq_events[-n:]
        oi_hist = open_interest_history[-n:]

        # Kumuliertes Liq-Volumen
        liq_volumes = np.array(
            [float(e.get("volume", 0.0)) for e in liq_events_trimmed],
            dtype=np.float64,
        )
        cum_liq = np.cumsum(liq_volumes)

        # S(t) = OI(t) - kumuliertes Liq-Volumen
        oi_arr = np.array(oi_hist, dtype=np.float64)
        s_arr = np.maximum(oi_arr - cum_liq, 1.0)  # mindestens 1 um Division/0 zu vermeiden

        # I(t) = Liq-Rate (gleitender Durchschnitt über kleine Fenster)
        # Wir nutzen die Liq-Volumen direkt als Proxy für I
        i_arr = np.maximum(liq_volumes, 0.0)

        # dI/dt ≈ finite difference
        if len(i_arr) < 3:
            return 0.001, 0.1

        di_dt = np.diff(i_arr)
        s_mid = s_arr[:-1]
        i_mid = i_arr[:-1]

        # OLS: dI/dt = β * S * I - γ * I
        # → dI/dt = β * (S*I) + (-γ) * I
        # X = [S*I, I], y = dI/dt
        si_product = s_mid * i_mid
        x_mat = np.column_stack([si_product, i_mid])
        y_vec = di_dt

        # Filter: nur Zeilen wo I > 0 (sonst ist die Regression sinnlos)
        mask = i_mid > 0.0
        if mask.sum() < 5:
            return 0.001, 0.1

        x_mat = x_mat[mask]
        y_vec = y_vec[mask]

        # Geschlossene OLS-Lösung: θ = (X^T X)^{-1} X^T y
        xtx = x_mat.T @ x_mat
        det = np.linalg.det(xtx)
        if abs(det) < 1e-30:
            return 0.001, 0.1

        try:
            theta = np.linalg.solve(xtx, x_mat.T @ y_vec)
        except np.linalg.LinAlgError:
            return 0.001, 0.1

        beta_est = float(theta[0])
        gamma_est = float(-theta[1])  # Negation weil Koeffizient von I ist -γ

        # Plausibilitätsprüfung
        if beta_est <= 0 or gamma_est <= 0:
            return 0.001, 0.1

        return beta_est, gamma_est

    # ------------------------------------------------------------------
    # BaseModule interface
    # ------------------------------------------------------------------

    def compute(
        self,
        liq_events: list[dict[str, Any]],
        open_interest: float,
        current_ts: float,
    ) -> dict[str, Any]:
        """Berechne SIR-basiertes Kaskaden-Signal.

        Parameters
        ----------
        liq_events : Liste von Liquidationsevents
            Jedes Event: {"volume": float, "timestamp_ms": int, ...}
        open_interest : Aktuelles Open Interest
        current_ts : Aktueller Zeitstempel (Unix seconds)

        Returns
        -------
        dict mit signal, r0, beta, gamma, s_current, i_current,
        peak_i_forecast, cascade_risk, method_id, confidence, ts.
        """
        ts_now = time.time()

        # Leere Events → neutrales Signal
        if not liq_events or open_interest <= 0:
            return {
                "signal": 0,
                "r0": 0.0,
                "beta": self._beta,
                "gamma": self._gamma,
                "s_current": open_interest,
                "i_current": 0.0,
                "peak_i_forecast": 0.0,
                "cascade_risk": False,
                "method_id": "M26",
                "confidence": 0.0,
                "ts": ts_now,
            }

        # Kumuliertes Liq-Volumen
        total_liq_volume = sum(
            float(e.get("volume", 0.0)) for e in liq_events
        )

        # Aktuelle Kompartiment-Schätzung
        s_current = max(open_interest - total_liq_volume, 1.0)
        i_current = float(liq_events[-1].get("volume", 0.0)) if liq_events else 0.0
        r_current = total_liq_volume

        # Re-Kalibrierung wenn genug Daten
        if len(liq_events) >= 10:
            # LIMITATION: nur das AKTUELLE Open-Interest ist hier bekannt.
            # Wir kalibrieren daher nur auf die jüngsten
            # _CALIBRATION_WINDOW_MAX_EVENTS Events (näher am aktuellen
            # OI-Zeitpunkt) statt auf das volle liq_events-Fenster, um die
            # Verzerrung durch die konstante-OI-Approximation zu begrenzen
            # (siehe Modul-Kopf-Kommentar / CRITICAL_REVIEW_2 M26-Finding).
            calib_events = liq_events[-_CALIBRATION_WINDOW_MAX_EVENTS:]
            oi_history = [open_interest] * len(calib_events)  # Approximation
            self._beta, self._gamma = self._calibrate(calib_events, oi_history)
            self._calibrated = True

        # R₀ berechnen — Division-by-Zero-Schutz
        gamma_safe = max(self._gamma, 1e-12)
        r0 = self._beta * s_current / gamma_safe

        # Kaskaden-Alarm
        cascade_risk = r0 > SIR_R0_CASCADE_THRESHOLD
        signal = 1 if cascade_risk else 0

        # Forward-Simulation: odeint über 30 min
        y0 = [s_current, max(i_current, 0.01), r_current]
        n_total = s_current + max(i_current, 0.01) + r_current
        if n_total > 0:
            y0_norm = [v / n_total for v in y0]
        else:
            y0_norm = [1.0, 0.0, 0.0]

        t_span = np.linspace(0, _FORWARD_HORIZON_S, _FORWARD_STEPS)
        solution = odeint(
            self._sir_ode,
            y0_norm,
            t_span,
            args=(self._beta, self._gamma),
        )
        i_trajectory = solution[:, 1]
        peak_i_forecast = float(np.max(i_trajectory)) * n_total

        # Confidence: basierend auf Datenqualität und R₀-Stärke
        data_quality = min(len(liq_events) / 50.0, 1.0)
        r0_strength = min(abs(r0 - 1.0) / 2.0, 1.0) if cascade_risk else 0.0
        confidence = min(data_quality * 0.5 + r0_strength * 0.5, 1.0)

        # Buffer für Re-Kalibrierung aktualisieren
        self._recal_buffer.append({
            "ts": current_ts,
            "s": s_current,
            "i": i_current,
            "r": r_current,
            "r0": r0,
        })

        return {
            "signal": signal,
            "r0": r0,
            "beta": self._beta,
            "gamma": self._gamma,
            "s_current": s_current,
            "i_current": i_current,
            "peak_i_forecast": peak_i_forecast,
            "cascade_risk": cascade_risk,
            "method_id": "M26",
            "confidence": confidence,
            "ts": ts_now,
        }

    def validate(self) -> bool:
        """Prüft ob Parameter plausibel sind."""
        return self._beta >= 0 and self._gamma >= 0

    def reset(self) -> None:
        """Setzt SIR-State auf Initialisierung zurück."""
        self._beta = 0.001
        self._gamma = 0.1
        self._calibrated = False
        self._recal_buffer.clear()
