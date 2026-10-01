# Test spec — workbench nav coverage gaps + site link integrity (#310)

Written 2026-09-16 by the completing agent, per TASK_WORKFLOW §6.

## What landed (behavior under test)

The five gaps #310 opened after #304. Two were real bugs, found while
writing the coverage the issue asked for:

1. **Site-wide link integrity** (the highest-value item). Every same-origin
   href on every served page must resolve, at the filesystem and over HTTP.
   The general form of the `workbench/terminal/` 404 that #304 fixed by hand.
2. **Deep links were dead.** `#rev-<work>-v3` did not open or scroll to its
   revision: the rows render asynchronously, so the browser's own anchor
   scroll fires before the target exists, and a collapsed `<details>` cannot
   be scrolled to. Fixed by applying the hash after render
   (`applyHashTarget()`), plus a `hashchange` listener.
3. **Corpus-tree links pointed at nothing.** `docs/index.html` linked
   `workbench/detail.html#<fid>` (e.g. `#bwv227.1`), and no such element
   existed — 12 of 13 rows were dead. The page now carries a per-work
   anchor (`work-<slug>`) and the tree links to it; unseeded rows link to the
   file viewer, which is where their content actually is.
4. **Nav survives the era-filter re-render** (regression pin on placement).
5. **`files.html` nav grid row** does not overlap the tree/main panes at
   desktop or mobile width.

Files: `docs/workbench/detail.html`, `docs/index.html`,
`tools/qa_frontend/tests/test_site_links.py` (new),
`tools/qa_frontend/tests/test_corpus_tree_dom.py` (updated contract).

## Coverage written

`test_site_links.py` — 11 tests, slow tier:
- every same-origin href resolves on disk, and >40 links are checked (so a
  broken scan cannot pass as "clean");
- every same-origin href serves HTTP 200;
- nav survives the era re-render (nav + jump bar intact across all three eras);
- `#rev-…` deep link opens its revision **and** scrolls to it;
- `#work-…` deep link reveals that work;
- each boardroom content page's links resolve (parametrized, 5 pages);
- `files.html` nav does not overlap the tree/main panes at 1280px and 375px.

`test_corpus_tree_dom.py` — 2 tests rewritten/added: rows link to slugged
anchors with no dots, and every row anchor exists on the live detail page.

## Deliberate exemptions (guarded, not silent)

- `/audio/*.wav` — rendered audio is session-local by convention (gitignored,
  regenerated on demand; `docs/audio/README.md`). `test_audio_wav_exemption_is_real`
  asserts a `.wav` link still exists *and* that the convention doc still
  states the rule, so the exemption cannot quietly outlive its justification.
- Template-literal hrefs (`href="${anchor}"`) — a static scan cannot evaluate
  them; those are covered by the DOM-level corpus-tree tests instead.

## Verification that the pins are not vacuous

Re-injecting the original defect (`workbench/terminal.html` →
`workbench/terminal/`) fails both sweep tests. Re-injecting the dead corpus-tree
anchor form fails the corpus-tree contract test.

## Known gaps (acceptable)

- Broken **external** URLs are not checked (no network by design; the repo's
  no-spend constraint).
- `docs/spike/index.html` links are covered by the sweep but its listener
  page has no dedicated DOM test.
- Anchor *targets* are verified only for the corpus tree and the detail page;
  a generic "every `#fragment` on every page resolves" check would be the
  next increment.

## Closed 2026-09-16 (#310, run=20260916-1525-8d06)

17 new/updated tests. `qa_frontend` 141 passed / 5 skipped (was 128/5);
fast tier all 35 suites green; `muse_docs` lint 0 findings.
## Follow-up coverage landed 2026-09-16 (#313, run=20260916-1525-8d06)

### The fragment gap, closed
The item-1 gap was the one that mattered: the sweep checked link *paths*, so
#310 bug 2 (corpus-tree anchors matching no element) got through — every href
resolved to a real file while the fragment went nowhere. The new
`test_anchor_fragments.py` resolves fragments against **rendered** pages, so
runtime-built anchors are covered; a static scan cannot see those. Re-injecting
the #310 bug fails it plus two sibling tests.

### Added (7 tests)
- Every rendered `path#fragment` link finds its anchor on the target page.
- The corpus-tree deep-link contract end to end (navigate, then assert the
  element exists).
- `slug()` drift guard: the two implementations are extracted and compared,
  since divergence breaks deep links silently.
- Every rendered anchor id is CSS-selector-safe.
- A jump link still opens its target after an era-filter re-render (#310
  pinned the nav surviving, not the click).
- The spike listener mounts and lists artifacts (it had no DOM test).

### Still open (deliberately)
- **External links** — no network by design; unchanged.
- **Generic fragment checking on non-rendered pages** — the parametrization
  covers the two JS-anchor pages; extending to every page is cheap but those
  pages' fragments are static and already swept.

Suite: qa_frontend 157 passed / 5 skipped (was 150/5).
