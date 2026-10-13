# Gate-Log Scinance 3.0 (append-only)

> Fortsetzung von `scinance2-impl/state/gate_log.md` (GL-001..GL-031).
> Neue Eintraege ab GL-032. Kein Lauf ohne registrierten Eintrag, kein
> Urteil ausser gegen das registrierte Gate.

_(noch keine Eintraege)_

## GL-032 - 2026-10-12 - H-28/H-29/H-30 Drittfassung (F-XSEC1, A3, YAML bd948f34...c299) - GL-012 vor dem Lauf, kein Lauf
- Anlass: Positivkontrolle NICHT BESTANDEN (rc 3, `state/runs/wp13_positivkontrolle_20261012`, result_sha256 b3daeea8...041d):
  mom1 PASS 1/3 Seeds, rev_gap 3/3, Negativkontrolle 0/3. Gate-Kette ohne Defekt (Injektion pos-neg +0,051..0,056).
- Ursache (outcome-frei, v5e): DEC-88 rechnete die Roh-IC-Bedingungen mit Boden-SE IC_min/2,4865; registriert ist
  SE = max(Boden, SD(IC_t))/sqrt(W) (DEC-75 (1)). SD(IC_t) der Roh-Null (methods.none factor_sd) W1 0,090/0,130,
  W2 0,061/0,082 (measured/stress) gegen Boden 0,049/0,042.
- Korrigiert, Prior 0,03, W1 measured/stress: mom1 P 0,47/0,21 (MDE80 0,042/0,060), rev_gap 0,48/0,21 (0,041/0,059);
  W2 0,85/0,55 (0,028/0,038). IC_min-Bedingung ebenso betroffen (W1 mom1 0,79/0,71). Bindend stress; gleiches Ergebnis.
- Zuordnung DEC-87 (F)/DEC-51 (2), mechanisch: MDE80 > 0,03 in W1 -> GL-012 fuer mom1 und rev_gap; mom2, mom4 (verschaerft),
  H-30 (Feasibility 2,764; vol_beta strukturell) unveraendert. Alle 7 Varianten GL-012 vor dem Lauf.
- DEC-52 anwendbar, nach DEC-87 (F) nicht genutzt; keine Viertfassung (gepoolt unter stress MDE80 0,034 > 0,03).
- Feststellung: Drittfassung F-XSEC1 im registrierten Design (Roh-IC je Fenster, C.10 hart, W1/W2, Union-Panel) bei
  IC_prior 0,03 nicht testbar. KEIN Verdikt ueber Momentum, Reversal, Vol-Anomalie; DROP-Relevanzzeile greift nicht.
- K = 7 bleibt (p = 1, BH/F-WEEK). YAML bitgleich, --run entfaellt; kein PC-Neulauf, keine Teilkohorte, kein Prior-Wechsel.
  L-Siegel und alle Siegeldateien bleiben geschlossen. Anderes Design nur als neue Hypothese mit eigenem K (DEC-58 E2).
- Akte: DEC-91, DEC-92; Audit `state/REVIEW_GATE_AUDIT_PC_v3_2026-10-12.md`; Gate-Auditor: BESTAETIGT.

## GL-033 - 2026-10-13 - A1 (H-31, Funding-Long-Bein D1 gegen Universums-Hedge, DEC-70) - GL-012 vor der Registrierung, nicht registriert
- Anlass: Feasibility vor dem Design (C.12), `state/herleitung_a1/` (FEASIBILITY sha `b4680f7c...ca72d9e`), ergebnisblind
  (keine A1-Outcome-Groesse ab 2024-07-01). Formationsseitig W1/W2: K 343..511 / 512..600 (Kill (3) nein), Schluessel-
  Autokorrelation 0,403 / 0,303 (Kill (4) formal nein, W2 an der Grenze), D1 nicht degeneriert (0,52 / 0,71), Spread
  175,8 / 339,6 bp/Woche. Nuisance 2022-04..2024-06 (nur Streuung): SD 354 bp, rho_1 -0,25, phi 0,573.
- Prior: prem = Spread x phi x theta; theta (nicht kompensierter Anteil) UNBELEGT. Bei theta = 1: prem W1/W2 100,7 / 194,5,
  gepoolt 147,6 bp.
- Zuordnung nach geltender Regel (DEC-67 E4, fuer A1 bestaetigt DEC-70 E1: W_eff = 0,41 W): 3,168 x SE_gepoolt = 176,5 bp
  > 147,6 bp -> GL-012 schon bei theta = 1 (theta_min 1,196). Guenstigste Lesart (c = max(1, gemessen)) braucht theta
  >= 0,766, ohne Quelle -> blockiert; W1 Power 0,80 bei keinem theta <= 1.
- Review `state/herleitung_a1/REVIEW_A1.md`: VETO gegen "knapp testbar", Zahlen bestaetigt; Orchestrator-Nachrechnung mit
  eigenem Code bestaetigt (Spread 174,0 / 336,3; SD 354,4; phi 0,568). Keine A1-spezifische Regelaenderung (DEC-93 E3).
- Feststellung: A1 in der Konstruktion DEC-70 unter den geltenden Beschluessen nicht testbar; nicht registriert. KEIN
  Verdikt ueber den Funding-Carry; DROP-Relevanzzeile greift nicht. Stufe 2 Akte ohne Rechtswirkung. Siegel unberuehrt.
- Akte: DEC-93; Reviewer: VETO (gegen Testbarkeit) angenommen.
