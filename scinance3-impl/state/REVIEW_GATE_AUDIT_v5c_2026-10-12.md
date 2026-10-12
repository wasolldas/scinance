# Gate-Audit WP-13a Vorlauf v5c - Beta-Kontroll-Methodenvergleich (DEC-77 E1 (c)) - 2026-10-12

Rolle: adversarischer Gate-Auditor (Veto-Recht), nur lesend. Keine Repo-Datei geaendert, nichts committet
(`git status` leer). Siegel gewahrt: keine `*_L_window_sealed.json`, `weekly_ic_series.csv`,
`ic_series_*_UNION_REAL.csv` geoeffnet, gehasht oder gegrept.

Gelesen: `state/runs/wp13a_20261012/wp13a_prelaunch.json` (sha256 `fe3b1650...c553b` = Lauf-Log),
`wp13a_prelaunch.md` (`cbf70147...e4e0` = Lauf-Log), `cloud_run.log`; DEC-58, DEC-73..DEC-84;
Registry H-28..H-30 (Erst-/Zweitfassung, beide Rueckzuege); REVIEW v1/v2; PRD 5.3; GL-012 (2.0-Akte);
Code `prelaunch.py`, `nulls.py`, `ic.py`, `characteristics.py`, `wp7_universe/panel_load.py`,
`pit_universe.py`. Lauf-Code 2f8c6a0; `git diff 2f8c6a0 HEAD -- src/.../wp13_xsec scripts/wp13_xsec.py` leer
(gelesener Code = gelaufener Code).

Eigene Nachrechnungen: nur Simulation (keine Realdaten, keine Charakteristik-Outcome-Verknuepfung),
synthetische Lebend-Maske mit der realen K-Reihe je Woche aus dem Artefakt (wie DEC-81-Kontrolllauf),
Bibliotheksfunktionen des Repos unveraendert, nur per Monkeypatch parametrisiert. Skripte:
`scratchpad/scripts/{recompute,variants,sens_sigma_e,sens_clean_btc,full_rule_clean}.py`,
Logs `scratchpad/clean_W1.log`, `clean_W2.log`.

---

## 0. Urteil

**VETO** gegen den Gate-Log-Eintrag "keine Methode -> Klasse W auf diesem Panel nicht testbar (GL-012)" auf
Basis von v5c. Regel und Arithmetik sind korrekt umgesetzt (Punkt 1), und das Ergebnis haelt dem
Monte-Carlo-Fehler stand (Punkt 2). Es haengt aber an einem **nicht registrierten Konstruktionsdetail der
Simulation**: Die simulierte "BTC-Spalte" ist eine beliebige Simulationsspalte mit voller
idiosynkratischer Vol. Damit stimmt sie nicht mit den gemessenen Kalibrierungszielen ueberein, die
DEC-77 (a) selbst festlegt (sigma_f und rho_f der realen BTC-Wochenserie). Die Gegenprobe prueft das
nicht. Setzt man die Marktspalte konsistent (= Faktor, reproduziert sigma_f und rho_f), bestehen
fm_neutral_8w/13w/26w und double_sort_13w **alle** Kriterien in W1 und W2, unter measured UND stress
(Punkt 4, D1). Damit ist das Ergebnis "keine Methode besteht" ein Artefakt dieses Konstruktionsdetails
und kein Befund ueber das Panel.

Das VETO erlaubt **keine** Registrierung: Die Konsistenz-Variante ist eine Schranke und keine
Kalibrierung. Auch eine Teilkohorte ist ausgeschlossen (Punkt 3). Weiter geht es nur mit einer neuen DEC,
die die Konstruktion vorab fixiert, und einem Vorlauf v5d mit unveraenderter PASS-Regel.

---

## 1. Ist die Entscheidungsregel korrekt implementiert und angewandt?

