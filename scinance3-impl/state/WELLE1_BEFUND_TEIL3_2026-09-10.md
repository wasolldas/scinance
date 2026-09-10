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

## Nachtrag 2026-09-10: Surrogat-Null der Stress-Zelle (Wiederholungslauf, DEC-64 erfuellt)

Wiederholungslauf `state/runs/wp10a2_20260910/` (ersetzt die Fassung ohne Surrogat-Block vom selben Tag; alle uebrigen Zahlen identisch, Seed 53). Je Paar B = 1.000 Surrogate in zwei Varianten; berichtet wird der Rang der realen Differenz rho_Stress - rho_Ruhe ("Lift") in der jeweiligen Null-Verteilung.

| Paar | realer Lift | Null p95 (unabh. Bloecke) | Rang unabh. Bloecke | Rang Selektion gem. Groesse |
|---|---:|---:|---:|---:|
| Funding ETH x BNB | +0,57 | 0,46 | 98,3 % | 99,7 % |
| Funding BTC x XRP | +0,44 | 0,37 | 97,6 % | 99,5 % |
| Funding ETH x SOL | +0,46 | 0,47 | 94,6 % | 96,5 % |
| Funding SOL x BNB | +0,43 | 0,46 | 93,4 % | 93,6 % |
| Funding ETH x XRP | +0,35 | 0,42 | 92,3 % | 97,6 % |
| Funding SOL x XRP | +0,33 | 0,48 | 87,5 % | 89,7 % |
| Funding BTC x ETH | +0,22 | 0,31 | 87,1 % | 93,1 % |
| Funding BTC x SOL | +0,13 | 0,46 | 66,7 % | 67,8 % |
| Funding XRP x BNB | +0,12 | 0,47 | 64,7 % | 68,7 % |
| Funding BTC x BNB | -0,05 | 0,47 | 44,0 % | 40,3 % |
| Funding BTC x IV-RV BTC / ETH | -0,42 / -0,44 | 0,38 | 2,1 % / 2,2 % | 5,0 % / 3,5 % |
| Funding XRP x IV-RV BTC / ETH | -0,31 / -0,26 | 0,39 / 0,40 | 9,8 % / 13,6 % | 10,8 % / 14,4 % |
| IV-RV BTC x ETH | +0,01 | 0,37 | 50,1 % | 61,5 % |
| uebrige Funding x IV-RV | -0,18 .. +0,05 | 0,37-0,49 | 26-58 % | 28-56 % |

**Lesart (deskriptiv, kein Verdikt):**
1. Beide Null-Varianten sind um 0 zentriert (Mittel -0,04 .. +0,015); die Variante "Selektion auf gemeinsame Groesse" liegt praktisch auf der unabhaengigen - der mechanische Extremstichproben-Effekt ist fuer diese Serien klein (die Stress-Maske kommt aus der RV, nicht aus den Serien selbst; symmetrische Randverteilungen erzeugen keine Verschiebung). Die breiten Null-Baender (p95 0,31-0,49) spiegeln n_Stress = 14-28.
2. Der Funding-Kohaerenz-Anstieg im Stress ist damit NICHT durch den Selektionseffekt erklaert: zwei Paare liegen in beiden Varianten ueber p95, fuenf weitere zwischen 87 % und 97 %, und die Richtung ist in 9 von 10 Paaren gleich. Ein formaler Gemeinschaftstest ist nicht registriert und wird nicht nachgeschoben (deskriptives Paket).
3. BTC-Funding x IV-RV: der negative Stress-Lift liegt am unteren Rand (Rang 2-5 %), ebenfalls konsistent ueber beide IV-Serien. Bleibt Deskriptor; kein Kandidat (DEC-58).
4. Die Stress-Matrix geht damit als Konstante in PRD 9.2 (DEC-64 Punkt 2 erfuellt): Funding-Beine sind im Stress deutlich kohaerenter (0,6-0,7) als in Ruhe (0,2-0,35); `N_eff` fuer A1 ist im Stress-Fenster getrennt zu fuehren.
