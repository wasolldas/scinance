# H-27 - Stufe 1a: Datenprobe (C.8) - Quellen, Konventionen, Abdeckung

> ENTWURF der Herleitung, Stand 2026-10-13. Nichts hier ist registriert. Ergebnisblindheit nach `KONTAMINATION.md`
> Abschnitt 5. Skripte unter `scratchpad/h27_herleitung/` (sha256 in `feasibility.json`).

## A. Datenunabhaengiger Teil (vor der Katalog-Abdeckungspruefung festgelegt)

### A.1 IV-Quelle (DEC-61, DEC-95)

- `deribit/dvol`, Symbole `BTC`, `ETH`, Stundenkerzen (OHLC) aus `public/get_volatility_index_data`, 24 Zeilen je
  UTC-Tag, `payload_json` = Boersenzeile unveraendert (Antwort Data-Harvest 2026-10-13). Backfill 2021-03-24..2025-07-31
  und laufender Strom ab 2025-08-01 aus derselben Schnittstelle -> EINE Quelle (DEC-61 "nicht mischen"); die
  Gleichheit von Format und Konvention wird in Teil B an der Naht 2025-07-31/2025-08-01 geprueft (nur Gleichheits-/
  Stetigkeitspruefung, keine Niveauausgabe).
- **Tagesschluss IV(t) = close der letzten Stundenkerze des UTC-Tages t** (Kerze 23:00-24:00 UTC), also der DVOL-Wert
  um 24:00 UTC. Begruendung: (i) WP-9 hat auf 176 Tagen gezeigt, dass der 1D-REST-Close exakt der letzte DVOL-Wert des
  UTC-Tages ist (DEC-61) - die Tageskerze ist die Aggregation der Stundenkerzen mit close = close der letzten; (ii) der
  Wert gehoert zur Partition des Tages t (kein Rueckgriff auf die Partition t+1, robust gegen einen fehlenden
  Folgetag); (iii) er faellt zeitlich mit dem Tagesschluss der Preisquelle zusammen (A.2). Der open der Folgestunde
  (00:00 von t+1) ist derselbe Zeitpunkt; die Gleichheit close(23h, t) = open(00h, t+1) wird in Teil B als
  Stetigkeitspruefung gezaehlt (Anteil gleicher Paare, keine Niveaus). Fehlt die 23h-Kerze, ist IV(t) fehlend
  (benannt, nie interpoliert, nie durch eine fruehere Stunde ersetzt).

### A.2 RV-Quelle (festgelegt aus dem Katalog, Export 2026-10-12 10:50 UTC, lokal gelesen, kein Download)

| Kandidat | Underlying | Abdeckung im Katalog | Volumen BTC+ETH 2021-03-24..2026-07-31 | Urteil |
|---|---|---|---|---|
| `deribit/publicTrade` BTC-PERPETUAL/ETH-PERPETUAL | gleiches Venue wie DVOL (Perp auf den Deribit-Index) | erst ab 2025-08-01 | - | deckt weder Vorperiode noch W1 -> verworfen |
| `bybit/publicTrade` BTCUSDT/ETHUSDT | Bybit-Perp | ab 2020-03-25 | ~58,5 GB (bis 2024-05-31) + ~124,6 GB (2024-06-01..2026-07-31) = ~183 GB -> ~25 h bei 2 MB/s (geteilt) | nicht vertretbar (Regel 2, DATA_ACCESS 5) |
| `binance/publicTrade` | Binance-Spot/Perp | ab 2025-01-01 | - | verworfen |
| kompakte Kerzen-/Index-Stroeme | - | **keine im Katalog** (Stroeme: orderbook, publicTrade, tickers, funding, OI, liquidations, insurance, dvol, markprice.options, options_chain) | - | nicht vorhanden |
| **Union-Panel `panel_1d` BTCUSDT/ETHUSDT** (Harvest-Export 2026-09-28, DEC-84) | Bybit-Linear-Perp, Tageskerzen (start_ms 00:00 UTC, OHLC, Volumen, Funding) | 2021-01-01..2026-09 | wenige KB, bereits in der Sitzung | **gewaehlt (Rueckfall laut Auftrag)** |

