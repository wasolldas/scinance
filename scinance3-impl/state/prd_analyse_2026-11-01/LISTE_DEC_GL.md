# Listen DEC, GL und verworfene Ansaetze (PRD-Gesamtanalyse, Listenagent)

Stand: 2026-11-01. Nur gelesen, nichts im Repo geaendert. Keine Siegeldatei geoeffnet.

Quellen:
- scinance3-impl/state/decisions.md (Z = Zeilennummer)
- scinance3-impl/state/gate_log.md (Z = Zeilennummer)
- scinance3-impl/survey/ERKENNTNIS_KOMPENDIUM.md, Abschnitt D (Zeilen 346-421)

## Legende

- **Datum:** im Eintrag genanntes Datum (Anlass, Entscheidung, Nachtrag). "(Lauf)" = Datum des referenzierten Laufs. "(Befundstand)" = Datum aus dem Dateinamen der zitierten Befundakte. "k.A." = im Eintrag kein Datum genannt. "k.A. (Bezug ...)" = nur ein Bezugsdatum auf eine andere Quelle.
- **Richtung:** nur wenn der Eintrag selbst ein Etikett oder eine ausdrueckliche Richtung nennt (Wortlaut in Klammern). Sonst "-".
- **Kandidaten:** Bezeichnungen aus dem jeweiligen Eintrag. Zuordnung der Kuerzel laut PRD und Eintraegen: A1 = Funding-Long-Bein (DEC-70); A2 = EXP-CLOCK, Verfalls-Ereignis (DEC-103); A3 = Querschnitt F-XSEC1 (H-28..H-30, H-32 fm8-Variante); A4 = Perp gegen datierten Future; A5 = Skew-Praemie / Options-Block (PRD 5.5); H-26 = VRP auf Optionen (2.0, gesperrt); H-27 = VRP auf DVOL-Backfill (nicht registriert); H-32 = A3 mit beta-neutralem IC (Pilot abgeschlossen); H-33 = beta-neutrales Kurzfrist-Reversal (GL-012 vor Registrierung).

## Liste 1: DEC (82 Zeilen)

