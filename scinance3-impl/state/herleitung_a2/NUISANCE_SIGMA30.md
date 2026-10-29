# A2-Vorarbeit Teil B: sigma30-Nuisance der Vorperiode 2021-03-24..2024-05-31 - NUR STREUUNG, KEIN MITTEL

> **Fassung 2 (2026-10-29) nach REVIEW_A2_VORARBEIT.md: Auflagen A-1..A-6 eingearbeitet.** Zahlen der
> Fassung 1 unveraendert (Rundung vereinheitlicht: SE zwei Stellen, MDE80 eine Stelle, W1 als Hauptwert, W2 in
> Klammern, wo die Rundung abweicht); Neues am Ende unter "Aenderungen gegen Fassung 1".
> ENTWURF der Herleitung (Nuisance/Power/Rauschboden), Stand 2026-10-29. Nichts hier ist registriert oder beschlossen;
> entscheiden darf nur der Orchestrator. **Kein Verdikt, keine Zuordnung als Urteil.**
> **Etikett:** wie Teil A (`label` in `a2_vorarbeit.json`): nur Streuungs-, Korrelations-, Autokorrelations-,
> Varianzfaktor- und Zaehlgroessen; **kein Mittel und kein Vorzeichen** von r_pre, r_post oder einer Differenz
> Ereignis minus Placebo wird ausgegeben oder gespeichert.
> **Ergebnisblindheit:** Kline-Extrakte BTCUSDT/ETHUSDT per Assert ohne Tag nach 2024-05-31 (vor jeder Rendite,
> `hfrv_common.load_kline` unveraendert wiederverwendet, zusaetzlich `assert_rv_day` auf dem letzten Tag). Mittelwerte
> entstehen nur intern als Zentrierung (SD, Kurtosis, ACF, Korrelation, Bootstrap-Summen) und werden nie ausgegeben,
> gespeichert oder angezeigt; MAD nutzt den Median nur intern. Waechter `no_mean` + `guard_keys` auf jedem
> Ausgabe-Dict (R-11). Lokaler Funding-Extrakt und Tageskerzen (reichen bis 2026-09-28) wurden **nicht** geoeffnet.
> Fassung 2: Datums-Assert auf `start_ms` allein (Spaltenlesung) **vor** jeder Preisspalte (`assert_kline_dates`, R-13);
> erweiterter Waechter `guard_keys_loc` (median/q50/loc/center/diff/contrast/minus nur auf dokumentierter Positivliste;
> keine unzentrierten Betrags-Quantile unter Differenz-Reihen, R-12), mit Selbsttest beim Import.
> **C.17 (Fassung 2):** unzentrierte Betrags-Quantile und 1,4826 x MAD je Klasse/Jahr/Serie wurden gesehen und
> ausgegeben, in Fassung 1 auch fuer die gepaarte Differenz-Reihe r_pre - r[15:30] (in Fassung 2 aus dem JSON
> entfernt, A-6); daraus wurde kein Lagewert abgeleitet. **W1/W2-Inventur:** die 2.0-Hypothesen H-01..H-18 sahen
> Bybit/Deribit-Daten 2026-03-27..2026-07-04 (Mikrostruktur, Sekunden- bis Minutenhorizont), darunter die
> 08:00-Slots 2026-03-27..2026-06-28 in W2; kein r_pre-Mittel ueber 07:30-08:00 wurde dort gebildet; Weiss et al.
> (2021-2023) liegt vor W1.
> **Kuerzel:** wie Teil A: `[aj-B:<pfad>]` = `a2_vorarbeit.json` -> `teil_B_sigma30`, `[aj-P:...]` -> `teil_B4_power`,
> `[aj-A:...]` -> `teil_A_oi_kalender_zeitlage`; `[S:<datei>]` unter `scratchpad/a2_vorarbeit/`; `[pb:A2]` = PROGRAMM_BILANZ
> 2.4; `[abg.]` abgeleitet; UNBELEGT; Fassung 2: `[aj-K:...]` -> `teil_B5_konjunktion`, `[aj-D:...]` -> `teil_B6_did`,
> `[aj-F:...]` -> `teil_A5_futures_kalender`. Einheit bp; "Cluster" x = (r_BTC + r_ETH)/2 je Tag; "gepoolt" = sqrt((s_BTC^2 +
> s_ETH^2)/2). Klassen: FRI = alle Freitage (W+M+Q), FRI_W Woche, FRI_M Monat, FRI_Q Quartal, FRI_MQ = M+Q, MODO = Mo-Do,
> WE = Sa/So, NONFRI = MODO+WE, ALL.

## 0. Befund in Kuerze

1. **sigma30 an [07:30, 08:00) (r_pre, close-to-close), 2021-03-24..2024-05-31** [aj-B:dispersion.pre.<Klasse>]: alle Tage BTC
   37,5 / ETH 47,2 / gepoolt 42,6 / Cluster 40,6 bp; Freitage 40,2 / 52,6 / 46,8 / 43,8 (n 167); Mo-Do 39,5 / 48,8 / 44,4 /
   42,5 (n 666); Wochenende 31,6 / 40,7 / 36,4 / 34,8 (n 332); Monat+Quartal 47,6 / 63,9 / 56,3 / 52,4 (n 39). Die
   PRD-Kette (36 bp, BTC-only) liegt fuer BTC nahe, unterschaetzt die **gepoolte** Freitags-SD um ~23 %.
2. **Vol-Regime:** gepoolte SD aller Tage 2021 59,4 / 2022 42,8 / 2023 26,3 / 2024 (bis 05-31) 35,9 - Faktor 2,3
   innerhalb der Vorperiode; das Stressjahr ist in allen Klassen 2021 [aj-B:dispersion.pre.<Klasse>.by_year].
3. **SD-Verhaeltnisse (gepoolt, Wochenblock-Bootstrap 2.000, Seed 27, 95-%-Band):** Freitag/Mo-Do 1,06 [0,85; 1,30];
   Woche/Mo-Do 0,99 [0,76; 1,27]; Monat+Quartal/Woche 1,29 [0,90; 1,78]; Wochenende/Mo-Do 0,82 [0,69; 0,98];
   [15:30, 16:00) alle Tage / [07:30, 08:00) Mo-Do 1,30 [1,17; 1,45] [aj-B:sd_ratios.fix1530_ALL/pre_MODO].
4. **rho(BTC, ETH) an [07:30, 08:00)** Pearson / Spearman: Freitage 0,781 / 0,769 [0,691; 0,859]; Mo-Do 0,848 / 0,823;
   alle Tage 0,837 / 0,801 [0,808; 0,861] - vertraeglich mit DEC-67 (0,815) und dem PRD-Arbeitswert 0,8 [aj-B:rho_btc_eth.pre].
5. **Autokorrelation ueber aufeinanderfolgende Ereignisse klein** (Freitage Lag 1..10 zwischen -0,16 und +0,14);
   Varianzfaktor nach P-3-Logik c_bind 1,15 (Freitage), 1,27 (Woche), 1,46 (Monat+Quartal, n 39), 1,32 (Mo-Do), 1,00
   (Wochenende, alle Tage); unter iid erzeugt dieselbe Regel Mediane 1,06..1,17 - die Werte sind mit c ~ 1 vertraeglich
   (Anteil iid-Simulationen >= beobachtet 0,08..0,51) [aj-B:persistence, aj-P:c_bind_iid_reference].
6. **SE(Kontrast) und MDE80 je 12-Monats-Fenster (zentral; P-1 / A3-Praxis; W1 (W2)):** D_i Freitag gegen Mo-Do 7,34 bp ->
   18,2 (18,3) / 24,4 bp; PRD_a (Placebo inkl. Wochenende) 6,90 -> 17,2 / 23,0; D_i_s (gepaarter Freitags-Slot 15:30) 11,15 ->
   27,7 / 37,1; D_ii Monat+Quartal gegen Woche 19,70 -> 49,0 / 65,6. Die Bilanz-Tabelle (5,13 / 11,28 bp) war um 34..43 %
   (woechentlich) bzw. 75 % (monatlich) zu optimistisch [aj-P:designs, aj-P:bilanz_reproduction].
