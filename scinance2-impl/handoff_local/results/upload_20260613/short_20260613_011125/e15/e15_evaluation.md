# E-15-Auswertung (H-01 · S3 Pre-Settlement, iter-5)

- **Hypothese:** H-01 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-06-13T01:16:26+00:00 (UTC)
- **Input `results_path`:** `E:\Claude\Projects\scinance\edge_research_framework\results\replay_all_results.json`
- **Input `trades_path`:** `E:\Claude\Projects\scinance\edge_research_framework\results\trades_iter5\trades_all.csv`
- **Input `baseline_results`:** `E:\Claude\Projects\scinance\edge-reconciliation\input\iter4_raw\replay_all_results.json`
- **Input `baseline_trades`:** `E:\Claude\Projects\scinance\edge-reconciliation\input\iter4_raw\trades_all.csv`

## Gate-Urteil: **DROP**

> Maschinelles Urteil exakt gegen die vorregistrierten H-01-Tore. Verbindlich wird es erst nach gate-auditor-Pruefung (T2 auf Echtdaten).

| Kriterium | Registry-Text (woertlich) | Operationalisierung | Messwert | Bestanden |
|---|---|---|---|---|
| `fix_time_stop_count` | time_stop_exceeded-Count: 1 -> erwartet ~60-70 (Fix-Wirksamkeit) | pass wenn Count in [54, 77] (= 60-70 +-10% fuer '~'); None wenn diagnostics fehlen | 128 | nein |
| `fix_n_over_120s` | n>120s-Trades: 68 -> erwartet ~0 | pass wenn Count <= 2 ('~0' mit Tick-Granularitaets-Toleranz: Time-Stop feuert erst auf dem ersten Tick NACH 120s) | 129 | nein |
| `fix_n_below_minus_30bps` | n<-30bps-Trades: 33 -> erwartet ~0 | pass wenn Count <= 2 ('~0') | 25 | nein |
| `weiter_net_edge` | WEITER: aggregierte Netto-Edge >= -5 bps UND E-17-Divergenz geklaert | Teilkriterium 1: mean pnl_bps (netto, trade-gewichtet ueber alle S3-Trades) >= -5.0 | -15.47 | nein |
| `weiter_e17_resolved` | WEITER: aggregierte Netto-Edge >= -5 bps UND E-17-Divergenz geklaert | Teilkriterium 2: E-17-Check resolved == true (false/inconclusive blockieren WEITER) | ja | ja |
| `drop_net_edge` | DROP: aggregierte Netto-Edge <= -10 bps | DROP wenn mean pnl_bps (netto) <= -10.0 | -15.47 | ja |

**Fix-Wirksamkeit gesamt:** nein (informativ — nicht urteils-tragend, s. Operationalisierung)

## S3-Metriken (netto = inkl. Fees, raw = Fees zurueckgerechnet)

| Symbol | n | mean bps (netto) | median bps (netto) | mean bps (raw) | n>120s | n<-30bps | time_stop | hard_stop | max Dauer (s) | worst trade (bps) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BNBUSDT | 50 | -14.07 | -15.00 | -3.07 | 40 | 0 | 40 | 0 | 129.1 | -29.93 |
| BTCUSDT | 81 | -15.84 | -16.85 | -4.85 | 24 | 4 | 23 | 2 | 178.4 | -37.85 |
| ETHUSDT | 66 | -16.65 | -16.22 | -5.65 | 19 | 6 | 19 | 3 | 123.3 | -38.06 |
| SOLUSDT | 60 | -16.10 | -17.71 | -5.11 | 25 | 12 | 25 | 7 | 123.6 | -38.10 |
| XRPUSDT | 63 | -14.27 | -16.63 | -3.27 | 21 | 3 | 21 | 3 | 124.4 | -37.05 |
| **Aggregat** | 320 | -15.47 | -16.58 | -4.48 | 129 | 25 | 128 | 15 | 178.4 | -38.10 |

Worst Trade gesamt: SOLUSDT -38.10 bps (-0.26 USD, 101.3 s, entry_ts=1780559929077)

## E-17-Klaerung: `ja`

Trade-Zahlen unterscheiden sich (Ratio 1.50), aber der mittlere Return pro Trade ist konsistent (Ratio 0.83) — Divergenz im total_return ist durch die Trade-Zahl erklaert. Endgueltiges E-17-Urteil faellt der gate-auditor gegen die Registry; dieser Check liefert die Datenbasis.

- n_trades-Ratio (aktuell/Baseline): 1.50
- |total_return|-Ratio: 1.25
- total_return-Gap: -1712.55 USD
- Groesster Symbol-Anteil am Gap: BTCUSDT (96 %)

---
*Erzeugt von `scripts/evaluate_e15.py` (WP-1, rein lesend auf den Replay-Artefakten). Endgueltiges Gate-Urteil: gate-auditor gegen H-01.*
