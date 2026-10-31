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

## Nachrechnung Teil C (Null-Simulation, Funding W2, P3fix, Produkt-MDE80, Pilot-Regel), 2026-10-31

Skripte `/home/user/scinance_work/orch_check/` (nicht im Repo; eigener Code, andere Seeds, keine Agentenmodule):
`a2_null_check.py` (Permutations-Null vor Lieferung der Herleitung gerechnet, Seed 2026, 4.000 Replikate, nur Wochen
vollstaendig im Fenster), `a2_p3fix_check.py` (P3fix-Reihe), `a2_teilc_check.py` (Formeln mit den in der Akte genannten
Konstanten). Datenextrakte vom Orchestrator selbst erstellt (`EXTRACT_LOG.json`). **Kein Mittel, kein realer Kontrast**
(Hash-Waechter gegen den realen Label-Vektor auch im eigenen Skript).

| Groesse | Herleitung Teil C | Orchestrator | Befund |
|---|---|---|---|
| Null-SD J-(i) je Vorperioden-Fenster (2021-06.., 2022-06.., 2023-06..), gepoolt | 7,52 / 6,02 / 4,51 / 3,75 | 7,69 / 5,95 / 4,41 / 3,75 | gepoolt identisch; je Fenster 2..3 % (Randwochen: Herleitung nimmt Teilwochen 4:1 / 3:1 / 2:1 mit, Benchmark nur volle Wochen; MC-Rauschen) |
| d95 reg. je Fenster / gepoolt | 12,44 / 9,78 / 7,39 / 6,14 | 11,84 / 9,98 / 7,70 / 6,38 (q95 der zentrierten Null, einseitig) | gleiche Groessenordnung; Herleitung exakt-kumulant, Benchmark MC mit 4.000 Replikaten (Band +-0,2..0,4) |
| Optionsdeliveries 2020-03-25..2026-06-30 (Kalender) | 174.931 gesamt <= 2026-06-30 | 174.931 / 167.076 ab 2020-03-25 | identisch (Review N7: 167.076) |
| Funding W2 BTCUSDT/ETHUSDT | 363 Tage x 3 (00/08/16), Anteil 1,0000 | 363 x 3 je Symbol, Stunden 0/8/16, keine Minutenabweichung | identisch |
| P3fix (Mo-Fr ohne Monatsend-Freitage, Vorperiode): N / SD / rho(r_pre, r_fix) Wochen-Freitage | 794 / 61,4 / -0,159 | 794 / 61,39 / -0,159 (n 128) | identisch (c_bind nicht nachgerechnet: eigener Batch-Means-Schaetzer 1,35 gegen P-3-Regel 1,168; Review prueft) |
| Produkt-MDE80 mit Null-Faktor W1 / W2 (Konstanten T3) | 23,4 / 24,4 | 23,44 / 24,39 | identisch |
| Produkt nur z-Terme; mit k_pred 1,0946 | 22,8 / 23,1; 23,7 / 24,8 | 22,82 / 23,09; 23,66 / 24,77 | identisch |
| Einzel-MDE80 P2'' / P3fix; Null-Bedingung allein (W1 / W2) | 18,2 / 18,8; 19,7; 16,8 / 19,1 | 18,25 / 18,85; 19,72; 16,76 / 19,12 | identisch |
| c_A2 (k_pred 1), t am Schwellenpunkt, Pilot-alpha | 24,4; ~6; <= 1,3e-9 | 24,39; 5,95; 1,3e-9 | identisch |
| Pilot-Power bei 16,5 / 25 bp (Kontrast-Skala; Ereignis-Skala 0,842) | 0,027 / 0,559; 0,005 / 0,207 | 0,027 / 0,559; 0,005 / 0,207 | identisch |
| DEC-103-E7-Produkt (Teil-B-SEs 7,34 / 7,18 / 6,53) | 21,90 | 21,89 | identisch |

Lesart: Die Formeln der Pilot-Regel und der Zuordnung sind reproduziert; die Null-Simulation stimmt im gepoolten Wert
exakt und je Fenster innerhalb der Randwochen-/MC-Toleranz. Die Pilot-Power von 2,7 % bei 16,5 bp ist eine korrekte
Folge der Regel (Produkt-Power 0,80 in 12-Monats-Fenstern gegen drei Placebos plus Null-Bedingung), kein Rechenfehler.

