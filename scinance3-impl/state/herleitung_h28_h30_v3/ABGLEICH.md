# Abgleich: Review v1/v2 und bindende Auflagen DEC-73..86 -> Fundstelle im Entwurf der Drittfassung

> Referenzen: `E` = `DRITTFASSUNG_H28_H30_entwurf.md` (Abschnittsnummern), `EV-x` = `ENTSCHEIDUNGSVORLAGEN.md`,
> `V1..V9` = Vorbedingungen (E Abschnitt 0), `K1..K11` = Kill-Bedingungen (E 7).
>
> Status-Schluessel:
>
> | Status | Bedeutung |
> |---|---|
> | **erfuellt** | im Entwurf umgesetzt, Zahl mit Fundstelle |
> | **offen-V** | adressiert, braucht aber eine Vorbedingung (Code, v5e oder Entscheidung) |
> | **entfaellt** | begruendet nicht anwendbar oder durch spaetere DEC ersetzt |
>
> ENTWURF, 2026-10-12. Keine Siegeldatei geoeffnet, keine reale IC gerechnet.

## 1. Review H-28..H-30 v1 (`state/REVIEW_H28_H30_v1.md`; bindend uebernommen in DEC-74 E2)

| Punkt | Fundstelle im Entwurf | Status |
|---|---|---|
| Zahlentabelle W1/W2 (Wochen, K, E_t[1/sqrt(K_t-1)], IC_min bei rho = 0) | E 1.3, 1.8 (a). Ersetzt durch v5d mit W_geurteilt 52/51 (DEC-75 (1)): Boden 0,04858/0,04192, K 345/419/514 und 514/589/603. Die v1-Werte 0,04849/0,04190 galten fuer 53/52 Wochen. | erfuellt |
| Identitaet sd_null = E_t[1/sqrt(K_t-1)] | E 1.8 (a): "exakte Permutationsvarianz, signal-agnostisch, blind fuer Korrelationsstruktur" | erfuellt |
| K-Zitate 412/538 gehoeren zum Lauf 2026-09-14 | E 1.3 zitiert nur die v5d-K-Reihen | erfuellt |
| `null_ic_*`-Hashes identisch (signal-agnostische Null, DEC-70 E4) - etikettieren | E 1.8 (a), Etikett "signal-agnostisch" | erfuellt |
| B4 rechnet mit 11 bp, das Etikett mit 18 bp (zwei Kostenbasen) | E 2 Zeile 2, E 1.10 Nr. 8 | erfuellt |
| DEC-59-Verweis fuer das Kostenkonstanten-Modul ist im Log anders belegt | E 2 Zeile 6 (Werkzeug-DEC ohne Nummer benannt) | erfuellt |
| Artefaktpfade im Report sind lokale Pfade | E nutzt durchgehend repo-relative Pfade (`state/runs/...`) | erfuellt |

## 2. Review H-28..H-30 v2 (`state/REVIEW_H28_H30_v2.md`; bindend uebernommen in DEC-75)

