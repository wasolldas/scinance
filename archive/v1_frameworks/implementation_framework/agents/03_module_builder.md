# AGENT: MODULE BUILDER
## Rolle: Implementierung aller 21 Methoden M1–M26 · Phase 1–4

---

## IDENTITÄT

Du bist der Module Builder. Du implementierst jedes Modul VOLLSTÄNDIG nach PRD-Spezifikation: exakte Formeln, korrekte Libraries, PRD-Schwellenwerte in `config.py`, saubere Interfaces. Kein Modul ist "in progress" — entweder fertig oder nicht angefangen.

**Jedes Modul hat dasselbe Interface:**
```python
class M{N}_{Name}:
    def __init__(self, config: dict = None): ...
    def compute(self, data: ...) -> dict: ...  # Returns Signal + Metadata
    def validate(self) -> bool: ...            # Prüft eigene Konfiguration
```

---

## IMPLEMENTIERUNGSREIHENFOLGE (aus PRD-Priorität)

### PHASE 1 — QUICK WINS (Woche 2–4)

---

#### M22: Funding-Rate-Clamp Pressure-Release [L5] ← ERSTE IMPLEMENTIERUNG

Datei: `src/bybit_edge/layers/l5_risk/m22_funding_pressure.py`

**Formeln (exakt aus PRD):**
```python
# F_t = P_t + clamp(I_t - P_t, -0.05%, +0.05%)
# Pressure_t = (I_t - P_t) - clamp(I_t - P_t, ±0.05%)
# Signal: |Pressure_t| > 2σ(Pressure_{24h}) AND T_settlement - t < 30 min

import numpy as np
from collections import deque
from config import (FUNDING_CLAMP_UPPER, FUNDING_CLAMP_LOWER,
                    FUNDING_INTEREST_RATE, PRESSURE_ENTRY_WINDOW_MINUTES,
                    PRESSURE_ZSCORE_THRESHOLD, PRESSURE_EXIT_MINUTES_POST_SETTLEMENT)

class M22FundingPressure:
    def __init__(self):
        self._pressure_history: deque[float] = deque(maxlen=24 * 60 * 10)  # 24h at 100ms
        self._24h_sigma: float = 0.0

    def compute(self, ticker: 'TickerSnapshot', seconds_to_settlement: float) -> dict:
        P_t = ticker.premium_index
        I_t = FUNDING_INTEREST_RATE
        F_t = P_t + np.clip(I_t - P_t, FUNDING_CLAMP_LOWER, FUNDING_CLAMP_UPPER)
        pressure = (I_t - P_t) - np.clip(I_t - P_t, FUNDING_CLAMP_LOWER, FUNDING_CLAMP_UPPER)

        self._pressure_history.append(pressure)
        if len(self._pressure_history) > 100:
            self._24h_sigma = np.std(list(self._pressure_history))

        in_window = 0 < seconds_to_settlement < PRESSURE_ENTRY_WINDOW_MINUTES * 60
        pressure_extreme = (self._24h_sigma > 0 and
                           abs(pressure) > PRESSURE_ZSCORE_THRESHOLD * self._24h_sigma)

        signal = 0
        if in_window and pressure_extreme:
            signal = 1 if pressure < 0 else -1  # negative pressure → Long, positive → Short

        return {
            "signal": signal,           # 1=Long, -1=Short, 0=Wait
            "pressure": pressure,
            "pressure_zscore": pressure / self._24h_sigma if self._24h_sigma > 0 else 0,
            "funding_rate": F_t,
            "seconds_to_settlement": seconds_to_settlement,
            "in_window": in_window,
        }
```

**Test:** `tests/unit/test_m22.py`
- Bekannter Pressure-Wert → korrektes Signal
- Außerhalb Settlement-Window → Signal = 0
- Sigma=0 → kein Signal (Division by zero verhindert)
- Walk-Forward auf 6M synthetischen Daten → Sharpe ≥ 1.5

---

#### M23: Mark-Index Basis Settlement Convergence [L5]

Datei: `src/bybit_edge/layers/l5_risk/m23_basis_convergence.py`

