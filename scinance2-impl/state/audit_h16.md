# Audit H-16 · Time-Arrow-CNN (V-02 Classifier-Two-Sample-Test) — 2026-07-10

> Unabhängiger, adversarialer Audit vor dem ersten GPU-Lauf auf der lokalen
> RTX-Maschine des Nutzers. Der Nutzer prüft/testet 2 Wochen lang nichts —
> dieser Bericht ist das einzige Qualitätsgate. Geprüfter Code-Stand:
> `src/bybit_edge/research/c16_arrow/{__init__,scalogram,iaaft,cnn,stats,driver}.py`,
> `scripts/c16_arrow.py`, `scinance2-impl/handoff_local/run_h16.{ps1,sh}` +
> `README_H16.md`, `tests/unit/test_c16_arrow.py`. Alle Dateien vollständig
> gelesen, gegen `state/hypothesis_registry.md` § H-16 (Welle 5) und
> `state/GPU_RESEARCH_SCAN_2026-07-09.md` § 3 (V-02) geprüft, `CLAUDE.md`
> als Rahmen berücksichtigt.

## Verdikt

**PASS — kein Blocker vor dem ersten GPU-Lauf.** Die Implementierung ist
sorgfältig, methodisch korrekt und deckt alle in der Registry geforderten
Pflicht-Kontrollen tatsächlich im Gate-Code ab (nicht nur als Payload-
Dekoration). Der methodisch kritischste Punkt — Reversal auf der Roh-Serie
VOR der CWT — ist im Code selbst (nicht nur im Test) korrekt implementiert
und an ZWEI unabhängigen Stellen (numpy-Referenzpfad `scalogram.py` UND
Torch-Trainingspfad `cnn.py`) konsistent umgesetzt. IAAFT ist eine korrekte,
literaturtreue Implementierung (Schreiber & Schmitz 1996). Compute-Gating
ist mehrschichtig und lässt keinen verdikt-tragenden CPU-Lauf zu.
`pytest` ist ECHT grün (38/38, selbst ausgeführt, siehe unten).

Gefundene Probleme sind ausschließlich **LOW/Nit** (siehe unten) — keine
HIGH/CRITICAL-Bugs, kein Show-Stopper für den GPU-Lauf.

## Spec-Treue-Tabelle

