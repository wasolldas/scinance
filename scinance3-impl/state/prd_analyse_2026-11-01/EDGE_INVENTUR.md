# EDGE-INVENTUR Scinance 2.0 + 3.0: welche bekannten Ergebnisse versprechen einen Edge, und was fehlt zum Nachweis?

> Herleitungsagent, 2026-11-01. ENTWURF ohne Rechtswirkung: nichts beschlossen, nichts registriert; registrieren darf nur
> der Orchestrator, die Programmrichtung waehlt der Nutzer (PRD Par. 8).
> Auftrag: Edge-Brief im Ordner `prd_review/` (Herleitungsagent), Regeln `prd_review/REGELN_UND_LESELISTE.md`.
> **Ergebnisblind:** keine Datenrechnung, kein Harvest-Client, kein Netz, keine Siegeldatei geoeffnet, keine
> Outcome-Statistik. Alle Zahlen stammen aus den Akten; mit **[abg.]** markierte Werte sind analytische Ueberschlaege
> aus Akten-Zahlen (Formel Bilanz 1.2: Einheiten je Fenster `n = c * (2,4865 * SD / Prior)^2`, P-1 nach DEC-94;
> Rechenskript: `scripts/edge_calc.py` in diesem Verzeichnis).
> **Gelesen:** PRD Abschn. 1-5, 9, 11; Verfassung/Orchestrierungs-Protokoll 3.0 (Leseliste Punkt 2); Kompendium A-F vollstaendig;
> decisions DEC-58..DEC-103 (selektiv, mit Nachtraegen); gate_log GL-032..GL-036; PROGRAMM_BILANZ mit Errata-Vermerken;
> STAND_2026-10-18 mit Nachtraegen bis 2026-10-31; UEBERGABE_2026-10-12 Nachtraege 12-13; Akten herleitung_a2 (Kurzfassungen
> NUISANCE_SIGMA30, PILOT_ROUTE_A2), herleitung_h33 (ENTSCHEIDUNGSVORLAGEN 0-1), herleitung_h27/KONTAMINATION.md (Inventar),
> ZENSUS_UNIVERSUM_UMSATZ, WELLE1_GESAMTBILANZ; 2.0: PROGRAM_FINAL_REPORT, WELLE6_KANDIDATEN_SYNTHESE,
> STRATEGIE_KANDIDATEN, gate_log GL-026..GL-028, Registry H-21/H-22/H-24/H-26, DATA_INVENTORY_2026-08-10 (Zeile Tardis);
> Exkurs S1/S4 (nur Delisting-/Funding-Kappen-Stellen); Dateninventar 2026-11-01; DATA_ACCESS.md (nur Stromtabelle);
> Code-Inventar `src/bybit_edge/research/` (Modulnamen, `power_p1.py`, `h32_fm8/`). Punkt 11 der Leseliste
> (FAKTENBLATT/LISTE) lag bei Abschluss nicht vor.
>
> **Kennzeichnung:** [F] Fakt mit Fundstelle - [U] Urteil des Herleitungsagenten - [V] Vermutung - [Vs] Vorschlag mit
> Richtung (Strenge / Testbarkeit / neutral) und Entscheider (O = Orchestrator, N = Programmfrage an den Nutzer).
> **Einordnung je Befund:** EK = Edge-Kandidat (Ertragsquelle denkbar, Friktionswand nicht a priori bindend);
> SR = Struktur-/Risikobefund (wahr, aber keine Ertragsquelle; Wert als Nuisance, Konstante, Kostenmodell);
> AF = Artefakt (die Messung zeigt nicht, was sie zu zeigen schien); NB = Nullbefund.

---

## 0. Befund in Kuerze

1. [F] Im gesamten Bestand gibt es **kein bestandenes Gate fuer eine Groesse, die als Ertragsquelle oberhalb der
   Friktionswand gelesen werden kann.** 2.0: 31 Gate-Eintraege, 0 handelbare Kanten (Kompendium Kopf). 3.0: kein einziger
   Lauf auf einem Urteilsfenster - GL-032 (GL-012 vor dem Lauf), GL-033/034/036 (GL-012 vor der Registrierung),
   GL-035 (GL-012 im Pilot).
2. [U] Die signifikanten eigenen Messungen zerfallen in drei Gruppen:
   (a) **echte Mikrostruktur-Signale** (H-04, H-05b, H-15, H-23, H-24): Sekunden/Minuten, 80-500x unter der Wand oder
   ohne oekonomische Groesse - nach K-0.1 arithmetisch tot;
   (b) **Struktur-/Risikobefunde des 3.0-Zensus** (Faktorstreuung, Funding-Totzone, Stress-Kohaerenz, Nach-Schock-Zerfall,
   Verfallskalender, sigma30-Klassen, Wochenende 0,82x, OI 13x, Universum liquide) - nach DEC-58 E2 nie promovierbar;
   (c) **genau ein preisprognostischer Querschnittsbefund mit |t| > 3:** der H-32-Pilot (beta-neutrales Momentum
   2022-04..2024-06, t -3,3..-4,1, **gegen** die registrierte Richtung; Screening, nicht konfirmatorisch, Abschnitt verbraucht).
3. [U] Einen Edge-**Hinweis** im engen Sinn (Ertragsquelle oberhalb der Wand mit eigener oder belastbarer
   Literatur-Evidenz) haben nur drei Linien: **Kurzfrist-Reversal im Querschnitt** (nur eigener Pilot; Literatur fuer
   liquide Universen gegenlaeufig), **VRP** (nur Literatur), **Funding-Carry A1** (Zahler klar, Hauptgroesse theta
   unbelegt). A2, A4, A5 haben weder eigene noch belastbare Literatur-Groesse.
4. [U/abg.] Engpass ist ueberall SD/Prior, nicht Daten oder Code (Bilanz 0.1). Fruehestes denkbares Urteil unter
   geltenden Regeln: Reversal auf blinden Fenstern ab 2026-10-05, beim **vollen** Pilot-Betrag voll 2028-05..2029-03,
   bei **halbem** Betrag 2033..2036 - blockiert durch fehlenden Literatur-Prior (GL-036) und die offene Reihenfolge der
   Blindperiode (DEC-98 E4 (b)). VRP 2029-07 (oberer Prior-Rand) bis 2033-01 (Referenz). A1 2030+ und nur mit
   theta-Beleg. A2 nur fuer Effekte ab ~25-30 bp je 12-Monats-Fenster.
5. [F/V] Drei Aktenbefunde, die bisher nirgends stehen: (i) **H-21** (2.0, Entsperrung "2026-12-27") ist sehr
   wahrscheinlich nie entsperrbar (allLiquidation 125/139 Tage; die 14 fehlenden Tage passen exakt zur Luecken-Karte
   DEC-98 N4 (f)) und kollidiert mit dem Blind-Siegel DEC-96 E3; (ii) **`tardis/options_chain` hat 91 monatliche
   Stichtage 2019-04..2026-10 (386 GB)** - Kompendium D.17 ("endgueltig tot") stuetzt sich auf 2 Tage; (iii) die
   Kontaminations-Inventur des Blindbereichs (herleitung_h27/KONTAMINATION.md K-1..K-12) fuehrt **WP-10(B)**
   (BTC/ETH-Mid-Renditen ab 2026-06-22 bis mindestens 2026-09-16) und **H-24 W-R2** (bis 2026-07-31) nicht.
6. [U] **Ehrliche Gesamtlage: Nichts im Bestand verspricht einen Edge im Sinne einer belegten, in absehbarer Zeit
   testbaren Ertragsquelle.** Es gibt einen staerksten eigenen Hinweis (Pilot-Reversal, mit unplausibel hoher impliziter
   Informationsrate), eine staerkste Literatur-Praemie (VRP, vor 2029 nicht pruefbar) und eine Reihe sauber vermessener
   Nicht-Edges. Die Rangliste (Abschnitt 4) ordnet nach erwartetem Erkenntniswert je Kalenderzeit, nicht nach
   Gewinnaussicht.

---

## 1. Rahmen

### 1.1 Friktions- und Power-Arithmetik (zitierfaehig)

- [F] Horizont-Friktions-Kurve K-0.1 (PRD 9.2): `edge_h = (2p-1) * 0,798 * sigma_h`; perfektes 1-s-Orakel 0,71 bp;
  Mindesthorizont bei p 0,55: 6,6 h Taker / 53 min Maker; Wochen-IC 0,05: 2,7 Tage.