```python
# Basis_t = (markPrice_t - indexPrice_t) / indexPrice_t
# Signal: Basis > 0.0008 AND T < 1h → Short
#         Basis < -0.0008 AND T < 1h → Long

from config import BASIS_LONG_THRESHOLD, BASIS_SHORT_THRESHOLD, BASIS_ENTRY_WINDOW_MINUTES

class M23BasisConvergence:
    def compute(self, ticker: 'TickerSnapshot', seconds_to_settlement: float) -> dict:
        basis = ticker.basis
        in_window = 0 < seconds_to_settlement < BASIS_ENTRY_WINDOW_MINUTES * 60
        signal = 0
        if in_window:
            if basis > BASIS_SHORT_THRESHOLD:
                signal = -1  # Short: Perp überbewertet
            elif basis < BASIS_LONG_THRESHOLD:
                signal = 1   # Long: Perp unterbewertet
        return {"signal": signal, "basis": basis, "in_window": in_window}
```

---

#### M2: OFI Cont-Kukanov-Stoikov [L1]

Datei: `src/bybit_edge/layers/l1_ingestion/m2_ofi.py`

```python
# Formel exakt aus PRD:
# e_n = I(P^b_n >= P^b_{n-1}) * q^b_n
#     - I(P^b_n <= P^b_{n-1}) * q^b_{n-1}
#     - I(P^a_n <= P^a_{n-1}) * q^a_n
#     + I(P^a_n >= P^a_{n-1}) * q^a_{n-1}
# OFI = rolling sum of e_n
# Signal: |OFI_rolling_5s| > Q90

import numpy as np
from collections import deque
from config import OFI_WINDOW_SECONDS, OFI_QUANTILE_THRESHOLD
import numba

@numba.njit
def _compute_event(pb_curr, pb_prev, qb_curr, qb_prev,
                   pa_curr, pa_prev, qa_curr, qa_prev) -> float:
    e = 0.0
    if pb_curr >= pb_prev: e += qb_curr
    if pb_curr <= pb_prev: e -= qb_prev
    if pa_curr <= pa_prev: e -= qa_curr
    if pa_curr >= pa_prev: e += qa_prev
    return e

class M2OFI:
    def __init__(self):
        self._events: deque[tuple[float, float]] = deque()  # (ts, e_n)
        self._ofi_history: deque[float] = deque(maxlen=5*60*50)  # 5min at 50hz
        self._prev_bb: tuple[float, float] = (0.0, 0.0)
        self._prev_ba: tuple[float, float] = (0.0, 0.0)
        self._q90: float = 0.0

    def update(self, ob: 'OrderbookState', ts: float) -> dict:
        # Berechne e_n
        bb = ob.best_bid
        ba = ob.best_ask
        e_n = _compute_event(bb[0], self._prev_bb[0], bb[1], self._prev_bb[1],
                             ba[0], self._prev_ba[0], ba[1], self._prev_ba[1])
        self._prev_bb, self._prev_ba = bb, ba

        # Rolling OFI
        self._events.append((ts, e_n))
        cutoff = ts - OFI_WINDOW_SECONDS
        while self._events and self._events[0][0] < cutoff:
            self._events.popleft()
        ofi = sum(e for _, e in self._events)

        # Quantile-Update
        self._ofi_history.append(abs(ofi))
        if len(self._ofi_history) > 100:
            self._q90 = np.quantile(list(self._ofi_history), OFI_QUANTILE_THRESHOLD)

        signal = 0
        if self._q90 > 0:
            if ofi > self._q90: signal = 1
            elif ofi < -self._q90: signal = -1

        return {"signal": signal, "ofi": ofi, "ofi_q90": self._q90, "e_n": e_n}
```

---

#### M7: Permutation Entropy [L3]

Datei: `src/bybit_edge/layers/l3_regime/m7_permutation_entropy.py`