7. **Feasibility (nur Zahlen, kein Urteil):** Mit dem Prior-Gitter erreicht D_i C10 je 12-Monats-Fenster erst bei
   ~18,2 (18,3) bp Kontrast gegen den bindenden Einzel-Placebo (Gitterpunkt 25 bp: C10; 16,5 bp: Fenster-Power 0,73,
   GL012); mit OI-Abschwaechung braucht es einen Ereignis-Effekt von ~21,7 bp. D_ii ist fuer jeden Gitterpunkt GL012 (16,5 bp [sek]: Power 0,21; 8,8 Jahre je Fenster).
   Ein Wochenverfalls-Prior existiert nicht (V-5b UNBELEGT) - nach PRD-Vorbedingung bleibt A2 GL-012.
8. **Fassung 2 (A-1, A-3, A-5):** gegen den ganzen Placebosatz {P2', P3fix, P3all} braucht D_i auf der Ereignis-Skala
   (P-1, W1) gemeinsam 19,8 bp, als Produkt der Einzel-Powers (Untergrenze, traegt nach Festlegung des Orchestrators die
   Zuordnung) 21,9 bp; mit OI-Abschwaechung 22,1 / 23,8 bp (6.5). Ohne die 48 Futures-Mo-Do-Tage in W2 (P2'') steigt
   die W2-SE von 7,34 auf 7,58 (MDE80 18,8, 6.7). Differenz-in-Differenzen: SE 12,62 (12,63), MDE80 31,4 bp (6.6).

---

## 1. Daten [aj-B:kline_meta, aj-B:class_day_counts]

| Stueck | Befund |
|---|---|
| Kline BTCUSDT / ETHUSDT | je 1.677.600 Zeilen, 2021-03-24..2024-05-31, 1.165 Tage x 1.440 Minuten, 0 Duplikate, 0 Zeitstempel neben voller Minute, 0 nicht-positive Schlusskurse (Pruefung `load_kline`, HF-RV R-1/R-2) |
| Klassen (R-4, Kalender gegen Deliveries geprueft) | FRI 167 (W 128, M 26, Q 13), MODO 666, WE 332, NONFRI 998, ALL 1.165; Ausreisser-Tage (Delivery > 60 s) in der Periode: keine |
| Slots | r_pre [07:30, 08:00), r_post [08:00, 09:00) (nur Streuung), Verschiebungen [07:30+k, 08:00+k) k = -3..+3 h, fester Slot [15:30, 16:00) (vor dem 16:00-Funding, keine Options-TWAP), P3-Baseline = (1/44) x Summe der 44 Halbstunden ausserhalb [07:00, 09:00), 48-Slot-Profil |
| Datenlage | BTC-1-min-Kerzen gibt es ab 2020-03-25, ETH ab 2021-03-15 (DEC-98 N4 (d)); die lokalen Extrakte decken 2021-03-24..2024-05-31 (gemeinsamer Zeitraum). Nicht geladen: BTC 2020-03-25..2021-03-23 |

## 2. Vorab fixierte Regeln (Docstring `a2v_common.py`, vor jeder Zahl)

R-1 Zeitgrenzen (Renditen <= 2024-05-31, Kalender/OI <= 2026-06-30); R-2 Feldfilter Settlements; R-3 Rendite-Gitter
(Preis am Gitterpunkt = close der dort endenden Kerze; r_pre = ln(C[07:59]/C[07:29])); R-4 Klassen und Ausschluss der
Ausreisser-Tage; R-5 Streuungsstatistiken (n, SD ddof 1, 1,4826 x MAD, Exzess-Kurtosis, Quantile von |r|, Jahre);
R-6 SD-Verhaeltnisse mit ISO-Wochen-Block-Bootstrap (alle Klassen gemeinsam, 2.000, Seed 27); R-7 rho Pearson/Spearman;
R-8 ACF 1..10 und c (Bartlett 4/8/13, Batch-Means 4/8/13 bei n/L >= 8, c_bind = max(1, Kandidaten); stationaerer
Bootstrap Bericht); R-9 SE je Design; R-10 Power nur mit `power_p1`; R-11 Waechter, Determinismus.
**Fassung 2 (vor jeder neuen Zahl in den Docstring geschrieben):** R-12 erweiterter Waechter (Lage-Schluessel nur auf
Positivliste, keine unzentrierten Betrags-Quantile unter Differenz-Reihen); R-13 `start_ms`-Assert vor jeder
Preisspalte; R-14 Futures-Kalender nur aus Namen/Typ/Datum; R-15 Konjunktion (Kovarianz der Kontraste = SE_E^2 +
rho_jk SE_j SE_k n_gemeinsam / sqrt(N_j N_k) mit gemessener Same-Day-Korrelation der Placebo-Reihen, Ereignis-
Placebo-Kovarianz 0 ohne Gutschrift; Monte Carlo 400.000 Ziehungen, Seed 94; Produkt der Einzel-Powers; MDE80 auf der
Ereignis-Skala per Bisektion mit gemeinsamen Zufallszahlen).
**Abweichung vom Auftragstext (vermerkt):** "MAD/1,4826" wird als **1,4826 x MAD** ausgegeben (die unter Normalverteilung
SD-konsistente Skalierung; MAD/1,4826 waere um den Faktor 2,2 kleiner und kein SD-Mass). Richtung neutral (Bericht).

## 3. B-1: sigma30 je Klasse

**r_pre [07:30, 08:00), 2021-03-24..2024-05-31** [aj-B:dispersion.pre.<Klasse>.<BTC|ETH|CLUSTER>, aj-B:sd_pre_bootstrap_band]

| Klasse | n | SD BTC | SD ETH | SD gepoolt | SD Cluster [95-%-Band] | 1,4826 x MAD BTC / ETH | Exzess-Kurtosis BTC / ETH | \|r\| q50 / q90 / q99 BTC |
|---|---:|---:|---:|---:|---|---|---|---|
| FRI (W+M+Q) | 167 | 40,2 | 52,6 | 46,8 | 43,8 [35,6; 52,7] | 28,9 / 37,2 | 4,9 / 4,6 | 20,0 / 63,7 / 137,6 |
| FRI_W | 128 | 37,8 | 48,9 | 43,7 | 41,1 [31,0; 52,2] | 24,4 / 32,4 | 5,4 / 7,5 | 17,7 / 63,2 / 114,4 |
| FRI_M | 26 | 35,8 | 56,6 | 47,4 | 44,6 [30,5; 54,7] | 36,5 / 46,3 | -0,6 / 0,6 | 25,8 / 53,1 / 83,5 |
| FRI_Q | 13 | 63,4 | 76,1 | 70,0 | 64,1 [35,6; 82,7] | 44,9 / 70,7 | 1,3 / -0,4 | 41,9 / 68,0 / 164,3 |
| FRI_MQ | 39 | 47,6 | 63,9 | 56,3 | 52,4 [39,3; 63,6] | 48,8 / 55,2 | 3,2 / 0,4 | 29,6 / 60,4 / 144,8 |
| MODO | 666 | 39,5 | 48,8 | 44,4 | 42,5 [37,0; 47,9] | 24,7 / 29,0 | 5,6 / 5,0 | 16,7 / 57,3 / 146,1 |
| WE | 332 | 31,6 | 40,7 | 36,4 | 34,8 [28,3; 41,5] | 16,0 / 21,8 | 9,6 / 10,1 | 10,9 / 45,7 / 142,6 |
| NONFRI | 998 | 37,0 | 46,3 | 41,9 | 40,1 [35,1; 45,0] | 21,7 / 26,7 | 6,6 / 6,2 | 14,6 / 54,2 / 151,6 |
| ALL | 1.165 | 37,5 | 47,2 | 42,6 | 40,6 [36,2; 45,0] | 22,7 / 27,4 | 6,3 / 6,0 | 15,3 / 55,4 / 152,3 |

Schwere Raender (Exzess-Kurtosis 5..10, 1,4826 x MAD ~0,6 x SD): Merkposten fuer die Normal-Naeherung der Power-Zeile,
vor allem bei N = 12 (Monat) je Fenster.

**Jahre (SD Cluster / gepoolt; n)** [aj-B:dispersion.pre.<Klasse>.by_year]

| Klasse | 2021 (ab 03-24) | 2022 | 2023 | 2024 (bis 05-31) |
|---|---|---|---|---|
| FRI | 58,7 / 61,3 (41) | 42,8 / 46,5 (52) | 35,2 / 37,4 (52) | 26,1 / 29,5 (22) |
| FRI_W | 58,1 / 60,7 (31) | 40,9 / 44,3 (40) | 30,1 / 31,6 (40) | 21,1 / 25,0 (17) |
| FRI_MQ | 61,7 / 64,2 (10) | 47,9 / 52,2 (12) | 48,6 / 52,6 (12) | 33,8 / 37,0 (5) |
| MODO | 58,1 / 61,1 (162) | 45,0 / 46,8 (208) | 21,4 / 22,5 (208) | 39,8 / 41,1 (88) |
| WE | 53,3 / 55,4 (80) | 29,6 / 31,4 (105) | 25,6 / 26,7 (105) | 20,1 / 21,5 (42) |
| ALL | 56,7 / 59,4 (283) | 40,7 / 42,8 (365) | 25,0 / 26,3 (365) | 34,4 / 35,9 (152) |

Das Freitag/Mo-Do-Verhaeltnis schwankt zwischen den Jahren stark (2023 1,64, 2024 0,66 Cluster) - kleine Jahres-n;
ueber die Periode 1,03 [0,81; 1,29] (Cluster).

**Andere Slots, alle Tage (SD BTC / ETH / gepoolt; Exzess-Kurtosis BTC / ETH)** [aj-B:dispersion.<slot>.ALL]

| Slot | SD BTC / ETH / gepoolt | Kurtosis | Verhaeltnis zu r_pre (gepoolt) [Band] |
|---|---|---|---|
| [04:30, 05:00) (k -3) | 34,9 / 42,2 / 38,7 | 23,4 / 6,8 | 0,91 [0,82; 1,01] |
| [05:30, 06:00) (k -2) | 37,7 / 48,8 / 43,6 | 28,0 / 21,4 | 1,02 [0,87; 1,20] |
| [06:30, 07:00) (k -1) | 43,5 / 52,7 / 48,3 | 35,0 / 20,3 | 1,13 [0,98; 1,28] |
| **[07:30, 08:00) r_pre** | 37,5 / 47,2 / 42,6 | 6,3 / 6,0 | 1 |
| [08:30, 09:00) (k +1, in r_post) | 41,6 / 57,9 / 50,4 | 8,4 / 15,7 | 1,18 [1,08; 1,29] |
| [09:30, 10:00) (k +2) | 40,3 / 50,4 / 45,6 | 12,0 / 9,0 | 1,07 [0,97; 1,19] |
| [10:30, 11:00) (k +3) | 37,2 / 49,8 / 43,9 | 7,2 / 11,1 | 1,03 [0,92; 1,15] |
| [15:30, 16:00) fest | 50,8 / 63,8 / 57,7 | 6,2 / 7,7 | 1,30 [1,17; 1,45] (gegen MODO-r_pre) |
| r_post [08:00, 09:00) (60 min) | 59,3 / 86,3 / 74,1 | 8,0 / 13,3 | je 30 min 1,23 [1,12; 1,35] |
| P3-Baseline (1/44 x Summe, 44 Halbstunden) | 7,1 / 9,0 / 8,1 | 3,5 / 6,7 | - |

**Fassung 2 (A-6):** Fuer die Differenz-Reihe r_pre - r[15:30] (`pre_minus_fix1530`, alle Klassen, Jahre und Serien)
sind die unzentrierten Betrags-Quantile aus dem JSON **entfernt** (528 Schluessel `abs_q50/90/95/99`); zentrierte
Quantile wurden nicht neu ausgegeben (das zentrierte q50 von |r - Median| ist MAD und steckt bereits in 1,4826 x MAD).
Die Differenz-Reihe traegt nur n, SD, 1,4826 x MAD, Kurtosis; der Waechter R-12 verhindert kuenftig Betrags-Quantile
unter Differenz-Reihen. Alle anderen Zahlen von `teil_B_sigma30` sind bitgleich zu Fassung 1.

**48-Slot-Profil (Cluster-SD, alle Tage)** [aj-B:sd_profile_48_slots.by_class.ALL.CLUSTER]: Minimum ~37 (03:30 und 04:30), r_pre-Slot
40,6, Spitzen 12:30-13:00 (73,9) und 13:30-14:00 (71,0) - die US-Makro-/Eroeffnungs-Slots (Hinweis A-1), danach 46..68
bis Mitternacht. Der Slot [07:30, 08:00) ist ein ruhiger Slot; jeder Placebo aus anderen
Tageszeiten traegt ein anderes Vol-Niveau.

**SD-Verhaeltnisse r_pre zwischen Klassen (Punkt [2,5 %; 97,5 %], 2.000 Wochenblock-Replikate)** [aj-B:sd_ratios]

| Verhaeltnis | BTC | ETH | Cluster | gepoolt |
|---|---|---|---|---|
| FRI / MODO | 1,02 [0,80; 1,27] | 1,08 [0,85; 1,34] | 1,03 [0,81; 1,29] | 1,06 [0,85; 1,30] |
| FRI_W / MODO | 0,96 [0,73; 1,24] | 1,00 [0,74; 1,31] | 0,97 [0,72; 1,27] | 0,99 [0,76; 1,27] |
| FRI_MQ / MODO | 1,21 [0,82; 1,66] | 1,31 [0,91; 1,69] | 1,24 [0,90; 1,58] | 1,27 [0,93; 1,61] |
| FRI_MQ / FRI_W | 1,26 [0,80; 1,85] | 1,31 [0,88; 1,85] | 1,28 [0,88; 1,81] | 1,29 [0,90; 1,78] |
| WE / MODO | 0,80 [0,66; 0,97] | 0,83 [0,69; 1,00] | 0,82 [0,68; 0,98] | 0,82 [0,69; 0,98] |
| FRI / WE | 1,27 [0,98; 1,67] | 1,29 [0,98; 1,66] | 1,26 [0,96; 1,65] | 1,28 [1,00; 1,65] |
| NONFRI / MODO | 0,94 [0,90; 0,99] | 0,95 [0,91; 1,00] | 0,94 [0,91; 0,99] | 0,94 [0,91; 0,99] |
| r_pre FRI / [15:30] FRI (gleiche Tage) | 0,72 [0,55; 0,95] | 0,79 [0,65; 0,95] | 0,74 [0,59; 0,92] | 0,76 [0,62; 0,93] |
| r_pre MODO / [15:30] MODO | 0,71 [0,60; 0,81] | 0,69 [0,60; 0,79] | 0,69 [0,61; 0,79] | 0,69 [0,61; 0,78] |

Lesart (nur Streuung): Freitags- und Mo-Do-Slots streuen gleich (Band enthaelt 1); Monats-/Quartalsfreitage tendenziell
+25..30 % (Band enthaelt 1, n 39); Wochenende signifikant ruhiger. Fuer die SE-Rechnung zaehlt, dass jede Klasse ihre
eigene SD bekommt (R-9), nicht eine gemeinsame sigma30.

## 4. B-2: rho(BTC, ETH) der 30-min-Renditen [aj-B:rho_btc_eth]

| Klasse | n | r_pre Pearson [Band] | r_pre Spearman | [15:30, 16:00) Pearson | r_post Pearson | r_pre Pearson je Jahr 2021 / 2022 / 2023 / 2024 |
|---|---:|---|---:|---:|---:|---|
| FRI | 167 | 0,781 [0,691; 0,859] | 0,769 | 0,855 | 0,883 | 0,832 / 0,793 / 0,801 / 0,642 |
| FRI_W | 128 | 0,790 [0,653; 0,882] | 0,736 | 0,879 | 0,869 | 0,839 / 0,780 / 0,820 / 0,484 |
| FRI_MQ | 39 | 0,767 [0,680; 0,881] | 0,855 | 0,730 | 0,904 | 0,864 / 0,825 / 0,845 / 0,742 |
| MODO | 666 | 0,848 [0,812; 0,877] | 0,823 | 0,853 | 0,879 | 0,836 / 0,878 / 0,819 / 0,879 |
| WE | 332 | 0,854 [0,798; 0,898] | 0,764 | 0,848 | 0,843 | 0,862 / 0,840 / 0,917 / 0,742 |
| ALL | 1.165 | 0,837 [0,808; 0,861] | 0,801 | 0,853 | 0,871 | 0,835 / 0,854 / 0,825 / 0,836 |

Vergleich: PRD-Arbeitswert 0,8 [sek], DEC-67 E4 0,815 [0,800; 0,828] (30-min, alle Slots, WP-7). Gemessen am r_pre-Slot:
0,78 (Freitag) .. 0,85 (Mo-Do); die Baender ueberdecken 0,815. Eine kleinere rho verkleinert die Cluster-Varianz
((1 + rho)/2); die SE-Rechnung nutzt daher die direkt gemessene Cluster-SD, nicht rho.

## 5. B-3: Autokorrelation ueber aufeinanderfolgende Ereignisse und Varianzfaktor c [aj-B:persistence.pre.<Klasse>.CLUSTER]

| Klasse (Cluster) | n | ACF Lag 1..5 | ACF Lag 6..10 | Bartlett 4 / 8 / 13 | Batch-Means 4 / 8 / 13 | stat. Bootstrap 4 / 8 | c_bind (BTC / ETH) |
|---|---:|---|---|---|---|---|---|
| FRI | 167 | 0,01 / 0,14 / 0,03 / -0,16 / -0,01 | -0,04 / -0,07 / 0,03 / -0,03 / -0,04 | 1,15 / 1,05 / 0,93 | 1,12 / 1,08 / 0,65 | 1,09 / 1,05 | **1,149** (1,16 / 1,18) |
| FRI_W | 128 | 0,10 / -0,05 / 0,01 / 0,04 / -0,07 | -0,01 / -0,12 / 0,02 / -0,12 / 0,03 | 1,12 / 1,03 / 0,89 | 1,25 / 1,27 / 0,53 | 1,07 / 1,06 | **1,269** (1,30 / 1,25) |
| FRI_MQ | 39 | -0,08 / 0,31 / 0,07 / 0,11 / 0,01 | -0,02 / -0,08 / -0,25 / -0,12 / -0,10 | 1,35 / 1,46 / 1,08 | 1,31 / - / - | 0,92 / 0,72 | **1,459** (1,34 / 1,65) |
| MODO | 666 | -0,11 / 0,07 / 0,02 / 0,04 / 0,04 | 0,05 / -0,01 / 0,04 / -0,01 / 0,01 | 0,93 / 1,05 / 1,10 | 0,91 / 1,08 / 1,32 | 0,96 / 1,00 | **1,318** (1,30 / 1,30) |
| WE | 332 | -0,02 / -0,12 / 0,07 / -0,01 / -0,06 | 0,16 / -0,03 / -0,01 / 0,03 / -0,08 | 0,89 / 0,91 / 0,89 | 0,82 / 0,95 / 0,85 | 0,92 / 0,90 | 1,000 |
| NONFRI | 998 | -0,10 / 0,01 / -0,02 / -0,02 / 0,06 | -0,00 / 0,04 / -0,08 / 0,02 / 0,02 | 0,82 / 0,84 / 0,86 | 0,84 / 0,85 / 0,73 | 0,86 / 0,90 | 1,000 |
| ALL | 1.165 | -0,09 / 0,01 / 0,01 / -0,02 / 0,00 | 0,05 / 0,00 / 0,05 / -0,04 / -0,05 | 0,86 / 0,88 / 0,88 | 0,82 / 0,92 / 0,82 | 0,89 / 0,85 | 1,000 |

Weitere Reihen (c_bind Cluster): [15:30, 16:00) alle Tage 1,094; gepaarte Differenz r_pre - [15:30] an Freitagen 1,099;
P3-Baseline alle Tage 1,123; r_post Freitage 1,000 [aj-B:persistence.<slot>]. ACF von x^2 (Vol-Clustering) als Bericht in
[aj-B:persistence.<slot>.<Klasse>.<CLUSTER>.acf_of_square].

**Einordnung (Referenz iid, gleiche Regel, 1.000 Normal-Reihen, Seed 27)** [aj-P:c_bind_iid_reference]: Median / q90 der
Regel unter iid: n 39: 1,06 / 1,70; n 128: 1,17 / 1,70; n 167: 1,16 / 1,63; n 332: 1,11 / 1,41; n 666: 1,08 / 1,29.
Anteil iid >= beobachtet: FRI_MQ 0,20, FRI_W 0,37, FRI 0,51, WE 1,00, MODO 0,08. **Erwartung bestaetigt:** Ereignisse
eine Woche auseinander tragen keine messbare Persistenz; c_bind > 1 ist ueberwiegend Auswahl-Bias der Max-Regel
(Richtung Strenge). Bindend bleibt c_bind (P-3-Logik, DEC-94 (4)); c = 1 wird als Bericht gefuehrt.

## 6. B-4: Placebo-SE, SE(Kontrast), MDE80 je Design

### 6.1 Die Formel [pb:A2] - Herleitung und Korrektur [abg.]

Je Cluster (Verfallstag i) x_i = (r_BTC,i + r_ETH,i)/2, also Var(x) = (s_B^2 + s_E^2 + 2 rho s_B s_E)/4. Mittel ueber
N_E Ereignisse mit Langfrist-Varianzfaktor c_E: Var(xquer_E) = c_E Var(x_E)/N_E; Placebo analog mit eigener SD, rho,
c_P, N_P. Kontrast Delta = xquer_E - xquer_P (Wortlaut PRD 5.2; hier nur als Statistik-Definition):

    SE(Delta)^2 = c_E Var(x_E)/N_E + c_P Var(x_P)/N_P - 2 Cov(xquer_E, xquer_P)

[pb:A2] `SE(Delta) = sqrt(sigma30^2 (1+rho)/(2N) + SE_placebo^2)` ist der Sonderfall c = 1, s_B = s_E = sigma30,
Cov = 0, mit SE_placebo nach derselben Cluster-Logik. **Bestaetigt als Struktur, mit fuenf Korrekturen:**
1. **Ungleiche Varianzen:** mit sigma30 := gepoolte SD sqrt((s_B^2+s_E^2)/2) ist die Formel eine **obere Schranke**:
   sigma30^2 (1+rho)/2 - Var(x) = rho (s_B - s_E)^2 / 4 >= 0. Gemessen: Freitage 44,17 (Formel) gegen 43,83 (direkt),
   Mo-Do 42,67 gegen 42,45 [aj-B:formula_check_cluster_sd] - 0,5..0,8 %, Richtung Strenge. Mit der BTC-SD statt der
   gepoolten (PRD-Kette) waere sie dagegen zu klein (ETH-SD 1,24..1,34 x BTC in den Hauptklassen).
2. **Varianzfaktor fehlt** (DEC-94 (4)): jeder Term wird mit c = max(1, c_hat) multipliziert (hier c_bind, Abschnitt 5).
3. **Klassen-SD statt einer sigma30:** Ereignis und Placebo haben eigene Slots/Tage und eigene SDs (Freitag 43,8, Mo-Do
   42,5, Wochenende 34,8, [15:30] 55,2 Cluster).
4. **Kovarianz:** gemessene Korrelation der Klassen-Aggregate derselben Woche Freitag/Mo-Do +0,014, Woche/Nicht-Freitag
   +0,004; Monat+Quartal gegen Wochen-Freitage desselben Monats +0,118 [aj-B:cross_corr_event_vs_placebo]. Positiv ->
   wuerde die SE senken; **keine Gutschrift** (Term 0, R-9, Richtung Strenge). Gepaart am selben Tag: SD der
   Tagesdifferenz direkt (Freitag r_pre gegen [15:30]: Korrelation -0,094 [aj-B:corr_pre_vs_fix1530_same_day], in der
   Differenz-SD enthalten).
5. **N_C10-Formel der Bilanz** haelt SE_placebo fest, waehrend N waechst; konsistent (beide Terme skalieren mit 1/L):
   L_C10 = (2,4865 x SE(Delta)_12M / prior)^2 Jahre je Fenster (hier per Bisektion mit `power_p1.window_power`). Die
   Bilanz-Tabelle selbst skaliert SE_placebo mit 1/sqrt(Jahre) und ist damit konsistent; nur der Formeltext nicht.

Reproduktion der Bilanz mit Akte-Eingaben (`power_p1.mde80`) [aj-P:bilanz_reproduction]: woechentlich 4,756 / 1,930 / 5,133
-> MDE80 12,76 (A3 17,08); monatlich 9,900 / 5,400 / 11,277 -> 28,04 (37,53) - identisch mit [pb:A2].

### 6.2 SE und MDE80 je Design (12-Monats-Fenster W1 2024-07-01..2025-06-30 / W2 2025-07-01..2026-06-28, N aus dem Kalender)

Nuisance-Linien: **zentral** = Klassen-SD der Periode, c_bind (bindend); **c=1** (Bericht, Richtung Testbarkeit);
**Stress** = Klassen-SD des Jahres mit groesster Streuung (2021) mit c_bind (Strenge) [aj-P:designs.<D>.contrasts.<linie>].

| Design | Ereignis N_E | bindender Placebo N_P | SE_E | SE_P | SE(Kontrast) zentral | c=1 | Stress | MDE80 P-1 zentral / Stress | MDE80 A3-Praxis zentral / Stress | [pb:A2]-Formel mit gemessenem sigma, rho, c=1 |
|---|---:|---|---:|---:|---:|---:|---:|---|---|---:|
| PRD_a | FRI 52 | P2 Nicht-Freitag 312 | 6,52 | 2,27 | 6,90 | 6,49 | 9,29 | 17,2 / 23,1 | 23,0 / 30,9 | 6,54 |
| **D_i** | FRI 52 | P2' MODO 208 (207) | 6,52 | 3,38 | **7,34** | 6,75 (6,76) | 9,87 (9,88) | **18,2 (18,3) / 24,6** | **24,4 / 32,9** | 6,80 |
| D_i (weitere Placebos) | | P3fix 364; P3all 364 | | 3,03; 0,43 | 7,18; 6,53 | | | 17,9; 16,2 | | |
| D_i_s | FRI 52 | P3'-Fri gepaart 52 | - | - | 11,15 (SD Differenz 76,7, c 1,10) | 10,63 | 15,13 | 27,7 / 37,6 | 37,1 / 50,4 | - |
| D_i_W | FRI_W 40 | P2' MODO 208 (207) | 7,32 | 3,38 | 8,06 | 7,13 | 11,33 | 20,0 (20,1) / 28,2 | 26,8 / 37,7 | 7,18 |
| D_ii | FRI_MQ 12 | P1' FRI_W 40 | 18,29 | 7,32 | 19,70 | 16,48 | 23,88 | 49,0 / 59,4 | 65,6 / 79,5 | 16,62 |
| D_iii (Bericht) | OI-Quintil 73 | OI-Quintil 73 | - | - | 6,72 | - | - | 16,7 | - | - |

Hauptwert W1, W2 in Klammern, wo die Rundung abweicht (N_P 207 statt 208). MDE80 = `power_p1.mde80(SE, 1,6449)` =
2,4865 SE (P-1) bzw. `mde80(SE, 2,4865)` = 3,3281 SE (A3-Praxis, DEC-94 (9)).

**Gegen PRD-Kette und Bilanz [abg.]:** woechentlich Bilanz 4,76 / 1,93 / 5,13 -> gemessen (D_i) 6,52 / 3,38 / 7,34 (+43 %),
(PRD_a) 6,52 / 2,27 / 6,90 (+34 %); MDE80 12,8 -> 18,2 (18,3) bzw. 17,2. Ursachen: Ereignis-SD 43,8 statt 36 x sqrt(0,9075) =
34,3 (gepoolte SD ueber BTC-Kette, x1,28), c_bind 1,149 (x1,07 auf die SE), Placebo P2' nur Mo-Do (N 208 statt 313, und
SD 42,5). Monatlich 9,90 / 5,40 / 11,28 -> 18,29 / 7,32 / 19,70 (+75 %): Monats-SD 52,4 (x1,53), c_bind 1,46, Placebo-SD
41,1 statt 36.