| Registry-Anforderung (H-16, wörtlich/paraphrasiert) | Code-Fundstelle | Status |
|---|---|---|
| Serie: 1s signed Trade-Imbalance (Buy−Sell Taker-Vol) | `driver.load_day_imbalance` (DuckDB-SQL, `side='buy'`→+vol, `'sell'`→−vol, Sekunden ohne Trade=0) | JA |
| Fenster 512s, Stride 64s, 64 Skalen 2s–256s, komplexer Morlet | `scalogram.py`: `WINDOW_S=512`, `STRIDE_S=64`, `N_SCALES=64`, `PERIOD_MIN_S/MAX_S=2/256`, `MORLET_OMEGA0=6.0`, T&C-1998-Formel | JA |
| Reversal auf Roh-Serie VOR CWT (nicht Bild-Flip) | `scalogram.scalogram_pair` (`cwt_logpower(window[::-1])`); `cnn._batch_images` (`torch.flip` auf Roh-Fenster, dann `cwt_logpower_batch_torch`) | JA (s. eigener Abschnitt unten) |
| CNN: ResNet-18 oder ConvNeXt | `cnn.ArrowResNet18` — Standard-ResNet-18 (BasicBlock [2,2,2,2], 64/128/256/512 Kanäle) | JA (auf ResNet-18 fixiert, PRD erlaubt beides) |
| Held-out-Day-Split, kein Tag-Leck | `driver.split_days_chronological` — letzte 20% valider Tage als Test, rein chronologisch, Fenster kreuzen nie Tagesgrenze (`extract_windows` pro Tag aufgerufen) | JA |
| Pipeline-Leak-Kontrolle (IAAFT, ≤0,52) Pflicht-Gate | `iaaft.py` (Schreiber&Schmitz), `driver.measure_symbol` (20 volle Retrainings), `stats.evaluate_gate` (`leak_ok`, `method_invalid`) | JA, im Gate-Code (nicht nur Report) |
| Volatility-Asymmetry-Ablation (\|Imbalance\|, unsigned) | `driver.windows_for_days(..., unsigned=True)`, `measure_symbol` (3 Ablations-Seeds), Report-only (nicht urteilstragend) — genau wie Registry verlangt | JA |
| Methodisch-invalide bei Leak>0,52 → KEIN Verdikt (nicht DROP) | `stats.evaluate_gate`: `status = STATUS_METHOD_INVALID`, distinct von `DROP`; getestet in `test_leak_control_failure_marks_method_invalid_not_drop` | JA |
| Gate: AUC≥0,60 UND Surrogat-p95<0,53, ≥4/5 Symbole nach BH-FDR α=0,10, UND Leak≤0,52 | `stats.AUC_MIN=0.60`, `SURROGATE_P95_MAX=0.53`, `N_SYMBOLS_MIN=4`, `FDR_ALPHA=0.10`, `LEAK_AUC_MAX=0.52` — exakt registrierte Werte | JA |
| FDR: eigene BH-Kopie, F-ARROW über 5 Symbole | `stats.benjamini_hochberg` (lokale Implementierung, keine Fremd-Imports), `FAMILY_SIZE=5`, Sentinel-Padding bei Ausfall (`sentinel_cell`, p=1.0) | JA |
| GPU zwingend, kein CPU-Verdikt | `cnn.gpu_status`, `driver.check_gpu`, `driver.run` (ComputeError ohne Torch/CUDA; `verdict_bearing` False ohne echtes CUDA, selbst mit `--allow-cpu`) | JA (s. eigener Abschnitt) |
| Differenzierungsabsatz zum gesperrten Cluster in README | `README_H16.md` §„DIFFERENZIERUNG" (wortgleich zu `driver.DIFFERENTIATION_NOTE`, auch im JSON/MD-Report) | JA |
| capital_free — keine Kosten-/Ertragsrechnung | `run()`: `"capital_free": True`; AST-Scan-Test verbietet `bps/pnl/sharpe/friction/edge_` im Modulverzeichnis; manueller Zusatz-Scan (s.u.) bestätigt auch CLI/Runner sauber | JA |
| T3-Runner: ein Befehl, kein Prompt, Timeout je Schritt, Exit-Code | `run_h16.sh`/`run_h16.ps1`: GPU-Check zuerst, Timeout 8h Default, SUMMARY_<datum>.md, exit 0/1/2 | JA |

## Gefundene Bugs

Keine HIGH/CRITICAL-Bugs gefunden. Zwei LOW/Nit-Punkte:

1. **LOW — `n_surrogates=0`-Randfall nicht explizit behandelt.** Wird
   `--n-surrogates 0` übergeben (nicht der Default, aber CLI-erlaubt), ist
   `surrogate_aucs=[]`, `leak_auc=float("nan")`. In `evaluate_gate` wird
   `leak_ok=False` (nicht endlich), aber `method_invalid` bleibt `False`
   (weil `method_invalid` nur bei einem ENDLICHEN Leak>0,52 greift, nicht
   bei NaN). Ergebnis: `leak_control_passed=False`, aber KEIN expliziter
   `METHOD_INVALID`-Status — der Lauf würde im Gate einfach als "Quorum
   nicht erreicht" statt als "methodisch nicht messbar" erscheinen. Betrifft
   NICHT den Default-Pfad (`N_SURROGATES_DEFAULT=20`, Runner übergibt immer
   20) — reine CLI-Robustheit gegen Fehlbedienung, kein Live-Risiko für den
   geplanten Lauf.
2. **LOW — capital_free-AST-Scan deckt nur `src/.../c16_arrow/*.py` ab,
   nicht `scripts/c16_arrow.py` oder die Runner-Skripte.** Manueller
   Zusatz-Scan (`grep -inE "bps|pnl|sharpe|friction|slippage|edge_|profit"`)
   über `scripts/c16_arrow.py`, `run_h16.sh`, `run_h16.ps1`, `README_H16.md`
   ergab **keinen Treffer** — die Reinheit ist also faktisch gegeben, nur
   die automatisierte Testabdeckung endet an der Modulgrenze. Test-Lücke,
   kein tatsächlicher Verstoß.
3. **Nit** — `test_differentiation_note_present_and_nonempty` prüft nur
   Substrings (`"Entropie"`, `"AUC"`, Länge>100), nicht den in der Registry
   geforderten Wortlaut exakt. Der tatsächliche Text in
   `driver.DIFFERENTIATION_NOTE`/README ist inhaltlich vollständig und
   korrekt (manuell mit Registry-Text Zeile 388 verglichen) — nur der Test
   selbst ist schwach.

