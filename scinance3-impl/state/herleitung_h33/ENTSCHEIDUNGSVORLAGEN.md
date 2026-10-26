# Entscheidungsvorlagen H-33: beta-neutrales Kurzfrist-Reversal (1, 2, 4 Wochen) auf W1/W2 mit Literatur-Prior (DEC-102, Option (a))

> **NICHT REGISTRIERT, kein Verdikt.** Herleitung (Gate-Design, Power, Rauschboden) nach `SPEC_H33_herleitung` vom 2026-10-26.
> Registrieren darf nur der Orchestrator.
> **Etikett (DEC-102 E2, Pflicht):** "beschlossen nach Kenntnis von GL-035 (Pilot-Vorzeichen der mom-Varianten); Richtung
> Testbarkeit; Richtungswahl nach Kenntnis korrelierter Daten eines anderen Fensters (2022-04..2024-06)".
> **Ergebnisblind:** keine Datenrechnung mit Outcome, kein Panel geladen, kein Harvest-Client, W1/W2 nicht geoeffnet,
> Siegeldateien nie geoeffnet (auch nicht `state/runs/wp7_20260921/weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`,
> `weekly_sigma_xs_sigma_ls.csv` im selben Ordner). Gelesen: v6b-Artefakt (Nuisance), registrierte H-32-YAML, GL-035
> (nur Etikett und Streuungszahlen), WP-7-Spread-Zensus (Zaehlungen, Median-Spreads), Literaturakten und Textextrakte.
> **Fundstellen:** `[fj: <datei>#<json-pfad>]`; `power_h33.json` (sha256 `026494b6681fb3d5b97d0e2cf77c9845b953bde7e31e97f976bbf3207b5b5bc9`)
> und `nuisance_neg.json` (sha256 `05e6f2a0a396d0be008579e6d160147c2002d7229a176a01c0f2c1b2076f0835`) in diesem Ordner,
> v6b = `state/runs/h32_20261021_v6b/h32_prelaunch.json` (sha256 `f872a3af...f98c`) und `h32_prelaunch_p_replicates.json`
> (sha256 `3c498e07...56ef`). Beide JSON zweimal gerechnet, bitgleich; Skript `scratchpad/h33_herleitung/h33_compute.py`
> (ausserhalb des Repos, sha256 im JSON-Kopf), alle Power-/MDE-/Zuordnungszahlen mit `power_p1` und `h32_fm8.estimators`.

---

## 0. Befund in Kuerze

1. **Prior: UNBELEGT.** Die Literatur liefert fuer "Kurzfrist-Reversal, Wochenhorizont" ein Band, dessen Vorzeichen am
   Universum haengt: klein/illiquide +0,039..+0,048 (fm8-Skala, Weg A*), breit/gleichgewichtet ~0..+0,014, gross/liquide
   -0,015..-0,026 (Momentum). Die Zuordnung des Bybit-USDT-Perp-Universums zu einer Gruppe ist aus der Akte nicht belegbar
   (kein USD-Umsatz, keine Marktkapitalisierung). **Registrierung blockiert; Rueckfrage an den Nutzer mit dem Prior-Gitter**
   (Abschnitt 2.6). Empfohlene Referenz-Lesart (Strenge): R3 "breit, gleichgewichtet" -> alle drei Varianten GL-012.
2. **MDE80 in negativer Richtung** (nur v6b-Null, Lesart T): W1/W2 mom1 0,0184/0,0161, mom2 0,0202/0,0176, mom4
   0,0236/0,0200 ((1b) bindet ueberall). Mit der GL-035-Streuung als Nuisance (Lesart S, DEC-94 (5)): 0,0395/0,0389,
   0,0418/0,0418, 0,0429/0,0431.
3. **K = 3** (rev1, rev2, rev4), keine Zusatzvariante (EV-2).
4. **v7: ja, wenn nach der Nutzerentscheidung ein Eintrag zuordnungsfaehig ist** - die in negativer Richtung bindende Zelle
   ist die driftfreie, deren Replikate v6b verworfen hat (EV-4). Die Power-Zeile selbst ist aus v6b rechenbar.
5. **PK-Welt / Power-Nuisance:** Lesart S empfohlen (GL-035-Streuung als reine Streuungs-Nuisance, Richtung Strenge).
6. **Neuer C.17-Befund (EV-0):** Die Persistenz-Null W1/W2 der Drittfassung (AR(1) je Symbol auf den Outcome-Renditen)
   ist **in H-33-Richtung** richtungstragend gesehen (W2 deutlich). W1/W2 sind fuer H-33 nicht voll ergebnisblind.

---

## 1. EV-0 - Ergebnisblindheit an der Akte (Grundlage des Etiketts C.17)

Inventur dessen, was fuer W1/W2 und fuer die Statistik (fm8-IC von mom1/mom2/mom4) je gesehen wurde, **mit Richtung fuer
H-33** (Reversal = negative Richtung):

