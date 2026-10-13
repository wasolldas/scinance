# Review A1 (H-31): adversarische Pruefung der Herleitung (Stufe 1 + bedingte Stufe 2)

> Zweiter Gutachter, 2026-10-13. Gegenstand: `FEASIBILITY.md`, `feasibility.json` (sha256 `b4680f7c...ca72d9e`),
> `ENTSCHEIDUNGSVORLAGEN.md`, `ERSTFASSUNG_H31_entwurf.md`, Skripte `scratchpad/a1_herleitung/`.
> Eigene Nachrechnung: `scratchpad/a1_review/` (`rv_load.py`, `rv_formation.py`, `rv_nuisance.py`, `rv_power.py`,
> `rv_wp7_zerofill.py`; Ausgaben `rv_formation.json`, `rv_nuisance.json`). Keine A1-Outcome-Groesse ab 2024-07-01
> berechnet oder angesehen; Nuisance-Code gibt kein Rendite-Mittel aus (Waechter: Haltewoche endet <= 2024-06-30);
> keine Tagesdaten nach 2026-06-28; keine Siegeldatei geoeffnet (`weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`
> in `runs/wp7_*` nicht beruehrt, nur `wp7_report.json` gelesen); nichts committet.

---

## Urteil: VETO gegen den Befund "Stopp-Regel greift nicht / A1 knapp testbar" - ZUSTIMMUNG zur Rechenarbeit

Die Zahlen der Herleitung sind korrekt (alle entscheidenden Werte unabhaengig reproduziert, Abschnitt R). Falsch ist
die Feststellung, auf der Stufe 2 beruht: Die Herleitung hat eine eigene, nicht beschlossene Autokorrelationsregel
(`c = max(1, gemessen)`) als "bindend" gesetzt und damit die Stopp-Regel des Auftrags verneint. Unter den geltenden
Beschluessen (DEC-67 E4, fuer A1 ausdruecklich bestaetigt in DEC-70 E1) greift die Stopp-Regel: GL-012 bei theta = 1
(`3,168 * SE_gepoolt = 176,5 bp > prem 147,6 bp`). Unabhaengig davon ist theta UNBELEGT (keine Quelle gefunden).

**Ersatz-Feststellung (Vorschlag an den Orchestrator):** "A1 (H-31) ist in der Konstruktion DEC-70 unter den geltenden
Beschluessen vor der Registrierung GL-012 (DEC-67 E4 / DEC-70 E1: 176,5 > 147,6 bp schon bei theta = 1); unabhaengig
davon ist prem_prior UNBELEGT (theta). Kein Verdikt ueber den Funding-Carry. Stufe 2 bleibt Akte ohne Rechtswirkung."

---

## Befunde

### B-1 (BLOCKIEREND) Stopp-Regel mit nicht beschlossener SE-Regel ausgewertet; DEC-67 E4 ist fuer A1 bindend