- [F] Wand 11 bp Taker-Round-Trip, ~15 bp inkl. Slippage (B.1); Maker 4 bp RT (B.3); Maker-Vorteil in Ruhe ~2,8 bp je
  gefuelltem Bein bei p_fill(60 s) 0,06 (FIFO) .. 0,37 (pro-rata), Stress-Zelle leer (DEC-71, DEC-78).
- [F] Dauer je Fenster `n = c * (2,4865 * SD / Prior)^2` (Bilanz 1.2); Prior +-25 % -> Dauer x0,64 / x1,78; zwei Fenster
  nach C.10 kosten bei gleicher Fehlerrate und Power +26 % Daten (DEC-98 E1 (c)).
- [F] Wochen-Long-Short (PRD 4.1): `R_LS = 3,51 * IC * sigma_xs`; sigma_xs 9,85 %/Woche (DEC-67 E4).

### 1.2 Fensterkarte: was ist fuer welche Statistik gesehen, verbraucht oder blind

| Zeitabschnitt | outcome-nah gesehen | Status | Fundstelle |
|---|---|---|---|
| 2021-07..2026-07, 5 Majors, Minuten | H-24: Tages-Rang-IC Minutenfluss -> 30 min je Halbjahr | fuer Minutenfluss-Lead verbraucht | GL-028 |
| L 2021-06-29..2022-12-31, OOS-1 2023-01..2024-06, OOS-2 2024-07..2025-12, 5 Majors, Stunden | H-20 Nachschock-Rendite (-40,5 / +4,8 / +17,3 bp); H-19 | fuer Tail-Aftermath verbraucht (D.12) | GL-025, GL-026 |
| 2023-07..2025-06 BTC (ETH 2023-04..2024-04) | H-22 L2-Tilt-IC | verbraucht (D.13) | GL-027 |
| Vorperiode 2021-03-24..2024-05-31, BTC/ETH | VRP-Streuung (SD, c), HF-RV-Streuung, A2-sigma30 je Klasse - kein Mittel | fuer VRP- und A2-Mittel formal blind; **A2 nur "durch Disziplin"** (|x_P| aus Teil-B-JSON auf zwei Kandidaten rekonstruierbar) | DEC-98 N5/N7, DEC-103 N1 (2), PILOT_ROUTE_A2 0 |
| Pilot 2022-04-18..2024-06-24, lineare USDT-Perps | fm8-IC mom1/2/4/rev_gap; A1-Nuisance (SD 354 bp, rho_1 -0,25, phi 0,573) | **verbraucht** fuer jede fm8-korrelierte Querschnitts-Statistik (auch andere Neutralisierung, Formationslaenge, Universum); A1-Funding-Bein-Mittel implizit offen (~83 bp/Woche) | DEC-99 (5), GL-035, DEC-93 (ii) |
| W1 2024-07-01..2025-06-30, W2 2025-07-01..2026-06-28 | Persistenz-Null (Eigen-AR(1) je Symbol); BTC-Wochen-SD; A1-Formation (Spread, psi, Schluessel-AK); DVOL-Stichpunkte W2; Verfallskalender | **blind** fuer Roh-/fm8-Querschnitts-IC und A2-r_pre-Mittel; **nicht blind fuer VRP** (DEC-96 E1); rev1 in W2 vorbelastet (GL-036 (4)) | DEC-96, GL-036, H-33 EV-0 C-2 |
| ab 2026-07-01 | STRESS_ABS-Tag 2026-08-19; Katalog-Metadaten; WP-10(B) bis 2026-09-16; H-24 W-R2 bis 2026-07-31 | Blind-Siegel BTC/ETH-Vol/Renditestreuung und DVOL; Einmal-Gut je Zeitabschnitt, geteilt von allen vor der ersten Rechnung registrierten Hypothesen; Reihenfolge offen | DEC-96 E3, DEC-98 E1 (b)/(d), E4 (b) |

---

## 2. Befunde E-1 .. E-32

Format je Befund: **Messung** - **Evidenz** (Statistik, N, vorregistriert, OOS) - **Einordnung** - **Friktion** -
**Fenster/Daten** - **Fehlt bis zum regelkonformen Test** - **Wiederverwertung / C.17**. Bei SR/NB/AF entfallen
Felder, die nichts tragen.

### A. 2.0 - Mikrostruktur und kapitalfreie Mess-WEITER

**E-1 H-04 Lead-Lag BTC -> ETH** (GL-006, GL-009, GL-014; Kompendium A.3/A.6)
- Messung: gerichtete Information BTC -> ETH auf 1-s-Raster (TE, Wavelet-Kohaerenz), zwei Fenster 2026.
- Evidenz: vorregistriert, 2 Fenster; WCOH p 0,0050 in beiden; bei 100.000 Surrogaten 4 Zellen p < 1e-5, alle
  ETH->BTC-Kanten "aufloesungsbedingt fragil". Tradability H-04b: netto -14,95 / -14,83 bp, Brutto-Einfang max +0,19 bp,
  Bootstrap p 1,0.
- Einordnung: **SR** - echt, oekonomisch tot. Horizont 1-3 s; selbst ein perfektes 1-s-Orakel bringt 0,71 bp (K-0.1).
- Friktion: ~80x unter der Wand.
- Fehlt: nichts Behebbares; ein Lead auf >= 53 min (Maker-Mindesthorizont) existiert nicht (H-24: Minutenfluss fuehrt
  nichts nach).
- Wiederverwertung: Positivkontrolle (so in H-14, H-24 genutzt); H-04c nicht impliziert (E.10).

**E-2 H-05b inverses OFI-Vorzeichen SOL** (GL-010, GL-011)
- Evidenz: vorregistriert, Entdeckungszelle (ETH-Juni) ausgeschlossen, echte OOS-Fenster; |corr| 0,010..0,051, nur ein
  Symbol, zwei Lags. H-05c: Brutto +0,03..+0,10 bp, netto ~-14,9 bp.
- Einordnung: **SR** (Market-Maker-Nachfuellung). 150-500x unter der Wand; OFI-Komplex abgeschlossen (D.5, kein H-05d).

**E-3 H-15 Trade-Tape-Grammatik** (GL-021)
- Evidenz: vorregistriert; 4/5 Symbole, Transformer schlaegt Markov k<=4 um >= 2 % relative Cross-Entropy, 200
  saisonalitaetserhaltende Surrogate, FDR; ~180 GPU-h.
- Einordnung: **SR** ohne oekonomische Groesse und ohne Horizontbruecke.
- Fehlt: die einzige Bruecke DAY-BRIDGE (Welle-6-Synthese 5: A-priori 15-20 %, ~100 GPU-h) ist nie registriert; DEC-57
  (GPU-Default 0) verlangt Begruendung plus Tradability-Pfad. Folgekandidaten DSM-02/04 nicht ausgeloest (E.11).

**E-4 H-16 Zeitpfeil** (GL-015 + Nachtrag, DEC-30, B.12)
- Evidenz: AUC bis 0,7353 gegen Bayes-Null 0,5; Ablation: 85-106 % des Effekts aus dem Aktivitaets-/Vol-Envelope.
- Einordnung: **AF** bezueglich "gerichteter Fluss-Struktur", **SR** bezueglich Vol-Asymmetrie (Leverage-artig).
  Kein neues Signal.

**E-5 H-23 Venue-Fingerprint** (GL-031, B.13)
- Evidenz: vorregistriert; gepoolt 0,8914 ueber zwei Trainings-Kohorten; Spearman -0,414 gegen H-12 (n 78).
- Einordnung: **SR**; Relevanz nur als Ausfuehrungsrisiko (ein deterministischer Bot ist selbst ein Fingerabdruck,
  STRATEGIE_KANDIDATEN Kandidat 2). H-17b nicht registriert.

**E-6 H-24 permanenter Minuten-Impact** (GL-028, B.14)
- Messung: Tages-Rang-IC Minuten-Nettofluss -> 30-min-Forward-Rendite, 5 Symbole, 2021H2..2026H1.
- Evidenz: vorregistriert; Positivkontrolle +0,53 (5,3x Floor); IC30 -0,0179 / -0,0169 in den Rezenz-Fenstern,
  ueber zehn Halbjahre -0,011..-0,022; IC5 -0,021/-0,024; IC120 -0,014/-0,016.
- Einordnung: **SR** - die einzige regime-invariante Groesse des Programms; ein Halb-Spread-Anteil ist nicht
  ausgeschlossen (GL-028 Vorbehalt). Kein EK (Betrag winzig, 30 min).
- Fenster: [F] W-R2 = 2026-02-01..2026-07-31 (2.0-Registry H-24) reicht in den spaeteren Blindbereich; in
  KONTAMINATION.md K-1..K-12 nicht gefuehrt (siehe E-31).

