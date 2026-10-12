# Hypothesen-Registry Scinance 3.0 (append-only)

> Fortsetzung von `scinance2-impl/state/hypothesis_registry.md` (H-01..H-26).
> Neue IDs ab H-27. Kandidaten aus dem Programmentwurf (A1..A5) sind NICHT
> registriert, bis ein Eintrag hier steht. Jeder Eintrag nutzt das
> 3.0-Template (PRD 3.0 §3): YAML-Block + die zehn Pflichtzeilen
> (Power, Entscheidungsrelevanz, Cluster-Einheit, Selektions-K,
> adversariales Fixture, Kostenmodell-Bindung, Nachladbarkeits-Probe,
> Positivkontroll-Vorschaltung, Kapital/Steuer/Venue, Stress-Definition).



---

## H-28 / H-29 / H-30 - Kohorte F-XSEC1 (A3: Querschnitts-Momentum, Kurzfrist-Reversal, Vol-Anomalie), Klasse W, kapitalfrei

**Registriert:** 2026-09-21 (Orchestrator), auf Basis PRD 3.0 5.3 und Welle-1-Befund (DEC-67, DEC-70, DEC-72, DEC-73). **Status:** H-28, H-29 registriert und lauffaehig nach Bau von WP-13; **H-30 registriert, Lauf BEDINGT** auf die Vol-Drag-Feasibility-Zeile (PRD 5.3 Vorbehalt A3-V) - die Bedingung betrifft die Schaetzbarkeit des Residuums, nie ein Datenergebnis. Nichts in diesem Eintrag darf nach dem Lesen der IC-Serie geaendert werden; die reale IC-Serie des Zensus wurde nicht gelesen (DEC-73).

**Hypothesen (je ein Satz, falsifizierbar).**
- **H-28 (A3-M):** Auf dem point-in-time-Union-Universum der Bybit-USDT-Perps ist der mittlere woechentliche Spearman-Rank-IC zwischen der Formationsrendite (1/2/4 Wochen) und der Folgewochenrendite in beiden urteilstragenden Fenstern **positiv** und >= IC_min.
- **H-29 (A3-R):** Der mittlere woechentliche Rank-IC zwischen der Vorwochenrendite und der Folgewochenrendite im **Gap-Design** (ein Tag Abstand) ist in beiden Fenstern **negativ** und <= -IC_min, und bleibt es nach Ausschluss des untersten Liquiditaetsdezils.
- **H-30 (A3-V):** Der mittlere woechentliche Rank-IC zwischen dem Vol-Rang (realisierte Wochenvol, MAX-Rendite, Beta zu BTC) und der vol-gewichteten, drag-bereinigten Folgewochenrendite ist in beiden Fenstern **negativ** und <= -IC_min.

**Ertragsquelle / Zahler:** H-28 Prognose (spaet einsteigende Momentum-Chaser, aus Verlustpositionen getriebene Halter); H-29 Praemie fuer Liquiditaetsbereitstellung (durchgedrueckter Fluss, liquidierte gehebelte Halter); H-30 Praemie gegen Lotterie-Nachfrage.

**Nicht-Wiederholungs-Nachweis (C.1):** wie PRD 5.3 - Breite K >= 260 statt N=5 (Rauschboden 0,0411 statt 0,50, Faktor 12), Wochenhorizont, Bounce-/Drag-Kontrolle, survivorship-freies Universum (261 delistete Symbole, DEC-72).

```yaml
id: A3 (H-28 A3-M, H-29 A3-R, H-30 A3-V)
klasse: W
capital_free: true
hypothese: siehe oben (drei Saetze, je eine Richtung)
ertragsquelle: Prognose (H-28) | Praemie Liquiditaet (H-29) | Praemie Lotterie (H-30)
metric: mittlerer woechentlicher Spearman-Rank-IC (Charakteristik_t vs. Rendite_t+1), nicht ueberlappend, gepoolt ueber das PIT-Union-Universum je Woche
richtung: H-28 positiv | H-29 negativ | H-30 negativ
windows:
  - {id: W1, von: 2024-07-01, bis: 2025-06-30, rolle: urteilstragend}
  - {id: W2, von: 2025-07-01, bis: 2026-06-30, rolle: urteilstragend}
  - {id: L,  von: 2021-03-01, bis: 2024-06-30, rolle: aera-profil}
fenster_regel: C10_hart
threshold: {wert: "IC_min = 2.4865 * SD_null / sqrt(52) = 2.4865 * 0.04112 / 7.2111 = 0.01418 je Fenster; Vorzeichen je Hypothese", ref: "state/runs/wp7_20260921/null_ic_per_window_w52.json (sha256 im Report) + tests/unit/test_wp7_universe.py::test_sd_null_threshold"}
structural_null:
  komponenten: [Querschnitts-Permutation innerhalb jeder Woche (1000, ganze Pipeline), Persistenz-Null (AR(1) der IC-Serie unter H0 simuliert), H-29 Bid-Ask-Bounce (Gap-Design strukturell), H-30 Vol-Drag sigma^2/2 analytisch abgezogen + vol-geschichtete Permutation]
  wert: "SD_null 0.04112 (W=52), 0.04398 (W=104); Persistenz-Null und Drag-Term werden vom Treiber WP-13 vor dem Lauf berichtet"
  ref: "state/runs/wp7_20260921/null_ic_per_window_w52.json; WP-13 tests T1 (zu bauen)"
power:
  alpha: 0.05
  sided: one
  power: 0.80
  z: 2.4865
  cluster_unit: kalenderwoche
  n_eff: "52 Wochen je Fenster; Sensitivitaet W_eff = 0.41*52 = 21 (Funding-Autokorrelation als konservative Obergrenze, DEC-67 E4; IC-Autokorrelation wird vom Treiber gemessen und berichtet)"
  a_priori_effekt: "IC_prior = 0.03 [sek, R2 0.3C]"
  detectable_effect: "0.01418 (= IC_min bei Power 0.80)"
  per_fenster_power: "Phi(0.03/0.005702 - 1.6449) = Phi(3.62) = 0.9999; unter W_eff 21: Phi(0.03/0.00890 - 1.6449) = Phi(1.73) = 0.958"
  zuordnungsregel: "Per-Fenster-Power >= 0.60 -> C.10 hart (beide Fenster einzeln); < 0.60 -> DEC-52. Festgestellt VOR dem Lauf: C.10 hart."
  ref: "state/WELLE1_BEFUND_TEIL6_2026-09-21.md; PRD 5.3"
selection: {K: 7, ceiling_analytic: "E[max IC_null ueber 7 Varianten] = 0.005702 * 1.386 = 0.0079 < IC_min 0.0142", ceiling_measured_ref: "WP-13 Null-Fixture (T1) - Pflicht vor dem Lauf"}
economic_minimum: {wert: "IC 0.062 Einzelposition / 0.102 Portfolio bei 18 bp Wochenkosten", ref: "PRD 5.3", label: unter_wand}
decision_relevance:
  on_pass: "getrennte Tradability-Registrierung mit symbolspezifischer Slippage (PERP_SPREAD_BP je Dezil, DEC-67); kein Kapitalpfad vor tradability3"
  on_drop: "Klasse W auf Bybit-Perps im Wochenhorizont erschoepft (D.7 auf breiter Basis bestaetigt); H-27/A1 unberuehrt"
capital_tax_venue: {kapitalbasis: "n/a (kapitalfrei)", steuer: "n/a", venue_event: "n/a", zahler_post_2024: "Delisting-Hazard 2023/24-Kohorten ~50 % - Zahlerbestand wechselt schnell (Etikett)"}
stress_episode: {liste_ref: "scinance3-impl/state/wp10_stress_canon/stress_rel.json (lokal; sha256 eb83fe40...)", rolle: abdeckungsnachweis, n_episoden: "STRESS_ABS in W1: 2 Tage, W2: 1 Tag; STRESS_REL-Zaehlung je Fenster wird vom Treiber aus der Fixture berichtet"}
irreversibility_probe: {ergebnis: nachladbar, ref: "V-1 (funding/history), WP-7 panel_1d, WP-12b panel_1d_delisted - alles oeffentlich"}
positive_control: {laufzeit_geschaetzt_h: 0.2, vorgeschaltet: false, ref: "Zensus-Laufzeit Minuten; Positiv-Fixture ist Test T1"}
fixtures:
  positive: "Panel mit injiziertem Querschnitts-IC 0.06 inkl. BTC-Beta-Faktor und Sektor-Bloecken (alle drei Gates muessen feuern)"
  null: "Faktor innerhalb jeder Woche permutiert (kein Gate feuert; gemessene Selektions-Decke)"
  adversarial: "Faktor mechanisch mit Markt-Beta korreliert auf Panel mit dominantem Marktfaktor (kein Gate darf feuern); H-29: Random Walk mit Bid-Ask-Bounce ohne Reversion; H-30: identische Vol-Dispersion ohne Zusammenhang"
artifacts:
  cluster_series_ref: "WP-13: IC-Wochenserie je Hypothese/Variante/Fenster als CSV + sha256"
  bootstrap_replicates_ref: "WP-13: 1000 Permutations- und Bootstrap-Replikate oder Seed 53 + Generator-Fingerprint"
fdr_family: F-XSEC1 (7 Tests, BH alpha 0.10)
over_family: F-WEEK -> Wellen-Ueber-Familie abhaengigkeitsrobust (DEC-62/65)
feasibility_verdict: bestanden (B2; K >= 260; Union-Panel; H-30 Feasibility-Zeile ausstehend)
constants_hash: "n/a - kapitalfrei; tradability3 nicht gebaut (DEC-59 Werkzeug offen)"
data_fingerprints: ["panel_1d + panel_1d_delisted Union-Range a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a", "delisting_dates.json 852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933"]
stats3_version: "wp7_universe (Commit 06ac7e5)"
bedingung_welle_1: [WP-7 B2, WP-12b, WP-10 FDR-Struktur]
```

**Gate-Text (woertlich aus PRD 5.3, bindend):** Ein A3-Faktor gilt als kapitalfrei BESTANDEN, wenn (1) der mittlere Wochen-Rank-IC in beiden urteilstragenden Fenstern die registrierte Schwelle mit dem registrierten Vorzeichen erreicht (C.10 hart); (2) das Ergebnis oberhalb der Querschnitts-Permutations-Null UND der Persistenz-Null liegt; (3) BH-FDR alpha 0,10 innerhalb F-XSEC1, danach die Ueber-Familie abhaengigkeitsrobust; (4) H-29: IC bleibt im Gap-Design und nach Ausschluss des untersten Liquiditaetsdezils erhalten, sonst Etikett Illiquiditaets-Artefakt; (5) H-30: Spearman gegen die Size-/Volumen-Achse < 0,60 (Erreichbarkeit vor dem Lauf am Panel geprueft); (6) DEC-53-Artefakte geschrieben, sonst KEIN VERDIKT; (7) das Gate faellt auf dem adversarialen Beta-Fixture durch. Panel-Mitglieder sind Beobachtungen, keine Hypothesen (L-7).

**Kill-Bedingungen (vorab):** K < 134 in einem Fenster; H-29: Bounce-Abzug erklaert den IC allein; H-30: Drag-Term > 2x plausible Kante und durch Vol-Gewichtung nicht unter ein Viertel drueckbar (Feasibility-Zeile). NICHT: sigma_xs (Etikett).

**Etiketten:** Klasse W; kapitalfrei; C.10 hart; unter_wand; zweistufige FDR abhaengigkeitsrobust; H-29 Bounce-Kontrolle urteilstragend; H-30 schaetzfehler-dominiert; Union-Panel survivorship-frei (DEC-72), `--allow-partial` (DEC-66).

---

## Rueckzug des Eintrags H-28/H-29/H-30 vom 2026-09-21 (Erstfassung) - append-only, kein Lauf erfolgt

**Datum:** 2026-09-21 (Orchestrator), nach adversarischem Opus-Review (`state/REVIEW_H28_H30_v1.md`). Der Eintrag oben bleibt unveraendert stehen und ist **zurueckgezogen**; kein Treiber wurde gegen ihn gebaut, keine IC-Serie gelesen. Bindende Befunde des Reviews (DEC-74): Schwelle aus einem fensterfremden Messfenster (W1 um 17 % zu niedrig); Permutations-Null ist die Identitaet E_t[1/sqrt(K_t-1)], Serienabhaengigkeit bleibt unbehandelt (rho = 0 in der Schwelle, DEC-51 (3)); Persistenz-Null ohne Wert und Regel (C.4); FDR-Stufe nicht ausfuehrbar; Gate (4) widerspruechlich; Gate (5) Erreichbarkeit nicht geprueft, aber als geprueft beschrieben (C.1); H-30-Feasibility einheitenlos; Survivorship-Behandlung weicht von PRD 4.1 DoD (4) ab; oekonomisches Etikett veraltet; Positiv-Fixture blind fuer Selbst-Ausrichtung. **Zweitfassung folgt nach dem Vorlauf WP-13a** (Schwellen je Fenster, Persistenz-Null, Erreichbarkeit 0,60, Vol-Drag-Feasibility, Delisting-Zaehlung, STRESS_REL-Abdeckung - alles ohne Outcome-Daten).

---

## H-28 / H-29 / H-30 - Zweitfassung (2026-09-22): Kohorte F-XSEC1 (A3), Klasse W, kapitalfrei

**Registriert:** 2026-09-22 (Orchestrator) nach Rueckzug der Erstfassung (DEC-74) und Vorlauf WP-13a (`state/runs/wp13a_20260922/`, `wp13a_prelaunch.json` sha256 `194ead3a2ee8f13c90e3319cf30813099d748be483c65bbe2ba7599d8838a235`, Seed 53, 1.000 Persistenz-Simulationen, Konvention `close_at_last`). Der Vorlauf hat **keine** reale Signal-Outcome-Verknuepfung berechnet (Siegel-Tests `tests/unit/test_wp13_xsec.py::test_seal_*`); das L-Fenster liegt versiegelt in `wp13a_prelaunch_L_window_sealed.json` und wird erst nach dem GL-Eintrag geoeffnet. Diese Fassung geht vor dem Bau des Lauf-Modus in den adversarischen Review; Aenderungen danach nur als neuer Eintrag.

### Gemeinsame Festlegungen der Kohorte (bindend fuer alle drei Hypothesen)

**Panel und Universum.** Vereinigung `data/panel_1d` (877 Ueberlebende, Stichtag 2026-09-14) + `data/panel_1d_delisted` (261 delistete Symbole mit Historie, Register-Stichtag 2026-09-16; Union-Range-Fingerprint `a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a`; `delisting_dates.json` `852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933`, Quelle durchgehend Announcement-Datum). PIT-Maske: Symbol lebt ab >= 8 Wochen Historie bis zur Woche des Delisting-Datums (DEC-72; Wiederlistungen nach Form a/b/c). Beide Stichtage liegen nach W2-Ende: kein Look-ahead in W1/W2. `--allow-partial` (69 Quellen-Luecken, DEC-66): keine davon in W1/W2 erheblich (K-Reihen im Artefakt).

**Cluster-Einheit und Metrik.** Kalenderwoche (ISO); die K_t Symbole einer Woche werden zu EINEM Spearman-Rank-IC gepoolt (L-7). Urteilstragende Groesse je Hypothese: Mittel des Wochen-IC ueber die Wochen des Fensters. Outcome = Folgewochenrendite (log), nicht ueberlappend. **Survivorship-Konvention (urteilstragend):** `close_at_last` - ein in Woche t lebendes, in t+1 delistetes Symbol bleibt im Querschnitt mit Folgerendite 0 (PRD 4.1 DoD (4)); die Fassung `drop` ist Pflicht-Sensitivitaet. Betroffene Symbol-Wochen: W1 80 (von 22.900), W2 140 (von 29.900). NO_HISTORY-Symbole in den Fenstern: W1 LITUSDT, MONUSDT, DATAUSDT; W2 SPCXUSDT - Etikett "<= 1 % des Querschnitts fehlt".

