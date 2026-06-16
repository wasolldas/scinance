# Entscheidungs-Log (DEC-xx)

> Format: DEC-xx · Frage · Optionen · Entscheidung · Begründung · Rückbauweg
> Keine Entscheidung ohne Eintrag, kein Eintrag ohne Entscheidung. (CLAUDE.md Autonomie-Protokoll §3)

---

### DEC-01 · Wo liegt die Verfassung?
- **Frage:** FINAL_PRD.md lag in `edge-reconciliation/results/`, Framework erwartet Repo-Root.
- **Optionen:** (a) Kopie in Root, Original bleibt; (b) Move; (c) Symlink.
- **Entscheidung:** (a) Kopie in Root.
- **Begründung:** Reconciliation-Artefakte bleiben als abgeschlossener, in sich konsistenter Run unangetastet (Audit-Trail); Root-Kopie ist die Arbeits-Verfassung. Reversibelste Option.
- **Rückbauweg:** Root-Kopie löschen; Original unverändert.

---

### DEC-02 · Output-Pfad der Scinance-2.0-Gate-Läufe (replay_all/evaluate)
- **Kontext:** WP-1 (P1/E-15-Auswertung). `scripts/replay_all.py` schreibt per Default nach `edge_research_framework/results/` (ein Framework-/Doku-Verzeichnis); Survey §4.8 markiert das als DEC-Kandidat. Das Auswertungs-Skript braucht einen stabilen, parametrisierbaren Ergebnis-Eingang.
- **Optionen:** A) Default-Output von `replay_all.py` umbiegen (Bestands-CLI ändern). B) Default unangetastet lassen; das neue `evaluate`-Skript bekommt `--results-path`/`--trades-path` mit Default = bestehender Pfad, plus optionalem `--input-dir` für Scinance-2.0-Läufe nach `handoff_local/results/`.
- **Entscheidung:** B. Bestands-CLI bleibt unverändert; neues Auswertungs-Tooling ist pfad-parametrisiert (Default = `edge_research_framework/results/replay_all_results.json` + `trades_all.csv`), die T2/T3-Runner setzen den Pfad explizit auf `handoff_local/results/`.
- **Begründung:** PRD/Survey schützen Bestands-Verhalten (kein Touch an Schutzgut-naher Replay-CLI); Parametrisierung ist additiv und voll reversibel. Kein Bestands-Konsument bricht.
- **Rückbauweg:** Neues Skript löschen; nichts am Bestand wurde geändert.

---

### DEC-03 · Platzierung des CFAR-Moduls (C-31): Pipeline-Layer vs. research-Paket
- **Kontext:** WP-3 (P4/C-31). Survey §2.P4 nennt zwei Optionen: `layers/l4_pattern/m27_cfar_cyclo.py` (M-xx-Pipeline-Konvention) ODER eigenes Analysepaket `src/bybit_edge/research/c31_cfar/`. C-31 ist laut PRD §3 ein Standalone-Falsifikations-Gate, KEIN Pipeline-Glied (kein `process_ticker`-Bedarf).
- **Optionen:** A) `m27_cfar_cyclo.py` als BaseModule im Pipeline-Baum — folgt M-xx-Konvention, zieht aber Pipeline-/Aggregator-Verdrahtung + Registrierung nach sich (mehr Bestands-Touch, schwerer rückbaubar). B) `src/bybit_edge/research/c31_cfar/` als isoliertes Paket (Cyclic-Spectrum-Schätzer, CFAR-Peak-Detektor, Surrogate-Test) + eigener read-only Replay-Driver über die `trades`-Tabelle.
- **Entscheidung:** B (research-Paket). Neues Verzeichnis `src/bybit_edge/research/` als Heimat für Scinance-2.0-Standalone-Analysemodule (auch WP-4 nutzt es, s. DEC-04).
- **Begründung:** PRD bezeichnet C-31 ausdrücklich als standalone/schnell-DROP-bar; Repo-Konvention (M-xx) ist für Pipeline-Glieder gedacht, nicht für Falsifikations-Gates. research-Paket ist die reversibelste Option (ein Verzeichnis löschen = vollständiger Rückbau, kein Pipeline-/Aggregator-Umbau). Schnittstelle bleibt Welle-2-fähig (CS-07-Footprint kann andocken).
- **Rückbauweg:** Verzeichnis `src/bybit_edge/research/c31_cfar/` + Tests löschen; Pipeline und Aggregator wurden nie berührt.

