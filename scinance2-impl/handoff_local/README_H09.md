# H-09 · Risk-Limit-Tier-Bunching Mess-Gate (F-BUNCH, KAPITALFREI)

T2-Lauf des kapitalfreien Bunching-Mess-Gates auf dem read-only
Harvester-Backfill (Welle 4 — Cross-Domain-Track, DEC-19, Herkunft
IC-MECH-2). **Reiner Struktur-/Verhaltensfakt — KEINE Kosten-/Handels-/
Latenz-Spalten; eine Tradability-Folge waere eine NEUE H-09b, NICHT
impliziert.** Gate-Urteil faellt der gate-auditor gegen den
H-09-Registry-Eintrag; dieses Skript faellt KEIN Gesamturteil.

## Aufruf (ein Befehl, keine Pflicht-Parameter, ca. 15-90 min je nach Datenvolumen)

    # Linux / macOS
    bash scinance2-impl/handoff_local/run_h09.sh

    # Windows (PowerShell 5.1)
    powershell -ExecutionPolicy Bypass -File .\scinance2-impl\handoff_local\run_h09.ps1

Ergebnisse landen unter `scinance2-impl/handoff_local/results/h09_<timestamp>/`
(`h09/c09_bunch_results.json` + `.md`, `SUMMARY_<datum>.md`, Logs).
Exit-Code: 0 = OK · 1 = FAIL · 2 = SKIP (Junction fehlt).

## !!! K_s-PLATZHALTER-WARNUNG (VOR echtem Gate-Urteil lesen) !!!

Die Tier-1→2-Risk-Limit-Kanten `K_s` je Symbol liegen in
`src/bybit_edge/research/c09_bunch/kinks.py`
(`RISK_LIMIT_TIER1_KINK_USDT`). **Nur BTCUSDT = 2.000.000 USDT ist im
Registry-Eintrag beziffert** (MMR 0,50% → 0,56%). Die uebrigen vier sind
konservative, plausible **PLATZHALTER**:

| Symbol | K_s (USDT) | Status |
|---|---:|---|
| BTCUSDT | 2.000.000 | registry-beziffert |
| ETHUSDT | 1.500.000 | **PLATZHALTER** |
| SOLUSDT | 1.000.000 | **PLATZHALTER** |
| BNBUSDT | 500.000 | **PLATZHALTER** |
| XRPUSDT | 500.000 | **PLATZHALTER** |

Vor dem echten Lauf MUSS (Registry H-09 Methodik, DEC-09-Muster):

1. jede Kante gegen die **aktuelle Bybit-Risk-Limit-Tabelle** verifiziert,
2. geprueft werden, dass K_s **ueber BEIDE Fenster W1+W2 konstant** war
   (historische K_s-Aenderungen invalidieren Zellen — Selbstkill-Klausel),
3. das Ergebnis als **datierter, append-only Operationalisierungs-Nachtrag**
   an den H-09-Registry-Eintrag angehaengt werden.

Das ist KEIN Torpfosten-Verstoss: die Methode ist fix vorregistriert, nur der
Zahlenwert wird recherchiert. Der JSON-Payload traegt je Zelle
`kink_is_placeholder` + die Warnung in `kink_placeholder_note`.

## Junction / Datenbasis

- Datenquelle: read-only Harvester-Backfill unter
  `data/harvest/raw/bybit/publicTrade/symbol=<SYM>/date=<d>/` (Junction
  `data/harvest`). **Kein Schreibzugriff** auf den Harvester-Baum (Schutzgut).
- Fehlt die Junction, Env `HARVEST_DIR` auf das Harvester-Root setzen:
  `HARVEST_DIR=/pfad/zu/harvest bash run_h09.sh`.
- Trockenlauf ohne Daten: `HANDOFF_DRY_RUN=1 bash run_h09.sh` (rc via
  `HANDOFF_DRY_RC`).
- Speicherhinweis: die Order-Aggregation (`GROUP BY ts_exchange_ms, side` +
  `SUM(price*size)`) laeuft VOLLSTAENDIG in DuckDB; es gibt **kein**
  Tick-Limit mehr und **keinen** `--max-ticks`-Schalter (audit_h09.md Bugs
  1+2 behoben) — nur die kleine Notional-Liste je Fenster erreicht Python,
  RAM bleibt window-fuer-window begrenzt statt alle 10 Fenster gleichzeitig
  zu halten.
