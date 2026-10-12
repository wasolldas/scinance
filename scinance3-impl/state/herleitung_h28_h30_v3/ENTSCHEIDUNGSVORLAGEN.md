# Entscheidungsvorlagen zur Drittfassung H-28/H-29/H-30 (Kohorte F-XSEC1, A3)

> ENTWURF der Herleitung, 2026-10-12. Nichts hier ist registriert oder beschlossen; entscheiden und registrieren
> darf nur der Orchestrator. Keine reale Charakteristik-gegen-Folgerendite-Rechnung, keine Siegeldatei geoeffnet.
>
> Fundstellen-Kuerzel:
> - `[v5d]` = `scinance3-impl/state/runs/wp13a_20261012_v5d/wp13a_prelaunch.json`
>   (sha256 `b0cb4629f6ce8639e3de34689a6f00fe63bc93dc957a97163f8839e1ef5948d9`), mit JSON-Pfad;
> - `[v5d-md]` = `wp13a_prelaunch.md` desselben Ordners (sha256 `1488b31781f0b89a699ea606aa655cbb185b75d5283f1c0e844ffec3a4b31cd1`);
> - `[abg.]` = in dieser Herleitung aus offenen Artefaktzahlen abgeleitet, Rechenweg steht daneben;
> - UNBELEGT = keine Fundstelle, blockiert die abhaengige Groesse.
>
> Teil 1 behandelt die drei offenen Punkte aus DEC-86 (a)-(c). Teil 2 enthaelt sieben weitere Punkte, die bei der
> Herleitung aufgefallen sind. Ohne Entscheidung zu ihnen ist die Drittfassung nicht lauffaehig.

---

## Teil 1 - Die drei offenen Punkte aus DEC-86

### A. Welche Selektionsdecke bindet GL-012?

**Frage.** Der v5d-Bericht fuehrt die Zeile "GL-012-bindende Decke (driftfree, residualisiert)" mit 0,04963 (W1)
und 0,04993 (W2) [v5d-md; v5d `windows.<W>.factor_preserving_null.driftfree.selection_ceiling_mean_of_max_residualized`].
DEC-86 nennt als Decke der registrierten Methode unter der kalibrierten Null 0,0074 (W1) und 0,0064 (W2).
Welche Zahl entscheidet ueber den Vor-Verdikt-Kill "Decke >= IC_min -> GL-012" (DEC-75 (2))?

**Fundstellen.**
- DEC-75 (2): Decke auf faktorerhaltender Null, Schaetzer "Mittel des Maximums ueber 7 Varianten", >= 1.000
  Replikate, Seed 53; Kill: Decke >= IC_min -> GL-012 vor dem Verdikt.
- DEC-76 E1 (c): Null OHNE Drift; residualisiert und roh getrennt berichten; "die Kill-Regel bindet an die
  residualisierte Decke". "Residualisiert" hiess damals "mit der Beta-Kontrolle". Die einzige Beta-Kontrolle war
  zu diesem Zeitpunkt die Zeitreihen-Residualisierung mit dem 8-Wochen-PIT-Beta.
- DEC-77 (Anlass/E1): Mit der 8-Wochen-TS-Residualisierung ergibt sich eine residualisierte Decke von 0,058/0,055 > IC_min.
  Ursache ist der Errors-in-Variables-Effekt der Beta-Schaetzung, also eine Eigenschaft der Methode. Die Methode
  muss deshalb vorab kalibriert gewaehlt werden. E1 (b) verlangt ihre Decke <= 1,5 x Rausch-Decke unter
  kalibrierter UND Stress-Null. E2: Der Lauf uebernimmt "die gewaehlte Methode".
- DEC-78 E1/E2: rho_f wurde mit 0,046 gemessen. Die Stress-Null rho 0,2 ist damit widerlegt; neu gilt
  stress = 2x rho_f UND 2x Faktoranteil. Die TS-Residualisierung ist "belegt unbrauchbar" und faellt aus dem Raster.
- DEC-85 (iv)/(v): Regel, Stress und Raster bleiben unveraendert. Das v5d-Ergebnis bindet in beide Richtungen;
  besteht eine Methode, ist sie die Grundlage der Drittfassung.