---

### DEC-04 · C-42-Repro: LightGBM-Dependency vs. sklearn-GBM
- **Kontext:** WP-4 (P2/C-42). `lightgbm` ist weder in `pyproject.toml` noch in der Sandbox vorhanden (Survey §2.P2); die Original-Kestrel-Baseline (research_notes) nutzt `kestrel.training.lightgbm_baseline`. Reproduktionsziel ist die Volatilitäts-Regression (`log(realised_vol_60m)`, Test-R² 0.249), NICHT Direction.
- **Optionen:** A) `lightgbm` als neue optionale Dependency (Repo-Konvention: schwere ML/DL-Deps liegen in `[project.optional-dependencies]`-Extras wie `gpu`/`foundation`/`tuning`) — bleibt nah am Original-Befund, neuer Extra `vol`. B) `sklearn.ensemble.HistGradientBoostingRegressor` (scikit-learn ist auch nicht installiert, aber leichter; KEIN Original-Algorithmus → Reproduktions-Treue fraglich).
- **Entscheidung:** A. Neuer Extra `[project.optional-dependencies].vol = ["lightgbm>=4.0", "scikit-learn>=1.4"]` (sklearn nur für Metrik-/Split-Hilfen, GBM bleibt LightGBM). Modul über einen schmalen `model`-Adapter so kapseln, dass der Estimator austauschbar bleibt.
- **Begründung:** PRD §3 verlangt „C-42-**Reproduktion**" — Reproduktion eines LightGBM-Befundes erfordert LightGBM, sonst misst man ein anderes Modell und das Gate (OOS-R² ≥ 0.15, QLIKE schlägt HAR-RV) wird unvergleichbar. Repo-Konvention für schwere Deps ist der Extra-Mechanismus (reversibel: Extra entfernen). Der Adapter hält B als Notausgang offen, falls LightGBM lokal nicht baubar ist.
- **Rückbauweg:** `vol`-Extra aus `pyproject.toml` streichen, `research/c42_rv/` löschen; Bestands-Deps unverändert. Bei Build-Problem: Adapter auf `HistGradientBoostingRegressor` umstellen (1 Zeile), als DEC-04a protokollieren.

---

### DEC-05 · Heimat des C-42-Repro-Codes
- **Kontext:** WP-4. Survey §2.P2 schlägt `src/bybit_edge/research/c42_rv/` oder `vol/` vor; PRD §7 sagt „C-42 muss in die Pipeline geholt werden" (lebt heute außerhalb des src-Baums).
- **Optionen:** A) `src/bybit_edge/research/c42_rv/` (konsistent mit DEC-03 research-Paket). B) Top-Level `vol/`-Paket.
- **Entscheidung:** A — `src/bybit_edge/research/c42_rv/` (Feature-Engineering 36 Features, purged-WF-Splitter, FDR/BH, QLIKE, LightGBM-Adapter), CLI in `scripts/c42_repro.py`. Datenzugriff read-only via `PersistenceLayer.query_kline`.
- **Begründung:** Ein gemeinsames `research/`-Dach für Scinance-2.0-Standalone-Module (C-31, C-42) hält den Bestands-Pipeline-Baum sauber und ist als Ganzes reversibel. „In die Pipeline holen" (PRD §7) = in den versionierten `src`-Baum + Tests + CLI, nicht zwingend ins Layer-/Aggregator-Wiring.
- **Rückbauweg:** `research/c42_rv/` + `scripts/c42_repro.py` löschen; Bestand unberührt.

---

