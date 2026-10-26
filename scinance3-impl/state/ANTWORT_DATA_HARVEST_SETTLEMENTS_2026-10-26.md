# Antwort Data-Harvest (ueber den Nutzer, 2026-10-26): Options-Deliveries im Strom `deribit/rest.settlements` ab 2026-08-01

> Wiedergabe der Antwort; kein Hostname, keine Zugangsdaten.

- **Keine Luecke des Sammlers, sondern eine Eigenschaft der Deribit-API:** `get_last_settlements_by_currency`
  (`type=delivery`) meldet seit **2026-08-01** keine Options-Deliveries mehr, nur noch Future-Deliveries.
- **Geprueft:** beim Blaettern ab "jetzt", mit `search_start_timestamp` und in Tagesfenstern an Verfallstagen
  (2026-08-28, 09-25, 10-16, 10-23: je 0 Optionen). Bis 2026-07-31 sind API und Archiv identisch; ein Reparaturlauf
  ueber die ganze Historie fand nichts Fehlendes.
- **Ersatz ab August 2026** (fuer Verfallskalender und Settlement-Preise der Optionen):
  1. `deribit/rest.instruments` (taeglich; am Tag verfallene Optionen),
  2. `deribit/rest.deliveryPrices` (taeglich, 08:00 UTC),
  3. `deribit/tickers` (Instrumentnamen mit Verfallstag und `settlement_price`).

## Folgen fuer Scinance (Orchestrator)
- Der A2-Ereigniszensus (DEC-98 N5) bleibt bis 2026-07-31 vollstaendig; fuer Tage ab 2026-08-01 ist die Ereignismenge
  der Optionsverfaelle aus `rest.instruments` (verfallene Instrumente je Tag) bzw. `rest.deliveryPrices` (Datum) zu
  zaehlen, die Zeitlage (08:00 UTC) aus den Future-Deliveries und den taeglichen Settlements. Nur Zaehlungen; Blind-
  Siegel DEC-96 E3 (keine BTC/ETH-Statistik ab 2026-07-01) unberuehrt.
- Keine Rueckfrage mehr offen. Kein Nachladen noetig.
