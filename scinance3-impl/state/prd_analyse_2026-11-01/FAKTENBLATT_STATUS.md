# Faktenblatt Status: Hypothesen, Kandidaten, Datenstroeme, Wartezeit-Regeln (Stand 2026-11-01)

> Kartierungsauftrag der PRD-Gesamtanalyse. Nur gelesen, nichts gerechnet: keine Marktdaten, kein Harvest-Client,
> keine Siegeldateien, kein Commit. Alle Zahlen sind aus der Akte uebernommen; abgeleitete Zahlen sind als [E] markiert.
> Kein Hostname, keine Zugangsdaten, keine Modellnamen (Rollen: Orchestrator, Herleitungsagent, Reviewer).

## 0. Lesehilfe

**Kennzeichen.** [F] = Fakt mit Fundstelle. [E] = Einschaetzung des Kartierungsagenten (kein Fakt, keine Akte).
[V] = Vermutung, in der gelesenen Akte nicht belegt. [P] = Vorschlag mit Richtung (Strenge / Testbarkeit / neutral).
Ohne Kennzeichen in einer Fundstellen-Spalte gilt [F].

**Fundstellen-Kuerzel** (Pfade unter `/home/user/scinance/`):

| Kuerzel | Datei |
|---|---|
| KOMP | `scinance3-impl/survey/ERKENNTNIS_KOMPENDIUM.md` (Abschnitte A-F) |
| PRD | `scinance3-impl/PRD_SCINANCE3.md` (Par. 1-11, Orchestrator-Fassung v2) |
| CLA3 | `scinance3-impl/CLAUDE.md` |
| DEC | `scinance3-impl/state/decisions.md` (DEC-51..DEC-103, Nachtraege "N") |
| DEC2 | `scinance2-impl/state/decisions.md` (DEC-01..DEC-50) |
| GL | `scinance3-impl/state/gate_log.md` (GL-032..GL-036); GL-001..GL-031 nur ueber KOMP/F2R zitiert |
| REG3 / REG2 | `scinance3-impl/state/hypothesis_registry.md` / `scinance2-impl/state/hypothesis_registry.md` |
| BIL | `scinance3-impl/state/PROGRAMM_BILANZ_2026-10-18.md` (mit Vermerken 2026-10-18 und 2026-10-29) |
| STAND | `scinance3-impl/STAND_2026-10-18.md` (Nachtraege bis 2026-10-31) |
| UEB | `scinance3-impl/UEBERGABE_2026-10-12.md` (Abschnitte 4-13) |
| BEF21 | `scinance3-impl/state/BEFUND_DATENSTROEME_2026-10-21.md` |
| HA2 / HHF / H32 / H33 | `scinance3-impl/state/herleitung_a2/`, `.../herleitung_hfrv/`, `.../herleitung_h32/`, `.../herleitung_h33/` |
| F2R / W6 / STRAT | `scinance2-impl/state/PROGRAM_FINAL_REPORT.md`, `WELLE6_KANDIDATEN_SYNTHESE_2026-08-10.md`, `STRATEGIE_KANDIDATEN_2026-08-20.md` |
| INV | `state/prd_analyse_2026-11-01/DATENINVENTAR_2026-11-01.md` (Katalog-Stand 2026-11-01T11:48Z) |
| DA | `scinance_work/harvest_client/DATA_ACCESS.md` (nur Strom-Beschreibungen und Datenbesonderheiten) |

### Auf einen Blick (8 Befunde, jeder in den Tabellen unten belegt)

1. **3.0 hat bis heute 0 Verdikte.** Acht Kandidatenzeilen: 2 registriert (A3-Drittfassung H-28..H-30, H-32) und beide ohne Test
   beendet (GL-032, GL-035); 3 GL-012 vor der Registrierung (A1/H-31, H-27, H-33); 3 gesperrt (A2, A4, A5). [F] T2.
2. **2.0: Friktion war nur bei H-04b und H-05c die bindende Todesursache** (plus H-25 a priori). H-03, H-09, H-24, die PRD Par. 1
   als Friktions-Messungen fuehrt, starben am Nulleffekt (Surrogate-p ~1,0 / Rauschen / negatives Vorzeichen). [F] T1; [E] zur PRD-Lesart.
3. **Kein 2.0-Test lief auf Wochen- oder Monatshorizont mit breitem Universum;** laengste Horizonte: H-11/H-11c 3 Tage (Vol), H-22 1 Tag (BTC),
   H-20 bis 24 h; H-26 (30 Tage) ist gesperrt. Dieselbe Information auf Tages-/Wochenhorizont ist bei allen 8 Zeilen mit Sekunden-/Tick-Horizont (H-04, H-04b, H-05, H-05b, H-05c, H-14, H-15, H-16) ungetestet. [F/E] T1.
4. **Die Wartezeit entsteht aus dem Zusammenspiel von Power 0,80 je Fenster, C.10 (zwei Fenster), 12-Monats-Fenstern, REZENZ und Blind-Siegel;**
   fruehestes bedingtes Datum je Kandidat (BIL, bedingt): A3-fm8 2027-08-22 (verbraucht), A1 2030-01-06 (nur mit theta), VRP 2030-04-04 (Prior 9,47)
   bis ~2033-01 (Prior 7,14), A3-Roh-IC 2031-05-11, A4 ~2029-12-28 [E]. [F] Daten T2/T4; die Aussage zum Zusammenspiel ist [E] (T4.4).
5. **Zwei Regeln wurden bereits als "Lockerung" beschlossen:** DEC-94 (P-1, 2026-10-13, ohne ausdrueckliche Nutzer-Zustimmung im Text) und
   DEC-99 (REZENZ/Pilot, 2026-10-20, mit Nutzer-Zustimmung). [E] Schwellenregeln sind in der Praxis Orchestrator-Entscheidungen; der Nutzer wurde einmal gefragt. [F] T4.
6. **Blind-Siegel + Einmal-Gut:** seit 2026-07-01 liegen 123 Tage (bis 2026-10-31, [E] gezaehlt) unberuehrt; die Reihenfolge-Frage (wer die Blindperiode zuerst
   verbraucht) ist seit 2026-10-18 beim Nutzer offen (DEC-98 E4 (b)). [F] T4.
7. **Datenstroeme:** 29 Stroeme im Katalog. Tick-/Trade-/L2-Daten nur fuer 5 Symbole; das breite Universum (~1.100 Perps) nur als Tages-OHLCV und
   Funding. Nicht von einem 3.0-Kandidaten genutzt (Akte): `rest.openInterest` (BTC/ETH ab 2024-03), `allLiquidation`, `insurance`, `bybit/orderbook`
   (nur 2.0 und Welle-1-Paket WP-10(B), kein Kandidat), `tardis/options_chain` (91 Stichtage), `deribit/orderbook`, `bitmex`. [F/E] T3.
8. **Offen beim Nutzer (Akte):** Reihenfolge der Blindperiode; A2-Vorlage P-0..P-3; Weiterleitung Datenauftrag Negativ-Panel; PDF-Nachlieferung. [F] Abschnitt 5.2.

---

## T1. Alle 2.0-Hypothesen H-01..H-26 (KOMP Abschnitt A)

Spalten: **Klasse** = Mikrostruktur-/Informationsfamilie [E] (das 3.0-Raster P/W/E gilt nur fuer 3.0, PRD Par. 3.2). **Horizont** = Zielhorizont der
urteilstragenden Statistik. **Todesursache** nach dem Raster des Auftrags (Friktion / Power / Positivkontrolle / Daten / Logik / Nulleffekt); "--" = kein Tod.
**Kap.-frei WEITER?** = blieb eine kapitalfreie Messung als WEITER stehen. **Horizont-abh.?** = ob dieselbe Information auf Tages-/Wochenhorizont noch ungetestet ist
[E, soweit nicht anders vermerkt]. Verdikte und GL-Nummern aus KOMP A; Horizonte aus REG2 und KOMP.