Keine Funde zu: Reversal-Reihenfolge, IAAFT-Korrektheit, Compute-Gating,
capital_free-Kernpfad, T3-Runner-Bugs (PS-Handle-Cache-Workaround korrekt
übernommen, Skript-Pfad korrekt VOR den Flags — der bekannte
`run_h05c`-rc=2-Bug ist in `run_h16.sh`/`.ps1` explizit vermieden, per
Kommentar referenziert und im Code verifiziert), FDR-Familiengröße/Sentinel-
Padding, Methodisch-invalide-Zustandsbehandlung.

## Test-Abdeckung

`PYTHONPATH=src python3 -m pytest tests/unit/test_c16_arrow.py -q`
— **selbst ausgeführt, ECHTES Ergebnis: `38 passed in 29.39s`, keine
Skips, keine Warnings, keine xfails.** (Sandbox hat kein Torch/CUDA — die
entsprechenden `ComputeError`-Degradationspfade werden dadurch aktiv
getestet statt übersprungen, s. `test_train_classifier_raises_compute_error_without_torch`
etc.)

Abdeckung nach Bug-Klasse:
- CWT-Korrektheit: reiner Sinuston peakt an erwarteter Skala (±log(1.3)).
- Reversal-vor-CWT: (i) allgemeine Nicht-Kommutativität der komplexen CWT
  unter Reversal explizit gezeigt (`cwt(x[::-1]) != flip(cwt(x))`, aber
  `== conj(flip(cwt(x)))` — die dokumentierte exakte Beziehung); (ii)
  `scalogram_pair` ruft nachweislich `cwt_logpower` FRISCH auf der
  reversierten Rohserie auf, nicht auf einem geflippten fertigen Bild
  (Test mit asymmetrischer Serie, die einen heimlichen Shortcut aufdecken
  würde).
- IAAFT: Amplitudenspektrum-Erhaltung (AR(1)-Prozess, rel. Fehler <5%),
  Phasen-Randomisierung (mittlere Phasendifferenz >1.2 rad, nahe π/2≈1.571
  für vollrandomisierte Phase), `end="spectrum"`-Variante exakt (<1e-6),
  Entartungsfall (konstante Serie) ehrlicher No-op, Input-Validierung.
- Methodisch-invalide-Zustand: eigener Test beweist `status != "DROP"` UND
  `gate_quorum_met=False` bei Leak>0,52.
- capital_free: AST-Identifier-Scan über das Modulverzeichnis.
- Compute-Gating: `--check-gpu-only` ehrlich ohne Torch; volle CLI-/Driver-
  Läufe brechen mit `ComputeError`/rc=2 ohne Torch/CUDA ab, NIE ein
  verdikt-tragender Fake-Payload.
- Daten-Loading gegen synthetischen Harvester-Baum (DuckDB/Parquet), Day-
  Split-Determinismus, BH-FDR/Mann-Whitney-AUC/exakter gepaarter Sign-Test
  als Stats-Primitive, Sentinel-Zell-Familiengrößen-Disziplin.

Keine Lücke bei den in der Aufgabenstellung genannten Bug-Klassen
identifiziert (bis auf die zwei LOW-Nits oben).

## capital_free-Check

`run()` setzt `"capital_free": True` explizit im Payload. AST-Scan-Test
verbietet die Identifier `bps/pnl/sharpe/friction/edge_` in jeder Datei des
Modulverzeichnisses (Namen, Attribute, Funktions-/Klassennamen, Argumente,
Keywords — vollständiger AST-Walk, nicht nur Text-Grep). Zusätzlicher
manueller Grep über `scripts/c16_arrow.py`, `run_h16.sh`, `run_h16.ps1`,
`README_H16.md` (nicht vom automatisierten Test erfasst) ergab ebenfalls
keinen Treffer für `bps|pnl|sharpe|friction|slippage|edge_|profit`. Das
gesamte Modul enthält an keiner Stelle eine Kosten-/Ertragsrechnung —
**Kapitalfreiheit ist tatsächlich durchgehalten**, nicht nur behauptet.

## T3-Runner-Check (PowerShell + Bash)

