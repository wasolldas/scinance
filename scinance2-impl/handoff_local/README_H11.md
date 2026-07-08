# H-11 — AnEn-Vol-Regime-Forecast vs. HAR-RV (T2-Runner)

> ## STATUS: **GESPERRT** (data-gated)
>
> H-11 ist per Registry-Eintrag (`scinance2-impl/state/hypothesis_registry.md`,
> Welle 4) **DATA-GATED**: Real existiert heute nur EIN Fenster — die
> ≥2-Fenster-Schwelle ist aktuell nicht erfüllbar. Der Code ist vollständig
> gebaut und getestet (synthetische Fixtures), damit der Lauf startklar ist,
> sobald die Entsperr-Bedingung erfüllt ist. **Bis dahin: kein Datenlauf,
> kein Gate-Urteil.** Der Runner erkennt den gesperrten Zustand selbst und
> meldet sauber SKIP (Exit-Code 2) — er crasht nicht.

## Entsperr-Bedingung (Teil der Pre-Registration, Schwelle wird NICHT gesenkt)

Manifest bestätigt **lückenlose done_days** für bybit `publicTrade` **UND**
`rest.fundingRate`, **BTC+ETH**, mindestens über **2024-03-27..2026-03-26**
(**≥730 Tage zusammenhängend**).

Programmatische Prüfung: `check_unlock` in
`src/bybit_edge/research/c11_anen/driver.py` fragt PRIMÄR das echte
`harvest_manifest.sqlite` (`data/harvest/state/harvest_manifest.sqlite`,
Tabelle `partitions`, read-only, Status `DONE` je Tag) ab — die
DATASET.md-§7-Manifest-Abfrage wörtlich
(`done_days == last_done − first_done + 1` ⇒ lückenlos). Nur wenn die
Manifest-Datei fehlt, fällt der Check auf einen `date=`-Partitionsordner-Scan
zurück (`data/harvest/raw/bybit/<stream>/symbol=<SYM>/date=<d>/`, ≥1
Parquet-Datei mit Größe > 0). Jeder fehlende Tag in der Range ⇒ gesperrt.

## Was ist H-11?

AnEn-Vol-Regime-Forecast (Analog-Ensemble, Delle Monache et al. 2013, k=20)
vs. HAR-RV (Corsi) über den 3-Tage-Horizont, **KAPITALFREI** (reines
Mess-Gate; Monetarisierung wäre NEUE H-11b — die Registry erwähnt die
25–75×-Friktions-Größenordnung nur narrativ, es wird KEINE Kostenrechnung
implementiert).

- **Features (5, OI EXKLUDIERT):** log RV_1d, log RV_5d, log RV_20d,
  Funding-Tagesmittel, Funding-5d-Trend (je Symbol, je Tag).
- **Fenster:** L = 2024-03-27..2025-09-30 (LOO-CRPS-Gewichtstuning, Grid
  {0;0,5;1;1,5;2}⁵, danach eingefroren) · W1 = 2025-10-01..2026-03-26 ·
  W2 = 2026-03-27..2026-06-30 — alle disjunkt, 30-Tage-Embargo zwischen
  Analog-Kandidat und aktuellem Zustand (t' ≤ t−30).
- **Ziel:** log annualisierte RV über t+1..t+3 (1-min-Returns, in DuckDB
  aggregiert — keine Tick-zu-Tick-Returns). **AnEn-Vorhersageverteilung** =
  empirische Verteilung der log-RV(t'+1..t'+3) der 20 Analoga, gescort mit
  echtem **Ensemble-CRPS** (Gneiting & Raftery 2007). Das entartete
  Punkt-CRPS (=|Prognose−Beobachtung|) gilt NUR für die HAR-Baseline
  (vorregistriert) — es kollabiert das Ensemble NICHT auf seinen Mittelwert.
- **Baseline:** HAR-RV OLS auf (log RV_1d, RV_5d, RV_22d), expanding ≤ t−30,
  monatlicher Refit, CRPS = |Prognose−Beobachtung| (entartete Verteilung,
  Punktprognose).
- **Null:** Block-Bootstrap (5-Tage-Blöcke, 1.000 Reps, DM-artig) je
  Symbol×Fenster für H0: mittlere CRPS-Differenz (HAR−AnEn) ≤ 0.
- **Gate (gate-auditor urteilt):** WEITER wenn für ≥1 Symbol ∈ {BTC,ETH} in
  BEIDEN Fenstern CRPSS = 1−ΣCRPS_AnEn/ΣCRPS_HAR ≥ 0,05 UND
  Bootstrap-p ≤ 0,05 nach BH-FDR α=0,10 über **F-ANEN** (2×2=4 Zellen).
  Hartes Ein-Fenster-DROP, kein Graubereich. A-priori: DROP.

## Sobald entsperrt — was zu tun ist

1. **Nur Entsperr-Check (schnell, ~Sekunden):**
   ```
   python scripts\c11_anen.py --check-unlock-only
   ```
   Exit 0 = entsperrt, Exit 2 = weiterhin gesperrt (JSON-Diagnose auf stdout
   zeigt je Stream/Symbol die fehlenden Tage).
2. **Voller Lauf (ein Befehl, prüft die Entsperr-Bedingung selbst nochmal):**
   ```
   powershell -ExecutionPolicy Bypass -File .\run_h11.ps1     (Windows)
   bash scinance2-impl/handoff_local/run_h11.sh               (Linux/WSL)
   ```
   Budget: ~5 min Check + bis ~60 min Voll-Lauf (LOO-Tuning über 3125
   Gewichts-Kombos × ~550 Tuning-Tage; CPU, trivial parallelisierbar-frei).
3. Ergebnisse liegen unter `handoff_local/results/h11_<timestamp>/`
   (`SUMMARY_<datum>.md` + `h11/c11_anen_results.{json,md}`) → hochladen,
   der **gate-auditor** urteilt gegen den registrierten H-11-Eintrag
   (nächstes freies GL-Verdikt).

## Verhalten im gesperrten Zustand (heute)

Runner-Ausgabe: `H-11 gesperrt - Manifest-Coverage <730 Tage,
Entsperr-Bedingung nicht erfuellt` · Schritt `H11_ANEN` = SKIP · Exit 2.
Kein Fehler, kein Datenzugriff über den Partitions-Ordner-Scan hinaus.

Env-Overrides: `HARVEST_DIR` (Junction-Pfad), `H11_RESULTS_DIR`,
`HANDOFF_DRY_RUN=1` (+`HANDOFF_DRY_RC`), `PYTHON`.

## Dateien

- `src/bybit_edge/research/c11_anen/` — `features.py` (kausale
  Feature-/Target-Berechnung), `analog.py` (k-NN-Ensemble + LOO-CRPS-Tuning),
  `baseline.py` (HAR-RV, eigene Kopie nach c42_rv-Muster), `stats.py`
  (Block-Bootstrap + eigene BH-FDR-Kopie), `driver.py` (Orchestrierung +
  `check_unlock`).
- `scripts/c11_anen.py` — CLI (`--check-unlock-only`, Exit 0/1/2).
- `tests/unit/test_c11_anen.py` — Kausalität/No-Lookahead, Embargo,
  HAR-Korrektheit, CRPSS, Positiv-/Null-Kontrolle, Entsperr-Check,
  End-to-End auf synthetischem Harvester-Baum (≥800 Tage), capital_free.
