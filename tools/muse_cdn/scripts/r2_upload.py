#!/usr/bin/env python3
"""Upload files to a Cloudflare R2 bucket via the REST API.

Usage:
  r2_upload.py --account <id> --bucket <name> --src <local_dir>
               [--prefix <key_prefix>] [--token <bearer> | env CLOUDFLARE_API_TOKEN]

Auth: needs a Cloudflare API token with Account -> Workers R2 Storage: Edit.
  - In Muse: the custom.cloudflare connector helper builds requests with
    dynamic_credentials.add_surrogate_to_request (see connector/bin/cf_api.py).
  - Anywhere else: export CLOUDFLARE_API_TOKEN=<token> and pass --token "$CLOUDFLARE_API_TOKEN".

Limits: 300 MB per object. Keys are URL-encoded except '/' (kept literal).
Skips files that already exist with the same size (assumes unchanged).
"""
import argparse, hashlib, os, sys, urllib.request
from urllib.parse import quote

def encode_key(key):
    return quote(key, safe="/")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--bucket", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--prefix", default="")
    ap.add_argument("--token", default=os.environ.get("CLOUDFLARE_API_TOKEN"))
    args = ap.parse_args()

    if not args.token:
        sys.exit("no API token: pass --token or set CLOUDFLARE_API_TOKEN")
    if args.token.startswith("{SURROGATE"):
        sys.exit("refusing to send a surrogate value literally; use add_surrogate_to_request in Muse")

    base = f"https://api.cloudflare.com/client/v4/accounts/{args.account}/r2/buckets/{args.bucket}/objects"

    files = []
    for root, _, names in os.walk(args.src):
        for n in names:
            full = os.path.join(root, n)
            rel = os.path.relpath(full, args.src).replace(os.sep, "/")
            key = (args.prefix.rstrip("/") + "/" + rel).lstrip("/") if args.prefix else rel
            files.append((full, key))
    files.sort(key=lambda x: x[1])
    print(f"{len(files)} files to consider", flush=True)

    ok, skipped, failed = 0, 0, 0
    for i, (full, key) in enumerate(files):
        size = os.path.getsize(full)
        if size > 300 * 1024 * 1024:
            print(f"[{i+1}/{len(files)}] SKIP (>{300}MB) {key}", flush=True)
            failed += 1
            continue
        # HEAD to check existing size
        try:
            head = urllib.request.Request(base + "/" + encode_key(key), method="HEAD")
            head.add_header("Authorization", f"Bearer {args.token}")
            with urllib.request.urlopen(head, timeout=30) as r:
                if r.status == 200 and int(r.headers.get("Content-Length", -1)) == size:
                    skipped += 1
                    if skipped % 500 == 0:
                        print(f"[{i+1}/{len(files)}] ... {skipped} skipped so far", flush=True)
                    continue
        except Exception:
            pass  # not present or HEAD unsupported; fall through to PUT
        try:
            with open(full, "rb") as f:
                data = f.read()
            req = urllib.request.Request(base + "/" + encode_key(key), data=data, method="PUT")
            req.add_header("Authorization", f"Bearer {args.token}")
            req.add_header("Content-Type", "application/octet-stream")
            req.add_header("Content-Length", str(len(data)))
            with urllib.request.urlopen(req, timeout=120) as r:
                if r.status in (200, 201):
                    ok += 1
                else:
                    print(f"[{i+1}/{len(files)}] HTTP {r.status} {key}", flush=True)
                    failed += 1
        except Exception as e:
            print(f"[{i+1}/{len(files)}] FAIL {key}: {e}", flush=True)
            failed += 1
        if (ok + failed) % 200 == 0:
            print(f"[{i+1}/{len(files)}] uploaded {ok}, skipped {skipped}, failed {failed}", flush=True)

    print(f"DONE: uploaded={ok} skipped={skipped} failed={failed}")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
