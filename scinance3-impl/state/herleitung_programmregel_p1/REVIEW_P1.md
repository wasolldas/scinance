# Review Programmregel P-1 (adversarisch, zweiter Gutachter)

> Stand 2026-10-13. Gegenstand: `state/herleitung_programmregel_p1/ENTWURF.md` (675 Zeilen) mit `rechnung_p1.py`
> (sha256 `264010f5...766c`) / `rechnung_p1.json` (sha256 `eca434a1...cc1cc`). Nichts beschlossen, nichts committet,
> nichts gepusht. Entscheiden darf nur der Orchestrator.
>
> **Ergebnisblindheit.** Keine Siegeldatei (`*_L_window_sealed.json`, `weekly_ic_series.csv`,
> `ic_series_*_UNION_REAL.csv`) geoeffnet oder gegrept; Fenster `L` des v5e-JSON nicht gelesen (Zugriff nur auf
> `windows.W1/W2`). Keine H-27-/DVOL-/Options-Akte geoeffnet (auch nicht DEC-61 im Wortlaut, nicht
> `state/ANFRAGE_DATA_HARVEST_DVOL_2026-10-13.md`), keine Zahl eines kuenftigen Kandidaten gerechnet.
> **Offenlegung:** Eine Zeilensuche nach "2,4865" im PRD hat Textzeilen der gesperrten Kandidaten A2/A4 mit ausgegeben
> (PRD:564-576, :671, :678, :695, :930, :935). Sie wurden weder ausgewertet noch verwendet; keine Aussage dieses Reviews
> haengt an ihnen.
>
> **Gegenrechnung.** Eigener Code des Reviewers, unabhaengig von `rechnung_p1.py` (scipy-Quadratur, numpy-Monte-Carlo):
> `state/herleitung_programmregel_p1/review_p1_gegenrechnung.py` (sha256 `ffaa6688...b6c6`), liest nur v5e (W1/W2) und
> `feasibility.json` (Konfiguration A), verweigert Siegelnamen, schreibt nichts. Zwei Laeufe, identische Ausgabe
> (stdout sha256 `703bb81d...5045`, ~35 s). Eingaben gegen den Entwurf geprueft: v5e sha256 `94d65559...b3b2`,
> `feasibility.json` `b4680f7c...ca72d9e`, `rechnung_p1.json` `eca434a1...cc1cc`, `rechnung_p1.py` `264010f5...766c` -
> alle gleich. Zitierweise wie im Entwurf: `dec` = `state/decisions.md`, `PRD` = `PRD_SCINANCE3.md`, `Verf` =
> `scinance3-impl/CLAUDE.md`, `Reg` = `state/hypothesis_registry.md`, `E:` = Zeile im ENTWURF, `[rg]` = Gegenrechnung.

---

## URTEIL: ZUSTIMMUNG MIT AUFLAGEN

Die Rechenarbeit ist korrekt (jede gepruefte Zahl reproduziert, Abschnitt 3), die Inventur haelt an allen
nachgeprueften Fundstellen, der Retro-Check ist im Kern ehrlich. Die Empfehlung P-1a ist als **prospektive
Programmregel zulaessig** und die Akte stuetzt die Lesart "Rueckkehr zur registrierten Programmsemantik" besser als die
Gegenlesart (Abschnitt 1). Sie ist aber in ihrer **Wirkung eine Lockerung** - auch gegenueber Verfassungstext, nicht nur
gegenueber "A3-Praxis" - und der DEC-Entwurf hat drei offene Stellen, die genau den Kandidaten, fuer den die Regel
zuerst gilt (H-27), oder kuenftige Registrierungen beguenstigen koennen: Geltung "ab H-32" (B-1), Hebel "strengeres
alpha" in den laxeren Zweig (B-2), nicht festgelegte Rechenart der Gate-Power (B-3). Ohne die Auflagen A-1..A-3 waere
mein Urteil VETO.

---

## 1. Pruefpunkt 1 - Torpfosten: Lockerung oder Rueckkehr zum Wortlaut?

### 1.1 Fundstellen fuer Lesart "Rueckkehr" (Schwelle = kritischer Wert zu alpha 0,05)
- dec:13 / PRD:104 DEC-51 (1): "Mess-Gates: alpha = 0,05 einseitig" - die einzige Stelle, an der das Programm ein
  alpha BESCHLIESST.
- PRD:109 definiert "z" ausdruecklich als Summe `1,6449 + 0,8416 = 2,4865` (z_alpha + z_beta) im Kontext der
  Power-Zeile (PRD:100 "Welchen Effekt sieht das Fenster mit Power 0,80?"). "z" ist per Definition ein MDE-Faktor.
