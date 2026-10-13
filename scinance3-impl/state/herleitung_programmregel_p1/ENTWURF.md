# Programmregel P-1 - Herleitung (ENTWURF): Schwelle, Power und Standardfehler aus einem Guss

> ENTWURF, Stand 2026-10-13. Nichts hier ist beschlossen oder registriert; entscheiden darf nur der Orchestrator.
> Nichts committet, nichts gepusht.
>
> **Ergebnisblindheit und Siegel.** Kandidaten-agnostisch: keine Daten zu H-27/DVOL/Optionen angesehen oder gerechnet,
> keine Zahl eines kuenftigen Kandidaten. Fuer PRD 5.2/5.4/5.5 (A2, A4, A5) werden nur Fundstelle und Formeltyp
> zitiert, keine Kandidatenzahl. Keine Datei `*_L_window_sealed.json`, `weekly_ic_series.csv`,
> `ic_series_*_UNION_REAL.csv` geoeffnet oder gegrept (Durchsuchungen nur mit expliziten Pfaden); das Fenster `L` des
> v5e-JSON wurde nicht gelesen. Keine Panel-, keine Outcome-Daten, keine neue Simulation: alle Zahlen sind Arithmetik
> auf zwei vorhandenen Akten.
>
> **Kuerzel.**
> - `[rj:<pfad>]` = `state/herleitung_programmregel_p1/rechnung_p1.json` (sha256 `eca434a1...cc1cc`), erzeugt von
>   `rechnung_p1.py` (sha256 `264010f5...766c`), deterministisch (zwei Laeufe, gleiche sha256), nur stdlib.
> - `[v5e:<pfad>]` = `state/runs/wp13a_20261012_v5e/wp13a_prelaunch.json` (sha256 `94d65559...b3b2`, gleich Audit PC v3).
> - `[fj:<pfad>]` = `state/herleitung_a1/feasibility.json` (sha256 `b4680f7c...ca72d9e`, gleich DEC-93).
> - `[abg.]` = hier aus offenen Zahlen abgeleitet, Rechenweg daneben.
> - Fundstellen als `Datei:Zeile`; `dec` = `state/decisions.md`, `PRD` = `PRD_SCINANCE3.md`, `Verf` =
>   `scinance3-impl/CLAUDE.md`, `Reg` = `state/hypothesis_registry.md`, `YAML` = `state/registered/h28_h30_v3.yaml`,
>   Code-Pfade relativ zu `src/bybit_edge/research/`.
>
> Reproduktion (aus der Repo-Wurzel, Sekunden):
> `python3 -I scinance3-impl/state/herleitung_programmregel_p1/rechnung_p1.py`

---

## 0. Befund in Kuerze

1. **Das Programm hat zwei unvereinbare Semantiken fuer "z".** Die Verfassung (DEC-51 (1)) und die PRD-Power-Formeln
   rechnen mit dem kritischen Wert 1,6449 (alpha 0,05); die PRD-Schwellenzeilen (5.1/5.2/5.3/5.4, YAML-Template) setzen
   die Schwelle auf den MDE-Faktor 2,4865 = 1,6449 + 0,8416 ("z des Regimes"). A3 hat die Schwelle 2,4865 * SE
   registriert (effektives alpha 0,0064 je Fenster) und GL-032 mit `Phi(prior/SE - 2,4865)` entschieden; A1 (GL-033)
   wurde nach der PRD-5.1-Formel mit 1,6449 und der gepoolten MDE-Pruefung 3,1680 * SE entschieden. Zwoelf
   Befunde I-1..I-12 (Abschnitt 2.6), tragend I-1 (Schwelle/Power), I-3 (SE), I-4 (Autokorrelation), I-5 (Luecke).
2. **Optionen** (Abschnitt 3): Schwelle (a) kritischer Wert, (b) MDE-Faktor mit passender Power, (c) Zuordnung nach
   gemeinsamer Gate-Power, (d) Default (a) mit explizit registrierbarem strengerem alpha. Autokorrelation: Statistik
   statt Schluessel, Untergrenze c >= 1 oder nicht, Nuisance aus Vorperiode, Simulation oder dem Maximum. Luecke
   0,60 <= P < 0,80: jede monotone Regel aendert DEC-51 (2) oder DEC-52 (i); die geltende Mischregel (DEC-87 (F)) ist
   nicht monoton (am A1-Gitter gezeigt: GL-012 -> DEC-52 -> GL-012 -> C.10 bei steigendem Prior).
3. **Retro-Check** (Abschnitt 4, nur v5e und `feasibility.json`): **Keine Option kippt GL-032 unter der bindenden
   stress-Kalibrierung, keine kippt GL-033** (theta UNBELEGT blockiert unabhaengig). Offen ausgewiesen: unter der NICHT
   bindenden measured-Kalibrierung waeren A3-mom1/mom2/mom4/rev_gap mit Option (a) lauffaehig gewesen (C.10 nach
   PRD-Wortlaut L1, DEC-52 nach L3/L3v/G); die Autokorrelationsregel "Statistik, c >= 1" haette den ERSTEN Grund von
   GL-033 (DEC-67 E4) aufgehoben, ausser mit (a)+L2, (b)+L3v, (b)+G oder L5.
4. **Falsch-Positiv-Raten** (Abschnitt 5): C.10 gemeinsam (a) 0,25 %, (b) 0,0042 % (Faktor 60). DEC-52 gemeinsam
   **0,85 %** unter (a), nicht 0,5 % wie PRD 3.5 annimmt (Screens und gepoolte Signifikanz sind stark abhaengig;
   Nebenbefund I-10). Zulassungsgrenze (zwei gleiche Fenster): A3-Praxis 3,33 SE, Empfehlung 2,49 SE, PRD-5.1-Wortlaut
   2,24 SE.
5. **Empfehlung** (Abschnitt 6): Paket P-1a = Schwelle (a)/(d) + eine SE fuer Test und Power + Autokorrelation der
   Teststatistik mit c >= 1 + Nuisance = Maximum aus Vorperiode und Simulation + Luecken-Regel L3v (DEC-52 fuer
   P < 0,80, nur wenn das volle DEC-52-Gate Power >= 0,80 hat). Pflicht-Etikett "beschlossen nach Kenntnis von A3/A1",
   Lockerung gegenueber der A3-Praxis offen benannt. Gleichwertig dokumentierte Alternative P-1b (Schwelle (b)):
   kippt gar nichts, verlangt aber eine Aenderung von DEC-51 (1) und ~79 % mehr Daten je MDE.

---

## 1. Begriffe, Konstanten, Notation

| Groesse | Wert | Herleitung |
|---|---|---|
| z_krit(0,05 einseitig) | 1,6449 | `Phi^-1(0,95)` [rj:constants.z05] |
| z_krit(0,01 einseitig) | 2,3263 | `Phi^-1(0,99)` [rj:constants.z01] |
| z_beta(Power 0,80) | 0,8416 | `Phi^-1(0,80)` [rj:constants.zb80] |
| MDE-Faktor je Fenster bei alpha 0,05 | 2,4865 | 1,6449 + 0,8416 (PRD:109, Verf:55) |
| MDE-Faktor gepoolt bei alpha 0,01 | 3,1680 | 2,3263 + 0,8416 (PRD:109) |
| Fenster-Fehlerrate, wenn 2,4865 Schwelle ist | 0,00645 | `1 - Phi(2,4865)` [rj:FPR.b.alpha_window]; DEC-74 (d) nennt 0,0064 |
| MDE80, wenn 2,4865 Schwelle ist | 3,3281 * SE | 2,4865 + 0,8416 [rj:constants.mde_factor_b_window] |
| gepoolte Rate, wenn 3,1680 Schwelle ist | 0,00077 | `1 - Phi(3,168)` [rj:FPR.b.pooled_alpha]; MDE80 dann 4,0096 * SE_p |
| MDE-Verhaeltnis (b)/(a) | 1,3385 | 3,3281/2,4865; Datenbedarf 1,3385^2 = 1,79 [rj:constants.n_ratio_b_over_a] |

- **Kritischer Wert** z_krit: die Signifikanzbedingung `Statistik >= z_krit * SE` hat unter der Null die Rate alpha.
- **MDE80** = (z_krit + 0,8416) * SE: der kleinste wahre Effekt, den diese Bedingung mit Power 0,80 sieht.
- **Power** einer Bedingung `x >= T`: `Phi((prior - T)/SD(x))`; bei `T = z_krit * SE` also `Phi(prior/SE - z_krit)`.
  **Konsistenzregel:** Schwelle T und Power-Formel muessen dasselbe T benutzen, SE der Power = SE des Tests.
- **Autokorrelation:** im Programm stehen zwei Notationen nebeneinander. `c` (A1, DEC-67 E4) ist ein
  **Varianz**-Faktor `1 + 2*sum_k (1-k/W)*rho_k`, SE = sigma * sqrt(c/W); DEC-67 E4: W_eff = 0,41 W <=> c = 1/0,41 =
  2,439. `c_rho` (A3, DEC-74 (b), `wp13_xsec/nulls.py:361-374`) ist ein **SD**-Faktor `sqrt(1 + 2*sum ...)`.
  Dieses Dokument benutzt `c` (Varianzfaktor); ein SD-Faktor heisst `sqrt(c)`.

---

## 2. Inventur (Auftrag 1)

Spalte "Typ": S = Schwelle, K = kritischer Wert/Niveau, P = Power/MDE-Formel, SE = SE-Regel, AK = Autokorrelation,
Z = Zuordnungsregel. Spalte "Befund": ok = in sich konsistent; I-n = Inkonsistenz nach 2.6.

### 2.1 Verfassung (`scinance3-impl/CLAUDE.md`)

| Fundstelle | Festlegung | Typ | Befund |
|---|---|---|---|
| Verf:45 | "Ein-Fenster-DROP bei Power 0,5 verwirft 3 von 4 echten Effekten -> DEC-52" | Z | ok (Begruendung DEC-52) |
| Verf:52-53 | C.10 hartes Ein-Fenster-DROP "ausser DEC-52 greift"; C.12 Feasibility vor dem Lauf | Z | ok |
| Verf:55-57 | DEC-51: alpha 0,05 einseitig, Power 0,80, Cluster-Einheit, Selektions-K, Ueberlappung | K, P | Massstab; I-1, I-5 |
| Verf:57-58 | DEC-52: nur bei Per-Fenster-Power < 0,6, gepooltes alpha 0,01 | Z, K | I-5 |
| Verf:69-71 | Sequenz-Zwang: Regelaenderungen VOR dem ersten Kandidaten, der sie braucht | - | Rahmen fuer Abschnitt 5 |
| Verf:113-114 | Fehlendes heisst UNBELEGT und blockiert | - | Rahmen (theta in GL-033) |

