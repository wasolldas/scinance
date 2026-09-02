# Scinance 3.0 - Programmentwurf (Orchestrator-Synthese nach Phase 3)

> Stand 2026-09-02. Grundlage: Erkenntnis-Kompendium (survey/), vier
> Tiefen-Recherchen R1-R4 (research/) und der adversarische Review
> (research/REVIEW_R1_R4.md). Dieses Dokument ist die ENTSCHEIDUNG des
> Orchestrators, nicht eine weitere Meinung; wo es dem Review folgt, steht
> es dabei, wo es abweicht, steht warum. Es ist die Vorlage fuer das PRD 3.0.

## 0. Bilanz und Pivot in drei Saetzen

2.0 hat 31 Gate-Eintraege ohne einen einzigen verschobenen Torpfosten und
ohne eine einzige handelbare Kante produziert. R4 zeigt, dass das arithmetisch
vorgezeichnet war: ein PERFEKTES 1-Sekunden-Orakel verdient 0,71 bp gegen
eine 11-bp-Wand; jede Hypothese unter ~7 Stunden Horizont war a priori tot.
3.0 sucht deshalb ausschliesslich dort, wo die Wand irrelevant wird - bei
Risikopraemien (Cashflow statt Prognose) und auf Tages- bis Wochen-Horizont
mit BREITEM Universum - und misst VORHER, ob die Klasse ueberhaupt testbar ist.

## 1. Die vier Zahlen, die 3.0 regieren (alle hergeleitet, keine Meinung)

| Groesse | Wert | Konsequenz |
|---|---|---|
| Horizont-Friktions-Kurve (R4 K-0.1) | Mindesthorizont bei p=0,55: 6,6 h Taker / 53 min Maker; bei Wochen-IC 0,05: 2,7 Tage | Kein 3.0-Kandidat unter Tageshorizont, ausser als reine Kosten-/Zensus-Messung |
| Sharpe-Nachweisdauer (Lo 2002) | T_min = 6,2/SR^2 Jahre; SR 0,5 braucht 25 Jahre | Sharpe ist NIE urteilstragend; die Praemie selbst ist es (10^3-10^4 Beobachtungen) |
| IC-Nachweisgrenze (R4 K-0.5) | N=5: 0,098; N=50: 0,03-0,07 je nach rho_quer | Das breite Universum ist Existenzbedingung der Querschnitts-Klasse, und rho_quer (Restkorrelation nach Demeaning) ist die bindende, UNGEMESSENE Zahl |
| Ein-Fenster-DROP bei Power 0,5 (R4 K-0.6) | verwirft 3 von 4 echten Effekten | Regelaenderung nur als eigenstaendige DEC vor jedem Kandidaten, mit den 5 Review-Auflagen (unten 2.3) |

## 2. Verfassungs-Deltas fuer 3.0 (Entscheidung)

### 2.1 Unveraendert uebernommen
Alle 19 Methoden-Lehren des Kompendiums (C.1-C.19). Insbesondere bleibt
**C.2 (Mess-Gate != Tradability-Gate) unangetastet**: R4s Vorschlag, eine
oekonomische Mindestmagnitude in die PASS-Bedingung des Mess-Gates zu nehmen,
wird ABGELEHNT (Review 4.5: haette H-04 zum DROP gemacht und Information
geloescht). Die Mindestmagnitude wandert in die Entscheidungsrelevanz-Zeile.

### 2.2 Neue Pflichtzeilen jeder 3.0-Registrierung
1. **Power-Zeile**: welchen Effekt kann das Fenster mit Power 0,8 sehen; eine
   Programm-Konvention (alpha 0,05 einseitig fuer Mess-Gates, Power 0,8,
   Cluster-Einheit benannt) wird als DEC-51 fixiert, weil R1-R4 drei
   verschiedene Konventionen benutzen (Review 3.10).
2. **Entscheidungsrelevanz-Zeile**: was aendert ein PASS konkret (naechster
   Schritt, Kapitalpfad, Tradability-Folge); enthaelt die oekonomische
   Mindestmagnitude aus der Horizont-Friktions-Kurve als ETIKETT, nicht als
   Gate. Ein Kandidat, dessen bester Fall unter der Wand liegt, ist
   registrierbar, traegt aber das Etikett und verbraucht bewusst einen
   Alpha-Slot (Fall R3-K-31).
