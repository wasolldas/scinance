# Kritische Code-Review – Scinance 2.0 (Stand 2026-07-09)

## Was ist das

Dies ist die Destillation eines adversarialen Fable-5-Review-Netzwerks über die
gesamte Scinance-2.0-Codebasis. 11 parallele "Lanes" (Recorder/Collector,
State-Layer, Orchestrierung/Execution, Layers L1–L5, Strategien/Backtest,
sowie vier Forschungs-Wellen und Dashboard/Scripts) haben unabhängig
voneinander Kandidaten-Befunde erzeugt. Jeder einzelne Befund wurde
anschließend von **drei unabhängigen Skeptiker-Agenten** gegengeprüft, die den
Code selbst gelesen und den behaupteten Fehlerpfad nachvollzogen haben; ein
Befund "überlebt" nur bei Mehrheitsvotum (mindestens 2 von 3 CONFIRMED).

**Ergebnis: 40/40 Kandidaten-Befunde bestätigt, 0 verworfen.**

Dieser Bericht ist eine reine, verlustarme Verdichtung der bereits verifizierten
Ergebnisse — es wurden keine eigenen Bewertungen, Meinungen oder zusätzlichen
Befunde ergänzt.

> **Update 2026-07-09 — Bugfix-Runde abgeschlossen:** Alle 5 Critical-Befunde
> sind gefixt, regressionsgetestet und committed (3 parallele Fable-5-Fix-
> Agenten, je eigenständig von mir verifiziert und committed):
> - `recorder/recording_engine.py:620` + `recorder/storage.py:208` → Commit `d8b3f5b`
> - `strategies/strategy1_cascade.py:297` + `layers/l4_pattern/m15_gr_omori.py:218` → Commit `3ebdc24`
> - `research/c01_ofi_sign/oos.py:138` → Commit `c61229f` (inkl. Transparenz-Nachtrag
>   zu GL-010/GL-011 in `gate_log.md` und DEC-23 — Verdikte selbst unverändert,
>   siehe dort für die materielle Bewertung)
>
> Die 21 High- und 14 Medium-Befunde unten sind **noch offen** (keine Fix-Runde
> angestoßen) — dokumentierter Backlog, nicht blockierend für den weiteren
> Programmablauf.

## Zusammenfassung

| Schweregrad | Anzahl |
|---|---|
| Critical | 5 |
| High | 21 |
| Medium | 14 |
| **Gesamt (bestätigt)** | **40** |
| Verworfen (refuted) | 0 |

Inhalt nach Schweregrad, darin gruppiert nach Lane:

- [Critical](#critical-5-befunde)
- [High](#high-21-befunde)
- [Medium](#medium-14-befunde)
- [Verworfene Kandidaten](#verworfene-kandidaten)

---

## Critical (5 Befunde)

### Lane: collector-recorder

#### `src/bybit_edge/recorder/recording_engine.py:620`

**Kategorie:** silent-failure-resource-exhaustion

`_run_housekeeping` ruft `_maybe_flush()` und `cap.enforce()` ungeschützt auf.
Eine einzelne Flush-Exception tötet die Housekeeping-Task dauerhaft und
lautlos, wodurch das Ring-Buffer-Storage-Cap und die Telemetrie stillstehen,
während der Dauerbetrieb-Recorder (Schutzgut) weiterschreibt.

Ein transienter Dateisystemfehler (Disk kurzzeitig voll, Permission-Hiccup,
`mkdir`-Fehler in `ParquetStreamWriter.flush`) lässt die Exception aus
`_maybe_flush()` (Zeile 620) entkommen und beendet die Coroutine dauerhaft;
`stop()` schluckt die gespeicherte Task-Exception mit
`except (asyncio.CancelledError, Exception): pass` (Zeilen 697–701) komplett.
Ab diesem Zeitpunkt läuft `cap.enforce()` nie wieder, `data/parquet/recording_f0/`
wächst unbegrenzt über das konfigurierte `--cap-gb` hinaus, bis die Festplatte
vollläuft — was wiederum den Recorder selbst sowie das co-lokalisierte
1.0-Kaltspeicher/DuckDB auf derselben Disk gefährdet. Kein Fehler wird
irgendwo sichtbar außer einer einzigen, längst vergangenen Log-Zeile.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/recorder/storage.py:208`

**Kategorie:** data-loss-write-ordering

`ParquetStreamWriter.flush()` leert den In-Memory-Buffer (`self._buffer = []`)
**bevor** das Parquet-Segment dauerhaft geschrieben ist; jede Exception aus
`mkdir`/`pa.table`/`pq.write_table` verwirft dauerhaft bis zu `flush_rows`
(2000) aufgezeichnete Zeilen, und die entweichende Exception destabilisiert
zusätzlich die WS-Loop.

Schlägt `pq.write_table` fehl (volle Disk, Antivirus-Lock, transienter
OSError), sind die Zeilen bereits aus `self._buffer` entfernt und damit
unwiederbringlich verloren — ohne Zähler oder ERROR-Log, der den Datenverlust
zuordnet. Die Exception propagiert weiter über `_run_ws_transport`s generisches
`except Exception`, was als "connection lost" geloggt wird und einen Reconnect
auslöst, **ohne** den noch offenen WebSocket zu schließen (Leck einer
Live-Verbindung pro Zyklus); ein fehlschlagender `writer.close()` in `stop()`
bricht zudem die gesamte Writer-Loop ab, sodass beim Shutdown auch alle
übrigen gepufferten Zeilen aller Streams lautlos verloren gehen.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: layers-l4-l5

#### `src/bybit_edge/layers/l4_pattern/m15_gr_omori.py:218`

**Kategorie:** data-corruption

M15 verarbeitet `liq_events` mit Delta-Semantik ("neue Liquidation-Events")
und hängt sie an den internen 24h-Buffer an — beide echten Aufrufer
(`replay_backtester.py:642–645` und `live_runner.py:281–284`) übergeben jedoch
bei **jedem** Tick das komplette rollierende 1h-Fenster aus
`liq_buffer.recent_by_ts(3600)`. Jedes Event wird dadurch pro Tick erneut
angehängt, ohne Deduplizierung — sämtliche M15-Statistiken (Aki-b-Value,
Q99-Mainshock-Schwelle, Omori-Aftershock-Rate) werden über ein massiv
dupliziertes Event-Multiset berechnet.

Bei einer Kaskade mit ~200 Events im 1h-Fenster und Pro-Tick-Kadenz wird jedes
Event hunderte Male im 100k-maxlen-Deque dupliziert; echte 24h-Historie wird
verdrängt, sodass der "24h"-Q99 und b-Value in Wahrheit dupliktionsgewichtete
Statistiken des jüngsten Fensters sind, und die Omori-Histogramm-Zählungen
K und aftershock_rate aufblähen. Da `replay_backtester` Strategy1 über diesen
Pfad treibt, basiert jedes S1-Replay-/Falsifikationsergebnis (b-Value-Gate,
`omori_active`, `aftershock_rate` und damit die WEITER/DROP-Gate-Evidenz) auf
korrumpierten Statistiken.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: strategies-backtest

#### `src/bybit_edge/strategies/strategy1_cascade.py:297`

**Kategorie:** causality-wallclock-in-replay

S1s Omori-Decay-Exit verwendet Wall-Clock-Zeit `time.time()` gegen den
Event-Zeit-`mainshock_ts`. In jedem historischen Replay ist die vergangene
Zeit dadurch Stunden bis Monate groß, die Exit-Bedingung `t > 5*c` ist immer
wahr, und jede S1-Position wird beim allerersten In-Trade-Tick zwangsweise
geschlossen.

`ReplayBacktester` spielt wochenalte DuckDB-Ticks ab und übergibt Event-Zeit
`current_ts` an `Strategy1.on_data`; beim nächsten Pipeline-Tick berechnet
`_check_exit` `elapsed = time.time() - mainshock_ts` (~6e5 bis 1e7 Sekunden,
da `mainshock_ts` ein historischer Event-Timestamp ist), was jede realistische
Schwelle `S1_OMORI_DECAY_FACTOR*c` überschreitet. Jeder replayte S1-Trade
dauert dadurch exakt ein Pipeline-Intervall (~1s) — die S1-PnL/Sharpe/Winrate,
die in das WAVE1-Urteil "S1 empirisch DROP" einfloss, hat also
Spread+Fee-Rauschen von Sofort-Roundtrips gemessen, nicht die
Mean-Reversion-Hypothese. Das widerspricht direkt der vom Replay-Modul
zugesicherten "strikten Kausalität (kein Lookahead)".

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: research-wave1-2

#### `src/bybit_edge/research/c01_ofi_sign/oos.py:138`

**Kategorie:** window-boundary-sql-precedence

Das SQL-WHERE in `load_harvest_window` hat einen AND/OR-Präzedenzfehler:
`ts_exchange_ms IS NOT NULL AND ts_exchange_ms >= {start_ms} AND side IS NOT NULL OR S IS NOT NULL`
wird als `(... AND ... AND side IS NOT NULL) OR (S IS NOT NULL)` geparst.
Jede Zeile im LIVE-Payload-Format (Schlüssel `$.S`) umgeht dadurch **beide**
Filter — sowohl den NULL-Timestamp-Filter als auch den vorregistrierten
Fenster-Start-Filter.

Empirisch gegen DuckDB verifiziert: Sowohl eine Live-Form-Zeile mit
`ts=50 < start_ms=90` als auch eine mit `ts=NULL` werden zurückgegeben. Folgen:
(a) Ticks von **vor** dem vorregistrierten OOS-Fenster-Start (H-05b) gelangen
lautlos ins Fenster und verdrängen (wegen `ORDER BY ts LIMIT max_ticks`)
gültige In-Window-Ticks; (b) NULL-ts-Zeilen werden zu NaN im ts-Array, sodass
`bin_ofi` entweder crasht oder alle OFI/Return-Paare lautlos verwirft. Dieser
Loader speist sowohl den GL-010 H-05b-WEITER-Lauf als auch den GL-011
H-05c-Lauf. Fix: OR-Klausel korrekt klammern.

Bestätigt von 3/3 unabhängigen Prüfern.

---

## High (21 Befunde)

### Lane: collector-recorder

#### `src/bybit_edge/recorder/recording_engine.py:342`

**Kategorie:** wrong-data-endpoint-mix

Mit der Standard-Betreiberkonfiguration mischt der Recorder lautlos
TESTNET- und MAINNET-Marktdaten in einem Forschungsdatensatz: Linear-WS und
Premium-Index-REST folgen `config.BYBIT_TESTNET` (Default `true`, von
`scripts/setup_local.sh` ins `.env` geschrieben), während `OPTION_WS_URL`
hartcodiert auf den Mainnet-Endpunkt zeigt — ohne Endpunkt-Herkunftsmarkierung
in den Parquet-Segmenten.

Nach `setup_local.sh` + `start_recorder.ps1` verbindet sich der Linear-WS/REST
mit Testnet, während `option_tickers` fest an
`wss://stream.bybit.com/v5/public/option` (Mainnet) hängt. RPI-Orderbook,
Insurance-Pool-Salden und Premium-Index-Klines sind dann Testnet-Artefakte
neben echten Mainnet-Options-IVs — ohne jede Möglichkeit, dies nachträglich
zu erkennen, da Segmente keinen Endpunkt-Tag tragen. Monate an
Schutzgut-Aufzeichnung können dadurch wissenschaftlich wertlos sein.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/persistence/db.py:782`

**Kategorie:** duplicate-data-pagination

`backfill_kline` geht davon aus, dass Bybit Klines "oldest-last" liefert, doch
die v5-`/v5/market/kline`-API sortiert newest-first. `candles[-1][0]` entspricht
damit dem Fensterstart, der Cursor rückt pro 200-Minuten-Request nur eine
einzige Minute vor, und ~199 von 200 Candles werden bei jeder Iteration erneut
in `kline_1min` eingefügt (keine PK/Dedup).

Bei `backfill_kline('BTCUSDT', months=6)` wird jede 1-Minuten-Kerze bis zu
~200-mal dupliziert — jedes nachgelagerte Aggregat (Volumen, OHLC-Resampling,
Walk-Forward-Fenster) wird dadurch massiv falsch, und der Backfill benötigt
~200x so viele API-Calls und läuft tagelang.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: state-layer

#### `src/bybit_edge/state/trade_buffer.py:30`

**Kategorie:** data-corruption

`TradeEvent.from_ws` füllt lautlos alle Felder mit 0/leer, wenn ihm das
Bybit-REST-Recent-Trade-Schema statt des WS-Schemas übergeben wird — und genau
das passiert beim Reconnect-Resync des Collectors, wodurch ~50 korrupte
Trades (`price=0.0`, `timestamp_ms=0`, `side=""`) in den TradeBuffer und die
persistierte `trades`-Tabelle injiziert werden.

`ws_collector._snapshot_resync` holt `/v5/market/recent-trade` (Schema
`{execId, price, size, side, time, isBlockTrade}`) und leitet jedes Item an
`TradeEvent.from_ws` weiter, das nur WS-Kurzschlüssel (`T/p/v/S/BT`) liest.
Diese ~50 Garbage-Events pro Reconnect fließen sowohl in Kyle-Lambda/OFI/Hawkes
als auch unkonditioniert in die persistierte Trades-Tabelle — ohne jeden
Fehler. Da Reconnects (Netz-Hänger, Bybits 24h-Verbindungsrecycling) routinemäßig
auftreten, wiederholt sich dies in jeder langlaufenden Collector-Session mit
Persistenz.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/state/orderbook_state.py:69`

**Kategorie:** silent-state-desync

`apply_delta` prüft keinerlei Update-ID-/Sequenz-Kontinuität und invalidiert
das Buch bei fehlgeschlagenem/partiellem Apply nie: `last_update_id` wird
gespeichert, aber nie geprüft — gelappte, doppelte, unsortierte oder halb
angewendete Deltas desynchronisieren das Buch lautlos für alle nachgelagerten
Konsumenten.

Zwei konkrete Pfade: (1) `ws_collector._dispatch` fängt Exceptions ab und
macht weiter — bricht `apply_delta` mitten in der Anwendung ab (z.B. bei
malformter Preis-/Größenangabe), bleibt das Buch halb aktualisiert, ohne
Resync bis zum nächsten Reconnect; (2) die Queue verwirft bei Überlauf die
ältesten Nachrichten, ohne dass `OrderbookState` die Lücke bemerken kann.
Resultat: veraltetes/gekreuztes Buch (`best_bid > best_ask` darstellbar und
unerkannt), falsche `mid_price`/Spread/Imbalance, sowie bei aktiviertem
`PERSIST_ORDERBOOK` korrumpierte 1-Hz-L2-Snapshots, die Replay/Forschung
später als Ground-Truth behandeln.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: orchestration-execution

#### `src/bybit_edge/live_runner.py:470`

**Kategorie:** silent-data-loss

`_flush_persist` leert die Tick-Buffer destruktiv **vor** dem Schreiben und
requeued bei Fehlern nie — jede DuckDB-Schreib-Exception verwirft lautlos und
dauerhaft ein ganzes Flush-Fenster an Tickern/Trades/Liquidationen/
Orderbook-Snapshots; die drei `write_*_batch`-Aufrufe laufen zudem nicht in
einer Transaktion.

Bei einer transienten DuckDB-`IOException` während `write_trades_batch`
(volle Disk oder die in `CLEANUP_PLAN.md` dokumentierte
Cross-Prozess-Dateisperren-Konkurrenz) sind `self._buf_tickers` etc. bereits
auf `[]` zurückgesetzt, bevor der try-Block beginnt — der Exception-Handler
loggt nur, die ausgetauschten Listen werden garbage-collected. Ticker können
halb committed sein, während Trades/Liquidationen/OB-Snapshots des Fensters
komplett verloren gehen. Der Prozess läuft und heartbeatet weiter und täuscht
einen gesunden Recorder vor.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/live_runner.py:799`

**Kategorie:** silent-failure-masquerading-as-success

Schlägt die Executor-Initialisierung fehl, loggt `run()` "Executor-Init
fehlgeschlagen — laufe read-only weiter", entwaffnet aber nichts wirklich:
`self.executor` bleibt gesetzt und `_execution_active()` bleibt `true`, sodass
später weiterhin Orders platziert werden — mit nie synchronisiertem
Positionsstatus und Risikobudget.

Bei `EXECUTION_ENABLED=true` auf einem Demo-Account mit bereits offener
Short-Position: schlägt `set_leverage()`/`get_equity()` beim Start transient
fehl, wird die falsche "read-only"-Behauptung geloggt, aber
`self._position_side` bleibt `""` und das Risikobudget wird nie geladen. Bei
der nächsten "long"-Entscheidung hält `_act_on_decision` den Account
fälschlich für flach, überspringt das Schließen der Gegenposition und sendet
einen Buy-Market-Order gegen die tatsächliche Short-Position — Tracked-State
und Exchange-State divergieren für den Rest der Session.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: layers-l1-l2

#### `src/bybit_edge/layers/l2_denoising/m5_ffd.py:197`

**Kategorie:** wrong-results-stale-state

`M5FFD.compute()` meldet einen veralteten ADF-p-Value und Konfidenz aus einem
vorherigen Aufruf: `self._last_adf_pvalue` wird wiederverwendet, sobald es
nicht `None` ist, und der Fallback-Pfad von `_find_optimal_d` (kein d
besteht, Rückgabe 1.0) räumt diesen Wert nie auf — eine Serie, die bei
**jedem** Grid-d durchfällt, wird mit dem p-Value der vorigen Serie und
nahezu maximaler Konfidenz gemeldet.

Empirisch reproduziert: Aufruf 1 auf stationärer Serie liefert p=0.001;
Aufruf 2 auf einer reinen linearen Rampe (jeder Grid-d-ADF-Test schlägt fehl)
liefert trotzdem `d=1.0`, `adf_pvalue=0.001`, `confidence=0.999` statt
`p>=0.99`/`None`/`confidence=0.0`. In diesem Falsifikationsprogramm ist der
ADF-p-Value die Stationaritäts-Evidenz — eine nicht-stationäre Eingabe wird
lautlos als stark stationär gemeldet. Konsumiert von
`Strategy4PatternEnsemble.on_data` bei jedem Tick.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: layers-l3

#### `src/bybit_edge/layers/l3_regime/m8_bocpd.py:169`

**Kategorie:** resource-exhaustion

Die BOCPD-Run-Length-Verteilung und die NIG-Suffizienzstatistik-Arrays
wachsen pro `compute()`-Aufruf um ein Element ohne jedes Pruning/Trunkierung
— unbegrenzter Speicherverbrauch und O(t) pro Schritt bzw. O(T²) kumulativ in
einem Modul, das für Dauerbetrieb ausgelegt ist.

Bei sekündlichem Aufruf (Pipeline, Strategy3, Replay) summiert sich ein
30-Tage-Replay (~2,6 Mio. Schritte) zu ~O(T²) Elementoperationen mit
`gammaln` (keine Low-Mass-Hypothesen-Prunung) — Monats-Replays hängen sich
effektiv auf, und ein langlaufender Live-/Recording-nahmer Prozess
akkumuliert Speicher und Pro-Tick-Latenz unbegrenzt, bis er dem Tick-Stream
nicht mehr folgen kann.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/pipeline.py:158`

**Kategorie:** silent-failure

Die Live-Pipeline füttert den M9-HMM mit konstanten Platzhalter-Features
(`realized_vol` hartcodiert 0.02, OFI-Sign hartcodiert 0.0), und
`M9.compute()` prüft nie das `_fitted`-Flag — die Pipeline gibt plausibel
aussehende Regime-States/Konfidenzen aus, fabriziert aus handjustierten
Default-Emissionsparametern und Fake-Eingaben.

`pipeline.process_ticker` ruft bei jedem Tick `self.m9.compute(np.array([0.02, 0.0, funding_rate]))`
auf; kein Aufrufer ruft je `M9HMM.fit()`. Der HMM-Forward-Schritt läuft auf
2 konstanten Features + Funding-Rate gegen die hartcodierten
Default-Emissionsmittel/-varianzen und liefert State/Label/Wahrscheinlichkeiten/
Konfidenz, die wie ein funktionierender Regime-Detektor aussehen — ohne
Fehler, Warnung oder "unfitted"-Markierung.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: layers-l4-l5

#### `src/bybit_edge/strategies/strategy1_cascade.py:297`

**Kategorie:** causality-wall-clock-vs-event-time

`Strategy1._check_exit` berechnet den Omori-Decay-Exit als
`elapsed = time.time() - m15_out['mainshock_ts']` und mischt damit
Wall-Clock-"jetzt" mit dem historischen Event-Zeit-Mainshock-Timestamp,
obwohl die Strategie im Replay-Harness sonst über `current_ts` (Event-Zeit)
gesteuert wird.

In jedem Replay ist `mainshock_ts` Stunden bis Monate in der Vergangenheit,
während `time.time()` die Laufzeit ist — `elapsed` übersteigt daher immer
`S1_OMORI_DECAY_FACTOR * c`, sodass jeder S1-Trade mit gesetztem
`omori_params` bereits beim nächsten Tick mit Grund `omori_decay` schließt.
Alle Replay-abgeleiteten S1-Trade-Dauern und PnL sind dadurch systematisch
verkürzt und verzerren die Falsifikations-Evidenz, auf der die
Gate-Entscheidung beruht.

*(Hinweis: gleiche Codestelle wie der Critical-Befund oben; hier separat
unter der Kategorie "causality-wall-clock-vs-event-time" bestätigt.)*

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/layers/l4_pattern/m19_timesnet.py:310`

**Kategorie:** silent-failure-masquerading-as-success

Ist `torch` nicht verfügbar (ein explizit unterstützter Optional-Modus), ist
`M19TimesNet.fit()` ein No-Op, setzt aber trotzdem `self._fitted = True` —
`compute()` läuft dadurch am Untrained-Guard vorbei und nutzt den
All-Null-Forecast von `_forward_np`, um ein Richtungssignal auszugeben, statt
dem dokumentierten Vertrag "ohne Training: Zero-Forecast, signal=0,
confidence=0" zu folgen.

Ohne `torch` ergibt jede `compute()`-Berechnung `delta = 0 - last_price`,
also z.B. bei BTC ~60000 ein `forecast_direction = signal = -1` mit
`confidence = 1.0` bei **jedem** Tick — ein dauerhaftes
Maximal-Konfidenz-Short-Signal von einem nie trainierten Modell, ohne
jeglichen Fehler (nur eine Log-Warnung beim Import). `M18PatchTST` behandelt
denselben Fall korrekt.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/layers/l5_risk/m26_sir.py:225`

**Kategorie:** wrong-results-unit-inconsistency

M26 SIR mischt inkompatible Einheiten: `beta`/`gamma` werden auf absoluter
S-Skala (~Open-Interest) pro Event-Index-Zeitschritt kalibriert (oder fallen
auf 0.001/0.1 zurück), aber (a) `R0 = beta*s_current/gamma` wird gegen die
epidemiologische Schwelle 1.0 in absoluten Einheiten verglichen, und (b) die
Vorwärts-`odeint`-Simulation wendet dasselbe `beta`/`gamma` auf
**normalisierte** Kompartiment-Fraktionen an — `peak_i_forecast` ist dadurch
um Größenordnungen falsch.

Bei weniger als 10 `liq_events` (üblicher ruhiger Markt, Kalibrierung
übersprungen, Fallback `beta=0.001`, `gamma=0.1`) ergibt
`r0 = 0.01 * s_current` (s_current ~ Open Interest in zehntausenden
Kontrakten) einen R0 im Hunderte-bis-Millionen-Bereich — `cascade_risk`/
`signal=1` feuert praktisch bei jedem Tick mit nur geringen Liquidationen,
und S1s "R0 > 1"-Entry-Gate wird gegenstandslos.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: strategies-backtest

#### `src/bybit_edge/strategies/strategy1_cascade.py:303`

**Kategorie:** wrong-baseline-instant-exit

`_pre_cascade_oi` wird **beim Entry** erfasst (Zeile 188), also bereits auf
dem kaskadenbedingt eingebrochenen OI-Niveau, sodass der
"OI-Erholung > 95% des Pre-Cascade-Levels"-Exit
(`open_interest / _pre_cascade_oi > 0.95`) sofort ~1.0 beträgt und die
Position beim nächsten Tick zwangsweise schließt — live wie im Replay.

Der Entry setzt voraus, dass die Omori-Aftershock-Phase aktiv ist, d.h. der
Open Interest bereits eingebrochen ist. Einen Tick später ist der OI kaum
verändert, `recovery_pct ~= 1.0 > 0.95` — der Exit `oi_recovery` feuert,
sofern der OI nicht binnen ~1 Sekunde weiter um >5% fällt. Unabhängig vom
Wall-Clock-Bug (Zeile 297) kann S1 dadurch strukturell keine
Mean-Reversion-Position halten — alle S1-Backtest-Schlüsse basieren auf
degenerierten Ein-Tick-Trades.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/tuning/optuna_tuner.py:84`

**Kategorie:** tuning-selection-leakage

Das Optuna-Objective maximiert Sharpe auf den Walk-Forward-**TEST**-Folds
(die Train-Phase ist reines State-Warmup, keine Parameteranpassung), und
`tune.py` meldet `best_value` als "best_sharpe" ohne Held-out-Fenster — die
gemeldete Out-of-Sample-Metrik ist ein Maximum über 50 Trials, selektiert auf
genau den Daten, für die sie berichtet wird.

Jeder Optuna-Trial berechnet Sharpe ausschließlich aus den zusammengefügten
Test-Fold-Trades; TPE wählt den Parametersatz mit dem höchsten Sharpe auf
diesen selben Test-Folds, und `tune.py` schreibt ihn als vermeintlich echte
Walk-Forward-OOS-Performance nach `tuning_results.json`. Bei ~50 Ziehungen
über ein verrauschtes Sharpe ist das Maximum selbst bei einer Strategie ohne
echten Edge stark positiv verzerrt — jede Gate-/Registry-Entscheidung, die
`best_value` konsumiert, überschätzt den Edge systematisch.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/training/dataset.py:290`

**Kategorie:** label-lookahead-leakage

`TickDataset` bildet die Vol-Spike-Klassifikationsschwelle als
`np.quantile(future_vol, q)` über die **gesamte** Tick-Serie, bevor ein
chronologischer Train/Val-Split stattfindet — Trainings-Labels werden also
mithilfe der Volatilitätsverteilung der Validierungs-/Zukunftsperiode
definiert.

Bei einem späteren chronologischen Split verschiebt ein Vol-Regimewechsel im
späteren (Validierungs-)Segment die globale Schwelle und relabelt die
früheren (Trainings-)Fenster rückwirkend: z.B. führt ein ruhiger erster Monat
gefolgt von einem volatilen zweiten Monat zu nahezu keinen Positiv-Labels im
Training und konzentrierten Positiven im Val-Set. Jedes M1-Trainings-/
Validierungsergebnis aus `TickDataset` ist dadurch durch Lookahead in der
Label-Konstruktion kontaminiert.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: research-wave1-2

#### `src/bybit_edge/research/c31_cfar/lead_edge.py:197`

**Kategorie:** gate-criterion-not-measured

Die H-03-Gate-Größe "Lead-Zeit > 50 ms" wird nie aus Daten gemessen:
`lead_ms = min(forward_horizon_ms, period_ms)` ist eine reine Funktion der
Konfigurationskonstante `forward_horizon_ms` (Default 100.0) und der
Peak-Periode — das Kriterienblock meldet `passed: lead_ms > 50` dennoch als
wäre es ein empirisches Ergebnis.

Bei Default `forward_horizon_ms=100` besteht das registrierte
Lead-Kriterium automatisch für **jeden** erkannten Top-Peak mit Periode über
50 ms, unabhängig davon, ob der Zyklus dem Preis überhaupt vorausläuft. Im
adjudizierten Gate-Log (GL-005) zeigt die Lead-Zeile exakt 100.0 ms mit "ja"
in allen vier Fenstern für BTC und ETH — die Konstante, keine Messung. H-03
war zwar auf p/edge DROP (das Endurteil bleibt korrekt), aber das Gate-Log
präsentiert ein konstruktionsbedingt fabriziertes Kriterium als getestet.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/research/c01_ofi_sign/driver.py:351`

**Kategorie:** non-reproducible-surrogate-seed

Der Per-Variante-Surrogate-Seed nutzt `abs(hash(symbol)) % 991`; Pythons
`str`-Hash ist pro Prozess gesalzen (`PYTHONHASHSEED`-Randomisierung, nirgends
im Repo fixiert), sodass die Permutations-Surrogat-p-Values von H-05, H-05b
und H-06 trotz des Kommentars "deterministic per (symbol, window, delta) seed
offset" **nicht** reproduzierbar sind.

Zwei Läufe desselben registrierten Runs erzeugen unterschiedliche
Surrogat-Permutationen und damit unterschiedliche p-Values pro Zelle. Bei
`n_surrogates=200` hat p eine Auflösung von 1/201, und die GL-010
H-05b-WEITER-Entscheidung liegt auf einer knapp bemessenen FDR-Familie
(`p_crit=0.0199`) — ein Rerun unter anderem Hash-Salt kann Zellen über die
BH-Schwelle verschieben. Der gleiche Musterfehler existiert auch in
`c07_pe/driver.py:377` (H-06); dass dies ein bekanntes Risiko im Repo ist,
zeigt `c09_bunch/driver.py:147`, das dasselbe Problem dokumentiert und einen
deterministischen Digest verwendet.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: research-wave3

#### `src/bybit_edge/research/c06_xmr/xsec.py:93`

**Kategorie:** look-ahead

Die "Non-Crash-Regime"-Konditionierung von Achse B zum Entscheidungszeitpunkt
t wird aus **zukünftigen** Daten berechnet: `panel_realized_vol` summiert
quadrierte Returns über Balken (t, t+3] — exakt die Balken, die den
Forward-Return-Target für h=1 und h=3 (und die Hälfte von h=6) bilden;
`non_crash_mask` leitet zusätzlich seine Dezil-Schwelle aus der
In-Sample-RV-Verteilung des gesamten Fensters ab (inklusive der Zukunft
jedes t).

Ein Event bei Balken t wird nur dann ins konditionierte Set aufgenommen,
wenn sich im Nachhinein zeigt, dass die nächsten 15 Minuten Low-Vol waren —
für h∈{1,3} ist der Ziel-Return dieselbe Menge Balken, die über die
Zulassung entscheidet. Crash-Continuation-Events (der große negative
`rev_ret`-Tail, wo Reversion scheitert) werden mit zum Zeitpunkt t nicht
verfügbarem Wissen herausgefiltert — das verzerrt `mu_rev_conditioned` nach
oben und begünstigt ein falsches WEITER-Urteil beim
Amplifikations-Kriterium.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/research/c06_xmr/stats.py:98`

**Kategorie:** wrong-results

`surrogate_p_mu_positive` implementiert die Nullhypothese als i.i.d.-Ziehung
mit Zurücklegen aus dem gepoolten Baseline-Set, nicht als das
vorregistrierte "Block-Shift/Permutation der Forward-Renditen gegen z". Bei
stark überlappenden Forward-Returns unterschätzt dies die
Null-Varianz des konditionierten Mittelwerts und liefert anti-konservative
p-Values, die in BH-FDR einfließen.

Im Rank-Modus (H-08) feuert Achse A fast bei jedem Balken (501–508
konditionierte Events pro 576-Balken-Fenster); für h=6 teilen sich
aufeinanderfolgende Events 5/6 ihres Forward-Return-Fensters. Die wahre
Null-Varianz des konditionierten Mittelwerts ist dadurch deutlich größer als
die i.i.d.-resampelte Surrogat-Verteilung — `surrogate_p` wird systematisch
zu klein, BH-FDR über F-XMR/F-XMR-RANK weist dadurch spuriose Nullhypothesen
zurück, was falsche "fdr_significant"-Zellen im Falsifikations-Gate erzeugt.

Bestätigt von 2/3 unabhängigen Prüfern (Mehrheitsvotum).

### Lane: research-wave4-second-opinion

#### `src/bybit_edge/research/c13_tailshape/returns_tail.py:153`

**Kategorie:** resource-exhaustion

`load_returns_window()` materialisiert **jeden** rohen `publicTrade`-Tick des
rückblickenden Fensters via `con.execute(sql).fetchall() + zip(*rows)` in
Python — genau die OOM/Timeout-Fehlerklasse, die bei H-09/H-11 bereits als
HIGH eingestuft und durch DuckDB-seitige Aggregation behoben wurde, hier aber
unbehoben überlebt hat, weil der H-13-Audit das Datenvolumen nie
berücksichtigte.

Bei einem 60-Tage-Fenster (BTCUSDT `publicTrade`, laut den eigenen
Machbarkeitszahlen des Programms 6×10⁷–6×10⁸ Zeilen) baut `fetchall()` eine
Python-Liste von Tupeln (~8 GB bis 70–90+ GB) auf der 82-GB-Zielmaschine.
Zusätzlich ruft der Unlock-Scan denselben Loader mehrfach mit 5-Tage-Fenstern
pro Kandidaten-Snapshot-Datum auf. Bei dokumentierten Datenvolumina führt
dies zu OOM-Crash oder Timeout — der unbeaufsichtigte Overnight-H-13-Lauf
schlägt hart fehl statt sauber zu SKIPpen, ohne jedes Ergebnis-JSON.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: scripts-dashboard

#### `src/bybit_edge/dashboard/app.py:139`

**Kategorie:** stale-data-masquerading-as-live

Der Dashboard-Header zeigt immer "Letztes Update: vor 0s" (wird bei jedem
Rerun neu auf `time.time()` gesetzt), während die
Snapshot-Präferenzlogik immer dann auf Snapshot-Parquet-Dateien
zurückgreift, wenn solche existieren — deren Alter nirgends geprüft wird. Ein
toter Collector/LiveRunner wird dadurch als live und gesund dargestellt.

Stürzt `LiveRunner` (der geschützte Datencollector) ab, nachdem einmal
`data/dashboard/*.parquet` geschrieben wurde, rendert das Dashboard bei jedem
10s-Auto-Refresh weiterhin "vor 0s" plus eingefrorene Zeilenzahlen und
Liquidationen aus tagealten Snapshot-Dateien — ohne jede Warnung. Der
Betreiber glaubt, die Aufzeichnung laufe, während sie lautlos nicht
läuft — genau das Szenario, das das Schutzgut-Monitoring eigentlich
erkennen soll.

Bestätigt von 3/3 unabhängigen Prüfern.

---

## Medium (14 Befunde)

### Lane: collector-recorder

#### `src/bybit_edge/persistence/db.py:818`

**Kategorie:** data-loss-non-atomic-archive

`archive_old_data` ist ein nicht-atomares COPY-dann-DELETE, dessen
Ausgabedateiname (`{table}_{date_tag}.parquet`, `date_tag` = Cutoff-Tag) nicht
eindeutig pro Lauf ist: ein zweiter Aufruf am selben UTC-Tag lässt DuckDBs
`COPY TO` die frühere Archivdatei überschreiben, deren Zeilen bereits aus der
Hot-DB gelöscht wurden — dauerhafter Verlust von Kaltspeicher-Zeilen. Ein
Absturz zwischen COPY und DELETE dupliziert umgekehrt Zeilen in die
Datei des Folgetages.

Läuft `archive_old_data` z.B. um 02:00 UTC und erneut um 20:00 UTC desselben
Tages, überschreibt der zweite `COPY TO`-Aufruf die Morgendatei mit nur den
neu gealterten Zeilen — die Zeilen von 02:00 existieren dann nirgends mehr.
Schweregrad auf Medium reduziert, da das Modul DEPRECATED markiert ist und
aktuell kein Aufrufer von `archive_old_data` im Repo existiert.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: state-layer

#### `src/bybit_edge/state/ticker_state.py:79`

**Kategorie:** wrong-results-latent

`TickerSnapshot.from_ws` nullt dokumentationsgemäß alle in einem
Tickers-Delta-Payload fehlenden Felder, und `TickerStateManager.update`
überschreibt den kompletten vorherigen Snapshot — wer das State-Modul exakt
nach eigener API-Dokumentation nutzt (`from_ws` pro Delta → Manager), erhält
bei jedem Delta lautlos genullte `mark_price`, `index_price`,
`funding_rate`, `open_interest`, `bid1`/`ask1`; `basis` maskiert die
Korruption zusätzlich, indem es bei `index_price==0` einfach `0.0` liefert.

Ein Delta wie `{symbol, lastPrice}` ergibt in `from_ws` `mark_price=0`,
`index_price=0`, `funding_rate=0`, `open_interest=0`; nach `update()` liefert
`get(symbol)` diese Nullwerte bis zum nächsten vollständigen Snapshot — ohne
Fehler. Der einzige aktuelle Live-Konsument übersteht dies nur, weil
`live_runner._on_ticker` extern ein Raw-Dict-Merge **vor** `from_ws`
durchführt; jeder neue Konsument, der sich an die Modul-Doku hält, erhält
systematisch genullte Funding-/Basis-/OI-Serien für die Module
M7/M8/M13/M22/M23/M24/M26.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: orchestration-execution

#### `src/bybit_edge/live_runner.py:412`

**Kategorie:** constitution-compliance

Primärer Befund: Echter Order-Platzierungscode existiert
(`LiveRunner._act_on_decision` → `BybitExecutor.place_market_order` →
`POST /v5/order/create`) und ist weiterhin vollständig in den
Standard-Einstiegspunkt `python -m bybit_edge` verdrahtet, mit einem
einzigen Env-Var reaktivierbar (`EXECUTION_ENABLED=true`) — aber **kein**
Echtgeld-Live-Pfad ist erreichbar: `EXECUTION_ENABLED` ist standardmäßig
`false`, `BYBIT_TESTNET` standardmäßig `true`, und
`BybitExecutor._safety_check()` wirft im Live-Modus einen `RuntimeError`,
sofern nicht `allow_live=True` übergeben wird — was kein Aufrufer im Repo
je tut.

Dies ist eine Härtungs-/Konstitutions-Lücke, kein aktiver Live-Order-Pfad:
Setzt ein Nutzer/Agent (z.B. über ein veraltetes Produkt-1.0-`.env`)
`EXECUTION_ENABLED=true` und startet `python -m bybit_edge`, werden echte
signierte Orders an Bybit-Demo-/Testnet-Endpunkte gesendet — obwohl die
Konstitution besagt, Live-Order-Code sei "nicht gebaut", und der
CLEANUP_PLAN vorsah, die Live-Pipeline "mechanisch unzugänglich" zu machen.
Echtgeld-Orders bleiben in allen Konfigurationen durch den
`allow_live`-Guard hart blockiert.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: layers-l1-l2

#### `src/bybit_edge/layers/l2_denoising/m4_wavelet.py:231`

**Kategorie:** wrong-results-inverted-metric

`M4WaveletDenoiser`s `snr_improvement_db` (und damit seine Konfidenz) ist
mathematisch invertiert: `noise = signal - denoised` (die entfernte
Komponente), `snr_after = signal_power/noise_power` — je **weniger** der
Denoiser entfernt, desto **höher** die gemeldete SNR-Verbesserung; ein
Fast-No-Op erzielt einen höheren Score als effektives Denoising.

Empirisch reproduziert: Bei sinusförmigem Signal + starkem Rauschen, bei dem
der Denoiser substanzielle Arbeit leistet, `snr_improvement_db=3.92`,
`confidence=0.196`; bei fast keinem Rauschen (Denoiser entfernt praktisch
nichts) `snr_improvement_db=7.93`, `confidence=0.397` — die
Konfidenz-Rangfolge ist exakt umgekehrt. `snr_before` ist zudem dimensional
gar keine SNR (Verhältnis begrenzt auf 1), sodass die berichtete dB-Zahl
bedeutungslos ist und systematisch Nichtstun belohnt.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/layers/l1_ingestion/m1_spikewavformer.py:273`

**Kategorie:** wrong-results-warmup

`M1SpikeWavformer._normalize_input` übergibt für die ersten 9 Samples nach
jedem `__init__`/`reset()` **rohe**, unnormalisierte Kanalwerte an das LIF
(fixer `v_threshold=1.0`) — realistische Rohgrößen (`liq_volume` in
USD/Kontrakten, `oi_delta` in Kontrakten, Größenordnungen über 1.0)
garantieren dadurch spurious Kanal-Spikes und ein falsches
System-Spike-Signal=1 während der Warmup-Ticks.

Empirisch reproduziert: Der allererste `compute()`-Call nach Init liefert
`spike=True`, `signal=1`, `confidence=0.67`, rein weil `len(rolling) < 10`
die Normalisierung überspringt und z.B. `25000 >> v_threshold=1.0` ist. Da
`reset()` `_rolling_values` leert, löst jeder Backtester-Segment-Reset
garantierte Falsch-Positiv-Spike-Events zu Beginn jedes Fensters aus, was
Spike-Zähl-Statistiken und darauf getriggerte Downstream-Logik verzerrt.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: layers-l3

#### `src/bybit_edge/layers/l3_regime/m13_cross_sectional_z.py:117`

**Kategorie:** correctness

M13 berechnet einen anderen z-Score als seine eigene dokumentierte
PRD-Formel: Der Ensemble-Mittelwert wird über die rollierenden zeitlichen
Mittel `E_t[X_j]` gebildet statt über die aktuellen Returns `R_{j,t}` —
erzwingt Zero-Sum-z-Scores und ein anderes Extremwert-Symbol-Set als die
registrierte Hypothese; zusätzlich werden Symbole mit ungleicher
Historienlänge (≥10 Samples vs. 60-Balken-Fenster) im selben Querschnitt
gemischt.

Bei einem Snapshot, in dem alle 1h-Mittel ähnlich sind, aber die aktuellen
Returns stark divergieren, meldet die PRD-Statistik Mean-Reversion-Extreme,
während die implementierte Statistik z~0 meldet (und umgekehrt) — der
Falsifikationstest bewertet eine andere Hypothese als die registrierte.
Zusätzlich erzeugt ein Symbol mit nur 10 Balken Historie sofort nach
Aufnahme spurious `|z|>2.5`-Einträge durch aufgeblähtes `sigma_cross`.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `src/bybit_edge/layers/l3_regime/m9_hmm.py:285`

**Kategorie:** correctness

Die einzelne Baum-Welch-EM-Verfeinerung akkumuliert Xi-Terme über Zeitschritte
hinweg **ohne** Pro-Zeitschritt-Normalisierung, während Alphas und Betas
jeweils mit unterschiedlichen Pro-t-Konstanten reskaliert werden — die
Transitionsmatrix-Aktualisierung ist dadurch eine verzerrte Gewichtung, die
Zeitschritte mit großer Emissionsdichte überbewertet.

Korrektes EM erfordert, dass jedes `xi_t(i,j)` vor der Akkumulation durch
seine Pro-t-Evidenzsumme geteilt wird; hier tragen Zeitschritte, deren
nächste Beobachtung in einen Niedrig-Varianz-(Hochdichte-)Emissionsbereich
fällt, Größenordnungen mehr Gewicht zu den Transitionszählungen bei. Auf
Trainingsdaten mit heterogenen Zustandsvarianzen ist die gefittete
Transitionsmatrix systematisch zu Übergängen in Niedrig-Varianz-Zustände
verzerrt, was die Regime-Persistenz-Schätzungen des Moduls degradiert.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: layers-l4-l5

#### `src/bybit_edge/layers/l4_pattern/m17_renyi_te.py:286`

**Kategorie:** misalignment-stale-data

M17 richtet Referenz- und Alt-Return-Serien bei unterschiedlicher Länge per
Kopf-Trunkierung aus (`ref_returns[:min_len]`, `alt_returns[:min_len]`),
was die **jüngsten** Samples der längeren Serie verwirft und für die
üblichen schwanzausgerichteten Rolling-Buffer nicht-zeitgleiche Fenster
vergleicht — dies korrumpiert die Transfer-Entropie-Lead-Lag-Schätzung, auf
der das Signal beruht.

Ein Symbol mit kürzerem Buffer (z.B. 50 Samples nach Reconnect vs. BTCs 500)
erhält eine TE-Berechnung zwischen BTCs **ältesten** 50 Returns und den
**jüngsten** 50 Returns des Alt-Symbols — komplett disjunkte Zeiträume —, was
spuriose `lead_lag_edges` über der Schwelle und `signal=1` erzeugt. Korrekt
wäre eine Tail-Ausrichtung (`[-min_len:]`). Wirkung heute begrenzt, da S5 im
Replay-Harness nicht triggerbar ist; jede reaktivierte Nutzung von M17 erbt
den Fehler jedoch.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: strategies-backtest

#### `src/bybit_edge/replay_backtester.py:376`

**Kategorie:** unbounded-memory-fetchall

`load_events()` führt für das (standardmäßig unbegrenzte) Fenster ein
`fetchall()` über jede Ticker-/Trade-/Liquidations-Zeile aus und
materialisiert jede als Python-Dict in einer einzigen In-Memory-Liste — der
Replay-Speicherbedarf wächst dadurch unbegrenzt, während der geschützte
Dauerbetrieb-Collector weiter aufzeichnet.

`replay_all.run_symbol()` ruft `bt.load_events()` ohne Start-/End-Grenzen
auf; das Modul nennt selbst bereits 4,5 Mio. Events für einen Snapshot,
jedes Event kostet ~0,5–1 KB, also ~3–4 GB. Nach einigen Monaten
Dauerbetrieb-Aufzeichnung erreicht ein einzelnes Symbol zig Millionen Zeilen
und zig GB RSS, was den unbeaufsichtigten Overnight-Runner (`run_overnight`)
mitten im Sweep per OOM killt — ein Silent-Failure-Risiko für die
morgendliche Gate-Auswertung.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: research-wave1-2

#### `src/bybit_edge/research/c42_rv/metrics.py:103`

**Kategorie:** fdr-family-construction

Der "F-VOL BH-FDR alpha=0.10 über 36 Features" (H-02) kann strukturell keine
einzelnen Features zurückweisen: Der Permutations-p-Value stammt aus
`n_repeats=20` Shuffles, der minimal erreichbare p-Wert ist damit 1/21 ≈
0.0476, während BH über m=36 bei alpha=0.10 `p_(k) ≤ (k/36)*0.10` verlangt —
eine Zurückweisung ist nur möglich, wenn ≥18 von 36 Features **gleichzeitig**
das exakte Minimum-p erreichen; zusätzlich aggregiert `pipeline.py:141`
Pro-Fold-p-Values über den **Mittelwert**, was keine valide
p-Wert-Kombination ist.

Für jedes realistische Ergebnis (eine Handvoll wirklich informativer
Features) gilt `p ≥ 0.0476 > 0.10*k/36` für alle erreichbaren k —
`n_significant` ist damit effektiv fest auf 0 verdrahtet, und die
berichtete FDR-Zeile testet nicht, was sie behauptet. Im entarteten
Gegenfall (≥18 Features mit allen 20 Drops > 0) werden umgekehrt alle
gleichzeitig zurückgewiesen — eine Alles-oder-Nichts-Familie.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: research-wave3

#### `src/bybit_edge/research/c06_xmr/panel.py:157`

**Kategorie:** data-integrity

`synchronise_panel` berechnet Balken-Returns **nach** dem Verwerfen
unvollständiger Zeilen und spleißt dabei Preise über die entstandenen
Lücken hinweg: ein einzelner "Ein-Balken"-Return kann eine beliebig lange
Echtzeit-Lücke überspannen, und alle nachgelagerten Balken-Index-Semantiken
(60-Min-Lookback-Mittel, 5/15/30-Min-Forward-Horizonte, 15-Min-Panel-RV)
überspannen die Lücke lautlos mit.

Hat einer von 5 Symbolen einen Datenausfall länger als `MAX_FFILL_BARS=1`
(eine einzelne >10-Min-Lücke in einem 2-Tage-Fenster), werden die
betroffenen Zeilen für **alle** Symbole verworfen, und die
Rückkehr-Berechnung behandelt den Preissprung über die gesamte (ggf.
stundenlange) Lücke als einen einzigen 5-Min-Balken-Return. Dieser
Lücken-Return wird typischerweise groß und dadurch systematisch zum
Rank-1-Extremevent (H-08 Achse A) — Datenlücken-Artefakte fließen direkt in
Event-Selektion und gemessene Reversion-Statistik ein, ohne Flag oder
Ausschluss.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: research-wave4-second-opinion

#### `src/bybit_edge/research/c13_tailshape/options_loader.py:206`

**Kategorie:** resource-exhaustion

`load_snapshot_entries()` führt ein `fetchall()` über einen **kompletten
Tag** an Deribit-`markprice.options`-Zeilen **inklusive** der vollen
`payload_json`-Strings aus und filtert erst danach in Python auf das
±30-Minuten-Fenster um 08:00 UTC — dieselbe Unbounded-Fetch-Fehlerklasse wie
beim Returns-Loader, hier im Options-Pfad. Jede Zeile trägt die komplette
aktive-Strikes-IV-Surface (hunderte Instrumente, ~100+ KB JSON pro Zeile).

Im Unlock-Scan ruft `scan_and_select` `load_smile` → `load_snapshot_entries`
einmal pro verfügbarem Snapshot-Datum pro Symbol auf. Bei Wochen an
Live-Aufzeichnung (dutzende Datumspartitionen, je potenziell 10⁴–10⁵
Batch-Surface-Ticks × ~100 KB) materialisiert jeder Aufruf transient
mehrere Gigabyte JSON, um nur ~60 Minuten um 08:00 UTC zu behalten — über
alle gescannten Daten summiert erschöpft dies RAM oder sprengt die
900s-/3600s-Timeouts des unbeaufsichtigten `run_h13`-Runners und macht aus
einer datengesteuerten SKIP-oder-Run-Entscheidung einen harten FAIL ohne
Payload.

Bestätigt von 3/3 unabhängigen Prüfern.

### Lane: scripts-dashboard

#### `src/bybit_edge/dashboard/app.py:639`

**Kategorie:** wrong-results

Der KPI "Trades im Journal heute" wird aus `load_journal(JOURNAL_PATH, n=50)`
berechnet, sodass `_trades_today_count` nur innerhalb der 50 jüngsten
Journal-Zeilen zählt und der Metrikwert lautlos bei 50 saturiert.

An einem Live-Tag mit 300 Journal-Aktionen (enter/exit/risk_block) enthält
die Journal-CSV 300 Zeilen mit heutigem Timestamp, aber `load_journal`
trunkiert nach absteigender Sortierung auf `head(50)` — der Header-KPI
meldet "Trades im Journal heute: 50", eine Untererfassung um Faktor 6, ohne
jeden Trunkierungs-Hinweis.

Bestätigt von 3/3 unabhängigen Prüfern.

#### `scripts/setup_local.sh:83`

**Kategorie:** dead-error-handling

Mit `set -euo pipefail` (Zeile 2) bricht die Pipeline
`python -m pytest tests/unit/ ... | tail -20` das gesamte Setup-Skript bei
jedem Testfehler ab (pipefail propagiert pytest's Nonzero-Status, `set -e`
beendet) — der eigentlich vorgesehene `RESULT=$?`-Warnzweig (Zeilen 84–91)
ist damit toter, unerreichbarer Code, und die Setup-Schritte 7–8
(.env-Template-Erstellung, Daten-/Log-Verzeichnisse) laufen nie.

Schlägt auf einer frischen Maschine ein einzelner Unit-Test fehl (z.B.
fehlende optionale Abhängigkeit), bricht Bash sofort nach der
pytest-Pipeline ab — der Nutzer sieht nie den skriptierten
"ACHTUNG: Einige Tests fehlgeschlagen"-Hinweis, kein `.env` wird generiert,
`data/parquet`- und `logs/`-Verzeichnisse werden nicht angelegt — das Setup
endet unerklärt auf halbem Weg.

Bestätigt von 3/3 unabhängigen Prüfern.

---

## Verworfene Kandidaten

Die "refuted"-Liste des Review-Laufs ist **leer** — alle 40 Kandidaten-Befunde
haben die adversariale Verifikation überlebt (mindestens 2 von 3 Skeptiker-
Agenten CONFIRMED). Es gibt daher keine verworfenen Befunde zu dokumentieren.
