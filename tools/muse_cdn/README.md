# muse_cdn — token-gated sample-library CDN (Cloudflare Worker + R2)

Serves rubato's CC-licensed sample libraries to agents over HTTPS from a
Cloudflare R2 bucket, with range requests and sha256 verification. Built so
agents stop re-downloading gigabytes of samples into `/tmp` on every fresh
sandbox.

Live: <https://rubato-samples-cdn.rubato.workers.dev> — 7,014 files, ~4.7 GB.

## License boundary (read first)

This CDN is for **CC0 / CC-licensed content only**:

| Library | License | Upstream |
|---|---|---|
| VSCO 2 CE (~3.0 GB) | CC0 1.0 | <https://github.com/sgossner/VSCO-2-CE> |
| Sonatina SSO (~1.4 GB) | CC Sampling+ 1.0 (noncommercial research) | <https://github.com/peastman/sso> |

**Never upload Spitfire libraries here** (BBCSO Discover, SSO Discover, or any
paid tier). Their EULA forbids redistribution and forbids reformatting for
another sampler. A local download for listening is fine; serving the files to a
fleet is not. See `docs/design/l5-sample-waiver.md` for the commercial-tier path.

## Layout

```
worker/src/index.js        the worker: auth, manifest, range-aware file serving
worker/wrangler.toml       worker + R2 bucket binding
worker/manifest.example.json  shape of the manifest the worker serves
scripts/upload.sh          push a library to R2 (rclone) and refresh manifest.json
scripts/r2_upload.py       REST-API uploader (resumable, 300 MB/object cap)
scripts/fetch.sh           agent-side: sync a library with sha256 verification
tests/worker_test.mjs      live worker harness (17 checks)
```

## Agent usage

```sh
export RUBATO_CDN_URL="https://rubato-samples-cdn.rubato.workers.dev"
export RUBATO_CDN_TOKEN="<the CDN_TOKEN secret>"
sh scripts/fetch.sh sonatina-sso /tmp/sso
```

Raw curl also works (auth via header or `?token=`):

```sh
curl -H "Authorization: Bearer $RUBATO_CDN_TOKEN" \
  "$RUBATO_CDN_URL/manifest.json"
curl -H "Authorization: Bearer $RUBATO_CDN_TOKEN" \
  -r 0-1048575 "$RUBATO_CDN_URL/libs/sonatina-sso/strings/violin-sus.sfz" \
  -o violin-sus.sfz.part
```

Files are served immutable (`Cache-Control: max-age=31536000, immutable`); the
manifest is short-cached (5 min). Version a library by uploading under a new
`libs/<name>-<version>/` prefix rather than overwriting.

## Verify

Two suites, one live and one hermetic.

```sh
# Hermetic (fast tier, CI): local wrangler dev + local R2, no secret, no network.
node tests/worker_hermetic_test.mjs
# or via the unified runner (registers as the `muse_cdn` suite):
./tools/run_tests.sh

# Live end-to-end (operator/landing): needs the deployed URL and the real secret.
node tests/worker_test.mjs "$RUBATO_CDN_URL" "$RUBATO_CDN_TOKEN"
```

`worker_hermetic_test.mjs` (14 checks) starts `wrangler dev` against a
throwaway `--persist-to` directory, seeds `manifest.json` + one library file
into the local R2 binding, and passes the token as a literal `--var` — so it
needs no `CDN_TOKEN` and never touches the network. It covers auth gating,
manifest shape, file fetch + sha256, `Range`/206, plain GET/200, HEAD, the
percent-encoded-path regression, and the manifest POST/405 gate. It needs the
`wrangler` CLI on `PATH` (or `WRANGLER_BIN`); the pytest wrapper skips if the
CLI is absent, so a sandbox without a node toolchain does not fail the gate.

`worker_test.mjs` (17 checks) is the live harness: auth gating, manifest shape,
per-library fetch + sha256 match, Range/206, HEAD, and both regression pins.
Last full run 2026-10-19: **17 passed, 0 failed**.

## Deploy

See `RUNBOOK.md` for the from-scratch sequence (enable R2, create the bucket,
upload objects, deploy the worker, enable the workers.dev route, set the secret,
upload the manifest). Operational gotchas — R2 must be enabled in the dashboard
first, the workers.dev route needs its own enable call, 300 MB per object — are
recorded there. `RUNBOOK.md` §Authenticating to the Cloudflare API covers the
API-token auth pattern (including why every call is direct REST rather than
`wrangler`); no credential-bearing helper is carried in this repo.

## Cost

Inside Cloudflare's free tier: 10 GB R2 storage, 1M Class A / 10M Class B ops
per month, $0 egress. Both libraries together are ~4.7 GB.
