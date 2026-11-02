"""A2 preparatory work (EXP-CLOCK): placebo design under daily expiries and sigma30 nuisance of the
pre-period -- shared rules, loaders and guards.  OPTION-NEUTRAL, NO VERDICT, NO MEAN.

PRE-FIXED RULES (written BEFORE any statistic of the 1-min data or of the settlement positions was
computed; deviations only with reason and fork direction, pattern DEC-93 H-1):

R-1  Time limits.  Returns only from the kline extracts 2021-03-24..2024-05-31 (assert at load, before
     any return is formed: no UTC day > 2024-05-31).  Calendar and position (OI) quantities only for
     expiry dates <= 2026-06-30: raw settlement partitions with date > 2026-06-30 are never opened,
     calendar rows after 2026-06-30 are dropped at load (assert).  No sealed file, no harvest client,
     nothing under data/harvest, nothing downloaded or listed remotely.
R-2  Raw settlement partitions (deribit/rest.settlements): ONLY the payload fields type,
     instrument_name, timestamp, position are extracted, by Arrow regex extraction on the payload
     buffer (``FieldGuard``); the payload is never JSON-decoded, no price field ever becomes a value
     object; the guard raises on index_price / mark_price / profit_loss / any *price* / *profit* key
     and on any key outside the allow-list (self-test at import).  Use: option deliveries only;
     position = delivered contracts (coin units, inverse options) -> only counts and sums.
R-3  Return grid (as HF-RV R-3): the price at grid time tau is the close of the 1-min candle that ENDS
     at tau (candle start tau - 1 min).  r_pre(d) = ln(C[07:59] / C[07:29]) ("cc", [07:30, 08:00));
     report-only alternative r_pre_oc = ln(C[07:59] / O[07:30]).  r_post = ln(C[08:59] / C[07:59])
     ([08:00, 09:00), report only).  Shift slots k in {-3,-2,-1,+1,+2,+3} h: [07:30+k, 08:00+k);
     fixed comparison slot [15:30, 16:00) (before the 16:00 funding, no option TWAP).  Profile: all
     48 half-hour slots; slot 00:00 uses C[23:59] of the previous day.  Units bp (1e4 x log return).
     Day completeness as HF-RV R-2 (1,440 minutes); incomplete day -> all its slots missing.
R-4  Day classes from the Deribit calendar (rule C-3 of a2_census, re-checked here: every day of the
     pre-period must carry option deliveries of BTC AND ETH): FRI_W weekly-only Friday, FRI_M monthly
     (not quarter), FRI_Q quarterly, FRI = W+M+Q, FRI_MQ = M+Q, MODO = Mon-Thu (daily expiry only),
     WE = Sat/Sun (daily expiry only), ALL = every day.  Outlier days (any option delivery booked
     > 60 s after 08:00:00 UTC) are excluded from every event and placebo set (rule fixed now; count
     reported).
R-5  Statistics per class and per symbol (BTC, ETH), for the cluster series x = (r_BTC + r_ETH) / 2
     (DEC-67: one expiry = one cluster) and the pooled sigma sqrt((s_BTC^2 + s_ETH^2) / 2): n, SD
     (ddof 1), MAD / 1.4826 (centre never output), excess kurtosis, quantiles q50/q90/q95/q99 of |r|
     (dispersion only); by calendar year 2021 / 2022 / 2023 / 2024 (2024 up to 05-31).
R-6  SD ratios (FRI/MODO, WE/MODO, FRI/WE, FRI_MQ/FRI_W, FRI_W/MODO, FRI_MQ/MODO, P3fix/MODO slot pre,
     pre/P3fix same days, shift-slot/pre on ALL days, r_post-per-30min/pre) with a bootstrap band:
     ISO-week blocks resampled iid (all classes jointly, keeps the common vol regime and the pairing),
     2,000 replicates, seed 27; bands = percentiles 2.5/97.5 and 5/95.
R-7  rho(BTC, ETH) per class: Pearson and Spearman on the same slot and day; week-block bootstrap band
     (same replicates as R-6).
R-8  Autocorrelation over consecutive events of a class (chronological, missing days dropped): ACF
     lags 1..10 of x (and of x^2 as vol-clustering report).  Variance factor of an event-mean
     statistic, P-3 logic: candidates Bartlett (power_p1.variance_factor) B in {4, 8, 13} and batch
     means L in {4, 8, 13} (only where n / L >= 8); c_bind = max(1, candidates); stationary bootstrap
     (power_p1.stationary_bootstrap_se, mean block 4 and 8, 2,000 replicates, seed 27) report only.
R-9  SE per design (B-4): SE_E = SD(x_E) sqrt(c_E / N_E), SE_P = SD(x_P) sqrt(c_P / N_P), class SDs
     of the pre-period; SE(contrast) = sqrt(SE_E^2 + SE_P^2 - 2 Cov), the covariance term is used
     ONLY if it raises the SE (measured cross-correlation < 0; no credit, analogous to DEC-94 (4));
     paired same-day placebo: SD of the per-day difference.  Binding placebo = largest SE(contrast)
     (PRD 5.2).  Stress line: the calendar year with the largest class SD (Strenge); the smallest
     year is report.  The Bilanz formula [pb:A2] is evaluated alongside with the measured pooled
     sigma and rho.  N per 12-month window from the calendar (W1 2024-07-01..2025-06-30, W2
     2025-07-01..2026-06-28 after DEC-99 (8); 2025-07..2026-06 shown as well), event counts only.
R-10 Power with power_p1 only: MDE80 = power_p1.mde80(SE, 1.6449) (P-1) and mde80(SE, 2.4865)
     (A3 practice, DEC-94 (9)); window power power_p1.window_power; regime power_p1.assign_regime /
     assign_regime_a3_practice on two equal windows; prior grid 5 / 8 / 12 / 16.5 / 25 bp; window
     length (years) for C10 by bisection on power_p1.window_power with SE(L) = SE_12m / sqrt(L).
     For size contrasts (event vs smaller expiry) a second prior line assumes the effect is
     proportional to delivered contracts: prior_contrast = prior x (1 - OI_P / OI_E) with the q50
     OI ratio of A-2 (assumption UNBELEGT, direction Strenge against the unattenuated line).
R-11 Every output dict passes h27_common.no_mean and guard_keys below (refuses mean / avg / mittel /
     sign / vorzeichen / effect / delta / drift / r_pre_mean ... keys); LABEL in every file;
     deterministic (fixed seeds; two runs, same sha256).
FASSUNG 2 (2026-10-29, review conditions A-1..A-6, written before any new number):
R-12 Extended guard (A-6): additionally refuses location-type key segments median / q50 / loc / location /
     center / centre / diff / difference / contrast / minus, unless the full key path matches the
     documented allow-list ``_LOC_ALLOW`` (counts and OI quantiles of part A, the c_bind iid reference,
     SE / prior keys of a contrast, the names of difference SERIES that carry only dispersion).  Under a
     difference series (path segment contains minus / diff / did) every key abs_q* (uncentred
     absolute quantile) is refused -- difference series carry SD, 1.4826 x MAD, kurtosis only.
R-13 Kline date assert on ``start_ms`` alone (pyarrow column read) BEFORE any price column is read
     (``assert_kline_dates``), then the unchanged HF-RV loader.
R-14 Futures calendar (A-3): raw settlement partitions <= 2026-06-30, fields type / instrument_name /
     timestamp only (FieldGuard), future deliveries by name CCY-DDMMMYY; no position, no price.
R-15 Conjunction (A-1): contrasts Delta_j = event mean - placebo_j mean; Cov(Delta_j, Delta_k) = SE_E^2 +
     Cov(placebo_j mean, placebo_k mean) with Cov = rho_jk SE_j SE_k n_common / sqrt(N_j N_k) (rho_jk =
     measured same-day correlation of the two placebo cluster series on their common days, 0 if no
     common day); event-placebo covariance 0 (no credit, R-9).  Joint power = Monte Carlo
     P(all Delta_j >= 1.6449 SE_j), 400,000 draws, seed 94; product of single powers = lower bound.
     Assignment (C10 / DEC52 / GL012) by the PRODUCT (orchestrator decision, analogous to DEC-94 (6)),
     joint power = report.  MDE80 on the event scale by bisection (common random numbers).
"""
from __future__ import annotations

