"""Bybit-Edge Streamlit Dashboard — read-only live visualisation.

Das Dashboard läuft als eigener Prozess parallel zum LiveRunner und liest
ausschließlich aus DuckDB (read-only), dem Trade-Journal-CSV und der REST-
API des Executors. Es nimmt keine Order-Aktionen vor und öffnet keinen
WebSocket.

Start:
    streamlit run src/bybit_edge/dashboard/app.py
oder
    python scripts/dashboard.py
"""
from __future__ import annotations

from bybit_edge.dashboard.data import (
    load_account_status,
    load_heartbeat_file,
    load_journal,
    load_recent_liquidations,
    load_row_counts,
)

__all__ = [
    "load_account_status",
    "load_heartbeat_file",
    "load_journal",
    "load_recent_liquidations",
    "load_row_counts",
]
