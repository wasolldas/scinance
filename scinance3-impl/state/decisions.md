# Entscheidungs-Log Scinance 3.0 (append-only)

> Fortsetzung von `scinance2-impl/state/decisions.md` (DEC-01..DEC-50). Die
> Nummerierung laeuft weiter; die 2.0-Akte wird nicht mehr veraendert.
> Regel unveraendert: DEC-xx = Frage, Optionen, Entscheidung, Begruendung,
> Rueckbauweg. Keine Entscheidung ohne Eintrag, kein Eintrag ohne Entscheidung.

---

### DEC-51 · Power-Konvention 3.0 (bindend fuer jede Registrierung)
- **Anlass:** Die vier Phase-3-Recherchen rechnen mit drei verschiedenen Konventionen (Review 3.10): einseitig/zweiseitig gemischt, Power 0,8 vs. "t=2", Cluster-Einheit teils Symbol, teils Tag, teils Fenster. Ohne gemeinsame Konvention sind Power-Zeilen nicht vergleichbar und Schwellen nicht pruefbar.
- **Entscheidung:**
  1. Mess-Gates: **alpha = 0,05 einseitig** in Hypothesenrichtung (die Richtung ist Teil der Registrierung); zweiseitige Fragen (META/Zensus) alpha = 0,05 zweiseitig, ausdruecklich so etikettiert.
  2. **Power-Ziel 0,80** fuer den in der Power-Zeile benannten Mindesteffekt. Die Power-Zeile nennt den kleinsten Effekt, den das registrierte Fenster mit 0,80 sieht; liegt die A-priori-Erwartung darunter, ist die Registrierung ein GL-012-Fall (Feasibility-DROP vor dem Lauf) oder braucht ein anderes Design.
  3. **Cluster-Einheit** ist die groesste Einheit, innerhalb derer Beobachtungen gemeinsame Schocks teilen: bei Symbol-Panels der **Kalendertag** (bzw. die Kalenderwoche bei Wochenhorizont), bei Ereignisstudien das **Ereignis** (alle Symbole desselben Verfalls = ein Cluster), bei Fenster-Designs das **Fenster**. Effektives N wird als `N_eff = N/(1+(N-1)*rho)` mit GEMESSENEM rho ausgewiesen; rho = 0 ist nie Default.
  4. **Selektions-K** (Zahl der vorab benannten Varianten) steht in jeder Registrierung; die Schwelle liegt ueber der Bailey/Lopez-de-Prado-Decke fuer dieses K (R4 K-0.3).
  5. **Ueberlappende Renditen** zaehlen nicht als unabhaengige Beobachtungen; effektives N ueber Blocklaenge = Ueberlappung (R3-K-37-Lehre, Review 2.4).
- **Begruendung:** reine Vergleichbarkeit; die Werte selbst sind Standard (Lo 2002; Bailey/LdP 2014). Keine Gate-Schwelle wird dadurch veraendert.
- **Rueckbauweg:** Dokumentation; betrifft nur kuenftige Registrierungen.

---

### DEC-52 · (ENTWURF, NICHT BESCHLOSSEN) Kontrollierte Entschaerfung des harten Ein-Fenster-DROP fuer Klassen mit Per-Fenster-Power < 0,6
- **Status:** Entwurf. Wird erst beschlossen, wenn der Retro-Check auf H-06/H-20/H-22 vorliegt und veroeffentlicht ist. Bis dahin gilt PRD-2.0 §8.5 / Kompendium C.10 unveraendert.
- **Anlass:** R4 K-0.6: bei Per-Fenster-Power 0,5 verwirft die harte Regel 3 von 4 echten Effekten. Review 4.1 haelt eine Aenderung nur unter fuenf Auflagen fuer legitim.
- **Vorgesehene Regel (woertlich, mit den fuenf Review-Auflagen):**
  (i) nur anwendbar, wo die Power-Zeile VOR dem Lauf Per-Fenster-Power < 0,6 ausweist; Zensus-artige, hoch-gepowerte Fragen behalten die harte Regel;
  (ii) je Fenster: Punktschaetzer mit hypothesiertem Vorzeichen UND >= 0,5x der registrierten Schwelle;
  (iii) Signifikanz ausschliesslich auf dem GEPOOLTEN Schaetzer mit fenster-geclustertem stationaerem Bootstrap;
  (iv) gepooltes alpha = 0,01 (nicht 0,05), weil der Zwei-Fenster-Filter das alpha nicht mehr traegt;
  (v) Retro-Check auf H-06, H-20, H-22 wird veroeffentlicht; kippt er ein Verdikt, wird die Regel als "Lockerung" etikettiert, die alten Verdikte bleiben unveraendert.
