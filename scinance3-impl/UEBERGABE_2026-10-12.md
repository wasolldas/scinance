# Scinance 3.0 - Uebergabe (Stand 2026-10-12)

> Ergaenzt `UEBERGABE_2026-10-09.md` (Rollen, Regeln, Fallen, Datei-Landkarte gelten weiter).
> Hier nur, was sich seither geaendert hat und was als Naechstes kommt.

## 1. Arbeitsweise seit 2026-10-10 (DEC-83, Nutzer-Auflage)

- **Cloud-first:** gerechnet wird in der Cloud-Sitzung; alle Daten kommen vom Thin Client (Data-Harvest).
  Nutzer-PC/Autopilot nur noch Rueckfall. Laengere Laeufe als Hintergrundprozess der Sitzung.
- **Bybit-REST ist aus der Cloud geo-gesperrt** (CloudFront, US-Region) - nicht per Allowlist loesbar.
- **Panel `panel_1d` + `panel_1d_delisted`:** liegt im Harvest-Archiv unter festem Schluessel
  `exports/scinance/INDEX.json` -> `scinance_panel_1d_2026-09-28.zip` (Data-Harvest DEC-45,
  `state/ANTWORT_DATA_HARVEST_PANEL_2026-10-12.md`). Nur exakte Schluessel lesen, Groesse + SHA256 pruefen,
  Zip hat Windows-Pfadtrenner -> mit Pfadpruefung in ein frisches Sitzungsverzeichnis entpacken (nie ins Repo,
  nie unter `data/harvest`), dann `--panel-base <dir>/panel_1d --delisted-base <dir>/panel_1d_delisted`.
  Stand reicht fuer WP-13 vollstaendig (Fenster enden 2026-06-30). Variante B (taeglicher Panel-Strom auf dem
  Thin Client) ist beim Data-Harvest-Projekt in Arbeit; Abweichungen angenommen (DEC-84).
- **Branches:** jede Cloud-Sitzung hat einen eigenen Branch; Commits zusaetzlich per Fast-Forward auf
  `claude/subagent-prd-development-T16fE` pushen (Merge-Commit, falls der Autopilot dort etwas gepusht hat).

## 2. Was seit 2026-10-09 passiert ist

| DEC | Inhalt |
|---|---|
| 81 | Kalibrierung: Suche mit gemeinsamen Zufallszahlen, Gegenprobe auf Standardfehler-Basis, realer Querschnitt; `beta_characteristic` bitgleich ~36x schneller |
| 82/84 | Erweiterte V-1: I skaliert exakt mit dem Intervall (Totzonen-Klumpen 1h/2h/4h/8h exakt bei 0,00125/0,0025/0,005/0,01 %); Auto-Switch seit 2025-10-30: 1h-Episoden kurz (Median 8 Tage, 129 Symbole), Rueckwechsel meist auf 4h (`state/runs/v1x_20261012/`) |
| 83 | Cloud-first |
| 85 | Gate-Audit-VETO gegen v5c ("keine Methode"): simulierte Marktspalte verfehlte DEC-77-Ziele (D1), Null-Renditen statt NaN (D2); v5d vorab fixiert, bindend |
| 86 | **v5d: vier Beta-Kontroll-Methoden bestehen in W1 und W2; registriert wird `fm_neutral_8w`** (`state/runs/wp13a_20261012_v5d/`) |

Tests: 1.992 passed / 3 failed (Legacy `test_execution_live.py`, Sandbox-bedingt, unveraendert) / 9 skipped.

## 3. Ergebnis A3 und naechste Schritte (Stand Abend 2026-10-12)

- **A3 (H-28..H-30, Kohorte F-XSEC1) ist abgeschlossen: GL-032, alle sieben Varianten GL-012 vor dem Lauf.**
  Drittfassung registriert (DEC-90, `state/registered/h28_h30_v3.yaml`), Positivkontrolle in Produktionskonfiguration
  NICHT BESTANDEN (DEC-91): die Power-Zuordnung hatte mit dem Boden-SE statt der registrierten SE gerechnet; mit der
  faktorbedingten IC-Streuung (W1 0,09/0,13 statt Boden 0,049) ist der Test in W1 bei Prior 0,03 zu schwach (Power
  0,47/0,21). Feststellung im registrierten Design, KEIN Verdikt ueber die Effekte. Gate-Audit bestaetigt; kein
  DEC-52-Zweig nachtraeglich (DEC-92). Keine reale IC berechnet, alle Siegel geschlossen.
