# Review A2-Vorarbeit Teil C: Null-Simulation J-(i), bindende SE, Funding-Intervall W2, Pilot-Uebergaberegel U-A2

> Adversarischer Gate-Review (Richtung Strenge), Stand 2026-10-31. **Kein Verdikt ueber A2, nichts registriert,
> nichts committet.** Gegenstand: `NULL_SIMULATION_A2.md`, `PILOT_ROUTE_A2.md`, `a2_teilC.json` unter
> `state/herleitung_a2/` - **sha256 von `a2_teilC.json` geprueft: 5741d90c3a84a4d23c4935b67298315232c20810d677dcbecdfe37364ac99f93**
> (gleich der Angabe der Herleitung; dritter Lauf in einer sha256-gleichen Kopie bitgleich). Auftrag der Herleitung:
> `SPEC_A2_teilC.md`; Massstab: DEC-103, DEC-94 (3)(5)(6), DEC-99 (2)(3)(5)(6), DEC-101 E7/E8, PRD 5.2, DEC-98 N5/N7,
> Teil A/B Fassung 2, `REVIEW_A2_VORARBEIT.md`, `power_p1.py` (sha256 74a8dede...d111, benutzt, nicht nachgebaut).
> **Etikett:** Renditen nur 2021-03-24..2024-05-31 (eigener Datums-Assert auf `symbol`/`start_ms` vor jedem Preis),
> Kalender nur <= 2026-06-30 ohne `position`, Funding-Zeitstempel nur W2. Ausgegeben werden nur Streuung, Quantil-
> Abstaende vom Null-Zentrum, Kurtosis, Zaehlungen, Schwellen, Powers. **Kein Mittel, kein Median, kein Vorzeichen
> irgendeiner Verfallstag-Rendite; der Kontrast mit den realen Labels wurde nie gebildet, auch nicht zur Probe; der in
> B-1/B-2 beschriebene Kanal wurde nur auf synthetischen Renditen und durch Zaehlen gespeicherter Stellen geprueft,
> nie mit realen Werten ausgerechnet.** Siegeldateien nicht geoeffnet, kein Harvest-Client, kein Netz.
> `NACHRECHNUNG_ORCHESTRATOR.md` und `scinance_work/orch_check/` vor Fertigstellung nicht gelesen (Unabhaengigkeit).
> **Kuerzel:** `[R:<datei>]` = Skript unter `/home/user/scinance_work/a2_teilC_review/`; `[rj1:<pfad>]` = dessen
> `work/r1.json`, `[rj2:...]` = `work/s2_probe.json`, `[rj3:...]` = `work/r3.json`; `[aj-C:<pfad>]` wie in der Herleitung.

## 0. Urteil

**VETO (aufloesbar), eng begrenzt: gegen Commit, Weitergabe und Registrierungs-Verwendung von `a2_teilC.json` in der
vorliegenden Fassung** - Grund B-1: Die JSON enthaelt mit 12 signifikanten Stellen die Streuung der Vereinigung
U = Ereignis u P2'' (verdeckt im Feld `sd_of_null_shift_iid`) neben den Klassen-SDs derselben Werte; ueber die
Varianzzerlegung ist daraus der **Betrag des realen P2''-Kontrasts** je Vorperioden-Fenster exakt ableitbar, fuer VP
also |x_P|, der Betrag der Pilotstatistik selbst. Das verletzt die bindende Regel "kein Mittel ... gespeichert" in
algebraisch aequivalenter Form; die Waechter (Hash, `guard_keys`) erkennen den Kanal nicht. Die Dateien sind noch
nicht im Repo (untracked) - der Fehler ist vor dem Commit vollstaendig behebbar (Auflage A-1). Aufhebung des VETO:
A-1 erfuellt und vom Orchestrator nachgeprueft (Kanal-Scan, neue sha256).

**Inhaltlich (Zahlen, Null-Definition, Pilot-Regel): ZUSTIMMUNG MIT AUFLAGEN A-2..A-9.** Jede gepruefte Zahl ist mit
eigenem Code und anderem Seed reproduziert (Abweichungen nur Monte-Carlo-Rauschen, Abschnitt 3); die Null J-(i)
entspricht DEC-103 E4; die Behandlung der 12 nicht permutierbaren W2-Wochen ist korrekt und offengelegt; die
Pilot-Power 0,027 bei 16,5 bp ist **eine korrekte Folge der Regel und der Daten, kein Rechen- oder
Konstruktionsfehler** (B-3). Programmweit kommt B-2 hinzu: Derselbe Kanal liegt bereits im committeten
`a2_vorarbeit.json` (Teil B, Commit 363f3d9) - nicht Gegenstand dieses VETO, aber vor jeder Vorlage der Pilot-Route an
den Nutzer offenzulegen (A-2).

## 1. Pruefpunkte