Kompendium (normativ ueber Verf:48): `survey/ERKENNTNIS_KOMPENDIUM.md:283-287` C.10 (Schwelle in EINEM von >= 2
Fenstern verfehlt -> DROP), :293-298 C.12 - ohne Zahlwert fuer alpha oder z; kein eigener Befund.

### 2.2 PRD (`PRD_SCINANCE3.md`)

| Fundstelle | Festlegung | Typ | Befund |
|---|---|---|---|
| PRD:100 | 3.3.1 Power-Zeile: "Welchen Effekt sieht das registrierte Fenster mit Power 0,80?" | P | ok |
| PRD:103-107 | DEC-51 (1)-(5) wortgleich | K, P, SE | Massstab |
| PRD:109 | "Zahlenwerte: einseitig z = 1,6449 + 0,8416 = 2,4865; zweiseitig 2,8016; alpha 0,01 3,1680" - die Zahlen sind MDE-Faktoren, heissen aber "z" | P | I-8 (Benennung), Quelle von I-1 |
| PRD:113 | `N_eff = N_c/(1+(N_c-1)*rho)` mit gemessenem rho (Querschnitt) | SE | ok; I-11 (Verhaeltnis zur Zeitreihen-SE ungeregelt) |
| PRD:115 | Selektionsdecke Bailey/LdP; Schwelle ueber der Decke | S | ok; Wechselwirkung I-12 |
| PRD:181 | YAML-Template `z: <2.4865 / 2.8016 / 3.1680>` - nur MDE-Faktoren, kein Feld fuer z_krit/alpha | S, K | I-1 |
| PRD:184-187 | `a_priori_effekt`, `detectable_effect`, `per_fenster_power` ("entscheidet ueber DEC-52 (i)"), `zuordnungsregel` | P, Z | ok (Felder), Formel offen |
| PRD:211 | C.10: "effektives alpha 0,05^2 = 0,25 %" - setzt alpha 0,05 je Fenster voraus | K | konsistent nur mit (a); I-1 |
| PRD:216-221 | DEC-52 (i) P < 0,60; (ii) Screen 0,5x Schwelle, Band [0,5x; 2,0x]; (iii) fenster-geclusterter stationaerer Bootstrap; (iv) gepoolt alpha 0,01 | Z, K, SE | I-5; I-6 ((iii) mit zwei Fenstern nicht ausfuehrbar) |
| PRD:225 | FPR nach DEC-52 "~0,5 x 0,01 = 0,5 %" | - | **I-10** (exakt 0,85 %) |
| PRD:233 | Lo 2002: `T_min = 2,4865^2 * (...)` | P | konsistent nur mit (a) (Stichprobengroesse fuer Power 0,80 bei alpha 0,05) |
| PRD:263 | Welle 1 zweiseitig, z = 2,8016; Kandidaten-Power-Zeilen "uebernehmen deren einseitige Konvention" | K | 2,8016 ist MDE-Faktor, kein kritischer Wert; I-8 |
| PRD:297-307 | WP-7-Feasibility: `detektierbar = 2,4865*SD_null/sqrt(52)`, gepoolt `3,1680*SD_null/sqrt(104)`; Schranken 0,08699 / 0,09657 | P | konsistent mit (a) (MDE80 eines alpha-0,05- bzw. 0,01-Tests) |
| PRD:318 | Breiten-Floors K >= 134 / 109 / 117 | P | aus PRD:297-307; ok unter (a) |
| PRD:333-334 | B1/B2 an denselben Schranken | P | ok unter (a) |
| PRD:335 | B3: Survivorship-Verzerrung < halbe registrierte Schwelle | S | haengt an der Schwelle (I-1) |
| PRD:487 | A1-Power-Zeile: N_eff "korrigiert um die Autokorrelation ueber den stationaeren Bootstrap (Politis/Romano; Blocklaenge Politis/White)" | SE, AK | Massstab fuer I-4, I-6 |
| PRD:490-492 | detektierbarer Mittelwert 0,344886 * sigma_LS (C.10) / 0,310648 * sigma_LS (DEC-52) = MDE-Faktoren / sqrt(W) | P | ok unter (a) |
| PRD:500 | `P_fenster = Phi(prem_prior/(sigma_LS/sqrt(52)) - 1,6449)` | P | Power eines Tests mit Schwelle 1,6449*SE; **I-1** gegen PRD:512 |
| PRD:501-502 | P >= 0,60 -> C.10 hart; < 0,60 -> DEC-52 | Z | **I-5** gegen DEC-51 (2) |
| PRD:503 | GL-012, wenn `3,1680 * sigma_LS/sqrt(104) > prem_prior` | P, Z | = MDE80 des gepoolten alpha-0,01-Tests, ok unter (a) |
| PRD:512 | Schwelle `mean_min = max(obere CI-Grenze Nulleffekt; z * sigma_LS/sqrt(W))` "mit dem z des registrierten Fenster-Regimes" (2,4865 / 3,1680) | S | **I-1** |
| PRD:523 | Kill (4): Schluessel-Autokorrelation < 0,30 (Design-Parameter) | AK | kein SE-Bezug; bleibt |
| PRD:564 | A2: Per-Fenster-Power `Phi(Effekt/SE - 1,6449)` | P | **I-1** gegen PRD:574 |
| PRD:566-567 | A2 gepoolt: "detektierbar 3,1680*SE", Power `Phi(Effekt/SE - 2,3263)` | P | in sich ok unter (a) |
| PRD:574 | A2-Schwelle `max(oberes 95-%-Quantil Placebo; 2,4865 * SE(Delta))` | S | **I-1** (Kandidatenzahlen bewusst nicht uebernommen) |
| PRD:623 | A3: `SE = SD_null/sqrt(52)` (Boden) | SE | **I-3** gegen DEC-75 (1) |
| PRD:626-627 | A3: `P_fenster = Phi(0,03/(SD_null/sqrt(52)) - 1,6449)` | P | **I-1** gegen PRD:634, **I-3** |
| PRD:630 | A3-Zuordnung: Power < 0,60 -> DEC-52 zulaessig, sonst C.10 | Z | I-5 |
| PRD:634 | A3-Schwelle `IC_min = 2,4865 * SD_null/sqrt(52)` | S | **I-1** |
| PRD:638 | A3-Gate (1): "die registrierte Schwelle ... (C.10 hart)" | S | erbt I-1 |
| PRD:671 | A4: `detektierbar = 2,4865 * sigma_w/sqrt(8)`; Zuordnungsregel "identisch zu A1" (also 1,6449) | P, Z | **I-1** gegen PRD:678 |
| PRD:678, 695 | A4-Schwelle `w >= 2,4865 * sigma_w / sqrt(N_cluster)` plus "signifikant gegen w_null" | S | **I-1** (Kandidatenzahlen nicht uebernommen) |
| PRD:720, 730 | A5-Schwelle "aus gemessener Skew-Verteilung" | S | kein z; ausserhalb (nur Fundstelle) |
| PRD:922 | Konstanten-Tabelle "DEC-51-Konstanten ... 2,4865 / 2,8016 / 3,1680" | P | I-8 |
| PRD:924-927, 930-931, 935 | WP-7-Schranken, A1-Etikett, A2-Varianten, A4-Schwelle | S, P | erben I-1 (A2/A4: nur Fundstelle) |
| PRD:932 | "A3-Per-Fenster-Power 0,75 (K=117) bis 0,98 (K=300) ... C.10 hart" | P | **I-1, I-3** |
| PRD:939 | FPR nach DEC-52 "0,5 %" | - | **I-10** |
| PRD:969 | B-4: gepoolter Zweig durchgaengig mit z = 3,1680 | P | ok als MDE-Faktor (PRD:503); als Schwelle I-1 |
| PRD:1011, 1046 | Bel-5 Funding-Autokorrelation 0,30 Design-Parameter; 11.4 Buehlmann-Straub-Ersatz `k <= 2,333*w` | AK | Kill-Parameter, keine SE-Regel; ausserhalb P-1 |

### 2.3 Entscheidungen (`state/decisions.md`, DEC-51..DEC-93)

