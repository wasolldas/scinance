# H-07 · C-06 Cross-Sectional Ergodic Mean-Reversion Mess-Gate (KAPITALFREI)

T2-LOCAL_SHORT-Lauf des kapitalfreien Cross-Sectional-MR-Mess-Gates auf dem
read-only Harvester-Backfill. **Reiner Mess-/Verstaerkungs-Test — KEINE
bps/Edge/PnL/Sharpe/Friction.** Gate-Urteil faellt der gate-auditor gegen den
H-07-Registry-Eintrag; dieses Skript faellt KEIN Gesamturteil.

## Aufruf (ein Befehl, keine Pflicht-Parameter, ca. 10-30 min)

    # Linux / macOS
    bash scinance2-impl/handoff_local/run_h07.sh

    # Windows (PowerShell 5.1)
    powershell -ExecutionPolicy Bypass -File .\scinance2-impl\handoff_local\run_h07.ps1

Ergebnisse landen unter `scinance2-impl/handoff_local/results/h07_<timestamp>/`
(`h07/c06_xmr_results.json` + `.md`, `SUMMARY_<datum>.md`, Logs).

## Junction / Datenbasis

- Datenquelle: read-only Harvester-Backfill unter
  `data/harvest/raw/bybit/publicTrade/symbol=<SYM>/date=<d>/` (Junction
  `data/harvest`). **Kein Schreibzugriff** auf den Harvester-Baum (Schutzgut).
- Fehlt die Junction, Env `HARVEST_DIR` auf das Harvester-Root setzen:
  `HARVEST_DIR=/pfad/zu/harvest bash run_h07.sh`.
- Trockenlauf ohne Daten: `HANDOFF_DRY_RUN=1 bash run_h07.sh` (rc via
  `HANDOFF_DRY_RC`).

## Vorregistrierte Parameter (DEC-15 / DEC-17 / H-07, NICHT aendern)

| Parameter | Wert |
|---|---|
| Panel | BTC/ETH/SOL/BNB/XRP (5 Perp) |
| Fenster A / B | ab 2026-04-15 / ab 2026-05-15 (je 2 Kalendertage, UTC) |
| Bar-Laenge | 5 min (Last-Price je Bar, kontemporaer synchronisiert, ffill <=1 Bar) |
| Lookback L | 12 Bars (60 min) |
| Z_THRESH | 2.5 (Achse A: `\|z\| >= 2.5`) |
| Crash-Dezil | 0.9 (Achse B: Panel-15min-RV NICHT im obersten Dezil) |
| Horizonte h | {1, 3, 6} Bars |
| N-Floor | 30 konditionierte Ereignisse / Fenster |
| Surrogates / Bootstrap | 200 / 1000 |
| FDR | F-XMR, BH-FDR alpha = 0.10 |

## Gate (gate-auditor gegen H-07 — hier nur zur Orientierung)

**WEITER** (ALLE gemeinsam, fuer >=1 Horizont in >=2 Fenstern):
1. konditioniert `mu_rev > 0` (echte Reversion, kein Momentum),
2. Surrogate-`p <= 0.05` nach BH-FDR alpha=0.10 ueber F-XMR,
3. `mu_rev > 0` + FDR-sig in **>= 2 disjunkten Fenstern**,
4. **Nicht-Trivialitaets-Anker (Pflicht):** die 95%-Block-Bootstrap-CI von
   `mu_rev,kond` liegt OBERHALB und ueberlappt NICHT die CI von
   `mu_rev,baseline` (konditioniert echt staerker als der unkonditionierte
   Panel-Baseline).

**DROP** (jede EINE Bedingung reisst, hartes Ein-Fenster-Kriterium, kein
GRAUBEREICH): Anker verfehlt (CIs ueberlappen = die E-04-/PRD-§6-verbotene
Trivial-MR-Lesart) ODER `mu_rev <= 0` ODER FDR-`p > 0.05` in >=1 Fenster ODER
Verstaerkung nur in 1 Fenster ODER **N-Floor verfehlt** (< 30 Ereignisse/Fenster
nach Konditionierung — KEIN Symbol-Nachladen, KEINE Z_THRESH-Absenkung).

> **Hinweis Power-Risiko (ehrlich benannt):** Mit population-Cross-Sectional-Std
> ueber N=5 Symbole ist `|z|` mathematisch durch `sqrt(N-1)=2.0` beschraenkt —
> das registrierte `Z_THRESH=2.5` kann auf 5 Symbolen NIE feuern, der N-Floor
> reisst dann (N=0). Das ist genau die research_notes-§7.5-Power-DROP-Moeglichkeit
> ("5 Symbole zu eng gekoppelt"), NICHT ein Bug. Der A-priori ist DROP.

## Morgen-Auswertung / Upload

- Roh-Ergebnis (`c06_xmr_results.json`) + `SUMMARY_<datum>.md` an den Orchestrator
  hochladen. Der gate-auditor urteilt gegen H-07 und protokolliert nach
  `state/gate_log.md` als **GL-012**.
- `capital_free: true` im JSON ist Pflicht-Marker; Payload enthaelt KEINE
  bps/Edge/PnL/Sharpe/Friction-Felder.