- Beide Runner (`run_h16.ps1`, `run_h16.sh`) laufen ohne Pflicht-Parameter,
  mit sinnvollen Env-Overrides (`HARVEST_DIR`, `H16_END_DATE`,
  `H16_N_SEEDS`, `H16_N_SURROGATES`, `H16_ABLATION_SEEDS`,
  `H16_TIMEOUT_SEC`, `HANDOFF_DRY_RUN`).
- **Bekannter `run_h05c`-rc=2-Bug (Skript-Pfad nach den Flags statt davor)
  ist explizit vermieden** — in beiden Runnern steht der Skriptpfad als
  ERSTES Element im Argument-Array, VOR allen `--flags` (per Kommentar
  referenziert, im Code verifiziert).
- PowerShell-spezifische Fallstricke sauber behandelt: `$null = $p.Handle`
  vor `WaitForExit` (bekannter .NET/PS5.1-Bug, bei dem `WaitForExit` ohne
  vorherigen Handle-Zugriff hängen kann), `BelowNormal`-Priorität in
  try/catch (kein Abbruch bei fehlenden Rechten), ASCII-kompatible
  Body-Konstruktion via `StringBuilder` + `WriteAllText` (keine BOM-/
  Encoding-Fallen), Timeout in ms korrekt aus Sekunden multipliziert.
- Zwei-Stufen-Ablauf: `H16_GPU_CHECK` (rc 2 → SKIP, KEIN Start des vollen
  Laufs) vor `H16_ARROW` (voller Lauf, nur bei rc 0 des GPU-Checks
  gestartet) — verhindert einen Fake-Vollauf auf einer Maschine ohne CUDA
  bereits auf Runner-Ebene, zusätzlich zur internen Absicherung in
  `driver.run`/`scripts/c16_arrow.py`.
- Exit-Codes konsistent zwischen `.sh`/`.ps1`: 0=OK, 1=FAIL, 2=SKIP;
  `SUMMARY_<datum>.md` wird in beiden Fällen geschrieben (auch bei SKIP,
  mit klarer Fehlermeldung statt offenem Prompt) — erfüllt CLAUDE.md
  Testpyramide-Anforderung "bricht NIE mit offenem Prompt ab".
- Bash-Runner: GNU/BSD-`date`-Kompatibilität für den Default-Cutoff
  ("gestern UTC") korrekt mit Fallback behandelt.

Keine Bugs gefunden.

## Compute-Gating-Korrektheit (höchste Priorität)

Mehrschichtige Absicherung, jede Schicht unabhängig geprüft:

1. **Runner-Ebene:** `H16_GPU_CHECK`-Schritt läuft IMMER zuerst
   (`--check-gpu-only`, kein Datenzugriff, kein Training); nur bei rc=0
   wird der `H16_ARROW`-Vollauf überhaupt gestartet. rc=2 → Runner
   protokolliert SKIP und startet den Vollauf NICHT.
2. **CLI-Ebene (`scripts/c16_arrow.py`):** ruft `check_gpu()` selbst
   nochmal auf VOR jedem Vollauf-Aufruf (unabhängig vom Runner) — schützt
   auch bei direktem CLI-Aufruf ohne Runner, und gegen den Randfall, dass
   die GPU zwischen Runner-Check und Vollauf-Start verschwindet
   (Preemption). Ohne `--allow-cpu` → `RC_SKIP_NO_COMPUTE=2`, KEIN
   `run()`-Aufruf.
3. **Driver-Ebene (`driver.run`):** wirft `ComputeError`, wenn Torch fehlt
   ODER (kein CUDA UND `allow_cpu=False`) — selbst wenn CLI/Runner
   umgangen werden (z.B. direkter Python-Import).
4. **Payload-Ebene:** `verdict_bearing = compute["verdict_capable"] AND
   device.startswith("cuda")` — selbst mit `--allow-cpu` gesetzt und
   `device="cpu"` explizit gewählt bleibt `verdict_bearing=False`. Ich habe
   den Fall geprüft, dass ein Nutzer `--device cpu` bei VORHANDENER GPU
   angibt: `compute["verdict_capable"]` wäre `True` (CUDA vorhanden), aber
   `device.startswith("cuda")` ist `False` → `verdict_bearing=False` bleibt
   korrekt erzwungen. Auch `max_days` (Smoke-Cap) erzwingt
   `verdict_bearing=False` unabhängig vom Compute-Status.
