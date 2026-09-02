# REVIEW R1-R4 -- Adversarischer Gate-Audit

> Gate-Auditor, Scinance-3.0-Phase-3, 2026-09-02. Read-only.
> Grundlage: `BRIEF_COMMON.md`, `ERKENNTNIS_KOMPENDIUM.md` (A-F vollstaendig),
> `R1_RISIKOPRAEMIEN.md`, `R2_TAGES_WOCHEN_HORIZONT.md`, `R3_EREIGNIS_STRUKTUR.md`,
> `R4_METHODIK_INFRA.md`.
> Auftrag: zerlegen, nicht loben. Alles unten ist nachgerechnet; wo ich rechne,
> steht der Rechenweg da, damit er seinerseits angreifbar ist.

---

## 0. Der eine Satz, der den ganzen Audit traegt

Drei der vier Berichte setzen ihre Machbarkeitsrechnungen unter der Annahme
**querschnittlicher Unabhaengigkeit** an (R2 `SE(IC)=1/sqrt((K-1)W)`, R3 poolt
BTC+ETH bzw. 5 Symbole als unabhaengige Ereignisse, R1 poolt 5 Symbole in K-07).
R4 rechnet als einziger mit `N_eff = N_c/(1+(N_c-1)*rho_quer)` und stellt
gleichzeitig fest: **`rho_quer` ist UNGEMESSEN.** Damit haengt die
Registrierbarkeit von mindestens acht Kandidaten an einer Zahl, die niemand
kennt und die keiner der vier Berichte zu messen vorschlaegt (R2s V-0 misst
`rho_bar`, die ROHE paarweise Wochenkorrelation -- das ist eine andere
Groesse als die Restkorrelation nach querschnittlichem Demeaning).

Zweitens: **R1s zentraler struktureller Nulleffekt widerlegt R1s zentralen
Kandidaten**, und der Bericht merkt es nicht (Abschnitt 2.1).

Drittens: **R4s neue Pflichtzeile "oekonomische Mindestmagnitude" bricht die
Programm-Doktrin C.2 (Mess-Gate != Tradability-Gate)**, die R4 zwei Seiten
spaeter als "unveraendert bindend" auffuehrt (Abschnitt 4.5).

---

## 1. URTEILE JE KANDIDAT

Kuerzel: **REG** = registrierbar (ggf. als WP ohne Alpha-Budget);
**AUFL** = nur mit Auflage; **TOT** = a priori tot / nicht registrieren;
**DUP** = Duplikat eines anderen Berichts.
IDs sind mit Quellpraefix versehen, weil R1/R2 beide bei K-01 anfangen.

