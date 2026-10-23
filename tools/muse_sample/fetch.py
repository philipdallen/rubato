"""Fetch the VSCO 2 CE string sections from the Rubato CDN sample library.

The CDN hosts the raw VSCO 2 CE pool (no SFZ); this pulls the four
sustain-vibrato sections the sample tier renders with. Any agent with
the CDN token can stand up the quality tier locally:

    python3 tools/muse_sample/fetch.py ./samples --token <CDN_TOKEN>
    RUBATO_SAMPLE_ROOT=./samples python3 tools/muse_rehearse/cli.py \\
        render-dry-run seeds/bwv227.1.seed.yaml "phrase: quieter at bar 8" \\
        --tier samples
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

CDN = "https://rubato-samples-cdn.rubato.workers.dev"
PREFIX = "libs/vsco2-ce/"

from muse_sample.render import DEFAULT_INSTRUMENTS  # noqa: E402


def _get(url, token):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (rubato-sample-fetch)")
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dest", help="local root for the sample pool")
    ap.add_argument("--token", default=os.environ.get("RUBATO_CDN_TOKEN"),
                    help="CDN token (env RUBATO_CDN_TOKEN)")
    ap.add_argument("--dry", action="store_true",
                    help="list what would be fetched, download nothing")
    args = ap.parse_args(argv)
    if not args.token:
        print("no CDN token: pass --token or set RUBATO_CDN_TOKEN",
              file=sys.stderr)
        return 1
    manifest = json.loads(_get(CDN + "/manifest.json", args.token))
    wanted = {PREFIX + rel + "/" for rel in DEFAULT_INSTRUMENTS.values()}
    files = [f for f in manifest["libraries"]["vsco2-ce"]["files"]
             if any(f["path"].startswith(w) for w in wanted)]
    total = sum(f["size"] for f in files)
    print(f"{len(files)} files, {total / 1e6:.0f} MB")
    for f in files:
        rel = f["path"][len(PREFIX):]
        dest = os.path.join(args.dest, rel)
        if args.dry:
            print(" ", rel)
            continue
        if os.path.isfile(dest) and os.path.getsize(dest) == f["size"]:
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        data = _get(CDN + "/" + f["path"].replace(" ", "%20"), args.token)
        with open(dest, "wb") as fh:
            fh.write(data)
        print(" ", rel)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
