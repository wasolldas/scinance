## H-31 - Erstfassung (ENTWURF 2026-10-13): A1 Funding-Long-Bein D1 gegen Universums-Hedge, Klasse P, kapitalfrei

> **ORCHESTRATOR-VERMERK 2026-10-13 (DEC-93, GL-033):** Ersetzt durch die Feststellung des Reviews (`REVIEW_A1.md`):
> A1 ist unter den geltenden Beschluessen (DEC-67 E4, fuer A1 bestaetigt in DEC-70 E1: W_eff = 0,41 W) vor der
> Registrierung GL-012 (176,5 > 147,6 bp schon bei theta = 1) und zusaetzlich theta-UNBELEGT. Die Aussage "Stopp-Regel
> greift nicht" unten ist damit hinfaellig; Stufe 2 ist Akte ohne Rechtswirkung. Kein Verdikt ueber den Funding-Carry.

**Status:** ENTWURF der Herleitung, NICHT registriert und **bedingt**. Registrieren darf nur der Orchestrator, nach
adversarischem Review und erst nach den Vorbedingungen in Abschnitt 0. Der Entwurf existiert, weil die Stopp-Regel
der Feasibility (GL-012 bei theta = 1,0) in Konfiguration A mit gemessener SE nicht greift (`FEASIBILITY.md` 8).
**Die strenge Lesart von EV-1 oder EV-2 macht A1 bei jedem theta <= 1 zum GL-012-Fall, EV-3 in der A3-Lesart
(ohne DEC-52-Zweig) ebenso; ohne belegtes theta >= 0,77 (EV-6) ist die Power-Zeile UNBELEGT und die Registrierung
blockiert.**
Fuer diesen Entwurf wurde keine A1-Outcome-Groesse auf Daten ab 2024-07-01 berechnet, keine Siegeldatei geoeffnet und
kein Rendite-Mittel der Nuisance-Periode ausgegeben. Aenderungen nach einer Registrierung nur als neuer Eintrag.

**Fundstellen-Kuerzel.**

| Kuerzel | Bedeutung |
|---|---|
| `[F <abschnitt>]` | `state/herleitung_a1/FEASIBILITY.md` |
| `[fj ...]`, `[fj:A ...]`, `[fj:B ...]` | `state/herleitung_a1/feasibility.json` (sha256 `b4680f7c0b7e58ce9a6fa256f6913656cb8b432b55b40bc915aa0f930ca72d9e`), JSON-Pfad; A/B = Konfiguration |
| `[EV-x]` | `state/herleitung_a1/ENTSCHEIDUNGSVORLAGEN.md`, Vorlage x |
| `[abg.]` | hier abgeleitet, Rechenweg angegeben |
| `[sek]` | Sekundaerbeleg |
| UNBELEGT | keine Fundstelle; blockiert die abhaengige Groesse |

---

### 0. Vorbedingungen der Registrierung

| Nr | Gegenstand | Fundstelle | Abhilfe vor der Registrierung |
|---|---|---|---|
| V1 | 1h-Symbol-Wochen primaer ein- oder ausgeschlossen; B ist GL-012 bei jedem theta <= 1 | [EV-1]; [fj:B] | Orchestrator-DEC; bei (B) endet A1 hier |
| V2 | SE-Regel der Gesamtrendite (gemessen, c >= 1) gegen DEC-67 E4 (W_eff = 0,41 W) | [EV-2]; [F 3.1] | DEC: DEC-67 E4 gilt nicht fuer die A1-Gesamtrendite; SE-Regel EV-10 |
| V3 | Luecke 0,60 <= P < 0,80 zwischen DEC-52 (i) und DEC-51 (2) | [EV-3] | programmweite DEC VOR der Registrierung (Sequenz-Zwang) |
| V4 | Schwellenkonvention (kritischer Wert gegen MDE) | [EV-4] | programmweite DEC VOR der Registrierung |
| V5 | Kill (4): Schaetzer; W2 auf der Grenze (0,303) | [EV-5]; [fj kill4_ci_formationsseitig] | DEC zum Schaetzer und zur Gueltigkeit des Buehlmann-Straub-Ersatzes |
| V6 | **theta UNBELEGT**; noetig >= 0,766 (GL-012), >= 0,975 fuer P_W1 >= 0,60 | [EV-6]; [F 5, 6.1] | Quelle [sek oder primaer]; ohne sie keine Registrierung |
| V7 | Code fehlt vollstaendig (Abschnitt 10) | - | Bau nach Spezifikation, Abnahme T0-T7 durch den Orchestrator |
| V8 | Vorlauf (outcome-frei, `--prelaunch`) reproduziert die Feasibility-Zahlen im Paketcode und friert sie in der YAML ein | [F 9] | Ergebnis +-1 % gegen `feasibility.json`, sonst Ursachenanalyse |
| V9 | Positivkontrolle in Produktionskonfiguration BESTANDEN | Abschnitt 3; [EV-12] | allein, zuerst; rc 0 ist Vorbedingung des Laufs |
| V10 | Daten-Fingerprints | [fj:A fingerprint] | union_range `a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a`, delisting_dates `852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933`, as_of 2026-09-28 in `data_fingerprints` |

