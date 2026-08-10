# Welle 5 — Abschlussbericht (GPU-Wellen H-14..H-18)

> Stand 2026-08-07, nach GL-021. Erstellt vom Orchestrator aus den fünf
> Gate-Verdikten (GL-014, GL-015, GL-019, GL-020, GL-021), den archivierten
> Payloads unter `state/` und dem Zwischenbericht vom 2026-07-25.
> Bindend bleiben ausschliesslich `hypothesis_registry.md` und `gate_log.md`.

---

## 1. Ergebnis in einem Absatz

Welle 5 war die erste GPU-Welle des Programms: fünf vorregistrierte Hypothesen,
~300 GPU-Stunden auf einer RTX 5060 Ti, verteilt über drei Wochen und rund
25 Checkpoint-Sessions. **Zwei Hypothesen bestehen ihr Gate vollständig
(H-16, H-15) — beide kapitalfrei, beide gegen ein vorregistriertes
"DROP erwartet"-A-priori.** Eine ist ein abgeschlossenes Auflösungs-Audit
(H-18), eine bleibt ohne Verdikt, weil ihr Redundanz-Gate strukturell nicht
auswertbar war (H-17), und eine hat sich durch ihre eigene vorregistrierte
Positivkontrolle als methodisch invalide erwiesen (H-14). Kein einziger
Torpfosten wurde verschoben.

---

## 2. Die fünf Verdikte

| GL | H | Thema | Verdikt | Kernzahl |
|---|---|---|---|---|
| GL-014 | H-18 | GL-006-Auflösungs-Audit (N: 200 → 100.000) | **AUDIT-BEFUND** (kein Verdikt) | 12/12 Survivor bleiben BH-sig; nur 4/12 halten p≤1e-3 |
| GL-015 | H-16 | Time-Arrow-CNN (Zeit-Irreversibilität) | **WEITER (kapitalfrei)** | AUC 0,733/0,735/0,665/0,642 (4/5), Null exakt 0,50 |
| GL-019 | H-17 | Venue-Fingerprint (Contrastive, LOSO) | **VERDIKT AUSSTEHEND** | 5/5 Folds bestanden (BalAcc bis 0,995) — Redundanz-Gate n=2 Tage |
| GL-020 | H-14 | Cross-Venue-Lead-Lag-Graph (12 Nodes) | **METHODISCH INVALIDE** | Positivkontrolle 0/9 BTC→ETH-Kanten in beiden Fenstern |
| GL-021 | H-15 | Trade-Tape-Event-Grammatik | **WEITER (kapitalfrei)** | rel. CE-Lücke 3,10/3,94/2,69/5,24% (4/5), alle Surrogat-p am 1/201-Floor |

### 2.1 Die beiden WEITER — und warum sie zusammengehören

**H-16 (GL-015)** zeigt: Ein CNN erkennt auf 1s-Trade-Imbalance-Skalogrammen,
ob die Zeit vorwärts oder rückwärts läuft — mit AUC bis 0,735 gegen eine
*exakte* Bayes-Null von 0,50, symbol-repliziert, seed-stabil (Streuung ±0,01),
und IAAFT-Surrogate (lineare Struktur + Marginal erhalten) liegen sauber bei
0,50. Der Zeitpfeil sitzt also in der **nichtlinearen** Struktur des Flows.

**H-15 (GL-021)** zeigt: Ein Causal-Transformer schlägt die beste
Variable-Order-Markov-Baseline (k≤4) auf dem tokenisierten Trade-Tape um
2,7–5,2 % relative Cross-Entropy — und zwar gegen eine Null, die
Tageszeit-Saisonalität und lokale Blockstruktur **erhält** und nur die
längerreichweitige Sequenz-Grammatik zerstört. Keines von 200 Surrogaten je
Symbol erreichte die beobachtete Lücke.

