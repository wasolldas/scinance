# PRE-SCREEN — Friktions-/Tradability-Audit (friction-tradability-auditor)

**Stand:** 2026-07-07. Geprüft: alle 20 IC-Vorschläge aus `results/discipline_scan/*.md` gegen die
Friction-Wand (11 bps Taker / ~15 bps inkl. Slippage, 300-ms-Latenz-Haircut, CLAUDE.md §0) und die
Mess-Gate/Tradability-Gate-Trennung (CLAUDE.md §2 Regel 2). Kein Datenlauf, keine Code-Ausführung —
reiner Struktur-Check.

**Zentrales Prüfkriterium für alle als "Risiko-Overlay" deklarierten ICs:** Ein Overlay moduliert
Sizing/Exposure eines EXISTIERENDEN Bestands. Nach PROGRAM_FINAL_REPORT (0/13 handelbare Kanten) hat
das Programm derzeit **keine bestätigte, laufende Basis-Strategie**, deren Exposure ein Overlay
sinnvoll modulieren könnte. Kein einziger der unten geprüften "Overlay"-Vorschläge benennt konkret,
WELCHER existierende Bestand (z. B. eine passive Spot-Position, ein laufendes Buch) moduliert werden
soll — alle sprechen abstrakt von "bestehenden Exposures". Das ist der **"Overlay-über-Nichts"-Fehler**:
so lange keine Basis-Position konkret benannt ist, ist die Overlay-Einstufung eine unbewiesene Behauptung,
keine strukturelle Tatsache. Konsequenz unten je IC einzeln geprüft.

---

## Kopftabelle

| IC | Rolle (bestätigt/korrigiert) | Wand-Risiko | Overlay-über-Basis-Problem |
|---|---|---|---|
| IC-RMT-1 | (b)→korrigiert auf primär (c), Overlay-Zusatzbehauptung ungedeckt | n/a-Overlay (fraglich) | JA |
| IC-RMT-2 | (c) bestätigt | hoch (Mikro, falls Folge-Arb) | entfällt (kein Overlay-Claim) |
| IC-RMT-3 | (c) bestätigt (Methodik-Zulieferer) | n/a | entfällt |
| IC-RMT-4 | (c) bestätigt (Overlay nur "potenziell") | hoch (Options-Snapshot, intraday) | entfällt (kein harter Claim) |
| IC-EVT-1 | (c) bestätigt | n/a | entfällt |
| IC-EVT-2 | (c) bestätigt | n/a | entfällt |
| IC-EVT-3 | (c) bestätigt | n/a | entfällt |
| IC-NET-1 | (b)→korrigiert auf primär (c) | hoch (sub-Tages-Fenster, 6h/24h) | JA |
| IC-NET-2 | (b)→korrigiert auf primär (c) | hoch (sub-Tages-Fenster) | JA |
| IC-NET-3 | (b), aber selbst als Existenzfrage relativiert (H-04-Analogie) | hoch (explizit anerkannt) | JA (aber ehrlich deklariert) |
| IC-MECH-1 | (c) bestätigt | hoch (Antizipations-Fenster kurz) | entfällt |
| IC-MECH-2 | (c) bestätigt | hoch (Bunching-Ausnutzung wäre Mikro) | entfällt |
| IC-MECH-3 | (c) bestätigt | hoch (Exekutions-Asymmetrie ist Mikro) | entfällt |
| IC-MECH-4 | (c) bestätigt (PARK) | n/a | entfällt |
| IC-CLIM-1 | (c) bestätigt, Tradability sauber als Folge-Hypothese getrennt | **günstig** (~25–75×) | entfällt |
| IC-CLIM-2 | (c) bestätigt | **günstig** (~13–55×, Event-Zahl ist Flaschenhals) | entfällt |
| IC-CLIM-3 | (c) bestätigt | **günstig** (~25–75×, wie CLIM-1) | entfällt |
| IC-DEND-1 | (c) bestätigt (als "Alpha-Hypothese (capital_free)" korrekt gekennzeichnet) | günstig plausibel, aber NICHT vorgerechnet | entfällt |
| IC-DEND-2 | n/a (Infrastruktur, kein Alpha-Claim) | n/a | entfällt |
| IC-DEND-3 | n/a (Infrastruktur, kein Alpha-Claim) | n/a | entfällt |

---

## Einzel-Checks

