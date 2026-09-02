# AGENT: INFRASTRUCTURE BUILDER
## Rolle: Phase 0 · WebSocket-Collector · State-Engine · Persistence · Backtester

---

## IDENTITÄT

Du bist der Infrastructure Builder. Du baust das Fundament, auf dem alle 21 Methoden laufen. Ohne dich ist kein einziges Modul lauffähig. Dein Code muss production-grade sein: Reconnect-Logik, Event-Time-Indexing, saubere Pub/Sub-Struktur.

**Kein Modul-Builder beginnt seine Arbeit, bevor Infrastructure-Tests 100 % Pass haben.**

---

## KOMPONENTE 1: WebSocket Collector

Datei: `src/bybit_edge/collector/ws_collector.py`

```python
"""
Bybit V5 WebSocket Collector
- Verbindet sich mit allen benötigten Streams
- Auto-Reconnect mit exponential backoff
- Pub/Sub via asyncio.Queue pro Stream-Typ
- Snapshot-Resync bei Reconnect via REST
- Schema-Version in jedem Message-Objekt
"""
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional
import websockets
from websockets.exceptions import ConnectionClosed

# Alle 4 Pflicht-Streams laut PRD:
STREAMS = {
    "tickers": "tickers.{symbol}",           # 100ms
    "trades": "publicTrade.{symbol}",         # event-driven
    "orderbook50": "orderbook.50.{symbol}",   # ~20ms deltas
    "liquidation": "allLiquidation.{symbol}", # 500ms
}

@dataclass
class WSMessage:
    stream: str
    symbol: str
    data: dict
    recv_ts: float  # time.time() bei Empfang — Event-Time für Backtester
    schema_version: int = 1
```

**Implementiere vollständig:**
1. `class BybitWSCollector` mit `connect()`, `subscribe()`, `disconnect()`
2. `_reconnect_loop()` mit exponential backoff (1s, 2s, 4s, 8s, max 60s)
3. `_snapshot_resync()` via REST bei Reconnect (orderbook + recent-trade)
4. Pro Stream-Typ eine `asyncio.Queue` — max_size=10000
5. `add_handler(stream: str, handler: Callable)` für Pub/Sub
6. Windows-Fix: `asyncio.WindowsProactorEventLoopPolicy` in `__main__.py`

**Test:** `tests/unit/test_collector.py` — Mock-WebSocket, prüft Reconnect-Logik

---

## KOMPONENTE 2: State Engine

### 2a. OrderbookState
Datei: `src/bybit_edge/state/orderbook_state.py`

```python
"""
Top-50 Orderbook State — sorted arrays, efficient delta-updates
Benötigt von: M2 OFI, M3 Iceberg, M6 Entropie, M14 Hawkes, M25 Kyle
"""
import numpy as np
from sortedcontainers import SortedDict

class OrderbookState:
    def __init__(self, symbol: str, depth: int = 50):
        self.symbol = symbol
        self.depth = depth
        self.bids: SortedDict = SortedDict(lambda x: -x)  # descending
        self.asks: SortedDict = SortedDict()               # ascending
        self.last_update_id: int = 0
        self.last_ts: float = 0.0

    def apply_snapshot(self, data: dict) -> None: ...
    def apply_delta(self, data: dict) -> None: ...

    @property
    def best_bid(self) -> tuple[float, float]: ...  # (price, size)
    @property
    def best_ask(self) -> tuple[float, float]: ...
    @property
    def mid_price(self) -> float: ...
    @property
    def spread(self) -> float: ...

    def imbalance(self, levels: int = 1) -> float:
        """bid_size - ask_size normalized"""
        ...

    def top_n_arrays(self, n: int = 20) -> tuple[np.ndarray, np.ndarray]:
        """Returns (bid_prices, bid_sizes), (ask_prices, ask_sizes) as numpy arrays"""
        ...
```

### 2b. TickerState
Datei: `src/bybit_edge/state/ticker_state.py`

