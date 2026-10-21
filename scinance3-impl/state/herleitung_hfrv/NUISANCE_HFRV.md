# HF-RV-Nuisance (Option 3, DEC-98) - Vorperiode 2021-03-24..2024-05-31 - NUR NUISANCE, KEIN MITTEL

> ENTWURF der Herleitung (Herleitungs-Agent Nuisance/Power/Rauschboden), Stand 2026-10-21. Nichts hier ist
> registriert oder beschlossen; entscheiden und registrieren darf nur der Orchestrator.
> **Etikett:** "HF-RV-Nuisance 2021-03-24..2024-05-31 (IV-Tage bis 2024-05-01, 1-min-Kerzen bis 2024-05-31): nur
> Streuungs-, Autokorrelations-, Verhaeltnis- und RV-Niveaugroessen; der Mittelwert der Praemie (jede Einheit), ihr
> Vorzeichen und das DVOL-Mittel werden weder ausgegeben noch gespeichert." (`LABEL` in `nuisance_hfrv.json`, dazu das
> unveraenderte H-27-Etikett.)
> **Ergebnisblindheit:** keine Preise/Renditen nach 2024-05-31 (Assert beim Laden der Kline-Extrakte, `assert_rv_day`
> auf jedem RV-Tag), IV nur fuer t <= 2024-05-01 (`assert_dvol_level_day`), kein Praemienmittel, kein DVOL-Mittel, keine
> Vorzeichen-/Niveauaussage der Praemie (Waechter `h27_common.no_mean` plus Zusatzwaechter `hfrv_common.guard_keys` auf
> jedem Ausgabe-Dict). Kein Harvest-Client, nichts nachgeladen, nichts gelistet; keine Siegeldatei, keine
> WP-10(A2)-/WP-10(A)-IV-RV-Datei, nichts unter `data/harvest` geoeffnet. Das lokale Union-Panel wurde nur fuer die
> Jahre 2021..2024 gelesen und beim Lesen bei 2024-05-31 abgeschnitten (nur Gleichheitspruefung der Tagesschluesse).
> **Kuerzel:** `[nj:<pfad>]` = `nuisance_hfrv.json` (gleicher Ordner); `[fj:<pfad>]` = `herleitung_h27/feasibility.json`;
> `[S:<datei>]` = Skript unter `scratchpad/hfrv_herleitung/` (sha256 in `[nj:skripte_sha256]`); `[abg.]` hier
> abgeleitet; UNBELEGT = keine Fundstelle, blockiert; VP = Vol-Punkte.

## 0. Befund in Kuerze

1. **Option 3 traegt nicht: die Hochfrequenz-RV senkt die Streuung der Praemie nicht.** BTC S1 (Vol-Punkte), SD je
   RV-Variante gegen 18,60 (H-27, close-to-close): 1-min 18,58; 5-min 19,47; **5-min subsample-gemittelt 18,62**;
   15-min 19,27; 30-min 17,69; close-to-close aus dem letzten 1-min-close 18,60 (reproduziert H-27 auf 1e-5)
   [nj:stats.BTC.<v>.S1.sd]. Die UNBELEGT-Annahme SD ~15,1 (REVIEW_H27 B-1) ist **nicht bestaetigt (unguenstiger)**
   (vorab fixierte Regel R-9) [nj:recommendation_R10].
2. **Der Varianzfaktor steigt:** c nach Regel P-3 30,7..31,6 (HF) gegen 28,17 (cc); Konsens-c (getaperte ACF-Summe wie
   Review) 23,1..26,5 (HF) gegen 18,6 (cc). Grund: die negative ACF der cc-Praemie um Lag 30 (-0,155) verschwindet
   weitgehend (HF -0,04..-0,05) [nj:stats.BTC.<v>.S1.acf_out, .c_bind, .c_consensus_tapered_acf].
3. **Fensterlaenge (C10 unter P-1, BTC S1, pi-2 zentral 9,47, SE_null H-27, empfohlene Variante (iii)):** 751,7 Tage
   je Fenster mit c nach Regel (voll 2030-09-11; cc: 671,8 / 2030-04-04), 582,1 Tage mit gemessenem Konsens-c (voll
   2029-10-08; cc: 443,0 / 2029-01-03). A3-Praxis: 1.346,7 Tage (2033-12-14). Die Bilanz-Zeilen "HF-RV 442,9 / 292,4
   Tage" (SD 15,1 angenommen) sind **widerlegt**. Bei L = 12 (n 335 bindend / 365 Bericht) bleibt jede HF-Variante mit
   zentralem Prior GL012 (Power 0,51 / 0,53 mit Regel-c) [nj:power.BTC_S1.<v>].
4. **Warum kein Gewinn (gemessen, nur Streuungen/Korrelationen):** P_cc = P_HF + D mit D = RV_HF - RV_cc. D streut mit
   8,1 VP (Variante iii; 19 % der Praemienvarianz - das ist das tatsaechliche Messrauschen von RV_cc gegen HF, kleiner
   als die 10,9 VP der Delta-Methode), ist aber nicht unabhaengig: Corr(D, P_HF) = -0,22, Corr(D, RV_HF) = +0,41; der
   Kovarianzterm 2 Cov(P_HF, D) = -67,0 hebt die Varianz von D (66,3) auf [nj:decomposition_P_cc_eq_P_v_plus_D.BTC.v3_5min_sub]. Das
   kappa-Rauschmass der HF-Tages-RV liegt bei ~2,05 statt nahe 1 - die Delta-Methode des Reviews misst also
   Tag-zu-Tag-Schwankung der wahren Varianz mit, nicht nur Rauschen.
5. **Niveau-Verzerrung:** rms RV_fwd30 BTC 64,95 % (iii) gegen 61,55 % (cc), Verhaeltnis 1,055 (1-min 1,061; 5-min
   1,072; 15-min 1,029; 30-min 1,009); Lag-1-ACF der 5-min-Renditen -0,047 (Intraday-Umkehr) [nj:rv_level,
   nj:data_rv_day]. Eine HF-Statistik braucht ein eigenes J (UNBELEGT) und eine Prior-Lesart fuer die RV-Definition
   der Literatur (Gabelung, Abschnitt 6).
6. **Empfohlene Variante nach der vorab fixierten Regel R-10 (nicht nach SD gewaehlt, Richtung neutral):** (iii) 5-min
   subsample-gemittelt (Signatur gegen 30-min 1,046 BTC / 1,041 ETH, knapp im Band 0,95..1,05; (ii) faellt mit 1,063
   / 1,067 heraus). Die Empfehlung aendert Befund 1 nicht: keine Variante bringt in S1 einen Gewinn; die einzige
   Variante mit kleinerer S1-SD (30-min, 17,69) waere eine Auswahl nach Kenntnis der SD (Richtung Testbarkeit) und
   bleibt mit 661,7 / 514,7 Tagen auf cc-Niveau.
7. **Daten:** 1-min-Kerzen BTCUSDT/ETHUSDT 2021-03-24..2024-05-31 lueckenlos (je 1.165 Tage x 1.440 Zeilen, keine
   Duplikate, keine Zeitstempel ausserhalb voller Minuten), DVOL je 1.165 Tage x 24 Stundenkerzen, 1.135 IV-Tage je
   Symbol; ALLDONE ohne `failed_months` in beiden Logs. Keine Praemie fehlt (n = 1.135 je Serie).

---

## 1. Daten und Pruefungen [nj:data_kline, nj:data_dvol, nj:data_rv_day, nj:check_last_1min_close_vs_panel_1d]

| Stueck | Befund |
|---|---|
| Download-Logs | `ALLDONE hf {"kline1m_BTC": [], "kline1m_ETH": [], "dvol": []}`; `ALLDONE deribit {"settlements": [], "deliveryPrices": []}` - keine fehlenden Monate |
| Kline BTCUSDT / ETHUSDT | je 1.677.600 Zeilen, 2021-03-24..2024-05-31 (Assert: kein Tag > 2024-05-31), Symbol eindeutig, `category` linear, `interval` 1; 1.165 Tage, alle mit genau 1.440 Minuten; 0 exakte, 0 widerspruechliche Duplikate; 0 Zeitstempel neben voller Minute; 0 nicht-positive Schlusskurse |
| RV-Tage | 1.164 je Symbol (2021-03-25..2024-05-31; der erste Tag dient als Anker), keine fehlenden |
| Anker-Konvention | open der 00:00-Kerze = close der 23:59-Kerze des Vortags an 1.163/1.164 (BTC) bzw. 1.164/1.164 (ETH) Tagesnaehten |
| DVOL | 55.920 Zeilen, ein Payload-Schema (close, high, low, open, timestamp), `ts_exchange_ms` = Payload-`timestamp` in allen Zeilen, alle auf voller Stunde, 24 Kerzen je Tag; IV(t) = close der 23:00-UTC-Kerze (H-27-Konvention), 1.135 IV-Tage je Symbol, keiner fehlt |
| Zusatzkontrolle Panel (R-13) | letzter 1-min-close = Panel-Tagesschluss an 1.164/1.165 Tagen (BTC; Ausnahme 2021-03-24, relative Abweichung 2,1e-4) und 1.165/1.165 (ETH). Folge: Variante (vi) reproduziert H-27 (BTC S1 SD 18,5974 gegen 18,5974 [fj:nuisance.BTC.S1.sd], c 28,172 gegen 28,172; ETH identisch) |

## 2. Vorab fixierte Regeln (R-1..R-13, vor jeder Zahl im Docstring von `hfrv_common.py`)

- **R-1 Stichprobe** wie H-27 P-1; Kline-Extrakte per Assert ohne Tag nach 2024-05-31.
- **R-2 Tagesvollstaendigkeit:** nur 1.440 eindeutige Minuten = vollstaendig (keine Schwelle 1.380); exakte Duplikate
  entfernt und gezaehlt, widerspruechliche machen den Tag unvollstaendig. Angewandt: kein Fall.
- **R-3 Rendite-Gitter:** Preis am Gitterpunkt = close der dort endenden 1-min-Kerze; Tagesanker = close 23:59 des
  Vortags. Damit teleskopieren die Intraday-Renditen jeder Variante exakt auf die close-to-close-Tagesrendite (vi);
  alle Varianten messen dasselbe 24-h-Intervall.
- **R-4 Varianten:** (i) 1-min (1.440 Renditen), (ii) 5-min-Gitter (288), (iii) Mittel ueber 5 Phasen des 5-min-Gitters
  mit Randstuecken (jede Phase deckt den ganzen Tag), (iv) 15-min (96), (v) 30-min (48), (vi) r_s^2.
- **R-5** RV_fwd30 = sqrt((365/30) * Summe der 30 Tages-RV nach t); P in S1/S2/S3 wie `h27_series.premium_frame`.
- **R-6** IV wie H-27 (Payload-Zeitstempel 23:00 UTC, close/100).
- **R-7** Statistiken mit `nuisance.describe` (H-27-Code, unveraendert kopiert, sha256 gleich); kappa wie
  `noise_share.py` des Reviews (L 2, 3, 5; zusaetzlich L 2..5); Konsens-c = getaperte ACF-Summe wie
  `mc_rule_bias.c_true_longrun` des Reviews.
- **R-8** SE_W = max(SD * sqrt(c/n), SE_null); SE_null = H-27-Wert bei n 365, skaliert mit sqrt(365/n) (cc-Welt; die
  HF-SE_null waere kleiner, UNBELEGT, nicht neu kalibriert). Tage je Fenster mit dem Bilanz-Loeser (kopiert,
  quelltextgleich geprueft) ueber `power_p1`.
- **R-9** Vergleich mit 15,1: "bestaetigt" nur fuer SD in [14,1; 16,1].
- **R-10** Empfehlung: Reihenfolge (iii) > (ii) > (iv) > (v), erste Variante mit Signatur rms(RV_v)/rms(RV_30min) in
  [0,95; 1,05] fuer BTC und ETH; (i) und (vi) nur Bericht; SD und kappa nur Bericht.
- **R-11..R-13** Bein BTC bindend; Waechter auf jedem Ausgabe-Dict; Panel-Zusatzkontrolle nur Zaehlungen.

**Abweichungen:** keine von R-1..R-13. Zusatz ueber den Auftrag hinaus (Bericht): Zerlegung P_cc = P_HF + D
(Abschnitt 4), Gegenlesart des Priors bei Niveau-Verzerrung (Abschnitt 6), DEC-98-Nachtrag-2-Priors 7,14 / 3,16 VP.

## 3. Statistiken der Praemie (Vorperiode, n = 1.135 je Serie, keine Luecke; Bootstrap 2.000 Replikate, Seed 27)

**BTC S1 (Vol-Punkte; bindendes Bein)** [nj:stats.BTC.<v>.S1]

| Variante | SD | ACF 1 / 10 / 20 / 30 / 60 / 120 / 180 | erster Lag < 0,10 | Kurt. (exz.) | c Bartlett 60/90/120 | c BM 60/90/120 | c stat. Bootstrap 30/60/90 | **c Regel P-3** | Konsens-c | Monat SD / ACF1 / c_m |
|---|---:|---|---:|---:|---|---|---|---:|---:|---|
| (i) 1-min | 18,58 | 0,966 / 0,558 / 0,154 / -0,042 / 0,033 / -0,000 / -0,059 | 22 | 2,45 | 20,4 / 21,6 / 21,2 | 25,6 / 31,6 / 23,4 | 17,8 / 20,2 / 20,0 | **31,61** | 24,5 | 18,72 / -0,05 / 1,0 |
| (ii) 5-min | 19,47 | 0,966 / 0,568 / 0,163 / -0,053 / 0,017 / 0,025 / -0,085 | 22 | 3,32 | 20,3 / 21,2 / 20,6 | 25,9 / 31,0 / 22,9 | 17,6 / 19,1 / 18,9 | **30,96** | 23,1 | 19,63 / -0,06 / 1,0 |
| **(iii) 5-min sub** | **18,62** | 0,967 / 0,562 / 0,161 / -0,039 / 0,029 / -0,005 / -0,084 | 22 | 2,58 | 20,5 / 21,7 / 21,2 | 25,7 / 31,5 / 24,2 | 17,8 / 19,5 / 19,2 | **31,46** | 24,4 | 18,76 / -0,05 / 1,0 |
| (iv) 15-min | 19,27 | 0,966 / 0,564 / 0,161 / -0,049 / 0,073 / 0,009 / -0,062 | 22 | 2,61 | 20,7 / 22,5 / 22,4 | 25,8 / 31,3 / 25,8 | 18,2 / 21,0 / 20,9 | **31,31** | 26,5 | 19,43 / -0,06 / 1,0 |
| (v) 30-min | 17,69 | 0,964 / 0,545 / 0,143 / -0,042 / 0,028 / 0,024 / -0,072 | 22 | 1,82 | 20,1 / 21,2 / 20,7 | 24,0 / 30,7 / 21,2 | 17,8 / 20,0 / 19,4 | **30,65** | 23,8 | 17,83 / -0,05 / 1,0 |
| (vi) cc (= H-27) | 18,60 | 0,955 / 0,514 / 0,107 / -0,155 / 0,054 / 0,012 / -0,073 | 21 | -0,03 | 16,9 / 17,4 / 17,8 | 19,2 / 28,2 / 15,2 | 15,9 / 17,7 / 17,5 | **28,17** | 18,6 | 18,70 / -0,16 / 1,0 |

