# S3 - ASTROSTATISTIK: METHODEN FUER LUECKENHAFTE, UNREGELMAESSIG ABGETASTETE ZEITREIHEN

**Scout:** S3 | **Phase:** 3b Wissenschafts-Exkurs, Scinance 3.0 | **Stand:** 2026-09-03
**Pflichtlektuere gelesen:** `survey/ERKENNTNIS_KOMPENDIUM.md` (A-F vollstaendig);
`PRD_SCINANCE3.md` (1, 2, 3.1-3.9, 4.4, 5.2, 5.3, 7.1-7.3, 9.1-9.3);
`edge-research-v3/results/CROSSDOMAIN_PARK.md` + `CROSSDOMAIN_PRD.md`. Ergaenzend:
`research/R2_TAGES_WOCHEN_HORIZONT.md` (0.3D Nachweisgrenzen, "Was ich NICHT vorschlage").

**Vier Vorschlaege, alle Klasse X (Enabler) bzw. R (Regime-Konditionierer), alle horizontfrei,
alle CPU, GPU 0.** Keiner behauptet eine Kante, keiner braucht neue Stroeme, Kauf oder Keys.

---

## 0. Was die Disziplin beitraegt

Astronomie und Hochenergiephysik arbeiten routinemaessig unter genau den drei Bedingungen, an
denen dieses Programm wiederholt gescheitert ist:

1. **Die Null ist nie weiss.** Lichtkurven haben rotes Rauschen; jede gegen ein
   Dirac-/Weiss-Null gepruefte Metrik findet Struktur, die nicht da ist. Das ist das
   Dressing-Geschenk (B.9: CRPSS 0,21-0,29) - in der Astronomie eine benannte Standardfalle mit
   eigener Literatur.
2. **Der Trials-Faktor wird gerechnet, nicht behauptet.** Kein Peak-p-Wert ohne
   Look-Elsewhere-Deflation - die harte Fassung von PRD 3.3.4.
3. **Luecken sind der Normalfall.** Die Fensterfunktion wird mitpubliziert, weil Luecken sonst
   als Periodizitaeten erscheinen.

Der Bestand hat konkrete Loecher (L2 41/74 %, nur BTC/ETH; ETH-Options 2026-08-22..08-27
**endgueltig verloren**, E.8; Deribit 38-126 Tage; `allLiquidation` 43 Tage per 2026-08-10).
Dagegen steht ein bis H-19 nie genutztes Fundament: `bybit/publicTrade` lueckenlos ab 2020-03-25
und der WP-0-Bar-Cache (10.054 Cache-Tage, 14,4 Mio Minutenbars, SHA-256-gepinnt, F.2). **Alle
vier Vorschlaege haengen primaer daran, nicht an den jungen Stroemen** - das ist die
Feasibility-Entscheidung, die sie zulaessig macht.

**Abgrenzung zu R2 0.3D.** Die 41 bps/Tag sind die Nachweisgrenze fuer den **Mittelwert einer
nullzentrierten Renditeserie mit 350 bps Tages-SD**. Aktivitaets-/Intensitaets-Periodizitaet ist
eine strikt positive Groesse, deren SNR nicht am Renditerauschen haengt; die 41 bps sind dafuer
nicht bindend. **Die zugehoerige Aktivitaets-SD ist allerdings UNGEMESSEN** und ist die erste zu
liefernde Zahl. Kein Vorschlag unten setzt eine Renditeschwelle.

---

## X-ASTRO-1 - Bayesian Blocks als deterministische Regime-Segmentierung und gemessene Cluster-Einheit

**Methode.** Scargle, Norris, Jackson, Chiang (2013, ApJ **764**, 167, "Studies in Astronomical
Time Series Analysis. VI. Bayesian Block Representations"; Vorlaeufer Scargle 1998, ApJ 504,
405): exakte dynamische Programmierung findet die optimale stueckweise-konstante Zerlegung -
**kein Fensterparameter, keine Bandbreite, kein Gitter**. Additive Fitness (Poisson-Likelihood
fuer Ereignisdaten, Gl. 19; Gauss fuer gemessene Punkte, Gl. 41) minus Strafterm `ncp_prior` je
Changepoint. Der Strafterm ist nicht frei, sondern an eine Falsch-Positiv-Rate `p0` gebunden:

```
ncp_prior = 4 - ln( 73.53 * p0 * N^(-0.478) )     [Scargle 2013 Gl. 21, korrigiert]
p0=0,05, N=2008 -> 6,332      p0=0,05, N=730 -> 5,850
```
Beleg: `astropy/stats/bayesian_blocks.py`, Zeile `return 4 - np.log(73.53 * self.p0 *
(N**-0.478))`; korrigiert die im Original fehlerhafte Gl. 21 [sek: astropy-Quelltext GitHub,
abgerufen 2026-09-03; Originalpaper und docs.astropy.org egress-blockiert]. Der einzige mir
bekannte Segmentierer, dessen Tuning-Parameter eine **Fehlerrate ist**.

**Uebertragung.** WP-0-Bar-Cache, Tagesraster, BTC+ETH urteilstragend (SOL/BNB/XRP Bericht);
drei Kanaele: realisierte Tagesvol, Aktivitaet `n_trades`, Umsatz `vol_total`. Bericht
zusaetzlich: `deribit/dvol` (112+ T), `bybit/rest.fundingRate` (113+ T). **Horizont: keiner.
Klasse X mit Zweitrolle R.** Liefert (i) eine **gemessene** Cluster-Einheit statt der Konvention
"Kalendertag/Kalenderwoche" (DEC-51 Pkt. 3); (ii) ein **gemessenes** rho innerhalb und zwischen
Bloecken - DEC-51 verlangt "rho = 0 ist nie Default", der heute verwendete rho(BTC,ETH)=0,8 ist
ein **[sek]-Arbeitswert aus Review R1-R4 2.3, dort selbst ungemessen** (PRD 5.2); (iii) eine
operationale REZENZ-Definition (C.18): "juengstes Regime" = "letzter Block" statt eines
Halbjahres von Hand.

**Struktureller Nulleffekt.** Auf iid-Rauschen liefert der Strafterm im Mittel die Rate p0 - die
*einfache* und **falsche** Null. Die richtige: Bayesian Blocks nimmt Unabhaengigkeit
**innerhalb** eines Blocks an und zerschneidet deshalb auch eine **stationaere**
Langgedaechtnis-Serie. Das ist die Fehlerklasse, die Emmanoulopoulos, McHardy, Uttley (2010,
MNRAS **404**, 931) fuer Structure Functions belegt haben: "spurious breaks will appear in the
SFs of almost all light curves, even though these light curves may contain no intrinsic
characteristic time-scales", mit Bruch-Skalen abhaengig von Serienlaenge und PSD-Form.
**Bindend:** 1.000 Surrogate, die Randverteilung UND Autokorrelation erhalten (IAAFT bzw.
FIGARCH), aber keinen Regimewechsel enthalten; urteilstragend ist `n_blocks_real -
q95(n_blocks_surrogat)`, nie `n_blocks` selbst (C.4, L-2, R4 1.0).

