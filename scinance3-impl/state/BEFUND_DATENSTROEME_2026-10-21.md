# Befund Datenstroeme Data-Harvest (Katalog 2026-10-21T11:39:31Z) - Abdeckung, Schema, Panel-Luecke DEC-100

> Orchestrator, 2026-10-21. Nur Zaehlungen, Zeitstempel, Symbol- und Datumslisten; keine Marktwerte, keine Statistik
> auf Tagen ab 2026-07-01 (DEC-96 E3). Kein Hostname, keine Zugangsdaten. Skripte (Scratchpad, nicht im Repo):
> `hscripts/check_streams_1021.py`, `probe_partitions_1021.py`, `register_and_coverage_1021.py`,
> `consistency_surv_vs_kline1d.py`, `download_1021.py`.

## 1. Katalog (380.604 Partitionen, 29 Stroeme) - die neuen Stroeme aus DEC-98 N4 sind alle da

| Strom | Umfang | Status | Bemerkung |
|---|---|---|---|
| `bybit/rest.kline1m` BTCUSDT | 2020-03-25..2026-10-20, 2.401 Tage, 0 Luecken, alle DONE | vollstaendig | nur 2020-03-25 (Symbolstart) 804 Zeilen, sonst 1.440/Tag |
| `bybit/rest.kline1m` ETHUSDT | 2021-03-15..2026-10-20, 2.046 Tage, 0 Luecken | vollstaendig | 1.440 Zeilen/Tag ohne Ausnahme |
| `bybit/rest.kline1d` (symbol=ALL) | **2021-01-01**..2026-10-20, 2.119 Tage, 0 Luecken | vollstaendig | NICHT erst ab 2026-09-29: Data-Harvest hat den Tagesstrom bis 2021 zurueckgefuellt; Zeilen tragen das Kontraktsymbol in der Spalte `symbol`, Payload = Dict (`symbol, category, interval, startTime, openPrice, highPrice, lowPrice, closePrice, volume, turnover`), nicht die Listenform der API |
| `bybit/rest.fundingRateAll` (symbol=ALL) | 2021-01-01..2026-10-20, 2.119 Tage | vollstaendig | Payload `{symbol, fundingRate, fundingRateTimestamp, category}`, eine Zeile je Abrechnung |
| `bybit/rest.instruments` | ab 2026-10-20 (Tagesschnappschuss) | laufend | 2.017 Instrumente am 2026-10-21 (linear 1.024 Closed / 906 Trading / 6 PreLaunch / 5 PendingOpen; inverse 50/26) |
| `bybit/delisting_dates` | ab 2026-10-20 | laufend | 339 Zeilen am 2026-10-21: 333 `Closed` + 6 `Relisted`; Felder `last_trading_day`, `announcement_day` (268 gefuellt), `announced_delisting_utc`, `first_seen_closed`, `relisted_launch_day` |
| `bybit/rest.tickers15m` | ab 2026-10-20 | laufend | 26 Symbole (20 datierte BTC/ETH-Kontrakte + 6 Perps), 45 Schnappschuesse am 2026-10-21 (Tag noch offen) |
| `bybit/rest.deliveryPrice` | 2021-06-25..2026-09-25, 119 Partitionen | - | Settlement-Historie (A4, DEC-98 N4) |
| `deribit/rest.settlements` BTC/ETH | 2017-05-25..2026-10-20, 3.436 Tage, 0 Luecken (ETH erst ab 2019) | vollstaendig | je Zeile `type` delivery/settlement, `instrument_name`, `timestamp`, dazu Preise (fuer den A2-Zensus entfernt) |
| `deribit/rest.deliveryPrices` | 2016-03-18..2026-10-20 | - | fruehe Jahre nur woechentlich (193 Luecken-Bloecke, erwartbar) |
| `deribit/dvol` BTC/ETH | 2021-03-24..2026-10-20, 0 Luecken | vollstaendig | unveraendert |

