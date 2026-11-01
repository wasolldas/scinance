# KRITIK_PRD - Adversarische Pruefung des PRD Scinance 3.0 und seiner Verfassung (Stand 2026-11-01)

> Rolle: Herleitungs-/Kritikrolle (adversarischer Pruefer des PRD selbst, nicht einzelner Hypothesen).
> Grundlage: vollstaendige Leseliste (`REGELN_UND_LESELISTE.md`), Pfade unter `/home/user/scinance/`. Nur gelesen,
> nichts im Repo geaendert, nichts committet; keine Daten geladen, kein Harvest-Client, keine Siegeldatei, keine
> Outcome-Statistik. Alle Rechnungen sind analytisch oder Simulationen ohne Marktdaten (Abschnitt 10).
>
> **Kennzeichen.** [F] Fakt mit Fundstelle - [R] eigene Rechnung (reproduzierbar, Abschnitt 10) - [U] Urteil des
> Pruefers - [V] Vermutung (nicht belegt, Pruefauftrag) - [P] Vorschlag mit Richtung (Strenge / Testbarkeit /
> neutral) - [Lit.] Literaturhinweis ausserhalb der Akte, in dieser Sitzung nicht verifiziert.
> **Zustaendigkeit.** **N** = Programmfrage des Nutzers (PRD Par. 8; Verfassungs-/Fehlerraten-/REZENZ-Fragen, alles mit
> Etikett "Lockerung"); **O** = Orchestrator kann selbst entscheiden (Rechenkorrekturen, Konstanten, Vorbereitung).
> **Kuerzel.** PRD = `scinance3-impl/PRD_SCINANCE3.md`; DEC/GL = `scinance3-impl/state/decisions.md` / `gate_log.md`;
> KOMP = `scinance3-impl/survey/ERKENNTNIS_KOMPENDIUM.md`; BIL = `scinance3-impl/state/PROGRAMM_BILANZ_2026-10-18.md`;
> R2/R4 = `scinance3-impl/research/R2_TAGES_WOCHEN_HORIZONT.md` / `R4_METHODIK_INFRA.md`; HA2 = `state/herleitung_a2/`;
> INV = `state/prd_analyse_2026-11-01/DATENINVENTAR_2026-11-01.md`; F2R = `scinance2-impl/state/PROGRAM_FINAL_REPORT.md`.

---

## 0. Befund in sechs Saetzen

1. Drei der vier "regierenden Zahlen" sind falsch hergeleitet oder falsch gedeutet: die Horizont-Friktions-Kurve
   unterschaetzt die Kante eines korrelierten Signals um Faktor pi/2 (Mindesthorizonte x2,5 zu lang), die
   Sharpe-Nachweisdauer gilt **identisch** fuer den Praemientest (Klasse P braucht SR_eff >= 2,49 je 12-Monats-Fenster),
   und der WP-7-Rauschboden ist eine algebraische Identitaet, die die gesuchte Breite gar nicht enthaelt (K-1..K-3).
2. Das Gate-Geruest kontrolliert die Fehlerrate (C.10 gemeinsam <= 0,25 %, A2-Pilotroute 5e-18), aber **niemand die
   Gesamt-Power**: lokal begruendete "Strenge"-Schritte (Produktregel, doppelt gezaehlte Null-Bedingung, Stress bindend,
   Maximum-Regeln, UNBELEGT-Default 0,95) blaehen z. B. die A2-MDE von 18,8 auf 32,1 bp auf (Daten x2,9) (K-4..K-6).
3. Die Programmregeln behandeln Power-, Prior- und Fensterlaengen-Wahlen als Torpfosten, obwohl sie die Testgroesse
   alpha nicht beruehren (die Schwelle rechnet mit der Lauf-SE); das erzeugt Wartezeit und Nutzer-Rueckfragen ohne
   Validitaetsgewinn (K-7..K-9).
4. Die Literatur-Prior-Pflicht schuetzt keine Fehlerrate, sondern nur das Datenbudget; sie blockiert A1, A2, H-33 und
   fm8 und ist durch eine registrierte oekonomische Mindestgroesse (SESOI) ersetzbar, mit der A2 heute registrierbar
   waere und A1/VRP auf 12-Monats-Fenstern definitiv (nicht "UNBELEGT") geschlossen waeren (K-10).
5. Die Pivot-Diagnose ("2.0 starb an der Friktionswand") ist fuer drei der fuenf genannten Hypothesen falsch, Klasse P
   kann nach eigener Verfassung nie mehr als PARK erreichen (L-12-Verstoss), und REZENZ wird nur in Richtung Strenge
   angewandt (K-11, K-12).
6. Mehrere Datenannahmen sind ueberholt (tardis-Monatsstichtage 2019-2026, H-21 durch Luecken faktisch tot, OI-Tiefe
   still fallengelassen, Negativ-Panel aus `publicTrade` baubar), und das PRD ist als Verfassung nicht mehr lesbar ohne
   220 kB DEC-Nachtraege (K-13, K-14).

---

## 1. Die vier regierenden Zahlen (Auftrag 1)

### K-1 Horizont-Friktions-Kurve: inkonsistentes Kantenmodell, Faktor-2-empfindliche Kosten
- **Fundstelle.** PRD Par. 1 Tabelle Zeile 1; PRD 9.2 K-0.1; R4 K-0.1 und 1.2.d (`0,798*(2p-1)*693 bp - 11 bp` mit
  `p = 0,5 + arcsin(IC)/pi`); PRD 4.1 "IC_min = 0,062"; DEC-73 E4 (Etikett `unter_wand`).
- **Befund [F].** Die Kurve setzt `Kante = (2p-1) * E|r_h|` (Trefferquote unabhaengig von der Bewegungsgroesse) und
  rechnet IC per Gauss-Konkordanz `p = 1/2 + arcsin(IC)/pi` in eine Trefferquote um.
- **Rechnung [R].** Unter demselben bivariaten Normalmodell, aus dem `arcsin` stammt, gilt exakt
  `E[sign(s) * r] = IC * 0,798 * sigma_h` (weil `E[r|s] = IC*sigma*s/sigma_s`); die PRD-Formel liefert
  `(2/pi)*arcsin(IC)*0,798*sigma_h`, also fuer kleine IC den Faktor pi/2 = 1,571 zu wenig (bei IC 0,05: 1,570).
  Der Mindesthorizont skaliert mit Kante^-2, also Faktor 2,47:

  | Fall (BTC sigma_1d 262 bp) | PRD | Gauss-konsistent |
  |---|---:|---:|
  | p = 0,55, Taker 11 bp | 6,6 h | 2,7 h |
  | Wochen-IC 0,05, Taker 11 bp | 2,73 Tage | 1,11 Tage |
  | Wochen-IC 0,05, Maker gemessen 2x(2,0 + 0,7 adv_sel) = 5,4 bp RT (DEC-71) | 0,66 Tage | 0,27 Tage |
  | Break-even Wochen-IC Einzelposition / x2 "oekonomisches Minimum" | 0,031 / 0,062 | 0,020 / 0,040 |
  | Kosten halbiert (5,5 bp), p = 0,55 | 1,7 h | 0,7 h |

  Das 1-s-Orakel (0,71 bp) bleibt robust (selbst x2,5 = 1,8 bp << 11 bp).
- **Gegenlaeufige Fehler [U].** (a) Die Maker-Konstanten (p_fill, adv_sel, DEC-71) sind fuer **uninformierte** Quotes
  gemessen; eine signalgetriebene passive Order wird bevorzugt gefuellt, wenn das Signal falsch ist (PRD 4.3 nennt genau
  dieses adversariale Fixture) - die 53-min-Maker-Frontier ist optimistisch. (b) Fette Raender senken `E|r|/sigma`
  unter 0,798 - Kante kleiner. (c) Die 15-bp-Gesamtwand enthaelt ~4 bp ungemessene Slippage bei einem gemessenen
  Ein-Tick-Spread von 0,016-0,054 bp (PRD 9.2 B.1/B.2) - Kosten eher zu hoch. Netto: die Grenze "Tageshorizont" ist
  je nach Lesart irgendwo zwischen ~0,3 und ~2,7 Tagen; sie ist eine Konvention, keine Herleitung.
- **Folge [U].** Die Mission "kein Kandidat unter Tageshorizont" (PRD 1, CLAUDE.md Mission) steht auf einer Zahl mit
  Fehlerfaktor 2,5 (Modell) x 4 (Kosten x2) im Horizont. Das PRD benutzt zudem zwei unvereinbare Modelle: im
  Portfoliorahmen die Gauss-Regression (Dezilfaktor 3,51 = 2*E[z|Top-Dezil], L-18), im Einzelpositionsrahmen die
  magnitudenunabhaengige Trefferquote. L-18 verlangt ausdruecklich, dass ein zu pessimistischer Faktor dokumentiert
  wird - hier ist ein zweiter.