**Fenster.** W1 = 2024-07-01..2025-06-30 (53 ISO-Wochen, Wochenliste im Artefakt, K 345..515, Median 419); W2 = 2025-07-01..2026-06-30 (52 Wochen, 2025-07-07..2026-06-29, K 514..606, Median 589); L = 2021-03-01..2024-06-30 (174 Wochen, aera-profil, versiegelt, kein Vorzeichen-Argument). Die 11 Wochen 2026-07-01..2026-09-14 sind **nicht beurteilt und werden nach dem Verdikt nicht nachgereicht**. Fenster-Regel: **C.10 hart** (beide Fenster einzeln; Per-Fenster-Power des registrierten Tests gegen IC_prior 0,03: W1 Phi(0,03/0,00666 - 2,4865) = 0,98, W2 Phi(0,03/0,00581 - 2,4865) = 0,996; unter c_rho 1,13 (mom1 W2) 0,99). DEC-52-Zweig ausgeschlossen.

**Schwelle je Fenster und Variante (vorab, analytisch):** `IC_min = 2,4865 * E_t[1/sqrt(K_t-1)] * max(1, c_rho) / sqrt(W)`. Rauschboden E_t[1/sqrt(K_t-1)] = 0,04849 (W1, 53 W), 0,04190 (W2, 52 W) - exakte Permutationsvarianz, blind fuer Korrelationsstruktur (kein "gemessener" Boden). c_rho aus der Persistenz-Null (unten), **nach unten auf 1 gedeckelt** (eine Null darf die Schwelle nie unter den rho=0-Wert senken). Alpha-Semantik: Kritwert-Faktor 2,4865 (Groesse je Fenster 0,0064, gemeinsam 4,1e-5); MDE bei Power 0,80 = IC_min; Referenztest ist der registrierte, nicht der 1,6449-Test.

| Variante | IC_min W1 | IC_min W2 | c_rho W1 / W2 (roh) | Persistenz-Null q95 in Richtung W1 / W2 |
|---|---:|---:|---|---|
| mom1 (H-28) | **0,01838** | **0,01634** | 1,110 / 1,131 | -0,0064 / -0,0362 |
| mom2 (H-28) | **0,01656** | **0,01445** | 0,974 / 0,995 | +0,0074 / -0,0094 |
| mom4 (H-28) | **0,01656** | **0,01445** | 0,959 / 0,982 | +0,0081 / -0,0064 |
| rev_gap (H-29, Richtung negativ) | **0,01656** | **0,01445** | 0,957 / 0,976 | +0,0063 / +0,0195 (5 %-Quantil) |
| vol_rv (H-30) | **0,01656** | **0,01445** | 0,936 / 0,930 | -0,0112 / -0,0105 |
| vol_max (H-30) | **0,01656** | **0,01445** | 0,939 / 0,925 | -0,0119 / -0,0101 |
| vol_beta (H-30) | **0,01656** | **0,01445** | 0,912 / 0,843 | -0,0119 / -0,0105 |

**Persistenz-Null (registriert, DEC-74 (c)):** je Symbol AR(1) auf den Wochenrenditen des Fensters (phi geclippt bei |0,98|, Median phi 0,00, Q25 -0,04 (W1) / -0,09 (W2)), 1.000 Simulationen mit Seed 53, volle Pipeline je Variante, Statistik = Mittel-IC ueber die Fensterwochen. Vol-Varianten nutzen in der Simulation Wochen-Proxies (|r|, Querschnittsmittel als Marktfaktor) - Etikett. Die Null-Mittel sind fuer mom1/mom2/mom4 negativ (-0,019..-0,047) und fuer rev_gap positiv (+0,018..+0,030): die Wochen-Autokorrelation der Renditen wirkt GEGEN beide registrierten Richtungen; die Persistenz-Komponente ist damit fuer H-28/H-29 nicht bindend, wird aber als Gate (2) mitgefuehrt. **Gate-Text (2):** Mittel-IC liegt jenseits des registrierten Quantils der Persistenz-Null (q95 fuer positive, q05 fuer negative Richtung) UND jenseits von IC_min.

**Selektion.** K = 7 (bleibt Nenner fuer BH und Decke, auch wenn eine Variante nicht laeuft). Decke analytisch (Bailey/LdP, ohne den PRD-Faktor 1/sqrt(2), der aus dem gepoolten 2-Jahres-Sharpe stammt): W1 0,00923, W2 0,00790; **gemessen am Null-Fixture mit der K-Reihe und W des Fensters (300 Replikate, Seed 53): W1 0,00909, W2 0,00809** - beide unter jedem IC_min. Liegt die im Lauf erneut gemessene Decke ueber IC_min eines Fensters: GL-012-DROP vor dem Verdikt, Schwelle wird nicht angehoben.

**FDR (DEC-74 (e)).** Einheit = Variante (7). p-Wert je Variante = Permutations-p (>= 10.000 Permutationen innerhalb der Wochen, ganze Pipeline) des **schwaecheren** Fensters (Max-p). BH alpha 0,10 innerhalb F-XSEC1 zum Laufzeitpunkt. Ueber-Familie F-WEEK: Benjamini-Yekutieli (c(m) = sum 1/i) am Wellenschluss ueber alle bis dahin registrierten Wochen-Hypothesen; das A3-Verdikt traegt bis dahin das Etikett "vorlaeufig bis F-WEEK geschlossen".

**Gate (5) Erreichbarkeit (geprueft im Vorlauf, ohne Outcome):** Median Spearman(vol_rv-Rang, Turnover-Rang) W1 0,159 (Q25/Q75 0,105/0,227), W2 0,142 (0,105/0,164) - die importierte 0,60 ist erreichbar; Size-Achse = trailing 8-Wochen-Median-Turnover (PIT), keine Marktkapitalisierung im Panel.

**H-30-Feasibility (Vorlauf, L-Fenster):** Kante = 3,51 * 0,03 * sigma_xs(L) = 91,4 bp/Woche; Drag_rest nach Vol-Gewichtung (Ziel-Vol = Median-Wochenvol L) = target_vol^2/2 = 8,5 bp/Woche; Verhaeltnis 0,093 <= 0,5 -> **H-30 laeuft**. Die Drag-Bereinigung im Lauf: je Symbol-Woche wird sigma_w^2/2 (aus den Tagesrenditen der Woche) von der vol-gewichteten Folgewochenrendite abgezogen; die Vol-Gewichtung skaliert die Rendite auf die Ziel-Vol.

**Liquiditaets-Sensitivitaet (Gate (4), H-29):** Ausschluss des untersten Turnover-Dezils (trailing 8-Wochen-Median, PIT) ist **Pflicht-Sensitivitaet mit Etikett**, keine PASS-Bedingung; Etikett "Illiquiditaets-Artefakt", wenn `IC_ohne_D1 > -0,5 * IC_min` in einem Fenster.

**Fixtures (T1, alle vor dem Lauf gruen; T2 Determinismus N>=3; T7 Artefakt-Round-Trip):** positiv (injizierter IC 0,06 mit BTC-Beta-Faktor und Sektor-Bloecken: alle Gates feuern); null_fixture (Wochen-Permutation: kein Gate feuert, Decke gemessen); adversarial (Beta-korrelierte Charakteristik: kein Gate feuert; H-29: Random Walk mit Bounce; H-30: Vol-Dispersion ohne Zusammenhang); Ausrichtungs-Fixture (IC exakt +1,000 / -1,000); Lag-Profil -1..+2 (nur +1 zeigt den Effekt; auf Realdaten berichtet, nie geurteilt); Delisting-Fixture (drop vs. close_at_last, Differenz im CI um 0); schwellennahes Fixture (Trefferquote 0,4-0,6). Positivkontrolle **vorgeschaltet** (Laufzeit > 1 h wegen 10.000 Permutationen x 7 x 2).

**DEC-53-Artefakte (Pflicht, sonst KEIN VERDIKT):** IC-Wochenserie je Variante/Fenster/Konvention (CSV + sha256), K-Reihe und Wochenliste je Fenster, Permutations- und Persistenz-Replikate oder Seed + Generator-Fingerprint, Bootstrap-Replikate des Wochen-Cluster-CI, Lag-Profil, Liquiditaets-Sensitivitaet, L-Fenster in getrennter versiegelter Datei.

**Oekonomisches Etikett (C.2, kein Gate):** Portfolio-Minimum IC = 2 * 18 bp / (3,51 * 1018 bp) = **0,0101** (unter IC_min - im Portfoliorahmen ist die statistische Schwelle die bindende); Einzelposition 0,062 (IC_prior 0,03 liegt darunter: `unter_wand` nur im Einzelpositionsrahmen). Kostenbasis 18 bp Wochenkosten (A3-M), 30 bp (A3-R), 4,5-7,5 bp (A3-V); Taker-Wand 11 bp getrennt (B4 nicht ausgeloest).

**Stress-Abdeckung (DEC-56 (1), Nachweis, kein Filter; fuer Klasse W freiwillig gefuehrt):** STRESS_REL (`state/runs/stress_rel.json`, sha256 `6648a210c25fd3dd...` Datei / Kanon `eb83fe402b7b8724...`): W1 22 Tage, W2 8 Tage; STRESS_ABS (`stress_abs.json` `b8008257e963eaa2...`): W1 2, W2 1.

**Abweichungen vom PRD-Text (Etiketten, bestaetigt):** Reversal-Gap = eine Woche statt ein Tag (Wochenpanel; der Bid-Ask-Bounce ist auf Wochenschluss-Ebene mit Wochen-Gap strukturell eliminiert); Persistenz-Null mit Wochen-Proxies fuer Vol-Varianten; Delisting-Datum = Announcement-Datum (Maske endet einige Tage vor Handelsende, konservativ).

**Entscheidungsrelevanz.** PASS eines Faktors: getrennte Tradability-Registrierung mit gemessener Dezil-Slippage (DEC-67 E4), kein Kapitalpfad vor `tradability3`. DROP aller drei: Klasse W auf Bybit-Perps im Wochenhorizont erschoepft (D.7 breit bestaetigt). Kill vor dem Verdikt: K < 134 (min der K-Reihe) in einem Fenster; gemessene Decke >= IC_min; H-30 Feasibility (erledigt: feasibel).

**Nicht-Wiederholungs-Nachweis (C.1):** wie Erstfassung; Rauschboden 0,048/0,042 statt 0,50 (N=5), Wochenhorizont, Bounce-/Drag-Kontrolle, survivorship-freies Universum.

**Constants/Version:** `constants_hash: n/a - kapitalfrei; Kostenkonstanten-Modul tradability3 nicht gebaut (Werkzeug-DEC offen, PRD 3.4)`; `stats3_version: wp13_xsec Commit 94aa9e6 (Vorlauf); Lauf-Modus-Commit wird im GL-Eintrag genannt`.

### H-28 - A3-M Querschnitts-Momentum

**Hypothese:** Auf dem PIT-Union-Universum ist der mittlere woechentliche Rank-IC zwischen der Formationsrendite (1, 2, 4 Wochen) und der Folgewochenrendite in W1 und W2 jeweils positiv und >= IC_min der Variante.

**Ertragsquelle / Zahler:** Prognose; Zahler: spaet einsteigende Momentum-Chaser und aus Verlustpositionen getriebene Halter

```yaml
id: H-28
kohorte: A3 / F-XSEC1
klasse: W
capital_free: true
hypothese: "Auf dem PIT-Union-Universum ist der mittlere woechentliche Rank-IC zwischen der Formationsrendite (1, 2, 4 Wochen) und der Folgewochenrendite in W1 und W2 jeweils positiv und >= IC_min der Variante."
ertragsquelle: "Prognose; Zahler: spaet einsteigende Momentum-Chaser und aus Verlustpositionen getriebene Halter"
metric: "Mittel des woechentlichen Spearman-Rank-IC (Charakteristik_t vs. Folgewochenrendite_t+1, close_at_last), je Fenster"
varianten: [mom1, mom2, mom4]
richtung: positiv
windows:
  - {id: W1, von: 2024-07-01, bis: 2025-06-30, wochen: 53, rolle: urteilstragend}
  - {id: W2, von: 2025-07-01, bis: 2026-06-30, wochen: 52, rolle: urteilstragend}
  - {id: L,  von: 2021-03-01, bis: 2024-06-30, wochen: 174, rolle: aera-profil, versiegelt: true}
fenster_regel: C10_hart
threshold:
  W1: {mom1: 0.01838, mom2: 0.01656, mom4: 0.01656}
  W2: {mom1: 0.01634, mom2: 0.01445, mom4: 0.01445}
  formel: "2.4865 * E_t[1/sqrt(K_t-1)] * max(1, c_rho) / sqrt(W)"
  ref: "state/runs/wp13a_20260922/wp13a_prelaunch.json#windows.<W>.noise_floor_and_threshold.ic_min_per_variant (sha256 194ead3a...); Pin: WP-13 T5 test_ic_min_pins_registered_values"
structural_null:
  komponenten: [permutation_within_week, persistence_ar1]
  permutation_floor: {W1: 0.04849, W2: 0.04190, ref: "wp13a_prelaunch.json#windows.<W>.noise_floor_and_threshold.floor.e_floor"}
  persistence_quantile_registered_direction: {W1: {mom1: -0.0064, mom2: 0.0074, mom4: 0.0081}, W2: {mom1: -0.0362, mom2: -0.0094, mom4: -0.0064}, ref: "wp13a_prelaunch.json#windows.<W>.noise_floor_and_threshold.persistence_null.variants"}
power:
  alpha: 0.05
  sided: one
  power: 0.80
  z: 2.4865
  cluster_unit: kalenderwoche
  n_eff: {W1: 53, W2: 52, rho_ref: "c_rho aus der Persistenz-Null je Variante (Tabelle oben), auf >= 1 gedeckelt; reale IC-Autokorrelation wird nach dem Lauf berichtet"}
  a_priori_effekt: 0.03
  a_priori_ref: "R2 0.3C [sek]"
  detectable_effect: {W1: {mom1: 0.01838, mom2: 0.01656, mom4: 0.01656}, W2: {mom1: 0.01634, mom2: 0.01445, mom4: 0.01445}}
  per_fenster_power_registrierter_test: {W1: 0.98, W2: 0.996}
  zuordnungsregel: "Per-Fenster-Power >= 0.60 -> C.10 hart; festgestellt vor dem Lauf"
  ref: "Zweitfassung, Abschnitt Fenster"
selection: {K: 7, ceiling_analytic: {W1: 0.00923, W2: 0.00790}, ceiling_measured: {W1: 0.00909, W2: 0.00809, n_replicates: 300, seed: 53}, ceiling_measured_ref: "wp13a_prelaunch.json#windows.<W>.selection_ceiling_measured", regel: "gemessene Decke >= IC_min -> GL-012-DROP vor dem Verdikt"}
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, ref: "PRD 4.1 sigma_xs_min invertiert; sigma_xs 1018 bp (wp7_20260914), 18 bp", label: "unter_wand nur Einzelposition"}
decision_relevance: {on_pass: "Tradability-Registrierung mit Dezil-Slippage (DEC-67 E4)", on_drop: "Klasse W im Wochenhorizont erschoepft"}
capital_tax_venue: {kapitalbasis: "n/a kapitalfrei", steuer: "n/a", venue_event: "n/a", zahler_post_2024: "Delisting-Hazard 2023/24 ~50 % (Etikett)"}
stress_episode: {liste_ref: "state/runs/stress_rel.json (sha256 6648a210c25fd3dd)", rolle: abdeckungsnachweis, n_tage: {W1: 22, W2: 8}}
irreversibility_probe: {ergebnis: nachladbar, ref: "V-1, WP-7, WP-12b"}
positive_control: {laufzeit_geschaetzt_h: 2, vorgeschaltet: true, ref: "10.000 Permutationen x 7 x 2 + Persistenz-Null"}
fixtures: {positive: "injizierter IC 0.06 + Beta + Sektoren", null_fixture: "Wochen-Permutation", adversarial: "Beta-korrelierte Charakteristik", alignment: "+1.000/-1.000", lag_profile: "-1..+2", delisting: "drop vs close_at_last", near_threshold: "Trefferquote 0.4-0.6"}
artifacts:
  cluster_series_ref: "WP-13 Lauf: ic_weekly_<variante>_<fenster>_<konvention>.csv + sha256"
  bootstrap_replicates_ref: "WP-13 Lauf: Seed 53 + Generator-Fingerprint, Permutations-/Persistenz-/Bootstrap-Replikate"
fdr_family: "F-XSEC1 (7, BH 0.10, Max-p ueber Fenster, >= 10000 Permutationen)"
over_family: "F-WEEK (Benjamini-Yekutieli am Wellenschluss; Verdikt bis dahin vorlaeufig)"
feasibility_verdict: bestanden
constants_hash: "n/a - kapitalfrei; tradability3 nicht gebaut"
data_fingerprints: ["union a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a", "delisting_dates 852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933", "prelaunch 194ead3a2ee8f13c90e3319cf30813099d748be483c65bbe2ba7599d8838a235", "Stichtage: Ueberlebende 2026-09-14, Register 2026-09-16"]
stats3_version: "wp13_xsec 94aa9e6 (Vorlauf); Lauf-Commit im GL-Eintrag"
bedingung_welle_1: [WP-7 B2, WP-12b, WP-13a]
```

