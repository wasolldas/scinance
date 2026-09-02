# PRD Review Report — FINAL_PRD.md (Scinance 2.0)

**Phase:** 7 — REVIEW (judge, Review-Modus)
**Stand:** 2026-06-11
**Geprüft:** `results/FINAL_PRD.md`
**Referenzen:** `verdict.md`, `alignment_matrix.md`, `claims_register.md`, `evidence_register.md`
**Maßstab:** QUALITÄTS-CHECKLISTE FINAL_PRD (CLAUDE.md §119–129), 6 Punkte + Stichproben.

---

## 1. Checklisten-Prüfung (6 Punkte)

### Punkt 1 — Jeder übernommene Ansatz auf Entscheidungsmatrix rückführbar (keine Ansätze aus dem Nichts, keine stillen Streichungen): **PASS**

- Jeder PRD-Posten trägt C-/CS-/E-/GM-/INC-IDs und verweist auf verdict-§ (z.B. §3 Pilot 1 „wörtlich aus verdict §3 übernommen", §4-Tabelle „verdict §4 Welle 2", §5 „verdict §1, §8").
- Gegenprobe Vollständigkeit: Anhang (PRD §Anhang) listet REFUTED 3, Welle-1-Pilots 4, Welle-2+-Pilots, ADOPT 0 — deckungsgleich mit verdict §8 Verteilung (ADOPT 0 / PILOT ~16 F-Zellen / PARK ~25 / DROP ~70 / REFUTED 3).
- Alle Futures-PILOTs aus verdict §1/§8 sind im PRD wieder auffindbar: C-42, C-06, C-22, C-27, C-28, C-29, C-37, C-32, C-20, C-36, C-31, C-16, C-07, C-01, C-10, C-35, C-33, CS-03, CS-06 → in PRD §3/§4/§5 vollständig vorhanden.
- Keine stille Streichung gefunden. Auch die DROP-Module ohne Mechanismus (C-24, C-18-F, C-19-F) sind im PRD adressiert: C-18 in PARK-Register (Z. 177) als „REFUTED-nahe Doku", C-19 in PARK (Z. 162), C-24 ist als reiner DROP (verdict §1c, „zu wenig Substanz für eigenes Budget") nicht eigens gelistet — das ist zulässig, weil DROP-ohne-Mechanismus kein eigener PRD-Eintrag sein muss; C-24 ist im Anhang über „C-01..C-43 vollständig in claims_register" abgedeckt. MINOR-Hinweis siehe §3.

### Punkt 2 — REFUTED-Ansätze in eigenem Abschnitt dokumentiert: **PASS**

- PRD §6 „REFUTED-Register" enthält exakt die 3 forensisch belasteten Claims C-14, CS-01, CS-02 — identisch zu verdict §2 und alignment_matrix (REFUTED 3).
- Volle forensische Kette je Eintrag übernommen (E-01/E-02 für C-14; E-03/E-04/E-16 für CS-02; Modul-≠-Strategie-Differenzierung für CS-01). „Verbotene Wiederholung"-Klauseln ergänzt (Wissensspeicher-Funktion erfüllt, CLAUDE.md Grundhaltung „Negative Ergebnisse sind Ergebnisse").
- Keine REFUTED-Inflation: C-15/C-26/C-06/C-01/C-07 bleiben korrekt SUSPECT, nicht REFUTED (PRD §2.1 letzter Absatz + §6 CS-01/CS-02-Text).

### Punkt 3 — Je Ansatz: Markt-Zuordnung, Validierungs-Gate mit Schwellwert, Abbruchkriterium, benötigte Datenströme: **PASS**