| Nr (Z) | Datum | Titel (<= 20 Worte) | Richtung | Kandidaten |
|---|---|---|---|---|
| DEC-51 (Z10) | k.A. | Power-Konvention 3.0 fuer jede Registrierung: alpha 0,05 einseitig, Power 0,80, Cluster-Einheit, N_eff, Selektions-K, Ueberlappung | - | Programm (alle Registrierungen) |
| DEC-52 (Z23) | k.A. | Entwurf: Entschaerfung des harten Ein-Fenster-DROP bei Per-Fenster-Power unter 0,6, Vorbedingungen (i) bis (v); nicht beschlossen | - | Klassen mit Per-Fenster-Power unter 0,6; Retro-Check H-06, H-20, H-22 |
| DEC-52 N1 (Z35) | 2026-09-02 | Retro-Check auf H-06, H-20, H-22 liegt vor; Regel beschlossen; kein Verdikt kippt; Bootstrap-Einschraenkung offen benannt | Verbesserung (Etikett im Eintrag) | H-06, H-20, H-22 (2.0); Klassen mit Power unter 0,6 |
| DEC-53 (Z53) | k.A. | Ergebnis-Artefakt-Pflicht: jeder 3.0-Lauf speichert Cluster-Serie und Bootstrap-Replikate; ohne sie kein Verdikt | - | Alle 3.0-Laeufe |
| DEC-54 (Z61) | k.A. (Bezug 2026-06-23) | Repo-Umbau 3.0: Versionsordner fuer Akten und Artefakte, Quarantaene fuer toten Code, lebender Baum unveraendert | - | keine (Repo-Struktur) |
| DEC-55 (Z73) | k.A. | Kanonischer Stress-Kanon als Fixture: Tage ueber 97,5-Perzentil plus 2026-08-19; Design-Parameter, keine Gate-Schwelle | - | Alle Stress-Klauseln |
| DEC-56 (Z81) | k.A. | Stress-Kanon praezisiert: rollierende Liste als Abdeckungsnachweis, absolute Zweitliste STRESS_ABS fuer Liquiditaetsfragen | - | WP-10(A); Liquiditaets- und Fill-Fragen |
| DEC-57 (Z88) | k.A. | GPU-Standardbudget je Hypothese auf 0; 24-h-Grenze nur Meldegrenze, keine Schwelle | - | Alle GPU-Laeufe; H-14..H-18 (2.0) |
| DEC-58 (Z95) | k.A. | Wissenschafts-Exkurs: Aufnahmen als Vorfragen, Null-Zensus-Klausel (kein Kandidat aus Zensus), Auflagen fuer A1 und A2 vor Registrierung | - | A1, A2; X-OEKO-1, X-OEKO-3, X-ASTRO-3 |
| DEC-59 (Z107) | 2026-09-08 (Lauf) | Welle-1-Vorfragen: A4 recording-first; A1-Nulleffekt als Totzonen-Modell neu gefasst; Intervall-Heterogenitaet 4h/8h statt 1h/8h | - | A4, A1; A2 (V-5a) |
| DEC-60 (Z118) | 2026-09-08 (Lauf) | WP-11 Lauf 1: Schaetzer uninformativ (real gleich Pseudo-Null); Umstellung auf Superposed-Epoch-Mittelprofil; Vergleichszeile Pflicht | - | WP-11; H-20 (Ereignisdefinition) |
| DEC-61 (Z127) | 2026-09-09 (Lauf) | WP-9 Befund B1: DVOL-REST-Backfill mit Harvester-Strom austauschbar; H-27-Klasse eroeffnet, nicht registriert | - | H-27; H-26 (gesperrt, unberuehrt) |
| DEC-62 (Z135) | 2026-09-09 (Lauf) | WP-10(A): Stress-Kohaerenz mit Harvest-Serien nicht messbar; Wiederholung als WP-10(A2) auf nachgeladenen Tagesserien; Konstanten uebernommen | - | WP-10(A2); A1 (N_eff); H-27 und A5 (BTC+ETH als ein Bein) |
| DEC-63 (Z144) | 2026-09-09 (Lauf) | WP-11 v2: Nach-Schock-Ueberschuss zerfaellt potenzgesetzartig auf Tages-Skala; Konstante fuer Kostenmodell; kein Kandidat | - | Kostenmodell (tradability3); X-OEKO-1 (Arm b) |
| DEC-64 (Z152) | 2026-09-09 (Lauf) | WP-10(A2): Stress-Zelle besetzt, Funding-Kohaerenz steigt im Stress; Surrogat-Null vor Konstante nachzuruesten | - | WP-10(A2); A1 (N_eff-Pflicht) |
| DEC-65 (Z160) | 2026-09-10 (Lauf) | WP-10(A2) mit Surrogat-Null: Funding-Kohaerenz-Anstieg im Stress nicht selektionsbedingt; Stress-Matrix wird Konstante; Welle-1-Teil A abgeschlossen | - | A1 (Stress-N_eff); WP-10(A2); F-PREM1, F-PREM2 |
| DEC-66 (Z168) | 2026-09-10 und 2026-09-14 (Lauf) | WP-7 panel_1d: 69 PARTIAL-Partitionen sind Quellen-Luecken; Zensus mit --allow-partial gilt fuer die Feasibility-Frage; Abbruch-Schwelle bleibt | - | WP-7 (Klasse W, Feasibility); A3 |
| DEC-67 (Z176) | 2026-09-14 (Lauf) | WP-7 Befund B2/B3/B5: Klasse W testbar; harte Per-Fenster-Regel fuer A3 und A1-Schluessel; Degenerations-Kill vorab; Konstanten registriert; WP-12 angeordnet | - | A3; A1 (Schluessel, Kill); WP-12 (Survivorship) |
| DEC-68 (Z188) | 2026-09-10 (Lauf); Diagnose 2026-09-15 | WP-10(B) Lauf 1 leer: Manifest fuehrt kompaktierte Tage als EMPTY; geschlossener Tag gilt bei Manifest-DONE oder kompaktierter Datei | - | WP-10(B); Kostenmodell |
| DEC-69 (Z195) | 2026-09-15 (Lauf) | WP-10(B) Lauf 2: p_fill-Kurve als Konstante; Adverse-Selektion durch Slice-Fehler unmessbar; Korrektur und Wiederholung | - | WP-10(B); tradability3 (Kostenmodell) |
| DEC-70 (Z204) | 2026-09-16 (Befundstand) | WP-7 v2 und WP-12: A1 wird Long-Bein gegen Universums-Hedge, Short-Bein degeneriert; B3 durch WP-12b; N_eff-Konstanten registriert | - | A1 (Konstruktion); WP-12; Klasse W |
| DEC-71 (Z214) | 2026-09-16 (Lauf) | WP-10(B) Lauf 3: Fill-Kurve und Adverse Selektion liegen vor; Maker-Vorteil traegt in Ruhe, Stress-Zelle leer; Konstanten registriert | - | WP-10(B); Kostenmodell (Maker, Taker-Pfad Stress) |
| DEC-72 (Z225) | 2026-09-21 (Union-Zensus) | Wiedergelistete Symbole in der Union: delistete Episode als eigene Spalte; Ueberlebenden-Spalte unveraendert | - | Klasse W (Union-Panel); A3 |
| DEC-72 N1 (Z229) | 2026-09-21 | Form b: Ueberlebenden-Baum enthaelt fruehere Episode bei wiederverwendetem Namen; delistete Spalte verworfen, Luecke statt Rendite | - | Klasse W (Union-Panel) |
| DEC-72 N2 (Z230) | 2026-09-21 | Form c: ICXUSDT als frische Delistung nach Ueberlebenden-Fetch; delisteter Baum massgeblich, gemeinsame Closes muessen exakt gleich sein | - | Klasse W (Union-Panel) |
| DEC-73 (Z234) | 2026-09-21 (Befundstand) | Welle 1 abgeschlossen: B3 aufgeloest; erste Registrierung A3-Kohorte F-XSEC1 (H-28..H-30); A1 bleibt bis erweiterte V-1 gesperrt | - | A3 (H-28..H-30); A1 (gesperrt); A2, A4, A5 (gesperrt); H-27 (eroeffnet) |
| DEC-74 (Z245) | k.A. | Registrierung H-28..H-30 Erstfassung nach Review zurueckgezogen; Vorlauf WP-13a vor Zweitfassung; bindende Korrekturen (a) bis (k) | - | A3 (H-28, H-29, H-30) |
| DEC-74 N1 (Z262) | 2026-09-21 | Vorlauf-Eingaben: STRESS_REL-Abdeckung beider Fenster belegt; delisting_dates mit Announcement-Datum als Etikett; Deribit-Liefergebuehr als [sek]-Konstante | - | A3; A5 (V-4a, Liefergebuehr); DEC-45 |
| DEC-68 N-Heading (Z266) | 2026-09-22 | Registrar-Antwort: EMPTY kam vom falschen Adapter; Sequenzbrueche durch Topic-Vermischung erklaert; Replay soll je Tag auf ein Topic filtern | - | WP-10(B); WP-2, WP-4 (falls betroffen) |
| DEC-75 (Z272) | k.A. | Zweitfassung H-28..H-30 zurueckgezogen; Drittfassung mit faktorerhaltender Null, Cluster-SE, Beta-Kontrolle und eindeutigem H-30; Verschaerfungen nach zweitem Review | Strenge (Text: 'alle verschaerfend') | A3 (H-28, H-29, H-30); Survivorship (Klasse W) |
| DEC-76 (Z288) | 2026-09-22 (Vorlauf) | Vorlauf v2: driftende Faktor-Null ist keine Null fuer den rohen IC; Rollen der Nullen festgelegt; WP-10(B)-Sequenzbrueche als Duplikate eingestuft | - | A3 (Nullen H-28..H-30); WP-10(B) |
| DEC-76 N1 (Z295) | 2026-09-23 | Duplikate bestaetigt: 2026-08-13 je Symbol 50 Prozent exakte Duplikate; Dedupe-Fix; ein Befehl je Runde (Nutzer-Auflage) | - | WP-10(B) (Replay); Betrieb |
| DEC-77 (Z299) | 2026-09-23 (Lauf) | Vorlauf v3: Markt-Persistenz erzeugt mechanisches Querschnitts-Momentum in Hoehe von IC_prior; Beta-Residualisierung entfernt es nicht | - | A3 (H-28..H-30, Beta-Kontrolle) |
| DEC-78 (Z308) | 2026-09-24 (Lauf) | Vorlauf v4: gemessene Kalibrierung widerlegt Stress-Null; Beta-Pool an gemessenen Faktoranteil gebunden; WP-10(B) Schema 4 bestaetigt DEC-71 | - | A3 (Null, Beta-Kontrolle); WP-10(B) |
| DEC-78 N1 (Z316) | k.A. | Kalibrierung v5: Beta-Streuung per Bisektion auf den gemessenen Faktoranteil gesetzt; Gegenprobe bleibt; Lauf liest Kalibrierung aus Registrierung | - | A3 |
| DEC-79 (Z320) | 2026-09-26 (Nutzer-Auftrag) | Autopilot: Laeufe auf der Nutzer-Maschine ohne Handstart, Git als Auftrags- und Ergebniskanal; keine Cloud-Rechenumgebung | - | keine (Betrieb); Datenzugang WP-7, WP-10 |
| DEC-80 (Z329) | 2026-10-07 (Briefing); Lauf 2026-09-28 | Data-Harvest-Zugang fuer die Cloud-Sitzung ueber Secrets; Vorlauf v5 scheitert erneut an der Gegenprobe; Uebergabe | - | A3 (Vorlauf v5); Betrieb |
| DEC-81 (Z338) | k.A. (Bezug 2026-10-09) | Kalibrierung v5c: Gegenprobe auf Standardfehler-Basis, Suche mit gemeinsamen Zufallszahlen; Data-Harvest aus der Cloud nutzbar; Bybit-REST geo-gesperrt | - | A3 (Vorlauf v5c); Datenzugang |
| DEC-82 (Z349) | 2026-10-09 (Bericht) | Erweiterte V-1 (Funding-Regeln, DEC-58 E3): Recherche-Stand; Regeln erst nach empirischer Gegenprobe belegt; kein Kandidat promoviert | - | A1 (V-1); WP-7 |
| DEC-82 N1 (Z354) | k.A. | Bau: WP-7-Zensus um Intervallklassen-Empirie erweitert, neue Tests; Lauf per Autopilot-Auftrag nach Vorlauf v5c | - | A1; WP-7 |
| DEC-83 (Z358) | 2026-10-10 | Nutzer-Auflage Cloud-first: Rechnen in der Cloud-Sitzung, Daten vom Thin Client; einziges fehlendes Stueck ist panel_1d; Anfrage an Data-Harvest | - | Panel-abhaengige WP (WP-7, WP-10(A2), WP-12, WP-13) |
| DEC-84 (Z367) | 2026-10-12 (Antwort) | Panel ueber Thin Client; V-1-Empirie: Funding-Schwelle I skaliert exakt mit dem Intervall; Auto-Switch seit 2025-10-30 erzeugt kurze 1h-Episoden | - | A1 (V-1, Intervall-Klassen); WP-7 (Panel) |
| DEC-85 (Z377) | 2026-10-12 (Audit) | Gate-Audit-VETO gegen Befund 'keine Methode' (v5c): simulierte Marktspalte verfehlt Kalibrierungsziele; Null-Renditen statt NaN; Vorlauf v5d vorab fixiert | - | A3 (Klasse-W-Null) |
| DEC-86 (Z393) | 2026-10-12 (Lauf) | Vorlauf v5d: vier Methoden bestehen die Regel in beiden Fenstern; registriert wird fm_neutral_8w als Grundlage der Drittfassung | - | A3 (H-28..H-30, Beta-Kontrolle) |
| DEC-86 N1 (Z400) | 2026-10-12 | W1-Gewinnerzahlen ungueltig (falsche Kalibrierung im Code); Methodenentscheidung bleibt gueltig; W1 bis v5e nur Rasterzahlen | - | A3 |
| DEC-87 (Z404) | k.A. | Drittfassung H-28..H-30: Entscheidungen A bis J zur Herleitung (Decke, Gap, Kalibrierung je Fenster, Drag, Gate-Code, Varianten) vor Vorlauf v5e | - | A3 (H-28..H-30); H-30 (vol_rv, vol_max, vol_beta) |
| DEC-88 (Z424) | 2026-10-12 (Lauf v5e) | Vorlauf v5e: Gewinner fm_neutral_8w bestaetigt; bindende Decken; H-30 vor dem Lauf GL-012; gerechnet werden nur H-28_mom1 und H-29_rev_gap | - | A3 (H-28_mom1, H-29_rev_gap; H-30 GL-012) |
| DEC-89 (Z445) | k.A. | Vor Registrierung: Positivkontrolle in Produktionskonfiguration festgelegt; Bounce-Fixture aus Messungen; restliche Code/Text-Abweichungen | - | A3 |
| DEC-89 N1 (Z452) | 2026-10-12 (E2) | Kontrollwelt auf null_scales aus v5e umgestellt; strenger als vorher, vor jeder gerechneten Kontrolle festgelegt; Code und Tests angepasst | Strenge (Text: 'Strenger als vorher') | A3 (Positivkontrolle) |
| DEC-90 (Z456) | k.A. | Registrierung der Drittfassung H-28..H-30 (Kohorte F-XSEC1, A3) nach Review v3; Review-VETO mit zwei blockierenden Punkten behoben | - | A3 (H-28..H-30; gerechnet H-28_mom1, H-29_rev_gap) |
| DEC-91 (Z463) | 2026-10-12 (Lauf) | Positivkontrolle NICHT BESTANDEN (rc 3): kein Lauf; Ursache Power-Zuordnung mit Boden-SE statt registrierter SE; Ursachenanalyse | - | A3 (H-28_mom1, H-29_rev_gap) |
| DEC-91 N1 (Z468) | 2026-10-12 (Audit-Datei) | Gate-Audit bestaetigt Ursache; Positivkontrolle ohne Code-Defekt; GL-012-Entscheidung ruht auf v5e-Zahlen, nicht auf dem Kontrolllauf | - | A3 |
| DEC-92 (Z472) | k.A. | Drittfassung H-28..H-30: alle sieben Varianten GL-012 vor dem Lauf; kein Lauf; kein DEC-52-Zweig nach strengster Lesart; naechster Kandidat A1 | Strenge (Text: 'Strengste Lesart') | A3 (alle sieben Varianten); A1 (naechster Kandidat) |
| DEC-93 (Z484) | k.A. | A1 (H-31, Funding-Long-Bein): GL-012 vor der Registrierung unter den geltenden Beschluessen; theta UNBELEGT; keine Registrierung | - | A1 (H-31); H-27 (naechster Kandidat) |
| DEC-94 (Z496) | k.A. (Verfassung: seit 2026-10-13) | Programmregel P-1: kritischer Wert statt MDE-Faktor, Power mit registrierter SE, Autokorrelation der Teststatistik, Zuordnungsregel; prospektiv | Lockerung (Etikett im Eintrag) | Alle Registrierungen ab P-1, inkl. H-27; PRD 5.1-5.4 (Altzeilen) |
| DEC-95 (Z517) | 2026-10-13 (Antwort) | DVOL-Historie fuer H-27 ueber Thin Client (Variante B); Nachtrag zur DEC-94-Feststellung: realisierte BTC-Volatilitaet der Fenster bereits gesehen | - | H-27; H-26 (DVOL); A1, A3 (Fenster-RV gesehen) |
| DEC-96 (Z526) | k.A. | H-27: blinde prospektive Urteilsfenster ab 2026-07-01 (EV-0c); W1/W2 nur Aera-Profil; Blind-Siegel auf BTC/ETH-Vol; DVOL-Luecken nachfordern | Strenge (Text: 'strenge Lesart') | H-27; H-26 (unberuehrt); programmweit (Blind-Siegel) |
| DEC-96 N1 (Z534) | 2026-10-13 | Luecken nachgeladen; taegliche Wartung selbstheilend; BTC/ETH-Tagesschluesse aus Trade-Strom; Vollstaendigkeit geprueft, ohne Preise | - | H-27 |
| DEC-96 N2 (Z535) | 2026-10-14 | Katalog-Stillstand behoben; Archiv- und Live-Trades in gleicher Partition korrigiert; je Berechnung nur eine Herkunft | - | H-27 |
| DEC-96 N3 (Z536) | 2026-10-17 | Katalog wieder erschienen; DVOL BTC/ETH 2021-03-24..2026-10-16 lueckenlos; publicTrade BTC/ETH ab 2026-07-01 lueckenlos; nur Vollstaendigkeit geprueft | - | H-27 |
| DEC-97 (Z540) | k.A. | H-27 (VRP, DVOL-Backfill, EV-0c): GL-012 vor der Registrierung; keine Fensterlaenge L in {6, 9, 12} testbar; nicht registriert | - | H-27 |
| DEC-98 (Z550) | 2026-10-18 (Nutzer) | Programm-Bilanz angenommen mit Korrekturen A-1..A-4; H-26 bleibt gesperrt (R-1); Datenauftraege freigegeben; Entscheidungsvorlage an den Nutzer | - | H-26; A3 (fm8, H-32-Vorarbeit); A1; A2; A4; H-27; Blind-Siegel |
| DEC-98 N1 (Z563) | 2026-10-18 | Recherche: Prior fuer beta-neutralen IC UNBELEGT; theta UNBELEGT; V-5c Richtung [sek]; VRP-Prior-Korrektur auf 7,03 VP; Kontaminations-Register | - | A3 (H-32-Prior); A1 (theta); A2 (V-5b/c); H-27 (VRP-Prior) |
| DEC-98 N2 (Z564) | 2026-10-20 | PDF-Belege: kein Punkt >= 0,020 belegt (beta-neutraler Wochen-IC); VRP-Prior 7,14 VP; V-5c primaer belegt; theta bleibt UNBELEGT | - | A3 (H-32); H-27; A2 (V-5c); A1 (theta) |
| DEC-98 N3 (Z565) | 2026-10-20 | Varianzfaktor c_hat der Bilanz fuer A3 stammt aus 45/44-Wochen-Null (Artefakt); Bilanz-Dauern durch H-32-Power-Zeile ersetzt; C.17-Liste praezisiert | - | A3 (H-32) |
| DEC-98 N4 (Z589) | 2026-10-20 | Auftraege B-0 bis B-5 umgesetzt: A4-Quoten ab 2026-10-20; H-26-Lesarten; Delisting-Register-Abgleich; 1-min-Kerzen; Settlements; Optionsluecken | - | A4; H-26; A2; A5 (Optionen); H-32 (Register) |
| DEC-98 N5 (Z569) | 2026-10-21 | Option 3 (Hochfrequenz-RV) geschlossen; A2-Ereigniszensus: taegliche Optionsverfaelle, PRD-Placebo nicht umsetzbar; Nutzer-Vorlage verengt sich | - | H-27 (HF-RV); A2 (Placebo); H-26; H-33 (VRP-Vorlage in diesem Eintrag) |
| DEC-98 N6 (Z571) | 2026-10-26 | Options-Deliveries ab 2026-08-01 nur noch Future-Deliveries in der Schnittstelle; Ersatzquellen fuer Verfallskalender benannt; Rueckfrage erledigt | - | A2 (Verfallskalender) |
| DEC-98 N7 (Z573) | 2026-10-29 | A2-Vorarbeit: Placebo-Design optionsneutral als Groessen-Kontrast; sigma30 gemessen; Rauschboden je Design; Festlegungen; A2 GL-012 ohne V-5b-Beleg | Strenge (Etikett: 'Praezisierung (Richtung Strenge)') | A2 |
| DEC-99 (Z575) | 2026-10-20 (Zustimmung) | Programmregel REZENZ 3.0 und Pilot-Schaetzfenster; C.18 praezisiert; Zaehlregel F-WEEK; W2-Ende 2026-06-28; prospektiv | Lockerung (Richtung Testbarkeit; Etikett) | Alle Registrierungen (Rezenz); H-32 (erste Anwendung); F-WEEK; H-26 (unberuehrt) |
| DEC-99 N1 (Z603) | 2026-10-20 | p-Wert-Konvention F-WEEK: Replikate der faktorerhaltenden Null statt Block-Permutation; Bau H-32 (h32_fm8) mit Tests; Folgebau Delisted-Baum | - | H-32; F-WEEK |
| DEC-100 (Z593) | k.A. (Register 2026-10-20) | Panel-Vollstaendigkeit: 45 delistete lineare USDT-Perps fehlen im Union-Panel, 31 davon mit letztem Handelstag in W2; Register-Datum wird letzter Handelstag | - | H-32 (wartet auf Nachladen); WP-12; A1, H-27, v5e-Nuisance (Erratum) |
| DEC-100 N1 (Z601) | 2026-10-21 | Luecke ohne Backfill geschlossen ueber Tageskerzen-Strom; sechs Relisted-Symbole bleiben Ueberlebende; Delisted-Baum v2 gebaut; Freigabe Vorlauf v6 | - | H-32; WP-12 |
| DEC-100 N2 (Z605) | 2026-10-21 | Erratum-Etikett: 'Panel vollstaendig' gilt nur fuer USDT-Perps; USDC-Perps und datierte Futures sind im H-32-Universum nicht enthalten | - | H-32 |
| DEC-101 Teil 1 (Z607) | 2026-10-21 | H-32 Teil 1: Universum lineare USDT-Perps; skalierte Null; technische Pilot-Sperre; Pins; Vorlauf v6 verworfen (Erratum v6a) | Strenge (Etikett: 'Bereinigung (Strenge)') | H-32 |
| DEC-101 Teil 2 (Z620) | k.A. | H-32 Teil 2: Regel U-4; Positivkontrolle in Produktionskonfiguration; Pilot-Versuchsmarker; Registrierung h32_v1.yaml; Pilot-Freigabe | Strenge (Text E7: 'Richtung: Strenge') | H-32 |
| DEC-101 Teil 3 (Z632) | 2026-10-21 (Pilot-Lauf) | H-32 Teil 3: Pilot-Ergebnis festgehalten; GL-012 (Pilot) fuer alle Varianten; H-32 abgeschlossen ohne Test; Vorlage an den Nutzer | - | H-32; mom1, mom2, mom4, rev_gap; A3-fm8 (Pilotabschnitt verbraucht) |
| DEC-102 (Z641) | 2026-10-26 (Nutzer) | Nutzerentscheid zum H-32-Pilotbefund: Option a; neue Hypothese H-33 (beta-neutrales Kurzfrist-Reversal 1-4 Wochen) mit Literatur-Prior; Reihenfolge der Blindperiode offen | Testbarkeit (Etikett im Eintrag) | H-33; H-32 (Pilotbefund); mom1, mom2, mom4; rev_gap (ausgeschlossen, E4); W1/W2 |
| DEC-102 N1 (Z651) | 2026-10-26 | Prior fuer H-33 UNBELEGT (Literaturband je Universum); MDE80 je Variante in Reversal-Richtung; bedingtes Vorab-VETO gegen C10-Registrierung; Default bei Stille: GL-012 | Testbarkeit (Etikett E2, ergaenzt) | H-33 (rev1, rev2, rev4); H-32; W2 (Persistenz-Null) |
| DEC-102 N2 (Z653) | 2026-10-27 | Nutzer waehlt Option 1 (Default): H-33 GL-012 vor Registrierung, kein Bau, kein Vorlauf v7; Klasse W ausgeschoepft | - | H-33; Klasse W und A3-fm8; Programm (Aufzeichnungsmodus) |
| DEC-103 (Z655) | 2026-10-31 (Nutzerentscheid) | A2 (EXP-CLOCK): Placebo-Design neu gefasst (Groessen-Kontrast, Null-Definition, Placebosatz) nach DEC-98 N5/N7; Pilot-Route nur Vorlage | Strenge (Etikett E8: 'Praezisierung ... Richtung Strenge'); Lockerung (Etikett der Pilot-Route, nur Vorlage) | A2 |
| DEC-103 N1 (Z675) | 2026-10-31 | Pilot-Uebergabe-Power bei 16,5 bp und 25 bp berechnet; Review-VETO (Siegel-Kanal) aufloesbar; Vorlage P-0 bis P-3 | Lockerung (Etikett der Pilot-Route, nur Vorlage) | A2 |

