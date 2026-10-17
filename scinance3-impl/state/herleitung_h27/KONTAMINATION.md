# H-27 (VRP auf DVOL-Backfill) - Stufe 0: Kontaminations-Inventur (Etikett C.17)

> **ORCHESTRATOR-VERMERK 2026-10-13 (DEC-96):** EV-0c beschlossen - H-27 auf blinden, prospektiven Fenstern ab
> 2026-07-01 (Laenge nach vorab fixierter Regel L in {6, 9, 12} Monaten, nur aus Nuisance), W1/W2 nur Aera-Profil;
> Blind-Siegel auf DVOL- und BTC/ETH-Vol-Statistik ab 2026-07-01. Getroffen vor jeder H-27-Power-/Nuisance-Zahl.

> ENTWURF der Herleitung, Stand 2026-10-13. Nichts hier ist registriert oder beschlossen; entscheiden und registrieren
> darf nur der Orchestrator. Diese Inventur entstand VOR jeder Datenladung fuer H-27 (Reihenfolge laut Auftrag).
> Nicht geoeffnet: jede Siegeldatei (`*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`),
> die WP-10(A2)-IV-RV-Dateien (beide Laeufe), die WP-10(A)-Bestands-IV-RV-Dateien, der Inhalt der WP-9-Differenzserien.
> Bei Dateien, deren Inhalt fuer die Inventur noetig war, wurden nur Schluesselnamen bzw. Kopfzeilen gelesen (Skript-
> Ausgaben mit maskierten Ziffern); die Fundstellen sind unten genannt.

## 0. Befund in Kuerze

1. Die **realisierte Volatilitaet der Urteilsfenster** (BTC) steht in der Akte (DEC-85/v5e, A1-Feasibility). Damit ist
   die RV-Haelfte jeder Niveau-Statistik der Praemie in W1 UND W2 bis auf einige Vol-Punkte bekannt.
2. Die **IV-Haelfte** ist fuer **W2 teilweise** bekannt (R3: zwei DVOL-Stichpunkte im Fenster, Praktikerquelle) und liegt
   fuer W1/W2 vollstaendig in Dateien der Akte, die bis heute (von diesem Agenten) nicht geoeffnet wurden (WP-10(A2)-IV-RV,
   WP-9-Differenzserie mit Spalte `rest_close`).
3. **Vorwissen der Agenten:** Der Herleitungs-Agent (und jeder andere Agent desselben Modelltyps, auch der Reviewer)
   hat allgemeines Weltwissen ueber Krypto-Volatilitaetsregime 2024-2026 bis zu seinem Wissensstand (Mitte 2026). Es ist
   nicht quantifizierbar und nicht entfernbar; es wurde in keiner Zahl dieser Herleitung verwendet.
4. **Bewertung:** Die natuerliche H-27-Statistik (mittlere Praemie IV - RV_fwd30 je Fenster, in Vol-Punkten, Varianz-
   oder Log-Einheiten) ist **in W2 weitgehend, in W1 zur Haelfte nicht blind** (Akte), fuer beide Fenster zusaetzlich
   qualitativ durch Vorwissen. **Blind gegenueber der Akte bleiben:** die IV-Seite von W1; Konstrukte, die von der
   Kovarianz innerhalb des Fensters abhaengen (z. B. Prognose-Effizienz, bedingte Praemie); das ETH-Einzelbein auf der
   RV-Seite; und jedes Fenster ab 2026-07-01 (bis auf benannte Einzeltage). Stufe 0 macht damit **nicht jede** sinnvolle
   Statistik nicht-blind; die Stopp-Regel des Auftrags (Stufe 0) greift nach dieser Lesart nicht. Die Lesart ist eine
   Ermessensentscheidung (Richtung: **Testbarkeit**); die strenge Gegenlesart steht als EV-0 unten.
5. **Etikett C.17 (Pflicht, Wortlaut-Vorschlag):** "H-27: Fenster-RV BTC W1/W2 gesehen (DEC-85/v5e 0,0669/0,0551
   Wochen-SD; A1-Feasibility 6,5 %/5,3 %); W2-DVOL-Stichpunkte gesehen (R3 K-36, Praktikerquelle, 2025-11/2025-12);
   WP-10(A2)-IV-RV-Serie und WP-9-Differenzserie existieren mit W1/W2-Niveaus (nicht geoeffnet); Vorwissen der Agenten
   ueber Krypto-Vol 2024-2026 (nicht quantifizierbar); Literaturzahl BVRP 0,14 (Stichprobe 2017-2022, vor W1)."