- DEC-86: Registriert wird `fm_neutral_8w` (Beta-Fenster 8) mit den v5d-Kalibrierungen "je Fenster und Kalibrierung".
- Code: `run.run_full` rechnet je Fenster `nulls.beta_controlled_factor_null` neu, und zwar mit der registrierten
  Methode, driftfrei und unter der stress-Kalibrierung. Die Gate-Arithmetik vergleicht dann den eingefrorenen Wert
  mit IC_min (`gates.evaluate`).

**Herleitung.**
1. Die v3-Zeile (0,0496/0,0499) ist die Decke einer anderen Statistik. Gemessen wird dort der Mittel-IC
   gegen den TS-8w-residualisierten Outcome, mit rho_f 0,2 und Beta ~ U(0,5; 2,0)
   [v5d `factor_preserving_null.driftfree.rho_f` = 0,2; Label "rho_f=0.2, drift_f=0.0"]. Geurteilt wird aber der
   Mittel-IC gegen den fm_neutral_8w-neutralisierten Outcome. GL-012 soll den Selektionseffekt der GEURTEILTEN
   Statistik begrenzen. Die Decke einer nicht registrierten Methode begrenzt ihn nicht.
2. Die Null der v3-Zeile ist durch Messung widerlegt (DEC-78: rho_f 0,046 statt 0,2). Ihr hoher Wert ist zudem ein
   Methodenartefakt der TS-Residualisierung (DEC-77). Sie wuerde jede Variante vor dem Verdikt toeten: 0,0496 liegt
   ueber jedem IC_min (0,0146..0,0197). Fuer 0,0499 gilt dasselbe.
   Die Folge waere "Klasse W nicht testbar", obwohl v5d eine Methode bestaetigt hat. Das widerspraeche DEC-85 (v)
   und DEC-86 und waere ein Torpfosten-Verschieben in die strenge Richtung, das die Verfassung ebenso ausschliesst
   ("in KEINE Richtung").
3. Laufpraktisch scheitert die v3-Zeile ohnehin. `run.run_full` prueft die eingefrorene Decke gegen die eigene
   Nachrechnung mit der registrierten Methode (+-10 %, `assert_null_calibration`). Die Abweichung waere -84 %
   (W1) bzw. -86 % (W2), Folge ist `NullCalibrationError`, also KEIN Verdikt fuer keine Hypothese
   [abg.: statische Pruefung `work/validate_template.txt`].
4. Unter den vertretbaren Lesarten ist diese die strengste: Die Decke muss unter BEIDEN registrierten Kalibrierungen halten
   (DEC-77 E1 (b): "bei kalibriertem UND Stress-rho"). Bindend ist deshalb die groessere, also die stress-Decke.
   Das ist zugleich die Konfiguration, die der Lauf-Code nachrechnet. Die zero-Kalibrierung liegt darunter
   (W1 0,00723, W2 0,00599 [v5d `beta_control_method_study.calibrations.zero.methods.fm_neutral_8w.ceiling_mean_of_max`]).
5. **Korrektur zu DEC-86.** Die dort zitierten W1-Werte 0,0074/0,0079 und die W1-Null-Mittel 0,00058/0,00124
   stammen aus `beta_control_recommended_high_rep` von W1. Dieser Lauf wurde mit der W2-Kalibrierung gerechnet:
   rho_f 0,04158 und beta_sd 0,44648 bzw. 0,08317 und 0,58333 [v5d `windows.W1.beta_control_recommended_high_rep.{measured,stress}.rho_f/beta_sd`].
   Die W1-eigenen Werte sind 0,04624 und 0,57367 bzw. 0,09248 und 0,77067.
   Ursache ist ein Code-Defekt: In `prelaunch.assemble_prelaunch_report` nutzt die Gewinner-Schleife die Variable
   `study` aus der vorherigen Fensterschleife, also immer W2. Korrekt kalibriert liegen fuer W1 nur die
   300-Replikate-Studienzellen vor: Decke measured 0,00750 und stress 0,00810.
6. Abstand zur Schwelle: min IC_min / bindende Decke = 0,01675/0,00810 = 2,07 (W1) und 0,01460/0,00685 = 2,13 (W2)
   [abg.]. Der Kill greift fuer keine Variante, der Befund ist gegen den MC-Fehler der Decke robust. Der MC-SE einer
   Decke aus 300 Replikaten liegt bei ~0,00025 [abg.: SD des Maximums der Rausch-Decke 0,00427/sqrt(300)].

