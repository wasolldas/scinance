# Welle-2-Abschlussbericht — Scinance 2.0

**Branch:** `scinance2-wave2`
**Stand:** 2026-06-18
**Status:** DONE (Welle 2) — alle vier Welle-2-Gates entschieden (H-04, H-04b, H-05, H-06)

---

## 1. Executive Summary

Welle 2 ist abgeschlossen. Vier Gates wurden gegen die vorregistrierten Tore der Hypothesen-Registry entschieden — und Welle 2 liefert **den ersten Nicht-DROP des Programms**: H-04 WEITER auf dem 2-Symbol-Lead-Lag-Mess-Gate (BTC→ETH, kapitalfrei) *(GL-006)*. Gleichzeitig beweist die direkt anschließende, vorregistrierte Tradability-Prüfung H-04b, **warum WEITER nicht „handelbar" bedeutet**: derselbe Befund endet unter realistischer Friktion (11 bps Taker) und Latenz (300 ms) ehrlich auf PARK *(GL-009)*. H-05 (C-01 OFI-Vorzeichen) fällt als DROP mit kaskaden-wirksamer Sperre für C-09-OFI-Bein und C-14-OFI-Erbe; auf ETHUSDT erscheint dabei das **INC-02-Falsifikator-Vorzeichen signifikant invers** und löst eine pre-registrierte Folge-Hypothese H-05b aus, deren konfirmatorischer Lauf auf frische OOS-Daten wartet *(GL-007)*. H-06 (C-07 Permutation Entropy) fällt am vorgeschalteten ρ-PRE-Gate (≈20× unter Schwelle) durch und scheitert obendrein am Haupt-Gate-AUC-Lift *(GL-008)*. **Methodisches Kernergebnis der Welle 2:** die saubere Trennung zwischen **Mess-Gate** (H-04 kapitalfrei, Existenz gerichteter Information) und **Tradability-Gate** (H-04b mit verbindlicher Friction-Wand + Latenz-Haircut, Anti-Gaming-Klausel) hat den **S2-2023-Trap** (Mess-Existenz mit Handelbarkeit verwechseln) erstmals explizit und vorregistriert abgefangen. Die F-WAVE2-Über-Familien-FDR hat in 0 von 17 Stage-1-Survivorn ein Urteil verändert. Welle 3 startet damit auf stark ausgedünntem Pilot-Universum.

## 2. Die vier Gate-Verdikte

### Übersicht

| Gate | Vorregistrierte Schwelle | Messwert (worst-of) | Verfehlt um | GL-Referenz |
|---|---|---|---|---|
| **H-04 · Lead-Lag-Existenz** (KAPITALFREI) | Surrogate-p ≤ 0.05 BH-FDR in ≥ 2 Fenstern UND Lead-Symbol stabil | WCOH p=0.0050 in F0 und F1; Lead BTCUSDT in beiden Fenstern stabil; 12/22 F-LEADLAG-Survivor, p_crit F0 = 0.0697 / F1 = 0.0199 | bestanden (Mess-Existenz; Kapital-Status bleibt PARK) | *(GL-006 · 2026-06-17)* |
| **H-04b · Lead-Lag-TRADABILITY** (NICHT kapitalfrei) | Netto-Edge > 0 UND Bootstrap-p ≤ 0.05 in ≥ 2 Fenstern, latenz ≥ 300 ms, Wand ≥ 11 bps | PRIMARY F0 −14.95 bps / F1 −14.83 bps; Bootstrap p=1.0000; 0 FDR-Survivor; max Brutto-Einfang +0.19 bps | ~80× unter 15-bps-Gesamt-Wand; F0 löst PARK | *(GL-009 · 2026-06-18)* |
| **H-05 · OFI-Vorzeichen** (KAPITALFREI) | sign=+ UND p ≤ 0.05 BH-FDR UND ≥ 2-Fenster-Konsistenz UND \|corr\|≥0.05 ODER HR≥0.53 | kein Symbol/δ FDR-sig positiv in beiden Fenstern; BTC/ETH durchgängig negativ; ETHUSDT w0 δ1s signifikant INVERS (corr −0.0550, p=0.0050) | hartes Ein-Fenster-Kriterium mehrfach verletzt | *(GL-007 · 2026-06-17)* |
| **H-06 · Permutation Entropy** (KAPITALFREI) | PRE-Gate ρ ≥ 0.30 in ≥ 2 Fenstern UND Haupt-Gate p ≤ 0.05 BH-FDR + AUC-Lift ≥ +0.03 in G1, ≥ 2 Fenster | PRE-Gate: max ρ = +0.0145 (BNB w1) in 10/10 Symbol×Fenster; Haupt-Gate: bester AUC-Lift +0.0072 (XRP w1, δ15/60min) | ρ ~20× unter Schwelle; AUC-Lift ~4× zu klein; doppelt verfehlt | *(GL-008 · 2026-06-17)* |

