# Verifikation PRD_SCINANCE3_v2.md gegen die Orchestrator-Korrekturliste

**Pruefling:** `scratchpad/prd/PRD_SCINANCE3_v2.md` (1011 Zeilen, vollstaendig gelesen)
**Methode:** Zeile-fuer-Zeile-Abgleich jedes der 12 Korrekturpunkte gegen den Volltext.

---

## 1. rho_quer gestrichen; SD_null(IC_t) per 1000 Permutationen; z=2,4865/W=52 und z=3,1680/W=104; N_eff deskriptiv; Feasibility rein statistisch (IC_prior=0,03 [sek]); Wand nur Etikett; B1/B2 statistisch

**IMPLEMENTIERT.** Z. 276: rho_quer-Schaetzer "ERSATZLOS gestrichen" mit vollstaendiger algebraischer Begruendung (`sum_i e_{i,t}=0`, Aequikorrelation `-1/(K-1)`, Vol-Heterogenitaets-Artefakt +0,045). Z. 280-291: SD_null(IC_t) via 1000 Permutationen je Woche auf realem Panel, N_eff nur "deskriptiv zusaetzlich, ohne Urteilslast". Z. 293: "Die Feasibility-Frage ist ausschliesslich statistisch"; IC_prior=0,03 mit [sek]-Quelle (R2 0.3C, Primaerliteratur egress-gesperrt). Z. 295-305: Formeln exakt mit z=2,4865/W=52 und z=3,1680/W=104. Z. 331-332: B1 "Rein statistischer Ausloeser, keine Kostenzahl (C.2)"; B2 rein statistisch. Wand nur Etikett bestaetigt in Z. 28, 293.

Keine widerspruechliche Stelle gefunden.

## 2. Gepoolter Zweig durchgaengig z=3,1680; K_min 117; sigma_LS <= 116 bps/Woche

**IMPLEMENTIERT.** Z. 107 (DEC-51-Text), Z. 302-304 (WP-7), Z. 490 (A1), Z. 564-565 (A2) verwenden konsistent z=3,1680 im gepoolten Zweig. K_min=117 an Z. 316 und Z. 923 ("notwendig, nicht hinreichend"). sigma_LS <= 116 bps/Woche (DEC-52-Zweig) an Z. 506 und Z. 925.

**Beobachtung, nicht Widerspruch:** In 5.2 (Z. 572-576) wird die A2-Registrierungsschwelle je Fenster mit z=2,4865 gerechnet, obwohl Variante (b) laut Z. 563 im DEC-52-Zweig laeuft. Das ist methodisch konsistent, WEIL DEC-52(ii) einen Vorzeichen-/Magnituden-Screen JE FENSTER mit dem fensterlokalen z verlangt und die eigentliche Signifikanz separat "ausschliesslich auf dem GEPOOLTEN Schaetzer" (Z. 216, alpha=0,01) laeuft. Kein Fehler, aber die Trennung Screen-z (2,4865) vs. Pool-Signifikanz-z (3,1680) ist im A2-Abschnitt selbst nicht so explizit benannt wie in 5.1 (A1) - moegliche Praezisierung fuer v3.

## 3. C.2: A4-PASS = statistischer Rauschboden, w_min nur Etikett; WP-7-B-Befund zu sigma_xs nur Etikett unter_wand, keine Streichungsoption

**IMPLEMENTIERT.** A4-Gate-Text Z. 691-694: PASS ausschliesslich ueber `w >= 2,4865*sigma_w/sqrt(N_cluster)`, Bootstrap-CI, ex-ante Terminkurve; `w_min` ausdruecklich "Etikett und Bestandteil des getrennt zu registrierenden Tradability-Gates A4b" (Z. 680, 694). WP-7-Befund B4 (Z. 334): "Konsequenz ausschliesslich: alle Klasse-W-Kandidaten tragen das Etikett `unter_wand`. Keine Streichung, kein DROP, keine Aenderung einer PASS-Bedingung." A3-Feasibility-Liste bestaetigt explizit (Z. 643): "Nicht in dieser Liste: sigma_xs - Befund B4 erzeugt ausschliesslich ein Etikett (C.2)."

## 4. DEC-52-Anwendung: A3->C.10 hart (Power 0,72-0,78); A1-> EIN Design/Default hart, DEC-52 nur bei gemessener Power<0,6 VOR Registrierung, kein Doppel-Design; A2-> EINE Statistik (r_pre, 30 min), r_post nur Bericht; 36-bps-Kette ausgeschrieben, BTC-only; rho_BTC_ETH in WP-7 gemessen, bis dahin [sek] 0,8

