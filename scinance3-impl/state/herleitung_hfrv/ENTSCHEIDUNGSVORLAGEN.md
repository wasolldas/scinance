> **Stand nach Review (Orchestrator, 2026-10-21):** `REVIEW_HFRV.md` = ZUSTIMMUNG MIT AUFLAGEN A-1..A-7, in DEC-98 Nachtrag 5
> eingearbeitet. Lesarten dieser Vorlage, die davon abweichen, sind durch den DEC-Text ersetzt: (a) Befund als Spanne
> "Langfristvarianz HF/cc 0,87..1,31, in keiner Lesart materiell frueher" (A-1); (b) Dauer mit dem Prior aus DEC-98 N2
> (7,14; Band 3,2..10,5 -> 614..6.750 Tage), Fensterlaenge nicht vorab fixierbar (A-2); (c) L = 12 mit n 365 (A-3);
> (d) Bilanz-Zeilen mit SE_null 1,39 gekennzeichnet (A-4); (e) H-33 ist eine eigene Vorlage mit Siegel-Preis, kein
> Ergebnis von Option 3 (A-7); (f) V-5a: woechentlich spaetestens ab 2016-03-18 (A-6). `a2_census.json` vor dem Commit
> auf Daten <= 2026-06-30 gekuerzt (A-5).

# Entscheidungsvorlagen zur HF-RV-Nuisance (Option 3, DEC-98) - fuer den Orchestrator

> ENTWURF, Stand 2026-10-21. Vorlagen, keine Entscheidungen: registrieren und beschliessen darf nur der Orchestrator.
> Grundlage: `NUISANCE_HFRV.md` / `nuisance_hfrv.json` (Kuerzel `[nj:]`), `A2_EREIGNISZENSUS.md` / `a2_census.json`
> (`[aj:]`). Kein Praemienmittel, kein Vorzeichen und kein DVOL-Mittel wurde berechnet, gespeichert oder gesehen; alle
> Zahlen sind Nuisance-Groessen der Vorperiode (Etikett in beiden JSON-Dateien).

## (a) Ist Option 3 tragfaehig?

**Befund: nein - die Hochfrequenz-RV ist kein Hebel.**

| Groesse (BTC S1) | cc (H-27) | HF (iii) 5-min sub | Bilanz-Annahme HF | Quelle |
|---|---:|---:|---:|---|
| SD der Praemie (VP) | 18,60 | 18,62 | 15,1 (UNBELEGT) | [nj:stats.BTC.*.S1.sd] |
| c nach Regel P-3 | 28,17 | 31,46 | 28,2 | [nj:stats.BTC.*.S1.c_bind] |
| Konsens-c (gemessen) | 18,58 | 24,36 | 18,6 | [nj:stats.BTC.*.S1.c_consensus_tapered_acf] |
| Tage je Fenster C10 (P-1, pi-2 9,47), Regel-c | 671,8 | 751,7 | 442,9 | [nj:power.BTC_S1.*.c_rule_P3\|se_null_h27.durations.pi2_central] |
| dto. Konsens-c | 443,0 | 582,1 | 292,4 | dto. `c_consensus_measured` |
| voll (C10 P-1), Regel-c / Konsens-c | 2030-04-04 / 2029-01-03 | 2030-09-11 / 2029-10-08 | 2029-01-01 / 2028-03-07 | dto. |
| L = 12, n 335: Fenster-Power / Regime P-1 | 0,544 / GL012 | 0,506 / GL012 | 0,73 bei n 365 / GL012 (Review B-1) | [nj:...windows_L12.pi2_central.335] |

- **SD-Gewinn:** keiner in S1 (BTC +0,1 %; ETH +8,8 %); in S3 -9 %, aber dort steigt c (Konsens 14,9 -> 23,7).
- **Mechanismus (gemessen):** das Messrauschen von RV_cc gegen HF ist real (SD 8,1 VP), aber positiv mit dem RV-Niveau
  korreliert; die HF-Praemie traegt dafuer zusaetzliche Streuung des RV-Niveaus (Intraday-Umkehr, Lag-1-ACF der
  5-min-Renditen -0,047), netto bleibt Var(P) gleich. Zugleich verschwindet die negative Autokorrelation um Lag 30, die
  bei cc den Varianzfaktor druckte -> c steigt.
- **Folge fuer die Bilanz (Vorschlag fuer einen DEC-Nachtrag):** PROGRAMM_BILANZ 2.3 (Zeilen "HF-RV (UNBELEGT)"), 2.7
  ("VRP HF-RV + Konsens-c 292,4"), 2.8 (Hebel "HF-Statistik -34 % / -57 %") und Teil C Option 3 sind durch die Messung
  ersetzt: HF-Statistik +12 % (Regel-c) bzw. +31 % (Konsens-c) Tage gegen cc mit gleichem c-Schaetzer.
