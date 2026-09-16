# Welle 1 - Befund Teil 5: WP-7 Zensus v2, WP-12 Delisting-Register, WP-10(B) Lauf 2, Manifest-Semantik (2026-09-15/16)

> Orchestrator-Adjudikation. Laeufe: `state/runs/wp7_20260916/` (Zensus v2,
> DEC-67 E6), WP-12 Konsolenausgabe 2026-09-16 (Register + Kline-Probe;
> Schritt 3 laut abgebrochen), `state/runs/wp10b_20260915/` (DEC-69),
> `harvest_manifest_status.py` 2026-09-16.

## WP-7 v2: Korrekturen liefern die fehlenden Konstanten

| Groesse | Wert | Bemerkung |
|---|---|---|
| N_eff (Ledoit-Wolf) letzte 52 Wochen | **178,8** (423 balancierte Symbole) | urteilstragendes Fenster W=52 |
| N_eff letzte 104 Wochen | **101,2** (260 balanciert) | gepooltes Fenster |
| N_eff STRESS_ABS-Wochen | 2,4 (3 Stress-Wochen in 104) | nur Etikett, unbrauchbar |
| A1-Schluessel SD_null je Fenster / gepoolt | 0,0435 / 0,0495 | Permutations-Null ist signal-agnostisch (untied Ranks gegen Outcome); Bindungs-Korrektur bei 12 % Klumpen < 0,2 %, vernachlaessigbar |
| dito W_eff-adjustiert (0,41 W) | 0,0679 / 0,0773 | unter Schranken 0,0870 / 0,0966 -> A1 je Fenster machbar |
| Dezil-Degeneration, letzte 52 Wochen, Median-Woche 2026-03-16 | Klumpen 12,5 %, negativ 76,2 %, positiv 11,3 % | D1 nicht degeneriert (0/52), D10 nicht in der Median-Woche, aber 21/52 Wochen |
| Dezil-Degeneration, vorherige 52 Wochen, Median-Woche 2025-03-17 | Klumpen 12,2 %, negativ 87,2 %, **positiv 0,6 %** | **D10 degeneriert** (36/52 Wochen) |
| Intervallklassen-Wechsel je Symbol (878) | 580 nie, 140 einmal, 143 zwei- bis fuenfmal, 15 oefter | dynamischer Wechsel ist ueblich |

**Lesart des Schluessels F - I:** Die Praemie ueber dem Zins-Term ist in 76-87 % der Symbol-Wochen NEGATIV (Funding unter I, konsistent mit V-3), in 12 % exakt null, nur in 1-11 % positiv. Ein Long-Short-Dezil-Portfolio auf diesem Schluessel hat ein gut besetztes Long-Bein (D1: staerkste Unterschreitung von I) und ein Short-Bein, das im Fenster 2024-09..2025-09 im Null-Klumpen liegt. Nach der vorab fixierten Kill-Regel (DEC-67 E3) waere A1 in diesem Fenster KEIN VERDIKT - die Zwei-Fenster-Konstruktion ist mit zweiseitigem Dezil-Portfolio nicht durchfuehrbar.

## WP-12: Delisting-Register existiert, Bybit liefert Historie delisteter Symbole

- Announcements-API (`type=delistings`, 11 Seiten): **476 Announcements, 276 Symbole, 268 linear**; Register `register.parquet` sha256 `1560b829...`.
- Kline-Probe (90 Tage vor Delisting): **261 von 268 Symbolen mit Tageskerzen** verfuegbar, 7 ohne.
- Schritt 3 (Fixture) brach laut an den 69 PARTIAL-Partitionen ab (DEC-66-Ursache; `-AllowPartial` noetig).
- **Konsequenz:** Die B3-Vorabfestlegung "kein Survivorship-freies Universum aus Bordmitteln" ist durch Evidenz widerlegt: aus oeffentlichen Daten laesst sich ein Panel mit delisteten Symbolen bauen (WP-12b, DEC-70). Das B3-Fixture wird dann auf ECHTEN Delistings gerechnet, nicht auf 90-Tage-Fenstern oder Synthetik.

## WP-10(B) Lauf 2: siehe DEC-69
p_fill-Kurve Konstante (FIFO ~6 %, pro-rata ~35 % binnen 60 s); adv_sel unmessbar durch Slice-Fehler; Wiederholung mit Schema 2 laeuft.

## Manifest-Semantik (Registrar-Frage, DEC-68 (5))
`2026-07-01 orderbook BTCUSDT: status EMPTY, rows 0, size 0, archived_at None, ts_done 2026-08-10` bei 316 MB `_compacted.parquet` auf der Platte; `2026-08-02: DONE, 159.501 rows, archived_at 2026-09-10`. Das Backup-Manifest spiegelt fuer kompaktierte Tage nicht den Inhalt; die DEC-68-Regel (Kompaktierungsdatei = geschlossener Tag) bleibt. Frage an den Registrar: Warum werden orderbook-Tage mit Inhalt als EMPTY gefuehrt (Harvester-Bug oder Bedeutung "aus Rohteilen kompaktiert")?
