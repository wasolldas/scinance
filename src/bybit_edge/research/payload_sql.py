"""Shared read-path SQL for the TWO harvester ``publicTrade`` payload forms.

The harvester stores an identical 7-column container schema everywhere
(``ts_local_ns, ts_exchange_ms, topic, stream, symbol, payload_json, date``),
but ``payload_json`` comes in two structurally different shapes
(DATASET.md §6 "publicTrade (Trades) — ZWEI Formen!"):

**A) FLAT (backfill form)** — ONE trade per parquet row, keys top-level::

    bybit    {"timestamp":"...","symbol":"BTCUSDT","side":"Sell",
              "size":"0.001","price":"64717.10","trdMatchID":"..."}
    binance  {"id":"...","price":"2321.16","qty":"0.014",
              "quote_qty":"...","time":"...","is_buyer_maker":"true"}
    deribit  {"trade_seq":..,"trade_id":"...","timestamp":1776211200244,
              "price":74192.0,"instrument_name":"BTC-PERPETUAL",
              "direction":"buy","amount":...}   <- NATIVE JSON numbers

**B) ENVELOPE (live form)** — MANY trades nested in one parquet row::

    bybit    {"topic":"publicTrade.BTCUSDT","type":"snapshot","ts":<pkt ms>,
              "data":[{"T":<trade ms>,"s":"BTCUSDT","S":"Sell","v":"0.010",
                       "p":"64085.60","i":"<tradeId>","BT":false}, ...]}
    deribit  either the same ``$.data[*]`` shape with deribit element keys,
             or the JSON-RPC notification
             {"jsonrpc":"2.0","method":"subscription",
              "params":{"channel":"trades...","data":[{...}, ...]}}
             -- BOTH paths are handled here (the deribit live shape is not
             verified against a stored file, so the reader is deliberately
             defensive rather than assuming one of them).

Every trade loader in ``bybit_edge.research`` used to read ONLY top-level
keys (``COALESCE($.price,$.p)`` etc.), so envelope rows produced NULL and
were silently dropped: bybit from 2026-07-17 (end of backfill coverage) and
deribit from ~2026-06-16 yielded 0 parsable trades, which flipped 19/50 W2
days of the H-12 run to ``panel_valid=False``.

``trade_rows_sql`` fixes that at ONE place: it wraps a parquet scan into a
row source of ONE TRADE PER ROW, so all pre-existing extraction SQL keeps
working unchanged on top of it -- the envelope element carries exactly the
venue-native keys the loaders already know (``p``/``v``/``S``/``i`` for
bybit live, ``price``/``amount``/``direction``/``trade_id`` for deribit).

BIT-IDENTITY GUARANTEE (the registered verdicts GL-006..GL-021 depend on
it): a row that is NOT an envelope is passed through the flat branch
untouched -- same ``ts_exchange_ms``, same ``payload_json`` string. No
known flat trade dialect carries a ``data`` key at all, so for a
backfill-only partition the expansion is a provable no-op.

KAPITALFREI: pure read-path SQL. No friction/PnL/threshold logic.
"""
from __future__ import annotations

#: JSON expression yielding the envelope trade array/object of a row, if any.
#: ``$.data`` covers the Bybit V5 WS form, ``$.params.data`` the JSON-RPC
#: subscription-notification form (Deribit).
_ENVELOPE = ("COALESCE(json_extract(payload_json,'$.data'),"
             " json_extract(payload_json,'$.params.data'))")

#: A row is an ENVELOPE row iff one of the two paths holds a JSON container.
#: ``OBJECT`` is accepted next to ``ARRAY`` purely defensively (a
#: single-trade envelope, e.g. a Binance combined-stream record); it can
#: never affect a flat dialect, none of which has a ``data`` key.
_IS_ENVELOPE = ("json_type(payload_json,'$.data') IN ('ARRAY','OBJECT')"
                " OR json_type(payload_json,'$.params.data') IN ('ARRAY','OBJECT')")

#: Complement of ``_IS_ENVELOPE`` written NULL-safely (``json_type`` returns
#: NULL for a missing path, and ``NULL IN (...)`` is NULL, not FALSE).
_IS_FLAT = (
    "json_type(payload_json,'$.data')        IS DISTINCT FROM 'ARRAY'\n"
    "          AND json_type(payload_json,'$.data')        IS DISTINCT FROM 'OBJECT'\n"
    "          AND json_type(payload_json,'$.params.data') IS DISTINCT FROM 'ARRAY'\n"
    "          AND json_type(payload_json,'$.params.data') IS DISTINCT FROM 'OBJECT'"
)

#: Exchange trade identifier across all known dialects. Bybit live ``i`` /
#: bybit backfill ``trdMatchID`` / Binance ``id`` (REST) and ``a`` (aggTrade)
#: / Deribit ``trade_id``. NULL when the dialect carries no id.
TRADE_ID_SQL = (
    "COALESCE(json_extract_string(payload_json,'$.i'),"
    " json_extract_string(payload_json,'$.trdMatchID'),"
    " json_extract_string(payload_json,'$.id'),"
    " json_extract_string(payload_json,'$.a'),"
    " json_extract_string(payload_json,'$.trade_id'))"
)

