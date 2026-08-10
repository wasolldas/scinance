# Welle-6-Synthese — Kandidatenauswahl

> Orchestrator-Synthese aus drei parallelen Recherche-Lanes (2026-08-10).
> Eingaben: Lane A (Horizont-Pivot), Lane B (Aufbau auf H-15/H-16),
> Lane C (neu verifizierte Datenquellen). 14 Kandidaten, davon 6 von den
> Lanes selbst begründet aussortiert. Grundlage: `DATA_INVENTORY_2026-08-10.md`.
> Dieses Dokument wählt aus und begründet — die bindende Pre-Registration
> folgt separat in `hypothesis_registry.md`.

## 1. Die drei Befunde, die die Auswahl bestimmt haben

**(a) Der GL-015-Korrekturbefund (Lane B, vom Orchestrator nachgerechnet).**
Die unsigned-|Imbalance|-Ablation reproduziert 85–106 % des H-16-Zeitpfeils.
Der Träger ist überwiegend die Asymmetrie des Aktivitäts-Envelopes, nicht
die Flussrichtung (Nachtrag 2026-08-10 zu GL-015, DEC-30). **Folge für die
Auswahl:** Kandidaten, die schwer auf H-16 als Beleg *gerichteter* Struktur
aufbauen, verlieren ihre Prämisse. Die teuren GPU-Vertiefungen von Lane B
werden dadurch weniger dringlich, nicht dringlicher.

**(b) Die Ökonomie-Arithmetik (Lane A + C, unabhängig gerechnet).**
Zum ersten Mal im Programm gibt es Kandidaten, deren Zielgröße ÜBER der
~15-bps-Friktionswand liegt: TAIL-AFTERMATH 25–50 bps (**1,7–3,3×**),
L2-DAILY-TILT 25–30 bps (**1,7–2×**). Zum Vergleich: H-04b lag bei 0,19 bps
= 80× DARUNTER. Beide sind nur messbar, weil die Historie Jahre statt
Monate umfasst.

**(c) Die Budget-Realität.** Lane B allein schlägt 420–470 GPU-h vor
(≈ 30-Tage-Welle). Welle 5 lieferte ~300 GPU-h in drei Wochen — inklusive
drei Reboots, einer RAM-Kaskade, einem Junction-Verlust und ~36 verbrannten
Stunden vor dem Checkpoint-Einbau. Die Lane-A- und Lane-C-Spitzenkandidaten
sind dagegen **CPU-only** (Stunden, nicht Tage).

## 2. Auswahl: vier Hypothesen, CPU-first

Alle vier greifen das im Welle-5-Abschlussbericht diagnostizierte
**Horizont-Problem** an oder bringen eine im Programm noch nie genutzte
Informationsklasse. Alle laufen **einzeln nacheinander** — damit greift die
Kohorten-Regel nicht und es ist keine Über-Familie zu registrieren
(DEC-24-Präzedenz aus Welle 5).

| # | Arbeitstitel | Herkunft | Kern | Rechenlast | Ökonomie vs. Wand |
|---|---|---|---|---|---|
| 1 | **DRIFT** | Lane A (K-D) | Ist die Tape-Struktur über 5 Jahre stationär? 3 Mikrostruktur-Deskriptoren gegen Kalenderzeit, konditioniert auf Vol/Aktivität | CPU, ~2 h | n/a (Meta) |
| 2 | **TAIL-AFTERMATH** | Lane A (K-A) | Reversions-signierte Nachbewegung 2–24 h nach 3,5-σ-Stundenereignissen | CPU, 2–4 h | **1,7–3,3× darüber** |
| 3 | **LIQ-TAG** | Lane C (K3) | Trägt das exogene Liquidations-Label Information, die ein gematchter gewöhnlicher Trade nicht trägt? | CPU, Stunden | ~0,2–0,5× (unter) |
| 4 | **L2-TILT** | Lane C (K4) | Tagesmittel der Near-Touch-Buchneigung → 1-Tages-Rendite | CPU nach L2-Ein-Pass | **1,7–2× darüber** |

**Warum diese vier:**
- **DRIFT zuerst**, weil es die billigste Messung ist und über die Auswertung
  aller anderen entscheidet: Ist die Struktur nicht stationär, muss jede
  Mehrjahres-Auswertung regime-gesplittet werden. Beide Zweige sind
  informativ (H-18-Muster).
- **TAIL-AFTERMATH** ist der ökonomisch stärkste Kandidat der Runde bei
  geringsten Kosten. Sein Effekt existiert auf 100 Tagen prinzipiell nicht
  messbar (dort ~10 Ereignisse/Symbol — exakt die N=0-Falle von H-10/GL-017).
