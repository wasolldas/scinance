# Auftrags-Warteschlange (Autopilot, DEC-79)

- `auftrag.json` - der aktuelle Auftrag. Der Orchestrator schreibt ihn und pusht; der
  Autopilot auf der Nutzer-Maschine (`handoff_local/autopilot.py`, geplante Aufgabe
  "Scinance Autopilot", alle 15 min) fuehrt ihn aus. Schema: `id` (eindeutig),
  `tasks` (nur `wp13a`, `wp10b`, `wp7`, `wp10a2`, `wp12`, `wp13run`, `diag`),
  optional `registered` + `registered_sha256` (nur fuer `wp13run`), `wp10b_resume`,
  `skip_if_done_since` (Commit-Hash; Aufgaben, die seitdem mit rc=0 gemeldet wurden,
  entfallen), `zweck` (Freitext). Alles andere wird abgelehnt.
- `gestartet/<id>.json` - vom Autopiloten beim Start gepusht.
- `erledigt/<id>.json` - von `nacht.ps1` am Ende gepusht (Ergebnisse je Aufgabe, Protokollpfad).

Jede ID laeuft je Maschine hoechstens einmal. Neuer Auftrag = neue ID.