| Nr. | Pruefpunkt | Status | Beleg | Richtung |
|---|---|---|---|---|
| 1 | Siegel-Treue | **ABWEICHUNG** (B-1 schwer, B-2 programmweit, B-10 gering) | Schluessel-Scan (1.568 Pfade): kein mean/median/sign/delta-Schluessel; Skript-Lesung: Mittel nur intern (Wochenmittel zur Zentrierung, Klassenmittel in SD/Korrelation/c, Replikat-Mittel in Kurtosis, Tagesmittel der P3all-Slots), keines ausgegeben; Datums-Assert vor jeder Preisspalte (Code + T-10), `position` nicht gelesen, Kalender-Assert <= 2026-06-30. Waechter auf einer sha256-gleichen Kopie provoziert [R:s2_guard_probe.py]: reale Zeile mit x = None, versteckt unter 1.000 Zeilen, als bool/int64/float64 -> jeweils `RealLabelError` (VP und W2); Zeile "real bis auf eine Woche" -> akzeptiert; `guard_keys` laesst `sd_of_null_shift_iid` passieren. Die 11 Tests der Herleitung laufen auf der Kopie (11 passed). **Algebraischer Kanal** zum Betrag des realen Kontrasts in der JSON (B-1) und in `a2_vorarbeit.json` (B-2) | Ergebnisblindheit der Pilot-Route (DEC-99 (3)) |
| 2 | Null-Definition gegen DEC-103 E4 | **BESTAETIGT** (Hinweise B-8, B-9) | Eigene Mengen aus dem Kalender: je ISO-Woche genau ein Freitags-Label unter {Freitag, P2''-Tage}, Anzahl erhalten; Mo-Do ohne Futures-Tage (Vorperiode 0, W2 48 ab 2026-04-06); Wochenende in keiner Menge; Ausreisser 2020-08-27/2024-08-19 (W1: P2'' 208 statt 209); P3-Identitaet T_P3 - E = N_P/(N_P+W) (T_P2'' - E) algebraisch nachvollzogen -> N3-1 (J-(i) als eine Pipeline-Null, P3-Null-Bedingung redundant) ist begruendet und mit Richtung versehen; N3-2 korrekt als andere, nicht label-invariante Null benannt und nicht gebaut. Austauschbarkeit: gleiche Tageszeit ja; gleicher Funding-Termin in W2 belegt (363/363 Tage 8h), in Vorperiode (= Pilot) und W1 UNBELEGT (B-8); zweite Momente nicht austauschbar (V2: Freitag 31,7 gegen Mo-Do 40,0) - durch die Max-Regel DEC-94 (5) gedeckt | Grenze E4 (Wochentagseffekt) offengelegt |
| 3 | Nachrechnung | **BESTAETIGT** | Alle Kernzahlen mit eigenem Code (Seeds 7001..7004, 50.000 Replikate; exakte Null-Verteilung per FFT-Faltung) und power_p1; groesste Abweichung bei d95 reg. +0,08 bp (V3: MC der Herleitung 7,39 gegen exakt 7,31, im ausgewiesenen MC-Band [7,26; 7,51]), bei d99 der Gegenrichtung 0,35 bp (V2, ~2 MC-SE); MDE80 auf 0,01..0,1 bp; Funding und Kalender exakt (Abschnitt 3) | - |
| 4 | Pilot-Uebergaberegel | **BESTAETIGT** in Arithmetik und DEC-Konformitaet; **ABWEICHUNG** in Teilen (B-4..B-7) | Formel mechanisch, alle Konstanten vor dem Pilot fixierbar; c_A2 24,36 (W2) / 23,43 (W1), Pilot-Power 0,0275 / 0,0053 bei 16,5 bp, 0,562 / 0,209 bei 25 bp, alpha 1,3e-9 reproduziert; die Regel ist die direkte Mechanisierung von DEC-99 (6) + DEC-94 (6) (B-3). Offen: Null-Faktor im Produkt ist eine Lesart (B-4), PK-Kriterium zu nachsichtig und ohne Gate (4) (B-5), Gate (4) fehlt in Schwelle/Power (B-6), k_pred gegen G-C7 und zentral gegen stress (B-7). Keine versteckte Richtungswahl in der Regel selbst gefunden; die Defaults sind an jeder Gabelung die strengere Seite, ausser G-C3 (zentral) und dem PK-Kriterium | Lockerung (Route) korrekt etikettiert; B-5 Testbarkeit |
| 5 | Vollstaendigkeit/Belege | **BESTAETIGT** mit Luecken (B-8, B-9) | UNBELEGT benannt: V-5b, OI-Proportionalitaet, Negativ-Panel-Daten, Funding W1; es fehlen: Funding der Vorperiode, [sek]-Marke beim CME-Fenster. Etikett "Lockerung" ausformuliert (PILOT_ROUTE 7) - muss um B-2 ergaenzt werden. Gabelungen G-C1..G-C8, P-G1..P-G7, F-1..F-4 mit Richtung. Determinismus: zwei Laeufe der Herleitung bitgleich (sha-Dateien), dritter Lauf in Kopie bitgleich (c1/c2/c3/a2_teilC.json); eigene Skripte je zweimal bitgleich | - |

## 2. Befunde

