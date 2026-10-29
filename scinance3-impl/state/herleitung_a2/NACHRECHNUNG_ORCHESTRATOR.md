# Nachrechnung des Orchestrators (unabhaengiges Skript, 2026-10-29): sigma30 der Vorperiode nach Tagesklasse

Skript `scratchpad/orch_check/a2_spot.py` (nicht im Repo): r_pre = 1e4 x ln(C[07:59] / C[07:29]) aus den 1-min-Kerzen
BTCUSDT/ETHUSDT 2021-03-24..2024-05-31 (assert: kein Tag nach 2024-05-31), Ausreisser-Tage 2020-08-27 und 2024-08-19
ausgeschlossen (liegen ausserhalb bzw. am Rand des Fensters), Klassen nach Wochentag (Freitag / Mo-Do / Wochenende).
**Kein Mittel ausgegeben**, nur SD (ddof 1) und Pearson-rho.

| Klasse | n | SD BTC (bp) | SD ETH (bp) | SD Cluster-Mittel (r_BTC + r_ETH)/2 | rho(BTC, ETH) | Herleitung (NUISANCE_SIGMA30) |
|---|---:|---:|---:|---:|---:|---|
| Freitag | 167 | 40,2 | 52,6 | 43,8 | 0,78 | 40,2 / 52,6; gepoolt 46,8 (= sqrt((SD_BTC^2 + SD_ETH^2)/2), obere Schranke); Cluster 43,8; rho 0,78 |
| Mo-Do | 666 | 39,5 | 48,8 | 42,5 | 0,85 | 39,5 / 48,8; 0,85 |
| Wochenende | 332 | 31,6 | 40,7 | 34,8 | 0,85 | 31,6 / 40,7 |
| alle Tage | 1.165 | 37,5 | 47,2 | 40,6 | 0,84 | 37,5 / 47,2; 0,84 |

Befund: Die Klassen-SDs und rho der Herleitung reproduzieren sich bitgenau auf der ausgewiesenen Stelle. "gepoolt" in
der Herleitung ist die gestapelte SD (obere Schranke); fuer die Cluster-Statistik x = (r_BTC + r_ETH)/2 (PRD-Gate (3))
gilt die kleinere Cluster-SD (Freitag 43,8 bp), die die Herleitung ebenfalls fuehrt. Die PRD-Vol-Kette (36 bp, BTC-only,
Tagesvol 2,5 %) unterschaetzt die gemessene Freitags-Streuung um ~10 % (BTC) bzw. ~20 % (Cluster).

## Nachrechnung der neuen Review-Zahlen (B-5 Konjunktions-Power, B-7 Futures-Kalender), 2026-10-29

Skripte `scratchpad/orch_check/a2_joint_check.py` und `a2_fut_check.py` (nicht im Repo; eigener Code, keine
Reviewer-Module). Eingaben nur SE/SD/c aus der Akte bzw. Instrumentnamen/Typ/Datum des Settlement-Kalenders
<= 2026-06-30; keine Rendite beruehrt.

| Groesse | Review | Orchestrator | Befund |
|---|---|---|---|
| D_i gemeinsame Power gegen {P2', P3fix, P3all} bei 16,5 / 18,25 / 25 bp | 0,645 / 0,733 / 0,944 | 0,647 / 0,735 / 0,944 | gleich (MC, Seed 11, 400.000 Replikate) |
| D_i Produkt der Einzel-Powers (dto.) | 0,438 / 0,570 / - | 0,439 / 0,572 / 0,916 | gleich |
| MDE80 D_i Ereignis-Skala: Einzel / gemeinsam / Produkt | 18,25 / 19,8 / 21,9 | 18,25 / 19,7 / 21,9 | gleich |
| dto. mit OI-Abschwaechung 0,842 auf P2' | 21,7 / 22,2 / 23,8 | 21,7 / 22,1 / 23,7 | gleich |
| erste Nicht-Freitags-Futures-Delivery BTC / ETH | 2026-04-04 | 2026-04-04 / 2026-04-04 | gleich |
| Futures-Deliveries an Nicht-Freitagen 2020-03-25..2026-06-30 | 134 | 134 (76 Tage) | gleich |
| W2 (2025-07-01..2026-06-28) Mo-Do-Tage mit Futures-Delivery / beide Waehrungen | 48 von 207 / 36 | 48 von 207 / 36 (erster 2026-04-06) | gleich |
| W1 Mo-Do-Tage mit Futures-Delivery | 0 | 0 | gleich |

Lesart: die Konjunktions-Zahlen bestaetigen Review B-5 (die Einzel-Placebo-MDE80 18,3 bp ist die Untergrenze des
Rauschbodens, die Produkt-Untergrenze 21,9 bp die konservative Zuordnungsgrundlage analog DEC-94 (6)); die
Futures-Zahlen bestaetigen B-7 (P2' ist zwischen W1 und W2 nicht homogen).