- **180-Regel (P-3):** ACF(120) liegt in allen Varianten unter 0,10 -> nicht ausgeloest [nj:stats.*.*.*.c_rule].
- Bindend ist in allen HF-Varianten wieder Batch-Means L 90 (12 Bloecke, Richtung Strenge, wie H-27 A-2); Bartlett
  20,1..22,5, Bootstrap 17,6..21,0, Konsens 23,1..26,5 - alle ueber den cc-Werten.
- Monatsvariante (nicht ueberlappend): c_m = 1 ueberall (keine Gutschrift); SD_m 17,8..19,6 - kein Gewinn gegen cc
  18,70.
- Die HF-Praemie ist breitschwaenziger (Exzess-Kurtosis 1,8..3,3 gegen -0,03); fuer die Normal-Naeherung der
  Power-Zeile ein Merkposten (Bericht).

**BTC S3 (Log) und S2 (Varianz x 100), Kurzfassung** [nj:stats.BTC.<v>.S3 / .S2]

| Variante | S3 SD | S3 c Regel / Konsens | S2 SD | S2 c Regel / Konsens |
|---|---:|---|---:|---|
| (i) 1-min | 0,271 | 28,97 / 24,3 | 31,55 | 29,70 / 22,5 |
| (ii) 5-min | 0,286 | 26,58 / 22,1 | 34,09 | 29,71 / 21,4 |
| (iii) 5-min sub | 0,276 | 28,02 / 23,7 | 31,50 | 30,15 / 22,9 |
| (iv) 15-min | 0,293 | 26,30 / 23,9 | 32,32 | 29,76 / 24,4 |
| (v) 30-min | 0,270 | 27,60 / 21,4 | 28,69 | 29,58 / 24,2 |
| (vi) cc | 0,304 | 25,94 / 14,9 | 27,26 | 29,44 / 23,6 |

In S3 senkt die HF-RV die SD um 5..11 %, der Varianzfaktor steigt aber ebenfalls (Konsens 14,9 -> 21..24); in S2 steigt
die SD (+5..+25 %). ETH: SD S1 24,35..29,42 gegen 25,10 (cc), c Regel 34,1..35,5 gegen 27,64; Tagesmittel BTC/ETH S1
20,56..24,05 gegen 20,93, c 32,8..34,3 gegen 27,91 (Volltabellen Anhang A).

## 4. RV-Niveau, Signatur, kappa und Zerlegung [nj:rv_level, nj:kappa_rv_day, nj:sd_ratios, nj:decomposition_P_cc_eq_P_v_plus_D]

| Symbol | Variante | rms RV_fwd30 % | / cc | / 30-min | Niveau-Abw. VP | kappa L2,3,5 | Rausch-SD VP (Delta) | SD S1 | SD / SD_cc | SD "rauschfrei" (Delta) | SD(D) VP | Corr(D, P_v) | Corr(D, RV_v) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC | (i) 1-min | 65,32 | 1,061 | 1,052 | 3,77 | 2,06 | 6,13 | 18,58 | 0,999 | 17,54 | 7,95 | -0,21 | 0,36 |
| BTC | (ii) 5-min | 65,98 | 1,072 | 1,063 | 4,43 | 2,51 | 7,41 | 19,47 | 1,047 | 18,01 | 9,16 | -0,33 | 0,46 |
| BTC | (iii) 5-min sub | 64,95 | 1,055 | 1,046 | 3,40 | 2,05 | 6,06 | 18,62 | 1,001 | 17,60 | 8,14 | -0,22 | 0,41 |
| BTC | (iv) 15-min | 63,35 | 1,029 | 1,021 | 1,80 | 2,54 | 7,17 | 19,27 | 1,036 | 17,88 | 9,13 | -0,31 | 0,35 |
| BTC | (v) 30-min | 62,07 | 1,009 | 1,000 | 0,52 | 2,20 | 6,21 | 17,69 | 0,951 | 16,57 | 7,52 | -0,09 | 0,25 |
| BTC | (vi) cc | 61,55 | 1,000 | 0,992 | 0,00 | 4,78 | 10,92 | 18,60 | 1,000 | 15,06 | - | - | - |
| ETH | (iii) 5-min sub | 82,94 | 1,046 | 1,041 | 3,62 | 2,53 | 9,36 | 27,32 | 1,088 | 25,67 | 8,55 | -0,41 | 0,38 |
| ETH | (vi) cc | 79,32 | 1,000 | 0,996 | 0,00 | 4,04 | 12,62 | 25,10 | 1,000 | 21,70 | - | - | - |

(D = RV_fwd30 der Variante minus RV_fwd30 cc in VP, nur RV; Identitaet Var(P_cc) = Var(P_v) + Var(D) + 2 Cov(P_v, D)
auf Rechengenauigkeit erfuellt. ETH-Volltabelle Anhang A.)

**Lesart:**
- Die cc-Zeile reproduziert das Review exakt (kappa 4,78; Rausch-SD 10,92; "rauschfrei" 15,06).
- Die HF-Tages-RV hat kappa ~2,0..2,5 statt ~1. Bei 288 Renditen je Tag waere reines Diskretisierungsrauschen von der
  Ordnung 1 + 2/288 x Kurtosis-Faktor [abg.]; der Rest ist Tag-zu-Tag-Schwankung der wahren Varianz (Spruenge,
  Clusterung innerhalb der Woche). Die Delta-Methode schreibt diese Schwankung dem Rauschen zu - auch bei cc. Damit war
  "34 % Rauschanteil, SD rauschfrei ~15,1" eine Ueberschaetzung.
- Das direkt gemessene Rauschen von RV_cc gegen HF ist SD(D) ~8 VP (~19 % der Praemienvarianz), aber D ist mit dem
  RV-Niveau positiv korreliert (Intraday-Umkehr hebt die HF-RV in bewegten Phasen ueber die Tages-RV: Lag-1-ACF der
  5-min-Renditen -0,047 BTC / -0,048 ETH, der 1-min-Renditen +0,019 / +0,011 [nj:data_rv_day]). Die HF-Praemie traegt
  diese Zusatzstreuung des RV-Niveaus; netto bleibt die Varianz der Praemie gleich (BTC) oder steigt (ETH).
- Signatur: die rms-RV faellt von 5 min (1,072) ueber 15 min (1,029) und 30 min (1,009) zu cc (1,000); 1-min (1,061)
  und das Phasenmittel der 5-min-Gitter (1,055) liegen unter dem 5-min-Gitter ab 00:00 (1,072) - das Gitter ab voller
  Stunde traegt also eine phasenabhaengige Zusatzkomponente (Beobachtung, Ursache nicht untersucht). Ein
  Bid-Ask-Rauschen im engeren Sinn ist nicht der Treiber: es wuerde 1-min am staerksten verzerren, die Lag-1-ACF der
  1-min-Renditen ist aber positiv [abg.].

## 5. Varianzfaktor c nach Regel P-3 und Konsens-c (A-3)

| Variante (BTC S1) | c Regel P-3 (max aus 6) | traegt | Konsens-c (getaperte ACF-Summe) | c stat. Bootstrap 30 / 60 / 90 | c_m Monat |
|---|---:|---|---:|---|---:|
| (i) 1-min | 31,61 | BM L 90 | 24,46 | 17,8 / 20,2 / 20,0 | 1,0 |
| (ii) 5-min | 30,96 | BM L 90 | 23,12 | 17,6 / 19,1 / 18,9 | 1,0 |
| (iii) 5-min sub | 31,46 | BM L 90 | 24,36 | 17,8 / 19,5 / 19,2 | 1,0 |
| (iv) 15-min | 31,31 | BM L 90 | 26,47 | 18,2 / 21,0 / 20,9 | 1,0 |
| (v) 30-min | 30,65 | BM L 90 | 23,84 | 17,8 / 20,0 / 19,4 | 1,0 |
| (vi) cc | 28,17 | BM L 90 | 18,58 (Review: 18,6) | 15,9 / 17,7 / 17,5 | 1,0 |

- Der Konsens-c ist **je Variante neu gemessen** (gleicher Schaetzer wie Review). Der Review-Wert 18,6 gilt nur fuer cc;
  ihn auf HF zu uebertragen waere eine Lesart in Richtung Testbarkeit ohne Beleg (nur Bericht, Spalte "Konsens 18,6" in
  Anhang A).
- Konsens-c als bindende Regel waere eine programmweite Aenderung von P-3 (eigene DEC, Richtung Testbarkeit) - UNBELEGT
  als Regel, hier nur Gabelung.
- B-7 (REVIEW_H27) gilt verschaerft: stationaerer Bootstrap mit Blocklaenge 30..90 gibt 17,6..21,0, deutlich unter dem
  Regel-c und unter dem Konsens; eine Lauf-SE mit kurzer Blocklaenge waere gegen die Power-Zeile antikonservativ.

## 6. Fenster-SE, Fensterlaenge und Kalenderdaten (A-4, `power_p1`)

**SE und Zuordnung zweier gleicher Fenster (BTC S1, pi-2 zentral 9,47 VP, SE = max(SE_nuis, SE_null H-27))**
[nj:power.BTC_S1.<v>.<c>|se_null_h27.windows_L12.pi2_central]

| Variante | c | SE n 335 (bindend) | Power P-1 | Regime P-1 / A3 | SE n 365 (Bericht) | Power P-1 | Regime P-1 / A3 |
|---|---|---:|---:|---|---:|---:|---|
| (iii) 5-min sub | Regel 31,46 | 5,70 | 0,506 | GL012 / GL012 | 5,47 | 0,535 | GL012 / GL012 |
| (iii) 5-min sub | Konsens gemessen 24,36 | 5,02 | 0,595 | GL012 / GL012 | 4,81 | 0,627 | GL012 / GL012 |
| (i) 1-min | Regel 31,61 | 5,71 | 0,506 | GL012 / GL012 | 5,47 | 0,535 | GL012 / GL012 |
| (v) 30-min | Regel 30,65 | 5,35 | 0,549 | GL012 / GL012 | 5,13 | 0,580 | GL012 / GL012 |
| (vi) cc | Regel 28,17 | 5,39 | 0,544 | GL012 / GL012 | 5,17 | 0,575 | GL012 / GL012 |
| (vi) cc | Konsens 18,58 | 4,38 | 0,698 | GL012 / GL012 | 4,20 | 0,730 | GL012 / GL012 |

SE_null (4,17 bei n 365, cc-Welt) bindet nirgends ausser bei (v) mit Review-c 18,6 (Anhang A). Oberer Prior-Rand 13,72
bei n 365: (iii) Regel-c Power 0,807 -> C10 nur unter P-1 ("zugelassen nur durch DEC-94"), bei n 335 0,776 -> GL012.

**Tage je Fenster fuer C10 / DEC-52 und Datum "voll" (zwei disjunkte Fenster ab 2026-07-01, RV-Ziel 30 Tage nach
Fensterende; Spalten wie Bilanz Zeilen 272-274)** [nj:power.BTC_S1.<v>.<c>|se_null_h27.durations]

| Konfiguration (BTC S1) | SD | c | Prior | C10 P-1 | DEC-52 P-1 | C10 A3-Praxis | DEC-52 A3 (3,168) | voll C10 P-1 | voll DEC-52 P-1 | voll A3 |
|---|---:|---:|---|---:|---:|---:|---:|---|---|---|
| **(iii) 5-min sub, c Regel** | 18,62 | 31,46 | **pi-2 zentral 9,47** | **751,7** | 822,9 | 1.346,7 | 1.080,5 | **2030-09-11** | 2031-01-31 | 2033-12-14 |
| (iii), c Regel | 18,62 | 31,46 | pi-2 unten 7,00 | 1.375,9 | 1.506,3 | 2.464,9 | 1.977,7 | 2034-02-10 | 2034-10-30 | 2040-01-28 |
| (iii), c Regel | 18,62 | 31,46 | pi-2 oben 13,72 | 358,2 | 392,1 | 641,7 | 514,8 | 2028-07-17 | 2028-09-23 | 2030-02-03 |
| (iii), c Regel | 18,62 | 31,46 | pi-1 10,48 | 613,6 | 671,8 | 1.099,3 | 882,0 | 2029-12-09 | 2030-04-04 | 2032-08-07 |
| (iii), c Regel | 18,62 | 31,46 | DEC-98 N2 pi-2 7,14 | 1.322,1 | 1.447,5 | 2.368,6 | 1.900,4 | 2033-10-27 | 2034-07-04 | 2039-07-20 |
| (iii), Konsens-c gemessen | 18,62 | 24,36 | pi-2 zentral 9,47 | 582,1 | 637,3 | 1.042,9 | 836,7 | 2029-10-08 | 2030-01-26 | 2032-04-15 |
| (iii), Konsens-c gemessen | 18,62 | 24,36 | DEC-98 N2 pi-2 7,14 | 1.023,8 | 1.120,9 | 1.834,3 | 1.471,7 | 2032-03-08 | 2032-09-18 | 2036-08-16 |
| (iii), Review-c 18,6 (nicht belegt fuer HF) | 18,62 | 18,60 | pi-2 zentral 9,47 | 444,4 | 486,6 | 796,2 | 638,8 | 2029-01-05 | 2029-03-30 | 2030-12-10 |
| (i) 1-min, c Regel | 18,58 | 31,61 | pi-2 zentral 9,47 | 752,3 | 823,7 | 1.347,9 | 1.081,4 | 2030-09-13 | 2031-02-02 | 2033-12-16 |
| (ii) 5-min, c Regel | 19,47 | 30,96 | pi-2 zentral 9,47 | 809,4 | 886,2 | 1.450,1 | 1.163,5 | 2031-01-05 | 2031-06-08 | 2034-07-10 |
| (iv) 15-min, c Regel | 19,27 | 31,31 | pi-2 zentral 9,47 | 801,6 | 877,6 | 1.436,1 | 1.152,2 | 2030-12-20 | 2031-05-21 | 2034-06-12 |
| (v) 30-min, c Regel | 17,69 | 30,65 | pi-2 zentral 9,47 | 661,7 | 724,4 | 1.185,5 | 951,1 | 2030-03-15 | 2030-07-19 | 2033-01-26 |
| (v) 30-min, Konsens-c gemessen | 17,69 | 23,84 | pi-2 zentral 9,47 | 514,7 | 563,5 | 922,2 | 739,9 | 2029-05-25 | 2029-08-31 | 2031-08-19 |
| (vi) cc = H-27-Referenz, c Regel | 18,60 | 28,17 | pi-2 zentral 9,47 | 671,8 | 735,5 | 1.203,6 | 965,7 | 2030-04-04 | 2030-08-10 | 2033-03-03 |
| (vi) cc, Konsens-c | 18,60 | 18,58 | pi-2 zentral 9,47 | 443,0 | 485,0 | 793,7 | 636,8 | 2029-01-03 | 2029-03-28 | 2030-12-04 |
| Bilanz-Annahme HF (SD 15,1 UNBELEGT), c Regel | 15,1 | 28,2 | pi-2 zentral | 442,9 | 484,9 | 793,5 | 636,6 | 2029-01-01 | 2029-03-26 | 2030-12-04 |
| Bilanz-Annahme HF, Konsens-c 18,6 | 15,1 | 18,6 | pi-2 zentral | 292,4 | 320,1 | 523,9 | 420,3 | 2028-03-07 | 2028-05-02 | 2029-06-12 |

