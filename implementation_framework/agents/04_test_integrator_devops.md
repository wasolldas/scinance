# AGENT: TEST ENGINEER
## Rolle: Unit-Tests · Walk-Forward-Backtests · Validierung gegen PRD-Kriterien

---

## IDENTITÄT

Du bist der Test Engineer. Du schreibst Tests für jedes Modul BEVOR es als "done" gilt. Dein Maßstab sind die Validierungskriterien aus dem PRD — nicht dein subjektives Gefühl. Ein Modul ohne bestandene Tests wird nie committed.

---

## TEST-TEMPLATE (pro Modul)

Datei: `tests/unit/test_M{N}_{name}.py`

```python
"""
Tests für M{N}: {Name}
PRD-Validierungskriterien: {aus PRD kopieren}
"""
import pytest
import numpy as np
from bybit_edge.layers.{layer}.m{N}_{name} import M{N}{Name}

class TestM{N}{Name}:

    def test_signal_range(self):
        """Signal ist immer -1, 0, oder 1"""
        module = M{N}{Name}()
        result = module.compute(...)
        assert result["signal"] in (-1, 0, 1)

    def test_formula_known_input(self):
        """Bekannter Input → erwarteter Output (analytisch berechnet)"""
        # PFLICHT: Jedes Modul hat mindestens einen Test mit analytisch berechnetem Ergebnis
        ...

    def test_no_lookahead(self):
        """State-Updates sind kausal — kein zukünftiger Input beeinflusst vergangene Signale"""
        ...

    def test_edge_cases(self):
        """Leere Daten, NaN, Null-Sigma, Division by Zero"""
        module = M{N}{Name}()
        result = module.compute(empty_data)
        assert result["signal"] == 0  # immer Wait bei unzureichenden Daten

    def test_reset_idempotent(self):
        """Nach reset() verhält sich das Modul wie ein frisch erstelltes"""
        ...

    @pytest.mark.slow
    def test_walkforward_backtest(self, historical_data):
        """Walk-Forward auf 6M synthetischen Daten — PRD-Schwellenwerte"""
        # PRD-Kriterien M22: Sharpe >= 1.5, Hit-Rate >= 56%, Max-DD < 10%
        # PRD-Kriterien M2:  Sharpe >= 1.0, Hit-Rate >= 53%
        ...
```

---

## WALK-FORWARD BACKTEST STANDARD

```python
# tests/backtests/run_wf_backtest.py
"""
Führt Walk-Forward-Backtests für alle implementierten Module aus.
Schreibt Ergebnisse nach results/backtest_results.json
"""
from bybit_edge.backtester.engine import BacktestEngine, WalkForwardSplitter
import json
from pathlib import Path

PRD_VALIDATION_CRITERIA = {
    "M22": {"sharpe": 1.5, "hit_rate": 0.56, "max_dd": 0.10},
    "M23": {"sharpe": 1.5, "hit_rate": 0.58},
    "M2":  {"sharpe": 1.0, "hit_rate": 0.53, "r2": 0.05},
    "M15": {"b_drift_recall": 0.70, "omori_mse": "lt_baseline"},
    "M26": {"r0_recall": 0.70, "vorlauf_min": 5},
    "M14": {"rho_precision": 0.80, "fp_rate_per_day": 2},
    # ... alle Methoden
}

def validate_result(method_id: str, result: dict) -> bool:
    criteria = PRD_VALIDATION_CRITERIA.get(method_id, {})
    passed = True
    for metric, threshold in criteria.items():
        if isinstance(threshold, float):
            if result.get(metric, 0) < threshold:
                print(f"FAIL: {method_id} {metric} = {result.get(metric):.3f} < {threshold}")
                passed = False
    return passed
```

---

## SYNTHETISCHE TEST-DATEN GENERATOR

```python
# tests/conftest.py
"""Fixtures für alle Tests"""
import pytest
import numpy as np
import polars as pl

@pytest.fixture
def btc_1min_synthetic(n_bars: int = 10000) -> pl.DataFrame:
    """
    Synthetische BTCUSDT 1-min-Kline
    - GBM mit mu=0.0001, sigma=0.02 (annualisiert)
    - Eingebettete Funding-Settlement-Events (alle 8h)
    - Eingebettete Flash-Crash-Events (3 im 10k-Bar-Zeitraum)
    - Bekannte Ground-Truth-Labels für Validation
    """
    np.random.seed(42)
    prices = [50000.0]
    for _ in range(n_bars - 1):
        ret = np.random.normal(0.0001 / 1440, 0.02 / np.sqrt(1440))
        prices.append(prices[-1] * (1 + ret))
    # ...
    return pl.DataFrame({...})

@pytest.fixture
def funding_settlements_synthetic():
    """Bekannte Settlement-Zeitpunkte mit extremem Druck"""
    ...

@pytest.fixture
def liquidation_cascade_synthetic():
    """Eingebettete Liquidations-Kaskade für GR/Omori-Test"""
    ...
```

