# archive/

Verworfene Ansaetze OHNE lebenden Code -- reine Doku-Frameworks
(`v1_frameworks/`) und nicht mehr gepflegte CLI-Werkzeuge
(`v1_scripts/`). Toter, aber weiterhin importierter und getesteter Code
(der eigentliche Scinance-1.0-Stack: Layer, Strategien, Live-Runner,
Dashboard usw.) liegt NICHT hier, sondern quarantaeniert im Paket selbst
unter `src/bybit_edge/_legacy_v1/` -- siehe die Docstring-Begruendung dort
und `scinance3-impl/UMBAU_SPEZIFIKATION.md` §0/§1.3.

| Ordner | Inhalt | README |
|---|---|---|
| `v1_frameworks/` | Vier reine Markdown-Multiagenten-Forschungsframeworks (0 Code), die zu den fruehen PRD-Entwuerfen fuehrten | `v1_frameworks/README.md` |
| `v1_scripts/` | Neun Scinance-1.0-CLI-Skripte (`backtest.py`, `backfill.py`, `dashboard.py`, `train_models.py`, `tune.py`, `replay_all.py`, `replay_backtest.py`, `_profile_replay.py`, `setup_local.sh`) | `v1_scripts/README.md` |

Nichts hier wird geloescht -- alle Verschiebungen liefen per `git mv`, die
Git-Historie bleibt erhalten.
