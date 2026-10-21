# Gate-Review Registrierung H-32 - Nachpruefung auf Vorlauf v6b (Pruefpunkte 1-5, Regel U-3, Umsetzung V-1/A-1..A-5)

> Stand 2026-10-21. Gegenstand: DEC-101 Teil 1 (`state/decisions.md`), Code-Commits `6e4b447` (DEC-101 Teil 1) und
> `f07d060` (Regel U-3), HEAD `d9c8585`; Vorlauf v6b `state/runs/h32_20261021_v6b/` (`h32_prelaunch.json` sha256
> `f872a3af...f98c`, result_sha256 `eee9ced9...65ab1`, p-Replikate `3c498e07...56ef`, K-Reihen, `.md`,
> `h32_pp3_dry_run.json` `6c5e2947...8a83`), Logs `scratchpad/h32_v6b_r1.log`, `h32_v6b_r2.log`, Zweitlauf-Ordner
> `scratchpad/h32_v6b_run2`, `scratchpad/h32_pp3_dry.log`; Vorlage `h32_v1_TEMPLATE.yaml` (sha256 `a3079cf9...bbe9`);
> `REGISTRIERUNG_H32_entwurf.md` Fassung 2. Massstab wie im Erstreview (`REVIEW_REGISTRIERUNG_H32.md`).
>
> **Ergebnisblindheit.** Keine Datenrechnung mit Outcome, kein Pilot-/Test-/Positivkontroll-Lauf auf Realdaten, kein
> Panel geladen. Gelesen: v6b-Artefakte (Nuisance, Null-Replikate), Vorlage, Akten, Code, Logs. Sperren und Gate wurden nur
> mit temporaeren, synthetischen Dateien bzw. Zahlen geprueft. Siegeldateien nie geoeffnet. Nichts committet. Skripte:
> `scratchpad/h32_reg_review2/` (Abschnitt 8).

---

## 1. Urteil

**VETO aufgehoben: JA.** V-1 (Universum), A-1 (skalierte Null), A-2 (Pilot-Sperre), A-3 (Pins) sind umgesetzt und
nachgeprueft. Die v6b-Zahlen sind ohne Abweichung nachgerechnet. Die Zwillinge sind aus K verschwunden.

**Neues Urteil: ZUSTIMMUNG MIT AUFLAGEN.** Vor der Registrierung sind N-1, N-2, N-4 und N-5 (Abschnitt 6) zu
erfuellen; N-3 ist eine Empfehlung. Die
gewichtigste Auflage betrifft die Positivkontrolle. Die Entscheidung des Builders (Gate-Kette der PK ohne Skalierung,
Erstfassung 4 woertlich) ist **nicht akzeptabel**:
- Die PK prueft dann eine mildere Bedingung (1c) als der Test (Produktionskonfiguration, DEC-94 (5)).
- Das woertliche Injektionsziel von Erstfassung 4 liegt fuer (1c)-bindende Varianten unter der MDE80 des Gates. Erwartete
  PASS-Quote im bindenden Fenster bei k = 1: mom4 0,72 (< 0,734), mom2 0,76, rev_gap 0,75.
- Folge: Eine Nicht-Bestehen-Wahrscheinlichkeit von ~65 % (mom4) entsteht erst nach dem verbrauchten Pilot.

Eine erneute Vetopruefung ist nicht noetig, wenn N-1 und N-2 wie formuliert umgesetzt und mit T0/T4-Tests belegt sind.
Weicht der Orchestrator ab, ist eine kurze Nachpruefung angezeigt.

## 2. Kurzfassung (<= 10 Zeilen)

