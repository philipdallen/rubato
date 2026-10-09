# Design docs index — task scaffolds for all phases

**Purpose:** one scaffold per task across W/S/P/C/L/E, scoped and
dependency-linked *before* any design doc is drafted or any issue is filed.
Source of decomposition: [../phase-scoping.md](../phase-scoping.md). Live
plan: [../pipeline.md](../pipeline.md).

## Convention: design docs, not user stories

Supporting artifacts: [../tech-stack.md](../tech-stack.md) (borrow/build
index), [../literature-review-w1.md](../literature-review-w1.md)
(pre-W1 evidence), [../prior-art-spike.md](../prior-art-spike.md)
(component intel).

User-story format ("as a user I want…") suits user-facing features. This
pipeline is backend/infrastructure work — formats, parsers, encoders,
harnesses — so each task gets a **design doc** (a.k.a. tech spec /
engineering design doc): problem, goals/non-goals, dependencies, interfaces,
acceptance criteria. The GitHub issue links the design doc; it does not
embed a narrative.

**Documentation deliverable:** every code task ships a `README.md` in its
tool directory (usage, API, dependencies) and a test spec in `tests/`.
The doc is part of the Definition of Done — code without its doc is
incomplete. Design docs live here; user-facing docs live with the code.

Supporting evidence: [../literature-review-w1.md](../literature-review-w1.md)
(pre-draft lit review for W1/S-series scope), plus
[../prior-art-spike.md](../prior-art-spike.md) (renderer/mockup component
intel), and the rendering research synthesis
[../../RENDERING_RESEARCH_AND_ROADMAP.md](../../RENDERING_RESEARCH_AND_ROADMAP.md)
(what to build next, what is uncertain, and the first controlled experiment).

## Maturity ladder

`scaffold → draft → approved`. All docs start as scaffolds. A doc is
promoted to draft when its upstream dependencies are themselves drafted (or
earlier); draft-of-draft dependency chains are acceptable, final-form
dependencies are deferred to approval. Issues get filed only against
approved drafts.

**One claim per agent at a time.** An agent holds exactly one
`status:claimed` across the tracker; finish (commit + close + unblock
dependents) before claiming the next. Parallel is safe because each agent
respects the rule.

## Dependency matrix

| Task | Doc | Upstream (needs) | Downstream (feeds) | Maturity |
|---|---|---|---|---|
| W1 — Event-stream IR | [w1-event-ir](w1-event-ir.md) | — (corpus sources) | W2, W3, W4, W5 | done (#123/#128) |
| W2 — Corpus loader | [w2-corpus-loader](w2-corpus-loader.md) | W1 | W3, W5 | done (#125) |
| W3 — Pattern analyzer | [w3-pattern-analyzer](w3-pattern-analyzer.md) | W1, W2 | S1–S5, W5, C3 | draft |
| W4 — Diff tool | [w4-diff-tool](w4-diff-tool.md) | W1 | S2, P3, C2, L1 | draft |
| W5 — Visualizer | [w5-visualizer](w5-visualizer.md) | W1 (+W3 overlays) | founder review | draft |
| S1 — Event stream format | [s1-event-stream-format](s1-event-stream-format.md) | W3, W4 | P1, C1–C4, L1 | scaffold |
| S2 — Score encoding | [s2-score-encoding](s2-score-encoding.md) | W3, W4 | P1 | scaffold |
| S3 — Seed format | [s3-seed-format](s3-seed-format.md) | W3 + delta analysis | C1 | scaffold |
| S4 — Language spec | [s4-language-spec](s4-language-spec.md) | W3 | P1 | scaffold |
| S5 — Container + manifest | [s5-container-manifest](s5-container-manifest.md) | — (spec fields) | P1, C4 | scaffold |
| P1 — Reference decoder | [p1-reference-decoder](p1-reference-decoder.md) | S1, S2, S5 | P2, L-series | scaffold |
| P2 — Reference renderer | [p2-reference-renderer](p2-reference-renderer.md) | S1 | P3, L2 | scaffold |
| P3 — Conformance suite | [p3-conformance-suite](p3-conformance-suite.md) | P1, P2 | CI gate | scaffold |
| C1 — Seed format impl. | [c1-seed-format-impl](c1-seed-format-impl.md) | S3 | C2, C3, C4, L1 | scaffold |
| C2 — AI-assisted authoring | [c2-ai-assisted-authoring](c2-ai-assisted-authoring.md) | C1, W1, W4 | feeds seeds | scaffold |
| C3 — Budget calibration | [c3-expression-budget-calibration](c3-expression-budget-calibration.md) | C1 + delta corpora | feeds seeds | scaffold |
| C4 — Assertion authoring | [c4-assertion-authoring](c4-assertion-authoring.md) | C1 | L1 | scaffold |
| L1 — Mockup harness | [l1-mockup-harness](l1-mockup-harness.md) | C1–C4, S1, P2 | L2, L3, L4 | scaffold |
| L2 — Performance renderer | [l2-performance-renderer](l2-performance-renderer.md) | L1, P2 | L3, E1 | scaffold |
| L3 — Model comparison rig | [l3-model-comparison](l3-model-comparison.md) | L1, L2 | E1 | scaffold |
| L4 — Distiller | [l4-distiller](l4-distiller.md) | L1, C1 | E1 | scaffold |
| E1 — The work | [e1-the-work](e1-the-work.md) | L1–L4 | E2, E3 | scaffold |
| E2 — The venue | [e2-the-venue](e2-the-venue.md) | E1 | E3 | draft (#210) |
| E3 — The recording | [e3-the-recording](e3-the-recording.md) | E1, E2 | — | draft (#211; publish blocked on event) |
| W6 — B9 compute scaling | [w6-b9-scaling](w6-b9-scaling.md) | W1, W2, W3 | W3, S-series | scaffold |
| W7 — Mockup schema v0 | [w7-mockup-schema](w7-mockup-schema.md) | W4 + delta + spike | L1 | scaffold |
| C5 — Baroque delta measurement | [c5-baroque-delta](c5-baroque-delta.md) | W4 + corpora | C3, W3 | scaffold |
| L5 — Sample-quality waiver | [l5-sample-waiver](l5-sample-waiver.md) | L2 + spike listener | E1 | scaffold |
| S6 — Vocal text schema | [s6-vocal-text](s6-vocal-text.md) | S1, W1 | S1, v1.0 | scaffold |
| E4 — Extension decision | [e4-extension](e4-extension.md) | founder + S5 | S5, publication | scaffold |

**Critical path:** W1 → W2 → W3(+W6) → S3(+C5) → C1 → C2 → L1(+W7) →
L2(+L5 condition). Everything else is parallel. Promotion order follows the
critical path; W1 is the first draft.
