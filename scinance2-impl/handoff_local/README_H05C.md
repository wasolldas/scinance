# H-05c OFI-Fade-Tradability — Runner-Anleitung

**Was:** Tradability-Gegenstück zu H-05b (analog H-04→H-04b). Konfrontiert die in
GL-010 gemessene inverse OFI-Kante (SOLUSDT δ1s/δ5s) mit der **11-bps-Friction-Wand
nach 300-ms-Latenz-Haircut**. `capital_free=FALSE`, aber **historischer Backtest mit
Kostenmodell — KEIN Live-Order-Code, KEIN Geld** (CLAUDE.md §4). Kapital-Status PARK.

## Voraussetzung

Junction `data\harvest` zeigt read-only auf den Harvester-data-Ordner; SOLUSDT-
Backfill deckt April + Mai 2026 ab (per `harvest_coverage.py` bestätigt).

## Lauf (ein Befehl, ~10–30 min)

```powershell
powershell -ExecutionPolicy Bypass -File .\scinance2-impl\handoff_local\run_h05c.ps1
```
(Linux/macOS: `bash scinance2-impl/handoff_local/run_h05c.sh`)

## Vorregistrierte Parameter (DEC-16 — NICHT im Lauf ändern)

| | Wert |
|---|---|
| Symbol | SOLUSDT (einziges GL-010-≥2-Fenster-konsistentes Symbol) |
| Fenster | A@2026-04-15 + B@2026-05-15, je 300k Ticks (DEC-15) |
| δ | {1, 5} s (die GL-010-Survivor) |
| Trading-Regel | Fade: Position **entgegen** OFI-Vorzeichen, glatt nach horizon=δ |
| Friction-Wand | 11 bps Taker + 4 bps Slippage = 15 bps all-in |
| Latenz-Haircut | 300 ms (Einfang `[t+latenz, t+δ]`) |
| FDR | F-OFI-INV-TRADE, BH α=0.10 |

## Vier Blöcke

- **H05C_PRIMARY** (300ms/11bps/Taker) — **urteilstragend**, `gate_valid_assumptions=true`
- **H05C_LAT100 / H05C_LAT500** — Latenz-Robustheit, NICHT urteilstragend
- **H05C_MAKER** — adverse-selection-vorbehaltlicher Sekundär-Fall, NICHT urteilstragend

Die drei Nicht-Primary-Blöcke setzen `gate_valid_assumptions=false` und dürfen ein
WEITER NICHT erzwingen (Anti-Gaming-Klausel).

## Gate (gate-auditor urteilt gegen H-05c)

- **WEITER:** Netto-Edge > 0 UND statistisch > 0 (Bootstrap p ≤ 0.05 nach BH-FDR über
  F-OFI-INV-TRADE) in ≥ 2 disjunkten Fenstern für ≥ 1 der Zellen SOL-δ1s/δ5s,
  **am PRIMARY-Punkt**.
- **DROP/PARK:** Netto ≤ 0 in ≥ 1 Fenster ODER FDR-p > 0.05. **Hartes Ein-Fenster-
  Kriterium, kein GRAUBEREICH.** A-priori erwartet **PARK** (schwaches Mess-Signal
  aus GL-010 vs. 15-bps-Wand).

## Hochladen

Ganzes `results/h05c_<timestamp>/`-Verzeichnis → gate-auditor fällt GL-011 gegen H-05c.