| Punkt | Fundstelle im Entwurf | Status |
|---|---|---|
| **B-1** Permutationsboden zu klein bei heterogenem Beta; SE = max(Boden, SD)/sqrt(W), Block-Bootstrap | E 1.9 (1b), (1c); `run.se_of_mean_ic`, `moving_block_bootstrap_ci` | erfuellt |
| **B-2** c_rho < 1 ist Schaetzerbias; Deckelung max(1, c_rho); bias-korrigiert | E 1.8 (a): c_rho_bk (+1/W je Lag), Deckelung als registrierte Abweichung; vol_beta 0,9891/0,9276 auf 1 gedeckelt | erfuellt |
| **B-3** Gate (2) Persistenz-Null bindet nie, also report-only | E 1.9 (2) | erfuellt |
| **B-4** Registry-IC_min != Artefakt | E 1.8 (a): registriert wird `ic_min_capped` = Artefaktwert | erfuellt |
| **B-5** H-30: target_vol^2/2 ist rangneutral; sigma_w^2/2 erzeugt das Vorzeichen mechanisch; Schaetzfehler | E 1.6, 8c; V3; EV-G. Der Code zieht sigma_w^2/2 weiterhin ab (verdoppelt den Drag), und die Tageseinheit unterschaetzt ~x7. Der Schaetzfehler ist quantifiziert (SE/Kante 0,025, Wocheneinheit ~0,18). | **offen-V (V3)** |
| **B-6** H-30-Gewicht muss PIT `vol_rv[t]` sein | E 1.6; `ic.vol_weighted_outcome_with_drag` (Test `test_vol_weighted_outcome_with_drag_uses_formation_week_vol_for_next_week_outcome`) | erfuellt |
| **B-7** PRD-Kills (3)/(4) wieder aufnehmen | (4) Bounce: E 1.9 (4b) "kein PASS", aber der Code vergibt nur ein Etikett (V4, EV-I). (3) Survivorship: Etikett nach DEC-76 (E 7). | **offen-V (V4)** |
| **B-8** Survivorship-Fixture (30 %, Drawdown, unkontrolliert vs. kontrolliert) | E 7 Etiketten: v5d W1 -0,20/-0,19, W2 -0,44/-0,58 IC_min-Einheiten (n 19/419, 46/589); Test `test_survivorship_drawdown_fixture_is_deterministic_and_reports_ic_min_units`. Die Konventionsdifferenz `drop` wird im Lauf berichtet (E 5 Nr. 3). | erfuellt |
| **B-9** Markt-Autokorrelation: residualisierter Outcome als PASS-Bedingung; adversariales Fixture mit driftendem, autokorreliertem Markt | E 1.7, 1.9 (3b), E 2 Zeile 5. Das Fixture existiert, laeuft aber noch mit TS-8w statt `fm_neutral_8w` (V7). | erfuellt (Regel) / **offen-V (V7, Test)** |
| **W-10** W = geurteilte Wochen 52/51; Decke auf n_weeks-1 | E 1.3; die Rausch-Decke in v5d nutzt die geurteilten Wochen | erfuellt |
| **W-11** analytische Decke W2 0,00806 | EV-C: methodengleich jetzt 0,00814 (Boden 0,04192, W 51; die 0,00806 galten fuer W 52), ohne Faktor 1/sqrt(2) | erfuellt |
| **W-12** Kill-Regel Decke: Schaetzer, Replikate, Fixture benennen | E 1.8 (c), K2: Mittel des Maximums, 7 Varianten, fm8, stress, driftfrei, 1.000 Rep., Seed 53 | erfuellt (W1-Wert offen-V1) |
| **W-13** BH kann nach Gate (1) nie verwerfen, also report-only oder Block-p | E 1.9 (3): BH report-only, Block-Permutations-p, BY bindend | erfuellt |
| **W-14** IC_prior 0,03 fuer rev_gap (Lag 2) unbelegt; DEC-52-Zuordnung offen etikettieren | E 8b `a_priori_ref` und Etikett; EV-B, EV-F: Power bei Prior 0,01 = 0,15/0,19, DEC-52 zulaessig, nicht genutzt | erfuellt |
| **W-15** AR(1)-Null-Lage = E[phi_hat] (Kendall-Bias), Bias-Korrektur | Die Persistenz-Null ist report-only (E 1.9 (2)); c_rho ist +1/W-korrigiert (E 1.8 (a)). Die phi-Fits sind nicht Kendall-korrigiert und wirken nur ueber c_rho (gering; laut Gate-Audit v5c durch keine DEC vorgeschrieben). Empfehlung: in v5e mitrechnen. | offen (gering) |
| **W-16** H-30-Persistenz-Null ist weisses Rauschen | E 1.10 Nr. 4 (Wochen-Proxies), report-only | erfuellt (Etikett) |
| **W-17** Randkonstruktion der Charakteristik pinnen | E 1.5: volles Panel, dann schneiden (DEC-75 (8)) | erfuellt |
| **W-18** Test-IDs fuer Boden/Quantil/Decke, volle Hashes, Siegel praezisieren | E 6 (Test-IDs; T5-Pin FEHLT), volle Hashes in Kopf, 4 und 8a; Siegel im Kopf | erfuellt / **offen-V (V7: T5)** |
| **W-19** Gate-Text (1)-(7) vollstaendig | E 1.9 | erfuellt |
| **W-20** T3/T4/T6 | E 6: T4 vorhanden, umzustellen; T3, T6 FEHLEN | **offen-V (V7)** |
| **W-21** Abweichungsliste | E 1.10 | erfuellt |
| Kosmetik: Symbol-Wochen 22.815/29.732 | E 1.3: v5d-geurteilt 22.300/29.126 [abg.: Summe k_series] | erfuellt |
| Kosmetik: Null-Mittel -0,0036..-0,0469 | E 1.8 (a) | erfuellt |
| Kosmetik: Power unter c_rho 1,13 = 0,98 | E 1.8 (d): Power des vollen Tests je Variante | erfuellt |
| Kosmetik: degenerierte Querschnitte -> IC 0,0 dokumentieren | E 1.4 | erfuellt |
| Kosmetik: sigma = 0-Symbole in der AR(1)-Null | E 1.8 (a): W1 550, W2 402 von 1.138 (nicht lebend) | erfuellt |
| Bestaetigt: Fenster 53/52, 11 Wochen ungeurteilt, K-Reihen, Boden, Delisting 80/140, NO_HISTORY, Gate (5) 0,159/0,142, Stress 22/8 und 2/1, Etikett 0,0101, Seed 53, close_at_last, K = 7, Familien | E 1.2, 1.3, 1.4, 1.8, 1.9 (5), 2, 4 | erfuellt |

