"""DEC-100: ``scripts/h32_build_delisted_tree.py`` / ``h32_fm8.delisted_tree`` on SYNTHETIC Data-Harvest partitions in the
container schema (``symbol`` + ``payload_json`` with the Bybit API row as strings; ``rest.kline1d`` / ``rest.fundingRateAll``,
one partition per day, ``symbol=ALL``): selection, partial candle at the last trading day, a symbol without API data, a
symbol without funding, gaps, relisting rows, the delisting-dates file, the fingerprints and the round trip against the
UNCHANGED ``panel_load.load_panel_union``.  Nothing real is read."""
from __future__ import annotations

import csv
import importlib.util
import json
import math
from argparse import Namespace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from bybit_edge.research.h32_fm8 import artifacts, checks, delisted_tree as dt, schema
from bybit_edge.research.h32_fm8.errors import DataFingerprintError, DelistedTreeError
from bybit_edge.research.wp7_universe import panel_load, panel_store

ROOT = Path(__file__).resolve().parents[2]
DAY_MS = 86_400_000
HEADER = ["symbol", "category", "contractType", "baseCoin", "quoteCoin", "settleCoin", "launch_day", "last_trading_day"]


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name.replace(".py", "_driver"), ROOT / "scripts" / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BUILD = _load_script("h32_build_delisted_tree.py")
H32 = _load_script("h32_fm8.py")


def _ms(d: date) -> int:
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000)


def _days(first: str, last: str):
    d, end = date.fromisoformat(first), date.fromisoformat(last)
    while d <= end:
        yield d
        d += timedelta(days=1)


# ----------------------------------------------------------------------------
# synthetic Data-Harvest world
# ----------------------------------------------------------------------------

def _write_partition(root: Path, stream: str, day: date, rows: list[tuple[str, object]]) -> None:
    d = root / "bybit" / stream / "symbol=ALL" / f"date={day.isoformat()}"
    d.mkdir(parents=True, exist_ok=True)
    n = len(rows)
    table = pa.table({"ts_local_ns": pa.array([0] * n, pa.int64()), "ts_exchange_ms": pa.array([_ms(day)] * n, pa.int64()),
                      "topic": pa.array([stream] * n, pa.string()), "stream": pa.array([stream] * n, pa.string()),
                      "symbol": pa.array([s for s, _ in rows], pa.string()),
                      "payload_json": pa.array([p if isinstance(p, str) else json.dumps(p) for _, p in rows], pa.string())})
    pq.write_table(table, d / "part-0.parquet")


def make_world(tmp: Path, specs: list[dict], extra_register: list[list[str]] | None = None, name: str = "world"):
    """Writes the register CSV and the partitions; returns ``(register, partitions_dir, kline_source, funding_source)`` where
    the sources hold the numbers the builder must reproduce."""
    root = tmp / name
    part = root / "partitions"
    register = root / "register.csv"
    kl_by_day: dict[date, list[tuple[str, object]]] = {}
    fu_by_day: dict[date, list[tuple[str, object]]] = {}
    kl_src: dict[str, dict[date, dict]] = {}
    fu_src: dict[str, list[tuple[int, float]]] = {}
    reg_rows = []
    for k, sp in enumerate(specs):
        sym = sp["symbol"]
        reg_rows.append([sym, sp.get("category", "linear"), "LinearPerpetual", sym[:3], sp.get("quote", "USDT"), sp.get("quote", "USDT"),
                         sp["launch"], sp["last"]])
        if sp.get("no_rows"):
            continue
        first = sp.get("first", sp["launch"])
        last_row = sp.get("last_row", sp["last"])
        kl_src[sym] = {}
        for i, d in enumerate(_days(first, last_row)):
            if d.isoformat() in sp.get("skip", set()):
                continue
            partial = sp.get("partial_last") and d.isoformat() == sp["last"]
            base = 100.0 + k + 0.01 * i
            rec = {"start_ms": _ms(d), "open": base, "high": base + 1.5, "low": base - 0.75, "close": base + 0.25 * ((i % 7) - 3),
                   "volume": (10.0 if partial else 1000.0 + i), "turnover": (1000.0 if partial else 1.0e5 + 17.0 * i)}
            kl_src[sym][d] = rec
            payload = [str(rec["start_ms"])] + [repr(rec[f]) for f in ("open", "high", "low", "close", "volume", "turnover")]
            kl_by_day.setdefault(d, []).append((sym, payload))
        for d in sp.get("before", []):
            dd = date.fromisoformat(d)
            payload = [str(_ms(dd)), "1.0", "2.0", "0.5", "1.5", "5.0", "7.0"]
            kl_by_day.setdefault(dd, []).append((sym, payload))
            kl_src[sym][dd] = {"start_ms": _ms(dd), "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 5.0, "turnover": 7.0}
        if sp.get("funding"):
            fu_src[sym] = []
            fend = date.fromisoformat(sp.get("funding_last", sp["last"]))
            for i, d in enumerate(_days(first, fend.isoformat())):
                hours = (0, 8, 16) if i % 40 != 5 else tuple(range(24))                 # a 1h-funding stretch now and then
                for h in hours:
                    ts = _ms(d) + h * 3_600_000
                    rate = 1e-4 * (((i + h) % 5) - 2)
                    fu_src[sym].append((ts, rate))
                    fu_by_day.setdefault(d, []).append((sym, {"symbol": sym, "fundingRate": repr(rate), "fundingRateTimestamp": str(ts)}))
    for d, rows in kl_by_day.items():
        _write_partition(part, dt.STREAM_KLINE, d, rows)
    for d, rows in fu_by_day.items():
        _write_partition(part, dt.STREAM_FUNDING, d, rows)
    register.parent.mkdir(parents=True, exist_ok=True)
    with register.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER)
        w.writerows(reg_rows + (extra_register or []))
    return register, part, kl_src, fu_src