| ID | Klasse [E] | Horizont | Verdikt (GL) | Bindende Todesursache | Kap.-frei WEITER? | Horizont-abh.? (Tag/Woche ungetestet?) | Fundstelle |
|---|---|---|---|---|---|---|---|
| H-01 | Funding/Pre-Settlement-Entry, Perp | Minuten bis Stunden (Tick-Zeit-Time-Stop) [E] | DROP (GL-004) | **Nulleffekt**: RAW-Edge -4,48 bps schon vor Friktion; netto -15,47 bps | nein | teilweise: Funding auf Wochenhorizont = A1/H-31, GL-012, ungetestet | KOMP A.2 H-01; REG2 H-01; F2R Tab. 4 |
| H-02 | Vol-Prognose LightGBM/HAR, Ziel log(RV 60 min), 5 Symbole | 60 min | DROP/PARK (GL-001) | **Logik**: R^2 0,249 war L1-Selbstauskunfts-Artefakt; 0/5 Symbole, 0/36 Features FDR | nein | nein fuer 3 Tage (H-11c DROP); Woche ungetestet | KOMP A.2; REG2 H-02 |
| H-03 | Cyclostationary CFAR, Inter-Arrival | Ticks/Sekunden | DROP (GL-005) | **Nulleffekt**: Surrogate-p ~1,0; Edge 0,01-0,04 bps (zusaetzlich 250x unter Wand) | nein | nein (kein Signal) | KOMP A.2 H-03, D.4 |
| H-04 | Lead-Lag BTC->ETH (TE, WCOH) | Lags 1-3 s (getestet 1,2,3,5,10 s) | **WEITER** kapitalfrei (GL-006); H-18 (GL-014) bestaetigt 12/12 | -- | **ja** | **ja**: Tages-/Wochen-Lead-Lag BTC->Alts nie getestet | KOMP A.3, A.6 H-18; REG2 H-04 |
| H-04b | Lead-Lag-Tradability | 1-3 s | PARK (GL-009) | **Friktion**: netto -14,95/-14,83 bps; Einfang max +0,19 bps (~80x unter 11 bps); Maker -5,9 bps | (Folge von H-04: ja) | **ja**: Wand fix, Einfang waechst mit Horizont (PRD Par. 1 / R4 K-0.1: Mindesthorizont 6,6 h Taker, 53 min Maker) | KOMP A.3; PRD Par. 1 |
| H-05 | OFI-Vorzeichen positiv (Aggression-Folge) | Lags ab 1 s | DROP (GL-007) | **Logik/Nulleffekt**: These widerlegt, einziger robuster FDR-Effekt invers (ETH corr -0,0550) | nein | teilweise: 30-min-Fluss H-24 negativ; Tages-/Wochenfluss ungetestet | KOMP A.3, D.5 |
| H-05b | OFI invers (MM-Replenishment), SOL | 1 s / 5 s | **WEITER** kapitalfrei (GL-010) | -- (schmal: 1 Symbol, abs(corr) 0,010-0,051) | **ja** | **ja** wie H-05 | KOMP A.3 |
| H-05c | OFI-Fade-Tradability | 1-5 s | PARK (GL-011) | **Friktion**: Einfang +0,03..+0,10 bps, 150-500x unter 15 bps | (Folge: ja) | **ja** | KOMP A.3 |
| H-06 | Permutation Entropy -> Vol-Cluster | 15 min | DROP (GL-008) | **Nulleffekt**: PRE-Gate rho max +0,0145 gegen 0,30 (~20x) | nein | nein (Grundannahme traegt nicht, KOMP D.6) | KOMP A.3, D.6 |
| H-07 | Querschnitts-MR, absolutes z >= 2,5, N=5 | 5/15/30 min | DROP strukturell (GL-012) | **Logik**: max abs(z) = sqrt(N-1) = 2,0 < 2,5 (kein Datenlauf) | nein | im Design-Sinn: Wochen-Reversal auf K >= 117 = A3-R/H-29/H-33 (GL-012; nicht gelaufen) | KOMP A.4, B.11, C.12 |
| H-08 | Querschnitts-MR rangbasiert | 5/15/30 min | DROP (GL-013) | **Nulleffekt** (0/6 Zellen FDR, Anker verfehlt, Mai negativ); Power nie gerechnet | nein | wie H-07 | KOMP A.4, D.7; PRD Par. 2 L-5 |
| H-09 | Risk-Limit-Tier-Bunching | Order-Aggregate (kein Preishorizont) | DROP (GL-016) | **Nulleffekt**: 0/10 Zellen, Rundzahl-Praeferenz | nein | nein | KOMP A.5, D.8 |
| H-10 | Cross-Stream-Pointer-Days | Tage (taegliche Detektionsserien, 79-Tage-Fenster) | DROP (GL-017) | **Daten**: N_pointer = 0, N-Floor (>= 3) gerissen | nein | **ja** im Datensinn: Neuauflage nur mit laengerem Fenster (KOMP D.9); Tageshistorie 5+ Jahre fuer Trades/Funding jetzt vorhanden [E] | KOMP A.5, D.9; REG2 H-10 |
| H-11 | AnEn-Vol vs HAR, CRPS | 3 Tage | WEITER (GL-022), danach entwertet | -- (Schwelle 0,05 war Faktor 4-5 zu niedrig; Dressing-Artefakt 0,21-0,29) | formal ja, durch H-11c entwertet | 3 Tage getestet; Wochen-Vol ungetestet | KOMP A.5, B.9 |
| H-11c | AnEn vs gedresste HAR | 3 Tage | DROP (GL-024) | **Nulleffekt**: CRPSS_dressed in 3/4 Zellen negativ, kein p unter 0,29 | nein | s. H-11 | KOMP A.5, B.10 |
| H-12 | Cross-Exchange-Fragmentierung (RMT) | Tagesmatrix aus Minutenbars | DROP (GL-018) | **Nulleffekt**: IPR 0,169 ~ 1/6 (vollstaendig delokalisiert) | nein | nein | KOMP A.5, D.10 |
| H-13 | Tail-Form GPD vs risikoneutral | Snapshot-Tage | GESPERRT (nie gelaufen) | **Daten**: braucht 2 vol-regime-disjunkte Tage, >= 12 Strikes | n/a | n/a | KOMP A.5, E.3 |
| H-14 | Cross-Venue-Lead-Lag-Graph (DL, 12 Nodes) | 10 s | METHODISCH INVALIDE (GL-020) | **Positivkontrolle**: 0/9 bekannte Kanten detektiert | nein (kein Verdikt) | **ja** (nur 10 s) | KOMP A.6, D.11, C.13 |
| H-15 | Trade-Tape-Grammatik (Transformer) | Tick-/Token-Skala | **WEITER** (GL-021) | -- ; Folge H-15b nie registriert (Entscheidungsrelevanz: bestes Ergebnis entscheidet nichts, PRD L-12) | **ja** | **ja** (nur Tick-Skala) | KOMP A.6, E.10; PRD Par. 2 L-12 |
| H-16 | Time-Arrow-CNN (Zeit-Irreversibilitaet) | Sekunden-Skalogramme | **WEITER**, korrigierte Lesart (GL-015 + Nachtrag) | -- ; 85-106 % des Effekts = Envelope-Asymmetrie (Leverage-Effekt), nicht Flussrichtung | **ja** | Envelope-Asymmetrie als Tages-Vol-Information ungetestet | KOMP A.6, B.12 |
| H-17 | Venue-Fingerprint (urspr.) | kein Preishorizont | VERDIKT AUSSTEHEND (GL-019) -> H-23 | **Daten**: n=2 Ueberlappungstage < 10-Floor | -> H-23 | n/a | KOMP A.6, E.4 |
| H-18 | Lead-Lag-Aufloesungs-Audit | wie H-04 | AUDIT-BEFUND (GL-014), kein Verdikt | -- (4 Zellen hart p<1e-5, 8 aufloesungsfragil) | (stuetzt H-04) | s. H-04 | KOMP A.6 |
| H-19 | DRIFT: Stationaritaet der Tape-Struktur | Kalenderzeit (Jahre) | BEFUND stationaer-genug (GL-025) | -- (META) | n/a | n/a | KOMP A.7 |
| H-20 | Tail-Aftermath nach 3,5-sigma-Stunden | 2-24 h | DROP (GL-026) | **Power** (ungeklaert): OOS-2 +17,3 bps erreicht, p=0,17; Vorzeichen instabil (BTC -16->+36, ETH +32->-12 bps); keine Power-Zeile | nein | **ja**: Tages-/Wochen-Aftermath nur deskriptiv (DEC-63/WP-11: Zerfall potenzgesetz-artig auf Tages-Skala), nie als Hypothese | KOMP A.7, D.12; PRD Par. 2 L-5; DEC-63 |
| H-21 | LIQ-TAG: Liquidations-Label | 30 min | GESPERRT bis 2026-12-27 | **Daten** (Kalenderzeit; Inventar zeigt 14 fehlende Tage, s. Abschnitt 5) | n/a | n/a | KOMP A.7, E.1; REG2 H-21; INV |
| H-22 | L2-Tilt -> Folgetag, BTC | 1 Tag | DROP (GL-027) | **Power** (ungeklaert) + Nulleffekt: IC +0,0665 / -0,0112 gegen 0,10; Vorzeichenwechsel (RETROCHECK_DEC52) | nein | 1 Tag getestet; Wochen und Alts ungetestet (L2 nur BTC/ETH ausreichend) | KOMP A.7, D.13; PRD Par. 3.5 |
| H-23 | Venue-Fingerprint, Voll-Distanzserie | kein Preishorizont | **WEITER** (GL-031) | -- (Pooled-Acc 0,8914; rho -0,414 gegen H-12) | **ja** | n/a | KOMP A.8, B.13 |
| H-24 | Impact-Persistenz, Minutenfluss | 30 min | DROP (GL-028) | **Nulleffekt**: IC30 in beiden Fenstern negativ (-0,0179/-0,0169), 10 Halbjahre stabil; Positivkontrolle bestanden | nein | Tages-Flusspersistenz ungetestet | KOMP A.8, B.14, D.14 |
| H-25 | Maker-Spread-Capture | Sekunden | NICHT registriert (WP-4, DEC-42) | **Friktion** (a priori): Spread = 1 Tick (0,016-0,054 bp), 75-255x unter Maker-Roundtrip 4 bp | n/a | nein (per Definition kurz) | KOMP A.10 WP-4, B.2, D.1; STRAT |
| H-26 | VRP auf Deribit (S- und K-Seite) | 30 Tage (RV_fwd30) | GESPERRT (R-1, DEC-98 E2) | **Daten**/Kalenderzeit; Power-Grenze ~3 unabhaengige Bloecke je 90-Tage-Fenster (REG2) | n/a | Horizont bereits Monat | KOMP A.9, E.2; REG2 H-26; DEC-98 E2, N4 |

**Auswertung T1** (Zaehlung des Kartierungsagenten [E] nach den Zeilen oben):

- Bindende Todesursache **Friktion:** H-04b, H-05c (Tradability-Gates), H-25 (a priori) = 3. **Nulleffekt:** H-01, H-03, H-05, H-06, H-08, H-09, H-11c, H-12, H-24 = 9.
  **Logik:** H-02, H-07 = 2 (H-05 teils). **Power (ungeklaert):** H-20, H-22 = 2. **Positivkontrolle:** H-14 = 1. **Daten:** H-10, H-17, H-13*, H-21*, H-26* = 5 (* gesperrt, nie gelaufen).
- **PRD-Lesart vs. Akte [F/E]:** PRD Par. 1 ("Der Pivot") fuehrt H-03, H-04b, H-05c, H-09, H-24 als "sechsmal dieselbe Friktions-Arithmetik ... alle 80-500x unter der Wand".
  Die Verdikte lauten bei H-03 (Surrogate-p ~1,0), H-09 (0/10 Zellen, Rauschen) und H-24 (negatives Vorzeichen, Positivkontrolle bestanden) auf Nulleffekt; nur H-04b und H-05c
  sind Friktions-Tode im engen Sinn. Die Aussage, Sekunden-/Minutenhorizonte seien wegen der Wand tot, ist fuer H-04/H-05b mit Messungen belegt (Einfang 0,03-0,19 bps), fuer die uebrigen Zeilen nicht.
- **Power:** PRD Par. 2 L-5 [F]: "26 Registrierungen ohne Power-Zeile; H-20 ... H-22 ... bleiben ungeklaert". Fuer alle DROP-Zeilen ohne Power-Zeile (H-08, H-20, H-22 u. a.) ist
  nicht unterscheidbar, ob "kein Effekt" oder "kein Nachweis" vorliegt. [F] Das DEC-52-Retro-Check-Ergebnis (RETROCHECK_DEC52, in PRD Par. 3.5): kein Verdikt kippt (H-06, H-20, H-22).
- **Zaehl-Inkonsistenz [F]:** KOMP-Kopf nennt "sieben kapitalfreie Mess-WEITER", nennt aber sechs (H-04, H-05b, H-11, H-15, H-16, H-23); PRD Par. 1 vermerkt die Diskrepanz.
  STAND Abschn. 1 / F2R zaehlen fuer die ersten 13 Verdikte 2 Mess-WEITER. Tradability-Folgetests existieren nur fuer H-04 und H-05b (beide PARK); fuer H-11, H-15, H-16, H-23 nie registriert (KOMP E.10).
- **Horizont-Bilanz [E]:** Von den Zeilen mit Sekunden-/Tick-Horizont (H-04, H-04b, H-05, H-05b, H-05c, H-14, H-15, H-16; darunter alle Mess-WEITER ausser H-11 und H-23) ist die Information auf Tages-/Wochenhorizont in allen 8 ungetestet;
  H-01 (Funding) liegt mit A1 auf Wochenhorizont in GL-012. Der Bestand `bybit/publicTrade` (5 Symbole, 5-6 Jahre) ist laut KOMP B.16 "der einzige bekannte Weg aus dem Horizont-Problem".

---

## T2. 3.0-Kandidaten A1-A5 und H-27..H-33

**Zuordnung A-Nummer <-> H-Nummer [F]:** A1 = H-31 (nicht registriert; REG3 "Vermerk H-31"); A3 = H-28/H-29/H-30 (Drittfassung, registriert) und seine beta-neutrale
Neufassung H-32 (registriert); H-27 = VRP (Klasse eroeffnet DEC-61, nicht registriert); H-33 = beta-neutrales Kurzfrist-Reversal (nicht registriert). A2, A4, A5 tragen keine H-Nummer.
Naechste freie Nummer: H-34 (REG3 "Vermerk H-33"). Welle 1 (Zensus WP-7/9/10/11/12, V-1..V-5) ist abgeschlossen (DEC-73); Alpha-Slots wurden verbraucht, ohne dass ein Test lief.

### T2.1 Klasse, Statistik, Fenster, Status

