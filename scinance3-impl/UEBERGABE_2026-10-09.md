# Scinance 3.0 - Uebergabe an die naechste Sitzung (Stand 2026-10-09)

> Zweck: Eine neue Orchestrator-Sitzung kann hier ohne Vorwissen weiterarbeiten.
> Lesereihenfolge: (1) diese Datei, (2) `scinance3-impl/CLAUDE.md` (Verfassung),
> (3) `scinance3-impl/state/decisions.md` ab DEC-73, (4) `scinance3-impl/state/hypothesis_registry.md`
> (Zweitfassung H-28..H-30 und beide Rueckzuege), (5) `scinance3-impl/state/WELLE1_GESAMTBILANZ_2026-09-21.md`.
> Arbeitsbranch: `claude/subagent-prd-development-T16fE` (ist auch der Default-Branch des Repos).

---

## 1. Rollen, Regeln, Nutzer-Auflagen (bindend)

- **Orchestrator** entscheidet, schreibt Registrierungen, Gate-Urteile, DEC-Eintraege. Bau-Arbeit an Sonnet-Builder (Hintergrund-Agenten), Registrierungs-Reviews an einen Opus-Reviewer (adversarisch). Abnahme immer selbst: Tests laufen lassen, Zahlen nachrechnen, erst dann committen.
- **Autonomie:** Nutzer nie fragen ausser bei Zugriffsrechten, Geldausgaben, destruktiven Aktionen. Kein Live-Order-Code. Oeffentliche Bybit/Deribit-Endpunkte erlaubt, keine Keys fuer Boersen, keine privaten Endpunkte. Nie unter `data/harvest` schreiben.
- **Registry-Disziplin:** Vorab-Registrierung, append-only, keine Schwellenbewegung in irgendeine Richtung; Aenderung = neuer Eintrag (Rueckzug + Neufassung). Null-Zensus-Klausel (DEC-58): ein Zensus promotet nie einen Kandidaten.
- **Siegel:** Die reale Signal-gegen-Folgerendite-IC der A3-Kohorte ist bis zum registrierten Lauf versiegelt. Nie oeffnen: `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`, `*_L_window_sealed.json` (alle unter `state/runs/`).
- **Commits:** kleine Commits, nie force-push, nie History umschreiben. Trailer laut System-Hinweis der Sitzung. Keine Modellnamen in Repo-Artefakten.
- **Nutzer-Auflage 2026-09-23:** Nie mehr "fuehre erst das, dann das aus, dann hochladen". Laeufe gehen ueber den Autopiloten (Abschnitt 3); ein Handbefehl ist hoechstens ein einziger.
- **Oeffentliches Repo** (GitHub `private: false`): niemals Zugangsdaten, niemals den Hostnamen des Heim-Datendienstes ins Repo, in Commits, Logs oder Notebooks.

## 2. Wo die Daten sind

| Quelle | Inhalt | Zugriff |
|---|---|---|
| Nutzer-PC `E:\Claude\Projects\scinance` | `data/panel_1d` (877 Ueberlebende, Tageskerzen + Funding, 2021-2026), `data/panel_1d_delisted` (261 delistete Symbole, WP-12b), `data/barcache` (WP-0), `data/dvol_rest`, `data/l2tilt` (fillshadow-Store), `data/harvest` (Spiegel des Harvest-Archivs, nur lesen) | nur ueber den Autopiloten |
| **Data-Harvest-Archiv** (S3-kompatibel, nur lesend, ~1,4 TB, 312.000 Partitionen) | Bybit/Deribit/Binance/BitMEX/OKX: Trades, L2-Orderbuch (BTC/ETH, ab 2026-06), Ticker inkl. Options-IV/Greeks, Funding, OI, Liquidationen, DVOL | aus der Cloud-Sitzung, sobald die Umgebungs-Secrets gesetzt sind (Abschnitt 4) |
| Bybit-REST (oeffentlich) | Klines/Funding/Instruments aller Perps | Cloud-Sitzung: **gesperrt** (Proxy 403), bis `api.bybit.com` in der Netzwerk-Allowlist steht; PC: frei |

