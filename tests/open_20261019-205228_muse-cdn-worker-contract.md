# Test spec — muse_cdn worker contract (`tools/muse_cdn/tests/worker_test.mjs`)

Written 2026-10-19 by the landing agent, per TASK_WORKFLOW §6.

## What landed (behavior under test)

`tools/muse_cdn` — the token-gated Cloudflare Worker + R2 CDN that serves the
CC-licensed sample libraries to agents. The harness exercises the deployed
worker against its contract; it is a live integration test, not a unit test.

Coverage: `tests/worker_test.mjs` (17 checks, requires node ≥ 18 + `CDN_TOKEN`).

## Checks

**Auth gating**
1. `GET /manifest.json` with no token → 401.
2. `GET /manifest.json` with a wrong token → 401.

**Manifest**
3. Authed `GET /manifest.json` → 200.
4. `manifest.libraries["sonatina-sso"].files` is an array.
5. `manifest.libraries["vsco2-ce"].files` is an array.
6. Sonatina entries carry a `sha256`.
7. VSCO2-CE entries carry a `sha256`.

**File fetch + integrity (both libraries)**
8. `GET /libs/sonatina-sso/<path>` → 200.
9. Body sha256 equals the manifest's `sha256` for that file.
10. `GET /libs/vsco2-ce/<path>` → 200.
11. Body sha256 equals the manifest's `sha256` for that file.

**Range / methods / regressions**
12. `Range: bytes=0-99` → 206.
13. `Content-Range` is exactly `bytes 0-99/<size>`.
14. Plain GET → 200, not 206 (regression: R2's `get()` spuriously sets `obj.range`).
15. `HEAD` → 200.
16. `HEAD` `Content-Length` equals the manifest size.
17. Percent-encoded path → 200, not 404 (regression: worker once skipped
    `decodeURIComponent` on the captured path).

## Verification that the checks are not vacuous

Two bugs in the original harness were found and fixed while landing this, and
the live run is what proved them:

- **Wrong manifest shape.** The harness read `manifest.files[lib]`; every
  producer/consumer uses `manifest.libraries[lib].files` (confirmed against the
  live `manifest.json`: top-level key is `libraries`). The old read threw
  `TypeError` before any file check.
- **Unreachable URLs.** The harness built `"/" + lib + "/" + path`, which never
  matches the worker's `^/libs/([A-Za-z0-9._-]+)/(.+)$` route → every fetch
  404'd. Entry `path` values are already R2 keys of the form
  `libs/<lib>/<rel>`; the harness now fetches them verbatim.

Run against the live worker after the fix: **17 passed, 0 failed** (2026-10-19).

## Known gaps (acceptable)

- **Requires the live endpoint and a real `CDN_TOKEN`.** It cannot run offline
  or in the fast tier; it is an operator/landing verification, run by hand.
- **Does not test the write path** (R2 upload, worker deploy, secret set).
  Those are manual runbook steps; automating them needs the Cloudflare API
  token and would write to production.
- **Multi-range and `?token=`** are documented behaviors, not asserted.
