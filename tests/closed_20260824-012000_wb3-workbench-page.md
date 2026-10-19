# Test spec — W-B3 seed workbench page

**Task:** #187 (W-B3 — Seed workbench page)
**Written:** 2026-08-24

## What to verify

1. **Page structure**
   - `docs/workbench/index.html` exists; loads `data/seeds/index.json`
   - Per-seed: seed panel (params + philosophy) + probe panel (per-probe status)
   - Empty-state message when no seeds committed

2. **Probe artifact**
   - `data/seeds/bwv227.1.probes.json` exists; `ok: true`
   - Deterministic: re-running probes CLI yields identical JSON

3. **DOM mount safety**
   - Panels render for the committed seed; no JS exceptions on load
     (headless check)

## How to run

```bash
python3 tools/muse_probes/cli.py seeds/bwv227.1.seed.yaml --work corpus/bach/bwv227.1.mxl \
    > docs/workbench/data/seeds/bwv227.1.probes.json
# serve: python3 -m http.server -d docs/workbench 8000
```

## Addendum 2026-08-24 (#229, run=20260824-1107-409b)

- **Routes:** the page lives at `docs/workbench/detail.html` (W-B6 rename);
  `test_workbench_routes.py` pins the contract. `/workbench/` bare serves a
  redirect shell → detail.html (restored by #227).
- **Era filter is decorative for verdicts today:** the select re-renders
  but probe rows come from the committed artifact (computed at
  era=baroque). Per-era budget verdicts need page-side recompute +
  per-era budget data — pinned as current behavior in
  test_workbench_dod.py::test_era_filter_verdicts_are_artifact_driven_today;
  flip it when the recompute lands.

---

**Closed 2026-10-19** (issue #418 reconciliation, run=20261019-0741-2g2w): the owning task **#187** is closed as completed; its page/route coverage landed in `tools/qa_frontend/tests/test_workbench_dod.py` and `test_workbench_routes.py` (per addendum above). No open `Tests:` issue remains.
