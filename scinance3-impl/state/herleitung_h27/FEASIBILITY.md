# H-27 (VRP auf DVOL-Backfill) - Stufe 1: Feasibility (C.12) - STAND 2026-10-17: GL-012 VOR DER REGISTRIERUNG

> **ORCHESTRATOR-VERMERK 2026-10-17 (DEC-97, GL-034):** Befund GL-012 vor der Registrierung beschlossen (Review
> ZUSTIMMUNG MIT AUFLAGEN, `REVIEW_H27.md`). Auflagen A-1..A-3 sind in DEC-97 umgesetzt: Gabelung Hochfrequenz-RV
> (UNBELEGT) ergaenzt; c = 28,17 ist das Maximum der Regel P-3 (Konsens 18,6, Richtung Strenge); Offenlegung der
> Orchestrator-Sicht auf publicTrade-Metadaten im Blindbereich und der vermeidbaren Bytesummen; DVOL-Cache ab
> 2024-07-01 am 2026-10-17 geloescht.

> ENTWURF der Herleitung. Nichts hier ist registriert oder beschlossen; entscheiden und registrieren darf nur der
> Orchestrator. Gerechnet nach DEC-96 (EV-0c, blinde Fenster W3/W4 ab 2026-07-01, Fensterlaengen-Regel E2,
> Blind-Siegel E3) und den VOR jeder Nuisance-Zahl fixierten Regeln P-1..P-9 (Anhang A, Abschnitt A-3; dort
> ueberholt ist nur die W1/W2-Fensterzuordnung, P-4 wird durch DEC-96 E2 ersetzt).
> Ergebnisblindheit: keine RV ab 2024-06-01, keine DVOL-Niveau-/Streuungsstatistik ab 2024-07-01, nichts ab
> 2026-07-01 ausser Vollstaendigkeit; kein Praemienmittel (jede Einheit) und kein DVOL-Mittel der Vorperiode
> ausgegeben oder gespeichert (Waechter `h27_common.no_mean`); keine Siegeldatei, keine IV-RV-Datei aus WP-10(A2)/
> WP-10(A), kein Inhalt der WP-9-Differenzserie geoeffnet.
> Kuerzel: `[fj]` = `feasibility.json` (gleicher Ordner, JSON-Pfad); `[S:<datei>]` = Skript unter
> `scratchpad/h27_herleitung/` (sha256 in `[fj] skripte_sha256`); `[sek]` Sekundaerbeleg; `[abg.]` hier abgeleitet.

## 0. Befund in Kuerze

1. **Fensterlaenge nach DEC-96 E2: kein L existiert.** In der Referenz-Konfiguration (P-9: Statistik S1 =
   Fenstermittel von IV - RV_fwd30 minus Nullwelt-J, Bein BTC, SE = max(Nuisance, Nullwelt), Prior pi-2 zentral)
   ist die Zuordnung mit `power_p1.assign_regime` fuer **L = 6, 9 und 12 Monate GL012**; der Doppelausweis
   `assign_regime_a3_practice` ebenfalls GL012. Bei L = 12: Fenster-Power 0,575 / 0,575, DEC-52-Gate (Produkt)
   0,359 (exakt 0,491, Bericht), MDE80 12,85 Vol-Punkte gegen Prior 9,47. **Folge nach DEC-96 E2: H-27 ist GL-012 vor
   der Registrierung. KEIN Verdikt ueber die Volatilitaets-Risikopraemie.** Stufe 2 wurde nicht erstellt.
2. **Robust auf der strengen und der zentralen Seite:** alle Einheiten (S1/S2/S3), alle Beine (BTC, ETH, Tagesmittel),
   Monatsvariante und Nullwelt-SE allein ergeben beim zentralen Prior fuer jedes L GL012. Beim zentralen Prior
   braucht C10 je Fenster mindestens 672 Tage (S1/BTC; 633..1.310 je Konfiguration), DEC-52 mindestens 736 Tage.