1. VETO aufgehoben: Universum lineare USDT-Perps (1.182 -> 1.066, 68 USDC-Perps + 48 Futures, excluded_sha256 nachgerechnet), K jetzt unter den USDT-Lebendzahlen (2025-11-03 510 < 557; vorher 560); v6b zweimal bitgleich (alle 6 Dateien), PP3-Trockenprobe ok.
2. Nachrechnung ohne Abweichung: alle Frozen-Werte (inkl. q95 = max(1.000er, 10.000er), bindende Zellen, Draw-Hashes), floor/v, K-Reihen, m_P, result_sha256, Vorlage per Re-Emit bitgleich, T/Decke 0,445..0,640, U-3-Schwellen 0,020538/0,023027/0,028049/0,018465 bitgleich mit handover.py; 277 Tests gruen.
3. U-3: YAML-Text = `C.HANDOVER_COND_II`, Logik identisch; am Rand uebergeben, 1e-9 darunter nicht; Fensterpowers (1b)/(1c) >= 0,80; OC <= 0,29 % (Lage m_P) bzw. <= 0,28 % (Lage 0).
4. A-1 korrekt: Gate (1c) und F-WEEK-p mit derselben Transformation (k, m, q95); p an y = q95_eff 0,040..0,050 fuer k = 1/1,1/1,3; NaN schliesst; Verify leitet nach. A-2/A-3 an temporaeren Dateien geprueft: neues Verzeichnis, Fremdtreffer, Baum-Pin, Runner-Pins greifen.
5. HOCH N-1: Die PK nutzt q95 ohne Skalierung (keine Produktionskonfiguration). Bei realer SD x1,1 ueberschaetzt sie die PASS-Quote um +0,045..0,05.
6. HOCH N-2: Das PK-Ziel (z SE_T + z80 SD_T) liegt fuer (1c)-bindende Varianten und rev_gap unter der Gate-MDE80 der PK-Welt. Erwartete Quote 0,78/0,76/0,72/0,75 -> ~65 % Fehlschlag mom4 nach verbrauchtem Pilot. Vorschlag F liefert 0,80 fuer alle.
7. NIEDRIG N-3 (Empfehlung): Der (1c)-Term von U-3 nutzt q95 mit k = 1; bei Pilot-k 1,1..1,3 sinkt die Uebergabe-Power fuer (1c) auf 0,797..0,790 (mom4, sonst >= 0,798). U-4 mit k_pred stellt 0,80 her und aendert bei k_pred = 1 keine Zahl.
8. MITTEL N-4: Die Pilot-Sperre sieht keinen abgebrochenen Lauf. x_P wird geloggt, bevor eine Datei existiert; ein Versuchsmarker im gepinnten Verzeichnis vor dem Laden genuegt (vom Glob erfasst, getestet).
9. NIEDRIG N-5: DEC-101 E5 sagt "Regel U unveraendert" (Widerspruch zu U-3 -> Teil 2); A3-Werte 0,0259/0,0287/0,0336/0,0247; Endpower mom4 an der U-3-Schwelle 0,738/../0,379/0,126. Weitere Errata in Abschnitt 5: v6b-Code 6e4b447 neben dem Registrierungs-Commit, Registry-Text q95_eff, fdr.p_formula, Abweichung 11, voller prelaunch-sha.
10. Nicht folgt: kein Urteil ueber H-32; die Testfehlerraten sind nach A-1 robuster als in v6a; die Auflagen betreffen PK-Gueltigkeit, Power-Konsistenz und Sperren.

---

## 3. Pruefpunkte 1-5 auf v6b (und U-3)