## 3. Autopilot (DEC-79) - wie Laeufe ohne Nutzer passieren

- Geplante Aufgabe "Scinance Autopilot" auf dem Nutzer-PC (Rechner `PC2022`), alle 15 min, `pythonw.exe scinance3-impl/handoff_local/autopilot.py`. **Installiert und nachweislich funktionsfaehig** (Auftrag `2026-09-26_wp13a_v5b` am 2026-09-28 selbst gestartet, Ergebnis gepusht).
- **Auftrag erteilen:** `scinance3-impl/state/queue/auftrag.json` mit NEUER `id` schreiben, committen, pushen. Schema in `state/queue/README.md`; erlaubte Aufgaben: `wp13a`, `wp10b`, `wp7`, `wp10a2`, `wp12`, `wp13run` (braucht `registered` + `registered_sha256`), `diag`. Optional `skip_if_done_since: <commit>`.
- **Rueckmeldung:** `state/queue/gestartet/<id>.json` beim Start, `state/queue/erledigt/<id>.json` am Ende; Ergebnisordner unter `state/runs/<wp>_<datum>/` (Dateien > 5 MB bleiben auf dem PC); Protokoll `state/runs/nacht_<stamp>.log`; Commit-Betreff `results(nacht <stamp>): <task> rc=<n> ... [auftrag <id>]`.
- **Selbst wecken:** nach dem Push einen Weckruf in diese Sitzung legen (Routine `send_later`, Fertigzeit + Puffer); beim Wecken `git pull`, Marker lesen, weiter. Laufzeiten: `wp13a` 1,5-4 h, `wp10b` 6-8 h, `wp7` Minuten.
- Handstart bleibt moeglich: `nacht.ps1 -Tasks a,b` (Sperrdatei verhindert Parallellaeufe).

## 4. Data-Harvest-Zugang aus der Cloud-Sitzung (neu seit 2026-10-07)

- Der Nutzer hat ein Briefing mit nur-lesendem Schluessel geliefert. **Die Werte nie aus dem Chat oder einer Datei uebernehmen** - die Sicherheitspruefung hat das am 2026-10-07 zu Recht blockiert. Erwartet werden Umgebungs-Secrets: `HARVEST_S3_ENDPOINT`, `HARVEST_S3_ACCESS_KEY`, `HARVEST_S3_SECRET_KEY`. Pruefen mit `env | grep -c '^HARVEST_S3_'` (soll 3 sein). Empfehlung an den Nutzer war: Schluessel neu ausstellen lassen (der alte stand im Chat-Upload).
- Netz: der Harvest-Host war am 2026-10-07 aus der Sandbox erreichbar (S3 antwortet 400 ohne Signatur); `api.bybit.com` war gesperrt.
- Client: `harvest_data.py` vom Server holen (Bucket `harvest`, Schluessel `catalog/client/harvest_data.py` und `catalog/client/DATA_ACCESS.md`, ueber `pyarrow.fs.S3FileSystem` mit `endpoint_override` aus der Umgebung, `region="us-east-1"`, `force_virtual_addressing=False`, `proxy_options=$HTTPS_PROXY`). Nicht ins Repo committen ohne Pruefung; `pip install pyarrow polars`; **kein** DuckDB-httpfs (Erweiterungs-Host gesperrt).
- Regeln (Data-Harvest): nie den Bucket listen/globben, nur `hd.catalog()`; Bandbreite ~2 MB/s, geteilt; `columns=` nutzen; Luecken (`hd.gaps`) benennen, nie fuellen; Thin Client rechnet nicht. Bekannte Besonderheiten: 2026-08-13 alle Bybit-Live-Stroeme exakt doppelt (Client dedupliziert), 2026-08-14 Ausfalltag, `bybit/orderbook` fehlt 06-26, 07-06..07-16, 08-01; ETH-Optionen 08-22..08-27 ohne Frames.
- **Was dadurch in der Cloud rechenbar wird:** alles mit kleinem Datenvolumen (Trades je Symbol-Tag 10-40 MB, Ticker/Options-IV, Funding, OI, DVOL, Liquidationen). **Nicht** sinnvoll in der Cloud: Orderbuch-Grosslaeufe (WP-10B ~59 GB) -> Autopilot. **WP-13 braucht `panel_1d`** (Tageskerzen ~1.140 Perps), das nicht im Harvest-Archiv liegt -> entweder `api.bybit.com` freigeben und das Panel in der Cloud bauen (`scripts/wp7_universe_census.py --fetch`, `scripts/wp12_delisting.py --fetch-delisted-panel`; Bybit-Geosperre der Cloud-Region pruefen) oder weiter per Autopilot.
- Fuer die Verfassung vorgesehener Abschnitt (ohne Hostname, ohne Schluessel): Anhang Abschnitt 7 des Briefings; in `scinance3-impl/CLAUDE.md` unter "Marktdaten (Data-Harvest)" uebernommen.