### H-29 - A3-R Kurzfrist-Reversal im Gap-Design

**Hypothese:** Auf dem PIT-Union-Universum ist der mittlere woechentliche Rank-IC zwischen der Rendite der Woche t-1 (eine Woche Gap) und der Folgewochenrendite t+1 in W1 und W2 jeweils negativ und <= -IC_min.

**Ertragsquelle / Zahler:** Praemie fuer Liquiditaetsbereitstellung; Zahler: durchgedrueckter Fluss, liquidierte gehebelte Halter

```yaml
id: H-29
kohorte: A3 / F-XSEC1
klasse: W
capital_free: true
hypothese: "Auf dem PIT-Union-Universum ist der mittlere woechentliche Rank-IC zwischen der Rendite der Woche t-1 (eine Woche Gap) und der Folgewochenrendite t+1 in W1 und W2 jeweils negativ und <= -IC_min."
ertragsquelle: "Praemie fuer Liquiditaetsbereitstellung; Zahler: durchgedrueckter Fluss, liquidierte gehebelte Halter"
metric: "Mittel des woechentlichen Spearman-Rank-IC (Charakteristik_t vs. Folgewochenrendite_t+1, close_at_last), je Fenster"
varianten: [rev_gap]
richtung: negativ
windows:
  - {id: W1, von: 2024-07-01, bis: 2025-06-30, wochen: 53, rolle: urteilstragend}
  - {id: W2, von: 2025-07-01, bis: 2026-06-30, wochen: 52, rolle: urteilstragend}
  - {id: L,  von: 2021-03-01, bis: 2024-06-30, wochen: 174, rolle: aera-profil, versiegelt: true}
fenster_regel: C10_hart
threshold:
  W1: {rev_gap: 0.01656}
  W2: {rev_gap: 0.01445}
  formel: "2.4865 * E_t[1/sqrt(K_t-1)] * max(1, c_rho) / sqrt(W)"
  ref: "state/runs/wp13a_20260922/wp13a_prelaunch.json#windows.<W>.noise_floor_and_threshold.ic_min_per_variant (sha256 194ead3a...); Pin: WP-13 T5 test_ic_min_pins_registered_values"
structural_null:
  komponenten: [permutation_within_week, persistence_ar1, bid_ask_bounce_gap_design; Sensitivitaet: unterstes Turnover-Dezil ausgeschlossen (Etikett)]
  permutation_floor: {W1: 0.04849, W2: 0.04190, ref: "wp13a_prelaunch.json#windows.<W>.noise_floor_and_threshold.floor.e_floor"}
  persistence_quantile_registered_direction: {W1: {rev_gap: 0.0063}, W2: {rev_gap: 0.0195}, ref: "wp13a_prelaunch.json#windows.<W>.noise_floor_and_threshold.persistence_null.variants"}
power:
  alpha: 0.05
  sided: one
  power: 0.80
  z: 2.4865
  cluster_unit: kalenderwoche
  n_eff: {W1: 53, W2: 52, rho_ref: "c_rho aus der Persistenz-Null je Variante (Tabelle oben), auf >= 1 gedeckelt; reale IC-Autokorrelation wird nach dem Lauf berichtet"}
  a_priori_effekt: 0.03
  a_priori_ref: "R2 0.3C [sek]"
  detectable_effect: {W1: {rev_gap: 0.01656}, W2: {rev_gap: 0.01445}}
  per_fenster_power_registrierter_test: {W1: 0.98, W2: 0.996}
  zuordnungsregel: "Per-Fenster-Power >= 0.60 -> C.10 hart; festgestellt vor dem Lauf"
  ref: "Zweitfassung, Abschnitt Fenster"
selection: {K: 7, ceiling_analytic: {W1: 0.00923, W2: 0.00790}, ceiling_measured: {W1: 0.00909, W2: 0.00809, n_replicates: 300, seed: 53}, ceiling_measured_ref: "wp13a_prelaunch.json#windows.<W>.selection_ceiling_measured", regel: "gemessene Decke >= IC_min -> GL-012-DROP vor dem Verdikt"}
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, ref: "PRD 4.1 sigma_xs_min invertiert; sigma_xs 1018 bp (wp7_20260914), 18 bp", label: "unter_wand nur Einzelposition"}
decision_relevance: {on_pass: "Tradability-Registrierung mit Dezil-Slippage (DEC-67 E4)", on_drop: "Klasse W im Wochenhorizont erschoepft"}
capital_tax_venue: {kapitalbasis: "n/a kapitalfrei", steuer: "n/a", venue_event: "n/a", zahler_post_2024: "Delisting-Hazard 2023/24 ~50 % (Etikett)"}
stress_episode: {liste_ref: "state/runs/stress_rel.json (sha256 6648a210c25fd3dd)", rolle: abdeckungsnachweis, n_tage: {W1: 22, W2: 8}}
irreversibility_probe: {ergebnis: nachladbar, ref: "V-1, WP-7, WP-12b"}
positive_control: {laufzeit_geschaetzt_h: 2, vorgeschaltet: true, ref: "10.000 Permutationen x 7 x 2 + Persistenz-Null"}
fixtures: {positive: "injizierter IC 0.06 + Beta + Sektoren", null_fixture: "Wochen-Permutation", adversarial: "Beta-korrelierte Charakteristik, bid_ask_bounce_gap_design; Sensitivitaet: unterstes Turnover-Dezil ausgeschlossen (Etikett)", alignment: "+1.000/-1.000", lag_profile: "-1..+2", delisting: "drop vs close_at_last", near_threshold: "Trefferquote 0.4-0.6"}
artifacts:
  cluster_series_ref: "WP-13 Lauf: ic_weekly_<variante>_<fenster>_<konvention>.csv + sha256"
  bootstrap_replicates_ref: "WP-13 Lauf: Seed 53 + Generator-Fingerprint, Permutations-/Persistenz-/Bootstrap-Replikate"
fdr_family: "F-XSEC1 (7, BH 0.10, Max-p ueber Fenster, >= 10000 Permutationen)"
over_family: "F-WEEK (Benjamini-Yekutieli am Wellenschluss; Verdikt bis dahin vorlaeufig)"
feasibility_verdict: bestanden
constants_hash: "n/a - kapitalfrei; tradability3 nicht gebaut"
data_fingerprints: ["union a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a", "delisting_dates 852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933", "prelaunch 194ead3a2ee8f13c90e3319cf30813099d748be483c65bbe2ba7599d8838a235", "Stichtage: Ueberlebende 2026-09-14, Register 2026-09-16"]
stats3_version: "wp13_xsec 94aa9e6 (Vorlauf); Lauf-Commit im GL-Eintrag"
bedingung_welle_1: [WP-7 B2, WP-12b, WP-13a]
```

### H-30 - A3-V Vol-/MAX-/Beta-Anomalie (vol-gewichtet, drag-bereinigt)

**Hypothese:** Auf dem PIT-Union-Universum ist der mittlere woechentliche Rank-IC zwischen dem Vol-Rang (realisierte Wochenvol, MAX-Tagesrendite, 8-Wochen-Beta zu BTC) und der vol-gewichteten, um sigma_w^2/2 bereinigten Folgewochenrendite in W1 und W2 jeweils negativ und <= -IC_min der Variante.

**Ertragsquelle / Zahler:** Praemie gegen Lotterie-Nachfrage; Zahler: Kaeufer hochvolatiler Perps

```yaml
id: H-30
kohorte: A3 / F-XSEC1
klasse: W
capital_free: true
hypothese: "Auf dem PIT-Union-Universum ist der mittlere woechentliche Rank-IC zwischen dem Vol-Rang (realisierte Wochenvol, MAX-Tagesrendite, 8-Wochen-Beta zu BTC) und der vol-gewichteten, um sigma_w^2/2 bereinigten Folgewochenrendite in W1 und W2 jeweils negativ und <= -IC_min der Variante."
ertragsquelle: "Praemie gegen Lotterie-Nachfrage; Zahler: Kaeufer hochvolatiler Perps"
metric: "Mittel des woechentlichen Spearman-Rank-IC (Charakteristik_t vs. Folgewochenrendite_t+1, close_at_last), je Fenster"
varianten: [vol_rv, vol_max, vol_beta]
richtung: negativ
windows:
  - {id: W1, von: 2024-07-01, bis: 2025-06-30, wochen: 53, rolle: urteilstragend}
  - {id: W2, von: 2025-07-01, bis: 2026-06-30, wochen: 52, rolle: urteilstragend}
  - {id: L,  von: 2021-03-01, bis: 2024-06-30, wochen: 174, rolle: aera-profil, versiegelt: true}
fenster_regel: C10_hart
threshold:
  W1: {vol_rv: 0.01656, vol_max: 0.01656, vol_beta: 0.01656}
  W2: {vol_rv: 0.01445, vol_max: 0.01445, vol_beta: 0.01445}
  formel: "2.4865 * E_t[1/sqrt(K_t-1)] * max(1, c_rho) / sqrt(W)"
  ref: "state/runs/wp13a_20260922/wp13a_prelaunch.json#windows.<W>.noise_floor_and_threshold.ic_min_per_variant (sha256 194ead3a...); Pin: WP-13 T5 test_ic_min_pins_registered_values"
structural_null:
  komponenten: [permutation_within_week, persistence_ar1, vol_drag_analytisch, vol_geschichtete_permutation; Gate (5): Spearman(Vol-Rang, Turnover-Rang) < 0.60 je Woche im Median (Erreichbarkeit 0.16/0.14 geprueft)]
  permutation_floor: {W1: 0.04849, W2: 0.04190, ref: "wp13a_prelaunch.json#windows.<W>.noise_floor_and_threshold.floor.e_floor"}
  persistence_quantile_registered_direction: {W1: {vol_rv: -0.0112, vol_max: -0.0119, vol_beta: -0.0119}, W2: {vol_rv: -0.0105, vol_max: -0.0101, vol_beta: -0.0105}, ref: "wp13a_prelaunch.json#windows.<W>.noise_floor_and_threshold.persistence_null.variants"}
power:
  alpha: 0.05
  sided: one
  power: 0.80
  z: 2.4865
  cluster_unit: kalenderwoche
  n_eff: {W1: 53, W2: 52, rho_ref: "c_rho aus der Persistenz-Null je Variante (Tabelle oben), auf >= 1 gedeckelt; reale IC-Autokorrelation wird nach dem Lauf berichtet"}
  a_priori_effekt: 0.03
  a_priori_ref: "R2 0.3C [sek]"
  detectable_effect: {W1: {vol_rv: 0.01656, vol_max: 0.01656, vol_beta: 0.01656}, W2: {vol_rv: 0.01445, vol_max: 0.01445, vol_beta: 0.01445}}
  per_fenster_power_registrierter_test: {W1: 0.98, W2: 0.996}
  zuordnungsregel: "Per-Fenster-Power >= 0.60 -> C.10 hart; festgestellt vor dem Lauf"
  ref: "Zweitfassung, Abschnitt Fenster"
selection: {K: 7, ceiling_analytic: {W1: 0.00923, W2: 0.00790}, ceiling_measured: {W1: 0.00909, W2: 0.00809, n_replicates: 300, seed: 53}, ceiling_measured_ref: "wp13a_prelaunch.json#windows.<W>.selection_ceiling_measured", regel: "gemessene Decke >= IC_min -> GL-012-DROP vor dem Verdikt"}
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, ref: "PRD 4.1 sigma_xs_min invertiert; sigma_xs 1018 bp (wp7_20260914), 18 bp", label: "unter_wand nur Einzelposition"}
decision_relevance: {on_pass: "Tradability-Registrierung mit Dezil-Slippage (DEC-67 E4)", on_drop: "Klasse W im Wochenhorizont erschoepft"}
capital_tax_venue: {kapitalbasis: "n/a kapitalfrei", steuer: "n/a", venue_event: "n/a", zahler_post_2024: "Delisting-Hazard 2023/24 ~50 % (Etikett)"}
stress_episode: {liste_ref: "state/runs/stress_rel.json (sha256 6648a210c25fd3dd)", rolle: abdeckungsnachweis, n_tage: {W1: 22, W2: 8}}
irreversibility_probe: {ergebnis: nachladbar, ref: "V-1, WP-7, WP-12b"}
positive_control: {laufzeit_geschaetzt_h: 2, vorgeschaltet: true, ref: "10.000 Permutationen x 7 x 2 + Persistenz-Null"}
fixtures: {positive: "injizierter IC 0.06 + Beta + Sektoren", null_fixture: "Wochen-Permutation", adversarial: "Beta-korrelierte Charakteristik, vol_drag_analytisch, vol_geschichtete_permutation; Gate (5): Spearman(Vol-Rang, Turnover-Rang) < 0.60 je Woche im Median (Erreichbarkeit 0.16/0.14 geprueft)", alignment: "+1.000/-1.000", lag_profile: "-1..+2", delisting: "drop vs close_at_last", near_threshold: "Trefferquote 0.4-0.6"}
artifacts:
  cluster_series_ref: "WP-13 Lauf: ic_weekly_<variante>_<fenster>_<konvention>.csv + sha256"
  bootstrap_replicates_ref: "WP-13 Lauf: Seed 53 + Generator-Fingerprint, Permutations-/Persistenz-/Bootstrap-Replikate"
fdr_family: "F-XSEC1 (7, BH 0.10, Max-p ueber Fenster, >= 10000 Permutationen)"
over_family: "F-WEEK (Benjamini-Yekutieli am Wellenschluss; Verdikt bis dahin vorlaeufig)"
feasibility_verdict: bestanden
constants_hash: "n/a - kapitalfrei; tradability3 nicht gebaut"
data_fingerprints: ["union a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a", "delisting_dates 852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933", "prelaunch 194ead3a2ee8f13c90e3319cf30813099d748be483c65bbe2ba7599d8838a235", "Stichtage: Ueberlebende 2026-09-14, Register 2026-09-16"]
stats3_version: "wp13_xsec 94aa9e6 (Vorlauf); Lauf-Commit im GL-Eintrag"
bedingung_welle_1: [WP-7 B2, WP-12b, WP-13a]
```

---

## Rueckzug der Zweitfassung H-28/H-29/H-30 vom 2026-09-22 - append-only, kein Lauf erfolgt

