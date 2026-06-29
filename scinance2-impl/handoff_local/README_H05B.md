# H-05b OOS-Konfirmation — Runner-Anleitung

**Was:** Konfirmatorischer Lauf der inversen OFI-Vorzeichen-Lesart (MM-Replenishment)
gegen das registrierte H-05b-Gate. **KAPITALFREI** — reiner Vorzeichen-/Korrelations-
Mess-Test, keine bps/Edge/PnL.

## Voraussetzungen

1. **Junction `data\harvest`** zeigt auf den Harvester-data-Ordner (read-only):
   ```powershell
   New-Item -ItemType Junction -Path "data\harvest" -Target "E:\Claude\Projects\Data Harvest\data-harvest\data"
   ```
2. Harvester-Backfill für **bybit publicTrade** deckt April + Mai 2026 ab (per
   `harvest_coverage.py` bestätigt: alle 5 Symbole DONE).

## Lauf (ein Befehl, ~10–30 min)

```powershell
powershell -ExecutionPolicy Bypass -File .\scinance2-impl\handoff_local\run_h05b_oos.ps1
```
(Linux/macOS: `bash scinance2-impl/handoff_local/run_h05b_oos.sh`)

## Vorregistrierte Parameter (DEC-15 — NICHT im Lauf ändern)

| | Wert |
|---|---|
| Datenbasis | read-only Harvester-Backfill, `data/harvest/raw/bybit/publicTrade/` |
| Fenster A | erste 300 000 Ticks/Symbol ab **2026-04-15 00:00 UTC** |
| Fenster B | erste 300 000 Ticks/Symbol ab **2026-05-15 00:00 UTC** |
| Symbole | BTC/ETH/SOL/BNB/XRP |
| δ-Lags | {1, 5, 15, 60, 300} s |
| FDR | F-OFI-INV, BH-FDR α = 0.10 |
| Surrogates | 200 · Seed 42 |

**Entdeckungszelle (ETHUSDT, Juni, δ1s) ist per Konstruktion ausgeschlossen** —
der Lauf nutzt ausschließlich April/Mai-Daten, die der H-05-Entdeckungslauf nie
gesehen hat (sauberer OOS-Holdout, DEC-15).

## Output

`results/h05b_oos_<timestamp>/`:
- `h05b/h05b_oos_results.json` — Roh-Daten (gate-neutral)
- `h05b/h05b_oos_results.md` — Inverse-Konsistenz-Tabelle je (Symbol, δ) + Detail
- `SUMMARY_<datum>.md` — Schritt-Status, Grundlage der gate-auditor-Auswertung

## Gate (gate-auditor urteilt gegen H-05b)

- **WEITER** (inverse Mess-Existenz): sign = − UND p ≤ 0.05 (BH-FDR F-OFI-INV) UND
  inverse-Konsistenz in **≥ 2 disjunkten Fenstern** UND (|corr| ≥ 0.05 ODER
  Hit-Rate ≤ 0.47).
- **DROP**: Vorzeichen ≥ 0 in ≥ 1 Fenster ODER Magnitude verfehlt ODER FDR-p > 0.05.
  **Hartes Ein-Fenster-Kriterium, kein GRAUBEREICH.**
- **Symmetrie-Falle:** weder positiv (H-05, schon DROP) noch negativ → beide
  Vorzeichen-Lesarten verworfen, **KEIN H-05c**.

## Hochladen

Ganzes `results/h05b_oos_<timestamp>/`-Verzeichnis → der gate-auditor fällt GL-010
gegen H-05b.
