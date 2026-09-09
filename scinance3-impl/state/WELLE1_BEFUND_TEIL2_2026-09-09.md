# Welle 1 - Befund Teil 2: WP-9, WP-10(A), WP-11 v2 (Echtlaeufe 2026-09-09)

> Orchestrator-Adjudikation der drei auf der Nutzer-Maschine mit dem
> korrigierten Code (Commit `3d9e1f0`/`8fc5e78`) erzeugten Laeufe.
> Ergebnisordner unveraendert unter `state/runs/{wp9,wp10a,wp11}_20260909/`
> (DEC-53: Cluster-Serien, Profilmatrix, Bootstrap-Fingerprints liegen bei).
> Alle Konsequenzen waren VORAB fixiert (PRD 3.0 4.2/4.3/11.3, DEC-56,
> DEC-58 Null-Zensus-Klausel, DEC-60); hier wird der eingetretene Zweig
> festgestellt. Kein Kandidat wird promoted.

## WP-9 DVOL: Befund **B1** - Historie reicht, Quellen austauschbar

| Groesse | BTC | ETH |
|---|---|---|
| F1 Tiefe REST 1D (`data/dvol_rest`) | 2021-03-24 .. 2026-09-09, 1.996 Tage | 2021-03-24 .. 2026-09-09, 1.996 Tage |
| Fingerprint Parquet | `42574a1a...` | `bbdaf089...` |
| Harvest-Partitionen (`symbol=BTC` / `symbol=ETH`) | 176 Tage (2025-08-01 .. 2026-08-13, mit Luecken) | 176 Tage |
| Ueberlappung n | 176 | 176 |
| Tagesdifferenz REST-Close minus Harvest-Letztframe | p5/p50/p95 = 0,0 / 0,0 / 0,0; SD = 0,0 | identisch |
| Block-Bootstrap (5 Tage, 1.000, Seed 53) 95 %-CI | [0,0000; 0,0000] | identisch |
| Materialitaetsband +-0,3 Vol-Punkte erreichbar | ja | ja |
| Befund | **a** (austauschbar) | **a** |

**Lesart.** Die Differenz ist auf allen 176 Tagen EXAKT null: der REST-Tageskerzen-Close ist der letzte DVOL-Tick des UTC-Tages, und der Harvester hat diesen Tick an jedem aufgezeichneten Tag erwischt. Die Bucket-Konventions-Kontrollrechnung (Bucket-Anfang vs. -Ende) ist damit gegenstandslos - eine Konventionsverschiebung haette ein tageweise wechselndes Vorzeichen erzeugt. Das entartete CI (Varianz 0) ist kein Messfehler, sondern die Aussage "gleiche Zahl aus gleicher Quelle"; F2 haette bei jeder Konvention `|b| < 0,30` und `s < 2,85` erfuellt.

**Vorab fixierte Konsequenz (PRD 4.2, Zeile B1):** Die **H-27-Klasse** (VRP auf REST-Backfill-Basis, 5,5 Jahre Tiefe) wird als eigens vorzuregistrierende Hypothesenklasse **eroeffnet** - nicht registriert. **Unveraendert bindend:** WP-9 entsperrt H-26 NICHT und erfuellt die C-33-12-Monats-Uhr NICHT; H-26 bleibt gegen `done_days` des Harvesters vorregistriert.

**Nebenbefund Abdeckung.** 176 Harvest-Tage in einem 378-Tage-Fenster: der DVOL-Strom hat Luecken (er ist im Harvester-Manifest bewusst nicht registriert, siehe Registrar-Auskunft). Fuer 3.0 ist das ohne Folge, weil der REST-Backfill als austauschbar belegt ist; fuer H-26 (`done_days`-gebunden) bleibt es die bekannte Einschraenkung.

## WP-10(A) Praemien-Kohaerenz: Stress-Frage mit Bestandsdaten NICHT beantwortbar; Ruhe-Matrix und Portfolio-Konstanten liegen vor

**Serien (Bestand, DEC-53-CSV je Serie):** Funding BTC/ETH 892/894 Tage (2024-03-01..2026-08-13), SOL/XRP/BNB je 139 Tage (ab 2026-03-26), IV-RV BTC/ETH je 165 Tage (2025-08-01..2026-07-31, lueckig), Basis-Proxy BTC/ETH 61 Tage (2026-06-16..2026-08-29, Delta-Strom, Last-Known-Value).

**STRESS_ABS (DEC-56, Fixture `b75fb7a0...`):** 30 Tage / 19 Episoden ueber 2.320 BTC-Tage (2020-05-10 .. 2026-08-19); Schwellen RV-Tag BTC 9,20 %, ETH 12,18 %. Davon fallen in die Bestandsserien: Funding BTCxETH **3 Tage**, alle anderen Paare **0 bis 1 Tag** -> ueberall `TOO_FEW`, Stress-Zelle leer.