### 6.3 Prior-Gitter: Fenster-Power, Regime, Fensterlaenge fuer C10 (nur Zahlen, keine Zuordnung als Urteil)

Prior = Kontrast in registrierter Richtung (Vorzeichen offen, PRD 5.2); "abg." = mit OI-Abschwaechung (Kontrast-Prior =
Ereignis-Prior x Faktor; D_i/PRD_a 0,842, D_i_W 0,826, D_ii 0,687; P3-Placebos ohne Abschwaechung) [aj-P:oi_attenuation].
Bindend = Placebo mit kleinster Fenster-Power. Regime = `power_p1.assign_regime` (zwei gleiche 12-Monats-Fenster) /
`assign_regime_a3_practice`; L = Jahre je Fenster fuer Power 0,80 (P-1 / A3-Praxis). `*` = "zugelassen nur durch DEC-94
(Lockerung)" [aj-P:designs.<D>.prior_grid.<linie>.<prior>.<unattenuated|oi_attenuated_strict>].

**D_i (empfohlen), zentral**

| Ereignis-Prior (bp) | Kontrast-Prior | Fenster-Power P-1 | DEC-52-Gate (Produkt) | Regime P-1 / A3 | L P-1 / A3 (Jahre) | abg.: Kontrast / Power / Regime / L P-1 |
|---|---:|---:|---:|---|---|---|
| 5 | 5,0 | 0,17 | 0,01 | GL012 / GL012 | 13,3 / 23,9 | 4,2 / 0,14 / GL012 / 18,8 |
| 8 | 8,0 | 0,29 | 0,05 | GL012 / GL012 | 5,2 / 9,3 | 6,7 / 0,23 / GL012 / 7,4 |
| 12 | 12,0 | 0,50 | 0,25 | GL012 / GL012 | 2,32 / 4,15 | 10,1 / 0,39 / GL012 / 3,27 |
| 16,5 [sek, Monat, Aktien] | 16,5 | 0,73 | 0,62 | GL012 / GL012 | 1,22 / 2,19 | 13,9 / 0,60 / GL012 / 1,73 |
| 25 | 25,0 | 0,96 | 0,98 | C10 / C10 | 0,53 / 0,96 | 21,0 / 0,89 / C10* / 0,75 |

