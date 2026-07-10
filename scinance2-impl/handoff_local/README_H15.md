# H-15 · Trade-Tape-Event-Grammatik jenseits Markov (KAPITALFREI, GPU)

T3-LOCAL_LONG-Lauf des kapitalfreien Existence-of-Structure-Gates
(F-GRAMMAR) auf dem read-only Harvester-Baum. **Reine Mess-/Existenzfrage —
KEINE Kapital-Metriken.** Gate-Urteil fällt der gate-auditor gegen den
H-15-Registry-Eintrag (`scinance2-impl/state/hypothesis_registry.md`,
Abschnitt "H-15"); dieses Skript fällt KEIN Gesamturteil.

## Was gemessen wird

Enthält der tokenisierte Bybit-`publicTrade`-Strom (Side × Signed-Size-
Quantil-Bucket × Log-Inter-Arrival-Bucket, Vocab 128) Struktur JENSEITS
eines Variable-Order-Markov-Modells (k≤4) UND jenseits Intraday-
Saisonalität — gemessen als OOS-Token-Level-Cross-Entropy-Vorteil eines
kleinen Causal-Transformers (~2-4M Parameter, Kontext 1024 Token) gegenüber
der Markov-Baseline?

* **Tokenisierung:** Side (2) × Signed-Size-Quantil-Bucket (8, NUR auf dem
  jeweiligen TRAIN-Fold gefittet) × Log-Inter-Arrival-Bucket (8) = Vocab
  128. Optionale Tick-Direction-Erweiterung auf Vocab 256 ist per Default
  AUS (registrierte Basis ist 128; `--use-tick-direction` würde
  `gate_valid` explizit voiden).
* **Transformer:** Decoder-only, ~3.5M Parameter (d_model=256, 4 Layer,
  4 Heads, Kontext 1024), Next-Token-Cross-Entropy, je Symbol trainiert.
* **Baseline:** KT-geglättetes Variable-Order-Markov k=0..4 + interpolierte
  Backoff-Variante (k=4), GLEICHER Train-Fold wie der Transformer — bewusst
  der CPU-günstige Vergleichsarm (reine numpy-Zähltabellen).
* **Fenster:** Purged Walk-Forward, 4 Folds über ~100 Tage (2026-03-27..
  2026-07-04), 1-Tag-Embargo je Fold, 3 Seeds je Fold. EIN vorregistriertes
  Fenster (kein W1/W2-Split — die 4-Fold-Struktur selbst ist das
  Robustheits-Design).
* **Null:** ≥200 saisonalitätserhaltende Surrogate via Within-Hour-of-Day-
  Block-Shuffle (Blocklänge 256 Events) — permutiert NUR die Blockreihenfolge
  INNERHALB jeder Stunde-des-Tages-Gruppe, erhält die stündliche
  Marginalverteilung exakt, zerstört Sequenzstruktur jenseits 256 Events.
* **Gate:** WEITER, wenn OOS-Token-CE des Transformers ≥2% relativ
  niedriger als die beste Markov-k-(k≤4)-Baseline bei ≥4/5 Symbolen UND die
  CE-Lücke über dem 95. Perzentil der Surrogat-Lücken-Verteilung liegt,
  nach BH-FDR α=0.10 über F-GRAMMAR (5 Symbole). Hartes Kriterium — kein
  Graubereich, kein nachträgliches Vocab-/Kontext-/Architektur-Nachjustieren.

## Differenzierung zum gesperrten Informationstheorie-Cluster (Pflicht)

**Wörtlich aus der Registry (H-15, "Selbstkill-/Restrisiko"):**

> Differenzierung zu den gesperrten Informationstheorie-Clustern (PE/TE,
> H-06/H-04) ist konzeptionell sauber (Event-Stream statt Renditen, CE als
> Scoring-Rule statt Entropie-Schätzer, kein rho/Trading-Gate) — MUSS im
> Runner-Output/README wörtlich dokumentiert werden, um Verwechslung mit
> dem gesperrten Cluster auszuschließen.

Ausformuliert (identisch als `driver.DIFFERENTIATION_NOTE` im
JSON-Payload jedes Laufs und im gerenderten Markdown-Report enthalten):

