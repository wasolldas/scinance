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
