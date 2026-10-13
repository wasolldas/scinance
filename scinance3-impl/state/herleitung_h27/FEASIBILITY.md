# H-27 (VRP auf DVOL-Backfill) - Stufe 1: Feasibility (C.12) - STAND: WARTET AUF DATEN

> ENTWURF der Herleitung, Stand 2026-10-13. Nichts hier ist registriert oder beschlossen; entscheiden und registrieren
> darf nur der Orchestrator. Keine RV ab 2024-06-01, keine DVOL-Niveau-Statistik ab 2024-07-01, kein Praemienmittel
> berechnet; keine Siegeldatei, keine WP-10(A2)-/WP-10(A)-IV-RV-Datei, kein Inhalt der WP-9-Differenzserie geoeffnet.
> Kuerzel: `[fj]` = `feasibility.json` (gleicher Ordner); `[S:<datei>]` = Skript unter `scratchpad/h27_herleitung/`;
> `[sek]` = Sekundaerbeleg; `[abg.]` = hier abgeleitet; UNBELEGT = keine Fundstelle, blockiert.

## 0. Befund in Kuerze

1. **Abdeckungspruefung (einmal, `hd.catalog(refresh=True)`):** Der Katalog ist weiterhin der Export vom
   2026-10-12 10:50 UTC; `deribit/dvol` BTC/ETH beginnt am **2025-08-01** -> der Backfill 2021-03-24..2025-07-31 ist
   **noch nicht sichtbar**. Laut Auftrag: **Stopp, "wartet auf Daten".** Datenprobe (Teil B) und Feasibility-Rechnung
   sind nicht ausgefuehrt; dieses Dokument enthaelt den datenunabhaengigen Teil und die VOR jeder Nuisance-Zahl
   fixierten Rechenregeln (Abschnitt 3), damit die Fortsetzung keine Ermessensspielraeume mehr hat.
2. **Neuer, blockierender Datenbefund (nur Katalog):** Der bestehende Strom ab 2025-08-01 hat eine zusammenhaengende
   Luecke **2025-09-01..2026-03-19 (200 Tage, BTC und ETH)**, dazu 2026-08-02..03 und 2026-09-20. Im Urteilsfenster W2
   (2025-07-01..2026-06-30) waeren nach dem angekuendigten Backfill (endet 2025-07-31) nur **165 von 365 Tagen**
   abgedeckt (Juli 2025 aus dem Backfill, August 2025, 2026-03-20..06-30). Der bestellte Backfill reicht damit fuer W2
   **nicht**. Benoetigt wird zusaetzlich 2025-09-01..2026-03-19 (sinnvoll auch 2026-08-02..03, 2026-09-20) aus derselben
   Schnittstelle - oder Variante A (PC-REST-1D-Dateien, durchgehend 2021-03-24..2026-09-09, DEC-61-geprueft) als die
   EINE Quelle. Siehe `DATENPROBE.md` B.1.
3. **RV-Quelle:** Union-Panel `panel_1d` BTCUSDT/ETHUSDT (Tagesschluesse, 24:00 UTC), lueckenlos 2021-03-24..2026-09-14
   (ETH ab 2021-03-15) [S:panel_coverage.py]; Begruendung `DATENPROBE.md` A.2 (kein kompakter Intraday-Preisstrom im
   Katalog; `bybit/publicTrade` ~183 GB).
4. **Prior [sek]:** BVRP (BTC, Deribit-Optionen 2017-07..2022-12, VIX-Methode) im Mittel **0,14** (annualisierte
   Varianz), S&P 0,02 (Almeida/Grith/Miftachov/Wang 2024) - Stichprobe vor W1, also zulaessig. Umrechnung in
   Vol-/Log-Einheiten braucht eine Niveau-Annahme (UNBELEGT, als Band gefuehrt). ETH: keine Literaturzahl
   (**ETH-Prior UNBELEGT**). Primaertext nicht einsehbar (Egress) - vor einer Registrierung im Original zu pruefen.
5. **Zuordnung (P-1, A3-Praxis): nicht gerechnet** (keine DVOL-Vorperiode). UNBELEGT bleiben: Nuisance-SD, c, Jensen-J.

---

## 1. Was die Fortsetzung braucht (Datenstand)