- **Vorschlag [P].** (a) K-0.1 als Kurvenschar (magnitudenunabhaengig / Gauss) mit gemessenen Kosten (Taker; Maker inkl.
  adv_sel und p_fill mit Taker-Rueckfall) neu fuehren, L-18-Vermerk, IC_min 0,062 -> 0,040 (neutral, **O**).
  (b) Stundenhorizonte (1-24 h) nicht per Mission ausschliessen, sondern per SESOI-Feasibility (K-10) entscheiden
  (Testbarkeit des Suchraums, **N**, weil Mission/PRD 1).
- **Rueckwirkung.** DEC-73 E4: A3 bleibt `unter_wand` (0,03 < 0,040), Abstand halbiert. Kein GL betroffen (Etikett).

### K-2 Sharpe-Nachweisdauer: "Praemie statt Sharpe" verkuerzt nichts - Klasse P war a priori untestbar
- **Fundstelle.** PRD Par. 1 Zeile 2 ("Sharpe ist NIE urteilstragend; urteilstragend ist die Praemie selbst"), PRD 3.6,
  9.2 K-0.2; GL-033, GL-034; BIL 2.2/2.3.
- **Rechenfehler [R].** PRD 3.6 und 9.2: "Bei Tagesdaten (q = 365) ... SR 2,0 ergibt exakt 1,80 statt 1,55 Jahre".
  Mit q = 365 ist `T = 2,4865^2*(1 + 4/730)/4 = 1,554` Jahre (Korrektur 0,5 %); 1,80 ergibt sich nur mit q = 12.
- **Kernfehler [R].** Der Test "mean(prem) > 0" hat die Statistik `t = mean/(sd/sqrt(n)) = SR_p * sqrt(n)`. Seine
  Nachweisdauer bei Power 0,80, alpha 0,05 einseitig ist `T = 2,4865^2 * c / SR_ann^2` - dieselbe Lo-Arithmetik
  (ohne den vernachlaessigbaren Term SR^2/2q). Umbenennen in "Praemie" kauft keine Power. Unter C.10 mit
  12-Monats-Fenstern und Power 0,80 je Fenster braucht jede Praemie ein **effektives Brutto-SR >= 2,49 p.a. je
  Fenster** (24 Monate: 1,76; 36 Monate: 1,44; nach Autokorrelation c). Gegenprobe: H-27 `SR_eff = 9,47/(18,6*sqrt(28,2/365)) = 1,83`
  -> 1,84 Jahre je Fenster (= 672 Tage, BIL 2.3, GL-034); A1 bei theta = 1, W1, c = 1: `100,7/(372,9/sqrt(52)) = 1,95` -> GL.
- **Folge [U].** Die GL-012-Ausgaenge von A1 und H-27 waren am 2026-09-02 mit **einer** Zahl je Kandidat
  vorhersagbar (Brutto-SR der Praemienreihe gegen 2,49). Ein Klassen-Feasibility-Check (C.12 auf Klassenebene, wie
  H-07 fuer N = 5) fehlt; stattdessen wurden A1 (DEC-70, 82, 84, 93) und H-27 (DEC-95..97) einzeln hergeleitet.
- **Vorschlag [P].** (a) Klassen-Feasibility vor jeder Herleitung: benoetigtes SR_eff je Fensterlaenge gegen ein
  belegtes oder SESOI-Band (neutral, **O**). (b) Fensterlaenge als abgeleitete Groesse statt fester 12 Monate (K-7;
  Testbarkeit, **N**, weil REZENZ/DEC-99).
- **Rueckwirkung.** GL-033/GL-034 unveraendert, aber ~4 Wochen Herleitungsarbeit vermeidbar.