| Kandidat | Klasse | Urteilstragende Statistik | Fenster | Status (2026-11-01) | DEC / GL | Fundstelle |
|---|---|---|---|---|---|---|
| **A1 = H-31** Funding-Carry (DEC-70: Long-Bein D1 gegen Universums-Hedge) | P (Praemie) | Wochen-Gesamtrendite (Funding-Bein + Preisbein) D1 minus Universum; Residual-Alpha nach Orthogonalisierung | W1 2024-07-01..2025-06-30, W2 2025-07-01..2026-06-30 (PRD 5.1; ab DEC-99 (8) W2-Ende 2026-06-28) | **GL-012 vor der Registrierung** (GL-033, 2026-10-13); nicht registriert, kein K, kein Lauf | DEC-58 E3, 59, 67 E4, 70, 84, 93, 94; GL-033 | PRD 5.1; DEC-93; REG3 Vermerk H-31 |
| **A2** EXP-CLOCK (Verfallstag-Takt) | E (Ereignis) | Delta = Mittel r_pre (ln C[07:59]/C[07:29]) an Freitagen minus Placebo P2'' (Mo-Do 07:30-08:00 ohne Futures-Verfall); BTC/ETH gleichgewichtet; Placebos {P2'', P3fix, P3all}; Null = Label-Permutation Freitag<->Mo-Do je ISO-Woche | W1 2024-07-01..2025-06-30, W2 2025-07-01..2026-06-28 (DEC-103 E7) | **gesperrt**: ohne weiteren Schritt "GL-012 vor der Registrierung" (V-5b UNBELEGT); kein GL-Eintrag ("kein Gate-Ereignis"); Pilot-Route nur Vorlage, Entscheidung P-0..P-3 offen | DEC-58 E4, 59, 73 E3, 98 N5/N7, 103 (+N1) | PRD 5.2; DEC-103; HA2 PILOT_ROUTE_A2 Abschn. 8 |
| **A3 = H-28/H-29/H-30** (Kohorte F-XSEC1, Drittfassung) | W (Querschnitt) | Wochen-Roh-IC (Spearman): mom1, mom2, mom4, rev_gap (Gap-Design), vol_rv, vol_max, vol_beta; K = 7 | W1/W2 wie A1 (Drittfassung unveraendert, DEC-99 (8)) | **REGISTRIERT** 2026-10-12 (DEC-90, YAML sha256 bd948f34...c299); alle 7 Varianten **GL-012 vor dem Lauf** (GL-032); kein Lauf; p = 1 im BH-Nenner | DEC-73 E1, 74-78, 85-92, 94; GL-032 | REG3 H-28/29/30 + Nachtrag; DEC-90, 92 |
| **H-32** A3-fm8 (beta-neutral, Zweistufen) | W | fm_neutral_8w-Wochen-IC: mom1/mom2/mom4 (positiv), rev_gap (negativ); K = 4 | Pilot P 2022-04-18..2024-06-24 (nicht urteilstragend); Test W1/W2 | **REGISTRIERT** 2026-10-21 (DEC-101 T2, YAML sha256 0fadda78...bbd60); **Pilot einmal gelaufen -> GL-012 (Pilot) fuer alle 4 Varianten** (GL-035); kein Test, kein Verdikt; abgeschlossen (DEC-101 E11) | DEC-98 N2, 99, 100, 101 T1-T3; GL-035 | REG3 H-32 + Nachtrag |
| **H-33** Kurzfrist-Reversal (fm8, negative Richtung) | W | fm8-IC rev1, rev2, rev4 (1/2/4 Wochen); K = 3 | W1/W2 (REZENZ) | **GL-012 vor der Registrierung** (GL-036, 2026-10-27, Nutzer-Entscheid Option 1 = Default); kein K, kein Bau, kein Vorlauf | DEC-102 (+N1, N2); GL-036 | REG3 Vermerk H-33; H33 ENTSCHEIDUNGSVORLAGEN |
| **A4** Perp gegen datierten Future | P | Wedge w je Verfallzyklus (ex-ante-Terminzins minus akkumuliertes Funding), Test gegen w_null | >= 8 Quartalszyklen in zwei Haelften; noch kein Fenster fixiert | **gesperrt, RECORDING-FIRST** (DEC-59); Aufzeichnung (`rest.tickers15m`) seit 2026-10-20; Settlement-Pfad RAISED bis V-4 | DEC-59, 73 E3, 98 N4 (a) | PRD 5.4; DEC-59 |
| **A5** Skew-Praemie / Options-Block | P | 25d-Risk-Reversal, Halten bis Verfall; Schwelle aus gemessener Skew-Verteilung | keine | **GESPERRT** (Reihenfolge E.6: V-4, durchgaengiger Spread-Zensus, H-26 gemessen); keine Power-Rechnung | DEC-73 E3 | PRD 5.5; KOMP E.6 |
| **H-27** VRP auf DVOL-Backfill | P [E] | S1 = Fenstermittel (IV minus RV_fwd30, Bybit-Tagesschluss, BTC-Bein) minus Nullwelt-J | blinde Fenster W3/W4 ab 2026-07-01, Laenge L in {6, 9, 12} Monaten (DEC-96 E2); W1/W2 nur Aera-Profil | **GL-012 vor der Registrierung** (GL-034, 2026-10-17); nicht registriert | DEC-61, 94, 95, 96 (+N1-N3), 97; GL-034; DEC-98 N2, N5 | REG3 Vermerk H-27; DEC-97 |

### T2.2 Bindender Engpass (Zeit / Beleg / Daten / Power)

Datumsangaben "voll am" = Ende des zweiten Fensters bei bindender Nuisance, **bedingt** (Blind-Siegel, DEC-98 E1 (b); keine Zusage; BIL Teil A, Stand 2026-10-18 mit Errata).

| Kandidat | Zeit (bis wann) | Beleg (was fehlt) | Daten | Power / Zahl | Fundstelle |
|---|---|---|---|---|---|
| **A1** | theta = 1, W1-Spread, c = 1: 85 Wochen je Fenster -> voll **2030-01-06**; theta 0,77: 143 Wo. -> 2032-04-11; theta 0,5: 339 Wo. -> 2039; unter DEC-67 E4 jeweils x2,44; Start 2026-10-05 | **theta UNBELEGT** (nicht kompensierter Anteil des Funding-Vorteils); nahe Literatur ist Zeitreihen-Carry, kein Querschnitt (He et al.: 28 % des BTC-Perp-Carry aus Funding) | erfuellt (`rest.kline1d`, `rest.fundingRateAll` ab 2021-01-01, INV) | bei theta = 1: 3,168 x SE_gepoolt = **176,5 bp > prem 147,6 bp** (theta_min 1,196 unter DEC-67 E4); guenstigste Lesart theta_min 0,766; W1: MDE80 128,6 bp > prem 100,7 bp | GL-033; DEC-93 E1-E2; DEC-98 N2 (4); BIL 0 Pkt. 1, 2.7 |
| **A2** | keine Daten-Wartezeit (Historie ab 2020-03-25). [E] Fensterlaenge fuer Power 0,80 bei dem einzigen Prior 16,5 bp: ~24 Monate (zentral, MDE80prod 23,4 bp) bis ~30 Monate (stress 26,1 bp) je Fenster nach Wurzelgesetz (12 Monate x (MDE/16,5)^2); Akte: 16,5 bp "in keiner DEC-konformen Lesart testbar" auf 12-Monats-Fenstern (MDE80prod >= 22,8 bp) | **V-5b** Effektgroesse UNBELEGT (Weiss et al. FRL 2026: Fall vor Verfall nur bei hohem ATM-OI, keine bp-Zahl; Volltext nicht beschaffbar, Nutzer 2026-10-31). V-5c erledigt (TWAP 07:30-08:00 UTC primaer belegt) | 1m-Kerzen BTC/ETH vorhanden; **Negativ-Panel XRP/BNB(/SOL) 1m fehlt** (`rest.kline1m` nur BTC/ETH, INV) - Datenauftrag 2026-10-31 offen; Funding-Intervall BTC/ETH: 8h-Takt an allen 363 W2-Tagen gezaehlt (UEB Abschn. 13) | MDE80 je 12-Monats-Fenster: Einzel max 19,7 bp (P3fix), Produkt zentral 23,4 / 24,4, stress 26,1 / 27,2 bp; Pilot-Route: Uebergabeschwelle c_A2 = 32,1 bp (stress), Uebergabe-Wahrscheinlichkeit < 0,0001..0,027 bei 16,5 bp und 0,003..0,56 bei 25 bp (stress bis zentral, Kontrast- bzw. Ereignis-Skala; die Quelle nennt mehrere Lesarten) | DEC-103 E7, N1 (3)-(10); DEC-98 N2 (3), N7; STAND Nachtr. 2026-10-31 |
| **A3 (H-28..30)** | Roh-IC mom1 (W1-stress): 119 Wochen je Fenster -> voll **2031-05-11**; rev_gap 132 Wo. -> 2031-10-26; measured: 57 Wo. -> 2028-12-10. Die Wochenzahlen sind laut DEC-98 N3 obere Naeherungen (c_hat aus 45/44-Wochen-Simulation, Artefakt) | Prior IC 0,03 [sek] fuer breites Perp-Universum nicht gestuetzt (breit/gleichgewichtet ~0 oder negativ) | erfuellt; ABER A3-Fenster ab 2026-07-01 durch Blind-Siegel gesperrt bis zur Reihenfolge-Entscheidung | MDE80 W1 **0,042 (measured) / 0,060 (stress)** gegen Prior 0,03; Fenster-Power W1 0,47 / 0,21, W2 0,85 / 0,55 | GL-032; DEC-91, 92, 98 E1 (b), N2 (1), N3; BIL 0 |
| **H-32** | abgeschlossen; alternativ A3-fm8 auf blindem Fenster: 23 Wochen je Fenster -> 2027-08-22 (BIL, vor GL-035 und unter Siegel-Vorbehalt) | Prior = Pilot-Punkt (DEC-99 (6)); Literatur: Band 0,004..0,033, Vorzeichen haengt am Universum | erfuellt | Pilot x_P (in Richtung): mom1 -0,03847, mom2 -0,05003, mom4 -0,04463, rev_gap +0,01667 (t 1,53); Schwellen 0,0423 / 0,0458 / 0,0501 / 0,0363; MDE80 v6b W1: 0,0201 / 0,0228 / 0,0280 / 0,0185 | GL-035; REG3 H-32; BIL 2.7 |
| **H-33** | Alternative "blindes Fenster ab 2026-07-01": bei Literatur-Prior <= 0,0144 grob die siebenfache Fensterlaenge (DEC-102 N1 (11)); sonst keine Registrierung | **Prior UNBELEGT**: Literaturband fm8-Skala klein/illiquid +0,039..0,048; breit/gleichgewichtet ~0..+0,014; gross/liquide -0,015..-0,026 (Momentum); Universum ist nach Umsatz "liquide" (STAND 2026-10-29) | erfuellt (W1/W2 ungeoeffnet; W2 fuer rev1 nicht voll blind, Persistenz-Null) | Mindest-Prior fuer C10 (Lesart S): rev1 0,0395, rev2 0,0418, rev4 0,0431; MDE80 W1/W2 rev1 0,0395 / 0,0389 | GL-036; DEC-102 N1; H33 |
| **A4** | sigma_w fruehestens **2027-10-20** messbar, Registrierung dann; 4 Zyklen je Fenster [E] voll ~**2029-12-28** (BIL nannte 2029-06-29 bei Start 2027-06-16; +2 Quartalsverfaelle nach der Verschiebung DEC-98 N4 (a)); bei prior < 1,24 sigma_w entsprechend spaeter | **V-4** Delivery-/Settlement-Gebuehr (RAISE); Margin-Regeln (w_null) UNGEMESSEN; Prior UNBELEGT; sigma_w UNGEMESSEN | datierte Futures NICHT in `bybit/tickers`; nur `rest.tickers15m` (20 BTC/ETH-Kontrakte + 6 Perps, seit 2026-10-20); Illiquiditaet: turnover24h 45.000-530.000 USD | MDE80 = 2,4865 x sigma_w x sqrt(c/N); N_cluster = 8: 0,879 sigma_w (PRD 5.4); 1,243 sigma_w je Haelfte (BIL 2.5) | DEC-59; DEC-98 N4 (a); BIL 2.5; PRD 5.4 |
| **A5** | Kette E.6: (c) H-26 gemessen **fruehestens 2027-04-06** (DEC-98 N4 (b)); PASS "fruehestens 2027" (PRD 5.5) | **V-4** offen; (b) durchgaengiger Bybit-Options-Spread-Zensus nicht gebaut (Luecken-Karte geliefert 2026-10-20) | Options-Ticker erst ab 2026-06-16 (INV) = ~4,5 Monate; "reicht fuer kein urteilstragendes Fenster" (PRD 5.5); 14 Tage ohne Optionsdaten auf beiden Boersen, 9 weitere ohne Bybit | keine Power-Rechnung (Schwelle aus gemessener Skew-Verteilung, GL-012-Vorabcheck offen) | PRD 5.5; DEC-98 N4 (f); BIL 2.6 |
| **H-27** | Referenz L = 12: 672 Tage je Fenster, Prior 9,47 VP -> voll **2030-04-04**; Konsens-c 443 Tage -> 2029-01-03; mit Prior pi-2 7,14 VP: 1.182 Tage je Fenster (cc) -> **~2033-01** [E; STAND 2026-10-21: "eher 2033"]; Prior-Band 3,16..10,48 VP: 6.033..548 Tage | **VRP-Niveau-Prior**: 9,47 VP [sek] nicht gestuetzt; Almeida et al. v1 gibt 7,14 (BVIX-Route) bzw. 3,16 (Q-Dichte-Route); IV-Niveau der Literaturstichprobe UNBELEGT (P-9) | DVOL BTC/ETH lueckenlos 2021-03-24..2026-10-31 (INV); RV-Quelle Bybit-publicTrade-Tagesschluss | Referenz L = 12: **Fenster-Power 0,575, DEC-52-Gate 0,359**, MDE80 12,85 VP, SD 18,6 VP, c = 28,17 (Regel P-3); Hochfrequenz-RV bringt nichts (SD 18,6 VP, c 30,7..31,6; Option 3 geschlossen) | GL-034; DEC-97; DEC-98 N2, N5; STAND Nachtr. 2026-10-21 |

