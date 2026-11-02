"""Registration schema and linter for Constitution 3.1 (``registry31``, programme step F1, DEC-104 E9).

Modules: ``schema`` (data model of the registration, loud failure, JSON Schema export) and ``lint`` (rules as data,
CLI ``python -m bybit_edge.research.registry31.lint <registration.yaml>``).  Reads one YAML file; no market data, no
sealed file, no network.
"""
from __future__ import annotations

__all__ = ["__version__"]

__version__ = "1.0.0"
