# CROSSDOMAIN_PRD — Cross-Domain-Track, Pre-Registration H-09..H-13

**Phase:** REGISTRY-WRITE
**Stand:** 2026-07-07
**Erstellt von:** `registry-keeper`
**Maßgebliche Quellen:** `results/deep_validation/hardened_hypotheses.md` (H-09..H-13, gehärtet, registry-fertig — Inhalt wörtlich übernommen, hier nur ins Enddokument-Format gebracht), `results/deconflict.md` (Orchestrator-Auswahl der 5 aus 7 Shortlist-Kandidaten), `results/critique/scores.md` (Scoring-Herkunft), `results/discipline_scan/*.md` (rohe IC-Vorschläge), `reference/FINAL_PRD.md` (Stildokument), `CLAUDE.md` (Verfassung §2, ID-Schema §3), `reference/PROGRAM_FINAL_REPORT.md` (Fortsetzung von H-08/GL-013).

> **Rückführbarkeit ist oberstes Gebot.** Jede Aussage unten trägt die IC-Nummer, aus der sie stammt. Kein Eintrag kommt „aus dem Nichts"; Schwellen, Fenster und Abbruchkriterien sind wörtlich aus `hardened_hypotheses.md` übernommen — der `registry-keeper` verschiebt keinen Torpfosten, er formatiert nur.

---

## 1. Kontext

`reference/PROGRAM_FINAL_REPORT.md` (Stand 2026-07-06) hat Scinance 2.0 nach drei Wellen und 13 vorregistrierten Gates (H-01..H-08, GL-001..GL-013) für **daten-gated statt arbeits-gated** erklärt: 9 DROP, 2 PARK, 2 kapitalfreie WEITER, **0 handelbare Kanten**. Die Friction-Wand (11 bps Taker / ~15 bps inkl. Slippage) hat jede gemessene Kante geschlagen, auch die beiden bestbelegten Mikrostruktur-Signale (BTC→ETH-Lead-Lag, inverses OFI auf SOL) lagen 80–500× darunter. Die Empfehlung „keine Welle 4 auf Vorrat" bezog sich explizit auf *mehr vom Gleichen* im bereits erschöpften Microstructure-/ML-Werkzeugkasten.

Dieser Cross-Domain-Run eröffnet stattdessen eine **neue Suchachse**: sechs Fachgebiete (Random-Matrix-Theory, Extremwerttheorie/Aktuarmathematik, Netzwerktheorie, Mechanism Design, Climatology-Ensemble-Forecasting, Dendrochronologie), die in keiner der drei Scinance-2.0-Wellen und im Vorgänger-Scouting (`edge-research-v2`) benutzt wurden. Die **methodische Verfassung ist unverändert**: Feasibility-Check vor Pre-Registration, Mess-Gate ≠ Tradability-Gate (`capital_free=true` bei allen 5 Einträgen), FDR-Pflicht (BH α=0,10), Pre-Registration ohne Torpfosten-Verschiebung, hartes Ein-Fenster-Kriterium, Single-Operator-Realismus (max. 4–5 Hypothesen).

Der Ablauf AUDIT → DISCIPLINE-SCAN → PRE-SCREEN → CRITIQUE → DECONFLICT → DEEP-VALIDATION → REGISTRY-WRITE ist vollständig durchlaufen: 20 rohe IC-Vorschläge (`results/discipline_scan/`), gescort in `results/critique/scores.md` (Schwelle ≥8/12, keine Dimension 0 → 7 Shortlist-Kandidaten), gedeckelt auf 5 in `results/deconflict.md`, gehärtet zu H-09..H-13 in `results/deep_validation/hardened_hypotheses.md`. Dieses Dokument ist die Übergabe der 5 Einträge in konsistentem Enddokument-Format, Fortsetzung der Hypothesen-Registrierung von `reference/PROGRAM_FINAL_REPORT.md` (letzter Eintrag H-08/GL-013).

---

## 2. Übersichts-Tabelle

| H-xx | Disziplin | Kernfrage (Kurzform) | FDR-Familie | Reifegrad | Rechenaufwand | capital_free |
|---|---|---|---|---|---|---|
| **H-09** | Mechanism Design | Order-Notional-Bunching unterhalb der ersten Bybit-Risk-Limit-Tier-Kante (Margin-Kink-Vermeidung), asymmetrisch + über Rundzahl-Placebo | F-BUNCH | sofort testbar | CPU | true |
| **H-10** | Dendrochronologie | Cross-Stream-Pointer-Tage (≥60 % von 30 Serien synchron) + 1–5-Tage-Pre-Event-Drift der gehaltenen Deribit-dvol-Zielmetrik | F-POINTER | sofort testbar (Basis-Version) | CPU | true |
| **H-11** | Climatology (§5-Sonderrolle) | Analog-Ensemble-Vorhersage (CRPS) der 3-Tage-realisierten-Vol schlägt HAR-RV-Baseline | F-ANEN | **data-gated** (gesperrt) | CPU | true |
| **H-12** | Econophysics/RMT | Lokalisierter, börsenspezifischer Restmodus (λ2/IPR) jenseits des Marktmodus in der Cross-Exchange-Korrelationsmatrix (Bybit/Binance/Deribit) | F-FRAG | sofort testbar | CPU | true |
| **H-13** | EVT/Aktuarmathematik | Divergenz zwischen statistischem GPD-ξ (Returns) und risikoneutralem Tail-Shape ξ_Q (Options-IV-Surface) | F-TAILSHAPE | **data-gated** (gesperrt) | CPU | true |