5. **Gate-Ebene:** bei `verdict_bearing=False` überschreibt `driver.run`
   `gate["status"]` zu `"NOT_VERDICT_BEARING"` (eigener String, nicht
   verwechselbar mit `MEASURED_GATE_NEUTRAL` oder `METHOD_INVALID_NO_VERDICT`)
   — ein CPU-Smoke-Payload kann nie wie ein echtes Messergebnis aussehen.
6. **Torch/CUDA-Parität:** `verify_torch_parity()` wird bei JEDEM
   `run()`-Aufruf VOR dem ersten Training auf dem Zielgerät ausgeführt und
   wirft `RuntimeError` bei Abweichung >1e-6 zur numpy-Referenz — verhindert
   ein Training auf einer fehlerhaften GPU-Implementierung, bevor Rechenzeit
   verschwendet wird. Ich habe den Torch-Batch-Reflect-Pad-Code von Hand
   gegen `numpy.pad(mode="reflect")` durchgerechnet (Beispiel [1,2,3,4,5],
   pad=2 → links [3,2], rechts [4,3]) — die Torch-Implementierung
   (`X[:,1:pad+1].flip(-1)` / `X[:,-pad-1:-1].flip(-1)`) reproduziert das
   exakt; die Parity-Prüfung ist also nicht nur Kosmetik, sondern eine
   echte Absicherung eines tatsächlich korrekt implementierten, aber
   fehleranfälligen Indexierungsschritts.

**Antwort auf die Kernfrage: Nein — ein Lauf ohne echtes CUDA-Training kann
in diesem Code zu keinem Zeitpunkt verdikt-tragend werden.** Alle sechs
Schichten wurden unabhängig am Code nachvollzogen, nicht nur am
Testbericht.

## Reversal-vor-CWT-Verifikation (wichtigster methodischer Check)

**Selbst am Code verifiziert, nicht nur am Testbericht des Builders.**

Numpy-Referenzpfad (`scalogram.py`):
```python
def scalogram_pair(window, ...):
    fwd = cwt_logpower(window, ...)
    rev = cwt_logpower(window[::-1], ...)   # Reversal auf ROH-Fenster, dann CWT
    return fwd, rev
```
`cwt_logpower` normalisiert die (bereits ggf. reversierte) Rohserie
(`normalise_window`, Mittelwert/Std — beide invariant unter Zeitumkehr,
kann also kein Zeitpfeil-Artefakt erzeugen) und ruft danach erst
`cwt_complex` auf. Die Reihenfolge ist also: **reverse → normalise → CWT**,
niemals CWT → flip.

Torch-Trainingspfad (`cnn.py`, der Pfad, der tatsächlich für das Training
verwendet wird):
```python
def _batch_images(windows, labels, bank):
    x = windows.clone()
    rev = labels == 0
    if bool(rev.any()):
        x[rev] = torch.flip(x[rev], dims=[-1])   # Reversal auf ROH-Fenster
    return cwt_logpower_batch_torch(x, bank).unsqueeze(1)  # CWT danach
```
`torch.flip` wirkt auf die 1D-Roh-Zeitachse der unverarbeiteten Fenster,
BEVOR `cwt_logpower_batch_torch` (das intern ebenfalls erst normalisiert,
dann FFT/CWT rechnet) aufgerufen wird. **Beide Pfade — der numpy-Referenz-
und der tatsächliche GPU-Trainingspfad — reversieren nachweislich die
Rohserie vor der CWT, nie das fertige Bild.**