| Fundstelle | Festlegung | Typ | Befund |
|---|---|---|---|
| dec:13 | DEC-51 (1) Mess-Gates alpha 0,05 einseitig | K | Massstab |
| dec:14 | DEC-51 (2) Power 0,80; Prior < MDE80 -> GL-012 "oder braucht ein anderes Design" | P, Z | I-5 |
| dec:15 | DEC-51 (3) N_eff = N/(1+(N-1)*rho), gemessenes rho, nie 0 | SE | I-11 |
| dec:16-17 | DEC-51 (4) Selektions-K, (5) Ueberlappung -> Blocklaenge | S, SE | ok; I-12 |
| dec:27-31 | DEC-52 (i)-(v) | Z, K, SE | I-5, I-6 |
| dec:32 | DEC-52 Sequenz-Zwang | - | Rahmen |
| dec:35-48 | DEC-52-Nachtrag: Retro-Check, Etikett "Verbesserung" | - | Muster fuer Abschnitt 4 |
| dec:55 | DEC-53 Bootstrap-Replikate >= 1.000 bzw. Seed | SE | ok |
| dec:162 | DEC-65 (2): "Kill-/Power-Rechnung von A1 verwendet den Stress-N_eff" | SE | **I-11** (nie operationalisiert) |
| dec:178 | DEC-67 E1: A3 "Per-Fenster-Power > 0,9 auch unter W_eff = 21" (Rechnung `WELLE1_BEFUND_TEIL4:41`: 1,6449, Boden-SE) | P | **I-1, I-3** |
| dec:181 | DEC-67 E4: Funding-Wochen-Autokorrelation 0,42/0,24/0,18/0,15 -> "DEC-51-Power fuer Funding-basierte Hypothesen rechnet mit W_eff = 0,41 W" (Herleitung `WELLE1_BEFUND_TEIL4:31`: AR(1) (1-0,42)/(1+0,42)) | AK | **I-4** |
| dec:205-206 | DEC-70: A1-Schluessel-Null W_eff-adjustiert 0,068 < 0,087; E1 "W_eff = 0,41 W bleiben" | AK, P | I-4 (fuer den IC des Schluessels selbst passt E4 eher) |
| dec:236 | DEC-73 E1: A3 Power > 0,95 unter W_eff 0,41 W -> C.10 hart; "Schwelle IC_min = 0,0142 je Fenster aus dem gemessenen Rauschboden" (= 2,4865 * 0,0411/sqrt(52) [abg.]) | S, P | **I-1, I-3** |
| dec:249 | DEC-74 (a) `IC_min(W) = 2,4865 * E_t[1/sqrt(K_t-1)] * c_rho / sqrt(W)` | S | erbt I-1 |
| dec:250 | DEC-74 (b) `c_rho = sqrt(1 + 2*sum_{k=1..4}(1-k/W)*rho_k)` aus der Persistenz-Null | AK | I-7 (SD-Faktor, eigene Quelle) |
| dec:251 | DEC-74 (c) Persistenz-Null, 95-%-Quantil | K | report-only (DEC-75 (6)) |
| dec:252 | DEC-74 (d) "Kritwert-Faktor 2,4865 je Fenster (Groesse 0,0064; gemeinsam 4,1e-5), MDE bei Power 0,80 = IC_min" | K, P | **I-2** (innerer Widerspruch) |
| dec:275 | DEC-75 (1) `SE = max(E_t[...], SD(IC_t))/sqrt(W)`; PASS `abs(IC) >= 2,4865*SE` UND CI-Grenze (Niveau 1-0,0064, MBB Block 4) jenseits 0 UND `abs(IC) >= IC_min` | S, K, SE, AK | in sich konsistent (alpha 0,0064); gegen DEC-51 (1) I-1; I-6 |
| dec:277 | DEC-75 (3) Beta-Kontrolle `abs(IC_res) >= IC_min` | S | erbt I-1 |
| dec:282 | DEC-75 (8) Deckelung `max(1, c_rho)`; DEC-52 fuer rev_gap zulaessig bei Power < 0,60 (Prior 0,01) | AK, Z | Praezedenz c >= 1 |
| dec:290 | DEC-76 E1 (a) SE-Regel; (b) 99,36-%-Quantil der driftenden Null | SE, K | (b)-Semantik (alpha 0,0064) |
| dec:302, 312 | DEC-77 E1 (b)/DEC-78 E1: Methodenkriterien `0,25*Boden/sqrt(W)`, `1,5*Rausch-Decke` | - | Methodenkriterium, keine Test-Schwelle; Massstab Boden-SE (Hinweis, kein P-1-Befund) |
| dec:341 | DEC-81 Gegenprobe `z <= 3`, `3*se_diff <= 0,25*Ziel` | - | Kalibrierungs-QS, kein Gate |
| dec:407 | DEC-87 (A) bindende Decke unter stress | S | ok |
| dec:408 | DEC-87 (B) "DEC-52 fuer rev_gap zulaessig (Power bei Prior 0,01: 0,15 / 0,19)" | P | **I-3** (Boden-SE, [abg.: Phi(0,01*2,4865/0,01727 - 2,4865) = 0,148]) |
| dec:409 | DEC-87 (C) analytische Decke 1,3868 * SE_W | S | ok (report-only) |
| dec:411 | DEC-87 (E) bindendes Beta-Kontroll-Quantil | K | (b)-Semantik |
| dec:412 | DEC-87 (F) "volle Power >= 0,80 in beiden Fenstern -> C.10 hart; MDE80 > IC_prior in einem Fenster -> GL-012 ... DEC-52-Zweig ist nicht gebaut" | Z | **I-5** (nicht monoton, Abschnitt 3.4) |
| dec:430 | DEC-88 Formeln `P_ICmin = Phi(0,03*2,4865/IC_min - 2,4865)`, `MDE80 = max(1,3385*IC_min, ...)` | P | Schwelle/Power konsistent (b), aber **I-3** (Boden-SE) |
| dec:465, 468 | DEC-91 + Nachtrag: Ursache Boden-SE; auch die IC_min-Bedingung | P, SE | Korrektur fuer A3 |
| dec:474-478 | DEC-92 E1/E2 und Lehre "Power-/MDE-Zeilen ... mit genau der SE-Regel des registrierten Tests" | P, SE | Massstab, aber nur Lehre, keine Regel |
| dec:486-488 | DEC-93 E1 (DEC-67 E4 bindend: `3,168*SE_gep. = 176,5 > 147,6`), E2 (theta UNBELEGT), E3 (keine A1-spezifische Abweichung) | AK, P, Z | Befund nach PRD:500-503 (a-Semantik) mit E4 |
| dec:490 | DEC-93 Merkposten (a) Schluessel- statt Statistik-Persistenz, (b) PRD-5.1-Schwelle MDE-Faktor, (c) WP-7-Null-Auffuellung, (d) Sonderpaare I = 0 | AK, S | Anlass dieses Auftrags |

### 2.4 Registrierte YAML und Registry-Text

| Fundstelle | Festlegung | Typ | Befund |
|---|---|---|---|
| YAML:61-68, 110-117 | `ic_min_capped` je Variante (Faktor 2,4865) | S | erbt I-1 |
| YAML:88-103, 137-152 | `res_quantile_driftfree/drifting` auf Niveau 0,9936 | K | (b)-Semantik |
| YAML:162-163 | `rules.block_len: 4`, `rules.level: 0.9936` | K, AK | (b)-Semantik; MBB (I-6) |
| YAML:17, 23 | Sperrgruende mom2/mom4 mit DEC-88-Zahlen (Boden-SE) | P | I-3; YAML bleibt bitgleich (Akte) |
| Reg:400-404 | Formelblock "Mechanische Zuordnung" (`P_ICmin` mit Boden-SE) | P | I-3; ueberholt (Reg:1136 ff.) |
| Reg:407-408 | Zuordnungsregel DEC-87 (F) | Z | I-5 |
| Reg:505 | `IC_min = 2,4865 x B_W x max(1, c_rho_bk) / sqrt(W)` | S | I-1 |
| Reg:676, 682-684 | (1b) `abs(IC_W) >= 2,4865 x SE_W`; CI-Niveau 0,9936 | S, K | (b)-Semantik |
| Reg:974 | Pflichtzeile 1: "alpha 0,05 einseitig, Power 0,80, z 2,4865" | K | **I-9** (registrierter Test hat alpha 0,0064) |
| Reg:976 | effektives N = W/c_rho_bk^2 | AK | I-7 (Notation) |
| Reg:1146-1151 | Vermerk H-31 nicht registriert | - | - |

### 2.5 Code

| Fundstelle | Festlegung | Typ | Befund |
|---|---|---|---|
| `wp13_xsec/gates.py:15-22` | Docstring: PASS `abs(mean_ic) >= 2.4865 * SE` UND CI (level 1 - 0.0064) UND `>= IC_min_capped`; DEC-52 nicht verdrahtet | S, K | (b)-Semantik, gleich DEC-75 (1) |
| `wp13_xsec/gates.py:82` | `Z_PER_WINDOW = 2.4865` als kritischer Wert | K | gegen DEC-51 (1): I-1 |
| `wp13_xsec/gates.py:100-102, 105, 115, 123` | magnitude/ci/ic_min/beta-Bedingungen, `window_pass` | S | ok gegen DEC-75 |
| `wp13_xsec/nulls.py:202-203` | Kommentar "DEC-51/DEC-74 (d): per-window critical value (alpha 0.05 one-sided)" zu `Z_PER_WINDOW = 2.4865` | K | **I-8** (falsch: kritischer Wert zu alpha 0,0064 bzw. MDE-Faktor zu 0,05) |
| `wp13_xsec/nulls.py:361-374` | `c_rho_from_lag_autocorr`: SD-Faktor, Lags 1..4 | AK | I-7 |
| `wp13_xsec/nulls.py:377-385` | Bias-Korrektur +1/W je Lag | AK | ok (DEC-75 (8)) |
| `wp13_xsec/nulls.py:464-480` | `ic_threshold(z = 2.4865, cap max(1, c_rho))` | S, AK | erbt I-1; Praezedenz c >= 1 |
| `wp13_xsec/nulls.py:494-496` | `BLOCK_SIZE_WEEKS = 4`; `SELECTION_CEILING_ONE_SIDED_QUANTILE = 1 - 0.0064` | K, AK | (b)-Semantik; I-6 |
| `wp13_xsec/run.py:289-298` | `se_of_mean_ic`: `max(floor, SD(IC_t))/sqrt(W_judged)` - ohne Autokorrelation in der SE | SE | **I-6** (Autokorrelation nur ueber MBB-CI und c_rho) |
| `wp13_xsec/run.py:301-339` | `moving_block_bootstrap_ci`, Default `level = 1 - 0.0064`, Block 4 | K, AK | (b)-Semantik; MBB statt stationaer (I-6) |
| `wp13_xsec/run.py:549, 674, 1081` | `ci_level = 1.0 - 0.0064` Defaults | K | wie oben |
| `wp13_xsec/run.py:955-982` | `resolve_rules`: `block_len`/`level` aus YAML, gegen Code-Konstanten gepinnt (T5) | K | ok; Anpassungsstelle |
| `wp13_xsec/prelaunch.py:367-382` | analytische Selektionsdecke (Faktor 1/sqrt(2) historisch, DEC-87 (C)) | S | report-only |
| `wp13_xsec/prelaunch.py:436-454` | Methodenkriterien `0.25*floor/sqrt(W)`, `1.5*Decke` | - | kein P-1-Befund |
| `wp13_xsec/*` | **keine Funktion fuer Power, MDE oder Zuordnung** - DEC-88/91/92 wurden von Hand bzw. in Skripten gerechnet | P | **Luecke** (Ursache des DEC-91-Fehlers liegt ausserhalb jeder Testabdeckung) |
| `wp7_universe/stats.py:27-33` | `Z_PER_WINDOW = 2.4865`, `Z_POOLED = 3.1680`, Kommentar "alpha 0.05 / 0.01" | P | Arithmetik ok (MDE), Benennung I-8 |
| `wp7_universe/stats.py:221-235` | `detectable_effect`, `sd_null_threshold`, `feasible` (MDE80) | P | ok unter (a); Boden-SE (fuer WP-7-Feasibility so gewollt) |
| `wp7_universe/stats.py:238-253` | `W_EFF_FACTOR = 0.41`; `sd_null_w_eff_adjusted` "reported ALONGSIDE ... never replacing" | AK | **I-4** (Docstring deskriptiv, DEC-67 E4 bindend) |
| `wp7_universe/panel_load.py:507` | `funding_autocorrelation`: `np.nansum` fuellt Wochen ohne Funding mit 0 | AK | Quelle der 0,42 (DEC-93 Merkposten (c)); ausserhalb des Auftragsumfangs, der Vollstaendigkeit halber |