| # | Pruefpunkt | Befund | Beleg |
|---|---|---|---|
| 1 | Panel, Fingerprints, Universum, Determinismus | **BESTAETIGT** | Fingerprints unveraendert (Dateien gleich): union_range `e503bedb...`, register `a28c7eb7...`, Baum `250a923b...`, delisting_dates `c1306c56...` in JSON, YAML (jetzt mit Baum-Pin) und Entwurf. Runner-Pins as_of 2026-09-28, 2021..2026, allow_partial in JSON und YAML. Universum: 1.182 -> 1.066, ausgeschlossen 68 `*PERP` + 48 `*-DDMMMYY` + 0 sonstige; excluded_sha256 `50aaee3c...` aus der Liste nachgerechnet, kein ausgeschlossenes Symbol ist ein linearer USDT-Perp; YAML-Pin `excluded_at_prelaunch` 68/48/0. Schnitt 2026-06-28 (82 Tage, max 2026-06-28, letzte Woche 2026-06-22), 1.066 -> 882 Symbole (184 ohne Daten vor dem Schnitt). K_fm8 gegen die lebenden USDT-Perps des Orchestrators: 2023-01-02 179 <= 181, 2025-07-07 501 <= 530, 2025-11-03 510 <= 557 - in v6a lagen K darueber (186, 537, 560). v6b-Lauf 1 und 2 (parallel, 17:22..19:03 UTC) liefern sechs bitgleiche Dateien. PP3-Trockenprobe: K_fm8-Reihen P (Schnitt 2024-06-30), W1, W2 = Pins, keine IC. v6b-Code = Commit `6e4b447` (alle 46 Datei-Hashes); seither geaendert nur `constants`, `handover`, `powerline`, `vorlauf` (U-3, Vorlagentext) - keine eingefrorene Konstante betroffen (N-5). |
| 2 | Fenster und Zaehlungen | **BESTAETIGT** | P 115 Kalenderwochen / 114 geurteilt (2022-04-18..2024-06-17, Outcome bis 2024-06-24), W1 53/52, W2 51/50; K (alive) P 126/206/339, W1 343/416,5/500, W2 501/526/545 (Kill 117/134 nicht ausgeloest); Entwurf rundet 416,5 -> 416. |
| 3 | Eingefrorene Groessen | **BESTAETIGT** | se_mean, e_se_rule, sd_week, null_mean = Maximum der Zellen (32/32 bitgleich); q95_1000 = max der Zellen-q95, q95_10000 = `numpy.quantile` der 10.000 p-Replikate der bindenden Zelle, q95 = max (alle bitgleich); ceiling = driftfreie Zelle; erste 1.000 Replikate = Zellen-Mittel und Draw-Hash; floor/v aus den K-Reihen bitgleich; m_P = max der P-Zellen. Ueberschreitung des eingefrorenen q95 in den unabhaengigen Replikaten 1.001..10.000: W1 4,1/4,4/3,9/5,0 %, W2 5,0/5,0/5,0/5,1 % (B-6 behoben). T_W,v / Decke: W1 0,578/0,520/0,447/0,640, W2 0,567/0,511/0,445/0,616 - kein Vor-Verdikt-Kill. Groesse des Gates im Null-Modell (k = 1): W1 4,2/3,9/3,5/3,6 %, W2 4,3/4,4/3,9/3,1 %. |
| 4 | Power-Zeile, U-3, Endpower | **BESTAETIGT** (Zahlen, Code = YAML); Rest N-3 (Empfehlung), N-5 | MDE80 (1b mit Gutschrift / 1c) wie Artefakt und Entwurf; U-3-Schwellen bitgleich mit `evaluate_handover` (bindend U/U/1c/U); an der Schwelle C10, Fensterpowers (1b) W1/W2 mom1 0,831/0,920, mom2 0,838/0,919, mom4 0,860/0,943, rev_gap 0,800/0,878; (1c) 0,817/0,926, 0,809/0,912, **0,800**/0,923, 0,857/0,923; A3-Praxis am Rand GL012. OC Abschnitt 7.4. Endpower Abschnitt 7.3. |
| 5 | p-Konvention mit skalierter Null | **BESTAETIGT** (Rest NIEDRIG) | Testlauf: `k = scale_factor(SD(IC_t), sd_week)`, `q95_eff = q95_effective(m, k, q95)`, p aus `scaled_replicates(d, m, k)` - dieselben m (eingefrorenes Null-Mittel = bindende Zelle), k und q95 in Gate und p; Max-p W1/W2; unskaliertes p report-only; `verify_run_artifacts` leitet k, q95_eff und p aus Serie und Konstanten nach. Nachgerechnet: p an y = q95_eff je Zelle 0,040..0,0501 fuer k = 1, 1,1, 1,3 (monotone Transformation, (1c) erzwingt p <= ~0,05). NaN-k -> (1c) verfehlt, p = 1. Rest: Gate-Fallback ohne `null_scaling` (k = 1) und `fdr.p_formula` ohne Skalierung (N-5). |

## 4. Umsetzung V-1, A-1..A-5 (DEC-101 Teil 1) im Code

