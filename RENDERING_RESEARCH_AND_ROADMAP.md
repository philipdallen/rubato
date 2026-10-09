# Rubato: Rendering Research and Roadmap

**Status:** Research synthesis and proposed experiments. Not a spec, not a
plan of record — a direction record and a falsifiable test set.
**Purpose:** Connect expressive-performance research to Rubato's product
architecture and its validation plan.
**Scope:** Notation playback, expressive-performance models, MIDI and
controller representations, sound rendering, and rehearsal-style coaching.
**Relationship to existing docs:** [PRIOR_ART_REVIEW.md](PRIOR_ART_REVIEW.md)
records *what exists*. This document asks a different question: given that
landscape, **what should Rubato build, what remains uncertain, and what
evidence would change our direction?** Detailed claims and citations live in
`PRIOR_ART_REVIEW.md` or in linked research records; this is the synthesis
layer on top of them.

> **Read with the repo, not instead of it.** The four layers below are not
> new architecture — they are names for boundaries the repo already draws
> (score = `roll.bin`, interpretation = seed + directives, performance
> representation = mockup, rendering = L2). Naming them is the point: the
> hypotheses are only testable once the boundary between them is explicit.

---

## 1. Product objective

Rubato provides a rehearsal-like interface through which a conductor can
communicate interpretive intent to a virtual ensemble. The system translates
coaching into revisions of a performance while preserving the original score,
the performance-specific coaching history, and the ability to revisit an
earlier interpretation.

The objective is **not** merely to generate expressive MIDI. It is to make
musical interpretation **coachable, inspectable, repeatable, and increasingly
effective through iterative rehearsal.** That is the product thesis; expressive
MIDI is an implementation detail somewhere inside it.

This framing is already load-bearing in the repo: the R-series
([r1-rehearsal-directives.md](docs/design/r1-rehearsal-directives.md)) ships a
typed coach-language → seed-revision grammar whose directives are files and
whose lineage roots are hashes; the lineage proposal
([proposal-lineage-chain.md](docs/design/proposal-lineage-chain.md)) makes the
coaching chain walkable from directive to seed to mockup. What remains
unproven is whether a coached change **survives the render** — which is the
question this document exists to make testable.

---

## 2. Working model

Four conceptual layers, each of which can succeed or fail independently:

| # | Layer | Question it answers | Repo artifact |
|---|---|---|---|
| 1 | **Musical source** | What is the work? | Score / `roll.bin` / W1 IR |
| 2 | **Interpretation** | How may it live, and by whose direction? | Seed (S3) + directives (R-series) + coaching history |
| 3 | **Performance representation** | What did this reading actually decide? | Mockup (L1), tempo map, curves, balance |
| 4 | **Rendering** | How does it sound? | L2 renderer tiers (soundfont → SFZ → neural, later) |

These layers must be **evaluated separately.** Better interpretation does not
guarantee better audio; more realistic audio does not guarantee better
interpretation. Conflating them is what lets a result look good for the wrong
reason.

### The water analogy

The founder's image, kept because it names the boundary precisely:

- **The water** — the musical information and expressive intent.
- **The nozzle** — the representation of notes, timing, velocity, and
  controllers (MIDI-class; today, the mockup).
- **The showerhead** — the rendering engine: instrument articulation,
  synthesis, and the mapping of expressive controls to sound (L2 and below).
- **The person adjusting the shower** — the conductor, coaching across
  repeated listening and revision (layers 2 and the rehearsal loop).

Two consequences follow, and they are the whole research programme in two
sentences:

1. **A better showerhead cannot recover information the nozzle never
   conveys.** Rendering cannot add intent the performance representation
   never carried.
2. **A better nozzle cannot make an unconvincing instrument sound convincing
   by itself.** Representation cannot substitute for sound generation.

Rubato must investigate, and keep separate, both sides of that boundary.

---

## 3. Research findings and limitations

- **Notation playback** provides useful baselines but varies in its treatment
  of phrasing, rubato, articulation, and instrumental balance.
