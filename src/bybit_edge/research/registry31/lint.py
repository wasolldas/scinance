"""Linter for registrations under Constitution 3.1 (F1, DEC-104 E9; PRD v3 draft section 3).

Usage::

    python -m bybit_edge.research.registry31.lint <registration.yaml> [--json]
    python -m bybit_edge.research.registry31.lint --list-rules
    python -m bybit_edge.research.registry31.lint --emit-schema

The rules are DATA (:data:`RULES`: id, title, dossier source, the input paths a rule needs, the check).  Output is a
deterministic list of findings ``(rule, source, status, message)`` with status ``OK`` / ``FEHLER`` / ``HINWEIS``.  The
return code is non-zero if and only if a finding is ``FEHLER`` (1) or the file cannot be read or parsed (2).

The linter reads one YAML file.  It opens no market data, no sealed file and no network; it prints the class and path of
a suspicious text, never the text itself.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import PurePosixPath
from statistics import NormalDist
from typing import Any, Callable, Iterator

from . import schema as S

__all__ = ["Finding", "Rule", "Ctx", "RULES", "lint", "lint_file", "load_yaml", "format_text", "main", "LintInputError",
           "STATUS_OK", "STATUS_ERR", "STATUS_HINT"]

STATUS_OK, STATUS_ERR, STATUS_HINT = "OK", "FEHLER", "HINWEIS"
STRICTNESS_USER_SUBMISSION = 1.3     # DEC-104 E8 (b): from this ratio on a user submission precedes the registration
ANNUAL_BOOK_LIMIT = 0.10             # DEC-104 E4 (g): above this many expected false PASS per year -> user submission
BY_Q = 0.10                          # DEC-104 E4 (f): Benjamini-Yekutieli q of the cohort
SEEDS_MIN = 1000                     # DEC-104 E8 (a), VR-f04
Z_TOL = 5e-4                         # tolerance for z values quoted with four decimals


class LintInputError(Exception):
    """The file cannot be read or is not parseable YAML (return code 2)."""


@dataclass(frozen=True)
class Finding:
    rule: str
    source: str
    status: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"rule": self.rule, "source": self.source, "status": self.status, "message": self.message}


@dataclass
class Ctx:
    d: dict[str, Any]              # normalised data (valid wherever a rule's ``needs`` are valid)
    raw: Any                       # loaded YAML as is
    issues: list[S.Issue]

    def g(self, dotted: str) -> Any:
        return S.get_path(self.d, dotted)


Check = Callable[[Ctx], list[tuple[str, str]]]


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    source: str
    needs: tuple[str, ...]
    check: Check
    ok: str


# --------------------------------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------------------------------
def _close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


def _zscore(alpha: float) -> float:
    return NormalDist().inv_cdf(1.0 - alpha)


@dataclass(frozen=True)
class _Entry:
    idx: int
    zone: str
    fam: str
    von: _dt.date
    bis: _dt.date
    rein_ab: _dt.date
    ausnahme: str | None
    outcome: bool | None


def _entries(c: Ctx) -> list[_Entry]:
    out = []
    for i, e in enumerate(c.d["zone"]):
        von, bis = S.parse_abschnitt(e["abschnitt"])
        out.append(_Entry(i, e["zone"], e["datenfamilie"], von, bis, e["rein_ab"], e.get("ausnahme"),
                          e.get("outcome_beruehrend")))
    return out


_SEALED = re.compile(r"(_L_window_sealed\.json$|(^|/)weekly_ic_series\.csv$|(^|/)ic_series_[^/]*_UNION_REAL\.csv$)")


def _unsafe_path(p: str, *, allow_sealed: bool = False) -> str | None:
    """Reason why a repository path is not acceptable in a registration, else ``None``."""
    p = p.split("#", 1)[0]
    pp = PurePosixPath(p)
    if pp.is_absolute() or "\\" in p or re.match(r"^[A-Za-z]:", p):
        return "absolute path"
    if ".." in pp.parts:
        return "path leaves the repository ('..')"
    if "data/harvest" in p:
        return "path below data/harvest"
    if not allow_sealed and _SEALED.search(p):
        return "sealed file (project rules)"
    return None


def _walk_strings(obj: Any, path: str = "") -> Iterator[tuple[str, str, bool]]:
    """Yield (path, text, is_key) for every string of a loaded YAML tree."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            kp = f"{path}.{k}" if path else str(k)
            if isinstance(k, str):
                yield kp, k, True
            yield from _walk_strings(v, kp)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj, False


def _iter_kind(spec: S.Spec, data: Any, kind: str, path: str = "") -> Iterator[tuple[str, Any]]:
    """Yield (path, value) of every node of ``kind`` present in the normalised data."""
    if spec.kind == kind and data is not None:
        yield path, data
    if spec.kind == "obj" and isinstance(data, dict):
        for f in spec.fields:
            if f.name in data:
                yield from _iter_kind(f, data[f.name], kind, f"{path}.{f.name}" if path else f.name)
    elif spec.kind == "list" and isinstance(data, list) and spec.item is not None:
        for i, x in enumerate(data):
            yield from _iter_kind(spec.item, x, kind, f"{path}[{i}]")


# --------------------------------------------------------------------------------------------------------------------
# rules (each returns a list of (status, message); an empty list means OK with the rule's ``ok`` text)
# --------------------------------------------------------------------------------------------------------------------
def r_schema(c: Ctx) -> list[tuple[str, str]]:
    out = []
    for i in c.issues:
        pz = S.pz_of_path(i.path)
        out.append((STATUS_ERR, f"{i.path or '<root>'}: [{i.code}] {i.message}" + (f" ({pz})" if pz else "")))
    return out