- **Sequenz-Zwang:** Die Regel wird NIE kandidatenspezifisch beschlossen. Sie muss VOR der Registrierung des ersten Kandidaten stehen, der sie braucht (Review 4.1 Auflage 1) - sonst waere sie eine Torpfosten-Verschiebung.
- **Rueckbauweg:** Streichen des Eintrags vor Beschluss; nach Beschluss nur durch neue DEC.

> **Nachtrag zu DEC-52 (2026-09-02): Retro-Check liegt vor, Regel BESCHLOSSEN.**
> `state/RETROCHECK_DEC52.md`: kein Verdikt kippt. H-06 verfehlt den
> 0,5x-Screen in beiden Fenstern und beiden Metriken (7-62 % der halben
> Schwelle); H-22 faellt am Vorzeichenwechsel in BTC W-L2-2 (IC +0,067 ->
> -0,011); H-20 ist der einzige knappe Fall (OOS-1 +4,83 bp gegen 5-bp-Screen,
> Abstand 0,17 bp), waere aber auch bei bestandenem Screen an der gepoolten
> Signifikanz gescheitert (Proxy-Obergrenzen p ~0,20-0,34 gegen alpha 0,01).
> **Einschraenkung, offen benannt:** Auflage (iii) - gepoolter, fenster-
> geclusterter Bootstrap - war fuer die 2.0-Laeufe NICHT nachrechenbar, weil
> keiner der drei Ergebnis-JSONs Roh-Serien je Cluster oder Bootstrap-
> Replikate speichert; der Retro-Check nutzt Stouffer/Fisher-Kombinationen der
> Fenster-p als OBERGRENZE der Evidenz. Da selbst diese Obergrenzen alpha 0,01
> um Faktor >20 verfehlen, ist der Schluss robust. Etikett: **Verbesserung**,
> nicht Lockerung.
> **Daraus folgt eine neue Pflicht (DEC-53).**

---

### DEC-53 · Ergebnis-Artefakt-Pflicht: jeder 3.0-Lauf speichert die Cluster-Serie und die Bootstrap-Replikate
- **Anlass:** Der DEC-52-Retro-Check konnte den gepoolten Bootstrap nicht nachrechnen, weil 2.0-Ergebnis-JSONs nur Aggregate speichern (Review-Lehre: Checkpoint-Round-Trip C.15 auf Ergebnisse ausgeweitet).
- **Entscheidung:** Jeder 3.0-Treiber schreibt neben dem Summary (a) die urteilstragende Serie auf Cluster-Ebene (je Kalendertag/Woche/Ereignis, gemaess DEC-51 Cluster-Einheit) als Parquet/CSV mit SHA-256, (b) die Bootstrap-Replikate des Gate-Schaetzers (mindestens die 1.000 Ziehungen) oder den Seed + Generator-Fingerprint, aus dem sie bit-identisch reproduzierbar sind. Ein Lauf ohne (a)+(b) ist KEIN VERDIKT (loud fail im Treiber, Test gepinnt).
- **Begruendung:** Ohne Cluster-Serien sind Regel-Retro-Checks, Meta-Analysen ueber Kohorten und die Portfolio-Sicht (R4 6.2a) unmoeglich; die Kosten sind Megabytes.
- **Rueckbauweg:** Treiber-Konvention; alte 2.0-Laeufe bleiben, wie sie sind.

---

