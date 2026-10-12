# Gate-Audit: Positivkontrolle der Drittfassung H-28..H-30 und Feststellung zur Kohorte F-XSEC1 (2026-10-12)

Rolle: adversarischer Gate-Auditor mit Veto. Nur gelesen, nichts im Repo geaendert, nichts committet.
Siegel: Keine `*_L_window_sealed.json`, keine `weekly_ic_series.csv`, keine `ic_series_*_UNION_REAL.csv` geoeffnet oder
gegrept. Keine reale Charakteristik-Folgerendite-Rechnung, kein `--run`. Alle Zahlen stammen aus v5e
(`wp13a_prelaunch.json`), aus dem PC-Artefakt (synthetisch) oder aus eigener Simulation (synthetisch).

## URTEIL

**BESTAETIGT: Feststellung GL-012 fuer alle sieben Varianten der Drittfassung, also fuer die ganze Kohorte F-XSEC1.
Kein Lauf.** Kein VETO. Fuer den Wortlaut gelten fuenf Auflagen (Abschnitt 5). Eine Viertfassung mit DEC-52-Zweig
empfehle ich nicht. Sie waere eine nachtraegliche Lockerung einer vorab fixierten Zuordnungsregel. Unter der bindenden
stress-Kalibrierung erreicht sie zudem selbst nur MDE80 0,034 > 0,03.

Gepruefte Hashes, alle gleich der Akte:
- v5e JSON `94d65559...b3b2`;
- YAML `bd948f34...c299`;
- PC-JSON `a700aa66...aac6`;
- PC-MD `68792f48...cec0`.

---

## 1. Ursachenanalyse (Pruefauftrag 1)

### 1.1 Was der registrierte Test verlangt (Code `849ec4a`)

`run.se_of_mean_ic` setzt `SE = max(e_floor, SD(IC_t; ddof=1)) / sqrt(W_judged)`. Dabei ist `e_floor` =
E_t[1/sqrt(K_t-1)] ohne c_rho: W1 0,04858, W2 0,04192, W_judged 52/51.

`gates._window_pass` verlangt je Fenster:
- (a) `|IC| >= 2,4865*SE`;
- (b) die MBB-CI-Grenze (Block 4, 1.000 Ziehungen, Niveau 0,9936) jenseits von 0;
- (c) `|IC| >= IC_min_capped`;
- (d) die Beta-Kontrolle (Vorzeichen, `|IC_res| >= IC_min`, jenseits q_binding).

Das entspricht DEC-75 (1).

### 1.2 Wo DEC-88 abweicht

DEC-88 und Vorlage F rechnen `P_ICmin = Phi(0,03*2,4865/IC_min - 2,4865)`. Das unterstellt als Stichproben-SD des
Mittel-IC `IC_min/2,4865 = Boden*c_rho/sqrt(W)` (W1 mom1 0,0079). Dieselbe Groesse steckt im Registry-Text der
Drittfassung (Formelblock "Mechanische Zuordnung").

Die Herkunft liegt weiter zurueck:
- Die PRD-5.3-Power-Zeile rechnet `SE = SD_null/sqrt(52)`.
- DEC-75 (1) hat die Test-SE auf `max(Boden, SD(IC_t))` umgestellt. Anlass war Review v2 B-1: Faktor-SD ~1,8x Boden.
- Die Power-Zeile wurde danach nie nachgezogen.
- Review v3 hat die Arithmetik von Vorlage F reproduziert, die Herleitung aber nicht ("effektive Schwellen <= 0,0224").

### 1.3 Nachrechnung aus v5e (IC_prior 0,03)

Quellen:
- `beta_control_method_study.calibrations.<cal>.methods.none.variants.<v>.factor_sd`;
- `mean_ic_draws_sd`;
- `noise_floor_and_threshold`;
- `frozen_null_constants`;
- `beta_control_recommended_high_rep`.

Skript: `scratchpad/power_v5e.py`.

Formeln:
- P_mag = Phi(0,03/SE - 2,4865);
- MDE_mag = 3,3281*SE;
- P_ICmin mit der echten Stichproben-SD des Mittel-IC = Phi((0,03 - IC_min)/sd_mean);
- P_beta wie DEC-88.