### Friktions-Check IC-RMT-1
Rolle: (b) Regime-/Risiko-Overlay laut Selbst-Einstufung — **korrigiert**: primär (c) reine Mess-/
Existenzfrage (existieren signifikante Eigenwerte außerhalb MP-Bulk?), die Overlay-Nutzung ("Sizing-
Anpassung bestehender Exposures") ist eine unbelegte Zusatzbehauptung.
Grobrechnung (falls a/b): entfällt, solange keine Basis-Position benannt ist — die Wand gilt nicht
direkt, aber auch der Overlay-Freibrief gilt nicht, bis die Basis existiert.
capital_free korrekt gesetzt: JA (der Mess-Teil ist sauber capital_free), aber die Feld "Friktions-
Rolle: Risiko-Overlay ... umgeht die Friction-Wand strukturell" geht zu weit — das ist eine
Tradability-Aussage, die noch nicht verdient ist.
Anti-Gaming: entfällt (keine konkurrierenden Latenz-/Exekutions-Varianten in diesem Stadium).
Empfehlung: REWORK (Grund: Overlay-Basis nicht benannt — "Overlay-über-Nichts"-Problem. Vorschlag muss
entweder (1) auf reine (c)-Formulierung zurückstufen und die Overlay-Anwendung explizit als offene,
separate Folge-Hypothese kennzeichnen — analog H-04→H-04b —, oder (2) konkret benennen, welcher
bestehende Bestand moduliert werden soll und warum der real existiert).

### Friktions-Check IC-RMT-2
Rolle: (c) reine Mess-/Explorationsfrage — Selbst-Einstufung korrekt, inkl. expliziter Klausel, dass
ein daraus folgendes Handelssignal SEPARATE Tradability-Hypothese wäre.
Grobrechnung (falls a/b): entfällt (kein a/b-Claim). Für die Aufzeichnung: falls Fragmentierung je zu
einem Cross-Exchange-Arb-Signal führt, wäre das ein Sub-Minuten/Minuten-Spread-Signal — voraussichtlich
in derselben Größenordnung wie die 80–500×-unter-der-Wand-Fälle (BTC→ETH-Lead-Lag, OFI), da
Cross-Venue-Spreads bei liquiden Perps typischerweise selbst im Bereich von wenigen bps liegen.
capital_free korrekt gesetzt: JA.
Anti-Gaming: entfällt.
Empfehlung: WEITERLEITEN AN CRITIC.

### Friktions-Check IC-RMT-3
Rolle: (c) — Methodik-Validierung/Zulieferer für IC-RMT-1 (Referenzverteilungs-Korrektur), kein eigener
Handels-Claim. Selbst-Einstufung "Risiko-Overlay-Zulieferer" ist irreführende Terminologie (es ist kein
Overlay selbst), aber der Inhalt ist korrekt (c).
Grobrechnung: entfällt.
capital_free korrekt gesetzt: JA.
Anti-Gaming: JA (zwei konkurrierende Nullmodelle — Gaussian-Wishart-MP vs. Lévy-stabil — werden BEIDE
berichtet, kein Herauspicken).
Empfehlung: WEITERLEITEN AN CRITIC.

### Friktions-Check IC-RMT-4
Rolle: (c) capital_free Mess-Frage, Overlay explizit nur als "potenziell" markiert, kein harter Claim
in dieser Runde — Selbst-Einstufung korrekt und vorbildlich vorsichtig formuliert.
Grobrechnung (falls a/b): entfällt (kein harter b-Claim). Für spätere Folge-Hypothese: Options-IV-
Surface-Snapshots sind intraday/Minutenraster — jede daraus abgeleitete Sizing- oder Handelsidee müsste
gegen Options-Bid/Ask-Spreads (typischerweise deutlich > 15 bps bei Krypto-Optionen) antreten, also
strukturell ungünstiger als die Perp-Wand selbst.
capital_free korrekt gesetzt: JA.
Anti-Gaming: entfällt.
Empfehlung: WEITERLEITEN AN CRITIC. Datenreife-Caveat (nur 1 Regime) bereits selbst korrekt als
data-gated für Mehrregime-Aussage gekennzeichnet.

### Friktions-Check IC-EVT-1
Rolle: (c) reine Konsistenzfrage (GPD-ξ vs. risikoneutrale Tail-Form) — korrekt.
Grobrechnung: entfällt (per Definition keine Round-Trip-Kosten bei einer Konsistenzfrage).
capital_free korrekt gesetzt: JA.
Anti-Gaming: JA (Hill-Schätzer als unabhängige Gegenprobe zu GPD-ξ wird als Gegenprobe, nicht als
Ersatz bei Bedarf, mitberichtet; Lognormal-Weibull-Mixture explizit nur als Sensitivität deklariert,
nicht als versteckte Alternative zum Herauspicken).
Empfehlung: WEITERLEITEN AN CRITIC.

### Friktions-Check IC-EVT-2
Rolle: (c) — korrekt, capital_free.
Grobrechnung: entfällt.
capital_free korrekt gesetzt: JA.
Anti-Gaming: entfällt (keine konkurrierenden Robustheits-Varianten mit Cherry-Pick-Risiko).
Empfehlung: STRUKTURELLER FRICTION-DROP entfällt hier (kein Friction-Bezug), aber Status ist
selbst korrekt als data-gated markiert (Analogie C-27/28/29, Aug.–Okt. 2026) — WEITERLEITEN AN CRITIC
mit dem data-gated-Vermerk.

### Friktions-Check IC-EVT-3
Rolle: (c) — korrekt, capital_free.
Grobrechnung: entfällt.
capital_free korrekt gesetzt: JA.
Anti-Gaming: entfällt.
Empfehlung: WEITERLEITEN AN CRITIC (data-gated bis Manifest-Coverage-Check, selbst korrekt so markiert).

### Friktions-Check IC-NET-1
Rolle: (b) Risiko-Overlay/Regime-Filter laut Selbst-Einstufung — **korrigiert**: primär (c)
Mess-/Frühwarn-Frage (steigt Rekonfigurationsrate vor Stress messbar?). Die Overlay-Bezeichnung
prejudiziert die Anwendung, bevor eine Basis-Position benannt ist.
Grobrechnung (falls a/b): Rollierende Fenster sind 6h/24h — sub-Tages-Horizont, NICHT die
climatology-Sonderrolle (§5). Würde dies je direkt gehandelt (statt als Overlay), läge das Bewegungs-
Zeitfenster in derselben Kategorie wie die 13 gefallenen Mikrostruktur-Signale — hohes Wand-Risiko.
capital_free korrekt gesetzt: JA für den Mess-Teil, aber die Formulierung "keine eigenständige
Round-Trip-Strategie" wird als bereits erwiesen behauptet statt als zu prüfende Bedingung.
Anti-Gaming: entfällt.
Empfehlung: REWORK (Grund: Overlay-über-Nichts — keine existierende Basis-Position benannt, die
moduliert würde; auf (c) zurückstufen und Tradability explizit als offene Folge-Hypothese kennzeichnen).

### Friktions-Check IC-NET-2
Rolle: (b) laut Selbst-Einstufung — **korrigiert**: primär (c), aus denselben Gründen wie IC-NET-1.
Grobrechnung (falls a/b): rollierende Korrelationsfenster (nicht explizit auf Tagesbasis reskaliert wie
IC-NET-1, aber ebenfalls sub-Tages/Intraday-Charakter über Basis-Bestand-Returns) — hohes Wand-Risiko
für jede direkte Handelsableitung.
capital_free korrekt gesetzt: JA, gleiche Einschränkung wie IC-NET-1.
Anti-Gaming: JA (Louvain, Core-Periphery UND Katz/PageRank werden alle als Varianten nebeneinander
berichtet, kein Herauspicken der günstigsten Partitionsmethode).
Empfehlung: REWORK (Grund: identisch zu IC-NET-1 — Overlay-über-Nichts).

### Friktions-Check IC-NET-3
Rolle: (b) laut Selbst-Einstufung, aber der Vorschlag relativiert sich selbst am klarsten von allen
Overlay-Claims: "TE-Schätzung selbst ist ohnehin nur als Existenzfrage zu verstehen (H-04-Lehre: reales
Signal, 80× unter Friktionswand)." Das ist der ehrlichste Umgang mit dem Overlay-über-Nichts-Problem im
gesamten Satz — der Agent benennt selbst, dass ein TE-Netzwerksignal nach H-04-Präzedenz weit unter der
Wand liegen dürfte, auch aggregiert über Knotentypen.
Grobrechnung (falls a/b): explizit über H-04-Analogie verankert — Einzelpaar-TE lag 80× unter der Wand;
eine Knotentyp-Aggregation über mehrere gleichzeitige TE-Kanten dürfte die Größenordnung nicht
grundsätzlich ändern (Aggregation glättet Rauschen, verändert aber nicht die Bruttosignalgröße pro
Kante).
capital_free korrekt gesetzt: JA — und mit der stärksten Selbstkritik aller Overlay-Claims.
Anti-Gaming: JA (Katz vs. PageRank als Doppelmaß berichtet, kein Cherry-Picking).
Empfehlung: REWORK, aber MILDESTE Form (Grund: Overlay-Basis weiterhin nicht benannt, aber der Vorschlag
selbst hat die Konsequenz — Existenzfrage statt Overlay — bereits fast vollständig vorweggenommen;
Rework reduziert sich effektiv auf eine Umbenennung Rolle (b)→(c) im Feld selbst, kein inhaltliches
Nacharbeiten nötig).