Erst danach wird die Registrierungs-YAML erzeugt (Skelett in Abschnitt 11); ihre sha256 ist der Wert fuer
`--registered-sha256`.

---

### 1. Festlegungen

#### 1.1 Hypothese, Klasse, Richtung, Familie

| Feld | Wert | Fundstelle |
|---|---|---|
| Hypothese | Das gleichgewichtete Long-Bein D1 (niedrigstes Dezil der Wochen-SUMME von F - I) gegen den gleichgewichteten PIT-Universums-Hedge erzielt ueber die folgende Kalenderwoche eine Gesamtrendite (Preisbein plus Funding-Bein), die nicht vollstaendig durch die kompensierende Preisdrift aufgezehrt wird und nach Orthogonalisierung gegen Markt, Momentum und Reversal ein positives Residual-Alpha behaelt. | PRD 5.1; DEC-70 E1 |
| Klasse | P, kapitalfrei | PRD 3.2, 5.1 |
| Richtung | positiv | DEC-51 (1); PRD 5.1 |
| Ertragsquelle | Praemie; Zahler = die Short-Seite der D1-Perps, die bei F < I Funding an die Longs zahlt | PRD 5.1; DEC-70 E1 |
| Selektions-K | **1** (Wochen-SUMME, 7-Tage-Lookback); Abweichung von PRD 5.1 (K = 3), Etikett | [EV-7]; DEC-67 E2 |
| Familie | F-CARRY1 (ein Mitglied), Ueber-Familie F-PREM abhaengigkeitsrobust (BY) | PRD 5.1; [EV-7] |
| Nullhypothese | exakte Kompensation (theta = 0): E[Gesamtrendite D1 minus Universum] = 0 | PRD 5.1 (c); DEC-70 E1 |

#### 1.2 Panel, Universum, Datenbezug

- **Union-Panel** `panel_1d` (877) + `panel_1d_delisted` (261), Harvest-Export 2026-09-28 (DEC-84), Fingerprints V10.
  Gelesen mit `panel_load.load_panel_union` (`allow_partial=True`, DEC-66), Jahre 2021..2026.
- **PIT-Universum U_t:** lebend nach `weekly_returns_and_mask_union` (>= 8 Wochen Historie, Delisting-Woche als letzte
  Woche, DEC-72) UND am Schluss von Woche t handelbar (Delisting-Datum nach dem Wochenende); Konfiguration nach [EV-1];
  I=0-Paare (USDCUSDT, ETHBTCUSDT) mit I = 0 im Schluessel; Symbol-Wochen mit TradFi-Schliessungsmuster
  (>= 50 % exakt-0-Funding-Tage in den 8 Wochen bis t) ausgeschlossen [EV-11] Punkt 3.
- **Delisting:** letzter gehandelter Kurs, keine Imputation; Survivorship-Etikett: 7 delistete Symbole ohne Historie
  fehlen (DEC-72).

#### 1.3 Fenster

| Fenster | von / bis | Formationswochen (judged) | Rolle |
|---|---|---:|---|
| W1 | 2024-07-01 / 2025-06-30 | 52 (2024-07-01 .. 2025-06-23) | urteilstragend |
| W2 | 2025-07-01 / 2026-06-30 | 51 (2025-07-07 .. 2026-06-22) | urteilstragend |
| Nuisance | 2021-03-01 / 2024-06-30 | 114 (Basis K_t >= 117) | nur Streuung und Persistenz-Verhaeltnis fuer die Power-Zeile; Aera-Profil wird NICHT gerechnet |

REZENZ (C.18): nur W1/W2 urteilen. Wochen nach 2026-06-30 bleiben ungenutzt.

#### 1.4 Cluster-Einheit

Nicht-ueberlappende Kalenderwoche (DEC-51 (3)); N_cluster = W_j = 52 / 51, gepoolt 103. Gemessene Autokorrelation der
Statistik auf der Nuisance-Basis: rho_1 = -0,250 [F 3.1]; registriert ist c = max(1, gemessen) = 1 [EV-2], d. h.
N_eff = N_cluster (keine Gutschrift fuer negative Autokorrelation, rho = 0 ist dabei NICHT unterstellt, sondern
gemessen und zugunsten der Strenge gekappt).

#### 1.5 Konstruktion je Formationswoche t (formationsseitig, PIT)

1. Schluessel `key[t,i]` = Wochen-SUMME (F - I) ueber alle Zahlungen von Woche t (`panel_load.funding_excess_weekly`,
   DEC-67 E2, I skaliert nach Intervall, DEC-84). Fuer I=0-Paare I = 0 [EV-11].
2. D1 = floor(n_t/10) Symbole von U_t mit dem niedrigsten Schluessel, stabile Reihenfolge; kein Tie-Break im Klumpen
   (DEC-67 E2).
