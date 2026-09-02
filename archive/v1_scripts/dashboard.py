"""Wrapper-Skript zum Start des Streamlit-Dashboards.

Aufruf::

    python scripts/dashboard.py [--port 8501] [--host 0.0.0.0]

Startet ``streamlit run src/bybit_edge/dashboard/app.py`` als Subprozess
und gibt die URL aus.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Bybit Edge Dashboard")
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--host", type=str, default="localhost")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    app_path = repo_root / "src" / "bybit_edge" / "dashboard" / "app.py"
    if not app_path.exists():
        print(f"[ERROR] Dashboard-App nicht gefunden: {app_path}", file=sys.stderr)
        return 1

    url = f"http://{args.host}:{args.port}"
    print("=" * 64)
    print(f"  Bybit Edge Dashboard")
    print(f"  URL: {url}")
    print("=" * 64)

    cmd = [
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.port", str(args.port),
        "--server.address", args.host,
        "--browser.gatherUsageStats", "false",
    ]
    try:
        return subprocess.call(cmd)
    except FileNotFoundError:
        print(
            "[ERROR] Streamlit nicht installiert. Installiere mit:\n"
            "        pip install -e '.[dashboard]'",
            file=sys.stderr,
        )
        return 1
    except KeyboardInterrupt:
        print("\nDashboard beendet.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