**E-7 H-11 / H-11c Vol-Prognose und RV-Envelope** (GL-022, GL-024, B.9/B.10)
- Evidenz: H-11-WEITER war ein Dressing-Artefakt (Geschenk 0,21-0,29); H-11c gegen gedresste HAR 0/4 Zellen,
  CRPSS_dressed in 3/4 negativ, kein p unter 0,29. Nebenbefund GL-022 E4: Dispersions-Ratio der RV-Verteilung
  0,72-0,74; BTC W1 Unter-Prognose (STRATEGIE_KANDIDATEN, Korrektur 3).
- Einordnung: **AF** fuer einen Prognosevorsprung; **SR** fuer die kalibrierte RV-Verteilung als Sizing-Werkzeug.
- Wiederverwertung: nur Sizing/Risiko einer spaeteren VRP-Position, Zitierpflicht GL-024; kein Timing-Signal.

### B. 2.0 - Stunden- und Tages-Horizont

**E-8 H-20 Tail-Aftermath** (GL-026)
- Messung: reversions-signierte Nachbewegung 2-24 h nach 3,5-sigma-Stunden, 5 Symbole gepoolt, Tages-Cluster.
- Evidenz: vorregistriert, N-Floor erfuellt (403 / 362 Ereignistage). OOS-1 +4,8 bp (p 0,40), OOS-2 +17,3 bp
  (p 0,17), L-Fenster -40,5 bp (Fortsetzung); SE des gepoolten Mittels ~12-13 bp; Vorzeichen je Symbol instabil
  (BTC -16 -> +36, ETH +32 -> -12 bp).
- Einordnung: **NB mit Aera-Abhaengigkeit** [U]; kein EK: L-Fenster gegenlaeufig, Symbole uneinheitlich.
- Friktion: die erhofften 25-50 bp (Welle-6-Synthese 1b) sind nicht bestaetigt.
- Power [abg.]: MDE80 je Fenster ~2,4865 x 12..13 = 30..32 bp; selbst der OOS-2-Punkt waere unter C.10 nicht
  nachweisbar.
- Wiederverwertung: D.12 - keine Sigma-/Horizont-/Luecken-Nachsuche ohne neue Vorregistrierung, die die
  Vorzeichen-Instabilitaet als Gegenevidenz zitiert; die Ereignisdefinition lebt nur deskriptiv in WP-11 weiter.

**E-9 H-22 L2-Tilt** (GL-027)
- Evidenz: BTC IC +0,0665 (2023/24, p 0,097), -0,0112 (2024/25, p 0,57); ETH-Bericht +0,062.
- Einordnung: **NB**, aera-abhaengig (D.13). Rezenz-L2 (`orderbook.1000`) existiert erst ab 2026-06 und liegt damit im
  Blindbereich [F Inventar, U].

**E-10 H-01 Pre-Settlement und H-07/H-08 5-Symbol-Reversion** (GL-004, GL-012, GL-013)
- H-01: RAW-Edge -4,48 bp, auf allen 5 Symbolen negativ (-3,07..-5,65). Selbst umgedreht ~+4,5 bp < 11 bp [U].
  **NB**; Folge: Funding-Termin 08:00 UTC ist Pflicht-Placebo jeder A2-Fassung (P2 / P2'').
- H-08: April +0,9..+2,3 bp Reversion, Mai -0,8 bp; N = 5 traegt keine Querschnittsstatistik (D.7). **NB**.

**E-11 Weitere 2.0-Nullbefunde** (Kompendium A, D.2-D.11): H-02 (0/5 Symbole, 0/36 Features), H-03 (Surrogate-p ~1,0,
~250x unter der Wand), H-06 (rho max 0,0145), H-09 (Rauschmuster), H-10 (0 Pointer-Tage), H-12 (IPR ~1/6), H-14
(methodisch invalide), H-19 (stationaer genug; D3-Uebergang bis ~Mitte 2024 begruendet C.18). Alle **NB**, keine
Wiederverwertung als Signal.

**E-12 Friktions-Konstanten** (WP-4/5/6, DEC-42..48, B.2-B.8; WP-7 B5, DEC-67 E4)
- Perp-Spread exakt ein Tick (0,016-0,054 bp) -> Spread-Capture tot (D.1). Options-Quote 0,14 / 0,26 VP im Bein-Band,
  im Stress 97-99 % der Minuten eng; passiv + Halten bis Verfall frisst 25/26 % einer 3-VP-Kante, Taker-RT 85/96 %
  (B.7). Perp-Spread je Umsatz-Dezil 1,6 / 4,2 / 6,3 / 8,7 / 8,2 / 11,6 / 10,4 / 13,3 / 13,0 / 30,6 bp (ein Snapshot).
- Einordnung: **SR** (Kostenmodell); bindend fuer jede Querschnitts-Idee, die in illiquiden Dezilen lebt, und fuer
  jede Optionsstruktur, deren Nutzen eine Greek-Differenz ist (PRD 5.5).

### C. 3.0 - Querschnitt (Klasse W)

**E-13 WP-7: Breite vorhanden, Permutations-Rauschboden klein** (DEC-67, DEC-70, DEC-100, WELLE1_GESAMTBILANZ 2)
- K 400-700 je Woche; Union 1.138 Symbole (261 delistet), Register spaeter 306 delistete lineare USDT-Perps; SD_null
  0,0411 / 0,0440; N_eff 182 (52 W) / 97 (104 W); sigma_xs 9,85 %; sigma_LS 4,77 %; rho(BTC, ETH) 30 min 0,815;
  Delisting-Hazard je Kohorte 20-49 %.
- Einordnung: **SR** (Testbarkeitsvoraussetzung "Breite" erfuellt; kein Signal). Null-Zensus-Klausel DEC-58 E2.

**E-14 Faktorbedingte IC-Streuung 2-3x Boden; reale Wochen-IC-Streuung 2,3..2,6x Null** (DEC-91/92, GL-032, GL-035 Nebenbefund, DEC-101 T3)
- Messung: SD(IC_t) der Roh-Null in der Faktorwelt 0,090 / 0,130 (W1 measured/stress), 0,061 / 0,082 (W2) gegen Boden
  0,049 / 0,042; reale fm8-IC-Wochen-SD im Pilot 0,116..0,134 gegen Null-SD 0,044..0,066 (F2_real 0,0086..0,0131 gegen
  v_fm8_P 0,0049; k_pred 1,9..2,5).
- Evidenz: Streuung gemessen; als Power-Nuisance zulaessig (DEC-102 N1, Lesart S).
- Einordnung: **SR, und zwar der folgenreichste der Klasse W:** Querschnitts-Abhaengigkeit jenseits des
  Ein-Faktor-Modells ist die bindende Streuungsquelle; sie hat A3 (GL-032) und H-33 (MDE80 0,039..0,043) getoetet.
  [F] Mechanisches Momentum aus Markt-Persistenz ist unter gemessener Kalibrierung vernachlaessigbar (rho_f 0,046/0,042,
  Faktoranteil 1,6 %/0,7 % -> 0,0005/0,0002; DEC-78) - der Pilotbefund (E-15) ist also kein Ein-Faktor-Timing-Artefakt [U].
- Fehlt / Hebel: [Vs, Testbarkeit, O] Eine **Mehrfaktor-Null** (v6b-artig, k Faktoren aus der Residual-Kovarianz,
  outcome-only, ohne Charakteristik-Outcome-Verknuepfung) klaert zuerst, ob die 2,3..2,6x mit k Faktoren reproduzierbar
  ist. Nur dann ist eine Mehrfaktor-Neutralisierung als Primaerstatistik begruendet. Wirkung [abg., V]: faellt die
  Wochen-SD von ~0,12 auf 0,05..0,066, sinkt die noetige Fensterlaenge auf 16..29 %. Die Bilanz-Hebelmatrix (2.8) kennt
  nur die Beta-Neutralisierung. Jede solche Statistik ist eine neue Hypothese mit eigenem K (DEC-58 E2) und braucht
  einen Prior.
- Wiederverwertung: Streuungen als Nuisance ja; die Faktorstruktur selbst promotet nichts. [V] Die Gemeinfaktoren
  koennten eine eigene Ertragsquelle tragen (Faktor-Rotation); dafuer gibt es keinen Prior in der Akte.

**E-15 H-32-Pilot: beta-neutrales Momentum negativ** (GL-035, DEC-101 T3, DEC-102)
- Messung: fm8-Wochen-Rang-IC (Fama-MacBeth-Neutralisierung, 8-Wochen-PIT-Beta), lineare USDT-Perps,
  2022-04-18..2024-06-24, W 114, K 126 / 206 / 339.