## Liste 2: GL (5 Zeilen)

| Nr (Z) | Datum | Hypothese | Ergebnis | Grund (<= 15 Worte) |
|---|---|---|---|---|
| GL-032 (Z9) | 2026-10-12 | H-28/H-29/H-30 Drittfassung (F-XSEC1, A3) | GL-012 vor dem Lauf | Power-Zuordnung mit Boden-SE statt registrierter SE; MDE80 ueber 0,03 in W1; alle sieben Varianten GL-012 |
| GL-033 (Z26) | 2026-10-13 | A1 (H-31, Funding-Long-Bein D1 gegen Universums-Hedge) | GL-012 vor der Registrierung | theta UNBELEGT; Zuordnung bei theta=1 bereits GL-012 (3,168 x SE > Praemie); kein Verdikt |
| GL-034 (Z42) | 2026-10-17 | H-27 (VRP auf DVOL-Backfill, EV-0c) | GL-012 vor der Registrierung | Keine Fensterlaenge 6/9/12 erreicht C10 oder DEC-52; Power bei L=12 nur 0,575 |
| GL-035 (Z58) | 2026-10-21 | H-32 (A3 fm8, Zweistufen-Design), Pilot | GL-012 (Pilot) | Pilot-Uebergaberegel fuer alle vier Varianten nicht erfuellt; kein Test; W1/W2 bleiben blind |
| GL-036 (Z74) | 2026-10-27 | H-33 (beta-neutrales Kurzfrist-Reversal 1/2/4 Wochen) | GL-012 vor der Registrierung | Literatur-Prior fuer beta-neutrales Reversal UNBELEGT; kein Bau, kein Vorlauf; Nutzer waehlte Default |

