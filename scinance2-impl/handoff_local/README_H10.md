# H-10 · Cross-Stream-Pointer-Days + Pre-Event-Drift (KAPITALFREI)

T2-LOCAL_SHORT-Lauf des kapitalfreien Zwei-Stufen-Mess-Gates (F-POINTER) auf
dem read-only Harvester-Baum. **Reine Mess-/Existenzfrage — KEINE
Kapital-Metriken.** Gate-Urteil fällt der gate-auditor gegen den
H-10-Registry-Eintrag; dieses Skript fällt KEIN Gesamturteil.

- **Stufe 1 (Synchronisations-Existenz):** Pointer-Tage über die vorab
  fixierten **30 Detektions-Serien** (5 Perp-Symbole × {bybit, binance} ×
  {RV, Funding, ΔlogOI}) — Tag t ist Pointer-Tag, wenn `n_avail ≥ 18` UND
  `max(#{C ≥ 1.5}, #{C ≤ −1.5}) / n_avail ≥ 0.60` (Cropper-Score auf trailing
  63-Tage-Median-Residuen, zentriertes 11-Tage-Fenster). Null: 1.000
  zirkuläre Surrogate je Serie (Marginal/Autokorrelation erhalten,
  Cross-Ausrichtung zerstört).
- **Stufe 2 (Pre-Event-Drift, Hold-out):** dvol-Index D_t = z-standardisiertes
  Mittel der Deribit-dvol-Level **BTC + ETH** (Symbole `BTC`/`ETH`, NICHT
  `BTCUSDT`; dvol und book_summary sind vollständig aus der Detektion
  ausgeschlossen). Δpre(t) = Mittel(D,[t−5,t−1]) − Mittel(D,[t−15,t−6]);
  S = Mittel(Δpre) über die Pointer-Tage des Fensters. Null: 1.000
  Permutations-Ziehungen gleich großer Zufalls-Tagesmengen mit ≥ 6 Tagen
  Abstand zu JEDEM Pointer-Tag; p zweiseitig.

## Aufruf (ein Befehl, keine Pflicht-Parameter, ca. 5-20 min)

    # Linux / macOS
    bash scinance2-impl/handoff_local/run_h10.sh

    # Windows (PowerShell 5.1)
    powershell -ExecutionPolicy Bypass -File .\scinance2-impl\handoff_local\run_h10.ps1

Ergebnisse landen unter `scinance2-impl/handoff_local/results/h10_<timestamp>/`
(`h10/c10_pointer_results.json` + `.md`, `SUMMARY_<datum>.md`, Logs).
Exit-Codes: 0 = OK · 1 = FAIL · 2 = SKIP (Harvester-/Hold-out-Pfad fehlt).

## Junction / Datenbasis

- Datenquelle: read-only Harvester-Baum unter
  `data/harvest/raw/<exchange>/<stream>/symbol=<SYM>/date=<d>/` (Junction
  `data/harvest`). **Kein Schreibzugriff** auf den Harvester-Baum (Schutzgut).
- Fehlt die Junction, Env `HARVEST_DIR` auf das Harvester-Root setzen:
  `HARVEST_DIR=/pfad/zu/harvest bash run_h10.sh`.
- Der Runner prüft VOR dem Lauf `raw/bybit/publicTrade` UND
  `raw/deribit/dvol` (Stufe 2 braucht den Hold-out zwingend) → sonst SKIP.
- Trockenlauf ohne Daten: `HANDOFF_DRY_RUN=1 bash run_h10.sh` (rc via
  `HANDOFF_DRY_RC`).

## Die 4 Stream-Loader (NEU, `c10_pointer/loaders.py`) — Annahmen

| Stream | Aggregat | payload_json-Feld(er) | Sicherheit |
|---|---|---|---|
| `publicTrade` → RV | Tages-Last-Price via `arg_max(price, ts)`; RV_t = (Δlog P_Tag)² | `price` (Backfill), Fallback `p` (Live) | GESICHERT (identisch `load_harvest_window`) |
| `rest.fundingRate` → Funding | Tagesmittel | `fundingRate`, Fallback `lastFundingRate` (Binance-REST-Form) | Bybit GESICHERT (Registry); Binance-Fallback = **ANNAHME** |
| `rest.openInterest` → ΔlogOI | Tagesschluss (last by ts), dann Δlog | `openInterest`, Fallback `sumOpenInterest` (Binance-Form) | Bybit GESICHERT (Registry); Binance-Fallback = **ANNAHME** |
| `dvol` (deribit, Hold-out) | Tagesmittel | Kandidaten in Reihenfolge: `dvol`, `value`, `index_value`, `close`, `price`; sonst **erstes numerisches Top-Level-Feld mit WARN-Log** | Payload-Struktur **UNBEKANNT-GENERISCH** — Feldwahl ist eine dokumentierte Annahme; WARN im stderr-Log (`H10_POINTER.err.log`) prüfen! |

RV-Lesart (Registry wörtlich "Last-Price je Tages-Bar, log-Return-Quadrate
summiert"): mit TAGES-Bars reduziert sich die Summe auf das EINE quadrierte
Tages-Log-Return pro Tag — exakt so implementiert (Kommentar in
`loaders.py::rv_from_daily_last_price`).

## Vorregistrierte Parameter (Registry H-10, NICHT ändern)

| Parameter | Wert |
|---|---|
| Detektions-Serien | 30 = 5 Symbole (BTC/ETH/SOL/BNB/XRP-USDT) × {bybit, binance} × {RV, Funding, ΔlogOI} |
| Hold-out-Ziel | Deribit `dvol` BTC + ETH (NIE in der Detektion) |
| Tagesraster | 2026-03-27..2026-07-04 UTC, Burn-in 21 Tage |
| Fenster | W1 = 2026-04-17..2026-05-25 (39 Tage) · W2 = 2026-05-26..2026-07-04 (40 Tage) |
| Detrending | trailing 63-Tage-Median, min_periods = 21 |
| Cropper | zentriertes 11-Tage-Fenster, Schwelle \|C\| ≥ 1.5 |
| Pointer-Tag | n_avail ≥ 18 UND Anteil gleicher Richtung ≥ 0.60 |
| Stufe-1-Null | 1.000 zirkuläre Surrogate je Serie |
| Stufe-2-Null | 1.000 Permutations-Ziehungen, ≥ 6 Tage Abstand zu jedem Pointer-Tag, p zweiseitig |
| N-Floor | 3 Pointer-Tage je Fenster (**NICHT absenkbar**) |
| FDR | F-POINTER (4 Zellen = 2 Stufen × 2 Fenster), BH-FDR α = 0.10 |

CLI-Äquivalent: `scripts/c10_pointer.py` (Defaults = obige Werte).

## Gate (gate-auditor gegen H-10 — hier nur zur Orientierung)

**WEITER**, wenn nach BH-FDR α=0.10 über F-POINTER ALLE 4 Zellen bestehen:
1. Stufe-1-Surrogat-p ≤ 0.05 in W1 UND W2,
2. N_pointer ≥ 3 je Fenster (Power-DROP sonst; Schwellen 60%/1.5 werden NICHT gesenkt),
3. Stufe-2-Permutations-p ≤ 0.05 (zweiseitig) in W1 UND W2.

**DROP** (hartes Ein-Fenster-Kriterium): eine Zelle verfehlt → DROP. Kein
Graubereich. A-priori: Stufe 1 WEITER-nah, Stufe 2 DROP erwartet.