### T2.3 Fenster-Register: welche Fenster sind verbraucht oder blind (mit Datum)

| Fenster / Abschnitt | Status | Gilt fuer | Seit / Datum | Fundstelle |
|---|---|---|---|---|
| Pilotabschnitt 2022-04-18..2024-06-24 | **VERBRAUCHT** | jede mit dem fm8-IC korrelierte Statistik (gleiche Charakteristik-Familie, andere Neutralisierung, Formationslaenge oder Universum); ein weiterer Pilot dort zaehlt alle frueheren Varianten kumulativ in K | 2026-10-21 (GL-035) | DEC-99 (5); DEC-101 E11-E12; GL-035 |
| W1 2024-07-01..2025-06-30 und W2 2025-07-01..2026-06-28 | **ungeoeffnet / blind** fuer fm8-Momentum und fm8-Reversal; fuer jede andere Statistik "je Fall zu pruefen (C.17)" | A3-fm8, H-33, A2 (DEC-103 E7 "blind fuer A2") | GL-035, GL-036 (2026-10-21/27) | DEC-101 E12; GL-036; DEC-103 E7 |
| W1/W2 fuer **VRP** | **NICHT blind**: RV-Haelfte beider Fenster steht in der Akte (BTC-Wochen-SD 0,067 / 0,055, DEC-85), W2 zusaetzlich zwei DVOL-Stichpunkte (R3 K-36); nur Aera-Profil | H-27 und jede VRP-Hypothese | 2026-10-13 (DEC-96) | DEC-95 E2; DEC-96 E1 |
| W2 fuer **rev1** | **nicht voll blind** (richtungsgleicher Eigen-Autokorrelationsanteil aus der Persistenz-Null der Drittfassung); ein PASS dort waere nicht konfirmatorisch, ein DROP aussagekraeftig | H-33 rev1 | 2026-10-26 | DEC-102 N1 (7) |
| W1/W2 fuer **A1** | formationsseitig gesehen (K, Schluessel-Autokorrelation, Formations-Spread 174,0 / 336,3 bp/Woche, Halbwochen-Funding-Analog); keine Preisinformation, keine Outcome-Groesse ab 2024-07-01 | A1 | 2026-10-13 | GL-033; DEC-93 Feststellung |
| Vorperiode 2021-03-24..2024-05-31 (A2-Nuisance) | **Streuung gesehen; Blindheit nur noch durch Disziplin**: aus der committeten Vorarbeits-Datei laesst sich der Betrag des Vorperioden-Kontrasts auf zwei Kandidaten bestimmen (geschachtelte Klassen-Streuungen); Kombinationsverbot, kein History-Rewrite | A2-Pilot (Vorperiode wuerde bei Route P-1 verbraucht) | 2026-10-31 | DEC-103 N1 (1)-(2); STAND Nachtr. 2026-10-31 |
| Nuisance-Periode 2022-04..2024-06 (A1/H-27/Pilot) | Streuung und Autokorrelation gesehen; **Funding-Bein-Mittel implizit offengelegt** (phi x Spread ~83 bp/Woche, A1); WP-10(A2)-IV-RV-Serie 2021-03-24..2026-07-31 gebaut, nur Rangkorrelationen ausgewertet, Dateien ungeoeffnet | A1, VRP | 2026-10-13 | DEC-93 Feststellung (ii); DEC-94 A-5 (1); DEC-96 E3 |
| **Blindperiode ab 2026-07-01** (BTC/ETH-Vol, DVOL, Renditestreuung) | **unverbraucht, versiegelt** (DEC-96 E3); bis 2026-10-31 = 123 Tage [E]; offengelegt gesehen: Katalog-Metadaten `bybit/publicTrade` (Status/rows, 582-s-Pause 2026-10-08), Bytesummen, STRESS_ABS-Tag 2026-08-19 | VRP (zuerst), seit DEC-98 E1 (b) auch Klasse W und A1 (Kalibrierung, Betas, fm8 brauchen BTC-Renditestreuung), H-26 | 2026-10-13 / 2026-10-18 | DEC-96 E3; DEC-97 A-3; DEC-98 E1 (b) |
| A3-Fenster ab 2026-10-05 / VRP-Fenster ab 2026-07-01 | "Einmal-Gut": die erste Outcome-Rechnung verbraucht die Blindheit fuer alle spaeter registrierten Hypothesen derselben Groesse | alle | 2026-10-18 | DEC-98 E1 (d); BIL Teil C |
| Rohe IC-Niveaus WP-7 (`wp7_report.json`, `survivorship_bias_UNION_REAL.json`) | in Abweisungsliste kuenftiger Herleitungen (C.17) | alle Klasse-W-Herleitungen | 2026-10-26 | DEC-102 N1 (10) |
| H-21-Fenster W1 2026-07-01..09-28, W2 2026-09-29..12-27 (2.0-Registrierung) | **liegen vollstaendig in der Blindperiode** [V]: die Akte prueft den Konflikt mit DEC-96 E3 nicht; H-21 misst 30-min-Renditen von BTC/ETH (nicht Streuung/Niveau); Siegel-Wortlaut deckt "Renditestreuung", nicht "Mittel" - Auslegungsfrage | H-21 | -- | REG2 H-21; DEC-96 E3 |
| 2.0-Fenster (verbraucht, 2.0-Akte) | H-05b/H-05c OOS 2026-04-15 und 2026-05-15 (je 300.000 Ticks); H-09/H-12 W1 2026-03-27..05-15, W2 2026-05-16..07-04; H-24 zehn Halbjahre 2021-2026 | 2.0-Hypothesen (abgeschlossen) | 2026-06..08 | REG2 H-05b, H-09, H-12; KOMP A.8 |

---

## T3. Datenstroeme (Katalog-Stand 2026-11-01T11:48Z, 29 Stroeme; INV)

Zeitraum, Symbole, Groesse, Zeilen aus INV (nur `hd.catalog()`). "Genutzt von" = in der gelesenen Akte als Datenquelle benannt [F]. "Koennte nutzen, tut nicht" = Einschaetzung des
Kartierungsagenten [E], jeweils markiert; ein "tut nicht" heisst nur: in der gelesenen 3.0-Akte steht kein Kandidat darauf (die 3.0-Akte kennt die Stroeme teils nicht beim Namen).

