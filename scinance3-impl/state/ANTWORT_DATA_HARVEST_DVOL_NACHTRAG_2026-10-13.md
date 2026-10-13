# Antwort Data-Harvest: Nachtrag DVOL-Lücken (2026-10-13)

> Kein Hostname, keine Zugangsdaten in dieser Datei.

Eure Lückenliste deckt sich mit unserem eigenen Befund (DEC-49/DEC-50):
je Symbol 202 Tage ohne Daten (2025-09-01 .. 2026-03-19 sowie 2026-08-02/03
und 2026-09-20) und 2026-03-19 mit einem Abruffehler. Ursache war das zu
kurze Nachlade-Fenster der täglichen Wartung bei längeren Ausfällen — kein
Problem der Quelle.

1. **Nachladen:** läuft auf dem Thin Client, gleicher Weg wie der Backfill
   (Stundenkerzen aus `public/get_volatility_index_data`, Archiv-Layout
   `raw/deribit/dvol/symbol=…/date=…`). Sichtbar in `hd.catalog()` nach dem
   nächsten Katalog-Export (täglich gegen Mittag).
2. **Selbstheilend**, ab sofort:
   - die tägliche Wartung plant die letzten **30 Tage** und lädt jeden
     fehlenden Tag nach (vorher 7 — daher die Lücken);
   - Abruffehler werden bis zu 5-mal erneut versucht;
   - lehnt Deribit einen Tag ab, wird er 7 Tage lang täglich neu versucht,
     statt dauerhaft als leer zu gelten.
3. **Nicht lieferbare Tage** bleiben als Lücke stehen (nie interpoliert) und
   erscheinen in `hd.gaps("dvol", ["BTC", "ETH"], …, exchange="deribit")`.
   Nach dem Export ist dort für 2021-03-24 .. heute eine leere Liste
   zu erwarten; bleibt etwas übrig, melden wir es und ihr entscheidet über
   Variante A (WP-9-Dateien bis 2026-09-09).

**BTCUSDT/ETHUSDT-Tagesschlüsse ab 2026-07-01:** dafür ist der Panel-Strom
nicht nötig. Beide Symbole liegen bereits lückengeheilt im Archiv:
Schlusskurs = letzter Trade vor 00:00 UTC aus `bybit/publicTrade`, Funding aus
`bybit/rest.fundingRate`. Für beide gilt dieselbe 30-Tage-Selbstheilung.
Bitte einmal `hd.gaps("publicTrade", ["BTCUSDT", "ETHUSDT"], "2026-07-01", …,
exchange="bybit")` prüfen und Auffälligkeiten melden.
