# E-15-Auswertung (H-01 · S3 Pre-Settlement, iter-5)

- **Hypothese:** H-01 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-06-12T11:53:52+00:00 (UTC)
- **Input `results_path`:** `E:\Claude\Projects\scinance\edge_research_framework\results\replay_all_results.json`
- **Input `trades_path`:** `E:\Claude\Projects\scinance\edge_research_framework\results\trades_iter4\trades_all.csv`
- **Input `baseline_results`:** `E:\Claude\Projects\scinance\edge-reconciliation\input\iter4_raw\replay_all_results.json`
- **Input `baseline_trades`:** `E:\Claude\Projects\scinance\edge-reconciliation\input\iter4_raw\trades_all.csv`

## Gate-Urteil: **DROP**

> Maschinelles Urteil exakt gegen die vorregistrierten H-01-Tore. Verbindlich wird es erst nach gate-auditor-Pruefung (T2 auf Echtdaten).

| Kriterium | Registry-Text (woertlich) | Operationalisierung | Messwert | Bestanden |
|---|---|---|---|---|
| `fix_time_stop_count` | time_stop_exceeded-Count: 1 -> erwartet ~60-70 (Fix-Wirksamkeit) | pass wenn Count in [54, 77] (= 60-70 +-10% fuer '~'); None wenn diagnostics fehlen | 1 | nein |
| `fix_n_over_120s` | n>120s-Trades: 68 -> erwartet ~0 | pass wenn Count <= 2 ('~0' mit Tick-Granularitaets-Toleranz: Time-Stop feuert erst auf dem ersten Tick NACH 120s) | 68 | nein |
| `fix_n_below_minus_30bps` | n<-30bps-Trades: 33 -> erwartet ~0 | pass wenn Count <= 2 ('~0') | 33 | nein |
| `weiter_net_edge` | WEITER: aggregierte Netto-Edge >= -5 bps UND E-17-Divergenz geklaert | Teilkriterium 1: mean pnl_bps (netto, trade-gewichtet ueber alle S3-Trades) >= -5.0 | -16.81 | nein |
| `weiter_e17_resolved` | WEITER: aggregierte Netto-Edge >= -5 bps UND E-17-Divergenz geklaert | Teilkriterium 2: E-17-Check resolved == true (false/inconclusive blockieren WEITER) | ja | ja |
| `drop_net_edge` | DROP: aggregierte Netto-Edge <= -10 bps | DROP wenn mean pnl_bps (netto) <= -10.0 | -16.81 | ja |

**Fix-Wirksamkeit gesamt:** nein (informativ — nicht urteils-tragend, s. Operationalisierung)

## S3-Metriken (netto = inkl. Fees, raw = Fees zurueckgerechnet)

| Symbol | n | mean bps (netto) | median bps (netto) | mean bps (raw) | n>120s | n<-30bps | time_stop | hard_stop | max Dauer (s) | worst trade (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BNBUSDT | 19 | -21.08 | -20.08 | -10.09 | 14 | 8 | 1 | 6 | 2124.9 | -56.60 |
| BTCUSDT | 62 | -16.57 | -16.82 | -5.58 | 14 | 5 | 0 | 2 | 561.4 | -47.70 |
| ETHUSDT | 50 | -16.34 | -15.80 | -5.34 | 13 | 7 | 0 | 0 | 1099.1 | -37.72 |
| SOLUSDT | 36 | -18.20 | -17.78 | -7.20 | 13 | 9 | 0 | 3 | 1342.1 | -48.93 |
| XRPUSDT | 46 | -14.78 | -16.22 | -3.79 | 14 | 4 | 0 | 2 | 1998.7 | -46.39 |
| **Aggregat** | 213 | -16.81 | -16.46 | -5.81 | 68 | 33 | 1 | 13 | 2124.9 | -56.60 |

Worst Trade gesamt: BNBUSDT -56.60 bps (-3.40 USD, 1204.1 s, entry_ts=1780559553318)

## E-17-Klaerung: `ja`

Aktueller Lauf und Baseline sind konsistent: n_trades-Ratio 1.00 (Band (0.8, 1.25)), |total_return|-Ratio 1.00 (Band (0.5, 2.0)). Die registrierte ~3.2x-Divergenz reproduziert sich nicht. Endgueltiges E-17-Urteil faellt der gate-auditor gegen die Registry; dieser Check liefert die Datenbasis.

- n_trades-Ratio (aktuell/Baseline): 1.00
- |total_return|-Ratio: 1.00
- total_return-Gap: 0.00 USD

---
*Erzeugt von `scripts/evaluate_e15.py` (WP-1, rein lesend auf den Replay-Artefakten). Endgueltiges Gate-Urteil: gate-auditor gegen H-01.*
