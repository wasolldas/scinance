# data_manifest - Herkunft der A2-Datenextrakte (F0)

`EXTRACT_LOG.json` ist das Manifest der vier Extrakte (Zeilen, sha256, Warnungen). Die Parquet-Dateien selbst
(Marktdaten) liegen nicht im Repo und werden nur ueber diese sha256 referenziert; die Teil-C- und Review-Skripte
pruefen sie beim Laden gegen dieses Manifest.

Reihenfolge der Erzeugung: `extract_a2.py` (Kerzen 2021-03-24..2024-05-31, Kalender, Funding W2) ->
`extract_a2_fast.py` (paralleler Cache-Warmup, Kalender und Funding W2 erneut, Kerzen-Hash uebernommen, schreibt
EXTRACT_LOG.json neu) -> `extract_funding_pre_w1.py` (Funding 2021-03-24..2025-06-30, ergaenzt EXTRACT_LOG.json).

Zugang: Data-Harvest-Archiv ueber dessen Client (nicht im Repo). Zugangsdaten ausschliesslich aus den
Umgebungs-Secrets `HARVEST_S3_ENDPOINT` / `HARVEST_S3_ACCESS_KEY` / `HARVEST_S3_SECRET_KEY`; nie ins Repo, nie in
Logs. Die Skripte enthalten weder Host noch Schluessel; Reproduktion ist nur in einer Sitzung mit Archivzugang moeglich.
Siegel: Kerzen nur bis 2024-05-31 (Assert), Kalender nur bis 2026-06-30 ohne Preisfelder (Assert), Funding nur
Zeitstempel. Ergebnisdateien im Repo: keine ausser diesem Manifest.