Nicht im Katalog: `bybit/rest.deliveryPrices` (heisst `rest.deliveryPrice`), `deribit/rest.dvol` (heisst `dvol`).
Alle sechs Kestrel-Spalten (`ts_local_ns, ts_exchange_ms, topic, stream, symbol, payload_json`) in jedem Strom.

## 2. Panel-Luecke DEC-100: die 45 Symbole sind im Strom `rest.kline1d` bereits enthalten

Abgleich des Registers `bybit/delisting_dates` (2026-10-21) gegen den Extrakt `rest.kline1d` 2021-01-01..2026-09-28
(1.168 Symbole, 2.097 Tage, 692.628 Zeilen; Register-Kopie `state/data_harvest_delisting_register_2026-10-21.csv`):

| Menge | Zahl | Befund |
|---|---:|---|
| lineare USDT-Perps mit `last_trading_day` <= 2026-09-28 | 312 | davon 306 `Closed`, 6 `Relisted` |
| Abdeckung Listung..letzter Handelstag lueckenlos (`OK`) | 280 | alle DEC-100-Beispiele (AGTUSDT, CELRUSDT, GLMRUSDT, GTCUSDT, OSMOUSDT, PERPUSDT, RSS3USDT, LOOKSUSDT, EOSUSDT, PUMPUSDT ...) vollstaendig |
| `PARTIAL` | 25 | ausnahmslos fehlende Tage am **Anfang** (Listungstag ohne Tageskerze: 20 Symbole 1 Tag, DARKUSDT/DODOUSDT/FETUSDT/SCRUSDT 2, ORBSUSDT 4, HOOKUSDT 6, HIGHUSDT 10 Tage; MATICUSDT: Register-Listung 2021-01-15, erste Kerze 2021-06-29 - die API liefert fuer 2021 H1 nur 5..16 Symbole je Tag, identisch mit dem Ueberlebenden-Baum) |
| `NO_ROWS` | 1 | LAYERUSDT: Listung = letzter Handelstag 2025-01-24, keine API-Kerze |
| `Relisted` (DATAUSDT, KORUUSDT, LITUSDT, MONUSDT, SPCXUSDT, ZKUSDT) | 6 | Data-Harvest hat P-2 beantwortet: alle sechs wurden delistet (z. B. ZKUSDT letzter Handelstag 2024-06-06) und spaeter unter gleichem Namen neu gelistet (`relisted_launch_day`, z. B. ZKUSDT 2024-06-20). Die Kline-API liefert nur den NEUEN Kontrakt (erste Kerze = `relisted_launch_day`, identisch im Ueberlebenden-Baum); die fruehere Episode ist weder im Strom noch im alten Delisted-Baum rekonstruierbar. Behandlung: bleiben Ueberlebende (Builder laesst `status != Closed` aus und benennt sie); die PIT-Maske endet NICHT frueh (DEC-100 (3) damit erledigt) |

**Folge:** Der Auftrag P-1 (`state/AUFTRAG_DATA_HARVEST_PANEL_DELISTED_2026-10-20.md`) ist durch den bestehenden
Strom erfuellt - kein weiterer Backfill noetig; die Antwort zu P-2 steckt im Register-Strom.

## 3. Konsistenz Ueberlebenden-Baum (Zip 2026-09-28, Daten bis 2026-09-14) gegen `rest.kline1d`

- 876 Symbole im Ueberlebenden-Baum, davon 830 Perps auch im Strom; **erste Kerze identisch bei 830 von 830**;
  Tagesschluesse identisch auf 506.039 von 506.863 gemeinsamen (Symbol, Tag)-Zeilen, die 824 Abweichungen liegen alle
  in 2026 (eine je Symbol: letzter offener Tag 2026-09-14 des Baums gegen die abgeschlossene Kerze des Stroms).
- 46 Baum-Symbole fehlen im Strom: ausschliesslich **datierte Futures** (`BTCUSDT-25DEC26` ...), die im Strom (nur
  Perps) nicht gefuehrt werden; sie sind kein Teil des Perp-Universums.