| Auflage | Umsetzung | Pruefung (eigene Probe) | Befund |
|---|---|---|---|
| V-1 Universum | `universe.py`: Filter nach Fingerprint, vor Schnitt und Rechnung, in allen Modi (`ensure_universe`, `assert_universe`), Pin `universe.rule` + `excluded_at_prelaunch`, Bericht mit Liste und sha256 | Zaehlungen, sha, K-Gegenprobe (Pruefpunkt 1) | BESTAETIGT |
| A-1 skalierte Null | `estimators.scale_factor / q95_effective / scaled_replicates`, `gate.effective_q95`, `testrun` (Payload `null_scaling`), YAML-Block `null_scaling` | Gate mit k = 1,2: q95_eff 0,0200 statt 0,0170, (1c) verfehlt; NaN schliesst; p-Konsistenz (Pruefpunkt 5) | BESTAETIGT; PK nicht einbezogen (N-1) |
| A-2 Pilot-Sperre | `pilot_window.out_dir` (gepinnt), `check_pilot_out_dir`, `find_pilot_results` (rekursiv unter `state/runs`, gleicher registered_sha256), Neuprufung im Writer | anderes `--out` -> Abbruch; Treffer in anderem Verzeichnis -> Abbruch auch im gepinnten; Treffer anderer Registrierung -> erlaubt; unlesbare Musterdatei -> Abbruch; Markerdatei `h32_pilot_attempt.json` wuerde erkannt | BESTAETIGT; Restluecke Abbruch vor dem Schreiben (N-4) |
| A-3 Pins | `delisted_tree_sha256` Pflicht (Schema + `check_data_fingerprints`), `runner`-Block, `check_runner_pins` vor dem Laden | falscher Baum-Hash -> Abbruch; YAML ohne Pin -> Schema- und Fingerprint-Abbruch; as_of = heute bzw. ohne allow_partial -> Abbruch | BESTAETIGT |
| A-4 q95-Regel, Power-Ausweis | `frozen_q95`, `powerline.py`, U-3 (`f07d060`) | Pruefpunkte 3, 4 | BESTAETIGT; unter skalierter Null Power-Rest <= 0,01 (N-3) |
| A-5 Determinismus, PP3, mu_sel | v6b x2 bitgleich, `pp3.py` (`--pp3-dry-run`, keine IC), `mu_sel_detail` (Platzhalter als "keine Loesung") | Hashes beider Laeufe, PP3-JSON; mu_sel an c_v + 0,5 SE_P geloest (z. B. mom1 0,0167) | BESTAETIGT |

---

## 5. Befunde

### N-1 (HOCH; Entscheidungspunkt des Builders) Positivkontrolle nicht in Produktionskonfiguration

`positive_control.py` beurteilt jede Urteils-Seed mit `gate.window_conditions({"y", "se_w", "q95": frozen})`, also ohne
`null_scaling`. Der Test beurteilt mit q95_eff = max(0, m) + k (q95 - m), k aus der realen Wochen-SD. Die PK-Welt wird auf
die Wochen-SD sqrt(v_fm8 + max(F2_null, F2_real)) kalibriert. Ist F2_real > F2_null, gilt in der PK-Welt k > 1, und die
PK prueft eine mildere Bedingung (1c) als der Test.

Beispiel k = 1,1, woertliches Ziel: Erwartete PASS-Quote im bindenden Fenster ohne Skalierung mom1 0,817, mom2 0,808,
mom4 0,794; mit Skalierung 0,772 / 0,761 / 0,744. Die falsche PASS-Quote der Negativkontrolle steigt ohne Skalierung auf
5,7 / 5,3 / 4,8 % (mit Skalierung 4,1 / 3,8 / 3,4 %).

