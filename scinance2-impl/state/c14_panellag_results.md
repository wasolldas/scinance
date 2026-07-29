# H-14 · Conditional Cross-Venue-Lead-Lag-Graph (Node-Ablation-Cross-Attention, F-PANELLAG, KAPITALFREI, GPU)

- **Hypothese:** H-14 — `scinance2-impl/state/hypothesis_registry.md` (Welle 5)
- **Erzeugt:** 2026-07-29T11:15:27+00:00 (UTC)
- **Quelle:** `E:\Claude\Projects\scinance\data\harvest/raw/{bybit,binance,deribit}/publicTrade (12-node panel, 1s grid)`
- **Fenster (vorregistriert):** W1, W2
- **Panel:** 12 Nodes = BTC/ETH x {Bybit, Binance, Deribit-PERP} + SOL/BNB/XRP x {Bybit, Binance}, publicTrade 1s-Grid
- **Modell:** Pro Node ein PatchTST-Style-Encoder (m18-Wiederverwendung) + Cross-Node-Multi-Head-Attention; Target = Vorzeichen der naechsten 10s-Rendite je Node
- **Statistik:** T(j->i) = OOS-Delta-Log-Loss (Vollmodell vs. Single-Source-j-Retrain-Ablation, zirkulaeres Surrogat) — KEINE Attention-Gewicht-Lesart
- **Null:** ~100 Retrainings je Fenster mit komplett surrogaten Cross-Node-Inputs (zirkulaerer Shift je Node, Targets aus der geshifteten Serie); Null-Deltas = alle geordneten Paardifferenzen der Null-OOS-Losses je Target · Seed: 42
- **FDR-Familie:** F-PANELLAG (EINE Familie ueber BEIDE Fenster, 198 Kanten-Tests) · BH-FDR alpha 0.1 · p_crit 0.0001 · FDR-signifikant: 1
- **Familien-Groesse:** 12 Nodes -> 132 gerichtete Kanten; ohne die 3 BTC-Source-Nodes exakt 9x11=99 Non-BTC-Source-Kanten je Fenster (Registry-Schaetzung '~110'); Familie = beide Fenster gemeinsam.
- **KAPITALFREI:** ja — reine Struktur-/Existenzfrage. Eine Handelsfolge waere NEUE H-14b, NICHT impliziert.

## Compute-Gating (GPU-Pflicht)

- torch verfuegbar: ja · CUDA verfuegbar: ja · Device: NVIDIA GeForce RTX 5060 Ti
- **auf GPU gelaufen:** ja · CPU-Fallback: nein · synthetisches train_fn: nein
- **gate_valid:** ja — GPU-Pflicht (Registry H-14, Rechenaufwand): ohne echtes CUDA-Training ist der Lauf NICHT verdikt-tragend — gate_valid=false, weiter_indication=null. Der numpy-/CPU-Pfad ersetzt die registrierte ~226-Retrain-Null NICHT.

- **Positivkontrolle:** Positivkontrolle (Registry H-14): mindestens eine BTC->ETH-Kante muss je Fenster das 95. Perzentil ihrer Null ueberschreiten (durch H-04 etabliert, vom Pass-Kriterium AUSGESCHLOSSEN). Scheitert sie, ist der Lauf METHODISCH INVALIDE (kein Verdikt, NICHT DROP).
- **Validitaets-Status dieses Laufs:** **UNGUELTIG**

> Gate-Urteil faellt der gate-auditor gegen H-14. WEITER verlangt in BEIDEN Fenstern mindestens eine gerichtete Non-BTC-Source-Kante ueber dem 95. Perzentil der ~100-Surrogat-Null UND BH-FDR alpha=0,10 ueber F-PANELLAG ueberlebend. DROP (hartes Ein-Fenster-Kriterium): null ueberlebende Non-BTC-Source-Kanten in einem Fenster. Kein Graubereich, kein Kanten-/Schwellen-Nachjustieren. BTC->ETH ist Positivkontrolle (vom Pass ausgeschlossen; Scheitern = methodisch invalide). A-priori: DROP erwartet.

**WEITER-Indikation (nur bei gate_valid und gueltigem Lauf):** n/a (nicht verdikt-tragend) · **alle Fenster mit Survivor:** nein · **Positivkontrolle alle Fenster:** nein

## Fenster-Uebersicht (Gate-Kern)

| Fenster | Familien-Kanten | ueber Null-q95 | FDR-sig | ueberlebend | >=1 Survivor | Positivkontrolle |
|---|---:|---:|---:|---:|:---:|:---:|
| W1 | 99 | 8 | 1 | 1 | ja | nein (0/9) |
| W2 | 99 | 0 | 0 | 0 | nein | nein (0/9) |

## Kanten W1

**Ueberlebende Non-BTC-Source-Kanten (ueber q95 UND FDR-sig):**

| Quelle -> Ziel | Delta-Log-Loss | Null-q95 | p |
|---|---:|---:|---:|
| bybit:BNBUSDT -> binance:SOLUSDT | 0.000612 | 0.000220 | 0.0001 |

**Top-10 Familien-Kanten nach Delta-Log-Loss:**

