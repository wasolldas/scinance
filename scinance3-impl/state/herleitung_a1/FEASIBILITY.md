# A1 (H-31) - Stufe 1: Feasibility-Befund (C.12) vor jedem Design

> **ORCHESTRATOR-VERMERK 2026-10-13 (DEC-93, GL-033):** Ersetzt durch die Feststellung des Reviews (`REVIEW_A1.md`):
> A1 ist unter den geltenden Beschluessen (DEC-67 E4, fuer A1 bestaetigt in DEC-70 E1: W_eff = 0,41 W) vor der
> Registrierung GL-012 (176,5 > 147,6 bp schon bei theta = 1) und zusaetzlich theta-UNBELEGT. Die Aussage "Stopp-Regel
> greift nicht" unten ist damit hinfaellig; Stufe 2 ist Akte ohne Rechtswirkung. Kein Verdikt ueber den Funding-Carry.

> ENTWURF der Herleitung, Stand 2026-10-13. Nichts hier ist registriert oder beschlossen; entscheiden und
> registrieren darf nur der Orchestrator. Keine A1-Outcome-Groesse auf Daten ab 2024-07-01 berechnet, angesehen oder
> gespeichert; keine Siegeldatei geoeffnet; keine Tagesdaten nach 2026-06-28 geladen.
>
> Fundstellen-Kuerzel:
> - `[fj]` = `scinance3-impl/state/herleitung_a1/feasibility.json`
>   (sha256 `b4680f7c0b7e58ce9a6fa256f6913656cb8b432b55b40bc915aa0f930ca72d9e`), mit JSON-Pfad;
>   `[fj:A]` = `configs.A_dec70_1h_eingeschlossen`, `[fj:B]` = `configs.B_1h_symbolwochen_ausgeschlossen`;
> - `[S:<datei>]` = Skript unter `scratchpad/a1_herleitung/` (sha256 je Skript in `[fj] skripte`);
> - `[abg.]` = hier aus offenen Zahlen abgeleitet, Rechenweg daneben;
> - UNBELEGT = keine Fundstelle; blockiert die abhaengige Groesse.

---

## 0. Befund in Kuerze

1. **Stopp-Regel des Auftrags (GL-012-Pruefung bei theta = 1,0), ausgewertet:** In der Konstruktion des Auftrags
   (DEC-70, Schluessel mit intervall-skaliertem I, alle Intervallklassen = Konfiguration A) und mit der SE des
   registrierten Mittelwert-Tests ist A1 bei theta = 1,0 **knapp testbar**:
   `3,1680 * SE_gepoolt = 113,0 bp < prem_gepoolt = 147,6 bp` (Faktor 1,31). Bei theta = 0,5 und 0,25 ist A1
   GL-012. Kleinstes theta ohne GL-012: **0,766**. **Stufe 2 wurde deshalb erstellt - als bedingter Entwurf.**
2. **Der Befund ist nicht robust.** Jeder der folgenden drei Schalter macht A1 schon bei theta = 1,0 zum GL-012-Fall:
   - (EV-1) 1h-Symbolwochen look-ahead-frei ausgeschlossen (DEC-58-E3-Lesart, Konfiguration B): 116,2 > 100,0 bp;
   - (EV-2) W_eff = 0,41 W nach DEC-67 E4 statt der gemessenen Autokorrelation der Gesamtrendite: 176,5 > 147,6 bp;
   - (EV-3) DEC-51 (2) je Fenster wie in DEC-87 (F)/GL-032: W1 erreicht Power 0,80 bei KEINEM theta <= 1
     (MDE80_W1 = 128,6 bp > 100,7 bp bei theta = 1; P_W1 = 0,62). Ohne DEC-52-Zweig (wie in A3) ist A1 damit bei
     jedem theta GL-012; mit gebautem DEC-52-Zweig nur fuer theta >= 0,975 (Luecke, EV-3).
3. **theta ist UNBELEGT** (keine Quelle). Damit ist `prem_prior` UNBELEGT und blockiert die Registrierung, bis eine
   Quelle theta >= 0,77 belegt (Abschnitt 5).
4. Formationsseitig (W1 / W2): K 343..511 / 512..600, kein Kill (3); Schluessel-Autokorrelation lag 1 (WP-7-Schaetzer)
   0,403 / 0,303 - W2 liegt auf der Kill-(4)-Grenze (90-%-KI 0,281..0,329); D1 nicht degeneriert (streng negativer
   Anteil Median-Woche 0,52 / 0,71); Formations-Spread Mittel 175,8 / 339,6 bp/Woche (Median 148 / 354).
