# WP-1 · L2-Pre-Flight-Zensus (read-only, KAPITALFREI)

- **Erzeugt:** 2026-08-14T08:37:57+00:00 (UTC)
- **Streams entdeckt:** orderbook
- **Sampling:** jeder 14. Tag + erster/letzter

> Entscheidungsregel (Synthese §3): Faellt der Zensus gegen die Snapshot+Delta-Lesart aus, wird L2-TILT NICHT registriert.

## BTCUSDT

### `orderbook` — 964 Tage (2023-01-18..2026-08-13), 70 gesampelt, 0 Fehler

| Regime (topic · type) | Tage (gesampelt) | erster..letzter | Zeilen | MB | Tiefe b min..max | Seq-Brueche / geprueft |
|---|---:|---|---:|---:|---|---:|
| `orderbook.500.BTCUSDT - delta` | 66 | 2023-01-18..2025-08-13 | 56695351 | 84733.4 | 0..1000 | 66 / 56695486 |
| `orderbook.500.BTCUSDT - snapshot` | 66 | 2023-01-18..2025-08-13 | 135 | 2.9 | 500..500 | 66 / 56695486 |
| `orderbook.1000.BTCUSDT - delta` | 4 | 2026-06-22..2026-08-13 | 787944 | 1742.4 | 0..1393 | 2 / 787951 |
| `orderbook.1000.BTCUSDT - snapshot` | 4 | 2026-06-22..2026-08-13 | 7 | 0.3 | 1000..1000 | 2 / 787951 |

## ETHUSDT

### `orderbook` — 533 Tage (2023-01-18..2026-08-13), 39 gesampelt, 0 Fehler

| Regime (topic · type) | Tage (gesampelt) | erster..letzter | Zeilen | MB | Tiefe b min..max | Seq-Brueche / geprueft |
|---|---:|---|---:|---:|---|---:|
| `orderbook.500.ETHUSDT - delta` | 35 | 2023-01-18..2024-05-10 | 29751490 | 25814.1 | 0..1000 | 37 / 29751564 |
| `orderbook.500.ETHUSDT - snapshot` | 35 | 2023-01-18..2024-05-10 | 74 | 1.4 | 500..500 | 37 / 29751564 |
| `orderbook.1000.ETHUSDT - delta` | 4 | 2026-06-19..2026-08-13 | 1284968 | 2261.3 | 0..1152 | 32 / 1284981 |
| `orderbook.1000.ETHUSDT - snapshot` | 4 | 2026-06-19..2026-08-13 | 13 | 0.5 | 1000..1000 | 32 / 1284981 |

*Erzeugt von `scripts/l2_census.py`. Kein Byte Extraktion — nur Zaehlung/Discovery. Die L2-TILT-Registrierungsentscheidung faellt der Orchestrator gegen dieses Dokument.*