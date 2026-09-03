# S2 - Oekologie, kritische Uebergaenge und sequentielle Detektion

**Phase:** 3b Wissenschafts-Exkurs (Scinance 3.0) | **Scout:** S2 | **Stand:** 2026-09-03
**Auftrag:** `scratchpad/exkurs/BRIEF_EXKURS.md`

**Gelesen (vollstaendig):** `survey/ERKENNTNIS_KOMPENDIUM.md` (A-F); `PRD_SCINANCE3.md`
(1, 2, 3.1-3.4, 4.1/4.3/4.4, 9.1-9.3); `CROSSDOMAIN_PARK.md`; `CROSSDOMAIN_PRD.md`.
Zusaetzlich zur Duplikat-Vermeidung: `research/R3_EREIGNIS_STRUKTUR.md` (K-34/K-35 und
dessen "NICHT vorgeschlagen"-Liste), `research/R4_METHODIK_INFRA.md` (1.1-1.2),
`scinance2-impl/state/hypothesis_registry.md` (H-19/H-20-Wortlaut), `state/gate_log.md`
(GL-026), `state/decisions.md` (DEC-14), `scinance3-impl/survey/CODE_MAP.md`.

> **Belegregel.** Der Egress-Proxy blockte in dieser Sitzung `arxiv.org`,
> `journals.plos.org`, `link.springer.com`, `pmel.noaa.gov`. **Kein einziger Volltext
> war lesbar.** Jede externe Zahl traegt **[sek]** (Quelle = Suchtreffer-Metadaten);
> selbst gerechnete Formeln sind **eigene Herleitung** und nachrechenbar;
> Programm-Zahlen tragen ihre GL-/DEC-/B-Referenz. Belegstatus am Ende. Nichts geraten.

---

## 0. Der ehrliche Rahmen

Meine Disziplin verkauft "Fruehwarnung vor dem Kipppunkt". Auf diesem Bestand ist das
mit hoher Wahrscheinlichkeit nicht einloesbar - drei unabhaengige Gruende, die ich VOR
dem ersten Vorschlag auf den Tisch lege:

1. **Die Finanzmarkt-Uebertragung des Critical Slowing Down (CSD) ist empirisch
   ueberwiegend gescheitert.** Guttal et al. (2016, *PLoS ONE*) finden vor
   Markt-Zusammenbruechen **kein** CSD und schliessen auf *stochastische* statt
   *bifurkatorische* Uebergaenge; nur "steigende Variabilitaet" bleibt, mit
   Falschalarm-Vorbehalt [sek]. Diks/Hommes/Wang (2019, *Empirical Economics*) pruefen
   vier Krisen und bleiben bestenfalls gemischt [sek]. Der einzige krypto-native
   Fachaufsatz ist ein **Negativbefund** (arXiv 2607.27070: Fruehwarnsignale sind ueber
   sieben Perp-Liquidationskaskaden *ereignis-heterogen*) - R3 zitiert ihn bereits als
   Grund, warum K-34 kein Vorhersage-Gate auf Einzelkaskaden setzt.
2. **Der Rolling-Window-Schaetzer hat ein effektives N, das kaum jemand ausrechnet.**
   Kendall-tau auf einer aus ueberlappenden Fenstern der Laenge `w` gebildeten
   Indikatorreihe hat `n_eff ~ T/w`, nicht `T-w`. Beim Literatur-Default `w = T/2`
   sind das **zwei**. Das ist die H-07/GL-012-Fehlerklasse in neuer Metrik (C.12).
3. **Der Selektionsfehler der Literatur.** Boettiger & Hastings (2012, *Proc. R. Soc. B*)
   nennen ihn beim Namen: EWS-Studien waehlen Systeme aus, *weil* dort ein Uebergang
   stattfand ("Prosecutor's Fallacy") [sek]. Wer post hoc auf den 19.08.2026 schaut,
   begeht ihn - und C.9/DEC-44 (n=1-Extrapolation) hat das Programm schon einmal teuer
   bezahlt.

**Konsequenz: ich schlage kein Fruehwarn- und kein Richtungssignal vor.** Was ich
vorschlage, ist die Rueckseite der Disziplin - der Teil, den sie sauber hinbekommt und
den dieses Programm nachweislich braucht: die **Recovery-Rate** (Resilienz gemessen NACH
einer Stoerung, nicht prognostiziert VOR einer), die **sequentielle Detektion** mit
anytime-valid Garantie, der **Nulleffekt-Zensus der EWS-Familie**, und die
**Change-Point-Operationalisierung der REZENZ-Klausel**. Drei von vier sind reine
Enabler. Keiner beansprucht eine bps-Kante, keiner braucht GPU (DEC-57), keiner braucht
Daten ausserhalb des Bestands plus der in PRD 7.1 ohnehin vorgesehenen Backfills.

> **Klassen-Hinweis.** Das PRD kennt nur P/W/E (3.2). "R" und "X" stammen aus dem
> Exkurs-Brief. Registriert wuerde ein X-Paket am ehesten als **WP** - WP-4/5/6 sind
> genau dieses Format (eine Frage, ein binaerer Befund, Konsequenz vorab fixiert).

---

## X-OEKO-1 - RECOVER: Relaxationsrate des Aktivitaets-/Liquiditaetszustands nach Schockstunden

**Methode + Primaerliteratur.** Die tragfaehigste Groesse der Resilienz-Oekologie ist
nicht das Fruehwarnsignal, sondern die **Erholungsrate nach einer Stoerung**. van Nes &
Scheffer (2007, *Am. Nat.* 169(6), *Slow Recovery from Perturbations as a Generic
Indicator of a Nearby Catastrophic Shift*) zeigen ueber sechs Modelle, dass die
Rueckkehrrate nach einer kleinen Stoerung ein generischer Resilienz-Indikator ist [sek];
Scheffer et al. (2009, *Nature* 461:53-59) fuehren sie als eine der drei generischen
Signaturen [sek]; Dakos et al. (2012, *PLoS ONE* 7(7):e41010) liefern den
Schaetzer-Werkzeugkasten [sek]. Der Schaetzer ist elementar: nach dem Stoerungszeitpunkt
wird `A_t = A_inf + (A_0 - A_inf) exp(-lambda t)` gefittet (aequivalent der
AR(1)-Koeffizient des Post-Ereignis-Residuums, `lambda = -ln phi`); Kennzahl ist die
Halbwertszeit `T_half = ln2/lambda`. Der in der Literatur oft uebersehene Punkt:
`lambda` ist nicht nur ein Skalar, sondern potentiell eine **Zustandsvariable**.

**Uebertragung auf den Bestand.**
- **Strom:** ausschliesslich **WP-0-Bar-Cache** (1-min, 10.054 Cache-Tage, 14,4 Mio Bars,
  SHA-256-gepinnt, F.2). **Kein L2, kein Nachladen, keine Optionskette.**
- **Zustandsvariablen (vorab fixiert, keine Auswahl nach dem Sehen):**
  `A1 = log(n_trades/min)`, `A2 = log(px_high/px_low)`. Beides sind Cache-Spalten.
- **Symbole:** alle 5, gepoolt; Symbol-Zellen berichtend (H-20-Muster).
- **Ereignis-Definition: WOERTLICH aus H-20 geerbt, kein neuer Parameter.**
  Stunden-Log-Rendite aus `px_last`; Stunden mit <45 Minutenbars sind kein Kandidat;
  `sigma_h = 1,4826 x Rolling-MAD` ueber 720 vorangehende Stunden (min. 360), strikt
  kausal; Ereignis bei `|r_h| >= 3,5 sigma_h`; je Symbol nur das erste Ereignis in 24 h.
  Ich importiere keine Schwelle - ich erbe eine vorregistrierte Maschinerie, die
  nachweislich laeuft (GL-026: 1.044/962 Ereignisse, 0 wegen Datenqualitaet verworfen).