| Strom | Zeitraum / Abdeckung (INV) | Symbole | Groesse | Genutzt von [F] | Koennte nutzen, tut nicht [E] | Fundstelle |
|---|---|---|---|---|---|---|
| `bybit/publicTrade` | 2020-03-25..2026-11-01; 10.519 Part.; Tage = Kalendertage (lueckenlos) | 5 (BTC ab 2020-03-25, ETH 2020-10-21, XRP 2021-05-13, SOL/BNB 2021-06-29) | 309,26 GB; 7,04 Mrd Zeilen | 2.0: H-03..H-10, H-12, H-14..H-17, H-19, H-20, H-22 (Rendite), H-23, H-24 (direkt oder via Bar-Cache WP-0); 3.0: STRESS_REL/ABS (Bar-Cache), WP-11, H-27 (RV aus Tagesschluss) | Tages-/Wochen-Fluss (signierter Umsatz, Trade-Groessenverteilung, Intraday-Profil) fuer 5 Symbole ueber 5-6 Jahre; kein 3.0-Kandidat nutzt Trades auf Tages-/Wochenhorizont, obwohl KOMP B.16 den Bestand als "der einzige bekannte Weg aus dem Horizont-Problem" fuehrt | KOMP B.16, F.1; PRD 3.3.10; DEC-96 N1; INV |
| `bybit/orderbook` | 2023-01-18..2026-11-01; BTC 1.043/1.384 Tage, ETH 612/1.384, SOL/BNB/XRP 117/131 (ab 2026-06-24); Luecken 2026-06-26, 07-06..07-16, 08-01 endgueltig | 5 | 377,14 GB; 1,43 Mrd | 2.0: WP-1/WP-2/WP-4, H-22 (BTC); 3.0: WP-10(B) Fill-Schatten (DEC-71) | Slippage-/Tiefe-Konstante je Symbol und Regime-Zustand des Buchs; nur 5 Symbole - fuer Alt-Slippage "prinzipiell nicht" ausreichend (R3-K-35) | KOMP F.1; DEC-71; PRD 9.1 R3-K-35; DA Abschn. 6 |
| `bybit/rest.kline1m` | BTC 2020-03-25..2026-10-31 (2.412/2.412); ETH 2021-03-15.. (2.057/2.057) | 2 | 0,28 GB; 6,43 Mio | A2-Vorarbeit (sigma30, Null; Renditen nur bis 2024-05-31), HF-RV-Nuisance (DEC-98 N5); A2-Test geplant | Kalender-/Slot-Effekte jenseits Verfall (Funding-Settlement 00/08/16 UTC, Tageszeit, CME-Fix-Fenster) fuer BTC/ETH; Negativ-Panel XRP/BNB/SOL fehlt (Datenauftrag 2026-10-31 offen) | DEC-98 N4 (d), N5; DEC-103 E5; INV |
| `bybit/rest.kline1d` | 2021-01-01..2026-10-31 (2.130/2.130); ALL; frueh 2021 H1 nur 5..16 Symbole/Tag (API) | ALL (~1.170 lineare Perps inkl. delistete, BEF21) | 0,04 GB; 0,72 Mio | A3 (H-28..H-30), H-32, H-33, A1 (Preisbein), WP-7/panel_1d, Delisted-Baum v2 (DEC-100 N1) | weitere Tages-Querschnittsfaktoren (Groesse, Illiquiditaet, Listungsalter, Delisting-Hazard, Wochentag); Vol-Anomalie ist H-30 (GL-012); 69 PARTIAL-Partitionen = Quellenluecken der Kerzenhistorie | DEC-66; DEC-100 N1; BEF21 Abschn. 1-3 |
| `bybit/rest.fundingRateAll` | 2021-01-01..2026-10-31 (2.130/2.130); ALL | ALL | 0,04 GB; 3,25 Mio | A1 (H-31), WP-7 (Funding-Zensus, V-1/V-6); A2-Vorarbeit nutzt Funding-Zeitstempel ohne Rate (Quelle in der Akte nicht benannt) | Funding als Charakteristik/Zustand fuer Klasse W; Intervallwechsel (Auto-Switch seit 2025-10-30) als natuerliches Experiment (DEC-58 E1 nahm nur den Zensus auf, RKD/Diff-in-Disc "nicht uebernommen") | DEC-58 E1, DEC-84; BEF21 |
| `bybit/rest.fundingRate`, `binance/rest.fundingRate` | Bybit 2024-03-01..; Binance 2026-03-19.. | je 5 Majors | je 0,00-0,01 GB | WP-10(A/A2) Funding-Kohaerenz (DEC-62/64/65) | Cross-Venue-Funding-Spread (5 Symbole, ~7 Monate); Bybit-Teil redundant zu `fundingRateAll` | DEC-62..65; INV |
| `bybit/rest.openInterest`, `binance/rest.openInterest` | Bybit BTC/ETH 2024-03-01..2026-10-31 (971/975, 973/975); SOL/BNB/XRP 2026-03-26..; Binance 2026-05-18.. | 5 Majors | Bybit 0,03 GB; 0,75 Mio | 2.0: H-10 (Delta-log-OI-Detektionsserien); **3.0: kein Kandidat in der Akte** | Leverage-/Positionierungs-Zustand (R3-K-34 LEV-STATE wurde mangels Rauschboden verworfen, PRD 9.1); OI-Aenderung als Zeitreihen- oder Querschnittsfaktor fuer 5 Symbole. PRD 7.2 Pkt. 3 fuehrte "OI-Tiefe" als kritischsten offenen Datenpunkt - INV beantwortet sie jetzt (BTC/ETH 2,6 Jahre) | PRD 7.2, 9.1; REG2 H-10; INV |
| `bybit/allLiquidation`, `bybit/insurance` | 2026-06-16..2026-11-01; allLiquidation BTC/ETH 125/139 Tage, SOL/BNB/XRP 117/131; insurance 125 Part. | 5 / 1 | je 0,01 GB; 0,16 Mio / 0,31 Mio | 2.0: H-21 (gesperrt) | Kaskaden-Zensus (R3-K-33 Stufe 1, "bewusst vertagt"); Stress-Definition jenseits Volatilitaet (STRESS_ABS ist vol-basiert); 4,5 Monate Tiefe | PRD 3.3.10, 9.1; KOMP E.12; REG2 H-21 |
| `bybit/tickers`, `bybit/tickers_1h` | 2026-06-16..2026-11-01 (tickers_1h bis 2026-10-30); ETH-Optionen ohne Frames 2026-08-22 08:00..08-27 08:00 (endgueltig); Universum 2026-08-23..26 ausgeduennt | 13.687 (Options-Instrumente + 5 Perps; keine datierten Futures, DEC-98 N4 (a)) | 504,61 GB; 12,40 Mrd / 0,30 GB; 2,8 Mio | Inhaltsprobe (DEC-98 N4 (a)); vorgesehen A5/H-26b | Bybit-Optionsflaeche (IV, Greeks, bid/ask, OI) fuer Skew/Term; **Perp-Universums-Spread/OI/Turnover-Zeitreihe fehlt** (PRD 7.2 Pkt. 2 nicht umgesetzt, Spreads nur Ein-Snapshot) | DEC-98 N4; DA Abschn. 6; PRD 7.2; STAND Abschn. 2 |
| `bybit/rest.instruments`, `bybit/delisting_dates` | 2026-10-20..2026-11-01 (13 Part.); **nicht nachladbar** | ALL | 0,00 GB; 26.455 / 4.414 Zeilen | PIT-Maske und Delisted-Baum (DEC-100), V-4(b) deliveryFeeRate (geplant) | Listing-/Delisting-Ereignisstudien, Funding-Cap-/Intervall-Parameter je Symbol; jeder Tag ohne Lauf ist irreversibel verloren (PRD 7.2 Pkt. 1) | DEC-100; DA Abschn. 2; PRD 7.2 |
| `bybit/rest.tickers15m`, `bybit/rest.deliveryPrice` | tickers15m 2026-10-20..; deliveryPrice 2021-06-25..2026-09-25 (119 Part.) | 26 Kontrakte / ALL | je 0,00 GB; 28.154 / 302 Zeilen | A4 (Aufzeichnung laeuft, kein Treiber) | -- | DEC-98 N4 (a); BEF21 |
| `deribit/dvol` | 2021-03-24..2026-10-31 (2.048/2.048 je Symbol, lueckenlos) | BTC, ETH | 0,01 GB; 98.304 | H-27, H-26 (gesperrt), WP-9, WP-10(A2), 2.0 H-10 (Zielserie) | DVOL als Tages-Regimevariable; unter Blind-Siegel ab 2026-07-01 keine Niveau-/Verteilungsstatistik | DEC-95, 96; GL-034; INV |
| `deribit/rest.settlements`, `rest.deliveryPrices`, `rest.instruments` | settlements BTC 2017-05-25.., ETH 2019-03-15.. (lueckenlos); deliveryPrices 2016-03-18..; instruments 2026-10-20..; Options-Deliveries in `settlements` enden 2026-07-31 (API-Eigenschaft) | BTC, ETH / ALL | je ~0,01-0,03 GB | A2 (Ereigniskalender, V-5a) | Preisfelder wurden fuer den A2-Zensus entfernt; Pinning-/Strike-Effekte: Max-Pain "empirisch mehrfach gescheitert" (PRD 5.2) | DEC-98 N5, N6; BEF21 |
| `deribit/publicTrade` | 2025-08-01..2026-11-01; BTC 251/457, BTC-PERPETUAL 251/458 Tage (rund 207 Kalendertage fehlen) | BTC, BTC-PERPETUAL, ETH, ETH-PERPETUAL (Inhalt "BTC"/"ETH" UNBELEGT) | 3,12 GB; 97,0 Mio | H-26 (RV-Quelle, gesperrt), 2.0 H-12/H-14/H-17/H-23 (Deribit-Perp) | Luecke begrenzt jede Fensterrechnung; ohne Inhaltsangabe kein Nutzungsvorschlag | KOMP F.1; DEC-98 N4 (b); INV |
| `deribit/tickers`, `deribit/markprice.options` | 2026-06-16..2026-11-01; markprice btc_usd/eth_usd 125/139 Tage | 16.714 (Options + Perps) / 2 | 542,12 GB; 12,05 Mrd / 8,76 GB; 0,93 Mrd | 2.0: H-13 (gesperrt); 3.0: A5-Datenplan | IV-Flaeche, Skew, OI je Strike (GEX); 4,5 Monate Tiefe, PRD 5.5 "reicht fuer kein urteilstragendes Fenster" | PRD 5.5; KOMP E.3 |
| `deribit/orderbook` | 2026-06-16..2026-11-01 (125/139) | BTC-/ETH-PERPETUAL | 4,39 GB; 53,6 Mio | keiner in der Akte | Cross-Venue-Liquiditaet Perp | INV |
| `binance/publicTrade`, `binance/orderbook` | Trades BTC 2025-01-01.. (610/669), Alts 2026-03-27.. (219/219); Orderbook 2026-03-26.. (bookDepth in Prozent-Buckets) | 5 | 46,23 GB; 3,26 Mrd / 0,54 GB; 27,8 Mio | 2.0: H-14, H-17, H-23, H-12 (Cross-Venue) | zweite Boerse fuer dieselben Coins bringt fuer A3 "<= -14 %, fuer gleiche Coins ~0" (BIL 2.8) | KOMP F.1; BIL 2.8 |
| `bitmex/publicTrade` | 2026-03-19..2026-09-16 (173 Part. bei 181 Kalendertagen; Strom endet oder pausiert, UNBELEGT) | XBTUSD | 0,17 GB; 5,19 Mio | keiner | tot: nur ~112-173 Tage statt der angenommenen 2014er-Historie | KOMP D.17, F.1 |
| `tardis/options_chain` | 2019-04-01..2026-10-01; **91 Partitionen = 1 Stichtag/Monat** (91 von 2.741 Kalendertagen) | "OPTIONS" (Boerse im Katalog nicht benannt, UNBELEGT) | 386,63 GB; 5,27 Mrd | keiner (KOMP D.17: "2 Tage, Options-Chain-Kandidaten endgueltig tot") | monatliche Optionsflaechen-Zeitreihe 2019-04..2026-10 (nicht ueberlappende Monatsziele, 7,5 Jahre, mehrere Regime) als **Pilot-Schaetzmaterial** fuer Skew-/VRP-Niveau-Priors nach DEC-99 (2a); Widerspruch zu KOMP F.1 ("2 Tage") ist in der Akte nicht aufgeloest; Regime-Archaeologie nach REZENZ | KOMP D.17, F.1; DEC-99 (2); INV |

### T3.2 Was fehlt (Universum, Boerse, Instrument, Zeitraum)

