# Bug — worker test harness could not pass; manifest shape and route URL both wrong

**Found by:** run=20261019-2052-7c41 (TASK_WORKFLOW §1c in-flight defect log)
at 2026-10-19 ~20:50Z, while landing the `rubato-cdn-full` package as
`tools/muse_cdn`.

## Symptom

The package's verification harness — the evidence for the "10 checks, all 10
passed 2026-10-18" claim — cannot pass against the deployed worker or its own
artifacts. Three independent defects:

1. **Wrong manifest shape.** `worker_test.mjs` read `manifest.files[lib]`
   (lines 44–47). Every producer and consumer uses
   `manifest.libraries[lib].files`:
   - `upload.sh`: `manifest.setdefault("libraries", {})[lib] = {...}`
   - `fetch.sh`: `(manifest.get("libraries") or {}).get(lib)`
   - `manifest.example.json`: has the `libraries` wrapper
   - the live worker: top-level key is `libraries`
   Line 44 throws `TypeError: Cannot read properties of undefined (reading
   'sonatina-sso')`, aborting before any file check.
2. **Unreachable URLs.** The harness built `"/" + lib + "/" + path`; the worker
   matches `^/libs/([A-Za-z0-9._-]+)/(.+)$`. Simulated: manifest path
   `libs/sonatina-sso/foo.wav` → test URL `/sonatina-sso/libs/sonatina-sso/foo.wav`
   → 404. Every fetch/range/HEAD/encoded-path check 404s, and the 404 body is
   not JSON, so `r.json()` fails too.
3. **Miscounted checks.** Docs claim 10 checks; the file has 15 `check()` call
   sites, two inside a 2-iteration loop → 17 at runtime.

## Repro

```bash
# manifest shape (live)
curl -s -H "Authorization: Bearer $RUBATO_CDN_TOKEN" \
  https://rubato-samples-cdn.rubato.workers.dev/manifest.json \
  | python3 -c "import sys,json; print(list(json.load(sys.stdin).keys()))"
# -> ['libraries']   (the harness read manifest.files)

# route (simulate the harness URL)
node -e 'console.log(/^\/libs\/([A-Za-z0-9._-]+)\/(.+)$/.test("/sonatina-sso/strings/x.sfz"))'
# -> false
```

## Root cause

The harness was written against a manifest shape and a route prefix that the
worker never had. The worker and the manifest agree with each other
(`libs/<lib>/<rel>`); only the harness diverged. The 2026-10-18 "10 passed"
claim therefore did not come from this file as shipped.

## Fix

`tests/worker_test.mjs`: read `manifest.libraries[lib].files`, fetch entry
`path` values verbatim (`url()` percent-encodes each segment, preserving the
`libs/<lib>/` prefix), and correct the check count to 17.

## Verification

Run against the live worker with the real `CDN_TOKEN` after the fix:

```
PASS no-token manifest -> 401
PASS wrong-token manifest -> 401
PASS authed manifest -> 200
PASS manifest has sonatina-sso
PASS manifest has vsco2-ce
PASS sonatina manifest entries have sha256
PASS vsco2-ce manifest entries have sha256
PASS sonatina-sso file 200
PASS sonatina-sso sha256 matches manifest
PASS vsco2-ce file 200
PASS vsco2-ce sha256 matches manifest
PASS range request -> 206
PASS content-range header correct
PASS plain GET -> 200 not 206
PASS HEAD -> 200
PASS HEAD has content-length
PASS encoded path -> 200 not 404

17 passed, 0 failed
```

This also independently confirms the two worker fixes the package documents
(encoded paths, plain-GET-not-206) are live.