### H-04 — Cross-Sectional Lead-Lag (Mess-Existenz)

Auf dem BTC/ETH-Perp-Paar (1s-Grid, 2 disjunkte Fenster F0/F1 zu je ~3 875 Bars, n_surrogates=200) ist gerichtete Information BTC→ETH messbar und FDR-signifikant: WCOH-Phasen-Lead **+0.9028 / +0.9076 bei p=0.0050 in beiden Fenstern**; TE BTC→ETH FDR-signifikant auf Lags 1–3 s in beiden Fenstern, Zerfall ab lag5/lag10 *(WAVE2_SUMMARY.md H-04-Tabelle)*. Lead-Symbol ist über beide Fenster **BTCUSDT** auf beiden Achsen (TE und WCOH); die Lead-Symbol-Stabilitäts-Frage bei bidirektionaler Signifikanz in F0 wurde streng nach Registry-Wortlaut „Lead-Symbol kippt" entschieden — das dominante Lead bleibt BTC, ein Kippen findet nicht statt; die strengere Lesart wurde als verdeckte Torpfosten-Verschiebung verworfen *(GL-006 §Bewertungsfrage)*. **KAPITALFREIHEIT** ist Pflichtbestandteil: WEITER bedeutet ausschließlich „gerichtete Information existiert messbar", **NICHT** „handelbar"; die signifikanten Lags liegen bei 1–3 s (tiefes HFT-Territorium); der Kapital-Status bleibt PARK; Tradability wurde explizit als neue H-04b ausgewiesen *(Registry H-04 Z.55 + GL-006 KAPITALFREIHEIT-Notiz)*.

### H-04b — Lead-Lag-TRADABILITY (Friction-Wand + Latenz-Haircut)