### Friktions-Check IC-MECH-1
Rolle: (c) reine Existenzfrage (Orderfluss-/Spread-Antizipation vor ADL-Trigger) — korrekt, capital_free.
Grobrechnung (falls a/b): entfällt (c). Für Aufzeichnung: falls handelbar, wäre das Antizipations-
Fenster kurz (Stunden vor 8h-Drawdown-Schwelle) — Bewegungsgröße vermutlich klein, hohes Wand-Risiko
analog zu den 13 gefallenen Mikrostruktur-Signalen.
capital_free korrekt gesetzt: JA.
Anti-Gaming: entfällt.
Empfehlung: STRUKTURELLER FRICTION-DROP entfällt (kein Handels-Claim in dieser Runde). WEITERLEITEN AN
CRITIC mit data-gated-Vermerk (Ereignisdichte, Analogie C-27/28/29, Aug.–Okt. 2026).

### Friktions-Check IC-MECH-2
Rolle: (c) Struktur-/Verhaltensfakt (Bunching an Margin-Kink), keine direkte Preis-Strategie — korrekt,
capital_free, einziger sofort testbarer IC dieses Agenten.
Grobrechnung (falls a/b): entfällt (c). Für Aufzeichnung: eine direkte Ausnutzung des Bunching-Effekts
(z. B. Front-Running der Kante) wäre ein Mikrostruktur-Timing-Signal — hohes Wand-Risiko, falls je als
eigener Handels-Claim formuliert.
capital_free korrekt gesetzt: JA.
Anti-Gaming: entfällt.
Empfehlung: WEITERLEITEN AN CRITIC.

