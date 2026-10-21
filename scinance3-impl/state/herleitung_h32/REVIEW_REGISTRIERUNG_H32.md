# Gate-Review Registrierung H-32 (adversarisch, Gate-Auditor mit Veto): Vorlauf v6, Registrierungs-Vorlage, Registry-Eintrag, DEC-101-Entwurf

> Stand 2026-10-21. Gegenstand: `state/runs/h32_20261021_v6/` (`h32_prelaunch.json` sha256 `96edd5ea...1ddb831a`,
> result_sha256 `2ae9bad6...dd6fa0`, `h32_prelaunch_p_replicates.json` sha256 `f10250dd...02847a62`, K-Reihen, `.md`),
> Lauf-Log `scratchpad/h32_v6.log`, Vorlage `state/herleitung_h32/h32_v1_TEMPLATE.yaml` (sha256 `bddfb9cb...a28d90`),
> `REGISTRIERUNG_H32_entwurf.md` (Vorbedingungen, Kernzahlen, Power-Zeile, DEC-101-Entwurf, Registry-Block),
> Orchestrator-Nachrechnung `scratchpad/orch_check/h32_v6_power.py` (+ `.json`). Massstab in dieser Reihenfolge:
> `scinance3-impl/CLAUDE.md`; DEC-94, DEC-96, DEC-99 (+N1), DEC-100 (+N1); `ERSTFASSUNG_H32_entwurf.md` (0, 1, 2, 4, 5, 9,
> 10, 11) und `REVIEW_H32.md`; `state/BEFUND_DATENSTROEME_2026-10-21.md`; Paket `src/bybit_edge/research/h32_fm8/` und
> `scripts/h32_fm8.py`.
>
> **Ergebnisblindheit dieses Reviews.** Keine Datenrechnung mit Outcome: kein Panel-Preis, keine Rendite, kein IC, kein
> Pilot-, Test- oder Positivkontroll-Lauf auf Realdaten. Gelesen: das v6-Artefakt (Nuisance, Null-Replikate), die
> Vorlage, die Akten-Texte, der Code; aus den Panel-Manifesten (Scratchpad-Kopie) und dem Register
> `state/data_harvest_delisting_register_2026-10-21.csv` NUR Symbolnamen, Kontraktklasse, Status, Listungs-/letzter
> Handelstag und Zeilenzahlen je (Symbol, Jahr) - Vollstaendigkeits-Metadaten im Sinne von DEC-96 E3; aus dem
> Spread-Zensus nur den Wert D10. Die Smoke-Verzeichnisse `scratchpad/h32_smoke/` sind laut ihren Skripten synthetisch
> (`h32_fixtures.make_panel`); ihre Ausgaben wurden nicht geoeffnet. Nie geoeffnet: `*_L_window_sealed.json`,
> `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`. Nichts committet. Eigene Skripte:
> `scratchpad/h32_reg_review/` (Abschnitt 8).

---

## 1. Urteil: VETO (aufloesbar; kein Rechenfehler, sondern ein Universums- und Null-Modell-Befund)

Die Arithmetik ist sauber: Jede eingefrorene Zahl der Vorlage ist bitgleich aus dem v6-Artefakt reproduziert,
result_sha256 und Vorlage sind bitgleich nachgebaut, die Power-Zeile des Entwurfs ist mit `power_p1` exakt
nachgerechnet, Regel U im Code ist woertlich Erstfassung 1.8, 196 Tests gruen, code_sha256 = HEAD.

Das VETO betrifft **B-1**: Das v6-Universum ist nicht das, was die Akte beschreibt. Der Ueberlebenden-Baum fuehrt
neben den linearen USDT-Perps **68 USDC-Perps (jeder mit einem USDT-Zwilling) und 48 datierte USDT-Futures** (6 davon
mit Daten vor dem Schnitt, ebenfalls Zwillinge von BTC/ETH); der Delisted-Baum v2 waehlt dagegen nur `quoteCoin USDT`
aus (17 delistete USDC-Perps fehlen, 14 davon lebten im Pilotfenster). Die Zwillinge stehen im K, im Boden und im
Querschnitts-IC; die faktorerhaltende Null simuliert jede Spalte unabhaengig. Folge (synthetisch belegt): die reale
Null-Streuung des Wochen-IC liegt in W2 um ~13 %, in W1 um ~5 % ueber der simulierten; damit sind q95 und das bindende
F-WEEK-p (DEC-99 N1) zu eng - Fenstergroesse von (1b)+(1c) in W2 fuer mom1/mom2/mom4 ~6,4..7,0 % statt <= 5 %
(Richtung Testbarkeit). Die DEC-100-N1-Feststellung "Panel vollstaendig, Ueberlebenden-Verzerrung behoben" gilt nur fuer
die USDT-Perps; nichts davon ist etikettiert. Registriert wuerde ein Universum, dessen Definition die Akte nicht
enthaelt, mit Konstanten, die das Null-Modell auf diesem Universum verfehlen. DEC-100 hat eine Panel-Luecke derselben
Groessenordnung (31 von ~590 in W2) als registrierungssperrend behandelt; Konsistenz verlangt dasselbe hier.

Aufhebung des VETO: Abschnitt 6 (V-1 mit Wahl (a) oder (b), dazu A-1..A-3), danach Nachpruefung der neuen Zahlen
(Pruefpunkte 1-5) durch den Gate-Auditor. Alle uebrigen Punkte sind Auflagen bzw. Errata ohne Vetowirkung.

## 2. Kurzfassung (<= 10 Zeilen)

