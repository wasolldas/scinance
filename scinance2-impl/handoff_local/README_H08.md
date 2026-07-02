# H-08 · C-06 Cross-Sectional MR mit RANG-Über-Dehnung (KAPITALFREI)

T2-LOCAL_SHORT-Lauf des kapitalfreien Cross-Sectional-MR-Mess-Gates im
**Rang-Modus** (DEC-18) auf dem read-only Harvester-Backfill. **Reiner
Mess-/Verstärkungs-Test — KEINE bps/Edge/PnL/Sharpe/Friction.** Gate-Urteil
fällt der gate-auditor gegen den H-08-Registry-Eintrag; dieses Skript fällt
KEIN Gesamturteil.

**Unterschied zu H-07 (einziger):** Achse A ist rang-basiert und schwellen-frei
— je Bar das EINE extremste Symbol `i* = argmax |z|` (Gleichstand: alphabetisch
erstes Symbol, deterministisch), KEIN Magnitude-Schwellwert. Alles Übrige
(Achse B Crash-Dezil, Baseline, Surrogates, CIs, FDR-Mechanik, N-Floor,
Fenster) ist wörtlich H-07/DEC-17. Neue FDR-Familie: **F-XMR-RANK**.

## Aufruf (ein Befehl, keine Pflicht-Parameter, ca. 10-30 min)

    # Linux / macOS
    bash scinance2-impl/handoff_local/run_h08.sh

    # Windows (PowerShell 5.1)
    powershell -ExecutionPolicy Bypass -File .\scinance2-impl\handoff_local\run_h08.ps1

Ergebnisse landen unter `scinance2-impl/handoff_local/results/h08_<timestamp>/`
(`h08/c06_xmr_results.json` + `.md`, `SUMMARY_<datum>.md`, Logs).
Exit-Codes: 0 = OK · 1 = FAIL · 2 = SKIP (Harvester fehlt).

## Junction / Datenbasis

- Datenquelle: read-only Harvester-Backfill unter
  `data/harvest/raw/bybit/publicTrade/symbol=<SYM>/date=<d>/` (Junction
  `data/harvest`). **Kein Schreibzugriff** auf den Harvester-Baum (Schutzgut).
- Fehlt die Junction, Env `HARVEST_DIR` auf das Harvester-Root setzen:
  `HARVEST_DIR=/pfad/zu/harvest bash run_h08.sh`.
- Trockenlauf ohne Daten: `HANDOFF_DRY_RUN=1 bash run_h08.sh` (rc via
  `HANDOFF_DRY_RC`).

## Vorregistrierte Parameter (DEC-15 / DEC-17 / DEC-18 / H-08, NICHT ändern)

| Parameter | Wert |
|---|---|
| Panel | BTC/ETH/SOL/BNB/XRP (5 Perp) |
| Fenster A / B | ab 2026-04-15 / ab 2026-05-15 (je 2 Kalendertage, UTC) |
| Bar-Länge | 5 min (Last-Price je Bar, kontemporär synchronisiert, ffill <=1 Bar) |
| Lookback L | 12 Bars (60 min) |
| Achse A | RANG: `argmax \|z\|` je Bar, schwellen-frei (Gleichstand: alphabetisch erstes Symbol) |
| Crash-Dezil | 0.9 (Achse B: Panel-15min-RV NICHT im obersten Dezil — unverändert H-07) |
| Horizonte h | {1, 3, 6} Bars |
| N-Floor | 30 konditionierte Ereignisse / Fenster (durch Rang-1 jetzt erfüllbar) |
| Surrogates / Bootstrap | 200 / 1000 |
| FDR | F-XMR-RANK, BH-FDR alpha = 0.10 |

CLI-Äquivalent: `scripts/c06_xmr.py --overextension rank` (Default `z` bleibt
der unveränderte H-07-Pfad).

## Gate (gate-auditor gegen H-08 — hier nur zur Orientierung)

**WEITER** (ALLE gemeinsam, für >=1 Horizont in >=2 Fenstern):
1. konditioniert `mu_rev > 0` (echte Reversion, kein Momentum),
2. Surrogate-`p <= 0.05` nach BH-FDR alpha=0.10 über F-XMR-RANK,
3. `mu_rev > 0` + FDR-sig in **>= 2 disjunkten Fenstern**,
4. **Nicht-Trivialitäts-Anker (Pflicht):** die 95%-Block-Bootstrap-CI von
   `mu_rev,kond` liegt OBERHALB und überlappt NICHT die CI von
   `mu_rev,baseline`.

**DROP** (jede EINE Bedingung reißt, hartes Ein-Fenster-Kriterium, kein
GRAUBEREICH): Anker verfehlt (CIs überlappen) ODER `mu_rev <= 0` ODER
FDR-`p > 0.05` in >=1 Fenster ODER Verstärkung nur in 1 Fenster ODER N-Floor
verfehlt.

> **Verdünnung (ehrlich benannt, Registry H-08):** Rang-1 feuert JEDE Bar,
> auch bei ruhigem Panel — die Über-Dehnung ist im Mittel SCHWÄCHER als eine
> |z|>=2.5-Selektion. Die gesamte Beweislast liegt auf dem Nicht-Trivialitäts-
> Anker (CI-Trennung kond vs. Baseline). **A-priori: DROP.**

## Morgen-Auswertung / Upload

- Roh-Ergebnis (`h08/c06_xmr_results.json`, Pflicht-Marker
  `hypothesis: "H-08"`, `fdr_family: "F-XMR-RANK"`,
  `overextension_mode: "rank"`) + `SUMMARY_<datum>.md` an den Orchestrator
  hochladen. Der gate-auditor urteilt gegen H-08 und protokolliert nach
  `state/gate_log.md` als **GL-013**.
- `capital_free: true` im JSON ist Pflicht-Marker; Payload enthält KEINE
  bps/Edge/PnL/Sharpe/Friction-Felder.