Mathematische Kontrolle (selbst nachvollzogen, nicht nur behauptet): für
die KOMPLEXEN CWT-Koeffizienten gilt `CWT(x[::-1]) ≠ flip(CWT(x))` im
Allgemeinen (nicht-kommutativ, wie in der Aufgabenstellung gefordert);
die exakte Beziehung ist `CWT(x[::-1]) = conj(flip(CWT(x)))` für reelle
Signale mit symmetrischem Reflect-Padding — das komplexe Vorzeichen der
Imaginärteile unterscheidet sich. Für das tatsächlich verwendete
Log-POWER-Bild (`|CWT|²`, Betragsquadrat) fallen wegen `|conj(z)|=|z|`
beide Operationen zufällig zusammen (`|CWT(x[::-1])| = flip(|CWT(x)|)`) —
das ist in `scalogram.py`s Docstring EXPLIZIT als "dokumentierte Ehrlichkeit"
festgehalten und mit einem eigenen Test abgesichert
(`test_reversal_precedes_cwt_general_noncommutation`), der genau davor
warnt, dass ein naiver "flip des fertigen Bildes"-Shortcut bei DIESER
Repräsentation zufällig richtige Ergebnisse liefern würde, aber bei einer
künftigen Erweiterung (z.B. Phasen-Kanal) sofort falsch würde. Der Code
implementiert nachweislich NICHT den Shortcut, sondern ruft an beiden
Stellen `cwt_logpower`/`cwt_logpower_batch_torch` frisch auf der
reversierten Rohserie auf — bestätigt durch
`test_scalogram_pair_reverses_raw_series_not_finished_image`, das mit
einer asymmetrischen Testserie einen versteckten Shortcut aufgedeckt hätte.

**Fazit: Die Reihenfolge ist in BEIDEN Ausführungspfaden korrekt
implementiert — Reversal auf der Rohserie, CWT danach, exakt wie von der
Registry verlangt.**

## IAAFT-Korrektheit

`iaaft.py` implementiert den Standardalgorithmus (Schreiber & Schmitz 1996,
PRL 77(4)) exakt:

1. Zielspektrum `A_k = |rfft(x)|`, sortierte Originalwerte `v = sort(x)`.
2. Start: Zufallspermutation von `x`.
3. Iteration bis Fixpunkt (Rang-Permutation unverändert) oder `max_iter=200`:
   - **Spektrum-Schritt:** Phasen der aktuellen Iterierten behalten, Ziel-
     Amplituden `A_k` aufprägen, `irfft`.
   - **Amplituden-Schritt:** Rang-Remapping auf die sortierten Original-
     werte `v` (macht die Randverteilung exakt).
4. Ende auf dem Amplituden-Schritt (Default `end="amplitude"`) → exakte
   Randverteilung, approximatives Spektrum; `end="spectrum"` macht
   stattdessen das Spektrum exakt.

Das ist algorithmisch korrekt und deckungsgleich mit der Literaturreferenz
— selbst nachvollzogen, keine vereinfachte Näherung (z.B. kein simples
"nur FFT-Phasen randomisieren ohne Rang-Remap", was die Randverteilung
verzerren würde und NICHT die IAAFT-Garantie hätte).

**Builder-Testbehauptung selbst nachvollzogen:**
- `test_iaaft_preserves_amplitude_spectrum_linear_process`: AR(1)-Prozess
  (`x[i] = 0.6*x[i-1] + eps[i]`, n=4000), Amplitudenspektrum-Fehler
  `< 5%` relative RMS-Norm — **plausibel und bestätigt** (lief in der
  Sandbox mit, Teil der 38 grünen Tests).
- `test_iaaft_randomises_phase_not_just_amplitude`: mittlere absolute
  gewickelte Phasendifferenz `> 1.2 rad` (Erwartungswert bei voller
  Randomisierung: `E[|Uniform(-π,π)|] = π/2 ≈ 1.5708`) — korrekt als
  Diskriminator gewählt: ein Bug, der die Phase NICHT randomisiert (z.B.
  versehentlich die Originalserie zurückgibt oder Phase statt Amplitude
  erhält), würde eine mittlere Differenz nahe 0 zeigen, nicht nahe π/2.
  **Bestätigt.**
- `test_iaaft_end_spectrum_variant_is_exact_in_spectrum`: `end="spectrum"`
  liefert Spektrum-Fehler `< 1e-6` — **bestätigt**, exakte Variante
  funktioniert wie dokumentiert.
- Degenerierter Fall (konstante Serie): ehrlicher No-op statt Division
  durch Null oder NaN-Propagation — **bestätigt**.

Zusätzlich mathematisch geprüft: die Verbindung zur Registry-Null wird in
`iaaft.py`s Docstring korrekt begründet — ein stationärer linearer
Gaußprozess unter einer statischen monotonen Transformation (genau das,
was IAAFT emuliert) ist zeitreversibel (Weiss 1975), sodass die
Bayes-Null AUC=0,5 für Surrogate gilt und eine AUC materiell über 0,5 auf
Surrogaten einen Pipeline-Leak anzeigt, nicht Marktstruktur — das ist die
korrekte methodische Begründung für die Leak-Kontrolle, keine
Fehlinterpretation.