### K-3 IC-Rauschboden: der WP-7-Ersatzschaetzer ist eine Identitaet - "Klasse W testbar" war ein Falsch-Positiv
- **Fundstelle.** PRD 4.1 ("Dieser Schaetzer enthaelt die tatsaechliche effektive Breite exakt ... annahmefrei
  gegenueber Vol-Heterogenitaet, Sektorstruktur und Marktfaktor"); PRD Par. 1 Zeile 3; L-2b (PRD 2); DEC-67 (B2),
  DEC-73 E1; DEC-74 ("Permutations-Null ist deterministisch E_t[1/sqrt(K_t-1)] (0,0411229 gemessen vs. 0,0411160
  Identitaet)"); DEC-75 B-1 (Faktor ~1,8); DEC-91 (SD(IC_t) W1 0,090/0,130 gegen Boden 0,0486); GL-035 Nebenbefund
  (reale fm8-Wochen-SD 2,3..2,6x der Ein-Faktor-Null); R4 K-0.5.
- **Rechnung [R].** Bei Permutation der Charakteristik innerhalb der Woche ist Spearman(perm, Rendite) exakt nach der
  Null-Verteilung des Spearman-rho fuer K Elemente verteilt, Var = 1/(K-1) - **unabhaengig** von jeder
  Korrelationsstruktur der Renditen. Der Schaetzer kann die effektive Breite nicht enthalten; das PRD hat damit die
  eigene Lehre L-2b ("ein Schaetzer, der die gesuchte Groesse gar nicht enthaelt") im Ersatzschaetzer wiederholt.
  Breite wirkt ueber die **Zeitreihen**-Varianz von IC_t, wenn die Charakteristik mit Faktorladungen korreliert.
  Mit der PRD-eigenen Arithmetik (`detektierbar = 0,344886 * SD`, Schranke 0,03): Boden 0,0486 -> 0,0168 (B2),
  measured 0,0901 -> 0,0311 (**B1**), stress 0,1302 -> 0,0449 (**B1**).
  Nebenbefund: die Zahl "N = 5: 0,098" rechnet mit t = 2 (R4 K-0.5: "detektierbar bei t=2"), nicht mit DEC-51
  (2,4865 -> 0,122).
- **Folge [U].** Der Feasibility-Befund B2 (DEC-67, DEC-73 E1) war ein Falsch-Positiv. Die Kette Erst-, Zweit- und
  Drittfassung H-28..H-30, Vorlaeufe v2..v5e, drei Reviews und die Positivkontrolle (DEC-73..DEC-92) endete in GL-032
  genau dort, wo ein korrekter WP-7-Befund am 2026-09-14 begonnen haette. Die Positivkontrolle hat den Fehler
  gefangen - aber vier Wochen spaeter.
- **Vorschlag [P].** (a) Feasibility jeder Zensusfrage auf der SD der **Teststatistik selbst** (Vorperiode nur
  Streuung + kalibrierte Null, Maximum; inhaltlich DEC-94 (5)) als PRD-Regel fuer Zensus-Pakete (neutral, **O**).
  (b) L-2b operational: jeder Zensus-Schaetzer muss auf einem Null-Fixture mit Faktorstruktur einen anderen Wert
  liefern als auf einem unabhaengigen Panel; eine Identitaet faellt durch (Strenge, **O**).
- **Rueckwirkung.** DEC-67/DEC-73 E1: B1 fuer den Roh-IC statt B2; GL-032 am 2026-09-14 statt 2026-10-12; Ergebnis gleich,
  der beta-neutrale Weg (H-32) waere sofort die einzige Option gewesen.

### K-4 Ein-Fenster-DROP / Zwei-Fenster-Ziel: das nominale Power-Ziel ist nicht die Entscheidungs-Power
- **Fundstelle.** PRD Par. 1 Zeile 4, 3.5, 9.2 K-0.6; DEC-51 (2); DEC-94 (Gegenprobe 0,85 %); DEC-98 E1 (c); BIL Teil C O5/O6.
- **Rechnung [R].** `(1-beta)^2` ist korrekt; bei 0,80 je Fenster ist die Entscheidungs-Power 0,64 bei gemeinsamem
  alpha 0,0025. Bei gleichen Daten und gleichem gemeinsamen alpha haette ein gepoolter Test Power 0,76; fuer
  gemeinsame Power 0,80 braucht C.10 je Fenster 0,894 (+36 % Daten). PRD 3.5 beziffert die DEC-52-Fehlerrate als
  `0,5 x 0,01 = 0,5 %` unter Unabhaengigkeit von Vorzeichenfilter und gepoolter Signifikanz; simuliert sind es 1,00 %
  (nur Vorzeichen) bzw. 0,86 % (mit 0,5x-Screens) - Faktor ~2 in Richtung Lockerung (von DEC-94 korrigiert, z 2,5287).
  K-0.6 "0,42^2 = 0,18, Faktor 4,7": exakt `Phi(1,4-1,6449)^2 = 0,163`, Faktor 5,2 (gering, gegen DEC-52).
- **Folge [U].** DEC-51 (2) nennt 0,80, entschieden wird mit 0,64 (und nach K-5 deutlich darunter). Regime-Robustheit
  ist seit DEC-99 (1) doppelt kodiert (beide Fenster unter C.10 UND juengstes Fenster als notwendige Bedingung).
- **Vorschlag [P].** Power-Ziel auf der vollstaendigen Entscheidungsregel definieren und zwischen (i) C.10 mit
  gemeinsamer Power 0,80 (+36 % Daten, Strenge) und (ii) gepooltem Test alpha 0,0025 plus REZENZ-Screen im juengsten
  Fenster (+8 % gegen C.10-0,80/0,80, gleiche Fehlerrate, neutral) explizit waehlen. **N** (BIL Option 4).
- **Rueckwirkung.** Kein GL kippt (die GL-012-Befunde werden unter einem gemeinsamen Power-Ziel eher strenger).

---

## 2. Power- und Gate-Geruest (Auftrag 2)

### K-5 Kumulierte Strenge ohne Gesamt-Operationscharakteristik
- **Fundstelle.** DEC-94 (5)(6); DEC-98 N7 (4a); DEC-103 E3, E7, N1 (3)(6)(8); HA2 `PILOT_ROUTE_A2.md` 4, 6a; DEC-97 A-2;
  DEC-101 E7 ("Endpower ... report-only"); CLAUDE.md Arbeitsregel 4 ("UNBELEGT ... blockiert ..., nie ein Default").
- **Beleg [F/R].** A2-MDE80 je 12-Monats-Fenster W2 (Zahlen aus DEC-98 N7 und DEC-103 N1):

  | Schritt (W2) | MDE80 bp | MDE-Faktor | Daten-Faktor |
  |---|---:|---:|---:|
  | Einzel-Placebo P2'' | 18,8 | 1,00 | 1,00 |
  | strengste Einzelbedingung P3fix | 19,7 | 1,05 | 1,10 |
  | Produkt der z-Bedingungen (DEC-103 E3) | 23,1 | 1,23 | 1,51 |
  | + Null-Bedingung als eigener Faktor (N1 (8a)) | 24,4 | 1,30 | 1,68 |
  | + Stress-Kalibrierung 2021/22 bindend (N1 (8c)) | 27,2 | 1,45 | 2,09 |
  | + Gate-(4)-Faktor 0,9025 (UNBELEGT, N1 (8f)) | 32,1 | 1,71 | 2,92 |

  Exakte gemeinsame Power (zentral, Bericht) 22,3 bp: der Endwert braucht gegenueber der exakten Rechnung x2,07 Daten.
- **Vier Einzeldefekte [R/U].**
  (a) **Doppelt gezaehlte Bedingung.** Die Null-Bedingung testet dieselbe Statistik gegen tau95 = 1,6533 SE (N1 (3);
  der Test skaliert die Null mit k = SE_Lauf/SD_null, N1 (8b)) - praktisch identisch mit `1,6449 * SE`. Als
  unabhaengiger Faktor im Produkt wird ihre Power quadriert (0,9 -> 0,81). Das ist ein Rechenartefakt, keine Strenge.
  (b) **Produktregel bei gemeinsamem Ereignisterm.** Alle Placebo-Kontraste enthalten dasselbe Freitagsmittel;
  Korrelation ~0,7..0,9. Illustration (Ereignis-SE 6,5; Placebo-SE 3,4/4,5/1,5): bei 22 bp exakt 0,83 gegen Produkt
  0,76; bei 20 bp 0,76 gegen 0,64. Jeder weitere Faktor m erzwingt je Bedingung Power `0,8^(1/m)`: m = 3 -> 0,928
  (MDE x1,25, Daten x1,56), m = 5 -> 0,956 (x1,35 / x1,82). Dasselbe gilt fuer das DEC-52-Gate (DEC-94 (6)): bei A2
  und 16,5 bp Produkt 0,60, exakt 0,69.
  (c) **UNBELEGT als Default - nur in Richtung Strenge.** Der Gate-(4)-Faktor 0,95 je Symbol ist ausdruecklich
  UNBELEGT und geht dennoch in die bindende Zuordnung ein; Arbeitsregel 4 verbietet Defaults. Fuer Priors (theta,
  V-5b, fm8) wird dieselbe Regel blockierend angewandt.
  (d) **Maximum-Regeln stapeln Aufwaertsverzerrungen.** c nach P-3 = Maximum ueber Batch-Means-Ausrichtungen (H-27:
  28,2 gegen Konsens 18,6; MC P(Regel >= 28) = 14 %, DEC-97 A-2), "groessere SE ueber Quellen und Kalibrierungen"
  (DEC-94 (5)), `c = max(1, c_hat)`, `k = max(1, ...)`: das Maximum verrauschter Schaetzer ist systematisch zu gross.
- **Alpha-Seite [F/R].** Dort wird nichts gewonnen: C.10 liegt gemeinsam bei <= 0,25 %, jede weitere
  Intersection-Union-Bedingung senkt die Rate weiter; die A2-Pilotroute hat Zwei-Stufen-Fehlerrate <= 5,4e-18
  (`PILOT_ROUTE_A2.md` 4). H-32: Endpower nach F-WEEK an der Schwelle 0,11..0,75 je nach Variante und m (mom1
  0,75 / 0,44 / 0,20 bei m = 1 / 4 / 11) - "report-only".
- **Folge [U].** Jeder Schritt ist lokal begruendet ("Richtung Strenge"); keine Regel begrenzt die Summe. Die
  Operationscharakteristik der vollstaendigen Kette `P(PASS | mu)` ist nirgends Entscheidungsgrundlage.
- **Vorschlag [P].** (1) Doppelte Null-Bedingung aus dem Produkt streichen (Rechenkorrektur, neutral, **O**).
  (2) Zuordnung ueber die exakte gemeinsame Power (deterministische MC, fester Seed) statt Produkt (Testbarkeit,
  Fehlerrate unveraendert; aendert DEC-94 (6) -> **N**). (3) Pflicht-"OC-Zeile" je Registrierung: P(PASS|0),
  P(PASS|SESOI), P(PASS|Prior) der gesamten Kette inkl. Pilot und FDR; bindend sind ein Fehlerraten-Budget UND ein
  Power-Ziel; ein Strenge-Schritt jenseits des Budgets braucht eine Begruendung auf der alpha-Seite (neutral, **N**).
  (4) UNBELEGT symmetrisch behandeln: entweder RAISE auch fuer Strenge-Defaults oder benannte Defaults in beide
  Richtungen (neutral, **O**).
- **Rueckwirkung.** DEC-103: Zuordnungs-MDE W2 von 32,1 auf ~22..24 bp (zentral exakt 22,3; mit Stress [V,
  extrapoliert] ~25..26). DEC-97: mit Konsens-c Power 0,73 statt 0,575 bei L = 12 (GL-034 bleibt). GL-032: bindend
  stress, measured haette W1 MDE80 0,042 > 0,03 - bleibt GL.

### K-6 Fehlerbudget invertiert: billiges PASS wird teuer abgesichert, endgueltiges Nicht-Wissen wird in Kauf genommen
- **Fundstelle.** PRD 3.1 (C.2-Bestaetigung: "DROP ist endgueltig und append-only"), PRD 3.6 Auflage (2), Par. 5
  Entscheidungsrelevanz-Zeilen (PASS -> nur weiterer Mess-/Tradability-Schritt), DEC-51 (1), BIL Teil C Option 4,
  GL-032..GL-036, STAND Abschnitt 1.
- **Rechnung [R].** Positiver Vorhersagewert eines Mess-PASS bei Basisrate 5 / 10 / 20 % echter Effekte:
  C.10 (alpha 0,0025, Power 0,64) 0,93 / 0,97 / 0,98; gepoolt (0,01; 0,80) 0,81 / 0,90 / 0,95; ein Fenster (0,05; 0,80)
  0,46 / 0,64 / 0,80. Gepoolt mit alpha 0,01 waeren auf W1+W2 erreichbar: A3-Roh-IC measured MDE80 0,024 (< 0,03),
  stress 0,034 (> 0,03); A2 Einzel-Placebo 16,7 bp (Power 0,79 beim einzigen Literaturwert 16,5 bp); H-27 bei
  12-Monats-Fenstern 11,6 VP > 9,47 (bleibt GL).
- **Folge [U].** Ein Mess-PASS kauft laut Verfassung nur den naechsten gegateten Schritt (A1b, Tradability, PARK) -
  billig und reversibel; ein DROP ist endgueltig; ein GL-012 liefert null Information. Die Verfassung setzt das
  alpha 20-fach strenger als ihr nominaler Wert (0,25 % statt 5 %) und laesst die Power unkontrolliert. Ergebnis:
  zwei Monate, fuenf Kandidaten, null Tests (GL-032..036).
- **Vorschlag [P].** Explizites Programm-Fehlerbudget: Mess-Gate gepoolt mit alpha 0,0025..0,01 plus REZENZ-Screen,
  gemeinsame Power 0,80, und eine **Pflicht-Bestaetigungsstufe auf neuen Daten** (vorwaerts, blind) fuer jedes PASS
  vor jeder Tradability-Frage. Stufe 1 Richtung Testbarkeit, Gesamtkette Richtung Strenge. **N**.
- **Rueckwirkung.** A2 (DEC-103) und A3-Roh-IC unter measured (GL-032) waeren testbar; A1, H-27, H-33 bleiben GL-012.

---

## 3. Warteregeln: REZENZ, Blind-Siegel, Einmal-Gut, Pilot (Auftrag 3)

**Einordnung [U] - statistisch notwendig oder Konvention?**

| Regel (Fundstelle) | Status | Wartezeit ohne Erkenntnisgewinn? | gleich strenge Alternative [Lit.] |
|---|---|---|---|
| REZENZ 3.0 (C.18, DEC-99 (1)) | Konvention (inhaltliche Annahme "Regime aendert sich"), nicht statistisch noetig | ja: verbietet Pooling, erzwingt 12-Monats-Fenster (K-2, K-12) | gepoolter Schaetzer + vorab registrierter Stabilitaetstest (K-12) |
| Blind-Siegel (DEC-96 E3, DEC-98 E1 (b)) | noetig nur fuer noch nicht registrierte Statistiken; als Programmsperre Konvention | ja: juengste Daten fuer alle Klassen gesperrt (K-8) | Pre-Registration mit Lockbox je Design |
| Einmal-Gut (BIL Teil C, DEC-98 E1 (d)) | Folge des Ein-Blick-Designs mit fester Fallzahl | ja: Reihenfolge-Frage seit 2026-10-18 offen | gemeinsame Vorab-Registrierung + gruppensequentielles Design (alpha-spending) |
| Pilot-Verbrauch (DEC-99 (5)) | noetig (Data-Snooping), aber die zusaetzliche K-Strafe im Test nicht | teilweise (K-9) | Stichprobenteilung / adaptiver Kombinationstest |
| C.17 Offenlegung (KOMP C.17) | noetig (macht ein PASS nicht-konfirmatorisch) | nein - aber die Ausweitung zur Pflicht, Agenten blind zu halten, ist im oeffentlichen Repo nicht durchsetzbar (B-2, K-8) | Lockbox statt Agenten-Blindheit |
| Nested CV | fuer Ein-Statistik-Tests ohne Nutzen; sinnvoll nur fuer Variantenwahl (A3 K = 7, H-32 K = 4) | - | Wahl EINER Variante im Pilot, Test nur dieser (K-9) |

### K-7 Power-, Prior- und Fensterlaengen-Wahlen sind keine Torpfosten (Kategorienfehler)
- **Fundstelle.** DEC-93 E3 ("Wechsel jetzt ... Torpfosten-Verschiebung"); DEC-96 E2 (L nur aus {6, 9, 12}); DEC-97
  ("Fenster ueber 12 Monate ... ist ausgeschlossen"); DEC-98 E4 (Option 4 ausgeschlossen); DEC-94 (1)(4) (Schwelle
  `z_krit * SE`, SE im Lauf aus den Lauf-Daten); REGELN ("so wenig menschliches Eingreifen wie moeglich").
- **Befund [F].** Die Testschwelle rechnet mit der SE des Laufs (DEC-94 (1)(4)); die Groesse des Tests (alpha) haengt
  nicht von der Power-Zeile ab.
- **Rechnung/Lit. [R/Lit.].** Designwahlen, die nur Nuisance (Streuung, Autokorrelation) einer Vorperiode und externe
  Priors benutzen und vor jedem Outcome des Urteilsfensters fallen, aendern alpha nicht (Stein 1945, Zweistufen-Verfahren;
  verblindete Fallzahl-Neuschaetzung, Kieser/Friede 2003 [Lit.]). Einzige Ausnahme: Nuisance und Mittelwert sind
  abhaengig (Schiefe) oder die Wahl wurde von outcome-nahen Groessen beeinflusst - das ist eine C.17-Frage, keine
  Torpfosten-Frage.
- **Folge [U].** Die einzigen Kosten einer zu optimistischen Power-Zeile sind verbrauchte Daten (ein schwacher Test),
  kein Falsch-Positiv. Indem das Programm jede Power-/Prior-/L-"Gabelung in Richtung Testbarkeit" wie eine
  Schwellenverschiebung behandelt, muss jede Designanpassung als "Lockerung" zum Nutzer (DEC-99, DEC-103 Pilotroute,
  Reihenfolge-Frage). Das widerspricht dem Autonomie-Ziel, ohne die Fehlerrate zu schuetzen.
- **Vorschlag [P].** Verfassungszeile "nuisance-adaptive Designwahl": vorab registriertes Design-Menue (L, gepoolt/C.10,
  Placebosatz) plus mechanische Auswahlregel nur auf Vorperioden-Nuisance und registriertem SESOI/Prior; die Auswahl
  ist keine Lockerung und wird vom Orchestrator autonom ausgefuehrt; C.17-Inventur bleibt Pflicht. Testbarkeit,
  alpha neutral. **N** (Verfassungsauslegung), Vorbereitung **O**.
- **Rueckwirkung.** DEC-96 E2 / DEC-97 / GL-034: H-27 waere mit L ~ 22 Monaten je Fenster (672 Tage, BIL 2.3) auf den
  blinden Fenstern registrierbar gewesen (Urteil ~2030, mit K-8 frueher abbrechbar) statt GL-012. DEC-93 E3: Ergebnis
  unveraendert (theta, siehe K-10).

### K-8 Blind-Siegel, Einmal-Gut und Reihenfolge-Frage: Hortung verderblicher Daten
- **Fundstelle.** DEC-96 E3; DEC-97 ("Blind-Siegel bleibt bestehen"); DEC-98 E1 (b)(d), E4 (b) (offen seit 2026-10-18);
  DEC-98 N5 (2) ("Ein VRP-Urteil ist auf keinem Datenweg vor 2029 erreichbar"); DEC-99 (1)(5); DEC-103 N1 (2)
  (Blindheit der A2-Vorperiode "durch Disziplin, nicht durch die Daten geschuetzt"); F2R 8 und KOMP-Bezug DEC-15
  (2.0: Pre-Discovery-OOS "dem Forward-Warten methodisch und operativ ueberlegen").
- **Befund [F].** Das Siegel sperrt programmweit jede BTC/ETH-Vol- und Renditestreuungs-Statistik ab 2026-07-01, also
  auch Kalibrierungen der Klassen W und A1 (DEC-98 E1 (b)); geschuetzt wird eine nicht registrierte kuenftige
  VRP-Hypothese, die vor 2029..2033 auf keinem Weg testbar ist. Die Reihenfolge-Frage liegt seit zwei Wochen beim Nutzer;
  bis dahin rechnet niemand auf den juengsten Daten.
- **Urteil [U].** (1) "Einmal-Gut" ist eine Eigenschaft von Ein-Blick-Designs mit fester Fallzahl. DEC-98 E1 (d)
  raeumt selbst ein, dass alle vor der ersten Rechnung registrierten Hypothesen einen Abschnitt teilen - die
  Reihenfolge-Frage loest sich auf, wenn alle Blindperioden-Designs gleichzeitig vorab registriert werden.
  (2) REZENZ macht blinde Daten verderblich: nach DEC-99 (1) endet das Urteilsfenster am juengsten nutzbaren Tag;
  ungenutzte Fenster verlieren mit jedem neuen nutzbaren Tag ihren Urteilswert. Horten ist nicht kostenlos.
  (3) Blindheit durch Agenten-Disziplin in einem oeffentlichen Repo ist bruechig (B-2-Kanal); eine Lockbox
  (Registrierungs-Hash vor jedem Zugriff, codegesicherter Einmalzugriff auf die Urteilsstatistik) schuetzt die
  Validitaet unabhaengig davon, was Agenten gesehen haben. (4) 3.0 hat die 2.0-Lehre umgedreht: statt vorab
  registrierter historischer OOS-Fenster wird vorwaerts gewartet.
- **Rechnung [R].** Gruppensequentielles Design, 4 vorab registrierte Blicke (O'Brien-Fleming, einseitig, eigene
  Simulation): alpha 0,05: Maximalumfang x1,04, erwarteter Umfang unter H1 0,82; alpha 0,0025: x1,02 / 0,88; mit
  nicht bindender Futility-Grenze (Z < 0 an den Zwischenblicken) erwarteter Umfang unter H0 0,57..0,65 bei
  Maximalumfang x1,04 (alpha 0,0025) bzw. x1,20 (alpha 0,05). Lan/DeMets
  alpha-spending und Jennison/Turnbull [Lit.]; mehrfach nutzbarer Holdout (Dwork et al. 2015 [Lit.]) fuer wiederholte
  Nuisance-Abfragen.
- **Vorschlag [P].** (a) Default der Reihenfolge-Frage: gemeinsame Vorab-Registrierung aller Blindperioden-Designs
  (VRP mit abgeleiteter Fensterlaenge, ggf. W/A1) mit GSD-Blicken und Lockbox je Design; Siegel-Umfang danach auf die
  registrierten Statistiken beschraenken (Testbarkeit: erwartete Wartezeit -12..-43 %, alpha neutral, **N**).
  (b) Vorbereitung der GSD-Grenzen in `power_p1` (neutral, **O**).
- **Rueckwirkung.** DEC-96 E3 / DEC-98 E1 (b): Siegelumfang; DEC-97: H-27 mit GSD; die W/A1-Fenster ab 2026-10 waeren
  nutzbar.

### K-9 Pilot-Route: Uebergabe nur bei voller Test-Staerke, danach verworfen - und doppelt bestraft
- **Fundstelle.** DEC-99 (2a)(3)(5); DEC-101 E7 (Regel U-4); GL-035; HA2 `PILOT_ROUTE_A2.md` 0, 2, 4, 7; DEC-103 N1 (9);
  DEC-74 (e) und DEC-99 (3) (BH-Nenner fest, nicht uebergebene Varianten mit p = 1).
- **Rechnung [R].** U-4/U-A2 verlangen `x_P >= c` mit c = MDE80 des Tests am Pilotpunkt. Per Konstruktion gilt
  `P(Uebergabe | mu = c) = 0,5`; die Zwei-Stufen-Power bei mu = c ist <= 0,5 x 0,8 = 0,4. A2: c = 32,1 bp,
  SE_P = 4,10 -> Schwelle bei t = 7,85; P(Uebergabe) bei 16,5 bp 7e-5, bei 25 bp 0,042; Pilot-alpha 2,4e-15.
  H-32 mom1: c = 0,0205, SE_P 0,0116 -> P(Uebergabe | 0,03) = 0,79, P(. | 0,02) = 0,48.
- **Urteil [U].** Der Pilot wird nicht als Prior benutzt, sondern als zweiter Test in voller Staerke, dessen Evidenz
  danach verworfen wird. Zusaetzlich bleiben nicht uebergebene Varianten im festen BH-Nenner des Tests, obwohl die
  Auswahl auf unabhaengigen Daten stattfand (Stichprobenteilung: der konfirmatorische Test der ausgewaehlten Variante
  braucht keine Korrektur fuer die nicht ausgewaehlten, Cox 1975 [Lit.]) - doppelte Selektionsstrafe. Fuer H-32 war
  das Ergebnis trotzdem richtig (mom negativ, rev_gap zu schwach); fuer A2 ist die Route ein teurer Weg zu GL-012
  ("praktisch nie", `PILOT_ROUTE_A2.md` 0).
- **Alternativen [P/Lit.].** (i) Uebergabe ueber Assurance/praediktive Power (O'Hagan/Stevens/Campbell 2005 [Lit.]):
  uebergeben, wenn P(Test-PASS | Pilot-Posterior) >= 0,3..0,5; (ii) adaptiver Zwei-Stufen-Kombinationstest
  (Bauer/Koehne 1994 [Lit.]) - Pilot-Evidenz zaehlt mit, REZENZ ueber einen Screen im juengsten Fenster; (iii) einfacher
  Screen (Vorzeichen und t >= 1), alpha traegt allein der Test. Dazu: nicht uebergebene Varianten aus dem
  konfirmatorischen Nenner nehmen. Testbarkeit, alpha unveraendert, **N** (DEC-99 ist Nutzerentscheid).
- **Rueckwirkung.** DEC-103 Pilotroute bekaeme fuer 20..30-bp-Effekte eine reale Chance; GL-035 unveraendert.

---

## 4. Priors (Auftrag 4)

### K-10 Literatur-Prior-Pflicht: Ressourcenregel im Gewand einer Validitaetsregel
- **Fundstelle.** DEC-51 (2); CLAUDE.md Arbeitsregel 4; PRD 5.2 (Vorbedingung V-5); PRD 3.1 (v2-Ausdehnung von C.2 auf
  Feasibility-Kill-Bedingungen); DEC-93 E2; DEC-98 N1, N2; DEC-102 E3, N1; DEC-103 (V-5b); PRD 4.1 (`IC_prior = 0,03`
  [sek: R2 0.3C]); R2 Abschnitt 0.3 ("realistisch angesetzten IC von 0,03"); PRD 5.1 Etikett (36 bp/Woche); PRD 9.2 B.7.
- **Befund [F].** Blockiert durch UNBELEGT: theta (A1), V-5b (A2), fm8-Prior (H-32 vor dem Pilot), H-33, VRP-Niveau
  (Band 3,2..10,5 VP, Faktor ~11 in der Dauer). Volltexte sind aus der Sitzung nicht erreichbar oder kostenpflichtig.
- **Urteil [U].** (1) Nach K-7 schuetzt ein Prior keine Fehlerrate, er steuert nur Power und Regime; die Pflicht
  schuetzt allein das Datenbudget. (2) Sie widerspricht REZENZ: akzeptiert werden LTW (2014-2018), Aktienoptionen
  (Ni/Pearson/Poteshman), Almeida (2017-2022) - aeltere oder fremde Regime -, waehrend eigene Daten 2021-2024 als
  Evidenz ausgeschlossen sind. (3) Publizierte Effekte sind nach oben verzerrt (Rueckgang ausserhalb der Stichprobe
  bzw. nach Publikation ~26..58 %, McLean/Pontiff 2016 [Lit.]) - Literatur-Priors erzeugen eher zu optimistische
  Power-Zeilen. (4) Die Belegregel wurde
  selektiv angewandt: `IC_prior = 0,03` ist die Setzung eines Recherche-Agenten (R2 0.3), wurde als [sek] akzeptiert und
  trug die gesamte Klasse-W-Arbeit; DEC-98 N2: fuer ein breites Perp-Universum nicht gestuetzt. R3s 12 bp und R2s
  Erosionsindizien wurden dagegen als UNBELEGT verworfen.
- **Rechnung [R] - SESOI statt Literatur-Prior.** Registriert wird die kleinste oekonomisch relevante Wirkung
  (aus K-1 korrigiert und gemessenen Kosten); Feasibility: MDE80 <= SESOI; ein DROP heisst dann "kein Effekt >= SESOI"
  (mit Aequivalenz-Logik informativ, Lakens 2017 [Lit.]).

  | Kandidat | SESOI (Herleitung) | MDE80 (Akte bzw. [R]) | Befund |
  |---|---|---|---|
  | A2 | 2 x 11 bp Taker = 22 bp (Maker gemessen 2 x 5,4 = 10,8 bp) | Einzel 18,25/18,8; exakt gemeinsam 21,2/22,3; gepoolt 16,7 (alpha 0,01) / 19,3 (0,0025) | gegen die Taker-SESOI registrierbar, ohne V-5b |
  | A1 | 36 bp/Woche (PRD 5.1 Etikett) | 128,6 bp (W1, c = 1) | strukturell untestbar, theta irrelevant (12,8 Jahre je Fenster) |
  | VRP | ~1,5 VP (2 x 25 % von 3 VP, B.7) | 12,9 VP (L = 12) | strukturell untestbar |

- **Weitere Alternativen [P].** Minimal-Effekt-Lesart (registriert "Effekt >= MDE80 des Designs", PASS/DROP relativ
  dazu gelesen); Bayes-Prior (skeptische Verteilung N(0, tau^2), tau aus dem Literaturband, Assurance); Pilot (K-9).
  Fehlt nur die Richtung (DEC-58 E4, V-5c), loest ein zweiseitiger Test die Blockade zum Preis MDE x1,13 / Daten x1,27
  [R].
- **Folge [U].** Die v2-Ausdehnung von C.2 auf Feasibility-Kills (PRD 3.1) hat die natuerliche SESOI verbaut. Der
  C.2-Grund (H-04 waere ein endgueltiger DROP gewesen) trifft auf GL-012 nicht zu: GL-012 ist kein Verdikt.
- **Vorschlag [P].** Feasibility gegen registrierte SESOI (oder MDE-Lesart), Literatur nur als Bericht; C.2 bleibt fuer
  PASS-Bedingungen unangetastet. Testbarkeit (A2) und Klarheit (A1/VRP definitiv statt "UNBELEGT"). **N**.
- **Rueckwirkung.** DEC-103: A2 auf W1/W2 registrierbar ohne Pilotroute; DEC-93: A1 geschlossen aus Strukturgruenden,
  nicht wegen theta; DEC-102/GL-036: H-33 bleibt GL (SESOI fuer Reversal ~0,017 auf IC-Skala [V, fm8-Umrechnung
  UNBELEGT] gegen MDE80 0,040).

---

## 5. Oekonomische Annahmen (Auftrag 5)

### K-11 Die Pivot-Diagnose ist ueberzeichnet; die Wand ist ein Parameter, kein Naturgesetz
- **Fundstelle.** PRD 1 "Der Pivot" ("2.0 hat sechsmal dieselbe Friktions-Arithmetik ... gemessen (H-03, H-04b, H-05c,
  H-09, H-24 - alle 80-500x unter der Wand)"); KOMP A.2 H-03 (Surrogate-p ~1,0), A.5 H-09 (0/10 Zellen, Rauschmuster),
  A.8 H-24 (IC30 negativ, p 1,0); PRD 9.2 B.1-B.3; DEC-71; PRD 8.2; DEC-58 E5.
- **Befund [F].** Nur H-04b und H-05c starben an der Friktion. H-03 starb am Nulleffekt (Surrogate-p ~1,0, die
  Wand-Relation ist nachrangig), H-09 an Rauschen, H-24 am falschen Vorzeichen. Die Wand: 11 bp = VIP0-Taker-Gebuehr
  (B.3), ~4 bp Slippage ungemessen (B.1) bei Ein-Tick-Spread (B.2) und gemessenem Maker-adv_sel 0,6..0,8 bp (DEC-71);
  die tatsaechliche Gebuehrenstufe des Nutzers wurde nie erfragt (8.2 fragt Kapital, Steuer, r_opp); die
  [sek]-Gebuehrenaenderung 2026-09-01 ist unverifiziert (DEC-58 E5); Steuer/Kapital offen seit 2026-09-02.
- **Urteil [U].** Der dominante 2.0-Fehlermodus war "kein Signal", nicht "zu teuer". Ein Pivot, der nur der Wand
  ausweicht, adressiert ihn nicht; die Wahrscheinlichkeit, auf langen Horizonten erneut "kein Signal" zu finden, sinkt
  dadurch nicht. Die Wand bestimmt die SESOI (K-10) - ihre Eingangsgroessen sind deshalb entscheidungsrelevant.
- **Vorschlag [P].** (a) PRD 1 korrigieren (neutral, **O**). (b) Wand als Parametersatz (VIP0-Taker; Maker gemessen mit
  p_fill/adv_sel; Nutzer-Stufe) mit Sensitivitaet (neutral, **O**). (c) Nutzer beantwortet 8.2 plus Gebuehrenstufe
  (neutral, **N**).
- **Rueckwirkung.** Keine direkte; Voraussetzung fuer K-10.

### K-12 Klasse P endet per Verfassung in PARK; REZENZ wirkt nur in Richtung Strenge; Zahler-Zeile formal
- **Fundstelle.** PRD 3.6 Auflagen (1)(2) ("PARK, nicht WEITER"; "Kein Kapitalschritt folgt aus einem P-A-PASS"); PRD 2
  L-12; PRD 8.1 Default (b); DEC-99 (1)(2); DEC-103 N1 (8c) (Stress-Kalibrierung 2021-06..2022-05 bindet A2);
  DEC-98 N7 (8) (Vorperioden-Vol-Regime Faktor 2,3); DEC-96 E2 (Nuisance 2021-03..2024-05); PRD 3.3.9c, 5.1 (Zahler
  "Mechanismus unveraendert"), L-16.
- **Urteil [U].** (1) Das bestmoegliche Ergebnis der Klasse P ist PARK (MinTRL > Historie auf absehbare Zeit) - L-12
  verbietet woertlich, eine solche Hypothese einzuplanen. Zusammen mit K-2 (SR_eff >= 2,49 je Fenster) ist Klasse P
  doppelt leer, obwohl sie das erste Suchgebiet der Mission ist. (2) REZENZ-Asymmetrie: aeltere Daten sind als Evidenz
  ausgeschlossen, als Nuisance aber zulaessig und sogar bindend (Stress 2021/22 fuer A2-Fenster 2024-2026) - wenn das
  Regime so verschieden ist, dass es nicht urteilen darf, ist auch die Nuisance-Uebertragung fraglich. Alt-Daten werden
  nur in Richtung Strenge benutzt. (3) Die Zahler-Zeile ist so formal geblieben wie L-16 es 2.0 vorwarf: A1 "Mechanismus
  unveraendert"; fuer A2/VRP keine Pruefung, ob sich nach 2024 die Hedger/Verkaeufer verschoben haben (gelistete
  ETF-Optionen, Renditeprodukte, die Vol verkaufen [V]).
- **Vorschlag [P].** (a) Klasse P entweder als reines Mess-/Aufzeichnungsprogramm fuehren oder eine Kapitalregel ohne
  MinTRL definieren (z. B. Erwartungsverlust mit Stress-Szenarien) - **N**. (b) REZENZ als pruefbare Hypothese: gepoolter
  Schaetzer plus vorab registrierter Stabilitaets-/Zerfallstest (Interaktion mit Post-2024, Aequivalenzmarge) statt
  harter Schnitt - Testbarkeit (mehr Daten) und Strenge (expliziter Stabilitaetstest), **N**. (c) Symmetrie-Regel:
  bindende Nuisance aus dem juengsten Vorfenster, aeltere nur als Sensitivitaet (neutral, **O** nach N-Entscheid zu (b)).
- **Rueckwirkung.** DEC-103: W2-Zuordnungs-MDE ohne Stress-Bindung 24,4 statt 27,2 bp (N1 (6)); DEC-99 Pilot-/REZENZ-Logik.

---

## 6. Datenannahmen gegen das Dateninventar (Auftrag 6)

### K-13 Ueberholte, uneingeloeste oder nie gepruefte Datenannahmen

| PRD-/Akte-Annahme (Fundstelle) | Stand laut INV 2026-11-01 bzw. Akte | Folge / Richtung |
|---|---|---|
| REST-Backfills auf dem Nutzer-PC, ~41 min (PRD 7.1); "Klines und Funding NICHT in den Harvester" (PRD 7.2 (5)) | `bybit/rest.kline1d` und `rest.fundingRateAll` ALL 2021-01-01..2026-10-31 lueckenlos im Archiv; Bybit-REST aus der Cloud geo-gesperrt (DEC-81, DEC-83) | Irreversibilitaets-Kriterium ignorierte Erreichbarkeit; 7.1/7.2 ueberholt (neutral, O: Text) |
| PIT-Roster "grundsaetzlich nicht nachholbar" (PRD 7.2 (1)) | Universum per Delisting-Register + Kerzen geschlossener Kontrakte rekonstruiert (DEC-100 N1); Instruments-Schnappschuss erst ab 2026-10-20 | Annahme zu absolut; nicht rekonstruierbar sind nur Instrumentparameter-Historien (Caps, Intervalle) |
| OI-Tiefe "der kritischste offene Datenpunkt" (PRD 7.2 (3)) | `bybit/rest.openInterest` nur 5 Symbole (BTC/ETH ab 2024-03, Rest ab 2026-03); keine DEC zur Probe gefunden (grep) | still fallengelassen; Universums-OI fehlt (O: Probe oder ausdruecklich streichen) |
| A5: "deribit/tickers ~38 Tage ... reicht fuer kein urteilstragendes Fenster" (PRD 5.5); KOMP D.17 "Tardis ... endgueltig tot" | `tardis/options_chain` 91 Stichtage 2019-04-01..2026-10-01 (386 GB, ein Tag je Monat); `deribit/rest.settlements` ab 2017, `rest.deliveryPrices` ab 2016 | [V] monatliche Halte-bis-Verfall-PnL (Skew, VRP mit nicht ueberlappenden Monatszielen) fuer ~91 Monate rekonstruierbar - unabhaengig von der H-26-Sperre der E.6-Reihenfolge; Inhaltsprobe C.8 noetig (Testbarkeit, O) |
| A2-Placebos ueber "verfallsfreie" Tage, V-5(a) fragt nur nach Wochenverfaellen (PRD 5.2, 4.4) | seit 2020-03-25 jeder Kalendertag Verfallstag (DEC-98 N5 (3)) | Design war nie umsetzbar; P2 von Anfang an kontaminiert |
| Negativ-Panel XRP/BNB braucht Datenauftrag (DEC-103 E5) | `bybit/publicTrade` XRP ab 2021-05-13, BNB/SOL ab 2021-06-29 lueckenlos; WP-0-Bar-Cache baute 1-min-Bars aus Trades fuer 5 Symbole (KOMP F.2) | [V] Auftrag vermeidbar: Minutenbars aus Trades (Aufwand ~29 MB je Symbol-Tag laut INV-Mittel, d. h. zweistellige GB) (O) |
| H-21 "GESPERRT bis 2026-12-27", zwei feste 90-Tage-Fenster lueckenlos (KOMP A.7, E.1) | `bybit/allLiquidation` BTC 125/139 Tage ab 2026-06-16; die 14 fehlenden Tage passen in der Zahl zu den bekannten Luecken 06-26, 07-06..07-16, 08-01, 08-14 (UEBERGABE_2026-10-09 Abschnitt 4) [V]; davon 13 in W1 (07-01..09-28) | H-21 ist in der registrierten Form nie entsperrbar; in 3.0 nirgends neu bewertet (O: GL-Vermerk "nicht entsperrbar") |
| H-26 "Entsperrung ~Mitte November 2026" (KOMP A.9, E.2) | `deribit/publicTrade` 251/457 Tage; fruehestens 2027-04-06 (DEC-98 N4) | Akte korrigiert, KOMP nicht |
| WP-10(B)-Stresszelle leer, Maker im Stress RAISE bis >= 10 Stress-Tage (DEC-71 E2) | `bybit/orderbook` BTC 1.043 Tage ab 2023-01-18 (Snapshot+Delta-Aera laut WP-1, KOMP A.10) | [V] Stress-Tage 2023-2025 (z. B. der benannte 2025-10-10) evtl. mit L2 belegt - Pruefauftrag (O) |
| `publicTrade` 5 Symbole als "Voraussetzung fuer Horizonte von Tagen bis Wochen" (PRD 9.2 B.16) | Klasse W laeuft auf `kline1d` ALL (~1.100 Perps); Trades nur fuer A2/HF relevant | Konstante B.16 inhaltlich ueberholt |
| A4: Quotes "seit 2026-06-16" (BIL 1.3) | datierte Futures erst ab 2026-10-20 in `rest.tickers15m` (DEC-98 N4 (a)) | A4 vier Monate spaeter; siehe K-14 (a) |

- **Vorschlag [P].** Datenannahmen-Register (jede PRD-Datenaussage mit Katalog-Pruefdatum), Inhaltsproben fuer
  `tardis/options_chain` und L2 2023-2025, H-21 formal schliessen (neutral/Testbarkeit, **O**).

---

## 7. Innere Widersprueche und Definitionsluecken (Auftrag 7)

### K-14 Liste
- (a) **A4-Fenster.** PRD 5.4: ">= 8 vollstaendige Verfallzyklen (Quartale = 2 Jahre)" und zugleich "Gate-Lauf in 12+
  Monaten"; die Power-Zeile rechnet `0,879 sigma_w` mit N = 8, das Gate verlangt die Schwelle "in beiden Haelften" (4 je
  Haelfte -> 1,243 sigma_w; BIL 2.5 "doppeldeutig"). Mit Quotes ab 2026-10-20 sind 8 Quartale fruehestens Ende 2028 voll.
