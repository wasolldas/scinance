# A2-Vorarbeit Teil A: Placebo-Design bei taeglichen Verfaellen, Ereignisgroesse, Zeitlage (V-5c-Datenteil)

> **Fassung 2 (2026-10-29) nach REVIEW_A2_VORARBEIT.md: Auflagen A-1..A-6 eingearbeitet.** Zahlen der
> Fassung 1 unveraendert (Rundung vereinheitlicht: SE zwei Stellen, MDE80 eine Stelle, W1 als Hauptwert, W2 in
> Klammern, wo die Rundung abweicht); Neues am Ende unter "Aenderungen gegen Fassung 1".
> ENTWURF der Herleitung (Gate-Design/Nuisance), Stand 2026-10-29. Nichts hier ist registriert oder beschlossen;
> entscheiden und registrieren darf nur der Orchestrator. **Kein Verdikt.** A2 bleibt durch V-5b (Effektgroesse)
> gesperrt (PRD 5.2 Vorbedingung, DEC-98 Nachtrag 5 (3)).
> **Etikett:** "A2-Vorarbeit (EXP-CLOCK): Placebo-Design und sigma30-Nuisance. Renditen nur 2021-03-24..2024-05-31
> (1-min-Kerzen), Kalender/OI (gelieferte Kontrakte) nur bis 2026-06-30; nur Streuungs-, Korrelations-,
> Autokorrelations-, Varianzfaktor- und Zaehlgroessen. Kein Mittel und kein Vorzeichen irgendeiner Verfallstag-Rendite
> (r_pre, r_post, Differenz Ereignis minus Placebo) wird ausgegeben oder gespeichert; keine Preisfelder der
> Settlements gelesen. Kein Verdikt, nichts registriert." (`label` in `a2_vorarbeit.json`)
> **Ergebnisblindheit / Waechter:** Settlement-Rohpartitionen nur bis 2026-06-30 geoeffnet (spaetere nie), daraus nur
> die Felder `type`, `instrument_name`, `timestamp`, `position` per Arrow-Regex-Extraktion mit Positivliste
> (`FieldGuard`, raised bei `index_price`/`mark_price`/`profit_loss` und jedem Feld ausserhalb der Liste; Selbsttest
> beim Import); die Payload wird nie JSON-dekodiert. Jedes Ausgabe-Dict passiert `h27_common.no_mean` und
> `a2v_common.guard_keys` (mean/avg/mittel/sign/vorzeichen/effect/delta/drift ...). Keine Siegeldatei, kein
> Harvest-Client, nichts unter `data/harvest`, nichts nachgeladen oder entfernt gelistet. Fassung 2: zusaetzlich
> `guard_keys_loc` (median/q50/loc/center/diff/contrast/minus nur auf einer dokumentierten Positivliste; keine
> unzentrierten Betrags-Quantile unter Differenz-Reihen) und Datums-Assert auf `start_ms` vor jeder Preisspalte (R-12, R-13).
> **C.17 (Fassung 2):** unzentrierte Betrags-Quantile und 1,4826 x MAD je Klasse/Jahr/Serie wurden gesehen und
> ausgegeben, in Fassung 1 auch fuer die gepaarte Differenz-Reihe r_pre - r[15:30] (in Fassung 2 aus dem JSON
> entfernt, A-6); daraus wurde kein Lagewert abgeleitet. **W1/W2-Inventur:** die 2.0-Hypothesen H-01..H-18 sahen
> Bybit/Deribit-Daten 2026-03-27..2026-07-04 (Mikrostruktur, Sekunden- bis Minutenhorizont), darunter die
> 08:00-Slots 2026-03-27..2026-06-28 in W2; kein r_pre-Mittel ueber 07:30-08:00 wurde dort gebildet; Weiss et al.
> (2021-2023) liegt vor W1.
> **Kuerzel:** `[aj-A:<pfad>]` = `a2_vorarbeit.json` -> `teil_A_oi_kalender_zeitlage.<pfad>`; `[aj-B:...]` ->
> `teil_B_sigma30`; `[aj-P:...]` -> `teil_B4_power`; `[cj:<pfad>]` = `state/herleitung_hfrv/a2_census.json`;
> `[S:<datei>]` = Skript unter `scratchpad/a2_vorarbeit/` (sha256 in `[aj:skripte_sha256]`); `[pb:A2]` =
> PROGRAMM_BILANZ 2.4; `[abg.]` hier abgeleitet; `[sek]` Sekundaerbeleg; UNBELEGT = keine Fundstelle. Fassung 2:
> `[aj-F:...]` -> `teil_A5_futures_kalender`, `[aj-K:...]` -> `teil_B5_konjunktion`, `[aj-D:...]` -> `teil_B6_did`.
> Zahlen in bp = 1e-4 Log-Rendite; "Cluster" = (r_BTC + r_ETH)/2 je Verfallstag (DEC-67, ein Verfall = ein Cluster).

## 0. Befund in Kuerze

1. **Placebo-Lage (A-1):** Seit 2020-03-25 hat jeder Kalendertag einen Options-Verfall um 08:00 UTC mit
   TWAP 07:30-08:00 (0 von 2.289 Tagen ohne BTC- UND ETH-Optionsdelivery [aj-A:every_day_has_btc_and_eth_option_delivery]).
   P1 (verfallsfreie Freitage) ist leer; P2 misst "Freitag minus kleiner Tagesverfall, Funding gleich"; P3 misst
   "Ereignis-Slot minus andere Tageszeit ohne Options-TWAP" und traegt das Tageszeit-Vol-Profil. Keines der PRD-Placebos
   misst mehr "Verfall gegen kein Verfall" - **jeder registrierbare Kontrast ist ein Groessen-Kontrast** oder ein
   Tageszeit-Kontrast.
2. **Ereignisgroesse (A-2, gelieferte Optionskontrakte je Verfallstag):** Freitage (Woche+Monat+Quartal) gegen Mo-Do
   (q50-Verhaeltnis) BTC 12,8 / ETH 13,5 in 2021-03-24..2024-05-31, W1 9,7 / 7,6, W2 (bis 2026-06-28) 9,1 / 6,3; Monat+Quartal
   gegen Wochen-Freitag 3,4 / 3,7 (Vorperiode), 3,5 / 3,2 (W1), 3,8 / 3,4 (W2) [aj-A:size_by_period_and_class.<periode>.<ccy>.ratio_q50].
   Kein Freitag liegt unter dem Mo-Do-Median seiner Woche (Minimum 3,4x) [aj-A:within_week_and_month_ratios]. Der
   Abstand schrumpft ueber die Jahre (BTC 14,3 in 2021 -> 9,8 in 2025; ETH 11,5 -> 7,1). **Eine OI-Sortierung ist
   praktisch eine Freitags-Sortierung:** alle 167 Freitage der Vorperiode liegen im oberen OI-Quintil, das untere enthaelt
   keinen [aj-A:design_iii_oi_sorted_report].
