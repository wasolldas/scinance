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
