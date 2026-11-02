"""Merge the guarded work outputs into state/herleitung_a2/a2_vorarbeit.json with provenance per section,
input and script sha256 (R-11).  Reads only the work JSONs and file bytes for hashing."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import a2v_common as c  # noqa: E402

SCRIPTS = ("a2v_common.py", "a2v_oi.py", "a2v_sigma30.py", "a2v_power.py", "a2v_fut.py", "a2v_corr2.py",
           "a2v_konj.py", "a2v_build.py")
C17_LINE = ("C.17 (Fassung 2): unzentrierte Betrags-Quantile und 1,4826 x MAD je Klasse/Jahr/Serie wurden gesehen und "
            "ausgegeben, in Fassung 1 auch fuer die gepaarte Differenz-Reihe r_pre - r[15:30] (in Fassung 2 aus dem JSON "
            "entfernt); daraus wurde kein Lagewert abgeleitet. W1/W2: die 2.0-Hypothesen H-01..H-18 sahen Bybit/Deribit-"
            "Daten 2026-03-27..2026-07-04 (Mikrostruktur, Sekunden- bis Minutenhorizont), darunter die 08:00-Slots "
            "2026-03-27..2026-06-28 in W2; kein r_pre-Mittel ueber 07:30-08:00 wurde dort gebildet; Weiss et al. "
            "(2021-2023) liegt vor W1.")
REUSED = {"hfrv_common.py (load_kline)": c.SCRATCH / "hfrv_herleitung" / "hfrv_common.py",
          "h27_common.py (Waechter)": c.SCRATCH / "hfrv_herleitung" / "h27_common.py",
          "power_p1.py": Path("/home/user/scinance/src/bybit_edge/research/power_p1.py")}


def raw_partitions_digest() -> dict:
    h = hashlib.sha256()
    n = 0
    for sym in ("BTC", "ETH"):
        for day, f in c.raw_partitions(sym):
            h.update(f"{sym}|{day}|{Path(f).name}|{c.sha256(f)}\n".encode())
            n += 1
    return {"n_files": n, "sha256_of_sorted_list": h.hexdigest(),
            "range": f"{c.FIRST_CAL_DAY}..{c.LAST_CAL_DAY} (spaetere Partitionen nie geoeffnet)"}


def main() -> None:
    oi = json.loads((c.WORK / "a2v_oi.json").read_text())
    sg = json.loads((c.WORK / "a2v_sigma30.json").read_text())
    pw = json.loads((c.WORK / "a2v_power.json").read_text())
    fu = json.loads((c.WORK / "a2v_fut.json").read_text())
    cr = json.loads((c.WORK / "a2v_corr2.json").read_text())
    kj = json.loads((c.WORK / "a2v_konj.json").read_text())
    for d in (oi, sg, pw, fu, cr, kj):
        d.pop("label", None)
    b5 = {"quelle": kj["quelle"], "festlegung_orchestrator": kj["festlegung_orchestrator"], "mc": kj["mc"],
          "n_per_window": kj["n_per_window"], "modo_days_with_future_delivery": kj["modo_days_with_future_delivery"],
          "same_day_corr_cluster_inputs": {"quelle": cr["quelle"], **cr["same_day_corr_cluster"]},
          "designs": kj["designs"]}
    b6 = {"quelle": kj["quelle"] + "; Wochen-Korrelation S:a2v_corr2.py",
          "week_corr_inputs": cr["did_week_corr_fri_vs_modo_paired_series"], **kj["did"]}
    out = {
        "label": c.LABEL + " " + C17_LINE,
        "stand": "Fassung 2 (2026-10-29) nach REVIEW_A2_VORARBEIT.md, Auflagen A-1..A-6 eingearbeitet; ENTWURF der "
                 "Herleitung (nichts registriert, kein Verdikt)",
        "regeln": "R-1..R-11 (Fassung 1) und R-12..R-15 (Fassung 2) im Docstring von a2v_common.py (jeweils vor der ersten Zahl fixiert)",
        "herkunft": {
            "teil_A_oi_kalender_zeitlage": "S:a2v_oi.py; Eingaben: Settlement-Rohpartitionen (nur type/instrument_name/"
                                           "timestamp/position, R-2), Kalender-Extrakt; Regeln R-1, R-2, R-4",
            "teil_B_sigma30": "S:a2v_sigma30.py; Eingaben: 1-min-Kerzen BTCUSDT/ETHUSDT 2021-03-24..2024-05-31 "
                              "(Assert R-1), Kalenderklassen R-4; Regeln R-3..R-8",
            "teil_B4_power": "S:a2v_power.py; Eingaben: teil_A + teil_B (nur Streuung/Zaehlung); power_p1; Regeln R-9, R-10",
            "teil_A5_futures_kalender": "S:a2v_fut.py; Eingaben: Settlement-Rohpartitionen <= 2026-06-30, nur type/"
                                        "instrument_name/timestamp der Futures-Deliveries; Regel R-14",
            "teil_B5_konjunktion": "S:a2v_konj.py + S:a2v_corr2.py; Eingaben: teil_A, teil_B (Streuung, Korrelation), "
                                   "teil_A5; power_p1; Regel R-15",
            "teil_B6_did": "S:a2v_konj.py + S:a2v_corr2.py; Eingaben: teil_B (gepaarte Differenz-SD, c), Wochen-Korrelation; "
                           "power_p1",
            "fassung2_teil_B_sigma30": "gegen Fassung 1 nur entfernt: Betrags-Quantile abs_q* der Differenz-Reihe "
                                       "pre_minus_fix1530 (528 Schluessel); alle anderen Zahlen bitgleich",
        },
        "inputs_sha256": {
            "bybit_rest_kline1m_BTCUSDT_2021-03-24_2024-05-31.parquet": c.sha256(c.hc.KLINE["BTC"]),
            "bybit_rest_kline1m_ETHUSDT_2021-03-24_2024-05-31.parquet": c.sha256(c.hc.KLINE["ETH"]),
            "deribit_rest_settlements_CALENDAR_2017-05-25_2026-10-20.parquet": c.sha256(c.SETT_CAL),
            "deribit_rest.settlements_raw_partitions": raw_partitions_digest(),
        },
        "skripte_sha256": {s: c.sha256(HERE / s) for s in SCRIPTS},
        "wiederverwendet_sha256": {k: c.sha256(v) for k, v in REUSED.items()},
        "teil_A_oi_kalender_zeitlage": oi,
        "teil_B_sigma30": sg,
        "teil_B4_power": pw,
        "teil_A5_futures_kalender": fu,
        "teil_B5_konjunktion": b5,
        "teil_B6_did": b6,
    }
    h = c.dump(out, c.OUT_DIR / "a2_vorarbeit.json")
    print("sha256", h)


if __name__ == "__main__":
    main()