**Das ist der Befund, kein Fehler:** 27 der 30 Stress-Tage liegen vor 2024-03 (2020-2023: COVID, Mai 2021, Terra/3AC, FTX). Ein Kohaerenzmass "im Stress" kann auf Harvest-Aera-Serien prinzipiell nicht entstehen; das PRD hatte 6-10 Episoden erwartet - real sind es 0-3.

**Ruhephase (Spearman, Cluster-Bootstrap, Bonett/Wright-SE) - deskriptiv, keine Schwelle:**

| Paar | rho | 95 %-CI | n |
|---|---:|---|---:|
| Funding BTC x ETH | 0,460 | [0,401; 0,515] | 888 |
| Funding BTC x SOL / XRP / BNB | 0,39 / 0,44 / 0,24 | alle CI > 0 | 136 |
| Funding SOL x XRP | 0,509 | [0,360; 0,624] | 138 |
| IV-RV BTC x IV-RV ETH | **0,907** | [0,859; 0,940] | 164 |
| Funding (alle 5) x IV-RV (BTC/ETH) | -0,02 .. 0,08 | alle CI enthalten 0 | 127-164 |
| Basis-Proxy x alles | -0,33 .. 0,19 | n = 33-43, CI breit | 33-60 |

Lesart (kapitalfrei): (1) Die Funding-Serien sind untereinander moderat kohaerent (0,24-0,51) - ein Querschnitts-Funding-Signal ueber 5 Symbole hat deutlich weniger als 5 unabhaengige Beine; die Ledoit-Wolf-`N_eff`-Zeile aus WP-7 wird dadurch fuer A1 zur Pflichtangabe. (2) IV-RV BTC/ETH ist EIN Faktor (0,91) - fuer H-27/A5 zaehlt BTC+ETH als ein Bein. (3) Funding und IV-RV sind in Ruhe orthogonal - die FDR-Struktur F-PREM1 vs. F-PREM2 ist in Ruhe NICHT verletzt; ueber Stress bleibt es unentschieden, also gilt weiter die vorab fixierte abhaengigkeitsrobuste Korrektur (PRD 4.3). (4) Basis-Proxy: 61 Tage sind fuer keine Aussage genug; recording-first wie A4.

**Portfolio-Nulleffekt (Konstanten fuer ein spaeteres Portfolio-Gate, KEINE Schwelle; Pool = 2.319 Tage BTC/ETH-Bar-Cache-Renditen, Block 5, Seed 53):**

| k Gleichgewichtung | E[SR] | SD | p95 | p99 |
|---:|---:|---:|---:|---:|
| 2 | 0,025 | 0,403 | 0,66 | 0,91 |
| 3 | -0,031 | 0,408 | 0,63 | 0,97 |
| 4 | -0,015 | 0,410 | 0,65 | 0,97 |
| 5 | -0,018 | 0,412 | 0,66 | 0,95 |

Selektions-Obergrenze (Bailey/Lopez de Prado, `sigma_SR` = 0,398): E[max SR] ueber K = 5/10/20/50/100 Varianten = 0,46/0,61/0,74/0,88/0,97 (empirisch) bzw. 0,48/0,63/0,76/0,91/1,01 (analytisch). Gleichgewichtung von Rauschsignalen erzeugt erwartungsgemaess KEINEN Sharpe-Anstieg mit k (SD ~ konstant 0,40); die Selektion ueber K Varianten dagegen den bekannten Order-Statistik-Anstieg. Beide Tabellen gehen als Konstanten in PRD 9.2.

**Konsequenz (DEC-62):** WP-10(A) wird als **WP-10(A2) auf nachgeladenen Tagesserien** wiederholt: Funding aus der oeffentlichen `funding/history` (V-1: vollstaendig nachladbar; `panel_1d.funding_sum` aus WP-7 oder direkter Abruf fuer die 5 Symbole), IV aus dem REST-DVOL-Backfill (durch WP-9 B1 als austauschbar belegt), RV aus dem WP-0-Bar-Cache (reicht bis 2020-05). Damit liegen 25-30 STRESS_ABS-Tage in der Ueberlappung. Der Basis-Proxy bleibt Harvest-only (Kandidat fuer Backfill: `premium-index-price-kline`, oeffentlich; zu proben, nicht zu unterstellen).

## WP-11 v2 Relaxation nach Schockstunden: Differenzprofil zerfaellt LANGSAM (Potenzgesetz-artig), Tages-Skala

3.570 reale Ereignisse (H-20-Definition, unveraendert) gegen 3.570 gematchte Pseudo-Null-Ereignisse; 1.468 Ereignistage; Superposed-Epoch-Profil in 5-Minuten-Buckets ueber 24 h; Cluster-Bootstrap je Kalendertag, 1.000 Replikate, Seed 42.

