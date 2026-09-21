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
