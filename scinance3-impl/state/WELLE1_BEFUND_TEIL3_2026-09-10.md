# Welle 1 - Befund Teil 3: WP-10(A2) Stress-Kohaerenz auf Backfill-Serien (Echtlauf 2026-09-09)

> Orchestrator-Adjudikation. Ergebnisordner `state/runs/wp10a2_20260909/`
> (DEC-53: Cluster-Serien je Serie, Bootstrap-Fingerprint). Modus
> `--source backfill` (DEC-62). Deskriptiv, KEIN PASS/FAIL. Kein Kandidat.

## Serien und Abdeckung

| Serie | Quelle | Tage | von .. bis |
|---|---|---:|---|
| Funding BTC / ETH | oeffentliche funding/history (panel_1d bzw. REST) | 2.320 / 2.110 | 2020-03-25 / 2020-10-21 .. 2026-07-31 |
| Funding SOL / XRP / BNB | dito | 1.859 / 1.906 / 1.859 | 2021-05..06 .. 2026-07-31 |
| IV-RV BTC / ETH | REST-DVOL (DEC-61) minus WP-0-RV | 1.956 / 1.956 | 2021-03-24 .. 2026-07-31 |
| Basis-Proxy BTC / ETH | Harvest-only (unveraendert) | 61 / 61 | 2026-06-16 .. 2026-08-29 |

**Bestand vs. Backfill (Pflichtzeile, DEC-60-Lehre):** Funding 5 Symbole: 128-883 Ueberlappungstage, max|diff| = 0, kein abweichender Tag. IV-RV: 165 Tage, max|diff| = 0 Vol-Punkte. Der Backfill reproduziert den Bestand exakt; die Serien duerfen durchgehend aus dem Backfill kommen.

## Stress-Zelle (STRESS_ABS, 30 Tage / 19 Episoden) - jetzt besetzt

| Paar | rho Stress [95 %-CI] | n Stress (Episoden) | rho Ruhe [95 %-CI] | n Ruhe |
|---|---|---:|---|---:|
| Funding BTC x ETH | 0,57 [0,17; 0,84] | 28 (17) | 0,35 [0,31; 0,39] | 2.081 |
| Funding BTC x XRP | 0,66 [0,21; 0,90] | 20 (10) | 0,22 [0,18; 0,27] | 1.885 |
| Funding ETH x SOL | 0,72 [0,29; 0,92] | 14 (9) | 0,26 [0,21; 0,31] | 1.844 |
| Funding ETH x BNB | 0,74 [0,35; 0,94] | 14 (9) | 0,17 [0,12; 0,22] | 1.844 |
| Funding ETH x XRP | 0,59 [0,16; 0,85] | 20 (10) | 0,24 [0,19; 0,29] | 1.885 |
| Funding SOL x XRP / SOL x BNB | 0,63 / 0,65 | 14 (9) | 0,30 / 0,22 | 1.844 |
| Funding BTC x SOL / BTC x BNB / XRP x BNB | 0,35 / 0,06 / 0,33 (CI enthaelt 0) | 14 (9) | 0,22 / 0,11 / 0,21 | 1.844 |
| IV-RV BTC x ETH | 0,89 [0,66; 0,98] | 22 (12) | 0,88 [0,86; 0,89] | 1.933 |
| Funding BTC x IV-RV BTC / ETH | -0,43 [-0,75; 0,02] / -0,46 [-0,77; -0,06] | 22 (12) | -0,01 / -0,02 (CI enthaelt 0) | 1.933 |
| Funding ETH/SOL/XRP/BNB x IV-RV | -0,29 .. 0,06 (alle CI enthalten 0) | 14-22 | ~0 | 1.844-1.933 |
| Basis x alles | TOO_FEW (0-1) | - | n = 33-59, CI breit | - |

## Lesart (kapitalfrei, deskriptiv)

1. **Funding-Praemien werden im Stress kohaerenter.** In 9 von 10 Funding-Paaren liegt rho_Stress ueber rho_Ruhe, typisch 0,6-0,7 gegen 0,2-0,35; die Stress-CIs sind breit (SE 0,21-0,32 bei n 14-28), aber die Richtung ist ueber alle Paare gleich. Ob dieser Anstieg ueber den mechanischen Selektionseffekt (Extremstichprobe) hinausgeht, ist OFFEN: die vom PRD 4.3 verlangte Surrogat-Null der Stress-Zelle fehlte im Treiber (Bauluecke des Orchestrators, siehe DEC-64). Bis sie vorliegt, gilt: A1 (Querschnitts-Funding) hat im Stress weniger unabhaengige Beine als in Ruhe; `N_eff` ist im Stress-Fenster getrennt auszuweisen.
2. **IV-RV BTC/ETH bleibt ein Faktor** (0,88 in beiden Regimen) - unveraendert ein Bein.
3. **Funding x IV-RV: in Ruhe orthogonal, im Stress schwach negativ** (BTC-Funding gegen IV-RV -0,43/-0,46, ein CI schliesst 0 knapp aus, n = 22). Deskriptiv: an Stress-Tagen faellt BTC-Funding (Shorts zahlen), waehrend IV-RV steigt oder faellt weniger. Kein Kandidat (Null-Zensus-Klausel DEC-58), aber die vorab fixierte abhaengigkeitsrobuste Ueber-Familien-Korrektur (F-PREM1/F-PREM2) bleibt bestehen - in Ruhe waere sie verzichtbar, im Stress nicht.
4. **Basis-Proxy** bleibt ohne Aussage (recording-first wie A4).

## Konsequenzen (DEC-64)
- Surrogat-Null der Stress-Zelle nachruesten (zwei Varianten: unabhaengige Block-Surrogate; Selektion auf gemeinsame Groesse) und den Lauf wiederholen; erst dann geht die Stress-Matrix als Konstante in PRD 9.2.
- Konstanten aus Teil 2 (Portfolio-Null, Selektions-Decke) sind unveraendert reproduziert (Seed 53, identische Werte).
