"""P3 conformance CLI.

    python3 tools/muse_ci/cli.py verify            # fast registry (the gate)
    python3 tools/muse_ci/cli.py verify --full     # all 14 corpus works
    python3 tools/muse_ci/cli.py generate --full   # rebuild vectors/ from corpus
    python3 tools/muse_ci/cli.py dump <work-id>    # actual decoded canonical JSON

verify exits 0 when every selected vector conforms, 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "s1_stream"))

from muse_ci.conformance import (  # noqa: E402
    FAST_REGISTRY,
    REGISTRY,
    VECTORS_DIR,
    decoded_canonical,
    generate,
    verify,
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="muse-ci")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("verify", "generate"):
        p = sub.add_parser(name)
        p.add_argument("--full", action="store_true",
                       help="whole corpus registry (default: fast subset)")
        p.add_argument("--vectors", default=VECTORS_DIR,
                       help="vector store directory (default: committed store)")
    d = sub.add_parser("dump", help="write the actual decoded canonical JSON")
    d.add_argument("work_id")
    d.add_argument("-o", "--output", required=True)
    d.add_argument("--vectors", default=VECTORS_DIR)
    args = ap.parse_args(argv)

    if args.cmd == "dump":
        mu = os.path.join(args.vectors, f"{args.work_id}.ru")
        with open(args.output, "wb") as fh:
            fh.write(decoded_canonical(mu))
        print(f"wrote {args.output}")
        return 0

    registry = REGISTRY if args.full else FAST_REGISTRY
    if args.cmd == "generate":
        vectors = generate(args.vectors, registry)
        print(f"generate: wrote {len(vectors)} vectors to {args.vectors}")
        return 0

    results = verify(args.vectors, registry)
    for r in results:
        print(f"{r.status}  {r.work_id:24s} {r.detail}")
    ok = all(r.status == "PASS" for r in results)
    print("verify:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
