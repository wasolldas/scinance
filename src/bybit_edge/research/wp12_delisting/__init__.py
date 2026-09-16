"""WP-12 -- Delisting-Register + Survivorship-Fixture (B3-Konsequenz, DEC-67
Entscheidung 5), KAPITALFREI.

See ``scinance3-impl/state/decisions.md`` DEC-58(g) (Aufnahme: Delisting-
Hazard/IPCW als Beifahrer in WP-7 -- superseded in substance by this
package's fuller register), DEC-67 Entscheidung 5 (this package's mandate,
worded verbatim below) and ``PRD_SCINANCE3.md`` 4.1 Befund B3:

    "Kein Survivorship-freies Universum aus Bybit-Bordmitteln. Konsequenz
    vorab: Klasse W laeuft nur, wenn das Survivorship-Fixture eine
    Verzerrung kleiner als die halbe registrierte Schwelle zeigt; sonst
    nicht registrierbar."

WP-12 does three things, in order:

  1. ``announcements.py`` -- builds a delisting register from the PUBLIC
     Bybit announcements index (keyfrei, no auth), regex-extracted symbols,
     a category guess, and a best-effort delisting timestamp parsed from
     the announcement text.
  2. ``kline_probe.py`` -- for every delisted LINEAR symbol in the
     register, probes whether Bybit still serves daily kline history in
     the 90 days before delisting. This is the decisive feasibility
     question the PRD anticipates: if history is available, delisted
     symbols can (in a LATER task, not here) be added to ``panel_1d`` as a
     separate ``source=bybit_delisted`` tree.
  3. ``survivorship_fixture.py`` -- pure, no-network: measures the bias a
     momentum weekly IC estimator picks up from omitting delisted symbols
     (``IC_with - IC_without``), with a week-cluster bootstrap CI. The
     registered threshold (PRD 4.1 B3, "kleiner als die halbe registrierte
     Schwelle") is **NOT YET REGISTERED** (A3 is gated on this very
     fixture, DEC-67 Entscheidung 1) -- this module therefore never prints
     PASS/FAIL, only the measured bias and that sentence.

``panel_read.py`` is a small, self-contained ``panel_1d`` reader (own
implementation, does NOT import ``wp7_universe.panel_load`` -- a
concurrently-edited file per the build brief) built only from
``wp7_universe.panel_store`` (read-only) + ``pyarrow`` + ``pit_universe``
(read-only). ``report.py`` assembles ``wp12_report.md``/
``wp12_summary.json`` (DEC-53 artifacts: register parquet sha256, per-week
IC series with/without CSV, bootstrap seed).

Everything here is read-only with respect to existing data and NEVER
writes under ``data/harvest`` (Schutzgut, CLAUDE.md). Public endpoints
only, no API keys, no private endpoints, no orders.

**WP-12b addendum (DEC-70):** ``delisted_panel.py`` fetches the FULL daily
kline (+funding) history for every delisted linear symbol into its own
``data/panel_1d_delisted/`` tree (same on-disk layout/manifest discipline
as ``wp7_universe.panel_store``, never ``data/panel_1d/``). See
``wp7_universe.panel_load.load_panel_union`` for the point-in-time
survivorship-free union read path and ``scripts/wp7_universe_census.py
--include-delisted`` for the census that runs on it.
"""
from __future__ import annotations
