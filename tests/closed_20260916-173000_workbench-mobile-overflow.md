# Test spec — workbench mobile overflow fix (#309)

Written 2026-09-16 by the completing agent, per TASK_WORKFLOW §6.

## What landed (behavior under test)

At 375px the workbench pages scrolled horizontally: `detail.html` by 197px,
`terminal.html` by 5px. Root cause, measured on the page: grid/flex items
default to `min-width: auto`, so the wide `<pre>` seed/probe dumps set the
column width instead of scrolling inside it; the terminal's prompt row did
not wrap, so its `--help` button overran by 5px.

Fix (CSS only, no markup or behavior change):

- `detail.html`: `.panel > * { min-width: 0 }`, `.work { min-width: 0 }`,
  `.card { min-width: 0 }`, `pre { max-width: 100% }`.
- `terminal.html`: `.prompt { flex-wrap: wrap }`,
  `.prompt input { flex: 1 1 12rem; min-width: 0 }`.

Coverage: `tools/qa_frontend/tests/test_workbench_dod.py` — 4 new tests
(3 parametrized width checks + 1 readability check), slow tier.

## Coverage written

1. **No horizontal overflow at 375px** on `/workbench/detail.html`,
   `/workbench/terminal.html`, `/workbench/files.html` — the regression pin,
   mirroring the existing sibling-page checks
   (`test_pipeline_table_no_mobile_overflow` for `/index.html`,
   `test_mobile_no_horizontal_overflow` for `/explorer/`). Those two pages
   were already clean; the workbench pages had no such pin, which is why the
   overflow survived.
2. **Content does not collapse when the width is constrained.** The probe
   card's `bounding_box().width` must be `<= 375` and its text must still
   contain the probe rows — i.e. the `<pre>` blocks scroll *inside* the card
   rather than the card being clipped away. A pure overflow assertion could
   be satisfied by hiding content; this one cannot.

## Verification that the pins are not vacuous

Reverting the four CSS properties fails `test_workbench_pages_fit_mobile_width
[/workbench/detail.html]` and `test_detail_panels_remain_readable_at_mobile`.
Restoring passes.

Measured across all six surfaces at 375px and 1280px after the fix: overflow
is 0 everywhere (index, explorer, detail, files, terminal, boardroom).

## Known gaps (acceptable)

- **Only 375px and 1280px are pinned.** The `.panel` breakpoint is 900px; the
  range between 376–899px is not swept. A parametrized width sweep (e.g.
  320/375/768/1024/1280) would catch a regression in the single-column band,
  and 320px (iPhone SE) is not asserted at all.
- **Other pages' mobile widths are still unpinned** beyond the two sibling
  pages: `files.html` is covered by this change, but the boardroom content
  pages and `docs/spike/index.html` have no width pin.
- **Vertical/zoom behaviour** (e.g. 200% text zoom) is not checked; the
  overflow check uses viewport width only.

## Closed 2026-09-16 (#309, run=20260916-1525-8d06)

Bug log `bugs/open_20260916-160200_workbench-mobile-overflow.md` renamed
`closed_`. `qa_frontend` 145 passed / 5 skipped (was 141/5); fast tier all 35
suites green; `muse_docs` doc-prose lint 0 findings.
## Follow-up coverage landed 2026-09-16 (#314, run=20260916-1525-8d06)

### The sweep found three more overflowing pages
The issue asked for a width sweep and the remaining surfaces. Doing it found
breakage no existing pin covered — including one at 375px, the very width the
sibling pins used:

| Page | 320px | 375px | cause |
|---|---|---|---|
| /boardroom/competitive.html | 99px | 44px | width-constrained **and** an unbreakable token |
| /boardroom/status.html | 32px | 0 | table with no scroll container |
| /spike/index.html | 10px | 0 | verdict button row did not wrap |

Fixes were CSS-only: `.table-scroll` wrappers (the pattern
`docs/index.html` already used for `.pipeline`), `overflow-wrap: anywhere`
on text containers, and `flex-wrap` on the spike button row. The 19px
residual on competitive.html survived every table-specific fix — it was a
single unbreakable token in a list item.

### Consolidated (the fragmentation that let #309 happen)
`tools/qa_frontend/overflow.py` now owns `PAGES`, `WIDTHS`, `measure()`
and `assert_no_overflow()`. Adding a surface is one line, and
`test_pages_registry_covers_every_served_page` fails when the site grows a
page that is not listed — so a new surface cannot ship unpinned again. The
three original per-page assertions remain as named regressions with pointers
to the general form.

`WIDTHS` is a six-point sweep (320/375/768/900/1024/1280). The workbench
`.panel` breakpoint is 900px, so 376-899 was previously unswept and 320px
was unasserted.

### Self-diagnosing failures
The helper names the offending element (tag, id, class, geometry), skipping
anything clipped by a scroll container. That guard is not cosmetic: my own
first diagnosis of competitive.html was misled by a table reported as an
offender when it was safely clipped by `.table-scroll` — the same false lead
the helper now prevents, pinned by `test_clipped_elements_are_not_blamed`.

### Still open (deliberately)
- **Zoom / text scaling** — a distinct failure mode from viewport width;
  unchecked (recorded, not silently skipped).

Suite: qa_frontend 176 passed / 5 skipped (was 157/5).