| Nr. | Schwere | Befund | Richtung | Auflage |
|---|---|---|---|---|
| **B-1** | **schwer (Siegel)** | **Lage-Kanal ueber die Varianzzerlegung in `a2_teilC.json`.** `teil_C1.pre_windows.<V>.sd_of_null_shift_iid` ist `sd(x ueber U) x g(Kalender)` (c1_nullsim.py: `shift_sd_iid(pn, sig_u)` mit `sig_u = sd(x)`, x = r_pre-Cluster aller Tage von U = E u P2''); g ist reiner Kalender (V1 0,0072, VP 0,0017; > 0 wegen Randwochen und N_P != 4W). Daneben stehen `sd_class_window.E` / `.P2ss` (dieselben Werte, ddof 1) und `counts`, alles mit 12 signifikanten Stellen [R:s0_leak_channel_presence.py]. Mit `(n_U - 1) s_U^2 = (W - 1) s_E^2 + (N_P - 1) s_P^2 + (W N_P / n_U) Delta^2` folgt **|Delta| des realen P2''-Kontrasts je V1/V2/V3/VP exakt; VP = Pilotmenge, also |x_P|.** Auf synthetischen Renditen mit dem realen Kalender rekonstruiert diese Rechnung |Delta| auf 1e-9 bp (12 Stellen), 0,02..0,55 bp (4 Stellen), 0,3..4,6 bp (3 Stellen) [rj2:g_synthetic_channel_demo] - Runden allein schliesst den Kanal nicht. Mit realen Werten **nicht** ausgerechnet. Dieselben Felder stehen in `a2_teilC/work/c1.json`, `c1_pre.json`, `a2_teilC_run1/2.json`. Die MD-Spalte "SD der Null-Verschiebung" (2 Nachkommastellen) ist praktisch kanalfrei. `guard_keys` (Schluesselnamen) und der Hash-Waechter (exakte Labelzeile) koennen diesen Kanal per Konstruktion nicht sehen | Ergebnisblindheit: |x_P| entscheidet mit, ob ueberhaupt uebergeben werden kann (Uebergabe setzt |x_P| >= c_A2 voraus) | **A-1** |
| **B-2** | **hoch (programmweit, ausserhalb Teil C)** | **Derselbe Kanal liegt im committeten `a2_vorarbeit.json` (Teil B, Commit 363f3d9, oeffentlich).** `teil_B_sigma30.dispersion.pre.{ALL, FRI, NONFRI, MODO, WE, FRI_W, FRI_MQ, FRI_M, FRI_Q}.CLUSTER.{n, sd}` mit 16..17 signifikanten Stellen; n: 1.165 = 167 + 998, 998 = 666 + 332, 167 = 128 + 39 (geprueft nur n und Stellenzahl). Daraus sind exakt ableitbar: |m_FRI - m_NONFRI|, |m_MODO - m_WE|, |m_FRI_W - m_FRI_MQ| auf r_pre der Vorperiode (dazu je Jahr, `pre_oc`, `pre_minus_fix1530`); wegen m_F - m_M = (m_F - m_NF) + (332/998)(m_WE - m_M) liegt |x_P| damit schon heute auf zwei Kandidaten fest. Vom Review der Vorarbeit nicht erkannt (dort nur der schwache Kanal B-3 Betrags-Quantile). Mit realen Werten **nicht** ausgerechnet | Ergebnisblindheit der Pilot-Route; die Blindheit haengt nur noch an Disziplin, nicht an den Daten | **A-2** |
| **B-3** | Bestaetigung (entscheidungsrelevant) | **Pilot-Power 0,027 bei 16,5 bp ist korrekte Folge, kein Fehler.** x_P ~ N(16,5; 4,10^2) muss c_A2 = 24,4 erreichen: (24,4 - 16,5)/4,10 = 1,93 -> 0,027 (eigene Rechnung 0,0275). Die Regel "Uebergabe iff Pilotpunkt >= MDE80prod des Testfensters" ist keine Wahl, sondern DEC-99 (6) (Pilotpunkt = A-priori-Erwartung) + DEC-94 (6)/DEC-103 E3 (C10 nur bei Produkt-Power >= 0,80 am Prior) - strukturgleich mit U-4 (DEC-101 E7). Jede Regel, die unter MDE80prod uebergibt, ordnet einen Prior mit Gate-Power < 0,80 dem C10-Test zu (Bruch von DEC-94 (6)). Die kleine Power ist eine Eigenschaft der Daten: SE je 12-Monats-Fenster 7,3..7,9 bp -> MDE80prod >= 22,8 bp in jeder DEC-konformen Lesart; **ein 16,5-bp-Effekt ist auf 12-Monats-Fenstern unter C10 nicht testbar, mit oder ohne Pilot**; die Route kauft nur die Chance auf Uebergabe bei Effekten ab ~24 bp. Vergleich mechanischer, vorab fixierbarer Regeln (Pilot-Power bei 16,5 / 25 bp) [rj3:pilot_power_by_rule]: R0 U-A2-Default c 24,36: 0,027 / 0,56; R1 P2''-Bedingung exakt als max(Zentrum + d95; z SE) (bivariat) c 23,77: 0,038 / 0,62 (Lesart, Richtung Testbarkeit gegen R0); R2 ohne Null-Faktor c 23,09: 0,054 / 0,68 (Testbarkeit, P-G3); R3 Stress-Linie c 27,15: 0,005 / 0,30 (Strenge); R5 untere 80-%-Schranke x_P - 0,84 SE_P >= c: 0,003 / 0,25 (Strenge, selektionsrobust); R4 nur t >= 2: 0,98 / 1,00 (verletzt DEC-94 (6), unzulaessig). **Mechanisch, vorab fixierbar und nicht in Richtung Testbarkeit gewaehlt ist R0** (oder strenger R3/R5); R1/R2 jetzt zu waehlen waere eine Gabelung nach Kenntnis der Pilot-Power-Tabelle (Muster DEC-93 H-1) und braucht das Etikett | keine (Information); Wahl R1/R2 waere Testbarkeit | A-4, A-9 |
| **B-4** | mittel | **Der "Null-Faktor" im Produkt ist eine Lesart, kein DEC-Text.** Herkunft (nachgerechnet): Faktor = P(Y >= d95_W) mit Y ~ N(kappa_W f pi, SD_null,W^2), SD_null,W = a_W x 43,26 x sqrt(sum_w (n_w - 1)/n_w) (gepoolte within-week-SD der Vorperiode, Kalender von W) = 6,70 / 6,24, d95_W = 1,6553 x SD = 11,10 / 10,33 (tau95 = MC-Maximum ueber V1..V3; exakt 1,6533), kappa 0,999 / 0,815. Er ist **kein Placebo**, sondern der q95-Term der PRD-Schwelle max(q95; z SE) auf **derselben** P2''-Statistik; DEC-103 E3/N7 (4a) verlangen das Produkt ueber die Placebo-Bedingungen. Als eigener Faktor behandelt das Produkt zwei stark korrelierte Ereignisse (Modell-Korrelation 0,91 W1 / 0,82 W2) als unabhaengig: MDE80prod 23,43 / 24,36 gegen 22,93 / 23,77 mit exakter P2''-Bedingung [rj3:W1/W2.mde80_product_P2exact] und 22,82 / 23,09 nur z. In W2 ist der Beitrag ueberwiegend echt (kappa 0,815: Null-Bedingung allein 19,1 > z 18,8). Default Strenge, als G-C5/P-G3 ausgewiesen | Strenge (Default), Alternativen Testbarkeit | A-4 |
| **B-5** | mittel | **Positivkontrolle: Kriterium (b) zu nachsichtig, Gate (4) fehlt in der Kette.** Injektion F = MDE80prod (Produkt 0,80), erwartete gemeinsame PASS-Quote dort ~0,87 (Herleitung 0,876 / 0,871; eigenes Modell plausibel: 0,91 / 0,89 bei 25 bp), Kriterium aber 0,734 aus H-32, wo die Erwartung 0,80 war (DEC-101 E8: Ziel so gewaehlt, dass die erwartete Quote 0,80 ist). Eine Pipeline mit wahrer Quote 0,75 besteht mit Wahrscheinlichkeit 0,72, mit 0,78 zu 0,95 [rj3:pk_pass_prob_at_true_rate] - die PK trennt eine um ~15 % ueberschaetzte Power-Zeile nicht. Analog DEC-101 E8 waere: Kriterium = erwartete Quote am Ziel - 2,3263 x Binomial-SE (~0,816 / 0,822) oder Ziel am gemeinsamen MDE80 (21,2 / 22,3) mit 0,734. Ausserdem: die Gate-Kette der PK enthaelt kein Negativ-Panel (Gate (4)) - "Gate-Kette = Test (N-1)" ist damit nicht erfuellt | Testbarkeit (PK verliert Trennschaerfe) | A-5 |
| **B-6** | mittel | **Gate (4) (Negativ-Panel) ist weder in der Power-Zeile noch in c_A2.** "Was die Schwelle deckt" (PILOT_ROUTE 2) nennt (1)-(3) und die Null; die Bedingung "XRP/BNB (beta-residualisiert) zeigt kein vergleichbares Delta" ist noch nicht mechanisch formuliert (Schwelle, SE-Regel) und kostet unter einem echten Effekt Power (Fehlauslosung durch Rest-Spillover oder Zufall). Die Aussage "am Pilotpunkt hat jedes Testfenster Produkt-Power >= 0,80" gilt nur ohne Gate (4) | Testbarkeit (c_A2 kann nur steigen) | A-6 |
| **B-7** | gering bis mittel | **Zwei verbundene Gabelungen nicht gemeinsam entschieden.** (a) Die Pilot-Schwelle skaliert die Null mit k_pred (U-4-woertlich, P-G2), der Test skaliert seine Null nach Default G-C7 nicht - die Regel deckt damit eine Bedingung, die der Test nicht hat (Strenge, aber inkonsistent; je 0,1 in k_pred +0,5 bp). (b) DEC-94 (5): "bindend ist die groessere SE ueber Quellen **und registrierte Kalibrierungen (stress)**"; die Herleitung fuehrt stress als Bericht (G-C3, Default zentral). Wird eine Stress-Kalibrierung registriert, bindet sie: c_A2 27,15 statt 24,36, Pilot-Power bei 16,5 bp 0,005 (Praezedenz GL-032: stress bindend). Beides ist ausgewiesen, aber die Default-Richtung von G-C3 ist relativ zum DEC-94-(5)-Wortlaut die weniger strenge | (a) Strenge; (b) Default zentral = Testbarkeit gegen die Stress-Lesart | A-4 |
| **B-8** | gering | **Funding-Termin nur fuer W2 belegt.** Die Pilotstufe laeuft auf der Vorperiode; die Austauschbarkeit "gleicher Funding-Termin" (E4-Argument) ist dort und in W1 UNBELEGT (nur DEC-84-Verweis fuer W1, Vorperiode gar nicht genannt). Die vorgeschlagene Schutzregel (G-C8) muss auch fuer den Pilot gelten | Austauschbarkeit | A-7 |
| **B-9** | gering | Redaktion/Konsistenz: (a) Regime-Tabelle: C10 mit Null-Faktor, der DEC-52-Zweig (OI 25 bp "DEC52") ohne Null-Bedingung - ungleiche Behandlung (folgenlos, solange P-G4 den Zweig ausschliesst). (b) T10: Spalte "c_A2 = max_W" mischt fuer die OI-Variante die Schwelle auf x_P (23,0 / 25,7) mit Ereignis-Skala-MDE in W1/W2. (c) CME-Referenzfenster (P3fix/P3all-Ausschluesse) ohne [sek]-Marke (DEC-103 E6 traegt sie). (d) DEC-103 E6 nennt Freitags-Futures mit Referenz 16:00 New York; die zugehoerige Stunde (19:00..21:00 UTC) liegt an allen Freitagen in P3all und steht nicht in der Kontaminationsliste (Wirkung vernachlaessigbar: 2 von 44 Slots an 52 von 260 Tagen; Beleg [sek]). (e) tau95 aus dem Maximum dreier MC-Schaetzungen (1,6553) statt exakt (1,6533; Faltung moeglich) - +0,02 bp, Strenge. (f) NULL_SIMULATION 3 "mit c = 1 ... 1..8 %": V3 sind 9 % | - | A-8 |
| **B-10** | gering | **Hash-Waechter nur gegen exakte Gleichheit** (Probe d: Labelzeile "real bis auf eine Woche" wird akzeptiert; offengelegt als "notwendig, nicht hinreichend"). `centred_replicates` nimmt eine frei uebergebene Labelmatrix; mit wenigen fast-realen Zeilen liesse sich der reale Kontrast zusammensetzen. Im Herleitungscode nicht genutzt | Ergebnisblindheit (Produktionscode) | A-8 |