```python
# Bibliothek: ordpy
# PE < Median_24h → Markt geordneter → Greenlight
import ordpy
import numpy as np
from collections import deque
from config import PE_ORDER, PE_DELAY, PE_WINDOW_BARS

class M7PermutationEntropy:
    def __init__(self):
        self._prices: deque[float] = deque(maxlen=PE_WINDOW_BARS * 2)
        self._pe_history: deque[float] = deque(maxlen=24 * 60)  # 24h at 1/min

    def update(self, price: float) -> dict:
        self._prices.append(price)
        if len(self._prices) < PE_WINDOW_BARS:
            return {"greenlight": False, "pe": None}

        prices_arr = np.array(list(self._prices)[-PE_WINDOW_BARS:])
        pe = ordpy.permutation_entropy(prices_arr, order=PE_ORDER, delay=PE_DELAY)

        self._pe_history.append(pe)
        median_24h = np.median(list(self._pe_history)) if len(self._pe_history) > 10 else pe
        greenlight = pe < median_24h

        return {"greenlight": greenlight, "pe": pe, "pe_median": median_24h}
```

---

#### M8: BOCPD (Online Change Point Detection auf OI) [L3]

Datei: `src/bybit_edge/layers/l3_regime/m8_bocpd.py`

```python
# Library: bayesian-changepoint-detection
# Signal: Posterior-Spike → Strukturbruch in OI
import numpy as np
from collections import deque
import bayesian_changepoint_detection.online_changepoint_detection as oncd
from functools import partial
from config import BOCPD_HAZARD_LAMBDA

class M8BOCPD:
    def __init__(self):
        self._oi_history: deque[float] = deque(maxlen=2000)
        hazard_fn = partial(oncd.constant_hazard, BOCPD_HAZARD_LAMBDA)
        self._R, self._maxes = np.array([[1]]), []

    def update(self, open_interest: float) -> dict:
        self._oi_history.append(open_interest)
        if len(self._oi_history) < 10:
            return {"changepoint": False, "run_length_prob": 0.0}

        oi_arr = np.array(list(self._oi_history))
        # Incremental update
        # ... BOCPD online-update logic
        changepoint_prob = float(self._R[0, -1]) if self._R.size > 0 else 0.0
        changepoint = changepoint_prob > 0.5

        return {"changepoint": changepoint, "run_length_prob": changepoint_prob,
                "open_interest": open_interest}
```

---

#### M15: Gutenberg-Richter + Omori [L4]

Datei: `src/bybit_edge/layers/l4_pattern/m15_gr_omori.py`

```python
# GR: log10(N(>=M)) = a - b*M
# Omori: lambda(t) = K / (t - t_main + c)^p
# b-Wert MLE: b_hat = log10(e) / (M_bar - M_min) (Aki 1965)

import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import kstest
from config import GR_MAINSHOCK_QUANTILE, GR_MIN_EVENTS, OMORI_FORECAST_MINUTES

class M15GROmori:
    def __init__(self):
        self._mainshock_ts: float | None = None
        self._omori_params: dict | None = None  # K, c, p

    def _aki_b_value(self, magnitudes: np.ndarray) -> float:
        """Aki (1965) MLE-Schätzer für b-Wert"""
        M_min = magnitudes.min()
        M_bar = magnitudes.mean()
        return np.log10(np.e) / (M_bar - M_min) if M_bar > M_min else 1.0

    def _omori_fn(self, t: np.ndarray, K: float, c: float, p: float) -> np.ndarray:
        return K / (t + c) ** p

    def update(self, liq_buffer: 'LiquidationBuffer', current_ts: float) -> dict:
        magnitudes = liq_buffer.magnitudes_usd(seconds=3600)  # 1h window
        if len(magnitudes) < GR_MIN_EVENTS:
            return {"b_value": None, "mainshock": False, "omori_active": False,
                    "aftershock_rate": 0.0, "signal": 0}

        b = self._aki_b_value(magnitudes)
        b_low = b < 1.0  # großbeben-prone

        # Mainshock detection
        recent_events = liq_buffer.recent(seconds=300)  # 5 min
        mainshock = False
        if recent_events:
            max_usd = max(e.usd_value for e in recent_events)
            q99 = np.quantile([e.usd_value for e in liq_buffer.recent(86400)], GR_MAINSHOCK_QUANTILE)
            if max_usd > q99:
                mainshock = True
                mainshock_event = max(recent_events, key=lambda e: e.usd_value)
                self._mainshock_ts = mainshock_event.timestamp_ms / 1000

        # Omori-Fit wenn Mainshock aktiv
        omori_active = False
        aftershock_rate = 0.0
        if self._mainshock_ts and (current_ts - self._mainshock_ts) < OMORI_FORECAST_MINUTES * 60:
            omori_active = True
            t_elapsed = current_ts - self._mainshock_ts
            if self._omori_params:
                K, c, p = self._omori_params["K"], self._omori_params["c"], self._omori_params["p"]
                aftershock_rate = float(self._omori_fn(np.array([t_elapsed]), K, c, p)[0])

        return {
            "b_value": b,
            "b_low": b_low,
            "mainshock": mainshock,
            "omori_active": omori_active,
            "aftershock_rate": aftershock_rate,
            "signal": 1 if (mainshock and omori_active) else 0  # Signal für Strategie 1
        }
```

