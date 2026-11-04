"""Data model of a registration under Constitution 3.1 (PRD v3 draft section 3.2 / 3.3, DEC-104 E9) -- loud failure.

The model is DATA: a tree of :class:`Spec` nodes (name, kind, required, allowed values, range, pattern, source).  Three
consumers read the same tree: :func:`validate` (all defects at once, never a default), :func:`json_schema` (export for
other tools) and the lint rules in ``lint.py``.

Doctrine (PRD 3.1 (a)/(b), PRD_ANALYSE "stille Defaults"):

* a missing required field is an issue, never a default; a field that may be ``null`` must still be PRESENT;
* unknown fields are issues (no silent typos);
* a threshold or a null effect carries a derivation reference (file path + test id), never a bare scalar;
* nothing is read from the outside: no market data, no sealed file, no network.

Field names follow the YAML template 3.1 (PRD v3 section 3.3).  The 30 mandatory lines PZ-01..PZ-30 are mapped to their
fields in :data:`PZ_FIELDS`.  Extensions against the template text (each flagged in the README): ``code_sha256``,
``test_pflichten`` (PZ-12), ``decision_rule.variante`` (PZ-16), ``sesoi_curve.punkte``/``horizont_tage``/
``gabelung_etikett``/``persistenz_herkunft``/``persistenz_ref`` (PZ-18).
"""
from __future__ import annotations

import datetime as _dt
import math
import re
from dataclasses import dataclass
from typing import Any

__all__ = [
    "SCHEMA_VERSION", "Spec", "Issue", "RegistrationSchemaError", "SPEC", "PZ_FIELDS", "ALIASES",
    "ALPHA_TEST", "Z_KRIT", "Z_SCREEN", "COHORT_FIRST", "ZONE_X_END", "ZONE_V_START", "ZONE_V_END", "ZONE_K_START_ALL",
    "FAMILIES", "DATA_FAMILIES", "ZONE_K_START", "Family", "SCREEN_VARIANTS", "DECIDED_VARIANT", "ALPHA_STAB",
    "STAB_VOID_MONTHS", "REPORT_LINE_FIELDS",
    "validate", "load_registration", "json_schema", "parse_abschnitt", "required_paths", "pz_of_path", "get_path",
]

SCHEMA_VERSION = "3.1.0"

# --------------------------------------------------------------------------------------------------------------------
# constants taken from the dossier (each with its source)
# --------------------------------------------------------------------------------------------------------------------
ALPHA_TEST = 0.0025                      # DEC-104 E2 (fixed per test); z_krit one-sided pooled 2.8070 (VR-b14)
Z_KRIT = 2.8070
Z_SCREEN = {"a": 1.6449, "a'": 0.8416}   # DEC-104 E2 (screen 0.05); DEC-104 N2 (4) variant (a') screen 0.20
SCREEN_VARIANTS = ("a", "a'", "c")       # DEC-104 N2 (4): (a) screen 0.05, (a') screen 0.20, (c) stability test
DECIDED_VARIANT = "c"                    # DEC-107 (1) (user decision P-2, 2026-11-04): registered stability test
ALPHA_STAB = 0.05                        # DEC-104 N4 (1) / DEC-107 (1): one-sided Welch-t against a drop
STAB_VOID_MONTHS = 12                    # DEC-107 (1) (b): test void with <= 12 months of confirmation data
COHORT_FIRST = _dt.date(2027, 1, 1)      # DEC-104 E4 (f)
ZONE_X_END = _dt.date(2024, 6, 30)       # DEC-104 E4 (a): zone X = everything before 2024-07-01
ZONE_V_START = _dt.date(2024, 7, 1)      # DEC-104 E4 (a): W1/W2
ZONE_V_END = _dt.date(2026, 6, 30)       # DEC-104 N1 (3): V for daily statistics ends 2026-06-30
ZONE_K_START_ALL = _dt.date(2026, 7, 1)  # DEC-96 E3 / DEC-104 E4 (a): seal period
REPORT_LINE_FIELDS = ("estimate", "se", "ci95", "upper_limit95", "n_eff", "c_overlap", "selection_k",
                      "shrinkage_note", "zone")                      # DEC-105 (Pflicht-Berichtszeile)


@dataclass(frozen=True)
class Family:
    """One data family (FENSTERREGISTER section 2 and 6)."""

    code: str
    name: str
    zone_k_start: _dt.date         # first PURE zone-K day (FENSTERREGISTER section 6, "Zone K rein ab")
    v_policy: str                  # "no" | "blind" | "exception" | "non_outcome"  (FENSTERREGISTER section 2)
    rule: str