- **LIQ-TAG** bringt als einziger eine **exogene Flussmarkierung**. Alle
  bisherigen Flussgrößen des Programms (OFI, Imbalance, Grammatik) waren aus
  dem Tape inferiert. Billigster Lauf der Welle, methodisch unabhängig.
- **L2-TILT** ist der zweite Kandidat über der Wand und der einzige, der die
  neu entdeckte L2-Tiefe nutzt — allerdings mit dem größten Vorbehalt (s. §4).

## 3. Vorleistungen (vor jeder Registrierung)

**WP-0 · Geteilter Bar-Cache (CPU, eine Nacht).** Einmaliger Tick-Durchlauf
über ~4·10⁹ Trades → 1-min-Bars (Last-Price, High/Low, Buy-/Sell-Volumen,
Trade-Count) + die tick-auflösungsbedürftigen Tages-Deskriptoren. Ohne ihn
liest jede Hypothese 0,5–1 TB Roh-JSONL einzeln; mit ihm läuft die ganze
Welle in Stunden. Ergebnis hash-gepinnt, read-only.

**WP-1 · L2-Pre-Flight-Zensus (CPU, ein Nachmittag) — harte Vorbedingung für L2-TILT.**
Record-Typ-Verteilung, Bytes/Tag, Sequenzbrüche, tatsächliche Level-Zahl je
Symbol/Regime. Lane C zeigt per Byte-Arithmetik, dass reine 500-Level-Snapshots
~17 TB allein für BTC bedeuten würden (unplausibel) — die wahrscheinlichere
Lesart ist Snapshot+Delta mit einem Tiefen-Bruch 500→1000. **Fällt der Zensus
gegen die Delta-Lesart aus, wird L2-TILT nicht registriert.** Kein Byte
Extraktion vor diesem Zensus.

**Gemeinsames Fensterschema (Lane A, arithmetisch gegen die Inventur geschlossen):**

| Fenster | Zeitraum | Tage | Rolle |
|---|---|---:|---|
| L (Kalibrierung) | 2021-06-29 .. 2022-12-31 | 551 | danach eingefroren |
| OOS-1 | 2023-01-01 .. 2024-06-30 | 547 | urteilstragend |
| OOS-2 | 2024-07-01 .. 2025-12-31 | 549 | urteilstragend |

551+547+549+222 = 1869 = SOL/BNB-Tagesanzahl; +461 = 2330 = BTC. Alle drei
Fenster liegen **vor** dem Format-Bruch 2026-07-16, sind also durchgehend
flache Backfill-Form. Keine Hypothese H-01..H-18 hat je Daten vor 2026-03-27
gesehen — es sind echte Pre-Discovery-Fenster.

## 4. Bekannte Schwächen der Auswahl (ehrlich)

- **L2-TILT:** Bybit-`orderbook.500` deckt bei BTC nur **±5 bps** Buchtiefe ab
  (500 Preis-Level, nicht 500 bps). Dass deren Tagesmittel eine 1-Tages-Rendite
  prognostiziert, widerspricht der üblichen Zerfallsstruktur — Lane C selbst
  erwartet DROP. Er bleibt drin, weil er der zweite Kandidat über der Wand ist
  und der Lauf nach dem Ein-Pass trivial; er fällt raus, wenn WP-1 negativ ist.
- **LIQ-TAG:** nur 43 Tage Liquidations-Historie, ~21 Tagesblöcke je Fenster.
  Die urteilstragende Statistik ist deshalb die stratifizierte Permutation, der
  Tagesblock-Bootstrap nur Robustheitsbericht. Ein Lauf im Q4 wäre materiell
  besser als sofort — die Fenster wachsen mit dem Kalender.
- **TAIL-AFTERMATH:** Per-Symbol-Zellen sind unterpowert; urteilstragend ist die
  gepoolte, tages-geclusterte Statistik. Der N-Floor (100 Ereignistage/Fenster)
  ist der harte Abbruch — nicht absenkbar (GL-017-Lehre).
- **DRIFT:** über-powert statt unter-powert (ρ=0,30 bei N≈1800 entspricht z≈12,7).
  Deshalb magnitudengetriebenes Gate statt p-Gate — die spiegelbildliche
  H-07-Lehre.

## 5. Vertagt (Welle 7 / bedingt) — mit Begründung, nicht stillschweigend