3. Long D1 gleichgewichtet, Short U_t gleichgewichtet, Haltewoche t+1, woechentlich neu gebildet.
4. Preisbein `p = mean_D1(R_{t+1}) - mean_U(R_{t+1})`, R einfache Wochenrendite (Schlusskurs der letzten Tageskerze der
   ISO-Woche); Funding-Bein `g = mean_U(sumF_{t+1}) - mean_D1(sumF_{t+1})` (Long zahlt F, Short erhaelt F);
   Gesamtrendite `x = p + g` in bp.
5. Funding-Buchhaltung nach [EV-11]: Umschalt-Tage belassen (Fehler <= 0,875 bp je Tag, 0,37 % / 0,83 % der
   D1-Tage), Teiltage laut gezaehlt, Haltewochen-Funding = Tage Mo..So von t+1.

#### 1.6 Urteilstragende Groesse

- **Residual-Alpha** a_W: Achsenabschnitt der OLS-Regression von x_t auf (MKT_EW, MOM1, REV_GAP) der Haltewoche, je
  Fenster; Faktoren als gleichgewichtete Haltewochen-Rendite des Universums bzw. Dezil-L/S auf der Vorwochenrendite
  (MOM1) und der Vorvorwochenrendite (REV_GAP) im selben U_t [EV-8].
- Mitberichtet (kein Urteil): Mittel von x, p, g; Zerlegung; Sharpe, MaxDD, Tail-Ratio mit Rauschboeden (PRD 3.6);
  Pflicht-Sensitivitaet Konfiguration B.

#### 1.7 SE-Regel

`SE_W = max(SD(x_W)/sqrt(W_j), SE_MBB(x_W))`, MBB Block 4, 1.000 Replikate, Seed 53;
`SE_alpha,W = max(OLS-SE mit W_j - 4 Freiheitsgraden, SE_MBB(alpha_W))` mit Neuschaetzung der Regression je
Replikat [EV-10]. Gepoolt: stratifizierter stationaerer Bootstrap je Fenster, gepoolter Schaetzer = Mittel der
Fensterschaetzer [EV-9].

#### 1.8 Schwelle (Herleitungs-Referenz, DEC-58b; nach [EV-4] Option (a))

- C.10: `T_W = max(obere 95-%-Grenze des am Null-Fixture gemessenen Alpha-Nulleffekts; 1,6449 * SE_alpha,W)`, plus
  MBB-Untergrenze (95 %, einseitig) > 0.
- DEC-52: gepoolt `T_pool = max(obere 99-%-Grenze des Null-Fixture-Effekts; 2,3263 * SE_alpha,pool)`; Screens je
  Fenster a_W > 0 und a_W >= 0,5 * T_pool; Magnituden-Band nach [EV-9] Punkt 1.
- Registriert wird je Schwelle der Pfad und die Test-ID der Herleitung (Abschnitt 6), nie ein nackter Skalar.

#### 1.9 Fenster-Regime (Zuordnungsregel PRD 5.1, mechanisch, VOR der Registrierung)

Eingaben: bindende SD 372,9 / 354,5 bp [F 4], c = 1, `prem_prior_W = Spread_W * 0,573 * theta` mit Spread 175,8 /
339,6 bp [F 2 (d), 3.3, 5]; `P_W = Phi(prem_W/SE_W - 1,6449)`; P_W >= 0,60 in beiden Fenstern -> C.10 hart, sonst DEC-52;
GL-012, wenn `3,1680 * SE_gepoolt > prem_gepoolt` (SE_gepoolt 35,67 bp).

| theta (belegt) | Regime | Power | Befund |
|---|---|---|---|
| < 0,766 | - | - | GL-012 vor dem Lauf |
| 0,766 .. 0,975 | DEC-52 | gepoolt 0,80..0,96 (alpha 0,01); mit Screens ~0,60..0,83 | registrierbar nach V1-V10 |
| >= 0,975 | C.10 hart | W1 0,60..0,62, W2 0,99; gemeinsam ~0,61 | Luecke [EV-3] |

Heute ist theta UNBELEGT -> **keine Zuordnung moeglich**. Der DEC-52-Zweig muss in jedem Fall gebaut sein.

#### 1.10 Gate-Text (Entwurf, woertlich)

> **H-31 (A1) gilt als kapitalfrei BESTANDEN, wenn:** (1) das Residual-Alpha der nicht-ueberlappenden
> Wochen-Gesamtrendite D1 minus Universum gegen (MKT_EW, MOM1, REV_GAP) die registrierte Schwelle im registrierten
> Fenster-Regime erreicht - C.10 hart: in beiden Fenstern `a_W >= T_W` und MBB-Untergrenze > 0; DEC-52: Screens je
> Fenster und gepoolt `a_pool >= T_pool` bei alpha 0,01; (2) die rohe Gesamtrendite das hypothesierte Vorzeichen in
> beiden Fenstern hat (Bericht der Magnitude, kein zweites Gate); (3) das Ergebnis oberhalb der am Null-Fixture
> gemessenen Decke liegt (K = 1); (4) die Funding-Buchhaltung intervall-normiert ist und die einbezogene Symbolmenge
> je Woche namentlich als Artefakt vorliegt; (5) D1 in der Median-Woche jedes Fensters nicht degeneriert ist (sonst
> KEIN VERDIKT in diesem Fenster); (6) die DEC-53-Artefakte geschrieben und verifiziert sind (sonst KEIN VERDIKT);
> (7) das Gate auf dem Peso-Fixture nachweislich durchfaellt.
> **Ein PASS ist ein kapitalfreies WEITER und traegt verpflichtend das Etikett: "Praemien-EXISTENZ; die
> risikoadjustierte Frage ist auf diesem Bestand untestbar (MinTRL > Historie) und daher PARK, nicht WEITER." Kein
> Kapitalschritt folgt daraus.** Besteht die rohe Gesamtrendite und faellt das Residual-Alpha durch, lautet das
> Ergebnis "verpacktes A3, kein eigener Kandidat" (Kill (5)), kein PASS.