| # | Gesehen | Quelle | Richtung fuer H-33 |
|---|---|---|---|
| C-1 | **Pilot GL-035** 2022-04-18..2024-06-17: fm8-IC x_P mom1/mom2/mom4 -0,038/-0,050/-0,045 (t -3,3/-4,1/-3,6), rev_gap +0,017 (t 1,53); SD_P, SE_P, F2_real 0,0103/0,0120/0,0131, k_pred, c_real 1,000 | `gate_log.md` GL-035, `state/runs/h32_pilot_v1/h32_pilot.md` | **mit** der Richtung (Anlass der Richtungswahl, DEC-102 E2); anderes Fenster, korrelierte Statistik; Pilotabschnitt verbraucht (DEC-99 (5)) |
| C-2 | **Persistenz-Null W1/W2** (v5d/v5e; AR(1) je Symbol auf den **Wochenrenditen der Fenster** = Outcomes, Roh-IC): Median phi 0,00, Q25 -0,04 (W1) / -0,09 (W2); Null-Mittel mom1/2/4 -0,0036..-0,047 (positive Richtung); q95 positive Richtung mom1 -0,0064 / **-0,0362**, mom2 +0,0074 / -0,0094, mom4 +0,0081 / -0,0064 | `hypothesis_registry.md` Z. 111-121 (Zweitfassung), `herleitung_h28_h30_v3/DRITTFASSUNG_H28_H30_entwurf.md` Z. 156-168; H-32 EV C-12 | **mit** der Richtung (in negativer Richtung Null-Mittel +0,004..+0,047; W2 mom1: das ganze 95-%-Band der Null liegt im Reversal). Modellbasiert, Roh-IC (nicht fm8), Kendall-Anteil ~ -1/T je Symbol; fuer H-32 "gegen die Richtung" und daher unschaedlich - **fuer H-33 nicht** |
| C-3 | v6b-Nuisance W1/W2/P: sigma_f, rho_f, Faktoranteil, beta_sd, Null-Mittel und -Quantile je Zelle, se_mean, e_se_rule, sd_week, K-Reihen, floor/v, Stress-Zaehlungen | `[fj: h32_prelaunch.json#windows]` | Null-Mittel der mom-Varianten positiv (mechanisches Momentum) = **gegen** H-33; Streuungen richtungsfrei |
| C-4 | WP-7 B3: Survivorship-Differenz des rohen 4-Wochen-Momentum-IC IC_union - IC_survivors +0,0033 [-0,0076; +0,0132], 271 Wochen (ganze Historie) | `state/runs/wp7_20260921/wp7_report.md` Z. 15 | Union zeigt mehr Momentum = **gegen** H-33 (klein, insignifikant) |
| C-5 | Survivorship-Fixture (synthetisch) | `[fj: nuisance_neg.json#windows.<W>.variants.<v>.survivorship]` | unkontrolliert **mit** H-33 (+0,47..+0,70 T_neg); registriert ist `close_at_last` |
| C-6 | Literatur: Ficura (Reversal klein/illiquide, Momentum gross seit 2021 unprofitabel), LTW, Bianchi, Dobrynskaya [sek] | `BELEGE_AUS_PDF_2026-10-20.md` 2-4, 8 | uneinheitlich (Abschnitt 2) |
| C-7 | WP-7-Spread-Zensus (Schnappschuss 2026-09, nach dem Siegel): 886 Kontrakte, Median-Spread je Umsatzdezil 1,6..36,2 bp | `[fj: power_h33.json#spread_zensus]` | richtungsfrei (keine Rendite) |
| C-8 | A1-/H-27-/HF-RV-/A2-Groessen (BTC-Wochen-SD W1/W2, Funding-Spreads, psi, VRP-Nuisance, Verfallskalender); DEC-100 N1 Listen/Zaehlungen, Tagesschluss-Gleichheit bis 2026-09-14 (Zaehlung) | DEC-85, DEC-93, DEC-98 N5, DEC-100 N1 | richtungsfrei fuer den Querschnitts-IC |
| C-9 | Vorwissen der Agenten ueber Marktniveaus 2022-2026 | - | nicht quantifizierbar, nicht verwendet |

Nie geoeffnet: L-IC-Details v5c/v5d/v5e (Siegel), WP-7-Rohserie des 4-Wochen-Momentum-IC, die Pilot-Wochenreihen
(`h32_pilot_*_P_ic_weekly.csv`) und `h32_pilot.json` (diese Herleitung). Nie berechnet: realer fm8-IC oder roher IC in W1/W2.

**Vorlage EV-0 (offen, Nutzer-relevant):** C-2 ist fuer H-33 ein richtungstragender Vorab-Hinweis auf die Eigen-
Autokorrelation der Outcomes, vor allem in W2. Optionen:
- (a) **Etikett und weiter** (DEC-102 E2 ergaenzen: "zudem Persistenz-Null W1/W2 in Richtung gesehen"); Richtung Testbarkeit.
- (b) **Strenge Lesart:** W1/W2 gelten fuer die Reversal-Richtung nicht als ergebnisblind; H-33 waere dann nur auf blinden
  Fenstern ab 2026-07-01 konfirmatorisch - das beruehrt die offene Reihenfolge-Frage (DEC-98 E4 (b)), also Nutzer.
- **Empfehlung:** (a) nur mit ausdruecklicher Nutzerkenntnis - der Befund gehoert in dieselbe Rueckfrage wie der Prior
  (Abschnitt 7). Der Orchestrator entscheidet nicht still (Autonomie-Protokoll 3).

---

## 2. EV-1 - Prior aus der Literatur (Kern)

### 2.1 Quellen (Stichprobe vor 2024-07; Volltext gelesen, wo [PDF])