## Nachrechnung Teil C Fassung 2 (nach REVIEW_A2_TEILC.md: VETO-Aufloesung A-1, Festlegungen), 2026-10-31 abends

Abnahme der Fassung 2 (`a2_teilC.json` sha256 8c01d72ece18e1c607b7ef585a88bef2ea19bca87c422c9e229780354bd17687):
Struktur-Scan `scratch/orch_check/channel_scan.py` (nicht im Repo; sucht Klassen-Eintraege mit n und sd und Gruppen, in
denen eine Klassenzahl die Summe anderer ist; kombiniert nie Werte): Vereinigungs-Feld `sd_of_null_shift_iid` entfernt,
Ersatz aus der within-week-Streuung; 20 Klassen-Eintraege, kein Tripel derselben Reihe; einzige Zaehl-Koinzidenz
P3all = E + P2'' (andere Slot-Werte, kein Kanal). Keine Daten nach 2026-06-30, keine Lage-Schluessel, ASCII, keine
Modellnamen, sha256 in beiden Textdateien. Derselbe Scan auf `a2_vorarbeit.json` (Teil B, Commit 363f3d9) bestaetigt
Review B-2 strukturell: 1.188 geschachtelte Gruppen (ALL = FRI + NONFRI, NONFRI = MODO + WE, FRI = FRI_W + FRI_MQ,
FRI_MQ = FRI_M + FRI_Q; je Reihe und Slot) mit voller Praezision - keine Werte kombiniert.

| Groesse (Festlegungen: Stress bindend, skalierte Null k_W = SE_T/Null-SD, Gate-(4)-Faktor 0,9025) | Herleitung F2 | Orchestrator | Befund |
|---|---|---|---|
| k_pred,W vor dem Pilot W1 / W2 | 1,096 / 1,215 | 1,096 / 1,215 | identisch |
| MDE80prod stress R0 (mit Gate 4) W1 / W2 = c_A2 | 29,0 / 32,1 | 28,99 / 32,17 | identisch |
| dto. ohne Gate-(4)-Faktor | 26,6 / 29,3 | 26,63 / 29,32 | identisch |
| dto. k_pred x 1,1 | 29,9 / 34,1 | 29,90 / 34,16 | identisch |
| MDE80prod zentral R0 (mit / ohne Gate 4) W1 / W2 | 26,0 / 28,8; 23,9 / 26,2 | 26,05 / 28,79; 23,92 / 26,25 | identisch |
| Fassung 1 unskaliert ohne Gate 4 (stress / zentral) W1 / W2 | 26,1 / 27,2; 23,4 / 24,4 | 26,08 / 27,19; 23,44 / 24,39 | identisch |
| Pilot-Power bei c_A2 32,1: 16,5 bp Kontrast / Ereignis; 25 bp | 0,0001 / < 0,0001; 0,0406 / 0,0034 | 0,0001 / 0,0000; 0,0417 / 0,0035 (ohne Vorzeichen-Faktoren der P3-Kontraste) | identisch bis auf die P3-Vorzeichenfaktoren |
| t am Schwellenpunkt (SE_P 4,10) | ~7,8 | 7,83 | identisch |
| PK-Kriterium (b): erwartete Quote 0,914 x 0,9025, minus 2,3263 x Binomial-SE (200 Seeds) | 0,825 -> 0,763 | 0,825 -> 0,762 | identisch (Rundung) |
| Funding Vorperiode / W1 (Extrakt `rest.fundingRateAll`, nur Zeitstempel) | 1.165 / 365 Tage je 3 Termine 00/08/16 UTC, beide Symbole | identisch (eigene Zaehlung vor der Herleitung) | identisch |

Hinweis: Eine erste eigene Rechnung ohne Skalierung des Null-Nenners (nur k x d95 im Zaehler) ergab 30,8 statt 32,1 bp
fuer W2 stress; die Regel-Formel der Akte skaliert Zaehler und Nenner der Null-Bedingung mit k (DEC-101 E2 analog) -
mit ihr stimmen alle Werte. Lesart: die Pilot-Route ist mit den Festlegungen bei jedem Prior unter ~30 bp praktisch ein
sicherer GL-012 (Pilot); das ist die korrekte Folge von Regel und Daten (Review B-3), kein Rechenfehler.
