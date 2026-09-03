# S5 - AKTUAR / RUIN-THEORIE / PRAEMIENPRINZIPIEN

**Phase:** 3b Wissenschafts-Exkurs (Scinance 3.0) | **Stand:** 2026-09-03
**Pflichtlektuere gelesen:** `survey/ERKENNTNIS_KOMPENDIUM.md` (A-F vollstaendig),
`PRD_SCINANCE3.md` (1, 2, 3.1-3.9, 4.1-4.4, 5.1-5.5, 6, 9.1-9.3),
`edge-research-v3/results/CROSSDOMAIN_PARK.md`, `.../CROSSDOMAIN_PRD.md`.
**Vier Vorschlaege, alle Klasse X (Enabler / Nulleffekt-Kalibrierung), keiner verbraucht einen
Alpha-Slot, keiner braucht GPU, keiner ist gerichtet. Read-only im Repo.**

---

## 0. Der Befund, der die eigene Rangliste umdreht

Die Disziplin bepreist seit Lundberg (1903) genau zwei Groessen: was das Tragen eines Risikos
kosten muss, und wieviel Kapital das Tragen ueberlebt. Das ist woertlich die Klasse P. Beim
Nachrechnen der Uebertragung faellt aber sofort auf:

> **Unter Normalitaet kollabieren ALLE klassischen Praemienprinzipien auf den Sharpe.**
> Standardabweichungsprinzip `H = E[X]+b*SD(X)` -> `b = prem/sigma`. Wang-Transform bei
> normalem Risiko: Mittelwertverschiebung `lambda*sigma` -> `lambda = prem/sigma`.
> Exponentialprinzip -> `alpha = 2*prem/sigma^2` - **und das ist exakt der
> Cramer-Lundberg-Anpassungskoeffizient `R = 2mu/sigma^2`** der Diffusionsnaeherung.

Drei Konsequenzen, die alles Weitere strukturieren:

1. **Ein "aktuarisch fairer Preis" als neuer Massstab neben dem Sharpe existiert nicht.** PRD
   3.6 hat den Sharpe wegen `MinTRL > Historie` (K-0.2: SR 0,5 -> 24,7 a gegen 5-6 a Bestand)
   bereits als nicht urteilstragend eingestuft; jedes Prinzip erbt diese Untestbarkeit in
   seinem Gauss-Anteil. Neu ist ausschliesslich der **Tail-Anteil** (X-AKT-1). Das degradiert
   meinen eigenen Kopf-Vorschlag auf Rang 4.
2. **Praemienprinzip und Ruin-Theorie sind dieselbe Zahl** (`alpha_implizit` vs. `R`), solange
   die Verlustverteilung leicht-schwaenzig ist. Ihr Verhaeltnis ist ein Tail-Diagnostikum, kein
   zweiter Massstab.
3. **Fuer schwer-schwaenzige Verluste existiert `R` gar nicht** (Standardresultat: fuer
   Pareto-Schaeden gibt es keinen Anpassungskoeffizienten [sek]). Dann gilt statt `psi(u) <=
   e^{-Ru}` die subexponentielle Asymptotik von Embrechts/Veraverbeke (1982) mit POTENZabfall.
   Damit wird "leichter oder schwerer Tail" zu einer harten binaeren Kapitalfrage, die das
   Programm bisher nirgends stellt (X-AKT-2).

Der PARK-Hinweis *"Ruin-Theorie/aktuarische Reservierung auf den Insurance Fund"*
(CROSSDOMAIN_PARK, Cross-Domain-Hinweise) ist ausdruecklich offen und wird als X-AKT-3
eingeloest - mit einem Befund, der ihn erst tragfaehig macht: **`adlAlert` ist auf der
Bybit-Linear-WS ein Phantom-Topic** (`ret_msg='error:handler not found,topic:adlAlert'`,
DEC-08; primaer: `src/bybit_edge/recorder/recording_engine.py` Z. 286-295). Eine
ADL-Wahrscheinlichkeit ist aus einem Ereignis-Feed auf dieser Boerse **nie** messbar. Der
Ruin-Prozess des Insurance Fund ist der einzige Weg zu der Zahl, die PRD 3.3.9c als
Pflichtzeile verlangt und heute mit einem unbelegten Platzhalter ("1 %/Jahr", Review R1-R4 6.3)
fuellt.

---

## 1. X-AKT-4 - Buehlmann-Straub-Credibility auf den Funding-Sortierschluessel

**Rang 1. Klasse X. Etikett: Enabler.**

**Methode.** Buehlmann (1967, ASTIN Bulletin 4, 199-207) zeigt, dass die Credibility-Formel die
beste linearisierte Kleinste-Quadrate-Naeherung an die exakte Bayes-Prognose ist;
Buehlmann/Straub (1970, "Glaubwuerdigkeit fuer Schadensaetze", Mitteilungen der Vereinigung
Schweizerischer Versicherungs-Mathematiker 70, 111-133) erweitern das auf **heterogene
Exposure-Gewichte** - der Fall, in dem Risiken unterschiedlich lange Historie haben. Lehrbuch:
Buehlmann/Gisler (2005), *A Course in Credibility Theory*, Springer [sek]. Schaetzer:
`mu_i^cred = z_i*X_quer_i + (1-z_i)*mu_kollektiv`, `z_i = w_i/(w_i+k)`, `k = s^2/a`, `a =
Var(Theta)` (Heterogenitaet der wahren Mittel), `s^2 = E[sigma^2(Theta)]` (Rauschen innerhalb
eines Risikos), `w_i` = Beobachtungsgewicht.

**Uebertragung.** Strom: der oeffentlich nachladbare `GET /v5/market/funding/history`
(A1-Daten, PRD 5.1: ~9.300 Calls, ~31 min) plus `panel_1d` aus WP-7. Aufloesung:
Funding-Settlement, aggregiert auf Kalenderwoche. Symbole: point-in-time-Universum aus WP-7
(`K` = 117..300). Horizont: horizontfrei. **Klasse X.** Das Objekt: A1s Sortierschluessel ist
heute `f_taeglich_i = funding_sum_i/n_Tage` ueber **3-7 Tage** (PRD 5.1(b)), also ein
ungeschrumpfter Stichprobenmittelwert aus 9-21 Achtstunden-Settlements - der klassische
Erfahrungstarifierungs-Fall. Drei Lieferungen:

- **(L1) Gemessene Zerlegung `a` vs. `s^2`.** `k = s^2/a` ist die Beobachtungszahl, ab der ein
  Symbol Gewicht `z = 0,5` traegt.
- **(L2) Herleitung eines heute GESETZTEN Design-Parameters.** PRD 5.1 Feasibility-Kill (4)
  fixiert "Autokorrelation des Sortierschluessels ueber eine Woche unter **0,30** ->
  Registrierung unterbleibt" und etikettiert die 0,30 ausdruecklich als "Design-Parameter
  (keine Schwelle)". Fuer einen Schluessel, der ein persistentes wahres Mittel mit
  unabhaengigem Messfehler schaetzt, ist die Woche-zu-Woche-Autokorrelation in erster Ordnung
  **gleich der Reliabilitaet `z`**. Damit ist 0,30 aequivalent zu `w_i/(w_i+k) >= 0,30`, also
  `k <= 2,333*w_i`, bei `w_i = 9..21` also **`k <= 21..49`**. Aus einem gesetzten Skalar wird
  eine messbare Aussage ueber die Kollektivstruktur (L-1/C.12-konform).
  *Gueltigkeitsbedingungen, die mitgeprueft werden:* (i) wahres Mittel ueber eine Woche
  naeherungsweise konstant, (ii) Messfehler benachbarter Wochen unkorreliert - beide am Fixture
  quantifiziert, nicht behauptet.