---

### PHASE 2 — CORE METHODS (Woche 5–10)

**Implementiere in dieser Reihenfolge:**

#### M26: SIR-Contagion [L5]
Datei: `src/bybit_edge/layers/l5_risk/m26_sir.py`

Formel: `dS/dt = -β·S·I`, `dI/dt = β·S·I - γ·I`, `dR/dt = γ·I`, `R₀ = β·S₀/γ`
Library: `scipy.integrate.odeint`, `scipy.optimize.curve_fit`
Signal: R₀ > 1.0 → Kaskaden-Alarm

#### M14a: Hawkes 1-D Single Channel [L4]
Datei: `src/bybit_edge/layers/l4_pattern/m14_hawkes.py`

Formel: `λ(t) = μ + α·β·Σ_i exp(-β·(t-t_i))`, `n_∞ = α/β (branching ratio)`
Library: `hawkeslib` (Windows-kompatibel, PRIMÄR) + `scipy` Fallback
Signal: Branching-Ratio > 0.85 → Kaskaden-Alarm
Note: `tick`-Library NUR im Docker-Container (Linux)

#### M25: Kyle's Lambda [L5]
Datei: `src/bybit_edge/layers/l5_risk/m25_kyle_lambda.py`

Formel: `Δp_t = λ·v_t·sign_t + ε_t`, OLS rolling 100 Trades
Library: `statsmodels.regression.rolling.RollingOLS` oder `numpy.linalg.lstsq`
Signal: λ > Q95(λ_{30d}) → Toxic Flow → kein Limit-Order-Entry

#### M6: Shannon-L2-Orderbook Entropy [L3]
Datei: `src/bybit_edge/layers/l3_regime/m6_entropy.py`

Formel: `H = -Σ p_i log(p_i)` über normalisierte Size-Verteilung der Top-20 Levels
Library: `numpy`
Signal: H < Median − 2σ → Entropie-Kollaps → Greenlight

#### M4: Wavelet-Symlet Denoising [L2]
Datei: `src/bybit_edge/layers/l2_denoising/m4_wavelet.py`

Library: `PyWavelets` (`pywt.wavedec` + `pywt.threshold` + `pywt.waverec`)
Wavelet: `sym6`, Level 4
Output: Entrauschter Imbalance-Stream

#### M9: HMM (3-State) [L3]
Datei: `src/bybit_edge/layers/l3_regime/m9_hmm.py`

Library: `hmmlearn.GaussianHMM(n_components=3)`
Features: `[realized_vol_5min, sign(OFI_5min), fundingRate]`
Output: State-Posterior → Regime-Label

#### M5: FFD Fractional Differentiation [L2]
Datei: `src/bybit_edge/layers/l2_denoising/m5_ffd.py`

Formel: `(1-B)^d x_t = Σ_k (-1)^k C(d,k) x_{t-k}`, d gesucht via ADF-Test
Library: `numpy`, `statsmodels.tsa.stattools.adfuller`

---

### PHASE 3 — ADVANCED (Woche 11–20)

**Implementiere in dieser Reihenfolge:**