**IMPLEMENTIERT, vollstaendig.**
- A3 (Z. 628): Power 0,72 (K=110) bis 0,78 (K=300) unter Review-Arbeitswerten, 0,75-0,98 unter neuem Rahmen; "Beide Rechenwege liegen ueber 0,60. DEC-52 (i) ist damit fuer A3 NICHT erfuellt: A3 laeuft unter C.10 hart."
- A1 (Z. 495-504): "EIN registriertes Design", C.10 als Default, Zuordnungsregel `P_fenster>=0,60 -> C.10 hart; <0,60 -> DEC-52`, ausgewertet nach WP-7 VOR Registrierung; Z. 504: "Es gibt kein zweites Design im Text und keine Wahl nach dem Lauf."
- A2 (Z. 536): "Genau EINE urteilstragende Statistik... r_pre... r_post... wird nur berichtet und traegt kein Urteil."
- 36-bps-Kette (Z. 538-543): "BTC-Tagesvol 2,5% -> Stunden-SD 51 bps -> 30-Minuten-SD 36 bps", explizit "Die 36 bps sind damit BTC-only."
- rho(BTC,ETH) (Z. 322, 545): in WP-7 gemessen; Arbeitswert 0,8 als [sek: Review R1-R4 2.3, dort selbst ungemessen] bis dahin.

## 5. A2-P1: beide Varianten mit eigener Effektherleitung/Placebosatz; 12 bps unbelegt fuer Wochenmenge; A2 verliert "laufbereit"; V-5 eingefuehrt; groesster Placebo-SE bindend

**IMPLEMENTIERT.** Tabelle Z. 551-567: Variante (a) wochentlich und (b) monatlich, je eigenes N_eff, SE, Placebosatz, belegte Effektgroesse. Z. 561: Variante (a) "belegte Effektgroesse fuer diese Menge: KEINE - UNBELEGT, Vorfrage V-5". Z. 567: "die in R3 registrierten 12 bps stammen aus dem monatsverfalls-basierten Aktien-Analogon... nicht zu R3s Ereignismenge" und "A2 verliert den in v1 behaupteten Status 'fruehester laufbereiter Kandidat'." V-5 als Zeile in Tabelle Z. 442 vollstaendig spezifiziert. Placebo mit groesstem SE bindend: Z. 549 und im Gate-Text Z. 584 Punkt (2).

## 6. WP-10(A) deskriptiv (kein rho_stress/rho_ruhig, kein PASS/FAIL), Spearman-SE 1,06/sqrt(n-3), Portfolio-Nulleffekt-Konstante; WP-10(B) adv_sel<=1,75 bp, keine p_fill-Schwelle, Fill-Kurve mit 10s/60s als Design-Parameter

**IMPLEMENTIERT.** Z. 396: "DESKRIPTIV, kein PASS/FAIL", rho_stress=0,70/rho_ruhig=0,45 "sind gestrichen, und mit ihnen die Befundzweige A-B1/A-B2". Z. 398: `SE(z)=1,06/sqrt(n-3)` (Bonett/Wright). Z. 402: Portfolio-Nulleffekt als "Schwellen-Basis eines spaeteren, getrennt zu registrierenden Portfolio-Gates". Teil B: Z. 410 "Die v1-Schwelle p_fill(60s)>=0,70 ist gestrichen"; Fill-Raten-KURVE gemessen, "10 s und 60 s sind DESIGN-PARAMETER (keine Schwellen)". Z. 415: `adv_sel_max = 3,5/2 = 1,75 bp je Bein`.

## 7. WP-9-Materialitaet 0,012 gestrichen; neue Herleitung aus H-26-Gate-Arithmetik (0,3 Vol-Pkt Verschiebung des 90-Tage-Mittels), Erreichbarkeitspruefung zuerst

**IMPLEMENTIERT.** Z. 364: "Die v1-Schranke 3/250=0,012 Vol-Punkte ist gestrichen." Z. 366-373: neue Herleitung ueber systematischen (`|b|>=0,30`) und zufaelligen Anteil (`s>=2,85=0,30*sqrt(90)`), beide an das 90-Tage-Mittel gekoppelt. Z. 375: "Erreichbarkeitspruefung ZUERST" ist explizit vorgeschaltet vor der Schranken-Anwendung.

## 8. DEC-Status: DEC-51/52 BESCHLOSSEN; DEC-53=Artefaktpflicht (Template-Feld `artifacts`, T7); Stress-Kanon=DEC-55/56; GPU-Default=DEC-57 BESCHLOSSEN; DEC-51 zweiseitig fuer Zensus + Richtungsfeld im YAML

