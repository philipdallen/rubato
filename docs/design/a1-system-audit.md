# A1 — System audit: docs vs. working system (design doc)

**Status: draft, task filed.** A per-module verification pass answering
one question per module: *does the working system do what the
documentation says it does?* Triggered after the 2026-08-25/26 batch
(seven lineage tasks + parallel agent work) — the pace where doc drift
and silently-broken seams accumulate.

## What this is / isn't

An audit **verifies** — it does not fix. Every finding becomes either a
confirms-works entry in the report or a filed issue (bug, doc drift, or
missing test). The audit's output is a report; the issues are the work.

## Module inventory (audit unit = one row)

The audit unit is the *tool directory* (34 under `tools/`), not the
pipeline's task letters — the letters mix sub-tasks, doc-only deliverables,
and cross-cutting work. Four doc-series are *not* tool dirs and are
audited as doc-only rows: E-series (`docs/design/e1..e3`, the publication
docs), the B-series boardroom (`docs/boardroom/` + `docs/design/b*.md`),
the qa_frontend tier (the docs-coherence suite is its own auditor, already
fast-tier), and FORMAT_SPEC-level claims (verified by the conformance
suite P3, #141, not re-checked here).

The remaining **26 audit modules**:

| Series | Modules | Core doc claim to verify |
|---|---|---|
| W (analysis) | ir, corpus_loader, muse_analyze, muse_diff, muse_viz, s1_stream | corpus loads; analyzer produces the report; diff is tick-space correct; golden vectors verify |
| S (format) | muse_seed, muse_roll, muse_mu, muse_ops, muse_seed_cli, assertions | seed validates; roll round-trips; container hashes verify; ops parse; C1 gate works |
| P (player) | muse_decode, muse_play, muse_ci | decoder produces the S1 stream; reference renderer plays; conformance gate passes on golden vectors |
| C (authoring) | muse_budgets, muse_author, muse_assert | budgets calibrate; authoring proposals validate; assertions evaluate |
| L (LLM) | muse_mockup, muse_provider, muse_generate, muse_render, muse_compare, muse_distill, muse_audio | mockup schema validates; providers replay fixtures; generate/validate/fix loop runs; render produces WAV; A/B rig compares; distill extracts |
| Growth/probes | muse_grow, muse_probes, muse_lineage, muse_explorer, muse_event | grow loop iterates; probes compute; lineage walks; workbench data regenerates deterministically |

## Per-module verification method

Each module row is answered with three checks, in order of strength:

1. **Known-answer** — run the module's own gate against a committed
   fixture and diff the output against the pinned expectation (the
   strongest; most modules have one: golden vectors, corpus counts,
   probe JSONs, the v3 lineage chain).
2. **Round-trip** — where no pin exists, run the module end-to-end on a
   small corpus input and verify the output validates against the next
   module's input contract (the seam map already encodes these:
   S2↔S5, S1→P1, mockup→render, seed→C1).
3. **Doc-claim spot-check** — for claims with no executable pin (doc
   tables, status rows, "done" markers), verify the referenced artifact
   exists and the claim is not contradicted by the code (e.g. pipeline
   says X is done → `tools/<x>` exists and its README documents the
   claimed behavior).

Checks 1–2 are executed by running the module's test suite plus a
handful of targeted CLI invocations — **not** by writing new test
infrastructure. Check 3 is a read-and-verify pass.

## Process

- **One module per audit issue**, claimed/closed like any task
  (one claim at a time; the audit is serial work).
- Findings file as: `bug` label (code contradicts docs),
  `documentation` label (docs drift), or a Tests: follow-up (behavior
  works but is unpinned). **Nothing is fixed inside an audit task** —
  the audit's commit is the report row; fixes are their own issues.
- **Auditor independence:** where practical, a module is audited by an
  agent that did not build it. (This batch was heavily co-built by two
  runs; cross-auditing is the norm, not a courtesy.)

## Deliverables

- `docs/audit/<YYYY-MM-DD>-system-audit.md` — one row per module (naming pattern; `<YYYY-MM-DD>` is a placeholder):
  module, doc claim, evidence (command + result), verdict
  (works / broken / drift / unpinned), linked findings.
- The findings issues themselves.
- A pipeline.md row marking the audit complete with the report link.

## Sizing / waves

26 modules is too many for one run and too many to file as 26 issues
up front. File in waves of ~6 (one series per wave), starting with the
modules this batch touched: **Wave 1 = L-series + growth/probes**
(muse_mockup, muse_provider, muse_generate, muse_render, muse_distill,
muse_grow, muse_probes, muse_lineage — the freshest surface, most
likely to have drift). Waves 2–4 (W, S, P+C series) file after Wave 1's
report, informed by what the first pass actually finds.

### Wave 1 split (2026-08-26)

A 12-module single issue (#277) was over the one-agent-run sizing rule —
suites run fast (197 tests, 64s) but the audit's value is per-module
depth: reading each doc claim, running each known-answer gate, verifying
each seam, writing evidence-backed rows. Wave 1 is filed as four
cohesion-grouped tasks:

| Task | Modules | Cohesion |
|---|---|---|
| **A1.1 — Generate loop** | muse_mockup, muse_provider, muse_generate | one functional unit: schema + provider + generate/validate/fix; their docs claim about each other |
| **A1.2 — Render/compare/distill/audio** | muse_render, muse_compare, muse_distill, muse_audio | the post-mockup chain; seams between them are the audit surface |
| **A1.3 — Growth + probes + lineage** | muse_grow, muse_probes, muse_lineage | this batch's core; shared seed/mockup store + the walker |
| **A1.4 — Surfaces** | muse_explorer, muse_event | the read surfaces |

The missing-README findings (muse_explorer, muse_generate, muse_grow,
muse_provider — AGENTS.md's doc-deliverable rule) are findings of
whichever task covers the module, not a separate task: A1.1 picks up
provider/generate, A1.3 grow, A1.4 explorer.

## Explicitly out of scope

- The qa_frontend/docs-coherence suite's own beat (it audits docs vs.
  docs continuously — the audit consumes its output, doesn't duplicate it)
- Performance/cost audits (G4's expansion-time data is the seed of that
  line, not this one)
- The stalled human-input blockers (#211, #224) — those are decisions,
  not verification targets
