# Kestrel-AI — Research Notes

Final write-up of what was built, what was tested, and what we learned over three months of work on the PRD-v1.4 deep-learning trading model for Bybit perpetual futures.

The headline: **none of the direction-prediction approaches generated alpha at retail trading costs**. Volatility forecasting works (Test R² = 0.25), pair trading on majors has a fragile small edge with maker execution, and cross-venue funding-arbitrage between Bybit and Binance is sub-edge for retail.

That's not a wasted three months — it's an exhaustive answer to a well-posed question, with a complete reproducible pipeline.

## Table of contents

1. [Project goal](#project-goal)
2. [What was built](#what-was-built)
3. [Empirical results](#empirical-results)
4. [What works (and how to use it)](#what-works-and-how-to-use-it)
5. [What doesn't work and why](#what-doesnt-work-and-why)
6. [Honest deployment guidance](#honest-deployment-guidance)
7. [Reproducibility commands](#reproducibility-commands)
8. [Open follow-ups](#open-follow-ups)

## Project goal

Build a deep-learning trading model per the PRD v1.4 spec — Bybit perpetual futures, 10 majors, LightGBM as default primary, TFT challenger, Triple-Barrier labelling, MODWT wavelet features, Polymarket sentiment integration, cross-venue funding + OI features. Target: a deployable system with measurable edge net of fees.

## What was built

| Phase | Module | Status |
|-------|--------|--------|
| P1 Live WS ingestion | `kestrel.data.bybit.ws_client`, `kestrel.data.storage.parquet_writer` | ✅ Production-grade with auto-reconnect + atomic flush |
| P1 Historical backfill | `scripts/backfill.py` + `kestrel.data.historical.*` | ✅ Bybit klines + trade archive + Bybit/Binance REST funding/OI |
| P2 Features | `kestrel.features.bars`, `kestrel.features.wavelets`, `kestrel.features.cross_venue`, `kestrel.features.polymarket` | ✅ 1s + 1m bars, MODWT, cross-venue, sentiment |
| P3-1 Feature cache | `kestrel.features.cache` | ✅ Parquet-cached per (symbol, date) |
| P3-2 Triple-Barrier labels | `kestrel.features.labels` | ✅ ATR-scaled barriers + label-cache |
| P3-3 PyTorch dataset | `kestrel.training.dataset` | ✅ 256-bar sliding window, per-symbol chronological 60/20/20 split |
| P3-4 LightGBM baseline | `kestrel.training.lightgbm_baseline` | ✅ Direction (3-class + binary) + volatility regression |
| P3-5 Backfill orchestrator | `scripts/backfill.py` | ✅ 10 symbols × 91 days, ~24 GiB cache built in 65min |
| P3-6 TFT challenger | `kestrel.training.tft` | ✅ Transformer encoder, bf16 AMP, RTX 5060 Ti (Blackwell sm_120) |
| P3-7 Vol-regime classifier | `kestrel.features.regime` | ✅ Per-symbol quantile bins, training-only fit |
| P3-9 Backtest engines | `kestrel.backtest.engine`, `kestrel.backtest.pair_strategy`, `kestrel.backtest.funding_strategy` | ✅ Single-symbol, pair-trading (static + walk-forward), funding-arb |
| Ops | `scripts/check_health.py`, `scripts/daily_report.py`, `scripts/compact_parquet.py --loop`, `docs/production.md` | ✅ Windows Task Scheduler runbook |

Total: ~30 modules, ~6,500 LOC of source + 4,300 LOC of tests. 200+ tests passing.

## Empirical results

All numbers from the **April 2026 test window**, after training/screening on Jan-March 2026.

### Direction prediction

LightGBM and TFT both fail to beat coin-flip on next-bar direction:

| Model | Horizon | Train F1 | Test AUC | Verdict |
|-------|---------|---------:|---------:|---------|
| LightGBM 3-class | 1h | 0.745 | 0.658 | Overfit, no generalisation |
| LightGBM binary, reg | 1h | 0.336 | 0.504 | Underfit, stuck at random |
| LightGBM binary, mod | 1h | n/a | 0.504 | Random |
| **TFT binary** | **1h** | n/a | **0.495** | **Random** |
| LightGBM binary | 4h | n/a | 0.503 | Random |

Feature-importance analysis showed the model could find regime info (funding_rate, OI level) but no information that helps with direction. **The 36-feature 1m-snapshot pipeline structurally cannot predict direction** at 1h or 4h horizons for Bybit majors — consistent with market efficiency on those timescales.

### Volatility prediction

Same 36-feature pipeline, regression target = `log(realised_vol_60m)`. **This works:**

| Split | RMSE | MAE | R² | Pearson |
|-------|-----:|----:|---:|--------:|
| Train | 0.279 | 0.210 | 0.701 | 0.838 |
| Val | 0.398 | 0.315 | 0.231 | 0.594 |
| **Test** | **0.470** | **0.326** | **0.249** | **0.578** |

Feature importance ranks `atr_60` first (35.8% gain) followed by trade-flow features (38%). Volatility clustering is real and captured cleanly. **This is the one deployable predictive signal in the codebase.**

### Pair trading (price cointegration)

22 cointegrated pairs found on Jan-March training, backtested on April:

| Setup | Mean Return | Mean Sharpe | Positive Sharpe |
|-------|------------:|------------:|----------------:|
| Static, taker (5.5 bp) | -39.46% | -20.78 | 0/22 |
| Static, taker + cooldown + filter | -22.00% | -18.23 | 0/14 |
| Static, **maker** (1.0 bp) + filter | -2.75% | -1.35 | **3/14** |
| Walk-forward + DD-stop, taker | -2.26% | -6.82 | 0/14 |
| Walk-forward + DD-stop, **maker** | -2.07% | -0.48 | **4/14** |

Walk-forward refit revealed that **most pairs only stayed cointegrated for 0-15 days out of 30** — `BTCUSDT-ETHUSDT` passed only 2/30 daily refits, `ETHUSDT-LINKUSDT` 0/30. Cointegration between crypto majors is not persistent.

The 4 maker-fee winners (best Sharpe):
- `LINKUSDT-XRPUSDT`: +3.90%, Sharpe +4.47
- `AVAXUSDT-ETHUSDT`: +2.73%, Sharpe +4.02
- `AVAXUSDT-LINKUSDT`: +1.92%, Sharpe +3.04
- `BTCUSDT-XRPUSDT`: +0.12%, Sharpe +0.25

Two of three top winners involve XRP — April had XRP structurally diverging from trending majors, classic mean-reversion setup. Generalisation to other months is unknown.

### Cross-venue funding arbitrage

Bybit vs Binance funding spreads on the 8 backfilled majors over April:

| Symbol | Mean | Std | abs95 |
|--------|----:|----:|------:|
| BTCUSDT | +0.10 bp | 0.46 bp | 0.85 bp |
| ETHUSDT | +0.03 bp | 0.52 bp | 1.01 bp |
| SOLUSDT | +0.19 bp | 0.61 bp | 1.25 bp |
| BNBUSDT | +0.20 bp | 0.59 bp | 1.00 bp |
| XRPUSDT | +0.22 bp | 0.41 bp | 0.88 bp |
| AVAXUSDT | +0.13 bp | 0.48 bp | 1.01 bp |
| LINKUSDT | -0.05 bp | 0.49 bp | 1.00 bp |
| TONUSDT | -0.03 bp | 0.46 bp | 0.95 bp |

Backtest result:

| Fee | Mean Return | Mean Sharpe | Positive |
|-----|------------:|------------:|---------:|
| Taker 5.5 bp | -1.28% | -13.37 | 0/10 |
| Maker 1.0 bp | -0.19% | -10.64 | 0/10 |

**Spreads are <1 bp on average; round-trip taker cost is 22 bp.** No retail-grade execution can be profitable here — the venues' own internal arbitrageurs already tighten the spreads at the bp level.

## What works (and how to use it)

### 1. Volatility forecasting — deployable as monitoring

The LightGBM regression model produces calibrated forward-looking volatility forecasts for every symbol every minute. Test R² = 0.25 over 30 days of out-of-sample crypto data is solid.

**Use cases:**
- Risk gauge: "is the next hour likely to be quieter or wilder than now?"
- Position sizing for other strategies (inverse-vol sizing)
- Daily-report dashboards
- Stop-loss calibration (e.g. stop = entry ± 1.5 × predicted_vol × close)

**What it cannot do:** generate alpha on its own. Backtests showed that pure vol-targeting underperformed buy-and-hold on a bullish April. Vol-prediction is a **risk** signal, not a **direction** signal.

### 2. The full data + features + labels pipeline

- 1-minute label cache for 10 symbols × 91 days, with Triple-Barrier labels, vol target, vol regime, predicted log-RV, MODWT wavelets, cross-venue features all on disk.
- Live ingestion + compaction + daily report + health watchdog wired up for Windows Task Scheduler in `docs/production.md`.
- 70+ tests cover the critical correctness invariants (no-lookahead, label leakage, NaN handling, fee accounting, Walk-forward refit).

This is the longest-lived asset of the project. Even if no strategy ships from here, the data pipeline is reusable for any future research.

## What doesn't work and why

### Direction prediction at 1m-snapshot resolution

The 36-feature snapshot has no information about *where* the price is going next. The TFT challenger with attention over a 256-bar history, after fp16-AMP training on a Blackwell GPU, scores the same Test AUC as the LightGBM single-tree baseline: 0.50.

**Why:** the predictive content of OHLC + trade aggregates + MODWT wavelets + funding/OI is exhausted by regime classification ("we are in a high-vol period") and provides no edge on direction. This is what the efficient-markets hypothesis predicts on liquid majors at minute granularity, and the data confirms it.

The escape: real **Microstructure features** — actual L2 order-book reconstruction at tick frequency, sub-second order-flow imbalance, queue position, footprint analysis. The current pipeline captures 1-minute aggregates of those quantities, which is too coarse. Building this requires multi-month live tick-level data accumulation.

### Pair trading on Bybit majors alone

Cointegration is regime-specific. The pairs that pass Engle-Granger on Jan-March only stay cointegrated for half the test month on average. Walk-forward refit recovers some of the lost edge but introduces a tradeoff with sample size (shorter fit windows are noisier).

The 4 maker-fee winners are likely **survivorship bias** — they happened to keep mean-reverting in April but there's no structural reason to expect them to keep doing so. This would need to be verified on multiple months of test data, and even then the per-trade edge is sub-10 bp — wafer-thin under any real-world slippage.

### Cross-venue funding arbitrage

Spreads are <1 bp on average between Bybit and Binance. The cross-venue arbitrageurs are the HFT firms; they price in the differential at the millisecond scale. Retail with 5.5 bp taker fee cannot extract this edge no matter what the threshold.

## Honest deployment guidance

What I would actually deploy if forced to ship from this codebase:

1. **Live WS ingestion**, mainnet, all 10 symbols. The data is valuable raw material for future research and the cost is one workstation running Windows Task Scheduler.

2. **Daily monitoring report** (`scripts/run_daily_pipeline.py`, see `docs/production.md`). Produces a Markdown file every day with the current vol forecast and regime per symbol. Useful as a manual decision-support tool, not as an automated trader.

3. **External health watchdog** (`scripts/check_health.py`) for the ingestion. Hook into any uptime monitor (Healthchecks.io, Uptime Kuma, plain cron + email-on-failure).

What I would **not** deploy:

* Anything that places actual orders. The strategy results don't justify it.
* Pair-trading as a standalone strategy. The fragility is too high.
* Funding-arbitrage on Bybit↔Binance. Spreads are below execution cost.

## Reproducibility commands

For someone picking this up cold, the path from zero to all the results in this document:

```bash
# 0. Setup
git clone <repo> && cd kestrel-ai
uv sync --extra dev --extra exchange --extra features --extra dl --extra ml

# 1. Backfill 3 months of public data (~65 min, ~24 GiB cache)
uv run python scripts/backfill.py --all-symbols \
    --start 2026-01-30 --end 2026-04-30

# 2. Re-label with Triple-Barrier + realised-vol target
uv run python scripts/relabel.py --all-symbols \
    --start 2026-01-30 --end 2026-04-30

# 3. Fit per-symbol vol-regime quantiles on training window
uv run python scripts/build_regime.py --all-symbols \
    --start 2026-01-30 --end 2026-04-30

# 4. Train LightGBM volatility regression (the one signal that works)
uv run python scripts/train_lightgbm.py --all-symbols \
    --start 2026-01-30 --end 2026-04-30 --target volatility

# 5. Apply the model to April for monitoring
uv run python scripts/predict_volatility.py \
    --model-dir models/lightgbm/<run_id> \
    --all-symbols --start 2026-04-01 --end 2026-04-30

# 6. Generate daily monitoring report
uv run python scripts/daily_report.py --all-symbols

# --- Negative results, for completeness ---

# Direction (1h binary, AUC ~0.50)
uv run python scripts/train_lightgbm.py --all-symbols \
    --start 2026-01-30 --end 2026-04-30 --binary

# Pair trading screen + backtest
uv run python scripts/cointegration_screen.py \
    --start 2026-01-30 --end 2026-03-24 \
    --out data/pairs/cointegration_v1.json

uv run python scripts/backtest_pairs.py \
    --pairs data/pairs/cointegration_v1.json \
    --start 2026-04-01 --end 2026-04-30 \
    --walk-forward --drawdown-stop 0.03 --taker-fee-bps 1.0

# Funding-arb backtest
uv run python scripts/backtest_funding_arb.py --all-symbols \
    --start 2026-04-01 --end 2026-04-30 --taker-fee-bps 1.0
```

## Open follow-ups

If anyone picks this up:

1. **Live L2 microstructure data accumulation.** Run the ingestion for 3+ months, then rebuild features from real tick-level Order-Book snapshots (not the 1m aggregates we use today). Retry direction prediction with microsecond OFI, queue depth, footprint. This is the canonical next research step.

2. **Multi-strategy portfolio backtest.** Combine the marginal-positive pair-trading-with-maker-fees outputs (LINK-XRP, AVAX-ETH, AVAX-LINK, BTC-XRP) with vol-target sizing across symbols. Even if each component is fragile, a 4-pair diversified book might compress the tail-risk enough to be deployable. The infrastructure to do this is in `kestrel.backtest`; what's missing is the position-aggregator layer.

3. **HMM-based regime classifier.** The quantile classifier in `kestrel.features.regime` is the simplest workable variant. A 3-state `hmmlearn.GaussianHMM` on the realised-vol series would give smoother regime transitions and a probability distribution over regimes instead of a hard label. PRD §5.4 explicitly mentions HMM; we shipped the simpler version first.

4. **Bigger backfill window.** All conclusions in this document are from one test month (April 2026). A 6-month rolling validation would catch regime-specific artefacts. The backfill code is parallelisable and could probably do a year in a weekend.

5. **Real execution layer.** None of the backtests model order-book impact, partial fills, queue-position dynamics, or maker-vs-taker conversion. If any strategy were to go live, that's where the next code lives.