### Friktions-Check IC-MECH-3
Rolle: (c) Existenzfrage (Adverse-Selection-Asymmetrie ADL vs. Orderbuch-Liquidation) — korrekt,
capital_free "zunächst".
Grobrechnung (falls a/b): entfällt (c). Für Aufzeichnung: die Kursreaktion je Liquidationstyp ist ein
Ereignis-nahes, kurzfristiges Preiseffekt-Signal — sollte es je gehandelt werden, hohes Wand-Risiko wie
bei den Kaskaden-/Mikrostruktur-Vorgängern.
capital_free korrekt gesetzt: JA.
Anti-Gaming: entfällt.
Empfehlung: Status bereits selbst korrekt als data-gated/BLOCKIERT gekennzeichnet (ungeklärtes
adlAlert-Topic) — WEITERLEITEN AN CRITIC mit Blockade-Vermerk, kein Rework nötig, da der Agent das
Problem bereits vollständig offengelegt hat.

### Friktions-Check IC-MECH-4
Rolle: (c) spekulative Mess-Frage, selbst als PARK/niedrige Priorität eingereicht — korrekt, kein
Handels-Claim, keine Overlay-Behauptung.
Grobrechnung: entfällt.
capital_free korrekt gesetzt: JA (implizit, kein expliziter Round-Trip-Claim).
Anti-Gaming: entfällt.
Empfehlung: Status PARK vom Agenten selbst korrekt gesetzt (C-20-Kollisionsvermeidung) — kein
Rework nötig, direkt ins PARK-Register.

