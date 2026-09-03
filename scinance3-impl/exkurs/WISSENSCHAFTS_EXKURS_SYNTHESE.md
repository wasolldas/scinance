# Wissenschafts-Exkurs (Phase 3b) - Synthese und Entscheidungen des Orchestrators

> 2026-09-03. Fuenf Fachgebiets-Scouts (Opus) in Disziplinen, die der fruehere
> Cross-Domain-Track nicht abgedeckt hatte, danach ein adversarischer Review
> (Opus, nicht Autor). Dieses Dokument ist die Entscheidung; die Berichte und
> der Review liegen daneben in `exkurs/`.

## 0. Ergebnis in einem Satz
**Null neue Alpha-Kandidaten, aber drei Zeilen und zwei billige Messungen,
die bestehende Pakete praeziser machen** - und zwei programmweite Befunde,
die vor jeder A1-/A2-Registrierung geklaert sein muessen. Das ist ein
gutes Ergebnis: der Exkurs hat das getan, was ein Falsifikationsprogramm
von einem Ausflug erwarten darf - er hat Loecher gefunden, nicht Kanten.

## 1. Was uebernommen wird (Entscheidung)

| # | Objekt | Herkunft | Form der Aufnahme |
|---|---|---|---|
| 1 | **Totzonen-/Bindungs-Zensus** des Funding-Sortierschluessels: Anteil der Symbol-Intervalle mit `F` exakt = `I` (0,01 %) | S4 X-NEXP-1 (dort Nebenbefund), Review Top-1 | Erste Messung auf den 113 Harvest-Tagen (Vorfragen-Runner, Minuten); danach Pflichtzeile in WP-7 (`panel_1d`) und A1-Feasibility-Zahl: bei breiter Bindung ist die Dezil-Sortierung degeneriert (GL-012) |
| 2 | **Intervallwechsel-Zensus** (8h->1h je Tag/Dezil/Fenster) | S1 X-SURV-2 + S4 X-NEXP-2, verschmolzen | Zaehl-Vorfrage auf dem A1-Backfill; Intervallklassen-Spalte in `panel_1d`; Materialitaetsgrenze vorab |
| 3 | **Formretention von `r_pre`** (analytisch, 1 h, kein Lauf) | S3 X-ASTRO-2 | Nachtrag zu PRD 5.2; V-5 bekommt Teilfrage (c): Zeitlage der Umkehr relativ zu 08:00 UTC; ohne Beleg ist A2s Richtung nicht registrierbar |
| 4 | **Relaxationsrate nach Schockstunden** (Arm a, deskriptiv) | S2 X-OEKO-1 | Kleines Paket auf dem WP-0-Bar-Cache, Ereignis-Definition aus H-20 geerbt (kein neuer Parameter), N = 403/362 Ereignistage (GL-026); haertet B.8 von n=1 zur Verteilung; Erholungszeit als Konstante fuer Fill-/Slippage-Modelle auf STRESS_ABS |
| 5 | **Konstanten-Nachtrag Klasse P**: (a) der gesetzte Autokorrelations-Parameter 0,30 (PRD 5.1 Kill-4) wird zu `k <= 2,333*w` (Buehlmann-Straub-Credibility); (b) der MaxDD-Boden `1,2533*sigma*sqrt(T)` ist driftlos - Ruin-Kapital `u(eps) = (sigma^2/2mu)*ln(1/eps)` als zweite Berichtszeile | S5 X-AKT-4 L2, X-AKT-2 | Text in PRD 3.6 und 5.1; keine Gate-Aenderung (C.2) |
| 6 | **Time-to-Fill als Competing Risk** (Zensierung durch L2-Abdeckung 74 %/41 %; Nulleffekt exakt bis Faktor 2,0) | S1 X-SURV-3 | Schaetzer-Spezifikation in WP-10(B), kein eigenes Paket |
| 7 | **Delisting-Hazard/IPCW** als Zahl statt Haekchen | S1 X-SURV-1 | Beifahrer in WP-7 (nur deskriptiv, wenn < 32 Delisting-Chargen) |
| 8 | **Change-Point-Segmentierung** als REZENZ-Operationalisierung | S2 X-OEKO-4 + S3 X-ASTRO-1, verschmolzen (3 Detektoren, 2-von-3) | Nur per eigener DEC, mit ausdruecklicher Nicht-Rueckwirkung auf bereits fixierte Fenster; nicht in Welle 1 |
| 9 | **Verfassungszeile "Null-Zensus-Klausel"**: ein Nulleffekt-/Erreichbarkeits-Zensus darf NIEMALS einen Kandidaten promoten; zulaessige Ausgaenge sind D-Eintrag oder "nicht ausgeschlossen" | Review 6.9 | DEC-58; schliesst den H-11-Entstehungspfad |

## 2. Programmweite Befunde und ihre Konsequenzen