## 3. Nachrechnung (eigener Code, andere Seeds; bp)

Null der Herleitung: 20.000 Replikate, Seed 103 + k. Eigene Null: 50.000 Replikate, Seeds 7001..7004, dazu die **exakte**
Verteilung der zentrierten Null (FFT-Faltung der Wochen-Gleichverteilungen, Gitter 0,0004..0,0005 bp). MC-Standardfehler
der SD bei 20.000 Replikaten ~SD/200 (0,04 / 0,03 / 0,02 / 0,02).

| Groesse | Herleitung | eigene Rechnung | Abweichung | Bemerkung |
|---|---|---|---|---|
| Null-SD V1 / V2 / V3 / VP (MC) | 7,52 / 6,02 / 4,51 / 3,75 | 7,50 / 6,00 / 4,50 / 3,74 | <= 0,02 | MC-Rauschen |
| Null-SD exakt | 7,52 / 6,00 / 4,49 / 3,74 | 7,52 / 6,00 / 4,49 / 3,74 | 0 | label-invariant, exakt |
| d95 reg. (MC Herleitung gegen exakt) | 12,44 / 9,78 / 7,39 / 6,14 | exakt 12,44 / 9,76 / 7,31 / 6,18 (eigene MC 12,33 / 9,80 / 7,32 / 6,20) | 0,00 / +0,02 / +0,08 / -0,04 | jeweils im MC-Band der Herleitung |
| d99 reg. | 17,57 / 13,56 / 10,22 / 8,73 | exakt 17,59 / 13,59 / 10,20 / 8,75 | <= 0,03 | MC |
| d95 / d99 Gegenrichtung | 12,25 / 17,44; 10,08 / 14,41; 7,47 / 10,64; 6,19 / 8,70 | exakt 12,32 / 17,30; 10,00 / 14,06; 7,48 / 10,63; 6,14 / 8,64 | <= 0,35 (d99) | MC (99-%-Rand) |
| tau95 je Fenster; Transfer | 1,655 / 1,624 / 1,638 / 1,638; 1,6553 | exakt 1,653 / 1,627 / 1,627 / 1,651; Max 1,6533 | +0,002 | B-9 (e) |
| Exzess-Kurtosis / Schiefe exakt | -0,034 / -0,085 / -0,032 / -0,016; -0,026 / 0,055 / 0,065 / -0,021 | identisch | 0 | Null praktisch normal |
| SE analytisch P2'' (c_bind) / c = 1 | 8,25 / 5,69 / 5,31 / 4,10; 7,59 / 5,20 / 4,89 / 3,77 | 8,25 / 5,69 / 5,31 / 4,10; 7,59 / 5,20 / 4,89 / 3,77 | 0 | |
| SE analytisch P3fix / P3all | 8,66 / 6,45 / 6,06 / 4,43; 7,39 / 4,77 / 4,78 / 3,66 | identisch | 0 | |
| bindende SE P2'' (Quelle) | 8,25 a / 6,02 N / 5,31 a / 4,10 a | 8,25 a / 6,00 N / 5,31 a / 4,10 a | MC | V2: Null bindet (bestaetigt) |
| bindender Schwellenterm | z x SE in allen Fenstern; Marge 1,13 / 0,13 / 1,34 / 0,59 | z x SE; Marge gegen exaktes d95 1,13 / 0,11 / 1,42 / 0,56 | MC | |
| c_bind E / P2'' / P3fix / P3all | 1,149 / 1,318 / 1,168 / 1,000 | 1,149 / 1,318 / 1,168 / 1,000 | 0 | eigene Bartlett/Batch-Means |
| Same-Day-rho (Fr r_pre gegen 15:30 / P3all) | -0,159 / -0,110 | -0,159 / -0,110 | 0 | |
| Klassen-SD VP E / P2'' / P3fix / P3all | 43,83 / 42,45 / 61,39 / 8,53 | identisch | 0 | |
| sigma_within gepoolt / stress (V1) | 43,26 / 48,61 | 43,26 / 48,61 (klassisch gepoolt 43,00) | 0 | |
| N W1: E / P2'' / P3fix / P3all | 52 / 208 / 248 / 260 | identisch | 0 | |
| N W2 | 52 / 159 / 247 / 259 | identisch | 0 | |
| W2 permutierbar / fest; kappa W1 / W2 | 40 / 12; 0,999 / 0,815 | 40 / 12; 0,9988 / 0,8154 | 0 | 12 Freitage 2026-04-10..06-26 identisch; 48 Mo-Do-Futures-Tage ab 2026-04-06 |
| SD Null-Verschiebung iid W1 / W2 | 0,23 / 2,97 | 0,23 / 2,97 | 0 | |
| SE_bind W1: P2'' / P3fix / P3all | 7,34 / 7,93 / 6,56 | 7,34 / 7,93 / 6,56 | 0 | |
| SE_bind W2 | 7,58 / 7,93 / 6,56 | 7,58 / 7,93 / 6,56 | 0 | |
| Null-SD Transfer / d95 W1 / W2 | 6,70 / 11,10; 6,24 / 10,33 | 6,70 / 11,08; 6,24 / 10,32 (exaktes tau) | -0,02 | tau |
| MDE80 Einzel je Bedingung W1 (z_P2'' / Null / z_P3fix / z_P3all) | 18,2 / 16,8 / 19,7 / 16,3 | 18,25 / 16,74 / 19,71 / 16,31 | <= 0,06 | |
| dto. W2 | 18,8 / 19,1 / 19,7 / 16,3 | 18,84 / 19,09 / 19,73 / 16,31 | 0 | |
| Einzel max (bindend) W1 / W2 | 19,7 / 19,7 | 19,71 / 19,73 | 0 | P3fix bindet (Befund 1 bestaetigt) |
| Produkt mit Null-Faktor W1 / W2 | 23,4 / 24,4 | 23,43 / 24,36 (exaktes tau 23,44 / 24,38) | <= 0,04 | |
| Produkt nur z | 22,8 / 23,1 | 22,82 / 23,09 | 0 | |
| gemeinsam mit Null (Bericht) | 21,2 / 22,3 | 21,16 / 22,26 | <= 0,04 | eigenes Kovarianzmodell, Seeds 9001 / 9002 |
| OI 0,842: Produkt / gemeinsam | 25,8 / 27,3; 23,3 / 25,1 | 25,79 / 27,24; 23,23 / 25,02 | <= 0,08 | |
| stress: Produkt (u / OI) | 26,1 / 27,2; 28,8 / 30,5 | 26,07 / 27,15; 28,80 / 30,45 | <= 0,05 | |
| A3-Praxis Produkt | 29,2 / 29,7 | 29,18 / 29,69 | 0 | |
| Gitter Produkt 16,5 / 25 bp W1 / W2 | 0,31 / 0,26; 0,87 / 0,83 | 0,311 / 0,264; 0,868 / 0,829 | 0 | Regime GL012 / C10 |
| Gitter OI 25 bp | 0,76 / 0,69 | 0,763 / 0,694 | 0 | |
| Gabelung F-3 / F-4 (W2) | Einzel 21,6, Produkt 26,4 / Produkt 23,4 | 21,63, 26,34 / 23,44 | <= 0,06 | tau |
| Pilot: SE_P P2'' / P3fix / P3all; Null-SD; k_pred erw. | 4,10 / 4,43 / 3,66; 3,74; 1,095 | 4,097 / 4,426 / 3,661; 3,743; 1,0946 | 0 | |
| c_A2 (k = 1) W1 / W2 / max | 23,4 / 24,4 / 24,4 | 23,43 / 24,36 / 24,36 | 0 | |
| c_A2 bei k 1,095 / 1,2 / 1,3 | 24,8 / 25,3 / 25,8 | 24,76 / 25,27 / 25,83 (tau 1,6553) | 0 | |
| t am Schwellenwert | 5,95 | 5,95 | 0 | |
| Pilot-Power 16,5: Kontrast / Ereignis (k = 1) | 0,027 / 0,005 | 0,0275 / 0,0053 | 0 | B-3 |
| Pilot-Power 25: Kontrast / Ereignis; Zwei-Stufen | 0,56 / 0,21; 0,40 / 0,11 | 0,562 / 0,209; 0,404 / 0,111 | 0 | |
| Pilot-alpha; Zwei-Stufen-Fehlrate | <= 1,3e-9; <= 3,3e-12 | 1,30e-9 (bei c 24,40), 1,37e-9 (bei c 24,36); 3,4e-12 | Rundung | |
| Funding W2 je Symbol | 363 Tage, 1.089 Zeitstempel, 8h 363 (1,0000), 0 Duplikate | identisch; 0 Nicht-8h-Tage in allen 12 Monaten | 0 | |
| 08:00-Funding beide Symbole: E / P2'' / Mo-Do / WE | 52/52, 159/159, 207/207, 104/104; 0 in [07:00, 08:00) | identisch | 0 | |
| Kalender: ccy = Instrumentname; Name-Datum-Abweichungen; Ausreisser | 212.735 / 0 / 2020-08-27, 2024-08-19 | identisch (Vorperiode: 0 Ausreisser, 0 Mo-Do-Futures-Tage, 167 Freitage mit Futures) | 0 | |
| Determinismus | zwei Laeufe bitgleich | dritter Lauf (Kopie, sha256-gleich) bitgleich: c1 6eb71dca..., c2 579b67e9..., c3 1814f2ae..., a2_teilC.json 5741d90c... | 0 | |