**Ja.** `prelaunch.beta_control_pass_table` (Z. 400-447) prueft je Methode fuer `measured` UND `stress`:
(a) max ueber alle 7 Varianten von |`mean_ic_draws_mean`| <= `0,25 * e_floor / sqrt(w_judged)`,
(b) `ceiling_mean_of_max` <= `1,5 * selection_ceiling_measured.ceiling_ic_mean` (gemessene
Rausch-Decke, 300 Replikate, Seed 53). `zero` wird berichtet und ist nicht bindend, wie DEC-77
("kalibriert UND Stress-rho") es vorsieht. `beta_control_recommendation` (Z. 450-495) verlangt das
Bestehen in **jedem** Fenster (Schnittmenge) und gibt sonst `None` mit dem GL-012-Hinweis zurueck.
`assemble_prelaunch_report` uebergibt `floor=e_floor`, `w_judged`, `pure_noise_ceiling` des Fensters.

Nachrechnung aus dem JSON (alle 12 Tabellenzeilen stimmen auf 5 Stellen mit dem .md ueberein):

| Fenster | e_floor | W_geurt. | 0,25*Boden/sqrt(W) | Rausch-Decke | 1,5*Decke |
|---|---|---|---|---|---|
| W1 | 0,048579 | 52 | **0,001684** (JSON 0,001684) | 0,009185 | **0,013778** (JSON 0,013778) |
| W2 | 0,041921 | 51 | **0,001468** (JSON 0,001468) | 0,007782 | **0,011672** (JSON 0,011672) |

Stichproben: W1 stress fm_neutral_13w: worst mom4 0,00183 > 0,00168 -> FAIL; Decke 0,01213 <= 0,01378.
W2 stress fm_neutral_8w: worst mom1 0,00273 > 0,00147 -> FAIL; Decke 0,01212 > 0,01167 -> FAIL.
W2 measured double_sort_26w: 0,00152 > 0,00147 -> FAIL. In beiden Fenstern ist `passing_methods` leer,
die Empfehlung ist `None`.

Anmerkungen ohne Urteilsrelevanz:
- e_floor W1 0,048579 (52 geurteilte Wochen) gegen den Registry-Wert 0,04849 (53 Wochen): Die
  Grenze verschiebt sich um 0,000003.
- Die Lesart "schlechteste von 7" fuer das Null-Mittel steht so nicht woertlich in DEC-77. Sie ist aber
  die einzig vertretbare, weil die Methode als EIN Parameter fuer alle 7 Varianten registriert wird
  (DEC-77 E2 `beta_control: {methode, beta_fenster}`; `run.py` Z. 629-637). Die Decke ist per Definition
  "Mittel des Maximums ueber 7 Varianten" (DEC-75 (2), DEC-76 (c)).
- Die Regel wird gegen die gemessene Rausch-Decke geprueft, die analytische Decke (0,00661/0,00576) waere
  strenger. PRD 5.3 legt die gemessene Decke als verbindlich fest; das ist korrekt und im Zweifel milde.
- Testluecke (kosmetisch): `test_beta_control_pass_table_pass_and_fail_boundaries` hat keinen Fall, in
  dem eine Methode nur unter stress scheitert. Die Schleife in Z. 424-439 deckt diesen Fall aber
  offensichtlich ab, und das Artefakt zeigt ihn (W1-FM-Zeilen).

## 2. Ist "keine Methode besteht" robust gegen den Monte-Carlo-Fehler?

**Innerhalb des implementierten Modells ja, und zwar wegen W2.** Deine SE-Rechnung
(SE = `mean_ic_draws_sd / sqrt(300)`, Grenze deterministisch) ist korrekt. Nachgerechnet:

| stress | W1 schlechteste Variante | (|m|-Grenze)/SE | W2 schlechteste Variante | (|m|-Grenze)/SE |
|---|---|---|---|---|
| fm_neutral_8w | **mom2** 0,00208 | +0,66 | mom1 0,00273 | +2,44 |
| fm_neutral_13w | **mom4** 0,00183 (mom2 +0,2) | +0,23 | mom1 0,00300 | +2,87 |
| fm_neutral_26w | **mom4** 0,00200 | +0,49 | mom1 0,00280 | +2,23 |