FAMILIES: dict[str, Family] = {
    "F1": Family("F1", "BTC/ETH aggregates (returns, RV, DVOL/IV, funding BTC/ETH, mid move)", _dt.date(2026, 10, 1),
                 "exception", "zone K prospectively only; zone V only for the A2 r_pre exception (DEC-104 E4 (i))"),
    "F2": Family("F2", "panel cross-sections (daily/weekly returns, characteristics)", _dt.date(2026, 7, 1),
                 "blind", "zone V (W1/W2) only while blind (C.17), zone K; sealed IC series stay unread"),
    "F3": Family("F3", "funding of all perps, OI, turnover", _dt.date(2026, 9, 15),
                 "non_outcome", "zone V only for non-outcome statistics; funding level K from 2026-09-15 (OI/turnover "
                                "2026-07-01 -- the stricter date is used)"),
    "F4": Family("F4", "option chain, settlements, deliveries", _dt.date(2026, 7, 1),
                 "no", "zone K prospectively; snapshot dates from 2026-07 only as counts"),
    "F5": Family("F5", "live streams from 2026-06", _dt.date(2026, 7, 1),
                 "no", "zone K entirely; before cohort 1 counts only"),
    "F6": Family("F6", "trades / order books of 5 symbols", _dt.date(2026, 10, 1),
                 "no", "zone K prospectively for daily aggregates; microstructure K from 2026-10-01"),
}
DATA_FAMILIES = tuple(FAMILIES)                                       # data_family codes
ZONE_K_START = {code: f.zone_k_start for code, f in FAMILIES.items()}  # zone_k_start per data family


# --------------------------------------------------------------------------------------------------------------------
# issues and the spec node
# --------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Issue:
    """One schema defect.  ``code``: missing | null | type | value | unknown | alias."""

    path: str
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: [{self.code}] {self.message}"


class RegistrationSchemaError(ValueError):
    """Raised by :func:`load_registration`; carries every issue."""

    def __init__(self, issues: list[Issue]):
        self.issues = list(issues)
        super().__init__("; ".join(str(i) for i in self.issues[:20]) + (" ..." if len(self.issues) > 20 else ""))


@dataclass(frozen=True)
class Spec:
    """A node of the data model.  No node has a default value: a required field that is absent is an issue."""

    name: str
    kind: str                       # text|num|int|bool|date|enum|sha256|ref|range|sourced_num|list|obj
    required: bool = True
    nullable: bool = False          # may hold an explicit null (the key must still be present)
    pz: str = ""                    # mandatory line this field belongs to (top-level nodes), e.g. "PZ-15"
    src: str = ""                   # dossier source
    allowed: tuple = ()             # enum values
    lo: float | None = None
    hi: float | None = None
    lo_open: bool = False
    hi_open: bool = False
    pattern: str | None = None
    literals: tuple = ()            # extra literal strings accepted by kind sha256
    item: "Spec | None" = None      # list element
    fields: tuple["Spec", ...] = ()  # obj children
    min_items: int = 0
    strict_ref: bool = False        # ref must be "path#test_id"
    doc: str = ""


# small constructors -------------------------------------------------------------------------------------------------
def _t(name, **kw):
    return Spec(name, "text", **kw)


def _n(name, **kw):
    return Spec(name, "num", **kw)


def _i(name, **kw):
    return Spec(name, "int", **kw)


def _b(name, **kw):
    return Spec(name, "bool", **kw)


def _d(name, **kw):
    return Spec(name, "date", **kw)


def _e(name, allowed, **kw):
    return Spec(name, "enum", allowed=tuple(allowed), **kw)


def _h(name, **kw):
    return Spec(name, "sha256", **kw)


def _r(name, strict=True, **kw):
    return Spec(name, "ref", strict_ref=strict, **kw)


def _o(name, *fields, **kw):
    return Spec(name, "obj", fields=tuple(fields), **kw)


def _l(name, item, **kw):
    return Spec(name, "list", item=item, **kw)