- (b) **Sharpe "nie urteilstragend" vs. A1-Gate (2).** Die A1-Selektionsdecke ist in SR-Einheiten (0,60, PRD 5.1),
  verglichen mit einer Mittelwert-Statistik in bp; erst DEC-94 (7) stellt auf z-Einheiten um.
- (c) **Schwellenfaktor.** PRD 5.1-5.4 setzen den MDE-Faktor 2,4865 als Schwelle (DEC-94: "verwechseln MDE-Faktor und
  kritischen Wert") - fuenf Wochen lang Grundlage der A3-Fassungen (DEC-74 (d)).
- (d) **STRESS_ABS gegen REZENZ.** 99-Perzentil der Gesamthistorie (DEC-56) liefert in den Urteilsfenstern 2 bzw. 1 Tag
  (DEC-74 N (1)); Folgen: Stresszelle leer (DEC-71), 27 < 30 (DEC-63), PRD 3.6 Auflage (4) "effektives N = Zahl der
  Stress-Episoden" strukturell ~1..2. Der Design-Parameter wurde nie auf Erreichbarkeit geprueft (L-1 auf eigene
  Parameter nicht angewandt); das PRD versprach Stress-/Risikoaussagen, die die Kombination nie zulassen konnte.
- (e) **Fehlerraten unter Unabhaengigkeit.** PRD 3.5 (DEC-52-Rate) und DEC-94 (6) / DEC-103 E3 (Produktregel)
  behandeln korrelierte Ereignisse als unabhaengig - einmal in Richtung Lockerung (Rate 0,5 % statt ~0,9..1,0 %),
  einmal in Richtung Strenge (Power unterschaetzt). Dasselbe Modellierungsdefizit, zwei Richtungen (K-4, K-5).
