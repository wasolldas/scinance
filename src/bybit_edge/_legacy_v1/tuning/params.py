# DEPRECATED (2026-06-23): Scinance-1.0-Legacy.
# Siehe scinance2-impl/state/CLEANUP_PLAN.md - Live-Pipeline gestoppt (TODO-2),
# Strategien S1-S5 sind empirisch DROP (WAVE1_FINAL_REPORT.md), Modul folgt der
# LiveRunner-Deprecation. Aufruf gilt als Anti-Pattern; Code bleibt nur als
# Audit-Trail im Repo. Reaktivierung ware eine neue, vorregistrierte Hypothese.

"""ParameterContext — temporary, exception-safe overrides on ``bybit_edge.config``.

Motivation
----------
The five strategies and their layer modules import config constants with
``from bybit_edge.config import X``. Once a module has executed that line,
its local binding ``X`` is detached from the ``bybit_edge.config`` module
object — re-assigning ``bybit_edge.config.X`` at runtime does NOT update the
strategy's binding (Python's from-import semantics).

To make hyperparameter tuning work without rewriting every strategy, the
:class:`ParameterContext` patches BOTH locations:

1. ``bybit_edge.config.X`` itself (so any fresh ``from bybit_edge.config
   import X`` after the patch sees the new value).
2. Every already-loaded module in ``sys.modules`` that exposes an attribute
   with the same name. The override only patches the attribute when the
   currently-loaded value equals ``bybit_edge.config.X`` (i.e. the module
   originally got it via ``from bybit_edge.config import``). This avoids
   accidentally clobbering local variables that happen to share a name.

Why this works for the tuner
----------------------------
``ReplayBacktester.run_walkforward`` re-instantiates one fresh strategy per
fold via :meth:`ReplayBacktester._build_strategies`. The strategies (and
their internal M*-modules) read config-derived thresholds **either** in
``__init__`` (e.g. ``self._x = X``) **or** at runtime in ``_check_entry`` /
``_check_exit``. In both cases, by patching the strategy module's namespace
BEFORE the fold's ``_build_strategies()`` runs, the new instances pick up
the overridden values.

S3 specifics
------------
``strategy3_pre_settlement`` pre-computes ``_ENTRY_WINDOW_SECONDS`` and
``_EXIT_SECONDS_POST_SETTLEMENT`` at module import time. Those derived
constants are NOT updated by the generic attribute patch above, so they
must not be tuned via ``PRESSURE_ENTRY_WINDOW_MINUTES`` /
``PRESSURE_EXIT_MINUTES_POST_SETTLEMENT`` directly. A tiny shim in the same
strategy module (``_resolve_entry_window_seconds()``) re-reads the live
config value on each call, so the tuner CAN safely override the *minutes*
constant. The shim is the only structural change to a strategy in this
package and is documented inline in :mod:`strategy3_pre_settlement`.
"""
from __future__ import annotations

import logging
import sys
from types import ModuleType
from typing import Any

import bybit_edge.config as _cfg

logger = logging.getLogger(__name__)

# Modules outside the ``bybit_edge`` package (test runners, third-party) are
# never patched. This keeps the override surgical and reversible.
_PACKAGE_PREFIX: str = "bybit_edge"


class ParameterContext:
    """Temporarily override ``bybit_edge.config`` attributes.

    Usage::

        with ParameterContext({"PRESSURE_ZSCORE_THRESHOLD": 1.8}):
            backtester.run_walkforward()
        # PRESSURE_ZSCORE_THRESHOLD is back to its original value here.

    Parameters
    ----------
    overrides:
        Mapping ``{config_attribute_name: new_value}``. Every key must be
        an existing attribute on :mod:`bybit_edge.config`; unknown keys
        raise :class:`ValueError` immediately on ``__enter__`` (fail-fast).
    """

    def __init__(self, overrides: dict[str, Any]) -> None:
        self._overrides: dict[str, Any] = dict(overrides)
        # (module_object, attribute_name, original_value) tuples used by
        # __exit__ to restore the world. Populated by __enter__.
        self._backup: list[tuple[ModuleType, str, Any]] = []
        # Keys that were not present in any module (apart from cfg itself).
        # Tracked only for informative debug logging.
        self._only_in_cfg: list[str] = []
        self._active: bool = False

    # ------------------------------------------------------------------
    # Context manager protocol
    # ------------------------------------------------------------------
    def __enter__(self) -> "ParameterContext":
        # Fail-fast validation: every key must exist on bybit_edge.config.
        for key in self._overrides:
            if not hasattr(_cfg, key):
                raise ValueError(
                    f"ParameterContext: unknown config attribute {key!r} — "
                    f"must be defined in bybit_edge.config."
                )
        self._apply()
        self._active = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Always restore, even on exception. The backup list captures the
        # original value per (module, name) so the world is bit-identical
        # to pre-context state when this exits.
        self._restore()
        self._active = False
        # Do not suppress exceptions.
        return None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _patch_targets(self, key: str) -> list[ModuleType]:
        """Return every bybit_edge module that currently holds the same
        ``key`` attribute as ``bybit_edge.config``.

        Modules that have not imported ``key`` are skipped. Modules where
        ``key`` has been locally re-bound to a different object (i.e. its
        ``id()`` differs from ``getattr(cfg, key)``) are also skipped to
        avoid clobbering unrelated variables.
        """
        original_value = getattr(_cfg, key)
        targets: list[ModuleType] = [_cfg]
        for mod_name, mod in list(sys.modules.items()):
            if mod is None or mod is _cfg:
                continue
            if not mod_name.startswith(_PACKAGE_PREFIX):
                continue
            if not hasattr(mod, key):
                continue
            try:
                local_value = getattr(mod, key)
            except Exception:
                continue
            # Identity check: only patch modules that share the SAME object
            # as bybit_edge.config (i.e. via ``from bybit_edge.config import
            # X``). Skip when the module has rebound the name to a fresh
            # value, which signals a derived/local constant.
            if local_value is original_value:
                targets.append(mod)
        return targets

    def _apply(self) -> None:
        """Snapshot originals, then write all overrides."""
        for key, new_value in self._overrides.items():
            targets = self._patch_targets(key)
            for mod in targets:
                self._backup.append((mod, key, getattr(mod, key)))
                setattr(mod, key, new_value)
            if len(targets) == 1:
                # Only patched on the config module itself — informative
                # debug log so users can spot config keys that are never
                # imported anywhere.
                self._only_in_cfg.append(key)
        if self._only_in_cfg:
            logger.debug(
                "ParameterContext: keys patched only on bybit_edge.config "
                "(no consuming module currently imports them): %s",
                self._only_in_cfg,
            )

    def _restore(self) -> None:
        """Roll every (module, key) pair back to its captured original."""
        # Restore in reverse insertion order so that if multiple overrides
        # ever touched the same (module, key) the original wins out.
        while self._backup:
            mod, key, original = self._backup.pop()
            setattr(mod, key, original)