- **Methodische Lehre:** Power/MDE immer mit der SE-Regel des registrierten Tests inkl. faktorbedingter Streuung unter
  der kalibrierten Null rechnen; Positivkontrolle in Produktionskonfiguration vor jedem Lauf (hat den Fehler gefangen).
- **Naechster Kandidat: A1** (Funding-Long-Bein gegen Universums-Hedge, DEC-70). V-1 ist jetzt empirisch belegt
  (DEC-84). Vor einer Registrierung: Herleitung mit Power auf der realistischen SE (Lehre oben), Positivkontroll-Plan.
- Ein anderes A3-Design (z. B. fm8-neutralisierter IC als Primaerstatistik, gepoolte Fenster) nur als NEUE Hypothese
  mit eigenem K (DEC-58 E2) und mit Offenlegung der gesehenen Zahlen (Etikett C.17).
- Nebenbei: `persistence_null`/`h30_feasibility`/Survivorship auf `returns_est` sind erledigt (DEC-87); offene
  Kosmetik: Docstring `positive_control.py` (Skalen) - aendert den Code-Hash, deshalb erst mit der naechsten Aenderung.
- Data-Harvest Variante B (taeglicher Panel-Strom) beim Data-Harvest-Projekt; bis dahin Zip-Export (Stand 2026-09-28).

## 4. Nachtrag 2026-10-13: A1 nicht registriert (DEC-93, GL-033)

- **A1 (Funding-Long-Bein D1 gegen Universums-Hedge, DEC-70) ist unter den geltenden Beschluessen vor der
  Registrierung GL-012:** mit W_eff = 0,41 W (DEC-67 E4, fuer A1 bestaetigt in DEC-70 E1) schon bei theta = 1
  (Preisbein kompensiert nichts) 176,5 > 147,6 bp. Zusaetzlich ist theta (nicht kompensierter Anteil des
  Funding-Vorteils) UNBELEGT; selbst die guenstigste Lesart braucht theta >= 0,77. KEIN Verdikt ueber den Carry.
  Akte: `state/herleitung_a1/` (Feasibility, Review mit VETO gegen "knapp testbar", Stufe 2 ohne Rechtswirkung).
- **Lehre (zusaetzlich zu DEC-92):** Feasibility-Pruefungen rechnen mit den GELTENDEN Konstanten; eine methodisch
  bessere Regel wird programmweit und vor dem Kandidaten beschlossen, der sie braucht, nie danach. Merkposten fuer
  eine programmweite DEC: DEC-67 E4 (Schluessel- statt Statistik-Persistenz), PRD-5.1-Schwelle (MDE-Faktor statt
  kritischer Wert), WP-7-Null-Auffuellung der Funding-Autokorrelation, Sonderpaare I = 0 (DEC-93 Merkposten).
- **Naechster Kandidat: H-27 (VRP auf DVOL-Backfill, DEC-61).** Datenzugang ist offen: die oeffentliche Deribit-API
  ist aus der Cloud durch die Proxy-Richtlinie gesperrt (2026-10-13 geprueft); die DVOL-REST-Historie ab 2021-03-24
  (WP-9) liegt auf dem PC. Weg wie beim Panel: Export ueber den Thin Client (Data-Harvest) anfragen. Danach
  Feasibility zuerst (Power mit der SE des registrierten Tests, geltende Konstanten), dann Herleitung + Review.
- Naechste freie Hypothesen-Nummer: H-32 (H-31 vermerkt, nicht registriert).

## 5. Nachtrag 2026-10-13 (spaeter): Programmregel P-1 beschlossen (DEC-94), DVOL-Anfrage gestellt