| Quelle | Universum / Konstruktion | Wochenhorizont-Befund (Q5-Q1 bzw. FM) | Fundstelle |
|---|---|---|---|
| Ficura 2023 [PDF] | CMC-Spot 2017/06-2022/12, gleichgewichtet, Quintile, NW-t; **klein/illiquide** = Marktkap. 1-50 Mio USD oder Wochenvolumen < 5 Mio USD | 1W -3,91 % (t -7,31), 2W -3,35 % (-6,35), 4W -3,15 % (-6,77); BTC-alpha 1W -3,90 % (-7,59) | S. 8 Tab. 3; S. 11 Tab. 5 |
| dto. | **gross/liquide** (>= 50 Mio, >= 5 Mio) | 1W +1,36 % (2,33), 2W +1,44 % (2,69), 4W +0,84 % (1,57) - Momentum; "seit Anfang 2021 nicht mehr profitabel" | S. 8 Tab. 3; S. 7 |
| dto. | **breit** M > 1 Mio, V > 100 Tsd. | 1W -0,12 % (t -0,22), 2W -0,15 % (-0,30), 4W -0,50 % (-1,05) | S. 13 Tab. 7 A, Sp. 1 |
| dto. | M > 10 Mio, V > 1 Mio | 1W +1,44 % (2,08), 2W +1,77 % (2,48), 4W +1,13 % (1,95) - Momentum | S. 13 Tab. 7 A, Sp. 2 |
| dto. | M > 1 Mio, **V < 100 Tsd.** | 1W -3,06 % (-5,93), 2W -2,58 % (-5,12), 4W -2,58 % (-5,70); "Reversal getrieben von sehr niedrigem Volumen" | S. 13-14 Tab. 7 B, Sp. 1 |
| Liu/Tsyvinski/Wu NBER 2019 [PDF] | CMC 2014-2018; FM gleichgewichtet, Regressor Quintilsnummer, > 1 Mio USD | r1 -0,002 (t -0,69), r2 0,000 (0,02), r4 -0,001 (-0,27) | S. 32 Tab. 13 D |
| dto. | wertgewichtet, Quintil-Long-Short | 1W +0,027 (t 1,99), 2W +0,033, 4W +0,025 - Momentum | S. 13 Tab. 4 |
| Bianchi/Babiak/Dickerson [PDF] | Top-100 liquide USD-Paare 2017-03..2022-03 | **1-Tages**-Reversal: abg. Tages-IC 0,090 (gleichgew.) / 0,023 (wertgew.); Wochenhorizont **UNBELEGT** | S. 24-25; BELEGE 4 |
| Dobrynskaya [sek] | 2.000 groesste Coins 2014-2020 | Momentum 2-4 Wochen, Reversal erst nach ~1 Monat; Zahlen UNBELEGT (PDF fehlt) | RECHERCHE 1.1 Q1-2 |
| Shen/Urquhart/Wang 2020 | nur ueber Ficura S. 3-4: woechentliches Reversal (gleichgew., ohne Mindest-Marktkap.) | keine Zahl im Textextrakt: **UNBELEGT** | Ficura S. 3-4 |

### 2.2 Umrechnung in den Rang-IC (zwei Wege, je mit Richtung)

- **Weg A\*** (BELEGE 4, hier verallgemeinert): `IC_n = S_r(n) / S_x(1W)` der Gruppe; S_x(1W) aus Ficura Tab. 5 (Mittel der
  Signal-Quintile 5 minus 1): klein/illiquide 0,609, gross/liquide 0,414. Annahme: Querschnitts-SD der Folgewochenrendite =
  die der Vorwochenrendite derselben Gruppe (Normalitaet, Quintile; k = 2,800 kuerzt sich). Fuer 2W/4W gilt dieselbe
  Ergebnis-Streuung (Folgewoche). **Richtung: Mittelwert unter Normalitaet; eher Testbarkeit** (Spreads in Krypto stark
  ausreissergetrieben; Ficura winsorisiert erst bei 1000 %).
- **Weg B** (RECHERCHE 1.2): `IC = (t / sqrt(N)) x SD(IC_t)` mit N ~ 291 Wochen [abg.] und **SD = v6b-Null-Wochen-SD**
  `sd_week` je Fenster/Variante. **Richtung: Untergrenze (Strenge)** - die reale SD liegt ueber der Null-SD (GL-035
  Nebenbefund); die Pilot-SD einzusetzen ist ausgeschlossen, weil der Pilot dann die Groesse des Priors mitbestimmte
  (DEC-102 E3).
- **Weg FM** (LTW): `IC ~ b x sqrt(2) / sigma_xs`, sigma_xs in {0,148; 0,182; 0,25} (Anker BELEGE 4).
- **Rang-Faktor** 0,955 (Spearman vs. Pearson, kleiner IC): Strenge, als Variante ausgewiesen.
- **fm8-Skala** x 0,754 (synthetisch fuer mom1, `power_h32.json#fm8_daempfung`); mom2/mom4 vermutlich staerker gedaempft ->
  dort **Obergrenzen (Testbarkeit)**. Die Beta-Neutralisierung selbst aendert die Spreads kaum (Ficura BTC-alpha -3,90 %
  vs. roh -3,91 %; LTW 1W-Beta -0,021, R^2 0,000).

### 2.3 Lesarten (Rang-IC in Reversal-Richtung; fm8-Skala = x 0,754) `[fj: power_h33.json#umrechnung.variants.<v>.fm8_skala]`