**IMPLEMENTIERT.** DEC-51 BESCHLOSSEN Z. 100; DEC-52 BESCHLOSSEN Z. 213. DEC-53 BESCHLOSSEN Z. 138, YAML-Feld `artifacts` Z. 195-197, Teststufe T7 Z. 152. Stress-Kanon = DEC-55 (Z. 127) und DEC-56 (Z. 130), beide BESCHLOSSEN, nicht DEC-53. GPU-Default DEC-57 BESCHLOSSEN Z. 239. DEC-51 Punkt 1 zweiseitig fuer META/Zensus (WP-7/9/10) Z. 101; YAML-Feld `richtung` Z. 168 mit Verweis "DEC-51 Punkt 1: Teil der Registrierung"; `sided: <one|two>` Z. 177.

## 9. Gesetzte Skalare (sigma_xs 500, 3x, <0,30, 8 Wochen, "6 von 8", 99%) hergeleitet oder als Design-Parameter etikettiert; "6 von 8" aus A4 gestrichen

**IMPLEMENTIERT.** sigma_xs 500 ersetzt durch Formel `sigma_xs_min = 2*Kosten/(f*IC_prior)` (Z. 337-345). Faktor 3x (Alt-Spread) gestrichen (Z. 335: "war unhergeleitet und ist gestrichen"). Funding-Autokorrelation-Schwelle 0,30 als "Design-Parameter (keine Schwelle)" mit vorab fixierter Konsequenz (Z. 521). Listing-Ausschluss 8 Wochen als "Design-Parameter, keine Schwelle" mit Sensitivitaet bei 4/12 Wochen (Z. 347). "6 von 8" in A4 gestrichen (Z. 669: "Die v1-Regel 'Vorzeichenkonsistenz in >= 6 von 8 Zyklen' ist gestrichen"). 99-Perzentil (STRESS_ABS) als Design-Parameter (Z. 133). Sammelliste bestaetigend in Bel-5 (Z. 1009).

## 10. Evidenz: 36-bps-Kette vorhanden; "Deribit woechentliche Freitags-Verfaelle" [sek] mit V-5; Endpunktparameter [sek]; FRL-2026 mit R3-Vorbehalt; "11% Zerfall p.a." / "2025 negativer Carry" mit benannter Sekundaerquelle oder UNBELEGT

**GROESSTENTEILS IMPLEMENTIERT, EIN WORTLAUT-ABWEICHUNG.** 36-bps-Kette: siehe Punkt 4. Endpunktparameter als [sek] markiert: Bel-3 (Z. 1007, `instruments-info`-Cursorpaginierung, `delivery-price` "200/Seite, Cursor", Deribit-`resolution`). FRL-2026 mit R3-Vorbehalt woertlich uebernommen: Z. 534 "[sek; R3 vermerkt ausdruecklich: Autoren nicht ermittelbar, Volltext gesperrt - dieser Vorbehalt gehoert zum Zitat]". "11% Zerfall p.a." / "2025 negativer Carry": Z. 456 und Bel-2 (Z. 1006) als **UNBELEGT** gefuehrt, keine benannte Sekundaerquelle - erfuellt die Alternative "oder UNBELEGT".

**Abweichung:** Die Korrekturliste verlangt "Deribit weekly Friday expiries marked [sek]". Das PRD markiert die Behauptung stattdessen als **UNBELEGT** (V-5(a), Z. 442; Bel-1, Z. 1005: "'Deribit fuehrt woechentliche Freitags-Verfaelle' ist als UNBELEGT gefuehrt"), nicht als `[sek]`. Das ist laut der PRD-eigenen Belegregel (Z. 9: "ein [sek] ohne benennbare Quelle wird als UNBELEGT gefuehrt") korrekt, weil keine benennbare Sekundaerquelle vorliegt - mithin *inhaltlich* strenger als gefordert, aber *woertlich* nicht die verlangte `[sek]`-Etikettierung. Keine Bedeutungsluecke, nur ein Etikettwechsel; als Praezisierungshinweis vermerkt, nicht als Fehler gewertet.

## 11. Arithmetik: 5 req/s = 4,2% des Limits; 9.300 Calls ~31 min; r_USD=0 als Annahme mit 8.2 verknuepft

**IMPLEMENTIERT.** Z. 771: "Die Selbst-Drossel von 5 Req/s ist damit 4,2% des Limits (nicht 0,4%)". Z. 776/939: "~9.300... 31 min" (v1-Fehler "~15 min" korrigiert und benannt, Z. 776). r_USD=0: Z. 462 "einer Annahme, die R1 als konservativ setzt und die dieselbe oekonomische Groesse betrifft wie r_opp in Par. 8.2, weshalb sie hier ausdruecklich als Annahme etikettiert und mit 8.2 verlinkt wird"; Ruecklink in 8.2 (Z. 836) mit identischem Wortlaut.

