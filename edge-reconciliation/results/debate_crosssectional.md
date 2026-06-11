# Debatte: Cross-Sectional / Lead-Lag

**Cluster:** crosssectional (Cross-Sectional / Lead-Lag)
**Claims:** C-09 (HMM 3-State), C-13 (Cross-Sectional Ergodicity-Reversion Z), C-17 (Renyi-Transfer-Entropy Lead-Lag), C-41 (Cross-Asset Wavelet Coherence), CS-05 (S5 „Cross-Sectional Ergodicity Reversion"), CS-13 (K3 „Rudel-Läufer" Lead-Lag-Rotation)
**Stand:** 2026-06-11

---

## Advocate

**Zentrale Randbedingung (vorab anerkannt):** Der gesamte Cluster ist nach E-14 UNTESTED — S5 feuerte 0 Trades bei `single_symbol_replay_unsupported` = 100 % über alle 5 Symbole. Das ist keine inhaltliche Widerlegung, sondern eine **architektonische Mess-Lücke**: der Replayer kann Cross-Sectional-Logik prinzipiell nicht ausführen. Kein einziges der sechs Claims ist je gelaufen (alle SUSPECT, nicht REFUTED — Alignment-Matrix C-09/C-13/C-17/C-41). Mein Argument ist deshalb bewusst zweigleisig: (a) warum die Mechanismen vielversprechend sind, (b) warum die Panel-Harness-Investition gerechtfertigt ist, BEVOR ein Einzelnachweis existiert. Markt-Differenzierung ist Pflicht; ich führe sie je Argument bzw. gebündelt in A-7.

### A-1 — Die einzige Cluster-spezifische negative Evidenz ist eine Infrastruktur-Lücke, kein Inhaltsbefund — der Cluster ist damit der „sauberste" UNTESTED-Block im ganzen Register

E-14 belegt: S5 verlor nicht, scheiterte nicht an Friktion, lieferte kein Anti-Signal — es lief schlicht nie. Anders als CS-02 (REFUTED über drei Forensiken E-03/E-04/E-16) oder C-14 (REFUTED-Schwelle E-01) trägt dieser Cluster **null widerlegende Evidenz**. Die Alignment-Matrix bestätigt das ausdrücklich (E-14: „UNGEEIGNET … braucht Panel-Daten-Loader, keinen Code-Fix in der Strategie"). Für die DEBATE heißt das: jeder Pessimismus gegen diesen Cluster ist nicht aus Daten ableitbar, sondern nur aus Priors. Der Cluster verdient daher prozedural eine PILOT-Behandlung, nicht ein DROP — DROP wäre eine Entscheidung gegen einen Mechanismus, der nie gemessen wurde, was GM-1/GRUNDHALTUNG („Negative Ergebnisse sind Ergebnisse") gerade NICHT hergibt, weil hier kein negatives Ergebnis existiert.

### A-2 — Lead-Lag/BTC-Führung ist der einzige direktionale Ansatz im gesamten Material, der mit der harten empirischen Baseline (INC-05) kompatibel bleibt

INC-05 ist das vernichtendste Quer-Resultat des Registers: unkonditionale Richtungsprognose = AUC ≈ 0.50 (Münzwurf) auf 1h/4h mit klassischen Features. Das setzt C-09 (HMM-Direktional), aber auch alle PatchTST/MOMENT/TFSAX-Direktionalansprüche unter Revisionsdruck (Alignment C-09: „INC-05 setzt den unkonditionalen HMM-Direktional-Anspruch unter Revisionsdruck"). **Genau hier ist der Lead-Lag-Ansatz strukturell überlegen:** C-17/C-41/CS-13 behaupten gar keine unkonditionale Prognose, sondern eine *bedingte* Kante (AUC > 0.55 nur auf Konsens-Kanten ≥ 2/3 Achsen, in G1-Fenstern). Das ist exakt die Form, die INC-05 als einzig überlebensfähige übriglässt („direktionale Claims nur regime-konditioniert"). C-17 nutzt zudem eine *exogene* Informationsquelle (BTC→Alt-Fluss), nicht nur die Eigenhistorie des Ziel-Assets — der einzige Mechanismus im Register, der überhaupt aus der Münzwurf-Falle herausführen kann, weil er Information aus einem anderen Symbol importiert.

### A-3 — Mean-Reversion auf relative Querschnitts-Mispricings (C-13) ist mechanistisch robuster als die gescheiterten Single-Symbol-Momentum-Ansätze