**Feasibility.** N = 2008 Handelstage (2.190 Kalendertage im `panel_1d`-Raster); REZENZ-Fenster
W1 2024-09-01..2025-08-31, W2 2025-09-01..2026-08-31, davor Aera-Profil. A-priori: H-19/GL-025
findet keinen laufenden Drift, meldet aber ausdruecklich einen "einmaligen Uebergang bis
~2022->2024" der D3-Aktivitaetskonzentration - ein rollierender rho-Test kann ihn nicht
lokalisieren. Also **mindestens ein** echter Changepoint im Aera-Profil; die Zahl in den
Urteilsfenstern ist **UNBELEGT** (das ist die Messung). **Power (DEC-51: alpha 0,05, Power
0,80):** die Streuung der Zaehlstatistik ist erst nach dem Surrogatlauf bekannt - hier wird
**keine Zahl behauptet**. Die Registrierung setzt die Schwelle als `q95(Surrogat)` und rechnet
die Power gegen eine VOR dem Lauf fixierte Alternative; Power < 0,80 -> GL-012-Fall (C.12),
keine Registrierung. **REZENZ ist eingebaut:** liegt der letzte Blockwechsel vor 2024, sind
W1/W2 regime-homogen - das ist selbst der Befund.

**Rechenbudget.** Exakte DP O(N^2): N=2008 -> ~4,0e6 Zellen, Millisekunden. 1.000 Surrogate x 3
Kanaele x 5 Symbole: **< 10 CPU-Minuten**, RAM < 1 GB. GPU 0.

**Nicht-Duplikat.** (a) **H-19/GL-025 (C-19 DRIFT)** misst mit rollierender Rangkorrelation, ob
die Tape-Struktur *monoton driftet* - eine **Trendfrage**. Bayesian Blocks stellt die
**Sprungfrage** und liefert Zeitpunkte statt eines Koeffizienten; H-19s eigener D3-Nebenbefund
beweist, dass die Trendfrage die Sprungfrage nicht beantwortet. (b) **DEC-55/56** sind
Perzentilschnitte; DEC-56 haelt selbst fest, dass ein rollierender 97,5-%-Schnitt per
Konstruktion in jedem Fenster ~2,5 % Stresstage erzeugt und deshalb "nie binden" kann. Dieser
Vorschlag **ersetzt sie nicht stillschweigend** - er laeuft daneben und wird gegen sie
berichtet; eine Ersetzung waere nach dem DEC-55-Etikett eine **neue DEC vor dem Lauf**. (c) PARK
**IC-NET-1** (lambda2-Stress-Fruehindikator) ist ein "Overlay-ueber-Nichts" mit
Vorhersageanspruch; hier gibt es weder Overlay noch Vorhersage. (d) **Bayesian Blocks kommt im
gesamten Programm nicht vor** (Volltextsuche ueber alle Registry-, Gate-, Review- und
PARK-Dokumente).

**Entscheidungsrelevanz.** *PASS:* eine **gemessene** Cluster-Einheit und ein **gemessenes** rho
fuer jede kuenftige Power-Zeile (3.3.1/3.3.3) - heute stehen dort eine Konvention und ein
[sek]-Wert; dazu eine nicht-diskretionaere REZENZ-Definition und ein Kandidat fuer eine neue
Stress-DEC. *DROP:* die Kalendertag-/-wochen-Konvention ist dann **empirisch gerechtfertigt**
statt gesetzt, und die offene Frage aus L-6/DEC-51 Pkt. 3 ist geschlossen. Beide Ausgaenge
verwertbar - Definition eines guten Enablers.

**Fixture-Paar (DEC-39/C.5).** *Positiv:* stueckweise konstanter Prozess mit drei injizierten
Level-Spruengen; die Kanten MUESSEN auf +/-1 Tag getroffen werden. *Negativ:* stationaeres
FIGARCH-Surrogat mit identischer Randverteilung und ACF, **ohne** Sprung; die Blockzahl MUSS
innerhalb q95 bleiben - faellt dieses Fixture durch, ist die Methode fuer diesen Bestand
disqualifiziert. *Adversarial (3.3.5):* ein einziger glatter Trend ohne Sprung darf nicht als
Regimewechsel berichtet werden.

**Risiko-Etikett: Enabler.** Hoher Nutzen, geringe Kosten - aber alles haengt an der
Langgedaechtnis-Surrogat-Kalibrierung. Ohne sie waere es ein H-11-Wiedergaenger.

---

## X-ASTRO-2 - Matched-Filter-Bank mit gemessenem Hintergrund auf dem AKTIVITAETSKANAL des Verfalls-/Settlement-Fensters

**Methode.** Matched Filtering mit Template-Bank und empirisch geschaetzter Falschalarmrate wie
in der Gravitationswellen-Suche: Allen, Anderson, Brady, Brown, Creighton (2012, PRD **85**,
122006, FINDCHIRP) - der optimale lineare Filter fuer eine bekannte Form in **farbigem**
Rauschen ist das mit der Rausch-PSD geweisste Template, Statistik `SNR = <s,h>/sqrt(<h,h>)`. Neu
hier: die Falschalarmrate kommt aus einem **gemessenen Hintergrund** (Time-Slides /
Placebo-Termine) statt aus einer Verteilungsannahme; ein **chi^2-Zeit-Frequenz-Konsistenztest**
(Allen 2005, PRD **71**, 062001) verwirft Ausschlaege, deren Energieverteilung nicht zur
Template-Form passt. [sek fuer beide: LIGO-Standardreferenzen, Volltexte nicht geprueft.]

**Der Befund, der VOR jedem Lauf verfuegbar ist.** A2 (PRD 5.2) registriert genau eine
urteilstragende Statistik: `r_pre` = Log-Rendite ueber `[07:30, 08:00)` UTC. Eine Fensterrendite
ist der matched filter fuer eine **Stufe/Drift**. Die zitierte Evidenz beschreibt aber eine
**V-foermige Umkehr** (Finance Research Letters Juni 2026 [sek; R3 vermerkt: Autoren nicht
ermittelbar, Volltext gesperrt]). Die Sensitivitaet von `r_pre` gegen eine Form ist das
Skalarprodukt der normierten Formen:

```
Rampe h(t)=t gegen Rechteck:  cos = 0,5 / (1/sqrt(3)) = 0,866  ->  13,4 % SNR-Verlust
Symmetrische V-Umkehr mit Wendepunkt INNERHALB [07:30,08:00), Rueckkehr zum
   Ausgangsniveau:            r_pre -> 0                       ->  100 % Verlust
```
**A2 kann also aus rein geometrischen Gruenden ein Nullurteil liefern, auch wenn der Mechanismus
existiert** - naemlich wenn der Wendepunkt im Fenster statt an dessen Rand liegt. Diese Rechnung
kostet eine Stunde, ist unabhaengig von V-5 und steht heute in keinem Dokument.