#### 1.11 Abweichungen vom PRD-5.1-Text (registriert, etikettiert)

| PRD 5.1 | Entwurf | Grund |
|---|---|---|
| Dezil-Long-Short | Long D1 gegen EW-Universum | DEC-70 E1 (D10 degeneriert) |
| K = 3 (Lookback 3/5/7 Tage) | K = 1 (Wochen-SUMME) | DEC-67 E2; [EV-7] |
| Schwelle "z * sigma/sqrt(W)" mit z = 2,4865/3,1680 | kritischer Wert 1,6449 / 2,3263 | DEC-51 (1), PRD 3.5, Konsistenz mit P_fenster; [EV-4] (a) |
| "nur homogene 8h-Klasse, solange I_1h offen" | alle Klassen intervall-normiert (Konfiguration A) | DEC-84; [EV-1] |
| Orthogonalisierung gegen Momentum und Reversal | zusaetzlich Markt (MKT_EW) | A3-Lehre (Beta-Fehlanpassung); [EV-8] |
| N_eff "korrigiert ueber den stationaeren Bootstrap" | c = max(1, MBB) | [EV-2], [EV-10] |

---

### 2. Die zwoelf Pflichtzeilen (PRD 3.3.1-3.3.12)

| # | Zeile | Inhalt | Fundstelle |
|---|---|---|---|
| 1 | **Power** | alpha 0,05 einseitig je Fenster (C.10) bzw. 0,01 gepoolt (DEC-52), Power 0,80, Richtung positiv, Cluster Kalenderwoche, N_eff = 52/51 (c = 1, gemessenes rho_1 -0,25). Detektierbarer Effekt (MDE80): C.10 W1 128,6 bp, W2 122,2 bp; DEC-52 gepoolt 113,0 bp. A-priori-Effekt `prem_prior = Spread * 0,573 * theta`, **theta UNBELEGT**; Obergrenze theta = 1: 100,7 / 194,5 bp, Power C.10 0,62 / 0,99. Zuordnung: 1.9. | [F 4-6]; [EV-6] |
| 2 | **Entscheidungsrelevanz** | PASS: genau ein Schritt - getrennte Registrierung A1b (Tradability: Slippage der D1-Symbole, Kapitalbindung, Steuer, Ausfuehrbarkeit). DROP: schliesst nur theta >= dem registrierten theta aus (Power dort 0,60..0,84 je nach Regime); "Klasse P auf Perp-Funding im Querschnitt erschoepft" folgt NICHT, solange die Power gegen realistische theta < 0,8 liegt (C.13). Oekonomische Mindestmagnitude 36 bp/Woche als ETIKETT (C.2): prem_prior liegt darueber ab theta 0,36 (W1) / 0,19 (W2) [abg.: 36/100,7; 36/194,5]. | PRD 5.1; [EV-6] |
| 3 | **Cluster-Einheit** | Kalenderwoche; MBB Block 4; N_cluster 52/51, gepoolt 103 (stratifiziert je Fenster) | DEC-51 (3); [EV-9], [EV-10] |
| 4 | **Selektions-Deflation** | K = 1; analytische Decke entfaellt (keine Auswahl); Decke am Null-Fixture gemessen und berichtet (T1). Bei K = 3: ~0,85 * SE je Variante [abg.]. | [EV-7]; PRD 3.3.4 |
| 5 | **Adversariales Fixture** | Peso: Nullpraemie, Spruenge -35 % mit Rate 1/3 Jahre auf das D1-Bein (Carry 22,4 bp/Woche); PASS-Rate <= alpha + 3 MC-SE, sprungfrei <= 0,05; Ehrlichkeitszeile [EV-13] | PRD 3.3.5; [EV-13] |
| 6 | **Kostenmodell-Bindung** | `constants_hash`: "n/a - kapitalfrei ohne Kostenmodell"; keine Kostengroesse in einer PASS-Bedingung (C.2); `tradability3` gehoert zu A1b | PRD 3.3.6, 3.4 |
| 7 | **Irreversibilitaets-Probe** | nachladbar: Bybit-Kerzen und Funding-Historie oeffentlich (aus der Cloud geo-gesperrt, DEC-83), Panel-Export im Harvest-Archiv (DEC-84) | PRD 3.3.7 |
| 8 | **Positivkontroll-Vorschaltung** | vorgeschaltet: ja, allein und zuerst, mit vorab fixierter Bestehensregel, die die Power-Annahme prueft (Abschnitt 3); Laufzeit geschaetzt Minuten [abg.: 3 theta * 500 Replikate * 103 Wochen Regression] | PRD 3.3.8; DEC-92 Lehre |
| 9 | **Kapital/Steuer/Venue** | Kapital-Multiplikator m UNGEMESSEN (Pflicht-Sensitivitaet in A1b); Steuer UNBELEGT (PRD 8.2); Venue: ADL auf dem gewinnenden Bein, Auszahlungsstopp (Etikett). Zahler nach 2024 (formationsseitig): mittlerer D1-Schluessel -196,7 / -385,2 bp/Woche, streng negativer Anteil des Universums 0,67 / 0,69 - die zahlende Short-Seite existiert in W1/W2; das belegt Zahler, keine Praemie. | PRD 3.3.9; [F 2] |
| 10 | **Stress-Episode** | Abdeckungsnachweis (DEC-56 (1), kein Filter): STRESS_REL W1 13, W2 6 Episoden; STRESS_ABS W1 2 (2024-08-05, 2025-02-03), W2 1 (2025-10-10) | Abschnitt 4 |
| 11 | **Ergebnis-Artefakte** | Abschnitt 5; ohne sie KEIN VERDIKT | DEC-53 |
| 12 | **Test-Pflichten** | T0-T7, Abschnitt 6 | PRD 3.3.12 |

