# Architektur einer vollautomatischen Analyseinstitution (Scinance) - Herleitung

> Rolle: Herleitungsagent (Architektur), Stand 2026-11-01. ENTWURF: nichts beschlossen, nichts registriert, im Repo
> nichts geaendert. Gelesen: Leseliste 1-2, 4-7, 9-10 (PRD, Verfassung, decisions DEC-51..103, gate_log, Registry
> selektiv, Programm-Bilanz, STAND, Uebergaben 10-09/10-12, Akten A2/H-33/H-32/HFRV, Dateninventar, DATA_ACCESS,
> Code `src/bybit_edge/research/`, Git-Historie). Keine Datenrechnung, kein Harvest-Client, kein Netz, keine
> Siegeldatei. Neue Zahlen hier sind nur Normal-Arithmetik und eine synthetische Simulation (Anhang A).
>
> Kuerzel: [F] Fakt mit Fundstelle; [U] Urteil; [V] Vorschlag; [S] Schaetzung/Vermutung ohne Messbasis;
> [abg.] hier abgeleitet (Anhang A). Richtung: (Strenge) / (Testbarkeit) / (neutral). Ebene: (N) Programmfrage des
> Nutzers nach PRD Par. 8 bzw. Geld/Daten/Recht; (O) kann der Orchestrator per DEC entscheiden.
> Pfade relativ zu `scinance3-impl/`, sofern nicht anders angegeben.

---

## 0. Befund in Kuerze

1. [F] Seit Welle 1 wurden sechs Kandidaten bearbeitet (A3/H-28..30, A1/H-31, H-27, H-32, H-33, A2). Ergebnis: null
   urteilstragende p-Werte; GL-032..GL-036 sind GL-012 vor Lauf, Registrierung oder Uebergabe, A2 steht per Default auf
   GL-012 vor der Registrierung (DEC-103 Nachtrag 1 (10)). [U] Die Maschine ist nicht der Engpass: Maschinenzeit je
   Feasibility-Befund 1 bis ~30 Stunden; die verstrichene Zeit wird von Nutzerrueckfragen (1-5 Tage je Frage, eine seit
   14 Tagen offen) und Datenauftraegen ueber den Nutzer bestimmt (Abschnitt 1.4).
2. [U] Drei Engpaesse: (a) die Literatur-Prior-Pflicht (Verfassung Arbeitsregel 4, DEC-102 E3) bei gesperrten
   Volltexten erzeugt je Kandidat eine Programmfrage (A1 theta, H-33, A2 V-5b; H-32 erst nach PDF-Upload); (b) der
   Datenkanal zu Data-Harvest laeuft ueber den Nutzer (10 aus-, 7 eingehende Dokumente in drei Wochen); (c) Power
   (Wurzelgesetz, PROGRAMM_BILANZ 1.2). Automation loest (a) und (b), nicht (c).
3. [F] Reproduzierbarkeitsschuld: die Akte verweist 61-mal (eindeutig) auf `scratchpad/...`-Pfade (Specs, Herleitungs-,
   Review- und Nachrechnungsskripte, Extrakte), keiner davon ist versioniert; der Scratch-Bereich ist seit 2026-10-31
   nicht mehr nutzbar (Uebergabe 10-12 Nachtrag 13).
4. [F] Siegel haengen an Disziplin: aus der committeten `herleitung_a2/a2_vorarbeit.json` ist der Betrag eines
   Pilotkontrasts bis auf zwei Kandidaten rekonstruierbar (B-2, DEC-103 Nachtrag 1 (2)); Waechter gibt es nur
   paketweise (`h32_fm8/panel_cut.py`) oder als Einmalskript ausserhalb des Repos (`channel_scan.py`).
5. [F] Regeln als Code existieren punktuell: `power_p1.py` (generisch), `h32_fm8` (Schema, Pins, Pilot-Sperre,
   Schnitt-Waechter, skalierte Null; 5.794 Zeilen fuer EINE Hypothesenfamilie). Das Registry-Format mit Linter
   (PRD 3.4, Bau-Reihenfolge 9.3 Schritt 5) wurde nie beschlossen; seine Nummern DEC-58/59 sind anderweitig vergeben.
6. [V] Soll: zehn Bausteine (2.1). Kern: Ledger als einzige Wahrheit, Fensterregister mit K- und FDR-Buch,
   Datenzugangsschicht mit Statistikklassen und Schluesseltrennung, Feasibility-Rechner auf einem Nuisance-Katalog,
   generischer Registrierungs-/Lauf-/Kontrollrahmen, Entscheidungswarteschlange mit Default und Frist.
7. [V] Fenster-Politik (3): Zonen X/V/C je Datenfamilie, Kohorten-Stichtage statt Reihenfolge-Entscheidungen,
   prospektive Konfirmation fuer agentenbekannte Groessen mit gruppensequentieller Auswertung. Fehlerrate je Test
   unveraendert (0,25 % gemeinsam); geteilte Scheiben kosten bei m = 4 den Datenfaktor 1,54 statt 4x Serialisierung;
   E[N] unter H1 0,81 der Festgroesse, bei doppeltem Effekt 0,51 [abg.]. Das Wurzelgesetz bleibt.
8. [V] Nutzer: zehn einmalige Entscheidungen (5.3); danach nur Programmrichtung, Geld, Datenquellen/Schluessel, Recht -
   gesammelt woechentlich, nie auf dem kritischen Pfad ausser bei Geld/Recht.
9. [V] Reihenfolge: Schadensbegrenzung (Versionierung, Kanal-Scan, Kostenbuch) -> Ledger/Schema/Linter ->
   Register/Datenzugang -> Feasibility-Rechner -> Lauf-Rahmen -> Generator und Takt. Grob 120-180 Agentenstunden
   in 90 Tagen [S].

---

## 1. Ist-Zustand

### 1.1 Was heute automatisiert ist

| Komponente | Stand | Fundstelle | Grenze |
|---|---|---|---|
| Datenclient `harvest_data.py` | `catalog`, `load` (Dedup, Luecken-Warnung), `gaps`; Secrets aus der Umgebung | Verfassung "Marktdaten"; DATA_ACCESS 4-5 | je Sitzung neu vom Server geholt, nicht im Repo, Version nicht gepinnt (Uebergabe 10-09 Abschnitt 4/9); ~2 MB/s geteilt; keine Siegel-Logik |
| Katalog-Inventar | vom Orchestrator erzeugt | `DATENINVENTAR_2026-11-01.md` | Handanstoss |
| Power/MDE/Zuordnung | `power_p1.py`, generisch, 32 Tests | DEC-94 (8); PROGRAMM_BILANZ 6 | wird aufgerufen, nicht erzwungen |
| A3-Treiber | `wp13_xsec` mit Startsperre ueber registrierten sha256 | DEC-75 E2, DEC-90 | 6.970 Zeilen, hypothesenspezifisch |
| H-32-Treiber | `h32_fm8`: Schema-Pruefung der YAML, Daten-/Runner-/Universums-Pins, Panel-Schnitt-Waechter, Genau-ein-Pilot mit Versuchsmarker, skalierte Null, Positivkontrolle in Produktionskonfiguration, PP3-Trockenprobe | DEC-101 E1-E10; `src/bybit_edge/research/h32_fm8/` | 5.794 Zeilen, Konstanten fest auf H-32 (`constants.py`) |
| Registrierungsdateien | YAML mit sha256 als Startsperre | `state/registered/`; DEC-90, DEC-101 E9 | Registry-Text bleibt Markdown, kein Linter |
| Autopilot Nutzer-PC | Git als Auftragskanal | DEC-79 | seit DEC-83 Rueckfall; letzter Auftrag 2026-10-09 (`state/queue/auftrag.json`) |
| Testsuite | 2.399 passed / 3 Altfaelle | Uebergabe 10-12 Nachtrag 10d | - |
| Agentenrollen | Herleitung, adversarischer Review, Bau, Gate-Audit; Volltexte in Dateien, Kurzfassungen <= 10 Zeilen | Verfassung "Modell- und Teampolitik" | Auftrags-Specs lagen im Scratch (verloren) |
| Weckruf | geplante Nachricht an die Sitzung | Uebergabe 10-09 Abschnitt 3 | kein Institutions-Takt |

### 1.2 Was der Orchestrator von Hand macht

| Taetigkeit | Beleg | Folge |
|---|---|---|
| Auftraege an Agenten schreiben (`SPEC_*.md`) | Uebergabe 10-12 Nachtraege 10/11; `/home/user/scinance_work/drafts/` | Specs ausserhalb des Repos, teils verloren |
| Abnahme: Tests, Fingerprints, Diff-Grenzen | Verfassung "Regeln" (nie auf Zuruf) | richtig, aber unversioniert |
| Nachrechnung mit eigenem Code | `herleitung_a2/NACHRECHNUNG_ORCHESTRATOR.md` (Skripte unter `scratchpad/orch_check/` bzw. `scinance_work/orch_check/`) | nicht reproduzierbar aus dem Repo |
| Kanal-Scan vor Commit | DEC-103 Nachtrag 1 (1) | Einmalskript, kein CI |
| Gabelungen entscheiden, DEC/GL/Registry-Texte, Nachtraege, Errata | DEC-93 E3, DEC-101 Teil 1-3; PROGRAMM_BILANZ Vermerk E-1 ("angekuendigter Eintrag war unterblieben") | Dokumentdrift |
| Kontaminations-/C.17-Inventuren | DEC-95 E2 (Liste aus DEC-94 korrigiert), DEC-97 A-3 | fehleranfaellig |
| Commits, Push auf zwei Branches | Uebergabe 10-12 Abschnitt 1 | Handschritt je Ergebnis |
| Data-Harvest-Korrespondenz, Katalog-Pruefungen | `state/ANFRAGE_*`, `RUECKMELDUNG_*`; DEC-96 N1-N3 | Weiterleitung durch den Nutzer |
| Uebergabe-/Stand-Dokumente | Uebergabe 10-12 mit 13 Nachtraegen; STAND mit 8 Nachtraegen | Wissen in Prosa |