## 5. Programmstand

**Welle 1 abgeschlossen** (DEC-73, Gesamtbilanz). Kernergebnisse:
- WP-7 (+Union mit Delistungen): Klasse W testbar (B2). Rauschboden E_t[1/sqrt(K_t-1)] W1 0,0486 / W2 0,0419; K je Woche 345-606 in den Urteilsfenstern; Survivorship-Verzerrung des Momentum-IC +0,003 [-0,008; +0,013]; Delisting-Hazard 2023/24-Kohorten ~50 %.
- WP-9: DVOL-REST = Harvester exakt; H-27 (VRP) eroeffnet, nicht registriert.
- WP-10(A2): Funding-Kohaerenz im Stress 0,6-0,7 vs. Ruhe 0,2-0,35 (nicht selektionsbedingt).
- WP-10(B) Schema 4 (massgeblich, `state/runs/wp10b_20260924`): p_fill(60 s) FIFO 0,056-0,065 / pro-rata 0,32-0,37; adverse Selektion 0,6-0,8 bp FIFO -> Maker-Vorteil traegt in Ruhe; Stress-Zelle leer.
- WP-11 v2: Nach-Schock-Halbwertszeit 22-31 h (Potenzgesetz).
- Kalibrierung (DEC-78): BTC-Wochenautokorrelation 0,046 / 0,042; Faktoranteil der Querschnitts-Dispersion (Median R^2 auf 26-W-PIT-Beta) 1,6 % / 0,7 %; mechanisches Beta-Momentum analytisch ~0,0005 (vernachlaessigbar).

**Registrierung A3-Kohorte F-XSEC1 (H-28 Momentum, H-29 Reversal Gap, H-30 Vol-Anomalie):** Erstfassung (DEC-74) und Zweitfassung (DEC-75) zurueckgezogen. Drittfassung ist **noch nicht geschrieben**; ihr Inhalt ist durch DEC-75 (Cluster-SE, faktorerhaltende Null, Beta-Kontrolle, H-30 eindeutig, PRD-Kills zurueck), DEC-76 (Rollen der Nullen), DEC-77/78 (Beta-Kontroll-Methode per Simulation kalibriert) bindend festgelegt. Der Lauf-Modus `scripts/wp13_xsec.py --run` existiert und ist gesperrt: er startet nur mit Registrierungs-YAML + passendem sha256 (`--emit-registered-template` erzeugt das Geruest aus dem Vorlauf-Artefakt; `beta_control.method` muss der Orchestrator fuellen).