### DEC-54 · Repo-Umbau fuer 3.0: Versionsordner fuer Akten/Artefakte, Quarantaene fuer toten Code, lebender Baum unveraendert
- **Anlass:** Nutzer-Auftrag "Repo aufraeumen, Struktur erzeugen, Basis fuer einen ueberdachten Ansatz". Grundlage: Code-Map (Import-Graph), Infra/Ops-Map (lokale Kopplungen), bestaetigter `CLEANUP_PLAN.md` (2026-06-23).
- **Optionen:** (a) starre Versionsordner `v1/ v2/ v3/` fuer Code; (b) Versionsordner nur fuer Akten und Artefakte, toter Code als Quarantaene-Unterpaket im selben Paket; (c) toten Code loeschen (Git-Historie als Archiv).
- **Entscheidung: (b).** (a) haette ~13.000 Zeilen Import-Umschreibungen ueber Paketgrenzen oder doppelte Pakete erzeugt; (c) verletzt den Nutzer-Wunsch, verworfene Ansaetze als Artefakte sichtbar zu halten, und das Schutzgut "Test-Suite wird nie reduziert". Ergebnis: `archive/v1_frameworks/` (vier Doku-Frameworks, 0 Code), `archive/v1_scripts/` (9 Legacy-Skripte), `src/bybit_edge/_legacy_v1/` (kompletter 1.0-Stack, importierbar, getestet), `scinance2-impl/` unveraendert plus `FINAL_PRD_SCINANCE2.md`, `scinance3-impl/` als 3.0-Akte; lebender Baum `config.py`, `recorder/`, `persistence/db.py`, `research/` unangetastet (Diff = 0 Dateien).
- **Abnahme (vom Orchestrator nachvollzogen, nicht nur gemeldet):** 1.495 gesammelte Tests vorher und nachher; 1.483 bestanden / 3 vorbestehende Fehler (torch-Abwesenheit in `test_execution_live.py`) / 9 Dependency-Skips - identisch; die vier Forensik-Tests byteidentisch (`git diff --stat` leer) und gruen; kein lebendes Modul importiert Legacy (grep leer); Schutzgut-Pfade (Recorder, config, db, research, .ps1/.bat, fixtures, scinance2-impl) ohne Aenderung. Eine vom Agenten vorgenommene Docstring-Aenderung in `research/c14_panellag/encoder.py` wurde ZURUECKGENOMMEN - "research/** unangetastet" gilt woertlich, auch fuer Kommentare.
- **Compat-Shims:** `src/bybit_edge/strategies/__init__.py` und `src/bybit_edge/replay_backtester.py` servieren das REALE `_legacy_v1`-Modulobjekt unter dem alten Namen (sys.modules-Alias), damit `mock.patch`-Ziele der Forensik-Tests weiter das echte Objekt treffen. Neuer Code schreibt nie gegen die Shims.
- **Bekannte Folgearbeit:** `scripts/evaluate_e15.py` traegt veraltete Default-Pfade (zeigen auf das verschobene `edge-reconciliation/`); als Schutzgut-Skript unveraendert gelassen, von keinem Test erreicht. Bei naechster Nutzung anpassen (eigene DEC).
- **Lokale Kopplungen:** keine der drei Scheduled Tasks, die Junction, `start.bat` oder ein `handoff_local`-Pfad ist betroffen; kein Re-Registrieren noetig.
- **Rueckbauweg:** reine `git mv`-Historie; `git revert` des Umbau-Commits stellt den Vorzustand her.

---

### DEC-55 · Kanonischer Stress-Kanon als Fixture (Design-Parameter, keine Gate-Schwelle)
- **Anlass:** "Stress-Episode" war in den Recherchen ein undefinierter Gate-Begriff (Review R1-R4 6.6); DEC-45 und WP-6 benutzen ihn bereits. Ohne kanonische Definition ist jede stress-bedingte Klausel ein offener Torpfosten.
- **Entscheidung:** Der Stress-Kanon ist eine deterministisch erzeugte Tagesliste aus dem WP-0-Bar-Cache: alle UTC-Tage, deren realisierte Tagesvol (BTC oder ETH) ueber dem 97,5-Perzentil der juengsten 24 Monate liegt, plus der 2026-08-19 als Referenz-Ereignis; zusammenhaengende Tage mit hoechstens einem Nicht-Stress-Tag Luecke bilden EINE Episode. Die Liste wird als Fixture mit SHA-256 gepinnt und je Kalendermonat fortgeschrieben (append-only; alte Eintraege aendern sich nicht).
- **Etikett (bindend):** 97,5 %, 24 Monate und die Luecken-Regel sind DESIGN-PARAMETER, keine Gate-Schwellen. Keine Hypothese darf sie variieren oder eine eigene Stress-Definition einfuehren; wer eine andere braucht, registriert sie als neue DEC vor dem Lauf.
- **Rueckbauweg:** Fixture-Datei + Generator-Skript; Entfernen stellt den Vorzustand her.

---

### DEC-56 · Stress-Kanon praezisiert: rollierende Liste ist Abdeckungs-Nachweis, absolute Zweitliste STRESS_ABS fuer Liquiditaets-Fragen
- **Anlass:** Offener Punkt V2-1 des PRD-Entwurfs (Review PRD3 W-10): ein rollierender 97,5-Perzentil-Schnitt erzeugt per Konstruktion ~2,5 % Stress-Tage in JEDEM Fenster; die Klausel ">= 1 Stress-Episode je urteilstragendem Fenster" kann damit nie binden. Zweitens misst ein relativer Vol-Schnitt Vol-Regime, nicht Liquiditaets-Crashs, die WP-10(A) braucht.
- **Entscheidung:** (1) Die DEC-55-Liste (`STRESS_REL`) wird ausdruecklich als **Abdeckungs-Nachweis** gefuehrt (das Fenster enthaelt nachweislich seine Regime-Extreme), nie als Filter oder Gate. (2) Eine zweite, absolute Liste **`STRESS_ABS`** wird als Fixture eingefuehrt: alle UTC-Tage, deren realisierte Tagesvol (BTC oder ETH) ueber dem 99-Perzentil der GESAMTEN WP-0-Historie liegt, plus namentlich **2025-10-10** und **2026-08-19**. `STRESS_ABS` ist die Stress-Definition fuer WP-10(A) (Praemien-Kohaerenz) und fuer jede Liquiditaets-/Fill-Frage. (3) 99 % und die zwei benannten Tage sind DESIGN-PARAMETER (kein Gate, nicht variierbar); Ergaenzungen der Namensliste nur per neuer DEC.
- **Rueckbauweg:** Fixture + Generator; Entfernen stellt DEC-55 allein wieder her.

