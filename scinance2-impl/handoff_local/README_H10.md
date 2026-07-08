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
- **Stufe 2 (Pre-Event-Drift, Hold-out):** dvol-Index D_t = Mittel der JE
  SERIE z-standardisierten Deribit-dvol-Tagesschlüsse **BTC + ETH** (Symbole
  `BTC`/`ETH`, NICHT `BTCUSDT`; dvol und book_summary sind vollständig aus
  der Detektion ausgeschlossen; z-Parameter über den nutzbaren Zeitraum,
  siehe DEC-21 in `state/decisions.md`). Δpre(t) = Mittel(D,[t−5,t−1]) −
  Mittel(D,[t−15,t−6]); S = Mittel(Δpre) über die Pointer-Tage des Fensters.
  Null: 1.000 Permutations-Ziehungen gleich großer Zufalls-Tagesmengen mit
  ≥ 6 Tagen Abstand zu JEDEM Pointer-Tag; p zweiseitig.
- **Neuwirth-Fenster-Crosscheck (mitberichtet, NICHT-urteilstragend):**
  dieselbe Detrend-/Pointer-Regel mit einem 13-Tage-Fenster statt des
  urteilstragenden 11-Tage-Cropper-Fensters — reines Anti-Method-Shopping-
  Diagnostikum im JSON-Payload (`neuwirth_crosscheck`), geht in KEINE Zelle,
  KEIN p, KEINE FDR ein (Registry H-10 "Methoden-Fixierung").

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
- Der Runner prüft VOR dem Lauf `raw/bybit/publicTrade`, `raw/binance/rest.fundingRate`,
  `raw/binance/rest.openInterest` UND `raw/deribit/dvol` (Stufe 2 braucht den
  Hold-out zwingend, die Detektion braucht beide Exchanges) → sonst SKIP
  (audit_h10 BUG-5: der alte Pre-Check prüfte nur 2 der 4 benötigten Pfade).
- Trockenlauf ohne Daten: `HANDOFF_DRY_RUN=1 bash run_h10.sh` (rc via
  `HANDOFF_DRY_RC`).
- Die CLI (`scripts/c10_pointer.py`) bricht mit rc=1 ab, wenn die
  Detektions-Serien strukturell unter dem `n_avail`-Floor (18) bleiben ODER
  der Hold-out-dvol unter `DVOL_MIN_USABLE_DAYS=30` nutzbare Tage hat — sonst
  würde ein Feldnamen-Fehlgriff (BUG-3/4) als vollständig aussehendes, aber
  bedeutungsloses DROP-Payload mit rc=0 durchrutschen (audit_h10 BUG-5).

## Die 4 Stream-Loader (NEU, `c10_pointer/loaders.py`) — Annahmen

| Stream | Aggregat | payload_json-Feld(er) | Sicherheit |
|---|---|---|---|
| `publicTrade` → RV | 1-Min-Last-Price-Bars (`max_by(price, ts)` je 60s-Bucket, wie `c12_frag`); RV_t = log Σ(Δlog P_1min)² je Tag; NaN bei < `RV_MIN_BARS_PER_DAY`=30 Bars | `price` (Backfill), Fallback `p` (Live) | GESICHERT (identisches Feld-Coalesce wie `load_harvest_window`); RV-Definition = wörtlich hardened_hypotheses.md |
| `rest.fundingRate` → Funding | Tagesmittel | `fundingRate`, Fallback `lastFundingRate` (Binance-REST) bzw. `info.fundingRate` (ccxt-normalisiert, DATASET.md §6) | Bybit GESICHERT (Registry); Binance-Fallbacks = **ANNAHME** |
| `rest.openInterest` → ΔlogOI | Tagesschluss (last by ts), dann Δlog | `openInterest`, Fallback `openInterestAmount` (ccxt Top-Level), `sumOpenInterest`, `info.sumOpenInterest` (ccxt-normalisiert, DATASET.md §6) | Bybit GESICHERT (Registry); Binance-Fallbacks = **ANNAHME** |
| `dvol` (deribit, Hold-out) | Tagesschluss (last by ts) | Kandidaten in Reihenfolge: `dvol`, `value`, `index_value`, `close`, `price`, `volatility`, `mark_iv`; sonst **erstes numerisches, NICHT-zeitstempel-artiges Top-Level-Feld (Wert ≤ 1e6) mit WARN-Log** | Payload-Struktur **UNBEKANNT-GENERISCH** — Feldwahl ist eine dokumentierte Annahme; Parse-Modus steht im JSON-Payload (`dvol_parse_mode`), WARN zusätzlich im stderr-Log (`H10_POINTER.err.log`) |

**RV-Lesart (korrigiert, audit_h10 BUG-1):** die registrierte Definition ist
wörtlich `hardened_hypotheses.md` H-10 "Methodik": "RV = log Σ r²(1-min-
Last-Price) je Tag" — 1-Minuten-Bars, NICHT ein einzelner quadrierter
Tages-Return, UND mit äußerem Logarithmus. (Eine frühere Code-/README-Fassung
rationalisierte eine TAGES-Bar-Kurzform mit einem angeblichen Registry-Zitat
"Last-Price je Tages-Bar, log-Return-Quadrate summiert" — dieses Zitat
existiert in KEINEM der beiden Ground-Truth-Dokumente und wurde entfernt;
siehe `state/audit_h10.md` BUG-1.)

**Coverage-Audit (audit_h10 BUG-3):** jede Serie, deren Partitionen existieren
aber auf 0 finite Tage parsen (falscher Feldname), löst eine WARN im
stderr-Log aus; `detection_series_finite_days` im JSON-Payload zeigt die
finite-Tage-Zahl je der 30 Serien für eine nachträgliche Prüfung.

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