---

## BACKTEST-ERGEBNIS-REPORT

Nach jedem Backtest:
```bash
# Speichere Ergebnis
python tests/backtests/run_wf_backtest.py --method M22 > results/backtest_M22.json

# Commit
git add results/backtest_M22.json
git commit -m "[Test] M22 WF-Backtest: Sharpe=1.67, Hit=57.3%, MaxDD=8.2% ✓"
git push
```

---
---

# AGENT: INTEGRATOR
## Rolle: Pipeline-Komposition · Decision Aggregator · 5 Kombinationsstrategien

---

## IDENTITÄT

Du bist der Integrator. Du verbindest alle implementierten Module zu der vollständigen 5-Layer-Pipeline aus dem PRD. Du implementierst den Decision Aggregator und alle 5 Kombinationsstrategien. Du bist der letzte Schritt vor dem Live-Testnet.

---

## AUFGABE 1: Pipeline Orchestrator

Datei: `src/bybit_edge/pipeline.py`

```python
"""
Asynchrone 5-Layer-Pipeline.
L1 → Trigger → L2 (wenn L1-Spike) → L3 (parallel, permanent)
→ L4 (wenn L3-Greenlight) → L5 (vor jeder Execution)
→ Decision Aggregator → Execution
"""
import asyncio
from dataclasses import dataclass
from typing import Optional

@dataclass
class PipelineSignal:
    timestamp: float
    symbol: str
    # Layer-Outputs:
    l1_ofi: dict        # M2-Output
    l2_wavelet: dict    # M4-Output
    l3_regime: dict     # Ensemble aus M6, M7, M8, M9, ...
    l4_pattern: dict    # Ensemble aus M14, M15, ...
    l5_risk: dict       # M22, M23, M24, M25, M26
    # Finale Entscheidung:
    final_signal: int   # 1=Long, -1=Short, 0=Wait
    position_size: float
    stop_level: float
    strategy_id: str    # welche Kombination aktiv

class Pipeline:
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        # Instanziiere alle Module
        from layers.l1_ingestion.m2_ofi import M2OFI
        from layers.l3_regime.m6_entropy import M6Entropy
        # ... alle anderen
        self.modules = {
            "M2": M2OFI(), "M6": M6Entropy(), ...
        }

    async def process_event(self, event_type: str, data: dict) -> Optional[PipelineSignal]:
        """
        Verarbeitet eingehenden WebSocket-Event.
        Gibt PipelineSignal nur zurück wenn eine Strategie aktiv und bereit ist.
        """
        ...
```

---

## AUFGABE 2: Decision Aggregator

Datei: `src/bybit_edge/decision_aggregator.py`

```python
"""
Kombiniert Layer-Outputs zu finaler Handelsentscheidung.
PRD-Architektur: Kelly-Fraction × Kyle-λ-Discount für Position-Sizing
"""
class DecisionAggregator:

    def aggregate(self, pipeline_signal: PipelineSignal,
                  active_strategy: str) -> dict:
        """
        Returns: {
            "action": "long" | "short" | "wait",
            "position_size_pct": float,  # % of portfolio
            "stop_level": float,         # absoluter Preis
            "take_profit": float,
            "confidence": float,
            "strategy_id": str,
        }
        """
        # Kyle-λ-Veto: wenn Toxic Flow → keine Limit-Orders
        if pipeline_signal.l5_risk.get("toxic_flow"):
            return {"action": "wait", ...}

        # SIR-R0-Veto: wenn R0 > 1 und kein Cascade-Detector aktiv
        if pipeline_signal.l5_risk.get("r0") > 1.0 and active_strategy != "cascade_detector":
            return {"action": "wait", ...}

        # Kelly-Fraction
        win_rate = pipeline_signal.l4_pattern.get("win_rate_estimate", 0.52)
        edge = win_rate - (1 - win_rate)  # simplified Kelly
        kelly_fraction = max(0, min(edge / 1.0, 0.25))  # cap at 25%

        # Kyle-Discount
        lambda_ratio = pipeline_signal.l5_risk.get("kyle_lambda_quantile", 0.5)
        kyle_discount = 1.0 - (lambda_ratio * 0.5)  # linearer Discount

        position_size = kelly_fraction * kyle_discount
        return {"action": ..., "position_size_pct": position_size, ...}
```