### DEC-06 · Recording-Engine: eigene Datei/Tabellen statt Collector-Umbau
- **Kontext:** WP-2 (P3/C-36). Survey §2.P3 + §4.6: `insurance.USDT`/`adlAlert` passen nicht ins `{symbol}`-Topic-Template des Bestands-Collectors; Options-Tickers liegen auf einer anderen WS-URL.
- **Optionen:** A) `STREAMS`/`_dispatch` im Bestands-Collector erweitern (Schutzgut-naher Umbau). B) Eigene Recording-Engine `src/bybit_edge/recorder/recording_engine.py` neben dem Collector, eigene Tabellen (`rpi_orderbook`, `insurance_pool`, `adl_alerts`, `premium_index_kline`, `option_tickers`) und eigener Parquet-Unterpfad `data/parquet/recording_f0/` + Ringpuffer-Storage-Deckel.
- **Entscheidung:** B. Collector (`ws_collector.py`) und Bestands-Schema (`db.py`-Tabellen) bleiben unangetastet; die Engine wird additiv aufgebaut und ist streamfähig erweiterbar (Welle-2-Andockpunkt für C-39/C-40/C-33-IV).
- **Begründung:** Schutzgut 1 (laufender Collector) und Schutzgut 3 (Bestands-Parquet) sind nicht verhandelbar; additive Engine + neue Pfade brechen nichts und sind per Datei-/Tabellen-Löschung rückbaubar. Deckt PRD §3-Deckel + Sunset direkt im neuen Modul ab.
- **Rückbauweg:** `recorder/`-Modul, neue Tabellen-DDL und `data/parquet/recording_f0/` entfernen; Collector/Schema nie verändert.

---

### DEC-07 · Storage-Deckel-Default der Recording-Engine (Ratifizierung)
- **Kontext:** WP-2. PRD §3 verlangt eine „fixe GB-Obergrenze, ringpuffer-/rotationsbasiert", nennt aber KEINE Zahl. Der builder hat `DEFAULT_CAP_GB=50.0` als dokumentierte Annahme gesetzt, `--cap-gb`-überschreibbar.
- **Optionen:** A) 50 GB Default (≈ Wochen RPI+IV-Ticks, passt auf übliche Consumer-SSD-Reserven). B) Kleinerer Default (10 GB, konservativer, evtl. zu kurzer Ringpuffer für den Sunset-Review-Horizont 90 Tage). C) Kein Default, Pflicht-Flag (verletzt Ein-Befehl-Runner-Regel der Testpyramide).
- **Entscheidung:** A — 50 GB Default, ratifiziert.
- **Begründung:** PRD-stumm → reversibelste sinnvolle Option; CLI-überschreibbar; Sunset-Review (90 Tage) braucht genug Ringpuffer-Tiefe; C verletzt CLAUDE.md-Runner-Regeln.
- **Rückbauweg:** Konstante ändern oder `--cap-gb` im Runner setzen; kein struktureller Umbau.

---

### DEC-08 · Recorder-Streams: Per-Spec-Subscribe + Phantom-Markierung statt Löschung
- **Kontext:** DIAG2 (2026-06-12). Der T2-Retest des Recorders zeigt im Log eindeutig: `[linear] SUBSCRIBE/REQUEST REJECTED: ret_msg='error:handler not found,topic:adlAlert'`. Bybit lehnt die GESAMTE Subscribe-Request auf der Linear-WS ab, weil ein einziges Topic (`adlAlert`) auf diesem Endpoint nicht existiert (PRD-fable5-Phantom, INC-04/INC-06-Lektion bestätigt). Folge: `rpi_orderbook` und `insurance.USDT` verlieren als Kollateral ihre Subscription, obwohl die Topics vermutlich gültig sind. Ursachen-Code: `recording_engine.run()` bündelte alle Topics einer Transport-Gruppe in EINE Subscribe-Request (all-or-nothing).
- **Optionen:**
  - A) `adl_alerts`-StreamSpec komplett aus `default_stream_specs` entfernen (klein, aber löscht Wissen, kein Audit-Trail; Rückbau bedeutet Re-Implementierung inkl. Normaliser/Schema).
  - B) `phantom: bool = False`-Feld auf `StreamSpec`; phantom-Specs werden beim Run mit WARN geskippt, Schema/Writer/Normaliser bleiben als Wissensspeicher; zusätzlich JEDE StreamSpec als EIGENE Subscribe-Request senden (per-spec subscribe) → ein abgelehntes Topic killt nur seinen eigenen Stream.
  - C) Nur per-spec subscribe, `adl_alerts` unverändert lassen — das Log würde den ERROR weiterhin alle 10 s liefern, ohne Audit-Trail-Entscheidung.