Zwei verschiedene Repräsentationen (Zeit-Frequenz-Bild vs. Token-Sequenz),
zwei verschiedene Statistiken (Klassifikator-AUC vs. Scoring-Rule-CE), zwei
verschiedene Nullen (IAAFT vs. Block-Shuffle) — **eine gemeinsame Aussage:
Der Orderflow der grossen Perp-Märkte trägt nichtlineare, zeitgerichtete,
längerreichweitige sequentielle Struktur, die lineare und
Kurzgedächtnis-Modelle prinzipiell nicht sehen.** Das ist der belastbarste
Befund des gesamten Programms.

Ein wiederkehrendes Detail, das beide teilen: **BNBUSDT ist in beiden Fällen
das einzige Symbol, das den Stärke-Floor verfehlt** (H-16: AUC 0,593 < 0,60;
H-15: −0,08 % < 2 %). Mit ~9 M Events ist es 20× dünner als BTC/ETH. Die
Effektstärke folgt in beiden Hypothesen grob der Liquiditätsordnung — ein
konsistentes, unabhängig zweifach beobachtetes Muster.

### 2.2 H-17 — herausragend gemessen, ohne Verdikt

Der Venue-Fingerprint ist der stärkste reine *Messbefund* der Welle:
Balanced Accuracy 0,71–**0,995** auf nie gesehenen Symbolen, 5/5 Folds,
pooled 0,894. Das Modell erkennt die Börse am shape-normalisierten
Order-Flow, nachdem alle trivialen Tells (Tick-Size, Fee-Clustering,
Aktivitätslevel) durch Pro-Tag-Quantil-Normalisierung zerstört wurden.

Trotzdem: **kein WEITER.** Das vorregistrierte Non-Redundanz-Gate gegen
H-12 verlangt |Spearman ρ| < 0,6 an überlappenden Tagen — es gab nur **2**
(technisches Minimum: 10), weil die c17-Distanzserie konstruktionsbedingt
nur auf den Fold-Test-Tagen lebt (14.06.–04.07.) und die c12-Serie dort
wegen der Deribit-Panel-Lücken fast überall invalide ist. Ein WEITER allein
auf dem Messbefund wäre eine Torpfosten-Verschiebung gewesen.

Das ist kein Scheitern der Hypothese, sondern eine **Design-Kollision
zweier korrekt registrierter Gates**. Auflösungspfade (jeweils
Neuregistrierung nötig): (a) H-17-Wiederholung mit über alle Tage
definierter Distanzserie; (b) c12-Neulauf mit vollständigem Panel nach
Stabilisierung der Deribit-Streams.

### 2.3 H-14 — die Selbstzerstörungs-Klausel hat funktioniert

H-14 lief technisch sauber (echtes CUDA, ~226 Trainings), aber die
vorregistrierte Positivkontrolle scheiterte in **beiden** Fenstern: Keine
einzige der 9 BTC→ETH-Kanten überschritt ihre Null — obwohl dieser Lead
durch H-04/GL-006 nachweislich existiert und durch H-18 sogar auf N=100.000
bestätigt wurde. Wenn die Messmaschinerie den bekannten Effekt nicht sieht,
ist ihr Null-Befund auf allen anderen Kanten wertlos. Genau dafür war die
Kontrolle registriert.

Wahrscheinliche Ursache: Der H-04-Lead lebt auf **1–3 s**; das H-14-Target
war das Vorzeichen der **10 s**-Forward-Rendite — vermutlich jenseits der
Kohärenzzeit des Effekts. Eine Horizont-Neufassung wäre eine neue
Hypothese und ist nicht nahegelegt.

### 2.4 H-18 — was das Audit über GL-006 gelehrt hat

Bei 500-facher Surrogat-Auflösung bleiben alle 12 GL-006-Survivor
BH-signifikant, aber nur 4 halten die strenge p≤1e-3-Schranke. Entscheidend
ist das Richtungsmuster: **Alle 4 harten Zellen sind BTC→ETH oder
symmetrische Kohärenz; alle 4 ETH→BTC-Zellen driften** und tragen ab jetzt
das Etikett "auflösungsbedingt fragil". Die Auflösung hat die Asymmetrie
geschärft: BTC führt, die Gegenrichtung ist schwach.