3. **Empfohlenes Design (Gabelungsmuster, Abschnitt 5):** D_i - Ereignis = alle Freitage (52 je 12-Monats-Fenster),
   Placebo P2' = Mo-Do-Slots [07:30, 08:00) (208 (207)), dazu P3-Baselines; bindend P2'. SE(Kontrast) 7,34 bp, MDE80
   18,2 (18,3) bp (P-1) / 24,4 bp (A3-Praxis) je Fenster, Stress-SE 9,87 (9,88), Stress-MDE80 24,6 / 32,9 bp
   [aj-P:designs.D_i.contrasts]; gegen den ganzen Placebosatz (Fassung 2, A-1): gemeinsam 19,8, Produkt-Untergrenze 21,9 bp
   (Ereignis-Skala; mit OI-Abschwaechung 22,1 / 23,8) [aj-K:designs.D_i__S3_P2s_P3fix_P3all]. Der
   Kontrast ist ein **Groessen-Effekt**; bei OI-Proportionalitaet (Annahme, UNBELEGT) traegt er 0,84 des Ereignis-Effekts
   (Richtung Strenge) [aj-P:oi_attenuation.FRI/MODO]. Monatsverfaelle gegen Wochen-Freitage (D_ii) sind mit MDE80
   49,0 bp je Fenster nicht testbar (Power 0,21 gegen den einzigen belegten Prior 16,5 bp [sek]).
4. **Zeitlage (A-3, V-5c-Datenteil):** 167.076 Options-Deliveries 2020-03-25..2026-06-30: Median 0,038 s nach 08:00:00
   UTC, q99 0,443 s, keine vor 08:00, > 60 s nur an 2020-08-27 und 2024-08-19 [aj-A:timing_option_delivery_seconds_after_0800].
   Der Slot [07:30, 08:00) deckt das TWAP-Fenster vollstaendig. r_pre-Konvention: **close(07:59) / close(07:29)**
   empfohlen; auf Bybit-Kerzen ist open(07:30) = close(07:29) an 1.161/1.165 (BTC) und 1.165/1.165 (ETH) Tagen, beide
   Konventionen sind praktisch identisch (Korrelation 0,999998 / 1,0) [aj-B:open_eq_prev_close, aj-B:corr_pre_cc_vs_oc].
5. **Offen (UNBELEGT):** V-5b (Effektgroesse fuer Freitags-/Wochenverfaelle, Prior), Funding-Intervall BTCUSDT/ETHUSDT
   nach 2025-10-30 (Auto-Switch DEC-84; hier nicht geprueft, der lokale Funding-Extrakt reicht in den Blindbereich), Fensterlage gegen Blind-Siegel und
   Vorperiode (ENTSCHEIDUNGSVORLAGEN EV-G).
6. **Fassung 2:** taegliche Deribit-**Futures**-Verfaelle ab 2026-04-04 belegen 48 von 207 Mo-Do-Tagen in W2 (36 in beiden
   Waehrungen), keinen in W1 oder der Vorperiode [aj-F:by_window] - P2' ist zwischen W1 und W2 nicht homogen (Abschnitt
   3a); die PRD-Null "Zufallstermine mit identischer Kalenderverteilung" ist unter taeglichen Verfaellen leer bzw. mit
   dem Ereignis identisch und wird neu definiert (Abschnitt 4a, nur Definition); ein CME-Referenzfenster vor 16:00
   London ist als P3-Kontamination UNBELEGT vermerkt (Abschnitt 2).

---

## 1. Daten und Pruefungen [aj-A:raw_partition_checks, aj-A:raw_vs_calendar]

| Stueck | Befund |
|---|---|
| Settlement-Rohpartitionen (lokaler Cache `deribit/rest.settlements`) | je Waehrung 2.289 Tagespartitionen 2020-03-25..2026-06-30 gelesen (Partitionen danach nie geoeffnet); Zeilen aller Typen BTC 100.061 / ETH 100.816; Options-Deliveries 83.068 / 84.008 |
| Feldfilter | nur `type`, `instrument_name`, `timestamp`, `position` (Arrow-Regex, Positivliste); `position` an allen Options-Deliveries vorhanden, 0 null, 0 negativ, 0 gleich null |
| Konsistenz | Verfallsdatum (Name) = Partitionsdatum = Datum des Zeitstempels in allen Zeilen; 0 Duplikate; gegen den Kalender-Extrakt: 4.578 Waehrungstage, 0 Tage mit abweichender Instrumentzahl, 167.076 Zeitstempel identisch, 0 fehlend |
| Jeder Tag Verfallstag | 2.289 Tage, an jedem BTC- und ETH-Optionsdelivery (0 fehlend) [aj-A:every_day_has_btc_and_eth_option_delivery] |
| Einheit von `position` | **UNBELEGT** (Fassung 2, A-6): keine Fundstelle in der Akte; Lesart "gelieferte Kontrakte, bei inversen Optionen in Coin-Einheiten" ist eine Annahme. Verwendet werden nur Summen und Quotienten je Waehrung - die Verhaeltnisse haengen nicht von der Einheit ab, solange sie innerhalb einer Waehrung gleich ist; BTC und ETH werden nie addiert (keine Preise zur Umrechnung) |
| Kalender-Extrakt | wie a2_census (keine Preisspalte, Assert auf Spaltenmenge); Zeilen nach 2026-06-30 beim Laden verworfen (Assert) |

**C.17-Vermerk (gesehen, nicht ausgewertet):** Instrumentnamen enthalten Strikes (ein schwacher Stellvertreter des
Preisniveaus); hier weder gezaehlt noch ausgegeben. Gesehen und ausgegeben: Kontraktsummen je Verfallstag bis
2026-06-30 (W1/W2 eingeschlossen) - Zaehlgroessen, nicht ergebnisnah, vom Auftrag erlaubt.

## 2. A-1: Was jedes Placebo nach heutigem Kalender misst

Grundlage: Kalender [cj:placebo_calendar], Klassenregel C-3 (a2_census, hier fuer jeden Tag gegen die Deliveries
geprueft), Deribit-Settlement-Regel (BELEGE_AUS_PDF 6: TWAP des Index 07:30-08:00 UTC, 4-s-Takt; taegliches
Settlement 08:00 UTC fuer Futures/Perps mit Handelspause "settlement_in_progress"), Bybit-Funding 00/08/16 UTC (PRD 5.2).