- (f) **UNBELEGT asymmetrisch.** Priors blockieren (Arbeitsregel 4), Strenge-Defaults (Gate-(4)-Faktor 0,95) werden
  verwendet (K-5 (c)); IC 0,03 [sek] akzeptiert, 12 bp [sek] verworfen (K-10 (4)).
- (g) **"Eine Datei, eine Wahrheit" (PRD 3.4) gilt nicht fuer die Verfassung selbst.** PRD-Altzeilen werden nicht
  umgeschrieben (DEC-94 "Nicht Teil"; DEC-103 E8), die bindende Fassung von 5.1-5.4, C.18, Fenstern, Placebos und
  Null steht in DEC-94/99/101/103 und deren Nachtraegen (~220 kB). Fuer einen autonomen Betrieb ist das ein Risiko.
- (h) **Fenster-Zeilen.** A1/A3 W1 2024-07-01..2025-06-30 (53 Wochen, DEC-74), A2 2024-09..2026-08 (reicht ins Siegel,
  BIL 2.4), W2-Ende 2026-06-28 (DEC-99 (8)), A4 "juengste Haelfte endet am Laufdatum", H-27 blind ab 2026-07; das PRD
  fuehrt weiter "je 52 Wochen".
- (i) **Design-Parameter ohne Pruefung.** "Design-Parameter (keine Schwelle)" (Listing 8 Wochen, Funding-AK 0,30,
  V-2 1 %, 97,5 %/24 Monate, 99 %) wirken als Kill-/Filterbedingungen; das Etikett ersetzt nicht die
  Erreichbarkeitspruefung (siehe (d)).
