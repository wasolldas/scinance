# DATASET — Crypto Data Harvester: Projekt & Datensatz-Referenz

> **Zweck dieser Datei:** EIN autarkes Dokument, das ein externes Backtest-Tool
> (oder dessen Agent) lesen kann, um **ohne Vorwissen** zu verstehen, *was*
> gesammelt wird, *wie* es auf der Platte liegt, *wie weit* es zurückreicht und
> *wie* man es liest. Stand-Snapshot: **2026-07-02** (Zahlen ändern sich täglich —
> die *aktuellen* Werte liefert immer die Manifest-Abfrage in §7).
>
> ⚠️ **Gerade läuft ein DEEP-BACKFILL** (2014-01-01 … 2026-03-26, alle Quellen):
> Die historische Tiefe wächst über mehrere Tage von „~3 Monate" auf „volle freie
> Quellen-Historie" (§5). Bis er fertig ist, ist die Abdeckung **im Aufbau** —
> Konsumenten MÜSSEN die tatsächliche Abdeckung per Manifest-Abfrage (§7) prüfen,
> statt Tiefe anzunehmen.
>
> Verwandt: `docs/EXPORT.md` (Trade-Export), `state/coverage_matrix.md`
> (Abdeckungsmatrix), `state/source_registry.md` (Quellen-Detailblätter),
> `CLAUDE.md`/`README.md` (Projekt-Mission).

---

## 1. Was ist das?

Ein **genereller Krypto-Daten-Harvester**, additiv auf der bestehenden
**Kestrel**-Infrastruktur gebaut. Er sammelt **nur kostenlose** Marktdaten in
**zwei Betriebsarten** in **ein** einheitliches, partitioniertes Parquet-Archiv:

- **Backfill** — historische Tagesarchive von Börsen-Bulk-/REST-Quellen.
- **Live** — fortlaufende WebSocket-Sammlung (forward-only, ab Collector-Start).

Beide schreiben in **dasselbe** Schema/Layout und werden über ein **SQLite-
Manifest** idempotent/resume-fähig verwaltet.

---

## 2. Speicher-Layout (Hive-Partitionierung)

Alles liegt unter EINEM Baum (zstd-Parquet), Wurzel = `$KESTREL_DATA_DIR` bzw.
`<repo>/data`:

```
data/raw/<exchange>/<stream>/symbol=<SYM>/date=<YYYY-MM-DD>/<uuid>.parquet
```

- `<exchange>` ∈ `bybit | binance | deribit | bitmex | tardis` (OKX vorbereitet, **disabled**).
- `<stream>` = Datentyp (s. §4), z.B. `publicTrade`, `orderbook`, `rest.fundingRate`.
- `symbol=` und `date=` sind **Hive-Partition-Keys** (von DuckDB/pyarrow automatisch erkannt).
- Eine Partition (`exchange,stream,symbol,date`) kann **mehrere** Parquet-Dateien
  enthalten (Live flusht laufend); die **Kompaktion** faltet sie nächtlich zu
  wenigen großen zusammen — **Schema/Inhalt bleiben identisch**.

Daneben: `data/state/harvest_manifest.sqlite` (Index, §7). **Roh-Archiv & Manifest
sind nicht in git** (`.gitignore: /data/`).

---

## 3. Das EINE Parquet-Schema (alle Quellen, alle Streams)

Jede Parquet-Datei hat **identisch** sechs Spalten:

| Spalte | Typ | Bedeutung |
|---|---|---|
| `ts_local_ns` | int64, not null | Empfangs-/Schreibzeit (ns) — für Live; bei Backfill aus Event-Zeit abgeleitet |
| `ts_exchange_ms` | int64, nullable | **Börsen-Event-Zeit (ms)** ← die für Backtests maßgebliche Zeit |
| `topic` | string | Roh-Topic/Kanal der Quelle |
| `stream` | string | = `<stream>` der Partition |
| `symbol` | string | = `<symbol>` der Partition |
| `payload_json` | string, not null | **Vollständiger Original-Record als JSON** (verlustfrei) |

> **Kernprinzip:** Die *nutzbaren Felder* (Preis, Size, Side, IV, Greeks, …)
> stehen **in `payload_json`** — als quell-spezifisches JSON. Das Schema bleibt
> dadurch über alle Quellen stabil; der Konsument extrahiert die Felder beim
> Lesen (§6, §8). Die `payload_json`-Form je Stream ist in §6 dokumentiert.

---

