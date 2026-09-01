# WP-6 - Options-Quote-Breite im Stress vom 19.08.2026: Befund

> Quelle: Harvest-Baum `raw/bybit/tickers` (WS-Frames, Dialekt bidIv/askIv),
> Fenster 2026-08-15..23, Minuten-Aufloesung (letzter Frame je Symbol/Minute,
> deterministisch). Bein-Band: 7-14 DTE, abs(Delta) 0,15-0,30.
> Rohdaten: `state/wp6_20260826/` (Summary + 10.367 Minuten-Zeilen).
> Erzeugt von `scripts/wp6_optstress_census.py` nach bestandener Feld-Probe.

## 0. Das Ereignis

Der 19.08. war ein echter Stresstest, der groesste im bisherigen
Beobachtungsfenster: BTC 64.470 -> 70.319 (+9 %), ETH 1.912 -> 2.311
(+21 %); ATM-Mark-IV BTC 25,5 -> 41,9 Vol-Punkte, ETH 36,0 -> 62,0. Zwei
Schub-Phasen: ~15:27-15:45 UTC (erster Beinbruch nach oben) und
~20:50-21:30 UTC (zweiter Schub, ETH-Spitze).

## 1. Kernbefund: die Enge haelt fast durchgehend - und bricht genau an den Schock-Minuten

Stundenmediane der Bein-Breite am Stress-Tag: **BTC 0,16-0,17 Vol-Punkte in
23 von 24 Stunden** - identisch mit den Ruhe-Tagen (0,145-0,16). Nur die
Crash-Stunde 15:00 zeigt 0,30. ETH: 0,10-0,20 fast durchgehend; 15:00 =
0,40, 21:00 = 0,53.

Die Verbreiterung ist **episodisch, kurz und punktgenau an den Schocks**:

| | breite Minuten (>0,5 Pkt) | Episoden | laengste | Spitzenwerte |
|---|---:|---:|---:|---|
| BTC | 34 / 5.178 (**0,66 %**) | 10 | 8 min | 9,53 (19.08. 15:29) |
| ETH | 146 / 5.180 (**2,82 %**) | 28 | 75 min (18.08. Vorlaeufer) | 53,8 (19.08. 21:07) |

Renormalisierung ist schnell: BTC ist um 16:00 wieder bei 0,16; ETH faellt
mitten in der 21:00-Episode zwischenzeitlich auf 0,33 (21:17) zurueck und
ist um 23:00 wieder bei 0,10. Das Buch kehrt binnen Minuten bis maximal
~1-2 Stunden zur Ein-Tick-artigen Enge zurueck.

## 2. Ehrlichkeits-Grenzen dieser Zahlen

1. **Die Spitze (53,8) ist eine Ein-Symbol-Minute.** Waehrend des ETH-Schubs
   duennt das Bein-Band auf n_legs=1 aus (21:06-21:10) - teils weil Quotes
   verschwinden, teils weil ein 21-%-Move die Deltas aus dem Band schiebt.
   Die Zahl ist eine reale Quote, aber keine Aussage ueber die ganze Kette.
2. **ETH-Bein-Band ist generell duenn** (Median n_legs=2 je Minute). Die
   Minuten-Mediane sind entsprechend rauschig; die Episoden-Struktur (wann,
   wie lange) ist robuster als die exakte Breite.
3. **Abdeckungsluecken im Fenster:** 15.08. nur ab ~16:50; einzelne Stunden
   mit 20-27 von 60 Minuten (u. a. 14:00 am Stress-Tag, direkt VOR dem
   ersten Schub). 5 Beobachtungstage sind eine Stichprobe, kein Klima.
4. Minuten-Aufloesung, letzter Frame je Minute: Intra-Minuten-Spitzen
   koennen schaerfer gewesen sein.

## 3. Was das fuer die beiden Strategie-Seiten heisst

**Fuer die DEC-45-Form (VRP-Verkauf: passiver Einstieg an ruhigen Tagen,
Halten bis Verfall):** Der Befund traegt sie. 97-99 % der Minuten sind eng;
der Einstieg findet per Definition nicht in den Schock-Minuten statt, und
Halten bis Verfall muss im Stress nichts ueber den Spread schliessen. Das
Stress-Risiko dieser Form ist die Mark-to-Market-P&L, nicht die Quote.

