# Review A2-Vorarbeit: Placebo-Design bei taeglichen Verfaellen und sigma30-Nuisance (adversarisch)

> Rolle: adversarischer Reviewer (Gate-Auditor, Richtung Strenge), Stand 2026-10-29. Nichts registriert, kein Verdikt,
> nichts committet. **Etikett:** Dieses Review gibt kein Mittel, keinen Median und kein Vorzeichen irgendeiner
> Verfallstag-Rendite (r_pre, r_post, Differenz Ereignis minus Placebo) aus; nachgerechnet wurden nur Streuung,
> Korrelation, Autokorrelation, Varianzfaktor, Zaehlungen und Summen gelieferter Kontrakte. Renditen nur
> 2021-03-24..2024-05-31, Kalender/OI nur bis 2026-06-30, keine Siegeldatei, kein Harvest-Client.
> **Gegenstand:** `state/herleitung_a2/` PLACEBO_DESIGN_A2.md (sha256 332fc3fe...), NUISANCE_SIGMA30.md (ca31718f...),
> ENTSCHEIDUNGSVORLAGEN.md (e4118e31...), a2_vorarbeit.json (**2bd1ad7e7118cc4018a3fab077f999673db6785222dbedbf77b173447367d30a**,
> geprueft), Skripte `scratchpad/a2_vorarbeit/` (run_all.sh, a2v_common.py, a2v_oi.py, a2v_sigma30.py, a2v_power.py,
> a2v_build.py). Auftrag `scratchpad/SPEC_A2_vorarbeit.md`. Massstab: PRD 5.2, PROGRAMM_BILANZ 2.4, DEC-94, DEC-96 E3,
> DEC-98 Nachtrag 5, DEC-67 E4, DEC-99 (8), `power_p1.py`. Die waehrend des Reviews entstandene
> `NACHRECHNUNG_ORCHESTRATOR.md` wurde nicht gelesen (Unabhaengigkeit).
> **Kuerzel:** `[R:<skript>]` = Review-Skript unter `scratchpad/a2_review/`; `[aj:<pfad>]` = a2_vorarbeit.json; Zahlen in bp.

## 0. Urteil

**ZUSTIMMUNG MIT AUFLAGEN.** Kein VETO.

- **Siegel-Treue haelt** (Pruefpunkt 1 zuerst): kein Mittel, kein Median, kein Vorzeichen einer Verfallstag-Rendite
  in JSON, MD, Zwischen-Dateien oder Logs (Skripte drucken nur sha256); Renditen nur bis 2024-05-31 (unabhaengig per
  Assert auf `start_ms` vor jedem Preis nachgeprueft); Settlement-Preisfelder nie dekodiert. Drei Schwaechen der
  Waechter-/Doku-Ebene (B-1..B-3), keine davon ein Bruch.
- **Alle nachgerechneten Zahlen stimmen exakt:** 203 Streuungs-/rho-/ACF-/c-Groessen mit eigenem Code bis 3,7e-16
  relativ; N je Fenster, OI-Summen und -Verhaeltnisse, Zeitlage, SE(Kontrast), MDE80, Bilanz-Reproduktion identisch;
  dritter Lauf der Agenten-Skripte bitgleich (sha256 2bd1ad7e...). Keine Abweichung > 1 %.
- **Inhaltliche Auflagen** betreffen das Design, nicht die Zahlen: (B-5) die MDE80 je Design gilt fuer den bindenden
  Einzel-Placebo, nicht fuer die vom Gate verlangte Konjunktion "gegen alle Placebos" (D_i: 18,25 -> 19,8 bp gemeinsam,
  21,9 bp als Produkt-Untergrenze); (B-6) die PRD-Null "Zufallstermine mit identischer Kalenderverteilung" ist unter
  taeglichen Verfaellen nicht mehr definiert; (B-7) taegliche Deribit-**Futures**-Verfaelle ab 2026-04-04 veraendern P2'
  im letzten Viertel von W2 (48 von 207 Mo-Do-Tagen) - im Placebo-Design nicht erwaehnt; (B-8..B-9) fehlende
  Kontaminationen/Varianten (CME-Referenzfenster vor 16:00 UTC am Monatsende, historische verfallsfreie Baseline,
  Differenz-in-Differenzen).