5. Nuisance 2022-04..2024-06 (Etikett Regel 1): Wochen-SD der Gesamtrendite D1 minus Universum 354 bp, davon
   Preisbein 91 % der Varianz; Autokorrelation lag 1 -0,25 (c <= 0,76); Persistenz des Funding-Beins 0,573.
   Bindende SD je Fenster 373 / 354 bp; SE je Fenster 51,7 / 49,2 bp.

---

## 1. Daten, Konstruktion, Ergebnisblindheit

### 1.1 Daten

- Union-Panel `panel_1d` + `panel_1d_delisted` (Harvest-Export, DEC-84), gelesen mit `panel_load.load_panel_union`
  (`allow_partial=True` wie DEC-66), Jahre 2021..2026, as_of 2026-09-28. 1.138 Symbole (877 + 261 delistet).
- Daten-Fingerprints gleich dem v5e-Lauf (DEC-88): union_range `a7e4dec7...793a`, delisting_dates `852bf753...2933`
  [fj:A fingerprint].
- **Tagesdaten nach 2026-06-28 werden verworfen** (`a1_common.truncate_daily`, `LAST_DAY_USED`): die letzte
  W2-Formationswoche ist 2026-06-22; die Haltewoche 2026-06-29 und alle Wochen nach 2026-06-30 bleiben unberuehrt.
  Ergebnis: 2.005 Tage 2021-01-01..2026-06-28, 287 Wochen 2020-12-28..2026-06-22.
- 906 Symbole tragen Funding-Daten, darunter alle 261 delisteten [S:a1_explore.py, Log].

### 1.2 Konstruktion (DEC-70, wie im Auftrag fixiert)

- **Schluessel** `key[t,i]` = Wochen-SUMME von (F - I) ueber alle Zahlungen der ISO-Woche t, I je Zahlung skaliert nach
  Intervallklasse (`panel_load.funding_excess_weekly`, DEC-67 E2, DEC-84). Unabhaengig nachgerechnet:
  `key = sum_Tage(funding_sum - 0,03 %)` ueber Tage mit Funding, maximale Abweichung 2,8e-17 [S:a1_selfcheck.py].
- **Formations-Universum** U_t = PIT-lebend in t (>= 8 Wochen Historie, DEC-72-Delisting-Konvention) UND am Schluss
  der Woche t noch handelbar (Delisting-Datum nach Wochenende; im Gitter = `alive[t+1]`).
- **D1** = die floor(n_t/10) Symbole mit dem niedrigsten Schluessel (staerkste Unterschreitung von I), stabile
  Reihenfolge bei Gleichstand (wie `stats.sigma_ls_series`).
- **Hedge** = gleichgewichtetes U_t. Haltewoche t+1.
- **Vorzeichen (nur fuer die Nuisance-Messung benutzt):** Preisbein `p = mean_D1(R) - mean_U(R)` mit einfacher
  Wochenrendite R; Funding-Bein `g = mean_U(sum F) - mean_D1(sum F)` (Long zahlt F, Short erhaelt F); Gesamtrendite
  `x = p + g`. Formations-Spread `s_t = mean_U(key_t) - mean_D1(key_t)` (> 0).

### 1.3 Fenster

| Fenster | Formationswochen (judged) | Anzahl | Rolle |
|---|---|---:|---|
| W1 | 2024-07-01 .. 2025-06-23 | 52 | urteilstragend (nur formationsseitig gemessen) |
| W2 | 2025-07-07 .. 2026-06-22 | 51 | urteilstragend (nur formationsseitig gemessen) |
| Nuisance-Basis | 2022-04-18 .. 2024-06-17 (Haltewochen bis 2024-06-24, Ende 2024-06-30), K_t >= 117 | 114 | Streuung/Kovarianz/Verhaeltnis |
| Nuisance gesamt | 2021-07-05 .. 2024-06-17, K_t >= 10 | 155 | nur Bericht (D1 dort 1..33 Symbole) |

Die Basis "K_t >= 117" (Programm-Floor K_min, DEC-73) wurde VOR der ersten Nuisance-Rechnung als primaer festgelegt:
vor 2022-04-18 hat das Universum weniger als 117 Symbole (2021-03: 5), D1 ist dann 1..11 Symbole gross und fuer W1/W2
(D1 34..60) nicht repraesentativ.

### 1.4 Ergebnisblindheit (Regel 1) - was wo berechnet wurde

