# Antwort Data-Harvest: Katalog-Stillstand + `bybit/publicTrade`-Metadaten (2026-10-14)

> Bezug: Rückmeldungen KATALOG (2026-10-14) und PUBLICTRADE (2026-10-13). Danke für die genaue Prüfung.
> Kein Hostname, keine Zugangsdaten in dieser Datei.

## 1. Katalog seit 2026-10-12 nicht erneuert — behoben (DEC-52)

Die tägliche Wartung kam am 13./14.10. nicht bis zum Katalog-Export: Die
Schritte davor hatten keine Zeitgrenze (Rückstand an Kompaktierung seit
06.10., erstes 30-Tage-Nachladen), und die Unit wird nach 8 h beendet. Jetzt
hat jeder lange Schritt eine Obergrenze und der Export eine feste Reserve — er
läuft jeden Tag. Ein Export wird heute zusätzlich von Hand angestoßen; danach
sind DVOL ab 2021-03-24 und alle geschlossenen Lücken sichtbar. Bitte dann wie
angekündigt `hd.gaps` prüfen.

## 2. `bybit/publicTrade` — eure sechs Befunde

Ursache von 1–4 ist das bekannte Doppel-Schreiben aus DEC-18 (C1): Live-Sammlung
und Archiv-Nachlader schreiben in dieselbe Partition. Bei Deribit-Instrumenten
gab es dagegen längst eine Sperre, bei Bybit nicht.

| # | Befund | Ursache | Stand |
|---|---|---|---|
| 1 | EMPTY/0 trotz Datei | Börsenarchiv beim Abruf noch nicht veröffentlicht → „leer"; die Partition enthält **nur Live-Daten** (vollständig im Sinne der Aufzeichnung) | Status wird auf DONE mit echter Zeilenzahl korrigiert |
| 2 | `rows` < Datei | Manifest zählt nur die Archiv-Trades; die Datei enthält zusätzlich die Live-Frames **derselben** Trades (Doppel in zwei Formaten) | Ursache abgestellt: der Nachlader überspringt ab sofort Tage mit Live-Daten |
| 3 | `status = null` | Wartungsausfall, keine Manifest-Zeile; Live-Daten vorhanden | wird als DONE registriert |
| 4 | RUNNING, ~1,5× Größe | Archiv-Nachladen mitten im Schreiben abgebrochen → Live + Archiv in einer Partition | nächster Wartungslauf schließt ihn ohne erneutes Nachladen ab (DONE); inhaltlich wie Befund 2 behandeln |
| 5 | 582 s Pause 2026-10-08 | sehr wahrscheinlich Aufzeichnungslücke der Live-Sammlung (Reconnect) | siehe unten |
| 6 | 2026-08-13 doppelt | bekannt, Client dedupliziert | unverändert |

**Was das für eure Tagesschlüsse heißt:** Der letzte Trade vor 00:00 UTC ist
in beiden Formaten derselbe — Doppel ändern den Schlusskurs nicht. Für
Volumen/Trade-Zahlen auf gemischten Tagen nur **eine** Herkunft nehmen:
Archiv-Zeilen haben `trdMatchID`/`side`/`size` flach, Live-Zeilen sind
WS-Frames mit `data[]` (je Frame mehrere Trades). Ab sofort entstehen keine
gemischten Tage mehr.

**Zu Befund 5:** In dieselbe Partition nachfüllen würde wieder Doppel erzeugen.
Für den Tagesschluss ist eine Pause mitten am Tag ohne Bedeutung. Wenn ihr
lückenlose Trades für volle Tage braucht, wäre der saubere Weg ein eigener
Strom mit den Archiv-Trades (getrennt von Live) — bitte melden, dann planen wir
ihn ein. Ebenso bleibt das Tages-Panel (Variante B) vorgemerkt.