---

### 3. Positivkontroll-Vorschaltung (Produktionskonfiguration, vorab fixierte Bestehensregel)

**Welt** [EV-12]: echte W1/W2-Wochenraster, echte PIT-Alive-Masken, echte Formationsschluessel, echtes D1 und U_t
(formationsseitig); synthetische Haltewochen-Renditen `R = beta_{i,t} * f + u_D1 + e_i` mit den PIT-Betas und
Residualvarianzen des Fensters, Faktor-SD des Fensters (EW 13,2 % / 7,9 %), gemeinsamem D1-Schock (kalibriert auf
kappa = 1,877) und synthetischem Funding `sumF = 0,21 % + 0,573 * (key_i - mean_U key) + Rauschen` (SD 71,7 bp,
rho_1 0,52 des Funding-Beins); Kompensation `E[p] = -(1 - theta_pc) * E[g]`. Synthetische Faktoren (MKT_EW, MOM1,
REV_GAP) aus denselben synthetischen Renditen. Volle Gate-Kette des Laufs (gleiche Funktion `evaluate`), R = 500
Replikate je theta_pc in {0; theta_reg; 1}, Seeds 53..552.

**Bestehensregel (alle vier, vorab):**
1. SD der synthetischen A1-Serie je Fenster in +-10 % der bindenden SD (372,9 / 354,5 bp); darueber ist die
   Power-Zeile zu optimistisch -> NICHT BESTANDEN.
2. theta_pc = 0: PASS-Rate <= nominales alpha des Regimes + 3 MC-SE.
3. theta_pc = theta_reg: PASS-Rate >= registrierte Power - 3 MC-SE.
4. Je Fenster: Rate der Fensterbedingung in +-3 MC-SE der Fenster-Power der Power-Zeile.

Andere Seeds ergeben nie BESTANDEN. NICHT BESTANDEN -> kein Lauf, Ursachenanalyse, neue DEC (DEC-91-Muster).

---

### 4. Stress-Episoden (Abdeckungsnachweis, DEC-56 (1); kein Filter, kein Gate)

| Liste | sha256 (Kanon) | W1 | W2 |
|---|---|---|---|
| STRESS_REL (`state/runs/stress_rel.json`) | `eb83fe402b7b87243b1fc93691079a073461a42b6c17341502bc8c83678ca667` | 13 Episoden (2024-08-05 .. 2025-04-09) | 6 Episoden (2025-10-10 .. 2026-06-05) |
| STRESS_ABS (`state/runs/stress_abs.json`) | `b75fb7a08a6d590363f62828de99f23359c1c63fe1f385d0e4f37ba09bccf794` | 2 (2024-08-05, 2025-02-03) | 1 (2025-10-10) |

---

### 5. Ergebnis-Artefakte (DEC-53, Pflicht; sonst KEIN VERDIKT)

| # | Artefakt | Inhalt |
|---|---|---|
| 1 | Cluster-Serie je Fenster (CSV + sha256) | Woche, x, p, g, Formations-Spread s, K_t, n_D1, MKT_EW, MOM1, REV_GAP, Residuum, Zahl der 1h-/I=0-/Teiltag-Symbol-Wochen in D1 |
| 2 | D1-Mitgliedschaft je Woche (CSV + sha256) | Symbolnamen, Schluessel, Intervallklasse |
| 3 | Bootstrap-Replikate | MBB (Mittel und Alpha) je Fenster und stratifiziert gepoolt, 1.000 Ziehungen, ODER Seed 53 + Generator-Fingerprint (Bit-Generator, numpy-Version, sha256 der Ziehungen) |
| 4 | Pflicht-Sensitivitaet | Konfiguration B (Bericht), Spread-/Persistenz-Kennzahlen, Buchhaltungs-Zaehler |
| 5 | Kill-Tabelle und Etiketten | alle Werte aus Abschnitt 7 |
| 6 | Generator-Fingerprint des Laufs | Code-sha256, Commit, Daten-Fingerprints, YAML-sha256, Parameter |
| 7 | Abbruch | fehlt 1, 2 oder 3: KEIN VERDIKT (loud fail, Test gepinnt) |