---

## 1. Inventur: was in der Akte steht und das H-27-Ergebnis in W1/W2 teilweise verraet

Fenster (C.18, PRD/Auftrag): W1 2024-07-01..2025-06-30, W2 2025-07-01..2026-06-30.

| # | Groesse | Wert / Inhalt | Fundstelle | Betrifft | Angesehen? |
|---|---|---|---|---|---|
| K-1 | BTC-Wochenrendite-SD je Fenster (sigma_f, DEC-77-Kalibrierung) | W1 0,06685 (n 53 Wochen), W2 0,05514 (n 52); annualisiert x sqrt(365,25/7) = 7,224 -> **48,3 % / 39,8 %** [abg.] | DEC-85 ("gemessen 0,067 / 0,055"), `state/runs/wp13a_20261012_v5e/wp13a_prelaunch.md` Z. 34/86 | RV-Niveau BTC, beide Fenster | ja (Akte, von allen gelesen) |
| K-2 | BTC-Wochen-Autokorrelation je Fenster | 0,046 / 0,042 (v5e: 0,0462 / 0,0416) | DEC-78, v5e Z. 34/86 | Abbildung Wochen- auf 30-Tage-Vol | ja |
| K-3 | Markt-Faktor-SD je Fenster (A1) | BTC 6,5 % / 5,3 % je Woche, EW-Universum 13,2 % / 7,9 % | `state/herleitung_a1/FEASIBILITY.md` Abschnitt 4 Punkt 1 | RV-Niveau BTC (zweite Messung), Altcoin-Vol | ja |
| K-4 | WP-10(A2)-Tagesserie IV - RV (REST-DVOL-Close minus Tages-RV aus 1-min-Bars, annualisiert, 365) BTC/ETH 2021-03-24..2026-07-31 | Niveaus je Tag (NICHT angesehen) | `state/runs/wp10a2_20260910/wp10a_ivrv_backfill_{BTC,ETH}_daily.csv` und namensgleich `state/runs/wp10a2_20260909/` (gleiche Groesse) | **fast das ganze H-27-Ergebnis** (Fenstermittel IV minus Fenstermittel Tages-RV) | **nein** (Datei nicht geoeffnet; Definition aus Code `wp10_coherence/series.py`, `rv.py`) |
| K-5 | WP-10(A)-Bestandsserie IV - RV BTC/ETH 2025-08-01..2026-07-31 (165 Tage, lueckig) | Niveaus je Tag | `state/runs/wp10a_20260909/wp10a_ivrv_{BTC,ETH}_daily.csv` | W2-Ergebnis (Teil) | **nein** |
| K-6 | WP-9-Differenzserie mit Spalten `date,rest_close,harvest_close,diff` | DVOL-Niveaus an 176 Tagen 2025-08-01..2026-08-13 (ueberwiegend W2) | `state/runs/wp9_20260909/wp9_{BTC,ETH}_diff_series.csv` | IV-Niveau W2 | **nein** (nur Kopfzeile gelesen); wer WP-9 adjudiziert hat, kann sie gesehen haben (unbekannt) |
| K-7 | Rangkorrelationen der IV-RV-Serien | BTC x ETH 0,907 (Bestand 2025-08..2026-07), 0,88 Ruhe / 0,89 Stress (Backfill); BTC-Funding x IV-RV im Stress -0,43/-0,46 | `WELLE1_BEFUND_TEIL2_2026-09-09.md`, `..._TEIL3_2026-09-10.md`, DEC-62/64/65; `wp10a_summary.json` (nur Schluesselnamen geprueft: keine Niveau-/Mittelwertschluessel fuer IV-RV) | Abhaengigkeitsstruktur, KEIN Niveau | ja |
| K-8 | DVOL-Stichpunkte im Fenster W2 | "DVOL schwankte zwischen 43 % (Ende 12/2025) und 63 % (Ende 11/2025), gegen einen VIX von 14-20" [unbelegt, Praktikerquelle] | `scinance3-impl/research/R3_EREIGNIS_STRUKTUR.md` K-36 | IV-Niveau W2 (zwei Monatsenden) | **ja** (beim Lesen von R3 in dieser Herleitung gesehen; seit 2026-09 in der Akte) |
| K-9 | Literaturzahl BVRP | 0,14 gegen ~0,02 fuer den S&P, Deribit 2017-2022 [sek] | `research/R1_RISIKOPRAEMIEN.md` K-05; DEC-94 Feststellung (i) | Prior-Quelle; Stichprobe VOR W1 -> keine Outcome-Information | ja |
| K-10 | Stress-Kanon | STRESS_ABS: 30 Tage/19 Episoden bis 2026-08-19, Schwellen = 99-%-Perzentil der Tages-RV 2020-05..2026-08 (BTC 9,20 %, ETH 12,18 %), benannt 2025-10-10 und 2026-08-19; STRESS_REL: 84 Tage/52 Episoden (rollierendes 97,5-%-Perzentil) | `state/runs/stress_{abs,rel}.json`, TEIL2 | Lage von RV-Extremtagen in W1/W2 (kein Mittel) | Struktur ja, Tageslisten nicht ausgewertet |
| K-11 | Programmannahmen zur BTC-Vol | sigma_1d 262 bp (50 % p.a., R4 K-0.1), Tagesvol 2,5 % (PRD 5.2), sigma_ann 50 % (R1 0.4) | PRD 9.2, R1, R4 | Arbeitswerte ohne Fensterbezug | ja |
| K-12 | H-26-Akte (2.0) | Gate 3 Vol-Punkte (C-33), A-priori "PASS erwartet ~70/30", nie gelaufen | `scinance2-impl/state/hypothesis_registry.md` H-26 | Meinung, keine Daten | ja |