| Stueck | Stand 2026-10-13 | benoetigt fuer |
|---|---|---|
| `deribit/dvol` 2021-03-24..2025-07-31 | angekuendigt (Data-Harvest), noch nicht im Katalog | Vorperiode (Nuisance), W1 |
| `deribit/dvol` 2025-09-01..2026-03-19 | **Luecke im Strom, nicht bestellt** | W2 |
| `deribit/dvol` 2026-03-20..2026-07-31 | vorhanden | W2 (IV bis 2026-06-30) |
| Panel BTCUSDT/ETHUSDT bis 2026-07-30 | vorhanden (bis 2026-09-14) | RV aller Fenster |

Empfehlung an den Orchestrator (keine Entscheidung des Agenten): die Data-Harvest-Anfrage um 2025-09-01..2026-03-19
(+ 2026-08-02..03, 2026-09-20) erweitern oder Variante A als einzige IV-Quelle waehlen. DEC-61 ("nicht mischen") gilt
fuer beide Wege: entweder durchgehend der stuendliche REST-Abzug (Variante B inkl. Lueckenfuellung) oder durchgehend
die REST-1D-Dateien (Variante A); keine Fensterhaelfte aus der einen, die andere aus der anderen Quelle.

---

## 2. Prior (datenunabhaengig, Literatur vor 2024-07)

| # | Quelle | Stichprobe | Zahl | Einheit | Status |
|---|---|---|---|---|---|
| L-1 | Almeida, Grith, Miftachov, Wang (2024), "Risk Premia in the Bitcoin Market", arXiv 2410.15195 (SSRN-Fassung 2025) | Deribit-BTC-Optionen 2017-07..2022-12, implizite Varianz nach VIX-Methode, Ein-Monats-Horizont | **BVRP im Mittel 14 %** gegen 2 % fuer den S&P (Bollerslev/Tauchen/Zhou 2009); BVRP im Niedrigvol-Regime hoeher, im Hochvol-Regime niedriger (qualitativ) | annualisierte Varianz (0,14), [abg.] aus dem S&P-Vergleich (BTZ-VRP ~0,02 in annualisierter Varianz) | [sek] via Suchmaschinen-Auszug; Volltext nicht erreichbar (Egress); in R1 K-05 zitiert ("BVRP 0,14 gegen ~0,02") |
| L-2 | Deribit Insights / Amberdata, "Decoding Option Flows: Q2, 2023" | DVOL gegen nachfolgend realisierte Vol ("DVOL shifted forward"), BTC; Zeitraum nicht sichtbar, Veroeffentlichung 2023-07 -> vor W1 | **Median-VRP +14 IV-Punkte** | Vol-Punkte, brutto (inkl. Jensen), Median nicht Mittel | [sek], Praktikerquelle; Stichprobe UNBELEGT |
| L-3 | Alexander/Imeraj (2021), J. Altern. Invest. 23(4) 84-109 | Deribit-BVIX 2019-03..2020-03 | kein Mittelwert im Auszug | - | nicht verwendbar |
| L-4 | ETH | - | Praktikernotizen (Amberdata 2021: ETH-IV-Praemie kleiner als BTC; Paradigm: "nearly 25 vol points at times", undatiert) | - | **ETH-Prior UNBELEGT** |
| L-5 | H-26 (2.0) | - | "PASS erwartet ~70/30" | Meinung | keine Effektgroesse |

**Umrechnung L-1 in die Testeinheiten [abg.]** (V = 0,14 = IV^2 - RV^2, RV als Wurzel der mittleren Varianz):

| angenommenes IV-Niveau der L-1-Stichprobe | RV = sqrt(IV^2 - V) | Vol-Praemie IV - RV (netto, ohne Jensen) | Log-Praemie ln(IV/RV) |
|---|---|---|---|
| 0,65 | 0,532 | 11,8 Vol-Punkte | 0,201 |
| **0,75 (zentral)** | **0,650** | **10,0 Vol-Punkte** | **0,143** |
| 0,85 | 0,763 | 8,7 Vol-Punkte | 0,108 |

Das IV-Niveau der L-1-Stichprobe ist **UNBELEGT** (nicht im Auszug); das Band ist eine Annahme. L-2 (Median 14 brutto)
liegt nach Abzug eines Jensen-Terms von einigen Vol-Punkten im oder ueber dem Band (Median > Mittel bei linksschiefer
Praemie) - konsistent, aber nicht unabhaengig belastbar.