_ID = r"^[A-Z]{1,4}-[0-9]{1,4}[A-Za-z0-9_]*$"
_ABSCHNITT = r"^[0-9]{4}-[0-9]{2}-[0-9]{2}\.\.[0-9]{4}-[0-9]{2}-[0-9]{2}$"
_KONTO = r"^O-[0-9]{3}$"                                  # KONTO_INVENTAR_2026-11-02.md row ids O-001.. / O-9xx
_STRESS = r"^(STRESS_REL|STRESS_ABS)[ :@+]+(sha256:)?[0-9a-f]{64}$"
_FILE = r"^\S+$"
_TESTS = ("T0", "T1", "T2", "T3", "T4", "T5", "T6", "T7")  # PZ-12 / PRD 3.3.12
_CONSTANTS_NA = "n/a - kapitalfrei ohne Kostenmodell"      # PRD v3 3.3 template, constants_hash

SPEC: Spec = _o(
    "registration",
    # --- identity ----------------------------------------------------------------------------------------------------
    _t("id", pattern=_ID, src="PRD 3.4; PRD v3 3.3"),
    _e("klasse", ("P", "W", "E"), src="PRD 3.2"),
    _b("capital_free", src="C.2"),
    _t("hypothese", src="PRD 3.4"),
    _t("ertragsquelle", src="PRD 3.4; PZ-09 (c)"),
    _t("metric", src="PRD 3.4"),
    _e("richtung", ("positiv", "negativ"), src="DEC-51 (1)"),
    # --- PZ-14 / PZ-13 / PZ-30 / PZ-25 / PZ-29 -------------------------------------------------------------------------
    _d("cohort", pz="PZ-14", src="DEC-104 E4 (f)"),
    _l("zone", _o("zone_entry",
                  _t("abschnitt", pattern=_ABSCHNITT, doc="YYYY-MM-DD..YYYY-MM-DD"),
                  _e("zone", ("X", "V", "K")),
                  _e("datenfamilie", DATA_FAMILIES, doc="data_family, FENSTERREGISTER section 6"),
                  _d("rein_ab", doc="zone_k_start / pure-from date of this section"),
                  _e("ausnahme", ("a2_r_pre",), required=False, doc="only F1 in zone V (DEC-104 E4 (i))"),
                  _b("outcome_beruehrend", required=False, doc="F3 in zone V: must be false")),
       min_items=1, pz="PZ-13", src="DEC-104 E9, E4 (a); N1 (2); FENSTERREGISTER 6"),
    _t("vorwissens_klasse", pz="PZ-30", src="DEC-104 E4 (i)"),
    _l("lesestatus", _o("lesestatus_zeile",
                        _t("datei", pattern=_FILE),
                        _e("status", ("nie_berechnet", "berechnet_versiegelt_ungelesen", "gelesen"))),
       min_items=1, pz="PZ-25", src="DEC-104 N1 (6); VR-g07"),
    _l("c17_refs", _t("konto_zeile", pattern=_KONTO), pz="PZ-29", src="DEC-104 N1 (1); C.17; VR-d18",
       doc="rows of the account inventory (O-nnn); may be empty only if nothing was opened"),
    _l("windows", _o("window",
                     _t("id", pattern=r"^[A-Za-z0-9_]+$"),
                     _d("von"), _d("bis"),
                     _e("zone", ("X", "V", "K")),
                     _e("rolle", ("urteilstragend", "pilot_nicht_urteilstragend", "aera_profil")),
                     _e("datenfamilie", DATA_FAMILIES, required=False)),
       min_items=1, src="DEC-99 (1); DEC-104 E4 (d)/(e)"),
    # --- decision rule: PZ-15, PZ-16, PZ-01 -----------------------------------------------------------------------------
    _o("decision_rule",
       _n("alpha_test", pz="PZ-15", src="DEC-104 E2", lo=0.0, hi=1.0, lo_open=True, hi_open=True),
       _n("z_krit", src="DEC-94 (1); VR-b14", lo=0.0, lo_open=True),
       _e("variante", SCREEN_VARIANTS, pz="PZ-16", src="DEC-104 E2, N2 (4)"),
       _o("screen", _t("fenster"), _n("alpha", lo=0.0, hi=1.0, lo_open=True, hi_open=True),
          _n("z_krit", lo=0.0, lo_open=True), nullable=True, pz="PZ-16", src="DEC-104 E2, E6"),
       _o("stability_test", _t("statistik"), _n("alpha", lo=0.0, hi=1.0, lo_open=True, hi_open=True),
          _n("kostenquote_q", lo=0.0, hi=1.0, lo_open=True), _t("entfaellt_wenn"), _t("an_blicken"), _r("ref"),
          nullable=True, pz="PZ-16", src="DEC-104 E6, N4 (1)-(3); DEC-107 (1)"),
       _n("power_target_gemeinsam", lo=0.80, hi=1.0, hi_open=True, pz="PZ-01", src="DEC-104 E2"),
       _n("mde_faktor", lo=0.0, lo_open=True, src="DEC-94 (1); never a threshold"),
       src="PZ-15, PZ-16"),
    # --- looks: PZ-17 ---------------------------------------------------------------------------------------------------
    _o("looks",
       _o("zone_v", _i("anzahl", lo=1, hi=1), required=False),
       _o("zone_k",
          _i("anzahl", lo=1, hi=4),
          _e("plan", ("obrien_fleming",)),
          _t("spending"),
          _l("zeitpunkte", _d("blick"), min_items=1),
          _b("screen_an_jedem_stopp"),
          _t("futility"),
          _e("grenzen", ("t_artig",)),
          required=False),
       pz="PZ-17", src="DEC-104 E4 (d)/(e); N2 (5)/(7); VR-d11, VR-d12, VR-f08"),
    # --- SESOI curve: PZ-18 ---------------------------------------------------------------------------------------------
    _o("sesoi_curve",
       _h("kostenmodell_constants_hash"),
       _e("rahmen", ("einzelposition", "dezil_ls")),
       _e("kostenbasis", ("taker_vip0", "maker_vip0")),
       _t("gabelung_etikett"),
       _n("persistenz_phi", lo=-1.0, hi=1.0, hi_open=True),
       _e("persistenz_herkunft", ("gemessen", "default_0_etikett")),
       _r("persistenz_ref", strict=False, nullable=True),
       _i("horizont_tage", lo=1),
       _l("punkte", _o("kurvenpunkt", _i("horizont_tage", lo=1), _n("phi", lo=-1.0, hi=1.0, hi_open=True),
                       _n("sesoi", lo=0.0, lo_open=True)), min_items=1),
       _r("ref"),
       pz="PZ-18", src="DEC-104 E3 (a); DEC-105 (1), (8); N3 (1)"),
    # --- prior: PZ-19 ----------------------------------------------------------------------------------------------------
    _o("prior_label",
       _e("literatur", ("primaer", "sek", "UNBELEGT")),
       _t("prior_verteilung_ref", nullable=True),
       _b("selektionsbereinigt"),
       _o("sensitivitaetsspanne", _t("groesse"), _n("nominal"), _n("untere"), _n("obere"), required=False,
          doc="required when literatur is UNBELEGT; two-sided (untere < nominal < obere)"),
       pz="PZ-19", src="DEC-104 E3 (b)/(c)/(d); VR-c05, VR-c06"),
    # --- threshold / null / nuisance / power ------------------------------------------------------------------------------
    _o("threshold", _t("regel"), _r("ref"), src="DEC-94 (1); PRD 3.1 (b)"),
    _o("structural_null", _l("komponenten", _t("komponente"), min_items=1), _t("skalierung"), _r("ref"),
       src="C.4; VR-e06; PRD 3.1 (b)"),
    _o("nuisance",
       _l("quellen", _e("quelle", ("vorperiode_nur_streuung", "null_simulation")), min_items=1),
       _e("bindend", ("juengstes_vorfenster", "groessere_SE_ueber_quellen_und_stress")),
       _t("stress_zeile"),
       src="DEC-94 (5); DEC-104 E6"),
    _o("power",
       _t("se_regel"),
       _o("sd_teststatistik", _n("wert", lo=0.0, lo_open=True), _r("ref", strict=False)),
       _t("c"),
       _t("blocklaenge"),
       _o("mde80", _n("wert", lo=0.0, lo_open=True), _r("ref")),
       _n("sesoi", lo=0.0, lo_open=True),
       _b("testbar"),
       pz="PZ-01", src="DEC-94 (3)/(4); DEC-104 E2, E3 (a), N2 (6)"),
    _e("cluster_unit", ("kalendertag", "kalenderwoche", "ereignis", "fenster"), pz="PZ-03", src="DEC-51 (3); VR-b03"),
    Spec("n_eff", "sourced_num", pz="PZ-23", src="DEC-51 (3); DEC-105", lo=0.0, lo_open=True),
    Spec("c_overlap", "sourced_num", pz="PZ-24", src="DEC-104 N2 (7); VR-b05", lo=0.0, lo_open=True,
         doc="the lint demands >= 1"),
    # --- selection K: PZ-04 / PZ-20 ----------------------------------------------------------------------------------------
    _o("selection", _i("K"), _i("K_kumuliert_familie"), _n("z_max", lo=0.0, lo_open=True), _r("ceiling_ref"),
       pz="PZ-04", src="DEC-94 (7); DEC-104 N1 (9); VR-b17"),
    _o("design_menu", _l("optionen", _t("option"), min_items=1), _t("auswahlregel"), _t("gewaehlt"),
       pz="PZ-26", src="DEC-104 E5; VR-e01"),
    _l("reachability", _o("erreichbarkeit", _t("parameter"), _i("beobachtungen_in_urteilsfenstern", lo=0)),
       min_items=1, pz="PZ-27", src="DEC-104 E8 (d); VR-f07"),
    _o("oc_line",
       _n("p_pass_0", lo=0.0, hi=1.0), _n("p_pass_sesoi", lo=0.0, hi=1.0), _n("p_pass_prior_median", lo=0.0, hi=1.0),
       _n("p_pass_nur_aelter_1mde", lo=0.0, hi=1.0), _i("seeds", lo=1), _r("ref"),
       pz="PZ-21", src="DEC-104 E8 (a); VR-f04; DEC-107 (1) (d) protection line"),
    _o("strictness_ratio", _n("wert", lo=0.0, lo_open=True), _l("zerlegung", _t("festlegung"), min_items=1),
       _r("gabelungsregister_ref", strict=False),
       pz="PZ-22", src="DEC-104 E8 (b); N1 (9); VR-f05"),
    _o("annual_book", _i("jahr", lo=2027), _n("erwartete_falsch_pass_vorher", lo=0.0),
       _n("mit_dieser_registrierung", lo=0.0),
       pz="PZ-28", src="DEC-104 E4 (g); VR-d14"),
    _o("economic_minimum", _n("wert", lo=0.0), _r("ref", strict=False), _e("label", ("ueber_wand", "unter_wand")),
       pz="PZ-02", src="C.2; PRD 3.3.2"),
    _o("decision_relevance", _t("on_pass"), _t("on_drop"), _t("on_gl012"), pz="PZ-02", src="PRD 3.3.2; VR-g08"),
    _o("capital_tax_venue", _t("kapitalbasis"), _t("steuer"), _t("venue_event"), _t("zahler_post_2024"),
       pz="PZ-09", src="PRD 3.3.9; PRD 8.2"),
    _o("stress_episode", _t("liste_ref", pattern=_STRESS), _e("rolle", ("abdeckungsnachweis",)),
       _i("tage_in_fenstern", lo=0), pz="PZ-10", src="DEC-55/56; DEC-104 E8 (d); VR-g13, VR-f07"),
    _o("irreversibility_probe", _e("ergebnis", ("nachladbar", "irreversibel")), _r("ref", strict=False),
       pz="PZ-07", src="PRD 3.3.7"),
    _o("positive_control", _b("vorgeschaltet"), _b("produktionskonfiguration"), _t("welt"), _t("kriterium"),
       _r("ref", strict=False), pz="PZ-08", src="PRD 3.3.8; VR-f12"),
    _o("fixtures", _t("positive"), _t("null"), _t("adversarial"), pz="PZ-05", src="PRD 3.3.5"),
    _o("test_pflichten", *[_r(t, strict=True) for t in _TESTS], pz="PZ-12", src="PRD 3.3.12",
       doc="one derivation reference (path#test_id) per T0..T7"),
    _o("artifacts", _t("cluster_series_ref"), _t("bootstrap_replicates_ref"), pz="PZ-11", src="DEC-53; DEC-105; VR-f03"),
    _l("report_line", _e("feld", REPORT_LINE_FIELDS), min_items=1, pz="PZ-11", src="DEC-105; VR-f02"),
    _o("fdr", _t("family"), _n("bh_alpha", lo=0.0, hi=1.0, lo_open=True), _t("p"), _t("over_family"),
       _n("kohorte_by_q", lo=0.0, hi=1.0, lo_open=True), src="VR-b16, VR-b17, VR-d13; DEC-104 E4 (f)"),
    Spec("constants_hash", "sha256", pz="PZ-06", src="PRD 3.3.6; VR-g14", literals=(_CONSTANTS_NA,)),
    _l("code_sha256", _o("code", _t("pfad", pattern=_FILE), _h("sha256")), min_items=1,
       src="PRD_ANALYSE section 7 (no number without a versioned script); KONTO_ZONE_X rule 1"),
    _l("data_fingerprints", _t("fingerprint"), min_items=1, src="H-32 precedent (panel, register, code commit, YAML)"),
    _e("feasibility_verdict", ("testbar", "GL-012 strukturell nicht testbar"), src="DEC-104 E3 (a)"),
    _l("etiketten", _t("etikett"), src="PRD v3 3.3"),
)