FULL_SPECS = [
    dict(symbol="AAAUSDT", launch="2022-03-10", last="2022-09-15", funding=True, partial_last=True),
    dict(symbol="BBBUSDT", launch="2021-06-01", last="2023-02-20", skip={"2022-04-04"}, before=["2020-12-31"]),   # a gap, no funding
    dict(symbol="CCCUSDT", launch="2022-05-01", last="2022-05-20", no_rows=True),                               # the API delivered nothing
    dict(symbol="GGGUSDT", launch="2022-02-01", last="2022-08-10", last_row="2022-09-05", funding=True, funding_last="2022-08-20"),
    dict(symbol="HHHUSDT", launch="2021-03-01", last="2021-03-31", funding=True),
    dict(symbol="FFFUSDT", launch="2022-01-01", last="2026-09-10", last_row="2022-01-10", funding=True, funding_last="2022-01-10"),  # after the cut
    dict(symbol="DDDUSDC", launch="2022-01-01", last="2022-02-01", quote="USDC", last_row="2022-01-05"),      # not USDT
    dict(symbol="EEEUSD", category="inverse", launch="2022-01-01", last="2022-02-01", quote="USD", last_row="2022-01-05"),
]
CLEAN_SPECS = [FULL_SPECS[0], FULL_SPECS[3], FULL_SPECS[4]]
CUT = "2026-06-28"


