# SPEC Zone-X-Programm 1: IK-05 (RMT-Faktorzahl) und IK-04 (Momente fuer die Nullwelt) auf dem Tages-Panel - Bauauftrag 2026-11-02

Rolle: Bau nach Spezifikation (Code + Tests mit synthetischen Fixtures). **Kein Datenzugriff in diesem Auftrag** (der
Datendienst ist nicht erreichbar; der Orchestrator fuehrt den Lauf spaeter nach Konto-Eintrag aus). Nichts committen.

## Zweck (PRD_ANALYSE Nachtrag 1, Sweep IK-04/IK-05; DEC-104 E4 (c) Zone X mit Konto)

Zwei Messungen zweiter Momente auf Zone X (lineare USDT-Perps, `rest.kline1d` ALL, **2021-01-01..2024-06-30**, nichts
spaeter), ohne Mittelwerte oder Vorzeichen von Renditen auszugeben:
1. **IK-05:** Hat die residuale Korrelationsmatrix der Tagesrenditen (nach Marktfaktor) Eigenwerte oberhalb der
   Marchenko-Pastur-Kante (1 + sqrt(K/T))^2, und wie viele? Entscheidet, ob eine Faktorstruktur die 2,5-fache
   IC-Streuung der Klasse W erklaeren kann (Eigenwert >= 6,25 noetig) oder ob sie aus Zeitvariation kommt.
2. **IK-04:** Momente fuer die minimale Nullwelt: Kurtosis und Schiefe der Tagesrenditen und der Marktresiduen (Verteilung
   ueber Symbole: Quantile), Querschnittsstreuung sigma_xs je Tag (Verteilung ueber Tage: Median, q10, q90; Autokorrelation
   Lag 1..5), Vol-Clustering (Autokorrelation von |r|), effektive Clusterzahl eines 365-Tage-Fensters (aus der
   Autokorrelation der Tagesstatistik), Anteil fehlender Tage je Symbol.

## Ort und Form

- `src/bybit_edge/research/zone_x/__init__.py`, `common.py` (Lader, Zonen-Waechter, Ausgabe-Schema), `ik05_rmt.py`,
  `ik04_moments.py`, `run_zone_x_1.py` (CLI: `--out <json>`, `--start 2021-01-01 --end 2024-06-30`, `--min-days 250`).
- Tests `tests/unit/test_zone_x_1.py` (pytest, ohne Netz, ohne Daten): synthetisches Panel mit k = 0 / 1 / 3 Faktoren ->
  erkannte Faktorzahl; MP-Kante gegen Formel; Kurtosis-Schaetzer auf t(4)-Stichprobe (Erwartung Exzess-Kurtosis ~6,
  Toleranz); Zonen-Waechter wirft bei einem Tag > 2024-06-30 und bei Start < 2021-01-01; Ausgabe enthaelt kein Feld
  mit Mittelwert/Vorzeichen (Schema-Test); Determinismus (zwei Laeufe bitgleich auf dem Fixture).
- Code und Kommentare Englisch, ASCII, keine Hostnamen, keine Modellnamen, keine Zugangsdaten. Datenzugriff nur ueber
  den bestehenden Lader-Pfad des Repos: pruefe, wie `src/bybit_edge/research/h32_fm8/` das Tages-Panel laedt (Harvest-Client
  `harvest_data` ueber `sys.path`/Konfiguration, `hd.load("rest.kline1d", ...)`, Spalten `close`, `turnover`/`volume`), und
  **benutze denselben Weg**; der Client selbst gehoert nicht ins Repo. Fehlende Tage nie interpolieren; Symbole mit
  weniger als `--min-days` Tagen ausschliessen und zaehlen.

## Rechenweg

- Renditen r_i,t = ln(C_t / C_{t-1}) je Symbol (nur fuer interne Rechnung; nie ausgeben). Marktfaktor r_M,t =
  gleichgewichtetes Mittel ueber die am Tag vorhandenen Symbole (nicht ausgeben). Residuen e_i,t = r_i,t - beta_i r_M,t
  (beta_i ueber das ganze Fenster, nicht ausgeben).
- IK-05: Korrelationsmatrix der Residuen auf dem groessten vollstaendig besetzten Teilpanel (Symbole mit >= 90 % der
  Tage; fehlende Tage paarweise ausschliessen oder Teilpanel balancieren - Wahl dokumentieren); Eigenwerte absteigend;
  MP-Kante (1 + sqrt(K/T))^2 mit K Symbole, T Tage; Ausgabe: K, T, Top-20-Eigenwerte, Kante, Anzahl Eigenwerte > Kante,
  Anteil erklaerter Varianz der Eigenwerte > Kante, dasselbe fuer die Roh-Renditen (ohne Marktfaktor) zum Vergleich;
  Robustheit: dasselbe fuer drei Teilfenster (2021-01..2022-02, 2022-03..2023-04, 2023-05..2024-06) und fuer
  Rang-Korrelationen (Spearman).
- IK-04: je Symbol Exzess-Kurtosis und Schiefe von r und e (Ausgabe nur Quantile q10/q25/q50/q75/q90 ueber Symbole,
  getrennt nach Umsatz-Terzil); sigma_xs,t = Querschnitts-SD der r_i,t je Tag (Ausgabe Quantile ueber Tage, Mittel
  ueber Tage als Niveau ist erlaubt, da Streuung); ACF(1..5) von sigma_xs,t und von |r_M,t| (Betrag erlaubt, Vorzeichen
  nicht); effektive Clusterzahl n_eff = n / (1 + 2 sum rho_k) fuer n = 365 aus der ACF einer Tagesstatistik ohne
  Vorzeichen (|r_M|); Anteil fehlender Tage.
- **Verbotene Ausgaben (Waechter + Schema-Test):** jedes Mittel oder Vorzeichen von r, e, r_M; jede Zeitreihe von
  Renditen; symbolweise Niveaus ausser Varianz/Kurtosis/Schiefe-Quantilen; keine Tageslisten mit Werten. Keine
  geschachtelten Klassen-Streuungen mit Zaehlungen (DEC-103 N1 (2c)); der Orchestrator laesst `scinance3-impl/tools/channel_scan.py`
  ueber die Ausgabe laufen.
- Ausgabe-JSON mit `zone: "X"`, `window`, `code_sha256` (des Moduls), `inputs` (Stream, Symbole-Zaehlung, Tage), DEC-105-
  Berichtsfelder, soweit sinnvoll (`n_eff`, `c_overlap` = 1 fuer Tagesrenditen ohne Ueberlappung).

## Konto-Entwurf (fuer den Orchestrator, nicht eintragen)

Schreibe nach `<scratchpad>/zonex/KONTO_ENTWURF.md`
die zwei Konto-Zeilen (Familie "Nullwelt/Nuisance Klasse W", Statistik exakt, Fenster, K = 1, Zweck S1) im Format von
`scinance3-impl/state/KONTO_ZONE_X.md`.

## Lieferung

Code unter `<scratchpad>/zonex/stage/` mit
Repo-relativen Pfaden (src/..., tests/...), `pytest` auf dem Stage lauffaehig (gib den Befehl an), Kurzfassung <= 10
Zeilen mit Testergebnis und offenen Punkten. Harte Regeln: nichts im Repo aendern, nichts committen, keine Marktdaten
laden, keine Siegeldatei oeffnen, Test-Suite-Baseline nie reduzieren.