- Evidenz: vorregistrierter Pilot (DEC-99), genau ein Lauf, Seed 53, Bootstrap-SE, c_real 1,000. mom1 -0,0385 (t -3,33),
  mom2 -0,0500 (t -4,10), mom4 -0,0446 (t -3,55) **gegen** die registrierte positive Richtung; rev_gap +0,0167
  (t 1,53). Kein OOS; Pilot ist "Screening, nie Konfirmation" (DEC-99 (2a)).
- Einordnung: **EK-Hinweis** - der staerkste preisprognostische Befund des Programms -, mit Vorbehalten [U]:
  (i) eine Aera (Crash 2022, Erholung, viele Listungen); (ii) mom1/2/4 hoch korreliert, effektiv ~ein Befund bei K 4;
  (iii) [abg.] implizite Informationsrate |x|/SD x sqrt(52) = 2,25 (mom1) / 2,77 (mom2) / 2,40 (mom4) p.a. - fuer eine
  bekannte Anomalie unplausibel hoch, kraeftige Schrumpfung ist zu erwarten [V].
- Gegenevidenz [F]: Literatur fuer gross/liquide Universen Momentum (-0,015..-0,026 in Reversal-Richtung, fm8-Skala,
  GL-036 (1)); das Universum ist nach Umsatz liquide (E-17); der Widerspruch ist offen (ZENSUS_UNIVERSUM_UMSATZ, Lesart).
- Friktion [abg., V]: `R_LS = 3,51 x IC x 985 bp` = 138 bp/Woche bei IC 0,04, 52 bp bei 0,015 - gegen ~30 bp/Woche
  A3-R-Kosten (PRD 5.3) also 1,7..4,6x; Vorbehalt: Reversal konzentriert sich typischerweise in illiquiden Dezilen
  (Spreads 13..31 bp, E-12). Die Formel nutzt sigma_xs roh; bei Faktoranteil 1,6 % ist der Fehler klein.
- Fenster: Pilotabschnitt verbraucht; W1/W2 fuer fm8 blind, rev1-W2 vorbelastet; ab 2026-07-01 Siegel.
- Fehlt: **ein zulaessiger Prior.** GL-035 ("ein neuer Prior muesste aus der Literatur kommen"), DEC-101 T3 (a) und
  DEC-102 E3 verlangen einen Literatur-Betrag; die Literatur liefert fuer dieses Universum keinen (GL-036).
  Power [abg.] eines blinden Reversal-Fensters (c 1, reale Pilot-SD, nur Bedingung (1b); ohne skalierte Null,
  Selektionsdecke, F-WEEK - also Untergrenze der Dauer):

  | Prior (Anteil am Pilot-Betrag) | mom1 Wochen/Fenster | mom2 | mom4 | voll (Start 2026-10-05) |
  |---|---:|---:|---:|---|
  | 100 % | 63,7 | 41,8 | 55,9 | 2028-05-14 .. 2029-03-18 |
  | 75 % | 113,3 | 74,4 | 99,3 | 2029-08-19 .. 2031-02-16 |
  | 50 % | 254,9 | 167,4 | 223,4 | 2033-03-13 .. 2036-07-13 |
  | Literatur breit, Oberwert 0,014 | ~481 | - | - | ~2045 |

  Power je 52-Wochen-Fenster beim vollen Pilot-Betrag 0,73 / 0,87 / 0,78 (mom1/2/4) [abg.] - selbst dann knapp.
- Wiederverwertung (DEC-99 (5), C.17): **zulaessig** ist die Richtung als offengelegte Vorinformation einer NEUEN
  Hypothese mit eigenem K und Etikett "beschlossen nach Kenntnis GL-035; Richtungswahl nach Kenntnis korrelierter Daten"
  (Muster DEC-102 E2). **Nicht zulaessig:** (a) Konfirmation im Pilotabschnitt (Entdeckungszelle, C.17); (b) jede
  fm8-korrelierte Statistik im Pilotabschnitt als blind fuehren - auch "anderes Universum, gleiche Zeit" ist durch
  DEC-99 (5) ausdruecklich verbraucht; (c) der Pilot-Betrag als Prior. Ein vorzeichengedrehter, vorab geschrumpfter
  Pilot-Prior waere eine **Lockerung (Testbarkeit)** und eine Programmfrage (N).

**E-16 Eigen-Autokorrelation der Wochenrenditen in W1/W2; Survivorship-Differenz** (H-33 EV-0 C-2/C-4, GL-036 (4))
- Messung: AR(1) je Symbol auf Wochenrenditen (Persistenz-Null der Drittfassung): Median phi 0,00, Q25 -0,04 (W1) /
  -0,09 (W2). Survivorship: IC_union - IC_survivors (4-Wochen-Momentum, roh) +0,0033 [-0,0076; +0,0132], 271 Wochen.
- Einordnung: **SR** mit schwacher Reversal-Tendenz in W2 (Zeitreihe, nicht Querschnitt) [U]; Survivorship insignifikant.
- Wiederverwertung: macht W2 fuer rev1 nicht voll blind; jede Reversal-Registrierung auf W2 traegt das C.17-Etikett.

**E-17 Universum "liquide"** (ZENSUS_UNIVERSUM_UMSATZ_2026-10-29, nur Zaehlungen)
- Kein lineares USDT-Perp unter 100 Tsd. USD/Woche; Median-Wochenumsatz je Symbol 10..25 Mio USD; 75..85 % >= 5 Mio;
  W2 umsatzschwaecher und breiter (29,7 % in 1-5 Mio).
- Einordnung: **SR**. Die Literaturgruppe mit Wochen-Reversal (klein/illiquide) ist nicht dieses Universum; Vorbehalt
  Perp-Turnover != Spot-Volumen; Marktkapitalisierung UNBELEGT.

**E-18 Literaturband beta-neutraler Wochen-IC** (DEC-98 N2, GL-036 (1), H-33 EV-1)
- Quelle, keine Messung: klein/illiquide +0,039..+0,048; breit/gleichgewichtet ~0..+0,014; gross/liquide Momentum;
  Ficura: Momentum grosser Coins seit 2021 unprofitabel; der PRD-Prior 0,03 ist fuer ein breites Perp-Universum nicht
  gestuetzt.
- Einordnung: Prior-Quelle, fuer unser Universum widerspruechlich.

### D. 3.0 - Funding (Klasse P)

**E-19 Funding-Mechanik: Totzone, Intervalle, Auto-Switch** (DEC-59, DEC-67, DEC-84, STAND 2)
- 46,7 % der Symbol-Tage exakt auf I; I skaliert exakt mit dem Intervall (1h 0,00125 %, 2h 0,0025 %, 4h 0,005 %, 8h
  0,01 %); Intervalle ueberwiegend 4h/8h (412 / 409 Symbole); Caps heterogen (BTC/ETH 0,333 %, Masse 2,0-2,5 %);
  V-3: Median F - I = -0,0059 %/8h; Auto-Switch auf 1h seit 2025-10-30: 161 Laeufe auf 129 Symbolen, Median 8 Tage
  (vorher 63 Laeufe, Median 224 Tage).
- Einordnung: **SR.** Folgen: Schluessel F - I mit Klumpen bei 0, D10-Short-Bein degeneriert (DEC-70), W1/W2 inhomogen
  (DEC-58 E3).
- [Vs, neutral, O] Der Auto-Switch ist ein exogenes, maschinenlesbares Ereignis (Cap-Treffer) -> Kandidat R-7.

**E-20 A1-Formationsseite: Funding-Spread und Persistenz** (DEC-70, DEC-93, GL-033, Bilanz 2.2)
- Messung: Formations-Spread D1 gegen Universum 175,8 / 339,6 bp/Woche (W1/W2); phi 0,573 = Anteil, der in der
  Folgewoche im Funding-Bein ankommt (Nuisance 2022-04..2024-06); Schluessel-AK lag1 0,42 (W_eff 0,41 W);
  Teststatistik rho_1 -0,25; SD der Gesamtrendite 354..373 bp/Woche.
- Evidenz: Formation und Streuung gemessen; **theta** (nicht durch das Preisbein kompensierter Anteil) UNBELEGT; He et
  al. (Zeitreihe, BTC): 28 % des Perp-Carry aus Funding [sek] - kein Querschnitts-Beleg (DEC-98 N2 (4)).
- Einordnung: **EK** (Cashflow statt Prognose; Zahler: gehebelte Gegenseite) mit offener Hauptgroesse.
- Friktion [F/abg.]: ~18 bp/Woche (Turnover 0,6, PRD 5.1); bei theta 1 Praemie ~100 bp/Woche (W1-artig) - weit ueber
  der Wand.