- **Entscheidung:** B. `StreamSpec.phantom: bool = False` eingeführt; `adl_alerts` mit `phantom=True` markiert (Bezug auf Bybit-Antwort 2026-06-12). Die Subscribe-Logik in `_run_ws_transport` sendet jetzt eine Request pro StreamSpec (`_subscribe_per_spec`); phantom-Specs werden mit WARN geskippt. Transports, deren Specs ALLE phantom sind, öffnen gar nicht erst eine Verbindung.
- **Begründung:** Reversibelste Option mit Audit-Trail. Schema (`STREAM_SCHEMAS["adl_alerts"]`), Normaliser (`_norm_adl_alert`), Writer und Tests bleiben unangetastet — falls Bybit das Topic je dokumentiert oder ein anderer Endpoint es liefert, reicht ein `phantom=False` zur Re-Aktivierung. Per-spec subscribe ist die strukturelle Behebung der Kollateral-Klasse von Bugs: kein einzelner abgelehnter Topic-Name kann mehr Sibling-Streams mitreißen. Beide Schritte sind isoliert testbar (siehe `TestPerSpecSubscribeAndPhantom`).
- **Rückbauweg:** `phantom=True` auf `adl_alerts` entfernen → Stream wird wieder subscribed. `_subscribe_per_spec` wieder durch `_subscribe(ws, all_topics)` ersetzen → all-or-nothing-Verhalten zurück. Beides 1-Zeilen-Reverts.
- **Was DEC-08 NICHT entscheidet:** Den Status der Options-WS (`tickers.BTC`/`tickers.ETH`). Die Subscribe-Form ist im Code als korrekt dokumentiert (`repo_survey §2.P3`: Underlying-Topic auf der Option-WS liefert ALLE lebenden Kontrakte für dieses Underlying). Beobachtung: success=true im T2-Log, aber 0 Frames in 5 min. Hypothese: kein Trading-Volume in dem Fenster, oder die Push-Frequenz ist event-getrieben. → braucht eigenen T2-Retest mit verlängertem `RECORDER_SMOKE` (20 min statt 5 min) und ist KEINE DEC-08-Sache.

---

### DEC-09 · C-31-CFAR: Fenster-Tick-Obergrenze (H-03 lief nie durch — 5400s-TIMEOUT 5/5)
- **Kontext:** Overnight 2026-06-14. `C42_WF` lief 5/5 OK (--db-copy-Fix wirkt), aber `C31_CFAR` lief auf ALLEN 5 Symbolen in den 5400s-Timeout (`scinance2-impl/handoff_local/results/upload_20260615/overnight_20260614_150830/C31_CFAR_*.err.log`): DB-Copy + Korrupt-Zeilen-Drop liefen sauber, danach 5400s komplett stumm. Root-Cause im Code verifiziert: `split_windows()` teilt die GESAMTE Tick-Serie eines Symbols in `n_windows` (Default 2). Die Bestands-`trades`-Tabelle des Live-Collectors ist tage-/wochentief (viel älter als die 8h-Aufnahme), also spannt jedes Fenster Tage. `bin_counts()` rastert über die ZEITspanne des Fensters bei `bin_dt_ms` (10/50/100ms) → Millionen bis Milliarden Bins (`MAX_BINS=1e9` fängt nur den Extremfall). Die F-CFAR-Familie = **3 Varianten** (`DEFAULT_BIN_GRID_MS` 10/50/100ms × 1 Threshold 6.0) × `surrogate_test(n_surrogates=200)`, jedes Surrogate baut Timeline + `bin_counts` + SCD neu → 2 Fenster × 3 Varianten × (1+200) ≈ 1206 volle SCD über riesige Arrays. Explosion. Zusätzlich: KEIN Progress-Logging — die err.log war 5400s stumm, ein Hang war nicht diagnostizierbar.
- **Frage:** Wie wird der CFAR-Lauf je Symbol rechenbar gemacht, ohne die vorregistrierten H-03-Torpfosten zu verschieben (Registry-Disziplin §8.2/§8.3: keine Post-hoc-Schwellen-Anpassung)?
- **Optionen:**
  - A) **Deterministische Tick-Obergrenze je Fenster** (`WINDOW_MAX_TICKS=150_000`): die jüngsten `n_windows × max_ticks` Ticks der chronologisch sortierten Serie nehmen, in `n_windows` disjunkte zusammenhängende Fenster teilen. Daten-Scoping, KEINE Schwellen-Änderung.
  - B) **Dauer-Cap je Fenster** (z.B. „letzte N Minuten"): ebenfalls Daten-Scoping, aber bei stark schwankender Tick-Rate ist die Last (= Tick-Anzahl × Bins) NICHT garantiert beschränkt; auf illiquiden Phasen evtl. zu wenig Ticks, auf liquiden zu viele.
  - C) **Nur `n_surrogates` reduzieren:** verändert die Auflösung des Surrogate-Tests (p-Granularität) → schwächt den vorregistrierten Test, faktisch Schwellen-Verschiebung (Registry §8.3-Verstoß). Verworfen.
  - D) **Nur optimieren (vektorisieren/cachen):** verschiebt die Wand, behebt die VERLETZTE Stationaritätsannahme tage-langer Fenster nicht, und bleibt bei Milliarden-Bin-Fenstern letztlich intractable.