- **Messfenster:** `t0..t0+24h`, 5-Minuten-Aggregate. **Keine Rendite, kein Vorzeichen** -
  das ist die harte Abgrenzung zu H-20.
- **Horizont:** keiner (Messung). **Klasse: X (Enabler)** fuer Arm (a); **R** nur als
  getrennt zu registrierende Folge, falls Arm (b) besteht.

**Struktureller Nulleffekt (C.4).** Gross und leicht zu uebersehen: wer auf einen Gipfel
selektiert und danach den Rueckgang misst, misst zuerst **Regression zur Mitte**. Auf
einem stationaeren AR(1) liefert dieselbe Prozedur exakt `lambda_null = -ln(phi_0)` -
weit ueber null, ohne jede Resilienz-Interpretation. Kalibrierung zweistufig, beide
Pflicht: (1) analytisch `lambda_null` aus dem unbedingten AR(1)/HAR-Fit derselben Reihe;
(2) empirisch und urteilstragend: stationaerer Block-Bootstrap (Politis & Romano 1994,
Blocklaenge nach Politis & White 2004 - R4-Kanon) erzeugt Surrogate mit identischer
Randverteilung **und** ACF, auf die die *identische* Ereignis-Selektion und derselbe Fit
laufen; 1.000 Reps -> Verteilung von `lambda_null` und `Var(lambda_null)`.
Urteilstragend ist nie `lambda` selbst, sondern **(a)** `T_half` mit CI als deskriptive
Konstante (kein Gate) und **(b)** `Var(lambda_beob)/Var(lambda_null)` als Gate. Ohne (2)
waere das ein garantiertes Schein-PASS - die H-11/DEC-31-Falle.
**Zweite Nulleffekt-Quelle, als bindendes Etikett:** alle Aussagen sind bedingt darauf,
dass ein Schock stattfand. X-OEKO-1 sagt nichts ueber die Wahrscheinlichkeit eines
Schocks und darf nie so zitiert werden (Prosecutor's Fallacy, Boettiger & Hastings [sek]).

**Feasibility (DEC-51: alpha 0,05 einseitig, Power 0,80, z = 2,4865).**
- **Cluster-Einheit:** UTC-**Ereignistag** (DEC-51 Punkt 3; identisch mit H-20, weil die
  5 Symbole ihre Schockstunden weitgehend teilen - die L-6-Lehre ist eingebaut).
- **N GEMESSEN, nicht geschaetzt:** GL-026 weist **403 Ereignistage** (OOS-1) und
  **362** (OOS-2) aus. Das ist das beste N, das dieses Programm auf einer Ereignisfrage
  je hatte.
- **Arm (a):** `d = 2,4865/sqrt(403) = 0,124 SD` bzw. `= 0,131 SD` (eigene Herleitung);
  Arm (a) ist ohnehin deskriptiv, die Zahl zeigt nur, dass das CI eng wird.
- **Arm (b):** `SE(ln Var) = sqrt(2/361) = 0,0744`; `2,4865 x 0,0744 = 0,185` in log ->
  detektierbares **Varianz-Verhaeltnis 1,20** (eigene Herleitung). Das Design sieht mit
  Power 0,80 einen 20-%-Ueberschuss der Ereignis-zu-Ereignis-Streuung ueber der
  Surrogat-Null. **Ob 20 % die richtige Groessenordnung ist, ist UNBELEGT** - die einzige
  Fachaussage zur Heterogenitaet (arXiv 2607.27070) ist qualitativ und beruht auf
  **sieben** Ereignissen [sek]. Deshalb traegt Arm (a) den Wert des Pakets.
- **REZENZ (C.18):** die H-20-Fenster stammen aus 2026-08; fuer X-OEKO-1 werden die zwei
  juengsten disjunkten Fenster **vor dem Lauf** neu geschnitten und schriftlich
  festgestellt (PRD 9.3 Punkt 6), Endpunkt = letzter Manifest-DONE-Tag. Der Bar-Cache
  ist bis heute lueckenlos (B.16) - anders als jede L2-basierte Resilienz-Messung.

**Rechenbudget.** GL-026 rechnete die gesamte H-20-Maschinerie in **95 s** (rc=0). Plus
~2.000 Exponentialfits je Zustandsvariable und 1.000 Bootstrap-Reps je Fenster:
**20-60 min CPU, <4 GB RAM, keine GPU.** T0/T1 Sandbox, T2/T3/T7 Nutzer-PC.

**Nicht-Duplikat-Nachweis.**
- **D.12/H-20 (naechster Eintrag):** H-20 misst `y = -sign(r_event) x Summe Log-Renditen
  t0+2h..t0+24h` - eine **vorzeichenbehaftete Renditegroesse**. X-OEKO-1 misst die
  Relaxationsrate einer Aktivitaets-/Spannenreihe, ohne Rendite und ohne Vorzeichen.
  Keine gemeinsame Zelle, keine gemeinsame Teststatistik. Die D.12-Klausel "keine
  Sigma-/Horizont-/Luecken-Nachsuche" ist eingehalten: ich variiere keinen dieser drei
  Parameter, ich lasse die Renditefrage vollstaendig weg.
- **R3-K-35 SLIP-ZENSUS (PRD 9.1 nachrangig):** misst Buch-Resilienz (Large 2007) auf
  **L2** und scheitert an der REZENZ-Luecke. X-OEKO-1 benutzt kein L2 - genau deshalb
  existiert er. Falls WP-3/K-35 je gebaut wird, ist Arm (a) dort ein billiger Zusatzpass.
- **B.8/WP-6 (DEC-47/48):** WP-6 hat die Renormalisierung der Options-Quote nach dem
  19.08. an **genau einem Tag** gemessen ("binnen Minuten bis max. ~2 h") - eine
  n=1-Aussage in der von C.9/DEC-44 gebrandmarkten Form. X-OEKO-1 macht daraus eine
  Verteilung ueber ~765 Ereignistage, auf dem Perp-Bein (die Options-Quote-Reihe
  existiert nur fuer die WP-6-Fenster, F.2).
- **H-19 (DRIFT):** monotone Kalenderzeit-Drift von Tape-Deskriptoren. Keine
  Ueberschneidung.
- **CROSSDOMAIN_PARK:** kein Eintrag betrifft Recovery-Raten; der naechste, IC-NET-1
  (Turnover als Stress-Fruehindikator), ist ein *Fruehindikator* ueber einer nicht
  existierenden Basis-Strategie ("Overlay-ueber-Nichts") - X-OEKO-1 ist eine
  Nach-Schock-Messung ohne Overlay-Anspruch.

**Entscheidungsrelevanz.**
- **PASS Arm (a)** (immer erreichbar, es ist eine Messung): gemessene Halbwertszeit der
  Aktivitaets-/Liquiditaets-Renormalisierung mit CI, je Symbol und Aera. Folgen: (i) die
  frei gesetzte "24-h-Kill-Regel nach einer 3,5-sigma-Stunde", die R3-K-34 ausdruecklich
  als *ungemessen* benennt, bekommt eine Herleitung oder wird widerlegt; (ii) B.8 wird
  von n=1 zu einer Verteilung gehaertet; (iii) jedes Fill-/Slippage-Modell auf
  `STRESS_ABS` bekommt eine gemessene Erholungszeit statt einer Annahme.
- **PASS Arm (b)** (Var-Verhaeltnis >= 1,20 in **beiden** Fenstern, gleiches Vorzeichen,
  Cluster-Bootstrap-p <= 0,05): Resilienz ist eine Zustandsvariable. Naechster Schritt:
  **getrennt zu registrierende** R-Hypothese, die die Praemien-Klasse
  (A5/H-26-Short-Vol-Sizing) darauf konditioniert - **nie** ein Richtungssignal.
- **DROP Arm (b):** die Erholungsrate ist mechanische Regression zur Mitte; die
  Resilienz-Uebertragung als Zustandsvariable ist fuer diesen Bestand erledigt
  (D-Eintrag). Arm (a) bleibt geliefert - dieses Paket kann nicht wertlos enden.

**Fixtures (C.5/DEC-39, drittes nach 3.3.5).** *Positiv:* Aktivitaetsreihe mit
injizierter **ereignis-abhaengiger** Relaxationsrate (`lambda` alterniert 2:1, gesteuert
von einem verborgenen Zwei-Zustands-Prozess) - beide Arme muessen die injizierten Werte
im CI zurueckgewinnen, das Varianz-Verhaeltnis muss ausschlagen. *Negativ:*
GARCH(1,1)-Reihe mit **konstantem** `lambda` und fetten Raendern - Verhaeltnis ~1,0.
*Adversarial:* i.i.d.-Reihe **ohne jede Autokorrelation** mit derselben
Gipfel-Selektion; sie erzeugt maximale Regression zur Mitte, also grosses `lambda` -
**das Gate MUSS durchfallen**, sonst ist die Surrogat-Kalibrierung kaputt.

**Risiko-Etikett.** Arm (a): **Enabler** (Wert sicher, N=765 Ereignistage).
Arm (b): **Blick wert** (Mechanismus plausibel, Effektgroesse UNBELEGT, einziger
Fachbeleg ein Heterogenitaets-Negativbefund mit N=7).

---

## X-OEKO-2 - ANYTIME: sequentielle Detektion mit anytime-valid Garantie

**Methode + Primaerliteratur.** Sequentielle Detektion ist die Antwort der Statistik -
und der oekologisch-klimatologischen Regime-Shift-Literatur, die sie importiert hat -
auf genau die Lage dieses Programms: **Daten wachsen kalendarisch, und man moechte
schauen, ohne das Fehlerniveau zu zerstoeren.** Klassiker: Wald (1945) SPRT; Page (1954)
CUSUM; in der Klimaliteratur Rodionov (2004, *GRL* 31:L09204, sequentieller t-Test /
STARS), der ausdruecklich mit Echtzeit-Signalisierung wirbt [sek]. Moderne Fassung:
**Test-Martingale / e-Werte.** Howard, Ramdas, McAuliffe & Sekhon (2021, *Ann. Statist.*
49(2):1055-1080) zeit-uniforme Konfidenzsequenzen [sek]; Gruenwald, de Heide & Koolen
(2024, *JRSS-B* 86(5):1091-1128, "Safe Testing") - e-Wert-Tests behalten Typ-I-Kontrolle
unter **optional continuation** [sek]; Vovk & Wang (2021, *Ann. Statist.*
49(3):1736-1754) - e-Werte sind **durch Mittelung unter beliebiger Abhaengigkeit**
kombinierbar [sek]; e-BH uebertraegt das auf FDR unter beliebiger Abhaengigkeit [sek].
Kern in einer Zeile: `P(sup_t E_t >= 1/alpha) <= alpha` (Ville) - man darf jederzeit
schauen und jederzeit stoppen.

**Uebertragung.** Methodenneutral. Validiert auf (i) synthetischen Fixtures und (ii) den
nach **DEC-53** ohnehin zu speichernden **Cluster-Serien** - der e-Prozess ist genau aus
diesen Artefakten berechenbar, was DEC-53 zum perfekten Vorbau macht. Zielhypothesen:
die gesperrten Faeden **H-21** (bis 2026-12-27), **H-26** (bis ~Mitte November 2026),
**H-13** (kein Datum), **A5** und jeder Options-Kandidat mit kalendarisch wachsendem
Fenster. **Horizont:** keiner. **Klasse: X (Enabler).**

**Struktureller Nulleffekt.** Er IST hier die Frage und wird **gemessen, nicht
behauptet** (L-2/R4 1.0). (1) Naives wiederholtes Schauen - Armitage, McPherson & Rowe
(1969, *JRSS-A* 132:235-244) zeigen die Inflation der Falsch-Positiv-Rate bei
wiederholten Tests auf akkumulierenden Daten [sek]; **die Zahlenwerte werden NICHT
importiert, sondern auf den Fixtures gemessen** (L-1). (2) Der e-Prozess: die empirische
Ueberschreitungsrate von `sup_t E_t >= 1/alpha` ueber >= 100.000 Nullpfade muss
`<= alpha` bleiben. Verfehlt sie das, faellt der Vorschlag.

**Feasibility - und der ehrlich gerechnete Preis (eigene Herleitung).**
Normal-Mischungs-e-Wert mit Prior `N(0, 1/rho)`:

```
E_n = sqrt(rho/(n+rho)) * exp(S_n^2 / (2(n+rho))),   ablehnen bei E_n >= 1/alpha
=> |S_n|/sqrt(n) >= sqrt( ((n+rho)/n) * (2 ln(1/alpha) + ln((n+rho)/rho)) )
```

Mit `alpha = 0,05` (`ln(1/alpha) = 2,9957`), ausgewertet am geplanten Horizont `n`:

| Tuning | Schranke (z) | + 0,8416 (Power 0,80) | N-Kostenfaktor gegen z = 2,4865 |
|---|---|---|---|
| `rho = n`   | 3,656 | 4,498 | **3,27** |
| `rho = n/4` | 3,082 | 3,924 | **2,49** |
| `rho = n/9` | 3,036 | 3,878 | **2,43** |
| `rho = n/16`| 3,062 | 3,904 | **2,47** |

Optimum bei `rho ~ n/9..n/12`; **der Preis der anytime-valid Garantie ist Faktor 2,4-3,3
in N** gegenueber dem Fixed-N-Test der DEC-51-Konvention. Die Zahl gehoert offen auf den
Tisch, weil sie den Vorschlag fast toetet - und ihn dann doch nicht toetet:

1. **Fuer datengesperrte Hypothesen wird N mit Kalenderzeit bezahlt, und der Harvester
   laeuft ohnehin.** Die knappe Ressource ist nicht N, sondern die **Zahl der Schuesse**:
   H-26 hat heute genau einen (Fixed-N bei 210 `done_days`, Urteil danach append-only).
   Ein sequentielles Design hat unbegrenzt viele Blicke bei garantiertem alpha.
2. **Frueher Stopp bei grossem Effekt** (klassischer SPRT-Gewinn, Wald 1945 [sek]):
   Faktor 2,4 ist der Worst-Case, nicht der Erwartungswert.
3. **Der eigentliche Gewinn: die Fenster-Kombination.** L-17 haelt fest, dass der
   DEC-52-Retro-Check Auflage (iii) nicht nachrechnen konnte und ersatzweise
   **Stouffer/Fisher als *Obergrenze* der Evidenz** verwenden musste. e-Werte aus zwei
   Fenstern kombinieren **exakt** - Produkt unter sequentieller Bedingung,
   arithmetisches Mittel unter *beliebiger* Abhaengigkeit (Vovk & Wang 2021 [sek]).
   Keine Unabhaengigkeitsannahme, keine Obergrenze. Dasselbe gilt fuer die zweistufige
   FDR (DEC-22) und fuer die von WP-10(A) ausdruecklich geforderte
   **abhaengigkeitsrobuste** Ueber-Familien-Korrektur: e-BH liefert genau das [sek].

**N/REZENZ:** n/a (Methoden-Enabler); Kalibrierung auf >= 100.000 Pfaden. Die
Retro-Anwendung auf abgeschlossene Laeufe dient **ausschliesslich** der
Boundary-Kalibrierung - **bindend: kein gefallenes Urteil wird beruehrt** (C.1).

**Rechenbudget.** 10^5-10^6 Pfade, vektorisiert: **<30 min CPU, <2 GB RAM, keine GPU.**
T0/T1 vollstaendig sandbox-lauffaehig.

**Nicht-Duplikat-Nachweis.**
- **`m8_bocpd.py` (naechster Code-Verwandter):** CODE_MAP fuehrt ihn als LEGACY-V1 mit
  **bekanntem, bewusst nicht gefixtem** Shape-Mismatch-Bug (DEC-14); DEC-14 haelt
  woertlich fest, dass eine kuenftige BOCPD-Verwendung eine NEUE Hypothese mit eigener
  Reimplementierung waere. X-OEKO-2 ist **kein BOCPD**: BOCPD schaetzt online die
  Run-Length-Posterior einer Segmentierung, X-OEKO-2 ist ein **Test-Martingal auf einer
  vorregistrierten Nullhypothese** mit Ville-Garantie. Verschiedene Objekte,
  verschiedene Garantien; C.11 (Modul != Strategie) eingehalten, kein Modul
  rehabilitiert.
- **DEC-52 (BESCHLOSSEN):** wird **nicht ersetzt und nicht geaendert.** DEC-52 regelt
  zwei Fenster bei fixem N; X-OEKO-2 ist eine *zusaetzliche, optionale* Designform, die
  eine Hypothese **vor** dem Lauf waehlt und dann mit Grenze, `rho`, Stoppregel und
  `constants_hash` vorregistriert. Designwechsel nach dem Sehen von Daten waere
  Torpfosten-Verschiebung und ist ausdruecklich verboten.
- **R4_METHODIK_INFRA:** enthaelt Bootstrap, HAC, DSR, MinTRL, FDR - per Volltextsuche
  (`SPRT|CUSUM|sequenti|anytime|alpha.spend`) **kein einziges sequentielles Verfahren**.
  Echte Luecke.
- **CROSSDOMAIN_PARK/PRD:** kein Eintrag betrifft sequentielle Inferenz; der naechste
  (IC-CLIM-3, SRS-Bootstrap-Rauschkorrektur auf AnEn-Analoglaeufen) ist eine andere
  Frage.

**Entscheidungsrelevanz.** **PASS** (Kalibrierung gruen, Kostenfaktor bestaetigt): eine
vorregistrierbare Designform steht bereit; H-21/H-26/H-13/A5 koennen als sequentielle
statt Ein-Schuss-Fixed-N-Designs aufgesetzt werden; DEC-52-Zweige und die
DEC-22-Ueber-Familie bekommen eine exakte, abhaengigkeitsrobuste Kombinationsregel statt
Stouffer/Fisher-Obergrenze (L-17 geschlossen). Braucht eine eigene DEC. **DROP**
(Kalibrierung rot oder Kostenfaktor > ~4 auf realistischen Stichproben): dokumentiert,
dass anytime-valid Inferenz auf diesen Stichprobengroessen zu teuer ist; das Programm
hoert dann auf, "warten und nochmal schauen" mitzudenken.

**Fixtures.** *Positiv:* Gauss-Strom mit injiziertem Design-Effekt - der e-Prozess muss
mit der geplanten Power stoppen und die erwartete Stoppzeit muss unter dem Fixed-N-Plan
liegen. *Negativ:* reiner Nullstrom - ueber 100.000 Pfade und unbegrenzt viele Blicke
Ueberschreitungsrate `<= alpha`. *Adversarial:* Nullstrom mit **starker Autokorrelation
und fetten Raendern** (GARCH), auf dem die i.i.d.-Fassung nachweislich ueberverwirft -
nur die block-/cluster-robuste Fassung darf kalibriert sein (L-6-Lehre).

**Risiko-Etikett. Enabler.** Kein Kanten-Anspruch. Das Risiko ist nicht "wirkt nicht",
sondern "Preis zu hoch" - und der Preis steht oben, vor dem Bau.

---

## X-OEKO-3 - EWS-NULL: Nulleffekt-Zensus der Fruehwarn-Indikatorfamilie (WP-4-Muster)

**Methode + Primaerliteratur.** Die EWS-Familie (Scheffer et al. 2009 [sek]; Dakos et al.
2012 [sek]) berechnet auf gleitenden Fenstern Indikatoren - Lag-1-Autokorrelation,
Varianz, Schiefe, DFA-Exponent, Spektralverhaeltnis - und liest deren **Trend**
(Kendall-tau) als Naeherung an einen Kipppunkt. Drei quantifizierbare Artefakte:
(i) Fensterlaenge und Detrending-Bandbreite sind freie Parameter, deren Variantenzahl
`K` die Selektions-Decke hebt (K-0.3); (ii) die Indikatorreihe ist per Konstruktion
stark autokorreliert, das nominale Kendall-tau-p ist wertlos; (iii) Prosecutor's Fallacy
(Boettiger & Hastings 2012 [sek]). Der **zweite Arm** kommt aus derselben Disziplin und
ist fuer stark verrauschte Systeme der theoretisch passendere Ast: Dakos, van Nes &
Scheffer (2013, *Theor. Ecol.* 6(3):309-317, *Flickering as an early warning signal*)
zeigen, dass in rausch-dominierten Systemen nicht CSD, sondern **Flickering**
(Bimodalitaet, Sprung zwischen Attraktoren, steigende Varianz ohne steigende
Autokorrelation) den Uebergang ankuendigt [sek] - passgenau zu Guttal 2016 [sek].

**Der Vorschlag ist ein ZENSUS im WP-4/5/6-Muster:** eine Frage, ein binaerer Befund,
Konsequenz jedes Ausgangs vorab fixiert. **Keine Kante, keine Prognosefrage.**

**Uebertragung.** WP-0-Bar-Cache zu Tageswerten (realisierte Tagesvol, Tages-`n_trades`,
Tages-Buy/Sell-Anteil); plus die oeffentlich nachladbare **Funding-Historie** (PRD 7.1 /
V-1, ~35.000 Records, Minuten Download) und **DVOL** (WP-9-Backfill, ~5,4 Jahre).
5 Perp-Symbole + BTC/ETH-DVOL. Ziel-Ereignisse ausschliesslich **`STRESS_ABS`**
(DEC-56); keine eigene Stress-Definition (DEC-55/56 verbieten das).
**Horizont:** keiner. **Klasse: X (Enabler-Messung).**

**Struktureller Nulleffekt - der Zensus misst nichts anderes.**
1. **Effektives N des Rolling-Trend-Schaetzers (eigene Herleitung, der wichtigste Wert
   des Pakets).** `n_eff ~ T/w`, nicht `T-w`. Mit `T ~ 2.350` Tagen (BTC ab 2020-03-25,
   B.16):

   | `w` | `n_eff = T/w` | einseitig 95-%-kritisches Kendall-tau | `SE(AC1) ~ 1/sqrt(w)` |
   |---|---|---|---|
   | 1.175 (= T/2, Literatur-Default) | 2 | nicht definiert | 0,029 |
   | 500 | 4,7 | ~0,73 | 0,045 |
   | 250 | 9,4 | ~0,50 | 0,063 |
   | 100 | 23,5 | ~0,29 | 0,100 |

   Die Klemme ist damit numerisch benannt: kurze Fenster kaufen `n_eff` und zerstoeren
   die Indikator-Praezision, lange umgekehrt. Beim Literatur-Default ist die Frage ein
   **struktureller A-priori-DROP nach C.12/GL-012** - vor jedem Datenlauf feststellbar.
   Der Zensus klaert, ob im Bereich `w = 100..250` beides zugleich reicht.
2. **Empirische Nullverteilung** von Kendall-tau je Indikator, 1.000 Surrogate je Serie
   in **drei** Familien: (a) stationaerer Block-Bootstrap, (b) GARCH(1,1)-Surrogate,
   (c) ARFIMA(0,d,0)-Surrogate. **Ohne (c) ist der Zensus wertlos**, weil Langgedaechtnis
   allein steigende Rolling-AC1 erzeugt.
3. **Empirische Selektions-Decke (R4 1.1d - der bei H-11 fehlende Schritt):** die
   **komplette** Variantenpipeline (`K = |w| x |Detrending| x |Indikatoren|`,
   Groessenordnung 100-150) laeuft auf dem Null-Fixture; die Verteilung des **Bestwerts**
   ist die Decke. Vergleichsanker: Bailey/LdP, K=100 -> `E[max SR] = 1,13` (K-0.3).

**Feasibility.** Cluster-Einheit: Kalendertag fuer die Surrogat-Bloecke,
`STRESS_ABS`-Episode fuer den Vorlaufvergleich. **N:** `STRESS_ABS` (99-Perzentil der
Gesamthistorie) -> Groessenordnung ~23 Tage bei ~2.350, plus die zwei namentlich
genannten; nach Episoden-Verklebung erwartet das PRD selbst **6-10 Episoden** (4.3). Das
ist klein - und genau deshalb ist dies **kein Signal-Test**, sondern ein
Nulleffekt-/Erreichbarkeits-Zensus. Wer aus 6-10 Episoden ein EWS-Gate baut, wiederholt
H-10 (N_pointer=0) und H-13 (2 Snapshot-Tage). **Effektgroesse:** in der Oekologie werden
CSD-Amplituden `Delta AC1 ~ 0,1-0,3` berichtet [sek, Groessenordnung aus Sekundaerquelle,
**nicht** aus dem Volltext]; gegen `SE(AC1) ~ 0,10` bei `w=100` ist das SNR ~1-3 pro
Fenster - grenzwertig, was den Zensus rechtfertigt statt ihn zu erledigen.
**REZENZ:** Lauf ueber die Gesamthistorie und getrennt ueber die zwei juengsten Fenster;
urteilstragend ist die rezente Haelfte.

**Vorab fixierte Entscheidungsregel (binaer).** Liegt das beobachtete Kendall-tau
**jedes** Indikators vor `STRESS_ABS`-Episoden im zentralen 90-%-Band **aller drei**
Surrogat-Familien, wird die EWS-/CSD-Rolling-Window-Familie fuer diesen Bestand als
**a priori tot** eingetragen (neuer D-Eintrag). Liegt **genau einer** ausserhalb und
ueberlebt die Selektions-Decke, wird **er allein** Kandidat fuer eine getrennt zu
registrierende R-Hypothese - keine Nachsuche in der Familie.
**Zweiter Arm (deskriptiv, ohne Urteilslast):** Flickering statt CSD - Hartigan-Dip- und
Silverman-Bandbreitentest auf Bimodalitaet der Zustandsverteilung plus
Verweilzeit-Verteilung zwischen Modi. Dieser Arm ist gegen das `n_eff`-Problem **immun**,
weil er auf der Rohstichprobe schaetzt, nicht auf einer Rolling-Trend-Reihe.

**Rechenbudget.** ~120 Varianten x 1.000 Surrogate x ~10 Serien x ~2.350 Punkte,
vektorisiert: **1-3 h CPU, <8 GB RAM, keine GPU.** Sandbox-tauglich.

**Nicht-Duplikat-Nachweis.**
- **D.6/H-06 (Permutation Entropy, DROP)** - naechster im Geiste. H-06 testete **ein**
  Vorhersage-Gate (`rho >= 0,30`) und verfehlte es um Faktor ~20. X-OEKO-3 testet **kein
  Vorhersage-Gate**, sondern misst Nullverteilung und Selektions-Decke; ein PASS heisst
  hier nicht "Signal existiert", sondern "diese Metrik liegt ausserhalb ihrer eigenen
  Null". Permutation Entropy ist im Indikatorsatz **nicht enthalten** (D.6 verbietet es).
- **D.9/H-10 (Pointer-Days, N=0):** keine Synchronisationsmetrik, keine
  Multi-Serien-Gleichrichtungsregel; der PARK-Hinweis zur
  GLK-/Event-Synchronization-Matrix ist nicht beruehrt, weil ich H-10 nicht erweitere.
- **D.12/H-20:** keine Renditegroesse, kein Nach-Schock-Fenster.
- **R3-K-34 LEV-STATE (PRD 9.1 nicht aufgenommen):** dort OI/Funding-Zustand gegen die
  Abwaerts-Semivarianz des Folgetags mit RV-gematchter Baseline. Hier keine
  Folgetags-Zielgroesse, keine Semivarianz, kein Zustands-Dezil. Die vom Review benannte
  K-34-Schwaeche ("einziger R3-Kandidat ohne hergeleiteten Rauschboden") ist hier der
  **Gegenstand** statt der Luecke.
- **CROSSDOMAIN IC-NET-1** (PARK, "Overlay-ueber-Nichts"): dort Netzwerk-Aggregat als
  Fruehindikator ohne Basis-Strategie und ohne Schwelle. Hier weder Netzwerkmetrik noch
  Overlay noch Fruehindikator-Behauptung.

**Entscheidungsrelevanz.** **PASS:** genau ein Indikator wird Kandidat fuer eine
getrennte R-Registrierung, alle anderen sind erledigt. **DROP:** neuer D-Eintrag
"EWS-/CSD-Rolling-Window-Familie auf diesem Bestand a priori tot" mit der
`n_eff`-Tabelle als Begruendung - denselben Dienst hat WP-4 dem Market-Making-Zweig
geleistet (D.1), in einem Nachmittag. **In beiden Faellen** faellt die gemessene
Selektions-Decke fuer Rolling-Window-Variantenpipelines ab - eine Konstante, die dem
Programm heute fehlt.

**Fixtures.** *Positiv:* Ornstein-Uhlenbeck mit **langsam sinkender Rueckstellkraft**
(kanonisches CSD-Modell) - AC1 und Varianz muessen steigen, tau ausserhalb der Null.
*Negativ:* ARFIMA(0; d=0,4; 0) **ohne jeden Uebergang**; sie erzeugt steigende
Rolling-AC1 allein aus Langgedaechtnis - das Verfahren MUSS innerhalb der Null bleiben
(wer nur gegen weisses Rauschen testet, besteht dieses Fixture nicht). *Adversarial:*
rauschgetriebenes Bistabil-Modell mit **Flickering, aber ohne CSD** - der CSD-Arm muss
schweigen, der Flickering-Arm ausschlagen.

**Risiko-Etikett. Enabler** - mit der ehrlichen Ansage: **der wahrscheinlichste Ausgang
ist ein DROP der ganzen Familie.** Genau deshalb billig gehalten und genau deshalb wert.

---

## X-OEKO-4 - CPREZENZ: Change-Point-Detektion als Operationalisierung der REZENZ-Klausel

**Methode + Primaerliteratur.** Die oekologisch-klimatologische Regime-Shift-Literatur
hat saubere Werkzeuge fuer eine Frage, die dieses Programm heute per Kalender-Konvention
beantwortet: **wo genau endet das alte Regime?** Rodionov (2004, *GRL* 31:L09204) STARS -
sequentieller t-Test mit Cutoff-Laenge `l`, Regime-Shift-Index `RSI`, Niveau `p`, spaeter
um Prewhitening gegen Rotrauschen ergaenzt (Rodionov 2006) [sek]; Killick, Fearnhead &
Eckley (2012, *JASA* 107(500):1590-1598) PELT - exakte Multi-Change-Point-Loesung in
linearer Zeit [sek]; Barry & Hartigan (1993) bzw. Fearnhead (2006) fuer die bayesische
Produkt-Partition-Fassung [sek]. Der Konfound ist ebenso gut dokumentiert:
**Langgedaechtnis und Strukturbrueche sind wechselseitig verwechselbar** (Granger & Hyung
2004, *J. Empirical Finance*) [sek] - jeder Detektor feuert auf einem ARFIMA-Prozess ohne
jeden Bruch.

**Uebertragung.** Tagesreihen: (i) **Funding** je Symbol aus dem oeffentlichen Backfill
(~6 Jahre), (ii) **DVOL** BTC/ETH (WP-9, ~5,4 Jahre), (iii) realisierte Tagesvol und
Tages-Aktivitaetskonzentration aus dem **WP-0-Bar-Cache** (5-6 Jahre, 5 Symbole).
**Horizont:** keiner. **Klasse: X (Enabler)** mit R-Nebenprodukt (die Partition selbst).
Zwei Lieferungen:
- **(L1) REZENZ-Verdikt.** Fuer jede geplante urteilstragende Fenstergrenze wird
  geprueft, ob sie einen detektierten Change Point **ueberspannt**. Tut sie es, ist das
  Fenster nicht homogen und muss neu geschnitten werden - oder die Hypothese ist
  aera-deskriptiv. Das ist die mechanische Fassung dessen, was Review R1-R4 als **L-16**
  rueget ("Die REZENZ-Klausel wird formal, nicht inhaltlich angewendet").
- **(L2) Regime-Partition** fuer den R4-1.1c-Gleichheitstest. R4 verlangt fuer Klasse P
  statt eines Differenztests **gleiches Vorzeichen in ALLEN K Regimen bei abgesenkter
  Per-Regime-Schwelle**; heute waeren diese K Regime frei gewaehlt, L2 liefert sie
  deterministisch und vorregistriert.
- **Anti-Snooping-Klausel (bindend, C.17):** die Partition wird **nie** auf derselben
  Reihe erzeugt, auf der getestet wird. Fuer eine Praemien-Hypothese wird auf
  Vol-/Funding-Zustandsreihen partitioniert, nicht auf der Praemien-PnL - sonst waere L2
  eine Entdeckungszellen-Verletzung.

**Struktureller Nulleffekt.** **Ein Change-Point-Detektor findet immer Change Points.**
Je Serie werden ARFIMA(0,d,0)- und GARCH(1,1)-Modelle gefittet und 1.000 **bruchfreie**
Surrogate simuliert; alle drei Detektoren laufen darauf. Ergebnis: Nullverteilung von
(a) der **Anzahl** gefundener Change Points und (b) der Segment-Mittelwertsdifferenz an
der staerksten Bruchstelle. Ein Change Point zaehlt nur, wenn er (i) das 95-Perzentil der
Surrogat-Differenz uebersteigt **und** (ii) von **mindestens 2 von 3** Detektoren
innerhalb eines vorab fixierten Toleranzfensters gefunden wird (Toleranz =
**Design-Parameter, keine Schwelle**, mit vorab fixierter Konsequenz, 3.3.10-Muster).

**Feasibility.** Cluster-Einheit: das **Segment** (nicht der Tag) - Beobachtungen
innerhalb eines Regimes teilen den Regime-Schock. Detektierbare Bruchgroesse (eigene
Herleitung): `delta_det = 2,4865 * sigma * sqrt(2/m)`; bei Tages-log-RV und `m = 90`
Tagen `= 0,371 sigma`; bei Monats-Mittel-Funding und `m = 12` Monaten
`= 1,015 sigma_Monat`. **`sigma_Monat` des Funding ist UNGEMESSEN** - V-1/V-3 und WP-7
liefern es; bis dahin ist die Funding-Achse ein UNBELEGT-Eintrag und nicht
registrierbar, die RV-Achse ist sofort rechenbar. Serienlaengen: ~2.350 Tage
(Bar-Cache), ~2.100 (Funding-Backfill), ~1.980 (DVOL ab 2021-04 [sek, ueber R3 zitierte
Deribit-API-Doku]). **REZENZ:** X-OEKO-4 *erzeugt* die REZENZ-Aussage; die Klausel ist
Ergebnis, nicht Nebenbedingung.

**Rechenbudget.** PELT ist linear in `n`, STARS ein Ein-Pass-t-Test. 3 Detektoren x
~12 Serien x 1.000 Surrogate x ~2.300 Punkte: **<1 h CPU, <2 GB RAM, keine GPU.**

**Nicht-Duplikat-Nachweis.**
- **H-19 (C-19 DRIFT, STATIONAER-GENUG)** - naechster Verwandter und zugleich das
  staerkste Argument FUER X-OEKO-4. H-19 testet **monotone** Kalenderzeit-Drift
  (`|rho_p| >= 0,30` in beiden OOS, gleiches Vorzeichen) und findet 0/15 Zellen. Aber
  H-19 haelt selbst fest, dass die D3-Aktivitaets-Konzentration "einen einmaligen
  Uebergang bis ~2022->2024" zeigt - **ein abrupter Uebergang, den ein Monotonie-Test
  per Konstruktion nicht lokalisieren kann.** X-OEKO-4 lokalisiert ihn. Verschiedene
  Alternativhypothesen (monoton vs. abrupt), verschiedene Teststatistiken, keine
  gemeinsame Zelle; der H-19-Befund wird nicht angetastet.
- **`m8_bocpd.py` / C-08:** in `wave3_survey` als "blockiert / tote Spur" gefuehrt, Bug
  per DEC-14 bewusst nicht gefixt, jede kuenftige Verwendung braucht laut DEC-14 eine
  neue Hypothese mit eigener Reimplementierung. **Konsequenz hier, ausdruecklich:**
  Primaerdetektor ist **PELT** (offline, exakt, deterministisch), zweiter **STARS**; eine
  bayesische Fassung nur als dritte Meinung und nur als **Neubau in `research/`**
  (Welle-2-Muster: C-07 kam als `research/c07_pe/`, nicht als L3-Modul). Kein
  Legacy-Import (T6).
- **DEC-55/56 (`STRESS_REL`/`STRESS_ABS`):** beides Perzentil-Schnitte auf der Tagesvol,
  also **Punktmengen**. X-OEKO-4 liefert **Intervalle mit Grenzen** auf einer anderen
  Frage (wo endet ein Regime, nicht welcher Tag ist extrem). Die Design-Parameter der
  Stress-Fixtures werden **nicht** angetastet.
- **CROSSDOMAIN: Changepoint auf `lambda1(t)`** wurde im `econophysics-rmt`-Scan
  ausdruecklich verworfen ("C-08-BOCPD-Territorium"). Unterschied: X-OEKO-4 beansprucht
  **keine Alpha-Frage** und benutzt den Change Point nicht als Signal, sondern als
  **Fenster-Schnitt-Regel** - eine Registry-Disziplin-Frage. Diese Verwendung existiert
  nirgends im Programm.

**Entscheidungsrelevanz.** **PASS** (Detektoren trennen sich nachweisbar von der
Langgedaechtnis-Null): jede kuenftige Fensterwahl bekommt eine mechanische Begruendung,
L-16 ist geschlossen, A1/A3/A4 und jede Klasse-P-Registrierung koennen die
R4-1.1c-Gleichheitspruefung auf einer nicht frei gewaehlten Partition fahren; braucht
eine DEC (Fenster-Schnitt-Regel). **DROP** (nicht von der ARFIMA-Null trennbar): belegt,
dass REZENZ auf diesen Reihen nicht datengetrieben operationalisierbar ist - die
Kalender-Konvention bleibt, ab dann als *bewusste* Konvention mit Beleg statt als
stillschweigende Annahme. Auch das schliesst L-16, nur andersherum.

**Fixtures.** *Positiv:* stueckweise konstante Reihe, 3 injizierte Brueche von
`1,0 sigma` bei Segmentlaenge 200 - alle muessen von >= 2 von 3 Detektoren in Toleranz
gefunden werden. *Negativ:* ARFIMA(0; d=0,45; 0) **ohne Bruch** - die Zahl gueltig
gezaehlter Change Points muss ~0 sein (ein Detektor, der hier feuert, ist fuer diesen
Bestand unbrauchbar; das ist der ganze Punkt). *Adversarial:* **ein** echter Bruch plus
starkes Langgedaechtnis - der echte Bruch muss gefunden werden, ohne die Artefakte
mitzuzaehlen.

**Risiko-Etikett. Enabler.** Mittleres Risiko, dass die Langgedaechtnis-Null die
Detektoren schluckt - das waere dann selbst der Befund.

---

## Rangliste

| Rang | ID | Warum hier | Startbar | Klasse |
|---|---|---|---|---|
| **1** | **X-OEKO-1 RECOVER** | Bestes N des Programms auf einer Ereignisfrage (**403/362 Ereignistage, GEMESSEN**, GL-026), null Nachladeaufwand, **kein neuer Parameter** (Ereignis-Definition aus H-20 geerbt), Rechenzeit Minuten. Arm (a) kann nicht wertlos enden: er haertet die n=1-Aussage B.8 zu einer Verteilung und liefert die Herleitung der frei gesetzten 24-h-Kill-Regel. | **ja** | X (+R als Folge) |
| **2** | **X-OEKO-2 ANYTIME** | Greift die strukturelle Pathologie an (drei gesperrte Faeden, ein Schuss je Hypothese, Fenster-Kombination nur als Stouffer/Fisher-*Obergrenze*, L-17) und schliesst eine echte Luecke: R4 kennt kein sequentielles Verfahren. Preis vorab ausgerechnet (Faktor 2,4-3,3 in N). | **ja** (Simulation) | X |
| **3** | **X-OEKO-3 EWS-NULL** | WP-4-Muster: ein Nachmittag, binaerer Befund, wahrscheinlichster Ausgang ein D-Eintrag, der eine ganze Fremddisziplin-Familie schliesst. Liefert nebenbei die gemessene Selektions-Decke fuer Rolling-Window-Pipelines. | **ja** | X |
| **4** | **X-OEKO-4 CPREZENZ** | Schliesst L-16, haengt aber am Funding-/DVOL-Backfill (V-1/WP-9) und braucht eine eigene DEC; die RV-Achse allein ist sofort rechenbar, die Funding-Achse ist UNGEMESSEN. | teilweise | X (+R) |

**Ueber-Familie (DEC-22).** Nur X-OEKO-1 Arm (b) traegt ein alpha-artiges Gate; 2/3/4
tragen binaere Zensus-Befunde oder Kalibrier-Bedingungen. Laufen X-OEKO-1(b) und ein
spaeterer R-Kandidat aus X-OEKO-3 gemeinsam, ist **vor** dem Lauf eine Ueber-Familie zu
registrieren. **Sequenz:** X-OEKO-1 und X-OEKO-3 parallel (beide nur Bar-Cache, keine
gemeinsame Teststatistik, zusammen <4 h CPU); X-OEKO-2 jederzeit (sandbox-lauffaehig, von
keinem Datenpaket abhaengig); X-OEKO-4 erst nach V-1/WP-9.

---

## Was ich NICHT vorschlage und warum

1. **CSD als Fruehwarn- oder Richtungssignal.** Drei unabhaengige Gruende, jeder allein
   ausreichend: (i) die Fachliteratur ist fuer Finanzmaerkte ueberwiegend negativ
   (Guttal 2016; Diks/Hommes/Wang 2019; krypto-nativ arXiv 2607.27070 - alle [sek]);
   (ii) `n_eff = 2` beim Literatur-Default `w = T/2` -> struktureller A-priori-DROP
   (C.12); (iii) ein Sub-Tages-Richtungssignal ist nach K-0.1 arithmetisch tot
   (perfektes 1-s-Orakel: 0,71 bp gegen 11 bp Wand). Was bleibt, ist der
   Nulleffekt-Zensus X-OEKO-3 - ausdruecklich ohne Signal-Anspruch.

2. **Maker/Taker-Populationsdynamik (Lotka-Volterra) aus L2-Nachfuellraten und
   Trade-Aggression.** Ehrlich gerechnet an der Datenlage gescheitert, nicht am Konzept:
   rezenz-konform ist ausschliesslich `orderbook.1000` ab Juni 2026, heute **~2,5
   Monate**, nur BTC/ETH (SOL/BNB/XRP: 35 Tage); die 500er-Aera hat bei ETH ein
   **2-Jahres-Loch**, bei BTC ein **10-Monats-Loch**, plus einen Formatbruch, der beide
   Aeren getrennt auszuweisen zwingt (F.1, R3-K-35). Ein Raeuber-Beute-Modell braucht
   **mehrere Zyklen** der langsamen Variablen; auf 2,5 Monaten ist die Zyklenzahl nicht
   einmal definierbar, und C.18 verbietet, das Urteil auf die Archiv-Aera zu stuetzen.
   Zusaetzlich hat das PRD den einzigen L2-Kandidaten (R3-K-35) bereits **nachrangig**
   gestellt, exakt mit diesem Argument (9.1); ein datenhungrigeres Modell auf derselben
   Basis waere die S4/S5-Falle (D.16). **Entsperr-Bedingung, falls spaeter aufgegriffen:**
   >= 18 Monate durchgehende `orderbook.1000` auf >= 3 Symbolen **plus** ein
   vorregistriertes Identifikationsargument, dass Nachfuellrate und Aggression nicht
   bloss zwei Seiten derselben Volumenreihe sind (sonst ist die "Kopplung" eine
   Identitaet).

3. **BOCPD-Wiederbelebung (`m8_bocpd.py`, C-08).** DEC-14: Bug bewusst nicht gefixt,
   Modul nie isoliert getestet, `wave3_survey` fuehrt C-08 als "blockiert / tote Spur",
   und jede kuenftige Verwendung waere eine NEUE Hypothese mit eigener Reimplementierung.
   Deshalb ist der Primaerdetektor in X-OEKO-4 PELT, der zweite STARS, und eine
   bayesische Fassung darf nur als dritte Meinung und nur als Neubau in `research/`
   auftreten (T6-Legacy-Import-Sperre).

4. **Permutation Entropy und jede entropiebasierte Regime-Metrik.** D.6: H-06 verfehlt
   das PRE-Gate um Faktor ~20 (max 0,0145 gegen 0,30) - "die Grundannahme selbst traegt
   nicht". Der Indikatorsatz von X-OEKO-3 enthaelt sie deshalb **nicht**, obwohl die
   EWS-Standardliteratur sie fuehrt.

5. **Cross-Stream-Synchronisation / Event-Synchronization-Matrizen als Fruehwarnung.**
   D.9: H-10 findet im gesamten 79-Tage-Fenster **N=0** Pointer-Tage (Existenz-DROP).
   Der PARK-Hinweis zur GLK-/Event-Synchronization-Matrix verlangt zwingend Dedup gegen
   H-10; ich erweitere H-10 nicht und schlage keine Synchronisationsmetrik vor.

6. **Tail-Aftermath in jeder neuen Fassung.** D.12 verbietet
   Sigma-/Horizont-/Luecken-Nachsuche ohne neue Vorregistrierung. X-OEKO-1 variiert
   **keinen** dieser drei Parameter - es misst eine andere Zielgroesse (Relaxationsrate
   statt Rendite) auf derselben, unveraenderten Ereignismenge.

7. **Raeumliche EWS-Indikatoren** (Kefi et al. 2014: raeumliche Varianz,
   Patch-Groessenverteilung, Korrelationslaenge [sek]). Sie brauchen eine raeumliche
   Dimension; der naechste Ersatz waere der Symbol-Querschnitt - und H-12 hat gemessen,
   dass der zweite Eigenmodus dort **praktisch vollstaendig delokalisiert** ist (IPR
   0,169 gegen theoretisches Minimum 1/6 = 0,167, D.10). Es gibt keine raeumliche
   Struktur, die langsamer werden koennte. Struktureller A-priori-DROP.

8. **Buch-Resilienz nach Large (2007) als eigener Vorschlag.** Gehoert R3-K-35, das im
   PRD 9.1 bereits eingeordnet ist; ein Duplikat waere wertlos. X-OEKO-1 vermeidet die
   Kollision, indem es den Bar-Cache statt L2 benutzt.

9. **Varianz/AC1 als Querschnittsfaktor der Klasse W.** Waere ein Vol-Anomalie-Faktor
   unter anderem Namen und liegt in der geplanten Kohorte **F-XSEC1** (A3, PRD 5.3).

10. **Potential-Landschafts-Rekonstruktion / "Abstand zum Kipppunkt"** (Livina & Lenton,
    DFA-basierte Potentialanalyse [sek]). Setzt Stationaritaet um einen Attraktor im
    Fenster voraus. Auf einer Reihe, deren Minuten-Impact nachweislich **permanent** ist
    (B.14/H-24: gleichzeitiger IC ~+0,53, Forward-IC30 ~-0,015, ueber zehn Halbjahre
    stabil), ist das Potential per Konstruktion flach - es gibt keinen Attraktor, dessen
    Kruemmung messbar waere. Struktureller A-priori-DROP (C.12).

11. **Ruin-/Reservierungs-Modell auf den Insurance Fund** (PARK-Hinweis, Bruecke
    evt-actuarial -> mechanism-design). Nicht meine Disziplin, und die Datenlage ist die
    H-21-Falle: `bybit/insurance` **43 Tage** (F.1). Ich melde es weiter statt es zu
    duplizieren.

---

## Belegstatus

| Beleg | Status | Bemerkung |
|---|---|---|
| Scheffer et al. 2009, *Nature* 461:53-59 | **[sek]** | DOI 10.1038/nature08227 ueber Suchtreffer; Volltext nicht abrufbar |
| Dakos et al. 2012, *PLoS ONE* 7(7):e41010 | **[sek]** | Zitat bestaetigt; `journals.plos.org` **gesperrt**. "Delta AC1 ~ 0,1-0,3" ist damit **im Volltext UNBELEGT** und oben so markiert |
| van Nes & Scheffer 2007, *Am. Nat.* 169(6) | **[sek]** | Titel/Journal/Kernaussage ueber Suchtreffer |
| Dakos, van Nes & Scheffer 2013, *Theor. Ecol.* 6(3):309-317 | **[sek]** | DOI 10.1007/s12080-013-0186-4; Flickering-Kernaussage aus Zusammenfassung |
| Boettiger & Hastings 2012, *Proc. R. Soc. B* 279(1748):4734-4739 | **[sek]** | DOI 10.1098/rspb.2012.2085; Prosecutor's Fallacy aus Abstract |
| Guttal et al. 2016, *PLoS ONE* 11(1):e0144198 | **[sek]** | Kernbefund (kein CSD; stochastische statt kritische Uebergaenge) aus Suchtreffer-Zusammenfassung |
| Diks, Hommes & Wang 2019, *Empirical Economics* | **[sek]** | DOI 10.1007/s00181-018-1527-3; vier Krisen; Ergebnisrichtung **nur qualitativ** belegt (Springer gesperrt) |
| arXiv 2607.27070 (EWS ereignis-heterogen, 7 Kaskaden) | **[sek], doppelt** | programm-intern in R3 zitiert; eigener Abruf: `arxiv.org` **gesperrt**; N=7 aus der R3-Zitation |
| Rodionov 2004, *GRL* 31:L09204 (STARS) | **[sek]** | Zitat + Verfahrensbeschreibung ueber Suchtreffer; `pmel.noaa.gov` gesperrt -> **RSI-/`l`-/`p`-Parameterwerte UNBELEGT**, im Bau zu verifizieren |
| Rodionov 2006 (Prewhitening) | **[sek]** | nur ueber Verweis in Suchtreffern |
| Killick, Fearnhead & Eckley 2012, *JASA* 107(500):1590-1598 | **[sek]** | DOI 10.1080/01621459.2012.737745 bestaetigt |
| Barry & Hartigan 1993 / Fearnhead 2006 (BCP) | **[sek]** | Standardzitate, nicht einzeln verifiziert |
| Granger & Hyung 2004, *J. Empirical Finance* | **[sek]** | nicht einzeln verifiziert |
| Wald 1945 (SPRT), Page 1954 (CUSUM) | **[sek]** | Klassiker, nicht einzeln verifiziert |
| Armitage, McPherson & Rowe 1969, *JRSS-A* 132:235-244 | **[sek]** | Existenz + Kernaussage bestaetigt; **Zahlenwerte bewusst NICHT importiert, sondern gemessen** (L-1) |
| Howard, Ramdas, McAuliffe & Sekhon 2021, *Ann. Statist.* 49(2):1055-1080 | **[sek]** | Titel/Band/Seiten bestaetigt |
| Gruenwald, de Heide & Koolen 2024, *JRSS-B* 86(5):1091-1128 | **[sek]** | Titel/Band/Seiten und "optional continuation" bestaetigt |
| Vovk & Wang 2021, *Ann. Statist.* 49(3):1736-1754 | **[sek]** | Titel/Band/Seiten und "Mittelung unter beliebiger Abhaengigkeit" bestaetigt |
| Wang & Ramdas, e-BH (FDR mit e-Werten) | **[sek]** | nur ueber Verweis; **Jahr/Venue nicht verifiziert** |
| Kefi et al. 2014 (raeumliche EWS) | **[sek]** | ueber Suchtreffer-Titel (PLoS ONE) |
| Livina & Lenton (Potentialanalyse) | **[sek]** | nur dem Namen nach; **Jahr/Venue UNBELEGT** |
| Politis & Romano 1994 / Politis & White 2004 | programm-intern | bereits R4-Kanon (1.1a) |
| **Alle Programm-Zahlen** (403/362 Ereignistage; 1.044/962 Ereignisse; 95 s; B.1-B.17; K-0.1..K-0.7; DEC-51..57; H-20-Wortlaut; F.1-F.3) | **primaer** | `gate_log.md` (GL-026), `hypothesis_registry.md`, `decisions.md`, `PRD_SCINANCE3.md`, `ERKENNTNIS_KOMPENDIUM.md` |
| **Alle Formeln in den Feasibility-Abschnitten** | **eigene Herleitung** | Mischungs-e-Wert-Schranke + Kostentabelle; `n_eff = T/w`; `d = 2,4865/sqrt(N)`; `SE(ln Var) = sqrt(2/(n-1))`; `delta_det = 2,4865 sigma sqrt(2/m)` |

**Egress-Bilanz:** `arxiv.org`, `journals.plos.org`, `link.springer.com`,
`www.pmel.noaa.gov` je `EGRESS_BLOCKED`. **Kein Volltext lesbar**; alle externen Belege
stammen aus Suchtreffer-Metadaten und sind als `[sek]` gefuehrt. Nichts geraten.

---

## Kurzfassung fuer den Orchestrator

Meine Disziplin liefert hier **kein Fruehwarnsignal** - die Literatur ist dagegen, die
Arithmetik des Rolling-Window-Schaetzers ist dagegen, die Friktionskurve ist gegen jedes
Sub-Tages-Richtungssignal. Was sie liefert, ist die Rueckseite:

- **X-OEKO-1 (RECOVER)** - einziger Vorschlag mit gemessenem, grossem N (403/362
  Ereignistage), null Nachladeaufwand, keinem neuen Parameter, und einem Arm, der nicht
  wertlos enden kann: er macht aus der n=1-Aussage in B.8 eine Verteilung und liefert
  die Herleitung der heute frei gesetzten 24-h-Kill-Regel.
- **X-OEKO-2 (ANYTIME)** - groesster Hebel auf die Programm-Pathologie (drei gesperrte
  Faeden, ein Schuss je Hypothese, L-17-Evidenzobergrenze), mit dem ehrlichsten
  Preisschild (Faktor 2,4-3,3 in N, oben vorgerechnet).
- **X-OEKO-3 (EWS-NULL)** - ein Nachmittag im WP-4-Muster, wahrscheinlichster Ausgang
  ein D-Eintrag; genau deshalb machen, damit dieselbe Fremddisziplin nicht in zwei
  Jahren ein drittes Mal vorgeschlagen wird.
- **X-OEKO-4 (CPREZENZ)** - schliesst L-16, haengt am Backfill, braucht eine DEC.

*Ende S2_OEKOLOGIE_KRITISCHE_UEBERGAENGE.md*