- PRD:175-181 YAML-Template: `alpha: 0.05` und `z: <2.4865|...>` stehen unter `power:`; die Schwelle ist ein eigenes
  Feld `threshold: {wert: <Zahl|Formel>}`. Das Template setzt die Schwelle NICHT auf den MDE-Faktor (vgl. B-9).
- PRD:211 "effektives alpha von 0,05^2 = 0,25 % statt 5 %" und PRD:225/:939 (DEC-52 "~0,5 %") - die Fehlerraten-
  Buchhaltung der Verfassung setzt alpha 0,05 je Fenster voraus.
- PRD:300-305 WP-7-Feasibility "z = 2,4865, alpha 0,05 einseitig: detektierbar = 2,4865*SD/sqrt(52)" = MDE80 eines
  alpha-0,05-Tests; PRD:500, :626 Power-Formeln mit 1,6449; PRD:503 gepoolte GL-012-Pruefung = MDE80 bei alpha 0,01.
- dec:252 DEC-74 (d) Satz 2 "MDE bei Power 0,80 = IC_min" ist nur unter (a) wahr - die Absicht war "IC_min = MDE80".
- Reg:974 ("alpha 0,05 ... z 2,4865"), `wp13_xsec/nulls.py:202-203` ("critical value (alpha 0.05 one-sided)"),
  `wp7_universe/stats.py:27-29` ("alpha 0.05") - die Umsetzer hielten 2,4865 fuer den Wert zu alpha 0,05 (Verwechslung).
- dec:490 DEC-93 Merkposten (b): der Orchestrator selbst nennt die PRD-5.1-Schwelle mit MDE-Faktor "derselbe
  Fehlertyp wie DEC-91" - vor dieser Herleitung, nach Kenntnis von A1.

### 1.2 Fundstellen fuer Lesart "Lockerung" (Schwelle = MDE-Faktor war registriert)
- PRD:512 ("`z * sigma_LS/sqrt(W)` mit dem `z` des registrierten Fenster-Regimes"), PRD:634 (`IC_min = 2,4865 *
  SD_null/sqrt(52)`), PRD:574, :678, :695 - Kandidaten-Schwellenzeilen des PRD, und das PRD IST die Verfassung
  (Verf:14 "Das PRD ist die Verfassung"). Beide Textschichten stehen seit der fruehesten erhaltenen PRD-Fassung
  (git `30a6b9a`, 2026-09-10) nebeneinander - keine ist nachtraeglich.
- dec:236 DEC-73 E1 (`IC_min = 0,0142`), dec:252 DEC-74 (d) Satz 1 "Kritwert-Faktor 2,4865 je Fenster (Groesse
  0,0064; gemeinsam 4,1e-5)" - die Groesse wurde fuer A3 WISSENTLICH festgehalten; dec:275 DEC-75 (1), YAML
  `rules.level 0.9936`, `gates.py:82, :100`, `run.py:303`.
- `REVIEW_GATE_AUDIT_PC_v3_2026-10-12.md:231-232`: "Die strengere Fehlerrate zu waehlen ist immer erlaubt" - die
  A3-Groesse war eine zulaessige, strengere Wahl, kein Regelverstoss.

### 1.3 Entscheidung
Die Akte stuetzt **"Rueckkehr"** als Lesart der **Programmregel**: Nur DEC-51 (1) beschliesst ein alpha; jede
programmweite Zahl (Fehlerraten, WP-7-Feasibility, Power-Formeln, Lo-Formel) ist unter (a) konsistent; die
(b)-Artefakte tragen selbst die Spuren der Verwechslung (DEC-74 (d) Satz 2, Reg:974, nulls.py:202). DEC-74 (d) war
eine A3-Registrierungsentscheidung, keine Programmregel.

Aber: In der **Wirkung** ist P-1a eine **Lockerung**, und zwar gegenueber Verfassungstext (PRD 5.1-5.4
Schwellenzeilen) und gegenueber der einzigen umgesetzten Registrierung - nicht nur gegenueber einer "Praxis". Der
Entwurf stellt das einseitig dar (B-4).