3. **Gabelung (A1-Lehre, ausgewiesen):** Testbar wird H-27 nur mit Lesarten in Richtung Testbarkeit:
   (a) Prior am oberen Rand des UNBELEGTEN Niveau-Bands (pi-2 hoch, IV der Literaturstichprobe 0,65): C10 bei L = 12
   (nur unter P-1, A3-Praxis GL012 -> Etikett "zugelassen nur durch DEC-94"); (b) zusaetzlich c nur aus Bartlett-
   Schaetzern (17,8 statt 28,2): C10 bei L = 9; (c) pi-1 (konstante Varianzpraemie) mit Bartlett-c: C10 bei L = 12.
   Nach P-9 bindet die Referenz; dass der zentrale Prior und der obere Bandrand auf verschiedenen Seiten der Grenze
   liegen, heisst "haengt am UNBELEGTEN Niveau" und blockiert wie UNBELEGT. Keine der Gabelungen ist beschlossen.
4. **Datenprobe:** DVOL BTC/ETH 2021-03-24..2026-10-16 lueckenlos (2.033 Tage, je 24 Stundenkerzen, ein Schema, eine
   `topic`, `ts_exchange_ms` = Kerzenbeginn), Naht 2025-07-31/08-01 gleich (close 23h = open 00h, beide Symbole).
   RV-Konvention: Panel-Tagesschluss = letzter `publicTrade`-Trade vor 00:00 UTC an 12/12 Pruefungstagen
   (2021-06..2024-03, Abweichung 0) -> dieselbe RV-Definition fuer Vorperiode und W3/W4 ist moeglich.
5. **Nuisance (Vorperiode, Etikett):** BTC-Praemie S1: SD 18,60 Vol-Punkte, ACF faellt bei Lag 21 unter 0,10, bei
   Lag 30 -0,16 (Ueberlappungs-Dreieck plus Rueckkehr), Varianzfaktor c = 28,2 bindend (Batch-Means L 90; Bartlett
   60..120: 16,9..17,8; stationaerer Bootstrap 15,9..17,8); Nullwelt-Jensen J = +2,1 Vol-Punkte (S1, auf dem
   Vorperioden-Niveau), +0,059 (S3), ~0 (S2).
6. **Prior [sek]:** BVRP 0,14 (Almeida/Grith/Miftachov/Wang 2024, Deribit-BTC 2017-07..2022-12); auf dem
   Vorperioden-Niveau (RV-rms 61,6 %) nach pi-2: 9,47 Vol-Punkte (Band 7,00..13,72), nach pi-1: 10,48. ETH-Prior
   UNBELEGT. Volltext von L-1 nicht einsehbar (Egress).

---

## 1. Daten und Konventionen (Details `DATENPROBE.md` Teil C)

| Stueck | Stand | Quelle |
|---|---|---|
| Katalog | Export 2026-10-17T10:39:26Z, 349.961 Partitionen, einmal geladen | [S:catalog_check2.py] |
| `deribit/dvol` BTC/ETH | 2021-03-24..2026-10-16, je 2.033 Tage, 0 Luecken, alle DONE, 24 Zeilen je Tag | [S:catalog_check2.py], [S:dvol_probe.py] |
| IV(t) | close der Stundenkerze 23:00 UTC (Wert um 24:00 UTC); Abweichung zum open der Folgestunde in der Vorperiode hoechstens 0,01 (BTC) / 0,05 (ETH) Vol-Punkte an 39 / 84 von 1.195 Tagesnaehten | [S:dvol_probe.py] |
| Preise Vorperiode | Union-Panel BTCUSDT/ETHUSDT, Tagesschluss, abgeschnitten bei 2024-05-31 | [S:h27_series.py] |
| Preise W3/W4 | `bybit/publicTrade` BTCUSDT/ETHUSDT, letzter Trade vor 00:00 UTC (lueckenlos ab 2026-07-01 laut Katalog) oder kuenftiger Panel-Strom | DEC-96 Nachtrag |
| Gleichheit der Konvention | 12/12 Tage (je Symbol 2021-06-15, 2022-11-09, 2023-03-15, 2023-09-15, 2023-12-15, 2024-03-15) Panel-close = letzter Trade, relative Abweichung 0 | [S:conv_check.py] |
| RV_fwd30(t) | `sqrt((365/30) * sum_{k=1..30} r_{t+k}^2)`, r = ln(C_s/C_{s-1}), eine Konstante 365 | [S:h27_series.py] |