| Variante | Fenster | Kal. | SD(IC_t) | SE | P_mag | MDE_mag | P_ICmin | P_beta | P_voll | MDE80 |
|---|---|---|---|---|---|---|---|---|---|---|
| mom1 | W1 | measured | 0,0901 | 0,01250 | **0,466** | **0,0416** | 0,794 | 0,832 | 0,466 | 0,0416 |
| mom1 | W1 | stress | 0,1302 | 0,01806 | **0,205** | **0,0601** | 0,714 | 0,832 | 0,205 | 0,0601 |
| mom1 | W2 | measured | 0,0610 | 0,00854 | 0,848 | 0,0284 | 0,936 | 0,976 | 0,848 | 0,0284 |
| mom1 | W2 | stress | 0,0817 | 0,01144 | 0,554 | 0,0381 | 0,872 | 0,976 | 0,554 | 0,0381 |
| rev_gap | W1 | measured | 0,0889 | 0,01233 | **0,479** | **0,0410** | 0,832 | 0,949 | 0,479 | 0,0410 |
| rev_gap | W1 | stress | 0,1286 | 0,01783 | **0,211** | **0,0593** | 0,747 | 0,949 | 0,211 | 0,0593 |
| rev_gap | W2 | measured | 0,0612 | 0,00856 | 0,845 | 0,0285 | 0,952 | 0,986 | 0,845 | 0,0285 |
| rev_gap | W2 | stress | 0,0817 | 0,01144 | 0,554 | 0,0381 | 0,886 | 0,986 | 0,554 | 0,0381 |
| mom2 | W1 | measured / stress | 0,0903 / 0,1323 | | 0,464 / 0,197 | | | 0,597 | 0,464 / 0,197 | 0,0417 / 0,0611 |
| mom4 | W1 | measured / stress | 0,0920 / 0,1355 | | 0,446 / 0,187 | | | 0,380 | 0,380 / 0,187 | 0,0425 / 0,0626 |

DEC-91 ist damit exakt reproduziert:
- W1: 0,47 / 0,21, MDE80 0,041 / 0,060;
- W2: 0,85 / 0,55, MDE80 0,028 / 0,038;
- mom1 und rev_gap liegen praktisch gleich.

DEC-88 reproduziert sich mit der alten Formel ebenfalls (mom1 W1 P_ICmin 0,904, P_beta 0,832, MDE80 0,0291). Die
gemeinsame C.10-Power (Produkt der Fenster, Obergrenze) liegt fuer mom1 bei 0,40 (measured) / 0,11 (stress), fuer
rev_gap bei 0,41 / 0,12.

**Zusatz zu DEC-91: ein zweiter Fehler mit derselben Wurzel.** Auch die IC_min-Bedingung (c) war mit der Boden-SE als
Stichproben-SD gerechnet:
- W1 mom1 echt 0,79 (measured) / 0,71 (stress) statt 0,90;
- MDE 0,030 / 0,035.

Die Beta-Bedingung (d) ist korrekt gerechnet. Ihre sd stammt aus der fm8-Null selbst.

**Robustheit.** MDE80 <= 0,03 in W1 verlangte SD(IC_t) <= 0,0650 (W2 <= 0,0644). Schon die Null ohne jede
Faktor-Autokorrelation (`zero`, rho_f 0, gemessener Faktoranteil) hat in W1 0,0906. Das Ergebnis haengt also nicht an
rho_f, sondern am gemessenen Faktoranteil.

### 1.4 Ist `factor_sd` (methods.none) die richtige Groesse fuer SD(IC_t)?

Ja, mit drei kleinen Vorbehalten. Keiner aendert das Ergebnis.

1. **Statistik.** Bedingungen (a)/(b) laufen auf der ROHEN Wochen-IC-Serie. `methods.none` ist genau diese Serie
   unter der kalibrierten Faktor-Null (Marktspalte := Faktor, beta_sd per Bisektion auf den gemessenen Faktoranteil).
   Die fm8-SD (0,048..0,051) gehoert zur residualisierten Serie. Sie geht im registrierten Gate nicht in die SE ein.