---

### 6. Test-Pflichten T0-T7 (alles neu zu bauen; Abnahme durch den Orchestrator)

| Stufe | Inhalt |
|---|---|
| T0 | Schluessel-Arithmetik je Klasse (8h/4h/2h/1h: Totzone exakt 0), Umschalt- und Teiltage (gezaehlt), I=0-Paare; U_t-Regel (Delisting in Woche t ausgeschlossen); D1-Groesse und stabile Reihenfolge; Vorzeichen von p und g; SE-Regel (max iid/MBB); OLS-Alpha mit Freiheitsgraden; stratifizierter gepoolter Bootstrap |
| T1 | DEC-39-Trio als echte Tests: **Null** mit exakter Kompensation, 8h- und 1h-Symbole nebeneinander (1h-Episoden mit Rueckwechsel), PASS-Rate <= alpha + 3 MC-SE, D1-Klassenanteile = Universums-Klassenanteile (+-3 Binomial-SE), Gegenprobe: ein Schluessel aus dem Satz je Zahlung sortiert messbar nach Klasse; **Positiv** 50 % unkompensiert (theta = 0,5) in Hochpower-Konfiguration, theta_hat in [0,4; 0,6] und PASS; **Peso** nach [EV-13]. Zusaetzlich: Null-Fixture-Decke (Abschnitt 1.8) |
| T2 | Determinismus N >= 3 (Prelaunch, Positivkontrolle, Lauf auf Fixture) mit sha256 der Payloads |
| T3 | Checkpoint-Round-Trip: Lauf ohne Checkpoint (Minuten); per Test gepinnt, dass kein Resume-Zustand existiert, Round-Trip der Artefakte ist T7 (wie WP-13 `test_dec87_t3_*`) |
| T4 | Gate-Arithmetik auf konserviertem Payload, beide Regime (C.10, DEC-52), Kills (5)/(6), Peso |
| T5 | Konstanten-Pin: YAML-Konstanten (SD-Projektion, phi, Spread, Schwellenregel, Block 4, Seed 53, R 1.000) gegen Code |
| T6 | Legacy-Import-Sperre fuer das neue Paket und das CLI |
| T7 | Artefakt-Round-Trip: Artefakte laden, Alpha, SE und Bootstrap-Grenzen bitgleich reproduzieren; Fehlendes -> KEIN VERDIKT |
| Siegel | `--prelaunch` berechnet keine Haltewochen-Groesse einer Sortierung mit Haltewoche nach 2024-06-30 (struktureller Test wie WP-13 `test_seal_*`) |
| Startsperre | `--run` verweigert ohne passende `--registered-sha256` |

---

### 7. Kill-Bedingungen (vorab; keine wird nach dem Lauf geaendert)

| Nr | Bedingung | Folge | Stand |
|---|---|---|---|
| K1 | WP-7-Befund B1 | Querschnitts-Arm faellt weg (PRD 5.1 Kill (1)) | nicht ausgeloest (DEC-67 E1) |
| K2 | Zuordnungsregel ergibt GL-012 | GL-012 vor dem Lauf | haengt an theta: GL-012 fuer theta < 0,766 |
| K3 | Funding-Historie < 117 Symbole ueber beide Fenster | A1 in Breitenform tot | nicht ausgeloest (strengste Lesart 239) |
| K4 | Schluessel-Autokorrelation lag 1 < 0,30 | Registrierung unterbleibt | WP-7-Schaetzer 0,403 / 0,303, W2 Grenze; Ersatz [EV-5] |
| K5 | kein Residuum (rohe Rendite besteht, Alpha nicht) | "verpacktes A3", kein PASS | Laufzeit |
| K6 | D1 degeneriert in der Median-Woche eines Fensters (streng negativer Anteil < 0,10) | KEIN VERDIKT in diesem Fenster | nicht ausgeloest (0,52 / 0,71) |
| K7 | DEC-53-Artefakte unvollstaendig | KEIN VERDIKT | Bau |
| K8 | Positivkontrolle nicht bestanden | kein Lauf | offen |
| K9 | Startsperre oder Daten-Fingerprint verletzt | kein Lauf | Bau |