- **DEC-94 (P-1, prospektiv, Etikett "Lockerung"):** Schwelle = kritischer Wert zum registrierten alpha (1,6449 je
  Fenster, DEC-52 gepoolt 2,5287), Power/MDE/Zuordnung mit derselben SE, Autokorrelation der Teststatistik (c >= 1),
  DEC-52 bei Fenster-Power < 0,80 nur wenn das DEC-52-Gate (Produktrechnung) Power >= 0,80 hat; Doppelausweis unter
  A3-Praxis in jeder Registrierung. Gilt ab sofort inkl. H-27; GL-032/GL-033 unveraendert. Akte:
  `state/herleitung_programmregel_p1/` (Entwurf, Review ZUSTIMMUNG MIT AUFLAGEN). Code-Bau (Power-Funktion, z_krit aus
  dem YAML, stationaerer Bootstrap) steht noch aus - vor der H-27-Registrierung.
- **H-27-Daten:** Anfrage `state/ANFRAGE_DATA_HARVEST_DVOL_2026-10-13.md` (Nutzer leitet weiter). Harvest-Katalog fuehrt
  `deribit/dvol` erst ab 2025-08-01. Achtung Ergebnisblindheit: im Repo liegt die WP-10(A2)-Serie IV-RV
  (`state/runs/wp10a2_20260910/wp10a_ivrv_backfill_*_daily.csv`, 2021-03-24..2026-07-31) - vor der H-27-Registrierung
  nicht auf Niveau/Streuung auswerten ausser nach den Regeln der H-27-Herleitung (DEC-94 Feststellung).

## 6. Nachtrag 2026-10-13 (Abend): H-27 auf blinden Fenstern ab 2026-07-01 (DEC-95/96)

- DVOL-Historie kommt per Data-Harvest Variante B (DEC-95); Backfill 2021-03-24..2025-07-31 war im Katalog-Export
  2026-10-12 noch nicht sichtbar. Nachtrags-Anfrage wegen Luecken (2025-09-01..2026-03-19, 2026-08-02..03, 2026-09-20):
  `state/ANFRAGE_DATA_HARVEST_DVOL_NACHTRAG_2026-10-13.md` (Nutzer leitet weiter).
- **DEC-96:** H-27 wird nicht auf W1/W2 registriert (nicht blind), sondern auf zwei gleich langen, prospektiven Fenstern
  ab 2026-07-01 (L in {6, 9, 12} Monaten, kleinstes L mit Zuordnung C10/DEC52 aus der Nuisance 2021-03-24..2024-05-31).
  **Blind-Siegel programmweit:** keine DVOL- und keine BTC/ETH-Vol-/Renditestreuungs-Statistik ab 2026-07-01 bis zum
  H-27-Lauf (Panel in anderen Paketen bei 2026-06-30 abschneiden).
- Herleitung `state/herleitung_h27/` (Stufe 0 fertig; Stufe 1 wartet auf den Backfill im Katalog). RV-Quelle: Panel-
  Tagesschluesse BTCUSDT/ETHUSDT (Katalog hat keinen kompakten Intraday-Preisstrom). Prior [sek]: BVRP 0,14 (BTC,
  Deribit 2017-07..2022-12, arXiv 2410.15195), Volltext vor Registrierung im Original pruefen (Egress gesperrt).

## 7. Nachtrag 2026-10-17: H-27 GL-012 vor der Registrierung (DEC-97, GL-034) - Stand des Programms

- Katalog wieder taeglich (Data-Harvest DEC-53..56); DVOL BTC/ETH 2021-03-24..2026-10-16 lueckenlos.
- **H-27 nicht registriert:** auf blinden Fenstern ab 2026-07-01 erreicht keine Laenge 6/9/12 Monate die Power
  (L 12: 0,575; MDE80 12,9 VP gegen Prior 9,5 VP; C10 braeuchte ~22 Monate je Fenster). Kein Verdikt ueber die VRP.
  Blind-Siegel DEC-96 E3 bleibt (Fenster ab 2026-07-01 fuer jede kuenftige VRP-Hypothese blind).