| Placebo (PRD 5.2) | heutiger Kalender (seit 2020-03-25) | was der Kontrast Ereignis minus Placebo misst | verbleibende Kontamination |
|---|---|---|---|
| **P1** Nicht-Verfalls-Freitage, gleiche Uhrzeit | **leer**: 0 von 327 Freitagen ohne Delivery (Vorperiode 0/219, W1 0/52, W2 0/52) [cj:placebo_calendar] | nicht bildbar. Naechste Annaeherung **P1'** = Freitage mit nur Wochenverfall: misst "Monat/Quartal minus Woche" (Groessen-Kontrast, Faktor ~3,2..3,8 OI) | Monatsende-/Quartalsende-Flows (Rebalancing, Futures-Rollen der Quartalsfutures am selben Termin), gleiche Wochentagsstruktur |
| **P2** Nicht-Freitags-08:00-Slots | jeder Slot hat einen **Tagesverfall** (gleiches TWAP-Fenster, gleiche Uhrzeit) **und** die Bybit-Funding-Abrechnung 08:00; 2/7 der Slots sind Wochenende | "Freitags-Verfall minus Tagesverfall" bei gleichem Funding-Termin. Funding hebt sich auf, **sofern** sein Einfluss auf r_pre nicht vom Wochentag abhaengt; der Tagesverfall ist im Placebo enthalten -> Groessen-Kontrast, konservativ | (a) taeglicher Verfall (Faktor 1/9,7..1/6,3 des Freitags in W1/W2, wachsend); (b) Wochenend-Liquiditaet: SD WE/MODO 0,82 [0,68; 0,98] (Cluster) [aj-B:sd_ratios.WE/MODO]; (c) Wochentags-Effekte, die nicht verfallsbedingt sind (nicht trennbar, da P1 leer); (d) **Fassung 2:** taegliche Deribit-Futures-Verfaelle ab 2026-04-04 (W2: 48 von 207 Mo-Do-Tagen, 26 Wochenendtage; W1 keiner) [aj-F:by_window] - Teil des Ereignismechanismus im Placebo, W1/W2 inhomogen |
| **P3** uebrige Tagesstunden | keine Options-TWAP ausserhalb [07:30, 08:00); Funding nur 00:00/16:00 (Slots [23:30, 00:00) und [15:30, 16:00) liegen davor) | "Ereignis-Slot minus andere Tageszeit"; enthaelt Freitags-Verfall + Tagesverfall-Basis + 08:00-Funding gegen Funding-16:00 (beim festen Slot) | Tageszeit-Vol-Profil (SD [15:30, 16:00) alle Tage / [07:30, 08:00) Mo-Do = 1,30 [1,17; 1,45] gepoolt [aj-B:sd_ratios.fix1530_ALL/pre_MODO]); **CME-Referenzfenster** der CME-BTC/ETH-Futures am letzten Monatsfreitag (Stunde vor 16:00 London, in GMT-Monaten [15:00, 16:00) UTC, ueberdeckt [15:30, 16:00)) - **UNBELEGT** (Hinweis des Reviews, kein Primaerbeleg in der Akte, Fassung 2, A-4); "keine Options-TWAP ausserhalb [07:30, 08:00)" gilt nur fuer Deribit; US-Makro-Termine 12:30/13:30 UTC (nur Hinweis; betrifft P3-Slots um die US-Eroeffnung, Freitags z. B. Arbeitsmarktdaten); Kurtosis der Nachbar-Slots ([06:30, 07:00): 20..35) [aj-B:dispersion.shift-1h.ALL] |