import calendar
import glob
import hashlib
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
SCRATCH = HERE.parent
sys.path.insert(0, str(SCRATCH / "hfrv_herleitung"))
sys.path.insert(0, "/home/user/scinance/src")
from h27_common import no_mean, RV_LAST_PRICE_DAY, assert_rv_day  # noqa: E402
import hfrv_common as hc  # noqa: E402  (load_kline: R-1/R-2 of the HF-RV derivation, reused unchanged)

D = SCRATCH / "hf_data" / "raw"
SETT_CAL = D / "deribit_rest_settlements_CALENDAR_2017-05-25_2026-10-20.parquet"
RAW_SETT = SCRATCH / "hcache" / "raw" / "deribit" / "rest.settlements"
OUT_DIR = Path("/home/user/scinance/scinance3-impl/state/herleitung_a2")
WORK = HERE / "work"

LAST_RETURN_DAY = "2024-05-31"
FIRST_RETURN_DAY = "2021-03-24"
LAST_CAL_DAY = "2026-06-30"
FIRST_CAL_DAY = "2020-03-25"
SEED = 27
N_BOOT = 2000

LABEL = ("A2-Vorarbeit (EXP-CLOCK): Placebo-Design und sigma30-Nuisance. Renditen nur 2021-03-24..2024-05-31 "
         "(1-min-Kerzen), Kalender/OI (gelieferte Kontrakte) nur bis 2026-06-30; nur Streuungs-, Korrelations-, "
         "Autokorrelations-, Varianzfaktor- und Zaehlgroessen. Kein Mittel und kein Vorzeichen irgendeiner "
         "Verfallstag-Rendite (r_pre, r_post, Differenz Ereignis minus Placebo) wird ausgegeben oder gespeichert; "
         "keine Preisfelder der Settlements gelesen. Kein Verdikt, nichts registriert.")