### 1.1 Aussagen des Orchestrators zum Gesehenen (Akte)

- DEC-94 Feststellung (A-5 (1)): keine H-27-Zahl zu Prior, SE, Power oder Feasibility existiert oder wurde gerechnet;
  offengelegt R1-Literaturzahl (K-9) und WP-10(A2)-Serie (K-4, "nur Rangkorrelationen ausgewertet").
- DEC-95 E2: Nachtrag - die realisierte BTC-Volatilitaet der Urteilsfenster (K-1, K-3) ist gesehen; Folge: Inventur,
  RV-Sperre ab 2024-06-01, DVOL-Niveau-Sperre ab 2024-07-01.
- `ANFRAGE_DATA_HARVEST_DVOL_2026-10-13.md`, UEBERGABE 2026-10-12 Abschnitt 5, Auftrag "Datenstand beim Start": nur
  Katalog-Abdeckung (`deribit/dvol` ab 2025-08-01, 2 Symbole), keine Niveaus.
- P-1-Herleitung und -Review (`state/herleitung_programmregel_p1/`): ausdruecklich keine DVOL-/H-27-Daten angesehen.
- Nicht in der Akte festgehalten (also UNBEKANNT): ob jemand bei der Adjudikation von WP-9 (DEC-61) die Spalte
  `rest_close` (K-6) oder bei WP-10(A2) die CSV-Inhalte (K-4/K-5) angesehen hat. Der Strom `deribit/dvol` ab
  2025-08-01 ist seit Wochen ueber den Thin Client fuer jede Sitzung lesbar; ein Blick darauf ist nicht vermerkt.

### 1.2 Was dieser Herleitungs-Agent zusaetzlich gesehen hat (Offenlegung)

- R3 K-36 (K-8) beim Pflichtlesen der VRP-Akte.
- Web-Suche nach Prior-Literatur (Abschnitt Prior in `FEASIBILITY.md`): neben den genutzten Snippets (Stichproben vor
  2024-07) erschienen **Ergebnistitel** mit moeglichem Fensterbezug, deren Inhalt NICHT geoeffnet wurde (WebFetch ist
  in der Sandbox ohnehin gesperrt): ein GitHub-Pull-Request-Titel "research/x5: Deribit DVOL / variance risk premium
  (NEGATIVE, power-limited)" (Autor, Stichprobe, Fragestellung unbekannt) und ein Blog-Titel zu "DVOL in Q2 2026"
  (Inhalt unbekannt). Ausserdem eine Praktiker-Zusammenfassung (Paradigm/Amberdata), die von "nearly 25 vol points at
  times" und flachen negativen Praemien spricht (undatiert). Keines davon geht in eine Zahl ein.