---

### DEC-57 · GPU-Standardbudget je Hypothese = 0; 24-h-Grenze ist Meldegrenze, keine Schwelle
- **Anlass:** ~350 GPU-Stunden in 2.0 (H-14..H-18) mit 2 kapitalfreien WEITER und 0 registrierten Tradability-Folgen (R4 K-0.7, 6.1a); keine der drei 3.0-Klassen braucht GPU (R4 4.2).
- **Entscheidung:** GPU-Budget je Hypothese ist standardmaessig 0. Ein GPU-Lauf braucht (a) eine registrierte Begruendung, warum die CPU-Fassung die Frage nicht beantworten kann, und (b) eine Entscheidungsrelevanz-Zeile mit Tradability-Pfad. Die aus R4 vorgeschlagene 24-h-Wall-Clock-Kappe wird NICHT als Schwelle uebernommen (unhergeleitet; H-15 lief 180 h checkpointet und lieferte ein gueltiges WEITER), sondern als Meldegrenze: Laeufe > 24 h werden vor dem Start gemeldet und begruendet. Wirksames Instrument bleibt die Positivkontroll-Vorschaltung (Pflichtzeile 3.3.8).
- **Rueckbauweg:** Dokumentation.

---

### DEC-58 · Phase 3b Wissenschafts-Exkurs: Aufnahmen, Null-Zensus-Klausel, A1-/A2-Auflagen
- **Anlass:** Fuenf fachfremde Scouts (Survival/Epidemiologie, Oekologie/kritische Uebergaenge, Astrostatistik, natuerliche Experimente, Aktuar/Ruin) plus adversarischer Review (`exkurs/REVIEW_S1_S5.md`). Synthese in `exkurs/WISSENSCHAFTS_EXKURS_SYNTHESE.md`.
- **Entscheidung 1 - Aufnahmen (keine Hypothesen-Kandidaten):** (a) Totzonen-/Bindungs-Zensus des Funding-Sortierschluessels als Vorfrage und WP-7-Pflichtzeile; (b) Intervallwechsel-Zensus 8h->1h auf dem A1-Backfill; (c) analytische Formretention von `r_pre` als Nachtrag zu PRD 5.2, V-5 um Teilfrage (c) erweitert; (d) Relaxationsrate nach Schockstunden (X-OEKO-1a) als kleines deskriptives Paket auf dem Bar-Cache; (e) Konstanten-Nachtrag Klasse P: `k <= 2,333*w` statt gesetztem 0,30, Ruin-Kapital neben driftlosem MaxDD-Boden; (f) Competing-Risk-Schaetzer fuer Time-to-Fill in WP-10(B); (g) Delisting-Hazard/IPCW als Beifahrer in WP-7; (h) Change-Point-REZENZ nur per spaeterer DEC mit Nicht-Rueckwirkung.
- **Entscheidung 2 - Verfassungszeile (Null-Zensus-Klausel):** Ein Nulleffekt-/Erreichbarkeits-Zensus darf NIEMALS einen Kandidaten promoten; zulaessige Ausgaenge sind ein D-Eintrag oder "nicht ausgeschlossen". Jede Registrierung, die aus einem Zensus hervorgeht, braucht eine eigene, vorab formulierte Hypothese mit eigenem K. (Schliesst den H-11-Entstehungspfad; betrifft X-OEKO-3/X-ASTRO-3 unmittelbar.)
- **Entscheidung 3 - A1-Auflagen (vor jeder Registrierung, PRD 5.1):** V-1 wird erweitert (Zins-Term I je Kontraktklasse inkl. 1h, Clamp-Grenze, Cap-Formel, Ausnahmeliste, Auto-Switch- und Rueckwechsel-Regel an der Primaerquelle); Ausschluss der 1h-Klasse nur als look-ahead-freie Symbol-Wochen-Regel; Intervallklassen-Spalte in `panel_1d`; Pflicht-Sensitivitaet mit intervall-normiert eingeschlossenen 1h-Symbolen (Bericht, kein zweites Gate); **schriftliche Feststellung der W1/W2-Inhomogenitaet** (Auto-Switch ab 2025-10-30 [sek]: W1 vor-, W2 ueberwiegend nach-Reform) - eine W1/W2-Divergenz ist damit nicht automatisch ein Regime-Befund. IPCW nur bei gemessener Materialitaet und dann vorab registriert.
- **Entscheidung 4 - A2-Auflage:** Ohne Primaerbeleg der Zeitlage der Umkehr relativ zu 08:00 UTC (V-5c) ist A2s Richtung nicht registrierbar; kein Wechsel der Teststatistik nach dem Sehen von Daten.
- **Entscheidung 5 - Gebuehren:** Die [sek]-gemeldete Bybit-Gebuehrenaenderung 01.09.2026 beruehrt kein Gate (C.2); Konstantenpruefung an der Primaerquelle (V-4-Nachbarschaft), bis dahin RAISE fuer Altcoin-Maker in `tradability3`, Gebuehren-Fussnote an `adv_sel_max` in WP-10(B).
- **Nicht uebernommen:** SIR (D.2), Fruehwarnsignale, e-Werte, gestaffelte DiD mit Binance-Backfill, RKD/Diff-in-Disc/IV vor erweiterter V-1, Praemienprinzipien/TPR, Insurance-Fund-Ruin vor Nachladbarkeits-Probe, Periodizitaets-Inventar, Upcrossing-Trials - Gruende in der Synthese.
- **Rueckbauweg:** Dokumentation + Spezifikations-Nachtraege; kein bestehendes Gate veraendert.