| Groesse | Zeitraum | Art | Skript |
|---|---|---|---|
| K, Schluesselverteilung, D1, Degeneration, Spread der Formationswoche, Intervallklassen | W1, W2, Nuisance | formationsseitig | `a1_window_census.py` |
| PIT-Betas und Residualvarianzen (26 Wochen nachlaufend, bis einschliesslich t) | W1, W2, Nuisance | formationsseitig | `a1_model.py` |
| SD der Marktfaktoren (EW-Universum, BTC) | W1, W2 | "Faktor-SD des Marktes" (erlaubt), nur SD | `a1_window_census.py` |
| Zeitreihen-Autokorrelation lag 1 des Schluessels je Symbol (Auftrag (b)) | W1, W2 | Folge von Formationsschluesseln, keine Sortierung, kein Portfolio | `a1_window_census.py`, `a1_kill4_ci.py` |
| Persistenz innerhalb der Formationswoche (Mo-Mi sortiert, Do-So gemessen) | W1, W2 | nur Daten der Formationswoche t (vor der A1-Formation) | `a1_formation_sensitivity.py`, `a1_psi_by_class.py` |
| SD, Autokorrelation, Zerlegung, R^2, Steigungen, Persistenz-VERHAELTNIS | Nuisance (Haltewoche endet <= 2024-06-30) | outcome-seitig, nur Streuung | `a1_nuisance.py` |

Waechter: `a1_common.assert_nuisance_holding_week` bricht laut ab, wenn eine Haltewoche nach 2024-06-30 endet; die
Wochenserie der Nuisance-Rendite lebt nur im Speicher; `_no_mean` verweigert jeden Ausgabeschluessel fuer ein
Rendite-Niveau. **Etikett (Pflicht, steht in jeder Nuisance-Ausgabe):** "Nuisance 2021-03-01..2024-06-30, nur
Streuungs-/Kovarianz-Groessen und Verhaeltnisse; der Mittelwert der A1-Rendite (gesamt, Preisbein, Funding-Bein) und
der MOM/REV-Faktorrenditen wird weder ausgegeben noch gespeichert." Die MOM/REV-Faktorrenditen der Nuisance-Periode
(= A3-L-Fenster) gehen nur als Kovarianz ein; ihr Mittel wird weder ausgegeben noch gespeichert (A3-L-Siegel-Geist).

### 1.5 Zwei Konfigurationen

- **A** = Konstruktion des Auftrags: alle Intervallklassen, intervall-normiert. Grundlage der Stopp-Regel.
- **B** = DEC-58-E3-Lesart "Ausschluss der 1h-Klasse als look-ahead-freie Symbol-Wochen-Regel": eine Symbol-Woche
  faellt aus U_t, wenn die Formationswoche t mindestens einen Tag mit `funding_n = 24` hat (Umgebungsvariable
  `A1_EXCL1H=1`). Bericht; ihre Rolle (primaer oder Sensitivitaet) ist Entscheidungsvorlage EV-1.

---

## 2. Formationsseitiger Zensus W1/W2 (Auftrag (a)-(e)), Konfiguration A

### (a) Breite - Kill PRD 5.1 (3): < 117 Symbole

| Groesse | W1 | W2 | Fundstelle |
|---|---:|---:|---|
| K_t min / Median / max | 343 / 418 / 511 | 512 / 584 / 600 | [fj:A fenster_formationsseitig.<W>.K] |
| Symbole mit Funding in W1 UND W2 | 533 | | [fj:A symbole_ueber_beide_fenster] |
| ... in jeder Formationswoche beider Fenster im Universum | 239 | | dito |
| ... in jeder Formationswoche beider Fenster mit 7 Funding-Tagen | 260 | | dito |

**Kill (3) nicht ausgeloest** - jede Lesart liegt ueber 117 (strengste: 239). In Konfiguration B: 200 [fj:B].

### (b) Schluessel-Autokorrelation lag 1 - Kill PRD 5.1 (4): < 0,30

WP-7-Schaetzer (Median ueber Symbole der Pearson-Autokorrelation lag 1, Symbol >= 12 Mitgliedswochen), angewandt
auf den DEC-67-Schluessel je Fenster:

| Schaetzer | W1 | W2 | Nuisance-Basis | Fundstelle |
|---|---:|---:|---:|---|
| Median je Symbol (WP-7, min 12 Wochen) | **0,403** | **0,303** | 0,540 | [fj:A fenster_formationsseitig.<W>.key_autocorr], [fj:A formationsseitige_sensitivitaeten.sets.nuisance_K_ge_117] |
| 90-%-KI (Symbol-Bootstrap, 2.000 Ziehungen, Seed 53) | 0,384..0,421 | 0,281..0,329 | | [fj kill4_ci_formationsseitig] |
| Median, min 8 / 26 / 40 Wochen | 0,395 / 0,416 / 0,421 | **0,2997** / 0,325 / 0,336 | | dito |
| gepoolt innerhalb Symbol | 0,282 | 0,313 | 0,418 | [fj:A ...key_autocorr.key_F_minus_I.pooled_within_lag1] |
| roher Wochen-Funding (WP-7-Objekt) | 0,403 | 0,304 | | [fj:A ...raw_weekly_funding_sum] |