## 2. Nuisance (Vorperiode IV-Tage 2021-03-24..2024-05-01, Preise bis 2024-05-31; n = 1.135 je Serie, keine Luecke)

Etikett: "Nuisance 2021-03-24..2024-05-31: nur Streuungs-, Autokorrelations- und Verhaeltnisgroessen; der Mittelwert
der Praemie (jede Einheit) und das DVOL-Mittel der Vorperiode werden weder ausgegeben noch gespeichert." [fj:nuisance]

| Serie | SD | ACF 1 / 10 / 20 / 30 / 60 / 120 | erster Lag < 0,10 | c Bartlett 60/90/120 | c Batch-Means 60/90/120 | c stat. Bootstrap 30/60/90 | **c bindend (P-3)** | Monatsvariante SD / ACF1 / c_m |
|---|---:|---|---:|---|---|---|---:|---|
| BTC S1 (Vol-Punkte) | 18,60 | 0,955 / 0,514 / 0,107 / -0,155 / 0,054 / 0,012 | 21 | 16,9 / 17,5 / 17,8 | 19,2 / 28,2 / 15,2 | 15,9 / 17,8 / 17,5 | **28,17** | 18,70 / -0,16 / 1,0 |
| ETH S1 | 25,10 | 0,965 / 0,582 / 0,189 / -0,072 / -0,032 / 0,038 | 23 | 20,3 / 20,5 / 20,2 | 27,6 / 27,2 / 23,0 | 18,0 / 19,4 / 19,7 | 27,64 | 25,22 / -0,06 / 1,0 |
| Bein-Mittel S1 | 20,93 | 0,962 / 0,554 / 0,152 / -0,107 / 0,006 / 0,026 | 22 | 18,9 / 19,3 / 19,3 | 23,7 / 27,9 / 18,8 | 17,0 / 18,8 / 19,0 | 27,91 | 21,04 / -0,11 / 1,0 |
| BTC S2 (Varianz x 100) | 27,26 | 0,943 / 0,486 / 0,128 / -0,046 / 0,047 / 0,013 | 21 | 18,7 / 20,3 / 21,7 | 22,0 / 29,4 / 18,0 | 17,2 / 20,8 / 21,3 | 29,44 | 27,28 / -0,05 / 1,0 |
| BTC S3 (Log) | 0,304 | 0,960 / 0,529 / 0,072 / -0,278 / 0,108 / 0,017 | 20 | 14,6 / 14,7 / 14,3 | 16,6 / 25,9 / 13,0 | 14,4 / 14,7 / 14,2 | 25,94 | 0,306 / -0,29 / 1,0 |

- **Bandbreite (Begruendung):** die Praemie ist bis Lag ~20 stark positiv (Ueberlappung der 30-Tage-Ziele) und bei
  Lag 30 negativ; ab Lag ~45 liegt die ACF im Rauschband (|ACF| < 0,11 bei n = 1.135). Bandbreiten 60..120 decken die
  gesamte gemessene Persistenz ab; die Erweiterung auf 180 (P-3) war nicht noetig (ACF(120) = 0,012). Bindend ist nach
  der vorab fixierten Regel das Maximum (hier Batch-Means L 90 mit nur 12 Bloecken - der groesste, aber auch der
  unsicherste Schaetzer; Richtung Strenge). Bartlett und Bootstrap liegen bei 16..18 (Gabelung im Befund 0.3).
- Korrelation BTC/ETH der Tagespraemie: 0,83 (S1), 0,81 (S2), 0,84 (S3) - stuetzt "ein Bein" (DEC-62 E3); das
  Tagesmittel senkt die SD in Vol-Punkten nicht, weil ETH auf hoeherem Niveau streut (20,9 gegen 18,6).