2. **Schaetzer.** `factor_sd` ist die gepoolte SD ueber 300 Replikate x 52 Wochen (n_ic_pooled 15.600). Sie enthaelt
   die Streuung der Replikat-Mittel. Die Within-SD ist ~1 % kleiner: sqrt(0,0901^2 - 0,0126^2) = 0,0892. Die
   Stichproben-SD mit ddof=1 ist nach Jensen leicht kleiner. Effekt < 2 % auf die SE.
3. **Unabhaengigkeit.** `mean_ic_draws_sd` ist gleich `factor_sd/sqrt(W)` (0,01259 gegen 0,01250). Die IC_t sind
   unter der Null praktisch unabhaengig, die naive SE ist also die richtige Stichproben-SE.
4. **Null gegen Alternative.** Ein Signal von IC 0,03 aendert SD(IC_t) vernachlaessigbar. Die PC mit IC 0,06 zeigt
   dieselbe Groessenordnung.
5. **Richtung des Restfehlers.** Die Ein-Faktor-Null bildet nur den BTC-Beta-Anteil ab. Jede weitere gemeinsame
   Komponente (Sektoren, Narrative, Groesse) erhoeht die reale SD(IC_t). Die PC-Welt mit 8 Sektoren hat in W1
   SD(IC_t) 0,093..0,154. `measured` ist damit eher eine Untergrenze. Ohne Siegelbruch nicht pruefbar und
   ausdruecklich nicht geprueft.

### 1.5 CI-Bedingung (b)

Monte Carlo mit synthetischen IC-Serien (iid normal und t4, je 1.500 Serien, MBB wie im Code; Skript
`scratchpad/mc_ci.py`):

| Fenster | Kalibrierung | Verteilung | P_mag | P_CI | P_mag UND P_CI |
|---|---|---|---|---|---|
| W1 | measured | normal | 0,46 | 0,51 | 0,43 |
| W1 | measured | t4 | 0,50 | 0,57 | 0,48 |
| W1 | stress | normal | 0,23 | 0,29 | 0,21 |
| W1 | stress | t4 | 0,25 | 0,31 | 0,22 |
| W2 | measured | normal | 0,85 | 0,86 | 0,82 |
| W2 | measured | t4 | 0,85 | 0,85 | 0,82 |
| W2 | stress | normal | 0,56 | 0,62 | 0,53 |
| W2 | stress | t4 | 0,60 | 0,66 | 0,57 |

Die CI-Bedingung ist praktisch dieselbe Bedingung wie (a), nur geringfuegig weicher (Perzentil-MBB). Sie rettet
nichts.

### 1.6 Ist die Positivkontrolle konsistent, oder zeigt sie einen Code-Defekt?

Sie ist konsistent. Ich finde keinen Defekt in der Gate-Kette.
- **Injektion wirkt wie konstruiert.** Die Differenz positiv minus negativ (gleiches Basis-Panel) betraegt in allen
  12 Seed-Fenster-Paaren +0,053..0,056 (mom1) bzw. -0,051..-0,055 (rev_gap). Erwartet sind ~0,054..0,056
  (Spearman-Daempfung, -c^2-Term der Doppelinjektion).
- **SE-Pfad aktiv.** Alle PC-SEs liegen ueber Boden/sqrt(W). SD(IC_t) betraegt in W1 0,093..0,154, in W2
  0,070..0,083. Die Faktor-plus-Sektor-Welt verhaelt sich wie in 1.4 beschrieben.
- **Ausfallbild passt zu den Bedingungen.**
  - Seed 55 W1: |IC| 0,0479 < 2,4865*0,0214 = 0,0532 (a).
  - Seed 53 W1 faellt an (b) mit CI -0,00046 UND ebenfalls an (a): 0,0418 < 2,4865*0,01902 = 0,0473. DEC-91
    nennt nur (b), das ist eine kleine Praezisierung.
  - Die Negativkontrolle liefert 0/3 PASS.
- **Erwartete Trefferquote.** Bei SD 0,135 und realisiertem W1-IC 0,045..0,056 liegt die Einzel-Power der
  Rohbedingungen bei 0,46..0,64 (MC), bei nominal 0,06 bei 0,73. Die ~0,8 aus DEC-91 gelten nur mit dem
  mechanischen Momentum der stress-Welt (+0,011). P(3/3) liegt damit grob bei 0,1..0,5. Beobachtet wurden mom1 1/3
  und rev_gap 3/3, beides plausibel.
