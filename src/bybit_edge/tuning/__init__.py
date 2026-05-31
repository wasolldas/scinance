"""Hyperparameter-Tuning package for the five Bybit-Edge strategies.

This package is intentionally optional: importing :mod:`bybit_edge.tuning`
does NOT pull in Optuna. Only :mod:`bybit_edge.tuning.optuna_tuner` requires
``optuna`` (declared in the ``[tuning]`` extra of ``pyproject.toml``).

Public API
----------
* :class:`ParameterContext` — temporarily override ``bybit_edge.config``
  attributes for the duration of a ``with``-block, then restore originals.
* :data:`SPACES` and :func:`sample_from_space` — per-strategy parameter
  search spaces in a serialisable dict format.
* :class:`OptunaTuner` (lazy-imported) — TPE-driven walk-forward optimiser.
"""
from __future__ import annotations

from bybit_edge.tuning.params import ParameterContext
from bybit_edge.tuning.spaces import SPACES, sample_from_space

__all__ = [
    "ParameterContext",
    "SPACES",
    "sample_from_space",
]
