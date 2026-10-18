# Programm-Bilanz Scinance 3.0: Power-Zensus - wo ist auf unserem Bestand Power 0,80 erreichbar? (Stand 2026-10-18)

> Herleitungs-Akte P-2 (Power, Rauschboden, Gate-Design). ENTWURF: nichts hier ist beschlossen oder registriert;
> entscheiden darf nur der Orchestrator, die Programmrichtung waehlt der Nutzer (PRD Par. 8). Keine Aussage dieser
> Akte lockert eine Regel zugunsten eines Kandidaten; Regelaenderungen erscheinen nur als programmweite Optionen mit
> Fehlerrate und Etikett (Teil C, Option 4).
>
> **Ergebnisblindheit (Regel 1 des Auftrags):** gerechnet wurde ausschliesslich mit Nuisance-Groessen, die in den
> Akten stehen (SD, Varianzfaktor c, Rauschboden, K, Literatur-Prior). Keine Outcome-Statistik, kein Panel-, DVOL-
> oder Trade-Laden, kein Katalogzugriff. Nicht geoeffnet: alle Siegeldateien (`*_L_window_sealed.json`,
> `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`), die WP-10(A2)/WP-10(A)-IV-RV-Dateien,
> `pair_corr_BTCUSDT_ETHUSDT.json` (Zeitraum reicht in den Blindbereich; rho = 0,815 stammt aus DEC-67). Blind-Siegel
> DEC-96 E3 (ab 2026-07-01) gewahrt. Aus `wp7_report.json` wurden nur K, SD_null, N_eff, sigma_LS und die
> Funding-Autokorrelation gelesen.
>
> **Rechenweg:** jede Power-, MDE- und Zuordnungszahl stammt aus `src/bybit_edge/research/power_p1.py`
> (`assign_regime`, `assign_regime_a3_practice`, `dec52_gate_power`, `window_power`, `mde80`, `effective_z`);
> die benoetigte Dauer ist der kleinste Fensterumfang n, bei dem der jeweilige `power_p1`-Befund eintritt (Bisektion,
> zwei gleich lange Fenster). Die geschlossene Formel `n = c * (z_mde * SD / prior)^2` ist Gegenprobe (stimmt fuer C10
> auf 1e-9). Skript `scratchpad/bilanz/bilanz_census.py` (sha256 im JSON-Feld `skript`), Zahlen in
> `state/programm_bilanz.json` (Kuerzel `[pb:<pfad>]`), Tabellen gerendert mit `scratchpad/bilanz/make_tables.py`.
> Kuerzel: `[sek]` Sekundaerbeleg, `[abg.]` hier abgeleitet, UNBELEGT = keine Fundstelle, blockiert.

---

## 0. Befund in Kuerze

1. **Die drei Kandidaten scheitern an derselben Groesse: SD der Teststatistik relativ zum Literatur-Prior.** Unter
   P-1 (DEC-94) braucht jedes Fenster `n = c * (2,4865 * SD / prior)^2` Einheiten; der Prior geht quadratisch ein.
   Mit bindender Nuisance und zentralem Prior ergibt das (zwei blinde Fenster, C.10):
   - **VRP (H-27-Design, BTC, Tagesschluss-RV):** 672 Tage je Fenster; ab 2026-07-01 **voll am 2030-04-04**
     (DEC-52-Gate 736 Tage -> 2030-08-10; A3-Praxis 1.204 Tage -> 2033-03-03). Prior-Band 7,00..13,72 VP:
     2033-04-24 .. 2028-05-02.
   - **A3 Roh-IC (mom1, bindend W1-stress):** 119 Wochen je Fenster; ab 2026-10-05 **voll am 2031-05-11**
     (rev_gap 132 Wochen -> 2031-10-26; unter measured 57 Wochen -> 2028-12-10; A3-Praxis 214 Wochen -> 2034-12-17).
   - **A1:** theta UNBELEGT blockiert unabhaengig von jeder Dauer. Bedingt: theta = 1 und W1-artiger Spread 85 Wochen
     -> 2030-01-06; theta = 0,77 143 Wochen -> 2032-04-11; theta = 0,5 339 Wochen -> 2039. Unter DEC-67 E4 jeweils
     x2,44. Der Formationsspread des kuenftigen Fensters (W1 176 gegen W2 340 bp/Woche) aendert die Dauer um Faktor ~4.
2. **DEC-52 ist bei zwei gleich starken Fenstern kein Abkuerzungsweg:** das Produkt-Gate braucht ~9,5 % mehr Daten
   als C10 (672 -> 736 Tage). Es hilft nur bei ungleichen Fenstern (A1 W1/W2-artig: 85 -> 51 Wochen).
3. **Welcher Hebel wo wirkt (Abschnitt 2.8):** Zeit wirkt ueberall, aber nur mit der Wurzel. Mehr Symbole helfen A3
   im bindenden Fall hoechstens -14 % (Faktor-Streuung dominiert), eine zweite Boerse mit denselben Coins praktisch
   nicht. BTC+ETH als ein VRP-Bein: -4 bis -9 %. Hochfrequenz-RV: -34 % (UNBELEGT, SD 15,1 statt 18,6), mit Konsens-c
   -57 %. Nicht ueberlappende Monatsziele: +8 % (schlechter). Beta-Neutralisierung (fm_neutral_8w als
   Primaerstatistik): A3 -81 % (23 statt 119 Wochen, voll 2027-08-22) - aber NEUE Hypothese (DEC-58 E2, DEC-92),
   Prior fuer den neutralisierten IC UNBELEGT. A1-Hedge gegen A3-Faktoren: -7 %. Ereignisdesigns (A2: 52 Wochen-
   verfaelle je Jahr, Trades seit 2020) haben die meisten unabhaengigen Einheiten, sind aber durch V-5b/c gesperrt,
   nicht durch Daten.
4. **Doppelausweis:** unter der A3-Praxis (Schwelle 2,4865 SE) verlaengert sich jede C10-Dauer um Faktor 1,79.
   Mehrere Zuordnungen sind nur unter P-1 zulassungsfaehig (Etikett "zugelassen nur durch DEC-94"), z. B. A2
   Monatsverfaelle mit 3-Jahres-Fenstern, H-27 am oberen Prior-Rand.
5. **Datenbedarf, Top-3 (Teil B):** (1) taeglicher Panel-Strom aller Perps (Variante B, irreversibel: PIT-Roster und
   Delistungen) - Voraussetzung jedes blinden A3/A1-Fensters; (2) Inhaltsprobe und ggf. 15-min-Schnappschuss der
   datierten Futures (A4, irreversibel); (3) 1-Minuten-Kerzen BTCUSDT/ETHUSDT mit Backfill ab 2021-03 (macht die
   UNBELEGTE HF-RV-Zahl messbar und liefert die A2-Nuisance; ~0,1-0,3 GB statt ~183 GB Trades).
6. **Teil C** legt fuenf Optionen neutral vor (Recording-first mit Entsperrdaten, Ereignis-/Einheiten-Designs, HF-Weg
   VRP, programmweite Regelaenderung nur ausgewiesen, Pause/Abschluss). Zwei Strukturbefunde fuer die Entscheidung:
   die blinden Fenster sind ein Einmal-Gut (jede Hypothese, die auf ihnen laeuft, verbraucht sie), und die
   Zwei-Fenster-Regel ist bei gleicher Gesamt-Fehlerrate kein Zeitfresser (ein Fenster mit alpha 0,0025 braucht 7,7 %
   MEHR Daten) - die Dauer treibt das Power-Ziel je Fenster.
7. **H-26 (2.0, nur Status):** nach der 2.0-Lesart der `done_days` faellt die Entsperrung (~Mitte November 2026) so,
   dass mindestens das zweite H-26-Fenster im Blindbereich ab 2026-07-01 laege - Konflikt mit DEC-96 E3/DEC-97, offen
   fuer den Orchestrator (Abschnitt 2.6).
8. **Was nicht folgt:** kein Verdikt ueber Momentum, Reversal, Carry oder VRP; die Daten sind Zeitpunkte, an denen
   die Power-Zeile bei unveraenderter Nuisance erreichbar WAERE, keine Zusagen.

---

## 1. Grundlage und Konvention

### 1.1 Regeln

- **P-1 (DEC-94):** Schwelle je Fenster `z_krit * SE` mit z_krit 1,6449; Power 0,80 je Fenster (DEC-51 (2)) ->
  MDE-Faktor 2,4865; SE der Power-Zeile = SE des registrierten Tests, inklusive Varianzfaktor `c = max(1, c_hat)` der
  Teststatistik (DEC-94 (4)); bindend ist die groessere SE ueber Quellen und Kalibrierungen (DEC-94 (5), stress).
- **Zuordnung (DEC-94 (6)):** alle Fenster >= 0,80 -> C10; sonst DEC-52-Gate (gepoolt z 2,5287, Screens 0,5x je
  Fenster, Produkt-Power >= 0,80) -> DEC52; sonst GL012. Ein-Fenster-Designs haben keinen DEC-52-Zweig.