**Zulaessigkeit.** "Kein Torpfosten-Verschieben in KEINE Richtung" bindet die Registry-Disziplin "fuer jeden Lauf"
(Verf:14-16) und verbietet nachtraegliche oder kandidatenspezifische Aenderungen (DEC-52-Sequenz-Zwang dec:32,
DEC-92 E2 dec:475, DEC-93 E3 dec:488). Es verbietet keine prospektive Programmregel; sonst waere DEC-52 selbst
unzulaessig - DEC-52 war eine power-motivierte Lockerung (PRD:211, Faktor 4,7 Retention gegen Faktor 2 Fehlerrate),
beschlossen vor dem ersten Kandidaten, der sie braucht, mit veroeffentlichtem Retro-Check (dec:35-48). Massstab fuer
P-1 ist also: (i) nicht kandidatenspezifisch, (ii) vor dem ersten Kandidaten, der sie braucht, (iii) Retro-Check,
(iv) Etikett. (iii) ist erfuellt; (i), (ii) und (iv) sind es erst mit den Auflagen A-1, A-2, A-4, A-5.

---

## 2. Befunde

Schweregrad: **HOCH** = vor Beschluss zu beheben (sonst VETO); **MITTEL** = Auflage an Regeltext/Etikett;
**NIEDRIG** = Hinweis/Korrektur.

**B-1 (HOCH) Geltung laesst H-27 offen.** E:559-560 "Geltung: jede Registrierung ab H-32 und jede Feasibility- oder
Power-Zeile, die nach diesem Beschluss geschrieben wird". H-27 ist nach DEC-93 (dec:491) und E:518 der naechste
Kandidat, traegt aber eine Nummer < 32. Folge: H-27s Power-Zeile faellt unter P-1, seine Registrierung (Schwelle) nicht
- genau die Mischlage von I-1 - oder es entsteht nach Kenntnis der H-27-Feasibility eine Wahl zwischen alter und neuer
Regel. Das waere der kandidatenspezifische Fall, den dec:32 verbietet.

**B-2 (HOCH) Hebel in den laxeren Zweig.** P-1 (2) (E:570-572) erlaubt ein strengeres alpha, mit dem "Power, MDE,
Zuordnung ... rechnen". Ein strengeres Fenster-alpha senkt die Fenster-Power unter 0,80 und schiebt den Kandidaten nach
P-1 (6) in den DEC-52-Zweig, dessen gemeinsame Fehlerrate 3,4-mal hoeher ist (0,85 % gegen 0,25 %). Zahlen [rg],
zwei gleiche Fenster, Prior d in SE: d = 2,6 -> Default: P_W 0,830, C.10 (gemeinsame Power 0,689, Rate 0,25 %);
mit alpha 0,00645: P_W 0,545 -> DEC-52, Gate-Power 0,844 (Produkt) / 0,881 (exakt), Rate 0,85 %. Ebenso d = 2,5 und
2,8. Derselbe Hebel steckt in P-1 (5) "(i) ... und/oder (ii)" (E:585-588): wer eine zusaetzliche Nuisance-Quelle
heranzieht, erhoeht die SE, senkt P_W und kann in den DEC-52-Zweig wechseln. Klausel (d) ist also nicht "immer
strenger", wie E:316-317 annimmt.

**B-3 (HOCH) Zulassungsgrenze haengt an nicht festgelegter Rechenart.** P-1 (6) (E:591-596) verlangt "Power des
vollstaendigen DEC-52-Gates >= 0,80", sagt aber nicht wie. Der Entwurf rechnet das Produkt der Einzel-Powers (E:503-504,
selbst als Untergrenze benannt); P-1 (8) verlangt eine getestete Funktion, die ebenso exakt rechnen koennte.
Gegenrechnung (gemeinsame Normalverteilung, Fenster unabhaengig, gepoolt = gewichtetes Mittel) [rg]:

| Paket | Zulassung ab d (Produkt) | Zulassung ab d (exakt) | Fenster-Power dort (exakt) |
|---|---:|---:|---:|
| A3-Praxis (b) + DEC-87 (F) | 3,329 | 3,329 | 0,80 |
| (b) + L3v | 2,982 | **2,877** | 0,65 |
| (a) + L3v (Empfehlung) | 2,487 | **2,345** | 0,76 |
| (a) + L3v, gepoolt z_krit 2,5287 | 2,487 | 2,468 | 0,79 |
| (a) + L3v, gepoolt z_krit 2,7720 | 2,487 | 2,487 | 0,80 |

Die Aussage E:501-503 "bei zwei gleich starken Fenstern praktisch identisch mit Fenster-Power >= 0,80; der DEC-52-Zweig
wirkt nur bei ungleichen Fenstern" ist ein Artefakt der Produktrechnung. Die Retro-Einordnungen aendern sich exakt
gerechnet nicht (Abschnitt 4), die Zulassungsgrenze und damit das Mass der Lockerung schon (3,33 -> 2,35 statt 2,49 SE).

