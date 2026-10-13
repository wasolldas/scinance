# Nachtrag zur DVOL-Anfrage an das Data-Harvest-Projekt (2026-10-13)

> Bezug: Antwort vom 2026-10-13 (Variante B, Backfill 2021-03-24..2025-07-31). Danke - angenommen (Scinance DEC-95).
> Kein Hostname, keine Zugangsdaten in dieser Datei.

Beim Pruefen des Katalogs (Export 2026-10-12 10:50 UTC) fehlen im bestehenden Strom `deribit/dvol` fuer BTC UND ETH
zusaetzlich diese Tage:

| Luecke | Tage | Prioritaet fuer Scinance |
|---|---:|---|
| 2026-08-02 .. 2026-08-03 | 2 | **hoch** - liegt im kuenftigen Urteilsfenster von H-27 (ab 2026-07-01) |
| 2026-09-20 | 1 | **hoch** - dito |
| 2025-09-01 .. 2026-03-19 | 200 | mittel - fuer eine durchgehende Reihe (Beschreibung, nicht urteilstragend) |

Bitte:
1. Diese Tage auf dieselbe Weise wie den Backfill nachladen (Stundenkerzen aus `public/get_volatility_index_data`,
   Archiv-Layout `raw/deribit/dvol/symbol=.../date=...`), sodass `hd.catalog()` sie fuehrt.
2. Den taeglichen DVOL-Job selbstheilend machen: fehlende Tage der letzten N Tage beim naechsten Lauf per REST
   nachholen (Scinance wertet ab 2026-07-01 ein blindes Fenster ueber 12-24 Monate aus; jede Luecke dort fehlt im
   Urteil, sie wird nie interpoliert).
3. Falls Deribit einzelne Tage nicht mehr liefert: als Luecke stehen lassen und kurz melden (dann ggf. Variante A mit
   den WP-9-PC-Dateien fuer die Zeit bis 2026-09-09).

Gleiches gilt sinngemaess fuer den kuenftigen taeglichen Panel-Strom (Variante B des Panel-Auftrags): Scinance braucht
daraus BTCUSDT/ETHUSDT-Tagesschluesse ab 2026-07-01 lueckenlos.