1. Urteil VETO (aufloesbar): Universum mit 68 USDC-Perps + 6 datierten Futures als Zwillinge (W2 ~11 % von K), Delisted-Seite nur USDT (17 USDC-Delistete fehlen, 14 in P); Null unabhaengig je Spalte -> Null-SD W2 ~x1,13, Groesse (1b)+(1c) W2 mom ~6,4..7,0 %, F-WEEK-p anti-konservativ; nicht etikettiert.
2. Nachrechnung ohne Abweichung: alle Frozen-Werte, floor/v, K-Reihen, m_P, Zellen, result_sha256, Vorlage (Re-Emit bitgleich), T_W,v, Decke/T 0,44..0,67, MDE80 W1/W2, m*, Uebergabeschwellen 0,01998/0,02288/0,02752/0,01787; code_sha256 = HEAD; 196 passed.
3. Abweichungen der Nachrechnung: (1c) q95 bindet in 5/8 Zellen und fehlt in Power-Zeile/Endpower; Endpower mit Replikat-p fuer mom zu guenstig (m=4: 0,43/0,38/0,34 statt 0,48/0,53/0,56; m=11: 0,14/0,08/0,06 statt 0,25/0,30/0,34), rev_gap zu unguenstig (0,53/0,34 statt 0,41/0,20); Orchestrator-Skript rundet z_80 (rev_gap 0,79999).
4. HOCH: Genau-ein-Pilot-Sperre greift nur im selben --out-Verzeichnis (pilot_result_sha256 bleibt in der eingefrorenen YAML null).
5. MITTEL: delisted_tree_sha256 fehlt in der YAML (Registry nennt Pflicht-Pin; Code prueft nur, wenn vorhanden); q95 aus 1.000 Replikaten: in den unabhaengigen 9.000 p-Replikaten Ueberschreitung W1 mom2/mom4 5,6 %, W2 rev_gap 5,9 %.
6. MITTEL: (1b) traegt kein Null-Mittel und E[SE]/SD W2 mom2/mom4 0,94/0,92 -> das Niveau der mom-Zellen haengt allein an q95 der Ein-Faktor-Null; rev_gap-p ist um ein negatives Null-Mittel zentriert (Gutschrift, die Gate und Regel U nicht geben).
7. W1-Determinismus-Ersatz formal ausreichend (Fixture-T2, Baum-Zweitbau, P6/K-Pins vor jedem Outcome), aber Fehler erschienen erst nach verbrauchtem Pilot -> v6 zweimal bitgleich + PP3-Trockenprobe.
8. Auflagen vor Registrierung: V-1 Universum per DEC (empfohlen USDT-Perps, v6 neu x2), A-1 skalierte Null fuer q95/p + keine negative Gutschrift, A-2 Pilot-Sperre technisch, A-3 Baum-Pin, A-4 Power/Endpower-Text, A-5 Errata/C.17.
9. Bestaetigt: Fenster P 114 (115 Kalenderwochen inkl. Outcome-Woche), W1 52, W2 50, P-Outcome endet 2024-06-30 vor W1; Schnitt 2026-06-28 (82 Tage, max 2026-06-28, letzte Woche 2026-06-22); OC Regel U 0,14..0,32 % (Null-Lage m_P); C.17 nichts ergebnisnah.
10. Nicht folgt: kein Urteil ueber H-32, keine Effektaussage; DEC-99/100-Regeln unberuehrt; die v6-Zahlen sind als Rechnung korrekt.

---

## 3. Pruefpunkte (Befund je Punkt)