```python
"""
Alle relevanten Felder aus tickers-Stream.
Wird von M7, M8, M13, M22, M23, M24, M26 genutzt.
"""
from dataclasses import dataclass
import time

@dataclass
class TickerSnapshot:
    symbol: str
    last_price: float
    mark_price: float
    index_price: float
    funding_rate: float
    next_funding_time: int      # Unix ms
    open_interest: float
    open_interest_value: float
    bid1_price: float
    bid1_size: float
    ask1_price: float
    ask1_size: float
    ts: int                     # exchange timestamp ms
    recv_ts: float = 0.0        # time.time() bei Empfang

    @property
    def basis(self) -> float:
        """(mark_price - index_price) / index_price"""
        return (self.mark_price - self.index_price) / self.index_price

    @property
    def premium_index(self) -> float:
        """Approximate P — (mark - index) / index"""
        return self.basis

    @property
    def seconds_to_funding(self) -> float:
        """Sekunden bis nächstem Settlement"""
        return (self.next_funding_time / 1000) - time.time()
```

### 2c. LiquidationBuffer
Datei: `src/bybit_edge/state/liquidation_buffer.py`

```python
"""
Rolling Buffer für allLiquidation Events.
Benötigt von: M14 Hawkes, M15 GR/Omori, M26 SIR
"""
from collections import deque
from dataclasses import dataclass
import numpy as np

@dataclass
class LiquidationEvent:
    timestamp_ms: int    # T
    symbol: str          # s
    side: str            # S: "Buy" (Short-Liq) or "Sell" (Long-Liq)
    volume: float        # v (Stückzahl)
    price: float         # p (Bankrupt-Preis)
    usd_value: float     # volume * price

class LiquidationBuffer:
    def __init__(self, maxlen: int = 2000):
        self._buffer: deque[LiquidationEvent] = deque(maxlen=maxlen)

    def add(self, event: LiquidationEvent) -> None: ...

    def recent(self, seconds: float) -> list[LiquidationEvent]:
        """Events der letzten N Sekunden"""
        ...

    def magnitudes_usd(self, seconds: float) -> np.ndarray:
        """np.log10(usd_value) für G-R b-Wert-Schätzung"""
        ...

    def rate_per_second(self, window_seconds: float = 60) -> float:
        """Durchschnittliche Liquidationsrate"""
        ...
```

### 2d. TradeBuffer
Datei: `src/bybit_edge/state/trade_buffer.py`

```python
"""
Rolling Buffer für publicTrade Events.
Benötigt von: M2 OFI, M14 Hawkes, M25 Kyle's Lambda
"""
from collections import deque
from dataclasses import dataclass
import numpy as np

@dataclass  
class TradeEvent:
    timestamp_ms: int
    price: float
    volume: float
    side: str       # "Buy" or "Sell"
    is_block: bool  # BT flag

    @property
    def signed_volume(self) -> float:
        return self.volume if self.side == "Buy" else -self.volume

class TradeBuffer:
    def __init__(self, maxlen: int = 2000):
        self._buffer: deque[TradeEvent] = deque(maxlen=maxlen)

    def add(self, event: TradeEvent) -> None: ...
    def recent_signed_volumes(self, n: int = 100) -> np.ndarray: ...
    def recent_prices(self, n: int = 100) -> np.ndarray: ...
    def recent_timestamps(self, n: int = 100) -> np.ndarray: ...
```

---

## KOMPONENTE 3: Persistence Layer

Datei: `src/bybit_edge/persistence/db.py`

```python
"""
DuckDB für Hot-Storage (30 Tage in-process, SQL-Interface)
Parquet + ZSTD für Cold-Storage (lifetime archiving)
"""
import duckdb
import polars as pl
from pathlib import Path
from config import DB_PATH, PARQUET_DIR, HOT_RETENTION_DAYS

class PersistenceLayer:
    def __init__(self):
        self.conn = duckdb.connect(str(DB_PATH))
        self._init_schema()

    def _init_schema(self):
        """Erstellt alle Tabellen: tickers, trades, liquidations, orderbook_snapshots"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tickers (
                ts BIGINT NOT NULL,
                symbol VARCHAR NOT NULL,
                last_price DOUBLE,
                mark_price DOUBLE,
                index_price DOUBLE,
                funding_rate DOUBLE,
                next_funding_time BIGINT,
                open_interest DOUBLE,
                bid1_price DOUBLE,
                ask1_price DOUBLE,
                recv_ts DOUBLE
            )
        """)
        # + CREATE INDEX ts_symbol ON tickers(ts, symbol)
        # + liquidations table
        # + trades table
        # + kline_1min table (für REST-Backfill)

    def write_ticker(self, snap: 'TickerSnapshot') -> None: ...
    def write_liquidation(self, evt: 'LiquidationEvent') -> None: ...
    def write_trade(self, evt: 'TradeEvent') -> None: ...

    def query_kline(self, symbol: str, start_ts: int, end_ts: int,
                    interval: str = "1min") -> pl.DataFrame: ...

    def backfill_kline(self, symbol: str, months: int = 6) -> None:
        """REST-Backfill via /v5/market/kline mit Rate-Limit-Handling"""
        ...

    def archive_old_data(self) -> None:
        """Daten > HOT_RETENTION_DAYS → Parquet komprimieren, aus DuckDB löschen"""
        ...
```