- Fenster: Formationsseite W1/W2 gesehen (psi, Spread); blinde Fenster hinter Siegel (DEC-98 E1 (b)).
- Fehlt: theta-Beleg (einziger echter Hebel, Bilanz 2.2), dann 85 Wochen je Fenster (theta 1, W1-Spread) -> voll
  2030-01-06; theta 0,77: 2032-04-11; unter DEC-67 E4 x2,44.
- Wiederverwertung: Nuisance ja; eine Quelle mit Stichprobe aus W1/W2 waere Outcome-Information (DEC-93 E2).

**E-21 Stress-Kohaerenz** (DEC-64/65, WELLE1_GESAMTBILANZ 2)
- Funding-Paare 0,6-0,7 im Stress gegen 0,2-0,35 in Ruhe (Rang 87-99,7 % gegen Surrogate); IV-RV BTC x ETH 0,88;
  BTC-Funding x IV-RV im Stress -0,43 / -0,46 (Rang 2-5 %).
- Einordnung: **SR/Risiko**: Diversifikation zwischen Funding-Beinen bricht im Stress; Stress-N_eff bindet A1.
  Kein Kandidat (DEC-65 (4)).

### E. 3.0 - Volatilitaet und Optionen

**E-22 VRP: Streuung gemessen, Niveau nur Literatur** (DEC-97, GL-034, DEC-98 N2/N5)
- Messung (nur Streuung, Vorperiode): SD der Praemie S1 (BTC) 18,6 VP; Varianzfaktor c 28,2 (Regel P-3; Konsens 18,6)
  -> ~13 unabhaengige Beobachtungen je Jahr; HF-RV aendert nichts (SD 18,58, c 30,7..31,6, Langfristvarianz HF/cc
  0,87..1,31); RV-Messrauschen cc SD 8,1 VP.
- Prior [sek]: Almeida et al. 2017-07..2022-12, pi-2 7,14 VP, Band 3,2..10,5 VP; BVRP 0,14.
- Einordnung: **EK** (literaturstaerkste Praemie; Zahler Vol-Kaeufer/Hedger); eigene Evidenz: keine.
- Friktion: Optionen B.4-B.7; Liefergebuehr 0,015 % des Underlyings je Kontrakt, Cap 12,5 % [sek] (DEC-74 N).
- Power: 12-Monats-Fenster SE 5,17 VP, MDE80 12,86 VP [abg.]; Tage je Fenster 548 / 1.182 / 6.033 bei 10,5 / 7,14 /
  3,2 VP (DEC-98 N5) -> ab 2026-07-01 voll 2029-07-30 / 2033-01-18 / 2059 [abg.].
- Fenster: W1/W2 nicht blind; ab 2026-07-01 blind, Einmal-Gut, Kollision mit H-26 (DEC-98 E2).
- [Vs, Testbarkeit, O] Ungepruefter Hebel: **nicht ueberlappende 7-Tage-Praemie aus Wochenverfaellen** (52 statt ~13
  Einheiten je Jahr). Lohnt nur, wenn deren SD unter ~37 VP liegt [abg.: 5,17 x sqrt(52)]. Die Nuisance ist UNBELEGT,
  weil Wochen-IV vor 2026-06 im Archiv fehlt (deribit/publicTrade ab 2025-08-01; Tardis 1 Tag/Monat).

**E-23 DVOL-Quelle** (WP-9, DEC-61, DEC-96 N3; Inventar): REST = Live bitgenau auf 176 Tagen; DVOL BTC/ETH
lueckenlos 2021-03-24..2026-10-31 (2.048/2.048 Tage). Datenfakt (SR).

**E-24 Nach-Schock-Zerfall** (WP-11 v2, DEC-63): Differenzprofil bei t 0 1,22 z; Halbwertszeit BTC/ETH 22-31 h,
Potenzgesetz-Exponent 0,23-0,32 (Omori-artig); SOL-Volumen 2,5 h. **SR** (Kostenfenster >= 1 Tag nach Schock; ein
Schocktag ist ein Cluster). Kein Kandidat (DEC-63 (4)); eine bedingte VRP "nach Schock" starb als R3-K-36 an der Power
(PRD 9.1).

**E-25 Tardis-Optionsketten** (Inventar 2026-11-01; DATA_ACCESS.md Stromtabelle; DATA_INVENTORY_2026-08-10 Z. 70; D.17)
- [F] `tardis/options_chain`: 91 von 2.741 Kalendertagen 2019-04-01..2026-10-01, 386,63 GB, 5,27 Mrd. Zeilen
  ("Tardis-Gratis-Stichtage"). Das 2.0-Urteil "Options-Chain-Kandidaten endgueltig tot" beruht auf 2 Tagen.
- Einordnung: Datenbefund. Monatliche Vollketten ueber 7,5 Jahre erlauben nicht ueberlappende Monatsbeobachtungen von
  Skew und Term-Struktur (~12/Jahr) und den GL-012-Vorabcheck von A5 (PRD 5.5 Kill (2)) auf Tagen **vor** 2026-07-01.
- Power [F/abg.]: fuer das VRP-Mittel kein Gewinn (Monatsziele SD_m 18,70, c 1: SE 5,40 / MDE80 13,4 VP je 12 Monate,
  Bilanz 2.3).
- Fehlt: C.8-Inhaltsprobe (Boerse, Felder, Stichtag); D.17-Revision (O, neutral).

### F. 3.0 - Ereignisse (Klasse E, A2)

**E-26 Verfallskalender taeglich, OI-Groessenverhaeltnis Freitag/Mo-Do ~13x** (DEC-98 N5/N7, DEC-103 E1)
- Deribit-Verfall stets 08:00:00 UTC (Median +0,04 s); BTC-Tagesverfaelle ab 2020-02-04; **seit 2020-03-25 jeder
  Kalendertag Verfallstag**; taegliche Deribit-Futures-Verfaelle ab 2026-04-04 (W2: 48 von 207 Mo-Do-Tagen); gelieferte
  Kontrakte Freitag/Mo-Do q50 12,8 (BTC) / 13,5 (ETH) in der Vorperiode, W1/W2 9,7 / 7,6 bzw. 9,1 / 6,3; Monat+Quartal
  gegen Woche 3,2..3,8.
- Einordnung: **SR.** Jeder A2-Kontrast ist ein Groessen-Kontrast; unter OI-Proportionalitaet (UNBELEGT) bleiben
  0,84..0,92 des Effekts; das Groessenverhaeltnis faellt in W1/W2 auf 6..10 (Verduennung) [F/U].

**E-27 sigma30-Klassen und Wochenend-Streuung 0,82x** (NUISANCE_SIGMA30 0/3, DEC-98 N7 (2), DEC-103 E3)
- r_pre [07:30, 08:00), Vorperiode, Cluster-SD: Freitag 43,8 bp (n 167), Mo-Do 42,5 (n 666), Wochenende 34,8 (n 332),
  Monat+Quartal 52,4 (n 39); Verhaeltnisse (Wochenblock-Bootstrap, 95 %): Freitag/Mo-Do 1,06 [0,85; 1,30],
  Monat+Quartal/Woche 1,29 [0,90; 1,78], Wochenende/Mo-Do 0,82 [0,69; 0,98]; Jahresregime Freitag 2021 58,7 gegen
  2023 35,2; Exzess-Kurtosis 5..10; Slot 15:30 1,30x, US-Slots 12:30-14:00 Spitzen (73,9 / 71,0).
- Einordnung: **SR.** Keine erhoehte Varianz an Wochen-Freitagen; Monat+Quartal leicht erhoeht, Band schliesst 1 ein
  [U]. Wochenende ist ein eigenes Liquiditaetsregime (einzige Klasse mit Band unter 1) und darum aus allen A2-Mengen
  ausgeschlossen.
- Wiederverwertung: Nuisance fuer A2 ja; **Kombinationsverbot** fuer geschachtelte Klassenstreuungen (DEC-103 N1 (2)).
  Eine Wochenend- oder Verfalls-**Varianz**-Hypothese waere neu, Prior UNBELEGT, die Vorperiode dafuer gesehen -> nur
  blinde Fenster; nicht empfohlen [U].

**E-28 A2-Rauschboden, Literatur und Pilot-Route** (NULL_SIMULATION_A2, PILOT_ROUTE_A2, DEC-103 + N1, UEBERGABE 13)
- [F] SE je 12-Monats-Fenster (P2'') 7,34 / 7,58 bp; MDE80 Einzel 18,25; P3fix bindend 19,7; Produkt (Zuordnung)
  zentral 23,4 / 24,4, stress 26,1 / 27,2 bp (Ereignis-Skala, bindend); W2: 12 von 52 Wochen nicht permutierbar.