- Welle-1-Pilots (§3) haben alle vier Felder explizit: je „Markt-Zuordnung", „Benötigte Datenströme", „Validierungs-Gate" (mit Zahl), „Abbruchkriterium". Beispiel Pilot 4 (C-31): Markt Futures; Datenstrom publicTrade WS #8; Gate p≤0.05 + Lead>50ms + Edge>11bps; Abbruch bei Verfehlen eines Kriteriums in einem Fenster.
- Welle-2+-Tabelle (§4) führt je Zeile Markt / Vorbedingung / Gate (mit Schwelle) / Abbruchkriterium.
- PARK-Register (§5) führt Markt + Park-Grund + Entsperr-Bedingung (statt aktivem Gate — korrekt, da PARK = blockiert, kein laufendes Gate; entspricht judge.md PARK-Definition „mit Entsperr-Bedingung").
- Datenströme: für recording-abhängige Pilots in §3 Pilot 3 zentral benannt (orderbook.rpi, insurance.USDT, adlAlert, Premium-Index-Kline, Options-Tickers, repo_map §5).

### Punkt 4 — PILOT-Ansätze mit konkretem Testdesign (was, womit, Erfolgsmaß): **PASS**

- Pilot 2 (C-42): „purged Walk-Forward (≥L2), ≥2 disjunkte OOS-Fenster, FDR (BH α=0.10) über 36 Features" → was/womit/Erfolgsmaß (OOS-R²≥0.15 + QLIKE schlägt HAR) vollständig.
- Pilot 4 (C-31): Surrogate-Test (geshuffelte Inter-Arrivals) gegen Cyclic Spectrum, Lead-/Edge-Messung in ≥2 Fenstern → vollständig.
- Pilot 1 (E-15): Tore wörtlich aus verdict §3 mit Vorab-Festlegung ADOPT-Kandidatur vs. DROP (PENDING-Regel judge.md #3 korrekt umgesetzt — keine verschiebbaren Torpfosten).
- Welle-2-Tests (C-27/C-28 als EIN Test, C-29 separat, C-08-Ockham gegen trivialen Time-Stop) tragen je ein operationalisiertes Erfolgsmaß.

### Punkt 5 — Bezug zum Repo (was bleibt / ändert / kommt neu, Architektur-Skizzen-Niveau, kein Code): **PASS**

- PRD §7 dreigeteilt: BLEIBT (Replay-Harness, Test-Suite, Friction-Modell, Diagnostik/Funnel, Daten-/State-Layer), ÄNDERT (S1/S2 retired, S3 bedingt, S4/S5 eingefroren), NEU (Recording-Engine F0, C-42-Repro-Pipeline, CFAR-Modul, Multiple-Testing-Registry).
- Architektur-Skizzen-Niveau eingehalten: Dateinamen/Modulnamen genannt (`replay_backtester.py`, `m2_ofi.py` etc.), aber kein Code.
- Repo-Bezug korrekt aus repo_map abgeleitet; PRD korrigiert sogar einen repo_map-Fehler (C-01/C-02-Vertauschung in repo_map §2.1, PRD §7 Z. 211) und verweist auf claims_register als kanonisch — saubere Disziplin.

### Punkt 6 — Multiple-Testing-Risiko über alle Ansätze adressiert: **PASS**

- PRD §8 dedizierter Abschnitt, deckungsgleich mit verdict §5: GM-2-Problem (~25 Hypothesen-Gates), Welle-1-Deckel 4 Gates / effektives Alpha-Budget 1 (nur C-31), FDR-Familien (Funding / Vol-Feature / Cascade / Cross-Sectional), Pre-Registration, Peso/L0-Schwellenverschärfung, hartes Ein-Fenster-Abbruch.
- Querschnitt korrekt: C-27+C-28 als EIN Test geführt (geteilter ω_s-Kernel, statistisch nicht unabhängig) — sowohl in §4-Tabelle als auch §8.2.

---

## 2. Stichproben-Querprüfung

### 2a. PILOT/PARK-Einträge verdict → PRD (≥5 Stichproben)

| # | verdict-Eintrag | verdict-Urteil | PRD-Befund | Konsistent? |
|---|---|---|---|---|
| 1 | C-37 Spread-Execution (F) | PILOT, Gate: Maker-Quote ≥70 % UND Round-Trip ≤6 bps in Release-Fenstern; verfehlt→DROP (verdict §1c/§3) | §4-Tabelle: „Maker-Quote ≥70 % UND realisierter Round-Trip ≤6 bps SPEZIELL in Pressure-Release-Fenstern", verfehlt→DROP | ✓ exakt |
| 2 | C-33 VRP (O) | PILOT verschärft; ≥12-Mon.-Recording + ≥1 Stress; (IV−RV)≥3 %; <3 %→DROP (verdict §1g/§4/§5.3) | §4-Tabelle: „(IV − RV) ≥ 3 % im 12-Mon.-OOS in ≥2 Fenstern … <3 % in einem Fenster ODER Liquidität unzureichend → DROP" | ✓ exakt |
| 3 | C-30 Natural-Time κ₁ (F) | PARK; Wiedergänger-Risiko C-14; erst nach C-27-Validierung (verdict §1b) | §5 PARK: „erst nach C-27-Validierung; Distributions-Check analog E-01 zuerst" | ✓ exakt |
| 4 | CS-12 Funding-Uhr K2 (F) | PARK bis E-15+C-37 positiv (verdict §1h) | §5 PARK: „Produkt aus 4 offenen Faktoren … erst wenn E-15 + C-37 positiv" | ✓ exakt |
| 5 | C-20 MOMENT (F) | PILOT nur Zero-Shot-Neulisting, MASE<1.0, sonst DROP (verdict §1d) | §4-Tabelle: „RV-Zero-Shot auf neu gelistete Symbole ohne Lookback; MASE < 1.0 … sonst DROP" | ✓ exakt |
| 6 | C-13 Cross-Sectional-Z (F) | PARK; Fee-Verdopplung 22–30 bps; Panel-Harness=S4/S5-Falle (verdict §1e) | §5 PARK: „Fee-Verdopplung 22–30 bps/Paar gegen 4–7 bps Roh-Edge; Panel-Harness = S4/S5-Falle" | ✓ exakt |
| 7 | C-08 BOCPD (F) | PARK→PILOT nur falls Time-Stop E-10-Tail nicht schneidet; Ockham (verdict §1f/§6) | §4-Tabelle als Welle-2-PILOT (Ockham-Test gegen trivialen Time-Stop), §5 nicht doppelt | ✓ (Übergang PARK→bedingter Test korrekt abgebildet) |

Ergebnis: 7/7 Stichproben verdict↔PRD konsistent in Status, Markt, Gate-Schwelle und Abbruchkriterium. Keine stille Status- oder Schwellenänderung.

### 2b. Zahlen-Gates PRD → rückwärts gegen evidence_register/verdict (≥3)

| Gate (PRD) | PRD-Stelle | Rückwärts-Quelle | Übereinstimmung? |
|---|---|---|---|
| Friction-Wand 11 bps Taker / ~15 bps inkl. Slippage; Roh-Edge max 4–7 bps | §1, §2.3 | evidence_register KOSTENBASELINE (Taker RT 11.0 bps, CSV 10.997; gesamt ~15 bps; Kernrelation „max |Roh| ≈ 4–7 bps") | ✓ unverändert |
| E-15-Tore: time_stop 1→60–70, n>120s 68→~0, n<-30bps 33→~0; netto ≥-5 → fortführen, ≤-10 → DROP; -16.81 Baseline | §3 Pilot 1 | verdict §3 (wörtlich) + evidence E-07 (68 Trades >120s, Time-Stop 1×), E-08 (33 Trades <-30 bps), E-09 (mean -16.81 netto) | ✓ exakt rückführbar |
| C-42 Gate OOS-R² ≥ 0.15 (Baseline Test-R² 0.249) | §3 Pilot 2 / §4 | verdict §4 (Gate „OOS-R² ≥ 0.15") + alignment C-42 (Test-R²=0.249, L1-Selbstauskunft) | ✓ Schwelle identisch |
| CS-03-Folge-Gate Sharpe ≥1.2 / WR ≥55 % / PF ≥1.3 über ≥200 Trades walk-forward | §3 Pilot 1 | verdict §3 (PRD-kestrel-Schwelle, identisch) | ✓ exakt |
| C-37 ≤6 bps real / Maker-Quote ≥70 % | §4 | verdict §3 + Kostenbaseline (C-37 ~4 bps PRD-Referenz, unmeasured) | ✓ konsistent (Gate ≤6 bps strenger als 4-bps-Claim — bewusst) |

Ergebnis: 5/5 Zahlen-Gates rückwärts sauber auf verdict/evidence_register herleitbar. Keine still erhöhten oder gesenkten Schwellen.

**Eine Zahlen-Abweichung geprüft (E-03):** PRD §6 CS-02 nennt BTC -3.61/ETH -3.71/SOL -3.99/BNB -1.65/XRP -4.06, Aggregat -3.45. Identisch zu evidence E-03 und verdict §2. ✓

---

## 3. Mängelliste

### BLOCKER: **0**

Keine inhaltlichen Rückführbarkeits-, REFUTED-, Gate- oder Multiple-Testing-Verstöße gefunden, die DONE blockieren.

### MINOR: **3**

- **MINOR-1 (Zähl-Diskrepanz im Quelltext, vom PRD korrekt aufgelöst):** verdict §5.1 schreibt „Davon sind 2 reine Infrastruktur/Reproduktion (E-15-Auswertung, C-42-Repro, C-36-Recording)" — die Zahl „2" widerspricht der danach aufgezählten Dreierliste (Tippfehler in verdict, sollte „3" sein). Das PRD §1/§8.1 gibt korrekt „3 Infrastruktur/Reproduktion + 1 Alpha (C-31)" wieder. Kein PRD-Fehler; nur Hinweis, dass der zugrundeliegende verdict-Satz einen Zahlendreher enthält. Kann dokumentiert bleiben.
- **MINOR-2 (reine DROP-Module ohne eigenen Eintrag):** C-24 (Kalman-Premium, DROP F) und C-19 (TimesNet) erscheinen nicht als eigenständige Zeile in §4/§5, sondern nur kollektiv über den Anhang („C-01..C-43 vollständig in claims_register"). Für C-24 ist das vertretbar (verdict: DROP, „zu wenig Substanz für eigenes Budget"), C-19 ist immerhin in PARK §5 (Z.162) gelistet. Empfehlung (optional): einen Ein-Zeiler „DROP ohne Mechanismus/Substanz: C-24, C-18-F, C-19-F" in §6 oder Anhang, damit auch reine DROPs explizit sichtbar sind statt nur implizit. Nicht DONE-blockierend, da Checklisten-Punkt 1 „keine stillen Streichungen" durch den Anhang-Verweis + verdict-Rückführbarkeit erfüllt ist.
- **MINOR-3 (Label-Kollision, kein Fehler):** In claims_register Z.756 steht C-16 in der kestrel-Spalte als „S5 (TFSAX+SW)". Das „S5" ist hier das interne kestrel-PRD-Modul-Label, NICHT Strategie CS-05. Das PRD ordnet C-16 korrekt CS-04 zu (§2.4, §4). Keine Korrektur nötig; nur zur Klarstellung dokumentiert, dass keine echte Inkonsistenz vorliegt.

---

## 4. Gesamturteil: **APPROVED**

Das FINAL_PRD erfüllt alle 6 Checklisten-Punkte (6× PASS), die Stichproben sind durchgängig konsistent (7/7 verdict↔PRD, 5/5 Zahlen-Gates rückwärts sauber), und es gibt 0 BLOCKER. Die 3 MINOR-Punkte sind dokumentierbar und blockieren DONE nicht; ein Korrektur-Loop an den prd-architect ist nicht erforderlich.

**Optionale (nicht erzwungene) Verbesserung für eine spätere Revision:** MINOR-2 (expliziter DROP-ohne-Eintrag-Einzeiler). Wenn der Orchestrator den erlaubten 1 Korrektur-Loop dennoch nutzen will, ist dies die einzige sinnvolle Ergänzung — andernfalls direkt auf DONE.

*Ende review_report.md*
