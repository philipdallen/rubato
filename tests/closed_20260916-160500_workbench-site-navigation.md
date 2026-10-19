# Test spec — workbench site navigation (task #304)

Written 2026-09-16 by the completing agent, per TASK_WORKFLOW §6.

## What landed (behavior under test)

A persistent cross-page nav (`nav.site-nav`) on the six QA surfaces, with
byte-identical markup on every page and root-relative hrefs so one string
works at any depth; plus per-revision jump links on
`docs/workbench/detail.html` (`#jump`) and a stable anchor id on each
`details.wb-rev` block. Clicking a jump link opens the target revision
before scrolling, so the reader lands on panels, not a one-line summary.

Files: `docs/{index.html,explorer/index.html,workbench/detail.html,
workbench/files.html,workbench/terminal.html,boardroom/index.html}`.
Also fixed in the same commit: six pages linked the removed trailing-slash
route `workbench/terminal/` (404) — now `workbench/terminal.html`, with the
stale route corrected in `docs/design/workbench-terminal-mode.md`.

## Coverage to write

`tools/qa_frontend/tests/test_workbench_nav.py` — slow tier
(`./tools/run_tests.sh --full`, needs Playwright chromium); run alone with
`cd tools && python3 -m pytest qa_frontend/tests/test_workbench_nav.py -q`.

1. **Markup identity (source-scan, fast).** Every surface carries the nav;
   the nav block hashes identically across all six pages (the DoD's "same
   markup on every page", pinned so a divergent copy fails in CI).
2. **Route completeness.** The nav exposes all six routes; no page links
   the removed `workbench/terminal/` route.
3. **No origin coupling.** The nav carries no `http(s)://` URL and no IP
   literal — the #305 failure mode (a hardcoded `127.0.0.1:9145`) must not
   be reintroduced through the nav.
4. **Mount + resolution (DOM).** Every page mounts exactly one
   `nav.site-nav`; each of the six nav targets resolves 200 and serves
   HTML over the static server.
5. **Clickable affordance.** Clicking the Files entry from the detail page
   navigates to `/workbench/files.html` and the nav survives the
   navigation.
6. **Jump-link contract.** One jump link per committed revision, each
   `data-rev` matching an existing `details.wb-rev#id`; anchor ids are
   CSS-selector-safe (a dotted work_id like `bwv227.1` must be slugged or
   a plain `#id` selector cannot resolve it); clicking a link to a
   collapsed revision opens it.
7. **Zero console errors** across index/explorer/detail/boardroom mounts.

## Known gaps (acceptable)

- The nav is duplicated markup by design (a shared static site has no
  include mechanism and no build step). The hash pin is what keeps the
  copies honest; a future build step would replace it with a real include.
- Mobile overflow on the workbench pages is pre-existing and out of scope
  here — logged as `bugs/open_20260916-160200_workbench-mobile-overflow.md`
  and filed #309. The nav itself adds 0px (it wraps), verified by stashing
  the `docs/` changes and re-measuring.
- `boardroom/deck.html` is a full-screen slide deck and keeps its own
  chrome (per the existing B1 scaffold contract, which pins nav on the
  boardroom landing only); the deck's cross-links were still corrected to
  the real terminal route.

---

**Closed 2026-10-19** (issue #418 reconciliation, run=20261019-0741-2g2w): the owning task **#304** is closed as completed; the seven-point coverage it calls for landed in `tools/qa_frontend/tests/test_workbench_nav.py` (present, slow tier). No open `Tests:` issue remains.
