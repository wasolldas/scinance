# Rueckmeldung an das Data-Harvest-Projekt: `bybit/publicTrade` BTCUSDT/ETHUSDT ab 2026-07-01 (2026-10-13)

> Bezug: Antwort "Nachtrag DVOL-Luecken" vom 2026-10-13, Bitte um `hd.gaps`-Pruefung. Danke fuer Nachladen und
> 30-Tage-Selbstheilung - angenommen. Kein Hostname, keine Zugangsdaten in dieser Datei.
> Scinance hat nur Vollstaendigkeit geprueft (Katalog, Parquet-Fuss, Zeitstempel `ts_exchange_ms`); Preise wurden
> bewusst nicht gelesen (Blind-Siegel fuer ein kuenftiges Urteilsfenster).

## Ergebnis (Katalog-Export 2026-10-12 10:50 UTC, Zeitraum 2026-07-01 .. 2026-10-12)

`hd.gaps("publicTrade", ["BTCUSDT", "ETHUSDT"], "2026-07-01", "2026-10-12", exchange="bybit")`: **leer** - jeder Tag hat
eine Partition. Auffaellig sind nur Katalog-Metadaten:

| # | Befund | Tage | Beleg |
|---|---|---|---|
| 1 | `status = EMPTY` und `rows = 0`, obwohl Dateien mit Daten vorliegen | BTCUSDT 33, ETHUSDT 34 Tage, 2026-08-19 .. 2026-10-10 (kompaktiert und nicht kompaktiert) | z. B. BTCUSDT 2026-10-08: Katalog EMPTY/0, Parquet-Fuss 849.477 Zeilen, Zeitstempel 00:00:00 .. 23:59:58 |
| 2 | `rows` im Katalog kleiner als die Zeilen in der Datei | z. B. BTCUSDT 2026-09-15: Katalog 2.828.624, Fuss 3.691.889 | - |
| 3 | `status = null` bei geschlossenen Tagen mit Daten | 2026-08-02, 2026-08-03 (beide Symbole; dieselben Tage wie die DVOL-Luecke) | 10-50 MB je Tag |
| 4 | `status = RUNNING` bei geschlossenem Tag | ETHUSDT 2026-09-21 (123 MB, etwa 1,5x ueblich) | - |
| 5 | Handelspause innerhalb eines Tages | BTCUSDT 2026-10-08: groesster Abstand zwischen zwei Trades 582 s (sonst 15-20 s) - moeglicher Aufzeichnungsausfall | Zeitstempel |
| 6 | `duplicate_rows` (bekannt, Client dedupliziert) | 2026-08-13 beide Symbole | Flag |

Laut `DATA_ACCESS.md` ist der Katalog-`status` heute massgeblich (EMPTY-Korrektur DEC-32) - Befund 1 widerspricht dem.
Bitte pruefen, ob Status/Zeilenzahl der Wartung nach dem Kompaktieren bzw. nach dem 30-Tage-Nachladen neu geschrieben
werden, und ob Befund 5 eine Luecke im Mitschnitt ist (dann waere sie per REST-Nachladen schliessbar?).

## Wofuer Scinance die Daten braucht
Tagesschluesse BTCUSDT/ETHUSDT (letzter Trade vor 00:00 UTC) ab 2026-07-01 fuer ein blindes H-27-Urteilsfenster.
Das Datenvolumen ist dafuer gross (~73-82 MB je Symbol und Tag, ~28 GB je Symbol und Jahr bei ~2 MB/s): eine kompakte
Tagesschluss-Reihe (z. B. aus dem geplanten Panel-Strom, Variante B) waere weiterhin willkommen, ist aber nicht dringend.