---

### DEC-59 · Welle-1-Vorfragen: A4 recording-first, A1-Nulleffekt als Totzonen-Modell neu aufgesetzt, Intervall-Heterogenitaet ist 4h/8h
- **Anlass:** Vorfragen-Lauf 2026-09-08 (`state/WELLE1_VORFRAGEN_BEFUND_2026-09-08.md`). Alle Konsequenzen waren vorab fixiert (PRD 4.4/11); hier wird der eingetretene Zweig festgestellt.
- **A4 (Perp vs. datierter Future): RECORDING-FIRST.** Datierte Kontrakte existieren (40 linear, 4 inverse), `turnover24h` der vordersten BTC/ETH-Kontrakte 45.000-530.000 USD gegen Perp-Umsatz in Milliarden (< 1 %). Vorab fixierte Konsequenz: nicht gestrichen, erst nach >= 12 Monaten Quote-Aufzeichnung registrierbar. Kein Alpha-Slot in Welle 1/2.
- **A1-Nulleffekt: die Anker-Formulierung wird ersetzt.** V-3 zeigt alle sieben Symbole systematisch unter I (Median F-I = -0,0059 %/8h), V-6 zeigt 11-46 % aller Intervalle EXAKT bei I. Das bestaetigt die Klemm-Formel `F = P + clamp(I-P, +-0,05 %)`: I ist Totzonen-Wert, nicht Erwartungswert. Neu fuer die A1-Registrierung: (1) Nulleffekt = Totzonen-Modell mit Klumpen bei I und symbolabhaengigem Tie-Anteil; (2) Sortierschluessel = Wochen-SUMME, Tie-Anteil je Woche/Dezil als Pflichtausgabe; (3) WP-7 misst den Totzonen-Anteil je Symbol-Dezil auf dem vollen Backfill; (4) Kill-Bedingung "Dezil-Degeneration" mit einer Grenze, die VOR dem A1-Lauf aus dem WP-7-Befund hergeleitet wird. Die im PRD 5.1 stehende Herleitung "I kuerzt sich im Querschnitt heraus" bleibt als notwendige, nicht hinreichende Bedingung stehen.
- **Intervall-Heterogenitaet ist 4h/8h, nicht 1h/8h.** instruments-info: 412 Symbole mit 240 min, 409 mit 480 min, 1 mit 60 min. Der A1-"1h-Ausschluss" ist gegenstandslos; `funding_n`-Normierung ist Kern des Sortierschluessels. Die DEC-58-Selektionsfrage gilt fuer den 4h/8h-Wechsel je Symbol; die Auslese-Mechanik ist an der Primaerquelle zu klaeren (V-1 erweitert). Caps sind stark heterogen (BTC/ETH 0,333 %, Masse 2,0-2,5 % je Intervall) - Cap-Treffer-Ereignisse sind fuer Alt-Perps um Faktor 6-8 seltener; X-NEXP-2 (Diff-in-Disc) muss das in seiner N_cluster-Zaehlung beruecksichtigen.
- **V-5a:** Deribit fuehrt Tages-, Wochen-, Monats- und Quartalsverfaelle; A2-P1(a) real, P1 leer, A2 bleibt GL-012 bis V-5b/c. Bybit-datierte Futures verfallen freitags.
- **Nebenbefund:** `deliveryFeeRate` ist ein instruments-info-Feld - V-4(b) wird beim naechsten Vorfragen-Lauf maschinell gelesen.
- **Rueckbauweg:** Dokumentation; PRD-5.1-Text erhaelt einen Nachtrag, kein bestehender Text wird geaendert.