- Faellt ein Symbol beim Laden aus (fehlende/luekenhafte Daten), wird es NICHT
  stillschweigend aus der F-BUNCH-Familie entfernt: es wird als p=1.0-
  Sentinel-Zelle in beide Fenster eingefuegt (Familiengroesse bleibt bei 10),
  `family_size_deviation: true` gesetzt und `gate_valid_assumptions` auf
  `false` erzwungen (audit_h09.md Bug 3).

## Vorregistrierte Parameter (Registry H-09 / DEC-19, NICHT aendern)

| Parameter | Wert |
|---|---|
| Panel | BTC/ETH/SOL/BNB/XRP (5 USDT-Perp) |
| Fenster | W1 = 2026-03-27..2026-05-15, W2 = 2026-05-16..2026-07-04 |
| Beobachtungseinheit | Taker-Order-Aggregat (konsekutive publicTrade-Records gleichen symbol/side/ts_exchange_ms gemerged), urteilstragend |
| Schaetzband | [0,40·K_s, 1,30·K_s), Bin-Breite 0,01·K_s (90 Bins) |
| Counterfactual | Polynom Grad 7, Ausschluss [0,90·K_s, 1,10·K_s) |
| Bunching-Fenster B− | [0,95·K_s, 1,00·K_s) |
| Kontrollfenster B+ | (1,00·K_s, 1,05·K_s] |
| Bootstrap | Residuen-Bootstrap (Chetty et al. 2011), 500 Reps, Seed 42 |
| Placebos | P1 = 0,5·K_s, P2 = 0,75·K_s (NICHT Teil der FDR-Familie) |
| N-Floor | ≥2.000 Order-Beobachtungen im Band UND Counterfactual-Erwartung in B− ≥50, sonst Zelle ungueltig |
| FDR | F-BUNCH = 5 Symbole × 2 Fenster (Order-Level) = 10 Tests, BH-FDR alpha = 0,10 |

## Gate (gate-auditor gegen H-09 — hier nur zur Orientierung)

**WEITER**, wenn fuer mindestens 1 Symbol in BEIDEN Fenstern (gueltige Zelle)
ALLE vier Bedingungen gelten:

1. Bootstrap-p(b̂−→0) ≤ 0,05 nach BH-FDR alpha=0,10 ueber F-BUNCH,
2. b̂− ≥ 1,0,
3. b̂− − b̂+ ≥ 0,5 (asymmetrische Signatur),
4. b̂− > max(b̂_P1, b̂_P2) (staerker als Rundzahl-Praeferenz).

**DROP** (hartes Ein-Fenster-Kriterium, kein GRAUBEREICH): kein Symbol
erfuellt alle vier Bedingungen in beiden Fenstern ODER der N-Floor wird in
einem Fenster von allen 5 Zellen verfehlt (DROP wegen Power, KEINE
Floor-Absenkung). Keine nachtraegliche Band-/Bin-/Placebo-Anpassung
(`gate_valid_assumptions` im JSON schuetzt den registrierten Punkt).
**A-priori (ehrlich, Registry): DROP erwartet** (Rundzahl-Praeferenz statt
Kanten-Effekt).

## Upload / Morgen-Auswertung

Nach dem Lauf den kompletten Ordner
`scinance2-impl/handoff_local/results/h09_<timestamp>/` hochladen bzw. in der
Sandbox verfuegbar machen. Der gate-auditor wertet `h09/c09_bunch_results.json`
gegen den H-09-Registry-Eintrag aus → das Verdikt wird als **GL-014ff.**
(erstes Welle-4-Verdikt; die GL-Zaehlung steht bis dahin bei GL-013)
in `state/gate_log.md` protokolliert. Vorbedingung fuer ein gueltiges
Verdikt: der K_s-Operationalisierungs-Nachtrag (s.o.) liegt vor.
Kohorten-Regel beachten: laufen ≥2 der sofort testbaren Welle-4-Hypothesen
(H-09/H-10/H-12) als gemeinsame Kohorte, ist VOR jenem Lauf die
Ueber-Familie F-XDOM1 zu registrieren.
