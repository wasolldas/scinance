# Anfrage an das Data-Harvest-Projekt: Bybit-Tagespanel auf den Thin Client (2026-10-10)

> Zweck: Scinance rechnet ab jetzt vollstaendig in der Cloud-Sitzung und holt alle Daten vom Thin Client
> (Nutzer-Auflage 2026-10-10, DEC-83). Einziges fehlendes Datenstueck ist das Bybit-Tagespanel.
> Kein Hostname, keine Zugangsdaten in dieser Datei.

## Was fehlt und warum

- WP-7, WP-10(A2), WP-12 und WP-13 (A3-Kohorte H-28..H-30) rechnen auf `panel_1d`: Tageskerzen (open/high/low/close,
  volume, turnover) und Funding je Tag (`funding_sum`, `funding_n`) fuer **alle Bybit-USDT-Perps seit 2021**,
  877 laufende + 261 delistete Symbole (`panel_1d_delisted`). Liegt heute nur auf dem Nutzer-PC (`data\panel_1d`,
  `data\panel_1d_delisted`).
- Im Harvest-Archiv gibt es Bybit-Perps nur fuer BNB/BTC/ETH/SOL/XRP.
- Die Cloud kann das Panel nicht selbst bei Bybit holen: Bybit sperrt die Cloud-Region per CloudFront-Geosperre
  ("configured to block access from your country"); das ist keine Allowlist-Frage. Der Thin Client (Deutschland)
  ist davon nicht betroffen.

## Variante A - sofort, einmalig (reicht fuer WP-13 vollstaendig)

Die Urteilsfenster von WP-13 enden 2026-06-30; das vorhandene PC-Panel (Stand 2026-09-28) deckt sie ab.

1. Auf dem PC beide Ordner unveraendert in EINE Datei packen: `data\panel_1d` und `data\panel_1d_delisted`
   (inkl. `panel_manifest.sqlite`) -> `scinance_panel_1d_2026-09-28.zip` (geschaetzt einige 10 MB).
2. Datei in das vom Thin Client bereitgestellte Archiv legen, fester Schluessel:
   `exports/scinance/scinance_panel_1d_2026-09-28.zip` (Bucket `harvest`).
3. Daneben `exports/scinance/INDEX.json` mit `{"file": ..., "bytes": ..., "sha256": ...}`.

Die Cloud liest genau diese zwei Schluessel (kein Listing), prueft Groesse und SHA256 und entpackt lokal in der
Sitzung (nie in `data/harvest`). Ein Download dauert bei ~2 MB/s unter einer Minute.

## Variante B - dauerhaft (Panel bleibt aktuell, PC ganz raus)

Taeglicher kleiner REST-Job auf dem Thin Client (Bybit v5, oeffentlich, keyfrei; einige hundert KB pro Tag):

| Strom | Endpunkt | Inhalt |
|---|---|---|
| `bybit/rest.instruments` | `GET /v5/market/instruments-info?category=linear` | Universum inkl. `launchTime`, `deliveryTime`, `status`, `fundingInterval`, `upperFundingRate` (taeglicher Schnappschuss) |
| `bybit/rest.kline1d` | `GET /v5/market/kline?category=linear&interval=D` | Tageskerze je Symbol |
| `bybit/rest.fundingRate` (bestehender Strom, auf alle Perps erweitern) | `GET /v5/market/funding/history?category=linear` | jede Abrechnung je Symbol |

Einmaliger Backfill ab Listing (2020/2021) fuer alle Symbole, die je gelistet waren (die delistete Liste stammt aus
dem Bybit-Announcements-Index, `GET /v5/announcements/index`; Scinance kann die 261 Namen liefern). Ablage im
normalen Archiv-Layout, damit `hd.catalog()`/`hd.load()` es finden.

## Empfehlung

A jetzt (entsperrt WP-13 heute), B als dauerhafte Loesung im Data-Harvest-Projekt.
