# Auftrag: PRD Scinance 3 - Fassung v3 (konsolidierter Entwurf) - 2026-11-02

Rolle: PRD-Text (Herleitung). Du schreibst einen **Entwurf**, keinen Beschluss; der Nutzer beschliesst. Nichts im Repo aendern,
nichts committen, keine Marktdaten, keine Siegeldatei (`scinance3-impl/state/runs/*_L_window_sealed.json`, `weekly_ic_series.csv`,
`ic_series_*_UNION_REAL.csv`), keine Produktnamen von Sprachmodellen (Rollen: Orchestrator, Herleitung, Review, Bau, Kartierung),
keine Hostnamen, ASCII, Deutsch (Code Englisch).

## Zweck (PRD_ANALYSE 9.2 Nr. 9; Kritik K-14 "eine Datei, eine Wahrheit")

Die Verfassung von Scinance 3.0 steht in `scinance3-impl/PRD_SCINANCE3.md` (Stand 2026-09-02, 1.053 Zeilen) plus ~220 kB
bindender Nachtraege in `scinance3-impl/state/decisions.md` (DEC-51..DEC-105 mit Nachtraegen). Eine neue Sitzung muss heute
~6.000 Zeilen lesen, um nichts zu verletzen. Ziel: **eine konsolidierte Fassung v3**, in der jede Regel genau einmal steht, mit
Herkunft (DEC-Nummer), Etikett (Lockerung/Verschaerfung/neutral; Entscheider), Geltung (sofort / ab Kohorte 1 = 2027-01-01) und
markierten Altzeilen (durchgestrichen oder in einem Anhang "ersetzt durch"). Die bestehenden Dateien bleiben unveraendert
(append-only); v3 wird als neue Datei vorgeschlagen.

## Pflichtlektuere (Pfade unter /home/user/scinance/scinance3-impl/)

1. `PRD_SCINANCE3.md` vollstaendig.
2. `state/decisions.md` vollstaendig (DEC-51..DEC-105 inkl. aller Nachtraege; besonders DEC-94, DEC-96, DEC-98 (+N1..N7), DEC-99,
   DEC-101..DEC-105 und DEC-104 Nachtraege 1 und 2).
3. `CLAUDE.md` (Verfassungszusammenfassung), `state/PRD_ANALYSE_2026-11-01.md` (Befunde K-1..K-14, Abschnitte 6, 9; Nachtraege 1-3),
   `state/prd_analyse_2026-11-01/KRITIK_PRD.md` (K-14 Widersprueche), `state/FENSTERREGISTER.md`, `state/KONTO_ZONE_X.md`,
   `state/DATENANNAHMEN_REGISTER.md`, `state/H21_LUECKENLISTE_2026-11-02.md`, `state/gate_log.md` (GL-032..036),
   `state/hypothesis_registry.md` (3.0), `survey/ERKENNTNIS_KOMPENDIUM.md` Abschnitt C (C.1..C.19) und D.
4. `state/prd_analyse_2026-11-01/OC_VERFASSUNG31_2026-11-02.md` (fuer die offene P-2-Frage) und `METHODEN_SWEEP_2026-11-02.md`
   (Abschnitt 3.13: TOST-Form, Enrichment; nur als "vorgeschlagen, N").

## Lieferung

`<scratchpad>/prdv3/PRD_SCINANCE3_v3_ENTWURF.md`
mit dieser Gliederung:

0. **Kopf:** Status "ENTWURF v3, 2026-11-02, nicht beschlossen"; Lesehinweis; Verhaeltnis zu PRD v2 und decisions.md (bis zum
   Beschluss gelten die Originale; v3 ist Lesefassung).
