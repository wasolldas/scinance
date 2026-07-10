# H-17 · Venue-Fingerprint Mess-Gate (Contrastive-Embedding, F-VENUE, KAPITALFREI, GPU)

T3-Lauf des kapitalfreien Venue-Fingerprint-Gates (Welle 5 — GPU-
Forschungswelle). **Symbol-invariante Boersen-Identitaet** (Bybit vs.
Binance) in Shape-normalisiertem Order-Flow via InfoNCE-Contrastive-
Embedding + Frozen-Linear-Probe, Leave-One-Symbol-Out. Reine Struktur-/
Existenzfrage — **KEIN Handelssignal; eine Handelsfolge waere eine NEUE
H-17b, NICHT impliziert.** Gate-Urteil faellt der gate-auditor gegen den
H-17-Registry-Eintrag (`scinance2-impl/state/hypothesis_registry.md` →
„### H-17 · Venue-Fingerprint"); dieses Skript faellt KEIN Gesamturteil.

> **Status:** Code komplett gebaut (`src/bybit_edge/research/c17_venue/`,
> CLI `scripts/c17_venue.py`, Runner `run_h17.{sh,ps1}`), gegen
> synthetische Panels sandbox-getestet
> (`tests/unit/test_c17_venue.py`, gruen). **KEIN Lauf gegen echte Daten
> erfolgt und KANN in dieser Sandbox nicht erfolgen** — die Sandbox hat
> **kein torch, keine GPU**; nur PIPELINE-Korrektheit ist hier pruefbar
> (Feature-Extraktion, Pro-Tag-Quantil-Normalisierung, LOSO-Fold-
> Konstruktion, Permutations-Null-Statistik, Redundanz-Gate, FDR,
> `capital_free`), NICHT die tatsaechliche Contrastive-Trainings-Power.

## ZWINGENDE GPU-Vorbedingung (verbindlich, registry H-17)

Batch-Groesse **>= 2048** ist Teil der registrierten Methode — Small-Batch-
CPU-Training wuerde die Embedding-Qualitaet messbar verschlechtern und ein
Null-Ergebnis konfundieren (registry, woertlich). Deshalb:

1. Der Runner prueft **ZUERST** per `python scripts/c17_venue.py
   --check-gpu-only`, ob ein echtes CUDA-Device sichtbar ist (JSON-Report:
   `torch_available`, `cuda_available`, `device_name`, `verdict_capable`).
2. **Ohne echtes CUDA-Device wird der volle Lauf UEBERSPRUNGEN** (SKIP,
   exit 2) — kein stundenlanger, nicht-verdikt-tragender CPU/Numpy-
   Pipeline-Smoke.
3. Selbst ein erzwungener Lauf (`HANDOFF_H17_FORCE_NO_GPU=1`, NUR fuer
   Pipeline-Diagnose) waere wegen des eingebauten Compute-Gates in
   `driver.run()` NIE urteilstragend: das JSON-Feld
   `compute.verdict_bearing` steht dann `false`, `weiter_indication` wird
   erzwungen `false`, egal wie die Accuracy-Zahlen aussehen.

**Vor jeder Auswertung durch den gate-auditor MUSS
`c17_venue_results.json["compute"]["verdict_bearing"] == true` geprueft
werden** — sonst ist der Lauf eine reine Pipeline-Smoke ohne Gate-Anspruch.

## Aufruf (ein Befehl, keine Pflicht-Parameter)

```powershell
powershell -ExecutionPolicy Bypass -File .\scinance2-impl\handoff_local\run_h17.ps1   # Windows (PS 5.1)
```
```bash
bash scinance2-impl/handoff_local/run_h17.sh                                          # Linux/macOS
```

Ergebnisse landen unter `scinance2-impl/handoff_local/results/h17_<timestamp>/`
(`h17/c17_venue_results.json` + `.md`, `SUMMARY_<datum>.md`, Logs).
Exit-Code: 0 = OK · 1 = FAIL · 2 = SKIP (Harvester fehlt ODER keine GPU).

**Laufzeit (registry-Schaetzung): GPU ~1-2 Tage.** ~105 volle Trainings
(5 Leave-One-Symbol-Out-Folds x (1 echtes Training + 20 Permutations-Null-
Retrainings)) je 10-20 Min auf RTX 5060 Ti. Timeout-Budget im Runner:
172800 s (48h), Override `HANDOFF_H17_TIMEOUT_S`. Ein abgebrochener Lauf
persistiert **keinen** Zwischenstand — erneuter Aufruf startet den
GESAMTEN Lauf neu (kein Fold-/Epoch-Checkpointing in dieser Version).

## Non-Redundanz-Gate gegen c12_frag/H-12 (vorregistriert, bindend)

**|Spearman rho| < 0,6** zwischen der taeglichen Cross-Venue-Embedding-
Distance-Serie (sekundaerer H-17-Output, "nichtlinearer Fragmentierungs-
index") und der c12_frag-Tages-lambda2/IPR-Serie an ueberlappenden Tagen
— **|rho| >= 0,6 = REDUNDANT zu H-12 = DROP unabhaengig von der Accuracy.**

**Verdrahtung:** `redundancy.py` liest die c12_frag-JSON-Payload-Struktur
GENAU so, wie `c12_frag.driver.run()` sie schreibt (`c12_frag_results.json`,
`src/bybit_edge/research/c12_frag/driver.py`): `payload["windows"][*]
["days"][*]` mit `analyzed=true` traegt `date`, `lambda2`, `ipr_v2` — das
IST die c12-Tagesserie. Konservative Lesart: die Gate-Statistik ist
`max(|rho_lambda2|, |rho_ipr_v2|)` (beide werden auch einzeln berichtet).

**Damit das Gate auswertbar ist, braucht der Runner einen bestehenden
`c12_frag_results.json`** (aus einem H-12-Lauf, `run_h12.sh`/`.ps1`):

```bash
C12_RESULTS_JSON=/pfad/zu/c12_frag_results.json bash run_h17.sh
```

Ohne diesen Pfad bleibt `redundancy_gate.evaluable = false` — der Lauf
schlaegt NICHT fehl, aber WEITER ist dann nicht moeglich (der
gate-auditor kann das Gate nicht beurteilen). Empfehlung: `run_h12.sh`
VOR `run_h17.sh` laufen lassen und dessen Ergebnis-JSON referenzieren.

## Junction / Datenbasis

- Datenquelle: read-only Harvester-Backfill unter
  `data/harvest/raw/<exchange>/publicTrade/symbol=<SYM>/date=<d>/`
  (Junction `data/harvest`). **Kein Schreibzugriff** (Schutzgut). Der
  Runner prueft VOR dem Lauf, dass BEIDE Boersen-Pfade existieren
  (`raw/bybit/publicTrade`, `raw/binance/publicTrade`).
- Fehlt die Junction, Env `HARVEST_DIR` setzen:
  `HARVEST_DIR=/pfad/zu/harvest bash run_h17.sh`.
- Trockenlauf ohne Daten/GPU: `HANDOFF_DRY_RUN=1 bash run_h17.sh` (rc via
  `HANDOFF_DRY_RC`).

## Vorregistrierte Parameter (Registry H-17, NICHT aendern)

| Parameter | Wert |
|---|---|
| Panel | 10 Nodes = 5 Symbole (BTC/ETH/SOL/BNB/XRP) x {Bybit, Binance}, publicTrade only |
| Fenster | 5-Min-Event-Fenster je Node |
| Kanaele | Inter-Trade-Dauer, Log-Trade-Size, Aggressor-Sign, Tick-Direction (4) |
| Normalisierung | Pro-Tag-Quantil-Normalisierung je Kanal/Node (zerstoert Tick-Size/Fee-Clustering/Aktivitaetslevel-Tells) |
| Encoder | Temporal-CNN/Transformer, InfoNCE-Training (Positive = gleicher Node andere Zeit, Negative = voller Batch) |
| Batch | >= 2048 (Teil der Methode, NICHT verhandelbar) |
| Probe | Frozen-Linear-Probe fuer Venue-Identitaet |
| Folds | Leave-One-Symbol-Out, 5 Folds; Test = letzte 3 Wochen des ausgelassenen Symbols |
| Null | Within-Symbol-Within-Day-Label-Permutation, 20 VOLLE Retrainings je Fold (kein Frozen-Model-Shuffling) |
| FDR | **F-VENUE** — 5 Fold-p-Werte, BH-FDR alpha=0,10 |
| Redundanz-Gate | \|Spearman rho\| < 0,6 vs. c12_frag-Tages-lambda2/IPR-Serie |

*Seed 42, Steps 10000 sind Code-/Runner-Default (Determinismus/Praxis),
NICHT von der Registry vorregistriert — separat ausgewiesen.*

## Gate (gate-auditor gegen H-17 — hier nur zur Orientierung)

**WEITER**, wenn ALLES gilt:
1. Held-out-Balanced-Accuracy >= 0,60 in >= 4 von 5 Leave-One-Symbol-Out-
   Folds gegenueber der 20-Retrainings-Permutations-Null, nach BH-FDR
   alpha=0,10 ueber F-VENUE.
2. Non-Redundanz-Gate erfuellt: |Spearman rho| < 0,6 gegen c12_frag.
3. `compute.verdict_bearing == true` (echtes CUDA-Device, Batch >= 2048).

**DROP**, wenn EINES gilt (hartes Kriterium, kein Graubereich):
- Pooled-Balanced-Accuracy < 0,55, ODER
- < 4/5 Folds erfuellen die Schwelle nach FDR, ODER
- |rho| >= 0,6 gegen c12_frag (REDUNDANT zu H-12 — DROP UNABHAENGIG von
  der Accuracy).

Kein nachtraegliches Schwellen-/Kanal-/Architektur-Nachjustieren.

## Sandbox-Testabdeckung (was HIER geprueft ist, was NICHT)

`tests/unit/test_c17_venue.py` (PYTHONPATH=src python3 -m pytest
tests/unit/test_c17_venue.py -q):

- Pro-Tag-Quantil-Normalisierung zerstoert nachweislich einen injizierten
  trivialen Venue-Tell (Trade-Groessen-Skala + Fee-Clustering): ein
  einfacher Summary-Stat-Probe trennt Venues fast perfekt VOR, faellt auf
  nahezu Zufallsniveau NACH der Normalisierung.
- Leave-One-Symbol-Out-Fold-Konstruktion: kein Symbol-Leck, Test-Zeitraum
  exakt die letzten 3 Wochen des ausgelassenen Symbols.
- Permutations-Null: Within-Group-Label-Permutation erhaelt die Gruppen-
  Label-Zusammensetzung; `run_fold` fuehrt garantiert 1 echtes + n_perm
  VOLLE Retrainings mit je einer FRISCHEN Encoder-Instanz durch (kein
  Frozen-Model-Shuffling — per fit()-Call-Zaehler auf dem Sandbox-Dummy-
  Encoder verifiziert).
- Redundanz-Gate-Berechnung: synthetische Embedding-Distance-Serie mit
  bekannter Korrelation zu einer synthetischen c12_frag-artigen Serie
  ergibt den korrekten Spearman-rho und den korrekten DROP/WEITER-Pfad.
- FDR-Familie (eigene BH-Kopie) + `capital_free`/Verbotstoken-Scan.
- `--check-gpu-only` meldet ehrlich `torch_available=False`,
  `cuda_available=False` in dieser Sandbox (exit 3) und laeuft NICHT in
  den vollen Pipeline-Pfad.
- End-to-End-CLI-Smoke ueber einen synthetischen Harvester-Baum (5
  Symbole x 2 Boersen) — rc=0, valide JSON/MD, `compute.verdict_bearing
  == False` (keine GPU hier).

**NICHT** in der Sandbox pruefbar: reale Contrastive-Embedding-Qualitaet,
reale Held-out-Balanced-Accuracy, reale Trainingsdynamik bei Batch>=2048
— das ist explizit der Zweck des T3-GPU-Laufs auf der Nutzer-Maschine.

## Selbstkill-/Restrisiko (registry, woertlich zu wiederholen)

Redundanz-Risiko zu H-12/F-FRAG ist explizit als Gate-Bestandteil
abgefangen (nicht nur Kommentar) — s. Non-Redundanz-Gate oben. Zwei
geparkte Schwester-Kandidaten (XV-DUAL-RETRIEVAL, V-03) zielen auf
dasselbe Konstrukt; H-17 ist der EINZIGE Venue-Signature-Slot dieser
Welle, keine Nachregistrierung der Geschwister ohne neue Deconflict-
Begruendung. Pro-Tag-Quantil-Normalisierung MUSS nachweislich die
trivialen Tells toeten (Builder-Diagnostik-Pflicht — s. Sandbox-
Testabdeckung oben, `test_per_day_quantile_normalization_destroys_trivial_tell`).
