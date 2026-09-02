# REVIEW PRD_SCINANCE3_DRAFT.md - Adversarischer Gate-Audit

> Gate-Auditor, Phase 4, 2026-09-02. Read-only. Pruefobjekt: `scratchpad/prd/PRD_SCINANCE3_DRAFT.md` (982 Zeilen). Bindende Vorlagen: `PROGRAMMENTWURF_3.0.md` (Orchestrator-Entscheidung), `state/decisions.md` (DEC-51/52/53), `research/REVIEW_R1_R4.md`, `survey/ERKENNTNIS_KOMPENDIUM.md` (B, C, D, E). Auftrag: zerlegen, nicht loben. Jede Rechnung unten ist nachgerechnet und steht mit Rechenweg da, damit sie ihrerseits angreifbar ist.

---

## 0. Der eine Satz, der den Audit traegt

Das PRD ist handwerklich das dichteste Dokument des Programms, aber seine zentrale Zahl - `rho_quer <= 0,03`, die ueber die gesamte Klasse W entscheidet - steht auf einem Schaetzer, der mathematisch nichts messen kann, und auf einer oekonomischen Mindestmagnitude, die dasselbe Dokument an anderer Stelle mit einem um Faktor 1,6 abweichenden Wert fuehrt. Und **DEC-52 wird bei genau den beiden Kandidaten angewendet, bei denen keine Power-Zahl existiert, und bei genau dem Kandidaten ausgeschlossen, bei dem eine existiert.**

---

## 1. NACHGERECHNETE ZAHLEN

| # | Groesse | PRD-Ort | Urteil |
|---|---|---|---|
| 1.1 | `rho_quer`-Schwelle 0,0313 (Kettenrechnung) | Z. 344-352 | arithmetisch **richtig**, beide Eingaenge **falsch** (1.1a/1.1b) |
| 1.2 | `IC_min = 0,062` aus Break-even 0,031 | Z. 341 | arithmetisch **richtig**, Kostenbasis **inkonsistent** |
| 1.3 | 0,062 vertraeglich mit DEC-51? | Z. 345 | `z=2,4865` ja; im DEC-52-Zweig **falsches alpha** (1.3) |
| 1.4 | Demeaning-Bias `-1/(K-1)` | Z. 327-331 | Zahlen **richtig**, Korrekturformel **konzeptionell falsch** |
| 1.5 | A2 `N_eff` je Ereignis = 1,111 | Z. 634 | **richtig** (2/1,8) |
| 1.6 | A2 58 statt 104 Ereignisse | Z. 635 | **richtig** (52 x 1,111 = 57,8) |
| 1.7 | A2 `SE = 4,73 bps` | Z. 636 | **richtig** (36/sqrt(58) = 4,727) |
| 1.8 | A2 `SE(Delta) = 5,11 bps` | Z. 642 | **richtig** (sqrt(4,73^2 + 1,93^2) = 5,106) |
| 1.9 | A2 12 bps = 2,35 SE | Z. 643 | **richtig** (2,3503) |
| 1.10 | A2 Per-Fenster-Power 0,76 | Z. 644 | richtig **nur fuer `r_pre`**; fuer `r_post` **0,51** |
| 1.11 | WP-10(A) `N_cluster >= 46` | Z. 430-432 | arithmetisch **richtig**, Effektgroesse **erfunden**, Spearman-Faktor fehlt |
| 1.12 | WP-10(B) `adv_sel <= 3,5 bp` | Z. 449 | Differenz **richtig**, Schwellenlogik **inkonsistent** |
| 1.13 | A4 `w_min = 0,49 % p.a. + m*r_opp` | Z. 741-744 | arithmetisch **richtig**, Inhalt = **C.2-Bruch** |
| 1.14 | WP-9-Materialitaet 0,012 Vol-Punkte | Z. 409 | 3/250 **richtig**, die 250 **importiert**, Erreichbarkeit ungeprueft |
| 1.15 | Selektions-Decken 0,60 (K=3) / 0,98 (K=7) | Z. 543, 696 | **richtig**, exakt nachgerechnet |
| 1.16 | K-0.1-Kurve (0,71 bp; 6,6 h; 53 min; 2,7 d) | Z. 946 | **vollstaendig richtig** |
| 1.17 | Detektierbarkeits-Tabelle K=110/170/300/Decke | Z. 356-361 | alle 20 Zellen **richtig** |
| 1.18 | Peso-Fixture `p = e^-1,67 = 0,19` | Z. 110 | **richtig** (lambda*T = 5/3) |
| 1.19 | Vol-Drag 0,105 %/Tag = 73,5 bps/Woche | Z. 684 | **richtig** |
| 1.20 | `T_min = 6,18/SR^2` | Z. 240 | **Naeherung**, Korrekturterm still gestrichen (SR 2,0: 1,80 statt 1,55 a) |
| 1.21 | "5 Req/s = 0,4 % des Limits" | Z. 298, 834 | **FALSCH: 4,2 %** (600 je 5 s = 120 Req/s) |
| 1.22 | A1-Funding-Backfill "~9.300 Calls, ~15 min" | Z. 520 | **FALSCH: ~31 min** bei 5 Req/s |
| 1.23 | GPU-Bilanz 309-357 h | Z. 255 | **richtig** |
| 1.24 | A1-Feasibility `sigma_LS <= 104 / 148` | Z. 538-539 | 104 **richtig**, 148 **falsch** (korrekt 116) |
| 1.25 | A2-Monatsvariante SE 9,87 / Power 0,11 | Z. 650 | **richtig**; Placebo-Term fehlt (10,06 / 0,106) |
| 1.26 | Merton/Mertens-Faktor 1,827 -> 11,3 a | Z. 240 | **richtig** (monatlicher SR 0,2887) |

### 1.1 Die `rho_quer`-Kette (Z. 344-352)

Nachgerechnet: `0,062*sqrt(52)/2,4865 = 0,179806`; `1/0,179806^2 = 30,9307`; `N_eff >= 31,9307`; `rho_quer <= 1/31,9307 = 0,031318`. **Die Arithmetik ist exakt.** Falsch sind beide Eingaenge.

**(a) Der Schaetzer kann nichts messen (BLOCKER B-1).** `rho_quer` ist in Z. 319-323 definiert als Mittel der paarweisen Korrelationen der querschnittlich demeanten Reihen. Fuer die demeanten Residuen gilt `sum_i e_{i,t} = 0` in jeder Woche, also `Var(sum_i e_i) = 0`, also `sum_i Var(e_i) + sum_{i!=j} Cov(e_i,e_j) = 0`, also **mittlere paarweise Kovarianz = -(mittlere Varianz)/(K-1)**. Bei gleichen Varianzen ist die mittlere paarweise Korrelation damit **identisch `-1/(K-1)` - fuer jede Datenlage.** Numerisch verifiziert (K = 110/170/300, T = 3.000 Wochen, Blockstruktur mit wahrer Sektorkorrelation 0,0 / 0,3 / 0,6): der Schaetzer liefert in allen neun Faellen exakt `-1/(K-1)` auf fuenf Nachkommastellen. In die PRD-Korrekturformel Z. 330 eingesetzt ergibt das `rho_quer_hat = (-1/(K-1) + 1/(K-1))/(1 - 1/(K-1)) = 0` - **immer**; Befund B2 waere garantiert.

