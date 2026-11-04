# Auftrag: Herleitung "Kapitalregel Klasse P ohne MinTRL" (DEC-107 (5), P-10) - 2026-11-04

Rolle: Herleitung (eigener Code fuer Formeln/Simulation, keine Marktdaten, keine Siegeldatei, nichts im Repo aendern, nichts
committen). Ausgabe nach `<herleitung_kapitalregel_p>/`:
HERLEITUNG_KAPITALREGEL_P.md, calc/kapital_sim.py, kapital_results.json, kapital_sim.out. ASCII, Deutsch (Code Englisch),
Rollen statt Modellnamen (Orchestrator, Herleitung, Review, Bau, Kartierung), keine Hostnamen.

## Anlass
Nutzer 2026-11-04 (DEC-107 (5) in `/home/user/scinance/scinance3-impl/state/decisions.md`): "Klasse P bekommt eine Kapitalregel."
Bisher: PRD 3.6 Auflagen (1) "Praemien-EXISTENZ; risikoadjustierte Frage untestbar (MinTRL > Historie), PARK nicht WEITER" und
(2) "kein Kapitalschritt folgt aus einem P-A-PASS" (PRD v3 VR-f13); Kritik K-12 (`state/prd_analyse_2026-11-01/KRITIK_PRD.md`):
Klasse P endet per Verfassung in PARK, L-12 verletzt. Sharpe wird berichtet, nie geurteilt (Lo 2002: T_min ~ 6,2/SR^2 Jahre).

## Zu leisten
1. **Was ein P-A-PASS freigibt.** Ein PASS der Klasse P ist ein Mess-PASS (Praemie mean(prem) > 0 bei alpha 0,0025 gepoolt +
   Stabilitaetstest, DEC-107 (1); Schaetzer, CI95, Ausschlussgrenze Pflicht). Herleiten, welcher Kapitalschritt daraus logisch
   folgen kann, ohne Sharpe/MinTRL als Urteil: Kapitalregel als Funktion von (a) Praemien-Schaetzer und CI-Untergrenze, (b)
   Ruin-Kapital u(eps) = (sigma^2 / 2 mu) ln(1/eps) (VR-f13 zweite Berichtszeile) mit mu = CI-Untergrenze statt Punktschaetzer,
   (c) Stress-Episoden-N als Risikomass (PRD 3.6 Auflage (4)), (d) MaxDD-Boden E[MaxDD] = 1,2533 sigma_ann sqrt(T).
   Kelly-Bruchteil-Formen (f = mu/sigma^2 mit CI-Untergrenze; Bruchteil 1/4..1/2) herleiten und gegen Ruin-Kapital stellen.
2. **Getrenntes Tradability-Gate (C.2).** Der Kapitalschritt ist NIE Teil des Mess-PASS. Vorschlag fuer ein getrennt
   registriertes Tradability-Gate der Klasse P: Kostenmodell `constants_hash` (VR-g14), Fill-Annahmen (Funding-Praemien sind
   Maker-/Halte-Positionen), Stress-Abdeckung (STRESS_ABS, VR-g13), Steuer/Kapital UNBELEGT-Zeile (PRD 8.2). Ausfuehrungsspur
   nach PRD 8.1 Default (b): leer bis Mess-PASS, Tradability-PASS und ausdrueckliche Freigabe des Nutzers; **kein Live-Order-Code,
   kein Live-Kapital** (Nutzer 2026-11-04).
3. **Rauschboden der Kapitalregel.** Welche Kapitalgroesse ist bei den Nuisance-Zahlen der Akte ueberhaupt belegbar? Beispiel A1
   (Funding-Praemie, GL-033 strukturell geschlossen: `state/gate_log.md`, DEC-93) und H-27/VRP (GL-034, DEC-97) als Zahlenbeispiele
   fuer "was waere die Kapitalregel gewesen" - nur mit den in der Akte offenen Zahlen (SE, Fensterlaengen), keine Siegeldatei.
   Simulation: Verteilung der Kapitalempfehlung bei wahrer Praemie = SESOI gegen Null; P(Kapital > 0 | Null) muss <= alpha sein.
4. **Verhaeltnis zu L-12 und zur Mission.** Zeigen, dass mit der Kapitalregel ein P-PASS "etwas entscheidet" (L-12 erfuellt),
   ohne dass eine oekonomische Groesse in die PASS-Bedingung wandert (C.2, VR-a02; DEC-107 BE-03).
5. **Etikett und Strenge-Quotient.** Lockerung gegenueber PRD 3.6 (2) (Kapitalschritt moeglich); Verschaerfung (zusaetzliches
   Gate); Entscheider N; Geltung ab Kohorte 1; Rueckbauweg.
6. **Registrierungstext.** Vorschlag fuer VR-f13 neu (Wortlaut), neue Pflichtzeile(n) im YAML 3.1 (`capital_rule`: formel,
   eps, bruchteil, ci_basis, stress_n_min, tradability_gate_ref) und DEC-Nachtrags-Wortlaut.
7. **Was nicht folgt** und Kurzfassung <= 12 Zeilen.

Quellen (nur lesen): `scinance3-impl/PRD_SCINANCE3_v3.md` (VR-f13, VR-a02, VR-g08, VR-g13, VR-g14, 5.2 P-10, WD-12),
`scinance3-impl/PRD_SCINANCE3.md` 3.6 und 8.1/8.2, `state/decisions.md` DEC-58 E1 (e), DEC-93, DEC-97, DEC-104 E1/E3/E8,
DEC-107, `state/prd_analyse_2026-11-01/KRITIK_PRD.md` K-12, `survey/ERKENNTNIS_KOMPENDIUM.md` C.2, L-12 im PRD v2 Par. 2.
Nicht oeffnen: `state/runs/*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`.