1. **EVENT-STREAM statt Renditen** — tokenisiert wird der `publicTrade`-
   Fluss (Side/Size/Inter-Arrival), keine Preis- oder Rendite-Serie.
2. **CROSS-ENTROPY als SCORING-RULE** zweier expliziter Modelle
   (Causal-Transformer vs. Variable-Order-Markov) statt eines
   Entropie-SCHÄTZERS — keine Permutations-Entropie (H-06-Cluster), keine
   Transfer-Entropie (H-04-Cluster).
3. **KEIN ρ-/Trading-Gate** — reine kapitalfreie
   Existence-of-Structure-Messung. Eine Handelsfolge wäre eine NEUE
   Hypothese H-15b, NICHT durch diesen Lauf impliziert.

## Compute-Gating (verbindlich — bindend für JEDEN Lauf)

Ein verdikt-tragender H-15-Lauf **BRAUCHT ein echtes CUDA-Gerät**
(Registry: "Rechenaufwand: GPU, zwingend" — 5 Symbole × 4 Folds × 3 Seeds ×
mehrere Epochen über 1024-Token-Kontexte + ≥200 Surrogat-Evaluierungen).
Ohne CUDA gibt es **kein** verdikt-tragendes Ergebnis:

* `python scripts/c15_grammar.py --check-gpu-only` meldet torch-/CUDA-
  Verfügbarkeit (immer rc=0, KEIN Lauf) — das ist eine reine Statusabfrage.
* `--mode full` (Standard) **verweigert den Start** ohne CUDA
  (`ComputeUnavailableError`, rc=1) — kein stiller CPU-Ersatzlauf.
* `--mode mechanics` läuft überall (auch ohne torch), ist aber **NIEMALS
  verdikt-tragend**: der Payload trägt IMMER `gate_valid: false` und
  `ran_on_gpu: false`. In dieser Sandbox (kein torch, keine GPU) ist NUR
  `--mode mechanics` testbar — Pipeline-Korrektheit (Tokenisierung,
  Walk-Forward-Folds, Kausalität/Embargo, Markov-Baseline, FDR, Block-
  Shuffle-Null), NICHT die tatsächliche Transformer-Trainings-Power.
* Der T3-Runner (`run_h15.sh`/`run_h15.ps1`) prüft VOR dem Hauptlauf per
  `--check-gpu-only`: fehlt CUDA bei `MODE=full`, ist das Ergebnis ein
  sauberer **SKIP (exit 2)**, kein irreführender CPU-Fallback.
* Zusätzliche `gate_valid`-Gründe im Payload (`gate_valid_reasons`):
  Abweichung von den registrierten Defaults (4 Folds, 1-Tag-Embargo, 3
  Seeds, ≥200 Surrogate, Blocklänge 256, Vocab 128, volle Datenbindung
  ohne `--max-events-per-day`-Kappung) — jede Abweichung voidet
  `gate_valid`, unabhängig vom CUDA-Status.

## Aufruf (ein Befehl, keine Pflicht-Parameter, Stunden — über Nacht)

    # Linux / macOS
    bash scinance2-impl/handoff_local/run_h15.sh

    # Windows (PowerShell 5.1)
    powershell -ExecutionPolicy Bypass -File .\scinance2-impl\handoff_local\run_h15.ps1

Ergebnisse landen unter `scinance2-impl/handoff_local/results/h15_<timestamp>/`
(`h15/c15_grammar_results.json` + `.md`, `SUMMARY_<datum>.md`,
`gpu_status.json`, Logs). Exit-Codes: 0 = OK · 1 = FAIL · 2 = SKIP
(Harvester-Pfad fehlt ODER kein CUDA bei `MODE=full`).

Env-Overrides: `HARVEST_DIR` (Harvester-Root), `MODE=mechanics` (expliziter
CPU-Mechanik-Override, NIE verdikt-tragend), `HANDOFF_DRY_RUN=1`
(+`HANDOFF_DRY_RC`).

## Junction / Datenbasis

* Datenquelle: read-only Harvester-Baum unter
  `data/harvest/raw/bybit/publicTrade/symbol=<SYM>/date=<d>/` (Junction
  `data/harvest`). **Kein Schreibzugriff** auf den Harvester-Baum
  (Schutzgut).