| Dimension | Fehlt | Beleg | Betroffen [E] | Nachbestellbar? [P] mit Richtung |
|---|---|---|---|---|
| Universum | Trades, L2 und 1m-Kerzen nur fuer 5 bzw. 2 Symbole; Alt-Intraday existiert nicht | INV; DEC-98 N4 (d); PRD 7.3 ("nicht machbar ... Tick-Analysen ueber ein breites Universum") | jede Klasse-W-Idee unter Tageshorizont; Alt-Slippage | 1m-Kerzen XRP/BNB/SOL bereits angefragt (Status offen); Richtung Testbarkeit |
| Universum | Zeitreihe von Spread, OI und Umsatz fuer alle Perps (nur Ein-Snapshot, Etikett `unter_wand`/B4) | STAND Abschn. 2; DEC-73 E4; PRD 7.2 Pkt. 2-3 | A1, A3 Kostenetikett; Slippage je Dezil | taeglicher Universums-Ticker-Strom (irreversibel, kein Nachladen); Richtung neutral |
| Boerse | Kein Spot (Bybit/Binance), kein Binance-Perp-Universum ("nicht: Binance-Panel", DEC-98 E3), kein CME/ETF, keine Makro-/Zins-/On-chain-/Stablecoin-Daten | INV (nur binance, bitmex, bybit, deribit, tardis); DEC-98 E3 | Zahler-Frage nach Spot-ETF-Start (PRD L-16) nicht pruefbar; Basis-Kandidaten ohne Spot-Bein | Spot-Tageskerzen, CME-Basis, Stablecoin-Fluesse: nur bei Bedarf eines registrierten Kandidaten; Richtung neutral |
| Instrument | Kein Index-/Mark-Preis-Kline, kein Premium-Index (nur als Delta in `tickers`), Bybit-Options-Trade-Tape unklar, keine datierten Futures vor 2026-10-20 | KOMP F.1; DEC-98 N4 (a) | A4 (Basis), DSM-03 (Funding-Premium, KOMP D.17) | Index/Premium-Klines per REST nachladbar [V]; Richtung Testbarkeit |
| Zeitraum | Optionen, Liquidationen, Insurance, Deribit-Book erst ab 2026-06-16; Binance-Alts ab 2026-03-27; Deribit-Trades 251 von 458 Tagen; OI/Funding(Majors) ab 2024-03 | INV | A5, H-13, H-21, H-26, Kaskaden | nur Kalenderzeit; Richtung -- |
| Zeitraum | Kein Datenstrom vor 2020-03-25 (Bybit), Tageskerzen nur ab 2021-01-01, 2021-H1 mit 5..16 Symbolen/Tag | INV; BEF21 Abschn. 2 | Regime-Tiefe fuer Klasse W (2 Jahre W1/W2 + Pilot 2022-04..) | extern (Quellenluecke der API, DEC-66); Richtung -- |

---

## T4. Regeln, die Wartezeit erzeugen

Entscheider-Spalte: **Orchestrator** = in der Akte vom Orchestrator beschlossen/ausgelegt; **Programmfrage** = PRD Par. 8 bzw. Nutzer hat entschieden oder wird gefragt. PRD Par. 8 selbst listet nur
drei Nutzerfragen (8.1 Ausfuehrung, 8.2 Kapital/Steuer/r_opp, 8.3 Sunset der Recording-Engine); Fehlerraten, Power, Fenster und Siegel stehen dort **nicht** [F]. Die Zuordnung unten folgt den DEC-Texten [F]
und ist an den markierten Stellen [E].

### T4.1 Die sechs genannten Regeln

| Regel | Wortlaut-Fundstelle (Kernsatz) | Was sie schuetzt | Welche Kandidaten sie wie lange blockiert (Datum) | Entscheider |
|---|---|---|---|---|
| **REZENZ** (C.18 / DEC-99) | DEC2 DEC-38 E4 (Welle 7, 2026-08): "urteilstragende Fenster muessen das juengste verfuegbare Regime abdecken; aeltere Historie darf ausschliesslich als deskriptives Aera-Profil mitlaufen"; KOMP C.18. DEC-99 (1) (2026-10-20): "Jede Registrierung hat ein urteilstragendes Fenster, das mit der letzten vollstaendigen Cluster-Einheit vor dem juengsten ergebnisblind nutzbaren Tag endet ... dieses Fenster muss bestehen"; (2) Altdaten nur vorab als Pilot-Schaetzfenster oder zusaetzliches Urteilsfenster; (8) W2 endet 2026-06-28 | Regime-Archaeologie: H-20-Vorzeichen kippt zwischen Aeren, H-22-IC lebt nur 2023/24, D3-Uebergang endet ~Mitte 2024 (DEC-38 E4) | Alle Kandidaten: die 5-6 Jahre Historie (KOMP B.16) koennen das juengste Fenster nie ersetzen, nur ergaenzen (Pilot oder Zusatzfenster, DEC-99 (2)); urteilstragend bleiben W1+W2 (24 Monate) bzw. blinde Fenster. H-27: nur Fenster ab 2026-07-01 -> voll **2030-04-04** (Prior 9,47) bis **~2033-01** (Prior 7,14) [E]; A3-Roh-IC **2031-05-11**; A1 **2030-01-06** (theta = 1); A2: Vorperiode nur als Pilot (Route P-1) | DEC-38 E4: Orchestrator. DEC-99: Orchestrator **mit Nutzer-Zustimmung 2026-10-20** (Anlass Nutzer 2026-10-18: "Wir koennen nicht bis 2027 warten ... andere Fenster waehlen"). Weitere Aenderung = Programmfrage |
| **Blind-Siegel** (DEC-96 E3) | DEC-96 E3 (2026-10-13): "Keine Niveau-, Streuungs- oder Verteilungsstatistik von DVOL (BTC/ETH) und keine realisierte Volatilitaet bzw. Renditestreuung von BTC oder ETH auf Tagen ab 2026-07-01 - auch nicht als Nebenprodukt anderer Pakete ... Erlaubt: Vollstaendigkeitspruefungen"; DEC-97: Siegel bleibt fuer jede kuenftige VRP-Hypothese; DEC-98 E1 (b): "Jede Klasse-W- oder A1-Rechnung auf Fenstern ab 2026-07-01 ist deshalb bis zu einer Reihenfolge-Entscheidung (...) gesperrt" | Ergebnisblindheit (C.17): die RV-Haelfte der VRP-Fenster stand in der Akte, dazu Vorwissen der Agenten bis Mitte 2026 (DEC-96 E1) | VRP/H-27-Nachfolger (zuerst), Klasse W und A1 auf Fenstern ab 2026-07-01 (DEC-98 E1 (b)), H-26 (DEC-98 E2: Lauf wuerde den blinden Bereich verbrauchen; gesperrt), A2-Outcomes ab 2026-07-01 (DEC-103 E7). Dauer: Wortlaut "bis zum registrierten H-27-Lauf" (DEC-96 E3) = ohne Datum; DEC-98 N5 (2): "Blind-Siegel E3 bis 2030..2033". Blinder Vorrat bis 2026-10-31: 123 Tage [E] | DEC-96 E3: Orchestrator (vor jeder Zahl). **Reihenfolge der Blindperiode = Programmfrage des Nutzers, offen** (DEC-98 E4 (b); STAND Nachtraege bis 2026-10-31 "Offen bei dir") |
| **Einmal-Gut** | BIL Teil C: "Die blinden Fenster sind ein Einmal-Gut ... Die erste Hypothese, die auf ihnen laeuft (auch H-26, 2.6), verbraucht die Blindheit fuer alle anderen derselben Groesse." DEC-98 E1 (d): "Blindheit gilt je Zeitabschnitt; alle Hypothesen, die VOR der ersten Rechnung auf dem Abschnitt registriert sind, teilen ihn. Ein H-26-Lauf zuerst kostet einen VRP-Nachfolger ~139 blinde Tage, nicht die Fenster." DEC-99 (5) fuer Pilotabschnitte | Konfirmatorik: eine zweite Statistik auf bereits gerechneten Daten ist nicht konfirmatorisch (C.17) | Konkurrenz um den Vorrat ab 2026-07-01: VRP-Nachfolger vs H-26 vs Klasse W vs A1; H-26 liegt (2.0-Lesart) mit dem zweiten Fenster vollstaendig im Blindbereich (BIL 2.6). Bis zur Reihenfolge-Entscheidung rechnet niemand dort | Auslegung: Orchestrator (DEC-98 E1 (d), Review B-4 angenommen). **Zuteilung = Programmfrage (Nutzer), offen** |
| **Zwei-Fenster-Regel** (C.10 / DEC-52) | KOMP C.10 (PRD 2.0 Par. 8.5): "Verfehlt eine Schwelle in EINEM von >= 2 disjunkten Fenstern, ist das DROP/PARK - unabhaengig davon, wie stark andere Fenster performen." DEC-52 (PRD 3.5): Zweig nur bei Per-Fenster-Power < 0,6, gepoolt alpha 0,01. DEC-94 (6): "Fenster-Power >= 0,80 in jedem urteilstragenden Fenster -> C.10 hart. Sonst DEC-52-Zweig, wenn die Power des vollstaendigen DEC-52-Gates >= 0,80 ist ... Sonst GL-012" | Regime-Robustheit (PRD 3.5 (a)) und niedrige Gesamt-Fehlerrate (C.10 gemeinsam 0,05^2 = 0,25 % unter P-1, DEC-94 Etikett) | Alle Kandidaten. Preis: +26 % Daten bei gleicher Gesamtrate und Power 0,80 (DEC-98 E1 (c), "kein Zeitfresser" zurueckgenommen); DEC-52-Gate +9,5 % gegenueber C10 bei zwei gleichen Fenstern (BIL 0 Pkt. 2). Ein Fenster (alpha 0,05) wuerde vorziehen: A3-Roh-IC 2031-05-11 -> 2029-01-21, VRP 2030-04-04 -> 2028-06-01, A1 2030-01-06 -> 2028-05-21 (BIL Option 4, O3; Fehlerrate x20) | C.10: Verfassung (Programm 2.0). DEC-52/DEC-94: Orchestrator ("Verbesserung" bzw. "Lockerung"; DEC-94 nennt keine Nutzer-Zustimmung [F]). Programmweite Aenderung ("Option 4") = Programmfrage; DEC-98 E4 und DEC-99 (9) schliessen sie als Default aus |
| **Power-Ziel 0,80** | DEC-51 (2): "Power-Ziel 0,80 fuer den in der Power-Zeile benannten Mindesteffekt ... liegt die A-priori-Erwartung darunter, ist die Registrierung ein GL-012-Fall (Feasibility-DROP vor dem Lauf) oder braucht ein anderes Design." DEC-94 (3): "Eine SE fuer Test und Power" | Trennung "kein Effekt" / "kein Nachweis" (PRD L-5); ein DROP bleibt informativ (bei Power 0,5 je Fenster verwirft C.10 drei von vier echten Effekten, K-0.6) | Direkt GL-012: A3 (GL-032, 2026-10-12), A1 (GL-033, 2026-10-13), H-27 (GL-034, 2026-10-17), H-33 (GL-036, 2026-10-27); A2 (V-5b, MDE80 18-27 bp gegen 16,5 bp). Gemeinsame Power zweier Fenster mit je 0,80 ist 0,64 (BIL Option 4, O0). Preis einer Absenkung (BIL, O1, Power 0,5 je Fenster; gemeinsame Power 0,25, DROP uninformativ): A3-Roh-IC 2028-10-15, VRP 2028-03-11, A1 2028-03-19, A3-fm8 2027-02-21 | DEC-51: Orchestrator ("reine Vergleichbarkeit"). Aenderung nach Kenntnis der Kandidaten = Torpfosten (DEC-93 E3, DEC-97); programmweit = Programmfrage |
| **12-Monats-Fenster** (DEC-96 E2 / PRD) | PRD 5.1/5.3: W1 2024-07-01..2025-06-30, W2 2025-07-01..2026-06-30 ("je 52 Wochen"); PRD 5.2 Gate: "beiden urteilstragenden 12-Monats-Fenstern". DEC-96 E2: "Laenge L in Monaten aus {6, 9, 12}: gewaehlt wird das kleinste L, fuer das power_p1.assign_regime (...) C10 oder DEC52 ergibt; ist auch L = 12 GL012, ist H-27 GL-012 vor der Registrierung." DEC-97: "Fenster ueber 12 Monate sieht DEC-96 E2 nicht vor; sie jetzt einzufuehren waere eine Entscheidung nach Kenntnis dieser Feasibility und ist ausgeschlossen." BIL Option 1: Fassungen ueber 12 Monate = "NEUE Hypothese mit Etikett 'Fensterlaenge beschlossen nach Kenntnis von GL-032..034'" | Vorab fixierte Fensterlaenge (Torpfosten-Schutz, nur Nuisance, DEC-96 E2). **Eine Herleitung der Zahl 12 steht in den gelesenen Stellen nicht** [F: nicht gefunden] | H-27: L = 12 -> Fenster-Power 0,575, DEC-52-Gate 0,359 -> GL-012 (GL-034); C10 braeuchte >= 672 Tage je Fenster (voll 2030-04-04). A2: MDE80 18,25-27,2 bp je 12-Monats-Fenster. A4: >= 12 Monate Quote-Aufzeichnung (DEC-59) -> registrierbar fruehestens **2027-10-20** (nach DEC-98 N4 (a)). C-33/H-26b: >= 12 Monate IV-Recording mit Stress -> "fruehestens Mitte 2027" (KOMP E.7) | Orchestrator (DEC-96 E2 vor jeder Zahl; PRD-Fenster aus Herleitung). Laengere Fenster = neue Hypothese mit Etikett "Testbarkeit nach Kenntnis" -> Orchestrator mit Nutzer-Information [E]; keine Nutzerfrage nach PRD Par. 8 |
| **Pilot-Verbrauch** (DEC-99 (5)) | DEC-99 (5): "Nach dem Pilot ist der Pilotabschnitt programmweit fuer jede Statistik, die mit einer dort gerechneten korreliert (gleiche Charakteristik-Familie, andere Neutralisierung, Formationslaenge oder Universum), nicht mehr blind; ein weiterer Pilot auf demselben Abschnitt zaehlt alle frueheren Pilot-Varianten kumulativ in K"; (3) "genau ein Pilotlauf" | Screening nie Konfirmation (C.17/C.18); Selektions-Inflation | Pilotabschnitt 2022-04-18..2024-06-24 unbefristet verbraucht fuer fm8-korrelierte Statistiken (seit GL-035, 2026-10-21): H-33 kann dort keinen Pilot haben (DEC-102 E2). A2-Route P-1 wuerde die Vorperiode 2021-03-24..2024-05-31 verbrauchen: Uebergabe-Wahrscheinlichkeit < 0,0001..0,027 bei 16,5 bp, danach "A2 endet in GL-012 (Pilot)" (DEC-103 N1 (10)) | DEC-99: Orchestrator **mit Nutzer-Zustimmung 2026-10-20**. Anwendung auf A2: **Nutzer entscheidet (P-0..P-3, offen)** |