- Vorwissen aus dem Training (Punkt 0.3): allgemeine Kenntnis von Krypto-Vol-Regimen bis Mitte 2026, einschliesslich
  der gaengigen Marktnarrative ueber implizite und realisierte BTC-Vol 2024-2026. Nicht gezielt abgerufen, nicht in
  Zahlen verwendet, nicht quantifizierbar. Gilt gleichermassen fuer den Reviewer.

---

## 2. Was K-1..K-12 ueber das H-27-Ergebnis verraten (quantitativ, soweit moeglich)

**RV-Haelfte (K-1, K-3).** Die mittlere realisierte Varianz eines Fensters ist bis auf Stichprobenfehler die quadrierte
annualisierte Wochen-SD: W1 ~ 0,483^2 = 0,233, W2 ~ 0,398^2 = 0,158 (Varianzeinheiten) [abg.]. Unsicherheit: SE der
SD aus 52 Wochen ~ SD * sqrt((kappa - 1)/(4 n)); bei Wochen-Kurtosis kappa 4..6 ~ 12..15 % relativ, also ~ +-6 / +-5
Vol-Punkte (1 SE) [abg.]; zusaetzlich Abweichung Woche (Close-to-Close, Wochen-Autokorrelation 0,04) gegen 30-Tage-RV
aus Tagesrenditen (klein) und der Jensen-Abstand zwischen Mittel der Vol und Wurzel des Varianzmittels (einige Vol-
Punkte nach unten). Folge: **das Fenstermittel von RV_fwd30 ist fuer BTC in beiden Fenstern auf ~+-5..8 Vol-Punkte
bekannt** (W1 um ~45, W2 um ~37 Vol-Punkte als grobe Lesart, ausdruecklich keine Messung). Fuer ETH steht keine
Einzel-RV in der Akte (nur der EW-Faktor, K-3).

**IV-Haelfte.** W1: kein IV-Niveau in gelesenen Akten (nur in K-4, nicht geoeffnet). W2: zwei Monatsend-Stichpunkte
43 / 63 (K-8, Praktikerangabe ohne Beleg) - das Fenstermittel ist daraus nicht bestimmbar, aber die Groessenordnung
"DVOL W2 deutlich ueber 40" ist gesehen. Zusammen mit K-1 ergibt das fuer W2 eine **grobe Vorzeichen-/Groessen-
Information ueber die Praemie** (Praemie in W2 eher positiv und einstellig bis niedrig zweistellig), fuer W1 keine.

**Abhaengigkeitsstruktur (K-7).** BTC- und ETH-IV-RV korrelieren zu ~0,9 (Rang) - das stuetzt "BTC+ETH = ein Bein"
(DEC-62 E3) und ist kein Niveau. Wird fuer die Aggregation zitiert, nicht neu gemessen.

**Extreme (K-10).** Stress-Tage in W1/W2 sind bekannt (Datum), ihre Anzahl ist beim rollierenden Kanon per Konstruktion
~2,5 % je Fenster (DEC-56) - keine Niveau-Information ueber das Fenstermittel. Die Abdeckungs-Pflicht (3.3.10) darf
STRESS_REL zaehlen.

---

## 3. Bewertung je Teststatistik