### 1.3 Was den Nutzer braucht (2026-10-09..2026-10-31)

| Art | Anzahl | Belege | Latenz |
|---|---|---|---|
| Programmentscheidungen | 7 getroffen, 2 offen | DEC-83 (10-10), DEC-98 (10-18), DEC-99 (10-20), DEC-102 (10-26), GL-036 (10-27), Vorarbeiten (Uebergabe Nachtrag 12), DEC-103 (10-31); offen: Reihenfolge der Blindperiode (DEC-98 E4 (b), seit 10-18), A2 P-0..P-3 (seit 10-31) | 1-5 Tage; offen 14 Tage |
| Datenauftraege weiterleiten | 10 aus, 7 ein | `state/ANFRAGE_*` (4), `AUFTRAG_*` (2), `RUECKMELDUNG_*` (4), `ANTWORT_*` (7) | H-27: ~4 Tage bis Katalog (DEC-96 N3) |
| Volltexte | 12 PDFs hochgeladen; kostenpflichtige nicht beschaffbar | `BELEGE_AUS_PDF_2026-10-20.md`; DEC-103 | - |
| Zugang | Secrets, Netzfreigaben | DEC-80; Uebergabe Nachtrag 13 (Netzsperre fuer Volltexte) | einmalig, teils offen |

### 1.4 Zeit und Kosten je Hypothese

Zeiten aus Commit-Zeitstempeln; Token sind [S]: die Akte fuehrt keine Token-Buchhaltung. Methode: je Agentenlauf
Kontext 0,1-0,2 Mio Token x 30-100 Werkzeugrunden = 3-15 Mio verarbeitete Token (ueberwiegend Kontext-Wiederholung),
Ausgabe 0,03-0,1 Mio; Basis sind die Groessen der gelesenen und erzeugten Dateien (~3,5 Byte je Token).

| Kandidat | Zeitraum | Maschine aktiv | Warten auf Nutzer | Warten auf Daten | Agentenlaeufe | Akte | Token [S] | Ergebnis |
|---|---|---|---|---|---|---|---|---|
| A3 (H-28..30) | 09-21 -> 10-12 (21 Tage) | 8 Vorlaeufe v1..v5e (je 1,5-4 h CPU) + ~9 Sitzungstage | Sitzungsluecke 09-28..10-09 (Ursache nicht in der Akte) | Autopilot-Laeufe | 3 Fassungen, 3 Reviews, 2 Gate-Audits, >= 6 Bauauftraege | Akte 95 KB, Reviews 73 KB, Registry ~60 KB | 50-250 Mio | GL-032 |
| A1 (H-31) | 10-12 24:00 -> 10-13 09:36 | <= 10 h | - | - | Herleitung + Review | 308 KB | 5-30 Mio | GL-033 |
| H-27 | 10-13 12:48 -> 10-17 14:18 | ~1,5 h nach Datenankunft + Stufe 0 | 2 Weiterleitungen | ~4 Tage (Backfill, Katalog-Stillstand) | 2 Herleitungsstufen + Review | 354 KB | 10-45 Mio | GL-034 |
| H-32 | 10-18 10:28 -> 10-21 20:36 | ~30 h (CPU: v6a 2 h, v6b 2 x 2 h, Pilot Minuten) | ~2,2 Tage (PDFs, Zustimmung DEC-99) | Klaerung DEC-100 ~20 h (Daten waren schon da) | Herleitung, Review, 3 Bauauftraege, Gate-Review (VETO), Nachpruefung | 299 KB + 5.794 Zeilen Code + Tests | 25-120 Mio | GL-035 |
| H-33 | 10-21 20:36 -> 10-27 17:17 | ~1 h (Herleitung + Review, Commit 3b9d29a) | 4,6 Tage (Optionswahl) + 1,2 Tage (Prior-Vorlage) | - | Herleitung + Review | 318 KB | 5-30 Mio | GL-036 |
| A2 (Vorarbeit A/B/C) | 10-27 -> offen | ~2 Sitzungstage | 10-29 -> 10-31; seit 10-31 offen | Negativ-Panel (Auftrag offen) | 2 Herleitungen, 2 Reviews, 3 Nachrechnungen | 1,74 MB (220 KB Text) | 20-100 Mio | GL-012 per Default; Siegel-Befund B-2 |

### 1.5 Urteil: wohin Zeit und Kosten gehen

1. [U] **Nutzerlatenz liegt auf dem kritischen Pfad.** H-33: 1 h Maschine gegen 5,8 Tage Warten; H-32: 30 h gegen
   2,2 Tage; die Reihenfolge-Frage blockiert seit 14 Tagen jede Rechnung auf Daten ab 2026-07-01 (DEC-98 E4).
2. [U] **Die Prior-Pflicht ist der haeufigste Blocker**, nicht die Daten: A1 (theta UNBELEGT, DEC-93 E2), H-33
   (DEC-102 N1 (1)), A2 (V-5b, DEC-103), H-32 vor dem Upload (DEC-98 Nachtrag). Volltexte sind aus der Sandbox nicht
   erreichbar (`RECHERCHE_BELEGE_2026-10-18.md` Abschnitt 0: Preprint-Server, SSRN, NBER, Deribit-Doku gesperrt; nur
   Websuche erreichbar).
3. [U] **Feasibility kostet jedes Mal eine volle Herleitung plus Review**, weil die Nuisance je Kandidat neu gemessen
   wird. A1, H-27 und H-33 endeten genau dort. Die Programm-Bilanz hat dieselbe Rechnung fuer alle Kandidaten in einem
   Lauf gemacht (`power_p1`, < 1 s, PROGRAMM_BILANZ 6) - der Rechner existiert, der Nuisance-Katalog nicht.
4. [U] **Hypothesenspezifischer Code und Mehrfachfassungen** sind die groessten Kostenposten (A3: 3 Fassungen, 8
   Vorlaeufe; H-32: 5,8 Tsd. Zeilen, Regel U -> U-3 -> U-4 innerhalb von Stunden, DEC-101 E7). Drift wird durch
   Reviews gefangen statt durch Struktur verhindert.
5. [F/S] **Wissen in Prosa skaliert nicht.** Die neun Kerndokumente der Leseliste (PRD, Verfassung, decisions,
   Registry, Gate-Log, Uebergabe 10-12, STAND, Bilanz, Kompendium) haben 656.775 Byte, `decisions.md` allein 221.371
   Byte (DEC-103 Nachtrag 1 ist eine einzige Zeile von ~10 KB). [S] Das sind ~0,17-0,2 Mio Token Pflichtlektuere je
   Agent - mehr, als ein Agent sicher ueberblickt; bindende Regeln stehen verstreut in Nachtraegen.

### 1.6 Befunde zur Verfassung (Kritik, mit Ebene)

| Nr. | Befund | Fundstelle | Ebene |
|---|---|---|---|
| K-1 | "Niemals den Nutzer fragen" kollidiert mit der Prior-Pflicht: jede UNBELEGT-Blockade wird zur Programmfrage. Eine Institution braucht eine Prior-Quelle, die sie selbst erzeugen darf | Autonomie 3; Arbeitsregel 4; DEC-102 E3; DEC-99 | (N) |
| K-2 | Die Ueber-Familie F-WEEK wird "am Wellenschluss" korrigiert, Urteile sind bis dahin vorlaeufig; im Dauerbetrieb gibt es keinen Wellenschluss | DEC-74 (e); DEC-99 (7); C.16 | (N), Verfahren neutral waehlbar |
| K-3 | Registry-Format und Linter (PRD 3.4) und das Konstantenmodul mit `constants_hash` (3.3.6) sind nie gebaut; die vorgesehenen Nummern DEC-58/59 tragen andere Beschluesse | PRD 3.4, 9.3 Schritt 5; decisions DEC-58/59; kein Linter in `src/`, `scripts/`, `tests/` | (O) |
| K-4 | Abnahme "selbst nachvollziehen" ist richtig, aber die Nachrechnung ist nicht versioniert | Verfassung Teampolitik; NACHRECHNUNG_ORCHESTRATOR (A2, HFRV) | (O) |
| K-5 | Das oeffentliche Repo macht jedes Siegel-Leck irreversibel (kein History-Rewrite) | DEC-103 Nachtrag 1 (2a); Uebergabe 10-09 Abschnitt 1 | (N, Recht) |
| K-6 | Die Null-Zensus-Klausel sperrt systematische Screens als Ideenquelle; DEC-99 (4) hat fuer Pilotfenster bereits eine Abgrenzung geschaffen | DEC-58 E2; DEC-99 (4) | (N) |
| K-7 | Blindheit historischer Fenster gegen Vorwissen der Agenten wird je Kandidat entschieden, nicht als Regel | DEC-96 E1 ("Vorwissen der Agenten ueber Krypto-Vol bis Mitte 2026") | (O), Strenge |
| K-8 | Die Verfassung bindet Rollen an benannte Modellversionen statt an Funktion und Pruefpflichten | Verfassung "Modell- und Teampolitik" | (O) |