- **Bilanz:** A3 (GL-032), A1 (GL-033) und H-27 (GL-034) sind alle an der Power gescheitert, nicht an Daten oder Code:
  mit zwei Jahresfenstern, C.10 hart und Power 0,80 sind Effekte in Literaturgroesse auf diesem Bestand nicht testbar.
  A2 (V-5c), A4 (recording-first) und A5 (E.6) bleiben gesperrt.
- **Naechster Schritt (Vorschlag):** Programm-Bilanz mit Power-Zensus ueber die verbleibenden Klassen (wo ist bei
  gegebener Datenlage ueberhaupt Power >= 0,80 erreichbar - laengere blinde Aufzeichnung, Ereignis-Designs mit vielen
  unabhaengigen Einheiten, Hochfrequenz-RV, A4-Aufzeichnung) als Entscheidungsvorlage fuer den Nutzer (PRD Par. 8),
  bevor weitere Einzelherleitungen Kosten erzeugen.

## 8. Nachtrag 2026-10-18: Programm-Bilanz (DEC-98), Nutzer-Stand, Datenauftraege

- `STAND_2026-10-18.md` (fuer den Nutzer), `state/PROGRAMM_BILANZ_2026-10-18.md` + Review + DEC-98 (Power-Zensus: wann
  waere wo Power 0,80 erreichbar; Hebel; Datenbedarf; fuenf Optionen). Kernzahlen: VRP 672 Tage je Fenster (2030-04),
  A3 Roh-IC 119/57 Wochen (stress/measured), A1 nur mit theta, A4 ab 2029-06; A3 mit beta-neutralem IC auf W1/W2
  HEUTE C10-faehig bei belegtem Prior >= 0,020 (UNBELEGT) - neue Hypothese H-32.
- **Blindperiode ab 2026-07-01 ist je Groesse einmal vergebbar** (VRP vs. Klasse W/A1 vs. H-26) - Nutzer-Entscheidung
  offen; Default: niemand rechnet dort, H-26 bleibt gesperrt (R-1), keine Regelaenderung.
- Datenauftraege freigegeben (`state/AUFTRAG_DATA_HARVEST_2026-10-18.md`, Data-Harvest setzt selbst um): B-0 done_days-
  Inventur H-26, B-1 Panel-Strom aller Perps + Instruments-Schnappschuss + Funding (irreversibel), B-2 A4-Quotes +
  Inhaltsproben, B-3 1-min-Kerzen BTC/ETH ab 2021, B-4 Deribit-Verfallskalender.
- Naechste Arbeit des Orchestrators (ohne Nutzer-Entscheidung moeglich): Recherche-Belege (Prior beta-neutraler IC,
  theta, V-5b/c, V-4; Volltexte per Nutzer-Upload), HF-RV-Streuung auf der Vorperiode nach B-3 (nur Streuung).

## 9. Nachtrag 2026-10-20: DEC-99 (Pilot-Schaetzfenster), H-32 gebaut, DEC-100 (Panel-Luecke), Datenlieferungen

- **DEC-99 (Nutzer-Zustimmung):** REZENZ als notwendige Bedingung, aeltere Daten vorab registriert als Pilot-Schaetzfenster
  oder zusaetzliches Urteilsfenster; genau ein Pilotlauf; F-WEEK zaehlt nur getestete Hypothesen; W2 endet 2026-06-28.
  Nachtrag 1: F-WEEK-p aus den Replikaten der faktorerhaltenden Null (Permutation kontaminiert, DEC-77).
- **H-32 (A3 mit beta-neutralem IC, Zweistufen-Design):** Herleitung + Review (`state/herleitung_h32/`, ZUSTIMMUNG MIT
  AUFLAGEN, eingearbeitet). Treiber gebaut und abgenommen: `src/bybit_edge/research/h32_fm8/`, `scripts/h32_fm8.py`,
  Tests `tests/unit/test_h32_*.py` (Commit f7dd471; Gesamtsuite 2.248 passed / 3 bekannte Altfaelle / 9 skipped).
  Modi: `--prelaunch` (v6, outcome-frei, Panel-Schnitt <= 2026-06-28), `--emit-template`, `--pilot` (Schnitt <= 2024-06-30,
  Uebergaberegel U, mu_sel, Genau-ein-Pilot-Sperre), `--positive-control`, `--run`. Folgebau laeuft (p-Replikate in v6,
  `scripts/h32_build_delisted_tree.py`). NICHT registriert; kein Lauf auf Realdaten bisher.