Korrektur: In W1 ist die schlechteste Variante mom2 (8w) bzw. mom4 (13w, 26w), nicht mom1. In W1
liegen mom1/mom2/mom4 fast gleichauf, deshalb ist das Maximum ueber Varianten nach oben verzerrt
(Gewinnerfluch). W1 ist bei n_reps 300 nicht entscheidbar. In W2 ist mom1 klar am schlechtesten, und
unter 8w/13w liegen auch mom2/mom4 ueber der Grenze. Pro Methode betraegt die einseitige
MC-Wahrscheinlichkeit, faelschlich zu scheitern, etwa 0,002-0,013. Weil alle Zellen denselben Seed 53
nutzen (gemeinsame Zufallszahlen), sind die Fehler zwischen den Methoden korreliert und nicht
unabhaengig. Zusaetzlich verletzt jede FM-Methode in W2 stress auch die Decke
(0,01212/0,01242/0,01285 > 0,01167). Grob geschaetzt sind das 0,7-1,8 SE; die SD des Maximums je
Replikat steht nicht im Artefakt. Fuer sich allein ist das nicht robust, es stuetzt den Befund aber.

Weitere Fehlerquellen:
- Kalibrierungsfehler: Die SE der Suche (W2 stress 4,5 % des Anteils) verschiebt das Null-Mittel um
  etwa 0,0001 und ist damit vernachlaessigbar.
- Gegenprobe: In W2 liegt der simulierte Anteil 3-4 % unter dem Ziel. Die W2-Null-Mittel sind also
  eher unterschaetzt, das wirkt konservativ. In W1 liegt er +7 % darueber (z 1,5-1,7, ueber die
  gemeinsamen Seeds korreliert), damit sind die W1-Werte leicht ueberschaetzt.
- Unabhaengige Replikation mit synthetischer Maske und unveraenderter Konvention:
  W2 stress fm_8w mom1 +0,00336 (+3,7 SE) FAIL;
  W1 stress fm_8w/13w/26w mom1 +0,00245/+0,00230/+0,00199 (+1,3/+1,1/+0,5 SE) FAIL.

**Aber:** Robust gegen MC-Fehler heisst nicht robust gegen Modellfehler, siehe Punkt 4.

## 3. Ganze Kohorte oder Teilkohorte? Strengste vertretbare Lesart

**Die Konsequenz gilt fuer die ganze Kohorte und darueber hinaus fuer die ganze Klasse W auf diesem
Panel. Eine Teilkohorte waere jetzt Zurueckskalieren bzw. Torpfosten-Verschieben und keine legitime
neue Hypothese.** (Das gilt fuer den Fall, dass ein korrigierter Vorlauf erneut "keine Methode" ergibt.)

Zitate:
- DEC-77 E1 (c): "die Drittfassung registriert die Methode, die die Kriterien bei beiden rho erfuellt;
  erfuellt keine, ist **Klasse W auf diesem Panel** nicht testbar (B1-analog, GL-012) - dann **keine
  Registrierung, kein Zurueckskalieren**." Der Geltungsbereich ist die Klasse, nicht eine Hypothese.
- DEC-77 E2: "Lauf-Modus uebernimmt **die** gewaehlte Methode als Parameter der Registrierungsdatei
  (`beta_control: {methode, beta_fenster}`)". Das ist eine Methode fuer die ganze Registrierung; eine
  Wahl je Hypothese ist nicht vorgesehen.
- DEC-73 E1: "K = 7 der Kohorte ist vorab deklariert, damit spaetere Aufnahme keine Inflation ist";
  DEC-74 (e): "K = 7 bleibt Nenner, auch bei Nichtlauf von H-30"; DEC-75 (2) / DEC-76 (c): Decke =
  "Mittel des Maximums ueber 7 Varianten". Auch eine Teilkohorte muesste also die Decke ueber 7
  Varianten bestehen. Diese schliesst die Momentum-Varianten ein, die Teilkohorte gewinnt dadurch
  rechnerisch nichts.