- **(L3) Die exakte Obergrenze des Enablers - Ehrlichkeitszeile.** **Bei GLEICHEN `w_i` ist die
  Schrumpfung eine gemeinsame affine Transformation des Querschnitts und laesst jede
  Rangordnung - und damit den Rank-IC - exakt unveraendert.** Der Enabler wirkt ausschliesslich
  in dem Mass, in dem die Historienlaengen HETEROGEN sind (Neu-Listings,
  8-Wochen-Einschlussgrenze aus WP-7). Die eigentliche Messung ist also die Verteilung von
  `w_i` und die daraus folgende Streuung von `z_i`; ist `z_i` praktisch konstant, ist der
  Enabler wertlos - sauberer binaerer Befund.

**Struktureller Nulleffekt (C.4), exakt.** `a = 0` (alle Symbole teilen EIN wahres Mittel) =>
`k = unendlich` => `z_i = 0` => geschrumpfter Schluessel konstant => Querschnitts-IC exakt 0
und Schluessel-Autokorrelation 0. Das ist zugleich ein von `SD_null(IC_t)` UNABHAENGIGER
Feasibility-Test der Querschnittsklasse: `SD_null` sagt "wieviel Rauschen", die Zerlegung sagt
"gibt es ueberhaupt sortierbare Heterogenitaet".
*Die Falle, die gemessen werden MUSS (L-2b-Klasse):* der uebliche unverzerrte Schaetzer fuer
`a` ist eine Differenz zweier Varianzschaetzer, kann NEGATIV werden und wird konventionell bei
0 abgeschnitten - eine Trunkierung, die `a` und damit `z` unter der Null systematisch nach oben
verzerrt. Genau die Fehlerklasse, an der WP-7s v1-`rho_quer`-Schaetzer gestorben ist. Vorab
fixiert: die Nullverteilung von `a_hat` wird am Null-Fixture MIT realistischer
Vol-Heterogenitaet (lognormal, `sigma_log = 0,6`, K = 170 - identisch zum WP-7-Null-Fixture)
gemessen; haengt `z_quer` dort von der Vol-Streuung statt von `a` ab, wird der Schaetzer
**nicht gebaut**.

**Feasibility / Power.** Cluster-Einheit **Kalenderwoche** (DEC-51 Pkt. 3), `N_cluster` = 52 je
Fenster / 104 gepoolt - identisch zu A1, keine neue Datenlage. Zweiseitige META-Frage (DEC-51
Pkt. 1): `alpha = 0,05` zweiseitig, `z = 2,8016`, Power 0,80. A-priori: `z_quer` 0,2-0,5, falls
die 0,30 aus PRD 5.1 eine sinnvolle Groessenordnung war - **die 0,30 ist selbst UNBELEGT**,
also wird nicht gegen sie gepowert, sondern die Zahl mit Bootstrap-CI ueber Wochen-Cluster
berichtet. Bindend ist nicht N, sondern ob `w_i` streut. **REZENZ (C.18):** urteilstragend
exakt A1s Fenster W1 = 2024-07-01..2025-06-30, W2 = 2025-07-01..2026-06-30; aeltere Historie
ist Aera-Profil. Da Neu-Listings im juengsten Regime am dichtesten sind, arbeitet die
REZENZ-Klausel hier FUER den Vorschlag. **Kein Alpha-Slot:** wird der geschrumpfte Schluessel
je als A1-Sortierschluessel verwendet, ist das eine ANDERE, vorab zu registrierende Hypothese;
sie erhoeht `K` von 3 auf 6 und damit die Selektions-Decke ueber die heutigen 0,60.
Post-hoc-Anwendung waere Torpfosten-Verschiebung.

**Rechenbudget.** CPU, Sekunden; ~0,3 Personentage Code; laeuft als Beifahrer in WP-7 (dieselbe
Panel-Maschinerie, dieselben Fingerabdruecke). **GPU 0** (DEC-57 trivial erfuellt). Speicher:
vernachlaessigbar.

**Nicht-Duplikat.** Naechster Nachbar **WP-7** (PRD 4.1): misst `SD_null(IC_t)` per
Permutation, also den Rauschboden; Credibility zerlegt die Schluessel-Varianz in Signal (`a`)
und Rauschen (`s^2`), also die Quelle. WP-7 kann nicht sagen, ob ein verfehlter IC an fehlender
Heterogenitaet oder an einem verrauschten Schaetzer liegt - die Zerlegung kann es. Zweiter
Nachbar **D.7** (Cross-Sectional Mean-Reversion auf N=5 erschoepft): dort war der strukturelle
Deckel `max|z| = sqrt(N-1)`, hier geht es um die Reliabilitaet eines Schaetzers. Kein
Shrinkage-/Credibility-Verfahren kommt in Kompendium A-F, im PARK-Register oder in R1-R4 vor.

**Entscheidungsrelevanz.** *PASS (Heterogenitaet vorhanden, `z_i` streut):* A1s
Feasibility-Kill (4) hat eine HERGELEITETE statt gesetzten Grenze; der geschrumpfte Schluessel
wird als zweiter, vorab registrierter Sortierschluessel mit korrigierter Selektions-Decke
aufgenommen. *DROP (`a_hat` nicht von 0 trennbar):* die Querschnitts-Praemie hat keine
sortierbare Symbol-Heterogenitaet - ein GL-012-Feasibility-Befund gegen A1s Querschnittsarm VOR
dem Lauf, ohne Alpha-Slot-Verbrauch. Beide Ausgaenge aendern etwas.

**Fixture-Paar (DEC-39/C.5).** *Positiv:* Panel mit `a > 0` und stark heterogenen
Historienlaengen (`w_i` 9..250), wahres Mittel je Symbol konstant - `z_i` muss sichtbar
streuen, der geschrumpfte Schluessel hoehere Rangkorrelation zum wahren Mittel haben als der
rohe. *Negativ:* Panel mit `a = 0`, identische wahre Mittel, lognormale Vol-Heterogenitaet
(`sigma_log = 0,6`) - `a_hat` im CI von 0, `z_quer ~ 0`, insbesondere KEINE Abhaengigkeit von
der Vol-Streuung. *Adversarial (3.3.5):* `a = 0`, aber `w_i` korreliert mit dem realisierten
Mittel (junge Symbole nach Listing-Pump) - der unkontrollierte Schaetzer MUSS ein scheinbares
`a > 0` melden, der kontrollierte nicht.

---

## 2. X-AKT-3 - Insurance Fund als beobachtbarer Ruin-Prozess; die ADL-Konstante fuer PRD
3.3.9c

**Rang 2. Klasse R/X. Etikett: Stufe 1 "Blick wert", Stufe 2 "spekulativ" (vertagt).**

