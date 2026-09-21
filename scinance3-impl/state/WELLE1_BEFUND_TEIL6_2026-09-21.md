# Welle 1 - Befund Teil 6: WP-7 Zensus auf der Vereinigung (survivorship-frei), Echtlauf 2026-09-21

> Orchestrator-Adjudikation. Ergebnisordner `state/runs/wp7_20260921/`
> (Union-Range-Fingerprint `a7e4dec7...`, 6.507 Partitionen; 877
> Ueberlebende + 261 delistete Symbole; 7 NO_HISTORY; ICXUSDT als frische
> Delistung nach DEC-72 Form c). `--allow-partial` (DEC-66). Die reale
> Momentum-IC-Serie (`weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`)
> liegt als DEC-53-Artefakt bei und wurde NICHT gelesen; einzig die
> vorab fixierte B3-Differenz wurde zur Kenntnis genommen.

## Kennzahlen auf der Vereinigung (Vergleich: Ueberlebende allein, Teil 5)

| Groesse | Union | Ueberlebende allein |
|---|---|---|
| K je Woche Median (min/max) | **252** (5/719) | 171 (5/719) |
| K letzte 52 Wochen min/Median | 412/538 (unveraendert, keine Delistung dort) | 412/538 |
| SD_null Momentum je Fenster / gepoolt | **0,0411 / 0,0440** | 0,0435 / 0,0495 |
| SD_null A1-Schluessel je Fenster / gepoolt (W_eff-adj.) | 0,0411 / 0,0440 (0,0642 / 0,0687) | 0,0435 / 0,0495 |
| N_eff 52 W / 104 W | 182,3 / 97,1 | 178,8 / 101,2 |
| Dezil-Degeneration D10, Fenster 2024-09..2025-09 | 27/52 Wochen, Median-Woche positiv 1,7 % | 36/52, 0,6 % |
| Delisting-Kohorten (gelistet / delistet) | 2021 91/18, 2022 86/30, 2023 113/55, **2024 228/105**, 2025 255/51, 2026 358/9 | alle 0 |
| rho(BTC,ETH) 30-min | 0,815 | 0,815 |

**Survivorship-Verzerrung des Momentum-IC (B3-Messung, vorab fixiert):** IC_union - IC_survivors = **+0,0033 [-0,0076; +0,0132]** (271 Wochen, Wochen-Cluster-Bootstrap, Seed 53). Punktwert klein und positiv (Delistungen schwaechen das Momentum-Signal NICHT, sie staerken es leicht: Verlierer, die aus dem Ueberlebenden-Panel verschwinden, sind im Union-Panel als Verlierer sichtbar). Das CI schliesst 0 ein.

**Delisting-Hazard ist hoch:** 46 % der 2024er Listungen und 49 % der 2023er sind bereits delistet. Ein Ueberlebenden-Panel ueberschaetzt damit die Universumsgroesse historisch um bis zu die Haelfte - K-Median 171 statt 252.

## Konsequenzen (DEC-73)
1. **B3 aufgeloest:** Das survivorship-freie Universum existiert aus oeffentlichen Daten; A3 laeuft auf der VEREINIGUNG. Die Kill-Bedingung (3) aus PRD 5.3 ("Survivorship nicht rekonstruierbar UND Verzerrung >= halbe Schwelle") ist nicht ausgeloest - der erste Teil ist falsch geworden. Die halbe Schwelle (0,0071) wird vom Punktwert unterschritten, vom CI nicht; auf dem Union-Panel ist die Frage gegenstandslos.
2. **A3-Konstanten** aus der Union: SD_null 0,0411 je Fenster (Schranke 0,0870), 0,0440 gepoolt (0,0966); `IC_min = 2,4865 * 0,0411 / sqrt(52) = 0,0142` je Fenster; K in W1/W2 >= 260.
3. **A1-Konstanten** unveraendert in der Richtung (Long-Bein D1 vs. Hedge, DEC-70); D10 auch auf der Union degeneriert.
4. Register-Hygiene: 476 Announcements enthalten auch Token-Swaps und Auszahlungs-Einstellungen ohne Symbole (harmlos, kein Symbol extrahiert) und Datums-Updates ohne parsebares Delisting-Datum (dann Announcement-Datum). Keine Aenderung noetig.
