# Adversarial-Audit H-17 (C-17-VENUE) — Venue-Fingerprint (Contrastive-Embedding, F-VENUE)

- **Auditor:** frische, unabhaengige Session (Code nicht selbst geschrieben; einziges
  Qualitaetsgate vor dem ersten GPU-Lauf auf der lokalen RTX-Maschine des Nutzers)
- **Datum:** 2026-07-10
- **Gepruefte Artefakte:** `src/bybit_edge/research/c17_venue/{__init__,features,encoder,contrastive,redundancy,stats,driver}.py`,
  `scripts/c17_venue.py`, `scinance2-impl/handoff_local/{run_h17.ps1,run_h17.sh,README_H17.md}`,
  `tests/unit/test_c17_venue.py` — alle vollstaendig gelesen. Ground Truth:
  `scinance2-impl/state/hypothesis_registry.md` (Abschnitt „### H-17", Welle 5),
  `scinance2-impl/state/GPU_RESEARCH_SCAN_2026-07-09.md` (Abschnitt „4. VENUE-FINGERPRINT"),
  `scinance2-impl/CLAUDE.md`, sowie — als vorgeschriebener Redundanz-Referenzpunkt —
  `src/bybit_edge/research/c12_frag/driver.py` (`run()` volltextgelesen).
- **Tests selbst ausgefuehrt:**
  `PYTHONPATH=src python3 -m pytest tests/unit/test_c17_venue.py tests/unit/test_c12_frag.py -q`
  → **26 passed in 66.21 s** (2026-07-10, diese Sandbox; 18 c17_venue + 8 c12_frag).
  Zusaetzlich eigene Gegenrechnungen: Spearman-rho-Eigenkopie numerisch gegen `scipy.stats.spearmanr`
  auf 5 synthetischen Reihen inkl. Ties abgeglichen (max. Abweichung 1.1e-16, floating-point-exakt);
  `git status`/`git diff --stat` gegen `c12_frag`-Pfade geprueft — **keine Aenderung** (Regressionscheck
  bestanden: H-17 hat den c12_frag-Code nicht angefasst).

---

## Verdikt: **PASS-WITH-NOTES**

Kein kritischer Defekt gefunden. Das Compute-Gate ist tatsaechlich hart verdrahtet (kein Lauf
ohne echtes CUDA-Device UND Batch>=2048 kann `weiter_indication=True` liefern), das
Redundanz-Gate gegen c12_frag liest exakt die reale `c12_frag.driver.run()`-JSON-Struktur
(`windows[].days[].{date,analyzed,lambda2,ipr_v2}`) und erzwingt `|rho|>=0,6` als hartes DROP
unabhaengig von der Accuracy, die Permutations-Null ist nachweislich ECHTES Retraining (kein
Frozen-Model-Shuffling, per fit()-Call-Zaehler getestet), Leave-One-Symbol-Out hat kein
Symbol-Leck, und beide Test-Suiten (c17_venue + c12_frag) sind gruen — H-17 hat den
c12_frag-Code nicht veraendert. Ein MEDIUM-Befund (Batch-Groessen-Gate prueft nur den
angeforderten, nicht den tatsaechlich erreichten Batch je Retraining) und mehrere LOW/INFO-Befunde
unten — keiner davon blockiert einen unbeaufsichtigten T3-Lauf, aber der MEDIUM-Befund sollte vor
dem ~1-2-Tage-GPU-Lauf gefixt werden, weil er GENAU die vom Nutzer als hoechste Prioritaet
benannte Compute-Gating-Frage betrifft (auch wenn das Realrisiko angesichts der Panelgroesse
gering ist, s. unten).

---

## Spec-Treue-Tabelle (Registry H-17 → Code)

| Konstante / Schwelle | Registriert | Code | Match? |
|---|---|---|---|
| Panel: 10 Nodes = 5 Symbole x {Bybit, Binance}, publicTrade only | woertlich | `DEFAULT_SYMBOLS` (5), `DEFAULT_EXCHANGES=("bybit","binance")` (features.py:49-52); `run()` erzwingt `len(venue_order)==2` | JA |
| 5-Min-Event-Fenster, 4 Kanaele (Inter-Trade-Dauer, Log-Trade-Size, Aggressor-Sign, Tick-Direction) | woertlich | `WINDOW_MINUTES=5`, `CHANNELS` exakt diese 4 in dieser Reihenfolge (features.py:58-75); `extract_raw_channels`/`build_node_windows` | JA |
| Pro-Tag-Quantil-Normalisierung je Kanal/Node | verdikt-kritisch | `per_day_quantile_normalize` — Rang -> u=rank/(n+1) je (Tag, Kanal) EINES Nodes (features.py:92-138) | JA |
| Encoder: Temporal-CNN/Transformer, InfoNCE (Positive=gleicher Node andere Zeit, Negative=voller Batch), Batch>=2048 | woertlich | `TemporalCNN` (dilatierte Conv1d-Kette) + Masked-Mean-Pool; `infonce_loss_np`/Torch-Trainer implementieren multi-positive SupCon-Loss mit Node-Identitaet als Label; `BATCH_SIZE_MIN=2048` hart geprueft (contrastive.py) | JA |
| Frozen-Linear-Probe fuer Venue-Identitaet | woertlich | `train_linear_probe`/`probe_predict`, numpy-Logistic-Regression auf eingefrorenen Pre-Projection-Embeddings (contrastive.py:192-243) | JA |
| Leave-One-Symbol-Out, 5 Folds, Test = letzte 3 Wochen des ausgelassenen Symbols | woertlich | `build_loso_folds`: `TEST_WEEKS=3`→`TEST_DAYS=21`; Train = ALLE Fenster der anderen Symbole, Test = Fenster des Symbols im `[max_date-20, max_date]`-Fenster; frueh liegende Fenster des ausgelassenen Symbols werden NIRGENDS verwendet (driver.py:133-163) | JA — eigens durch `test_loso_folds_no_symbol_leak` verifiziert (6 Einzelassertions) |
| Null: Within-Symbol-Within-Day-Label-Permutation, 20 VOLLE Retrainings je Fold, KEIN Frozen-Model-Shuffling | woertlich, hoechste Prioritaet lt. Auftrag | `permute_within_groups` permutiert NUR innerhalb (Symbol,Tag)-Zellen der TRAIN-Labels (stats.py:105-123); `run_fold` erzeugt je Replikat eine FRISCHE Encoder-Instanz via `encoder_factory(...)` und ruft `enc_r.fit(...)` GENAU EINMAL — echtes Retraining, nicht Label-Shuffling auf einem fixen Modell (driver.py:219-236) | JA — `test_run_fold_null_is_full_retraining_not_frozen_shuffle` zaehlt `fit()`-Aufrufe pro Instanz (`n_fit_calls==1` fuer ALLE 1+n_perm Instanzen) |
| ONE F-VENUE BH-FDR-Familie ueber die 5 Fold-p-Werte, alpha=0,10 | woertlich | eigene BH-Kopie `stats.benjamini_hochberg`, `FDR_ALPHA=0.10`, EIN Aufruf ueber `p_values` der 5 Folds (driver.py:318-323) | JA |
| Gate WEITER: Balanced-Acc>=0,60 in >=4/5 Folds NACH FDR, UND Non-Redundanz-Gate | woertlich | `BALANCED_ACC_MIN=0.60`, `MIN_PASSING_FOLDS=4`; `r["passed"] = acc_threshold_met AND fdr_significant` (AND, nicht ODER); `folds_ok = n_folds_passed>=4` (driver.py:73-76, 321-343) | JA |
| DROP: Pooled-Acc<0,55 ODER <4/5 Folds ODER \|rho\|>=0,6 (redundant, DROP UNABHAENGIG von Accuracy) | woertlich, kritischster Punkt | `POOLED_ACC_MIN=0.55`; `redundancy_ok=redundancy["passed"]`; `weiter_indication = verdict_bearing AND folds_ok AND pooled_ok AND redundancy_ok` — `redundant` und `passed` sind mutually exclusive (`redundancy.py:175-176`), redundant blockiert WEITER unabhaengig von den Accuracy-Feldern | JA |
| Redundanz-Gate: c12_frag-JSON `windows[].days[].{date,analyzed,lambda2,ipr_v2}` | woertlich, „kritischster Punkt" lt. Auftrag | `extract_c12_daily_series` liest EXAKT diese Pfade/Feldnamen (`redundancy.py:96-114`) — **1:1 gegen den realen `c12_frag.driver.run()`-Output geprueft**, s. unten | JA |
| Spearman rho, eigene Kopie (kein scipy) | Repo-Konvention „keine Cross-Package-Imports" | `stats.spearman_rho` — eigene `_rankdata_average` + Pearson auf Raengen, `stats.py` importiert NUR numpy | JA — numerisch exakt gegen `scipy.stats.spearmanr` verifiziert (s. Test-Abdeckung unten) |
| Batch>=2048 IST Teil der Methode; ohne CUDA NIE verdikt-tragend | woertlich, hoechste Prioritaet lt. Auftrag | `compute.verdict_bearing = cuda_used AND encoder_verdict_capable AND batch_size>=BATCH_SIZE_MIN`; zusaetzlich `len(symbols)!=N_FOLDS` blockiert (driver.py:346-360) | TEILS — s. Befund M-1 (Batch-Check prueft nur den ANGEFORDERTEN, nicht den je Retraining TATSAECHLICH erreichten Batch) |
| capital_free = true, keine bps/PnL/Sharpe/Friction-Felder | woertlich | `"capital_free": True`; Payload-Scan (Grep im Source + Test) findet NULL Vorkommen dieser Tokens ausserhalb negierender Kommentare | JA |
| FDR-Alpha 0,10, eigene BH-Kopie je Package | Repo-Konvention | `stats.py` eigenstaendig, kein Cross-Import aus `c12_frag`/`c07_pe`/etc. | JA |

---

## Redundanz-Gate-Korrektheit (WICHTIGSTER Check)

Ich habe `src/bybit_edge/research/c12_frag/driver.py::run()` volltextgelesen (Zeilen 75-296) und
die reale Payload-Struktur direkt mit `redundancy.py::extract_c12_daily_series` verglichen:

- `c12_frag.driver.run()` liefert `payload["windows"]` als Liste von `window_records` (eine je
  vorregistriertem Fenster), jedes mit `"days": day_records` (Zeile 144-156, 217-243). Jeder
  `day_records`-Eintrag hat IMMER `"date"`, `"analyzed"` (bool); NUR wenn `day.valid` UND das
  Spektrum nicht degeneriert ist, werden zusaetzlich `"lambda1"`, `"lambda2"`, `"ipr_v1"`,
  `"ipr_v2"`, ... gesetzt (Zeile 101-136).
- `redundancy.py::extract_c12_daily_series` iteriert `payload.get("windows", [])` →
  `win.get("days", [])` → `if not day.get("analyzed"): continue` → liest `day["date"]`,
  `day["lambda2"]`, `day["ipr_v2"]` (redundancy.py:107-113). **Feldnamen, Verschachtelungstiefe
  und das `analyzed`-Gate stimmen exakt mit dem realen c12_frag-Output ueberein** — kein
  Schema-Drift, kein defensives `.get(..., default)`, das einen fehlenden Wert stillschweigend
  durchliesse (fehlt `lambda2`/`ipr_v2` bei `analyzed=True`, wirft `float(day["lambda2"])` einen
  `KeyError` statt still 0/NaN einzusetzen — korrektes Fail-Loud-Verhalten, kein Datenverlust
  ueber ein degenerate `.get`).
- Der Test `test_extract_c12_daily_series_matches_driver_shape` sowie die beiden
  `test_redundancy_gate_*`-Tests bauen ein `_c12_like_payload`, das GENAU diese Struktur nachbildet
  (inkl. eines nicht-analysierten Tages, der korrekt uebersprungen wird) — deckt sich mit meiner
  eigenen Volltextlektuere des echten `c12_frag`-Outputs.
- **Spearman-rho-Eigenkopie:** `stats.spearman_rho` nutzt eine eigene `_rankdata_average`
  (Average-Rank-Tie-Behandlung) + Pearson-Korrelation auf den Raengen — importiert NUR numpy,
  KEIN scipy (erfuellt die Repo-Konvention „eigene Kopie, kein Cross-Import"). Ich habe das
  eigenstaendig gegen `scipy.stats.spearmanr` auf 5 synthetischen Reihen (n=2,3,5,10,50, teils mit
  injizierten Ties) gegengerechnet: maximale Abweichung 1.1e-16 (Floating-Point-Rauschen) — die
  Implementierung ist mathematisch exakt.
- **Harte DROP-Durchsetzung, UNABHAENGIG von der Accuracy:** `redundancy_gate()` setzt
  `redundant = evaluable AND max_abs_rho>=0.6` und `passed = evaluable AND max_abs_rho<0.6` — diese
  beiden Flags sind by construction disjunkt. `driver.run()` setzt
  `redundancy_ok = redundancy["passed"]` und
  `weiter_indication = verdict_bearing AND folds_ok AND pooled_ok AND redundancy_ok` (driver.py:344,
  362-363). Es gibt **keinen Codepfad**, auf dem `redundant=True` UND `weiter_indication=True`
  gleichzeitig gelten koennten — das Redundanz-Gate ist nicht nur ein Info-Feld im Payload
  (`redundancy_gate.redundant` wird zusaetzlich klar exponiert), sondern faktisch bindend fuer die
  einzige berechnete Beobachtungs-Flag. Das entspricht der Registry wortgetreu: „|rho|>=0,6 ...
  dann als REDUNDANT zu H-12 deklariert = DROP UNABHAENGIG von der Accuracy."
- Konservative Lesart `max(|rho_lambda2|, |rho_ipr_v2|)` (statt z.B. Mittelwert) ist explizit
  dokumentiert und im Code umgesetzt (redundancy.py:16-17, 172-176) — strengere Lesart als noetig,
  kein Aufweichen.
- **Nicht auswertbar != REDUNDANT != bestanden:** Fehlt der c12-Payload oder ist der Tages-Overlap
  unter der technischen Floor (`MIN_OVERLAP_DAYS=10`, explizit als NICHT-registrierter technischer
  Floor gekennzeichnet), bleibt `evaluable=False` → weder `redundant` noch `passed` → WEITER wird
  blockiert, aber es ist KEIN automatischer DROP. Das ist korrekt getrennt (analog zur
  Validitaets-Vorbedingung in `c12_frag`) und wird vom Runner (`README_H17.md`, `run_h17.{ps1,sh}`)
  transparent kommuniziert: ohne `C12_RESULTS_JSON` bleibt das Gate nicht auswertbar, der Lauf
  schlaegt aber NICHT fehl.

**Fazit Redundanz-Gate: spec-treu, korrekt verdrahtet, hart durchgesetzt. Kein Befund.**

---

## Compute-Gating-Korrektheit

Grundfrage laut Auftrag: **Darf ein Lauf ohne echtes CUDA-Training UND ohne Batch>=2048 jemals
verdikt-tragend sein?** Antwort: **Nein, nicht ueber den ausgewerteten `weiter_indication`-Pfad**
— aber das Gate hat eine Luecke bei der Batch-Groessen-PRUEFUNG selbst (Befund M-1).

- `compute.verdict_bearing = bool(cuda_used AND encoder_verdict_capable AND batch_size>=BATCH_SIZE_MIN)`
  (driver.py:346-348), zusaetzlich hart auf `False` gezwungen, wenn `len(symbols)!=N_FOLDS`
  (driver.py:357-360). `weiter_indication` prueft `verdict_bearing` als ERSTE UND-Bedingung
  (driver.py:362-363) — ohne CUDA ODER ohne verdikt-faehigen Encoder ODER mit falschem
  Symbol-Panel ist `weiter_indication` IMMER `False`, unabhaengig von den Accuracy-Zahlen. Das ist
  durch zwei unabhaengige Tests verifiziert:
  `test_driver_run_compute_gate_blocks_verdict_without_cuda` (kein CUDA → `verdict_bearing=False`,
  `weiter_indication=False`) und `test_driver_run_pretends_cuda_used_still_blocked_by_fallback_encoder`
  (selbst ein FALSCH gemeldetes `cuda_used=True` wird durch die zweite, unabhaengige Verteidigungslinie
  `encoder_verdict_capable` — ein Klassen-Attribut, `False` fuer `NumpyFallbackEncoder` — blockiert).
- `NumpyFallbackEncoder.verdict_bearing=False` als Klassenattribut ist by Design NIE `True` —
  selbst ein absichtlich manipulierter Aufruf mit `cuda_used=True` kann also keinen Fallback-Lauf
  zum Verdikt hochstufen (zweite Verteidigungslinie greift).
- Der T3-Runner (`run_h17.{ps1,sh}`) prueft VOR jedem echten Lauf `--check-gpu-only` und
  **ueberspringt den gesamten Lauf (SKIP, exit 2)**, wenn kein CUDA-Device sichtbar ist — verhindert
  proaktiv einen stundenlangen, ohnehin nicht verdikt-tragenden CPU-Smoke (das eingebaute Driver-Gate
  waere ohnehin die zweite Verteidigungslinie).
- **Befund M-1 (MEDIUM):** `compute.batch_size` im Payload ist `int(batch_size)` — der Wert, den der
  AUFRUFER (CLI-Flag `--batch-size`, Default 2048) angefordert hat (driver.py:279, 404). Das
  eigentliche Training in `contrastive.train_contrastive_encoder` verwendet aber
  `eff_batch = min(batch_size, n)` (contrastive.py:136), wobei `n` die Groesse des TRAIN-Sets DIESES
  Folds ist. Ist `n < batch_size` (z.B. bei sehr duennem Panel, kuerzerem Test-Zeitraum oder einem
  abweichend parametrierten Ad-hoc-Lauf), sinkt der TATSAECHLICH verwendete Batch je Optimizer-Step
  UNTER das registrierte Minimum — **OHNE** dass der `driver.run()`-Compute-Gate-Check das bemerkt,
  weil dieser nur den angeforderten CLI-Wert prueft, nicht `fit_info["batch_size"]`/
  `fit_info["small_batch_override"]` (die PRO FOLD korrekt berechnet und im Payload unter
  `folds[*].fit_info` abgelegt werden, aber nirgends aggregiert/gegen `BATCH_SIZE_MIN` geprueft
  werden). Der explizite `--allow-small-batch`-Pfad (Nutzer fordert absichtlich <2048 an) IST
  abgesichert (`train_contrastive_encoder` wirft `ValueError` ohne dieses Flag, UND
  `driver.run()`s eigener `batch_size<BATCH_SIZE_MIN`-Check blockiert `verdict_bearing` bereits
  auf Basis des angeforderten Werts) — die Luecke betrifft NUR den STILLEN Fall, in dem der
  angeforderte Batch >= 2048 ist, aber das tatsaechliche Trainingsset eines einzelnen Folds kleiner
  ist. **Realrisiko:** gering — bei ~99 Tagen (2026-03-27..07-04) x 5-Min-Fenstern liegt das
  Train-Set jedes Folds (4 Symbole x 2 Boersen, MIN_EVENTS_PER_WINDOW=64) fuer liquide
  Bybit/Binance-Perp-Majors typischerweise im hohen 5- bis 6-stelligen Bereich, weit ueber 2048 —
  aber der Code verlaesst sich fuer die „harte Garantie" (registry: „DAS Batch-Size-Regime ist Teil
  der Methode") stillschweigend auf diese empirische Annahme statt sie zu pruefen. Fuer XRP/BNB
  (die duennsten der 5 Symbole) in kurzen Testfenstern ist das nicht mit letzter Sicherheit
  auszuschliessen. **Empfehlung (vor dem GPU-Lauf, klein):** `run()` sollte zusaetzlich
  `min(r["fit_info"].get("batch_size", BATCH_SIZE_MIN) for r in fold_records)` (real+null-Retrainings)
  gegen `BATCH_SIZE_MIN` pruefen und bei Unterschreitung `verdict_bearing=False` erzwingen (Blocker-
  Grund „effektiver Batch < 2048 in mind. einem Retraining"), statt sich nur auf den
  CLI-Request-Wert zu verlassen.

**Fazit Compute-Gating: im ausgewerteten `weiter_indication`-Pfad hart durchgesetzt (Kernanforderung
erfuellt); aber der Batch-Groessen-Teil des Gates hat eine Luecke bei impliziter Unterschreitung —
M-1, vor dem Lauf fixen oder zumindest bewusst als Restrisiko akzeptieren.**

---

## Permutations-Null-Echtheit

Bereits oben tabellarisch gepruefte Kernaussage vertieft:

- `permute_within_groups` permutiert die TRAIN-Venue-Labels streng INNERHALB jeder
  (Symbol,UTC-Tag)-Zelle (`stats.py:105-123`) — Gruppenzusammensetzung (Anzahl Bybit-/
  Binance-Fenster je Zelle) bleibt exakt erhalten; getestet in
  `test_permute_within_groups_preserves_group_composition` (Multiset-Gleichheit je Gruppe).
- In `run_fold` wird fuer JEDES der `n_perm` Replikate `encoder_factory(...)` NEU aufgerufen
  (frische Instanz, nicht die reale trainierte Instanz wiederverwendet), und `enc_r.fit(...)` wird
  GENAU EINMAL pro Instanz aufgerufen (driver.py:219-236) — das ist ein echtes Full-Retraining, kein
  Label-Shuffling auf einem eingefrorenen Modell. Die permutierten Venue-Labels definieren dabei
  auch die Node-Identitaet fuer die Contrastive-Positives neu (`_node_ids(venues_perm, ...)`,
  driver.py:224-227) — der gesamte Repraesentationslernprozess, nicht nur die Probe, laeuft unter
  der Null neu.
- `test_run_fold_null_is_full_retraining_not_frozen_shuffle` verifiziert das MASCHINELL (nicht nur
  durch Code-Lektuere): ein Fit-Call-Zaehler auf dem Dummy-Encoder bestaetigt `len(made)==1+n_perm`
  FRISCHE Instanzen UND `enc.n_fit_calls==1` fuer JEDE einzelne — ein starker, spezifischer Test
  gegen genau die Bug-Klasse „Frozen-Model-Label-Shuffling", die der Auftrag befuerchtet.
- Accuracy unter der Null wird immer gegen die WAHREN Test-Labels gemessen (`balanced_accuracy(y_te,
  pred_r)`, driver.py:232), nicht gegen die permutierten — korrekt (die Null misst, ob ein auf
  Zufallslabels trainiertes Modell zufaellig die echten Testlabels trifft).

**Fazit Permutations-Null: spec-treu, echtes Retraining, maschinell verifiziert. Kein Befund.**

---

## Pro-Tag-Quantil-Normalisierungs-Wirksamkeit

- `per_day_quantile_normalize` transformiert jeden Kanal je (Node, UTC-Tag) auf
  `u = rank/(n+1) in (0,1)` (Average-Rank-Ties) — das ist mathematisch invariant gegenueber JEDER
  monoton steigenden Transformation des Rohkanals (Skala, Rundung, additive Verschiebung), was
  genau die genannten trivialen Tells (Tick-Groesse, Fee-Rundung, absolutes Aktivitaetsniveau)
  eliminiert. Direkt bewiesen durch
  `test_quantile_normalize_marginal_is_uniform_regardless_of_scale` (`u_raw == u_scaled` fuer eine
  beliebige affine Reskalierung).
- Der Builder-Diagnosetest `test_per_day_quantile_normalization_destroys_trivial_tell` ist
  methodisch sauber konstruiert: **Event-Count-Konfundierung wird explizit kontrolliert** — beide
  synthetischen Venues erhalten die IDENTISCHE `duration_scale_ms=300.0` (also statistisch dieselbe
  Ereignisrate/Fensterbelegung), NUR `size_log_mean` (Groessen-Skala) und `size_round` (Fee-Rundung)
  unterscheiden sich zwischen Venue A und B — der Test-Docstring begruendet das explizit
  („confound a genuine event-COUNT-per-window difference"). Damit misst der Test wirklich den
  Normalisierungseffekt auf Werteverteilungen, nicht einen Seiteneffekt aus unterschiedlicher
  Fensterbelegung.
  - Vor Normalisierung: `acc_raw >= 0.85` (ein einfacher linearer Summary-Stat-Probe trennt die
    Venues fast perfekt).
  - Nach Normalisierung: `acc_norm <= 0.70` UND `acc_norm < acc_raw - 0.15` (deutlicher Abfall).
- `trivial_tell_probe_features` ist bewusst „count-free" (keine Event-Count-/Pad-Fraction-Merkmale),
  weil der Encoder ohnehin ueber eine Masked-Mean pooled — das Diagnosewerkzeug misst also exakt die
  Groesse, die die registrierte Normalisierung angreifen soll (Werteverteilungen), nicht die
  Fenster-Belegung.
- **Einschraenkung (INFO, kein Blocker):** Der Diagnosetest verwendet `train_frac=0.6` und einen
  festen Seed — die absolute Schwelle `acc_norm<=0.70` ist plausibel, aber nicht selbst als
  vorregistrierter Gate-Wert in der Registry fixiert (die Registry verlangt nur qualitativ „muss
  nachweislich die trivialen Tells toeten", ohne Zahlenwert) — das ist Builder-Diagnostik-Pflicht,
  kein Teil des bindenden H-17-Gates selbst, also kein Fehlverhalten, nur zur Einordnung erwaehnt.

**Fazit Quantil-Normalisierung: nachgewiesen wirksam, Event-Count-Konfundierung sauber kontrolliert.
Kein Befund.**

---

## capital_free-Check

- `driver.run()` setzt `"capital_free": True` fest im Payload (driver.py:373).
- Repo-weiter Grep ueber `src/bybit_edge/research/c17_venue/` und `scripts/c17_venue.py` nach
  `bps|pnl|sharpe|friction|slippage` (case-insensitive) findet AUSSCHLIESSLICH Vorkommen in
  negierenden Docstring-/Kommentarzeilen („No friction, bps, PnL, Sharpe." etc.) — kein einziges
  tatsaechliches Datenfeld, keine Berechnung.
- `test_driver_run_capital_free_and_no_forbidden_tokens` UND
  `test_end_to_end_cli_produces_valid_json` scannen den SERIALISIERTEN JSON-Payload-Blob
  (`json.dumps(payload).lower()`) auf `("bps","pnl","sharpe","friction","edge_")` — beide gruen.
- Die Registry-KAPITALFREIHEIT-Klausel („Eine Handelsfolge waere NEUE H-17b, NICHT impliziert")
  wird woertlich im Docstring von `driver.py` sowie in `render_markdown()` wiederholt.

**Fazit capital_free: sauber. Kein Befund.**

---

## T3-Runner-Check (PowerShell + Bash)

- **Handle-Cache-Workaround (bekannte PS-5.1-Bug-Klasse):** `run_h17.ps1` cached `$p.Handle` VOR
  jedem `WaitForExit`/`ExitCode`-Zugriff sowohl in `Invoke-Step` als auch in `Invoke-GpuCheck`
  (Zeilen 109, 153) — korrekt gegen den bekannten PS-5.1-Bug angewendet, bei dem `$p.ExitCode` ohne
  vorherigen Handle-Zugriff `null` liefert. Konsistent in beiden Funktionen.
- **BelowNormal-Prioritaet:** sowohl fuer den PowerShell-Hauptprozess selbst
  (`(Get-Process -Id $PID).PriorityClass='BelowNormal'`, Zeile 68) als auch fuer die gestarteten
  Kindprozesse (`$p.PriorityClass='BelowNormal'`, Zeilen 110, 154) gesetzt — korrekt, verhindert dass
  ein Mehrtages-GPU-Lauf die interaktive Nutzung der Maschine blockiert.
- **Timeout-Arithmetik:** `$TmoMain` Default 172800 s (48h) fuer `WaitForExit($TimeoutSec*1000)` —
  `172800*1000=172.8e6`, weit unter `Int32.MaxValue` (2.15e9), kein Ueberlauf.
- **GPU_CHECK als reine Diagnose-Probe, kein Fail:** `rc=3` (kein CUDA) wird explizit NICHT als
  `FAIL` gewertet (`if ($rc -ne 0 -and $rc -ne 3) { $status='FAIL' }`), sondern als `INFO` — korrekt,
  da ein fehlendes CUDA-Device ein erwarteter, informativer Ausgang ist (jeder Sandbox-Lauf), kein
  Runner-Absturz.
- **Ohne CUDA wird der gesamte Hauptlauf uebersprungen (SKIP, exit 2)** statt stundenlang eine
  nicht-verdikt-tragende Pipeline-Smoke zu fahren — spart Zeit auf der Zielmaschine, konsistent mit
  dem Compute-Gate im Code (zweite, redundante Absicherung).
- **Argument-Quoting:** einfaches Whitespace-basiertes Quoting (`if ($a -match '\s')`) — fuer den
  hier verwendeten festen Satz von Pfaden/Flags ausreichend (keine eingebetteten Anfuehrungszeichen
  in den erzeugten Argumenten), kein Befund fuer DIESEN konkreten Aufrufsatz.
- **LOW-Befund (kosmetisch):** `run_h17.ps1` enthaelt genau EIN Nicht-ASCII-Zeichen (`—`, Em-Dash,
  Zeile 135) in einem `#`-Kommentar innerhalb `Invoke-GpuCheck`. Die Datei hat KEIN UTF-8-BOM
  (verifiziert: erste 3 Bytes sind `# =`, nicht `EF BB BF`). Der Header der Datei deklariert
  explizit „PS 5.1-kompatibel (handle-cache + BelowNormal + **ASCII-Body**)" als Entwurfsinvariante
  — das trifft auf den tatsaechlich per `WriteAllText` geschriebenen `$sb`-Summary-Body (Zeilen
  229-256) zu (dort ausschliesslich ASCII, verifiziert), NICHT aber auf die Skriptdatei selbst,
  die im Kommentarbereich ein Unicode-Zeichen enthaelt. PowerShell 5.1 liest `.ps1`-Dateien ohne
  BOM je nach System-Codepage (nicht garantiert UTF-8) — im schlimmsten Fall wird nur das
  Kommentarzeichen auf einer Nicht-UTF-8-Windows-Maschine als Mojibake angezeigt (Kommentare
  brechen die Parsing-Syntax nicht), funktional harmlos, aber ein Bruch der selbst deklarierten
  ASCII-Invariante. **Empfehlung:** Zeile 135 auf ASCII (`-` statt `—`) normalisieren, um die
  eigene Entwurfsregel konsequent einzuhalten (rein kosmetisch, kein Lauf-Blocker).
- **`run_h17.sh` (Bash):** `timeout "$tmo" ...` mit Fallback ohne `timeout`-Binary, korrekte
  `rc=124`-Erkennung, GPU_CHECK ebenfalls als reine `INFO`-Probe (`rc!=0 && rc!=3` -> FAIL) —
  strukturell identisch zum PS1-Pendant, kein Befund.
- Beide Runner pruefen VOR dem Start, dass `raw/bybit/publicTrade` UND `raw/binance/publicTrade`
  unter dem Harvester-Root existieren, sonst SKIP (kein FAIL) — vermeidet einen kryptischen
  Python-Traceback als ersten Eindruck eines unbeaufsichtigten Laufs.
- Beide Runner weisen im Summary-Text EXPLIZIT darauf hin, dass `compute.verdict_bearing==true`
  vor jeder Auswertung geprueft werden MUSS — deckt sich mit dem Code-Gate (Redundanz statt
  Single-Point-of-Failure).

**Fazit T3-Runner: strukturell solide, bekannte PS-5.1-Fallstricke korrekt behandelt. Ein
kosmetischer LOW-Befund (Em-Dash-Kommentar).**

---

## Gefundene Bugs (nach Schweregrad)

| ID | Schweregrad | Fund | Ort | Empfehlung |
|---|---|---|---|---|
| M-1 | **MEDIUM** | Compute-Gate `compute.batch_size`/`verdict_bearing` prueft nur den ANGEFORDERTEN CLI-Batch, nicht den je Fold/Replikat TATSAECHLICH erreichten `eff_batch=min(batch_size,n)`. Bei einem Trainingsset < 2048 Fenstern (unwahrscheinlich, aber fuer duenne Symbole/kurze Fenster nicht ausgeschlossen) koennte `verdict_bearing=True` trotz stillschweigend unterschrittenem Batch-Minimum stehen. | `driver.py:279,346-348,404`; `contrastive.py:136` | Vor dem GPU-Lauf: `min(fit_info["batch_size"])` ueber alle Folds+Retrainings aggregieren und zusaetzlich gegen `BATCH_SIZE_MIN` pruefen; bei Unterschreitung `verdict_bearing=False` erzwingen. |
| L-1 | LOW (kosmetisch) | `run_h17.ps1` Zeile 135: ein Em-Dash (`—`) in einem Kommentar verletzt die selbst deklarierte „ASCII-Body"-Invariante der Datei (Datei hat kein BOM). Funktional harmlos (Kommentar), aber inkonsistent mit dem eigenen Entwurfsprinzip. | `run_h17.ps1:135` | Auf ASCII (`-`) normalisieren. |
| I-1 | INFO | `acc_norm<=0.70`-Schwelle im Builder-Diagnosetest fuer die Quantil-Normalisierung ist plausibel, aber selbst nicht in der Registry als Zahl vorregistriert (Registry verlangt nur qualitativ „muss die Tells toeten") — kein Fehlverhalten, nur zur Einordnung. | `tests/unit/test_c17_venue.py:169-174` | Keine Aenderung noetig; ggf. im Runner-README explizit als Builder-Diagnostik-Konvention (nicht Gate-Wert) kennzeichnen (README tut das teilweise bereits). |
| I-2 | INFO | `MIN_EVENTS_PER_WINDOW=64` und `MIN_OVERLAP_DAYS=10` sind korrekt als NICHT-registrierte technische Floors im Code kommentiert und nicht mit den vorregistrierten Gate-Schwellen vermengt — positiv vermerkt, kein Befund. | `features.py:64-66`, `redundancy.py:39-43` | — |

Keine CRITICAL- oder HIGH-Befunde.

---

## Test-Abdeckung

`tests/unit/test_c17_venue.py` (18 Tests) deckt ab: (a) Quantil-Normalisierung toetet injizierten
trivialen Tell + Skaleninvarianz-Beweis; (b) LOSO-Fold-Konstruktion ohne Symbol-Leck (6 Assertions
je Fold, inkl. Symbol-Count-Mismatch-Fehlerpfad); (c) Permutations-Null-Gruppenerhaltung +
maschinell verifiziertes echtes Retraining (Fit-Call-Zaehler); (d) Redundanz-Gate gegen synthetische
UND exakt c12_frag-foermige Payloads (hohe Korrelation → REDUNDANT/DROP, niedrige → PASS, fehlender
Payload → nicht auswertbar, zu wenig Overlap → nicht auswertbar, Feldextraktion inkl.
`analyzed=False`-Skip); (e) eigene BH-Kopie + `capital_free`/Verbotstoken-Scan ueber den vollen
`driver.run()`-Payload; (f) `--check-gpu-only` ehrliche Sandbox-Meldung ohne vollen Lauf; (g)
End-to-End-CLI-Smoke ueber einen synthetischen Harvester-Baum (5 Symbole x 2 Boersen, echte
DuckDB/Parquet-Dateien) mit `rc=0`, validem JSON/MD, `verdict_bearing==False`.

**Was NICHT in der Sandbox pruefbar ist** (README_H17.md ehrlich dokumentiert): reale
Contrastive-Embedding-Qualitaet, reale Held-out-Accuracy, reale Trainingsdynamik bei Batch>=2048 —
das ist explizit Zweck des T3-GPU-Laufs. Diese Einschraenkung ist sauber kommuniziert, kein
verstecktes Overselling der Sandbox-Testabdeckung.

**Eigene Testlaeufe (diese Session):**
```
PYTHONPATH=src python3 -m pytest tests/unit/test_c17_venue.py tests/unit/test_c12_frag.py -q
26 passed in 66.21s
```
`git status`/`git diff --stat` gegen `src/bybit_edge/research/c12_frag/`, `scripts/c12_frag.py`,
`tests/unit/test_c12_frag.py` → **leerer Diff** — H-17s Implementierung hat den c12_frag-Code NICHT
angefasst (Regressionscheck bestanden, wie vom Auftrag verlangt).

---

## Gesamtfazit

H-17 ist spec-treu implementiert und die drei vom Auftrag als hoechste Prioritaet benannten Punkte
sind alle im Kern korrekt: (1) Compute-Gating blockiert `weiter_indication` hart ohne echtes CUDA
UND Batch>=2048 — mit einer MEDIUM-Luecke bei impliziter (nicht explizit angeforderter)
Batch-Unterschreitung, die vor dem produktiven Lauf gefixt werden sollte, deren Realrisiko aber
angesichts der Panelgroesse gering ist; (2) das Redundanz-Gate gegen c12_frag liest die reale
JSON-Struktur exakt korrekt, hat eine numerisch verifiziert exakte eigene Spearman-Implementierung
und erzwingt `|rho|>=0,6` als echtes, unumgehbares DROP unabhaengig von der Accuracy; (3) die
Permutations-Null ist nachweislich echtes Retraining, maschinell verifiziert. Beide Test-Suiten
(c17_venue + c12_frag) sind gruen, und H-17 hat keine Regression in c12_frag verursacht. Empfehlung:
M-1 vor dem ~1-2-Tage-GPU-Lauf beheben (kleiner, risikoarmer Patch), L-1 optional.