## 4. Quellen × Streams × Symbole

**Symbol-Universum (USDT-Perp, Bybit-/Binance-Notation):** **BTCUSDT, ETHUSDT,
SOLUSDT, BNBUSDT, XRPUSDT** — alle 5 aktiv in Backfill UND Live (DEC-10, bestätigt
Lauf 9). Deribit nutzt `BTC/ETH` bzw. `BTC-PERPETUAL` etc.

| Quelle (SRC) | exchange | stream(s) | Modus | Symbole |
|---|---|---|---|---|
| SRC-01 | bybit | `publicTrade` | Backfill | 5 Perp |
| SRC-02 | bybit | `orderbook` (L2, bycsi) | Backfill¹ | 5 Perp |
| SRC-03 | bybit | `rest.fundingRate`, `rest.openInterest` | Backfill+Live | 5 Perp |
| SRC-04 | bybit | `orderbook`, `publicTrade`, `tickers`, `allLiquidation`, `insurance` | **Live** | 5 Perp (+ USDC-Optionen für BTC/ETH) |
| SRC-05 | binance | `publicTrade` (aggTrades) | Backfill | 5 Perp |
| SRC-06 | binance | `orderbook` (bookDepth, %-Buckets) | Backfill | 5 Perp |
| SRC-07 | binance | `rest.fundingRate`, `rest.openInterest`, `liquidationSnapshot` | Backfill | 5 Perp |
| SRC-10 | deribit | `publicTrade`, `dvol`, `book_summary` | Backfill | BTC, ETH |
| SRC-11 | deribit | `orderbook`, `publicTrade`, `tickers`, `markprice.options` | **Live** | BTC-PERPETUAL, ETH-PERPETUAL (+ Options-Surface) |
| SRC-12 | bitmex | `publicTrade` | Backfill | XBTUSD |
| SRC-13 | tardis | `options_chain` (+ generalisierte Datatypes) | Backfill | OPTIONS (ganze Chain/Tag) |
| SRC-09 | okx | (Trades/L2) | **DISABLED** (DEC-04, bis SMOKE) | — |
| Paid (P01–P04) | — | Tardis-Perp/Crypto-Lake/Laevitas/CoinGlass | **STUB, disabled** (INV-FREE) | — |

Storage-Ziel je Symbol/Tag: `data/raw/<exchange>/<stream>/symbol=<SYM>/date=<d>/`.
**Optionen-IV** (Deribit `markprice.options` = ganze Surface; Bybit/Deribit per-Strike
`tickers.<OPTION>`) landen als eigene `symbol=<OPTION-INSTRUMENT>`-Partitionen.

> ¹ **Bybit-L2-Backfill (SRC-02) ist im aktuellen Fenster faktisch leer.** Der
> bycsi-Bulk-Endpoint (`quote-saver.bycsi.com/orderbook/linear/...`) liefert für
> 2026-Tage durchweg **HTTP 404** (verifiziert Lauf 9: alle 360 Tage/Symbol → EMPTY);
> freie L2-Tagesarchive existieren dort nur für ältere Zeiträume. **L2 für die 5 Perp
> wird daher vorwärts über Live SRC-04 (`orderbook.1000`) gesammelt**, nicht per
> Backfill. Sobald eine freie Quelle L2 für das Zielfenster führt, re-queued
> `--reset-source SRC-02` die Tage (Adapter unverändert). Siehe DEC-11.

---

## 5. Zeitliche Abdeckung — WIE WEIT ZURÜCK?

**Zwei Schichten:**

1. **Basis-Bestand (fertig, lückenlos):** **2026-03-27 … heute** für alle enabled
   Backfill-Quellen × 5 Symbole (das frühere rollende 3-Monats-Fenster der
   Nachtläufe; wächst täglich nach vorn).
2. **Deep-Backfill (LÄUFT GERADE, Start 2026-07-02):** `--start 2014-01-01
   --end 2026-03-26` über alle Quellen. Er füllt die Historie **rückwärts bis zum
   freien Quellen-Start** auf. Bis „fertig" gilt: Abdeckung je (Quelle, Symbol,
   Stream) **per Manifest prüfen** (§7) — während des Laufs können einzelne Tage
   noch PENDING/FAILED sein, `first_done` kann alt sein, ohne dass dazwischen
   schon alles DONE ist.

**Erwartete End-Tiefe je Quelle** (frühester Tag mit echten Daten; davor liefern
die Quellen korrekt EMPTY):

