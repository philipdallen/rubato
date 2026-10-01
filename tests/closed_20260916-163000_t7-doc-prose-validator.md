# Test spec — T7 doc-prose validator (task #299)

Written 2026-09-16 by the completing agent, per TASK_WORKFLOW §6.

## What landed (behavior under test)

`tools/muse_docs/` — an offline, deterministic mechanical doc lint.

- `lint.py`: four finding kinds (plus one for encoding) with the exclusion
  rules that keep the signal honest.
- `cli.py`: `lint` subcommand — `--report` (markdown triage), `--json`,
  `--kind`, `--quiet`; exit 1 when findings exist, 0 when clean.
- `docs/superseded.txt`: the exemption listing (one doc: `SCHEMA_SPEC.md`).
- AGENTS.md gained the **doc-prose checklist** — the prose layer the issue
  asks for (the agent's own verification step, no API).
- Registered in `tools/run_tests.sh` as a fast-tier suite.

Coverage: `tools/muse_docs/tests/test_lint.py` — run with
`cd tools && python3 -m pytest muse_docs -q` (29 tests, sub-second).

## Coverage written

1. **Each check catches its drift class** — `broken-link`, `unresolved-ref`,
   `stale-open-ref`, `unfilled-template`, `encoding` — each proven against a
   synthetic repo in `tmp_path` (the test creates the drift, so it cannot
   pass vacuously).
2. **Depth semantics** — `../FORMAT_SPEC.md` from `docs/design/` resolves;
   `../../FORMAT_SPEC.md` escapes the repo root and is flagged. This is the
   exact class of the three real depth bugs found on landing.
3. **False-positive guards pinned**, one test each:
   - anchors/absolute URLs/mailto are not links to resolve;
   - placeholders, globs and abbreviated lists (`YYYY-MM-DD`,
     `docs/design/e1..e3`, `seeds/x.v1/v2`, `tests/**`) are prose;
   - a command line in backticks truncates to its leading path;
   - a doc-relative backticked path resolves;
   - **historical framing** ("not the earlier `tools/muse_ir/`") is skipped,
     while the same dead path *unframed* is still flagged;
   - a backticked marker (`` `[TODO]` ``) is documentation, not an unfilled
     template.
4. **Exclusions** — `tests/closed_*`, `bugs/open_*`, `blockers/closed_*` and
   `docs/audit/*` are historical and never linted; live docs are not
   excluded; `docs/superseded.txt` exempts a listed doc; the tool's own
   docs are exempt.
5. **De-duplication** — the same reference three times is one finding.
6. **Repo gate** — `test_real_repo_has_no_findings` lints the real tree and
   fails with the full finding list if drift lands. Verified to fail on
   injected drift (appending a broken link to `docs/pipeline.md` fails the
   suite and makes the CLI exit 1; restoring makes both pass).
7. **Determinism** — two scans of the same tree produce identical output.

## Known gaps (acceptable)

- **Prose quality is not machine-checked.** Hollow sentences, unverifiable
  claims, and stale *status words* need the agent checklist (AGENTS.md step
  2–3), by the issue's own constraint: "the agent *is* the checker", no API.
  The lint deliberately stops at mechanically decidable facts.
- **Status claims vs the issue API are not verified.** The issue text
  suggests comparing `**done**` claims against the queue; that needs a
  GitHub call, which the no-spend constraint forbids. The checklist step 3
  covers it by hand. A future task could add an opt-in network mode.
- **Markdown link resolution ignores case** and does not model symlinks.
  No such paths exist in the repo today.
- Findings stay a triaged non-blocking queue: the suite fails so drift
  cannot land silently, and the report format is
  `docs/audit/<date>-doc-prose.md` (seeded at `docs/audit/2026-09-16-doc-prose.md`).

## Closed 2026-09-16 (#299, run=20260916-1525-8d06)

Landed with 29 tests. On landing the lint found **26 real findings in 12
files**, all fixed in the same commit: 10 READMEs linking test specs by
their pre-rename `open_*` name; 3 path-depth errors (`FORMAT_SPEC.md`,
`docs/pipeline.md`, `docs/design/s3-seed-format/SPEC.md`); 1 dead
`docs/audio-convention` reference; and one **non-UTF-8 doc**
(`docs/design/r1-rehearsal-directives.md`, a mangled em-dash from #283).
Repo now lints clean.
## Follow-up coverage landed 2026-09-16 (#311, run=20260916-1525-8d06)

The deferred gaps above were implemented, and writing them up found a real
hole in the linter.

### Found: titled and reference-style links were silently unchecked
The inline pattern could not match `[x](dest "Title")` (nor `[x][label]`
+ `[label]: dest`), so a broken link written in either form linted
**clean** — a hole, not just missing tests. Fixed by replacing the single
regex with `extract_link_targets()`, covering inline, inline+title,
angle-bracketed, and reference-style forms, plus flagging a reference use
with no matching definition. Each form now has a broken-target test; a
naive-pattern revert fails three of them.

### Added
- `tests/test_cli.py` (new, 14 tests): exit codes (clean 0 / findings 1 /
  `--quiet` silent on both), `--kind` filtering, `--json` shape,
  `--report` structure (header, total, kind table, per-file grouping),
  and the budget error on **stderr** with the findings list still on stdout.
- Link-form coverage (parametrized broken-target per form; titled link with
  a real target is clean; missing reference definition is flagged).
- Resolution semantics pinned: relative-to-document, case-sensitive
  (a wrong-case link is flagged — it would 404 on a case-sensitive host),
  symlinks followed.
- `FINDING_BUDGET` (25) with `check_budget()` and `--max-findings`:
  above the ceiling the CLI names the budget on stderr, because a rule that
  suddenly flags hundreds of things is a mis-firing linter, not hundreds of
  defects. `test_repo_corpus_is_far_below_budget` keeps the real tree
  well clear of it.

### Still open (deliberately)
- **Opt-in status-claim mode.** Comparing `**done**` claims against the
  issue queue needs a GitHub call the no-spend constraint forbids by
  default. Unchanged: the AGENTS.md checklist step 3 covers it by hand.
  A future `--check-issues` flag (network, off by default, never in CI)
  would close the last DoD gap — that is a design decision, not a test gap.

Suite: 57 tests (was 29). `muse_docs` still sub-second; fast tier green.
