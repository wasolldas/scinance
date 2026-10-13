# Antwort Data-Harvest: DVOL-Tageshistorie BTC/ETH ab 2021 (Anfrage vom 2026-10-13)

> Kein Hostname, keine Zugangsdaten in dieser Datei.

## Entscheidung: Variante B (DEC-48)

Der Strom `deribit/dvol` stammt bereits aus genau der vorgeschlagenen
Schnittstelle (`public/get_volatility_index_data`, keyfrei) und wird täglich
fortgeschrieben; er war nur nie weiter als bis 2025-08-01 zurück angesetzt.
Der Thin Client lädt jetzt einmalig **2021-03-24 .. 2025-07-31 für BTC und ETH**
nach — im normalen Archiv-Layout, ohne PC:

```
raw/deribit/dvol/symbol=BTC/date=YYYY-MM-DD/…parquet
raw/deribit/dvol/symbol=ETH/date=YYYY-MM-DD/…parquet
```

- **Auflösung: stündliche OHLC-Kerzen** (24 Zeilen je UTC-Tag, `payload_json`
  = Börsenzeile unverändert) — wie der bestehende Strom ab 2025-08-01. Die
  Tagesreihe ist deren Aggregation (open = erste, close = letzte, high/low =
  Extrema); das ist genau der Weg, den WP-9 auf 176 Überlappungstagen mit
  Differenz 0 gegen den 1D-REST-Backfill geprüft hat.
- Es ist ein REST-Backfill wie der bestehende Strom auch (kein Live-Strom; die
  Live-Sammlung schreibt kein `dvol`).
- Sichtbar in `hd.catalog()` nach dem nächsten Katalog-Export (täglich gegen
  Mittag); `hd.load("dvol", ["BTC", "ETH"], "2021-03-24", "2026-06-30",
  exchange="deribit")`.
- Tage, die Deribit nicht (mehr) liefert, erscheinen als Lücke (`hd.gaps`) —
  nicht interpoliert. Bitte melden, falls am Anfang des Zeitraums Tage fehlen;
  dann legen wir für genau diese die PC-Dateien aus WP-9 als Export nach.

## Variante A bleibt als Notweg vorbereitet

Falls Lücken bleiben: `exports/scinance/INDEX_dvol.json` + Zip, eigener Index,
der Panel-Index (`INDEX.json`) bleibt unberührt — die Ablage unterstützt das
jetzt (DEC-48).