- Gegenprobe des Wortlauts: Wo die Akte einen DROP je Hypothese wollte, steht er ausdruecklich da:
  DEC-74 (h) "Nichtbestehen = GL-012-DROP **fuer H-30**, K bleibt 7". DEC-77 (c) waehlt bewusst die
  Klasse. Ein stilles "nur H-30" ist deshalb nicht hineinlesbar.
- PRD 5.3: "Andernfalls wird die Kohorte gestrichen und nie ... zurueckskaliert"; "Bei DROP aller drei:
  die Klasse W ist auf Bybit-Perps im Wochenhorizont erschoepft".
- Verfassung (scinance3-impl/CLAUDE.md, Autonomie 1): "kein Torpfosten-Verschieben in KEINE Richtung".
- DEC-58 E2: "Ein Nulleffekt-/Erreichbarkeits-Zensus darf NIEMALS einen Kandidaten promoten; zulaessige
  Ausgaenge sind ein D-Eintrag oder 'nicht ausgeschlossen'. Jede Registrierung, die aus einem Zensus
  hervorgeht, braucht eine eigene, vorab formulierte Hypothese mit eigenem K." Das ist eine
  **notwendige** Bedingung und keine Erlaubnis. "Vorab formuliert" ist fuer eine Vol- oder
  Reversal-Teilkohorte nicht mehr erfuellbar, weil die variantenweisen Ergebnisse des Vorlaufs bekannt
  sind (die Null-Mittel verletzen nur mom1/mom2/mom4). Jede Auswahl "die sauberen Varianten" waere
  durch genau diesen Befund informiert.
- GL-012 (2.0) als Praezedenz: "Der DROP wird angenommen, nicht umgangen". H-08 war nur zulaessig als
  "NEUE, separat vorzuregistrierende Hypothese (nicht durch dieses DROP nahegelegt ...)" mit
  geaendertem Design, das die strukturelle Ursache beseitigt. Hier liegt die Ursache (Markt-Persistenz x
  Beta-Schaetzrauschen) im Panel und nicht in H-28. Ein "nur H-30" beseitigt sie nicht, es meidet nur
  die Varianten, an denen sie sichtbar wird.

Sachlich spricht noch etwas gegen eine Vol-Teilkohorte: Die Studie zertifiziert die Vol-Varianten gar
nicht. In der Simulation sind vol_rv und vol_max beide der Proxy |r| und damit identisch
(`characteristics.weekly_only_proxy_characteristic`, Z. 349-350), und die Studie ist driftfrei. Fuer
Vol/Beta-Charakteristiken ist aber gerade die Drift der relevante Kanal (DEC-76; das Artefakt zeigt
"Quantil drifting res" vol_beta -0,115/-0,111). Dass diese Varianten fast kein Null-Mittel haben, ist
eine Eigenschaft des Proxys und kein Befund.

Strengste vertretbare Lesart: Ergibt ein **korrekt kalibrierter** Vorlauf keine Methode, dann gilt:
keine Registrierung von H-28, H-29 oder H-30, weder einzeln noch in Teilmengen, und keine neue
Klasse-W-Hypothese auf diesem Panel (Union panel_1d, W1/W2). Das gilt, solange nicht eine neue DEC
eine andere Datenbasis eroeffnet, die unabhaengig von diesem Ergebnis begruendet ist.

## 4. Defekte in der Kalibrierungs-/Studienkette

### D1 (ergebnisbestimmend) - Die simulierte Marktspalte verletzt die eigenen Kalibrierungsziele

`nulls.py` Modul-Docstring (Z. 140-149) beschreibt die "Simulierte BTC-Spalte" als "die simulierte
Ziehung, die an BTCUSDTs Position landet", also `(1 + s*z) * f + e` mit voller idiosynkratischer Vol
sigma_e. Diese Konvention stammt aus dem Bau-Briefing und steht in **keiner DEC**. Gegen diese Spalte
werden alle simulierten PIT-Betas geschaetzt (FM, Doppelsortierung, Kalibrierungs-Suche,
Gegenprobe). DEC-77 (a) verlangt dagegen: "rho_f und sigma_f aus der realen BTC-Wochenserie je Fenster
messen ...; Null damit kalibrieren". Die simulierte BTC-Spalte reproduziert keines der beiden Ziele
(per Simulation nachgemessen, 2000 Panels):