- Korrelation benachbarter Fenstermittel (Ziel ragt 30 Tage ins Folgefenster): BTC S1 -0,10 (L 6) .. -0,06 (L 12) -
  negativ, die Unabhaengigkeitsannahme des gepoolten DEC-52-Gates ist damit konservativ [fj:power.configs.*.L.*.dec52_with_adjacent_corr].
- RV-Niveau der Vorperiode (zulaessig, RV allein): rms RV_fwd30 BTC 61,55 %, ETH 79,32 %.

## 3. Nullwelt (DEC-94 (5) (ii), C.4: Jensen) [S:nullworld.py], [fj:nullwelt]

- Modell je Symbol: log-normales SV, `h_t = mu + phi (h_{t-1} - mu) + eta e_t`, `r_t = exp(h_t/2) z_t`, z
  standardisiert t(nu); IV_null(t) = sqrt((365/30) sum_k E_t[exp(h_{t+k})]) geschlossen (keine Praemie).
  Kalibrierung nur auf RV der Vorperiode (Momente von y = ln RV30^2: SD, ACF 30, ACF 90; Kurtosis der standardisierten
  Tagesrenditen), gemeinsame Zufallszahlen, Gitter phi 0,95..0,998, eta 0,04..0,30, nu 4,5..15.
  BTC: phi 0,996, eta 0,06, nu 4,5 (Distanz 0,79); ETH: phi 0,998, eta 0,08, nu 4,5 (0,33). nu liegt am Gitterrand;
  die Kurtosis ist schwach identifiziert (simulierte SD des Moments ~18) - nu 4,5 gibt den groessten J und die
  groesste SE_null (konservativ); nu-Sensitivitaet unten.
- Wegen phi nahe 1 streut das Vol-Niveau zwischen simulierten Fenstern stark; S1/S2 werden deshalb je Fenster auf das
  Vorperioden-Niveau normiert (`*_at_ref`), S3 ist niveaufrei.

| Groesse (BTC, n = 365) | S1 Vol-Punkte | S2 Varianz x 100 | S3 Log |
|---|---:|---:|---:|
| J (struktureller Nulleffekt, auf Vorperioden-Niveau) | **+2,09** (roh 1,87 +- 0,06) | roh +0,02 +- 0,12 (per Konstruktion 0) | **+0,059** |
| J bei nu 6 / 8 / 15 | 1,49 / 1,33 / 1,12 | - | 0,042 / 0,036 / 0,030 |
| SE_null der Fenster-Statistik n = 184 / 274 / 365 | 5,64 / 4,65 / 4,17 | 8,98 / 7,36 / 6,81 | 0,087 / 0,073 / 0,065 |
| c_null | ~27 | ~28 | ~28 |

ETH: J (S1) +3,32 Vol-Punkte, S3 +0,067; SE_null (S1) 7,54 / 6,19 / 5,57. In allen Konfigurationen bindet die
Nuisance-SE (groesser als SE_null).

## 4. Prior (Literatur vor 2024-07; Abschnitt A-2 im Anhang unveraendert gueltig)

Auf dem Vorperioden-Niveau sigma_n (rms RV) bewertet, netto (der Test zieht J ab):

| Bein | sigma_n | pi-2 zentral (ln 0,1431) | pi-2 Band (0,1077..0,2012) | pi-1 (V = 0,14 konstant) |
|---|---:|---:|---|---:|
| BTC (S1, Vol-Punkte) | 61,55 % | **9,47** | 7,00 .. 13,72 | 10,48 |
| BTC (S3) | - | 0,143 | 0,108 .. 0,201 | 0,157 |
| BTC (S2, x 100) | - | 12,55 | 9,11 .. 18,77 | 14,00 |
| ETH (S1), Prior UNBELEGT, nur Bericht mit gleicher relativer Praemie | 79,32 % | 12,20 | 9,02 .. 17,68 | 8,38 |

