# Auftrag: Herleitung des registrierten Stabilitaetstests (P-2 Variante (c), DEC-104 Nachtrag 2 (4)) - 2026-11-02

Rolle: Herleitung mit eigenem Code (Formeln, Simulation; keine Marktdaten). Nichts im Repo aendern, nichts committen, keine
Siegeldatei. Ausgabe nach `<scratchpad>/stab/`
(HERLEITUNG_STABILITAETSTEST.md, calc/stab_sim.py, stab_results.json, stab_sim.out). ASCII, Deutsch, Rollen statt Modellnamen.

## Anlass

Die OC des Pakets 3.1 (`scinance3-impl/state/prd_analyse_2026-11-01/OC_VERFASSUNG31_2026-11-02.md`, Abschnitt (a) Nr. 6 und (g);
DEC-104 N2 (3)-(4) in `scinance3-impl/state/decisions.md`) zeigt: der REZENZ-Screen auf dem juengsten 12-Monats-Fenster bei
alpha 0,05 erzwingt den Boden MDE >= 2,4865 SE_12. Variante (c) ersetzt den Screen durch einen **registrierten Stabilitaetstest**
"der juengste Teil faellt nicht ab" (gepoolt 0,0025 + unabhaengiger Test, Power 0,95 -> Pool-Power 0,8/0,95, kein Boden,
+9 % Daten). Der Nutzer entscheidet; die Regel muss vorher fertig hergeleitet sein.

## Zu leisten

1. **Definition.** Statistik des Stabilitaetstests fuer eine Registrierung mit Konfirmationsdaten aus Zone V (ein Blick) und/oder
   Zone K (bis zu vier Quartalsblicke): Teststatistik D = (Mittel juengster Teil - Mittel aelterer Teil) / SE(D) mit juengstem
   Teil = letzte 12 Monate bzw. letzte vier Quartale; Nullhypothese und Richtung so, dass "Effekt nur im aelteren Teil" verworfen
   wird; einseitige Fehlerrate 0,05; Beziehung zur gepoolten Statistik (Unabhaengigkeit von Differenz und Summe bei gleichen
   Varianzen: zeigen und den Fall ungleicher Varianzen/Anteile r behandeln). Alternative Formulierung als Nicht-Unterlegenheits-
   Test (TOST-artig: "juengster Effekt >= f x gepoolter Effekt" mit f = 0,5) - Vor- und Nachteile.
2. **Entscheidungsregel.** PASS = gepoolt Z > 2,807 und Stabilitaetstest nicht verworfen; Power-Planung: gemeinsame Power 0,80
   an der SESOI (Pool-Power 0,80/P(Stabilitaet haelt | H1 homogen)); P(Stabilitaet haelt | homogen) als Funktion von r und
   Blickzahl berechnen (nicht pauschal 0,95 setzen) und die Datenfaktoren gegen gepoolt ohne Screen und gegen C.10 je 0,80
   ausweisen (OC-Zahlen 1,0905 / 1,1741 bei r 1/2 reproduzieren oder korrigieren).
3. **Schutzwirkung.** P(PASS) wenn der Effekt nur im aelteren Teil liegt (f x MDE, f 0,5/1/1,5/2), wenn er abklingt (juengster
   Teil halber Effekt), und wenn er nur im juengsten Teil liegt; Vergleich mit Screen 0,05 und 0,20 (OC (a) Nr. 4 und 6).
4. **Gruppensequentiell.** Wie der Stabilitaetstest an den Quartalsblicken (OBF, 4 Blicke, alpha 0,0025) gefuehrt wird: nur
   am letzten Blick oder an jedem Stopp; alpha_eff und E[N bei H1] je Variante (Monte Carlo >= 200.000 Pfade, feste Seeds).
5. **Nuisance und schwere Raender.** t-artige Grenzen bei 40..52 Clustern (DEC-104 N2 (7)); Blocklaenge; Wirkung der Kurtosis
   5..10 auf alpha und Power des Stabilitaetstests (Simulation).
6. **A2 und Klasse W als Beispiele.** Mit den Akten-Zahlen (A2: SE P2'' 7,34/7,58, Stress 8,52, Gate-(4)-Faktor 0,9025, exakte
   Konjunktion; Klasse W: Wochen-IC-SD 0,09/0,13, SESOI 0,040 bzw. Dezil-Rahmen 0,0085) die MDE80 und den fruehesten
   Konfirmationszeitpunkt unter (c) gegen (a) ausweisen (Zone K fuer BTC/ETH ab 2026-10-01, FENSTERREGISTER Abschnitt 6).
7. **Registrierungstext.** Vorschlag fuer die Pflichtzeilen `screen`/`stability_test` (PRD v3 Entwurf PZ, YAML-Template 3.1
   in `scinance3-impl/PRD_SCINANCE3_v3_ENTWURF.md` Abschnitt 3.3) und fuer den Wortlaut eines DEC-104 Nachtrags, Etikett
   (Lockerung gegenueber (a): kein Boden; Verschaerfung: zusaetzlicher Test; alpha je Test unveraendert), Entscheider N.
8. **Was nicht folgt** und Kurzfassung <= 12 Zeilen.

Quellen: OC-Bericht und `scripts/oc_sim.py`, `orch_oc_check.py`; DEC-51/52/94/99/104 (+N1-N3)/105; `src/bybit_edge/research/
feasibility31/rules.py` (R4/R5-Implementierung lesen, nicht aendern); DEC-99 (1) REZENZ-Wortlaut.