| # | Pruefpunkt | Befund | Kern |
|---|---|---|---|
| 1 | Panel und Fingerprints | **VETO (B-1)**; Fingerprints BESTAETIGT; Determinismus-Ersatz ABWEICHUNG (B-7) | union_range `e503bedb...`, register `a28c7eb7...`, Baum `250a923b...`, delisting_dates `c1306c56...` identisch in JSON, Registry, DEC-100 N1, Baum-Fingerprint-Datei; Register-Kopie im Repo hasht `a28c7eb7...`. YAML ohne `delisted_tree_sha256` (B-5). Schnitt: Log "82 days removed", `cut.max_date` 2026-06-28, letzte Woche 2026-06-22, 956 von 1.182 Symbolen (226 ohne Daten vor dem Schnitt; der Manifest-Abgleich der Zeilenzahlen ergibt 184 USDT-Perps + 42 datierte Futures). Universum: B-1. |
| 2 | Fenster und Zaehlungen | BESTAETIGT (Errata B-9) | P: 115 Kalenderwochen 2022-04-18..2024-06-24 = 114 Formationswochen (W_P) + Outcome-Woche; dieselbe Konvention wie W1 53/52 und W2 51/50. 114 steht konsistent in `constants.W_PILOT`, `W_JUDGED`, YAML `w_pilot`, Registry; der Pin `check_window_pins` erzwingt sie. K (alive, = K_fm8-Zusammenfassung) P 127/213/353, W1 360/440,5/536, W2 537/589,5/603 gegen Erstfassung 120/202/339, 345/419/514: hoeher (Delisted-Baum v2, Datumskonvention; in W1 +15..+22, nicht "5 Symbole mehr"). Kill PRD 5.3 (117/134) nicht ausgeloest. P-Outcome endet 2024-06-30 < W1-Start 2024-07-01; W1-Outcome endet 2025-07-06 vor der ersten W2-Outcome-Woche 2025-07-14 (dokumentiert in Erstfassung 1.3). |
| 3 | Eingefrorene Groessen | BESTAETIGT (Rechnung); ABWEICHUNG Genauigkeit q95 (B-6) | Alle 40 Fensterwerte (se_mean, e_se_rule, sd_week, null_mean, q95 je Variante) = Maximum der beiden Zellen, bitgleich; ceiling_k4 = driftfreie Zelle; floor/v aus den K-Reihen bitgleich; m_P = max der P-Zellen; T_W,v und Decke/T exakt; kein Vor-Verdikt-Kill (0,443..0,665). Richtung gegen v5e plausibel (Abschnitt 5.3). |
| 4 | Power-Zeile, Regel U | BESTAETIGT (Zahlen, Code = Erstfassung 1.8); ABWEICHUNG (B-4) | MDE80 W1/W2, MDE80*, m*, Uebergabeschwellen exakt; Regel U am Rand (x_P = c_v uebergeben, c_v - 1e-9 nicht), stets C10; A3-Praxis am Rand GL012 (Etikett "zugelassen nur durch DEC-94" zu erwarten). (1c) fehlt in Power-Zeile und Endpower; Endpower-Tabelle mit Replikat-p korrigiert. Lesart A (point) in YAML, Erstfassung und Entwurf etikettiert; B nicht registriert. OC Abschnitt 5.5. |
| 5 | p-Konvention DEC-99 N1 | Umsetzung BESTAETIGT; ABWEICHUNG Null-Modell (B-2) | R = 10.000, Zelle mit groesserem Null-Mittel (mom: drifting, rev_gap: driftfrei, wie erwartet), erste 1.000 Replikate reproduzieren Zellen-Mittel/-SD/-q95 und den Draw-Hash; Max-p W1/W2; sha in YAML; Block-Permutation und Normalnaeherung report-only (Schema-Pin); BH Nenner 4 fest; F-WEEK m = getestete, Doppelausweis 11. Inhaltlich: B-2 (Querschnitts-Abhaengigkeit, Zentrierung rev_gap). |
| 6 | Siegel und Sperren | BESTAETIGT bis auf **ABWEICHUNG Pilot-Sperre (B-3)** | Schnitt + Maximaldatum-Waechter (zweifach), Sonntag-/Grenz-Pruefung vor dem Laden; Pilot-Schnitt 2024-06-30 aus `seal`; Startsperre vor jedem Panel-Byte; Stress-Listen sofort nach dem Parsen auf <= Stichtag gefiltert (Test); `refuse_unsafe_path` weist die drei Siegelmuster ab (Test); kein roher IC, kein Lag-Profil, kein Beta-Kalibrierungs-IC im Paket (`not_computed`); P6-Null-Nachrechnung und K-Pins laufen vor jedem realen IC. Genau-ein-Pilot: nur je `--out`-Verzeichnis wirksam. |
| 7 | Ergebnisblindheit C.17 | BESTAETIGT, Liste ergaenzen (B-9) | Gesehen heute: Zaehlungen/Listen (DEC-100 N1), Gleichheit von Tagesschluessen als Zaehlung, v6-Nuisance (Streuung, Autokorrelation inkl. rho_f der Pilotperiode, Faktoranteil, Null-Mittel/-Quantile, K), HF-RV-Nuisance (Marktebene), A2-Kalender. Nichts davon ist ein realer Charakteristik-gegen-Outcome-Wert. Die Permutations-Kontamination aus DEC-99 N1 stammt aus dem synthetischen Fixture (`run_sig`), nicht aus Realdaten; kein `--pilot`/`--run` auf Realdaten auffindbar. |
| 8 | Registry/YAML gegen Erstfassung 10/11 | ABWEICHUNG (B-1, B-4, B-5, B-9) | Pflichtfelder vollstaendig; YAML = Erstfassung 11 plus DEC-99-N1-fdr und `fweek_counting`; Positivkontroll-Block woertlich Erstfassung 4/11 (Seeds, Kriterien 1,10/0,734/0,086/0,10); `rules.bounce_spread` 0,003621 = D10 36,21 bp des Spread-Zensus (sha `fa1546be...`); EV-2..EV-8 und Abweichungen 1-14 im DEC-101-Entwurf; Etikett "zugelassen nur durch DEC-99" vorhanden. Fehlend: Universumsdefinition (B-1), Baum-Pin (B-5), korrekte Endpower (B-4). |
| 9 | Tests, code_sha256 | BESTAETIGT | `tests/unit/test_h32_{cli,core,delisted_tree,modes}.py` + `test_power_p1.py`: **196 passed** (175 s, HEAD `ebd2591`). code_sha256 im Artefakt `3e249b01...` = `code_fingerprint()` auf HEAD; letzter Code-Commit `9364993` (13:14 UTC) vor dem v6-Start (13:28 UTC). Die Vorlage validiert gegen `schema.validate_registered`. |

---

## 4. Befunde

### B-1 (HOCH, VETO; Pruefpunkte 1, 8) Universum: USDC-Perps und datierte Futures als Zwillinge, asymmetrische Delisted-Seite

**Beleg (nur Metadaten).**
- Ueberlebenden-Manifest (`panel_1d`, 878 Symbole): 116 Nicht-USDT-Perps, davon **68 USDC-Perps** (`BTCPERP`, `ETHPERP`,
  `1000PEPEPERP`, ... - alle 68 mit einem USDT-Perp gleichen Basiswerts) und **48 datierte USDT-Futures**
  (`BTCUSDT-25SEP26`, `-25DEC26`, `-26MAR27`, ...); 42 der Futures beginnen erst nach dem Schnitt, **6 (BTC/ETH)** haben
  Daten davor (ab ~2025-10, ~2026-01, ~2026-04). USDC-Perp-Zeilen je Jahr / Tage: 2022 ~3, 2023 ~7, 2024 ~18, 2025 ~41,
  2026 (bis 09-14) ~65 Symbole je Tag.
- Kein Code-Pfad filtert sie (`load_panel_symbols` = alle Manifest-Symbole; `weekly`, `make_window`, `nullsim` ohne
  Klassenfilter). Die 226 im Schnitt entfernten Symbole sind genau 184 USDT-Perps + 42 Futures mit Start nach
  2026-06-28; die 68 USDC-Perps und 6 Futures bleiben in den 956.