| Lesart | Universums-Analogon | rev1 (mom1) | rev2 (mom2) | rev4 (mom4) | Richtung |
|---|---|---:|---:|---:|---|
| R1 A\* | Ficura klein/illiquide | 0,0484 (Rang 0,0462) | 0,0415 (0,0396) | 0,0390 (0,0373) | Testbarkeit |
| R1 B | dto., Weg B (W1-SD / W2-SD) | 0,0166 / 0,0144 | 0,0160 / 0,0135 | 0,0198 / 0,0164 | Strenge innerhalb R1 |
| R2 A\* | Ficura V < 100 Tsd. USD/Woche | 0,038..0,056 | 0,032..0,047 | 0,032..0,047 | Testbarkeit (Extrem) |
| R3 A\* | Ficura breit (M > 1 Mio, V > 100 Tsd.) | 0,0015..0,0022 | 0,0019..0,0027 | 0,0062..0,0091 | Mitte |
| R3 FM | LTW FM > 1 Mio (gleichgew.) | 0,0085..0,0144 (t -0,69) | 0,000 (t 0,02) | 0,0043..0,0072 (t -0,27) | Mitte |
| R4 A\* | Ficura gross/liquide | -0,0248 | -0,0262 | -0,0153 | gegen H-33 |
| R4 A\* | Ficura M > 10 Mio, V > 1 Mio | -0,026..-0,018 | -0,032..-0,022 | -0,021..-0,014 | gegen H-33 |

Weg-B-Werte zu R3 liegen bei ~0..0,0031 (fm8; Ficura breit 0,0005/0,0008/0,0031, LTW-FM 0,0017/~0/0,0008 mit W1-SD), alle
Quellen von R3 sind insignifikant.

### 2.4 Zuordnung des Bybit-Universums (nur Zaehlungen)

- Bybit lineare USDT-Perps lebend (v6b, alive): W1 343/416,5/500, W2 501/526/545 `[fj: h32_prelaunch.json#windows.W1.k]`.
- WP-7-Spread-Zensus: 886 Kontrakte in 10 Umsatzdezilen, Median-Spread D1 1,62 bp .. D10 36,21 bp; **kein USD-Umsatz,
  keine Marktkapitalisierung** `[fj: power_h33.json#spread_zensus]`. Ficuras Gruppengrenzen (Wochenvolumen 100 Tsd. / 5 Mio
  USD, Marktkap. 1/10/50 Mio USD, CMC-Spot-Aggregat) sind damit nicht anwendbar: **UNBELEGT**.
- Indiz (kein Beleg): In der Zahl entsprechen ~500 Kontrakte den CMC-Coins ueber ~10..50 Mio USD Marktkapitalisierung Ende
  2021/2022 (Ficura Tab. 1, S. 5: > 10 Mio 1.083 / 684, > 50 Mio 601 / 315) - also eher Tab. 7 A Spalte 2/3 (Momentum)
  als der Reversal-Treiber V < 100 Tsd. USD. Anderer Zeitraum, Spot statt Perp: nur Richtungs-Indiz (gegen R1, Strenge).
- Ein Universum aller gelisteten Perps, gleichgewichtet im Rang-IC, ist konstruktiv am naechsten an Ficura "breit" und
  LTW-FM (gleichgewichtet, Mindestgroesse) - also **R3**.

### 2.5 Empfehlung und was UNBELEGT bleibt

- **Status: UNBELEGT** (blockiert die Registrierung, Arbeitsregel 4 / DEC-102 E3). Gruende: (u1) Universums-Zuordnung
  ohne USD-Umsatz/Marktkap.; (u2) A\*/B-Luecke Faktor ~2,5..3 fuer dieselbe Quelle; (u3) fm8-Daempfung fuer mom2/mom4
  nicht gemessen; (u4) Stichproben 2014-2022 (Spot) gegen 2024-2026 (Perps), Ficura: Regimewechsel 2021 fuer Momentum;
  (u5) Shen/Urquhart/Wang, Dobrynskaya, Zaremba ohne Zahlen; Bianchi nur Tageshorizont.
- **Empfohlene Referenz-Lesart (Richtung Strenge): R3 "breit, gleichgewichtet"**, Punkt = oberer R3-Wert je Variante
  (rev1 0,0144 LTW-FM, rev2 0,0027 Ficura, rev4 0,0091 Ficura). Folge: alle drei **GL-012** unter Lesart T und S
  `[fj: power_h33.json#power_an_literatur_lesarten]`.
- **Gegenlesart R1 A\* (Testbarkeit):** rev1/rev2/rev4 0,048/0,041/0,039 -> unter T alle C10, unter S nur rev1 C10. R1
  faellt in der Groessenordnung mit dem verbrauchten Pilot zusammen (GL-035); eine Wahl von R1 waere von einer
  pilotgeleiteten Wahl nicht unterscheidbar -> nur mit Nutzerentscheid und Etikett "Prior-Lesart nach Kenntnis von GL-035".

### 2.6 Prior-Gitter (Pflicht bei UNBELEGT) `[fj: power_h33.json#power_lines.<T|S>.variants.<v>.grid]`

Fenster-Power W1 / W2, gemeinsam (Produkt), Zuordnung `power_p1.assign_regime` (P-1, (1c) eingerechnet), A3-Praxis, Endpower
nach F-WEEK m = 3 / m = 14 (`estimators.end_power_replicates`, Replikat-Quantile in negativer Richtung, strenge Untergrenze).

