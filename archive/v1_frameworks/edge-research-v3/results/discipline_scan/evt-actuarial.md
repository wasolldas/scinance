# DISCIPLINE-SCAN — evt-actuarial

**Fachgebiet:** Extremwerttheorie (EVT) + Versicherungsmathematik (Aktuarwissenschaft)
**Stand:** 2026-07-07, Datenbasis: `results/audit_inventory.md` (nicht live verifiziert, s. dort)

## Schritt 1 — Methodenrecherche (Pflicht, über Rollen-Werkzeugkasten hinaus)

Web-Recherche (WebSearch, mehrere Suchen 2026-07-07) über POT/GPD + Breeden-Litzenberger/SVI hinaus:

1. **Hill-Schätzer** (Tail-Index über Ordnungsstatistiken, kein Schwellen-Fit) — Quelle:
   MDPI *Comparative Analysis of Tail Risk in Emerging/Developed Equity Markets* (2026),
   RyanOConnellFinance *EVT in Finance*. Bekannt instabil ("Hill horror plot"), aber
   nützlich als **unabhängiger Robustheits-Check** neben GPD-ξ, nicht als Ersatz.
2. **Block-Maxima/GEV** — Standard-Alternative zu POT; nutzt nur Blockmaxima, verschenkt
   Exzedenz-Information bei kurzen Fenstern. Für unsere ~3,5-Monats-Basis-Bestand
   (Basis-Bestand-Fenster, s.u.) ungünstig, weil Blockbildung (z. B. Tagesmaxima) die
   ohnehin knappe Beobachtungszahl weiter reduziert — POT bleibt Kernmethode, GEV nur als
   Sensitivitäts-Gegenprobe erwähnt.
3. **Extremal-Index θ (Cluster-EVT)** — Quelle: arXiv 2409.18643 (Kiriliouk/Zhou, *Tail
   Risk Analysis for Financial Time Series*), arXiv 2506.04656 (*Classification of
   Extremal Dependence*). Misst Clusterlänge von Extremereignissen (θ<1 ⇒ Clustering,
   z. B. Liquidationskaskaden) — direkt anschlussfähig an die Liquidations-/Insurance-
   Streams, aber datenhungrig (braucht viele Cluster-Instanzen).
4. **Mean-Excess-Plot / Threshold-Stability-Diagnostik** — Quelle: FasterCapital *Return
   Level Estimation*, Standard-Diagnostik zur Schwellenwahl (ξ(u)/σ(u) über Grid von u
   auftragen, niedrigsten stabilen u wählen). Kein eigenständiger Schätzer, aber
   Pflicht-Vorstufe vor jedem POT-Fit — in Methodik unten mit aufgenommen.
5. **Lognormal-Weibull-Mixture / Entropie-basierte RND-Extraktion** — Quelle:
   ScienceDirect S0304407624000940 (*Parametric RND via finite lognormal-Weibull
   mixtures*, 2024), Rompolis (Maximum-Entropie-RND). Alternative zu Breeden-
   Litzenberger/SVI für die risikoneutrale Dichte; laut Quelle robuster gegen fette linke
   Tails, aber komplexer zu kalibrieren als SVI. Als Robustheits-Gegenprobe zur SVI-Skew
   vorgeschlagen, nicht als Primärmethode (Rechenaufwand/Overfitting-Risiko bei kurzer
   Options-Historie).
6. **Spektrale Risikomaße (Exponential Spectral Risk Measures)** — Quelle: arXiv
   1103.5409/1103.5408. Kohärente Alternative zu VaR/ES mit expliziter Risikoaversions-
   Gewichtung der Tail-Quantile. Interessant als aktuarisches Framing der Konsistenzfrage
   (gewichtete Tail-Diskrepanz statt Punkt-ξ-Vergleich), aber **verworfen** als
   Kernmethode: fügt eine zusätzliche, schwer vorregistrierbare Gewichtsfunktions-
   Wahl hinzu, ohne die Kernfrage (ξ-Konsistenz) schärfer zu machen — bleibt als
   optionale Sensitivitäts-Erweiterung vermerkt.