- K-Gegenprobe gegen die Zaehlung des Orchestrators (BEFUND 5, Union = Strom, "lineare USDT-Perps lebend"): K_fm8
  2025-07-07 **537** gegen 530 lebende USDT-Perps (2025-07-01), 2025-11-03 **560** gegen 557, 2023-01-02 186 gegen 181 -
  obwohl K nur Symbole mit >= 8 Wochen Historie zaehlt. Am 2026-06-26 fuehrte der Ueberlebenden-Baum 652 Symbole mit
  Daten (BEFUND 3), die Union 599 lebende USDT-Perps einschliesslich spaeter Delisteter: mindestens 53, geschaetzt ~70
  Nicht-USDT-Kontrakte (~11 %).
- Delisted-Baum v2: Selektion `category linear, quoteCoin USDT, status Closed` (Baum-Fingerprint). Das Register hat
  **17 delistete USDC-Perps** (`linear`, `Closed`, `*PERP`): 13 mit Listung 2022-08..10 und letztem Handelstag
  2023-03-21..2023-04-04 (ADA, APE, APT, ATOM, AVAX, CHZ, EOS, GMT, LDO, LUNA2, NEAR, SAND, SWEAT - im Pilotfenster),
  MATICPERP (2022-09..2024-09-06, lebte in P und W1), TONPERP (2024-05..2026-06-15, W1 und W2), AI16ZPERP und IPPERP
  (2025-07..2025-11-06 bzw. 2026-06-26, W2). Keiner davon ist in einem
  der Baeume; die ueberlebenden USDC-Perps sind es. Abgelaufene datierte Futures fehlen ebenso.

**Wirkung.**
- Die faktorerhaltende Null simuliert je Spalte ein unabhaengiges e (`nulls.simulate_factor_panel`); Zwillinge haben in
  Charakteristik und Outcome fast identische Raenge (gleiches Beta -> gleiches fm8-Residuum). Synthetisch
  (`rr_twins.py`, K 570 mit 58 Paaren + 2 Viererbuendeln wie W2; K 440 mit 25 Paaren wie W1): Wochen-IC-SD relativ zur
  zwillingsfreien Spalte **x1,13 (W2)**, **x1,055 (W1)**, x1,04 (P-artig).
- Das Gate: (1b) nutzt die SE der realen Serie und skaliert mit; (1c) und das bindende p (DEC-99 N1) kommen aus der zu
  engen Null. Fenstergroesse (1b)+(1c), Normalnaeherung (`rr_size_twins.py`): W2 mom1 4,9 -> **7,0 %**, mom2 4,4 ->
  **6,6 %**, mom4 4,3 -> **6,4 %**; W1 (x1,05) 4,1..4,9 -> 4,9..5,8 %. Replikat-p bei x1,13: P(p <= 0,05 | H0) 7,3 %,
  P(p <= 0,012) 2,3 % (BY m = 4), P(p <= 0,003) 0,75 % (m = 11).
- floor_fm8, v_fm8 und K sind um die Zwillinge zu gross gezaehlt (Boden ~5 % zu klein in W2); SE_W,Pilot misst F2_real im
  Pilot, wo der Zwillingsanteil klein ist - die W2-Streuung unterschaetzt auch Regel U.
- Der Pilot hat eine Klassen-Ueberlebensverzerrung (13 USDC-Zwillinge mit Ende 2023-03/04 und MATICPERP fehlen, 3..7 sind drin) - als
  Zwillinge oekonomisch klein, aber genau der Typ Luecke, den DEC-100 schliessen wollte.

**Richtung:** Testbarkeit (Null zu eng, Power zu guenstig). **Etikett:** keines; Registry, DEC-101-Entwurf und
DEC-100 N1 nennen "Panel vollstaendig" ohne Einschraenkung. PRD 4.1 definiert das Universum als
`instruments-info?category=linear` (enthaelt USDC-Perps und Futures) - die Aufnahme ist also nicht regelwidrig, aber die
Delisted-Seite folgt einer anderen Definition, und die Null passt nicht zu Zwillingen.

### B-2 (HOCH; Pruefpunkt 5) Null-Modell traegt das Niveau allein; Querschnitts-Abhaengigkeit und rev_gap-Zentrierung

- (1b) lautet `y >= z_krit * SE_W` ohne Abzug des Null-Mittels (`gate.window_conditions`); das mechanische Null-Mittel
  geht nur ueber q95 (1c) ein. Unter dem v6-Null-Modell haette (1b) allein die Groesse 6,1 % (W1 mom1), 6,4 %, 7,6 %;
  W2 7,3 %, 9,3 %, **10,5 %** (mom4); (1c) bringt alle mom-Zellen auf 4,1..4,9 %. In W2 mom2/mom4 liegt dazu
  E[SE-Regel] unter der SD des Fenstermittels (0,938 / 0,916; W1 mom4 0,991) - der Bootstrap mit Block 4 erfasst die
  Autokorrelation ueberlappender Formationsfenster bei W = 50 nicht voll. Das Niveau der mom-Zellen haengt damit
  vollstaendig an der Ein-Faktor-Null.
- Jede reale Querschnitts-Abhaengigkeit ueber F2_null hinaus (Zwillinge, B-1; Sektoren - die PRD-Sektorwelt hob die
  Wochen-SD um +18 %, Review H-32 B-9) macht q95 und das Replikat-p zu eng. Die Block-Permutation (Erstfassung 1.10)
  haette die Querschnittsstruktur einer Woche erhalten; der Wechsel nach DEC-99 N1 tauscht eine Kontamination
  (Null-Mittel) gegen eine andere (Null-Streuung). "Keine neue Lockerung" (DEC-99 N1) gilt fuer die Lage, nicht fuer die
  Streuung.
- rev_gap: Die bindende Zelle ist um ein **negatives** Null-Mittel zentriert (W1 -0,0008, W2 -0,0011, in Richtung).
  Gate und Regel U geben fuer negative Null-Mittel keine Gutschrift (`max(0, null_mean)`), das p tut es implizit; fuer
  rev_gap ist "stress" (rho_f verdoppelt) gerade die Kalibrierung mit dem guenstigsten Null-Mittel.