**Folgerung (nur Kalender und Mechanik, keine Rendite):** Kein Placebo misst "Verfall gegen kein Verfall". Ein
Kontrast "Freitag gegen Mo-Do am selben Slot" haelt Uhrzeit, Funding-Termin, TWAP-Mechanik und Tagesverfall-Basis
konstant und variiert die Ereignisgroesse; seine verbleibende Schwaeche ist die fehlende Kontrolle reiner
Wochentagseffekte (P1 leer). Diese Kontrolle ist nur noch ueber einen anderen Slot desselben Freitags moeglich
(gepaartes P3'-Fri, Design D_i_s) - zum Preis von ~52 % mehr SE (Abschnitt 4).

**Folge aus A-4 (Fassung 2):** Solange das CME-Referenzfenster nicht primaer belegt ist, wird ein Slot [15:30, 16:00)
an Monatsend-Freitagen (12 je Fenster) **nicht** als Paarungs- oder Fix-Slot fixiert (betrifft D_i_s, die
Differenz-in-Differenzen und P3fix an diesen Tagen); Alternative ist ein Paarungs-Slot ohne fremdes Referenzfenster
(G-1).

## 3. A-2: Ereignisgroesse (gelieferte Optionskontrakte je Verfallstag und Klasse)

Je Verfallstag Summe von `position` ueber alle verfallenden Optionen der Waehrung; Klassen nach R-4; die zwei
Ausreisser-Tage (Abschnitt 6) sind ausgeschlossen [S:a2v_oi.py].

**Vermerk (Fassung 2, A-3):** Die Groesse zaehlt nur **Options**-Kontrakte. Freitage tragen seit 2021-02-19 (BTC) bzw.
2021-03-12 (ETH) zusaetzlich Wochen-Futures-Verfaelle (Vorperiode 2021-03-24..2024-05-31: an allen 167 Freitagen in
beiden Waehrungen) [aj-F:by_window], die hier fehlen -> die Freitags-Groesse ist unterschaetzt, der
Abschwaechungsfaktor (1 - OI_P/OI_E) eher zu klein (Richtung Strenge); in W2 tragen ab 2026-04 auch Mo-Do-Tage
Futures-Verfaelle (Abschnitt 3a), dort ist die Richtung offen.

**Verteilung je Klasse, q50 [q05; q95] in Kontrakten (Coin-Einheiten)** [aj-A:size_by_period_and_class.<periode>.<ccy>.contracts_per_expiry_date_by_class]

| Periode | Waehrung | Mo-Do (taeglich) | Wochenende | Freitag Woche | Freitag Monat | Freitag Quartal |
|---|---|---|---|---|---|---|
| 2020-03-25..2026-06-30 | BTC | 2.556 [1.141; 5.999] (n 1.306) | 2.978 [1.365; 7.156] | 26.211 [14.922; 48.067] (n 251) | 80.768 [46.216; 127.565] (n 50) | 139.339 [76.275; 194.862] (n 26) |
| | ETH | 20.932 [7.618; 46.750] | 22.594 [9.004; 46.751] | 198.087 [115.764; 317.758] | 569.540 [289.109; 920.043] | 1.091.775 [505.272; 1.704.489] |
| 2021-03-24..2024-05-31 (Nuisance-Periode) | BTC | 2.157 [1.023; 4.643] (n 666) | 2.610 [1.248; 5.272] | 24.164 [14.066; 43.533] (n 128) | 72.292 [44.616; 107.633] (n 26) | 135.009 [69.911; 186.206] (n 13) |
| | ETH | 17.244 [8.655; 36.179] | 19.742 [10.057; 40.149] | 207.454 [126.560; 332.063] | 630.195 [318.712; 972.574] | 1.237.214 [627.608; 1.831.883] |
| W1 2024-07-01..2025-06-30 | BTC | 2.737 [1.559; 5.110] (n 208) | 2.958 | 23.958 [17.168; 36.888] (n 40) | 69.719 (n 8) | 138.940 (n 4) |
| | ETH | 24.405 [11.763; 50.752] | 23.516 | 176.770 [121.398; 240.585] | 505.608 | 1.002.258 |
| W2 2025-07-01..2026-06-28 (DEC-99) | BTC | 3.844 [2.178; 6.952] (n 207) | 4.760 | 29.980 [20.413; 44.193] (n 40) | 103.848 (n 8) | 167.954 (n 4) |
| | ETH | 33.898 [21.230; 53.684] | 34.209 | 195.140 [128.236; 281.234] | 607.406 | 1.138.352 |

**Verhaeltnisse (q50 / q50)** [aj-A:size_by_period_and_class.<periode>.<ccy>.ratio_q50]; in Klammern das Verhaeltnis
der Summen je Tag [aj-A:...ratio_total_per_day]

| Periode | Waehrung | Freitag / Mo-Do | Woche / Mo-Do | Monat+Quartal / Woche | Monat / Woche | Quartal / Woche | Wochenende / Mo-Do |
|---|---|---:|---:|---:|---:|---:|---:|
| Nuisance 2021-03-24..2024-05-31 | BTC | 12,76 (17,24) | 11,20 | 3,38 (3,67) | 2,99 | 5,59 | 1,21 |
| | ETH | 13,47 (18,67) | 12,03 | 3,69 (3,97) | 3,04 | 5,96 | 1,14 |
| W1 | BTC | 9,69 (13,63) | 8,75 | 3,52 (3,68) | 2,91 | 5,80 | 1,08 |
| | ETH | 7,61 (10,69) | 7,24 | 3,19 (3,68) | 2,86 | 5,67 | 0,96 |
| W2 (DEC-99) | BTC | 9,09 (13,04) | 7,80 | 3,81 (4,26) | 3,46 | 5,60 | 1,24 |
| | ETH | 6,32 (9,57) | 5,76 | 3,42 (3,87) | 3,11 | 5,83 | 1,01 |

**Je Kalenderjahr, Freitag / Mo-Do (q50):** BTC 2021 14,34 / 2022 14,20 / 2023 12,40 / 2024 10,04 / 2025 9,75 / 2026 (bis
06-30) 7,12; ETH 11,47 / 13,43 / 12,48 / 11,86 / 7,06 / 5,17 [aj-A:size_by_period_and_class.jahr_<y>]. Monat+Quartal /
Woche liegt in allen Jahren bei 3,0..4,3.

**Innerhalb derselben Woche bzw. desselben Monats** [aj-A:within_week_and_month_ratios]: Freitag / q50(Mo-Do derselben
ISO-Woche) in der Nuisance-Periode q50 12,4 (BTC) / 12,9 (ETH), Minimum 5,7 / 5,4; in W1 9,4 / 7,7 (Minimum 4,6 / 3,4),
in W2 8,7 / 6,1 (Minimum 4,7 / 3,5). Monat+Quartal / q50(Wochen-Freitage desselben Monats): q50 3,5 / 3,5 (Nuisance),
3,5 / 3,2 (W1), 3,9 / 3,5 (W2); Minimum 1,8.

**OI-sortiert (Design (iii), nur Bericht)** [aj-A:design_iii_oi_sorted_report]: Score je Tag = halbe Summe der
Perzentil-Raenge (je Waehrung) der gelieferten Kontrakte. Oberes Quintil der Nuisance-Periode (233 Tage): 128 Woche + 26
Monat + 13 Quartal + 34 Mo-Do + 32 Wochenende, d. h. **alle 167 Freitage**; unteres Quintil: 0 Freitage (178 Mo-Do, 55
WE). W1/W2: oberes Quintil (73 Tage) = 52 Freitage + 21 Nicht-Freitage. Die OI-Sortierung fuegt der Kalenderklasse
"Freitag" also nur die groessten ~20 Tagesverfaelle je Jahr hinzu. Sie ist ex post (position am Verfall); OI am Vortag
08:00 ist PIT erst aus `tickers` ab 2026-06-16 verfuegbar (Auftrag A-2) - fuer eine Registrierung auf W1/W2 nicht
zulaessig, nur Bericht.

## 3a. A-3 (Fassung 2): Futures-Kalender und Klassenregel

Aus den Settlement-Rohpartitionen <= 2026-06-30 (BTC 3.324, ETH 2.665 Tagespartitionen ab 2017-05-25 bzw. 2019-03-15),
nur `type`, `instrument_name`, `timestamp` der Futures-Deliveries (Name CCY-DDMMMYY; keine `position`, kein Preis; Regel
R-14) [S:a2v_fut.py, aj-F:raw_partition_checks]: 383 (BTC) / 343 (ETH) Futures-Deliveries, Verfallsdatum = Partitionsdatum =
Zeitstempel-Datum in allen Zeilen.

| | BTC | ETH |
|---|---|---|
| erste Futures-Delivery | 2017-05-26 | 2019-03-29 |
| **erste Nicht-Freitags-Futures-Delivery** | **2026-04-04** (Sa) | **2026-04-04** (Sa) |
| Nicht-Freitags-Futures-Tage bis 2026-06-30 (davon vor 2026) | 76 (0) | 58 (0) |

**Futures-Deliveries je Klasse und Fenster (BTC / ETH; je Tag hoechstens eine je Waehrung)** [aj-F:by_window]

| Fenster | Freitag Woche | Freitag Monat | Freitag Quartal | Mo-Do | Wochenende | Mo-Do-Tage mit Futures (eine / beide Waehrungen) von allen Mo-Do |
|---|---|---|---|---|---|---|
| Vorperiode 2020-03-25..2024-05-31 | 132 / 130 | 27 / 26 | 17 / 17 | 0 / 0 | 0 / 0 | 0 / 0 von 874 |
| Nuisance 2021-03-24..2024-05-31 | 128 / 128 | 26 / 26 | 13 / 13 | 0 / 0 | 0 / 0 | 0 / 0 von 666 |
| W1 2024-07-01..2025-06-30 | 40 / 40 | 8 / 8 | 4 / 4 | 0 / 0 | 0 / 0 | 0 / 0 von 209 (208 nach R-4) |
| W2 2025-07-01..2026-06-28 | 40 / 40 | 8 / 8 | 4 / 4 | **48 / 36** | 26 / 20 | **48 / 36 von 207** (erster 2026-04-06; je 16 im April, Mai, Juni) |

**Klassenregel (Ergaenzung R-4, Fassung 2):** Die Optionsklassen bleiben unveraendert; jeder Tag wird zusaetzlich mit
"Futures-Delivery ja/nein (je Waehrung)" markiert. Das ist PIT-fixierbar (Verfallsdatum steht im Instrumentnamen
bei Listung). **Kontaminationsregister:** P2' (Mo-Do) enthaelt in W2 ab 2026-04-06 an 48 Tagen einen Futures-Verfall
mit derselben TWAP-Regel (Futures settlen auf den 30-min-TWAP, BELEGE_AUS_PDF 6) - der Placebo traegt dort einen Teil
des Ereignismechanismus (Kontrast kleiner, Richtung Strenge) und W1/W2 sind fuer P2' nicht homogen (betrifft
Kill-Bedingung (3) Vorzeichenwechsel und REZENZ). Gabelung "P2'' = Mo-Do ohne Futures-Tage" (N_P W2 159) mit SE/MDE80
in NUISANCE_SIGMA30 6.7 und Default-Vorschlag in ENTSCHEIDUNGSVORLAGEN EV-K. Die Freitage tragen seit 2021 in jeder
Woche Futures-Verfaelle (Ereignisseite, siehe Vermerk Abschnitt 3).