**Datum:** 2026-09-22 (Orchestrator) nach dem zweiten adversarischen Opus-Review (`state/REVIEW_H28_H30_v2.md`, DEC-75). Die Zweitfassung bleibt stehen und ist **zurueckgezogen**; kein Treiber gegen sie gebaut, keine IC-Serie gelesen. Bindend fuer die Drittfassung: urteilstragende SE = max(Permutationsboden, SD der realen IC-Serie)/sqrt(W_geurteilt) mit Wochen-Block-Bootstrap (der Permutationsboden unterschaetzt die Querschnitts-Varianz bei heterogenem Beta um Faktor ~1,8); Decke und Permutations-p auf faktorerhaltender Null; Beta-Kontrolle (markt-residualisierter Outcome) als zusaetzliche PASS-Bedingung; H-30 Gewicht PIT (`vol_rv[t]`) und Drag-Definition eindeutig, Feasibility ueber rohen Dezil-Drag-Spread und Schaetzfehler; PRD-Kills (3)/(4) wieder aufgenommen mit Drawdown-Survivorship-Fixture; Gate (2)/(3) report-only (nachweislich nie bindend); vollstaendiger Gate-Text (1)-(7); T3/T4/T6; Deckelung `max(1, c_rho)` als Abweichung registriert und im Code; bias-korrigiertes rho; W = geurteilte Wochen 52/51. Unveraendert uebernehmbar: Fenster, K-Reihen, Boden 0,04849/0,04190, Delisting-Zaehlung 80/140, NO_HISTORY-Liste, Gate-(5)-Erreichbarkeit 0,159/0,142, Stress-Abdeckung, Seed 53, `close_at_last`, K = 7, Familienstruktur.

---

## H-28 / H-29 / H-30 - Drittfassung (2026-10-12): Kohorte F-XSEC1 (A3), Klasse W, kapitalfrei

**Registriert:** 2026-10-12 (Orchestrator).

**Herkunft:**
- Rueckzug der Zweitfassung (DEC-75), Herleitung `state/herleitung_h28_h30_v3/`, Entscheidungen DEC-86 Nachtrag,
  DEC-87, DEC-88 und DEC-89.
- Code fuer Positivkontrolle und Lauf: `849ec4a`. Der Vorlauf v5e lief auf `92607da`; die Vorlauf-Pipeline ist in
  `849ec4a` unveraendert: `prelaunch.py`, `nulls.py`, `characteristics.py` und `ic.py` sind ohne Diff. Geaendert sind
  `run.py`, `gates.py`, das neue `positive_control.py`, `scripts/wp13_xsec.py` und der Docstring von `__init__.py`.
- Vorlauf v5e `state/runs/wp13a_20261012_v5e/`:
  - `wp13a_prelaunch.json`, sha256 `94d655599b90a0841fef3e3a77404e12f216e2c7281e337208042c0a475ae3b2`;
  - `wp13a_prelaunch.md`, sha256 `dede4f050010fe773685b3f6af6f8b8a01781a50ec40f51f6920182f009bf4fb`.
- Der Vorlauf hat keine reale Signal-Outcome-Verknuepfung berechnet (Siegel-Tests
  `tests/unit/test_wp13_xsec.py::test_seal_*`).
- Das L-Fenster liegt versiegelt in `wp13a_prelaunch_L_window_sealed.json` (sha256
  `1d0b20bdf3c2043350ff92d78a027f29ac50dc6dba9833d5a52a910aa41b32a4`, nur aus `cloud_run.log` zitiert) und wird erst nach
  dem GL-Eintrag geoeffnet.

**Siegel und Aenderungsregel:** Keine IC-Serie wurde gelesen. Nichts in diesem Eintrag wird nach dem Lesen einer
IC-Serie geaendert; Aenderungen erfolgen nur als neuer Eintrag (append-only).

**Registrierungsdatei:** `scinance3-impl/state/registered/h28_h30_v3.yaml`, sha256
`bd948f34516bb444f152287863e6096da6faf82712b579c6dfa211599015c299`. Das ist der Wert fuer `--registered-sha256` bei
`--positive-control` und `--run`.
- `run.validate_registered(require_frozen_constants=True)` ist bestanden; das schliesst die DEC-89-Pflichtfelder ein.
- `run.check_data_fingerprints` gegen v5e ist bestanden.
- `run.resolve_rules` ergibt seed 53, n_reps 1.000, Bootstrap und Permutationen je 1.000, Persistenz 1.000,
  block_len 4, level 0,9936, bh_alpha 0,10 und bounce_spread 0,003621.

**Vorbedingungen V1-V9 der Herleitung:** erfuellt durch DEC-87 (Entscheidungen A-J, Bau `92607da`, Abnahme durch den
Orchestrator), DEC-88 (Vorlauf v5e, mechanische Power-Zuordnung) und DEC-89 (Positivkontrolle in
Produktionskonfiguration, gemessene Bounce-Parameter, Restabweichungen; Bau `849ec4a`).

**Fundstellen.** `[v5e <pfad>]` ist ein JSON-Pfad in `wp13a_prelaunch.json` v5e, `<W>` steht fuer W1 oder W2.
`[abg.]` ist aus v5e-Zahlen abgeleitet; der Rechenweg steht daneben.

---

### Gemeinsame Festlegungen der Kohorte (bindend fuer alle drei Hypothesen)

**Klasse und Selektion.**
- Klasse W, kapitalfrei. K = **7** Varianten (DEC-73 E1):
  - H-28: mom1, mom2, mom4 (positiv);
  - H-29: rev_gap (negativ);
  - H-30: vol_rv, vol_max, vol_beta (negativ).
- **K = 7 bleibt Nenner** in der Selektionsdecke (Mittel des Maximums ueber 7) und im BH-Nenner (fest 7; gesperrte
  Varianten gehen mit p = 1 ein), auch wenn nur zwei Varianten gerechnet werden (DEC-74 (e), DEC-87 (J), DEC-88).
- Jede Variante ist ein eigener Eintrag (`H-28_mom1` .. `H-30_vol_beta`). Eine Hypothese ist PASS, wenn mindestens
  eine ihrer Varianten PASS ist. Jede Variante wird einzeln berichtet (DEC-87 (J)).

**Mechanische Zuordnung (DEC-87 (F), DEC-88; IC_prior 0,03 [sek, R2 0.3C, PRD 5.3]).**

Formeln:
- P_ICmin = Phi(0,03 x 2,4865 / IC_min - 2,4865);
- P_beta = Phi((0,03 - max(IC_min, |q|)) / sd), mit q = bindendes Beta-Kontroll-Quantil und sd = SD des Mittel-IC der
  fm8-stress-Null in der bindenden Driftvariante [v5e `<W>.beta_control_recommended_high_rep.{stress, stress_drifting}.variants.<v>.mean_ic_draws_sd`];
- P_voll = min(P_ICmin, P_beta);
- MDE80 = max(1,3385 x IC_min, max(IC_min, |q|) + 0,8416 x sd).

Regeln:
- P_voll >= 0,80 in beiden Fenstern: C.10 hart.
- MDE80 > 0,03 in einem Fenster: GL-012-Feasibility-DROP der Variante vor dem Lauf (DEC-51 (2)), K bleibt 7.
- Der DEC-52-Zweig ist nicht gebaut und wird nicht genutzt.

| Eintrag | W1 P_voll / MDE80 | W2 P_voll / MDE80 | Status in der YAML | Grund |
|---|---|---|---|---|
| **H-28_mom1** | 0,832 / 0,0291 | 0,963 / 0,0233 | **gerechnet, C.10 hart** | - |
| H-28_mom2 | 0,597 / 0,0353 | 0,912 / 0,0264 | `gl012_pre_run` | MDE80 0,0353 > 0,03 in W1 (DEC-51 (2)) |
| H-28_mom4 | 0,380 / 0,0424 | 0,722 / 0,0321 | `gl012_pre_run` | MDE80 > 0,03 in W1 und W2 (DEC-51 (2)) |
| **H-29_rev_gap** | 0,949 / 0,0238 | 0,986 / 0,0210 | **gerechnet, C.10 hart** | DEC-52 nach DEC-75 (8) zulaessig (Power bei Prior 0,01: 0,148 / 0,194), festgestellt, nicht genutzt (DEC-87 (B)) |
| H-30_vol_rv | (0,946 / 0,0245) | (0,986 / 0,0216) | `gl012_pre_run` | H-30-Feasibility in Wocheneinheiten verfehlt: Spread(D10-D1)/Kante 2,764 > 0,5 (DEC-74 (h), DEC-87 (G)) |
| H-30_vol_max | (0,946 / 0,0245) | (0,986 / 0,0216) | `gl012_pre_run` | wie vol_rv |
| H-30_vol_beta | - | - | `gl012_pre_run` | strukturell durch die registrierte Beta-Kontrolle neutralisiert (C.4, DEC-87 (H)); dazu die H-30-Feasibility |

Fundstellen: DEC-88; [abg.] aus [v5e `<W>.noise_floor_and_threshold.ic_min_capped_per_variant`,
`<W>.frozen_null_constants.res_quantile_binding`] und den sd-Pfaden oben, mit identischem Ergebnis nachgerechnet.
Klammerwerte bei H-30 sind formal und ohne Bedeutung, weil die Feasibility vor der Power sperrt.

**Panel und Universum.**
- Union `panel_1d` (877 Ueberlebende) + `panel_1d_delisted` (261 delistet) = 1.138 Symbole, 2.085 Tage, 299 Wochen
  2020-12-28..2026-09-14, as_of 2026-09-28 (`cloud_run.log` v5e).
- Bezug: Harvest-Export `exports/scinance/scinance_panel_1d_2026-09-28.zip`, sha256
  `03dc0e7cfce96737c31cd6d59bce1767f1bb112a74ac539c2ed5b091c49b16cb`. Nur exakte Schluessel lesen, Groesse und SHA256
  pruefen, in ein frisches Sitzungsverzeichnis entpacken, nie ins Repo, nie unter `data/harvest`, Zugangsdaten nur aus
  `HARVEST_S3_*` (DEC-80, DEC-84).
- Daten-Fingerprints [v5e `data_fingerprints`], im Lauf geprueft, bei Abweichung KEIN VERDIKT:
  - union_range `a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a` (Jahre 2021-2026, 6.507 Partitionen,
    as_of 2026-09-28);
  - delisting_dates `852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933`.
- PIT-Maske DEC-72. Delisting-Datum = Announcement-Datum (Etikett, konservativ). `--allow-partial` (DEC-66).
- NO_HISTORY in den Fenstern: W1 LITUSDT, MONUSDT, DATAUSDT; W2 SPCXUSDT [v5e `no_history_symbols`]. Etikett
  "<= 1 % des Querschnitts fehlt".

**Cluster-Einheit und Metrik.**
- Cluster ist die Kalenderwoche (ISO). Die K_t lebenden Symbole einer Woche ergeben **einen** Spearman-Rank-IC (L-7).
  Wochen mit weniger als 10 gueltigen Symbolen fallen aus; ein degenerierter Querschnitt ergibt IC 0,0
  (`ic.weekly_ic_series`, `pit_universe.spearman_rank_ic`).
- Urteilstragend je Variante und Fenster ist das Mittel der Wochen-ICs ueber die geurteilten Wochen. Outcome ist die
  Folgewochen-Log-Rendite, nicht ueberlappend.
- Survivorship-Konvention `close_at_last` (urteilstragend): ein in t+1 delistetes Symbol geht mit Folgerendite 0 ein.
  Betroffene Symbol-Wochen W1 80, W2 140 [v5e `<W>.delisting.n_symbol_weeks_delisting`]. `drop` ist Pflicht-Sensitivitaet
  und wird nur berichtet.

**Fenster.**

| Fenster | Kalender | ISO-Wochen | W geurteilt | K min / Median / max | Symbol-Wochen | Rolle |
|---|---|---:|---:|---|---:|---|
| W1 | 2024-07-01..2025-06-30 | 53 | 52 | 345 / 419 / 514 | 22.300 | urteilstragend |
| W2 | 2025-07-01..2026-06-30 | 52 (2025-07-07..2026-06-29) | 51 | 514 / 589 / 603 | 29.126 | urteilstragend |
| L | 2021-03-01..2024-06-30 | 174 | - | versiegelt | - | Aera-Profil, versiegelt |

Fundstelle: [v5e `<W>.noise_floor_and_threshold.floor.{k_series, w_judged, weeks}`]; Symbol-Wochen [abg.] als Summe der
k_series. Die 11 Wochen 2026-07-01..2026-09-14 werden **nicht beurteilt und nach dem Verdikt nicht nachgereicht**.

**Charakteristiken.** Alle werden auf dem vollen Panel gebaut und danach auf die Fenster geschnitten (DEC-75 (8)).
- mom1/mom2/mom4: Summe der Wochen-Log-Renditen der Wochen t-n+1..t, n = 1/2/4.
- rev_gap: Wochen-Log-Rendite der Woche t-1; Woche t ist das Gap.
- vol_rv: SD der Tages-Log-Renditen der Woche t, in Tageseinheit.
- vol_max: groesste Tages-Log-Rendite der Woche t.
- vol_beta: OLS-Beta zu BTCUSDT ueber die Wochen t-7..t.

Code: `characteristics.*`.

**Beta-Kontrolle (DEC-86, bestaetigt in DEC-88).** `fm_neutral_8w` mit Beta-Fenster 8 Wochen:
- Fuer jede Outcome-Woche t+1 eine Querschnitts-OLS (Achsenabschnitt und Steigung) des Outcomes auf das PIT-Beta zu
  BTCUSDT.
- Das Beta wird ueber t-7..t aus `returns_est` geschaetzt (nicht handelnde Symbol-Wochen = NaN, DEC-85 (iii)) und
  braucht 8 gueltige Wochen. Gerechnet wird ueber die in t und t+1 lebenden Symbole, mindestens 5.
- Das Residuum ersetzt das Outcome, danach wird IC_res gebildet (`ic.apply_beta_control`, `ic.fm_neutralize_outcome`).
- Gewinner-Bestaetigung mit 1.000 Replikaten und je Fenster eigener Kalibrierung [v5e
  `beta_control_confirmation.attempts[0].windows.<W>.row`]:

| Fenster | measured Null-Mittel / Grenze | measured Decke / Grenze | stress Null-Mittel / Grenze | stress Decke / Grenze | Regel |
|---|---|---|---|---|---|
| W1 | 0,00072 / 0,00168 | 0,00757 / 0,01378 | **0,00165 / 0,00168** | 0,00834 / 0,01378 | PASS |
| W2 | 0,00022 / 0,00147 | 0,00637 / 0,01167 | 0,00084 / 0,00147 | 0,00685 / 0,01167 | PASS |

**Schwachstelle (festgehalten, keine Regelaenderung):** In W1 unter stress liegt das schlechteste Null-Mittel nur
0,11 SE unter der Grenze:
- mom4: 0,00165 gegen 0,00168; SE = 0,01061/sqrt(1.000) = 0,00034 [abg.; v5e `...cells.stress.variants.mom4.mean_ic_draws_sd`].
- Die vorab fixierte Regel (DEC-77 E1 (b), DEC-85 (iv)) ist erfuellt. Kein Neuziehen, kein Methodenwechsel (DEC-86, DEC-87 V1).
- Fuer die gerechneten Varianten ist der Rest-Mechanikterm klein: mom1 W1 stress +0,00076, rev_gap W1 +0,00114 (gegen
  die registrierte Richtung).
- Die Marge der Methode selbst ist in W1 aber nicht robust, und ein Seed-/MC-Wechsel koennte die Regel kippen. Eine
  Wiederholung mit anderem Seed ist NICHT registriert und wird nicht nachgereicht.

**Kalibrierung der Null je Fenster** (DEC-78 Nachtrag, DEC-81, DEC-85 (i)/(ii), DEC-87 (D)) [v5e
`<W>.beta_control_method_study.calibrations.<cal>`, `<W>.factor_calibration`]:

| Groesse | W1 | W2 |
|---|---:|---:|
| sigma_f (BTC-Wochen-SD) | 0,06685 | 0,05514 |
| sigma_e (idiosynkratisch, verwendet) | 0,12064 | 0,10729 |
| rho_f measured / stress | 0,04624 / 0,09248 | 0,04158 / 0,08317 |
| Faktoranteil measured / stress | 0,03211 / 0,06422 | 0,01389 / 0,02777 |
| beta_sd kalibriert measured / stress / zero | 0,57367 / 0,77067 / 0,57687 | 0,44648 / 0,58333 / 0,44648 |
| Gegenprobe z measured / stress / zero (alle ok, inkl. Marktspalten-Band) | 0,63 / 0,02 / 1,03 | 1,90 / 1,24 / 1,90 |

**Schwelle (DEC-74 (a)/(b), DEC-75 (8)).** `IC_min = 2,4865 x B_W x max(1, c_rho_bk) / sqrt(W)`.
- B_W = E_t[1/sqrt(K_t-1)] ueber die geurteilten Wochen, also die exakte Permutationsvarianz, signal-agnostisch:
  W1 0,04858, W2 0,04192.
- c_rho_bk ist bias-korrigiert (+1/W je Lag) aus der Persistenz-Null (AR(1) auf `returns_est`, 1.000 Simulationen,
  Seed 53) und auf >= 1 gedeckelt (registrierte Abweichung von DEC-74 (b)).
- Fundstelle: [v5e `<W>.noise_floor_and_threshold.{floor.e_floor, ic_min_capped_per_variant, ic_min_raw_per_variant,
  persistence_null.variants.<v>}`].

| Variante | IC_min W1 | IC_min W2 | c_rho_bk W1 / W2 | Persistenz-q in Richtung W1 / W2 (nur Bericht) |
|---|---:|---:|---|---|
| mom1 | **0,01966** | **0,01744** | 1,1739 / 1,1948 | -0,0064 / -0,0362 |
| mom2 | 0,01754 | 0,01558 | 1,0469 / 1,0677 | +0,0074 / -0,0094 |
| mom4 | 0,01729 | 0,01541 | 1,0325 / 1,0555 | +0,0081 / -0,0064 |
| rev_gap | **0,01727** | **0,01531** | 1,0309 / 1,0492 | +0,0063 / +0,0195 (q05) |
| vol_rv | 0,01694 | 0,01470 | 1,0110 / 1,0070 | -0,0112 / -0,0105 |
| vol_max | 0,01698 | 0,01464 | 1,0139 / 1,0028 | -0,0119 / -0,0101 |
| vol_beta | 0,01675 (roh 0,01657) | 0,01460 (roh 0,01354) | 0,9891 / 0,9276 (gedeckelt 1) | -0,0118 / -0,0105 |

**Beta-Kontroll-Quantil (DEC-76 (b), DEC-87 (E)).** Es gilt das 99,36-%-Quantil des Mittel-IC unter der fm8-Null mit
stress-Kalibrierung des Fensters, 1.000 Replikate, Seed 53. Es wird driftfrei und mit Drift 0,002/Woche gerechnet; bindend
ist das in Hypothesenrichtung extremere [v5e `<W>.frozen_null_constants.{res_quantile_driftfree, res_quantile_drifting,
res_quantile_binding}`].

| Variante | W1 driftfrei / drift / **bindend** | W2 driftfrei / drift / **bindend** |
|---|---|---|
| mom1 | +0,02244 / +0,02219 / **+0,02244** | +0,01700 / +0,01691 / **+0,01700** |
| mom2 | +0,02756 / +0,02780 / **+0,02780** | +0,02029 / +0,02043 / **+0,02043** |
| mom4 | +0,03243 / +0,03331 / **+0,03331** | +0,02490 / +0,02506 / **+0,02506** |
| rev_gap | -0,01666 / -0,01659 / **-0,01666** | -0,01546 / -0,01514 / **-0,01546** |
| vol_rv, vol_max | -0,01843 / -0,01748 / **-0,01843** | -0,01639 / -0,01609 / **-0,01639** |
| vol_beta | -0,00557 / -0,00559 / **-0,00559** | -0,00483 / -0,00486 / **-0,00486** |

In der Simulation sind vol_rv und vol_max identisch (Proxy |r|, Etikett).

Effektive Schwelle der gerechneten Varianten fuer IC_res = max(IC_min, |q|) [abg.]: mom1 W1 0,02244 / W2 0,01744;
rev_gap W1 0,01727 / W2 0,01546.

**Selektionsdecke, GL-012-bindend (DEC-87 (A)).** Mittel des Maximums ueber K = 7 der Methode fm_neutral_8w unter der
stress-Kalibrierung des Fensters, driftfrei, 1.000 Replikate, Seed 53 [v5e `<W>.frozen_null_constants.ceiling_method_stress`]:

| | W1 | W2 |
|---|---:|---:|
| **bindend** | **0,00834** | **0,00685** |
| min IC_min / Decke [abg.] | 2,01 | 2,13 |
| Bericht: Driftvariante | 0,00851 | 0,00696 |
| Bericht: analytisch 1,3868 x SE_W, ohne 1/sqrt(2) (DEC-87 (C)) [v5e `selection_ceiling_analytic.ceiling_ic_without_factor`] | 0,00934 | 0,00814 |
| Bericht: reines Rauschen, gemessen (300 Rep.) [v5e `selection_ceiling_measured`] | 0,00919 | 0,00778 |
| historisch, nicht bindend: TS-8w, rho_f 0,2 (v3) | 0,04963 | 0,04993 |

**Persistenz-Null (Gate (2), report-only, DEC-75 (6)).** Die Persistenz-Null bindet nie. Ihre Mittel liegen fuer mom1/2/4
negativ und fuer rev_gap positiv, also gegen die registrierten Richtungen (Tabelle oben).

**FDR (DEC-74 (e), DEC-75 (6), DEC-87 (J)).**
- Einheit ist die Variante.
- p = Block-Permutations-p: Outcome-Wochen in Bloecken der Laenge 4 permutiert, faktorerhaltend, 1.000, Seed 53.
  Massgeblich ist das schwaechere Fenster (Max-p).
- BH alpha 0,10 mit festem Nenner 7, report-only.
- Ueber-Familie F-WEEK: Benjamini-Yekutieli am Wellenschluss, bindend. Bis dahin traegt jedes PASS das Etikett
  "vorlaeufig bis F-WEEK geschlossen".

**Gate (5) Erreichbarkeit (nur Bericht, H-30 gesperrt):** Median Spearman(Rang der Charakteristik, Rang des
trailing-8-Wochen-Median-Turnovers):
- vol_rv 0,159 / 0,142;
- vol_max 0,150 / 0,104;
- vol_beta 0,154 / 0,050 (W1 / W2; L 0,115 / 0,113 / 0,068).

Alle Werte sind < 0,60 [v5e `<W>.gate5_reachability_by_variant.<v>.median`].

**H-30-Feasibility (DEC-87 (G)), Wocheneinheit sigma_w = sqrt(n_t) x vol_rv:**
- Kante 91,42 bp/Woche;
- Spread(D10-D1)/Kante **2,764** > 0,5;
- SE(sigma_w^2/2)/Kante 0,175;
- n_t Median 7,0.

Fundstelle: [v5e `h30_feasibility_weekly_units`]. Folge: **GL-012 fuer H-30 vor dem Lauf** (DEC-74 (h)), K bleibt 7.

**Oekonomisches Etikett (C.2, kein Gate).**
- Portfolio IC 0,0101 (f 3,51, sigma_xs 1.018 bp, 18 bp), Einzelposition 0,062 (DEC-74 (k)). IC_prior 0,03 liegt unter
  0,062: `unter_wand` nur im Einzelpositionsrahmen.
- Kostenbasen 18 bp (A3-M), 30 bp (A3-R), 4,5-7,5 bp (A3-V). Die Taker-Wand 11 bp ist getrennt (B4 nicht ausgeloest).

**Stress-Abdeckung (DEC-56 (1), Nachweis, kein Filter):**
- STRESS_REL (`state/runs/stress_rel.json`, sha256 `6648a210c25fd3dd2f1e94d645fc4045bfcd99e3ea7ec8767d5c18edc45cb69e`,
  Kanon `eb83fe402b7b87243b1fc93691079a073461a42b6c17341502bc8c83678ca667`): W1 22 Tage, W2 8 Tage.
- STRESS_ABS (`state/runs/stress_abs.json`, `b8008257e963eaa2bd81882d1169503ca8f4c38d7860d65c357b8db3308fc11e`): W1 2 Tage
  (2024-08-05, 2025-02-03), W2 1 Tag (2025-10-10).

Fundstelle: [v5e `<W>.stress_rel`, `<W>.stress_abs`].

**Survivorship-Fixture (Etikett, DEC-76, DEC-89 E3 (2); synthetisch, Drawdown -40 %/8 Wochen, 30 % geloescht)**
[v5e `<W>.survivorship_fixture`; registriert als `windows.<W>.survivorship`]:

| | W1 (19 von 419 geloescht) | W2 (46 von 589 geloescht) |
|---|---:|---:|
| mom1 (IC_min-Einheiten; "Beobachtung verworfen" minus "zum letzten Schlusskurs geschlossen") | -0,198 | -0,438 |
| rev_gap | -0,189 | **-0,579** |

rev_gap W2 liegt bei >= 0,5 IC_min: Ein unkontrolliertes Panel waere in Hypothesenrichtung verzerrt. Der Lauf nutzt das
kontrollierte Union-Panel. Der Lauf setzt das Etikett aus der YAML an `H-28_mom1` und `H-29_rev_gap`; es ist report-only
und nie ein Kill.

**Bounce-Fixture-Parameter (DEC-89 E1, gemessen, in der YAML registriert, vom Lauf gelesen).**

`rules.bounce_spread` = **0,003621**:
- Wert: Median-Perp-Spread des illiquidesten Dezils D10 = 36,21 bp / 1e4. D10 ist die strengste Wahl, weil sie den
  groessten Bounce erzeugt.
- Quelle: WP-7-Spread-Zensus `state/runs/wp7_20260921/spread_census.json`, sha256
  `fa1546be8216564005b21827190549b44edf8f5353602e5173b5d4f6497e7083`, Pfad `deciles[decile=10].perp_spread_bp_median`
  (886 Symbole gerankt, D10 89 Symbole).
- Etikett: Die Datei nennt als Quelle "REST-Fallback (bybit_rest.fetch_tickers, ein Call; Inhaltsprobe fehlgeschlagen)".
  Der Wert ist also eine Momentaufnahme vom 2026-09-21, kein Mittel ueber W1/W2.

`windows.<W>.bounce_sigma_true` = W1 **0,17186**, W2 **0,13311**:
- Wert: gemessene Median-Wochen-Vol der Symbole des Fensters.
- Quelle: [v5e `<W>.factor_preserving_null.driftfree.sigma_e_median_symbol_weekly`].

Seed `rules.seed` = 53. Im Ein-Wochen-Gap ist der Bounce-IC konstruktionsbedingt ~0: Formation und Outcome teilen keinen
Schlusskurs. Die Parameter tragen das Ergebnis kaum, sind aber belegt (Arbeitsregel 4).

---

### Gate-Text (1)-(7), wie ihn Code `849ec4a` auswertet (`gates.evaluate`, `run.run_full`/`run.evaluate_entry`, `scripts/wp13_xsec.py cmd_run`)

**Abbrueche vor jedem Verdikt (rc = 1, KEIN VERDIKT fuer keine Hypothese, C.14), in dieser Reihenfolge:**

- (P0) **Startsperre:** sha256 der `--registered`-Datei = `--registered-sha256`, sonst kein Lauf.
- (P1) **Schema** (`validate_registered(require_frozen_constants=True)`, vor dem Laden des Panels). Abgewiesen wird:
  - ein globaler `calibration`-Block oder der Altschluessel `ceiling_driftfree_res`;
  - eine fehlende `windows.<W>.calibration.stress`;
  - eine unbekannte Variante, Richtung oder ein unbekannter Status;
  - ein `gl012_pre_run` ohne `reason`;
  - H-30 ohne `outcome: vol_weighted`;
  - eine doppelt registrierte Variante;
  - eine fehlende eingefrorene Konstante (`ceiling_method_stress`, `res_quantile_driftfree`, `res_quantile_drifting`
    fuer alle 7 Varianten);
  - DEC-89: ein fehlendes oder ungueltiges `rules.bounce_spread`, `rules.block_len`, `rules.level`,
    `windows.<W>.bounce_sigma_true`, `windows.<W>.w_judged` oder `windows.<W>.survivorship.{mom1,rev_gap}_diff_in_ic_min_units`.
- (P2) **beta_control:** Methode gesetzt und bekannt, `beta_window_weeks` = 8 passend zu `fm_neutral_8w`.
- (P3) **Daten-Fingerprints:** union_range und delisting_dates des geladenen Panels = YAML.
- (P4) **T5-Pins** (`resolve_rules`, `registered_window_constants`, `ConstantPinError`):
  - `rules.block_len` = 4 (`nulls.BLOCK_SIZE_WEEKS`);
  - `rules.level` = 0,9936 (`nulls.SELECTION_CEILING_ONE_SIDED_QUANTILE`);
  - `windows.<W>.w_judged` = W_judged des geladenen Fensters (52/51).
  - Jede Abweichung ist ein Abbruch. Die gepinnten YAML-Werte werden danach verwendet.
- (P5) **`returns_valid`** muss vorhanden sein.
- (P6) **Null-Nachrechnung je Fenster** (`nulls.run_configuration_null`): registrierte Methode, Fenster-`calibration.stress`
  direkt gelesen, Seed 53, `rules.n_reps` = 1.000, Niveau `rules.level`, driftfrei UND Drift 0,002.
  - `ceiling_method_stress` und beide Quantilmengen aller **7** Varianten (auch der gesperrten) muessen je innerhalb
    +-10 % der eingefrorenen Werte liegen; ist der eingefrorene Wert 0, gilt eine absolute Toleranz von 1e-4.
  - Bei identischem Panel, as_of, Jahren und Code ist die Nachrechnung deterministisch gleich.
  - Geurteilt wird immer gegen die eingefrorenen Werte.
- (P7) **DEC-53-Artefakte** werden VOR jedem Verdikt geschrieben und per Round-Trip verifiziert
  (`write_run_artifacts`/`verify_run_artifacts`). Fehlt etwas oder weicht ab, wird KEIN Verdikt geschrieben.

**Gesperrte Eintraege** (`status: gl012_pre_run`: mom2, mom4, vol_rv, vol_max, vol_beta):
- Sie werden nicht gerechnet: keine Gate-Payload, kein Verdikt-IC. Ausnahme (Etikett C.17): die DEC-75-(3)-Kalibrierung
  berichtet den realen Mittel-IC der Beta-Charakteristik gegen die rohe Folgerendite (`beta_calibration_mean_ic`), dazu
  das Lag-Profil (rev_gap Lag -1 = Reversal ohne Gap). Jede kuenftige Beta-/A3-V- oder Ein-Tages-Gap-Registrierung auf
  diesem Panel muss diese Zahlen als gesehen offenlegen.
- Verdikt DROP mit dem Etikett "GL-012 vorab (gesperrt, nicht gerechnet, p=1 im BH-Nenner 7): <reason>".

**Gerechnete Eintraege (H-28_mom1, H-29_rev_gap): Verdikt je Variante.** Zuerst die Vor-Verdikt-Pruefung:

**(GL-012)** Ist `ceiling_method_stress_W` >= IC_min(v, W) in einem Fenster, folgt DROP mit Etikett GL-012, vor jeder
PASS-Logik. Stand: 0,00834 < 0,01966/0,01727 (W1) und 0,00685 < 0,01744/0,01531 (W2), also kein Kill.

