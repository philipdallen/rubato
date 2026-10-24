#!/bin/sh
# Stage the Clinton St proof page on the CDN (#443).
#
# Requires: RUBATO_CDN_TOKEN with R2 write access.
# Two steps, both currently blocked by a stale credential (401):
#   1. add a "/proof/" entry to SITE_PREFIXES in
#      tools/muse_cdn/worker/src/index.js and redeploy the worker;
#   2. upload site/proof/clinton-st/{index.html,score.png,clinton-st.wav} to R2.
set -eu
CDN="https://rubato-samples-cdn.rubato.workers.dev"
HERE="$(cd "$(dirname "$0")" && pwd)"
: "${RUBATO_CDN_TOKEN:?set RUBATO_CDN_TOKEN}"

# Fail fast and loudly on a stale credential, rather than half-uploading.
code=$(curl -s -o /dev/null -w '%{http_code}' \
  -H "Authorization: Bearer $RUBATO_CDN_TOKEN" "$CDN/manifest.json")
if [ "$code" != "200" ]; then
  echo "CDN auth failed ($code) - token stale, nothing uploaded." >&2
  exit 1
fi

for f in index.html score.png; do
  curl -sS -f -X PUT -H "Authorization: Bearer $RUBATO_CDN_TOKEN" \
    --data-binary "@$HERE/$f" "$CDN/site/proof/clinton-st/$f"
  echo "uploaded $f"
done

# The WAV is 4 MB and reproducible; render it, then upload.
python3 "$HERE/../../artifacts/clinton-st/build.py" >/dev/null
curl -sS -f -X PUT -H "Authorization: Bearer $RUBATO_CDN_TOKEN" \
  --data-binary "@$HERE/../../artifacts/clinton-st/clinton-st.wav" \
  "$CDN/site/proof/clinton-st/clinton-st.wav"
echo "uploaded clinton-st.wav"
echo "staged: $CDN/proof/clinton-st/index.html?token=<CDN_TOKEN>"