| ID | Quelle | Urteil | Der eine entscheidende Grund | Auflage(n) |
|---|---|---|---|---|
| **R1-K-01** Funding-Carry Spot/Perp | R1 Par.1 | **AUFL** (Kandidat fuer TOT) | Der eigene Nulleffekt `r_null = I_Anker` (10,95% p.a.) kuerzt die gesamte behauptete Bruttokante weg: `r_excess = r_USD - Kostendrift`, bei dem vom Bericht selbst verlangten konservativen `r_USD=0` also **-3,8% p.a.** Die registrierte Schwelle +4,0% verlangt damit real >=18,7% p.a. Ist-Funding. Nie nachgerechnet -- GL-012-Verstoss im Bericht, der GL-012 predigt. | (1) Median(Ist-Funding - I) auf den 43 Harvest-Tagen VOR Registrierung, Schwelle nur wenn erreichbar; (2) `SR_block` aus dem Gate in den Bericht degradieren (R4 K-0.2); (3) `TR<=250` neu herleiten oder streichen; (4) Rendite auf KAPITAL statt auf Notional; (5) "Stress-Episode" kanonisch definieren, sonst ist G5 ein offener Torpfosten; (6) 1h- vs 8h-Funding-Symbole trennen (R4 `funding_n`) |
| **R1-K-02** Intra-Venue-Funding-Spread | R1 Par.1 | **AUFL** | Groessenordnung vollstaendig unbelegt; der Bericht nennt selbst den binaeren 43-Tage-Vorabcheck (<0,4% p.a. -> DROP). Das ist kein Kandidat, das ist eine 10-Minuten-Vorfrage. | Vorabcheck zuerst; `I` je Kontraktklasse aus `instruments-info` verifizieren (sonst ist `r_null=0` falsch); Konvexitaets-Residual des Inverse-Beins VOR und nicht nach der Schwelle rechnen |
| **R1-K-03** Perp vs. datierter Future | R1 Par.1 | **AUFL** (nah an TOT) | Die Headline "billigster Fall des Auftrags" steht auf der ungepruefen Annahme, das Future-Bein settle **gebuehrenfrei**. Das ist exakt die Kostenklasse, die Kompendium E.6(a) fuer Optionen als blockierend fuehrt und die R4 mit `RAISE` statt Default belegt. Dazu: Liquiditaet unbelegt, Klines verfallener Symbole vermutlich nicht abrufbar. | Ein `tickers`-Call (turnover24h) + Primaerquellen-Check der Delivery-/Settlement-Gebuehr; **Schwelle 2,0% p.a. ist per Federstrich gesetzt** ("ich setze bewusst hoeher" statt der hergeleiteten 0,5%) -- das ist eine architect-gesetzte Gate-Schwelle und verstoesst gegen C.19; neu herleiten aus Kapitalbindung |
| **R1-K-04** Skew-Praemie 25d-RR | R1 Par.1 | **AUFL**, nicht in dieser Welle | Reihenfolge aus E.6 ist bindend (H-26 zuerst), Datenlage 38 Tage. Zusaetzlich: die Schwelle `1,5 Vol-Punkte` ist gegen die **C-33-Schwelle** kalibriert, die fuer das Vol-NIVEAU einer Einzeloption definiert wurde -- ein importierter Massstab fuer eine andere Groesse (D.2-Klasse). | Schwelle aus der gemessenen Skew-Verteilung herleiten, nicht aus C-33; GL-012-Vorabcheck (Median-25d-Skew auf 38 Tagen) wie vorgeschlagen; die von R3-K-31 gemessene Settlement-Fenster-Verzerrung in die Halte-bis-Verfall-Rechnung aufnehmen |
| **R1-K-05** Kalender-/Forward-Vol | R1 Par.1 | **TOT** (a priori, Autor stimmt zu) | Netto-Vega-Verduennung: 2,51 Vol-Punkte Kosten je Einheit Netto-Vega gegen eine Forward-Vol-Praemie, fuer die keinerlei Evidenz existiert; erforderlich >=5,0 Vol-Punkte. | Nicht registrieren. Die verallgemeinerbare Lehre ("jede Bybit-Options-Struktur, deren Nutzen eine Greek-DIFFERENZ ist, ist gebuehren-strukturell benachteiligt") als Programm-Konstanten-Kandidatin protokollieren. Nebenbefund: K-05s Kostentabelle laesst die Delivery-Gebuehr weg, die K-04s Tabelle enthaelt -- berichtsinterne Inkonsistenz |
| **R1-K-06** ETH-vs-BTC-Relative-Vol | R1 Par.1 | **TOT** (Autor stimmt zu) | ~3,9 Vol-Punkte Maker-Kosten gegen einen Praemienanteil, den der Bericht selbst auf <2 Vol-Punkte schaetzt; der Dispersions-Mechanismus existiert in dieser Marktstruktur nicht. | Nicht registrieren. Einzig behaltenswert: der WP-0-basierte Nulleffekt (mittlere realisierte Vol-Differenz) -- eine 10-Minuten-Rechnung |
| **R1-K-07** Kohaerenz + Maker-Fill-Zensus | R1 Par.1 | **REG als WP** (kein Alpha-Budget) -- **aber Teil (A) ist wie spezifiziert infeasible** | Einziger Vorschlag in vier Berichten, der die Portfolio-These prueft, BEVOR auf ihr gebaut wird; vollstaendig aus dem Bestand, gebaute Werkzeuge. Aber: der N-Floor ">=15 gemeinsame Extremtage" ist ein ROH-N. Die 5 Symbole teilen sich dieselben Extremtage; bei rho~0,8 ist `N_eff = 15/(1+4*0,8) = 3,6`. Das Gate liefert mit hoher Wahrscheinlichkeit KEIN VERDIKT. | (A) N-Floor auf **Kalender-Cluster** umstellen (R4 1.3.c) und den Floor aus der Cluster-Zahl herleiten; (B) Schwelle `adv_sel <= 1,5 bp` ist **fehlhergeleitet** -- der Maker-Vorteil betraegt 5,5-2,0 = 3,5 bp je Bein, nicht 1,5; Herleitung korrigieren; mit R4 6.3 (Quote-Schatten-Messung) und R4 6.2(a) (Portfolio-Nulleffekt = erwarteter Sharpe einer Gleichgewichtung von K Rauschsignalen) vereinigen |
| **R2-V-0** Universums-/Survivorship-Zensus | R2 | **REG als WP -- Rang 1 des gesamten Feldes** | Ohne K, sigma_xs, rho und die Delisting-Antwort ist jede Schwelle in R2 ein C-14-Wiedergaenger. WP-4-Muster: eine Frage, ein binaerer Befund, toetet oder oeffnet eine ganze Klasse. | Muss **`rho_quer`** messen (Restkorrelation NACH woechentlichem Querschnitts-Demeaning), nicht nur `rho_bar` -- R4 K-0.5 zeigt, dass `rho_quer` und nicht K die bindende Zahl ist; mit R4 WP-8 (Alt-Symbol-Spread) vereinigen; **1d zuerst, 1h-Panel-Store erst nach bestandener Feasibility** |
| **R2-K-01** Querschnitts-Momentum breit | R2 | **AUFL** (bei rho_quer>0,03: **TOT**) | Die Feasibility-Tabelle (K>=169 bei IC 0,03) setzt `rho_quer=0`. Bei R4s Arbeitswert 0,05 ist `N_eff <= 1/rho = 20`, der SE-Boden ueber 52 Wochen also `1/sqrt(19*52)=0,0318` -> detektierbarer IC **0,089**. Dann existiert **kein K**, das das 2x12-Monats-Design traegt: struktureller GL-012-DROP wie H-07, nur an der Korrelationsachse. | `rho_quer` messen; bei >0,03 ist die einzige tragfaehige Form R4s gepoolter 3-Jahres-Schaetzer -- und dann darf K-01 **erst nach** unabhaengiger Entscheidung ueber die Verfassungsaenderung registriert werden (sonst ist die Aenderung fuer diesen Kandidaten gemacht = Torpfosten) |
| **R2-K-02** Querschnitts-Funding-Carry (perp-only) | R2 | **REG mit Auflage -- bester Alpha-Kandidat des Feldes** | Der Boersen-Zinsanker `I`, an dem R1-K-01 stirbt, **kuerzt sich im Querschnitt heraus** (alle USDT-Perps teilen dasselbe `I`). Praemie statt Prognose, identifizierbarer Zahler, kein Spot-Bein, und die Nullhypothese (exakte Kompensation durch das Preisbein) ist exakt ausrechenbar. Weder R1 noch R2 haben diesen Zusammenhang gesehen. | Dieselbe `rho_quer`-Bedingung wie K-01; **Funding-Intervall-Heterogenitaet** (1h- vs 8h-Symbole) zwingend behandeln, sonst sortiert der Schluessel Aepfel gegen Birnen; Orthogonalisierung gegen Momentum/Reversal ist urteilstragend (so registriert -- gut); symbolspezifische Slippage aus WP-8 ist Vorbedingung jeder Tradability-Aussage |
| **R2-K-03** Time-Series-Momentum | R2 | **TOT** in der Portfolio-Sharpe-Form (Autor stimmt zu) | Eigene Power-Rechnung: SR 2,80 je 12-Monats-Fenster noetig, bester unabhaengiger Literaturwert 1,6. | Die Driscoll-Kraay-Panel-Form ist eine ANDERE Hypothese und heute nur eine Skizze; sie braucht zuerst die Persistenz-Null (R4 1.2.b(2), Valkanov/BRW: AR(1) unter der Null simulieren) und ist ohne sie nicht registrierbar |
| **R2-K-04** Kurzfrist-Reversal breit | R2 | **AUFL** | Turnover ~1,0 -> 30 bps/Woche, und der Bid-Ask-Bounce-Nulleffekt kann den gemessenen IC allein erklaeren. Der Bericht erkennt beides korrekt. | Das **Gap-Design (Formation/Halten um einen Tag getrennt) muss die PRIMAERE Fassung sein**, nicht die Alternative -- sonst wird der Bounce geschaetzt statt eliminiert; `rho_quer`-Bedingung; die D.7-Nichtwiederholung woertlich in die Registrierung (so vorgesehen -- gut) |
| **R2-K-05** Vol-/Beta-Anomalie | R2 | **AUFL** | Der Vol-Drag-Nulleffekt (0,74%/Woche) ist **groesser als jede erwartete Kante** -- die beste Nulleffekt-Herleitung in allen vier Berichten. Genau deshalb ist die urteilstragende Groesse ein Residuum nach Abzug eines Terms, der groesser ist als es selbst: schaetzfehler-dominiert. | Registrierung muss VOR dem Lauf das Verhaeltnis Nullterm/Erwartungseffekt ausweisen und einen Feasibility-Check bestehen, dass das Residuum in der beanspruchten Genauigkeit ueberhaupt schaetzbar ist; Redundanz-Check gegen Size/Volumen bei rho>0,8 beibehalten |
| **R2-K-06** Kalender-Interaktion | R2 | **TOT** (Wochenende, Monatsende, letzter Freitag) / **AUFL** (Session-Achse) | Eigene Nachweisgrenzenrechnung unter REZENZ: 33 bps/Tag bei n~104 Wochenendtagen je Fenster. | Die Session-Achse ist inhaltlich **kein Kalendereffekt**: die einzige zitierte Evidenz (Quarter-Hour-Effect) ist ein FLUSS-Signal. Als "Kalender"-Hypothese registriert misst sie etwas anderes als ihr Name sagt -- umbenennen oder fallen lassen |
| **R2-K-07** Vol-Targeting | R2 | **REG nur als vorab fixierte Variante** (nie eigenstaendig) | Diszipliniertester Einzelpunkt der vier Berichte: er verhindert genau die nachtraegliche Rettungsanker-Einfuehrung, die C.1/C.3 verbietet. PRD-PARK-Entsperrbedingung (netto-positive Basis) bleibt bindend. | Die Geschenk-Verteilung (blockweise umsortierte Renditen, 1.000 Ziehungen) muss **gemessen** werden, nicht angenommen; Delta-Sharpe-Schwelle oberhalb ihres 95.-Perzentils |
| **R3-K-31** EXP-CLOCK | R3 | **REG mit Auflage** | Einziger Kandidat mit null Nachladeaufwand, N~200 und einem **Gratis-Negativ-Panel aus Realdaten** (XRP/BNB ohne liquide Kette). Aber: SE ist zu guenstig gerechnet (s. Abschnitt 2.3), und die Schwelle 12 bps liegt bewusst UNTER der Wand -- ein PASS hat a priori keine Handelsperspektive. | SE mit `N_eff` statt N=104 neu rechnen; im Registrierungstext ausdruecklich festhalten, dass der beste Fall unterhalb der Wand liegt (die Welle gibt damit ihren Alpha-Slot fuer eine wissentlich sub-Wand-Messung aus -- das ist eine Entscheidung, keine Nebensache); Funding-Settlement-Zeiten fuer P2 gegen die Boersen-Doku verifizieren (so vorgesehen) |
| **R3-K-32** GEX-KOND | R3 | **TOT fuer diese Welle** (Autor stimmt zu) | ~10 Verfalls-Ereignisse heute = die H-10/H-13-N-Falle zum dritten Mal; GEX-Vorzeichen ohne Options-Taker-Tape nicht identifiziert. | Der vorgeschlagene **Harvester-Auftrag ist selbst Infrastruktur-Ausgabe vor validiertem Basissignal**: er wird erst gestellt, wenn K-31 ein PASS liefert. Sonst S4/S5 (s. Abschnitt 5.2) |
| **R3-K-33** X-PULL | R3 | **Stufe 1 REG (Zensus) / Stufe 2 TOT a priori** | Die eigene A-priori (Median 1-3 bps, 40-60 bps nur in Kaskaden) impliziert, dass der N-Floor von 30 Ereignissen je Halbjahr bei \|b\|>=20 bps mit hoher Wahrscheinlichkeit reisst -- und die Ereignisse, die auftreten, fallen per Konstruktion in Kaskadenminuten, in denen die 15-bps-Annahme nachweislich falsch ist. | Stufe 1 als billigen binaeren Zensus behalten; Stufe 2 nicht als Kandidat fuehren, sondern als konditionale Fortsetzung ohne eigenen Registrierungsanspruch |
| **R3-K-34** LEV-STATE | R3 | **AUFL** | Der einzige R3-Kandidat **ohne hergeleiteten Rauschboden**: die Schwelle 0,25 auf einer Differenz zweier Semivarianz-Verhaeltnisse ist gesetzt, nicht hergeleitet. Zusaetzlich poolt er 5 Symbole zu "~180 Dezil-Tagen", obwohl der Hebelzustand ueber Symbole an denselben Tagen auftritt (effektiv ~40). | Rauschboden von `(R_bedingt - R_RV-gematcht)` per Bootstrap auf dem Aera-Profil VOR der Schwellenfestlegung; effektives N als Kalender-Cluster ausweisen (R4 1.3.c); OI-Arm bleibt korrekt an die Ruecklaufzeit-Probe gebunden |
| **R3-K-35** SLIP-ZENSUS (WP-3) | R3 | **REG als WP, aber nachrangig** | Wertvoll, aber nur ~2,5 Monate rezenz-konforme `orderbook.1000` und nur BTC/ETH -- er kann die Frage, die R2 blockiert (Alt-Symbol-Slippage), **prinzipiell nicht** beantworten. Ausserdem ueberzeichnet die Rahmung den Ertrag: 15 bps = 11 bps Gebuehr + ~4 bps Slippage; die Messung kann die Konstante maximal um ~27% korrigieren und nie unter 11 bps Taker druecken. | R4s WP-8 (tickers-basiert, ganzes Universum, Minuten) laeuft ZUERST; Konstanten-Ersetzung als DEC registrieren, **bevor** ein Kandidat davon profitiert; Anti-Torpfosten-Klausel (H-04b/H-05c bleiben unberuehrt) beibehalten -- korrekt so vorgesehen |
| **R3-K-36** VRP-KOND | R3 | **DUPLIKAT** (Datenfund) **+ TOT** (Gate) | Der DVOL-Fund ist identisch mit R4 3.4. Das Terzil-Gate faellt an der eigenen Power-Rechnung: `SE(Terzil-Differenz) ~ 4,1` Vol-Punkte gegen eine 3-Punkte-Schwelle = **0,73 SE**. Beide angebotenen Auswege sind verboten: ueberlappende Wochen kaufen keine Power (R4 1.2.a), 24-Monats-Fenster kollidieren mit REZENZ. | Datenfund unter R4s Rahmung ausfuehren (WP + Ueberlappungs-Kreuzvalidierung gegen die 112 harvesteten Tage, kein Alpha-Gate); Terzil-Gate nicht registrieren |
| **R3-K-37** SKEW-VORLAEUFER | R3 | **Stufe 1 REG (Ketten-Zensus) / Stufe 2 TOT wie spezifiziert** | Stufe 2 leitet den Rauschboden als `1/sqrt(60)=0,129` aus 60 **ueberlappenden** Tagesbeobachtungen (5-Tage-Delta gegen 10-Tage-Forward) her. Effektives N ~6, Rauschboden ~0,41 -- die 0,25-Schwelle ist strukturell unerreichbar. Der Bericht benennt die Ueberlappungsfalle, traegt sie aber nicht in die Schwellenherleitung. | Stufe 1 (tagesgenaue Ketten-Luecken-Karte) sofort -- sie fehlt dem Programm komplett und wird von jedem Options-Kandidaten gebraucht; Stufe 2 nur nach Neuherleitung des Rauschbodens auf nicht-ueberlappenden Einheiten |