- Symbole je Tag: 2022-04-18 Baum 109 / Strom 154; 2024-07-01 255 / 404; 2025-07-01 393 / 567; 2026-06-26 652 / 668.
  Die Differenz sind die delisteten (jetzt im Register) und Nicht-USDT-Perps (`*PERP` USDC, inverse).
- Der Strom ist auf jedem geprueften Tag eine Obermenge des Baums (Perps): Baum-only 0.

## 4. Was folgt
- Delisted-Baum neu bauen aus `rest.kline1d`/`rest.fundingRateAll` (Builder `scripts/h32_build_delisted_tree.py`, Dict-
  Payload und `status` seit 716191b/Folgecommit) mit dem Register 2026-10-21, `--cut 2026-09-28`; Fingerprints; dann
  Union-Abgleich je Tag (Ueberlebende + Delisted gegen Strom, lineare USDT-Perps).
- H-32: Vorlauf v6 auf dem vollstaendigen Panel (Panel-Schnitt 2026-06-28), Registrierung.
- Optional spaeter: das gesamte Union-Panel direkt aus dem Strom (ein Baum) - eigene DEC, nicht vor H-32.

## 5. Delisted-Baum v2 gebaut und Union gegen den Strom geprueft (2026-10-21, 13:25 UTC)

`scripts/h32_build_delisted_tree.py --register state/data_harvest_delisting_register_2026-10-21.csv --partitions-dir
<Harvest-Cache>/raw/bybit --out <Scratchpad>/panel_delisted_v2 --cut 2026-09-28 --start-year 2021` (rc 3 = benannte
Luecken). Fingerprint und `delisting_dates.json` liegen unter `state/runs/delisted_tree_v2_20261021/` (nur Hashes,
Zaehlungen, Daten).

| Groesse | Wert |
|---|---|
| Register 2026-10-21 | 339 Zeilen, sha256 `a28c7eb7...4d639b22`; 306 selektiert (linear USDT, <= 2026-09-28, Closed), 6 `Relisted` ausgelassen und benannt |
| Eingaben | `rest.kline1d` 2.097 Partitionen / 692.628 Zeilen, `rest.fundingRateAll` 2.097 / 3.119.696; 0 identische, 0 widerspruechliche Duplikate |
| Baum | 305 Symbole mit Historie, 772 Partitionen: 747 DONE, 25 PARTIAL (Listungstag ohne Kerze, Abschnitt 2), 1 FAILED (LAYERUSDT NO_HISTORY); Baum-sha256 `250a923b...6427e401`; kein Symbol ohne Funding; keine Zeilen nach dem letzten Handelstag |
| Union (Produktions-Loader `load_panel_union`, as_of 2026-09-28, allow_partial) | 1.182 Spalten = 877 Ueberlebende + 305 Delistete; laedt ohne Fehler |
| Union gegen Strom, lineare USDT-Perps lebend je Tag | **identisch** an allen Pruefungstagen (2022-04-18: 153/153; 2023-01-02: 181/181; 2024-07-01: 381/381; 2025-07-01: 530/530; 2025-11-03: 557/557; 2026-06-26: 599/599); Jahres-Mediane 2022..2025 identisch (173 / 222 / 381 / 529); 2026 weicht nur nach dem Ende des Ueberlebenden-Baums (2026-09-14) ab - fuer den H-32-Schnitt 2026-06-28 ohne Belang |

Die Ueberlebenden-Verzerrung aus DEC-100 ist damit behoben: W2 hat 557..599 statt ~526..568 lebende Symbole; die
alte Luecke war **31 von ~590 (5,3 %) in W2** und 5 in W1 (Zahlen aus Abschnitt 2 und dem Union-Abgleich).

**Was folgt:** Vorlauf v6 (`--prelaunch`, Panel-Schnitt 2026-06-28) auf diesem Union-Panel; Registrierung H-32 mit den
Fingerprints `delisting_register_sha256 = a28c7eb7...` und dem Baum-Hash. Der Auftrag P-1 an Data-Harvest entfaellt
(Mitteilung an Data-Harvest: `state/RUECKMELDUNG_DATA_HARVEST_PANEL_2026-10-21.md`).