**Kill (4) mit dem registrierten WP-7-Schaetzer nicht ausgeloest, W2 aber auf der Grenze** (0,0029 darueber; mit
min 8 Wochen 0,2997 darunter). WP-7 hatte 0,42..0,43 ueber die Vollhistorie; in W2 faellt der Wert.

**Buehlmann-Straub-Ersatz (PRD 11.4, DEC-58 E1 (e): `k <= 2,333*w`):** Einweg-Zerlegung der Wochenschluessel je
Fenster ergibt k = 8,98 (W1) / 11,70 (W2) Wochen, z(1 Woche) = 0,100 / 0,079 - **das Kriterium k <= 2,333 ist
woertlich verletzt.** Die Gueltigkeitsbedingung (i) der Aequivalenz ("wahres Mittel naeherungsweise konstant", S5
X-AKT-4) ist aber messbar verletzt: auf der Nuisance-Basis ist z = 0,040 (k = 24,3), die tatsaechliche
Querschnitts-Persistenz derselben Wochen aber 0,445 (Pearson) / 0,590 (Spearman) und das Funding-Bein-Verhaeltnis
0,573 [fj:A nuisance.bases.K_ge_117.persistence]. z misst den permanenten Symbolanteil (Fenstermittel), nicht die
Vorhersagbarkeit eine Woche voraus. Der Exkurs-Review hatte genau diese Falle benannt (REVIEW_S1_S5 X-AKT-4:
"sonst wird eine Herleitung an die falsche Groesse geheftet"). Entscheidungsvorlage EV-5.

### (c) D1-Degeneration (DEC-67 E3 / DEC-70: streng negativer Anteil >= 10 % in der Median-Woche)

| | W1 | W2 |
|---|---:|---:|
| chronologische Median-Woche (Code-Konvention `decile_degeneration_window_summary`) | 2024-12-23: 0,524 | 2025-12-29: 0,714 |
| Median der Wochenanteile | 0,672 | 0,694 |
| Minimum / degenerierte Einzelwochen | 0,027 / 4 von 52 | 0,219 / 0 von 51 |
| Klumpen-Anteil (Schluessel exakt 0), Median | 0,260 | 0,173 |

**D1 nicht degeneriert** in beiden Fenstern [fj:A ...degeneration].

### (d) Schluessel-Spread der Formationswoche, `mean_U(key) - mean_D1(key)`, bp/Woche

| | Mittel | q10 | q25 | Median | q75 | q90 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| W1 | **175,8** | 73,5 | 88,0 | 148,0 | 238,8 | 307,0 | 38,1 | 621,5 |
| W2 | **339,6** | 139,7 | 216,5 | 354,4 | 460,6 | 543,1 | 74,5 | 692,0 |
| Nuisance-Basis | 145,3 | | | 112,4 | | | | |

Mittlerer Schluessel D1 / Universum: W1 -196,7 / -20,9 bp, W2 -385,2 / -45,6 bp [fj:A ...key_mean_*].

### (e) Intervallklassen (Modalklasse der Formationswoche) und W1/W2-Inhomogenitaet (DEC-58 E3)

| Anteil der Symbol-Wochen | W1 D1 | W1 U | W2 D1 | W2 U |
|---|---:|---:|---:|---:|
| 8h | 68,8 % | 76,2 % | 24,7 % | 36,1 % |
| 4h | 25,3 % | 22,3 % | 50,1 % | 55,6 % |
| 2h | 4,1 % | 1,2 % | 4,7 % | 2,0 % |
| 1h | 1,8 % | 0,3 % | **20,5 %** | 5,9 % |
| mindestens ein 1h-Tag in der Woche | 2,1 % | 0,3 % | **22,9 %** | 6,3 % |

**Schriftliche Feststellung der W1/W2-Inhomogenitaet (DEC-58 E3):** W1 liegt vor dem Auto-Switch (2025-10-30 [sek],
DEC-84), W2 ueberwiegend danach. In W2 ist D1 zu einem Fuenftel mit 1h-Symbol-Wochen besetzt - der Auto-Switch wird
durch Cap-/Floor-Treffer ausgeloest, die 1h-Klasse ist also selbst eine Folge extremen Fundings. Ohne 1h-Wochen
faellt der W2-Spread von 339,6 auf 197,6 bp (W1: 175,8 -> 164,1) [fj:A formationsseitige_sensitivitaeten.sets.<W>.spread_bp].
Eine W1/W2-Divergenz eines spaeteren Laufs ist deshalb nicht automatisch ein Regime-Befund. Die Persistenz innerhalb
der Formationswoche ist fuer 1h-Mitglieder niedriger (W2 0,493 gegen 0,650 fuer die uebrigen; W1 0,495 / 0,636;
Nuisance 0,575 / 0,585) [fj psi_innerhalb_formationswoche_nach_klasse].