---

### DEC-60 · WP-11 Lauf 1: Schaetzer uninformativ (real ~ Pseudo-Null) - Umstellung auf Superposed-Epoch-Mittelprofil
- **Anlass:** Echtlauf WP-11 (2026-09-08, 3.570 Ereignisse aus der H-20-Definition, 1.468 Ereignistage; `state/runs/wp11_20260908/`). Die per-Ereignis-AR(1)-Halbwertszeiten (Median Volumen 0,142 h, RV 0,072 h) sind praktisch identisch mit denen der gematchten Pseudo-Zufalls-Null (0,120 h / 0,065 h); gleichzeitig kehren ~23 % der realen Ereignisse binnen 24 h nie auf 10 % des Schock-Excess zurueck. Beides zusammen zeigt: der Schaetzer misst das generische Kurzgedaechtnis der 5-Minuten-Excess-Reihe, nicht die Relaxation des Schocks.
- **Einordnung (ehrlich):** Fehler in der Orchestrator-Bauvorgabe (per-Ereignis-Fit statt Mittelprofil). Das DEC-39-Adversarial-Fixture hat den Selektionsartefakt abgesichert - den richtigen Fehlermodus (Uninformativitaet durch Rauschen) nicht. Lehre, aufgenommen in die Verfassung: **jede deskriptive Messung braucht neben Positiv/Null/Adversarial die Pseudo-Null-VERGLEICHSZEILE in der Hauptausgabe** - real vs. gematchte Null nebeneinander, nicht nur als Varianzverhaeltnis.
- **Entscheidung:** WP-11 v2 misst das mittlere Excess-Profil in Ereigniszeit (Superposed-Epoch-Analyse; Standard in Klimatologie/Astrophysik), zieht das Pseudo-Null-Profil (Selektions-Bump = struktureller Nulleffekt) ab und fittet exponentiell und als Potenzgesetz auf dem Differenz-Profil mit Cluster-Bootstrap-CI. Die v1-Kennzahlen bleiben als Diagnostik im Report, tragen aber keine Ausgabe (i)-(iii) mehr. Kein PASS/FAIL, keine Schwelle (unveraendert).
- **Was der Lauf trotzdem geliefert hat:** die Ereignismenge (N gemessen, Aera-Verteilung), die STRESS_ABS-Untergruppe ist mit 27 Ereignistagen unter dem 30-Cluster-Floor - RECOVERY_H_P90 auf STRESS_ABS ist heute KEIN BEFUND (korrekt so ausgewiesen).
- **Rueckbauweg:** v2 ist additiv; v1-Artefakte bleiben mit Fingerprint erhalten.

---

### DEC-61 · WP-9 Befund B1: DVOL-REST-Backfill (2021-03-24 ff.) ist mit dem Harvester-Strom austauschbar - H-27-Klasse eroeffnet, nicht registriert
- **Anlass:** Echtlauf WP-9 2026-09-09 (`state/runs/wp9_20260909/`, `state/WELLE1_BEFUND_TEIL2_2026-09-09.md`). F1: 1.996 Tage je BTC/ETH ab 2021-03-24. F2: 176 Ueberlappungstage, Tagesdifferenz REST-Close minus Harvest-Letztframe exakt 0 auf jedem Tag; Materialitaetsband +-0,3 erreichbar; Befund a.
- **Entscheidung:** Vorab fixierte Konsequenz B1 (PRD 4.2) tritt ein: die H-27-Klasse (VRP auf REST-Backfill-Basis) darf als eigene, vorab zu formulierende Hypothese mit eigenem K vorregistriert werden. Registriert wird nichts vor dem Abschluss von Welle 1 (PRD 9.3 Punkt 7). REST-DVOL darf ab sofort als IV-Quelle in deskriptiven Paketen (WP-10(A2)) benutzt werden; Harvester-DVOL und REST-DVOL werden dabei NICHT gemischt, sondern der REST-Backfill wird durchgehend verwendet.
- **Unveraendert:** H-26 bleibt gegen `done_days` gesperrt; C-33-Uhr unberuehrt.
- **Rueckbauweg:** Dokumentation.

---

