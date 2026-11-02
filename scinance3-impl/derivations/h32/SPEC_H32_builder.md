# Builder-Auftrag H-32 (DEC-99): Zweistufen-Treiber fuer den beta-neutralen Querschnitts-IC - Vorlauf v6, Pilot, Test, Positivkontrolle

Repo Scinance, Paket `bybit_edge` unter `src/`. Eigener git-worktree. Tests IMMER mit
`PYTHONPATH=$(pwd)/src python -m pytest ...` aus der Worktree-Wurzel (einmal pruefen:
`PYTHONPATH=$(pwd)/src python -c "import bybit_edge;print(bybit_edge.__file__)"` zeigt in den Worktree).

## Verbindliche Texte (in dieser Reihenfolge lesen; bei Widerspruch gilt die frueher genannte Quelle)
1. `scinance3-impl/state/decisions.md`: **DEC-99** (Pilot-Schaetzfenster, Panel-Waechter, genau ein Pilotlauf, Doppelausweis,
   F-WEEK-Zaehlregel (7), W2-Ende 2026-06-28), DEC-94 (P-1: kritischer Wert, SE-Regel (4), Zuordnung (6), Selektionsdecke (7)),
   DEC-96 E3 (Blind-Siegel ab 2026-07-01), DEC-85/87/89 (Null, Kalibrierung je Fenster, Positivkontrolle), DEC-53 (Artefakte).
2. `scinance3-impl/state/herleitung_h32/ERSTFASSUNG_H32_entwurf.md` (Stand nach Auflagen): Abschnitt 1 (Festlegungen:
   Fenster P/W1/W2, Statistik, Beta-Kontrolle, Null, eingefrorene Groessen, Uebergaberegel U, Power-Zeile), 2 (Gate-Text
   woertlich), 4 (Positivkontroll-Regel woertlich), 5 (DEC-39-Trio, Testpflichten T0-T7), 11 (YAML-Schema
   `state/registered/h32_v1.yaml` mit neuen Feldern), 12 (Bauliste B-1..B-6).
3. `scinance3-impl/state/herleitung_h32/REVIEW_H32.md` Befunde B-4 (Injektion auf realisierten Effekt), B-6 (harter
   Panel-Schnitt, W2-Neukalibrierung, Stress-Datumsfilter), B-7 (E[SE-Regel] einfrieren), B-8 (m_P aus Pilot-Kalibrierung,
   Regel max(0, m_P, m_W1, m_W2)), B-9 (sigma_g an F2_real, PRD-Sektorwelt report-only), B-15 (vorzeichenbereinigte Decke).
4. Vorbild-Code: `src/bybit_edge/research/wp13_xsec/` (prelaunch.py, run.py, gates.py, ic.py, nulls.py, characteristics.py,
   positive_control.py), `src/bybit_edge/research/power_p1.py`, `scripts/wp13_xsec.py`, Tests `tests/unit/test_wp13_*.py`,
   `tests/unit/test_power_p1.py`, Fixture-Panels der CLI-E2E-Tests.

## Harte Regeln
- Nicht committen, nicht pushen. NIE Dateien oeffnen, die `*_L_window_sealed.json`, `weekly_ic_series.csv` oder
  `ic_series_*_UNION_REAL.csv` heissen. Nie unter `data/harvest` schreiben. KEIN `--prelaunch`, `--pilot`, `--run` oder
  `--positive-control` auf Realdaten (das faehrt der Orchestrator) - nur Fixture-Panels.
- **Additiv:** neues Paket `src/bybit_edge/research/h32_fm8/` und CLI `scripts/h32_fm8.py`; `wp13_xsec/` und `wp7_universe/`
  NICHT aendern (Code-Hash der A3-Registrierung), nur importieren. `power_p1.py` nur additiv, falls noetig.
- Code/Kommentare Englisch, Stil der Dateien, Docstrings mit "DEC-99". Keine Modellnamen. Bestehende Tests nie loeschen.
- Jede Zahl, die der Lauf gegen die YAML prueft, ist eingefroren (T5-Pin); keine Konstante ohne Quelle.

## Bau (je Punkt mit Tests; Details in Erstfassung Abschnitt 12 und den genannten Review-Befunden)
B-1 **Vorlauf v6** `--prelaunch` (outcome-frei): harter Panel-Schnitt VOR jeder Rechnung (`--cut-date`, Default
    2026-06-28; Waechter raised bei spaeteren Tagen, Test), Fenster P/W1/W2 nach Abschnitt 1.3; faktorerhaltende Null
    der Drittfassung mit 8 Beta-Vorlaufwochen, K = 4 Varianten (mom1, mom2, mom4, rev_gap), 1.000 Replikate, Seed 53,
    driftfrei und Drift 0,002; Kalibrierung je Fenster neu (W2 auf dem geschnittenen Fenster; Pilotperiode P nur
    Streuung/Autokorrelation/Faktoranteil mit Waechter "kein Mittel"); eingefroren je Fenster und Variante: sd_week,
    se_mean, **E[SE nach Regel P-1 (4)]** (Bootstrap der SE-Regel unter der Null), Null-Mittel m (stress, driftfrei/Drift,
    auch m_P), MDE80 nach DEC-94 (3) mit T = z_krit x E[SE_Regel], SD = se_mean; K_fm8-Reihen aus `returns_valid`;
    Stress-Abdeckung nur mit Datumsfilter <= cut-date; Template-Emitter fuer `h32_v1.yaml` (Abschnitt 11, inkl.
    `pilot_window`, `handover_rule`, `fweek_counting`, `alpha`/`z_krit`, p-Groesse/Permutationszahl, Fingerprints).