- **RV-Schaetzer (primaer):** `RV_fwd30(t) = 100 * sqrt( (365/30) * sum_{k=1..30} r_{t+k}^2 )`, `r_s = ln(C_s / C_{s-1})`
  aus Tagesschluessen `C_s` (close der Bybit-Tageskerze des UTC-Tages s, also 24:00 UTC). Ohne Mittelwertabzug: die
  Summe quadrierter Renditen ist fuer die quadratische Variation erwartungstreu (Drift auf Tagesbasis vernachlaessigbar);
  damit ist die Varianz-Praemie (S2) im Nullfall frei von Schaetzer-Jensen, die Vol-Praemie (S1) nicht (Nullwelt in
  `FEASIBILITY.md`). Ziel-Intervall (t, t+30] beginnt genau zum Zeitpunkt der IV-Beobachtung (24:00 UTC von t) und
  umfasst 30 Kalendertage = die 30-Tage-Laufzeit des DVOL.
- **Annualisierung:** EINE gemeinsame Konstante 365 Tage/Jahr (24/7), dieselbe wie `wp10_coherence.rv.
  ANNUALIZATION_DAYS_PER_YEAR`; DVOL wird von Deribit bereits annualisiert veroeffentlicht und nicht umgerechnet
  (DVOL-Day-Count 365 [sek], wie in `rv.py` vermerkt).
- **Fehlende Tage:** fehlt einer der 31 Schluesse C_t..C_{t+30}, ist RV_fwd30(t) fehlend (benannt). Panel-Luecken
  BTCUSDT/ETHUSDT werden in Teil B gezaehlt (fuer Tage ab 2024-06-01 nur Zeilenzaehlung, keine Rendite).
- **Underlying-Abweichung (benannt, nicht gemessen):** DVOL bezieht sich auf Deribit-Optionen auf den Deribit-BTC-Index;
  die RV kommt vom Bybit-USDT-Perp. Unterschiede: Basisaenderung Perp/Index, USDT/USD. Fuer die 30-Tage-Vol aus
  Tagesrenditen vermutlich klein; eine Messung waere eine RV-Rechnung im Fenster (gesperrt) und ist Bericht im Lauf.
- **Alternativen (Entscheidungsvorlage, Stufe 2):** Spannweiten-Schaetzer (Garman-Klass/Parkinson) aus derselben
  Tageskerze (effizienter, kleine Diskretisierungsverzerrung) - Richtung Testbarkeit; Stundenrenditen aus Trades -
  Datenvolumen wie oben, nicht vertretbar.

### A.3 Praemien-Definition (H-26-Erbe, PRD 3.2 Klasse P)

`P(t) = IV(t) - RV_fwd30(t)` in Vol-Punkten (S1); Varianten S2 `(IV^2 - RV^2)/100` (annualisierte Varianz in
Dezimal-Einheiten x 100, d. h. 0,14 = 14 "Varianzpunkte") und S3 `ln(IV/RV)`. BTC und ETH je Tag; das Bein (DEC-62 E3)
siehe `FEASIBILITY.md`.

### A.4 Zeitraeume

| Zweck | IV-Tage t | Preistage | Regel |
|---|---|---|---|
| Vorperiode (Nuisance) | 2021-03-24..2024-05-01 | bis 2024-05-31 | Praemien nur im Speicher, kein Mittel ausgegeben |
| Abdeckung/Vollstaendigkeit | 2021-03-24..2026-07-31 (+ Naht) | Panel bis 2026-07-30 | nur Zeilen/Luecken/Zeitstempel/Schema/Gleichheit |
| Urteilsfenster (nur fuer die Lauf-Spezifikation) | W1 2024-07-01..2025-06-30, W2 2025-07-01..2026-06-30 | bis 2026-07-30 | nicht berechnet |

## B. Datenteil - Stand 2026-10-13: WARTET AUF DATEN

### B.1 Katalog-Abdeckung `deribit/dvol` (einmalige Pruefung `hd.catalog(refresh=True)`, [S:catalog_check.py])

- Katalog-Export: **2026-10-12 10:50:14 UTC** (unveraendert gegenueber dem Stand beim Start), 329.442 Partitionen.
- `deribit/dvol` BTC und ETH: je **234 Partitionen, 2025-08-01..2026-10-11**; im Bereich 2021-03-24..2026-07-31 je
  165 Tage vorhanden, **1.791 fehlend** (`hd.gaps`). Der angekuendigte Backfill 2021-03-24..2025-07-31 ist **nicht
  sichtbar** -> Stopp laut Auftrag ("wartet auf Daten").