Zusatz zu GL-034 (Z56, Vermerk 2026-10-21): Erratum-Etikett zu GL-032 bis GL-034. Die Nuisance-Rechnungen nutzten den Ueberlebenden-Baum einschliesslich USDC-Perps und datierter Futures; die Feststellungen bleiben bestehen.

## Liste 3: Kompendium Abschnitt D, verworfene Ansaetze (17 Zeilen)

Die Todesursache ist eine Zuordnung des Listenagenten anhand des angegebenen Belegs. Der Kompendium-Text nennt keine Kategorie.

| Nr (Z) | Kuerzel | Ansatz | Todesursache | Beleg (Kurzzitat aus dem Eintrag) |
|---|---|---|---|---|
| D1 (Z352) | WP-4, DEC-42 | Spread-Capture / Market-Making auf Bybit-Perp-Majors | Friktion | Spread ein Tick, "75-255x unter jeder Gebuehrenwand" |
| D2 (Z358) | C-14 (auch C-30) | Hawkes-Branching-Ratio-Schwelle 0,85 und direkte Wiederholungen | Logik | "Sechs Groessenordnungen unter dem importierten Threshold"; Erreichbarkeit nicht gezeigt |
| D3 (Z363) | CS-02 / S2 | Entropie-Momentum / Sign-Flip-Strategien auf Orderflow-Entropie | Logik | "Verliert auch bei 0 Fees, nicht invertierbar" |
| D4 (Z367) | C-31 (H-03, GL-005) | Cyclostationary CFAR auf publicTrade-Inter-Arrivals | Friktion | "Edge 250x unter der Wand, Surrogate-p~1,0" |
| D5 (Z370) | C-01 / H-05 (auch C-09-OFI, C-14-OFI) | OFI-Vorzeichen als direktes Follow-Signal | Power; Friktion (Nebenbeleg) | "Kein Symbol zeigt konsistent-positives, FDR-signifikantes Vorzeichen"; invers "selbst dort nicht handelbar" (H-05c) |
| D6 (Z374) | C-07 / H-06 | Permutation Entropy als Vol-Cluster-Vorbote | Logik | "PRE-Gate-Korrelation praktisch null (max 0,0145 gegen Schwelle 0,30)"; Grundannahme traegt nicht |
| D7 (Z377) | C-06 / H-07, H-08 | Cross-Sectional Mean-Reversion auf 5-Symbol-Panel, alle Definitionen | Daten | 5-Symbol-Panel, "C-06 auf diesem Panel erschoepft"; Nebenbeleg: "max abs z = 2,0 < 2,5" (Logik) |
| D8 (Z382) | C-09 / H-09 | Risk-Limit-Tier-Bunching als Order-Placement-Signal | Logik | "Reine Rundzahl-Praeferenz, kein Kanten-Effekt; 0/10 Zellen, Rauschmuster" |
| D9 (Z384) | C-10 / H-10 | Cross-Stream-Pointer-Days / Synchronisations-Detektion | Daten | "N=0 Pointer-Tage im gesamten 79-Tage-Fenster" |
| D10 (Z387) | C-12 / H-12 | Cross-Exchange-Fragmentierungs-Eigenstruktur via RMT | Logik | "Zweiter Eigenmodus praktisch vollstaendig delokalisiert" (IPR ~1/6) |
| D11 (Z391) | H-14 | Conditional Cross-Venue-Lead-Lag-Graph via Deep-Learning-Ablation | Positivkontrolle | "Positivkontrolle scheitert" |
| D12 (Z395) | C-20 / H-20 | Tail-Aftermath-Reversion nach Vol-Schocks auf 3,5-sigma-Basis | Logik | "Vorzeichen ueber Symbole und Aeren instabil" |
| D13 (Z398) | C-22 / H-22 | L2-Buchneigung als Folgetags-Richtungssignal | Logik | "Buchtiefe binnen +-25 bps traegt auf 1-Tages-Horizont nichts" |
| D14 (Z401) | C-24 / H-24 | Minuten-Netto-Fluss als Fortsetzungs- oder Lead-Signal | Logik | "Ueber zehn Halbjahre stabil NEGATIVER Forward-IC"; Impact permanent |
| D15 (Z405) | WP-6 | Reaktives Long-Vol (Strangle-Kauf auf Bewegungssignal) | Friktion | Einstieg in Schock-Minuten, "Spread das 10-100-fache" (WP-6); Nebenbeleg: keine Prognose-Hypothese (Logik) |
| D16 (Z410) | CS-04, CS-05 | Schwere Multi-Modell-/Panel-Infrastruktur vor validiertem Basissignal | Logik | "S4/S5-Falle"; "teure Infra ohne validiertes Kernsignal" (Vorgehen) |
| D17 (Z415) | DSM-03; CHAIN-GRAPH, SET-SHAPE; Bitmex-Multi-Zyklen | Superseded / gestrichene Kandidaten (v1/v3) | Daten | "nur 43 Tage"; "Tardis-Sampling nur 2 Tage/3 Monate"; "nur 112 Tage Tiefe" |

