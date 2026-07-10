# H-14 · Conditional Cross-Venue-Lead-Lag-Graph (F-PANELLAG, KAPITALFREI, **GPU ZWINGEND**)

> Registrierter Eintrag: `scinance2-impl/state/hypothesis_registry.md` →
> „### H-14 · Conditional Cross-Venue-Lead-Lag-Graph via
> Node-Ablation-Cross-Attention" (Welle 5). Code komplett gebaut und gegen
> einen synthetischen 12-Node-Harvester-Baum getestet
> (`tests/unit/test_c14_panellag.py`, 20/20 grün); **KEIN Lauf gegen echte
> Daten, KEIN echtes Transformer-Training erfolgt** — die Sandbox hat weder
> torch noch GPU, daher ist in dieser Umgebung nur **Pipeline-Korrektheit**
> getestet (Panel-Laden/-Sync, Kausalität/kein Lookahead, Edge-Statistik +
> BH-FDR-Familie, Checkpoint/Resume, Compute-Gating), NICHT die tatsächliche
> Trainings-Power. Der volle Lauf gehört auf die lokale RTX-Maschine.

## Kernidee

12-Node-Panel = BTC/ETH × {Bybit, Binance, Deribit-PERPETUAL} + SOL/BNB/XRP
× {Bybit, Binance}, `publicTrade` auf 1s-Grid resampled
(`panel.DEFAULT_NODES`). Pro Node ein PatchTST-Style-Encoder
(Wiederverwendung des Musters aus `bybit_edge.layers.l4_pattern.m18_patchtst`
— Patch-Tokenisierung + Transformer-Encoder + Mean-Pool, adaptiert in
`encoder.py`), gespeist in EINEN Cross-Node-Multi-Head-Attention-Layer
(`encoder.PanelLagModel`). Target = Vorzeichen der nächsten 10s-Rendite je
Node. Edge-Statistik `T(j->i)` = OOS-Delta-Log-Loss zwischen Vollmodell und
einer Retrain-Ablation, bei der Source-Node j durch ein zirkulär geshiftetes
Surrogat ersetzt und das GESAMTE Modell neu trainiert wird (**Retrain**, kein
Attention-Gewicht-Lesen und kein Frozen-Shuffle). Null: ~100 Retrainings mit
komplett surrogaten Cross-Node-Inputs (jeder Node unabhängig geshiftet) je
Fenster.

## Warum das so teuer ist

Pro Fenster: **1 Vollmodell + 12 Single-Source-Ablationen + ~100
All-Surrogat-Nullen = 113 Trainings**, × 2 Fenster = **~226 volle
Transformer-Trainings**, je 10–20 Min auf einer RTX 5060 Ti → **~2–3
GPU-Tage total**. Auf CPU ~50–100× langsamer (Monate) — die registrierte
Retrain-Null ist auf CPU schlicht nicht durchführbar, eine billigere
Frozen-Shuffle-Null wäre eine schwächere, angreifbare Statistik (Registry
H-14, wörtlich).

## Checkpoint/Resume (bindend — Registry-Selbstkill-Klausel)

Diese Laufzeit macht einen Datenverlust bei Absturz inakzeptabel. Deshalb:

- Jedes einzelne abgeschlossene Training (egal ob `full`, `ablate/NN` oder
  `null/NNN`) schreibt SOFORT einen eigenen JSON-Checkpoint (atomic
  tmp+rename, `ablation._write_checkpoint`) nach
  `<ckpt-dir>/<W1|W2>/<task_id>.json`.
- Der Checkpoint-Ordner ist **STABIL, NICHT zeitgestempelt**
  (`results/h14_checkpoints/`, Default in `run_h14.{sh,ps1}`) — er überlebt
  Neustarts des Runners.
- Beim (Neu-)Start lädt `ablation.run_window_plan` zuerst alle vorhandenen
  Checkpoints und überspringt die entsprechenden Trainings; nur fehlende
  Tasks werden trainiert.
- Ein Stromausfall/Timeout verliert **höchstens das gerade laufende
  einzelne Training** (10–20 Min), nie den Gesamtfortschritt.
- **Der Runner ist deshalb explizit für MEHRFACHE Aufrufe über mehrere
  Nächte ausgelegt** — einfach `run_h14.sh`/`run_h14.ps1` erneut starten,
  bis der Schritt `H14_PANELLAG` mit `rc=0` durchläuft (= alle ~226
  Trainings beider Fenster fertig, `c14_panellag_results.json` geschrieben).
  Ein TIMEOUT/FAIL bei unvollständigem Plan ist der NORMALE Zwischenzustand,
  kein Fehler.