Mit realistischer Vol-Heterogenitaet kippt es in die Gegenrichtung: bei lognormaler Vol-Streuung (sigma_log = 0,6; K = 170) misst derselbe Schaetzer **+0,045 bei wahrer Sektorkorrelation NULL** und +0,048 bei 0,5 - der Wert ist ein Vol-Heterogenitaets-Artefakt des gleichgewichteten Demeanings und praktisch unabhaengig von der Groesse, die er messen soll. Dann waere Befund B1 (Klasse W TOT) garantiert. **Das Rang-1-Paket der Welle entscheidet damit ueber die gesamte Klasse W anhand einer Zahl, die entweder eine algebraische Identitaet oder ein Artefakt ist.** Der eigene Positiv-Fixture (Z. 385: "`rho_quer_hat` muss den injizierten Wert treffen") kann nicht bestehen; der Null-Fixture (Z. 386) besteht trivial mit gleichen Varianzen und faellt durch mit realistischen. Nach der Logik von Z. 387 waere die Panel-Maschinerie damit "methodisch invalide".

**(b) Die 0,062 ist nicht die Kostenbasis dieses Kandidaten.** Z. 341 leitet sie gegen die **11-bp-Einzelpositions-Wand** her. Dasselbe Dokument nennt die Wochenkosten desselben Portfolios in Z. 704 mit **18 bps** (A3-M), **30 bps** (A3-R), und in Z. 534 mit **36 bps** (A1, bereits inkl. Faktor 2). Setzt man die eigenen Zahlen in dieselbe Formel:

| Rahmen | `IC_min` | zulaessiges `rho_quer` |
|---|---|---|
| Einzelposition, Wand 11 bp (PRD Z. 341) | 0,0625 | **0,0313** |
| Einzelposition, Wand 18 bp (PRD Z. 704, A3-M) | 0,1022 | **0,0808** |
| Dezil-Rahmen `R_LS = 2,0*IC*sigma_xs`, sigma_xs 500 | 0,036 | **0,0108** |
| Dezil-Rahmen, exakter Faktor 3,51 (Review 2.7) | 0,0205 | **0,0035** |

**Faktor 23 zwischen vier Lesarten desselben Dokuments.** Die 0,03 ist nicht hergeleitet, sondern eine von vier gleichberechtigten Zahlen. Dass Review 2.7 (Dezil-Spreadfaktor 2,0 gegen exakt 3,51) im PRD **gar nicht vorkommt** - der Review verlangte ausdruecklich, ihn zu erwaehnen, "damit die Korrektur nicht spaeter als Verbesserung der Kante verkauft wird" - ist deshalb kein Formfehler: er bewegt die zentrale Wellenzahl um Faktor 3.

### 1.3 DEC-51 gegen DEC-52 (iv): der alpha-Fehler (BLOCKER B-4)

`z = 1,6449 + 0,8416 = 2,4865` ist unter DEC-51 (alpha 0,05 einseitig, Power 0,80) korrekt, und 0,062 ist als detektierbarer IC damit vertraeglich - solange das Urteil bei alpha 0,05 liegt. Der **gepoolte** Schaetzer laeuft nach DEC-52 (iv) aber bei **alpha = 0,01**, also `z = 2,3263 + 0,8416 = 3,1680`. Das PRD rechnet den gepoolten Zweig durchgaengig mit 2,4865:

- Z. 363: "gepoolt bei K=170 detektierbar **0,0469** - klar unter der Mindestmagnitude". Korrekt: `3,1680 * 0,018869 = 0,0598`. Unter 0,062, aber nicht "klar".
- **Bei K = 110 - der in Befund B2 (Z. 370) registrierten Untergrenze - ist der gepoolte detektierbare Wert 0,0624 > 0,062, die Bedingung also verletzt.** Der Mindest-K unter korrektem alpha ist **117**, nicht 110.
- Z. 539: A1 gepoolt `sigma_LS <= 36/0,24384 = 148 bps/Woche`. Korrekt: `36/0,31064 = 116 bps/Woche`. Die Feasibility-Schranke ist um **28 % zu weit**.

### 1.4 Demeaning-Bias (Z. 327-331)

Die Zahlenwerte sind richtig: `-1/109 = -0,00917` (K=110), `-1/169 = -0,00592` (K=170), `-1/299 = -0,00334` (K=300); der Hinweis "dieselbe Groessenordnung wie die Entscheidungsschwelle 0,03" ist richtig und wichtig. Die **Korrekturformel** Z. 330 ist jedoch nicht ableitbar: im Aequikorrelationsmodell ist `corr(e_i,e_j) = (rho - A)/(1 - A)` mit `A = (1 + (K-1)rho)/K`, und wegen `rho - A = -(1-rho)/K` und `1 - A = (K-1)(1-rho)/K` folgt exakt `-1/(K-1)` **unabhaengig von rho**. Der Bias ist kein additiver Offset auf einem sonst informativen Schaetzer, er ist der ganze Schaetzer.

### 1.10 A2: die Power-Zeile deckt nur die halbe Metrik ab

Die Metrik (Z. 627) ist zweiteilig: `r_pre` = [07:30, 08:00) = 30 min und `r_post` = [08:00, 09:00) = 60 min. Die Power-Zeile rechnet durchgaengig mit `36 bps`, der 30-Minuten-SD. Fuer `r_post` gilt `SD = 36*sqrt(2) = 51 bps` (R3s eigene Kette: Tagesvol 2,5 % -> Stunden-SD 51 bps -> 30-min 36 bps):

```
SE(Ereignis) = 51/sqrt(58)  = 6,70 bps
SE(Placebo)  = 51/sqrt(348) = 2,73 bps
SE(Delta)    = 7,23 bps  ->  12 bps = 1,659 SE
Per-Fenster-Power = Phi(1,659 - 1,6449) = 0,51
```

**Fuer `r_post` liegt die Per-Fenster-Power bei 0,51, also unter 0,60.** Die Aussage Z. 648 ("Per-Fenster-Power 0,76 liegt ueber 0,60 - DEC-52 (i) ist fuer A2 NICHT anwendbar") gilt damit nur fuer eine der beiden registrierten Teststatistiken. Zusaetzlich verlangt der Gate-Text Z. 660 (2) Signifikanz "gegen **alle** vorregistrierten Placebos gleichzeitig" - bindend ist dann der Placebo mit dem **groessten** SE, nicht P2 mit dem kleinsten. Review 2.3 setzt den Placebo-Term ausdruecklich "mindestens so gross" wie den Ereignis-Term an; unter dieser Annahme ist `SE(Delta) = 6,69`, `12 bps = 1,79 SE`, Power **0,56** - und DEC-52 (i) waere fuer A2 anwendbar. Das PRD weicht hier ohne Kennzeichnung vom Review ab, und zwar in die Richtung, die die eigene Schlussfolgerung stuetzt.

