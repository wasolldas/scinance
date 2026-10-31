# A2-Vorarbeit Teil C (1): Null-Simulation J-(i) auf der Vorperiode, bindende SE, MDE80 neu, Funding-Intervall

> **Fassung 2 (2026-10-31) nach REVIEW_A2_TEILC.md: VETO-Aufloesung A-1, Auflagen A-2..A-9 eingearbeitet.** Zahlen der
> Fassung 1 unveraendert (sie stehen als "unskaliert (Fassung 1)" weiter in den Tabellen); neu sind die Zeilen nach den
> Festlegungen des Orchestrators und der Funding-Befund fuer Vorperiode und W1. Aenderungen am Ende ("Aenderungen gegen
> Fassung 1").
> ENTWURF der Herleitung (Gate-Design/Rauschboden), Stand 2026-10-31. **Nichts registriert, nichts beschlossen, kein
> Verdikt.** Entscheiden und registrieren darf nur der Orchestrator. A2 bleibt ohne weiteren Schritt GL-012 vor der
> Registrierung (DEC-103, V-5b UNBELEGT).
> **Etikett:** "A2-Vorarbeit Teil C (EXP-CLOCK, DEC-103). Renditen nur 2021-03-24..2024-05-31 (1-min-Kerzen), Kalender
> nur <= 2026-06-30 (ohne Preisfelder), Funding-Zeitstempel nur 2021-03-24..2026-06-28 (ohne Rate). Ausgegeben werden nur
> Streuung, Quantil-Abstaende vom Null-Zentrum, Kurtosis, Zaehlungen, Schwellen und Powers; **kein Mittel, kein Median,
> kein Vorzeichen** irgendeiner Verfallstag-Rendite (r_pre, r_post, Differenz Ereignis minus Placebo); der Kontrast mit
> den realen Labels wird **nie gebildet** (Waechter R-C6, mit Test); **keine Streuung einer Vereinigung ausgegebener
> Klassen derselben Werte** (R-C12a, Kanal-Test). Kein Verdikt, nichts registriert." (`label` in `a2_teilC.json`)
> **Festlegung des Orchestrators (2026-10-31, nach Kenntnis der Nuisance einschliesslich der Pilot-Power-Tabelle,
> Richtung Strenge):** (a) Null-Bedingung in der Zuordnung als eigener Faktor, exakte bivariate P2''-Bedingung als
> Doppelausweis-Bericht; (b) der Test skaliert seine Null wie DEC-101 E2 (q95_eff = max(0, m) + k (q95 - m),
> k = max(1, SE_Lauf / Null-SD)), die Pilot-Schwelle behaelt k_pred (U-4 woertlich); (c) eine Stress-Kalibrierung
> (Fenster V1 2021-06..2022-05: Klassen-SDs und sigma_within) wird mitregistriert und **bindet** (DEC-94 (5), Praezedenz
> GL-032), zentral ist Bericht; (d) Pilot-Regel R0 registriert, R1/R2 Bericht, R3/R5 strengere Alternativen; (e)
> PK-Kriterium (b) = erwartete PASS-Quote am Ziel minus 2,3263 x Binomial-SE, Gate (4) in der PK-Kette; (f) Gate (4)
> mechanisch, als Faktor 0,95 je Negativ-Symbol in P_W(pi) (vorlaeufig, UNBELEGT bis Negativ-Panel-Daten). Die
> Alternativen stehen jeweils als Bericht daneben (Doppelausweis).
> **Quellen:** DEC-103 (bindend), DEC-94 (3)/(4)/(5), DEC-98 N5/N7, DEC-99 (3)/(8), DEC-101 E2/E7/E8, PRD 5.2, Teil A/B
> Fassung 2 (`PLACEBO_DESIGN_A2.md`, `NUISANCE_SIGMA30.md`, `ENTSCHEIDUNGSVORLAGEN.md`, `a2_vorarbeit.json` sha256
> 9a2f5ac9...), `REVIEW_A2_VORARBEIT.md`, `REVIEW_A2_TEILC.md`, `src/bybit_edge/research/power_p1.py` (benutzt, nicht
> nachgebaut). Daten: `/home/user/scinance_work/hf_data/raw/` (vier Dateien, sha256 gegen `EXTRACT_LOG.json` geprueft).
> **Kuerzel:** `[aj-C:<pfad>]` = `a2_teilC.json` -> `<pfad>` (`teil_C1` Null-Simulation/SE/MDE80, `teil_C2` Funding,
> `teil_C3` Pilot-Regel, `kanal_scan_R_C12a`); `[aj-B:...]` = `a2_vorarbeit.json` (Teil B); `[S:<datei>]` = Skript unter
> `/home/user/scinance_work/a2_teilC/` (nicht im Repo; sha256 in `[aj-C:skripte_sha256]`). Einheit bp = 1e-4 Log-Rendite;
> Cluster x = (r_BTC + r_ETH)/2 je Tag; "reg." = in registrierter Richtung (negativ, DEC-103 E2).
> **Waechter / Siegel:** Kerzen-Datums-Assert auf `symbol`/`start_ms` allein vor jeder Preisspalte (R-C1); Kalender nur
> `ccy`/`type`/`instrument_name`/`timestamp` (Spaltenmenge geprueft, `position` nicht gelesen, Preisfelder existieren
> nicht), Zeilen > 2026-06-30 -> Abbruch; Funding nur `symbol`/`fts`. Die einzige Kontrast-Funktion
> (`PermNull.centred_replicates`) leitet den realen Label-Vektor selbst aus den Daten ab und verweigert jede Zeile mit
> dessen sha256 (R-C6). Jedes Ausgabe-Dict passiert `guard_keys` (mean/median/q50/sign/vorzeichen/effect/delta/drift/
> centre/zentrum/loc/observed ...) **und** `assert_no_variance_channel` (R-C12a: keine Klasse {series, n, sd}, deren n die
> Summe der n anderer Klassen derselben Reihe ist). `print` nur sha256 und Zaehlungen. Keine Siegeldatei, kein
> Harvest-Client, kein Netz, nichts unter `data/harvest`.
> **C.17 (gesehen in diesem Teil):** Streuung, Quantil-Abstaende, Kurtosis/Schiefe der permutierten Null; Klassen-SD je
> 12-Monats-Fenster fuer E, P2'', P3fix, P3all; Same-Day-Korrelationen (Abhaengigkeitsmasse); Kalender-Zaehlungen bis
> 2026-06-30; Funding-Zeitstempel 2021-03-24..2026-06-28. **Intern berechnet, nie ausgegeben:** Wochen-Mittel der
> r_pre-Cluster als Zentrierung, Replikat-Mittel als Zentrierung von SD/Kurtosis, Mittel/Median in SD, Korrelation und c
> (wie Teil B). Das **Null-Zentrum** wird nicht gebildet; alle Quantile sind Abstaende davon. **Fassung 1 trug den Kanal
> B-1** (`sd_of_null_shift_iid` = SD der Vereinigung E u P2'' x Kalenderfaktor, 12 Stellen, neben den Klassen-SDs): daraus
> war |Kontrast| je Vorperioden-Fenster, fuer VP also |x_P|, exakt ableitbar - **niemand hat diese Kombination gebildet**
> (Review: nur synthetisch gezeigt); das Feld ist entfernt, die kanaltragenden Zwischendateien (`work/c1.json`,
> `c1_pre.json`, `a2_teilC_run1/2.json` und Entwicklungs-Kopien unter /tmp) sind geloescht und kanalfrei neu erzeugt.

## 0. Befund in Kuerze

1. **Null J-(i) gebaut (DEC-103 E4), Waechter bestanden, Kanal geschlossen.** Je 12-Monats-Fenster der Vorperiode und
   gepoolt 20.000 Replikate (Seed 103 + Fenster), je Woche genau ein Freitags-Label unter {Freitag, Mo-Do}, Anzahl
   erhalten; alle 80.000 Replikat-Zeilen gegen den Hash des realen Label-Vektors geprueft; 13 Tests (synthetische
   Renditen) bestanden, darunter der neue Kanal-Test (A-1); zwei Laeufe bitgleich. Kanal-Scan der JSON: 20
   Klassen-Eintraege, **0 Tripel derselben Reihe**; 3 Zaehl-Koinzidenzen nur ueber verschiedene Reihen (P3all = E + P2''
   in der Anzahl, aber andere Werte). Die Null ist label-invariant und praktisch normal (Exzess-Kurtosis exakt
   -0,09..-0,02, |Schiefe| exakt <= 0,07).
2. **Null-SD gegen analytische SE (P2''):** V1 7,52 gegen 8,25 (0,91); V2 6,02 gegen 5,69 (**1,06 - die Null bindet**);
   V3 4,51 gegen 5,31 (0,85); gepoolt 3,75 gegen 4,10 (0,92), gegen c = 1 3,77 (0,995) [aj-C:teil_C1.pre_windows].
3. **Bindende SE je Testfenster (stress bindend nach Festlegung (c)):** P2'' 8,25 (W1) / 8,52 (W2), P3fix 8,66 / 8,67,
   P3all 7,39 / 7,39 (alle analytisch; Null 7,53 / 7,01). Zentral (Bericht): 7,34 / 7,58, 7,93 / 7,93, 6,56 / 6,56.
4. **Schwelle max(q95; z_krit x SE):** unskaliert bindet ueberall z_krit x SE (tau95 1,624..1,655 gegen 1,645). **Mit
   der skalierten Null (Festlegung (b))** wird der Null-Term k x d95 = tau95 x SE_bind und bindet, sobald tau95 > z_krit:
   V1 und W1/W2 um +0,08..0,09 bp (= (tau95 - z_krit) x SE bei Null-Zentrum 0); in W2 kommt das Zentrum der 12 festen
   Freitage hinzu (max(0, m), unter H0 SD 2,97 / 3,34 bp, unter einem Effekt ~0,18 x Effekt).
5. **P3-Bedingungen:** Unter J-(i) gilt exakt T_P3(J) - E = N_P/(N_P + W) x (T_P2''(J) - E); die P3-Null-Bedingung ist
   identisch mit der von P2''. Default: J-(i) als eine Pipeline-Null; die Tageszeit-Permutation wird nicht gebaut.
6. **Befund 1 (Fassung 1, bestaetigt):** P3fix hat in der DEC-103-Fassung den groessten SE (zentral 7,93 gegen 7,34 /
   7,58). **Befund 2 (bestaetigt):** in W2 sind 12 von 52 Wochen nicht permutierbar (kappa 0,815).
7. **MDE80 neu (P-1, Ereignis-Skala, W1 / W2), bindend = stress, skaliert, x Gate (4) (vorlaeufig): 29,0 / 32,1 bp**;
   ohne Gate-(4)-Faktor 26,6 / 29,3; zentral 26,0 / 28,8; Fassung 1 (zentral, unskaliert) 23,4 / 24,4; exakte bivariate
   P2''-Bedingung (Bericht) zentral unskaliert 22,9 / 23,8, stress skaliert 25,4 / 28,5 (ohne Gate (4)). Einzel (max ueber
   Bedingungen) stress 21,5 (P3fix) / 26,1 (Null-Bedingung W2). Regime nach Produkt: **auf jedem Gitterpunkt GL012**
   (25 bp: Produkt 0,65 / 0,54).
8. **Funding (C-2):** Vorperiode (Pilot) 1.165 / 1.165, W1 365 / 365, W2 363 / 363 Tage im 8h-Takt (00/08/16 UTC) fuer
   BTCUSDT und ETHUSDT (Anteil 1,0000); Freitage und P2'' in allen drei Perioden zu 100 % mit 08:00-Funding in beiden
   Symbolen; kein Termin in [07:00, 08:00); die Schutzregel G-C8 betrifft in Pilot und Test **0 Tage**.
9. **Dateiuebergreifend (offengelegt, Entscheidung des Orchestrators):** innerhalb der JSON keine geschachtelte Klasse;
   gegen das committete `a2_vorarbeit.json` (Teil B) ist die gepoolte P3fix-Klasse der Vorperiode (r_1530, Mo-Fr ohne
   Monatsend-Freitage, n 794) **die Vereinigung der Teil-B-Klassen fix1530 MODO (666) und FRI_W (128)** - daraus folgt
   |Mittel r[15:30] an Wochen-Freitagen minus an Mo-Do| der Vorperiode (eine Wochentags-Lage des 15:30-Slots, **nicht**
   die Pilotstatistik und kein P3-Kontrast); nicht gebildet. E und P2'' sind mit Teil-B-Klassen identisch (keine neue
   Information; deren Zerlegungen sind B-2). Abschnitt 7, Gabelung G-C9.

## 1. Daten, Pruefungen, Regeln

| Stueck | Befund |
|---|---|
| Eingaben | sha256 aller vier Dateien = `EXTRACT_LOG.json` (Schluessel kline / settlements / funding / funding_pre_w1) [aj-C:teil_C1.inputs_sha256, teil_C2.inputs_sha256] |
| 1-min-Kerzen | BTCUSDT / ETHUSDT je 1.677.600 Zeilen = 1.165 Tage x 1.440 Minuten, 2021-03-24..2024-05-31 (Assert vor jeder Preisspalte), 0 doppelte Minuten, 0 Luecken, 0 nicht-positive Schlusskurse [aj-C:teil_C1.kline_meta] |
| Reproduktion Teil B | Cluster-SD Freitag / Mo-Do und c_bind 1,1491 / 1,3177 bitgleich zu Teil B [aj-C:teil_C1.teil_B_reproduction] |
| Kalender | 212.735 Zeilen (delivery 175.657, settlement 37.078), gelesen nur `ccy`/`type`/`instrument_name`/`timestamp`; die Spalte `ccy` ist in allen 212.735 Zeilen gleich dem Instrumentnamen, die Waehrung kommt aus dem Namenspraefix BTC-/ETH-; Verfallsdatum im Namen = UTC-Tag des Zeitstempels in allen 174.931 Options- und 726 Futures-Deliveries; Ausreisser-Tage (> 60 s) bis 2026-06-30 genau 2020-08-27 und 2024-08-19. Vorperiode: alle 1.165 Tage mit BTC- und ETH-Optionsdelivery, 0 Ausreisser, 0 Mo-Do-Futures-Tage, 167 Freitage mit Futures-Delivery - reine Wochentagsklassen; Vorab-Lauf `--pre-only` und voller Lauf in allen Vorperioden-Abschnitten bitgleich |
| Funding | W2-Extrakt 2.178 Zeitstempel, Vorperiode/W1-Extrakt 9.360 (je Symbol 4.680 = 1.560 Tage x 3; Quelle laut Orchestrator `bybit/rest.fundingRateAll`, nur Zeitstempel), 0 Duplikate, alle auf voller Sekunde |
| Regeln | R-C1..R-C12 (Fassung 1) und R-C12a, R-C13..R-C18 (Fassung 2) im Docstring von `c_common.py`, jeweils vor der ersten Zahl geschrieben |

**Mengen nach DEC-103 (R-C4)** je Fenster: E = alle Freitage (W+M+Q) ohne Ausreisser-Tage; P2'' = Mo-Do ohne
Ausreisser- und ohne Futures-Tage (Vorperiode: alle Mo-Do); P3fix = Slot [15:30, 16:00) an Mo-Fr ohne Monatsend-Freitage;
P3all = je Tag (1/n_s) x Summe der n_s Halbstunden ausserhalb [07:00, 09:00) an Mo-Fr (n_s = 44, an Monatsend-Freitagen
ohne [14:00, 16:00): 40, CME-Referenzfenster GMT/BST nach DEC-103 E6 [sek]); Wochenende in keiner Menge. r_pre =
ln(C[07:59] / C[07:29]); am ersten Extrakt-Tag fehlt die 00:00-Halbstunde -> kein P3all-Wert. Fenster der Vorperiode:
V1 2021-06-01..2022-05-31, V2 2022-06-01..2023-05-31, V3 2023-06-01..2024-05-31, gepoolt VP 2021-03-24..2024-05-31.
**Kontaminationsliste P3all (Fassung 2, B-9 (d), [sek]):** DEC-103 E6 nennt fuer Freitags-Futures der CME die Referenz
16:00 New York; die Stunde davor ([19:00, 20:00) UTC in EDT, [20:00, 21:00) UTC in EST) liegt an allen Freitagen in
P3all (2 von 44 Slots an 52 von 260 Tagen je Fenster). Vermerkt, nicht ausgeschlossen (Zahlen unveraendert); Gabelung
"an Freitagen ohne [19:00, 21:00)" mit Richtung Reinheit, Wirkung auf die SE vernachlaessigbar.

## 2. Die Null J-(i): Definition, Eigenschaften, Waechter

**Definition (R-C5, DEC-103 E4).** Je ISO-Woche, beschraenkt auf das Fenster, sei U_w = {Freitag} u {P2''-Tage der
Woche}. Ein Replikat gibt das Freitags-Label genau einem Tag aus U_w (gleichverteilt), die uebrigen Tage von U_w sind
Placebo. P2''-Tage in Wochen ohne Ereignis-Freitag bleiben Placebo, Freitage ohne P2''-Partner bleiben Ereignis
(beides "fest"); die Anzahl W der Ereignis-Labels ist erhalten. Statistik eines Replikats = Kontrast Ereignis-Mittel
minus P2''-Mittel von x. 20.000 Replikate je Fenster, Seed 103 + Fensterindex (DEC-103 E4 verlangt >= 1.000).

**Zentrierte Form (nur sie wird gebildet).** Mit a = 1/W + 1/N_P gilt fuer jedes Replikat

    T(J) - E_perm[T] = a x Summe_w (x_{w,J_w} - xquer_w)          (Summe ueber die permutierbaren Wochen)

E_perm[T] (das Null-Zentrum) ist eine gewichtete Summe von Wochenmitteln - eine Lagegroesse; es wird weder gebildet noch
ausgegeben. Bei vollen Wochen ist es exakt 0; Randwochen verschieben es um einen kleinen Betrag, dessen Streuung aus
Kalender und **sigma_within** (gepoolte within-week-SD, label-invariant) folgt - Fassung 2: nicht mehr aus der SD der
Vereinigung (R-C12a). Alle Quantile sind **Abstaende vom Null-Zentrum**: d95 reg. = -q_0,05 der zentrierten Null, d99
reg. = -q_0,01, dazu die Gegenrichtung. Das obere Quantil in registrierter Richtung ist "Zentrum + d95"; im Testlauf wird
es auf W-Daten gebildet.

**Eigenschaften.** (i) Label-Invarianz: die Verteilung haengt nur von den Wochen-Multimengen ab (Test T-7). (ii) Exakte
Kumulanten: SD = a x sqrt(Summe_w s_w^2) mit der Populationsvarianz s_w^2 innerhalb der Woche; Monte Carlo und exakt
stimmen auf 0,01..0,02 bp (T1). (iii) Unter einem Effekt mu an allen Ereignis-Tagen: E[T_real - E_perm T] = kappa x mu,
kappa = a x Summe_w (n_w - 1)/n_w (volle Wochen: 1). (iv) Keine Zwischen-Wochen-Varianz, keine Autokorrelation; SD
entspricht der iid-SE (c = 1) der Vorperiode (gepoolt 3,75 gegen 3,77). (v) sigma_within ist kein Vereinigungs-Kanal:
die Vereinigungs-SD folgt aus ihr nur mit der Zwischen-Wochen-Quadratsumme, die nicht ausgegeben wird.

**Waechter (R-C6, R-C12a) und Tests.** Die einzige Funktion, die aus Labels einen Kontrast bildet, leitet den realen
Label-Vektor selbst aus den Tagesdaten ab, bildet dessen sha256 und verweigert vor jeder Beruehrung der Renditen jede
Zeile mit diesem Hash, ebenso fehlgeformte Zeilen. Tests [S:test_c_guards.py], nur synthetische Renditen: T-1 reale
Zeile mit x = None -> RealLabelError, T-2 reale Zeile unter 50 permutierten -> verweigert, T-3 permutierte Zeilen
passieren, T-4 fehlgeformte Matrizen verweigert, T-5 Ereignismenge != Freitage verweigert, T-6 exakte SD = Monte Carlo,
T-7 Label-Invarianz, T-8 P3-Identitaet, T-9 Schluessel-Waechter, T-10 Kerzen-Datums-Assert, T-11 Klassenregel;
**Fassung 2:** T-12 Kanal-Test - der Vorperioden-Lauf auf synthetischen Kerzen (realer Kalender, Zufallspfad mit
t-Rauschen) liefert keine Klasse derselben Reihe mit n_k = n_i + n_j; eine eingepflanzte Vereinigungs-SD (der Kanal der
Fassung 1) wird vom Scan erkannt und verweigert, und die Varianzzerlegung rekonstruiert auf diesen synthetischen Zahlen
|Kontrast| auf 1e-9 (der Kanal ist real); T-13 skalierte Null = Phi(kappa pi / SE - tau). **13 / 13 bestanden.**
Grenzen (offengelegt, B-10): der Hash-Waechter prueft exakte Gleichheit - eine Zeile "real bis auf eine Woche" wird
angenommen, und `centred_replicates` nimmt eine frei uebergebene Labelmatrix; im Herleitungscode nicht genutzt
(Labelmatrix nur aus `draw_labels`); Vorgabe fuer den Produktionscode in Abschnitt 7 (A-8).

## 3. C-1 Ergebnisse auf der Vorperiode

### T1 Null J-(i) je Vorperioden-Fenster (P2''-Kontrast, Cluster x, bp)

| Fenster | N_E / N_P'' | Wochen permutierbar (n_w) | Null-SD MC / exakt | d95 reg. [MC-95-%-Band] | d99 reg. | d95 / d99 Gegenrichtung | tau95 = d95/SD | Exzess-Kurtosis MC / exakt | Schiefe exakt | sigma_within | SD der Null-Verschiebung (iid, aus sigma_within) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| V1_2021-06..2022-05 | 52 / 209 | 52 (4:1, 5:51) | 7,52 / 7,52 | 12,44 [12,21; 12,64] | 17,57 | 12,25 / 17,44 | 1,655 | -0,016 / -0,034 | -0,026 | 48,61 | 0,35 |
| V2_2022-06..2023-05 | 52 / 209 | 52 (3:1, 5:51) | 6,02 / 6,00 | 9,78 [9,60; 9,98] | 13,56 | 10,08 / 14,41 | 1,624 | -0,060 / -0,085 | 0,055 | 38,80 | 0,39 |
| V3_2023-06..2024-05 | 53 / 209 | 53 (2:1, 5:52) | 4,51 / 4,49 | 7,39 [7,26; 7,51] | 10,22 | 7,47 / 10,64 | 1,638 | -0,054 / -0,032 | 0,065 | 29,28 | 0,29 |
| VP_2021-03-24..2024-05-31 | 167 / 666 | 167 (3:1, 5:166) | 3,75 / 3,74 | 6,14 [6,01; 6,29] | 8,73 | 6,19 / 8,70 | 1,638 | -0,019 / -0,016 | -0,021 | 43,26 | 0,07 |

### T2 Null-SD gegen analytische SE je Vorperioden-Fenster, bindende SE (DEC-94 (5)), Schwellen-Term (unskaliert / skaliert R-C13)

| Fenster | Bedingung | SD Klasse E / Placebo (Reihe) | SE analytisch c_bind / c=1 | SE Teil-B-Art (VP-SD, Fenster-N) | Null-SD (P3: N_P/(N_P+W) x) | Null/analytisch | SE_bind (Quelle) | z_krit x SE_bind | d95 reg. | k x d95 (R-C13) | bindender Term unskaliert / skaliert |
|---|---|---|---|---|---|---|---|---|---|---|---|
| V1_2021-06..2022-05 | P2ss | 49,37 / 47,45 (r_pre) | 8,25 / 7,59 | 7,34 | 7,52 | 0,911 | 8,25 (analytisch) | 13,57 | 12,44 | 13,66 | z_krit x SE / skaliertes Null-Quantil |
| V1_2021-06..2022-05 | P3fix | 49,37 / 62,11 (r_1530) | 8,66 / 8,09 | 7,92 | 6,02 | 0,695 | 8,66 (analytisch) | 14,24 | 9,96 | - | z_krit x SE (Null-Bed. = P2'') |
| V1_2021-06..2022-05 | P3all | 49,37 / 9,67 (p3all_slot_mean) | 7,39 / 6,90 | 6,56 | 6,02 | 0,814 | 7,39 (analytisch) | 12,16 | 9,96 | - | z_krit x SE (Null-Bed. = P2'') |
| V2_2022-06..2023-05 | P2ss | 31,73 / 40,03 (r_pre) | 5,69 / 5,20 | 7,34 | 6,02 | 1,059 | 6,02 (Null-Simulation) | 9,91 | 9,78 | 9,78 | z_krit x SE / z_krit x SE |
| V2_2022-06..2023-05 | P3fix | 31,73 / 61,08 (r_1530) | 6,45 / 6,02 | 7,92 | 4,82 | 0,747 | 6,45 (analytisch) | 10,62 | 7,83 | - | z_krit x SE (Null-Bed. = P2'') |
| V2_2022-06..2023-05 | P3all | 31,73 / 8,12 (p3all_slot_mean) | 4,77 / 4,45 | 6,56 | 4,82 | 1,012 | 4,82 (Null-Simulation) | 7,93 | 7,83 | - | z_krit x SE (Null-Bed. = P2'') |
| V3_2023-06..2024-05 | P2ss | 32,26 / 29,83 (r_pre) | 5,31 / 4,89 | 7,28 | 4,51 | 0,850 | 5,31 (analytisch) | 8,73 | 7,39 | 8,69 | z_krit x SE / z_krit x SE |
| V3_2023-06..2024-05 | P3fix | 32,26 / 51,70 (r_1530) | 6,06 / 5,65 | 7,87 | 3,60 | 0,594 | 6,06 (analytisch) | 9,96 | 5,89 | - | z_krit x SE (Null-Bed. = P2'') |
| V3_2023-06..2024-05 | P3all | 32,26 / 5,90 (p3all_slot_mean) | 4,78 / 4,46 | 6,50 | 3,60 | 0,753 | 4,78 (analytisch) | 7,86 | 5,89 | - | z_krit x SE (Null-Bed. = P2'') |
| VP_2021-03-24..2024-05-31 | P2ss | 43,83 / 42,45 (r_pre) | 4,10 / 3,77 | 4,10 | 3,75 | 0,916 | 4,10 (analytisch) | 6,74 | 6,14 | 6,71 | z_krit x SE / z_krit x SE |
| VP_2021-03-24..2024-05-31 | P3fix | 43,83 / 61,39 (r_1530) | 4,43 / 4,13 | 4,43 | 3,00 | 0,678 | 4,43 (analytisch) | 7,28 | 4,91 | - | z_krit x SE (Null-Bed. = P2'') |
| VP_2021-03-24..2024-05-31 | P3all | 43,83 / 8,53 (p3all_slot_mean) | 3,66 / 3,42 | 3,66 | 3,00 | 0,819 | 3,66 (analytisch) | 6,02 | 4,91 | - | z_krit x SE (Null-Bed. = P2'') |

**Lesart (nur Streuung).**
- **SD der Null je Fenster folgt dem Vol-Regime** (7,52 -> 6,02 -> 4,51 bp, Faktor 1,7); gepoolt 3,75 bp. Die Null ist
  normal (Kurtosis ~0) - der Merkposten "Normal-Naeherung bei Kurtosis 5..10" (Teil B Abschnitt 7) ist fuer die
  Null-Bedingung von D_i erledigt.
- **Null gegen analytisch:** die analytische Linie liegt in V1, V3 und gepoolt um 9..18 % ueber der Null; mit c = 1
  stimmen beide auf 1..9 % ueberein (B-9 (f)). In **V2 bindet die Null** (6,02 gegen 5,69), weil die Freitags-SD dort
  klein ist (31,7 gegen Mo-Do 40,0).
- **Schwelle:** unskaliert liegt z_krit x SE_bind ueberall ueber d95 reg. (1,13 / 0,13 / 1,34 / 0,59 bp; 99 %: 1,62 /
  0,45 / 2,13 / 0,80). Mit der skalierten Null (R-C13) bindet in V1 der Null-Term (k 1,098, k x d95 13,66 gegen 13,57,
  +0,09 bp), in V2 ist k = 1 (SE_bind ist die Null-SD), in V3 und VP bleibt z_krit x SE.
- **Vergleich mit Teil B 7,34:** die Teil-B-Art (gepoolte Klassen-SD, Fenster-N) gibt je 12-Monats-Fenster 7,28..7,34;
  die Null je Fenster liegt nur in V1 darueber (7,52).

## 4. Welche Null gilt fuer P3fix und P3all (Default-Vorschlag mit Richtung)

**Identitaet (exakt, R-C6, Test T-8).** Unter J-(i) bleiben die P3-Placebomengen fest; nur das Ereignis-Mittel bewegt
sich. Fuer jedes Replikat und am realen Label gilt

    T_P3(J) - E_perm[T_P3] = N_P / (N_P + W) x (T_P2''(J) - E_perm[T_P2''])      (Faktor 0,80 bei vollen Wochen)

Die Null-Bedingung einer P3-Bedingung ist damit **dasselbe Ereignis** wie die Null-Bedingung von P2''; das P3-Zentrum
(Tageszeit-Lage) muss nie berechnet werden und wird nicht berechnet. Das gilt unskaliert wie skaliert (k kuerzt sich
ebenso, wenn der Test die P3-Nullen mit demselben k skaliert; sonst ist die P3-Null-Bedingung schwaecher als die von
P2'' und bindet nicht).

| Vorlage | Inhalt | Folge | Richtung |
|---|---|---|---|
| **N3-1 (Default-Vorschlag)** | J-(i) ist die eine Pipeline-Null fuer alle drei Bedingungen (PRD 5.2; DEC-103 E4 woertlich) | P3-Null-Bedingungen = P2''-Null-Bedingung; fuer P3fix/P3all bindet z_krit x SE_P3; nichts Zusaetzliches zu bauen; label-invariant | Referenz |
| N3-2 | Tageszeit-Permutation innerhalb des Tages (J-(ii)) | nicht label-invariant (das unpermutierte Replikat ist der beobachtete Kontrast), vor einem Pilot nicht berechenbar, Hash-Waechter unanwendbar; zweite Null = neue Gabelung | Strenge (zusaetzliche, nicht redundante Bedingung); **nicht gebaut** |
| N3-3 | keine Permutations-Null fuer P3 | wegen der Identitaet im Ergebnis gleich N3-1 | gleich N3-1 |

**SE der P3-Bedingungen:** analytisch (c_bind der gepoolten P3-Reihen: P3fix 1,168, P3all 1,000; Same-Day-Kovarianz
Ereignis/Placebo nur wenn erhoehend: rho -0,159 an Wochen-Freitagen gegen r[15:30], -0,110 an Freitagen gegen P3all).

## 5. Uebertragung auf die Testfenster W1 / W2: bindende SE, Schwelle, MDE80 neu

**Regel (R-C8, R-C13, R-C14).** Analytische SE mit den Klassen-SDs und c_bind, N aus dem Kalender; Null-SD = a_W x
sqrt(sigma_w^2 x Summe_w (n_w - 1)/n_w) mit der Wochenstruktur des Testfensters; d95 = tau95 x Null-SD (tau95 = 1,6553,
groesster MC-Tail-Faktor der drei 12-Monats-Fenster, Strenge; exakt per Faltung 1,6533, Review B-9 (e)); k_W = max(1,
SE_bind,W / Null-SD_W). **Bindend ist die Stress-Kalibrierung** (V1: Klassen-SDs, sigma_w 48,61; Festlegung (c));
zentral (gepoolte Vorperiode, sigma_w 43,26) ist Bericht. SE_bind = max(analytisch, Null) je Bedingung (DEC-94 (5)).

Transfer: sigma_within gepoolt 43,26, Stress (V1_2021-06..2022-05, bindend nach R-C14) 48,61; tau95 = 1,6553, tau99 = 2,3380

### T3 Struktur der Testfenster und bindende SE je Bedingung (stress bindend, zentral Bericht)

| Fenster / Linie | N_E / N_P'' / N_P3fix / N_P3all | Wochen perm. / fix | kappa | SE_bind P2'' / P3fix / P3all | groesster SE | Null-SD / d95 | k (R-C13) | SD Null-Verschiebung | Schwelle P2'': z SE / d95 / k d95 | bindend unskaliert / skaliert |
|---|---|---|---|---|---|---|---|---|---|---|
| W1 stress | 52 / 208 / 248 / 260 | 52 / 0 | 0,999 | 8,25 / 8,66 / 7,39 | P3fix | 7,53 / 12,47 | 1,096 | 0,26 | 13,58 / 12,47 / 13,66 | z_krit x SE / skaliertes Null-Quantil (+ max(0, Zentrum)) |
| W1 zentral | 52 / 208 / 248 / 260 | 52 / 0 | 0,999 | 7,34 / 7,93 / 6,56 | P3fix | 6,70 / 11,10 | 1,095 | 0,23 | 12,07 / 11,10 / 12,15 | z_krit x SE / skaliertes Null-Quantil (+ max(0, Zentrum)) |
| W2 stress | 52 / 159 / 247 / 259 | 40 / 12 | 0,815 | 8,52 / 8,67 / 7,39 | P3fix | 7,01 / 11,61 | 1,215 | 3,34 | 14,01 / 11,61 / 14,10 | z_krit x SE / skaliertes Null-Quantil (+ max(0, Zentrum)) |
| W2 zentral | 52 / 159 / 247 / 259 | 40 / 12 | 0,815 | 7,58 / 7,93 / 6,56 | P3fix | 6,24 / 10,33 | 1,214 | 2,97 | 12,46 / 10,33 / 12,54 | z_krit x SE / skaliertes Null-Quantil (+ max(0, Zentrum)) |

### 5.1 Bindende SE und Schwelle

- **P2'':** SE_bind stress 8,25 / 8,52 (zentral 7,34 / 7,58), Quelle analytisch. Schwelle unskaliert: z_krit x SE bindet
  (13,58 / 14,01 gegen d95 12,47 / 11,61). **Skaliert (Festlegung (b)):** k = 1,096 / 1,215, Null-Term k x d95 = 13,66 /
  14,10 = tau95 x SE -> der skalierte Null-Term bindet um +0,09 bp bei Zentrum 0; gegenueber dem unskalierten Null-Term
  steigt er um (k - 1) x d95 = 1,19 / 2,49 bp. In W2 ist k groesser, weil SE_bind die Streuung des festen Zentrums
  (12 Wochen) enthaelt, die Null-SD nicht; im Testlauf kommt dort max(0, Zentrum) hinzu. Der Satz "die Schwelle steigt um
  hoechstens (tau95 - z_krit) x SE" gilt daher nur fuer ein Null-Zentrum <= 0 (W1: SD 0,26 bp); in W2 nicht.
- **P3fix:** SE_bind stress 8,66 / 8,67 (zentral 7,93 / 7,93) - groesster SE des Satzes (Befund 1).
- **P3all:** SE_bind stress 7,39 / 7,39 (zentral 6,56 / 6,56).

### 5.2 MDE80 neu (P-1, power_p1)

Modell je Bedingung: z-Bedingungen Phi(pi_j / SE_j - z_krit) (power_p1.window_power); Null-Bedingung von P2'' skaliert
Phi((kappa f pi - k d95) / (k SD_null)) = Phi(kappa f pi / SE - tau95) (R-C13; die Streuung der zentrierten Statistik ist
nach der Skalierungslogik k x SD_null = SE_bind; unskaliert, Fassung 1: Phi((kappa f pi - d95) / SD_null)); Gate (4) als
Faktor 0,95^2 = 0,9025 (vorlaeufig, R-C15). Zuordnung = Produkt der Einzel-Powers (DEC-103 E3, Festlegung (a)); exakte
bivariate P2''-Bedingung und gemeinsame Power (Monte Carlo 400.000, Seeds 1031/1032, +10 stress) sind Bericht.

### T4 MDE80 neu (P-1, bp, Ereignis-Skala; W1 / W2)

| Linie | Einzel max (bindende Bed.) | Produkt nur z | Produkt unskaliert (Fassung 1) | Produkt skaliert (a)+(b) | **Produkt skaliert x Gate (4) (bindend, vorlaeufig)** | bivariat exakt (Bericht): skaliert W1 / W2 // unskaliert W1 / W2 | gemeinsam skaliert x Gate (4) (Bericht) | A3-Praxis |
|---|---|---|---|---|---|---|---|---|
| stress, unabgeschwaecht | 21,5 / 26,1 (z_P3fix / null_P2ss) | 25,4 / 25,7 | 26,1 / 27,2 | 26,6 / 29,3 | **29,0 / 32,1** | 25,4 / 28,5 // 25,5 / 26,5 | 26,2 / 30,6 | 35,0 / 36,5 |
| stress, oi_0842 | 24,5 / 31,0 (null_P2ss / null_P2ss) | 27,3 / 27,8 | 28,8 / 30,5 | 29,7 / 33,5 | **32,5 / 37,2** | 27,5 / 32,1 // 27,6 / 29,2 | 28,9 / 35,7 | 38,4 / 41,2 |
| zentral, unabgeschwaecht | 19,7 / 23,2 (z_P3fix / null_P2ss) | 22,8 / 23,1 | 23,4 / 24,4 | 23,9 / 26,2 | **26,0 / 28,8** | 22,9 / 25,5 // 22,9 / 23,8 | 23,7 / 27,4 | 31,5 / 32,8 |
| zentral, oi_0842 | 21,8 / 27,6 (null_P2ss / null_P2ss) | 24,5 / 25,0 | 25,8 / 27,3 | 26,6 / 29,9 | **29,0 / 33,1** | 24,6 / 28,7 // 24,8 / 26,2 | 26,0 / 31,9 | 34,4 / 36,8 |

### T5 Einzel-MDE80 je Bedingung (Kontrast-Skala; W1 / W2)

| Linie | z P2'' | Null P2'' unskaliert (Fassung 1) | Null P2'' skaliert (R-C13) | z P3fix | z P3all |
|---|---|---|---|---|---|
| stress | 20,5 / 21,2 | 18,8 / 21,5 | 20,6 / 26,1 | 21,5 / 21,6 | 18,4 / 18,4 |
| zentral | 18,2 / 18,8 | 16,8 / 19,1 | 18,3 / 23,2 | 19,7 / 19,7 | 16,3 / 16,3 |

### T6 Prior-Gitter: Produkt-Power (skaliert x Gate (4)) W1 / W2, gemeinsam (Bericht), Regime nach Produkt

| Prior (bp) | stress: Produkt W1 / W2 | Regime | zentral: Produkt W1 / W2 | gemeinsam W1 / W2 | Regime | stress OI 0,842: Produkt W1 / W2 | Regime |
|---|---|---|---|---|---|---|---|
| 5,0 | 0,000 / 0,000 | GL012 | 0,001 / 0,001 | 0,08 / 0,05 | GL012 | 0,000 / 0,000 | GL012 |
| 8,0 | 0,004 / 0,003 | GL012 | 0,007 / 0,005 | 0,15 / 0,11 | GL012 | 0,002 / 0,002 | GL012 |
| 12,0 | 0,03 / 0,02 | GL012 | 0,06 / 0,04 | 0,31 / 0,23 | GL012 | 0,02 / 0,01 | GL012 |
| 16,5 | 0,16 / 0,11 | GL012 | 0,26 / 0,19 | 0,53 / 0,41 | GL012 | 0,10 / 0,07 | GL012 |
| 25,0 | 0,65 / 0,54 | GL012 | 0,77 / 0,67 | 0,83 / 0,74 | GL012 | 0,51 / 0,39 | GL012 |

**Lesart (nur Zahlen, keine Zuordnung als Urteil):** (a) Mit allen Festlegungen bindet in W1 die Konjunktion knapp,
in W2 die skalierte Null-Bedingung (kappa 0,815 und k 1,215): Einzel 26,1 bp (stress). (b) **Zuordnungs-MDE80 (stress,
skaliert, x Gate (4)) 29,0 / 32,1 bp**; die Beitraege gegen Fassung 1 (zentral 23,4 / 24,4): Stress-Kalibrierung +2,6 /
+2,8, Skalierung +0,6 / +2,1, Gate (4) +2,4 / +2,8 (W1 / W2, gerundet, in dieser Reihenfolge zugefuegt). (c) Exakte
bivariate P2''-Bedingung (Bericht): zentral unskaliert 22,9 / 23,8 (Review-Wert bestaetigt), stress skaliert 25,4 / 28,5
(beide ohne Gate (4)). (d) Die Teil-B-Produktzeile wird mit den Teil-B-SEs bitgenau reproduziert (21,90 / 22,18)
[aj-C:teil_C1.dec103_e7_reproduction_teil_B_se]. (e) Regime (B-9 (a): der DEC-52-Zweig traegt jetzt dieselben Faktoren
- Null-Bedingung des schwaecheren Fensters und Gate (4)): auf jedem Gitterpunkt und in jeder Linie GL012; 25 bp stress
Produkt 0,65 / 0,54, zentral 0,77 / 0,67.

### 5.3 Befund 2: J-(i) in W2 - 12 Wochen ohne P2''-Partner (Gabelung F-1..F-4)

Alle Mo-Do-Tage 2026-04-06..2026-06-25 tragen eine Futures-Delivery und fehlen in P2''; die 12 Freitage 2026-04-10,
04-17, 04-24, 05-01, 05-08, 05-15, 05-22, 05-29, 06-05, 06-12, 06-19, 06-26 haben in ihrer ISO-Woche keinen P2''-Tag und
bleiben unter J-(i) woertlich fest Ereignis: die Null streut nur ueber 40 Wochen, ihr Zentrum enthaelt 12/52 realer
Freitags-Renditen (unter einem Effekt kappa = 0,815), und der P2''-Placebo hat im letzten Viertel von W2 keinen Tag. Mit
der skalierten Null verstaerkt sich der Effekt (k 1,215). Die Gabelung ist vor jeder Zahl mit Prior zu fixieren (A-3).

### T6a W2-Gabelungen F-1 / F-3 / F-4 (Produkt-MDE80, Ereignis-Skala, unabgeschwaecht)

| Linie | Gabelung | N_E / N_P'' | kappa | SE_bind P2'' / P3fix / P3all | skaliert x Gate (4) | skaliert | unskaliert (Fassung 1) |
|---|---|---|---|---|---|---|---|
| stress | F1_woertlich | 52 / 159 | 0,815 | 8,52 / 8,67 / 7,39 | 32,1 | 29,3 | 27,2 |
| stress | F3_E_ohne_Freitage_ohne_P2ss_Partner | 40 / 159 | 1,000 | 9,42 / 9,56 / 8,41 | 32,7 | 30,1 | 29,4 |
| stress | F4_P2strich_alle_MoDo | 52 / 207 | 1,000 | 8,26 / 8,67 / 7,39 | 29,0 | 26,6 | 26,1 |
| zentral | F1_woertlich | 52 / 159 | 0,815 | 7,58 / 7,93 / 6,56 | 28,8 | 26,2 | 24,4 |
| zentral | F3_E_ohne_Freitage_ohne_P2ss_Partner | 40 / 159 | 1,000 | 8,37 / 8,70 / 7,47 | 29,3 | 26,9 | 26,4 |
| zentral | F4_P2strich_alle_MoDo | 52 / 207 | 1,000 | 7,34 / 7,93 / 6,56 | 26,1 | 23,9 | 23,4 |

| Gabelung | Inhalt | Richtung |
|---|---|---|
| **F-1 (Default bei Stille)** | J-(i) woertlich; die 12 Freitage bleiben fest Ereignis | Strenge; keine Aenderung an DEC-103 |
| F-2 | Permutationspartner in diesen Wochen = Mo-Do mit Futures-Tag (nur fuer die Null) | Testbarkeit; Austauschbarkeit verletzt; nicht gebaut (Grenze: Produkt nicht unter dem nur-z-Produkt) |
| F-3 | die 12 Freitage auch aus E (W2: N_E 40) | Strenge in der SE; aendert DEC-103 E1 |
| F-4 | in W2 P2' (alle Mo-Do) statt P2'' | Testbarkeit; kehrt DEC-103 E3/K-1 um (Inhomogenitaet W1/W2) |

## 6. C-2 Funding-Intervall BTCUSDT / ETHUSDT (Vorperiode = Pilot, W1, W2)

**Daten:** W2-Extrakt 2.178 Zeitstempel; Fassung 2 (Auflage A-7, Festlegung (g)): Extrakt 2021-03-24..2025-06-30 mit
9.360 Zeitstempeln (je Symbol 4.680 = 1.560 Tage x 3), sha256 d8cfdfb8... = `EXTRACT_LOG.json` ("funding_pre_w1"); nur
`symbol`/`fts`, keine Rate; 0 Duplikate, alle auf voller Sekunde [aj-C:teil_C2].

### T7 Funding-Zeitstempel je Periode und Symbol

| Periode | Symbol | Tage | Tage ohne Zeitstempel | Zeitstempel | Tage 8h (00/08/16) | Anteil 8h | Nicht-8h-Tage |
|---|---|---|---|---|---|---|---|
| VP_pilot_2021-03-24..2024-05-31 | BTCUSDT | 1165 | 0 | 3495 | 1165 | 1,0000 | 0 |
| VP_pilot_2021-03-24..2024-05-31 | ETHUSDT | 1165 | 0 | 3495 | 1165 | 1,0000 | 0 |
| W1_2024-07-01..2025-06-30 | BTCUSDT | 365 | 0 | 1095 | 365 | 1,0000 | 0 |
| W1_2024-07-01..2025-06-30 | ETHUSDT | 365 | 0 | 1095 | 365 | 1,0000 | 0 |
| W2_2025-07-01..2026-06-28 | BTCUSDT | 363 | 0 | 1089 | 363 | 1,0000 | 0 |
| W2_2025-07-01..2026-06-28 | ETHUSDT | 363 | 0 | 1089 | 363 | 1,0000 | 0 |

### T8 Funding um 08:00 in Ereignis- und Placebo-Menge (beide Symbole) und Schutzregel G-C8

| Periode | Menge | Tage | 08:00 in beiden Symbolen | 8h-Muster in beiden | Termin in [07:00, 08:00) BTC / ETH | Tage von G-C8 betroffen |
|---|---|---|---|---|---|---|
| VP_pilot_2021-03-24..2024-05-31 | E_Freitage | 167 | 167 (1,0000) | 167 | 0 / 0 | 0 |
| VP_pilot_2021-03-24..2024-05-31 | MoDo_alle | 666 | 666 (1,0000) | 666 | 0 / 0 | 0 |
| VP_pilot_2021-03-24..2024-05-31 | P2ss_MoDo_ohne_Futures | 666 | 666 (1,0000) | 666 | 0 / 0 | 0 |
| VP_pilot_2021-03-24..2024-05-31 | Wochenende | 332 | 332 (1,0000) | 332 | 0 / 0 | 0 |
| W1_2024-07-01..2025-06-30 | E_Freitage | 52 | 52 (1,0000) | 52 | 0 / 0 | 0 |
| W1_2024-07-01..2025-06-30 | MoDo_alle | 208 | 208 (1,0000) | 208 | 0 / 0 | 0 |
| W1_2024-07-01..2025-06-30 | P2ss_MoDo_ohne_Futures | 208 | 208 (1,0000) | 208 | 0 / 0 | 0 |
| W1_2024-07-01..2025-06-30 | Wochenende | 104 | 104 (1,0000) | 104 | 0 / 0 | 0 |
| W2_2025-07-01..2026-06-28 | E_Freitage | 52 | 52 (1,0000) | 52 | 0 / 0 | 0 |
| W2_2025-07-01..2026-06-28 | MoDo_alle | 207 | 207 (1,0000) | 207 | 0 / 0 | 0 |
| W2_2025-07-01..2026-06-28 | P2ss_MoDo_ohne_Futures | 159 | 159 (1,0000) | 159 | 0 / 0 | 0 |
| W2_2025-07-01..2026-06-28 | Wochenende | 104 | 104 (1,0000) | 104 | 0 / 0 | 0 |

**Befund:** In allen drei Perioden liegen die Funding-Termine an **jedem Tag und fuer beide Symbole genau auf 00:00,
08:00 und 16:00 UTC** (Vorperiode 1.165 / 1.165, W1 365 / 365, W2 363 / 363 Tage); kein Termin in [07:00, 08:00). Der
Auto-Switch kurzer Intervalle (DEC-84, ab 2025-10-30) hat BTCUSDT/ETHUSDT nicht erfasst. **Folge fuer P2'':** in Pilot
(E 167, P2'' 666), W1 (52 / 208) und W2 (52 / 159) tragen alle Ereignis- und Placebo-Tage das 08:00-Funding in beiden
Symbolen - das E4-Argument "J-(i) erhaelt den Funding-Termin" ist fuer Pilot und Test belegt (Review B-8 erledigt).
**Schutzregel G-C8 (Vorlage, fuer Pilot und Test):** "Tage, an denen eines der beiden Symbole kein Funding um 08:00:00 UTC
oder einen Termin in [07:30, 08:00) hat, werden aus Ereignis- und Placebo-Menge ausgeschlossen" - betrifft in Pilot, W1
und W2 **0 Tage** (Richtung neutral; Schutz gegen kuenftige Intervallwechsel, PIT aus dem Funding-Zeitplan). Grenze:
nur Zeitstempel - ob die Funding-Hoehe an Freitagen und Mo-Do vergleichbar ist, bleibt ungeprueft (Teil-B-Etikett).

## 7. Gabelungen mit Richtung (dieser Teil) und Vorgaben fuer den Produktionscode

| Nr. | Gabelung | Default (bei Stille) / Festlegung | Alternative(n) | Richtung der Alternative |
|---|---|---|---|---|
| G-C1 | Null fuer P3fix/P3all | N3-1 J-(i) als Pipeline-Null (Identitaet) | N3-2 Tageszeit-Permutation | Strenge, nicht label-invariant, nicht vor dem Pilot baubar |
| G-C2 | W2-Wochen ohne P2''-Partner | F-1 woertlich | F-2 / F-3 / F-4 | Testbarkeit / Strenge in SE / Testbarkeit |
| G-C3 | Kalibrierungs-Linie | **Festlegung (c): stress (V1) bindet** | zentral | Testbarkeit (Bericht) |
| G-C4 | Quantile | Abstand vom Null-Zentrum (Zentrum nie ausgegeben) | rohe Quantile | Siegel |
| G-C5 | Null-Bedingung in der Zuordnung | **Festlegung (a): eigener Faktor** | exakte bivariate Bedingung / nur z-Terme | Testbarkeit (Bericht) |
| G-C6 | Bindende Einzel-Bedingung | max ueber Bedingungen (DEC-94 (3), PRD 5.2) | P2'' als "bindender Einzel-Placebo" (DEC-103 E3 Wortlaut) | Testbarkeit |
| G-C7 | Skalierung der Null im Test | **Festlegung (b): skaliert wie DEC-101 E2** | unskaliert (DEC-103 E4 woertlich, Fassung 1) | Testbarkeit (W2 deutlich, Abschnitt 5.1) |
| G-C8 | Funding-Schutzregel | Regel vorab fuer Pilot und Test (0 Tage betroffen) | keine Regel | neutral |
| G-C9 | P3fix-Vereinigung gegen Teil B (Abschnitt 0 Punkt 9) | offengelegt, Zahlen unveraendert; Vermerk in die Abweisungsliste (A-2): Klassen-SDs geschachtelter Klassen auch dateiuebergreifend nie kombinieren | gepoolte P3fix-SD durch die geschichtete SD (innerhalb MODO/FRI_W) ersetzen | **nicht empfohlen:** die Differenz zur bereits gesehenen Fassung-1-Zahl (7,93 / 61,4; Review-Nachrechnung mit 12 Stellen) oeffnete einen neuen Differenzkanal |
| G-C10 | Gate (4) | Festlegung (f): Faktor 0,95 je Symbol, vorlaeufig | Power aus Daten (nach Negativ-Panel) | offen (UNBELEGT) |

**Vorgaben fuer den Produktionscode (A-8, nur notiert):** (1) die Labelmatrix entsteht nur intern aus dem registrierten
Seed (keine oeffentliche Kontrast-Funktion mit frei uebergebener Labelmatrix), plus Hash-Waechter; (2) der Kanal-Test
R-C12a (Klassen {series, n, sd}, Summen-Suche) laeuft auf jedem Ausgabe-Artefakt, auch dateiuebergreifend gegen die
Teil-B-Klassen; (3) tau95 exakt per Faltung statt MC-Maximum; (4) Regime-Tabellen mit denselben Faktoren in C10 und
DEC-52 (B-9 (a)); (5) CME-Fenster mit [sek] (B-9 (c)) und die 16:00-New-York-Stunde in der P3all-Kontaminationsliste
(B-9 (d)).

## 8. Was NICHT folgt

- Kein Verdikt, keine Effektgroesse, kein Vorzeichen, kein Prior (V-5b bleibt UNBELEGT); A2 bleibt ohne weiteren
  Schritt GL-012 vor der Registrierung. Mit den Festlegungen ist A2 auf jedem Gitterpunkt (bis 25 bp) GL012.
- Keine Registrierung, keine Design-Wahl ausser den als Festlegung des Orchestrators gekennzeichneten; DEC-103 wird nicht
  geaendert.
- Der Gate-(4)-Faktor 0,9025 ist eine Annahme bis zu den Negativ-Panel-Daten (UNBELEGT); alle Zeilen "x Gate (4)" sind
  vorlaeufig.
- Die Null-SD der Vorperiode ist keine Vorhersage der W1/W2-Streuung; W1/W2 wurden nicht beruehrt (nur Kalender und
  Funding-Zeitstempel).
- Die Null J-(i) trennt keinen reinen Wochentagseffekt vom Verfallseffekt (Grenze von DEC-103 E4).
- Die Entfernung des B-1-Feldes heilt nicht B-2 (Teil B) und nicht G-C9; beide liegen beim Orchestrator (A-2).

## 9. Reproduktion

Skripte `/home/user/scinance_work/a2_teilC/` (nicht im Repo): `c_common.py` (Regeln R-C1..R-C18, Waechter, Kanal-Scan,
Lader), `c1_nullsim.py` (C-1; Modus `--pre-only` nur Kerzen), `c2_funding.py` (C-2), `c3_pilot.py` (C-3), `c_build.py`
(JSON mit Kanal-Scan), `c_tables.py` (Tabellen), `test_c_guards.py` (13 Tests), `run_all.sh` (Tests, zwei volle
Laeufe, sha256-Vergleich, offizielles JSON). Seeds: Null 103 + Fensterindex (20.000 Replikate), Monte Carlo 1031/1032
(+10 stress, 400.000 Ziehungen), synthetischer Kanal-Test 2026/3. Zwei vollstaendige Laeufe bitgleich (`run_all.sh`): `work/c1.json` 536a491d8a2d2925ed8868ad15e43da7e7368c14aa173798b7b384cb8eedeb1b, `work/c2.json` e998d95f8751c3d048b22f06e7c18a234db5f2de10f5dc4c15787d9e3e783ffa, `work/c3.json` 797b881c2c16338ae2f6b6bea6e0ecdd6b1f6894f2cefba6be8d12c6f7870375; **`a2_teilC.json` (Fassung 2) sha256 8c01d72ece18e1c607b7ef585a88bef2ea19bca87c422c9e229780354bd17687**. Skripte (sha256, voll in `[aj-C:skripte_sha256]`): `c1_nullsim.py` 2422c38467feb712..., `c2_funding.py` aa8fef8798620602..., `c3_pilot.py` d7e4e343670232fc..., `c_build.py` 81dcedfb3f1436c7..., `c_common.py` 6e1cee9d3931cb65..., `c_tables.py` a2fdb5cae3b1e312..., `run_all.sh` 1c519973797d06c1..., `test_c_guards.py` b4d5af87b99793f7...; `power_p1.py` 74a8dedec983a0342af8378533d0e01b907a5293746d6b839dfebf2bfe36d111. Eingaben (sha256 = `EXTRACT_LOG.json`): Kerzen c18a06bdd96174b4f2d794269d3d64daa1e206a8417b355e450a28e92e28ded5, Kalender b1a9fc2285358ef22f78262343b562f2ff28e755676d198af99b6e94d67981a8, Funding W2 ba6eb8de325ca274b317e247009e866754b599284538f8a31712c633006e0903, Funding Vorperiode/W1 d8cfdfb829df985e552cc490643f47ff8b91f7152f6ea26b936b067576598f9b. **Kalender-Ableitung:** die Spalte `ccy` enthaelt den Instrumentnamen (identisch mit `instrument_name` in allen 212.735 Zeilen); die Waehrung kommt aus dem Namenspraefix BTC-/ETH- (Regex `^(BTC|ETH)-DDMMMYY(-Strike-C/P)?$`), `ccy` wird nur auf Gleichheit geprueft. Vorab-Lauf `c1_nullsim.py --pre-only` (nur Kerzen, Wochentagsklassen; `work/c1_pre.json` 154bcd016f1332b8b45a698d18fcaa97c0a58664aeca396b87ed29e7ed16b901, kanalfrei) und voller Lauf stimmen in allen Vorperioden-Abschnitten bitgenau ueberein. Die kanaltragenden Fassung-1-Dateien (`work/c1.json`, `c1_pre.json`, `a2_teilC_run1/2.json`, Entwicklungs-Kopien unter /tmp) wurden geloescht und durch die kanalfreien Fassung-2-Dateien ersetzt. `print` nur sha256 und Zaehlungen.

## Aenderungen gegen Fassung 1

1. **A-1 (VETO-Aufloesung):** `sd_of_null_shift_iid` (SD der Vereinigung E u P2'' x Kalenderfaktor) aus allen
   Vorperioden-Fenstern entfernt; Ersatz `sd_null_shift_iid_sigma_within` aus der gepoolten within-week-SD; Klassen-SDs
   als {series, n, sd}; Regel R-C12a und `assert_no_variance_channel` in jedem Ausgabe-Dict; Kanal-Test T-12 auf
   synthetischen Renditen; kanaltragende Zwischendateien geloescht und kanalfrei neu erzeugt; Scan-Ergebnis in
   `[aj-C:kanal_scan_R_C12a]` (0 Tripel derselben Reihe); dateiuebergreifende Pruefung gegen Teil B
   `[aj-C:teil_C1.cross_file_check_teil_B]` mit Befund G-C9.
2. **Festlegungen (a)-(c), (f) (Orchestrator):** skalierte Null (R-C13), Stress bindend (R-C14), Gate-(4)-Faktor
   (R-C15), exakte bivariate Bedingung als Bericht (R-C17); neue Zeilen in T3-T6, T6a; Fassung-1-Zahlen als
   "unskaliert (Fassung 1)" unveraendert ausgewiesen.
3. **A-7 / Festlegung (g):** Funding-Zeitstempel Vorperiode und W1 ausgezaehlt (R-C18); Schutzregel G-C8 fuer Pilot und
   Test (0 Tage).
4. **B-9:** (a) DEC-52-Zweig mit denselben Faktoren; (b) Pilot-Tabelle getrennt (PILOT_ROUTE T10); (c) [sek] beim
   CME-Fenster; (d) 16:00-New-York-Stunde in der P3all-Kontaminationsliste; (e) tau95 exakt als Vorgabe A-8; (f) "1..9 %".
5. **B-10** als Grenze offengelegt (Abschnitt 2); A-8-Vorgaben notiert (Abschnitt 7).
6. Neue sha256 von `a2_teilC.json`: siehe Abschnitt 9 (Fassung 1: 5741d90c..., verworfen).