@pytest.fixture(scope="module")
def full(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("dt_full")
    register, part, kl, fu = make_world(tmp, FULL_SPECS)
    out = tmp / "tree"
    report = dt.build_tree(register, part, out, cut=CUT)
    return {"tmp": tmp, "register": register, "part": part, "kl": kl, "fu": fu, "out": out, "report": report}


@pytest.fixture(scope="module")
def clean(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("dt_clean")
    register, part, kl, fu = make_world(tmp, CLEAN_SPECS)
    out = tmp / "tree"
    report = dt.build_tree(register, part, out, cut=CUT)
    return {"tmp": tmp, "register": register, "part": part, "kl": kl, "fu": fu, "out": out, "report": report}


def _survivors(tmp: Path, first: str, last: str) -> tuple[Path, Path]:
    """A tiny survivors tree (BTCUSDT, ETHUSDT) with complete DONE years."""
    base, man = tmp / "panel_1d", tmp / "panel_1d" / "panel_manifest.sqlite"
    for k, sym in enumerate(("BTCUSDT", "ETHUSDT")):
        by_year: dict[int, list[dict]] = {}
        for i, d in enumerate(_days(first, last)):
            by_year.setdefault(d.year, []).append({"start_ms": _ms(d), "open": 1.0, "high": 2.0, "low": 0.5, "close": 100.0 + k + 0.1 * i,
                                                   "volume": 10.0, "turnover": 100.0, "funding_n": 3, "funding_sum": 0.0003})
        for y, rows in by_year.items():
            panel_store.write_year_partition(base, man, sym, y, rows, listing_date=date.fromisoformat(first),
                                             as_of_date=date.fromisoformat(last), frozen=True)
    return base, man


# ----------------------------------------------------------------------------
# register and selection
# ----------------------------------------------------------------------------

def test_register_selection_is_linear_usdt_up_to_the_cut(full):
    rows = dt.read_register(full["register"])
    assert len(rows) == len(FULL_SPECS)
    assert [r["symbol"] for r in dt.select_symbols(rows, "2026-09-28")] == ["AAAUSDT", "BBBUSDT", "CCCUSDT", "FFFUSDT", "GGGUSDT", "HHHUSDT"]
    assert [r["symbol"] for r in dt.select_symbols(rows, CUT)] == ["AAAUSDT", "BBBUSDT", "CCCUSDT", "GGGUSDT", "HHHUSDT"]    # FFF ends after the cut
    assert full["report"]["symbols"] == ["AAAUSDT", "BBBUSDT", "CCCUSDT", "GGGUSDT", "HHHUSDT"]            # no USDC, no inverse
    assert dt.select_symbols(rows, "2021-01-01") == []


def test_register_errors_are_loud(tmp_path):
    def reg(text: str) -> Path:
        p = tmp_path / f"r{len(list(tmp_path.glob('r*.csv')))}.csv"
        p.write_text(text, encoding="utf-8")
        return p
    good = "symbol,category,contractType,baseCoin,quoteCoin,settleCoin,launch_day,last_trading_day\n"
    with pytest.raises(DelistedTreeError, match="columns missing"):
        dt.read_register(reg("symbol,category\nA,linear\n"))
    with pytest.raises(DelistedTreeError, match="twice"):
        dt.read_register(reg(good + "A,linear,L,A,USDT,USDT,2022-01-01,2022-02-01\nA,linear,L,A,USDT,USDT,2022-01-01,2022-02-01\n"))
    with pytest.raises(DelistedTreeError, match="ISO date"):
        dt.read_register(reg(good + "A,linear,L,A,USDT,USDT,2022-13-01,2022-02-01\n"))
    with pytest.raises(DelistedTreeError, match="before launch_day"):
        dt.read_register(reg(good + "A,linear,L,A,USDT,USDT,2022-03-01,2022-02-01\n"))
    with pytest.raises(DelistedTreeError, match="no rows"):
        dt.read_register(reg(good))
    with pytest.raises(DelistedTreeError, match="not found"):
        dt.read_register(tmp_path / "none.csv")
    with pytest.raises(Exception):
        artifacts.refuse_unsafe_path(tmp_path / "weekly_ic_series.csv")
    # an announcement_day column is optional and kept as a label
    rows = dt.read_register(reg(good.strip() + ",announcement_day\nA,linear,L,A,USDT,USDT,2022-01-01,2022-02-01,2022-01-20\n"))
    assert rows[0]["announcement_day"] == "2022-01-20"


# ----------------------------------------------------------------------------
# the tree
# ----------------------------------------------------------------------------

def test_tree_layout_manifest_and_named_gaps(full):
    out, rep = full["out"], full["report"]
    assert (out / "frozen/source=bybit/category=linear/symbol=AAAUSDT/year=2022/part.parquet").is_file()
    assert (out / dt.MANIFEST_FILE).is_file() and (out / dt.DELISTING_DATES_FILE).is_file() and (out / dt.FINGERPRINT_FILE).is_file()
    assert (out / dt.REGISTER_COPY).read_bytes() == full["register"].read_bytes()                         # verbatim copy
    assert not list(out.glob("open"))                                                                       # a dead symbol has no open year
    assert rep["no_history_symbols"] == {"CCCUSDT": "no_api_rows"} and rep["funding_missing_symbols"] == ["BBBUSDT"]
    assert rep["dropped_after_last_trading_day"] == {"GGGUSDT": {"n_rows": 26, "first": "2022-08-11", "last": "2022-09-05"}}
    assert rep["dropped_before_start_year"] == {"BBBUSDT": 1}
    nd = {(p["symbol"], p["year"]): p for p in rep["not_done_partitions"]}
    assert set(nd) == {("BBBUSDT", 2022)} and nd[("BBBUSDT", 2022)]["status"] == "PARTIAL"
    assert nd[("BBBUSDT", 2022)]["missing_days"] == 1 and nd[("BBBUSDT", 2022)]["missing_head"] == ["2022-04-04"]
    assert rep["status_counts"] == {"DONE": 5, "PARTIAL": 1, "FAILED": 1}           # AAA 1, BBB 2021 + 2023 (2022 PARTIAL), GGG 1, HHH 1, CCC marker
    assert rep["n_partitions"] == 6
    assert rep["n_symbols"] == 5 and rep["n_symbols_with_history"] == 4
    assert rep["rows_of_symbols_not_in_the_selection"]["rest.kline1d"] > 0                                  # FFF / DDD rows are only counted
    assert rep["first_last_candle"]["AAAUSDT"] == {"first_candle": "2022-03-10", "last_candle": "2022-09-15"}


def test_delisting_dates_come_from_the_register_with_the_last_trading_day(full):
    payload = json.loads((full["out"] / "delisting_dates.json").read_text(encoding="utf-8"))
    assert payload["n_symbols"] == 5 and set(payload["symbols"]) == set(full["report"]["symbols"])
    a = payload["symbols"]["AAAUSDT"]
    assert a["delist_date"] == "2022-09-15" and a["source"] == "data_harvest_register" and a["announcement_id"] is None
    assert a["launch_day"] == "2022-03-10" and "announcement_day" not in a
    assert payload["symbols"]["CCCUSDT"]["delist_date"] == "2022-05-20"                                     # also the symbol without API data
    assert panel_load.load_delisting_dates(full["out"] / "delisting_dates.json")["GGGUSDT"] == date(2022, 8, 10)


def test_round_trip_against_the_unchanged_union_loader(clean, tmp_path):
    base, man = _survivors(tmp_path, "2021-01-01", "2023-03-01")
    rep = clean["report"]
    assert rep["status_counts"] == {"DONE": 3} and not rep["not_done_partitions"] and not rep["no_history_symbols"]
    panel = panel_load.load_panel_union(base, man, clean["out"], clean["out"] / dt.MANIFEST_FILE, year_start=2021, year_end=2023,
                                        as_of=date(2023, 3, 1), delisting_dates_path=clean["out"] / "delisting_dates.json")
    assert panel["symbols"] == ["AAAUSDT", "BTCUSDT", "ETHUSDT", "GGGUSDT", "HHHUSDT"]
    assert panel["delisted_symbols"] == ["AAAUSDT", "GGGUSDT", "HHHUSDT"] and bool(panel["is_delisted"][0]) and not bool(panel["is_delisted"][1])
    j = {s: panel["symbols"].index(s) for s in panel["symbols"]}
    assert panel["last_alive_day"][j["AAAUSDT"]] == "2022-09-15" and panel["last_alive_day"][j["GGGUSDT"]] == "2022-08-10"
    pos = {d: i for i, d in enumerate(panel["dates"])}
    # every candle of the source is in the panel, bit for bit; nothing after the last trading day, nothing invented
    for sym, src in clean["kl"].items():
        col = j[sym]
        last = date.fromisoformat(next(r["last_trading_day"] for r in dt.read_register(clean["register"]) if r["symbol"] == sym))
        for d, rec in src.items():
            if d <= last:
                assert panel["close"][pos[d.isoformat()], col] == rec["close"] and panel["turnover"][pos[d.isoformat()], col] == rec["turnover"]
            elif d.isoformat() in pos:
                assert math.isnan(panel["close"][pos[d.isoformat()], col])
        assert int(np.isfinite(panel["close"][:, col]).sum()) == sum(1 for d in src if d <= last)
    # the partial candle of the last trading day is kept as delivered
    a_last = clean["kl"]["AAAUSDT"][date(2022, 9, 15)]
    assert a_last["turnover"] == 1000.0 and panel["turnover"][pos["2022-09-15"], j["AAAUSDT"]] == 1000.0
    assert math.isnan(panel["close"][pos["2022-09-16"], j["AAAUSDT"]])
    # funding per day exactly as panel_store.merge_funding_daily: settlements counted from the real timestamps
    stats = panel_store.daily_funding_stats([{"funding_rate": r, "ts_ms": t} for t, r in clean["fu"]["AAAUSDT"]])
    for d, rec in stats.items():
        if d in pos:
            assert panel["funding_n"][pos[d], j["AAAUSDT"]] == rec["funding_n"] and panel["funding_sum"][pos[d], j["AAAUSDT"]] == rec["funding_sum"]
    assert {panel["funding_n"][pos[d.isoformat()], j["AAAUSDT"]] for d in clean["kl"]["AAAUSDT"]} >= {3.0, 24.0}   # 8h and 1h stretches
    # GGG funding stops 2022-08-20, after its last trading day: those settlements are not in the tree
    assert np.isnan(panel["funding_n"][pos["2022-08-11"], j["GGGUSDT"]]) if "2022-08-11" in pos else True


def test_full_build_gap_is_loud_in_the_union_loader_until_allow_partial_and_the_no_history_symbol_is_absent(full, tmp_path):
    base, man = _survivors(tmp_path, "2021-01-01", "2023-03-01")
    kw = dict(year_start=2021, year_end=2023, as_of=date(2023, 3, 1), delisting_dates_path=full["out"] / "delisting_dates.json")
    with pytest.raises(panel_load.PanelLoadError, match="PARTIAL"):
        panel_load.load_panel_union(base, man, full["out"], full["out"] / dt.MANIFEST_FILE, **kw)
    panel = panel_load.load_panel_union(base, man, full["out"], full["out"] / dt.MANIFEST_FILE, allow_partial=True, **kw)
    assert "CCCUSDT" not in panel["symbols"] and panel["n_no_history_only"] == 1
    j = panel["symbols"].index("BBBUSDT")
    pos = {d: i for i, d in enumerate(panel["dates"])}
    assert math.isnan(panel["close"][pos["2022-04-04"], j])                                                  # the gap stays a gap
    assert np.isnan(panel["funding_n"][:, j]).all()                                                          # no funding delivered: None, never 0
    assert "2020-12-31" not in pos                                                                          # before start_year: dropped and named


def test_tree_is_deterministic_and_never_overwritten(clean, tmp_path):
    again = dt.build_tree(clean["register"], clean["part"], tmp_path / "tree2", cut=CUT)
    assert again["tree_sha256"] == clean["report"]["tree_sha256"] and again["files"] == clean["report"]["files"]
    assert (tmp_path / "tree2" / "delisting_dates.json").read_bytes() == (clean["out"] / "delisting_dates.json").read_bytes()
    with pytest.raises(DelistedTreeError, match="not empty"):
        dt.build_tree(clean["register"], clean["part"], clean["out"], cut=CUT)
    with pytest.raises(ValueError, match="data/harvest"):
        dt.build_tree(clean["register"], clean["part"], tmp_path / "data/harvest/x", cut=CUT)
    with pytest.raises(DelistedTreeError, match="listing_anchor"):
        dt.build_tree(clean["register"], clean["part"], tmp_path / "t3", cut=CUT, listing_anchor="nope")
    with pytest.raises(DelistedTreeError, match="no register row"):
        dt.build_tree(clean["register"], clean["part"], tmp_path / "t4", cut="2021-01-01")


def test_listing_anchor_register_is_strict_and_observed_anchors_at_the_first_candle(tmp_path):
    specs = [dict(symbol="LATEUSDT", launch="2022-03-01", first="2022-03-04", last="2022-06-30", funding=True)]
    register, part, kl, _ = make_world(tmp_path, specs, name="late")
    strict = dt.build_tree(register, part, tmp_path / "strict", cut=CUT)
    assert [p["status"] for p in strict["not_done_partitions"]] == ["PARTIAL"] and strict["not_done_partitions"][0]["missing_head"] == ["2022-03-01", "2022-03-02", "2022-03-03"]
    obs = dt.build_tree(register, part, tmp_path / "obs", cut=CUT, listing_anchor="observed")
    assert obs["not_done_partitions"] == [] and obs["status_counts"] == {"DONE": 1}


def test_a_year_without_rows_although_days_are_expected_is_failed_and_named(tmp_path):
    specs = [dict(symbol="HOLEUSDT", launch="2021-06-01", last="2023-03-31", funding=True)]
    register, part, kl, _ = make_world(tmp_path, specs, name="hole")
    for d in list(_days("2022-01-01", "2022-12-31")):                                       # remove the whole year 2022 from the partitions
        for f in (part / "bybit" / dt.STREAM_KLINE / "symbol=ALL" / f"date={d.isoformat()}").glob("*.parquet"):
            f.unlink()
    rep = dt.build_tree(register, part, tmp_path / "hole_tree", cut=CUT)
    nd = {(p["symbol"], p["year"]): p for p in rep["not_done_partitions"]}
    assert nd[("HOLEUSDT", 2022)]["status"] == "FAILED" and nd[("HOLEUSDT", 2022)]["reason"] == "GAP_NO_ROWS" and nd[("HOLEUSDT", 2022)]["missing_days"] == 365
    assert rep["status_counts"] == {"DONE": 2, "FAILED": 1}
    assert not (tmp_path / "hole_tree/frozen/source=bybit/category=linear/symbol=HOLEUSDT/year=2022").exists()


# ----------------------------------------------------------------------------
# reading the partitions
# ----------------------------------------------------------------------------

def _mini(tmp_path: Path, kline_rows: list[tuple[str, object]], funding_rows: list[tuple[str, object]] | None = None, day="2022-03-10"):
    part = tmp_path / "mini"
    d = date.fromisoformat(day)
    _write_partition(part, dt.STREAM_KLINE, d, kline_rows)
    _write_partition(part, dt.STREAM_FUNDING, d, funding_rows or [("AAAUSDT", {"symbol": "AAAUSDT", "fundingRate": "0.0001", "fundingRateTimestamp": str(_ms(d))})])
    return part


def _k(day: str, close: str = "1.5"):
    return [str(_ms(date.fromisoformat(day))), "1.0", "2.0", "0.5", close, "5.0", "7.0"]


def test_reader_identical_duplicates_are_counted_and_differing_ones_are_loud(tmp_path):
    part = _mini(tmp_path, [("AAAUSDT", _k("2022-03-10")), ("AAAUSDT", _k("2022-03-10"))])
    rows, stat = dt.read_klines(part, ["AAAUSDT"])
    assert stat["n_identical_duplicates"] == 1 and len(rows["AAAUSDT"]) == 1
    part2 = _mini(tmp_path / "b", [("AAAUSDT", _k("2022-03-10")), ("AAAUSDT", _k("2022-03-10", close="1.6"))])
    with pytest.raises(DelistedTreeError, match="DIFFERENT"):
        dt.read_klines(part2, ["AAAUSDT"])
    d = date(2022, 3, 10)
    f_dup = [("AAAUSDT", {"symbol": "AAAUSDT", "fundingRate": "0.0001", "fundingRateTimestamp": str(_ms(d))})] * 2
    part3 = _mini(tmp_path / "c", [("AAAUSDT", _k("2022-03-10"))], f_dup)
    assert dt.read_funding(part3, ["AAAUSDT"])[1]["n_identical_duplicates"] == 1
    f_bad = [("AAAUSDT", {"symbol": "AAAUSDT", "fundingRate": "0.0001", "fundingRateTimestamp": str(_ms(d))}),
             ("AAAUSDT", {"symbol": "AAAUSDT", "fundingRate": "0.0002", "fundingRateTimestamp": str(_ms(d))})]
    with pytest.raises(DelistedTreeError, match="DIFFERENT"):
        dt.read_funding(_mini(tmp_path / "d", [("AAAUSDT", _k("2022-03-10"))], f_bad), ["AAAUSDT"])


def test_reader_layout_errors_are_loud(tmp_path):
    with pytest.raises(DelistedTreeError, match="not attributable"):
        dt.read_klines(_mini(tmp_path / "a", [("ALL", _k("2022-03-10"))]), ["AAAUSDT"])
    with pytest.raises(DelistedTreeError, match="Bybit layout"):
        dt.read_klines(_mini(tmp_path / "b", [("AAAUSDT", ["1", "2", "3"])]), ["AAAUSDT"])
    with pytest.raises(DelistedTreeError, match="Bybit layout"):
        dt.read_klines(_mini(tmp_path / "c", [("AAAUSDT", "not json")]), ["AAAUSDT"])
    with pytest.raises(DelistedTreeError, match="day boundary"):
        dt.read_klines(_mini(tmp_path / "d", [("AAAUSDT", [str(_ms(date(2022, 3, 10)) + 3_600_000), "1", "2", "0.5", "1.5", "5", "7"])]), ["AAAUSDT"])
    d = date(2022, 3, 10)
    with pytest.raises(DelistedTreeError, match="payload symbol"):
        dt.read_funding(_mini(tmp_path / "e", [("AAAUSDT", _k("2022-03-10"))],
                              [("AAAUSDT", {"symbol": "BBBUSDT", "fundingRate": "0.0001", "fundingRateTimestamp": str(_ms(d))})]), ["AAAUSDT", "BBBUSDT"])
    with pytest.raises(DelistedTreeError, match="Bybit layout"):
        dt.read_funding(_mini(tmp_path / "f", [("AAAUSDT", _k("2022-03-10"))], [("AAAUSDT", {"symbol": "AAAUSDT"})]), ["AAAUSDT"])
    (tmp_path / "empty_dir_that_exists").mkdir()
    with pytest.raises(DelistedTreeError, match="no partitions of the stream"):
        dt.read_klines(tmp_path / "empty_dir_that_exists", ["AAAUSDT"])
    with pytest.raises(DelistedTreeError, match="not found"):
        dt.read_klines(tmp_path / "nope", ["AAAUSDT"])
    # a funding row whose column symbol is ALL takes its symbol from the payload
    part = _mini(tmp_path / "g", [("AAAUSDT", _k("2022-03-10"))], [("ALL", {"symbol": "AAAUSDT", "fundingRate": "0.0001", "fundingRateTimestamp": str(_ms(d))})])
    assert list(dt.read_funding(part, ["AAAUSDT"])[0]) == ["AAAUSDT"]
    # the stream directory may be the root itself or any depth below it
    assert list(dt.read_klines(part / "bybit" / dt.STREAM_KLINE, ["AAAUSDT"])[0]) == ["AAAUSDT"]


# ----------------------------------------------------------------------------
# fingerprints
# ----------------------------------------------------------------------------

def test_fingerprint_pins_the_register_and_every_parquet_and_detects_tampering(clean, tmp_path):
    import shutil
    tree = tmp_path / "tree"
    shutil.copytree(clean["out"], tree)
    ok = dt.verify_tree(tree)
    assert ok["tree_sha256"] == clean["report"]["tree_sha256"] and ok["register_sha256"] == artifacts.sha256_file(clean["register"]) and ok["n_files"] == 3
    obs = dt.observed_tree_fingerprints(tree)
    assert obs == {"delisting_register_sha256": artifacts.sha256_file(clean["register"]), "delisted_tree_sha256": ok["tree_sha256"]}
    part = next(tree.rglob("part.parquet"))
    original = part.read_bytes()
    part.write_bytes(original[:-9] + b"X" + original[-8:])
    with pytest.raises(DelistedTreeError, match="changed"):
        dt.verify_tree(tree)
    with pytest.raises(DelistedTreeError):
        dt.observed_tree_fingerprints(tree)
    part.write_bytes(original)
    dt.verify_tree(tree)
    part.unlink()
    with pytest.raises(DelistedTreeError, match="missing"):
        dt.verify_tree(tree)
    part.write_bytes(original)
    extra = tree / "frozen/source=bybit/category=linear/symbol=ZZZUSDT/year=2022/part.parquet"
    extra.parent.mkdir(parents=True)
    extra.write_bytes(original)
    with pytest.raises(DelistedTreeError, match="extra"):
        dt.verify_tree(tree)
    extra.unlink()
    (tree / dt.REGISTER_COPY).write_text("symbol\n", encoding="utf-8")
    with pytest.raises(DelistedTreeError, match="register copy differs"):
        dt.verify_tree(tree)
    # a legacy tree (no register copy, no fingerprint file) yields None -- the registration then refuses it
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    assert dt.observed_tree_fingerprints(legacy) == {"delisting_register_sha256": None, "delisted_tree_sha256": None}
    with pytest.raises(DelistedTreeError):
        dt.verify_tree(legacy)


def test_data_fingerprint_check_pins_the_register_and_optionally_the_tree(clean):
    fp = {"union_range_fingerprint": "ab" * 32, "delisting_dates_sha256": "cd" * 32,
          "delisting_register_sha256": artifacts.sha256_file(clean["register"])}
    reg = {"data_fingerprints": dict(fp)}
    checks.check_data_fingerprints(reg, dict(fp))
    with pytest.raises(DataFingerprintError, match="delisting_register_sha256"):
        checks.check_data_fingerprints(reg, {**fp, "delisting_register_sha256": "00" * 32})
    with pytest.raises(DataFingerprintError, match="delisting_register_sha256"):
        checks.check_data_fingerprints(reg, {k: v for k, v in fp.items() if k != "delisting_register_sha256"})
    reg_t = {"data_fingerprints": {**fp, "delisted_tree_sha256": clean["report"]["tree_sha256"]}}
    checks.check_data_fingerprints(reg_t, {**fp, "delisted_tree_sha256": clean["report"]["tree_sha256"]})
    with pytest.raises(DataFingerprintError, match="delisted_tree_sha256"):
        checks.check_data_fingerprints(reg_t, {**fp, "delisted_tree_sha256": "00" * 32})
    checks.check_data_fingerprints(reg, {**fp, "delisted_tree_sha256": "00" * 32})                       # not pinned: not compared


def test_h32_union_loader_quotes_the_register_fingerprint_and_refuses_a_tampered_tree(clean, tmp_path):
    import shutil
    base, _man = _survivors(tmp_path, "2021-01-01", "2023-03-01")
    tree = tmp_path / "tree"
    shutil.copytree(clean["out"], tree)
    ns = Namespace(panel_base=str(base), delisted_base=str(tree), delisted_manifest="", delisting_dates="", start_year=2021, end_year=2023,
                   as_of="2023-03-01", allow_partial=False)
    loaded = H32.load_union_panel(ns)
    assert loaded is not None
    panel, observed = loaded
    assert observed["delisting_register_sha256"] == artifacts.sha256_file(clean["register"])
    assert observed["delisted_tree_sha256"] == clean["report"]["tree_sha256"]
    assert observed["delisting_dates_sha256"] == artifacts.sha256_file(tree / "delisting_dates.json")
    assert schema.is_hex64(observed["union_range_fingerprint"]) and panel["delisted_symbols"] == ["AAAUSDT", "GGGUSDT", "HHHUSDT"]
    (tree / dt.REGISTER_COPY).write_text("symbol\n", encoding="utf-8")                                    # register copy no longer the fingerprinted one
    assert H32.load_union_panel(ns) is None                                                              # tampered: loud fail, no panel
    legacy_ns = Namespace(**{**vars(ns), "delisted_base": str(clean["tmp"] / "legacy_missing")})
    assert H32.load_union_panel(legacy_ns) is None


# ----------------------------------------------------------------------------
# the script
# ----------------------------------------------------------------------------

def test_script_rc_0_clean_3_named_gaps_1_abort(clean, full, tmp_path, capsys):
    args = ["--register", str(clean["register"]), "--partitions-dir", str(clean["part"]), "--cut", CUT]
    assert BUILD.main([*args, "--out", str(tmp_path / "t_clean")]) == 0
    assert (tmp_path / "t_clean" / dt.FINGERPRINT_FILE).is_file()
    err = capsys.readouterr().err
    assert "Baum sha256" in err and "Register sha256" in err and "NO_HISTORY" not in err
    gaps = ["--register", str(full["register"]), "--partitions-dir", str(full["part"]), "--cut", CUT]
    assert BUILD.main([*gaps, "--out", str(tmp_path / "t_gaps")]) == 3
    err = capsys.readouterr().err
    assert "NO_HISTORY" in err and "CCCUSDT" in err and "BBBUSDT/2022=PARTIAL" in err and "ohne Funding" in err and "Wiederlistung" in err
    assert BUILD.main([*gaps, "--out", str(tmp_path / "t_gaps")]) == 1                                  # not empty
    assert BUILD.main(["--register", str(tmp_path / "none.csv"), "--partitions-dir", str(clean["part"]), "--cut", CUT, "--out", str(tmp_path / "x")]) == 1
    assert BUILD.main([*args, "--out", str(tmp_path / "data/harvest/never")]) == 1
    assert not (tmp_path / "data/harvest/never").exists()
    assert BUILD.main([*args, "--cut", "2026-13-40", "--out", str(tmp_path / "y")]) == 1
    with pytest.raises(SystemExit):
        BUILD.main(["--register", str(clean["register"])])


def test_script_output_feeds_the_registration_fingerprints_end_to_end(clean, tmp_path):
    """The tree written by the script is read by the h32 loader, and the register hash it quotes is the one a registration
    pins (template -> schema)."""
    import shutil
    base, _man = _survivors(tmp_path, "2021-01-01", "2023-03-01")
    tree = tmp_path / "tree"
    shutil.copytree(clean["out"], tree)
    ns = Namespace(panel_base=str(base), delisted_base=str(tree), delisted_manifest="", delisting_dates="", start_year=2021, end_year=2023,
                   as_of="2023-03-01", allow_partial=False)
    _panel, observed = H32.load_union_panel(ns)
    fp = {k: observed[k] for k in ("union_range_fingerprint", "delisting_dates_sha256", "delisting_register_sha256")}
    assert all(schema.is_hex64(v) for v in fp.values())
    checks.check_data_fingerprints({"data_fingerprints": fp}, observed)