| | reale BTC-SD | Sim-BTC-Spalte SD | Faktor | Autokorrelation Sim-Spalte / rho_f (Populationswert) |
|---|---|---|---|---|
| W1 | 0,0669 | 0,088 | x1,32 | x0,58 |
| W2 | 0,0551 | 0,092 | x1,67 | x0,36 |

Die Gegenprobe (DEC-78/81) prueft nur den Faktoranteil und kann diese Abweichung nicht sehen. Folge:
In der Simulation ist der Regressor verrauscht, die Beta-Schaetzungen sind deutlich unzuverlaessiger
als gegen die reale BTC-Serie. Die Bisektion gleicht den beobachteten Anteil durch einen zu hohen
**wahren** Faktoranteil aus (W2 stress 0,074 statt 0,047), und FM laesst entsprechend mehr mechanisches
Momentum stehen. Die Verzerrung geht **gegen** die Methoden.

Ergebnisrelevanz, A/B mit sonst identischem Aufbau (synthetische Maske, Artefakt-sigma_f/sigma_e/rho_f,
Ziel-Anteile und Grenzen, Seed 53, 300 Replikate, alle 7 Varianten). Einzige Aenderung:
Sim-BTC-Spalte := f. Damit werden sigma_f und rho_f exakt reproduziert, beta_sd wird neu bisektiert
(konvergiert):

| Fenster/Kal. | fm_neutral_8w | fm_neutral_13w | fm_neutral_26w | double_sort_13w | Decken |
|---|---|---|---|---|---|
| W1 measured | +0,00055 (-2,6 SE) | +0,00052 (-2,8) | -0,00080 (-2,3) | +0,00081 (-2,0) | 0,0073-0,0094 <= 0,01378 |
| W1 stress | +0,00094 (-1,6) | +0,00064 (-2,3) | -0,00072 (-2,7) | +0,00142 (-0,6) | 0,0078-0,0094 <= 0,01378 |
| W2 measured | +0,00102 (-1,3) | +0,00084 (-1,7) | +0,00134 (-0,3) | +0,00089 (-1,4) | 0,0067-0,0091 <= 0,01167 |
| W2 stress | +0,00103 (-1,3) | +0,00090 (-1,4) | +0,00137 (-0,2) | +0,00124 (-0,5) | 0,0071-0,0091 <= 0,01167 |

(Angegeben ist jeweils die schlechteste Variante, in Klammern (|m| - Grenze)/MC-SE.) **Alle vier
Methoden bestehen die vollstaendige DEC-77-Regel in beiden Fenstern.** fm_neutral_8w und 13w tun das
mit 1,3-2,8 SE Abstand, 26w und double_sort_13w nur knapp. Die Kontrolle mit demselben Aufbau und der
alten Konvention reproduziert das FAIL (Punkt 2). Die Differenz geht also allein auf die Marktspalte
zurueck.

Der wahre Zustand liegt zwischen den Schranken: Reale BTC hat gegenueber dem Alt-Faktor eine eigene,
aber deutlich kleinere idiosynkratische Komponente, als die Konvention unterstellt. Die Konvention
impliziert Korrelation(BTC, Faktor) von 0,76 (W1) bzw. 0,60 (W2) **und** eine zu hohe BTC-SD. Das ist
kein "konservativer Stress" im Sinne von DEC-78. Die Stress-Kalibrierung ist dort vorab und genau
definiert ("2x rho_f UND 2x Faktoranteil"); eine unregistrierte, nicht gemessene dritte
Verschaerfung kommt dort nicht vor. DEC-77 nennt die Bedingung selbst: "Bevor das als
Feasibility-Ergebnis gilt, ist zu klaeren, ob die Null realistisch kalibriert ist."