| Variante | Prior | Lesart T: W1 / W2 / gem. / Regime / A3 / EP m3 / EP m14 | Lesart S: W1 / W2 / gem. / Regime / A3 / EP m3 / EP m14 |
|---|---:|---|---|
| rev1 | 0,010 | 0,380 / 0,442 / 0,168 / GL012 / GL012 / 0,059 / 0,005 | 0,148 / 0,157 / 0,023 / GL012 / GL012 / 0,005 / 0,000 |
| rev1 | 0,015 | 0,647 / 0,746 / 0,483 / GL012 / GL012 / 0,268 / 0,053 | 0,234 / 0,246 / 0,058 / GL012 / GL012 / 0,016 / 0,001 |
| rev1 | 0,020 | 0,856 / 0,929 / 0,795 / **C10** / GL012 (nur DEC-94) / 0,610 / 0,249 | 0,342 / 0,357 / 0,122 / GL012 / GL012 / 0,043 / 0,003 |
| rev1 | 0,025 | 0,960 / 0,989 / 0,949 / **C10** / C10 / 0,869 / 0,586 | 0,465 / 0,481 / 0,224 / GL012 / GL012 / 0,096 / 0,011 |
| rev1 | 0,033 | 0,998 / 1,000 / 0,998 / **C10** / C10 / 0,990 / 0,936 | 0,664 / 0,679 / 0,451 / GL012 / GL012 / 0,256 / 0,053 |
| rev1 | 0,048 | 1,000 / 1,000 / 1,000 / **C10** / C10 / 1,000 / 1,000 | 0,917 / 0,923 / 0,846 / **C10** / GL012 (nur DEC-94) / 0,698 / 0,345 |
| rev2 | 0,010 | 0,339 / 0,407 / 0,138 / GL012 / GL012 / 0,048 / 0,004 | 0,143 / 0,144 / 0,021 / GL012 / GL012 / 0,005 / 0,000 |
| rev2 | 0,015 | 0,580 / 0,683 / 0,396 / GL012 / GL012 / 0,205 / 0,036 | 0,221 / 0,223 / 0,049 / GL012 / GL012 / 0,013 / 0,001 |
| rev2 | 0,020 | 0,794 / 0,882 / 0,700 / **DEC52** (Gate 0,811) / GL012 (nur DEC-94) / 0,495 / 0,171 | 0,320 / 0,322 / 0,103 / GL012 / GL012 / 0,034 / 0,002 |
| rev2 | 0,025 | 0,925 / 0,971 / 0,898 / **C10** / GL012 (nur DEC-94) / 0,776 / 0,445 | 0,433 / 0,435 / 0,189 / GL012 / GL012 / 0,076 / 0,008 |
| rev2 | 0,033 | 0,992 / 0,999 / 0,991 / **C10** / C10 / 0,971 / 0,858 | 0,623 / 0,624 / 0,389 / GL012 / GL012 / 0,206 / 0,037 |
| rev2 | 0,048 | 1,000 / 1,000 / 1,000 / **C10** / C10 / 1,000 / 0,999 | 0,888 / 0,888 / 0,788 / **C10** / GL012 (nur DEC-94) / 0,614 / 0,263 |
| rev4 | 0,010 | 0,290 / 0,351 / 0,102 / GL012 / GL012 / 0,034 / 0,003 | 0,143 / 0,142 / 0,020 / GL012 / GL012 / 0,004 / 0,000 |
| rev4 | 0,015 | 0,483 / 0,590 / 0,285 / GL012 / GL012 / 0,133 / 0,020 | 0,219 / 0,217 / 0,048 / GL012 / GL012 / 0,012 / 0,001 |
| rev4 | 0,020 | 0,681 / 0,799 / 0,544 / GL012 / GL012 / 0,339 / 0,091 | 0,314 / 0,311 / 0,098 / GL012 / GL012 / 0,031 / 0,002 |
| rev4 | 0,025 | 0,837 / 0,926 / 0,775 / **C10** / GL012 (nur DEC-94) / 0,599 / 0,263 | 0,423 / 0,419 / 0,177 / GL012 / GL012 / 0,067 / 0,006 |
| rev4 | 0,033 | 0,964 / 0,992 / 0,957 / **C10** / C10 / 0,893 / 0,663 | 0,606 / 0,602 / 0,365 / GL012 / GL012 / 0,183 / 0,030 |
| rev4 | 0,048 | 1,000 / 1,000 / 1,000 / **C10** / C10 / 0,998 / 0,984 | 0,873 / 0,870 / 0,759 / **C10** / GL012 (nur DEC-94) / 0,568 / 0,223 |

Regime nach P-1 (6); mit EV-6 (nur C10) wird DEC52 zu GL-012. Mindest-Prior fuer C10 (= MDE80\*): Lesart T rev1 0,0184, rev2 0,0202, rev4 0,0236; Lesart S 0,0395, 0,0418, 0,0431
`[fj: power_h33.json#power_lines.<T|S>.variants.<v>.min_prior_c10]`. Endpower: "gate_method_bericht" (BY nur auf p) und
Normalnaeherung stehen report-only im JSON.

---

## 3. EV-2 - Varianten und K