- Richtung: Testbarkeit. Groesse: Abschnitt B-1; fuer Sektoren UNBELEGT (F2_real wird erst im Pilot gemessen).

### B-3 (HOCH; Pruefpunkt 6) Genau-ein-Pilot-Sperre nur je Ausgabeverzeichnis

`checks.check_rerun_lock` sperrt, wenn das `--out`-Verzeichnis `h32_pilot*` enthaelt ODER die YAML ein
`pilot_window.pilot_result_sha256` traegt. Die YAML wird mit `null` registriert und ist danach sha-gesperrt - der zweite
Zweig kann fuer h32_v1 nie greifen. Ein zweiter Pilotlauf in ein neues Verzeichnis laeuft technisch durch (der Test
`test_t3_exactly_one_pilot_lock...` prueft genau diesen Fall nicht). DEC-99 (3) und Erstfassung PP0' verlangen
"verweigert einen zweiten Lauf ohne DEC-Verweis". Richtung: Testbarkeit (Pilot-Shopping nur durch Prozessdisziplin
verhindert).

### B-4 (MITTEL; Pruefpunkt 4) Power-Zeile ohne (1c); Endpower-Tabelle zu guenstig fuer mom

- q95 liegt in 5 von 8 Zellen ueber `z_krit * e_se_rule + max(0, null_mean)`: W1 mom2 +0,00034, mom4 +0,00061; W2 mom1
  +0,00002, mom2 +0,00120, mom4 +0,00184. MDE80 der Bedingung (1c) (= q95 + 0,8416 * se_mean): W1 0,01853 / **0,02129** /
  **0,02568** / 0,01612; W2 **0,01717** / **0,02037** / **0,02426** / 0,01399. DEC-94 (3) verlangt MDE80 = max ueber die
  Bedingungen. Regel U deckt das bei den v6-Konstanten nur ueber m_P > null_mean_W: Marge c_v - max(Gate-MDE80) = mom1
  0,0011, mom2 0,0016, mom4 0,0018, rev_gap 0 ((1b) bindet). Kein Zuordnungsfehler, aber die ausgewiesenen
  Fensterpowers (W2 mom4 0,924) gelten fuer (1b); fuer (1c) 0,889 (W2) bzw. 0,850 (W1 mom4).
- Endpower nach F-WEEK: Der Entwurf (und `estimators.end_power`) rechnet die BY-Schwelle als `z_eff * e_se_rule +
  max(0, null_mean)`. Bindend ist aber das Replikat-p (Quantil der bindenden Zelle); die mom-Replikate sind rechtsschief
  (Quantil 1 - 0,003 bei 3,1..3,7 SD statt 2,75). Korrigiert (Gate inkl. (1c) und Replikat-Quantil, an der
  Uebergabeschwelle): Tabelle 5.4. Zu guenstig: mom1 m >= 3, mom2/mom4 fuer alle m (m = 1 0,752/0,756 statt 0,786/0,799);
  zu unguenstig: rev_gap (negatives Null-Mittel).
- Nebenbefund Orchestrator-Skript: `Z80 = 0.8416` statt `power_p1.Z_POWER` -> rev_gap-W1-Power an der Schwelle 0,79999;
  der Code nutzt den exakten Wert (0,80000, C10).

### B-5 (MITTEL; Pruefpunkte 1, 8) Baum-Hash nicht gepinnt

Registry-Block und Abweichung 13 nennen `delisted_tree_sha256` einen "neuen Pflicht-Pin"; die Vorlage enthaelt nur
union_range, delisting_dates, delisting_register. `checks.check_data_fingerprints` prueft den Baum-Hash nur, wenn die
YAML ihn traegt - nachgewiesen: ein abweichender Baum-Hash passiert die Pruefung mit der Vorlage, mit eingetragenem Pin
nicht. Praktisch deckt union_range die Partitionsdateien beider Baeume; die Aussage im Entwurf stimmt aber nicht.

### B-6 (MITTEL; Pruefpunkt 3) Monte-Carlo-Genauigkeit der q95 aus 1.000 Replikaten

Ueberschreitungsquote des eingefrorenen q95 in den unabhaengigen Replikaten 1.001..10.000 der bindenden Zelle:
W1 mom1 5,2 %, **mom2 5,6 %, mom4 5,6 %**, rev_gap 5,4 %; W2 mom1 4,7 %, mom2 4,3 %, mom4 4,6 %, **rev_gap 5,9 %**. In
W1 mom2/mom4 bindet (1c) - das Niveau liegt dort schon im eigenen Null-Modell bei ~5,6 %. Das 10.000er-Quantil ist
vorhanden (p-Replikate), ergebnisfrei und strenger: W1 0,01276/0,01520/0,01844/0,01035, W2 rev_gap 0,00900.

### B-7 (MITTEL; Pruefpunkt 1) Ersatz der W1-Determinismus-Kontrolle

Ehrlich als Abweichung 11 begruendet (Panel geaendert); der YAML-Kopf sagt nur "nicht angefordert". Fehlerraten-seitig
ausreichend: Fixture-T2 N = 3 (Null-Zelle, Vorlauf-Report, Pilot, Lauf, Positivkontrolle), Baum-Zweitbau bitgleich,
K_fm8-Pins (PP3/P4) und P6-Null-Nachrechnung (+-10 %) laufen vor jedem realen IC - ein Fehler endet als KEIN VERDIKT.
Betrieblich nicht ausreichend: ein Realdaten-Nichtdeterminismus oder ein Unterschied der P-K-Reihe zwischen Schnitt
2026-06-28 (v6) und 2024-06-30 (Pilot) zeigte sich erst nach der Registrierung (PP3) oder nach dem verbrauchten Pilot
(P6). Beides ist ergebnisfrei vorab pruefbar.