- **Nebenbefund N-1 (nicht urteilsrelevant).** Das mom1-Basisniveau der Negativkontrolle liegt unter dem
  stress-Null-Mittel von `none`: W1 -0,010 gegen +0,011 (z -2,0), W2 -0,003 gegen +0,006 (z -1,4). Bei rev_gap gibt
  es keine Abweichung. Das erklaert einen Teil des mom1-Ausfalls und macht die PC schwerer, nicht leichter. Es
  besteht also kein Falsch-PASS-Risiko. Fuer GL-012 ist das ohne Belang, weil GL-012 allein auf v5e-Zahlen ruht.
  Nur pruefen, falls je wieder eine PC dieser Welt laeuft.
- **Entscheidend.** Die GL-012-Feststellung haengt NICHT am PC-Ergebnis. Die PC hat den Fehler nur sichtbar
  gemacht. Haette sie zufaellig bestanden, waere ein Test mit gemeinsamer Power ~0,4 / ~0,1 gelaufen. Ein DROP haette
  dann faelschlich "Klasse W erschoepft" ausgeloest (C.13).

---

## 2. Kalibrierung fuer die Power-Zuordnung (Pruefauftrag 2)

**In die Zuordnung gehoert `stress`.** Strenger formuliert: Die Bedingung muss unter beiden Kalibrierungen halten. Das
laeuft auf dasselbe hinaus. Begruendung:
- (a) Vorlage F und DEC-88 nehmen q und sd fuer P_beta ausdruecklich aus der fm8-stress-Null. Eine Mischung aus
  stress fuer (d) und measured fuer (a)-(c) waere inkonsistent.
- (b) Die Programmkonvention verlangt fuer vorab bindende Feasibility- und Methodenkriterien "bei kalibriertem UND
  Stress-rho" (DEC-77 E1 (b), DEC-85 (iv)). Bindende Konstanten nehmen die strengere Kalibrierung (DEC-87 (A), (E)).
- (c) Die PC-Welt ist stress (DEC-89 E2).
- (d) `measured` ist nach 1.4 (5) eher eine Untergrenze der realen SD(IC_t), also kein konservativer Mittelwert.

**Aendert die Wahl das Ergebnis?**
- **Fuer DEC-87 (F): nein.** W1 MDE80 liegt fuer mom1 und rev_gap auch unter measured ueber 0,03 (0,0416 / 0,0410).
  Unter measured besteht nur W2 (0,028); unter stress faellt auch W2 (0,038).
- **Fuer einen hypothetischen DEC-52-Zweig: ja.** Gepoolte SE (103 Wochen), alpha 0,01, z 3,1680:
  - measured: SE 0,0076, MDE80 0,024, waere feasible;
  - stress: SE 0,0107, MDE80 **0,034 > 0,03**, waere selbst GL-012 nach DEC-51 (2).
  Hinzu kommen die Fenster-Screens nach DEC-52 (ii). Ein DEC-52-Weg traegt also nur, wenn man ZUSAETZLICH von stress
  auf measured wechselt. Das ist der Kern der Empfehlung in Abschnitt 3.

---

## 3. DEC-52-Frage (Pruefauftrag 3)

### Lesart A - Viertfassung mit DEC-52-Zweig ist zulaessig, ggf. geboten

Fundstellen:
- PRD 3.5: DEC-52 BESCHLOSSEN, Retro-Check veroeffentlicht.
- Verfassung: "C.10 ..., ausser DEC-52 greift"; Vier-Zahlen-Tabelle "Ein-Fenster-DROP bei Power 0,5 verwirft 3 von
  4 echten Effekten -> DEC-52".
- PRD 5.3: "ergibt sie Power < 0,60, ist der DEC-52-Zweig zulaessig - die Entscheidung faellt an dieser Stelle, nie
  nach dem Lauf".