---

## 2. RECHENFEHLER- UND UEBERZEICHNUNGS-REGISTER

Alles hier ist nachgerechnet. Was nicht aufgefuehrt ist, habe ich geprueft und
korrekt gefunden (R1s Vol-Punkt-Umrechnungen, R2s Power- und Download-Tabellen,
R4s K-0.1 bis K-0.6 komplett -- inkl. der Mertens-Erweiterung, deren Faktor 1,827
sich korrekt aus einem MONATLICHEN SR=0,2887 ergibt, was der Bericht nicht
dazusagt, aber richtig rechnet).

### 2.1 R1: der Anker-Doppelzaehlungsfehler (schwerwiegend)

R1 Par.0.2 stellt fest: `E[Funding] = I = 10,95% p.a.` ist mechanisch verankert,
und **jeder Funding-Kandidat setzt `r_null = I_Anker - r_USD`**. R1 Par.1 K-01
rechnet dann die Bruttokante als **eben diese** 10,95% p.a. und meldet "netto
~5-7% p.a." bzw. "~8-10% p.a.".

Beides zusammen ergibt:
`r_excess = (10,95 - Kostendrift) - (10,95 - r_USD) = r_USD - Kostendrift`.
Mit dem vom Bericht selbst geforderten konservativen `r_USD = 0` und der
30-Tage-Drift 3,77% p.a. ist `r_excess = -3,77% p.a.`
Die registrierte Schwelle `r_excess >= 4,0%` verlangt also ein **realisiertes
Funding von >=18,7% p.a.** -- 71% ueber dem Anker, ueber zwei disjunkte
12-Monats-Fenster. Das ist ein GL-012-Feasibility-Fall, und er wird nirgends
geprueft. Der Bericht, der den Anker als seinen wichtigsten Befund fuehrt,
zieht ihn in seinem Hauptkandidaten nicht ab.

### 2.2 R1: "ab ~2 Wochen ein Abschlag von 2-4 Prozentpunkten p.a."

R1 Par.0.3, als "Befund, der den ganzen Auftrag traegt" ausgewiesen. Nachgerechnet:
31 bps ueber 14 Tage = 2,21 bps/Tag = **8,08% p.a.** Die 2-4 Punkte entsprechen
30 bis 90 Tagen Haltedauer (3,77% bzw. 1,26%), nicht zwei Wochen. Die Aussage ist
um Faktor 2-4 zu guenstig und traegt die gesamte Rangliste von R1.

### 2.3 R3: SE-Herleitung von K-31 poolt korrelierte Ereignisse

R3 rechnet: 30-Min-SD 36 bps, N=52 Verfalls-Freitage je Symbol/Fenster, gepoolt
BTC+ETH N=104, `SE = 36/sqrt(104) = 3,5 bps`, Schwelle 12 bps = "3,4 SE".
BTC- und ETH-Stundenrenditen korrelieren ~0,8. `N_eff = 2/(1+0,8) = 1,11`
-> effektiv 58 Ereignisse -> `SE = 36/sqrt(58) = 4,7 bps` -> 12 bps = **2,55 SE**.
Dazu ist Delta eine DIFFERENZ gegen Placebos, deren SE mindestens so gross ist.
Per-Fenster-Power bei wahrem Delta=12 bps: `Phi(2,55-1,96) = 0,72`; ueber zwei
Fenster 0,52; nach BH ueber 8 Zellen weniger. Kein Killer, aber die Behauptung
"Feasibility bestanden (3,4 SE)" ist um ein Drittel zu optimistisch, und die
Ablehnung der 6-Monats-Fassung ("2,4 SE, unwahrscheinlich") trifft nach
Korrektur die 12-Monats-Fassung fast genauso.

### 2.4 R3: K-37 traegt die Ueberlappung nicht in die Schwelle

Rauschboden `1/sqrt(N)` mit N=60 Tagen ist nur gueltig fuer unabhaengige
Beobachtungen. 5-Tage-Delta gegen 10-Tage-Forward auf Tagesraster: effektives
N ~ 60/10 = 6, Rauschboden 0,41. Schwelle 0,25 damit unter dem Rauschboden --
struktureller A-priori-DROP nach GL-012. Der Bericht nennt die Falle und
adressiert sie nur bei der p-Wert-Berechnung (Blockpermutation), nicht bei der
Schwellenherleitung. Beides muss dieselbe Einheit benutzen.

### 2.5 R3: K-34 poolt 5 Symbole, deren Zustandstage identisch sind

"~36 Dezil-Tage je Symbol, gepoolt ueber 5 Symbole ~180 -- ausreichend."
Hoher OI-Aufbau bei einseitigem Funding tritt ueber BTC/ETH/SOL/BNB/XRP an
weitgehend denselben Kalendertagen auf. Effektives N ist die Zahl der
Kalender-Cluster (~40), nicht 180. Exakt die Fehlerklasse, die R4 1.3.c
(Kolari/Pynnoenen) als verbindlich zu vermeiden benennt.