- **Gegenprobe:** derselbe Loeser gibt fuer die H-27-Referenz 671,8 / 735,5 / 1.203,6 / 965,7 Tage und 2030-04-04
  [nj:solver_check_h27_reference] - identisch mit Bilanz 2.3 und [fj:power.configs.BTC/S1.days_needed_pi2_central].
  Die letzten zwei Zeilen sind die Bilanz-Werte (PROGRAMM_BILANZ Zeilen 272-273), hier als widerlegt gefuehrt.
- **Fruehestes VRP-Urteil mit HF-RV** (C10 unter P-1, beide Fenster, zentraler Prior, c nach Regel): **2030-09-11**
  (Variante iii; mit dem nach DEC-98 Nachtrag 2 gestuetzten Prior 7,14 VP: 2033-10-27). Mit gemessenem Konsens-c
  (Gabelung Testbarkeit): 2029-10-08. Mit cc statt HF (H-27-Definition): 2030-04-04 bzw. 2029-01-03 - HF ist in jeder
  Lesart spaeter.
- **Selektionsdecke (DEC-94 (7), Bericht):** zaehlen alle hier gerechneten Konfigurationen (6 RV-Varianten x 3
  Einheiten x 3 Beine, K 54), steigt z auf 2,306 und (iii) braucht 1.204 Tage (2033-03-05); K 12 / 18: 764 / 883 Tage;
  K <= 11 aendert nichts [nj:power.selection_K_report].
- **Vergleich mit SD 15,1 (R-9):** nicht bestaetigt (unguenstiger); gemessen 18,62 (iii), +3,5 VP. Die Bilanz-Hebelzeile
  "HF-Statistik -34 % / -57 %" kehrt sich um: +12 % Tage (c Regel) bzw. +31 % (Konsens, je gegen cc mit gleichem
  c-Schaetzer) [abg.: 751,7/671,8; 582,1/443,0].
- **Prior-Lesarten bei Niveau-Verzerrung (Gabelung, Bericht):** pi-2 auf dem HF-Niveau bewertet 9,99 VP (Testbarkeit;
  nur wenn die RV der Literatur HF-artig gemessen ist) -> 675,1 Tage; Gegenlesart "Literatur-RV wie Tagesschluss, die
  HF-RV liegt 5,5 % hoeher" -> Netto-Prior 100 x 0,6155 x (e^0,1431 - 1,055) = 6,07 VP (Strenge) -> 1.827,8 Tage
  (2036-08-02) [nj:power.BTC_S1.v3_5min_sub.c_rule_P3|se_null_h27.durations.pi2_central_cc_literature_level_bias]. Die
  RV-Definition der Literaturquelle ist UNBELEGT (DEC-98 Nachtrag 2: "RV nachlaufend", Frequenz nicht genannt).

## 7. Bein-Aggregation (A-5, Bericht; c Regel bzw. Konsens, SE_null H-27, pi-2 zentral; ETH-Prior UNBELEGT)

| Variante | Bein | SD S1 | c Regel / Konsens | Prior | C10 P-1 Tage (Regel / Konsens) | voll (Regel) |
|---|---|---:|---|---:|---|---|
| (iii) | BTC | 18,62 | 31,46 / 24,36 | 9,47 | 751,7 / 582,1 | 2030-09-11 |
| (iii) | ETH (relative Praemie wie BTC, UNBELEGT) | 27,32 | 35,40 / 28,48 | 12,20 | 1.097,1 / 882,4 | 2032-08-03 |
| (iii) | Tagesmittel BTC/ETH | 22,53 | 34,28 / 27,17 | 10,84 | 916,5 / 726,4 | 2031-08-07 |
| (iii) | Konjunktion BTC und ETH | - | - | - | 1.097,1 / 882,4 | 2032-08-03 |
| (vi) cc | Tagesmittel BTC/ETH | 20,93 | 27,91 / 20,06 | 10,84 | 643,4 / 462,5 | 2030-02-07 |
| (vi) cc | Konjunktion | - | - | - | 723,3 / 547,3 | 2030-07-17 |

Korrelation der Tagespraemie BTC/ETH S1 (Pearson / Spearman): HF 0,911..0,932 / 0,872..0,900, cc 0,831 / 0,817
[nj:correlations]. Mit HF-RV wandern die Beine noch staerker gemeinsam; das Tagesmittel bringt keinen Gewinn (DEC-62 E3
"ein Bein" bestaetigt). Korrelation HF- gegen cc-Praemie desselben Symbols: BTC 0,88..0,92, ETH 0,93..0,96.

## 8. Gabelungen (Ermessen mit Richtung, Muster DEC-93 H-1)

| Wahl | Lesart hier | Gegenlesart | Richtung der Gegenlesart | Wirkung (Tage C10, iii) |
|---|---|---|---|---|
| RV-Variante | (iii) nach Regel R-10 (vorab) | (v) 30-min, kleinste SD | Testbarkeit (Auswahl nach SD) | 751,7 -> 661,7 |
| Varianzfaktor | Regel P-3 (31,46) | gemessener Konsens (24,36) | Testbarkeit (P-3-Aenderung, eigene DEC) | 751,7 -> 582,1 |
| Konsens-Wert | je Variante gemessen | Review-Wert 18,6 uebertragen | Testbarkeit, unbelegt | 582,1 -> 444,4 |
| SE_null | H-27-Wert (cc-Welt) | HF-SE_null kleiner (UNBELEGT) | Testbarkeit | ohne Wirkung (Nuisance bindet) |
| Prior | pi-2 zentral 9,47 (Auftrag) | DEC-98 N2: 7,14 (Band 3,2..10,5) | Strenge | 751,7 -> 1.322,1 |
| Prior-Niveau | cc-Niveau 61,55 % | HF-Niveau 64,95 % (9,99) / Literatur-RV cc-artig (6,07) | Testbarkeit / Strenge | 675,1 / 1.827,8 |
| Fensterumfang L = 12 | n 335 bindend (Auftrag) | n 365 (DEC-96 E2-Zaehlung) | Testbarkeit | Power 0,506 -> 0,535 |

Keine Gabelung macht HF-RV besser als cc mit gleichem Schaetzer; der einzige Weg zu kuerzeren Fenstern als H-27 ist eine
Kombination mehrerer Testbarkeits-Lesarten (Konsens-c als Regel plus Prior-Obergrenze), die schon fuer cc offenlag.

## 9. UNBELEGT / offen

| Punkt | Status | Wirkung |
|---|---|---|
| Jensen-J der HF-Welt (Niveau-Verzerrung 1,055, Intraday-Umkehr) | UNBELEGT, nicht gerechnet | jede HF-Statistik in S1/S2; Prior-Lesart 6,07 vs 9,99 VP |
| SE_null der HF-Welt | UNBELEGT (waere kleiner als 4,17), nicht neu kalibriert | ohne Wirkung, solange die Nuisance bindet |
| ETH-Prior | UNBELEGT | ETH-Bein, Tagesmittel, Konjunktion nur Bericht |
| Konsens-c als Regel | waere P-3-Aenderung (eigene DEC, Testbarkeit) | Faktor ~0,77 auf die Tage |
| RV-Definition der Literatur-Stichprobe (Almeida et al.) | UNBELEGT (Frequenz nicht genannt) | Prior einer HF-Statistik |
| Abdeckung `bybit/rest.kline1m` ab 2026-07-01 (Definitionsgleichheit kuenftiger Fenster) | nicht geprueft (kein Katalogzugriff in diesem Auftrag); nur Vollstaendigkeit pruefbar (DEC-96 E3) | Voraussetzung jeder HF-Hypothese |
| Normal-Naeherung der Power-Zeile bei Exzess-Kurtosis 2,6 der HF-Praemie | Merkposten | Power-Zeile, Positivkontrolle |

## 10. Reproduktion

- Skripte unter `scratchpad/hfrv_herleitung/` (sha256 in [nj:skripte_sha256]): `hfrv_common.py` (Regeln R-1..R-13,
  Lader, Waechter), `hfrv_power.py` (Bilanz-Loeser, quelltextgleich per AST geprueft), `nuisance_hfrv.py` (dieser
  Bericht), `a2_census.py` (Teil B), `make_tables.py` (Anhang A); unveraendert kopiert aus `scratchpad/h27_herleitung/`:
  `h27_common.py` (4093396d...), `h27_series.py` (d3c9d339...), `nuisance.py` (33e3f89a...), `power_h27.py` (d65c8579...).
- Aufruf: `python3 -I nuisance_hfrv.py` (~20 s, CPU), dann `python3 -I make_tables.py`. Drei Laeufe ergaben dieselbe
  sha256 von `nuisance_hfrv.json` (`3c03e5bf...ddd74fed`); Eingaben-sha256 in [nj:inputs_sha256].
- Ausgaben ohne Praemien-/DVOL-Mittel und ohne Vorzeichen: `no_mean` und `guard_keys` laufen vor dem Schreiben.

---

## Anhang A - Volltabellen (gerendert aus `nuisance_hfrv.json` mit `make_tables.py`)


### BTC S1

| Variante | n (zus.haengend) | SD | ACF 1 / 10 / 20 / 30 / 60 / 120 / 180 | erster Lag < 0,10 | Kurt. (exz.) | c Bartlett 60/90/120 | c BM 60/90/120 | c stat. Bootstrap 30/60/90 | **c Regel P-3** | Konsens-c | Monat SD / ACF1 / c_m |
|---|---:|---:|---|---:|---:|---|---|---|---:|---:|---|
| (i) 1-min | 1135 (1135) | 18,58 | 0,966 / 0,558 / 0,154 / -0,042 / 0,033 / -0,000 / -0,059 | 22 | 2,45 | 20,4 / 21,6 / 21,2 | 25,6 / 31,6 / 23,4 | 17,8 / 20,2 / 20,0 | **31,61** | 24,5 | 18,72 / -0,05 / 1,0 |
| (ii) 5-min | 1135 (1135) | 19,47 | 0,966 / 0,568 / 0,163 / -0,053 / 0,017 / 0,025 / -0,085 | 22 | 3,32 | 20,3 / 21,2 / 20,6 | 25,9 / 31,0 / 22,9 | 17,6 / 19,1 / 18,9 | **30,96** | 23,1 | 19,63 / -0,06 / 1,0 |
| (iii) 5-min sub | 1135 (1135) | 18,62 | 0,967 / 0,562 / 0,161 / -0,039 / 0,029 / -0,005 / -0,084 | 22 | 2,58 | 20,5 / 21,7 / 21,2 | 25,7 / 31,5 / 24,2 | 17,8 / 19,5 / 19,2 | **31,46** | 24,4 | 18,76 / -0,05 / 1,0 |
| (iv) 15-min | 1135 (1135) | 19,27 | 0,966 / 0,564 / 0,161 / -0,049 / 0,073 / 0,009 / -0,062 | 22 | 2,61 | 20,7 / 22,5 / 22,4 | 25,8 / 31,3 / 25,8 | 18,2 / 21,0 / 20,9 | **31,31** | 26,5 | 19,43 / -0,06 / 1,0 |
| (v) 30-min | 1135 (1135) | 17,69 | 0,964 / 0,545 / 0,143 / -0,042 / 0,028 / 0,024 / -0,072 | 22 | 1,82 | 20,1 / 21,2 / 20,7 | 24,0 / 30,7 / 21,2 | 17,8 / 20,0 / 19,4 | **30,65** | 23,8 | 17,83 / -0,05 / 1,0 |
| (vi) cc | 1135 (1135) | 18,60 | 0,955 / 0,514 / 0,107 / -0,155 / 0,054 / 0,012 / -0,073 | 21 | -0,03 | 16,9 / 17,4 / 17,8 | 19,2 / 28,2 / 15,2 | 15,9 / 17,7 / 17,5 | **28,17** | 18,6 | 18,70 / -0,16 / 1,0 |

### BTC S2

| Variante | n (zus.haengend) | SD | ACF 1 / 10 / 20 / 30 / 60 / 120 / 180 | erster Lag < 0,10 | Kurt. (exz.) | c Bartlett 60/90/120 | c BM 60/90/120 | c stat. Bootstrap 30/60/90 | **c Regel P-3** | Konsens-c | Monat SD / ACF1 / c_m |
|---|---:|---:|---|---:|---:|---|---|---|---:|---:|---|
| (i) 1-min | 1135 (1135) | 31,55 | 0,962 / 0,546 / 0,149 / -0,017 / -0,025 / -0,041 / -0,056 | 22 | 8,42 | 20,3 / 21,0 / 20,5 | 27,7 / 29,7 / 20,3 | 17,7 / 19,1 / 18,5 | **29,70** | 22,5 | 31,66 / -0,03 / 1,0 |
| (ii) 5-min | 1135 (1135) | 34,09 | 0,965 / 0,569 / 0,172 / -0,018 / -0,053 / -0,004 / -0,079 | 23 | 11,36 | 20,7 / 20,9 / 20,2 | 28,8 / 29,7 / 20,2 | 17,8 / 18,3 / 17,7 | **29,71** | 21,4 | 34,23 / -0,02 / 1,0 |
| (iii) 5-min sub | 1135 (1135) | 31,50 | 0,962 / 0,550 / 0,159 / -0,006 / -0,028 / -0,043 / -0,078 | 22 | 8,89 | 20,5 / 21,3 / 20,8 | 28,0 / 30,2 / 21,3 | 17,8 / 18,8 / 18,1 | **30,15** | 22,9 | 31,63 / -0,02 / 1,0 |
| (iv) 15-min | 1135 (1135) | 32,32 | 0,963 / 0,551 / 0,158 / -0,018 / 0,003 / -0,024 / -0,063 | 22 | 9,13 | 20,6 / 21,8 / 21,8 | 28,0 / 29,8 / 21,9 | 18,1 / 20,0 / 19,7 | **29,76** | 24,4 | 32,47 / -0,02 / 1,0 |
| (v) 30-min | 1135 (1135) | 28,69 | 0,956 / 0,516 / 0,133 / -0,005 / 0,005 / -0,009 / -0,063 | 22 | 5,93 | 20,0 / 21,3 / 21,5 | 26,1 / 29,6 / 20,4 | 17,8 / 20,3 / 19,9 | **29,58** | 24,2 | 28,78 / -0,01 / 1,0 |
| (vi) cc | 1135 (1135) | 27,26 | 0,943 / 0,486 / 0,128 / -0,046 / 0,047 / 0,013 / -0,048 | 21 | 1,26 | 18,7 / 20,3 / 21,7 | 22,0 / 29,4 / 18,0 | 17,2 / 20,8 / 21,3 | **29,44** | 23,6 | 27,28 / -0,05 / 1,0 |

