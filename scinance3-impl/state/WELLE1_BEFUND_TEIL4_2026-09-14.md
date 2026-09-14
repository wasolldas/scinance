# Welle 1 - Befund Teil 4: WP-7 Universums-Zensus (Echtlauf 2026-09-14)

> Orchestrator-Adjudikation. Ergebnisordner `state/runs/wp7_20260914/`
> (DEC-53: IC-Wochenserie, Permutations-Null je Fenster, sigma-Serie,
> Totzonen-Tabelle, Spread-Zensus, rho-Artefakt; Range-Fingerprint
> `6d4c3252...`, 5.268 Partitionen 2021-2026, 878 Symbole). Lauf unter
> `--allow-partial` (DEC-66: 69 Quellen-Luecken, dokumentiert). Die reale
> IC-Serie des Momentum-Signals liegt als Artefakt vor, wird hier aber
> NICHT gelesen oder bewertet - sie gehoert zur A3-Registrierung, nicht
> zum Zensus (Null-Zensus-Klausel DEC-58).

## Befund B1..B5 (vorab fixierte Konsequenzen, PRD 4.1)

| Befund | Messwert | Schranke | Ergebnis |
|---|---|---|---|
| B1/B2 SD_null je Fenster (W=52, letzte 51 Wochen, 1.000 Permutationen, Seed 53) | 0,0435 | 0,0870 | **B2: Klasse W testbar** |
| B1/B2 SD_null gepoolt (W=104) | 0,0495 | 0,0966 | testbar |
| K je Woche, letzte 52 Wochen | min 412 / Median 538 / max 701 | K_min 117 | erfuellt; K >= 100 erst ab 2022-05, K >= 300 ab 2025-01 |
| B3 Survivorship | Kohorten 2020-2025: 0 delistete Symbole (Panel enthaelt nur heute handelnde) | - | **B3 bestaetigt:** Survivorship-Verzerrung aus Bordmitteln nicht herstellbar |
| B4 sigma_xs (Wochen-Querschnitts-Dispersion, Median) | 9,85 % (q25 7,6 %, q75 12,6 %) | sigma_xs_min 2,09 % (f=3,51, Wand 11 bp) | nicht ausgeloest |
| sigma_LS (Dezil-Long-Short-Wochenvol, deskriptiv) | 4,77 % | - | Konstante |
| B5 PERP_SPREAD_BP je Umsatz-Dezil (EIN REST-Snapshot 2026-09-14, 874 Symbole) | D1 1,6 / D2 4,2 / D3 6,3 / D4 8,7 / D5 8,2 / D6 11,6 / D7 10,4 / D8 13,3 / D9 13,0 / D10 30,6 bp | - | als Konstante zu registrieren (DEC-67) |
| rho(BTC,ETH) 30-Minuten, 32.927 Buckets | Pearson 0,815 [0,800; 0,828], Spearman 0,797 | - | Konstante |

## Deskriptive Pflichtzeilen

**DEC-59 Totzonen-Zensus.** 46,7 % aller Symbol-Tage mit Funding (236.541 von 506.863) liegen EXAKT beim Zins-Term I. Je Dezil des rohen Wochen-Summen-Schluessels: D1 48,5 %, D2 78,5 %, D3 80,6 %, D4 65,4 %, D5 50,2 %, D6 39,7 %, D7 33,3 %, D8 28,3 %, D9 25,4 %, D10 17,1 %. Die Totzone ist nicht "die Mitte", sie ist die Masse der Verteilung; der rohe Summen-Schluessel sortiert Totzonen-Wochen nach Intervallklasse (4h-Symbole summieren doppelt so viele I-Zahlungen wie 8h-Symbole), nicht nach Praemie.

