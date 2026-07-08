# H-12 · Cross-Exchange-Fragmentierungsmatrix Mess-Gate (RMT/MP-IPR, F-FRAG, KAPITALFREI)

T2-Lauf des kapitalfreien RMT/MP-IPR-Mess-Gates auf dem read-only
Harvester-Backfill (Welle 4 — Cross-Domain-Track, Herkunft IC-RMT-2).
**Reine Mess-/Explorationsfrage — KEIN Kosten-/Handels-/Latenz-Bezug; ein
Cross-Exchange-Arbitragesignal wäre eine NEUE H-12b, NICHT impliziert.**
Gate-Urteil fällt der gate-auditor gegen den H-12-Registry-Eintrag
(`scinance2-impl/state/hypothesis_registry.md` → „### H-12 ·
Cross-Exchange-Fragmentierungsmatrix"); dieses Skript fällt KEIN Gesamturteil.

> **Status:** Code komplett gebaut und gegen synthetische Harvester-Bäume
> getestet (`tests/unit/test_c12_frag.py`); **KEIN Lauf gegen echte Daten
> erfolgt, KEIN Commit** (siehe DEC-20 in `state/decisions.md` — Fable-5-
> Wochenlimit erreicht, CLI/Runner/Tests von Sonnet nachgezogen; die
> Statistik-Substanz der 5 Moduldateien selbst stammt unverändert von Fable 5).

## Aufruf (ein Befehl, keine Pflicht-Parameter, ca. 20-40 min)

```powershell
powershell -ExecutionPolicy Bypass -File .\scinance2-impl\handoff_local\run_h12.ps1   # Windows (PS 5.1)
```
```bash
bash scinance2-impl/handoff_local/run_h12.sh                                          # Linux/macOS
```

Ergebnisse landen unter `scinance2-impl/handoff_local/results/h12_<timestamp>/`
(`h12/c12_frag_results.json` + `.md`, `SUMMARY_<datum>.md`, Logs).
Exit-Code: 0 = OK · 1 = FAIL · 2 = SKIP (Junction fehlt).

Die Laufzeit ist deutlich höher als bei den anderen Welle-4-T2-Runnern, weil
je gültigem Tag ZWEI unabhängige Monte-Carlo-Simulationen mit je 1000
Replikationen laufen (Stufe-a-Wishart-Referenz einmal je Fenster, Stufe-b-
Ein-Faktor-Null einmal PRO TAG) — bei ~70-100 gültigen Tagen über beide
Fenster ergibt das insgesamt ~70.000-100.000 6x6-Eigenzerlegungen zzgl. der
beiden Stufe-a-Referenzen. Timeout-Budget im Runner: 2400 s.

## Junction / Datenbasis

- Datenquelle: read-only Harvester-Backfill unter
  `data/harvest/raw/<exchange>/publicTrade/symbol=<SYM>/date=<d>/`
  (Junction `data/harvest`). **Kein Schreibzugriff** auf den Harvester-Baum
  (Schutzgut). Der Runner prüft VOR dem Lauf, dass ALLE DREI Börsen-Pfade
  existieren (`raw/bybit/publicTrade`, `raw/binance/publicTrade`,
  `raw/deribit/publicTrade`) — fehlt auch nur einer, wird sauber übersprungen
  (SKIP, exit 2), denn die Korrelationsmatrix braucht alle 6 Serien.
- Fehlt die Junction, Env `HARVEST_DIR` auf das Harvester-Root setzen:
  `HARVEST_DIR=/pfad/zu/harvest bash run_h12.sh`.
- Trockenlauf ohne Daten: `HANDOFF_DRY_RUN=1 bash run_h12.sh` (rc via
  `HANDOFF_DRY_RC`).

## Symbol-Mapping (Deribit-Notation)

Interne Programmnotation ist durchgehend die Bybit-Schreibweise
(`BTCUSDT`/`ETHUSDT`); Bybit und Binance teilen sich diese Notation direkt.
Deribit-Perp-Instrumente heißen abweichend `BTC-PERPETUAL`/`ETH-PERPETUAL`
(Registry H-12 / DATASET.md SRC-10/11). Das Mapping liegt fest in
`panel.DERIBIT_SYMBOL_MAP` (`src/bybit_edge/research/c12_frag/panel.py`):

| Interne Notation | Deribit-Storage-Symbol |
|---|---|
| `BTCUSDT` | `BTC-PERPETUAL` |
| `ETHUSDT` | `ETH-PERPETUAL` |

`panel.map_exchange_symbol(exchange, symbol)` wendet das Mapping an
(Fallback für unbekannte Deribit-Symbole: `<BASE>-PERPETUAL`). Die
Storage-Partition unter `raw/deribit/publicTrade/symbol=BTC-PERPETUAL/...`
muss entsprechend existieren — NICHT `symbol=BTCUSDT`.

Die sechs Panel-Spalten sind exchange-major geordnet:
`bybit:BTCUSDT, bybit:ETHUSDT, binance:BTCUSDT, binance:ETHUSDT,
deribit:BTC-PERPETUAL, deribit:ETH-PERPETUAL`.

## Vorregistrierte Parameter (Registry H-12, NICHT ändern)

| Parameter | Wert |
|---|---|
| Panel | BTC/ETH-Perp × {Bybit, Binance, Deribit} = 6 Serien |
| Bar | Minuten-Last-Price je `[t, t+60s)`, Forward-Fill ≤ 1 min |
| Fenster | W1 = 2026-03-27..2026-05-15, W2 = 2026-05-16..2026-07-04 (identisch H-09) |
| Tagesfenster | UTC, T=1440; Tag gültig ⟺ jede Serie ≥1380/1440 gültige Minuten |
| Spektrum | Log-Returns je Serie je Tag z-standardisiert, Korrelationsmatrix C (6×6), Eigenzerlegung λ1≥...≥λ6, IPR(v)=Σv_i⁴ |
| Null Stufe a | MC-Gaussian-Wishart-Referenz (Q=T/N=240), 1000 Ziehungen, NICHT urteilstragend |
| Null Stufe b | Ein-Faktor-Gauss-Null je Tag aus (λ1,v1), 1000 Replikationen, urteilstragend; Tages-p = P(λ2_sim≥λ2_obs) |
| FDR | **F-FRAG** — alle Tages-λ2-Tests beider Fenster (~70-100 Tests), BH-FDR α=0,10 |
| Seed | 42 |

## Gate (gate-auditor gegen H-12 — hier nur zur Orientierung)

**WEITER**, wenn in BEIDEN Fenstern gilt:

1. (a) Anteil gültiger Tage mit λ2 nach BH-FDR α=0,10 über F-FRAG signifikant
   über der Ein-Faktor-Null ≥20%,
2. (b) Median-IPR(v2) über den FDR-signifikanten Tagen ≥0,40
   (delokalisiert wäre 1/6≈0,167),
3. (c) an ≥70% der FDR-signifikanten Tage entfällt die größte v2²-Börsenlast
   auf dieselbe Börse.

**DROP** (hartes Ein-Fenster-Kriterium, kein GRAUBEREICH): (a), (b) oder (c)
in einem Fenster verfehlt. Kein Nachverhandeln von Bar-Raster,
Tages-Gültigkeitsquote oder IPR-Schwelle.

### Validitäts-Vorbedingung (VOR dem Gate, KEIN Gate-Bestandteil)

`IPR(v1) ≤ 0,25` an ≥90% der gültigen Tage UND ≥35 gültige Tage je Fenster.
Wird das verfehlt, ist der Lauf **UNGÜLTIG**: eigener `validity_status` im
JSON-Payload (`"ungueltig"` statt `"gueltig"`), **KEIN Verdikt**, explizit
**NICHT DROP**. Grund: Uhren-Asynchronität zwischen Börsen kann Schein-
Restmoden erzeugen oder echte verwischen — die Vorbedingung fängt grob
degenerierte Panels ab, bevor das Gate überhaupt geprüft wird.

**A-priori (ehrlich, Registry):** DROP erwartet (Fragmentierungs-Anteil unter
20% — liquide Perps sind auf Minutenskala eng arbitriert).

## Kapitalfreiheit

Reine Mess-/Explorationsfrage — im gesamten Modul existiert keine
Kosten-/Ertragsrechnung (von den Tests erzwungen: kein `bps`/`pnl`/`sharpe`/
`friction`/`edge_`-Token irgendwo im JSON-Payload, `capital_free: true`).

## Tests (Sandbox, alles synthetisch)

```
PYTHONPATH=src python3 -m pytest tests/unit/test_c12_frag.py -q
```

Deckt ab: Spektrum-Korrektheit an bekanntem Ein-Faktor-Fall (IPR(v2) NICHT
lokalisiert, ≈1/6), Kalibrierung der Ein-Faktor-Null, End-to-End-Null-Kontrolle
(rein ein-faktoriell erzeugte Panels → Gate-Kriterien NICHT erfüllt),
End-to-End-Positiv-Detektion (gemeinsamer Marktfaktor + lokalisierter
Börsen-Restfaktor bei 2 von 6 Serien → alle drei Kriterien erfüllt),
Validitäts-Vorbedingung (zu wenige gültige Tage → „ungültig", nicht „DROP"),
Kapitalfreiheits-Wächter, End-to-End gegen einen synthetischen 3-Börsen-
Harvester-Baum über die volle CLI (`scripts/c12_frag.py`, rc=0, valides JSON).

## Upload / Morgen-Auswertung

Nach dem Lauf den kompletten Ordner
`scinance2-impl/handoff_local/results/h12_<timestamp>/` hochladen bzw. in der
Sandbox verfügbar machen. Der gate-auditor wertet `h12/c12_frag_results.json`
gegen den H-12-Registry-Eintrag aus → das Verdikt wird in
`state/gate_log.md` protokolliert. Kohorten-Regel beachten: laufen ≥2 der
sofort testbaren Welle-4-Hypothesen (H-09/H-10/H-12) als gemeinsame Kohorte,
ist VOR jenem Lauf die Über-Familie F-XDOM1 zu registrieren.