- **Entscheidung:** **A — `WINDOW_MAX_TICKS = 150_000`** (neue Konstante in `cyclic_spectrum.py` bei `MAX_BINS`; CLI-Flag `--max-ticks-per-window`, Default = Konstante; durchgereicht `scripts/c31_cfar.py` → `run()` → `split_windows()`). Logik: jüngste `n_windows × max_ticks` Ticks der sortierten Serie, geteilt in `n_windows` disjunkte zusammenhängende Fenster ≤ `max_ticks`; bei weniger Ticks unveränderte gleichmäßige Teilung. Plus Fix 2: Progress-Logging je Fenster/Variante/Surrogate-Schub auf stderr; Pro-Symbol-Timeout in den Runnern von 5400s → 1800s. Die Span-Sanity-Prüfung in `run()` läuft jetzt NACH dem Cap auf den gekappten Fenstern.
- **Begründung:** Reversibelste Option mit korrektem Methoden-Fundament. Zyklostationarität setzt (Quasi-)Stationarität INNERHALB des Fensters voraus; die H-03-Hypothese zielt auf HFT-Skala-Zyklen (Gate: Lead > 50 ms, sub-sekündlich). ~150k Ticks spannen auf liquiden Symbolen zig Minuten — reichlich für sub-sekündliche Zyklik —, während ein tage-langes Fenster die Stationaritätsannahme VERLETZT und obendrein nicht rechenbar ist. Der Bound ist also methodisch KORREKTER, nicht nur schneller. „Jüngste Ticks" ist deterministisch (keine diskretionäre Wahl) und bleibt im Registry-Wortlaut „deterministisch-chronologisch, ≥2 disjunkte Fenster". **Die Gate-Schwellen p≤0.05 / Lead>50ms / Edge>11bps sowie `n_surrogates=200` und BH-FDR α=0.10 bleiben EXAKT wie registriert** — hinzugefügt wird nur ein vorher unspezifizierter Daten-Scoping-Parameter, KEINE Torpfosten-Verschiebung. B verworfen (Last nicht garantiert beschränkt), C verworfen (schwächt den registrierten Test = §8.3-Verstoß), D verworfen (behebt Stationaritätsverletzung nicht).
- **Rückbauweg:** `WINDOW_MAX_TICKS` sehr hoch setzen ODER `--max-ticks-per-window` auf einen riesigen Wert (kein Cap) → ursprüngliches Voll-Serien-Splitten zurück. Konstante + Flag + die Cap-Zeilen in `split_windows()` entfernen = vollständiger Rückbau; `run()`/Surrogate-Statistik unverändert. Progress-Logging ist rein observativ und kann separat entfernt werden.

---

