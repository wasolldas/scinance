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