- **Luecken im bestehenden Strom (BTC und ETH identisch):** **2025-09-01..2026-03-19 (200 Tage)**, 2026-08-02..2026-08-03,
  2026-09-20. In W2 (2025-07-01..2026-06-30) liegen vom Strom nur 2025-08-01..08-31 und 2026-03-20..06-30 vor (134 Tage);
  mit dem bestellten Backfill (bis 2025-07-31) kaemen 31 Tage hinzu -> **165 von 365 W2-Tagen**. Der Backfill-Auftrag an
  Data-Harvest deckt die W2-Luecke nicht ab (Erweiterung noetig, siehe `FEASIBILITY.md` Abschnitt 1). Dass Deribit diese
  Tage liefert, belegt der PC-REST-Backfill aus WP-9 (1.996 Tage lueckenlos 2021-03-24..2026-09-09, DEC-61).
- Katalog-Metadaten: August 2025 je Tag eine nicht kompaktierte Datei mit `rows`/`status` leer, ab 2026-03-20
  `rows` 24 / `status` DONE; `location` archive 176 / ssd 58.

### B.2 Schema des bestehenden Stroms (Stichprobe 2025-08-01, 2025-08-31, 2026-03-20, 2026-06-30; [S:schema_probe_stream.py])

Ohne Werte (nur Struktur und Zeitstempel): je Tag und Symbol **24 Zeilen**, sechs Spalten wie im Archiv-Layout,
`topic` = `dvol.BTC` / `dvol.ETH`, `payload_json` = Objekt mit genau den Schluesseln `{close, high, low, open, timestamp}`,
`timestamp` = Kerzenbeginn (Stunden 00..23 des UTC-Tages, 24 verschiedene), `ts_exchange_ms` belegt. Vor und nach der
Luecke identisch (August-2025-Dateien trotz leerer Katalog-Metadaten gleiches Format). Der Tagesschluss nach A.1 ist
damit `close` der Zeile mit `timestamp` = 23:00 UTC des Tages. (Die vier Stichprobentage liegen je Symbol im
Sitzungs-Cache `scratchpad/h27_herleitung/hcache/`; ihre Werte wurden weder ausgegeben noch ausgewertet.)

### B.3 Preisquelle (Union-Panel, nur Vollstaendigkeit; [S:panel_coverage.py])

| Symbol | Zeilen | erster Tag | letzter Tag | fehlende Tage 2021-03-01..2026-07-31 | Duplikate | start_ms nicht 00:00 | close <= 0 / leer |
|---|---:|---|---|---:|---:|---:|---:|
| BTCUSDT | 2.083 | 2021-01-01 | 2026-09-14 | 0 | 0 | 0 | 0 |
| ETHUSDT | 2.010 | 2021-03-15 | 2026-09-14 | 14 (2021-03-01..03-14, vor Listing; ab 2021-03-15 lueckenlos) | 0 | 0 | 0 |

Damit sind alle 31 Tagesschluesse fuer jedes t in 2021-03-24..2026-06-30 vorhanden (Ziel bis 2026-07-30).

### B.4 Noch auszufuehren, sobald der Backfill im Katalog steht (Reihenfolge fix)

1. `hd.gaps` 2021-03-24..2026-07-31 je Symbol, Zeilen je Tag (Soll 24), doppelte/fehlende Stunden, Zeitstempel-Raster,
   Schema-Gleichheit Backfill vs. Strom (Schluessel, Typen, `topic`), alles ohne Werte.
2. Naht 2025-07-31/2025-08-01: `close(23h, 2025-07-31) == open(00h, 2025-08-01)` als Gleichheit (ja/nein) und dieselbe
   Stetigkeitszaehlung ueber alle aufeinanderfolgenden Tagespaare (Anteil gleicher Paare) - keine Niveaus.
3. DEC-61-Kreuzprobe ohne Niveauausgabe: Anteil der Tage, an denen der aus Stundenkerzen gebildete Tagesschluss gleich
   dem Tagesschluss des REST-1D-Backfills ist, ist nur auf dem PC pruefbar (Variante A); in der Cloud entfaellt sie,
   die Gleichheit ist durch WP-9 belegt (176 Tage, Differenz 0).
4. Vorperiode: Nuisance nach `FEASIBILITY.md` Abschnitt 3.

## C. Datenteil - Fortsetzung 2026-10-17 (Daten vollstaendig; B.4 hiermit ausgefuehrt)

### C.1 Katalog (einmal geladen, [S:catalog_check2.py])

- Export **2026-10-17T10:39:26Z** (`partitions-20261017T101504Z.parquet`, 17,6 MB, sha256 `031bc308...14c7d7`),
  349.961 Partitionen.
