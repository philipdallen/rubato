# qa_frontend — Tier 2 headless DOM tests

Playwright + headless Chromium against a local static server. The explorer
page executes for real: the work-list populates, row clicks render detail,
piano-roll images resolve, the fetch-failure fallback shows, and console
errors fail the suite.

## Setup (one-time)

```bash
pip install playwright          # now covered by tools/requirements.test.txt (#238)
python3 -m playwright install chromium
```

The unified runner handles both: `pip` deps come from
tools/requirements.test.txt, and `./tools/run_tests.sh --full` installs
Chromium for the qa_frontend suite automatically (fast tier never touches
the browser).

## Tests

```bash
cd tools/qa_frontend && python3 -m pytest   # full DOM suite, ~65s
```

Registered in `tools/run_tests.sh` as a slow-tier suite (Chromium download
is a one-time environment cost; CI caches it). Live count:
`./tools/run_tests.sh --list`.

## Coverage

- work-list populates (13 rows), per-row parts/notes meta
- row click renders detail (stats grid, pattern table, part names)
- piano-roll `<img>` resolves (naturalWidth > 0)
- back button returns to the list
- fetch failure → visible error fallback (route-aborted JSON)
- zero console errors on load
- data endpoint serves valid JSON
- shared site nav mounts on every surface, markup identical, every route
  resolves 200, and the detail-page revision jump links open their target
  (`test_workbench_nav.py`, slow tier — #304)
- every same-origin link resolves, on disk and over HTTP, plus deep-link
  behavior and boardroom content-page links (`test_site_links.py` — #310)
- every `path#fragment` link finds its anchor on the target page, resolved
  against **rendered** pages so JS-built anchors are covered
  (`test_anchor_fragments.py` — #313)
- every served page fits a six-width sweep (320/375/768/900/1024/1280) with
  the offending element named on failure (`test_mobile_widths.py` — #314)
- the coaching console: the Rehearse pane's committed-directive log, its
  CLI hint, and the audio manifest/players; gaps are pinned as `xfail`
  so a green run that gains an XPASS flags the fix
  (`test_workbench_rehearse.py` — #388, #389)

## Mobile overflow: the shared helper

`tools/qa_frontend/overflow.py` holds `PAGES`, `WIDTHS`, `measure()` and
`assert_no_overflow()`. Three near-identical per-page assertions used to
exist; that fragmentation is why #309 (workbench pages overflowing) shipped —
the pages with pins were clean and nobody added a third.

Adding a surface is now one line in `PAGES`; a registry test fails if the
site grows a page that is not listed. The helper reports *which element*
overflows (skipping elements clipped by a scroll container, which cannot
widen the page), because diagnosing #309 and #314 meant enumerating offenders
by hand.