| Option | Inhalt | Richtung | Bewertung |
|---|---|---|---|
| **K = 3 (empfohlen)** | rev1, rev2, rev4 = mom1/mom2/mom4 in negativer Richtung, Rahmen DEC-102 E1 | neutral (Rahmen) | Selektionsdecke z_max(3) = 0,853 < 1,6449 `[fj: power_h33.json#selection]`; BH-Nenner 3 |
| + 2-Wochen-Reversal mit 1-Wochen-Gap (Jegadeesh/Dobrynskaya-artig) | Charakteristik r_(t-2)+r_(t-1) | Testbarkeit (mehr Chancen) | enthaelt die rev_gap-Woche t-1 (Korrelation der Charakteristiken ~0,7 unter iid) - Naehe zu der nach DEC-102 E4 ausgeschlossenen Statistik (C.1); **nicht empfohlen** |
| + Universum "klein/illiquide" (z. B. Umsatz-Bucket 1-2) | eigenes Universum je Horizont, K = 6 | Testbarkeit (hoeherer Literatur-Prior R1/R2), aber K_t ~80..110 -> Boden ~0,1/sqrt(W), MDE80 >= ~0,035 schon unter der Null-SD | keine v6b-Nuisance (neuer Vorlauf noetig), Liquiditaets-Wahl nach Literatur und nach GL-035; Tradability fraglich (D10-Spread 36 bp); **nicht empfohlen** |
| + Universum "liquide" (ohne Bucket 1) | Gegenstueck | Strenge | Prior noch kleiner (R3/R4); nur Etikett (wie H-32) |

`rev_gap` bleibt ausgeschlossen (DEC-102 E4). Jede gerechnete Variante zaehlt in K, BH-Nenner und Selektionsdecke.

---

## 4. EV-3 - Streuungs-Nuisance der Power-Zeile und Welt der Positivkontrolle (ohne Pilot)

DEC-94 (5): SD der Teststatistik aus beiden Quellen, soweit verfuegbar (Vorperiode, nur Streuung; Null-Simulation),
**bindend ist die groessere SE**; die PK ist NICHT BESTANDEN, wenn ihre Welt-SD > 1,10 x SD der Power-Zeile.

| Lesart | Power-Zeile | PK-Welt | Richtung | Folge |
|---|---|---|---|---|
| **T** | SE_T = e_se_rule, SD_T = se_mean (v6b-Null), k_pred = 1 | F2_ref := F2_null (sigma_g = 0), Ziel F mit k_pred = 1 | **Testbarkeit** | MDE80\* 0,018..0,024. Traegt der GL-035-Befund (reale Wochen-SD ~2,2..2,5 x Null-SD) nach W1/W2, skaliert der Test k automatisch (DEC-101 E2) - die Fehlerrate ist geschuetzt, aber die reale Power faellt auf die Werte von S (z. B. rev1 bei 0,025: gemeinsam 0,95 -> 0,22). Die 10-%-Regel der PK waere leer (Welt = Null-Welt). |
| **S (empfohlen)** | SE_W,Pilot = sqrt(c_real) sqrt(v_fm8_W + F2_real) / sqrt(W) mit F2_real aus GL-035; SE_T = max(e_se_rule, SE_W,Pilot), SD_T = max(se_mean, SE_W,Pilot); k_pred = max(1, sqrt(v_fm8 + F2_real) / sd_week) im (1c)-Term | Welt-SD-Ziel sqrt(v_fm8 + max(F2_null, F2_real)), Ziel F mit k_pred (wie H-32 E8) | **Strenge** | MDE80\* 0,040..0,043; PK realistisch (Produktionskonfiguration inkl. Querschnitts-Abhaengigkeit) |

Begruendung S: (i) DEC-94 (5) (i) laesst Streuung und Autokorrelation einer Vorperiode ausdruecklich zu; (ii) DEC-101 Teil 3
fuehrt den Nebenbefund als "Etikett fuer alle Querschnitts-Designs"; (iii) die Streuung ist richtungsfrei (SD von -IC = SD
von IC) und traegt kein Mittel; (iv) der Verbrauch (DEC-99 (5)) betrifft die Blindheit des Pilotabschnitts, nicht die
Zulaessigkeit einer Streuungsgroesse; (v) DEC-102 E3 verbietet den Pilot als Quelle des **Priors** (Lage), nicht der SE.
Gegenargument (Wortlaut): DEC-94 (5) (i) nennt "kein Mittel ausgegeben" - das Pilotmittel ist ausgegeben (GL-035); die
Ausnahme DEC-99 (6) gilt nur fuer Registrierungen mit Pilotfenster. Die Verwendung in Richtung Strenge verschiebt keinen
Torpfosten zugunsten der Hypothese; sie ist als **"Streuungs-Nuisance aus GL-035 (DEC-94 (5) (i)), kein Mittel; beschlossen
nach Kenntnis von GL-035"** zu etikettieren. Alternative ohne Pilot (S2, Bauaufwand gross): Mehrfaktor-Null (Sektor-/PCA-
Faktoren aus der kontemporaeren Kovarianz der W1/W2-Renditen, ohne Charakteristik) in v7 - liefert eine realistische
Null-SD ohne GL-035; offen gelassen.

---

## 5. EV-4 - Umrechnung aus v6b oder Vorlauf v7

Replikate in v6b: die p-Datei enthaelt je Fenster/Variante 10.000 Fenstermittel **der Drift-Zelle** (bindend in positiver
Richtung); die ersten 1.000 reproduzieren Mittel, SD, q95 und `draws_sha256` der Drift-Zelle bitgleich (geprueft,
`[fj: nuisance_neg.json#meta.checks]`). Die 10.000 driftfreien Replikate hat v6b gerechnet und verworfen (`vorlauf.py`).