**A1** (Funding-Long-Bein gegen Universums-Hedge, DEC-70): Konstruktion fest, Registrierung wartet auf die erweiterte V-1 (Umschalt-/Rueckwechselregel 4h/8h an der Primaerquelle, DEC-58 E3) - Orchestrator-Recherche. **A2** gesperrt (V-5b/c), **A4** recording-first, **A5** gesperrt.

## 6. Offene Arbeit, nach Prioritaet

1. **Vorlauf v5 (WP-13a) scheitert an der Gegenprobe** - zweimal identisch (2026-09-25 und 2026-09-28, nach dem Fix `38af605`): Kalibrierung `zero` (rho_f 0), simulierter Faktoranteil 0,0212 gegen Ziel 0,0162 (+30 %), beta_sd 0,2474. Da rho_f gemessen nur 0,046 ist, sind `measured` und `zero` fast gleich parametriert; die Suche (n_reps 40, Toleranz 10 %) akzeptiert, die unabhaengige Gegenprobe (n_reps 30, Toleranz 25 %) verwirft. Diagnose-Hypothese: Stichprobenstreuung des Median-R^2-Schaetzers ist groesser als die Toleranzen (Builder-Hinweis), kein Wiederverwendungsfehler. **Vorschlag fuer die naechste DEC:** Streuung des Schaetzers je Kalibrierung messen (SD ueber Replikate) und Suche wie Gegenprobe auf "Ziel innerhalb 3 Standardfehler" umstellen, n_reps beider auf >= 100; Gegenprobe bleibt laut. Danach `wp13a` per Autopilot neu (Code: `src/bybit_edge/research/wp13_xsec/nulls.py`, `calibrate_beta_sd_to_observed_share`, `factor_share_gegenprobe`, `beta_control_method_study`; Log: `state/runs/nacht_20260928_1339.log`).
2. **Drittfassung H-28..H-30** schreiben (nach erfolgreichem Vorlauf v5: gewaehlte Beta-Kontroll-Methode, eingefrorene Konstanten, vollstaendiger Gate-Text (1)-(7), T0-T7), Opus-Review, Registrierungs-YAML + sha256, dann Auftrag `wp13run` an den Autopiloten.
3. **Data-Harvest in der Cloud nutzen**, sobald Secrets gesetzt: Client holen, Verbindungstest, `hd.catalog()`; pruefen, ob `api.bybit.com` freigegeben ist (sonst Nutzer einmal bitten).
4. **Erweiterte V-1** recherchieren -> A1-Registrierung vorbereiten.
5. Folgearbeiten ohne Eile: Bar-Cache-Tag 2026-08-13 mit DISTINCT-Lesung neu (Volumen/Trade-Zahl sonst ~2x; DEC-76 Nachtrag 2); Registrar: watchdog-Auszuege fuer 2026-06-26 und 2026-08-01 (07-06..07-16 und 08-14 sind geklaert); `characteristics.beta_characteristic` vektorisieren (dominiert die Vorlauf-Laufzeit).

## 7. Datei-Landkarte

- Verfassung `scinance3-impl/CLAUDE.md`; PRD `scinance3-impl/PRD_SCINANCE3.md`; Entscheidungen `state/decisions.md` (DEC-51..79); Registry `state/hypothesis_registry.md`; Gate-Log `state/gate_log.md` (noch leer); Befunde `state/WELLE1_*`; Reviews `state/REVIEW_H28_H30_v1.md`, `_v2.md`.
- Laeufe `state/runs/<wp>_<datum>/`; Stress-Kanon `state/runs/stress_rel.json`, `stress_abs.json`.
- Code: `src/bybit_edge/research/wp7_universe` (Zensus, Panel, Union), `wp9_dvol`, `wp10_coherence`, `wp10_fillshadow` (Replay, Schema 4), `wp11_relax`, `wp12_delisting` (Register, delistetes Panel), `wp13_xsec` (A3: characteristics, ic, nulls, prelaunch, run, gates). Skripte unter `scripts/`. Tests `tests/unit/test_wp*.py`, `test_autopilot.py`.
- Runner/Autopilot: `scinance3-impl/handoff_local/` (`nacht.ps1`, `autopilot.py`, `install_autopilot.ps1`, `run_*.ps1`, Diagnose-Skripte).

