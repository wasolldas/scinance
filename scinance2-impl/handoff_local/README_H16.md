# H-16 · Time-Arrow-CNN (F-ARROW, KAPITALFREI, **GPU ZWINGEND**)

> Registrierter Eintrag: `scinance2-impl/state/hypothesis_registry.md` →
> „### H-16 · Time-Arrow-CNN" (Welle 5). Code komplett gebaut und gegen
> synthetische Harvester-Bäume getestet (`tests/unit/test_c16_arrow.py`);
> **KEIN Lauf gegen echte Daten, KEIN echtes CNN-Training erfolgt** — die
> Sandbox hat weder torch noch GPU, daher ist in dieser Umgebung nur
> **Pipeline-Korrektheit** getestet, NICHT die tatsächliche CNN-Trainings-
> Power. Der volle Lauf gehört auf die lokale RTX-Maschine.

## Kernidee

1 s-signed-Trade-Imbalance-Serie (Buy- minus Sell-Taker-Volumen, Bybit-Perp
`publicTrade`, 5 Symbole) → Morlet-CWT-Log-Power-Scalogram (512 s-Fenster,
64 s-Stride, 64 Skalen 2 s–256 s) → ResNet-18 klassifiziert FORWARD vs.
TIME-REVERSED (Classifier-Two-Sample-Test, Lopez-Paz & Oquab 2017). Für einen
zeitreversiblen Prozess ist die Bayes-optimale AUC **exakt** 0,5 — das ist
die Haupt-Null, ohne Resampling.

## DIFFERENZIERUNG (Registry-Pflicht, wörtlich)

H-16 ist **KEIN Duplikat** des gesperrten Informationstheorie-/Nichtlineare-
Dynamik-Clusters (PE/TE/RQA/MFDFA/TDA, H-04/H-06-Linie):

- **Kein Entropie-Schätzer** taucht irgendwo in diesem Paket auf.
- Gemessene Eigenschaft ist **Zeit-Irreversibilität** (richtungsabhängige
  Asymmetrie des Prozessgesetzes unter Zeitumkehr `t -> -t`), **nicht**
  Komplexität oder Vorhersagbarkeit.
- Die Null ist die **exakte** Bayes-optimale AUC = 0,5 des Classifier-Two-
  Sample-Tests — ein exakter, vorab spezifizierbarer Wert, **kein**
  geschätzter Schwellenwert aus einer surrogat-kalibrierten Entropie-
  Statistik.

Dieselbe Formulierung steht wortgleich in `driver.DIFFERENTIATION_NOTE` und
in jedem JSON-/Markdown-Report.

## Compute-Gating (bindend)

Ein voller Lauf ist **NUR mit torch + echtem CUDA-Device verdikt-tragend**
(`--check-gpu-only` meldet ehrlich den Compute-Status; rc 2 = kein CUDA →
SKIP, der volle Lauf startet dann gar nicht). `--allow-cpu` ist eine
explizite Notlösung für einen **NICHT-verdikt-tragenden** CPU-Smoke-Run
(`verdict_bearing=false` im Payload). Vor dem ersten echten Training
verifiziert der Driver auf dem GPU-Gerät selbst, dass der torch-Batch-CWT-
Pfad (`torch.fft`) die numpy-Referenz reproduziert
(`scalogram.verify_torch_parity`, `atol=1e-6`) — die Sandbox kann nur die
numpy-Referenz testen, daher MUSS der erste echte Lauf sich selbst
verifizieren, bevor trainiert wird.

## Start

```powershell
powershell -ExecutionPolicy Bypass -File .\run_h16.ps1     # Windows (PS 5.1)
```
```bash
bash scinance2-impl/handoff_local/run_h16.sh                # Linux/macOS
```

Ablauf: (1) `H16_GPU_CHECK` (`scripts/c16_arrow.py --check-gpu-only`, kein
Datenzugriff, kein Training; rc 2 = kein CUDA → SKIP), (2) nur bei rc 0:
`H16_ARROW` (voller Lauf: 5 Symbole × [5 Haupt-Seeds + 20 IAAFT-Surrogat-
Retrainings (Pflicht-Leak-Kontrolle) + 3 Ablations-Seeds auf `|Imbalance|`]
≈ 140 Trainings). Exit: 0=OK · 1=FAIL · 2=SKIP. Ergebnisse:
`results/h16_<ts>/h16/…` + `SUMMARY_<datum>.md`. Env: `HARVEST_DIR`,
`H16_END_DATE` (Cutoff, Default gestern UTC), `H16_N_SEEDS`,
`H16_N_SURROGATES`, `H16_ABLATION_SEEDS`, `H16_TIMEOUT_SEC` (Default 8 h),
`HANDOFF_DRY_RUN` (+`HANDOFF_DRY_RC`).

## Methodik (vorregistriert, nicht verhandelbar)

- **Serie:** 1 s signed Taker-Volumen-Imbalance je Symbol/Tag (Sekunden ohne
  Trade = 0 — natürliche Flow-Semantik, keine Interpolation).
