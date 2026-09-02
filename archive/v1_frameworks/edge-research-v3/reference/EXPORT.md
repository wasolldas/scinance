# Tick-Level-Export für Downstream-Tools (`scripts/export_symbol.py`)

Read-only/standalone — flacht das immutable Roh-Archiv in eine **side-erhaltende
Trades-Tabelle** ab. **Keine Aggregation.** Berührt Harvester/Manifest/Archiv
nicht (Schutzgut) und importiert NICHT das `harvester`-Paket (läuft mit nur
`pyarrow` — kein zstandard/ccxt nötig).

## Output-Schema (eine Zeile pro Trade)

| Spalte | Typ | Bedeutung |
|---|---|---|
| `ts_exchange_ms` | int64 | Börsen-Event-Zeit (ms) |
| `side` | string | `"Buy"` / `"Sell"` (normalisiert: `BUY`/`SELL`-Varianten → `Buy`/`Sell`; Nicht-buy/sell-Werte bleiben verbatim sichtbar) |
| `price` | double | |
| `size` | double | |
| `symbol` | string | |

Eine Parquet- (oder CSV-)Datei je `--symbol`/`--start`/`--end`, global nach
`ts_exchange_ms` sortiert.

## Aufruf

```bash
# venv aktiv (oder .venv-Python verwenden)
python scripts/export_symbol.py --symbol ETHUSDT --start 2026-06-10 --end 2026-06-16
python scripts/export_symbol.py --symbol ETHUSDT --start 2026-06-15 --end 2026-06-15 \
    --out eth_sample.parquet --peek 5     # --peek: druckt rohe payload_json-Zeilen nach stderr
python scripts/export_symbol.py --symbol ETHUSDT --start 2026-06-15 --end 2026-06-15 --format csv
```
Optionen: `--stream` (Default `publicTrade`), `--exchange` (Default `bybit`),
`--out`, `--format parquet|csv`, `--base-dir` (Default `$KESTREL_DATA_DIR` bzw.
`<repo>/data`), `--peek N`.

## Wichtig: ZWEI payload_json-Formen werden abgedeckt

Der `publicTrade`-Stream enthält je nach Herkunft zwei Formen — der Export
normalisiert beide transparent:

**BACKFILL** (Bybit `public.bybit.com`-CSV-Zeile, EIN Trade je Record):
```json
{"timestamp":"1750000000.000","symbol":"ETHUSDT","side":"Buy","size":"0.10","price":"2500.5","tickDirection":"PlusTick"}
```
→ Keys `side` / `price` / `size`.

**LIVE** (Bybit V5 WS-Nachricht, VIELE Trades je Record unter `data`):
```json
{"topic":"publicTrade.ETHUSDT","ts":1750086400500,
 "data":[{"T":1750086400111,"s":"ETHUSDT","S":"Buy","v":"0.01","p":"2600.1"},
         {"T":1750086400222,"s":"ETHUSDT","S":"Sell","v":"0.02","p":"2600.0"}]}
```
→ Keys `S` / `p` / `v`; die `data`-Liste wird **explodiert** (eine Output-Zeile
je Trade), als Zeit wird das per-Trade-`T` genommen (genauer als das Nachrichten-`ts`).

Feld-Aliase im Exporter: side `S|side`, price `p|price`, size `v|size`,
ts `T|timestamp` (Fallback: `ts_exchange_ms`-Spalte des Records), symbol `s|symbol`
(Fallback: Partition-Symbol).

## Caveat: Backfill+Live-Überlappung an Randdatumen

Ein historischer Tag liegt i.d.R. nur als Backfill vor, ein sehr junger Tag nur
als Live. **Am Übergang** (heutiger Tag: Live gesammelt + später per Backfill
nachgeladen) kann ein Tag BEIDE Formen enthalten → mögliche Doppel-Trades. Für
saubere Fenster: wähle Datumsbereiche, die klar historisch (Backfill) **oder**
klar jung (Live) sind — die Abdeckung je Tag steht im Manifest:

```python
import sqlite3, pandas as pd
con = sqlite3.connect("data/state/harvest_manifest.sqlite")
print(pd.read_sql("""SELECT date, status FROM partitions
    WHERE exchange='bybit' AND stream='publicTrade' AND symbol='ETHUSDT'
      AND status='DONE' ORDER BY date""", con))
```
(Backfill-Tage stehen als DONE im Manifest; Live-only-Tage erscheinen dort
nicht — siehe `state/coverage_matrix.md`.)

## Reales 1-Tages-Sample erzeugen (für den Downstream-Adapter)

```bash
python scripts/export_symbol.py --symbol ETHUSDT --start 2026-06-15 --end 2026-06-15 \
    --out eth_2026-06-15.parquet --peek 5
```
→ liefert das saubere Trades-Parquet **und** druckt 5 rohe `payload_json`-Zeilen
(beide Formen) nach stderr, an denen die `S`/`p`/`v`- bzw. `side`/`price`/`size`-
Extraktion verifiziert werden kann.