- **Expressive-performance research** demonstrates promising results
  (Basis Mixer / Con Espressione, VirtuosoNet, S2A), but performance quality,
  repertoire coverage, instrumentation, and evaluation methods vary by system.
- **Text-conditioned performance systems and LLM-to-MIDI prototypes**
  (Midi-LLM, MIDI-GPT, MIDI-VALLE) are adjacent prior art. Their existence
  does not establish that Rubato's proposed coaching-history architecture is
  novel.
- **MIDI is a representation and control interface, not a sound-generation
  engine.** Its practical expressive ceiling depends on the controls encoded,
  the receiving instrument, and the renderer.
- **Neural synthesis and richer controller formats** may offer future paths
  beyond note-and-velocity workflows. Compatibility with full orchestral
  scores remains an open question.
- **Current Rubato mockups sound MIDI-like.** Until rendering quality is
  controlled, listening results cannot reliably isolate the quality of the
  interpretation layer — a spike result the repo already recorded
  ([docs/spike.md](docs/spike.md): GM masked everything, SSO strings made
  interpretation perceptible, "not overly expressive" was the honest ceiling).

Time-sensitive claims here are revalidated before they are treated as current
facts; the repo's rule that a documented absence is not proof of absence
applies to every negative claim above.

---

## 4. Architectural principle

**Preserve the distinction between the score and its performance-specific
interpretation.**

- Coaching is stored as a **traceable record of directions and revisions.**
  Each direction has an explicit scope, and precedence or conflicts are
  inspectable.
- New coaching is applied to the **current** performance history — never
  silently replaced by assumptions drawn from previous performances of the
  same composition (the failure mode the R1 lineage-root design exists to
  prevent).
- A renderer consumes a **well-defined performance representation** rather
  than becoming the sole location where interpretive intent exists.

Concretely: **the mockup is the single carrier of interpretive intent across
the nozzle boundary.** A renderer may translate, but must not invent,
interpretation. If a rendering improvement needs new intent, that intent
belongs upstream in the representation, not inside the renderer.

---

## 5. Open hypotheses

Each is stated so it can fail. None is verified until tested.

| # | Hypothesis | What would falsify it |
|---|---|---|
| **H1** | Hierarchical coaching improves expressive results beyond a score-only playback baseline. | Coached and baseline performances are indistinguishable under controlled measurement. |
| **H2** | Preserving coaching history improves consistency across repeated renders and sessions. | Replaying identical history yields divergent results, or history adds no consistency. |
| **H3** | Separating interpretation from rendering makes improvements portable across playback engines. | The same performance data renders inconsistently across engines in ways the representation cannot explain. |
| **H4** | Richer control curves and articulation mappings produce audible improvements when rendered with appropriate instruments. | Richer controls are inaudible even through a capable engine. |
| **H5** | A better renderer makes existing interpretive improvements easier for trained musicians to evaluate. | A better renderer does not change expert judgments of the same representation. |

H1–H4 are testable on the current toolchain. **H5 depends on a renderer we do
not yet have**, so it is last by construction.

---

## 6. Proposed evaluation sequence

1. Establish a reproducible **score-only baseline.**
2. Apply a **small set of controlled coaching directions.**
3. Verify the generated performance changes **in the intended direction** and
   respects score constraints unless an explicit exception is requested.
4. **Repeat identical renders** to test determinism and inspect
   coaching-history consistency.
5. Compare baseline and coached performances through the **same rendering
   engine and instrument configuration.**
6. Repeat selected comparisons through a **second renderer** to test
   portability (H3).
7. Conduct **blinded evaluations with trained musicians** when the rendering
   conditions are sufficiently credible.

Measure interpretation, score compliance, rendering quality, repeatability,
and coaching effort **separately.** A single blended score would hide the
very boundary this document is trying to protect.

---

## 7. Immediate priority

Do not begin by replacing MIDI or building a custom neural synthesizer.

First determine:

- whether Rubato's **current performance representation** can express the
  intended changes;
- whether those changes **survive rendering**;
- and which limitations are attributable to the **representation** versus the
  **sound engine.**