| Kandidat | Lane | Warum vertagt |
|---|---|---|
| **REACH-LADDER** (τ½ in Sekunden + H-15/H-16-Redundanz) | B | Wissenschaftlich der eleganteste Entwurf der Runde, aber 135–150 GPU-h. Die Redundanzfrage ist durch den GL-015-Korrekturbefund bereits teilweise beantwortet (H-16 ≈ Envelope-Asymmetrie, H-15 mit Seiten-Kanal ⇒ vermutlich verschieden). Wird registrierbar, wenn eine CPU-Hypothese Tages-Skalen-Struktur belegt und die Reichweitenfrage dadurch entscheidungsrelevant wird. |
| **DAY-BRIDGE** (eingefrorener H-15-Encoder → 24-h-Richtung, **nicht kapitalfrei**) | B | Der einzige direkte Tradability-Versuch und der bestbewertete Einzelkandidat (12/12) — aber A-priori 15–20 %, ~100 GPU-h, und Lane B selbst sequenziert ihn hinter zwei Diagnostiken. Ehrlicher Weg: erst zeigen, dass auf Tagesskala überhaupt Struktur existiert (TAIL-AFTERMATH, L2-TILT), dann die Brücke registrieren. |
| **CARRIER** (welcher Token-Kanal trägt H-15?) | B | 90–100 GPU-h für eine Deflationsprüfung. Wertvoll, aber nachrangig gegenüber Kandidaten mit Ökonomie über der Wand. |
| **REGIME-TRANSFER** (2021→2025 Zero-Shot) | B | 100–110 GPU-h; inhaltlich teilweise von DRIFT (CPU, ~2 h) vorweggenommen. Nach DRIFT neu bewerten. |
| **SWEEP-PRE** (V-01 wiederbelebt) | C | Datenseitig wirklich entsperrt (4 → ~270 Testtage, Faktor 65). Aber Execution-Timing-Wert, kein gerichtetes Alpha — unter der Wand. Nach dem L2-Ein-Pass billig nachholbar. |
| **BOOK-ARROW** (Zeitpfeil im Buch) | C | 1,5–3 GPU-Tage, ökonomisch stumm; und nach dem GL-015-Befund ist mit demselben Envelope-Deflationsmuster zu rechnen. |
| **IMPACT-PERSISTENZ** | A | CPU-billig und methodisch elegant (Positivkontrolle nach GL-020-Lehre), aber 0,3–1,3× der Wand und Abgrenzungsrisiko zum erschöpften OFI-Cluster. Reservekandidat, falls einer der vier ausfällt. |
| **CLOCK-COUPLING** | A | Braucht einen extern belegten Settlement-Fahrplan über 5 Jahre als Vorbedingung; Auflösungsgrenze liegt exakt auf der Wand. |
| **XV-TAPE-RETRIEVAL** | C | Strukturell hinter der H-17-Auflösung eingesperrt — würde GL-019 exakt wiederholen. |
| **H-17b** | — | Bereits vom Nutzer in die „What-else"-Phase verschoben. |

**Endgültig gestrichen** (von den Lanes mit Rechnung erlegt): Wochenzyklus
(Power: auflösbar erst ab 113 bps), Illiquidität→Wochenrendite (keine Null
konstruierbar, die Illiquidität von Volatilität trennt), BDEPTH-DIR (IC_min
0,27), V-03 Dual-Venue-Buchgeometrie (Binance ist bookDepth-Prozentbuckets,
kein Preislevel-Buch — strukturell, nicht T-gebunden), MEM-TAU und
ARROW-HOURS (von REACH-LADDER dominiert bzw. sequenz-abhängig).

## 6. Operative Reihenfolge

1. **WP-0** Bar-Cache (eine CPU-Nacht) · **WP-1** L2-Zensus (ein Nachmittag)
2. **Pre-Registration** der vier Hypothesen in `hypothesis_registry.md`
   (Gates, Schwellen, Fenster, FDR-Familien, A-priori, Feasibility-Check,
   Selbstkill-/Abgrenzungsklauseln) — H-19..H-22
3. Läufe einzeln in der Reihenfolge **DRIFT → TAIL-AFTERMATH → LIQ-TAG → L2-TILT**
4. Adjudikation je Lauf durch den gate-auditor gegen die Registry

**Warum diese Welle anders aussieht als Welle 5:** Sie ist CPU-first. Welle 5
war GPU-gebunden und hing an einer Maschine, die drei Reboots, eine
RAM-Kaskade und einen Junction-Verlust hatte. Diese Welle läuft in Stunden
statt Wochen, blockiert die GPU nicht und liefert zwei Kandidaten mit
Zielgrößen über der Friktionswand — die erste Welle des Programms, für die
das gilt.