Sonderpaare mit I = 0 (USDCUSDT, ETHBTCUSDT; DEC-82): 16 von 2.196 (W1) bzw. 9 von 2.875 (W2) D1-Symbol-Wochen;
Wochen mit ausschliesslich exakt-0-Funding in D1: 4 / 4; D1-Wochen mit weniger als 7 Funding-Tagen: 0 / 0
[fj:A ...d1_*]. Materiell unerheblich, Buchhaltung siehe Stufe 2.

---

## 3. Nuisance 2021-03-01..2024-06-30 (Etikett nach Regel 1), Konfiguration A, Basis K_t >= 117

> Etikett: nur Streuungs-/Kovarianz-Groessen und Verhaeltnisse; kein Rendite-Mittel ausgegeben oder gespeichert.

### 3.1 Streuung und Autokorrelation der Wochen-Gesamtrendite D1 minus Universum

| Groesse | Gesamt x | Preisbein p | Funding-Bein g |
|---|---:|---:|---:|
| SD (bp/Woche) | **354,5** | 338,2 | 71,7 |
| rho lag 1 / 2 / 3 / 4 | **-0,250** / 0,112 / 0,022 / -0,088 | -0,307 / 0,105 / -0,008 / -0,085 | 0,519 / 0,220 / 0,163 / 0,219 |
| c = 1 + 2*sum (1-k/T) rho_k (k <= 4) | 0,598 | 0,418 | 3,202 |
| c Bartlett (L = 4) | 0,717 | 0,595 | 2,313 |
| MBB-Varianzverhaeltnis (Block 4, 2.000 Ziehungen, Seed 53) | **0,756** | 0,642 | 2,015 |

Varianzanteile: Preisbein 0,910, Funding-Bein 0,041, Kovarianz 0,049; corr(p, g) = 0,127.
Blockweise SD: 2022-04..2023-04 344 bp (D1-Median 17), 2023-04..2024-04 377 bp (D1-Median 23). Gesamtbasis (K >= 10,
mit D1 1..33): 432 bp [fj:A nuisance.bases.*].

**Lesart:** Das Funding-Bein hat genau die Persistenz, die DEC-67 E4 fuer "Funding-basierte" Statistiken unterstellt
(c ~ 2..3, DEC-67: 1/0,41 = 2,44), traegt aber nur 4 % der Varianz. Die Gesamtrendite ist negativ autokorreliert
(lag 1 -0,25; Standardfehler von rho ~ 1/sqrt(114) = 0,094 [abg.]) - W_eff = 0,41 W ist fuer die A1-Statistik
empirisch widerlegt (EV-2).

### 3.2 Beta-Fehlanpassung D1 gegen Universum und faktorbedingte Streuung (A3-Lehre)

| | EW-Universum als Faktor | BTC als Faktor |
|---|---:|---:|
| PIT-Beta-Differenz delta = beta_D1 - beta_U (26 Wochen nachlaufend): Mittel / RMS | -0,058 / 0,116 | -0,042 / 0,137 |
| Modell-Faktorvarianz delta^2*Var(f), Anteil an der Modellvarianz | 19 % | 12 % |
| realisiert: Steigung Preisbein auf f_{t+1}, R^2 | 0,005, 0,0002 | 0,035, 0,005 |
| Modell-SD (Faktor + unabhaengige Idiosynkrasie) | 259 bp | 287 bp |
| kappa = realisierte Varianz x / Modellvarianz | **1,877** | 1,526 |

Die PIT-Betas sagen eine Faktorladung voraus, die sich realisiert nicht zeigt (R^2 ~ 0); umgekehrt ist die
realisierte Varianz 1,5..1,9-mal groesser als das Modell mit unabhaengigen Residuen - D1-Mitglieder teilen
gemeinsame Schocks (kappa > 1). Beides geht in die SD-Projektion (Abschnitt 4) ein.

A3-Faktoren (Faktorrenditen = Dezil-L/S auf mom1 / mom2 / mom4 / rev_gap im selben Universum, Haltewoche):
R^2 von x auf (mom1, rev_gap) 0,063, auf alle vier 0,066, zusaetzlich Markt 0,068; Residual-SD 343..350 bp,
Residual-MBB-Verhaeltnis 0,75 [fj:A nuisance.bases.K_ge_117.a3_factor_regression].

### 3.3 Persistenz des Funding-Beins (nur Verhaeltnisse)

| Schaetzer | Wert |
|---|---:|
| phi = Summe g / Summe s (Haltewochen-Funding-Spread / Formations-Spread) | **0,573** |
| dasselbe nur mit dem Schluessel (ohne I-Terme) | 0,573 |
| Steigung durch den Ursprung / Median der Wochenverhaeltnisse | 0,534 / 0,502 |
| Querschnitts-Korrelation key_t -> key_{t+1}, Pearson / Spearman (Wochenmittel) | 0,445 / 0,590 |
| D1-Verbleib in D1 der Folgewoche | 0,494 |