CS-02 scheiterte, weil ein Single-Symbol-Momentum-Signal (Entropie-Kollaps → Aggression folgen) in 6–8 % Hit-Rate kollabierte und reines Execution-Rauschen war (E-04: hit_sum 0.179). C-13 macht das mechanistisch *Gegenteilige* und *Marktneutrale*: es handelt die Differenz `time-averaged return − ensemble mean` als Long-Short-Portfolio (claims_register C-13: „Sharpe ≥ 1.0 nach Fees, Long-Short"). Ein Long-Short-Konstrukt hat zwei strukturelle Vorteile, die genau die CS-02/CS-03-Schwächen adressieren: (1) es ist **richtungs-bias-immun** — die 189/190-Long-Pathologie aus E-06/E-12 (die sowohl S2 als auch S3 plagt) kann in einem dollar-neutralen Spread per Konstruktion nicht auftreten; (2) Mean-Reversion auf relative Mispricings hat einen ökonomischen Anker (Ergodizitäts-Defekt → Konvergenz), während Single-Symbol-Momentum keinen hatte. Das ist kein Beweis, aber es ist der einzige Cluster, dessen Konstruktion die zwei dokumentierten Pathologien des Registers (Long-Bias, Friktions-Dominanz) baulich umgeht.

### A-4 — Die Friktions-Kernrelation (11–15 bps > jede gemessene Roh-Edge) trifft den Lead-Lag-Cluster *am wenigsten* von allen Clustern

Die Kostenbaseline ist die härteste Einzelschranke des Registers: 11 bps Round-Trip-Taker übersteigt jede gemessene Roh-Edge (max |Roh| ≈ 4–7 bps). Aber diese Relation wurde auf **Single-Symbol-Sekunden/Minuten-Signalen** (S2/S3) gemessen. Der Lead-Lag-Mechanismus ist friktions-günstiger aus zwei Gründen: (1) C-17 behauptet ein BTC→Alt-Lag von 30–60 s (claims_register C-17), das auf *Alt-Forward-Returns über mehrere Minuten* zielt — der Edge-Horizont liegt über der Sekundenskala, auf der Friktion ~35× dominiert (E-16). (2) C-41 löst die Kante *frequenzaufgelöst* auf (Morlet-CWT) und handelt nur Bänder mit Phasenstabilität ≥ 80 % — das ist ein eingebauter Selektivitätsfilter, der die Trade-Frequenz drückt und damit die kumulative Friktionslast senkt. Das adressiert direkt den INC-03-Befund (S3 übertriggert: 50–60 Trades/24h). Ein selektiverer Trigger ist die mechanische Antwort auf das Friktions-Problem.

### A-5 — Die Harness-Investition ist gerechtfertigt, weil sie EIN Infrastruktur-Stück ist, das die GESAMTE Cross-Sectional-Familie auf einmal freischaltet (höchster Hebel pro Investition im Register)

Die Alignment-Matrix benennt das explizit als kritische Datenlücke #2: „Ein Multi-Symbol-Replayer schließt die gesamte Cross-Sectional-Familie auf einmal" (C-13, C-17, C-09, +C-41). Das ist ein ungewöhnlich günstiges Aufwand/Ertrag-Profil:
- **Eine** Investition (Panel-Daten-Loader) → vier Module (C-09/C-13/C-17/C-41) + zwei Strategien (CS-05, CS-13) werden gleichzeitig messbar.
- Im Gegensatz dazu schaltet der S4-Loader-Fix (Datenlücke #1) nur ungetestete DL-Modelle frei, die zusätzlich unter dem INC-05-Münzwurf-Verdikt stehen — schlechteres Ertragsprofil.
- Die Harness ist **kein Modell, kein Hyperparameter, kein Edge-Claim**, sondern reine Mess-Infrastruktur. Sie zu bauen ist erkenntnistheoretisch risikolos: sie kann keinen Ansatz künstlich gut aussehen lassen (anders als ein optimierter Threshold), sondern macht nur das Messen überhaupt möglich. Die Investition ist damit *vor* jedem Einzelnachweis gerechtfertigt, weil sie die Voraussetzung dafür ist, dass der Cluster überhaupt jemals ein Verdikt (positiv ODER negativ) bekommen kann. Solange die Harness fehlt, sind sechs Claims dauerhaft im UNTESTED-Limbo — das ist der teuerste Zustand (offene Position ohne Information).

### A-6 — Antwort auf GM-3 (BTC-Konzentration): die Konzentrations-Schwäche ist genau das Argument FÜR die Harness, nicht dagegen — und der Mechanismus ist universums-skalierbar

GM-3 ist real: BTC = 97 % des $-Aggregats, das 5-Symbol-Universum (BTC/ETH/SOL/BNB/XRP) ist BTC-dominiert; ein Querschnitt über 5 Symbole, von denen einer 97 % wiegt, hat ein Konzentrationsproblem. Drei Punkte dazu:
1. **GM-3 ist ein Artefakt des qty=1.0-Notional-Bugs UND der Universumsgröße, nicht des Mechanismus.** Die PRD-Quelle spezifiziert C-13 ausdrücklich auf einem „Top-20-USDT-Perp-Panel" (claims_register C-13: „z > 2.5 ist nicht durch BTC-Dominanz allein erklärbar" als Kernannahme). Das 5-Symbol-Replay-Universum ist die *Test*-Engstelle, nicht die *Design*-Engstelle. Cross-Sectional-Ansätze werden mit der Universumsbreite stärker, nicht schwächer — N=20 oder N=50 entschärft die BTC-Dominanz strukturell (BTC-Gewicht sinkt, Querschnitts-Dispersion steigt).
2. **Die Harness-Spezifikation muss das mit-adressieren** — und kann es billig: dollar-neutrale (nicht unit-neutrale) Positions-Normierung in der Panel-Engine eliminiert den GM-3/qty=1.0-Verzerrungseffekt per Konstruktion. Das ist Teil desselben Infrastruktur-Stücks aus A-5.
3. **C-17/C-41/CS-13 sind sogar *Nutznießer* der BTC-Dominanz:** wenn BTC tatsächlich 97 % des ökonomischen Gewichts trägt, ist „BTC führt, Alts folgen mit 30–60 s Lag" eine *plausiblere* Hypothese, nicht eine schwächere — die Konzentration begründet gerade die Lead-Lag-Asymmetrie. Für den *Lead-Lag*-Teil des Clusters ist GM-3 kein Problem, sondern die ökonomische Grundlage.

→ Validierungs-Gate-Konsequenz: jeder PILOT in diesem Cluster muss auf einem Universum mit **≥ 15–20 Symbolen** und **dollar-neutraler Normierung** laufen; das 5-Symbol/qty=1-Setup ist explizit als unzulässig für ein Verdikt zu deklarieren.

### A-7 — Markt-Differenzierung (Pflicht): der Cluster ist Futures-nativ, für Spot teil-übertragbar, für Optionen nur als Input

- **Futures-Perpetuals:** Primärmarkt. Alle sechs Claims sind laut Quelle Futures-spezifiziert (claims_register: Zielmarkt Perpetual durchgängig). Hier sind Datenlage (Multi-Symbol-Tickers/Trade-Streams vorhanden), Liquidität (BTC/ETH/SOL/BNB/XRP tief) und Mikrostruktur (einheitliche Perp-Kontraktlogik, Funding als zusätzliche Cross-Sectional-Achse) optimal. **Empfehlungstendenz: PILOT** — der einzige Markt, auf dem der Cluster vollständig getestet werden kann, sobald die Harness steht.
- **Spot:** Der Lead-Lag-*Mechanismus* (C-17/C-41) ist auf Spot konzeptionell übertragbar (BTC-Spot führt Alt-Spot), aber ohne Funding/OI-Achse verliert C-13 seine stärkste Cross-Sectional-Dimension, und Spot-Liquidität auf Alts ist dünner. **Tendenz: PARK** — als sekundärer Replikationstest erst nach Futures-Proof, kein eigener Pilot-Aufwand.
- **Optionen:** Kein Claim dieses Clusters adressiert Optionen direkt; INC-04 bestätigt, dass Optionen im ganzen Material kaum durchdacht sind und kein IV-Archiv existiert. Cross-Asset-Kohärenz (C-41) *könnte* langfristig eine Vol-Lead-Lag-Achse (BTC-RV führt Alt-IV) liefern, aber das ist spekulativ und an die fehlende IV-Aufzeichnung (INC-04) gebunden. **Tendenz: DROP für diesen Cluster** (Optionen werden anderswo via C-33/C-34 adressiert, nicht hier).

### A-8 — C-41 (Wavelet-Coherence) und C-17 (Transfer-Entropy) sind methodisch *orthogonal* und bilden ein eingebautes Robustheits-Kreuz — das senkt das Multiple-Testing-Risiko (GM-2) statt es zu erhöhen

GM-2 (keine FDR-Korrektur) ist eine berechtigte Cluster-übergreifende Sorge. CS-13 antwortet darauf *konstruktiv*: das K3-Design verlangt **Konsens über ≥ 2/3 Achsen** (C-17 Transfer-Entropy / C-41 Wavelet-Coherence / C-01 Multi-Level-OFI), bevor eine Kante handelbar ist (claims_register CS-13). Da C-17 (informationstheoretisch, Tail-gewichtet) und C-41 (frequenz-/phasenaufgelöst) auf unterschiedlichen mathematischen Kernen beruhen, ist ihre gemeinsame Bestätigung ein eingebauter Out-of-Method-Robustheitstest — ein Mechanismus, der zufällige Einzelbefunde herausfiltert, statt sie (wie bei S2/S3) ungefiltert zu handeln. Das Validierungs-Gate ist zudem das einzige im Cluster, das FDR-Korrektur *explizit fordert* (CS-13: „bedingte AUC > 0.55, Sharpe ≥ 0.8, FDR-korrigiert"). Dieser Cluster ist damit der einzige, der das GM-2-Problem im Design bereits internalisiert hat.

### A-9 — Vorgeschlagenes Validierungs-Gate (für PILOT-Empfehlung an den Judge)

Damit der Cluster aus UNTESTED herauskommt, schlage ich ein gestaffeltes, falsifizierbares Gate vor (Abbruchkriterien explizit):

1. **Infrastruktur-Gate (Vorbedingung):** Panel-Replay-Harness mit (a) ≥ 15 Symbolen, (b) dollar-neutraler Positions-Normierung (löst GM-3/qty=1.0), (c) synchronisiertem Multi-Symbol-Tick-Strom. Aufwand: ein Infrastruktur-Stück, schaltet C-09/C-13/C-17/C-41 + CS-05/CS-13 gemeinsam frei (A-5).
2. **Mechanismus-Gate (billig, vor Strategie-Aufwand):** Reiner Messlauf — existiert ein stabiler BTC→Alt-Lag? Gate: C-17 ρ(Alt-Forward, BTC-Move | T>0.05) ≥ 0.3 ODER C-41 Phasenstabilität ≥ 80 % auf ≥ 2 Konsens-Kanten, **out-of-sample (walk-forward, ≥ 2 disjunkte Fenster)**. Abbruch: beide unter Schwelle → Lead-Lag-These DROP.
3. **Strategie-Gate (CS-13/CS-05):** bedingte Richtungs-AUC > 0.55 auf Konsens-Kanten, FDR-korrigiert; Long-Short-Sharpe ≥ 0.8 nach 11 bps Friktion über ≥ 200 Trades walk-forward. Abbruch: AUC ≤ 0.55 in einem Fenster ODER Sharpe < 0.5.
4. **Konzentrations-Gate (GM-3-spezifisch):** Edge muss bestehen bleiben, wenn BTC aus dem Querschnitt entfernt wird (Alt-only-Subpanel). Abbruch: Edge verschwindet ohne BTC → Befund ist BTC-Artefakt, nicht Querschnitts-Edge.

### A-10 — Was ich zugestehe (ehrlich schwächste Stellen)

- **Kein einziger Mess-Punkt stützt diesen Cluster positiv.** Alle Argumente sind mechanistisch + analog, keiner ist empirisch. Die einzige *direkte* Evidenz (E-14) ist die Mess-Lücke selbst. Das ist die schwächste Stelle überhaupt: ich argumentiere für eine Investition auf reiner Plausibilität.
- **C-09 (HMM) ist der schwächste Claim im Bündel** und steht unter direktem INC-05-Revisionsdruck (Münzwurf-Baseline). Sein Direktional-Anspruch sollte im PILOT auf reines *Gating/Konditionierung* zurückgestuft werden, nicht als eigenständiges Signal — sonst importiert der Cluster genau die Direktional-Schwäche, die A-2 zu vermeiden behauptet.
- **C-01 (OFI) ist als CS-13-Achse 3 verbaut und trägt den INC-02-Verdacht** (Vorzeichen markiert MM-Replenishment, nicht Aggression — Alignment C-01). Wenn die OFI-Achse falsch orientiert ist, schwächt das den 2/3-Konsens-Mechanismus aus A-8. Das Konsens-Design fängt das teilweise ab (2 von 3 reichen), aber eine kontaminierte Achse ist ein realer Defekt.
- **GM-3 ist nur *teilweise* entschärfbar** (A-6): die Universums-Erweiterung auf ≥ 15 Symbole ist eine *Annahme* über zukünftige Datenbeschaffung; ob die nötigen Alt-Perp-Datenströme in ausreichender Tiefe/Synchronität verfügbar sind, ist selbst ungeprüft. Wenn das Universum praktisch auf BTC-dominierte 5 Symbole begrenzt bleibt, kollabiert der Cross-Sectional-Vorteil (A-3) und der Cluster reduziert sich auf reines BTC→Alt-Lead-Lag (C-17/C-41) ohne den Querschnitts-Reversions-Teil (C-13).

---

*Ende ADVOCATE-Teil. Skeptic antwortet Punkt für Punkt auf A-1 … A-10.*