- (j) **Modellnamen.** PRD 3.9 und `scinance3-impl/CLAUDE.md` (Modell- und Teampolitik) nennen konkrete
  Modellbezeichnungen; UEBERGABE_2026-10-09 Abschnitt 1 verlangt "Keine Modellnamen in Repo-Artefakten" (oeffentliches
  Repo).
- (k) **Rechenkleinigkeiten.** Lo-Beispiel q = 12 statt 365 (K-2); K-0.6 Faktor 5,2 statt 4,7 (K-4); N = 5-Boden mit
  t = 2 (K-3).
- **Vorschlag [P].** Konsolidierte PRD-Fassung v3 (Nachtraege eingearbeitet, Altzeilen markiert, eine bindende
  Fassung je Kandidat), Rechenkorrekturen (a)-(c),(k) als Erratum; (d)/(i) Erreichbarkeitspruefung fuer jeden
  Design-Parameter gegen die REZENZ-Fenster (neutral, **O**); (j) Modellbezeichnungen durch Rollen ersetzen (**O**).

---

## 8. Rueckwirkung auf vergangene Entscheidungen (Auftrag 8; nur Richtung und Groessenordnung)

| Entscheidung | Betroffen durch | Was anders ausfiele | Groessenordnung |
|---|---|---|---|
| DEC-67 / DEC-73 E1 (B2 "Klasse W testbar") | K-3 | B1 fuer den Roh-IC | 4 Wochen Arbeit (DEC-73..92) vermieden, GL-032 frueher; Ergebnis gleich |
| GL-032 / DEC-92 (A3 Drittfassung) | K-3, K-5, K-6 | unter gepooltem alpha 0,01 und measured testbar (MDE 0,024), unter stress weiter GL (0,034) | haengt allein an "stress bindend" + Fehlerbudget (N) |
| GL-033 / DEC-93 (A1) | K-2, K-10 | GL bleibt, aber aus Struktur (MDE 129 >> SESOI 36 bp; SR_eff 1,95 < 2,49), nicht wegen theta | Ergebnis gleich, Begruendung definitiv |
| GL-034 / DEC-96 E2 / DEC-97 (H-27) | K-2, K-7, K-8, K-5 (d) | registrierbar mit L ~ 22 Monaten je Fenster und GSD | Urteil ~2030 statt nie; erwartete Dauer -12..-43 % |
| DEC-98 E1 (b), E4 (b) (Siegelumfang, Reihenfolge) | K-8 | gemeinsame Vorab-Registrierung, Siegel nur fuer registrierte Statistiken | juengste Daten fuer W/A1 nutzbar |
| DEC-99 (Pilot-Schaetzfenster, Zaehlregel) | K-9, K-12 | Assurance-Uebergabe (Schwelle am Testkriterium statt an MDE80); nicht uebergebene Varianten nicht im Nenner | Pilot-Uebergabe bei mu = c von 0,5 auf ~0,80 (SE_P ~ SD_T) bzw. ~0,93 (A2: SE_P 4,1 gegen 7,3) [R, Normalnaeherung] |
| GL-035 / DEC-101 (H-32) | K-9 | unveraendert (mom negativ, rev_gap t 1,53 zu schwach) | - |
| GL-036 / DEC-102 (H-33) | K-10 | unveraendert (MDE 0,040 > jede SESOI-/Literaturlesart) | - |
| DEC-103 (A2) | K-5, K-6, K-10, K-12, K-13 | registrierbar auf W1/W2 gegen Taker-SESOI 22 bp mit exakter Power oder gepooltem Test; Negativ-Panel aus `publicTrade` | Zuordnungs-MDE 32,1 -> ~19..24 bp; Pilotroute entbehrlich |
| DEC-73 E4 (Etikett `unter_wand`) | K-1 | Etikett bleibt, Abstand halbiert (0,03 gegen 0,040 statt 0,062) | - |
| KOMP E.1 / H-21 | K-13 | formal nicht entsperrbar [V] | - |