**Etiketten statt Kill:** Klasse P; kapitalfrei; "Praemien-EXISTENZ / Tradability PARK" (im PASS-Text); Zahler-Erosion
UNBELEGT; Steuerregime UNBELEGT (8.2); Kapital-Multiplikator m UNGEMESSEN; W1/W2-Inhomogenitaet (Auto-Switch ab
2025-10-30 [sek]: D1-1h-Anteil 1,8 % / 20,5 %); Survivorship (Union, 7 ohne Historie); 1h-Konfiguration [EV-1] mit
Pflicht-Sensitivitaet; I=0-Paare und TradFi-Regel [EV-11]; Kill (4) W2 an der Grenze; theta-Prior [EV-6]; Peso-
Ehrlichkeitszeile [EV-13]; C.17 (Abschnitt 9).

---

### 8. DEC-39-Trio (T1) - Konstruktion

- **Null (exakte Kompensation, 8h und 1h nebeneinander):** 300 Symbole, 104 Wochen, Klassen 40 % 8h, 40 % 4h, 20 % mit
  1h-Episoden (Laenge Median 8 Tage, Rueckwechsel auf 4h, DEC-84); je Zahlung `F = I_Klasse + d_{i,t}`, d mit
  Wochenpersistenz und einer Querschnitts-SD auf Hoehe der Nuisance-Schluesselstreuung; Preis
  `R = sumF + beta_i * f + e` (der Long zahlt genau, was der Preis bringt). Erwartung: Gesamtrendite D1 minus U = 0.
- **Positiv (50 % unkompensiert):** wie Null, Preis `R = sumF - 0,5 * (sumF - mean_U sumF) + beta_i * f + e`; erwartete
  Gesamtrendite = 0,5 * Funding-Vorteil; Hochpower-Konfiguration (600 Symbole, kleine e), damit der Test
  deterministisch besteht.
- **Peso:** Null plus Merton-Spruenge -35 % mit Rate 1/3 Jahre auf das D1-Bein, Carry so, dass E = 0 [EV-13].

---

### 9. Entscheidungsrelevanz und Nicht-Wiederholungs-Nachweis (C.1, C.17)

- A1 war nie registriert; keine A1-Lauf-, Ergebnis- oder Siegeldatei existiert. Die Konstruktion stammt aus DEC-70
  (Randverteilung des Schluessels, keine Outcome-Daten).
- **Offengelegt (C.17), bevor registriert wird:** alle formationsseitigen Zahlen von W1/W2 in `feasibility.json`
  (Schluessel, Spread, Degeneration, Intervallklassen, Schluessel-Autokorrelation, PIT-Betas, Faktor-SD); auf
  2021-03..2024-06 Streuung, Autokorrelation, R^2 und das Persistenz-Verhaeltnis 0,573 der A1-Statistik - kein Mittel.
  Die Wahl zwischen den Vorlagen EV-1..EV-5 faellt in Kenntnis dieser Zahlen; jede Vorlage nennt deshalb die Folge
  beider Optionen.
- **Nebenwirkung auf A3 (C.17):** Der A1-Lauf rechnet MOM1- und REV_GAP-Faktorrenditen auf W1/W2. Jede kuenftige
  A3-Fassung auf diesen Fenstern fuehrt sie als gesehen; das L-Siegel von A3 bleibt unberuehrt (A1 urteilt nicht auf L).

---

### 10. Bauarbeiten (was im Code fehlt)

Wiederverwendbar: `wp7_universe.panel_load` (Union-Laden, Wochenraster, `funding_excess_weekly`,
`decile_degeneration_weekly`), `wp13_xsec.run.moving_block_bootstrap_ci` (MBB-Muster), `wp13_xsec.run.benjamini_hochberg`,
Startsperre/DEC-53-Muster aus `wp13_xsec.run` und `scripts/wp13_xsec.py`, Struktur von `wp13_xsec.positive_control`.

| Nr | Baustein | Inhalt |
|---|---|---|
| B1 | neues Paket `src/bybit_edge/research/a1_carry/` | `formation.py` (U_t, D1, Konfiguration A/B, I=0-Liste, TradFi-Regel, Buchhaltungs-Zaehler), `legs.py` (Haltewochen-Preis- und Funding-Bein, Delisting), `factors.py` (MKT_EW, MOM1, REV_GAP), `stats.py` (SE-Regel, OLS-Alpha mit MBB, stratifizierter stationaerer Bootstrap), `gates.py` (rein: C.10, DEC-52, Kills, Etiketten), `prelaunch.py`, `positive_control.py`, `run.py` |
| B2 | DEC-52-Zweig | Screens, Magnituden-Band nach [EV-9], gepoolte Signifikanz alpha 0,01, gepoolte Replikate - erstmals im Programm, programmweit wiederverwendbar |
| B3 | Prelaunch (outcome-frei) | reproduziert `feasibility.json` (formationsseitig + Nuisance-Streuung) im Paketcode, schreibt die YAML-Vorlage mit eingefrorenen Konstanten; struktureller Siegel-Test |
| B4 | CLI `scripts/a1_carry.py` | `--prelaunch`, `--positive-control`, `--run --registered <yaml> --registered-sha256 <hex>`, `--panel-base`, `--delisted-base`, `--as-of`; Fingerprint-Pruefung; Ein-Befehl-Runner |
| B5 | Fixtures | Null (8h/1h), Positiv (50 %), Peso; Null-Fixture-Decke |
| B6 | DEC-53-Schreiber und -Pruefer | Abschnitt 5, KEIN-VERDIKT-Abbruch |
| B7 | Tests T0-T7, Siegel, Startsperre | Abschnitt 6; Suite wird erweitert, nie reduziert |
| B8 | keine Aenderung an `panel_load` | Teiltag-Verzerrung von I wird im neuen Paket gezaehlt, nicht im WP-7-Code korrigiert (WP-7-Ausgaben bleiben bitgleich) |