Die I-Terme der Haltewoche (Teilwochen, Sonderpaare) aendern phi nicht (0,5729 gegen 0,5728).

---

## 4. Vorab fixierte Rechenregeln (vor der Power-Rechnung festgelegt, `a1_power.py` Kopf)

1. **SD der Gesamtrendite je Fenster, bindend = Maximum von vier Projektionen:**
   P1 Nuisance-SD direkt; P2 kappa_EW * Modellvarianz des Fensters (EW-Faktor); P3 kappa_BTC * Modellvarianz (BTC);
   P4 (Nuisance-Varianz minus realisierte Faktorvarianz) skaliert mit dem Verhaeltnis der Fenster-Idiosynkrasie,
   plus die PIT-Faktorvarianz des Fensters (EW). Die Fenster-Modellvarianz nutzt nur formationsseitige Groessen:
   D1-Groesse, PIT-Betas und Residualvarianzen der Mitglieder, Faktor-SD des Fensters.

   | bp/Woche | P1 | P2 | P3 | P4 | **bindend** |
   |---|---:|---:|---:|---:|---:|
   | W1 | 354,5 | 372,9 | 328,3 | 357,1 | **372,9** |
   | W2 | 354,5 | 305,8 | 298,8 | 330,5 | **354,5** |

   Fenster-Eingaben: EW-Faktor-SD W1 13,2 % / W2 7,9 % (BTC 6,5 % / 5,3 %), delta W1 -0,128 / W2 -0,053, mittlere
   D1-Groesse 42,2 / 56,4 [fj:A fenster_formationsseitig.<W>.pit_beta_model, market_factor_sd_weekly]. Die hohe
   EW-Faktor-SD in W1 ist kein Ausreisser-Effekt (getrimmtes EW 13,0 %, IQR-SD 13,2 %) [S:a1_check_factor.py].
2. **Autokorrelation:** bindend `c = max(1, gemessen)` = 1 (keine Gutschrift fuer die negative Autokorrelation);
   Varianten: gemessenes MBB-Verhaeltnis 0,756 und DEC-67 E4 (c = 1/0,41 = 2,439).
3. **SE je Fenster** = max(SE des Mittelwert-Tests, SE des Residual-Alpha-Tests gegen mom1/rev_gap) mit
   SE_alpha = sigma * sqrt(1 - R^2) * sqrt(c/W) * sqrt(W/(W-3)). Ergebnis: Mittelwert-Test bindet
   (W1 51,71 gegen 51,57; W2 49,16 gegen 49,02 bp).
4. **W = 52 je Fenster** (Auftrag; W_judged ist 52 / 51), gepoolt 104; SE_gepoolt = sqrt(SE_W1^2 + SE_W2^2)/2.

---

## 5. A-priori-Effekt `prem_prior`

`prem_prior_W = Spread_W (Mittel der Formationswochen, Abschnitt 2 (d)) * phi (0,573, Abschnitt 3.3) * theta`.

**theta = Anteil des Funding-Vorteils, der NICHT durch das Preisbein kompensiert wird: UNBELEGT.** Die PRD fuehrt die
Zahler-Erosions-Zitate selbst als UNBELEGT (PRD 5.1); aus den Daten ist theta nur ueber das Rendite-Mittel
bestimmbar, das Regel 1 sperrt. Gerechnet wird das Gitter des Auftrags; die Nullhypothese ist theta = 0 (exakte
Kompensation), theta = 1,0 ist die Obergrenze "gar keine Kompensation". **Das Funding-Bein ist nicht der Effekt** -
unter der Null wird es vollstaendig vom Preisbein aufgezehrt.

| theta | prem W1 | prem W2 | prem gepoolt |
|---:|---:|---:|---:|
| 0,25 | 25,2 | 48,6 | 36,9 |
| 0,5 | 50,3 | 97,3 | 73,8 |
| 1,0 | 100,7 | 194,5 | 147,6 |

(bp/Woche; oekonomisches Etikett PRD 5.1: 36 bp/Woche, kein Gate, C.2.)

---

## 6. Power, Zuordnungsregel PRD 5.1 und GL-012, Konfiguration A

Formeln (PRD 5.1, mit der SE aus Abschnitt 4): `P_fenster = Phi(prem/SE_W - 1,6449)`; P >= 0,60 -> C.10 hart,
sonst DEC-52; GL-012, wenn `3,1680 * SE_gepoolt > prem_gepoolt`. Zusaetzlich berichtet: MDE80 je Fenster
`2,4865 * SE_W` (DEC-51 (2)) und die Power eines Gates mit Schwelle `2,4865 * SE_W` (PRD-5.1-Schwellentext,
A3-Konvention `IC_min`): `Phi(prem/SE_W - 2,4865)` (EV-4).

