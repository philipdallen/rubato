# Test spec — muse_cdn hermetic worker suite (task #423)

Written 2026-10-19 by the completing agent, per TASK_WORKFLOW §6.

## What landed (behavior under test)

`tools/muse_cdn/tests/worker_hermetic_test.mjs` — a hermetic contract suite for
`tools/muse_cdn/worker/src/index.js`, runnable with **no `CDN_TOKEN` and no
network**. It starts `wrangler dev` (workerd) against a throwaway `--persist-to`
state directory, seeds `manifest.json` and one library file into the local R2
binding via `wrangler r2 object put --local`, and passes the token as a literal
`--var CDN_TOKEN:<value>`. The live harness (`worker_test.mjs`) stays as the
end-to-end check; this is the fast-tier counterpart that makes a worker change
verifiable without the deployed endpoint or the real secret.

Coverage: `tools/muse_cdn/tests/worker_hermetic_test.mjs` (14 checks).

Invoke:

```sh
node tests/worker_hermetic_test.mjs            # WRANGLER_BIN optional
./tools/run_tests.sh                           # fast tier (suite `muse_cdn`)
```

Registered in `tools/run_tests.sh` as the `muse_cdn` suite via
`tools/muse_cdn/tests/test_worker_hermetic.py`, a thin pytest wrapper. The
wrapper **skips** when `node` or the `wrangler` CLI is absent, so a sandbox
without a node toolchain does not report a red gate for a suite it cannot run.
`WRANGLER_BIN` points at a specific binary.

## Checks

**Auth gating**
1. `GET /manifest.json` with no token → 401.
2. `GET /manifest.json` with a wrong token → 401.
3. `GET /manifest.json` with the correct token → 200.

**Manifest shape**
4. `manifest.libraries["demo-lib"].files` is an array.
5. Entries carry a `sha256`.

**File fetch + integrity**
6. `GET /libs/demo-lib/<path>` → 200.
7. Body sha256 equals the manifest `sha256`.

**Range / methods / regressions**
8. `Range: bytes=0-99` → 206.
9. `Content-Range` is exactly `bytes 0-99/<size>`.
10. Plain GET → 200, not 206 (regression: R2 `get()` spuriously sets `obj.range`).
11. `HEAD` → 200.
12. `HEAD` `Content-Length` equals the fixture size.
13. Percent-encoded path → 200, not 404 (regression: `decodeURIComponent`).
14. `POST /manifest.json` → 405 (manifest route method gate).

## Why the checks are not vacuous

- The token is a literal (`hermetic-test-token`), never the real secret, so the
  401/200 split is proven against a known value rather than an environment one.
- The manifest is built by the suite from the same bytes it uploads, so the
  sha256 match cannot pass against a stale fixture.
- The fixture is 300 bytes, so `bytes=0-99` is a strict prefix and the
  `Content-Range` assertion pins the exact size.

## Known gaps (acceptable)

- **Needs the `wrangler` CLI.** It is not a pip dependency; the pytest wrapper
  skips without it. CI provisions it (or skips the suite) rather than failing.
- **Does not test the write path** (R2 upload, worker deploy, secret set) —
  those are manual runbook steps, unchanged from the live harness.
- **Multi-range and `?token=`** are documented behaviors, still not asserted.
