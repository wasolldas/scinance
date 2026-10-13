# Anfrage an das Data-Harvest-Projekt: DVOL-Tageshistorie BTC/ETH ab 2021 auf den Thin Client (2026-10-13)

> Zweck: Der naechste Scinance-Kandidat H-27 (Volatilitaets-Risikopraemie, DEC-61/DEC-93) braucht die Deribit-DVOL-
> Tagesreihe fuer BTC und ETH ueber beide Urteilsfenster (2024-07-01..2026-06-30) plus Vorperiode ab 2021-03-24.
> Kein Hostname, keine Zugangsdaten in dieser Datei.

## Was fehlt und warum

- Im Harvest-Archiv beginnt `deribit/dvol` am 2025-08-01 (Katalog 2026-10-13: 2 Symbole, bis 2026-10-11). Das deckt das
  erste Urteilsfenster (2024-07..2025-06) nicht ab.
- Die Cloud kann nicht selbst bei Deribit nachladen: `www.deribit.com` wird vom Ausgangs-Proxy der Cloud-Umgebung
  abgewiesen (Organisationsrichtlinie, geprueft 2026-10-13). Der Thin Client ist davon nicht betroffen.
- Auf dem Nutzer-PC liegt der vollstaendige REST-Backfill aus WP-9 (2026-09-09): `data\dvol_rest\BTC_1D.parquet` und
  `data\dvol_rest\ETH_1D.parquet` (je 1.996 Tage, 2021-03-24..2026-09-09; Fingerprints aus dem Fetch-Manifest
  BTC `42574a1a...512b`, ETH `bbdaf089...d786`). WP-9 hat ihn gegen den Harvester-Strom geprueft: auf 176
  Ueberlappungstagen Tagesdifferenz exakt 0 (DEC-61).

## Variante A - sofort, einmalig (wie beim Panel, Data-Harvest DEC-45)

1. Auf dem PC den Ordner `data\dvol_rest` unveraendert (inkl. Manifest-Datei, falls vorhanden) in EINE Datei packen:
   `scinance_dvol_rest_2026-09-09.zip` (wenige hundert KB).
2. Ablage im Bereich `exports/scinance/` unter festem Schluessel, daneben ein EIGENER Index, damit der Panel-Index
   unberuehrt bleibt: `exports/scinance/INDEX_dvol.json` mit `{"file": ..., "bytes": ..., "sha256": ..., "published_utc": ...}`.

Die Cloud liest genau diese zwei Schluessel (kein Listing), prueft Groesse und SHA256, entpackt nur in der Sitzung
(nie in `data/harvest`) und gleicht die Fingerprints oben ab.

## Variante B - alternativ, ohne PC

Der Thin Client holt die Luecke 2021-03-24..2025-07-31 einmalig selbst ueber die oeffentliche Deribit-Schnittstelle
(`GET /api/v2/public/get_volatility_index_data`, `currency=BTC|ETH`, `resolution=1D`, keyfrei) und legt sie im normalen
Archiv-Layout als `deribit/dvol` ab (gekennzeichnet als REST-Backfill, nicht als Live-Strom), sodass `hd.catalog()`
den Zeitraum ab 2021-03-24 zeigt. Der laufende Strom ab 2025-08-01 bleibt unveraendert.

## Empfehlung

A, wenn der PC ohnehin laeuft (Minuten); sonst B. Scinance kann mit beiden arbeiten.