**Methode.** Cramer-Lundberg-Ueberschussprozess `U(t) = u + c*t - S(t)` mit zusammengesetztem
Poisson-Schadenprozess (Lundberg 1903 [sek]; Cramer 1930 [sek]). Verallgemeinerung auf
Erneuerungsankuenfte: Sparre Andersen (1957), "On the collective theory of risk in case of
contagion between the claims", Transactions of the XVth International Congress of Actuaries,
Vol. 2, 219-227 - dessen eigene Motivation woertlich *"contagion, which may be characterized by
the property that a claim is more likely to occur shortly after another claim"* ist, also exakt
die Selbsterregung von Liquidationskaskaden. Ruinzeit/Defizit: Gerber/Shiu (1998), North
American Actuarial Journal 2(1), 48-72. Referenzwerk: Asmussen/Albrecher (2010), *Ruin
Probabilities*, 2. Aufl. [sek]. Reservierung: Mack (1993), "Distribution-free Calculation of
the Standard Error of Chain Ladder Reserve Estimates", ASTIN Bulletin 23(2), 213-225.
Boersen-Kontext, neu: Campbell/Hey/Moallemi/Nutz (2026), "Risk-Based Auto-Deleveraging",
arXiv:2603.15963 [sek, arxiv egress-gesperrt] - formuliert ADL als Minimierung des
Boersen-Verlustrisikos, wenn Margin und "other loss-absorbing resources" (= Insurance Fund)
nicht reichen. Chitra (2025, rev. 2026), "Autodeleveraging: Impossibilities and Optimization",
arXiv:2512.01112 [sek] - Trilemma Solvenz/Erloes/Fairness, "zero-loss socialization
impossible"; benennt ausdruecklich, dass es bis dahin **keine formale Studie von ADL** gab.

**Uebertragung.** Strom `bybit/insurance` (Kompendium F.1: 43 Tage Stand 2026-08-10;
`research/R3_EREIGNIS_STRUKTUR.md` Z. 28 rechnet auf **~66 Tage** Stand 2026-09-02 hoch).
Schema primaer aus `src/bybit_edge/recorder/storage.py` Z. 116-121: `(ts, coin, balance,
recv_ts)` bei ~1 s Takt - also eine **direkt beobachtete Ueberschuss-Zeitreihe `U(t)`**. Das
ist die einzige Stelle im gesamten Bestand, an der ein echter Ruin-Prozess sichtbar ist; alle
anderen Stroeme sind Preise und Fluesse. Symbol-los (USDT-Pool). Horizont: horizontfrei.
**Klasse R/X.**

- **Stufe 1 (nur `insurance`):** `Delta B` wird in praemienartige Zufluesse
  (Liquidationsueberschuss, Gebuehrenanteil) und schadenartige Abfluesse (Bad-Debt-Absorption)
  zerlegt; daraus Schadenhoehenverteilung der negativen Inkremente, Ankunftsprozess (Poisson
  vs. Sparre-Andersen-Erneuerung wegen Kaskadenclusterung), daraus `psi(B_jetzt)` ueber einen
  Kalenderhorizont. **`psi` IST die ADL-Wahrscheinlichkeit**, weil ADL per Konstruktion greift,
  sobald der Fonds den Fehlbetrag nicht mehr absorbiert (Campbell et al. 2026 [sek]).
- **Stufe 2 (Chain-Ladder, braucht `allLiquidation`): VERTAGT.** Die Verzoegerung zwischen
  Liquidationsereignis und Fonds-Dekrement erzeugt ein echtes Abwicklungsdreieck, auf das Mack
  (1993) einen verteilungsfreien Reservefehler fuer "ausstehende" (IBNR-artige)
  Liquidationsverluste liefert. Nicht jetzt: R3 fuehrt `allLiquidation` (~66 Tage)
  ausdruecklich als **fuer H-21 reserviert** und heute zu kurz. Erst nach Abschluss der
  H-21-Fenster (2026-12-27). Das vermeidet dieselbe N-Falle wie H-10/H-13.

**Die Vorfrage, die alles entscheidet (Irreversibilitaets-Regel 3.3.7 / L-10).** 66 Tage
enthalten mit hoher Wahrscheinlichkeit **null** Depletionsereignisse; null Schaeden =>
Raten-MLE 0 => `psi = 0` => uninformativ. Eine Registrierung darauf waere die dritte
Wiederholung des N-Fehlers. **Aber die Historie ist mutmasslich oeffentlich nachladbar**, und
3.3.7 verlangt genau diese Probe:
- Bybit fuehrt `GET /v5/market/insurance` [sek:
  `bybit-exchange.github.io/docs/v5/market/insurance`, Host **egress-gesperrt**, nur
  Suchtreffer]; laut demselben Treffer isolierter Pool im 1-Minuten-, geteilter Pool im
  24-Stunden-Takt. Ob HISTORIE oder nur Momentanstand: **UNBELEGT**.
- Bybit publiziert nach dem Februar-2025-Vorfall eine "Daily Insurance Fund Balance"-Seite mit
  echter Historie [sek, Host gesperrt]; Tiefe **UNBELEGT**.
- Binance: `GET /fapi/v1/insuranceBalance` plus oeffentliche "Insurance Fund History"-Seite
  [sek, `developers.binance.com` gesperrt]; Tardis fuehrt `insuranceBalance` **erst seit
  2026-03-17** [sek].

