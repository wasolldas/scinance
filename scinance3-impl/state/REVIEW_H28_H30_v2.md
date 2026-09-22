# Adversarischer Review H-28/H-29/H-30 Zweitfassung (Opus, 2026-09-22) - Kurzfassung

Vollstaendiger Review im Sitzungsprotokoll; bindende Punkte in DEC-75. Verdikt: nicht bauen; Drittfassung noetig.

**BLOCKER (vom Orchestrator uebernommen):**
- B-1 Permutationsboden E_t[1/sqrt(K_t-1)] ist die SD unter Austauschbarkeit der Charakteristik; bei heterogenem Beta (0,5..2,0) auf signalfreiem Panel SD(IC_t) = 0,0811 gegen Boden 0,0448 (Faktor 1,81). Reale Groesse je Fenster damit 0,08 statt 0,0064; Decke auf faktorerhaltender Null 0,0145/0,0166 >= IC_min. Korrektur: SE = max(Boden, SD(IC_t))/sqrt(W), Wochen-Block-Bootstrap bindend.
- B-2 c_rho < 1 ist Schaetzerbias (-1/W je Lag); Deckelung max(1, c_rho) notwendig, aber nicht in DEC-74 (b)/Code/Artefakt; mom1 bias-korrigiert 0,01936/0,01724.
- B-3 Gate (2) Persistenz-Null bindet in keiner der 14 Zellen -> report-only.
- B-4 Registry-IC_min (gedeckelt) != Artefakt (ungedeckelt) in 12/14 Zellen.
- B-5 H-30: target_vol^2/2 ist rangneutral (misst nichts); sigma_w^2/2 vom gewichteten Return erzeugt das registrierte Vorzeichen mechanisch; Schaetzfehler ~60 % auf sigma_w^2/2 unquantifiziert.
- B-6 H-30: Vol-Gewicht muss vol_rv[t] (PIT) sein, Helfer nutzt Zeilenindex des Outcomes.
- B-7 PRD-Kills (3) Survivorship >= halbe Schwelle und (4) Bounce-Abzug entfallen -> Lockerung, zurueck.
- B-8 PRD-Survivorship-Fixture (30 %, Drawdown-Trigger, unkontrolliert vs. kontrolliert) fehlt; Konventionsdifferenz gemessen -0,00035 (unkritisch).
- B-9 Querschnitts-Demeaning ist fuer Spearman ein No-op; Markt-Autokorrelation 0,10 liefert 38 % von IC_min ohne Prognostizierbarkeit -> markt-residualisierter Outcome als zusaetzliche PASS-Bedingung, adversariales Fixture mit driftendem, autokorreliertem Markt.

**WICHTIG:** W-10 W = geurteilte Wochen 52/51, Decke auf n_weeks-1; W-11 Decke W2 analytisch 0,00806; W-12 Kill-Regel Decke: Schaetzer/Replikate/Fixture benennen; W-13 BH kann nach Gate (1) nie verwerfen -> report-only oder Block-p; W-14 IC_prior 0,03 fuer rev_gap (Lag-2-Wochen) unbelegt, DEC-52-Zuordnung offen etikettieren; W-15 AR(1)-Null-Lage = E[phi_hat] (Kendall-Bias), Bias-Korrektur; W-16 H-30-Persistenz-Null ist weisses Rauschen; W-17 Randkonstruktion der Charakteristik pinnen; W-18 Test-IDs fuer Boden/Quantil/Decke, volle Hashes, Siegel praezisieren (Feasibility-Zahlen ins offene Artefakt); W-19 Gate-Text (1)-(7) vollstaendig; W-20 T3/T4/T6; W-21 Abweichungsliste.

**KOSMETIK:** Symbol-Wochen 22.815/29.732; Null-Mittel -0,0036..-0,0469; Power unter c_rho 1,13 = 0,98; degenerierte Querschnitte -> IC 0,0 (dokumentieren); sigma=0-Symbole in der AR(1)-Null (7/10).

**Bestaetigt:** Fenster 53/52 lueckenlos, 11 ungeurteilte Wochen; K-Reihen; Boden; Delisting 80/140; NO_HISTORY; Gate (5) 0,159/0,142; Stress 22/8, 2/1; oekonomisches Etikett 0,0101; Seed; close_at_last; K=7; Familien.