### B-8 (NIEDRIG; Pruefpunkt 4) Operationscharakteristik der Regel U

Analytisch mit v6 (x_P ~ N(Lage, se_mean_P^2), se_mean_P 0,0065..0,0081, Pilot-Quelle bindet nicht): P(Uebergabe) bei
Lage = m_P (mechanische Null) mom1 **0,32 %**, mom2 0,32 %, mom4 0,20 %, rev_gap 0,14 %; bei Lage = 0 mom 0,03..0,11 %,
rev_gap **0,45 %** (m* = 0, keine Gutschrift fuer m_P < 0). "<= 0,3 %" haelt naeherungsweise; Familie (4 Varianten)
<= ~1 %. Fehluebergaben aendern die Testfehlerrate nicht (getrennte Daten), nur m in F-WEEK. t_P an der Schwelle
2,6..3,4 -> (iii) redundant (wie Review H-32).

### B-9 (NIEDRIG; Pruefpunkte 2, 7, 8) Errata und Etiketten

1. Abweichung 11 "W1 ... 5 Symbole mehr": W1 gewinnt alle frueher fehlenden Symbole, die in W1 lebten (auch die 31
   W2-Delistungen) plus Datumskonvention - K W1 +15 / +21,5 / +22 (min/Median/max).
2. C.17 ergaenzen: (a) die v6-Null-Mittel W1/W2/P sind **richtungstragend** (modellbasiert, fuer mom positiv = mit der
   Richtung, fuer rev_gap negativ); (b) der Gleichheitsvergleich der Tagesschluesse (BEFUND 3) umfasste Tage bis
   2026-09-14, also nach dem Siegel - nur Zaehlung, kein Wert; (c) rho_f, sigma_f, Faktoranteil und Querschnittsstreuung
   der Pilotperiode sind neu gesehen (zulaessig nach DEC-94 (5) (i)).
3. YAML-Kopf: "W1-Determinismus-Kontrolle gegen v5e: nicht angefordert" -> "entfaellt (DEC-100 N1), Ersatz ...".
4. Erwartbares Etikett: Jede Uebergabe unter der A3-Praxis-MDE80 auf x_P (mom1 0,0250, mom2 0,0277, mom4 0,0329,
   rev_gap 0,0240; mit Gutschrift) traegt mechanisch "zugelassen nur durch DEC-94 (Lockerung)"; an der Schwelle trifft
   es alle vier Varianten. Der Entwurf weist A3-Praxis 0,0239/0,0240 ohne Gutschrift aus.
5. `estimators.mu_sel` liefert knapp ueber der Schwelle die Klammergrenze x_P - 40 SE_P (an c_v + 1e-4: -0,2415) - ein
   Platzhalter, keine Loesung; im Pilotbericht kennzeichnen (report-only).
6. Runner-Parameter festhalten, die den union_range-Fingerprint bestimmen: `--as-of 2026-09-28 --start-year 2021
   --end-year 2026 --allow-partial` (Defaults `as_of` = heute wuerden einen Fingerprint-Abbruch ausloesen - sicher, aber
   vermeidbar).
7. F-WEEK-Doppelausweis polstert auf m = 11 auf; mit weiteren getesteten Hypothesen der Welle waere die alte Zaehlung
   7 + 4 + Welle (report-only, `fweek.apply_fweek`).
8. Registry: K-Mediane 440,5 / 589,5; P-Start 2022-04-18 ist fest (DEC-99), nicht aus der K-117-Regel auf dem neuen
   Panel neu abgeleitet - so etikettieren.

---

## 5. Nachrechnung (eigenes Skript mit `power_p1`, `handover`, v6-Konstanten; keine Datenrechnung)

### 5.1 Artefakt und Vorlage

| Groesse | v6 / Entwurf | eigener Wert | Abweichung |
|---|---|---|---|
| result_sha256 (kanonisch, ohne `code`) | 2ae9bad6...dd6fa0 | 2ae9bad6...dd6fa0 | 0 |
| sha256 h32_prelaunch.json / Vorlage / p-Replikate | 96edd5ea / bddfb9cb / f10250dd | identisch; Vorlage per `--emit-template` neu erzeugt: bddfb9cb (bitgleich) | 0 |
| code_sha256 | 3e249b01... | HEAD 3e249b01... | 0 |
| YAML-Frozen gegen JSON (W1/W2 alle Felder, Kalibrierung, null_scales, bounce, m_P, K-sha) | - | 0 Abweichungen | 0 |
| frozen = max(driftfrei, Drift) je Feld; ceiling = driftfrei | - | 40/40 bitgleich; ceiling W1 0,0076016, W2 0,0069755 | 0 |
| bindende Zelle; erste 1.000 Replikate | drifting (mom), driftfree (rev_gap) | erwartet identisch; Mittel/SD/q95/Draw-Hash = Zelle | 0 |
| floor_fm8 / v_fm8 P, W1, W2 | 0,068771/0,004804; 0,047441/0,002258; 0,041552/0,001727 | aus K-Reihen bitgleich | 0 |
| K min/Median/max | 127/213/353; 360/440/536; 537/590/603 | 127/213/353; 360/440,5/536; 537/589,5/603 | Rundung |
| m_P | 0,002176 / 0,003274 / 0,004296 / -0,002540 | = max der P-Zellen, bitgleich | 0 |

### 5.2 Schwellen und Decke