## 4. Kandidaten-Designs (Ereignismenge und Placebo vorab fixierbar aus dem Kalender)

Cluster = Verfallsdatum, BTC und ETH ein Cluster (DEC-67); Teststatistik je Cluster x = (r_BTC + r_ETH)/2 auf
[07:30, 08:00) nach A-3. N je 12-Monats-Fenster aus dem Kalender nach Ausschluss der Ausreisser-Tage (R-4)
[aj-A:event_counts]; SE und MDE80 aus Teil B mit gemessener Nuisance der Vorperiode (Zentral-Linie: SD der Klasse 2021-03-24..2024-05-31, c nach
P-3-Logik; Stress = SD des Jahres mit groesster Streuung, hier jeweils 2021) [aj-P:designs.<D>.contrasts]. Bindend nach
PRD 5.2 = Placebo mit groesstem SE(Kontrast).

**Fensterlage (Fassung 2, A-6):** PRD 5.2 nennt W1 = 2024-09-01..2025-08-31 und W2 = 2025-09-01..2026-08-31; diese
Fenster reichen in den Blindbereich ab 2026-07-01 (DEC-96 E3). Fuer jede Registrierung ab 2026-10-20 gilt DEC-99 (8):
W1 2024-07-01..2025-06-30, W2 2025-07-01..2026-06-28; alle Fensterzahlen hier folgen DEC-99 (8), nicht dem PRD-Text.

**Ereigniszahlen je Kalenderjahr und Fenster** [aj-A:event_counts.<periode>.ohne_ausreisser_regel_R4]

| Zeitraum | Freitage gesamt | Woche | Monat | Quartal | Monat+Quartal | Mo-Do | Wochenende | Nicht-Freitag | alle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 53 | 41 | 8 | 4 | 12 | 208 | 104 | 312 | 365 |
| 2022 | 52 | 40 | 8 | 4 | 12 | 208 | 105 | 313 | 365 |
| 2023 | 52 | 40 | 8 | 4 | 12 | 208 | 105 | 313 | 365 |
| 2024 (ohne 2024-08-19) | 52 | 40 | 8 | 4 | 12 | 209 | 104 | 313 | 365 |
| 2025 | 52 | 40 | 8 | 4 | 12 | 209 | 104 | 313 | 365 |
| hypothetisch W1 2024-07-01..2025-06-30 (ohne 2024-08-19) | 52 | 40 | 8 | 4 | 12 | 208 | 104 | 312 | 364 |
| hypothetisch W2 2025-07-01..2026-06-30 | 52 | 40 | 8 | 4 | 12 | 209 | 104 | 313 | 365 |
| W2 nach DEC-99 (bis 2026-06-28) | 52 | 40 | 8 | 4 | 12 | 207 | 104 | 311 | 363 |
| Nuisance-Periode 2021-03-24..2024-05-31 | 167 | 128 | 26 | 13 | 39 | 666 | 332 | 998 | 1.165 |

**Design-Tabelle (W1 / W2 nach DEC-99; SE und MDE80 in bp je Fenster)**

