# Wave-3-SURVEY — Scinance 2.0

**Erstellt:** 2026-06-18 · **Branch:** `scinance2-wave2` (Welle 2 inhaltlich abgeschlossen, Welle 3 noch nicht abgezweigt) · **Phase:** 1 (SURVEY, Welle 3) · **Sprache:** Deutsch
**Methode:** Delta zur Welle-2-Survey *(scinance2-impl/state/wave2_survey.md, 2026-06-15)* nach der Welle-2-Auswertung (GL-006/007/008/009). Alle Pfade absolut.

---

## 1. Status-Aktualisierung der PRD-§4-Pilot-Tabelle nach Welle 2

Ausgangspunkt: PRD §4 *(FINAL_PRD.md Z.119-133)* und die Welle-1-Tabelle *(WAVE1_FINAL_REPORT.md §6)*. Welle 2 hat vier dort als „offen" geführte Pilots verbraucht: **C-17/C-41-Mess-Gate** (H-04 WEITER kapitalfrei), **C-17/C-41-Tradability** (NEUE H-04b PARK), **C-01-Vorzeichen-Test** (H-05 DROP, kaskaden-wirksam auf C-09-OFI-Bein + C-14-OFI-Erbe), **C-07 Permutation Entropy** (H-06 DROP). Verbleibend „offen": **C-06 NICHT-triviale MR, C-20 MOMENT, C-40 Forschungsasset**. Hinzu kommt **H-05b** als OOS-pending Folge-Pre-Registration.

| §4-Pilot | Markt | Vorbedingung (PRD §4) | Welle-1/2-Auswirkung | Status für Welle 3 |
|---|---|---|---|---|
| **C-17/C-41 Mess-Gate** | F | nach Welle 1, kapitalfrei | H-04 WEITER (Mess-Existenz) *(GL-006)* | **abgeschlossen WEITER kapitalfrei** |
| **C-17/C-41 Tradability** | F | (Klausel aus H-04) | H-04b PARK, Netto -14.95 / -14.83 bps *(GL-009)* | **abgeschlossen PARK** |
| **C-01 OFI (Vorzeichen)** | F | INC-02-Vorzeichen ZUERST | H-05 DROP, kaskaden-wirksam *(GL-007)* | **abgeschlossen DROP** (+ C-09-OFI-Bein/C-14-OFI-Erbe) |
| **C-07 Permutation Entropy** | F | ρ ≥ 0.3, m/τ fixiert | H-06 DROP (PRE-Gate ρ≈0 in allen 10 Symbol×Fenster) *(GL-008)* | **abgeschlossen DROP** |
| **C-06 NICHT-triviale MR** | F | neue Hypothese (Sign-Flip via E-04 widerlegt) | unabhängig | **offen auf Hypothesen-Ebene** — Lauf erst nach Hypothesen-Formulierungsarbeit |
| **C-20 MOMENT Zero-Shot** | F | RV auf Neulistings, MASE < 1.0 | unabhängig — Datenbedarf | **offen, aber datenkritisch** (Bybit-Neulisting-Vorlauf erforderlich) |
| **C-40 RPI Hidden-Liquidity** | S/F | Forschungs-/Sicherungs-Asset (PRD §5 PARK), KEIN Edge-Claim | rpi_orderbook läuft (~5 Mio Zeilen+) | **offen als Forschungsasset** (kein Alpha-Gate) |
| H-05b OFI inverse (MM-Replenishment) | F | Folge nach GL-007 | registriert 2026-06-17, OOS-pending | **offen, wartet auf OOS-Fenster-Reife** |
| C-10 / C-35 / C-11 / C-12 / C-34 / VRP-RV-Bein | F/S/O | nach C-42-Reproduktion | H-02 DROP (Welle 1) — Anker fehlt | **blockiert** (bräuchte H-02b mit bit-genauer Original-Feature-Spec) |
| C-08 BOCPD (Ockham) | F | nach E-15, Time-Stop schneidet Tail NICHT | H-01 DROP, Time-Stop hat den E-10-Tail gekappt | **blockiert / tote Spur** |
| C-37 Spread-Execution / CS-12 Funding-Uhr K2 | F | nur falls CS-03 in Graubereich | H-01 DROP klar unter -10 bps | **blockiert** |
| CS-07 Footprint-Detektor | F | nach C-16 UND C-31 je einzeln | C-31-Bein via H-03 DROP | **blockiert** (nur via C-16-Pfad, datenhungrig) |
| C-25 Toxic Flow / Kyle-λ / VPIN | F | braucht positive Basis-Strategie | nach H-04b PARK + Welle-1-DROPs gibt es **keine positive Basis** | **blockiert (zirkulär)** |
| **C-33 VRP / Short-Vola** | O | ≥ 12-Mon. IV-Recording + Stress | option_tickers NO_DATA bleibt offen; IV-Stream tot | **gated** (Defekt-Diagnose + 12-Mon. Vorlauf — Welle-N) |
| **C-27 + C-28** Cori-Rₜ / NB-k | F | Recording-Vorlauf ≥ 30 Kaskaden + ω_s-Stabilität | insurance_pool event-arm (~7/h) | **gated** (Monate) |
| **C-29** Avalanche Shape-Collapse | F | Recording-Vorlauf + ω_s-Stabilität | rpi/insurance läuft | **gated** (Wochen-Monate) |
| **CS-06** Kaskaden-Cockpit | F | sequenziell nach C-27/C-28/C-29 | folgt der Cascade-Kette | **gated** (≥ 3-4 Mon.) |
| **C-39** Kaskaden-Anatomie | F | nach C-36 + Stress-reichem Fenster | insurance läuft, adl_alerts phantom *(DEC-08)* | **gated** (Bybit-Topic-Klärung + Stress) |