| Statistik (je Fenster) | Aus Fenster-RV und Fenster-IV-Mittel ableitbar? | Akte W1 | Akte W2 | Vorwissen | Lesart |
|---|---|---|---|---|---|
| S1 mittlere Praemie IV - RV_fwd30 (Vol-Punkte) | ja (bis auf Jensen-/Streuungsterme) | RV-Haelfte bekannt, IV unbekannt -> **halb** | RV bekannt, IV teilweise (K-8) -> **weitgehend nicht blind** | qualitativ | **nicht blind (C.17-Etikett Pflicht)** |
| S2 mittlere Varianzpraemie IV^2 - RV_fwd30^2 | ja (RV^2-Mittel = Fenster-Varianz, direkter als S1) | halb | weitgehend | qualitativ | nicht blind |
| S3 mittlere Log-Praemie ln(IV/RV_fwd30) | ja, naeherungsweise | halb | weitgehend | qualitativ | nicht blind |
| S4 Anteil Tage/Monate mit IV > RV_fwd30, Median-Praemie | nicht exakt, aber bei bekannten Mitteln weitgehend vorhersagbar | halb | ueberwiegend | qualitativ | teilweise nicht blind |
| S5 ETH-Einzelbein | ETH-RV nicht in der Akte (nur EW-Faktor) | IV und RV unbekannt -> blind ggue. Akte | IV-Stichpunkte nur BTC -> blind ggue. Akte (ETH-BTC-Kopplung ~0,9, K-7) | qualitativ | gegenueber der Akte weitgehend blind; inhaltlich ~BTC |
| S6 Konstrukte aus der Kovarianz im Fenster (Mincer-Zarnowitz-Steigung von RV_fwd30 auf IV, bedingte Praemie nach IV-Zustand, Korrelation Praemie/IV-Niveau) | nein | blind | blind | gering | **blind**, aber andere Hypothese (H-27 ist die Existenz-/Niveaufrage); R3-K-36 (bedingte Praemie) ist an der Power gestorben (Review R1-R4) |
| S7 S1..S3 auf Fenstern ab 2026-07-01 (z. B. W3 2026-07-01..2027-06-30) | - | - | - | jenseits des Wissensstands des Agenten | **blind** bis auf K-10 (2026-08-19 Stress-Tag), K-4 (bis 2026-07-31, ungeoeffnet), K-6 (bis 2026-08-13, ungeoeffnet) und den frei lesbaren Harvest-Strom |

**Gesamtlesart.** Fuer die Fenster W1/W2 ist die H-27-Kernstatistik (S1..S3) **nicht blind**. Blind bleiben S5 (gegen-
ueber der Akte, nicht gegenueber dem Weltwissen), S6 (andere Frage) und S7 (andere Fenster). Damit ist nicht "jede
sinnvolle Statistik" nicht-blind; die Herleitung laeuft mit Pflicht-Etikett weiter.

---

## 4. Folge fuer das Design - Entscheidungsvorlage EV-0 (Orchestrator)

| Option | Inhalt | Folgen | Richtung |
|---|---|---|---|
| **EV-0a** | H-27 auf W1/W2 mit S1 (bzw. S2/S3), Etikett C.17 wie in 0.5; Registrierung legt offen, dass die RV-Haelfte beider Fenster und IV-Stichpunkte in W2 gesehen sind; alle Designwahlen (Statistik, RV-Schaetzer, Fenster-Zugehoerigkeit, Aggregation, Prior) mit Gabelungs-Richtung ausgewiesen | Ergebnis ist eine Bestaetigung unter teilweiser Kenntnis; Schwelle bleibt mechanisch (DEC-94, z_krit * SE), Wahlfreiheit liegt nur in den Designwahlen | **Testbarkeit** |
| EV-0b | wie EV-0a, aber W2 nach C.17 nicht konfirmatorisch (Naehe zur "Entdeckungszelle" wegen K-8) | nur ein urteilstragendes Fenster -> weder C.10 (zwei Fenster) noch DEC-52 (>= 2 Fenster) moeglich -> **GL-012 per Konstruktion** | Strenge |
| EV-0c | neue, blinde Urteilsfenster ab 2026-07-01 (S7), z. B. W3 = 2026-07-01..2027-06-30 (+30 Tage RV), W4 = 2027-07-01..2028-06-30; W1/W2 nur Aera-Profil | blind gegenueber Akte und Agenten-Wissensstand; REZENZ (C.18) inhaltlich erfuellt (juengstes Regime), formal Abweichung von den Programm-Fenstern -> eigene DEC VOR der Registrierung; Wartezeit bis 2027-07-30 bzw. 2028-07-30; Datenquelle (DVOL-Strom, Panel-Strom Variante B) muss bis dahin laufen | Strenge |
| EV-0d | blinde Konstrukte (S6) als H-27-Statistik | ist nicht die H-27-Frage (Existenz der Praemie); eigene Hypothese mit eigenem K (DEC-58 E2) | - |