**D_i, Stress (2021-SD):** 16,5 bp: Power 0,51, GL012, L 2,22; 25 bp: 0,81, C10* (A3 GL012), L 0,97; abg. 25 bp: 0,69, GL012.
**D_i, c = 1 (Bericht):** 16,5 bp: 0,79, GL012 (Gate 0,73), L 1,04; 25 bp: 0,98, C10.

**Uebrige Designs, zentral (Power P-1 / Regime P-1 / L P-1 in Jahren; unabgeschwaecht | abgeschwaecht)**

| Design | 8 bp | 12 bp | 16,5 bp | 25 bp |
|---|---|---|---|---|
| PRD_a | 0,31 / GL012 / 4,6 \| 0,25 / GL012 / 6,5 | 0,54 / GL012 / 2,04 \| 0,43 / GL012 / 2,89 | 0,77 / GL012 / 1,08 \| 0,64 / GL012 / 1,53 | 0,98 / C10 / 0,47 \| 0,92 / C10* / 0,66 |
| D_i_s | 0,18 / GL012 / 12,0 | 0,28 / GL012 / 5,3 | 0,43 / GL012 / 2,82 | 0,73 / GL012 / 1,23 |
| D_i_W | 0,26 / GL012 / 6,3 \| 0,20 / GL012 / 9,2 | 0,44 / GL012 / 2,79 \| 0,34 / GL012 / 4,09 | 0,66 / GL012 / 1,48 \| 0,52 / GL012 / 2,16 | 0,93 / C10* / 0,64 \| 0,82 / C10* / 0,94 |
| D_ii | 0,11 / GL012 / 37,5 \| 0,09 / GL012 / 79,4 | 0,15 / GL012 / 16,7 \| 0,11 / GL012 / 35,3 | **0,21 / GL012 / 8,8 \| 0,14 / GL012 / 18,7** | 0,35 / GL012 / 3,8 \| 0,22 / GL012 / 8,1 |