**Selektions-Bump ist messbar und wird abgezogen:** bei t = 0 liegt das reale Mittel bei 1,47 (z-Einheiten Excess) gegen 0,25 fuer die gematchte Null; Differenz 1,22 [1,13; 1,31]. Nach 5 Minuten 1,13 vs. 0,14.

**(i) Halbwertszeit des Differenzprofils (Exponentialfit) und Potenzgesetz-Exponent p, je Symbol** (Zeilenreihenfolge im Lauf-Report: Volumen / Trades / RV - die Variablenspalte fehlte im Report dieses Laufs, im Code behoben):

| Symbol | Volumen T_half (h) [KI90] | Trades T_half (h) | RV T_half (h) | R^2 exp | p Potenzgesetz |
|---|---|---|---|---|---|
| BTCUSDT | 24,6 [18,2; 34,6] | 23,6 | 30,8 | 0,30-0,37 | 0,23-0,28 |
| ETHUSDT | 22,1 [16,1; 31,1] | 22,1 | 29,8 | 0,24-0,29 | 0,25-0,32 |
| XRPUSDT | 13,6 | 7,2 | 15,7 | 0,31-0,44 | 0,32-0,40 |
| SOLUSDT | 2,5 [2,1; 2,9] (R^2 0,83) | 11,7 | 21,2 | 0,26-0,83 | 0,27-0,42 |
| BNBUSDT | 13,4 | 15,6 | 20,0 | 0,18-0,22 | 0,29-0,35 |

**Lesart (deskriptiv, kein Gate):** Der Exponentialfit passt schlecht (R^2 meist 0,2-0,4); der Potenzgesetz-Exponent liegt bei 0,25-0,4, d. h. der Ueberschuss nach einer Schockstunde zerfaellt Omori-artig langsam und ist nach 24 h noch nicht abgeklungen (konsistent mit den 23 % Nicht-Rueckkehrern aus Lauf 1). Halbwertszeiten von ~1 Tag fuer BTC/ETH bedeuten: Aktivitaets- und RV-Regime nach Schocks sind auf TAGES-Skala persistent. Das ist v1 diametral entgegengesetzt (0,07-0,2 h) und bestaetigt DEC-60: v1 hatte Rauschgedaechtnis gemessen. SOL-Volumen (2,5 h, R^2 0,83) ist die einzige Zelle mit sauberem Exponentialzerfall.

**(ii) RECOVERY_H_P90 auf STRESS_ABS: KEIN BEFUND** - 84 Ereignisse auf 27 Ereignistagen, Floor 30 (Bauvorgabe, nicht verschiebbar). Die Zelle fuellt sich nur durch neue Stress-Tage (Kanon append-only). Kein Ersatzwert.

**(iii) Aera-Vergleich (deskriptiv):** L 10,9 / 2,7 / 19,0 h; OOS1 22,1 / 23,7 / 27,1 h; OOS2 17,3 / 19,2 / 25,4 h; OTHER 2,4 / 20,9 / 28,8 h (Volumen/Trades/RV). Die KI90 der drei urteilstragenden Aeren ueberlappen fuer RV und Trades; die Volumen-Halbwertszeit in L ist kuerzer. Keine Aera-Invarianz-Aussage (kein Gate), aber auch kein Bruch, der die H-20-Definition in Frage stellt.

**Struktureller Nulleffekt v1 (Diagnostik):** Varianzverhaeltnis lambda_obs/lambda_null 0,76-1,17 - kein Selektionsartefakt der Ereignis-Extremwertauswahl.

**Was daraus folgt (DEC-63):** Konstante fuer das Kostenmodell und WP-10(B): "Nach-Schock-Regime" ist ein Tagesfenster, nicht ein Stundenfenster; die Stress/Ruhe-Trennung in WP-10(B) und die Cluster-Einheit Kalendertag sind damit angemessen (ein Schock-Tag ist EIN Cluster, nicht 24). Fuer A1 (Wochen-Summe) ist ein einzelner Schock-Tag kein unabhaengiger Beitrag zum Wochenschluessel. **Null-Zensus-Klausel (DEC-58): kein Kandidat entsteht aus diesem Befund.** X-OEKO-1 Arm (b) bliebe eine getrennt vorzuregistrierende Hypothese mit eigenem K.

## Offen nach Teil 2
- WP-7: Lauf ist an einer fehlenden Resume-Logik gescheitert (eingefrorene Partitionen aus Lauf 1 blockierten Lauf 2) - behoben, Wiederholung noetig. Tickers-Probe: `bid1Price/openInterest/fundingRate` fehlen im Delta-Strom - REST-Fallback fuer den Spread-Zensus, wie vorgesehen; Last-Known-Value-Rekonstruktion aus dem Delta-Strom ist Folgearbeit (kein Blocker).
- WP-10(B): laeuft.
- WP-10(A2): Bauauftrag (DEC-62).
- V-4(a), PRD 8.x: Nutzer.