- Literatur [sek]: Ni/Pearson/Poteshman 16,5 bp (Aktien-Monatsverfaelle); Weiss et al. FRL 2026, 1.059 Deribit-
  Verfallstage 2021-2023: Fall vor / Umkehr nach dem Verfall **nur bei ATM-OI im obersten Dezil**, am staerksten bei
  negativem Netto-GEX, keine bp-Zahl.
- Power [abg.] (Jahre je Fenster fuer C10, Produkt stress): 16,5 bp 2,5..2,7; 20 bp 1,7..1,85; 25 bp 1,1..1,2;
  30 bp ~0,8. Pilot-Route: Uebergabe erst ab ~32 bp Pilot-Kontrast; bei 16,5 bp 0,0001, bei 25 bp 0,04 [F].
- Einordnung: **EK nur unter der Annahme "Effekt >= ~25-30 bp"**; eigene Evidenz keine.
- Friktion: 30-min-Horizont; 12..30 bp liegt an bzw. ueber der 11-bp-Taker-Wand und unter/an der 15-bp-Gesamtwand
  -> nur passiv (PRD 5.2 Etikett).
- [Vs, neutral, O] **Weiss-Konditionierung** als vorab fixierte Ereignismenge (oberstes ATM-OI-Dezil je Verfallstag,
  alle Wochentage): Datenteil vermutlich aus `deribit/rest.settlements` (Delivery je Instrument mit Feld `position`,
  BTC ab 2017-05, ETH ab 2019-03) rekonstruierbar [V; Einheit von `position` UNBELEGT, DEC-98 N7 (1)]. Lohnt nur, wenn der
  Effekt ueberproportional konzentriert ist (so der Abstract) [V]; erster Schritt ist ein reiner Zaehl-Zensus.

### G. Akten- und Datenbefunde mit Edge-Relevanz

**E-29 H-21 LIQ-TAG: Entsperrung praktisch ausgeschlossen, Siegel-Konflikt ungeloest**
- [F] Entsperrung verlangt lueckenlose done_days fuer allLiquidation UND publicTrade, BTC+ETH, in W1 2026-07-01..09-28
  und W2 09-29..12-27 (2.0-Registry H-21). Inventar: allLiquidation BTCUSDT/ETHUSDT 125/139 Tage. Luecken-Karte B-5:
  14 Tage ohne Optionsdaten auf beiden Boersen = 06-26, 07-06..07-16, 08-01, 08-14 (DEC-98 N4 (f)) - exakt 14, davon 13
  in H-21-W1 [V: dieselben Tage; per Lueckenliste zu bestaetigen]. allLiquidation ist ein Live-Strom (DATA_ACCESS.md),
  rueckwirkend nicht nachladbar [V].
- [F] Outcome von H-21 ist `y = s x r(t -> t+30 min)` auf BTC/ETH - eine Renditestatistik im Blindbereich (DEC-96 E3);
  der Konflikt ist fuer H-26 entschieden (DEC-98 E2), fuer H-21 nirgends.
- Edge: keiner (A-priori 0,2-0,5x unter der Wand, Registry).

**E-30 Negativ-Panel A2: Rohdaten liegen moeglicherweise schon vor**
- [F] Anfrage 1-min XRP/BNB/SOL 2021-03-24..2026-06-28 (2026-10-31); `bybit/publicTrade` XRP/BNB/SOL lueckenlos seit
  2021 (1.999 / 1.952 / 1.952 Tage, Inventar).
- [V] r_pre braucht nur die Schlusskurse 07:29 und 07:59 je Tag; aus publicTrade ableitbar, sofern zeitlich gefiltert
  geladen werden kann (Durchsatz ~2 MB/s, Verfassung "Marktdaten").

**E-31 Luecken der Kontaminations-Inventur des Blindbereichs**
- [F] KONTAMINATION.md (H-27) K-1..K-12 fuehrt WP-10(B) (Quotes, Fills, adv_sel aus BTC/ETH-Mid-Renditen
  2026-06-22..09-16; DEC-69/71/78) und H-24 W-R2 (Minutenfluss-IC 2026-02-01..07-31) nicht; beide liegen vor DEC-96.
- [V] Materialitaet gering (adv_sel-Mittel 0,6-0,8 bp; CI-Breiten verraten die 60-s-Mid-Streuung allenfalls grob; H-24
  ist ein Rang-IC), aber fuer jede kuenftige Blindfenster-Registrierung zu fuehren.

**E-32 Lebenszyklus-Ereignisse (Neulistung, Delisting-Ankuendigung) - in der Akte nur als Survivorship-Problem**
- [F] Die 8-Wochen-PIT-Regel existiert, weil ein "Listing-Pump-Artefakt" angenommen wird (PRD 4.1, R2 Z. 199) -
  gemessen wurde es nie; Delistungen kommen in Chargen (Exkurs S1), Hazard je Kohorte 20-49 %, 306 delistete lineare
  USDT-Perps (DEC-100); Daten: `rest.kline1d` inkl. Delisteter, `delisting_dates` (last_trading_day), WP-12-
  Ankuendigungsdaten (`publish_ms`, 268).
- Einordnung: [V] naheliegende Klasse-E-Familie, nie formuliert; Prior in der Akte UNBELEGT. Kritische Vorfrage:
  Handelbarkeit nach der Ankuendigung (Reduce-only-Zeitpunkt) an der Primaerquelle UNBELEGT -> R-6.

---

## 3. Wiederverwertung: was C.17, DEC-99 (5) und DEC-58 E2 erlauben

| Befund | erlaubt | verboten | Fundstelle |
|---|---|---|---|
| H-32-Pilot (E-15) | Richtung als offengelegte Vorinformation einer neuen Hypothese mit eigenem K; Pilot-Streuung als Power-Nuisance | Konfirmation im Pilotabschnitt; fm8-korrelierte Statistik (andere Neutralisierung, Formationslaenge, Universum) dort als blind; Pilot-Betrag als Prior | C.17, DEC-99 (5), GL-035, DEC-101 T3 (a), DEC-102 E3 |
| Persistenz-Null W1/W2 (E-16) | Etikett | W2 fuer rev1 als voll blind fuehren | GL-036 (4) |
| A2-sigma30 (E-27/28) | Nuisance, Null-Simulation | Kombination geschachtelter Klassen; ein Mittel der Vorperiode ausser per registriertem Pilot | DEC-103 N1 (2) |
| VRP-Streuung (E-22) | Fensterlaenge, Power | Registrierung auf W1/W2 | DEC-96 E1 |
| A1-Formation (E-20) | Nuisance | Quelle mit Stichprobe aus W1/W2 als theta | DEC-93 E2 |
| Zensus-Strukturbefunde (E-13, E-14, E-19, E-21, E-24, E-26, E-27) | Konstanten, Kostenmodell, Nuisance | Promotion zum Kandidaten ohne eigene, vorab formulierte Hypothese mit eigenem K | DEC-58 E2 |
| 2.0-Nullbefunde (E-8..E-11) | Positivkontrolle, Aera-Profil | Nachsuche ohne neue Registrierung mit Gegenevidenz | D.12, D.13, GL-026/027 |

**Zur Frage des Auftrags ("negativer Momentum-Pilot als Richtungs-Prior fuer Reversal auf ANDEREN Daten/Fenstern"):**
[F/U] Andere *Fenster* derselben Statistik (W1/W2 oder blinde Fenster ab 2026-07/10) - ja, aber nur mit Literatur-
Betrag (fehlt) und Etikett; W2 fuer rev1 vorbelastet. Andere *Daten* im Pilotzeitraum (anderes Universum, andere Boerse,
andere Neutralisierung) - nein, DEC-99 (5) zaehlt genau diese als korreliert und verbraucht. Andere Daten in anderen
Zeitraeumen (z. B. ein zweites Universum ab 2026-07) - ja wie "andere Fenster"; ein Binance-Perp-Panel existiert aber
nicht (Inventar: 5 Symbole), und Bilanz B-6 hat es aus Power-Gruenden nicht beauftragt.

---

## 4. Rangliste der aussichtsreichsten Edge-Hypothesen

Ordnungskriterium [U]: erwarteter Erkenntniswert je Kalenderzeit unter den geltenden Regeln = Plausibilitaet einer
Ertragsquelle oberhalb der Wand x Aussicht auf ein Urteil bis ~2029. **Keine Zeile ist eine Registrierungsempfehlung;**
nach geltenden Regeln ist heute jede Zeile GL-012 vor der Registrierung (Prior oder Daten fehlen) bzw. gesperrt.