Getestet in der Sandbox (`test_run_window_plan_executes_and_checkpoints`,
`test_driver_run_end_to_end_with_dummy_train_fn`): zweiter Aufruf mit
identischem Checkpoint-Verzeichnis löst NULL neue Trainings aus; Löschen
eines einzelnen Checkpoints erzwingt genau EIN Retraining.

## Compute-Gating (bindend, analog H-11/H-13-Daten-Gating für Rechenleistung)

Ein voller Lauf ist **NUR mit torch + echtem CUDA-Device verdikt-tragend**:

- `--check-gpu-only` meldet ehrlich `torch_available`/`cuda_available`
  (kein Datenzugriff, kein Training; rc 0 = GPU bereit, rc 2 = kein CUDA →
  SKIP).
- Ohne `--allow-cpu-fallback` bricht ein voller Lauf OHNE echtes CUDA-Device
  SOFORT ab (`"GPU erforderlich, torch.cuda.is_available()=False"`, rc 2) —
  **bevor** irgendein Training versucht wird.
- `--allow-cpu-fallback` ist eine explizite TEST-Notlösung: läuft echtes
  torch auf CPU (falls installiert) oder — falls torch fehlt (Sandbox) —
  eine rein deterministische Dummy-Loss-Funktion
  (`ablation.make_dummy_train_fn`, **KEIN Modell**, nur Pipeline-Test). In
  BEIDEN Fällen markiert der Payload `compute_gating.gate_valid=false` und
  `weiter_indication=null` (JSON `null`, NICHT verdikt-tragend) — niemals
  ein numpy-/CPU-Ersatz für die registrierte ~226-Trainings-Retrain-Null.

## Start

```powershell
powershell -ExecutionPolicy Bypass -File .\run_h14.ps1     # Windows (PS 5.1)
```
```bash
bash scinance2-impl/handoff_local/run_h14.sh                # Linux/macOS
```

Ablauf: (1) `H14_GPU_CHECK` (`scripts/c14_panellag.py --check-gpu-only`,
rc 2 = kein CUDA → SKIP), (2) nur bei rc 0: `H14_PANELLAG` (voller
Teil-/Gesamtlauf innerhalb des Zeitbudgets dieses Aufrufs, resume-fähig s.o.).
Exit: 0 = OK (komplett fertig) · 1 = FAIL/TIMEOUT (normal bei
unvollständigem Plan — einfach erneut starten) · 2 = SKIP (kein CUDA).
Ergebnisse: `results/h14_<ts>/h14/…` + `SUMMARY_<datum>.md`. Checkpoints
(stabil): `results/h14_checkpoints/`.

Env-Overrides: `HARVEST_DIR`, `H14_N_NULL` (Default 100), `H14_TIMEOUT_SEC`
(Default 36000 = 10h Budget **pro Aufruf**, nicht Gesamtlaufzeit),
`H14_CKPT_DIR` (Default `results/h14_checkpoints` — zwischen Aufrufen
desselben Laufs NICHT ändern, sonst kein Resume), `HANDOFF_DRY_RUN=1`
(+`HANDOFF_DRY_RC`).

## Methodik (vorregistriert, nicht verhandelbar)

- **Panel:** 12 Nodes, 1s-Last-Price, Forward-Fill ≤ 60s (builder-fixiert
  VOR jedem Lauf, `panel.FFILL_CAP_SECONDS` — Registry macht dazu keine
  Vorgabe), Log-Returns (`panel.log_returns`).
- **Fenster:** W1 = 2026-03-27..2026-05-15, W2 = 2026-05-16..2026-07-04
  (identisch H-09/H-12-Konvention).
- **Modell (vorab fixiert, `encoder.DEFAULT_MODEL_PARAMS`):** Lookback
  120s, Patch-Länge 16/Stride 8, d_model 64, 4 Heads, 2 Layer je
  Node-Encoder, 4 Cross-Attention-Heads. **NICHT auf den Testfenstern
  getuned** (Registry-Selbstkill-Klausel).
- **Target:** Vorzeichen der nächsten 10s-Rendite je Node
  (`panel.target_sign_labels`); exakt-null Forward-Return wird maskiert
  (keine erzwungene Klasse).
- **Kausalität:** ein Sample am Anker t nutzt NUR `returns[:, t-119..t]`
  als Input und `returns[:, t+1..t+10]` für das Target
  (`panel.valid_sample_indices`, per-Node-Kausalitätstest in der Sandbox
  verifiziert). Train/OOS-Split chronologisch mit Embargo = Lookback +
  Horizon (`panel.train_oos_split`) — keine Leckage zwischen den Segmenten.