---

## KOMPONENTE 4: Backtester

Datei: `src/bybit_edge/backtester/engine.py`

```python
"""
Event-Time-Backtester mit Walk-Forward-Cross-Validation.
PRD-Anforderungen:
- Event-Time-Indexing (kein Lookahead)
- Walk-Forward: 30d Train / 7d Test sliding
- Embargo: 30 min zwischen Train und Test
- Fees: Taker 0.055%, Maker 0.02%
- Slippage-Modell: kalibrierbar
"""
import polars as pl
import numpy as np
from dataclasses import dataclass, field
from typing import Callable, Generator
from config import FEE_TAKER, FEE_MAKER, WF_TRAIN_DAYS, WF_TEST_DAYS, WF_EMBARGO_MINUTES, RANDOM_SEED

@dataclass
class Trade:
    symbol: str
    entry_ts: int
    exit_ts: int
    side: str           # "Long" or "Short"
    entry_price: float
    exit_price: float
    quantity: float
    fee_type: str       # "taker" or "maker"
    pnl: float = 0.0
    pnl_bps: float = 0.0

@dataclass
class BacktestResult:
    trades: list[Trade]
    sharpe: float
    max_drawdown: float
    win_rate: float
    total_return: float
    n_trades: int
    equity_curve: np.ndarray

class WalkForwardSplitter:
    """Generiert Train/Test-Splits mit Embargo"""
    def __init__(self, df: pl.DataFrame, train_days: int = WF_TRAIN_DAYS,
                 test_days: int = WF_TEST_DAYS, embargo_minutes: int = WF_EMBARGO_MINUTES):
        ...

    def splits(self) -> Generator[tuple[pl.DataFrame, pl.DataFrame], None, None]:
        """Yields (train_df, test_df) mit Embargo-Gap"""
        ...

class BacktestEngine:
    def __init__(self, fee_taker: float = FEE_TAKER, fee_maker: float = FEE_MAKER,
                 slippage_bps: float = 2.0, random_seed: int = RANDOM_SEED):
        ...

    def run_walkforward(self, strategy_fn: Callable, data: pl.DataFrame,
                        symbol: str = "BTCUSDT") -> BacktestResult:
        """
        Walk-Forward mit striktem Event-Time-Indexing.
        strategy_fn bekommt train_data, gibt zurück: Signal-Funktion.
        Signal-Funktion bekommt bar-by-bar den Test-Stream (chronologisch).
        """
        ...

    def compute_metrics(self, trades: list[Trade]) -> BacktestResult:
        """Sharpe, Max-DD, Win-Rate, Total-Return"""
        ...
```

---

## KOMPONENTE 5: Funding Settlement Scheduler

Datei: `src/bybit_edge/scheduler.py`

```python
"""
Deterministischer Settlement-Scheduler.
BTCUSDT: 00, 08, 16 UTC (konfigurierbar per Symbol).
"""
import asyncio
import time
from datetime import datetime, timezone
from typing import Callable
from config import FUNDING_SETTLEMENT_HOURS

class FundingScheduler:
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        self._callbacks: list[Callable] = []

    def seconds_to_next_settlement(self) -> float:
        now_utc = datetime.now(timezone.utc)
        next_h = min(h for h in FUNDING_SETTLEMENT_HOURS if h > now_utc.hour,
                     default=FUNDING_SETTLEMENT_HOURS[0] + 24)
        ...

    def register_callback(self, fn: Callable) -> None:
        self._callbacks.append(fn)

    async def run(self) -> None:
        """Wartet auf nächstes Settlement, feuert alle Callbacks, wiederholt"""
        while True:
            wait_sec = self.seconds_to_next_settlement()
            await asyncio.sleep(wait_sec)
            for fn in self._callbacks:
                await fn()
```

---

## KOMPONENTE 6: Projekt-Setup-Files

### `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.backends.legacy:BuildBackend"

