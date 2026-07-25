# Forschungs-Zwischenbericht Scinance 2.0 — Stand 2026-07-25

> Erstellt vom Orchestrator (Fable-5-Synthese) aus drei parallelen Bestands-Scans
> (Gate-Log GL-001..015 · Registry/DEC-15..28 · Ideen-/Ressourcen-Inventar).
> Zweck: Was ist gedroppt, was geparkt, was aussichtsreich, was kommt als
> Naechstes — plus Strategie-Skizze. Kein Gate-Dokument; bindend bleiben
> ausschliesslich Registry + gate_log.

---

## 1. Programm in fuenf Saetzen

15 Gate-Verdikte, 0 Torpfosten-Verschiebungen, 0 handelbare Kanten. Sieben
Hypothesen-Klassen sind empirisch oder strukturell tot (Vol-Anker, S1-S5-Erbe,
CFAR, OFI-positiv, Entropie-Vol, Cross-Sectional-MR x2). Drei kapitalfreie
Mess-WEITER stehen: H-04 (BTC fuehrt ETH, 1-3 s — durch das GL-014-Audit auf
einen harten BTC->ETH-Kern praezisiert), H-05b (inverses OFI, SOL-lokal,
schwach) und H-16 (**Zeit-Irreversibilitaet im Orderflow, AUC bis 0,735,
symbol-repliziert — das staerkste und sauberste Ergebnis des Programms**).
Die Friktions-Wand (~15 bps) hat bislang JEDE Tradability-Pruefung getoetet
(Einfang +0,03..+0,19 bps = 80-500x unter der Wand) — sie ist der eigentliche
Endgegner, nicht die Signalsuche. Der wichtigste Bestandsbefund dieser
Synthese: **Welle 4 (H-09/H-10/H-12) ist fertig gebaut, auditiert, gefixt,
vorregistriert — und wurde nie ausgefuehrt**; ihr Lauf kostet CPU-Minuten.

---

## 2. Bestandsaufnahme

### 2.1 GEDROPPT (endgueltig, kein Nachschieben nahegelegt)

| Klasse | Verdikte | Kern-Scheitergrund |
|---|---|---|
| Vol-Prognose-Anker + gesamter Vol-Stack (C-10/11/12/34/35) | H-02/GL-001 | 0/5 Symbole Repro, 0/36 Features FDR-sig; Reaktivierung NUR via neue H-02b mit bit-genauer Original-Feature-Spec |
| Scinance-1.0-Strategieportfolio (S1-S5) | H-01/GL-004 | RAW-Edge −4,48 bps — negativ schon VOR Gebuehren, in allen 5 Symbolen |
| CFAR/Radar-Mikrostruktur-Timing | H-03/GL-005 | Surrogat-ununterscheidbar (p 0,80-1,00), Edge ~250x unter der Wand |
| OFI mit positivem Vorzeichen (inkl. C-09/C-14-Erben) | H-05/GL-007 | 0 Zellen konsistent; einziger robuster Effekt ist INVERS |
| Entropie-basierte Vol-Prognose | H-06/GL-008 | PRE-Gate ~20x unter der Korrelations-Schwelle, in ALLEN Fenstern |
| Cross-Sectional-MR auf dem 5-Symbol-Panel (beide Definitionen) | H-07/GL-012 + H-08/GL-013 | strukturell (max|z|=2,0<2,5 bei N=5) bzw. 0 FDR-Survivor + Survivorship-Guard; "C-06-Raum erschoepft" |

### 2.2 GEPARKT (real, aber unterhalb der Friktions-Wand)

- **H-04b** (Lead-Lag-Tradability, GL-009): Netto −14,95/−14,83 bps; auch
  LAT100/LAT500/MAKER negativ. Kein Wiedervorlage-Trigger; H-04c nicht nahegelegt.
- **H-05c** (OFI-Fade-Tradability, GL-011): Netto −14,90..−14,97 bps bei
  nachweislich realem Signal (Surrogat-p 0,005). H-05d nicht nahegelegt.
- **C-42-Vol-Anker-Reaktivierung** (H-02b-Pfad): nur mit verifizierter
  Original-Feature-Spez — Aussenarbeit, kein aktiver Slot.
- Einordnung: Beide PARKs sind *ehrliche* Ergebnisse — die Signale existieren,
  sind aber auf Sekunden-Horizonten um Groessenordnungen zu klein fuer die Wand.

### 2.3 WEITER-Bestand (kapitalfreie Messbefunde — das Fundament)