### 2.6 R2: `SE(IC)=1/sqrt((K-1)W)` unterstellt rho_quer = 0

Die Formel ist arithmetisch richtig (ich habe alle vier Zeilen der
K-Tabelle nachgerechnet: 169/378/95/61 bei W=52 stimmen exakt), aber sie gilt
nur bei querschnittlicher Unabhaengigkeit. Bei `rho_quer = 0,05` liegt der
SE-Boden unabhaengig von K bei `1/sqrt(19*52) = 0,0318` -> detektierbarer IC
0,089. Der gesamte Ausweg "Breite" von R2 haengt an einer Zahl, die R2 nicht
misst. Siehe Abschnitt 3.1.

### 2.7 R2: Dezil-Spreadfaktor 2,0 ist konservativ, nicht falsch

`R_LS ~ 2,0 * IC * sigma_xs`; der exakte Normalapproximations-Faktor ist
`2 * E[z | oberstes Dezil] = 3,51`. R2 ist um Faktor 1,75 zu pessimistisch --
die einzige Stelle in vier Berichten, an der ein Fehler gegen den eigenen
Kandidaten laeuft. Zu erwaehnen, damit die Korrektur nicht spaeter als
Verbesserung der Kante verkauft wird.

### 2.8 R1: `adv_sel <= 1,5 bp` widerspricht seiner eigenen Begruendung

"bei groesserem Abschlag uebersteigt der effektive Maker-Preis den Taker-Preis
von 5,5 bp". Maker 2,0 bp/Bein gegen Taker 5,5 bp/Bein -> der Vorteil betraegt
3,5 bp, nicht 1,5. Die Schwelle ist strenger als ihre Herleitung; strenger ist
unschaedlich, aber eine Schwelle mit falscher Herleitung ist nach C.4/GL-012
nicht registrierbar.

### 2.9 R1 und R2: 8h-Funding wird stillschweigend fuer alle Symbole ueber 5,5 Jahre unterstellt

R1s Anker (0,01%/8h) und R2s Record-Zahl (5,5a x 3/Tag = 6.023) setzen beide ein
konstantes 8-Stunden-Intervall voraus. Bybit fuehrt Symbole mit 1h-Funding, und
Intervalle aendern sich ueber die Historie. Nur R4 (5.3, `funding_n`) sieht das.
Fuer R2-K-02 (Funding als Sortierschluessel) ist das nicht kosmetisch: ohne
Intervall-Normierung sortiert der Schluessel Symbole nach Abrechnungsfrequenz.

---

## 3. UEBERSCHNEIDUNGEN UND WIDERSPRUECHE ZWISCHEN DEN BERICHTEN

### 3.1 rho_quer / N_eff -- R2 gegen R4 (der harte Widerspruch)

R2 0.3C: `SE(IC) = 1/sqrt((K-1)*W)`, Breite hilft unbegrenzt, K>=170 loest alles.
R4 K-0.5: `N_eff = N_c/(1+(N_c-1)*rho_quer)`, "die Breite hilft stark von 5 auf
~50 und danach kaum noch", `rho_quer` UNGEMESSEN.
**Entscheidung: R4 hat recht.** In Krypto ist praktisch alles Beta zu BTC; nach
querschnittlichem Demeaning bleibt Sektor-/Beta-Restkorrelation. Bei rho_quer
schon von 0,05 ist R2s gesamter Querschnittsblock in der 2x12-Monats-Form ein
struktureller GL-012-DROP. **Konsequenz fuer die Welle:** V-0 muss um die
Messung von rho_quer erweitert werden, und keine Schwelle in R2 darf vor dieser
Messung gesetzt werden. Ohne diese Aenderung waere V-0 selbst ein C-14-Fall
(Schwelle gesetzt, Erreichbarkeit ungeprueft).

### 3.2 Funding-Carry: R1-K-01 gegen R1-K-02 gegen R2-K-02

Drei Kandidaten, eine Datenschicht (`/v5/market/funding/history`-Backfill), drei
verschiedene Fragen: Niveau delta-neutral mit Spot-Bein (R1-K-01),
Intra-Venue-Differenz (R1-K-02), Querschnitts-Sortierung perp-only (R2-K-02).
**Entscheidung: vereinen auf der Datenschicht, trennen in der Frage -- aber die
Rangfolge dreht sich gegenueber beiden Berichten.** R1-K-01 stirbt an seinem
eigenen Anker (2.1). R2-K-02 ueberlebt ihn, weil `I` sich im Long-Short
herauskuerzt -- ein Zusammenhang, den weder R1 noch R2 herstellt: R1 findet den
Anker und uebersieht, dass die Querschnittsform ihn neutralisiert; R2 baut die
Querschnittsform und zitiert die 11% p.a. als "typische" Rate statt als
mechanischen Anker. **Die richtige Fassung ist R2-K-02 mit R1s Ankerherleitung
als explizitem Nulleffekt-Nachweis (`r_null = 0, weil I sich kuerzt -- geprueft
an instruments-info`).** R1-K-02 bleibt eine eigenstaendige dritte Frage, aber
mit R1s eigenem Vorbehalt: falls die drei Kontraktklassen verschiedene `I`
tragen, ist `r_null = I_A - I_B` und nicht 0.

### 3.3 DVOL-Historie: R3-K-36 gegen R4 3.4

Identischer Fund (oeffentlicher Deribit-Endpunkt ab ~2021-04, ~1.980 statt 112
Tage), identische korrekte Registry-Warnung (entsperrt H-26 NICHT, erfuellt die
C-33-12-Monats-Uhr NICHT).
**Entscheidung: R4s Fassung uebernehmen.** R4 macht daraus einen Backfill-WP
plus den besten denkbaren Quellen-Kreuzvalidierungstest (stimmen die 112
Ueberlappungstage ueberein?) und eine eigens vorzuregistrierende H-27. R3 macht
daraus ein Terzil-Gate, das an der eigenen Power-Rechnung stirbt (0,73 SE).
Der Datenfund ist wertvoll, das Gate ist es nicht.

### 3.4 Delivery-/Settlement-Gebuehr: R1 gegen R4 gegen Kompendium E.6(a)

R1 Par.0.1 traegt sie als **NEU, sekundaerbelegt** ein: min(1,5 bp Index; 12,5%
Intrinsic), nur ITM -- und rechnet mit ihr in K-04/K-06.
R4 2.2 macht `delivery_fee_of_index` zu einem Default-`None`, dessen Benutzung
ohne gesetzten Wert **RAISED**.
Kompendium E.6(a) macht die Verifikation an der Primaerquelle zur Vorbedingung
der H-26b-Registrierung.
**Entscheidung: R4 gewinnt, ohne Abstriche.** R1s Zahl darf **nicht** nach
`constants.py`; sie ist ausschliesslich als zweiseitige Sensitivitaetsgrenze
zulaessig. Verschaerfend: **R1-K-03 unterstellt fuer datierte Futures ein
gebuehrenfreies Settlement** -- dieselbe unmessene Kostenklasse ein Produkt
weiter, ohne jede Quelle. Unter R4s Regel muss auch dieser Pfad RAISEN. Damit
faellt R1-K-03s Alleinstellungsmerkmal ("3 Fills statt 4") bis zum Nachweis weg.

### 3.5 Verfalls-Effekte: R1-K-04/K-05 gegen R3-K-31

Kein direkter Widerspruch, aber eine unbemerkte Kopplung: R1-K-04 haelt bis zum
Verfall und wird am 30-Minuten-Settlement-TWAP abgerechnet; R3-K-31 behauptet,
genau in diesem Fenster liege eine hedge-getriebene Preisverzerrung von 10-40
bps. Wenn R3 recht hat, settlen R1s Options-Kandidaten **systematisch in die
Verzerrung hinein** -- ein Kostenposten (oder Ertragsposten), den R1s
Kostentabelle nicht fuehrt.
**Entscheidung: zusammenfuehren, nicht waehlen.** R3-K-31 ist ohnehin frueher
laufbereit (kein Nachladen) und der Options-Block ist hinter H-26 gesperrt.
K-31s Ergebnis wird Pflicht-Eingang in jede spaetere Halte-bis-Verfall-Rechnung.

### 3.6 Slippage-Konstante: R3-K-35 gegen R4 WP-8 gegen R2 "Nicht vorschlagen #10"