[project]
name = "bybit-edge"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "websockets>=12.0",
    "aiohttp>=3.9",
    "duckdb>=0.10",
    "polars>=0.20",
    "numpy>=1.26",
    "numba>=0.59",
    "scipy>=1.12",
    "statsmodels>=0.14",
    "pandas>=2.1",
    "python-dotenv>=1.0",
    "structlog>=24.0",
    "sortedcontainers>=2.4",
    "pykalman>=0.9",
    "filterpy>=1.4",
    "hmmlearn>=0.3",
    "PyWavelets>=1.5",
    "ordpy>=1.1",
    "MFDFA>=0.4",
    "ripser>=0.6",
    "persim>=0.3",
    "giotto-tda>=0.6",
    "hawkeslib>=0.2",
    "tslearn>=0.6",
    "saxpy>=1.0",
    "pyinform>=0.2",
    "biopython>=1.83",
    "antropy>=0.1",
    "bayesian-changepoint-detection>=0.3",
]

[project.optional-dependencies]
gpu = [
    "torch>=2.3",
    "torchvision>=0.18",
    "torchaudio>=2.3",
    "snnTorch>=0.9",
]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.10",
    "ipykernel>=6.29",
]
```

### `environment.yml`

```yaml
name: bybit-edge
channels:
  - pytorch
  - nvidia
  - conda-forge
  - defaults
dependencies:
  - python=3.11
  - pytorch::pytorch
  - pytorch::torchvision
  - pytorch::torchaudio
  - nvidia::pytorch-cuda=12.4
  - conda-forge::duckdb
  - conda-forge::polars
  - conda-forge::numba
  - pip
  - pip:
    - -e ".[dev,gpu]"
```

### `scripts/setup_windows.bat`

```batch
@echo off
echo === Bybit Edge System Setup (Windows) ===
echo.

REM 1. Conda environment
conda env create -f environment.yml
if errorlevel 1 (
    echo ERROR: Conda environment creation failed!
    pause
    exit /b 1
)

REM 2. Activate
conda activate bybit-edge

REM 3. Verify CUDA
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"

REM 4. Create .env template
if not exist .env (
    echo BYBIT_API_KEY=your_testnet_key_here > .env
    echo BYBIT_API_SECRET=your_testnet_secret_here >> .env
    echo BYBIT_TESTNET=true >> .env
    echo LOG_LEVEL=INFO >> .env
    echo .env created - fill in your Bybit Testnet credentials!
)

REM 5. Create data directories
mkdir data\parquet 2>nul

echo.
echo Setup complete! Next steps:
echo 1. Edit .env with your Bybit Testnet API keys
echo 2. Run: python -m bybit_edge.collector  (starts data collection)
echo 3. Run: python scripts/backfill_kline.py  (backfill 6M history)
echo 4. Run: pytest tests/ -v
pause
```

---

## TEST-ANFORDERUNGEN (Infrastruktur)

Datei: `tests/unit/test_infrastructure.py`

```python
"""
Infrastruktur-Tests — müssen 100% Pass haben vor jedem Modul-Build.
"""
import pytest
import asyncio
import numpy as np
from unittest.mock import AsyncMock, patch

def test_orderbook_state_apply_delta():
    """Delta-Update korrekt angewendet"""
    ...

def test_orderbook_state_mid_price():
    ...

def test_ticker_state_basis_calculation():
    """basis = (mark - index) / index"""
    snap = TickerSnapshot(mark_price=50100, index_price=50000, ...)
    assert abs(snap.basis - 0.002) < 1e-6

def test_liquidation_buffer_magnitudes():
    """log10(usd_value) für GR b-Wert"""
    ...

def test_walk_forward_splitter_no_lookahead():
    """test_start > train_end + embargo immer sichergestellt"""
    ...

def test_funding_scheduler_seconds_to_next():
    """Sekunden bis Settlement immer positiv und < 8h"""
    ...

@pytest.mark.asyncio
async def test_ws_collector_reconnect():
    """Reconnect löst Snapshot-Resync aus"""
    ...
```

---

## ABSCHLUSS-COMMIT

Nach vollständiger Infrastruktur:
```bash
git add src/ tests/unit/test_infrastructure.py pyproject.toml environment.yml scripts/
git commit -m "[Phase 0] Infrastructure: Collector, StateEngine, Persistence, Backtester"
git tag v0.1.0
git push && git push --tags
```

`[INFRA] DONE | COMPONENTS: 8 | TESTS: 100% | COMMIT: v0.1.0`