3. **Cluster-Einheit-Zeile**: Resampling-Einheit und effektives N; Pooling
   korrelierter Symbole ueber dieselben Kalendertage zaehlt als EIN Cluster
   (Review 2.3/2.5 - drei Kandidaten hatten das falsch).
4. **Selektions-Deflation**: Zahl der Varianten K registriert; Schwelle liegt
   ueber der Bailey/LdP-Decke fuer dieses K.
5. **Drittes, adversariales Fixture** (Peso-Problem) neben Positiv- und
   Null-Fixture.
6. **Kostenmodell-Bindung**: `constants_hash` der verwendeten Kosten-
   konstanten im Ergebnis; ungemessene Konstanten RAISEN statt Default.
7. **Irreversibilitaets-Regel**: vor jeder daten-gated-Sperre eine
   dokumentierte Probe auf oeffentliche Nachladbarkeit (H-26/DVOL-Lehre).
8. **Positivkontroll-Vorschaltung**: bei jeder Maschinerie mit >1 h Laufzeit
   laeuft die Positivkontrolle ZUERST und allein.
9. **Kapital-, Steuer- und Venue-Zeile** bei jeder Praemien-Registrierung:
   Rendite auf gebundenes Kapital (nicht Notional), steuerliche Behandlung
   der Cashfluesse (Funding = laufender Ertrag), Boersen-/ADL-Ereignisrisiko.
   Die Eingangswerte kommen vom Nutzer (siehe 6).
10. **Stress-Episode** wird kanonisch definiert und als Fixture gepinnt
    (Review 6.6): Liste der Stress-Tage aus WP-0-Bar-Cache (Tages-RV ueber
    dem 97,5-Perzentil der juengsten 24 Monate) + der 19.08.2026.

### 2.3 Ein-Fenster-DROP: kontrollierte Entschaerfung, nur unter Auflagen
Beschluss als eigenstaendige DEC-52 VOR jeder Kandidaten-Registrierung, mit
den fuenf Review-Auflagen woertlich: (i) nur wo die Power-Zeile Per-Fenster-
Power < 0,6 ausweist; (ii) je Fenster gleiches Vorzeichen UND >= 0,5x der
registrierten Schwelle; (iii) Signifikanz nur auf dem gepoolten Schaetzer mit
fenster-geclustertem Bootstrap; (iv) gepooltes alpha 0,01; (v) Retro-Check
auf H-06/H-20/H-22 wird veroeffentlicht - kippt er ein Verdikt, heisst die
Regel "Lockerung", nicht "Verbesserung", und die alten Verdikte bleiben.

### 2.4 Weitere Entscheidungen
- **Praemie statt Sharpe** als urteilstragende Groesse fuer Klasse P; Sharpe,
  MaxDD, Tail-Ratio werden BERICHTET (mit hergeleitetem Rauschboden), nie
  geurteilt.
- **Registry-Format**: YAML-Block IM Markdown fuer neue 3.0-Eintraege
  (Schwellen als Herleitungs-Referenz, nicht als nackter Skalar); 2.0-Registry
  wird NICHT migriert.
- **GPU-Default 0**; eine GPU-Hypothese braucht die Entscheidungsrelevanz-
  Zeile mit Tradability-Pfad. Die 24-h-Kappe aus R4 wird NICHT als Schwelle
  uebernommen (unhergeleitet), sondern als Budget-Meldegrenze.
- **Kein Live-Order-Code** bleibt Verfassung des FORSCHUNGSprogramms. Der vom
  Review benannte Widerspruch (6.4: die billigste zu messende Klasse ist die
  teuerste zu betreibende) wird NICHT still entschieden - siehe 6.

## 3. Welle 1 von 3.0: Zensus zuerst, kein Alpha-Slot ohne Feasibility

Reihenfolge ist bindend. Jeder Schritt hat einen binaeren Befund (WP-4-Muster).