- **Scalogram:** komplexer Morlet-CWT (ω₀=6, Torrence & Compo 1998), 64
  log-verteilte Fourier-Perioden 2 s–256 s, Log-Power, pro-Bild standardisiert.
  Reflect-Padding auf die doppelte Fensterlänge (**Randeffekt-/COI-Doku:**
  die Cone-of-Influence der größten Skala (256 s) überdeckt einen erheblichen
  Teil des 512 s-Fensters — das dämpft Kontrast an den Rändern, kann aber
  KEIN Zeitpfeil-Artefakt erzeugen, da Reflect-Padding mit Zeitumkehr
  kommutiert und für FORWARD/REVERSED identisch wirkt).
- **Reversal (bindend):** auf der **Roh-Serie VOR der CWT**
  (`scalogram.scalogram_pair`), niemals als Flip des fertigen Bildes.
- **CNN:** ResNet-18, Single-Channel-Input, 1 Logit, BCE + AdamW.
- **Split (vorab fixiert, dokumentiert):** chronologischer **Day-Level**-Split
  je Symbol — die letzten 20 % der validen Tage (mind. 1) sind Held-out-Test,
  alle früheren validen Tage Train (`driver.split_days_chronological`). Kein
  W1/W2; Fenster überschreiten nie eine Tagesgrenze, daher keine weitere
  Purging-Notwendigkeit.
- **Haupt-Null:** exakte Bayes-optimale AUC = 0,5 (kein Resampling); p-Wert
  je Symbol = exakter gepaarter Sign-Test des Median-Seed-AUC gegen diese
  Null.
- **Pflicht-Kontrolle (a) Pipeline-Leak:** dieselbe Pipeline auf 20 Tage-
  weisen **IAAFT**-Surrogaten (Schreiber & Schmitz 1996, Ende auf dem
  Amplituden-Schritt → exakte Marginalverteilung, approximatives Spektrum).
  `leak_auc` = Mittelwert der 20 Surrogat-AUCs, muss **≤ 0,52** bleiben;
  `surrogate_p95` = 95. Perzentil, muss **< 0,53** bleiben. **Verletzung ⇒
  `status = METHOD_INVALID_NO_VERDICT`** — ein EIGENER Zustand, explizit
  **KEIN DROP**: aus einem methodisch invaliden Lauf darf in keiner Richtung
  ein Verdikt abgeleitet werden.
- **Pflicht-Kontrolle (b) Volatility-Asymmetry-Ablation:** identische
  Pipeline auf `|Imbalance|` (unsigned), 3 Seeds, **nicht urteilstragend**,
  aber Pflicht-Report — trennt Leverage-Effekt (Vol-Level-Asymmetrie) von
  Flow-Richtungs-Asymmetrie.
- **Gate (wörtlich):** WEITER, wenn Held-out-AUC ≥ 0,60 MIT Surrogat-95.-
  Perzentil < 0,53, bei ≥ 4/5 Symbolen nach BH-FDR α = 0,10 über **F-ARROW**,
  UND die Leak-Kontrolle bleibt ≤ 0,52 (sonst methodisch invalide, s. o.).
  DROP: AUC < 0,60 bei < 4/5 Symbolen. Kein Graubereich, keine nachträgliche
  Skalen-/Fenster-Anpassung. Payload ist gate-neutral (`capital_free=true`,
  `gpu_required=true`, `verdict_bearing`); der gate-auditor urteilt.

## FDR-Familie

**F-ARROW** (neu, eigene Kopie in `stats.py`) — fix 5 Symbole. Ein Symbol,
dessen Messung fehlschlägt (Datenlücke, Zell-Fehler), besetzt seinen Slot
trotzdem als **Sentinel-Zelle mit p = 1,0** (`measured=false`) — die Familie
schrumpft nie unter m = 5 (c13-Konvention, anti-konservative Schrumpfung
ausgeschlossen).

## Kapitalfreiheit

Reine Struktur-/Existenzfrage ohne Round-Trip per Definition — im gesamten
Modul existiert keine Kosten-/Ertragsrechnung. Eine Handelsfolge wäre eine
NEUE **H-16b**, NICHT impliziert.

## Tests (Sandbox, nur Pipeline-Korrektheit — kein GPU, kein echtes Training)

`PYTHONPATH=src python3 -m pytest tests/unit/test_c16_arrow.py -q` — deckt
ab: CWT-Korrektheit an einem reinen Sinuston (Peak an der erwarteten Skala),
Forward/Reversed-Konstruktion beweisbar VOR der CWT (`cwt(x[::-1]) !=
flip(cwt(x))` für die komplexen Koeffizienten, aber der Code verwendet
nachweislich Ersteres), IAAFT erhält das Amplitudenspektrum (`|FFT|`)
innerhalb Toleranz, randomisiert aber die Autokorrelation/Phase, BH-FDR/
`capital_free`-Tokenscan, `--check-gpu-only` meldet ehrlich `torch_available=
False` in der Sandbox, und der Methodisch-invalide-Zustand
(Leak-Kontrolle > 0,52) wird im Payload als `METHOD_INVALID_NO_VERDICT`
markiert statt als DROP. Der volle CNN-Trainingslauf ist NICHT Teil der
Sandbox-Tests (torch fehlt) — erste Verifikation läuft on-device via
`verify_torch_parity` beim ersten echten `run()`-Aufruf.