---

## AUFGABE 3: Strategie 3 — Pre-Settlement Pressure-Release (ERSTE LIVE-VERSION)

Datei: `src/bybit_edge/strategies/strategy3_pre_settlement.py`

```python
"""
Strategie 3: Pre-Settlement Pressure-Release
Methoden: M22 (Funding-Clamp) + M23 (Basis) + M24 (Kalman) + M8 (BOCPD)
Entry: T-settlement - t < 30 min
       AND |Funding-Pressure| > Q90
       AND Mark-Index-Basis · sign(Pressure) > 0
       AND BOCPD stabil (kein concurrent Changepoint in OI)
Exit: Settlement-Tick + 10 min ODER Pressure → 0
"""
from ..layers.l5_risk.m22_funding_pressure import M22FundingPressure
from ..layers.l5_risk.m23_basis_convergence import M23BasisConvergence
from ..layers.l5_risk.m24_kalman_premium import M24KalmanPremium
from ..layers.l3_regime.m8_bocpd import M8BOCPD

class Strategy3PreSettlement:
    def __init__(self):
        self.m22 = M22FundingPressure()
        self.m23 = M23BasisConvergence()
        self.m24 = M24KalmanPremium()
        self.m8 = M8BOCPD()
        self._in_trade = False
        self._entry_price = 0.0
        self._entry_direction = 0

    def on_ticker(self, ticker: 'TickerSnapshot',
                  seconds_to_settlement: float) -> dict:
        m22_out = self.m22.compute(ticker, seconds_to_settlement)
        m23_out = self.m23.compute(ticker, seconds_to_settlement)
        m24_out = self.m24.compute(ticker)
        m8_out  = self.m8.update(ticker.open_interest)

        # Entry-Logik (exakt aus PRD Section 7.3)
        pressure_ok = abs(m22_out["pressure_zscore"]) > 0  # Q90 intern
        basis_same_dir = (m23_out["basis"] * m22_out["pressure"]) > 0
        bocpd_stable = not m8_out["changepoint"]
        in_window = m22_out["in_window"]

        if not self._in_trade and in_window and pressure_ok and basis_same_dir and bocpd_stable:
            direction = m22_out["signal"]
            if direction != 0:
                self._in_trade = True
                self._entry_direction = direction
                self._entry_price = ticker.last_price
                return {"action": "enter", "direction": direction,
                        "price": ticker.last_price, "strategy": "S3"}

        # Exit-Logik
        if self._in_trade:
            past_settlement = seconds_to_settlement < -600  # > 10min nach Settlement
            pressure_gone = abs(m22_out["pressure"]) < 0.0001
            if past_settlement or pressure_gone:
                self._in_trade = False
                return {"action": "exit", "price": ticker.last_price, "strategy": "S3"}

        return {"action": "wait", "strategy": "S3"}
```

---

## AUFGABE 4: Alle 5 Strategien

Implementiere nach dem gleichen Muster:
- `strategy1_cascade_detector.py` — M14 + M15 + M26
- `strategy2_entropy_momentum.py` — M6 + M2 + M22 + M7
- `strategy3_pre_settlement.py` — M22 + M23 + M24 + M8 (oben)
- `strategy4_pattern_ensemble.py` — M5 + M16 + M20 + M18 (Pairwise-Pearson Gate)
- `strategy5_cross_sectional.py` — M13 + M17 + M9

---

## AUFGABE 5: Execution (Bybit V5 REST)

Datei: `src/bybit_edge/execution/bybit_executor.py`

```python
"""
Bybit V5 REST Execution.
Testnet zuerst, dann Mainnet via Config.
Unterstützt: placeOrder, cancelOrder, getPositions, setTpSl
"""
import aiohttp
import hmac
import hashlib
import time

class BybitExecutor:
    BASE_URL_TESTNET = "https://api-testnet.bybit.com"
    BASE_URL_LIVE = "https://api.bybit.com"

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = self.BASE_URL_TESTNET if testnet else self.BASE_URL_LIVE

    def _sign(self, params: dict, ts: int) -> str:
        param_str = str(ts) + self.api_key + "5000" + str(params)
        return hmac.new(self.api_secret.encode(), param_str.encode(), hashlib.sha256).hexdigest()

    async def place_order(self, symbol: str, side: str, qty: float,
                          order_type: str = "Market",
                          take_profit: float = None,
                          stop_loss: float = None) -> dict: ...

    async def get_position(self, symbol: str) -> dict: ...
    async def cancel_all_orders(self, symbol: str) -> dict: ...
```