### BTC S3

| Variante | n (zus.haengend) | SD | ACF 1 / 10 / 20 / 30 / 60 / 120 / 180 | erster Lag < 0,10 | Kurt. (exz.) | c Bartlett 60/90/120 | c BM 60/90/120 | c stat. Bootstrap 30/60/90 | **c Regel P-3** | Konsens-c | Monat SD / ACF1 / c_m |
|---|---:|---:|---|---:|---:|---|---|---|---:|---:|---|
| (i) 1-min | 1135 (1135) | 0,271 | 0,970 / 0,571 / 0,134 / -0,133 / 0,123 / 0,067 / -0,053 | 21 | 0,46 | 19,2 / 20,7 / 20,0 | 23,4 / 29,0 / 25,0 | 17,1 / 19,7 / 20,0 | **28,97** | 24,3 | 0,273 / -0,14 / 1,0 |
| (ii) 5-min | 1135 (1135) | 0,285 | 0,967 / 0,560 / 0,108 / -0,186 / 0,139 / 0,067 / -0,074 | 21 | 0,49 | 17,8 / 19,1 / 18,4 | 21,9 / 26,6 / 23,8 | 16,1 / 17,9 / 17,8 | **26,58** | 22,1 | 0,288 / -0,19 / 1,0 |
| (iii) 5-min sub | 1135 (1135) | 0,276 | 0,969 / 0,574 / 0,134 / -0,146 / 0,126 / 0,062 / -0,069 | 21 | 0,39 | 19,0 / 20,3 / 19,6 | 23,1 / 28,0 / 25,2 | 16,8 / 18,8 / 18,9 | **28,02** | 23,7 | 0,278 / -0,15 / 1,0 |
| (iv) 15-min | 1135 (1135) | 0,293 | 0,967 / 0,562 / 0,109 / -0,185 / 0,170 / 0,055 / -0,044 | 21 | 0,60 | 18,2 / 19,9 / 19,1 | 22,3 / 26,3 / 26,1 | 16,5 / 18,8 / 18,6 | **26,30** | 23,8 | 0,296 / -0,19 / 1,0 |
| (v) 30-min | 1135 (1135) | 0,270 | 0,970 / 0,578 / 0,136 / -0,137 / 0,079 / 0,078 / -0,059 | 21 | 0,54 | 19,2 / 19,7 / 18,0 | 21,9 / 27,6 / 19,2 | 16,9 / 18,1 / 17,4 | **27,60** | 21,4 | 0,272 / -0,14 / 1,0 |
| (vi) cc | 1135 (1135) | 0,304 | 0,960 / 0,529 / 0,072 / -0,278 / 0,108 / 0,017 / -0,090 | 20 | -0,06 | 14,6 / 14,7 / 14,3 | 16,6 / 25,9 / 13,0 | 14,4 / 14,7 / 14,2 | **25,94** | 14,9 | 0,306 / -0,29 / 1,0 |

### ETH S1

| Variante | n (zus.haengend) | SD | ACF 1 / 10 / 20 / 30 / 60 / 120 / 180 | erster Lag < 0,10 | Kurt. (exz.) | c Bartlett 60/90/120 | c BM 60/90/120 | c stat. Bootstrap 30/60/90 | **c Regel P-3** | Konsens-c | Monat SD / ACF1 / c_m |
|---|---:|---:|---|---:|---:|---|---|---|---:|---:|---|
| (i) 1-min | 1135 (1135) | 26,63 | 0,976 / 0,652 / 0,291 / 0,048 / -0,031 / 0,036 / -0,154 | 27 | 4,63 | 24,7 / 25,9 / 25,8 | 34,7 / 35,5 / 31,5 | 21,3 / 23,8 / 24,9 | **35,47** | 28,6 | 26,86 / 0,05 / 1,1 |
| (ii) 5-min | 1135 (1135) | 29,42 | 0,976 / 0,661 / 0,293 / 0,031 / -0,041 / 0,068 / -0,150 | 27 | 6,45 | 24,6 / 25,4 / 25,1 | 35,4 / 34,4 / 31,1 | 21,0 / 22,6 / 23,5 | **35,38** | 27,3 | 29,69 / 0,04 / 1,1 |
| (iii) 5-min sub | 1135 (1135) | 27,32 | 0,977 / 0,659 / 0,300 / 0,053 / -0,039 / 0,034 / -0,156 | 27 | 5,36 | 25,0 / 26,1 / 25,9 | 35,3 / 35,4 / 32,1 | 21,4 / 23,3 / 24,3 | **35,40** | 28,5 | 27,56 / 0,06 / 1,1 |
| (iv) 15-min | 1135 (1135) | 26,96 | 0,975 / 0,643 / 0,275 / 0,031 / 0,002 / 0,030 / -0,140 | 26 | 4,36 | 24,3 / 25,9 / 26,0 | 34,1 / 33,4 / 33,5 | 21,2 / 23,6 / 24,3 | **34,12** | 29,4 | 27,20 / 0,04 / 1,1 |
| (v) 30-min | 1135 (1135) | 24,35 | 0,975 / 0,643 / 0,278 / 0,051 / -0,030 / 0,037 / -0,170 | 27 | 3,07 | 24,5 / 25,7 / 25,5 | 33,1 / 34,3 / 31,8 | 21,4 / 23,7 / 24,5 | **34,31** | 28,5 | 24,56 / 0,05 / 1,1 |
| (vi) cc | 1135 (1135) | 25,10 | 0,965 / 0,582 / 0,189 / -0,072 / -0,032 / 0,038 / -0,100 | 23 | 3,35 | 20,3 / 20,5 / 20,2 | 27,6 / 27,2 / 23,0 | 18,0 / 19,4 / 19,7 | **27,64** | 20,9 | 25,22 / -0,06 / 1,0 |

### ETH S2

| Variante | n (zus.haengend) | SD | ACF 1 / 10 / 20 / 30 / 60 / 120 / 180 | erster Lag < 0,10 | Kurt. (exz.) | c Bartlett 60/90/120 | c BM 60/90/120 | c stat. Bootstrap 30/60/90 | **c Regel P-3** | Konsens-c | Monat SD / ACF1 / c_m |
|---|---:|---:|---|---:|---:|---|---|---|---:|---:|---|
| (i) 1-min | 1135 (1135) | 64,52 | 0,977 / 0,639 / 0,243 / -0,004 / -0,062 / 0,003 / -0,124 | 25 | 13,70 | 23,0 / 23,2 / 22,5 | 35,8 / 30,8 / 25,2 | 20,0 / 20,3 / 20,3 | **35,77** | 23,9 | 64,91 / 0,01 / 1,0 |
| (ii) 5-min | 1135 (1135) | 76,91 | 0,979 / 0,658 / 0,261 / -0,005 / -0,063 / 0,041 / -0,111 | 25 | 18,14 | 23,5 / 23,7 / 23,1 | 36,7 / 31,2 / 26,6 | 20,4 / 20,2 / 20,4 | **36,71** | 24,2 | 77,47 / 0,00 / 1,0 |
| (iii) 5-min sub | 1135 (1135) | 67,69 | 0,978 / 0,647 / 0,256 / 0,006 / -0,062 / 0,007 / -0,122 | 25 | 15,05 | 23,4 / 23,8 / 23,1 | 36,5 / 31,4 / 26,6 | 20,4 / 20,4 / 20,4 | **36,50** | 24,6 | 68,15 / 0,02 / 1,0 |
| (iv) 15-min | 1135 (1135) | 63,55 | 0,977 / 0,627 / 0,226 / -0,017 / -0,041 / -0,000 / -0,118 | 24 | 13,82 | 22,5 / 23,1 / 22,4 | 35,2 / 29,3 / 26,0 | 19,9 / 20,1 / 19,9 | **35,17** | 24,3 | 63,93 / -0,00 / 1,0 |
| (v) 30-min | 1135 (1135) | 54,17 | 0,974 / 0,617 / 0,220 / 0,004 / -0,055 / 0,002 / -0,146 | 24 | 9,32 | 22,5 / 22,9 / 22,1 | 34,1 / 29,9 / 25,3 | 19,8 / 20,4 / 20,2 | **34,13** | 23,9 | 54,45 / 0,02 / 1,0 |
| (vi) cc | 1135 (1135) | 55,95 | 0,967 / 0,572 / 0,140 / -0,104 / -0,051 / 0,020 / -0,080 | 21 | 10,29 | 19,1 / 18,7 / 17,8 | 29,4 / 23,7 / 18,2 | 17,1 / 17,2 / 16,8 | **29,41** | 18,1 | 56,05 / -0,08 / 1,0 |

### ETH S3

| Variante | n (zus.haengend) | SD | ACF 1 / 10 / 20 / 30 / 60 / 120 / 180 | erster Lag < 0,10 | Kurt. (exz.) | c Bartlett 60/90/120 | c BM 60/90/120 | c stat. Bootstrap 30/60/90 | **c Regel P-3** | Konsens-c | Monat SD / ACF1 / c_m |
|---|---:|---:|---|---:|---:|---|---|---|---:|---:|---|
| (i) 1-min | 1135 (1135) | 0,286 | 0,973 / 0,643 / 0,281 / 0,016 / 0,076 / 0,082 / -0,120 | 26 | 0,15 | 24,4 / 27,0 / 28,0 | 31,2 / 35,0 / 38,8 | 21,2 / 26,1 / 28,7 | **38,82** | 32,5 | 0,289 / 0,02 / 1,1 |
| (ii) 5-min | 1135 (1135) | 0,311 | 0,971 / 0,628 / 0,240 / -0,055 / 0,078 / 0,092 / -0,116 | 24 | 0,56 | 22,4 / 24,3 / 24,9 | 29,6 / 30,9 / 36,4 | 19,6 / 23,2 / 24,9 | **36,43** | 28,5 | 0,314 / -0,05 / 1,0 |
| (iii) 5-min sub | 1135 (1135) | 0,290 | 0,973 / 0,643 / 0,272 / -0,008 / 0,065 / 0,078 / -0,121 | 26 | 0,31 | 23,7 / 25,8 / 26,5 | 30,5 / 33,4 / 37,4 | 20,7 / 24,6 / 26,6 | **37,37** | 30,4 | 0,293 / -0,01 / 1,0 |
| (iv) 15-min | 1135 (1135) | 0,308 | 0,970 / 0,620 / 0,233 / -0,059 / 0,110 / 0,073 / -0,096 | 24 | 0,73 | 22,3 / 24,7 / 25,5 | 29,0 / 29,7 / 38,6 | 19,9 / 23,9 / 25,2 | **38,60** | 29,9 | 0,312 / -0,06 / 1,0 |
| (v) 30-min | 1135 (1135) | 0,276 | 0,974 / 0,647 / 0,270 / 0,002 / 0,058 / 0,096 / -0,124 | 26 | 0,25 | 23,9 / 26,0 / 26,5 | 29,6 / 32,9 / 35,6 | 21,1 / 24,9 / 27,0 | **35,57** | 30,4 | 0,278 / 0,00 / 1,0 |
| (vi) cc | 1135 (1135) | 0,287 | 0,958 / 0,554 / 0,181 / -0,108 / 0,018 / 0,066 / -0,106 | 23 | 0,69 | 19,1 / 19,7 / 20,1 | 23,5 / 26,4 / 24,0 | 17,1 / 19,2 / 20,2 | **26,42** | 21,0 | 0,287 / -0,10 / 1,0 |

### LEG_BTCETH S1

| Variante | n (zus.haengend) | SD | ACF 1 / 10 / 20 / 30 / 60 / 120 / 180 | erster Lag < 0,10 | Kurt. (exz.) | c Bartlett 60/90/120 | c BM 60/90/120 | c stat. Bootstrap 30/60/90 | **c Regel P-3** | Konsens-c | Monat SD / ACF1 / c_m |
|---|---:|---:|---|---:|---:|---|---|---|---:|---:|---|
| (i) 1-min | 1135 (1135) | 22,16 | 0,974 / 0,617 / 0,236 / 0,013 / -0,003 / 0,016 / -0,121 | 25 | 3,87 | 23,1 / 24,4 / 24,2 | 31,3 / 34,2 / 28,5 | 20,0 / 22,5 / 23,1 | **34,21** | 27,3 | 22,34 / 0,01 / 1,0 |
| (ii) 5-min | 1135 (1135) | 24,05 | 0,974 / 0,628 / 0,245 / -0,000 / -0,020 / 0,047 / -0,129 | 25 | 5,32 | 23,0 / 23,9 / 23,5 | 31,9 / 33,3 / 28,1 | 19,7 / 21,3 / 21,7 | **33,30** | 25,8 | 24,26 / -0,00 / 1,0 |
| (iii) 5-min sub | 1135 (1135) | 22,53 | 0,974 / 0,624 / 0,248 / 0,019 / -0,011 / 0,013 / -0,133 | 25 | 4,34 | 23,3 / 24,5 / 24,3 | 31,7 / 34,3 / 29,2 | 20,1 / 22,0 / 22,4 | **34,28** | 27,2 | 22,73 / 0,02 / 1,0 |
| (iv) 15-min | 1135 (1135) | 22,69 | 0,973 / 0,612 / 0,228 / -0,003 / 0,033 / 0,018 / -0,114 | 25 | 3,81 | 22,8 / 24,6 / 24,6 | 30,9 / 32,8 / 30,3 | 20,0 / 22,6 / 22,9 | **32,76** | 28,4 | 22,89 / -0,00 / 1,0 |
| (v) 30-min | 1135 (1135) | 20,56 | 0,972 / 0,603 / 0,220 / 0,011 / -0,006 / 0,027 / -0,138 | 24 | 2,70 | 22,7 / 23,9 / 23,5 | 29,5 / 33,0 / 27,1 | 19,9 / 22,1 / 22,2 | **32,99** | 26,6 | 20,73 / 0,01 / 1,0 |
| (vi) cc | 1135 (1135) | 20,93 | 0,962 / 0,554 / 0,152 / -0,107 / 0,006 / 0,026 / -0,108 | 22 | 1,56 | 18,9 / 19,3 / 19,3 | 23,7 / 27,9 / 18,8 | 17,0 / 18,8 / 19,0 | **27,91** | 20,1 | 21,04 / -0,10 / 1,0 |