**Tabelle (alle driftfrei, Mittel des Maximums ueber 7 Varianten).**

| Zeile | W1 | W2 | Rolle | Fundstelle |
|---|---:|---:|---|---|
| fm_neutral_8w, stress (Fensterkalibrierung) | **0,00810** (300 Rep.) | **0,00685** (1.000 Rep.) | **GL-012-bindend (Empfehlung)** | W1: `beta_control_method_study.calibrations.stress.methods.fm_neutral_8w`; W2: `beta_control_recommended_high_rep.stress` |
| fm_neutral_8w, measured | 0,00750 (300) | 0,00637 (1.000) | Bericht | analog `measured` |
| fm_neutral_8w, zero | 0,00723 (300) | 0,00599 (300) | Bericht | `calibrations.zero` |
| roh (`none`), stress | 0,02777 | 0,01740 | Bericht (DEC-76 (c)); liegt ueber IC_min, deshalb ist die Beta-Kontrolle PASS-Komponente | `calibrations.stress.methods.none` |
| roh (`none`), measured | 0,01770 | 0,01154 | Bericht | `calibrations.measured.methods.none` |
| TS-8w, rho_f 0,2 (v3) | 0,04963 | 0,04993 | historisch, nicht bindend | `factor_preserving_null.driftfree` |
| DEC-86-Zitat W1 | 0,0074 / 0,0079 | - | ungueltig (W2-Kalibrierung) | `windows.W1.beta_control_recommended_high_rep` |

**Empfehlung (ein Satz).** GL-012-bindend ist die Decke der registrierten Methode `fm_neutral_8w` unter der strengeren
der beiden registrierten Kalibrierungen: stress, je Fenster mit der eigenen Fensterkalibrierung, driftfrei, Mittel
des Maximums ueber K = 7, 1.000 Replikate, Seed 53. Die Werte sind W1 0,0081 (vorlaeufig, die 1.000-Replikate-Nachrechnung
mit W1-Kalibrierung ist Pflicht) und W2 0,00685. Die TS-v3-Zeile 0,0496/0,0499 wird nur als historische
Report-Zeile gefuehrt.

**Folge.** Im Registrierungs-YAML werden `windows.<W>.ceiling_driftfree_res` mit diesen Werten belegt, nicht mit der
Vorlage. Der Prelaunch-Defekt wird behoben, danach rechnet v5e die W1-Gewinnerzellen neu. Dieser Lauf ist bindend in
beide Richtungen (DEC-85 (v)), denn die W1-stress-Marge des DEC-77-Kriteriums betraegt bei korrekter Kalibrierung nur
+0,76 SE: mom4 0,00123 gegen die Grenze 0,00168, SE 0,0104/sqrt(300) [abg.].

---

### B. Gap im Reversal-Design: eine Woche statt PRD-"ein Tag"

**Frage.** PRD 5.3 legt das Gap-Design mit einem Tag Abstand zwischen Formation und Halteperiode als PRIMAERE Fassung
fest. Der Code (`characteristics.reversal_gap_characteristic`: `char[t] = returns[t-1]`) trennt um eine ganze
Woche. Laut Bericht ist das "kleinste darstellbare Gap" [v5d `reversal_gap_design_deviation`].

**Fundstellen.** PRD 5.3, Tabelle A3-R: Bid-Ask-Bounce erzeugt einen positiven Reversal-IC, das Gap-Design soll ihn
strukturell eliminieren. Review v2 W-14: IC_prior 0,03 ist fuer rev_gap (Lag 2 Wochen) unbelegt. DEC-75 (8):
"rev_gap: Prior aus dem Ein-Tages-Design uebernommen, DEC-52-Zweig fuer rev_gap vorab zugelassen, falls
Power < 0,60 bei Prior 0,01 - Feststellung VOR dem Lauf". Die Zweitfassung (zurueckgezogen) fuehrte die Woche als
"bestaetigte" Abweichung, DEC-86 (b) als offen.

