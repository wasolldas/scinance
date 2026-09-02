# WP-9 - DVOL-Backfill (Deribit, oeffentlich) und Quellen-Kreuzvalidierung

> Orchestrator-Spezifikation 2026-09-02. Zensus-Paket der 3.0-Welle 1, KEIN
> Alpha-Gate. Aendert die H-26-/C-33-Sperren NICHT (Irreversibilitaets-Regel:
> die Probe auf Nachladbarkeit ist Pflicht, nicht die Entsperrung).

## 1. Ziel
Zwei Fragen, je mit VORAB fixierter Konsequenz:
- **F1 Tiefe:** Wie weit reicht der oeffentliche Deribit-DVOL-Index (BTC, ETH)
  in Tagesaufloesung zurueck? Erwartung [sek]: ~2021-04. Konsequenz: Tage <
  Erwartung -> Befund "kuerzer als erwartet", Zahl steht im Report; keine
  weitere Folge.
- **F2 Austauschbarkeit:** Sind REST-Tagesschluss und der harvestete
  `deribit/dvol`-Strom (112+ Ueberlappungstage) dieselbe Groesse?
  Konsequenz: (a) austauschbar -> eine kuenftige H-27-Registrierung darf
  die REST-Historie als IV-Quelle nennen; (b) nicht austauschbar -> nur der
  Harvest-Strom ist fuer Deribit-IV zulaessig, REST-Historie bleibt
  deskriptiv. Beides ist ein Ergebnis.

## 2. Materialitaet (hergeleitet, DEC-32-Muster, NICHT importiert)
H-26 urteilt auf dem 90-Tage-Mittel der Praemie gegen 3 Vol-Punkte. Eine
Quellenabweichung ist MATERIAL, wenn sie dieses Mittel um >= 10 % der
Schwelle (0,3 Vol-Punkte) verschieben kann. Kriterium fuer F2:
|Mittel der Tagesdifferenz (REST - Harvest)| ueber die Ueberlappung <= 0,3
Vol-Punkte UND das 95-%-Bootstrap-CI dieses Mittels liegt innerhalb
[-0,3; +0,3]. Erreichbarkeitspruefung ZUERST: die Verteilung der
Tagesdifferenzen (p5/p50/p95, Autokorrelation) wird berichtet, BEVOR das
Kriterium angewandt wird; ist die Tagesdifferenz-SD so gross, dass das CI
bei n Ueberlappungstagen das Band nicht treffen KANN, lautet der Befund
"nicht entscheidbar bei n" (kein (b)!).

## 3. Datenquellen
- REST (oeffentlich, keine Keys): Deribit `public/get_volatility_index_data`
  mit currency=BTC|ETH, resolution=1D, start_timestamp/end_timestamp (ms),
  Antwort `result.data` als Liste [ts, open, high, low, close] [sek -
  Feldnamen im Lauf verifizieren, loud fail bei Abweichung]. Paginierung
  rueckwaerts bis leere Antwort. Drossel <= 5 Req/s.
- Harvest: `data/harvest/raw/deribit/dvol/symbol=*/date=YYYY-MM-DD/*.parquet`
  (Schema ts_local_ns, ts_exchange_ms, topic, stream, symbol, payload_json).
  Tagesschluss = LETZTER Frame je UTC-Tag (arg_max ueber (ts, payload),
  deterministisch), Wert aus payload (Feldname per Probe: erwartet
  `volatility`, evtl. unter `data`/`params.data` - Wrapper-tolerant wie
  wp6_optstress.unwrap_payload). Manifest-DONE-Tage bevorzugen
  (bar_cache.resolve_manifest_path); Nicht-DONE-Tage nur mit Etikett.

## 4. Deliverables
- `src/bybit_edge/research/wp9_dvol/` : `rest_client.py` (Paginierung,
  Drossel, Wrapper-Toleranz, SHA-256 der Rohantworten), `harvest_close.py`
  (Tagesschluss aus dem Strom, DuckDB, deterministisch),
  `crossval.py` (Differenzen, Bootstrap-CI stationaer Block 5 Tage,
  Erreichbarkeitspruefung, Befund a/b/nicht entscheidbar).
- `scripts/wp9_dvol_backfill.py` : `--probe` (Feldnamen/Tiefe fuer 3 Tage,
  laut), `--fetch` (Backfill -> `data/dvol_rest/<CUR>_1D.parquet` +
  Manifest-JSON mit Fingerprint; NIE in data/harvest schreiben),
  `--crossval` (Report JSON + Markdown nach `scinance3-impl/state/wp9_<datum>/`).
- `scinance3-impl/handoff_local/run_wp9_dvol.ps1` (PS 5.1, ASCII, Probe ->
  Fetch -> Crossval, rc != 0 bei Probe-Fehler).
- Tests (`tests/unit/test_wp9_dvol.py`): REST-Parser gegen Fixture-Antwort
  (inkl. falscher Feldnamen -> loud fail), Harvest-Tagesschluss auf
  synthetischem Baum (2 Tage, Wrapper-Varianten), Crossval mit DEC-39-
  Fixturepaar: POSITIV (identische Quellen -> Befund a), NULL/ADVERSARIAL
  (um +0,5 verschobene Quelle -> Befund b; sehr kleines n mit grosser SD ->
  "nicht entscheidbar"), Determinismus (zweimal rechnen, identischer
  Fingerprint), DEC-53-Artefakte (Tagesdifferenz-Serie + Bootstrap-Seed im
  Output).
- Kein numpy-Zwang noetig, aber erlaubt (Nutzer-PC hat volle Umgebung).

## 5. Nicht-Ziele
Keine Praemienberechnung, keine RV-Seite, keine Terzil-Gates (Review:
R3-K-36-Gate ist tot), keine Aenderung an H-26.