**Bindende Zelle in negativer Richtung:** null_mean_neg = -null_mean_raw; groesser ist die **driftfreie** Zelle in allen
sechs Faellen (z. B. W1 mom1 -0,001221 gegen -0,001290) `[fj: nuisance_neg.json#windows.<W>.variants.<v>.binding_cell_neg]`.
Grund: Drift (beider Vorzeichen) und Markt-Persistenz erzeugen mechanisches Momentum, also gegen Reversal; driftfrei ist die
strengere Lage. Unter DEC-101 E2 gibt es bei m < 0 keine Gutschrift (q95_eff = k (q95 - m)); es zaehlt dann nur die Form
der Zelle.

| Groesse (negative Richtung) | aus v6b registrierbar? | Quelle / Grund |
|---|---|---|
| se_mean, e_se_rule, sd_week (richtungsfrei, max der Zellen) | **ja** | `frozen_v6` |
| floor_fm8, v_fm8, K-Reihen-Hashes, Kalibrierung, null_scales, bounce_sigma_true | **ja** (unveraendert) | `windows.<W>` |
| null_mean_neg je Zelle, bindende Zelle (driftfrei) | **ja** | Zellen-Mittel |
| q95_neg und p-Replikate der Drift-Zelle (1.000 / 10.000) | **ja** | -Q_0,05 der p-Datei |
| Selektionsdecke K = 3 der Drift-Zelle | **ja** (gemeinsame Replikate je Simulation) | `signed_selection_ceiling`, Vorzeichen -1 |
| Survivorship mom1 | **ja** (Vorzeichen umgekehrt) | `windows.<W>.survivorship` |
| q95_neg der driftfreien Zelle, eingefrorenes q95_neg nach DEC-101 E5 | **nein** | driftfreie Replikate fehlen |
| p-Replikate der bindenden (driftfreien) Zelle | **nein** | dto. |
| Decke K = 3 der driftfreien Zelle (H-32-Konvention) | **nein** | dto. |
| Survivorship mom2/mom4 | nicht im Artefakt; **ohne Daten reproduziert** (Fixture mit K 417/526 reproduziert v6b mom1 und rev_gap bitgleich) | `[fj: nuisance_neg.json#windows.<W>.variants.mom2.survivorship]` |

Wirkung auf die Zuordnung: unter Lesart T bindet (1b) in allen sechs Fenster/Varianten-Paaren mit 1,4..6,2 % Abstand zu (1c)
(`binding_condition` im JSON) - die Zuordnung haengt dort nicht an der Zelle. Unter S bindet (1c) in vier Paaren um 0,3..2,5 %
(W1 rev1, W1/W2 rev2, W2 rev4); dort bewegt die Zellwahl die Schwelle nur in dieser Groessenordnung.

| Option | Inhalt | Richtung | Empfehlung |
|---|---|---|---|
| **v7 (empfohlen, falls nach der Nutzerentscheidung ein Eintrag zuordnungsfaehig ist)** | v6b-Null W1/W2 erneut (Seed 53, gleiche Kalibrierung aus der YAML), beide Zellen, 10.000 Replikate, **beide** Replikatsaetze gespeichert, Richtung negativ, K = 3; Bruecke: `draws_sha256` der ersten 1.000 je Zelle (Rohrichtung) = v6b, Drift-Zelle 10.000 = v6b-p-Datei; zweimal bitgleich; ~1..1,5 h Cloud | Strenge (exakte Zellregel, Determinismus) | ja |
| v6b-Drift-Zelle mit Etikett | Drift-Zelle statt driftfrei als bindende Zelle registrieren | Richtung unbestimmt (Form-Unterschied der Zellen unbekannt), formal Abweichung von DEC-99 N1 | nein |
| kein v7 | wenn alle Eintraege GL-012 vor der Registrierung sind (Referenz-Lesart) | - | entfaellt dann |

---

## 6. EV-5 - Gate-Details in negativer Richtung

- **(1b)** y_W >= z_krit x SE_W (P-1 (4)); Gutschrift max(0, m) = 0. Report-only: "mechanischer Zug" (y traegt das negative
  Null-Mittel, falls real) - MDE80 + |m| (z. B. W1 rev1 0,0196 statt 0,0184) `[fj: power_h33.json#power_lines.T.variants.mom1.windows.W1.mde80_1b_bericht_mechanischer_zug]`.
- **(1c)** y_W >= q95_eff = max(0, m) + k (q95_neg - m), m < 0 -> k (q95_neg + |m|) (DEC-101 E2, keine Gutschrift). Der
  Wortlaut des Auftrags "(1c) = q95_neg + z_80 x se_mean" ohne Rezentrierung waere milder (W1 rev1 0,0168 statt 0,0181) und
  wird nur berichtet (**Abweichung zur Strenge**).
- **p** aus den transformierten Replikaten d' = max(0, m) + k (d_neg - m) der bindenden Zelle; Max-p W1/W2; BH Nenner 3
  report-only; **F-WEEK BY bindend, m = getestete Eintraege** (H-33 allein: bis 3; BY-Schwelle 0,0182), Doppelausweis alte
  Zaehlung 7 + 4 + 3 = 14 (0,0022).
- **Selektionsdecke** K = 3, Drift-Zelle: roh 0,0019/0,0023 (W1), 0,0017 (W2); rezentriert 0,0035..0,0039 / 0,0031;
  Decke/T <= 0,32 -> kein Vor-Verdikt-Kill `[fj: power_h33.json#pre_verdict_kill]`.