## 1. Pruefpunkte (Status, Beleg, Richtung)

| Nr. | Pruefpunkt | Status | Beleg | Richtung |
|---|---|---|---|---|
| 1 | Siegel-Treue | **BESTAETIGT** (mit B-1..B-4, gering) | Schluessel-Scan aller vier JSON (334 / 96 / 137 / 125 Schluessel): keine mean/median/sign/effect/delta-Schluessel; einzige Treffer "total" = OI-Summen [R:keyscan.py]. Pfad-Scan: unter `dispersion` nur n, sd, 1,4826 x MAD, Kurtosis, Betrags-Quantile; kein vorzeichenbehaftetes Quantil [R:pathscan.py]. Skripte: `.mean(`/`np.median`/`nanmean`/`np.sum(..)/len` nur intern (Zentrierung SD/Kurtosis/ACF, MAD-Zentrum, Wochen-/Monatsaggregate fuer eine Korrelation, Batch-Means, P3-Tagesstatistik), nie ausgegeben; `print` nur sha256. Kline-Extrakt endet 2024-05-31 (eigener Assert auf `start_ms` vor jedem Preis) [R:rv_sigma.py]. Settlement-Rohdaten: einzige Spalte `payload_json`; nur Regex-Extraktion von type/instrument_name/timestamp/position, nie JSON-dekodiert; Partitionen > 2026-06-30 vor dem Oeffnen verworfen (Code gelesen). Zugriffszeiten: Funding-Extrakt, DVOL, deliveryPrices heute nicht gelesen; die heutige Lesung der Tageskerzen (15:57:41) gehoert zum Umsatz-Zensus (Skript 15:57:35, vor dem A2-Auftrag 16:00:14), nicht zur A2-Vorarbeit. Siegeldateien zuletzt 2026-10-12 gelesen. | - |
| 2 | r_pre-Konvention, Zeitlage | **BESTAETIGT** | r_pre = ln(C[07:59]/C[07:29]) = Kerzen-Index 479/449 auf UTC-`start_ms` (Kerzenbeginn); deckt [07:30:00, 08:00:00) und damit das TWAP-Fenster (BELEGE_AUS_PDF 6: 07:30-08:00 UTC, 4-s-Takt). Delivery-Zeitstempel nachgerechnet: 167.076 Options-Deliveries 2020-03-25..2026-06-30, Median 0,038 s, q99 0,443 s nach 08:00:00, keine davor, > 60 s nur an 2020-08-27 und 2024-08-19; Vorperiode max 0,3 s [R:rv_timing.py]. cc gegen oc: Korrelation Cluster 0,9999995 (identisch) | neutral |
| 3 | Ereignisgroesse/OI | **BESTAETIGT** mit B-7 | Eigene Extraktion (eigene Regexe, Positivliste): q50-Verhaeltnisse Freitag/Mo-Do BTC/ETH 12,762 / 13,466 (Vorperiode), 9,688 / 7,614 (W1), 9,090 / 6,319 (W2 bis 06-28); Monat+Quartal/Woche 3,378 / 3,690, 3,523 / 3,195, 3,811 / 3,419 - alle exakt; 0 Duplikate, keine Options-Namen ausserhalb des Musters BTC/ETH-DDMMMYY-K-C/P; Freitag-Minimum je Woche 4,56 / 3,42 (2021-03-24..2026-06-28) [R:rv_oi.py]. Optionen und Futures getrennt (Futures verworfen), Klassenregel = DEC-98 N5 (letzter Freitag, Quartal Mrz/Jun/Sep/Dez, ohne Feiertagsverschiebung). **Nicht berichtet:** Futures-Kalender (taeglich ab 2026-04-04, B-7); Einheit von `position` ohne Fundstelle (B-10) | Futures-Ausschluss unterschaetzt die Freitagsgroesse -> Abschwaechungsfaktor eher zu klein (Strenge) |
| 4 | Placebo-Design | **ABWEICHUNG** (B-5..B-9) | A-1-Analyse (taeglicher Verfall, Funding 08:00, Wochenende) inhaltlich richtig, Richtungen fuer D_i/PRD_a/D_i_s/D_i_W ausgewiesen, fuer D_ii/PRD_b nicht ("-"). Ereignis- und Placebomengen sind Kalenderklassen und damit PIT-fixierbar; D_i stammt aus dem Auftrag (A-2 (i)), keine Wahl nach Sehen; die testbarere Alternative PRD_a wurde verworfen (Strenge). Fehlend: Konjunktions-Power (B-5), Null-Definition (B-6), Futures-Tagesverfall in W2 (B-7), CME-Fenster (B-8), historische Baseline und DiD (B-9) | Agentenzahlen lehnen in Richtung Testbarkeit (B-5) |
| 5 | sigma30/rho/c | **BESTAETIGT** | 203 Groessen exakt (Abschnitt 3); Bartlett eigene Implementierung = `power_p1.variance_factor`; Bootstrap-Baender mit fremdem Seed (4711) und mit Monats- statt Wochenbloecken vertraeglich [R:rv_sigma.py, R:rv_band.py] | - |
| 6 | SE(Delta)/MDE80/Power | **BESTAETIGT** mit B-5/B-6 | Formel-Herleitung 6.1 korrekt (Schranke rho (s_B - s_E)^2/4 nachgerechnet; Kovarianzterm = r_w SE_E SE_P bei gleichen Wochenzaehlungen, keine Gutschrift); N je Fenster unabhaengig gezaehlt (W1 52/40/12/208/312/364, W2 bis 2026-06-28 52/40/12/207/311/363; Ausreisser 2024-08-19); `power_p1.mde80`/`window_power`/`assign_regime` benutzt; Prior-Gitter 5/8/12/16,5/25 wie Auftrag; Bilanz 5,133 / 11,277 reproduziert; keine verdeckte Zuordnung ("GL-012-Kandidat" wie im Auftrag erlaubt, D_ii "nicht tragfaehig" = PRD 5.2-Befund) | B-5: Testbarkeit |
| 7 | Vollstaendigkeit/Belege | **BESTAETIGT** mit B-10/B-11 | UNBELEGT benannt: V-5b, OI-Proportionalitaet, Funding-Intervall W2, 6 s -> 4 s, Fensterlage/Reihenfolge; Gabelungen G-1..G-5 / EV-A..EV-I mit Richtung; deterministisch (4 Agentenlaeufe + 1 Reviewlauf bitgleich). Luecken: Einheit von `position`, PRD-5.2-Fenstertext, C.17-Inventur W1/W2 (B-10, B-11) | - |