7. **Aktuarische Reservierung/Ruin-Theorie (Return-Period, Ruin-Wahrscheinlichkeit)** —
   Quelle: ORMIR-Whitepaper (Jun Li), arXiv 1310.8604 (*Catastrophic deaths via EVT +
   Reinsurance-Pricing-Mikrosimulation*). Klassisches aktuarisches Werkzeug für
   Wiederkehrperioden aus GPD-Fit — direkt für Return-Period-Ableitung genutzt (s.
   Methodik), aber die Ruin-Wahrscheinlichkeits-Anwendung auf den Insurance Fund selbst
   ist **fachfremd** → siehe Cross-Domain-Hinweis unten.

---

### IC-EVT-1 — Tail-Shape-Konsistenz BTC/ETH: statistisches GPD-ξ vs. risikoneutrale Tail-Dichte
Fachgebiet: EVT/Aktuarwissenschaft
Kernfrage: Stimmt der aus realisierten Hochfrequenz-Renditen geschätzte GPD-Shape-Parameter ξ (POT) mit dem aus der aktuellen Optionen-IV-Surface implizierten Tail-Shape (risikoneutrale Dichte) überein, oder divergieren beide systematisch?
Erwogene Alternativen: (1) Hill-Schätzer als Robustheits-Gegenprobe zum GPD-ξ (instabil bei kleinem N, aber schätzer-unabhängige Zweitmeinung); (2) Block-Maxima/GEV verworfen — reduziert die ohnehin knappe Beobachtungszahl im Basis-Bestand-Fenster weiter, POT nutzt alle Exzedenzen; (3) Mean-Excess-Plot/Threshold-Stability-Diagnostik als Pflicht-Vorstufe zur Schwellenwahl, kein Ersatz; (4) Lognormal-Weibull-Mixture/Entropie-RND als Gegenprobe zu Breeden-Litzenberger/SVI bei der risikoneutralen Dichte-Extraktion (robuster bei fetten linken Tails laut Quelle, aber höherer Kalibrierungsaufwand — nur als Sensitivität, nicht Primärmethode).
Datenbindung: Statistische Seite: Bybit/Binance `publicTrade` + Deribit `publicTrade`/`book_summary`, **Basis-Bestand 2026-03-27…heute** (sofort nutzbar lt. Audit, ~3,5 Monate Tick-/Hochfrequenzdaten BTC+ETH — für hohe Perzentil-Schwellen (z. B. 1-Min-Renditen) reichen mehrere hundert Exzedenzen auch in diesem Fenster, KEINE Abhängigkeit vom Deep-Backfill nötig). Markt-Seite: Deribit `markprice.options` Live (ganze IV-Surface je Tick), forward-only seit ~2026-06-16, ~3 Wochen — mehrere Snapshot-Tage daraus als disjunkte Prüfzeitpunkte.
Methodik: Mean-Excess-Plot zur Schwellenwahl → POT/GPD-Fit (scipy `genpareto`) auf realisierten Returns je Symbol; parallel Hill-Schätzer als Gegenprobe. Risikoneutrale Dichte je Snapshot-Tag via Breeden-Litzenberger (2. Ableitung der IV-Surface nach Strike) oder SVI-Fit, daraus Tail-Shape extrahieren. Return-Period-Ableitung aus GPD-Fit als aktuarische Zusatzgröße (Einordnung, nicht Testgröße).
Nicht-Redundanz zu C-33: C-33 misst den GEMITTELTEN Level-Spread (IV−RV) über ≥12 Monate inkl. Stress-Periode. Dieser IC misst die FORM (ξ, Tail-Steilheit) an wenigen disjunkten Zeitpunkten, ohne Mittelung — Divergenz-Signal statt Prämien-Niveau. Explizit KEIN Rückgriff auf durchschnittliche Prämien-Vereinnahmung.
Friktions-Rolle: capital_free (Konsistenzfrage hat per Definition keine Round-Trip-Kosten)
Rechenaufwand: CPU (scipy.stats.genpareto + einfache Ableitung/Fit reichen; SVI-Kalibrierung über wenige Tage ist ebenfalls CPU-leicht)
Cross-Domain-Hinweis: keiner spezifisch für diesen IC (Kern bleibt EVT-eigen)
Offene Punkte für data-feasibility-scout: Reifegrad = **sofort testbar, bedingt**. Basis-Bestand-Return-Historie ist gesichert sofort nutzbar; das Live-Options-Fenster (~3 Wochen seit ~06-16) muss auf ECHTE Disjunktheit geprüft werden — die IV-Surface bewegt sich autokorreliert von Tag zu Tag, daher zählt nicht jeder Kalendertag als unabhängiger Prüfpunkt. Bitte konkret ermitteln: wie viele Tage mit spürbar unterschiedlichem Vol-Regime (z. B. getrennt durch einen Realized-Vol-Sprung) liegen in den ~3 Wochen? Selbstkill greift, falls <2 echte disjunkte Punkte übrig bleiben.

