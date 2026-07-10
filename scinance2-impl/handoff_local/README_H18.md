# H-18 · GL-006/H-04 Lead-Lag High-N-Surrogat-Aufloesungs-Audit (F-LEADLAG, KAPITALFREI, Welle 5)

> Registrierter Eintrag: `scinance2-impl/state/hypothesis_registry.md` →
> „### H-18 · GL-006/H-04 Lead-Lag High-N-Surrogat-Aufloesungs-Audit"
> (Welle 5). Basis-Gate: `scinance2-impl/state/gate_log.md` → „## GL-006 ·
> 2026-06-17 · H-04 · C-17/C-41 Cross-Sectional Lead-Lag".

## Sonderstatus — **AUFLOESUNGS-AUDIT, KEINE NEU-ADJUDIKATION**

**H-18 ist KEINE neue empirische Hypothese über die Welt.** Es ist eine
Re-Execution der byte-identischen, bereits vorregistrierten und bereits
adjudizierten F-LEADLAG-Pipeline aus **GL-006** (H-04, WEITER kapitalfrei,
Kapital-Status PARK) mit GENAU EINER vorab deklarierten Änderung:
`n_surrogates` 200 → 100.000 (500×), als GPU-Tensor-Batches erzeugt.

**Das GL-006-Verdikt bleibt append-only UNVERÄNDERT stehen.** Dieses Modul
und dieser Runner schreiben `gate_log.md` **NICHT**. Bei Abschluss entsteht
ein eigener, neuer GL-Eintrag (GL-014ff.), der aus dem Payload dieses Laufs
**manuell** vom gate-auditor erstellt wird — dieser Runner selbst adjudiziert
nichts.

Jeder abdriftende GL-006-Stage-1-FDR-Survivor **falsifiziert NICHT GL-006
selbst** — er markiert das stehende Messungen-WEITER als
„aufloesungsbedingt fragil" (Audit-Finding). Kein Goalpost-Move, keine
Rücknahme von GL-006.

## Warum wiederholen?

Bei N=200 ist die Permutations-p-Untergrenze `1/201 ≈ 0,005` — die 12
GL-006-Stage-1-FDR-Survivor (inkl. beider WCOH-Zellen) sind an dieser
Untergrenze gefloort, und zwei Lesart-Entscheidungszellen (ETH→BTC F0 Lag1
und Lag2) liegen innerhalb 1 MC-SE von `p_crit` — konstruktionsbedingt
unentscheidbar. Bei N=100.000 sinkt die Untergrenze auf `1/100.001 ≈ 1e-5`
(MC-SE ≤ 2,2e-4 bei p=0,005).

## Vorregistrierte Teil-Claims (T1, T2 — beide Zweige informativ)

- **T1:** Alle 12 GL-006-Stage-1-FDR-Survivor messen bei `p <= 1e-3`
  (≥5× unter der alten Untergrenze) neu und bleiben unter dem neu
  berechneten BH-Step-up signifikant.
- **T2:** Die zwei Lesart-Entscheidungszellen ETH→BTC F0 Lag1 und Lag2
  lösen sich auf eine Seite von `p_crit` mit >5 MC-SE Abstand auf.

Beide Claims sind im Payload als separate, klar benannte Felder
(`t1_partial_claim`, `t2_partial_claim`) ausgegeben.

## Compute-Gating-Pflicht

Ein voller 100k-Surrogat-Lauf ist **NUR auf einem echten CUDA-Device
verdikt-tragend** (`verdict_carrying: true` im Payload — verlangt
`n_surrogates >= 100000` UND `backend == "torch-cuda"`). Ohne torch/CUDA
degradiert `c18_leadlag_audit` **ehrlich** auf numpy — jeder solche Lauf
(inkl. jeder Sandbox-Ausführung) wird `verdict_carrying: false` markiert;
T1/T2 werden dann nur **informativ**, nicht als vorregistriertes Ergebnis
berechnet.

## Start

```powershell
powershell -ExecutionPolicy Bypass -File .\run_h18.ps1     # Windows (PS 5.1)
```
```bash
bash scinance2-impl/handoff_local/run_h18.sh                # Linux/macOS
```

Ablauf: **(1)** `H18_SELFTEST` (`--self-test`: Methodik-Aequivalenz-Test
gegen die ORIGINALE `c17_c41_lead_lag`-Pipeline bei kleinem N auf
synthetischem Input — MUSS `rc=0` liefern, sonst FAIL/Regression), **(2)**
`H18_GPU_CHECK` (`--check-gpu-only`; rc 0 = CUDA vorhanden, rc 3 = kein CUDA
→ sauberer SKIP für Schritt 3), **(3)** `H18_AUDIT` (voller Lauf, nur bei
rc 0 aus Schritt 2: 100.000 Surrogate, Seed 42, `--backend cuda`).
Exit: 0=OK (inkl. sauberem GPU-losem SKIP) · 1=FAIL · 2=SKIP (kein CUDA).
Ergebnisse: `results/h18_<ts>/h18/…` + `SUMMARY_<datum>.md`.
Env: `HANDOFF_DUCKDB`, `PYTHON`, `HANDOFF_DRY_RUN` (+`HANDOFF_DRY_RC`).