**Fazit Nachrechnung:** keine Abweichung ausserhalb des Monte-Carlo-Rauschens; die bindenden SEs (P2'' 7,34 / 7,58,
P3fix 7,93 als groesster SE), die Schwellenterme, die MDE80-Zeilen, die W2-Struktur, der Funding-Befund und alle
Pilot-Zahlen sind korrekt.

## 4. Auflagen vor einem DEC-Nachtrag

- **A-1 (VETO-Aufhebung, vor jedem Commit):** `sd_of_null_shift_iid` der Vorperioden-Fenster entfernen oder mit einer
  U-freien Streuung rechnen (z. B. gepoolte within-week-SD oder aus den ohnehin ausgegebenen Klassen-SDs); Regel
  R-C12 erweitern: "keine Streuung einer Vereinigung zweier ausgegebener Klassen derselben Werte (und keine Groesse,
  aus der sie mit Kalenderwissen folgt)"; ein Test, der auf synthetischen Renditen prueft, dass aus dem Ausgabe-JSON
  kein Kontrastbetrag rekonstruierbar ist (Varianzzerlegung ueber alle Klassenpaare); `a2_teilC.json` neu bauen,
  neue sha256; die kanaltragenden Zwischendateien unter `a2_teilC/work/` loeschen oder ersetzen. Nachpruefung durch
  den Orchestrator (Schluessel- und Kanal-Scan) vor dem Commit.