- **DEC-100:** 45 delistete lineare USDT-Perps fehlen im Union-Panel (31 mit letztem Handelstag in W2) - Ueberlebenden-
  Verzerrung; Register-Datum kuenftig = letzter Handelstag (Data-Harvest `bybit/delisting_dates`); 6 Symbole bei uns
  faelschlich als delistet. **H-32-Registrierung wartet auf das Nachladen** (`state/AUFTRAG_DATA_HARVEST_PANEL_DELISTED_
  2026-10-20.md`); danach Delisted-Baum neu bauen, Fingerprints, Vorlauf v6, Registrierung, Positivkontrolle, Pilot, Test.
- **Datenlieferungen (DEC-98 Nachtrag 4):** Panel-Strom aller Perps ab 2026-09-29 (`rest.kline1d`, `rest.fundingRateAll`,
  `rest.instruments` ab 2026-10-20), A4-Quotes `rest.tickers15m` ab 2026-10-20 (Korrektur: Ticker-Strom hatte keine
  datierten Futures), 1-min-Kerzen BTC/ETH (ETH ab 2021-03-15), Deribit `rest.settlements` ab 2017, Options-Lueckenkarte.
  H-26 bleibt gesperrt (strenge Lesart unerfuellbar; naechste Lesart fruehestens 2027-04-06).
- **PDF-Belege (DEC-98 Nachtrag 2):** beta-neutraler IC-Prior nur als Band 0,004..0,033 (Universum entscheidet) -> Pilot
  ersetzt den Literatur-Prior; VRP-Prior 7,1 VP; V-5c primaer belegt; theta offen. Fehlende PDFs: LTW JF 2022, Weiss 2026 u. a.
- **Naechste Schritte:** (1) Data-Harvest-Backfill abwarten -> Delisted-Baum -> v6 -> Registrierung H-32 (YAML + sha,
  Registry-Eintrag, Doppelausweise) -> Positivkontrolle -> Pilot -> Uebergabe -> Test; (2) Check-in 2026-10-21 12:40 UTC:
  neue Stroeme im Katalog -> HF-RV-Nuisance (nur <= 2024-05-31) und A2-Ereigniszensus; (3) Blind-Siegel DEC-96 E3 gilt.

## 10. Nachtrag 2026-10-21: Datenstroeme geprueft, Panel-Luecke ohne Backfill geschlossen, Vorlauf v6 und HF-RV-Nuisance gestartet

- **Katalog 2026-10-21 (Befund `state/BEFUND_DATENSTROEME_2026-10-21.md`):** alle Stroeme aus DEC-98 N4 sind da und
  vollstaendig: `rest.kline1m` BTCUSDT 2020-03-25.. / ETHUSDT 2021-03-15.. (1.440 Zeilen je Tag, 0 Luecken),
  `rest.kline1d` + `rest.fundingRateAll` **ab 2021-01-01** (Data-Harvest hat den Tagesstrom aller Perps rueckgefuellt),
  `rest.instruments`, `delisting_dates`, `rest.tickers15m` ab 2026-10-20, `deribit/rest.settlements` ab 2017-05-25.
  Falle: Kline-Payload der REST-Partitionen ist ein Dict mit benannten Feldern (Builder angepasst, 716191b/9364993).