| Design | Ereignis (N_E) | Placebos (N_P) | bindend | SE(Kontrast) zentral / c=1 / Stress | MDE80 P-1 zentral (Stress) | MDE80 A3-Praxis zentral | Kontamination, die bleibt | Richtung |
|---|---|---|---|---|---:|---:|---|---|
| PRD_a (Referenz) | alle Freitage (52) | P2 = alle Nicht-Freitage (312 (311)) | P2 | 6,90 / 6,49 / 9,29 | 17,2 (Stress 23,1) | 23,0 | Tagesverfall, Wochenende im Placebo | Testbarkeit gegen D_i (Wochenend-SD senkt SE_P) |
| **D_i (empfohlen)** | alle Freitage (52) | P2' = Mo-Do (208 (207)); P3fix = alle Tage [15:30, 16:00) (364 (363)); P3all = alle Tage, 44 Halbstunden ausserhalb [07:00, 09:00) | P2' | **7,34 / 6,75 (6,76) / 9,87 (9,88)** | **18,2 (18,3) (Stress 24,6)** | **24,4** | Tagesverfall im Placebo (Groessen-Kontrast), Wochentagseffekte nicht getrennt | Strenge gegen PRD_a (+6 % SE); konservativ (Kontrast < Ereigniseffekt) |
| D_i_s (streng) | alle Freitage (52) | wie D_i + P3'-Fri = derselbe Freitag [15:30, 16:00), gepaart (52) | P3'-Fri | 11,15 / 10,63 / 15,13 | 27,7 (Stress 37,6) | 37,1 | Tageszeit-Vol-Profil (15:30 = 1,30 x 07:30), US-Session | Strenge (kontrolliert Wochentag), +52 % SE |
| D_i_W | Wochen-Freitage ohne Monat (40) | wie D_i | P2' | 8,06 / 7,13 / 11,33 | 20,0 (20,1) (Stress 28,2) | 26,8 | wie D_i | Strenge gegen D_i (kleineres N), aber reinere Klasse |
| D_ii | Monat+Quartal (12) | P1' = Wochen-Freitage (40); P2', P3fix, P3all | P1' | 19,70 / 16,48 / 23,88 | 49,0 (Stress 59,4) | 65,6 | Monats-/Quartalsende-Flows, Quartalsfutures | Strenge gegen jede Freitags-Variante (N 12 statt 52, Placebo P1' traegt selbst ~1/3,2 des Ereignis-OI, Abschwaechung 0,687); in jeder Linie GL012 (Fassung 2, A-6) |
| PRD_b (Referenz) | Monat+Quartal (12) | P1 -> P1' (40) | P1' | = D_ii | 49,0 | 65,6 | wie D_ii | wie D_ii; zusaetzlich Strenge gegen den PRD-Wortlaut (P1 "verfallsfrei" nicht bildbar, P1' traegt Wochenverfaelle) |
| D_iii (Bericht) | oberes OI-Quintil (73) | unteres OI-Quintil (73) | - | 6,72 (SD/c der Klasse ALL) | 16,7 | - | ex post, = Freitag + ~20 Tagesverfaelle | nicht registrierbar |

Quellen: [aj-P:designs.<D>.contrasts.<zentral|c1|stress_max_year>.by_placebo.<P>.windows.W1.se_contrast],
[aj-P:...mde80_p1], [aj-P:...mde80_a3_practice], [aj-P:designs.D_iii_report]. W1 und W2 unterscheiden sich nur in N_P
(208 gegen 207); Hauptwert W1, W2 in Klammern, wo die Rundung abweicht.

**Konjunktion (Fassung 2, A-1):** Die Spalte MDE80 gilt fuer den bindenden **Einzel**-Placebo. Das Gate verlangt
Signifikanz gegen **alle** Placebos des Satzes; MDE80 auf der Ereignis-Skala, P-1, W1 (W2), Einzel / gemeinsam (Monte
Carlo, Bericht) / Produkt der Einzel-Powers (Untergrenze) [aj-K:designs.<D>.lines.<linie>.mde80]: D_i {P2'} 18,2 (18,3) /
18,3 / 18,2 (18,3); D_i {P2', P3fix} 18,2 (18,3) / 19,7 / 21,0; **D_i {P2', P3fix, P3all} 18,2 (18,3) / 19,8 / 21,9**;
D_i_W 20,0 (20,1) / 21,6 / 24,2; PRD_a {P2, P3fix, P3all} 17,9 / 19,0 / 21,4; D_i_s 27,7 / 27,9 / 28,6; D_ii 49,0 /
51,4 / 61,1. **Festlegung des Orchestrators (uebernommen, als Festlegung gekennzeichnet):** die Zuordnung
(C10/DEC52/GL012) traegt analog DEC-94 (6) das **Produkt** (Untergrenze), die gemeinsame Power ist Bericht;
Richtung Strenge. Details NUISANCE_SIGMA30 6.5.

**Prior-Lesart je Design:** bei D_i, D_i_W, D_ii ist der getestete Kontrast ein Groessen-Effekt. Unter der Annahme
"Effekt proportional zu gelieferten Kontrakten" (PRD 5.2: "Hedgebedarf proportional zum verfallenden Open Interest";
als Proportionalitaet UNBELEGT) ist der Kontrast-Prior = Ereignis-Prior x (1 - OI_P/OI_E); mit dem kleinsten
q50-Verhaeltnis aus {BTC, ETH} x {W1, W2} (Richtung Strenge): D_i 0,842 (6,32), D_i_W 0,826 (5,76), D_ii gegen P1' 0,687
(3,19), D_ii gegen Mo-Do 0,949 (19,68) [aj-P:oi_attenuation]. Mit den Verhaeltnissen der Nuisance-Periode waeren es
0,922 / 0,911 / 0,704 (Richtung Testbarkeit). P3-Placebos haben keine Options-TWAP: dort gilt der volle Prior.

## 4a. Null fuer den Groessen-Kontrast (Fassung 2, A-2; nur Definition, nicht gebaut, nicht gerechnet)

**Etikett: "Null neu definiert nach DEC-98 N5".** PRD 5.2 definiert den strukturellen Nulleffekt als die Pipeline auf
"Zufallsterminen mit identischer Kalenderverteilung (gleiche Anzahl, Wochentags-, Tageszeit- und Cluster-Struktur)",
1.000-fach; die Schwelle ist max(95-%-Quantil dieser Placebo-Verteilung; z SE), und DEC-94 (5) (ii) verlangt eine
kalibrierte Null-Simulation. **Seit 2020-03-25 ist jeder Kalendertag ein Verfallstag:** eine wochentags- und
tageszeittreue Ziehung von 52 "Freitagen" um 07:30 zieht genau die Ereignisse selbst - die PRD-Null ist leer bzw. mit
dem Ereignis identisch. Sie muss fuer den Groessen-Kontrast neu gefasst werden, **vor jeder Zahl**:

| Vorlage | Definition | erhaelt | Richtung |
|---|---|---|---|
| **(i) Label-Permutation Freitag <-> Mo-Do innerhalb derselben ISO-Woche (Default bei Stille)** | je Woche wird das Label "Ereignis" zufaellig einem der fuenf Tage Mo..Fr zugeordnet (die uebrigen vier sind "Placebo"); Statistik = derselbe Kontrast Ereignis minus P2'; 1.000 Ziehungen, Seed registriert | Wochen-Cluster, Tageszeit (07:30-Slot), Funding-Termin, Vol-Regime der Woche, Anzahl 52 / 208 | exakt unter Austauschbarkeit Freitag/Mo-Do, robust gegen schwere Raender und Vol-Regime (neutral bis Strenge fuer die Streuung); **Grenze:** ein reiner Wochentagseffekt verletzt die Austauschbarkeit und erscheint als "Effekt" - dieselbe Grenze wie P2' (Richtung Testbarkeit bezueglich Wochentags-Konfundierung) |
| (ii) Slot-Verschiebung bei festen Tagen | dieselben Ereignis- und Placebo-Tage, der 30-min-Slot wird zufaellig auf einen anderen Halbstunden-Slot verschoben (ohne [07:00, 09:00) und ohne Funding-/Referenz-Slots), Statistik = derselbe Kontrast | Kalender, Wochentage, Cluster, Anzahl | **Strenge bezueglich Wochentag** (ein Freitag-gegen-Mo-Do-Unterschied zu anderen Tageszeiten verbreitert/verschiebt die Null); die anderen Slots streuen meist staerker (07:30 ist ein ruhiger Slot, NUISANCE_SIGMA30 B-1) -> breitere Null (Strenge); Grenze: andere Slots tragen eigene Termine (US-Makro, Funding 16:00, CME-Fenster UNBELEGT) |

Beide Vorlagen sind nur definiert; gebaut und gerechnet wird erst nach einer Entscheidung (ENTSCHEIDUNGSVORLAGEN EV-J).

## 5. Empfehlung (mit Gabelungen und Richtung)

**Empfohlen: D_i** - Ereignis = alle Freitage (Woche + Monat + Quartal, Kalenderklasse, vorab fixierbar), urteilstragender
Kontrast gegen P2' = Mo-Do [07:30, 08:00), Placebosatz {P2', P3fix, P3all}, bindend P2' (groesstes SE und kleinster
Kontrast-Prior). Begruendung:
1. **Groesste Ereignismenge mit klar groesserem Ereignis:** 52 Cluster je Fenster; jeder Freitag liegt ueber 3,4x dem
   Mo-Do-Median seiner Woche (A-2). Die Abschwaechung durch den Tagesverfall im Placebo ist klein (Faktor 0,84..0,92).