**IAAFT-Implementierung ist korrekt.**

## Methodisch-invalide-Zustandsbehandlung

Eigener, getesteter Codepfad, klar getrennt von DROP:

- `stats.evaluate_gate` setzt `method_invalid=True` NUR wenn ein GEMESSENES
  Symbol einen ENDLICHEN Leak-AUC-Wert `> 0,52` hat (`c["method_invalid"] =
  measured AND finite(leak) AND leak > leak_auc_max`).
- Bei `method_invalid=True`: `status = STATUS_METHOD_INVALID =
  "METHOD_INVALID_NO_VERDICT"` (String-Konstante, nicht `"DROP"`),
  `status_note` erklärt explizit auf Deutsch: "Lauf METHODISCH INVALIDE,
  KEIN VERDIKT (weder WEITER noch DROP ableitbar)".
- `gate_quorum_met` ist bei `method_invalid=True` IMMER `False`
  (`not method_invalid AND leak_all_ok AND n_gate_met >= n_symbols_min`) —
  selbst wenn AUC/FDR/Surrogat-p95 für alle Symbole an sich das Gate
  erfüllen würden, kann ein methodisch invalider Lauf niemals als "Quorum
  erfüllt" durchrutschen.
- `symbol_gate_met` einer betroffenen Zelle ist ebenfalls `False`
  (`leak_ok` ist Teil der UND-Verknüpfung).
- Test `test_leak_control_failure_marks_method_invalid_not_drop` prüft
  ALLE diese Invarianten explizit inkl. `gate["status"] != "DROP"`.
- `render_markdown` gibt bei `method_invalid` einen eigenen, unübersehbaren
  Absatz aus ("METHODISCH INVALIDE — KEIN VERDIKT ... Dies ist ein eigener
  Zustand, KEIN DROP").
- `driver.run` überschreibt bei `verdict_bearing=False` zusätzlich
  `gate["status"]` zu `"NOT_VERDICT_BEARING"` — das darunterliegende
  `gate["method_invalid"]`-Flag bleibt dabei erhalten (nicht überschrieben),
  sodass auch ein Nicht-CUDA-Smoke-Lauf mit zufällig hohem Leak-AUC die
  Information nicht verliert, nur die Top-Level-Statusmeldung priorisiert
  korrekt "nicht verdikt-tragend" vor "methodisch invalide".

**Korrekt implementiert als eigener Zustand, nicht als DROP.**

## Sonstige geprüfte Punkte

- **Kausalität/Held-out-Day-Split:** chronologisch, deterministisch, keine
  Diskretion; Fenster kreuzen nie eine Tagesgrenze (pro Tag extrahiert) →
  kein Tag-Leck zwischen Train/Test möglich. Getestet
  (`test_split_days_chronological_is_deterministic_and_tail_biased`,
  `test_windows_never_cross_synthetic_day_boundary`).
- **FDR:** eigene `benjamini_hochberg`-Implementierung in `stats.py`
  (keine Fremd-Imports aus anderen research-Modulen — Repo-Konvention
  "eigene Kopie pro Familie"), `FAMILY_SIZE=5`, Sentinel-Padding bei
  Symbol-Ausfall verhindert anti-konservative Schrumpfung der Familie
  (c13-Konvention, im Code-Kommentar referenziert).
- **Differenzierungsabsatz:** wortgleich in `README_H16.md`,
  `driver.DIFFERENTIATION_NOTE`, jedem JSON/MD-Report vorhanden — inhaltlich
  mit Registry-Zeile 388 abgeglichen, korrekt.
- Gesamtzahl Trainings: 5 Symbole × (5 Haupt-Seeds + 20 Surrogate + 3
  Ablation) = 140, konsistent mit dem Registry-Schätzwert "~145" und den
  CLI-/Modul-Defaults (`N_SEEDS_DEFAULT=5`, `N_SURROGATES_DEFAULT=20`,
  `ABLATION_SEEDS_DEFAULT=3`, keine Drift zwischen Konstanten und CLI-
  Defaults).

## Test-Ausführung (Beleg)

```
$ PYTHONPATH=src python3 -m pytest tests/unit/test_c16_arrow.py -q
......................................                                   [100%]
38 passed in 29.39s
```
Selbst ausgeführt am 2026-07-10, echtes Ergebnis, keine Manipulation.