MON = {m.upper(): i for i, m in enumerate(calendar.month_abbr) if m}
RE_OPT = re.compile(r"^(BTC|ETH)-(\d{1,2})([A-Z]{3})(\d{2})-([0-9d.]+)-([CP])$")
RE_FUT = re.compile(r"^(BTC|ETH)-(\d{1,2})([A-Z]{3})(\d{2})$")

# ----------------------------------------------------------------------------------------------
# guards (R-11)
# ----------------------------------------------------------------------------------------------
_BAD = re.compile(
    r"(^|_)(mean|means|avg|average|mittel|mittelwert|drift|bias|effect|effekt|delta|sign|signed|"
    r"vorzeichen)(_|$)|r_pre_mean|mean_r|sign_of|vorzeichen|durchschnitt", re.I)


def guard_keys(d, path: str = ""):
    if isinstance(d, dict):
        for k, v in d.items():
            if _BAD.search(str(k)):
                raise RuntimeError(f"blindness guard: key {path}/{k!r} refused")
            guard_keys(v, f"{path}/{k}")
    elif isinstance(d, (list, tuple)):
        for v in d:
            guard_keys(v, path)
    return d


_LOC = re.compile(r"(^|[_\W])(median|medians|q50|loc|location|center|centre|centered|diff|difference|"
                  r"differenz|contrast|contrasts|kontrast|minus)([_\W]|$)", re.I)
_DIFF_SERIES = re.compile(r"minus|diff|(^|_)did(_|$)", re.I)
# documented allow-list (R-12): (regex on the full path "/a/b/key", reason)
_LOC_ALLOW = (
    (r"(size_by_period_and_class|within_week_and_month_ratios|design_iii_oi_sorted_report)/.*", "OI-Zaehlgroessen (Teil A)"),
    (r"oi_attenuation/.*q50_ratio_[a-z_]+$", "OI-Verhaeltnisse (Teil A)"),
    (r"c_bind_iid_reference/[^/]+/q50$", "Verteilung des Varianzfaktors unter iid (Simulation)"),
    (r"/(se_contrast[a-z0-9_]*|prior_contrast|contrasts)$", "SE bzw. Prior-Eingabe eines Kontrasts"),
    (r"/(pre_minus_fix1530|sd_paired_diff[a-z0-9_]*|c_paired_diff[a-z0-9_]*)$", "Name einer Differenz-REIHE (nur Streuung)"),
    (r"/dispersion/[^/]+/[^/]+/(by_year/[^/]+/)?(BTC|ETH|CLUSTER)/abs_q50$", "Betrags-Quantil einer Einzelrenditen-Reihe"),
    (r"raw_vs_calendar/(days_with_count_difference|count_difference_examples)$", "Zaehlvergleich Rohdaten/Kalender"),
)


def guard_keys_loc(d, path: str = ""):
    """R-12: location-type key segments only on the documented allow-list; no abs_q* under a
    difference series."""
    if isinstance(d, dict):
        for k, v in d.items():
            p = f"{path}/{k}"
            if str(k).lower().startswith("abs_q") and _DIFF_SERIES.search(path):
                raise RuntimeError(f"blindness guard: uncentred abs quantile under difference series {p!r}")
            if _LOC.search(str(k)) and not any(re.search(rx, p) for rx, _ in _LOC_ALLOW):
                raise RuntimeError(f"blindness guard (location): key {p!r} refused")
            guard_keys_loc(v, p)
    elif isinstance(d, (list, tuple)):
        for v in d:
            guard_keys_loc(v, path)
    return d