### DEC-62 · WP-10(A): Stress-Kohaerenz ist mit Harvest-Aera-Serien nicht messbar - Wiederholung als WP-10(A2) auf nachgeladenen Tagesserien; Ruhe-Matrix und Portfolio-Konstanten uebernommen
- **Anlass:** Echtlauf WP-10(A) 2026-09-09 (`state/runs/wp10a_20260909/`). STRESS_ABS enthaelt 30 Tage/19 Episoden seit 2020-05; die Bestandsserien beginnen 2024-03 (Funding BTC/ETH), 2025-08 (IV-RV), 2026-03 (Funding SOL/XRP/BNB), 2026-06 (Basis): Stress-Ueberlappung 0-3 Tage je Paar, alle Stress-Zellen `TOO_FEW`. Das PRD hatte 6-10 Episoden erwartet; die Erwartung war falsch, weil sie die Aera der Serien nicht gegen die Aera des Kanons gehalten hat.
- **Entscheidung 1 - WP-10(A2):** dieselbe Messung (Spearman-Matrix Stress/Ruhe, Cluster-Bootstrap, Bonett/Wright, struktureller Nulleffekt) auf Tagesserien, die bis zum Kanon-Beginn zurueckreichen: Funding-Cashflow aus der oeffentlichen `funding/history` (V-1: vollstaendig nachladbar; Quelle `panel_1d.funding_sum` aus WP-7, ersatzweise direkter Abruf fuer BTC/ETH/SOL/XRP/BNB), IV-RV aus REST-DVOL (DEC-61) minus Bar-Cache-RV, Basis-Proxy weiterhin Harvest-only (61 Tage; Backfill ueber `premium-index-price-kline` erst nach Probe). Neuer Treiber-Modus `--source backfill`, alte Bestandsserien bleiben als Vergleichszeile (Pseudo-Null-Vergleichslehre aus DEC-60 sinngemaess: Bestand vs. Backfill nebeneinander auf der gemeinsamen Ueberlappung). DEC-39-Trio unveraendert gueltig; Pflichttest: Backfill- und Bestandsserie muessen auf der Ueberlappung identische Tageswerte liefern (Funding) bzw. innerhalb des WP-9-Bands (IV).
- **Entscheidung 2 - Uebernommene Konstanten (PRD 9.2, keine Schwellen):** Ruhe-Matrix (Funding untereinander 0,24-0,51; IV-RV BTC/ETH 0,907; Funding x IV-RV ~0); Portfolio-Nulleffekt der Gleichgewichtung k=2..5 (E[SR] ~0, SD ~0,40, p95 ~0,65, p99 ~0,95); Selektions-Obergrenze E[max SR] fuer K=5..100 (0,46..0,97 empirisch; sigma_SR 0,398). Alle mit Seed 53 und Fingerprint reproduzierbar.
- **Entscheidung 3 - Folgen fuer Registrierungen:** Ledoit-Wolf-`N_eff` (WP-7) wird Pflichtangabe fuer A1 (Funding-Beine sind kohaerent); BTC+ETH zaehlen fuer H-27/A5 als EIN Bein; die abhaengigkeitsrobuste Ueber-Familien-Korrektur bleibt in Kraft, solange die Stress-Zelle leer ist.
- **Rueckbauweg:** additiver Treiber-Modus; Bestandslauf bleibt mit Fingerprint erhalten.

---

### DEC-63 · WP-11 v2: Nach-Schock-Ueberschuss zerfaellt potenzgesetz-artig auf Tages-Skala - Konstante fuer Kostenmodell und Cluster-Einheit; kein Kandidat
- **Anlass:** Echtlauf WP-11 v2 2026-09-09 (`state/runs/wp11_20260909/`, Profilmatrix 7.776 Zeilen mit Real-/Pseudo-/Differenz-CI). Differenzprofil bei t=0: 1,22 [1,13; 1,31] z-Einheiten; Halbwertszeiten des Exponentialfits BTC/ETH 22-31 h (R^2 0,24-0,37), Potenzgesetz-Exponent 0,23-0,32; XRP/BNB 7-20 h; SOL-Volumen 2,5 h (R^2 0,83). v1 (0,07-0,2 h) war Rauschgedaechtnis (DEC-60 bestaetigt).
- **Entscheidung:** (1) Deskriptor "Nach-Schock-Regime = Tages-Skala, langsamer (Omori-artiger) Zerfall" geht als Konstante in PRD 9.2 und in `tradability3` (Stress-Kostenfenster mindestens ein Kalendertag nach Schockstunde). (2) Cluster-Einheit Kalendertag fuer alle Bar-Cache-Pakete bestaetigt; ein Schock-Tag ist EIN Cluster. (3) RECOVERY_H_P90 auf STRESS_ABS bleibt KEIN BEFUND (27 < 30 Ereignistage); der Floor wird nicht bewegt, die Zelle fuellt sich nur durch neue Kanon-Tage. (4) Null-Zensus-Klausel: kein Kandidat; X-OEKO-1 Arm (b) nur als getrennt vorregistrierte Hypothese.
- **Report-Korrektur:** Tabellen (i)/(iii) trugen im Lauf-Report keine Variablenspalte (Zeilenreihenfolge Volumen/Trades/RV); im Code behoben, Werte unveraendert.
- **Rueckbauweg:** Dokumentation.

---

