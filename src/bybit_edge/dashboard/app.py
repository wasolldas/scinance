"""Streamlit-Dashboard — Live-Sicht auf den Bybit-Edge-LiveRunner.

Read-only: liest Trade-Journal-CSV, DuckDB (read-only) und den
Bybit-REST-Account des Executors. Sendet keine Orders, öffnet keinen
WebSocket.

Start::

    streamlit run src/bybit_edge/dashboard/app.py
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import duckdb
import pandas as pd

try:
    import streamlit as st
except ImportError as exc:  # pragma: no cover — UI-Only
    raise SystemExit(
        "Streamlit ist nicht installiert. Installiere mit: "
        "pip install -e '.[dashboard]'"
    ) from exc

try:
    import plotly.express as px
    import plotly.graph_objects as go
    _HAS_PLOTLY = True
except ImportError:  # pragma: no cover
    _HAS_PLOTLY = False

try:
    from streamlit_autorefresh import st_autorefresh
    _HAS_AUTOREFRESH = True
except ImportError:  # pragma: no cover
    _HAS_AUTOREFRESH = False

from bybit_edge.config import (
    BYBIT_DEMO,
    BYBIT_TESTNET,
    DASHBOARD_SNAPSHOT_DIR,
    DATA_DIR,
    DB_PATH,
    PRIMARY_SYMBOL,
)
from bybit_edge.dashboard.data import (
    JOURNAL_COLUMNS,
    load_account_status,
    load_coverage,
    load_heartbeat_file,
    load_journal,
    load_journal_aggregated,
    load_recent_liquidations,
    load_replay_results,
    load_row_counts,
    ms_to_iso,
    top_n_symbol_strategy,
)
from bybit_edge.execution.bybit_executor import BybitExecutor

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_MS = 10_000
JOURNAL_PATH = DATA_DIR / "trades_journal.csv"
HEARTBEAT_PATH = DATA_DIR / "dashboard_state.json"


# --------------------------------------------------------------------------
# Resource helpers
# --------------------------------------------------------------------------

def _mode_str() -> str:
    if BYBIT_DEMO:
        return "DEMO"
    if BYBIT_TESTNET:
        return "TESTNET"
    return "LIVE"


def _open_duckdb_readonly(db_path: Path) -> Optional[duckdb.DuckDBPyConnection]:
    """Öffne eine read-only Connection — kompatibel mit parallel laufendem
    LiveRunner (DuckDB-Write-Lock wird nicht angefasst).
    """
    if not db_path.exists():
        return None
    try:
        return duckdb.connect(str(db_path), read_only=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("DuckDB read-only Connect fehlgeschlagen: %s", exc)
        return None


def _get_executor(symbol: str) -> Optional[BybitExecutor]:
    """Erzeugt pro Aufruf einen frischen ``BybitExecutor``.

    KEIN ``@st.cache_resource`` mehr: Streamlit baut bei jedem Auto-Refresh
    einen neuen Event-Loop (``asyncio.run``); eine über Reruns gecachte
    ``BybitExecutor``-Instanz würde die loop-gebundene ``aiohttp.ClientSession``
    aus dem alten (geschlossenen) Loop wiederverwenden und mit
    "Event loop is closed" crashen. Der eigentliche REST-Call läuft ohnehin
    in ``load_account_status`` mit einer frischen Executor-Instanz; dieser
    Wrapper liefert nur ein Platzhalter-Objekt (mit ``symbol``-Attribut),
    damit ``load_account_status`` weiß, dass ein API-Call gemacht werden soll.
    """
    try:
        return BybitExecutor(symbol)
    except Exception:  # noqa: BLE001
        return None


# --------------------------------------------------------------------------
# Layout-Helfer
# --------------------------------------------------------------------------

def _render_header(symbol: str, last_update: float) -> None:
    mode = _mode_str()
    cols = st.columns([3, 2, 2, 2])
    cols[0].markdown(f"### Bybit Edge — `{symbol}`")
    badge_colors = {"DEMO": "#3b82f6", "TESTNET": "#f59e0b", "LIVE": "#ef4444"}
    color = badge_colors.get(mode, "#6b7280")
    cols[1].markdown(
        f"<div style='padding:6px 12px;border-radius:6px;background:{color};"
        f"color:white;text-align:center;font-weight:bold'>Modus: {mode}</div>",
        unsafe_allow_html=True,
    )
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    cols[2].metric("Zeit (UTC)", now)
    delta = max(0, int(time.time() - last_update))
    cols[3].metric("Letztes Update", f"vor {delta}s")

    if mode == "LIVE":
        st.error(
            "ACHTUNG — LIVE-Modus aktiv. Das Dashboard ist read-only, "
            "aber der LiveRunner könnte ECHTES Geld bewegen, "
            "falls EXECUTION_ENABLED=true gesetzt ist.",
            icon=":material/warning:",
        )


def _render_kpis(
    symbol: str,
    account: dict,
    counts: dict[str, int],
    trades_today: int,
    session_start_equity: float | None,
) -> None:
    c1, c2, c3, c4 = st.columns(4)

    equity = account.get("equity", 0.0)
    if account.get("connected"):
        delta = (
            f"{equity - session_start_equity:+.2f} USDT seit Session-Start"
            if session_start_equity is not None
            else None
        )
        c1.metric("Equity (USDT)", f"{equity:,.2f}", delta=delta)
    else:
        c1.metric("Equity (USDT)", "n/a")
        c1.caption(f"Account nicht verbunden — {account.get('error', '')}")

    pos = account.get("position", {})
    if pos.get("size", 0) > 0:
        c2.metric(
            f"{pos.get('side', '?')} {pos.get('size', 0):.4f}",
            f"@ {pos.get('avg_price', 0):,.2f}",
            delta=f"uPnL {pos.get('unrealised_pnl', 0):+.2f}",
        )
    else:
        c2.metric("Position", "flat")

    persist_summary = (
        f"T:{counts.get('tickers', 0):,} "
        f"Tr:{counts.get('trades', 0):,} "
        f"L:{counts.get('liquidations', 0):,} "
        f"OB:{counts.get('orderbook_snapshots', 0):,}"
    )
    c3.metric("Persisted Rows", persist_summary)

    c4.metric("Trades im Journal heute", f"{trades_today}")


def _equity_chart(history: list[tuple[float, float]]) -> None:
    if not history:
        st.info("Noch keine Equity-Samples gesammelt. Warte ein paar Refresh-Zyklen.")
        return
    df = pd.DataFrame(history, columns=["ts", "equity"])
    df["time"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    if _HAS_PLOTLY:
        fig = px.line(df, x="time", y="equity", title="Account-Equity")
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=380)
        st.plotly_chart(fig, width="stretch")
    else:
        st.line_chart(df.set_index("time")["equity"])


def _render_journal_tab(journal_path: Path) -> None:
    df = load_journal(journal_path, n=50)
    if df.empty:
        st.info(f"Trade-Journal `{journal_path}` ist leer oder existiert noch nicht.")
        return

    def _status(row: dict) -> str:
        try:
            rc = int(row.get("ret_code", -1))
        except Exception:
            return "?"
        return "OK" if rc == 0 else f"ERR ({rc})"

    df = df.copy()
    df["status"] = df.apply(_status, axis=1)
    cols = ["ts_iso", "strategy_id", "action", "side", "qty", "price",
            "confidence", "status", "order_id"]
    cols = [c for c in cols if c in df.columns]
    st.dataframe(df[cols], width="stretch", height=520)


def _snapshots_available() -> bool:
    """True wenn mindestens eine Dashboard-Snapshot-Datei existiert."""
    base = Path(DASHBOARD_SNAPSHOT_DIR)
    return any(
        (base / name).exists()
        for name in ("row_counts.parquet", "liquidations_recent.parquet", "coverage.parquet")
    )


def _render_liquidations_tab(conn: Optional[duckdb.DuckDBPyConnection], symbol: str) -> None:
    # Bevorzugt Snapshot-Read (kein DuckDB-Lock-Konflikt); Fallback auf conn.
    rows = load_recent_liquidations(conn, symbol, n=30)
    if not rows:
        if not _snapshots_available() and conn is None:
            st.info(
                "Snapshots werden in Kürze verfügbar. Starte den LiveRunner mit "
                "`PERSIST_ENABLED=true`; der erste Export erfolgt nach "
                "~PERSIST_FLUSH_SECONDS."
            )
        else:
            st.info("Keine Liquidationen für dieses Symbol.")
        return
    df = pd.DataFrame(rows)
    df["time"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    if _HAS_PLOTLY:
        fig = px.bar(df, x="time", y="usd_value", color="side",
                     title="Liquidations (USD)")
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
        st.plotly_chart(fig, width="stretch")
    else:
        st.bar_chart(df.set_index("time")["usd_value"])

    c1, c2 = st.columns(2)
    side_counts = df["side"].value_counts().to_dict()
    c1.metric("Buy-Liqs", int(side_counts.get("Buy", 0)))
    c2.metric("Sell-Liqs", int(side_counts.get("Sell", 0)))

    st.dataframe(
        df[["time", "side", "volume", "price", "usd_value"]],
        width="stretch", height=320,
    )


def _render_persistence_tab(conn: Optional[duckdb.DuckDBPyConnection]) -> None:
    counts = load_row_counts(conn)
    coverage = load_coverage(conn)
    if not counts and not coverage:
        if not _snapshots_available() and conn is None:
            st.info(
                "Snapshots werden in Kürze verfügbar. Starte den LiveRunner mit "
                "`PERSIST_ENABLED=true`; der erste Export erfolgt nach "
                "~PERSIST_FLUSH_SECONDS."
            )
        else:
            st.warning(
                "Keine DuckDB-Daten gefunden. Erst Daten sammeln mit "
                "`PERSIST_ENABLED=true`, dann diesen Tab neu laden."
            )
        return

    if counts:
        df = pd.DataFrame(
            {"table": list(counts.keys()), "rows": list(counts.values())}
        )
        if _HAS_PLOTLY:
            fig = px.bar(df, x="table", y="rows", title="Persisted Rows pro Tabelle")
            fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
            st.plotly_chart(fig, width="stretch")
        else:
            st.bar_chart(df.set_index("table")["rows"])

    size_bytes = DB_PATH.stat().st_size if DB_PATH.exists() else 0
    st.metric("DuckDB-Dateigröße", f"{size_bytes / 1024 / 1024:,.1f} MB")

    range_rows: list[dict] = []
    for table, stats in coverage.items():
        if stats.get("min_ts") is None or stats.get("max_ts") is None:
            continue
        range_rows.append(
            {
                "table": table,
                "earliest": ms_to_iso(stats["min_ts"]),
                "latest": ms_to_iso(stats["max_ts"]),
                "hours": round(float(stats.get("hours", 0.0)), 2),
            }
        )
    if range_rows:
        st.dataframe(pd.DataFrame(range_rows), width="stretch")


def _render_pipeline_tab() -> None:
    hb = load_heartbeat_file(HEARTBEAT_PATH)
    if hb is None:
        st.info(
            "Kein Heartbeat-File. Starte den LiveRunner mit "
            "`ENABLE_HEARTBEAT_FILE=true`, damit hier Pipeline-Statistiken erscheinen."
        )
        return
    ts = hb.get("ts")
    age = max(0, int(time.time() - float(ts))) if ts else None
    c1, c2, c3 = st.columns(3)
    c1.metric("LiveRunner-Symbol", hb.get("symbol", "?"))
    c2.metric("Modus", hb.get("mode", "?"))
    c3.metric("Heartbeat-Alter", f"{age}s" if age is not None else "?")

    c1, c2, c3 = st.columns(3)
    c1.metric("Messages gesamt", f"{int(hb.get('msgs', 0)):,}")
    c2.metric("Trade-Buffer", int(hb.get("trade_buffer_len", 0)))
    c3.metric("Liq-Buffer", int(hb.get("liq_buffer_len", 0)))

    c1, c2, c3 = st.columns(3)
    c1.metric("Last Price", f"{float(hb.get('last_price', 0)):,.2f}")
    c2.metric("Mid Price", f"{float(hb.get('mid_price', 0)):,.2f}")
    c3.metric("Persisted", int(hb.get("persisted", 0)))

    st.caption(f"Position-Side im LiveRunner: `{hb.get('position_side', '') or 'flat'}`")


def _sharpe_color(sharpe: float) -> str:
    """Plotly-Farb-Bucket je nach Sharpe-Niveau."""
    if sharpe >= 1.0:
        return "#16a34a"   # green-600
    if sharpe >= 0.0:
        return "#eab308"   # yellow-500
    return "#dc2626"       # red-600


def _replay_status(n_trades: int, data_limited: bool) -> str:
    if data_limited and n_trades == 0:
        return "data-limited"
    if n_trades == 0:
        return "no-trades"
    if n_trades < 5:
        return "data-limited"
    return "OK"


def _render_strategy_performance_tab(journal_path: Path) -> None:
    """Tab 6 — Strategie-Performance: OOS-Replay + Live-Aggregat."""
    st.markdown("#### Sektion A — OOS-Replay-Ergebnisse")
    replay = load_replay_results()
    if replay is None or not replay.get("per_strategy"):
        st.info(
            "Noch kein Replay durchgeführt — führe "
            "`python scripts/replay_all.py --auto --walkforward` "
            "aus (Multi-Symbol) oder den Single-Symbol-Treiber "
            "`python scripts/replay_backtest.py --symbol BTCUSDT`."
        )
    else:
        per_strat: dict[str, dict] = replay["per_strategy"]
        src = replay["source"]
        if src == "multi_symbol":
            label = "Multi-Symbol-Aggregat (replay_all)"
        elif src == "walkforward":
            label = "Walk-Forward OOS-Replay"
        else:
            label = "Single-Pass-Replay"

        # Top-3 Highlight-Karte: bester (Symbol, Strategie, Sharpe).
        per_symbol = replay.get("per_symbol") or {}
        if isinstance(per_symbol, dict) and per_symbol:
            top = top_n_symbol_strategy(per_symbol, n=3, min_trades=5)
            if top:
                best = top[0]
                st.success(
                    f"**Bester Edge:** {best['symbol']} / {best['strategy']} · "
                    f"Sharpe = {best['sharpe']:.2f} · Trades = {best['n_trades']}"
                )
            else:
                st.warning(
                    "Noch keine Symbol/Strategie-Kombi mit ≥ 5 Trades — alles "
                    "data-limited. Mehr Live-Daten sammeln."
                )

        st.caption(
            f"Quelle: **{label}** — `{replay['path']}` · Datei-Stand: "
            f"{replay.get('timestamp', '?')} · Symbol: "
            f"{replay.get('symbol', '?') or '?'} · Events: "
            f"{replay.get('n_events', 0):,}"
        )
        if src == "walkforward" and replay.get("walkforward"):
            wf = replay["walkforward"]
            st.caption(
                f"Fold: train={wf.get('train_days', '?')}d / "
                f"embargo={wf.get('embargo_minutes', '?')}min / "
                f"test={wf.get('test_days', '?')}d · "
                f"Folds executed: {wf.get('n_folds_executed', '?')}"
            )

        # KPI-Cards — bis zu 5 Strategien (S1..S5)
        sids_sorted = sorted(per_strat.keys())
        cols = st.columns(max(len(sids_sorted), 1))
        for col, sid in zip(cols, sids_sorted):
            m = per_strat[sid]
            n = m["n_trades"]
            sharpe = m["sharpe"]
            wr = m["win_rate"]
            status = _replay_status(n, m.get("data_limited", False))
            if n == 0:
                col.markdown(
                    f"<div style='padding:8px;border-radius:6px;"
                    f"background:#1f2937;color:#9ca3af'>"
                    f"<b>{sid}</b><br>Sharpe: n/a<br>Trades: 0<br>"
                    f"Status: {status}</div>",
                    unsafe_allow_html=True,
                )
            else:
                color = _sharpe_color(sharpe)
                col.markdown(
                    f"<div style='padding:8px;border-radius:6px;"
                    f"background:{color};color:white'>"
                    f"<b>{sid}</b><br>Sharpe: {sharpe:.2f}<br>"
                    f"Trades: {n}<br>WinRate: {wr:.0%}<br>"
                    f"Status: {status}</div>",
                    unsafe_allow_html=True,
                )

        # Bar-Chart — Sharpe pro Strategie, absteigend
        chart_rows = [
            {
                "strategy": sid,
                "sharpe": m["sharpe"],
                "n_trades": m["n_trades"],
                "color": _sharpe_color(m["sharpe"]),
            }
            for sid, m in per_strat.items()
        ]
        chart_df = pd.DataFrame(chart_rows).sort_values("sharpe", ascending=False)
        if _HAS_PLOTLY and len(chart_df):
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=chart_df["strategy"],
                        y=chart_df["sharpe"],
                        marker_color=chart_df["color"].tolist(),
                        text=[f"{s:.2f}" for s in chart_df["sharpe"]],
                        textposition="outside",
                    )
                ]
            )
            fig.update_layout(
                title="Sharpe-Ratio pro Strategie (OOS)",
                yaxis_title="Sharpe",
                xaxis_title="Strategie",
                margin=dict(l=10, r=10, t=40, b=10),
                height=340,
            )
            st.plotly_chart(fig, width="stretch")
        elif len(chart_df):
            st.bar_chart(chart_df.set_index("strategy")["sharpe"])

        # Detail-Tabelle
        detail_rows = []
        for sid in sorted(per_strat.keys()):
            m = per_strat[sid]
            detail_rows.append(
                {
                    "Strategie": sid,
                    "Sharpe": round(m["sharpe"], 3),
                    "WinRate": round(m["win_rate"], 3),
                    "MaxDD": round(m["max_drawdown"], 4),
                    "Total Return": round(m["total_return"], 4),
                    "Trades": m["n_trades"],
                    "Status": _replay_status(
                        m["n_trades"], m.get("data_limited", False)
                    ),
                }
            )
        st.dataframe(pd.DataFrame(detail_rows), width="stretch")

        # --- Pro-Symbol Detail (nur Multi-Symbol-Modus) -----------------
        per_symbol_block = replay.get("per_symbol") or {}
        if isinstance(per_symbol_block, dict) and per_symbol_block:
            st.markdown("##### Pro Symbol")
            ps_rows = []
            for sym in sorted(per_symbol_block.keys()):
                strat_map = per_symbol_block[sym] or {}
                for sid in sorted(strat_map.keys()):
                    m = strat_map[sid]
                    ps_rows.append(
                        {
                            "Symbol": sym,
                            "Strategie": sid,
                            "Sharpe": round(float(m.get("sharpe", 0.0)), 3),
                            "WinRate": round(float(m.get("win_rate", 0.0)), 3),
                            "MaxDD": round(float(m.get("max_drawdown", 0.0)), 4),
                            "Trades": int(m.get("n_trades", 0)),
                            "Status": str(
                                m.get("status")
                                or _replay_status(
                                    int(m.get("n_trades", 0)),
                                    bool(m.get("data_limited", False)),
                                )
                            ),
                        }
                    )
            ps_df = pd.DataFrame(ps_rows)
            if not ps_df.empty:
                ps_df = ps_df.sort_values(
                    ["Sharpe", "Trades"], ascending=[False, False], kind="stable"
                ).reset_index(drop=True)
            st.dataframe(ps_df, width="stretch")

            if replay.get("skipped_symbols"):
                st.caption(
                    "Skipped (keine Events / zu wenig Daten): "
                    + ", ".join(replay["skipped_symbols"])
                )

    st.markdown("---")
    st.markdown("#### Sektion B — Live-Trade-Aggregat (`trades_journal.csv`)")
    agg = load_journal_aggregated(journal_path)
    if not agg:
        st.info(
            "Noch keine Live-Trades aufgezeichnet "
            "(EXECUTION_ENABLED=true setzen + auf gefüllte Signale warten)."
        )
    else:
        rows = []
        for sid in sorted(agg.keys()):
            r = agg[sid]
            n_total = max(r["n_total"], 1)
            rows.append(
                {
                    "Strategie": sid,
                    "Total": r["n_total"],
                    "Enter": r["n_enter"],
                    "Exit": r["n_exit"],
                    "Risk-Block": r["n_risk_block"],
                    "Erfolg (ret_code=0)": r["n_success"],
                    "Erfolgsrate": round(r["n_success"] / n_total, 3),
                }
            )
        st.dataframe(pd.DataFrame(rows), width="stretch")

    st.markdown("---")
    st.markdown("#### Sektion C — Lese-Hinweis")
    st.markdown(
        "> Sektion A zeigt was die Strategien rückblickend AUF GESAMMELTEN "
        "TICKS getan hätten (out-of-sample wenn Walk-Forward). Sektion B "
        "zeigt was sie tatsächlich live ausgeführt haben. Walk-Forward ist "
        "der ehrlichere Maßstab — Live-Stats werden erst nach Wochen "
        "statistisch belastbar."
    )


def _trades_today_count(journal_df: pd.DataFrame) -> int:
    if journal_df.empty or "ts_unix" not in journal_df.columns:
        return 0
    try:
        ts = pd.to_numeric(journal_df["ts_unix"], errors="coerce")
    except Exception:
        return 0
    today_utc_start = (
        datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    )
    return int((ts >= today_utc_start).sum())


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:  # pragma: no cover — UI-only
    st.set_page_config(
        page_title="Bybit Edge Dashboard",
        page_icon=":chart_with_upwards_trend:",
        layout="wide",
    )

    # Auto-Refresh alle 10 s
    if _HAS_AUTOREFRESH:
        st_autorefresh(interval=REFRESH_INTERVAL_MS, key="dash_autorefresh")
    else:
        st.caption(
            "Hinweis: `streamlit-autorefresh` nicht installiert — bitte "
            "manuell mit `R` neu laden oder das Extra installieren."
        )

    if "equity_history" not in st.session_state:
        st.session_state.equity_history = []  # list[tuple[ts, equity]]
    if "session_start_equity" not in st.session_state:
        st.session_state.session_start_equity = None
    if "last_update_ts" not in st.session_state:
        st.session_state.last_update_ts = time.time()

    symbol = PRIMARY_SYMBOL

    # --- Daten laden -----------------------------------------------------
    executor = _get_executor(symbol)
    account = load_account_status(executor)

    if account.get("connected"):
        eq = float(account["equity"])
        if st.session_state.session_start_equity is None and eq > 0:
            st.session_state.session_start_equity = eq
        # Equity-Sample (alle ~10 s ein Punkt, da Page jedes Refresh läuft)
        if eq > 0:
            st.session_state.equity_history.append((time.time(), eq))
            # Maximal 24 h Punkte vorhalten (10s × 8640)
            if len(st.session_state.equity_history) > 8640:
                st.session_state.equity_history = st.session_state.equity_history[-8640:]

    # Snapshots bevorzugen — vermeidet DuckDB-Lock-Konflikt mit dem LiveRunner.
    # Fallback auf direkten read-only Connect ist nur sinnvoll, wenn KEIN
    # Snapshot existiert (z.B. LiveRunner ist nie gelaufen).
    if _snapshots_available():
        conn = None
    else:
        conn = _open_duckdb_readonly(DB_PATH)
    counts = load_row_counts(conn)
    journal_df = load_journal(JOURNAL_PATH, n=50)
    trades_today = _trades_today_count(journal_df)

    st.session_state.last_update_ts = time.time()

    # --- Header + KPIs ---------------------------------------------------
    _render_header(symbol, st.session_state.last_update_ts)
    _render_kpis(
        symbol,
        account,
        counts,
        trades_today,
        st.session_state.session_start_equity,
    )

    # --- Tabs ------------------------------------------------------------
    tab_eq, tab_tr, tab_liq, tab_pers, tab_pipe, tab_strat = st.tabs(
        [
            "Equity",
            "Recent Trades",
            "Liquidations",
            "Persistence",
            "Pipeline-Stats",
            "Strategie-Performance",
        ]
    )
    with tab_eq:
        _equity_chart(st.session_state.equity_history)
    with tab_tr:
        _render_journal_tab(JOURNAL_PATH)
    with tab_liq:
        _render_liquidations_tab(conn, symbol)
    with tab_pers:
        _render_persistence_tab(conn)
    with tab_pipe:
        _render_pipeline_tab()
    with tab_strat:
        _render_strategy_performance_tab(JOURNAL_PATH)

    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass


main()  # pragma: no cover — Streamlit ruft das Skript bei jedem Reload