---

## 2. Soll-Architektur in Bausteinen

### 2.0 Leitprinzipien [V]

1. **Ledger ist die Wahrheit, Prosa ist Sicht.** Jede Entscheidung, Registrierung, jeder Lauf und Datenzugriff ist ein
   maschinenlesbarer, append-only Eintrag; Markdown wird gerendert.
2. **Regeln als Code, Gate als Daten.** Was eine DEC bindend festlegt, prueft ein Test oder Linter; Gate-Bedingungen
   stehen als Ausdruck in der Registrierung und werden von einer einzigen Bibliothek ausgewertet.
3. **Siegel durch Technik, nicht durch Disziplin.** Datenzugang nur ueber eine Schicht mit Zweck, Familie und
   Statistikklasse; versiegelte Daten nur in einer Umgebung, in der nur registrierte Laeufe starten.
4. **Keine Zahl ohne versioniertes Skript.** Jede in der Akte zitierte Zahl verweist auf eine versionierte Datei.
5. **Mensch nur fuer Programmrichtung, Geld, Daten/Schluessel, Recht** - mit Default und Frist.

### 2.1 Bausteintabelle

| Nr. | Baustein | Kern (Soll) | Ersetzt / verallgemeinert (Ist) | Richtung | Ebene | Phase |
|---|---|---|---|---|---|---|
| a1 | Datenzugangsschicht + Zugriffsbuch | eine Ladefunktion mit Zweck, Familie, Scheibe, Statistikklasse; Datumsschnitt vor jeder Rechnung; jeder Zugriff im Ledger | `h32_fm8/panel_cut.py`; Hash-Waechter in Einzelskripten (A2); h27-Waechter (Scratch, verloren) | Strenge | O | F2 |
| a2 | Siegel-Engine | Klassenmatrix Zone x Klasse (S0-S3), Ausgabe-Allowlist, Klassen-Deklaration je veroeffentlichter Streuung, globaler Kanal-Scan in CI | DEC-96 E3; DEC-103 N1 (2c); `channel_scan.py` ausserhalb des Repos | Strenge | O | F0/F2 |
| a3 | Schluesseltrennung + Datenvertraege | Explorations- und Konfirmationsumgebung mit getrennten Schluesseln; taegliche Katalog-Checks; Universumsregel als Daten | Disziplin; DEC-96 N1-N3, DEC-100, DEC-101 B-1 | Strenge | N (Datenauftrag, Secrets) | F2/F6 |
| b | Generator + Nuisance-Katalog + Feasibility-Rechner | Ideenkarte mit Mechanik-Checkliste; registrierte X-Screens mit K; Zuordnung je Fensterlaenge in Minuten | Einzelherleitungen (A1, H-27, H-33); Bilanz-Skript (Scratch) | Strenge (Vorfilter), Testbarkeit (Screens) | O; Screens N (E-3) | F3/F5 |
| c | Registrierungsschema + Linter + Gate als Daten | JSON-Schema der zwoelf Pflichtzeilen; Referenz statt nackter Zahl; Hash-Pin der Alt-Eintraege; `power_p1`-Pflicht; Fensterreservierung | PRD 3.4 (nie gebaut); `h32_fm8/schema.py` | Strenge | O | F1/F4 |
| d | Fensterregister + K-Buch + FDR-Buch | Scheiben x Statistikfamilien mit Zustaenden; Kohorten; jede Lage-Statistik verbucht | DEC-98 E1 (d); DEC-99 (3)(5)(7); Reihenfolge-Frage | neutral; Strenge bei Verbuchung | N (E-1, E-2) | F2/F6 |
| e | Lauf-Rahmen + Takt | Manifest, Runner mit Startsperre, Checkpoints, N >= 3, Artefakte DEC-53; taeglicher Takt mit frischer Sitzung | Autopilot DEC-79; Handstarts; h32/wp13-Treiber | neutral | O | F4/F5 |
| f | Pruefschleifen | Maschine vor Mensch; Nachrechnung als Code; generischer PK/NK-Harness; Gabelungsregister; Abweisungsliste als Tests | NACHRECHNUNG_* (Hand); Reviews | Strenge | O | F4 |
| g | Ledger + Sichten + Provenienz + Digest + Kostenbuch | Hash-Kette; generiertes Markdown; C.17 aus dem Zugriffsbuch; Zahlen als Platzhalter auf Artefakte | decisions.md 221 KB; Uebergaben mit 13 Nachtraegen | neutral | O | F0/F1 |
| h | Entscheidungswarteschlange | vier Klassen; Default + Frist; woechentliche Sammelvorlage | Einzelvorlagen (VORLAGE_NUTZER_H33, PILOT_ROUTE_A2 Abschnitt 8) | neutral | N (einmalig) | F5 |

### 2.2 (a) Datenzugang, Cache und Siegel-Regeln als Code [V]

1. **Client pinnen.** sha256 der Client-Version je Lauf ins Manifest; Versionswechsel ist ein Ledger-Eintrag. Ins
   oeffentliche Repo erst nach Pruefung auf Hostnamen/Schluessel (Uebergabe 10-09 Abschnitt 4). (neutral, O)
2. **Datenzugangsschicht (DAL).** Einzige zulaessige Ladefunktion vor `hd.load`:
   `load_for(zweck, familie, scheibe, klasse, registrierung)`. Sie fragt das Fensterregister, schneidet Tage vor jeder
   Rechnung (Verallgemeinerung von `panel_cut.py`, DEC-99 (3)), verweigert laut (C.14) und schreibt das Zugriffsbuch
   (Strom, Symbole, Tage, Zweck, Code-Commit, Ausgabeklasse). (Strenge, O)
3. **Statistikklassen.** S0 Vollstaendigkeit (Zeilen, Luecken, Zeitstempel, Schema - ueberall erlaubt, im Siegelbereich
   nur aus dem Katalog, DEC-96 E3); S1 Streuung/Abhaengigkeit ohne Lage (DEC-94 (5) (i)); S2 Lage/Vorzeichen (nur in
   einer registrierten Pilot-, Screen- oder Teststufe, DEC-99); S3 Gate-Bit (Zwischenblicke, 3.3 R-3). Die Matrix
   Zone x Familie x Klasse steht im Register, nicht im Kopf des Agenten.
4. **Ausgabe-Allowlist und Kanal-Scan.** S1-Ausgaben nur in registrierten Schemata; nur disjunkte Partitionen, nie
   Eltern- und Teilklasse zugleich, keine Vereinigungs-Streuung (DEC-103 N1 (2c)). Jede veroeffentlichte Streuung traegt
   eine Klassen-Deklaration (Reihe, Slot, Praedikat, n), damit ein globaler Scan ueber ALLE versionierten Dateien
   Schachtelungen findet - auch dateiuebergreifend (G-C9 in DEC-103 N1 (1)) und gegen fruehere Fassungen
   (Differenzkanal). Runden schliesst den Kanal nicht (REVIEW_A2_TEILC: mit 4 Stellen noch 0,02..0,55 bp). Der Scan
   blockiert den Commit (CI). Bekannte Kanaltypen werden Tests; unbekannte Kanaele hoeherer Ordnung (Quantile,
   Kurtosis) bleiben Restrisiko. (Strenge, O)
5. **Schluesseltrennung.** Zwei Cloud-Umgebungen: Exploration mit einem Schluessel ohne Lesezugriff auf versiegelte
   Partitionen (Archivpfad enthaelt `date=`, Sperre als Praefix-Regel), Konfirmation mit vollem Schluessel, in der nur
   der Runner mit registrierter Datei laeuft. Ob der Datendienst praefixbasierte Rechte kann: UNBELEGT (Datenauftrag).
   Wirkung: Lage im Siegelbereich ist fuer Agenten technisch unerreichbar, auch versehentlich (vgl. DEC-97 A-3:
   Katalog-Bytesummen im Blindbereich ausgegeben). (Strenge, N)
6. **Cache.** Inhaltsadressiert (Partitionsschluessel + Katalog-Pruefsumme), wegwerfbar; zitiert wird das Manifest
   (Strom, Symbole, Tage, Katalogstand, Client-sha), nie ein lokaler Extrakt. Versiegelte Extrakte ausserhalb des Repos
   (Uebergabe Nachtrag 13) entfallen in der Explorationsumgebung. (neutral, O)
7. **Datenvertraege.** Taeglicher Katalog-Check je benutztem Strom (Zeilen, Luecken, Status, Schema, Herkunftsmischung
   Archiv/Live wie DEC-96 N2) mit lautem Alarm; Universumsregel je Familie als Daten (DEC-101 E1). (Strenge, O)

### 2.3 (b) Hypothesen-Generator [V]

1. **Ideenkarte (YAML, eine Seite).** Klasse P/W/E; Zahler und sein Bestand nach 2024 (PRD 3.3.9c, L-16); Horizont >=
   Tageshorizont (Verfassung, "vier Zahlen": unter Tag nur Kosten-/Zensus-Messung); oekonomische Mindestmagnitude als
   Etikett, nie Gate (C.2); Statistikfamilie (Outcome, Horizont, Universum, Signalfamilie); unabhaengige Einheiten je
   Jahr; Datenstrom im Katalog mit Inhaltsprobe (C.8); Vorwissensklasse (agentenbekannt/aggregiert gegen obskur,
   DEC-96 E1); Prior-Band mit Quelle oder "aus X-Zone".