Drei Berichte, dieselbe Luecke, drei Namen, zwei unvereinbare Datenpfade
(L2-Replay vs. `tickers`-Snapshot) und zwei unvereinbare Abdeckungen
(BTC/ETH-Tiefe vs. ganzes Universum, Top-of-Book).
**Entscheidung: R4s WP-8 zuerst, R3s K-35 danach, beide behalten.** Nur WP-8
kann die Frage beantworten, die R2s ganze Klasse blockiert (Alt-Symbol-Spread) --
und es ist moeglicherweise **auf Bestandsdaten** (`bybit/tickers`, 3.751
Symbole, 43 Tage) in Minuten rechenbar, wenn die von R4 geforderte Inhaltsprobe
(C.8) das Feld `bid1Price/ask1Price` findet. K-35 liefert etwas anderes und
Ergaenzendes: die Tiefen-Kurve `c(Q)` fuer BTC/ETH, die kein `tickers`-Zensus
liefern kann. Beide Konstanten-Ersetzungen sind als DEC zu registrieren,
**bevor** ein Kandidat von ihnen profitiert.

### 3.7 Sharpe als urteilstragende Groesse: R1 G3 gegen R4 K-0.2

R1 macht `SR_block >= 0,60` zu einem harten Gate-Bestandteil.
R4 K-0.2: `T_min = 6,18/SR^2` -> fuer SR 0,6 sind das **17,2 Jahre**; der Sharpe
darf nicht die urteilstragende Groesse sein.
**Entscheidung: R4 gewinnt.** R1s eigene Herleitung (`SE(SR)=0,31` bei
`N_eff=12`) ist technisch korrekt, ergibt aber ein Gate mit ~50% Power je
Fenster und 25% ueber zwei -- nach R4s K-0.6 eine Typ-II-Maschine. `SR_block`
wird Bericht, nicht Gate; urteilstragend ist `mean(prem)` nach R4 1.1.a.

### 3.8 Tail-Ratio: R1 G4 gegen R4 1.1.b(6)

R1: `TR = |CVaR_1%|/mean <= 250 Tage`, **nicht verhandelbares eigenstaendiges
Gate**.
R4: eine echte Praemie hat strukturell eine schlechte Tail-Kennzahl (negative
Schiefe ist ihr Preis); eine Tail-Kennzahl als Existenzkriterium toetet jede
echte Praemie -- sie ist Risiko-Deskriptor mit Untergrenze, nie Gate.
**Entscheidung: R4 gewinnt im Prinzip; R1s Schwelle ist zusaetzlich
fehlkonstruiert.** Die 250 Tage sind eine importierte Zahl mit einem Slogan
statt einer Herleitung ("ein Tail-Tag darf weniger kosten als eine Jahresernte")
-- D.2-Klasse. Schlimmer: die Kennzahl hat den Mittelwert im Nenner, also
bestraft sie kleine Praemien und belohnt grosse -- und der Mittelwert ist genau
die Groesse mit dem groessten Schaetzfehler. Eine exzellente Praemie mit
0,5 bps/Tag und CVaR 200 bps hat TR=400 (getoetet), eine mittelmaessige mit
2 bps/Tag und CVaR 400 hat TR=200 (bestanden). Degradieren auf Deskriptor.

### 3.9 Portfolio-/Kohaerenzfrage und Maker-Fill: R1-K-07 gegen R4 6.2(a)/6.3

Zwei unabhaengige Entdeckungen derselben zwei Luecken.
**Entscheidung: vereinen.** R4 liefert den Nulleffekt, den R1-K-07(A) fehlt
(erwarteter Sharpe einer Gleichgewichtung von K Rauschsignalen) und die
Verfassungs-Einordnung fuer K-07(B) ("kein Live-Order-Code" macht jede
Maker-Annahme unfalsifizierbar -- Ausweg: kapitalfreie Quote-Schatten-Messung).
R1 liefert die konkreten Schwellen. Ergebnis ist ein WP, kein Alpha-Kandidat.

### 3.10 Drei verschiedene Power-Konventionen

R2 rechnet zweiseitig alpha=0,05, Power 0,80 -> `z = 2,802`.
R4 rechnet einseitig -> `z = 2,4865`.
R3 rechnet "~2 Rauschboeden" bzw. "3,4 SE" ohne genannte Power.
Der Unterschied ist nicht kosmetisch: `(2,4865/2,802)^2 = 0,79`, R2s K>=169
wuerde unter R4s Konvention zu K>=134. **Entscheidung: eine Konvention vor der
ersten Registrierung fixieren, und jede Power-Zeile muss alpha, Seitigkeit und
Power ausdruecklich nennen.** Sonst bekommt derselbe Kandidat je nach Bericht
ein anderes Feasibility-Urteil.

### 3.11 Was NICHT widersprechen: GPU

Alle vier Berichte kommen unabhaengig zu "kein GPU in Welle 1". Das ist der
einzige einstimmige Befund und sollte als solcher in die Verfassung.

---

## 4. METHODIK-PRUEFUNG R4

### 4.1 Vorzeichen-Konsistenz + gepoolter Test statt hartem Ein-Fenster-DROP

**Fuer die Aenderung.**
(a) Die Arithmetik stimmt: bei Per-Fenster-Power 0,5 verwirft die harte Regel
drei von vier echten Effekten (`0,5^2 = 0,25`); Vorzeichen-Konsistenz bei
wahrem t=1,4 gibt `0,919^2 = 0,845` gegen `0,42^2 = 0,18`, Faktor 4,7. Ich habe
nachgerechnet -- korrekt.
(b) Das Programm faehrt heute unbemerkt bei einem **effektiven alpha von 0,25%**
(0,05^2), nicht bei 5%. Das war nie beschlossen, es ist ein Nebeneffekt der
Regel. Eine bewusste Wahl ist einer unbewussten vorzuziehen.
(c) R4 leitet die Aenderung schriftlich und **vor** jedem 3.0-Lauf her und sagt
selbst, dass ein Vorschlag nach einem Lauf ein C.1-Verstoss waere. Das ist die
korrekte Prozedur.
(d) Die Regel bleibt fuer billige, hoch-gepowerte Messungen unveraendert -- die
Aenderung ist auf die Klassen P und W begrenzt.

**Gegen die Aenderung.**
(a) **Der Zweck der Regel war nie alpha-Kontrolle, sondern Regime-Robustheit.**
C.18/DEC-38 existiert, weil das Programm wiederholt Effekte fand, die nur in
einer Aera lebten (H-22: IC "lebt nur 2023/24"; H-20: Vorzeichen kippt
BTC -16->+36, ETH +32->-12). Ein gepoolter Schaetzer mittelt genau darueber
hinweg und kann von einem Fenster getragen werden. Das ist der Ausfallmodus,
gegen den die Regel gebaut wurde.
(b) **Vorzeichen ist ein 1-Bit-Test.** Unter der Null bestehen zwei Fenster mit
Wahrscheinlichkeit 0,5 (gleiches Vorzeichen) bzw. 0,25 (beide positiv). Als
Filter traegt das faktisch nichts.
(c) **Das Magnituden-Band [0,4x; 2,5x] ist lose.** Ein Fenster bei 2,4x und
eines bei 0,42x besteht -- Faktor 5,7 Spreizung zwischen den Fenstern gilt dann
als "konsistent".
(d) **Ein konkreter Retro-Test spricht dagegen.** H-20: OOS-2 erreichte die
Magnitude (+17,3 bps, p=0,17), OOS-1 verfehlte sie (p=0,40). Unter der neuen
Regel haette der gepoolte Schaetzer plausibel bestanden, und H-20 waere kein
DROP. Eine Regelaenderung, die mindestens ein bestehendes Verdikt umdreht, ist
per Definition eine Lockerung -- und zwar an genau der Stelle, an der das
Programm sein bestes Beispiel fuer Disziplin hat.

**Urteil.** Legitime Verbesserung **nur unter vier Auflagen**, sonst
Torpfosten-Verschiebung durch die Hintertuer:
1. Als eigenstaendige DEC beschliessen, **bevor** ein 3.0-Kandidat registriert
   ist, und nie kandidatenspezifisch. Wenn R2-K-01 sie braucht, um registrierbar
   zu sein (und nach 3.1 braucht er sie), dann ist die Reihenfolge
   Aenderung-dann-Kandidat zwingend und muss so protokolliert werden.
2. Nur zulaessig, wo die **Power-Zeile vor dem Lauf** eine Per-Fenster-Power
   < 0,6 ausweist. Fuer Zensus-artige, hoch-gepowerte Fragen bleibt C.10 hart.