### D2 (echter Code-Defekt, fuer sich nicht ergebnisbestimmend) - Null-Renditen statt NaN fuer nicht handelnde Symbol-Wochen

`panel_load._daily_close_to_weekly` setzt `returns = np.zeros(...)` (Z. 297). Vor dem Listing, nach dem
Delisting und in Luecken steht damit 0,0 statt NaN.

(a) sigma_e: `idiosyncratic_vol_from_beta_regression` und `window_sigma_f_sigma_e` nehmen den Median
ueber **alle** 1.138 Spalten ohne Lebend-Maske. In W1 waren 550 Symbole nie lebend, in W2 402
(AR(1)-sigma = 0 im Artefakt), und sie gehen mit SD 0 in den Median ein. Ergebnis: sigma_e_used
0,057/0,073 und Gesamt-Vol 0,063/0,094. Der Median der lebend-restringierten Vol (AR(1)-sigma im
Artefakt) liegt dagegen bei 0,164/0,126; in W1 waere die Median-Alt-Vol damit absurd kleiner als die
BTC-Vol. Wirkung:
- Unter der alten Konvention ist der Fehler milde. Mit sigma_e 0,105/0,126 (W2) steigen die
  FM-Null-Mittel in W2 stress auf 0,0048-0,0058, mit 0,143 (W1) auf 0,0053-0,0059.
- Unter konsistenter Marktspalte ist er bedeutungslos, denn das Modell ist dann skaleninvariant. Bei
  sigma_e 0,073 und 0,105 kommen identische Null-Mittel heraus.
- sigma_e verschaerft aber D1: Mit korrektem sigma_e laege die Sim-BTC-SD bei etwa 0,12 statt
  real 0,055.

(b) Beta-Maske: `beta_characteristic` prueft `min_weeks` nur fuer die Marktspalte. 8-26 Wochen alte
Symbole erhalten deshalb ein endliches, durch die Null-Auffuellung gedaempftes 26-Wochen-Beta. Beleg:
Masken-K == Lebend-K in jeder der 105 Wochen beider Fenster; das W2-PIT-Beta-Quantil q05 liegt bei
0,079. DEC-81 (c) "derselbe Querschnitt" gilt damit nur der Zahl nach. Der reale Ziel-Anteil enthaelt
gedaempfte Betas fuer etwa 10-15 % des Querschnitts; die Richtung ist unbestimmt. Ausserdem wird die
Zusage in `ic.py` (Modul-Docstring) "a symbol-week without a FULL N-week trailing history gets NaN" auf
dem realen Panel nicht eingehalten. Das betrifft auch den kuenftigen Lauf-Modus, weil die Coverage dort
irrefuehrend ausgewiesen wuerde.

### Geprueft, kein Defekt bzw. nicht ergebnisrelevant
- **Stress-Definition** entspricht DEC-78 E1 und Nachtrag: rho_f x2 UND beobachteter Anteil x2, eigene
  Bisektion (`beta_control_method_study` Z. 1603-1622). "2x" ist auf der Skala des beobachteten
  Schaetzers gemeint; der wahre Anteil steigt dabei nur um x1,54. Das ist im Sinne des Nachtrags korrekt.
- **Gegenproben** 6/6 bestanden: z 0,53-1,67 <= 3, Power-Auslastung 0,54-0,76 < 1. Alle Suchen
  konvergiert (7-9 Iterationen, 400 Replikate, gemeinsame Zufallszahlen, unabhaengiger Seed
  1.000.056). Die Gegenprobe ist allerdings blind fuer D1.
- **Querschnittsmaske DEC-81 (c)** ist formal korrekt verdrahtet (`calibration_mask = alive & finite
  beta & finite returns`, mask_k_median 419/589), Einschraenkung siehe D2 (b).
- **Seed 53** ist registriert (DEC-74 (c), DEC-75 (2)) und wird in allen Zellen gemeinsam genutzt; das
  ist Design. **n_reps** 300 fuer das Raster (DEC-81 E1 (d)) und 1.000 fuer den Gewinner (DEC-78 E2) sind
  vorab festgelegt; es gab keinen Gewinner, deshalb keinen Lauf mit 1.000 Replikaten.