- Beleg Herleitung: `FEASIBILITY.md` Z. 19 ff., Z. 262 ("bindend `c = max(1, gemessen)`"), Z. 358 ("Die Stopp-Regel
  greift nicht"); `a1_power.py` Z. 103-105 (DEC-67 nur als Variante).
- Beleg Bindung: `decisions.md` Z. 181 (DEC-67 E4: "DEC-51-Power fuer Funding-basierte Hypothesen rechnet mit W_eff =
  0,41 W"), Z. 206 (DEC-70 E1, A1-spezifisch, vor jeder A1-Feasibility-Zahl: "Der Schluessel ... und W_eff = 0,41 W
  bleiben"). **EV-2 zitiert DEC-67 E4, aber nicht DEC-70 E1** - die A1-spezifische Bestaetigung fehlt in der Vorlage.
  Der Auftrag nennt fuer die SE ausdruecklich "W_eff"; der einzige im Programm definierte W_eff ist 0,41 W.
- Nachgerechnet (`rv_power.py`): c = 1/0,41 -> SE 80,8 / 76,8 bp, `3,168 * 55,7 = 176,5 > 147,6` -> GL-012,
  theta_min 1,196. Damit ist A1 bei jedem theta <= 1 GL-012; nach Auftrag waere hier aufzuhoeren gewesen.

**Antwort auf Frage (a).**
1. *Bindend:* ja. DEC-67 E4 und DEC-70 E1 sind nicht widerrufen. Die DEC-92-Lehre ("Power mit genau der SE-Regel des
   registrierten Tests", `decisions.md` Z. 478) steht dazu in Spannung, hebt die Konstante aber nicht auf. Bei zwei
   kollidierenden bindenden Texten hat das Programm zuletzt die strengste Lesart gewaehlt (DEC-92 E2, Z. 475,
   "Audit Lesart B").
2. *Methodisch passt sie nicht:* (i) 0,41 ist die AR(1)-Naeherung `(1-0,42)/(1+0,42)` aus der Autokorrelation der
   Wochen-Funding-SUMME je Symbol (`WELLE1_BEFUND_TEIL4` Z. 31), also aus der Persistenz des Praediktors, nicht der
   Teststatistik. (ii) Die Teststatistik x (D1 minus Universum) hat auf der Nuisance-Basis rho_1 = -0,250
   (Bootstrap-SD 0,103), c gemessen 0,60..0,77 (Bartlett 0,717, MBB 0,765, stationaerer Bootstrap Block 4 0,713);
   nur das Funding-Bein (4 % der Varianz) hat rho_1 0,52. (iii) PRD 5.1 schreibt die Autokorrelationskorrektur ueber den
   stationaeren Bootstrap der Wochenserie vor (`PRD_SCINANCE3.md` Z. 487); ein Test mit dieser SE hat keinen Faktor
   2,44. (iv) Zusatz: der WP-7-Schaetzer, aus dem 0,42 stammt, fuellt Wochen ohne Funding mit 0 auf
   (`panel_load.py` Z. 507, `np.nansum`); auf dem Union-Panel 0,478 woertlich gegen 0,412 ohne Auffuellung
   (`rv_wp7_zerofill.py`) - die Konstante ist auch als Persistenzmass nach oben verzerrt.
3. *Torpfosten:* Ein Abweichen JETZT waere nach dem Massstab des Programms eine Torpfosten-Verschiebung: die Regel
   wuerde nach Kenntnis ihrer A1-Konsequenz (GL-012 <-> testbar), in Richtung des Kandidaten und fuer genau den
   Kandidaten gewechselt, der sie braucht (Sequenz-Zwang DEC-52, `decisions.md` Z. 32; Praezedenz DEC-92 E2: eine
   nachtraegliche Rettungsregel wurde fuer A3 abgelehnt). Mildernd, aber nicht heilend: anders als in DEC-92 E2 aendert
   c nur Power-Zeile und Regime-Zuordnung, nicht das alpha des spaeteren Gates. Zulaessig waere hoechstens eine
   programmweite DEC ("Power-Zeilen rechnen mit der Autokorrelation der Teststatistik aus der Vorperiode, c >= 1;
   DEC-67 E4 nur fuer Statistiken mit Schluessel-Persistenz") mit Pflicht-Etikett "beschlossen nach Kenntnis der
   A1-Feasibility, A1 beguenstigt". Fuer A1 haette sie heute keine Wirkung, weil theta die Registrierung ohnehin
   blockiert (B-2). Empfehlung: EV-2 fuer A1 nicht entscheiden; GL-012 nach geltender Regel feststellen.

### B-2 (BLOCKIEREND) theta UNBELEGT - Zustimmung zur Herleitung, Antwort auf Frage (b)

- Repo: keine Quelle. R2-K-02 selbst: Querschnitts-Funding-Sortierung perp-only "in der Literatur nicht gefunden"
  (`research/R2_TAGES_WOCHEN_HORIZONT.md` Z. 379-381); die Erosions-Zitate sind UNBELEGT (PRD 5.1); Schmeling/Schrimpf/
  Todorov "Crypto Carry" [sek] betrifft den Zeitreihen-Carry Future gegen Spot (`research/R1_RISIKOPRAEMIEN.md` Z. 141).
- Begrenzte Literaturpruefung (bewusst eng, um keine Ergebnisse aus W1/W2 zu sehen):
  - Christin/Routledge/Soska/Zetlin-Jones, "The Crypto Carry Trade" (Working Paper v1.0, 2022) [sek, nur Abstract
    gesehen]: Short-Perp gegen Long-Spot ist in-sample sehr profitabel (Sharpe 7-10). Das sagt, dass Funding in der
    Zeitreihe nicht durch die Perp-Spot-Basis kompensiert wird - nichts ueber die relative SPOT-Drift von
    Niedrig-Funding-Symbolen gegen das Universum. Nicht auf theta uebertragbar.
  - He/Manela/Ross/von Wachter, "Fundamentals of Perpetual Futures" (arXiv 2212.06888) [sek]: Mechanik, keine
    Querschnittszahl.
  - Koijen/Moskowitz/Pedersen/Vrugt, "Carry", JFE 127(2) 2018 [sek, nur bibliographisch bestaetigt]: Carry ueber
    Anlageklassen; Koeffizienten nicht eingesehen, keine Krypto-Perps -> keine verwertbare Zahl.
  - Kein Papier mit Querschnitts-Funding-Sortierung auf Perps gefunden.
- Strukturell: Eine Quelle, deren Stichprobe 2024-07..2026-06 abdeckt, waere Outcome-Information der Urteilsfenster
  und unzulaessig; intern ist theta nur ueber das Rendite-Mittel bestimmbar (Regel 1 sperrt). **theta >= 0,77 ist
  nirgends belegbar; prem_prior bleibt UNBELEGT und blockiert.** Nebenbei: "theta = 1 = Obergrenze" ist eine
  Modellkappe, keine Schranke (theta > 1 waere bei Carry-Anomalien moeglich); am Befund aendert das nichts.

### H-1 (HOCH) Gabelungsmuster: jede Vorlage loest zugunsten der Testbarkeit auf

- EV-1 (A statt B), EV-2 (c = 1 statt 0,41 W), EV-3 (PRD woertlich statt DEC-51 (2) je Fenster), EV-4 (kritischer Wert
  1,6449 statt PRD-Schwellentext 2,4865), EV-5 (WP-7-Variante statt Buehlmann-Straub), EV-7 (K = 1 statt PRD K = 3):
  alle sechs Empfehlungen fallen in Richtung "A1 testbar". Jede einzeln ist begruendet; zusammen ist "knapp testbar"
  nur der Pfad, auf dem jede Gabel guenstig faellt. Strenge Lesart von EV-1, EV-2 oder EV-3 (A3-Praezedenz DEC-87 (F) /
  GL-032) allein -> GL-012; EV-5 (b) -> Kill.
- Asymmetrie im Argument: EV-1 "vor den Zahlen fixiert -> beibehalten" (`ENTSCHEIDUNGSVORLAGEN.md` Z. 55); EV-2 wuerde
  das ebenfalls vor den Zahlen fixierte DEC-70 E1 ersetzen. Dasselbe Prinzip, gleichmaessig angewandt, ergibt GL-012.

### H-2 (HOCH) Frage (c): Schluessel-Autokorrelation W2 0,303 an der Kill-Grenze 0,30

- Nachgerechnet (`rv_formation.py`, formationsseitig): W2 0,3029 (min 12 Wochen, Mitgliedspaare) bestaetigt; min 8:
  0,2997; Mitgliedschaft "lebend und Funding-Tag": 0,2995; rohe Funding-Summe 0,304; WP-7-artig ohne Auffuellung,
  alle Symbole mit Funding: 0,312; WP-7-Funktion woertlich auf den W2-Tagen: 0,361 (durch Null-Auffuellung erhoeht).
  W1 0,39..0,42 unkritisch. Konfiguration B W2 0,307..0,316.
- Die Bezeichnung "WP-7-Schaetzer" in `FEASIBILITY.md` 2 (b) ist ungenau: WP-7 (`panel_load.funding_autocorrelation`)
  fuellt Wochen ohne Funding mit 0 auf und nimmt alle Symbole; die Herleitung beschraenkt auf Universumswochen.
- Lesart: Kill (4) verweist auf "die in WP-7 gemessene" Autokorrelation (`PRD_SCINANCE3.md` Z. 523) = 0,421
  (2026-09-14) / 0,433 (Union 2026-09-21) -> woertlich nicht ausgeloest. Die Fensterbestaetigung ist eine
  Auftragsergaenzung ohne vorab fixierten Schaetzer; ihr W2-Wert ist schaetzerabhaengig (0,2995..0,361). Eine
  Schaetzerwahl jetzt waere selbst eine Gabel. Empfehlung: Kill (4) formal nicht ausgeloest, Pflicht-Etikett
  "W2 an der Kill-Grenze, schaetzerabhaengig 0,30..0,36".
- Inhaltlich wichtiger als der Kill: prem_W2 (2/3 des gepoolten prem) ruht auf phi = 0,573 aus 2022-2024, waehrend die
  Schluessel-Persistenz in W2 von 0,54 auf 0,30 faellt. GL-012-frei bei theta = 1, c = 1 erfordert phi_W2 >= 0,369
  (64 % des Nuisance-phi, `rv_power.py`); mit Autokorrelations-Skalierung 0,321 -> GL-012 (so auch die Herleitung,
  Abschnitt 7). Dieselbe Groesse, die an der Kill-Grenze liegt, entscheidet also die Testbarkeit.

### M-1 (MITTEL) W2-SD: Funding-Bein nicht mit dem W2-Spread skaliert; c = 1 dort keine Reserve

- Die SD-Projektionen P1-P4 (`FEASIBILITY.md` 4) skalieren nur das Preisbein. Der W2-Formationsspread ist 2,34-mal
  (Mittel) bzw. 1,60-mal (SD) so gross wie auf der Nuisance-Basis. Mit Bartlett-Langfristkomponenten aus der Nuisance
  (`rv_nuisance.json` `lrv_bp2`) ergibt sich fuer W2: SD 369 / 394 bp, c_W2 0,84 / 1,00 (statt 0,72),
  SE_W2 51,2 / 54,7 bp (statt 49,2), theta_min 0,78 / 0,81 (statt 0,766). Kippt bei theta = 1 nicht, verschiebt aber
  die Untergrenze. `c = max(1, gemessen)` ist in W2 gerade ausreichend, keine Sicherheitsmarge.
- Positivkontrolle (EV-12, Regel 1: SD in +-10 %) faengt das nur oberhalb von +10 % (Skalierung mit dem Mittel: +11 %).

### M-2 (MITTEL) SE-Regel: PRD verlangt den stationaeren Bootstrap

- EV-10 nutzt `max(SD/sqrt(W), SE_MBB)`; PRD 5.1 Z. 487 nennt den stationaeren Bootstrap (Politis/Romano). Gemessen:
  stationaer Block 4 c = 0,713, Block 8 0,597 (MBB 0,765). Abweichung als Etikett fuehren; die max(1, .)-Regel ist
  eine strengere Zusatzregel, die einer DEC bedarf.

### N-1 (NIEDRIG) Ergebnisblindheit: kein Verstoss gefunden, eine Grauzone, eine Etikett-Unschaerfe

- Code gelesen (`a1_common`, `a1_model`, `a1_window_census`, `a1_nuisance`, `a1_formation_sensitivity`,
  `a1_psi_by_class`, `a1_kill4_ci`, `a1_check_factor`, `a1_selfcheck`, `a1_bookkeeping`, `a1_explore*`, `a1_power`):
  keine Haltewochen-Groesse eines sortierten Satzes ab 2024-07-01; Nuisance-Waechter wirkt; Tagesdaten ab 2026-06-29
  verworfen; W1/W2 nur Schluessel, D1, K, PIT-Betas aus Vergangenheitsrenditen, Markt-Faktor-SD.
- Grauzone: psi (`a1_formation_sensitivity.py` Z. 5-11) sortiert auf W1/W2 nach Mo-Mi-Funding und misst das
  Do-So-Funding derselben D1 - ein Halbwochen-Analogon des Funding-Beins auf den Urteilsfenstern. Woertlich zulaessig
  (keine Woche nach der Formation), keine Preisinformation, theta unberuehrt; Etikett "Funding-Bein-Analog auf W1/W2
  gesehen" empfohlen.
- Etikett-Unschaerfe: phi 0,5729 und der Nuisance-Formationsspread 145,3 bp sind beide veroeffentlicht; ihr Produkt
  (~83 bp/Woche) ist das Mittel des Nuisance-Funding-Beins, entgegen dem Wortlaut "Funding-Bein-Mittel weder ausgegeben
  noch gespeichert". Vom Auftrag so angelegt, kein Preis-/Gesamtmittel; nur Wortlaut korrigieren.

### N-2 (NIEDRIG) Funding-Buchhaltung - geprueft, in Ordnung

- I je Zahlung `0,01 % * 3/funding_n` = 0,03 %/Tag in jeder Klasse; eigener Schluessel aus Rohspalten identisch
  (`rv_load.py`). Wochen-SUMME, ISO-Woche; Vorzeichen g = mean_U(F) - mean_D1(F) richtig (Long zahlt F, Short erhaelt
  F). Umschalt-Tage <= 0,875 bp Fehler, 0,4 / 0,8 % der D1-Tage. Sonderpaare (USDCUSDT, ETHBTCUSDT) tragen im Schluessel
  faelschlich I = 0,03 %/Tag (kuenstlich -21 bp/Woche) und rutschen so in D1: 16 / 9 Symbol-Wochen - unerheblich,
  EV-11 (3) behebt es. Universumsmitglieder ohne Funding-Daten: W1 0, W2 <= 6 je Woche. Ungueltige Renditezellen
  Nuisance: 0 (die 0-Ersetzung in `a1_nuisance.py` wirkt nicht).

### N-3 (NIEDRIG) Stufe 2 formal vollstaendig, aber nur Akte

- Zwoelf Pflichtzeilen vorhanden, DEC-39-Trio und Positivkontrolle mit vorab fixierter Bestehensregel, die die
  Power-Annahme prueft (A3-Lehre). Zeile 1 rechnet mit c = 1 (B-1) und braucht theta (B-2) - nicht registrierbar.
  K = 1 statt PRD K = 3 ist eine weitere beguenstigende Abweichung (H-1), braucht eine DEC.

---

## R. Unabhaengige Nachrechnung (eigener Code, gleiche Daten)

| Groesse | Herleitung | Review | Status |
|---|---:|---:|---|
| Formationsspread Mittel W1 / W2 (bp/Woche) | 175,8 / 339,6 | 175,78 / 339,57 | bestaetigt |
| K min/median/max W1; W2 | 343/418/511; 512/584/600 | gleich | bestaetigt |
| Nuisance SD x (bp), rho_1 x, corr(p,g) | 354,5; -0,250; 0,127 | 354,47; -0,2498; 0,127 | bestaetigt |
| phi (Summe g / Summe s) | 0,5729 | 0,5729 | bestaetigt |
| Schluessel-Autokorrelation W2 (min 12 / min 8) | 0,303 / 0,2997 | 0,3029 / 0,2997 | bestaetigt |
| GL-012 c = 1: 3,168*SE_gep. vs prem; theta_min | 113,0 vs 147,6; 0,766 | 113,0 vs 147,6; 0,766 | bestaetigt |
| GL-012 DEC-67 E4 | 176,5 vs 147,6 (GL-012) | 176,5 vs 147,6 (GL-012) | bestaetigt |
| P_fenster W1 / W2 (c = 1, theta = 1); MDE80_W1 | 0,619 / 0,990; 128,6 | 0,619 / 0,990; 128,6 | bestaetigt |
| D1-Degeneration | 0,524 / 0,714 | nicht nachgerechnet | - |

Reproduktion: `cd /tmp && PYTHONPATH=/home/user/scinance/src python -I scratchpad/a1_review/rv_load.py`, danach
`rv_formation.py`, `rv_nuisance.py`, `rv_power.py`, `rv_wp7_zerofill.py` (je Sekunden).

## Auflagen, falls der Orchestrator A1 dennoch offen haelt

1. Feststellung in `FEASIBILITY.md` 0/8 durch die Ersatz-Feststellung oben ersetzen; Stufe 2 als bedingt ohne
   Rechtswirkung kennzeichnen.
2. Keine A1-spezifische Entscheidung zu EV-2; wenn ueberhaupt, programmweite DEC mit Etikett (B-1 Punkt 3).
3. theta-Quelle mit Stichprobe vor 2024-07 und Querschnittsbezug, sonst keine Registrierung (B-2).
4. W2-SD mit skaliertem Funding-Bein (M-1) und stationaerer Bootstrap (M-2) in jeder kuenftigen Power-Zeile.
5. Kill (4): formale Lesart dokumentieren, W2-Etikett "an der Grenze, schaetzerabhaengig" (H-2).