#: mandatory line -> field paths of this model (PRD v3 section 3.2); every line has at least one required field
PZ_FIELDS: dict[str, tuple[str, ...]] = {
    "PZ-01": ("power", "decision_rule.power_target_gemeinsam", "decision_rule.mde_faktor"),
    "PZ-02": ("decision_relevance", "economic_minimum"),
    "PZ-03": ("cluster_unit",),
    "PZ-04": ("selection",),
    "PZ-05": ("fixtures",),
    "PZ-06": ("constants_hash",),
    "PZ-07": ("irreversibility_probe",),
    "PZ-08": ("positive_control",),
    "PZ-09": ("capital_tax_venue",),
    "PZ-10": ("stress_episode",),
    "PZ-11": ("artifacts", "report_line"),
    "PZ-12": ("test_pflichten",),
    "PZ-13": ("zone",),
    "PZ-14": ("cohort",),
    "PZ-15": ("decision_rule.alpha_test",),
    "PZ-16": ("decision_rule.variante", "decision_rule.screen", "decision_rule.stability_test"),
    "PZ-17": ("looks",),
    "PZ-18": ("sesoi_curve",),
    "PZ-19": ("prior_label",),
    "PZ-20": ("selection.K",),
    "PZ-21": ("oc_line",),
    "PZ-22": ("strictness_ratio",),
    "PZ-23": ("n_eff",),
    "PZ-24": ("c_overlap",),
    "PZ-25": ("lesestatus",),
    "PZ-26": ("design_menu",),
    "PZ-27": ("reachability",),
    "PZ-28": ("annual_book",),
    "PZ-29": ("c17_refs",),
    "PZ-30": ("vorwissens_klasse",),
}