## 8. Fallen, die schon Zeit gekostet haben

- PowerShell 5.1: verschachtelte Anfuehrungszeichen in `python -c` brechen -> immer Skriptdateien; `-Tasks a,b` ueber `-File` kommt als ein String an (in `nacht.ps1` gesplittet); Runner nur ASCII.
- Sandbox-Python verliert nach Container-Wechsel Pakete: `pip install` der Abhaengigkeiten aus `pyproject.toml` ohne `filterpy` (baut nicht), dann `pip install --no-deps -e .`, plus `pytest pyarrow pyyaml`.
- Ein Builder meldet "fertig", aber Zahlen im echten Lauf weichen ab -> jede Simulations-Kalibrierung gegen die gemessene Groesse mit demselben Schaetzer gegenpruefen (DEC-78).
- Registry-Fehler der Vergangenheit: Schwelle aus fensterfremdem Messfenster, Rauschboden als "Messung" einer Identitaet, nie bindende Gates, stillschweigend entfallene Kill-Bedingungen - jede Neufassung gegen beide Reviews pruefen.

---

## 9. Nachtrag (zweite Sitzung 2026-10-09) - was sich geaendert hat

- **Vorlauf v5 repariert (DEC-81):** Ursache war die Stichprobenstreuung des Median-R^2-Schaetzers (~8,5 % bei 30-40 Replikaten) zusammen mit einer Bisektion auf frischen Zufallszahlen je Iteration. Jetzt: Suche mit gemeinsamen Zufallszahlen (400 Replikate, 1 % Praezision, nicht konvergiert = laut), Gegenprobe unabhaengig (400 Replikate, `z <= 3` UND `3*se_diff <= 0,25*Ziel`), Simulation ueber den realen Querschnitt je Woche, `beta_characteristic` bitgleich ~36x schneller. Kontrolllauf mit echten W1/W2-Groessen: alle sechs Gegenproben bestanden (z <= 0,82, Power-Auslastung <= 0,78). Auftrag `2026-10-09_wp13a_v5c` an den Autopiloten.
- **Data-Harvest in der Cloud: funktioniert** (Secrets gesetzt, Client gelesen und genutzt, Katalog 319.063 Partitionen). Client-Datei liegt NICHT im Repo; jede Sitzung holt sie neu (Abschnitt 4). Bybit-Stroeme im Archiv nur BNB/BTC/ETH/SOL/XRP.
- **`api.bybit.com` aus der Cloud: Geosperre von Bybit selbst** (CloudFront, US-Region), nicht die Allowlist. `panel_1d` bleibt dauerhaft Autopilot-Sache; den Nutzer dafuer nicht um Freigaben bitten.
- **Erweiterte V-1 (DEC-82):** Recherche in `state/V1_ERWEITERT_RECHERCHE_2026-10-09.md`. Naechster Schritt: empirische Gegenprobe auf `panel_1d` (Modalwert von `funding_sum/funding_n` je Intervallklasse = skaliertes I; Intervallwechsel je Symbol aus `funding_n`) als eigener Autopilot-Auftrag nach v5c.
- **Branches:** Die Cloud-Sitzung bekommt je Sitzung einen eigenen Branch zugewiesen; der Autopilot liest NUR `claude/subagent-prd-development-T16fE`. Deshalb jeden Commit auf beide pushen (`git push origin HEAD:claude/subagent-prd-development-T16fE`, nur Fast-Forward, nie force).
- **Testbaseline dieser Sandbox:** 3 Legacy-Fehler in `tests/unit/test_execution_live.py` (caplog/Root-Rechte, auch vor DEC-81) - kein WP-13-Bezug.
