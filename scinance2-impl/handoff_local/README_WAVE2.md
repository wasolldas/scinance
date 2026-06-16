# Welle 2 - Handoff-Runner (T3, unbeaufsichtigt)

## WAS laeuft

`run_wave2.ps1` (Windows) / `run_wave2.sh` (Linux/WSL) faehrt sequentiell:

1. **H-04** - C-17/C-41 Lead-Lag-Mess-Gate auf dem Paar BTC/ETH (TE + Wavelet-
   Coherence, F-LEADLAG BH-FDR alpha=0.10, KAPITALFREI)
2. **H-05** - C-01 OFI-Vorzeichen-Test fuer BTC/ETH/SOL/BNB/XRP (F-OFI BH-FDR
   alpha=0.10, KAPITALFREI; INC-02-Anker)
3. **H-06** - C-07 Permutation Entropy fuer BTC/ETH/SOL/BNB/XRP (Bandt-Pompe
   m=4/tau=1 vorab fixiert, PRE-Gate rho >= 0.30, F-ENTROPY BH-FDR alpha=0.10,
   KAPITALFREI)
4. **WAVE2_FDR** - F-WAVE2 zweistufige BH-FDR-Aggregation: erst Stage 1 je
   Familie (innerhalb der Driver), dann Stage 2 BH-FDR alpha=0.10 ueber ALLE
   Stage-1-Survivor-p-Werte aus H-04+H-05+H-06 gemeinsam. Eine Variante gilt
   nur als bestanden, wenn sie BEIDE Stufen ueberlebt. Schreibt
   `WAVE2_SUMMARY.md`.

Reihenfolge ist fest. Jeder Block hat ein eigenes Timeout (90 min / 120 min /
120 min / 10 min) und wird in try/catch gekapselt - ein Fehler in einem Block
beendet den Lauf nicht, er wird geloggt und der Lauf laeuft weiter.

## WIE LANGE

Ca. 2-4 Stunden je nach Daten-Tiefe der lokalen DuckDB. Der maximale
Zeitbudget-Deckel liegt bei rund 5.5 h (Summe aller Timeouts), tatsaechlich
laeuft es typischerweise schneller, weil die Daten-Caps (max-ticks-per-window
= 150 000 fuer H-04/H-05, max-bars-per-window = 43 200 = 30 Tage fuer H-06)
die Arbeitslast deterministisch deckeln.

## Voraussetzungen

- Lokale DuckDB mit `trades`- und `kline_1min`-Tabelle. Default-Pfad ist
  `data/bybit_edge.duckdb` relativ zum Repo-Root. Override:
  `HANDOFF_DUCKDB=<pfad>`.
- Python-Umgebung mit `numpy`, `duckdb`, `scipy` (H-04 importiert scipy als
  Existenz-Check; H-05 und H-06 nutzen nur numpy). Standard-Repo-`pyproject`
  zieht alles mit.
- Windows: vor dem Start `powercfg /change standby-timeout-ac 0` damit der
  Rechner nicht einschlaeft.

## Aufruf

```powershell
# Windows
powershell -ExecutionPolicy Bypass -File .\run_wave2.ps1
```

```bash
# Linux / WSL
bash run_wave2.sh
```

## WO Ergebnisse landen

`scinance2-impl/handoff_local/results/wave2_<timestamp>/`:

- `WAVE2_SUMMARY.md` - die F-WAVE2-Aggregation (Stage 1 vs. Stage 2 je
  Hypothese, Survivor-Tabelle, je Fenster die einzelnen Gate-Kriterien,
  PRE-Gate-rho fuer H-06 separat, H-05 `inverse_significant`-Flags)
- `wave2_summary.json` - dieselbe Aggregation als JSON-Sidecar
- `h04/c17_c41_results.json` + `.md` - Driver-Output H-04
- `h05/c01_ofi_sign_results.json` + `.md` - Driver-Output H-05
- `h06/c07_pe_results.json` + `.md` - Driver-Output H-06
- `steps.tsv` - eine Zeile je Block (Name, Status, Rc, Dauer, Detail)
- `summary.txt` - einzeilige Block-Zusammenfassung + Exit-Code
- `<BLOCK>.log` / `<BLOCK>.err.log` - stdout/stderr je Schritt

Ergebnisse aus `handoff_local/results/wave2_<ts>/` in die Session hochladen ->
automatische Auswertung durch gate-auditor gegen H-04/H-05/H-06.

## Dry-Run

Mechanik-Test ohne echte Laeufe (keine Python-Subprozesse, nur Mechanik
verifizieren):

```bash
HANDOFF_DRY_RUN=1 bash run_wave2.sh
HANDOFF_DRY_RUN=1 HANDOFF_DRY_RC=1 bash run_wave2.sh   # Mechanik mit FAILs
```

```powershell
$env:HANDOFF_DRY_RUN=1; powershell -ExecutionPolicy Bypass -File .\run_wave2.ps1
```