#: accepted alternative spellings (normalised at load time; both present is an issue)
ALIASES: dict[str, str] = {"c17_list": "c17_refs"}


# --------------------------------------------------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------------------------------------------------
_SHA = re.compile(r"^[0-9a-f]{64}$")
_REF_STRICT = re.compile(r"^[^\s#]+#[^\s#]+$")
_REF_PATH = re.compile(r"^[^\s#]+(#[^\s#]+)?$")


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def _parse_date(x: Any) -> _dt.date | None:
    if isinstance(x, _dt.datetime):
        return None
    if isinstance(x, _dt.date):
        return x
    if isinstance(x, str):
        try:
            d = _dt.date.fromisoformat(x)
        except ValueError:
            return None
        return d if d.isoformat() == x else None
    return None


def parse_abschnitt(s: str) -> tuple[_dt.date, _dt.date]:
    """``"YYYY-MM-DD..YYYY-MM-DD"`` -> (von, bis); raises ``ValueError`` for anything else."""
    von, sep, bis = str(s).partition("..")
    a, b = _parse_date(von), _parse_date(bis)
    if not sep or a is None or b is None:
        raise ValueError(f"not an interval 'YYYY-MM-DD..YYYY-MM-DD': {s!r}")
    return a, b


def _range_ok(spec: Spec, v: float, path: str, issues: list[Issue]) -> bool:
    if spec.lo is not None and (v < spec.lo or (spec.lo_open and v == spec.lo)):
        issues.append(Issue(path, "value", f"must be {'>' if spec.lo_open else '>='} {spec.lo}, got {v}"))
        return False
    if spec.hi is not None and (v > spec.hi or (spec.hi_open and v == spec.hi)):
        issues.append(Issue(path, "value", f"must be {'<' if spec.hi_open else '<='} {spec.hi}, got {v}"))
        return False
    return True