- **DEC-100 Nachtrag 1:** die 45 delisteten Perps sind im Strom bereits enthalten (280 lueckenlos, 25 ohne Listungstag,
  LAYERUSDT ohne Kerze); Auftrag P-1 entfaellt (`state/RUECKMELDUNG_DATA_HARVEST_PANEL_2026-10-21.md` an Data-Harvest
  weiterleiten). Die sechs Symbole sind `Relisted` (delistet, spaeter neu gelistet; nur der neue Kontrakt in der API) ->
  bleiben Ueberlebende. Delisted-Baum v2 (`state/runs/delisted_tree_v2_20261021/`, Register-sha a28c7eb7..., Baum-sha
  250a923b...): Union = 877 Ueberlebende + 305 Delistete, lebende USDT-Perps je Tag **identisch** mit dem Strom.
  Der Baum selbst liegt im Scratchpad (`panel_delisted_v2`), bei neuer Sitzung aus dem Harvest-Cache neu bauen:
  `scripts/h32_build_delisted_tree.py --register state/data_harvest_delisting_register_2026-10-21.csv --partitions-dir
  <cache>/raw/bybit --out <neu> --cut 2026-09-28 --start-year 2021` (rc 3 = benannte Luecken; Hash muss 250a923b... sein).
- **Vorlauf v6 gelaufen** (13:28..15:28 UTC, rc 0, result_sha256 2ae9bad6..., Artefakte `state/runs/h32_20261021_v6/`, Template `state/herleitung_h32/h32_v1_TEMPLATE.yaml` - NICHT registriert): `scripts/h32_fm8.py --prelaunch --cut-date 2026-06-28 --n-reps 1000 --n-boot 1000
  --p-reps 10000 --seed 53 --allow-partial --as-of 2026-09-28`, Ausgabe `state/runs/h32_20261021_v6/`. OHNE
  `--v5e-reference`: die W1-Determinismus-Kontrolle setzt ein unveraendertes W1-Panel voraus, das DEC-100 geaendert hat
  (5 Symbole in W1 neu) - sie wuerde hart abbrechen; Ersatz: Zweitlauf-Fingerprint (optional) und T2-Tests.
  Pilotfenster P: 115 Formationswochen, K 127..353 (vorher 114 / 120..339).
- **HF-RV-Nuisance + A2-Zensus (Auftrag `scratchpad/SPEC_HFRV_herleitung.md`, Opus-Agent laeuft):** Extrakte unter
  `scratchpad/hf_data/raw/` (1-min BTC/ETH 2021-03-24..2024-05-31, DVOL roh, Settlement-KALENDER ohne Preise,
  deliveryPrices-DATEN ohne Preise). Ergebnis nach `state/herleitung_hfrv/`. Nur Streuung/c, kein Mittel.
- **Naechste Schritte:** v6 auswerten (Kernzahlen nachrechnen) -> `--emit-template` -> `state/registered/h32_v1.yaml`
  fuellen (Erstfassung Abschnitt 11) -> adversarischer Review -> Registrierung (Registry-Eintrag, sha256) ->
  Positivkontrolle -> Pilot -> Uebergabe -> Test. Dann HF-RV-Review -> DEC-Nachtrag (Option 3 tragfaehig?) -> Nutzer.
- **Nachtrag 10a (16:30 UTC): Gate-Review VETO (aufloesbar) und DEC-101 Teil 1.** `state/herleitung_h32/
  REVIEW_REGISTRIERUNG_H32.md`: v6-Arithmetik bestaetigt, aber das Universum enthaelt 68 USDC-Perps (`*PERP`, Zwillinge
  der USDT-Perps) und datierte Futures (`*-DDMMMYY`); Delisted-Seite nur USDT; Null zu eng (W2 ~x1,13). DEC-101 Teil 1:
  Universum = lineare USDT-Perps (Filter vor jeder Rechnung), skalierte Null im Testlauf (k = max(1, SD_real/sd_week),
  keine negative Gutschrift), Pilot-Ausgabepfad gepinnt + Suche nach Pilot-JSONs, Pins (delisted_tree_sha256, runner),
  q95 = max(1.000er, 10.000er Quantil), Endpower aus Replikat-Quantilen, `--pp3-dry-run`. Der Vorlauf 13:28 ist **v6a,
  verworfen** (Akte). Builder-Auftrag `scratchpad/SPEC_DEC101_builder.md` laeuft (Sonnet, Worktree). Danach: Abnahme,
  v6b zweimal bitgleich (je ~2 h), Template, Entwurf, Nachpruefung Pruefpunkte 1-5, PP3, Registrierung (DEC-101 Teil 2).