- **A-2 (programmweit, B-2):** C.17-Vermerk und Feststellung des Orchestrators: "`a2_vorarbeit.json` (Commit 363f3d9)
  speichert implizit (Varianzzerlegung ALL/FRI/NONFRI, NONFRI/MODO/WE, FRI/FRI_W/FRI_MQ) die Betraege von
  Lage-Differenzen auf r_pre der Vorperiode; |x_P| ist daraus auf zwei Kandidaten bestimmbar; niemand hat die
  Kombination gebildet." Verbot fuer alle Agenten, Klassen-SDs geschachtelter Klassen zu kombinieren (Abweisungsliste);
  kuenftige Nuisance-Ausgaben ohne Vereinigungs-SD in voller Praezision (Pruefpunkt fuer jeden Review). Das Etikett
  "Lockerung" der Pilot-Route (PILOT_ROUTE 7) und die Nutzer-Vorlage nennen das ausdruecklich. Kein History-Rewrite.
- **A-3 (Zahlen-Nachtrag zu DEC-103 E7):** P3fix ist in der DEC-103-Fassung der Placebo mit dem groessten SE
  (7,93; Einzel-MDE80 19,7 statt 18,25 / 18,8); Produkt-Zuordnung 23,4 / 24,4 (mit Null-Faktor) bzw. 22,8 / 23,1;
  W2: 12 Wochen ohne P2''-Partner, kappa 0,815. Die W2-Gabelung F-1..F-4 vor jeder Zahl mit Prior fixieren
  (Default F-1, woertlich DEC-103 E4).
