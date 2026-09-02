# Retro-Check: neue kontrollierte Fenster-Regel gegen H-06 / H-20 / H-22

Status: NUR Sensitivitaets-Check. Bestehende Verdikte (GL-008 DROP, GL-026 DROP,
GL-027 DROP) werden NICHT geaendert. Keine Datei im Repo wurde modifiziert.

Gepruefte neue Regel (wie in der Aufgabe spezifiziert):
- Schritt 1 (Screen, je Fenster): (a) Vorzeichen des Punktschaetzers stimmt mit der
  Hypothese ueberein UND (b) |Punktschaetzer| >= 0,5x der registrierten Schwelle.
  Verfehlt EIN Fenster diesen Screen -> weiterhin DROP (die Regel ersetzt nur die
  Haerte der Schwelle, nicht das Ein-Fenster-Prinzip selbst).
- Schritt 2 (Signifikanz, NUR wenn Schritt 1 in ALLEN Fenstern besteht): gepoolter
  Schaetzer, fenstergeclusterter Bootstrap, alpha = 0,01 (statt bisher alpha = 0,05
  je Fenster einzeln).

Quellen: `state/gate_log.md` (GL-008, GL-026, GL-027), `state/hypothesis_registry.md`
(H-06, H-20, H-22 Eintraege), sowie die Rohlauf-JSONs:
- `handoff_local/results/wave2_20260617_090618/h06/c07_pe_results.json`
- `state/h20_20260817/c20_tail_results.json`
- `state/h22_20260818/c22_l2tilt_results.json`
- `state/wp2_20260817/l2tilt_extract.json` (WP-2-Vorleistung fuer H-22)

---

## H-06 · C-07 Permutation Entropy (GL-008)

H-06 hat ZWEI registrierte Schwellen mit eigenem Punktschaetzer (kein einzelner
gepoolter Fenster-Wert wie bei H-20/H-22). Beide werden separat gegen die neue
Regel gepruft; je Fenster wird der GUENSTIGSTE Fall (bester Wert ueber alle
5 Symbole bzw. alle Symbol x Delta-Zellen) verwendet, um der neuen Regel die
bestmoegliche Chance zu geben.

### 1a) PRE-Gate (rho, Schwelle 0,30; Vorzeichen positiv erwartet)

| Fenster | Schwelle | Punktschaetzer (bestes Symbol) | Vorzeichen ok? | >= 0,5x Schwelle (0,15)? | Fenster-p |
|---|---:|---:|:---:|:---:|---|
| w0 | 0,30 | +0,0111 (ETHUSDT) | ja | **nein** (7,4 % von 0,15) | n/a (Korrelations-Floor, kein Signifikanztest) |
| w1 | 0,30 | +0,0145 (BNBUSDT) | ja | **nein** (9,7 % von 0,15) | n/a |

Alle 10 Symbol-Fenster-Zellen liegen zwischen -0,0059 und +0,0145 (siehe GL-008);
selbst der guenstigste Fall je Fenster erreicht keine 10 % der halben Schwelle.

### 1b) Haupt-Gate AUC-Lift (Schwelle +0,03; Vorzeichen positiv erwartet)

| Fenster | Schwelle | Punktschaetzer (beste Zelle) | Vorzeichen ok? | >= 0,5x Schwelle (0,015)? | Fenster-p (Surrogate, dieser Zelle) |
|---|---:|---:|:---:|:---:|---|
| w0 | 0,03 | +0,0030 (XRPUSDT, d15min) | ja | **nein** (20 % von 0,015) | 0,2736 |
| w1 | 0,03 | +0,0093 (SOLUSDT, d15min) | ja | **nein** (62 % von 0,015) | 0,3731 |

Nachrichtlich (naehester Fall insgesamt, nicht die beste AUC-Lift-Zelle): XRP w1
d15min/d60min hat den einzigen FDR-signifikanten Surrogate-p (0,0050) im ganzen
Lauf, aber AUC-Lift dort ist nur +0,0072 (48 % der halben Schwelle) — signifikant,
aber immer noch unter dem gelockerten Betrags-Screen.

