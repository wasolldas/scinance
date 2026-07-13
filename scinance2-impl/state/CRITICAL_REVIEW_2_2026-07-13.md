# Kritische Code-Review – Scinance 2.0, Runde 2 (Stand 2026-07-13)

## Was ist das

Dies ist die Destillation eines **zweiten** adversarialen Review-Netzwerks über
die Scinance-2.0-Codebasis (erste Runde: `state/CRITICAL_REVIEW_2026-07-09.md`).
12 parallele Lanes liefen diesmal: fünf frische Bug-Hunts auf den neueren
Wave-5-GPU-Forschungsmodulen (`c14_panellag`, `c15_grammar`, `c16_arrow`,
`c17_venue`, `c18_leadlag_audit`), eine `fix-verification`-Lane (prüft, ob
die Fixes der ersten Runde wirklich vollständig sind), sowie sechs Lanes,
die den Rest der Codebasis erneut nach zuvor übersehenen Bugs durchsucht
haben.

Die fünf Wave-5-GPU-Modul-Lanes liefen auf **Fable 5**. Die restlichen sieben
Lanes liefen auf dem **Default-Modell der Session**, nachdem Fable 5 mitten
im Lauf ein hartes Nutzungslimit erreicht hatte (kein Reset-Zeitpunkt
angegeben). Jeder einzelne Kandidaten-Befund wurde anschließend von **drei
unabhängigen Skeptiker-Agenten** gegengeprüft, die den Code selbst gelesen
und den behaupteten Fehlerpfad nachvollzogen haben; ein Befund "überlebt"
nur bei Mehrheitsvotum (mindestens 2 von 3 CONFIRMED).

**Ergebnis: 34/35 Kandidaten-Befunde bestätigt, 1 verworfen.**

Dieser Bericht ist eine reine, verlustarme Verdichtung der bereits
verifizierten Ergebnisse — es wurden keine eigenen Bewertungen, Meinungen
oder zusätzlichen Befunde ergänzt.

## Zusammenfassung

| Schweregrad | Anzahl |
|---|---|
| Critical | 5 |
| High | 23 |
| Medium | 6 |
| **Gesamt (bestätigt)** | **34** |
| Verworfen (refuted) | 1 |

Inhalt nach Schweregrad, darin gruppiert nach Lane:

- [Critical](#critical-5-befunde)
- [High](#high-23-befunde)
- [Medium](#medium-6-befunde)
- [Verworfene Kandidaten](#verworfene-kandidaten)

---

## Critical (5 Befunde)

### Lane: wave5-c15-grammar

#### `src/bybit_edge/research/c15_grammar/driver.py:358`

**Kategorie:** compute-gating-bypass

Der Checkpoint-Fingerprint (`_run_fingerprint`) enthält weder `mode`, `device`
noch `ran_on_gpu`. Ein voller GPU-Lauf (`--mode full`) kann dadurch
stillschweigend Checkpoints eines vorherigen CPU-Laufs (`--mode mechanics`)
übernehmen und stempelt `gate_valid=true`/`ran_on_gpu=true` auf ein
Ergebnis, hinter dem kein einziger GPU-Trainingsschritt steckt.

Ein `mechanics`-Lauf auf einer CPU-only-Maschine trainiert alle Symbole auf
CPU und checkpointet sie im geteilten, nicht-timestamped Verzeichnis
(`results/h15_ckpt`, von beiden T3-Runnern verwendet). Ein späterer
`--mode full`-Lauf mit CUDA erzeugt denselben Fingerprint, lädt daher alle
Symbole aus dem CPU-Checkpoint statt neu zu trainieren, und das Endergebnis
wird trotzdem als `gate_valid: true, ran_on_gpu: true, mode: full`
ausgewiesen — ein direkter Verstoß gegen das harte Wave-5-Compute-Gate
("ein Lauf ohne echtes CUDA/GPU-Training darf NIE ein verdikt-tragendes
Ergebnis produzieren"). Kein Test deckt diesen Mode-Mismatch-Resume-Fall ab.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: wave5-c17-venue

#### `src/bybit_edge/research/c17_venue/contrastive.py:137`

**Kategorie:** compute-gating-bypass

Das Compute-Gate prüft nirgends die Anzahl der tatsächlich durchgeführten
Optimizer-Schritte. Ein CUDA-Lauf mit `--steps 0` (argparse hat keine
Untergrenze) führt null Trainingsiterationen aus, meldet aber trotzdem
`trained: True` und einen `batch_size >= 2048`, obwohl nie ein Batch
gesampelt wurde.

`driver.run()`s Compute-Gate prüft nur `cuda_used`/`encoder_verdict_capable`/
angeforderte Batch-Size, nie `fit_info["steps"]`. Alle 105 "Trainings" sind
dadurch nur zufallsinitialisierte TemporalCNN-Encoder — random-projection-
Klassifikatoren können jedoch echte Trennschärfe zeigen, sodass ein echtes
`weiter_indication=True` mit buchstäblich null GPU-Compute erreichbar ist,
exakt das von Wave-5 verbotene Ergebnis. Der analoge `--allow-small-batch`-
Override ist doppelt abgesichert, `--steps` dagegen gar nicht.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: fix-verification

#### `src/bybit_edge/recorder/storage.py:194`

**Kategorie:** resource-exhaustion-regression-from-fix

Der Fix vom 2026-07-09 ("buffer-before-write", Commit `d8b3f5b`)
aktualisiert `_last_flush` jetzt nur noch bei erfolgreichem Schreiben. Bei
einer anhaltenden Flush-Fehlfunktion (z.B. eine wirklich volle Disk — exakt
das Szenario, das der Fix adressieren sollte) bleibt die zeitbasierte
`should_flush()`-Bedingung ab dann für immer erfüllt.

Da `RecordingEngine._run_ws_transport` nach JEDER eingehenden Nachricht
`_maybe_flush` aufruft, versucht der Writer ab dem Ausfall bei jeder
einzelnen Nachricht einen vollen, synchronen `pq.write_table`-Versuch —
inklusive Neuaufbau der Arrow-Table über den gesamten, ständig wachsenden
Puffer (Zeilen werden nie verworfen). Das blockiert den Event-Loop,
verzögert den App-Ping, lässt Bybits Keepalive verpassen und den WebSocket
abbrechen — ein Reconnect/Backoff-Zyklus, der sich wiederholt und aus einem
kurzen Disk-Hänger eine anhaltende CPU-/Log-Explosion macht. Der bestehende
Regressionstest prüft nur, dass Zeilen erhalten bleiben, nicht die
Retry-Storm-Folge unter realistischer Nachrichtenlast.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: strategies-execution

#### `src/bybit_edge/replay_backtester.py:1461`

**Kategorie:** position-accounting-desync

Nach der TRAIN-Warmup-Phase im Walk-Forward setzt der Backtester zwar sein
eigenes `open_pos[sid]`-Bookkeeping auf `None`, aber NICHT das interne
`_in_trade`-Flag der Strategie-Objekte selbst (Strategy1–5). Eine während
TRAIN offene Position lässt Backtester- und Strategiezustand an jeder
Fold-Grenze auseinanderlaufen.

Hält eine Strategie am Ende von TRAIN eine offene Position, glaubt sie beim
Eintritt in TEST weiterhin `_in_trade=True` und prüft nur noch
Exit- statt Entry-Bedingungen — echte Entry-Chancen werden verworfen, bis
der stale, aus TRAIN stammende Exit irgendwann feuert (kann Stunden
dauern). Feuert der Exit dann, ist `open_pos[strategy_id]` bereits `None`,
sodass auch der Exit lautlos verworfen wird — kein Trade, kein Log, keine
Exception. Da die Walk-Forward-Test-Trades genau die Evidenzgrundlage des
WEITER/DROP-Gates und des Optuna-Sharpe-Objectives sind, werden Trade-Zahlen
und Sharpe unvorhersehbar für einen Teil der Folds auf null gedrückt — ohne
dass ein Test dies abdeckt.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: infra-collector

#### `src/bybit_edge/multi_runner.py:101`

**Kategorie:** constitution-compliance-gate-bypass

`MultiSymbolRunner` übergibt jedem `LiveRunner` immer einen konkreten
`bool` als `execution_override` (`sym == execution_symbol`) statt `None`.
Dadurch ignoriert `LiveRunner._execution_active()` den Master-Switch
`EXECUTION_ENABLED` für den Execution-Symbol-Runner vollständig — **echte
Orders werden auch bei `EXECUTION_ENABLED=false` platziert.**

`_execution_active()` gibt `EXECUTION_ENABLED` nur zurück, wenn
`execution_override is None`; `MultiSymbolRunner` setzt aber immer
`True`/`False`. Da `execution_symbol` standardmäßig `PRIMARY_SYMBOL`
(BTCUSDT) ist und der reale Einstiegspunkt `python -m bybit_edge` genau
diesen Default nutzt, ist `_execution_override` für den BTCUSDT-Runner immer
`True` — unabhängig vom `EXECUTION_ENABLED`-Wert. `run()` initialisiert
daraufhin unbedingt einen `BybitExecutor`, und `_act_on_decision` sendet
echte signierte `POST /v5/order/create`-Requests gegen die Bybit-
Testnet/Demo-API, sobald `MULTI_SYMBOL_RUNNER_ENABLED=true` und API-Keys
gesetzt sind — obwohl das Modul selbst dokumentiert: "Orders werden nur
gesendet wenn EXECUTION_ENABLED=true". Ein bestehender Test bestätigt dieses
Verhalten explizit als Ist-Zustand, prüft aber nie, dass
`EXECUTION_ENABLED=False` die Order-Platzierung im Multi-Symbol-Modus
tatsächlich unterdrückt.

Bestätigt von 3/3 unabhängigen Prüfern.

---

## High (23 Befunde)

### Lane: wave5-c14-panellag

#### `src/bybit_edge/research/c14_panellag/ablation.py:157`

**Kategorie:** checkpoint-staleness-verdict-corruption

Checkpoint-Resume ist nur nach `(window_label, task_id)` geschlüsselt und
prüft nur das `device`-Feld — Checkpoints aus Läufen mit anderen
Fensterdaten, anderem `--seed` oder anderen Paneldaten werden lautlos in
ein `gate_valid=true`-Ergebnis übernommen, weil weder JSON noch Resume-Check
Fenster-Start/Ende oder Seed speichert bzw. vergleicht.

Der vorherige Audit (`audit_h14.md`, GL-012) empfiehlt einen kurzen
GPU-Feasibility-Vorlauf mit abweichenden Fenstern vor dem Produktionslauf.
Landet dieser im selben Checkpoint-Verzeichnis (Standard
`results/h14_checkpoints`), übernimmt der spätere Produktionslauf über die
registrierten 50-Tage-Fenster alle Checkpoints ungeprüft (`device='cuda'`
reicht als Beleg), meldet `gate_valid=true` und die registrierten
Fensterdaten — obwohl jeder Loss auf dem kurzen Feasibility-Fenster
berechnet wurde.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/research/c14_panellag/driver.py:147`

**Kategorie:** nan-poisoning-false-weiter

Es gibt keinen isfinite-Guard in den Edge-/Null-Statistiken: Ein einzelner
nicht-finiter Trainings-Loss (checkpointet als JSON `null` — ein normaler
Vorgang bei Mehrnächte-Betrieb) lässt `empirical_p_ge` für jede Edge in das
betroffene Ziel den minimal möglichen p-Wert (1/9901) liefern, weil
NaN-Vergleiche immer `False` sind. Das kann fälschlich BH-Rejections in die
gesamte 198-Test-F-PANELLAG-Familie einschleusen und `weiter_indication`
von `False` auf `True` kippen.

End-to-end reproduziert: Ein einziger `None`-Loss injizierte 16 falsche
signifikante Edges, hob den BH-Schwellwert an, sodass ein eigentlich nicht-
signifikanter, echter Edge in beiden Fenstern signifikant "überlebte" —
Ergebnis kippte von `weiter_indication=False` auf `True` bei
`gate_valid=true`. Da `encoder.fit_panel` kein Gradient-Clipping hat
(~226 unabhängige Trainings), ist ein divergierender Loss realistisch — eine
falsche WEITER-Entscheidung auf einem Falsifikations-Gate ist das denkbar
schlechteste Ergebnis.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: wave5-c15-grammar

#### `src/bybit_edge/research/c15_grammar/driver.py:528`

**Kategorie:** checkpoint-data-binding-drift

Der Checkpoint-Fingerprint berücksichtigt auch `events_capped`/
`max_events_per_day` nicht — ein ungecappter Full-Lauf kann Checkpoints aus
einem per-Tag-gecappten (also inhaltlich anderen) Lauf übernehmen und
trotzdem `gate_valid=true` stempeln.

Ein Debug-Lauf mit `--max-events-per-day 20000` wird zwar selbst korrekt
via `events_capped`-Gate-Reason entwertet, checkpointet aber trotzdem jedes
Symbol. Ein späterer Lauf ohne Cap im selben Checkpoint-Verzeichnis hat
denselben Fingerprint, übernimmt alle Symbole aus den gecappten
Checkpoints, hat aber selbst `events_capped=False` — das Ergebnis trägt
`gate_valid: true`, obwohl alle Statistiken auf gekürzten,
nicht-registrierten Daten basieren.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/research/c15_grammar/driver.py:497`

**Kategorie:** gate-integrity

Das registrierte ~100-Tage-Datenfenster wird im `gate_valid`-
Abweichungscheck nie geprüft — `--data-start`/`--data-end` sind freie
CLI-Flags, sodass nachträgliches "Window-Shopping" trotzdem
`gate_valid=true` ergibt.

Nach einem ersten Full-GPU-Lauf mit DROP-Ergebnis kann ein erneuter Lauf mit
einem beliebigen, mindestens 15-tägigen Teilfenster (z.B.
`--data-start 2026-05-01`) `gate_valid: true` liefern, weil der
Deviation-Check zwar Folds, Embargo, Seed-Anzahl, Surrogates, Symbol-Panel
etc. prüft, aber nie `days[0]`/`days[-1]` gegen die registrierten
Default-Werte vergleicht — dieselbe Bug-Klasse, die `audit_h15.md` bereits
für die Architektur gefixt hat, fehlt hier für das eine registrierte
Fenster ("EIN Fenster").

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/research/c15_grammar/driver.py:502`

**Kategorie:** gate-integrity

Nur die ANZAHL der Seeds wird gegen die Registry geprüft
(`len(seeds) != N_SEEDS`), nicht die registrierten Seed-WERTE (42, 43, 44) —
Seed-Shopping oder degenerierte Duplikat-Seeds ergeben trotzdem
`gate_valid=true`.

`--seeds 7,8,9` (wiederholt bis das gewünschte Ergebnis erreicht ist) oder
`--seeds 42,42,42` (drei identische Modelle statt echter Seed-Varianz)
passieren den Deviation-Check, weil nur die Länge=3 verglichen wird. Der
Checkpoint-Fingerprint speichert die Seed-Werte zwar bereits — beweist also,
dass die Identität an anderer Stelle als relevant erkannt wurde — nur der
Gate-Check prüft sie nicht.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: wave5-c16-arrow

#### `src/bybit_edge/research/c16_arrow/driver.py:563`

**Kategorie:** fdr-family-construction

Die registrierte, feste F-ARROW-Familiengröße (`FAMILY_SIZE = 5`) wird
nirgends erzwungen — `run()` baut Zellen nur für die übergebenen Symbole,
`evaluate_gate()` rechnet BH über `len(cells)`. Ein CLI-Aufruf mit weniger
als 5 (oder duplizierten) Symbolen schrumpft die BH-Familie unbemerkt,
obwohl das Modul selbst dokumentiert, dass "BH nie über eine still
geschrumpfte Familie läuft".

Reproduziert: Bei 4 statt 5 Symbolen kippt der BH-Schwellwert von 0.08
(5er-Familie mit Sentinel-Padding) auf 0.10 (4er-Familie) — identische
Daten, entgegengesetztes Quorum-Ergebnis (`gate_quorum_met` False vs.
True), ohne Fehler oder Downgrade von `verdict_bearing`.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/research/c16_arrow/driver.py:533`

**Kategorie:** silent-failure-masquerading-as-success

`verdict_bearing` hängt nur vom Compute-Status und `max_days` ab, nie davon,
wie viele Zellen tatsächlich gemessen wurden — ein Lauf, bei dem ALLE 5
Symbole beim Datenladen scheitern (jede Zelle wird zum p=1.0-Sentinel),
liefert trotzdem `verdict_bearing=True` und CLI-Exit 0.

Bei leerem/veraltetem `HARVEST_DIR` bestehen alle 5 `measure_symbol`-
Aufrufe aus `DataError`, werden zu Sentinel-Zellen, `evaluate_gate` liefert
`MEASURED_GATE_NEUTRAL` mit `quorum=False`, aber `verdict_bearing` bleibt
`True` — ein reiner Datenausfall kann so als echtes DROP-Verdikt für H-16
fehlinterpretiert werden.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/research/c16_arrow/driver.py:558`

**Kategorie:** crash-loses-overnight-run

Die Pro-Symbol-Schleife in `run()` fängt nur `DataError` ab; jede
torch/CUDA-Laufzeit-Exception (OOM, Device-Side-Assert, cuFFT-Fehler —
realistisch über ~140 ResNet-Trainings in einer 8h-Nacht) propagiert nach
oben, das CLI fängt nur `ComputeError` — der gesamte Prozess stirbt ohne
Payload, alle bereits abgeschlossenen Symbol-Zellen (Stunden GPU-Arbeit)
gehen verloren.

BTCUSDT/ETHUSDT/SOLUSDT sind fertig (3–5h Arbeit), bei BNBUSDT tritt ein
OOM auf — der Prozess bricht mit Exit 1 ohne Ergebnisdatei ab, die gesamte
Nacht muss wiederholt werden. Verstößt gegen die T3-Regel ("ein
fehlgeschlagener Teiltest darf den Nacht-Lauf nicht beenden") und die
eigentlich für genau diesen Fall vorgesehene Sentinel-Padding-Logik.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: wave5-c17-venue

#### `src/bybit_edge/research/c17_venue/driver.py:153`

**Kategorie:** degenerate-metric-wrong-result

Ein LOSO-Fold-Testset kann durch eine venue-spezifische Datenlücke im
letzten 3-Wochen-Fenster des Hold-out-Symbols nur EINE Venue-Klasse
enthalten; `balanced_accuracy` degeneriert dann zum Single-Class-Recall,
wodurch der registrierte 0.60-Schwellwert von einem venue-verzerrten
Klassifikator trivial erreicht wird — ohne jede Warnung.

Stoppt z.B. der Binance-Backfill für XRPUSDT Wochen vor dem Bybit-Stream,
enthält das letzte Testfenster nur Bybit-Daten. Ein systematisch auf
"bybit" verzerrter Probe erreicht 1.00 Accuracy, Null-Retrainings mit
permutierten Labels liegen bei ~0.5 — der Fold wird FDR-signifikant und
"besteht", obwohl gar keine echte Venue-Diskrimination mehr gemessen wird.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/research/c17_venue/features.py:415`

**Kategorie:** resource-exhaustion

`load_node_trades` lädt den KOMPLETTEN ~100-Tage-Tick-Stream eines Nodes
per `con.execute(sql).fetchall()` in Python-Tupel plus mehrere
List-Comprehensions — bei realistischen BTCUSDT/ETHUSDT-Volumina
(10^6–10^7 Trades/Tag über ~100 Tage) sind das zig GB Python-Objekte, die
die unbeaufsichtigte T3-GPU-Maschine beim Panel-Laden OOM-killen oder ins
Swap-Thrashing treiben können.

`run_h17.{ps1,sh}` starten den vollen Lauf; das erste `load_panel`
(BTCUSDT/bybit) lädt bereits O(10^8) Zeilen über `fetchall()`
(~15–60+ GB) — der Prozess wird gekillt, bevor überhaupt ein GPU-Training
beginnt. Genau die "unbounded-memory-fetchall"-Klasse, die die erste Review
(2026-07-09) bereits für andere Module flagged; `c17` wurde NACH dieser
Review geschrieben.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: wave5-c18-leadlag-audit

#### `src/bybit_edge/research/c18_leadlag_audit/te_batched.py:13`

**Kategorie:** numerical-equivalence

Die dokumentierte Behauptung, die ~1e-16-Batch-Summierungsabweichung habe
"nie einen p-Wert verändert", ist widerlegbar: Bei exakt gebundenen (tied)
Surrogat-TE-Statistiken (häufig bei kleinen Fenstern/tie-lastigen
quantisierten Serien) bricht die 1-ULP-Rundungsdifferenz zwischen der
seriellen (c17) und der gebatchten (c18) TE-Berechnung exakte
`>=`-Ties in unterschiedliche Richtungen — demonstrierte p-Wert-Sprünge von
bis zu ~0.14 absolut.

Deterministisch reproduziert (numpy-Backend): identischer Input liefert
`p_value=0.5692` seriell vs. `0.6308` gebatcht — die Surrogat-Ensembles sind
bitidentisch, aber mehrere Surrogat-TE-Werte, die dem beobachteten Wert
exakt gleich sind, runden in einer Pipeline knapp darunter, in der anderen
exakt gleich. Bei der registrierten GL-006-Skala (n=3874) traten in 26
Versuchen 0 Flips auf — das reale Risiko für den registrierten BTC/ETH-
Re-Run ist damit gering, aber die Äquivalenz-Garantie selbst ist nicht
generell haltbar.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: layers-early

#### `src/bybit_edge/layers/l3_regime/m12_rqa.py:261`

M12RQA hat keinen Schutz gegen nahezu-konstante (eingefrorene)
Inputserien: Eine konstante oder quasi-konstante Serie drückt `epsilon` auf
den 1e-6-Floor, macht die Recurrence-Matrix vollständig rekurrent und
erzeugt ein Maximalkonfidenz-"Breakout-imminent"-Signal statt keines
Signals.

`M12RQA().compute(np.ones(500))` (z.B. bei gestecktem WS-Feed, illiquidem
Symbol oder wiederholtem Last-Price während eines Reconnects) liefert
reproduzierbar `breakout_signal=True` mit Konfidenz ≈1.0 — ein
eingefrorener Markt erzeugt so das stärkste mögliche
"Konsolidierung-vor-Breakout"-Signal, ohne Fehler oder Low-Confidence-Flag.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/layers/l3_regime/m8_bocpd.py:175`

Eine einzelne NaN-Beobachtung vergiftet die Run-Length-Posterior von
M8BOCPD dauerhaft und lautlos — der Fallback-Zweig für eine entartete
`evidence`-Summe setzt NICHT auf einen sicheren Prior zurück (anders als
die äquivalente Absicherung in M9HMM).

Ein einziger NaN-Wert (z.B. aus einer 0/0-Berechnung auf der OI-Serie)
macht `evidence` zu NaN; da `evidence > 0` für NaN `False` ist, wird der
NaN-vergiftete Array direkt übernommen. Ab diesem Zeitpunkt liefert JEDER
folgende `compute()`-Aufruf — auch mit völlig normalen Werten — dauerhaft
`changepoint_prob=nan`, `changepoint=False`, ohne Exception oder Log-Zeile.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: layers-late

#### `src/bybit_edge/layers/l5_risk/m26_sir.py:219`

Die OLS-Kalibrierung von beta/gamma in M26 SIR verwendet für das GESAMTE
historische Kalibrierungsfenster das AKTUELLE (Berechnungszeitpunkt-)
Open-Interest statt des zum jeweiligen historischen Liquidations-Zeitpunkt
tatsächlich geltenden OI — ein eigenständiger Kausalitäts-/
Daten-Konstruktionsfehler, unabhängig vom bereits dokumentierten
R0-Einheiten-Bug in Zeile 225.

Während einer aktiven Liquidations-Kaskade fällt OI progressiv (z.B. von
10.000 auf 6.000 Kontrakte); `oi_history = [open_interest] * len(liq_events)`
speist aber für JEDEN historischen Zeitpunkt im Fenster das aktuelle
(niedrigste) OI ein — für das erste/früheste Ereignis im Fenster wird
`S(t)` daher massiv unterschätzt. Das verzerrt beta/gamma und damit
r0/cascade_risk/peak_i_forecast systematisch, genau während der Kaskaden,
die das Modul erkennen soll.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/layers/l5_risk/m22_funding_pressure.py:90`

`self._24h_sigma` (Basis des PRD-Gates `|Pressure|>2σ(Pressure_24h)`) wird
über eine hart auf 50.000 Samples gedeckelte Deque berechnet, die bei
realistischer Live-Ticker-Kadenz weit weniger als 24h Daten abdeckt — und
schließt zudem den gerade erst angehängten aktuellen Tick in seine eigene
Referenzverteilung ein.

Da Funding-Settlements etwa alle 8h wiederkehren, ist der extreme
Pressure-Spike des VORHERIGEN Settlements aus dem Buffer bereits
herausgealtert, wenn das nächste Settlement-Entry-Fenster öffnet —
`_24h_sigma` spiegelt dann nur ruhiges Inter-Settlement-Rauschen statt der
echten 24h-Tail-Verteilung, wodurch `pressure_zscore` systematisch überhöht
ist und das Mean-Reversion-Signal auf Werten feuert, die gegen eine echte
24h-Referenz gar nicht extrem wären.

Bestätigt von 2/3 unabhängigen Prüfern.

#### `src/bybit_edge/layers/l5_risk/m24_kalman_premium.py:83`

Der 2D-Kalman-Filter (F/Q, `_predict()`) wird einmal PRO `compute()`-Aufruf
angewendet, ohne die tatsächlich verstrichene Wall-Clock-Zeit zwischen
Aufrufen einzubeziehen — obwohl `compute()` pro unregelmäßigem
Ticker-Update aufgerufen wird, nicht auf festem Timer.

Bei 50 Updates in 5 Sekunden zerfällt `sentiment` mit `F[1,1]=0.95` pro
Call um Faktor ~13x, während ein einzelner Tick nach einer 5-minütigen
Ruhephase im selben Zeitraum nur um Faktor 0.95 zerfällt — eine
Größenordnung Unterschied in der effektiven Zerfallsrate allein durch
Tick-Dichte, nicht durch echte Marktdynamik. `sentiment`/`sentiment_zscore`
und das Fade-Trade-Signal sind dadurch über Regime, Symbole und
Reconnect-Lücken hinweg nicht vergleichbar.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: strategies-execution

#### `src/bybit_edge/replay_backtester.py:490`

**Kategorie:** causality-ordering

Die Tie-Break-Reihenfolge beim Merge des Event-Streams sortiert
`kind='ticker'` (Rang 0) vor `'trade'` (Rang 1) und `'liq'` (Rang 2) bei
gleichem effektivem Timestamp — dadurch wird ein Ticker mit exakt demselben
`ts` wie ein Trade/Liq VOR dessen Ingestion in `trade_buffer`/`liq_buffer`
ausgewertet, ein Verstoß gegen die dokumentierte Invariante "Events mit
ts <= t sind bereits eingeflossen".

Bei einer Liquidations-Kaskade oder Trade-Burst können Zeilen exakt
denselben Timestamp teilen (insbesondere bei ts=0-Legacy-Tickern mit
recv_ts-Fallback). Der Pipeline-Tick, der auf den Ticker feuert, wertet
Strategien (z.B. S1 mit Kyle-Lambda/liq_events/Hawkes) mit Buffern aus,
denen genau die zeitgleichen Trade-/Liq-Zeilen fehlen — sie werden erst
beim NÄCHSTEN Tick sichtbar, was die Erkennung genau der Liquidations-
Burst, die S1 erkennen soll, um ein Throttle-Intervall verzögert. Kein Test
deckt diesen Gleichstand-Fall ab.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: research-modules

#### `src/bybit_edge/research/c01_ofi_tradability/net_edge.py:65`

Der primäre verdikt-tragende Signifikanztest (`bootstrap_mean_le_zero_p`)
resampelt Round-Trip-Net-Edges i.i.d. mit Zurücklegen, obwohl
aufeinanderfolgende Round-Trips sich stark überlappende Forward-Return-
Fenster teilen (überlappende Beobachtungen) — der Bootstrap unterschätzt
dadurch systematisch die wahre Stichprobenvarianz und liefert zu kleine
(anti-konservative) p-Werte, die direkt ins H-05c-WEITER/DROP-Gate
einfließen.

Bei `grid_ms=1000` und einem 5000ms-Capture-Fenster (delta_s=5, einer von
nur zwei GL-010-Survivor-Zellen) überlappen sich 80% der Returns
aufeinanderfolgender Round-Trips — die effektive unabhängige
Stichprobengröße liegt eher bei n/5 als bei n, wodurch der Bootstrap die
Verteilung des Mittelwerts deutlich zu eng schätzt.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: infra-collector

#### `src/bybit_edge/live_runner.py:379`

**Kategorie:** silent-state-desync

`LiveRunner._act_on_decision()` prüft an drei Stellen nie den `retCode`
von `BybitExecutor.close_position()`, bevor `self._position_side` auf
"flat" zurückgesetzt wird — ein fehlgeschlagenes Close desynchronisiert den
getrackten Positionsstatus lautlos von der echten Exchange-Position. (Der
Entry-Pfad direkt daneben prüft `retCode == 0` korrekt.)

`close_position()` kann einen Fehler-Response (unzureichende Margin,
reduce-only rejected, Rate-Limit) zurückgeben, ohne eine Exception zu
werfen — an drei Stellen (Risk-Force-Close, Opposite-Position-Close,
Exit-Action-Handler) wird `_position_side` trotzdem unbedingt geleert. Der
interne State glaubt danach "flat", während am Exchange weiterhin eine
offene Position besteht.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/persistence/backfill.py:121`

**Kategorie:** silent-data-loss-wrong-granularity

`BackfillManager.backfill_klines()`s `skip_if_exists`-Check ruft
`count_klines(symbol, interval)` auf, aber `count_klines` ignoriert
`interval` komplett (die `kline_1min`-Tabelle hat gar keine
Interval-Spalte) — ein Backfill eines Intervalls blockiert (oder
korrumpiert bei `--force`) lautlos einen späteren Backfill mit anderem
Intervall.

Ein Backfill mit 5-Minuten-Kerzen (Default in `backfill_all`/
`backfill_universe`) gefolgt von einem gezielten `--kline-interval 1`-Lauf
für dasselbe Symbol wird von `skip_if_exists` fälschlich als "bereits
vorhanden" erkannt, weil `count_klines` jede Zeile für das Symbol zählt,
unabhängig vom tatsächlichen Intervall.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: scripts-dashboard

#### `scripts/backfill.py:134`

**Kategorie:** silent-data-loss-partial-backfill

`backfill.py` hat keine Pro-Symbol/Pro-Quelle-Exception-Behandlung um die
REST-Backfill-Schleife, und `BackfillManager`s `skip_if_exists`-Check
behandelt jede Teildatenmenge (`count > 0`) als "bereits vollständig
gebackfilled" — ein Netzwerk-/API-Fehler mitten im Lauf trunkiert
historische Forschungsdaten dauerhaft und lautlos.

`main()` umschließt die Pro-Symbol-Schleife nur mit `try/finally` (kein
`except`). Scheitert `_http_get` auf Seite N eines paginierten Pulls
(Rate-Limit, Timeout, transienter 5xx) nach bereits committeten Batches,
propagiert die Exception aus `main()` und beendet das gesamte Script — die
restlichen Symbole werden nie verarbeitet, die bereits geschriebenen
Teildaten bleiben aber in DuckDB und gelten künftig als "vollständig" wegen
des `count > 0`-Checks.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `scripts/c01_ofi_sign_oos.py:85`

**Kategorie:** silent-fdr-family-shrinkage

Scheitert das Laden beider vorregistrierten DEC-15-OOS-Fenster für ein
Symbol, wird es lautlos aus dem Lauf entfernt statt den Lauf fehlschlagen
zu lassen oder eine Protokoll-Abweichung zu flaggen — die F-OFI-INV-BH-
Familie schrumpft dadurch unbemerkt vom registrierten 5-Symbol-Universum,
ohne abweichenden Exit-Code oder "Partial-Run"-Markierung im Payload.

Schlägt `load_harvest_window` für ein Symbol fehl (transiente Harvester-
I/O-Lücke), läuft das Script mit nur 4 statt 5 Symbolen weiter, schreibt
Ergebnisse und gibt `rc=0` zurück — identisch zu einem vollständigen
5-Symbol-Lauf. Die BH-FDR-Korrektur in `run_oos` rechnet über die
tatsächlich geladene, nicht die registrierte Familiengröße, wodurch
`p_crit` und alle `fdr_significant`-Flags verfälscht werden.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `scripts/c17_venue.py:143`

**Kategorie:** compute-gate-inconsistency

Anders als alle anderen Wave-5-GPU-gegateten Geschwister-CLIs
(`c14_panellag`, `c15_grammar --mode full`, `c16_arrow`) hat
`c17_venue.py` kein explizites Opt-in-Flag für einen Non-GPU-Lauf und
keinen dedizierten SKIP-Exit-Code: Ohne CUDA fällt es lautlos auf eine
numpy-Pipeline-Smoke-Encoder zurück und gibt trotzdem Exit 0 zurück —
identisch zu einem echten, verdikt-tragenden GPU-Lauf.

Während `c14`/`c16` ohne `--allow-cpu-fallback` mit `RC_SKIP_NO_COMPUTE`
verweigern und `c15` im Default-Mode ohne CUDA hart fehlschlägt, druckt
`c17_venue.py` bei fehlendem `use_torch` nur eine stderr-WARNUNG und läuft
dann komplett durch (~1–2 GPU-Tage geschätzter Aufwand, tatsächlich auf
CPU/numpy) und schreibt am Ende `RC_OK`. Ein Operator oder eine künftige
Automatisierung, die das Script direkt aufruft (statt über `run_h17.sh`,
das separat vorprüft), kann einen wertlosen CPU-Smoke-Lauf nicht von einem
echten GPU-Lauf unterscheiden.

Bestätigt von 3/3 unabhängigen Prüfern.

---

## Medium (6 Befunde)

### Lane: wave5-c14-panellag

#### `src/bybit_edge/research/c14_panellag/ablation.py:249`

**Kategorie:** statistical-bias-eval-set-asymmetry

Die beobachtete Teststatistik T(j→i) vergleicht OOS-Losses, die auf
systematisch unterschiedlichen Anker-Mengen ausgewertet werden (jeder Task
berechnet `valid_sample_indices` neu aus der eigenen, verschobenen
Matrix), während die Null-Delta-Verteilung (verschoben-vs-verschoben,
symmetrisch um 0) diesen Anker-Zusammensetzungs-Offset nicht modellieren
kann — ein familienweiter Bias in dieselbe Richtung für alle 99 Edges und
die Positivkontrolle.

Reale, gekappte NaN-Lücken (>60s ohne Trades, häufig bei dünneren Feeds)
sind cross-venue zeitlich korreliert (Ausfälle, ruhige Stunden) — das
Full-Model-Anker-Set unterscheidet sich dadurch systematisch von jedem
Surrogat-Lauf, dessen Lücken zufällig rotiert sind. Ein solcher
Composition-Offset kann viele Edges gleichzeitig — und identisch in BEIDEN
Fenstern — über die q95-Schwelle drücken, wodurch das
Zwei-Fenster-Erfordernis keinen Schutz mehr bietet.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: wave5-c16-arrow

#### `src/bybit_edge/research/c16_arrow/stats.py:113`

**Kategorie:** anti-conservative-statistics

Der exakte gepaarte Sign-Test nimmt laut Docstring an, dass die
(fwd>rev)-Vorzeichen "unabhängig über Hold-out-Fenster" seien — bei Stride
64s und Fensterlänge 512s teilen sich aufeinanderfolgende Testfenster
jedoch 87.5% ihrer Rohdaten, die Vorzeichen sind also stark positiv
korreliert; Binomial(n_eff, 1/2) unterschätzt die Varianz massiv (effektive
unabhängige Anzahl ≈ n/8), wodurch die p-Werte für das BH-FDR-Gate
anti-konservativ sind.

Bei einer minimalen echten (oder artefakthaften) gerichteten Asymmetrie
(z.B. wahre Vorzeichenwahrscheinlichkeit 0.52) über ~27.000 korrelierte
Paare liefert der Sign-Test einen astronomisch kleinen p-Wert und macht
`fdr_significant` praktisch immer wahr, sobald AUC nur marginal über 0.5
liegt — die IAAFT-Surrogat-Kontrolle kalibriert dies nicht, da sie nur
AUC-Mean/p95 gated, nie den Sign-Test-p unter Abhängigkeit.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: wave5-c17-venue

#### `scripts/c17_venue.py:175`

**Kategorie:** late-failure-total-compute-loss

Die c12-Redundanz-Payload wird zwar beim Start gelesen, aber erst NACH dem
vollen 1–2-Tage-GPU-Lauf strukturell verwendet (`redundancy_gate` ist der
letzte Schritt); eine JSON-valide, aber strukturell unerwartete c12-Datei
(Array-Root, fehlende/null `lambda2`/`ipr_v2`) wirft dort
AttributeError/KeyError/TypeError — `main()` fängt aber nur `ValueError`,
sodass die Ergebnisse aller ~105 Trainings verloren gehen (JSON/MD werden
erst nach `run()` geschrieben, kein Resume dokumentiert).

Ein c12-File mit abweichendem Schema (z.B. NaN-`lambda2` als `null`
serialisiert, was c17s eigene `_dumps` exakt so produziert) lässt
`driver.run()` erst alle 5 Folds x 21 Retrainings durchlaufen
(~1–2 GPU-Tage), dann in `redundancy_gate` mit einer nicht abgefangenen
Exception abstürzen — ein in Millisekunden beim Start erkennbarer Fehler
zerstört so einen mehrtägigen geschützten T3-Lauf vollständig.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: wave5-c18-leadlag-audit

#### `src/bybit_edge/research/c18_leadlag_audit/driver.py:167`

**Kategorie:** preregistration-binding

`_verdict_carrying()`/`mode='resolution_audit'` binden nur an
(`backend=='torch-cuda'` AND `n_surrogates>=100000`), nicht aber an die
vorregistrierte H-18-Methodik (Seed 42, 2 Fenster, GL-006-Parameter) — ein
CUDA-100k-Lauf mit z.B. `--seed 99` liefert `verdict_carrying=true` und
echte T1/T2-Booleans, nicht unterscheidbar vom registrierten Audit in
SUMMARY/CLI-Output.

Ein Operator (oder künftige Automatisierung) kann `--seed` wiederholt
variieren, bis `t1_holds`/`t2_holds` das gewünschte Ergebnis liefern
(~1h/Lauf, über zwei Wochen unbeaufsichtigt machbar) — jeder solche Payload
trägt `verdict_carrying=true` und passiert den Data-Binding-Check, da nur
seed-unabhängige Statistiken verglichen werden. Der einzige Hinweis ist das
rohe `seed`-Feld, das in keiner SUMMARY/CLI-Ausgabe gegen den registrierten
Wert geprüft wird — anders als bei jeder anderen Abweichung (Backend, N,
Paar/Lags, Fensterdrift), die ehrlich geflaggt wird.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: layers-early

#### `src/bybit_edge/layers/l3_regime/m9_hmm.py:320`

`M9HMM.compute()` validiert Form/Länge des Input-Feature-Vektors nicht —
ein missgebildetes oder leeres Features-Array crasht mit einer
unbehandelten `ValueError` statt geordnet zu degradieren.

`compute(np.array([]))` (oder jedes Array mit Länge != `n_features=3`,
z.B. aus einem Upstream-Feature-Builder bei einer Datenlücke) wirft
reproduzierbar `ValueError: operands could not be broadcast together` in
`_gaussian_emission`. Anders als M6–M8/M10–M13 im selben Layer, die
degenerierte Inputs tolerieren, stürzt der Regime-Layer hier komplett ab.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: strategies-execution

#### `src/bybit_edge/strategies/strategy1_cascade.py:268`

**Kategorie:** statistical-self-reference-bias

`_is_b_value_extreme` (und analog `_is_entropy_collapsed` in
`strategy2_entropy_momentum.py`) testet, ob der AKTUELLE Tick-Wert extrem
relativ zu Mean/Median und Std einer History-Deque ist, in die der
aktuelle Wert bereits EINE ZEILE VORHER eingefügt wurde — der getestete
Wert steckt in seiner eigenen Referenzverteilung.

Kein Look-ahead (nur Vergangenheits-/aktuelle Daten), aber ein
Selbstreferenz-Bias: Nahe der Mindest-Sample-Schwelle (jedes Sample trägt
~1–2% Gewicht) zieht ein wirklich extremer aktueller Wert den Mean/Median
zu sich selbst und bläht die Std auf — der Extremwert-Test wird dadurch
systematisch schwerer auszulösen genau dann, wenn das zugrundeliegende
Ereignis am extremsten ist (selbstdämpfend), was die statistische
Evidenzgrundlage der S1/S2-Entry-Gates für das Falsifikationsverdikt
untergräbt.

Bestätigt von 3/3 unabhängigen Prüfern.

---

## Verworfene Kandidaten

**1 von 35 Kandidaten-Befunden hat die adversariale Verifikation NICHT
überlebt** (keine Mehrheit von mindestens 2/3 CONFIRMED unter den
Skeptiker-Agenten):

- **`scinance2-impl/handoff_local/run_h16.ps1`** (Lane: wave5-c16-arrow) —
  Behauptung: Das Script berechnet `$exit` (0=OK/1=FAIL/2=SKIP) und
  schreibt ihn in die SUMMARY, ruft aber nie `exit $exit` auf, sodass der
  Prozess immer mit Exit-Code 0 terminiert — entgegen dem eigenen
  dokumentierten Exit-Code-Vertrag und als einziger von ~20 Runnern in
  `handoff_local` ohne abschließendes `exit`.
  **NICHT bestätigt** — der Datensatz enthält für diesen Kandidaten keine
  weiteren Detail-Voten der Skeptiker-Agenten, nur die verworfene
  Behauptung selbst.