(D_i_s: der bindende gepaarte Placebo hat keine Options-TWAP, daher keine Abschwaechung; 5-bp-Spalte in der JSON.)

**Fensterlage (REZENZ, DEC-99 (1)/(8)) [aj-P:rezenz_geometry]:** juengstes Fenster endet 2026-06-28. Zwei gleiche Fenster
ohne Ueberlappung mit der Nuisance-Periode (Ende 2024-05-31): hoechstens **1,04 Jahre je Fenster**; mit aller
1-min-Historie (ETH ab 2021-03-15): hoechstens **2,65 Jahre je Fenster** - dann liegt die Vorperiode in den Fenstern
(DEC-94 (5) (i) nicht erfuellbar, nur Null-Simulation (ii)), und die Literaturstichprobe 2021-2023 (Weiss et al. [sek])
liegt im Urteilsbereich (C.17).

### 6.4 Was die Zahlen fuer die Feasibility bedeuten (GL-012-Kandidat je Design, mit Richtung)

| Design | GL-012-Kandidat? | Begruendung (nur Zahlen) | Richtung der Lesart |
|---|---|---|---|
| D_i | **ja, solange V-5b offen** (PRD-Vorbedingung); rechnerisch C10 auf 12-Monats-Fenstern gegen den bindenden Einzel-Placebo ab Kontrast ~18,2 (18,3) bp (zentral) bzw. ~24,6 bp (Stress), d. h. Ereignis-Effekt ~21,7 / ~29,2 bp bei OI-Abschwaechung; gegen den ganzen Placebosatz (Fassung 2, 6.5) gemeinsam ~19,8, Produkt ~21,9 bp (abg. 22,1 / 23,8) | 16,5 bp (einziger belegter Prior, Monat/Aktien) gibt 0,73 / GL012; Fenster > 1,04 Jahre kollidieren mit der Vorperiode | zentral = c_bind (Strenge gegen c = 1: MDE 16,8) |
| PRD_a | ja (wie D_i) | MDE80 17,2; Wochenend-Kontamination | Testbarkeit gegen D_i |
| D_i_s | ja | MDE80 27,7; selbst 25 bp GL012 | Strenge |
| D_i_W | ja | MDE80 20,0 (20,1); 25 bp nur C10*; Produkt-Linie abg. bei 25 bp GL012 (6.5) | Strenge gegen D_i |
| D_ii | **ja, auch gegen den belegten Prior** | 16,5 bp [sek]: Power 0,21 (abg. 0,14), 8,8 (18,7) Jahre je Fenster; jeder Gitterpunkt GL012 | Strenge gegen jede Freitags-Variante (N 12, Placebo P1' traegt selbst Wochenverfaelle, Abschwaechung 0,687); in jeder Linie GL012 (Fassung 2, A-6) |
| D_iii | nicht registrierbar (ex post) | MDE80 16,7 (Bericht) | - |

### 6.5 Konjunktion: Power gegen alle Placebos des Satzes (Fassung 2, A-1)

**Festlegung des Orchestrators (uebernommen, als Festlegung gekennzeichnet):** Die Zuordnung (C10 / DEC52 / GL012) traegt
analog DEC-94 (6) das **Produkt der Einzel-Powers** (Untergrenze der gemeinsamen Power bei positiv korrelierten
Kontrasten); die gemeinsame Power (Monte Carlo) ist Bericht. Richtung Strenge. Je Placebo j: Einzel-Power und DEC-52-
Gate-Power aus `power_p1.assign_regime`; C10, wenn das Produkt der Fenster-Powers in W1 und W2 >= 0,80; sonst DEC52,
wenn das Produkt der Gate-Powers >= 0,80; sonst GL012; A3-Praxis analog mit Faktor 2,4865 (ohne DEC-52).
Kovarianz nach R-15 [S:a2v_konj.py, S:a2v_corr2.py]. Gemessene Same-Day-Korrelationen der Placebo-Cluster-Reihen
[aj-K:same_day_corr_cluster_inputs]: r_pre gegen [15:30] auf Mo-Do 0,033, Woche-Freitag -0,159, Nicht-Freitag 0,022;
r_pre gegen P3-Baseline auf Mo-Do 0,018, Woche-Freitag -0,138, Nicht-Freitag -0,004; [15:30] gegen P3-Baseline alle
Tage 0,166, Freitag 0,207. Daraus Korrelationen der Kontraste (W1) D_i: P2'/P3fix 0,81, P2'/P3all 0,89, P3fix/P3all
0,91 [aj-K:designs.<D>.windows.W1.test_corr_matrix].

**MDE80 auf der Ereignis-Skala (bp; W1 (W2)); Einzel (bindend) / gemeinsam (Bericht) / Produkt (Zuordnung)**
[aj-K:designs.<D>.lines.<linie>.mde80]

| Design / Placebosatz | P-1 unabgeschwaecht | P-1 OI-abgeschwaecht | A3-Praxis unabgeschwaecht | A3-Praxis abgeschwaecht |
|---|---|---|---|---|
| D_i {P2'} | 18,2 (18,3) / 18,3 / 18,2 (18,3) | 21,7 / 21,7 / 21,7 | 24,4 / 24,4 (24,5) / 24,4 | 29,0 / 29,0 / 29,0 |
| D_i {P2', P3fix} | 18,2 (18,3) / 19,7 / 21,0 | 21,7 / 22,1 / 23,3 | 24,4 / 25,8 / 27,1 (27,2) | 29,0 / 29,3 / 30,2 |
| **D_i {P2', P3fix, P3all}** | **18,2 (18,3) / 19,8 / 21,9** | **21,7 / 22,1 / 23,8** | 24,4 / 25,8 / 27,9 | 29,0 / 29,2 / 30,5 |
| D_i_W {P2', P3fix, P3all} | 20,0 (20,1) / 21,6 / 24,2 | 24,3 / 24,6 / 26,5 | 26,8 / 28,3 / 30,8 | 32,5 / 32,6 / 34,0 (34,1) |
| PRD_a {P2, P3fix, P3all} (PRD: "P2 und P3") | 17,9 / 19,0 / 21,4 | 20,4 / 20,9 / 23,0 | 23,9 / 24,9 / 27,2 | 27,3 / 27,6 / 29,4 |
| D_i_s {P2', P3fix, P3all, P3'-Fri} | 27,7 / 27,9 / 28,6 | 27,7 / 28,6 / 29,5 | 37,1 / 37,1 / 37,4 | 37,1 / 37,6 / 38,2 |
| D_ii {P1', P2', P3fix, P3all} | 49,0 / 51,4 / 61,1 | 71,3 / 71,4 / 74,2 | 65,6 / 67,6 / 77,0 | 95,4 / 95,5 / 96,5 |

Bei {P2'} ist "gemeinsam" = Einzel bis auf den Monte-Carlo-Fehler (18,3 statt 18,2). In PRD_a bindet mit P3 der
Placebo P3fix (SE 7,18 > 6,90), daher Einzel 17,9 statt 17,2 (Fassung 1 nur {P2}).

**Power (W1) und Zuordnung auf dem Gitter: Einzel / gemeinsam / Produkt, Regime P-1 / A3 nach Produkt** (`*` = "zugelassen
nur durch DEC-94") [aj-K:designs.<D>.lines.<linie>.prior_grid]

| Design / Linie | 12 bp | 16,5 bp | 18,25 bp | 25 bp |
|---|---|---|---|---|
| D_i {P2'} | 0,50 / 0,50 / 0,50 GL012 | 0,73 / 0,73 / 0,73 GL012 | 0,80 / 0,80 / 0,80 GL012 | 0,96 / 0,96 / 0,96 C10 / C10 |
| D_i {P2', P3fix} | 0,50 / 0,40 / 0,25 GL012 | 0,73 / 0,65 / 0,54 GL012 | 0,80 / 0,74 / 0,65 GL012 | 0,96 / 0,94 / 0,93 C10 / GL012* |
| **D_i {P2', P3fix, P3all}** | 0,50 / 0,39 / 0,15 GL012 | **0,73 / 0,65 / 0,44 GL012** | 0,80 / 0,74 / 0,57 GL012 | 0,96 / 0,94 / 0,92 C10 / GL012* |
| D_i {P2', P3fix, P3all}, abg. | 0,39 / 0,34 / 0,12 GL012 | 0,60 / 0,56 / 0,36 GL012 | 0,67 / 0,65 / 0,48 GL012 | 0,89 / 0,88 / 0,85 C10 / GL012* |
| D_i_W, unabg. / abg. | 0,44 / 0,34 / 0,10 GL012 | 0,66 / 0,57 / 0,32 GL012 | 0,73 / 0,66 / 0,44 GL012 | 0,93 / 0,90 / 0,83 C10 / GL012* \| abg. 0,82 / 0,81 / 0,74 GL012 |
| PRD_a {P2, P3fix, P3all} | 0,51 / 0,43 / 0,16 GL012 | 0,74 / 0,68 / 0,47 GL012 | 0,82 / 0,77 / 0,60 GL012 | 0,97 / 0,96 / 0,93 C10 / GL012* |
| D_i_s | 0,29 / 0,20 / 0,04 GL012 | 0,44 / 0,37 / 0,19 GL012 | 0,50 / 0,45 / 0,28 GL012 | 0,73 / 0,71 / 0,66 GL012 |
| D_ii | 0,15 / 0,11 / 0,00 GL012 | 0,21 / 0,16 / 0,00 GL012 | 0,24 / 0,18 / 0,00 GL012 | 0,35 / 0,29 / 0,02 GL012 |

Lesart (nur Zahlen): der Unterschied zwischen Einzel-, gemeinsamer und Produkt-Power ist bei D_i gross, weil drei
Kontraste aehnlicher SE einen Ereignis-Term teilen (Korrelation 0,81..0,91); jeder zusaetzliche Placebo kostet Power
(Produkt-MDE80 18,2 -> 21,0 -> 21,9 bp fuer 1 / 2 / 3 Placebos). Unter der Produkt-Festlegung ist 25 bp bei D_i nur
unter P-1 zugelassen (A3-Praxis GL012), 18,25 bp in keiner Variante.

### 6.6 Differenz-in-Differenzen (Fassung 2, A-5; Gabelung, eigene Rechnung)

DiD = [Freitag (r_pre - r[15:30])] - [Mo-Do (r_pre - r[15:30])]: kontrolliert Wochentags- und Tageszeit-Haupteffekt
zugleich, laesst nur die Interaktion Freitag x 07:30. Gepaarte Differenz-Reihen (Cluster) aus Fassung 1: SD Freitag
76,67 (c_bind 1,099), Mo-Do 73,28 (c_bind 1,360) [aj-D:sd_paired_diff_fri, aj-D:sd_paired_diff_modo]; Korrelation der
Wochen-Aggregate +0,101 (positiv -> keine Gutschrift, Term 0) [aj-D:week_corr_inputs]. Je Fenster: SE Freitags-Teil
11,15, Mo-Do-Teil 5,93 (5,94); **SE(DiD) 12,62 (12,63), MDE80 31,4 bp (P-1) / 42,0 bp (A3-Praxis)**; auf der
Ereignis-Skala mit OI-Abschwaechung 37,3 bp [aj-D:windows, aj-D:mde80_event_scale_attenuated_p1]. Fenster-Power P-1 bei
16,5 / 25 bp: 0,37 / 0,63, GL012 auf jedem Gitterpunkt [aj-D:prior_grid]. Richtung: Strenge (Identifikation) gegen
D_i und D_i_s; die 15:30-Kontamination an Monatsend-Freitagen (CME-Fenster, UNBELEGT) betrifft auch die DiD.

### 6.7 P2'' = Mo-Do ohne Futures-Verfallstage (Fassung 2, A-3; Gabelung)

Futures-Kalender (Teil A 3a) [aj-F:by_window]: in W2 tragen 48 von 207 Mo-Do-Tagen eine Futures-Delivery (36 in beiden
Waehrungen), in W1 und der Vorperiode keiner. P2'' schliesst Mo-Do-Tage mit Futures-Delivery in mindestens einer
Waehrung aus: N_P W1 208, W2 159. Die Vorperioden-Nuisance von P2'' ist die von P2' (dort kein Futures-Tag). SE(Kontrast)
W1 7,34, **W2 7,58**; MDE80 Einzel 18,2 (**18,8**) bp, A3 24,4 (25,2); gegen {P2'', P3fix, P3all}: gemeinsam 19,8 (20,2),
Produkt 21,9 (22,2) bp [aj-K:designs.D_i_futfrei__S1_P2ss, aj-K:designs.D_i_futfrei__S3_P2ss_P3fix_P3all]. Richtung:
Reinheit und W1/W2-Homogenitaet des Placebos gegen +3 % SE in W2 (Strenge in der SE).

## 7. B-5: Etiketten (Pflicht fuer jede Weiterverwendung)

- **"V-5b UNBELEGT":** keine bezifferte Effektgroesse fuer Freitags-/Wochenverfaelle (RECHERCHE_BELEGE 3.3: Weiss et al.
  FRL 2026 nur Richtung [sek], Deribit 2021-2023); das Prior-Gitter ist kein Prior.
- **"Vorperiode = anderes Vol-Regime":** SD-Spanne 2021..2023 Faktor 2,3; W1/W2-Streuung hier nicht gemessen (Auftrag:
  nur <= 2024-05-31); die Stress-Linie (2021) ist die Strenge-Grenze, nicht eine Prognose.
- **"Bybit-Funding 08:00 in Ereignis und Placebo":** gleicher Funding-Termin in allen [07:30, 08:00)-Slots; hebt sich im
  Kontrast nur bei wochentagsunabhaengiger Wirkung auf; Funding-Intervall BTCUSDT/ETHUSDT nach 2025-10-30 UNBELEGT
  (Auto-Switch DEC-84, nicht geprueft).
- **"Datenlage":** Extrakte 2021-03-24..2024-05-31 lueckenlos; BTC 2020-03-25..2021-03-23 nicht geladen; Normal-Naeherung
  bei Exzess-Kurtosis 5..10 und N 12 (Monat) fraglich.
- **"Groessen-Kontrast":** jeder kalenderfixierbare Kontrast seit 2020-03-25 misst gross gegen klein, nie Verfall gegen
  keinen (Teil A).

## 8. Kontamination und C.17 (Register)

Gesehen (nicht ergebnisnah, vom Auftrag erlaubt): Streuungen, Korrelationen, Autokorrelationen und Varianzfaktoren von
r_pre/r_post und Nachbar-Slots 2021-03-24..2024-05-31 nach Wochentagsklassen; gelieferte Kontraktsummen je Verfallstag
bis 2026-06-30 (W1/W2 eingeschlossen); Fassung 2: Futures-Liefertermine bis 2026-06-30 (nur Namen/Datum).
**Intern berechnet, nie ausgegeben, gespeichert oder angezeigt** (Fassung 2, A-6; Fassung 1 sagte hier faelschlich
"nicht berechnet"): Mittel je Klasse/Jahr/Serie als Zentrierung in `describe()` (SD, Kurtosis) und `acf()`, in
`np.corrcoef`/`np.std`; der Median als MAD-Zentrum in `describe()`; Klassen-Mittel je ISO-Woche/Monat als Aggregate fuer
eine Korrelation (`agg_corr()` in a2v_sigma30.py, Fassung 2 auch die DiD-Wochenkorrelation in a2v_corr2.py); Batch-Mittel
(`batch_means_c()`); Replikat-Mittel des stationaeren Bootstraps (`power_p1.stationary_bootstrap_se`); Wochensummen des
Block-Bootstraps (`WeekBoot`); die P3-Tagesstatistik (1/44 x Summe). Ausgegeben wurde davon nur Streuung,
Korrelation, Varianzfaktor; `print` nur sha256. **Kein Mittel, kein Median und kein Vorzeichen** irgendeiner
Slot-Rendite oder Differenz wurde ausgegeben, gespeichert oder angezeigt.
**C.17-Zeile (A-6):** unzentrierte Betrags-Quantile und 1,4826 x MAD je Klasse/Jahr/Serie wurden gesehen, in Fassung 1
auch fuer die gepaarte Differenz-Reihe (in Fassung 2 entfernt, Abschnitt 3); unter Symmetrie liesse sich daraus ein
verrauschter Lagebetrag ableiten - nicht getan. **W1/W2-Inventur (A-6, Fakten des Orchestrators):** die 2.0-Hypothesen
H-01..H-18 sahen Bybit/Deribit-Daten 2026-03-27..2026-07-04 (Mikrostruktur, Sekunden- bis Minutenhorizont), darunter
die 08:00-Slots 2026-03-27..2026-06-28 in W2; kein r_pre-Mittel ueber 07:30-08:00 wurde dort gebildet; Weiss et al.
(2021-2023) liegt vor W1. Die Nuisance-Periode ueberlappt die Stichprobe von Weiss et al.
(2021-2023, Richtung von r_pre [sek] bekannt) - fuer jede spaetere Registrierung, die 2021-2023 als Urteilsfenster nutzen
wollte, ist das ein C.17-Etikett; als reine Nuisance-Quelle (DEC-94 (5) (i)) ist es zulaessig. Die signierten ACF-Werte
und die Korrelation r_pre gegen [15:30] (-0,094 an Freitagen) sind Abhaengigkeitsmasse, keine Lage.

## 9. Reproduktion

`scratchpad/a2_vorarbeit/run_all.sh`; Skripte `a2v_common.py` (Regeln, Waechter, Lader), `a2v_oi.py`, `a2v_sigma30.py`,
`a2v_power.py`, `a2v_build.py`; sha256 der Skripte, der wiederverwendeten Module (`hfrv_common.py`, `h27_common.py`,
`power_p1.py`) und der Eingaben in `[aj:skripte_sha256]`, `[aj:wiederverwendet_sha256]`, `[aj:inputs_sha256]`.
Bootstrap-Seeds 27 (R-6, R-8, iid-Referenz). Fassung 1: `a2_vorarbeit.json` sha256 `2bd1ad7e...d30a`, `work/a2v_oi.json`
`f3559cc8...7006`, `work/a2v_sigma30.json` `7e98d022...49b5`, `work/a2v_power.json` `552bf0d1...7394`.
**Fassung 2** (zusaetzlich `a2v_fut.py`, `a2v_corr2.py`, `a2v_konj.py`; MC-Seed 94; zwei vollstaendige Laeufe bitgleich):
`a2_vorarbeit.json` `9a2f5ac91a1ce7f8c71953afd2ef83a6b5ceeda150ff9c28a681905c9de26052`; `work/a2v_oi.json` und `work/a2v_power.json`
unveraendert bitgleich zu Fassung 1; `work/a2v_sigma30.json` `37700ae3...74bb3` (nur die 528 Betrags-Quantile der
Differenz-Reihe entfernt, sonst identisch); neu `work/a2v_fut.json` `6590ba5a...e1bf9`, `work/a2v_corr2.json`
`048022fb...77d73`, `work/a2v_konj.json` `02f23c9d...e1e12`.

## 10. Aenderungen gegen Fassung 1

1. **A-1:** Abschnitt 6.5 - Konjunktions-Power als Doppelausweis je Design (Einzel / gemeinsam / Produkt) und fuer D_i
   je Placebosatz; D_i {P2', P3fix, P3all}: MDE80 18,2 (18,3) / 19,8 / 21,9 bp, abgeschwaecht 21,7 / 22,1 / 23,8; bei
   16,5 bp Power 0,73 / 0,65 / 0,44. Festlegung: Zuordnung nach Produkt, gemeinsame Power Bericht.
2. **A-2:** Null fuer den Groessen-Kontrast neu definiert (Teil A 4a, ENTSCHEIDUNGSVORLAGEN EV-J), nicht gebaut.
3. **A-3:** Futures-Kalender (Teil A 3a); Gabelung P2'' (6.7): W2 N_P 159, SE 7,58, MDE80 18,8 bp.
4. **A-4:** CME-Referenzfenster als UNBELEGTE Kontamination (Teil A 2); betrifft P3fix, D_i_s und DiD an Monatsend-Freitagen.
5. **A-5:** DiD (6.6): SE 12,62 (12,63), MDE80 31,4 / 42,0 bp; historische Baseline und Beta-Residualisierung in
   ENTSCHEIDUNGSVORLAGEN EV-M.
6. **A-6:** Abschnitt 8 korrigiert ("intern berechnet, nie ausgegeben" mit Stellen); Waechter um Lage-Schluessel
   erweitert, `start_ms`-Assert vor den Preisspalten; Betrags-Quantile der Differenz-Reihe aus dem JSON entfernt;
   C.17-Zeile und W1/W2-Inventur; Rundung vereinheitlicht; Beschriftung "[15:30] alle Tage / [07:30] Mo-Do"; Richtung
   D_ii. Neue sha256 `a2_vorarbeit.json`: `9a2f5ac91a1ce7f8c71953afd2ef83a6b5ceeda150ff9c28a681905c9de26052`.