**B-4 (HOCH, Etikett) Lockerung nur halb benannt.** E:510 Spalte "gegenueber Verfassung: keine Bewegung (DEC-51 (1)
woertlich)" ist einseitig: P-1a senkt die Schwellen der Verfassungszeilen PRD:512, :574, :634, :678, :695 von
2,4865 / 3,1680 auf 1,6449 / 2,3263 SE. E:498 "(a) + L1 = PRD-5.1-Wortlaut" ist ein Hybrid: der PRD-5.1-Wortlaut hat
Schwelle 2,4865 * SE (PRD:512) mit Power-Formel 1,6449 (PRD:500) - an seiner Zulassungsgrenze 2,24 SE hat das
registrierte Gate nur Fenster-Power Phi(2,24 - 2,4865) = 0,40. "Verschaerfung gegenueber PRD-5.1-Wortlaut" (E:510,
E:604) gilt nur fuer die Zulassung; die Schwelle selbst sinkt. Die Etikett-Zahl "Zulassung ... ab 2,49" (E:604) gilt
nur unter Produktrechnung (B-3).

**B-5 (MITTEL) DEC-52-Rate ueber dem Wortlaut, und P-1a erweitert den Zweig.** Die gemeinsame Rate im DEC-52-Zweig ist
0,851 % (bestaetigt: Quadratur 0,00851, Monte-Carlo 2e7 Ziehungen Seed 7 0,00850) gegen die "bewusst in Kauf genommene
Groesse" 0,5 % (PRD:225, :939). P-1a oeffnet diesen Zweig zusaetzlich fuer 0,60 <= P < 0,80 (L3v). Wer P-1a mit dem
Wortlaut begruendet, muss auch die Wortlaut-Rate halten: gepoolter kritischer Wert **2,5287** (alpha_p 0,00572)
[rg; = E:481-482]. Unter der Niveau-Lesart (alpha = Obergrenze der Groesse, Audit PC v3:231-232) ist das mit DEC-52
(iv) "alpha 0,01" vereinbar. Retro-Wirkung: keine Einordnung aendert sich (A1 c = 1 (a) Gate 0,812 Produkt / 0,843
exakt; A3 measured (a) 0,87 / 0,90; A3 stress (a) 0,46 / 0,58) [rg].

**B-6 (MITTEL, Pruefpunkt 6) P-1b nicht fair dargestellt; dritte Option fehlt.**
(i) E:299-300, :533-535, :549-550: (b) "widerspricht DEC-51 (1)" und "muesste die Verfassung bewegen". Unter der
Standard-Lesart (alpha ist Niveau = Obergrenze der Groesse) ist ein Test mit Groesse 0,0064 ein gueltiger
alpha-0,05-Test; das Programm hat genau das vertreten (Audit PC v3:231-232; DEC-87 (F) dec:412). (b) braucht dann keine
Aenderung von DEC-51 (1)/DEC-52 (iv), nur die Korrektur beschreibender Raten (PRD:211, :225, :939) und der
MDE-/Feasibility-Arithmetik (PRD:297-307, :500-503, :626). Symmetrisch: (a) bewegt die Schwellenzeilen (B-4), (b) die
Power-/Feasibility-Zeilen. Das Hauptargument 6.1 Nr. 1 ist schwaecher als dargestellt.
(ii) E:547 "falls der Orchestrator jede Lesart als Lockerung ausschliessen will" - P-1b enthaelt L3v und ist damit
selbst eine Lockerung gegenueber DEC-87 (F) (Zulassung 3,33 -> 2,98 Produkt / 2,88 exakt SE).
(iii) Die strenge, konsistente dritte Option ist **P-1c** = (b) als ausdrueckliches alpha (je Fenster 0,00645,
z_krit 2,4865; gepoolt 0,00077, z_krit 3,1680) + eine SE (3.2) + A-Stat>=1 + N-Max + **L5**: Zulassung 3,329 SE =
A3-Praxis, Fehlerraten 4,2e-5 (C.10), kippt nichts und keinen Teilgrund (A3 und A1 ueberall GL-012, E:405-438 Spalte
L5), keine Schwellen-Lockerung. Preis: ~79 % mehr Daten je MDE (1,3385^2 = 1,79) und DEC-52 de facto ausser Kraft
(gegen Verf:45, :57 - wobei DEC-52 nach Audit PC v3:231 "nie geboten" ist). Ganz lockerungsfrei nur mit c = max(1,
c_hat, c_E4) fuer Funding-Statistiken (E4 als Untergrenze, methodisch das falsche Objekt, DEC-93 E3).