## 2. Befunde

| Nr. | Schwere | Befund | Richtung | Auflage |
|---|---|---|---|---|
| **B-1** | gering | **"Nicht berechnet" ist falsch, richtig ist "intern berechnet, nie ausgegeben".** NUISANCE_SIGMA30 Abschnitt 8 sagt "Nicht berechnet ... Mittel, Median oder Vorzeichen irgendeiner Slot-Rendite"; der Kopf derselben Datei und der Code sagen zutreffend "nur intern": `describe()` bildet Median (MAD-Zentrum, a2v_sigma30.py Z. 71) und Mittel (Z. 73) je Klasse/Jahr, `agg_corr()` bildet Klassen-Mittel je ISO-Woche/Monat (Z. 317-318, als `np.sum/len`), Batch-Means, `stationary_bootstrap_se` Replikat-Mittel. Nichts davon wird gespeichert, gedruckt oder geloggt (geprueft). Fuer SD/MAD/ACF unvermeidlich und vom Auftrag (MAD, ACF, Korrelation) gedeckt | - | Satz in Abschnitt 8 korrigieren |
| **B-2** | gering | **Waechter nur namensbasiert und lueckenhaft.** `guard_keys` laesst `median`, `r_pre_median`, `q50`, `loc`, `center`, `diff`, `contrast_bp`, `event_minus_placebo` passieren [R:guardtest.py]; `no_mean` (h27) kennt nur Praemien-Schluessel. Die eigentliche Sperre ist die Struktur von `describe()` (nur Betrags-Quantile) - per Pfad-Scan bestaetigt. Zusaetzlich: `load_kline` liest den ganzen Extrakt vor dem Datums-Assert (hier folgenlos, der Extrakt endet 2024-05-31) | Strenge bei Wiederverwendung | Guard um median/q50/loc/center/diff/contrast erweitern; Assert auf `start_ms` vor dem Lesen der Preisspalten |
| **B-3** | gering | **Schwacher, vorzeichenfreier Lage-Kanal.** Je Klasse, Jahr und Serie werden **unzentrierte** Betrags-Quantile (abs_q50) neben dem **median-zentrierten** 1,4826 x MAD ausgegeben - auch fuer die gepaarte Differenz r_pre - r[15:30] (eine Ereignis-minus-Placebo-Reihe) und fuer r_post. Aus beiden laesst sich unter Symmetrie ein verrauschter Betrag der Lage ableiten (kein Vorzeichen). Vom Auftrag (Betrags-Quantile und MAD erlaubt) gedeckt; vom Reviewer bewusst **nicht** ausgerechnet | Ergebnisblindheit | C.17-Register: "Betrags-Quantile und MAD je Klasse/Jahr gesehen"; kuenftig fuer Differenz-Reihen nur zentrierte Quantile |r - Zentrum| oder keine Betrags-Quantile |
| **B-4** | Hinweis | Preisfelder der Settlements stehen als **unge-parste Bytes** kurzzeitig im Arrow-Puffer (`payload_json` ist die einzige Datenspalte, Schema geprueft). Mit dem Auftragswortlaut "Feldfilter beim Parsen" vereinbar; kein Preis wurde Wertobjekt | - | keine |
| **B-5** | **mittel** | **Konjunktions-Power fehlt.** PRD 5.2 Gate (2) verlangt Signifikanz gegen **alle** Placebos gleichzeitig; die Vorarbeit weist MDE80/Power des bindenden Einzel-Placebos aus (DEC-94 (3) woertlich "max ueber Bedingungen"). Bei D_i liegen die drei Kontraste dicht beieinander (SE 7,34 / 7,18 / 6,53) und teilen den Ereignis-Term (Korrelation ~0,8..0,9), die gemeinsame Power ist deutlich kleiner [R:rv_power.py, Monte Carlo, Kovarianz = SE_E^2; Kreuzterme aus den gemessenen Same-Day-Korrelationen auf < 2 % abgeschaetzt]: bei 16,5 bp Einzel 0,727 / gemeinsam 0,645 / Produkt 0,438; bei 18,25 bp 0,800 / 0,733 / 0,570. MDE80 (Ereignis-Skala, P-1): Einzel 18,25, **gemeinsam 19,8**, Produkt-Untergrenze 21,9; mit OI-Abschwaechung 0,842 auf P2': 21,7 / 22,2 / 23,8. Jeder zusaetzliche Placebo kostet Power (zwei Placebos {P2', P3fix}: 0,739 bei 18,25) - die Groesse des Placebosatzes ist eine Gabelung | Agentenzahlen: Testbarkeit | Konjunktions-Power und Produkt-Untergrenze als Doppelausweis; im DEC-Nachtrag festlegen, welche Zeile die Zuordnung traegt (analog DEC-94 (6) Produktregel = Strenge); Placebosatz vor jeder weiteren Zahl fixieren |
| **B-6** | **mittel** | **Struktureller Nulleffekt nicht mehr definiert.** PRD 5.2: Null = Pipeline auf "Zufallsterminen mit identischer Kalenderverteilung (gleiche Anzahl, Wochentags-, Tageszeit- und Cluster-Struktur)"; zugleich Schwelle = max(95-%-Quantil der Placebo-Verteilung; z SE) und DEC-94 (5) (ii) kalibrierte Null-Simulation. Wenn jeder Tag Verfallstag ist, zieht eine wochentagstreue Null genau die Freitage (die Ereignisse) - die Null ist leer bzw. identisch mit dem Ereignis. EV-H 4 fuehrt die Null nur als "nicht gebaut" | Strenge (ohne Null keine bindende SE nach DEC-94 (5)) | Null fuer den Groessen-Kontrast neu fassen, vor jeder Zahl: z. B. Permutation der Klassenlabels Freitag <-> Mo-Do innerhalb derselben ISO-Woche, oder Slot-Verschiebung bei festen Tagen; Etikett "Null neu definiert nach DEC-98 N5" |
| **B-7** | gering bis mittel | **Taegliche Futures-Verfaelle ab 2026-04-04 nicht erfasst.** Kalender-Extrakt: Futures-Deliveries ausserhalb von Freitagen erstmals 2026-04-04 (BTC und ETH), 134 bis 2026-06-30; in W2 (bis 06-28) tragen 48 von 207 Mo-Do-Tagen eine Futures-Delivery (36 beide Waehrungen), in W1 keiner [R:rv_fut.py]. P2' ist damit **zwischen W1 und W2 nicht homogen** (Kill-Bedingung (3) Vorzeichenwechsel und REZENZ betroffen). Ausserdem tragen Freitage seit 2021 Wochen-Futures-Verfaelle, die in der OI-Groesse fehlen. Die Vorarbeit sagt nur "Futures-Deliveries werden nicht verwendet" | Placebo bekommt Teil des Ereignismechanismus -> Kontrast kleiner (Strenge), aber Fensterinhomogenitaet | Klassenregel um Futures-Kalender ergaenzen (Bericht: Futures-Deliveries je Klasse und Fenster); Gabelung "P2' ohne Mo-Do-Tage mit Futures-Verfall" (N_P 159 in W2, Richtung Testbarkeit der Reinheit/Strenge der SE) vor jeder Zahl festlegen |
| **B-8** | gering, UNBELEGT | **CME-Referenzfenster fehlt in der P3-Kontaminationsliste.** Nach Kenntnisstand des Reviewers [in der Akte UNBELEGT] settlen CME-BTC/ETH-Futures am letzten Freitag des Monats auf eine Referenzrate aus der Stunde vor 16:00 London; in GMT-Monaten ist das [15:00, 16:00) UTC und ueberdeckt P3fix [15:30, 16:00) und den gepaarten Freitags-Slot von D_i_s an Monatsend-Freitagen. Die Aussage "keine Options-TWAP ausserhalb [07:30, 08:00)" gilt nur fuer Deribit | P3fix/P3'-Fri an Monatsfreitagen kontaminiert (Richtung offen) | Primaerbeleg holen, bevor ein 15:30-Slot als Placebo/Paarung fixiert wird; sonst Paarungs-Slot ohne fremdes Referenzfenster (G-1) |
| **B-9** | gering | **Naheliegende Varianten nicht genannt.** (a) **Historische verfallsfreie Baseline** (07:30-08:00 an Tagen ohne jeden Verfall vor 2020-02): auf den Programm-Instrumenten nicht bildbar - BTCUSDT-1-min erst ab 2020-03-25, also nach Beginn der BTC-Tagesverfaelle 2020-02-04, ETHUSDT ab 2021-03-15 (DEC-98 N4 (d), N5); nur ueber ein anderes Instrument (inverse Perps, Index), Verfuegbarkeit UNBELEGT; Aera mit kleinem Options-OI; nach DEC-99 nur als vorab registriertes Pilot-/Zusatzfenster -> hoechstens Aera-Bericht "Verfall gegen kein Verfall". (b) **Differenz-in-Differenzen** (Fr r_pre - Fr r[15:30]) - (Mo-Do r_pre - Mo-Do r[15:30]): kontrolliert Wochentags- und Tageszeit-Haupteffekt zugleich, laesst nur die Freitag-x-07:30-Interaktion; SD der gepaarten Differenz Mo-Do 73,3 (c 1,36), Freitag 76,7 (c 1,10) -> SE 12,6, MDE80 31,4 bp je Fenster [R:rv_did.py]. D_i_s kontrolliert nur den Wochentag, nicht den Tageszeit-Effekt. (c) Negativ-Panel XRP/BNB (Gate (4)) traegt Beta-Spillover aus BTC/ETH; ohne Residualisierung kann es einen echten Verfallseffekt als "Wochentags-Artefakt" toeten | (a) Strenge, nicht gate-faehig; (b) Strenge (Identifikation) gegen D_i/D_i_s; (c) Strenge falsch-negativ | in ENTSCHEIDUNGSVORLAGEN als Gabelungen mit Richtung nachtragen; (c) als Merkposten fuer die Gate-Bedingung (4) |
| **B-10** | gering | Belege/Redaktion: Einheit von `position` ("Coin-Einheiten, 1 Kontrakt = 1 BTC/ETH") ohne Fundstelle -> UNBELEGT (Verhaeltnisse je Waehrung unberuehrt); Richtung fuer D_ii/PRD_b fehlt; PRD-5.2-Fenstertext (W1 2024-09..2025-08, W2 2025-09..2026-08) wird stillschweigend durch DEC-99 (8) ersetzt - Verweis fehlt; Rundungen uneinheitlich (D_i MDE80 18,2 / 18,3, Stress-SE 9,87 / 9,88, D_i_W 20,0 / 20,1 = W1 / W2); "[15:30]/[07:30] = 1,30" ist ALL-15:30 gegen MODO-07:30 | - | korrigieren / UNBELEGT markieren |
| **B-11** | gering | **C.17-Inventur W1/W2 nur behauptet.** "Fenster blind fuer A2 (kein r_pre-Mittel je gerechnet)" belegt nur diese Herleitung. Programmweit beruehren 2.0-Laeufe mit Daten ab 2026-03-27 die 08:00-Slots in W2 (H-01 "S3 Pre-Settlement", ~24-h-Replay; Registry 2.0), vernachlaessigbar, aber zu fuehren; Weiss et al. (2021-2023) liegt vor W1 | - | eine Inventurzeile im DEC-Nachtrag |
| **B-12** | Hinweis | Vorperiode = anderes Vol-Regime (Faktor 2,3); Stress = 2021-Klassen-SD; W1/W2-Streuung ungemessen (Auftragsgrenze) - korrekt etikettiert. Kurtosis 5..10 bei N 12 (D_ii) macht die Normal-Naeherung fraglich - etikettiert | - | keine |