2. **Mechanik konstant gehalten:** gleiche Uhrzeit, gleiches TWAP-Fenster, gleicher Bybit-Funding-Termin (08:00) in
   Ereignis und Placebo; damit trifft Kill-Bedingung (2) der PRD (Funding erklaert den Effekt) den Kontrast nicht mehr
   direkt - ein reiner Funding-Effekt hebt sich auf, sofern wochentagsunabhaengig (Richtung: Strenge gegen H-01-Verwechslung).
3. **Wochenende ausgeschlossen** (gegen PRD_a): Wochenend-Slots haben 18 % kleinere SD und andere Liquiditaet; ihr
   Einschluss senkt die SE um 6 % (Richtung Testbarkeit) und mischt ein Liquiditaetsregime ein - nicht empfohlen.
4. **Variante (b) der PRD ist nicht tragfaehig:** D_ii braucht bei 16,5 bp (einziger belegter Prior, Aktien-Monatsverfall
   [sek]) 8,8 Jahre je Fenster (P-1), mit OI-Abschwaechung 18,7 (Abschnitt B-4 in NUISANCE_SIGMA30).
5. **Placebosatz und Konjunktion (Fassung 2):** jeder zusaetzliche Placebo kostet Power (D_i Produkt-MDE80 18,2 -> 21,0
   -> 21,9 bp fuer 1 / 2 / 3 Placebos); der Placebosatz ist vor jeder weiteren Zahl zu fixieren (ENTSCHEIDUNGSVORLAGEN EV-B).

**Gabelungen (offengelegt, keine gewaehlt):**
- G-1 **D_i_s statt D_i** (gepaarter Freitags-Slot [15:30, 16:00) als zusaetzlicher, dann bindender Placebo) - Richtung
  **Strenge**: kontrolliert Wochentagseffekte, die P2' nicht trennt; SE +52 % (11,15 statt 7,34), MDE80 27,7 bp.
  Alternative Paarungs-Slots (z. B. [05:30, 06:00), SD-Verhaeltnis zu [07:30, 08:00) 1,02 [aj-B:sd_ratios.shift-2h_ALL/pre_ALL])
  wuerden die SE weniger erhoehen, verlieren aber die Funding-Paarung; nicht gerechnet, Wahl vor jeder Zahl zu fixieren.
  Fassung 2 (A-4): an Monatsend-Freitagen ist [15:30, 16:00) wegen des UNBELEGTEN CME-Referenzfensters nicht als
  Paarungs-Slot zu fixieren.
- G-2 **PRD_a (Placebo inkl. Wochenende)** - Richtung **Testbarkeit** (SE 6,90 statt 7,34), mit Wochenend-Kontamination.
- G-3 **D_i_W (nur Wochen-Freitage)** - Richtung **Strenge** (SE 8,06), reinere Ereignisklasse ohne Monatsende-Flows.
- G-4 **OI-Sortierung** - nur Bericht (ex post); die Kalenderklasse erfasst sie bereits zu ~70 %.
- G-5 **Gewichtung BTC/ETH** gleich in bp (PRD-Gate (3) poolt beide); BTC allein haette kleinere SD (40,2 gegen 43,8
  Cluster an Freitagen) - Richtung Testbarkeit, widerspricht Gate-Bedingung (3), nicht empfohlen.
- G-6 (Fassung 2, A-3) **P2'' = Mo-Do ohne Futures-Verfallstage** - Richtung Reinheit/Homogenitaet W1/W2 gegen groessere
  SE (W2 7,58 statt 7,34, MDE80 18,8 statt 18,3) [aj-K:designs.D_i_futfrei__S1_P2ss]; Default-Vorschlag in EV-K.
- G-7 (Fassung 2, A-5) **Differenz-in-Differenzen** (Freitag r_pre - r[15:30]) - (Mo-Do r_pre - r[15:30]): kontrolliert
  Wochentag und Tageszeit zugleich; Richtung Strenge, SE 12,62 (12,63), MDE80 31,4 bp [aj-D:windows] (EV-M).

**Was die Empfehlung nicht leistet:** Sie belegt keine Effektgroesse (V-5b UNBELEGT); unter der Vorbedingung der PRD
bleibt A2 GL-012 bis zum Beleg. Die Feasibility-Zahlen (Prior-Gitter, Fensterlaenge) stehen in NUISANCE_SIGMA30 B-4.

## 6. A-3: V-5c-Datenteil - Zeitlage und r_pre-Definition

**Delivery-Zeitstempel gegen das TWAP-Fenster** [aj-A:timing_option_delivery_seconds_after_0800]

| Zeitraum | Options-Deliveries | q0 / q01 / q50 / q99 / q999 (s nach 08:00:00 UTC) | max | vor 08:00 | > 1 s | > 60 s |
|---|---:|---|---:|---:|---:|---:|
| 2020-03-25..2026-06-30 | 167.076 | 0,005 / 0,007 / 0,038 / 0,443 / 0,528 | 4.718 | 0 | 111 | 84 |
| 2021-03-24..2024-05-31 | 74.939 | 0,005 / 0,007 / 0,031 / 0,122 / 0,266 | 0,279 | 0 | 0 | 0 |

- Ausreisser-Tage (> 60 s): **2020-08-27** (Do) und **2024-08-19** (Mo) [aj-A:...outlier_days_gt_60s_until_2026-06-30];
  beide werden nach R-4 aus jeder Ereignis- und Placebo-Menge ausgeschlossen (Regel vor jeder Zahl fixiert; ob dort
  auch das Mittelungsfenster abwich, zeigt der Kalender nicht). Folge: W1 hat 208 statt 209 Mo-Do-Tage. In der
  Nuisance-Periode liegt keiner.
- **Lage:** Die Delivery wird ~0,04 s nach 08:00:00 UTC gebucht, unmittelbar nach dem Ende des 30-Minuten-TWAP
  07:30-08:00 (BELEGE_AUS_PDF 6, Wortlaut 2026; 2019 dieselbe 30-Minuten-Regel mit 6-s-Takt). Der Slot [07:30, 08:00)
  deckt das Mittelungsfenster also exakt; das Umstellungsdatum 6 s -> 4 s bleibt UNBELEGT (fuer die Slot-Lage ohne Belang).