B-2 **Pilot-Modus** `--pilot`: Startsperre (`--registered <yaml> --registered-sha256`), Panel-Schnitt <= 2024-06-30
    (Waechter + Test), je Variante Mittel des fm8-IC, SE nach P-1 (4) (`power_p1.stationary_bootstrap_se`), t, 80-%-Band;
    Uebergaberegel U mechanisch (Vorzeichen; Punkt - max(0, m_P, m_W1, m_W2) >= 2,4865 x groesste Test-SE; t >= 2);
    selektionsbereinigter Schaetzer mu_sel (bedingt median-unverzerrt gegeben die Schwelle) als Pflicht-Doppelausweis;
    Zuordnung `power_p1.assign_regime` + `assign_regime_a3_practice` mit Pilot-Punkt UND mu_sel; DEC-53-Artefakte;
    `h32_pilot.json` + sha256; **Genau-ein-Pilot-Sperre:** existiert bereits ein Pilot-Artefakt im Ausgabeverzeichnis
    bzw. ein registriertes `pilot_result_sha256` in der YAML, wird ein zweiter Lauf laut abgewiesen (kein Force-Flag).
B-3 **Testlauf** `--run`: Pilot-Sperre (Pilot-Artefakt + sha256 Pflicht), nur uebergebene Varianten, Gate nach Abschnitt 2
    als reine Funktion ueber ein konserviertes Payload (T4), Schwelle = z_krit x SE_W (DEC-94 (1)), SE-Regel P-1 (4),
    Panel-Schnitt <= 2026-06-28, BH mit festem Nenner 4 (nicht uebergebene p = 1), Ueber-Familie F-WEEK nach DEC-99 (7)
    (nur getestete) UND Doppelausweis alte Zaehlung (m inkl. p = 1-Eintraege), Etiketten (Bounce, Liquiditaet,
    Survivorship) wie Drittfassung; keine Nebengroessen; Markdown + JSON.
B-4 **Positivkontrolle** `--positive-control` nach Abschnitt 4 mit B-4/B-9: Welt je Fenster (stress, Marktspalte =
    Faktor, 8 Sektorbloecke; sigma_g per Bisektion an F2_real kalibriert, Null-SD als Untergrenze; PRD-Sektorwelt
    report-only), Injektion auf den REALISIERTEN Effekt (Mittel positiv minus negativ der fm8-Statistik) kalibriert,
    Urteils-Seeds 53..252, Kriterien (a)-(d), rc 0/3/1.
B-5 **Vorzeichenbereinigte Selektionsdecke** als neue Funktion (nicht `nulls._mean_of_max` aendern), Test gegen Monte Carlo.
B-6 **Tests** nach Abschnitt 5: T0, T1-Trio (positiv realisiert, null, adversarial), T2 Determinismus N >= 3 mit
    Fingerprint, T3/T7 Artefakt-Round-Trip, T4 Gate-Arithmetik auf Payload, T5 Konstanten-Pin gegen YAML, T6 Legacy-Sperre;
    CLI-E2E auf einem Fixture-Panel: prelaunch -> template -> pilot (Fixture mit injiziertem Signal: Uebergabe; ohne:
    GL-012 Pilot) -> positive-control -> run; alle Waechter (Panel-Schnitt, Pilot-Sperre, Startsperre, Genau-ein-Pilot).

## Abnahme durch dich
- `PYTHONPATH=$(pwd)/src python -m pytest -q tests/unit/test_h32*.py tests/unit/test_wp13_xsec.py tests/unit/test_wp13_run.py tests/unit/test_power_p1.py`
  gruen; danach `tests/unit` gesamt (Zahlen; die 3 bekannten `test_execution_live.py`-Fehler nur melden).
- Ein vollstaendiger E2E-Durchlauf auf dem Fixture-Panel mit allen Artefakten.

## Rueckmeldung
Hoechstens 10 Zeilen: Dateien, Testzahlen, genaue CLI je Modus, Abweichungen von Erstfassung/Review mit Grund,
absoluter Worktree-Pfad. Bei Unklarheiten in Erstfassung oder Review: die strengere Lesart bauen und melden.

## Nachtrag (Stand der Erstfassung nach den Auflagen, bindend)
Die Bauliste in Erstfassung Abschnitt 12 ist massgeblich und enthaelt jetzt **B-0** (Panel-Schnitt mit Maximaldatum-
Waechter und T1-Test) sowie die geaenderten B-1..B-6 (v6: e_se_rule, W2-Neukalibrierung, W1-Determinismus-Kontrolle,
Pilotperioden-Kalibrierung, m_P; Pilot: Neulauf-Sperre, mu_sel, Regel (ii) mit max(0, m_P, m_W1, m_W2); Test: F-WEEK nach
DEC-99 (7) mit Doppelausweis m = 11, Max-p der Block-Permutation Block 4, 10.000 Permutationen, Seed 53, Endpower-
Ausweis; Positivkontrolle: Welt-SD aus F2_real, Injektionsziel mit e_se_rule, PRD-Sektorwelt report-only; Schema:
Bloecke `seal` und `fdr`, Felder e_se_rule, m_P). Wo dieser Auftrag und die Erstfassung abweichen, gilt die Erstfassung.