## 3. Nachrechnungstabelle (eigener Code, nur Streuung/Zaehlung)

Eigene Implementierung ohne Import der Agentenmodule ausser `power_p1` [R:rv_sigma.py, R:rv_power.py, R:rv_oi.py];
Vergleich [R:cmp_sigma.py]. Kline: je 1.677.600 Zeilen, 1.165 vollstaendige Tage 2021-03-24..2024-05-31, 0 doppelte Minuten.

| Groesse (r_pre [07:30, 08:00), 2021-03-24..2024-05-31) | Review | Herleitung | Abweichung |
|---|---|---|---|
| n FRI / FRI_W / FRI_MQ / MODO / WE / ALL | 167 / 128 / 39 / 666 / 332 / 1.165 | gleich | 0 |
| SD BTC / ETH / gepoolt / Cluster, FRI | 40,195 / 52,608 / 46,815 / 43,830 | gleich | < 1e-15 |
| dto. MODO | 39,460 / 48,830 / 44,392 / 42,453 | gleich | < 1e-15 |
| dto. WE | 31,637 / 40,696 / 36,449 / 34,846 | gleich | < 1e-15 |
| dto. FRI_W | 37,847 / 48,916 / 43,733 / 41,083 | gleich | < 1e-15 |
| dto. FRI_MQ | 47,565 / 63,874 / 56,313 / 52,448 | gleich | < 1e-15 |
| dto. ALL | 37,480 / 47,227 / 42,633 / 40,617 | gleich | < 1e-15 |
| Cluster-SD je Jahr FRI 2021 / 2022 / 2023 / 2024 | 58,69 / 42,84 / 35,16 / 26,07 | gleich | 0 |
| rho Pearson FRI / MODO / FRI_MQ / ALL; Spearman FRI | 0,7805 / 0,8480 / 0,7671 / 0,8372; 0,7694 | gleich | 0 |
| c Bartlett 4/8/13 (eigene = `power_p1`), FRI | 1,149 / 1,047 / 0,933 | gleich | < 4e-16 |
| c_bind FRI / FRI_W / FRI_MQ / MODO / WE, NONFRI, ALL | 1,149 / 1,269 / 1,459 / 1,318 / 1,000 | gleich | < 2e-16 |
| SD Cluster [15:30, 16:00) ALL; P3-Baseline ALL; gepaarte Differenz FRI | 55,21 (c 1,094); 7,73 (c 1,123); 76,67 (c 1,099) | gleich | 0 |
| SD-Verhaeltnis gepoolt FRI/MODO [95-%-Band] | 1,055 [0,857; 1,277] (Seed 4711); Monatsbloecke [0,853; 1,289] | 1,055 [0,849; 1,301] | Band vertraeglich |
| dto. FRI_MQ/FRI_W; WE/MODO | 1,288 [0,902; 1,763]; 0,821 [0,682; 0,982] | [0,901; 1,779]; [0,689; 0,975] | vertraeglich |
| N W1 (FRI/FRI_W/FRI_MQ/MODO/NONFRI/ALL) | 52 / 40 / 12 / 208 / 312 / 364 | gleich | 0 |
| N W2 bis 2026-06-28 | 52 / 40 / 12 / 207 / 311 / 363 | gleich | 0 |
| SE(Kontrast) / MDE80 P-1 / A3 je Fenster, D_i (W1) | 7,340 / 18,25 / 24,43 | 7,34 / 18,25 / 24,43 | 0 |
| PRD_a; D_ii; D_i_W; D_i_s (SE / MDE80 P-1) | 6,899 / 17,15; 19,698 / 48,98; 8,060 / 20,04; 11,146 / 27,72 | gleich | 0 |
| Bilanz-Reproduktion SE woechentlich / monatlich, MDE80 | 5,133 / 11,277; 12,76 / 28,04 | gleich | 0 |
| OI q50 Freitag/Mo-Do BTC/ETH Vorperiode, W1, W2 | 12,762 / 13,466; 9,688 / 7,614; 9,090 / 6,319 | gleich | 0 |
| OI q50 Monat+Quartal / Woche (dto.) | 3,378 / 3,690; 3,523 / 3,195; 3,811 / 3,419 | gleich | 0 |
| Delivery-Zeitlage q50 / q99 / > 60 s (2020-03-25..2026-06-30) | 0,038 s / 0,443 s / 84 an 2 Tagen | gleich | 0 |
| **Neu:** gemeinsame Power D_i bei 16,5 / 18,25 / 25 bp (P-1) | 0,645 / 0,733 / 0,944 | (Einzel 0,727 / 0,800 / 0,961) | B-5 |
| **Neu:** MDE80 D_i gemeinsam / Produkt (Ereignis-Skala; abg. 0,842) | 19,8 / 21,9 (22,2 / 23,8) | 18,25 (21,7) | +8 % / +20 % |
| **Neu:** DiD SE / MDE80 P-1 je Fenster | 12,62 / 31,4 | - | B-9 |