3. Band von [0,4x; 2,5x] auf [0,5x; 2,0x] straffen **und** zusaetzlich
   verlangen, dass beide Fenster-Punktschaetzer das gleiche Vorzeichen UND
   jeweils >= 0,5x die registrierte Schwelle erreichen. Reines Vorzeichen
   reicht nicht.
4. Das gepoolte alpha wird auf 0,01 gesenkt, weil der Zwei-Fenster-Filter das
   alpha nicht mehr traegt. Sonst springt die gemeinsame
   Falsch-Positiv-Rate von 0,25% auf 2,5% -- Faktor 10, und **das** waere die
   eigentliche Lockerung, nicht die Regelform.
5. Pflicht-Retro-Check: die neue Regel wird auf H-06/H-20/H-22 angewendet und
   das Ergebnis veroeffentlicht. Kippt sie ein Verdikt, wird sie als Lockerung
   etikettiert und nicht als Verbesserung.

### 4.2 Praemie statt Sharpe als urteilstragende Groesse

**Fuer.** R4 K-0.2 ist unangreifbar: `T_min = 6,18/SR^2` heisst 6,2 Jahre fuer
SR 1,0 und 24,7 Jahre fuer SR 0,5, bei realistischer Schiefe 11,3 statt 6,2.
Der Bestand reicht 5-6 Jahre. Ein Sharpe-Gate auf dieser Datenlage ist entweder
unerreichbar oder bedeutungslos. Die Praemie ist direkt und kapitalfrei messbar
und trennt sauber Existenz- von Handelbarkeitsfrage (C.2).

**Gegen.** (a) Die Beobachtungszahl ist rhetorisch ueberzeichnet: "1.095
Funding-Beobachtungen statt 5 Jahresrenditen". Funding ist stark autokorreliert;
bei Blocklaenge ~30 Tagen ist das effektive N ~12/Jahr, nicht 1.095. Der reale
Power-Gewinn ist Faktor ~12, nicht ~219. R4s eigenes Verfahren (stationaerer
Bootstrap mit automatischer Blocklaenge) behandelt das korrekt -- die Begruendung
im Text tut es nicht. (b) Wichtiger: der Mittelwert einer Praemie ist genau die
Groesse, die ein Peso-Problem aufblaeht. Man tauscht eine ehrliche
Niedrig-Power-Statistik gegen eine Hoch-Power-Statistik ueber die falsche
Groesse. Fuer das RISIKO ist das effektive N die Zahl der Stress-Episoden
(1-3 in 5 Jahren), nicht 1.095.

**Urteil.** Legitim und notwendig -- **mit zwei Auflagen**: (1) jeder P-A-PASS
traegt verpflichtend das Etikett "Praemien-EXISTENZ; die risikoadjustierte
Frage ist auf diesem Bestand untestbar (MinTRL > Historie) und daher PARK, nicht
WEITER" -- R4 sieht das in P-B selbst vor, es muss aber im PASS-Text stehen, wie
die H-11/H-16-Etiketten; (2) kein Kapitalschritt darf aus einem P-A-PASS folgen.
Das adversariale Peso-Fixture (Merton-Spruenge, Rate 1/3 Jahre, -35%; ein
5-Jahres-Fenster ist mit p=0,19 sprungfrei) ist der beste einzelne
methodische Vorschlag in allen vier Berichten und ist Pflicht.

### 4.3 YAML-in-Markdown-Registry

**Fuer.** Der Kern ist richtig: eine Datei, eine Wahrheit, gezaeunter Block,
keine Migration der 2.0-Registry (die anzufassen waere ein schwererer Fehler als
jeder Komfortgewinn). Die neuen Pflichtzeilen werden linter-erzwingbar; die
zweistufige FDR (DEC-22) wird berechenbar statt handgefuehrt; ein Test kann
Code-Schwelle gegen Registry-Schwelle vergleichen -- das schliesst genau die
Fehlerquelle, die GL-029 war.

**Gegen / uebersehen.**
(a) Ein Linter, der einen Lauf blockieren kann, ist ein neuer Single Point of
Failure und muss selbst der Loud-Fail-Doktrin (C.14) unterliegen: er darf nie
still durchwinken, wenn er den Block nicht parsen kann.
(b) **Pflichtfelder werden zu Haekchen.** `structural_null: 0` erfuellt den
Parser und ist schlimmer als nichts. Der Linter muss statt eines Skalars eine
**Herleitungs-Referenz** verlangen (Dateipfad + Test-ID des Null-Fixtures), sonst
produziert er DEC-31-Wiedergaenger im Format-Gewand.
(c) Maschinenlesbarkeit macht die Registry **leichter still editierbar** als
Prosa. Die append-only-Eigenschaft muss mechanisch erzwungen werden (Test, der
die Bytes aller Alt-Eintraege hash-pinnt), sonst verliert man genau das, was die
Registry wertvoll macht.

**Urteil.** Legitime Verbesserung mit den drei Auflagen (a)-(c). Kosten ~1 h,
wie R4 sagt; die drei Auflagen kosten eine weitere Stunde und sind der
eigentliche Wert.

### 4.4 GPU-Default 0

**Fuer.** Empirisch stark: ~350 GPU-Stunden (nachgerechnet: 180+57+48..72+24..48
= 309-357), 2 kapitalfreie WEITER, 0 registrierte Tradability-Folgen; E.10 fuehrt
H-15b und H-16b explizit als NICHT registriert. Die Hypothesen waren so
geschnitten, dass ihr bestmoegliches Ergebnis nichts entscheiden konnte -- und
das war zum Registrierungszeitpunkt ablesbar. Die Regel kostet nichts, weil keine
der drei tragenden 3.0-Klassen GPU braucht.

**Gegen.** Die **harte 24-h-Wall-Clock-Obergrenze** ist selbst eine importierte
Schwelle ohne Herleitung -- exakt der C-14/D.2-Fehler, den R4 an anderer Stelle
zu Recht anprangert. Warum 24 und nicht 12 oder 72? H-15 lief 180 h,
checkpointet, und lieferte ein gueltiges WEITER; die Regel haette es verboten,
ohne dass jemand zeigen kann, dass das besser gewesen waere. Ausserdem ist die
Regel **redundant**: greift die Entscheidungsrelevanz-Klausel, kommt ohnehin
keine GPU-Welle durch; greift sie nicht, ist eine Stundenzahl das falsche
Instrument. R4 nennt selbst die richtige knappe Ressource: Kalenderzeit und die
Aufmerksamkeit des einzigen Betreibers -- die haengt nicht linear an GPU-Stunden.

**Urteil.** GPU-Default 0 = uebernehmen (Begruendungspflicht, kostenlos).
Harte 24-h-Grenze = **streichen oder herleiten**; ersetzen durch R4s eigene,
besser begruendete Regel 4.4.5 (Positivkontrolle laeuft zuerst und separat als
billiger T1-Schritt, ihr PASS ist Vorbedingung der Einplanung). Diese Regel
haette H-14s 2-3 verbrannte GPU-Tage verhindert; eine Stundengrenze haette es
nicht.

### 4.5 Zusatzbefund: R4s "oekonomische Mindestmagnitude" bricht C.2

Nicht angefragt, aber der schwerste Einzelbefund gegen R4. R4 1.1.c formuliert
die PASS-Bedingung als `mean >= max(strukturelle Null, oekonomische
Mindestmagnitude)`, wobei die oekonomische Mindestmagnitude = Zyklus-Kosten x 2.
Damit wandert die **Handelskosten-Wand in das Mess-Gate**. Folge: ein realer,
aber kleiner Effekt bekommt DROP statt "WEITER kapitalfrei / PARK Tradability" --
und DROP ist endgueltig und append-only. Unter dieser Regel waere H-04 (BTC->ETH
Lead-Lag, kapitalfrei WEITER, Tradability PARK) ein DROP gewesen, und die
Information "gerichtete Information existiert" waere geloescht worden. R4 fuehrt
C.2 zwei Seiten spaeter als "unveraendert bindend" auf.

**Urteil: C.2 gewinnt.** Die oekonomische Mindestmagnitude gehoert in die
**Entscheidungsrelevanz-Zeile** (lohnt der Alpha-Slot?) und in das
Tradability-Gate -- nicht in die PASS-Bedingung des Mess-Gates. Das ist direkt
urteilsrelevant fuer R3-K-31: dessen Schwelle (12 bps) liegt bewusst unter der
Wand. Unter R4s Regel waere K-31 nicht registrierbar; unter C.2 ist er es --
aber mit Pflicht-Etikett, dass der beste Fall keine Handelsperspektive hat.

