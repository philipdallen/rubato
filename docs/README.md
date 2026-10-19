# Docs index — read in this order

This directory holds ~40 prose docs. They are not a flat pile: read them by
phase, or jump to the load-bearing four. The live work plan is
[pipeline.md](pipeline.md); the issue queue and `git log origin/main` are the
system of record, and status tables in these docs are caches that may lag.

## Start here — the load-bearing four

These four carry the format and its reasoning. Everything else elaborates or
records them.

| Doc | What it fixes |
|---|---|
| [../FORMAT_SPEC.md](../FORMAT_SPEC.md) | The `.ru`/`.mu` format: score encoding, language, container, manifest. The platform the rest is built on. |
| [../SCHEMA_SPEC.md](../SCHEMA_SPEC.md) | Schema definitions. Design history only — superseded, retained for the reasoning (see [superseded.txt](superseded.txt)). |
| [decision-log.md](decision-log.md) | ADR-style index of locked and open decisions (D1–D…), each with its source. |
| [../PRIOR_ART_REVIEW.md](../PRIOR_ART_REVIEW.md) | The prior-art review the design borrows from and argues against. |

Then: [../README.md](../README.md) for the product, and
[../AGENTS.md](../AGENTS.md) for conventions.

## By phase

The build plan is [pipeline.md](pipeline.md); each phase below lists the docs
that support it.

**Phase 0 — analysis workbench (tools that teach)**
- [vision.md](vision.md) — product vision (revised 2026-08-23).
- [phase-scoping.md](phase-scoping.md) — scope of every remaining phase.
- [analysis-report.md](analysis-report.md) — W3 full-corpus pattern analysis (Phase 0 evidence).
- [literature-review-w1.md](literature-review-w1.md) — pre-drafting evidence for W/S-series.
- [prior-art-spike.md](prior-art-spike.md) — component intel for the spike.
- [spike.md](spike.md) — the mockup proof (D9: mockup is dense DNA, not sketches).
- [checkpoint-egg-model.md](checkpoint-egg-model.md) — architecture settled; subtraction method (D8).

**Phase 1 — format spec v1.0**
- [../FORMAT_SPEC.md](../FORMAT_SPEC.md) — the spec itself.
- [design/](design/) — one design doc per task (S/W/C/L/P/E series), indexed by [design/index.md](design/index.md).

**Phase 2 — deterministic player (the baseline)**
- [design/p1-reference-decoder.md](design/p1-reference-decoder.md), [design/p2-reference-renderer.md](design/p2-reference-renderer.md), [design/p3-conformance-suite.md](design/p3-conformance-suite.md).
- [chain-report.md](chain-report.md) — E2E harness output (parse → pack → container → decode → verify → render).

**Phase 3 — seed authoring (the craft, proprietary)**
- [seed-iteration.md](seed-iteration.md) — how to iterate on a seed.
- [delta-analysis-plan.md](delta-analysis-plan.md) — the delta-analysis data problem.

**Phase 4 — mockup harness + renderer (the product)**
- [design/l1-mockup-harness.md](design/l1-mockup-harness.md) and the L-series design docs.
- [rr1-seed-coaching-abc.md](rr1-seed-coaching-abc.md) — seed-level coaching A/B/C experiment.

**Phase 5 — the event (the unveiling)**
- [design/e3-the-recording.md](design/e3-the-recording.md) — the recording plan (publication blocked).

## Reference and process

| Doc | What it is |
|---|---|
| [tech-stack.md](tech-stack.md) | Borrow/build index — what Rubato uses vs. builds. |
| [podcast-source.md](podcast-source.md) | System overview written for an outside reader. |
| [lit-review-drift.md](lit-review-drift.md) | Timed check that the work is converging with research. |
| [integration-testing-scope.md](integration-testing-scope.md) | Integration-testing scope (snapshot, 2026-08-23). |
| [ci-retry.md](ci-retry.md) | Manual re-run of transient CI failures. |
| [AUDITOR.md](AUDITOR.md) | The daily repo health/drift automation. |
| [HUB_STATUS_LOG.md](HUB_STATUS_LOG.md) | The append-only `status_log.jsonl` snapshot format. |
| [../TASK_WORKFLOW.md](../TASK_WORKFLOW.md) | Multi-agent task coordination (claim, done, blockers). |
| [../SECURITY.md](../SECURITY.md) | Security posture. |

## Evidence and records

- [audit/](audit/) — dated audit records (system audits, doc-prose, tier-2 baseline). Historical: state at the time written.
- [design/](design/) — per-task design docs; see [design/index.md](design/index.md) for the task→doc map.
- [audio/](audio/) — rendered audio artifacts and their manifest.
- [boardroom/](boardroom/), [explorer/](explorer/), [spike/](spike/), [workbench/](workbench/) — generated HTML/wav artifacts, not prose docs.