- `deribit/dvol` BTC und ETH: je **2.033 Partitionen 2021-03-24..2026-10-16, 0 Luecken (`hd.gaps`), alle DONE, je 24
  Zeilen**. Die W2-Luecke 2025-09-01..2026-03-19 und die Tage 2026-08-02..03, 2026-09-20 sind geschlossen.
- `bybit/publicTrade` BTCUSDT/ETHUSDT 2026-07-01..2026-10-16: je 108 Tage, 0 Luecken (ETHUSDT ein Tag `RUNNING`);
  2021-03-01..2024-05-31: je 1.188 Tage, 0 Luecken. (Katalog-Bytesummen siehe `KONTAMINATION.md` Nachtrag.)

### C.2 DVOL-Inhaltsprobe ohne Niveaus ([S:dvol_probe.py], Ergebnis `scratchpad/h27_herleitung/dvol_probe.json`)

| Pruefung | BTC | ETH |
|---|---|---|
| Zeilen / Tage | 48.792 / 2.033, jeder Tag 24 Stunden | identisch |
| doppelte Stunden, Zeitstempel nicht auf voller Stunde, nicht-numerische OHLC | 0 / 0 / 0 | 0 / 0 / 0 |
| Tage ohne 23:00-Kerze | 0 | 0 |
| Payload-Schluessel | `close,high,low,open,timestamp` in allen vier Perioden (Vorperiode, Backfill 2024-07..2025-07, Strom 2025-08..2026-06, blind ab 2026-07) | identisch |
| `topic` | `dvol.BTC` in allen Perioden | `dvol.ETH` |
| `ts_exchange_ms` = Payload-`timestamp` (Kerzenbeginn) | 48.792 / 48.792 | 48.792 / 48.792 |
| **Naht 2025-07-31 23h close = 2025-08-01 00h open** | **gleich** | **gleich** |
| Tagesnaht close(23h, d) = open(00h, d+1): Vorperiode / 2024-07..2025-07 / 2025-08..2026-06 | 1.156 gleich, 39 abweichend / 382 : 14 / 329 : 4 | 1.111 : 84 / 381 : 15 / 326 : 7 |
| max. Abweichung an der Tagesnaht (nur Vorperiode ausgegeben) | 0,01 Vol-Punkte | 0,05 Vol-Punkte |
| Stundennaht close(h) = open(h+1) gleich (Vorperiode) | 26.509 : 976 (max 5,23) | 25.560 : 1.925 (max 1,91) |

Lesart: Backfill und Strom sind dieselbe Quelle und Konvention (Schema, `topic`, Zeitstempel gleich, Stetigkeitsquoten aehnlich;
DEC-61/DEC-95 E1 erfuellt). Tagesschluss = close der 23:00-Kerze; die Wahl gegen den open der Folgestunde ist in der
Vorperiode hoechstens 0,05 Vol-Punkte wert (an 3..7 % der Tage) und damit fuer die Statistik unerheblich. Ab
2026-07-01 wurden nur Zeilen, Zeitstempel und Schema geprueft (Blind-Siegel DEC-96 E3).

### C.3 RV-Konvention Panel gegen `publicTrade` ([S:conv_check.py], vor 2024-06-01)

| Symbol | Tage | Panel-close = letzter Trade vor 00:00 UTC | rel. Abweichung | letzter Trade vor Mitternacht |
|---|---|---|---|---|
| BTCUSDT | 2021-06-15, 2022-11-09, 2023-03-15, 2023-09-15, 2023-12-15, 2024-03-15 | 6 / 6 | 0 | 0,15 .. 1,0 s |
| ETHUSDT | dieselben Tage | 6 / 6 | 0 | 0,01 .. 6,3 s |

Archivformat: eine Zeile je Trade, `payload_json` mit `timestamp` (Sekunden mit Nachkommastellen; 2022 teils ganze
Sekunden), `price`, `trdMatchID`. Am letzten Zeitstempel koennen mehrere Trades liegen (2022-11-09: 37 BTC- / 86
ETH-Trades in derselben Sekunde); der Gleichstand wurde nach Dateireihenfolge aufgeloest und ergab den Panel-close.
Folge: Die RV-Definition der Vorperiode (Panel) und der Fenster W3/W4 (`publicTrade`, Live-Frames ab 2026-07 mit
`data[]`-Listen) ist dieselbe, wenn der Lauf-Lader den letzten Trade des UTC-Tages in Boersen-Reihenfolge nimmt
(Zeitstempel, dann Position im Frame/in der Datei); die Regel gehoert in die Lauf-Spezifikation (C.14: Gleichstand
ohne eindeutige Reihenfolge -> laut scheitern).