def _check(spec: Spec, v: Any, path: str, issues: list[Issue]) -> Any:
    """Validate ``v`` against ``spec``; returns the normalised value (dates -> ``datetime.date``)."""
    k = spec.kind
    if k == "text":
        if not isinstance(v, str) or not v.strip():
            issues.append(Issue(path, "type", f"expected a non-empty text, got {v!r}"))
            return None
        if spec.pattern and not re.match(spec.pattern, v):
            issues.append(Issue(path, "value", f"does not match {spec.pattern}: {v!r}"))
        elif spec.name == "abschnitt":
            try:
                a, b = parse_abschnitt(v)
                if b < a:
                    issues.append(Issue(path, "value", "interval end before start"))
            except ValueError as exc:
                issues.append(Issue(path, "value", str(exc)))
        return v
    if k in ("num", "int"):
        if k == "int":
            if isinstance(v, bool) or not isinstance(v, int):
                issues.append(Issue(path, "type", f"expected an integer, got {v!r}"))
                return None
        elif not _is_num(v):
            issues.append(Issue(path, "type", f"expected a finite number, got {v!r}"))
            return None
        _range_ok(spec, float(v), path, issues)
        return v
    if k == "sourced_num":
        if _is_num(v):
            _range_ok(spec, float(v), path, issues)
            return float(v)
        if isinstance(v, dict):
            sub = _o("sourced", _n("wert", lo=spec.lo, lo_open=spec.lo_open), _r("ref", strict=False))
            out = _check(sub, v, path, issues)
            return None if out is None else float(out["wert"]) if _is_num(out.get("wert")) else None
        issues.append(Issue(path, "type", f"expected a number or {{wert, ref}}, got {v!r}"))
        return None
    if k == "bool":
        if not isinstance(v, bool):
            issues.append(Issue(path, "type", f"expected true/false, got {v!r}"))
            return None
        return v
    if k == "date":
        d = _parse_date(v)
        if d is None:
            issues.append(Issue(path, "type", f"expected an ISO date YYYY-MM-DD, got {v!r}"))
        return d
    if k == "enum":
        if v not in spec.allowed or isinstance(v, bool):
            issues.append(Issue(path, "value", f"must be one of {list(spec.allowed)}, got {v!r}"))
            return None
        return v
    if k == "sha256":
        if isinstance(v, str) and (_SHA.match(v) or v in spec.literals):
            return v
        extra = f" or {list(spec.literals)}" if spec.literals else ""
        issues.append(Issue(path, "value", f"expected 64 lowercase hex characters{extra}, got {v!r}"))
        return None
    if k == "ref":
        rx = _REF_STRICT if spec.strict_ref else _REF_PATH
        if not isinstance(v, str) or not rx.match(v):
            what = "path#test_id" if spec.strict_ref else "path or path#test_id"
            issues.append(Issue(path, "value", f"expected a derivation reference '{what}' without blanks, got {v!r}"))
            return None
        return v
    if k == "list":
        if not isinstance(v, list):
            issues.append(Issue(path, "type", f"expected a list, got {type(v).__name__}"))
            return None
        if len(v) < spec.min_items:
            issues.append(Issue(path, "value", f"needs at least {spec.min_items} item(s), got {len(v)}"))
        assert spec.item is not None
        return [_check_item(spec.item, x, f"{path}[{i}]", issues) for i, x in enumerate(v)]
    if k == "obj":
        if not isinstance(v, dict):
            issues.append(Issue(path, "type", f"expected a mapping, got {type(v).__name__}"))
            return None
        out: dict[str, Any] = {}
        for f in spec.fields:
            p = f"{path}.{f.name}" if path else f.name
            if f.name not in v:
                if f.required:
                    issues.append(Issue(p, "missing", "required field missing (no default exists)"))
                continue
            if v[f.name] is None:
                if f.nullable:
                    out[f.name] = None
                else:
                    issues.append(Issue(p, "null", "required field is null (no default exists)"))
                continue
            out[f.name] = _check(f, v[f.name], p, issues)
        for extra in sorted(set(v) - {f.name for f in spec.fields}, key=str):
            p = f"{path}.{extra}" if path else str(extra)
            issues.append(Issue(p, "unknown", f"unknown field; allowed {[f.name for f in spec.fields]}"))
        return out
    raise AssertionError(f"unknown spec kind {k}")