Tests/Skripte, die die Konstanten pinnen (fuer die Anpassungsliste): `tests/unit/test_wp13_run.py:904, 1322, 2029,
2339, 2390, 2454` (`level 0.9936`), `tests/unit/test_wp13_xsec.py:337, 563, 565` (`nulls.Z_PER_WINDOW`),
`tests/unit/test_wp7_universe.py:430, 1009, 1200` (`2.4865`, `Z_PER_WINDOW/Z_POOLED` im Bericht, `W_EFF_FACTOR ==
0.41`), `scripts/wp13_xsec.py:61, 609` (`level: 0.9936`), `scripts/wp7_universe_census.py:350` (`w_eff_factor`).

### 2.6 Die Inkonsistenzen

- **I-1 Schwelle und Power-Formel passen nicht zusammen (Kern).** PRD:512, :574, :634, :678 und das YAML-Template
  PRD:181 setzen die Schwelle auf den MDE-Faktor ("z des Regimes" = 2,4865 bzw. 3,1680); PRD:500, :564, :626, :671
  (via A1) rechnen die Power mit dem kritischen Wert 1,6449. Ist die Schwelle 2,4865 * SE, ist die Power
  `Phi(prior/SE - 2,4865)`, nicht `Phi(prior/SE - 1,6449)`; die PRD-Formel ueberschaetzt sie. Beispiel A1 (c = 1,
  theta = 1): PRD-Formel W1 0,619, Power des Gates mit Schwelle 2,4865 * SE 0,295 [fj:configs.A_dec70_1h_eingeschlossen.
  power.grid."c1_binding|theta=1.0".W1]. Folgefehler: DEC-67 E1 (dec:178), DEC-73 E1 (dec:236), PRD:932.
- **I-2 DEC-74 (d) ist in sich widerspruechlich** (dec:252): "Kritwert-Faktor 2,4865 (Groesse 0,0064)" UND "MDE bei
  Power 0,80 = IC_min". Mit kritischem Wert 2,4865 * SE ist MDE80 = 3,3281 * SE = 1,3385 * IC_min (so korrekt in
  DEC-88, dec:430). Die zweite Haelfte ist nur unter (a) wahr. Die A3-Registrierung hat die erste Haelfte umgesetzt
  (gates.py:100, run.py:303), die zweite als Absicht behalten.
- **I-3 SE der Power != SE des Tests.** PRD:623 (`SD_null/sqrt(52)`), dec:178, dec:236, dec:408, dec:430, Reg:400-404,
  YAML:17/23 rechnen mit der Boden-SE; der registrierte Test nutzt `max(Boden, SD(IC_t))/sqrt(W)` (dec:275,
  run.py:289-298). Folge DEC-91: W1 Power 0,47 (measured) / 0,21 (stress) statt 0,90. Korrigiert nur fuer A3
  (DEC-91/92), als Programmregel nur "Lehre" (dec:478).
- **I-4 Autokorrelation aus dem Schluessel, nicht aus der Teststatistik.** DEC-67 E4 (dec:181) leitet W_eff = 0,41 W
  aus der lag-1-Autokorrelation der Wochen-Funding-SUMME je Symbol ab (`WELLE1_BEFUND_TEIL4:31`), DEC-70 E1 (dec:206)
  bestaetigt sie fuer A1; PRD:487 und DEC-52 (iii) (dec:29) verlangen den stationaeren Bootstrap der urteilstragenden
  Wochenserie. Fuer A1 ist die Teststatistik negativ autokorreliert (rho_1 -0,25, c 0,60..0,77) gegen c = 2,439 aus E4
  [fj:configs.A_dec70_1h_eingeschlossen.power.inputs.c_options; FEASIBILITY.md:204-208]. Der Code fuehrt E4 nur als
  deskriptive Zeile (stats.py:248-252), die Quelle 0,42 ist durch Null-Auffuellung nach oben verzerrt (panel_load.py:507;
  REVIEW_A1.md:51-53: Union 0,478 woertlich gegen 0,412 ohne Auffuellung).
- **I-5 Luecke 0,60 <= P < 0,80.** DEC-51 (2) (dec:14): unter MDE80 -> GL-012 "oder anderes Design"; DEC-52 (i)
  (dec:27, PRD:216): DEC-52 nur bei P < 0,60; PRD:501-503 (A1) und PRD:630 (A3): P >= 0,60 -> C.10, GL-012 nur gepoolt;
  DEC-87 (F) (dec:412): MDE80 > Prior -> GL-012. Die Texte widersprechen sich in genau diesem Band, und die
  DEC-87-(F)-Mischung ist nicht monoton (Abschnitt 3.4).
- **I-6 Bootstrap-Variante und Ort der Autokorrelation uneinheitlich.** Stationaer mit Politis/White-Blocklaenge
  (PRD:487), stationaer "fenster-geclustert" (DEC-52 (iii), mit zwei Fenstern nicht als Cluster-Resampling
  ausfuehrbar, `herleitung_a1/ENTSCHEIDUNGSVORLAGEN.md:218-220`), MBB Block 4 (DEC-75 (1), run.py:301-339; A1 EV-10).
  Im A3-Gate steckt die Autokorrelation nur in der CI-Bedingung und in IC_min (c_rho), nicht in der SE der
  Groessenbedingung (run.py:289-298).
- **I-7 Notation c gegen c_rho.** Varianzfaktor (DEC-67 E4, A1) gegen SD-Faktor (DEC-74 (b), nulls.py:361-374);
  Bias-Korrektur +1/W nur bei A3. Kein Rechenfehler gefunden, aber eine Regel braucht eine Notation.
- **I-8 Benennung.** "z" fuer MDE-Faktoren (PRD:109, :263, :922; stats.py:27-33); falscher Kommentar
  nulls.py:202-203 ("critical value (alpha 0.05 one-sided)" fuer 2,4865).
- **I-9 Etikett der A3-Pflichtzeile** Reg:974 "alpha 0,05" gegen registriertes Niveau 0,9936 (YAML:163).
- **I-10 FPR-Arithmetik DEC-52** (PRD:225, :939): "P(Vorzeichenfilter) x alpha_gepoolt ~ 0,5 x 0,01 = 0,5 %" setzt
  Unabhaengigkeit von Filter und gepoolter Signifikanz voraus. Unter der Null sind sie stark positiv abhaengig: exakt
  **0,851 %** mit 0,5x-Screens, 0,830 % mit Band-Obergrenze, 0,990 % nur Vorzeichen [rj:FPR.a.DEC52_joint_*;
  numerische Integration, Monte-Carlo-Gegenprobe 2e7 Ziehungen Seed 53: 0,852 % / 0,991 %]. Der Faktor gegen C.10
  (0,25 %) ist 3,4, nicht 2. Kein 2.0-Verdikt kippt dadurch (der DEC-52-Retro-Check hat kein Verdikt gekippt).
- **I-11 Stress-N_eff fuer A1** (dec:162) ist eine Querschnittsgroesse ohne definierten Ort in einer Zeitreihen-SE;
  die A1-Herleitung hat sie nicht benutzt (`ERSTFASSUNG_H31_entwurf.md:89, :175`). Niedrig.
- **I-12 Selektionsdecke gegen kritischen Wert.** DEC-51 (4) verlangt Schwelle > Decke. Die Bailey/LdP-Decke
  E[max von K] uebersteigt 1,6449 ab K = 12 (z_max(12) = 1,665) und 2,4865 erst ab K = 89 (2,489)
  [rj:FPR.selection_ceiling_K_star]. Unter (a) bindet die Decke also frueher; eine Regel muss das ausdruecklich sagen.

---

## 3. Optionen (Auftrag 2)

### 3.1 Schwellenregel

**(a) Schwelle = kritischer Wert zum registrierten alpha; Power und MDE mit derselben SE.**
C.10 je Fenster `x_W >= 1,6449 * SE_W` (alpha 0,05, DEC-51 (1)), Bootstrap-Grenzen und Null-Quantile auf Niveau 0,95;
DEC-52 gepoolt `>= 2,3263 * SE_p` (DEC-52 (iv)). Power `Phi(prior/SE - 1,6449)`, MDE80 = 2,4865 * SE.
- Vorteile: Wortlaut der Verfassung und DEC-51 (1); PRD-Power-Formeln (PRD:500, :564, :626), WP-7-Feasibility
  (PRD:297-307), Lo-Formel (PRD:233), C.10-Rate 0,25 % (PRD:211) und gepoolte GL-012-Pruefung (PRD:503) werden ohne
  Aenderung konsistent; erfuellt die zweite Haelfte von DEC-74 (d) ("MDE80 = IC_min"); 25 % kleinere MDE als (b).
- Nachteile: gegenueber der A3-Registrierungspraxis und den PRD-Schwellenzeilen Lockerung der Fenster-Fehlerrate
  0,0064 -> 0,05 (C.10 gemeinsam Faktor 60); nach zwei GL-012 als Erleichterung fuer kuenftige Kandidaten lesbar;
  Selektionsdecke bindet ab K = 12 (I-12).

**(b) Schwelle = MDE-Faktor (A3-Praxis); Power zwingend `Phi(prior/SE - Schwellenfaktor)`.**
C.10 je Fenster `>= 2,4865 * SE_W` (alpha 0,00645), DEC-52 gepoolt `>= 3,1680 * SE_p` (alpha 0,00077); MDE80 =
3,3281 * SE bzw. 4,0096 * SE_p.
- Vorteile: entspricht der registrierten A3-Praxis (gates.py, YAML) und dem Entscheidungsweg von GL-032; kein Befund
  kippt (Abschnitt 4); keine Lesart als Lockerung.
- Nachteile: widerspricht DEC-51 (1)/Verfassung (alpha 0,05) und DEC-52 (iv) (alpha 0,01) - beide muessten geaendert
  werden (in strenger Richtung; nach "kein Torpfosten-Verschieben in KEINE Richtung" ebenfalls eine Bewegung); PRD:211,
  :225, :233, :297-307, :503 muessten neu gerechnet werden (z. B. WP-7-Schranke je Fenster 0,03*sqrt(52)/3,3281 =
  0,0650 statt 0,08699 [abg.]; der B2-Befund 0,041..0,049 haelt auch dann); ~79 % mehr Daten je MDE.