| # | Paket | Was es beantwortet | Aufwand | Toetet/oeffnet |
|---|---|---|---|---|
| WP-7 | **Universums-Zensus** (R2-V-0 + R4-WP-8 vereinigt): 1d-Klines fuer alle Bybit-USDT-Perps inkl. delisteter (instruments-info + Survivorship-Roster), K, sigma_xs, **rho_quer** (Restkorrelation nach Querschnitts-Demeaning, woechentlich), Alt-Symbol-Spread aus dem VORHANDENEN `bybit/tickers`-Strom (Inhaltsprobe zuerst, C.8) | Ist die Querschnitts-Klasse ueberhaupt testbar? Welches K, welcher Spread? | 1d-Klines ~10 min; Tickers-Probe Minuten; ~1 Personentag | rho_quer > 0,03 => Klasse W in der 2x12-Monats-Form TOT; sonst offen |
| WP-9 | **DVOL-Backfill** (oeffentliche Deribit-API ab ~2021-04) + Kreuzvalidierung gegen die 112 harvesteten Tage | Sind 5,4 Jahre IV-Historie verfuegbar und konsistent? | Sekunden Download, 1 h Abgleich | Oeffnet H-27-Klasse (neue Registrierung), aendert H-26/C-33-Sperren NICHT |
| WP-10 | **Praemien-Kohaerenz + Maker-Fill-Schattenmessung** (R1-K-07 + R4 6.2a/6.3), N-Floor auf Kalender-Cluster umgestellt, Maker-Vorteil 3,5 bp/Bein korrekt hergeleitet | Wie korrelieren die Praemien-Quellen im Stress? Wie wahrscheinlich ist ein passiver Fill? | Bestand + WP-2/WP-4-Replay, CPU-Stunden | Entscheidet ueber Portfolio-These und ueber jedes Maker-Kostenmodell |
| V-1..V-4 | **Vier 10-Minuten-Vorfragen** (Nutzer-Maschine, oeffentlich): (1) Tiefe von `/v5/market/funding/history` je Symbol; (2) `turnover24h` der datierten Bybit-Futures; (3) Median(Ist-Funding - I) auf den 43 Harvest-Tagen; (4) Delivery-/Settlement-Gebuehr Optionen UND datierte Futures an der Primaerquelle | Vorbedingungen fuer R2-K-02, R1-K-03, R1-K-01 | Minuten | jede kann einen Kandidaten vorab toeten |

## 4. Alpha-Kandidaten, konditional auf Welle 1 (Rangfolge = Entscheidung)

| Rang | Kandidat | Bedingung | Etikett |
|---|---|---|---|
| A1 | **R2-K-02 Querschnitts-Funding-Carry, perp-only** - der Boersen-Zinsanker I (10,95 % p.a.), an dem R1-K-01 stirbt, kuerzt sich im Querschnitt heraus; Cashflow statt Prognose; exakt ausrechenbare Null | WP-7 (rho_quer, K, Spread), V-1, Funding-Intervall-Heterogenitaet 1h/8h behandelt, Orthogonalisierung gegen Momentum urteilstragend | Praemien-Klasse P |
| A2 | **R3-K-31 EXP-CLOCK** - Verfallskalender als deterministischer Ereignistakt ueber 6 Jahre Bar-Cache, N~200, Negativ-Panel aus Realdaten (XRP/BNB) | SE mit N_eff neu (BTC/ETH = ein Cluster je Ereignis); Pflicht-Etikett "bester Fall 12 bps liegt unter der Wand" | Ereignis-Klasse E, Alpha-Slot bewusst sub-Wand |
| A3 | **R2-K-01/K-04/K-05 als Kohorte F-XSEC1** (Momentum / Reversal mit Gap-Design als Primaerfassung / Vol-Anomalie mit Vol-Drag-Null) | NUR wenn WP-7 rho_quer <= 0,03 UND K >= 110; sonst gestrichen, nie auf N=5 zurueckskaliert | Klasse W, zweistufige FDR |
| A4 | **R1-K-03 Perp vs. datierter Future** | V-2 (Liquiditaet) und V-4 (Settlement-Gebuehr) positiv; Schwelle aus Kapitalbindung hergeleitet, nicht "bewusst hoeher gesetzt" | Klasse P |
| A5 | **R1-K-04 Skew-Praemie** und Options-Block | erst nach H-26-Verdikt (E.6-Reihenfolge), Schwelle aus gemessener Skew-Verteilung, nicht aus C-33 | Klasse P, gesperrt |

