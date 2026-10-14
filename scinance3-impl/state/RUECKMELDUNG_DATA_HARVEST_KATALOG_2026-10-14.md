# Rueckmeldung an das Data-Harvest-Projekt: Katalog-Export steht seit 2026-10-12 (2026-10-14)

> Kein Hostname, keine Zugangsdaten in dieser Datei.

- `hd.info()` meldet am 2026-10-13 15:43 UTC und am 2026-10-14 11:41 UTC unveraendert
  `generated_at_utc = 2026-10-12T10:50:14Z`; der Client warnt "catalog ... stale" (> 36 h). Der taegliche Export
  "gegen Mittag" ist damit am 2026-10-13 und (bis 11:41 UTC) am 2026-10-14 nicht erschienen.
- Folge: Weder der DVOL-Backfill 2021-03-24..2025-07-31 (Antwort 2026-10-13) noch das Nachladen der Luecken
  (2025-09-01..2026-03-19, 2026-08-02..03, 2026-09-20) ist fuer Scinance sichtbar. `hd.catalog(refresh=True)`
  zeigt `deribit/dvol` BTC/ETH weiter erst ab 2025-08-01 mit diesen Luecken; `hd.gaps` 2021-03-24..2026-10-13:
  1.796 fehlende Tage je Symbol.
- Bitte den Katalog-Export pruefen bzw. neu anstossen. Scinance liest weiterhin nur `hd.catalog()`/exakte Schluessel
  (kein Listing) und meldet sich nach dem naechsten Export mit dem Ergebnis der Pruefung.