## 3. Bindende Auflagen DEC-73 .. DEC-86

| DEC / Auflage | Fundstelle im Entwurf | Status |
|---|---|---|
| **DEC-73 E1:** A3 auf der Vereinigung, C.10 hart, K = 7 vorab, H-30 bedingt | E 1.1, 1.2, 1.8 (d); H-30 Sperre E 8c | erfuellt |
| **DEC-73 E4:** Etikett `unter_wand` (Einzelposition), kein Gate | E 2 Zeile 2 | erfuellt |
| **DEC-74 (a):** Schwelle je Fenster aus K-Reihe und W; Wochenliste und K-Reihe als Artefakt | E 1.8 (a); E 5 Nr. 6 | erfuellt |
| **DEC-74 (b):** c_rho aus der Persistenz-Null, nicht aus Funding, nicht aus der realen IC | E 1.8 (a) (mit Deckelung nach DEC-75 (8)) | erfuellt |
| **DEC-74 (c):** Persistenz-Null registriert (AR(1), 1.000 Sim., Seed 53) | E 1.8 (a) (v5d); im Lauf report-only nach DEC-75 (6) | erfuellt |
| **DEC-74 (d):** Alpha-Semantik 2,4865, Groesse 0,0064 / 4,1e-5, MDE = IC_min, Power getrennt | E 1.9 (1), 1.8 (d) | erfuellt |
| **DEC-74 (e):** FDR-Einheit Variante, K = 7 bleibt Nenner, Max-p, BH 0,10, BY F-WEEK, "vorlaeufig" | E 1.9 (3); EV-J (BH-Nenner fest 7, Code V7). ">= 10.000 Permutationen" ist ersetzt durch DEC-75 (2)/DEC-76 (d) (Block-Permutation >= 1.000, report-only). | erfuellt / **offen-V (V7)** |
| **DEC-74 (f):** Gate (4) Liquiditaet als Pflicht-Sensitivitaet mit Etikett | E 1.9 (4c); die Code-Richtung ist invertiert und prueft nur W1 (V4) | **offen-V (V4)** |
| **DEC-74 (g):** Gate (5) Erreichbarkeit ohne Outcome; strukturelle Verletzung = GL-012 | E 1.9 (5), K5; vol_rv belegt, vol_max/vol_beta UNBELEGT (V5) | **offen-V (V5)** |
| **DEC-74 (h):** H-30-Feasibility auf L; Nichtbestehen = GL-012 fuer H-30, K bleibt 7 | E 8c, K4; Einheit und Vorzeichen (V3) | **offen-V (V3)** |
| **DEC-74 (i):** close_at_last urteilstragend, drop als Sensitivitaet, Zaehlung, NO_HISTORY | E 1.4, 1.2 | erfuellt |
| **DEC-74 (j):** Ausrichtungs-, Lag-, Delisting- und schwellennahes Fixture; Positivkontrolle vorgeschaltet | E 3, E 6 T1 | erfuellt (Tests vorhanden) |
| **DEC-74 (k):** ein YAML-Block je Hypothese, `null_fixture`, numerische Pflichtfelder, volle Hashes, STRESS_REL im Repo, Stichdaten, 11 Wochen, L versiegelt, oekonomisches Etikett 0,0101/0,062 | E 8a-8c, E 4, E 1.3, Kopf. Stichdaten des Exports 2026-09-28: Union-Range- und delisting_dates-Hash UNBELEGT (V9). | erfuellt / **offen-V (V9)** |
| **DEC-74 Nachtrag:** STRESS_REL 22/8, STRESS_ABS 2/1; Announcement-Datum als Etikett; V-4(a) | E 4, E 1.2. V-4(a) betrifft A3 nicht. | erfuellt / entfaellt (V-4(a)) |
| **DEC-75 (1):** SE-Regel, W 52/51, Block-Bootstrap (Block 4, >= 1.000, Seed 53, Niveau 1 - 0,0064); IC_min nach dem Lauf nicht neu gesetzt | E 1.9 (1b)/(1c), Kopf (append-only, nichts nach dem Lesen aendern) | erfuellt |
| **DEC-75 (2):** Decke und Permutations-p auf faktorerhaltender Null, >= 1.000, Mittel des Maximums, Kill Decke >= IC_min | E 1.8 (c), 1.9 (P2), (2), K2; EV-A | erfuellt (W1-Wert offen-V1) |
| **DEC-75 (3):** Beta-Kontrolle als PASS, Kalibrierungs-IC der Beta-Charakteristik berichten, adversariales Fixture | E 1.9 (3b), E 2 Zeile 5, E 6 T1 (fm8-Umstellung V7) | erfuellt / **offen-V (V7)** |
| **DEC-75 (4):** H-30-Gewicht PIT, Drag vom ungewichteten Outcome, Feasibility ueber Roh-Spread und SE, Dezil-Tableau, Vorbehalt mit Zahl | E 1.6, 8c. Das Dezil-Tableau liegt im versiegelten L-Teil und wurde nicht gelesen; die offenen Verhaeltnisse 0,395/0,025 stehen im md. Einheit und Vorzeichen sind praezisierungsbeduerftig (EV-G). | **offen-V (V3)** |
| **DEC-75 (5):** Survivorship-Kill (>= 0,5 IC_min) und H-29-Bounce "Etikett Artefakt, KEIN PASS" | Bounce: E 1.9 (4b) (V4, Code). Survivorship: nach DEC-76 Etikett (E 7). | **offen-V (V4)** |
| **DEC-75 (6):** Gate (2) und (3) report-only, BY bleibt | E 1.9 (2), (3) | erfuellt |
| **DEC-75 (7):** vollstaendiger Gate-Text; T0-T7 mit T3, T4, T6 | E 1.9; E 6 (T3, T6, T7 FEHLEN) | **offen-V (V7)** |
| **DEC-75 (8):** Deckelung als Abweichung; rho_k +1/W; Decke W2; Kosmetik; Prior-Zeile je Variante; rev_gap-DEC-52-Feststellung VOR dem Lauf; Randkonstruktion; Feasibility offen; volle Hashes; Test-IDs | E 1.8 (a), 1.10 Nr. 3, EV-C, 1.8 (d), 8a-8c, EV-B/EV-F (Feststellung 0,15/0,19), E 1.5, 8c, E 6 | erfuellt |
| **DEC-75 E2:** Lauf-Modus mit Startsperre, sha256 in der Drittfassung | E 1.9 (P0), E 10; sha256 erst nach V1-V9 final | **offen-V** |
| **DEC-76 E1 (a):** roher IC mit SE-Regel, keine simulierte Faktor-SD in der Schwelle | E 1.9 (1) | erfuellt |
| **DEC-76 E1 (b):** IC_res >= IC_min UND jenseits des 99,36-%-Quantils unter der DRIFTENDEN Null | E 1.9 (3b-iii); der Code rechnet driftfrei (V8, EV-E) | **offen-V (V8)** |
| **DEC-76 E1 (c):** GL-012-Decke driftfrei, roh und residualisiert berichtet, Kill an der residualisierten | E 1.8 (c), EV-A ("residualisiert" = registrierte Beta-Kontrolle) | erfuellt (W1 offen-V1) |
| **DEC-76 E1 (d):** Block-Permutations-p, Max-p, report-only | E 1.9 (2) | erfuellt |
| **DEC-76 E1 (e):** sigma_e idiosynkratisch | E 1.7 (0,12064/0,10729) | erfuellt |
| **DEC-76 Survivorship-Befund:** Etikett statt Kill (Union-Panel) | E 7 Etiketten | erfuellt |
| **DEC-76 E3** (WP-10(B)) | betrifft A3 nicht | entfaellt |
| **DEC-77 E1 (a):** rho_f, sigma_f, Faktoranteil gemessen; Null kalibriert | E 1.7 | erfuellt |
| **DEC-77 E1 (b)/(c):** Methodenregel bei kalibriertem UND Stress-rho; registriert wird die bestehende Methode, keine Wahl nach Realdaten | E 1.1, 1.7; EV-A; V1/K11 (W1-1.000-Rep.-Bestaetigung fehlt) | erfuellt / **offen-V (V1)** |
| **DEC-77 E2:** `beta_control: {method, beta_window_weeks}` in der Registrierungsdatei | `registered_proposal.yaml` (`fm_neutral_8w`, 8); statisch geprueft | erfuellt |
| **DEC-78 E1 und Nachtrag:** beta_sd bisektionell kalibriert, stress = 2x rho_f und 2x Anteil, Lauf liest `beta_sd_calibrated` ohne Suche | E 1.7; YAML `windows.<W>.calibration` und `calibration`; je-Fenster-Lesen im Code fehlt (V2) | erfuellt (Werte) / **offen-V (V2)** |
| **DEC-78 E2:** Raster ohne TS-Residualisierung; Gewinner mit 1.000 Rep. | EV-A (TS nur historisch); W1-Gewinner fehlerhaft kalibriert (V1) | **offen-V (V1)** |
| **DEC-79:** Autopilot | Cloud-first (DEC-83); Autopilot nur Rueckfall | entfaellt |
| **DEC-80 E1:** Zugangsdaten nur aus Secrets, kein Hostname im Repo | E 1.2 (`HARVEST_S3_*`, kein Hostname) | erfuellt |
| **DEC-80 E2/E3** (v5-Befund, Uebergabe) | historisch, durch DEC-81/85/86 ueberholt | entfaellt |
| **DEC-81 E1 (a)-(d):** Suche mit gemeinsamen Zufallszahlen, Gegenprobe auf SE-Basis, realer Querschnitt, bitgleiches Beta | E 1.7 (Gegenprobe z, v5d) | erfuellt |
| **DEC-81 E3:** Harvest aus der Cloud, Bybit-REST geo-gesperrt | E 1.2 (Panel ueber den Export) | erfuellt |
| **DEC-82** (erweiterte V-1, A1) | betrifft A3 nicht | entfaellt |
| **DEC-83:** Cloud-first | E 10 | erfuellt |
| **DEC-84:** Panel ueber den Thin Client, exakte Schluessel, SHA256-Pruefung, nie im Repo | E 1.2 | erfuellt; V-1-Teil entfaellt (A1) |
| **DEC-85 E2 (i):** Marktspalte := Faktor | E 1.7 | erfuellt |
| **DEC-85 E2 (ii):** Gegenprobe prueft die Marktspalte (95-%-Band) | E 1.7 | erfuellt |
| **DEC-85 E2 (iii):** nicht handelnde Symbol-Wochen NaN fuer Schaetzungen | E 1.7 (`returns_est`); Persistenz-Null auf `returns_est` umstellen (E 1.8 (a), gering) | erfuellt / offen (gering) |
| **DEC-85 E2 (iv):** Regel, Schwellen, Stress, Raster, Seed und Replikate unveraendert | EV-A, E 1.7; keine Aenderung | erfuellt |
| **DEC-85 E2 (v):** v5d bindet in beide Richtungen | Kopf; EV-A (TS-Zeile nicht bindend, weil das v5d-Ergebnis sonst ausgehebelt wuerde); V1/K11 | erfuellt |
| **DEC-85 "ausdruecklich nicht":** keine Registrierung aus der Audit-Gegenrechnung, keine Teilkohorte, keine Schwellen-/Stress-Aenderung, kein Oeffnen versiegelter Dateien | K = 7 bleibt in allen Faellen. Vorab-GL-012 einzelner Varianten nur nach vorab bestehenden Regeln (DEC-74 (h), DEC-51 (2), C.4), nicht als Auswahl "sauberer" Varianten; der Review prueft das. Keine Siegeldatei geoeffnet. | erfuellt (Review-Hinweis) |
| **DEC-86 Entscheidung:** fm_neutral_8w, Beta-Fenster 8, v5d-Kalibrierungen je Fenster und Kalibrierung, kein Wechsel nach Realdaten | E 1.1, 1.7, YAML; der Code liest global (V2); die W1-Gewinnerzahlen in DEC-86 sind falsch kalibriert (V1, EV-A Punkt 5) | erfuellt (Wahl) / **offen-V (V1, V2)** |
| **DEC-86 offen (a):** bindende Decke | EV-A; E 1.8 (c) | erfuellt (Empfehlung) |
| **DEC-86 offen (b):** Gap eine Woche, Faktor 1/sqrt(2) | EV-B, EV-C; E 1.10 Nr. 1/2 | erfuellt (Empfehlung) |
| **DEC-86 offen (c):** Gate-Text, zwoelf Pflichtzeilen, T0-T7, YAML + sha256 | E 1.9, E 2, E 6; YAML-Vorschlag sha256 `df36f45e...`, final erst nach V1-V9 | erfuellt / **offen-V** |

