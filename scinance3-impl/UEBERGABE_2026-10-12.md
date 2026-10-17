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