**r_pre auf 1-min-Kerzen** (Bybit, `start_ms` = Kerzenbeginn, 1.440 Kerzen je UTC-Tag):

| Konvention | Formel | Intervall in Handelszeit |
|---|---|---|
| (a) close-to-close (**empfohlen**) | r_pre = ln(close[07:59] / close[07:29]) | letzter Trade vor 07:30:00 bis letzter Trade vor 08:00:00 |
| (b) open-to-close | r_pre = ln(close[07:59] / open[07:30]) | erster Trade ab 07:30:00 bis letzter Trade vor 08:00:00 |

- **Daten:** open[07:30] = close[07:29] an 1.161 von 1.165 Tagen (BTC) und 1.165 von 1.165 (ETH); ueber alle
  Minuten 1.674.593 / 1.676.435 bzw. 1.675.361 / 1.676.435 [aj-B:open_eq_prev_close]. Korrelation (a)/(b) 0,999998 (BTC),
  1,0 (ETH); SD-Verhaeltnis 1,000 [1,000; 1,000] [aj-B:corr_pre_cc_vs_oc, aj-B:sd_ratios.pre_oc_ALL/pre_ALL]. Auf
  diesem Datensatz sind beide Konventionen praktisch gleich.
- **Begruendung fuer (a):** (1) der TWAP beginnt seine Schnappschuesse ab 07:30:00; der Preis "um 07:30:00" ist der
  letzte Trade davor = close[07:29], der Preis "um 08:00:00" = close[07:59] (die 07:59-Kerze schliesst vor der Buchung
  08:00:00 + 0,04 s); (2) (a) teleskopiert mit allen anderen Slots und mit r_post = ln(close[08:59]/close[07:59]) - keine
  Rendite zwischen zwei Kerzen geht verloren; (3) gleiche Gitter-Konvention wie HF-RV R-3 und die Vorlage des
  A2-Zensus (Abschnitt 7: "close 07:29 bis close 07:59"); (4) (a) haengt nicht an der Open-Konvention der Boerse.
- **Vermerk:** Die Settlement-TWAP ist ein Index (Spot-Komposit), r_pre misst den Bybit-Perp; die Basis Perp-Index
  liegt im Slot und ist Teil der Streuung.

## 7. Offene Punkte

| Punkt | Status |
|---|---|
| V-5b Effektgroesse fuer Freitags-/Wochenverfaelle | UNBELEGT (Weiss et al. FRL 2026: Richtung [sek], Groesse fehlt) - blockiert jede Registrierung |
| Proportionalitaet Effekt ~ gelieferte Kontrakte | UNBELEGT (Annahme fuer die Kontrast-Prior-Linie) |
| Funding-Intervall BTCUSDT/ETHUSDT ab 2025-10-30 (W2) | UNBELEGT hier (der lokale Funding-Extrakt reicht bis 2026-09-28 in den Blindbereich und wurde nicht geoeffnet; Pruefung nur mit auf <= 2026-06-28 geschnittenem Strom) |
| Kontinuitaet der TWAP-Regel 2020..2026 | Endpunkte belegt (2019, 2026), Zeitstempel durchgehend 08:00 + < 0,6 s; Umstellung 6 s -> 4 s UNBELEGT |
| Wochentagseffekte ohne Verfallsbezug | mit P2' nicht trennbar (P1 leer); nur ueber gepaarten Slot (G-1) oder DiD (G-7) |
| Einheit von `position` (Fassung 2) | UNBELEGT; Quotienten je Waehrung unberuehrt |
| CME-Referenzfenster vor 16:00 London am Monatsende (Fassung 2) | UNBELEGT; 15:30-Slot an Monatsend-Freitagen nicht fixieren |
| Futures-Tagesverfaelle in P2' ab 2026-04-04 (Fassung 2) | gemessen (48/207 Mo-Do in W2); Gabelung G-6 / EV-K offen |
| Null fuer den Groessen-Kontrast (Fassung 2) | definiert (Abschnitt 4a), nicht gebaut |

## 8. Reproduktion

`scratchpad/a2_vorarbeit/run_all.sh` (a2v_oi.py, a2v_sigma30.py, a2v_power.py, Fassung 2 zusaetzlich a2v_fut.py,
a2v_corr2.py, a2v_konj.py; dann a2v_build.py; zusammen ~2 min); liest nur die lokalen Extrakte und Cache-Partitionen
<= 2026-06-30. Zwei Laeufe mit identischen sha256 der Zwischen- und Endausgaben. Regeln R-1..R-11 (Fassung 1) und
R-12..R-15 (Fassung 2) im Docstring von `a2v_common.py`, jeweils vor der ersten Zahl geschrieben.

## 9. Aenderungen gegen Fassung 1

1. **A-1 (Konjunktion):** MDE80 gegen den ganzen Placebosatz als Doppelausweis (Abschnitt 4); D_i {P2', P3fix, P3all}:
   Einzel 18,2 (18,3), gemeinsam 19,8, Produkt 21,9 bp (mit OI-Abschwaechung 21,7 / 22,1 / 23,8); Zuordnung traegt
   das Produkt (Festlegung des Orchestrators).
2. **A-2 (Null):** Abschnitt 4a - PRD-Null unter taeglichen Verfaellen leer; Vorlagen (i) Label-Permutation in der
   ISO-Woche (Default) und (ii) Slot-Verschiebung; nicht gebaut.
3. **A-3 (Futures):** Abschnitt 3a - erste Nicht-Freitags-Futures-Delivery 2026-04-04 (BTC und ETH); W2: 48 von 207
   Mo-Do-Tagen mit Futures-Verfall (36 beide Waehrungen), W1 und Vorperiode keiner; Vermerk zur Freitags-OI.
4. **A-4 (CME):** CME-Referenzfenster als UNBELEGTE P3-Kontamination; 15:30-Slot an Monatsend-Freitagen nicht fixiert.
5. **A-5:** Gabelungen DiD (G-7, MDE80 31,4 bp) und Futures-freies P2'' (G-6); historische Baseline und
   Beta-Residualisierung in ENTSCHEIDUNGSVORLAGEN EV-M.
6. **A-6:** C.17-Kopfzeile und W1/W2-Inventur; Einheit von `position` UNBELEGT; Richtung D_ii/PRD_b; PRD-5.2-Fenster
   -> DEC-99 (8); Rundung vereinheitlicht; Beschriftung "[15:30] alle Tage / [07:30] Mo-Do = 1,30"; Waechter erweitert.
   Neue sha256 von `a2_vorarbeit.json`: `9a2f5ac91a1ce7f8c71953afd2ef83a6b5ceeda150ff9c28a681905c9de26052` (Fassung 1: `2bd1ad7e...d30a`).