Verteilung D-Liste (Zuordnung): Logik 9, Friktion 3, Daten 3, Power 1 (D5, Nebenbeleg Friktion), Positivkontrolle 1.

## Hinweise zur Struktur (ohne Bewertung)

1. Datum k.A. ohne jeden Bezug: 19 DEC-Zeilen (DEC-51, 52, 53, 55, 56, 57, 58, 74, 75, 78 N1, 82 N1, 87, 89, 90, 92, 93, 96, 97, 101 Teil 2). Nur Bezugsdatum: 4 Zeilen (DEC-54, 81, 94, 100). Das Datum von DEC-94 stammt aus der Verfassungsdatei im Verzeichnis scinance3-impl, nicht aus dem Eintrag.
2. Richtung "-": 68 Zeilen. Etikett oder ausdrueckliche Richtung im Eintrag: 14 Zeilen.
3. Mehrfach belegte Nummern: DEC-68 (Z188 und Z266, Nachtrag als eigene Ueberschrift); DEC-101 (Z607, Z620, Z632, drei Teile).
4. H-33 ist in zwei Eintraegen belegt: DEC-98 N5 (Z569) als VRP-Vorlage; DEC-102 (Z641) als beta-neutrales Reversal. GL-036 (Z74) nennt H-34 als naechste freie Nummer.
5. Platzierung: DEC-98 N4 steht als Absatz bei Z589, also im Abschnitt DEC-99 (Z575 bis Z591). DEC-74 N1 (Z262) steht vor der Ueberschrift des DEC-68-Nachtrags (Z266).
6. DEC-98 N4 bis N7 und DEC-100/102/103 Nachtraege sind in der Liste mit eigenem Z-Wert gefuehrt.
7. Keine Siegeldatei (L-Fenster, weekly_ic_series, ic_series_UNION_REAL) geoeffnet. Keine Outcome-Zahl ausgezogen; Zahlen stammen nur aus Titeln und Belegen der Eintraege.