---

## 3. Was Welle 5 methodisch gelehrt hat

**Was funktioniert hat:**
1. **Vorregistrierte Positivkontrollen** (H-14) und **Redundanz-Gates**
   (H-17) haben beide exakt das getan, wofür sie gebaut wurden — sie haben
   je ein WEITER verhindert, das sonst plausibel ausgesehen hätte.
2. **Compute-Gating** (verdict_bearing nur bei echtem CUDA + vollem N) hat
   verhindert, dass abgebrochene oder degradierte Läufe je adjudizierbar
   wurden. In keiner einzigen Session entstand ein "leise falsches" Ergebnis.
3. **Checkpoint/Resume** war die Voraussetzung dafür, dass diese Welle
   überhaupt endete: H-15 lief über 9 Sessions und ~180 h, H-16 über 4
   Sessions, H-17 über 3 — jeweils bit-konsistent zusammengesetzt, über
   Timeouts, einen Windows-Shutdown und einen Junction-Ausfall hinweg.

**Was Zeit gekostet hat (in dieser Reihenfolge):**
1. **Fehlende Checkpoints** — H-16 verbrannte 36 GPU-Stunden ersatzlos,
   bevor das System gebaut war (DEC-26/28: kein checkpoint-loser Lauf > 8 h).
2. **Datenverfügbarkeits-Claims ohne Prüfung** — der Recherche-Scout hatte
   Verzeichnis-*Existenz* für Symbol×Datum-*Abdeckung* gehalten; H-14/H-17
   verloren zwei Wochen, bis der Binance-Backfill sie entsperrte. Dieselbe
   Fehlerklasse traf später H-11 (Lebenszeit-Ordner ≠ done_days im Fenster).
3. **Angenommene statt verifizierte Runner-Parameter** — `H15_TIMEOUT_SEC`
   war hartkodiert und wurde still ignoriert; Sessions endeten wochenlang
   nach 12 h statt der angeforderten 24 h.
4. **Infrastruktur-Fragilität der Zielmaschine** — drei Reboots, ein
   RAM-Kaskaden-Ausfall, ein Junction-Verlust, ein still gewordener
   Collector-Datenstrom. Jeder Vorfall wurde durch einen Fix beantwortet
   (Mutex, Loud-Fail-Guards, Junction-Guard mit Autostart).

---

## 4. Wo das Programm jetzt steht

**21 GL-Einträge, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten.**

| Kategorie | Bestand |
|---|---|
| Kapitalfreie Mess-WEITER | **4** — H-04 (Lead-Lag), H-05b (inverses OFI), H-16 (Zeitpfeil), H-15 (Grammatik) |
| Tradability-PARK | 2 — H-04b, H-05c (beide ~15 bps unter der Wand) |
| DROP | 9 — H-01/02/03/05/06/07/08 (Wellen 1–3), H-09/H-10/H-12 (Welle 4) |
| Ohne Verdikt | 2 — H-17 (Gate nicht auswertbar), H-14 (methodisch invalide) |
| Gesperrt (data-gated) | 2 — H-11 (Manifest 8/730 Tage), H-13 (Options-Fenster zu jung) |

**Die zentrale Diagnose des Zwischenberichts gilt unverändert und ist durch
Welle 4 sogar geschärft:** Das Programm hat kein Signal-Problem, sondern ein
Horizont-Problem. Alle vier Mess-WEITER leben auf Sekunden-Skalen, wo die
~15-bps-Friktionswand jede Monetarisierung um Faktor 80–500 erschlägt. Von
den zwei registrierten Pfaden mit Arithmetik *über* der Wand ist einer
gestorben (H-10b: ohne Pointer-Tage nichts zu handeln), und der andere
(**H-11**, 25–75× über der Wand) ist data-gesperrt — mit einer
Entsperr-Bedingung, die durch einen Bybit-Deep-Backfill erfüllbar wäre.