### 6.1 Bindend (c = 1)

| theta | SE W1 / W2 | P_fenster W1 / W2 | Zuordnung | 3,168*SE_gep. | prem gep. | GL-012 | C.10 gemeinsam | Gate-Power (Schwelle 2,4865 SE) W1 / W2 |
|---:|---|---|---|---:|---:|---|---:|---|
| 0,25 | 51,7 / 49,2 | 0,123 / 0,256 | DEC-52 | 113,0 | 36,9 | **ja** | 0,032 | 0,023 / 0,067 |
| 0,5 | 51,7 / 49,2 | 0,251 / 0,631 | DEC-52 (W1) | 113,0 | 73,8 | **ja** | 0,158 | 0,065 / 0,306 |
| 1,0 | 51,7 / 49,2 | **0,619 / 0,990** | **C.10 hart** | 113,0 | 147,6 | **nein** | **0,612** | 0,295 / 0,929 |

DEC-52-Zweig bei theta = 1 (nur Information; nach DEC-52 (i) bei P >= 0,60 nicht anwendbar): gepoolte Power bei
alpha 0,01 0,965; Fenster-Screens bei 0,5 * 2,3263 * SE_gep. 0,874 / 0,999 (Produkt ~0,84), bei 0,5 * 3,168 * SE_gep.
0,804 / 0,998 (Produkt ~0,77) [fj:A power.grid."c1_binding|theta=1.0".pooled].

MDE80 je Fenster (Signifikanz-Konvention): W1 **128,6 bp**, W2 122,2 bp; MDE80 des Gates mit Schwelle 2,4865 SE:
W1 172,1 bp, W2 163,6 bp. **W1 erreicht DEC-51 (2) (Power 0,80) bei keinem theta <= 1.**

Kleinstes theta je Kriterium: GL-012-frei **0,766**; P_W1 >= 0,60 0,975; P_W2 >= 0,60 0,480; MDE80_W1 <= prem
1,277 (> 1); MDE80_W2 <= prem 0,628 [fj:A power.grid."c1_binding|theta_min"].

### 6.2 Varianten der Autokorrelation (theta = 1,0)

| c | SE W1 / W2 | P W1 / W2 | 3,168*SE_gep. vs prem | GL-012 | theta_min GL-012 |
|---|---|---|---|---|---:|
| 1 (bindend) | 51,7 / 49,2 | 0,619 / 0,990 | 113,0 < 147,6 | nein | 0,766 |
| 0,756 (MBB gemessen) | 45,0 / 42,7 | 0,724 / 0,998 | 98,3 < 147,6 | nein | 0,666 |
| 2,439 (DEC-67 E4) | 80,8 / 76,8 | 0,345 / 0,813 | **176,5 > 147,6** | **ja** | 1,196 |

---

## 7. Sensitivitaeten (theta = 1,0, c = 1) und Konfiguration B

| Variante | prem W1 / W2 | P W1 / W2 | 3,168*SE_gep. vs prem gep. | GL-012 |
|---|---|---|---|---|
| bindend (Abschnitt 6.1) | 100,7 / 194,5 | 0,619 / 0,990 | 113,0 / 147,6 | nein |
| phi als Steigung (0,534) | 93,8 / 181,2 | 0,567 / 0,979 | 113,0 / 137,5 | nein |
| phi als Median-Verhaeltnis (0,502) | 88,2 / 170,4 | 0,524 / 0,966 | 113,0 / 129,3 | nein |
| Median statt Mittel des Spreads | 84,8 / 203,0 | 0,498 / 0,994 | 113,0 / 143,9 | nein |
| phi skaliert mit Persistenz innerhalb der Formationswoche (0,599 / 0,552) | 105,3 / 187,6 | 0,652 / 0,985 | 113,0 / 146,4 | nein |
| phi skaliert mit Schluessel-Autokorrelation (0,427 / 0,321) | 75,1 / 109,0 | 0,424 / 0,717 | 113,0 / 92,1 | **ja** |
| nur W2-Spread ohne 1h-Wochen | 100,7 / 113,2 | 0,619 / 0,745 | 113,0 / 107,0 | **ja** |
| sigma = groesste 52-Wochen-Block-SD (377) | 100,7 / 194,5 | 0,610 / 0,981 | 117,3 / 147,6 | nein |
| sigma = Gesamtbasis K >= 10 (432) | 100,7 / 194,5 | 0,514 / 0,945 | 134,3 / 147,6 | nein |
| **Konfiguration B** (1h-Symbol-Wochen look-ahead-frei aus U_t) | 90,8 / 109,3 | 0,524 / 0,699 | **116,2 / 100,0** | **ja** |
| Konfiguration B, c = MBB 0,803 | 90,8 / 109,3 | 0,602 / 0,780 | 104,1 / 100,0 | **ja** |