### IC-EVT-2 — Extremal-Index/Cluster-Tail auf Liquidationskaskaden vs. implizite Skew-Dynamik
Fachgebiet: EVT/Aktuarwissenschaft
Kernfrage: Bildet die implizite Vol-of-Vol-/Skew-Dynamik der Optionen-Surface die tatsächliche CLUSTERING-Struktur realisierter Extremereignisse (Extremal-Index θ aus Liquidationskaskaden) korrekt ab, oder preist der Markt Extremereignisse als unabhängiger (θ näher an 1) ein, als sie tatsächlich auftreten (θ≪1)?
Erwogene Alternativen: (1) Extremal-Index θ (Cluster-Länge = 1/θ) als Kernschätzer — direkt aus Liquidations-Timestamps ableitbar; (2) Hawkes-Branching-Ratio explizit VERWORFEN — bereits REFUTED (C-14, CLAUDE.md §1), andere Messgröße hier (θ statt ρ) reicht laut Rollen-Definition nicht automatisch als Entsperrung, daher nur als Kontrastfolie erwähnt, nicht als Methode übernommen; (3) Block-Maxima/GEV auf Liquidationsgrößen als Alternative zur POT-Clusterbildung — verworfen, weil Blockbildung bei ohnehin wenigen Kaskaden-Events die Stichprobe weiter dezimiert; (4) Spektrale Risikomaße als Gewichtungsalternative zur reinen θ-Schätzung — als optionale Sensitivität vermerkt, nicht Kernmethode (siehe Recherche-Punkt 6 oben).
Datenbindung: Bybit `allLiquidation` + `insurance` Live, forward-only seit ~2026-06-16 (~3 Wochen Historie zum Audit-Datum). Vergleichsseite: Deribit Options-Skew-Dynamik im selben Fenster.
Methodik: Extremal-Index-Schätzung (Blocks-/Runs-Estimator) auf Liquidations-Interarrival-Zeiten je Symbol; Vergleich mit Skew-Steilheits-Änderung über dasselbe Fenster.
Nicht-Redundanz zu C-33: Betrifft Cluster-FORM (θ), keine gemittelte Prämie — unabhängig von C-33.
Friktions-Rolle: capital_free
Rechenaufwand: CPU
Cross-Domain-Hinweis: Die Insurance-Fund-Seite dieser Frage (reicht der Fund-Bestand angesichts der beobachteten Cluster-Statistik? Ruin-Wahrscheinlichkeit im aktuarischen Sinn) ist eher `mechanism-design`-Territorium (Auktionstheorie/ADL-Mechanik) als reine EVT — dort als aktuarische Ruin-Perspektive auf den Insurance Fund zur Prüfung weitergeben, nicht hier umgesetzt.
Offene Punkte für data-feasibility-scout: **Data-gated.** PROGRAM_FINAL_REPORT §7/§8 nennt für die verwandte Kaskaden-Schwelle (C-27/28/29, ~7 Insurance-Events/h) einen Vorlauf bis ≥30 Ereignisse ca. Aug.–Okt. 2026 — als Analogie-Richtwert für belastbare Extremal-Index-Schätzung ebenfalls zu knapp; ~3 Wochen Live-Historie liefern nach grober Schätzung deutlich weniger als die für einen stabilen Cluster-Schätzer nötigen Dutzende Kaskaden-Instanzen. Selbst als data-gated markiert, Wiedervorlage-Termin analog C-27/28/29 (Aug.–Okt. 2026).