=> **V-AKT-1 (10-Minuten-Vorfrage, Nutzer-Maschine, keyfrei, Muster PRD 4.4):** liefert der
Endpunkt bzw. die Historienseite eine Zeitreihe, und reicht sie ueber **2025-10-10** und
**2026-08-19** zurueck (die beiden in DEC-56 namentlich fixierten `STRESS_ABS`-Tage)? *Vorab
fixierte Konsequenz:* **Nein** -> Stufe 1 nicht registrierbar, der WS-Sekundenstrom laeuft als
irreversibles Gut weiter (genau der Fall, den 7.2 "nur Irreversibles rechtfertigt einen
Dauerstrom" meint), Neubewertung bei 12+ Monaten. **Ja** -> Backfill (< 1 MB), Stufe 1
registrierbar.
*Messgrenze, vorab genannt:* eine TAGES-Bilanz kann eine untertaegige Depletion mit
Wiederauffuellung unsichtbar machen - und genau das war die Form des 10.10.2025. Der
Tages-Backfill liefert deshalb eine **Untergrenze** der Schadenzahl, der Sekundenstrom die
exakte Form fuer die Zukunft; beides wird getrennt ausgewiesen.

**Struktureller Nulleffekt (C.4), zwei exakte Komponenten.** *(a) Netto-Profit-Bedingung:* `c >
lambda*E[X]`. Bei Gleichheit (`rho = 1`) ist `psi(u) = 1` fuer jedes `u` - **der Nulleffekt ist
`psi = 1`, nicht 0; die naive Lesart hat das Vorzeichen falsch.** *(b) Selektions-Null der
Schadenzaehlung:* werden Schaeden aus negativen Inkrementen einer Bilanzreihe extrahiert,
erzeugt reines Mess-/Rundungsrauschen bereits "Schaeden". Der Nulleffekt wird per
Block-Bootstrap aus einer schadenfreien Surrogat-Bilanz mit identischer
Inkrement-Randverteilung erzeugt, **nie mit 0 angesetzt** (Muster identisch zu WP-10(A), PRD
4.3).

**Feasibility - die entscheidende Ehrlichkeitszeile.** **Eine ADL-Haeufigkeit ist als FREQUENZ
strukturell nicht schaetzbar.** Um eine Rate von 1 %/Jahr mit Power 0,80 bei `alpha = 0,05`
einseitig von 0 zu trennen, braucht ein Poisson-Zaehler die Groessenordnung `10^2..10^3`
Beobachtungsjahre - ein GL-012-A-priori-DROP fuer JEDEN zaehlbasierten Schaetzer, unabhaengig
von der Datenlage. Deshalb, und nur deshalb, ist der parametrische Ruin-Weg gangbar: er nutzt
die gesamte Inkrement-Verteilung statt nur der Ruin-Ereignisse. **Der Preis ist
Modellabhaengigkeit, und er wird ausgewiesen:** geliefert wird ein **Intervall unter benannter
Modellfamilie plus Sensitivitaet** (Poisson vs. Sparre-Andersen; leicht- vs. schwer-schwaenzige
Schadenhoehe), **nie eine Punktzahl**.
Cluster-Einheit **Kalendertag** (Inkremente teilen Tagesschocks); `N_cluster` = Backfill-Tage
(bei Historie ab 2025-02 ~580, bei 66 Tagen nicht registrierbar). Zweiseitig, `z = 2,8016`.
Kalibrierungs-Groessenordnung: Binance zog am 10.10.2025 **188 Mio. USD** aus dem Insurance
Fund [sek]; das Gesamtereignis liquidierte ~19 Mrd. USD ueber ~1,6 Mio. Konten [sek].
Bybit-Fondsgroesse und -Dekrement: **UNBELEGT - V-AKT-1**. **REZENZ (C.18):** urteilstragend
nur, wenn der Backfill 2025-10-10 UND 2026-08-19 enthaelt; ohne den 10.10.2025 enthaelt die
Stichprobe null Grossereignisse und die Extrapolation ist reine Modellprojektion - dann Etikett
"spekulativ", kein Verdikt.

**Rechenbudget.** V-AKT-1: Minuten (Nutzer-Maschine, Sandbox egress-gesperrt). Backfill < 1 MB.
Fit + Bootstrap: CPU-Minuten. ~1 Personentag Code. **GPU 0.** Positivkontroll-Vorschaltung
entfaellt (Laufzeit < 1 h, 3.3.8).

**Nicht-Duplikat.** **PARK IC-MECH-1** (ADL-Trigger-Antizipation) will ADL VORHERSAGEN, also
ein gerichtetes Sub-Tages-Signal - unter K-0.1 tot (perfektes 1-s-Orakel 0,71 bp gegen 11 bp).
X-AKT-3 will die **unbedingte Wahrscheinlichkeit als Risiko-Konstante**, horizontfrei, ohne
Kanten-Anspruch. **PARK IC-MECH-3** ist auf `adlAlert` blockiert (Daten-Passung 0) - X-AKT-3
braucht `adlAlert` ausdruecklich NICHT, weil das Topic ein Phantom ist. **Kompendium E.12**
(Kaskaden-Cockpit C-27..C-30): Kaskaden-DETEKTOREN auf Trades, kein Reservierungsmodell auf
einer Bilanzreihe. **H-21 (LIQ-TAG):** Informationsgehalt des Liquidations-LABELS; Stufe 1
fasst `allLiquidation` gar nicht an, Stufe 2 ist explizit dahinter vertagt. Der PARK-Hinweis
"Ruin-Theorie/aktuarische Reservierung auf den Insurance Fund" ist per Konstruktion Einloesung,
nicht Duplikat.

**Entscheidungsrelevanz.** *PASS (V-AKT-1 positiv, `psi` mit CI schaetzbar):* PRD 3.3.9c
bekommt statt "1 %/Jahr" ein gemessenes Intervall; der Erwartungswert-Abschlag jeder
Klasse-P-Registrierung (A1, A4, A5) wird gerechnet statt gesetzt, und WP-10(A)s Zeile
"Korrelation Praemien-PnL vs. Handlungsfaehigkeit des Betreibers" (Review R1-R4 6.7) bekommt
ihre Zielgroesse. *DROP (V-AKT-1 negativ):* 3.3.9c bleibt dauerhaft UNBELEGT und muss in jeder
P-Registrierung so etikettiert werden - besser als der heutige stille Platzhalter, und fuer 10
Minuten Aufwand.

**Fixture-Paar (DEC-39/C.5).** *Positiv:* simulierter Fonds, Poisson-Schaeden, `rho = 0,8`,
exponentielle Schadenhoehe - `R` und `psi(u)` muessen die analytische Loesung im CI treffen.
*Negativ:* monoton wachsende Bilanz plus Rundungsrauschen - der Schaetzer darf KEINE
Schadenrate > 0 melden. *Adversarial:* Pareto-Schadenhoehe (`xi = 0,4`), Fenster ohne
Grossschaden - der Schaetzer MUSS melden, dass kein Anpassungskoeffizient existiert, und darf
nicht aus der trunkierten Stichprobe ein endliches `R` zurueckgeben (Loud-Fail, C.14).

---

## 3. X-AKT-2 - Ruin-Kapital statt importierter MaxDD-Schwelle

**Rang 3. Klasse X. Etikett: Enabler / Berichtsgroesse.**

**Methode.** Lundberg-Ungleichung `psi(u) <= e^{-R*u}`, `R` positive Loesung von
`lambda*(M_X(R)-1) = c*R`. Diffusionsnaeherung `R ~= 2mu/sigma^2`, also `psi(u) =
exp(-2mu*u/sigma^2)` und **`u(eps) = (sigma^2/(2mu))*ln(1/eps)`**. Schwer-schwaenziger Fall:
fuer regulaer variierende Schaeden existiert `R` nicht [sek]; dann Embrechts/Veraverbeke
(1982), "Estimates for the probability of ruin with special emphasis on the possibility of
large claims", Insurance: Mathematics and Economics 1, 55-72: `psi(u) ~
(rho/(1-rho))*F_I_quer(u)` - **Potenz- statt Exponentialabfall.**

**Uebertragung.** **Keine neuen Daten.** X-AKT-2 ist ein Nachbereiter auf (a) den nach
**DEC-53** ohnehin pflichtgemaess geschriebenen Cluster-Serien jeder Klasse-P-Registrierung
(A1, A4) und (b) den vier taeglichen Praemien-Proxy-PnLs, die **WP-10(A)** ohnehin baut
(Funding-Carry, Perp/Future-Wedge, Short-Skew, Short-Vol). Horizontfrei. **Klasse X.**

**Warum das eine echte Luecke schliesst.** PRD 3.6 leitet den MaxDD-Boden aus `E[MaxDD] =
1,2533*sigma_ann*sqrt(T)` her (Magdon-Ismail et al. 2004 [sek]) und zeigt damit korrekt, dass
"MaxDD < 30 %" strukturell unerreichbar ist. **Diese Formel ist aber die driftlose Brownsche
Loesung: sie ignoriert `mu` vollstaendig** - fuer einen Prozess, der per Hypothese eine Praemie
traegt, ueberschaetzt sie den Drawdown - und sie waechst mit `sqrt(T)`, ist also als
Kapitalregel unbrauchbar (jede endliche Zahl reisst bei genuegend langem `T`). `u(eps)` ist
drift-bewusst und horizontunabhaengig. Mit PRD-eigenen Eingaben (9.2 C: `sigma_LS <= 104
bps/Woche` A1-Etikett-Grenze, 36 bps/Woche oekonomische Mindestmagnitude), also `sigma_ann =
0,0104*sqrt(52) = 7,50 %` und `E[MaxDD](T=5a) = 1,2533*0,0750*sqrt(5) = 21,0 %`:

| prem/Woche | SR_ann | `R = 2mu/sigma^2` | `u(1 %)` | `u(0,1 %)` | `E[MaxDD]`, T=5 a |
|---|---|---|---|---|---|
| 36 bp | 2,50 | 66,6 | **6,9 %** | 10,4 % | 21,0 % |
| 20 bp | 1,39 | 37,0 | **12,5 %** | 18,7 % | 21,0 % |
| 10 bp | 0,69 | 18,5 | **24,9 %** | 37,4 % | 21,0 % |
| 5 bp | 0,35 | 9,25 | **49,8 %** | 74,7 % | 21,0 % |

Der Befund: **die Rangordnung kippt.** Bei der Etikett-Grenzpraemie (36 bp, ein unplausibel
hoher Jahres-Sharpe von 2,5) ist das Ruin-Kapital 3,0-mal KLEINER als `E[MaxDD]`; bei den
Praemien, die das Programm realistisch erwartet (einstellige bp/Woche), 1,2- bis 2,4-mal
GROESSER. Eine importierte MaxDD-Zahl ist in beide Richtungen falsch, abhaengig von genau der
Groesse, die gemessen werden soll - die D.2/L-1-Fehlerklasse in einer Metrik, in der sie bisher
niemand gesucht hat.

**Struktureller Nulleffekt (C.4), exakt.** Unter der No-Arbitrage-Null der Klasse P (PRD
5.1(c): Funding-Cashflow exakt durch Preisdrift kompensiert) ist `mu = 0`, also `R = 0`,
`psi(u) = 1` fuer jedes endliche `u`, `u(eps) = unendlich` fuer jedes `eps < 1`. **Der
Nulleffekt der Kapitalgroesse ist unendlich, nicht 0** - wieder mit dem Vorzeichen, das die
naive Lesart verfehlt. Konsequenz: gemessen und berichtet wird `R` (Null exakt 0) mit
Bootstrap-CI, nicht `u`.

**Der harte binaere Teilbefund - und seine ehrliche Power.** Die Frage ist nicht "wie gross ist
`u`", sondern **"existiert `R` ueberhaupt"**, also: ist der GPD-Shape `xi` der
Strategie-Verlustverteilung leicht (`xi <= 0`) oder schwer (`xi > 0`)? Kapital-Skalierung
schwer: `u ~ eps^{-xi/(1-xi)}`, also `u(0,1%)/u(1%) = 10^{xi/(1-xi)}` gegen `ln(1000)/ln(100) =
1,50` im leichten Fall. xi = 0,1 -> 1,29; 0,2 -> 1,78; 0,3 -> 2,68; 0,5 -> 10,0. Crossover bei
`xi/(1-xi) = log10(1,5)`, also **`xi = 0,150`**.
Power-Zeile, unangenehm, mit `SE(xi_hat) ~= (1+xi)/sqrt(k)` (GPD-MLE, `xi = 0,3`):
- Wochen-Aufloesung (A1-Cluster): 208 Wochen, 10 % Exzedenzen -> `k = 21`, `SE = 0,284`; die
  Frage "xi > 0,15?" hat `|Delta|/SE = 0,53` -> Power `Phi(0,53-1,6449) = 0,13`. **Nicht
  entscheidbar.**
- Tages-Aufloesung (WP-10(A)-Proxy, 5,5 a = 2.008 Tage, 10 %) -> `k = 201`, `SE = 0,092`, Power
  **0,49**. Immer noch unter 0,80.
- Fuer Power 0,80 (`z = 2,4865`) braucht es `SE = 0,0603`, also `k ~= 465` Exzedenzen; bei
  2.008 Tagen waere das eine Exzedenz-Rate von ~23 % - eine Schwelle so tief, dass die
  GPD-Asymptotik nicht mehr traegt. Tagesbeobachtungen sind zudem vol-geclustert, das effektive
  `k` also kleiner.

**Vorab fixierte Konsequenz (C.12/GL-012):** `xi` wird als **Intervall mit
Schwellen-Sensitivitaetskurve** (u bei 90/95/97,5 %) berichtet, das leicht/schwer-Verdikt hat
einen ausdruecklichen Zweig **"nicht entscheidbar"**, und `R`, `psi`, `u(eps)` sind **BERICHT,
nie Gate** - konsistent zu PRD 3.6 ("Sharpe, MaxDD und Tail-Ratio werden BERICHTET, nie
geurteilt"). Wer daraus ein Gate machte, baute einen Sharpe-Wiedergaenger: `R = 2mu/sigma^2`
ist monoton im Sharpe, und der ist nach K-0.2 auf diesem Bestand untestbar.

**Feasibility / REZENZ.** Cluster-Einheit Kalenderwoche (A1-Gate-Serie) bzw. Kalendertag
(WP-10(A)-Proxies), beides DEC-51 Pkt. 3 mit gemessenem `rho`. `N_cluster` 104 Wochen gepoolt
bzw. ~2.008 Tage; **fuer das RISIKO gilt PRD 3.6 Auflage (4): das effektive N ist die Zahl der
Stress-Episoden** (`STRESS_ABS`, DEC-56), Groessenordnung 6-10. REZENZ identisch zu den
Fenstern der Quell-Registrierung, `STRESS_REL`-Abdeckung wird mitberichtet. Kein Alpha-Slot,
keine eigene Registrierung - Erweiterung der Berichtszeile bestehender und kuenftiger
P-Registrierungen.

**Rechenbudget.** CPU, Minuten (GPD-Fits + 1.000er Bootstrap); ~0,5 Personentage. **GPU 0.**

**Nicht-Duplikat.** **PRD 3.6 / K-0.4** selbst: dort der driftlose MaxDD-Boden, hier die
drift-bewusste Kapitalgroesse. **H-13** (GPD-`xi` physisch vs. risikoneutral, GESPERRT):
vergleicht zwei Tail-FORMEN von RENDITEN an zwei Snapshot-Tagen und braucht die
Options-Surface; X-AKT-2 schaetzt den Tail der **Strategie-PnL**, braucht keine Optionen, ist
nicht gesperrt. **PARK IC-EVT-3** (Multi-Zyklen-`xi`-Stabilitaet): Stabilitaetsfrage auf
Returns, keine Kapitalfrage auf einem Ueberschussprozess. **PARK IC-EVT-2** (Extremal-Index):
Clusterung von Ueberschreitungen, kein Ruin-Funktional. **D.12 / H-20**: gerichtete
Reversions-Hypothese, unverwandt.

**Entscheidungsrelevanz.** *`xi` klar unter 0,15:* die Kapitalzeile 3.3.9a bekommt eine
risikobasierte statt margin-basierte Groesse; der heute **UNGEMESSENE** Kapital-Multiplikator
`m` bekommt eine boersen-unabhaengige Untergrenze. *`xi` klar ueber 0,15:* jede exponentielle
Kapitalintuition - und damit jede importierte MaxDD-Zahl - ist fuer die Klasse P falsifiziert;
das ist eine programmweite Lehre in der Klasse von D.1 (Spread-Capture a priori tot). *"nicht
entscheidbar":* fixiert, dass die Kapitalfrage der Klasse P auf 5,5 Jahren strukturell offen
bleibt, und verhindert, dass spaeter eine Zahl gesetzt wird.

**Fixture-Paar (DEC-39/C.5).** *Positiv:* Ueberschussprozess mit exponentiellen Schaeden, `rho
= 0,7` - `R_hat` und `u(1 %)` muessen die analytische Loesung im CI treffen. *Negativ:*
driftloser Random Walk (`mu = 0`) - `R_hat` im CI von 0 und `u(eps)` als DIVERGENT gemeldet,
nicht als grosse endliche Zahl. *Adversarial:* Pareto-Schaeden (`xi = 0,4`) auf einem Fenster
ohne Grossschaden - "kein `R`" ist Pflichtmeldung; ein endliches `R_hat` aus der trunkierten
Stichprobe ist ein Testfehlschlag (C.14).

---

## 4. X-AKT-1 - Praemienprinzipien als Tail-Anteil des Klasse-P-Nulleffekts

**Rang 4. Klasse X. Etikett: Enabler / Berichtsgroesse - mit der ausdruecklichen Warnung, dass
drei Viertel der Methode nichts Neues liefern.**

**Methode.** Die klassische Hierarchie:

| Prinzip | Formel | Primaerliteratur |
|---|---|---|
| Erwartungswert | `(1+theta)*E[X]` | Buehlmann (1970), *Mathematical Methods in Risk Theory*, Springer [sek] |
| Varianz / Standardabweichung | `E[X]+a*Var(X)` / `E[X]+b*SD(X)` | ebd. [sek] |
| Exponential / Nullnutzen | `(1/alpha)*ln E[e^{alpha X}]` | Gerber (1979), *An Introduction to Mathematical Risk Theory*, Huebner Monograph 8 [sek] |
| Esscher | `E[X e^{hX}]/E[e^{hX}]` | Buehlmann (1980), ASTIN Bulletin 11, 52-60; Gerber/Shiu (1994), TSA 46, 99-191 [sek] |
| Verzerrung / Wang | `int g(S_X(x))dx`, `g_lambda(u) = Phi(Phi^{-1}(u)+lambda)` | Wang (1996), ASTIN Bulletin 26(1), 71-92; Wang (2000), Journal of Risk and Insurance 67(1), 15-36 |

**Was NICHT uebertragbar ist.** Unter Normalitaet gilt exakt `b = lambda = prem/sigma = Sharpe`
und `alpha = 2*prem/sigma^2 = R`. Standardabweichungs-, Varianz- und Wang-Prinzip liefern also
unter Normalitaet **keine einzige neue Zahl** und erben die Untestbarkeit des Sharpe (K-0.2:
`T_min = 11,3 a` bei realistischer Schiefe gegen 5-6 a Bestand). Das streicht drei Viertel der
Methode und ist der Grund fuer Rang 4.

**Was uebertragbar ist: die Abweichung von der Normalitaet.** Definiert wird **genau eine**
skalenfreie Groesse mit exakt herleitbarem Nulleffekt:

```
TPR (Tail-Praemien-Ratio) = lambda_implizit^Wang(empirische Verteilung) / (prem/sigma)
```

`lambda_implizit^Wang` ist der Verzerrungsparameter, der - auf die **empirische** Verteilung
angewandt - den beobachteten Praemien-Mittelwert exakt reproduziert; der Nenner ist derselbe
Parameter unter Normalapproximation.
**Struktureller Nulleffekt (C.4), exakt: `TPR = 1` fuer eine gaussische Praemienverteilung -
fuer JEDEN Wert von `prem` und `sigma`.** Der Nulleffekt ist damit von der Effektgroesse
entkoppelt; genau diese Eigenschaft fehlte dem CRPSS-Massstab in H-11, wo der strukturelle
Boden 0,21-0,29 statt 0 war. **Richtung: negativ** - eine linksschiefe Verteilung braucht ein
kleineres `lambda` fuer denselben Mittelwert, also `TPR < 1`; je kleiner `TPR`, desto groesser
der Anteil der gemessenen Praemie, der reine Kompensation fuer Tail-Asymmetrie ist.
Zweite, mitberichtete Groesse: **`alpha_implizit/R`** - unter Normalitaet exakt 1, sonst ein
zweites, unabhaengiges Tail-Diagnostikum. Es verknuepft X-AKT-1 und X-AKT-2 zu EINER
Konsistenzpruefung; weichen beide Diagnostika gegenlaeufig ab, ist einer der Schaetzer kaputt.

**Uebertragung.** Keine neuen Daten: Eingang sind die DEC-53-Cluster-Serien der
Klasse-P-Kandidaten (Woche) und die vier taeglichen Praemien-Proxy-PnLs aus WP-10(A) (Tag).
Symbole: A1-Universum. Horizontfrei. **Klasse X.** Nutzen jenseits des Diagnostikums: **`TPR`
ist skalenfrei und damit die einzige Einheit, in der Funding-Carry, Perp/Future-Wedge,
Short-Skew und Short-Vol vergleichbar sind.** WP-10(A) korreliert heute vier PnL-Reihen mit
voellig verschiedenen Volatilitaeten; die abhaengigkeitsrobuste Ueber-Familie `F-PREM` haengt
an der Frage, ob diese vier dieselbe Ertragsquelle messen. Teilen sie denselben Tail-Preis, ist
das ein starkes Indiz fuer eine gemeinsame Quelle.

**Was ausdruecklich NICHT gemacht wird.** `TPR` oder die Risikoladung **darf keine
PASS-Bedingung werden.** Eine Risikoladung ist zwar keine Handelskostenzahl (C.2 waere
buchstaeblich nicht verletzt), aber sie ist eine oekonomische Mindestmagnitude in anderer
Verpackung - und genau die hat PRD 3.1 als R4-Vorschlag ABGELEHNT, weil unter ihr H-04 ein DROP
gewesen waere. Vorab fixiert: **Bericht, nie Gate.**

**Feasibility / Power.** Cluster-Einheit Woche bzw. Tag, N wie X-AKT-2. Bindend fuer den
Tail-Anteil ist PRD 3.6 Auflage (4): effektives N = Zahl der **Stress-Episoden** nach
`STRESS_ABS` (DEC-56), Groessenordnung **6-10**. Bei 6-10 Episoden ist der Bootstrap-CI von
`TPR` weit offen - dieselbe Lage, die WP-10(A) bereits zur rein deskriptiven Form gezwungen hat
(`SE(z) = 1,06/sqrt(5) = 0,474`). **Konsequenz uebernommen: deskriptiv, mit CI, ohne
PASS/FAIL.** Zusaetzlich zu messen, nicht anzunehmen: die **endliche-Stichproben-Verzerrung**
von `TPR` bei N = 104 (quantilbasierte Verzerrungsintegrale sind bei kleinem N verzerrt) - am
Gauss-Null-Fixture gemessen und korrigiert, oder das Mass wird verworfen (L-2b). REZENZ
identisch zu den Quell-Fenstern, `STRESS_REL`-Abdeckung ausgewiesen.

**Rechenbudget.** CPU, Minuten; ~0,5 Personentage. **GPU 0.**

**Nicht-Duplikat.** **PRD 5.1s Nulleffekt-Katalog** (Zinsanker, Intervall-Heterogenitaet,
No-Arbitrage-Null, Reversal-Ladung): vier Komponenten, keine davon eine Risikoladung; PRD 3.2
nennt fuer Klasse P Jensen-Term, Ueberlappung, Peso-Term, Selektions-Decke, MaxDD-Boden,
Tail-Ratio-Richtungsfehler - kein Praemien-Preis-Funktional. **Peso-Fixture (3.3.5):** prueft,
ob das Gate auf einem sprungfreien Fenster durchfaellt; sagt nichts darueber, wieviel Praemie
fuer die Spruenge, die IM Sample sind, fair ist. **H-26/C-33 (VRP):** misst das NIVEAU (IV vs.
RV); `TPR` misst den Preis der SCHIEFE der PnL-Verteilung, instrumentunabhaengig. **A5
(Skew-Praemie):** handelt die Schiefe des UNDERLYING ueber Optionen; `TPR` bepreist die Schiefe
der STRATEGIE-PnL ohne Optionen. In Kompendium A-F, im PARK-Register und in R1-R4 kommt kein
Praemienprinzip vor.

**Entscheidungsrelevanz.** *`TPR` deutlich unter 1:* ein grosser Teil jeder gemessenen
Klasse-P-Praemie ist aktuarisch faire Kompensation; jede P-PASS-Meldung bekommt diese Zerlegung
ins Etikett, und WP-10(A)s Ueber-Familien-Frage eine skalenfreie Vergleichsgroesse. *`TPR` nahe
1:* die Praemienverteilungen sind nahe gaussisch, alle Prinzipien kollabieren auf den Sharpe,
und die Disziplin hat dem Programm nichts ueber PRD 3.6 hinaus zu bieten - **auch das ist ein
verwertbarer, abschliessender Befund** und schliesst die Aktuar-Achse fuer die
Praemien-Bepreisung. *CI zu weit:* der Befund ist, dass 6-10 Stress-Episoden die
Tail-Bepreisung nicht tragen - eine harte Aussage ueber die Grenze des Bestands.

**Fixture-Paar (DEC-39/C.5).** *Positiv:* Praemienprozess mit gleichem `mean`/`sigma`, aber
starker Linksschiefe (Merton-Spruenge im Sample) - `TPR` messbar unter 1. *Negativ:* exakt
gaussischer Prozess mit demselben `mean`/`sigma` - `TPR` im CI von **1**, und zwar fuer mehrere
`mean`-Niveaus (prueft die Entkopplung von Nulleffekt und Effektgroesse). *Adversarial (Peso,
3.3.5):* Nullpraemie plus Merton-Spruenge (Rate 1/3 Jahre, -35 %), Fenster sprungfrei (`p =
e^-1,67 = 0,19`) - `TPR` MUSS dort faelschlich nahe 1 liegen, und die Messung muss das als
"Tail nicht im Sample, Aussage nicht tragfaehig" melden statt eine Zahl zu liefern (C.14).

---

## 5. Rangliste

| Rang | ID | Kurz | Etikett | Warum dieser Rang |
|---|---|---|---|---|
| 1 | **X-AKT-4** | Buehlmann-Straub-Credibility auf den Funding-Sortierschluessel | Enabler | Billigster Vorschlag (Sekunden, 0,3 PT, Beifahrer in WP-7); leitet einen heute GESETZTEN Design-Parameter her (Autokorrelation 0,30, PRD 5.1 Kill-4); liefert einen von `SD_null` unabhaengigen Feasibility-Test der Querschnittsklasse VOR dem Lauf; exakter Nulleffekt (`a=0 => z=0 => IC=0`); beide Ausgaenge aendern etwas. |
| 2 | **X-AKT-3** | Insurance Fund als Ruin-Prozess -> `p_ADL` | Blick wert (St. 1) / spekulativ (St. 2) | Fuellt eine PFLICHTZEILE (3.3.9c), die heute einen unbelegten Platzhalter traegt; loest den offenen PARK-Hinweis ein; `adlAlert` ist ein Phantom-Topic, der Ruin-Weg ist damit der EINZIGE Weg zu dieser Zahl. Rang 2, weil er an V-AKT-1 haengt und die Zahl modellabhaengig bleibt. |
| 3 | **X-AKT-2** | Ruin-Kapital `u(eps)` statt driftlosem MaxDD-Boden | Enabler / Bericht | Zeigt mit PRD-eigenen Eingaben, dass die MaxDD-Formel driftlos ist und die Rangordnung gegen `u(1 %)` je nach Praemie KIPPT (Faktor 3,0 in beide Richtungen); harter binaerer Teilbefund (`xi > 0,15`?). Rang 3, weil das Ergebnis nach PRD 3.6 zwingend BERICHT bleibt und die Power fuer `xi` ehrlich nicht reicht. |
| 4 | **X-AKT-1** | Praemienprinzipien -> `TPR` | Enabler / Bericht | Konzeptioneller Ursprung der anderen drei, aber drei Viertel der Methode kollabieren unter Normalitaet auf den Sharpe und erben dessen Untestbarkeit; der neue Teil haengt an 6-10 Stress-Episoden. Rang 4 aus Entscheidungsrelevanz, nicht aus Interesse. |

Zusammen: **~2,3 Personentage Code, CPU-Minuten Laufzeit, ein 10-Minuten-Egress-Call auf der
Nutzer-Maschine.** Kein Alpha-Slot, kein neuer Dauerstrom, kein GPU (DEC-57 trivial erfuellt),
nichts Gerichtetes und damit nichts, was K-0.1 beruehrt.

---

## 6. NICHT vorgeschlagen - und warum

1. **Solvency-II-Standardformel / SCR (99,5 %-VaR, ein Jahr) als Kapitalregel.** Importierte
   Kalibrierung, deren Erreichbarkeit auf diesem Bestand ungeprueft waere -
   L-1/D.2-Wiedergaenger (C-14: `rho`-Median 2e-7 gegen importierte 0,85); ausserdem
   regulatorisch bedeutungslos fuer einen Einzelbetreiber. Ersetzt durch die hergeleitete
   Groesse `u(eps)` in X-AKT-2 - und selbst die als Kurve, nicht als Schwelle.
2. **Ruin-Wahrscheinlichkeit `psi` als GATE einer P-Registrierung.** `R = 2mu/sigma^2` ist
   streng monoton im Sharpe; ein `psi`-Gate waere ein Sharpe-Gate mit Extraschritt, und PRD 3.6
   hat den Sharpe wegen `MinTRL > Historie` bereits degradiert. Waere Torpfosten-Verschieben in
   einer neuen Metrik (DEC-31-Fehlerklasse, H-11).
3. **Optimale Rueckversicherung / optimaler Selbstbehalt (proportional, Excess-of-Loss).**
   Setzt eine existierende Basisposition voraus, die moduliert wird. Das Programm hat **0
   handelbare Kanten** - exakt das "Overlay-ueber-Nichts", an dem CROSSDOMAIN_PARK (b) bereits
   IC-RMT-1 und IC-NET-1/2/3 geparkt hat. Jede Hedge-Konstruktion braeuchte zudem
   Ausfuehrungslogik; PRD 3.8 verbietet Live-Order-Code.
4. **Bonus-Malus- / Markov-Praemienanpassung.** Setzt wiederholte Schaeden JE
   Versicherungsnehmer voraus. Es gibt keine Entitaet mit einer Schadenhistorie in diesem Sinn;
   die naechstliegende (Konto-Ebene) ist nicht beobachtbar. Kein Analogon.
5. **Panjer-Rekursion / kollektives Modell auf Liquidations-Aggregate.** Braucht
   `allLiquidation` (~66 Tage) - dieselbe N-Falle wie H-10 (N_pointer = 0) und H-13 (2
   Snapshot-Tage); R3 fuehrt den Strom ausserdem ausdruecklich als **fuer H-21 reserviert**.
   Vertagt, nicht verworfen (identisch zur Stufe-2-Vertagung in X-AKT-3).
6. **Extremal-Index `theta` / Cluster-Tail-Abhaengigkeit.** Direktes Duplikat von **PARK
   IC-EVT-2** (7/12, data-gated, offene Rework-Auflage "numerische `theta`-Schwelle").
   Duplikate sind wertlos.
7. **Neue GPD-Tail-Schaetzung auf RETURNS (Multi-Regime-`xi`-Stabilitaet).** Duplikat von
   **PARK IC-EVT-3**, in Konkurrenz zu **H-13** (GESPERRT). X-AKT-2 schaetzt bewusst den Tail
   der STRATEGIE-PnL - das ist der Unterschied, der es zu keinem Duplikat macht.
8. **Hierarchische / Copula-Reservierung ueber mehrere Boersen** (Bybit + Binance + OKX
   gemeinsam). Nur EIN Fonds liegt im Harvest-Baum; Binance braucht eine eigene
   Nachladbarkeits-Probe, und Tardis fuehrt den Kanal erst seit 2026-03-17 [sek]. Ohne
   V-AKT-1-Ergebnis waere das eine Infrastruktur-Entscheidung vor der Feasibility - die
   S4/S5-Falle (D.16). Kandidat fuer eine Folge-Runde NACH V-AKT-1.
9. **ADL-Antizipation als Handelssignal** (Fonds-Dekrement als Vorlauf fuer eine gerichtete
   Position). Sub-Tages-Horizont, nach K-0.1 tot (0,71 bp gegen 11 bp); zusaetzlich Duplikat
   von **PARK IC-MECH-1**. Der Brief erlaubt Sub-Tages-Vorschlaege nur als
   Kosten-/Struktur-MESSUNG - X-AKT-3 ist genau das.
10. **Eine gesetzte Ruin-Toleranz `eps` (etwa 1 %/Jahr) als Registrierungs-Schwelle.**
    Importierte Zahl ohne Herleitung - dieselbe Klasse wie die von PRD 9.1 gestrichenen
    `rho_stress = 0,70`, `p_fill(60s) >= 0,70`, `sigma_xs < 500`. Deshalb liefert X-AKT-2 die
    **Kurve** `u(eps)` und X-AKT-3 ein **Intervall unter benannter Modellfamilie**.
11. **Credibility-geschrumpfter Sortierschluessel als stille Verbesserung von A1.** Waere
    Torpfosten-Verschiebung nach dem Sehen der Zahl. X-AKT-4 liefert die MESSUNG; jede
    Verwendung als Sortierschluessel ist eine eigene Vorregistrierung mit `K` 3 -> 6 und
    angepasster Selektions-Decke.
12. **Gerber/Shiu-Straffunktion in voller Form** (gemeinsame Verteilung von Ruinzeit,
    Ueberschuss vor Ruin, Defizit bei Ruin). Mathematisch die richtige Verallgemeinerung, aber
    sie beantwortet Fragen, die auf 6-10 Stress-Episoden nicht identifizierbar sind. Als Rahmen
    zitiert, nicht als Vorschlag.

---

## 7. Belegstatus

**Primaerliteratur, Zitat verifiziert** (Autor/Jahr/Venue/Band/Seiten ueber Suchtreffer
bestaetigt): Buehlmann (1967), "Experience rating and credibility", ASTIN Bulletin 4(3),
199-207 - Buehlmann/Straub (1970), "Glaubwuerdigkeit fuer Schadensaetze", Mitt. Ver. Schweiz.
Versicherungsmathematiker 70, 111-133 - Buehlmann (1980), "An Economic Premium Principle",
ASTIN Bulletin 11, 52-60 - Wang (1996), ASTIN Bulletin 26(1), 71-92 - Wang (2000), Journal of
Risk and Insurance 67(1), 15-36 (`g_alpha(u) = Phi(Phi^{-1}(u)+alpha)`) - Sparre Andersen
(1957), Trans. XVth Int. Congress of Actuaries, Vol. 2, 219-227 - Embrechts/Veraverbeke (1982),
Insurance: Mathematics and Economics 1, 55-72 - Gerber/Shiu (1998), North American Actuarial
Journal 2(1), 48-72 - Mack (1993), ASTIN Bulletin 23(2), 213-225.

**Primaerliteratur `[sek]`** (aus Fachkenntnis zitiert, Metadaten nicht gegengeprueft):
Lundberg (1903), *Approximerad framstaellning af sannolikhetsfunktionen*, Uppsala - Cramer
(1930), *On the Mathematical Theory of Risk*, Skandia-Jubilaeumsband - Buehlmann (1970),
*Mathematical Methods in Risk Theory*, Springer Grundlehren 172 - Gerber (1979), *An
Introduction to Mathematical Risk Theory*, Huebner Monograph 8 - Gerber/Shiu (1994), TSA 46,
99-191 - Buehlmann/Gisler (2005), *A Course in Credibility Theory*, Springer -
Asmussen/Albrecher (2010), *Ruin Probabilities*, 2. Aufl., World Scientific.

**Boersen-/ADL-Literatur, nur Suchtreffer** (arxiv.org egress-gesperrt, Volltext ungeprueft):
Campbell/Hey/Moallemi/Nutz (2026), "Risk-Based Auto-Deleveraging", arXiv:2603.15963 `[sek]` -
Chitra (2025, rev. 2026), "Autodeleveraging: Impossibilities and Optimization",
arXiv:2512.01112 `[sek]` - "Autodeleveraging as Online Learning", arXiv:2602.15182, Autoren
nicht ermittelt `[sek]`.

| Zahl | Status | Quelle / Rechenweg |
|---|---|---|
| `R = 2mu/sigma^2`, `u(eps) = (sigma^2/2mu)*ln(1/eps)` | hergeleitet | Diffusionsnaeherung der Lundberg-Ungleichung |
| `u(1 %)` = 6,9 / 12,5 / 24,9 / 49,8 % | hergeleitet | mit PRD 9.2 C `sigma_LS = 104 bps/Woche`, `prem` 36/20/10/5 bp |
| `E[MaxDD] = 21,0 %` (`sigma_ann = 7,50 %`, T=5 a) | hergeleitet | PRD K-0.4, `1,2533*sigma_ann*sqrt(T)` |
| Crossover `xi = 0,150` | hergeleitet | `xi/(1-xi) = log10(1,5)` |
| `SE(xi)` 0,284 (Woche) / 0,092 (Tag); `k = 465` fuer Power 0,80 | hergeleitet | `SE ~= (1+xi)/sqrt(k)`, `xi = 0,3`, `z = 2,4865` |
| Aequivalenz "Autokorrelation 0,30 <=> `k <= 2,333*w_i`" | hergeleitet | `z = w/(w+k)`, Reliabilitaet ~ Autokorrelation, 2 benannte Gueltigkeitsbedingungen |
| `bybit/insurance`-Schema `(ts, coin, balance, recv_ts)` | **primaer** | `src/bybit_edge/recorder/storage.py` Z. 116-121 |
| `adlAlert` = Phantom-Topic auf der Linear-WS | **primaer** | `src/bybit_edge/recorder/recording_engine.py` Z. 286-295 (DEC-08) |
| `bybit/insurance` ~66 Tage (2026-09-02) | **primaer, repo-intern** | `research/R3_EREIGNIS_STRUKTUR.md` Z. 28 (DATA_INVENTORY 2026-08-10: 43 Tage) |
| Binance-Fondsziehung 188 Mio. USD am 10.10.2025 | `[sek]` | Suchtreffer/Marktberichte, Primaerquelle gesperrt |
| ~19 Mrd. USD liquidiert, ~1,6 Mio. Konten am 10.10.2025 | `[sek]` | Suchtreffer |
| Bybit-Fondsgroesse; Tiefe der Bybit-Historienseite; ob `/v5/market/insurance` Historie liefert | **UNBELEGT - V-AKT-1** | Host egress-gesperrt |
| Binance `insuranceBalance` bei Tardis seit 2026-03-17 | `[sek]` | Suchtreffer, docs.tardis.dev gesperrt |
| Krypto-Carry ~8 % p.a. bei ~0,8 % Vol | `[sek]`, **nicht verwendet** | Suchtreffer ohne pruefbare Primaerquelle; nicht als A-priori-Effekt eingesetzt |

**Vom Egress-Proxy blockierte Hosts** (markiert, nicht geraten): `arxiv.org`,
`www.sciencedirect.com`, `www.mdpi.com`, `bybit-exchange.github.io`, `developers.binance.com`,
`docs.tardis.dev`, `decentralised.news`. Nichts davon wurde inhaltlich extrapoliert; wo nur ein
Snippet vorlag, steht `[sek]`, wo nichts vorlag, **UNBELEGT** mit benannter Vorfrage.

---

*Ende S5_AKTUAR_RUIN.md - Scout S5, Wissenschafts-Exkurs Scinance 3.0, 2026-09-03. Read-only;
nichts registriert, nichts gebaut.*