| Fenster | Variante | T_W,v Entwurf | eigener T | q95 | Gate-Schwelle max(T, q95) bei SE = e_se_rule | Decke/T |
|---|---|---:|---:|---:|---:|---:|
| W1 | mom1 | 0,01303 | 0,013026 | 0,012655 | 0,013026 | 0,584 |
| W1 | mom2 | 0,01445 | 0,014451 | 0,014786 | **0,014786** | 0,526 |
| W1 | mom4 | 0,01715 | 0,017153 | 0,017766 | **0,017766** | 0,443 |
| W1 | rev_gap | 0,01190 | 0,011900 | 0,010149 | 0,011900 | 0,639 |
| W2 | mom1 | 0,01177 | 0,011774 | 0,011792 | **0,011792** | 0,592 |
| W2 | mom2 | 0,01298 | 0,012978 | 0,014182 | **0,014182** | 0,537 |
| W2 | mom4 | 0,01517 | 0,015167 | 0,017004 | **0,017004** | 0,460 |
| W2 | rev_gap | 0,01048 | 0,010484 | 0,008571 | 0,010484 | 0,665 |

### 5.3 Plausibilitaet gegen v5e (Erstfassung 1.6)

se_mean W1 -10..-14 % (v6 rechnet 52 statt 45 Simulationswochen: sqrt(45/52) = -7 %; mehr Symbole), W2 -4..+3 %;
null_mean W1 mom1 +27 %, mom2/mom4 ~0, rev_gap -0,00114 -> -0,00080; W2 mom x2,2..2,4 (Neukalibrierung auf dem
geschnittenen Fenster, stress rho_f 0,1404), rev_gap -0,00046 -> -0,00111. Uebergabeschwellen -3,0 / -3,5 / -4,1 / -8,4 %
gegen die Vorabwerte 0,0206/0,0237/0,0287/0,0195 - Richtung und Groesse plausibel; die Erhoehung der W2-Null-Mittel
wirkt fuer mom streng, fuer das rev_gap-p locker (B-2).

### 5.4 Power-Zeile und Endpower (an der Uebergabeschwelle x_P = c_v)

| Variante | MDE80 W1 | MDE80 W2 | MDE80* | m* | c_v Entwurf | c_v eigen | Gate-MDE80 inkl. (1c) W1 / W2 | Endpower Entwurf m = 1/2/3/4/11 | Endpower korrigiert (Gate + Replikat-p) |
|---|---:|---:|---:|---:|---:|---:|---|---|---|
| mom1 | 0,017801 | 0,015913 | 0,017801 | 0,002176 | 0,01998 | 0,019977 | 0,01890 / 0,01717 | 0,757 / 0,680 / 0,560 / 0,479 / 0,252 | 0,756 / 0,673 / 0,523 / **0,429** / **0,143** |
| mom2 | 0,019606 | 0,017544 | 0,019606 | 0,003274 | 0,02288 | 0,022880 | 0,02129 / 0,02037 | 0,786 / 0,716 / 0,605 / 0,528 / 0,300 | **0,752** / 0,649 / 0,488 / **0,382** / **0,079** |
| mom4 | 0,023227 | 0,020251 | 0,023227 | 0,004296 | 0,02752 | 0,027524 | 0,02568 / 0,02426 | 0,799 / 0,735 / 0,631 / 0,558 / 0,335 | **0,756** / 0,638 / 0,469 / **0,341** / **0,061** |
| rev_gap | 0,017874 | 0,015907 | 0,017874 | 0 | 0,01787 | 0,017874 | 0,01787 / 0,01591 | 0,699 / 0,617 / 0,493 / 0,414 / 0,203 | 0,699 / 0,699 / 0,602 / 0,531 / 0,340 |

- Entwurfsmethode bitgleich reproduziert (auch `orch_check/h32_v6_power.json`); die Abweichung ist methodisch (B-4).
- Regel U im Code am Rand: x_P = c_v -> uebergeben, Regime C10, Fensterpowers mom1 0,840/0,900, mom2 0,862/0,911, mom4
  0,865/0,924, rev_gap 0,800/0,874; A3-Praxis GL012 fuer alle vier; x_P = c_v - 1e-9 -> GL-012 (Pilot).
- A3-Praxis-MDE80 W1 ohne Gutschrift 0,02390 / 0,02631 / 0,03107 / 0,02396 (Entwurf 0,0239 / - / - / 0,0240), mit
  Gutschrift auf x_P 0,02500 / 0,02766 / 0,03290 / 0,02396.

### 5.5 OC, Groesse, Genauigkeit

| Groesse | Wert |
|---|---|
| P(Uebergabe), Lage m_P | mom1 0,32 %, mom2 0,32 %, mom4 0,20 %, rev_gap 0,14 % |
| P(Uebergabe), Lage 0 | mom1 0,11 %, mom2 0,07 %, mom4 0,03 %, rev_gap 0,45 % |
| Groesse (1b)+(1c) im v6-Null-Modell | W1 4,9 / 4,1 / 4,5 / 3,7 %; W2 4,9 / 4,4 / 4,3 / 3,6 % |
| dto. bei realer Null-SD x1,05 (W1) / x1,13 (W2) | W1 5,8 / 4,9 / 5,3 / 3,7 %; W2 7,0 / 6,6 / 6,4 / 3,8 % |
| E[SE-Regel] / se_mean | W1 1,038 / 1,032 / 0,991 / 1,019; W2 1,003 / **0,938** / **0,916** / 0,989 |
| Ueberschreitung des q95 in Replikaten 1.001..10.000 | W1 5,2 / 5,6 / 5,6 / 5,4 %; W2 4,7 / 4,3 / 4,6 / 5,9 % |
| Zwillings-Faktor der Wochen-IC-SD (synthetisch) | W2-artig 1,13, W1-artig 1,055, P-artig 1,04 |

(Reihenfolge je Zeile mom1 / mom2 / mom4 / rev_gap.)

---

## 6. Auflagen VOR der Registrierung (V-1 traegt das VETO)