| Quelle -> Ziel | Delta-Log-Loss | Null-q95 | ueber q95 | p | FDR-sig |
|---|---:|---:|:---:|---:|:---:|
| bybit:BNBUSDT -> binance:BNBUSDT | 0.000683 | 0.000419 | ja | 0.0202 | nein |
| bybit:BNBUSDT -> binance:SOLUSDT | 0.000612 | 0.000220 | ja | 0.0001 | ja |
| binance:ETHUSDT -> binance:XRPUSDT | 0.000562 | 0.000247 | ja | 0.0058 | nein |
| binance:SOLUSDT -> binance:XRPUSDT | 0.000497 | 0.000247 | ja | 0.0084 | nein |
| binance:SOLUSDT -> bybit:XRPUSDT | 0.000467 | 0.000374 | ja | 0.0279 | nein |
| binance:BNBUSDT -> bybit:BNBUSDT | 0.000463 | 0.000561 | nein | 0.0796 | nein |
| bybit:BNBUSDT -> binance:XRPUSDT | 0.000457 | 0.000247 | ja | 0.0096 | nein |
| bybit:BNBUSDT -> deribit:BTC-PERPETUAL | 0.000361 | 0.000467 | nein | 0.0804 | nein |
| binance:BNBUSDT -> binance:XRPUSDT | 0.000357 | 0.000247 | ja | 0.0177 | nein |
| binance:BNBUSDT -> bybit:ETHUSDT | 0.000301 | 0.000293 | ja | 0.0487 | nein |

**BTC-Source-Kanten (NICHT urteilstragend, inkl. Positivkontrolle BTC->ETH):**

| Quelle -> Ziel | Delta-Log-Loss | Null-q95 | ueber q95 |
|---|---:|---:|:---:|
| binance:BTCUSDT -> bybit:XRPUSDT | 0.000355 | 0.000374 | nein |
| binance:BTCUSDT -> binance:SOLUSDT | 0.000260 | 0.000220 | ja |
| binance:BTCUSDT -> binance:XRPUSDT | 0.000248 | 0.000247 | ja |
| deribit:BTC-PERPETUAL -> bybit:XRPUSDT | 0.000207 | 0.000374 | nein |
| bybit:BTCUSDT -> binance:XRPUSDT | 0.000149 | 0.000247 | nein |
| bybit:BTCUSDT -> bybit:SOLUSDT | 0.000148 | 0.000345 | nein |

## Kanten W2

*Keine ueberlebende Non-BTC-Source-Kante in diesem Fenster.*

**Top-10 Familien-Kanten nach Delta-Log-Loss:**

| Quelle -> Ziel | Delta-Log-Loss | Null-q95 | ueber q95 | p | FDR-sig |
|---|---:|---:|:---:|---:|:---:|
| bybit:ETHUSDT -> deribit:BTC-PERPETUAL | 0.001020 | 0.002683 | nein | 0.1289 | nein |
| bybit:ETHUSDT -> bybit:BTCUSDT | 0.000760 | 0.000967 | nein | 0.0662 | nein |
| bybit:SOLUSDT -> deribit:BTC-PERPETUAL | 0.000755 | 0.002683 | nein | 0.1754 | nein |
| bybit:SOLUSDT -> bybit:BTCUSDT | 0.000744 | 0.000967 | nein | 0.0674 | nein |
| bybit:SOLUSDT -> binance:BTCUSDT | 0.000629 | 0.000930 | nein | 0.0777 | nein |
| binance:ETHUSDT -> deribit:BTC-PERPETUAL | 0.000558 | 0.002683 | nein | 0.2200 | nein |
| bybit:SOLUSDT -> binance:XRPUSDT | 0.000435 | 0.001221 | nein | 0.1421 | nein |
| binance:ETHUSDT -> binance:BTCUSDT | 0.000350 | 0.000930 | nein | 0.1613 | nein |
| binance:ETHUSDT -> deribit:ETH-PERPETUAL | 0.000339 | 0.000910 | nein | 0.1677 | nein |
| bybit:ETHUSDT -> binance:ETHUSDT | 0.000252 | 0.001357 | nein | 0.2619 | nein |

**BTC-Source-Kanten (NICHT urteilstragend, inkl. Positivkontrolle BTC->ETH):**

| Quelle -> Ziel | Delta-Log-Loss | Null-q95 | ueber q95 |
|---|---:|---:|:---:|
| binance:BTCUSDT -> bybit:BTCUSDT | 0.002027 | 0.000967 | ja |
| binance:BTCUSDT -> bybit:SOLUSDT | 0.001403 | 0.001649 | nein |
| binance:BTCUSDT -> bybit:BNBUSDT | 0.001228 | 0.001519 | nein |
| binance:BTCUSDT -> binance:XRPUSDT | 0.000946 | 0.001221 | nein |
| binance:BTCUSDT -> deribit:BTC-PERPETUAL | 0.000944 | 0.002683 | nein |
| binance:BTCUSDT -> binance:BNBUSDT | 0.000908 | 0.001565 | nein |

*Erzeugt von `scripts/c14_panellag.py` (Welle 5, read-only Harvester-Backfill, GPU-gated). capital_free=true. Endgueltiges Gate-Urteil: gate-auditor gegen H-14.*
