# Blocker: muse_cdn worker redeploy needs a Cloudflare API token the run does not have

- **Task:** #425 (ops(muse_cdn): redeploy the worker so the live build matches main)
- **Filed:** 2026-10-19T22:05Z, run=20261019-2202-8mhz
- **Status:** `status:blocked-needs-input` on #425

## What was attempted

Claimed #425 and measured the state the issue describes, then measured whether
the deploy was possible from this run's environment.

**The premise holds — the live worker is stale.** The repo source gates the
manifest route to GET/HEAD only (`tools/muse_cdn/worker/src/index.js:97-98`,
`131-132`: a non-GET/HEAD method returns `405 method not allowed`). Against the
live endpoint the gate is absent:

```
POST /manifest.json -> 200     # repo source would return 405
GET  /manifest.json -> 200
```

So the deployed script predates the method gate, exactly as the issue says.

**The deploy cannot be performed here.** The Cloudflare API token required for
the worker-script PUT is not present in this run's environment:

- `api.cloudflare.com` is reachable (unauthenticated `GET /client/v4/user` ->
  `403`), so this is a credential gap, not a network gap.
- The deploy PUT returns `HTTP 400` with
  `{"errors":[{"code":9106,"message":"Missing X-Auth-Key, X-Auth-Email or Authorization headers"}]}`
  — the request went out with no usable credential.
- No token-bearing variable is set: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_TOKEN`,
  `CF_API_TOKEN`, `CLOUDFLARE_API_KEY`, `CF_API_KEY` are all empty/unset.
- The run's secret store is empty: `GET /api/settings/secrets` ->
  `{"secrets": []}`.
- No CI workflow deploys the worker (`.github/workflows/` has no Cloudflare or
  R2 step), and no GitHub secret carries one.
- The repo's own docs say the token lives outside the package:
  `RUNBOOK.md` §Credentials — "It is in the secure vault, **not** in this
  package."

`RUBATO_CDN_TOKEN` *is* set in this run, but it is the worker's own bearer token
(`CDN_TOKEN`), not the Cloudflare management credential. It authenticates
requests *to* the CDN; it cannot deploy to the Cloudflare API. The issue body
anticipates exactly this case: "If the Cloudflare API token is unavailable in
the run's environment, record that as the blocker and stop — do not attempt a
partial deploy."

## What is missing (the decision for the human)

The Cloudflare API token with *Account → Workers R2 Storage: Edit* and
*Workers Scripts: Edit* must be provisioned into the automation environment
(or the deploy run by a human / from the Muse environment where the connector
helper resolves the placeholder). Nothing else about #425 is unresolved.

## Notes

- No partial deploy was attempted. The live worker was left untouched.
- The issue's other measurement (the worker test harness) was not run: the
  `POST -> 405` gate check is the decisive one for "is the live build stale",
  and it already shows the redeploy is needed and impossible from here.
- `RUNBOOK.md` §4 already carries the exact deploy sequence; no doc change is
  needed — only the credential.