Danach gilt **PASS genau dann, wenn in W1 UND W2 jeweils (1a)-(1d), (3b-i)-(3b-iii) und, falls anwendbar, (5) erfuellt
sind UND fuer H-29 kein Bounce-Kill (4b) vorliegt.** Sonst DROP mit Etikett.

**(1) Roher Mittel-IC je Fenster (C.10 hart):**
- (1a) Vorzeichen: IC_W > 0 (H-28, positiv) bzw. IC_W < 0 (H-29, negativ). Ein IC von NaN verfehlt die Bedingung.
- (1b) |IC_W| >= 2,4865 x SE_W mit SE_W = max(B_W, SD(IC_t,W)) / sqrt(W_W).
  - SD ist die Stichproben-SD (ddof 1) der endlichen Wochen-ICs.
  - B_W = E_t[1/sqrt(K_t-1)] der realen K_t-Reihe des Fensters; bei bestandenem Fingerprint W1 0,04858, W2 0,04192.
  - W_W ist das registrierte `w_judged` (52/51), gepinnt nach P4.
  - Ist SE NaN oder 0, ist (1b) nicht erfuellt.
- (1c) Die der Richtung zugewandte Grenze des einseitigen Moving-Block-Bootstrap-Intervalls liegt jenseits 0.
  - Block `rules.block_len` = 4 Wochen, 1.000 Ziehungen, Seed 53, Perzentilmethode, Niveau `rules.level` = 0,9936.
  - Bei positiver Richtung ist das Quantil 0,0064 der Bootstrap-Mittel massgeblich (> 0 verlangt), bei negativer das
    Quantil 0,9936 (< 0 verlangt).
- (1d) |IC_W| >= IC_min_capped(v, W) aus der YAML (Tabelle oben).

**(2) Querschnitts-Permutations-Null und Persistenz-Null:**
- Die Permutations-Null steckt als Boden B_W in (1b).
- Report-only, nur als Etikett:
  - das Block-Permutations-p (Block 4, 1.000, Seed 53, Max-p);
  - die Persistenz-Null (AR(1) auf `returns_est`, **1.000** Simulationen, **beide Fenster**). Je Fenster wird der rohe
    Mittel-IC mit dem 95-%-Quantil in Richtung verglichen; "bestanden" gilt nur, wenn beide Fenster bestehen.
  - Ist eine dieser Komponenten "nicht bestanden", gibt es ein Etikett, nie eine Verdiktaenderung.

**(3) FDR:**
- BH alpha 0,10 ueber die festen 7 Varianten; gesperrte und NaN-Varianten gehen mit p = 1 ein. Report-only, nur Etikett.
- Bindend ist BY ueber F-WEEK am Wellenschluss. Das ist nicht Teil des Lauf-Codes.
- Ein Hypothesen-PASS traegt im Lauf-Bericht das Etikett "vorlaeufig bis F-WEEK geschlossen (DEC-74 (e))".

**(3b) Beta-Kontrolle je Fenster** (zusaetzliche PASS-Bedingung). IC_res,W ist der Mittel-IC der Charakteristik gegen das
`fm_neutral_8w`-neutralisierte Outcome. Es muss gelten:
- (3b-i) gleiches Vorzeichen wie registriert;
- (3b-ii) |IC_res,W| >= IC_min_capped(v, W);
- (3b-iii) IC_res,W > q_bindend(v, W) (positiv) bzw. < q_bindend(v, W) (negativ). Dabei ist q_bindend das in Richtung
  extremere der beiden eingefrorenen Quantile (Tabelle oben). Ein Quantil ohne IC_res gilt als nicht bestanden.
- Der IC der reinen Beta-Charakteristik (`vol_beta`) wird je Fenster nur berichtet.

**(4) Nur H-29:**
- (4a) Gap-Design eine Woche: registrierte Abweichung von PRD 5.3 (Lag-2-Reversal; das PRD-Ein-Tages-Design ist nicht
  getestet, DEC-87 (B)).
- (4b) **Bounce-Kill je Fenster:** Ist |IC_bounce,W| >= |IC_W| in irgendeinem Fenster, gibt es KEIN PASS; Verdikt DROP,
  Etikett "Artefakt Bounce" (DEC-75 (5), DEC-87 (I)).
  - IC_bounce,W ist der rev_gap-Mittel-IC auf einem synthetischen Panel mit der Wochenzahl des Fensters und max(Median
    K_t, 10) Symbolen (`run.bounce_fixture_ic`).
  - Wahrer Preis: Random Walk ohne Reversion mit Wochen-SD `bounce_sigma_true` (W1 0,17186, W2 0,13311). Der Schlusskurs
    liegt je Woche zufaellig auf Bid oder Ask, Versatz +- halber Spread; Spread `rules.bounce_spread` = 0,003621.
    Seed 53.
  - Es gibt keine Code-Defaults; ein fehlender Parameter fuehrt zum Abbruch.
  - Die Pruefung greift nur, wenn beide Werte endlich sind.
- (4c) **Liquiditaets-Etikett je Fenster:** IC_ohne_D1,W ist der Mittel-IC ohne das unterste Dezil des
  trailing-8-Wochen-Median-Turnovers (PIT). Ist IC_ohne_D1,W > -0,5 x IC_min(rev_gap, W) in mindestens einem Fenster,
  gibt es das Etikett "Illiquiditaets-Artefakt (H-16-Muster)"; das Verdikt steht, die Lesart ist eingeschraenkt.

**Survivorship-Etikett:** Die registrierten Werte `windows.<W>.survivorship` werden an `H-28_mom1` (mom1-Wert) und
`H-29_rev_gap` (rev_gap-Wert) als Etikett gehaengt. Report-only, nie ein Gate-Input, das Verdikt bleibt unveraendert.

**(5) Nur H-30 (alle Eintraege gesperrt, im Lauf nicht ausgewertet):** Ein Fenster besteht nur, wenn der Median von
Spearman(Charakteristik-Rang, Turnover-Rang) < 0,60 ist (vorzeichenbehaftet; NaN verfehlt).

**(6) DEC-53:** P7 oben. Ohne vollstaendige, reproduzierende Artefakte gibt es KEIN VERDIKT. Neben dem Haupt-JSON
schreibt der Lauf `wp13_run.md`.

**(7) Adversariales Beta-Fixture:** Das Gate faellt darauf durch. Das wird vor dem Lauf als T1-Test geprueft
(`test_dec87_t1_fm8_adversarial_beta_fixture_drops_where_the_raw_gate_would_fire`); es ist keine Laufzeitgroesse.
Die Negativkontrolle der Positivkontrolle ist eine signalfreie Kontrolle in der kalibrierten stress-Null (driftfrei),
NICHT das adversariale Fixture nach DEC-75 (3) - sie belegt Gate (7) nicht.

**Verdikt je Hypothese** (`run.aggregate_hypotheses`):
- H-28 ist PASS, wenn H-28_mom1 PASS ist (mom2 und mom4 gesperrt).
- H-29 ist PASS, wenn H-29_rev_gap PASS ist.
- H-30: Alle Varianten sind gesperrt, das Verdikt lautet **"GL-012 vor dem Lauf"** mit den registrierten Gruenden
  (Feasibility-DROP, kein Verdikt ueber die Vol-Anomalie selbst).

---

### Abweichungen Code/Text (Code `849ec4a` gegen diesen Text bzw. PRD/DEC; nicht geglaettet)

**Erledigt** (bei `92607da` gemeldet, in `849ec4a` behoben, DEC-89):
- Positivkontrolle in Produktionskonfiguration;
- Survivorship-Etikett im Lauf;
- GL-012 auf Hypothesenebene;
- Persistenz-Null in beiden Fenstern mit 1.000 Simulationen;
- `w_judged`/`block_len`/`level` gelesen und gepinnt;
- Bounce-Parameter gemessen und registriert.

**Verbleibend:** keine. Die bei `849ec4a` noch gemeldete Abweichung (Positivkontrolle in einer schwaecheren
Faktorwelt als die kalibrierte stress-Null: sigma_e aus der Bounce-Vol, sigma_f aus dem Ziel-Anteil) ist in
`849ec4a` behoben (DEC-89 E2 Nachtrag): die Kontrollwelt nutzt `windows.<W>.null_scales` = gemessenes sigma_f
(0,06685/0,05514) und idiosynkratisches sigma_e_used (0,12064/0,10729) mit der stress-Kalibrierung (rho_f
0,09248/0,08317, beta_sd 0,77067/0,58333) - exakt die Welt, in der die Quantile eingefroren wurden.

**Hinweis, keine Abweichung:** Die Positivkontrolle rechnet die report-only-Nullen nicht (Block-Permutations-p, BH,
Persistenz-Null) und nutzt die eingefrorenen Konstanten statt einer Null-Neuberechnung. Beides ist im Modul dokumentiert
und betrifft keinen Gate-Input.

---

### H-28 - A3-M Querschnitts-Momentum

**Hypothese:** Auf dem PIT-Union-Universum der Bybit-USDT-Perps gilt fuer mindestens eine Formationslaenge (1, 2 oder
4 Wochen) in W1 und W2 jeweils:
- der mittlere woechentliche Spearman-Rank-IC zwischen Formationsrendite (bis Woche t) und Folgewochenrendite (t+1) ist
  positiv und >= IC_min der Variante;
- gegen das `fm_neutral_8w`-neutralisierte Outcome ist er ebenfalls positiv, >= IC_min und liegt ueber dem bindenden
  Null-Quantil.

Gerechnet wird nur mom1; mom2 und mom4 sind vorab GL-012 (DEC-88).

**Ertragsquelle / Zahler:** Prognose; Zahler sind spaet einsteigende Momentum-Chaser und Halter, die aus
Verlustpositionen getrieben werden.

```yaml
id: H-28
kohorte: A3 / F-XSEC1
klasse: W
capital_free: true
hypothese: "Mindestens eine Formationslaenge (1/2/4 Wochen): mittlerer woechentlicher Rank-IC (Formationsrendite_t vs. Folgewochenrendite_t+1) in W1 und W2 positiv und >= IC_min, roh UND nach fm_neutral_8w-Neutralisierung (dort zusaetzlich > bindendes Null-Quantil)."
ertragsquelle: "Prognose; Zahler: spaet einsteigende Momentum-Chaser, aus Verlustpositionen getriebene Halter"
metric: "Mittel des woechentlichen Spearman-Rank-IC (Charakteristik_t vs. Folgewochen-Log-Rendite_t+1, close_at_last, min 10 Symbole) ueber die geurteilten Wochen je Fenster"
varianten: {mom1: gerechnet, mom2: "gl012_pre_run (MDE80 0.0353 > 0.03 in W1, P_voll 0.597)", mom4: "gl012_pre_run (MDE80 0.0424/0.0321 > 0.03, P_voll 0.380/0.722)"}
charakteristik: "Summe der Wochen-Log-Renditen t-n+1..t, n = 1/2/4 (characteristics.momentum_characteristic)"
richtung: positiv
windows:
  - {id: W1, von: 2024-07-01, bis: 2025-06-30, wochen: 53, geurteilt: 52, rolle: urteilstragend}
  - {id: W2, von: 2025-07-01, bis: 2026-06-30, wochen: 52, geurteilt: 51, rolle: urteilstragend}
  - {id: L,  von: 2021-03-01, bis: 2024-06-30, wochen: 174, rolle: aera-profil, versiegelt: true}
fenster_regel: C10_hart
threshold:
  W1: {mom1: 0.01966, mom2: 0.01754, mom4: 0.01729}
  W2: {mom1: 0.01744, mom2: 0.01558, mom4: 0.01541}
  formel: "2.4865 * E_t[1/sqrt(K_t-1)] * max(1, c_rho_bk) / sqrt(W_geurteilt)"
  ref: "v5e windows.<W>.noise_floor_and_threshold.ic_min_capped_per_variant (sha256 94d655599b90a0841fef3e3a77404e12f216e2c7281e337208042c0a475ae3b2); Pin tests/unit/test_wp13_run.py::test_dec87_t5_constants_pin_the_yaml_values_flow_into_every_payload"
structural_null:
  komponenten: [permutationsboden_SE_untergrenze, beta_kontrolle_fm_neutral_8w_PASS, selektionsdecke_GL012, block_permutation_p_report_only, persistenz_ar1_report_only]
  permutation_floor: {W1: 0.04858, W2: 0.04192, ref: "v5e windows.<W>.noise_floor_and_threshold.floor.e_floor"}
  beta_control_quantile_binding: {W1: {mom1: 0.02244, mom2: 0.02780, mom4: 0.03331}, W2: {mom1: 0.01700, mom2: 0.02043, mom4: 0.02506}, ref: "v5e windows.<W>.frozen_null_constants.res_quantile_binding"}
  persistence_q95_report_only: {W1: {mom1: -0.0064, mom2: 0.0074, mom4: 0.0081}, W2: {mom1: -0.0362, mom2: -0.0094, mom4: -0.0064}}
power:
  alpha: 0.05
  sided: one
  power: 0.80
  z: 2.4865
  cluster_unit: kalenderwoche
  n_eff: {W1: 52, W2: 51, rho_ref: "c_rho_bk aus der Persistenz-Null (+1/W je Lag, gedeckelt >= 1): mom1 1.1739 / 1.1948"}
  a_priori_effekt: 0.03
  a_priori_ref: "R2 0.3C [sek], PRD 5.3"
  detectable_effect_mde80: {W1: {mom1: 0.0291, mom2: 0.0353, mom4: 0.0424}, W2: {mom1: 0.0233, mom2: 0.0264, mom4: 0.0321}}
  per_fenster_power_voll: {W1: {mom1: 0.832, mom2: 0.597, mom4: 0.380}, W2: {mom1: 0.963, mom2: 0.912, mom4: 0.722}}
  zuordnungsregel: "DEC-87 (F): P_voll >= 0.80 beide Fenster -> C.10 hart; MDE80 > 0.03 -> GL-012 (DEC-51 (2)); festgestellt vor der Registrierung (DEC-88)"
  ref: "DEC-88"
selection: {K: 7, ceiling_binding: {W1: 0.00834, W2: 0.00685}, schaetzer: "Mittel des Maximums ueber 7, fm_neutral_8w, stress, driftfrei, 1000 Rep., Seed 53", ref: "v5e windows.<W>.frozen_null_constants.ceiling_method_stress", ceiling_analytic: {W1: 0.00934, W2: 0.00814}, ceiling_noise_measured: {W1: 0.00919, W2: 0.00778}, regel: "Decke >= IC_min -> GL-012 vor dem Verdikt"}
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, kosten_bp_woche: 18, ref: "DEC-74 (k)", label: "unter_wand nur Einzelposition"}
decision_relevance: {on_pass: "getrennte Tradability-Registrierung mit gemessener Dezil-Slippage (DEC-67 E4); kein Kapitalpfad vor tradability3; vorlaeufig bis F-WEEK", on_drop: "A3-M (mom1) auf Bybit-Perps im Wochenhorizont widerlegt; mom2/mom4 ohne Verdikt (GL-012, unterpowert)"}
capital_tax_venue: {kapitalbasis: "n/a kapitalfrei", steuer: "n/a", venue_event: "n/a", zahler_post_2024: "Delisting-Hazard 2023/24 ~50 % (Etikett)"}
stress_episode: {liste_ref: "state/runs/stress_rel.json sha256 6648a210c25fd3dd2f1e94d645fc4045bfcd99e3ea7ec8767d5c18edc45cb69e", rolle: abdeckungsnachweis, n_tage: {W1: 22, W2: 8}, stress_abs: {W1: 2, W2: 1}}
irreversibility_probe: {ergebnis: nachladbar, ref: "Bybit v5 oeffentlich; Harvest-Export (DEC-84)"}
positive_control: {laufzeit_geschaetzt_h: "Lauf UNBELEGT (> 1 vermutet: ~2 h Null-Nachrechnung); Positivkontrolle ohne Null-Neuberechnung", vorgeschaltet: true, modus: "scripts/wp13_xsec.py --positive-control (Code 849ec4a)", kriterium: "DEC-89 E2: H-28_mom1 und H-29_rev_gap PASS in Seeds 53, 54, 55 UND Negativkontrolle (IC 0) in keinem Seed PASS; rc 0 nur bei BESTANDEN", ref: "Abschnitt Lauf, Schritt 1"}
fixtures: {positive: "Produktionskonfiguration --positive-control (DEC-89 E2); Unit: test_dec89_pc_passes_on_a_production_shaped_fixture_panel, test_dec87_prd_positive_fixture_passes_end_to_end_through_run_full, test_dec87_t1_fm8_positive_fixture_passes", negative: "Negativkontrolle der Positivkontrolle (IC 0, Seeds 53/54/55)", null: test_dec87_t1_fm8_null_fixture_drops, adversarial: test_dec87_t1_fm8_adversarial_beta_fixture_drops_where_the_raw_gate_would_fire, alignment: test_alignment_fixture_perfect_and_mirrored_ic, lag_profile: test_lag_profile_only_lag_plus1_shows_the_effect, delisting: test_delisting_fixture_conventions_agree_on_signal_free_panel, near_threshold: test_near_threshold_hit_rate_about_half}
artifacts:
  cluster_series_ref: "state/runs/wp13_run_<datum>/wp13_run_H-28_mom1_<W>_ic_weekly.csv und ..._ic_weekly_residualized.csv, je sha256"
  bootstrap_replicates_ref: "wp13_run_fingerprint.json (Seed 53, Bit-Generator, Code-Hash + Commit, sha256 der Bootstrap-Mittel und Permutationsziehungen, result_sha256)"
fdr_family: "F-XSEC1 (K = 7, BH 0.10 report-only, Nenner fest 7, Max-p, Block-Permutation 1000)"
over_family: "F-WEEK (Benjamini-Yekutieli am Wellenschluss, bindend)"
feasibility_verdict: "bestanden fuer mom1; mom2, mom4 GL-012 vorab (DEC-88)"
constants_hash: "n/a - kapitalfrei; tradability3 nicht gebaut"
data_fingerprints: ["panel_export 03dc0e7cfce96737c31cd6d59bce1767f1bb112a74ac539c2ed5b091c49b16cb", "union_range a7e4dec7cb7475426f477c6d17359007b75026b2f8562b29e66457fed027793a", "delisting_dates 852bf75332fd1990b13b9a059fd871a75d7f71757b48e2bf102bc1f25c412933", "prelaunch_v5e 94d655599b90a0841fef3e3a77404e12f216e2c7281e337208042c0a475ae3b2", "registered_yaml bd948f34516bb444f152287863e6096da6faf82712b579c6dfa211599015c299", "spread_census fa1546be8216564005b21827190549b44edf8f5353602e5173b5d4f6497e7083", "as_of 2026-09-28"]
stats3_version: "wp13_xsec 849ec4a (Lauf, Positivkontrolle); Vorlauf v5e 92607da"
bedingung_welle_1: [WP-7 B2, WP-12b, WP-13a v5d, WP-13a v5e]
```