| Quelle | Stream(s) | Echte Daten ab |
|---|---|---|
| bitmex | publicTrade (XBTUSD) | **2014-11-22** |
| binance | publicTrade, rest.fundingRate | **~2019** (Futures-Start) |
| deribit | publicTrade / dvol | **2019-03-30** / 2021-04-01 |
| bybit | publicTrade, rest.fundingRate | **~2020-07** (BTCUSDT-Listing) |
| tardis | options_chain (IV/Greeks) | **2019**, aber nur **1 Tag/Monat** (Stichproben) |
| binance | orderbook (bookDepth) | **2023-01** |
| bybit | orderbook (bycsi-L2) | s. Fußnote ¹ §4 — für 2026 leer; live forward-only |

**Symbol-Einschränkung:** SOL/BNB/XRP-Perps existieren erst ~**2020-2021** — echte
2019er-Tiefe gibt es nur für **BTC/ETH** (+ BitMEX XBTUSD, Deribit). Frühere Tage
dieser Symbole sind EMPTY (erwartet, kein Fehler).

**Strukturell NICHT rückwirkend verfügbar (frei):** L2-Orderbook vor 2023,
Options-IV-Surface vor Collector-Start (außer Tardis-Monatsstichproben),
Binance-OI älter ~30 Tage.

- **Live-Tiefe:** **forward-only ab Collector-Start** (~2026-06-16): L2-`orderbook`,
  `tickers`, Options-IV (`markprice.options`, per-Strike-`tickers`) wachsen nur
  nach vorn. Ein Always-On-Watchdog (`handoff_local/run_live_forever.*`) hält die
  Sammlung dauerhaft am Laufen.
- **Lücken:** Basis-Bestand: 0. Deep-Backfill-Bereich: erst nach Abschluss
  bewerten (Lücken-Report: `python scripts/harvest_report.py`).

Snapshot-Volumen (2026-06-25, VOR Deep-Backfill): ~**26 GB** (bybit 18,6 /
binance 6,6 / deribit 0,6 / bitmex 0,1). Nach dem Deep-Backfill: **mehrere
hundert GB** (v.a. Trades 2019-2026).

---

## 6. `payload_json`-Referenz je Stream (für Konsumenten)

Die JSON-Form hängt von **Quelle UND Modus** ab. Die wichtigsten:

### `publicTrade` (Trades) — ZWEI Formen!
- **Backfill** (Bybit/BitMEX-CSV, EIN Trade/Record):
  `{"timestamp":"1750000000.0","symbol":"ETHUSDT","side":"Buy","size":"0.10","price":"2500.5",...}`
  → Keys `side` / `price` / `size`.
- **Live** (Bybit V5 WS, VIELE Trades/Record):
  `{"topic":"publicTrade.ETHUSDT","ts":...,"data":[{"T":...,"s":"ETHUSDT","S":"Buy","v":"0.01","p":"2600.1"},...]}`
  → Keys `S`/`p`/`v`/`T`; **`data`-Liste explodieren** (1 Output-Trade je Element).
- **Binance** (aggTrades): `{"a":aggId,"p":price,"q":qty,"T":ms,"m":isBuyerMaker,...}` (Side aus `m`).
- → Nutze **`scripts/export_symbol.py`** (§8) — es normalisiert ALLE diese Formen
  zu `ts_exchange_ms|side(Buy/Sell)|price|size|symbol`.

### `orderbook` (L2)
- **Bybit (bycsi-Backfill UND Live):** roher WS-Stream — **Snapshot + inkrementelle
  Deltas** als JSON je Record (`{"topic":"orderbook.1000.BTCUSDT","type":"snapshot|delta","data":{"b":[[price,size],...],"a":[...],"u":updateId,"seq":...},"ts":...}`).
  **KEIN fertiges Tiefenbild** — Deltas anwenden (size=0 ⇒ Level löschen). Rekonstruktion
  ist **nutzerseitig** (Katalog-Vorgabe).
- **Binance (`orderbook`/bookDepth):** prozentbasierte Buckets um den Mid —
  `{"timestamp":"2026-06-15 00:00:04","percentage":"-5.00","depth":"...","notional":"..."}`
  (Datums-String, KEINE Levels-by-Price).

### `rest.fundingRate` / `rest.openInterest`
- Bybit V5: `{"symbol":...,"fundingRate":"0.0001","fundingRateTimestamp":"...ms"}` bzw.
  `{"openInterest":"...","timestamp":"...ms"}`. Binance via ccxt: ccxt-normalisierte Dicts.

