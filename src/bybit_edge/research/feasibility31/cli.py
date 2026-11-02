"""Command line: ``python -m bybit_edge.research.feasibility31.cli CANDIDATE.yaml [options]``.

Reads one candidate file (YAML/JSON, nuisance numbers of the dossier only), prints or writes the feasibility report as
JSON and/or Markdown.  Exit codes: 0 ok, 2 loud input failure, 3 regression values (``--check-expected``) deviate.
No network, no market data, no sealed file; input and output paths inside the run-artifact or harvest directories are
refused.
"""
from __future__ import annotations

import argparse
import sys

from . import report as rp
from .schema import FeasibilityInputError, guard_path, load_candidate, verify_sources

__all__ = ["main", "build_parser"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="feasibility31", description=__doc__.splitlines()[0])
    ap.add_argument("candidate", help="candidate file (.yaml/.yml/.json)")
    ap.add_argument("--format", choices=("json", "md", "both"), default="md", help="stdout format when --out-dir is not given")
    ap.add_argument("--out-dir", help="write <candidate_id>.json and <candidate_id>.md into this directory")
    ap.add_argument("--mc-reps", type=int, help="OC Monte Carlo replicates (>= 1000)")
    ap.add_argument("--gsd-paths", type=int, help="group-sequential Monte Carlo paths with screen (>= 1000)")
    ap.add_argument("--conjunction-mc", type=int, help="draws of the exact joint conjunction power (>= 1000)")
    ap.add_argument("--check-expected", action="store_true", help="compare the report with the file's 'expected' values")
    ap.add_argument("--verify-sources", metavar="REPO_ROOT", help="report sha256 drift of the cited dossier files (read-only)")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cand = load_candidate(args.candidate)
        rep = rp.evaluate(cand, mc_reps=args.mc_reps, gsd_paths=args.gsd_paths, conjunction_mc=args.conjunction_mc)
        if args.verify_sources:
            rep["source_check"] = verify_sources(cand, args.verify_sources)
        exp_rows = rp.compare_expected(rep, cand.expected) if args.check_expected else []
        if args.check_expected:
            rep["expected_check"] = exp_rows
        text_json = rp.to_json(rep)
        text_md = rp.to_markdown(rep)
        if args.out_dir:
            out = guard_path(args.out_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{cand.candidate_id}.json").write_text(text_json, encoding="ascii")
            (out / f"{cand.candidate_id}.md").write_text(text_md, encoding="ascii")
        else:
            if args.format in ("json", "both"):
                sys.stdout.write(text_json)
            if args.format in ("md", "both"):
                sys.stdout.write(text_md)
    except FeasibilityInputError as exc:
        sys.stderr.write(f"feasibility31: INPUT ERROR: {exc}\n")
        return 2
    if args.check_expected:
        bad = [r for r in exp_rows if not r["ok"]]
        for r in exp_rows:
            sys.stderr.write(f"  {'ok ' if r['ok'] else 'BAD'} {r['key']}: expected {r['expected']} actual {r['actual']}\n")
        if bad:
            sys.stderr.write(f"feasibility31: {len(bad)} of {len(exp_rows)} expected values deviate\n")
            return 3
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