Richtung: Testbarkeit fuer Kriterium (b), Strenge fuer (c). DEC-94 (5) und PRD 3.3.8 verlangen die PK in
Produktionskonfiguration. Erstfassung 4 nennt als Gate-Kette "die Bedingungen (1a)-(1c) und (4b) **des Tests**" - nach
DEC-101 E2 ist (1c) des Tests die skalierte Bedingung. Die woertliche Lesart stuetzt die Entscheidung des Builders also
nicht. **Auflage:** k je Seed aus der Wochen-SD der synthetischen Serie gegen das eingefrorene `sd_week` und der
`null_scaling`-Block wie im Test (Negativ- und Positivkontrolle); YAML-Satz im Block `positive_control`.

### N-2 (HOCH) Injektionsziel der PK unter der Gate-MDE80 der PK-Welt

Erstfassung 4 injiziert den realisierten Effekt z SE_T + z80 SD_T ("ohne Gutschrift; die Gutschrift traegt die Null
selbst"). Das stammt aus der Zeit vor B-4/A-4. Seit U-3 ist die MDE80 der Power-Zeile das Maximum ueber (1b) und (1c).
In der PK-Welt (stress, Drift 0) ist das Null-Mittel das der driftfreien Zelle (m_df W1: mom1 0,00122, mom2 0,00158,
mom4 0,00193, rev_gap -0,00120).

Erwartete PASS-Quote im bindenden Fenster (W1) beim woertlichen Ziel und k = 1 (`rr2_pk.py`): mom1 0,781, mom2 0,763,
**mom4 0,722**, rev_gap 0,752. Gruende:
- (1c) bindet bei mom4 (q95 0,0198 > m_df + z SE_W).
- rev_gap verliert in der Welt sein negatives Null-Mittel.

Kriterium (b) verlangt >= 0,734 bei 200 Seeds (SE ~0,03). Erwartete Fehlschlag-Wahrscheinlichkeit: mom4 ~65 %, rev_gap
~30 %, mom2 ~17 %, mom1 ~6 %. Ein NICHT BESTANDEN heisst "kein Test, neue DEC" - nach dem verbrauchten Pilot. Das ist
kein Power-Befund ueber das Design, sondern ein Definitionsfehler des Ziels. Kriterium (b) setzt eine erwartete Quote von
0,80 voraus.

**Auflage (Vorschlag F):**
```
Ziel_W = max(z_krit SE_T,W + z_80 SD_T,W - min(0, m_df,W),  q95_eff,W(k_pred,W) - m_df,W + z_80 SD_T,W)
```
- Das bindende Fenster ist argmax_W.
- k_pred,W = max(1, sqrt(v_fm8,W + F2_real) / sd_week_W,v) ist dieselbe Groesse, auf die die Welt-SD kalibriert wird.
- Damit liegt die erwartete Quote bei k_pred = 1; 1,1; 1,2 fuer alle vier Varianten bei 0,800 (`rr2_pk_f.py`).
- Die Kriterien (a), (c), (d) bleiben.
- Etikett: "Korrektur nach DEC-94 (3) (Review B-4/A-4), vor jeder Pilot-Zahl"; DEC-101 Teil 2.

### N-3 (NIEDRIG, Empfehlung) Regel U-3 nimmt fuer (1c) k = 1 an

Der (1c)-Term von U-3 ist max_W(q95_W,v + z80 SD_T,W) mit dem eingefrorenen q95. Der Test skaliert q95 mit k.

Meldet der Pilot F2_real > F2_null, so steigen SE_W,Pilot und SD_T mit k_pred, und der U-Term deckt den groessten Teil
ab. Rechnung (`rr2_u3k.py`, SE_T = max(e_se_rule, k se_mean), SD_T = k se_mean): kleinste Fensterpower der skalierten
Bedingung an der U-3-Schwelle
- mom4: 0,802 (k 1), 0,797 (1,1), 0,794 (1,2), 0,790 (1,3);
- mom2: bei 1,3 0,798;
- mom1 und rev_gap: >= 0,80.

Ein Rest von <= 0,01 Power gegen DEC-94 (3) bleibt. Empfehlung: im (1c)-Term `max(0, m) + k_pred,W (q95 - m) + z80 SD_T`
(k_pred wie N-2), Version U-4, YAML-Text = Code-Konstante, T0/T4-Test.
- Bei k_pred = 1 aendert sich keine Schwelle.
- Fuer rev_gap ist der (1c)-Term dann auch bei k = 1 mit dem Test deckungsgleich (q95 + |m|). Er bindet nicht: 0,017981
  gegen 0,018465.

Unterbleibt U-4, genuegt das Etikett "U-3 deckt (1c) unter skalierter Null bis auf <= 0,01 Power".

### N-4 (MITTEL) Genau-ein-Pilot: abgebrochener Lauf hinterlaesst keine Spur

`pilot.run_pilot` schreibt x_P, SE_P und t_P je Variante ins Log (Z. 102), bevor `write_pilot_artifacts` die erste Datei
anlegt.

Faellt der Lauf nach der ersten Variante aus, entsteht keine Datei `h32_pilot*` im gepinnten Verzeichnis. Beispiele:
`H32Abort` bei fehlenden Wochen einer spaeteren Variante, `ValueError` in `pilot_statistics`, Abbruch des Prozesses. Die
Sperre erlaubt dann einen zweiten Lauf ohne DEC, obwohl Pilotwerte gesehen wurden.

Fehler innerhalb von `write_pilot_artifacts` sind dagegen erfasst: CSV und `h32_pilot_fingerprint.json` mit
registered_sha256 werden vor der Pruefung geschrieben.

**Auflage:** vor dem Laden des Panels `h32_pilot_attempt.json` (registered_sha256, Zeitstempel, Modus) in
`pilot_window.out_dir` schreiben. Glob und Suche erfassen die Datei bereits (geprueft). Test "Abbruch nach dem Marker ->
zweiter Lauf nur mit DEC".

### N-5 (NIEDRIG) Errata und Dokumentation

1. DEC-101 E5 sagt "Regel U bleibt unveraendert (Erstfassung 1.8)". U-3 (f07d060, nach Kenntnis der v6b-Power-Zeile:
   Marge mom4 -0,000587, Richtung Strenge, vor jeder Pilot-Zahl) steht nur im Commit, in der Vorlage und im Entwurf.
   Teil 2 muss E5 ausdruecklich ersetzen, mit Etikett.
2. Code-Bezug: v6b (result_sha256 `eee9ced9...`) ist mit Code `6e4b447` gerechnet und nur damit bitgleich
   reproduzierbar - der Block `power_line` zeigt noch U-2 (mom4 0,027462). Registry und DEC nennen beide Commits: v6b-Code
   `6e4b447` und Registrierungs-Code HEAD. Dazu den Satz "die seitherigen Aenderungen beruehren keine eingefrorene
   Konstante (constants/handover/powerline/vorlauf: Version, U-3, Vorlagentext)".
3. Entwurf, A3-Praxis auf x_P mit Gutschrift: mom1 0,0259, mom2 0,0287, mom4 **0,0336**, rev_gap 0,0247 (Entwurf
   0,0257 / 0,0286 / 0,0329 / 0,0247; 0,0329 ist der v6a-Wert).
4. Entwurf, Endpower mom4 an der U-3-Schwelle: 0,738 / 0,675 / 0,507 / 0,379 / 0,126 (Methode des Artefakts).
   Registry-Spannen: m4 [0,38, 0,44], m11 [0,12, 0,21].
   - Die Artefakt-Methode `end_power_replicates` legt z_eff auch auf (1b). Die Regel kennt das nicht: BY wirkt nur auf p.
   - Das ist eine strenge Untergrenze. Mit (1b) = z_krit und transformierten Replikaten ergibt sich rev_gap m = 4 0,478
     statt 0,417, m = 11 0,279 statt 0,205.
   - Als Untergrenze etikettieren oder angleichen.
5. Registry-Block `threshold.formel` "max(1.6449 * SE_W, q95_W)" -> q95_eff (DEC-101 E2); EV-7 im DEC-Entwurf ebenso.
   `fdr.p_formula` der YAML nennt die unskalierten Replikate (der Block `null_scaling` regelt es - Verweis ergaenzen).
6. Abweichung 11 im Entwurf noch mit "5 Symbole mehr" und "v6-Zweitlauf optional" (v6b lief zweimal). EV-4 ohne
   Universum. C.17-Absatz ohne die B-9-Punkte (stehen nur unter Abweichung 15).
7. Registry: `prelaunch_v6b` mit vollem sha256 (`f872a3af25753e84db2ac99d412ccfecc349b8bbedab2fc23868d83ffed3f98c`); K-Median
   W1 416,5.
8. `gate.effective_q95` faellt ohne `null_scaling`-Block auf k = 1 zurueck. Der Testlauf liefert den Block immer, das
   Verify prueft ihn. Empfohlen: im Testmodus fehlender Block = Abbruch.

---

## 6. Auflagen VOR der Registrierung

- **N-1** PK-Gate-Kette mit `null_scaling` wie im Test (k je Seed); YAML-Satz; Test.
- **N-2** PK-Injektionsziel nach Vorschlag F (oder eine gleichwertige Definition mit erwarteter Quote 0,80 im bindenden
  Fenster); DEC-101 Teil 2 mit Etikett; Test (Fixture: erwartete Quote ~0,8).
- **N-3 (Empfehlung)** U-4: (1c)-Term mit k_pred; YAML-Text = Code-Konstante; T0/T4 - oder Etikett nach N-3. Nach jeder
  Regelaenderung die Vorlage neu emittieren (die v6b-Konstanten bleiben, nur Regeltexte aendern sich).
- **N-4** Versuchsmarker vor dem Panel-Laden; Test.
- **N-5** Errata 1-7 in DEC-101 Teil 2, Entwurf und Registry; 8 empfohlen.

Die eingefrorenen Konstanten, die Fingerprints und v6b selbst bleiben unberuehrt; kein neuer Vorlauf noetig. Der
Orchestrator nimmt N-1..N-5 ueber Tests und den Re-Emit selbst ab. Eine erneute Vetopruefung ist nur bei Abweichung von
N-1/N-2 noetig.

## 7. Nachrechnung (eigenes Skript mit power_p1, handover, estimators; v6b-Konstanten)

### 7.1 Artefakt

| Groesse | v6b / Entwurf | eigener Wert | Abweichung |
|---|---|---|---|
| result_sha256 (kanonisch, ohne `code`) | eee9ced9...65ab1 | identisch | 0 |
| Dateien Lauf 1 / Lauf 2 | 6 Dateien | alle sha256 gleich | 0 |
| Vorlage | a3079cf9...bbe9 | Re-Emit an HEAD bitgleich; validiert | 0 |
| v6b code_sha256 | a280a7bd... | = Commit 6e4b447 (46/46 Dateien); HEAD daef2dc3... (4 Dateien geaendert, keine Konstante) | erklaert (N-5.2) |
| YAML gegen JSON (alle Frozen-Felder inkl. q95_1000/q95_10000, m_P, K-sha) | - | 0 Abweichungen | 0 |
| Universum / excluded_sha256 | 1.182 -> 1.066; 68/48/0; 50aaee3c... | identisch | 0 |
| floor/v P, W1, W2 | 0,069642/0,004924; 0,048821/0,002391; 0,043639/0,001905 | bitgleich | 0 |
| m_P | 0,002152 / 0,002857 / 0,003829 / -0,002079 | bitgleich | 0 |

### 7.2 Schwellen, Power-Zeile, U-3

| Variante | MDE80 W1 (1b+G / 1c) | MDE80 W2 (1b+G / 1c) | m* | Schwelle_U | max (1c) | U-3 Entwurf | U-3 eigen = Code | bindend |
|---|---|---|---:|---:|---:|---:|---:|---|
| mom1 | 0,019676 / 0,020093 | 0,017057 / 0,016788 | 0,002152 | 0,020538 | 0,020093 | 0,020538 | 0,020537529 | U |
| mom2 | 0,021848 / 0,022769 | 0,019084 / 0,019428 | 0,002857 | 0,023027 | 0,022769 | 0,023027 | 0,023026502 | U |
| mom4 | 0,025699 / 0,028049 | 0,021974 / 0,023288 | 0,003829 | 0,027462 | 0,028049 | 0,028049 | 0,028048856 | (1c) |
| rev_gap | 0,018465 / 0,016785 | 0,016363 / 0,014698 | 0 | 0,018465 | 0,016785 | 0,018465 | 0,018464794 | U |

### 7.3 Endpower an der U-3-Schwelle (m = 1 / 2 / 3 / 4 / 11)

| Variante | Artefakt-Methode (z_eff auch auf (1b)) | Gate (1b z_krit, 1c, BY auf transformierten Replikaten, k = 1) |
|---|---|---|
| mom1 | 0,751 / 0,689 / 0,548 / 0,444 / 0,201 | 0,751 / 0,701 / 0,546 / 0,442 / 0,200 |
| mom2 | 0,738 / 0,661 / 0,494 / 0,382 / 0,124 | 0,738 / 0,660 / 0,491 / 0,380 / 0,122 |
| mom4 | 0,738 / 0,675 / 0,507 / 0,379 / 0,126 | 0,738 / 0,675 / 0,502 / 0,376 / 0,123 |
| rev_gap | 0,703 / 0,620 / 0,497 / 0,417 / 0,205 | 0,703 / 0,652 / 0,551 / 0,478 / 0,279 |

### 7.4 OC, Groesse, Skalierung, PK

| Groesse | Wert (mom1 / mom2 / mom4 / rev_gap) |
|---|---|
| P(Uebergabe), Lage m_P | 0,29 / 0,24 / 0,16 / 0,10 % |
| P(Uebergabe), Lage 0 | 0,10 / 0,07 / 0,03 / 0,28 % |
| Groesse Gate (1b)+(1c), Null-Modell k = 1 | W1 4,2 / 3,9 / 3,5 / 3,6 %; W2 4,3 / 4,4 / 3,9 / 3,1 % |
| (1b) allein (nur Information) | W1 6,7 / 7,4 / 8,6 / 3,6 %; W2 5,4 / 7,5 / 8,6 / 3,1 % |
| p an y = q95_eff (k = 1 / 1,1 / 1,3) | 0,040..0,050 je Zelle, fuer alle k gleich |
| PK: erwartete PASS-Quote, woertliches Ziel, k = 1 | 0,781 / 0,763 / **0,722** / 0,752 |
| PK: k = 1,1, ohne / mit Skalierung | 0,817/0,772, 0,808/0,761, 0,794/0,744, 0,757/0,757 |
| PK: Vorschlag F, k = 1 / 1,1 / 1,2 | 0,800 fuer alle Varianten |

## 8. Was NICHT folgt

- Kein Urteil ueber H-32; keine Effektaussage; Pilot, W1, W2 bleiben blind.
- Die Fehlerrate des Tests ist mit A-1 und dem bereinigten Universum besser geschuetzt als in v6a. N-1/N-2 betreffen die
  Gueltigkeit der Positivkontrolle, N-3 einen Power-Rest <= 0,01, N-4 die Pilot-Sperre.
- Kein neuer Vorlauf; die v6b-Konstanten und Fingerprints bleiben.

## 9. Reproduktion (`scratchpad/h32_reg_review2/`)

| Skript | Inhalt |
|---|---|
| `rr2_check.py` | Hashes, result_sha256, Universum, YAML gegen JSON, Zellen, q95-Regel, floor/v, K, Schwellen, U-3 gegen Code, Endpower (zwei Methoden), OC, Groesse, Skalierungskonsistenz -> `rr2_check.json` |
| `rr2_locks.py` | Pilot-Sperre, Baum-Pin, Runner-Pins, Gate mit/ohne Skalierung an temporaeren Dateien -> `rr2_locks.json` |
| `rr2_pk.py`, `rr2_pk_f.py` | erwartete PK-Quoten (woertliches Ziel, skaliert/unskaliert, Vorschlag F) |
| `rr2_u3k.py` | Fensterpower der skalierten (1c) an der U-3- bzw. U-4-Schwelle bei Pilot-k 1..1,3 |
| `h32_v1_reemit.yaml` | Re-Emit der Vorlage an HEAD (bitgleich) |
| `tests.log` | test_h32_* + test_power_p1: 277 passed |