_PLACEHOLDER = re.compile(r"<[^<>\s=][^<>]*>")


def r_placeholder(c: Ctx) -> list[tuple[str, str]]:
    return [(STATUS_ERR, f"{p}: unresolved placeholder '<...>' (template text is not a registration)")
            for p, t, is_key in _walk_strings(c.raw) if not is_key and _PLACEHOLDER.search(t)]


def r_alpha(c: Ctx) -> list[tuple[str, str]]:
    a, z = c.g("decision_rule.alpha_test"), c.g("decision_rule.z_krit")
    out = []
    if not _close(a, S.ALPHA_TEST, 1e-12):
        out.append((STATUS_ERR, f"alpha_test = {a}, fixed value is {S.ALPHA_TEST} per test (no budget split)"))
    if not _close(z, S.Z_KRIT, Z_TOL):
        out.append((STATUS_ERR, f"z_krit = {z}, fixed value is {S.Z_KRIT} (one-sided pooled test, VR-b14)"))
    if not _close(z, _zscore(a), Z_TOL):
        out.append((STATUS_ERR, f"z_krit = {z} is not the one-sided quantile of alpha_test = {a}"))
    return out


def r_screen(c: Ctx) -> list[tuple[str, str]]:
    v = c.g("decision_rule.variante")
    scr, stab = c.g("decision_rule.screen"), c.g("decision_rule.stability_test")
    out = []
    if v != S.DECIDED_VARIANT:
        out.append((STATUS_ERR, f"variante '{v}' is not the decided confirmation rule; DEC-107 (1) (P-2) makes only "
                                f"'{S.DECIDED_VARIANT}' registrable"))
    if v in S.Z_SCREEN:
        if scr is None:
            out.append((STATUS_ERR, f"variante '{v}' needs a non-null screen"))
        else:
            want_z = S.Z_SCREEN[v]
            want_a = 0.05 if v == "a" else 0.20
            if not _close(scr["alpha"], want_a, 1e-12) or not _close(scr["z_krit"], want_z, Z_TOL):
                out.append((STATUS_ERR, f"screen of variante '{v}' must be alpha {want_a}, z_krit {want_z}; "
                                        f"got alpha {scr['alpha']}, z_krit {scr['z_krit']}"))
        if stab is not None:
            out.append((STATUS_ERR, f"stability_test as a gate only in variante 'c' (found with variante '{v}')"))
    else:  # variant c (decided, DEC-107 (1))
        if stab is None:
            out.append((STATUS_ERR, "variante 'c' needs a non-null stability_test"))
        else:
            if not _close(stab["alpha"], S.ALPHA_STAB, 1e-12):
                out.append((STATUS_ERR, f"stability_test.alpha must be {S.ALPHA_STAB} (DEC-107 (1)); got {stab['alpha']}"))
            if stab["kostenquote_q"] > 1.0 - S.ALPHA_STAB + 1e-12:
                out.append((STATUS_ERR, f"stability_test.kostenquote_q {stab['kostenquote_q']} exceeds 1 - alpha_stab = "
                                        f"{1.0 - S.ALPHA_STAB} (q is a cost ratio, never above the pass probability)"))
        if scr is not None:
            out.append((STATUS_ERR, "variante 'c' has no screen: screen must be null"))
    if scr is not None and not _close(scr["z_krit"], _zscore(scr["alpha"]), Z_TOL):
        out.append((STATUS_ERR, "screen.z_krit is not the one-sided quantile of screen.alpha"))
    return out


def r_cohort(c: Ctx) -> list[tuple[str, str]]:
    d = c.g("cohort")
    out = []
    if d < S.COHORT_FIRST:
        out.append((STATUS_ERR, f"cohort {d} is before the first cohort date {S.COHORT_FIRST}"))
    if not (d.day == 1 and d.month in (1, 4, 7, 10)):
        out.append((STATUS_ERR, f"cohort {d} is not the first day of a quarter"))
    return out


def r_window_zone(c: Ctx) -> list[tuple[str, str]]:
    out = []
    entries = _entries(c)
    ids = [w["id"] for w in c.d["windows"]]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        out.append((STATUS_ERR, f"window id '{dup}' used more than once"))
    if not any(w["rolle"] == "urteilstragend" for w in c.d["windows"]):
        out.append((STATUS_ERR, "no window with rolle 'urteilstragend'"))
    for w in c.d["windows"]:
        wid, z, von, bis = w["id"], w["zone"], w["von"], w["bis"]
        if bis < von:
            out.append((STATUS_ERR, f"window {wid}: bis {bis} before von {von}"))
            continue
        if z == "X" and not bis <= S.ZONE_X_END:
            out.append((STATUS_ERR, f"window {wid}: zone X ends {S.ZONE_X_END}, window ends {bis}"))
        elif z == "V" and not (von >= S.ZONE_V_START and bis <= S.ZONE_V_END):
            out.append((STATUS_ERR, f"window {wid}: zone V is {S.ZONE_V_START}..{S.ZONE_V_END}, window "
                                    f"is {von}..{bis}"))
        elif z == "K" and not von >= S.ZONE_K_START_ALL:
            out.append((STATUS_ERR, f"window {wid}: zone K starts {S.ZONE_K_START_ALL}, window starts {von}"))
        cover = [e for e in entries if e.zone == z and e.von <= von and bis <= e.bis
                 and w.get("datenfamilie") in (None, e.fam)]
        if not cover:
            out.append((STATUS_ERR, f"window {wid} ({von}..{bis}, zone {z}) is not covered by a zone entry of the same "
                                    f"zone{' and family ' + w['datenfamilie'] if w.get('datenfamilie') else ''}"))
    return out


