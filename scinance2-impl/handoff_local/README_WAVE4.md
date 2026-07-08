# Welle 4 - Konsolidierter Kohorten-Runner (T3, unbeaufsichtigt)

## WAS laeuft

`run_wave4.ps1` (Windows) / `run_wave4.sh` (Linux/WSL) faehrt sequentiell:

1. **H11_UNLOCK_CHECK** - H-11 ist DATA-GATED/GESPERRT (Registry). Der Check
   (`scripts/c11_anen.py --check-unlock-only`) prueft die Entsperr-Bedingung
   (lueckenlose done_days bybit publicTrade + rest.fundingRate, BTC+ETH,
   2024-03-27..2026-03-26, >=730 Tage). rc 2 = gesperrt -> sauberer SKIP.
2. **H13_UNLOCK_CHECK** - H-13 ist DATA-GATED/GESPERRT. Der Check
   (`scripts/c13_tailshape.py --check-unlock-only`) sucht deterministisch
   2 vol-regime-disjunkte IV-Snapshot-Tage D1<D2 im Deribit-Live-Fenster
   (markprice.options laeuft erst seit ~2026-06-16). rc 2 = gesperrt -> SKIP.
3. **H09** - Risk-Limit-Tier-Bunching (F-BUNCH, 5 Symbole x 2 Fenster,
   500 Residuen-Bootstrap, Placebos 0.5/0.75*K_s, KAPITALFREI).
   K_s-PLATZHALTER-WARNUNG: nur BTCUSDT registry-beziffert (kinks.py).
4. **H10** - Cross-Stream-Pointer-Days + Pre-Event-Drift (F-POINTER,
   30 Detektions-Serien, dvol-Hold-out BTC+ETH, 1000 Surrogate/
   Permutationen, KAPITALFREI).
5. **H12** - Cross-Exchange-Fragmentierungsmatrix (F-FRAG, 6 Serien =
   2 Symbole x 3 Boersen, 1000 MC-Reps PRO gueltigem Tag, KAPITALFREI).
   Rechenintensivster Block (siehe README_H12.md).
6. **H11 / H13** - volle Laeufe NUR bei bestandenem Entsperr-Check
   (rc 0). Sind sie gesperrt (der HEUTE erwartete, korrekte Ausgang -
   H-11 braucht ~730 Tage Deep-Backfill, H-13 zwei regime-disjunkte
   Snapshot-Tage im erst ~3 Wochen alten IV-Stream), wird ein sauberer
   SKIP mit Diagnose protokolliert: kein Datenzugriff, kein Verdikt.
7. **WAVE4_FDR** - F-XDOM1 zweistufige BH-FDR-Aggregation ueber die
   Kohorte H-09/H-10/H-12: Stage 1 = BH-FDR alpha=0.10 je Familie
   (Driver-intern: F-BUNCH, F-POINTER, F-FRAG), Stage 2 = EINE weitere
   BH-FDR alpha=0.10 ueber ALLE Stage-1-Survivor-p-Werte gemeinsam.
   Eine Hypothese besteht nur, wenn sie BEIDE Stufen ueberlebt
   (Registry-Eintrag "F-XDOM1", DEC-22 - VOR diesem Lauf registriert,
   Kohorten-Regel der Welle-4-Sequenzierung). Schreibt
   `WAVE4_SUMMARY.md` + `wave4_summary.json` - gate-neutral, KEIN
   Gesamturteil (gate-auditor urteilt).

Die drei Kohorten-Bloecke rufen die Modul-CLIs DIREKT auf
(`scripts/c09_bunch.py` / `c10_pointer.py` / `c12_frag.py`) mit den in den
auditierten Einzel-Runnern (`run_h09`/`run_h10`/`run_h12`) registrierten
Default-Parametern - die Einzel-Runner werden NICHT verschachtelt
aufgerufen (kein doppeltes Timeout-/Summary-Gerippe). Jeder Block ist
einzeln gekapselt (try/catch + Timeout + weitermachen) - ein Fehler in
einem Block beendet den Lauf nicht.

## WIE LANGE