**Gepoolter Schaetzer/p ableitbar?** NEIN. Es sind weder die 200 Surrogat-MI-Werte
je Zelle (nur `surrogate_mi_mean`, keine volle Verteilung) noch eine ueber Fenster
gepoolte Bootstrap-Struktur gespeichert; das Originaldesign ist ohnehin ein
FDR-Familientest ueber 40 Zellen, kein Zwei-Fenster-Pooling. **Proxy (klar als
Obergrenze der Evidenz markiert):** Stouffer-Kombination der zwei guenstigsten
Fenster-p (0,2736; 0,3731, gleich gewichtet) -> p_proxy = 0,26; Fisher-Kombination
(chi2=4,56, df=4) -> p_proxy = 0,34. Beide weit ueber alpha=0,01.

**Verdikt unter neuer Regel:** Schritt-1-Screen scheitert in BEIDEN Fenstern und
bei BEIDEN Metriken deutlich (schlechtester Fall 7 %, bester Fall 62 % der
0,5x-Schwelle — keiner erreicht 100 %). -> **DROP.** Kein Unterschied zum
registrierten Verdikt (GL-008 DROP).

---

## H-20 · C-20 TAIL-AFTERMATH (GL-026)

Schwelle: gepoolter mean(y) >= +10 bps je Fenster, Vorzeichen positiv (Reversion)
erwartet. Gespeicherte Werte direkt aus `c20_tail_results.json` (Feld `cells`),
keine Rekonstruktion noetig fuer den Punktschaetzer/p — beide sind bereits die
gepoolten (5-Symbol) Fenster-Groessen.

| Fenster | Schwelle | Punktschaetzer mean(y) | Vorzeichen ok? | >= 0,5x Schwelle (+5 bp)? | Fenster-p (cluster-boot) |
|---|---:|---:|:---:|:---:|---:|
| OOS-1 | +10 bp | **+4,83 bp** | ja | **nein** (96,6 % von 5 bp — verfehlt um 0,17 bp) | 0,3976 |
| OOS-2 | +10 bp | **+17,28 bp** | ja | ja (173 % von 5 bp) | 0,1728 |

OOS-1 ist der einzige knappe Fall im gesamten Retro-Check: 4,83 bp liegt nur
0,17 bp (3,4 %) unter der gelockerten 5-bp-Schwelle. Trotzdem: Regel ist "je
Fenster (a) UND (b)", und OOS-1 verfehlt (b) — wenn auch knapp.

**Gepoolter Schaetzer/p ableitbar?** NEIN. Die JSON enthaelt nur die aggregierten
Fenster-Kennzahlen (`mean_aftermath_bp`, `cluster_boot_p`) und die 5
Symbol-Mittelwerte je Fenster (`per_symbol_report`), aber weder die
event-/tagesweise Rohserie noch die 1000 Bootstrap-Replikate — ein echter
fenstergeclusterter Pooled-Bootstrap ueber beide OOS-Fenster laesst sich aus dem
gespeicherten Artefakt nicht neu rechnen. **Deskriptiver Pooled-Punktschaetzer**
(events-gewichtet, nur als Illustration, KEIN Signifikanztest): (4,83x1044 +
17,28x962)/(1044+962) = **+10,80 bp** — ueber der vollen 10-bp-Schwelle, aber das
ist nur der Mittelwert, keine Aussage ueber Signifikanz. **Proxy-p (Obergrenze,
klar markiert):** Stouffer-Kombination der beiden Fenster-p (0,3976; 0,1728,
gleich gewichtet) -> p_proxy = 0,198 (n-gewichtet: 0,200); Fisher (chi2=5,36,
df=4) -> p_proxy = 0,253. Beide weit ueber alpha=0,01 — selbst die guenstigste
Obergrenze reicht nicht annaehernd an Signifikanz heran.

**Verdikt unter neuer Regel:** Schritt-1-Screen scheitert in OOS-1 (knapp,
3,4 % unter der Schwelle) -> **DROP**, unabhaengig vom (ohnehin weit
unsignifikanten) Pooled-Proxy. Kein Unterschied zum registrierten Verdikt
(GL-026 DROP). Einzige Anmerkung: dies ist der Fall im Retro-Check, der der
neuen, gelockerten Schwelle am naechsten kommt — bei einer Wiederholung des
Laufs mit geringfuegig anderem Sample koennte der Screen kippen; die
Pooled-Signifikanz (alpha=0,01) wuerde ihn aber selbst dann mit hoher
Wahrscheinlichkeit nicht tragen (Proxy-p ~0,2, nicht ~0,01).