The next engineering decision should be driven by controlled examples and
explicit failure cases, not by assumptions about a technology's potential.

---

## 8. Decision log

For each experiment, record **the question, controlled variables, artifacts,
results, limitations, and the resulting decision.** Distinguish observed
results from hypotheses, prior-art claims, and proposed future work.

This mirrors the repo's existing decision discipline
([docs/decision-log.md](docs/decision-log.md)) and the growth harness's
"compare deltas, never auto-apply" rule
([seed-growth-harness.md](docs/design/seed-growth-harness.md)). The first
entry is §9.

---

## 9. The first experiment (run before exploring neural synthesis)

Test whether the expressive information Rubato already produces can be
evaluated **independently of sound quality.**

**Material:** one short public-domain passage with a clear phrase and cadence
— the chorale material already in `seeds/` and `docs/workbench/` is the
available instance.

**Three versions:**

- **A — Baseline:** score played with no interpretive coaching.
- **B — Coached:** one specific instruction, e.g. *"build toward the cadence,
  then relax the tempo."*
- **C — Repeated coaching:** the same instruction, then a local correction to
  one measure, rendered again.

Keep the score, instrument preset, renderer, and all other settings **fixed.**

| What to measure | What it tells you |
|---|---|
| Tempo and dynamics | Did the requested change actually happen? |
| Local versus global effects | Did the correction affect the intended scope? |
| Score compliance | Were notes and structural constraints preserved? |
| Repeatability | Did the same coaching history produce consistent results? |
| Listening judgment | Can trained musicians hear and prefer the intended interpretation? |

For this initial experiment, **the first four measures are inspectable
programmatically.** The fifth needs listening tests, and a positive technical
result alone does **not** establish artistic quality.

**Artifacts to save:** the source score, the coaching instructions, the
structured performance output (mockup), the rendered audio, and the
evaluation results.

**What success looks like:** if B and C contain the intended musical changes
**even when the sound is basic**, Rubato has established something valuable
before investing in better samples. If the intended changes do not appear in
the representation, no renderer improvement can rescue them — that is a
representation failure, not an audio failure, and it is the more important
of the two to discover early.

### Where this rides on existing tooling

The measurement column maps onto tools that already exist:

- **Tempo / dynamics / local-vs-global** — the distiller's `Interpretation`
  fields (`tempo_curve_shape`, `velocity_pstdev`, `rubato_pstdev_ms`,
  `part_gains`) in [tools/muse_distill](tools/muse_distill), which R3
  already designates as the "did the directive survive the render"
  measurements.
- **Score compliance** — the W4 diff at tolerance 0, plus the seed
  assertions ([tools/muse_assert](tools/muse_assert)).
- **Repeatability** — the determinism probe in
  [tools/muse_probes](tools/muse_probes).
- **Coaching effort** — the R-series dry-run delta preview.

The experiment is therefore mostly **assembly and recording**, not new
machinery — which is the point: it establishes whether the current approach
works before new machinery is justified.