### DEC-64 · WP-10(A2): Stress-Zelle besetzt (n 14-28), Funding-Kohaerenz steigt im Stress - Surrogat-Null nachzuruesten, bevor die Matrix Konstante wird
- **Anlass:** Echtlauf WP-10(A2) 2026-09-09 (`state/runs/wp10a2_20260909/`, `state/WELLE1_BEFUND_TEIL3_2026-09-10.md`). Backfill reproduziert den Bestand exakt (Funding max|diff| 0 auf 128-883 Tagen; IV 0 Vol-Punkte auf 165 Tagen). Stress-Zellen: 9 von 10 Funding-Paaren mit rho_Stress 0,6-0,7 gegen rho_Ruhe 0,2-0,35; IV-RV BTC/ETH 0,89/0,88; BTC-Funding x IV-RV im Stress -0,43/-0,46.
- **Festgestellte Bauluecke (Orchestrator):** Der vom PRD 4.3 verlangte strukturelle Nulleffekt der Extremstichprobe (Block-Bootstrap aus unkorrelierten Surrogaten gleicher Randverteilung) war im Treiber nicht umgesetzt; das DEC-39-Adversarial-Fixture prueft einen anderen Fehlermodus (gemeinsamer Trend). Die Abnahme von WP-10(A) haette das sehen muessen.
- **Entscheidung:** (1) `surrogate_null` wird nachgeruestet - je Paar B = 1.000 seeded Surrogate in zwei Varianten: (a) unabhaengige stationaere Block-Surrogate je Serie mit derselben STRESS_ABS-Maske; (b) Maske je Surrogat aus der gemeinsamen Groesse der Surrogate neu gezogen (mechanischer Selektionseffekt). Berichtet werden Null-Verteilung der Differenz rho_Stress - rho_Ruhe (Mittel, p5, p95) und der Rang der realen Differenz - deskriptiv, keine Schwelle. (2) WP-10(A2) wird danach einmal wiederholt; erst diese Fassung liefert die Stress-Matrix als Konstante fuer PRD 9.2. (3) Bis dahin: `N_eff` im Stress-Fenster als Pflichtzeile fuer A1; abhaengigkeitsrobuste Ueber-Familien-Korrektur bleibt. (4) Kein Kandidat aus diesem Befund (DEC-58).
- **Rueckbauweg:** additiver Block im Summary/Report; Lauf 2026-09-09 bleibt mit Fingerprint erhalten.

---

### DEC-65 · WP-10(A2) mit Surrogat-Null: Funding-Kohaerenz-Anstieg im Stress nicht durch Selektion erklaert - Stress-Matrix wird Konstante; Welle-1-Teil A abgeschlossen
- **Anlass:** Wiederholungslauf 2026-09-10 (`state/runs/wp10a2_20260910/`, Nachtrag in `WELLE1_BEFUND_TEIL3_2026-09-10.md`). Beide Surrogat-Varianten um 0 zentriert; reale Lifts der Funding-Paare mit Rang 87-99,7 % (zwei Paare in beiden Varianten ueber p95, Richtung in 9 von 10 Paaren gleich); BTC-Funding x IV-RV Rang 2-5 %.
- **Entscheidung:** (1) Die Stress/Ruhe-Matrix (Funding untereinander 0,6-0,7 im Stress gegen 0,2-0,35 in Ruhe; IV-RV BTC/ETH 0,88 in beiden Regimen; Funding x IV-RV in Ruhe 0, BTC im Stress -0,4) wird als Konstante in PRD 9.2 gefuehrt, mit den Surrogat-Baendern daneben. (2) Fuer A1 gilt: `N_eff` im Stress-Fenster als eigene Pflichtzeile; Kill-/Power-Rechnung von A1 verwendet den Stress-`N_eff`, nicht den Ruhe-Wert. (3) Die abhaengigkeitsrobuste Ueber-Familien-Korrektur bleibt (F-PREM1/F-PREM2 sind im Stress verbunden). (4) Kein Kandidat aus dem Befund (DEC-58); der Funding-x-IV-RV-Deskriptor wird NICHT zu einer Hypothese ausgebaut, solange er nicht vorab mit eigenem K formuliert ist. (5) WP-10(A) gilt als abgeschlossen; offen in Welle 1 sind WP-7-Zensus und WP-10(B).
- **Methodische Notiz:** Die Variante "Selektion auf gemeinsame Groesse" ist bei symmetrischen Randverteilungen erwartungsgemaess unverschoben (Vorzeichen-Symmetrie); sie misst die Verzerrung durch schiefe Raender, nicht einen garantiert positiven Effekt. Die PRD-4.3-Formulierung "steigen mechanisch" bleibt als Warnung stehen, ist aber fuer RV-maskierte Stress-Zellen nicht der dominante Fehlermodus.
- **Rueckbauweg:** Dokumentation.