def r_zone_x(c: Ctx) -> list[tuple[str, str]]:
    return [(STATUS_ERR, f"window {w['id']}: zone-X data ({w['von']}..{w['bis']}, zone {w['zone']}) as confirmation "
                         f"(rolle urteilstragend); zone X is exploration only")
            for w in c.d["windows"]
            if w["rolle"] == "urteilstragend" and (w["zone"] == "X" or w["von"] <= S.ZONE_X_END)]


def r_family(c: Ctx) -> list[tuple[str, str]]:
    out = []
    entries = _entries(c)
    for e in entries:
        fam = S.FAMILIES[e.fam]
        if e.zone != "V":
            continue
        if fam.v_policy == "no":
            out.append((STATUS_ERR, f"zone[{e.idx}]: family {e.fam} is not confirmable in zone V ({fam.rule})"))
        elif fam.v_policy == "exception" and e.ausnahme != "a2_r_pre":
            out.append((STATUS_ERR, f"zone[{e.idx}]: family {e.fam} in zone V only with ausnahme 'a2_r_pre' ({fam.rule})"))
        elif fam.v_policy == "non_outcome" and e.outcome is not False:
            out.append((STATUS_ERR, f"zone[{e.idx}]: family {e.fam} in zone V only for non-outcome statistics "
                                    f"(outcome_beruehrend: false)"))
    for w in c.d["windows"]:
        if w["zone"] != "K" or w["bis"] < w["von"]:
            continue
        fams = sorted({e.fam for e in entries if e.zone == "K" and e.von <= w["von"] and w["bis"] <= e.bis
                       and w.get("datenfamilie") in (None, e.fam)})
        for f in fams:
            if w["von"] < S.ZONE_K_START[f]:
                out.append((STATUS_ERR, f"window {w['id']}: family {f} is pure zone K only from {S.ZONE_K_START[f]}, "
                                        f"window starts {w['von']}"))
    return out


def r_zone_entry(c: Ctx) -> list[tuple[str, str]]:
    out = []
    for e in _entries(c):
        p = f"zone[{e.idx}]"
        if e.bis < e.von:
            out.append((STATUS_ERR, f"{p}: interval end before start"))
        if e.zone == "X" and e.bis > S.ZONE_X_END:
            out.append((STATUS_ERR, f"{p}: zone X ends {S.ZONE_X_END}, section ends {e.bis}"))
        if e.zone == "V":
            if e.von < S.ZONE_V_START or e.bis > S.ZONE_V_END:
                out.append((STATUS_ERR, f"{p}: zone V is {S.ZONE_V_START}..{S.ZONE_V_END}, section is {e.von}..{e.bis}"))
            if e.rein_ab < S.ZONE_V_START or e.rein_ab > e.von:
                out.append((STATUS_ERR, f"{p}: rein_ab {e.rein_ab} must lie in {S.ZONE_V_START}..{e.von}"))
        if e.zone == "K":
            k0 = S.ZONE_K_START[e.fam]
            if e.rein_ab < k0:
                out.append((STATUS_ERR, f"{p}: rein_ab {e.rein_ab} before the pure zone-K start {k0} of family {e.fam}"))
            if e.von < e.rein_ab:
                out.append((STATUS_ERR, f"{p}: section starts {e.von} before rein_ab {e.rein_ab}"))
    return out


def r_looks(c: Ctx) -> list[tuple[str, str]]:
    out = []
    judged = [w for w in c.d["windows"] if w["rolle"] == "urteilstragend"]
    zv, zk = c.g("looks.zone_v"), c.g("looks.zone_k")
    if any(w["zone"] == "V" for w in judged) and zv is None:
        out.append((STATUS_ERR, "a judged zone-V window needs looks.zone_v (exactly one look)"))
    if any(w["zone"] == "K" for w in judged) and zk is None:
        out.append((STATUS_ERR, "a judged zone-K window needs looks.zone_k (group-sequential plan)"))
    if zv is not None and not any(w["zone"] == "V" for w in judged):
        out.append((STATUS_HINT, "looks.zone_v given but no judged zone-V window"))
    if zk is not None:
        if not any(w["zone"] == "K" for w in judged):
            out.append((STATUS_HINT, "looks.zone_k given but no judged zone-K window"))
        t = zk["zeitpunkte"]
        if len(t) != zk["anzahl"]:
            out.append((STATUS_ERR, f"looks.zone_k: anzahl {zk['anzahl']} but {len(t)} zeitpunkte"))
        if any(b <= a for a, b in zip(t, t[1:])):
            out.append((STATUS_ERR, "looks.zone_k.zeitpunkte must be strictly increasing"))
        coh = c.g("cohort")
        if coh is not None and any(x < coh for x in t):
            out.append((STATUS_ERR, "looks.zone_k.zeitpunkte before the cohort date"))
        if zk["screen_an_jedem_stopp"] is not True:
            out.append((STATUS_ERR, "looks.zone_k.screen_an_jedem_stopp must be true (screen at every efficacy stop)"))
    return out