- **Was bleibt:** Die Dauer einer VRP-Hypothese auf blinden Fenstern haengt weiter am Prior (Faktor ~4 ueber das Band)
  und an der c-Regel; die Optionen 1 (recording-first mit fixierten Entsperrdaten) und 5 der Bilanz sind davon
  unberuehrt. Kosten von Option 3 bisher: nur Rechenzeit; kein blindes Fenster verbraucht.

## (b) Welche RV-Variante vorab fixieren?

- **Empfehlung nach der vorab fixierten Regel R-10 (vor jeder Zahl, nicht nach SD, Richtung neutral):** (iii) 5-min
  subsample-gemittelt (5 Phasen, Gitter mit Randstuecken, Tagesanker close 23:59 des Vortags). Kriterien:
  Mikrostruktur-Signatur rms(RV)/rms(RV_30min) 1,046 (BTC) / 1,041 (ETH) im Band 0,95..1,05 ((ii) faellt mit 1,063 /
  1,067 heraus); kappa 2,05 (niedrigster Wert mit 1-min); SD 18,62; Phasenmittelung macht die Statistik unabhaengig vom
  Gitterbeginn; Definition aus `bybit/rest.kline1m` fuer Vorperiode und kuenftige Fenster identisch (1-min-close =
  Panel-Tagesschluss an 1.164/1.165 bzw. 1.165/1.165 Tagen).
- **Einordnung:** Wird ueberhaupt eine VRP-Hypothese auf den blinden Fenstern formuliert, ist (iii) gegenueber der schon
  vor H-27 fixierten cc-Definition in jeder c-Lesart laenger (Richtung Strenge, wenn gewaehlt). Ein Wechsel auf
  (v) 30-min wegen der kleinsten SD (17,69) waere eine Auswahl nach Kenntnis der Nuisance (Richtung Testbarkeit) und
  bringt gegen cc nur -1,5 % Tage (Regel-c). Neutral bleibt: die RV-Definition vor der Hypothese einmal festlegen und
  alle gerechneten Varianten in K zaehlen (Abschnitt c).
- **Voraussetzung fuer jede HF-Fassung:** Vollstaendigkeit von `bybit/rest.kline1m` BTCUSDT (und ETHUSDT als Bericht) ab
  2026-07-01 - nur Zeilen je Tag/Luecken pruefen (DEC-96 E3); in diesem Auftrag nicht geprueft.

## (c) Text-Entwurf: neue VRP-Hypothese (H-33-Kandidat)

> **H-33 (Kandidat, nicht registriert) - VRP auf blinden Fenstern mit vorab fixierter Fensterlaenge.**
> **Etikett (Pflicht):** "beschlossen nach Kenntnis der H-27-Feasibility (GL-034) und der HF-RV-Nuisance 2026-10-21;
> Richtung Testbarkeit (Fensterlaenge ueber 12 Monate, von DEC-96 E2 fuer H-27 ausgeschlossen); neue Hypothese mit
> eigenem K (DEC-58 E2); kein Outcome der Fenster gesehen."
> **Statistik:** S1 = Fenstermittel von IV(t) - RV_fwd30(t) minus J, IV(t) = DVOL-close 23:00 UTC, RV_fwd30 aus
> [Variante: (iii) 5-min subsample-gemittelt aus `bybit/rest.kline1m` | alternativ cc wie H-27 - Wahl vor der
> Registrierung, siehe (b)], Konstante 365, Bein BTC (ETH Bericht), Richtung einseitig wie H-27.
> **J:** fuer (iii) UNBELEGT (HF-Nullwelt mit Intraday-Struktur noetig; Niveau-Verzerrung 1,055), fuer cc +2,09 VP
> (H-27-Nullwelt, modellabhaengig, REVIEW B-3).
> **Fenster:** zwei disjunkte, gleich lange Fenster W5/W6 ab 2026-07-01 zu n Kalendertagen (IV-Tage), RV-Ziel 30 Tage
> nach Fensterende; n VORAB aus dieser Nuisance (C10 unter P-1, c nach Regel P-3, SE = max(Nuisance, SE_null H-27)):
>
> | Prior-Lesart | Variante | n je Fenster | W5 | W6 | Blind-Siegel bis (Ende RV-Ziel W6) |
> |---|---|---:|---|---|---|
> | pi-2 zentral 9,47 VP (Auftrag; laut DEC-98 N2 nicht gestuetzt) | (iii) | 752 | 2026-07-01..2028-07-21 | 2028-07-22..2030-08-12 | 2030-09-11 |
> | pi-2 7,14 VP (DEC-98 N2, Band 3,2..10,5; Richtung Strenge) | (iii) | 1.323 | 2026-07-01..2030-02-12 | 2030-02-13..2033-09-27 | 2033-10-27 |
> | pi-2 zentral 9,47 VP | cc | 672 | 2026-07-01..2028-05-02 | 2028-05-03..2030-03-05 | 2030-04-04 |
> | pi-2 7,14 VP | cc | 1.182 | 2026-07-01..2029-09-24 | 2029-09-25..2032-12-19 | 2033-01-18 |
>
> [nj:power.BTC_S1.<v>.c_rule_P3|se_null_h27.durations.<prior>; Daten [abg.] = 2026-07-01 + n - 1 usw.]
> **Selektions-K:** als Zahl vor der Registrierung fixieren. Gerechnet wurden hier 6 RV-Varianten x 3 Einheiten x 3
> Beine; zaehlen alle (K 54), steigt z auf 2,306 und n auf 1.204 Tage ((iii), 9,47; 2033-03-05); K <= 11 laesst n
> unveraendert, K 12 / 18 gibt 764 / 883 Tage [nj:power.selection_K_report]. Vorschlag zur Wahl (Orchestrator):
> K = Zahl der Varianten, die in der Registrierung urteilstragend oder als Bericht mit Gate stehen; die hier nur
> beschreibend gerechneten Varianten mit Etikett C.17 fuehren.
> **Zuordnung:** einmal vor der Registrierung mit `power_p1.assign_regime` und Doppelausweis A3-Praxis (bei n 752: C10
> P-1 genau an der Grenze, A3-Praxis braucht 1.347 Tage -> "zugelassen nur durch DEC-94").
> **Blind-Siegel:** DEC-96 E3 gilt bis zum Ende des RV-Ziels von W6 fuer BTC/ETH-Vol und DVOL; Kollision mit
> Klasse-W/A1-Fenstern ab 2026-07-01 (DEC-98 E1 (b)) vorher entscheiden.
> **Offen vor Registrierung:** Vorlauf (Positivkontrolle mit HF-Nullwelt), J, Lauf-SE-Regel = Power-SE-Regel (REVIEW B-7:
> Bootstrap-Blocklaenge >= 90 Tage oder c-Regel), Prior-Beleg (Volltext, RV-Definition der Literatur), K.