**Intervallklassen (aus funding_n je Symbol-Tag).** 480 min: 320.377 Symbol-Tage; 240 min: 163.679; 60 min: 14.620 (2,9 %); 120 min (funding_n = 12): 6.129 (1,2 %); Rest unklassifiziert (Listungs-/Luecken-Tage). instruments-info heute: 411 x 240 min, 411 x 480 min, 8 x 60 min, 40 x "0 min". Die 1h-/2h-Klassen existieren also historisch als Symbol-Tage (dynamischer Intervallwechsel bei Cap-Naehe), obwohl heute fast kein Symbol dauerhaft darin steht - genau die DEC-58-Auslesefrage, jetzt gemessen.

**Funding-Autokorrelation (Wochen-Summe, Median ueber 820 Symbole).** lag1 0,42, lag2 0,24, lag3 0,18, lag4 0,15. Die Wochen sind keine unabhaengigen Cluster; effektive Wochenzahl bei AR(1)-Naeherung (1-0,42)/(1+0,42) = 0,41 x W (52 -> 21; 104 -> 43).

**N_eff (Ledoit-Wolf).** In diesem Lauf `nan` (n_symbols_balanced = 0): der Treiber verlangt ein ueber die GESAMTE Historie balanciertes Panel, das es bei 298 Wochen und laufenden Listungen nicht gibt. Bau-Fehler, kein Datenbefund; Korrektur: N_eff auf den urteilstragenden Fenstern (letzte 52/104 Wochen, dort balanciert) und auf den 18 STRESS_ABS-Wochen im Panel (DEC-67, Wiederholung des Zensus-Schritts).

**Delisting-Kohorten.** 2020: 5 / 2021: 73 / 2022: 56 / 2023: 58 / 2024: 123 / 2025: 204 / 2026: 357 gelistete Symbole im Panel; "delistet" nur 8 in 2026 (letzte Bar-Woche vor as-of, vermutlich Luecken, keine Delistungen). Der Beifahrer bestaetigt B3: ohne externes Register ist die Hazard-Tabelle leer.

**Spread-Quelle.** Die Tickers-Inhaltsprobe des Harvest-Stroms scheitert weiterhin (Delta-Strom, Felder nur bei Aenderung); der Zensus nutzt einen REST-Snapshot. Mehrtaegige Spread-Verteilung per Last-Known-Value-Rekonstruktion bleibt Folgearbeit.

## Fensterregel-Zuordnung (PRD 9.3 Punkt 6, VOR jeder Registrierung)

- **A3 (Klasse W, Momentum/Reversal/Vol-Anomalie):** Per-Fenster-Power bei IC_prior 0,03, SD_null 0,0435, W = 52: z = 0,03 / (0,0435/sqrt(52)) = 4,97; Power einseitig alpha 0,05 > 0,99. Selbst mit einer IC-Autokorrelation wie beim Funding (W_eff = 21) bleibt z = 3,16, Power 0,93. **Zuordnung: harte Per-Fenster-Regel** (beide Fenster einzeln), DEC-52-Ausnahme greift nicht. Registrierung erlaubt, Lauf aber erst nach dem Survivorship-Fixture (B3-Konsequenz; WP-12).
- **A1 (Klasse P, Funding-Carry):** SD_null des Funding-Schluessels ist NICHT gemessen (der Zensus nutzt das Momentum-Signal). Vor der Registrierung: Permutations-Null auf dem in DEC-67 festgelegten Schluessel (Wochen-Summe von F - I), mit W_eff = 0,41 W wegen lag1 0,42. Zuordnung offen bis dahin.
- **A2, A4, A5:** unveraendert (V-5b/c, recording-first, gesperrt).

## Offen nach Teil 4
- Zensus-Schritt wiederholen nach N_eff-Korrektur und Erweiterung um den A1-Schluessel (Minuten, `-SkipFetch -AllowPartial`).
- WP-12 Delisting-Register + Survivorship-Fixture (oeffentliche Announcements-API, Kline-Verfuegbarkeit delisteter Symbole proben).
- WP-10(B) Report.