### `tickers` (Live, Funding/Mark/Index/OI; für Optionen IV/Greeks/OI)
- Bybit V5 WS ticker-Snapshot/-Delta; für USDC-Optionen mit `markIv`,`delta`,`gamma`,`vega`,`theta`,`openInterest`,`underlyingPrice` etc.

### `markprice.options` (Deribit Live) — **ganze IV-Surface in einem Stream**
- `{"params":{"channel":"markprice.options.btc_usd","data":[{"instrument_name":"BTC-...-C","mark_iv":...,"iv":...},...]}}` → pro Tick die Mark-IV aller aktiven Strikes.

### `dvol` (Deribit Volatilitätsindex), `book_summary` (Deribit Mark-IV/OI/Greeks der laufenden Instrumente), `allLiquidation`, `insurance`, `liquidationSnapshot`
- Jeweils das Roh-JSON der Quelle (Felder s. Börsen-Doku); verlustfrei in `payload_json`.

### `options_chain` (Tardis, `symbol=OPTIONS`)
- Eine Tagesdatei = ALLE Options-Instrumente: Strike, Expiry, Typ (C/P), Bid/Ask,
  Mark-IV, Bid/Ask-IV, Greeks (Δ/Γ/V/Θ/ρ), Underlying, OI. Roh-CSV-Zeile je Record.

---

## 7. Manifest & Coverage-Abfrage

`data/state/harvest_manifest.sqlite`, Tabelle `partitions`
(PK `exchange,stream,symbol,date`), Status:
`DONE` (geladen) · `EMPTY` (404/kein-Daten-Tag, terminal) · `FAILED` (Fehler;
< max_attempts wird wiederholt) · `PENDING`/`RUNNING`.

**Wichtig:** **Live-only-Partitionen** (z.B. Optionen-Ticker) stehen **NICHT** im
Manifest — nur Backfill-Partitionen. Live-Tage findest du auf der Platte.

**Aktuelle Abdeckung (first/last DONE je Symbol+Stream):**
```python
import sqlite3, pandas as pd
con = sqlite3.connect("data/state/harvest_manifest.sqlite")
print(pd.read_sql("""
  SELECT exchange, stream, symbol,
         SUM(status='DONE') AS done_days,
         MIN(CASE WHEN status='DONE' THEN date END) AS first_done,
         MAX(CASE WHEN status='DONE' THEN date END) AS last_done
  FROM partitions GROUP BY exchange, stream, symbol
  HAVING done_days > 0 ORDER BY exchange, stream, symbol
""", con).to_string(index=False))
```
`done_days == (last_done − first_done + 1)` ⇒ lückenlos. **Während des laufenden
Deep-Backfills ist genau DIESE Prüfung Pflicht**: `first_done` kann bereits 2019
sein, während mittlere Tage noch PENDING/FAILED sind — für Backtests nur Fenster
nutzen, in denen die Gleichung aufgeht (oder EMPTY-Tage bewusst mitzählen:
`SUM(status IN ('DONE','EMPTY'))` gegen die Spanne). Lücken-/Integritätsbericht:
`python scripts/harvest_report.py` → Markdown.

---

## 8. Daten konsumieren

### Trades (empfohlener Pfad) — `scripts/export_symbol.py`
Flacht beide Trade-Formen + Side-Normalisierung in eine saubere Tabelle ab
(`ts_exchange_ms|side|price|size|symbol`, 1 Zeile/Trade, sortiert). Read-only,
braucht nur `pyarrow`:
```bash
python scripts/export_symbol.py --symbol ETHUSDT --start 2026-06-10 --end 2026-06-16 --out eth.parquet
```
Details + Caveats: `docs/EXPORT.md`.

### Beliebiger Stream — direkt mit DuckDB/pyarrow
```python
import duckdb
df = duckdb.sql("""
  SELECT ts_exchange_ms,
         json_extract_string(payload_json,'$.fundingRate') AS funding
  FROM read_parquet('data/raw/bybit/rest.fundingRate/symbol=ETHUSDT/**/*.parquet',
                    hive_partitioning=1)
  WHERE date BETWEEN '2026-04-01' AND '2026-06-16'
  ORDER BY ts_exchange_ms
""").df()
```
`hive_partitioning=1` liefert `symbol`/`date` als Spalten. Für L2 (`orderbook`)
musst du Snapshot+Deltas selbst rekonstruieren (s. §6/§9).