---

## 9. Was NICHT folgt

- **Kein Verdikt kippt und keines entsteht.** GL-032..GL-036 sind Feststellungen "nicht testbar"; A1, H-27 (auf
  12-Monats-Fenstern), H-33 und GL-035 bleiben unter jeder hier vorgeschlagenen Lesart. Nichts hier sagt, ein Effekt
  existiere.
- **Keine 2.0-Kante wird handelbar.** Die pi/2-Korrektur von K-0.1 aendert an Abstaenden von 80-500x nichts.
- **Keine rueckwirkende Regelaenderung.** Alle Vorschlaege sind prospektiv, programmweit und vor dem naechsten
  Kandidaten zu beschliessen; was eine Fehlerrate oder REZENZ beruehrt, ist Nutzerentscheidung mit Etikett.
- **C.2 bleibt fuer PASS-Bedingungen unangetastet.** Die SESOI wirkt nur auf Feasibility und Power-Zeile.
- **Keine Siegeloeffnung, keine Nutzung von W1/W2 fuer fm8-Statistiken.** Die C.17-Lage (GL-035/036, B-2-Kanal) bleibt;
  K-8 betrifft Siegel-UMFANG und kuenftige Registrierungsform, nicht bestehende Siegel.
- **Keine Empfehlung, alpha zu lockern.** K-5 (1) und K-3/K-14 sind Korrekturen ohne alpha-Wirkung; K-6 legt das
  Fehlerbudget als Nutzerfrage mit Zahlen vor.