- **Doppelausweis (DEC-94 (9)):** A3-Praxis = Schwelle 2,4865 SE je Fenster (MDE-Faktor 3,3281), DEC-87 (F) ohne
  DEC-52; zusaetzlich ausgewiesen: DEC-52-Gate mit dem alten gepoolten Faktor 3,1680 (`allow_dec52`, Bericht).
- **Selektionsdecke (DEC-94 (7)):** `z = max(1,6449, z_max(K))`; bindet erst ab K = 12 (z_max 1,665), K = 20:
  1,901 (+22 % Dauer, Abschnitt 2.1).

### 1.2 Formel und Lesart der Dauer

`n_C10 = c * (z_mde * SD / prior)^2` mit z_mde = 2,4865 (P-1) bzw. 3,3281 (A3-Praxis), SD = SD der getesteten
Statistik je Einheit (Woche, Tag, Ereignis, Zyklus), c = Varianzfaktor. Daraus drei allgemeine Folgerungen
`[abg.]`:
- Prior +/-25 % -> Dauer x0,64 / x1,78; SD -10 % -> Dauer x0,81.
- DEC-52 (gleiche Fenster): Zulassung erst bei prior/SE ~2,60 statt 2,4865 -> Dauer x1,095; nur bei ungleichen
  Fenstern kuerzer als C10 (Herleitung P-1, ENTWURF 5.2).
- A3-Praxis gegen P-1: x(3,3281/2,4865)^2 = x1,79.

### 1.3 Fruehestmoeglicher blinder Start und Datumsregel

| Kandidat | Start | Begruendung | "voll am" |
|---|---|---|---|
| A3, A1 | **2026-10-05** (Montag der ersten vollen ISO-Woche im Oktober) | Auftrag: Panel-Strom ab Verfuegbarkeit, fruehestens 2026-10. Voraussetzung: Variante B liefert lueckenlos ab 2026-09-29 (Zip endet 2026-09-28) inklusive Delistungen, und keine A3/A1-Outcome-Groesse dieser Wochen wird vor dem Lauf berechnet. Blindheit, nicht Strombeginn, bestimmt den Start (Muster DEC-96). Jede Woche spaeter verschiebt alle Daten um eine Woche. | letzter Tag der letzten Halte-Woche: Start + 2 x n Wochen - 1 Tag |
| VRP (H-27-Design und jede neue VRP-Hypothese) | **2026-07-01** | DEC-96 E1/E3, DEC-97 | letzter RV-Zieltag: Start + 2 n - 1 + 30 Tage |
| A4 | Aufzeichnung seit **2026-06-16**; registrierbar fruehestens **2027-06-16** (12 Monate, DEC-59) | Urteilsfenster beginnen am ersten Quartalsverfall danach (2027-06-25) | Quartalsverfall nach 2 x N Zyklen |
| A2 | historisch (Trades seit 2020-03-25) | gesperrt durch V-5b/c, nicht durch Daten | - |

Ein frueherer A3/A1-Start (Juli 2026) waere nur nach einer Blindheits-Inventur der Wochen 2026-07..09 denkbar (die
WP-7-Serien bis 2026-09-14 liegen versiegelt vor); hier nicht angenommen.

### 1.4 Quellen der Nuisance (nur Akte)

| Kandidat | Groesse | Wert | Fundstelle |
|---|---|---|---|
| A3 | SD(IC_t) Roh-IC je Fenster und Kalibrierung (Null-Simulation, 300 Rep.) | W1 0,0901 / 0,1302, W2 0,0610 / 0,0817 (mom1, measured/stress) | `runs/wp13a_20261012_v5e/wp13a_prelaunch.json` `windows.<W>.beta_control_method_study.calibrations.<cal>.methods.none.variants.<v>.factor_sd` |
| A3 | c_hat der Teststatistik = W * SD(Mittel-IC ueber Rep.)^2 / SD(IC_t)^2 | 0,93..1,16 roh; 1,11..1,27 fm8 (MC-Fehler ~8 %) | dito, `mean_ic_draws_sd` `[abg.]` |
| A3 | Rauschboden E_t[1/sqrt(K_t-1)], w_judged, K | W1 0,0486 / 52 / 345..514; W2 0,0419 / 51 / 514..603 | dito `noise_floor_and_threshold.floor` |
| A1 | SD Gesamtrendite D1 - Universum (bindende Projektion), c_hat, phi, Formationsspread | 372,9 (W1-Proj.) / 354,5 bp (Nuisance direkt); MBB 0,756 (-> c = 1); phi 0,573; Spread 145,3 / 175,8 / 339,6 bp | `herleitung_a1/feasibility.json` `configs.A_dec70_1h_eingeschlossen.power.inputs`, `.formationsseitige_sensitivitaeten` |
| H-27 | SD S1 (BTC), c nach Regel P-3, Konsens-c, Prior-Band, Monatsvariante, SE_null | 18,60 VP; 28,17; 18,6 (Review); 9,47 (7,00..13,72; pi-1 10,48); SD_m 18,70, c_m 1; 4,17 (n 365) | `herleitung_h27/feasibility.json` `nuisance.BTC.S1`, `power.configs.BTC/S1.priors`, `nullwelt`; `REVIEW_H27.md` B-1/B-2 |
| H-27 | HF-RV-SD | ~15,1 (UNBELEGT, Delta-Methode) | `REVIEW_H27.md` B-1 |
| A2 | 30-min-SD, Placebo-SE, rho(BTC,ETH) | 36 bp (PRD-Arbeitswert, UNGEMESSEN), 1,93 / 5,40 bp, 0,815 (DEC-67) | PRD 5.2, DEC-67 E4 |
| A4 | sigma_w | UNGEMESSEN | PRD 5.4, DEC-59 |
| alle | WP-7: SD_null 0,0411 / gepoolt 0,0440; K je Woche Median 252 (Vollhistorie); N_eff 182 (52 W) / 97 (104 W); sigma_LS 4,51 %; Funding-AK lag1 0,433 | - | `runs/wp7_20260921/wp7_report.json` |

---

## 2. Teil A - Power-Zensus je Kandidat

### 2.1 A3 (Wochen-Rang-IC, Design H-28_mom1 / H-29_rev_gap; Prior 0,03 [sek])

**Nuisance** `[pb:A3.windows]`:

| Fenster-Basis | Kalibrierung | Variante | SD(IC_t) roh | c_hat (Null) | SD fm8 | c_hat fm8 | Boden | K min/Median/max |
|---|---|---|---:|---:|---:|---:|---:|---|
| W1 | measured | mom1 | 0,0901 | 1,015 | 0,0480 | 1,269 | 0,0486 | 345/419/514 |
| W1 | measured | rev_gap | 0,0889 | 1,150 | 0,0483 | 1,121 | 0,0486 | 345/419/514 |
| W1 | stress | mom1 | 0,1302 | 1,025 | 0,0511 | 1,271 | 0,0486 | 345/419/514 |
| W1 | stress | rev_gap | 0,1286 | 1,157 | 0,0513 | 1,109 | 0,0486 | 345/419/514 |
| W2 | measured | mom1 | 0,0610 | 0,930 | 0,0405 | 1,181 | 0,0419 | 514/589/603 |
| W2 | measured | rev_gap | 0,0612 | 1,066 | 0,0412 | 1,105 | 0,0419 | 514/589/603 |
| W2 | stress | mom1 | 0,0817 | 0,931 | 0,0425 | 1,193 | 0,0419 | 514/589/603 |
| W2 | stress | rev_gap | 0,0817 | 1,135 | 0,0433 | 1,124 | 0,0419 | 514/589/603 |

Lesart: Fuer kuenftige blinde Fenster ist die Vorperioden-Statistik (W1/W2-IC) versiegelt; nach DEC-94 (5) bleibt
nur die kalibrierte Null (ii), bindend die groessere SE -> **W1-stress**. W2 ist die guenstigste Lesart (Richtung
Testbarkeit), weil die Marktfaktor-Vol im kuenftigen Fenster unbekannt ist.

**Benoetigte Dauer** (zwei gleiche Fenster, c = max(1, c_hat)) `[pb:A3.windows.<W>.cells.<cal|v|none>.dur_c]`:

| Basis | Variante | Wochen je Fenster C10 P-1 | DEC-52-Gate P-1 | C10 A3-Praxis | DEC-52 A3 (3,168) | voll (C10 P-1) | voll (A3-Praxis) | mit c = 1: C10 P-1 / A3 |
|---|---|---:|---:|---:|---:|---|---|---|
| **W1-stress (bindend)** | mom1 | **119,3** | 130,7 | 213,8 | 171,5 | **2031-05-11** | 2034-12-17 | 116,5 / 208,7 |
| W1-stress | rev_gap | 131,5 | 144,0 | 235,6 | 189,0 | 2031-10-26 | 2035-10-21 | 113,6 / 203,5 |
| W1-measured | mom1 | 56,7 | 62,0 | 101,5 | 81,4 | 2028-12-10 | 2030-09-01 | 55,8 / 99,9 |
| W1-measured | rev_gap | 62,5 | 68,4 | 111,9 | 89,8 | 2029-03-04 | 2031-01-19 | 54,3 / 97,3 |
| W2-stress | mom1 | 45,9 | 50,2 | 82,2 | 65,9 | 2028-07-09 | 2029-12-09 | 45,9 / 82,2 |
| W2-stress | rev_gap | 52,0 | 57,0 | 93,2 | 74,8 | 2028-10-15 | 2030-05-12 | 45,9 / 82,2 |
| W2-measured | mom1 | 25,6 | 28,0 | 45,8 | 36,7 | 2027-10-03 | 2028-07-09 | 25,6 / 45,8 |
| W2-measured | rev_gap | 27,4 | 30,0 | 49,1 | 39,4 | 2027-10-31 | 2028-09-03 | 25,7 / 46,0 |

Formel-Gegenprobe W1-stress mom1: `1,0245 * (2,4865 * 0,13021 / 0,03)^2 = 1,0245 * 116,5 = 119,3` Wochen. Die STAND-Zahlen (~56 / ~116)
sind die Werte mit c = 1.

**Prior-Sensitivitaet** (W1-stress mom1; kein Literaturband vorhanden, Illustration `[pb:A3.prior_sensitivitaet_W1_stress_mom1]`):
Prior 0,02 / 0,025 / 0,03 / 0,04 -> C10 P-1 268,5 / 171,8 / 119,3 / 67,1 Wochen (A3-Praxis 481,0 / 307,9 / 213,8 /
120,3).

**Einheiten statt Dauer - mehr Symbole hilft kaum** (Zerlegung `SD^2 = Boden(K)^2 + F^2`, F = faktorbedingter Anteil,
additive Naeherung `[abg.]`, Boden skaliert mit 1/sqrt(K-1); mom1, c wie oben) `[pb:...breadth_lever]`:

| Basis | F | K wie gemessen | 2 K | 4 K | K -> unendlich | Gewinn max. |
|---|---:|---:|---:|---:|---:|---:|
| W1-stress | 0,1208 | 119,3 | 111,0 | 106,9 | 102,7 | -14 % |
| W1-measured | 0,0759 | 56,7 | 48,4 | 44,3 | 40,2 | -29 % |
| W2-stress | 0,0701 | 45,9 | 39,8 | 36,8 | 33,8 | -26 % |
| W2-measured | 0,0443 | 25,6 | 19,5 | 16,5 | 13,5 | -47 % |

Im bindenden Fall traegt die faktorbedingte Streuung 86 % der Varianz; selbst unendlich viele Symbole kuerzen nur
um 14 %. Das Bybit-Universum ist bereits vollstaendig (K 345..603). **Zweite Boerse (Binance-Perp-Panel):** dieselben
Coins tragen dieselbe Marktfaktor-/Beta-Struktur, F ist gemeinsam; der Gewinn ist durch die Zeile "K -> unendlich"
nach oben begrenzt und fuer doppelt gelistete Coins ~0 `[abg.]`. Kein Datenauftrag (Teil B, B-6).

**Hochfrequenz-Statistiken:** kein Hebel (Wochen-IC auf Tagesdaten; die Streuung ist Querschnitts-, nicht
Messrauschen). **Autokorrelation:** c_hat ~1, nichts zu gewinnen.

**Neutralisierung (Option, NEUE Hypothese):** `fm_neutral_8w` als Primaerstatistik senkt die SD auf 0,043..0,051
(c_hat 1,11..1,27) `[pb:A3.windows.<W>.cells.<cal|v|fm_neutral_8w>]`:

| Basis | Variante | SD fm8 | c | Wochen C10 P-1 | C10 A3-Praxis | voll P-1 | voll A3 |
|---|---|---:|---:|---:|---:|---|---|
| **W1-stress** | mom1 | 0,0511 | 1,271 | **22,8** | 40,8 | **2027-08-22** | 2028-04-30 |
| W1-stress | rev_gap | 0,0513 | 1,109 | 20,0 | 35,9 | 2027-07-25 | 2028-02-20 |
| W1-measured | mom1 | 0,0486 | 1,269 | 20,6 | 36,9 | 2027-07-25 | 2028-03-05 |
| W2-stress | mom1 | 0,0425 | 1,193 | 14,8 | 26,5 | 2027-05-02 | 2027-10-17 |
| W2-measured | mom1 | 0,0419 | 1,181 | 14,3 | 25,5 | 2027-05-02 | 2027-10-03 |

Vorbehalte (bindend fuer jede Lesart): (a) nach DEC-92 E4 / DEC-58 E2 nur als neue Hypothese mit eigenem K und
eigener Vorab-Registrierung, Etikett "beschlossen nach Kenntnis von GL-032" und C.17 (Beta-Kalibrierungs-IC und
Lag-Profil gesehen); (b) der Prior 0,03 gilt fuer den ROHEN Rang-IC; welcher Teil davon die Beta-Neutralisierung
ueberlebt, ist UNBELEGT - der Prior des neutralisierten IC muss eine eigene Quelle haben; (c) das registrierte
Beta-Kontroll-Quantil (DEC-87 (E)) liegt unter P-1 beim Niveau 0,95 etwa bei `1,645 * SE_null` und damit in derselben
Groessenordnung wie die SE-Bedingung (Null-Mittel 0,0003..0,0012) - die Zahlen oben gelten naeherungsweise, exakt erst
mit der registrierten Null; (d) die c_hat > 1 der fm8-Statistik stammen aus der Null-Simulation (8-Wochen-Beta).

**Selektions-K** (W1-stress mom1, `[pb:A3.selektions_K_W1_stress_mom1]`): K 1..7 -> 119,3 Wochen (z_krit bindet);
K 12 -> 121,3; K 20 -> 145,2 Wochen.

**Historische Fenster W1/W2 unter P-1 (nur Bericht, nicht zulaessig: DEC-94 nicht rueckwirkend, GL-032 steht auf
stress):** measured mom1/rev_gap waeren DEC52 (Fenster 0,775/0,969, Gate 0,870 bzw. 0,785/0,968, 0,877), stress GL012
(0,507/0,836, Gate 0,462); A3-Praxis jeweils GL012. Reproduziert den P-1-Retro-Check (ENTWURF 4.1).

### 2.2 A1 (Funding-Long-Bein D1 gegen Universums-Hedge, DEC-70; Prior = Spread x phi x theta)

Prior-Bausteine: phi = 0,573 (Nuisance, Verhaeltnis), theta UNBELEGT (Gitter 0,5 / 0,77 / 1,0), Spread des kuenftigen
Fensters UNBEKANNT (formationsseitig erst im Fenster messbar; die Zuordnung muss aber vorher stehen) - deshalb vier
Spread-Annahmen. SD bindend 372,9 bp (Projektion W1, strengste bekannte); c = 1 unter P-1 (c_hat der Teststatistik
0,60..0,76, keine Gutschrift) bzw. 2,439 nach DEC-67 E4 (unter P-1 nur bei Nachweis der Schluessel-Persistenz in
der Teststatistik; der Nachweis fehlt) `[pb:A1.grid]`:

| Spread-Annahme (bp/Woche) | theta | prem (bp) | c | C10 P-1 | DEC-52 P-1 | C10 A3-Praxis | DEC-52 A3 | voll C10 P-1 | voll A3 |
|---|---:|---:|---|---:|---:|---:|---:|---|---|
| Nuisance 2022-04..2024-06 (145,3) | 1,00 | 83,3 | 1 | 124,0 | 135,8 | 222,2 | 178,3 | 2031-07-20 | 2035-04-22 |
| Nuisance (145,3) | 0,77 | 64,1 | 1 | 209,2 | 229,0 | 374,8 | 300,7 | 2034-10-22 | 2041-02-17 |
| Nuisance (145,3) | 0,50 | 41,6 | 1 | 496,1 | 543,2 | 888,9 | 713,2 | 2045-10-22 | 2060-10-31 |
| **W1 (175,8)** | **1,00** | 100,7 | 1 | **84,8** | 92,8 | 151,9 | 121,9 | **2030-01-06** | 2032-08-01 |
| W1 (175,8) | 1,00 | 100,7 | 2,439 (E4) | 206,8 | 226,4 | 370,5 | 297,2 | 2034-09-10 | 2040-12-23 |
| W1 (175,8) | 0,77 | 77,5 | 1 | 143,0 | 156,6 | 256,2 | 205,6 | 2032-04-11 | 2036-08-10 |
| W1 (175,8) | 0,77 | 77,5 | 2,439 (E4) | 348,8 | 381,9 | 624,9 | 501,3 | 2040-02-19 | 2050-09-18 |
| W1 (175,8) | 0,50 | 50,3 | 1 | 339,1 | 371,3 | 607,6 | 487,5 | 2039-10-16 | 2050-01-23 |
| W2 ohne 1h-Wochen (197,6) | 1,00 | 113,2 | 1 | 67,1 | 73,5 | 120,2 | 96,4 | 2029-05-13 | 2031-05-25 |
| W2 ohne 1h (197,6) | 0,77 | 87,2 | 1 | 113,2 | 123,9 | 202,7 | 162,7 | 2031-02-16 | 2034-07-16 |
| W2 (339,6) | 1,00 | 194,5 | 1 | 22,7 | 24,9 | 40,7 | 32,7 | 2027-08-22 | 2028-04-30 |
| W2 (339,6) | 0,77 | 149,8 | 1 | 38,3 | 42,0 | 68,7 | 55,1 | 2028-04-02 | 2029-05-27 |
| W2 (339,6) | 0,50 | 97,3 | 1 | 90,9 | 99,5 | 162,8 | 130,6 | 2030-03-31 | 2033-01-02 |
| W2 (339,6) | 0,50 | 97,3 | 2,439 (E4) | 221,7 | 242,7 | 397,1 | 318,6 | 2035-04-08 | 2042-01-05 |

