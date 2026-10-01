# Task — Rename completed test specs from `open_*` to `closed_*`

**Repo:** philipdallen/rubato
**Filed:** 2026-10-01T12:00:00Z by openhands `run=20261001-1200-rlm1`
**Directive:** D22 (`docs/decisions/LOG.md`)
**Labels:** status:available, kind:hygiene

## Finding

Several test specs under `tests/` have been completed — they carry a `Closed` or `Retired` section — but the file is still named `open_*`. `TASK_WORKFLOW.md` §6 uses the `open_*`/`closed_*` name as the state marker, and the doc-prose lint excludes `tests/closed_*` as historical, so a completed spec left `open_*` is both mislabelled and linted as if live.

## Evidence (verified against raw files)

- Completed but still `open_*`: `tests/open_20260824-003200_frontend-qa-tier3.md` (RETIRED), `open_20260916-170000_terminal-runner-reachability.md` (Closed), `open_20260916-171500_nav-coverage-and-site-links.md` (Closed), `open_20260916-173000_workbench-mobile-overflow.md` (Closed), `open_20260916-190000_w6-b9-compute-scaling.md` (Closed), `open_20260916-163000_t7-doc-prose-validator.md` (Closed).
- `rubato/TASK_WORKFLOW.md` §6: the spec file is part of the Definition of Done; blockers are renamed `closed_*` on resolution (same convention).
- `tools/muse_docs/lint.py` excludes `tests/closed_*` and `bugs/open_*` as historical.

## Fix

Rename each completed spec from `open_*` to `closed_*` (git mv, one commit), leaving the body unchanged. Confirm each file's own `Closed`/`Retired` section first so an actually-open spec is not renamed.

## Verification

No `tests/open_*` file contains a `## Closed` or `## Retired` heading; `python3 tools/muse_docs/cli.py lint` still exits 0.

## Out of scope / do not re-derive

Do not change spec contents or close any issue. This is a rename of files whose state marker already disagrees with their name.

---
Filed from the RLM Analyzer triage pass. Filing policy: D22 in `docs/decisions/LOG.md`; consolidated record in `philipdallen/portfolio-ops` (`RLM_TRIAGE_2026-10-01.md`, branch `tasks/rlm-triage-2026-10-01`).

Directive: D22