**(c) Zuordnung nach der Power des ganzen registrierten Gates (Schwelle wie (a)).**
C.10 nur, wenn das Produkt der Fenster-Powers >= 0,80 (je Fenster ~0,894, MDE ~2,894 * SE [abg.: Phi^-1(sqrt(0,8)) =
1,249; 1,6449 + 1,249]); sonst DEC-52, wenn dessen volles Gate Power >= 0,80; sonst GL-012.
- Vorteile: misst die Wahrscheinlichkeit, einen wahren Effekt zu bestaetigen, und nicht nur ein Fenster; kein
  0,60-Schnitt; monoton.
- Nachteile: aendert DEC-51 (2) (je Fenster) UND DEC-52 (i); verschiebt Kandidaten mit Fenster-Power 0,80..0,894 von
  C.10 (Rate 0,25 %) in DEC-52 (0,85 %) - die strengere Power-Forderung erhoeht so paradoxerweise die Fehlerrate
  dieser Kandidaten (generisch: DEC-52-Bereich 2,487..2,895 SE [rj:generic_admission."a|G"]).

**(d) Default (a), strengeres alpha nur explizit registrierbar.**
Wie (a); eine Registrierung darf ein kleineres alpha waehlen, muss es dann als Zahl (`alpha`, `z_krit`) fuehren und
Power/MDE damit rechnen. A3 (DEC-74 (d), alpha 0,0064) waere eine solche Wahl gewesen.
- Vorteile: haelt die A3-Registrierung als zulaessige strengere Wahl gueltig ("die strengere Fehlerrate zu waehlen
  ist immer erlaubt", Audit PC v3 Abschnitt 3 Bewertung 1); verhindert stille Faktoren.
- Nachteile: eine zusaetzliche Wahl je Registrierung (Freiheitsgrad); nur zulaessig, wenn die Wahl vor jeder
  Feasibility-Zahl festgelegt wird.

### 3.2 SE-Regel (in jeder Option Pflicht)

Die Power-Zeile rechnet mit der Entscheidungsregel UND der SE-Regel des registrierten Gates; je Bedingung eine
Power, bindend das Minimum (Praxis DEC-88), berichtet das Produkt. Ist die SE datenabhaengig, wird die SD der
getesteten Statistik unter der kalibrierten Null bzw. aus der Vorperiode eingesetzt (DEC-92). Ohne diese Zeile sind
(a)-(d) wertlos: I-3 entsteht in jeder Schwellen-Semantik.

### 3.3 Autokorrelationsregel und Herkunft der Nuisance

| Option | Inhalt | Vorteile | Nachteile |
|---|---|---|---|
| A-E4 | Status quo: Funding-basierte Hypothesen W_eff = 0,41 W | einfach, beschlossen | falsches Objekt (I-4); Quelle verzerrt (panel_load.py:507); fuer negativ autokorrelierte Statistiken zu streng, fuer staerker autokorrelierte zu mild |
| A-Stat | c = gemessenes Varianzverhaeltnis der Teststatistik (stationaerer Bootstrap), ohne Untergrenze | richtiges Objekt, PRD:487 | Gutschrift fuer negative Autokorrelation (A1: c 0,756) ist schaetzunsicher (rho_1 -0,25 nur ~2,7 SE von 0, `herleitung_a1/ENTSCHEIDUNGSVORLAGEN.md:85`) |
| A-Stat>=1 | wie A-Stat, aber c = max(1, c_hat) | richtiges Objekt; nie Gutschrift; Praezedenz DEC-75 (8) `max(1, c_rho)`; Test bleibt bei c < 1 konservativ | bei c < 1 Power verschenkt; Wechsel von E4 beguenstigt A1-artige Statistiken (Etikett) |
| A-Sim | c aus der Null-Simulation (A3: c_rho aus der Persistenz-Null) | ohne Outcome-Kontakt | Modellrisiko (Audit PC v3 1.4 (5): die Ein-Faktor-Null ist eher Untergrenze) |

Fehlerrate je Fenster, wenn die Lauf-SE mit c_used gebaut ist und die wahre Autokorrelation c_true betraegt
(Schwelle 1,6449) [rj:FPR.autocorr_alpha_window_a]:

| c_true | naiv c = 1 | max(1, c_true) | c_true exakt | E4 c = 2,439 |
|---:|---:|---:|---:|---:|
| 0,60 | 1,69 % | 1,69 % | 5,00 % | 0,05 % |
| 0,756 | 2,93 % | 2,93 % | 5,00 % | 0,16 % |
| 1,00 | 5,00 % | 5,00 % | 5,00 % | 0,51 % |
| 1,50 | 8,96 % | 5,00 % | 5,00 % | 1,80 % |
| 2,439 | 14,61 % | 5,00 % | 5,00 % | 5,00 % |

Lesart: `max(1, c)` haelt die Fehlerrate nie ueber nominal und gibt nichts fuer negative Autokorrelation; eine feste
Konstante (E4) ist nur bei genau ihrem c_true nominal.

**Herkunft der Nuisance (SD und c der Teststatistik fuer die Power-Zeile).**
- N-Vor (A1-Praxis): Vorperiode vor dem ersten Urteilsfenster, nur Streuung/Autokorrelation, Mittel nie ausgegeben
  (Waechter `assert_nuisance_holding_week`). + echte Abhaengigkeitsstruktur; - Regimewechsel (A1: W2 im
  Auto-Switch-Regime), duenne fruehe Universen, Naehe zum Outcome; **fuer Klasse W ist die Vorperioden-Statistik das
  versiegelte L-Fenster - nicht verfuegbar**.
- N-Sim (A3-Praxis v5e): kalibrierte Null-Simulation. + kein Outcome-Kontakt, stress-Variante; - Modellrisiko
  (DEC-85 D1; Audit PC v3 1.4 (5)).
- N-Max: bindend die groessere SE ueber verfuegbare Quellen und registrierte Kalibrierungen (stress, DEC-77 E1 (b)),
  geprueft durch die Positivkontrolle (SD der Kontrollwelt hoechstens +10 % ueber der Power-Zeile, A1 EV-12 Regel 1).

### 3.4 Luecken-Regel 0,60 <= P < 0,80

| Regel | Inhalt | monoton? | aendert |
|---|---|---|---|
| L1 (PRD:501-503, :630 woertlich) | P >= 0,60 -> C.10; sonst DEC-52; GL-012 nur ueber die gepoolte MDE80 | ja | DEC-51 (2) (C.10-Laeufe mit Fenster-Power 0,60..0,80, gemeinsam bis 0,36) |
| L2 (DEC-87 (F) verallgemeinert) | P >= 0,80 -> C.10; 0,60..0,80 -> GL-012; < 0,60 -> DEC-52, wenn gebaut und gepoolt feasible | **nein** | nichts (geltende Mischlage) |
| L3 | P >= 0,80 -> C.10; sonst DEC-52, wenn gepoolte MDE80 <= Prior; sonst GL-012 | ja | DEC-52 (i) 0,60 -> 0,80 |
| L3v | wie L3, aber DEC-52 nur, wenn das VOLLE DEC-52-Gate (gepoolt x Screens) Power >= 0,80 hat | ja | DEC-52 (i) 0,60 -> 0,80 |
| L5 | P >= 0,80 -> C.10; sonst GL-012 (kein DEC-52) | ja | DEC-52 faktisch ausser Kraft (gegen Verf:45, :57) |
| G = Option (c) | gemeinsame Gate-Power | ja | DEC-51 (2) und DEC-52 (i) |

**Nicht-Monotonie von L2, am A1-Gitter** (Konfiguration A, c = 1, Option (a); theta skaliert den Prior linear)
[rj:A1."c1_binding|a".regime_segments_theta.L2]: theta < 0,766 GL-012; 0,766..0,974 DEC-52; **0,975..1,276 GL-012**;
ab 1,277 C.10. Ein groesserer Prior macht A1 untestbar - die Regel bestraft Evidenz. Dasselbe Muster in jeder
c-/Schwellen-Kombination [rj:A1.*.regime_segments_theta.L2]. EV-3 (`ENTSCHEIDUNGSVORLAGEN.md:98-99`) hatte das
qualitativ benannt.

**Trilemma.** Eine monotone Regel, die DEC-52 bei P < 0,60 behaelt, muss das Band 0,60..0,80 testbar machen: als
C.10 (L1, verletzt DEC-51 (2), DROP dort uninformativ, C.13) oder als DEC-52 (L3/L3v, Rate dort 0,85 % statt 0,25 %).
Die dritte monotone Moeglichkeit setzt DEC-52 ausser Kraft (L5). Jede Loesung aendert also einen Verfassungssatz.

---

## 4. Retro-Check (Auftrag 3, DEC-52-Stil)

**Status: Sensitivitaets-Check, keine Neubewertung.** GL-032 und GL-033 bleiben unveraendert stehen, gleich wie die
Regel ausfaellt (Nicht-Rueckwirkung). Keine Datei der Akte wurde veraendert.

**Basis.** A3: v5e, SE nach DEC-75 (1) mit `methods.none.variants.<v>.factor_sd` als SD(IC_t) (Audit PC v3 1.4),
W_judged 52/51, IC_min = `ic_min_capped` (unter (a) mit 1,6449/2,4865 skaliert), Beta-Kontrolle aus
`beta_control_recommended_high_rep.{stress, stress_drifting}` (bindend das extremere, DEC-87 (E); unter (a) das
0,95-Quantil in Normalnaeherung `mean + 1,6449 * sd` [abg.]), Prior 0,03, DEC-52 hypothetisch auf dem Mittel der 103
Wochen (Audit PC v3 2.), Screens 0,5 x gepoolte Schwelle, Beta-Kontrolle im DEC-52-Zweig nie definiert (nicht
enthalten). A1: `feasibility.json` Konfiguration A, SE je c-Option, theta = 1 (Obergrenze; theta UNBELEGT).
Reproduziert die Akte: A3 (b)/stress mom1 W1 P 0,205 / MDE80 0,0601, W2 0,554 / 0,0381 (DEC-91: 0,21/0,060, 0,55/0,038);
IC_min-Bedingung W1 0,796/0,716 (Audit 0,79/0,71); DEC-52 (a) gepoolt stress MDE80 0,0340 (Audit 0,034); A1 (a)/E4
gepoolt 176,5 > 147,6 (DEC-93) [rj:A3, rj:A1].

### 4.1 A3 (GL-032), Prior 0,03

P_voll = min(Groesse, IC_min, Beta); MDE80 je Fenster; gepoolt = DEC-52-Zweig [rj:A3."<v>|<cal>|<opt>"].

| Variante, Kal., Option | W1 P / MDE80 | W2 P / MDE80 | DEC-52: MDE80_p / Gate-Power | L1 | L2 | L3 | L3v | L5 | G |
|---|---|---|---|---|---|---|---|---|---|
| mom1 stress (b) = registriert | 0,205 / 0,0601 | 0,554 / 0,0381 | 0,0430 / 0,24 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 |
| mom1 stress (a) | 0,507 / 0,0449 | 0,836 / 0,0284 | 0,0340 / 0,53 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 |
| mom1 measured (b) | 0,466 / 0,0416 | 0,848 / 0,0284 | 0,0305 / 0,71 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 |
| mom1 measured (a) | 0,775 / 0,0311 | 0,969 / 0,0212 | 0,0241 / 0,90 | **C.10** | GL-012 | **DEC-52** | **DEC-52** | GL-012 | **DEC-52** |
| rev_gap stress (b) = registriert | 0,211 / 0,0593 | 0,554 / 0,0381 | 0,0427 / 0,25 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 |
| rev_gap stress (a) | 0,515 / 0,0443 | 0,836 / 0,0284 | 0,0337 / 0,54 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 |
| rev_gap measured (b) | 0,479 / 0,0410 | 0,845 / 0,0285 | 0,0302 / 0,72 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 |
| rev_gap measured (a) | 0,785 / 0,0307 | 0,968 / 0,0213 | 0,0239 / 0,90 | **C.10** | GL-012 | **DEC-52** | **DEC-52** | GL-012 | **DEC-52** |

mom2 und mom4 zeigen dasselbe Muster (measured (a): W1 0,774 / 0,760, W2 0,966 / 0,965, gepoolt 0,0242 / 0,0245;
stress und (b) ueberall GL-012) [rj:A3."mom2|*", "mom4|*"]. H-30 (vol_rv, vol_max: Feasibility 2,764 > 0,5;
vol_beta strukturell) haengt an keiner Schwellen- oder Power-Option. Selektionsdecke unter (a): kleinstes IC_min'
0,01108 (W1) / 0,00966 (W2) gegen bindende Decke 0,00834 / 0,00685 -> kein neuer Kill [rj:A3_ic_min_a; YAML:87, :136].
Autokorrelationsoptionen beruehren A3 nicht (IC_t unter der Null praktisch unabhaengig, Audit PC v3 1.4 (3); c_rho
ist gedeckelt, DEC-75 (8)).

**Ergebnis A3.** Unter der bindenden stress-Kalibrierung (DEC-92 E1, Audit Auflage 3) bleibt GL-032 in **jeder**
Option und Regel. Offen auszuweisen: unter der nicht bindenden measured-Kalibrierung waeren mom1, mom2, mom4 und
rev_gap mit Option (a) lauffaehig gewesen - nach dem PRD-Wortlaut (L1) als C.10 hart mit gemeinsamer Power 0,75
(mom1), nach L3/L3v/G im DEC-52-Zweig (Gate-Power 0,90). Unter (b) bleibt auch measured ueberall GL-012 (knapp: DEC-52
gepoolt MDE80 0,0305 / 0,0302 gegen 0,03).

### 4.2 A1 (GL-033), theta = 1 (Obergrenze), Konfiguration A

[rj:A1."<c>|<opt>"]; theta_min = kleinstes theta ohne GL-012 (Gitter 0,001).

| c, Option | W1 / W2 P | MDE80_p / prem_p | DEC-52-Gate | L1 | L2 | L3 | L3v | L5 | G | theta_min L1 / L3v |
|---|---|---|---|---|---|---|---|---|---|---|
| E4 2,439 (a) = geltend | 0,345 / 0,813 | 176,5 / 147,6 | 0,40 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 | 1,196 / 1,475 |
| E4 2,439 (b) | 0,108 / 0,519 | 223,4 / 147,6 | 0,16 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 | GL-012 | 1,514 / 1,750 |
| Stat>=1, c = 1 (a) | 0,619 / 0,990 | 113,0 / 147,6 | 0,84 | **C.10** | GL-012 | **DEC-52** | **DEC-52** | GL-012 | **DEC-52** | 0,766 / 0,945 |
| Stat>=1, c = 1 (b) | 0,295 / 0,929 | 143,0 / 147,6 | 0,67 | **DEC-52** | **DEC-52** | **DEC-52** | GL-012 | GL-012 | GL-012 | 0,970 / 1,121 |
| Stat, c = 0,756 (a) | 0,724 / 0,998 | 98,3 / 147,6 | 0,92 | **C.10** | GL-012 | **DEC-52** | **DEC-52** | GL-012 | **DEC-52** | 0,666 / 0,822 |
| Stat, c = 0,756 (b) | 0,402 / 0,981 | 124,4 / 147,6 | 0,83 | **DEC-52** | **DEC-52** | **DEC-52** | **DEC-52** | GL-012 | **DEC-52** | 0,843 / 0,975 |

**Ergebnis A1.** GL-033 kippt unter **keiner** Option: Grund E2 (theta UNBELEGT, dec:487) blockiert unabhaengig von
jeder Regel. Offen auszuweisen: Grund E1 (DEC-67 E4) haengt allein an der Autokorrelationsregel. Unter A-E4 bleibt E1 in
jeder Schwellen- und Luecken-Option (theta_min >= 1,196). Unter A-Stat>=1 entfaellt E1 bei theta = 1 in (a) mit L1, L3,
L3v, G und in (b) mit L1, L2, L3; er bleibt in (a)+L2, (b)+L3v, (b)+G und L5. Der Auftrag der Herleitung A1 hatte diese
Regelwahl als "nach Kenntnis, zugunsten des Kandidaten" erkannt (DEC-93 E3; REVIEW_A1.md:54-62) - sie gehoert deshalb
in eine programmweite Regel mit Etikett, nie in eine A1-Entscheidung.

### 4.3 Zusammenfassung Retro-Check

| Option | kippt GL-032 (bindend)? | kippt GL-033? | kippt einen Teilgrund / nicht bindende Lesart? |
|---|---|---|---|
| Schwelle (a) | nein | nein | A3 measured: ja mit L1, L3, L3v, G |
| Schwelle (b) | nein | nein | nein |
| (c) Gate-Power | nein | nein | A3 measured: ja; A1 E1 bei c = 1 ja |
| (d) | wie (a) | wie (a) | wie (a) |
| A-Stat>=1 | nein (A3 unberuehrt) | nein (E2) | A1 E1: ja, ausser (a)+L2, (b)+L3v, (b)+G, L5 |
| A-Stat (ohne Untergrenze) | nein | nein | A1 E1: ja, ausser L2 (a) und L5 |
| L1 / L3 / L3v | nein | nein | A3 measured mit (a); A1 E1 mit c = 1 (unter (b) nur L1/L3, nicht L3v) |
| L2 / L5 | nein | nein | nein (L2 nur wegen Nicht-Monotonie) |

**Nicht-Rueckwirkung (bindend in jeder Option):** GL-032, GL-033, DEC-88..DEC-93, die YAML `bd948f34...c299` und der
Vermerk H-31 bleiben; kein Rueckzug, keine Viertfassung, keine A1-Registrierung auf Grund von P-1. Ein anderes
A3-/A1-Design bleibt eine NEUE Hypothese mit eigenem K (DEC-58 E2, DEC-92) und muss die in GL-032/033 offengelegten
Zahlen als gesehen fuehren (C.17).

---

## 5. Torpfosten-Pruefung (Auftrag 4)

### 5.1 Falsch-Positiv-Raten (Null in beiden Fenstern, gleiche Fenster-SE, Vorzeichen registriert)

[rj:FPR]

| Paket | alpha je Fenster | C.10 gemeinsam | DEC-52 gemeinsam (Screens 0,5x) | dto. mit Band 2,0x | dto. nur Vorzeichen |
|---|---:|---:|---:|---:|---:|
| (a)/(d) | 5,0 % | **0,25 %** | **0,851 %** | 0,830 % | 0,990 % |
| (b) | 0,645 % | **0,0042 %** | **0,0713 %** | 0,0712 % | 0,0767 % |
| (c) | wie (a) je Regime | 0,25 % | 0,851 % | | |
| PRD 3.5 (Annahme) | 5,0 % | 0,25 % | 0,5 % | | |

- Verhaeltnis C.10 (a)/(b) = 60,1 [rj:FPR.ratio_C10_a_over_b].
- Die von PRD 3.5 "bewusst in Kauf genommene" DEC-52-Rate 0,5 % wuerde ein gepoolter kritischer Wert 2,5287
  (alpha 0,0057) einhalten [rj:FPR.DEC52_crit_p_for_joint_0p5pct] - Nebenoption fuer eine DEC-52-Korrektur, nicht Teil
  der Empfehlung.
- Autokorrelationsoptionen aendern die Fehlerrate eines zugelassenen Tests nur ueber die Lauf-SE (Tabelle 3.3); die
  Power-Zeile aendert, WELCHE Kandidaten zugelassen werden, also die Zahl der Tests und damit die erwartete Zahl
  falscher PASS im Programm, nicht deren Einzelrate.

### 5.2 Zulassungsgrenze in SE-Einheiten (kandidaten-agnostisch: zwei gleiche Fenster, SE_W = 1, Prior d in beiden)

[rj:generic_admission]

| Paket | ab d (SE) zugelassen | Regime ab dort | Fenster-Power an der Grenze |
|---|---:|---|---:|
| A3-Praxis (b) + L2 ohne DEC-52 | 3,329 | C.10 | 0,80 |
| (b) + L3v | 2,982 | DEC-52 (C.10 ab 3,329) | 0,69 |
| **(a) + L3v (Empfehlung)** | **2,487** | C.10 (DEC-52 nur bei ungleichen Fenstern) | 0,80 |
| (a) + G | 2,487 | DEC-52 bis 2,895, dann C.10 | 0,80 |
| (a) + L1 = PRD-5.1-Wortlaut | 2,241 | C.10 | 0,72 |
| (a) + L3 | 2,241 | DEC-52 bis 2,486, dann C.10 | 0,72 |

Lesart: Bei zwei gleich starken Fenstern ist L3v unter (a) praktisch identisch mit "Fenster-Power >= 0,80"; der
DEC-52-Zweig wirkt nur bei ungleichen Fenstern (A1, A3: W2 deutlich staerker) - genau der Fall, fuer den DEC-52 gebaut
wurde. Die DEC-52-Gate-Power ist als Produkt gerechnet; Screens und gepoolte Bedingung sind positiv abhaengig, das
Produkt ist also eine Untergrenze (konservativ).

### 5.3 Lesart als Lockerung und Pflicht-Etikett je Option

| Option | gegenueber A3-Praxis | gegenueber PRD-5.1-Wortlaut / A1-Entscheidungsweg | gegenueber Verfassung | Etikett (Pflicht) |
|---|---|---|---|---|
| (a)/(d) | **Lockerung** (Fenster-Rate 0,0064 -> 0,05, C.10 x60, Zulassung 3,33 -> 2,49 SE) | Verschaerfung (2,24 -> 2,49 SE, mit L3v) | keine Bewegung (DEC-51 (1) woertlich) | "Beschlossen nach Kenntnis von A3 (GL-032) und A1 (GL-033); Lockerung gegenueber der A3-Registrierungspraxis, Rueckkehr zum Wortlaut DEC-51 (1); kippt kein Verdikt unter bindender Kalibrierung; haette A3 unter measured lauffaehig gemacht." |
| (b) | keine Bewegung | Verschaerfung (Zulassung 2,24 -> 2,98/3,33 SE) | **Verschaerfung** von DEC-51 (1)/DEC-52 (iv) (ebenfalls Torpfosten-Bewegung, strenge Richtung) | "Beschlossen nach Kenntnis von A3/A1; Verschaerfung der Verfassungs-Fehlerrate auf 0,0064 je Fenster; kippt nichts." |
| (c) | Lockerung (wie (a)) | gemischt | aendert DEC-51 (2), DEC-52 (i) | wie (a) plus "DEC-52 fuer Fenster-Power < 0,894" |
| A-Stat>=1 | - | Lockerung fuer A1-artige Statistiken (c 2,44 -> 1) | praezisiert DEC-51 (3)/(5) | "Beschlossen nach Kenntnis der A1-Feasibility; A1 waere beguenstigt gewesen (Grund E1 von GL-033 entfiele); GL-033 bleibt (theta)." |
| A-Stat | - | staerkere Lockerung (Gutschrift) | - | wie oben plus "Gutschrift fuer negative Autokorrelation" - nicht empfohlen |
| L3 / L3v | Lockerung fuer 0,60 <= P < 0,80 (GL-012 -> DEC-52, Rate 0 -> 0,85 %) | Verschaerfung gegenueber L1 (C.10 bei P 0,60..0,80 entfaellt) | aendert DEC-52 (i) | "DEC-52 (i) auf < 0,80 erweitert nach Kenntnis von A1 (P_W1 0,619 lag im Band); Retro-Check 2.0 (H-06/H-20/H-22) unberuehrt, weil dort DEC-52 bereits kein Verdikt kippte." |
| L5 | Verschaerfung | Verschaerfung | setzt DEC-52 ausser Kraft | "DEC-52 suspendiert" |

**Sequenz-Zwang.** Der naechste Kandidat ist H-27 (DEC-93). Diese Herleitung hat keine H-27-/DVOL-Daten gesehen und
keine H-27-Zahl gerechnet; ob H-27 die Regel braucht oder von ihr profitiert, ist unbekannt. Ein Beschluss jetzt
erfuellt den Sequenz-Zwang formal (vor dem Kandidaten, der sie brauchen koennte), aber er faellt nach zwei GL-012 -
deshalb das Etikett in jedem Fall.

---

## 6. Empfehlung (Auftrag 5)

### 6.1 Paket P-1a und Begruendung

**Empfohlen:** Schwelle (a) mit Klausel (d); eine SE fuer Test und Power (3.2); Autokorrelation A-Stat>=1 mit
stationaerem Bootstrap; Nuisance N-Max; Luecken-Regel L3v; Selektionsdecke ausdruecklich (I-12); Power-Rechnung im
Code.

1. (a) ist die einzige Schwellen-Semantik, unter der Verfassung (DEC-51 (1), DEC-52 (iv)), PRD-Power-Formeln,
   WP-7-Feasibility, Lo-Formel, C.10-Rate und DEC-74 (d) Satz 2 ohne Aenderung gelten. (b) muesste die Verfassung in
   strenger Richtung bewegen; "kein Torpfosten-Verschieben in KEINE Richtung" trifft beide Richtungen.
2. Die A3-Registrierung bleibt ueber Klausel (d) eine zulaessige, explizit strengere Wahl; nichts wird nachtraeglich
   umgedeutet.
3. L3v ist die kleinste monotone Aenderung, die DEC-52 erhaelt UND jeden Lauf mit Power >= 0,80 des tatsaechlich
   registrierten Gates ausstattet (DEC-51 (2), C.13); G leistet das auch, aendert aber zusaetzlich DEC-51 (2) und
   schiebt Kandidaten mit Fenster-Power 0,80..0,894 in den Zweig mit hoeherer Fehlerrate. Der Preis von L3v (Rate
   0,85 % statt 0,25 % fuer Kandidaten im Band) ist offen benannt; wer ihn nicht tragen will, waehlt L5 und
   suspendiert DEC-52 ausdruecklich.
4. A-Stat>=1 misst das richtige Objekt (PRD:487, DEC-92) und gibt nie Gutschrift (DEC-75 (8)); E4 bleibt nur dort,
   wo die Statistik nachweislich die Schluessel-Persistenz traegt.
5. Retro: kippt GL-032 und GL-033 nicht; die Teilwirkungen (A3 measured, A1 E1) stehen im Etikett.

**Gleichwertig dokumentierte Alternative P-1b** (falls der Orchestrator jede Lesart als Lockerung ausschliessen will):
Schwelle (b) + 3.2 + A-Stat>=1 + N-Max + L3v. Kippt nichts, auch keinen Teilgrund (A1 c = 1: theta_min 1,121 > 1;
A3 measured: GL-012). Verlangt die Aenderung von DEC-51 (1) (alpha je Fenster 0,0064, z_krit 2,4865), DEC-52 (iv)
(gepoolt z_krit 3,1680, alpha 0,00077), PRD:211/:225/:233/:297-307/:503 und kostet ~79 % Daten je MDE.

### 6.2 DEC-Entwurf (wortgenau)

> ### DEC-94 (ENTWURF) - Programmregel P-1: Schwelle, Power und Standardfehler aus einem Guss; Autokorrelation der Teststatistik; Luecken-Regel - prospektiv, beschlossen nach Kenntnis von A3 (GL-032) und A1 (GL-033)
> - **Anlass:** Inkonsistenzen I-1..I-12 (`state/herleitung_programmregel_p1/ENTWURF.md` Abschnitt 2): Schwellen-
>   zeilen mit MDE-Faktor gegen Power-Formeln mit kritischem Wert (PRD 5.1-5.4), Power mit Boden-SE (DEC-88/91),
>   Autokorrelation aus dem Sortierschluessel (DEC-67 E4), Luecke 0,60 <= P < 0,80 (DEC-51 (2) / DEC-52 (i) / PRD 5.1 /
>   DEC-87 (F)); DEC-93 Programm-Merkposten (a), (b).
> - **Geltung:** jede Registrierung ab H-32 und jede Feasibility- oder Power-Zeile, die nach diesem Beschluss
>   geschrieben wird. **Nicht rueckwirkend:** GL-032, GL-033, DEC-88..DEC-93, `state/registered/h28_h30_v3.yaml`
>   (sha256 `bd948f34...c299`) und der Vermerk H-31 bleiben unveraendert; kein Rueckzug, keine Neufassung von
>   H-28..H-31 auf Grund dieser Regel; ein anderes A3-/A1-Design ist eine neue Hypothese mit eigenem K (DEC-58 E2).
> - **Regel:**
>   (1) **Kritischer Wert.** Jede urteilstragende Signifikanzbedingung lautet `Statistik in registrierter Richtung >=
>   z_krit * SE` mit `z_krit = Phi^-1(1 - alpha)` zum registrierten alpha: je Fenster alpha 0,05 einseitig, z_krit
>   1,6449 (DEC-51 (1)); DEC-52-Zweig gepoolt alpha 0,01, z_krit 2,3263 (DEC-52 (iv)); zweiseitige Zensusfragen 1,9600.
>   Bootstrap-Grenzen und Null-Quantile derselben Bedingung haben das Niveau 1 - alpha. Die Zahlen 2,4865 / 3,1680 /
>   2,8016 sind MDE-Faktoren (z_krit + 0,8416) und stehen nie als Schwelle in einem Gate; Feld- und Konstantennamen
>   unterscheiden `z_krit` und `mde_faktor`.
>   (2) **Strengeres alpha nur explizit.** Eine Registrierung darf ein kleineres alpha waehlen, vor jeder
>   Feasibility-Zahl; es steht als Zahl im YAML (`alpha`, `z_krit`), und Power, MDE, Zuordnung und Positivkontrolle
>   rechnen damit. Ein Schwellenfaktor ohne zugehoeriges alpha ist ein ungueltiger Eintrag.
>   (3) **Eine SE fuer Test und Power.** Power-Zeile, MDE80, Regime-Zuordnung und GL-012-Pruefung werden mit genau der
>   Entscheidungsregel und SE-Regel des registrierten Gates gerechnet: je Bedingung `P = Phi((prior - T)/SD)`, bei
>   `T = z_krit * SE` also `Phi(prior/SE - z_krit)`; bindend ist das Minimum ueber die Bedingungen, das Produkt wird
>   berichtet; `MDE80 = max_Bedingungen (T + 0,8416 * SD)`. Ist die SE-Regel datenabhaengig, wird die SD der getesteten
>   Statistik eingesetzt, nie ein Rauschboden allein.
>   (4) **Autokorrelation der Teststatistik.** Im Lauf: `SE_W = max(SD(x)/sqrt(W), SE_stat(x))`, `SE_stat` aus dem
>   stationaeren Bootstrap (Politis/Romano) der urteilstragenden Cluster-Serie x, mittlere Blocklaenge im YAML fixiert
>   (Default 4 Wochen), >= 1.000 Replikate, Seed registriert (DEC-53). In der Power-Zeile: Varianzfaktor
>   `c = max(1, c_hat)` mit `c_hat` = Langfrist- zu naiver Varianz DERSELBEN Statistik; keine Gutschrift fuer negative
>   Autokorrelation. DEC-67 E4 (W_eff = 0,41 W) gilt nur fuer Statistiken, deren Autokorrelation nachweislich die des
>   Sortierschluessels ist (Nachweis in der Herleitung), sonst nur als deskriptive Zeile. Notation: `c` ist ein
>   Varianzfaktor, ein SD-Faktor heisst `sqrt(c)`.
>   (5) **Herkunft der Nuisance.** SD und c der Teststatistik kommen aus (i) einer Vorperiode, die vor dem ersten
>   urteilstragenden Fenster endet (nur Streuung und Autokorrelation, kein Mittel ausgegeben, Waechter im Code),
>   und/oder (ii) der kalibrierten Null-Simulation des registrierten Tests; ist die Vorperioden-Statistik versiegelt,
>   nur (ii). Bindend ist die groessere SE ueber Quellen und registrierte Kalibrierungen (stress, DEC-77 E1 (b)). Die
>   Positivkontrolle in Produktionskonfiguration ist NICHT BESTANDEN, wenn die SD ihrer Kontrollwelt mehr als 10 %
>   ueber der SD der Power-Zeile liegt.
>   (6) **Regime-Zuordnung.** Fenster-Power >= 0,80 in jedem urteilstragenden Fenster -> C.10 hart. Sonst DEC-52-Zweig,
>   wenn die Power des vollstaendigen DEC-52-Gates (gepoolte Bedingung mal Fenster-Screens) >= 0,80 ist; sonst GL-012
>   vor dem Lauf. DEC-52 (i) lautet fuer kuenftige Registrierungen "Per-Fenster-Power < 0,80"; die Grenze 0,60 entfaellt
>   als Zuordnungsgrenze. Screens (ii): Vorzeichen und `>= 0,5 * z_krit_gepoolt * SE_gepoolt` je Fenster; die
>   Band-Obergrenze 2,0x ist Etikett, keine PASS-Bedingung. Die Zuordnung wird einmal vor der Registrierung
>   festgestellt, nie nach dem Lauf.
>   (7) **Selektionsdecke.** Die Schwelle liegt ueber der Selektionsdecke (DEC-51 (4)); die Power-Zeile rechnet mit
>   `max(z_krit, z_max(K))` (Bailey/LdP), unter (1) ab K >= 12 bindend.
>   (8) **Code.** Power, MDE80 und Zuordnung berechnet eine getestete Funktion (T0, T4 auf konserviertem Payload), die
>   dieselben Schwellen- und SE-Funktionen wie der Lauf benutzt; Handrechnungen sind Gegenprobe, nie Quelle.
> - **Etikett (Pflicht):** "Beschlossen nach Kenntnis von A3 (GL-032) und A1 (GL-033), vor jeder H-27-Zahl.
>   Gegenueber der A3-Registrierungspraxis (Schwellenfaktor 2,4865, alpha je Fenster 0,0064) eine Lockerung der
>   Fenster-Fehlerrate auf den Wortlaut DEC-51 (1) (C.10 gemeinsam 4,2e-5 -> 2,5e-3); gegenueber dem PRD-5.1-Wortlaut
>   eine Verschaerfung (Zulassung bei zwei gleichen Fenstern ab 2,49 statt 2,24 SE). DEC-52 (i) auf < 0,80 erweitert
>   (gemeinsame Fehlerrate im DEC-52-Zweig 0,85 %, nicht 0,5 % wie PRD 3.5). Die Autokorrelationsregel haette A1
>   beguenstigt (Grund E1 von GL-033 entfiele). Retro-Check: kippt weder GL-032 (bindende stress-Kalibrierung) noch
>   GL-033 (theta UNBELEGT); unter der nicht bindenden measured-Kalibrierung waeren A3-mom1/mom2/mom4/rev_gap
>   DEC-52-lauffaehig gewesen."
> - **Begruendung:** Verfassungstreue Semantik (DEC-51 (1)), Konsistenz von Schwelle, Power und SE (DEC-92-Lehre als
>   Regel), monotone Zuordnung, richtiges Autokorrelationsobjekt, keine Gutschrift.
> - **Rueckbauweg:** neue DEC; Registrierungen, die unter P-1 entstanden sind, bleiben unter P-1.

### 6.3 Anzupassende Stellen (nach Beschluss; append-only-Akten werden nicht umgeschrieben)

**Dokumente**
- `scinance3-impl/CLAUDE.md:55-58` - Satz DEC-51/DEC-52: "+ P-1 (DEC-94): Schwelle = kritischer Wert, Power mit
  derselben SE, DEC-52 bei Per-Fenster-Power < 0,80".
- `PRD_SCINANCE3.md` (Nachtrag-Abschnitt, Altertext bleibt mit Verweis): :109 und :922 (MDE-Faktoren als solche
  benennen, z_krit daneben), :181 (YAML-Template: `alpha`, `z_krit`, `mde_faktor`, `se_regel`, `c_regel`,
  `power_formel`, `nuisance_quelle`), :186-187, :216 ((i) < 0,80), :225 und :939 (Rate 0,85 %, Faktor 3,4), :487
  (SE-Regel P-1 (4)), :500-503 (Zuordnung P-1 (6)), :512, :574, :634, :678, :695 (Schwelle = z_krit * SE; Kandidaten-
  zahlen erst bei deren Herleitung), :564, :566-567, :626-627, :630, :671 (Power nach P-1 (3)), :932 (A3-Power als
  ueberholt markieren).
- `state/decisions.md`: neuer Eintrag DEC-94 (append-only); Verweis-Nachtraege an DEC-67 E4, DEC-74 (d), DEC-87 (F)
  ("fuer kuenftige Registrierungen durch DEC-94 ersetzt"), keine Aenderung des Alttexts.
- `state/hypothesis_registry.md`: keine Aenderung an H-28..H-31; Registrierungsvorlage ab H-32 mit den neuen Feldern.
- `state/registered/h28_h30_v3.yaml`: **keine Aenderung** (bitgleich, Akte).
- Kompendium (`survey/ERKENNTNIS_KOMPENDIUM.md` Abschnitt C): Lehre "Schwelle, Power und SE aus einem Guss" (Vorschlag
  Audit PC v3 Abschnitt 5) - optional.

**Code** (je mit Tests; Code-Hash der A3-Registrierung bleibt fuer A3 gueltig, Aenderungen nur additiv/parametrisch)
- `wp13_xsec/gates.py:82, :100` - `Z_PER_WINDOW` als kritischer Wert aus dem YAML (`rules.z_krit`), Default 2.4865 nur
  fuer die A3-YAML (Rueckwaertskompatibilitaet, T5-Pin); Docstring :15-22.
- `wp13_xsec/nulls.py:202-203` - Kommentar korrigieren (alpha 0,0064 bzw. MDE-Faktor); aendert den Code-Hash, daher
  mit der naechsten inhaltlichen Aenderung (wie N-12 aus Review v3). `:464-480` `ic_threshold` z aus der Registrierung;
  `:494-496` Quantil `1 - alpha` aus der Registrierung.
- `wp13_xsec/run.py:289-298` - SE-Regel P-1 (4) als Option (`max(SD/sqrt(W), SE_stat)`), `:301-339` stationaerer
  Bootstrap neben MBB; `:303, :549, :674, :1081` Defaults `1 - alpha`; `:955-982` `resolve_rules` liest `alpha`/`z_krit`.
- **Neu:** Power-/MDE-/Zuordnungsfunktion (z. B. `research/wp7_universe/stats.py` oder eigenes Modul) nach P-1 (3),
  (6), (7) mit T0 und T4 (konservierter Payload: A3-v5e-Zahlen muessen GL-032 reproduzieren, A1-Zahlen GL-033).
- `wp7_universe/stats.py:27-33` - Umbenennung/Kommentar `MDE_FACTOR_WINDOW`/`MDE_FACTOR_POOLED` (Alias fuer alte
  Namen), `:221-235` Docstrings "MDE80"; `:238-253` `W_EFF_FACTOR`-Docstring auf P-1 (4) begrenzen.
- `wp7_universe/panel_load.py:507` - Null-Auffuellung (DEC-93 Merkposten (c)) als eigener Punkt, nicht P-1.

**Tests/Skripte** - `tests/unit/test_wp13_run.py:904, 1322, 2029, 2339, 2390, 2454`, `tests/unit/test_wp13_xsec.py:337,
563, 565`, `tests/unit/test_wp7_universe.py:430, 1009, 1200`, `scripts/wp13_xsec.py:61, 609`,
`scripts/wp7_universe_census.py:350`: bestehende Pins fuer die A3-YAML bleiben; neue Tests fuer P-1-YAMLs (alpha 0,05 ->
level 0,95, z_krit 1,6449) und fuer die Zuordnung (Monotonie-Test: Prior steigt -> nie von testbar zu GL-012).

### 6.4 Nicht Teil von P-1 (nur vermerkt)

- DEC-93 Merkposten (c) WP-7-Null-Auffuellung und (d) Sonderpaare I = 0: deskriptiv bzw. A1-Buchhaltung.
- DEC-52-Rate: Wenn die PRD-3.5-Absicht 0,5 % gelten soll, waere der gepoolte kritische Wert 2,5287 (alpha 0,0057)
  [rj:FPR.DEC52_crit_p_for_joint_0p5pct] - eigene DEC.
- DEC-65 (2) Stress-N_eff (I-11): klaeren, ob die Zeile entfaellt oder als Stress-Sensitivitaet der Zeitreihen-SE
  gefuehrt wird.
- DEC-52 (iii) "fenster-geclustert" mit zwei Fenstern: stratifizierter Bootstrap je Fenster (A1 EV-9 (2)) als
  Auslegung festhalten.

---

## 7. Ergebnisblindheit, Reproduktion, Grenzen

- Gelesen: Verfassung, PRD, `decisions.md`, Registry, Gate-Log, YAML, Herleitungs- und Review-Akten A1/A3, Gate-Audit
  PC v3, Code und Tests (Fundstellen oben); v5e-JSON nur Fenster W1/W2 (`noise_floor_and_threshold`,
  `beta_control_method_study`, `beta_control_recommended_high_rep`); `feasibility.json` nur `configs.A...power`
  (Werte der Nuisance aus `FEASIBILITY.md` zitiert).
- Nicht gelesen: jede Siegeldatei, das Fenster `L`, jede DVOL-/H-27-/Options-Akte (auch nicht
  `state/ANFRAGE_DATA_HARVEST_DVOL_2026-10-13.md`).
- Grenzen: DEC-52-Gate-Power als Produkt (Untergrenze); Beta-Kontroll-Quantil unter (a) in Normalnaeherung;
  CI-Bedingung (b) nicht separat modelliert (Audit PC v3 1.5: praktisch dieselbe Bedingung wie die Groesse);
  A1 nur Konfiguration A (Konfiguration B ist nach DEC-93 strenger und aendert keine Aussage hier).
- Reproduktion: `python3 -I scinance3-impl/state/herleitung_programmregel_p1/rechnung_p1.py` (Sekunden; zwei Laeufe,
  gleiche sha256 `eca434a1...cc1cc`).
