"""muse-study CLI: run a conductor-training study script against a seed.

    python3 tools/muse_study/cli.py list
    python3 tools/muse_study/cli.py run <script> <seed.yaml>

Runs each directive step through the rehearsal compiler and reports, per
step, whether the directive survived (seed-param level; render-level is
stand-in-blocked until the real L1 lands). Exit 0 always — the report is
the drill, not a gate.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))

from muse_ir import load as load_work  # noqa: E402
from muse_seed import load_seed  # noqa: E402

from muse_study import SCRIPTS, run_script  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve(path):
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="muse-study", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list the precomposed study scripts")
    r = sub.add_parser("run", help="run a study script")
    r.add_argument("script", choices=sorted(SCRIPTS))
    r.add_argument("seed")
    r.add_argument("--era", default="baroque")
    r.add_argument("--live", action="store_true",
                   help="use the real L1 generate loop (mirrors "
                        "MUSE_L1_LIVE in muse_grow); default is the "
                        "deterministic stand-in")
    args = ap.parse_args(argv)

    if args.cmd == "list":
        for name, s in sorted(SCRIPTS.items()):
            print(f"{name:22s} {s.issue}")
        return 0

    script = SCRIPTS[args.script]
    seed = load_seed(open(_resolve(args.seed)).read(), fmt="yaml")
    work = load_work(_resolve(seed.provenance["source"])) \
        if seed.provenance.get("source") else None
    if args.live:
        # mirror muse_grow's gate: the live loop is selected by MUSE_L1_LIVE
        os.environ["MUSE_L1_LIVE"] = "1"
    _, reports = run_script(script, _resolve(args.seed), args.era, work)
    print(f"# {script.name} — {script.issue}\n")
    for rep in reports:
        print(f"[{rep.verdict:12s}] {rep.directive}")
        print(f"               knob {rep.measure}: {rep.base_value} -> "
              f"{rep.candidate_value}  ({rep.expect_note})")
        print(f"               render {rep.render_measure}: {rep.render_base} -> "
              f"{rep.render_candidate}  ({rep.render_verdict})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