- **V-1 (B-1) Universum per DEC-101 festlegen, mit Zahlen und Etikett, vor jeder Pilot-Zahl** - eine von:
  - **(a) empfohlen:** Universum = lineare USDT-Perpetuals (symmetrisch zur Selektion des Delisted-Baums: `quoteCoin USDT`,
    kein datierter Kontrakt). Additiver Filter im Treiber (eine Funktion + Test; Fingerprints bleiben dateibasiert),
    v6 neu (2 h, outcome-frei) **zweimal mit bitgleichem result_sha256**, neue Vorlage, neue Kernzahlen. Etikett
    "Bereinigung (Strenge), beschlossen nach Kenntnis der v6-Nuisance, vor jeder Pilot-Zahl".
  - **(b)** Universum bleibt `category=linear` der Ueberlebenden: dann Pflicht-Etikett (Zwillinge, asymmetrische
    Delisted-Seite, Groessenordnung aus B-1) **und** A-1 als registrierte Regel.
- **A-1 (B-2, bei V-1 (b) Pflicht, bei (a) dringend empfohlen):** im Testlauf je Fenster W und Variante
  `k = max(1, SD(IC_t,W) / sd_week_W,v)` (reale Wochen-SD gegen die eingefrorene Null-Wochen-SD) und
  `q95_eff = max(0, m) + k * (q95 - m)`, `p` aus `max(0, m) + k * (d - m)` (d Replikate, m Null-Mittel der bindenden
  Zelle); damit keine Gutschrift fuer negative Null-Mittel (rev_gap) und Querschnitts-Abhaengigkeit ueber F2_null hinaus
  im Niveau. Mechanisch, vorab, Richtung Strenge; YAML-Felder, Code, Test (T0/T4). Alternative: DEC mit ausdruecklichem
  Etikett "q95/p aus der Ein-Faktor-Null, Richtung Testbarkeit" und der Groessenordnung.
- **A-2 (B-3):** Genau-ein-Pilot technisch: Ausgabepfad des Pilots in der YAML pinnen (z. B.
  `pilot_window.out_dir: scinance3-impl/state/runs/h32_pilot_v1`) und jedes andere `--out` verweigern, oder vor dem Lauf
  alle `state/runs/**/h32_pilot*.json` mit gleichem `registered_sha256` suchen; Test fuer "neues Verzeichnis".
- **A-3 (B-5):** `data_fingerprints.delisted_tree_sha256: 250a923b...e401` in die YAML (Schema erlaubt es; dann prueft der
  Code ihn).
- **A-4 (B-4, B-6):** Registry/DEC-101: Fenster-MDE80 als Maximum ueber (1b)+Gutschrift und (1c) ausweisen; Satz "Regel U
  deckt (1c) bei den v6-Konstanten ueber m_P (Marge >= 0,0011; rev_gap (1b) bindend)"; Endpower-Tabelle durch die
  korrigierte ersetzen (oder beide mit Methode); empfohlen (Strenge, ergebnisfrei): q95 je Zelle =
  max(q95_1.000, Quantil der 10.000 p-Replikate).
- **A-5 (B-7, B-9):** v6 zweimal bitgleich (bei V-1 (a) ohnehin); PP3-Trockenprobe ohne IC (Panel <= 2024-06-30
  schneiden, Wochenarrays, K_fm8-Hash von P gegen die YAML); Errata 1-8 aus B-9 in Entwurf, DEC-101 und YAML-Kopf.

Aufhebung des VETO: V-1 entschieden und umgesetzt, A-1 (bei (b)) bzw. Entscheidung zu A-1 (bei (a)), A-2, A-3 in der
YAML; danach Nachpruefung der Pruefpunkte 1-5 auf dem neuen Artefakt durch den Gate-Auditor. A-4/A-5 kann der
Orchestrator selbst abnehmen.

## 7. Was NICHT folgt

- Kein Urteil ueber H-32 oder eine Variante, keine Aussage ueber Vorzeichen oder Groesse eines Effekts; Pilot, W1 und W2
  bleiben blind.
- Kein Fehler in der v6-Arithmetik, im Code von Regel U, Gate, Schnitt, Startsperre oder Siegelwaechtern; die Zahlen des
  Entwurfs sind als Rechnung korrekt.
- DEC-99 und DEC-100 bleiben als Regeln unberuehrt; B-1 korrigiert nur deren Tatsachenbasis ("vollstaendig" gilt fuer
  USDT-Perps). B-2 stellt die p-Konvention nicht in Frage, sondern ihre Streuungsannahme.
- GL-032..034 und die A3-Akte werden nicht neu bewertet; dass derselbe Ueberlebenden-Baum dort verwendet wurde, ist ein
  Erratum-Etikett, kein Grund fuer eine Neuberechnung.
- Die Synthetik in B-1 beziffert die Groessenordnung (perfekte Zwillinge); die reale Wirkung misst erst der neue Vorlauf
  bzw. der Pilot (F2_real).

## 8. Reproduktion (`scratchpad/h32_reg_review/`, ausserhalb des Repos)

| Skript | Inhalt | Laufzeit |
|---|---|---|
| `rr_check.py` | Hashes, result_sha256, YAML gegen JSON, floor/v, Zellen-Maxima, bindende Zellen, T, Decke, MDE80, m*, c_v, Regel U am Rand, Endpower (Entwurf / korrigiert), OC, Groesse -> `rr_check.json` | < 5 s |
| `rr_twins.py` | Zwillings-Faktor der Wochen-IC-SD (synthetisch), p-Inflation | ~4 min |
| `rr_size_twins.py` | Fenstergroesse (1b)+(1c) bei realer Null-SD x r | < 1 s |
| `rr_q95_mc.py` | Ueberschreitung des eingefrorenen q95 in den 10.000 p-Replikaten | < 1 s |
| `h32_v1_reemit.yaml` | `scripts/h32_fm8.py --emit-template` aus dem v6-JSON (bitgleich zur Vorlage) | < 1 s |
| `tests_h32.log` | `pytest` test_h32_* + test_power_p1: 196 passed | 175 s |