### 1.11 WP-10(A): Floor 46 (Z. 427-432)

`atanh(0,70) = 0,86730`, `atanh(0,45) = 0,48470`, Differenz `0,38260`; `(2,4865/0,38260)^2 + 3 = 45,24` -> 46. Arithmetik richtig. Aber `rho_stress = 0,70` und `rho_ruhig = 0,45` sind **frei gesetzt**, ohne Quelle und ohne Herleitung; sie definieren die Effektgroesse und damit den Floor vollstaendig (bei 0,80/0,40 waere er 27, bei 0,65/0,50 waere er 141). Zweitens gilt fuer **Spearman** `SE(z) = 1,06/sqrt(n-3)` (Bonett/Wright), nicht `1/sqrt(n-3)`; der korrekte Floor ist **51**. Drittens erscheint 0,70 in A-B1/A-B2 (Z. 439-440) erneut als Entscheidungsschwelle - eine gesetzte Zahl in einer vorab fixierten Konsequenz.

### 1.12 `adv_sel <= 3,5 bp` (Z. 449)

`FEE_TAKER - FEE_MAKER = 5,5 - 2,0 = 3,5` ist richtig (Kompendium B.3); Review 2.8 ist damit umgesetzt. Aber die Schwelle liegt **exakt am Break-even**: ein Kandidat, der sie gerade erreicht, hat aus passiver Ausfuehrung null Vorteil. Dasselbe Dokument fordert an drei anderen Stellen den **Faktor 2 ueber Break-even** (R4 1.1c: Z. 341, 534, 742). Konsistent waere `adv_sel <= 1,75 bp`. Unhergeleitet bleiben ausserdem `p_fill(60s) >= 0,70` sowie die 60-s- und 10-s-Fenster (Z. 447) - drei gesetzte Zahlen in einem Absatz, der mit "Schwellen, korrekt hergeleitet" ueberschrieben ist.

### 1.14 WP-9-Materialitaet 0,012 (Z. 409)

`3/250 = 0,012` ist richtig. Die **250** ist ein aus DEC-32 uebernommenes Verhaeltnis, das dort einen anderen Vergleich beschreibt (interne Reproduzierbarkeit gegen einen eigenen Speicher). Es fehlt exakt das, was L-1 (Z. 32) als Programm-Lehre auffuehrt: die **Erreichbarkeitspruefung**. Zwei unabhaengige Quellen mit unterschiedlicher Bucket-Konvention weichen im Tagesschluss regelmaessig um mehr als 0,012 Vol-Punkte ab - der PRD-eigene Adversarial-Fixture (Z. 413, "verschobene Zeitachse") sagt das selbst. Die Schranke ist damit ein C-14-Wiedergaenger: importiertes Verhaeltnis, Erreichbarkeit ungeprueft, Ausgang B2 ("Quellen nicht austauschbar") faktisch vorbestimmt.

---

## 2. VERFASSUNGSTREUE

### 2.1 C.2 (Mess-Gate != Tradability): drei Verstoesse

Das PRD verteidigt C.2 zweimal ausdruecklich (Z. 79, Z. 103) und verletzt es dreimal in den Gate-Texten.

**(i) A4, Gate-Bedingung (1) (Z. 751).** `w >= w_min` mit `w_min = 0,49 % p.a. + m*r_opp`. Das ist **vollstaendig** eine oekonomische Groesse: Zyklus-Kosten mal Faktor 2 plus Kapitalkosten. In A4s PASS-Bedingung steht **kein statistischer Rauschboden** - `sigma_w` ist ungemessen (Z. 734). Genau unter dieser Konstruktion waere H-04 ein DROP gewesen; sie ist das, was Review 4.5 zurueckgewiesen und der Orchestrator in Entwurf 2.1 abgelehnt hat. Die Vorgabe der Vorlage ("Schwelle aus Kapitalbindung hergeleitet, nicht bewusst hoeher gesetzt") rechtfertigt eine Herleitungs**methode** gegen R1s Federstrich, nicht die Aufnahme der Kostenwand in das Mess-Gate.

**(ii) WP-7-Befund B1 (Z. 369).** `rho_quer > 0,03` toetet Klasse W - und die 0,03 ist ueber `IC_min = 0,062` direkt aus der Friktionswand abgeleitet. Formal ein Feasibility-Check (C.12), materiell ein DROP-Automat, dessen Ausloeser eine Handelskostenzahl ist. Der Klammersatz in Z. 341 ("dient hier ausschliesslich der Feasibility-Rechnung") ist eine Behauptung, keine Trennung. Sauber waere, die Feasibility-Frage gegen den **strukturellen** Rauschboden zu stellen (kann das Design ueberhaupt einen IC in der Groesse des Permutations-Rauschbodens aufloesen?) und die Wand-Relation als Etikett zu fuehren.

**(iii) WP-7-Befund B5 (Z. 373).** `sigma_xs < 500 bps/Woche` -> "Etikett `unter_wand` ... oder wird gestrichen": eine oekonomische Groesse mit Streichungsoption.

Sauber gehandhabt sind dagegen A1 (Z. 545: Schwelle aus Nulleffekt-CI und Rauschboden, oekonomisches Minimum nur als Etikett Z. 551), A3 (Z. 698) und die A2-Etiketten (Z. 660). Das Prinzip ist verstanden, es wird nur nicht durchgehalten.

### 2.2 Die zehn Pflichtzeilen aus Entwurf 2.2

**Vollstaendig vorhanden**, jede mit eigenem Template-Schluessel: Power (`power`), Entscheidungsrelevanz (`economic_minimum` + `decision_relevance`), Cluster-Einheit (`power.cluster_unit`/`n_eff`), Selektions-Deflation (`selection`), adversariales Fixture (`fixtures.adversarial`), Kostenmodell-Bindung (`constants_hash`), Irreversibilitaet (`irreversibility_probe`), Positivkontroll-Vorschaltung (`positive_control`), Kapital/Steuer/Venue (`capital_tax_venue`), Stress-Episode (`stress_episode`). Kein Punkt fehlt; die DEC-54-Auflagen (a)-(c) sind woertlich uebernommen (Z. 147).

**Fehlend sind zwei Vorgaben aus den Vorlagen selbst:**

- **DEC-53 (Ergebnis-Artefakt-Pflicht, `state/decisions.md` Z. 53-57)** kommt im PRD **nirgends** vor: kein Template-Feld fuer die Cluster-Serie, keines fuer Bootstrap-Replikate bzw. Seed, keine Stufe in der T0-T6-Tabelle (Z. 133-141), keine Erwaehnung in Par. 6. Das ist die einzige DEC, die unmittelbar aus dem DEC-52-Retro-Check folgt - und sie ist unsichtbar. Ohne sie ist der naechste Regel-Retro-Check wieder nicht nachrechenbar, also genau der Fehler, der DEC-53 erzwungen hat.
- **DEC-51 Punkt 1** (zweiseitig fuer META-/Zensus-Fragen, ausdrueckliche Etikettierung) und die **Registrierung der Effektrichtung** ("die Richtung ist Teil der Registrierung") fehlen in der PRD-Fassung von DEC-51 (Z. 95-101) und im YAML (`sided: one`, aber kein Richtungsfeld). Da WP-7 eine Zensusfrage ist, ist die Seitigkeit dort nicht triviale Formsache.