**Filed as [#380](https://github.com/philipdallen/rubato/issues/380)** (seed
level). The render-level column awaits
[#381](https://github.com/philipdallen/rubato/issues/381).

---

## 10. The MIDI-bottleneck investigation (the showerhead question)

Investigate the rendering bottleneck as a **separate, small, structured
study** — three paths compared, not one commitment made.

**Path A — Richer control over existing instruments.**
Explore tempo curves, continuous dynamics, articulation switching, expression
controls, and instrument-specific mappings. This is the lowest-cost way to
determine whether Rubato's existing renderer can convey more expressive
intent. (The mockup schema — [w7](docs/design/w7-mockup-schema.md) and
[tools/muse_mockup](tools/muse_mockup) — is where Path A changes would land.)

**Path B — A more capable sound engine.**
Test whether the same performance data becomes more convincing when the
renderer has realistic legato, bowing, breath, articulation, and dynamic
transitions. This isolates the sound-generation bottleneck (H3/H5). The
renderer tiers are already named in
[l2-performance-renderer.md](docs/design/l2-performance-renderer.md) and the
sample-ceiling waiver in [l5-sample-waiver.md](docs/design/l5-sample-waiver.md).
**Filed as [#382](https://github.com/philipdallen/rubato/issues/382).**

**Path C — Alternative representations and neural synthesis.**
Investigate MIDI 2.0, richer per-note control, orchestral articulation
standards, and neural synthesis approaches. Determine what information they
preserve, what they require from the renderer, and whether they support the
full orchestral use case.

These are **research paths, not conclusions that one technology is superior.**
For each, record what it can represent, what it can render, what it cannot yet
do, and what evidence would justify adopting it.

> **The trap this section avoids.** "Adopt a richer representation" and
> "adopt a better engine" are not decisions — they are directions. The
> decision is which **observed failure** a given path fixes, and the
> failure must be recorded before the path is chosen.

---

## 11. What the project plan should say now

Add this near-term sequence alongside the existing plan
([docs/pipeline.md](docs/pipeline.md)):

- **Document the landscape.** Consolidate the notation playback,
  expressive-performance, LLM coaching, and alternative-rendering research
  into [PRIOR_ART_REVIEW.md](PRIOR_ART_REVIEW.md).
- **Formalize the performance history.** Make coaching scope, precedence,
  revisions, and score exceptions inspectable and reproducible — the R-series
  and lineage chain already do most of this; finish the walk.
- **Validate the current representation.** Demonstrate that a coaching
  instruction produces a measurable, correctly scoped change (§9).
- **Separate musical quality from audio quality.** Compare identical
  performance data across controlled rendering conditions.
- **Evaluate with musicians.** Establish whether the changes sound musically
  appropriate and whether experts can coach the system efficiently.
- **Choose the next technology from evidence.** Improve MIDI control, adopt a
  different renderer, or investigate alternative representations based on
  observed limitations.

### The defensible position

Avoid claiming that Rubato has solved expressive rendering, or that the field
has no competing approach. The defensible position is narrower and stronger:

> Rubato is building and testing a particular combination of **hierarchical
> rehearsal-style coaching, persistent performance history, and
> renderer-independent expressive control.**

That gives the repo a clear research direction while keeping the next
engineering task small and falsifiable.

---

## 12. Explicit non-claims

- No claim that Rubato's current render is expressive or concert-worthy
  (the spike's verdict was conditional at best).
- No claim of novelty for the components in isolation — only for the
  combination, and only once tested.
- No replacement of MIDI or a custom neural synthesizer in this phase; §7
  defers both until a controlled failure case demands them.
- No training in the product path — consistent with pipeline's standing
  decision that delta analysis produces design knowledge, never training data.

---

## Related documents

- [PRIOR_ART_REVIEW.md](PRIOR_ART_REVIEW.md) — the evidence layer.
- [FORMAT_SPEC.md](FORMAT_SPEC.md) — where the score/interpretation/
  representation boundaries are encoded.
- [docs/design/r1-rehearsal-directives.md](docs/design/r1-rehearsal-directives.md)
  — the coaching grammar and its lineage-root semantics.
- [docs/design/proposal-lineage-chain.md](docs/design/proposal-lineage-chain.md)
  — the walkable coaching chain.
- [docs/decision-log.md](docs/decision-log.md) — where this doc's decisions land.
- [docs/pipeline.md](docs/pipeline.md) — the plan of record this feeds.

## Filed follow-ups

The synthesis's next steps are filed as tasks (one task = one issue, per
[TASK_WORKFLOW.md](TASK_WORKFLOW.md)):

- [#380](https://github.com/philipdallen/rubato/issues/380) — RR1: run the
  first experiment at the seed level (this doc, §9).
- [#381](https://github.com/philipdallen/rubato/issues/381) — RR2: wire the
  real L1 generate loop into the study/probe survival path (the render-level
  bridge §9 depends on).
- [#382](https://github.com/philipdallen/rubato/issues/382) — RR3: sfizz/SFZ
  renderer tier + same-mockup portability A/B (§10 Path B; H3/H5).