### DEC-10 · C-17/C-41 Lead-Lag-Mess-Gate: Methoden-/Parameter-Festlegung (H-04, KAPITALFREI)
- **Kontext:** Welle-2-WP, neues Paket `src/bybit_edge/research/c17_c41_lead_lag/`. H-04 verlangt ein kapitalfreies Mess-Gate fuer gerichteten Informationsfluss BTC->Alt (Transfer-Entropy ODER Wavelet-Coherence-Phasen-Lead) gegen eine Surrogate-Null, p<=0.05 nach BH-FDR alpha=0.10 ueber F-LEADLAG, Existenz in >=2 disjunkten Fenstern, Lead-Symbol-Stabilitaet. PRD §4 / Registry nennen KEINE konkreten Methoden-Parameter (Resample-Raster, TE-Diskretisierung, Surrogate-Form, Fenster-Tick-Cap) — diese sind vorab-unspezifizierte Implementierungs-Parameter, KEINE Gate-Schwellen.
- **Frage:** Welche (a) Primaer-/Sekundaer-Achse, (b) Surrogate-Null, (c) Return-Diskretisierung, (d) Resample-Raster, (e) Fenster-Tick-Obergrenze waehlen, ohne die vorregistrierten H-04-Torpfosten zu beruehren (Registry-Disziplin §8.3)?
- **Optionen & Entscheidung:**
  - **(a) Achsen:** Primaer = **Shannon-Transfer-Entropy** (C-17), robust ohne scipy-Spezial-Deps, direktional in einer einzigen Statistik; Sekundaer = **numpy-FFT-Morlet-Wavelet-Coherence-Phasen-Lead** (C-41). BEIDE zaehlen in F-LEADLAG. Verworfen: nur eine Achse (Registry verlangt explizit C-17 ∧ C-41 in der Familie).
  - **(b) Surrogate-Null:** **zirkulaerer Block-Shift der Quell-("Leader")-Serie relativ zur Folger-Serie** (Roll um zufaelligen Offset >= 5% der Laenge). Zerstoert die gerichtete Kreuz-Kopplung, erhaelt Marginale UND Autokorrelation beider Serien exakt. Verworfen: Phase-Shuffle (zerstoert auch die Within-Series-Struktur -> testet das Falsche fuer Lead-Lag); reine Permutation (zerstoert Autokorrelation). N=200 Default (analog H-03-Nachtrag).
  - **(c) TE-Diskretisierung:** **Equal-Frequency-Quantil-Binning, n_bins=3 Default** (`DEFAULT_N_BINS`). 3 Bins (down/flat/up) haelt das Joint-Histogramm n_bins^3 klein genug fuer Plug-in-TE aus wenigen tausend Bars bei geringem Bias; equal-frequency ist robust gegen die Heavy-Tails von Krypto-Returns. CLI `--n-bins` ueberschreibbar; jede Bin-Variante zaehlt einzeln in F-LEADLAG.
  - **(d) Resample-Raster:** **1000 ms Default** (`DEFAULT_GRID_MS`), beide Symbole auf ein gemeinsames Bar-Raster ueber ihren ueberlappenden Zeitraum (last-tick/step-sampling, strikt rueckwaerts -> kein Look-ahead). 1s ist fein genug fuer die 30-60s-HFT-Skala der H-04-Hypothese, grob genug fuer stabile TE-Histogramme. CLI `--grid-ms` ueberschreibbar.
  - **(e) Fenster-Tick-Obergrenze:** **WINDOW_MAX_TICKS=150_000 je Symbol je Fenster** (analog DEC-09): die juengsten n_windows×max_ticks Ticks je Symbol, dann gemeinsamer Zeitraum in n_windows disjunkte Gleich-Zeit-Slices. Deterministisch-chronologisch, keine diskretionaere Wahl. Begruendung wie DEC-09: Stationaritaet + Rechenbarkeit, KEINE Schwellen-Verschiebung. CLI `--max-ticks-per-window` ueberschreibbar.
- **Begruendung:** Reversibelste sinnvolle Optionen wo PRD/Registry stumm sind; alle Parameter sind CLI-Flags mit dokumentierten Defaults. Die Gate-Schwellen (p<=0.05, BH-FDR alpha=0.10, >=2 Fenster, Lead-Stabilitaet, n_surrogates=200) bleiben EXAKT wie in H-04 registriert — DEC-10 fixiert nur vorher unspezifizierte Methoden-/Scoping-Parameter. **KAPITALFREIHEIT eingehalten:** kein bps/Edge/PnL/Friction-Code im Modul (Mess-Existenz only; Tradability waere H-04b).
- **Lead-Symbol-Bestimmung:** Das Lead-Symbol je Fenster wird aus der **direktionalen TE-Achse** abgeleitet (Quelle der staerksten FDR-signifikanten TE-Variante), da die WCOH-Coherence-Magnitude symmetrisch und ihr Vorzeichen-Lead rauschanfaellig ist; WCOH-Lead-Vorzeichen nur als Fallback wenn keine TE-Variante signifikant. Smoke-verifiziert (injizierter Lead -> korrektes Lead-Symbol + Lag).
- **Rueckbauweg:** Paket `c17_c41_lead_lag/` + `scripts/c17_c41_lead_lag.py` entfernen = vollstaendiger Rueckbau (standalone, NICHT in Live-Pipeline/replay_backtester verdrahtet, read-only ueber `trades`). Einzelne Defaults via Konstanten/CLI-Flags aenderbar; Bestands-Code unangetastet.