### 2.3 DEC-52: kandidatenspezifisch und auf Power >= 0,6 gestreckt

**Ja, in beide Richtungen.**

- **A2** (Z. 648): Power **gerechnet** (0,76) -> DEC-52 ausgeschlossen. Verfahren korrekt; siehe aber 1.10 (fuer `r_post` 0,51).
- **A3** (Z. 694): "Per-Fenster-Power liegt damit unter 0,60" - diese Zahl wird **nicht gerechnet**. Mit den Groessen derselben Zeile (SE 0,0267 bei K=170; wahrer Effekt = oekonomisches Minimum 0,062) ergibt sich `Phi(0,062/0,0267 - 1,6449) = Phi(0,679) = 0,75`; bei K=110 0,72; bei K=300 0,78. **Die Per-Fenster-Power liegt zwischen 0,72 und 0,78, also klar ueber 0,60 - DEC-52 (i) ist fuer A3 nicht erfuellt.** Nimmt man die konsistente Kostenbasis 18 bps (1.1b, `IC_min = 0,102`), ist sie 0,99. Es gibt keinen Eingangswert im Dokument, bei dem A3 unter 0,60 landet.
- **A1** (Z. 549): der Gate-Text schreibt DEC-52 (ii)/(iii)/(iv) **fest**, obwohl `sigma_LS` ungemessen ist (Z. 534) und damit **keine Power-Zahl existiert**. DEC-52 (i) verlangt die Power-Zeile **vor** dem Lauf. Z. 234 sagt selbst "A1 braucht sie voraussichtlich" - "voraussichtlich" ist keine Bedingungspruefung.

Damit gilt: **DEC-52 wird bei genau den zwei Kandidaten angewandt, bei denen keine Power-Zahl vorliegt, und bei dem einen ausgeschlossen, bei dem eine vorliegt.** Das ist die Kandidatenspezifik, die Auflage 1 verbietet - nicht in der Beschlussreihenfolge, sondern in der Anwendung der Anwendungsbedingung. Verschaerfend Z. 536-539: A1 stellt **zwei Designs nebeneinander** (per Fenster hart / gepoolt) und macht die Wahl vom gemessenen `sigma_LS` abhaengig - eine Designwahl **nach** dem Sehen einer Zahl, genau die Konstruktion, gegen die C.1/C.3 gebaut sind.

### 2.4 Status von DEC-51/52/53 gegenueber `state/decisions.md`

- DEC-51 ist **beschlossen** (decisions.md Z. 10-19); das PRD fuehrt es durchgaengig als "(Entwurf)" (Z. 95) und macht seinen Beschluss zur Vorbedingung (Z. 5, 480, 972).
- DEC-52 ist **beschlossen** (Nachtrag 2026-09-02, decisions.md Z. 35-49); der Retro-Check liegt als `state/RETROCHECK_DEC52.md` vor (kein Verdikt kippt; H-06 verfehlt den 0,5x-Screen in beiden Fenstern, H-22 am Vorzeichenwechsel, H-20 knapp mit 4,83 gegen 5 bp; Etikett **Verbesserung**). Das PRD fuehrt DEC-52 als "(Entwurf)" (Z. 222) und ordnet in Z. 974 an, den Retro-Check erst noch durchzufuehren. **Woertlich befolgt wuerde das PRD einen bereits vollzogenen Beschluss ruecknehmen.**
- **DEC-53 ist doppelt belegt.** In `decisions.md` ist DEC-53 die Ergebnis-Artefakt-Pflicht; das PRD vergibt dieselbe Nummer an den Stress-Tage-Kanon (Z. 127) und referenziert sie achtmal. Ein append-only-Log mit zwei verschiedenen DEC-53 ist kaputt.

### 2.5 Reihenfolge Zensus -> Alpha

Formal eingehalten: Statusregel Z. 5, Statuszeile Z. 480, Beschluss- und Baureihenfolge Z. 970-979; kein Abschnitt behauptet eine Registrierung. Materiell registriert das PRD A2 vorab: Fenster, Metrik, Placebosatz, Selektions-K, Schwelle **12 bps** und ein "woertlicher" Gate-Text (Z. 658-660) stehen fest, A2 hat "**keine Datenbedingung**" (Z. 672), und Z. 979 nennt ihn den "frueheste[n] laufbereite[n] Kandidat[en]". Das ist eine Registrierung in allem ausser dem Namen - und ihre Schwelle ist die einzige im Dokument, die aus einer importierten Zahl stammt (Abschnitt 4). Zweitens praejudiziert Z. 650 die noch offene Nutzer-/Orchestrator-Entscheidung A2-P1 ("arithmetisch ist nur (a) registrierbar") und macht die Gegenvariante ueber Feasibility-Kill-Bedingung 5 (Z. 666) zum automatischen DROP.

---

## 3. TORPFOSTEN-RISIKO: gesetzt statt hergeleitet

| Schwelle | Ort | Status | Abhaengig von |
|---|---|---|---|
| `sigma_xs < 500 bps/Woche` (B5) | Z. 373 | **gesetzt**, ohne Herleitung; Konsequenz **nicht** vorab fixiert | WP-7 |
| Alt-Spread `> 3x` Majors (B6) | Z. 374 | **gesetzt** (warum 3?) | WP-7 |
| `K >= 110` | Z. 370, 676 | gesetzt; korrekt waere 117 (1.3) | WP-7 + alpha-Korrektur |
| `p_fill(60s) >= 0,70`, 60 s, 10 s | Z. 447-449 | **gesetzt** | WP-10(B) |
| `rho_stress = 0,70` / `rho_ruhig = 0,45` | Z. 427, 439-440 | **erfunden**, traegt Floor 46 | - |
| `adv_sel <= 3,5 bp` | Z. 449 | hergeleitet, aber Break-even statt x2 | - |
| Autokorrelation Sortierschluessel `< 0,30` | Z. 559 | **gesetzt**, ist Kill-Bedingung | WP-7 |
| Listing-Ausschluss "erste 8 Wochen" | Z. 380 | **gesetzt** | - |
| Episodenluecke "hoechstens ein Nicht-Stress-Tag" | Z. 127 | **gesetzt** | - |
| Perzentil 97,5 / Fenster 24 Monate | Z. 127 | aus der Vorlage uebernommen, dort gesetzt | - |
| A2-Schwelle `12 bps` | Z. 656 | **importiert aus R3**, Herleitung zirkulaer | A2-P1 |
| A4 Vorzeichenkonsistenz "6 von 8" | Z. 751 | **gesetzt**; dritte, neue Fenster-Regel neben C.10 und DEC-52 | V-2 |
| Redundanz-Gate Spearman `< 0,60` | Z. 702 | importiert (B.13), Erreichbarkeit ungeprueft | - |
| WP-9 `<= 0,012` auf `>= 99 %` der Tage | Z. 409 | Verhaeltnis 250 und die 99 % beide importiert | - |