Typisch ~1-2 Stunden (H-12 dominiert mit ~20-40 min laut README_H12.md;
H-09 haengt an der DuckDB-seitigen Order-Aggregation ueber ~100 Tage
publicTrade). Der maximale Zeitbudget-Deckel liegt bei ~6.5 h (Summe aller
Timeouts: 600+900+7200+3600+7200+3600+3600+600 s) - die H-11/H-13-Vollauf-
Budgets werden bei gesperrten Gates gar nicht angefasst.

## Voraussetzungen

- Read-only Harvester-Junction `data/harvest` relativ zum Repo-Root
  (Override: `HARVEST_DIR=<pfad>`). Benoetigte Baeume je Block:
  - H-09: `raw/bybit/publicTrade`
  - H-10: `raw/bybit/publicTrade`, `raw/deribit/dvol`,
    `raw/binance/rest.fundingRate`, `raw/binance/rest.openInterest`
  - H-12: `raw/{bybit,binance,deribit}/publicTrade`
  - H-11: `raw/bybit/publicTrade` (+ Manifest `harvest_manifest.sqlite`)
  - H-13: `raw/bybit/publicTrade`, `raw/deribit/markprice.options`
  Fehlt ein Pfad, wird der betroffene Block sauber uebersprungen (SKIP).
- Python-Umgebung mit `numpy`, `duckdb`, `scipy` (Standard-`pyproject`).
- Windows: vor dem Start `powercfg /change standby-timeout-ac 0`.

## Aufruf

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .\run_wave4.ps1
```

```bash
# Linux / WSL
bash run_wave4.sh
```

## Exit-Codes

- **0** = alle Bloecke OK
- **1** = mindestens ein FAIL (Fehler/Timeout in einem Block)
- **2** = kein FAIL, aber mindestens ein SKIP - das ist beim heutigen
  Datenstand der ERWARTETE Exit (H-11 + H-13 gesperrt). Kein Handlungsbedarf.

## WO Ergebnisse landen

`scinance2-impl/handoff_local/results/wave4_<timestamp>/`:

- `WAVE4_SUMMARY.md` - die F-XDOM1-Aggregation (Stage-1/Stage-2-Bilanz je
  Hypothese, Survivor-Tabelle mit Stage-2-Ergebnis, Gate-Kriterien je
  Zelle, Nicht-p-Wert-Gate-Bestandteile separat) - entsteht IMMER, auch
  bei SKIPs und im Dry-Run
- `wave4_summary.json` - dieselbe Aggregation als JSON-Sidecar
- `SUMMARY_<datum>.md` - Block-Status-Tabelle (T3-Konvention)
- `h09/c09_bunch_results.json` + `.md` - Driver-Output H-09
- `h10/c10_pointer_results.json` + `.md` - Driver-Output H-10
- `h12/c12_frag_results.json` + `.md` - Driver-Output H-12
- `h11/`, `h13/` - nur bei Entsperrung (H-13-Unlock-Check schreibt
  zusaetzlich `h13/c13_unlock_check.json` mit der D1/D2-Diagnose)
- `steps.tsv` - eine Zeile je Block (Name, Status, Rc, Dauer, Detail)
- `summary.txt` - einzeilige Block-Zusammenfassung + Exit-Code
- `<BLOCK>.log` / `<BLOCK>.err.log` - stdout/stderr je Schritt

Ergebnisse aus `handoff_local/results/wave4_<ts>/` in die Session
hochladen -> Auswertung durch den gate-auditor gegen H-09/H-10/H-12
unter der Beide-Stufen-Regel (F-XDOM1) -> GL-014ff.

## Dry-Run

Mechanik-Test ohne echte Modul-Laeufe (nur die F-XDOM1-Aggregation laeuft
echt - reine lokale JSON-Aggregation ohne Datenzugriff, damit
`WAVE4_SUMMARY.md` immer entsteht):

```bash
HANDOFF_DRY_RUN=1 bash run_wave4.sh
HANDOFF_DRY_RUN=1 HANDOFF_DRY_RC=1 bash run_wave4.sh   # Mechanik mit FAILs
HANDOFF_DRY_RUN=1 HANDOFF_DRY_RC=2 bash run_wave4.sh   # Mechanik mit gesperrten Gates
```

```powershell
$env:HANDOFF_DRY_RUN=1; powershell -ExecutionPolicy Bypass -File .\run_wave4.ps1
```