def _check_item(spec: Spec, v: Any, path: str, issues: list[Issue]) -> Any:
    if v is None:
        issues.append(Issue(path, "null", "list item is null"))
        return None
    return _check(spec, v, path, issues)


def validate(obj: Any) -> tuple[dict[str, Any], list[Issue]]:
    """Validate a loaded registration; returns (normalised data, issues).  Never raises, never fills a default."""
    issues: list[Issue] = []
    if not isinstance(obj, dict):
        return {}, [Issue("", "type", f"the registration must be a mapping, got {type(obj).__name__}")]
    obj = dict(obj)
    for alias, canon in ALIASES.items():
        if alias in obj:
            if canon in obj:
                issues.append(Issue(alias, "alias", f"both '{alias}' and '{canon}' present"))
                del obj[alias]
            else:
                obj[canon] = obj.pop(alias)
    data = _check(SPEC, obj, "", issues)
    return data if isinstance(data, dict) else {}, issues


def load_registration(path: str) -> dict[str, Any]:
    """Read a YAML file and validate it; raises :class:`RegistrationSchemaError` listing every defect."""
    import yaml  # local import: pyyaml is the only third-party dependency

    with open(path, encoding="utf-8") as fh:
        obj = yaml.safe_load(fh)
    data, issues = validate(obj)
    if issues:
        raise RegistrationSchemaError(issues)
    return data


