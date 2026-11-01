# Auftrag (Herleitung/Kritik): Fehler und ungenaue Annahmen im PRD Scinance 3.0 und seiner Verfassung
Lies zuerst state/prd_analyse_2026-11-01/REGELN_UND_LESELISTE.md (Regeln gelten), dann die Leseliste vollstaendig (PRD, CLAUDE.md,
Kompendium, decisions, Bilanz, STAND/UEBERGABE, A2-Akte-Kurzfassungen, Dateninventar). Du bist adversarischer Pruefer
des PRD selbst (nicht einzelner Hypothesen). Ausgabe: state/prd_analyse_2026-11-01/KRITIK_PRD.md.

Pruefe und belege mindestens:
1. Die vier regierenden Zahlen (PRD 1 und 9.2): Horizont-Friktions-Kurve (0,71 bp Orakel, Mindesthorizonte), Sharpe-
   Nachweisdauer nach Lo, IC-Rauschboden, Ein-Fenster-DROP-Kosten. Sind die Herleitungen korrekt? Welche Annahmen stecken
   darin (Kostenannahmen 11/15 bp, Maker-Fill, Normalitaet, Unabhaengigkeit)? Was folgt, wenn sie um Faktor 2 falsch sind?
2. Das Power-/Gate-Geruest (DEC-51/52/94, C.10 zwei 12-Monats-Fenster, Produkt-Zuordnung, Konjunktion gegen Placebos,
   alpha 0,05 einseitig): Fehlerraten und Power im Zusammenspiel; ist "zwei Fenster je 0,80" ein konsistentes Ziel oder
   doppelt konservativ (Gesamt-Power 0,64)? Wie wirkt die Produkt-Regel (DEC-103 E3) bei korrelierten Bedingungen?
   Gibt es Stellen, an denen Strenge-Entscheidungen kumulieren, ohne dass jemand die Gesamtpower kontrolliert?
3. REZENZ 3.0 (DEC-99), Blind-Siegel (DEC-96 E3), Einmal-Gut, Pilot-Verbrauch (DEC-99 (5)), C.17/C.18: Sind diese
   Regeln statistisch notwendig oder Konvention? Wo erzeugen sie Wartezeit ohne Erkenntnisgewinn? Welche
   Alternativen aus der Literatur (Holdout-Design, Nested CV, sequentielle Tests, Alpha-Spending, Pre-Registration mit
   Lockbox) waeren gleich streng bei weniger Wartezeit? Richtung jeweils.
4. Die Kandidatenklassen P/W/E und ihre Priors: Literatur-Prior-Pflicht ([sek], UNBELEGT blockiert) - ist das der
   richtige Mechanismus, wenn Volltexte nicht beschaffbar sind? Alternativen (Pilot als Prior - mit ihren gemessenen
   Grenzen, Bilanz/A2 Teil C), Minimal-Effekt-Lesart (MDE als registrierter Prior "Effekt mindestens X"), Bayes-Prior.
5. Oekonomische Annahmen: Zahler-Identifikation, Friktionswand 11-15 bp (Taker/Maker, Funding-Kosten, Steuern), "kapitalfrei"
   als Mess-Status; REZENZ-Kritik an 2.0 (ETF-Start) - konsistent angewandt?
6. Datenannahmen des PRD gegen das Dateninventar: Was unterstellt das PRD (Universum, Stroeme, Zeitraeume), was liegt
   wirklich vor (z. B. tardis/options_chain 2019-2026, publicTrade 2020-2026 fuer 5 Symbole, orderbook 2023-2026,
   binance ab 2025, allLiquidation ab 2026-06)? Welche Annahmen sind damit ueberholt?
7. Innere Widersprueche und Definitionsluecken (z. B. Placebo "verfallsfrei" bei taeglichen Verfaellen, Fenster-Zeilen,
   Konstanten mit [sek], "Design-Parameter" ohne Pruefung), Stellen, an denen das PRD etwas verspricht, das die
   Datenlage nie zulassen konnte.
8. Fuer jede wichtige Kritik: Welche vergangene Entscheidung (GL-032..036, DEC-93/97/101/102/103) wuerde anders
   ausfallen, wenn der Punkt korrigiert wird? (Nur Richtung und Groessenordnung, keine Neuberechnung mit Daten.)
Form: nummerierte Befunde K-1.., je: Fundstelle, Befund, Beleg/Rechnung (analytisch), Folge, Vorschlag mit Richtung,
Zustaendigkeit (Nutzer / Orchestrator). Abschliessend "Was NICHT folgt". Kurzfassung <= 12 Zeilen.