---

## H-22 · C-22 L2-TILT (GL-027)

Schwelle: BTC IC >= 0,10 in BEIDEN Fenstern, Vorzeichen positiv erwartet
(judgment-bearing NUR BTC; ETH-Fenster ist Bericht, nicht urteilstragend und
bleibt hier ausser Betracht, wie im registrierten Gate).

| Fenster | Schwelle | Punktschaetzer IC | Vorzeichen ok? | >= 0,5x Schwelle (0,05)? | Fenster-p (Bootstrap) |
|---|---:|---:|:---:|:---:|---:|
| BTC W-L2-1 | 0,10 | **+0,0665** | ja | ja (133 % von 0,05) | 0,0969 |
| BTC W-L2-2 | 0,10 | **-0,0112** | **nein** (Vorzeichen negativ, Hypothese positiv) | nein | 0,5704 |

W-L2-2 scheitert bereits an Kriterium (a) — das Vorzeichen kippt komplett
(IC von +0,067 auf -0,011), nicht nur die Betragsschwelle. Das ist kein knapper
Fall wie bei H-20.

**Gepoolter Schaetzer/p ableitbar?** NEIN. `c22_l2tilt_results.json` speichert
nur `ic`, `boot_p`, `n_pairs`/`n_tilt_days` je Fenster; die WP-2-Vorleistung
(`state/wp2_20260817/l2tilt_extract.json`) speichert zusaetzlich nur SHA-256-
Fingerabdruecke der taeglichen Tilt-/Return-Werte (Bit-Bindung), NICHT die
Werte selbst — die Rohserie (Tages-Tilt, Folgetags-Rendite) ist damit aus den
gespeicherten Artefakten nicht rekonstruierbar, ein echter fenstergeclusterter
Pooled-Bootstrap ueber beide BTC-Fenster ist nicht nachrechenbar. **Proxy-p
(Obergrenze, klar markiert):** Stouffer-Kombination der beiden Fenster-p
(0,0969; 0,5704, gleich gewichtet) -> p_proxy = 0,214 (n-gewichtet: 0,209);
Fisher (chi2=5,79, df=4) -> p_proxy = 0,215. Weit ueber alpha=0,01.

**Verdikt unter neuer Regel:** Schritt-1-Screen scheitert in W-L2-2 durch
Vorzeichenwechsel (Kriterium a) -> **DROP.** Kein Unterschied zum registrierten
Verdikt (GL-027 DROP). Die vorab registrierte A-priori-Erwartung "DROP erwartet"
bleibt auch unter der neuen Regel bestaetigt.

---

## Gesamtfazit

Keine der drei Hypothesen kippt unter der vorgeschlagenen Regel: H-06 verfehlt
den gelockerten Betrags-Screen in beiden Fenstern und bei beiden Metriken
deutlich (7-62 % der 0,5x-Schwelle), H-22 scheitert an einem echten
Vorzeichenwechsel zwischen den BTC-Fenstern (nicht nur an der Betragsschwelle),
und H-20 scheitert knapp (3,4 % unter der 0,5x-Schwelle) in genau einem Fenster
— aber selbst wenn dieser eine Grenzfall zugunsten des Screens gekippt waere,
haette die gepoolte Signifikanzpruefung bei alpha=0,01 nicht getragen: alle drei
Proxy-Obergrenzen (Stouffer/Fisher, da echte gepoolte Bootstraps aus den
gespeicherten Artefakten mangels Rohdaten/Replikaten nicht rekonstruierbar sind)
liegen bei p ~ 0,20-0,34, also 20-30x ueber der neuen Schwelle. Fuer diese drei
Faelle ist die neue Regel also strukturell eine Lockerung des Ein-Fenster-Filters
(schwaecherer Betrags-Screen je Fenster statt volle Schwelle), die aber durch
die gleichzeitig verschaerfte Pooled-Signifikanzschwelle (alpha=0,01 statt 0,05)
kompensiert wird und in KEINEM der drei bereits adjudizierten Faelle zu einem
anderen Endverdikt fuehrt. Da keine Verschiebung eintritt, ist die "Lockerung"-
Kennzeichnung hier nicht ausgeloest — sie waere nur bei einem tatsaechlichen
PASS-Flip erforderlich gewesen.