- **Die [V]-Punkte sind Pruefauftraege, keine Befunde** (tardis-Inhalt, allLiquidation-Luecken, L2-Stresstage 2023-2025,
  Minutenbars aus `publicTrade`, Zahler-Verschiebung nach 2024).
- **GSD-, Assurance- und PPV-Zahlen sind generische Designeigenschaften**, keine Aussage ueber einen Kandidaten.

---

## 10. Reproduktion der Rechnungen

Skripte (ohne Marktdaten, deterministische Seeds), ausgefuehrt mit `python3 -I`:
- `state/prd_analyse_2026-11-01/scripts/kritik_calc.py`
  (K-0.1-Kurven Gauss vs. PRD, Lo q = 12/365, SR_eff, IC-Boden, C.10 vs. gepoolt, Produkt vs. exakte gemeinsame Power,
  A2-MDE-Kette, Pilot-Uebergabe-OC, PPV, GSD ohne Futility).
- `state/prd_analyse_2026-11-01/scripts/gsd_fut.py`
  (O'Brien-Fleming, 4 Blicke, mit/ohne Futility; 400.000 Pfade, Seed 53).
- `state/prd_analyse_2026-11-01/scripts/a2_pool.py`
  (A2 gepoolt, DEC-52-Gate Produkt vs. exakt, SR_eff je Fensterlaenge) und die DEC-52-Fehlerraten-Simulation (Abschnitt
  K-4, 4 Mio. Ziehungen, Seed 1).
Eingangszahlen ausschliesslich aus der Akte (Fundstellen je Befund).

---

## Kurzfassung an den Orchestrator (<= 12 Zeilen)

1. K-1: K-0.1 rechnet IC per arcsin in Trefferquoten, ignoriert aber die Gauss-Kopplung Treffer/Groesse - Kante x1,57 zu klein, Mindesthorizont x2,5 zu lang (IC 0,05: 1,1 statt 2,7 Tage; IC_min 0,040 statt 0,062). (O: Konstante; N: Mission)
2. K-2: Der Praemientest hat dieselbe Lo-Arithmetik wie Sharpe; Klasse P braucht SR_eff >= 2,49 je 12-Monats-Fenster (VRP 1,83, A1 1,95) - GL-033/034 waren am PRD-Tag vorhersagbar; Lo-Beispiel rechnet q = 12 statt 365.
3. K-3: Der WP-7-Rauschboden ist eine Identitaet (DEC-74) und enthaelt keine Breite; mit der Teststatistik-SD (0,09-0,13) waere B1 statt B2 gefolgt - DEC-73..92 vermeidbar.
4. K-5: Niemand kontrolliert die Gesamt-Power: A2-MDE 18,8 -> 32,1 bp (Daten x2,9) durch Produktregel, doppelt gezaehlte Null-Bedingung (Rechenartefakt, O streichen), Stress bindend, UNBELEGT-Default 0,95; alpha-Seite schon <= 0,25 % bzw. 5e-18.
5. K-6: Fehlerbudget invertiert (billiges PASS 20x streng, endgueltiges Nicht-Wissen akzeptiert); gepoolt alpha 0,01 machte A2 und A3-measured testbar. (N)
6. K-7: Power-/Prior-/L-Wahlen beruehren alpha nicht (Lauf-SE); sie als Torpfosten zu behandeln erzeugt Nutzerfragen ohne Validitaetsgewinn; H-27 waere mit L ~ 22 Monaten registrierbar. (N)
7. K-8/K-9: Siegel hortet verderbliche Daten fuer eine vor 2029 untestbare Hypothese; gemeinsame Vorab-Registrierung + GSD (E[N|H1] 0,82-0,88) loest die Reihenfolge-Frage; Pilot-Uebergabe U-4 hat P = 0,5 am Schwellenwert, A2 7e-5 bei 16,5 bp. (N)
8. K-10: Literatur-Prior-Pflicht schuetzt nur das Datenbudget; SESOI (A2 22 bp Taker) macht A2 heute registrierbar und schliesst A1/VRP strukturell; v2-Ausdehnung von C.2 auf Feasibility-Kills aufheben. (N)
9. K-11/K-12: Pivot-Diagnose falsch fuer H-03/H-09/H-24; Klasse P endet per Verfassung in PARK (L-12); REZENZ nur in Richtung Strenge (Stress 2021/22 bindet 2024-26). (N/O)
10. K-13: tardis 91 Monatsstichtage 2019-2026 [V: Inhalt pruefen], H-21 faktisch tot [V], OI-Probe still entfallen, Negativ-Panel aus publicTrade baubar [V]. (O)
11. K-14: Verfassung nur noch ueber ~220 kB DEC-Nachtraege lesbar - konsolidierte PRD v3 noetig; A4 "8 Quartale" vs "12+ Monate"; Modellnamen im Repo. (O)
12. Was nicht folgt: kein Verdikt kippt, keine Kante entsteht, nichts rueckwirkend, keine Siegeloeffnung; alle Fehlerraten-Fragen sind Nutzerentscheide.