**Uebertragung.** WP-0-Bar-Cache, 1-Minuten-Raster, Fenster `[06:30, 09:30)` UTC um jeden
Verfallstermin; BTC+ETH urteilstragend, XRP/BNB als Realdaten-Negativpanel (keine liquide
Optionskette - exakt das Panel, das A2 vorsieht). **Kanalwechsel, der eigentliche Vorschlag:**
gemessen wird nicht die Rendite, sondern der **Aktivitaets-/Flusskanal** (`n_trades`,
`vol_total`, signierter Fluss `(vol_buy-vol_sell)/vol_total` je Minute). Begruendung: der
Renditekanal hat 36 bps SD auf 30 Minuten (PRD 5.2) und ist nullzentriert; ein mechanisch
erzwungener 30-Minuten-Index-TWAP muss sich im Aktivitaetskanal **direkt** abbilden, wenn der
Mechanismus existiert - eine Mechanismus-Existenzfrage, keine Renditefrage. **Horizont: keiner.
Klasse E-Enabler / X.** **Template-Bank vorregistriert, K = 3:** (T1) Rampe mit Kollaps um
08:00, (T2) symmetrische V-Umkehr mit Wendepunkt 08:00, (T3) Rechteck-Plateau ueber `[07:30,
08:00)`; kein Scan ueber Formparameter. **Cluster-Einheit:** das Verfallsereignis ueber beide
Symbole = EIN Cluster (PRD 5.2 / DEC-51 Pkt. 3).

**Struktureller Nulleffekt.** (1) Ein Matched Filter liefert **immer** ein positives max-SNR
ueber die Bank - die Bank ist ein Trials-Faktor; Deflation ueber K=3 nach 3.3.4. (2) Das Null
ist die **gemessene** Hintergrundverteilung des SNR auf den drei A2-Placebos (P1
Nicht-Verfalls-Freitage; P2 Nicht-Freitags-08:00-UTC-Slots, zwingend wegen des Funding-Takts
00/08/16 UTC; P3 uebrige Tagesstunden), 1.000 Ziehungen gleicher Kalenderverteilung; bindend ist
der Placebo mit dem **groessten SE** (Orchestrator-Entscheidung PRD 5.2, uebernommen). (3)
**chi^2-Veto:** ein allgemeiner Vol-Spike passiert die reine SNR-Schwelle leicht; das Veto
verlangt den Ueberschuss im Zeit-Frequenz-Fussabdruck des Templates. Ohne Veto misst man "an
Verfallstagen ist mehr los" - trivial. (4) Die PSD zum Weissen wird auf **Nicht-Verfallstagen**
desselben Fensters geschaetzt.

**Feasibility.** N_cluster: Monatsverfaelle (belegt: Blasco/Corredor/Satrustegui 2023, IREF 85
[sek]) = 12 je 12-Monats-Fenster, 24 gepoolt; woechentliche Verfaelle = 52/104, **Existenz
UNBELEGT (Vorfrage V-5)**. Detektierbarer Effekt `d` in Einheiten der Ereignis-zu-Ereignis-SD
des SNR (z einseitig 2,4865; z gepoolt bei alpha 0,01 nach DEC-52(iv) 3,1680):

```
N_c =  12 (monatl., je Fenster) : SE = 0,2887 -> d = 0,718
N_c =  24 (monatl., gepoolt)    : SE = 0,2041 -> d = 0,647
N_c =  52 (woech., je Fenster)  : SE = 0,1387 -> d = 0,345
N_c = 104 (woech., gepoolt)     : SE = 0,0981 -> d = 0,311
```
Auf Monatsverfaellen sind ~0,65-0,72 SD noetig - viel, aber fuer ein mechanisch erzwungenes
Settlement-Fenster nicht absurd, und **ungleich guenstiger als A2s Renditekanal**, der gegen
seine eigene belegte Effektgroesse ein GL-012-Fall ist (16,5 bps gegen 25,2 bps detektierbar,
gepoolte Power 0,40; PRD 5.2). **UNGEMESSEN und Vorbedingung:** die Ereignis-zu-Ereignis-SD des
Aktivitaets-SNR im 07:30-08:00-Fenster - in CPU-Minuten aus dem Bar-Cache messbar, gehoert neben
V-5 in Welle 1. Ohne sie ist die Power-Zeile nicht ausfuellbar und die Registrierung unzulaessig
(3.3.1). **REZENZ:** W1/W2 identisch zu A2.

**Rechenbudget.** 3-h-Fenster x 24-104 Termine x 5 Symbole x 3 Templates plus 1.000
Placebo-Ziehungen: **< 5 CPU-Minuten**, RAM < 2 GB. GPU 0.

**Nicht-Duplikat - und die Abgrenzung zu CFAR/H-03 (D.4).**

| | H-03 / C-31 Cyclostationary CFAR (D.4, tot) | X-ASTRO-2 |
|---|---|---|
| Ereigniszeitpunkte | **endogen detektiert** | **exogen, kalendarisch fix** |
| Statistik | Zellschwelle gegen Nachbarzellen-Mittel, **keine Signalform** | SNR gegen **vorregistrierte Formbank**, PSD-geweisst, plus chi^2-Formveto |
| Nullmodell | angenommene Exponentialverteilung je Zelle, nominale Per-Zell-FAP, **nie global** | **gemessener** Hintergrund aus Placebo-Terminen gleicher Kalenderverteilung |
| Urteilsgroesse | **Kante in bps** (0,01-0,04 bp, ~250x unter der Wand) | Mechanismus-Existenz im Aktivitaetskanal; keine bps, kein Entry, kein Timing |
| Horizont | Sub-Sekunde | keiner |
| Verdikt | Surrogat-p ~ 1,0, DROP | offen |

CFAR ist ein **Detektor ohne Template und ohne globalen Hintergrund**; der Matched Filter ist
ein **Schaetzer fuer eine bekannte Form an bekannten Zeiten mit gemessenem Hintergrund**. D.4
verbietet die CFAR-Wiederaufnahme - hier wird kein Element davon uebernommen. Uebernommen wird
aber **A2s Objekt**; ehrliche Einordnung: **kein Konkurrent zu A2, sondern dessen
Mechanismus-Vorpruefung**. Nachbar PARK IC-MECH-1 (ADL-Trigger-Antizipation): anderes Ereignis,
anderer Strom, dort ein Timing-Signal, hier keines.