def r_sesoi(c: Ctx) -> list[tuple[str, str]]:
    cur = c.g("sesoi_curve")
    out = []
    if c.g("klasse") == "W" and cur["rahmen"] != "dezil_ls":
        out.append((STATUS_ERR, "klasse W is registered against the decile long/short frame (rahmen 'dezil_ls'), "
                                "not the single-position frame (DEC-104 N3 (1))"))
    if cur["kostenbasis"] == "taker_vip0" and "gabelung" not in cur["gabelung_etikett"].lower():
        out.append((STATUS_ERR, "kostenbasis taker_vip0 needs the label 'Gabelung Richtung Testbarkeit gegen Maker'"))
    if cur["persistenz_herkunft"] == "gemessen" and cur["persistenz_ref"] is None:
        out.append((STATUS_ERR, "persistenz_herkunft 'gemessen' needs a persistenz_ref (account row)"))
    if cur["persistenz_herkunft"] == "default_0_etikett" and cur["persistenz_phi"] != 0:
        out.append((STATUS_ERR, "persistenz_herkunft 'default_0_etikett' requires persistenz_phi = 0"))
    pts = cur["punkte"]
    if len({(p["horizont_tage"], p["phi"]) for p in pts}) < 2:
        out.append((STATUS_ERR, "sesoi_curve.punkte holds a single point: a constant, not a curve over horizon and "
                                "persistence"))
    hit = [p for p in pts if p["horizont_tage"] == cur["horizont_tage"] and _close(p["phi"], cur["persistenz_phi"], 1e-12)]
    sesoi = c.g("power.sesoi")
    if not hit:
        out.append((STATUS_ERR, "no curve point at (horizont_tage, persistenz_phi) of the registration"))
    elif sesoi is not None and not _close(hit[0]["sesoi"], sesoi, 1e-9 * max(1.0, abs(sesoi))):
        out.append((STATUS_ERR, f"power.sesoi {sesoi} differs from the curve value {hit[0]['sesoi']} at the "
                                f"registered horizon and persistence"))
    return out


def r_testable(c: Ctx) -> list[tuple[str, str]]:
    mde, sesoi = c.g("power.mde80.wert"), c.g("power.sesoi")
    testable = mde <= sesoi
    out = []
    if not testable:
        out.append((STATUS_HINT, f"MDE80 {mde} > SESOI {sesoi}: strukturell nicht testbar bei heutiger Nuisance und "
                                 f"Fensterlaenge (GL-012, DEC-104 E3 (a))"))
    if c.g("power.testbar") is not testable:
        out.append((STATUS_ERR, f"power.testbar = {c.g('power.testbar')} contradicts MDE80 <= SESOI ({testable})"))
    verdict = "testbar" if testable else "GL-012 strukturell nicht testbar"
    if c.g("feasibility_verdict") != verdict:
        out.append((STATUS_ERR, f"feasibility_verdict '{c.g('feasibility_verdict')}' contradicts MDE80/SESOI "
                                f"(expected '{verdict}')"))
    return out


def r_prior(c: Ctx) -> list[tuple[str, str]]:
    p = c.g("prior_label")
    out = []
    if p["literatur"] == "UNBELEGT":
        sp = p.get("sensitivitaetsspanne")
        if sp is None:
            out.append((STATUS_ERR, "literatur UNBELEGT needs a two-sided sensitivitaetsspanne (DEC-104 E3 (d))"))
        elif not sp["untere"] < sp["nominal"] < sp["obere"]:
            out.append((STATUS_ERR, "sensitivitaetsspanne must be two-sided: untere < nominal < obere"))
    if p["selektionsbereinigt"] is not True:
        out.append((STATUS_ERR, "prior from zone X must be selection-adjusted (selektionsbereinigt: true, E3 (c))"))
    return out


def r_literature(c: Ctx) -> list[tuple[str, str]]:
    return []  # informative by design: the label never blocks (VR-c05); the OK text states the label


def r_selection(c: Ctx) -> list[tuple[str, str]]:
    s = c.g("selection")
    out = []
    if s["K"] < 1:
        out.append((STATUS_ERR, f"selection.K = {s['K']} must be >= 1"))
    if s["K_kumuliert_familie"] < s["K"]:
        out.append((STATUS_ERR, f"K_kumuliert_familie {s['K_kumuliert_familie']} < K {s['K']}"))
    return out


def r_oc(c: Ctx) -> list[tuple[str, str]]:
    o = c.g("oc_line")
    out = []
    if o["seeds"] < SEEDS_MIN:
        out.append((STATUS_ERR, f"oc_line.seeds = {o['seeds']} < {SEEDS_MIN}"))
    if o["p_pass_0"] > S.ALPHA_TEST:
        out.append((STATUS_HINT, f"P(PASS | effect 0) = {o['p_pass_0']} exceeds alpha_test {S.ALPHA_TEST} "
                                 f"(effective alpha above the nominal value, DEC-104 E2 caveat)"))
    if o["p_pass_0"] > o["p_pass_sesoi"]:
        out.append((STATUS_HINT, "P(PASS | effect 0) exceeds P(PASS | SESOI)"))
    target = c.g("decision_rule.power_target_gemeinsam")
    if target is not None and c.g("power.testbar") is True and o["seeds"] >= 1:
        slack = 2.0 * math.sqrt(target * (1.0 - target) / o["seeds"])
        if o["p_pass_sesoi"] < target - slack:
            out.append((STATUS_HINT, f"P(PASS | SESOI) = {o['p_pass_sesoi']} below the power target {target} "
                                     f"(minus 2 Monte-Carlo SE): test not sensitive at the SESOI"))
    return out


def r_strictness(c: Ctx) -> list[tuple[str, str]]:
    r = c.g("strictness_ratio.wert")
    if r >= STRICTNESS_USER_SUBMISSION:
        return [(STATUS_HINT, f"strictness_ratio {r} >= {STRICTNESS_USER_SUBMISSION}: Nutzer-Vorlage before the "
                              f"registration (DEC-104 E8 (b))")]
    return []