- **A-4 (Lesarten gemeinsam fixieren, mit Etikett "nach Kenntnis der Nuisance einschliesslich der Pilot-Power-Tabelle"):**
  (a) Null-Bedingung in der Zuordnung: eigener Faktor (Default, Strenge) mit der exakten P2''-Bedingung als
  Doppelausweis (22,9 / 23,8); (b) k_pred in der Pilot-Schwelle (P-G2) und Null-Skalierung im Test (G-C7)
  konsistent entscheiden; (c) G-C3: ausdruecklich festhalten, ob eine Stress-Kalibrierung registriert wird
  (DEC-94 (5): dann bindet sie, c_A2 27,15); (d) Pilot-Regel R0 als registrierte Regel; R1/R2 nur als Bericht.
- **A-5 (Positivkontrolle):** Kriterium (b) analog DEC-101 E8 vorab fixieren - entweder Injektionsziel am gemeinsamen
  MDE80 (erwartete Quote 0,80, Kriterium 0,734) oder Kriterium = erwartete Quote am Produkt-Ziel minus 2,3263
  Binomial-SE (~0,82); Gate (4) (Negativ-Panel, synthetisch ohne Injektion) in die Gate-Kette der PK.
- **A-6 (Gate (4)):** "kein vergleichbares Delta" mechanisch formulieren (Statistik, Schwelle, SE-Regel, beta aus
  der Vorperiode fixiert) und als Faktor in P_W(pi), MDE80prod und c_A2 aufnehmen (oder begruenden, warum seine
  Power ~1 ist); erst danach ist c_A2 endgueltig.
- **A-7 (Funding):** Funding-Zeitstempel BTCUSDT/ETHUSDT fuer die Vorperiode (Pilot) und W1 zaehlen (nur
  Zeitstempel, keine Rate); die Schutzregel G-C8 gilt fuer Pilot und Test.
- **A-8 (Produktionscode T0-T7):** Labelmatrix nur intern aus dem registrierten Seed erzeugen (keine oeffentliche
  Kontrastfunktion mit frei uebergebener Labelmatrix) plus Hash-Waechter; Kanal-Test aus A-1; tau95 exakt
  (Faltung) statt MC-Maximum; Redaktion B-9 (a)-(d), [sek] beim CME-Fenster.