Empfehlung des Herleitungs-Agenten: keine (Orchestrator-Entscheidung). Hinweis: EV-0a ist die einzige Option, die H-27
in den Programmfenstern ueberhaupt rechenbar macht; sie ist in Richtung Testbarkeit gewaehlt und muss das Etikett
tragen. Die Feasibility (Stufe 1) wird fuer EV-0a gerechnet; ihre Power-/MDE-Zahlen gelten fuer EV-0c sinngemaess
(gleiche Fensterlaenge), sofern das Vol-Regime vergleichbar ist.

## 5. Regeln, die aus der Inventur fuer diese Herleitung folgen (eingehalten)

- Keine RV (BTC/ETH, beliebige Preisquelle) auf Tagen ab 2024-06-01; Preisdaten werden vor jeder Rechnung auf
  <= 2024-05-31 abgeschnitten (Waechter im Code).
- Keine DVOL-Niveau-Statistik ab 2024-07-01; ab dort nur Zeilen je Tag, Luecken, Zeitstempel, Schema, Gleichheits-/
  Stetigkeitspruefungen ohne Niveauausgabe.
- Nuisance-Groessen nur auf 2021-03-24..2024-05-31; der Mittelwert der Praemie (jeder Einheit) wird weder ausgegeben noch
  gespeichert; ebenso wird kein DVOL-Mittel der Vorperiode ausgegeben, damit das Praemienmittel nicht aus zwei Niveaus
  ableitbar ist (RV-Niveaus der Vorperiode sind fuer die Nullwelt-Kalibrierung zulaessig und werden ausgegeben).
- K-4, K-5, K-6 bleiben ungeoeffnet.

---

## Nachtrag 2026-10-17 (Fortsetzung nach DEC-96)

- **DEC-96 E1/E3:** Der Orchestrator hat EV-0c gewaehlt (blinde Fenster ab 2026-07-01) und das Blind-Siegel ab
  2026-07-01 beschlossen. Die Inventur oben bleibt fuer W1/W2 gueltig (dort nur noch Aera-Profil, Etikett "nicht
  blind"); fuer W3/W4 gilt sie nicht, ausser den in DEC-96 E3 genannten Punkten (STRESS_ABS-Tag 2026-08-19; K-4 und
  K-6 mit Werten bis 2026-07-31 bzw. 2026-08-13, weiterhin ungeoeffnet).
- **Was diese Fortsetzung ab 2026-07-01 gesehen hat:** nur Vollstaendigkeit - Katalogzeilen, Luecken, Status,
  Zeilenzahlen, Zeitstempel, Schema von `deribit/dvol` (keine Werte, keine Stetigkeitspruefung ab 2026-07-01) und
  `bybit/publicTrade`. **Offengelegt, weil schwacher Aktivitaets-Stellvertreter:** die Katalog-Bytesummen von
  `bybit/publicTrade` 2026-07-01..2026-10-16 wurden ausgegeben (BTCUSDT 7.909 MB, ETHUSDT 8.826 MB in 108 Tagen, also
  ~73 / ~82 MB je Tag; zum Vergleich Median 2024-06..2026-07 ~71 MB je Tag, `DATENPROBE.md` A.2). Die Handelsmenge
  korreliert mit der Volatilitaet; die Zahl ist eine grobe Tagesdurchschnitts-Groesse ohne Renditebezug und wird
  hier als "gesehen" gefuehrt. Weitere Bytesummen ab 2026-07-01 wurden nicht ausgegeben.
- **2024-07-01..2026-06-30 (DVOL-Niveau-Regel):** nur Gleichheitszaehlungen close/open an Stunden- und Tagesnaehten
  (keine Betraege), Naht 2025-07-31/08-01 als ja/nein.
- **Vorperiode:** RV-Niveau (rms RV_fwd30 BTC 61,55 %, ETH 79,32 %), Streuung, Autokorrelation und Varianzfaktoren der
  Praemie, Nullwelt-Kalibrierung aus Renditen bis 2024-05-31 - kein Praemienmittel, kein DVOL-Mittel (Waechter
  `no_mean`); Pruefungstage der Konventionsprobe liegen alle vor 2024-06-01.
- Keine neue Web-Suche in der Fortsetzung.