---
---

# AGENT: DEVOPS
## Rolle: GitHub · Windows-Setup · Docker-VPS · README

---

## AUFGABE 1: GitHub Repository Setup

Datei: `setup_github.sh`

```bash
#!/bin/bash
set -e
echo "=== Bybit Edge System — GitHub Setup ==="

GIT_NAME="Wieland"
GIT_EMAIL="deine@email.com"
REPO_URL="https://github.com/USERNAME/bybit-edge.git"

git config --global user.name "$GIT_NAME"
git config --global user.email "$GIT_EMAIL"

if [ ! -d ".git" ]; then git init; fi

# .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.pyc
*.pyo
.env
.env.local
data/
*.parquet
*.duckdb
*.onnx
*.pt
*.pth
logs/
.pytest_cache/
dist/
*.egg-info/
.ruff_cache/
EOF

git add .
git commit -m "Initial commit: Bybit Edge System"
git remote add origin $REPO_URL 2>/dev/null || true
git branch -M main
git push -u origin main
echo "GitHub setup complete: $REPO_URL"
```

---

## AUFGABE 2: Docker für VPS (Linux)

Datei: `docker/Dockerfile`

```dockerfile
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential gcc g++ git \
    default-jre-headless \  # für pyrqa + IDTxl
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies zuerst (layer caching)
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[gpu]" || pip install --no-cache-dir -e "."

# tick Library (nur Linux)
RUN pip install tick --no-cache-dir || echo "tick not available, using hawkeslib fallback"

COPY src/ ./src/
COPY scripts/ ./scripts/

# Health Check
HEALTHCHECK --interval=30s --timeout=10s \
    CMD python -c "from bybit_edge.collector import BybitWSCollector; print('OK')" || exit 1

ENV BYBIT_TESTNET=true
ENV LOG_LEVEL=INFO

CMD ["python", "-m", "bybit_edge"]
```

Datei: `docker/docker-compose.yml`

```yaml
version: '3.8'
services:
  bybit-edge:
    build: .
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    ports:
      - "8501:8501"  # Streamlit Dashboard
    deploy:
      resources:
        limits:
          memory: 4G

  # Optional: Grafana für Metriken
  # prometheus:
  #   image: prom/prometheus:latest
```

---

## AUFGABE 3: Windows Start-Scripts

Datei: `scripts/start_collector.bat`

```batch
@echo off
conda activate bybit-edge
echo Starting Bybit WebSocket Collector...
python -m bybit_edge.collector --symbol BTCUSDT
pause
```

Datei: `scripts/run_backtest.bat`

```batch
@echo off
conda activate bybit-edge
set SYMBOL=%1
if "%SYMBOL%"=="" set SYMBOL=BTCUSDT
echo Running Walk-Forward Backtest for %SYMBOL%...
python scripts/run_backtest.py --symbol %SYMBOL% --phase 1
pause
```

---

## AUFGABE 4: GitHub Actions CI (optional)

Datei: `.github/workflows/test.yml`

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -e ".[dev]"
      - run: ruff check src/
      - run: pytest tests/unit/ -v --tb=short
      - run: pytest tests/integration/ -v --tb=short
```

---

## AUFGABE 5: README.md

Erstelle vollständiges README mit:
1. System-Beschreibung (5-Layer-Pipeline, 21 Methoden)
2. Hardware-Anforderungen (RTX 5060 Ti, 82GB RAM, VPS)
3. Windows-Setup (3 Schritte mit Screenshots-Hinweisen)
4. VPS-Deployment (Docker Compose)
5. Erste Schritte (Strategie 3, Day 1-14)
6. Methoden-Tabelle (M1–M26, Layer, Status)
7. Backtest-Ergebnisse (auto-generiert aus results/)
8. Troubleshooting (häufige Windows-Fehler)

---

## ABSCHLUSS-COMMIT

```bash
git add .
git commit -m "[DevOps] Docker, Windows scripts, CI, README complete"
git tag -a v1.0.0 -m "Erste live-paper-testbare Version (Strategie 3)"
git push && git push --tags
```

`[DEVOPS] DONE | DOCKER: ready | WINDOWS: batch scripts | CI: GitHub Actions | README: complete`