(Vollstaendiges Gitter inkl. SD 354,5 und aller E4-Zeilen im JSON; mit SD 354,5 statt 372,9 sinkt jede Dauer um 10 %,
z. B. W1/theta 1/c 1: 76,6 Wochen -> 2029-09-16.)

Lesart: Die Dauer haengt vor allem an zwei UNBELEGTEN Groessen: theta (Faktor 4 zwischen 1,0 und 0,5) und dem
Spread-Regime (Faktor ~4 zwischen W1 und W2; W2 ist durch den Auto-Switch seit 2025-10-30 aufgeblaeht, DEC-58 E3/
DEC-93 Etikett (iv)). Eine kuenftige A1-Registrierung muesste die Spread-Annahme vorab fixieren; bei theta = 1 liegen
die strenge Wahl (Nuisance 145,3: 2031-07-20; W1: 2030-01-06) und die guenstige (W2: 2027-08-22) 2,4 bis 4 Jahre
auseinander.

**Ungleiche Fenster (W1-artig, dann W2-artig; c = 1):** DEC-52 kuerzt hier tatsaechlich - theta 1: C10 84,8, Zulassung
DEC52 ab 50,6 Wochen (A3-Praxis 151,9 / mit DEC-52 bei 3,168: 65,2); theta 0,77: 143,0 / 85,3 `[pb:A1.ungleiche_fenster_W1_dann_W2]`.

**Hebel:** Hedge gegen A3-Faktoren und Markt (Nuisance R^2 0,068, Residual-SD 342,1 statt 354,5 bp): -7 % (84,8 ->
79,0 Wochen). Zweite Boerse: Preisbein (91 % der Varianz) liegt auf denselben Coins, Gewinn ~0, UNBELEGT. HF:
keiner. Autokorrelation: unter P-1 bereits c = 1. **Der einzige wirksame Hebel ist ein Beleg fuer theta**
(Literatur; eine Quelle mit Stichprobe aus W1/W2 waere Outcome-Information, DEC-93 E2).

**Historische Fenster W1/W2 (nur Bericht; GL-033 steht auf theta UNBELEGT, DEC-94 nicht rueckwirkend):** c = 1,
theta = 1: P-1 DEC52 (Fenster 0,619/0,990, Gate 0,812), theta_min unter P-1 0,986; A3-Praxis GL012; unter E4 auch P-1
GL012 (theta_min 1,540).

### 2.3 H-27 / VRP (BTC, S1 = IV - RV_fwd30 minus Nullwelt-J, taeglich, ueberlappende 30-Tage-Ziele)

`SE(n) = max(SD * sqrt(c / n), SE_null(n))`, SE_null skaliert aus n = 365 mit 1/sqrt(n) `[abg.]` (bindet nirgends).
Tage je Fenster; voll = letzter RV-Zieltag des zweiten Fensters ab 2026-07-01 `[pb:H27.configs]`:

| Konfiguration | SD | c | Prior | C10 P-1 | DEC-52 P-1 | C10 A3-Praxis | DEC-52 A3 | voll C10 P-1 | voll DEC-52 P-1 | voll A3 |
|---|---:|---:|---|---:|---:|---:|---:|---|---|---|
| **Referenz (Tagesschluss, c Regel P-3)** | 18,6 | 28,2 | **pi-2 zentral 9,47** | **671,8** | 735,5 | 1203,6 | 965,7 | **2030-04-04** | 2030-08-10 | 2033-03-03 |
| Referenz | 18,6 | 28,2 | pi-2 unten 7,00 | 1229,7 | 1346,3 | 2203,1 | 1767,6 | 2033-04-24 | 2033-12-14 | 2038-08-24 |
| Referenz | 18,6 | 28,2 | pi-2 oben 13,72 | 320,1 | 350,5 | 573,5 | 460,2 | 2028-05-02 | 2028-07-01 | 2029-09-20 |
| Referenz | 18,6 | 28,2 | pi-1 10,48 | 548,4 | 600,4 | 982,6 | 788,3 | 2029-08-01 | 2029-11-13 | 2031-12-17 |
| Tagesschluss, Konsens-c | 18,6 | 18,6 | pi-2 zentral | 443,6 | 485,6 | 794,7 | 637,6 | 2029-01-03 | 2029-03-28 | 2030-12-06 |
| HF-RV (UNBELEGT), c Regel | 15,1 | 28,2 | pi-2 zentral | 442,9 | 484,9 | 793,5 | 636,6 | 2029-01-01 | 2029-03-26 | 2030-12-04 |
| HF-RV (UNBELEGT), Konsens-c | 15,1 | 18,6 | pi-2 zentral | 292,4 | 320,1 | 523,9 | 420,3 | 2028-03-07 | 2028-05-02 | 2029-06-12 |
| HF-RV (UNBELEGT), Konsens-c | 15,1 | 18,6 | pi-2 oben 13,72 | 139,3 | 152,5 | 249,6 | 200,3 | 2027-05-06 | 2027-06-01 | 2027-12-12 |
| Bein BTC+ETH (Tagesmittel, ETH-Prior UNBELEGT) | 20,9 | 27,9 | 10,84 | 643,4 | 704,4 | 1152,6 | 924,8 | 2030-02-07 | 2030-06-09 | 2032-11-21 |

Gegenprobe: 672 / 736 Tage reproduzieren `herleitung_h27/feasibility.json` `power.configs.BTC/S1.days_needed_pi2_central`;
443 / 292 Tage reproduzieren REVIEW_H27 Pruefpunkt 4.

**Einheiten statt Dauer:**
- **BTC+ETH als ein Bein (DEC-62 E3):** theoretisch bei gleicher SD und gleichem Prior Varianzfaktor (1+rho)/2 =
  0,915 / 0,940 / 0,954 fuer rho 0,83 (Praemie, Akte) / 0,88 / 0,907 (WP-10(A2)-Konstanten) -> 615 / 632 / 641 statt
  672 Tage; mit den Akte-Werten des Tagesmittels (ETH streut staerker) 643 Tage. **Kaum Gewinn (-4 bis -9 %)**, dazu
  ETH-Prior UNBELEGT.
- Mehr Underlyings jenseits BTC/ETH: DVOL existiert nur fuer BTC/ETH (Katalog) - kein Datenweg.

**Design mit weniger Autokorrelation - nicht ueberlappende Monatsziele:** SD_m 18,70, ACF1 -0,16 -> c_m = 1 (keine
Gutschrift); 24,1 Monate = 724 Tage je Fenster (+8 %), voll 2030-07-17; Power bei 12 Monaten 0,543 gegen 0,575
ueberlappend `[pb:H27.monatsziele_nicht_ueberlappend]`. **Schlechter**, weil das ueberlappende Design dieselbe
Information (~13 unabhaengige Ziele je Jahr) bereits nutzt.

**HF-Statistik:** der einzige materielle Hebel (RV-Messrauschen ~34 % der Praemienvarianz, REVIEW_H27 B-1): -34 %
mit Regel-c, -57 % zusammen mit dem Konsens-c. **UNBELEGT bis zur Messung** auf der Vorperiode (Datenbedarf B-3);
als neue Hypothese mit eigenem K und Etikett "beschlossen nach Kenntnis der H-27-Feasibility (GL-034)".

**Fensterlaenge:** DEC-96 E2 laesst nur L in {6, 9, 12} Monaten zu; 672 Tage (22 Monate) waeren eine neue Hypothese
nach Kenntnis der Feasibility (DEC-97). Die Tabelle zeigt, was eine solche Hypothese braeuchte, keine Zulassung.

### 2.4 A2 (EXP-CLOCK, r_pre 07:30-08:00 UTC an Verfallstagen; GESPERRT V-5b/c)