- **Edge-Statistik:** `T(j->i) = L_ablate_j(i) - L_full(i)` (OOS-Log-Loss,
  natürlicher Logarithmus, maskierter Mittelwert). Ablation = Retrain mit
  Node j zirkulär geshiftet (`panel.circular_shift_rows`); Targets werden
  IMMER aus der (ggf. geshifteten) Serie selbst berechnet, sodass nur
  Cross-Node-Information zerstört wird, nicht die Eigen-Ausrichtung des
  geshifteten Nodes.
- **Null-Konstruktion (builder-fixiert, dokumentiert in `stats.py`):** die
  Registry fixiert ~100 All-Surrogat-Retrainings je Fenster, aber nicht die
  Paarungslogik für die Delta-Null. Diese Implementierung bildet die
  Null-Verteilung je Ziel-Node i als ALLE geordneten Paardifferenzen
  `L_null_k(i) - L_null_k'(i)` (k≠k') der ~100 Null-Retrain-Losses
  (`stats.paired_null_deltas`) — symmetrisch um 0, ohne willkürliche
  Zentrierungswahl, 9900 Null-Deltas je Ziel bei 100 Nullen (feine
  Perzentil-/p-Wert-Auflösung, add-one-p_min ≈ 1/9901).
- **Gate (wörtlich):** WEITER, wenn in BEIDEN Fenstern mindestens eine
  gerichtete Non-BTC-Source-Kante über dem 95. Perzentil ihrer Null liegt
  UND BH-FDR α=0,10 über **F-PANELLAG** (99 Non-BTC-Source-Kanten je
  Fenster — 9 Non-BTC-Source-Nodes × 11 Ziele; Registry-Schätzung "~110")
  übersteht. DROP (hartes Ein-Fenster-Kriterium): null überlebende
  Non-BTC-Source-Kanten in einem Fenster. Kein Graubereich, kein
  nachträgliches Kanten-/Schwellen-Nachjustieren.
- **Positivkontrolle:** BTC-Source → ETH-Target-Kanten (9 Kanten: 3
  BTC-Nodes × 3 ETH-Nodes) sind vom Pass-Kriterium AUSGESCHLOSSEN. Übersteigt
  in einem Fenster KEINE dieser Kanten das 95. Perzentil ihrer Null, ist der
  Lauf **methodisch invalide** (`validity_status="ungueltig"`, KEIN Verdikt,
  KEIN DROP — Registry wörtlich).

## FDR-Familie

**F-PANELLAG** (neu, eigene Kopie in `stats.py`) — 99 Non-BTC-Source-Kanten
je Fenster × 2 Fenster = 198 Tests, BH-FDR α=0,10, EINE Familie über beide
Fenster gemeinsam.

## Kapitalfreiheit

Reine Struktur-/Existenzfrage — im gesamten Modul existiert keine
Kosten-/Ertragsrechnung (von den Tests erzwungen: kein `bps`/`pnl`/`sharpe`/
`friction`/`edge_`-Token irgendwo im JSON-Payload, `capital_free: true`).
Eine Handelsfolge wäre eine NEUE **H-14b**, NICHT impliziert.

## Tests (Sandbox, nur Pipeline-Korrektheit — kein GPU, kein echtes Training)

```
PYTHONPATH=src python3 -m pytest tests/unit/test_c14_panellag.py -q
```

20/20 grün. Deckt ab: 12-Node-Panel-Laden/-Sync gegen einen synthetischen
1s-Grid-Harvester-Baum (Deribit-Hyphen-Notation, Forward-Fill-Cap),
Kausalität/kein Lookahead in Fenster- und Target-Konstruktion (isolierte
Vergangenheits-/Zukunfts-Mutationstests je Anker), Train/OOS-Embargo,
Edge-Statistik- und BH-FDR-Familien-Konstruktion (99×2-Kanten) über eine
deterministische Fake-Loss-Funktion, volle Orchestrierung inkl.
Checkpoint/Resume (zweiter Aufruf = 0 neue Trainings, gelöschter Checkpoint
= genau 1 Retraining), `--check-gpu-only`-Ehrlichkeit, voller CLI-Lauf mit
`--allow-cpu-fallback` gegen einen synthetischen Hive-Baum (rc=0,
`gate_valid=false`, `weiter_indication=null`), Compute-Gate-Abbruch ohne
`--allow-cpu-fallback` (rc=2, kein Ergebnis-JSON), Kapitalfreiheits-Wächter.
Der volle Transformer-Trainingslauf ist NICHT Teil der Sandbox-Tests (torch
fehlt) — die tatsächliche Trainings-Power ist ausschließlich auf der
lokalen RTX-Maschine verifizierbar.