**B-7 (MITTEL) P-1 (6) entscheidet zwei offene DEC-52-Freiheitsgrade in milder Richtung, ohne Etikett.** Audit PC
v3:250-251 hatte "Screen-Schwelle (ii) ... Magnituden-Band [0,5x; 2,0x]" als offene Freiheitsgrade benannt, deren
Entscheidung "mit Kenntnis der Power-Landschaft" faellt. P-1 (6) (E:594-595) macht (1) das Band zum Etikett (Rate 0,830
-> 0,851 %, mehr Power) und (2) den Screen zu "0,5 * z_krit_gepoolt * SE_gepoolt". Der 2.0-Retro-Check las DEC-52 (ii)
als 0,5x der Fenster-Schwelle (`RETROCHECK_DEC52.md:71-79`: H-20 "+10 bps je Fenster", Screen 5 bp). Bei gleichen
Fenstern unter (a) identisch (0,82249 gegen 0,82243 SE_W [rg]); bei ungleichen Fenstern ist die gepoolte Lesart im
verrauschteren Fenster milder. E:515 "Retro-Check 2.0 unberuehrt" ist fuer den neuen Screen nicht belegt (H-20 lag
0,17 bp unter dem alten Screen); er haelt, weil H-20 gepoolt ohnehin scheitert (Fenster-p 0,40 / 0,17 gegen alpha 0,01,
dec:39-41) - das gehoert in den Text.

**B-8 (MITTEL, Pruefpunkt 4) Retro-Check ehrlich, eine Nebenaussage fehlt.** "Kein Kippen von GL-032" ist korrekt:
bindend ist stress, die Bedingung muss unter beiden Kalibrierungen halten (Audit PC v3:168-170, DEC-87 (A) dec:407,
DEC-92 E1 dec:474), und P-1 (5) N-Max setzt das fort. Zu ergaenzen: GL-032 traegt den Satz "Bindend stress; gleiches
Ergebnis" (`gate_log.md:16`), DEC-92 E1 "auch measured 0,042 / 0,041". Unter P-1a ((a)+L3v) waere das measured-Ergebnis
NICHT gleich (DEC-52-Gate 0,89..0,91 Produkt, 0,92..0,93 exakt) - GL-032 truege nur noch auf der stress-Bindung. Das ist
ein Teilgrund-Wegfall analog A1 E1 und gehoert so ins Etikett. Ferner ist das A3-DEC-52-Gate ohne Beta-Kontrolle
gerechnet (im Zweig nie definiert, E:393-394) - "lauffaehig" gilt nur vorbehaltlich dieser Bedingung (W1 P_beta measured
(a) 0,98, praktisch folgenlos).

**B-9 (NIEDRIG) Inventur: Fehlklassifikation und zwei fehlende Fundstellen.** PRD:181 ist unter I-1 als "Schwelle =
MDE-Faktor" gefuehrt (E:111, :232-233); das `z` steht unter `power:` neben `alpha: 0.05`, die Schwelle ist das getrennte
Feld `threshold` (PRD:175) - Befund I-8 (Benennung) plus Luecke "kein Feld z_krit", kein I-1. Es fehlen dec:18 (DEC-51
Begruendung "Keine Gate-Schwelle wird dadurch veraendert": DEC-51 war Power-Konvention) und PRD:109 als Definition
"z = z_alpha + z_beta" fuer die Lesartfrage (im Entwurf nur als Benennungsbefund I-8).

**B-10 (NIEDRIG) Regeltext.** (1) P-1 (4) (E:578) "SE_W = max(SD(x)/sqrt(W), SE_stat(x))" laesst einen registrierten
Strukturboden weg (A3: `max(Boden, SD(IC_t))`, dec:275); Vorschlag `SE_W = max(Boden_registriert, SD(x),
SD_stat(x)) / sqrt(W)`. (2) P-1 (7) (E:597-598) nennt nur die analytische Bailey/LdP-Decke; verbindlich ist die am
Null-Fixture gemessene (PRD 3.3.4) - `max(z_krit * SE, analytische Decke, gemessene Decke)`.

