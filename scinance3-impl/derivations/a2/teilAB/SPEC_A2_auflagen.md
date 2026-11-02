# Auftrag: A2-Vorarbeit, Fassung 2 nach Review (Einarbeitung der Auflagen A-1..A-6)

Rolle: dieselbe Herleitungsrolle wie in `SPEC_A2_vorarbeit.md`; alle dortigen Regeln gelten unveraendert (kein Mittel,
kein Median, kein Vorzeichen irgendeiner Verfallstag-Rendite ausgeben oder speichern; Renditen nur 2021-03-24..2024-05-31;
Settlement-Partitionen nur <= 2026-06-30, nur Felder type/instrument_name/timestamp/position; keine Siegeldateien; kein
Harvest-Client; nichts committen; Skripte nur unter `scratchpad/a2_vorarbeit/`; Ausgabe nur die vier Dateien unter
`scinance3-impl/state/herleitung_a2/`: PLACEBO_DESIGN_A2.md, NUISANCE_SIGMA30.md, ENTSCHEIDUNGSVORLAGEN.md,
a2_vorarbeit.json). REVIEW_A2_VORARBEIT.md und NACHRECHNUNG_ORCHESTRATOR.md nicht anfassen.

Lies zuerst vollstaendig: `scinance3-impl/state/herleitung_a2/REVIEW_A2_VORARBEIT.md` (Urteil ZUSTIMMUNG MIT AUFLAGEN).
Die Reviewer-Skripte unter `scratchpad/a2_review/` darfst du lesen, aber **nicht importieren oder kopieren**: jede neue
Zahl rechnest du mit eigenem Code; der Orchestrator vergleicht beide.

## Aenderungen (nur diese; unveraenderte Teile nicht neu herleiten, Zahlen der Fassung 1 nicht antasten)

A-1 (B-5) Konjunktions-Power als Doppelausweis, je Design (D_i, D_i_W, PRD_a, D_i_s, D_ii): (a) Einzel-Placebo
  (bindend, wie Fassung 1), (b) gemeinsame Power gegen alle Placebos des Satzes (Monte Carlo, gemeinsamer Ereignis-Term,
  Kovarianz der Kontraste = SE_E^2 plus gemessene Same-Day-Korrelation der Placebo-Reihen, Seed fest, >= 200.000
  Replikate), (c) Produkt der Einzel-Powers (Untergrenze). MDE80 je Zeile auf Ereignis-Skala und mit OI-Abschwaechung
  0,842 auf P2'. Fuer D_i zusaetzlich die Varianten Placebosatz {P2'} / {P2', P3fix} / {P2', P3fix, P3all}.
  **Festlegung des Orchestrators (in den Text uebernehmen, als Festlegung kennzeichnen):** die Zuordnung (C10/DEC52/
  GL012) traegt analog DEC-94 (6) das **Produkt** (Untergrenze), die gemeinsame Power ist Bericht; Richtung Strenge.
A-2 (B-6) Abschnitt "Null fuer den Groessen-Kontrast" in PLACEBO_DESIGN_A2.md und ENTSCHEIDUNGSVORLAGEN.md: feststellen,
  dass die PRD-5.2-Null (Zufallstermine mit identischer Kalenderverteilung) unter taeglichen Verfaellen leer bzw. mit dem
  Ereignis identisch ist; zwei Vorlagen mit Richtung: (i) Label-Permutation Freitag <-> Mo-Do innerhalb derselben
  ISO-Woche (erhaelt Wochen-Cluster und Tageszeit), (ii) Slot-Verschiebung bei festen Tagen. **Nicht bauen, nicht rechnen**,
  nur definieren; Etikett "Null neu definiert nach DEC-98 N5". Vorlage: (i) Default bei Stille.
A-3 (B-7) Futures-Kalender aus den Settlement-Rohpartitionen (<= 2026-06-30, nur Namen/Typ/Datum): erste Nicht-Freitags-
  Futures-Delivery je Waehrung, Zahl der Futures-Deliveries je Klasse (Freitag W/M/Q, Mo-Do, Wochenende) und Fenster
  (Vorperiode, W1, W2 bis 2026-06-28), Zahl der Mo-Do-Tage mit Futures-Delivery je Fenster (eine / beide Waehrungen).
  In die Klassenregel und das Kontaminationsregister aufnehmen; Gabelung "P2' ohne Mo-Do-Tage mit Futures-Verfall"
  (N_P je Fenster, SE/MDE80 neu fuer diese Variante, Richtung: Reinheit der Klasse gegen groessere SE) in
  ENTSCHEIDUNGSVORLAGEN mit Default-Vorschlag und Richtung. Freitags-OI: vermerken, dass Wochen-Futures-Verfaelle in der
  Options-OI-Groesse fehlen (Richtung: Abschwaechungsfaktor eher zu klein, Strenge).