- DEC-51 (2): "... oder braucht ein anderes Design".
- DEC-75 (8): DEC-52 fuer rev_gap vorab zugelassen.
- Vorlage F: Ausnahmeklausel "ausser P_voll < 0,60 und der DEC-52-Zweig ist gebaut und getestet".
- Registry: "Aenderungen erfolgen nur als neuer Eintrag".
- Praezedenz: Erst- und Zweitfassung wurden nach outcome-freien Reviews zurueckgezogen und neu gefasst (DEC-74,
  DEC-75).

Kern des Arguments:
- Die Regel DEC-52 stand vor der ersten Registrierung (2026-09-02 gegen DEC-73), sie ist nicht kandidatenspezifisch.
- Die Power-Zeile der Drittfassung war sachlich falsch, also wurde "die Stelle" nie korrekt erreicht.
- Es ist keine reale IC gesehen worden.

### Lesart B - Feststellung GL-012 der ganzen Kohorte (strengste vertretbare Lesart)

Fundstellen:
- **DEC-87 (F)**: Zuordnung "mechanisch ..., ohne Ermessen". MDE80 > IC_prior -> GL-012. "DEC-52-Zweig ist nicht
  gebaut, wird nicht genutzt".
- Registry-Text der Drittfassung: Regelblock und Kill-Tabelle "MDE80 > IC_prior -> GL-012 der Variante".
- **PRD 3.5**: "vorab fixierte Zuordnungsregel, die vor der Registrierung ausgewertet wird".
- Zustandsmaschine: "FEASIBILITY-BEFUND (binaer, Konsequenz vorab)"; C.12.
- Feasibility-Bindung im Programm: DEC-77 E1 (c) "kein Zurueckskalieren"; DEC-85 (v) "Bindung in beide Richtungen",
  "keine Teilkohorte"; DEC-87 v5e-Bindung "Kein Wechsel aus anderen Gruenden".
- DEC-87-Kopf: "keine lockert eine bindende Regel". DEC-75: Neufassungen "alle verschaerfend".
- **DEC-52 Sequenz-Zwang**: "muss VOR der Registrierung des ersten Kandidaten stehen, der sie braucht - sonst waere sie
  eine Torpfosten-Verschiebung".
- GL-012-Praezedenz (2.0, H-07): "Der DROP wird angenommen, nicht umgangen ... Kein H-07-Retten". Das neue Design
  wurde H-08 als NEUE, separat vorregistrierte Hypothese.
- Null-Zensus-Klausel DEC-58 E2, sinngemaess: Ein outcome-freier Erreichbarkeits-Befund darf keinen Kandidaten
  befoerdern. Zulaessig sind ein D-Eintrag oder "nicht ausgeschlossen". Was aus ihm hervorgeht, braucht eine eigene
  Hypothese mit eigenem K.

### Bewertung

1. **Geboten ist DEC-52 nie.** DEC-52 (i) und PRD 5.3 sprechen von "anwendbar" bzw. "zulaessig". Die strengere
   Fehlerrate zu waehlen ist immer erlaubt. Die Drittfassung hat das ausdruecklich getan (DEC-87 (B)/(F)).
2. **Wird die registrierte Regel korrekt angewandt, folgt GL-012.** Der Defekt liegt in der Auswertung (Zahlen), nicht
   in der Regel. Eine korrigierte Auswertung einer registrierten Regel ist Anwendung, keine Aenderung. Rueckzug plus
   Viertfassung (Option C, analog DEC-74/75) wuerde die registrierte Konsequenz umgehen. Deshalb lehne ich auch sie ab.
3. **Die Ausnahme ist bewusst gestrichen worden.** DEC-87 (F) hat sie VOR den v5e-Zahlen gestrichen, in Kenntnis
   davon, dass schwache Varianten GL-012 werden (Vorlage-F-Prognose: mom4 GL-012, mom2 offen). mom2/mom4 wurden genau
   so gesperrt. DEC-52 jetzt nur fuer mom1/rev_gap zu nutzen, waere kandidatenspezifisch. DEC-52 fuer alle zu nutzen,
   oeffnete mom2/mom4 nachtraeglich wieder.
