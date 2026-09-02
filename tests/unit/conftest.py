"""Shared pytest fixtures for unit tests.

Insbesondere isoliert ``_redirect_dashboard_snapshots`` den Dashboard-
Snapshot-Export des LiveRunners in ein temporäres Verzeichnis, damit
Tests die echten ``data/dashboard/*.parquet`` Dateien NICHT überschreiben
und sich gegenseitig nicht über diese Snapshots beeinflussen.
"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _redirect_dashboard_snapshots(tmp_path_factory: pytest.TempPathFactory,
                                  monkeypatch: pytest.MonkeyPatch) -> Path:
    """Leitet ``DASHBOARD_SNAPSHOT_DIR`` für jeden Test um.

    Verhindert, dass ``LiveRunner._export_dashboard_snapshots`` Snapshots
    in das echte ``data/dashboard``-Verzeichnis schreibt — andernfalls
    würden Dashboard-Tests einen stale Snapshot lesen statt den DuckDB-
    Fallback zu nehmen.
    """
    target = tmp_path_factory.mktemp("dashboard_snapshots")
    # live_runner importiert das Symbol direkt — wir patchen das Modul.
    try:
        import bybit_edge._legacy_v1.live_runner as lr_mod
        monkeypatch.setattr(lr_mod, "DASHBOARD_SNAPSHOT_DIR", target)
    except Exception:  # pragma: no cover — Modul-Import sollte funktionieren
        pass
    # Außerdem den Default in dashboard.data umlenken, damit Loader-Tests
    # nicht versehentlich auf echte Snapshots im Repo-Workspace zugreifen.
    try:
        import bybit_edge._legacy_v1.dashboard.data as data_mod
        monkeypatch.setattr(data_mod, "_DEFAULT_SNAPSHOT_DIR", target)
    except Exception:  # pragma: no cover
        pass
    return target