### T4.2 Preis der Regeln in Kalenderdaten (BIL Teil C Option 4, Stand 2026-10-18, bedingt; Fakten, keine Empfehlung)

"voll am" je Kandidat, zwei Fenster, bindende Nuisance, zentraler Prior; Start A3/A1 2026-10-05, VRP 2026-07-01. Jede Zeile ausser O0 waere eine Regelaenderung nach Kenntnis der Kandidaten (Torpfosten, DEC-93 E3/DEC-97). BIL
selbst: "NICHT empfohlen". Spalte Richtung nach BIL.

| Variante | Daten relativ | Fehlerrate gemeinsam | A3-Roh-IC | A3-fm8 | A1 (theta 1) | VRP | Richtung |
|---|---:|---:|---|---|---|---|---|
| O0 geltend (P-1) | 1,00 | 0,25 % | 2031-05-11 | 2027-08-22 | 2030-01-06 | 2030-04-04 | -- |
| O1 Power-Ziel 0,50 je Fenster | 0,44 | 0,25 % (Power gemeinsam 0,25) | 2028-10-15 | 2027-02-21 | 2028-03-19 | 2028-03-11 | Testbarkeit |
| O1 Power-Ziel 0,70 | 0,76 | 0,25 % (Power 0,49) | 2030-03-31 | 2027-06-13 | 2029-04-01 | 2029-05-19 | Testbarkeit |
| O2 alpha 0,10 je Fenster | 0,73 | 1,0 % (x4) | 2030-02-17 | 2027-05-30 | 2029-02-18 | 2029-04-05 | Testbarkeit |
| O3 ein Fenster, alpha 0,05 | 0,50 | 5,0 % (x20) | 2029-01-21 | 2027-03-14 | 2028-05-21 | 2028-06-01 | Testbarkeit |
| O4 ein Fenster, alpha 0,01 | 0,81 | 1,0 % (x4) | 2030-06-23 | 2027-06-27 | 2029-05-27 | 2029-07-25 | Testbarkeit |
| O5 ein Fenster, alpha 0,0025 | 1,08 | 0,25 % | 2031-09-07 | 2027-09-19 | 2030-04-07 | 2030-07-16 | neutral |
| O6 gemeinsame Power 0,80 | 1,36 | 0,25 % | 2032-12-19 | 2027-12-12 | 2031-03-02 | 2031-07-26 | Strenge |
| O7 A3-Praxis (Schwelle 2,4865 SE) | 1,79 | 0,0042 % | 2034-12-17 | 2028-04-30 | 2032-08-01 | 2033-03-03 | Strenge |

Quelle aller Zeilen: BIL Teil C, Option 4 (Tabelle). Die A3-fm8-Spalte ist durch GL-035 (Pilot, kein Test) und GL-036 ueberholt [F]; sie zeigt nur den Regelpreis. A3-/A1-Daten gelten nur nach Aufhebung der Siegel-Sperre
(DEC-98 E1 (b)).

### T4.3 Weitere Wartezeit-Regeln (nicht im Auftrag genannt, in der Akte wirksam)

| Regel | Wortlaut-Fundstelle | Wirkung (Kandidat, Datum) | Entscheider |
|---|---|---|---|
| **UNBELEGT blockiert (RAISE)** | CLA3 Arbeitsregel 4: "Fehlendes heisst UNBELEGT und blockiert die abhaengige Konstante (RAISE), nie ein Default."; DEC-102 E3 | A1 (theta), A2 (V-5b), H-33 (Literatur-Prior), A4 (V-4, sigma_w), A5 (V-4); Dauer unbestimmt, haengt am Zugang zu Volltexten (Egress gesperrt, Volltexte kostenpflichtig, DEC-103). Umgehung nur ueber Pilot-Schaetzfenster (DEC-99) | Verfassung (Orchestrator); Pilot-Route = Programmfrage |
| **Neue Hypothese statt Neufassung** | DEC-92 E2: "keine Viertfassung mit DEC-52"; DEC-58 E2: Zensus darf nie promoten, "eigenes K"; DEC-94: "Nicht rueckwirkend ... kein Rueckzug und keine Neufassung von H-28..H-31" | A3-Drittfassung und A1 bleiben GL-012, obwohl die spaetere Lockerung P-1 (DEC-94) sie testbarer gemacht haette; Folge H-32 (Neu-Hypothese, 9 Tage bis zum Pilotbefund, 2026-10-12..21) | Orchestrator (Sequenz-Zwang DEC-52) |
| **Recording-first / Mindestaufzeichnung** | DEC-59 (A4): "nicht gestrichen, erst nach >= 12 Monaten Quote-Aufzeichnung registrierbar"; KOMP E.7 (C-33) | A4 **2027-10-20** (sigma_w), Urteil ~2029-12-28 [E]; H-26b/C-33 Mitte 2027 | Orchestrator |
| **H-26-Entsperrung (done_days)** | REG2 H-26: lueckenlose `done_days` fuer dvol UND publicTrade je Symbol ueber >= 210 zusammenhaengende Tage (sinngemaess); DEC-98 E2/N4 (b): R-1, Lesart offen | Lesarten: Manifest-DONE 210 Tage am 2026-10-22 (durch PRD 4.2 ausgeschlossen); dvol DONE + Perp live Luecke <= 60 min **2027-04-06**, <= 30 min **2027-05-11**; zusaetzlich Blind-Konflikt | Orchestrator; Luecken-Grenze mit der Reihenfolge-Entscheidung (Nutzer) |
| **Genau ein Pilotlauf** | DEC-99 (3); DEC-101 E3, E9a (technische Sperre, Versuchsmarker) | H-32 kein zweiter Pilot moeglich; Neulauf nur per DEC bei Code-/Datenfehler | Orchestrator mit Nutzer-Zustimmung (DEC-99) |

### T4.4 Einschaetzungen zu T4 (Urteile, nicht Fakten)

1. **[E] Zusammenspiel statt Einzelregel.** Jede Regel ist einzeln begruendet; das Produkt (Power 0,80 je Fenster x zwei Fenster x 12-Monats-Cap x REZENZ x Siegel x Einmal-Gut) erzeugt die Daten
   2027-08 bis 2033 (T4.2). Die Akte rechnet nur die Regelvarianten O1-O7 (BIL), nicht die Frage, welche *Kombination* der Regeln den Hauptteil der Wartezeit erzeugt. Eine Zerlegung (z. B. Beitrag
   der REZENZ-Fenster allein) steht nicht in der Akte.
2. **[E] Zustaendigkeit uneinheitlich.** DEC-94 erhoehte die Fenster-Fehlerrate (0,0064 -> 0,05, x7,75; C.10 gemeinsam 4,2e-5 -> 2,5e-3, x60) als Orchestrator-Beschluss "Lockerung", DEC-99 loeste REZENZ nach Nutzer-Zustimmung; PRD Par. 8 benennt keine
   Zustaendigkeit fuer Fehlerraten/Fenster. [P, neutral] In PRD Par. 8 aufnehmen, welche Regelklassen (Fehlerrate, Power-Ziel, Fensterlaenge, Siegel) Programmfragen sind.
3. **[E] 12-Monats-Cap ohne Herleitung.** Die Laenge 12 Monate wird in den gelesenen Stellen nicht hergeleitet (DEC-96 E2 setzt das Menue {6, 9, 12}). [P, neutral] Herleitung nachtragen (Saisonalitaet? Kalenderraster?), bevor sie als
   Regel fuer weitere Kandidaten gilt; ein Wechsel von "Fenster-Cap" auf "Kalenderzeit abwarten" aendert keine Fehlerrate (Richtung neutral, Preis: Wartezeit).
4. **[E] Einmal-Gut laesst Teilung zu.** DEC-98 E1 (d) erlaubt, dass vor der ersten Rechnung registrierte Hypothesen einen Zeitabschnitt teilen. [P, Testbarkeit mit Selektionspreis] Mehrere VRP-/Klasse-W-
   /A1-Hypothesen vor der naechsten Rechnung gemeinsam registrieren (K steigt, Siegelkonflikt faellt weg) - das wuerde die Reihenfolge-Frage (Nutzer) entschaerfen.
5. **[E] Siegel-Erosion.** DEC-103 N1 (2) zeigt, dass die Blindheit der A2-Vorperiode nur noch an Disziplin haengt (Kanal ueber geschachtelte Streuungen in der oeffentlichen JSON). [P, Strenge] Struktur-Scan
   als Pflichtpunkt jedes Reviews (beschlossen, DEC-103 N1 (2)(c)) auf alle bereits committeten Nuisance-Dateien ausdehnen.

---

## 5. Offene Faeden (KOMP Abschnitt E) mit heutigem Status

Status: **erledigt** / **offen** / **ueberholt**. Stand der Pruefung: 2026-11-01. Wo die 3.0-Akte einen Faden nicht erwaehnt, steht "nicht nachgefuehrt" (Suche ueber die gelesenen 3.0-Dateien und `scinance3-impl/**/*.md` per Stichwort).