Zählung Welle 3: **3 offen (C-06, C-20, C-40) + 1 OOS-pending (H-05b) · 7 blockiert · 5 gated · 4 abgeschlossen.**

---

## 2. Welle-3-Pilot-Kandidaten (priorisierte Bewertung)

### 2.1 H-07-Kandidat: H-05b-OOS-Confirmation (C-01 inverse, MM-Replenishment)

- PRD-§4-Zitat: keine — H-05b ist Folge-Pre-Registration nach GL-007, im H-05-Eintrag explizit antizipiert *(hypothesis_registry.md §H-05 Z.69, §H-05b Z.96-117)*.
- Status: **Hypothese bereits registriert** (2026-06-17, vor Lauf-Start, Data-Snooping-Guard wirksam). Es braucht KEINE neue Pre-Registration und KEINEN neuen Code — `src/bybit_edge/research/c01_ofi_sign/` ist gate-neutral ausreichend *(hypothesis_registry.md §H-05b Code-Bedarf-Vermerk, Z.116)*.
- Was Welle 3 hier tun muss: **OOS-Reife abwarten**, dann Lauf, dann gate-auditor.
- FDR-Familie: F-OFI-INV (eigene Familie, getrennt von F-OFI; allein-laufend nur Familien-intern BH-FDR α=0.10) *(hypothesis_registry.md §H-05b Z.111)*.
- KAPITALFREI; voller Edge-Test wäre H-05c (L2/Wochen, NICHT hier).
- Falsifikations-Billigkeit: T2 (1-2 h) bei verfügbaren OOS-Daten — der Code steht.
- Reifezeit-Schätzung (heutiges Datum 2026-06-18): Entdeckungslauf endete Tick-Cutoff 1 780 619 066 816 ms ≈ 2026-06-16 *(gate_log.md §GL-006 Fenster-Cutoff)*. Bei ETHUSDT-Perp ~100-200k Trades/Tag und Pflicht ≥ 2 disjunkte Fenster à 150 000 Ticks post-Cutoff (Entdeckungszelle ETHUSDT w0 δ1s ausgeschlossen, §H-05b Z.100-102) — **sauber OOS ab ca. 23.-28.06.2026; konservativ ca. 30.06.-02.07.2026**.

### 2.2 H-08-Kandidat: C-20 MOMENT Zero-Shot Neulistings