**B-11 (NIEDRIG) Ungleicher Power-Massstab der Regime.** C.10 wird mit Fenster-Power 0,80 zugelassen (gemeinsam 0,64),
DEC-52 erst bei Gate-Power 0,80. Fuer d = 2,49..2,9 SE hat der DEC-52-Zweig mehr Gate-Power (exakt 0,85..0,94) als C.10
gemeinsam (0,64..0,80) [rg] - das ist der Anreiz hinter B-2. Kein eigener Regelbedarf, wenn A-2 umgesetzt ist; im Text
benennen.

**B-12 (NIEDRIG) Gabelungsmuster.** Von fuenf Regelgabeln faellt P-1a dreimal Richtung Testbarkeit ((a) statt (b),
A-Stat>=1 statt E4, L3v statt L2/L5) und zweimal streng (c >= 1, N-Max) - das Muster, das REVIEW_A1 H-1 / DEC-93 E3
(dec:488) festhielt. Jede der drei Wahlen hat eine von A1 unabhaengige Begruendung (DEC-51 (1); PRD:487 und DEC-92-Lehre;
Monotonie). Hinnehmbar mit Etikett; A-3 und A-6 mildern es.

**Bestaetigt (Pruefpunkt 2, Inventur-Stichprobe, je an der Fundstelle gelesen):** I-2 dec:252 (DEC-74 (d) beide
Saetze); I-3 PRD:623 (`SE = SD_null/sqrt(52)`) gegen `run.py:289-298` (`max(floor, SD)/sqrt(W)`); I-4 dec:181 (DEC-67
E4) und `stats.py:238-253` ("never replacing it"); I-5 dec:14, dec:27, PRD:216, PRD:501-503, PRD:630, dec:412; I-8
`nulls.py:202-203` und `stats.py:27-33`; I-9 Reg:974; I-10 PRD:225, :939; dazu `gates.py:82, :100`, `run.py:303, :549,
:674, :1081`, `nulls.py:479, :494-496`. Alle Zitate stimmen; einzige Abweichung B-9.

---

## 3. Pruefpunkt 3 - Arithmetik (unabhaengig nachgerechnet)

| Groesse | Entwurf | Gegenrechnung [rg] |
|---|---|---|
| z 0,05 / 0,01 / 0,80 | 1,6449 / 2,3263 / 0,8416 | gleich |
| Fenster-Groesse bei Schwelle 2,4865 | 0,00645 | 0,006450 (Faktor 7,75 unter 0,05) |
| C.10 gemeinsam (a) / (b), Verhaeltnis | 0,25 % / 0,0042 %, 60,1 | 0,002500 / 4,161e-5, 60,09 |
| DEC-52 gemeinsam (a): Screens / Band / Vorzeichen | 0,851 / 0,830 / 0,990 % | 0,851 / 0,830 / 0,990 %; MC 0,850 % |
| DEC-52 gemeinsam (b) | 0,0713 / 0,0712 / 0,0767 % | gleich |
| gepoolt z_krit fuer 0,5 % | 2,5287 (alpha 0,0057) | 2,5287 (0,00572); fuer 0,25 %: 2,7720 (0,00279) |
| MDE-Verhaeltnis, Datenbedarf | 1,3385, 1,79 | 1,3385, 1,7916 |
| Zulassung A3-Praxis / (a)+L3v / (a)+L1 / (b)+L3v | 3,329 / 2,487 / 2,241 / 2,982 | gleich (Produkt); exakt 3,329 / **2,345** / 2,240 / **2,877** (B-3) |
| Bailey K* unter (a) / (b) | 12 (1,665) / 89 (2,489) | 12 (1,6648) / 89 (2,4893) |
| IC_min unter (a), kleinstes W1 / W2 | 0,01108 / 0,00966 | 0,01108 / 0,00966 |
| Autokorrelationstabelle E:342-346 | - | Stichproben 1,69 % (0,60/naiv), 0,51 % (1,0/E4) gleich |

A3 (alle 16 Zellen Variante x Kalibrierung x Option) und A1 (6 Zellen) reproduziert, z. B. mom1 stress (b) W1 0,205 /
0,0601, W2 0,554 / 0,0381, gepoolt 0,0430; mom1 measured (a) 0,775 / 0,0311, 0,969 / 0,0212, gepoolt 0,0241 / Gate
0,899; A1 E4 (a) 0,345 / 0,813, 176,5 > 147,6; c = 1 (b) 0,295 / 0,929, 143,0, Gate 0,668. Kein Rechenfehler gefunden.

---

## 4. Pruefpunkt 4 - Retro-Check