## Methodik (vorab fixiert, EINZIGE Änderung ggü. GL-006)

Byte-identisch zu GL-006/`c17_c41_lead_lag` importiert (Fenster-Split,
Grid-Alignment, Lag-Set {1,2,3,5,10}, TE-Quantisierung, Wavelet-CWT-Formeln,
BH-FDR alpha=0.10): NUR die Surrogat-Ensemble-Auswertung ist auf
GPU-Tensor-Batches umgestellt.

- **Verdikt-tragende Null (unverändert GL-006):** zirkulärer Block-Shift
  der Quellserie — die Zufalls-Offsets werden über
  `generate_shift_offsets()` mit **exakt derselben sequenziellen
  RNG-Konsumption** wie im Original erzeugt, sodass bei gleichem N die
  Surrogat-Ensembles bit-identisch zur seriellen Original-Pipeline sind
  (nur die Statistik-Auswertung darüber ist gebatcht/GPU-faehig).
- **Registry-benannte GPU-Primitive** (`surrogate_gpu.phase_shuffle_surrogates`
  via `torch.fft.rfft`/`irfft`, `surrogate_gpu.permutation_surrogates` via
  Argsort von Uniform-Random-Keys): als **diagnostische** Generatoren
  bereitgestellt, aber **NICHT** die GL-006-Null und **NIE**
  verdikt-tragend — ihr Einsatz für T1/T2 würde die Byte-identische-
  Pipeline-Klausel brechen.
- **TE-Achse (C-17):** `te_batched.transfer_entropy_batch` — batched 3D-
  Histogramme via `scatter_add` (torch) / `bincount` (numpy), identische
  Quantisierung (doppelter stabiler Argsort) und identischer Plug-in-
  Schätzer wie `c17_c41_lead_lag.transfer_entropy.transfer_entropy`.
- **WCOH-Achse (C-41):** `wcoh_batched.wavelet_coherence_lead_batch` —
  batched Morlet-CWT via FFT-Multiplikation, boxcar-Glättung via FFT-
  Convolution; identische Skalen (`n_scales=16`, `w0=6`, geomspace) und
  Formeln wie das Original (die "~50 Skalen" aus dem GPU-Scan-Dokument
  waren eine Schätzung — die Byte-identische-Pipeline-Klausel gewinnt,
  daher bleiben die ORIGINALEN 16 Skalen erhalten).
- **FDR-Familie:** identisch F-LEADLAG (22 Varianten je Fenster, BH-FDR
  alpha=0.10) — importiert aus `c17_c41_lead_lag.surrogate.benjamini_hochberg`,
  KEINE neue Familie.

## Datenbindung

Identisch GL-006 — archivierte Fenster F0/F1 (BTCUSDT/ETHUSDT, 1000ms-Grid,
`max_ticks_per_window=150000`). Beim Standard-Paar/-Grid/-Lags vergleicht
der Payload (`data_binding_vs_gl006`) die neu gemessenen `observed_stat`-
Werte (die NICHT von `n_surrogates` abhängen) gegen die archivierten
GL-006-Werte — eine Abweichung würde bedeuten, dass die `trades`-Tabelle
sich seit GL-006 verändert hat, und wird ehrlich gemeldet, nicht versteckt.

## Kapitalfreiheit

Identisch GL-006: reine Mess-Existenz-Frage, **keine** bps/Edge/PnL/
Friction-Metrik im gesamten Modul (von den Tests erzwungen). H-04b bleibt
die separate, bereits PARK-adjudizierte Tradability-Folge — H-18 ändert
daran nichts.

## Tests (Sandbox, kein torch/keine GPU nötig)

`PYTHONPATH=src python3 -m pytest tests/unit/test_c18_leadlag_audit.py -q`

Wichtigster Test: **Methodik-Äquivalenz gegen die ORIGINALE
`c17_c41_lead_lag`-Pipeline** bei N=200 auf identischem synthetischem
Input — TE-/WCOH-Punktschätzer stimmen auf Float64-Präzision überein, und
weil die Zufalls-Offsets bit-identisch zur Original-RNG-Konsumption gezogen
werden, sind die Surrogat-p-Werte **exakt identisch** (nicht nur
„statistisch ähnlich"). Weitere Abdeckung: Phase-Shuffle erhält das
Amplitudenspektrum, T1/T2-Payload-Felder an einem konstruierten Beispiel,
`--check-gpu-only` meldet ehrlich (rc 0/3) und markiert jeden N=200-Testlauf
explizit als „Äquivalenz-Test, kein Auflösungs-Audit" statt als
T1/T2-Ergebnis, Kapitalfreiheits-Token-Scan, Modul-Import OHNE torch.

Die eigentliche 100.000-Surrogat-Skalierung ist NUR auf der GPU der
Nutzer-Maschine sinnvoll und verdikt-tragend — hier in der Sandbox wird
ausschließlich die Methodik-Äquivalenz bei kleinem N bewiesen.