---

## 9. Wichtige Caveats (für Backtest-Korrektheit)

1. **L2-`orderbook` ist roh** (Snapshot + Deltas), kein Tiefenbild — Rekonstruktion
   nutzerseitig (size=0 ⇒ Level löschen; `u`/`seq` für Reihenfolge).
2. **Trades: zwei `payload`-Formen** (Backfill flach vs. Live `data[]`-Liste) — der
   Export deckt beide ab; bei Direktzugriff beachten.
3. **Side** wird vom Export auf `Buy`/`Sell` normalisiert (historisch gab es `BUY`/`SELL`).
4. **Backfill/Live-Überlappung** an Randdatumen (ein Tag kann beide Formen enthalten
   ⇒ mögliche Doppel-Trades) — saubere Fenster wählen (§5/§7).
5. **Zeit:** Für Event-Zeit `ts_exchange_ms` (bzw. per-Trade `T` bei Live) nutzen,
   NICHT `ts_local_ns` (Empfangszeit).
6. **Binance-OI** nur ~30 Tage Historie; **bycsi-L2** hat Publish-Lag (jüngste Tage
   404 ⇒ EMPTY). Edge-Date `2026-03-19` FAILED = vor Verfügbarkeit (erwartet).
6b. **Deep-Backfill im Aufbau (ab 2026-07-02):** Tiefe je Serie erst nach der
   Lückenprüfung aus §7 als backtest-tauglich behandeln. EMPTY vor dem Listing-/
   Quellen-Start (§5-Tabelle) ist erwartet und kein Datenfehler.
7. **Optionen-Partitionen sind stark fragmentiert** (viele kleine Dateien) bis die
   Kompaktion sie eingeholt hat — Trades/Perp-Streams sind davon unberührt.
8. **Immutabilität/Idempotenz:** Tagesarchive sind unveränderlich; ein Tag wird nie
   doppelt geladen. Kompaktion ändert nur Dateigröße/-anzahl, nie Inhalt/Schema.

---

## 10. Betrieb & Reproduzierbarkeit

- **Backfill:** `python scripts/harvest_backfill.py [--source SRC-xx] [--symbol]
  [--days N | --start YYYY-MM-DD --end YYYY-MM-DD] [--dry-run]` — idempotent/
  resume-fähig (DONE/EMPTY wird übersprungen; Abbruch ⇒ einfach neu starten).
- **Live (dauerhaft):** Always-On-Watchdog `handoff_local/run_live_forever.{ps1,sh}`
  (Auto-Restart, Autostart via `install_live_startup.ps1`); einzeln:
  `python scripts/harvest_live.py [--duration SEC]`.
- **Validierung:**
  - `python scripts/check_health.py` — läuft der Collector? (In-Memory-Snapshot)
  - `python scripts/check_live.py [--json]` — landen frische, **valide** Parquet
    auf der Platte? (Live schreibt am Manifest vorbei; dieses Tool scannt das
    Archiv direkt. Exit 0/1/2/3 = ok/kein Archiv/stale/invalide.)
  - `python scripts/harvest_report.py [--schema-check-sample N]` — Backfill-
    Integrität (Lücken, FAILED, Schema-Drift) aus dem Manifest.
- **Kompaktion:** `python scripts/harvest_compact.py --days-old 1 [--max-seconds N]`
- **Recovery nach Fix:** `python scripts/harvest_backfill.py --reset-source SRC-xx`
  (setzt DONE/EMPTY/FAILED → PENDING).
- **Ein-Befehl-Nachtlauf** (alles, resume-fähig): `handoff_local/run_overnight.{sh,ps1}`
  → `handoff_local/results/SUMMARY_<datum>.md`.
- **Netz-Politik:** Rate-Limits je Quelle in `config/harvester.yaml`; 403/429/5xx
  werden mit Backoff wiederholt (403 von public.bybit.com = WAF-Rate-Limit, kein
  fehlender Tag — DEC-12).
- **Umgebung:** Python 3.11/3.12, venv unter `.venv` (Deps: pyarrow/duckdb/httpx/
  websockets/ccxt/zstandard/polars). Standalone-Skripte immer mit dem **venv-Python**
  laufen lassen.

**Stand/Reports:** `state/morning_report.md`, `state/coverage_matrix.md`,
`state/smoke_checklist.md`; Entscheidungen `state/decisions.md` (DEC-01…12);
offene Punkte `state/open_questions.md`.