# --------------------------------------------------------------------------------------------------------------------
# helpers over the model
# --------------------------------------------------------------------------------------------------------------------
def get_path(d: Any, dotted: str, default: Any = None) -> Any:
    """``get_path(d, "a.b")`` for nested mappings; ``default`` if a step is missing."""
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def required_paths(spec: Spec = SPEC, prefix: str = "") -> list[tuple[str, Spec]]:
    """Dotted paths of all required object fields (list items are not entered)."""
    out: list[tuple[str, Spec]] = []
    for f in spec.fields:
        p = f"{prefix}.{f.name}" if prefix else f.name
        if f.required:
            out.append((p, f))
        if f.kind == "obj":
            out.extend(required_paths(f, p))
    return out


def pz_of_path(path: str) -> str:
    """Mandatory line a schema issue path belongs to ("" if none)."""
    norm = re.sub(r"\[\d+\]", "", path)
    if not norm:
        return ""
    passes = (lambda p: norm == p,                       # the issue lies exactly at a mapped field
              lambda p: norm.startswith(p + "."),        # below a mapped field
              lambda p: p.startswith(norm + "."))        # above a mapped field (a whole block missing)
    for test in passes:
        for pz, paths in PZ_FIELDS.items():
            if any(test(p) for p in paths):
                return pz
    return ""


def json_schema() -> dict[str, Any]:
    """JSON Schema (draft 2020-12) generated from the same tree as :func:`validate` (YAML dates are strings there)."""

    def node(s: Spec) -> dict[str, Any]:
        k = s.kind
        if k == "text":
            d: dict[str, Any] = {"type": "string", "minLength": 1}
            if s.pattern:
                d["pattern"] = s.pattern
        elif k == "num" or k == "int":
            d = {"type": "integer" if k == "int" else "number"}
            if s.lo is not None:
                d["exclusiveMinimum" if s.lo_open else "minimum"] = s.lo
            if s.hi is not None:
                d["exclusiveMaximum" if s.hi_open else "maximum"] = s.hi
        elif k == "sourced_num":
            d = {"oneOf": [{"type": "number"}, {"type": "object", "required": ["wert", "ref"],
                                                "properties": {"wert": {"type": "number"}, "ref": {"type": "string"}},
                                                "additionalProperties": False}]}
        elif k == "bool":
            d = {"type": "boolean"}
        elif k == "date":
            d = {"type": "string", "format": "date"}
        elif k == "enum":
            d = {"enum": list(s.allowed)}
        elif k == "sha256":
            d = {"anyOf": [{"type": "string", "pattern": "^[0-9a-f]{64}$"}] + [{"const": x} for x in s.literals]}
        elif k == "ref":
            d = {"type": "string", "pattern": _REF_STRICT.pattern if s.strict_ref else _REF_PATH.pattern}
        elif k == "list":
            assert s.item is not None
            d = {"type": "array", "items": node(s.item), "minItems": s.min_items}
        elif k == "obj":
            d = {"type": "object", "additionalProperties": False,
                 "properties": {f.name: node(f) for f in s.fields},
                 "required": [f.name for f in s.fields if f.required]}
        else:  # pragma: no cover
            raise AssertionError(k)
        if s.nullable:
            d = {"anyOf": [d, {"type": "null"}]}
        meta = " | ".join(x for x in (s.pz, s.src, s.doc) if x)
        if meta:
            d["description"] = meta
        return d

    root = node(SPEC)
    # no "$schema" URL on purpose: the dialect is JSON Schema draft 2020-12 and no host name belongs in the repository text
    root["title"] = f"Registration under Constitution 3.1 (schema {SCHEMA_VERSION})"
    return root
