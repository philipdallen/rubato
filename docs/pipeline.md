# Muse build pipeline — work plan and status

The single source of truth for what gets built, in what order, and where it
stands. One task = one GitHub issue, per [TASK_WORKFLOW.md](../TASK_WORKFLOW.md).
Status column is updated by the docs-coherence sweep duty.

## Locked decisions

- **Three-component format.** `.mu` = score (fixed work, our MusicXML) +
  prompt (interpretive space) + plaintext rights manifest. Zip container.
- **MusicXML is the existing roll.** The compressor adapts it; we are not in
  the business of scanning historic documents.
- **The deterministic player is the baseline** — "our MIDI player," free,
  proves the format. **The LLM player is the product** — the musician.
- **The seed workbench and LLM player are proprietary.** The open surface is
  the score side: encoding (S2), the deterministic player (P-series), the
  spec. Proprietary: seed authoring (C-series), LLM player (L-series). Spec +
  reference player go public at launch; split at pre-launch.
- **Tools before spec freeze.** The analyzer teaches us what the language
  needs; the diff tool teaches us whether compression works. Spec v1.0 is
  written from evidence, not ahead of it.
- **The corpus is the ratchet.** Bach → Byrd → Schubert → Beethoven 5 →
  Beethoven 9. Each rung gates the next; the Ninth is the v1.0 target.
- **No model training in the product path.** The LLM conductor is a stock,
  swappable model steered by prompt alone (seed + score + instructions).
  Delta analysis (score↔performance datasets) produces design knowledge —
  mockup schema fields, seed budgets, prompt vocabulary — never training
  data. Fine-tuning is an explicit escape hatch (plan B), not the plan.
  The intelligence migrates into the format, not the model.

## Phase 0 — Analysis workbench (tools that teach)