- Die Simulation hat keinen Vorlauf vor dem Fenster. Fuer die ersten 8/13/26 Wochen fehlen deshalb die
  Betas (Coverage 0,54-0,89, im realen Lauf ~1). Das betrifft nur Decke und MC-Praezision, nicht den
  Erwartungswert des Null-Mittels.
- rho_f ist nicht Kendall-korrigiert (etwa -0,02). Das ist milde und durch keine DEC vorgeschrieben,
  also nur eine Anmerkung.

## 5. Urteil

**VETO.** Begruendung:
1. Die vorab fixierte Konsequenz (DEC-77 E1 (c)) ist drastisch (Klasse W nicht testbar, keine
   Registrierung). Sie darf nur aus einer Null folgen, die gegen ihre eigenen Messziele kalibriert ist.
2. Die v5c-Null verfehlt zwei dieser Ziele messbar (BTC-SD x1,3/x1,7, rho_f x0,58/x0,36), und keine
   Gegenprobe deckt das ab.
3. Das ist ergebnisbestimmend: Mit konsistenter Marktspalte und sonst unveraendertem Aufbau bestehen
   vier Methoden die volle Regel in beiden Fenstern.
4. Die Reparatur ist kein Torpfosten-Verschieben, wenn PASS-Regel, Schwellen, Stress-Multiplikatoren,
   Seed, n_reps, "schlechteste von 7" und "beide Fenster" unveraendert bleiben. Das Konsistenzkriterium
   muss vor dem Lauf feststehen, und das Ergebnis muss in beide Richtungen gelten. So ist die Akte auch
   bei DEC-78 (Faktoranteil x25 ueberzeichnet) und DEC-81 (stochastische Gegenprobe) verfahren.

Bedingungen fuer die Aufhebung des VETO (neue DEC vor jedem Lauf):
- (i) Konstruktion der Sim-Marktspalte mit Konsistenzkriterium: Die Sim-Spalte reproduziert die
  gemessene BTC-SD und rho_f. Entweder BTC := f, oder BTC = Faktor + gemessene BTC-Eigenkomponente,
  geschaetzt in der Siegel-zulaessigen Kategorie (gleichwoechige Rendite-gegen-Rendite-Relation, z. B.
  R^2 von BTC auf das lebend-gemittelte Querschnittsmittel). Welche Variante gilt, wird vorab
  begruendet entschieden, nicht nach dem Ergebnis.
- (ii) Gegenprobe erweitert um SD und Lag-1-Autokorrelation der Sim-Marktspalte, laut.
- (iii) sigma_e nur ueber lebende Symbol-Wochen; NaN statt 0 fuer nicht handelnde Wochen in der
  Beta-/Anteilsmessung (bzw. `min_weeks` je Symbol). Ziel-Anteil neu messen.
- (iv) PASS-Regel und alle Konstanten unveraendert; Vorlauf v5d; Ergebnis bindend, auch wenn es erneut
  "keine Methode" lautet.

Ausdruecklich **nicht** aus diesem VETO folgt:
- keine Registrierung von fm_neutral_* oder einer anderen Methode auf Basis meiner Schranken-Rechnung;
- keine Teilkohorte (Punkt 3);
- keine Aenderung von Schwellen, Stress-Multiplikatoren, Seed oder Replikatzahl;
- kein Oeffnen versiegelter Dateien;
- kein Verdikt ueber H-28..H-30.

## 6. Vorschlag Gate-Log-Eintrag (ASCII, <= 15 Zeilen)