def check_out(d):
    """All guards on every output dict (R-11, R-12)."""
    no_mean(d)
    guard_keys(d)
    guard_keys_loc(d)
    return d


def _selftest_guards() -> None:
    for bad in ({"r_pre_mean": 1}, {"x": {"mean": 1}}, {"delta_bp": 1}, {"sign": 1}, {"effect_bp": 1}):
        try:
            check_out(bad)
        except RuntimeError:
            continue
        raise AssertionError(f"guard self-test failed for {bad}")
    check_out({"design_i": 1, "se_contrast": 1, "sd": 1})   # must pass ("design" contains "sign")
    for bad in ({"median": 1}, {"r_pre_median": 1}, {"q50": 1}, {"loc": 1}, {"center": 1}, {"diff": 1},
                {"contrast_bp": 1}, {"event_minus_placebo": 1},
                {"dispersion": {"pre_minus_fix1530": {"FRI": {"CLUSTER": {"abs_q90": 1}}}}}):
        try:
            check_out(bad)
        except RuntimeError:
            continue
        raise AssertionError(f"extended guard self-test failed for {bad}")


_selftest_guards()


class FieldGuard:
    """R-2: allow-list extraction of payload fields by Arrow regex; price fields are refused."""
    ALLOWED = ("type", "instrument_name", "timestamp", "position")
    _FORBIDDEN_RX = re.compile(r"price|profit|loss|mark|index|funding|funded|tax|bankrupt|socialized", re.I)
    _VALUE = {"type": r'"(?P<type>[a-z_]+)"', "instrument_name": r'"(?P<instrument_name>[A-Za-z0-9_.\-]+)"',
              "timestamp": r"(?P<timestamp>[0-9]+)", "position": r"(?P<position>-?[0-9][0-9.eE+\-]*|null)"}

    def pattern(self, key: str) -> str:
        if self._FORBIDDEN_RX.search(key):
            raise RuntimeError(f"price guard: access to payload field {key!r} refused")
        if key not in self.ALLOWED:
            raise RuntimeError(f"price guard: field {key!r} not in allow-list {self.ALLOWED}")
        return r'"' + key + r'"\s*:\s*' + self._VALUE[key]

    def extract(self, payload: pa.ChunkedArray | pa.Array, key: str) -> pa.Array:
        st = pc.extract_regex(payload, pattern=self.pattern(key))
        return pc.struct_field(st, [0])


GUARD = FieldGuard()


def _selftest_fieldguard() -> None:
    for k in ("index_price", "mark_price", "profit_loss", "session_profit_loss", "settlement_price"):
        try:
            GUARD.pattern(k)
        except RuntimeError:
            continue
        raise AssertionError(f"FieldGuard self-test failed for {k}")


_selftest_fieldguard()


def read_settlement_partition(path: str) -> pa.Table:
    """Returns ONLY the four allowed fields (strings/ints) of one raw partition; the payload buffer is
    dropped before return.  No JSON decoding."""
    t = pq.read_table(path, columns=["payload_json"])
    payload = t.column("payload_json")
    cols = {k: GUARD.extract(payload, k) for k in FieldGuard.ALLOWED}
    n = t.num_rows
    del t, payload
    out = pa.table({"type": cols["type"], "instrument_name": cols["instrument_name"],
                    "timestamp": pc.cast(cols["timestamp"], pa.int64()),
                    "position_raw": cols["position"]})
    assert set(out.column_names) == {"type", "instrument_name", "timestamp", "position_raw"}
    assert out.num_rows == n
    return out


def read_settlement_fields(path: str, fields: tuple[str, ...]) -> pa.Table:
    """R-14: like read_settlement_partition, but only the requested allow-listed fields (e.g. without
    position).  No JSON decoding; the payload buffer is dropped before return."""
    for f in fields:
        GUARD.pattern(f)                       # raises for anything outside the allow-list
    t = pq.read_table(path, columns=["payload_json"])
    payload = t.column("payload_json")
    cols = {k: GUARD.extract(payload, k) for k in fields}
    del t, payload
    if "timestamp" in cols:
        cols["timestamp"] = pc.cast(cols["timestamp"], pa.int64())
    return pa.table(cols)