### LEG_BTCETH S2

| Variante | n (zus.haengend) | SD | ACF 1 / 10 / 20 / 30 / 60 / 120 / 180 | erster Lag < 0,10 | Kurt. (exz.) | c Bartlett 60/90/120 | c BM 60/90/120 | c stat. Bootstrap 30/60/90 | **c Regel P-3** | Konsens-c | Monat SD / ACF1 / c_m |
|---|---:|---:|---|---:|---:|---|---|---|---:|---:|---|
| (i) 1-min | 1135 (1135) | 47,25 | 0,975 / 0,611 / 0,213 / -0,009 / -0,054 / -0,017 / -0,109 | 24 | 12,37 | 22,1 / 22,5 / 21,7 | 33,3 / 30,5 / 23,3 | 19,2 / 19,8 / 19,5 | **33,33** | 23,3 | 47,50 / -0,00 / 1,0 |
| (ii) 5-min | 1135 (1135) | 54,78 | 0,977 / 0,635 / 0,236 / -0,011 / -0,066 / 0,023 / -0,107 | 25 | 16,48 | 22,7 / 22,8 / 22,0 | 34,5 / 30,7 / 24,3 | 19,6 / 19,4 / 19,3 | **34,52** | 23,1 | 55,13 / -0,01 / 1,0 |
| (iii) 5-min sub | 1135 (1135) | 48,82 | 0,975 / 0,621 / 0,228 / 0,002 / -0,057 / -0,015 / -0,115 | 25 | 13,49 | 22,6 / 23,0 / 22,3 | 34,1 / 31,1 / 24,7 | 19,6 / 19,8 / 19,5 | **34,08** | 23,9 | 49,11 / 0,01 / 1,0 |
| (iv) 15-min | 1135 (1135) | 47,22 | 0,974 / 0,603 / 0,201 / -0,020 / -0,031 / -0,014 / -0,106 | 23 | 12,69 | 21,8 / 22,5 / 22,0 | 32,9 / 29,4 / 24,1 | 19,2 / 19,8 / 19,5 | **32,85** | 24,0 | 47,48 / -0,01 / 1,0 |
| (v) 30-min | 1135 (1135) | 40,62 | 0,970 / 0,583 / 0,186 / -0,003 / -0,040 / -0,009 / -0,128 | 23 | 8,51 | 21,5 / 22,2 / 21,6 | 31,4 / 29,7 / 22,8 | 19,0 / 20,1 / 19,6 | **31,41** | 23,6 | 40,81 / -0,00 / 1,0 |
| (vi) cc | 1135 (1135) | 39,85 | 0,961 / 0,543 / 0,131 / -0,089 / -0,030 / 0,010 / -0,088 | 21 | 6,49 | 18,8 / 18,9 / 18,5 | 26,7 / 25,4 / 16,4 | 16,9 / 18,0 / 17,7 | **26,67** | 19,1 | 39,94 / -0,08 / 1,0 |

### LEG_BTCETH S3

| Variante | n (zus.haengend) | SD | ACF 1 / 10 / 20 / 30 / 60 / 120 / 180 | erster Lag < 0,10 | Kurt. (exz.) | c Bartlett 60/90/120 | c BM 60/90/120 | c stat. Bootstrap 30/60/90 | **c Regel P-3** | Konsens-c | Monat SD / ACF1 / c_m |
|---|---:|---:|---|---:|---:|---|---|---|---:|---:|---|
| (i) 1-min | 1135 (1135) | 0,273 | 0,973 / 0,611 / 0,212 / -0,057 / 0,108 / 0,074 / -0,089 | 24 | 0,33 | 22,0 / 24,2 / 24,5 | 27,7 / 32,3 / 32,9 | 19,3 / 23,3 / 24,8 | **32,89** | 29,0 | 0,275 / -0,06 / 1,0 |
| (ii) 5-min | 1135 (1135) | 0,293 | 0,970 / 0,598 / 0,178 / -0,120 / 0,113 / 0,078 / -0,096 | 23 | 0,55 | 20,3 / 21,9 / 22,0 | 26,2 / 28,9 / 31,0 | 18,0 / 20,8 / 21,6 | **30,96** | 25,7 | 0,296 / -0,12 / 1,0 |
| (iii) 5-min sub | 1135 (1135) | 0,278 | 0,973 / 0,612 / 0,206 / -0,077 / 0,102 / 0,068 / -0,097 | 23 | 0,35 | 21,5 / 23,4 / 23,5 | 27,2 / 31,1 / 32,2 | 18,9 / 22,0 / 23,1 | **32,20** | 27,6 | 0,281 / -0,08 / 1,0 |
| (iv) 15-min | 1135 (1135) | 0,295 | 0,970 / 0,594 / 0,172 / -0,124 / 0,150 / 0,063 / -0,071 | 22 | 0,74 | 20,3 / 22,5 / 22,6 | 26,0 / 28,1 / 33,1 | 18,3 / 21,6 / 22,1 | **33,08** | 27,4 | 0,298 / -0,13 / 1,0 |
| (v) 30-min | 1135 (1135) | 0,267 | 0,974 / 0,615 / 0,203 / -0,071 / 0,075 / 0,086 / -0,095 | 23 | 0,46 | 21,6 / 22,9 / 22,3 | 26,1 / 30,3 / 27,8 | 19,0 / 21,6 / 22,3 | **30,31** | 26,1 | 0,269 / -0,07 / 1,0 |
| (vi) cc | 1135 (1135) | 0,283 | 0,961 / 0,548 / 0,123 / -0,202 / 0,074 / 0,046 / -0,112 | 21 | 0,29 | 16,8 / 17,2 / 17,3 | 19,6 / 26,2 / 17,9 | 15,7 / 17,1 / 17,5 | **26,18** | 18,0 | 0,285 / -0,21 / 1,0 |

### RV-Niveau, Signatur, kappa, Rauschen

| Symbol | Variante | rms RV_fwd30 % | /cc | /30-min | Niveau-Abw. VP | kappa L1 | kappa L2,3,5 (Review) | kappa L2..5 | Rausch-SD VP (Delta) | SD S1 | SD/SD_cc | SD rauschfrei (Delta) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC | (i) 1-min | 65,32 | 1,061 | 1,052 | 3,77 | 1,62 | 2,06 | 2,04 | 6,13 | 18,58 | 0,999 | 17,54 |
| BTC | (ii) 5-min | 65,98 | 1,072 | 1,063 | 4,43 | 2,03 | 2,51 | 2,48 | 7,41 | 19,47 | 1,047 | 18,01 |
| BTC | (iii) 5-min sub | 64,95 | 1,055 | 1,046 | 3,40 | 1,63 | 2,05 | 2,04 | 6,06 | 18,62 | 1,001 | 17,60 |
| BTC | (iv) 15-min | 63,35 | 1,029 | 1,021 | 1,80 | 1,88 | 2,54 | 2,51 | 7,17 | 19,27 | 1,036 | 17,88 |
| BTC | (v) 30-min | 62,07 | 1,009 | 1,000 | 0,52 | 1,72 | 2,20 | 2,19 | 6,21 | 17,69 | 0,951 | 16,57 |
| BTC | (vi) cc | 61,55 | 1,000 | 0,992 | 0,00 | 3,68 | 4,78 | 4,51 | 10,92 | 18,60 | 1,000 | 15,06 |
| ETH | (i) 1-min | 82,95 | 1,046 | 1,042 | 3,63 | 1,74 | 2,32 | 2,29 | 8,69 | 26,63 | 1,061 | 25,17 |
| ETH | (ii) 5-min | 84,98 | 1,071 | 1,067 | 5,66 | 2,68 | 3,44 | 3,34 | 12,12 | 29,42 | 1,172 | 26,81 |
| ETH | (iii) 5-min sub | 82,94 | 1,046 | 1,041 | 3,62 | 1,93 | 2,53 | 2,49 | 9,36 | 27,32 | 1,088 | 25,67 |
| ETH | (iv) 15-min | 81,21 | 1,024 | 1,020 | 1,89 | 1,65 | 2,35 | 2,32 | 8,62 | 26,96 | 1,074 | 25,54 |
| ETH | (v) 30-min | 79,65 | 1,004 | 1,000 | 0,33 | 1,41 | 1,79 | 1,79 | 6,46 | 24,35 | 0,970 | 23,48 |
| ETH | (vi) cc | 79,32 | 1,000 | 0,996 | 0,00 | 4,14 | 4,04 | 4,09 | 12,62 | 25,10 | 1,000 | 21,70 |

### Korrelationen

| Variante | Pearson BTC/ETH S1 / S2 / S3 | Spearman BTC/ETH S1 / S2 / S3 | Pearson HF vs cc BTC S1 | ETH S1 |
|---|---|---|---:|---:|
| (i) 1-min | 0,920 / 0,927 / 0,921 | 0,879 / 0,875 / 0,893 | 0,909 | 0,953 |
| (ii) 5-min | 0,932 / 0,940 / 0,935 | 0,900 / 0,894 / 0,906 | 0,885 | 0,932 |
| (iii) 5-min sub | 0,922 / 0,928 / 0,926 | 0,888 / 0,880 / 0,903 | 0,904 | 0,950 |
| (iv) 15-min | 0,926 / 0,933 / 0,929 | 0,879 / 0,879 / 0,888 | 0,884 | 0,932 |
| (v) 30-min | 0,911 / 0,915 / 0,914 | 0,872 / 0,871 / 0,881 | 0,915 | 0,957 |
| (vi) cc | 0,831 / 0,812 / 0,835 | 0,817 / 0,824 / 0,803 | 1,000 | 1,000 |

### Fenster-SE und Zuordnung bei zwei Fenstern zu n IV-Tagen (BTC S1, pi-2 zentral 9,47)

| Variante | c | SE_null | SE n 335 (Quelle) | Power P-1 335 | Regime P-1 / A3 335 | SE n 365 | Power P-1 365 | Regime P-1 / A3 365 |
|---|---|---|---:|---:|---|---:|---:|---|
| (i) 1-min | c_rule_P3 31,6 | se_null_h27 | 5,71 (nuisance) | 0,506 | GL012 / GL012 | 5,47 | 0,535 | GL012 / GL012 |
| (i) 1-min | c_rule_P3 31,6 | nuisance_only | 5,71 (nuisance) | 0,506 | GL012 / GL012 | 5,47 | 0,535 | GL012 / GL012 |
| (i) 1-min | c_consensus_measured 24,5 | se_null_h27 | 5,02 (nuisance) | 0,595 | GL012 / GL012 | 4,81 | 0,627 | GL012 / GL012 |
| (i) 1-min | c_consensus_measured 24,5 | nuisance_only | 5,02 (nuisance) | 0,595 | GL012 / GL012 | 4,81 | 0,627 | GL012 / GL012 |
| (i) 1-min | c_consensus_review_18_6 18,6 | se_null_h27 | 4,38 (nuisance) | 0,698 | GL012 / GL012 | 4,19 | 0,730 | GL012 / GL012 |
| (i) 1-min | c_consensus_review_18_6 18,6 | nuisance_only | 4,38 (nuisance) | 0,698 | GL012 / GL012 | 4,19 | 0,730 | GL012 / GL012 |
| (ii) 5-min | c_rule_P3 31,0 | se_null_h27 | 5,92 (nuisance) | 0,482 | GL012 / GL012 | 5,67 | 0,510 | GL012 / GL012 |
| (ii) 5-min | c_rule_P3 31,0 | nuisance_only | 5,92 (nuisance) | 0,482 | GL012 / GL012 | 5,67 | 0,510 | GL012 / GL012 |
| (ii) 5-min | c_consensus_measured 23,1 | se_null_h27 | 5,12 (nuisance) | 0,582 | GL012 / GL012 | 4,90 | 0,613 | GL012 / GL012 |
| (ii) 5-min | c_consensus_measured 23,1 | nuisance_only | 5,12 (nuisance) | 0,582 | GL012 / GL012 | 4,90 | 0,613 | GL012 / GL012 |
| (ii) 5-min | c_consensus_review_18_6 18,6 | se_null_h27 | 4,59 (nuisance) | 0,662 | GL012 / GL012 | 4,40 | 0,695 | GL012 / GL012 |
| (ii) 5-min | c_consensus_review_18_6 18,6 | nuisance_only | 4,59 (nuisance) | 0,662 | GL012 / GL012 | 4,40 | 0,695 | GL012 / GL012 |
| (iii) 5-min sub | c_rule_P3 31,5 | se_null_h27 | 5,70 (nuisance) | 0,506 | GL012 / GL012 | 5,47 | 0,535 | GL012 / GL012 |
| (iii) 5-min sub | c_rule_P3 31,5 | nuisance_only | 5,70 (nuisance) | 0,506 | GL012 / GL012 | 5,47 | 0,535 | GL012 / GL012 |
| (iii) 5-min sub | c_consensus_measured 24,4 | se_null_h27 | 5,02 (nuisance) | 0,595 | GL012 / GL012 | 4,81 | 0,627 | GL012 / GL012 |
| (iii) 5-min sub | c_consensus_measured 24,4 | nuisance_only | 5,02 (nuisance) | 0,595 | GL012 / GL012 | 4,81 | 0,627 | GL012 / GL012 |
| (iii) 5-min sub | c_consensus_review_18_6 18,6 | se_null_h27 | 4,39 (nuisance) | 0,696 | GL012 / GL012 | 4,20 | 0,729 | GL012 / GL012 |
| (iii) 5-min sub | c_consensus_review_18_6 18,6 | nuisance_only | 4,39 (nuisance) | 0,696 | GL012 / GL012 | 4,20 | 0,729 | GL012 / GL012 |
| (iv) 15-min | c_rule_P3 31,3 | se_null_h27 | 5,89 (nuisance) | 0,485 | GL012 / GL012 | 5,64 | 0,513 | GL012 / GL012 |
| (iv) 15-min | c_rule_P3 31,3 | nuisance_only | 5,89 (nuisance) | 0,485 | GL012 / GL012 | 5,64 | 0,513 | GL012 / GL012 |
| (iv) 15-min | c_consensus_measured 26,5 | se_null_h27 | 5,42 (nuisance) | 0,541 | GL012 / GL012 | 5,19 | 0,571 | GL012 / GL012 |
| (iv) 15-min | c_consensus_measured 26,5 | nuisance_only | 5,42 (nuisance) | 0,541 | GL012 / GL012 | 5,19 | 0,571 | GL012 / GL012 |
| (iv) 15-min | c_consensus_review_18_6 18,6 | se_null_h27 | 4,54 (nuisance) | 0,670 | GL012 / GL012 | 4,35 | 0,703 | GL012 / GL012 |
| (iv) 15-min | c_consensus_review_18_6 18,6 | nuisance_only | 4,54 (nuisance) | 0,670 | GL012 / GL012 | 4,35 | 0,703 | GL012 / GL012 |
| (v) 30-min | c_rule_P3 30,7 | se_null_h27 | 5,35 (nuisance) | 0,549 | GL012 / GL012 | 5,13 | 0,580 | GL012 / GL012 |
| (v) 30-min | c_rule_P3 30,7 | nuisance_only | 5,35 (nuisance) | 0,549 | GL012 / GL012 | 5,13 | 0,580 | GL012 / GL012 |
| (v) 30-min | c_consensus_measured 23,8 | se_null_h27 | 4,72 (nuisance) | 0,641 | GL012 / GL012 | 4,52 | 0,673 | GL012 / GL012 |
| (v) 30-min | c_consensus_measured 23,8 | nuisance_only | 4,72 (nuisance) | 0,641 | GL012 / GL012 | 4,52 | 0,673 | GL012 / GL012 |
| (v) 30-min | c_consensus_review_18_6 18,6 | se_null_h27 | 4,36 (null_world_h27) | 0,701 | GL012 / GL012 | 4,17 | 0,734 | GL012 / GL012 |
| (v) 30-min | c_consensus_review_18_6 18,6 | nuisance_only | 4,17 (nuisance) | 0,734 | GL012 / GL012 | 3,99 | 0,766 | GL012 / GL012 |
| (vi) cc | c_rule_P3 28,2 | se_null_h27 | 5,39 (nuisance) | 0,544 | GL012 / GL012 | 5,17 | 0,575 | GL012 / GL012 |
| (vi) cc | c_rule_P3 28,2 | nuisance_only | 5,39 (nuisance) | 0,544 | GL012 / GL012 | 5,17 | 0,575 | GL012 / GL012 |
| (vi) cc | c_consensus_measured 18,6 | se_null_h27 | 4,38 (nuisance) | 0,698 | GL012 / GL012 | 4,20 | 0,730 | GL012 / GL012 |
| (vi) cc | c_consensus_measured 18,6 | nuisance_only | 4,38 (nuisance) | 0,698 | GL012 / GL012 | 4,20 | 0,730 | GL012 / GL012 |
| (vi) cc | c_consensus_review_18_6 18,6 | se_null_h27 | 4,38 (nuisance) | 0,697 | GL012 / GL012 | 4,20 | 0,729 | GL012 / GL012 |
| (vi) cc | c_consensus_review_18_6 18,6 | nuisance_only | 4,38 (nuisance) | 0,697 | GL012 / GL012 | 4,20 | 0,729 | GL012 / GL012 |

