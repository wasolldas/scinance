"""Tests of the registration schema and linter for Constitution 3.1 (``registry31``, F1).

No network, no market data, no sealed file: the valid example below is derived from the YAML template 3.1 (PRD v3
draft section 3.3) with invented, self-consistent numbers.
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import re
from pathlib import Path

import pytest
import yaml

import bybit_edge.research as _research

# Stage-run helper: when the package is merged into the repository this is a no-op; before the merge it lets the
# staged package be found next to the installed ``bybit_edge.research`` (a regular package shadows namespace portions).
_RESEARCH_DIR = Path(__file__).resolve().parents[2] / "src" / "bybit_edge" / "research"
if _RESEARCH_DIR.is_dir() and str(_RESEARCH_DIR) not in [str(Path(p).resolve()) for p in _research.__path__]:
    _research.__path__.append(str(_RESEARCH_DIR))

from bybit_edge.research.registry31 import lint as L  # noqa: E402
from bybit_edge.research.registry31 import schema as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = ROOT / "src" / "bybit_edge" / "research" / "registry31"
TEMPLATE = ROOT / "scinance3-impl" / "state" / "registered" / "TEMPLATE_3_1.yaml"
D = dt.date


def _h(c: str) -> str:
    return c * 64


# --------------------------------------------------------------------------------------------------------------------
# the valid example
# --------------------------------------------------------------------------------------------------------------------
VALID: dict = {
    "id": "H-34",
    "klasse": "W",
    "capital_free": True,
    "hypothese": "Der Dezil-Long/Short der Rueckkehr-Variante hat einen Rang-IC unter null.",
    "ertragsquelle": "Prognose + Liquiditaetszahler",
    "metric": "wochen_ic_dezil_ls",
    "richtung": "negativ",
    "cohort": D(2027, 1, 1),
    "zone": [
        {"abschnitt": "2021-01-01..2024-06-30", "zone": "X", "datenfamilie": "F2", "rein_ab": D(2021, 1, 1)},
        {"abschnitt": "2024-07-01..2025-06-30", "zone": "V", "datenfamilie": "F2", "rein_ab": D(2024, 7, 1)},
        {"abschnitt": "2026-07-01..2027-12-31", "zone": "K", "datenfamilie": "F2", "rein_ab": D(2026, 7, 1)},
    ],
    "vorwissens_klasse": "F2: Panel-Querschnitte auf W1/W2 blind, soweit nicht per C.17 verbraucht",
    "lesestatus": [
        {"datei": "scinance3-impl/state/FENSTERREGISTER.md", "status": "gelesen"},
        {"datei": "scinance3-impl/state/runs/wp7_ic_rohserie.csv", "status": "berechnet_versiegelt_ungelesen"},
    ],
    "c17_refs": ["O-010", "O-014", "O-027"],
    "windows": [
        {"id": "P0", "von": D(2022, 4, 18), "bis": D(2024, 6, 30), "zone": "X", "rolle": "pilot_nicht_urteilstragend"},
        {"id": "W1", "von": D(2024, 7, 1), "bis": D(2025, 6, 30), "zone": "V", "rolle": "urteilstragend"},
        {"id": "K1", "von": D(2026, 7, 1), "bis": D(2027, 12, 31), "zone": "K", "rolle": "urteilstragend"},
    ],
    "decision_rule": {
        "alpha_test": 0.0025,
        "z_krit": 2.8070,
        "variante": "a",
        "screen": {"fenster": "juengste_12_monate_bzw_4_quartale", "alpha": 0.05, "z_krit": 1.6449},
        "stability_test": None,
        "power_target_gemeinsam": 0.80,
        "mde_faktor": 2.4865,
    },
    "looks": {
        "zone_v": {"anzahl": 1},
        "zone_k": {"anzahl": 4, "plan": "obrien_fleming", "spending": "obrien_fleming_alpha_0.0025",
                   "zeitpunkte": [D(2027, 4, 1), D(2027, 7, 1), D(2027, 10, 1), D(2028, 1, 1)],
                   "screen_an_jedem_stopp": True, "futility": "Z < 0 an Blicken 1-3", "grenzen": "t_artig"},
    },
    "sesoi_curve": {
        "kostenmodell_constants_hash": _h("a"),
        "rahmen": "dezil_ls",
        "kostenbasis": "taker_vip0",
        "gabelung_etikett": "Gabelung Richtung Testbarkeit gegen Maker",
        "persistenz_phi": 0.5,
        "persistenz_herkunft": "gemessen",
        "persistenz_ref": "scinance3-impl/state/KONTO_ZONE_X.md#eintrag_1",
        "horizont_tage": 1,
        "punkte": [{"horizont_tage": 1, "phi": 0.0, "sesoi": 0.0085},
                   {"horizont_tage": 1, "phi": 0.5, "sesoi": 0.0056},
                   {"horizont_tage": 1, "phi": 0.8, "sesoi": 0.0035}],
        "ref": "tests/unit/test_sesoi.py#test_kurve_dezil",
    },
    "prior_label": {
        "literatur": "UNBELEGT",
        "prior_verteilung_ref": "KONTO_ZONE_X Zeile 1",
        "selektionsbereinigt": True,
        "sensitivitaetsspanne": {"groesse": "prior_ic", "nominal": 0.02, "untere": 0.01, "obere": 0.03},
    },
    "threshold": {"regel": "Statistik in Richtung >= z_krit * SE", "ref": "tests/unit/test_gate.py#test_schwelle"},
    "structural_null": {"komponenten": ["persistenz_null", "faktor_null"], "skalierung": "k = max(1, Ist/Null)",
                        "ref": "tests/unit/test_gate.py#test_struktur_null"},
    "nuisance": {"quellen": ["vorperiode_nur_streuung", "null_simulation"], "bindend": "juengstes_vorfenster",
                 "stress_zeile": "Stress 2021/22 nur als Sensitivitaets-Zeile"},
    "power": {
        "se_regel": "max(SD/sqrt(W), SE_stat) mit stationaerem Bootstrap",
        "sd_teststatistik": {"wert": 0.09, "ref": "scinance3-impl/state/herleitung_x/nuisance.json"},
        "c": "max(1, c_hat)",
        "blocklaenge": "4 Wochen aus gemessener Autokorrelation",
        "mde80": {"wert": 0.0040, "ref": "tests/unit/test_power.py#test_mde80"},
        "sesoi": 0.0056,
        "testbar": True,
    },
    "cluster_unit": "kalenderwoche",
    "n_eff": 98.5,
    "c_overlap": 1.0,
    "selection": {"K": 4, "K_kumuliert_familie": 8, "z_max": 2.1, "ceiling_ref": "tests/unit/test_decke.py#test_k4"},
    "design_menu": {"optionen": ["fenster_6", "fenster_9", "fenster_12"],
                    "auswahlregel": "kleinste MDE80 aus Vorperioden-Nuisance und SESOI", "gewaehlt": "fenster_12"},
    "reachability": [{"parameter": "min_symbole", "beobachtungen_in_urteilsfenstern": 104}],
    "oc_line": {"p_pass_0": 0.0019, "p_pass_sesoi": 0.81, "p_pass_prior_median": 0.55, "seeds": 1000,
                "ref": "tests/unit/test_oc.py#test_oc_t0"},
    "strictness_ratio": {"wert": 1.12, "zerlegung": ["Stress +0.04", "skalierte Null +0.08"],
                         "gabelungsregister_ref": "scinance3-impl/state/herleitung_x/gabelungen.md"},
    "annual_book": {"jahr": 2027, "erwartete_falsch_pass_vorher": 0.005, "mit_dieser_registrierung": 0.0075},
    "economic_minimum": {"wert": 0.0056, "ref": "scinance3-impl/state/herleitung_x/sesoi.md", "label": "ueber_wand"},
    "decision_relevance": {"on_pass": "naechster Messschritt", "on_drop": "Familie geschlossen",
                           "on_gl012": "kein Verdikt"},
    "capital_tax_venue": {"kapitalbasis": "Kapital-Multiplikator UNGEMESSEN, Sensitivitaet registriert",
                          "steuer": "UNBELEGT - PRD 8.2", "venue_event": "keines bekannt",
                          "zahler_post_2024": "Liquiditaetszahler, Bestand ungemessen"},
    "stress_episode": {"liste_ref": "STRESS_REL sha256:" + _h("d"), "rolle": "abdeckungsnachweis", "tage_in_fenstern": 12},
    "irreversibility_probe": {"ergebnis": "nachladbar", "ref": "scinance3-impl/state/herleitung_x/probe.md"},
    "positive_control": {"vorgeschaltet": True, "produktionskonfiguration": True, "welt": "kalibrierte Null-Welt",
                         "kriterium": "SD der Kontrollwelt <= 1,10 x SD der Power-Zeile",
                         "ref": "tests/unit/test_posctl.py"},
    "fixtures": {"positive": "injizierter IC an SESOI", "null": "permutierte Renditen",
                 "adversarial": "Faktor mit mechanischer Markt-Beta-Korrelation"},
    "test_pflichten": {t: f"tests/unit/test_x.py#test_{t.lower()}" for t in ("T0", "T1", "T2", "T3", "T4", "T5", "T6", "T7")},
    "artifacts": {"cluster_series_ref": "scinance3-impl/state/runs/x/cluster_series.csv + sha256 im Lauf",
                  "bootstrap_replicates_ref": "seed 53 + generator_fingerprint im Lauf"},
    "report_line": list(S.REPORT_LINE_FIELDS),
    "fdr": {"family": "F-XSEC", "bh_alpha": 0.10, "p": "Max-p ueber Fenster", "over_family": "F-WEEK",
            "kohorte_by_q": 0.10},
    "constants_hash": _h("a"),
    "code_sha256": [{"pfad": "src/bybit_edge/research/registry31/lint.py", "sha256": _h("c")}],
    "data_fingerprints": ["panel:" + _h("e"), "register:" + _h("f")],
    "feasibility_verdict": "testbar",
    "etiketten": ["C.17", "Gabelung Taker"],
}


def valid() -> dict:
    return copy.deepcopy(VALID)


# --------------------------------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------------------------------
def _tokens(path: str) -> list:
    out: list = []
    for part in path.split("."):
        m = re.match(r"^([^\[]+)((?:\[\d+\])*)$", part)
        assert m, path
        out.append(m.group(1))
        out.extend(int(i) for i in re.findall(r"\[(\d+)\]", m.group(2)))
    return out


def setp(obj: dict, path: str, value) -> dict:
    cur = obj
    toks = _tokens(path)
    for t in toks[:-1]:
        cur = cur[t]
    cur[toks[-1]] = value
    return obj


def delp(obj: dict, path: str) -> dict:
    cur = obj
    toks = _tokens(path)
    for t in toks[:-1]:
        cur = cur[t]
    del cur[toks[-1]]
    return obj


def statuses(findings, rule: str) -> set[str]:
    return {f.status for f in findings if f.rule == rule}


def errors(findings) -> list:
    return [f for f in findings if f.status == L.STATUS_ERR]


def run(mut=None):
    obj = valid()
    if mut:
        mut(obj)
    return L.lint(obj)


# --------------------------------------------------------------------------------------------------------------------
# valid example
# --------------------------------------------------------------------------------------------------------------------
def test_valid_example_is_green():
    f = L.lint(valid())
    assert errors(f) == [], [x.message for x in errors(f)]
    assert not [x for x in f if x.status == L.STATUS_HINT], [x.message for x in f if x.status == L.STATUS_HINT]
    assert {x.rule for x in f} == {r.id for r in L.RULES}
    assert all(x.status == L.STATUS_OK for x in f)


def test_valid_example_schema_has_no_issues_and_adds_nothing():
    data, issues = S.validate(valid())
    assert issues == []
    assert set(data) == set(VALID)                     # nothing added, nothing dropped (no defaults)


def test_valid_example_via_yaml_file_and_cli(tmp_path, capsys):
    p = tmp_path / "reg.yaml"
    p.write_text(yaml.safe_dump(valid(), sort_keys=False), encoding="utf-8")
    assert L.main([str(p)]) == 0
    out = capsys.readouterr().out
    assert "SUMMARY: 0 FEHLER, 0 HINWEIS" in out
    assert L.lint_file(str(p)) == L.lint(valid())
    assert S.load_registration(str(p))["id"] == "H-34"


def test_unquoted_null_key_in_fixtures_is_read_as_text(tmp_path):
    txt = yaml.safe_dump(valid(), sort_keys=False).replace("'null':", "null:")
    assert "\n  null:" in txt
    p = tmp_path / "reg.yaml"
    p.write_text(txt, encoding="utf-8")
    assert errors(L.lint_file(str(p))) == []


# --------------------------------------------------------------------------------------------------------------------
# the template is a template
# --------------------------------------------------------------------------------------------------------------------
def test_template_is_not_a_registration():
    head = TEMPLATE.read_text(encoding="utf-8").splitlines()[0]
    assert head.startswith("# TEMPLATE, nicht registriert")
    f = L.lint_file(str(TEMPLATE))
    assert statuses(f, "R02-PLATZHALTER") == {L.STATUS_ERR}
    assert statuses(f, "R01-SCHEMA") == {L.STATUS_ERR}
    assert errors(f)
    assert f == L.lint_file(str(TEMPLATE))


def test_template_has_every_top_level_field_and_only_those():
    obj = L.load_yaml(TEMPLATE.read_text(encoding="utf-8"))
    assert set(obj) == {f.name for f in S.SPEC.fields}


# --------------------------------------------------------------------------------------------------------------------
# one negative example per rule
# --------------------------------------------------------------------------------------------------------------------
_MODEL = "cla" + "ude"
_MODEL_B = "gp" + "t-4"
_HOST = "daten" + "." + "example" + ".com"
_SCHEME = "htt" + "ps:" + "//"
_IP = "10." + "0.0." + "12"


def _w(path, value):
    return lambda o: setp(o, path, value)


def _d(path):
    return lambda o: delp(o, path)


def _fam_k(o):
    o["zone"][2]["datenfamilie"] = "F1"          # F1 pure zone K only from 2026-10-01


def _no_k_looks(o):
    delp(o, "looks.zone_k")


def _k_count(o):
    o["looks"]["zone_k"]["anzahl"] = 3


def _mde_above(o):
    o["power"]["mde80"]["wert"] = 0.0100


NEG: list[tuple[str, str, object]] = [
    ("R01-SCHEMA", L.STATUS_ERR, _d("oc_line")),
    ("R01-SCHEMA", L.STATUS_ERR, lambda o: o.update({"unbekannt": 1})),
    ("R02-PLATZHALTER", L.STATUS_ERR, _w("hypothese", "<ein Satz, falsifizierbar>")),
    ("R03-ALPHA", L.STATUS_ERR, _w("decision_rule.alpha_test", 0.005)),
    ("R03-ALPHA", L.STATUS_ERR, _w("decision_rule.z_krit", 2.5)),
    ("R04-SCREEN", L.STATUS_ERR, lambda o: (setp(o, "decision_rule.variante", "a'"),
                                            setp(o, "decision_rule.screen.alpha", 0.20),
                                            setp(o, "decision_rule.screen.z_krit", 0.8416))),
    ("R04-SCREEN", L.STATUS_ERR, _w("decision_rule.screen.alpha", 0.20)),
    ("R04-SCREEN", L.STATUS_ERR, lambda o: (setp(o, "decision_rule.variante", "c"),
                                            setp(o, "decision_rule.screen", None),
                                            setp(o, "decision_rule.stability_test",
                                                 {"statistik": "juengster Teil faellt nicht ab", "alpha": 0.05,
                                                  "power": 0.95, "ref": "tests/unit/test_stab.py#t"}))),
    ("R05-KOHORTE", L.STATUS_ERR, _w("cohort", D(2026, 10, 1))),
    ("R05-KOHORTE", L.STATUS_ERR, _w("cohort", D(2027, 2, 1))),
    ("R05-KOHORTE", L.STATUS_ERR, _w("cohort", D(2027, 1, 2))),
    ("R06-FENSTER-ZONE", L.STATUS_ERR, _w("windows[1].bis", D(2026, 7, 1))),
    ("R06-FENSTER-ZONE", L.STATUS_ERR, _w("windows[2].von", D(2026, 6, 30))),
    ("R06-FENSTER-ZONE", L.STATUS_ERR,
     lambda o: o["windows"].append({"id": "W1", "von": D(2024, 7, 1), "bis": D(2024, 8, 1), "zone": "V",
                                    "rolle": "aera_profil"})),
    ("R06-FENSTER-ZONE", L.STATUS_ERR, lambda o: [w.update({"rolle": "aera_profil"}) for w in o["windows"]]),
    ("R07-ZONE-X", L.STATUS_ERR, _w("windows[0].rolle", "urteilstragend")),
    ("R08-FAMILIE", L.STATUS_ERR, _fam_k),
    ("R08-FAMILIE", L.STATUS_ERR, _w("zone[1].datenfamilie", "F4")),
    ("R08-FAMILIE", L.STATUS_ERR, _w("zone[1].datenfamilie", "F1")),
    ("R08-FAMILIE", L.STATUS_ERR, _w("zone[1].datenfamilie", "F3")),
    ("R09-ZONENEINTRAG", L.STATUS_ERR, _w("zone[1].rein_ab", D(2024, 6, 1))),
    ("R09-ZONENEINTRAG", L.STATUS_ERR, _w("zone[2].rein_ab", D(2026, 6, 1))),
    ("R10-BLICKE", L.STATUS_ERR, _no_k_looks),
    ("R10-BLICKE", L.STATUS_ERR, _d("looks.zone_v")),
    ("R10-BLICKE", L.STATUS_ERR, _k_count),
    ("R10-BLICKE", L.STATUS_ERR, _w("looks.zone_k.screen_an_jedem_stopp", False)),
    ("R11-SESOI", L.STATUS_ERR, _w("sesoi_curve.rahmen", "einzelposition")),
    ("R11-SESOI", L.STATUS_ERR, _w("sesoi_curve.gabelung_etikett", "ohne Etikett")),
    ("R11-SESOI", L.STATUS_ERR, _w("sesoi_curve.punkte", [{"horizont_tage": 1, "phi": 0.5, "sesoi": 0.0056}])),
    ("R11-SESOI", L.STATUS_ERR, _w("power.sesoi", 0.0060)),
    ("R11-SESOI", L.STATUS_ERR, _w("sesoi_curve.persistenz_ref", None)),
    ("R12-TESTBARKEIT", L.STATUS_ERR, _w("power.testbar", False)),
    ("R12-TESTBARKEIT", L.STATUS_HINT, lambda o: (_mde_above(o), setp(o, "power.testbar", False),
                                                  setp(o, "feasibility_verdict", "GL-012 strukturell nicht testbar"))),
    ("R13-PRIOR", L.STATUS_ERR, _d("prior_label.sensitivitaetsspanne")),
    ("R13-PRIOR", L.STATUS_ERR, _w("prior_label.sensitivitaetsspanne.untere", 0.025)),
    ("R13-PRIOR", L.STATUS_ERR, _w("prior_label.selektionsbereinigt", False)),
    ("R15-SELEKTION-K", L.STATUS_ERR, _w("selection.K", 0)),
    ("R15-SELEKTION-K", L.STATUS_ERR, _w("selection.K_kumuliert_familie", 2)),
    ("R16-OC-ZEILE", L.STATUS_ERR, _w("oc_line.seeds", 999)),
    ("R16-OC-ZEILE", L.STATUS_HINT, _w("oc_line.p_pass_0", 0.01)),
    ("R16-OC-ZEILE", L.STATUS_HINT, _w("oc_line.p_pass_sesoi", 0.60)),
    ("R17-STRENGE", L.STATUS_HINT, _w("strictness_ratio.wert", 1.3)),
    ("R18-NEFF-C", L.STATUS_ERR, _w("c_overlap", 0.9)),
    ("R19-C17", L.STATUS_ERR, _w("c17_refs", ["O-010", "O-010"])),
    ("R19-C17", L.STATUS_HINT, _w("c17_refs", [])),
    ("R20-JAHRESBUCH", L.STATUS_ERR, _w("annual_book.mit_dieser_registrierung", 0.001)),
    ("R20-JAHRESBUCH", L.STATUS_HINT, _w("annual_book.mit_dieser_registrierung", 0.2)),
    ("R21-BERICHTSZEILE", L.STATUS_ERR, _w("report_line", [x for x in S.REPORT_LINE_FIELDS if x != "se"])),
    ("R22-ARTEFAKTE", L.STATUS_ERR, _w("artifacts.cluster_series_ref", "serie.csv")),
    ("R22-ARTEFAKTE", L.STATUS_ERR, _w("artifacts.bootstrap_replicates_ref", "replikate.csv")),
    ("R23-KONSTANTEN", L.STATUS_ERR, _w("constants_hash", _h("9"))),
    ("R23-KONSTANTEN", L.STATUS_ERR, lambda o: (setp(o, "constants_hash", "n/a - kapitalfrei ohne Kostenmodell"),
                                                setp(o, "capital_free", False))),
    ("R24-CODE-HASH", L.STATUS_ERR, _w("code_sha256[0].pfad", "/abs/skript.py")),
    ("R24-CODE-HASH", L.STATUS_ERR, lambda o: o["code_sha256"].append(dict(o["code_sha256"][0]))),
    ("R25-STEUER", L.STATUS_ERR, _w("capital_tax_venue.steuer", "netto nach Steuer 3 %")),
    ("R26-TEXT-HYGIENE", L.STATUS_ERR, _w("hypothese", f"Wie bei {_MODEL} gezeigt")),
    ("R26-TEXT-HYGIENE", L.STATUS_ERR, _w("etiketten", [f"Entwurf von {_MODEL_B}"])),
    ("R26-TEXT-HYGIENE", L.STATUS_ERR, _w("etiketten", [f"Quelle {_HOST}"])),
    ("R26-TEXT-HYGIENE", L.STATUS_ERR, _w("etiketten", [_SCHEME + _HOST + "/pfad"])),
    ("R26-TEXT-HYGIENE", L.STATUS_ERR, _w("etiketten", ["Server " + _IP])),
    ("R26-TEXT-HYGIENE", L.STATUS_ERR, _w("etiketten", ["HARVEST" + "_S3_" + "KEY"])),
    ("R26-TEXT-HYGIENE", L.STATUS_ERR, _w("etiketten", ["pass" + "word: hunter22x"])),
    ("R27-REFS", L.STATUS_ERR, _w("threshold.ref", "../aussen/gate.py#t")),
    ("R27-REFS", L.STATUS_ERR, _w("threshold.ref", "scinance3-impl/state/runs/weekly_ic_series.csv#t")),
    ("R27-REFS", L.STATUS_ERR, _w("power.sd_teststatistik.ref", "data/harvest/x.parquet")),
    ("R28-LESESTATUS", L.STATUS_HINT, _w("lesestatus[1]", {"datei": "scinance3-impl/state/runs/wp13a_x_L_window_sealed.json",
                                                         "status": "gelesen"})),
    ("R28-LESESTATUS", L.STATUS_ERR, _w("lesestatus[0].datei", "/abs/datei.md")),
    ("R29-DESIGN-MENUE", L.STATUS_ERR, _w("design_menu.gewaehlt", "fenster_24")),
    ("R30-ERREICHBARKEIT", L.STATUS_HINT, _w("reachability[0].beobachtungen_in_urteilsfenstern", 0)),
    ("R31-FDR", L.STATUS_ERR, _w("fdr.kohorte_by_q", 0.05)),
    ("R32-VORWISSEN", L.STATUS_HINT, _w("vorwissens_klasse", "keine Angabe")),
    ("R33-POSITIVKONTROLLE", L.STATUS_HINT, _w("positive_control.vorgeschaltet", False)),
]


def test_every_rule_has_a_negative_example():
    covered = {r for r, _, _ in NEG}
    assert covered == {r.id for r in L.RULES} - {"R14-LITERATUR"}


@pytest.mark.parametrize("rule,status,mut", NEG, ids=[f"{r}-{i}" for i, (r, _, _) in enumerate(NEG)])
def test_negative_example(rule, status, mut):
    f = run(mut)
    assert status in statuses(f, rule), [(x.rule, x.status, x.message) for x in f if x.status != L.STATUS_OK]
    if status == L.STATUS_ERR:
        assert errors(f)


def test_hint_only_changes_keep_return_code_zero(tmp_path):
    for mut in (_w("strictness_ratio.wert", 1.3), _w("annual_book.mit_dieser_registrierung", 0.2),
                _w("reachability[0].beobachtungen_in_urteilsfenstern", 0)):
        f = run(mut)
        assert errors(f) == []
        assert any(x.status == L.STATUS_HINT for x in f)
    obj = valid()
    _mde_above(obj)
    obj["power"]["testbar"] = False
    obj["feasibility_verdict"] = "GL-012 strukturell nicht testbar"
    f = L.lint(obj)
    assert errors(f) == []
    assert any("strukturell nicht testbar" in x.message and x.status == L.STATUS_HINT for x in f)
    p = tmp_path / "hint.yaml"
    p.write_text(yaml.safe_dump(obj, sort_keys=False), encoding="utf-8")
    assert L.main([str(p)]) == 0


def test_strictness_hint_names_the_user_submission():
    f = run(_w("strictness_ratio.wert", 1.355))
    assert any("Nutzer-Vorlage" in x.message for x in f if x.rule == "R17-STRENGE")
    assert not any(x.status == L.STATUS_HINT for x in run(_w("strictness_ratio.wert", 1.29)) if x.rule == "R17-STRENGE")


# --------------------------------------------------------------------------------------------------------------------
# zones and families (FENSTERREGISTER section 6)
# --------------------------------------------------------------------------------------------------------------------
def _k_only(fam: str, k_start: D, win_start: D):
    def mut(o):
        o["zone"] = [{"abschnitt": f"{win_start.isoformat()}..2027-12-31", "zone": "K", "datenfamilie": fam,
                      "rein_ab": k_start}]
        o["windows"] = [{"id": "K1", "von": win_start, "bis": D(2027, 12, 31), "zone": "K", "rolle": "urteilstragend"}]
        delp(o, "looks.zone_v")
        o["vorwissens_klasse"] = f"{fam}: Regel"
        o["c17_refs"] = ["O-001"]
    return mut


@pytest.mark.parametrize("fam,k0", [(c, f.zone_k_start) for c, f in S.FAMILIES.items()])
def test_k_start_per_family(fam, k0):
    assert S.ZONE_K_START[fam] == k0
    assert errors(run(_k_only(fam, k0, k0))) == []
    day_before = k0 - dt.timedelta(days=1)
    f = run(_k_only(fam, k0, day_before))
    assert statuses(f, "R08-FAMILIE") == {L.STATUS_ERR} or statuses(f, "R09-ZONENEINTRAG") == {L.STATUS_ERR}
    assert errors(f)


def test_k_start_table_matches_register_section_6():
    assert {c: f.isoformat() for c, f in S.ZONE_K_START.items()} == {
        "F1": "2026-10-01", "F2": "2026-07-01", "F3": "2026-09-15", "F4": "2026-07-01", "F5": "2026-07-01",
        "F6": "2026-10-01"}
    assert S.DATA_FAMILIES == ("F1", "F2", "F3", "F4", "F5", "F6")


def test_zone_v_exception_and_non_outcome_policies():
    def f1_v(o):
        o["zone"][1]["datenfamilie"] = "F1"
        o["zone"][1]["ausnahme"] = "a2_r_pre"
        o["zone"][2]["datenfamilie"] = "F1"
        o["zone"][2]["rein_ab"] = D(2026, 10, 1)
        o["zone"][2]["abschnitt"] = "2026-10-01..2027-12-31"
        o["windows"][2]["von"] = D(2026, 10, 1)
        o["vorwissens_klasse"] = "F1 und F2: Regel"
    assert errors(run(f1_v)) == []

    def f3_v(o):
        o["zone"][1]["datenfamilie"] = "F3"
        o["zone"][1]["outcome_beruehrend"] = False
        o["zone"][2]["datenfamilie"] = "F3"
        o["zone"][2]["rein_ab"] = D(2026, 9, 15)
        o["zone"][2]["abschnitt"] = "2026-09-15..2027-12-31"
        o["windows"][2]["von"] = D(2026, 9, 15)
        o["vorwissens_klasse"] = "F3 und F2: Regel"
    assert errors(run(f3_v)) == []
    f = run(lambda o: (f3_v(o), setp(o, "zone[1].outcome_beruehrend", True)))
    assert statuses(f, "R08-FAMILIE") == {L.STATUS_ERR}


def test_zone_x_as_confirmation_is_an_error_even_if_declared_as_v_or_k():
    f = run(lambda o: o["windows"][0].update({"rolle": "urteilstragend", "zone": "V"}))
    assert statuses(f, "R07-ZONE-X") == {L.STATUS_ERR}
    assert statuses(f, "R06-FENSTER-ZONE") == {L.STATUS_ERR}


def test_window_boundaries():
    # V ends 2026-06-30 for daily statistics, K starts 2026-07-01
    def v_to_end(o):
        o["zone"][1]["abschnitt"] = "2025-07-01..2026-06-30"
        o["zone"][1]["rein_ab"] = D(2025, 7, 1)
        o["windows"][1].update({"von": D(2025, 7, 1), "bis": D(2026, 6, 30)})
    assert errors(run(v_to_end)) == []
    assert statuses(run(lambda o: (v_to_end(o), o["windows"][1].update({"bis": D(2026, 7, 1)}))),
                    "R06-FENSTER-ZONE") == {L.STATUS_ERR}


# --------------------------------------------------------------------------------------------------------------------
# literature never blocks
# --------------------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("label", ["primaer", "sek", "UNBELEGT"])
def test_literature_label_never_blocks(label):
    def mut(o):
        o["prior_label"]["literatur"] = label
        if label != "UNBELEGT":
            del o["prior_label"]["sensitivitaetsspanne"]
    f = run(mut)
    assert errors(f) == []
    assert statuses(f, "R14-LITERATUR") == {L.STATUS_OK}
    assert label in [x.message for x in f if x.rule == "R14-LITERATUR"][0]


def test_unbelegt_requires_two_sided_span_only():
    f = run(_d("prior_label.sensitivitaetsspanne"))
    assert [x.rule for x in errors(f)] == ["R13-PRIOR"]


# --------------------------------------------------------------------------------------------------------------------
# no defaults for mandatory fields (loud fail)
# --------------------------------------------------------------------------------------------------------------------
def _iter_required(spec: S.Spec, data, path: str = ""):
    if spec.kind == "obj" and isinstance(data, dict):
        for f in spec.fields:
            p = f"{path}.{f.name}" if path else f.name
            if f.required:
                yield p
            if f.name in data and data[f.name] is not None:
                yield from _iter_required(f, data[f.name], p)
    elif spec.kind == "list" and isinstance(data, list) and data and spec.item is not None and spec.item.kind == "obj":
        yield from _iter_required(spec.item, data[0], f"{path}[0]")


REQUIRED = sorted(set(_iter_required(S.SPEC, VALID)))


def test_required_paths_cover_a_lot():
    assert len(REQUIRED) > 150
    assert {"cohort", "decision_rule.alpha_test", "oc_line.p_pass_0", "zone[0].datenfamilie"} <= set(REQUIRED)


@pytest.mark.parametrize("path", REQUIRED)
def test_missing_required_field_is_an_issue_never_a_default(path):
    obj = valid()
    delp(obj, path)
    data, issues = S.validate(obj)
    assert any(i.path == path and i.code == "missing" for i in issues), [str(i) for i in issues]
    top = re.split(r"[.\[]", path)[0]
    assert not (path == top and top in data)            # not filled in
    f = L.lint(obj)
    assert errors(f) and statuses(f, "R01-SCHEMA") == {L.STATUS_ERR}


@pytest.mark.parametrize("path", [p for p in REQUIRED if "[" not in p and p.count(".") <= 1][:60])
def test_null_for_a_required_field_is_an_issue(path):
    spec = S.SPEC
    for part in path.split("."):
        spec = next(f for f in spec.fields if f.name == part)
    if spec.nullable:
        pytest.skip("explicit null is allowed here")
    obj = valid()
    setp(obj, path, None)
    _, issues = S.validate(obj)
    assert any(i.path == path and i.code == "null" for i in issues)


def test_nullable_fields_must_still_be_present():
    obj = valid()
    delp(obj, "decision_rule.stability_test")
    _, issues = S.validate(obj)
    assert [str(i) for i in issues if i.path == "decision_rule.stability_test"]
    obj = valid()
    delp(obj, "sesoi_curve.persistenz_ref")
    assert any(i.path == "sesoi_curve.persistenz_ref" for i in S.validate(obj)[1])


def test_empty_mapping_reports_every_top_level_field():
    _, issues = S.validate({})
    assert {i.path for i in issues} == {f.name for f in S.SPEC.fields if f.required}


def test_no_spec_field_has_a_default_value_of_its_own():
    # the node type has no value slot at all, so a default cannot exist
    assert not any(f in ("default", "value") for f in S.Spec.__dataclass_fields__)


def test_non_mapping_and_unknown_fields_are_issues():
    assert S.validate([])[1][0].code == "type"
    _, issues = S.validate({**valid(), "oops": 1})
    assert [i.code for i in issues] == ["unknown"]
    data, issues = S.validate({**valid(), "alpha_tset": 1})
    assert [i.path for i in issues] == ["alpha_tset"]


def test_type_and_range_errors():
    cases = [("cohort", "2027-13-01"), ("cohort", 20270101), ("decision_rule.alpha_test", "0.0025"),
             ("decision_rule.alpha_test", True), ("decision_rule.alpha_test", float("nan")),
             ("selection.K", 4.5), ("selection.K", True), ("oc_line.p_pass_0", 1.5), ("oc_line.p_pass_0", -0.1),
             ("n_eff", 0), ("c_overlap", 0), ("sesoi_curve.persistenz_phi", 1.0),
             ("decision_rule.power_target_gemeinsam", 0.79), ("klasse", "Q"), ("richtung", "up"),
             ("sesoi_curve.kostenmodell_constants_hash", "ABC"), ("constants_hash", "n/a"),
             ("threshold.ref", "keine_test_id"), ("c17_refs", ["O-1"]), ("hypothese", "  "),
             ("stress_episode.liste_ref", "STRESS_REL ohne hash"), ("zone[0].abschnitt", "2021-01-01..2020-01-01")]
    for path, bad in cases:
        obj = valid()
        setp(obj, path, bad)
        _, issues = S.validate(obj)
        assert any(i.path.startswith(path) for i in issues), (path, bad)


def test_n_eff_and_c_overlap_accept_a_sourced_number():
    obj = valid()
    obj["n_eff"] = {"wert": 98.5, "ref": "scinance3-impl/state/herleitung_x/rho.json"}
    obj["c_overlap"] = {"wert": 1.2, "ref": "scinance3-impl/state/herleitung_x/c.json"}
    data, issues = S.validate(obj)
    assert issues == [] and data["n_eff"] == 98.5 and data["c_overlap"] == 1.2
    obj["c_overlap"] = {"wert": 1.2}
    assert S.validate(obj)[1]


def test_alias_c17_list():
    obj = valid()
    obj["c17_list"] = obj.pop("c17_refs")
    data, issues = S.validate(obj)
    assert issues == [] and data["c17_refs"] == VALID["c17_refs"]
    obj["c17_refs"] = ["O-001"]
    assert [i.code for i in S.validate(obj)[1]] == ["alias"]


def test_duplicate_yaml_keys_and_bad_yaml_are_rejected(tmp_path, capsys):
    p = tmp_path / "dup.yaml"
    p.write_text("id: H-34\nid: H-35\n", encoding="utf-8")
    assert L.main([str(p)]) == 2
    p.write_text("id: [unclosed\n", encoding="utf-8")
    assert L.main([str(p)]) == 2
    assert L.main([str(tmp_path / "missing.yaml")]) == 2
    err = capsys.readouterr().err
    assert err.count("ERROR") == 3
    p.write_text("- a\n- b\n", encoding="utf-8")
    assert L.main([str(p)]) == 1                       # a list is not a registration: schema error, not a crash


# --------------------------------------------------------------------------------------------------------------------
# mandatory lines PZ-01..PZ-30
# --------------------------------------------------------------------------------------------------------------------
def test_all_thirty_mandatory_lines_are_mapped_to_existing_required_fields():
    assert list(S.PZ_FIELDS) == [f"PZ-{i:02d}" for i in range(1, 31)]
    names = {p for p in REQUIRED}
    for pz, paths in S.PZ_FIELDS.items():
        assert paths
        for p in paths:
            assert p in names, (pz, p)
            assert S.get_path(VALID, p, "ABSENT") != "ABSENT" or p == "decision_rule.stability_test"


def test_missing_line_names_its_pz_in_the_message():
    for pz, paths in S.PZ_FIELDS.items():
        obj = valid()
        top = paths[0]
        delp(obj, top)
        msgs = [x.message for x in L.lint(obj) if x.rule == "R01-SCHEMA" and x.status == L.STATUS_ERR]
        assert any(f"({pz})" in m for m in msgs), (pz, msgs)


# --------------------------------------------------------------------------------------------------------------------
# determinism
# --------------------------------------------------------------------------------------------------------------------
def test_determinism_of_lint_and_output(tmp_path, capsys):
    bad = valid()
    bad["c_overlap"] = 0.5
    bad["strictness_ratio"]["wert"] = 1.5
    bad["cohort"] = D(2026, 10, 1)
    runs = [L.format_text(L.lint(copy.deepcopy(bad))) for _ in range(3)]
    assert runs[0] == runs[1] == runs[2]
    reordered = dict(reversed(list(bad.items())))
    assert L.lint(reordered) == L.lint(bad)
    p = tmp_path / "r.yaml"
    p.write_text(yaml.safe_dump(bad, sort_keys=False), encoding="utf-8")
    outs = []
    for _ in range(3):
        rc = L.main([str(p), "--json"])
        outs.append(capsys.readouterr().out)
        assert rc == 1
    assert outs[0] == outs[1] == outs[2]
    parsed = json.loads(outs[0])
    assert parsed["errors"] == sum(1 for f in parsed["findings"] if f["status"] == "FEHLER")


def test_findings_follow_the_rule_table_order():
    order = {r.id: i for i, r in enumerate(L.RULES)}
    f = run(lambda o: (setp(o, "c_overlap", 0.5), setp(o, "cohort", D(2026, 10, 1)), setp(o, "alpha_x", 1)))
    idx = [order[x.rule] for x in f]
    assert idx == sorted(idx)


def test_json_schema_is_deterministic_and_matches_the_model():
    a, b = S.json_schema(), S.json_schema()
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    assert set(a["required"]) == {f.name for f in S.SPEC.fields if f.required}
    assert set(a["properties"]) == {f.name for f in S.SPEC.fields}
    assert a["properties"]["decision_rule"]["properties"]["alpha_test"]["description"].startswith("PZ-15")


def test_json_schema_accepts_the_valid_example():
    jsonschema = pytest.importorskip("jsonschema")
    inst = json.loads(json.dumps(VALID, default=str))
    jsonschema.Draft202012Validator(S.json_schema()).validate(inst)
    bad = copy.deepcopy(inst)
    del bad["oc_line"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.Draft202012Validator(S.json_schema()).validate(bad)


# --------------------------------------------------------------------------------------------------------------------
# CLI and housekeeping
# --------------------------------------------------------------------------------------------------------------------
def test_cli_list_rules_and_emit_schema(capsys):
    assert L.main(["--list-rules"]) == 0
    out = capsys.readouterr().out
    assert all(r.id in out for r in L.RULES)
    assert L.main(["--emit-schema"]) == 0
    assert json.loads(capsys.readouterr().out)["title"].startswith("Registration under Constitution 3.1")


def test_rules_are_data_with_sources():
    ids = [r.id for r in L.RULES]
    assert len(ids) == len(set(ids))
    for r in L.RULES:
        assert r.source.strip() and r.title.strip() and r.ok.strip()
        assert re.match(r"^R\d\d-[A-Z0-9-]+$", r.id)
        assert callable(r.check)
    assert any("DEC-104" in r.source for r in L.RULES)


def test_readme_lists_every_rule():
    readme = (PKG_DIR / "README.md").read_text(encoding="utf-8")
    for r in L.RULES:
        assert r.id in readme, r.id


def test_own_files_are_clean_under_the_repository_text_rules():
    files = list(PKG_DIR.glob("*.py")) + [PKG_DIR / "README.md", TEMPLATE, Path(__file__)]
    for f in files:
        text = f.read_text(encoding="utf-8")
        assert text.isascii(), f"{f.name}: non-ASCII character"
        assert not L._RX_MODEL.search(text), f"{f.name}: model name"
        assert not any(rx.search(text) for rx in L._RX_SECRET), f"{f.name}: credential-like text"
        for rx in L._RX_HOST:
            assert not rx.search(text), f"{f.name}: host-like text {rx.pattern}"


def test_package_reads_nothing_but_the_given_file():
    src = "\n".join(p.read_text(encoding="utf-8") for p in PKG_DIR.glob("*.py"))
    for forbidden in ("import requests", "urllib", "socket", "import boto", "subprocess", "duckdb", "pandas"):
        assert forbidden not in src, forbidden