**Vorfrage-abhaengig und trotzdem als Zahl fixiert:** `K >= 110` (WP-7 plus alpha), `sigma_xs < 500` (WP-7), `rho_quer <= 0,03` (offene Kostenbasis plus defekter Schaetzer), `< 0,30` Autokorrelation (WP-7), `12 bps` (A2-P1, weil die Ereignismenge die Effektgroesse aendert). Vorbildlich dagegen `w_min` (A4), das als **Formel** registriert ist - das ist die Form, die alle uebrigen haben muessten.

**Der schwerste Einzelfall ist B5** (Z. 373): "Entscheidung des Orchestrators nach dem Befund; die Schwelle 500 steht vorher fest." Die Schwelle steht fest, die **Konsequenz nicht** - die exakte Umkehrung des WP-4-Musters, das Z. 278 fuer bindend erklaert ("die Konsequenz jedes Ausgangs steht VORAB im Dokument").

---

## 4. DER A2-P1-BEFUND (Z. 650)

**Die Rechnung ist richtig:** `N_eff = 12*1,111 = 13,33`; `36/sqrt(13,33) = 9,86`; `12/9,87 = 1,216`; `Phi(1,216 - 1,6449) = 0,334`; `0,334^2 = 0,112`. Konsistenzfehler: fuer Variante (b) fehlt der Placebo-Term, den (a) enthaelt; mit ihm `SE = 10,06`, Power 0,33, ueber zwei Fenster 0,106 - Schluss unveraendert.

**Der Befund selbst ist neu und richtig gesehen.** R3 definiert den Verfallskalender als "jeder Freitag 08:00 UTC" (R3 Z. 104) und registriert gleichzeitig P1 = "Nicht-Verfalls-Freitage" (R3 Z. 121). Beides zusammen ist leer. Der Review hat das nicht bemerkt, das PRD schon.

**Die Schlussfolgerung "arithmetisch ist nur (a) registrierbar" traegt aber nicht**, aus drei Gruenden.

**(a) Der Effekt wird ueber beide Varianten konstant gehalten, obwohl er es nicht ist.** Die 12 bps stammen aus R3; R3 stuetzt sie auf Ni/Pearson/Poteshman (2005) - ein Befund an **Monats**verfaellen mit hohem Open Interest - und auf Blasco et al. (2023), ebenfalls Monatsverfaelle (R3 Z. 71-80). Der Mechanismus (netto short Gamma, Hedgebedarf proportional zum verfallenden Open Interest) skaliert mit dem OI des Termins; ein woechentlicher Verfall traegt einen Bruchteil des OI eines Quartalsverfalls. Variante (a) mittelt also ueber eine Menge, in der ~40 von 52 Terminen den Effekt strukturell verduennen - fuer diese Menge sind die 12 bps nicht belegt. Setzt man in (b) den Effekt auch nur um Faktor 2 hoeher an (24 bps), ergibt sich `Phi(24/10,06 - 1,6449) = 0,77` je Fenster, also **besser als (a)**. Der Vergleich bei konstantem Effekt bevorzugt systematisch die breitere, verduennte Menge.

**(b) Variante (b) bringt P1 zurueck.** Der Grund, ueber (b) ueberhaupt nachzudenken, war der Verlust des saubersten Placebos. Bei Monatsverfaellen sind ~40 Nicht-Verfalls-Freitage je Fenster vorhanden, P1 lebt, und der Wochentags-/Uhrzeit-Confounder wird direkt kontrolliert statt nur ueber P2/P3. Die Rechnung bilanziert diesen Gewinn nicht.

**(c) (a) ist nicht mehr die von R3 gemeinte Hypothese - aber (b) auch nicht ganz.** R3s Ereignismenge ist tatsaechlich woechentlich (N ~ 52 je Symbol und Fenster), insofern ist (a) formal R3-treu. R3s **Effektgroesse** ist es nicht: sie stammt aus dem monatsverfalls-basierten Aktien-Analogon 16,5 bps. (a) ist damit R3s Design mit einer Effektgroesse, die zu R3s Literatur, nicht zu R3s Ereignismenge gehoert - und das ist der eigentliche Konstruktionsfehler, den A2-P1 aufdeckt, ohne ihn zu benennen. **Empfehlung:** A2-P1 nicht per Power-Vergleich bei konstantem Effekt entscheiden, sondern beide Varianten mit **eigener** Effektherleitung und eigenem Placebosatz nebeneinanderstellen. Traegt keine der beiden eine belegte Effektgroesse, ist A2 ein GL-012-Fall und kein Alpha-Slot.

---

## 5. VOLLSTAENDIGKEIT

**Gliederung 1-9: vollstaendig.** Alle neun Abschnitte plus 9.1-9.3 vorhanden. Die Liste "nicht aufgenommen" (Z. 897-917) deckt alle 13 in der Vorlage Par. 4 genannten Ausschluesse ab, ergaenzt um vier R4-/R1-Punkte. Kein Abschnitt fehlt.

**Ausfuehrbarkeit unter Nutzer-Default (b): nein - aber nicht wegen des Nutzers.** 8.1/8.2/8.3 blockieren korrekt nichts. Blockiert sind: (1) **WP-7** ist wie spezifiziert nicht ausfuehrbar, weil der `rho_quer`-Schaetzer nicht misst, was er messen soll, und beide Befundzweige dadurch vorbestimmt sind; (2) **WP-10(A)** hat einen Floor, der nach eigener Rechnung unerreichbar ist - das ist bewusst so und mit A-B3 vorab konsequenziert, handwerklich sauber, aber der Floor steht auf zwei erfundenen Zahlen; (3) **A1/A3** koennen die DEC-52-Anwendbarkeit nicht nachweisen (2.3); (4) **A4** ist ohne `r_opp` (8.2) und ohne Margin-WP nicht numerisch bestimmbar - was das PRD korrekt ausweist (Z. 734, 747). Ohne jede Nutzerantwort ausfuehrbar sind: V-1..V-4, WP-9, WP-10(B), die Erzeugung des Stress-Kanons und saemtliche Fixtures.

**Nutzer-Fragen: klar als offen markiert und nicht vom PRD beantwortet.** 8.1 uebernimmt den Orchestrator-Default (b) aus der Vorlage Par. 6.1 und benennt den Preis aller drei Optionen; 8.2 und 8.3 sind offen mit Wirkungsangabe ("keine Blockade"). Eine Unschaerfe: `r_opp` steht in 8.2 als offen, waehrend Z. 492 im A1-Nulleffekt `r_USD = 0` verwendet - dieselbe oekonomische Groesse einmal offen, einmal auf 0 gesetzt. Die Setzung ist R1/Review zugeschrieben und konservativ, gehoert aber als Annahme etikettiert und mit 8.2 verlinkt.

---

## 6. ERFUNDENES, UNBELEGTES, UNMARKIERTES