**(i) Endogene 8h->1h-Zensierung auf A1s Sortierschluessel** (S1+S4
unabhaengig; Review korrigiert vierfach). Real, aber: der Ausschluss ist
V-1-bedingt (Zins-Term I je Klasse), der Mechanismus existiert erst ab
2025-10-30 [sek] - **W1 ist vor-, W2 zu zwei Dritteln nach-Reform**, das
Vorzeichen des Bias ist auf der urteilstragenden Summe (Funding + Preisbein)
unbestimmt, und der betroffene Anteil ist UNGEMESSEN. Konsequenz fuer A1
(PRD 5.1), in dieser Reihenfolge: V-1 erweitern (I je Klasse inkl. 1h,
Clamp, Cap-Formel, Ausnahmeliste, Auto-Switch, Rueckwechsel) -> Zaehl-
Vorfrage -> Registrierungstext: look-ahead-freie Symbol-Wochen-Regel,
Intervallklassen-Spalte, Pflicht-Sensitivitaet mit intervall-normiert
eingeschlossenen 1h-Symbolen (Bericht, kein zweites Gate) -> schriftliche
Feststellung der **W1/W2-Inhomogenitaet VOR der Registrierung**: eine
W1/W2-Divergenz ist nicht automatisch ein Regime-Befund, sondern kann eine
Betreiber-Regelaenderung sein. IPCW nur, wenn die Zaehlung Materialitaet
zeigt - und dann vorab registriert.

**(ii) `r_pre`-Geometrie** (S3). Richtig: eine V-Umkehr mit Wendepunkt INNERHALB
[07:30, 08:00) annulliert `r_pre`. Kein garantiertes Nullurteil, weil PRD 5.2
den Wendepunkt am Fensterrand liest (Settlement-TWAP endet 08:00) - aber die
Zeitgeometrie ist NIRGENDS belegt. V-5(c) wird Pflicht; kein Filterwechsel
nach dem Sehen von Daten.

**(iii) Bybit-Gebuehrenaenderung 01.09.2026** (S4, [sek]). Liegt NACH allen
urteilstragenden Fenstern, trifft laut Snippet nur Pro-Stufen. Kein Gate
bewegt sich (C.2). Faellig: Konstantenpruefung an der Primaerquelle in
V-4-Nachbarschaft; bis dahin RAISE in `tradability3` fuer Altcoin-Maker;
WP-10(B) `adv_sel_max` bekommt eine Gebuehren-Fussnote.

## 3. Was NICHT uebernommen wird (mit dem einen Grund)
- SIR/SEIR-Kontagion: R0 ist ein Branching-Ratio = D.2-Umbenennung (S1).
- Fruehwarnsignale/Critical Slowing Down als Signal: Literatur negativ,
  `n_eff = T/w` = 2 beim Default (S2); der EWS-Nulleffekt-Zensus X-OEKO-3
  waere K-Inflation mit Kandidaten-Promotion (Review Risiko 3).
- Anytime-valid/e-Werte (X-OEKO-2): Hauptbegruendung durch DEC-53
  entfallen; zweites Inferenz-Regime neben DEC-52 = offener Torpfosten.
- Gestaffelte DiD mit Binance-Backfill (X-NEXP-3): D.16 in Reinform.
- RKD an der Klemme, Diff-in-Disc, IV Verfallstakt (X-NEXP-1/2/4): nur mit
  Auflagen und erst nach erweiterter V-1; N_cluster UNGEMESSEN.
- Praemienprinzipien/TPR (X-AKT-1): kollabieren unter Normalitaet auf den
  Sharpe und erben dessen Untestbarkeit; Tail-Anteil an 6-10 Episoden.
- Insurance-Fund-Ruin (X-AKT-3): erst nach der ohnehin geschuldeten
  Nachladbarkeits-Probe (PRD 3.3.7) fuer `bybit/insurance`.
- Lomb-Scargle-Inventar (X-ASTRO-3), Upcrossing-Trials (X-ASTRO-4),
  Matched-Filter-Messteil (X-ASTRO-2b): Auflagen, D.4-Nachbarschaft bzw.
  Infrastruktur ohne Anwendungsfall.
- Lotka-Volterra Maker/Taker, Chain-Ladder auf Liquidationen, Structure
  Functions, BLS, GP-Imputation: von den Scouts selbst mit Beleg abgelehnt.

## 4. Bilanz
16 Vorschlaege -> 9 Aufnahmen, davon 0 Hypothesen-Kandidaten, 2 kleine
Messpakete (Zensus-Zeilen, Relaxationsrate), 5 Spezifikations-Nachtraege,
1 Verfassungszeile, 1 spaetere DEC. Rechenaufwand gesamt < 1 Personentag
plus Minuten CPU. Die wertvollste Zeile des Exkurses (Totzonen-Zensus)
stand bei ihrem Autor an vierter Stelle eines Nebenabschnitts - der Review
hat sie nach oben geholt. Das rechtfertigt die Zwei-Stufen-Struktur
Scout + Reviewer.