Vollstaendig fuer die Optionen des Entwurfs und im Kern ehrlich; die Teilwirkungen (A3 measured, A1 E1) stehen offen
im Etikett (E:605-608). Exakte Gate-Power aendert keine Einordnung [rg]: A3 stress (a) 0,65 / 0,63 / 0,61 / 0,66
(< 0,80, GL-012 bleibt); A3 measured (b) 0,77 / 0,76 / 0,75 / 0,78 (< 0,80, GL-012 bleibt; zudem gepoolt MDE80 > 0,03);
A1 E4 (a) 0,53; A1 c = 1 (b) 0,74 (GL-012 unter (b)+L3v bleibt, E:548 korrekt).

"Unter measured waere A3 mit (a) lauffaehig gewesen - nicht bindend, also kein Kippen": **korrekt eingeordnet**, weil
die Akte die Feasibility unter beiden Kalibrierungen verlangt (Audit PC v3:168-170) und P-1 (5) das fortschreibt.
Unvollstaendig ist nur die Nebenaussage (B-8): GL-032s "gleiches Ergebnis" unter measured entfiele; GL-032 stuende allein
auf der stress-Bindung. Mit A-6 (gepoolt 2,5287) bleibt A1 E1 bei theta = 1 entfallen (Gate 0,812 / 0,843); erst mit
2,7720 und Produktrechnung bliebe E1 stehen (0,766) [rg] - zur Information, keine Auflage.

---

## 5. Pruefpunkt 5 - L3v und Nuisance-Regel

- **Monoton im Prior: ja.** Alle drei Komponenten (Fenster-Power, gepoolte Power, Screens) steigen mit dem Prior (bei
  festen SE, gemeinsamer Skalierung theta); die Zuordnung kann nur GL-012 -> DEC-52 -> C.10 oder GL-012 -> C.10
  wandern, nie zurueck. Gilt fuer Produkt- und exakte Rechnung. Nachgeprueft am A1-Gitter (Segmente E:373 fuer L2
  reproduziert: 0,766 / 0,975 / 1,277).
- **Nicht monoton in alpha und SE** (B-2): strengeres alpha oder groessere SE kann von C.10 in den Zweig mit hoeherer
  Fehlerrate fuehren. Das ist kein Prior-Problem, aber ein Steuerungsproblem -> A-2.
- **In sich konsistent:** bis auf die offene Rechenart (B-3), die Screen-/Band-Festlegung (B-7) und den ungleichen
  Power-Massstab (B-11).
- **Vorab ohne Outcome-Daten anwendbar: ja**, sofern Prior registriert ist; Nuisance aus Vorperiode (Mittel nie
  ausgegeben) und/oder Simulation. Fuer Klasse W ist die Vorperiode das versiegelte L (E:354-355) - dann nur Simulation,
  korrekt im Regeltext (E:588).
- **Nuisance "groessere SE":** konsistent mit der Programmpraxis (DEC-77 E1 (b), DEC-87 (A)/(E), Audit PC v3:168-170),
  prior-unabhaengig, damit trivial monoton. Schwaeche: "und/oder" (E:586) laesst die Quellenwahl offen (B-2) -> "beide,
  soweit verfuegbar, Verfuegbarkeit vorab festgestellt". Die 10-%-Klausel der Positivkontrolle (E:589-590) ist gut.

---

## 6. Auflagen (Bedingung der Zustimmung)

- **A-1 (zu B-1).** Geltung: "jede Registrierung, Feasibility-, Power- und Zuordnungszeile, die nach diesem Beschluss
  entsteht, **einschliesslich H-27** und jeder eroeffneten, nicht registrierten Hypothese". Kein Nummernschnitt.
- **A-2 (zu B-2).** P-1 (6): Die Regime-Zuordnung wird immer mit dem Default-alpha (0,05 je Fenster) und der
  vollstaendigen Nuisance-Quellenliste nach P-1 (5) festgestellt; P-1 (5) "und/oder" -> "beide, soweit verfuegbar".
  Ein nach P-1 (2) gewaehltes strengeres alpha gilt nur innerhalb des so zugeordneten Zweigs und muss dort Power >= 0,80
  behalten; es kann nie einen Wechsel von C.10 in den DEC-52-Zweig bewirken.
- **A-3 (zu B-3).** P-1 (6): "Die Power des DEC-52-Gates ist das Produkt der Einzel-Powers (gepoolte Bedingung, beide
  Screens) - konservative Untergrenze; eine exakte Rechnung ist Bericht, nie Zuordnungsgrundlage." Die T4-Funktion nach
  P-1 (8) pinnt das.