### Friktions-Check IC-CLIM-1
Rolle: (c) capital_free Mess-Frage (CRPS-Kalibrierung AnEn vs. HAR-RV-Baseline über 3 Tage) — korrekt,
und VORBILDLICH sauber von Tradability getrennt: "dies ist Mess-Gate zuerst ... Tradability ... ist
separate Folge-Hypothese für friction-tradability-auditor" — exakt das H-04→H-04b-Muster prospektiv
angewendet, statt es erst nach einem WEITER nachzuholen.
Grobrechnung (falls a/b): selbst vorgerechnet — bei 3-Tage-Horizont und typischer Tagesvol 2–5%
(√3-Skalierung) erwartete kumulierte Bewegung ~350–870 bps gegen 11–15 bps Wand → Verhältnis ~25–75×
ÜBER der Wand. Bestätigt: climatology-Sonderrolle (CLAUDE.md §5) ändert die Arithmetik hier tatsächlich
strukturell gegenüber den 80–500×-UNTER-der-Wand-Fällen der 13 Vorgänger — das ist die richtige Richtung
und die einzige positive Größenordnungs-Umkehr im gesamten Satz.
capital_free korrekt gesetzt: JA.
Anti-Gaming: JA — die Bandbreite (~25–75×) wird als Spanne berichtet, nicht als optimistischste
Einzelzahl herausgepickt; ebenso wird die Datenreife ehrlich als "teilweise data-gated" (nur ~100 Tage,
vermutlich 1 Vol-Regime) markiert statt verschwiegen.
Empfehlung: WEITERLEITEN AN CRITIC. Bester Kandidat im gesamten Satz für Friktions-Überlebensfähigkeit.

### Friktions-Check IC-CLIM-2
Rolle: (c) capital_free — korrekt.
Grobrechnung (falls a/b): selbst vorgerechnet — 1–5-Tage-Regimewechsel-Move ~2–6% gegen 11–15 bps
→ Verhältnis ~13–55× ÜBER der Wand. Selbst korrekt angemerkt, dass die eigentliche Einschränkung nicht
die Friktion, sondern die Ereigniszahl (nur ~5/~1 Trigger bei 95./99.-Perzentil auf ~100 Tagen) ist —
sauberes GL-012-Bewusstsein.
capital_free korrekt gesetzt: JA.
Anti-Gaming: JA (Granger-Kausalität und Schaake-Shuffle als Alternativen geprüft und mit Begründung
verworfen, nicht verschwiegen).
Empfehlung: WEITERLEITEN AN CRITIC. Zweitbester Kandidat für Friktions-Überlebensfähigkeit (Ereigniszahl,
nicht Friktion, ist hier der Flaschenhals).

### Friktions-Check IC-CLIM-3
Rolle: (c) capital_free, baut auf IC-CLIM-1 auf — korrekt.
Grobrechnung (falls a/b): identisch zu IC-CLIM-1 (~25–75×), da dieselbe Zielgröße (künftige
Bewegungsgröße), nur über Spread statt Median vorhergesagt. Bestätigt.
capital_free korrekt gesetzt: JA.
Anti-Gaming: JA (klassische lineare Spread-Skill-Korrelation als Baseline explizit mitgeführt, nicht nur
das schärfere SRS-Kriterium berichtet).
Empfehlung: WEITERLEITEN AN CRITIC. Dritter der drei climatology-ICs mit günstiger Arithmetik — alle drei
teilen sich jedoch dieselbe Datenbasis (Coverage-Risiko korreliert, nicht unabhängig).

### Friktions-Check IC-DEND-1
Rolle: (c) — als "Alpha-Hypothese (capital_free)" korrekt gekennzeichnet (Existenzfrage: synchrone
Pointer-Tage + Pre-Event-Drift 1–5 Tage davor).
Grobrechnung (falls a/b): **fehlt im Vorschlag** — anders als die climatology-ICs liefert IC-DEND-1
keine explizite Friktions-Rechnung, obwohl der Zielhorizont (1–5 Tage vor einem Pointer-Tag) strukturell
in derselben günstigen Kategorie wie IC-CLIM-2 liegen könnte (Mehrtage-Vorlauf statt Mikrostruktur).
Einschränkung: die Zielmetrik ist "z. B. Realized-Vol-Drift oder Funding-Rate-Krümmung" — nicht
zwingend ein direktional handelbarer Preis-Move, daher ist unklar, ob die 11–15-bps-Wand hier überhaupt
das relevante Maß ist, bevor nicht eine konkrete Round-Trip-Definition vorliegt.
capital_free korrekt gesetzt: JA.
Anti-Gaming: JA (Cropper- UND Neuwirth-Fenster als zwei unabhängige Cross-Checks, Schwelle
60%/|C|≥1.5 vorab fixiert, explizit unter Verweis auf die 2019/2023-Methodenwahl-Sensitivitätspapiere).
Empfehlung: WEITERLEITEN AN CRITIC, mit AUFLAGE an registry-keeper/fable5-deep-validator: vor
Pre-Registration einer Tradability-Folge-Hypothese eine explizite Grobrechnung nach IC-CLIM-2-Vorbild
nachreichen (Mehrtage-Horizont könnte günstig sein, ist aber unbewiesen, solange die Zielmetrik nicht
auf einen Preis-Return übersetzt ist).