#### M14b: Hawkes 6-D (vollständige Matrix) [L4]
Upgrade von M14a auf 6 Event-Typen (MO+, MO-, LO+, LO-, CX+, CX-) + 2 Liq-Channels
Docker-only (tick Library), aber hawkeslib-Fallback pflegen

#### M16: TFSAX + Smith-Waterman [L4]
Libraries: `tslearn`, `saxpy`, `biopython.Bio.pairwise2`
Phase: 5y Kline-Historie laden, TFSAX-Sequenz-Library aufbauen
Windows: parasail-GPU für SW optional, Biopython CPU immer

#### M18: PatchTST Funding-Cycle [L4]
Libraries: `torch`, `transformers` (oder eigene Implementierung)
Input: FFD-präparierte Kline + fundingRate + openInterest
VRAM: ~4GB (Batch 32) → RTX 5060 Ti OK

#### M19: TimesNet 2D-Periodicity [L4]
Library: `momentfm` oder eigene TimesNet-Implementierung
Period-Dim: 8h Funding-Zyklus

#### M20: MOMENT Zero-Shot [L4]
Library: `momentfm`
MOMENT-base (110M, ~10GB Training-VRAM)
LoRA-FineTune (nicht full-finetune)
MOMENT-large: NUR Inferenz mit FP16

#### M17: Renyi-Transfer-Entropy [L4]
Library: `pyinform` (Windows-kompatibel)
q-Parameter: 1.5 (Standard → Tail-Events gewichtet)
Multi-Symbol: Top-20 Bybit-Perps

#### M13: Cross-Sectional Z-Score [L3]
Library: `polars`, `numpy`
Multi-Symbol-Panel aus TickerState

#### M21: Long/Short-Ratio Smart-Money Divergenz [L4]
REST-Endpoint: `/v5/market/long-short-ratio`
Signal: buyRatio > 0.75 AND Preis fällt → Smart-Money-Short-Signal

---

### PHASE 4 — MOONSHOTS (Woche 21–24)

#### M1: SpikeWavformer (SNN+DWT) [L1]
Libraries: `snnTorch`, `PyWavelets`, `torch`
Training: RTX 5060 Ti (~6-12h), Inferenz: CPU
Surrogate-Gradient-Training mit LIF-Neuronen

#### M11: TDA / Persistent Homology [L3]
Libraries: `ripser`, `gudhi`, `persim`
Rolling 100-Bar-Fenster über Multi-Symbol-Returns
L¹-Norm der Persistence-Landscape

#### M12: RQA [L3]
Library: `pyrqa` (benötigt Java/OpenJDK)
Embedding-Dim m=3, Delay via Mutual Information
DET + LAM als Regime-Indikatoren

#### M10: MF-DFA Multifraktal [L3]
Library: `MFDFA`
q ∈ [-5, 5], Rolling N=2048

#### M3: Iceberg-Detection [L1] (optional)
Library: `sortedcontainers`, `numpy`
Level-History aus orderbook.200

---

## INTERFACE-STANDARD (alle Methoden)

```python
from abc import ABC, abstractmethod
from typing import Any

class BaseModule(ABC):
    """Basis-Interface für alle 21 Methoden"""

    @abstractmethod
    def compute(self, *args, **kwargs) -> dict[str, Any]:
        """
        Returns immer mindestens:
        {
            "signal": int,        # 1=Long, -1=Short, 0=Wait/Neutral
            "confidence": float,  # 0.0–1.0
            "method_id": str,     # z.B. "M22"
            "ts": float,          # time.time() bei Berechnung
        }
        """
        ...

    def validate(self) -> bool:
        """Prüft Konfiguration — gibt False zurück wenn nicht einsatzbereit"""
        return True

    def reset(self) -> None:
        """Setzt internen State zurück (für Backtester)"""
        ...
```

---

## NACH JEDEM MODUL

```bash
# Unit-Tests ausführen
pytest tests/unit/test_M{N}_{name}.py -v

# Wenn PASS:
git add src/bybit_edge/layers/
git commit -m "[M{N}] {Name}: implemented + tested (Phase {n})"
git push
```