- **A-4 (zu B-4).** Etikett ohne Relativierung: "**Lockerung**, beschlossen nach Kenntnis von A3 (GL-032) und A1
  (GL-033). Fenster-Groesse 0,0064 -> 0,05 (x7,75), C.10 gemeinsam 4,2e-5 -> 2,5e-3 (x60); Schwellenzeilen PRD 5.1-5.4
  sinken von 2,4865 auf 1,6449 SE; Zulassung bei zwei gleichen Fenstern 3,33 -> 2,49 SE (Produktrechnung).
  Begruendung: Rueckkehr zur einzigen beschlossenen alpha-Semantik DEC-51 (1)." Die Zeile "Verschaerfung gegenueber
  PRD-5.1-Wortlaut" nur mit dem Zusatz "nur fuer die Zulassung; die Schwelle sinkt". GL-032-Nebenaussage nach B-8 ins
  Etikett.
- **A-5 (Blindheit und Wirkung).** (1) Der Orchestrator stellt vor dem Beschluss selbst fest und vermerkt im DEC, dass in
  der Akte keine H-27-Zahl zu Prior, SE, Power oder Feasibility existiert und keine gerechnet wurde (DEC-61, PRD,
  Daten-Anfrage) - der Reviewer durfte das nicht pruefen; andernfalls ist die Zahl im Etikett zu nennen. (2) Jede
  Registrierung unter P-1 weist ihr Regime zusaetzlich unter der A3-Praxis aus ((b) + DEC-87 (F), Produkt); ist sie nur
  unter P-1 zulassungsfaehig, tragen Registry und GL-Eintrag "zugelassen nur durch DEC-94 (Lockerung)".
- **A-6 (zu B-5, empfohlen).** DEC-52-Zweig gepoolt z_krit **2,5287** (alpha_p 0,0057), damit die gemeinsame Rate dem
  Verfassungswortlaut 0,5 % (PRD:225) entspricht. Lehnt der Orchestrator das ab, muss das Etikett "DEC-52-Rate 0,85 %
  statt 0,5 %, Zweig auf P < 0,80 erweitert" ausdruecklich als zweite Lockerung fuehren.
- **A-7 (zu B-7).** Band als Etikett und Screen-Lesart "0,5x gepoolte Schwelle" im Etikett als Festlegung nach Kenntnis
  der Power-Landschaft benennen; Satz zum 2.0-Retro-Check mit der H-20-Begruendung (gepoolt p >> 0,01) belegen.
- **A-8 (Textkorrekturen im Entwurf vor Beschluss).** 5.2-Tabelle um die exakte Spalte ergaenzen (B-3); 5.3/E:510 und
  E:498 nach B-4; 3.1 (b) und 6.1 nach B-6 (Niveau-Lesart, P-1b enthaelt Lockerung, P-1c als dritte Option); Inventur
  nach B-9; Regeltext P-1 (4)/(7) nach B-10.

---

## 7. Empfehlung an den Orchestrator

**Beschliessen: P-1a mit den Auflagen A-1..A-8** (kurz P-1a'), also Schwelle (a) mit Klausel (d) in der Form von A-2,
eine SE fuer Test und Power, A-Stat>=1, N-Max ("beide Quellen"), L3v mit Produktrechnung, DEC-52 gepoolt 2,5287.
**Etikett:** "Lockerung - beschlossen nach Kenntnis von A3 (GL-032) und A1 (GL-033), vor jeder H-27-Zahl (vom
Orchestrator festgestellt); Rueckkehr zur beschlossenen Semantik DEC-51 (1); kippt kein Verdikt; Teilgruende entfallen:
GL-032 'gleiches Ergebnis unter measured', GL-033 E1 (DEC-67 E4)."

Begruendung: P-1a' ist die einzige Option, unter der alle programmweiten Zahlen der Verfassung (Fehlerraten, WP-7,
Power-Formeln) ohne Neuberechnung gelten; die Lockerung ist real, aber prospektiv, nicht kandidatenspezifisch (A-1, A-5),
offen beziffert (A-4) und im DEC-52-Zweig auf den Wortlaut begrenzt (A-6).

**Wer das Etikett "Lockerung" nach zwei GL-012 nicht tragen will, beschliesst P-1c, nicht P-1b**: P-1b enthaelt ueber
L3v selbst eine Lockerung (B-6 (ii)); nur P-1c ((b) explizit + L5) haelt die A3-Zulassungsgrenze 3,33 SE exakt, um den
Preis von ~79 % mehr Daten je MDE und eines faktisch ausgesetzten DEC-52.