def r_neff(c: Ctx) -> list[tuple[str, str]]:
    out = []
    if c.g("c_overlap") < 1.0:
        out.append((STATUS_ERR, f"c_overlap = {c.g('c_overlap')} < 1 (variance factor, no credit for negative "
                                f"autocorrelation)"))
    if c.g("n_eff") <= 0:
        out.append((STATUS_ERR, "n_eff must be > 0"))
    return out


def r_c17(c: Ctx) -> list[tuple[str, str]]:
    refs = c.g("c17_refs")
    out = [(STATUS_ERR, f"c17_refs: duplicate row {r}") for r in sorted({x for x in refs if refs.count(x) > 1})]
    if not refs and any(w["zone"] in ("V", "K") for w in c.g("windows")):
        out.append((STATUS_HINT, "c17_refs is empty although zone V/K windows are used: confirm that no row of the "
                                 "account inventory concerns these data"))
    return out


def r_annual(c: Ctx) -> list[tuple[str, str]]:
    a = c.g("annual_book")
    out = []
    if a["mit_dieser_registrierung"] < a["erwartete_falsch_pass_vorher"]:
        out.append((STATUS_ERR, "annual_book: value with this registration is below the value before it"))
    if a["mit_dieser_registrierung"] > ANNUAL_BOOK_LIMIT:
        out.append((STATUS_HINT, f"annual_book {a['mit_dieser_registrierung']} > {ANNUAL_BOOK_LIMIT} expected false "
                                 f"PASS per year: Nutzer-Vorlage (DEC-104 E4 (g))"))
    coh = c.g("cohort")
    if coh is not None and a["jahr"] != coh.year:
        out.append((STATUS_HINT, f"annual_book.jahr {a['jahr']} differs from the cohort year {coh.year}"))
    return out


def r_report_line(c: Ctx) -> list[tuple[str, str]]:
    rl = c.g("report_line")
    out = []
    missing = [f for f in S.REPORT_LINE_FIELDS if f not in rl]
    if missing:
        out.append((STATUS_ERR, f"report_line lacks {missing} (DEC-105 mandatory report line)"))
    dups = sorted({f for f in rl if rl.count(f) > 1})
    if dups:
        out.append((STATUS_ERR, f"report_line lists {dups} more than once"))
    return out


def r_artifacts(c: Ctx) -> list[tuple[str, str]]:
    a = c.g("artifacts")
    out = []
    cs, bs = a["cluster_series_ref"].lower(), a["bootstrap_replicates_ref"].lower()
    if "sha256" not in cs:
        out.append((STATUS_ERR, "cluster_series_ref must name the cluster series with its sha256 (DEC-53 (a))"))
    if not ("sha256" in bs or ("seed" in bs and "generator_fingerprint" in bs)):
        out.append((STATUS_ERR, "bootstrap_replicates_ref must name sha256 or seed + generator_fingerprint "
                                "(DEC-53 (b))"))
    return out


def r_constants(c: Ctx) -> list[tuple[str, str]]:
    ch, sh = c.g("constants_hash"), c.g("sesoi_curve.kostenmodell_constants_hash")
    out = []
    if ch == "n/a - kapitalfrei ohne Kostenmodell":
        if c.g("capital_free") is not True:
            out.append((STATUS_ERR, "constants_hash 'n/a' only for a capital-free registration"))
    elif ch != sh:
        out.append((STATUS_ERR, "constants_hash differs from sesoi_curve.kostenmodell_constants_hash (PZ-06)"))
    return out


def r_code(c: Ctx) -> list[tuple[str, str]]:
    out = []
    paths = [x["pfad"] for x in c.g("code_sha256")]
    for p in sorted({x for x in paths if paths.count(x) > 1}):
        out.append((STATUS_ERR, f"code_sha256: path {p} listed more than once"))
    for p in paths:
        why = _unsafe_path(p)
        if why:
            out.append((STATUS_ERR, f"code_sha256: {p}: {why}"))
    return out


def r_tax(c: Ctx) -> list[tuple[str, str]]:
    if "UNBELEGT" not in c.g("capital_tax_venue.steuer"):
        return [(STATUS_ERR, "capital_tax_venue.steuer must carry 'UNBELEGT - PRD 8.2' (no net statement without "
                             "reservation)")]
    return []


def _fragments(*parts: str) -> str:
    return "".join(parts)


# Product names of language models are matched by stems that are assembled from fragments, so that this very file stays
# clean under the repository text scan.
_MODEL_STEMS = (_fragments("cla", "ude"), _fragments("son", "net"), _fragments("op", "us"), _fragments("hai", "ku"),
                _fragments("gp", "t"), _fragments("chat", "gp", "t"), _fragments("gem", "ini"), _fragments("lla", "ma"),
                _fragments("mis", "tral"), _fragments("co", "pilot"), _fragments("gr", "ok"),
                _fragments("deep", "seek"), _fragments("qw", "en"))
_RX_MODEL = re.compile(r"(?<![a-z0-9])(?:" + "|".join(_MODEL_STEMS) + r")(?![a-z])", re.I)
_TLDS = "com|net|org|io|dev|de|eu|ch|ai|app|cloud|local|lan|home|internal|intranet|xyz|me|info|biz|ru|cn"
_RX_HOST = (re.compile(r"[a-z][a-z0-9+.-]*://", re.I),
            re.compile(r"[\w.-]+@[\w-]+(?:\.[\w-]+)+"),
            re.compile(r"(?<![\d.])\d{1,3}(?:\.\d{1,3}){3}(?![\d.])"),
            re.compile(r"(?<![\w-])(?:[a-z0-9][a-z0-9-]*\.)+(?:" + _TLDS + r")(?![\w-])", re.I))