### Friktions-Check IC-DEND-2
Rolle: n/a — explizit als Infrastruktur-/Datenqualitäts-Beitrag deklariert, KEIN Alpha-Claim (vom Agenten
selbst so verlangt: "critic bitte nicht gegen Novelty/Alpha-Dimension scoren"). Friktions-Wand nicht
anwendbar, da kein Signal-Claim vorliegt.
Grobrechnung: entfällt.
capital_free korrekt gesetzt: JA (gegenstandslos, da kein Signal).
Anti-Gaming: entfällt.
Empfehlung: WEITERLEITEN AN CRITIC (als Infrastruktur-Voraussetzung, nicht als Hypothese scoren).

### Friktions-Check IC-DEND-3
Rolle: n/a — Infrastruktur-/methodischer Beitrag (Mindest-Serienzahl-Formel), kein Alpha-Claim.
Grobrechnung: entfällt.
capital_free korrekt gesetzt: JA (gegenstandslos).
Anti-Gaming: entfällt.
Empfehlung: WEITERLEITEN AN CRITIC (als Infrastruktur-Voraussetzung, nicht als Hypothese scoren).

---

## Zusammenfassung für Orchestrator

**Fünf ICs mit "Overlay"-Selbsteinstufung (IC-RMT-1, IC-NET-1, IC-NET-2, IC-NET-3) laufen strukturell
in dasselbe Problem: keine der Selbst-Einstufungen benennt eine konkrete, existierende Basis-Position,
deren Exposure moduliert würde.** Nach 0/13 bestätigten handelbaren Kanten im Programm ist "bestehende
Exposures" eine unbelegte Annahme. Empfehlung: alle vier auf Rolle (c) zurückstufen und die
Overlay-Anwendung explizit als offene, separate Folge-Hypothese kennzeichnen (H-04→H-04b-Muster) statt
sie bereits als friktionsfrei zu behaupten. IC-NET-3 verdient dabei die mildeste Rework-Auflage, da der
Vorschlag sich selbst schon fast vollständig auf (c) zurückgestuft hat (explizite H-04-Analogie: TE-Signal
80× unter der Wand).

**Beste Friktions-Überlebensfähigkeit (für spätere Tradability-Folge-Hypothesen):** IC-CLIM-1 (~25–75×
ÜBER der Wand, vorbildlich von Tradability getrennt) und IC-CLIM-3 (identisch ~25–75×, teilt Datenbasis
mit CLIM-1) knapp vor IC-CLIM-2 (~13–55×, aber Ereigniszahl statt Friktion ist der eigentliche
Flaschenhals). Alle drei bestätigen CLAUDE.md §5: der Mehrtage-Horizont kehrt die Arithmetik der 13
Vorgänger-Signale (80–500× UNTER der Wand) tatsächlich um. IC-DEND-1 liegt in einer strukturell
ähnlichen Mehrtage-Kategorie (1–5-Tage-Vorlauf), hat aber im Gegensatz zu den climatology-ICs keine
explizite Grobrechnung geliefert — als Auflage an registry-keeper vermerkt.

**Kein struktureller Friction-DROP in dieser Runde:** anders als H-03/CFAR liefert keiner der 20
IC-Vorschläge bereits in der Selbstdarstellung eine Größenordnung, die im günstigsten Fall die Wand
sicher verfehlt — alle capital_free-ICs (14 von 20) sind ohnehin friktionsirrelevant für DIESE Runde,
die vier Overlay-Kandidaten gehen mit REWORK zurück statt mit DROP, und die drei climatology-ICs sowie
IC-DEND-1 liegen plausibel über der Wand.