---

## 5. RANGLISTE UEBER ALLE BERICHTE

### 5.1 Top 5

| Rang | Kandidat (vereinigte Fassung) | Begruendung |
|---|---|---|
| **1** | **Zensus-Paket: R2-V-0 + R4-WP-8** (Universum, Survivorship, `sigma_xs`, **`rho_quer`**, Alt-Symbol-Spread) | Alles in R2 und die Haelfte von R1 haengt an vier ungemessenen Zahlen. WP-4-Muster: eine Frage, ein binaerer Befund, toetet oder oeffnet eine ganze Klasse. Kann per Konstruktion nicht ergebnislos enden. Ein Wochenende, ~4 GB, kein Alpha-Budget. Der Spread-Teil ist moeglicherweise auf dem vorhandenen `bybit/tickers`-Strom in Minuten rechenbar -- Inhaltsprobe zuerst (C.8). |
| **2** | **R2-K-02 Querschnitts-Funding-Carry** (perp-only), mit R1s Ankerherleitung als Nulleffekt-Nachweis | Der einzige Kandidat, bei dem Mechanismus, Zahler, Friktion (kein Spot-Bein) und ein **exakt ausrechenbarer** Nulleffekt gleichzeitig stimmen -- und der einzige, dessen Ertragsquelle ein Cashflow und keine Prognose ist. Der Boersen-Anker, an dem R1-K-01 stirbt, kuerzt sich hier heraus. Konditional auf Rang 1 (rho_quer). |
| **3** | **R1-K-07 + R4 6.2(a)/6.3: Praemien-Kohaerenz + Maker-Fill-Schattenmessung** | Kein Ertragsanspruch, hoechste Entscheidungsdichte je Rechenstunde: entscheidet ueber die gesamte Portfolio-These UND ueber die Gueltigkeit jedes Maker-Kostenmodells im Options- und Hedge-Pfad. Vollstaendig aus dem Bestand, gebaute und getestete Werkzeuge (WP-2/WP-4-Replay). Teil (A) muss vorher auf Cluster-N umgestellt werden, sonst liefert er KEIN VERDIKT. |
| **4** | **R3-K-31 EXP-CLOCK** | Einziger Alpha-Kandidat mit null Nachladeaufwand, N~200 Ereignissen, exogen-kalendarischem Ereignis ohne Nachsuch-Freiheitsgrad und einem **Negativ-Panel aus Realdaten** statt aus Synthetik. Nutzt genau den Bestand, den laut DATA_INVENTORY keine Hypothese je genutzt hat. Abgewertet von R3s Rang 1 auf 4, weil der SE um ein Drittel zu guenstig gerechnet ist und ein PASS bei 12 bps a priori unterhalb der Wand liegt. |
| **5** | **DVOL-Backfill als WP** (R4 3.4 = R3-K-36 Datenhaelfte) | Verwandelt 112 Tage in ~1.980 auf dem einzigen lebenden Strategie-Pfad, kostet Sekunden, und liefert nebenbei den besten denkbaren Kreuzvalidierungstest des harvesteten `dvol`-Stroms (112 Ueberlappungstage). Ausdruecklich **ohne** R3s Terzil-Gate und **ohne** jede Wirkung auf die H-26-/C-33-Sperren. |

**Knapp verfehlt:** R1-K-03 (Perp vs. datierter Future). Beste Friktion im Feld
-- falls das Settlement wirklich gebuehrenfrei ist und falls die datierten
Kontrakte liquide sind. Zwei unbelegte, je einzeln toedliche Annahmen, beide in
einem Call bzw. einem Primaerquellen-Blick klaerbar. Das ist eine
10-Minuten-Vorfrage, kein Ranglistenplatz.

### 5.2 Die drei mit dem hoechsten S4/S5-Risiko (teure Infra vor validiertem Signal)

**1. R3-K-32 GEX-KOND.** Verlangt einen **neuen Harvester-Strom** (Options-Taker-
Tape) von einem Drittprojekt, plus Warten bis ~2027-05 fuer den N-Floor -- fuer
einen **Konditionierer** eines Haupteffekts (K-31), der noch nicht gemessen ist.
Das ist eine Datenpipeline fuer den Term zweiter Ordnung eines unvalidierten
Terms erster Ordnung. R3 sagt korrekt "nicht registrieren", stellt den
Harvester-Auftrag aber trotzdem sofort -- und **der Auftrag ist die
Infrastruktur-Ausgabe**. Disziplin: kein Options-Tape-Auftrag vor einem
K-31-PASS. Vgl. DEC-38: "billig" ist kein Registrierungsgrund.

**2. Der Panel-Store: R2s 1h-Panel (300 Symbole, 14,5 Mio Zeilen) + R4s WP-7
Daily-Panel-Cache** (Jahrespartitionen, `frozen/`/`open/`, eigenes
`panel_manifest.sqlite`, Fingerprints, monatlicher 1%-Stichproben-Integritaets-
job). Das ist ein zweites WP-0 und das teuerste Einzelstueck im gesamten
Berichtssatz -- vorgeschlagen, **bevor** `rho_quer` gemessen ist und damit bevor
feststeht, ob die Klasse, der es dient, ueberhaupt testbar ist. R4 liefert das
Argument (K-0.5) und schlaegt den Store danach trotzdem vor. Richtige
Reihenfolge: 1d-Klines (10 min, ~3.000 Requests) -> K, sigma_xs, rho_quer ->
**erst dann** Store-Bau, und nur in der Aufloesung, die die ueberlebende
Feasibility braucht.

**3. Der Options-Block R1-K-04/K-05/K-06.** Drei Kandidaten auf 38 Tagen Daten,
hinter H-26 gesperrt, mit ~12 Monaten noetiger Bybit-Quote-Aufzeichnung, und mit
Kostenmodellen, die 49% (K-04), 84% (K-05) und >100% (K-06) der jeweils
unterstellten Kante fressen -- bevor eine einzige Praemie gemessen ist. K-06
wird vom eigenen Autor "nur der Vollstaendigkeit halber" gefuehrt. Das Risiko ist
nicht die Registrierung (R1s Sequenz ist korrekt), sondern dass der
Aufzeichnungsapparat "weil er ohnehin laeuft" ausgebaut wird.

**Nachruecker (Methodik-Variante derselben Falle):** R4s `tradability3/`-Modul --
7 Dateien, `constants_hash`, `CostReport`-Dataclass, Stress-Overlay,
Kapitalprofil -- vorgeschlagen, bevor ein einziger 3.0-Kandidat ein Verdikt hat,
und mit **vier von sieben Modulen auf UNGEMESSENEN Konstanten** (Impact-k,
Margin-Regeln, Delivery-Gebuehr, Alt-Spreads). Empfehlung: `constants.py` und
`report.py` bauen (die beiden, die pinnen, was gemessen IST), den Rest als Stub
mit `raise NotImplementedError` -- was zugleich R4s eigener Loud-Fail-Doktrin
entspricht.

---

## 6. WAS IN ALLEN VIER BERICHTEN FEHLT

### 6.1 Rendite auf KAPITAL -- nirgends gerechnet

Alle Kanten stehen in bps des Notionals oder in % p.a. auf Notional. Kein Bericht
nennt fuer irgendeinen Kandidaten die Kapitalbindung. Konkret: R1-K-01 braucht
100% Notional auf dem Spot-Bein plus Perp-Margin -- die 8-10% p.a. auf Notional
sind bei ~110% Kapitaleinsatz eher 7-9% auf Kapital; R2-K-01/K-04 rechnen "2x
Brutto" und melden 28% p.a., ohne die Margin-Basis zu nennen. **Zwei Kandidaten
sind ohne Kapitalbasis nicht vergleichbar, und die Rangliste kann sich dadurch
drehen.** R4 sieht die Luecke (`capital.py`, "Bybit-Margin-Regeln UNGEMESSEN"),
zieht aber keine Konsequenz fuer die Kandidatenbewertung. Pflichtzeile fuer 3.0:
jede Ertragsangabe traegt ihre Kapitalbasis.

### 6.2 Steuern -- in vier Berichten kein einziges Mal erwaehnt