### IC-EVT-3 — Multi-Zyklen-Tail-Form-Stabilität (2014/2019–2026) via Tardis-Monatsstichproben
Fachgebiet: EVT/Aktuarwissenschaft
Kernfrage: Ist der statistische GPD-Shape ξ über mehrere Marktzyklen (2018-Crash, COVID-2020, LUNA/FTX-2022, aktuelle Periode) STABIL (im Sinne der Return-Period-Ableitung), oder verschiebt sich ξ regimeabhängig in einer Weise, die die aktuelle risikoneutrale Tail-Bepreisung nicht erfasst?
Erwogene Alternativen: (1) Block-Maxima/GEV hier tatsächlich sinnvoll als Gegenprobe (bei mehrjährigen Blöcken/Zyklen ist der Beobachtungsverlust gegenüber POT gering) — im Gegensatz zu IC-EVT-1/2 hier NICHT verworfen, sondern als gleichwertige Zweitmethode vorgesehen; (2) Hill-Schätzer je Zyklus als Robustheits-Check; (3) Lognormal-Weibull-Mixture-RND für die (dünnen) historischen Options-Stichproben, da SVI bei nur 1 Tag/Monat Datenpunkten pro Zyklus schwerer zu stabilisieren ist; (4) aktuarische Return-Period-Schätzung als Hauptoutput, direkt vergleichbar zwischen Zyklen (Kern-Idee aus Punkt 7 der Methodenrecherche).
Datenbindung: BitMEX `publicTrade` (XBTUSD, ab 2014-11-22), Deribit `publicTrade`/`dvol` (ab 2019-03-30/2021-04-01), Tardis `options_chain` (1 Tag/Monat-Stichprobe seit 2019) — alle drei laut Audit **DEEP-BACKFILL-IM-AUFBAU**, nicht Teil des gesicherten Basis-Bestands.
Methodik: POT/GPD + GEV je identifiziertem Zyklus-Fenster auf Realized Returns; Return-Period-Vergleich über Zyklen; risikoneutrale Tail aus den dünnen Tardis-Monatsstichproben als Kontrastgröße (explizit als Sampling-Design, kein tägliches Panel, vorregistriert).
Nicht-Redundanz zu C-33: Reine Form-Stabilitätsfrage über Zyklen, keine gemittelte Prämie einer Einzelperiode — unabhängig von C-33.
Friktions-Rolle: capital_free
Rechenaufwand: CPU
Cross-Domain-Hinweis: keiner spezifisch.
Offene Punkte für data-feasibility-scout: **Data-gated bis Manifest-Coverage-Check.** Ohne Zugriff auf `harvest_manifest.sqlite` (lt. audit_inventory.md nicht in dieser Sandbox vorhanden) ist unklar, wie weit der Deep-Backfill für BitMEX/Deribit/Tardis tatsächlich zurückreicht (`done_days`-Prüfung nötig). Dies ist genau das Fenster, das „mehrere Zyklen/Crashes" (CLAUDE.md §0) tragen könnte — aber erst nach echtem Coverage-Nachweis auf der Windows-Maschine des Nutzers als „sofort testbar" umzuwidmen. Bis dahin: data-gated, kein fixes Wiedervorlage-Datum (abhängig vom Backfill-Fortschritt, nicht von externer Ereignis-Reife wie bei IC-EVT-2).

---

## Zusammenfassung Selbstkill-Prüfung
- IC-EVT-1: kein Selbstkill — sofort testbar, aber Disjunktheit der Live-Options-Snapshots muss data-feasibility-scout noch quantifizieren (Grenze: <2 disjunkte Punkte → doch data-gated).
- IC-EVT-2: explizit data-gated (Selbstkill-Kriterium „weniger als 2 disjunkte, vollständige Prüfzeitpunkte" hier eher „zu wenige Cluster-Instanzen" — analog behandelt, nicht als testbar vorgeschlagen).
- IC-EVT-3: explizit data-gated (fehlender Manifest-Zugriff, DEEP-BACKFILL-IM-AUFBAU).
- Keiner der drei Vorschläge läuft auf eine gemittelte Prämien-Level-Aussage hinaus → kein C-33-Duplikat.