* Fehlt die Junction, Env `HARVEST_DIR` auf das Harvester-Root setzen:
  `HARVEST_DIR=/pfad/zu/harvest bash run_h15.sh`.
* Panel: 5 Bybit-Perp-Symbole (`BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,XRPUSDT`),
  Basis-Bestand 2026-03-27..2026-07-04 (~100 Tage, identischer Cutoff wie
  die Welle-4-Raster).
* Die CLI (`scripts/c15_grammar.py`) bricht mit rc=1 ab, wenn ein Symbol
  strukturell unter dem Event-Floor (5.000 Events im gesamten Raster)
  bleibt — sonst würde ein leerer/kaputter Stream ein vollständig
  aussehendes, aber bedeutungsloses Ergebnis erzeugen.

## Vorab fixierte, aber unregistrierte Implementierungsentscheidungen

Die Registry legt Tokenisierung, Architektur-Größenordnung, Baseline,
Fenster, Null und Gate-Schwellen fest; folgende Details sind Registry-still
und wurden **vor jedem Lauf** hier fixiert (siehe `driver.py`-Docstring
"Documented pre-fixed implementation decisions", D1-D4):

* **D1 Fold-Aggregation:** Symbol-CE = Test-Token-gewichtetes Mittel über
  die 4 Folds (Transformer-CE je Fold = Mittel über die 3 Seeds zuerst);
  die Surrogat-Null wird mit demselben Funktional gepoolt.
* **D2 Surrogat-Scoring:** Surrogate werden mit den BEREITS trainierten
  Modellen NEU EVALUIERT (nie neu trainiert) — die registrierten "≥200
  Surrogat-Evaluierungen" sind Forward-Passes.
* **D3 Auswertungs-Support:** jedes Modell (alle Markov-Ordnungen UND der
  Transformer) bewertet exakt dieselben Token-Positionen (`t ≥ 4` des
  jeweiligen Test-Streams) — die CE-Lücke ist nie ein Artefakt
  unterschiedlicher Auswertungsbereiche.
* **D4 Vocab:** registrierte Basis 128; Tick-Direction-Erweiterung (256)
  ist ein Opt-in, das `gate_valid` voidet.

## Architektur (vorab fixiert, NICHT auf Testfenstern getuned)

d_model=256, n_heads=4, n_layers=4, dim_feedforward=4×d_model, dropout=0.1,
Kontext 1024, ≈3.5M trainierbare Parameter (innerhalb der registrierten
2-4M-Bandbreite). Training: AdamW lr=3e-4, Cosine-Schedule, Grad-Clip 1.0,
Batch 32 (nicht-überlappende Kontext+1-Chunks), 3 Epochen, seed-gesteuertes
Shuffling.

## Feasibility (GL-012-Check, Registry: BESTANDEN)

CE-Differenz ist eine unbeschränkte, kontinuierliche Statistik ohne
H-07-analogen strukturellen Deckel; 200 Surrogate geben eine 95.-Perzentil-
Auflösung von 1/201≈0,005, deutlich unter der 0,10-FDR-Schwelle.

## Torch-optional (Sandbox-Betrieb)

`transformer.py` folgt exakt dem `try: import torch ... _TORCH_AVAILABLE`-
Muster aus `src/bybit_edge/layers/l4_pattern/m18_patchtst.py`: das Modul
ist OHNE torch importierbar; `torch_cuda_status()` meldet ehrlich
`torch_available=False`, jeder Trainings-/Eval-Aufruf wirft
`ComputeUnavailableError` statt Fantasiezahlen zu produzieren. In dieser
Sandbox ist NUR die Pipeline-Mechanik testbar (`tests/unit/test_c15_grammar.py`):
Tokenisierung inkl. Leak-Test, Walk-Forward-Fold-Konstruktion inkl. Embargo,
Markov-Baseline-Korrektheit auf einem bekannten synthetischen Markov-Prozess,
saisonalitätserhaltende Block-Shuffle-Null, `--check-gpu-only` und
`capital_free`-Token-Scan.