**Herleitung.**
1. *Zweck erfuellt.* Bei einer Woche Gap teilen Formation (Woche t-1, Schlusskurse t-2 -> t-1) und Outcome
   (Woche t+1, Schlusskurse t -> t+1) keinen Schlusskurs. Ein Bounce-Term kann daher nicht in beide eingehen,
   der Bounce ist mindestens so streng eliminiert wie bei einem Tag Gap.
2. *Darstellbarkeit.* Die Behauptung "kleinste darstellbare Gap" gilt nur auf dem Wochenraster. `panel_1d` hat
   Tagesschluesse, ein Ein-Tages-Gap waere PIT berechenbar. Die ganze Null-Maschinerie rechnet aber auf Wochenproxies:
   Persistenz-Null, faktorerhaltende Null, Kalibrierung (`characteristics.weekly_only_proxy_characteristic`). Ein
   Ein-Tages-Gap hat dort keinen Proxy und waere ohne Tagesaufloesung der Simulation weder kalibrierbar noch durch v5d
   gedeckt. Eine Umstellung braeuchte einen neuen Vorlauf mit neuer Simulationsaufloesung, und v5d waere dafuer nicht
   mehr die bindende Grundlage (DEC-85 (v)).
3. *Inhaltliche Folge.* Getestet wird ein Lag-2-Reversal (Vorvorwochen-Rendite gegen Folgewoche), nicht das
   PRD-Kurzfrist-Reversal. Ein DROP von H-29 ist daher kein DROP des PRD-Ein-Tages-Designs. Die Entscheidungsrelevanz
   "DROP aller drei -> Klasse W erschoepft" muss fuer A3-R entsprechend eingeschraenkt werden.
4. *Power-Feststellung nach DEC-75 (8)* [abg.: P = Phi(Prior x 2,4865 / IC_min - 2,4865), IC_min aus v5d]:
   - Prior 0,03: W1 0,967, W2 0,991 (>= 0,60, also C.10 hart).
   - Prior 0,01: W1 0,148, W2 0,194 (< 0,60). Damit ist die Bedingung aus DEC-75 (8) erfuellt, und der
     DEC-52-Zweig fuer rev_gap ist zulaessig.
   - Der Code hat keinen DEC-52-Zweig (`gates.py`, Docstring: "NOT wired").

**Empfehlung (ein Satz).** Das Ein-Wochen-Gap wird als registrierte, etikettierte Abweichung von PRD 5.3 bestaetigt.
Es eliminiert den Bounce mindestens so streng wie das Ein-Tages-Gap, testet aber das Lag-2-Reversal. Die Variante
wird nicht umgebaut, und es kommt keine Zusatzvariante hinzu (K bleibt 7). Die DEC-75-(8)-Feststellung
"DEC-52 zulaessig (Power 0,15/0,19 bei Prior 0,01)" wird schriftlich vor dem Lauf gefuehrt. Die Zuordnung selbst
folgt Vorlage F.

**Folge.** Etiketten: "Gap-Design eine Woche (Abweichung PRD 5.3; Lag-2-Reversal)" und "PRD-Ein-Tages-Design nicht
getestet". Die Formulierung im Code-Docstring wird von "darstellbar" auf "auf dem Wochenraster" korrigiert (Kosmetik).

---

### C. Faktor 1/sqrt(2) in der analytischen Selektionsdecke

**Frage.** Der Bericht rechnet die analytische Decke als 1/sqrt(2) x z_max(K=7) x SE_W. Er deutet den Faktor als
"Kombination der zwei unabhaengigen Fenster" [v5d `selection_ceiling_scale_factor_interpretation`;
`prelaunch.analytic_selection_ceiling`].

**Fundstellen.** PRD 3.3.4: E[max SR] ~= sigma_SR x (...), sigma_SR ~= 1/sqrt(T). PRD 5.3: "Analytische Decke bei
T = 2 a: 0,7071*(0,4228*1,0676 + 0,5772*1,6207) = 0,98". Die Zweitfassung rechnete ausdruecklich "ohne den PRD-Faktor
1/sqrt(2), der aus dem gepoolten 2-Jahres-Sharpe stammt". Review v2 W-11 korrigierte die W2-Decke (analytisch 0,00806).

**Herleitung.**
1. 0,7071 ist sigma_SR = 1/sqrt(T) mit T = 2 Jahren. Der Faktor gehoert zur Streuung eines gepoolten
   Zwei-Jahres-Schaetzers.
