"""muse-rehearse CLI: parse a directive, dry-run the compiled delta, commit.

    python3 tools/muse_rehearse/cli.py dry-run <seed.yaml> "phrase: quieter at bar 8"
    python3 tools/muse_rehearse/cli.py commit <seed.yaml> <slug> "rebalance: bring P1 up at bar 8"

dry-run prints the param diff the commit would make (writes nothing).
score-dry-run compiles the candidate in memory and probes it against the
base seed — the score the dry run cannot show — and also writes nothing.
render-dry-run compiles the candidate and renders what it sounds like
through the deterministic stand-in; writes only the content-addressed
WAV under docs/workbench/data/renders/.
commit writes the directive file + revision and re-stamps lineage.
Exit 0 ok; 1 on a grammar error (with the valid vocabulary).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))

from muse_ir import load as load_work  # noqa: E402
from muse_seed import load_seed  # noqa: E402

from muse_rehearse import (  # noqa: E402
    DirectiveError, parse_directive, dry_run, commit_directive,
)

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve(path):
    return path if os.path.isabs(path) else os.path.join(REPO, path)


def _load(seed_path):
    seed = load_seed(open(_resolve(seed_path)).read(), fmt="yaml")
    src = seed.provenance.get("source")
    work = load_work(_resolve(src)) if src else None
    return seed, work


def main(argv=None):
    ap = argparse.ArgumentParser(prog="muse-rehearse", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dry-run", help="compile + show the param diff")
    d.add_argument("seed")
    d.add_argument("directive")
    d.add_argument("--era", default="baroque")

    s = sub.add_parser("score-dry-run",
                       help="compile the candidate in memory and probe it "
                            "against the base seed; writes nothing")
    s.add_argument("seed")
    s.add_argument("directive")
    s.add_argument("--era", default="baroque")

    rd = sub.add_parser("render-dry-run",
                        help="compile the candidate and render what it "
                             "sounds like (stand-in WAV); writes only "
                             "the content-addressed WAV")
    rd.add_argument("seed")
    rd.add_argument("directive")
    rd.add_argument("--era", default="baroque")
    rd.add_argument("--tier", default="sine", choices=["sine", "samples"],
                    help="sine: instant stand-in; samples: VSCO 2 CE pools "
                         "from the Rubato CDN (needs --sample-root or "
                         "RUBATO_SAMPLE_ROOT)")
    rd.add_argument("--sample-root", default=None,
                    help="local root of the VSCO 2 CE library")
    rd.add_argument("--out-dir", default=None,
                    help="render directory (default: "
                         "docs/workbench/data/renders)")

    c = sub.add_parser("commit", help="write directive + revision, stamp lineage")
    c.add_argument("seed")
    c.add_argument("slug")
    c.add_argument("directive")
    c.add_argument("--era", default="baroque")

    args = ap.parse_args(argv)
    seed, work = _load(args.seed)

    try:
        directive = parse_directive(args.directive, seed=seed, work=work)
    except DirectiveError as e:
        print(f"directive error: {e}", file=sys.stderr)
        return 1

    if args.cmd == "dry-run":
        _, diff = dry_run(directive, seed, args.era, work)
        print(json.dumps(diff, indent=2))
        return 0

    if args.cmd == "score-dry-run":
        # The candidate lives only in memory: compile it, probe it against
        # the base, and report both probe sets. Nothing is written — the
        # commit path stays the only writer (R2 item 7).
        #
        # The payload is the *score*, not the diff: the seed-sensitive
        # probes (budget_fit, assertions, coverage) plus the gate probes
        # (fidelity, determinism) for base and candidate. delta_curves is
        # work-fixed (the mockup is deterministic from the work, not the
        # seed), so it rides once as context. The full param diff stays
        # with dry-run; this command reports only the changed top-level
        # keys. Everything is sized to fit the runner's stdout window.
        from muse_probes.probes import compute_probes
        candidate, diff = dry_run(directive, seed, args.era, work)
        base_report = compute_probes(seed, work, era=args.era)
        cand_report = compute_probes(candidate, work, prior_seed=seed,
                                     era=args.era)

        def score_view(report):
            probes = json.loads(report.to_json())["probes"]
            return {
                "ok": report.ok,
                "budget_fit": probes["budget_fit"],
                "assertions": probes["assertions"],
                "coverage": probes["coverage"],
                "fidelity_guard": probes["fidelity_guard"],
                "determinism": probes["determinism"],
            }

        base_probes = json.loads(base_report.to_json())["probes"]
        print(json.dumps({
            "directive": args.directive,
            "changed": sorted(diff.get("changes", {}).keys()),
            "base": score_view(base_report),
            "candidate": score_view(cand_report),
            "delta_curves": base_probes["delta_curves"],
        }))
        return 0

    if args.cmd == "render-dry-run":
        # The coaching ear: compile the candidate, render what it sounds
        # like through the deterministic stand-in (muse_audio), and write
        # only the content-addressed WAV. The render is sub-second, so
        # there is no cache to keep honest — same candidate always yields
        # the same filename and the same bytes.
        import hashlib
        from muse_audio.audio import render_seed, SampleRootMissing
        from muse_seed import dump_seed
        candidate, diff = dry_run(directive, seed, args.era, work)
        tag = hashlib.sha256(
            (args.tier + dump_seed(candidate, fmt="json")).encode()
        ).hexdigest()[:16]
        out_dir = _resolve(args.out_dir) if args.out_dir else os.path.join(
            REPO, "docs", "workbench", "data", "renders")
        os.makedirs(out_dir, exist_ok=True)
        wav_name = f"candidate-{tag}.wav"
        try:
            duration_sec, notes, digest, library = render_seed(
                work, candidate, os.path.join(out_dir, wav_name),
                tier=args.tier, sample_root=args.sample_root)
        except SampleRootMissing as e:
            print(f"render error: {e}", file=sys.stderr)
            return 1
        print(json.dumps({
            "directive": args.directive,
            "changed": sorted(diff.get("changes", {}).keys()),
            "tier": args.tier,
            "library": library,
            "wav": f"data/renders/{wav_name}",
            "duration_sec": duration_sec,
            "notes": notes,
            "sha256": digest,
        }))
        return 0
        # The candidate lives only in memory: compile it, probe it against
        # the base, and report both probe sets. Nothing is written — the
        # commit path stays the only writer (R2 item 7).
        #
        # The payload is the *score*, not the diff: the seed-sensitive
        # probes (budget_fit, assertions, coverage) plus the gate probes
        # (fidelity, determinism) for base and candidate. delta_curves is
        # work-fixed (the mockup is deterministic from the work, not the
        # seed), so it rides once as context. The full param diff stays
        # with dry-run; this command reports only the changed top-level
        # keys. Everything is sized to fit the runner's stdout window.
        from muse_probes.probes import compute_probes
        candidate, diff = dry_run(directive, seed, args.era, work)
        base_report = compute_probes(seed, work, era=args.era)
        cand_report = compute_probes(candidate, work, prior_seed=seed,
                                     era=args.era)

        def score_view(report):
            probes = json.loads(report.to_json())["probes"]
            return {
                "ok": report.ok,
                "budget_fit": probes["budget_fit"],
                "assertions": probes["assertions"],
                "coverage": probes["coverage"],
                "fidelity_guard": probes["fidelity_guard"],
                "determinism": probes["determinism"],
            }

        base_probes = json.loads(base_report.to_json())["probes"]
        print(json.dumps({
            "directive": args.directive,
            "changed": sorted(diff.get("changes", {}).keys()),
            "base": score_view(base_report),
            "candidate": score_view(cand_report),
            "delta_curves": base_probes["delta_curves"],
        }))
        return 0

    dpath, spath = commit_directive(
        directive, _resolve(args.seed), args.slug,
        era=args.era, repo_root=REPO, work=work)
    print(f"directive: {os.path.relpath(dpath, REPO)}")
    print(f"revision:  {os.path.relpath(spath, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
