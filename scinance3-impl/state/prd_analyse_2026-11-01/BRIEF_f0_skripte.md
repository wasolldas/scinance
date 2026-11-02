# Auftrag F0: Herleitungs-, Review- und Pruefskripte fuer das Repo vorbereiten (2026-11-02)

Rolle: Bau/Kartierung. Du bereitest Kopien vor und schreibst ein Manifest. Du aenderst nichts im Repo, committest
nichts, oeffnest keine Parquet-/Siegeldatei, laedst keine Marktdaten.

## Warum

Die Akte verweist 61-mal auf Skripte, die nur in Arbeitsverzeichnissen ausserhalb des Repos lagen; am 2026-10-31 ging
ein solches Verzeichnis verloren. Verfassung 3.1 (angenommen 2026-11-02) verlangt "keine Zahl ohne versioniertes
Skript". Dieser Auftrag ist Fahrplan-Schritt F0 der Automations-Architektur
(`scinance3-impl/state/PRD_ANALYSE_2026-11-01.md` Abschnitt 7 und 9.2 Nr. 5).

## Quelle

`/home/user/scinance_work/` mit den Unterordnern `hscripts/` (Datenextrakte A2), `orch_check/` (Orchestrator-
Nachrechnungen, `channel_scan.py`), `a2_teilC/` und `a2_teilC_review/` (Agentenskripte Teil C und Review; `work/`-
Unterordner enthalten Ausgaben), `drafts/` (DEC-Entwuerfe, Specs, Commit-Texte), `hf_data/raw/EXTRACT_LOG.json`
(Manifest der Datenextrakte mit sha256). **Nicht anfassen:** `harvest_client/` (fremder Client, enthaelt
Zugangs-Doku), `hcache/`, `hf_data/raw/*.parquet` (Marktdaten; nie kopieren, nie oeffnen), `__pycache__`, `*.pyc`, `*.log`.

## Ziel-Layout (Vorschlag; pruefe zuerst `scinance3-impl/` auf vorhandene Struktur und DEC-54 Repo-Struktur in
`scinance3-impl/state/decisions.md` sowie PRD_SCINANCE3.md Par. 3; passe an, wenn es dort eine Vorgabe gibt)

- `scinance3-impl/derivations/a2/` : Agenten-Herleitungsskripte (Teil A/B/C) und ihre Specs (`SPEC_*.md`)
- `scinance3-impl/derivations/a2/data_manifest/` : `EXTRACT_LOG.json` (nur wenn frei von Hostnamen/Schluesseln) und
  die Extraktskripte aus `hscripts/`
- `scinance3-impl/verify/a2/` : Orchestrator-Checks (`orch_check/a2_*.py`), Review-Skripte (`a2_teilC_review/*.py`)
- `scinance3-impl/tools/channel_scan.py` : Struktur-Scan nach DEC-103 N1 (2c)
- `scinance3-impl/derivations/drafts_2026-10/` : nur Entwuerfe, die NICHT bereits inhaltlich im Repo stehen (DEC-Texte
  sind in `state/decisions.md` committet -> nicht kopieren; Specs an Agenten -> kopieren)

Du legst **alles unter** `<scratchpad>/f0/stage/`
ab, mit dem Zielpfad relativ zum Repo-Root darunter (z. B. `stage/scinance3-impl/verify/a2/a2_null_check.py`). Der
Orchestrator prueft und verschiebt. Nichts direkt ins Repo.

## Pruefung je Datei (Pflicht, vor dem Staging)

1. **Hygiene-Scan** (Treffer -> NICHT stagen, nur im Manifest mit Dateiname und Zeilennummer, niemals den Wert
   zitieren): Hostnamen, URLs, IP-Adressen, S3-Endpunkte, Bucket-Namen, Werte von Umgebungsvariablen (die Namen
   `HARVEST_S3_ENDPOINT`, `HARVEST_S3_ACCESS_KEY`, `HARVEST_S3_SECRET_KEY` sind als Namen erlaubt, ihre Werte nie),
   Zugangsdaten, Tokens, E-Mail-Adressen, absolute Pfade mit Nutzernamen ausser `/home/user/...` (den dokumentierst du
   als bekannten Sandbox-Pfad). Pruefe auch Kommentare und Strings. Modellnamen (Produktnamen von Sprachmodellen) sind
   in Repo-Dateien unerwuenscht: ersetze sie in Kopien durch Rollen (Orchestrator, Herleitung, Review, Bau) und vermerke
   die Ersetzung im Manifest.
2. **Ausgaberegel DEC-103 N1 (2c):** JSON-/CSV-Ausgaben mit Nuisance-Zahlen (z. B. in `a2_teilC/work/`,
   `a2_teilC_review/work/`) werden NICHT gestaged. Liste sie im Manifest mit sha256 und vermerke, ob eine Kopie bereits
   im Repo liegt (`scinance3-impl/state/herleitung_a2/*.json`, Vergleich per sha256).
3. **Nicht-ASCII:** Kopien muessen ASCII sein (Umlaute als ae/oe/ue/ss; in Code-Kommentaren ebenso).
4. **Dubletten mit dem Repo:** Wenn eine Datei inhaltlich bereits im Repo liegt (z. B. `drafts/dec103.md` in
   `state/decisions.md`, `drafts/uebergabe_n13b.md` in `UEBERGABE_2026-10-12.md`), nicht stagen, im Manifest "bereits
   im Repo (Ziel)" vermerken.
5. **Syntax-Check** fuer `.py`: `python3 -I -m py_compile <datei>` muss durchlaufen (nicht ausfuehren!).

## Manifest

`<scratchpad>/f0/F0_MANIFEST.md` (ASCII):

1. Tabelle je Quelldatei: Quellpfad, Zielpfad (oder "nicht gestaged"), sha256 (Quelle), Zweck (aus Docstring/Header,
   ein Satz), Akten-Verweise (grep des Dateinamens in `scinance3-impl/` - welche DEC/Dokumente nennen die Datei),
   Eingaben (Datenextrakte per Dateiname + sha256 aus `EXTRACT_LOG.json`, nie Inhalte), Status und Grund.
2. Abgleich der Akten-Verweise: `grep -rn 'scratchpad' scinance3-impl/` (und `scinance_work`) -> Liste der referenzierten
   Skriptnamen; je Name: durch eine gestagte Datei erfuellt (ja/nein, welcher Zielpfad) oder verloren (Scratch-Verlust
   2026-10-31) - dann "verloren, nur Ergebnis-sha256 in der Akte".
3. Hygiene-Befunde (Datei, Zeile, Art) ohne Werte.
4. Vorschlag fuer eine `README.md` je Zielordner (Zweck, Reproduktion: welche Extrakte mit welchem sha256 noetig sind,
   welche Ausgabe-Datei im Repo das Ergebnis traegt).
5. Kurzfassung (<= 10 Zeilen) an den Orchestrator: Anzahl gestaged / nicht gestaged / Hygiene-Treffer / verlorene
   Verweise.

## Regeln

Nur lesen und kopieren; keine Ausfuehrung von Skripten (ausser `py_compile`); keine Marktdaten; keine Siegeldateien
(`scinance3-impl/state/runs/*_L_window_sealed.json`, `weekly_ic_series.csv`, `ic_series_*_UNION_REAL.csv`); kein Commit;
nichts im Repo aendern. ASCII, Deutsch, Rollen statt Modellnamen, keine Hostnamen.