Erste nicht-kapitalfreie Hypothese des Programms (`capital_free=false`, dennoch historischer Backtest mit Kostenmodell auf read-only `trades` — kein Live-Order-Code, kein Geld; CLAUDE.md §4-konform). Die im H-04-Gate ausdrücklich antizipierte Folge-These wurde streng vorregistriert: Trading-Regel BTC-Signal → ETH-Position, glattgestellt nach `horizon=lag`, `lag ∈ {1,2,3} s` (H-04-Survivor-Set), Friction-Wand 11 bps Taker + 4 bps Slippage (≈ 15 bps Gesamt-Wand), Latenz-Haircut 300 ms (Einfang nur über `[t+latenz, t+lag+horizon]`), BH-FDR α=0.10 über F-LEADLAG-TRADE *(Registry H-04b + DEC-13)*. Der **urteilstragende PRIMARY-Block** (`gate_valid_assumptions=true`) liefert in beiden Fenstern F0/F1 (~9 984 + 9 619 Round-Trips) **Netto −14.95 / −14.83 bps, Bootstrap p=1.0000, 0 FDR-Survivor je Fenster und global** *(h04b/c17_c41_tradability_results.json + SUMMARY_2026-06-18.md)*. Der maximale Brutto-Einfang nach Latenz-Haircut erreicht **+0.19 bps** (F1, lag3) — **~80× unter** der 15-bps-Wand. Die Anti-Gaming-Klausel wurde respektiert: LAT100 (latenz=100 ms, `gate_valid_assumptions=false`), LAT500 (latenz=500 ms) und MAKER (`gate_valid_assumptions=false`) sind als Robustheits-/Sekundär-Spanne MIT-berichtet, dürfen aber kein WEITER tragen; alle vier Blöcke landen am PRIMARY-Punkt auf PARK; selbst der adverse-selection-vorbehaltliche MAKER-Block bleibt netto −5.95 / −5.83 bps *(GL-009 Anti-Gaming-Tabelle)*. **Reproduziert PRD §4 Z.133 a-priori** („abgegraste 30–60s-HFT-Anomalie → bleibt PARK") empirisch.

### H-05 — C-01 OFI-Vorzeichen (INC-02-Anker)

Lauf auf `trades` über 5 Symbole, 2 disjunkte Fenster, δ ∈ {1,5,15,60,300} s, eigener Aggressor-OFI (DEC-11, `m2_ofi.py` unberührt), BH-FDR α=0.10 über F-OFI (50 Varianten). **Kein einziges Symbol/δ** ist in beiden Fenstern FDR-signifikant positiv: BNBUSDT w0 δ1s/δ5s sind die einzigen positiven FDR-Survivor (corr +0.0441/+0.0204, p=0.0050), brechen aber in w1 zusammen (δ1s p=0.0597 nicht-sig, δ5s/δ15s sogar negativ); BTC/ETH zeigen über beide Fenster fast durchgängig negative Korrelationen *(WAVE2_SUMMARY.md H-05-Tabelle)*. Das harte Ein-Fenster-Kriterium ist mehrfach verletzt. **ETHUSDT w0 δ1s: corr = −0.0550, p = 0.0050 (FDR-sig, `inverse_significant=true`), Hit-Rate 0.490** — das ist die MM-Replenishment-Lesart der INC-02-Forensik (E-04 hit_sum 0.179, fälschlich invertiertes S2-Vorzeichen) read-only unabhängig reproduziert *(GL-007 §ETH-Befund)*. Konsequenz nach PRD §4 Z.131 wörtlich: DROP für C-01 + C-09-OFI-Bein + C-14-OFI-Erbe (kaskaden-wirksam). H-05b ist als eigenständige Folge-Hypothese pre-registriert (Data-Snooping-Guard: Entdeckungszelle ausgeschlossen, OOS-Anforderung; F-OFI-INV als eigene Familie; F-WAVE2 wird append-only NICHT erweitert) *(Registry H-05b + Code-Bedarf-Vermerk)*.

### H-06 — C-07 Permutation Entropy

Lauf auf `kline_1min` über 5 Symbole, 2 disjunkte Fenster, m=4/τ=1 vorab fixiert (DEC-12), `WINDOW_MAX_BARS=43 200` (30 Tage, Stationaritäts-Cap), n_surrogates=200, BH-FDR α=0.10 über F-ENTROPY (40 Varianten). Das **PRE-Gate ρ ≥ 0.30** ist in **allen 10 Symbol×Fenster-Paaren** verfehlt: ρ ∈ [−0.0059, +0.0145], max +0.0145 bei BNB w1 — **~20× unter** der Schwelle, mehrere ρ sogar negativ *(WAVE2_SUMMARY.md §H-06 PRE-Gate)*. Das löst hartes Ein-Fenster-DROP (Registry H-06 wörtlich „ρ < 0.30 in EINEM Fenster → DROP, kein Voll-Lauf"). Unabhängig davon ist auch das Haupt-Gate doppelt verfehlt: die einzigen 2 FDR-Survivor (XRP w1 δ15min/δ60min, p=0.0050) liefern AUC-Lift **+0.0072 / +0.0072 — ~4× unter** der +0.03-Schwelle, und beide liegen im selben Fenster w1 (≥ 2-Fenster-Forderung verletzt) *(GL-008)*.

## 3. F-WAVE2 zweistufige BH-FDR — Über-Familien-Korrektur

Stage 1 (BH-FDR α=0.10 innerhalb jeder Familie): F-LEADLAG **12/22** Survivor (p_crit F0 = 0.0697 / F1 = 0.0199), F-OFI **3/50** Survivor (p_crit = 0.0050), F-ENTROPY **2/40** Survivor (p_crit = 0.0050). Stage 2 (BH-FDR α=0.10 über die Vereinigung aller 17 Stage-1-Survivor-p, p_crit = 0.0697): **17/17 überleben** *(WAVE2_SUMMARY.md §Driver-Präsenz + Stage-1/Stage-2-Bilanz)*. **0 Survivor in Stage 2 verloren** — die Über-Familien-Korrektur kippt **kein einziges Urteil**. PRE-Gate (H-06) und `inverse_significant` (H-05) sind separat ausgewiesen und zählen explizit NICHT in F-WAVE2 — beides sind Strukturkriterien, keine p-Wert-Tests. F-LEADLAG-TRADE (H-04b) läuft als eigene Familie außerhalb F-WAVE2 (F-WAVE2 ist append-only abgeschlossen, *(Registry H-04b §FDR-Familie + Welle-2-Nachtrag Z.154)*).

## 4. Was empirisch erledigt ist

- **C-01 OFI-Vorzeichen-These (Aggression-Folge, positiv-konsistent über Symbole) widerlegt**; **C-09-OFI-Bein und C-14-OFI-Erbe kaskaden-wirksam DROP** *(GL-007 + PRD §4 Z.131)*. Der inverse ETH-Befund bestätigt INC-02/E-04/S2-2023 als methodischen Anker.
- **C-07 Permutation-Entropy-These (PE-Drop → 15-min-Vol-Cluster, ρ ≥ 0.3)** auf `kline_1min` widerlegt; m=4/τ=1 vorab fixiert (keine Embedding-Parameter-Suche möglich) *(GL-008)*.
- **C-17/C-41 Lead-Lag auf 1–3 s mit 300-ms-Latenz und 11-bps-Wand nicht handelbar:** das Mess-Signal existiert (H-04), aber der einfangbare Brutto-Move (+0.19 bps max) frisst die Wand ~80× nicht *(GL-009)*.
- **PRD §4 Z.133-A-priori empirisch reproduziert:** die „abgegraste 30–60s-HFT-Anomalie → PARK"-Lesart ist nicht mehr nur Konstruktions-Skepsis, sondern Messbefund — H-04 misst Existenz, H-04b widerlegt Handelbarkeit auf demselben Signal.

## 5. Welle-2-Werkzeug-Erbe (für Welle 3)

Kategorisiert, aus `wave2_state.md` CHANGELOG + `decisions.md` (DEC-10..13) aufgesammelt:

- **F-WAVE2 zweistufige BH-FDR-Aggregation** (`scinance2-impl/handoff_local/aggregate_wave2_fdr.py`, 551 LoC, W2-WP4) — Muster und wiederverwendbarer Baustein für künftige Welle-3-Über-Familien.
- **Anti-Gaming-Klausel als Modul-Pattern**: `gate_valid_assumptions`-Flag direkt im Modul (`src/bybit_edge/research/c17_c41_tradability/`) erzwingt maschinell, dass nur urteilstragende Annahmen-Punkte ein WEITER auslösen können — wiederverwendbar für jede künftige Tradability-Hypothese.
- **Mess-Gate-Modul-Konvention** (`research/c17_c41_lead_lag/`, `capital_free=true`) als **Bibliotheks-Import** für künftige Tradability-Module (siehe `research/c17_c41_tradability/`-Pattern: Resampling/Fenster/Lag-Gerüst nicht dupliziert, sondern importiert) *(Registry H-04b Code-Bedarf-Vermerk)*.
- **Data-Snooping-Guard-Muster** (H-05b): Entdeckungszelle ausgeschlossen, OOS bevorzugt, eigene FDR-Familie (F-OFI-INV), F-WAVE2 append-only abgeschlossen — formale Vorlage für jede post-hoc-Hypothese.
- **PS-5.1-Runner-Härtung**: BOM + ASCII + handle-cache + BelowNormal + `--db-copy` default + try/except je Schritt + dry-run via `HANDOFF_DRY_RUN` (`run_wave2.{ps1,sh}`, `run_h04b.{ps1,sh}`) — übernimmt sich für Welle 3.
- **Vier neue DEC-Entscheidungen (DEC-10..13)** als Architektur-Audit-Trail, alle reversibel mit dokumentiertem Rückbauweg *(decisions.md)*.
- **Bestehender Welle-1-Werkzeugkasten** (DuckDB-`--db-copy`, Epoch-ms-Filter, Progress-Logging, `WINDOW_MAX_TICKS`-Pattern aus DEC-09) bleibt durchgängig im Einsatz.

## 6. Welle-3-Implikationen (Kurzform — Vollsequenzierung folgt im Survey)

Die ausführliche Welle-3-Sequenzierung übernimmt der parallele Agent in `state/wave3_survey.md`. Hier nur die Leitplanken:

- **H-05b** bleibt im Wartezustand (OOS-Daten reifen, ~5–10 Tage ab 2026-06-18 → voraussichtlich ~23.–28.06.2026); kein Code, kein Lauf *(Registry H-05b §Out-of-Sample-Anforderung + wave2_state.md W2-H05b)*.
- **C-36 Recording weiterlaufen lassen** — sammelt Vorlauf für die gated Welle-2/3-Pilots (C-33 IV ≥ 12 Mon., C-27/C-28/C-29 Kaskaden, C-39, ggf. CS-06) *(WAVE1_FINAL_REPORT §6, weiterhin gültig)*.
- **Welle 3 wird klein:** nach Welle 1 (3 DROP) + Welle 2 (3 DROP + 1 PARK + 1 kapitalfreies WEITER) ist das Pilot-Universum stark ausgedünnt; viele PRD-§4-Pilots bleiben durch H-02-Kaskade blockiert *(WAVE1_FINAL_REPORT §6 Tabelle)*.
- **Erste Welle-3-Kandidaten** (aus PRD §4 + dem zu schreibenden Survey): C-06 NICHT-triviale-MR (neue Hypothese erforderlich), C-20 MOMENT (Datenbedarf Neulistings), CS-07 Footprint nur via C-16-Pfad — sämtlich Hypothesen-Arbeit zuerst.
- Vor jeder Welle-3-Hypothese: Pre-Registration, hartes Ein-Fenster-Kriterium, FDR-Familie wörtlich VOR Lauf-Start (Welle-1/2-Disziplin 7/7 Gates gegen vorregistrierte Tore — kein Nachverhandeln).
- **Keine Welle-1/2-DROP-Reaktivierung** ohne neue H-0xb mit eigener Registry-Zeile *(Registry-Disziplin §2 + §8 — Torpfosten-Verschiebung verboten)*.

## 7. Welle-2-Kosten-Ehrlichkeit

Beziffert (alle Zahlen aus `wave2_state.md` CHANGELOG + Lauf-Verzeichnissen):

- **~6 200 LoC Welle-2-Produktion**: `research/c17_c41_lead_lag/` ~1 410 LoC (W2-WP1), `research/c01_ofi_sign/` ~1 118 LoC (W2-WP2), `research/c07_pe/` ~1 500 LoC (W2-WP3), `research/c17_c41_tradability/` ~1 317 LoC (H-04b-BUILD), `aggregate_wave2_fdr.py` 551 LoC (W2-WP4) + Runner.
- **+132 neue Tests** (Suite 776 → 908 grün, davon 24+33+39+13+23 in den fünf Welle-2-Build-WPs; 0 Modul-Bugs zur Lauf-Zeit der Gate-Auswertungen) *(wave2_state.md W2-WP1..H-04b-BUILD)*.
- **Vier architekturelle DEC-Entscheidungen** (DEC-10 Lead-Lag-Methoden, DEC-11 eigener OFI-Schätzer, DEC-12 PE-Parameter + 43 200-Bar-Cap, DEC-13 H-04b-Tradability-Regel), alle reversibel.
- **Roh-Daten committet**: `handoff_local/results/wave2_20260617_090618/` (H-04/H-05/H-06 T3-Lauf) + `handoff_local/results/h04b_20260618_091937/` (vier H-04b-Blöcke).
- **Nutzer-Replay-Stunden**: 1× `run_wave2.ps1` (~2–4 h T3, sequenziell H-04→H-05→H-06→Aggregation) + 1× `run_h04b.ps1` (~3 min T2, vier Blöcke à 39–44 s).

Diese Kosten kaufen: ein methodisch sauberes Mess-WEITER (H-04), die ehrliche Tradability-Falsifikation desselben Signals (H-04b), zwei zusätzliche Falsifikationen (H-05, H-06) inklusive INC-02-Reproduktion auf ETH, und eine formal pre-registrierte Folge-Hypothese (H-05b) mit Data-Snooping-Guard.

## 8. Empfehlung für Welle 3

- **Welle-3-Survey schreiben lassen** (paralleler Agent → `state/wave3_survey.md`): Pilot-Universum gegen Welle-1+2-DROP/PARK-Kaskaden bewerten, F-WAVE3-Familien vorab benennen, Pre-Registration-Reihenfolge sequenzieren.
- **Klein anfangen**: nach den Welle-1/2-DROPs ist das Pilot-Universum aus PRD §4 dünn; Welle 3 sollte ≤ 2 neue Alpha-Tests parallel laufen (Welle-1-Parallelitäts-Deckel PRD §8.1 gilt unverändert) und C-36-gated Pilots NICHT verfrüht starten.
- **H-05b NICHT vorzeitig starten** — OOS-Datenreifung abwarten (~23.–28.06.2026). Bei vorzeitigem Lauf droht Zirkularität trotz Entdeckungszellen-Ausschluss.
- **C-36 Recording weiterlaufen lassen** als Vorlauf-Asset; Sunset-Review (3 Monate, PRD §9) als Anti-Data-Lake-Bremse beibehalten.
- **Vor jeder Welle-3-Hypothese: Pre-Registration in der Registry**, mit hartem Ein-Fenster-Kriterium und FDR-Familie wörtlich VOR Lauf-Start. Die Welle-1/2-Disziplin (7/7 Gates gegen vorregistrierte Tore, kein Torpfosten-Verschieben) ist das eigentliche Schutzgut.
- **Keine Reaktivierung von Welle-1/2-DROP-Pilots** ohne neue H-0xb (analog H-02b/H-05b/H-04b). Eine Schwellen-Anpassung am bestehenden Eintrag bleibt verboten *(Registry-Disziplin §2/§8.3)*.
- **Mess-Gate vs. Tradability-Gate Trennung** als feste Architektur-Konvention übernehmen: Jede künftige Hypothese, die Edge oder Handelbarkeit berührt, läuft als eigenes nicht-kapitalfreies Folge-Gate (H-0xb-Muster) mit Anti-Gaming-Klausel und MIT-berichteten Robustheits-Spannen — niemals als zirkuläre Nachbestätigung eines Mess-WEITER.

---

*Quellen durchgängig: `state/gate_log.md` (GL-006/007/008/009), `state/hypothesis_registry.md` (H-04/H-04b/H-05/H-05b/H-06 + DEC-09/DEC-12-Nachträge + Welle-2-FDR-Nachtrag Z.154), `state/decisions.md` (DEC-10/DEC-11/DEC-12/DEC-13), `state/wave2_state.md` (Phasen-Log + CHANGELOG W2-INIT..W2-H04b-GATE), `state/wave2_survey.md`, `state/WAVE1_FINAL_REPORT.md` (§6 Welle-2-Implikationen + Pilot-Universum), `FINAL_PRD.md` (§4 Welle 2+ Z.130/131/133, §8 Multiple-Testing-Disziplin, §8.5 hartes Ein-Fenster-Kriterium), `handoff_local/results/wave2_20260617_090618/WAVE2_SUMMARY.md` (F-WAVE2 zweistufige BH-FDR-Tabellen, H-05 inverse_significant, H-06 PRE-Gate), `handoff_local/results/wave2_20260617_090618/{h04,h05,h06}/*_results.{json,md}`, `handoff_local/results/h04b_20260618_091937/SUMMARY_2026-06-18.md` + `h04b/c17_c41_tradability_results.{json,md}` + `h04b_{lat100,lat500,maker}/c17_c41_tradability_results.json` (Anti-Gaming-Robustheits-Spanne).*