Konfiguration B im Einzelnen [fj:B]: Spread W1 164,1 / W2 197,6 bp; Nuisance-SD 363,9 bp, phi 0,553; bindende SD
383,7 / 363,9 bp; theta_min GL-012 = 1,161 (c = 1), 1,041 (MBB), 1,814 (DEC-67) - **in B ist A1 bei keinem
theta <= 1 testbar.** Kill (3): 200 Symbole; Kill (4): 0,403 / 0,316; Degeneration: Median-Woche 0,524 / 0,682 -
keiner ausgeloest.

Welche Sensitivitaet kippt: die beiden, die die schnellere Rueckbildung der W2-1h-Episoden abbilden (1h-Ausschluss,
Schluessel-Autokorrelation W2 0,303 gegen 0,540 in der Nuisance-Periode). Die Persistenz innerhalb der Formationswoche
spricht dagegen nicht fuer einen Abfall in W2 (0,574 gegen 0,595). Welche Lesart zutrifft, ist ohne Outcome nicht
entscheidbar.

---

## 8. Feststellung zur Stopp-Regel und Folgen

**Stopp-Regel (Auftrag):** "Ist A1 selbst bei theta = 1,0 in der GL-012-Pruefung nicht testbar, hoere hier auf."
In Konfiguration A mit der SE des registrierten Mittelwert-Tests (c = 1, ebenso c = MBB) ist A1 bei theta = 1,0
**nicht** GL-012. **Die Stopp-Regel greift nicht; Stufe 2 ist erstellt** (`ENTSCHEIDUNGSVORLAGEN.md`,
`ERSTFASSUNG_H31_entwurf.md`), **als bedingter Entwurf**: Die strenge Lesart von EV-1 oder EV-2 beendet A1 vor dem
Design als GL-012, unabhaengig von theta; EV-3 in der A3-Lesart ebenso, EV-4 (b) und EV-5 (b) fast oder ganz.

| Vorlage | Frage | Folge der strengen Lesart |
|---|---|---|
| EV-1 | 1h-Symbol-Wochen: primaer eingeschlossen (A) oder ausgeschlossen (B, DEC-58 E3)? | B: GL-012 bei jedem theta <= 1 |
| EV-2 | Gilt DEC-67 E4 (W_eff = 0,41 W) fuer die A1-Gesamtrendite? | ja: GL-012 bei jedem theta <= 1 |
| EV-3 | DEC-51 (2) je Fenster (Praezedenz DEC-87 (F), GL-032) zusaetzlich zur PRD-5.1-Regel? | ja und ohne DEC-52-Zweig (wie A3): GL-012 bei jedem theta <= 1; mit DEC-52-Zweig GL-012 fuer theta >= 0,975 |
| EV-4 | Schwelle = kritischer Wert (1,6449 SE) oder MDE (2,4865 SE, PRD-5.1-Text)? | MDE: Gate-Power W1 0,30 bei theta = 1 -> DEC-52; gepoolte Power 0,80 erst ab theta 0,969 |
| EV-5 | Kill (4): WP-7-Schaetzer oder Buehlmann-Straub-Ersatz? | BS woertlich: Kill (4) ausgeloest |
| EV-6 | Quelle fuer theta >= 0,77 | ohne Quelle: Registrierung blockiert (UNBELEGT) |

**Was ausdruecklich NICHT folgt:** kein Verdikt ueber den Funding-Carry; keine Zahl dieses Befunds stammt aus einer
Haltewoche nach 2024-06-30; die Nuisance-Persistenz ist ein Verhaeltnis, kein Praemienbeleg.

**UNBELEGT (blockierend):** theta (EV-6); die Rueckwechselregel 1h -> 4h an der Primaerquelle (DEC-82/84, nur
empirisch beschrieben); Kapital-Multiplikator m, Steuerregime (PRD 3.3.9, 8.2) - Etiketten, kein Gate.

---

## 9. Reproduktion

```
# aus einem Verzeichnis ausserhalb des Panel-Ordners; Panel nur gelesen
sh scratchpad/a1_herleitung/run_all.sh      # ~1 min; schreibt feasibility.json bitgleich (sha256 oben)
```

Zwei aufeinanderfolgende vollstaendige Laeufe (inklusive Neuladen des Panels) ergaben dieselbe sha256 von
`feasibility.json`; sie enthaelt die sha256 aller Skripte (`skripte`).
Unabhaengige Nachrechnung von Schluessel, Spread (175,78 / 339,57 bp), Nuisance-SD (354,47 bp) und phi (0,5729) mit
eigener Arithmetik: `a1_selfcheck.py` (Log `run_all.log`).
