"""List PARTIAL/FAILED partitions of the WP-7 panel_1d manifest (read-only)."""
import sqlite3
c = sqlite3.connect("data/panel_1d/panel_manifest.sqlite")
q = ("SELECT symbol, year, status, n_rows, expected_days, frozen, failure_reason "
     "FROM partitions WHERE status IN ('PARTIAL','FAILED') ORDER BY year, symbol")
for r in c.execute(q):
    print(r)