Formel `[pb:A2]`: `SE(Delta) = sqrt( sigma30^2 * (1 + rho) / (2 N) + SE_placebo^2 )`, Cluster = Verfall (BTC+ETH ein
Cluster, rho 0,815 gemessen, DEC-67). `N_C10 ~ (1+rho)/2 * (2,4865 * sigma30)^2 / (prior^2 - (2,4865 * SE_placebo)^2)`.
sigma30 ist **UNGEMESSEN** (PRD-Arbeitswert 36 bp aus 2,5 % BTC-Tagesvol); der Prior ist fuer Wochenverfaelle
UNBELEGT (V-5b), fuer Monatsverfaelle nur aus Aktien [sek, 16,5 bp Ni/Pearson/Poteshman 2005].

| Verfallsmenge | Laenge je Fenster | N je Fenster | SE Ereignis | SE Placebo | SE(Delta) | MDE80 P-1 | MDE80 A3-Praxis | Prior | Power P-1 | Regime P-1 / A3 |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| woechentlich | 1 Jahr | 52 | 4,76 | 1,93 | 5,13 | 12,8 | 17,1 | UNBELEGT | - | - |
| woechentlich | 2 Jahre | 104 | 3,36 | 1,36 | 3,63 | 9,0 | 12,1 | UNBELEGT | - | - |
| woechentlich | 3 Jahre | 156 | 2,75 | 1,11 | 2,96 | 7,4 | 9,9 | UNBELEGT | - | - |
| monatlich | 1 Jahr | 12 | 9,90 | 5,40 | 11,28 | 28,0 | 37,5 | 16,5 [sek] | 0,428 | GL012 / GL012 |
| monatlich | 2 Jahre | 24 | 7,00 | 3,82 | 7,97 | 19,8 | 26,5 | 16,5 [sek] | 0,664 | GL012 / GL012 |
| monatlich | 3 Jahre | 36 | 5,72 | 3,12 | 6,51 | 16,2 | 21,7 | 16,5 [sek] | 0,813 | C10 / GL012 (nur durch DEC-94) |

(bp; Placebo-SE skaliert mit 1/sqrt(Jahre) aus den PRD-Werten `[abg.]`.) Monatsverfaelle mit 16,5 bp brauchen
2,89 Jahre je Fenster (A3-Praxis 5,17) - zwei Fenster passen nur mit Historie ab 2020 und unter Verzicht auf REZENZ.
Allgemein, Ereignisse je Fenster fuer C10 ohne Placebo (Untergrenze): prior/sigma30 = 0,5 / 0,33 / 0,25 -> 22 / 52 /
90 (A3-Praxis 40 / 92 / 161).

**Was gemessen werden muesste (vor jeder A2-Feasibility):** (1) V-5c - Primaerbeleg der Zeitlage relativ zu 08:00 UTC
(Richtung); (2) V-5b - Effektgroesse fuer die gewaehlte Ereignismenge; (3) sigma30 gepoolt BTC/ETH an Verfalls-
Freitagen und an den Placebo-Slots in einer Vorperiode vor dem ersten A2-Fenster (Datenbedarf B-3); (4) der
historische Deribit-Verfallskalender (seit wann woechentlich; B-4). **Siegel-Hinweis:** die PRD-Fenster (W2 bis
2026-08-31) reichen in den Blindbereich; jede A2-Rechnung muesste dort die BTC/ETH-Renditestreuung berechnen
(DEC-96 E3) - W2 muesste bei 2026-06-30 enden oder die Kollision vorher entschieden werden.

### 2.5 A4 (Perp gegen datierten Future; recording-first)

Formel `[pb:A4]`: `MDE80 = 2,4865 * sigma_w * sqrt(c / N)`, `N_C10 = c * (2,4865 * sigma_w / prior)^2`, Cluster =
Verfallzyklus (mehrere Basiswerte am selben Verfall = ein Cluster). sigma_w UNGEMESSEN, Prior UNBELEGT, w_null
(Margin-Regeln) UNGEMESSEN, V-4 (Liefergebuehr) offen.

| prior / sigma_w | N_C10 P-1 je Fenster | DEC-52-Gate P-1 | C10 A3-Praxis |
|---:|---:|---:|---:|
| 0,5 | 24,7 | 27,1 | 44,3 |
| 0,75 | 11,0 | 12,0 | 19,7 |
| 1,0 | 6,2 | 6,8 | 11,1 |
| 1,5 | 2,7 | 3,0 | 4,9 |

PRD-Design (8 Quartalszyklen, 4 je Haelfte): MDE80 = 1,243 sigma_w je Haelfte (bzw. 0,879 sigma_w, wenn N = 8 je
Fenster gelesen wird - der PRD-Text ist hier doppeldeutig). Zeitlinie: Aufzeichnung seit 2026-06-16 -> sigma_w als
Nuisance messbar ab 2027-06-16 (4 Quartalszyklen; eine SD aus 4 Werten ist sehr unsicher) -> erste Urteilsfenster ab
dem Quartalsverfall 2027-06-25 -> **4 Zyklen je Fenster voll am 2029-06-29**; braucht die Power mehr Zyklen
(prior < 1,24 sigma_w), entsprechend spaeter: 6 / 7 / 11 / 25 Zyklen je Fenster -> voll 2030-06-28 / 2030-12-27 /
2032-12-31 / 2039-12-30 (prior = sigma_w braucht 6,2, also 7 Zyklen) `[pb:A4.voll_nach_N_zyklen_je_fenster]`.

**Einheiten:** Bybit fuehrt 40 datierte USDT-Futures (woechentlich bis quartalsweise, 8 Basiswerte, V-2); kuerzere
Zyklen erhoehen N, senken aber je Zyklus den Wedge etwa proportional zur Laufzeit, waehrend die Streuung nur mit der
Wurzel faellt - der Informationsgewinn je Kalenderzeit ist bei unkorreliertem Funding etwa null `[abg.]`, real
UNBELEGT. Die Illiquiditaet (turnover24h 45.000..530.000 USD, inverse Quartale 2..77 USD) macht Quote-Rauschen zum
Teil von sigma_w.

### 2.6 A5 und H-26 (nur Bedingungen / Status)

**A5 (Skew-Praemie, GESPERRT nach E.6):** Entsperrung erst, wenn (a) V-4 die Delivery-/Exercise-Gebuehr an der
Primaerquelle klaert, (b) ein Options-Spread-Zensus mit durchgaengiger Bybit-Aufzeichnung vorliegt (setzt die
tagesgenaue Ketten-Luecken-Karte R3-K-37 Stufe 1 voraus) und (c) H-26 gemessen ist. Keine Power-Rechnung (Schwelle aus
der gemessenen Skew-Verteilung, PRD 5.5). Daten: Options-Ticker laufen seit 2026-06-16 (Deribit 14.810, Bybit im
tickers-Strom) - Inhalt (Snapshot oder Delta, bid/ask, IV) ungeprueft (B-5).

**H-26 (2.0-Registrierung, kapitalfrei, GESPERRT bis >= 210 zusammenhaengende `done_days` fuer `deribit/dvol` UND
`deribit/publicTrade` je Symbol; W1/W2 = erste/zweite 90 Beobachtungstage nach Strombeginn):**
- Stand laut 2.0-Inventur: 112 dvol-Tage am 2026-08-10 -> Entsperrung ~Mitte November 2026. Die Zaehlung ist im
  3.0-Bestand nicht nachgefuehrt (UNBELEGT), ebenso die Lueckenlosigkeit von `deribit/publicTrade` (ab 2025-08-01).
- Offene Lesart: Zaehlen per REST nachgeladene dvol-Tage (Luecke 2025-09-01..2026-03-19, DEC-96 Nachtraege) als
  `done_days`? (PRD 4.2: WP-9 entsperrt H-26 nicht; R4 3.4.)
- **Konflikt (Feststellung, keine Entscheidung):** in der 2.0-Lesart laege mindestens das zweite H-26-Fenster
  vollstaendig im Blindbereich ab 2026-07-01; ein H-26-Lauf wuerde DVOL- und RV-Statistiken dort berechnen, die DEC-96
  E3/DEC-97 fuer jede kuenftige VRP-Hypothese blind halten. Der Orchestrator muss die Reihenfolge entscheiden (H-26
  verbraucht die blinden VRP-Fenster oder bleibt gesperrt). Power nicht gerechnet (Auftrag: nur Status); H-26 traegt
  nach eigenem Text "~3 unabhaengige Bloecke je Fenster" als benannte Power-Grenze.

### 2.7 Zusammenfassung Doppelausweis (zentraler Prior, bindende Nuisance)

