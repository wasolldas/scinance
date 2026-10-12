# Antwort Data-Harvest: Bybit-Tagespanel (Anfrage vom 2026-10-10)

> Kein Hostname, keine Zugangsdaten in dieser Datei. Zugang wie bisher über die
> Secrets `HARVEST_S3_*` der Umgebung.

## Variante A — umgesetzt (DEC-45)

Der Datendienst hat einen neuen, nur lesenden Bereich `exports/` im Bucket
`harvest`. Nach der Veröffentlichung durch den Betreiber liegen dort:

| Schlüssel | Inhalt |
|---|---|
| `exports/scinance/INDEX.json` | `{"file": ..., "bytes": ..., "sha256": ..., "published_utc": ...}` |
| `exports/scinance/scinance_panel_1d_2026-09-28.zip` | `panel_1d/` + `panel_1d_delisted/` unverändert (inkl. `panel_manifest.sqlite`) |

Lesen genau wie angefragt — erst `INDEX.json`, dann die dort genannte Datei,
Größe und SHA256 prüfen, kein Listing:

```python
import hashlib, json
idx = json.loads(s3.open_input_stream("harvest/exports/scinance/INDEX.json").read())
body = s3.open_input_stream(f"harvest/exports/scinance/{idx['file']}").read()
assert len(body) == idx["bytes"] and hashlib.sha256(body).hexdigest() == idx["sha256"]
```

Zusagen und Regeln:

- **Dateinamen sind unveränderlich.** Eine neuere Panel-Version bekommt einen
  neuen Namen (Datum im Namen); nur `INDEX.json` zeigt jeweils auf die neueste.
  Ältere Versionen bleiben liegen.
- Passen Größe oder SHA256 nicht: ~15 s warten und erneut lesen
  (Cache-Fenster des Dienstes direkt nach einer Veröffentlichung).
- `exports/` ist für alle Projektschlüssel lesbar (öffentliche Marktdaten,
  wie `raw/`). Nichts Vertrauliches hineinlegen.
- Bei ~2 MB/s geteilter Bandbreite: einmal laden, lokal in der Sitzung
  entpacken (nie in `data/harvest`), wie in der Anfrage vorgesehen.

## Variante B — Vorschlag, noch nicht gebaut

Grundsätzlich ja: Der Thin Client erreicht Bybit (Deutschland, keine
Geosperre). Drei Abweichungen vom Vorschlag:

1. **Delistete Symbole bleiben in der Zip aus A.** Ihre Historie ändert sich
   nie mehr; ein Nachladen über die API ist unnötig (und für delistete Symbole
   nicht sicher verfügbar). B deckt nur die aktiven USDT-Perps ab — inklusive
   Backfill ab Listing.
2. **Eine Partition je Tag mit allen Symbolen**, nicht je Symbol und Tag:
   ~877 Symbole × ~1.800 Tage wären ~1,6 Mio Mini-Partitionen (der ganze
   Katalog hat heute ~312k). Geplant: `bybit/rest.kline1d/symbol=ALL/date=…`
   und `bybit/rest.instruments/symbol=ALL/date=…` (Tagesschnappschuss).
3. **Funding aller Perps als eigener Strom**, nicht in `bybit/rest.fundingRate`
   gemischt (dort liegen die 5 Majors je Symbol — sonst entstünden Dubletten
   und zwei Partitionsschemata in einem Strom).

Wie überall im Archiv steht die Börsenantwort unverändert in `payload_json`;
`panel_1d` (OHLCV, turnover, funding_sum/funding_n) leitet Scinance daraus ab.
Bis B läuft, deckt die Zip aus A alles bis 2026-09-28 ab — für WP-13 genügt das.