2. Unter C.10 hart wird je Fenster geurteilt, und die Decke je Fenster ist z_max x SE_W. Der Faktor wuerde die Decke
   um sqrt(2) zu niedrig ansetzen.
3. Empirische Gegenprobe [v5d `selection_ceiling_measured.ceiling_ic_mean`, 300 Rep.; `selection_ceiling_analytic`]:

   | Fenster | analytisch ohne Faktor (1,3868 x SE_W) [abg.] | mit Faktor (v5d) | gemessen, reines Rauschen |
   |---|---:|---:|---:|
   | W1 | 0,00934 | 0,00661 | 0,00919 (MC-SE 0,00025) |
   | W2 | 0,00814 | 0,00576 | 0,00778 (MC-SE 0,00021) |

   Die Messung trifft die Fassung ohne Faktor und liegt 10 bis 11 MC-SE ueber der Fassung mit Faktor.
4. Keine bindende Zahl haengt am Faktor. Die DEC-77-Grenze nutzt die GEMESSENE Rausch-Decke
   (1,5 x 0,009185 = 0,013778 und 1,5 x 0,007782 = 0,011672 [v5d `beta_control_decision.ceiling_bound`]),
   GL-012 nutzt die Methodendecke aus Vorlage A.

**Empfehlung (ein Satz).** Der Faktor 1/sqrt(2) wird fuer die Je-Fenster-Decke verworfen. Er ist sigma_SR eines
gepoolten Zwei-Jahres-Schaetzers, keine Fensterkombination. Die analytische Report-Zeile lautet 1,3868 x SE_W =
0,00934 (W1) / 0,00814 (W2) und wird von der Messung 0,00919/0,00778 bestaetigt. Eine gepoolte SE ist nur im
DEC-52-Zweig zulaessig, und dort wird sie direkt aus der gepoolten Serie gerechnet, nicht als Faktor.

**Folge.** In `prelaunch.analytic_selection_ceiling` beide Werte berichten, bindend ohne Faktor (Kosmetik, nicht
ergebnisrelevant). Die v5d-Zahlen 0,00661/0,00576 werden nirgends als Decke zitiert.

---

## Teil 2 - Weitere Entscheidungen, die vor der Registrierung faellig sind

### D. Kalibrierung je Fenster (DEC-86) gegen den globalen W1-Block im Code

**Befund.** DEC-86 verlangt `beta_sd_calibrated` "je Fenster und Kalibrierung aus dem v5d-Artefakt". Der Code macht
es anders:
- `--emit-registered-template` schreibt nur den W1-Block (`calibration` aus `windows.W1.beta_control_method_study`).
- `run.run_full` nutzt `calibration.stress` fuer BEIDE Fenster.

Fuer W2 rechnet der Lauf damit mit rho_f 0,0925 und beta_sd 0,7707 statt mit dem W2-eigenen Paar 0,0832 und 0,5833.
Fuer diese Konfiguration gibt es keine v5d-Zahl, die +-10-%-Pruefung ist daher nicht vorhersagbar.

**Optionen.** (1) Code folgt DEC-86: Schema `windows.<W>.calibration`, `run_full` liest je Fenster. (2) Eine neue DEC
erklaert den globalen W1-Block fuer bindend. Das waere eine Abweichung von DEC-86, und die W2-Konstanten muessten mit
dem W1-Paar neu gerechnet werden.

**Empfehlung.** Option (1): Der Code folgt dem Wortlaut von DEC-86. Die eingefrorenen Konstanten entstehen danach in v5e
aus genau der Lauf-Konfiguration, also registrierte Methode, Fensterkalibrierung stress, driftfrei, 1.000 Rep., Seed 53,
as_of 2026-09-28. Fuer W2 liegen sie in v5d bereits vor; das W2-Paar ist bitgleich zur Lauf-Konfiguration, bei
identischem Panel und as_of reproduzierbar.

### E. Drift im Beta-Kontroll-Quantil: DEC-76 E1 (b) "driftend" gegen den Code "driftfrei"