def raw_partitions_upto(sym: str, first_day: str = "0000-00-00") -> list[tuple[str, str]]:
    """Local cache partitions first_day <= date <= LAST_CAL_DAY (later dates never opened, R-1)."""
    out = []
    for dpath in sorted(glob.glob(str(RAW_SETT / f"symbol={sym}" / "date=*"))):
        day = dpath.rsplit("date=", 1)[1]
        if day < first_day or day > LAST_CAL_DAY:
            continue
        for f in sorted(glob.glob(dpath + "/*.parquet")):
            out.append((day, f))
    assert all(d <= LAST_CAL_DAY for d, _ in out)
    return out


def raw_partitions(sym: str) -> list[tuple[str, str]]:
    """Local cache partitions (date, file) with FIRST_CAL_DAY <= date <= LAST_CAL_DAY; later dates are
    never opened (R-1)."""
    out = []
    for dpath in sorted(glob.glob(str(RAW_SETT / f"symbol={sym}" / "date=*"))):
        day = dpath.rsplit("date=", 1)[1]
        if day < FIRST_CAL_DAY or day > LAST_CAL_DAY:
            continue
        files = sorted(glob.glob(dpath + "/*.parquet"))
        for f in files:
            out.append((day, f))
    assert all(d <= LAST_CAL_DAY for d, _ in out)
    return out


# ----------------------------------------------------------------------------------------------
# calendar helpers (C-3 of a2_census, reused)
# ----------------------------------------------------------------------------------------------

def parse_option_expiry(name: str):
    m = RE_OPT.match(name or "")
    if not m:
        return None, None
    dd, mmm, yy = int(m.group(2)), m.group(3), int(m.group(4))
    return m.group(1), date(2000 + yy, MON[mmm], dd)


def last_friday(y: int, m: int) -> date:
    d = date(y, m, calendar.monthrange(y, m)[1])
    while d.weekday() != 4:
        d -= timedelta(days=1)
    return d


def cal_class(d: date) -> str:
    if d.weekday() != 4:
        return "daily"
    if d != last_friday(d.year, d.month):
        return "weekly"
    return "quarterly" if d.month in (3, 6, 9, 12) else "monthly"


def day_class(d: date) -> str:
    """R-4 fine class of a day (all days since 2020-03-25 are expiry days)."""
    c = cal_class(d)
    if c == "weekly":
        return "FRI_W"
    if c == "monthly":
        return "FRI_M"
    if c == "quarterly":
        return "FRI_Q"
    return "WE" if d.weekday() >= 5 else "MODO"


CLASS_SETS = {"FRI": ("FRI_W", "FRI_M", "FRI_Q"), "FRI_W": ("FRI_W",), "FRI_M": ("FRI_M",),
              "FRI_Q": ("FRI_Q",), "FRI_MQ": ("FRI_M", "FRI_Q"), "MODO": ("MODO",), "WE": ("WE",),
              "NONFRI": ("MODO", "WE"),
              "ALL": ("FRI_W", "FRI_M", "FRI_Q", "MODO", "WE")}


def days_range(lo: str, hi: str) -> list[date]:
    a, b = date.fromisoformat(lo), date.fromisoformat(hi)
    return [a + timedelta(i) for i in range((b - a).days + 1)]


def load_calendar() -> pl.DataFrame:
    """Calendar extract (no price column), rows with UTC day <= LAST_CAL_DAY only (R-1)."""
    df = pl.read_parquet(SETT_CAL)
    assert set(df.columns) == {"column_symbol", "instrument_name", "type", "timestamp_ms"}, df.columns
    df = df.with_columns(pl.from_epoch("timestamp_ms", time_unit="ms").dt.date().alias("ts_day"))
    df = df.filter(pl.col("ts_day") <= date.fromisoformat(LAST_CAL_DAY))
    assert df["ts_day"].max() <= date.fromisoformat(LAST_CAL_DAY)
    return df


def assert_kline_dates(path) -> str:
    """R-13: read ONLY the start_ms column and assert that no UTC day lies after LAST_RETURN_DAY,
    before any price column of the extract is read."""
    t = pq.read_table(path, columns=["start_ms"])
    mx = pc.max(t.column("start_ms")).as_py()
    last = datetime.fromtimestamp(mx / 1000.0, tz=timezone.utc).date().isoformat()
    if last > LAST_RETURN_DAY:
        raise RuntimeError(f"kline extract {path} contains {last} > {LAST_RETURN_DAY}")
    assert_rv_day(last)
    return last


def sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(obj, path: Path) -> str:
    check_out(obj)
    txt = json.dumps(obj, indent=1, sort_keys=False, ensure_ascii=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(txt)
    return hashlib.sha256(txt.encode()).hexdigest()