| KOMP E | Faden (Stand KOMP, 2026-09-02) | Heutiger Status | Beleg / Begruendung |
|---|---|---|---|
| E.1 | H-21 LIQ-TAG gesperrt bis 2026-12-27 (zwei 90-Tage-Fenster 2026-07-01..09-28, 09-29..12-27, lueckenlose `done_days`) | **offen, nicht nachgefuehrt** | Keine Erwaehnung in DEC-51..103, STAND, BIL, PRD Par. 5. INV: `allLiquidation` BTC/ETH 125 von 139 Kalendertagen (14 fehlen). [V] Die Zahl 14 stimmt mit den in DA Abschn. 6 genannten Ausfaellen ueberein (2026-06-26, 07-06..07-16, 08-01, 08-14: 1+11+1+1); wenn sie in W1 liegen, ist die Bedingung "lueckenlos" nicht erfuellbar. [V] Beide Fenster liegen vollstaendig im Blind-Siegel-Zeitraum (DEC-96 E3); die Akte prueft den Konflikt nicht |
| E.2 | H-26 VRP Deribit gesperrt bis ~Mitte November 2026 | **ueberholt, weiter gesperrt** | DEC-98 E2: bleibt gesperrt (Default R-1). DEC-98 N4 (b): Entsperrdatum nach Lesart 2027-04-06 (Luecke <= 60 min) bzw. 2027-05-11 (<= 30 min); `deribit/dvol` wird nie live gesammelt (nur REST), `deribit/publicTrade` live erst ab 2026-06-16; Manifest-DONE-Lesart (210 Tage am 2026-10-22) durch PRD 4.2 ausgeschlossen. Zweites H-26-Fenster laege im Blindbereich (BIL 2.6) |
| E.3 | H-13 Tail-Form GPD/RND, kein festes Datum | **offen** | Nicht nachgefuehrt in der 3.0-Akte. INV: `deribit/markprice.options` btc_usd/eth_usd 125/139 Tage (KOMP: 43 Tage am 2026-08-10); die Bedingung (2 vol-regime-disjunkte Tage, >= 12 Strikes) wurde nicht neu geprueft |
| E.4 | H-17 durch H-23/GL-031 aufgeloest | **erledigt** | KOMP A.6/A.8; append-only Eintrag bleibt |
| E.5 | SWEEP-PRE (V-01) / WP-3 L2-Sweep-Extraktion, nicht registriert | **offen, nicht aufgegriffen** | DEC2 DEC-38 E3 ("billig ist kein Registrierungsgrund"); in der 3.0-Akte nur in R3 (Recherche), nicht in PRD/DEC |
| E.6 | H-26b Options-VRP-Tradability: erst (a) Delivery-Gebuehr, (b) durchgaengiger Spread-Zensus, (c) H-26 gemessen | **offen** | (a) V-4 offen (PRD 4.4, DEC-73 E5); (b) Zensus nicht gebaut, Luecken-Karte geliefert 2026-10-20 (DEC-98 N4 (f)); (c) H-26 gesperrt. Reihenfolge gilt ebenso fuer A5 (PRD 5.5) |
| E.7 | C-33: >= 12 Monate IV-Recording mit Stress, unabhaengig von H-26 | **offen (Uhr laeuft)** | PRD 4.2: WP-9 "entsperrt H-26 NICHT und erfuellt die C-33-12-Monats-Uhr NICHT"; KOMP E.7: fruehestens Mitte 2027 |
| E.8 | ETH-Optionen-Luecke 2026-08-22 08:00..08-27 08:00 UTC, endgueltig verloren | **erledigt (bestaetigt)** | DA Abschn. 6 ("endgueltig; BTC lief durch"); Folgeluecken-Karte DEC-98 N4 (f) |
| E.9 | Bybit-native Options-Bid/Ask-Historie vor 2026-08-24 unverifiziert | **ueberholt** | DEC-98 N4 (f): Felder vollstaendig (bid/ask, IV, Greeks), Luecken-Karte; INV: `bybit/tickers` erster Tag 2026-06-16, davor existiert keine Optionshistorie im Katalog [E] |
| E.10 | Nicht registrierte Folge-Hypothesen (H-04c, H-05d, H-07b, H-09b, H-10b, H-11b, H-12b, H-13b, H-15b, H-16b, H-17b, H-20b, H-24b) | **offen, unveraendert nicht registriert** | REG3 enthaelt nur H-28..H-33 und Vermerke; kein Eintrag zu den Folge-Hypothesen. PRD 2 L-12: H-15b/H-16b ausdruecklich "NICHT registriert" |
| E.11 | GPU-Folgekandidaten DSM-02, DSM-04 (nie registriert) | **offen, praktisch ueberholt** [E] | Nicht in der 3.0-Akte; DEC-57 (PRD 3.7): GPU-Budget je Hypothese 0, ein GPU-Lauf braucht registrierte Begruendung und Entscheidungsrelevanz mit Tradability-Pfad |
| E.12 | Kaskaden-Module C-27/C-28/C-29/C-39/C-30 (CS-06) im PARK-Register | **offen, nicht aufgegriffen** | PRD 9.1: R3-K-33 X-PULL Stufe 2 verworfen, Stufe 1 (binaerer Zensus) "bewusst vertagt, Neubewertung nach WP-7" - keine Neubewertung in DEC-51..103 gefunden. Daten: `allLiquidation`/`insurance` ab 2026-06-16 (INV) |
| E.13 | C-40, C-02, C-43 im PARK-Register; C-36-Recording-Engine / Sunset-Review | **offen** | PRD 8.3: Sunset-Review "faellig seit ~2026-09-11, nie gelaufen"; CLA3 Schutzgut: Recorder laeuft "bis die Sunset-Review entschieden ist"; BIL Option 5 nennt sie als faellig; kein DEC mit Sunset-Entscheid in DEC-51..103 gefunden (Stichwortsuche). Programmfrage des Nutzers (PRD Par. 8.3) |

### 5.2 Offene Faeden aus 3.0 (nicht im Kompendium)

| Faden | Wer entscheidet | Stand | Fundstelle |
|---|---|---|---|
| Reihenfolge der Blindperiode (VRP zuerst / Klasse W zuerst / Teilung); beeinflusst Siegel-Preis ("bis 2030..2033"), H-26, Lueckengrenze fuer H-26 | **Nutzer** | offen seit 2026-10-18; STAND Nachtr. 2026-10-31: "Weiterhin offen bei dir" | DEC-98 E4 (b), N5 (2); DEC-102 N2 |
| A2-Vorlage P-0 (Default: nur vorbereiten) / P-1 (Pilot-Route, Lockerung) / P-2 (A2 ruht) / P-3 (blindes Fenster) | **Nutzer** | offen seit 2026-10-31; bis Antwort P-0, kein Code-Bau | DEC-103 N1 (10); UEB Abschn. 13 |
| Datenauftrag Negativ-Panel (1m-Kerzen XRP/BNB/SOL 2021-03-24..2026-06-28) an Data-Harvest weiterleiten | **Nutzer** (weiterleiten) | offen seit 2026-10-31; ohne die Daten fehlt A2 Gate-Bedingung (4) | DEC-103 E5; STAND Nachtr. 2026-10-31 |
| Belege: V-5b (A2-Effektgroesse), theta (A1), VRP-Niveau-Prior (Band 3,2..10,5 VP), Universums-Zuordnung (A3-/H-33-Prior), V-4 (Liefergebuehr); PDF-Nachlieferung (Liu/Tsyvinski/Wu, Weiss et al. u. a.) | Nutzer (Beschaffung) / Orchestrator (Auswertung) | offen; Volltexte aus der Cloud nicht erreichbar | DEC-98 N1-N2; DEC-102; STAND Nachtr. 2026-10-27 |
| PRD Par. 8.1 Ausfuehrung (Default (b)), 8.2 Kapitalbasis/Steuer/r_opp, 8.3 Sunset | **Nutzer** | keine Antwort in der gelesenen Akte; Defaults gelten ("blockieren keinen Welle-1-Schritt") | PRD Par. 8 |
| Siegel-Kanal A2-Vorperiode (Betrag des Kontrasts aus geschachtelten Streuungen ableitbar) | Orchestrator | festgestellt 2026-10-31; kein History-Rewrite, Kombinationsverbot | DEC-103 N1 (2) |
| DEC-93-Merkposten (c) WP-7 Null-Auffuellung (Funding-Autokorrelation nach oben verzerrt), (d) Sonderpaare I = 0; DEC-94 "nicht Teil von P-1": Stress-N_eff (DEC-65 (2)), stratifizierter Bootstrap | Orchestrator | vermerkt, nicht behoben | DEC-93; DEC-94 |
| Data-Harvest-Rueckmeldungen (Panel, Settlements) | -- | **erledigt** ("Keine Rueckfrage mehr offen") | STAND Nachtr. 2026-10-26 |

---

## 6. Grenzen dieses Faktenblatts

- **Gelesen:** KOMP vollstaendig; PRD Par. 1-3, 5, 7-9, 11 (Par. 4 nur Struktur, Par. 6/9.2/10 nicht); CLA3; DEC-51..53, 58, 59, 73, 90-103 im Wortlaut, DEC-60..89 nur Titel und die in DEC-93..103 zitierten Teile;
  GL-032..036 vollstaendig; REG3 Kopf, H-32-Block, Vermerke H-27/H-31/H-33 (Drittfassung H-28..H-30 nur ueber GL-032/DEC-90..92); BIL Abschn. 0-1, 2.5-2.8, Teil C (Option 1, 2, 4, 5); STAND vollstaendig;
  UEB Abschn. 1-3, 13; Herleitungsordner nur Kopfzeilen (Inhalt ueber die DEC-Nachtraege); F2R, W6, STRAT; INV vollstaendig; DA Abschn. 1-7; REG2 per Stichwortsuche (Horizonte).
- **Nicht gelesen:** Review-Dateien im Wortlaut, Vorlauf-/Nuisance-JSON, PRD Par. 4/6/10, REG2 im Volltext, DEC2 ausser DEC-38; keine Siegeldatei, kein Harvest-Client, keine Datenrechnung.
- **T1:** die Spalte "Klasse" und die Aufteilung der Todesursachen nach dem 6er-Raster sind teilweise Urteile [E]; die Akte selbst verwendet dieses Raster nicht. "Horizont-abh." ist [E], ausser wo ein DEC/GL die Aussage traegt.
- **T2:** "voll am"-Daten sind bedingte Rechnungen der BIL (Stand 2026-10-18 mit Errata); DEC-98 N3 (obere Naeherungen A3), N5 (HF-RV) und GL-035/036 haben einzelne Zeilen ueberholt. Eigene Ableitungen sind als [E] markiert
  (A2-Fensterlaenge ~24-30 Monate nach Wurzelgesetz; A4 ~2029-12-28; H-27 ~2033-01; 123 Blindtage).
- **T3:** Inhalt von `deribit/publicTrade` "BTC"/"ETH", Boerse und Zweck von `tardis/options_chain`, Ende von `bitmex/publicTrade` sind aus INV allein nicht bestimmbar (UNBELEGT). Die Spalte "koennte nutzen" ist Einschaetzung.
- **T4:** Wortlaute sind Kernsaetze, nicht vollstaendig; "Entscheider" folgt den DEC-Texten, PRD Par. 8 enthaelt keine Regelklassen-Zuordnung.