**Entscheidungsrelevanz.** *PASS* (SNR ueber allen Placebos, chi^2-Veto bestanden, Negativpanel
still): der Mechanismus existiert; A2s Renditefrage wird kalibriert - man weiss dann, welche
Form man sucht, und `r_pre` kann durch den passenden Filter ersetzt werden (neue Registrierung,
kein Torpfosten). Die A5-/H-26b-Auflage "Halte-bis-Verfall settelt in die Verzerrung hinein"
(Review R1-R4 3.5) wird erstmals quantifizierbar. *DROP:* der Mechanismus existiert im Bestand
nicht - A2s Renditetest ist a priori aussichtslos, **bevor** ein Alpha-Slot verbraucht wird;
Einsparbefund gegen die S4/S5-Falle (D.16) und gegen R3-K-32/GEX (PRD 9.1: "Kein
Options-Tape-Auftrag vor einem A2-PASS").

**Fixture-Paar (DEC-39/C.5).** *Positiv:* in eine reale Nicht-Verfallsserie injizierte Rampe/V
bekannter Amplitude; die Bank MUSS das richtige Template waehlen und das chi^2-Veto passieren.
*Negativ:* dieselben Termine mit erhoehter **breitbandiger** Volatilitaet ohne Form; SNR darf
die Schwelle reissen, das **chi^2-Veto MUSS ihn verwerfen** - genau dieses Fixture trennt
X-ASTRO-2 von CFAR. *Adversarial (3.3.5, Klasse E):* auf vergangenen Renditen selektierte
Ereignisse auf einem Random Walk (Fehlerklasse H-20); nach Placebo-Kalibrierung MUSS der Effekt
verschwinden.

**Risiko-Etikett: Blick wert.** Hoechste unmittelbare Entscheidungsrelevanz; Schwaeche:
N_cluster = 12/Fenster auf der belegten Monatsmenge, Ereignis-SD UNGEMESSEN.

---

## X-ASTRO-3 - Periodizitaets-Inventar der AKTIVITAET: Lomb-Scargle mit Baluev-FAP, Z^2_n auf Ereignisstroemen

**Methode.** Lomb-Scargle-Periodogramm (Lomb 1976, Ap&SS **39**, 447; Scargle 1982, ApJ **263**,
835) - Kleinste-Quadrate-Spektralanalyse fuer **ungleichmaessig abgetastete** Daten. Praktische
Fallstricke (Normierung, Fensterfunktion, Aliase, effektive Zahl unabhaengiger Frequenzen)
systematisch bei VanderPlas (2018, ApJS **236**, 16, doi 10.3847/1538-4365/aab766). Signifikanz
des **hoechsten** Peaks ueber ein Band in geschlossener Form aus der Extremwerttheorie: Baluev
(2008, MNRAS **385**, 1279, arXiv:0711.0330); EVT-/Bootstrap-Ergaenzung Sueveges (2014, MNRAS,
doi 10.1093/mnras/stu372). Fuer **reine Punktprozesse** ohne Binning: Z^2_n (Buccheri et al.
1983), `Z^2_n = (2/N) * sum_{k=1..n}[ (sum_j cos 2pi k phi_j)^2 + (sum_j sin 2pi k phi_j)^2 ]`,
unter der Null chi^2 mit 2n Freiheitsgraden; n=1 ist der Rayleigh-Test [sek: mehrfach
uebereinstimmend in der Pulsar-Literatur zitiert, A&A-Original nicht abrufbar].

**Uebertragung.** (a) **Aktivitaets-/Vol-Intensitaet**, WP-0-Bar-Cache, 1-Minuten-Raster, 5
Symbole - regulaer abgetastet, klassisches Periodogramm genuegt, aber dieselbe FAP-Maschinerie.
(b) **Liquidations-Ereignisrate**, `bybit/allLiquidation` BTC/ETH - echter Punktprozess, Z^2_n
auf Ereignisphasen, **kein Binning**. (c) **Funding**, `bybit/rest.fundingRate` plus
oeffentlicher Backfill `/v5/market/funding/history` (PRD 7.1: ~9.300 Requests, ~31 min); **V-1
fragt ausdruecklich, ob das Funding-Intervall ueber die Kontraktklassen identisch ist** - ist es
das nicht, ist die Universumsserie ungleichmaessig abgetastet und LS ist die richtige Methode
statt einer FFT. (d) **Open Interest**, `rest.openInterest` und der `bybit/tickers`-Deltastrom
(nur geaenderte Felder -> **intrinsisch unregelmaessig**) - die OI-Tiefe ist nach PRD 7.2 Pkt. 3
**UNBELEGT und der kritischste offene Datenpunkt**, daher Bericht, nicht urteilstragend.
**Vorregistrierte Linien statt Scan (die Disziplin):** 8 h (Funding 00/08/16 UTC), 24 h, 7 d, 1
h, 15 min, 5 min, 1 min - alle **exogen** aus Boersenkalender bzw. Taktung, nicht aus den Daten
gewaehlt. Damit K = 7 statt hunderter unabhaengiger Frequenzen. Ein Vollband-Scan laeuft
zusaetzlich, ist **nicht urteilstragend** und traegt die volle Deflation (X-ASTRO-4).
**Horizont: keiner. Klasse X / R.** Keine Rendite, keine Richtung, keine bps.

**A-priori (warum das kein Fischzug ist).** Auf einem Nachbarplatz mit vier von fuenf
identischen Symbolen ist der Effekt dokumentiert: periodische Ausbrueche von Volatilitaet und
Volumen an 1-Minuten-, 5-Minuten- und Viertelstundenmarken auf sechs Binance-USDT-Perps (BTC,
ETH, XRP, SOL, DOGE, ADA), mit scharf fallender Rundheit der Handelsgroessen innerhalb der
Ausbrueche [sek: arXiv:2607.09426 "The Quarter-Hour Effect"; Shynkevich, J. Futures Markets
2026, doi 10.1002/fut.70089 - **beide Volltexte egress-blockiert, alle Groessenangaben
UNBELEGT**]; ebenfalls [sek] und unbeziffert: Intraday-/Wochentagsmuster in Funding-Spreads, an
den Settlement-Mechanismus gekoppelt. Folge: die Linien 8 h / 1 h / 15 min / 5 min sind
**Positivkontrollen** nach C.13 - findet die Maschinerie sie nicht, ist ihr Nullbefund auf allen
anderen Linien uninformativ (Muster GL-020).

**Struktureller Nulleffekt - drei Pflichtschichten.**
1. **Trials-Faktor.** Unter weissem Gauss-Null ist die normierte Leistung an *einer festen*
   Frequenz Exp(1) (Mittel 1, SD 1) [sek: VanderPlas 2018]; ueber M unabhaengige Frequenzen
   `FAP(z) ~ M*exp(-z)`. Konkret, Tagesserie im 1-Minuten-Raster, Band [1/12h, 1/4min],
   Aufloesung 1/Tag: **M ~ 358**; fuer globale FAP 0,05 folgt `z = ln(358/0,05) = ln(7160) =
   8,876` gegen den naiven Ein-Frequenz-Wert `z = -ln(0,05) = 3,00` - **Faktor 2,96 in der
   Leistung**. Genau diese Luecke ist die Fehlerklasse von C-14 (importierte Schwelle) und H-11
   (Schwelle unter dem strukturellen Nulleffekt).
2. **Farbiges Rauschen.** Ein 1/f-Kontinuum erzeugt grosse Tieffrequenz-Peaks **ohne jede
   Periodizitaet**. Das Null ist ein PSD-erhaltendes Surrogat (Phasenrandomisierung/IAAFT) bzw.
   ein angepasstes gebogenes Potenzgesetz. Ohne diese Schicht misst man das Kontinuum und nennt
   es Signal.
3. **Fensterfunktion.** Sie wird **mitberichtet** (VanderPlas 2018). Bei den Loechern des
   Bestands (L2 41/74 %, Deltastroeme, Deribit 38-126 Tage, ETH-Options-Luecke) ist das nicht
   optional: jede Luecke erzeugt Aliaslinien am Abtastkamm; ohne veroeffentlichte
   Fensterfunktion ist ein Peak nicht interpretierbar.

**Feasibility.** Urteilstragend ist **nicht** ein globales Periodogramm ueber 5,5 Jahre (grosses
N, aber gemeinsame Schocks - L-6), sondern die **tageweise (bzw. wochenweise) normierte Leistung
an den vorregistrierten Linien**, gemittelt ueber Cluster, mit cluster-geclustertem stationaerem
Bootstrap. Unter der Null ist die Tagesleistung Exp(1), also SE = 1/sqrt(N_c):

```
Raster Tag (Perioden <= 12 h):
  N_c =  365 (je Fenster)          SE 0,0523 -> detektierbar 0,130 (13,0 %)
  N_c =  730 (gepoolt, z=3,1680)   SE 0,0370 -> 0,117 (11,7 %)
  N_c = 2008 (Aera-Profil)         SE 0,0223 -> 0,0555 (5,6 %)
Raster Woche (24 h, 7 d):
  N_c =   52 (je Fenster)          SE 0,1387 -> 0,345 (34,5 %)
  N_c =  104 (gepoolt)             SE 0,0981 -> 0,311 (31,1 %)
Liquidationen (allLiquidation, BTC/ETH):
  N_c ~   67 Tage (43 per DATA_INVENTORY 2026-08-10 + Kalenderzuwachs)
                                   SE 0,1222 -> 0,304 (30,4 %)
  zwei disjunkte Fenster a ~33 T   SE 0,1740 -> 0,433 (43,3 %)
```
Ehrlich: auf dem Bar-Cache ist die Power ueppig (5-13 % Leistungsueberschuss detektierbar); auf
den **Liquidationen** reicht es nur fuer eine **starke** Linie (die 8-h-Funding-Linie), schwache
Linien sind dort GL-012 und werden nicht registriert. Der Options-OI-Kanal ist heute nicht
registrierbar (s. u.). **REZENZ:** W1/W2 wie oben; der algorithmische Kamm ist per
H-19-Nebenbefund (D3-Uebergang bis ~2024) jung - Aera-Profil vor 2024 ist deskriptiv.

**Rechenbudget.** Schnelles LS ist O(N log N); 14,5 Mio Punkte, Periodogramme in Sekunden.
Kostenpunkt sind die Surrogate: 1.000 IAAFT je Tag und Symbol ~ 1e7 FFTs der Laenge 1440 ->
**1-3 CPU-Stunden**, parallelisierbar, RAM < 8 GB; unter der 24-h-Meldegrenze. GPU 0.

**Nicht-Duplikat.** (a) **H-03/C-31 (D.4)**: siehe Tabelle bei X-ASTRO-2; Zusatz: H-03
untersuchte *Inter-Arrival-Zeiten* auf Sub-Sekunden-Skala mit CFAR und urteilte in bps.
X-ASTRO-3 misst die **spektrale Leistung der Intensitaet** auf Minuten- bis Wochenskala gegen
ein **farbiges** Null mit Trials-Deflation und urteilt in Leistungsueberschuss.
**Ehrlichkeitszeile:** H-03s Surrogat-p ~ 1,0 ist das staerkste im Bestand existierende
Gegenargument gegen diesen Vorschlag und wird hier ausdruecklich zitiert. Es betrifft eine
andere Skala, Statistik und Frage - senkt aber den A-priori. Daher "Blick wert" und Rang 3,
nicht Rang 1. (b) **R2-K-06 / R2 0.3D**: gerichtete Kalendereffekte auf Tagesaggregaten, tot (41
bps/Tag) - andere Zielgroesse (Rendite vs. Intensitaet), keine Richtungsbehauptung hier. (c)
**A2-Placebo P2**: A2 braucht P2, weil der Funding-Takt einen Verfallseffekt vortaeuschen kann;
X-ASTRO-3 macht aus diesem einen Placebo ein **gemessenes Spektrum**. (d) **Lomb-Scargle,
Baluev, Z^2_n, Rayleigh kommen im gesamten Programm nicht vor** (Volltextsuche).

**Entscheidungsrelevanz.** *PASS:* (i) deflatiertes Taktfrequenz-Inventar mit kontrollierter
globaler FAP; (ii) das **farbige Nullmodell**, das jede kuenftige
Intensitaets-/Ereignishypothese braucht und heute niemand hat; (iii) die quantitative Grundlage
fuer A2s P2; (iv) die Antwort, ob das 07:30-08:00-Settlement-Fenster spektral vom Funding-Kamm
trennbar ist - **Vorbedingung dafuer, dass A2 ueberhaupt interpretierbar ist**. *DROP:* die
Erklaerung "verborgener Kalendertakt" ist fuer alle kuenftigen Nullbefunde geschlossen, A2s P2
wird Formalie, und jeder kuenftige Vorschlag auf Aktivitaetsperiodizitaet ist a priori tot.
**Nicht impliziert:** irgendeine Handelsfolge (s. Pkt. 3 unten).

**Fixture-Paar (DEC-39/C.5).** *Positiv:* reale Serie plus injizierter Sinus/Kamm bekannter
Amplitude bei 8 h und 15 min; beide MUESSEN mit korrekter Amplitude und globaler FAP < 0,05
wiedergefunden werden. *Negativ:* stationaeres, phasenrandomisiertes 1/f-Surrogat **ohne**
Linie; an keiner vorregistrierten Linie darf ein Ueberschuss ueber q95 gemeldet werden - das ist
der eigentliche Test. *Adversarial:* dieselbe Serie mit realistischen Blockluecken (L2-artig, 41
% Abdeckung); die Aliaspeaks MUESSEN von der mitberechneten Fensterfunktion erklaert und
etikettiert werden.

**Risiko-Etikett: Blick wert**, mit Enabler-Charakter. Beste Power, breitester Nutzen - aber der
naechste Nachbar ist ein D.4-Eintrag; die Registrierung braucht eine ausdrueckliche
Orchestrator-Abgrenzung, keine Selbsterklaerung des Scouts.

---

## X-ASTRO-4 - Look-Elsewhere-Deflation ueber Upcrossings (Gross/Vitells) fuer KONTINUIERLICHE Suchparameter

**Methode.** Gross & Vitells (2010, Eur. Phys. J. C **70**, 525, "Trial factors for the look
elsewhere effect in high energy physics", arXiv:1005.1891): wird eine Teststatistik `q(theta)`
ueber einen **kontinuierlichen** Parameter maximiert, gilt

```
p_global  <=  p_local  +  <N(c0)> * exp( -(c - c0)/2 )
```
mit `<N(c0)>` = mittlere Zahl der Aufwaertsdurchgaenge des Levels `c0` durch `q(theta)`. Der
Clou: `<N(c0)>` wird bei einem **niedrigen** Level aus wenigen Monte-Carlo-Laeufen geschaetzt
und analytisch nach oben extrapoliert - ~100 Toys statt ~10^5 fuer eine Deflation im
1e-4-Bereich.

**Uebertragung.** Kein Datenstrom, ein **Methodenmodul** (`stats3`) plus Nachrechnung an
konservierten Payloads. **Klasse X (Enabler), horizontfrei.** Die Luecke: PRD 3.3.4 deflatiert
ueber die Bailey/LdP-Decke mit einem **diskreten** K (K=5 -> 0,53; K=20 -> 0,85; K=50 -> 1,02).
Mehrere tote 2.0-Hypothesen haben aber ein **Kontinuum** durchsucht: H-04/H-18 ("signifikante
Lags 1-3 s"), H-20 (3,5-sigma-Schwelle), H-06 (Einbettungsdimension) - dazu X-ASTRO-3s
Vollband-Scan. Bei einem Kontinuum ist ein handgezaehltes K systematisch zu klein; Bailey/LdP
beantwortet ausserdem eine **andere** Frage (erwartetes Maximum der Sharpe ueber K Backtests)
als Gross/Vitells (globaler p-Wert eines Maximums ueber einen Suchraum). **Beide gehoeren ins
Programm, keiner ersetzt den anderen.**

**Zahlenbeispiel (hergeleitet, nicht importiert).** Scan ueber Lag 1..10 s liefert lokal Z =
3,0, also c = 9,0, `p_local = 1,35e-3`. Aus 100 Toys bei c0 = 1 werden im Mittel 3 Upcrossings
gemessen:
```
p_global ~ 1,35e-3 + 3*exp(-(9-1)/2) = 1,35e-3 + 3*0,018316 = 0,0563
Trials-Faktor = 0,0563 / 1,35e-3 = 41,7
```
Aus "Z = 3,0, hochsignifikant" wird "p = 0,056, nicht signifikant". **Programmbezug mit
Kostenzahl:** H-18/GL-014 war ein Aufloesungs-Audit, das die Surrogatzahl von 200 auf 100.000
hochfuhr, um *lokale* p-Werte aufzuloesen. Die Upcrossing-Methode erreicht dieselbe Tiefe mit
~100 Toys - und macht ueberhaupt erst eine **globale** Aussage moeglich, wo H-18 nur eine lokale
praezisiert hat.

**Struktureller Nulleffekt.** Die Methode **misst** den strukturellen Nulleffekt eines Maximums
- das ist ihr Zweck. Eigene Kalibrierung: QQ-Vergleich zwischen `p_global(Formel)` und der
direkt aus 100.000 Toys gemessenen Tailverteilung an einem noch messbaren Punkt (p ~ 1e-3);
Abweichung > Faktor 2 -> nicht anwendbar, das Modul verweigert laut (C.14). Der
Gueltigkeitsbereich haengt an einer asymptotisch chi^2-verteilten lokalen Statistik -
**Erreichbarkeitspruefung im Sinne von L-1**, Pflichtbestandteil.

**Feasibility.** N in Cluster-Einheiten entfaellt (Methodenmodul); Validierung an konservierten
Payloads (T4) und synthetischen Statistiken. Erwartete Wirkung: Trials-Faktoren ~5 (schmaler
Scan) bis ~50 (breiter Scan). Fuer die 2.0-Faelle **UNBELEGT**, weil deren Roh-Statistikserien
nicht gespeichert wurden - genau die Luecke, die DEC-53 schliesst. **Eine nachtraegliche
Deflation bestehender 2.0-Verdikte ist damit nicht moeglich und wird ausdruecklich nicht
versucht** (append-only, urteilstragend; C.1 / PRD 9.1). Power: n/a - das Modul verschiebt keine
Schwelle, es rechnet eine Deflation; **rein verschaerfend, nie erleichternd** (wie die
zweistufige FDR, C.16/DEC-22). REZENZ: n/a.

**Rechenbudget.** 100-1.000 Toys je Anwendung: Sekunden bis Minuten. Modul ~200 Zeilen plus
T0/T1/T2/T4. GPU 0, RAM vernachlaessigbar.

**Nicht-Duplikat.** (a) **PRD 3.3.4 / K-0.3 (Bailey/LdP)**: diskretes K, Zielgroesse "erwartetes
Maximum der Sharpe" - andere Frage, andere Groesse; X-ASTRO-4 ergaenzt. (b) **C.16 / DEC-22
(zweistufige BH-FDR)**: kontrolliert die FDR ueber eine **endliche Familie vorregistrierter
Hypothesen**; ein Kontinuum ist keine endliche Familie, BH ist dort nicht anwendbar ohne
willkuerliche Diskretisierung. (c) **H-18/GL-014**: Aufloesungs-Audit derselben *lokalen*
p-Werte, nie eine globale Deflation. (d) PARK **IC-RMT-3** (Levy-stabile RMT-Nullverteilung)
betrifft die Form einer Eigenwert-Nullverteilung, nicht die Deflation eines Maximums ueber einen
Suchraum. (e) **Trials-Faktor / Look-Elsewhere / Upcrossings kommen im Programm nicht vor.**

**Entscheidungsrelevanz.** *PASS* (Formel reproduziert die empirische Tailverteilung innerhalb
Faktor 2): `stats3` bekommt eine Pflichtfunktion, und die YAML-Zeile `selection: {K,
ceiling_analytic, ceiling_measured_ref}` ein drittes Feld fuer kontinuierliche Suchraeume. Jede
kuenftige Registrierung, die einen Parameter scannt, wird damit ueberhaupt erst zulaessig -
heute ist sie es streng genommen nicht, weil ihre Deflation nicht rechenbar ist. *DROP* (Formel
bricht auf den Statistiken dieses Programms zusammen): dann ist belegt, dass kontinuierliche
Scans hier nur ueber teure direkte MC-Tails deflatierbar sind, und die richtige Programmregel
lautet: keine kontinuierlichen Scans, Punkt.

**Fixture-Paar (DEC-39/C.5).** *Positiv:* `q(theta)` mit injiziertem echtem Peak bekannter
Amplitude - `p_global` MUSS klein bleiben. *Negativ:* reines Rauschen, dessen Maximum ueber
theta lokal Z = 3,0 erreicht - `p_global` MUSS > 0,05 herauskommen; das ist der Test, der die
Methode rechtfertigt. *Adversarial:* eine Statistik mit stark nicht-chi^2-artiger lokaler
Verteilung (schwere Tails) - die Erreichbarkeitspruefung MUSS fehlschlagen und das Modul MUSS
laut verweigern statt eine Zahl zu liefern (C.14).

**Risiko-Etikett: Enabler.** Geringstes Risiko, geringste Kosten, kein Datenbedarf; dafuer nur
wirksam, wenn ueberhaupt ein Kontinuum durchsucht wird - und PRD 3.0 verbietet Fenster-Scans
bereits weitgehend (5.2: "kein Fenster-Scan").

---

## RANGLISTE

| Rang | ID | Klasse | Begruendung |
|---|---|---|---|
| **1** | **X-ASTRO-1** Bayesian Blocks | X / R | Groesster Programmhebel bei bester Feasibility: liefert die **gemessene** Cluster-Einheit und das **gemessene** rho, die DEC-51 Pkt. 3 verlangt und die heute Konvention bzw. [sek]-Arbeitswert sind, plus eine nicht-diskretionaere REZENZ-Definition. N = 2008 Tage, < 10 CPU-Minuten. PASS und DROP beide verwertbar. |
| **2** | **X-ASTRO-2** Matched Filter, Aktivitaetskanal | E-Enabler / X | Hoechste unmittelbare Entscheidungsrelevanz: stuetzt oder toetet A2 vor der Registrierung und spart im DROP-Fall einen Alpha-Slot plus den R3-K-32-Datenauftrag. Enthaelt einen **heute schon verfuegbaren analytischen Befund** (V-Umkehr im Fenster -> `r_pre` -> 0). Abzug: N_cluster = 12/Fenster auf der belegten Monatsmenge, Ereignis-SD UNGEMESSEN. |
| **3** | **X-ASTRO-3** LS/Z^2_n-Periodizitaetsinventar | X / R | Beste Power (5-13 % detektierbarer Leistungsueberschuss) und breitester Nutzen (farbiges Nullmodell fuer alle kuenftigen Intensitaetsfragen, quantitatives A2-P2). Abzug: naechster Nachbar ist mit H-03/C-31 ein **D.4-Eintrag**; H-03s Surrogat-p ~ 1,0 senkt den A-priori. |
| **4** | **X-ASTRO-4** Upcrossing-Trials-Faktor | X | Billigster und risikoaermster Vorschlag, schliesst eine echte Luecke (diskretes K deckt kein Kontinuum), aber marginaler Nutzen, solange 3.0 Scans ohnehin weitgehend verbietet. Zugleich Vorbedingung des nicht-urteilstragenden Vollband-Scans in X-ASTRO-3. |

**Falls nur eines laeuft:** die *analytische* Haelfte von X-ASTRO-2 (die
Form-Retentions-Rechnung fuer `r_pre`) zuerst - eine Stunde, kein Datenlauf, und sie kann A2s
einzige urteilstragende Statistik als formblind entlarven, bevor V-5 beantwortet ist.

---

## NICHT VORGESCHLAGEN - UND WARUM

1. **Structure Functions als urteilstragende Metrik** (im Auftrag ausdruecklich genannt).
   Emmanoulopoulos, McHardy, Uttley (2010, MNRAS **404**, 931) zeigen per Simulation: **in fast
   jeder Lichtkurve erscheinen Scheinbrueche in der SF, auch wenn die PSD strukturlos ist**, mit
   Bruchskalen abhaengig von Serienlaenge und PSD-Form. Das ist exakt die B.9-/H-11-Fehlerklasse
   - eine Metrik, deren struktureller Nulleffekt das gesuchte Merkmal bereits erzeugt. Zulaessig
   nur als **berichtete Diagnostik mit gemessener Artefaktverteilung** in X-ASTRO-3, nie als
   Gate-Groesse.

2. **Box-Least-Squares (Kovacs, Zucker, Mazeh 2002, A&A **391**, 369) fuer periodische
   Liquiditaets-"Dips" um Settlement-Zeiten.** Drei Gruende, jeder hinreichend: (a) BLS
   **scannt** Periode, Dauer und Phase - ein dreidimensionales Kontinuum, der schlechteste
   Trials-Faktor-Fall; (b) die Periode ist hier **nicht unbekannt**, sondern kalendarisch exogen
   (Funding 00/08/16 UTC, Settlement 08:00 UTC, Stunden-/Viertelstundenkamm) - der gesamte Wert
   von BLS liegt im Finden einer *unbekannten* Periode, bei bekannter Periode sind Epoch-Folding
   bzw. der Matched Filter (X-ASTRO-2) strikt besser und ohne Look-Elsewhere ueber die Periode;
   (c) der Kanal fuer einen echten Tiefen-Dip ist L2 - 41/74 % Abdeckung, nur BTC/ETH, und nach
   PRD 9.1 (R3-K-35) nur ~2,5 Monate REZENZ-konforme `orderbook.1000`. Ein Zwei-Fenster-Design
   ist dort nicht baubar. **Superseded und infeasible.**

3. **Jede gerichtete Nutzung der Intraday-Periodizitaet**, insbesondere der dokumentierte
   4-12-h-Prognosegehalt der Viertelstunden-Orderimbalance [sek: arXiv:2607.09426, Volltext
   gesperrt]. Zwei unabhaengige Kills: (a) **Verfassung** - PRD 1/3.3.2 und die
   Auftragsrandbedingung lassen Gerichtetes unter ~1 Tag nur als Kosten-/Strukturmessung zu;
   (b) **Arithmetik** - Viertelstundenoeffnungen treten 96x/Tag auf; schon ein Bruchteil davon
   als Positionswechsel ergibt `96 * 11 bp = 1.056 bp/Tag` Friktion gegen eine BTC-Tagesvol von
   262 bp (K-0.1). Um mehr als eine Groessenordnung tot, bevor eine Kante gemessen wird. Die
   Periodizitaet selbst bleibt messenswert - als Regime-Konditionierer, nicht als Signal.

4. **Gaussian-Process-/CARMA-Kontinuumsmodellierung (Kelly et al. 2014, ApJ 788, 33 [sek]) als
   Imputationsschicht.** Technisch die eleganteste Antwort auf L2 41-74 % - und genau deshalb
   gefaehrlich: die Hyperparameter werden zu einem unregistrierten Freiheitsgrad, der in jede
   nachgelagerte Statistik durchschlaegt (Fehlerklasse L-1/C-14 mit Zwischenschritt).
   Verschaerfend: die ETH-Options-Luecke ist nach E.8 **endgueltig verloren**, fuer
   22.08.-24.08. 14:00 existiert **gar keine Quelle** - dort zu imputieren hiesse, Daten zu
   erzeugen. Zulaessig ist nur der Weg von X-ASTRO-3: Fensterfunktion mitrechnen und
   mitpublizieren, nicht die Luecke fuellen.

5. **Periodizitaets-/Epoch-Folding-Analyse auf dem OPTIONS-Open-Interest** (im Auftrag genannt).
   `deribit/tickers` ~38 Tage, `markprice.options` 43 Tage (ab 2026-06-16), Bybit-Options-Ticker
   mit unverifizierter Tiefe (E.9), plus die ETH-Luecke. Unter REZENZ ergibt das **ein** Regime
   und **ein** Fenster - die Zwei-Fenster-Regel (C.10) ist strukturell nicht erfuellbar, und der
   Options-Block ist ohnehin hinter H-26/E.6 gesperrt. **GL-012 a priori, kein Lauf noetig.**
   Entsperr-Bedingung: >= 2 disjunkte REZENZ-konforme Fenster mit lueckenlosen `done_days` auf
   `markprice.options` je Symbol - fruehestens etwa Mitte 2027 und erst nach einem H-26-Verdikt.

6. **Jede Wiederaufnahme von CFAR in irgendeiner Form** (D.4). X-ASTRO-2 uebernimmt
   ausdruecklich kein Element davon; die Unterschiede stehen dort in einer eigenen Tabelle, weil
   die Verwechslungsgefahr real ist.

7. **Multiharmonische Periodogramme (Schwarzenberg-Czerny 1996 [sek]) und CLEAN-Dekonvolution
   (Roberts, Lehar, Dreher 1987 [sek])** als eigene Vorschlaege. Sinnvolle *Varianten* innerhalb
   X-ASTRO-3, aber jede Variante erhoeht K und damit die Selektions-Decke (3.3.4). Tiefe vor
   Breite: eine Methode sauber deflatiert statt vier mit aufgeblaehtem K.

8. **Jede GPU-Nutzung.** Keiner der Vorschlaege braucht sie; DEC-57 verlangte sonst eine
   Begruendung, die nicht existiert. Groesster Posten ist X-ASTRO-3 mit 1-3 CPU-Stunden, unter
   der 24-h-Meldegrenze.

---

## BELEGSTATUS

**Primaerliteratur, Zitat verifiziert** (Autoren/Titel/Venue/Jahr per Websuche bestaetigt;
Volltexte ueberwiegend nicht abrufbar - Egress-Proxy):

- Scargle, Norris, Jackson, Chiang (2013) ApJ 764, 167 - Bayesian Blocks
- Lomb (1976) Ap&SS 39, 447; Scargle (1982) ApJ 263, 835 - LS-Periodogramm
- Baluev (2008) MNRAS 385, 1279 (arXiv:0711.0330) - analytische FAP aus EVT
- Sueveges (2014) MNRAS, doi 10.1093/mnras/stu372 - EVT-/Bootstrap-FAP
- VanderPlas (2018) ApJS 236, 16, doi 10.3847/1538-4365/aab766
- Gross & Vitells (2010) EPJC 70, 525 (arXiv:1005.1891) - Trials-Faktor/Upcrossings
- Kovacs, Zucker, Mazeh (2002) A&A 391, 369 (astro-ph/0206099) - BLS
- Emmanoulopoulos, McHardy, Uttley (2010) MNRAS 404, 931 - SF-Artefakte (Kernaussage woertlich
  aus dem Abstract belegt)

**[sek] - nur ueber Sekundaerquelle, Quelle benannt:**

- Buccheri et al. (1983) Z^2_n/Rayleigh - Formel und Nullverteilung mehrfach uebereinstimmend in
  der Pulsar-Literatur zitiert, A&A-Original nicht abrufbar
- Allen et al. (2012) PRD 85, 122006 (FINDCHIRP) und Allen (2005) PRD 71, 062001
  (chi^2-Diskriminator) - LIGO-Standardreferenzen, Volltexte nicht geprueft
- Kelly et al. (2014) ApJ 788, 33 (CARMA); Roberts/Lehar/Dreher (1987) CLEAN;
  Schwarzenberg-Czerny (1996) - nur in Absagen erwaehnt
- `ncp_prior`-Formel aus `astropy/stats/bayesian_blocks.py` (GitHub, abgerufen 2026-09-03), die
  die fehlerhafte Gl. 21 korrigiert (arXiv:1304.2818); **Originalpaper und docs.astropy.org
  egress-blockiert**
- Quarter-Hour-Effekt: arXiv:2607.09426 und Shynkevich, J. Futures Markets 2026,
  doi 10.1002/fut.70089 - **beide Volltexte egress-blockiert** (arxiv.org,
  onlinelibrary.wiley.com); belegt ist nur die **Existenz** der Muster
  (1-min/5-min/Viertelstunden-Ausbrueche, Binance-USDT-Perps BTC/ETH/XRP/SOL/DOGE/ADA), **alle
  Groessenangaben UNBELEGT**

**UNBELEGT / UNGEMESSEN (namentlich, damit nichts geraten wird):**

- Ereignis-zu-Ereignis-SD des Aktivitaets-SNR im 07:30-08:00-UTC-Fenster (X-ASTRO-2,
  Vorbedingung der Power-Zeile; in CPU-Minuten messbar)
- Amplituden der Aktivitaetsperiodizitaeten auf **Bybit** (die Literatur misst Binance)
- Zahl echter Changepoints in den Urteilsfenstern (X-ASTRO-1)
- Trials-Faktoren der konkreten 2.0-Faelle - nicht nachrechenbar, weil Roh-Statistikserien nicht
  gespeichert wurden (die Luecke, die DEC-53 schliesst); eine nachtraegliche Deflation
  bestehender Verdikte wird **nicht** versucht
- Existenz woechentlicher Deribit-Verfaelle (V-5) und OI-Historientiefe (PRD 7.2 Pkt. 3) -
  bleiben Vorfragen des PRD, nicht dieses Exkurses

**Ohne Neuherleitung aus dem Bestand zitiert** (Kompendium B/D/E/F, PRD 9.2): B.1 (11/~15 bps);
B.16 (Datenreichweite); F.1 (Stromabdeckungen); F.2 (WP-0-Bar-Cache); F.3 (Hardware); K-0.1
(sigma_1d = 262 bp); K-0.3 (Selektions-Decke); DEC-51-Konstanten (2,4865 / 2,8016 / 3,1680);
DEC-52 (i)-(v); DEC-53; DEC-55/56; DEC-57; PRD 5.2 (Vol-Kette 36 bps, N_eff-Rechnung,
Placebosaetze, A2-Fenster, 16,5 vs. 25,2 bps); R2 0.3D (41 bps/Tag, sigma_BTC 350 bps);
D.4 (H-03/CFAR); E.8/E.9 (Luecken).

*Ende S3_ASTROSTATISTIK.md - read-only im Repo, nur im Scratchpad geschrieben.*