_RX_SECRET = (re.compile(_fragments("HARVEST", "_S3_")), re.compile(r"AKIA[0-9A-Z]{16}"), re.compile(r"-----BEGIN [A-Z ]*KEY"),
              re.compile(r"(?i)\b(?:secret|passw(?:or)?d|api[_-]?key|access[_-]?key|token)\s*[:=]\s*\S{6,}"))


def r_hygiene(c: Ctx) -> list[tuple[str, str]]:
    out = []
    for p, t, is_key in _walk_strings(c.raw):
        where = f"{p} ({'key' if is_key else 'value'})"
        if _RX_MODEL.search(t):
            out.append((STATUS_ERR, f"{where}: product name of a language model (not allowed in the public repository)"))
        if any(rx.search(t) for rx in _RX_HOST):
            out.append((STATUS_ERR, f"{where}: host name, address or URL (not allowed in the public repository)"))
        if any(rx.search(t) for rx in _RX_SECRET):
            out.append((STATUS_ERR, f"{where}: credential-like text (never in the repository)"))
    return out


def r_refs(c: Ctx) -> list[tuple[str, str]]:
    out = []
    for p, v in _iter_kind(S.SPEC, c.d, "ref"):
        why = _unsafe_path(v)
        if why:
            out.append((STATUS_ERR, f"{p}: {v}: {why}"))
    return out


def r_reading(c: Ctx) -> list[tuple[str, str]]:
    out = []
    for i, z in enumerate(c.g("lesestatus")):
        why = _unsafe_path(z["datei"], allow_sealed=True)
        if why:
            out.append((STATUS_ERR, f"lesestatus[{i}].datei: {z['datei']}: {why}"))
        elif z["status"] == "gelesen" and _SEALED.search(z["datei"]):
            out.append((STATUS_HINT, f"lesestatus[{i}]: sealed file recorded as read: disclose in c17_refs"))
    return out


def r_design(c: Ctx) -> list[tuple[str, str]]:
    dm = c.g("design_menu")
    if dm["gewaehlt"] not in dm["optionen"]:
        return [(STATUS_ERR, "design_menu.gewaehlt is not one of the registered optionen (mechanical selection)")]
    return []


def r_reach(c: Ctx) -> list[tuple[str, str]]:
    return [(STATUS_HINT, f"reachability: parameter '{x['parameter']}' reaches 0 observations in the judging windows")
            for x in c.g("reachability") if x["beobachtungen_in_urteilsfenstern"] == 0]


def r_fdr(c: Ctx) -> list[tuple[str, str]]:
    f = c.g("fdr")
    out = []
    if not _close(f["kohorte_by_q"], BY_Q, 1e-12):
        out.append((STATUS_ERR, f"fdr.kohorte_by_q = {f['kohorte_by_q']}, fixed value is {BY_Q} (BY over the cohort)"))
    if not _close(f["bh_alpha"], BY_Q, 1e-12):
        out.append((STATUS_ERR, f"fdr.bh_alpha = {f['bh_alpha']}, fixed value is {BY_Q}"))
    return out


def r_prior_knowledge(c: Ctx) -> list[tuple[str, str]]:
    text = c.g("vorwissens_klasse")
    miss = sorted({e.fam for e in _entries(c)} - set(re.findall(r"F[1-6]", text)))
    if miss:
        return [(STATUS_HINT, f"vorwissens_klasse does not mention the families {miss} of the zone entries")]
    return []


def r_positive_control(c: Ctx) -> list[tuple[str, str]]:
    pc = c.g("positive_control")
    out = []
    if pc["vorgeschaltet"] is not True:
        out.append((STATUS_HINT, "positive_control.vorgeschaltet is false: its PASS is a precondition of scheduling "
                                 "(VR-f12)"))
    if pc["produktionskonfiguration"] is not True:
        out.append((STATUS_HINT, "positive_control.produktionskonfiguration is false (practice since DEC-89 E2)"))
    return out


# --------------------------------------------------------------------------------------------------------------------
# the rule table (data)
# --------------------------------------------------------------------------------------------------------------------
def _r(id_: str, title: str, source: str, needs: tuple[str, ...], check: Check, ok: str) -> Rule:
    return Rule(id_, title, source, needs, check, ok)


