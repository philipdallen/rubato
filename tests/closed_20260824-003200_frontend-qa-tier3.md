# [RETIRED 2026-09-16] Test spec — Frontend QA Tier 3 (task #184)

Written 2026-08-24 by the completing agent, per TASK_WORKFLOW §6.
Code under test: `tools/qa_frontend/tests/test_live_smoke.py` +
`.github/workflows/live-smoke.yml`.

## How to invoke

```bash
QA_LIVE=1 python3 -m pytest tools/qa_frontend/tests/test_live_smoke.py -q
```

## Coverage landed with the task

- **/explorer/ 200** on the live dev-- deploy
- **data/works.json** valid, 13 works, pinned fields present
- **piano-roll PNG** 200 with content length
- **zero console errors** headlessly on the live page
- **live interaction** (click through to detail and back)
- Local runs skip by default (QA_LIVE=1 gate); CI runs on a 6-hour
  schedule + workflow_dispatch.

## Cadence decision (documented per issue)

On-deploy polling via the Netlify status API was the alternative; the
6-hour schedule is the simpler, hook-free floor that still catches a
broken deploy within a workday. An on-deploy trigger can be added later
via Netlify's outgoing webhook → GitHub repository_dispatch.

## Behaviors still needing coverage (follow-up)

- **Deploy-triggered run** — schedule → webhook-driven (above).
- **Failure notification** — a failing live smoke currently fails the CI
  job silently; a Slack/issue notification is the escalation path.
- **Spike listener smoke** — /spike/ shares the deploy; its audio assets
  get the same treatment when P2 lands.


## Retired 2026-09-16 (run=20260916-1525-8d06)

Tier 3 is retired, not deferred: the hosted preview is gone. Removed with it —
`netlify.toml`, `tools/qa_frontend/tests/test_live_smoke.py`, and the site's
builds (stopped at the Netlify API). The Netlify `--allow-origin` guidance and
the deploy-trigger path (`repository_dispatch`) are gone too.

Why retired rather than resumed: the deploy only published `docs/` for a human
to look at. It cost builds on every push to `dev` while `netlify.toml` claimed
the site was paused — measured: ten pushes, ten deploys, `context=production`.
Tier 2 already executes every served page, so the deploy added hosting cost
without adding a distinct check.

What covers this spec's intent now (`tools/qa_frontend/tests/`):
- `test_site_links.py` — every same-origin link resolves, on disk and over HTTP
- `test_anchor_fragments.py` — every `#fragment` resolves against rendered pages
- `test_mobile_widths.py` — every served page fits a six-width sweep

This file is kept as the design record of what Tier 3 would have been; see
`docs/design/frontend-qa.md` §Tier 3 for the current statement.

The `Tests:` issue (#224) is closed as retired — see the closing comment.