**Niveau-Uebertragung (Gabelung, Abschnitt 3 P-7):** Die Praemie in Vol- und Varianzeinheiten haengt vom Vol-Niveau
ab; die Literaturstichprobe (2017-2022) liegt auf einem anderen Niveau als Vorperiode und Fenster. Zwei Lesarten:
(pi-1) konstante Varianzpraemie V = 0,14 in jedem Niveau (L-1: BVRP im Niedrigvol-Regime eher hoeher -> stuetzt
"mindestens konstant") - Richtung **Testbarkeit**; (pi-2) konstante relative Praemie ln(IV/RV) = 0,143 - Richtung
**Strenge**, niveau-konsistent.

**Status des Priors:** in Varianzeinheiten [sek] belegt (eine Zahl, Volltext ungeprueft); in Vol-/Log-Einheiten nur mit
UNBELEGTER Niveau-Annahme (Band); fuer ETH UNBELEGT. Folge fuer die Aggregation: P-6.

---

## 3. Vorab fixierte Rechenregeln (vor jeder Nuisance-Zahl, bindend fuer die Fortsetzung)

Diese Regeln stehen hier, BEVOR irgendeine Praemie, SD oder Autokorrelation berechnet wurde. Abweichungen in der
Fortsetzung nur mit Begruendung und Gabelungs-Richtung.

**P-1 Stichprobe der Vorperiode.** IV-Tage t in [2021-03-24, 2024-05-01], Preise bis 2024-05-31 (Waechter
`h27_common.truncate_prices`, `assert_rv_day`). Fehlende IV- oder Preistage -> P(t) fehlend, gezaehlt, nie gefuellt.
Etikett `h27_common.LABEL` in jeder Ausgabe; Ausgabe-Waechter `no_mean` (kein Praemienmittel, kein DVOL-Mittel der
Vorperiode; RV-Niveaus fuer die Nullwelt sind zulaessig).

**P-2 Statistiken (im Speicher), je BTC, ETH und Bein-Mittel, in S1 (Vol-Punkte), S2 (Varianz x 100), S3 (Log):**
n, SD (ddof 1), Autokorrelation (ACF) Lags 1..180, Korrelation BTC/ETH der Praemie, Kurtosis.

**P-3 Varianzfaktor c der Fenster-Mittel-Statistik (DEC-94 (4)).**
- Taeglich ueberlappend: Bartlett/Newey-West `power_p1.variance_factor` mit Bandbreite B in {30, 60, 90, 120};
  Batch-Means c_BM(L) = L * Var(Blockmittel) / Var(x) mit L in {30, 60, 90, 120} (nicht ueberlappende Bloecke);
  stationaerer Bootstrap (`power_p1.stationary_bootstrap_se`, mittlere Blocklaenge 30/60/90, 2.000 Replikate, Seed 27)
  als Bericht.
- **Bindend:** `c = max(1, max{Bartlett B 60/90/120, BM L 60/90/120})`. Begruendung: die 30-Tage-Ueberlappung allein
  erzeugt eine Dreiecks-ACF bis Lag 29; Bandbreiten unter 60 schneiden echte Persistenz ab (Docstring
  `variance_factor`: kurze Bandbreite unterschaetzt). Obergrenze 120 ~ n/9 begrenzt die Schaetzvarianz. Ist die ACF bei
  Lag 120 noch > 0,10, werden B/L = 180 in die Maximum-Menge aufgenommen (Persistenz ueber die Bandbreite hinaus).
  Richtung: Strenge.
- Monatlich nicht ueberlappend (30-Tage-Bloecke, alle 30 Phasen): SD, ACF Lag 1..3 (Phasenmittel),
  `c_m = max(1, Bartlett B 3, (1 + rho_1)/(1 - rho_1))`.

**P-4 Fenster-SE (Power-Zeile).** `SE_W = SD * sqrt(c / n_W)`; n_W = 335 (IV-Tage t in [Fensterbeginn, Fensterende - 30],
Ziel-Intervall vollstaendig im Fenster, Fenster disjunkt) **bindend**; n_W = 365 (Ziel ragt 30 Tage ins Folgefenster)
Bericht. Monatsvariante: `SE = SD_m * sqrt(c_m / 12)`. Beide Fenster erhalten dieselbe SE (eine Vorperiode).