Nicht registriert (mit Grund im Review): R1-K-01 in der Spot/Perp-Form
(stirbt am eigenen Nulleffekt), R1-K-05/K-06 (Gebuehren-strukturell tot;
Lehre: jede Struktur, deren Nutzen eine Greek-DIFFERENZ ist, ist auf Bybit
benachteiligt), R2-K-03 in Portfolio-Sharpe-Form, R2-K-06 Kalender ausser
Session-Achse (umzubenennen), R3-K-32 GEX (kein Harvester-Auftrag vor einem
K-31-PASS - S4/S5-Falle), R3-K-36-Gate (0,73 SE), R3-K-37 Stufe 2, R3-K-35
vor WP-7/WP-8.

## 5. Team- und Modellpolitik fuer die Umsetzung (Token-Effizienz)
- Orchestrator: Fable 5.1 (immer). Entscheidungen, Registrierungstexte,
  Gate-Urteile, Verfassung.
- Zensus-/Backfill-Bau (WP-7, WP-9, WP-10): Sonnet, mit Spezifikation vom
  Orchestrator und Test-Abnahme (Fixtures DEC-39, Determinismus-Fingerprint).
- Gate-Design und Registrierungs-Herleitungen (Rauschboeden, Power): Opus,
  danach adversarischer Review durch einen zweiten Opus-Agenten; Fable 5.1
  nur bei Widerspruch zwischen beiden.
- Kartierung, Inventur, Dokumentpflege: Sonnet (ggf. Haiku fuer reine
  Listen).
- Kein Agent registriert eine Hypothese; das tut nur der Orchestrator nach
  Review.

## 6. Entscheidungen, die NUR der Nutzer treffen kann (vor dem PRD-Abschluss)
1. **Ausfuehrungsfrage (Review 6.4):** Der beste Kandidat (A1) ist ein
   woechentlicher Dezil-Long-Short ueber 100-300 Perps (~30-60 Orders je
   Woche) - manuell unrealistisch, und "kein Live-Order-Code" ist
   Verfassung. Optionen: (a) Verfassung bleibt, 3.0 bleibt reines
   Messprogramm und A1 wird gemessen, aber nie betrieben; (b) eine spaetere,
   getrennt gegatete "Ausfuehrungs-Spur" wird im PRD als Phase vorgesehen,
   die erst nach PASS + Tradability-PASS + expliziter Nutzer-Freigabe
   gebaut wird; (c) Kandidaten werden auf "manuell betreibbar" (wenige
   Positionen) eingeschraenkt, was die Klasse W praktisch streicht.
   **Default des Orchestrators bis zur Antwort: (b)** - es aendert heute
   keinen Code und keine Regel.
2. **Kapitalbasis und Steuerregime** fuer die Kapital-/Steuer-Zeile (2.2.9):
   Groessenordnung des einsetzbaren Kapitals, steuerliche Behandlung von
   Funding-Ertraegen und Options-Praemien in deiner Jurisdiktion.
3. **Sunset-Review der Recording-Engine F0** (faellig seit ~2026-09-11 laut
   PRD 2.0 §9, nie gelaufen): abschalten, was keine registrierte Hypothese
   namentlich braucht? Der Orchestrator empfiehlt: Review durchfuehren,
   Streams behalten nur bei namentlichem Bedarf.

## 7. Naechste Schritte des Orchestrators (ohne Nutzer-Input moeglich)
1. Umbau (Phase 2) abnehmen und committen.
2. DEC-51 (Power-Konvention) und DEC-52 (Ein-Fenster-Regel mit Retro-Check)
   als Entwuerfe in `scinance3-impl/state/decisions.md` anlegen; DEC-52
   erst nach Retro-Check-Ergebnis beschliessen.
3. PRD 3.0 aus diesem Entwurf ausarbeiten (Opus-Entwurf, adversarischer
   Review, Orchestrator-Fassung), mit den drei Nutzer-Fragen als offen
   markierten Abschnitten.
4. WP-7-Spezifikation schreiben und bauen lassen (Sonnet); die vier
   Vorfragen V-1..V-4 als PowerShell-Einzeiler an den Nutzer.