- **Nachtrag 10b (17:20 UTC): DEC-101-Umbau abgenommen und uebernommen** (Commit 6e4b447: `universe.py`, `powerline.py`,
  `pp3.py`, skalierte Null in `testrun.py`/`gate.py`, Pilot-Sperre in `checks.py`, Pins in `schema.py`, Vorlage;
  Tests `test_h32_dec101.py`, Teilmenge 276 passed). **Vorlauf v6b laeuft zweimal parallel** (Universum 1.182 -> 1.066
  Symbole: 68 USDC-Perps, 48 datierte Futures ausgeschlossen; `scratchpad/run_h32_v6b.sh`, Ausgaben
  `scratchpad/h32_v6b_run1|run2`, Logs `h32_v6b_r1|r2.log`; result_sha256 muss bitgleich sein, dann Kopie nach
  `state/runs/h32_20261021_v6b/`). Danach: `--emit-template` -> Entwurf aktualisieren -> `--pp3-dry-run` ->
  Nachpruefung Gate-Auditor (Pruefpunkte 1-5) -> Registrierung (DEC-101 Teil 2) -> `--pilot --out
  scinance3-impl/state/runs/h32_pilot_v1` -> Positivkontrolle -> `--run`. Neue CLI-Pflicht: Runner-Argumente
  (`--as-of 2026-09-28 --start-year 2021 --end-year 2026 --allow-partial`) muessen den YAML-Pins entsprechen.
- **Nachtrag 10c (19:40 UTC): v6b bitgleich, U-3, PP3 bestanden, Nachpruefung laeuft.** Vorlauf v6b zweimal gerechnet,
  alle Artefakte bitgleich (result_sha256 eee9ced9..., `state/runs/h32_20261021_v6b/`); Universum 1.066 Symbole
  (P K 126/206/339, W1 343/416/500, W2 501/526/545). Power-Zeile zeigte: Regel U deckte (1c) bei mom4 nicht (Marge
  -0,0006) -> **Regel U-3** (Commit f07d060, DEC-101 Teil 2): Schwelle auf x_P = max(m* + MDE80*_U, max_W(q95 + z_80
  SD_T)); Schwellen mom1 0,0205, mom2 0,0230, mom4 0,0280, rev_gap 0,0185. Vorlage `h32_v1_TEMPLATE.yaml` sha256
  a3079cf9...; PP3-Trockenprobe BESTANDEN (K-Reihen P/W1/W2 = Pins, keine IC). Entwurf Fassung 2
  (`REGISTRIERUNG_H32_entwurf.md`). Nachpruefung der Pruefpunkte 1-5 durch den Gate-Auditor angefordert; danach
  Registrierung (DEC-101 Teil 2, Kopie nach `state/registered/h32_v1.yaml`, Registry-Eintrag), dann Pilot
  (`--pilot --out scinance3-impl/state/runs/h32_pilot_v1`, genau einmal).
- **Nachtrag 10d (20:32 UTC): H-32 REGISTRIERT.** Nachpruefung des Gate-Auditors: VETO aufgehoben, Auflagen
  N-1..N-5 umgesetzt (Commit 117dc02: Positivkontrolle in Produktionskonfiguration mit skalierter Null und Injektionsziel
  F, Regel U-4 mit k_pred, Pilot-Versuchsmarker; 307 Tests, Gesamtsuite 2.399 passed / 3 Altfaelle). Registrierungsdatei
  `state/registered/h32_v1.yaml` sha256 `0fadda785f37a9ab24b31f650611a468f5c6bfef8be8fb65a7dc54261c1bbd60` (Startsperre), Registry-Eintrag
  H-32, DEC-101 Teil 2. PP3-Trockenprobe auf der registrierten Datei bestanden. **Naechster Schritt: genau ein Pilotlauf**
  (`scratchpad/run_h32_pilot.sh`: `--pilot --registered state/registered/h32_v1.yaml --registered-sha256 <sha> ... --out
  scinance3-impl/state/runs/h32_pilot_v1 --seed 53`); danach GL-/DEC-Vermerk der Uebergabe je Variante, dann
  Positivkontrolle (`--positive-control`, nur mit uebergebenen Varianten), dann `--run`.
