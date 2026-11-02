"""Candidate file (YAML/JSON) -> validated dataclasses; every defect fails LOUDLY (C.14, no silent defaults).

One file per candidate.  Every nuisance number carries a source (file, field, sha256) or an explicit derivation text;
the calculator itself never opens the cited files (``verify_sources`` is an opt-in drift report).  The file may also
carry an ``expected`` list (regression values with source and relative tolerance) which the CLI/tests compare to the
computed report.

Loud failures (``FeasibilityInputError``): missing field, unknown field, ``c_overlap < 1``, SE or SD ``<= 0``, Zone-K
data before 2026-07-01, label UNBELEGT without a two-sided sensitivity span, malformed source, malformed numbers.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "FeasibilityInputError", "Source", "Sourced", "Statistic", "Nuisance", "SesoiCfg", "Prior", "ZoneData", "DataCfg",
    "DesignMenu", "ChainStep", "Chain", "PilotCfg", "Expected", "Candidate", "load_candidate", "candidate_from_obj",
    "guard_path", "verify_sources", "KNOWLEDGE_CLASSES", "ZONE_K_START", "PRIOR_LABELS", "STATISTIC_UNITS",
    "CLUSTER_UNITS", "sha256_of_file",
]

STATISTIC_UNITS = ("bp", "IC", "VP")
CLUSTER_UNITS = ("week", "day", "event")
PRIOR_LABELS = ("primaer", "sek", "UNBELEGT", "zone_x_selektionsbereinigt")
ZONE_K_START = _dt.date(2026, 7, 1)          # DEC-96 E3 / DEC-104 E4 (a): confirmation (sealed) zone starts here
LINES = ("central", "stress")
CONJUNCTION_MODES = ("product", "pair", "joint")
WINDOW_MONTHS_ALLOWED = (6, 9, 12)
LOOKS_ALLOWED = (1, 2, 3, 4)

#: FENSTERREGISTER section 2 / section 6: family -> (V allowed for confirmation, first pure K date, rule text)
KNOWLEDGE_CLASSES: dict[str, dict[str, Any]] = {
    "btc_eth_aggregate": {"v": "no", "k_start": _dt.date(2026, 10, 1),
                          "rule": "BTC/ETH aggregates: confirmation only prospectively in zone K (exception A2 r_pre)"},
    "panel_crosssection": {"v": "blind_only", "k_start": _dt.date(2026, 7, 1),
                           "rule": "panel cross-sections: W1/W2 only while blind (not consumed under C.17), zone K"},
    "funding_oi_volume": {"v": "no", "k_start": _dt.date(2026, 9, 15),
                          "rule": "funding/OI/turnover: zone V only for non-outcome statistics, zone K prospectively"},
    "options_chain": {"v": "no", "k_start": _dt.date(2026, 7, 1),
                      "rule": "option chain/settlements: zone K prospectively; snapshots from 2026-07 only counts"},
    "live_streams": {"v": "no", "k_start": _dt.date(2026, 7, 1),
                     "rule": "live streams from 2026-06: zone K entirely"},
    "trades_orderbooks": {"v": "no", "k_start": _dt.date(2026, 10, 1),
                          "rule": "trades/orderbooks: zone K prospectively for daily aggregates"},
}


class FeasibilityInputError(ValueError):
    """Raised for any defect of a candidate file or of the arguments of the calculator."""


# ------------------------------------------------------------------------------------------------------------------
# small validation helpers
# ------------------------------------------------------------------------------------------------------------------
def _fail(path: str, msg: str):
    raise FeasibilityInputError(f"{path}: {msg}")


def _need(obj: dict, key: str, path: str):
    if not isinstance(obj, dict):
        _fail(path, f"expected a mapping, got {type(obj).__name__}")
    if key not in obj or obj[key] is None:
        _fail(f"{path}.{key}" if path else key, "missing field")
    return obj[key]


def _only(obj: dict, allowed: tuple[str, ...], path: str) -> None:
    if not isinstance(obj, dict):
        _fail(path, f"expected a mapping, got {type(obj).__name__}")
    extra = sorted(set(obj) - set(allowed))
    if extra:
        _fail(path, f"unknown field(s) {extra}; allowed {sorted(allowed)}")


def _num(x: Any, path: str, *, positive: bool = False, minimum: float | None = None, maximum: float | None = None) -> float:
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        _fail(path, f"expected a number, got {x!r}")
    v = float(x)
    if not math.isfinite(v):
        _fail(path, "number must be finite")
    if positive and not v > 0.0:
        _fail(path, f"must be > 0, got {v}")
    if minimum is not None and v < minimum:
        _fail(path, f"must be >= {minimum}, got {v}")
    if maximum is not None and v > maximum:
        _fail(path, f"must be <= {maximum}, got {v}")
    return v


def _date(x: Any, path: str) -> _dt.date:
    if isinstance(x, _dt.datetime):
        return x.date()
    if isinstance(x, _dt.date):
        return x
    if isinstance(x, str):
        try:
            return _dt.date.fromisoformat(x)
        except ValueError:
            pass
    _fail(path, f"expected an ISO date, got {x!r}")


# ------------------------------------------------------------------------------------------------------------------
# sources and sourced numbers
# ------------------------------------------------------------------------------------------------------------------
_SHA = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class Source:
    """Where a number comes from: (file, field, sha256) of the dossier, or an explicit derivation text."""

    file: str | None = None
    field: str | None = None
    sha256: str | None = None
    derivation: str | None = None

    @classmethod
    def from_obj(cls, obj: Any, path: str) -> "Source":
        if not isinstance(obj, dict):
            _fail(path, "source must be a mapping with file/field/sha256 or derivation")
        _only(obj, ("file", "field", "sha256", "derivation", "note"), path)
        if "derivation" in obj:
            if not isinstance(obj["derivation"], str) or not obj["derivation"].strip():
                _fail(f"{path}.derivation", "must be a non-empty text")
            return cls(derivation=obj["derivation"], file=obj.get("file"), field=obj.get("field"), sha256=obj.get("sha256"))
        f = _need(obj, "file", path)
        fld = _need(obj, "field", path)
        sha = _need(obj, "sha256", path)
        if not isinstance(f, str) or not isinstance(fld, str):
            _fail(path, "file and field must be texts")
        if not isinstance(sha, str) or not _SHA.match(sha):
            _fail(f"{path}.sha256", "must be 64 lowercase hex characters")
        return cls(file=f, field=fld, sha256=sha)

    def as_dict(self) -> dict:
        d = {"file": self.file, "field": self.field, "sha256": self.sha256}
        if self.derivation:
            d["derivation"] = self.derivation
        return d


@dataclass(frozen=True)
class Sourced:
    value: float
    source: Source

    @classmethod
    def from_obj(cls, obj: Any, path: str, **num_kw) -> "Sourced":
        if not isinstance(obj, dict):
            _fail(path, "expected {value, source}")
        _only(obj, ("value", "source", "label"), path)
        return cls(_num(_need(obj, "value", path), f"{path}.value", **num_kw), Source.from_obj(_need(obj, "source", path), f"{path}.source"))


def _sourced_by_line(obj: Any, path: str, **num_kw) -> dict[str, Sourced]:
    """``{central: {value, source}, stress: {value, source}}``; ``central`` is mandatory, ``stress`` optional."""
    _only(obj, LINES, path)
    out = {"central": Sourced.from_obj(_need(obj, "central", path), f"{path}.central", **num_kw)}
    if obj.get("stress") is not None:
        out["stress"] = Sourced.from_obj(obj["stress"], f"{path}.stress", **num_kw)
    return out


# ------------------------------------------------------------------------------------------------------------------
# blocks
# ------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Statistic:
    name: str
    unit: str
    direction: str            # registered direction of the one-sided test: "positive" | "negative"

    @classmethod
    def from_obj(cls, obj: Any) -> "Statistic":
        _only(obj, ("name", "unit", "direction"), "statistic")
        name = _need(obj, "name", "statistic")
        unit = _need(obj, "unit", "statistic")
        direction = _need(obj, "direction", "statistic")
        if not isinstance(name, str) or not name.strip():
            _fail("statistic.name", "must be a non-empty text")
        if unit not in STATISTIC_UNITS:
            _fail("statistic.unit", f"must be one of {STATISTIC_UNITS}, got {unit!r}")
        if direction not in ("positive", "negative"):
            _fail("statistic.direction", "one-sided test in the registered direction: 'positive' or 'negative'")
        return cls(name, unit, direction)


@dataclass(frozen=True)
class Nuisance:
    """SE of the statistic per 12 months: either ``se12`` directly or ``sd_per_unit`` with ``c`` and units per year."""

    cluster_unit: str
    units_per_year: float
    c_overlap: float
    c_source: Source
    se12: dict[str, Sourced] = field(default_factory=dict)            # line -> value (c already inside)
    sd_per_unit: dict[str, Sourced] = field(default_factory=dict)     # line -> SD per cluster unit (c applied here)
    null_sd: Sourced | None = None
    condition_correlation: Sourced | None = None

    @classmethod
    def from_obj(cls, obj: Any) -> "Nuisance":
        _only(obj, ("cluster_unit", "units_per_year", "c_overlap", "se12", "sd_per_unit", "null_sd", "condition_correlation"),
              "nuisance")
        cu = _need(obj, "cluster_unit", "nuisance")
        if cu not in CLUSTER_UNITS:
            _fail("nuisance.cluster_unit", f"must be one of {CLUSTER_UNITS}, got {cu!r}")
        upy = _num(_need(obj, "units_per_year", "nuisance"), "nuisance.units_per_year", positive=True)
        c_obj = _need(obj, "c_overlap", "nuisance")
        if not isinstance(c_obj, dict):
            _fail("nuisance.c_overlap", "expected {value, source} (the factor c needs a source)")
        _only(c_obj, ("value", "source", "label"), "nuisance.c_overlap")
        c = _num(_need(c_obj, "value", "nuisance.c_overlap"), "nuisance.c_overlap.value")
        if c < 1.0:
            _fail("nuisance.c_overlap", f"autocorrelation/overlap factor c must be >= 1, got {c}")
        c_source = Source.from_obj(_need(c_obj, "source", "nuisance.c_overlap"), "nuisance.c_overlap.source")
        has_se, has_sd = obj.get("se12") is not None, obj.get("sd_per_unit") is not None
        if has_se == has_sd:
            _fail("nuisance", "give exactly one of 'se12' (SE per 12 months, c inside) or 'sd_per_unit' (SD per cluster unit)")
        se12 = _sourced_by_line(obj["se12"], "nuisance.se12", positive=True) if has_se else {}
        sd = _sourced_by_line(obj["sd_per_unit"], "nuisance.sd_per_unit", positive=True) if has_sd else {}
        null_sd = Sourced.from_obj(obj["null_sd"], "nuisance.null_sd", positive=True) if obj.get("null_sd") is not None else None
        cc = (Sourced.from_obj(obj["condition_correlation"], "nuisance.condition_correlation", minimum=-1.0, maximum=1.0)
              if obj.get("condition_correlation") is not None else None)
        return cls(cu, upy, c, c_source, se12, sd, null_sd, cc)

    def lines(self) -> tuple[str, ...]:
        src = self.se12 or self.sd_per_unit
        return tuple(ln for ln in LINES if ln in src)

    def se12_of(self, line: str) -> float:
        """SE of one 12-month window (statistic units) on the given nuisance line."""
        if line not in self.lines():
            _fail("nuisance", f"no nuisance line {line!r}")
        if self.se12:
            return self.se12[line].value
        return self.sd_per_unit[line].value * math.sqrt(self.c_overlap / self.units_per_year)

    def null_scale_k(self, line: str = "central") -> float | None:
        """Scaled-null factor ``k = max(1, SE / null SD)`` (R-C13 of the A2 dossier); ``None`` without a null SD."""
        if self.null_sd is None:
            return None
        return max(1.0, self.se12_of(line) / self.null_sd.value)


@dataclass(frozen=True)
class SesoiCfg:
    mode: str                          # "direct" | "decile" | "single_position"
    unit: str
    label: str
    value: Sourced | None = None       # direct
    cost_side: str = "taker"
    cost_bp: dict[str, Sourced] = field(default_factory=dict)
    phi: float | None = None
    turnover: float | None = None
    sigma_bp: Sourced | None = None    # single position: SD of the return per decision period; decile: cross-sectional SD
    sigma_daily_bp: Sourced | None = None
    horizon_days: float = 1.0
    rank_ic: bool = False
    curve_phis: tuple[float, ...] = (-1.0, 0.0, 0.5, 0.8)
    curve_horizons_days: tuple[float, ...] = ()
    curve_sigma_bp: dict[str, Sourced] = field(default_factory=dict)   # extra informational frames: frame -> sigma

    @classmethod
    def from_obj(cls, obj: Any, stat_unit: str) -> "SesoiCfg":
        allowed = ("mode", "unit", "label", "value", "cost_side", "cost_bp", "phi", "turnover", "sigma_bp", "sigma_daily_bp",
                   "horizon_days", "rank_ic", "curve_phis", "curve_horizons_days", "curve_sigma_bp")
        _only(obj, allowed, "sesoi")
        mode = _need(obj, "mode", "sesoi")
        if mode not in ("direct", "decile", "single_position"):
            _fail("sesoi.mode", "must be 'direct', 'decile' or 'single_position'")
        unit = _need(obj, "unit", "sesoi")
        if unit != stat_unit:
            _fail("sesoi.unit", f"SESOI unit {unit!r} must equal the statistic unit {stat_unit!r}")
        label = _need(obj, "label", "sesoi")
        if not isinstance(label, str) or not label.strip():
            _fail("sesoi.label", "must be a non-empty text (cost basis label, e.g. 'Taker (VIP0)')")
        cost_side = obj.get("cost_side", "taker")
        if cost_side not in ("maker", "taker", "total"):
            _fail("sesoi.cost_side", "must be 'maker', 'taker' or 'total'")
        costs = {}
        if obj.get("cost_bp") is not None:
            _only(obj["cost_bp"], ("maker", "taker", "total"), "sesoi.cost_bp")
            for k, v in obj["cost_bp"].items():
                costs[k] = Sourced.from_obj(v, f"sesoi.cost_bp.{k}", positive=True)
        value = Sourced.from_obj(obj["value"], "sesoi.value", positive=True) if obj.get("value") is not None else None
        sigma = Sourced.from_obj(obj["sigma_bp"], "sesoi.sigma_bp", positive=True) if obj.get("sigma_bp") is not None else None
        sig_d = (Sourced.from_obj(obj["sigma_daily_bp"], "sesoi.sigma_daily_bp", positive=True)
                 if obj.get("sigma_daily_bp") is not None else None)
        phi = _num(obj["phi"], "sesoi.phi", minimum=-1.0, maximum=1.0) if obj.get("phi") is not None else None
        turnover = _num(obj["turnover"], "sesoi.turnover", positive=True) if obj.get("turnover") is not None else None
        if mode == "direct":
            if value is None:
                _fail("sesoi.value", "missing field (mode 'direct' needs the SESOI in units of the statistic)")
        else:
            if cost_side not in costs:
                _fail("sesoi.cost_bp", f"missing cost for side {cost_side!r}")
            if sigma is None and sig_d is None:
                _fail("sesoi.sigma_bp", "missing field (mode needs sigma_bp or sigma_daily_bp)")
            if phi is None and turnover is None:
                _fail("sesoi.phi", "missing field (give the signal persistence phi or the turnover)")
        horizon = _num(obj.get("horizon_days", 1.0), "sesoi.horizon_days", positive=True)
        phis = tuple(_num(p, "sesoi.curve_phis[]", minimum=-1.0, maximum=1.0) for p in obj.get("curve_phis", (-1.0, 0.0, 0.5, 0.8)))
        hors = tuple(_num(h, "sesoi.curve_horizons_days[]", positive=True) for h in obj.get("curve_horizons_days", ()))
        csig = {}
        for fr, v in (obj.get("curve_sigma_bp") or {}).items():
            if fr not in ("decile", "single_position"):
                _fail("sesoi.curve_sigma_bp", "allowed frames: 'decile', 'single_position'")
            csig[fr] = Sourced.from_obj(v, f"sesoi.curve_sigma_bp.{fr}", positive=True)
        if csig and not costs:
            _fail("sesoi.cost_bp", "missing field (informational curves need cost_bp)")
        return cls(mode, unit, label, value, cost_side, costs, phi, turnover, sigma, sig_d, horizon,
                   bool(obj.get("rank_ic", False)), phis, hors, csig)


@dataclass(frozen=True)
class Prior:
    label: str
    median: Sourced | None = None
    band: tuple[float, float] | None = None
    sensitivity_span: tuple[float, float] | None = None
    source: Source | None = None
    note: str = ""
    extra_points: dict[str, Sourced] = field(default_factory=dict)

    @classmethod
    def from_obj(cls, obj: Any) -> "Prior":
        _only(obj, ("label", "median", "band", "sensitivity_span", "source", "note", "extra_points"), "prior")
        label = _need(obj, "label", "prior")
        if label not in PRIOR_LABELS:
            _fail("prior.label", f"must be one of {PRIOR_LABELS}, got {label!r}")

        def pair(key: str):
            if obj.get(key) is None:
                return None
            v = obj[key]
            if not (isinstance(v, (list, tuple)) and len(v) == 2):
                _fail(f"prior.{key}", "expected [low, high]")
            lo, hi = _num(v[0], f"prior.{key}[0]"), _num(v[1], f"prior.{key}[1]")
            if not lo < hi:
                _fail(f"prior.{key}", f"low must be < high, got {lo}, {hi}")
            return lo, hi

        median = Sourced.from_obj(obj["median"], "prior.median") if obj.get("median") is not None else None
        band, span = pair("band"), pair("sensitivity_span")
        if label == "UNBELEGT" and span is None:
            _fail("prior.sensitivity_span", "label UNBELEGT requires a two-sided sensitivity span [low, high] (DEC-104 E3 (d)); "
                  "a missing prior is never replaced by a worst-case default")
        if label != "UNBELEGT" and median is None:
            _fail("prior.median", "missing field (labels other than UNBELEGT need a median)")
        src = Source.from_obj(obj["source"], "prior.source") if obj.get("source") is not None else None
        extra = {}
        for k, v in (obj.get("extra_points") or {}).items():
            extra[str(k)] = Sourced.from_obj(v, f"prior.extra_points.{k}", positive=True)
        return cls(label, median, band, span, src, str(obj.get("note", "")), extra)

    def points(self) -> dict[str, float]:
        """Named effect values at which the OC row and the prior-days row are evaluated."""
        pts: dict[str, float] = {}
        if self.median is not None:
            pts["median"] = self.median.value
        if self.band is not None:
            pts["band_low"], pts["band_high"] = self.band
        if self.sensitivity_span is not None:
            pts["span_low"], pts["span_high"] = self.sensitivity_span
        for k, v in self.extra_points.items():
            pts[k] = v.value
        return pts


@dataclass(frozen=True)
class ZoneData:
    start: _dt.date | None
    end: _dt.date | None
    units: float | None            # cluster units available (X, V); None for K (prospective)
    se: Sourced | None = None      # directly measured SE of the whole zone (optional override for zone X)
    source: Source | None = None


@dataclass(frozen=True)
class DataCfg:
    knowledge_class: str
    cohort_date: _dt.date
    selection_k: int
    x: ZoneData | None
    v: ZoneData | None
    k_start: _dt.date
    a2_exception: bool
    v_blind_confirmed: bool

    @classmethod
    def from_obj(cls, obj: Any, units_per_year: float) -> "DataCfg":
        _only(obj, ("knowledge_class", "cohort_date", "selection_k", "zones", "a2_exception", "v_blind_confirmed"), "data")
        kc = _need(obj, "knowledge_class", "data")
        if kc not in KNOWLEDGE_CLASSES:
            _fail("data.knowledge_class", f"must be one of {sorted(KNOWLEDGE_CLASSES)}, got {kc!r}")
        cohort = _date(_need(obj, "cohort_date", "data"), "data.cohort_date")
        sk = _need(obj, "selection_k", "data")
        if isinstance(sk, bool) or not isinstance(sk, int) or sk < 0:
            _fail("data.selection_k", f"must be an integer >= 0, got {sk!r}")
        zones = _need(obj, "zones", "data")
        _only(zones, ("X", "V", "K"), "data.zones")

        def zone(name: str, allow_se: bool = False) -> ZoneData | None:
            z = zones.get(name)
            if z is None:
                return None
            _only(z, ("start", "end", "months", "units", "se", "source"), f"data.zones.{name}")
            start = _date(_need(z, "start", f"data.zones.{name}"), f"data.zones.{name}.start")
            end = _date(_need(z, "end", f"data.zones.{name}"), f"data.zones.{name}.end")
            if end < start:
                _fail(f"data.zones.{name}", "end before start")
            has_m, has_u = z.get("months") is not None, z.get("units") is not None
            if has_m == has_u:
                _fail(f"data.zones.{name}", "give exactly one of 'months' or 'units' (cluster units)")
            units = (_num(z["units"], f"data.zones.{name}.units", positive=True) if has_u
                     else _num(z["months"], f"data.zones.{name}.months", positive=True) * units_per_year / 12.0)
            se = Sourced.from_obj(z["se"], f"data.zones.{name}.se", positive=True) if z.get("se") is not None else None
            src = Source.from_obj(z["source"], f"data.zones.{name}.source") if z.get("source") is not None else None
            return ZoneData(start, end, units, se, src)

        x, v = zone("X"), zone("V")
        kz = zones.get("K")
        if kz is None:
            _fail("data.zones.K", "missing field (zone K start; prospective confirmation data)")
        _only(kz, ("start",), "data.zones.K")
        k_start = _date(_need(kz, "start", "data.zones.K"), "data.zones.K.start")
        if k_start < ZONE_K_START:
            _fail("data.zones.K.start", f"zone K data before {ZONE_K_START.isoformat()} are not confirmation data "
                  f"(sealed period starts there), got {k_start.isoformat()}")
        if x is not None and x.end >= _dt.date(2024, 7, 1):
            _fail("data.zones.X.end", "zone X ends before 2024-07-01 (DEC-104 E4 (a))")
        if v is not None and (v.start < _dt.date(2024, 7, 1) or v.end >= ZONE_K_START):
            _fail("data.zones.V", "zone V lies within 2024-07-01 .. 2026-06-30 (W1/W2, DEC-104 E4 (a))")
        return cls(kc, cohort, sk, x, v, k_start, bool(obj.get("a2_exception", False)), bool(obj.get("v_blind_confirmed", False)))

    def v_usable(self) -> tuple[bool, str]:
        rule = KNOWLEDGE_CLASSES[self.knowledge_class]
        if self.v is None:
            return False, "no zone V data given"
        if rule["v"] == "no":
            if self.a2_exception:
                return True, "zone V allowed by the A2 r_pre exception (DEC-104 E4 (i)), discipline label"
            return False, "zone V not allowed for this knowledge class: " + rule["rule"]
        if rule["v"] == "blind_only":
            if self.v_blind_confirmed:
                return True, "zone V blind (confirmed by the C.17 list)"
            return False, "zone V usable only while blind; 'v_blind_confirmed' not set"
        return True, ""

    def k_effective_start(self) -> _dt.date:
        return max(self.k_start, KNOWLEDGE_CLASSES[self.knowledge_class]["k_start"])


@dataclass(frozen=True)
class DesignMenu:
    window_months: tuple[int, ...]
    looks: tuple[int, ...]
    placebo_set_variants: dict[str, tuple[str, ...]]
    screen_alphas: tuple[float, ...]
    horizon_limit_months: float
    mc_reps: int
    gsd_paths: int
    conjunction_mc: int

    @classmethod
    def from_obj(cls, obj: Any) -> "DesignMenu":
        _only(obj, ("window_months", "looks", "placebo_set_variants", "screen_alphas", "horizon_limit_months", "mc_reps",
                    "gsd_paths", "conjunction_mc"), "design_menu")
        wm = tuple(int(_num(x, "design_menu.window_months[]")) for x in _need(obj, "window_months", "design_menu"))
        if not wm or any(w not in WINDOW_MONTHS_ALLOWED for w in wm):
            _fail("design_menu.window_months", f"subset of {WINDOW_MONTHS_ALLOWED} required, got {wm}")
        lk = tuple(int(_num(x, "design_menu.looks[]")) for x in _need(obj, "looks", "design_menu"))
        if not lk or any(k not in LOOKS_ALLOWED for k in lk):
            _fail("design_menu.looks", f"subset of {LOOKS_ALLOWED} required, got {lk}")
        pv_raw = obj.get("placebo_set_variants", {})
        if not isinstance(pv_raw, dict):
            _fail("design_menu.placebo_set_variants", "expected a mapping name -> list of condition names")
        pv = {str(k): tuple(str(x) for x in v) for k, v in pv_raw.items()}
        sa = tuple(_num(a, "design_menu.screen_alphas[]", minimum=1e-6, maximum=0.5) for a in obj.get("screen_alphas", (0.05, 0.10, 0.20, 0.50)))
        hl = _num(obj.get("horizon_limit_months", 60.0), "design_menu.horizon_limit_months", positive=True)
        mc = obj.get("mc_reps", 20000)
        if isinstance(mc, bool) or not isinstance(mc, int) or mc < 1000:
            _fail("design_menu.mc_reps", f"must be an integer >= 1000 (DEC-104 E8 (a)), got {mc!r}")
        gp = obj.get("gsd_paths", 200000)
        if isinstance(gp, bool) or not isinstance(gp, int) or gp < 1000:
            _fail("design_menu.gsd_paths", f"must be an integer >= 1000, got {gp!r}")
        cm = obj.get("conjunction_mc", 400000)
        if isinstance(cm, bool) or not isinstance(cm, int) or cm < 1000:
            _fail("design_menu.conjunction_mc", f"must be an integer >= 1000, got {cm!r}")
        return cls(wm, lk, pv, sa, hl, mc, gp, cm)


@dataclass(frozen=True)
class ChainStep:
    id: str
    label: str
    line: str = "central"
    conditions: tuple[str, ...] = ()
    null_scaled: bool = False
    mode: str = "product"
    gate: float = 1.0
    mde80: float | None = None          # declared value (mode of the chain is 'declared')
    source: Source | None = None


@dataclass(frozen=True)
class Chain:
    id: str
    label: str
    kind: str                           # "computed" | "declared"
    reference_window: str | None
    base_step: str | None
    steps: tuple[ChainStep, ...]

    @classmethod
    def from_obj(cls, obj: Any, idx: int) -> "Chain":
        p = f"chains[{idx}]"
        _only(obj, ("id", "label", "kind", "reference_window", "base_step", "steps"), p)
        cid = _need(obj, "id", p)
        kind = _need(obj, "kind", p)
        if kind not in ("computed", "declared"):
            _fail(f"{p}.kind", "must be 'computed' or 'declared'")
        steps_raw = _need(obj, "steps", p)
        if not isinstance(steps_raw, list) or len(steps_raw) < 2:
            _fail(f"{p}.steps", "a chain needs at least two steps (base and one commitment)")
        steps = []
        for j, s in enumerate(steps_raw):
            sp = f"{p}.steps[{j}]"
            _only(s, ("id", "label", "line", "conditions", "null_scaled", "mode", "gate", "mde80", "source"), sp)
            line = s.get("line", "central")
            if line not in LINES:
                _fail(f"{sp}.line", f"must be one of {LINES}")
            mode = s.get("mode", "product")
            if mode not in CONJUNCTION_MODES:
                _fail(f"{sp}.mode", f"must be one of {CONJUNCTION_MODES}")
            gate = _num(s.get("gate", 1.0), f"{sp}.gate", positive=True, maximum=1.0)
            md = None
            src = None
            if kind == "declared":
                md = _num(_need(s, "mde80", sp), f"{sp}.mde80", positive=True)
                src = Source.from_obj(_need(s, "source", sp), f"{sp}.source")
            steps.append(ChainStep(str(_need(s, "id", sp)), str(_need(s, "label", sp)), line,
                                   tuple(str(c) for c in s.get("conditions", ())), bool(s.get("null_scaled", False)),
                                   mode, gate, md, src))
        ids = [s.id for s in steps]
        if len(set(ids)) != len(ids):
            _fail(f"{p}.steps", "step ids must be unique")
        base = obj.get("base_step")
        if base is not None and base not in ids:
            _fail(f"{p}.base_step", f"unknown step id {base!r}")
        return cls(str(cid), str(_need(obj, "label", p)), kind, obj.get("reference_window"), base, tuple(steps))


@dataclass(frozen=True)
class PilotCfg:
    se: Sourced
    threshold: Sourced
    true_effects: tuple[float, ...]

    @classmethod
    def from_obj(cls, obj: Any) -> "PilotCfg":
        _only(obj, ("se", "threshold", "true_effects"), "pilot")
        te = tuple(_num(x, "pilot.true_effects[]", positive=True) for x in _need(obj, "true_effects", "pilot"))
        if not te:
            _fail("pilot.true_effects", "needs at least one effect")
        return cls(Sourced.from_obj(_need(obj, "se", "pilot"), "pilot.se", positive=True),
                   Sourced.from_obj(_need(obj, "threshold", "pilot"), "pilot.threshold", positive=True), te)


@dataclass(frozen=True)
class Expected:
    key: str
    value: float
    rel_tol: float
    source: Source
    note: str = ""


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    title: str
    statistic: Statistic
    nuisance: Nuisance
    sesoi: SesoiCfg
    prior: Prior | None
    data: DataCfg
    design_menu: DesignMenu
    gate: Sourced | None
    chains: tuple[Chain, ...]
    conjunction: dict | None
    pilot: PilotCfg | None
    expected: tuple[Expected, ...]
    notes: str = ""

    @property
    def gate_factor(self) -> float:
        return 1.0 if self.gate is None else self.gate.value


_TOP = ("schema_version", "candidate_id", "title", "statistic", "nuisance", "sesoi", "prior", "data", "design_menu",
        "gate_factor", "chains", "conjunction", "pilot", "expected", "notes")


def _validate_conjunction(obj: Any) -> dict:
    """Light structural validation of the conjunction block (numbers are checked when a model is built)."""
    _only(obj, ("tau95", "z_alpha", "pair", "windows", "reference_window"), "conjunction")
    wins = _need(obj, "windows", "conjunction")
    if not isinstance(wins, dict) or not wins:
        _fail("conjunction.windows", "expected a non-empty mapping window -> model")
    out_w: dict[str, dict] = {}
    for wname, w in wins.items():
        wp = f"conjunction.windows.{wname}"
        _only(w, ("kappa", "event", "conditions", "null_test"), wp)
        kappa = _num(_need(w, "kappa", wp), f"{wp}.kappa", positive=True, maximum=1.0)
        ev = _need(w, "event", wp)
        _only(ev, ("n", "c", "sd"), f"{wp}.event")
        conds = _need(w, "conditions", wp)
        if not isinstance(conds, dict) or not conds:
            _fail(f"{wp}.conditions", "expected a non-empty mapping name -> parameters")
        parsed_conds = {}
        for cn, c in conds.items():
            cp = f"{wp}.conditions.{cn}"
            _only(c, ("n", "c", "sd", "se"), cp)
            parsed_conds[cn] = {"n": _num(_need(c, "n", cp), f"{cp}.n", positive=True),
                                "c": _num(_need(c, "c", cp), f"{cp}.c", minimum=1.0),
                                "sd": _sourced_by_line(_need(c, "sd", cp), f"{cp}.sd", positive=True),
                                "se": _sourced_by_line(_need(c, "se", cp), f"{cp}.se", positive=True)}
        parsed_ev = {"n": _num(_need(ev, "n", f"{wp}.event"), f"{wp}.event.n", positive=True),
                     "c": _num(_need(ev, "c", f"{wp}.event"), f"{wp}.event.c", minimum=1.0),
                     "sd": _sourced_by_line(_need(ev, "sd", f"{wp}.event"), f"{wp}.event.sd", positive=True)}
        nl = w.get("null_test")
        parsed_null = None
        if nl is not None:
            _only(nl, ("sd", "d95", "centre_sd"), f"{wp}.null")
            parsed_null = {"sd": _sourced_by_line(_need(nl, "sd", f"{wp}.null"), f"{wp}.null.sd", positive=True),
                           "d95": _sourced_by_line(_need(nl, "d95", f"{wp}.null"), f"{wp}.null.d95", positive=True),
                           "centre_sd": _sourced_by_line(_need(nl, "centre_sd", f"{wp}.null"), f"{wp}.null.centre_sd", minimum=0.0)}
        out_w[str(wname)] = {"kappa": kappa, "event": parsed_ev, "conditions": parsed_conds, "null_test": parsed_null}
    tau95 = _num(_need(obj, "tau95", "conjunction"), "conjunction.tau95", positive=True)
    z_alpha = _num(obj.get("z_alpha", 1.6448536269514722), "conjunction.z_alpha", positive=True)
    pair = obj.get("pair")
    if pair is not None and not (isinstance(pair, list) and len(pair) == 2):
        _fail("conjunction.pair", "expected [condition, condition]")
    ref = obj.get("reference_window") or sorted(out_w)[-1]
    if ref not in out_w:
        _fail("conjunction.reference_window", f"unknown window {ref!r}")
    return {"tau95": tau95, "z_alpha": z_alpha, "pair": tuple(pair) if pair else None, "windows": out_w, "reference_window": ref}


def candidate_from_obj(obj: Any) -> Candidate:
    if not isinstance(obj, dict):
        _fail("", "candidate file must be a mapping")
    _only(obj, _TOP, "")
    sv = _need(obj, "schema_version", "")
    if sv != 1:
        _fail("schema_version", f"unsupported schema version {sv!r} (this calculator reads 1)")
    cid = _need(obj, "candidate_id", "")
    if not isinstance(cid, str) or not re.match(r"^[A-Za-z0-9_.-]+$", cid):
        _fail("candidate_id", "must be a short identifier [A-Za-z0-9_.-]")
    stat = Statistic.from_obj(_need(obj, "statistic", ""))
    nui = Nuisance.from_obj(_need(obj, "nuisance", ""))
    ses = SesoiCfg.from_obj(_need(obj, "sesoi", ""), stat.unit)
    prior = Prior.from_obj(obj["prior"]) if obj.get("prior") is not None else None
    data = DataCfg.from_obj(_need(obj, "data", ""), nui.units_per_year)
    menu = DesignMenu.from_obj(_need(obj, "design_menu", ""))
    gate = Sourced.from_obj(obj["gate_factor"], "gate_factor", positive=True, maximum=1.0) if obj.get("gate_factor") is not None else None
    chains = tuple(Chain.from_obj(c, i) for i, c in enumerate(obj.get("chains") or []))
    conj = _validate_conjunction(obj["conjunction"]) if obj.get("conjunction") is not None else None
    for ch in chains:
        if ch.kind == "computed" and conj is None:
            _fail(f"chains[{ch.id}]", "a computed chain needs a 'conjunction' block")
    for name, conds in menu.placebo_set_variants.items():
        if conj is None:
            _fail("design_menu.placebo_set_variants", "placebo-set variants need a 'conjunction' block")
        known = set(next(iter(conj["windows"].values()))["conditions"]) | {"null_test"}
        bad = [c for c in conds if c not in known]
        if bad:
            _fail(f"design_menu.placebo_set_variants.{name}", f"unknown condition(s) {bad}")
    pilot = PilotCfg.from_obj(obj["pilot"]) if obj.get("pilot") is not None else None
    exp = []
    for i, e in enumerate(obj.get("expected") or []):
        ep = f"expected[{i}]"
        _only(e, ("key", "value", "rel_tol", "source", "note"), ep)
        key = _need(e, "key", ep)
        if not isinstance(key, str):
            _fail(f"{ep}.key", "must be a text (dotted path into the report)")
        exp.append(Expected(key, _num(_need(e, "value", ep), f"{ep}.value"), _num(e.get("rel_tol", 0.01), f"{ep}.rel_tol", positive=True),
                            Source.from_obj(_need(e, "source", ep), f"{ep}.source"), str(e.get("note", ""))))
    title = _need(obj, "title", "")
    return Candidate(cid, str(title), stat, nui, ses, prior, data, menu, gate, chains, conj, pilot, tuple(exp), str(obj.get("notes", "")))


# ------------------------------------------------------------------------------------------------------------------
# loading, path guard, source verification
# ------------------------------------------------------------------------------------------------------------------
_FORBIDDEN_DIR_PAIRS = (("state", "runs"), ("data", "harvest"))
_FORBIDDEN_NAME_PARTS = ("_L_window" + "_sealed", "weekly_ic" + "_series", "ic_series" + "_")


def guard_path(path: str | Path) -> Path:
    """Refuse any path inside the run-artifact directory, the harvest tree or a sealed file name."""
    p = Path(path)
    parts = [x for x in p.resolve().parts]
    for a, b in _FORBIDDEN_DIR_PAIRS:
        for i in range(len(parts) - 1):
            if parts[i] == a and parts[i + 1] == b:
                raise FeasibilityInputError(f"path {p} lies inside a protected directory ({a}/{b}); refused")
    if any(frag in p.name for frag in _FORBIDDEN_NAME_PARTS):
        raise FeasibilityInputError(f"path {p} names a sealed file; refused")
    return p


def load_candidate(path: str | Path) -> Candidate:
    p = guard_path(path)
    if not p.is_file():
        raise FeasibilityInputError(f"candidate file not found: {p}")
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        import yaml  # local import: JSON candidates need no YAML library

        try:
            obj = yaml.safe_load(text)
        except yaml.YAMLError as exc:  # pragma: no cover - message passthrough
            raise FeasibilityInputError(f"{p}: invalid YAML: {exc}") from exc
    elif p.suffix.lower() == ".json":
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as exc:
            raise FeasibilityInputError(f"{p}: invalid JSON: {exc}") from exc
    else:
        raise FeasibilityInputError(f"{p}: use .yaml, .yml or .json")
    return candidate_from_obj(obj)


def sha256_of_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_sources(cand: Candidate):
    """Yield (location, Source) of every sourced number in the candidate."""
    def walk(prefix: str, x: Any):
        if isinstance(x, Sourced):
            yield prefix, x.source
        elif isinstance(x, Source):
            yield prefix, x
        elif isinstance(x, dict):
            for k, v in x.items():
                yield from walk(f"{prefix}.{k}", v)
        elif isinstance(x, (list, tuple)):
            for i, v in enumerate(x):
                yield from walk(f"{prefix}[{i}]", v)
        elif hasattr(x, "__dataclass_fields__"):
            for fld in x.__dataclass_fields__:
                yield from walk(f"{prefix}.{fld}" if prefix else fld, getattr(x, fld))

    yield from walk("", cand)


def verify_sources(cand: Candidate, repo_root: str | Path) -> list[dict]:
    """Opt-in drift report: compare the recorded sha256 with the file now.  Never raises on drift (append-only files
    legitimately change); a missing file is reported.  Reads only the cited dossier files, never data."""
    root = Path(repo_root)
    seen: dict[str, dict] = {}
    for loc, src in _iter_sources(cand):
        if not src.file or not src.sha256:
            continue
        key = f"{src.file}@{src.sha256}"
        if key in seen:
            seen[key]["locations"].append(loc)
            continue
        target = root / src.file
        try:
            guard_path(target)
        except FeasibilityInputError as exc:
            seen[key] = {"file": src.file, "status": "refused", "detail": str(exc), "locations": [loc]}
            continue
        if not target.is_file():
            seen[key] = {"file": src.file, "status": "missing", "locations": [loc]}
            continue
        now = sha256_of_file(target)
        seen[key] = {"file": src.file, "status": "ok" if now == src.sha256 else "drift", "recorded": src.sha256,
                     "current": now, "locations": [loc]}
    return sorted(seen.values(), key=lambda r: r["file"])
