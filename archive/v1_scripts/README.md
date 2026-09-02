# archive/v1_scripts/

Neun Scinance-1.0-CLI-Skripte -- **nicht mehr gepflegt, muessen NICHT
lauffaehig bleiben.** Keiner der `scinance2-impl/handoff_local/run_*.ps1`-
Runner und keine Option in `start.bat` ruft sie auf; sie sind operativ tot.

| Skript | Zweck (frueher) |
|---|---|
| `backtest.py` | Klassischer S1-S5-Strategie-Vergleich ueber Historie (`_legacy_v1.backtester.engine`) |
| `backfill.py` | REST-Kline-Backfill in `bybit_edge.duckdb` (`_legacy_v1.persistence.backfill`) |
| `dashboard.py` | Streamlit-Launcher-Wrapper fuer `_legacy_v1.dashboard.app` |
| `train_models.py` | Trainings-Pipeline fuer die L4-Pattern-Modelle (PatchTST/TimesNet/Moment) |
| `tune.py` | Optuna-Hyperparameter-Tuning fuer S1-S5 |
| `replay_all.py` | Forensischer Full-Replay ueber alle Strategien (Iter-5-Lauf) |
| `replay_backtest.py` | Duennere Replay-CLI |
| `_profile_replay.py` | cProfile-Wrapper um den Replay |
| `setup_local.sh` | Veraltetes Onboarding-Skript (referenziert ein nicht mehr existierendes `run_backtest.py`) |

Die drei Skripte `backtest.py`, `replay_all.py`, `replay_backtest.py`
werden weiterhin von `tests/unit/test_backtest_driver.py`,
`test_replay_all.py` bzw. `test_replay_backtest_cli.py` importiert (32
Tests) -- ihre `bybit_edge.*`-Imports wurden deshalb auf die neuen
`bybit_edge._legacy_v1.*`-Pfade umgeschrieben, damit diese Tests weiter
gruen bleiben (Testsuite ist Schutzgut, siehe
`scinance3-impl/UMBAU_SPEZIFIKATION.md` §0). Das macht sie importierbar,
nicht "lauffaehig" im Sinne von produktiv nutzbar -- Konfiguration,
Datenpfade und Live-Verbindungen sind nicht mehr gepflegt.

Der zugrundeliegende Code, den diese Skripte antreiben (Backtester, L1-L5-
Layer, S1-S5-Strategien), liegt seit dem Umbau unter
`src/bybit_edge/_legacy_v1/`.