| Rang | Hypothese (Klasse) | Hinweis / Prior | Daten JETZT (Inventar) | Power-Ueberschlag | Friktions-Etikett | Konflikt D / Fenster | Data-Harvest zusaetzlich | Hauptblocker (Entscheider) |
|---|---|---|---|---|---|---|---|---|
| **R-1** | Beta-neutrales Kurzfrist-Reversal 1-4 Wochen auf blinden prospektiven Fenstern (W) | Pilot t -3,3..-4,1 (E-15); W2-Eigen-AR Q25 -0,09 (E-16); Literatur liquide: Momentum (E-18) | kline1d ALL + fundingRateAll 2021-01..2026-10 lueckenlos; Panel-Strom ab 2026-09-29; instruments/delisting_dates ab 2026-10-20 | 42..64 Wo./Fenster beim vollen Pilot-Betrag (voll 2028-05..2029-03); 167..255 bei halbem (2033..2036) | Woche; ~30 bp/Woche Kosten; brutto 52..138 bp/Woche bei IC 0,015..0,04 -> ueber der Wand, ausser Konzentration in illiquiden Dezilen | nicht D.7 (K 400-700); Pilot verbraucht; H-33 GL-012; rev1-W2 vorbelastet; Siegel ab 2026-07 | Marktkapitalisierung + Spot-Volumen je Coin (Universums-Zuordnung, E-17) | Prior (N: geschrumpfter Pilot-Prior = Lockerung, oder Literatur); Reihenfolge Blindperiode (N) |
| **R-2** | VRP Deribit BTC/ETH, neue Hypothese auf blinden Fenstern > 12 Monate (P) | Literatur pi-2 7,14, Band 3,2..10,5 VP [sek]; eigene: keine | DVOL 2021-03..2026-10 lueckenlos; kline1m BTC ab 2020-03, ETH ab 2021-03; Optionsticker ab 2026-06-16; Tardis monatlich | 548..1.182 Tage/Fenster (oberer Rand..Referenz), voll 2029-07..2033-01 | Praemie; Optionsgebuehr frisst ~25 % einer 3-VP-Kante passiv bis Verfall; Delta-Hedge zahlt die Perp-Wand je Rehedge | kein D (D.15 betrifft Long-Vol); W1/W2 nicht blind; konkurriert um die Blindperiode; H-26-Kollision | fuer den 7-Tage-Hebel (E-22): Wochen-ATM-IV-Historie vor 2026-06 (z. B. Deribit-Options-Trades mit IV-Feld; Verfuegbarkeit UNBELEGT [V]) | Kalenderzeit; Reihenfolge (N); Fensterlaenge > 12 Monate ist eigene Vorlage (DEC-98 N5 (2)) |
| **R-3** | A1 Funding-Long-Bein D1 gegen Universums-Hedge (P) | Spread 176/340 bp/Woche, phi 0,573; theta UNBELEGT | fundingRateAll + kline1d 2021..2026 lueckenlos | theta 1: 85 Wo./Fenster (2030-01); theta 0,77: 143 (2032-04); E4 x2,44 | ~18 bp/Woche; Praemie bei theta 1 ~100 bp/Woche | Formation W1/W2 gesehen; W2 Auto-Switch-inhomogen; Siegel | nichts (Literatur fuer theta) | theta-Beleg (O Recherche, N PDFs) |
| **R-4** | A2 Freitags-Verfall gegen Mo-Do, r_pre 07:30-08:00 (E) | nur Richtung (Weiss) bzw. Aktien 16,5 bp [sek]; eigene: keine | kline1m BTC/ETH; settlements ab 2017/2019; Negativ-Panel fehlt (angefragt; E-30) | Produkt stress 26..27 bp je 12 Monate; 16,5 bp braucht 2,5..2,7 Jahre je Fenster; Pilot-Route uebergibt ab ~32 bp | 30 min; an der Taker-, unter der Gesamtwand -> nur passiv | H-01 durch P2'' abgegrenzt; Vorperiode nur durch Disziplin blind; W2-Q4 ohne P2''-Partner | Negativ-Panel; ATM-OI je Verfallstag (aus settlements ableitbar?) | V-5b (N: Pilot-Route P-1 = Lockerung) |
| **R-5** | A4 Perp gegen datierten Future, Wedge (P) | keiner; datierte Kontrakte illiquide (turnover24h 45k..530k USD, DEC-59) | rest.tickers15m ab 2026-10-20 (13 Tage); deliveryPrice linear ab 2023-03, invers ab 2021-06 (nur Settlement) | 6,2 / 11 / 25 Zyklen je Fenster bei Prior = 1 / 0,75 / 0,5 sigma_w; sigma_w ab 2027-10-20; Urteil fruehestens ~Ende 2029 [abg. aus Bilanz 2.5 + DEC-98 N4 (a), V] | 3 Fills / 90 Tage; Kapitalbindung ist die Kostenstelle | kein D; nichts verbraucht | Probe: oeffentliche Deribit-Futures- und Perp-Funding-Historie nachladbar? -> A4-Analogon mit Historie statt Recording-first [V] | Zeit / Datenquelle (O) |
| **R-6** | Lebenszyklus-Ereignisse: Post-Listing-Drift und Delisting-Ankuendigung (E, neu) | keiner in der Akte; 8-Wochen-Regel unterstellt einen Listing-Pump (E-32) | kline1d ALL inkl. Delisteter 2021..; delisting_dates; WP-12-Ankuendigungen (268) | Ereignisse zahlreich (306 Delistungen, Chargen), N_cluster UNGEMESSEN; bei Einzel-SD ~985 bp/Woche [V] sind 24 / 67 / 150 Cluster je Fenster fuer 500 / 300 / 200 bp noetig [abg.] | Woche; junge/illiquide Perps, Spreads bis ~31 bp und mehr; Funding der ueberfuellten Seite | kein D; W1/W2 und Vorperiode fuer diese Statistik unberuehrt [U]; Siegel ab 2026-07 | nichts Neues; zuerst Zaehl-Zensus (Ereignisse, Chargen, Listungsdaten) | Prior UNBELEGT; Reduce-only-Regel nach Ankuendigung UNBELEGT (O) |
| **R-7** | Funding-Cap-Treffer / Auto-Switch als Ereignis (E; vgl. Exkurs X-NEXP-2) | keiner; Mechanismus-Vermutung Crowding -> Umkehr [V] | fundingRateAll ab 2021 (Intervall aus Zeitstempeln, wie DEC-84); kline1d ALL | 161 Laeufe in ~8 Monaten bis zum Siegel, zeitlich geclustert -> N_cluster UNBELEGT; Bedarf wie R-6 | Woche, Alts; nur grosse Effekte relevant | A-priori-Gegenevidenz H-01 (Funding-Druck ohne Edge); D.12, falls mit Schockstunden deckungsgleich; Regimebruch 2025-10-30 | X-NEXP-2-Kontrolle "gleiches Asset auf Binance" braucht Binance-Alt-Perps (Inventar: nur 5 Symbole) | Prior, N; nur Rest-W2 vor dem Siegel |
| **R-8** | Skew-Praemie A5 (P, gesperrt) | Literatur [sek, R1]; eigene: keine | Tardis monatlich 2019..2026 (E-25); Optionsticker ab 2026-06-16 | N ~12/Jahr; SD UNBELEGT | RR-Hedge-Kasse 0,2 + 0,38..1,04 VP; Greek-Differenz gebuehren-benachteiligt | E.6-Reihenfolge (H-26 nie gemessen); D.17 erst zu revidieren | nichts; Tardis-Inhaltsprobe | E.6 (O/N) |

**Begruendung der Reihenfolge [U].**
- R-1 vor R-2, obwohl die VRP a priori die plausiblere Praemie ist: R-1 ist der einzige Befund mit eigener |t| > 3 und
  die einzige Linie, die (beim vollen Betrag) vor 2030 urteilsfaehig waere. Dagegen stehen die Literatur fuer liquide
  Universen und die unplausibel hohe implizite Informationsrate; realistisch geschrumpft landet R-1 in derselben Zeitzone
  wie R-2. Ein fair geschrumpfter Pilot-Prior (z. B. 50 %) macht R-1 zum Langlaeufer.
- R-3 vor R-4: A1 hat einen klaren Zahler und eine gemessene Formationsseite; A2 hat keine einzige eigene Zahl zum Effekt
  und muesste ueber 25-30 bp liegen, also ueber der Aktien-Literatur.