Hinweis zur Tragweite: In keiner Zeile liegt das fruehste Urteil vor 2030; mit dem nach DEC-98 Nachtrag 2 gestuetzten
Prior nicht vor 2033. Dass ein Kandidat mit Fenstern ueber 12 Monate auf diesem Weg "testbar" wird, folgt allein aus
der Fensterlaenge, nicht aus der HF-RV.

## (d) Was NICHT folgt

- Kein Verdikt ueber die Volatilitaets-Risikopraemie; keine Aussage ueber ihr Niveau oder Vorzeichen (nicht berechnet,
  nicht gesehen). GL-034 / DEC-97 bleiben unveraendert; H-26 bleibt gesperrt.
- Keine Registrierung, keine Regelaenderung: der Konsens-c ist nicht als Regel uebernommen (waere P-3-Aenderung, eigene
  DEC, Richtung Testbarkeit); DEC-96 E2 (L in {6, 9, 12} fuer H-27) unberuehrt.
- Keine Aussage, dass Hochfrequenzdaten fuer andere Klassen nutzlos sind: fuer A2 (sigma30) sind die 1-min-Kerzen die
  Datengrundlage (`A2_EREIGNISZENSUS.md` Abschnitt 7).
- Keine Aussage ueber W1/W2 oder die blinden Fenster: gerechnet wurde nur auf 2021-03-24..2024-05-31.
- A2 bleibt durch V-5b gesperrt; der Zensus liefert nur Kalender und Zeitlage.

## (e) Offene / UNBELEGTE Punkte

| Punkt | Status | blockiert / wirkt auf |
|---|---|---|
| Jensen-J der HF-Welt | UNBELEGT | jede HF-S1/S2-Statistik; Prior-Lesart 6,07 vs 9,99 VP |
| SE_null der HF-Welt | UNBELEGT (kleiner als 4,17), nicht neu kalibriert | ohne Wirkung, solange die Nuisance bindet |
| ETH-Prior | UNBELEGT | ETH-Bein, Tagesmittel, Konjunktion |
| Konsens-c als P-3-Aenderung | nicht beschlossen; je Variante gemessen | Faktor ~0,77 auf die Tage |
| RV-Definition (Frequenz) der Literatur-Stichprobe | UNBELEGT | Prior jeder HF-Statistik |
| Prior selbst | DEC-98 N2: Band 3,2..10,5 VP, pi-2 7,14 | Faktor ~1,8 gegen 9,47 |
| `bybit/rest.kline1m` ab 2026-07-01 | Vollstaendigkeit ungeprueft | Definitionsgleichheit kuenftiger Fenster |
| Options-Deliveries im Settlement-Strom ab 2026-08-01 | fehlen im Extrakt (81 Tage), Rueckfrage an Data-Harvest | A2-Kalender im Blindbereich (nur Vollstaendigkeit) |
| sigma30 (A2) | offene Vorlage, nicht gerechnet | A2-Feasibility |
| Normal-Naeherung bei Exzess-Kurtosis ~2,6 der HF-Praemie | Merkposten | Power-Zeile, Positivkontrolle |
| Underlying Bybit-Perp gegen Deribit-Index | nicht gemessen | Bericht im Lauf |