1. **H-16 / GL-015 — Zeitpfeil im Orderflow (staerkstes Ergebnis):** CNN
   erkennt Zeitrichtung mit AUC 0,73 (BTC/ETH), 0,66/0,64 (SOL/XRP); IAAFT-
   Surrogate exakt bei 0,50; Leak-Kontrolle bestanden; 4/5-Quorum exakt
   erfuellt. Interpretation: Der Flow traegt massive NICHTLINEARE, zeitlich
   gerichtete Struktur, die lineare Modelle prinzipiell nicht sehen.
   Effektstaerke folgt der Liquiditaetsordnung.
2. **H-04 / GL-006 + GL-014-Audit — BTC fuehrt ETH (1-3 s):** Bei 500x
   Aufloesung bleiben 12/12 Zellen BH-signifikant; der harte Kern (p<1e-5)
   ist ausschliesslich BTC->ETH + Kohaerenz; ALLE ETH->BTC-Zellen sind
   "aufloesungsbedingt fragil" (bindende Zitierpflicht fuer Folgearbeit).
3. **H-05b / GL-010 — inverses OFI (schwaechster WEITER):** nur SOL, nur
   delta 1s/5s, Magnitude ~0,01-0,05 — symbol-/lag-lokal, kein universelles
   Gesetz.

### 2.4 LAUFEND / IN ROTATION (Welle 5)

| H | Stand | Naechster Meilenstein |
|---|---|---|
| H-14 (Cross-Venue-Lead-Lag-Graph, Score 12/12) | entsperrt 2026-07-25, laeuft als Erstes im Wochenend-Slot | ~2-3 GPU-Tage -> GL-016-Kandidat |
| H-17 (Venue-Fingerprint, WEITER-nah laut Kritiker) | entsperrt, Checkpoints nachgeruestet | ~35h+ nach H-14 |
| H-15 (Event-Grammatik) | laeuft; **erster Messpunkt (BTC Fold 0): Gap 2,47% >= 2%-Schwelle UND weit ueber Surrogat-p95** — vorsichtig positiv gegen das A-priori "DROP erwartet" | ~1,5-2 Wochen Nacht-Tranchen |

---

## 3. Die zentrale strategische Diagnose

**Das Programm hat kein Signal-Problem — es hat ein Horizont-Problem.** Alle
gefundenen realen Effekte leben auf Sekunden-Skalen, wo die 15-bps-Wand jede
Monetarisierung um Faktor 80-500 erschlaegt. Die Registry enthaelt genau ZWEI
dokumentierte Groessenordnungs-UMKEHRUNGEN (Arithmetik UEBER der Wand statt
darunter), und beide liegen auf laengeren Horizonten:

- **H-11 (AnEn-Vol-Forecast, 3-Tage-Horizont): ~25-75x UEBER der Wand** —
  der oekonomisch wertvollste registrierte Pfad des Programms. GESPERRT,
  aber: die Entsperr-Bedingung (730 Tage bybit publicTrade+fundingRate) ist
  durch die verifizierte Bybit-Tiefe (2020/21..heute, lueckenlos) sehr
  wahrscheinlich ERFUELLT — **der Check wurde schlicht nie ausgefuehrt.**
- **H-10b-Arithmetik (Pointer-Day-Vorlauf 1-5 Tage): ~13-55x UEBER der Wand**
  (H-10 selbst ist kapitalfrei und nie gelaufen).

Ehrliche Gegenrechnung: Beide tragen "DROP erwartet"-A-prioris (HAR ist ein
harter Benchmark; Pointer-Days haben Power-Risiko). Aber die Payoff-Asymmetrie
ist einzigartig: Ueberall sonst waere selbst ein WEITER oekonomisch tot —
hier NICHT. Das diktiert die Priorisierung.

---

## 4. Sofort einloesbare Quick Wins (CPU, Minuten bis Sekunden)

1. **`run_wave4` ausfuehren** — H-09/H-10/H-12 in einem Lauf (Kohorte +
   F-XDOM1 automatisch). Kosten: CPU-Minuten. Ertrag: bis zu 3 neue Verdikte.
   Pikant: H-12 (Cross-Exchange-Fragmentierung) war bis zum Binance/Deribit-
   Backfill vom 24.07. faktisch genauso data-gated wie H-14/H-17 — seine
   "sofort testbar"-Zeile ist erst seit gestern wahr. Loader-Kompatibilitaet
   verifiziert (c12 liest wie c14 nur $.price/$.p — beide Dialekte liefern das).
2. **H-11-Unlock-Check** (`--check-unlock-only`) — Sekunden. Bei Erfolg wird
   der wertvollste gesperrte Pfad des Programms lauffaehig (selbst CPU-billig!).
3. **H-13-Unlock-Check** — Sekunden. Das markprice.options-Fenster ist von 3
   auf ~5,5 Wochen gewachsen; Kriterium (ii) ist kalendarisch erfuellbar.
   (Achtung: der Trades-Backfill hat H-13 NICHT entsperrt — separater Stream.)