4. **Es waere eine Lockerung.** Nach PRD 3.5 verdoppelt DEC-52 die gemeinsame Falsch-Positiv-Rate (0,25 % -> 0,5 %).
   Ausgeloest wuerde der Wechsel durch die Feststellung, dass der strenge Test nicht feasible ist. Genau das verbietet
   "kein Torpfosten-Verschieben in KEINE Richtung" auf Feasibility-Ebene. Dass keine reale IC gesehen wurde, macht es
   zulaessig, ueberhaupt neu zu entwerfen (Lesart A hat hier recht). Es macht aber den Bruch einer vorab fixierten
   Zuordnungsregel nicht zulaessig.
5. **Materiell traegt Lesart A nicht.** Unter der bindenden stress-Kalibrierung hat auch der gepoolte DEC-52-Test
   MDE80 0,034 > 0,03, er waere wieder GL-012 nach DEC-51 (2). Er traegt nur mit einem zweiten nachtraeglichen
   Wechsel auf measured. Unter measured ist DEC-52 (i) aber nur in W1 erfuellt (W2 0,85 > 0,60), unter stress in
   beiden. Das ist eine Zange: Wo DEC-52 eindeutig anwendbar ist, rettet er nicht; wo er retten wuerde, ist er nicht
   eindeutig anwendbar.
6. **Der Zweig ist nicht gebaut, und sein Bau oeffnet neue Freiheitsgrade.** Offen waeren: Screen-Schwelle (ii)
   (IC_min oder 2,4865*SE), Magnituden-Band [0,5x; 2,0x], gepoolte Fassung der Beta-Kontrolle, "fenster-geclusterter"
   Bootstrap bei zwei Fenstern. Jeder dieser Punkte wuerde mit Kenntnis der v5e-Power-Landschaft entschieden.

**Empfehlung: Lesart B.** Das ist die Feststellung GL-012 fuer alle sieben Varianten der Drittfassung. Es gibt keine
Viertfassung, keinen Rueckzug zur Neufassung und keinen DEC-52-Zweig fuer F-XSEC1 auf W1/W2.

---

## 4. Wortlaut der Feststellung und was NICHT folgt (Pruefauftrag 4)

**"Kohorte F-XSEC1 auf diesem Panel bei Prior 0,03 nicht testbar" ist zu weit.** Die Infeasibility ist eine
Eigenschaft von (Design x Panel x Fenster x Prior), nicht des Panels allein. Vorschlag:

> "Die Drittfassung H-28..H-30 (Kohorte F-XSEC1) ist in ihrem registrierten Design (roher Wochen-Rank-IC je Fenster
> mit SE = max(Boden, SD(IC_t))/sqrt(W), C.10 hart, W1/W2 auf dem Union-Panel) bei IC_prior 0,03 nicht testbar:
> MDE80 > 0,03 in W1 fuer jede gerechnete Variante (DEC-51 (2), DEC-87 (F)), H-30 zusaetzlich Feasibility/strukturell.
> GL-012, Feasibility-DROP vor dem Lauf."

### Was ausdruecklich NICHT folgt