| Task | What it is | Status |
|---|---|---|
| W1 — Event-stream IR | Canonical in-memory event format all tools share: notes (pitch/onset/duration/velocity), tempo map, meter, key, dynamics, parts. Parsers: MusicXML in, MIDI in. | **done** (#123 + review follow-up #128 → [tools/ir](../tools/ir/)) |
| W2 — Corpus loader | Loads every [corpus/](../corpus/) file into the IR. Known-answer tests: note counts, part counts per source README. | **done (#125)** |
| W3 — Analyzer | Pattern detector over the IR: exact repeats, transposed repeats, sequences, mirror/retrograde candidates, ostinati. Outputs per-work statistics + pattern inventory. | **done #131** (tools/muse_analyze/, docs/analysis-report.md) |
| W4 — Diff tool | Event stream ↔ event stream: recall/precision in tick space. The ground truth for every compression claim. | **done #126** (tools/muse_diff/) |
| W5 — Visualizer | Piano-roll plots with pattern overlays. Human evaluation aid — the founder reviews what the analyzer claims. | **done #127** (tools/muse_viz/) |

**Phase 0 done when:** the analyzer has run across all five works and produced
a pattern-frequency report that drives Phase 1 language decisions.

## Phase 1 — Format spec v1.0 (from evidence)

| Task | What it is | Status |
|---|---|---|
| S1 — Event stream format | The decoder↔renderer contract: binary layout, tick resolution, dynamics curves. | **done** (#137 → [FORMAT_SPEC](../FORMAT_SPEC.md) §4 + [tools/s1_stream](../tools/s1_stream/)) |
| S2 — Roll encoding | How the fixed score is packed: columnar, delta-encoded, entropy-coded. | **done (#138 → FORMAT_SPEC §4.6 + [tools/muse_roll](../tools/muse_roll/))** |
| S3 — Seed encoding | Interpretive parameters, sanctioned ranges, performance philosophy fields. | **decomposed #139 → S3.1–S3.6 (#142–#147), all done**; S3.7 lineage fields filed [#248](https://github.com/philipdallen/rubato/issues/248), S3.8a chain-walk filed [#251](https://github.com/philipdallen/rubato/issues/251), S3.8b mockup persistence [#254](https://github.com/philipdallen/rubato/issues/254) ([proposal](design/proposal-lineage-chain.md)) |
| S4 — Language spec | The executable layer: operators (transpose/invert/retro/aug/dim), control flow, assertions. Informed by W3's pattern report. | **done (#140 → FORMAT_SPEC §5.1 + [tools/muse_ops](../tools/muse_ops/))** |
| S5 — Container + manifest | Zip layout, plaintext rights manifest, content hashes, signature. | **done (#141 → FORMAT_SPEC §7.1 + [tools/muse_mu](../tools/muse_mu/))**; S5.1 manifest lineage fields filed [#249](https://github.com/philipdallen/rubato/issues/249) |

**Phase 1 done when:** FORMAT_SPEC.md v1.0 is written, with every construct
justified by Phase 0 evidence (a construct without corpus evidence doesn't ship).

**What "losslessly" means here — stated, not implied (amended 2026-09-16,
S6/#318).** The chain proves **IR → `.mu` → IR**: it parses the source into
the IR, packs from the IR, and verifies the decoded stream against that IR.
It does not re-read the source XML/MIDI and compare. So the gate holds over
what the IR carries, and its strength is bounded by parser coverage — a field
the parser never reads cannot fail the check.

That gap was real and is now closed for the one case that mattered: the
Ninth's 3,588 `<lyric>` elements were outside the IR entirely (#318), so
"source lossless" was unprovable for the v1.0 target. Vocal text now
round-trips (3,587 lyrics + 405 melismas) and is part of the canonical
comparison the chain diffs on, so a dropped lyric **fails** the chain.

Treat parser coverage as part of this gate: when a new source construct is
found, ask whether the IR reads it, not only whether the chain is green.

The one **known remaining instance** of that caveat is MIDI vocal text:
MIDI lyric meta events (`0x05`) are not read. The corpus's MIDI sources
(Byrd) are untexted, so there is no evidence to drive the behaviour and
guessing it would violate "a construct without corpus evidence doesn't
ship". The decision is recorded, not silently deferred — a texted MIDI
source loads with no lyric but does **warn** that the lyric events were
dropped (`Work.meta.warnings`), and `tools/ir/tests/test_vocal_text.py`
pins that state so it is visible as a loud choice rather than a silent
loss. When a texted MIDI source arrives, parsing plus a round-trip pin is
the follow-up, and that test is the one to invert.

## Phase 2 — Deterministic player (the baseline)

| Task | What it is | Status |
|---|---|---|
| P1 — Reference decoder | `.mu` roll stream → event stream. Deterministic, sandboxed, resource-bounded. | **done** (#197 → [tools/muse_decode](../tools/muse_decode/)) |
| P2 — Reference renderer | Event stream → audio (soundfont tier). CLI: `muse play file.mu`. | **done** (#198 → [tools/muse_play](../tools/muse_play/)) |
| P3 — Conformance suite | Golden vectors: `.mu` → event-stream pairs. CI gate. | **done** (#212 → [tools/muse_ci](../tools/muse_ci/)) |

**Phase 2 done when:** every corpus `.mu` round-trips through the player and
the diff tool confirms the score reconstructs the source losslessly.

## Phase 3 — Seed authoring (the craft, proprietary)

| Task | What it is | Status |
|---|---|---|
| C1 — Seed format implementation | S3's spec → working reader/writer + validator. | **done (#148)** |
| C2 — AI-assisted authoring | LLM analyzes IR → proposes seed. Human reviews, edits, approves. | **done #153** (tools/muse_author/) |
| C3 — Expression-budget calibration | Delta-analysis-informed budget suggestions per era/style. | **done** (#175 → [tools/muse_budgets](../tools/muse_budgets/)) |
| C4 — Assertion authoring | Human writes constraints (must_contain, register, form) per work. | **done** (#182 → [tools/assertions](../tools/assertions/)) |

**Phase 3 done when:** seeds are authored for corpus works and validate
against S3 — the founder's ear gates quality. Design docs:
[design/](design/).

## Phase 4 — Mockup harness + renderer (the product)

| Task | What it is | Status |
|---|---|---|
| L1 — Mockup harness | score + seed → LLM → mockup at full DNA density. Generate → validate → fix, bounded retries. | **done #173** (tools/muse_mockup/) |
| L2 — Performance renderer | Mockup → audio via sfizz + SFZ samples (SSO/VPO tier). The "worth listening to" bar. | **done** (#193 → [tools/muse_render](../tools/muse_render/)) |
| L3 — Model comparison rig | Same score+seed, different LLMs → different mockups. Blind A/B listening. | **done** (#195 → [tools/muse_compare](../tools/muse_compare/)) |
| L4 — Distiller | Mockup → extracted interpretation → seed revision. The learning loop. | **done** (#196 → [tools/muse_distill](../tools/muse_distill/)) |

**Phase 4 done when:** one corpus work, performed by the LLM player, passes
the founder's by-ear evaluation as a musical performance — a reading worth a
hall.

## Phase 5 — The event (the unveiling)

| Task | What it is | Status |
|---|---|---|
| E1 — The work | One corpus work, fully seeded + mocked + rendered at concert quality. | **done** (#200 → [tools/muse_event](../tools/muse_event/)) |
| E2 — The venue | Concert hall, projection, the "giant computer" staging. | **done** (#210 → [docs/design/e2-the-venue.md](design/e2-the-venue.md)) |
| E3 — The recording | Document the event; publish. | plan drafted (#211 → [docs/design/e3-the-recording.md](design/e3-the-recording.md)); **publish blocked** on the staged event |

**Phase 5 done when:** deferred until Phase 4 produces one concert-worthy
work.

## Milestone barriers & decomposed sub-tasks

The scaffold-era risk list (blockers/ + session report) decomposed into
workable sub-tasks per TASK_WORKFLOW ("sub-tasks are decomposed from issues
that prove too large"). Each has a design-doc scaffold in
[design/](design/) and feeds the task it unblocks.

| Sub-task | Parent barrier | What it does | Unblocks |
|---|---|---|---|
| **W6 — B9 compute scaling** | Beethoven 9 (239k notes) through pattern analysis | Profiled the real blocker: W4's diff was O(n_a × n_b), so B9 exceeded 15 min and the chain SKIPped `verify`. Fixed at tolerance 0 with a keyed lookup (#317) — **B9 now verifies at recall=precision=1.0 in ~1s** | done (#317) |
| **W7 — Mockup schema v0** | L1's unwritten intermediate artifact | Drafts the mockup session-file schema from delta-analysis evidence + spike JSONs; validate via W4 | L1 harness |
| **C5 — Baroque delta measurement** | C3's unmeasured Baroque budget gap | Runs delta-analysis vocabulary on Baroque corpora (chorales + polyphony); feeds era budgets | C3 (and W3's per-phrase curves) |
| **L5 — Sample-quality waiver** | L2's unresolved "convincing vs. concert" ceiling | Triggered only if L2 fails the founder's ear despite maximal mockup: either commercial-library contract or revised event bar | E1 (event quality) |
| **S6 — Vocal text schema** | Vocal/choral text (Ninth 52 staves, FORMAT_SPEC §8) | Done: `lyric`/`syllabic`/`extend` on the note, presence-bitmap bits 5–7 + string-table intern (#318). B9 round-trips 3,587 lyrics + 405 melismas; the Ode text reconstructs. Single verse in v0 | done (#318) |
| **E4 — Extension decision** | `.mu` extension collision (Kerbal/Lisp) | Pick final file extension before spec publication (`.mu`, `.muse`, `.muw`, …); update spec + corpus + tooling | S5, publication |

Design docs: [design/w6-b9-scaling.md](design/w6-b9-scaling.md),
[design/w7-mockup-schema.md](design/w7-mockup-schema.md),
[design/c5-baroque-delta.md](design/c5-baroque-delta.md),
[design/l5-sample-waiver.md](design/l5-sample-waiver.md),
[design/s6-vocal-text.md](design/s6-vocal-text.md),
[design/e4-extension.md](design/e4-extension.md).

## Phase 2.5 — Integration (chained, gated, explorable)

| Task | What it is | Status |
|---|---|---|
| E2E chain harness | corpus source → IR → pack → container → decode → render, determinism-checked; the compose-proof for the landed parts. | **done** ([#162](https://github.com/philipdallen/rubato/issues/162), tools/muse_chain/ + docs/chain-report.md) |
| CI conformance gate | W2/S1/S2/S5/chain gates run on every push; nothing guards merges today. | **done** ([#163](https://github.com/philipdallen/rubato/issues/163), .github/workflows/) |
| CI flaky retry | manual one-shot re-run of failed conformance jobs; workflow_dispatch-only (auto retry unsafe: `workflow_run` self-triggers, burn loop observed live; see #300)| **done** ([#293](https://github.com/philipdallen/rubato/issues/293), [#300](https://github.com/philipdallen/rubato/issues/300), .github/workflows/retry-flaky.yml + [docs/ci-retry.md](ci-retry.md)) |
| Frontend explorer | QA-only static site: corpus browser + patterns + piano-rolls + pack stats (+audio when P2 lands). | **done** ([#164](https://github.com/philipdallen/rubato/issues/164), docs/explorer/ + tools/muse_explorer/) |
| Integration testing scope | seam map + task breakdown; T1–T3 unblocked, T4–T5 wait on P1. | [docs/integration-testing-scope.md](integration-testing-scope.md) |
| T1 — Seam S2↔S5 | pack → container member → unpack round-trip, W4-diffed | **done** ([#165](https://github.com/philipdallen/rubato/issues/165), tools/muse_roll/tests/) |
| T2 — S2 golden fixtures | pinned payload per corpus tier; drift fails byte-exact compare | **done** ([#166](https://github.com/philipdallen/rubato/issues/166), tests/fixtures/) |
| T3 — Unified test runner | one command for all suites; fast/slow split; substrate for #163 | **done** ([#167](https://github.com/philipdallen/rubato/issues/167), tools/run_tests.sh) |
| T4 — Seam S1→P1 | golden vectors feed P1 decoder when it lands | **done as stub contract** ([#168](https://github.com/philipdallen/rubato/issues/168), DECODER swap pin); full verification awaits P1 |
| T5 — Chain test | full pipeline per corpus file via #162 + P1 | **done** ([#169](https://github.com/philipdallen/rubato/issues/169), chain-report full registry) |
| T6 — Committed-mockup guard | load + render the committed `*.mockup.json` artifacts so format drift fails loudly | **done** ([#275](https://github.com/philipdallen/rubato/issues/275), tools/muse_render/tests/test_committed_mockups.py) |
| A1 — System audit | per-module docs-vs-working-system verification; report + filed findings | [design](design/a1-system-audit.md); Wave 1 split into A1.1 [#278](https://github.com/philipdallen/rubato/issues/278), A1.2 [#279](https://github.com/philipdallen/rubato/issues/279) → [report done](audit/2026-08-26-system-audit-a1-2.md), A1.3 [#280](https://github.com/philipdallen/rubato/issues/280), A1.4 [#281](https://github.com/philipdallen/rubato/issues/281) |
| Frontend QA tiers | T1 static contract (done #164); T2 headless DOM (Playwright) — every served page, links, anchors, mobile widths; T3 live deploy smoke **retired 2026-09-16** | T2 [#183](https://github.com/philipdallen/rubato/issues/183); T3 retired with the hosted preview (#184/#224) |
| Seed workbench | explorer grown into the seed-iteration instrument panel: probes (W-B1), quality-check gate (W-B2), workbench page (W-B3), loop docs (W-B4) | [design](design/seed-workbench.md); W-B1 filed [#185](https://github.com/philipdallen/rubato/issues/185), W-B2 [#186](https://github.com/philipdallen/rubato/issues/186), W-B3 [#187](https://github.com/philipdallen/rubato/issues/187), W-B4 [#188](https://github.com/philipdallen/rubato/issues/188), W-B9 lineage probe [#253](https://github.com/philipdallen/rubato/issues/253) |
| Seed growth harness | close the loop: seed → mockup (L1) → distill (L4) → revised seed → growth report; the workbench's trajectory view | [design](design/seed-growth-harness.md); G1 filed [#203](https://github.com/philipdallen/rubato/issues/203), G2 [#204](https://github.com/philipdallen/rubato/issues/204), G3 [#205](https://github.com/philipdallen/rubato/issues/205), G4 expansion-time logging [#252](https://github.com/philipdallen/rubato/issues/252) |
| L1 generate loop (real) | score + seed → LLM → mockup at full DNA density, generate → validate → fix, bounded retries; the stand-in replacement | [design](design/l1-generate-loop.md); L1.1 [#206](https://github.com/philipdallen/rubato/issues/206), L1.2 [#207](https://github.com/philipdallen/rubato/issues/207), L1.3 [#208](https://github.com/philipdallen/rubato/issues/208), L1.4 [#209](https://github.com/philipdallen/rubato/issues/209), L1.10 mockup provenance [#250](https://github.com/philipdallen/rubato/issues/250), L1.11 stand-in swap **done** [#276](https://github.com/philipdallen/rubato/issues/276) (ManualProvider path); W-B10 pane wiring filed [#294](https://github.com/philipdallen/rubato/issues/294) |
| Workbench master index | routing shell: corpus tree + W-B6–W-B8 panes + pipeline-at-a-glance table (#241); rendered-shape tests #247 | **done** ([#233](https://github.com/philipdallen/rubato/issues/233) W-B6, [#234](https://github.com/philipdallen/rubato/issues/234) W-B7, [#235](https://github.com/philipdallen/rubato/issues/235) W-B8, [#241](https://github.com/philipdallen/rubato/issues/241), [#247](https://github.com/philipdallen/rubato/issues/247), docs/index.html) |
| R — Rehearsal directives | typed NL→seed-revision grammar (R1), workbench Study/Rehearse pane (R2), conductor-training scripts + feedback (R3); directives are lineage roots | [design](design/r1-rehearsal-directives.md); R1 [#282](https://github.com/philipdallen/rubato/issues/282), R2 [#283](https://github.com/philipdallen/rubato/issues/283), R3 [#284](https://github.com/philipdallen/rubato/issues/284) |
| F — Form curve | windowed compressibility (F1 `muse_form`) → viz track (F2) → structural assertion + distill/compare metric (F3); evidence layer, not a generation target | [design](design/f1-form-curve.md); F1 [#296](https://github.com/philipdallen/rubato/issues/296), F2 [#297](https://github.com/philipdallen/rubato/issues/297), F3 [#298](https://github.com/philipdallen/rubato/issues/298) |

## Research direction — rendering and interpretation (2026-10)

PRIOR_ART_REVIEW.md records *what exists*; the rendering research synthesis
([RENDERING_RESEARCH_AND_ROADMAP.md](../RENDERING_RESEARCH_AND_ROADMAP.md))
records *what to build, what is uncertain, and what evidence would change the
direction*. It is a direction record, not a plan of record. Its near-term
sequence, which this plan absorbs:

- **Document the landscape** — consolidate notation-playback,
  expressive-performance, LLM-coaching, and alternative-rendering research
  into [PRIOR_ART_REVIEW.md](../PRIOR_ART_REVIEW.md).
- **Formalize the performance history** — coaching scope, precedence,
  revisions, and score exceptions inspectable and reproducible (R-series +
  lineage chain; finish the walk).
- **Validate the current representation** — a coaching instruction produces a
  measurable, correctly scoped change (the synthesis's first experiment §9).
- **Separate musical quality from audio quality** — identical performance data
  across controlled rendering conditions.
- **Evaluate with musicians** — walked when rendering conditions are credible.
- **Choose the next technology from evidence** — not from assumptions.

Related standing decision: **D22** (decision-log) — rendering and
interpretation stay separable; a renderer consumes the mockup and never
becomes the sole location of interpretive intent.

## Explicitly not (yet)

- Public spec publication (pre-launch decision)
- Distribution/registry/marketplace
- Neural audio rendering (sample tier first)
- Notation-software and DAW plugins (post-launch)