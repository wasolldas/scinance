# Welle 1 - Gesamtbilanz (Stand 2026-09-21)

> Orchestrator-Fassung. Quellen: Befund Teil 1-6, DEC-59..DEC-73, Laeufe
> unter `state/runs/`. Zweck: Konstantentabelle fuer PRD 9.2,
> Fensterregel-Zuordnung je Kandidat, Registrierungsreihenfolge.

## 1. Was Welle 1 beantwortet hat

| Paket | Frage | Antwort |
|---|---|---|
| Vorfragen V-1..V-6 | Vorbedingungen A1/A2/A4 | Funding-Historie vollstaendig oeffentlich; Anker I ist Totzonen-Wert; 4h/8h-Heterogenitaet; A4 recording-first; A2 wartet auf V-5b/c |
| WP-7 (+v2, Union) | Klasse W testbar? | **B2 ja.** SD_null 0,0411 je Fenster (Schranke 0,0870); K 252 Median, >= 260 in W1/W2; B3 durch WP-12b aufgeloest; B4 nicht ausgeloest; B5 Spread-Dezile gemessen |
| WP-9 | DVOL-Historie und Quellen | **B1.** 1.996 Tage ab 2021-03-24, REST = Harvester exakt; H-27-Klasse eroeffnet |
| WP-10(A2) | Praemien-Kohaerenz im Stress | Funding-Paare 0,6-0,7 im Stress vs. 0,2-0,35 in Ruhe, nicht durch Selektion erklaert; IV-RV BTC/ETH ein Faktor; Funding x IV-RV in Ruhe 0, BTC im Stress -0,4 |
| WP-10(B) | Maker-Fill und adverse Selektion | p_fill(60 s) 0,06 FIFO / 0,35 pro-rata; adv_sel 0,6-0,7 bp FIFO -> Maker-Vorteil traegt in Ruhe; Stress-Zelle leer |
| WP-11 v2 | Relaxation nach Schockstunden | Tages-Skala, Potenzgesetz (p 0,25-0,4); ein Schock-Tag = ein Cluster |
| WP-12/12b | Survivorship | 268 delistete Symbole, 261 mit Historie; Verzerrung +0,003 [-0,008; +0,013]; Hazard 2023/24-Kohorten ~50 % |

## 2. Konstanten fuer PRD 9.2 (gemessen, mit Fingerprint; keine Schwellen)

| Konstante | Wert | Quelle |
|---|---|---|
| SD_null(IC_t) Momentum, Union, W=52 / W=104 | 0,0411 / 0,0440 | wp7_20260921 |
| SD_null A1-Schluessel (F-I) W=52 / W=104, W_eff-adj. | 0,0411 / 0,0440; 0,0642 / 0,0687 | wp7_20260921 |
| K je Woche (Union) Median; letzte 52 Wochen min/Median | 252; 412/538 | wp7_20260921 |
| N_eff Ledoit-Wolf 52 W / 104 W | 182 / 97 | wp7_20260921 |
| sigma_xs Wochen-Median; sigma_LS | 9,85 %; 4,77 % | wp7_20260914 |
| Totzonen-Anteil Symbol-Tage; Klumpen-Anteil Wochen | 46,7 %; ~12-16 % | wp7_20260914/21 |
| Funding-Wochen-Autokorrelation lag1..4 | 0,42 / 0,24 / 0,18 / 0,15 -> W_eff = 0,41 W | wp7_20260914 |
| Intervallklassen-Wechsel je Symbol (nie/1/2-5/>5) | 580 / 140 / 143 / 15 | wp7_20260916 |
| PERP_SPREAD_BP je Umsatz-Dezil (ein Snapshot) | 1,6 / 4,2 / 6,3 / 8,7 / 8,2 / 11,6 / 10,4 / 13,3 / 13,0 / 30,6 | wp7_20260914 |
| rho(BTC,ETH) 30-min Pearson / Spearman | 0,815 / 0,797 | wp7 |
| DVOL-Tiefe; REST-Harvester-Differenz | 2021-03-24 ff.; 0,0 | wp9_20260909 |
| Funding-Kohaerenz Ruhe / Stress (Median ueber Paare) | ~0,25 / ~0,63 | wp10a2_20260910 |
| IV-RV BTC x ETH | 0,88 beide Regime | wp10a2 |
| Portfolio-Null Gleichgewichtung k=2..5: SD / p95 / p99 | 0,40 / 0,65 / 0,95 | wp10a |
| Selektions-Decke E[max SR] K=5/10/20/50/100 | 0,46 / 0,61 / 0,74 / 0,88 / 0,97 | wp10a |
| p_fill(10 s / 60 s) FIFO BTC, ETH; pro-rata | 0,043/0,063, 0,045/0,057; 0,28/0,37, 0,27/0,32 | wp10b_20260916 |
| adv_sel FIFO / pro-rata (Mittel, Ruhe) | 0,6-0,7 bp / 0,3-0,4 bp | wp10b_20260916 |
| Nach-Schock-Halbwertszeit BTC/ETH (Differenzprofil) | 22-31 h, Potenzgesetz p 0,25-0,32 | wp11_20260909 |
| Delisting-Hazard je Kohorte (delistet/gelistet) | 2021 20 %, 2022 35 %, 2023 49 %, 2024 46 %, 2025 20 % | wp7_20260921 |

## 3. Fensterregel-Zuordnung je Kandidat (PRD 9.3 Punkt 6, vor der Registrierung)

| Kandidat | Klasse | Per-Fenster-Power (IC_prior 0,03 bzw. Praemie) | Zuordnung | Status |
|---|---|---|---|---|
| A3-M/R/V | W | > 0,99 (SE 0,0057); > 0,95 unter W_eff 0,41 W | **C.10 hart** | **registriert H-28..H-30** (H-30 bedingt) |
| A1 Long-Bein vs. Hedge | P | offen (Praemien-Erwartung erst nach erweiterter V-1) | C.10 hart erwartet (W_eff 21/Fenster) | gesperrt bis V-1 erweitert |
| A2 EXP-CLOCK | E | - | - | gesperrt (V-5b/c) |
| A4 Perp/Future | P | - | - | recording-first (>= 12 Monate) |
| A5 Skew / H-27 VRP | P | - | - | gesperrt (E.6) / eroeffnet |

## 4. Naechste Schritte
1. Opus-Review des Registry-Eintrags H-28..H-30; danach WP-13 (A3-Treiber, Sonnet) mit DEC-39-Trio, Beta-Fixture, Bounce-Fixture, Persistenz-Null, T7-Artefakten.
2. Vol-Drag-Feasibility-Zeile fuer H-30 als Zensus-Nachtrag (Verhaeltnis sigma^2/2-Term zu IC_prior je Vol-Dezil).
3. Erweiterte V-1 (Orchestrator-Recherche) -> A1-Registrierung.
4. STRESS_REL-Abdeckung der A3-Fenster aus `wp10_stress_canon/stress_rel.json` nachtragen (Fixture liegt nur lokal).