- **A-9 (Nutzer-Vorlage):** an erster Stelle: "Beim einzigen belegten Prior (16,5 bp) uebergibt die Route mit
  ~2,7 % (Kontrast) bzw. ~0,5 % (Ereignis-Skala); mit ~97 % ist die Vorperiode danach verbraucht und A2 endet in
  GL-012 (Pilot). Ein 16,5-bp-Effekt ist auf 12-Monats-Fenstern unter C10 in keiner DEC-konformen Lesart testbar
  (MDE80prod >= 22,8 bp)." Dazu B-2.

## 5. Was NICHT folgt

- Kein Verdikt ueber A2, keine Effektgroesse, kein Vorzeichen, kein Prior; V-5b bleibt UNBELEGT; A2 bleibt ohne
  weiteren Schritt GL-012 vor der Registrierung.
- Das VETO betrifft die Ausgabedatei (Siegel), nicht die Rechnung: alle geprueften Zahlen stimmen. Es ist kein Urteil
  ueber die Pilot-Route; ob sie registriert wird, entscheidet der Nutzer (DEC-103).
- B-1/B-2 bedeuten nicht, dass ein Lage-Wert bekannt ist: weder Herleitung noch Review haben ihn gebildet. Sie
  bedeuten, dass die Blindheit der Vorperiode fuer A2 nur noch durch Disziplin geschuetzt ist.
- Die bestaetigte Pilot-Power ist keine Aussage ueber den Effekt, nur ueber Regel und Rauschboden; die Null-SD der
  Vorperiode ist keine Vorhersage der W1/W2-Streuung (Vol-Regime Faktor 1,7 zwischen V1 und V3).
- Die J-(i)-Null trennt keinen reinen Wochentagseffekt vom Verfallseffekt (Grenze von DEC-103 E4, offengelegt).
- Keine Aenderung an DEC-94/DEC-99/DEC-103 durch diesen Review; die Auflagen sind Vorlagen fuer einen DEC-Nachtrag.

## 6. Reproduktion

Skripte unter `/home/user/scinance_work/a2_teilC_review/` (nicht im Repo; Python 3, numpy 2.5.3, polars 2.0.0;
`python3 -I`):

| Skript | Zweck | sha256 |
|---|---|---|
| `rv_common.py` | Regeln RV-1..RV-5, Lader (eigener Datums-Assert vor jedem Preis), Kalenderklassen, Null J-(i) mit eigenem Waechter (keine Ziehung gleich der realen Belegung), exakte Null per FFT, P-3-Regel | ec1dcb5cb15654e885d7c682ed2efb302d1accee70e318344f40e02a40c5d9fd |
| `r1_main.py` | C-1/C-2/C-3 nachgerechnet -> `work/r1.json` | a4860829e8266884ecca50dd95f90b0516fbe833c310707713d7bf5c99fb26b5 |
| `r3_extra.py` | exakte P2''-Bedingung, Pilot-Regeln R0..R5, PK-Kriterium, Null-Verschiebung -> `work/r3.json` (nur Kalender und r1.json) | a0f2b4428dd883d8e3144bf4c2b231e3333331193a8f836b86e1dd129113a46a |
| `s0_leak_channel_presence.py` | Pruefpunkt 1: Vorhandensein und Stellenzahl der Kanal-Felder (Textebene, ohne Werte zu kombinieren) | 818a3f0ced5c645fcf9c032fac06fb09db08691dde31bf598147e3845b5082ff |
| `s2_guard_probe.py` | Waechter-Provokation auf einer sha256-gleichen Kopie von `c_common.py`/`test_c_guards.py` (nur Kalenderdaten und synthetische Zahlen) und synthetischer Kanal-Nachweis -> `work/s2_probe.json` | 267b714d8ea00a245ffc39349fa4f9a6a2f59a525636b2a2b7b0e1323ff19740 |

Ausgaben (je zwei Laeufe bitgleich): `r1.json` 0cff3fd65952830d9d6827403662496fce78bedca8be2650a30a5c26353bb61d,
`r3.json` 184e4cde9fecdac924322facd36d2bc255acf0ae5dd1eacf3ba632988a67e760, `s2_probe.json`
7599b8ac9f92189018c1bc8d494c420e010df3da927b9b77920facc958334327. Seeds: Null 7001..7004 (50.000 Replikate, exakte
Faltung Gitter 0,02 bzw. 0,05 bp ungewichtet), gemeinsame Power 9001 / 9002 (+10 stress, 400.000 Ziehungen),
bivariat 31031 (2.000.000), synthetisch 11 / 99 / 2026. Eingaben (sha256 = `EXTRACT_LOG.json`): Kerzen
c18a06bdd96174b4f2d794269d3d64daa1e206a8417b355e450a28e92e28ded5, Kalender
b1a9fc2285358ef22f78262343b562f2ff28e755676d198af99b6e94d67981a8, Funding
ba6eb8de325ca274b317e247009e866754b599284538f8a31712c633006e0903. Code der Herleitung wurde nicht importiert und nicht
fuer die Nachrechnung kopiert; Kopien nur fuer die Waechter-Probe und den Determinismus-Lauf (`work/probe_copy/`,
sha256-gleich mit `[aj-C:skripte_sha256]`), deren JSON-Ausgaben nach dem Hash-Vergleich geloescht (sie tragen den
B-1-Kanal). `print` nur sha256 und Zaehlungen.
