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

SCRIPTS = ("a2v_common.py", "a2v_oi.py", "a2v_sigma30.py", "a2v_power.py", "a2v_build.py")
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
    for d in (oi, sg, pw):
        d.pop("label", None)
    out = {
        "label": c.LABEL,
        "stand": "2026-10-29, ENTWURF der Herleitung (nichts registriert, kein Verdikt)",
        "regeln": "R-1..R-11 im Docstring von a2v_common.py (vor jeder Zahl fixiert)",
        "herkunft": {
            "teil_A_oi_kalender_zeitlage": "S:a2v_oi.py; Eingaben: Settlement-Rohpartitionen (nur type/instrument_name/"
                                           "timestamp/position, R-2), Kalender-Extrakt; Regeln R-1, R-2, R-4",
            "teil_B_sigma30": "S:a2v_sigma30.py; Eingaben: 1-min-Kerzen BTCUSDT/ETHUSDT 2021-03-24..2024-05-31 "
                              "(Assert R-1), Kalenderklassen R-4; Regeln R-3..R-8",
            "teil_B4_power": "S:a2v_power.py; Eingaben: teil_A + teil_B (nur Streuung/Zaehlung); power_p1; Regeln R-9, R-10",
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
    }
    h = c.dump(out, c.OUT_DIR / "a2_vorarbeit.json")
    print("sha256", h)


if __name__ == "__main__":
    main()