Nach der eigenen Belegregel (Z. 5) zu beanstanden:

1. **`36 bps` (30-Min-SD)** - traegt die gesamte A2-Power-Zeile (Z. 631, 636, 639, 650), ohne Herleitung und ohne Quelle. Sie ist herleitbar (R3: Tagesvol 2,5 % -> 51 bps/h -> 36 bps/30 min), aber die Kette steht nicht im PRD; ausserdem ist sie BTC-only, waehrend ueber BTC+ETH gepoolt wird.
2. **`rho_stress = 0,70`, `rho_ruhig = 0,45`** (Z. 427) - ohne Quelle; tragen Floor 46 und die Befunde A-B1/A-B2.
3. **`rho ~ 0,8`** (BTC/ETH, Z. 631; 5 Symbole, Z. 427) - aus Review 2.3/2.5 uebernommen, dort selbst ungemessen, im PRD **nicht** `[sek]` markiert. Der gesamte `N_eff`-Block von A2 haengt daran.
4. **"Deribit fuehrt woechentliche Freitags-Verfaelle"** (Z. 650) - die Tatsachenbehauptung, die den A2-P1-Befund traegt, ohne Quelle und ohne `[sek]`.
5. **`/v5/market/delivery-price` "200/Seite, Cursor"** (Z. 726) und die `instruments-info`-Cursorpaginierung (Z. 297) - Endpunktparameter ohne `[sek]` und ohne Quelle.
6. **"Basis- und Spread-Abweichungen fallen ~11 % pro Jahr `[sek]`"** und **"ein 2025 negativ gewordener delta-neutraler Carry `[sek]`"** (Z. 486) - `[sek]` ohne benannte Sekundaerquelle ist kein Beleg; beide tragen die Zahler-Bestands-Zeile, die das PRD selbst zur Pflichtzeile macht (3.3.9c).
7. **`sigma_xs < 500`, Faktor `3x`, `p_fill 0,70`, 60 s, 10 s, `< 0,30`, "8 Wochen", "6 von 8"** - acht gesetzte Skalare (Abschnitt 3).
8. **FRL (2026)** (Z. 621) - R3 vermerkt "Autoren nicht ermittelbar, Volltext gesperrt"; das PRD zitiert ohne diesen Vorbehalt.
9. Korrekt gehandhabt und ausdruecklich festzuhalten: Z. 387 (Grobys/Sandretto mit offener Nicht-Verifizierbarkeit), Z. 298/395/469 (Endpunktparameter mit `[sek]`), Z. 514/520 (UNBELEGT - V-1), Z. 534 (UNGEMESSEN - WP-7), Z. 121/809 (`m` UNGEMESSEN), Z. 472 (V-4). Die Disziplin ist ueberwiegend vorhanden; die Ausnahmen sind zaehlbar und behebbar.

---

## 7. NOTWENDIGE AENDERUNGEN

### BLOCKER

**B-1. `rho_quer`-Schaetzer ersetzen (Par. 4.1: Z. 311-352, 379, 385-386).** *Aenderungstext:* "Der von R4 K-0.5 verlangte Eingang ist **nicht** `rho_quer` als mittlere paarweise Korrelation demeanter Reihen: diese Groesse ist wegen `sum_i e_{i,t} = 0` bei gleichen Varianzen identisch `-1/(K-1)` und bei ungleichen Varianzen ein Vol-Heterogenitaets-Artefakt. Gemessen wird stattdessen **direkt `N_eff`**: (i) die Wochenstreuung des Querschnitts-IC auf dem point-in-time-Universum wird empirisch bestimmt und ueber `N_eff = 1 + 1/SD(IC_t)^2` invertiert; (ii) als Kontrolle wird dieselbe Groesse aus der Querschnitts-Permutation innerhalb jeder Woche gewonnen (R4 1.2b(1)), die die effektive Breite exakt enthaelt, ohne dass eine Korrelation geschaetzt werden muss. Die Befunde B1/B2/B3 werden auf `N_eff` bzw. `SD(IC_t)` umgestellt; `rho_quer` wird nur noch nachrichtlich als `1/N_eff` berichtet. Der Null-Fixture prueft, dass der `N_eff`-Schaetzer auf unabhaengigen Reihen mit **realistischer Vol-Heterogenitaet** `N_eff ~ K` liefert."

**B-2. DEC-Nummern korrigieren und DEC-53 aufnehmen (durchgaengig).** *Aenderungstext:* Stress-Tage-Kanon zu **DEC-57** umnummerieren (alle acht Fundstellen), DEC-54/55/56 gegen den Log pruefen, und in Par. 3.3 eine **elfte Pflichtzeile** ergaenzen: "**Ergebnis-Artefakt-Zeile (DEC-53).** Jeder Lauf schreibt (a) die urteilstragende Serie auf Cluster-Ebene mit SHA-256 und (b) die Bootstrap-Replikate oder Seed plus Generator-Fingerprint, aus dem sie bit-identisch reproduzierbar sind. Ein Lauf ohne (a)+(b) ist KEIN VERDIKT (loud fail im Treiber, Test gepinnt)." Dazu YAML-Felder `cluster_series_ref` und `bootstrap_replicates_ref` sowie eine Stufe **T7** in der Tabelle Z. 133.

**B-3. Status von DEC-51/DEC-52 auf den Log ziehen (Z. 5, 95, 222, 480, 972-974).** *Aenderungstext:* "DEC-51 ist am 2026-09-02 **beschlossen** (`state/decisions.md`). DEC-52 ist nach dem veroeffentlichten Retro-Check (`state/RETROCHECK_DEC52.md`: kein Verdikt kippt; Etikett **Verbesserung**; Auflage (iii) war fuer die 2.0-Laeufe nicht nachrechenbar, daher Stouffer/Fisher als Obergrenze der Evidenz) ebenfalls **beschlossen**." Z. 974 ("Retro-Check durchfuehren") streichen und durch den Verweis auf das vorliegende Ergebnis ersetzen. Die benannte Einschraenkung des Retro-Checks gehoert woertlich in Par. 3.5, weil sie der Entstehungsgrund von DEC-53 ist.

**B-4. alpha im gepoolten Zweig korrigieren (Z. 356-363, 536-539, 694).** *Aenderungstext:* "Wo das Urteil nach DEC-52 (iv) auf dem gepoolten Schaetzer bei alpha = 0,01 liegt, wird der detektierbare Effekt mit `z = 2,3263 + 0,8416 = 3,1680` gerechnet, nicht mit 2,4865." Folgekorrekturen: gepoolte Detektierbarkeit K=110 -> **0,0624**, K=170 -> **0,0598**, K=300 -> **0,0576**; **K-Floor in B2 von 110 auf 117** (oder B2 unabhaengig von K als `N_eff >= 26,1` formulieren); A1-Tabelle Z. 539 auf `sigma_LS <= 116 bps/Woche`.