**Befund.** DEC-76 E1 (b) verlangt: Der residualisierte Mittel-IC muss jenseits des 99,36-%-Quantils "unter der
driftenden Faktor-Null" liegen (Drift 0,002/Woche). `run.run_full` rechnet das Quantil driftfrei (`drift_f =
DRIFT_F_DRIFTFREE`), der YAML-Schluessel heisst trotzdem `res_quantile_drifting`. DEC-77/78/85/86 aendern (b) nicht
ausdruecklich. Das Gate-Audit v5c (Punkt 3) haelt fest: Fuer Vol- und Beta-Charakteristiken "ist gerade die Drift der
relevante Kanal", und die Studie ist driftfrei. Der Driftwert 0,002 ist selbst nicht gemessen (UNBELEGT als
Messgroesse, nur als Wert aus DEC-76 belegt).

**Empfehlung.** Strengste Lesart ohne neuen Parameter: v5e rechnet das Quantil je Variante und Fenster zweimal, unter
der stress-Kalibrierung driftfrei und mit Drift 0,002 (dem einzigen registrierten Driftwert). Bindend ist das in
Hypothesenrichtung extremere der beiden. Der Code rechnet beide nach und prueft beide +-10 %. Der Schluessel wird
umbenannt oder dokumentiert. Faellt diese Option weg, braucht die driftfreie Fassung eine eigene DEC mit Begruendung,
denn das waere eine Abweichung von DEC-76 E1 (b).

### F. Power-Zeile des vollstaendigen Tests und Zuordnung C.10 / DEC-52 / GL-012 je Variante

**Befund** [abg.; Formeln: P_ICmin = Phi(0,03 x 2,4865/IC_min - 2,4865); P_beta = Phi((0,03 - max(IC_min, |q|))/sd);
q und sd = Quantil und SD des Mittel-IC der fm8-stress-Null; W1 aus 300 Rep. mit W1-Kalibrierung, W2 aus 1.000 Rep.].
Die bisherigen Power-Zeilen rechnen nur mit IC_min. Seit DEC-76 (b) gehoert das Beta-Kontroll-Quantil q zum
registrierten Test, und fuer die Momentum-Varianten liegt q ueber IC_min.

| Variante | W1: IC_min / q / P_ICmin / P_beta / MDE80 | W2: IC_min / q / P_ICmin / P_beta / MDE80 |
|---|---|---|
| mom1 | 0,01966 / 0,02042 / 0,90 / 0,89 / 0,0271 | 0,01744 / 0,01700 / 0,96 / 0,98 / 0,0233 |
| mom2 | 0,01754 / 0,02291 / 0,96 / **0,79** / **0,0303** | 0,01558 / 0,02029 / 0,99 / 0,92 / 0,0262 |
| mom4 | 0,01729 / 0,02815 / 0,97 / **0,57** / **0,0369** | 0,01541 / 0,02490 / 0,99 / **0,73** / **0,0319** |
| rev_gap | 0,01727 / -0,01422 / 0,97 / 0,96 / 0,0236 | 0,01531 / -0,01546 / 0,99 / 0,99 / 0,0210 |
| vol_rv, vol_max | 0,01694, 0,01698 / -0,02202 / 0,97 / 0,86 / 0,0282 | 0,01470, 0,01464 / -0,01639 / 0,99 / 0,99 / 0,0216 |
| vol_beta | 0,01675 / -0,00567 / 0,98 / ~0 (strukturell, Vorlage H) / - | 0,01460 / -0,00483 / 1,00 / ~0 / - |

Regeln: DEC-51 (2): Liegt der Prior unter der MDE bei Power 0,80, ist die Registrierung ein GL-012-Fall oder braucht ein
anderes Design. DEC-52 (i): Bei Per-Fenster-Power < 0,60 ist der DEC-52-Zweig anwendbar. DEC-75 (8) gilt fuer rev_gap
bei Prior 0,01, siehe Vorlage B. Die W1-Quantile aus 300 Ziehungen haben einen MC-Fehler von ~10 % [abg.:
SE(q_0,9936) ~= 0,253 x sd bei n = 300]. Bei mom2 liegt W1 damit innerhalb des MC-Fehlers an der Grenze.

**Empfehlung.** Die Power-Zeile wird fuer den vollstaendigen registrierten Test gefuehrt. Die Zuordnung je Variante
erfolgt mechanisch auf den v5e-Zahlen (1.000 Rep., Fensterkalibrierung, Driftentscheidung E) und VOR der Registrierung,
ohne Ermessen:
- P_voll >= 0,80 in beiden Fenstern: C.10 hart.
- MDE80 > IC_prior in einem Fenster: GL-012-Feasibility-DROP der Variante (DEC-51 (2), K bleibt 7), ausser
  P_voll < 0,60 und der DEC-52-Zweig ist gebaut und getestet.
- rev_gap: C.10 hart gegen den registrierten Prior 0,03; die DEC-52-Zulaessigkeit aus DEC-75 (8) wird festgestellt,
  aber nicht genutzt (strengere Fehlerrate), mit Etikett "unterpowert gegen Lag-2-Prior 0,01 (0,15/0,19)".

Prognose auf v5d-Basis, nicht entschieden: mom4 wird GL-012-Fall, mom2 ist offen bis v5e, die uebrigen gehen in C.10 hart.

### G. H-30: Drag in Tages- statt Wocheneinheiten, und das Vorzeichen verdoppelt den Drag

**Befund 1 (Einheit).** `vol_rv` ist die SD der Tages-Log-Renditen der Woche. Der Code-Docstring nennt sie
"Realized weekly vol", tatsaechlich hat sie Tageseinheit (`characteristics.realized_vol_characteristic`, `np.std` der
Tagesrenditen, ohne Skalierung). Daraus folgt:
- Der Drag `0,5 x vol_rv^2` (`ic.vol_weighted_outcome_with_drag`, `prelaunch.h30_feasibility`) ist ein Tages-Drag.
- Outcome (Wochen-Log-Rendite) und Kante (91,42 bp/Woche aus sigma_xs der Wochenrenditen) sind Wochengroessen.
- PRD 5.3 rechnet den Drag selbst als Tageswert x 7: "0,105 %/Tag = 73,5 bps/Woche".
- Die Zweitfassung bestaetigt die Tageseinheit indirekt: "target_vol^2/2 = 8,5 bp" ergibt target_vol ~ 0,041, also eine
  typische Tages-Vol.

Feasibility in Wocheneinheiten (Hochrechnung x n, n = 7 Tagesrenditen je Kalenderwoche, Krypto handelt 7 Tage):

| Verhaeltnis | v5d (Tageseinheit) | x 7 [abg.] | Grenze |
|---|---:|---:|---|
| Spread(D10-D1)/Kante | 0,395 | **~2,8** | <= 0,5, verfehlt |
| SE/Kante | 0,025 | ~0,18 | <= 0,5, erfuellt |

**Befund 2 (Vorzeichen).** Das Outcome ist eine Log-Rendite, und PRD 5.3 gibt E[r_arith] - E[r_log] = sigma^2/2 an.
Bereinigen heisst daher r_log + sigma^2/2. Der Code rechnet `(r_{t+1} - drag[t]) x weight[t]` und zieht den Drag ab,
verdoppelt ihn also. Der Zusatzterm -target x sigma_w/2 faellt streng monoton im Vol-Rang und erzeugt das registrierte
negative Vorzeichen mechanisch. Review v2 B-5 bleibt damit offen. DEC-75 (4) sagt woertlich "Drag-Abzug ... vom
UNGEWICHTETEN Outcome"; der Code folgt dem Wortlaut, nicht dem Zweck. Die Groesse des mechanischen IC ist UNBELEGT.
Eine Naeherung ergibt in Tageseinheit etwa 0,25 IC_min, in Wocheneinheit etwa 1,7 IC_min in Hypothesenrichtung.

**Empfehlung.**
1. Eine DEC praezisiert DEC-75 (4): sigma_w = Wochen-Vol aus den Tagesrenditen der Woche t (sqrt(n_t) x vol_rv), und
   "bereinigt" heisst r_log + sigma_w^2/2. Die Aenderung ist strenger, weil sie einen mechanischen Vorteil entfernt.
2. v5e rechnet die H-30-Feasibility auf L in Wocheneinheiten neu. Diese Zahl ist offen nach DEC-75 (8), das Siegel
   betrifft nur L-IC-Details.
3. Bei Spread/Kante > 0,5 (Prognose ~2,8) folgt GL-012-DROP fuer H-30 vor dem Lauf (DEC-74 (h)), K bleibt 7. Die drei
   H-30-Varianten werden dann NICHT gerechnet, also auch nicht berichtet; der BH-Nenner bleibt fest 7.
4. Das PRD-geforderte A3-V-Fixture "identische Vol-Dispersion ohne Zusammenhang" wird mit E[r_log] = mu - sigma^2/2 als
   T1-Test gebaut. Dort darf kein Gate feuern.

### H. vol_beta ist unter fm_neutral_8w strukturell nicht bestehbar (C.4)

**Befund.** Die Charakteristik `vol_beta` ist das 8-Wochen-PIT-Beta zu BTC. `fm_neutral_8w` regressiert das Outcome je
Woche auf genau dieses Beta (Kontrolle aus `returns_est`, mindestens 8 gueltige Wochen) und nimmt das Residuum. Das
Residuum ist linear orthogonal zur Charakteristik. In der Null hat der Mittel-IC von vol_beta eine SD von nur 0,0022
(W1) bzw. 0,0019 (W2) gegen IC_min 0,0168/0,0146 [v5d fm8-stress `variants.vol_beta.mean_ic_draws_sd`]. Selbst eine
echte Beta-Praemie kann (3b) daher praktisch nicht erfuellen.

**Empfehlung.** Vorab GL-012 fuer vol_beta mit dem Etikett "strukturell durch die registrierte Beta-Kontrolle
neutralisiert (C.4)". K bleibt 7, und kein Methodenwechsel nach DEC-86. Faellt H-30 nach Vorlage G ohnehin, wird das
nur dokumentiert.

### I. Gate-Code weicht von DEC-75 (5) und vom Liquiditaets-Etikett ab

**Befund** (`gates.evaluate`, Test `test_liquidity_and_bounce_labels_do_not_change_verdict`, `test_bounce_fixture_end_to_end_label_not_verdict_change`):
1. *Bounce.* DEC-75 (5) verlangt bei |IC_bounce| >= |IC_real| "Etikett Artefakt, KEIN PASS". Der Code vergibt nur ein
   Etikett, das Verdikt bleibt, und er prueft nur W1. Das ist die Lockerung, die Review v2 B-7 benennt.
2. *Liquiditaet.* Das Etikett "Illiquiditaets-Artefakt" gilt laut PRD 5.3 Gate (4) ("faellt er dort weg") und laut
   Zweitfassung bei IC_ohne_D1 > -0,5 x IC_min. Der Code etikettiert bei `liq <= -0,5*IC_min`, also genau dann, wenn
   der Effekt den Ausschluss UEBERLEBT. Die Bedingung ist invertiert und wird nur in W1 geprueft.

**Empfehlung.**
- Bounce: je Fenster gilt |IC_bounce,W| >= |IC_W| -> kein PASS, mit Etikett.
- Liquiditaet: Etikett, wenn IC_ohne_D1,W > -0,5 x IC_min(rev_gap, W) in mindestens einem Fenster.
- Beide Tests werden auf die registrierte Regel umgestellt.
- Survivorship bleibt Etikett (DEC-76: die PRD-Bedingung "nicht rekonstruierbar" ist durch das Union-Panel falsch
  geworden). Etikett rev_gap W2: -0,58 IC_min-Einheiten, d. h. ein unkontrolliertes Panel waere in Hypothesenrichtung
  verzerrt.

### J. Verdikt je Hypothese bei mehreren Varianten

**Befund.** H-28 und H-30 haben je drei Varianten. Die Vorlage bildet aber nur je eine ab (H-28 = mom1, H-30 = vol_rv),
damit faellt der BH-Nenner auf 3 statt K = 7 (DEC-74 (e)). Ob "H-28 PASS" alle Varianten oder mindestens eine verlangt,
ist nirgends festgelegt.

**Empfehlung.** Alle sieben Varianten werden als eigene Eintraege registriert (`H-28_mom1` ... `H-30_vol_beta`).
Eine Hypothese gilt als PASS, wenn mindestens eine ihrer Varianten PASS hat. Die Selektion ueber K = 7 ist durch die
GL-012-Decke (Mittel des Maximums ueber 7) und durch BY in F-WEEK gedeckt, jede Variante wird einzeln berichtet. Der
BH-Nenner ist fest 7; nicht gerechnete Varianten gehen mit p = 1 ein (Code-Anpassung).