**P-5 Nullwelt (DEC-94 (5) (ii), Jensen).** Diskretes log-normales SV-Modell je Symbol: `ln s2_t = mu + phi (ln s2_{t-1}
- mu) + eta e_t`, Tagesrendite `r_t = s_t z_t`, z standardisiertes Student-t(nu). Kalibrierung NUR auf RV der
Vorperiode (Preise bis 2024-05-31): Ziel-Momente (i) Mittel und (ii) SD von ln RV30 ueber nicht ueberlappende
30-Tage-Bloecke, (iii) deren Lag-1-Autokorrelation, (iv) Kurtosis der mit der Block-RV standardisierten Tagesrenditen;
Suche ueber (phi, eta, nu) mit gemeinsamen Zufallszahlen. IV_null(t) = sqrt((365/30) sum_k E_t[s2_{t+k}]) geschlossen.
Ausgaben: J (Erwartung der Fenster-Statistik unter der Null, je Einheit; S2 per Konstruktion ~0), SD der 335-Tage-
Fenster-Statistik (SE_null), c_null. **Bindende SE = max(SE_nuis, SE_null)** (DEC-94 (5)). Der Test zieht J ab
(C.4: struktureller Nulleffekt vor der Schwelle), d. h. die Schwelle lautet `mean - J >= z_krit * SE`.

**P-6 Bein-Aggregation (DEC-62 E3).** BTC+ETH sind EIN Bein (Rangkorrelation der IV-RV-Serien ~0,9, K-7). Wegen
ETH-Prior UNBELEGT ist **bindend: Bein = BTC** (A2, ETH als Bericht im Lauf); Bericht: Bein = Tagesmittel BTC/ETH (A1)
mit der Annahme "ETH-Prior = BTC-Prior" (Etikett UNBELEGT, Richtung Testbarkeit: SD-Gewinn sqrt((1+rho)/2)), und
Konjunktion beider Symbole (A3, Strenge). Gleiche Regel fuer die Selektions-K: gerechnete Varianten = K.

**P-7 Prior fuer die Zuordnung.** In S1 netto (nach Abzug von J), bewertet auf dem Vol-Niveau der Vorperiode
(dort ist die SE gemessen): sigma_n = Wurzel der mittleren RV30-Varianz BTC der Vorperiode (RV-Niveau, zulaessig).
- **Referenz (bindend fuer die Stopp-Regel):** pi-2, `prior = sigma_n * (exp(0,1431) - 1)`; in S3 direkt 0,143.
- Lesart Testbarkeit: pi-1, `prior = sqrt(sigma_n^2 + 0,14) - sigma_n`; in S2 direkt 0,14.
- Band: pi-2 mit 0,108..0,201 (Tabelle Abschnitt 2).
- Unbewertet bleibt das Niveau der Fenster (blind). Unter pi-2 ist die Bewertung auf dem Vorperioden-Niveau exakt
  (Praemie und SE skalieren gleich), unter pi-1 bei niedrigerem Fenster-Niveau konservativ.

**P-8 Zuordnung.** `power_p1.assign_regime(priors=[p, p], ses=[SE, SE])` und `power_p1.assign_regime_a3_practice`
(Doppelausweis DEC-94 (9)), K aus P-6 ueber `power_p1.effective_z`; Gitter ueber Prior und SE als Bericht; MDE80 je
Regime.

**P-9 Stopp-Regel.** Ausgewertet auf der Referenz-Konfiguration (S1, Bein BTC, n_W 335, c nach P-3, SE nach P-5,
Prior pi-2 zentral). GL-012 dort -> Stopp (Stufe 2 nicht), auch wenn eine Testbarkeits-Lesart C10/DEC52 ergaebe
(Gabelung wird ausgewiesen, A1-Lehre). Liegt das Ergebnis innerhalb des Prior-Bands auf beiden Seiten der Grenze,
wird das als "haengt am UNBELEGTEN Niveau" gefuehrt (blockiert wie UNBELEGT).

---

## 4. Offene / UNBELEGTE Punkte

| Punkt | Status | blockiert |
|---|---|---|
| DVOL 2021-03-24..2025-07-31 im Katalog | fehlt (angekuendigt) | alles Weitere |
| DVOL 2025-09-01..2026-03-19 (W2-Luecke) | fehlt, nicht bestellt | W2, Registrierung |
| L-1 Volltext (Definition, Einheit, Niveau) | nicht einsehbar (Egress) | Prior-Zeile der Registrierung |
| IV-Niveau der L-1-Stichprobe | UNBELEGT (Band) | Umrechnung in S1/S3 |
| ETH-Prior | UNBELEGT | Bein-Mittel A1 als bindende Variante |
| Nuisance-SD, c, Jensen-J, SE_null | nicht gerechnet | Power, Zuordnung |
| Underlying-Abweichung Bybit-Perp gegen Deribit-Index | nicht messbar ohne Fenster-RV | Bericht im Lauf |