**B-5. DEC-52-Anwendbarkeit je Kandidat rechnen, nicht behaupten (Z. 234, 549, 694).** *Aenderungstext A3:* "Per-Fenster-Power gegen den registrierten Mindesteffekt: `Phi(IC_min/SE - 1,6449)` = 0,72 (K=110) bis 0,78 (K=300) bei `IC_min = 0,062`. **DEC-52 (i) ist damit fuer A3 NICHT erfuellt; A3 laeuft unter C.10 hart.** Ergibt die korrigierte Kostenbasis (Par. 4.1) einen anderen `IC_min`, wird die Power neu gerechnet und die Anwendbarkeit vor der Registrierung schriftlich festgestellt." *Aenderungstext A1:* die DEC-52-Verweise aus dem Gate-Text entfernen und ersetzen durch: "Die Fenster-Regel fuer A1 wird **erst nach der WP-7-Messung von `sigma_LS`** festgelegt, indem die Per-Fenster-Power gerechnet und gegen die 0,60-Grenze aus DEC-52 (i) gehalten wird; diese Rechnung ist Teil der Registrierung und wird **vor** dem Lauf publiziert." Die Doppeltabelle Z. 536-539 wird zu **einer** vorab fixierten Zuordnungsregel (z. B. "`sigma_LS <= 104` -> C.10 hart; `104 < sigma_LS <= 116` -> DEC-52-Zweig, sofern (i) erfuellt; `> 116` -> GL-012-DROP"), damit die Designwahl nicht nach dem Sehen der Zahl faellt.

**B-6. A4s `w_min` aus der PASS-Bedingung nehmen (Z. 738-751).** *Aenderungstext:* "PASS-Bedingung des kapitalfreien Mess-Gates ist: `w` ist gegen `w_null` (Margin-Bindungsdifferenz mal Opportunitaetszins) signifikant, mit `w >= 2,4865 * sigma_w/sqrt(N_cluster)` als registrierter Schwelle, sobald `sigma_w` gemessen ist. `w_min = 0,49 % p.a. + m*r_opp` ist die **oekonomische Mindestmagnitude** und wandert vollstaendig in die Entscheidungsrelevanz-Zeile und in das getrennt zu registrierende Tradability-Gate A4b (C.2, Review 4.5)." Die Regel "Vorzeichenkonsistenz in >= 6 von 8" streichen oder als dritte Fenster-Regel in DEC-52 explizit herleiten - drei parallele Fenster-Regeln in einem Programm sind ein offener Torpfosten.

**B-7. Kostenbasis der oekonomischen Mindestmagnitude vereinheitlichen (Z. 341, 534, 704).** *Aenderungstext:* "Die oekonomische Mindestmagnitude eines **Portfolio**-Kandidaten wird im Portfoliorahmen gerechnet, nicht im Einzelpositionsrahmen der Kurve K-0.1: `R_LS = f * IC * sigma_xs` mit dem exakten Dezilfaktor `f = 3,51` (Review 2.7; R2s 2,0 ist um Faktor 1,75 pessimistisch), gegen die turnover-gewichteten Wochenkosten (A3-M 18, A3-R 30, A3-V 4,5-7,5 bps). Die Sensitivitaet der daraus abgeleiteten Breiten-Schwelle wird ausgewiesen: ueber die vier im Dokument vorkommenden Lesarten spannt sie `rho_quer <= 0,0035 ... 0,0808`. Solange `sigma_xs` ungemessen ist, wird die Welle-1-Schwelle als **Formel** registriert und die Zahl erst nach WP-7 gesetzt (DEC-54b)." Zugleich Review 2.7 als eigene Zeile in Par. 2 oder 9.2 aufnehmen - der Review verlangt das ausdruecklich, damit die Korrektur nicht spaeter als Kantenverbesserung verkauft wird.

**B-8. A2-Schwelle: die zirkulaere Herleitung offenlegen (Z. 656, 660, 662).** *Aenderungstext:* "Die 12 bps stammen aus R3 und sind dort **gegen die Friktionswand** gewaehlt ('bewusst unter der 15-bps-Wand'), nicht aus einem Rauschboden hergeleitet; die Angabe '2,35 SE' ist die **Folge** dieser Wahl, nicht ihre Herleitung. Registriert wird die Schwelle als `max(oberes 95-%-Quantil der Placebo-Verteilung ; 2,4865 * SE(Delta))` mit Herleitungs-Referenz; bei `SE(Delta) = 5,11` ergibt der zweite Term **12,7 bps**, endgueltig gesetzt nach der Placebo-Messung." Zusaetzlich die Etiketten korrigieren: 12 bps liegen **ueber** der 11-bp-Taker-Wand und unter der 15-bp-Gesamtwand - nicht "unter" beiden (Z. 656, 660) und nicht "zwischen" 4 und 11 bps (Z. 662).

### WICHTIG

**W-1.** A2-Power fuer `r_post` ergaenzen (Z. 644): `SD = 51 bps`, `SE(Delta) = 7,23`, Power **0,51**. Konsequenz vorab fixieren: entweder `r_post` streichen (dann K = 1 statt 2) oder A2 mit zwei Armen und getrennter Fenster-Regel fuehren.

**W-2.** Die `36 bps`-Kette in den Text schreiben ("Tagesvol 2,5 % -> 51 bps/h -> 36 bps/30 min, BTC") und die gepoolte SD statt der BTC-SD verwenden; ETH gesondert messen.

**W-3.** Placebo-SE begruenden: das Gate verlangt Signifikanz gegen **alle** Placebos, der Rauschboden wird aber aus P2 (kleinster SE) gebildet. Abweichung von Review 2.3 ("mindestens so gross") kennzeichnen oder mit dem groessten Placebo-SE rechnen (Power 0,56 - dann kippt die DEC-52-Zuordnung von A2).

**W-4.** WP-9-Materialitaet: Erreichbarkeitspruefung vorschalten (L-1/C-14). *Text:* "Vor Festlegung der Schranke wird an 10 Ueberlappungstagen gemessen, welche Abweichung allein die Bucket-Konvention erzeugt; die Schranke liegt oberhalb dieses Wertes und unterhalb 3/250. Ist die Konventionsabweichung groesser als 0,012, lautet B2 nicht 'Quellen nicht austauschbar', sondern 'Schranke unerreichbar' und wird neu hergeleitet."

**W-5.** WP-10(A): `rho_stress`/`rho_ruhig` als **Annahmen** kennzeichnen, den Floor als Funktion `n(rho_s, rho_r)` registrieren, den Spearman-Faktor 1,06 (Bonett/Wright) aufnehmen -> Floor **51** statt 46.

**W-6.** `adv_sel` entweder auf **1,75 bp** (Faktor 2 wie ueberall sonst) setzen oder die Ausnahme vom Faktor 2 begruenden. `p_fill 0,70`, 60 s und 10 s herleiten oder als "gesetzt, Deskriptor ohne Gate-Wirkung" etikettieren.

**W-7.** B5 (Z. 373): Konsequenz vorab fixieren. *Text:* "`sigma_xs` unter 500 bps/Woche -> A3 traegt das Etikett `unter_wand` und bleibt registrierbar; eine Streichung erfolgt aufgrund dieses Befundes **nicht** (C.2)." Und die 500 herleiten (aus `f*IC_min*sigma_xs >= 2 x Kosten`) oder als Formel registrieren.

