# Gemeinsame Regeln und Leseliste fuer die PRD-Gesamtanalyse (2026-11-01)

## Auftraggeber und Ziel
Der Nutzer von Scinance fragt: Wo liegen im PRD Fehler oder ungenaue Annahmen? Welche bisher bekannten Ergebnisse
versprechen einen Edge? Die Grundidee war, Erkenntnisse aus Naturwissenschaft und Technik auf grosse Tradingdaten
anzuwenden - wie weit sind wir? Was haben wir konzeptionell und strukturell uebersehen? Welche unentdeckten
Forschungsfelder gibt es, mit den Daten des Data-Harvest-Projekts (fehlende Daten koennen dort nachbestellt werden)?
Datenfenster fuer Hypothese und OOS sollen weise genutzt werden; wir wollen nicht mehrere Jahre warten. Ziel ist eine
vollautomatische Analyseinstitution, die aus der Sandbox heraus per Schluessel auf die Datensammlung zugreift und
Hypothesen eigenstaendig entwickelt, prueft und dokumentiert, mit so wenig menschlichem Eingreifen wie moeglich.

## Harte Regeln (gelten fuer jeden Agenten)
- Nur lesen im Repo /home/user/scinance; nichts committen, nichts im Repo aendern. Deine Ausgabe geht ausschliesslich
  in die dir genannte Datei unter state/prd_analyse_2026-11-01/.
- Keine Datenrechnung: kein Harvest-Client, kein Netz, keine Siegeldateien (`*_L_window_sealed.json`,
  `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`), keine Outcome-Statistik irgendeiner Art. Das Dateninventar
  liegt als Datei vor (siehe Leseliste).
- Das Repository ist oeffentlich: keine Zugangsdaten, kein Hostname des Datendienstes, keine Modellnamen in der
  Ausgabe (sprich von Rollen: Orchestrator, Herleitungsagent, Reviewer).
- Sprache Deutsch, ASCII-safe (ae/oe/ue/ss), Markdown. Jede Behauptung mit Fundstelle (Datei, Abschnitt, DEC-/GL-/H-
  Nummer) oder ausdruecklich als Vermutung/Vorschlag markiert. Fakten, Urteile und Vorschlaege trennen. Du darfst die
  Verfassung selbst kritisieren; markiere, was eine Programmfrage des Nutzers waere (PRD Par. 8) und was der
  Orchestrator selbst entscheiden koennte. Richtung von Vorschlaegen benennen (Strenge / Testbarkeit / neutral).
- Nicht dekorativ, nicht hoeflich, nicht vage. Lieber zehn harte, belegte Punkte als dreissig weiche.
- Am Ende eine Kurzfassung (<= 12 Zeilen) an den Orchestrator.

## Leseliste (Pfade unter /home/user/scinance/)
1. scinance3-impl/PRD_SCINANCE3.md (Verfassung 3.0, Welle 1, Kandidaten A1-A5, Anhang, Wissenschafts-Exkurs Abschnitt 11)
2. scinance3-impl/CLAUDE.md (Verfassung/Orchestrierungs-Protokoll)
3. scinance3-impl/survey/ERKENNTNIS_KOMPENDIUM.md (2.0-Erbe: Hypothesen A, Konstanten B, Methoden-Lehren C,
   verworfene Ansaetze D, offene Faeden E, Datenbestand F)
4. scinance3-impl/state/decisions.md (DEC-51..DEC-103 mit Nachtraegen), state/gate_log.md (GL-032..GL-036),
   state/hypothesis_registry.md (H-27..H-33; lang, selektiv lesen)
5. scinance3-impl/state/PROGRAMM_BILANZ_2026-10-18.md (Power-Zensus, Datenbedarf, Optionen) mit Vermerken
6. scinance3-impl/STAND_2026-10-18.md (Nutzer-Stand mit Nachtraegen bis 2026-10-31) und
   scinance3-impl/UEBERGABE_2026-10-12.md (Nachtraege 10-13)
7. scinance3-impl/state/herleitung_a2/ (A2-Akte: Placebo-Design, sigma30, Null-Simulation, Pilot-Route, Reviews),
   state/herleitung_h33/, state/herleitung_hfrv/, state/herleitung_h32/ (Kurzfassungen genuegen)
8. scinance2-impl/state/PROGRAM_FINAL_REPORT.md, scinance2-impl/state/WELLE6_KANDIDATEN_SYNTHESE_2026-08-10.md,
   scinance2-impl/state/STRATEGIE_KANDIDATEN_2026-08-20.md (2.0-Ergebnisse und Kandidatenideen)
9. Dateninventar (vom Orchestrator aus dem Katalog erzeugt, Stand 2026-11-01):
   state/prd_analyse_2026-11-01/DATENINVENTAR_2026-11-01.md
   und Zugangsregeln /home/user/scinance_work/harvest_client/DATA_ACCESS.md (kein Hostname zitieren)
10. Code-Inventar: src/bybit_edge/research/ (Modulnamen, power_p1.py, h32_fm8/), tests/unit/ (nur Ueberblick)
11. Falls vorhanden (entsteht parallel): state/prd_analyse_2026-11-01/FAKTENBLATT_STATUS.md und .../out/LISTE_DEC_GL.md
    (Hilfslisten; die Primaerquellen bleiben massgeblich).