2. **Quellen und ihre Grenzen.** (i) Literatur nur als Suchauszug [sek] - taugt fuer Mechanismen und Prior-BAENDER,
   nicht fuer belegte Prioren (RECHERCHE_BELEGE Abschnitt 0); Volltexte nur nach Netzfreigabe (E-8) oder Upload.
   (ii) Registrierte X-Screens: festes K, festes Selektionsverfahren, selektionsbereinigter Schaetzer (DEC-99 (3)
   `mu_sel`), mechanische Uebergabe nach V/C; K zaehlt voll im K-Buch. Abgrenzung zur Null-Zensus-Klausel DEC-58 E2
   analog DEC-99 (4) - Programmfrage (N, Testbarkeit). (iii) Mechanik-Checkliste Zahler/Horizont/Wand als Pflichtfilter.
   (iv) Hebel-Matrix (PROGRAMM_BILANZ 2.8): bevorzugt werden Designs mit vielen unabhaengigen Einheiten und
   Neutralisierung (fm8 -81 % Dauer; Ereignisse 52 je Jahr).
3. **Feasibility-Rechner als erstes Tor (C.12).** `n_noetig = c * (2,4865 * SD / prior)^2` je Fenster
   (PROGRAMM_BILANZ 1.2) und `power_p1.assign_regime`, mit SD und c aus einem **Nuisance-Katalog** (S1, nur X-Zone, je
   Standardfamilie einmal gemessen). Ergebnis in Minuten; GL-012-Ideen werden verbucht, nicht hergeleitet. Der Katalog
   muss die reale Streuung tragen, nicht nur die Nullsimulation: die reale fm8-Wochen-SD lag beim 2,3..2,6-fachen der
   Null-SD (GL-035 Nebenbefund; DEC-94 (5)). (Strenge, O)
4. **Budget.** Wochenkontingent fuer Generator und Herleitungen; Stopp bei Leerlauf (E-9).

### 2.4 (c) Maschinenlesbare Vorregistrierung [V]

1. **Schema.** JSON-Schema fuer die zwoelf Pflichtzeilen (PRD 3.3) und den YAML-Block (PRD 3.4), ergaenzt um DEC-94
   (`alpha`, `z_krit`, `mde_faktor` getrennt), DEC-99 (`pilot_window`, `handover_rule`), DEC-101 (`universe`,
   `null_scaling`, `runner`, `data_fingerprints`), Kohorte, Fensterzuweisung (Register-IDs), Gabelungsliste mit
   Richtung, generierte C.17-Liste, Budget. Kein Feld hat einen Default; UNBELEGT ist ein Fehler (Arbeitsregel 4).
2. **Linter** = der nie beschlossene Registry-Entwurf aus PRD 3.4 woertlich: (a) loud fail, wenn nicht parsebar;
   (b) jede Schwelle und jeder Nulleffekt mit Referenz `pfad#json-zeiger` auf ein versioniertes Artefakt plus Test-ID,
   nie ein nackter Skalar; (c) append-only per Hash-Pin aller Alt-Eintraege. Zusaetzlich: Referenzziel muss im Repo
   versioniert sein; die Power-Zeile wird mit `power_p1` reproduziert; der Doppelausweis DEC-94 (9) wird erzeugt.
3. **Power-Vorpruefung und Fensterzuweisung.** Der Linter ruft den Feasibility-Rechner mit der registrierten SE-Regel
   (DEC-94 (3), Lehre DEC-91/92) und fragt das Register nach freien Scheiben fuer die Familie; Reservierung ist eine
   Ledger-Transaktion mit Kohorte.
4. **Gate als Daten.** Gate-Bedingungen als Ausdrucksbaum (Statistik, Richtung, `z_krit`, Null-Quantil, Skalierung,
   Screens), ausgewertet von einer generischen Gate-Bibliothek; hypothesenspezifisch bleibt nur der Schaetzer.
   Verhindert Text/Code-Drift wie DEC-87 (Gate (5) im Lauf nicht geprueft, Bounce-Kill nur Etikett). (Strenge, O)

### 2.5 (d) Fensterregister / Lockbox [V]

- **Datenmodell.** Scheibe = (Datenfamilie, Zeitraum). Zustand je Statistikfamilie: `blind`, `S1-offen`,
  `pilot-verbraucht (H, sha)`, `test-verbraucht (H, sha)`, `offen`; Siegel mit Eigentuemer (Kohorte), Bedingung und
  Vorwissens-Status; Herkunft jedes Zustands als Ledger-Verweis.
- **Transaktionen.** reservieren (Registrierung) -> oeffnen (Laufstart, erst nach bestandener Positivkontrolle) ->
  verbrauchen (Ergebnis-sha) -> freigeben (Rotation in X, 3.3 R-4). Genau-ein-Pilot (DEC-99 (3), DEC-101 E3/E9a) wird
  eine Register-Eigenschaft statt Paketcode.
- **Familienkorrelation.** Konservative Standardregel nach DEC-99 (5): gleiches Outcome, ueberlappendes Universum und
  gleicher Horizont = gleiche Familie; Ausnahmen nur per DEC mit Simulation unter der Null.
- **K-Buch.** Jede S2-Statistik in jeder Zone - Screens, Pilot-Varianten, verworfene Fassungen (v6a, DEC-101 E1),
  abgebrochene Laeufe (Versuchsmarker) - mit p, falls gerechnet. "GL-012 vor jedem Datenblick" kostet kein alpha
  (DEC-99 (7)), wird aber als Gabelung gezaehlt.
- **FDR-Buch.** Konfirmatorische p-Werte in Eingangsreihenfolge; Verfahren nach E-2 (3.4).

### 2.6 (e) Ausfuehrung [V]