## 12. Abschnitt 10 Aenderungsprotokoll mit Review-Referenz je Zeile; Abschnitte 6-9 vorhanden; Nutzer-Entscheidungen in 8 als offen markiert mit Orchestrator-Default (b), nicht durch das PRD beantwortet

**IMPLEMENTIERT.** Abschnitt 10 (Z. 956-1010) mit drei Unterabschnitten (Blocker B-1..B-8, Wichtig W-1..W-16, Kosmetik/Belege K-1..K-8/Bel-1..Bel-5), jede Zeile mit Review- oder Orchestrator-Referenz in der letzten Spalte. Abschnitte 6 (Z. 736), 7 (Z. 765), 8 (Z. 814), 9 (Z. 848) vollstaendig vorhanden. Abschnitt 8 traegt den Titel "Offene Nutzer-Entscheidungen" (Z. 814) und Z. 816: "Diese drei Punkte kann nur der Nutzer entscheiden." 8.1 fuehrt explizit Optionen (a)/(b)-DEFAULT/(c) auf (Z. 822-826) und wendet (b) als Arbeitsdefault an (Z. 828: "Umsetzung unter Default (b), verbindlich"), ohne dass eine Nutzerantwort im Dokument behauptet wird - der Default blockiert nichts und ersetzt keine Entscheidung. 8.2/8.3 ebenso ausdruecklich unbeantwortet mit "keine Blockade"-Vermerk (Z. 838, 844).

---

## Neue Zahlen ohne Herleitung/Quelle (Pruefauftrag zusaetzlich)

Keine unbelegte, folgenlose Neuzahl gefunden. Alle in v2 neu auftauchenden Skalare tragen entweder eine Formel-Herleitung (sigma_xs_min, WP-9-Materialitaet, A2-Schwellen, DEC-51-z-Werte), eine Quellenmarkierung `[sek]` (rho(BTC,ETH)=0,8; 11%-Zerfall/2025-Carry als UNBELEGT; FRL-2026; Endpunktparameter), oder das Etikett "Design-Parameter (keine Schwelle)" mit vorab fixierter Konsequenz (Autokorrelation 0,30; Listing 8 Wochen; V-2-Liquiditaetsmarke 1%; Fill-Stuetzstellen 10s/60s; DEC-55/56-Parameter). Einzige Grenzstelle: `K_min=117` (Z. 316) ist explizit als "vom Orchestrator... fixiert" und "notwendig, nicht hinreichend" gekennzeichnet, mit Bracket-Logik (134 fuer Per-Fenster, 109 fuer gepoolt) transparent gemacht - kein freischwebender Skalar, aber die Herleitung des exakten Werts 117 selbst (statt z.B. 120 oder 125) liegt ausserhalb dieses Dokuments (Orchestrator-Entscheidung B-4) und wird hier nur zitiert, nicht neu gerechnet. Kein Fehler, aber die einzige Stelle, an der "Herleitung" durch "Zitat einer externen Entscheidung" ersetzt ist.

## Oekonomische Groesse innerhalb einer PASS-Bedingung (Pruefauftrag zusaetzlich)

Keine gefunden. Alle vier Gate-Texte (A1 Z. 512-515, A2 Z. 582-585, A3 Z. 634-637, A4 Z. 691-694) pruefen ausschliesslich statistische Rauschboeden, Selektions-Decken, Placebo-/Permutations-Verteilungen und Artefaktpflichten; jede Kostenzahl (36 bps/Woche, w_min, 15-bps-Wand, IC_min=0,062/0,102) ist explizit als "Etikett, nicht Gate" oder "Entscheidungsrelevanz-Zeile" ausgelagert (z.B. Z. 506, 517, 639, 680, 696). V-2s "1% Umsatz"-Marke fuehrt zu Recording-First statt DROP und ist ausdruecklich aus der A4-Kill-Liste ausgenommen (Z. 700, C.2-Zitat). Die C.2-Verschaerfung aus Z. 86 (auch Befundzweige und Feasibility-Kill-Bedingungen betreffend) ist damit durchgaengig eingehalten.

---

## Gesamtbefund

Alle 12 Korrekturpunkte sind **implementiert**. Keine Streichung, kein Rueckfall auf gesetzte Skalare, keine Kostenzahl in einer PASS-Bedingung gefunden. Zwei Stellen sind vermerkenswert, aber nicht als Verstoss zu werten: (a) Punkt 10 - "Deribit-Freitagsverfaelle" ist UNBELEGT statt `[sek]` markiert, was der PRD-eigenen, strengeren Belegregel entspricht; (b) `K_min=117` zitiert eine externe Orchestrator-Fixierung, statt sie im Dokument selbst neu herzuleiten.