- **Bounce (4b) fuer alle drei** (Strenge gegenueber H-32, wo nur rev_gap): rev1 ohne Gap teilt den Wochenschluss mit dem
  Outcome. Analytisch ist der Bounce-IC winzig (roh -1,1e-4 W1 / -1,8e-4 W2 bei 36,21 bp; <= 1,7 % von T), der Ein-Seed-
  Fixture-Wert des H-32-Codes ist aber Rauschen (SD 0,006..0,007): ein Effekt genau an der Schwelle wuerde mit 2..6,5 % je
  Fenster zufaellig getoetet `[fj: power_h33.json#bounce_fixture_synthetisch]`. **Empfehlung:** Kill gegen das Mittel ueber
  die Seeds 53..252 (SE ~0,0005) - Richtung Testbarkeit gegenueber dem Ein-Seed-Kill, Strenge gegenueber "kein Kill".
- **Liquiditaet:** Etikett wie H-32 (Mittel ohne Umsatz-Bucket 1, "Illiquiditaets-Artefakt" unter 0,5 x T_W). Option
  Kill (Strenge): nicht empfohlen - Reversal als Liquiditaetspraemie ist eine Tradability-Frage (C.2).
- **Survivorship** (synthetisch, Vorzeichen fuer H-33 umgekehrt): +0,47 / +0,59 / +0,49 T_neg (W1 rev1/rev2/rev4),
  +0,58 / +0,70 / +0,64 (W2); in v6b-Einheiten (positive Richtung) mom1 -0,425 / -0,538 -> **+0,425 / +0,538**. Richtung:
  das unkontrollierte Ueberlebenden-Panel erzeugt mechanisches Reversal = **mit** H-33 (Testbarkeit, falls Delistete
  fehlten); registriert ist `close_at_last` auf dem Union-Panel (DEC-100 N1) - Etikett.

## 7. EV-6 - DEC-52-Zweig

P-1 (6) laesst DEC52 zu (Gitter: rev2 bei 0,020 unter T). Das H-32-Paket hat keinen DEC-52-Zweig (Regel U liess nur C10 zu);
ein (1c)-Analogon fuer den gepoolten Schaetzer existiert nicht. Optionen: (a) Zweig bauen (gepoolte Bedingung z 2,5287,
Screens 0,5 x, gepooltes Null-Quantil aus gepaarten W1/W2-Replikaten) - nur wenn der registrierte Prior dort landet;
(b) vorab "nur C10" (wie DEC-87 (F); Strenge). **Empfehlung (b)** fuer H-33, festgelegt vor der Prior-Entscheidung des
Nutzers, mit Etikett "Abweichung von P-1 (6) in Richtung Strenge".

## 8. Gabelungs-Bilanz (DEC-93 H-1)

| EV | Empfehlung | Richtung |
|---|---|---|
| EV-0 Blindheit | Etikett + Nutzerkenntnis | Testbarkeit (Weiterfuehren trotz C-2), offen |
| EV-1 Prior | UNBELEGT; Referenz R3 | Strenge |
| EV-2 K | 3, keine Zusatzvariante | Strenge |
| EV-3 Nuisance/PK | S | Strenge |
| EV-4 v7 | ja (falls zuordnungsfaehig) | Strenge |
| EV-5 (1c) | rezentriert (statt Auftragswortlaut) | Strenge |
| EV-5 Bounce | alle drei, Mehrseed-Mittel | gemischt (s. o.) |
| EV-5 Liquiditaet | Etikett | Testbarkeit gegenueber Kill |
| EV-6 DEC-52 | nur C10 | Strenge |

Sechs Empfehlungen in Richtung Strenge, zwei gemischt/Testbarkeit, eine offen (EV-0). Die einzige Lesart, unter der H-33
testbar wird, ist R1 (Testbarkeit) - und mit S nur fuer rev1.

## 9. Offene Punkte (an den Orchestrator; Nutzer-Rueckfrage nach DEC-102 E3)

1. **Prior UNBELEGT** -> Rueckfrage mit dem Gitter 2.6 und den Lesarten R1/R3 (Vorschlag: R3, dann GL-012 fuer alle drei).
2. **EV-0 / C-2** (Persistenz-Null in H-33-Richtung) in dieselbe Rueckfrage.
3. EV-3 (T/S) vor jeder Prior-Zahl des Nutzers festlegen (sonst Gabelung nach Kenntnis).
4. v7 nur bei zuordnungsfaehigem Eintrag; dann Bauliste (Erstfassung 12).
5. Fehlende PDFs (DEC-102 Anlass): Dobrynskaya, LTW JF 2022, Shen/Urquhart/Wang 2020 - koennten R3/R1 stuetzen oder
   verwerfen; eine Universums-Zaehlung nach USD-Wochenumsatz (Bybit-Kline-Feld `turnover`, nur vor 2024-07 oder als reine
   Zaehlung) wuerde u1 entschaerfen, nicht aufloesen (Perp- statt Spot-Volumen).

## 10. Was nicht folgt

Kein Verdikt ueber Kurzfrist-Reversal; keine Registrierung; GL-035 und DEC-102 unveraendert; W1/W2 nicht geoeffnet; keine
Aenderung an Code oder YAML; die v6b-Zahlen sind nur umgerechnet (Nuisance).
