#!/bin/sh
# fetch.sh — agent-side downloader: sync one library from the R2 CDN with
# sha256 verification, skipping files that already verify.
#
# Usage: ./scripts/fetch.sh <library-name> <dest-dir>
#
# Env (required):
#   RUBATO_CDN_URL    worker base URL, e.g. https://rubato-samples-cdn.<you>.workers.dev
#   RUBATO_CDN_TOKEN  the CDN_TOKEN secret
#
# Requires: curl, python3, sha256sum.
set -eu

LIB="${1:?usage: fetch.sh <library-name> <dest-dir>}"
DEST="${2:?usage: fetch.sh <library-name> <dest-dir>}"
: "${RUBATO_CDN_URL:?set RUBATO_CDN_URL}"
: "${RUBATO_CDN_TOKEN:?set RUBATO_CDN_TOKEN}"
command -v curl >/dev/null || { echo "curl not found"; exit 1; }
command -v python3 >/dev/null || { echo "python3 not found"; exit 1; }

TMPD=$(mktemp -d)
trap 'rm -rf "$TMPD"' EXIT

auth() { # $1 = url, $2 = output file; extra curl args follow
  curl -sSf -H "Authorization: Bearer $RUBATO_CDN_TOKEN" "$@"
}

echo "-> fetching manifest ..."
auth "$RUBATO_CDN_URL/manifest.json" -o "$TMPD/manifest.json"

LIB="$LIB" DEST="$DEST" MANIFEST="$TMPD/manifest.json" \
BASE="$RUBATO_CDN_URL" TOKEN="$RUBATO_CDN_TOKEN" python3 - <<'EOF'
import json, os, subprocess, sys

lib = os.environ["LIB"]
dest = os.environ["DEST"]
base = os.environ["BASE"].rstrip("/")
token = os.environ["TOKEN"]

with open(os.environ["MANIFEST"]) as f:
    manifest = json.load(f)
entry = (manifest.get("libraries") or {}).get(lib)
if not entry:
    sys.exit(f"library not in manifest: {lib}")

ok = skip = 0
for fi in entry["files"]:
    rel = fi["path"]
    assert rel.startswith(f"libs/{lib}/"), f"bad path in manifest: {rel}"
    local = os.path.join(dest, os.path.relpath(rel, f"libs/{lib}"))
    os.makedirs(os.path.dirname(local), exist_ok=True)
    if os.path.exists(local):
        out = subprocess.run(["sha256sum", local], capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.split()[0] == fi["sha256"]:
            skip += 1
            continue
    url = f"{base}/{rel}"
    tmp = local + ".part"
    # Resume only from a partial smaller than the expected size. A stale .part
    # at or over the target makes `curl -C -` fail the whole run, not just this
    # file, so drop it first.
    if os.path.exists(tmp) and os.path.getsize(tmp) >= fi["size"]:
        os.remove(tmp)
    r = subprocess.run(
        ["curl", "-sSf", "-H", f"Authorization: Bearer {token}",
         "-C", "-", "-o", tmp, url],
        capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"download failed: {rel}\n{r.stderr.strip()}")
    out = subprocess.run(["sha256sum", tmp], capture_output=True, text=True)
    digest = out.stdout.split()[0]
    if digest != fi["sha256"]:
        os.remove(tmp)
        sys.exit(f"checksum mismatch: {rel}")
    os.replace(tmp, local)
    ok += 1
    if (ok + skip) % 50 == 0:
        print(f"  ... {ok + skip}/{len(entry['files'])}", flush=True)

print(f"done: {ok} fetched, {skip} already verified -> {dest}")
EOF