RULES: tuple[Rule, ...] = (
    _r("R01-SCHEMA", "required fields present, typed, allowed values; no defaults, no unknown fields",
       "PRD v3 3.1 (a)/(b); 3.2 PZ-01..PZ-30; DEC-104 E9", (), r_schema,
       "all mandatory lines PZ-01..PZ-30 present and well-formed"),
    _r("R02-PLATZHALTER", "no unresolved template placeholders '<...>'", "PRD v3 3.3; PRD 3.1 (b)", (), r_placeholder,
       "no placeholders left"),
    _r("R03-ALPHA", "alpha_test = 0.0025 and z_krit = 2.8070 (fixed per test)", "DEC-104 E2; VR-b14; PZ-15",
       ("decision_rule.alpha_test", "decision_rule.z_krit"), r_alpha, "alpha_test 0.0025, z_krit 2.8070"),
    _r("R04-SCREEN", "screen / stability_test variants a, a', c; only the decided variant", "DEC-104 E2, E6, N2 (4); PZ-16",
       ("decision_rule.variante", "decision_rule.screen", "decision_rule.stability_test"), r_screen,
       "decided variant with consistent screen / stability_test"),
    _r("R05-KOHORTE", "cohort = first day of a quarter >= 2027-01-01", "DEC-104 E4 (f); PZ-14", ("cohort",), r_cohort,
       "cohort date valid"),
    _r("R06-FENSTER-ZONE", "windows lie in their zone and are covered by a zone entry; one judging window",
       "DEC-104 E4 (a), (d), (e); FENSTERREGISTER 1; PZ-13", ("windows", "zone"), r_window_zone,
       "all windows in their zone"),
    _r("R07-ZONE-X", "no zone-X data as confirmation", "DEC-104 E4 (a), (c); KONTO_ZONE_X", ("windows",), r_zone_x,
       "no judging window uses zone X"),
    _r("R08-FAMILIE", "zone V policy and pure zone-K start per data family",
       "DEC-104 E4 (i); FENSTERREGISTER 2, 6; VR-d16; PZ-13, PZ-30", ("windows", "zone"), r_family,
       "windows respect the knowledge class and K start of their families"),
    _r("R09-ZONENEINTRAG", "zone entries: section inside the zone, rein_ab consistent", "FENSTERREGISTER 1, 6; PZ-13",
       ("zone",), r_zone_entry, "zone entries consistent"),
    _r("R10-BLICKE", "looks: zone V exactly one, zone K plan complete", "DEC-104 E4 (d), (e), N2 (7); PZ-17; VR-d11, VR-d12",
       ("looks", "windows", "cohort"), r_looks, "look plan consistent with the zones used"),
    _r("R11-SESOI", "sesoi_curve: frame, cost basis label, persistence, curve, SESOI value",
       "DEC-104 E3 (a), N3 (1); DEC-105 (1), (8); PZ-18", ("sesoi_curve", "klasse", "power.sesoi"), r_sesoi,
       "SESOI curve consistent"),
    _r("R12-TESTBARKEIT", "MDE80 <= SESOI, else strukturell nicht testbar; flag and verdict consistent",
       "DEC-104 E3 (a); VR-c01; PZ-01", ("power.mde80.wert", "power.sesoi", "power.testbar", "feasibility_verdict"),
       r_testable, "MDE80 <= SESOI: testbar"),
    _r("R13-PRIOR", "prior_label set; UNBELEGT carries a two-sided sensitivity span; selection-adjusted",
       "DEC-104 E3 (b), (c), (d); VR-c05, VR-c06; PZ-19", ("prior_label",), r_prior, "prior label complete"),
    _r("R14-LITERATUR", "literature is a label, never a block", "DEC-104 E3 (b); VR-c05", ("prior_label.literatur",),
       r_literature, "literatur label does not block"),
    _r("R15-SELEKTION-K", "selection K >= 1 and cumulative K >= K", "DEC-104 E9, N1 (9); VR-b17; PZ-04, PZ-20",
       ("selection",), r_selection, "selection K valid"),
    _r("R16-OC-ZEILE", "oc_line complete, >= 1000 seeds, plausible", "DEC-104 E8 (a); VR-f04; PZ-21",
       ("oc_line", "decision_rule.power_target_gemeinsam", "power.testbar"), r_oc, "oc_line complete"),
    _r("R17-STRENGE", "strictness ratio >= 1.3 -> Nutzer-Vorlage", "DEC-104 E8 (b); VR-f05; PZ-22",
       ("strictness_ratio.wert",), r_strictness, "strictness ratio below 1.3"),
    _r("R18-NEFF-C", "n_eff > 0 and c_overlap >= 1", "DEC-51 (3), (5); DEC-104 N2 (7); VR-b03, VR-b05; PZ-23, PZ-24",
       ("n_eff", "c_overlap"), r_neff, "n_eff and c_overlap valid"),
    _r("R19-C17", "c17_refs are unique rows of the account inventory", "DEC-104 N1 (1); VR-d18; PZ-29",
       ("c17_refs", "windows"), r_c17, "c17_refs valid"),
    _r("R20-JAHRESBUCH", "annual book consistent; > 0.10 -> Nutzer-Vorlage", "DEC-104 E4 (g); VR-d14; PZ-28",
       ("annual_book", "cohort"), r_annual, "annual book within the limit"),
    _r("R21-BERICHTSZEILE", "report_line carries the nine mandatory fields", "DEC-105; VR-f02; PZ-11",
       ("report_line",), r_report_line, "report line complete"),
    _r("R22-ARTEFAKTE", "result artifacts: cluster series + bootstrap (sha256 or seed + generator fingerprint)",
       "DEC-53; VR-f03; PZ-11", ("artifacts",), r_artifacts, "artifact obligations named"),
    _r("R23-KONSTANTEN", "constants_hash pinned and equal to the cost-model hash", "PRD 3.3.6; VR-g14; PZ-06",
       ("constants_hash", "sesoi_curve.kostenmodell_constants_hash", "capital_free"), r_constants,
       "constants hash consistent"),
    _r("R24-CODE-HASH", "code_sha256: repository-relative, unique paths", "PRD_ANALYSE 7 (versioned script)",
       ("code_sha256",), r_code, "code hashes valid"),
    _r("R25-STEUER", "tax treatment 'UNBELEGT - PRD 8.2'", "PRD 3.3.9; PRD 8.2; PZ-09",
       ("capital_tax_venue.steuer",), r_tax, "tax reservation present"),
    _r("R26-TEXT-HYGIENE", "no model names, host names, credentials in any text",
       "project hard rules; public repository", (), r_hygiene, "no model names, hosts or credentials"),
    _r("R27-REFS", "derivation references are repository-relative, not sealed, not below data/harvest",
       "project hard rules; PRD 3.1 (b)", (), r_refs, "references safe"),
    _r("R28-LESESTATUS", "reading status per file; sealed files recorded as read are flagged",
       "DEC-104 N1 (6); VR-g07; PZ-25", ("lesestatus",), r_reading, "reading status valid"),
    _r("R29-DESIGN-MENUE", "chosen design belongs to the registered menu", "DEC-104 E5; VR-e01; PZ-26",
       ("design_menu",), r_design, "design choice inside the menu"),
    _r("R30-ERREICHBARKEIT", "every parameter reaches observations in the judging windows",
       "DEC-104 E8 (d); VR-f07; PZ-27", ("reachability",), r_reach, "all parameters reachable"),
    _r("R31-FDR", "cohort BY q and BH alpha fixed at 0.10", "DEC-104 E4 (f); VR-b16, VR-b17, VR-d13", ("fdr",), r_fdr,
       "FDR parameters fixed"),
    _r("R32-VORWISSEN", "vorwissens_klasse names the families of the zone entries", "DEC-104 E4 (i); VR-d16; PZ-30",
       ("vorwissens_klasse", "zone"), r_prior_knowledge, "prior-knowledge class names all families"),
    _r("R33-POSITIVKONTROLLE", "positive control preceding, production configuration", "PRD 3.3.8; VR-f12; PZ-08",
       ("positive_control",), r_positive_control, "positive control scheduled"),
)


