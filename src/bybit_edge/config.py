"""
Zentrale Konfiguration — alle Parameter aus dem PRD extrahiert.

Jeder Wert ist ein direktes Mapping aus FINAL_PRD.md. Wo sinnvoll,
kann der Wert via Umgebungsvariable überschrieben werden (API-Keys,
Pfade, Log-Level, Testnet-Flag). Nicht-überschreibbare Werte sind
feste PRD-Konstanten.

Verwendung:
    from bybit_edge.config import PRIMARY_SYMBOL, FEE_TAKER
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════════════════════════
# BYBIT API
# ═══════════════════════════════════════════════════════════════════
BYBIT_API_KEY: str = os.getenv("BYBIT_API_KEY", "")
BYBIT_API_SECRET: str = os.getenv("BYBIT_API_SECRET", "")
BYBIT_TESTNET: bool = os.getenv("BYBIT_TESTNET", "true").lower() == "true"
BYBIT_DEMO: bool = os.getenv("BYBIT_DEMO", "false").lower() == "true"

BYBIT_WS_PUBLIC_LIVE: Final[str] = "wss://stream.bybit.com/v5/public/linear"
BYBIT_WS_PUBLIC_TESTNET: Final[str] = (
    "wss://stream-testnet.bybit.com/v5/public/linear"
)
BYBIT_WS_PUBLIC_DEMO: Final[str] = (
    "wss://stream-demo.bybit.com/v5/public/linear"
)
BYBIT_WS_PRIVATE_LIVE: Final[str] = "wss://stream.bybit.com/v5/private"
BYBIT_WS_PRIVATE_TESTNET: Final[str] = (
    "wss://stream-testnet.bybit.com/v5/private"
)
BYBIT_WS_PRIVATE_DEMO: Final[str] = "wss://stream-demo.bybit.com/v5/private"
BYBIT_REST_LIVE: Final[str] = "https://api.bybit.com"
BYBIT_REST_TESTNET: Final[str] = "https://api-testnet.bybit.com"
BYBIT_REST_DEMO: Final[str] = "https://api-demo.bybit.com"


def ws_public_url() -> str:
    """Gibt die aktive Public-WS-URL zurück.

    WICHTIG: Bybit Demo Trading hat KEINEN eigenen Public-Stream.
    Public-Marktdaten kommen im Demo-Modus vom Mainnet. Nur REST-Trading
    und der Private-Stream nutzen die Demo-Endpoints.
    """
    if BYBIT_DEMO:
        return BYBIT_WS_PUBLIC_LIVE
    return BYBIT_WS_PUBLIC_TESTNET if BYBIT_TESTNET else BYBIT_WS_PUBLIC_LIVE


def ws_private_url() -> str:
    """Gibt die aktive private WS-URL zurück."""
    if BYBIT_DEMO:
        return BYBIT_WS_PRIVATE_DEMO
    return BYBIT_WS_PRIVATE_TESTNET if BYBIT_TESTNET else BYBIT_WS_PRIVATE_LIVE


def rest_base_url() -> str:
    """Gibt die aktive REST-Base-URL zurück.

    Public-Markt-REST (orderbook/recent-trade-Resync) funktioniert auch
    auf der Demo-Base. Signiertes Trading läuft über die Demo-Base.
    """
    if BYBIT_DEMO:
        return BYBIT_REST_DEMO
    return BYBIT_REST_TESTNET if BYBIT_TESTNET else BYBIT_REST_LIVE


# REST-Endpoints (relativ zur Base-URL)
REST_KLINE: Final[str] = "/v5/market/kline"
REST_FUNDING_HISTORY: Final[str] = "/v5/market/funding/history"
REST_OPEN_INTEREST: Final[str] = "/v5/market/open-interest"
REST_LONG_SHORT_RATIO: Final[str] = "/v5/market/account-ratio"
REST_INSTRUMENTS_INFO: Final[str] = "/v5/market/instruments-info"
REST_RECENT_TRADE: Final[str] = "/v5/market/recent-trade"
REST_ORDERBOOK: Final[str] = "/v5/market/orderbook"

# REST-Rate-Limits (PRD Abschnitt 3)
REST_RATE_LIMIT_UNAUTH: Final[int] = 120  # req/min
REST_RATE_LIMIT_AUTH: Final[int] = 600  # req/min

# ═══════════════════════════════════════════════════════════════════
# SYMBOLE (PRD Abschnitt 3 — Top 10)
# ═══════════════════════════════════════════════════════════════════
PRIMARY_SYMBOL: Final[str] = "BTCUSDT"
MULTI_SYMBOL_UNIVERSE: list[str] = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "AVAXUSDT",
    "ADAUSDT",
    "LINKUSDT",
    "POLUSDT",  # ehemals MATICUSDT (Bybit-Rename 09/2024)
]

# ═══════════════════════════════════════════════════════════════════
# WEBSOCKET-STREAMS (PRD Abschnitt 3, Tabelle)
# ═══════════════════════════════════════════════════════════════════
WS_TOPIC_TICKERS: Final[str] = "tickers.{symbol}"  # 100 ms
WS_TOPIC_PUBLIC_TRADE: Final[str] = "publicTrade.{symbol}"  # event-driven
WS_TOPIC_ORDERBOOK_50: Final[str] = "orderbook.50.{symbol}"  # ~20 ms delta
WS_TOPIC_ORDERBOOK_200: Final[str] = "orderbook.200.{symbol}"  # ~100 ms snapshot
WS_TOPIC_ALL_LIQUIDATION: Final[str] = "allLiquidation.{symbol}"  # 500 ms

# ═══════════════════════════════════════════════════════════════════
# FUNDING (PRD M22, Abschnitt 2.2, 4 M22)
# ═══════════════════════════════════════════════════════════════════
FUNDING_INTERVAL_SECONDS: Final[int] = 8 * 3600  # 8 h für BTCUSDT
FUNDING_SETTLEMENT_HOURS_UTC: Final[tuple[int, ...]] = (0, 8, 16)
FUNDING_CLAMP_UPPER: Final[float] = 0.0005  # +0.05%
FUNDING_CLAMP_LOWER: Final[float] = -0.0005  # -0.05%
FUNDING_INTEREST_RATE: Final[float] = 0.0003  # 0.03% (I)

# ═══════════════════════════════════════════════════════════════════
# FEES / SLIPPAGE (PRD Abschnitt 5, 8)
# ═══════════════════════════════════════════════════════════════════
FEE_TAKER: Final[float] = 0.00055  # 0.055%
FEE_MAKER: Final[float] = 0.0002  # 0.02%
SLIPPAGE_DEFAULT_BPS: Final[float] = 2.0  # 2 bps

# --- OPTIONEN: eigene Groesse, NICHT mit den Perp-Konstanten mischen -------
# Bybit berechnet Options-Gebuehren als Bruchteil des INDEXPREISES, nicht des
# Positions-Notionals. Ein direkter Vergleich mit FEE_TAKER/FEE_MAKER oben ist
# deshalb bedeutungslos.
#
# Quelle: Konto-Gebuehrenseite des Nutzers, abgelesen 2026-08-24 (WP-5/DEC-45).
# Auf der Options-Karte war KEIN Rabatt-Schalter aktiv, d. h. dies sind die
# effektiven Saetze.
FEE_OPTION_TAKER_OF_INDEX: Final[float] = 0.0003  # 0.0300% = 3,0 bp des Index
FEE_OPTION_MAKER_OF_INDEX: Final[float] = 0.0002  # 0.0200% = 2,0 bp des Index

# Umrechnung in Vol-Punkte (WP-5, per Unit-Test gepinnt, skalen-invariant):
#     Kosten [Vol-Pkt] = n_Fills * Gebuehr [bp Index] / VEGA_OVER_INDEX_BP
# Gemessen im Strangle-Bein-Band (7-14 DTE, abs(Delta) 0,15-0,30) am
# Snapshot 2026-08-24: BTC 5,282 / ETH 5,100.
VEGA_OVER_INDEX_BP_BTC: Final[float] = 5.282
VEGA_OVER_INDEX_BP_ETH: Final[float] = 5.100

# NICHT verifiziert und deshalb bewusst KEINE Konstante: die Delivery-/
# Exercise-Gebuehr bei Verfall und eine etwaige Deckelung als Anteil der
# Praemie. Beide treffen genau die Halten-bis-Verfall-Variante. Wer sie
# braucht, misst sie erst.

# ═══════════════════════════════════════════════════════════════════
# PERSISTENCE (PRD Abschnitt 8, Phase 0)
# ═══════════════════════════════════════════════════════════════════
DATA_DIR: Path = Path(os.getenv("BYBIT_DATA_DIR", "data"))
DB_PATH: Path = DATA_DIR / "bybit_edge.duckdb"
PARQUET_DIR: Path = DATA_DIR / "parquet"
MODELS_DIR: Path = DATA_DIR / "models"
# Dashboard-Snapshots (Parquet) — vom LiveRunner periodisch geschrieben,
# vom read-only Streamlit-Dashboard gelesen. Vermeidet DuckDB-Multi-Process-
# Lock-Konflikte (DuckDB unterstützt nur Single-Process-Zugriff).
DASHBOARD_SNAPSHOT_DIR: Path = DATA_DIR / "dashboard"
HOT_RETENTION_DAYS: Final[int] = 30  # Rolling Hot-Window
PARQUET_COMPRESSION: Final[str] = "zstd"

# ═══════════════════════════════════════════════════════════════════
# TRAINIERTE MODELL-CHECKPOINTS (PyTorch-State-Dicts)
# ═══════════════════════════════════════════════════════════════════
# Vorlage: data/models/{module}_{symbol}_{interval}.pt
M1_WEIGHTS_PATH: Path = MODELS_DIR / "m1_spikewav.pt"
M18_WEIGHTS_PATH: Path = MODELS_DIR / "m18_patchtst.pt"
M19_WEIGHTS_PATH: Path = MODELS_DIR / "m19_timesnet.pt"
M20_WEIGHTS_PATH: Path = MODELS_DIR / "m20_moment.pt"

# ═══════════════════════════════════════════════════════════════════
# TRAINING DEFAULTS (PyTorch — RTX 5060 Ti, 16 GB VRAM)
# ═══════════════════════════════════════════════════════════════════
TRAIN_DEFAULT_LR: Final[float] = 1e-3
TRAIN_DEFAULT_EPOCHS: Final[int] = 20
TRAIN_DEFAULT_BATCH_SIZE: Final[int] = 32
TRAIN_DEFAULT_LOOKBACK: Final[int] = 128
TRAIN_DEFAULT_HORIZON: Final[int] = 12  # 12 × 5min = 1 h
TRAIN_VAL_FRACTION: Final[float] = 0.2
TRAIN_BACKFILL_MONTHS_DEFAULT: Final[int] = 6

# ═══════════════════════════════════════════════════════════════════
# M2: OFI Cont-Kukanov-Stoikov (PRD M2)
# ═══════════════════════════════════════════════════════════════════
OFI_WINDOW_SECONDS: Final[int] = 5  # Rolling-Sum 5 s
OFI_WINDOW_1S: Final[int] = 1  # 1-Sekunden-Window
OFI_WINDOW_30S: Final[int] = 30  # 30-Sekunden-Window
OFI_QUANTILE_THRESHOLD: Final[float] = 0.90  # Q90 rolling 5-min
OFI_BETA_RECAL_HOURS: Final[int] = 24  # Re-Kalibrierung alle 24 h
OFI_TRAIN_DAYS: Final[int] = 1  # 1-Tag-Window für Beta-OLS
OFI_FORECAST_R2_MIN: Final[float] = 0.05  # PRD: R²(1s) ≥ 0.05

# ═══════════════════════════════════════════════════════════════════
# M3: Iceberg-Detection (PRD M3)
# ═══════════════════════════════════════════════════════════════════
ICEBERG_REPLENISHMENT_RATIO: Final[float] = 0.8  # Size ≥ 80% restored
ICEBERG_SCORE_THRESHOLD: Final[float] = 0.7  # Score > 0.7
ICEBERG_MIN_HITS: Final[int] = 5  # N_hits > 5
ICEBERG_DELTA_MS: Final[int] = 500  # 500 ms recheck delay
ICEBERG_BOUNCE_RATE_MIN: Final[float] = 0.60  # ≥ 60% Bounce-Rate

# ═══════════════════════════════════════════════════════════════════
# M4: Wavelet-Symlet-Denoising (PRD M4)
# ═══════════════════════════════════════════════════════════════════
WAVELET_MOTHER: Final[str] = "sym6"  # Symlet-6 (PRD-default)
WAVELET_LEVEL: Final[int] = 4  # 4-Level-Zerlegung
WAVELET_WINDOW_TICKS: Final[int] = 256  # Sliding-Window
WAVELET_THRESHOLD_METHOD: Final[str] = "soft"  # Soft-Threshold
# VisuShrink: λ_j = σ_j * sqrt(2 * log(N))

# ═══════════════════════════════════════════════════════════════════
# M5: Fraktionale Differenzierung FFD (PRD M5)
# ═══════════════════════════════════════════════════════════════════
FFD_D_GRID: Final[tuple[float, ...]] = (0.3, 0.4, 0.5)  # d-Wert-Suche
FFD_WEIGHT_THRESHOLD: Final[float] = 1e-4  # τ für Weight-Kürzung
FFD_ADF_P_THRESHOLD: Final[float] = 0.05  # ADF p < 0.05
FFD_RECAL_DAYS: Final[int] = 30  # Re-Kalibrierung alle 30-90 Tage

# ═══════════════════════════════════════════════════════════════════
# M6: Shannon-Entropie L2-Orderbuch (PRD M6)
# ═══════════════════════════════════════════════════════════════════
ENTROPY_LEVELS: Final[int] = 20  # Top-20 Levels (Bid + Ask)
ENTROPY_UPDATE_MS: Final[int] = 100  # alle 100 ms
ENTROPY_ROLLING_WINDOW_HOURS: Final[int] = 24  # 24-h-Quantil
ENTROPY_GREENLIGHT_QUANTILE: Final[float] = 0.05  # H < Q5 → Greenlight
ENTROPY_EPSILON: Final[float] = 1e-12  # numerische Stabilität

# ═══════════════════════════════════════════════════════════════════
# M7: Permutation Entropy (PRD M7)
# ═══════════════════════════════════════════════════════════════════
PE_ORDER: Final[int] = 4  # m = 4 (Bandt-Pompe Embedding)
PE_DELAY: Final[int] = 1  # τ = 1
PE_WINDOW_TICKS: Final[int] = 100  # Rolling 100-Tick-Window
PE_GREENLIGHT_THRESHOLD: Final[str] = "median_24h"  # PE < Median(PE_24h)

# ═══════════════════════════════════════════════════════════════════
# M8: BOCPD auf openInterest (PRD M8)
# ═══════════════════════════════════════════════════════════════════
BOCPD_HAZARD_LAMBDA: Final[float] = 120.0  # 1/120 → ~10 h erwartete Regime-Dauer
BOCPD_AGGREGATE_MINUTES: Final[int] = 5  # 5-min-Buckets
BOCPD_CHANGE_POINT_THRESHOLD: Final[float] = 0.5  # P(CP) > 0.5
BOCPD_MAX_FALSE_POS_PER_DAY: Final[int] = 10  # ≤ 10% / Tag
BOCPD_DETECTION_LATENCY_MIN: Final[int] = 2  # ≤ 2 min

# ═══════════════════════════════════════════════════════════════════
# M9: HMM Vola-OFI-Funding (PRD M9)
# ═══════════════════════════════════════════════════════════════════
HMM_N_STATES: Final[int] = 3  # Trend / Mean-Revert / High-Vol
HMM_FEATURES: Final[tuple[str, ...]] = (
    "realized_vol_5min",
    "sign_ofi_5min",
    "funding_rate",
)
HMM_RETRAIN_DAYS: Final[int] = 30  # Walk-Forward alle 30 Tage
HMM_TRAIN_MONTHS: Final[int] = 6  # 6 M Training-Historie
HMM_STABILITY_THRESHOLD: Final[float] = 0.80  # State stabil ≥ 80% der Bars

# ═══════════════════════════════════════════════════════════════════
# M10: MF-DFA Multifractal (PRD M10)
# ═══════════════════════════════════════════════════════════════════
MFDFA_WINDOW_N: Final[int] = 2048  # Rolling N = 2048
MFDFA_Q_RANGE: Final[tuple[float, float]] = (-5.0, 5.0)
MFDFA_SCALE_RANGE: Final[tuple[int, int]] = (16, 256)
MFDFA_ZSCORE_THRESHOLD: Final[float] = 2.0  # Δh-Spike > z=2

# ═══════════════════════════════════════════════════════════════════
# M11: TDA / Persistent Homology (PRD M11)
# ═══════════════════════════════════════════════════════════════════
TDA_WINDOW_BARS: Final[int] = 100  # Rolling 100-Bar-Fenster
TDA_SYMBOLS: Final[tuple[str, ...]] = (
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
)
TDA_L1_ZSCORE_THRESHOLD: Final[float] = 3.0  # L¹-Spike > z=3
TDA_RISK_OFF_REDUCTION: Final[float] = 0.20  # Max-DD-Reduktion ≥ 20%

# ═══════════════════════════════════════════════════════════════════
# M12: RQA Recurrence Quantification Analysis (PRD M12)
# ═══════════════════════════════════════════════════════════════════
RQA_EMBEDDING_DIM: Final[int] = 3  # m = 3
RQA_WINDOW_BARS: Final[int] = 500  # Rolling 500-Bar-Window
RQA_DET_THRESHOLD: Final[float] = 0.7  # DET > 0.7
RQA_RETURN_THRESHOLD_PCT: Final[float] = 1.0  # |Return| > 1% in 1h
RQA_HIT_RATE_MIN: Final[float] = 0.55  # ≥ 55%

# ═══════════════════════════════════════════════════════════════════
# M13: Cross-Sectional Ergodicity Z-Score (PRD M13)
# ═══════════════════════════════════════════════════════════════════
CSZ_WINDOW_HOURS: Final[int] = 1  # Rolling 1h Returns
CSZ_Z_THRESHOLD: Final[float] = 2.5  # |z| > 2.5
CSZ_SYMBOLS_TOP_N: Final[int] = 20  # Top-20 USDT-Perps

# ═══════════════════════════════════════════════════════════════════
# M14: Hawkes Spektralradius (PRD M14)
# ═══════════════════════════════════════════════════════════════════
HAWKES_WINDOW_SECONDS: Final[int] = 300  # 5-min Rolling-Window
HAWKES_REFIT_SECONDS: Final[int] = 30  # Re-Fit alle 30 s
HAWKES_CRITICAL_RHO: Final[float] = 0.9  # ρ(Φ) > 0.9 → Kaskaden-Alarm
HAWKES_DRHO_THRESHOLD: Final[float] = 0.0  # dρ/dt > 0 (steigend)
HAWKES_FALSE_POS_MAX_PER_DAY: Final[int] = 2  # ≤ 2/Tag
HAWKES_DIMENSIONS_FULL: Final[int] = 6  # 6-D + 2 exogene
HAWKES_START_SINGLE_CHANNEL: Final[bool] = True  # Phase 2: 1D zuerst
# Event-Typen: MO+, MO-, LO+, LO-, CX+, CX-, LongLiq, ShortLiq

# ═══════════════════════════════════════════════════════════════════
# M15: Gutenberg-Richter b + Omori p,c,k (PRD M15)
# ═══════════════════════════════════════════════════════════════════
GR_MAINSHOCK_QUANTILE: Final[float] = 0.99  # Q99 rolling 24h
GR_MIN_EVENTS: Final[int] = 50  # Minimum 50 Events für b-Wert
GR_BUFFER_SIZE: Final[int] = 1000  # Sliding 1000-Events
GR_BUCKET_SECONDS: Final[int] = 1  # 1-s-Buckets
OMORI_FORECAST_MINUTES: Final[int] = 30  # Forward 30 min
OMORI_MAINSHOCK_WINDOW_MINUTES: Final[int] = 5  # Mainshock = max in 5 min
# Opt-in throttle for the M15 Omori ``curve_fit`` step in the replay
# backtester. Default of 0.0 means "no throttle, refit per tick" — the live
# pipeline and the legacy bit-identical replay both use 0.0 so behaviour is
# unchanged. When the replay CLI is invoked with ``--fast-omori`` and no
# explicit value, this constant is used as the refit interval (seconds of
# event time between two ``curve_fit`` calls on the same mainshock).
OMORI_REFIT_SECONDS: Final[float] = 30.0

# ═══════════════════════════════════════════════════════════════════
# M16: TFSAX + Smith-Waterman Alignment (PRD M16)
# ═══════════════════════════════════════════════════════════════════
TFSAX_ALPHABET_SIZE: Final[int] = 5  # |A| = 5
TFSAX_SEGMENT_LENGTH: Final[int] = 1440  # 24h × 1-min-Returns
TFSAX_HISTORY_YEARS: Final[int] = 5  # 5y Bybit-Historie
TFSAX_MATCH_SCORE_THRESHOLD: Final[float] = 0.75  # normalisiert > 0.75
TFSAX_TOP_K_MATCHES: Final[int] = 10  # Top-k Matches

# ═══════════════════════════════════════════════════════════════════
# M17: Renyi-Transfer-Entropy Lead-Lag (PRD M17)
# ═══════════════════════════════════════════════════════════════════
RENYI_Q: Final[float] = 2.0  # q > 1 für Tail-Gewichtung
RENYI_WINDOW_HOURS: Final[int] = 4  # Rolling 4h
RENYI_TE_THRESHOLD: Final[float] = 0.05  # T > 0.05 Bit
RENYI_LAG_SECONDS: Final[tuple[int, int]] = (30, 60)  # BTC→Alt Lag

# ═══════════════════════════════════════════════════════════════════
# M18: PatchTST Funding-Cycle-Forecast (PRD M18)
# ═══════════════════════════════════════════════════════════════════
PATCHTST_PATCH_LENGTH: Final[int] = 16  # P = 16
PATCHTST_STRIDE: Final[int] = 8  # S = 8
PATCHTST_LOOKBACK: Final[int] = 512  # L = 512
PATCHTST_N_LAYERS: Final[int] = 4  # Encoder 4 Layers
PATCHTST_D_MODEL: Final[int] = 256  # 256-dim
PATCHTST_TRAIN_MONTHS: Final[int] = 36  # 3y Training
PATCHTST_FORECAST_HORIZON_MIN: Final[int] = 30  # 30 min vor Settlement
PATCHTST_DIR_ACCURACY_MIN: Final[float] = 0.55  # ≥ 55%

# ═══════════════════════════════════════════════════════════════════
# M19: TimesNet 2D-Periodicity (PRD M19)
# ═══════════════════════════════════════════════════════════════════
TIMESNET_TOP_K_PERIODS: Final[int] = 3  # Top-3 FFT-Frequenzen
TIMESNET_EXPECTED_PERIODS_H: Final[tuple[int, ...]] = (8, 24, 168)
TIMESNET_FORECAST_HORIZON_H: Final[int] = 1  # 1h-Forecast
TIMESNET_KLINE_INTERVAL: Final[str] = "5"  # 5-min-Kline

# ═══════════════════════════════════════════════════════════════════
# M20: MOMENT Foundation Model (PRD M20)
# ═══════════════════════════════════════════════════════════════════
MOMENT_MODEL_NAME: Final[str] = "AutonLab/MOMENT-1-base"
MOMENT_FORECAST_HORIZON_MIN: Final[int] = 60  # 60-min-Horizon
MOMENT_MASE_THRESHOLD: Final[float] = 1.0  # MASE < 1.0 zero-shot
MOMENT_USE_LORA: Final[bool] = True  # LoRA statt full fine-tune

# ═══════════════════════════════════════════════════════════════════
# M21: Long/Short-Ratio Smart-Money-Divergenz (PRD M21)
# ═══════════════════════════════════════════════════════════════════
LS_RATIO_POLL_SECONDS: Final[int] = 300  # alle 5 min pollen
LS_RATIO_PERIOD: Final[str] = "1h"  # REST period=1h
LS_RATIO_DIVERGENCE_THRESHOLD: Final[float] = 0.25  # |buyRatio - 0.5| > 0.25
LS_RATIO_HIT_RATE_MIN: Final[float] = 0.54  # ≥ 54%

# ═══════════════════════════════════════════════════════════════════
# M22: Funding-Rate-Clamp Pressure-Release (PRD M22)
# ═══════════════════════════════════════════════════════════════════
PRESSURE_ENTRY_WINDOW_MINUTES: Final[int] = 30  # T - t < 30 min
PRESSURE_ZSCORE_THRESHOLD: Final[float] = 2.0  # |Pressure| > 2σ
PRESSURE_ROLLING_HOURS: Final[int] = 24  # Rolling 24h-σ
PRESSURE_EXIT_MINUTES_POST_SETTLEMENT: Final[int] = 10  # T + 10 min
PRESSURE_SHARPE_MIN: Final[float] = 1.5  # PRD: Sharpe ≥ 1.5
PRESSURE_HIT_RATE_MIN: Final[float] = 0.56  # PRD: ≥ 56%
PRESSURE_MAX_DD: Final[float] = 0.10  # PRD: < 10%

# ═══════════════════════════════════════════════════════════════════
# M23: Mark-Index Basis Settlement Convergence (PRD M23)
# ═══════════════════════════════════════════════════════════════════
BASIS_LONG_THRESHOLD: Final[float] = -0.0008  # Basis < -0.08% → Long
BASIS_SHORT_THRESHOLD: Final[float] = 0.0008  # Basis > +0.08% → Short
BASIS_ENTRY_WINDOW_MINUTES: Final[int] = 60  # T - t < 1h
BASIS_HIT_RATE_MIN: Final[float] = 0.58  # PRD: ≥ 58%
BASIS_SHARPE_MIN: Final[float] = 1.5  # PRD: ≥ 1.5

# ═══════════════════════════════════════════════════════════════════
# M24: Kalman-Funding-Premium-Decomposition (PRD M24)
# ═══════════════════════════════════════════════════════════════════
KALMAN_SENTIMENT_ZSCORE: Final[float] = 2.0  # |sentiment| > 2σ
KALMAN_SHARPE_MIN: Final[float] = 1.0  # PRD: Sharpe ≥ 1.0

# ═══════════════════════════════════════════════════════════════════
# M25: Kyle's Lambda Adverse Selection (PRD M25)
# ═══════════════════════════════════════════════════════════════════
KYLE_ROLLING_TRADES: Final[int] = 100  # OLS über letzte 100 Trades
KYLE_QUANTILE_THRESHOLD: Final[float] = 0.95  # λ > Q95(λ_30d)
KYLE_LOOKBACK_DAYS: Final[int] = 30  # 30d-Quantil
KYLE_LOSS_REDUCTION_MIN: Final[float] = 0.30  # PRD: ≥ 30%

# ═══════════════════════════════════════════════════════════════════
# M26: SIR-Kompartiment-Liquidations-Contagion (PRD M26)
# ═══════════════════════════════════════════════════════════════════
SIR_RECAL_DAYS: Final[int] = 30  # Rolling 30d β,γ-Kalibrierung
SIR_R0_CASCADE_THRESHOLD: Final[float] = 1.0  # R₀ > 1 → Kaskade
SIR_LEAD_TIME_MINUTES: Final[int] = 5  # ≥ 5 min Vorlauf
SIR_DETECTION_RATE: Final[float] = 0.70  # PRD: 70% der Mainshocks

# ═══════════════════════════════════════════════════════════════════
# BACKTESTER (PRD Abschnitt 8, 9)
# ═══════════════════════════════════════════════════════════════════
WF_TRAIN_DAYS: Final[int] = 30  # Walk-Forward Train-Window
WF_TEST_DAYS: Final[int] = 7  # Walk-Forward Test-Window
WF_EMBARGO_MINUTES: Final[int] = 30  # Embargo zwischen Train/Test
WF_MIN_SHARPE: Final[float] = 1.0  # Minimum Sharpe für Validierung
WF_PARAM_ROBUSTNESS_PCT: Final[float] = 0.20  # ±20% Robustheit
WF_ROBUSTNESS_RETAIN: Final[float] = 0.50  # Sharpe > 50% Mid-Perf
WF_HOLDOUT_FRACTION: Final[float] = 0.30  # 30% Hold-Out
BACKTEST_DATA_MONTHS: Final[int] = 6  # 6 M Standard-Backtest

# ═══════════════════════════════════════════════════════════════════
# HARDWARE (PRD Abschnitt 9.4)
# ═══════════════════════════════════════════════════════════════════
GPU_VRAM_GB: Final[int] = 16  # RTX 5060 Ti
GPU_CUDA_VERSION: Final[str] = "12.4"

# ═══════════════════════════════════════════════════════════════════
# STRATEGY PARAMETERS (PRD Abschnitt 7)
# ═══════════════════════════════════════════════════════════════════
# Strategie 1: Seismischer Cascade Detector
S1_RHO_ENTRY: Final[float] = 0.85  # ρ(Φ) > 0.85
S1_RHO_EXIT: Final[float] = 0.50  # ρ(Φ) < 0.5
S1_B_ZSCORE: Final[float] = 2.0  # b < b̄_30d - 2σ
S1_OMORI_DECAY_FACTOR: Final[float] = 5.0  # t > 5·c → Exit

# Iter-4 Push A: opt-in rho-distribution instrumentation. Default off ->
# the histogram path is dead code and the strategy has zero overhead.
S1_RHO_INSTRUMENT_ENABLED: bool = False
S1_RHO_INSTRUMENT_MAXLEN: int = 100_000

# Strategie 2: Entropie-Momentum
S2_ENTROPY_ZSCORE: Final[float] = 2.0  # H < Median - 2σ
S2_PRESSURE_DISSIPATION: Final[float] = 0.0001  # |P - F| < 0.01%
# Direction-inversion flags (debug/research; default False = current behavior).
# When True the corresponding strategy flips the sign of the direction it
# would enter with. Used to test the hypothesis that the PRD direction
# mapping is inverted vs. the actual edge.
S2_INVERT_DIRECTION: bool = False

# Iter-4 Push A: opt-in maker-only fill model for S2. Default False ->
# bit-identical taker-fee behavior. When True, S2 trade fees are 0.0
# (worst-case-for-our-hypothesis vs. the ~-2.5 bps Bybit maker rebate;
# if S2 still loses with zero fees, it would still lose with rebates).
# S3 fees are unaffected; this is strictly an S2 forensic.
S2_MAKER_ONLY: bool = False

# Strategie 3: Pre-Settlement Pressure-Release
S3_PRESSURE_QUANTILE: Final[float] = 0.90  # |Pressure| > Q90
S3_EXIT_FUNDING_BAND: Final[tuple[float, float]] = (-0.0001, 0.0001)
S3_INVERT_DIRECTION: bool = False

# Iter-4 Push A: bounded-loss exits for S3. Both default off ->
# bit-identical to iter-3 behavior. Enable via CLI flags
# --s3-time-stop / --s3-hard-stop on the replay drivers.
S3_TIME_STOP_ENABLED: bool = False
S3_TIME_STOP_MS: int = 120_000              # 120 s wall-clock cap
S3_HARD_STOP_ENABLED: bool = False
S3_HARD_STOP_BPS: float = -30.0             # -30 bps mark-to-market floor

# iter-5 T2: friction projection used by the hard-stop. Bybit taker = 5.5 bps
# per leg as of 2026-06 (1 bps = 0.0001). Set per-leg (not round-trip) so the
# arithmetic at the call-site is `mtm_bps - 2 * S3_FRICTION_BPS_PER_LEG`, which
# reads as "subtract the entry leg already paid plus the exit leg about to
# be paid". Mutable (not Final) so live runners can override at startup.
S3_FRICTION_BPS_PER_LEG: float = 5.5

# Strategie 4: Pattern × Foundation Ensemble
S4_CONSENSUS_MIN_MODELS: Final[int] = 2  # ≥ 2 von 3
S4_FORECAST_PEARSON_MIN: Final[float] = 0.6  # Pearson > 0.6
S4_FORECAST_RETURN_MIN: Final[float] = 0.005  # > 0.5%

# Strategie 5: Cross-Sectional Ergodicity Reversion
S5_Z_ENTRY: Final[float] = 2.5  # |Z| > 2.5
S5_Z_EXIT: Final[float] = 0.5  # |Z| < 0.5
S5_TIME_STOP_HOURS: Final[int] = 24  # Time-Stop 24h

# ═══════════════════════════════════════════════════════════════════
# LOGGING (PRD Abschnitt 8)
# ═══════════════════════════════════════════════════════════════════
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT: Final[str] = (
    "%(asctime)s.%(msecs)03d | %(levelname)-8s | "
    "%(name)-30s | %(message)s"
)
LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

# ═══════════════════════════════════════════════════════════════════
# RANDOM SEED (PRD Abschnitt 9.1)
# ═══════════════════════════════════════════════════════════════════
RANDOM_SEED: Final[int] = 42

# ═══════════════════════════════════════════════════════════════════
# EXECUTION (Live-Runner + Order-Ausführung)
# ═══════════════════════════════════════════════════════════════════
# Master-Schalter: wenn False, werden NIEMALS Orders gesendet (nur geloggt).
EXECUTION_ENABLED: bool = os.getenv("EXECUTION_ENABLED", "false").lower() == "true"
# Notional pro Paper-Trade in USD (Order-Größe = NOTIONAL / Preis).
EXECUTION_ORDER_USD: float = float(os.getenv("EXECUTION_ORDER_USD", "100.0"))
# Hebel für das Symbol (wird einmalig gesetzt).
EXECUTION_LEVERAGE: int = int(os.getenv("EXECUTION_LEVERAGE", "1"))
# Pipeline-Throttle: minimaler Abstand zwischen zwei Pipeline-Läufen (Sekunden).
PIPELINE_INTERVAL_SECONDS: float = float(os.getenv("PIPELINE_INTERVAL_SECONDS", "1.0"))
# Daten-Persistenz: schreibt Live-Ticks (Ticker/Trades/Liquidationen) in DuckDB,
# damit später Microstructure-Strategien (S1/S2) backtestbar werden.
PERSIST_ENABLED: bool = os.getenv("PERSIST_ENABLED", "false").lower() == "true"
PERSIST_FLUSH_SECONDS: float = float(os.getenv("PERSIST_FLUSH_SECONDS", "5.0"))
# Optionale L2-Orderbook-Persistenz (Opt-in, ergänzend zu PERSIST_ENABLED).
# Default OFF, da PRD Abschnitt 3 für orderbook.50-Deltas ~500 MB/Tag pro Symbol
# schätzt. Im Snapshot-Modus mit 1-s-Intervall sinkt das auf ~5-15 MB/Tag pro
# Symbol (40 Zeilen pro Snapshot × 86400 Snapshots × ~50 B/Zeile ≈ 170 MB/Tag
# unkomprimiert, deutlich weniger nach Parquet+ZSTD).
PERSIST_ORDERBOOK: bool = os.getenv("PERSIST_ORDERBOOK", "false").lower() == "true"
PERSIST_ORDERBOOK_DEPTH: int = int(os.getenv("PERSIST_ORDERBOOK_DEPTH", "20"))
PERSIST_ORDERBOOK_SNAPSHOT_SECONDS: float = float(
    os.getenv("PERSIST_ORDERBOOK_SNAPSHOT_SECONDS", "1.0")
)
# Optionaler JSON-Heartbeat-Export für das Streamlit-Dashboard.
# Default OFF, ändert das Verhalten bestehender Tests nicht.
ENABLE_HEARTBEAT_FILE: bool = (
    os.getenv("ENABLE_HEARTBEAT_FILE", "false").lower() == "true"
)
# REST recv_window (ms) für signierte Requests.
BYBIT_RECV_WINDOW_MS: int = int(os.getenv("BYBIT_RECV_WINDOW_MS", "5000"))
# Signierte REST-Endpoints (Trade/Account).
REST_ORDER_CREATE: Final[str] = "/v5/order/create"
REST_POSITION_LIST: Final[str] = "/v5/position/list"
REST_WALLET_BALANCE: Final[str] = "/v5/account/wallet-balance"
REST_SET_LEVERAGE: Final[str] = "/v5/position/set-leverage"
REST_INSTRUMENTS: Final[str] = "/v5/market/instruments-info"

# ═══════════════════════════════════════════════════════════════════
# RISK BUDGET (Live-Risiko-Schicht, opt-in)
# ═══════════════════════════════════════════════════════════════════
# Master-Schalter: aktiviert die Live-Risiko-Schicht (Max-DD, Daily-Loss,
# Vol-Scaling) im LiveRunner. Default OFF → bestehendes Verhalten unverändert.
RISK_BUDGET_ENABLED: bool = (
    os.getenv("RISK_BUDGET_ENABLED", "false").lower() == "true"
)
# Daily-Loss-Limit (negative Fraktion, z. B. -0.03 = -3 %).
RISK_DAILY_LOSS_PCT: float = float(os.getenv("RISK_DAILY_LOSS_PCT", "-0.03"))
# Max-Drawdown vom Peak (negative Fraktion, z. B. -0.15 = -15 %).
RISK_MAX_DRAWDOWN_PCT: float = float(os.getenv("RISK_MAX_DRAWDOWN_PCT", "-0.15"))
# Opt-in Vol-Scaling der Order-Größe basierend auf realisierter Vol.
RISK_VOL_SCALING_ENABLED: bool = (
    os.getenv("RISK_VOL_SCALING_ENABLED", "false").lower() == "true"
)
# Ziel-Vol-Beitrag in Basispunkten — bei höherer realisierter Vol wird
# die Order-Größe verkleinert.
RISK_VOL_TARGET_BPS: float = float(os.getenv("RISK_VOL_TARGET_BPS", "50.0"))
# Anzahl der jüngsten Preis-Bars für die Realized-Vol-Schätzung.
RISK_VOL_LOOKBACK_BARS: int = int(os.getenv("RISK_VOL_LOOKBACK_BARS", "60"))
# Persistenter Zustand des Risiko-Budgets (JSON).
RISK_STATE_PATH: Path = Path(
    os.getenv("RISK_STATE_PATH", str(DATA_DIR / "risk_state.json"))
)
# Einmal-Reset-Knopf: setzt blocked_reason zurück (manuell aktivieren).
RISK_BUDGET_RESET: bool = (
    os.getenv("RISK_BUDGET_RESET", "false").lower() == "true"
)
# Intervall (Sekunden) zwischen periodischen Equity-Updates im LiveRunner.
RISK_EQUITY_POLL_SECONDS: float = float(
    os.getenv("RISK_EQUITY_POLL_SECONDS", "30.0")
)

# ═══════════════════════════════════════════════════════════════════
# MULTI-SYMBOL RUNNER (parallele Datensammlung mehrerer Symbole)
# ═══════════════════════════════════════════════════════════════════
# Master-Schalter: aktiviert MultiSymbolRunner statt single-symbol LiveRunner.
MULTI_SYMBOL_RUNNER_ENABLED: bool = (
    os.getenv("MULTI_SYMBOL_RUNNER_ENABLED", "false").lower() == "true"
)


def _parse_multi_symbols(raw: str) -> list[str]:
    """Parsed komma-getrennte Symbol-Liste, leerer Input -> Universe-Default."""
    if not raw.strip():
        return list(MULTI_SYMBOL_UNIVERSE)
    out: list[str] = []
    seen: set[str] = set()
    for tok in raw.split(","):
        sym = tok.strip().upper()
        if sym and sym not in seen:
            seen.add(sym)
            out.append(sym)
    return out


MULTI_SYMBOLS: list[str] = _parse_multi_symbols(os.getenv("MULTI_SYMBOLS", ""))
# Symbol, für das im Multi-Modus Order-Execution erlaubt ist (Default: Primary).
MULTI_EXECUTION_SYMBOL: str = os.getenv("MULTI_EXECUTION_SYMBOL", PRIMARY_SYMBOL)

# ═══════════════════════════════════════════════════════════════════
# WS RECONNECT (PRD Abschnitt 9.2)
# ═══════════════════════════════════════════════════════════════════
WS_RECONNECT_DELAY_SECONDS: Final[float] = 1.0
WS_RECONNECT_MAX_DELAY_SECONDS: Final[float] = 60.0
WS_RECONNECT_BACKOFF_FACTOR: Final[float] = 2.0
WS_PING_INTERVAL_SECONDS: Final[int] = 20
WS_PING_TIMEOUT_SECONDS: Final[int] = 10

# ═══════════════════════════════════════════════════════════════════
# SPEICHER-SCHÄTZUNGEN (PRD Abschnitt 3, informativ)
# ═══════════════════════════════════════════════════════════════════
# Tickers + Funding + OI + L/S-Ratio: ~150 MB/Tag (Parquet+ZSTD)
# publicTrade: ~200 MB/Tag
# orderbook.50 (Deltas): ~500 MB/Tag
# allLiquidation: ~5 MB/Tag
# Gesamt 1 Symbol: ~300 GB/Jahr roh, ~80 GB komprimiert
# 10 Symbole: 1.5-3 TB roh
