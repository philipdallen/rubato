# Frontend QA — design doc scaffold

**Phase 2.5 — integration. Status: scaffold (awaiting sign-off).**

How the explorer (and any future static frontend) gets tested so agents can
QA the page themselves. Three tiers, ordered cheap → real.

## Tier 1 — Static contract (already landed, #164)

What exists: `tools/muse_explorer/tests/test_explorer.py` — artifact
contract (fields, registry coverage, determinism, freshness tripwire) and
DOM mount safety (noindex, fetch fallback, no external resources). This
catches data drift and missing-artifact bugs, but **never executes the
page**. Gap: the page's JS could be broken and Tier 1 still passes.

## Tier 2 — Headless DOM tests (proposed)

Run the page in a real browser engine (headless Chromium via Playwright)
and assert the rendered DOM:

- Page loads `index.html` from a local static server; `work-list` populates
  with 13 rows (fetch of `data/works.json` succeeds).
- Clicking a row renders the detail view: title, stats grid, part names,
  pattern table, piano-roll `<img>` that resolves (naturalWidth > 0).
- Back button returns to the list.
- Failure fallback: kill the JSON endpoint → page shows the error message
  instead of hanging on a blank screen.
- Console error capture: page must produce zero console errors on load.

Implementation: `tools/qa_frontend/` with a Playwright runner. Chromium
download (~150 MB) is a one-time environment cost; CI caches it. Runs in
the unified runner as a new suite. ~10–15 tests, all headless, no network
beyond localhost.

## Tier 3 — Live deploy smoke (RETIRED 2026-09-16)

> **Retired.** The Netlify QA site is gone: netlify.toml, the Tier 3 spec
> and the live-smoke test were removed, and the site's builds were stopped at
> the API level. There is no hosted deploy of `docs/` any more, so there is
> nothing for a post-deploy smoke to poll.
>
> Why retired rather than suspended: the deploy was never a QA dependency
> that paid for itself. It existed to publish `docs/` so a human could look
> at it, and it cost builds on every push to `dev` while a repo comment
> claimed it was paused (see the session note below). Tier 2 already executes
> every page; a deploy adds hosting cost without adding a distinct check.
>
> **What replaced it:** the Tier 2 suite now *is* the whole frontend QA path,
> and it got stronger in the process — every served page is exercised, not
> just the explorer:
> - `test_site_links.py` — every same-origin link resolves, on disk and over
>   HTTP (#310)
> - `test_anchor_fragments.py` — every `#fragment` resolves against rendered
>   pages, so JS-built anchors are covered (#313)
> - `test_mobile_widths.py` — every served page fits a six-width sweep (#314)
>
> The gap Tier 3 was meant to close — "is the live site broken right now?" —
> no longer applies, because there is no live site. If a hosted preview is
> ever wanted again, stand it up deliberately on a dedicated branch and add
> the smoke then; do not infer it from this doc.

## What "QA myself" means concretely

| Question | Tier that answers it |
|---|---|
| Is the data fresh/complete? | 1 (landed) |
| Does the page actually render and interact? | 2 |
| Is the live site broken right now? | n/a — no hosted deploy (Tier 3 retired 2026-09-16) |

## Open questions (draft-level)

- Playwright (Node, mature) vs Selenium (heavier)? Recommend Playwright.
- ~~Live smoke cadence~~ — moot: Tier 3 retired (no hosted deploy).
- Should Tier 2 run against the committed artifacts or regenerate first?
  (Committed — regeneration is Tier 1's freshness tripwire.)

## Acceptance criteria

- An agent can run one command and know the page renders, clicks work,
  links resolve and every surface fits — without a human opening a browser.
  (A hosted-deploy check was dropped with Tier 3; see above.)