- **Nachtrag 10e (20:50 UTC): H-32 Pilot gelaufen -> GL-012 (Pilot) fuer alle vier Varianten (GL-035, DEC-101 Teil 3).**
  Momentum-Varianten im Pilot deutlich negativ (x_P -0,038 / -0,050 / -0,045, t -3,3 / -4,1 / -3,6), rev_gap +0,017
  (t 1,5) unter der Schwelle 0,036. Keine Uebergabe, keine Positivkontrolle, kein Test; W1/W2 bleiben blind; Pilot
  verbraucht. Nebenbefund: reale Wochen-SD des fm8-IC ~2,3..2,6 x Null-SD (k_pred ~2) - Etikett fuer alle Querschnitts-
  Designs. Vorlage an den Nutzer in DEC-101 Teil 3 (umgedrehte Hypothese nur als neue DEC mit Literatur-Prior; oder
  Klasse W ruht). Artefakte `state/runs/h32_pilot_v1/`. **Offen fuer den Nutzer:** Reihenfolge der Blindperiode (DEC-98
  E4 (b)), Umgang mit dem Pilot-Befund (DEC-101 Teil 3 Vorlage), Weiterleitung der Data-Harvest-Rueckmeldung.

## 11. Nachtrag 2026-10-26: Nutzerentscheidung zum Pilotbefund (DEC-102) - H-33 Kurzfrist-Reversal in Herleitung

- **Nutzer 2026-10-26:** Option (a) zum H-32-Pilotbefund; Reihenfolge der Blindperiode prueft er noch (offen); restliche
  PDFs kostenpflichtig, Nachlieferung nach Moeglichkeit.
- **DEC-102 (Rahmen H-33):** mom1/mom2/mom4 in negativer Richtung (Reversal 1/2/4 Wochen), fm8-Statistik wie H-32,
  W1 2024-07-01..2025-06-30 / W2 2025-07-01..2026-06-28 (REZENZ), Universum lineare USDT-Perps, Gate/Null/PK wie
  DEC-101, F-WEEK zaehlt mit, **Prior nur aus der Literatur** (sonst UNBELEGT -> Nutzerfrage mit Prior-Gitter), kein
  Pilot (verbraucht), rev_gap ausgeschlossen, Etikett "beschlossen nach Kenntnis von GL-035, Richtung Testbarkeit".
- **Laufend:** Herleitung H-33 (Opus-Agent, Auftrag `scratchpad/SPEC_H33_herleitung.md`) -> `state/herleitung_h33/`.
  Danach: adversarischer Review -> Builder (Richtung je Hypothese konfigurierbar, Modus ohne Pilot, ggf. Vorlauf v7 in
  negativer Richtung zweimal bitgleich) -> Registrierungsentwurf -> Gate-Review -> Registrierung (DEC-103) ->
  Positivkontrolle -> `--run` (Test auf W1/W2, verbraucht die Fenster fuer diese Statistik).
- **Weiter offen (Nutzer):** Reihenfolge der Blindperiode (DEC-98 E4 (b)); Weiterleitung
  `state/RUECKMELDUNG_DATA_HARVEST_PANEL_2026-10-21.md` an Data-Harvest (inkl. Rueckfrage Options-Deliveries ab 2026-08).
- **Nachtrag 11a (2026-10-26): Data-Harvest-Antwort zu den Options-Deliveries** (`state/ANTWORT_DATA_HARVEST_SETTLEMENTS_
  2026-10-26.md`, DEC-98 N6): API-Eigenschaft seit 2026-08-01, keine Luecke; Ersatz `rest.instruments`/`rest.deliveryPrices`/
  `tickers`. Rueckfrage erledigt; Weiterleitung der Rueckmeldung ist damit geschehen.