### H-29 - A3-R Kurzfrist-Reversal im Gap-Design (Lag 2)

**Hypothese:** Auf dem PIT-Union-Universum ist der mittlere woechentliche Spearman-Rank-IC zwischen der Rendite der
Woche t-1 (Woche t ist das Gap) und der Folgewochenrendite t+1 in W1 und W2 jeweils:
- negativ und <= -IC_min;
- auch gegen das `fm_neutral_8w`-neutralisierte Outcome negativ, <= -IC_min und unter dem bindenden Null-Quantil;
- und vom Bounce-Fixture in keinem Fenster erklaert.

**Ertragsquelle / Zahler:** Praemie fuer Liquiditaetsbereitstellung; Zahler sind durchgedrueckter Fluss und liquidierte
gehebelte Halter.

```yaml
id: H-29
kohorte: A3 / F-XSEC1
klasse: W
capital_free: true
hypothese: "Mittlerer woechentlicher Rank-IC (Rendite der Woche t-1, Gap Woche t, vs. Folgewochenrendite_t+1) in W1 und W2 negativ und <= -IC_min, roh UND nach fm_neutral_8w-Neutralisierung (dort zusaetzlich < bindendes Null-Quantil); |IC_bounce,W| < |IC_W| in beiden Fenstern."
ertragsquelle: "Praemie Liquiditaetsbereitstellung; Zahler: durchgedrueckter Fluss, liquidierte gehebelte Halter"
metric: "wie H-28"
varianten: {rev_gap: gerechnet}
charakteristik: "Wochen-Log-Rendite der Woche t-1; Woche t ist Gap (characteristics.reversal_gap_characteristic)"
richtung: negativ
windows: "wie H-28"
fenster_regel: "C10_hart (P_voll 0.949/0.986); DEC-52 nach DEC-75 (8) zulaessig (Power bei Prior 0.01: 0.148/0.194), festgestellt, nicht genutzt (DEC-87 (B))"
threshold:
  W1: {rev_gap: 0.01727}
  W2: {rev_gap: 0.01531}
  formel: "wie H-28"
  ref: "v5e windows.<W>.noise_floor_and_threshold.ic_min_capped_per_variant"
structural_null:
  komponenten: [permutationsboden_SE_untergrenze, beta_kontrolle_fm_neutral_8w_PASS, selektionsdecke_GL012, bounce_kill_je_fenster, liquiditaets_etikett_je_fenster, block_permutation_p_report_only, persistenz_ar1_report_only]
  permutation_floor: {W1: 0.04858, W2: 0.04192}
  beta_control_quantile_binding: {W1: {rev_gap: -0.01666}, W2: {rev_gap: -0.01546}, ref: "v5e windows.<W>.frozen_null_constants.res_quantile_binding"}
  persistence_q05_report_only: {W1: {rev_gap: 0.0063}, W2: {rev_gap: 0.0195}}
  bounce: {regel: "|IC_bounce,W| >= |IC_W| in einem Fenster -> kein PASS (DEC-75 (5), DEC-87 (I))", fixture: "run.bounce_fixture_ic: Wochen des Fensters x max(Median K_t, 10) Symbole, Seed 53", spread: {wert: 0.003621, ref: "rules.bounce_spread; state/runs/wp7_20260921/spread_census.json deciles[10].perp_spread_bp_median 36.21 bp (sha256 fa1546be8216564005b21827190549b44edf8f5353602e5173b5d4f6497e7083), DEC-89 E1"}, sigma_true: {W1: 0.17186, W2: 0.13311, ref: "windows.<W>.bounce_sigma_true; v5e windows.<W>.factor_preserving_null.driftfree.sigma_e_median_symbol_weekly, DEC-89 E1"}, struktur: "Gap eine Woche -> kein gemeinsamer Schlusskurs, IC_bounce ~ 0"}
  liquiditaet: {regel: "IC_ohne_D1,W > -0.5 * IC_min(W) in mindestens einem Fenster -> Etikett Illiquiditaets-Artefakt, Verdikt steht", d1: "unterstes Dezil trailing-8-Wochen-Median-Turnover, PIT"}
power:
  alpha: 0.05
  sided: one
  power: 0.80
  z: 2.4865
  cluster_unit: kalenderwoche
  n_eff: {W1: 52, W2: 51, rho_ref: "c_rho_bk 1.0309 / 1.0492"}
  a_priori_effekt: 0.03
  a_priori_ref: "aus dem Ein-Tages-Design uebernommen (DEC-75 (8)); fuer Lag 2 UNBELEGT (Review v2 W-14) - Etikett"
  detectable_effect_mde80: {W1: 0.0238, W2: 0.0210}
  per_fenster_power_voll: {W1: 0.949, W2: 0.986}
  power_prior_0_01: {W1: 0.148, W2: 0.194}
  zuordnungsregel: "wie H-28 (DEC-88)"
selection: "wie H-28"
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, kosten_bp_woche: 30, label: "unter_wand nur Einzelposition"}
decision_relevance: {on_pass: "wie H-28", on_drop: "Lag-2-Reversal widerlegt; PRD-Ein-Tages-Gap-Design NICHT getestet"}
capital_tax_venue: "wie H-28"
stress_episode: "wie H-28"
irreversibility_probe: "wie H-28"
positive_control: "wie H-28 (rev_gap in der Positivkontrolle injiziert, IC 0.06 in Richtung negativ)"
fixtures: {bounce: test_dec87_t1_h29_bounce_fixture_fires_no_pass, sonst: "wie H-28"}
artifacts: {cluster_series_ref: "wp13_run_H-29_rev_gap_<W>_ic_weekly.csv und ..._residualized.csv; Liquiditaet und Bounce je Fenster im Haupt-JSON", bootstrap_replicates_ref: "wie H-28"}
fdr_family: "wie H-28"
over_family: "wie H-28"
feasibility_verdict: bestanden
constants_hash: "n/a - kapitalfrei"
data_fingerprints: "wie H-28"
stats3_version: "wp13_xsec 849ec4a (Lauf, Positivkontrolle); Vorlauf v5e 92607da"
bedingung_welle_1: [WP-7 B2, WP-12b, WP-13a v5d, WP-13a v5e]
```

### H-30 - A3-V Vol-/MAX-/Beta-Anomalie (vol-gewichtet, drag-bereinigt) - GL-012 vor dem Lauf

**Hypothese (registriert, nicht gerechnet):** Auf dem PIT-Union-Universum gilt fuer mindestens eine Vol-Charakteristik
in W1 und W2 jeweils:
- der mittlere woechentliche Rank-IC gegen die vol-gewichtete, drag-bereinigte Folgewochenrendite ist negativ und
  <= -IC_min;
- das gilt auch nach `fm_neutral_8w`-Neutralisierung;
- und Gate (5) ist erfuellt.

Das Outcome ist definiert nach DEC-87 (G):
- sigma_w = sqrt(n_t) x vol_rv;
- o_{t+1} = (r_{t+1} + sigma_w,t^2/2) x target/sigma_w,t, mit target = Median von sigma_w.

**Ertragsquelle / Zahler:** Praemie gegen Lotterie-Nachfrage; Zahler sind Kaeufer hochvolatiler Perps.

**Status:** **GL-012-Feasibility-DROP vor dem Lauf** (DEC-74 (h), DEC-87 (G), DEC-88):
- Spread(D10-D1)/Kante 2,764 > 0,5 [v5e `h30_feasibility_weekly_units`].
- vol_beta ist zusaetzlich strukturell neutralisiert (C.4, DEC-87 (H)).
- Kein Verdikt ueber die Vol-Anomalie selbst; K bleibt 7.

```yaml
id: H-30
kohorte: A3 / F-XSEC1
klasse: W
capital_free: true
hypothese: "Mindestens eine Vol-Charakteristik (vol_rv, vol_max, vol_beta): mittlerer woechentlicher Rank-IC gegen das vol-gewichtete, um +sigma_w^2/2 bereinigte Folgewochen-Outcome in W1 und W2 negativ und <= -IC_min, roh UND nach fm_neutral_8w (dort < bindendes Quantil); Gate (5) < 0.60."
ertragsquelle: "Praemie gegen Lotterie-Nachfrage; Zahler: Kaeufer hochvolatiler Perps"
metric: "wie H-28, Outcome vol-gewichtet und drag-bereinigt (run.h30_outcome_for_window)"
varianten: {vol_rv: "gl012_pre_run (Feasibility)", vol_max: "gl012_pre_run (Feasibility)", vol_beta: "gl012_pre_run (strukturell C.4 + Feasibility)"}
charakteristik: {vol_rv: "SD der Tages-Log-Renditen der Woche t", vol_max: "max Tages-Log-Rendite der Woche t", vol_beta: "OLS-Beta zu BTCUSDT t-7..t"}
richtung: negativ
windows: "wie H-28"
fenster_regel: "entfaellt (GL-012 vor dem Lauf)"
threshold:
  W1: {vol_rv: 0.01694, vol_max: 0.01698, vol_beta: 0.01675}
  W2: {vol_rv: 0.01470, vol_max: 0.01464, vol_beta: 0.01460}
  ref: "v5e windows.<W>.noise_floor_and_threshold.ic_min_capped_per_variant"
structural_null:
  vol_drag_feasibility_L: {kante_bp_woche: 91.42, spread_d10_d1_ueber_kante: 2.764, se_ueber_kante: 0.175, n_tage_median: 7.0, grenze: 0.5, feasibel: false, ref: "v5e h30_feasibility_weekly_units"}
  gate5_median_spearman: {W1: {vol_rv: 0.159, vol_max: 0.150, vol_beta: 0.154}, W2: {vol_rv: 0.142, vol_max: 0.104, vol_beta: 0.050}, grenze: 0.60, ref: "v5e windows.<W>.gate5_reachability_by_variant"}
  beta_control_quantile_binding: {W1: {vol_rv: -0.01843, vol_max: -0.01843, vol_beta: -0.00559}, W2: {vol_rv: -0.01639, vol_max: -0.01639, vol_beta: -0.00486}}
power: "entfaellt (Feasibility sperrt vor der Power-Zuordnung, DEC-88)"
selection: "wie H-28 (H-30-Varianten bleiben im Mittel des Maximums ueber 7 und im BH-Nenner mit p = 1)"
economic_minimum: {portfolio: 0.0101, einzelposition: 0.062, kosten_bp_woche: "4.5-7.5", label: "unter_wand nur Einzelposition"}
decision_relevance: {on_gl012: "A3-V auf diesem Panel nicht schaetzbar (Wochen-Drag-Spread 2.76x Kante); kein Verdikt ueber die Lotterie-Praemie; eine neue A3-V-Hypothese braucht ein Design, das die strukturelle Ursache beseitigt, eigene Registrierung"}
capital_tax_venue: "wie H-28"
stress_episode: "wie H-28"
irreversibility_probe: "wie H-28"
positive_control: "entfaellt"
fixtures: {a3v: test_dec87_t1_a3v_fixture_same_vol_dispersion_no_relation_fires_no_gate}
artifacts: "keine Serien (nicht gerechnet); Sperrgrund im Haupt-JSON je Eintrag"
fdr_family: "wie H-28 (p = 1)"
over_family: "wie H-28"
feasibility_verdict: verfehlt
constants_hash: "n/a - kapitalfrei"
data_fingerprints: "wie H-28"
stats3_version: "wp13_xsec 849ec4a (Lauf, Positivkontrolle); Vorlauf v5e 92607da"
bedingung_welle_1: [WP-7 B2, WP-12b, WP-13a v5d, WP-13a v5e]
```

---

### Die zwoelf Pflichtzeilen (PRD 3.3) - Kohorte

