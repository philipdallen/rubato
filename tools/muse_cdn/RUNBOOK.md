# rubato-samples CDN — Operations Runbook

A free Cloudflare R2 + Workers CDN serving rubato's CC-licensed sample
libraries to agents. Total bill: $0 (R2 free tier: 10 GB storage, 1M Class A /
10M Class B ops per month, $0 egress).

## Live inventory

- Cloudflare account ID: `ff2867fbdc8024306badfd79f5f079f3` (created 2026-10-18)
- R2 bucket: `rubato-samples` (WNAM, Standard, created 2026-10-18T23:47:00Z)
- Worker: `rubato-samples-cdn`
- Public URL: `https://rubato-samples-cdn.rubato.workers.dev`
- Contents (7,014 files, ~4.7 GB, verified 2026-10-18):
  - `libs/sonatina-sso/` — 3,827 files, 1,481,120,885 bytes. License:
    **CC Sampling+ 1.0** (noncommercial research use).
    Upstream: <https://github.com/peastman/sso>
  - `libs/vsco2-ce/` — 3,187 files, 3,237,679,771 bytes. License: **CC0 1.0**.
    Upstream: <https://github.com/sgossner/VSCO-2-CE>
- `manifest.json` (bucket root): per-file sha256 for every object.
- Worker source: `worker/src/index.js`.

## Credentials (two of them, do not mix them up)

1. **Cloudflare API token** — for managing Cloudflare (R2 uploads, worker
   deploys, secret rotation). Needs *Account → Workers R2 Storage: Edit* and
   *Workers Scripts: Edit*. Pass it as a Bearer token (`CLOUDFLARE_API_TOKEN`).
   It is in the secure vault, **not** in this package.
2. **CDN_TOKEN** — the bearer token the worker itself demands
   (`Authorization: Bearer <token>` on every request). Set once via the secrets
   API. The worker never exposes it; it is write-only. If it is lost, rotate it
   (step 6) and distribute the new value to agents.

## Deploy from scratch (or redeploy the worker)

All commands use the Cloudflare API directly. Replace `$TOKEN` with the API
token and `$ACCT` with the account ID.

### 0. One-time: enable R2
R2 must be enabled in the Cloudflare dashboard (Storage & Databases → R2)
before any API call. Without it every R2 call fails with code 10042
(`r2_storage_not_enabled`). A human must click this; there is no API path.

### 1. Create the bucket
```
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCT/r2/buckets/rubato-samples" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"locationHint":"wnam"}'
```

### 2. Upload objects
Use `scripts/r2_upload.py` (resumable, skips files already present at the same
size). Max 300 MB per object. Key encoding: percent-encode everything except
`/`, which stays literal. Example:
```
python3 scripts/r2_upload.py --account $ACCT --bucket rubato-samples \
  --src ./vsco2-ce --prefix libs/vsco2-ce
```
`scripts/upload.sh` is the rclone-based alternative (it also builds the
manifest entry).

### 3. Create the workers.dev subdomain (one-time per account)
```
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCT/workers/subdomain" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"subdomain":"rubato"}'
```
A 409 means the name is taken; pick another and update URLs everywhere.

### 4. Deploy the worker
Multipart upload of `worker/src/index.js`:
```
cd worker
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCT/workers/scripts/rubato-samples-cdn" \
  -H "Authorization: Bearer $TOKEN" \
  -F "metadata={\"main_module\":\"index.js\",\"compatibility_date\":\"2026-10-18\"};type=application/json" \
  -F "index.js=@src/index.js;type=application/javascript+module"
```

### 5. Enable the workers.dev route
Deploy alone does not make the workers.dev URL live; without this step requests
fail with error 1042 ("workers.dev routing not enabled"):
```
curl -s -X POST "https://api.cloudflare.com/client/v4/accounts/$ACCT/workers/scripts/rubato-samples-cdn/subdomain" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"enabled":true}'
```

### 6. Set the CDN_TOKEN secret
```
curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCT/workers/scripts/rubato-samples-cdn/secrets" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"CDN_TOKEN","text":"<new-token>","type":"secret_text"}'
```
Use a fresh random value
(`python3 -c "import secrets; print(secrets.token_urlsafe(32))"`). The worker
reads it at request time, no redeploy needed. Fails closed: without the secret
every request 503s, never serves samples.

### 7. Upload manifest.json
`manifest.json` maps `libraries -> {lib: {license, upstream, file_count, bytes,
files: [{path, size, sha256}]}}`. Generate it from the uploaded tree and PUT it
to the bucket root as key `manifest.json`. The worker serves it at
`/manifest.json` with `Cache-Control: max-age=300`.

### 8. Verify
```
node tests/worker_test.mjs https://rubato-samples-cdn.rubato.workers.dev <CDN_TOKEN>
```
17 checks: 401 on missing/wrong token, manifest 200 with both libraries,
file fetch + sha256 match for both libraries, Range 206 with correct
Content-Range, plain GET 200 (regression), HEAD 200, encoded-path 200
(regression). Last full run 2026-10-19: 17 passed, 0 failed.

## Gotchas

1. **R2 must be enabled in the dashboard first** (code 10042). No API path.
2. **The workers.dev route needs a separate enable call** (error 1042 without it).
3. **300 MB per object** on the REST upload endpoint.
4. **Multi-range requests return 416.** The worker parses a single
   `bytes=<start>-<end>` only; a multi-range header (`bytes=0-1,5-6`) is treated
   as unsatisfiable. Issue separate requests instead.
5. **`?token=` puts the secret in access logs and `Referer`.** It is supported
   for convenience; prefer the `Authorization` header for agent traffic.
6. **Free-tier headroom:** 10 GB storage (using ~4.7 GB), 1M Class A /
   10M Class B ops per month. `fetch.sh` does conditional re-sync so agents
   don't re-download the world.

## Routine operations

- **Rotate CDN_TOKEN:** run step 6 with a new value and distribute it to
  agents. Old token dies immediately.
- **Add a library:** upload its tree under a new prefix, regenerate
  `manifest.json`, PUT it to the bucket root. Keep the
  `worker/manifest.example.json` shape.
- **Agent sync:** `RUBATO_CDN_URL=... RUBATO_CDN_TOKEN=... sh scripts/fetch.sh <library-name> <dest-dir>`
  — pulls the manifest, downloads missing/changed files, verifies sha256.

## License boundary (non-negotiable)

Only CC-licensed content goes on this CDN: CC0 (VSCO 2 CE) and CC Sampling+ 1.0
(Sonatina SSO, noncommercial research OK). **Never host Spitfire or other
commercial libraries here.** The Spitfire EULA forbids redistribution, forbids
reformatting for another sampler, and forbids AI/LLM training use without
express written consent. Its free Discover libraries can only be used locally by
a human, never redistributed or served to agents.