4. *(optional, T3-CPU-Overnight)* GL-010-Breadth-Audit (n_surr 200->100k auf
   F-OFI-INV) — vom GPU-Scan explizit als CPU-Aufgabe empfohlen, nie gemacht.

## 5. Strategie-Skizze (empfohlene Reihenfolge)

**Phase A — "Ernte einfahren" (diese Woche, parallel zur GPU-Rotation):**
Wave-4-Lauf + beide Unlock-Checks. Bis zu 5 Klaerungen fuer ~0 Kosten. Die
GPU bleibt dabei ungestoert bei H-14->H-17->H-15.

**Phase B — Welle 5 abschliessen (laufende + naechste 2 Wochen):**
GL-016 (H-14), GL-017 (H-17), GL-018 (H-15) adjudizieren. Danach ist der
GPU-Scan-Shortlist-Zyklus komplett abgearbeitet.

**Phase C — der Horizont-Pivot (bedingt):**
- **Wenn H-11 entsperrt:** H-11-Lauf priorisieren (CPU!). Ein WEITER dort
  waere der erste Befund des Programms mit Monetarisierungs-Arithmetik ueber
  der Wand -> H-11b wuerde zur ersten echten Tradability-Chance.
- **Wenn H-15 WEITER:** DSM-02 (Memory-Horizon) + DSM-04 (Zero-Shot-
  Universalitaet) sind die vorgemerkten, konditionalen Folge-Kandidaten.
- **Wenn H-14 WEITER:** Cross-Venue-Graph + BTC-Fuehrung (GL-014-Kern)
  ergaeben zusammen ein koherentes Bild der Informationsarchitektur — dann
  lohnt eine Welle 6 um Cross-Venue-Dynamik auf laengeren Skalen.

**Welle-6-Kandidaten-Wartesaal** (aus dem GPU-Scan-Friedhof, 12 PARKs — nach
dem sortiert, was neue Daten/Assets inzwischen heilen):
| Kandidat | Was ihn jetzt heilt |
|---|---|
| XV-DUAL-RETRIEVAL (11/12) | Binance-Tape existiert jetzt; die fehlende Within-Hour-Kontrolle liegt als hour_block_shuffle-Baustein in c15 bereit |
| DSM-03 Funding-Premium via m18-PatchTST (10/12) | reines Cap-Opfer; m18 ist fertiges, ungenutztes Scaffolding; Funding-Historie tief |
| L2-MAE-GHOST (10/12) | 45-Tage-L2-Floor ist seit ~Ende Juli erreicht (forward-only seit 16.06.) |
| N-SVI-RESID / SURF-EVENT (10/8) | Options-Surface-Fenster waechst kalendarisch; SURF-EVENTs 300-Event-Floor braucht noch Wochen |
| BitMEX-2014er-Tape + Binance bookDepth ab 2023 | unerschlossene Multi-Zyklen-/L2-Historie — Kandidaten-Scouting lohnt erst nach Coverage-Check gegen done_days |

**Explizit NICHT verfolgen:** H-04c/H-05d/H-07b/H-08b (durch PARK/DROP nicht
nahegelegt), VQ-FLOW-LEX (konfundierte Null, nicht heilbar), TE/PE-Cluster-
Neuauflagen (gesperrt; nur byte-identische Re-Audits zulaessig), H-16b
(Zeitpfeil ist keine Richtungsprognose — Tradability-Pfad unklar; erst
denken, dann registrieren).

## 6. Prozess-Lehren (bindend fuer die naechste Scouting-Runde)

1. **Daten-Claims gegen done_days pruefen, nie gegen Verzeichnis-Existenz**
   (der Welle-5-Inventurfehler kostete zwei Hypothesen 2 Wochen).
2. **Kein checkpoint-loser Lauf >8h** (36 verbrannte GPU-Stunden bei H-16).
3. **BH-Rand-Zellen-Problem** bei kuenftigen Aufloesungs-Kriterien antizipieren
   (die grenzdefinierende Zelle kann per Konstruktion nie >x SE Abstand haben).
4. Runner-Timeouts gegen GEMESSENE Laufzeiten dimensionieren; False-OK-Bugs
   sind im PS-5.1-Bestand systematisch (14 Runner betroffen gewesen).

## 7. Offene Ops-Punkte (nicht Forschung, aber faellig)

- `option_tickers`-Keepalive-Defekt (blockiert C-33-Vorlauf seit Welle 1).
- Envelope-Live-Format: Fenster nach 2026-07-16 brauchen Envelope-Parsing
  oder den Harvester-Normalizer als Leseschicht (Entscheid faellig, sobald
  eine Hypothese Daten nach Mitte Juli braucht).
- Sunset-Review-Wecker ~2026-09-11 (PROGRAM_FINAL_REPORT §8).