- PRD-§4-Zitat: „**C-20 MOMENT (nur Zero-Shot-Neulisting) … RV-Zero-Shot auf neu gelistete Symbole ohne Lookback; MASE < 1.0 … sonst DROP (kein verlorener HAR-Vergleich)**" *(FINAL_PRD.md Z.132)*.
- Hypothesen-Skizze (nicht registriert): H-08 = MOMENT-Foundation-Modell prognostiziert auf NEU gelisteten Bybit-Perp-Symbolen RV mit **MASE < 1.0 in ≥ 2 disjunkten OOS-Fenstern** ohne Symbol-spezifisches Re-Training. **Kein HAR-Vergleich** (Verdict-Bedingung: „sonst DROP"). FDR-Familie F-MOMENT-ZS (klein, 1-2 Konditionierungen).
- Tradability-Gate: nicht zutreffend für MOMENT-Detektion-Gate; ein H-08b für ein Edge-Folge-Gate wäre eine eigene, später zu registrierende Hypothese.
- KAPITALFREI im Detektions-Gate (nur Forecast-Genauigkeit, kein PnL).
- Falsifikations-Kosten: T3 mittel, dominiert von **Heavy-Foundation-Modell-Dependency** (`momentfm`, DEC-Kandidat analog DEC-04 `vol`-Extra) *(wave2_survey.md §2.1 C-20-Zeile)*.
- Datenbedarf: Bybit listet ~wenige Perp-Symbole pro Monat. Welle 1+2 Recording-Start ~2026-06-11; bei aktuellem Datum 2026-06-18 = **~1 Woche Listings-Akkumulation**. Demonstrator-Lauf auf historischen Listings (letzte 3-6 Monate Kline-Backfill, öffentliche REST-API) möglich sofort; konfirmatorisches N=10-20 Listings braucht **Wochen bis Monate** Vorlauf für frische Live-Listings.
- Reihenfolge-Risiko: Repo-Aufwand (Foundation-Modell-Adapter, REST-Listings-Backfill) ist NICHT trivial — mehrere hundert LoC plus optionale Heavy-Dep. Lohnt nur, wenn Welle 3 ein klar nicht-OFI-/nicht-PE-Asset ergänzen will.

### 2.3 H-09-Kandidat: C-06 NICHT-triviale Mean-Reversion

- PRD-§4-Zitat: „**C-06 (NICHT-triviale MR) … nach Welle 1 … FDR-korrigiertes Gate für separates Folge-Signal (simple Sign-Flip-MR durch E-04 bereits widerlegt) … trivial-MR-Lesart verboten; ohne neue Hypothese kein PILOT**" *(FINAL_PRD.md Z.129)*. PRD §6 verbietet die simple Sign-Flip-Lesart explizit *(FINAL_PRD.md Z.203-205)*.
- **Das Problem ist ehrlich gesagt der Hypothesen-Engpass selbst.** PRD §6 verbietet die Sign-Flip-MR; was bleibt:
  - **Variante A (Regime-Konditionierung):** MR-Profil über T+1..T+k NUR in spezifisch konditionierten Marktregimes (z.B. nach Vol-Spike Q4 oder nach Cluster-detektiertem Aggressor-Exhaustion). Schwelle X = mittlere MR-Magnitude / FDR-sig über ≥ 2 disjunkte Fenster, kapitalfrei. **Risiko: Konditionierungs-Suche = Garden of Forking Paths.** Eine ehrliche Variante A muss die Konditionierungs-Achse VOR dem Lauf binden (max 2-3 vorab fixierte Regimes), sonst ist das Gate fingiert.
  - **Variante B (Mikrostruktur-MR, NICHT direktional):** MR als nicht-handelbare-Mess-Existenz auf Mikro-Skala (analog H-04 vs. H-04b-Trennung). Kapitalfrei, Survivor-Pfad zu späterer H-09b-Tradability nicht impliziert.
- Falsifikations-Kosten: T2-T3 mittel; Code-Pfad könnte teilweise auf c07_pe-Infrastruktur (Vol-Cluster-Definition) aufsetzen, neue Konditionierungs-Logik aber proprietär.
- Empfehlung: **C-06 ist KEIN nächster billiger Pilot.** Eine ehrlich formulierbare H-09 erfordert echte Hypothesen-Arbeit (WP-0-Welle-3 Vorlauf, mehrere Tage Forschungs-Notizen), nicht nur Code-Bau. Variante A ist anfällig für die Hypothesen-Engpass-Falle (§6); Variante B wäre nur ein weiteres kapitalfreies Mess-Gate ohne klaren Pfad zu handelbarem Edge.

### 2.4 H-10-Kandidat: C-40 RPI als Mess-Reproduktion (NICHT Edge-Gate)

- PRD-§4 / §5-Zitat: „**C-40 RPI Hidden-Liquidity … Recording an C-36 koppeln als Forschungs-/Sicherungs-Asset, KEIN Handels-Edge-Claim**" *(FINAL_PRD.md Z.154)*. PRD §5 PARK-Begründung: „selbstzerstörender Edge (HFT liest RPI-Buch live)".
- **Eine ehrlich registrierbare Mess-Hypothese H-10:** Der RPI-OrderBook-Recorder *(src/bybit_edge/recorder/, ~5 Mio Zeilen)* reproduziert auf einem schmalen Mess-Punkt ein **externes, dokumentiertes Bybit-RPI-Verhaltensmerkmal** (z.B. dokumentierte Tick-Distanz / Mindest-Quote-Größe / Aktualisierungs-Frequenz pro Symbol-Klasse) innerhalb einer vorab fixierten Toleranz. Das ist ein **Tooling-Validierungs-Gate**, KEIN Alpha-Gate — analog C-36-F0-Recall (kein Eintrag in der Hypothesen-Registry, Infrastruktur-Pilot).
- KAPITALFREI per Konstruktion (kein Edge-Claim).
- Falsifikations-Kosten: T2-T3 niedrig.
- Empfehlung: **Sinnvoll als Welle-3-Infrastruktur-Pilot, NICHT als Alpha-Gate.** Erspart spätere Welle-N-Pilots (C-39-Stress-Anatomie) Unsicherheit über die Provenance der RPI-Daten. Sollte als Forschungs-WP geführt werden (kein Registry-Eintrag), parallel zum Recording-Vorlauf.

### 2.5 Übersehene Pilots? (PRD §4 + verdict.md §1 systematisch)

Geprüft: PRD §4 Pilot-Tabelle (Z.121-133), §5 PARK-Register (Z.145-178). **Es gibt keine weiteren PRD-§4-Pilots, die jetzt durch Welle-2-Verläufe entsperrt sind.** Die Vol-Stack-Sperre (C-10/C-11/C-12/C-34/C-35/VRP-RV-Bein) bleibt durch H-02 DROP wirksam; eine H-02b mit bit-genauer Kestrel-Feature-Spec ist NICHT in Welle 3 priorisiert (Feature-Provenance-Beschaffung ist Außen-Arbeit, keine schnelle Falsifikation). C-25 bleibt zirkulär gated (braucht positive Basis-Strategie — existiert weiterhin nicht). PRD §5 PARK-Liste enthält keine Einträge mit Welle-2-induzierter Entsperr-Bedingung.

---

## 3. Recording-Vorlauf-Reifegrad

Aktuelle Datenlage (kein neueres `recording_check.json` als das Welle-1-Cumulative `upload_20260615/.../recording_check.json` in den handoff_local-Ergebnissen *(wave2_state.md §Welle-1-Stand)*; Welle-2-Läufe nutzten nur read-only `trades` und `kline_1min`, keinen neuen Recording-Stand persistiert). Recording läuft kontinuierlich seit ~2026-06-11 = **~1 Woche** bis 2026-06-18. Konservative Linear-Extrapolation aus 8h-Telemetrie `RECORDER_LONG.err.log` (~33k Frames/h rpi, ~5 MB/h) *(wave2_survey.md §2.3)*.

| Stream | Stand 2026-06-15 (Quelle) | Hochrechnung 2026-06-18 (~3 Tage später) | Benötigt für | Restwartezeit |
|---|---|---|---|---|
| `rpi_orderbook` | 4 987 255 rows / 3 378 files / Schema v1 | ~7.4 Mio rows (~+2.4 Mio bei ~330k/h × 24 × 3) | C-29 Shape-Collapse, C-40 Forschungs-Asset, C-39 (Anatomie) | C-29 ≥ 6-8 Wochen ab 2026-06-11 → ca. **Anfang Aug. 2026** |
| `insurance_pool` | 58 rows / 27 files | ~150 rows (~7/h × 24 × 3) | C-27 + C-28 Kaskaden (≥ 30) | Bei ~7 Events/h und ungewissem Kaskaden-/Event-Mapping → **Monate** (≥ 8-12 Wochen, abhängig von Stress-Anteil GM-6) → ca. **Sept.-Okt. 2026** |
| `premium_index_kline` | 95 600 rows / 478 files | ~110 000 rows | (Hilfsstream für C-33-VRP) | — |
| `option_tickers` | NO_DATA / WS-Drop alle ~30 s *(GL-004)* | NO_DATA (unverändert, Defekt offen) | C-33 VRP / C-11-M-S17 IV-Surface | **Diagnose-WP zuerst** + ≥ 12-Mon. Vorlauf + ≥ 1 Stress-Periode → **frühestens Juni 2027** *(wave2_survey.md §2.3)* |
| `adl_alerts` | EMPTY_OK, phantom *(DEC-08)* | EMPTY_OK | C-39 ADL-Bein | Bybit-Topic-Klärung erforderlich (kein Live-Topic) — **unbestimmt** |
| Storage-Belegung | 0.076 GB / 50 GB (0.15 %) | ~0.16 GB / 50 GB (0.3 %) | 50-GB-Deckel *(DEC-07)* erreicht nach ~7 Monaten Dauerbetrieb | Sunset-Review nach 3 Monaten *(PRD §9)* greift VOR Cap → kein Daten-Lake-Risiko |

**Kernbefund für Welle 3:** Die gated-Pilots **bleiben in Welle 3 noch immer gated**. Keine recording-abhängige Hypothese ist für Welle 3 reif. C-33 ist Welle-N (≥ Juni 2027). C-27/C-28/C-29/C-39/CS-06 erfordern weiter Vorlauf. Die einzige Recording-anhängige Welle-3-Aktion ist **das Recording weiterlaufen lassen** plus die zwei offenen Reparatur-WPs (option_tickers-Keepalive, adl_alerts-Topic-Klärung).

---

## 4. Pflicht-Vorarbeiten vor jedem Welle-3-Lauf (WP-0 Welle 3)

Pro Welle-3-Hypothese MUSS in `hypothesis_registry.md` als H-07/H-08/... VOR dem ersten Lauf eingetragen sein *(CLAUDE.md ZUSTANDSMASCHINE Phase 2; Registry-Disziplin §1)*:

1. **Wörtliches Gate** (WEITER / DROP / GRAUBEREICH oder explizit „kein GRAUBEREICH" — Welle 1/2-Konvention: kein GRAUBEREICH außer H-01).
2. **FDR-Familie** als NEUE Familien-ID, getrennt von F-S3/F-VOL/F-CFAR/F-LEADLAG/F-OFI/F-ENTROPY/F-OFI-INV/F-LEADLAG-TRADE *(hypothesis_registry.md §Registry-Disziplin §4 + Welle-2-Nachtrag)*.
3. **Hartes Ein-Fenster-Kriterium** (PRD §8.5) — Welle-1/2-Standard.
4. **Anti-Gaming-Klausel** wo eine Tradability-Komponente existiert — analog H-04b *(hypothesis_registry.md §H-04b Z.132)* und DEC-13 *(decisions.md §DEC-13)*.
5. **Data-Snooping-Guard** wo die Hypothese aus einer Welle-1/2-Beobachtung abgeleitet ist — analog H-05b *(hypothesis_registry.md §H-05b Entstehungs-Offenlegung Z.99-102)*: Entdeckungszelle nicht-konfirmatorisch + OOS-Anforderung + Konsistenz über ≥ 2 disjunkte Fenster aus ANDEREN Zellen.

**Über-Familien-Empfehlung Welle 3:**
- **F-WAVE2 ist abgeschlossen und wird NICHT erweitert** *(hypothesis_registry.md §H-05b Z.111, §H-04b Z.134)*. Append-only.
- **F-WAVE3 als neue Über-Familie nur konstruieren, falls in einer Welle-3-Kohorte ≥ 2 neue Hypothesen GLEICHZEITIG laufen.** Bei rollierender Folge-Pre-Registration (H-05b-Confirmation läuft allein vor einer eventuellen H-07-Kohorte) ist die F-WAVE2-Pattern *(Stage 1 Familien-intern → Stage 2 Über-Familie BH-FDR α=0.10)* zu übernehmen. Bei Einzel-Läufen genügt Familien-interne BH-FDR — exakt das H-05b/H-04b-Pattern.
- Empfehlung: **F-WAVE3 erst VOR dem konkreten Multi-Hypothesen-Lauf registrieren, nicht prophylaktisch.** Reduziert α-Budget-Verbrauch durch Familien, die nie zustande kommen.

---

## 5. Welle-3-Sequenzierungsvorschlag (empfohlene Reihenfolge, nicht Optionen-Liste)

Begründung: Die Welle-3-Pipeline ist hypothesen-arm. Die billigste falsifizierbare Aktion ist **H-05b-Confirmation, weil der Code steht und die Hypothese registriert ist**. Alles andere erfordert WP-0-Hypothesen-Arbeit (C-06) oder schweren Repo-Aufwand (C-20 Foundation-Modell). Sequentielle Strategie statt parallel-3-Pilot-Ansatz wie Welle 2.

### Empfohlene Reihenfolge:

1. **Stufe A — WP-0 Welle 3 (ab sofort, parallel zur OOS-Reife):** Forschungs-Notizen zu C-06 NICHT-triviale-MR vorbereiten. Ziel: ehrlich registrierbare H-09 mit max. 2-3 vorab fixierten Konditionierungs-Achsen (kein Forking-Paths-Risiko). Falls nicht formulierbar → C-06 fällt auf „blockiert auf H-Ebene" und scheidet als Welle-3-Pilot aus.

2. **Stufe B — H-05b-OOS-Confirmation-Lauf (Earliest ca. 23.06.2026 sauber, konservativ ab ca. 30.06.2026):**
   - Vorab Recording-Check (`recording_check.json`-Snapshot) zur Bestätigung der OOS-Tick-Verfügbarkeit ≥ 2 × 150 000 Ticks pro Symbol post-Cutoff.
   - Lauf via existierender Driver-Pfad `scripts/c01_ofi_sign.py` mit anders parametriertem Gate beim gate-auditor (Familie F-OFI-INV, Entdeckungszellen-Ausschluss im Audit, da Code-seitig optional) *(hypothesis_registry.md §H-05b Code-Bedarf-Vermerk)*.
   - gate-auditor urteilt → GL-010. Ausgang: WEITER würde inverse Lesart bestätigen (C-01 als handelbar bleibt aber offen — H-05c L2/Wochen); DROP würde zusammen mit GL-007 die Symmetrie-Falle auslösen *(hypothesis_registry.md §H-05b Z.107)*: beide Vorzeichen-Lesarten verworfen, OFI-Vorzeichen-Test inhaltlich erschöpft.

3. **Stufe C — Welle-3-Entscheidungspunkt nach GL-010:**
   - Falls C-06-WP-0 eine ehrlich registrierbare H-09 ergibt → H-09 registrieren, Build + T3, gate-auditor.
   - Falls NICHT → C-20 MOMENT-Demonstrator (T1-Sandbox-Stufe auf historischen Listings) als nicht-blockierender Welle-3-Lottoschein erwägen. Heavy-Dependency-Entscheidung (DEC-Kandidat analog DEC-04 `vol`-Extra) sauber dokumentieren.
   - C-40 als reines Tooling-WP parallel weiterführen (kein Registry-Eintrag).

4. **Parallel laufend (Welle 3 berührt sie nicht):**
   - Recording-Engine läuft weiter, Sunset-Review-Uhr tickt (erster Sunset ca. **2026-09-11**, 3 Monate nach Recording-Start *(PRD §9 Z.272)*).
   - Reparatur-WPs für `option_tickers` (Keepalive/Topic-Spelling) und `adl_alerts` (Bybit-Topic-Doc) als unabhängige Vorlauf-Reparaturen.

---

## 6. Risiken / Pitfalls für Welle 3

- **Hypothesen-Engpass:** Nach Welle 1+2 sind die niedrig-hängenden Falsifikationen abgegrast (3 Welle-1-DROPs, 2 Welle-2-DROPs, 1 Welle-2-PARK, 1 Welle-2-Mess-WEITER ohne Tradability). Welle 3 wird **Hypothesen-Erarbeitungs-Arbeit**, NICHT Pilot-Auswahl wie Welle 2. Der C-06-Pfad ist der Test, ob das Programm überhaupt eine weitere ehrlich falsifizierbare Alpha-Hypothese produzieren kann.

- **Garden of Forking Paths verschärft:** Je weniger frische Hypothesen-Quellen, desto höher das Risiko, dass eine in den Welle-2-Daten beobachtete Asymmetrie (oder eine Welle-1-Restbeobachtung) zur Hypothese erhoben wird, ohne sauber data-snooping-gehärtet zu sein. **H-05b setzt das Pattern; jede künftige Welle-3-Hypothese, die aus Welle-1/2-Daten geboren wird, MUSS einen H-05b-artigen Data-Snooping-Guard tragen** (Entdeckungszelle nicht-konfirmatorisch + OOS-Pflicht + Konsistenz aus anderen Zellen).

- **Symmetrie-Falle bei H-05b:** Falls H-05b auch DROP → der OFI-Vorzeichen-Test ist erschöpft, KEIN H-05c wird nachgeschoben *(hypothesis_registry.md §H-05b Z.107)*. Dann bleibt C-01 als Pilot vollständig erledigt. Welle 3 sollte sich darauf einstellen, dass das das wahrscheinlichste Ergebnis ist (ein in einer Zelle FDR-sig gefundener inverser Effekt überlebt OOS-Tests in der Mehrzahl der Fälle nicht — das ist das Forking-Paths-Argument selbst).

- **Recording als einzige zeit-positive Ressource:** C-36 wird mit der Zeit besser, alles andere nicht. Sunset-Review (3 Monate, PRD §9) bleibt die Anti-Data-Lake-Bremse — ungenutzte Streams (z.B. wenn `option_tickers` weiterhin tot bleibt) werden abgeschaltet. Erster Sunset fällt **ca. 2026-09-11**.

- **PRD §8.1 Welle-Budget:** Max 3-5 Pilots parallel, max 1 neuer Alpha-Test pro Welle. Welle 3 sollte konservativ planen: **1 OOS-Confirmation (H-05b) + max. 1 neuer Alpha-Test (H-09 ODER H-08)** — nicht beide.

- **Welle-3-Branch:** Branch `scinance2-wave3` ist noch NICHT abgezweigt. Sollte VOR dem ersten Welle-3-Build vom Welle-2-Endstand abgezweigt werden (analog W2-INIT-Pattern *(wave2_state.md §W2-INIT)*).

---

*Quellen durchgängig: `scinance2-impl/state/{WAVE1_FINAL_REPORT.md, wave2_survey.md, wave2_state.md, gate_log.md (GL-001..009), decisions.md (DEC-01..13), hypothesis_registry.md (H-01..H-06 + H-05b + H-04b + alle Nachträge + Registry-Disziplin §1-8 + Welle-2-Nachtrag)}`, `FINAL_PRD.md §3/§4/§5/§6/§8/§9`, `edge-reconciliation/results/verdict.md §1/§4/§8`, `scinance2-impl/handoff_local/results/{wave2_20260617_090618/WAVE2_SUMMARY.md, h04b_20260618_091937/SUMMARY_2026-06-18.md, upload_20260615/.../recording_check.json, upload_20260614/.../RECORDER_LONG.err.log}`.*