**Fuer die Long-Vol-Idee („wenn wir Bewegung vorhersagen, kaufen wir
Strangles"):** Der Befund QUANTIFIZIERT die Eintritts-Steuer, und sie ist
brutal. Wer auf das Bewegungssignal hin kauft, kauft in genau den Minuten,
in denen (a) die IV bereits 6-20 Punkte gesprungen ist und (b) der Spread
das 10- bis 100-fache des Normalzustands betraegt (BTC 15:29: halber Spread
x 2 Beine ~ 9,5 Vol-Punkte = das Dreifache der C-33-Kante). Ein
Long-Vol-Einstieg muesste VOR dem Schub liegen - das ist die bekannte,
harte Anforderung an die Prognose, jetzt mit gemessenem Preisschild.

## 4. Operativer Nebenbefund mit Frist: die Options-Aufzeichnung ist am 20.08. ausgefallen

| Tag | Status |
|---|---|
| 15.-19.08. | OK (Optionen vorhanden) |
| **20.08.** | **Dateien vorhanden, aber NULL Options-Frames** |
| **21.-23.08.** | **keine lesbaren tickers-Dateien im Baum** |

Der Options-Strom ist unmittelbar nach dem Stress-Tag verstummt - moeglich
als Spaetfolge des Stresses selbst oder des grossen Verfalls-/Symbol-Churns
um den 20AUG26-Termin. **Niemand hat es bemerkt, weil der Live-Pfad keine
Manifest-Zeilen schreibt** - exakt die Luecke aus DEC-46, jetzt mit einem
realen Schadensfall belegt: vier Tage Options-Historie fehlen, darunter die
Beruhigungsphase nach dem Stress. Der REST-Sampler (ab 24.08.) faengt die
Gegenwart auf; die Luecke 20.-23.08. ist endgueltig.

An das Harvest-Projekt: (1) Options-Sammlung wieder hochziehen bzw.
pruefen, ob sie laeuft und nur der lokale Baum veraltet ist; (2) der
Manifest-Registrar aus dem Auftrag haette diesen Ausfall am 20.08. als
Nicht-DONE sichtbar gemacht - der Schadensfall ist das Argument.

## 5. Bleibender Ertrag

Modul + Runner + 12 Tests (Wrapper- und Dialekt-tolerant, Probe-Pflicht,
DEC-39-Fixturepaar Ruhe/Stress Ende-zu-Ende). Jedes kuenftige Fenster ist
mit einem Befehl nachmessbar; die Minuten-CSV (10.367 Zeilen) liegt im
State fuer Folgeanalysen (z. B. Breite-vs-IV-Sprung-Regression, sobald
mehr Stress-Episoden vorliegen).


---

## NACHTRAG 2026-09-01: erweitertes Fenster 15.-28.08. (`state/wp6_ext_20260828/`)

Nach der Archiv-Kompaktierung im Harvest-Projekt wurde der Zensus ueber
2026-08-15..28 wiederholt. Vier Ergebnisse:

**1. Abschnitt 4 dieses Befunds ist zu KORRIGIEREN: der 20.-21.08. war KEIN
Recorder-Ausfall,** sondern Archiv-Verzug (der lokale Baum erhaelt Tage erst
~2 Tage spaeter, kompaktiert). Beide Tage sind vollstaendig vorhanden und
normal (20.08.: p50 0,16/0,12 — am Tag nach dem Stress).

**2. Aber es gab einen ECHTEN Ausfall, und zwar nur ETH:** ETH-Options-Frames
enden am **22.08. 08:00 UTC** und kehren am **27.08. 08:00 UTC** zurueck —
exakt 5 Tage, auf die Stunde rund, waehrend BTC durchgehend laeuft. Der
REST-Sampler (WP-5) belegt fuer den 24.-26.08. eine voll quotierte
ETH-Kette an der Boerse: der Ausfall lag im Harvester (ETH-Subscription),
nicht bei Bybit. Die runde 08:00-Grenze deutet auf einen taeglichen
Refresh-/Restart-Job. **Wieder unbemerkt, wieder mangels Manifest** — der
zweite Schadensfall fuer den DEC-46-Registrar binnen einer Woche.

**3. Die Beruhigungsphase bestaetigt den Kernbefund in verschaerfter Form:**
Am 20.-21.08. lag die ATM-IV noch bei 38-59 Vol-Punkten (gegen 26-41 vor dem
Stress) — die Bein-Breite war trotzdem wieder normal (p50 0,14-0,16 BTC,
0,12-0,15 ETH). **Die Enge haengt nicht am IV-NIVEAU, sondern nur am
SCHOCK-UEBERGANG.** Fuer die DEC-45-Form heisst das: auch der Einstieg in
einem erhoehten, aber ruhigen Vol-Regime zahlt den Normal-Spread.

**4. Verfalls-Rollover funktioniert wie erhofft:** Am 21.08. und 28.08.
liegen zwei Termine gleichzeitig im 7-14-DTE-Band (horizon_med 118-138
statt 62-76, n_legs 10 statt 4-6). Das Band laeuft ohne Definitionsluecke
ueber die Woechentlichen hinweg; die p95-Werte dieser Tage (0,45/0,76-1,08)
spiegeln die frisch aufgesetzten, noch duenn quotierten neuen Serien und
sind KEIN Stress-Signal.