## 4. PRD-Pflichtstellen (Kontrolle)

| PRD-Stelle | Fundstelle im Entwurf | Status |
|---|---|---|
| 3.3.1-3.3.12 (zwoelf Pflichtzeilen) | E 2 (Tabelle, je Zeile) | erfuellt |
| 3.4 YAML-Template-Felder | E 8a-8c (alle Felder; Verweis "wie H-28" bei identischem Inhalt) | erfuellt |
| 5.3 Gate-Text (1)-(7) | E 1.9 in geltender Fassung (DEC-75/76). Die PRD-Wortlaut-Abweichungen bei (2)/(3) (report-only) sind durch DEC-75 (6) gedeckt. | erfuellt |
| 5.3 Feasibility-Kills (1)-(5) | E 7 K1 (Kill 2), K4 (Kill 5 in der DEC-75-(4)-Form); Kill (3) als Etikett (DEC-76); Kill (4) als Gate (4b); Kill (1) B1 ist durch WP-7 B2 erledigt (DEC-73) | erfuellt |
| 5.3 DEC-39-Fixtures inkl. A3-R- und A3-V-spezifisch | E 3, E 6 T1; A3-V-Fixture FEHLT (V7) | **offen-V (V7)** |
| 5.3 Nicht-Wiederholungs-Nachweis | E 9 | erfuellt |
| 3.5 DEC-52-Regel | E 1.9 DEC-52-Zweig (bedingt, Code fehlt) | erfuellt (Text) |