Hoechste relative Abweichung ueber 203 verglichene Groessen: 3,7e-16. Determinismus: Agenten-Skripte erneut
ausgefuehrt, `work/*.json` und `a2_vorarbeit.json` (Ausgabe umgelenkt) bitgleich zu den Akten-Hashes.

## 4. Auflagen vor einem DEC-Nachtrag

1. **A-1 (B-5):** Konjunktions-Power und Produkt-Untergrenze je Design als Doppelausweis; der DEC-Nachtrag legt fest,
   welche Zeile die Zuordnung (C10/DEC52/GL012) traegt. Der Placebosatz (welche und wie viele Placebos) wird vor jeder
   weiteren Zahl fixiert, mit Richtung.
2. **A-2 (B-6):** Null-Simulation/Placebo-Verteilung fuer den Groessen-Kontrast neu definieren (Vorschlag:
   Label-Permutation Freitag <-> Mo-Do innerhalb der ISO-Woche), bevor eine Schwelle "max(95-%-Quantil; z SE)" registriert wird.
3. **A-3 (B-7):** Futures-Kalender in die Klassenregel und das Kontaminationsregister (taeglich ab 2026-04-04; 48/207
   W2-Mo-Do-Tage); Gabelung "P2' ohne Futures-Tage" mit Richtung vorab festlegen.