#: Cross-form de-duplication predicate (see ``cross_form_dedup_qualify``).
_CROSS_FORM_KEEP = (
    "NOT is_envelope\n"
    "     OR {tid} IS NULL\n"
    "     OR sum(CASE WHEN is_envelope THEN 0 ELSE 1 END)"
    " OVER (PARTITION BY {tid}) = 0"
)


def trade_rows_sql(source: str) -> str:
    """Wrap a parquet scan into a ONE-TRADE-PER-ROW source.

    ``source`` is any table expression, typically
    ``read_parquet([...], hive_partitioning=1, union_by_name=1)``.

    Returns a parenthesised sub-select exposing exactly three columns:

    ``ts_exchange_ms``  BIGINT  -- PER-TRADE exchange timestamp (ms)
    ``payload_json``    VARCHAR -- ONE trade's JSON object, top-level keys
    ``is_envelope``     BOOLEAN -- TRUE iff this row came out of a ``data[]``

    Structure is the UNION ALL of

      (A) the flat rows, passed through unchanged (bit-identity), and
      (B) the envelope rows, expanded with ``unnest(from_json(...))``.

    In branch (B) the PER-TRADE timestamp is used (``$.T`` for bybit live,
    ``$.timestamp`` for deribit), NOT the envelope's packet ``ts`` -- using
    the packet timestamp would collapse every trade of one WS message into
    a single millisecond and corrupt every minute/second bar and every
    inter-arrival time. The packet timestamp survives only as a last-resort
    fallback for an element that carries no timestamp of its own.

    The two branches read ``source`` twice (DuckDB scans the parquet files
    once per branch, with projection pushdown to the two columns used).
    That is the accepted cost of keeping branch (A) a literal pass-through.
    """
    return f"""(
        -- (A) FLAT rows (backfill form): one trade per record, top-level
        --     keys -- passed through byte-for-byte, so every extraction
        --     built on top of this source behaves exactly as before.
        SELECT ts_exchange_ms, payload_json, FALSE AS is_envelope
        FROM {source}
        WHERE {_IS_FLAT}
        UNION ALL
        -- (B) ENVELOPE rows (live form): explode $.data[*] / $.params.data[*]
        --     into one row per trade, keyed by the PER-TRADE timestamp.
        SELECT COALESCE(TRY_CAST(json_extract_string(elem,'$.T') AS BIGINT),
                        TRY_CAST(json_extract_string(elem,'$.timestamp') AS BIGINT),
                        envelope_ts) AS ts_exchange_ms,
               CAST(elem AS VARCHAR) AS payload_json,
               TRUE AS is_envelope
        FROM (
            SELECT ts_exchange_ms AS envelope_ts,
                   unnest(from_json(
                       CASE WHEN json_type({_ENVELOPE}) = 'ARRAY' THEN {_ENVELOPE}
                            ELSE json_array({_ENVELOPE}) END,
                       '["JSON"]')) AS elem
            FROM {source}
            WHERE {_IS_ENVELOPE}
        )
    )"""


def cross_form_dedup_qualify(trade_id_sql: str = TRADE_ID_SQL) -> str:
    """``QUALIFY`` clause dropping trades present in BOTH payload forms.

    DATASET.md §9 caveat 4: "Backfill/Live-Überlappung an Randdatumen (ein
    Tag kann beide Formen enthalten ⇒ mögliche Doppel-Trades)". Once the
    envelope form is read (it previously fell out silently), such a day
    delivers the same exchange trade twice -- once from the backfill row and
    once from the live envelope element -- which is harmless for a
    last-price-per-bar aggregation but NOT for event streams or signed-size
    sums.

    The rule keeps every flat row and drops an envelope row only when a FLAT
    row with the SAME exchange trade id exists in the same scan. Therefore:

      * a backfill-only partition has no envelope rows  -> no-op,
      * a live-only partition has no flat rows          -> no-op,

    i.e. the clause is a provable no-op outside genuinely mixed partitions,
    which is what keeps the registered flat-form verdicts bit-identical.
    Rows without a trade id (a dialect that carries none) are never dropped
    -- collapsing them by a NULL key would delete real trades.

    NOT covered (documented honestly rather than guessed):

      * duplicates WITHIN one form, e.g. the same live trade re-sent after a
        WS reconnect — that would be a harvester-level defect, and this read
        path deliberately does not silently rewrite within-form data;
      * a venue whose two forms use DIFFERENT id spaces. The clause matches
        on the id string, so if a backfill ``trdMatchID`` and the live ``i``
        of the same trade were ever to differ, the duplicate simply survives
        (the clause degrades to a no-op) — it never drops a WRONG row.

    COST (measured, not guessed): the clause is a hash-partitioned window
    aggregate over the scanned rows, so it roughly DOUBLES the pure load
    query. On a synthetic 2 000 000-trade flat day it moved
    ``c16.load_day_imbalance`` from 1.31 s to 2.41 s and
    ``c17.load_node_trades`` from 0.90 s to 1.89 s — seconds against
    pipelines whose training stages run for hours. Callers that KNOW their
    window is backfill-only can still switch it off explicitly.

    Requires the ``is_envelope`` column of ``trade_rows_sql`` to be in scope.
    """
    return "QUALIFY " + _CROSS_FORM_KEEP.format(tid=trade_id_sql)


__all__ = ["TRADE_ID_SQL", "cross_form_dedup_qualify", "trade_rows_sql"]