## 5. Zuordnung und Fensterlaenge (DEC-96 E2, `power_p1`) [S:power_h27.py], [fj:power]

Fenster: L 6 -> W3 2026-07-01..2026-12-31 (184 Tage), W4 2027-01-01..2027-06-30 (181); L 9 -> 2026-07-01..2027-03-31
(274), 2027-04-01..2027-12-31 (275); L 12 -> 2026-07-01..2027-06-30 (365), 2027-07-01..2028-06-30 (366). IV-Tage =
alle Kalendertage des Fensters, RV-Ziel bis 30 Tage nach Fensterende (DEC-96 E2). SE_W = max(SD * sqrt(c / n_W),
SE_null(n_W)).

**Referenz (bindend): BTC, S1, pi-2 zentral (Prior 9,47 Vol-Punkte)**

| L | SE W3 / W4 | Fenster-Power P-1 | DEC-52-Gate Produkt (exakt) | MDE80 C10 / Gate | P-1 | A3-Praxis (Power, Gate) |
|---|---|---|---|---|---|---|
| 6 | 7,28 / 7,34 | 0,366 / 0,362 | 0,105 (0,222) | 18,1 / 17,4 | **GL012** | GL012 (0,118; 0,030) |
| 9 | 5,96 / 5,95 | 0,477 / 0,478 | 0,223 (0,359) | 14,8 / 14,2 | **GL012** | GL012 (0,184; 0,083) |
| 12 | 5,17 / 5,16 | 0,575 / 0,575 | 0,359 (0,491) | 12,9 / 12,3 | **GL012** | GL012 (0,257; 0,164) |

-> **kein L in {6, 9, 12} -> H-27 GL-012 vor der Registrierung (DEC-96 E2).**

**Gabelungen (Bericht; Richtung jeweils angegeben):**

| Lesart | Richtung | L = 6 | L = 9 | L = 12 |
|---|---|---|---|---|
| pi-2 unterer Bandrand (7,00) | Strenge | GL012 | GL012 | GL012 |
| pi-1 (10,48) | Testbarkeit | GL012 | GL012 | GL012 (Power 0,65; Gate 0,48) |
| pi-2 oberer Bandrand (13,72) | Testbarkeit | GL012 | GL012 (0,74) | **C10** (0,844; A3 GL012 -> nur durch DEC-94) |
| c nur Bartlett (17,8), pi-2 zentral | Testbarkeit | GL012 | GL012 | GL012 (0,73; Gate 0,64) |
| c nur Bartlett, pi-1 | Testbarkeit | GL012 | GL012 | **C10** (0,807; A3 GL012) |
| c nur Bartlett, pi-2 oben | Testbarkeit | GL012 | **C10** (0,894) | C10 |
| Monatsvariante (12 Werte je Jahr, c_m 1), pi-2 zentral | - | GL012 | GL012 | GL012 (0,54) |
| S3 Log / S2 Varianz, pi-2 zentral | - | GL012 | GL012 | GL012 |
| ETH-Bein / Tagesmittel (ETH-Prior UNBELEGT) | Testbarkeit | GL012 | GL012 | GL012 (oberer Bandrand: C10) |

Bei zentralem Prior noetige Fensterlaenge je Fenster (Nuisance-SE, c bindend): BTC S1 **672 Tage C10 / 736 Tage
DEC-52**; S3 724 / 792; Tagesmittel S1 643 / 704; mit Bartlett-c (17,8) BTC S1 ~425 Tage C10 [abg.:
(2,4865 * 18,60 * sqrt(17,81) / 9,47)^2]. Informativ: eine Fensterlaenge ueber 12 Monate sieht DEC-96 E2 nicht vor; sie
waere eine neue Entscheidung nach Kenntnis dieser Feasibility (Etikett), keine Folgerung aus ihr.

**Stopp-Regel P-9 ausgewertet:** Referenz GL012 bei allen L -> Stopp; Stufe 2 (Entscheidungsvorlagen, Erstfassung)
nicht erstellt. Zusaetzlich liegt der obere Prior-Bandrand bei L = 12 auf der C10-Seite -> "haengt am UNBELEGTEN
Niveau" (blockiert ebenfalls).