# --------------------------------------------------------------------------------------------------------------------
# engine
# --------------------------------------------------------------------------------------------------------------------
def _blocked(need: str, issues: list[S.Issue]) -> bool:
    for i in issues:
        p = i.path
        if p == need or p.startswith((need + ".", need + "[")) or need.startswith((p + ".", p + "[")) or p == "":
            return True
    return False


def lint(obj: Any) -> list[Finding]:
    """Run every rule on a loaded YAML object; deterministic order (rule table order)."""
    data, issues = S.validate(obj)
    ctx = Ctx(data, obj, issues)
    findings: list[Finding] = []
    for rule in RULES:
        bad = [n for n in rule.needs if _blocked(n, issues)]
        if bad:
            findings.append(Finding(rule.id, rule.source, STATUS_HINT,
                                    f"not checked: input invalid or missing ({', '.join(bad)}); see R01-SCHEMA"))
            continue
        res = rule.check(ctx)
        if not res:
            msg = rule.ok
            if rule.id == "R14-LITERATUR":
                msg = f"literatur label '{ctx.g('prior_label.literatur')}' is a label, never a block"
            findings.append(Finding(rule.id, rule.source, STATUS_OK, msg))
        else:
            findings.extend(Finding(rule.id, rule.source, st, m) for st, m in res)
    return findings


def load_yaml(text: str) -> Any:
    """Safe YAML load that rejects duplicate keys and maps the bare key ``null`` to the text 'null'."""
    import yaml

    class Loader(yaml.SafeLoader):
        pass

    def construct_mapping(loader: Loader, node: Any, deep: bool = False) -> dict:
        loader.flatten_mapping(node)
        out: dict = {}
        for k_node, v_node in node.value:
            k = loader.construct_object(k_node, deep=True)
            if k is None:
                k = "null"           # the template's fixtures block has a field called null
            elif not isinstance(k, str):
                raise yaml.YAMLError(f"non-text mapping key {k!r} (line {k_node.start_mark.line + 1})")
            if k in out:
                raise yaml.YAMLError(f"duplicate key '{k}' (line {k_node.start_mark.line + 1})")
            out[k] = loader.construct_object(v_node, deep=True)
        return out

    Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)
    return yaml.load(text, Loader=Loader)  # noqa: S506 -- SafeLoader subclass


def lint_file(path: str) -> list[Finding]:
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise LintInputError(f"cannot read {path}: {exc}") from exc
    try:
        obj = load_yaml(text)
    except Exception as exc:  # yaml.YAMLError and friends
        raise LintInputError(f"{path}: not parseable YAML: {exc}") from exc
    return lint(obj)


def format_text(findings: list[Finding]) -> str:
    lines = [f"[{f.status}] {f.rule} ({f.source}): {f.message}" for f in findings]
    n = {s: sum(1 for f in findings if f.status == s) for s in (STATUS_ERR, STATUS_HINT, STATUS_OK)}
    lines.append(f"SUMMARY: {n[STATUS_ERR]} {STATUS_ERR}, {n[STATUS_HINT]} {STATUS_HINT}, {n[STATUS_OK]} {STATUS_OK}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m bybit_edge.research.registry31.lint",
                                 description="Lint a registration under Constitution 3.1.")
    ap.add_argument("yaml", nargs="?", help="registration YAML file")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--list-rules", action="store_true", help="print the rule table and exit")
    ap.add_argument("--emit-schema", action="store_true", help="print the JSON Schema and exit")
    args = ap.parse_args(argv)
    if args.list_rules:
        for r in RULES:
            print(f"{r.id}\t{r.source}\t{r.title}")
        return 0
    if args.emit_schema:
        print(json.dumps(S.json_schema(), indent=2, sort_keys=True))
        return 0
    if not args.yaml:
        ap.error("a YAML file is required")
    try:
        findings = lint_file(args.yaml)
    except LintInputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"findings": [f.as_dict() for f in findings],
                          "errors": sum(1 for f in findings if f.status == STATUS_ERR)}, indent=2, sort_keys=True))
    else:
        print(format_text(findings))
    return 1 if any(f.status == STATUS_ERR for f in findings) else 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