| Kandidat | Einheit | C10 P-1 | DEC-52 P-1 | C10 A3-Praxis | DEC-52 A3 (3,168) | in Monaten (C10 P-1 / DEC-52 P-1 / C10 A3) | voll C10 P-1 | voll A3 |
|---|---|---:|---:|---:|---:|---|---|---|
| A3 Roh-IC mom1 (W1-stress) | Wochen | 119,3 | 130,7 | 213,8 | 171,5 | 27,4 / 30,1 / 49,2 | 2031-05-11 | 2034-12-17 |
| A3-fm8 mom1 (W1-stress, neue Hyp.) | Wochen | 22,8 | 25,0 | 40,8 | 32,8 | 5,2 / 5,7 / 9,4 | 2027-08-22 | 2028-04-30 |
| A1 theta 1, W1-Spread, c 1 | Wochen | 84,8 | 92,8 | 151,9 | 121,9 | 19,5 / 21,3 / 34,9 | 2030-01-06 | 2032-08-01 |
| VRP Referenz | Tage | 671,8 | 735,5 | 1203,6 | 965,7 | 22,1 / 24,2 / 39,5 | 2030-04-04 | 2033-03-03 |
| VRP HF-RV + Konsens-c | Tage | 292,4 | 320,1 | 523,9 | 420,3 | 9,6 / 10,5 / 17,2 | 2028-03-07 | 2029-06-12 |
| A2 monatlich, 16,5 bp [sek] | Jahre | 2,89 | - | 5,17 | - | 34,7 / - / 62,1 | - | - |

"Zugelassen nur durch DEC-94" heisst bei fixierter Fensterlaenge (wie DEC-96 E2): die P-1-Dauer reicht, die
A3-Praxis-Dauer nicht. Faelle in dieser Akte: H-27 am oberen Prior-Rand bei L = 12 (FEASIBILITY H-27), A2
Monatsverfaelle mit 3-Jahres-Fenstern (2.4); bei jeder Fensterlaenge zwischen P-1- und A3-Dauer trifft es jeden
Kandidaten.

### 2.8 Hebel-Matrix (Wirkung auf die Dauer je Fenster, bindender Fall; Vorzeichen = Aenderung)

| Hebel | A3 (Roh-IC) | A1 | VRP | A2 | A4 |
|---|---|---|---|---|---|
| Laengere Zeit | wirkt (119 Wo.), 2031-05 | wirkt nur mit theta-Beleg | wirkt (672 Tage), 2030-04 | Historie ab 2020 vorhanden | Aufzeichnung laeuft, 2029-06 fruehestens |
| Mehr Symbole / Breite | max. -14 % (K -> unendlich) | Universum voll; ~0 | - | - | mehrere Basiswerte = ein Cluster |
| Zweite Boerse | <= -14 %, fuer gleiche Coins ~0 | ~0 (Preisbein gleich), UNBELEGT | - | Cross-Venue = anderer Mechanismus | - |
| Mehr Underlyings | - | - | BTC+ETH -4..-9 %, ETH-Prior UNBELEGT | BTC+ETH ein Cluster (rho 0,815) | - |
| Mehr Ereignisse | - | - | - | 52/Jahr woechentlich (Prior UNBELEGT) | kuerzere Zyklen ~0 [abg.] |
| HF-Statistik | keiner | keiner | -34 % (UNBELEGT), -57 % mit Konsens-c | macht sigma30 messbar | - |
| Weniger Autokorrelation | c ~1, nichts | c = 1 unter P-1 | Monatsziele +8 % (schlechter) | - | - |
| Hedge / Neutralisierung | fm8 -81 % (NEUE Hypothese, Prior UNBELEGT) | -7 % | - | Placebos sind die Neutralisierung | w_null UNGEMESSEN |
| Prior-Beleg | Band fehlt | theta: einziger echter Hebel | Niveau-Band 7,0..13,7 entscheidet Faktor 4 | V-5b | sigma_w und Prior |

---

## 3. Teil B - Datenbedarf (Auftragsliste fuer Data-Harvest, priorisiert)

Gemeinsame Regeln fuer jeden Auftrag: Data-Harvest speichert und prueft nur Vollstaendigkeit (Zeilen, Luecken,
Zeitstempel, Schema), rechnet keine Preis-, Rendite- oder Vol-Statistik; ab 2026-07-01 berechnet auch Scinance keine
BTC/ETH-Vol- oder Renditestreuung (DEC-96 E3, DEC-97). Luecken werden benannt, nie gefuellt; neue Stroeme erscheinen im
Katalog (`hd.catalog()`), kein Listing. Volumina sind Schaetzungen `[abg.]`.

| # | Strom / Quelle | Symbole | Aufloesung | Zeitraum | Kandidat / Frage | Power-Beitrag (Teil A) | Prio | Volumen |
|---|---|---|---|---|---|---|---|---|
| **B-1** | Variante B: `bybit/rest.kline1d/symbol=ALL` (GET /v5/market/kline, category linear, interval D), `bybit/rest.instruments/symbol=ALL` (instruments-info linear, Tagesschnappschuss: status, launchTime, deliveryTime, fundingInterval, Caps), Funding aller Perps als eigener Strom (GET /v5/market/funding/history, je Abrechnung) | alle linearen USDT-Perps (~820 aktiv; V-1b: 862 lineare Instrumente inkl. 40 datierter; PIT-Universum je Woche 514..603 in W2; Delistungen nach 2026-09-28 werden bis zum letzten Handelstag erfasst) | 1 Tag; Funding je Abrechnung (1h..8h); Instruments taeglich | Backfill 2026-09-29..heute lueckenlos (Anschluss an Zip 2026-09-28), dann taeglich laufend, selbstheilend (30 Tage Nachholen wie DVOL) | A3, A1 (blinde Fenster ab 2026-10-05); PIT-Universum und Survivorship (DEC-72: Stichdatum Register = Panel); Tagesschluss BTC/ETH fuer kuenftige VRP-Fenster | ohne B-1 kein blindes A3/A1-Fenster. A3 Roh-IC voll 2031-05-11 (bindend) / 2028-12-10 (measured); A3-fm8 (neue Hyp.) 2027-08-22; A1 bei theta 1 2030-01-06 | **1** (irreversibel: Tagesschnappschuss PIT-Roster, Kerzen kuenftig delisteter Symbole) | < 5 MB/Tag (Kerzen ~820 Zeilen, Funding einige Tausend Zeilen, ein Instruments-Schnappschuss) |
| **B-2** | A4-Quotes: (a) Inhaltsprobe des laufenden `bybit/tickers` fuer datierte Futures (LinearFutures USDC, InverseFutures): Snapshot- oder nur Delta-Frames? Felder Bid/Ask-Preis und -Groesse (beide Schreibweisen pruefen: mit "1", z. B. bid1Price, und ohne - Verfassung, Marktdaten: "Bybit-WS-Feldnamen ohne 1"; die WP-7-Probe fand bid1Price im Delta-Strom nicht), markPrice, indexPrice, deliveryTime, basis, openInterest. (b) falls nur Deltas: REST-Schnappschuss `/v5/market/tickers` category linear+inverse alle 15 min fuer alle datierten BTC/ETH-Kontrakte plus die zugehoerigen Perps (PRD 5.4). (c) `/v5/market/delivery-price` (Settlement-Historie, Backfill so weit verfuegbar), instruments-info linear+inverse taeglich (deliveryFeeRate -> V-4(b)) | alle datierten Kontrakte (40 USDT + 4 inverse laut V-2), mindestens BTC/ETH | 15 min (b); taeglich (c) | laufend seit 2026-06-16 (a); (b) ab sofort laufend; (c) Backfill + laufend | A4: sigma_w ab 2027-06-16 messbar; V-4(b) | UNBELEGT bis sigma_w gemessen; PRD-Design voll fruehestens 2029-06-29; N_C10 6,2 Zyklen/Fenster bei prior = sigma_w | **2** (irreversibel: verpasste Quotes sind nicht nachladbar) | ~10 MB/Monat (PRD 5.4) |
| **B-3** | 1-Minuten-Kerzen Bybit linear: GET /v5/market/kline interval 1, als `bybit/rest.kline1m/symbol=<S>/date=` | BTCUSDT, ETHUSDT | 1 min | Backfill 2021-03-01..heute (Probe zuerst: reicht die 1-min-Historie bis 2021? UNBELEGT), optional ab 2020-03-25 fuer A2; dann taeglich laufend | VRP: HF-RV-Nuisance auf der Vorperiode 2021-03-24..2024-05-31 (SD 18,6 -> ~15,1 messen); A2: sigma30, Placebo-SE, r_pre (07:30-08:00); Konvention 1-min-Close gegen Panel-Tagesschluss auf Tagen vor 2024-06 | VRP: 443 statt 672 Tage je Fenster (voll 2029-01-01 statt 2030-04-04), mit Konsens-c 292 (2028-03-07) - UNBELEGT bis Messung; A2: macht sigma30 messbar | **3** (reversibel, billig; schaltet eine UNBELEGT-Zahl frei) | ~1.440 Zeilen/Tag/Symbol; Backfill ~5,9 Mio Zeilen, ~0,1-0,3 GB, ~5.900 REST-Aufrufe; Ersatz fuer ~183 GB publicTrade |
| B-4 | Deribit-Verfallskalender und Settlement: `public/get_delivery_prices` (btc_usd, eth_usd), `public/get_instruments` (BTC/ETH, future+option, expired=true: expiration_timestamp, settlement_period), `public/get_last_settlements_by_currency` (Historie) | BTC, ETH | je Verfall / taeglich | Backfill ab 2019 (mindestens ab 2020-03-25), dann laufend | A2: Ereignismenge (seit wann woechentlich, V-5a), Settlement-Zeitlage als Datenteil von V-5c, Placebo-Kalender | A2 ist das einzige Design mit vielen unabhaengigen Einheiten in vorhandener Historie (52/Jahr); Power UNBELEGT (Prior V-5b, sigma30 aus B-3) | 4 | < 10 MB gesamt |
| B-5 | Options-Quotes: Inhaltsprobe `deribit/tickers` (14.810, seit 2026-06-16), `deribit/markprice.options`, Bybit-Optionen im `bybit/tickers`-Strom: Snapshot/Delta, best bid/ask, mark_iv, Greeks; tagesgenaue Ketten-Luecken-Karte (R3-K-37 Stufe 1) | BTC, ETH | wie aufgezeichnet | laeuft; nur Pruefung | A5 (E.6 (b)), H-26b | UNBELEGT (A5 gesperrt) | 5 | laeuft bereits |
| B-6 | **nicht beauftragen:** Binance-Perp-Panel als zweites Universum | - | - | - | A3, A1 | Teil A: A3-Gewinn <= -14 % und fuer gleiche Coins ~0; A1-Preisbein auf denselben Coins | - | - |
| B-7 | laeuft, keine Aenderung: `deribit/dvol` BTC/ETH (lueckenlos, selbstheilend), `bybit/publicTrade` BTC/ETH | - | - | laufend | jede kuenftige VRP-Hypothese auf den blinden Fenstern | Voraussetzung der Zeilen in 2.3 | - | - |