### Tage je Fenster und Datum 'voll' (zwei Fenster ab 2026-07-01, RV-Ziel +30 Tage)

| Variante | c | SE_null | Prior | C10 P-1 | DEC-52 P-1 | C10 A3-Praxis | DEC-52 A3 (3,168) | voll C10 P-1 | voll DEC-52 P-1 | voll C10 A3 |
|---|---|---|---|---:|---:|---:|---:|---|---|---|
| (i) 1-min | c_rule_P3 31,6 | se_null_h27 | pi2_central 9,47 | 752,3 | 823,7 | 1.347,9 | 1.081,4 | 2030-09-13 | 2031-02-02 | 2033-12-16 |
| (i) 1-min | c_rule_P3 31,6 | se_null_h27 | pi2_low 7,00 | 1.377,1 | 1.507,7 | 2.467,1 | 1.979,4 | 2034-02-14 | 2034-11-01 | 2040-02-03 |
| (i) 1-min | c_rule_P3 31,6 | se_null_h27 | pi2_high 13,72 | 358,5 | 392,5 | 642,3 | 515,3 | 2028-07-17 | 2028-09-23 | 2030-02-05 |
| (i) 1-min | c_rule_P3 31,6 | se_null_h27 | pi1 10,48 | 614,2 | 672,4 | 1.100,3 | 882,8 | 2029-12-11 | 2030-04-06 | 2032-08-09 |
| (i) 1-min | c_rule_P3 31,6 | se_null_h27 | dec98n2_pi2_7_14 7,14 | 1.323,3 | 1.448,8 | 2.370,7 | 1.902,1 | 2033-10-29 | 2034-07-06 | 2039-07-24 |
| (i) 1-min | c_rule_P3 31,6 | se_null_h27 | dec98n2_qdensity_3_16 3,16 | 6.755,8 | 7.396,4 | 12.103,4 | 9.710,9 | 2063-07-28 | 2067-01-30 | 2092-11-08 |
| (i) 1-min | c_rule_P3 31,6 | se_null_h27 | pi2_central_at_variant_level 10,05 | 667,9 | 731,3 | 1.196,6 | 960,1 | 2030-03-27 | 2030-08-02 | 2033-02-17 |
| (i) 1-min | c_rule_P3 31,6 | se_null_h27 | pi2_central_cc_literature_level_bias 5,70 | 2.079,9 | 2.277,2 | 3.726,3 | 2.989,7 | 2037-12-19 | 2039-01-19 | 2046-12-26 |
| (i) 1-min | c_rule_P3 31,6 | nuisance_only | pi2_central 9,47 | 752,3 | 823,7 | 1.347,9 | 1.081,4 | 2030-09-13 | 2031-02-02 | 2033-12-16 |
| (i) 1-min | c_consensus_measured 24,5 | se_null_h27 | pi2_central 9,47 | 582,2 | 637,4 | 1.043,0 | 836,8 | 2029-10-08 | 2030-01-26 | 2032-04-17 |
| (i) 1-min | c_consensus_measured 24,5 | se_null_h27 | pi2_low 7,00 | 1.065,6 | 1.166,7 | 1.909,1 | 1.531,7 | 2032-05-31 | 2032-12-19 | 2037-01-13 |
| (i) 1-min | c_consensus_measured 24,5 | se_null_h27 | pi2_high 13,72 | 277,4 | 303,7 | 497,0 | 398,8 | 2028-02-06 | 2028-03-29 | 2029-04-21 |
| (i) 1-min | c_consensus_measured 24,5 | se_null_h27 | pi1 10,48 | 475,3 | 520,3 | 851,5 | 683,1 | 2029-03-08 | 2029-06-06 | 2031-03-30 |
| (i) 1-min | c_consensus_measured 24,5 | se_null_h27 | dec98n2_pi2_7_14 7,14 | 1.024,0 | 1.121,1 | 1.834,5 | 1.471,9 | 2032-03-08 | 2032-09-20 | 2036-08-16 |
| (i) 1-min | c_consensus_measured 24,5 | se_null_h27 | dec98n2_qdensity_3_16 3,16 | 5.227,8 | 5.723,5 | 9.365,9 | 7.514,5 | 2055-03-16 | 2057-12-02 | 2077-11-11 |
| (i) 1-min | c_consensus_measured 24,5 | se_null_h27 | pi2_central_at_variant_level 10,05 | 516,9 | 565,9 | 926,0 | 742,9 | 2029-05-29 | 2029-09-04 | 2031-08-25 |
| (i) 1-min | c_consensus_measured 24,5 | se_null_h27 | pi2_central_cc_literature_level_bias 5,70 | 1.609,5 | 1.762,1 | 2.883,5 | 2.313,5 | 2035-05-24 | 2036-03-25 | 2042-05-15 |
| (i) 1-min | c_consensus_measured 24,5 | nuisance_only | pi2_central 9,47 | 582,2 | 637,4 | 1.043,0 | 836,8 | 2029-10-08 | 2030-01-26 | 2032-04-17 |
| (i) 1-min | c_consensus_review_18_6 18,6 | se_null_h27 | pi2_central 9,47 | 442,7 | 484,6 | 793,1 | 636,3 | 2029-01-01 | 2029-03-26 | 2030-12-04 |
| (i) 1-min | c_consensus_review_18_6 18,6 | nuisance_only | pi2_central 9,47 | 442,7 | 484,6 | 793,1 | 636,3 | 2029-01-01 | 2029-03-26 | 2030-12-04 |
| (ii) 5-min | c_rule_P3 31,0 | se_null_h27 | pi2_central 9,47 | 809,4 | 886,2 | 1.450,1 | 1.163,5 | 2031-01-05 | 2031-06-08 | 2034-07-10 |
| (ii) 5-min | c_rule_P3 31,0 | se_null_h27 | pi2_low 7,00 | 1.481,6 | 1.622,0 | 2.654,3 | 2.129,6 | 2034-09-10 | 2035-06-19 | 2041-02-11 |
| (ii) 5-min | c_rule_P3 31,0 | se_null_h27 | pi2_high 13,72 | 385,7 | 422,3 | 691,0 | 554,4 | 2028-09-09 | 2028-11-22 | 2030-05-12 |
| (ii) 5-min | c_rule_P3 31,0 | se_null_h27 | pi1 10,48 | 660,8 | 723,4 | 1.183,8 | 949,8 | 2030-03-13 | 2030-07-17 | 2033-01-22 |
| (ii) 5-min | c_rule_P3 31,0 | se_null_h27 | dec98n2_pi2_7_14 7,14 | 1.423,7 | 1.558,7 | 2.550,6 | 2.046,4 | 2034-05-17 | 2035-02-11 | 2040-07-18 |
| (ii) 5-min | c_rule_P3 31,0 | se_null_h27 | dec98n2_qdensity_3_16 3,16 | 7.268,4 | 7.957,5 | 13.021,7 | 10.447,6 | 2066-05-19 | 2070-02-25 | 2097-11-18 |
| (ii) 5-min | c_rule_P3 31,0 | se_null_h27 | pi2_central_at_variant_level 10,15 | 704,4 | 771,2 | 1.262,0 | 1.012,6 | 2030-06-09 | 2030-10-21 | 2033-06-29 |
| (ii) 5-min | c_rule_P3 31,0 | se_null_h27 | pi2_central_cc_literature_level_bias 5,04 | 2.855,2 | 3.125,9 | 5.115,2 | 4.104,1 | 2042-03-20 | 2043-09-11 | 2054-08-04 |
| (ii) 5-min | c_rule_P3 31,0 | nuisance_only | pi2_central 9,47 | 809,4 | 886,2 | 1.450,1 | 1.163,5 | 2031-01-05 | 2031-06-08 | 2034-07-10 |
| (ii) 5-min | c_consensus_measured 23,1 | se_null_h27 | pi2_central 9,47 | 604,6 | 661,9 | 1.083,1 | 869,0 | 2029-11-21 | 2030-03-15 | 2032-07-06 |
| (ii) 5-min | c_consensus_measured 23,1 | se_null_h27 | pi2_low 7,00 | 1.106,6 | 1.211,5 | 1.982,6 | 1.590,7 | 2032-08-21 | 2033-03-19 | 2037-06-08 |
| (ii) 5-min | c_consensus_measured 23,1 | se_null_h27 | pi2_high 13,72 | 288,1 | 315,4 | 516,1 | 414,1 | 2028-02-28 | 2028-04-22 | 2029-05-29 |
| (ii) 5-min | c_consensus_measured 23,1 | se_null_h27 | pi1 10,48 | 493,5 | 540,3 | 884,2 | 709,4 | 2029-04-13 | 2029-07-16 | 2031-06-04 |
| (ii) 5-min | c_consensus_measured 23,1 | se_null_h27 | dec98n2_pi2_7_14 7,14 | 1.063,4 | 1.164,2 | 1.905,1 | 1.528,5 | 2032-05-27 | 2032-12-15 | 2037-01-05 |
| (ii) 5-min | c_consensus_measured 23,1 | se_null_h27 | dec98n2_qdensity_3_16 3,16 | 5.428,9 | 5.943,7 | 9.726,2 | 7.803,6 | 2056-04-21 | 2059-02-15 | 2079-11-03 |
| (ii) 5-min | c_consensus_measured 23,1 | se_null_h27 | pi2_central_at_variant_level 10,15 | 526,2 | 576,1 | 942,7 | 756,3 | 2029-06-18 | 2029-09-26 | 2031-09-28 |
| (ii) 5-min | c_consensus_measured 23,1 | se_null_h27 | pi2_central_cc_literature_level_bias 5,04 | 2.132,6 | 2.334,8 | 3.820,7 | 3.065,4 | 2038-04-04 | 2039-05-13 | 2047-07-02 |
| (ii) 5-min | c_consensus_measured 23,1 | nuisance_only | pi2_central 9,47 | 604,6 | 661,9 | 1.083,1 | 869,0 | 2029-11-21 | 2030-03-15 | 2032-07-06 |
| (ii) 5-min | c_consensus_review_18_6 18,6 | se_null_h27 | pi2_central 9,47 | 486,3 | 532,4 | 871,3 | 699,0 | 2029-03-30 | 2029-06-30 | 2031-05-09 |
| (ii) 5-min | c_consensus_review_18_6 18,6 | nuisance_only | pi2_central 9,47 | 486,3 | 532,4 | 871,3 | 699,0 | 2029-03-30 | 2029-06-30 | 2031-05-09 |
| (iii) 5-min sub | c_rule_P3 31,5 | se_null_h27 | pi2_central 9,47 | 751,7 | 822,9 | 1.346,7 | 1.080,5 | 2030-09-11 | 2031-01-31 | 2033-12-14 |
| (iii) 5-min sub | c_rule_P3 31,5 | se_null_h27 | pi2_low 7,00 | 1.375,9 | 1.506,3 | 2.464,9 | 1.977,7 | 2034-02-10 | 2034-10-30 | 2040-01-28 |
| (iii) 5-min sub | c_rule_P3 31,5 | se_null_h27 | pi2_high 13,72 | 358,2 | 392,1 | 641,7 | 514,8 | 2028-07-17 | 2028-09-23 | 2030-02-03 |
| (iii) 5-min sub | c_rule_P3 31,5 | se_null_h27 | pi1 10,48 | 613,6 | 671,8 | 1.099,3 | 882,0 | 2029-12-09 | 2030-04-04 | 2032-08-07 |
| (iii) 5-min sub | c_rule_P3 31,5 | se_null_h27 | dec98n2_pi2_7_14 7,14 | 1.322,1 | 1.447,5 | 2.368,6 | 1.900,4 | 2033-10-27 | 2034-07-04 | 2039-07-20 |
| (iii) 5-min sub | c_rule_P3 31,5 | se_null_h27 | dec98n2_qdensity_3_16 3,16 | 6.749,7 | 7.389,7 | 12.092,5 | 9.702,2 | 2063-07-16 | 2067-01-16 | 2092-10-17 |
| (iii) 5-min sub | c_rule_P3 31,5 | se_null_h27 | pi2_central_at_variant_level 9,99 | 675,1 | 739,1 | 1.209,5 | 970,4 | 2030-04-12 | 2030-08-18 | 2033-03-15 |
| (iii) 5-min sub | c_rule_P3 31,5 | se_null_h27 | pi2_central_cc_literature_level_bias 6,07 | 1.827,8 | 2.001,1 | 3.274,6 | 2.627,3 | 2036-08-02 | 2037-07-16 | 2044-07-05 |
| (iii) 5-min sub | c_rule_P3 31,5 | nuisance_only | pi2_central 9,47 | 751,7 | 822,9 | 1.346,7 | 1.080,5 | 2030-09-11 | 2031-01-31 | 2033-12-14 |
| (iii) 5-min sub | c_consensus_measured 24,4 | se_null_h27 | pi2_central 9,47 | 582,1 | 637,3 | 1.042,9 | 836,7 | 2029-10-08 | 2030-01-26 | 2032-04-15 |
| (iii) 5-min sub | c_consensus_measured 24,4 | se_null_h27 | pi2_low 7,00 | 1.065,5 | 1.166,5 | 1.908,8 | 1.531,5 | 2032-05-31 | 2032-12-19 | 2037-01-11 |
| (iii) 5-min sub | c_consensus_measured 24,4 | se_null_h27 | pi2_high 13,72 | 277,4 | 303,7 | 496,9 | 398,7 | 2028-02-06 | 2028-03-29 | 2029-04-19 |
| (iii) 5-min sub | c_consensus_measured 24,4 | se_null_h27 | pi1 10,48 | 475,2 | 520,2 | 851,3 | 683,0 | 2029-03-08 | 2029-06-06 | 2031-03-30 |
| (iii) 5-min sub | c_consensus_measured 24,4 | se_null_h27 | dec98n2_pi2_7_14 7,14 | 1.023,8 | 1.120,9 | 1.834,3 | 1.471,7 | 2032-03-08 | 2032-09-18 | 2036-08-16 |
| (iii) 5-min sub | c_consensus_measured 24,4 | se_null_h27 | dec98n2_qdensity_3_16 3,16 | 5.227,0 | 5.722,6 | 9.364,5 | 7.513,4 | 2055-03-16 | 2057-11-30 | 2077-11-09 |
| (iii) 5-min sub | c_consensus_measured 24,4 | se_null_h27 | pi2_central_at_variant_level 9,99 | 522,8 | 572,4 | 936,6 | 751,5 | 2029-06-10 | 2029-09-18 | 2031-09-16 |
| (iii) 5-min sub | c_consensus_measured 24,4 | se_null_h27 | pi2_central_cc_literature_level_bias 6,07 | 1.415,4 | 1.549,7 | 2.535,8 | 2.034,6 | 2034-05-01 | 2035-01-24 | 2040-06-18 |
| (iii) 5-min sub | c_consensus_measured 24,4 | nuisance_only | pi2_central 9,47 | 582,1 | 637,3 | 1.042,9 | 836,7 | 2029-10-08 | 2030-01-26 | 2032-04-15 |
| (iii) 5-min sub | c_consensus_review_18_6 18,6 | se_null_h27 | pi2_central 9,47 | 444,4 | 486,6 | 796,2 | 638,8 | 2029-01-05 | 2029-03-30 | 2030-12-10 |
| (iii) 5-min sub | c_consensus_review_18_6 18,6 | nuisance_only | pi2_central 9,47 | 444,4 | 486,6 | 796,2 | 638,8 | 2029-01-05 | 2029-03-30 | 2030-12-10 |
| (iv) 15-min | c_rule_P3 31,3 | se_null_h27 | pi2_central 9,47 | 801,6 | 877,6 | 1.436,1 | 1.152,2 | 2030-12-20 | 2031-05-21 | 2034-06-12 |
| (iv) 15-min | c_rule_P3 31,3 | se_null_h27 | pi2_low 7,00 | 1.467,3 | 1.606,4 | 2.628,7 | 2.109,1 | 2034-08-13 | 2035-05-18 | 2040-12-21 |
| (iv) 15-min | c_rule_P3 31,3 | se_null_h27 | pi2_high 13,72 | 382,0 | 418,2 | 684,3 | 549,1 | 2028-09-01 | 2028-11-14 | 2030-04-30 |
| (iv) 15-min | c_rule_P3 31,3 | se_null_h27 | pi1 10,48 | 654,4 | 716,4 | 1.172,4 | 940,6 | 2030-03-01 | 2030-07-03 | 2032-12-31 |
| (iv) 15-min | c_rule_P3 31,3 | se_null_h27 | dec98n2_pi2_7_14 7,14 | 1.409,9 | 1.543,6 | 2.526,0 | 2.026,7 | 2034-04-19 | 2035-01-12 | 2040-05-29 |
| (iv) 15-min | c_rule_P3 31,3 | se_null_h27 | dec98n2_qdensity_3_16 3,16 | 7.198,2 | 7.880,7 | 12.895,9 | 10.346,8 | 2065-12-30 | 2069-09-24 | 2097-03-11 |
| (iv) 15-min | c_rule_P3 31,3 | se_null_h27 | pi2_central_at_variant_level 9,75 | 756,8 | 828,5 | 1.355,8 | 1.087,8 | 2030-09-21 | 2031-02-12 | 2034-01-01 |
| (iv) 15-min | c_rule_P3 31,3 | se_null_h27 | pi2_central_cc_literature_level_bias 7,67 | 1.221,4 | 1.337,2 | 2.188,2 | 1.755,7 | 2033-04-08 | 2033-11-26 | 2038-07-25 |
| (iv) 15-min | c_rule_P3 31,3 | nuisance_only | pi2_central 9,47 | 801,6 | 877,6 | 1.436,1 | 1.152,2 | 2030-12-20 | 2031-05-21 | 2034-06-12 |
| (iv) 15-min | c_consensus_measured 26,5 | se_null_h27 | pi2_central 9,47 | 677,5 | 741,8 | 1.213,8 | 973,9 | 2030-04-16 | 2030-08-22 | 2033-03-23 |
| (iv) 15-min | c_consensus_measured 26,5 | se_null_h27 | pi2_low 7,00 | 1.240,2 | 1.357,7 | 2.221,8 | 1.782,6 | 2033-05-16 | 2034-01-05 | 2038-09-29 |
| (iv) 15-min | c_consensus_measured 26,5 | se_null_h27 | pi2_high 13,72 | 322,8 | 353,5 | 578,4 | 464,1 | 2028-05-06 | 2028-07-07 | 2029-09-30 |
| (iv) 15-min | c_consensus_measured 26,5 | se_null_h27 | pi1 10,48 | 553,1 | 605,5 | 990,9 | 795,0 | 2029-08-11 | 2029-11-23 | 2032-01-02 |
| (iv) 15-min | c_consensus_measured 26,5 | se_null_h27 | dec98n2_pi2_7_14 7,14 | 1.191,7 | 1.304,7 | 2.135,0 | 1.713,0 | 2033-02-07 | 2033-09-21 | 2038-04-08 |
| (iv) 15-min | c_consensus_measured 26,5 | se_null_h27 | dec98n2_qdensity_3_16 3,16 | 6.084,0 | 6.660,9 | 10.899,8 | 8.745,2 | 2059-11-24 | 2063-01-19 | 2086-04-06 |
| (iv) 15-min | c_consensus_measured 26,5 | se_null_h27 | pi2_central_at_variant_level 9,75 | 639,6 | 700,3 | 1.145,9 | 919,4 | 2030-01-30 | 2030-06-01 | 2032-11-07 |
| (iv) 15-min | c_consensus_measured 26,5 | se_null_h27 | pi2_central_cc_literature_level_bias 7,67 | 1.032,4 | 1.130,3 | 1.849,5 | 1.483,9 | 2032-03-26 | 2032-10-08 | 2036-09-15 |
| (iv) 15-min | c_consensus_measured 26,5 | nuisance_only | pi2_central 9,47 | 677,5 | 741,8 | 1.213,8 | 973,9 | 2030-04-16 | 2030-08-22 | 2033-03-23 |
| (iv) 15-min | c_consensus_review_18_6 18,6 | se_null_h27 | pi2_central 9,47 | 476,1 | 521,3 | 853,0 | 684,4 | 2029-03-10 | 2029-06-08 | 2031-04-03 |
| (iv) 15-min | c_consensus_review_18_6 18,6 | nuisance_only | pi2_central 9,47 | 476,1 | 521,3 | 853,0 | 684,4 | 2029-03-10 | 2029-06-08 | 2031-04-03 |
| (v) 30-min | c_rule_P3 30,7 | se_null_h27 | pi2_central 9,47 | 661,7 | 724,4 | 1.185,5 | 951,1 | 2030-03-15 | 2030-07-19 | 2033-01-26 |
| (v) 30-min | c_rule_P3 30,7 | se_null_h27 | pi2_low 7,00 | 1.211,2 | 1.326,0 | 2.169,9 | 1.741,0 | 2033-03-19 | 2033-11-04 | 2038-06-17 |
| (v) 30-min | c_rule_P3 30,7 | se_null_h27 | pi2_high 13,72 | 315,3 | 345,2 | 564,9 | 453,2 | 2028-04-22 | 2028-06-21 | 2029-09-02 |
| (v) 30-min | c_rule_P3 30,7 | se_null_h27 | pi1 10,48 | 540,2 | 591,4 | 967,8 | 776,5 | 2029-07-16 | 2029-10-26 | 2031-11-17 |
| (v) 30-min | c_rule_P3 30,7 | se_null_h27 | dec98n2_pi2_7_14 7,14 | 1.163,9 | 1.274,2 | 2.085,1 | 1.672,9 | 2032-12-13 | 2033-07-23 | 2037-12-31 |
| (v) 30-min | c_rule_P3 30,7 | se_null_h27 | dec98n2_qdensity_3_16 3,16 | 5.941,9 | 6.505,3 | 10.645,2 | 8.540,9 | 2059-02-11 | 2062-03-15 | 2084-11-14 |
| (v) 30-min | c_rule_P3 30,7 | se_null_h27 | pi2_central_at_variant_level 9,55 | 650,6 | 712,3 | 1.165,6 | 935,2 | 2030-02-21 | 2030-06-25 | 2032-12-17 |
| (v) 30-min | c_rule_P3 30,7 | se_null_h27 | pi2_central_cc_literature_level_bias 8,95 | 741,5 | 811,8 | 1.328,4 | 1.065,8 | 2030-08-22 | 2031-01-09 | 2033-11-08 |
| (v) 30-min | c_rule_P3 30,7 | nuisance_only | pi2_central 9,47 | 661,7 | 724,4 | 1.185,5 | 951,1 | 2030-03-15 | 2030-07-19 | 2033-01-26 |
| (v) 30-min | c_consensus_measured 23,8 | se_null_h27 | pi2_central 9,47 | 514,7 | 563,5 | 922,2 | 739,9 | 2029-05-25 | 2029-08-31 | 2031-08-19 |
| (v) 30-min | c_consensus_measured 23,8 | se_null_h27 | pi2_low 7,00 | 942,2 | 1.031,5 | 1.688,0 | 1.354,3 | 2031-09-28 | 2032-03-24 | 2035-10-27 |
| (v) 30-min | c_consensus_measured 23,8 | se_null_h27 | pi2_high 13,72 | 245,3 | 268,5 | 439,4 | 352,6 | 2027-12-04 | 2028-01-19 | 2028-12-26 |
| (v) 30-min | c_consensus_measured 23,8 | se_null_h27 | pi1 10,48 | 420,2 | 460,0 | 752,8 | 604,0 | 2028-11-18 | 2029-02-06 | 2030-09-13 |
| (v) 30-min | c_consensus_measured 23,8 | se_null_h27 | dec98n2_pi2_7_14 7,14 | 905,4 | 991,2 | 1.622,0 | 1.301,4 | 2031-07-16 | 2032-01-04 | 2035-06-19 |
| (v) 30-min | c_consensus_measured 23,8 | se_null_h27 | dec98n2_qdensity_3_16 3,16 | 4.622,2 | 5.060,4 | 8.280,9 | 6.644,0 | 2051-11-22 | 2054-04-16 | 2071-12-03 |
| (v) 30-min | c_consensus_measured 23,8 | se_null_h27 | pi2_central_at_variant_level 9,55 | 506,1 | 554,1 | 906,7 | 727,5 | 2029-05-09 | 2029-08-13 | 2031-07-18 |
| (v) 30-min | c_consensus_measured 23,8 | se_null_h27 | pi2_central_cc_literature_level_bias 8,95 | 576,8 | 631,5 | 1.033,3 | 829,1 | 2029-09-26 | 2030-01-14 | 2032-03-28 |
| (v) 30-min | c_consensus_measured 23,8 | nuisance_only | pi2_central 9,47 | 514,7 | 563,5 | 922,2 | 739,9 | 2029-05-25 | 2029-08-31 | 2031-08-19 |
| (v) 30-min | c_consensus_review_18_6 18,6 | se_null_h27 | pi2_central 9,47 | 438,4 | 480,0 | 785,4 | 630,2 | 2028-12-24 | 2029-03-16 | 2030-11-18 |
| (v) 30-min | c_consensus_review_18_6 18,6 | nuisance_only | pi2_central 9,47 | 401,5 | 439,6 | 719,4 | 577,2 | 2028-10-11 | 2028-12-26 | 2030-07-09 |
| (vi) cc | c_rule_P3 28,2 | se_null_h27 | pi2_central 9,47 | 671,8 | 735,5 | 1.203,6 | 965,7 | 2030-04-04 | 2030-08-10 | 2033-03-03 |
| (vi) cc | c_rule_P3 28,2 | se_null_h27 | pi2_low 7,00 | 1.229,7 | 1.346,3 | 2.203,1 | 1.767,6 | 2033-04-24 | 2033-12-14 | 2038-08-24 |
| (vi) cc | c_rule_P3 28,2 | se_null_h27 | pi2_high 13,72 | 320,1 | 350,5 | 573,5 | 460,2 | 2028-05-02 | 2028-07-01 | 2029-09-20 |
| (vi) cc | c_rule_P3 28,2 | se_null_h27 | pi1 10,48 | 548,4 | 600,4 | 982,6 | 788,3 | 2029-08-01 | 2029-11-13 | 2031-12-17 |
| (vi) cc | c_rule_P3 28,2 | se_null_h27 | dec98n2_pi2_7_14 7,14 | 1.181,7 | 1.293,7 | 2.117,0 | 1.698,6 | 2033-01-18 | 2033-08-30 | 2038-03-05 |
| (vi) cc | c_rule_P3 28,2 | se_null_h27 | dec98n2_qdensity_3_16 3,16 | 6.032,8 | 6.604,8 | 10.808,1 | 8.671,7 | 2059-08-12 | 2062-09-29 | 2085-10-06 |
| (vi) cc | c_rule_P3 28,2 | se_null_h27 | pi2_central_at_variant_level 9,47 | 671,8 | 735,5 | 1.203,6 | 965,7 | 2030-04-04 | 2030-08-10 | 2033-03-03 |
| (vi) cc | c_rule_P3 28,2 | se_null_h27 | pi2_central_cc_literature_level_bias 9,47 | 671,8 | 735,5 | 1.203,6 | 965,7 | 2030-04-04 | 2030-08-10 | 2033-03-03 |
| (vi) cc | c_rule_P3 28,2 | nuisance_only | pi2_central 9,47 | 671,8 | 735,5 | 1.203,6 | 965,7 | 2030-04-04 | 2030-08-10 | 2033-03-03 |
| (vi) cc | c_consensus_measured 18,6 | se_null_h27 | pi2_central 9,47 | 443,0 | 485,0 | 793,7 | 636,8 | 2029-01-03 | 2029-03-28 | 2030-12-04 |
| (vi) cc | c_consensus_measured 18,6 | se_null_h27 | pi2_low 7,00 | 810,9 | 887,8 | 1.452,7 | 1.165,6 | 2031-01-07 | 2031-06-10 | 2034-07-14 |
| (vi) cc | c_consensus_measured 18,6 | se_null_h27 | pi2_high 13,72 | 211,1 | 231,1 | 378,2 | 303,4 | 2027-09-27 | 2027-11-06 | 2028-08-26 |
| (vi) cc | c_consensus_measured 18,6 | se_null_h27 | pi1 10,48 | 361,6 | 395,9 | 647,9 | 519,8 | 2028-07-23 | 2028-09-29 | 2030-02-15 |
| (vi) cc | c_consensus_measured 18,6 | se_null_h27 | dec98n2_pi2_7_14 7,14 | 779,2 | 853,1 | 1.396,0 | 1.120,0 | 2030-11-06 | 2031-04-03 | 2034-03-22 |
| (vi) cc | c_consensus_measured 18,6 | se_null_h27 | dec98n2_qdensity_3_16 3,16 | 3.978,1 | 4.355,3 | 7.127,0 | 5.718,1 | 2048-05-13 | 2050-06-06 | 2065-08-08 |
| (vi) cc | c_consensus_measured 18,6 | se_null_h27 | pi2_central_at_variant_level 9,47 | 443,0 | 485,0 | 793,7 | 636,8 | 2029-01-03 | 2029-03-28 | 2030-12-04 |
| (vi) cc | c_consensus_measured 18,6 | se_null_h27 | pi2_central_cc_literature_level_bias 9,47 | 443,0 | 485,0 | 793,7 | 636,8 | 2029-01-03 | 2029-03-28 | 2030-12-04 |
| (vi) cc | c_consensus_measured 18,6 | nuisance_only | pi2_central 9,47 | 443,0 | 485,0 | 793,7 | 636,8 | 2029-01-03 | 2029-03-28 | 2030-12-04 |
| (vi) cc | c_consensus_review_18_6 18,6 | se_null_h27 | pi2_central 9,47 | 443,6 | 485,6 | 794,7 | 637,6 | 2029-01-03 | 2029-03-28 | 2030-12-06 |
| (vi) cc | c_consensus_review_18_6 18,6 | nuisance_only | pi2_central 9,47 | 443,6 | 485,6 | 794,7 | 637,6 | 2029-01-03 | 2029-03-28 | 2030-12-06 |