---

## 5. Strategische Optionen — was jetzt möglich ist

### Option A · H-11 entsperren (höchster ökonomischer Hebel)
H-11 (AnEn-Vol-Regime-Forecast, 3-Tage-Horizont, CRPSS ≥ 0,05 gegen HAR-RV)
ist **der einzige verbliebene registrierte Pfad mit Friktions-Arithmetik über
der Wand**. Der Unlock-Check ergab 8 von 730 benötigten Tagen — es fehlt
bybit `publicTrade` + `rest.fundingRate` für BTC+ETH über
2024-03-27..2026-03-26. Bybit stellt öffentliche Tages-Dumps bereit
(`public.bybit.com`); das ist dieselbe Art Arbeitspaket wie der
Binance-Backfill, der H-14/H-17 entsperrt hat.
*Kosten: Harvester-Arbeit + Speicher. GPU: keine (H-11 ist CPU-billig).
A-priori: DROP erwartet (HAR-RV ist ein harter Benchmark) — aber es ist der
einzige Ort, an dem ein WEITER ökonomisch etwas öffnen würde.*

### Option B · Welle 6 registrieren (methodisch anschlussfähig)
Durch das H-15-WEITER sind erstmals die konditionalen Folge-Kandidaten
adressierbar, die der GPU-Scan 2026-07-09 dafür vorgemerkt hatte:
- **DSM-02** (Score 11/12) — Memory-Horizon-Ablation: Bis zu welcher
  Kontextlänge reicht die nachgewiesene Grammatik? Direkte Vertiefung von
  H-15, der genuin GPU-gebundenste Kandidat der Runde.
- **DSM-04** (10/12) — Cross-Symbol-Zero-Shot: Ist die Grammatik universell
  oder symbol-spezifisch? Billig (nur Evaluation, kein Retraining).
- **DSM-03** (10/12) — PatchTST auf Funding-Premium-Residuen. Ökonomisch
  der interessanteste: Funding-Capture über 8h-Fenster ist die einzige
  bekannte Krypto-Strategieklasse, deren Ertrag *pro Ereignis* nativ in der
  Grössenordnung der Kostenwand liegt. Nutzt das seit Langem ungenutzte
  m18-PatchTST-Scaffolding.
- **XV-DUAL-RETRIEVAL** (11/12) — scheiterte an fehlenden Cross-Venue-Daten
  (jetzt vorhanden) und einer Kontroll-Lücke (der Baustein dafür liegt seit
  H-15 im Repo).
- **L2-MAE-GHOST** (10/12) — der 45-Tage-L2-Floor ist seit Ende Juli erreicht.

### Option C · H-17 auflösen (billiger Restposten)
Der Messbefund ist herausragend und liegt fertig da; es fehlt nur die
Auswertbarkeit des Redundanz-Gates. Eine Neuregistrierung mit über alle Tage
definierter Distanzserie würde aus einem "ausstehend" ein echtes Verdikt
machen — ~35 h GPU, Code existiert vollständig inkl. Checkpointing.

### Option D · Tradability direkt angehen (nicht empfohlen, mit Begründung)
H-15b/H-16b wären naheliegend, sind aber **nicht impliziert** und
konzeptionell heikel: Zeitpfeil und Grammatik sind *Existenz*-Befunde, keine
Richtungsprognosen. "Der Flow ist nicht zeitreversibel" sagt nicht, ob der
Preis steigt. Eine ehrliche Tradability-Hypothese bräuchte zuerst eine
Brücke von Struktur zu gerichteter Prognose — die liefert eher DSM-03
(Funding-Residuen als natives Ziel) als eine direkte Monetarisierung von
H-15/H-16.

---

## 6. Empfehlung des Orchestrators

