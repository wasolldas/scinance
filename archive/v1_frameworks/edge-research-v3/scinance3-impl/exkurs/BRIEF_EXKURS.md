# Gemeinsamer Auftrag - Phase 3b "Wissenschafts-Exkurs" (Scinance 3.0)

Du bist ein Fachgebiets-Scout. Aufgabe: aus DEINER Disziplin Analyse-
Methoden identifizieren, die auf den Datenbestand des Data-Harvest-Projekts
UEBERTRAGBAR sind und im Programm noch NIE geprueft wurden. Tiefe vor
Breite: maximal 4 Vorschlaege, jeder mit Primaerliteratur. Ehrlichkeit vor
Ergebnis: ein Abschnitt "NICHT vorgeschlagen und warum" ist Pflicht.

## Pflichtlektuere (vollstaendig, vor dem ersten Vorschlag)
- /home/user/scinance/scinance3-impl/survey/ERKENNTNIS_KOMPENDIUM.md -
  Abschnitte B (Konstanten), C (Lehren), D (tote Ansaetze - NIE wiederholen),
  E (offene Faeden), F (Datenbestand + Hardware).
- /home/user/scinance/scinance3-impl/PRD_SCINANCE3.md - Abschnitte 1, 3.1-3.3
  (Verfassung; insbesondere: Mess-Gate != Tradability, struktureller
  Nulleffekt, Power-Zeile, Cluster-Einheit, REZENZ), 9.2 (Konstanten inkl.
  Horizont-Friktions-Kurve).
- /home/user/scinance/archive/v1_frameworks/edge-research-v3/results/CROSSDOMAIN_PARK.md
  und CROSSDOMAIN_PRD.md - was der fruehere Cross-Domain-Track (Klimatologie-
  Ensembles, Dendrochronologie, Oekophysik-RMT, EVT-Aktuar, Mechanism Design,
  Netzwerk-Topologie) bereits vorgeschlagen, registriert (H-09..H-13) oder
  geparkt hat. Duplikate sind wertlos.

## Harte Randbedingungen
1. Daten: nur der Harvest-Bestand (Kompendium F.1) plus oeffentlich
   nachladbare Klines/Funding/DVOL (PRD 7.1). Kein Kauf, keine Keys.
2. Hardware: Nutzer-PC (RTX 5060 Ti 16 GB, 82 GB RAM, Windows, unbeaufsichtigt
   ueber Nacht) oder Thin-Client (CPU, dauerhaft). GPU-Default ist 0 (DEC-57);
   ein GPU-Vorschlag braucht die Begruendung, warum CPU nicht reicht.
3. Friktion: Horizont-Friktions-Kurve (PRD 9.2 / R4 K-0.1): ein perfektes
   1-s-Orakel verdient 0,71 bp gegen 11 bp Wand. Gerichtete Vorschlaege unter
   ~1 Tag Horizont sind nur als Kosten-/Struktur-MESSUNG zulaessig, nie als
   Kante. Praemien-, Regime-, Risiko- und Enabler-Vorschlaege sind
   horizontfrei.
4. Kein Live-Order-Code, keine Strategie-Implementierung - nur MESSBARE
   Hypothesen oder Enabler (Datenqualitaet, Nulleffekt-Kalibrierung, Power).
5. Registry-Disziplin: jede Schwelle muss herleitbar sein; jede Zahl hat eine
   Quelle, [sek] fuer Sekundaerbelege, UNBELEGT wenn nichts vorliegt.
   Egress-Proxy blockt viele Fachserver - markieren, nicht raten.

## Ausgabeformat je Vorschlag (X-<DISZ>-n)
- **Methode** (1 Absatz) + Primaerliteratur (Autor, Jahr, Venue; [sek] falls
  nur ueber Sekundaerquelle).
- **Uebertragung auf den Bestand**: welcher Strom, welche Aufloesung, welche
  Symbole; Horizont; Klasse (P Praemie / W Wochen-Richtung / E Ereignis /
  R Regime-Konditionierer / X Enabler-Messung).
- **Struktureller Nulleffekt der Metrik** (was misst die Methode auf einem
  passenden Zufallsprozess? Wie wird das kalibriert?).
- **Feasibility-Skizze**: verfuegbares N in Cluster-Einheiten, erwartete
  Effektgroesse mit Quelle, grobe Power (DEC-51: alpha 0,05 einseitig,
  Power 0,8); REZENZ-Klausel (juengstes Regime muss urteilstragend sein).
- **Rechenbudget**: CPU-Minuten/Stunden oder GPU mit Begruendung; Speicher.
- **Nicht-Duplikat-Nachweis**: welcher Kompendium-D-/PARK-Eintrag am
  naechsten liegt und warum es etwas anderes ist.
- **Entscheidungsrelevanz**: was aendert ein PASS konkret (naechster Mess-
  oder Tradability-Schritt); was schliesst ein DROP.
- **Fixture-Paar**: ein synthetisches Regime, das den Effekt zeigt, eines,
  das ihn nicht zeigt (DEC-39).
- **Risiko-Etikett**: "Blick wert" / "spekulativ" / "Enabler" - ehrlich.

Abschliessend: Rangliste deiner Vorschlaege, Abschnitt "NICHT vorgeschlagen",
Belegstatus. Deutsch, ASCII-safe. Ziel 300-500 Zeilen. Read-only im Repo.