Disziplin-Abdeckung: 5 verschiedene Fachgebiete, keine Wiederholung (Deconflict-Vorgabe „max. 1 pro Fachgebiet"). Balance: 3 sofort testbar (H-09, H-10, H-12) + 2 data-gated, aber hochwertig gehärtet (H-11 = Friktions-Flaggschiff §5, H-13 = Tail-Form-Divergenz).

---

## 3. Die 5 Pre-Registrations

### H-09 — Risk-Limit-Tier-Bunching (Margin-Kink-Vermeidung) *(aus IC-MECH-2, `mechanism-design`)*

- **Markt-Zuordnung:** F (Futures-Perp, Bybit).
- **Kernfrage/Hypothese:** Taker-Order-Notionals auf Bybit-Perps clustern systematisch knapp UNTERHALB der ersten dokumentierten Risk-Limit-Tier-Kante K_s je Symbol (MMR-Sprung, z. B. BTCUSDT K=2.000.000 USDT: 0,50 %→0,56 %), wie es ein Bunching-Modell an einer diskreten Margin-Strafe (Saez 2010 / Chetty et al. 2011 Excess-Mass-Estimator) vorhersagt — mit der bunching-typischen ASYMMETRISCHEN Signatur (Excess-Mass unter der Kante, kein vergleichbarer Excess direkt darüber) und STÄRKER als reine Rundzahl-Präferenz an Placebo-Rundzahlen.
- **Gegen-These / A-priori:** Positionsgrößen werden auf Account-/Positions-Ebene gesteuert, nicht auf Order-Ebene; sichtbares Clustering an 2.000.000 ist überwiegend Rundzahl-Präferenz. **Erwarteter Ausgang: DROP** (über Placebo-Kontrolle oder Asymmetrie-Bedingung).
- **capital_free:** true — reiner Struktur-/Verhaltensfakt. Eine Tradability-Folge (Timing/Front-Running an der Kante) wäre eine NEUE **H-09b**, NICHT impliziert; laut `friction_audit.md` ein Mikrostruktur-Timing-Signal mit hohem Wand-Risiko.
- **Datenbindung & Reifegrad:** Bybit `publicTrade`, Basis-Bestand 2026-03-27…2026-07-04, alle 5 Symbole. **Sofort testbar** — einziger MECH-IC ohne Live-Stream-Abhängigkeit.
- **Datenströme & Fenster (disjunkt):** W1 = 2026-03-27…2026-05-15, W2 = 2026-05-16…2026-07-04 (deterministisch-chronologische Halbierung). Beobachtungseinheit (urteilstragend): Taker-Order-Aggregat (konsekutive `publicTrade`-Records gleichen symbol/side/ts_exchange_ms gemerged); Fill-Level nur nicht-urteilstragende Robustheit.
- **Methodik (vorab fixiert):** K_s je Symbol als datierter, append-only Operationalisierungs-Nachtrag vor Lauf-Start fixiert (DEC-09-Muster, keine Schwellen-Verschiebung). Schätzband [0,4·K_s, 1,3·K_s), Bin-Breite 0,01·K_s (90 Bins); Counterfactual = Polynom Grad 7 unter Ausschluss von [0,90·K_s, 1,10·K_s); Bunching-Fenster B− = [0,95·K_s, 1,00·K_s), Kontrollfenster B+ = (1,00·K_s, 1,05·K_s]. Excess-Mass-Ratio b̂− via Residuen-Bootstrap (Chetty et al. 2011, 500 Reps). Placebo-Kontrollen P1 = 0,5·K_s, P2 = 0,75·K_s (nicht Teil der FDR-Familie).
- **Nullhypothese:** glatte (polynomiale) Notional-Dichte ohne Kanten-Effekt; Bootstrap-Null b−=0.
- **N-Floor (Gate-Bestandteil):** Zelle nur gültig bei ≥2.000 Order-Beobachtungen im Schätzband UND Counterfactual-Erwartung in B− ≥50; sind in einem Fenster alle 5 Symbol-Zellen ungültig → DROP wegen Power (keine Floor-Absenkung).
- **Validierungs-Gate (wörtlich, bindend):** WEITER, wenn für mindestens ein Symbol in BEIDEN Fenstern (Order-Level, gültige Zelle): Bootstrap-p(b̂−>0) ≤0,05 nach BH-FDR α=0,10 über F-BUNCH UND b̂−≥1,0 UND b̂− − b̂+ ≥0,5 UND b̂− > max(b̂_P1, b̂_P2).
- **Abbruchkriterium (wörtlich, bindend):** DROP, wenn kein Symbol alle vier Bedingungen in beiden Fenstern erfüllt (hartes Ein-Fenster-Kriterium) ODER N-Floor in einem Fenster von allen 5 Zellen verfehlt wird. Kein Graubereich, keine nachträgliche Band-/Bin-/Placebo-Anpassung.
- **FDR-Familie:** **F-BUNCH** (neu) — 5 Symbole × 2 Fenster (Order-Level) = 10 Tests, BH-FDR α=0,10.
- **Feasibility-Gegenprüfung (GL-012):** kein struktureller Deckel auf b̂− (kein H-07-Analogon); limitierende Größe ist Groß-Order-Dichte (T-gebunden), abgefangen durch den N-Floor. **Bestanden.**
- **Rechenaufwand:** CPU — DuckDB-Binning über ~10⁸ Records + Polynom-Fit + 500 Bootstrap-Reps: Minuten.
- **Selbstkill-/Restrisiko:** Order-Aggregat ≠ Positions-Zuwachs (Interpretations-Grenze); Tier-Kanten sind selbst Rundzahlen (Placebo kontrolliert, kann echte Effekte konservativ maskieren); historische K_s-Änderungen invalidieren Zellen.
- **Herkunft:** IC-MECH-2 (`mechanism-design`), Feasibility bestätigt (PRE-SCREEN, 2026-07-07), Critic-Score 10/12 (`critique/scores.md`), Fable-5-gehärtet (2026-07-07).
- **Status:** gehärtet, registry-fertig; Lauf NICHT gestartet.

---

### H-10 — Cross-Stream-Pointer-Days + Pre-Event-Drift (Cropper) *(aus IC-DEND-1, `dendrochronology-crossdating`)*

- **Markt-Zuordnung:** F (5 Perp-Symbole, Bybit+Binance) mit gehaltener Zielmetrik aus O-Index (Deribit dvol).
- **Kernfrage/Hypothese:** (Stufe 1, Synchronisations-Existenz) An „Pointer-Tagen" (≥60 % der verfügbaren Symbol×Stream-Serien zeigen gleichzeitig eine Cropper-Anomalie gleicher Richtung) liegt die beobachtete Pointer-Tag-Zahl signifikant über einer Surrogat-Null, die Marginalraten erhält, aber Cross-Serien-Synchronisation zerstört. (Stufe 2, Pre-Event-Drift) 1–5 Handelstage vor Pointer-Tagen zeigt die gehaltene (nicht schwellenbildende) Deribit-dvol-Zielmetrik eine von der Baseline abweichende Drift.
- **Gegen-These / A-priori:** Pointer-Tage sind triviale Abbilder marktweiter Schock-Tage ohne Vorlauf-Information. **Erwarteter Ausgang:** Stufe 1 WEITER-nah, Stufe 2 DROP; reales Power-DROP-Risiko (nur ~2–6 erwartete Pointer-Tage je Fenster).
- **capital_free:** true — Existenzfrage. Tradability wäre NEUE **H-10b**, NICHT impliziert. Friktions-Grobrechnung (nachgereicht): ein evtl. 1–5-Tage-Preis-Vorlauf läge bei 200–600 bps ≈ 13–55× über der Wand — die hier vorregistrierte Zielmetrik ist aber eine dvol-Drift (keine Preis-Return-Übersetzung; das wäre Teil von H-10b).
- **Datenbindung & Reifegrad:** Basis-Bestand 2026-03-27…2026-07-04. **Detektions-Serien (30, vorab fixiert):** je 5 Symbole × {Bybit-RV, Bybit-Funding, Bybit-ΔlogOI, Binance-RV, Binance-Funding, Binance-ΔlogOI}. **Gehaltene Zielserie:** Deribit `dvol` (BTC+ETH) — dvol und `book_summary` vollständig aus der Detektion ausgeschlossen (sauberer Hold-out). **Sofort testbar (Basis-Version).** Die Multi-Regime-Kalibrierung über Bull/Bear/Crash bleibt separate, spätere Hypothese nach Deep-Backfill-Coverage — durch dieses Gate weder impliziert noch ersetzt.
- **Datenströme & Fenster:** Tagesraster UTC. Burn-in 21 Tage. Nutzbar 2026-04-17…2026-07-04; W1 = 2026-04-17…2026-05-25 (39 Tage), W2 = 2026-05-26…2026-07-04 (40 Tage).
- **Methodik (vorab fixiert):** trailing 63-Tage-Median-Detrending (min_periods=21); Cropper-Score C_t = (Residuum − Mittel_11z)/SD_11z (11-Tage zentriert). Pointer-Tag: n_avail≥18 UND max(#{C_t≥1,5}, #{C_t≤−1,5})/n_avail ≥0,60 (Schwellen aus Quell-IC unverändert übernommen). Neuwirth-Crosscheck nicht-urteilstragend.
- **Nullhypothese:** Stufe 1 — 1.000 zirkuläre Surrogate je Serie (erhält Marginal-/Autokorrelation, zerstört Cross-Ausrichtung). Stufe 2 — 1.000 Permutations-Ziehungen gleich großer Zufalls-Tagesmengen (≥6 Tage Abstand zu jedem Pointer-Tag).
- **Zielgröße Stufe 2:** dvol-Index D_t (z-standardisiertes Mittel BTC+ETH dvol); Δpre(t) = Mittel(D,[t−5,t−1]) − Mittel(D,[t−15,t−6]); Statistik S = Mittel von Δpre über alle Pointer-Tage.
- **Validierungs-Gate (wörtlich, bindend):** WEITER, wenn nach BH-FDR α=0,10 über F-POINTER alle vier Zellen bestehen: Stufe-1-Surrogat-p≤0,05 in W1 UND W2 UND N_pointer≥3 je Fenster UND Stufe-2-Permutations-p≤0,05 (zweiseitig) in W1 UND W2.
- **Abbruchkriterium (wörtlich, bindend):** DROP, wenn Stufe-1-p>0,05 in einem Fenster ODER N_pointer<3 in einem Fenster (Power-DROP, Schwellen 60 %/1,5 werden NICHT gesenkt) ODER Stufe-2-p>0,05 in einem Fenster ODER FDR-Korrektur nicht überlebt. Kein Graubereich.
- **FDR-Familie:** **F-POINTER** (neu) — 4 Zellen (2 Stufen × 2 Fenster), BH-FDR α=0,10.
- **Feasibility-Gegenprüfung (GL-012):** kein struktureller Deckel (60 % ≪ 100 % erreichbar); unter Unabhängigkeit P(Pointer-Tag)≈10⁻¹⁵ — Pointer-Tage können nur durch echte Kreuzkorrelation entstehen. Erwartete Pointer-Tage 2–6/Fenster: N-Floor 3 erreichbar, aber nicht garantiert (ehrliches Power-Risiko, T-gebunden). **Bestanden.**
- **Rechenaufwand:** CPU — 30 Serien × ~100 Tage, 1.000 Surrogate: Sekunden.
- **Selbstkill-/Restrisiko:** N_pointer=2–6 macht Stufe 2 power-schwach (harter N-Floor-DROP statt geschönt); zentriertes 11-Tage-Fenster überlappt Pre-Event-Fenster (Kontamination durch vollständigen dvol-Hold-out ausgeschlossen, Rest-Marktkorrelation bleibt Interpretationsfrage); OI-Lücken drücken n_avail (18er-Floor fängt ab). IC-DEND-2 (Zeitachsen-Integritätsprüfung) sollte VOR dem Lauf ausgeführt werden (Vorbedingung, kein Gate-Bestandteil).
- **Herkunft:** IC-DEND-1 (`dendrochronology-crossdating`), Feasibility bestätigt (PRE-SCREEN, 2026-07-07), Critic-Score 11/12, Fable-5-gehärtet (2026-07-07).
- **Status:** gehärtet, registry-fertig; Lauf NICHT gestartet.

---

### H-11 — AnEn-Vol-Regime-Forecast vs. HAR-RV (3-Tage-Horizont) *(aus IC-CLIM-1, `climatology-ensemble`)* — **gesperrt**

- **Markt-Zuordnung:** F (BTC/ETH-Perp; Ziel = Realized Vol, CLAUDE.md §5-Sonderrolle: Horizont ≥1 Tag).
- **Kernfrage/Hypothese:** Ein nichtparametrisches Analog-Ensemble (k=20 nächste historische Marktzustände, gewichteter Merkmalsabstand, Delle Monache et al. 2013) liefert für die realisierte Volatilität über die nächsten 3 Handelstage eine per CRPS messbar besser kalibrierte Verteilungsvorhersage als die HAR-RV-Punktschätzer-Baseline — regime-adaptiv per Konstruktion. **Abgrenzung zu H-02:** dort parametrisches Einzelmodell + R²-Anker; hier Verteilungsmaß CRPS, kein R², kein LightGBM.
- **Gegen-These / A-priori:** HAR-RV ist ein notorisch harter Benchmark. **Erwarteter Ausgang: DROP** (CRPSS<0,05 oder Ein-Fenster-Riss). Das WEITER ist bewusst schwer.
- **capital_free:** true — Mess-Gate. **Friktions-Sonderrolle (§5-Grund):** bei 3-Tage-Horizont und 2–5 % Tagesvol beträgt die erwartete kumulierte Bewegung (√3-Skalierung) ~350–870 bps gegen die 11–15-bps-Wand ≈ **25–75× über der Wand** — die einzige Größenordnungs-Umkehr im Programm. Monetarisierung (Vol-Targeting, Straddle) wäre NEUE **H-11b**, NICHT impliziert.
- **Datenbindung & Reifegrad:** **data-gated.** Real existiert heute nur EIN Fenster (Basis-Bestand ~100 Tage) — die ≥2-Fenster-Schwelle ist aktuell nicht erfüllbar (T-gebunden, prinzipiell erreichbar). **Entsperr-Bedingung (Teil der Pre-Registration, Schwelle wird NICHT gesenkt):** Manifest-Abfrage (DATASET.md §7) bestätigt lückenlose `done_days` für bybit `publicTrade` UND `rest.fundingRate`, BTC+ETH, mindestens über 2024-03-27…2026-03-26 (≥730 Tage zusammenhängend).
- **Datenströme & Fenster (OOS-Logik):** Streams bybit `publicTrade` (1-min-RV), `rest.fundingRate`. Tuning-Bereich L = 2024-03-27…2025-09-30 (LOO-CRPS-Gewichtstuning, danach eingefroren). W1 (Pre-Discovery-OOS, Backfill) = 2025-10-01…2026-03-26 (~177 Prognosetage). W2 = 2026-03-27…2026-06-30 (~96 Prognosetage, Basis-Bestand). W1∩W2=∅, W1/W2∩L=∅. 30-Tage-Embargo zwischen Analog-Kandidat und aktuellem Zustand.
- **Methodik (vorab fixiert):** Merkmalsvektor (5 Features, OI-Features exkludiert wegen 30-Tage-Rolling-Caveat): log RV_1d, log RV_5d, log RV_20d, Funding-Tagesmittel, Funding-5d-Trend. Gewichtet-euklidische Distanz auf z-standardisierten Features; Gewichte per LOO-CRPS auf L, Grid {0;0,5;1;1,5;2}⁵, danach eingefroren. k=20. Ziel: log annualisierte RV über t+1…t+3. Baseline: HAR-RV (Corsi) OLS, expanding Fit ≤t−30, monatlicher Refit. CRPS der Punktprognose = |Prognose−Beobachtung|. Rank-Histogramm/PIT nicht-urteilstragend.
- **Nullhypothese:** H0: mittlere CRPS-Differenz (HAR−AnEn) ≤0. Test: Block-Bootstrap (Blocklänge 5 Tage, 1.000 Reps, Diebold-Mariano-artig) je Symbol×Fenster.
- **Validierungs-Gate (wörtlich, bindend):** WEITER, wenn für mindestens ein Symbol ∈{BTC,ETH} in BEIDEN Fenstern: CRPSS = 1 − ΣCRPS_AnEn/ΣCRPS_HAR ≥0,05 UND Block-Bootstrap-p≤0,05 nach BH-FDR α=0,10 über F-ANEN.
- **Abbruchkriterium (wörtlich, bindend):** verfehlt ein Symbol CRPSS≥0,05 ODER p≤0,05 (FDR-korrigiert) in einem Fenster, scheidet es aus; erfüllt kein Symbol beide Fenster → DROP (keine k-/Gewichts-/Feature-Nachsuche). Kein Graubereich.
- **FDR-Familie:** **F-ANEN** (neu) — 2 Symbole × 2 Fenster = 4 Zellen, BH-FDR α=0,10 (k/Gewichte fixiert, bewusst keine Varianten-Familie).
- **Feasibility-Gegenprüfung (GL-012):** Scheiterpunkt ist heute nur die Fensterzahl (1<2, T-gebunden, kein struktureller Deckel). Nach Entsperrung: Analog-Bibliothek ≥550→~800 Zustände, k=20 sinnvoll besetzbar. CRPSS ohne strukturellen Deckel; Bootstrap-Power ausreichend (96–177 Differenzen je Fenster ≫30-Faustregel). **Bestanden (bedingt auf Entsperrung; heute korrekt data-gated).**
- **Rechenaufwand:** CPU — k-NN über ≤10³ Zustände × 5 Features, Bootstrap auf ≤200 Differenzen: trivial.
- **Selbstkill-/Restrisiko:** W1 liegt im Backfill (Datenqualitäts-Homogenität muss Manifest-/Lückenprüfung tragen); ~2 Jahre Historie decken evtl. nur 2–3 Vol-Regime ab (bewusst akzeptiert); Vol-Forecast-Nähe zu H-02 explizit abgegrenzt — ein WEITER rehabilitiert NICHT den gesperrten Vol-Stack (C-10/C-35/C-11/C-12 bleiben an H-02 gebunden).
- **Herkunft:** IC-CLIM-1 (`climatology-ensemble`), Feasibility bestätigt/data-gated (PRE-SCREEN, 2026-07-07), Critic-Score 11/12, Fable-5-gehärtet (2026-07-07).
- **Status:** gehärtet, registry-fertig; **gesperrt bis Entsperr-Bedingung erfüllt**; Lauf NICHT gestartet.

---

### H-12 — Cross-Exchange-Fragmentierungsmatrix (MP/IPR) *(aus IC-RMT-2, `econophysics-rmt`)*

- **Markt-Zuordnung:** F (BTC-/ETH-Perp auf Bybit, Binance, Deribit — N=6 Serien: 2 Symbole × 3 Börsen).
- **Kernfrage/Hypothese:** Die Korrelationsmatrix der Minuten-Returns über die 6 Cross-Exchange-Serien enthält jenseits des dominanten, delokalisierten „gemeinsamer-Preis"-Marktmodus (λ1≈N, IPR(v1)≈1/N) einen lokalisierten, börsenspezifischen Restmodus: λ2 signifikant über einer Ein-Faktor-Gauss-Null UND Eigenvektor lokalisiert (IPR≥0,40) UND über die Zeit stabil — Beleg für strukturelle (nicht wegarbitrierte) Fragmentierung.
- **Gegen-These / A-priori:** liquide Perps sind auf Minutenskala eng arbitriert; Rest liegt im Bulk der Ein-Faktor-Null. **Erwarteter Ausgang: DROP** (Fragmentierungs-Anteil unter 20 %).
- **capital_free:** true — reine Mess-/Explorationsfrage. Ein Cross-Exchange-Arbitragesignal wäre NEUE **H-12b**, NICHT impliziert — laut `friction_audit.md` voraussichtlich in der 80–500×-unter-der-Wand-Kategorie.
- **Datenbindung & Reifegrad:** Basis-Bestand 2026-03-27…2026-07-04: bybit/binance `publicTrade` (BTC/ETH), deribit `publicTrade` (BTC-PERPETUAL/ETH-PERPETUAL). **Sofort testbar.**
- **Datenströme & Fenster:** Minutenbars (Last-Price je 60s, Forward-Fill ≤1 Minute). Tagesfenster (UTC, T=1440, N=6, Q=240) als Analyseeinheit; Tag gültig bei ≥1.380/1.440 gültigen Minuten je Serie. W1 = 2026-03-27…2026-05-15, W2 = 2026-05-16…2026-07-04 (identisch H-09). Log-Returns je Serie je Tag z-standardisiert, Korrelationsmatrix C (6×6), Eigenzerlegung λ1≥…≥λ6, IPR(v)=Σvᵢ⁴.
- **Nullhypothese (zweistufig):** (a) Basis-Referenz: Marchenko-Pastur-Bulk (Q=240) mit Monte-Carlo-Gaussian-Wishart-Null (1.000 Ziehungen; nicht urteilstragend, TW-Asymptotik bei N=6 unzuverlässig). (b) Urteilstragende, strengere Null: Ein-Faktor-Gauss-Null je Tag kalibriert aus (λ1,v1) → 1.000 Replikationen → Nullverteilung von λ2 und IPR(v2). Tages-p = P(λ2_sim≥λ2_obs).
- **Validierungs-Gate (wörtlich, bindend):** WEITER, wenn in BEIDEN Fenstern gilt: (a) Anteil gültiger Tage mit λ2 nach BH-FDR α=0,10 über F-FRAG signifikant über der Ein-Faktor-Null ≥20 % UND (b) Median-IPR(v2) über den FDR-signifikanten Tagen ≥0,40 (delokalisiert wäre 1/6≈0,167) UND (c) an ≥70 % der FDR-signifikanten Tage entfällt die größte v2²-Börsenlast auf dieselbe Börse. **Validitäts-Vorbedingung (kein Gate-Bestandteil):** IPR(v1)≤0,25 an ≥90 % der gültigen Tage UND ≥35 gültige Tage je Fenster — sonst Lauf ungültig (kein Verdikt, zurück an IC-DEND-2-Ausrichtungsprüfung).
- **Abbruchkriterium (wörtlich, bindend):** DROP, wenn (a), (b) ODER (c) in einem Fenster verfehlt wird (hartes Ein-Fenster-Kriterium). Kein Graubereich, keine nachträgliche Anpassung von Bar-Raster, Tages-Gültigkeitsquote oder IPR-Schwelle.
- **FDR-Familie:** **F-FRAG** (neu) — alle Tages-λ2-Tests beider Fenster (~70–100 Tests), BH-FDR α=0,10.
- **Feasibility-Gegenprüfung (GL-012):** T/N=240≫10 (λ+≈1,133 bestätigt). Kein struktureller Deckel auf λ2 oder IPR(v2) (beide Schwellen strikt erreichbar, anders als H-07s √(N−1)-Deckel). MC-Aufwand ~10⁵ Simulationen: CPU-Minuten. **Bestanden.**
- **Rechenaufwand:** CPU — 6×6-Eigenzerlegungen, MC-Wishart-Ziehungen trivial; GPU brächte nichts.
- **Selbstkill-/Restrisiko:** Uhren-Asynchronität zwischen Börsen kann Schein-Restmoden erzeugen oder echte verwischen (Validitäts-Vorbedingung + IC-DEND-2 adressieren, eliminieren nicht vollständig); Deribit-Minutenlücken invalidieren Tage (35-Tage-Floor fängt ab); ein WEITER besagt nur Mess-Existenz von Fragmentierungsstruktur, keine Arbitrage-Aussage (H-12b-Doktrin).
- **Herkunft:** IC-RMT-2 (`econophysics-rmt`), Feasibility bestätigt (PRE-SCREEN, 2026-07-07), Critic-Score 10/12, Fable-5-gehärtet (2026-07-07).
- **Status:** gehärtet, registry-fertig; Lauf NICHT gestartet.

---

### H-13 — Tail-Form-Konsistenz: statistisches GPD-ξ vs. risikoneutrale Tail-Dichte *(aus IC-EVT-1, `evt-actuarial`)* — **gesperrt**

- **Markt-Zuordnung:** F (Returns-Seite: Bybit-Perp BTC/ETH) + O (risikoneutrale Seite: Deribit-Options-Surface).
- **Kernfrage/Hypothese:** Der aus realisierten 1-min-Renditen geschätzte GPD-Shape-Parameter ξ_P (POT, linker Tail) und der aus der Options-IV-Surface implizierte risikoneutrale Tail-Shape ξ_Q divergieren systematisch — gleiche Divergenzrichtung an zwei vol-regime-disjunkten Snapshot-Tagen, |ξ_P−ξ_Q|≥0,15. **Nicht-Redundanz zu C-33 (PARK):** C-33 misst den über ≥12 Monate gemittelten IV−RV-Level-Spread; hier wird die FORM (ξ) an einzelnen disjunkten Zeitpunkten verglichen.
- **Gegen-These / A-priori:** für regulär variierende Tails ist der Tail-Index aggregations-invariant, ein arbitrage-disziplinierter Optionsmarkt spiegelt die realisierte Tail-Form; Divergenz kann <0,15 oder über nur ~3 Wochen Live-Fenster instabil sein. **Erwarteter Ausgang: offen bis DROP.**
- **capital_free:** true — Konsistenz-/Divergenz-Messfrage ohne Round-Trip per Definition. Eine Tail-/Skew-Handelsfolge wäre NEUE **H-13b**, NICHT impliziert — Krypto-Options-Spreads liegen laut `friction_audit.md` deutlich über 15 bps.
- **Datenbindung & Reifegrad:** **data-gated.** Returns-Seite sofort nutzbar (Basis-Bestand); risikoneutrale Seite hängt am Live-Fenster `markprice.options` (Deribit, forward-only seit ~2026-06-16, ~3 Wochen). **Entsperr-Bedingung (Teil der Pre-Registration, wächst mit Kalenderzeit, Schwelle wird NICHT gesenkt):** am realen Feed existieren zwei Snapshot-Tage D1<D2 mit (i) |log(RV_5d(D1)/RV_5d(D2))|≥log(1,5), (ii) ≥10 Kalendertage Abstand, (iii) je Tag/Symbol ≥12 Strikes mit 0,01≤|Delta|≤0,5 im gewählten Tenor. **Deterministische Tageswahl (kein Cherry-Picking):** D1 = frühester Tag, der (iii) erfüllt; D2 = frühester spätere Tag, der (i)+(ii)+(iii) gegenüber D1 erfüllt.
- **Datenströme & Fenster:** Returns-Seite: trailing 60 Handelstage 1-min-Log-Returns je Snapshot-Tag. Options-Seite: Deribit `markprice.options`-Snapshot um 08:00 UTC; Tenor 20–45 DTE. Die beiden Snapshot-Tage ersetzen die ≥2-Fenster-Anforderung.
- **Methodik (vorab fixiert):** ξ_P: POT, u_P = empirisches 99,5 %-Quantil der 1-min-Verluste über trailing 60 Tage (fix, keine diskretionäre Mean-Excess-Wahl); GPD-MLE; SE via Block-Bootstrap (60 min Blöcke, 500 Reps). Hill-Schätzer als unabhängige Gegenprobe. ξ_Q: SVI-Fit auf IV-Smile → Breeden-Litzenberger-RND → GPD-Fit (PWM) auf RND-Exzess unterhalb 5 %-Quantil; SE via Strike-Bootstrap (500 Reps). Lognormal-Weibull-Mixture-RND nicht-urteilstragend.
- **Nullhypothese:** GPD-Form-Gleichheit H0: ξ_P=ξ_Q je Symbol×Tag; Δξ=ξ_P−ξ_Q; p aus kombinierter Bootstrap-Verteilung (Block-Bootstrap ξ_P × Strike-Bootstrap ξ_Q).
- **Validierungs-Gate (wörtlich, bindend):** WEITER, wenn für mindestens ein Symbol ∈{BTC,ETH} an BEIDEN Snapshot-Tagen: sign(Δξ) identisch UND |Δξ|≥0,15 UND Bootstrap-p≤0,05 nach BH-FDR α=0,10 über F-TAILSHAPE UND Hill-Gegenprobe widerspricht dem GPD-Vorzeichen nicht.
- **Abbruchkriterium (wörtlich, bindend):** DROP, wenn für alle Symbole an auch nur einem der beiden Snapshot-Tage |Δξ|<0,15 ODER p>0,05 (FDR-korrigiert) ODER das Divergenz-Vorzeichen zwischen D1/D2 kippt. Kein Graubereich; u_P, Tenor-Band, RND-Quantil und 0,15 nicht verhandelbar.
- **FDR-Familie:** **F-TAILSHAPE** (neu) — 2 Symbole × 2 Snapshot-Tage = 4 Zellen, BH-FDR α=0,10.
- **Feasibility-Gegenprüfung (GL-012):** ~432 Exzedenzen → SE(ξ_P)≈0,06–0,08; SE(ξ_Q)≈0,08–0,12; kombinierte SE≈0,10–0,14 → 0,15-Schwelle ~1,1–1,5 SE, bei literaturüblicher Divergenz (0,2–0,4) klar detektierbar; kein struktureller Deckel. Heutiger Blocker allein die unverifizierte Existenz zweier Snapshot-Tage (T-gebunden). **Bestanden (bedingt auf Entsperrung).**
- **Rechenaufwand:** CPU — genpareto-Fits, SVI-Kalibrierung, 2×500 Bootstrap-Reps: Sekunden bis Minuten.
- **Selbstkill-/Restrisiko:** RND-Flügel hängen an illiquiden Quotes (Strike-Floor mindert, Rest-Rauschen bleibt größter Unsicherheitsfaktor); Horizont-Brücke 1-min-Tail vs. ~30-Tage-RND stützt sich auf Aggregations-Invarianz (theoretisch fundiert, nur näherungsweise bei Semi-Heavy-Tails, deshalb 0,15-Schwelle großzügig gesetzt); nur ~3+ Wochen Live-IV deckt maximal 2 Regime ab — ein WEITER ist Zwei-Punkt-Existenzaussage, keine Regime-übergreifende Verallgemeinerung (spätere Erweiterung, vgl. PARK-Eintrag IC-RMT-4).
- **Herkunft:** IC-EVT-1 (`evt-actuarial`), Feasibility bestätigt/data-gated (PRE-SCREEN, 2026-07-07), Critic-Score 9/12, Fable-5-gehärtet (2026-07-07).
- **Status:** gehärtet, registry-fertig; **gesperrt bis Entsperr-Bedingung erfüllt**; Lauf NICHT gestartet.

---

## 4. Sequenzierungs-Empfehlung

**Reihenfolge:** zuerst die 3 sofort testbaren Hypothesen — **H-09 (Bunching), H-10 (Pointer-Days), H-12 (Fragmentierung)** — vor den 2 data-gated Einträgen **H-11 (AnEn-Vol)** und **H-13 (Tail-Form)**, deren Entsperr-Bedingungen (Manifest-Nachweis bzw. Snapshot-Tag-Existenz am Live-Feed) außerhalb dieser Recherche-Runde liegen und zuerst geprüft werden müssen.

**FDR-Über-Familien-Hinweis (bindend, aus `hardened_hypotheses.md` §5 übernommen):** Jede der 5 Hypothesen läuft in ihrer eigenen, neu registrierten Familie (F-BUNCH, F-POINTER, F-ANEN, F-FRAG, F-TAILSHAPE — kollisionsfrei zu allen bestehenden Familien F-S3/F-VOL/F-CFAR/F-LEADLAG(-TRADE)/F-OFI(-INV)(-TRADE)/F-ENTROPY/F-XMR(-RANK)/F-WAVE2). **Kohorten-Regel:** Laufen ≥2 der sofort testbaren Hypothesen (H-09/H-10/H-12) als gemeinsame Kohorte, ist VOR jenem Lauf eine Über-Familie **F-XDOM1** (zweite BH-FDR α=0,10 über die Familien-Survivor, analog F-WAVE2) durch den `registry-keeper` zu registrieren; F-WAVE2 selbst bleibt abgeschlossen und wird NICHT erweitert.

---

## 5. Verbindliche Schluss-Klausel

Diese Runde erzeugt **KEINE GL-Verdikte** — nur Pre-Registrations. Die GL-Nummerierung bleibt bei GL-013 (letzter Verdikt, `PROGRAM_FINAL_REPORT.md`); **GL-014ff. sind für den Moment reserviert**, in dem eine der 5 Hypothesen tatsächlich gegen Daten geprüft wird (Implementierung), das ist explizit NICHT Teil dieser Recherche-Runde (CLAUDE.md §8, `registry-keeper.md`). Die Implementierung (Backtest-Pipeline für H-09..H-13) ist eine spätere, separate Welle — kein Code, kein Datenlauf, keine Live-Berührung hat in dieser Runde stattgefunden.

**capital_free=true für alle 5 Einträge.** Jede Tradability-Folge (H-09b, H-10b, H-11b, H-12b, H-13b) ist eine NEUE, separat vorzuregistrierende Hypothese mit eigener Friction-Wand-/Latenz-Konfrontation, durch kein Mess-WEITER dieser Runde impliziert (H-04→H-04b-Doktrin, `PROGRAM_FINAL_REPORT.md` §2 lit. e).

*Ende CROSSDOMAIN_PRD.md*