A-4 (B-8) CME-Referenzfenster: in die P3-Kontaminationsliste als UNBELEGT aufnehmen (kein Primaerbeleg in der Akte; keine
  Websuche, kein Download); Folge: ein 15:30-Slot wird an Monatsend-Freitagen nicht als Paarungs-/Fix-Slot fixiert, bis
  ein Primaerbeleg vorliegt.
A-5 (B-9) Gabelungen in ENTSCHEIDUNGSVORLAGEN nachtragen, mit Richtung: Differenz-in-Differenzen (eigene Rechnung der
  gepaarten Differenz-SD Mo-Do und Freitag, c, SE, MDE80 je Fenster), historische verfallsfreie Baseline (auf den
  Programm-Instrumenten nicht bildbar, nur Aera-Bericht, Daten UNBELEGT), Beta-Residualisierung des Negativ-Panels
  (Merkposten fuer Gate-Bedingung (4)).
A-6 (B-1..B-3, B-10, B-11): NUISANCE_SIGMA30 Abschnitt 8 "Nicht berechnet" -> "intern berechnet, nie ausgegeben" mit
  Nennung der internen Stellen; `guard_keys` um median/q50/loc/center/diff/contrast/minus erweitern und den Datums-Assert
  auf `start_ms` vor das Lesen der Preisspalten ziehen (Skript + Doku); C.17-Zeile "Betrags-Quantile und 1,4826 x MAD je
  Klasse/Jahr/Serie gesehen, auch fuer die gepaarte Differenz-Reihe" in alle drei MD-Dateien (Kopf-Etikett); fuer
  Differenz-Reihen kuenftig keine unzentrierten Betrags-Quantile ausgeben (in Fassung 2: fuer die Differenz-Reihen die
  Betrags-Quantile aus dem JSON entfernen oder durch zentrierte |r - Zentrum|-Quantile ersetzen - sag im Text, was du
  getan hast); Einheit von `position` als UNBELEGT markieren; Richtung fuer D_ii/PRD_b ausweisen; PRD-5.2-Fenstertext
  (W1 2024-09..2025-08, W2 2025-09..2026-08) nennen und auf DEC-99 (8) verweisen; Rundungen vereinheitlichen (eine Stelle
  fuer MDE80, zwei fuer SE; W1-Werte als Hauptzeile, W2 in Klammern); "[15:30]/[07:30] = 1,30" korrekt beschriften.
  C.17-Inventur W1/W2 (eine Zeile, Fakten vom Orchestrator): die 2.0-Hypothesen H-01..H-18 sahen Bybit/Deribit-Daten
  2026-03-27..2026-07-04 (Mikrostruktur, Sekunden- bis Minutenhorizont), darunter die 08:00-Slots von 2026-03-27 bis
  2026-06-28 in W2; kein r_pre-Mittel ueber 07:30-08:00 wurde dort gebildet; Weiss et al. (2021-2023) liegt vor W1.

## Form
- Kopf jeder MD-Datei: "Fassung 2 (2026-10-29) nach REVIEW_A2_VORARBEIT.md: Auflagen A-1..A-6 eingearbeitet"; am Ende
  jeder Datei ein Abschnitt "Aenderungen gegen Fassung 1" (nummeriert A-1..A-6, je ein bis drei Saetze, mit den neuen
  Zahlen). Zahlen der Fassung 1 bleiben unveraendert (Determinismus: `work/*.json` fuer unveraenderte Teile bitgleich).
- `a2_vorarbeit.json`: neue Bloecke `teil_A5_futures_kalender`, `teil_B5_konjunktion`, `teil_B6_did`; `label` um die
  C.17-Zeile ergaenzt; `stand` = "Fassung 2"; sha256 des neuen JSON im Abschnitt "Aenderungen".
- Waechter wie bisher, plus der erweiterte `guard_keys`; `print` nur sha256. Laufzeit klein halten.
- Kurzfassung an den Orchestrator (<= 10 Zeilen): neue Kernzahlen (Konjunktions-Power/MDE80 D_i je Placebosatz, Produkt;
  Futures-Tage je Fenster; DiD SE/MDE80; neue sha256), was du bei den Betrags-Quantilen getan hast, Guards bestanden.
