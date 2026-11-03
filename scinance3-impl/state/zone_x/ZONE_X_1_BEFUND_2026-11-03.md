# Zone-X-Programm 1: Befund (2026-11-03) - IK-05 Faktorzahl per Zufallsmatrixtheorie, IK-04 Momente fuer die Nullwelt

> Zone X, `rest.kline1d` ALL 2021-01-01..2024-06-30 (1.276 Renditetage), lineare USDT-Perps: 407 geladen, 266 mit >= 250 Tagen,
> 132 Tage unter Mindestquerschnitt 10 (frueh 2021). Konto-Zeilen 1 und 2 (`KONTO_ZONE_X.md`); Code `src/bybit_edge/research/zone_x/`
> (sha256 in der JSON); Ausgabe `zone_x_1_2026-11-03.json` (sha256 980b9f31...), channel_scan: 0 Befunde. **Nur zweite Momente
> und Strukturmasse (SK1); kein Mittel, kein Vorzeichen, kein Verdikt.** Stichprobenfehler der Eigenwerte und Momente nicht
> ausgewiesen (deskriptiver Zensus).

## 1. IK-05: Gibt es Faktorstruktur jenseits des Marktfaktors? [F]

| Fenster | K Symbole (balanciert) | T Tage | MP-Kante | Markt-Eigenwert (roh) | residual: Top-Eigenwerte | > Kante | >= 6,25 |
|---|---|---|---|---|---|---|---|
| voll 2021-01..2024-06 | 21 | 1.034 | 1,31 | 14,5 (69 %) | 3,05; 1,67; 1,46; 1,39 | 4 | 0 |
| sub1 2021-01..2022-02 | 11 | 271 | 1,44 | 8,3 (75 %) | 1,94; 1,58 | 2 | 0 |
| sub2 2022-03..2023-04 | 145 | 387 | 2,60 | 95,7 (66 %) | **7,75**; 4,37; 4,07; 3,74 | 9 | 1 |
| sub3 2023-05..2024-06 | 215 | 365 | 3,12 | 102,1 (51 %) | **7,92; 7,04**; 5,89; 5,3 | 11 | 2 |

Rang-Korrelation (Spearman) gleichartig (sub3 residual 9,19; 8,09; 6,29). Lesart [U]: Das balancierte Vollfenster ist mit K 21
nicht aussagekraeftig (nur 21 Perps existieren seit 2021-01 durchgehend). In den beiden juengeren Teilfenstern mit K 145..215
tragen **ein bis zwei residuale Faktoren Eigenwerte um 8**, also ueber der Schwelle 6,25, die eine 2,5-fache IC-Streuung bei
voller Ausrichtung auf die Charakteristik erklaeren koennte (Sweep IK-05; halbe Ausrichtung braeuchte 11,5). Folge fuer S-4:
eine Mehrfaktor-Null (Markt + 1..2 residuale Faktoren) ist **nicht ausgeschlossen, sondern naheliegend**; ob die Faktoren mit
der fm8-Charakteristik ausgerichtet sind, misst erst der naechste Schritt (Konto-Zeile: Projektion der Faktorladungen auf
Charakteristiken, nur Streuungsanteil). Der Marktfaktor allein erklaert 51..75 % der Varianz.

## 2. IK-04: Momente und Nullwelt-Kenngroessen [F]

- **Querschnittsstreuung je Tag** sigma_xs (SD der Tagesrenditen ueber Symbole): Niveau 3,83 % (383 bp), Median 355 bp,
  q10 234 bp, q90 564 bp; ACF Lag 1..5: 0,51 / 0,42 / 0,35 / 0,34 / 0,37 (persistente Streuungsregime). Der Sweep hatte 370 bp
  [V] angenommen; die Dezil-SESOI (3,51 x IC x sigma_xs) rechnet damit mit 383 bp: Taker (phi 0) 0,0082, Maker 0,0030.
- **Exzess-Kurtosis** der Tagesrenditen je Symbol: Median 7,1 (q10 2,9; q25 4,0; q75 11,7; q90 23,6); Marktresiduen Median
  16,5 (q10 5,4; q90 52); nach Umsatz-Terzil: liquide Terzil 6,1 (Renditen) / 10,8 (Residuen), illiquide 8,1 / 19,8.
- **Schiefe**: Tagesrenditen Median +0,18 (q10 -0,72; q90 +1,51); Marktresiduen deutlich positiv (Median +1,95, q10 +0,45).
- **Vol-Clustering** |r_M|: ACF 0,22 / 0,27 / 0,11 / 0,19 / 0,18 -> c_hat 2,92; effektive Clusterzahl eines 365-Tage-Fensters
  fuer betragsartige Statistiken ~125 (Lag 5) bzw. 72 (Lag 20). Fuer vorzeichenbasierte IC-Statistiken ist c separat zu messen.
- Fehltage im balancierten Panel: keine.

## 3. Folgen (Orchestrator, keine Entscheidung)

1. **Nullwelt (OC, IK-04):** Kurtosis 7 (Renditen) bzw. 16 (Residuen) liegt ueber den in der OC angenommenen 5..10; die
   t-Grenzen-Pflicht (DEC-104 N2 (7)) ist bestaetigt und fuer Residual-Statistiken dringlicher; schiefe Residuen (+1,9)
   bedeuten fuer einseitige Tests in Richtung "positiv" ein erhoehtes effektives alpha (Edgeworth-Vorzeichen beachten).
2. **SESOI Klasse W:** sigma_xs ist jetzt gemessen (383 bp, nicht [V]); die Persistenz je Praediktor bleibt die offene Groesse.
3. **S-4 / Mehrfaktor-Null:** naechste Konto-Zeile (K kumuliert 2): Faktorladungen der residualen Top-2-Faktoren gegen
   Groesse/Umsatz/Beta-Charakteristiken projizieren (nur Anteile, keine Renditen); danach Mehrfaktor-Null als Nuisance-Paket
   fuer IK-10/F1.
4. **Universum:** nur 21 Perps seit 2021-01 durchgehend; Zone-X-Querschnittsmessungen sollten auf 2022-03..2024-06 (K ~145..215)
   rechnen; fuer frueher sind Panel-Statistiken mit K < 50 unbrauchbar (Erreichbarkeit, DEC-104 E8 (d)).
5. Konto-Zeilen 1 und 2: Ergebnisspalte "siehe diese Datei; SK1; keine Schaetzer unter Test".