- R-6/R-7 sind ungepruefte, naheliegende Ereignis-Familien mit vielen Einheiten und unberuehrten Fenstern; sie stehen
  unten, weil kein Prior existiert und die Handelbarkeit (Reduce-only, illiquide Perps) zweifelhaft ist.
- Nicht in der Rangliste: H-20-Neufassung (MDE ~30 bp, Vorzeichen instabil, D.12), H-22-Intraday (Rezenz-L2 nur im
  Blindbereich), H-21 (unter der Wand, Entsperrung unmoeglich), Wochentags-/Kalendereffekte (R2-K-06: Nachweisgrenze
  33 bp/Tag; Welle-6: Wochenzyklus erst ab 113 bp), Lead-Lag/OFI (K-0.1), Funding x IV-RV (DEC-65 (4)),
  Cross-Venue-Funding (Binance-Funding erst ab 2026-03, 5 Symbole, fast nur Blindbereich).

---

## 5. Was Data-Harvest zusaetzlich sammeln muesste (konsolidiert, priorisiert)

| Prio | Auftrag | fuer | Charakter |
|---|---|---|---|
| 1 | Marktkapitalisierung und Spot-Volumen je Coin, taeglich, Backfill ab 2021 (externe Quelle) | R-1 und jeder kuenftige Querschnitts-Prior (Literatur-Zuordnung, E-17) | PIT-Schnappschuesse kuenftig irreversibel [V] |
| 2 | Inhaltsprobe `tardis/options_chain` (Boerse, Felder, Stichtag je Monat) | R-8, D.17-Revision, A5-Vorabcheck | nur Pruefung |
| 3 | Probe: oeffentliche Nachladbarkeit von Deribit-Futures-Kursen (abgelaufene Laufzeiten) und Deribit-Perp-Funding | R-5 (A4-Analogon mit Historie) | Probe [V] |
| 4 | Probe: Wochen-ATM-IV-Historie vor 2026-06 (z. B. Deribit-Options-Trades mit IV-Feld als Backfill) | R-2-Hebel (7-Tage-Praemie) | Probe [V]; Nutzen nur, wenn SD_w < ~37 VP |
| 5 | Negativ-Panel XRP/BNB/SOL 1-min (bereits angefragt) - alternativ Ableitung aus `bybit/publicTrade` | R-4 Gate (4) | laufende Anfrage (E-30) |
| 6 | (nur falls R-7 verfolgt wird) Binance-Perp-Kerzen/Funding fuer die Bybit-Alts | Kontrollgruppe X-NEXP-2 | widerspricht Bilanz B-6 nicht (dort Power-Argument fuer A3), ist aber Zusatzaufwand |

Nicht noetig: HF-RV (geschlossen, DEC-98 N5), Binance-Panel fuer A3 (Bilanz B-6). Laufend und ausreichend: DVOL,
kline1m BTC/ETH, Panel-Strom, Funding aller Perps, A4-Quotes, Settlements.

---

## 6. Vorschlaege (mit Richtung und Entscheider)

| # | Vorschlag | Richtung | Entscheider |
|---|---|---|---|
| S-1 | H-21: Entsperrbarkeit per DEC feststellen (Lueckenliste allLiquidation 2026-07-01..12-27) und den Siegel-Konflikt wie H-26 behandeln (Default: gesperrt, kein Lauf im Blindbereich) | Strenge | O |
| S-2 | KONTAMINATION-Inventur des Blindbereichs um WP-10(B) und H-24 W-R2 ergaenzen (C.17-Nachtrag) | Strenge | O |
| S-3 | D.17 und F.1 nach Inhaltsprobe Tardis revidieren (C.8) | neutral | O |
| S-4 | Mehrfaktor-Null (v6b-artig, k Faktoren, outcome-only) als Nuisance-Paket: erst messen, ob sie die 2,3..2,6x reproduziert; nur dann Mehrfaktor-Neutralisierung als Primaerstatistik herleiten | Testbarkeit (nur Nuisance, keine Lockerung) | O |
| S-5 | Programmfrage: darf ein vorzeichengedrehter Pilot-Betrag mit vorab fixierter Schrumpfung (z. B. 50 %) als Prior einer Reversal-Hypothese auf blinden Fenstern dienen? | Testbarkeit (Lockerung von DEC-102 E3 / GL-035 "Was nicht folgt") | N |
| S-6 | Reihenfolge der Blindperiode entschaerfen: nach DEC-98 E1 (d) teilen alle vor der ersten Rechnung registrierten Hypothesen denselben Zeitabschnitt - eine gemeinsame Vorregistrierung (VRP lang, Querschnitt, A1) vor jeder Rechnung macht die Reihenfolge weitgehend gegenstandslos; Preis: frueh fixierte Fensterlaengen, Priors, K | neutral | N |
| S-7 | Zaehl-Zensen ohne Outcome: (a) ATM-OI je Verfallstag aus settlements (R-4-Variante), (b) Listungen/Delisting-Chargen je Fenster (R-6), (c) Cap-Treffer-Cluster je Monat (R-7) | neutral | O |
| S-8 | Vorfrage an der Primaerquelle: Reduce-only-Regel nach Delisting-Ankuendigung (R-6) | neutral | O |

---

## 7. Was NICHT folgt

- Kein Befund dieser Inventur ist ein Verdikt. GL-012 heisst "Lineal zu kurz", nicht "Effekt null" (STAND 4); die
  DROP-Relevanzzeilen von A1, A3, H-27, H-33 greifen nicht.
- Der H-32-Pilot ist kein Reversal-Nachweis: ein Fenster, Screening, gegen die registrierte Richtung, Aera 2022-24,
  implizite Informationsrate unplausibel hoch. Er begruendet keine Registrierung auf W1/W2 ohne Literatur-Prior.
- Die sechs Mess-WEITER (H-04, H-05b, H-11, H-15, H-16, H-23) implizieren keine Tradability (C.2, E.10); keiner ist ein
  Edge-Kandidat.
- Strukturbefunde (Faktorstreuung, Totzone, Stress-Kohaerenz, Nach-Schock-Zerfall, Verfallskalender, sigma30,
  Wochenende 0,82x, OI 13x, Universum liquide) promoten keinen Kandidaten (DEC-58 E2).
- Die Power-Ueberschlaege sind Untergrenzen der Dauer (nur eine Gate-Bedingung, c = 1, ohne skalierte Null,
  Selektionsdecke, F-WEEK) und gelten nur bei unveraenderter Nuisance; sie sind keine Zusagen.
- Die Rangliste ist keine Registrierungsempfehlung und keine Gewinnprognose.
- Die Tardis-Daten heben D.17 nicht auf; erst die Inhaltsprobe.
- Nichts hier betrifft Kapital, Steuer oder Ausfuehrung (PRD 8.1/8.2); kein Live-Order-Code.

---

## 8. Kurzfassung an den Orchestrator (<= 12 Zeilen)

1. Kein Ergebnis aus 2.0/3.0 belegt einen Edge; 3.0 hat noch kein Urteilsfenster gerechnet (GL-032..036).
2. Edge-Hinweise nur: Querschnitts-Reversal (Pilot t -3,3..-4,1, Literatur gegenlaeufig), VRP (nur Literatur), A1 (theta offen).
3. Rangliste R-1 Reversal blind, R-2 VRP, R-3 A1, R-4 A2, R-5 A4, R-6 Listung/Delisting (neu), R-7 Cap-Treffer, R-8 Skew.
4. Heute ist jede Zeile GL-012 vor der Registrierung oder gesperrt; Engpass SD/Prior, nicht Daten.
5. Reversal: voller Pilot-Betrag 42..64 Wochen je blindes Fenster (voll 2028-05..2029-03), halber 167..255 (2033+).
6. Implizite Informationsrate des Piloten 2,3..2,8 p.a. -> starke Schrumpfung erwartet; Betrag als Prior verboten (S-5 = N).
7. VRP 2029-07..2033-01; A1 2030+ nur mit theta; A2 nur bei Effekt >= ~25-30 bp je 12-Monats-Fenster.
8. Groesster ungepruefter Hebel Klasse W: Mehrfaktor-Null fuer die reale 2,3..2,6x-IC-Streuung (S-4, nur Nuisance).
9. Aktenbefunde: H-21 nie entsperrbar + Siegel-Konflikt (S-1); Tardis 91 Monatsstichtage, D.17 revidieren (S-3).
10. KONTAMINATION-Inventur ohne WP-10(B) und H-24 W-R2 (S-2); gemeinsame Vorregistrierung loest Reihenfolge (S-6).
11. Data-Harvest: Marktkapitalisierung/Spot-Volumen je Coin (Prio 1), Tardis-Inhaltsprobe, Deribit-Historien-Proben.