4. **A-4 (B-8):** CME-Referenzfenster primaer belegen oder den 15:30-Slot nicht als Paarungs-/Fix-Slot an Monatsfreitagen verwenden.
5. **A-5 (B-9):** Gabelungen nachtragen: DiD (Strenge, MDE80 31,4), historische Baseline (nur Aera-Bericht, Daten UNBELEGT),
   Beta-Residualisierung des Negativ-Panels.
6. **A-6 (B-1..B-3, B-10, B-11):** Abschnitt-8-Satz korrigieren; Guard erweitern; C.17-Zeile fuer Betrags-Quantile/MAD;
   `position`-Einheit UNBELEGT; Richtung D_ii; Verweis PRD-5.2-Fenster -> DEC-99 (8); Rundungen vereinheitlichen;
   C.17-Inventur W1/W2 (2.0 H-01) als eine Zeile.

Nicht blockierend fuer die Annahme der Vorarbeit als Nuisance-Akte; blockierend nur fuer eine A2-Registrierung, die
ohnehin durch V-5b gesperrt bleibt.

## 5. Was NICHT folgt

- Kein Urteil ueber einen Verfallseffekt; keine Effektgroesse, kein Vorzeichen (V-5b bleibt UNBELEGT, A2 bleibt gesperrt).
- Keine Wahl eines Designs: "D_i empfohlen" ist eine Vorlage; B-5/B-7 koennen die Reihenfolge D_i / D_i_W / DiD verschieben.
- Die Feasibility-Schwellen (Kontrast ~18,3 bp, Ereignis ~21,7 bp) sind Einzel-Placebo-Werte; mit Konjunktion ~19,8 /
  ~22,2 bp, als Produkt-Untergrenze ~21,9 / ~23,8 bp - keine davon ist ein Prior.
- Die exakte Reproduktion bestaetigt Rechnung und Siegel, nicht die Uebertragbarkeit der Vorperioden-Streuung auf W1/W2.
- Keine Regelaenderung; DEC-94 (3) wird nicht umgedeutet, B-5 ist eine Auslegungsfrage fuer den Orchestrator.

## 6. Reproduktion

Skripte `scratchpad/a2_review/`: `rv_sigma.py` (Streuung/rho/ACF/c, eigener Lader mit Assert vor jedem Preis, Seed
4711), `cmp_sigma.py` (Vergleich), `rv_power.py` (N, SE, MDE80, Konjunktions-Power, MC-Seed 11), `rv_oi.py` (OI aus den
Rohpartitionen <= 2026-06-30, Positivliste), `rv_fut.py` (Futures-Kalender), `rv_timing.py` (Zeitlage), `rv_did.py`
(DiD-Streuung), `rv_band.py` (Blockwahl), `keyscan.py` / `pathscan.py` / `guardtest.py` (Siegel-Scans); Laufzeit
zusammen < 1 min. sha256: rv_sigma.json e7b85dd0..., rv_power.json ea034145..., rv_oi.json 8e2e6b80...; Replay der
Agentenlaeufe unter `scratchpad/a2_review/replay/`.
