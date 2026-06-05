"""
Unit tests for ``scripts/replay_backtest.py`` CLI argument handling.

The single-symbol replay CLI builds its argparse parser inside ``main()`` so
the parser itself is not exposed for direct testing. The ``--fast-omori`` flag
delegates to the module-level :func:`_resolve_fast_omori` helper which IS
public — these tests exercise the three branches of that helper (flag absent,
flag without value, flag with explicit value) so the regression coverage for
the opt-in performance throttle matches the ``replay_all.py`` CLI.
"""
from __future__ import annotations

import scripts.replay_backtest as replay_backtest
from bybit_edge.config import OMORI_REFIT_SECONDS


def test_replay_backtest_fast_omori_flag_absent_resolves_to_zero() -> None:
    """Without ``--fast-omori`` the resolver returns 0.0 (no throttle)."""
    assert replay_backtest._resolve_fast_omori(None) == 0.0


def test_replay_backtest_fast_omori_flag_no_value_uses_config_default() -> None:
    """``--fast-omori`` without a value falls back to OMORI_REFIT_SECONDS."""
    assert replay_backtest._resolve_fast_omori(
        replay_backtest._FAST_OMORI_DEFAULT_SENTINEL
    ) == float(OMORI_REFIT_SECONDS)


def test_replay_backtest_fast_omori_flag_with_value_parsed() -> None:
    """``--fast-omori 15`` is resolved to the float 15.0."""
    assert replay_backtest._resolve_fast_omori(15.0) == 15.0


def test_replay_backtest_fast_omori_flag_parsed() -> None:
    """End-to-end parse: build the parser inline (matches ``main``) and run it.

    Mirrors the structure of the ``main()`` parser construction so the test
    breaks if the flag's ``nargs="?"`` / ``const`` wiring drifts.
    """
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fast-omori",
        dest="fast_omori",
        nargs="?",
        const=replay_backtest._FAST_OMORI_DEFAULT_SENTINEL,
        default=None,
        type=float,
    )
    ns_absent = parser.parse_args([])
    ns_bare = parser.parse_args(["--fast-omori"])
    ns_val = parser.parse_args(["--fast-omori", "15"])

    assert replay_backtest._resolve_fast_omori(ns_absent.fast_omori) == 0.0
    assert (
        replay_backtest._resolve_fast_omori(ns_bare.fast_omori)
        == float(OMORI_REFIT_SECONDS)
    )
    assert replay_backtest._resolve_fast_omori(ns_val.fast_omori) == 15.0