**Priorität 1 (Betrieb, sofort):** Collector-Autostart und Junction-Guard
einrichten. Der Collector ist ein Schutzgut; er wurde zweimal von Reboots
erwischt, und jeder Ausfalltag ist unwiederbringlich verlorene Historie.

**Priorität 2 (parallel, kostet keine GPU-Zeit):** H-11-Entsperrung als
Backfill-Auftrag an das data-harvest-Projekt geben. Selbst bei "DROP
erwartet" ist es der einzige Pfad, dessen WEITER ökonomisch relevant wäre —
und die GPU steht währenddessen frei für Welle 6.

**Priorität 3 (Forschung):** Welle 6 klein und scharf registrieren.
Vorschlag: **DSM-03** (ökonomisch anschlussfähig, nutzt ungenutztes
Scaffolding) + **DSM-02** (vertieft den stärksten Befund) + **DSM-04**
(billig, testet Universalität). Drei Hypothesen statt fünf — Welle 5 hat
gezeigt, dass GPU-Wellen an Rechenzeit und Maschinenstabilität hängen, nicht
an Ideenmangel. Bei ≥2 gemeinsam laufenden Hypothesen greift die
Kohorten-Regel: Über-Familie **vor** dem Lauf registrieren.

**Nicht verfolgen:** H-04c/H-05d/H-07b/H-08b/H-09b/H-10b (durch PARK/DROP
nicht nahegelegt), VQ-FLOW-LEX (konfundierte Null), TE/PE-Cluster-Neuauflagen
(gesperrt), direkte H-15b/H-16b-Monetarisierung ohne Brückenhypothese.

---

## 7. Offene Ops-Punkte

- **Collector-Autostart** (Schutzgut) — noch nicht eingerichtet.
- **Junction-Guard** — Skript liegt bereit (`ensure_harvest_junction.ps1`,
  auch in `run_wave5.ps1` verdrahtet); die geplante Aufgabe ist noch zu
  registrieren.
- **Envelope-Format:** Fenster nach 2026-07-16 brauchen Envelope-Parsing
  oder den Harvester-Normalizer als Leseschicht. Betrifft jede künftige
  Hypothese, die aktuelle Daten nutzt.
- **`option_tickers`-Keepalive-Defekt** — offen seit Welle 1, blockiert den
  C-33-Vorlauf.
- **Sunset-Review-Wecker** ~2026-09-11 (PROGRAM_FINAL_REPORT §8).

---

## KORREKTUR-NOTIZ 2026-08-10 (nachtraeglich angefuegt, Text oben unveraendert)

Die in §1, §2.1 und §4 verwendete Formulierung **„nichtlineare, zeitgerichtete Struktur im Orderflow"** ist durch die eigenen Payload-Daten **nicht gedeckt** und hiermit korrigiert. Die vorregistrierte Volatility-Asymmetry-Ablation von H-16 zeigt: die unsigned-|Imbalance|-Variante, die keinerlei Flussrichtung sieht, reproduziert **85–106 %** des Zeitpfeil-Ueberschusses (BTC 85 %, ETH 89 %, SOL 86 %, XRP 93 %, BNB 106 %). Der Traeger der Zeit-Irreversibilitaet ist also ueberwiegend die **Asymmetrie des Aktivitaets-/Volatilitaets-Envelopes**, nicht die Richtung des Flows.

Korrekt ist: „zeit-**asymmetrische** Struktur, ueberwiegend im Aktivitaets-Envelope". Das GL-015-Verdikt (WEITER, kapitalfrei) bleibt unberuehrt — das Gate lief auf der signed-AUC und war vollstaendig erfuellt; die Ablation war vorregistriert als nicht-urteilstragend. Ebenfalls unter Vorbehalt steht damit die in §2.1 behauptete **gemeinsame Aussage von H-15 und H-16**: ob beide dieselbe Struktur messen, ist eine offene, messbare Frage. Vollstaendige Darstellung: Nachtrag 2026-08-10 unter GL-015 in `gate_log.md` sowie DEC-30.