### Bericht: S3/S2/ETH/Bein (c Regel bzw. Konsens, SE_null H-27, pi-2 zentral)

| Variante | Konfiguration | c | SD | Prior | C10 P-1 Tage | voll | C10 A3 Tage | voll A3 |
|---|---|---|---:|---:|---:|---|---:|---|
| (i) 1-min | BTC_S3 | c_rule 29,0 | 0,271 | 0,143 | 641,6 | 2030-02-03 | 1.149,4 | 2032-11-15 |
| (i) 1-min | BTC_S3 | c_consensus_measured 24,3 | 0,271 | 0,143 | 537,3 | 2029-07-10 | 962,6 | 2031-11-07 |
| (i) 1-min | BTC_S2 | c_rule 29,7 | 31,550 | 12,553 | 1.159,9 | 2032-12-05 | 2.078,1 | 2037-12-17 |
| (i) 1-min | BTC_S2 | c_consensus_measured 22,5 | 31,550 | 12,553 | 880,2 | 2031-05-27 | 1.576,9 | 2035-03-19 |
| (i) 1-min | ETH_S1 | c_rule 35,5 | 26,634 | 12,203 | 1.044,7 | 2032-04-19 | 1.871,6 | 2036-10-29 |
| (i) 1-min | ETH_S1 | c_consensus_measured 28,6 | 26,634 | 12,203 | 841,3 | 2031-03-10 | 1.507,2 | 2034-11-01 |
| (i) 1-min | LEG_S1 | c_rule 34,2 | 22,162 | 10,836 | 884,7 | 2031-06-04 | 1.584,9 | 2035-04-04 |
| (i) 1-min | LEG_S1 | c_consensus_measured 27,3 | 22,162 | 10,836 | 705,0 | 2030-06-09 | 1.263,0 | 2033-06-29 |
| (i) 1-min | Konjunktion BTC+ETH | c_rule | - | - | 1.044,7 | 2032-04-19 | - | - |
| (i) 1-min | Konjunktion BTC+ETH | c_consensus_measured | - | - | 841,3 | 2031-03-10 | - | - |
| (ii) 5-min | BTC_S3 | c_rule 26,6 | 0,285 | 0,143 | 654,0 | 2030-02-27 | 1.171,6 | 2032-12-29 |
| (ii) 5-min | BTC_S3 | c_consensus_measured 22,1 | 0,285 | 0,143 | 544,2 | 2029-07-24 | 974,9 | 2031-12-01 |
| (ii) 5-min | BTC_S2 | c_rule 29,7 | 34,089 | 12,553 | 1.354,5 | 2033-12-30 | 2.426,6 | 2039-11-13 |
| (ii) 5-min | BTC_S2 | c_consensus_measured 21,4 | 34,089 | 12,553 | 975,8 | 2031-12-03 | 1.748,2 | 2036-02-26 |
| (ii) 5-min | ETH_S1 | c_rule 35,4 | 29,419 | 12,203 | 1.271,5 | 2033-07-17 | 2.277,9 | 2039-01-19 |
| (ii) 5-min | ETH_S1 | c_consensus_measured 27,3 | 29,419 | 12,203 | 979,4 | 2031-12-11 | 1.754,6 | 2036-03-09 |
| (ii) 5-min | LEG_S1 | c_rule 33,3 | 24,047 | 10,836 | 1.013,9 | 2032-02-17 | 1.816,5 | 2036-07-11 |
| (ii) 5-min | LEG_S1 | c_consensus_measured 25,8 | 24,047 | 10,836 | 785,4 | 2030-11-18 | 1.407,1 | 2034-04-15 |
| (ii) 5-min | Konjunktion BTC+ETH | c_rule | - | - | 1.271,5 | 2033-07-17 | - | - |
| (ii) 5-min | Konjunktion BTC+ETH | c_consensus_measured | - | - | 979,4 | 2031-12-11 | - | - |
| (iii) 5-min sub | BTC_S3 | c_rule 28,0 | 0,276 | 0,143 | 643,2 | 2030-02-07 | 1.152,3 | 2032-11-21 |
| (iii) 5-min sub | BTC_S3 | c_consensus_measured 23,7 | 0,276 | 0,143 | 542,9 | 2029-07-20 | 972,7 | 2031-11-27 |
| (iii) 5-min sub | BTC_S2 | c_rule 30,2 | 31,501 | 12,553 | 1.173,9 | 2033-01-02 | 2.103,1 | 2038-02-05 |
| (iii) 5-min sub | BTC_S2 | c_consensus_measured 22,9 | 31,501 | 12,553 | 890,9 | 2031-06-16 | 1.596,1 | 2035-04-28 |
| (iii) 5-min sub | ETH_S1 | c_rule 35,4 | 27,320 | 12,203 | 1.097,1 | 2032-08-03 | 1.965,5 | 2037-05-05 |
| (iii) 5-min sub | ETH_S1 | c_consensus_measured 28,5 | 27,320 | 12,203 | 882,4 | 2031-05-31 | 1.580,9 | 2035-03-27 |
| (iii) 5-min sub | LEG_S1 | c_rule 34,3 | 22,533 | 10,836 | 916,5 | 2031-08-07 | 1.642,0 | 2035-07-29 |
| (iii) 5-min sub | LEG_S1 | c_consensus_measured 27,2 | 22,533 | 10,836 | 726,4 | 2030-07-23 | 1.301,4 | 2033-09-15 |
| (iii) 5-min sub | Konjunktion BTC+ETH | c_rule | - | - | 1.097,1 | 2032-08-03 | - | - |
| (iii) 5-min sub | Konjunktion BTC+ETH | c_consensus_measured | - | - | 882,4 | 2031-05-31 | - | - |
| (iv) 15-min | BTC_S3 | c_rule 26,3 | 0,293 | 0,143 | 681,7 | 2030-04-24 | 1.221,2 | 2033-04-08 |
| (iv) 15-min | BTC_S3 | c_consensus_measured 23,8 | 0,293 | 0,143 | 618,0 | 2029-12-17 | 1.107,2 | 2032-08-23 |
| (iv) 15-min | BTC_S2 | c_rule 29,8 | 32,323 | 12,553 | 1.219,8 | 2033-04-04 | 2.185,4 | 2038-07-19 |
| (iv) 15-min | BTC_S2 | c_consensus_measured 24,4 | 32,323 | 12,553 | 999,4 | 2032-01-20 | 1.790,5 | 2036-05-20 |
| (iv) 15-min | ETH_S1 | c_rule 34,1 | 26,956 | 12,203 | 1.029,3 | 2032-03-20 | 1.844,0 | 2036-09-05 |
| (iv) 15-min | ETH_S1 | c_consensus_measured 29,4 | 26,956 | 12,203 | 886,1 | 2031-06-08 | 1.587,5 | 2035-04-10 |
| (iv) 15-min | LEG_S1 | c_rule 32,8 | 22,690 | 10,836 | 888,0 | 2031-06-10 | 1.590,9 | 2035-04-16 |
| (iv) 15-min | LEG_S1 | c_consensus_measured 28,4 | 22,690 | 10,836 | 769,2 | 2030-10-17 | 1.378,1 | 2034-02-16 |
| (iv) 15-min | Konjunktion BTC+ETH | c_rule | - | - | 1.029,3 | 2032-03-20 | - | - |
| (iv) 15-min | Konjunktion BTC+ETH | c_consensus_measured | - | - | 886,1 | 2031-06-08 | - | - |
| (v) 30-min | BTC_S3 | c_rule 27,6 | 0,270 | 0,143 | 606,8 | 2029-11-25 | 1.087,2 | 2032-07-14 |
| (v) 30-min | BTC_S3 | c_consensus_measured 21,4 | 0,270 | 0,143 | 471,3 | 2029-02-28 | 844,3 | 2031-03-16 |
| (v) 30-min | BTC_S2 | c_rule 29,6 | 28,688 | 12,553 | 955,2 | 2031-10-24 | 1.711,2 | 2035-12-14 |
| (v) 30-min | BTC_S2 | c_consensus_measured 24,2 | 28,688 | 12,553 | 780,6 | 2030-11-08 | 1.398,5 | 2034-03-28 |
| (v) 30-min | ETH_S1 | c_rule 34,3 | 24,352 | 12,203 | 844,7 | 2031-03-16 | 1.513,4 | 2034-11-13 |
| (v) 30-min | ETH_S1 | c_consensus_measured 28,5 | 24,352 | 12,203 | 700,5 | 2030-06-01 | 1.255,0 | 2033-06-13 |
| (v) 30-min | LEG_S1 | c_rule 33,0 | 20,560 | 10,836 | 734,2 | 2030-08-08 | 1.315,3 | 2033-10-13 |
| (v) 30-min | LEG_S1 | c_consensus_measured 26,6 | 20,560 | 10,836 | 591,3 | 2029-10-26 | 1.059,3 | 2032-05-19 |
| (v) 30-min | Konjunktion BTC+ETH | c_rule | - | - | 844,7 | 2031-03-16 | - | - |
| (v) 30-min | Konjunktion BTC+ETH | c_consensus_measured | - | - | 700,5 | 2030-06-01 | - | - |
| (vi) cc | BTC_S3 | c_rule 25,9 | 0,304 | 0,143 | 723,7 | 2030-07-17 | 1.296,6 | 2033-09-05 |
| (vi) cc | BTC_S3 | c_consensus_measured 14,9 | 0,304 | 0,143 | 460,6 | 2029-02-06 | 825,1 | 2031-02-06 |
| (vi) cc | BTC_S2 | c_rule 29,4 | 27,261 | 12,553 | 858,3 | 2031-04-13 | 1.537,7 | 2034-12-31 |
| (vi) cc | BTC_S2 | c_consensus_measured 23,6 | 27,261 | 12,553 | 689,4 | 2030-05-10 | 1.235,0 | 2033-05-06 |
| (vi) cc | ETH_S1 | c_rule 27,6 | 25,104 | 12,203 | 723,3 | 2030-07-17 | 1.295,8 | 2033-09-03 |
| (vi) cc | ETH_S1 | c_consensus_measured 20,9 | 25,104 | 12,203 | 547,3 | 2029-07-30 | 980,5 | 2031-12-13 |
| (vi) cc | LEG_S1 | c_rule 27,9 | 20,926 | 10,836 | 643,4 | 2030-02-07 | 1.152,6 | 2032-11-21 |
| (vi) cc | LEG_S1 | c_consensus_measured 20,1 | 20,926 | 10,836 | 462,5 | 2029-02-10 | 828,6 | 2031-02-12 |
| (vi) cc | Konjunktion BTC+ETH | c_rule | - | - | 723,3 | 2030-07-17 | - | - |
| (vi) cc | Konjunktion BTC+ETH | c_consensus_measured | - | - | 547,3 | 2029-07-30 | - | - |