- **Lauf-Manifest.** Registrierungs-sha, Code-Commit, Umgebungs-Lock (Paketversionen; Falle "Container verliert
  Pakete", Uebergabe 10-09 Abschnitt 8), Client-sha, Katalogstand, Partition-Pruefsummen, Seeds, erwartete Laufzeit.
  Der Runner verweigert einen schmutzigen Arbeitsbaum und jede Abweichung von den Pins (wie `h32_fm8/checks.py`).
- **Laufzeitgrenzen.** In der Cloud liefen v5c/v5d/v5e 101/120/128 min und v6a/v6b ~2 h je Lauf (Commits 10-12;
  Uebergabe Nachtrag 10: v6a 13:28..15:28, 10b/c: v6b zweimal); WP-10(B) mit 500 min lief nur auf dem PC (DEC-78); Sitzungen werden bei Leerlauf
  abgeraeumt (DEC-79); 1 GB laedt in ~8 min (DATA_ACCESS 5). Folge: Jobs in checkpointbare Stuecke <= ~90 min (T3),
  idempotent, Fortsetzung per Weckruf; Orderbuch-Grosslaeufe nur ueber den PC-Rueckfall oder gar nicht. Meldegrenze
  24 h und GPU 0 (DEC-57) im Budget-Waechter.
- **Takt.** Geplante Aufgabe "Institutions-Takt", taeglich, jede Ausfuehrung in frischer Sitzung, Zustand nur aus
  Repo/Ledger: (1) Datenvertraege, (2) faellige Jobs und Zwischenblicke, (3) Kohortenstichtage, (4) Digest.
  Woechentlich Generator und Feasibility-Rechner, quartalsweise Kohortenschluss. Eine Integrationslinie mit
  Fast-Forward (Uebergabe 10-12 Abschnitt 1); Ledger-Eintraege als Einzeldateien, damit parallele Sitzungen
  konfliktfrei schreiben.
- **Determinismus.** T2 mit N >= 3 und Fingerprint im Manifest (C.7; heute v6b nur x2); gemeinsame Zufallszahlen in
  Kalibrierungssuchen (Lehre DEC-81); eingefrorene Datenstaende je Registrierung.
- **Artefakte.** Generischer Writer fuer DEC-53 (Cluster-Serie + Replikate oder Seed/Generator-Fingerprint) mit T7.

### 2.7 (f) Pruefschleifen [V]

1. **Maschine vor Mensch.** Reihenfolge: Linter -> Kanal-Scan -> CI (T0-T7) -> Nachrechnung als Code -> adversarischer
   Review mit Veto (Rolle bleibt) -> Orchestrator.
2. **Nachrechnung als Code.** Der Reviewer schreibt eine zweite, unabhaengige Implementierung der urteilstragenden
   Zahlen, versioniert unter `verify/<id>/`; ein Job vergleicht mit Toleranz. Ersetzt die Handskripte hinter
   NACHRECHNUNG_ORCHESTRATOR; der Orchestrator prueft Abweichungsbericht und Diff statt selbst zu rechnen. (neutral, O)
3. **Generischer Positiv-/Negativkontroll-Harness** in Produktionskonfiguration: Injektion am MDE80 des bindenden
   Fensters in eine Kontrollwelt mit realer Streuung (DEC-94 (5), DEC-101 E8), Kriterium "erwartete PASS-Quote minus
   2,3263 Binomial-SE" (DEC-103 N1 (8e)). PRD 3.3.8 verlangt sie ab 1 h Laufzeit; [V] vor jedem Lauf, weil billig und
   weil sie den teuersten Fehler der Akte gefangen hat (DEC-91). (Strenge)
4. **Gabelungsregister.** Jede Entscheidungsvorlage traegt ihre Richtung; liegt mehr als die Haelfte einer Herleitung
   in Richtung Testbarkeit, ist ein Pflicht-Vetopunkt des Reviews faellig (Muster DEC-93 E3: alle sechs EV Richtung
   Testbarkeit). (Strenge)
5. **Abweisungsliste als Tests.** Bekannte Fehlerklassen werden Lint-Regeln: Boden-SE statt registrierter SE
   (DEC-91/92); MDE-Faktor als Schwelle (DEC-94 (1)); Vereinigungs-Streuung (DEC-103 N1); Null-Renditen statt NaN
   (DEC-85 D2); Universum mit USDC-Zwillingen/datierten Futures (DEC-101 B-1).
6. [S] **Review-Unabhaengigkeit.** Herleitung und Review aus derselben Agentenfamilie haben korrelierte blinde Flecken
   (B-2 vom Vorarbeit-Review uebersehen, erst im Teil-C-Review gefunden, DEC-103 N1 (2)); die mechanischen Pruefungen
   sind die eigentliche zweite Linie.

### 2.8 (g) Dokumentation [V]

- **Ledger.** Append-only, eine JSON-Datei je Eintrag; Typen DEC, GL, REG, RUN, ACCESS, FORK, USER, COST; Zeit,
  Vorgaenger-Hash, Nutzlast, Referenzen auf versionierte Artefakte; Hash-Kette in CI geprueft.
- **Sichten.** `decisions.md`, `gate_log.md`, `hypothesis_registry.md` werden ab Stichtag als Sichten gerendert; der
  Altbestand bleibt bytegleich (C.1). Eine konsolidierte Sicht "geltende Regeln" (Groessenordnung 30 KB, jede Zeile mit
  beschliessender DEC) ersetzt die Pflichtlektuere der Historie.
- **Zahlen-Provenienz.** Zahlen in Akten-Texten sind Platzhalter auf `artefakt#zeiger`, beim Rendern aufgeloest; ein
  unterbliebener Nachtrag wie PROGRAMM_BILANZ E-1 waere ein CI-Fehler.
- **C.17 generiert.** "Gesehen" = alle S1/S2-Ausgaben, die Familie und Scheibe einer neuen Registrierung beruehren, aus
  dem Zugriffsbuch; ersetzt Hand-Inventuren (DEC-95 E2 korrigierte die Liste von DEC-94).
- **Nutzerbericht.** Woechentlicher Digest (neue GL, offene Entscheidungen mit Default und Frist, Datenauftraege,
  Kosten); quartalsweise ein STAND in heutiger Form.
- **Kostenbuch.** Token, CPU-Minuten, Agentenlaeufe je Hypothese und Baustein - heute nicht vorhanden (1.4).

### 2.9 (h) Menschliche Eingriffspunkte [V]

| Klasse | Beispiele | Verhalten bei Stille |
|---|---|---|
| Programmrichtung (PRD Par. 8) | Klassen-Prioritaet, Ausfuehrungs-Spur (PRD 8.1, Phase 4), Lockerungen | Default laeuft nach Frist (z. B. 7 Tage), Lockerungen nie per Default |
| Geld | kostenpflichtige Volltexte, Rechenbudget ueber Deckel, privater Speicher | keine Ausgabe |
| Datenauftraege / Schluessel | neue Stroeme, Backfills, Schluesseltrennung, Netzfreigaben | nach E-6 direkt an Data-Harvest; sonst Sammelvorlage |
| Recht | Repo-Sichtbarkeit, Lizenzen, Veroeffentlichung | keine Aenderung |

Alles andere entscheidet der Orchestrator per DEC; die Institution wartet nur bei Geld und Recht. Jede Vorlage nennt
Frage, Optionen mit Richtung, Default, Frist und Wirkung bei Stille (Verfassung Autonomie 3, "dokumentierter Default").

### 2.10 Ablauf (Soll)

```
Quellen: Literatur [sek] | X-Screens (K-Buch) | Mechanik-Checkliste
   -> Ideenkarte (YAML)
   -> Feasibility-Rechner (Nuisance-Katalog S1, power_p1) --GL-012--> Ledger (keine Herleitung)
   -> Herleitung (Agent) + Maschinenpruefungen + Review (Agent, Veto)
   -> Registrierung (Orchestrator): Linter, Fensterreservierung, Kohorte
   -> Positivkontrolle (Harness, Produktionskonfiguration)
   -> Lauf (Konfirmationsumgebung, Manifest, N>=3, Artefakte DEC-53)
   -> Gate-Bibliothek -> GL im Ledger -> FDR-Buch -> Digest an den Nutzer
```

---

## 3. Fenster-Politik der Institution

### 3.1 Zonen [V]

- **X (Exploration):** frei fuer S1 und registrierte S2-Stufen (Screens, Piloten); jede S2-Statistik im K-Buch;
  nichts Konfirmatorisches. X muss nicht blind sein - "Verbrauch" kostet hier nur den Optionswert als spaeteres
  Zusatzfenster (DEC-99 (2b)).
- **V (Validierung):** ein historischer Block je Familie, der laut Register blind ist; urteilstragend nach C.10.
- **C (Konfirmation):** juengster Block (REZENZ, DEC-99 (1)) oder prospektive Scheibe ab Kohortenstichtag; muss
  bestehen. Daten wandern C -> V -> X, nie zurueck.
- [U] Die Zonen spiegeln die heutige Praxis (Pilot/W1/W2, DEC-99); neu sind Register, Kohorten, Rotation, Vorwissens-
  Regel und sequentielle Konfirmation.

### 3.2 Zuordnung des heutigen Bestands (Vorschlag)

| Datenfamilie (Katalog) | X | V | C | Einschraenkung (Fundstelle) |
|---|---|---|---|---|
| Bybit-Tagespanel + Funding aller Perps (`rest.kline1d`, `rest.fundingRateAll` ab 2021-01-01) | 2021-01..2024-06 (fm8-Familie 2022-04..2024-06 verbraucht, GL-035) | W1 2024-07-01..2025-06-30 | W2 2025-07-01..2026-06-28; prospektiv ab Stichtag | W1/W2 blind fuer A3-fm8, Reversal, A1-Outcome (DEC-101 E12, GL-036, DEC-93); Blind-Siegel BTC/ETH-Streuung ab 2026-07-01 (DEC-96 E3) |
| BTC/ETH 1-min (`rest.kline1m`) fuer Ereignisse (A2) | 2021-03..2024-05 (fuer A2 nur per Disziplin blind, B-2) | W1 | W2 | P2'' im letzten W2-Quartal leer (DEC-103 N1 (5)); Negativ-Panel fehlt |
| DVOL / VRP (`deribit/dvol` ab 2021-03-24) | 2021-03..2024-05 (nur S1) | prospektiv | prospektiv | W1/W2 nicht blind (DEC-96 E1); agentenbekannte Groesse |
| A4-Quotes (`rest.tickers15m` ab 2026-10-20) | erste 12 Monate nur S1 | prospektiv | prospektiv | sigma_w fruehestens 2027-10 (DEC-98 N4) |
| Options-Ticker (ab 2026-06-16) | - | prospektiv | prospektiv | A5 gesperrt (PRD 9.3 Schritt 7) |
| Trades der 5 Majors (`publicTrade` ab 2020/21) | bis 2024-05 | W1 | W2 | unter Tageshorizont nur Kosten-/Zensus (Verfassung) |

### 3.3 Regeln der rollierenden Freigabe [V]

- **R-1 Vorwissens-Test.** Aggregierte, oeffentlich diskutierte Groessen (BTC/ETH-Vol, VRP, Funding-Niveau der Majors)
  werden nur prospektiv konfirmiert; obskure Querschnitts- und Ereignisstatistiken duerfen historische V/C nutzen, wenn
  das Register sie als blind fuehrt (Praxis A3; DEC-96 E1). Regel je Familie, nicht je Kandidat. (Strenge, O)
- **R-2 Kohorten.** Quartalsweise Stichtage; alle vor dem Stichtag registrierten Hypothesen teilen ihre Scheiben
  (Verallgemeinerung von DEC-98 E1 (d)); Multiplizitaet ueber die Kohorte im FDR-Buch. Das macht die Reihenfolge-Frage
  DEC-98 E4 (b) gegenstandslos: VRP-, Klasse-W- und A1-Hypothesen auf derselben Blindperiode schreiben sich vorher ein;
  die Streuung, die Klasse W fuer Betas braucht, wird erst im registrierten Lauf berechnet (loest DEC-98 E1 (b)).
  (Testbarkeit bei gleicher Fehlerrate je Test; N)
- **R-3 Prospektive Scheiben gruppensequentiell.** Vier Blicke, O'Brien-Fleming-Grenzen auf alpha 0,05 einseitig je
  Fenster; Blicke geben nur das Gate-Bit aus (S3), Schaetzer erst am Ende; Abbruch fuer Wirksamkeit, optional nicht
  bindend fuer Aussichtslosigkeit. Bedingung: konsistente SE fuer Zwischenblicke (stationaerer Bootstrap, DEC-94 (4)).
  (FPR neutral, Testbarkeit auf Zeit; N)
- **R-4 Rotation.** Eine verbrauchte Scheibe wird fuer die verbrauchende Familie X (mit generierter C.17-Zeile), fuer
  andere Familien bleibt ihr Zustand. Ein Siegel ohne registrierten Eigentuemer bleibt bestehen, sperrt aber keine
  Hypothese, die sich bis zum naechsten Stichtag einschreibt. (neutral, O)
- **R-5 Uebergaberegel nach erwartetem Ertrag.** Die Schwelle X -> V/C wird so gewaehlt, dass die erwartete Zahl echter
  Funde je verbrauchter V/C-Scheibe maximal ist, statt "Pilotpunkt >= MDE80 des Tests" (U-4, DEC-101 E7). Das ist
  FPR-neutral, weil Pilot und Test getrennte Daten sind (DEC-99 (6)). Anlass: U-A2 uebergibt bei 16,5 bp in 2,7 %
  (zentral) bzw. 0,01 % (stress) der Faelle (DEC-103 N1 (9)). R-5 macht A2 nicht testbar - die V/C-MDE von 23..32 bp
  bleibt. (Testbarkeit, FPR-neutral; O mit Vorlage)
- **R-6 Verbuchung.** K-Buch fuer jede S2-Statistik in jeder Zone, auch verworfene; FDR-Buch nur fuer konfirmatorisch
  gerechnete p (DEC-99 (7)); Doppelausweis unter der alten Zaehlung bleibt Pflicht.

### 3.4 Vergleich mit der heutigen Praxis: Strenge und Wartezeit

| Element | Heute | Vorschlag | Strenge | Wartezeit |
|---|---|---|---|---|
| Prior-Quelle | Literatur, sonst UNBELEGT = Blockade (Arbeitsregel 4, DEC-102 E3); Pilot nur per Einzel-DEC (DEC-99) | X-Pilot/-Screen als Standard, Literatur als Etikett (E-3) | FPR des Tests unveraendert (DEC-99 (6)); Lockerung der PRD-Vorbedingung, etikettiert | Prior-Blockade entfaellt (A1-, A2-, H-33-Typ) |
| Blindheit | Einmal-Gut je Abschnitt und Groesse; Reihenfolge seit 10-18 offen (DEC-98 E1 (d), E4) | Kohorten teilen Scheiben (R-2) | Multiplizitaet ueber Kohorte verbucht | m = 4: Datenfaktor 1,54 statt Warten auf 3 Vorgaenger [abg.] |
| Urteilsfenster | W1 + W2 historisch, C.10, REZENZ (DEC-99 (1)(8)); VRP prospektiv per Einzel-DEC (DEC-96) | V/C historisch nur bei obskuren Statistiken (R-1), sonst prospektiv | strenger fuer agentenbekannte Groessen | gleich |
| Datenmenge | feste Fenster (12 Monate oder L aus Nuisance) | prospektiv gruppensequentiell (R-3) | FPR gleich (alpha-Ausgabe) | E[N] 0,81 unter H1, 0,51 bei doppeltem Effekt; Maximum 1,03 [abg.] |
| Mehrfachtest | BH je Familie, BY ueber F-WEEK am Wellenschluss, bis dahin vorlaeufig (DEC-74 (e)) | laufendes FDR-Buch (E-2) | nominal gleich (q 0,10) | Urteil endgueltig ohne Wellenschluss |
| Uebergabe Pilot -> Test | U-4: Pilotpunkt >= MDE80 des Tests (DEC-101 E7) | nach erwartetem Ertrag (R-5) | FPR-neutral | weniger fast-sichere GL-012 (Pilot) |
| Siegelschutz | Disziplin + Paketwaechter; B-2 offen | DAL, Klassenmatrix, Allowlist, globaler Scan, Schluesseltrennung | strenger | gleich |

Gemeinsame Fehlerrate je Hypothese bleibt 0,25 % (C.10 unter P-1, DEC-94 Etikett; DEC-52-Zweig 0,5 %).

### 3.5 Zahlen zur Abwaegung [abg., Anhang A]

- **Geteilte Scheibe gegen Serialisierung** (Bonferroni je Fenster als Obergrenze; FDR-Verfahren sind bei wenigen
  echten Effekten aehnlich, bei mehreren milder [S]): Datenfaktor je Hypothese m = 2: 1,27; m = 4: 1,54; m = 8: 1,80;
  m = 12: 1,96 - gegen 2x, 4x, 8x, 12x Wartezeit fuer die letzte Hypothese bei Serialisierung.
- **Gruppensequentiell (O'Brien-Fleming, einseitig 0,05, Power 0,80):** K = 2: Maximum 1,008, E[N|H1] 0,87,
  E[N|H0] 1,00, E[N|2x Effekt] 0,57; K = 4: 1,030 / 0,81 / 1,02 / 0,51; K = 8: 1,050 / 0,78 / 1,04 / 0,45.
- **Beispiele.** Familie mit blindem W1/W2 und C10-Zuordnung: heute Herleitung -> Review -> Bau -> Registrierung -> PK ->
  Lauf (H-32: ~30 h Maschine plus 2,2 Tage Nutzer); Soll: gleiche Strenge, Tage ohne Nutzer, wenn E-3 gilt.
  VRP-artige Groesse: heute 2 x 672 Tage ab 2026-07-01, voll 2030-04-04 (PROGRAMM_BILANZ Option 4, Zeile O0); Soll:
  gleiche Mindestmenge, Erwartung unter H1 ~0,81 davon, keine Serialisierung gegen Klasse W.

### 3.6 Was die Politik nicht leistet

- Sie verkleinert die Datenmenge fuer einen Effekt gegebener Groesse nicht (Wurzelgesetz). A3-roh bleibt bei 2 x 119
  Wochen, VRP bei 2 x 672 Tagen (PROGRAMM_BILANZ 0.1), solange Prior und Nuisance so sind.
- Die reale Nuisance ist eher schlechter als bilanziert: reale fm8-Wochen-SD 2,3..2,6 x Null (GL-035), Mindest-Prior fuer
  H-33 unter dieser Streuung 0,040..0,043 statt ~0,02 (GL-036). [abg.] Bei k ~2 waechst n mit k^2 ~4.
- Kohorten kosten Power ueber Multiplizitaet; der Gewinn liegt nur im Wegfall der Serialisierung.
- Die Vorwissens-Klasse ist ein Urteil - es wird je Familie einmal getroffen und registriert, nicht je Kandidat.

---

## 4. Fehlerbilder und Schutz

| Fehlerbild | Vorfall (Fundstelle) | Schutz heute | Schutz Soll (Baustein) | Restrisiko |
|---|---|---|---|---|
| Agenten-p-Hacking (Gabelungen nach Kenntnis) | A1: alle sechs EV Richtung Testbarkeit, nicht beschlossene c-Regel als bindend gesetzt (DEC-93 E1/E3); H-33-Richtung nach Pilot (DEC-102 E2); Lockerungen nach Kenntnis (DEC-94, DEC-99 Etiketten) | Review-Veto, Etiketten, Sequenz-Zwang | Gabelungsregister mit Quote (f4); Gate als Daten (c4); K-Buch (d); Regelaenderungen gelten erst ab naechster Kohorte, Lockerungen nur mit Nutzer (E-10) | Auswahl, WELCHE Ideen generiert werden; nur ueber K-Buch sichtbar |
| Siegel-Lecks (B-2-Typ) | `a2_vorarbeit.json` (Commit 363f3d9) mit 1.188 geschachtelten Gruppen (DEC-103 N1 (2)); Teil-C-Fassung 1 (B-1); Fenster-RV in der Akte (DEC-95 E2); Katalog-Metadaten im Blindbereich (DEC-97 A-3) | Disziplin; Hash-Waechter in Einzelskripten; Hand-Scan | DAL + Klassenmatrix + Allowlist + globaler Kanal-Scan in CI (a1/a2); Schluesseltrennung (a3); versiegelte Zwischenstaende nur als Hash oeffentlich (E-7) | Vorwissen der Agenten; unbekannte Kanaltypen |
| Spezifikationsdrift | DEC-87 (Gate (5) im Lauf nicht geprueft, Bounce-Kill nur Etikett, eine Kalibrierung fuer beide Fenster); DEC-101 E7 ersetzt "Regel U bleibt unveraendert" binnen Stunden; Registry-Abschnitt "Abweichungen Code/Text" (Drittfassung) | Reviews, T4, Pins | Gate als Daten + generische Gate-Bibliothek (c4); automatische Abweichungsliste YAML gegen Code-Konstanten; Schema-Versionen | Schaetzer-Code bleibt spezifisch |
| Kosten-Explosion | Pflichtlektuere 656.775 Byte; A3 mit 3 Fassungen und 8 Vorlaeufen; 300 Groessen bitgleich nachgerechnet (REVIEW_H33) | Kurzfassungsregel | Kostenbuch (g); Deckel je Hypothese (z. B. zwei Herleitungsrunden, danach GL-012 mit Grund); Feasibility-Rechner vor jeder Herleitung (b3); Regel-Sicht statt Historie; Nachrechnung nur der urteilstragenden Zahlen | Deckel kann echte Komplexitaet abschneiden - nur dokumentiert, nie still |
| Stille Defaults | Null-Renditen statt NaN (DEC-85 D2); Ankuendigungs- statt Handelsende-Datum (DEC-74 Nachtrag (2), DEC-100 E1); PRD L-14 | Arbeitsregel 4, C.14 | Schema ohne Defaults (c1); Datenvertraege mit NaN-/Datumspruefung (a2.7); Lint-Regeln aus der Abweisungsliste (f5) | Defaults in Bibliotheken (ddof, Fuellwerte) |
| Determinismusverlust | v6a verworfen (DEC-101 E1); W1-Determinismus-Kontrolle nach Panelaenderung unmoeglich (Uebergabe Nachtrag 10); Bisektion mit frischen Zufallszahlen (DEC-81); Paketverlust im Container (Uebergabe 10-09 Abschnitt 8); Archiv/Live-Mischung (DEC-96 N2) | T2, Fingerprints, Pins | Manifest mit Umgebungs-Lock, Client-sha, Katalogstand, Partition-Pruefsummen; N >= 3 (e) | Boersen revidieren REST-Historie (PRD 7.1): monatlicher Stichproben-Abgleich |
| Scratch-Verlust | 2026-10-31 (Uebergabe Nachtrag 13); 61 eindeutige `scratchpad/`-Verweise, 0 versioniert (z. B. `bilanz_census.py`, `h33_compute.py`, `orch_check/a2_spot.py`, alle `SPEC_*`) | Ergebnis-sha256 in den Texten | "Keine Zahl ohne versioniertes Skript" im Linter; `derivations/` und `verify/` im Repo; Extrakte nur als Manifest (F0) | Altbestand nur als Liste rettbar; Neubau kostet Rechenzeit |
| Datendrift beim Lieferanten (zusaetzlich) | 45 delistete Perps fehlten (DEC-100); USDC-Zwillinge im Universum (DEC-101 B-1); Katalog-Stillstand 10-12..10-17 (DEC-96 N2/N3) | Inhaltsproben (C.8), Reviews | Datenvertraege, Universumsregel als Daten, Katalog-Alarm (a2.7) | Fehler im Archiv selbst |
| Leerlauf durch Nutzerlatenz (zusaetzlich) | Reihenfolge-Frage seit 10-18; 4,6 Tage bis DEC-102 | "Default bei Stille" | Entscheidungswarteschlange mit Frist (h); Kohorten (R-2) | Geld und Recht bleiben blockierend |

---

## 5. Fahrplan

### 5.1 Reihenfolge und Aufwand

Aufwand [S]: Agentenstunden nach der Bau-Erfahrung H-32 (Treiber 5,8 Tsd. Zeilen + Tests in ~3 Bauauftraegen,
Commits f7dd471, 6e4b447, 117dc02); Token als verarbeitete Token (2-5 Mio je Agentenstunde, ueberwiegend
Kontext-Wiederholung) - ohne Messbasis, deshalb ist das Kostenbuch Teil von F0.

| Phase | Wochen | Inhalt | Regeln -> Code | Agenten-h | Token (Mio) | Nutzer | Fertig, wenn |
|---|---|---|---|---|---|---|---|
| F0 Schadensbegrenzung | 1 | Specs, Herleitungs-, Review-, Nachrechnungsskripte aus `/home/user/scinance_work/` (nach Pruefung auf Hostnamen/Schluessel) nach `derivations/`, `verify/`; Liste der 61 verlorenen Verweise; Umgebungs-Lock; `channel_scan` als CI-Test ueber alle JSON; Kostenbuch beginnt | DEC-103 N1 (2c) | 6-10 | 15-50 | nein | CI gruen; Liste im Ledger |
| F1 Ledger, Schema, Linter | 1-3 | Ledger mit Hash-Kette, JSON-Schema der zwoelf Pflichtzeilen, Linter, gerenderte Sichten, Sicht "geltende Regeln" | PRD 3.3/3.4; C.1; C.14 | 20-30 | 40-150 | nein | `h28_h30_v3.yaml` und `h32_v1.yaml` laufen rueckwaerts durch den Linter (bzw. ihre Abweichungen sind gelistet) |
| F2 Register und Datenzugang | 2-5 | Fensterregister, DAL, Zugriffsbuch, Klassenmatrix, C.17-Generator, Datenvertraege; Bestand nach 3.2 eintragen | DEC-96 E3; DEC-98 E1 (d); DEC-99 (3)(5); DEC-101 E1/E3/E9a | 25-35 | 50-175 | E-1 | Register reproduziert die Akte (fm8-P verbraucht, A2-Vorperiode mit B-2-Etikett, VRP-W1/W2 nicht blind) |
| F3 Feasibility | 4-7 | Nuisance-Katalog (S1, nur X) fuer Standardfamilien; Feasibility-Rechner | DEC-94 (3)-(6); C.12 | 15-25 | 30-125 | nein | reproduziert die Zuordnungen von GL-032, -033, -034, -036 aus Katalog und Akte (T4-artig) |
| F4 Lauf-Rahmen | 6-10 | Manifest-Runner, Gate-Bibliothek, PK/NK-Harness, Artefakt-Writer, Nachrechnung als Code; H-32 als Referenz migrieren | DEC-53; T0-T7; PRD 3.3.8; DEC-101 E2/E8 | 35-50 | 70-250 | nein | Pilot H-32 aus dem generischen Rahmen bitgleich zum Akten-Artefakt (result_sha256 8b63a56e...) - nur mit eingefrorenem Panel, in der Konfirmationsumgebung |
| F5 Generator und Takt | 8-12 | Ideenkarten, Mechanik-Checkliste, X-Screens (nach E-3), taeglicher/woechentlicher/quartalsweiser Takt, Entscheidungswarteschlange, Digest | DEC-58 E2-Abgrenzung; DEC-57 | 20-30 | 40-150 | E-3, E-9 | Kohorte K1 vor ihrem Stichtag registriert |
| F6 nach Tag 90 | - | FDR-Buch-Verfahren, sequentielle Blicke, Schluesseltrennung, privater Speicher | C.16; DEC-74 (e); DEC-99 (7) | 15-25 | 30-125 | E-2, E-5, E-6, E-7 | erste prospektive Scheibe mit Blickplan |
| Summe F0-F5 | | | | ~120-180 | ~0,25-0,9 Mrd | | |

Waehrend F0-F3 bleibt das Programm im Aufzeichnungsmodus (DEC-102 N2); neue Herleitungen erst, wenn der
Feasibility-Rechner steht (O).

### 5.2 Regeln, die als Code formalisiert werden

| Regel | Fundstelle | Heute im Code | Soll |
|---|---|---|---|
| Power/MDE/Zuordnung P-1, Doppelausweis | DEC-94 (1)-(9) | `power_p1.py` (generisch) | Pflichtaufruf im Linter und Feasibility-Rechner |
| Zwoelf Pflichtzeilen, YAML-Format, Linter | PRD 3.3, 3.4 | nur `h32_fm8/schema.py` | generisches Schema + Linter |
| Ergebnis-Artefakte | DEC-53, T7 | je Paket | generischer Writer + T7 |
| Datumsschnitt, Blind-Siegel | DEC-96 E3, DEC-99 (3)(8) | `h32_fm8/panel_cut.py` | DAL fuer jeden Strom |
| Genau-ein-Pilot, Versuchsmarker | DEC-99 (3), DEC-101 E3/E9a | `h32_fm8/checks.py` | Register-Transaktion |
| Verbrauch je Familie und Abschnitt | DEC-98 E1 (d), DEC-99 (5) | nein (Text) | Fensterregister |
| Universumsregel | DEC-101 E1 | `h32_fm8/universe.py` | Datenvertrag je Familie |
| Skalierte Null | DEC-101 E2 | `h32_fm8` testrun/gate | Gate-Bibliothek |
| Positivkontrolle in Produktionskonfiguration | PRD 3.3.8, DEC-89, DEC-101 E8 | `wp13_xsec`, `h32_fm8` | generischer Harness |
| Ausgaberegel Nuisance, Kanal-Scan | DEC-103 N1 (2c) | Skript ausserhalb des Repos | Allowlist + CI-Scan |
| Nuisance nur Streuung, kein Mittel | DEC-94 (5) (i) | Einzelskripte | Klassenmatrix S1 |
| F-WEEK-Zaehlregel | DEC-99 (7) | `h32_fm8/fweek.py` | FDR-Buch |
| C.17-Offenlegung | Kompendium C.17 | Hand | aus dem Zugriffsbuch generiert |
| Kostenmodell-Pin `constants_hash` | PRD 3.3.6 | nein (kapitalfrei "n/a") | beim ersten Kandidaten mit Kostenbezug |
| GPU 0, 24-h-Meldegrenze | DEC-57 | nein | Budget-Waechter |
| Stress-Kanon monatlich fortschreiben | DEC-55/56 | Fixture-Dateien | Monatsjob im Takt |
| Loud fail | C.14 | je Paket | Linter, Runner, DAL |

### 5.3 Einmalige Entscheidungen des Nutzers

| Nr. | Frage | Vorschlag als Default | Richtung | Ebene |
|---|---|---|---|---|
| E-1 | Fenster-Politik: Zonen 3.2, Kohorten quartalsweise, Vorwissens-Regel R-1 | annehmen; ersetzt die offene Reihenfolge-Frage DEC-98 E4 (b) | Strenge (R-1) + Testbarkeit (R-2) | N |
| E-2 | Mehrfachtest-Verfahren ueber die Institution | Kohorten-BY mit q 0,10 (wie F-WEEK, Kohorte statt Welle); laufendes Online-FDR erst nach Pruefung der Gueltigkeit unter Abhaengigkeit [S] | neutral | N |
| E-3 | Prior-Regel: X-Pilot/-Screen als Standardquelle (Verallgemeinerung DEC-99), Screens als registrierte Stufe abgegrenzt von DEC-58 E2 | annehmen, Etikett "Lockerung der PRD-Vorbedingung, FPR je Test unveraendert" | Testbarkeit | N |
| E-4 | Uebergaberegel nach erwartetem Ertrag (R-5) | Orchestrator legt Kriterium fest, Vorlage zur Kenntnis | Testbarkeit, FPR-neutral | O |
| E-5 | Gruppensequentielle Konfirmation prospektiver Scheiben (R-3) | annehmen | neutral (FPR), Testbarkeit (Zeit) | N |
| E-6 | Direkter Auftragskanal an Data-Harvest; Schluesseltrennung Exploration/Konfirmation | annehmen; Data-Harvest prueft Praefix-Rechte (UNBELEGT) | Strenge | N |
| E-7 | Versiegelte Zwischenstaende: privater Speicher oder nur Hash im oeffentlichen Repo | Hash-only, bis ein privater Speicher besteht | Strenge | N (Recht/Geld) |
| E-8 | Netzfreigabe fuer offene Volltextquellen in den Umgebungseinstellungen | annehmen | neutral | N |
| E-9 | Budget: Token-/CPU-Deckel je Monat und je Hypothese, Stoppregel bei Leerlauf, Ausgaben fuer Volltexte | Deckel nach F0-Kostenbuch | neutral | N (Geld) |
| E-10 | Regelaenderungs-Protokoll: Lockerungen nur mit Nutzer und erst ab naechster Kohorte; Verschaerfungen durch den Orchestrator | annehmen | Strenge | N |

Danach wiederkehrend nur: neue Geldausgaben, neue Datenquellen/Vertraege/Schluessel, Aenderung der Programmrichtung
(inkl. PRD 8.1 Ausfuehrungs-Spur), Recht. "Kein Live-Order-Code" bleibt unberuehrt.

### 5.4 Messbar nach 90 Tagen

| Messgroesse | Basis heute | Ziel |
|---|---|---|
| Akten-Verweise auf nicht versionierte Skripte/Daten | 61 `scratchpad/`-Pfade + Arbeitsverzeichnis ausserhalb des Repos | 0 neue; Altbestand gelistet |
| Datenzugriffe ueber DAL mit Zugriffsbuch | 0 % | 100 % neuer Laeufe |
| Kanal-Befunde in versionierten Dateien | 1 offen (B-2) | 0 neue (CI blockiert) |
| Maschinenzeit Ideenkarte -> Feasibility-Befund | 1-30 h, je Herleitung + Review | <= 2 h ohne Herleitung fuer Standardfamilien |
| Nutzer auf dem kritischen Pfad | 7 Entscheidungen, 2 offen, 17 Weiterleitungen in 23 Tagen | 1 Sammelvorlage je Woche; keine Wartezeit ausser Geld/Recht |
| C.17-Listen | Hand, mit Korrekturen (DEC-95 E2) | 100 % generiert |
| Kosten je Hypothese | ungemessen | gemessen; Baseline fuer E-9 |
| Determinismus registrierter Laeufe | v6b x2 | N >= 3 im Manifest |
| Kohorte K1 | - | registriert vor ihrem Stichtag, Fenster aus dem Register |
| PASS/Entdeckungen | - | ausdruecklich KEINE Zielgroesse (sonst Anreiz zum p-Hacking) |

---

## Was NICHT folgt

- Automation macht kleine Effekte nicht frueher testbar: die Mindestdatenmenge folgt dem Wurzelgesetz
  (PROGRAMM_BILANZ 1.2); A3-roh, VRP und A4 bleiben Jahre entfernt, solange Prior und Nuisance so sind.
- Kein Vorschlag senkt die Fehlerrate je Test unter 0,25 % gemeinsam oder hebt C.10, REZENZ oder Power 0,80 auf; die
  Lockerungen (E-3, Screens) sind als solche etikettiert und Programmfragen.
- Keine Aussage ueber Effekte: kein Verdikt ueber Momentum, Reversal, Carry, VRP oder Verfallseffekte; keine
  Outcome-Statistik wurde hier gerechnet.
- Der Siegel-Befund B-2 wird nicht rueckwirkend geheilt; die A2-Vorperiode bleibt "blind durch Disziplin".
- Die Schluesseltrennung setzt eine Faehigkeit des Datendienstes voraus, die UNBELEGT ist.
- Die Token- und Stundenzahlen sind Schaetzungen ohne Messbasis; die Akte hat kein Kostenbuch.
- Keine Ausfuehrungs-Spur, kein Live-Order-Code, keine Kapitalaussage (PRD 8.1 Default (b)).
- Die Fenster-Politik entscheidet die offene Reihenfolge-Frage nicht; sie macht sie nur gegenstandslos, wenn der Nutzer
  E-1 annimmt.

---

## Anhang A: Rechnung (reine Arithmetik, synthetisch, keine Marktdaten)

Ausgefuehrt mit `python3 -I`, numpy, Seed 1, 400.000 Pfade. Ausgabe wie in 3.5.

```python
from statistics import NormalDist
import numpy as np
N = NormalDist(); z80 = N.inv_cdf(0.8); base = N.inv_cdf(0.95) + z80      # 2,4865
for m in (1, 2, 4, 8, 12):                                                # geteilte Scheibe, Bonferroni je Fenster
    z = N.inv_cdf(1 - 0.05 / m); print(m, round(((z + z80) / base) ** 2, 3))
rng = np.random.default_rng(1)
def obf(K, alpha=0.05, power=0.8, nsim=400000):                         # O'Brien-Fleming, gleiche Abstaende
    t = np.arange(1, K + 1) / K
    B = np.cumsum(rng.standard_normal((nsim, K)) * np.sqrt(np.diff(np.r_[0, t])), axis=1)
    lo, hi = 1.0, 4.0
    for _ in range(50):                                                   # Grenze c/sqrt(t) mit P_H0 = alpha
        c = (lo + hi) / 2
        lo, hi = (c, hi) if ((B / np.sqrt(t)) >= c / np.sqrt(t)).any(1).mean() > alpha else (lo, c)
    c = (lo + hi) / 2
    pw = lambda th: (((B + th * t) / np.sqrt(t)) >= c / np.sqrt(t)).any(1).mean()
    lo, hi = 0.5, 5.0
    for _ in range(50):                                                   # Drift fuer Power 0,80
        th = (lo + hi) / 2; lo, hi = (th, hi) if pw(th) < power else (lo, th)
    th = (lo + hi) / 2; R = (th / base) ** 2                              # Maximum relativ zur Festgroesse
    def EN(d):
        cr = (((B + d * t) / np.sqrt(t)) >= c / np.sqrt(t))
        return t[np.where(cr.any(1), cr.argmax(1), K - 1)].mean() * R
    return c, R, EN(th), EN(0.0), EN(2 * th)
for K in (2, 4, 8): print(K, obf(K))
```

Ausgabe: m = 1/2/4/8/12 -> 1,000 / 1,270 / 1,537 / 1,804 / 1,959. OBF K = 2: c 1,671, Maximum 1,008, E[N|H1] 0,870,
E[N|H0] 1,004, E[N|2x] 0,565; K = 4: 1,734 / 1,030 / 0,811 / 1,022 / 0,506; K = 8: 1,789 / 1,050 / 0,782 / 1,039 /
0,453.

---

## Kurzfassung an den Orchestrator (<= 12 Zeilen)

1. Ist: sechs Kandidaten, null urteilstragende p-Werte; Maschinenzeit je Befund 1-30 h, Wartezeit dominiert von
   Nutzerfragen (1-5 Tage, eine seit 14 Tagen offen) und 17 Data-Harvest-Weiterleitungen in drei Wochen.
2. Engpaesse: Literatur-Prior-Pflicht bei gesperrten Volltexten (A1, H-33, A2), Datenkanal ueber den Nutzer, Power.
3. Risiken jetzt: 61 unversionierte Scratch-Verweise (Verlust 10-31), Siegel B-2 nur durch Disziplin, kein Linter.
4. Soll: Ledger + Fensterregister (K-/FDR-Buch) + DAL mit Statistikklassen und Kanal-Scan in CI + Schluesseltrennung +
   Feasibility-Rechner auf Nuisance-Katalog + generischer Lauf-/PK-Rahmen mit Gate als Daten + Entscheidungsqueue.
5. Fenster: Zonen X/V/C, Kohorten-Stichtage (loesen die Reihenfolge-Frage), prospektiv fuer agentenbekannte Groessen,
   gruppensequentiell; FPR je Test unveraendert 0,25 %; m = 4 Datenfaktor 1,54 statt Serialisierung; E[N|H1] 0,81.
6. Wurzelgesetz bleibt: A3-roh/VRP/A4 bleiben Jahre entfernt; gewonnen wird Prior-Freiheit, Parallelitaet, Leerlauf.
7. Fahrplan: F0 Versionierung/Kanal-Scan/Kostenbuch (Woche 1) -> F1 Ledger/Schema/Linter -> F2 Register/DAL ->
   F3 Feasibility -> F4 Lauf-Rahmen (H-32 bitgleich) -> F5 Generator/Takt; ~120-180 Agentenstunden [S].
8. Nutzer einmalig: E-1 Fenster, E-2 FDR, E-3 Prior aus X (Lockerung), E-5 Sequenzanalyse, E-6 Kanal/Schluessel,
   E-7 Ablage, E-8 Netz, E-9 Budget, E-10 Regelaenderungs-Protokoll; danach nur Richtung, Geld, Daten, Recht.
9. Sofort ohne Nutzer moeglich (O): F0, F1, F3; keine neue Herleitung vor dem Feasibility-Rechner.