1. **Kein Verdikt ueber Momentum, Lag-2-Reversal oder die Vol-Anomalie.** Weder widerlegt noch bestaetigt. Der
   DROP-Zweig der registrierten Entscheidungsrelevanz ("Klasse W ... erschoepft", "D.7 auf breiter Basis
   bestaetigt") greift NICHT. Nach C.13 waere ein Null-Befund dieser Maschinerie uninformativ gewesen.
2. **K.** K = 7 bleibt Nenner von F-XSEC1. Alle sieben Varianten gehen mit p = 1 ein (DEC-87 (J)), am Wellenschluss
   auch in F-WEEK/BY. Ein spaeteres anderes Design ist eine neue Hypothese mit eigenem K. Die sieben werden nicht
   "frei" oder recycelt, der Alpha-Slot gilt als verbraucht.
3. **Siegel.** Das L-Siegel (`wp13a_prelaunch_L_window_sealed.json`, auch v5c/v5d) und jede reale IC-Serie bleiben
   geschlossen. Schritt 3 der Registry ("L-Siegel erst nach dem GL-Eintrag") setzt einen Lauf voraus. GL-012 vor dem
   Lauf ist kein solcher Eintrag. Oeffnen wuerde jede kuenftige A3-Registrierung auf diesen Daten kontaminieren. Eine
   Oeffnung nur per eigener DEC.
4. **YAML.** `state/registered/h28_h30_v3.yaml` bleibt bitgleich als Akte (sha256-gepinnt). Kein Statusfeld wird
   nachgetragen. Der Abschluss kommt append-only in die Registry ("Abschluss der Drittfassung ohne Lauf: GL-012,
   GL-032") und als DEC-92. `--run` mit `bd948f34...c299` entfaellt endgueltig (PC rc 3, Registry: "Nur bei rc 0
   folgt Schritt 2").
5. **Keine Rettungspfade.** Kein PC-Neulauf, auch nicht mit anderen Seeds (Registry: "Andere Seeds als 53/54/55
   ergeben nie BESTANDEN"). Kein Lauf nur auf W2 oder nur fuer rev_gap (Teilkohorte, DEC-85). Keine Anhebung des
   Priors 0,03. Kein Wechsel auf measured.
6. **Kein Code-Defekt.** Code und v5e-Konstanten bleiben gueltige Artefakte. Die DEC-88-Power-Tabelle und der
   Formelblock im Registry-Text sind durch die korrigierte Tabelle (1.3) ueberholt. Das wird append-only vermerkt,
   ohne Aenderung am alten Text.
7. **Neues Design nur als neue Hypothese.** Ein anderes Design, etwa der fm8-neutralisierte IC als
   Primaerstatistik, bei dem SD(IC_t) ~0,05 ist und die Beta-Bedingung bei MDE80 0,029 knapp unter 0,03 liegt,
   waere nach DEC-51 (2), DEC-58 E2 und der Praezedenz H-07/H-08 eine NEUE, separat vorregistrierte Hypothese mit
   eigenem K, eigener Herleitung, eigenem Review und eigener PC. Es waere keine Fassung von H-28/H-29. Ob es so eine
   Hypothese gibt, entscheidet dieses Audit nicht. Ihre Power waere ebenfalls knapp.

---

## 5. Urteil und Auflagen (Pruefauftrag 5)

**BESTAETIGT (Feststellung GL-012, ganze Kohorte, kein Lauf).** Auflagen fuer DEC-92 und GL-032:
1. Wortlaut wie in Abschnitt 4: "im registrierten Design", nicht "auf diesem Panel".
2. Ursache vollstaendig nennen:
   - Boden-SE statt registrierter SE in (a)/(b) und auch in (c) (IC_min-Bedingung, W1 mom1 0,79/0,71);
   - Seed 53 faellt an (a) UND (b).
3. Kalibrierung `stress` als bindend benennen (Konvention DEC-77 E1 (b), DEC-87 (A), Vorlage F) und festhalten, dass
   das Ergebnis unter measured identisch ist.
4. DEC-52: festgestellt "anwendbar (Power < 0,60)", nach DEC-87 (F) "nicht genutzt". Unter stress wuerde auch der
   gepoolte Zweig MDE80 0,034 > 0,03 liefern. Keine Viertfassung.
5. Die NICHT-Folgen 1-6 aus Abschnitt 4 explizit aufnehmen, insbesondere Siegel bleibt zu, YAML bitgleich, kein
   PC-Neulauf.

Lehre fuer das Kompendium (Vorschlag, nicht Teil des Urteils): Die Power-Zeile wird mit der SE des registrierten
Tests gerechnet. Ist diese datenabhaengig, mit der SD der getesteten Statistik unter der kalibrierten Null. Ein Review
muss die Herleitung nachrechnen, nicht nur die Arithmetik.

### Vorschlag GL-032 (Deutsch, ASCII, 15 Zeilen)

```
## GL-032 - 2026-10-12 - H-28/H-29/H-30 Drittfassung (F-XSEC1, A3, YAML bd948f34...c299) - GL-012 vor dem Lauf, kein Lauf
- Anlass: Positivkontrolle NICHT BESTANDEN (rc 3, runs/wp13_positivkontrolle_20261012, result b3daeea8...041d):
  mom1 PASS 1/3 Seeds, rev_gap 3/3, Negativkontrolle 0/3. Gate-Kette ohne Defekt (Injektion pos-neg +0,053..0,056).
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
```