1. **Mission und Grundidee** (PRD Par. 1 mit DEC-105-Erratum 9: Pivot-Begruendung; Mess- vor Pruefinstitution nach DEC-104 E1).
2. **Verfassung 3.1** - je Regel: Nummer, Wortlaut (bindend), Herkunft (DEC), Etikett, Geltung. Gruppen: (a) Kompendium C.1..C.19
   mit Status (unveraendert / ersetzt durch ... fuer 3.1-Registrierungen); (b) Fehlerraten und Entscheidungsregel (DEC-51, DEC-52,
   DEC-94, DEC-104 E2 **mit der offenen Frage P-2 (Screen 0,05 / 0,20 / P-6-Lesart) als markiertem Entscheidungspunkt**, DEC-104 N2);
   (c) Prior/SESOI (DEC-104 E3, DEC-105 Erratum 1 und 8, zwei SESOI-Rahmen); (d) Fenster-Politik (DEC-96, DEC-99, DEC-104 E4 und
   N1: Zonen je Datenfamilie, Kohorten, GSD, Jahresbuch, Lockbox, Vorwissens-Klassen, Konto); (e) Designwahl, REZENZ, A2-Regeln
   (E5, E6, E7, DEC-103); (f) Berichts- und Pruefpflichten (E1, E8, DEC-53, DEC-105 Berichtszeile, t-Grenzen, SESOI-Planung
   nach N2 (6)/(7)); (g) Daten- und Siegelregeln (CLAUDE.md Marktdaten, DEC-96 E3, DEC-103 N1 (2c), Kanal-Scan); (h) Automation
   und Rollen (Modellpolitik als Rollen, Sequenz-Zwang, Zustandsmaschine mit Zonen).
3. **Pflichtzeilen einer Registrierung (3.3 neu):** die zwoelf alten plus `zone`, `cohort`, `alpha_test`, `screen`/`stability_test`,
   `looks`, `sesoi_curve`, `prior_label`, `selection_k`, `oc_line`, `strictness_ratio`, `n_eff`, `c_overlap`, `lesestatus`;
   YAML-Template (3.4 neu) als Codeblock.
4. **Kandidaten und Felder, eine bindende Fassung je Kandidat:** A1 (GL-033, strukturell geschlossen E3 (e)), A2 (DEC-103 Design,
   Status nach DEC-104 N2 (9): haengt an P-2), A3/H-32/H-33 (GL-032/035/036; W1/W2-Vorbelastung N1 (5)), A4 (Fensterwiderspruch
   DEC-105 (12): Vorschlag), A5 (gesperrt), H-27/VRP (GL-034, strukturell geschlossen), H-21/H-26 (2.0, Status nach DEC-105 (11)),
   Felder F1..F12 und Ideenkarten IK-01..IK-11 nur als Verweis mit Status (Zone X / Prior / Siegel).
5. **Datenannahmen** (Verweis auf DATENANNAHMEN_REGISTER, keine Dopplung) und **offene Nutzerfragen** (PRD Par. 8 alt: 8.1 Ausfuehrung
   Default (b), 8.2 Kapital/Steuer, 8.3 Sunset-Review; neu: P-2 Variante, P-10 Klasse P, P-11 Umgebung/Budget, P-12 Protokoll,
   P-13 W1/W2-Mikrostruktur-Zaehlgroessen; Datenauftraege).
6. **Errata-Anhang** (DEC-105 vollstaendig als Tabelle: Fundstelle, alt, neu).
7. **Konkordanz-Anhang:** Tabelle "PRD v2 Abschnitt/Zeile -> v3 Regelnummer -> ersetzende DEC" fuer jede geaenderte Altzeile;
   Liste der in v3 **nicht** uebernommenen v2-Passagen mit Grund.
8. **Pruefliste fuer den Beschluss:** was der Nutzer mit einem Satz bestaetigen muss; was der Orchestrator danach tut
   (CLAUDE.md-Kurzfassung aktualisieren, Registry-Template, Linter F1).

## Regeln

- Kein Satz ohne Herkunft; nichts erfinden. Wo zwei Quellen sich widersprechen, beide zitieren und als "offen" markieren (Liste in
  Abschnitt 5), nicht entscheiden.
- Keine Lockerung einfuehren, die nicht beschlossen ist; nicht beschlossene Vorschlaege (P-2 (c), TOST, Enrichment, P-13) nur als
  "vorgeschlagen, Entscheider N".
- Zahlen nur mit DEC-/Dokument-Fundstelle; Siegel- und Hygieneregeln woertlich uebernehmen.
- Umfang: so kurz wie moeglich bei vollstaendiger Regelabdeckung (Ziel < 900 Zeilen ohne Anhaenge); Anhaenge duerfen lang sein.
- Am Ende eine Kurzfassung (<= 10 Zeilen) an den Orchestrator: Zahl der Regeln, Zahl der ersetzten Altzeilen, Zahl der offenen
  Widersprueche, was du nicht zuordnen konntest.