Ersatzweg zu B-3, nur falls 1-min-Kerzen fuer die RV nicht genuegen (z. B. Close-Konvention bei Gleichstaenden): ein
getrennter Archiv-Trade-Strom (bei Data-Harvest vorgemerkt, DEC-96 Nachtrag 2), ~28 GB je Symbol und Jahr.

---

## 4. Teil C - Entscheidungsvorlage fuer den Nutzer (PRD Par. 8), neutral

Zwei Strukturbefunde vorweg (gelten fuer jede Option):
- **Die blinden Fenster sind ein Einmal-Gut.** Die VRP-Fenster ab 2026-07-01 und die A3/A1-Fenster ab 2026-10-05
  sind blind, solange niemand dort ein Outcome rechnet. Die erste Hypothese, die auf ihnen laeuft (auch H-26, 2.6),
  verbraucht die Blindheit fuer alle anderen derselben Groesse. Die Wahl, WELCHES Design ein blindes Fenster bekommt,
  ist deshalb selbst eine Entscheidung mit Kosten.
- **Der Zeitfresser ist das Power-Ziel je Fenster, nicht die Zwei-Fenster-Regel.** Bei gleicher Gesamt-Fehlerrate
  (0,25 %) braucht ein einzelnes Fenster 7,7 % mehr Daten als zwei Fenster mit je Power 0,80 (Option 4, O5).

### Option 1 - Recording-first-Programm mit vorab fixierten Entsperrdaten

- **Inhalt:** Fuer jeden Kandidaten werden jetzt, vor jeder Zahl aus den blinden Fenstern, Fensterlaenge und
  Entsperrdatum aus Teil A fixiert (nur Nuisance, wie DEC-96 E2); bis dahin nur Zensus, Infrastruktur, Positivkontroll-
  Maschinerie und Siegel-Pflege. Entsperrdaten bei bindender Nuisance und zentralem Prior (P-1, C10):
  A3 Roh-IC mom1 2031-05-11 (rev_gap 2031-10-26); VRP-Design wie H-27 mit 672-Tage-Fenstern 2030-04-04; A1 nur mit
  theta-Beleg (dann 2030-01-06 bei theta 1 / W1-Spread); A4 sigma_w 2027-06-16, Urteil fruehestens 2029-06-29.
- **Richtung:** keine Regel bewegt. Fensterlaengen ueber 12 Monate sind fuer H-27 nach DEC-96 E2 ausgeschlossen - jede
  solche Fassung ist eine NEUE Hypothese mit Etikett "Fensterlaenge beschlossen nach Kenntnis von GL-032..034"; sie
  faellt aus Nuisance, nicht aus Outcome (Muster DEC-96).
- **Kosten:** 1,5..5 Jahre Wartezeit ohne Urteil; laufende Datenkosten gering (B-1, B-2, B-7); Risiko der Blindheits-
  Erosion ueber Jahre (Zwischenblicke, Nebenprodukte anderer Pakete, Vorwissen) - braucht eine dauerhafte Siegel-Regel
  wie DEC-96 E3 fuer jede Klasse; Regimewechsel waehrend der Fenster (z. B. Auto-Switch) bleiben moeglich.

### Option 2 - Ereignis-/Einheiten-Designs vorziehen

- **A2 nach V-5b/c:** Daten liegen historisch vor (Trades seit 2020, Kalender ueber B-4, Nuisance ueber B-3). Mit den
  Arbeitswerten braucht ein 12-Monats-Fenster mit Wochenverfaellen einen Prior >= 12,8 bp (P-1) bzw. 17,1 bp
  (A3-Praxis); Monatsverfaelle mit 16,5 bp [sek] brauchen 2,9 Jahre je Fenster. Gesperrt bleibt A2, bis V-5c die
  Richtung und V-5b eine Effektgroesse fuer die gewaehlte Menge belegt (DEC-58 E4) - das ist Literatur-/Primaer-
  quellenarbeit (teils nur per Nutzer-Upload, Egress gesperrt). Siegel-Kollision der PRD-Fenster (2.4) vorher klaeren.
- **A4 nach 12 Monaten:** sigma_w ab 2027-06-16, Urteilsfenster ab 2027-06-25; voll fruehestens 2029-06-29
  (4 Zyklen je Fenster), wenn prior >= 1,24 sigma_w.
- **Richtung:** Testbarkeit durch Design (mehr unabhaengige Einheiten), keine Regel bewegt; jede Fassung mit eigenem K.
- **Kosten:** Recherche V-5b/c, V-4; Data-Harvest B-2/B-3/B-4 (klein); A2 bindet einen Alpha-Slot mit dem
  PRD-5.2-Etikett (bester Fall zwischen Taker-Wand 11 bp und Gesamtwand ~15 bp; Handelsperspektive nur passiv).

### Option 3 - Hochfrequenz-Datenweg fuer die VRP

- **Inhalt:** B-3 beauftragen; auf der Vorperiode (<= 2024-05-31) Messrauschen und SD der HF-RV-Praemie messen (nur
  Streuung, Waechter wie `h27_common`); bestaetigt sich SD ~15,1, eine neue VRP-Hypothese (H-32 ff.) auf den blinden
  Fenstern ab 2026-07-01 mit vorab fixierter Laenge herleiten.
- **Zahlen:** C10 443 Tage je Fenster mit Regel-c (voll 2029-01-01), 292 Tage nur zusammen mit dem Konsens-c
  (2028-03-07) - der Konsens-c waere eine programmweite Aenderung der c-Regel P-3 (eigene DEC vorher, Richtung
  Testbarkeit). Prior-Band entscheidet weiter mit Faktor 4.
- **Status:** UNBELEGT bis zur Messung; belegbar wenige Wochen nach B-3 (Backfill ~20 min REST am Thin Client plus
  eine Nuisance-Rechnung).
- **Richtung:** Testbarkeit (Schaetzerwahl nach Kenntnis von GL-034); zulaessig nur als neue Hypothese mit eigenem K
  und Etikett "beschlossen nach Kenntnis der H-27-Feasibility (GL-034)" (REVIEW_H27 B-1, DEC-93 E3).
- **Kosten:** klein (Daten ~0,1-0,3 GB, eine Herleitung + Review); verbraucht die blinden VRP-Fenster (Einmal-Gut).

### Option 4 - Programmweite Regelaenderung (nur ausgewiesen, NICHT empfohlen)

Jede Zeile waere eine Regelaenderung nach Kenntnis von GL-032, GL-033 und GL-034 und muesste das DEC-94-Etikett
tragen: "**Lockerung** (bzw. Verschaerfung), beschlossen nach Kenntnis von GL-032..034 und des Power-Zensus P-2;
Fehlerrate x -> y; kippt kein Verdikt" - prospektiv, programmweit, nie kandidatenspezifisch, vor dem ersten
Kandidaten, der sie nutzt. Fehlerraten fuer zwei Fenster unter der Null, gleiche SE `[pb:regel_optionen]`:

| Option | Daten gesamt (relativ) | Fehlerrate gemeinsam | Power gemeinsam am Prior | Richtung | A3 Roh-IC (W1-stress) | A3-fm8 | A1 (theta 1, W1) | VRP Referenz |
|---|---:|---:|---:|---|---|---|---|---|
| O0 geltend (P-1) | 1,00 | 0,25 % | 0,64 | - | 2 x 119 Wo. -> 2031-05-11 | 2 x 23 -> 2027-08-22 | 2 x 85 -> 2030-01-06 | 2 x 672 T. -> 2030-04-04 |
| O1 Power-Ziel 0,50 je Fenster | 0,44 | 0,25 % | 0,25 | Testbarkeit | 2 x 52 -> 2028-10-15 | 2 x 10 -> 2027-02-21 | 2 x 37 -> 2028-03-19 | 2 x 294 -> 2028-03-11 |
| O1 Power-Ziel 0,60 | 0,58 | 0,25 % | 0,36 | Testbarkeit | 2 x 70 -> 2029-06-10 | 2 x 13 -> 2027-04-18 | 2 x 49 -> 2028-09-03 | 2 x 392 -> 2028-09-21 |
| O1 Power-Ziel 0,70 | 0,76 | 0,25 % | 0,49 | Testbarkeit | 2 x 91 -> 2030-03-31 | 2 x 17 -> 2027-06-13 | 2 x 65 -> 2029-04-01 | 2 x 511 -> 2029-05-19 |
| O2 alpha 0,10 je Fenster | 0,73 | 1,0 % (x4) | 0,64 | Testbarkeit | 2 x 87 -> 2030-02-17 | 2 x 17 -> 2027-05-30 | 2 x 62 -> 2029-02-18 | 2 x 490 -> 2029-04-05 |
| O3 ein Fenster, alpha 0,05 | 0,50 | 5,0 % (x20) | 0,80 | Testbarkeit | 1 x 119 -> 2029-01-21 | 1 x 23 -> 2027-03-14 | 1 x 85 -> 2028-05-21 | 1 x 672 -> 2028-06-01 |
| O4 ein Fenster, alpha 0,01 | 0,81 | 1,0 % (x4) | 0,80 | Testbarkeit | 1 x 194 -> 2030-06-23 | 1 x 37 -> 2027-06-27 | 1 x 138 -> 2029-05-27 | 1 x 1091 -> 2029-07-25 |
| O5 ein Fenster, alpha 0,0025 | 1,08 | 0,25 % | 0,80 | neutral | 1 x 257 -> 2031-09-07 | 1 x 49 -> 2027-09-19 | 1 x 183 -> 2030-04-07 | 1 x 1447 -> 2030-07-16 |
| O6 gemeinsame Power 0,80 | 1,36 | 0,25 % | 0,80 | Strenge | 2 x 162 -> 2032-12-19 | 2 x 31 -> 2027-12-12 | 2 x 115 -> 2031-03-02 | 2 x 911 -> 2031-07-26 |
| O7 A3-Praxis (Schwelle 2,4865 SE) | 1,79 | 0,0042 % | 0,64 | Strenge | 2 x 214 -> 2034-12-17 | 2 x 41 -> 2028-04-30 | 2 x 152 -> 2032-08-01 | 2 x 1204 -> 2033-03-03 |

Lesart:
- O1 laesst die Fehlerrate je Test unveraendert, macht aber ein DROP uninformativ: bei Power 0,5 je Fenster verwirft
  C.10 drei von vier echten Effekten (K-0.6); die Feasibility-Regel DEC-51 (2) waere ausgehoehlt. Erwartete Zahl
  falscher PASS im Programm steigt nur ueber die groessere Zahl zugelassener Tests.
- O2/O3/O4 erhoehen die Fehlerrate je Test (x4 bis x20); O3 gibt zusaetzlich den Zweck von C.10 (Regime-Robustheit,
  PRD 3.5 (a)) auf.
- O5 zeigt: die Zwei-Fenster-Struktur kostet bei gleicher Rate nichts; O6/O7 sind Verschaerfungen (Gegenrichtung,
  ebenfalls Torpfosten-Bewegungen, wenn jetzt beschlossen).
- Eine Wahl zwischen diesen Zeilen nach Kenntnis der Kandidaten-Zahlen ist die Gabelung, die DEC-93 E3 und DEC-97
  ausschliessen; sie ist hier nur ausgewiesen, damit der Preis jeder Lesart sichtbar ist.

### Option 5 - Pause oder Abschluss von 3.0 mit dieser Bilanz

- **Inhalt:** 3.0 schliesst mit dem Befund "auf diesem Bestand unter DEC-51/DEC-94 fuer Literatur-Effektgroessen vor
  2028..2031 nicht testbar; kein Verdikt". Irreversible Datenstroeme (B-1, B-2, B-7) laufen kostenarm weiter, damit
  ein spaeterer Wiedereinstieg ueber Option 1 moeglich bleibt; Siegel bleiben geschlossen.
- **Richtung:** neutral. **Kosten:** kein Ergebnis; die Sunset-Review der Recording-Engine (PRD 8.3) wird faellig;
  offene Belege (theta, V-5b/c, V-4, VRP-Volltext) bleiben offen.

Die Optionen 1-3 sind kombinierbar (z. B. B-1/B-2 sofort, Option 3 als Messung, Option 2 als Recherche); Option 4 ist
mit jeder kombinierbar, aber nur programmweit und vorher.

**Was NICHT folgt:** kein Verdikt ueber Momentum, Reversal, Vol-Anomalie, Funding-Carry oder VRP; keine Aussage, dass
die Effekte fehlen; keine Empfehlung einer Regelaenderung; keine Registrierung. Die Daten in Teil A sind bedingte
Rechnungen: aendert sich die Nuisance im blinden Fenster (z. B. Marktfaktor-Vol fuer A3, Spread-Regime fuer A1), aendert
sich die Dauer - die Zuordnung wird vor jeder Registrierung neu festgestellt, nie danach.

---

## 5. UNBELEGT und offene Punkte

| Punkt | Status | blockiert / wirkt auf |
|---|---|---|
| A3-Prior 0,03 | [sek] (R2 0.3C, Primaerliteratur nicht eingesehen); kein Band | alle A3-Daten (W ~ prior^-2) |
| Prior des beta-neutralisierten IC (fm8) | UNBELEGT | Option fm8 |
| SD des kuenftigen A3-Fensters | angenommen W1-stress (bindend) | Datum A3 (2027-10..2031-05 je Lesart) |
| theta (A1) | UNBELEGT (DEC-93 E2) | A1 vollstaendig |
| Spread-Regime des kuenftigen A1-Fensters | unbekannt bis zum Fenster; vorab zu fixieren | A1-Dauer Faktor ~4 |
| VRP: IV-Niveau der Literaturstichprobe (Prior-Band 7,0..13,7), L-1-Volltext, ETH-Prior | UNBELEGT / nicht eingesehen | VRP-Dauer Faktor ~4 |
| HF-RV-SD 15,1 und ihr c | UNBELEGT (Delta-Methode, Review B-1) | Option 3 |
| 1-min-Historie Bybit bis 2021 | UNBELEGT, Probe in B-3 | B-3 |
| A2: sigma30 (gepoolt, Verfalls-Slot), Effektgroesse woechentlich (V-5b), Zeitlage (V-5c), Kalender-Historie (V-5a seit wann) | UNGEMESSEN / UNBELEGT | A2 |
| A4: sigma_w, Prior des Wedge, w_null (Margin-Regeln), V-4 Liefergebuehr, Inhalt des tickers-Stroms (Snapshot/Delta) | UNGEMESSEN / UNBELEGT | A4 |
| A5: V-4, Spread-Zensus, H-26-Verdikt | offen (E.6) | A5 |
| H-26: done_days-Zaehlung, Lesart nachgeladener Tage, Lueckenlosigkeit `deribit/publicTrade`, Kollision mit Blind-Siegel | UNBELEGT / zu entscheiden | H-26, alle VRP-Hypothesen |
| Verfuegbarkeitsdatum Variante B | unbekannt | Start A3/A1 (je Woche Verschiebung) |
| Additive Zerlegung SD^2 = Boden^2 + F^2 (A3-Breite) | Naeherung `[abg.]` | nur Abschnitt 2.1 Breite |

---

## 6. Reproduktion und Dateien

- `scratchpad/bilanz/bilanz_census.py` - liest nur `runs/wp13a_20261012_v5e/wp13a_prelaunch.json`,
  `herleitung_a1/feasibility.json`, `herleitung_h27/feasibility.json`, `runs/wp7_20260921/wp7_report.json`
  (Waechter verweigert Siegelnamen und WP-10(A)-Verzeichnisse; sha256 der Eingaben im JSON-Feld `quellen_sha256`),
  rechnet mit `power_p1`, schreibt `state/programm_bilanz.json` (< 1 s, deterministisch, kein Zufall; zwei Laeufe
  ergaben dieselbe sha256 `c4b29702...48cb4f`; `tests/unit/test_power_p1.py` 32 passed).
- `scratchpad/bilanz/make_tables.py` - rendert die Tabellen dieser Akte aus dem JSON.
- Aufruf: `PYTHONPATH=/home/user/scinance/src python3 -I bilanz_census.py && python3 -I make_tables.py`.