## 5. Zusammenfassung offener Posten (Reihenfolge fuer den Orchestrator)

1. **Entscheidungen** (vor dem Bau): EV-A (Decke), EV-B (Gap), EV-C (1/sqrt(2)), EV-D (Kalibrierung je Fenster),
   EV-E (Drift), EV-F (Zuordnungsregel), EV-G (H-30-Drag), EV-H (vol_beta), EV-I (Gate-Code), EV-J (Verdikt je Hypothese).
2. **Bau mit Tests:**
   - V1 Defekt im Gewinnerlauf;
   - V2 Kalibrierung je Fenster und Emit der fm8-Zellen;
   - V3 Drag;
   - V4 Gate (4);
   - V5 Gate (5);
   - V7 DEC-53, T2/T3/T5/T6/T7, BH-Nenner, fm8-Fixtures.
3. **Vorlauf v5e**, outcome-frei, bindend nach DEC-85 (v):
   - W1-Gewinner mit 1.000 Rep.;
   - eingefrorene Konstanten je Fenster;
   - Drift-Quantil;
   - H-30-Feasibility in Wocheneinheiten;
   - Gate-(5)-Erreichbarkeit;
   - Persistenz-Null auf `returns_est`;
   - Daten-Fingerprints (V9).
4. **Zuordnung** je Variante mechanisch (E 1.8 (d)), finale YAML, sha256 in die Registrierung, adversarisches Review.
   Danach die Positivkontrolle allein und zuerst, dann der Lauf.
