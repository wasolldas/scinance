"""Feasibility calculator for Constitution 3.1 (``feasibility31``, programme step F3, DEC-104 E9).

Answers mechanically, before any derivation or registration, whether a hypothesis is testable against its SESOI with
the measured nuisance: with which decision rule, window length, zone and from which date.  Works exclusively on
nuisance numbers taken from the dossier (YAML/JSON candidate files) and on formulas; it reads no market data, no
sealed file, no harvest client and uses no network.

Modules: ``schema`` (candidate file, loud failure), ``rules`` (decision-rule menu R1..R6), ``gsd`` (group-sequential
engines), ``conjunction`` (product vs exact joint power), ``sesoi`` (cost curves and SESOI), ``report`` (assembly of
the mandatory output rows, JSON and Markdown), ``cli`` (command line).
"""
from __future__ import annotations

__all__ = ["__version__", "SCHEMA_VERSION"]

__version__ = "1.0.0"
SCHEMA_VERSION = 1