| # | Zeile | Inhalt |
|---|---|---|
| 1 | Power | alpha 0,05 einseitig, Power 0,80, z 2,4865, Cluster Kalenderwoche, W 52/51, c_rho gemessen und gedeckelt. Volle Power und MDE80 je Variante: Zuordnungstabelle (DEC-88). |
| 2 | Entscheidungsrelevanz | PASS: Tradability-Registrierung mit Dezil-Slippage (DEC-67 E4). DROP von H-28_mom1 und H-29_rev_gap: Klasse W im Wochenhorizont fuer die gerechneten Faktoren widerlegt. H-30, mom2 und mom4 ohne Verdikt (GL-012). Oekonomisches Etikett 0,0101 / 0,062 (C.2). |
| 3 | Cluster-Einheit | Kalenderwoche; Resampling Moving Block 4; N = 52/51; effektives N = W/c_rho_bk^2 [abg. aus v5e `noise_floor_and_threshold.c_rho_corrected`]: mom1 37,7/35,7, rev_gap 48,9/46,3. |
| 4 | Selektions-Deflation | K = 7; bindende Decke 0,00834 / 0,00685 < min IC_min 0,01675 / 0,01460; analytisch 0,00934 / 0,00814; Rauschen gemessen 0,00919 / 0,00778. |
| 5 | Adversariales Fixture | Beta-korreliert mit dominantem, autokorreliertem, driftendem Marktfaktor unter `fm_neutral_8w`: kein PASS (T1-Test; die Negativkontrolle der Positivkontrolle ist nur eine signalfreie Kontrolle in der stress-Null, kein adversariales Fixture). H-29: Bounce-Fixture mit gemessenen Parametern. H-30: A3-V-Fixture. |
| 6 | Kostenmodell-Bindung | `constants_hash` n/a, kapitalfrei. `tradability3` nicht gebaut; die Werkzeug-DEC ist offen (PRD 3.4 nennt sie DEC-59, im Log ist DEC-59 anders belegt). |
| 7 | Irreversibilitaets-Probe | nachladbar (Bybit v5 oeffentlich, Harvest-Export). |
| 8 | Positivkontroll-Vorschaltung | ja, zuerst und allein, vorab fixiert (DEC-89 E2, PRD 3.3.8): `scripts/wp13_xsec.py --positive-control` mit der registrierten YAML (sha256 `bd948f34...c299`) auf der realen Fensterform (Wochen, PIT-Masken, K_t) mit synthetischen Renditen, injiziertem Signal IC 0,06 und eingefrorenen Konstanten. Kriterium: H-28_mom1 und H-29_rev_gap in den Seeds 53/54/55 PASS UND Negativkontrolle (IC 0) in keinem Seed PASS; rc 0 nur bei BESTANDEN. Lauf (~2 h Null-Nachrechnung, Dauer UNBELEGT) nur nach BESTANDEN. Befehl: Abschnitt Lauf, Schritt 1; |
| 9 | Kapital/Steuer/Venue | n/a kapitalfrei; Zahler nach 2024: Delisting-Hazard ~50 % (Etikett). |
| 10 | Stress-Episode | STRESS_REL 22/8 Tage, STRESS_ABS 2/1 Tage (Abdeckungsnachweis). |
| 11 | Ergebnis-Artefakte (DEC-53) | Rohe und residualisierte Wochen-IC-Serien je gerechnetem Eintrag und Fenster (CSV + sha256); `wp13_run_fingerprint.json` (Seed, Bit-Generator, Code-Hash/Commit, Daten-Fingerprints, Parameter, Replikat-Fingerprints, result_sha256); Haupt-JSON und `wp13_run.md` (mit den gelesenen DEC-89-Eingaben); L versiegelt. Positivkontrolle: `wp13_positive_control.json`/`.md` mit result_sha256. Fehlt etwas, gibt es KEIN VERDIKT (`verify_run_artifacts`). |
| 12 | Test-Pflichten | siehe die T-Liste unten |

**Test-Pflichten T0-T7** (alle in `tests/unit/test_wp13_*.py`):

| Stufe | Tests |
|---|---|
| T0 | Unit-Tests der WP-13-Module |
| T1 | `test_dec87_t1_*`, `test_dec87_prd_positive_fixture_passes_end_to_end_through_run_full`; Positivkontrolle `test_dec89_pc_*`, `test_dec89_cli_positive_control_*` |
| T2 | `test_dec87_t2_determinism_n3_with_fingerprint` |
| T3 | `test_dec87_t3_no_checkpoints_artifact_round_trip_documented` (Lauf ohne Checkpoint; Round-Trip ueber T7) |
| T4 | `test_t4_gate_arithmetic_pure_on_conserved_payload` |
| T5 | `test_dec87_t5_constants_pin_the_yaml_values_flow_into_every_payload`, `test_dec89_t5_rules_are_pinned_against_the_code_constants`, `test_dec89_w_judged_is_read_used_and_pinned`, `test_dec89_t5_constants_pin_lists_the_new_fields` |
| T6 | `test_dec87_t6_wp13_xsec_never_imports_the_legacy_package` |
| T7 | `test_dec87_t7_artifact_round_trip_reproduces_the_gate_estimators_bitwise`, `test_dec87_missing_mandatory_artifact_means_no_verdict_file`, `test_dec89_pc_is_deterministic_and_the_artifacts_round_trip` |

---

### Kill-Bedingungen (vorab; keine wird nach dem Lesen der IC-Serie geaendert)

| Bedingung | Folge | Stand |
|---|---|---|
| min K_t < 134 in einem Fenster (PRD 5.3 Kill (2)) | Kohorte nicht lauffaehig | W1 345, W2 514: nicht ausgeloest |
| Decke >= IC_min (DEC-75 (2)) | GL-012 der Variante vor dem Verdikt | nicht ausgeloest |
| Null-Nachrechnung ausserhalb +-10 % | KEIN VERDIKT (ganzer Lauf) | erwartet bitgleich |
| T5-Pin verletzt (`block_len`, `level`, `w_judged`) | KEIN VERDIKT | - |
| Daten-Fingerprint weicht ab | KEIN VERDIKT | - |
| DEC-53-Artefakte unvollstaendig | KEIN VERDIKT | - |
| H-30-Feasibility > 0,5 (DEC-74 (h)) | GL-012 H-30 vor dem Lauf | **ausgeloest (2,764)** |
| MDE80 > IC_prior (DEC-51 (2)) | GL-012 der Variante | **ausgeloest: mom2, mom4** |
| strukturelle Neutralisierung (C.4) | GL-012 der Variante | **ausgeloest: vol_beta** |
| Positivkontrolle NICHT BESTANDEN (rc 3) oder Abbruch (rc 1) | kein Lauf, neue DEC (DEC-89 E2) | - |

**Etiketten statt Kill:**
- Survivorship-Fixture (rev_gap W2 -0,579 IC_min), Liquiditaet (4c), NO_HISTORY, Gap eine Woche, Prior rev_gap uebernommen.
- vol_rv und vol_max sind in der Null identisch.
- Die Null-Simulation hat keinen Vorlauf vor dem Fenster (Coverage 0,889 / 0,877).
- Delisting-Datum = Announcement-Datum.
- AR(1)-Schaetzungen der Persistenz-Null ohne Kendall-Bias-Korrektur (Review v2 W-15): phi je Symbol ist nach unten
  verzerrt, damit c_rho_bk und IC_min eher zu NIEDRIG (milde Lockerung, Groesse gering; c_rho_bk enthaelt bereits die
  +1/W-Korrektur der IC-Autokorrelation, DEC-75 (8)).

**NICHT in der Kill-Liste:** sigma_xs (Etikett C.2).

### Entscheidungsrelevanz und Nicht-Wiederholungs-Nachweis (C.1, PRD 5.3 woertlich)

- **PASS einer Variante:** getrennte Tradability-Registrierung mit gemessener Dezil-Slippage (DEC-67 E4); kein
  Kapitalpfad vor `tradability3`. Jedes PASS ist "vorlaeufig bis F-WEEK geschlossen".
- **DROP von H-28_mom1 und H-29_rev_gap:** Klasse W auf Bybit-Perps im Wochenhorizont ist fuer Momentum (1 Woche) und
  Lag-2-Reversal erschoepft (D.7 auf breiter Basis bestaetigt); fuer A3-R gilt das nur im Lag-2-Design. mom2/mom4
  (Power) und H-30 (Feasibility/strukturell) sind GL-012 vor dem Lauf - kein Verdikt ueber diese Effekte.
- **Nicht-Wiederholung (C.1):** A3 wiederholt nicht D.7 (C-06/H-07/H-08): Breite K_t >= 345 statt N = 5 (H-07:
  max|z| = sqrt(N-1) = 2,0 < 2,5); Rauschboden 0,04858/0,04192 statt 0,50; Wochen- statt Stundenhorizont; explizite
  Bounce-, Drag- und Beta-Kontrolle; survivorship-freies Union-Panel (DEC-72).

### Abweichungen vom PRD-Text (registriert, etikettiert)

1. Das Reversal-Gap ist eine Woche statt ein Tag: getestet wird das Lag-2-Reversal, das PRD-Ein-Tages-Design ist nicht
   getestet (DEC-87 (B)).
2. Der Faktor 1/sqrt(2) wird fuer die Je-Fenster-Decke nicht verwendet (DEC-87 (C)).
3. Die Deckelung max(1, c_rho_bk) weicht von DEC-74 (b) ab (DEC-75 (8)).
4. Die Gates (2) und (3) sind report-only, bindend ist BY am Wellenschluss (DEC-75 (6)).
5. Die Kills (3)/(4) des PRD: Survivorship ist Etikett (DEC-76), der Bounce-Kill ist in Kraft (DEC-87 (I)).
6. Die Komposition aus Beta-Kontrolle und vol-gewichtetem H-30-Outcome ist registriert (`run.h30_outcome_for_window`),
   wegen GL-012 aber gegenstandslos.
7. Der PRD-5.3-Nicht-Trivialitaets-Anker "Dezil-L/S-Bruttorendite" wird nicht gerechnet (nicht gebaut; waere
   report-only und keine PASS-Komponente, C.2).

### Lauf (nach Registrierung)

Allgemein gilt fuer beide Schritte:
- Code `849ec4a`, Cloud (DEC-83); Code-Fingerprint `run.code_fingerprint()` bei `849ec4a` (19 Dateien):
  `code_sha256 65852b4167ee0a1d27b2a60bbf25d370e51339bfbdee3b4e5fa7ce6b3dc2701d`. Der GL-Eintrag prueft, dass
  `wp13_run_fingerprint.json` genau diesen Wert traegt (deckt auch die Lauf-Parameter aus Code-Defaults:
  `n_reps_bootstrap`, `n_reps_permutation`, `n_sims_persistence`).
- Das Panel aus dem Harvest-Export wird geprueft in ein frisches Sitzungsverzeichnis `<panel_dir>` entpackt.
- Beide Modi haben dieselbe Startsperre, denselben Schema-Preflight inklusive aller eingefrorenen Konstanten und der
  DEC-89-Felder, dieselbe Panel-Ladung und dieselbe Fingerprint-Pruefung.
- Alle Argumente sind gepinnt. Ein abweichendes `--start-year`/`--end-year` (Default: aktuelles Jahr) aendert den
  Union-Fingerprint und fuehrt zum Abbruch; `--as-of` waehlt nur frozen/open-Pfade und aendert ihn nur bei anderem Jahr -
  er ist trotzdem auf 2026-09-28 gepinnt.

**Schritt 1 - Positivkontrolle in Produktionskonfiguration, allein und zuerst** (DEC-89 E2, PRD 3.3.8):

```
python scripts/wp13_xsec.py --positive-control \
  --registered scinance3-impl/state/registered/h28_h30_v3.yaml \
  --registered-sha256 bd948f34516bb444f152287863e6096da6faf82712b579c6dfa211599015c299 \
  --panel-base <panel_dir>/panel_1d \
  --delisted-base <panel_dir>/panel_1d_delisted \
  --delisted-manifest <panel_dir>/panel_1d_delisted/panel_manifest.sqlite \
  --delisting-dates <panel_dir>/panel_1d_delisted/delisting_dates.json \
  --start-year 2021 --end-year 2026 --as-of 2026-09-28 \
  --convention close_at_last --allow-partial \
  --seeds 53,54,55 \
  --out scinance3-impl/state/runs/wp13_positivkontrolle_<YYYYMMDD>
```

Was der Modus tut:
- Vom realen Panel werden NUR das Wochenraster, die PIT-Alive-Masken, `returns_valid`, die Symbolreihenfolge und die
  Fingerprints genutzt. Die realen Renditen werden vor der Kontrolle verworfen; `run_positive_control` hat kein
  `returns`-Argument.
- Je Seed und Fenster entstehen synthetische Wochenrenditen: Faktorpanel mit stress-rho_f/beta_sd des Fensters,
  Marktspalte := Faktor, Drift 0, dazu 8 Sektorbloecke und ein injiziertes Signal IC 0,06 (mom1 positiv, rev_gap negativ
  im Ein-Wochen-Gap). Skalen = `windows.<W>.null_scales`: sigma_f 0,06685/0,05514 (gemessen), sigma_e 0,12064/0,10729
  (idiosynkratisch), stress-Kalibrierung rho_f 0,09248/0,08317, beta_sd 0,77067/0,58333 (DEC-89 E2 Nachtrag).
- Die komplette Gate-Auswertung des Laufs (`run.evaluate_entry`) rechnet gegen die EINGEFRORENEN Konstanten der YAML,
  ohne Null-Neuberechnung. Ergebnis: `wp13_positive_control.json` und `.md`.

**PASS-Kriterium (vorab fixiert, DEC-89 E2):**
- `H-28_mom1` und `H-29_rev_gap` sind in ALLEN drei Seeds 53, 54 und 55 PASS.
- Die Negativkontrolle (identische Welt, injiziertes Signal 0) liefert in KEINEM Seed ein PASS.
- Gesperrte Varianten werden uebersprungen. Andere Seeds als 53/54/55 ergeben nie BESTANDEN.
- Ausgabezeile "Positivkontrolle BESTANDEN" / "Positivkontrolle NICHT BESTANDEN". Exit-Code 0 NUR bei BESTANDEN,
  3 bei NICHT BESTANDEN, 1 bei Abbruch (Startsperre, Schema, Fingerprint, Pin, Panel).
- **Nur bei rc 0 folgt Schritt 2.** Sonst gibt es keinen Lauf, sondern eine Ursachenanalyse und eine neue DEC.
- Vor dem Lauf wird festgehalten (DEC + GL-Eintrag): rc 0, Pfad und `result_sha256` von `wp13_positive_control.json`.

**Schritt 2 - Lauf:**

```
python scripts/wp13_xsec.py --run \
  --registered scinance3-impl/state/registered/h28_h30_v3.yaml \
  --registered-sha256 bd948f34516bb444f152287863e6096da6faf82712b579c6dfa211599015c299 \
  --panel-base <panel_dir>/panel_1d \
  --delisted-base <panel_dir>/panel_1d_delisted \
  --delisted-manifest <panel_dir>/panel_1d_delisted/panel_manifest.sqlite \
  --delisting-dates <panel_dir>/panel_1d_delisted/delisting_dates.json \
  --start-year 2021 --end-year 2026 --as-of 2026-09-28 \
  --convention close_at_last --allow-partial \
  --out scinance3-impl/state/runs/wp13_run_<YYYYMMDD>
```

- Ergebnis: rc 0 mit Verdikten, oder rc 1 = KEIN VERDIKT (Abbrueche P0-P7).
- Artefakte:
  - `wp13_run_<Eintrag>_<W>_ic_weekly.csv` und `..._ic_weekly_residualized.csv`;
  - `wp13_run_fingerprint.json`;
  - `wp13_run.json` und `wp13_run.md`;
  - `wp13_run_L_window_sealed.json`.

**Schritt 3 - nach dem Lauf:**
- Gate-Check nur gegen diesen Text.
- GL-032 mit den Etiketten des Laufs (Survivorship, Liquiditaet, Persistenz, BH) und H-30 als "GL-012 vor dem Lauf".
- Das L-Siegel wird erst nach dem GL-Eintrag geoeffnet.

**Rueckbauweg:** Die Registry ist append-only; ein Widerruf ist ein neuer Eintrag. Erst-, Zweit- und Drittfassung
bleiben stehen. Die Registrierungsdatei ist per sha256 gepinnt; v5d und v5e bleiben als Artefakte.

**Registriert:** 2026-10-12 durch den Orchestrator (DEC-90), nach Review v3 (`state/REVIEW_H28_H30_v3.md`, formales VETO durch B-1/B-2 aufgehoben). Registrierungsdatei `state/registered/h28_h30_v3.yaml`, sha256 `bd948f34516bb444f152287863e6096da6faf82712b579c6dfa211599015c299`. Kein Lauf erfolgt; als Naechstes die Positivkontrolle allein.