## 6. Offene / UNBELEGTE Punkte (Stand 2026-10-17)

| Punkt | Status | Wirkung |
|---|---|---|
| IV-Niveau der L-1-Stichprobe (Umrechnung 0,14 -> Vol-/Log-Einheiten) | UNBELEGT (Band) | entscheidet zwischen GL012 (zentral) und C10 (oberer Rand) bei L = 12 |
| L-1 Volltext (Definition, Einheit) | nicht einsehbar (Egress) | Prior-Zeile |
| ETH-Prior | UNBELEGT | Bein-Mittel nur Bericht |
| nu der Nullwelt | am Gitterrand, schwach identifiziert | nur J/SE_null; Nuisance-SE bindet ueberall |
| Underlying Bybit-Perp gegen Deribit-Index | nicht gemessen (wuerde Fenster-RV verlangen) | Bericht im Lauf |
| Bybit-Tagesschluss bei gleichen Zeitstempeln | Gleichstand am letzten Zeitstempel (z. B. 37 Trades in derselben Sekunde 2022-11-09) per Dateireihenfolge aufgeloest; fuer Live-Frames (`data[]`) ist die gleiche Regel festzulegen | Lauf-Lader |

---

## Anhang A - Stand 2026-10-13 (UEBERHOLT durch DEC-96, unveraendert belassen)

Ueberholt sind: Abschnitt A-0/A-1 (Datenstand: Luecken inzwischen geschlossen), die W1/W2-Fenster (P-4: n_W 335/365;
ersetzt durch W3/W4 nach DEC-96 E2) und die W1/W2-Zuordnung. Die Prior-Tabelle (A-2) und die Regeln P-1..P-3,
P-5..P-9 (A-3) gelten und wurden oben angewendet.

> ENTWURF der Herleitung, Stand 2026-10-13. Nichts hier ist registriert oder beschlossen; entscheiden und registrieren
> darf nur der Orchestrator. Keine RV ab 2024-06-01, keine DVOL-Niveau-Statistik ab 2024-07-01, kein Praemienmittel
> berechnet; keine Siegeldatei, keine WP-10(A2)-/WP-10(A)-IV-RV-Datei, kein Inhalt der WP-9-Differenzserie geoeffnet.
> Kuerzel: `[fj]` = `feasibility.json` (gleicher Ordner); `[S:<datei>]` = Skript unter `scratchpad/h27_herleitung/`;
> `[sek]` = Sekundaerbeleg; `[abg.]` = hier abgeleitet; UNBELEGT = keine Fundstelle, blockiert.

### A-0. Befund in Kuerze

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

### A-1. Was die Fortsetzung braucht (Datenstand)

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

### A-2. Prior (datenunabhaengig, Literatur vor 2024-07)

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

### A-3. Vorab fixierte Rechenregeln (vor jeder Nuisance-Zahl, bindend fuer die Fortsetzung)

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

### A-4. Offene / UNBELEGTE Punkte

| Punkt | Status | blockiert |
|---|---|---|
| DVOL 2021-03-24..2025-07-31 im Katalog | fehlt (angekuendigt) | alles Weitere |
| DVOL 2025-09-01..2026-03-19 (W2-Luecke) | fehlt, nicht bestellt | W2, Registrierung |
| L-1 Volltext (Definition, Einheit, Niveau) | nicht einsehbar (Egress) | Prior-Zeile der Registrierung |
| IV-Niveau der L-1-Stichprobe | UNBELEGT (Band) | Umrechnung in S1/S3 |
| ETH-Prior | UNBELEGT | Bein-Mittel A1 als bindende Variante |
| Nuisance-SD, c, Jensen-J, SE_null | nicht gerechnet | Power, Zuordnung |
| Underlying-Abweichung Bybit-Perp gegen Deribit-Index | nicht messbar ohne Fenster-RV | Bericht im Lauf |