Fuer einen einzelnen deutschen Retail-Betreiber ist das nicht kosmetisch. Spot-
und Derivate-Bein einer delta-neutralen Position werden steuerlich
unterschiedlich behandelt (Spot potenziell 23-EStG-Logik mit Haltefrist,
Derivate Kapitalertragsteuer ~26,375% inkl. Soli). Eine **steuerlich
asymmetrische Hedge-Konstruktion kann bei einer Bruttokante von 5-10% p.a. den
Grossteil des Ertrags kosten** -- und R1-K-01 ist genau so konstruiert. Das
gehoert nicht in ein kapitalfreies Mess-Gate, aber zwingend in die
Entscheidungsrelevanz-Zeile und in jede Rangliste, die "netto" behauptet.

### 6.3 Boersen-/Gegenparteirisiko wird erwaehnt, nie quantifiziert

R1 kommt am naechsten (10.10.2025, ADL, Depegs; und die richtige Ablehnung von
Cross-Venue-Handel). Aber niemand beziffert: Verwahrrisiko auf Bybit, die
Wahrscheinlichkeit einer erzwungenen ADL auf dem **gewinnenden** Bein eines
delta-neutralen Paares (die eine gehedgte Position im schlechtesten Moment in
eine nackte verwandelt), Insurance-Fund-Erschoepfung, Auszahlungsstopp. Bei
einer Kante von 5-10% p.a. ist eine Ereigniswahrscheinlichkeit von 1%/Jahr fuer
einen Totalverlust ein Abschlag von 10-20% auf den Erwartungswert. R1s
Tail-Ratio misst Markt-Tails, nicht Venue-Tails. Pflichtzeile: "Venue-Ereignis"
in jeder Praemien-Registrierung.

### 6.4 Operator-Aufwand und der Verfassungswiderspruch beim Wochen-Rebalance

R2 schlaegt einen wochentlichen Dezil-Long-Short auf 150-300 Symbolen vor: ~60
Positionen, ~30-60 Orders pro Woche. Kein Bericht rechnet das in Betreiberzeit
um. Schwerer: die Programm-Randbedingung lautet **"kein Live-Order-Code"**.
Damit ist der beste Kandidat des Feldes einer, dessen Ausfuehrung das Programm
sich selbst verboten hat, und dessen manuelle Ausfuehrung fuer einen
Einzelbetreiber unrealistisch ist. R4 benennt den Preis der Regel nur fuer
Maker-Fills (6.3), nicht fuer die Ausfuehrbarkeit ganzer Kandidatenklassen.
**Die billigste zu MESSENDE Klasse ist die teuerste zu BETREIBENDE, und die
Verfassung blockiert sie.** Das gehoert vor die Wellenplanung, nicht danach.

### 6.5 Regime seit 2024: die REZENZ-Klausel wird formal, nicht inhaltlich angewendet

Alle vier Berichte zitieren C.18 und legen die Fenster hinter Mitte 2024. Keiner
fragt, **was sich strukturell geaendert hat**: der Spot-ETF-Start Anfang 2024 und
das dadurch zugefuehrte Basis-Arbitragekapital (das ist genau das Kapital, das
R1s Carry komprimiert -- R1 zitiert die Basis-Kompression 25% -> 4,46% und
verbindet sie nie mit dem Mechanismus), die Fragmentierung des Funding durch
On-Chain-Perps, und Bybits eigene Produkt-/Gebuehrenaenderungen. Die
entscheidende Frage jeder Praemie -- **existiert der ZAHLER nach 2024 noch?** --
wird nirgends gestellt. Pflichtzeile fuer jede Praemien-Registrierung.

### 6.6 "Stress-Episode" ist ein undefinierter Gate-Begriff

R1s G5 macht daraus eine Bedingung mit dem Ausgang KEIN VERDIKT; R4 weitet die
C-33-Auflage auf die ganze Klasse P aus. **Keiner definiert den Begriff
operational.** Damit ist "enthaelt eine Stress-Episode" nach dem Sehen der Daten
setzbar -- ein offener Torpfosten mitten in der neuen Verfassung. Erforderlich:
eine vorab fixierte, kanonische Stress-Tage-Liste mit deterministischer Regel
(z. B. Tagesrendite jenseits eines vorab festgelegten Quantils der
Gesamthistorie, plus die namentlich benannten Ereignisse 10.10.2025 und
19.08.2026), gepinnt als Fixture.

### 6.7 Korrelation der Praemien im Stress -- halb abgedeckt, und der wichtigere Teil fehlt

R1-K-07(A) ist die einzige Behandlung (R4 6.2(a) ist die generische Portfolio-
Luecke). Was auch dort fehlt: die relevante Korrelation ist nicht die zwischen
Praemien-PnLs, sondern die zwischen Praemien-PnL und der **Handlungsfaehigkeit
des Betreibers** (Margin-Call, Boersen-Ausfall, ADL, Auszahlungsstopp). Zweitens:
wenn alle Praemien derselbe Trade sind, sind F-PREM1/F-PREM2/F-XSEC1 **keine
unabhaengigen Familien**, und die zweistufige FDR (DEC-22) ist dann nicht in der
Weise verschaerfend, die DEC-22 unterstellt. Die Kohaerenzmessung ist damit
Vorbedingung fuer die Gueltigkeit der FDR-Struktur der ganzen Welle, nicht nur
fuer eine Portfolio-Aussage.

### 6.8 Kein Bericht sagt, was bei einem PASS passiert

31 Gate-Eintraege, sieben kapitalfreie WEITER, jedes davon in der eigens dafuer
registrierten Tradability-Pruefung PARK oder nie getestet. Vier Berichte
schlagen 21 neue Kandidaten vor und **keiner beschreibt den Pfad von einem WEITER
zum ersten Euro**: keine Kapitalplanung, keine Positionsgroessenregel, kein
Kriterium, ab wann gehandelt wird. R4s Entscheidungsrelevanz-Klausel ist das
Naechstliegende, betrifft aber GPU-Ausgaben, nicht Kapital. Ein 32. Gate-Eintrag
ist nicht offensichtlich mehr wert als die Definition dieses Pfades.

### 6.9 Provenienz-Risiko der neuen REST-Backfills

Alle vier Berichte haengen ab sofort an REST-Backfills von einer lebenden Boerse,
die historische Klines gelegentlich revidiert. Nur R4 sieht es (monatliche
1%-Stichprobe gegen Fingerprints). Das muss fuer **jeden** neuen Speicher gelten,
nicht nur fuer WP-7 -- inklusive des Funding-Backfills, an dem drei Kandidaten
haengen.

---

## 7. WAS VOR JEDER 3.0-REGISTRIERUNG ZU TUN IST (Kurzliste)

1. Eine Power-Konvention fixieren (alpha, Seitigkeit, Power) -- alle drei
   Berichte rechnen verschieden (3.10).
2. `rho_quer` messen. Ohne sie ist keine Querschnitts-Schwelle setzbar und V-0
   selbst waere ein C-14-Fall (3.1).
3. Inhaltsprobe auf `bybit/tickers` (C.8) vor jedem Spread-/OI-Zensus-Bau (3.6).
4. Kanonische Stress-Tage-Liste als Fixture pinnen (6.6).
5. Delivery-/Settlement-Gebuehren (Optionen UND datierte Futures) an der
   Primaerquelle klaeren oder alle davon abhaengigen Pfade RAISEN lassen (3.4).
6. Die Ein-Fenster-Regel-Aenderung als eigenstaendige DEC beschliessen, mit
   Retro-Check auf H-06/H-20/H-22, **bevor** ein Kandidat sie braucht (4.1).
7. Die oekonomische Mindestmagnitude aus der Mess-Gate-PASS-Bedingung entfernen
   und in Entscheidungsrelevanz + Tradability verschieben (4.5).
8. Funding-Intervall-Heterogenitaet (1h/8h) in jeder Funding-Rechnung (2.9).
9. Kapitalbasis, Steuerbehandlung und Venue-Ereignis als Pflichtzeilen jeder
   Praemien-Registrierung (6.1-6.3).
10. Den Widerspruch "bester Kandidat / kein Live-Order-Code" vor der
    Wellenplanung entscheiden (6.4).

---

*Ende REVIEW_R1_R4.md -- Gate-Auditor, 2026-09-02. Kein Verdikt hier ist ein
Registrierungs-Verdikt; alle Urteile sind Empfehlungen an den Orchestrator und
ersetzen keine Vorregistrierung.*