**W-8.** B6 und A3-Entscheidungsrelevanz: 15 bps ist die **Gesamtwand** (11 bp Gebuehr + ~4 bp Slippage), nicht die "Majors-Slippage-Konstante". Review 1-R3-K-35 woertlich uebernehmen: "eine Spread-Messung korrigiert die Konstante um hoechstens ~27 % und kann sie nie unter 11 bps Taker druecken." Faktor `3x` in B6 herleiten oder streichen.

**W-9.** Review 6.7 zweite Haelfte fehlt. Ergaenzen in WP-10(A): "Zusaetzlich wird die Korrelation zwischen Praemien-PnL und **Handlungsfaehigkeit des Betreibers** (Margin-Auslastung, ADL-Ereignisse, Auszahlungsstopp-Proxy) als Deskriptor berichtet; sie ist nach Review 6.7 die eigentlich relevante Groesse."

**W-10.** Stress-Kanon (Z. 127-129): der rollierende 97,5-Perzentil-Schnitt erzeugt **per Konstruktion** ~2,5 % Stress-Tage in jedem Fenster; die Bedingung ">= 1 Stress-Episode je Fenster" (Z. 129, 522, 549, 751) kann damit nie binden und ist ein Schein-Gate. Zweitens misst ein relativer Schnitt Vol-Regime, nicht Liquiditaets-Crashs - was WP-10(A) braucht. *Text:* "Der Kanon fuehrt zwei Listen: `STRESS_REL` (rollierendes 97,5-Perzentil, fuer Regimeabdeckung) und `STRESS_ABS` (absoluter RV-Schnitt der Gesamthistorie plus die namentlich benannten Ereignisse 10.10.2025 und 19.08.2026, fuer die Kohaerenzfrage; Review 6.6). Die Stress-Pflicht der Klasse P bezieht sich auf `STRESS_ABS`." Zugleich kennzeichnen, dass die Vorlage nur den 19.08.2026 nennt und 10.10.2025 aus Review 6.6 ergaenzt wurde.

**W-11.** DEC-51-Wiedergabe (Z. 95-101) um Punkt 1 (zweiseitig fuer META/Zensus, ausdrueckliche Etikettierung - betrifft WP-7 unmittelbar) und Punkt 5 (Ueberlappung) ergaenzen; YAML um `richtung: <positiv|negativ>` erweitern.

**W-12.** Positivkontroll-Vorschaltung (3.3.8, "> 1 h") auf WP-10(B) anwenden: 86 min je Fenster (Z. 461), im WP-10-Abschnitt fehlt `vorgeschaltet: true`.

**W-13.** Rechenfehler korrigieren: Z. 298/834 "0,4 % des Limits" -> **4,2 %**; Z. 520 "~9.300 Calls, ~15 min" -> **~31 min** bei 5 Req/s (oder die abweichende Drossel nennen). Beide Zahlen stuetzen die Aussage "extrem sicher" bzw. den Aufwandsplan.

**W-14.** `T_min`-Formel (Z. 240): den Faktor `(1 + SR_ann^2/(2q))` und `q` mitfuehren oder die Naeherung als solche kennzeichnen.

**W-15.** Vom Review verlangt, im PRD nicht eingeplant: **R3-K-37 Stufe 1** (tagesgenaue Ketten-Luecken-Karte; Review: "sofort - sie fehlt dem Programm komplett und wird von jedem Options-Kandidaten gebraucht") und **R3-K-33 Stufe 1** (billiger binaerer Zensus, "behalten"). Beide gehoeren als Zeile in Par. 4 oder mit ausdruecklicher Vertagungsbegruendung in 9.1; A5s Options-Spread-Zensus (Z. 767 (b)) setzt Stufe 1 faktisch voraus.

**W-16.** `r_opp` (8.2) gegen `r_USD = 0` (Z. 492): dieselbe Groesse, zwei Behandlungen. Die Setzung 0 als konservative Annahme etikettieren und auf 8.2 verlinken.

### KOSMETIK

**K-1.** Z. 11: "Sieben kapitalfreie Mess-WEITER" mit sechs Namen (aus dem Kompendium uebernommen) - Zahl oder Liste korrigieren.
**K-2.** Z. 89/131: "die zehn neuen Pflichtzeilen" plus 3.3.11 als elfte ("Zusatz"); nach B-2 werden es zwoelf - Ueberschrift anpassen.
**K-3.** Z. 978 nennt DEC-55, das im Dokument nirgends definiert wird.
**K-4.** Z. 230: nach DEC-52 (iv) liegt die gemeinsame Falsch-Positiv-Rate bei ~0,5 % gegen vorher 0,25 % (Vorzeichenfilter 0,5 mal alpha 0,01); der Restfaktor 2 sollte benannt werden, damit "keine Lockerung" praezise bleibt.
**K-5.** Z. 650: den Placebo-Term auch in Variante (b) mitrechnen (`SE = 10,06`).
**K-6.** Z. 471: V-3 nutzt korrekt 113 Tage (Kompendium F.1), waehrend Vorlage und Review von "43 Harvest-Tagen" sprechen - die Korrektur ist richtig und sollte als bewusste Abweichung vermerkt werden.
**K-7.** Z. 298 (2.008 Tage) gegen Z. 303/854 (2.190 Tage) - zwei Historienlaengen nebeneinander, einmal benennen.
**K-8.** Z. 621: FRL-(2026)-Zitat um R3s Vorbehalt "Autoren nicht ermittelbar" ergaenzen.

---

## 8. Was bleibt, wenn man alles abzieht

Nach den acht Blockern bleibt ein tragfaehiges Geruest: die Klassensystematik P/W/E mit klassenspezifischem Nulleffekt- und Fixture-Katalog, die zehn Pflichtzeilen als YAML mit Herleitungs-Referenz statt Skalar, die Peso-/Beta-/Selektions-Fixtures, die Trennung Backfill gegen Harvester nach Irreversibilitaet, die RAISE-Stub-Politik in `tradability3/`, die vorab fixierten Binaerbefunde nach WP-4-Muster und die vollstaendig korrekte Detektierbarkeits-Tabelle. Das ist mehr belastbare Methodik als in R1-R4 zusammen.

Die drei teuersten Fehler sind vom selben Typ und alle behebbar: **eine Zahl aus einem Bericht uebernehmen und die Herleitung nachtraeglich danebenschreiben** (12 bps in A2), **eine Groesse messen wollen, deren Schaetzer sie nicht enthaelt** (`rho_quer`), und **eine Regel anwenden, ohne ihre Anwendungsbedingung zu rechnen** (DEC-52 bei A1 und A3). Genau das ist die Fehlerklasse, gegen die die Verfassung 3.0 gebaut ist.

*Ende REVIEW_PRD3.md - Gate-Auditor, 2026-09-02. Kein Urteil hier ist ein Registrierungs-Verdikt; alle Befunde sind Empfehlungen an den Orchestrator.*