```
GL-0xx . 2026-10-12 . WP-13a v5c Beta-Kontroll-Methodenvergleich (A3/F-XSEC1, H-28..H-30) . VETO (Gate-Auditor) - KEIN GL-012
Gegenstand: state/runs/wp13a_20261012/wp13a_prelaunch.json sha256 fe3b1650...c553b, Code 2f8c6a0, Seed 53, n_reps 300.
Regel: DEC-77 E1 (b)/(c), DEC-78 E1: |Null-Mittel| <= 0,25*Boden/sqrt(W_geurt.) UND Decke <= 1,5*Rausch-Decke, measured UND stress, schlechteste von 7, beide Fenster.
Zahlen: Grenzen W1 0,00168/0,01378, W2 0,00147/0,01167; 0 von 6 Methoden bestehen; FM stress W2 0,00273-0,00300 (+2,2..+2,9 MC-SE), W1 0,00183-0,00208 (+0,2..+0,7).
Pruefung: Regel, Arithmetik, Gegenproben (z <= 1,67), Maske, Seed, n_reps korrekt; Ergebnis robust gegen MC-Fehler (W2).
Defekt: Sim-"BTC-Spalte" = beliebige Sim-Spalte (in keiner DEC registriert): SD 0,088/0,092 statt gemessen 0,067/0,055,
  Autokorrelation x0,58/x0,36 von rho_f - verletzt DEC-77 (a); von keiner Gegenprobe erfasst.
Relevanz: gleicher Aufbau mit Sim-Marktspalte = Faktor -> fm_neutral_8w/13w/26w und double_sort_13w bestehen alle Kriterien in W1 und W2.
Nebenbefund: Null-Renditen fuer nicht handelnde Wochen (panel_load) -> sigma_e ueber 550/402 nie lebende Symbole verzerrt, 26w-Beta junger Symbole gedaempft.
Urteil: VETO gegen "Klasse W auf diesem Panel nicht testbar" auf Basis v5c (DEC-77: "ob die Null realistisch kalibriert ist").
Konsequenz: DEC vor jedem Lauf - Marktspalte mit vorab fixiertem Konsistenzkriterium (BTC-SD, rho_f), Gegenprobe darauf erweitert,
  sigma_e/Beta nur ueber lebende Wochen; PASS-Regel, Stress x2, Seed 53, n_reps unveraendert; Vorlauf v5d, Ergebnis bindend in beide Richtungen.
Nicht folgt: keine Registrierung (auch nicht FM aus der Schranken-Rechnung), keine Teilkohorte (DEC-77 (c), K=7), keine Schwellen-/Stress-Aenderung,
  kein Oeffnen versiegelter Dateien, kein Verdikt ueber H-28..H-30.
```

## Anhang: Reproduktion

Alle Laeufe sind reine Simulation mit `python3 -B -I` (kein Bytecode ins Repo), aus
`state/runs/wp13a_20261012` heraus:
- `scripts/recompute.py wp13a_prelaunch.json`: Grenzen, Tabellen, MC-SE.
- `scripts/variants.py wp13a_prelaunch.json`: Null-Mittel je Variante.
- `scripts/sens_sigma_e.py wp13a_prelaunch.json W2 0.07281 fm_neutral_8w 300`: Kontrolle, alte Konvention.
- `scripts/sens_sigma_e.py ... W2 0.105,0.126 fm_neutral_8w,fm_neutral_13w,fm_neutral_26w 300`
  bzw. `... W1 0.05695,0.143 ...`: Sensitivitaet D2 (a).
- `scripts/sens_clean_btc.py ... W2 0.07281,0.105 none,fm_neutral_8w,fm_neutral_13w,fm_neutral_26w 300 stress`:
  Skaleninvarianz unter konsistenter Marktspalte.
- `scripts/full_rule_clean.py ... {W1,W2} clean fm_neutral_8w,fm_neutral_13w,fm_neutral_26w,double_sort_13w 300`:
  volle Regel unter D1-Korrektur (Logs `clean_W1.log`, `clean_W2.log`).

Laufzeit etwa 25 min auf 4 CPUs. Die synthetische Maske (`alive[t,:K_t]`) ersetzt die reale PIT-Maske.
Mit unveraenderter Konvention reproduziert sie das Artefakt qualitativ (FAIL), deshalb ist der A/B-Kontrast
auf D1 zurueckzufuehren.
