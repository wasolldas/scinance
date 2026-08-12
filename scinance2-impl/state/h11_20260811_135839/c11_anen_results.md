# H-11 — AnEn-Vol-Regime-Forecast vs. HAR-RV (KAPITALFREI, data-gated)

- **Hypothese:** H-11 — `scinance2-impl/state/hypothesis_registry.md`
- **Erzeugt:** 2026-08-11T15:02:00+00:00 (UTC)
- **Status:** RUN
- **KAPITALFREI:** ja — reines Mess-Gate (CRPS-Verteilungsvergleich); Monetarisierung waere NEUE H-11b.
- **Entsperr-Check:** ENTSPERRT — Coverage 2024-03-27..2026-03-26 (>= 730 Tage lueckenlos, publicTrade + rest.fundingRate, BTC+ETH; Quelle: Manifest-done_days)
- **Quelle:** `E:\Claude\Projects\scinance\data\harvest/raw/bybit/{publicTrade,rest.fundingRate}` (Symbole: BTCUSDT, ETHUSDT)
- **Fenster:** L=2024-03-27..2025-09-30 (Tuning) | W1=2025-10-01..2026-03-26 | W2=2026-03-27..2026-06-30 (disjunkt)
- **Methode:** k=20, Embargo 30 Tage, Grid [0.0, 0.5, 1.0, 1.5, 2.0]^5 (eingefroren nach L), Ziel log ann. RV t+1..t+3 (1-min-Returns); AnEn = Ensemble-CRPS der empirischen Verteilung der 20 Analog-Ziele, HAR-Baseline = Punkt-CRPS |Prognose-Beobachtung|
- **Null:** Block-Bootstrap (Blocklaenge 5 Tage, 1000 Reps, DM-artig), H0: mean(CRPS_HAR-CRPS_AnEn)<=0
- **FDR-Familie:** F-ANEN · BH-FDR alpha=0.1 · p_crit=0.0010

> Gate-Urteil faellt der gate-auditor gegen H-11. WEITER verlangt: fuer >=1 Symbol in {BTC,ETH} in BEIDEN Fenstern CRPSS>=0.05 UND Bootstrap-p<=0.05 nach BH-FDR alpha=0.10 ueber F-ANEN. Hartes Ein-Fenster-DROP, kein GRAUBEREICH, keine k-/Gewichts-/Feature-Nachsuche. A-priori: DROP.

## Eingefrorene Gewichte (LOO-CRPS auf L)

| Symbol | Gewichte (logRV1d, logRV5d, logRV20d, Funding-Mittel, Funding-Trend) | LOO-CRPS |
|---|---|---:|
| BTCUSDT | [2.0, 2.0, 0.5, 0.0, 0.0] | 0.17153 |
| ETHUSDT | [2.0, 0.5, 0.0, 0.0, 0.0] | 0.16765 |

## Zellen (F-ANEN: Symbol x Fenster)

| Symbol | Fenster | n | mean CRPS AnEn | mean CRPS HAR | CRPSS | >=0.05 | boot-p | p<=0.05 | FDR-sig | Zelle |
|---|---|---:|---:|---:|---:|:---:|---:|:---:|:---:|:---:|
| BTCUSDT | W1 | 177 | 0.1504 | 0.2124 | 0.2917 | ja | 0.0010 | ja | ja | PASS |
| BTCUSDT | W2 | 96 | 0.1296 | 0.1706 | 0.2401 | ja | 0.0010 | ja | ja | PASS |
| ETHUSDT | W1 | 177 | 0.1650 | 0.2193 | 0.2475 | ja | 0.0010 | ja | ja | PASS |
| ETHUSDT | W2 | 96 | 0.1563 | 0.2116 | 0.2615 | ja | 0.0010 | ja | ja | PASS |

## PIT-Rank-Histogramm (nicht-urteilstragend, mitberichtet)

*Rang der Beobachtung im k-Member-Ensemble je Prognosetag (21 Bins 0..k; kalibriert ~ uniform). Reine Sekundaerdiagnose — geht in KEIN Gate-Flag ein.*

| Symbol | Fenster | Histogramm (Bin 0..k) |
|---|---|---|
| BTCUSDT | W1 | 3 7 7 9 8 6 9 6 6 7 5 7 13 13 12 12 13 8 7 5 14 |
| BTCUSDT | W2 | 2 4 9 5 3 10 7 2 4 3 7 10 4 6 6 5 3 1 0 1 4 |
| ETHUSDT | W1 | 8 8 14 5 6 12 11 6 2 8 9 7 7 9 10 7 14 6 8 8 12 |
| ETHUSDT | W2 | 10 8 9 8 5 3 4 3 3 3 7 4 5 7 5 3 1 4 1 2 1 |

## Symbol-Rollup (Gate-Kern, gate-neutral)

| Symbol | Fenster gemessen | Fenster PASS | BEIDE Fenster PASS |
|---|---:|---:|:---:|
| BTCUSDT | 2 | 2 | JA |
| ETHUSDT | 2 | 2 | JA |

**Mindestens ein Symbol mit beiden Fenstern PASS:** ja

*Erzeugt von `c11_anen/driver.py` (read-only Harvester-Baum). capital_free=true. Endgueltiges Gate-Urteil: gate-auditor gegen H-11.*