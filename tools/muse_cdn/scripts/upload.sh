#!/bin/sh
# upload.sh — push one sample library to the R2 bucket and refresh manifest.json.
#
# Usage: ./scripts/upload.sh <library-name> <local-dir> <license> <upstream-url>
#
# Example:
#   ./scripts/upload.sh sonatina-sso /tmp/sso "CC Sampling+ 1.0" \
#       https://github.com/peastman/sso
#
# Env (required):
#   R2_ACCOUNT_ID        Cloudflare account ID
#   R2_ACCESS_KEY_ID     R2 API token access key
#   R2_SECRET_ACCESS_KEY R2 API token secret key
#   R2_BUCKET            bucket name (default: rubato-samples)
#
# Requires: rclone, python3.
#
# LICENSE BOUNDARY: only upload CC0 / CC-licensed content. Never upload
# Spitfire libraries (BBCSO Discover, SSO Discover, paid tiers) — their
# EULA forbids redistribution and reformatting for another sampler.
set -eu

LIB="${1:?usage: upload.sh <library-name> <local-dir> <license> <upstream-url>}"
SRC="${2:?usage: upload.sh <library-name> <local-dir> <license> <upstream-url>}"
LICENSE="${3:?usage: upload.sh <library-name> <local-dir> <license> <upstream-url>}"
UPSTREAM="${4:?usage: upload.sh <library-name> <local-dir> <license> <upstream-url>}"
BUCKET="${R2_BUCKET:-rubato-samples}"

: "${R2_ACCOUNT_ID:?set R2_ACCOUNT_ID}"
: "${R2_ACCESS_KEY_ID:?set R2_ACCESS_KEY_ID}"
: "${R2_SECRET_ACCESS_KEY:?set R2_SECRET_ACCESS_KEY}"
command -v rclone >/dev/null || { echo "rclone not found (https://rclone.org/install/)"; exit 1; }
command -v python3 >/dev/null || { echo "python3 not found"; exit 1; }
[ -d "$SRC" ] || { echo "not a directory: $SRC"; exit 1; }

ENDPOINT="https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com"
REMOTE="r2:$BUCKET"

rclone --version >/dev/null # fail fast on broken rclone
export RCLONE_CONFIG_R2_TYPE=s3
export RCLONE_CONFIG_R2_PROVIDER=Cloudflare
export RCLONE_CONFIG_R2_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID"
export RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY"
export RCLONE_CONFIG_R2_ENDPOINT="$ENDPOINT"

echo "-> syncing $SRC to $REMOTE/libs/$LIB/ ..."
rclone sync "$SRC" "$REMOTE/libs/$LIB/" \
  --transfers 16 --checkers 16 --s3-upload-concurrency 8 \
  --progress

echo "-> building manifest entry ..."
TMPD=$(mktemp -d)
MANIFEST="$TMPD/manifest.json"
# Pull the existing manifest if there is one; otherwise start fresh.
rclone cat "$REMOTE/manifest.json" > "$MANIFEST" 2>/dev/null || echo '{"libraries":{}}' > "$MANIFEST"

LIB="$LIB" LICENSE="$LICENSE" UPSTREAM="$UPSTREAM" SRC="$SRC" MANIFEST="$MANIFEST" \
python3 - <<'EOF'
import hashlib, json, os

lib = os.environ["LIB"]
src = os.environ["SRC"]
files = []
for root, _dirs, names in os.walk(src):
    for n in sorted(names):
        p = os.path.join(root, n)
        rel = os.path.relpath(p, src).replace(os.sep, "/")
        h = hashlib.sha256()
        size = 0
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
                size += len(chunk)
        files.append({"path": f"libs/{lib}/{rel}", "size": size, "sha256": h.hexdigest()})

with open(os.environ["MANIFEST"]) as f:
    manifest = json.load(f)
manifest.setdefault("libraries", {})[lib] = {
    "license": os.environ["LICENSE"],
    "upstream": os.environ["UPSTREAM"],
    "file_count": len(files),
    "bytes": sum(f["size"] for f in files),
    "files": files,
}
with open(os.environ["MANIFEST"], "w") as f:
    json.dump(manifest, f, indent=2)
    f.write("\n")
print(f"manifest entry: {lib}: {len(files)} files")
EOF

echo "-> uploading manifest.json ..."
rclone copyto "$MANIFEST" "$REMOTE/manifest.json" --s3-upload-concurrency 4
rm -rf "$TMPD"
echo "done. Library available at /libs/$LIB/ behind the worker."