---

### 11. YAML-Skelett (Entwurf; Werte mit UNBELEGT blockieren)

```yaml
id: A1
hypothese_id: H-31
klasse: P
capital_free: true
hypothese: "Long D1 (niedrigstes Dezil der Wochen-SUMME F - I) gegen EW-PIT-Universum: Residual-Alpha der Wochen-Gesamtrendite > 0"
ertragsquelle: "Praemie; Zahler = Short-Seite der D1-Perps (F < I)"
metric: residual_alpha_weekly_total_return_bp     # gegen MKT_EW, MOM1, REV_GAP
richtung: positiv
konfiguration_1h: UNBELEGT                        # EV-1: A (empfohlen) oder B (dann GL-012)
windows:
  - {id: W1, von: 2024-07-01, bis: 2025-06-30, rolle: urteilstragend, w_judged: 52}
  - {id: W2, von: 2025-07-01, bis: 2026-06-30, rolle: urteilstragend, w_judged: 51}
fenster_regel: UNBELEGT                           # mechanisch nach 1.9, sobald theta belegt ist
threshold: {regel: "EV-4 (a): C.10 1,6449*SE_alpha,W; DEC-52 2,3263*SE_alpha,pool; max mit Null-Fixture-CI", ref: "<pfad#test_id>"}
structural_null: {komponenten: [I_kuerzt_sich_im_Querschnitt, exakte_Kompensation, Totzonen-Klumpen], wert: 0, ref: "<pfad#test_null_exact_compensation_8h_1h>"}
power:
  alpha: 0.05                                     # C.10 je Fenster; DEC-52 gepoolt 0.01
  sided: one
  power: 0.80
  z: 2.4865                                       # DEC-52-Zweig 3.1680
  cluster_unit: kalenderwoche
  n_eff: {W1: 52, W2: 51, c: 1.0, rho1_gemessen_nuisance: -0.250}
  sigma_bindend_bp: {W1: 372.9, W2: 354.5}
  a_priori_effekt: UNBELEGT                       # prem = Spread * 0.573 * theta; theta UNBELEGT (EV-6)
  detectable_effect_bp: {W1: 128.6, W2: 122.2, gepoolt_dec52: 113.0}
  per_fenster_power: UNBELEGT                     # theta = 1: 0.619 / 0.990
  zuordnungsregel: "PRD 5.1: P_W = Phi(prem/SE_W - 1,6449); >= 0,60 beide -> C10_hart, sonst DEC52; GL-012 wenn 3,1680*SE_gepoolt > prem"
  ref: "state/herleitung_a1/feasibility.json"
selection: {K: 1, ceiling_analytic: "n/a (K = 1)", ceiling_measured_ref: "<pfad#test_null_fixture_ceiling>"}
economic_minimum: {wert: 36, einheit: bp_pro_woche, ref: "PRD 5.1", label: ueber_wand_ab_theta_0.36}
decision_relevance: {on_pass: "A1b Tradability getrennt registrieren", on_drop: "nur theta nahe der Untergrenze ausgeschlossen; keine Erschoepfungs-Aussage"}
capital_tax_venue: {kapitalbasis: "m UNGEMESSEN", steuer: "UNBELEGT (PRD 8.2)", venue_event: "ADL / Auszahlungsstopp (Etikett)", zahler_post_2024: "D1-Schluessel -196,7 / -385,2 bp/Woche (formationsseitig)"}
stress_episode: {liste_ref: "state/runs/stress_rel.json#eb83fe40", rolle: abdeckungsnachweis, n_episoden: {W1: 13, W2: 6}}
irreversibility_probe: {ergebnis: nachladbar, ref: "DEC-84"}
positive_control: {laufzeit_geschaetzt_h: 0.1, vorgeschaltet: true, ref: "ERSTFASSUNG Abschnitt 3"}
fixtures: {positive: "<pfad#test_positive_50pct>", null: "<pfad#test_null_exact_compensation_8h_1h>", adversarial: "<pfad#test_peso>"}
artifacts: {cluster_series_ref: "<pfad + sha256>", bootstrap_replicates_ref: "seed 53 + generator_fingerprint"}
fdr_family: F-CARRY1
over_family: F-PREM
feasibility_verdict: UNBELEGT                     # testbar nur fuer theta >= 0,766 (Konfiguration A, c = 1)
constants_hash: "n/a - kapitalfrei ohne Kostenmodell"
data_fingerprints: {union_range: a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a, delisting_dates: 852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933, as_of: 2026-09-28}
bedingung_welle_1: [WP-7, V-1, V-3, WP-10, DEC-84]
```
