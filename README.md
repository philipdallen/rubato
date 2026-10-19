# Rubato

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Start here.** New to the repo? Read this file, then
> [FORMAT_SPEC.md](FORMAT_SPEC.md) (the format), then
> [docs/decision-log.md](docs/decision-log.md) (why it is this way).
> [docs/README.md](docs/README.md) indexes every doc by phase.

**An executable music format.** A `.ru` file packages a musical work as three
components: the **score** (the fixed work — our compressed MusicXML), the
**prompt** (the interpretive space), and the **manifest** (plaintext rights).
Any conforming player reads the score for exact mechanical playback; an LLM
player reads score + prompt and brings the work to life — slowly,
deliberately. A performance is an event, not a render.

> **Status: pre-launch development.** The repo is public; the work inside it is
> not finished. Format spec, tooling, and corpus live on `main`; deterministic
> player (P1/P2) and LLM-side harnesses are landed and tested. Nothing here is
> launch-ready, and the format spec will not be announced before it is.

## At a glance

- **An executable music format**: a `.ru` file packages score + interpretive prompt + plaintext rights, so a work is portable and provably renderable — not just a static file.
- **AI-native playback coaching**: an LLM player reads score + prompt and *performs* the work, sculpting tempo, balance, and articulation inside the authored interpretive space — a performance is an event, not a render.
- **Reference corpus acquired**: five public-domain masterworks (Bach chorales through complete Beethoven 9) already corpus'd as the v1.0 conformance target.

> Full background below, or jump to [the product model](#the-product-model).
>> **Built with agentic AI tooling.** The author designed the format spec and directed AI-assisted tooling development; agent-based coding workflows implemented and tested the reference components.


## The product model

MusicXML is the existing roll — the full score, uncompressed. Rubato compresses
and adapts it into `.ru`: portable, executable, and carrying the interpretive
space alongside the notes.

```
MusicXML (the existing roll)
    │
    ▼  compressor (proprietary, AI-assisted)
.ru file = score + prompt + manifest
    │
    ├─▶ deterministic player (free, reference) — reads the score.
    │    "Our MIDI player." Proves the format, verifies encodings.
    │
    └─▶ LLM player (the product) — reads score + prompt, produces a
         mockup (the session file: tempo map, curves, balance), rendered
         through samples. "The musician." A performance is an event.
```

Technology advancing hardware by changing the software: the deterministic
player never changes; the rolls keep getting better.

## The components

| Component | Contains | Read by |
|---|---|---|
| **Score** | Notes, structure, form, dynamics — the fixed work | Deterministic player |
| **Prompt** | Interpretive space: sanctioned ranges, performance philosophy, what may vary. Authored from any source (MusicXML, DAW session, MIDI) via the shared IR. | LLM player |
| **Manifest** | License, provenance, AI disclosure, hashes | Anyone — plaintext |

## Component status

Phases 0–4 of the build plan ([docs/pipeline.md](docs/pipeline.md)) are
complete; Phase 5 (the unveiling) is partly landed and the public publication
step is deliberately deferred.

**Launch-ready** means: the format spec is frozen at v1.0 (Phase 1 done),
every corpus work round-trips through the deterministic player losslessly
(Phase 2 done), and one corpus work performed by the LLM player has passed
the founder's by-ear evaluation as a musical performance (Phase 4 done).
Until all three hold, nothing is announced.

The **TRL** column is the component's readiness level from
[status/trl.json](status/trl.json) (1 = idea, 9 = proven in the field); the
`_rationale` block there gives the done-when behind each number. A dash means
the component is not separately rated there.

| Component | TRL | Status | Visibility |
|---|---|---|---|
| Format spec ([FORMAT_SPEC.md](FORMAT_SPEC.md)) | 2 | v0 design draft; the encoding and language sections are pinned by Phase 0/1 evidence | Public at launch |
| Reference corpus ([corpus/](corpus/)) | 6 | **Acquired** — Bach, Byrd, Schubert, Beethoven 5, Beethoven 9 complete | Public domain sources |
| Workbench + analyzer (W-series) | 5 | **Landed** — event IR, corpus loader, analyzer, diff tool, visualizer, B9 scaling fix | Internal |
| Compressor (MusicXML → `.ru`) | 5 | **Landed** — score S2 [tools/muse_roll](tools/muse_roll/), language S4 [tools/muse_ops](tools/muse_ops/), container S5 [tools/muse_mu](tools/muse_mu/), seed S3 series [tools/muse_seed](tools/muse_seed/) | Proprietary |
| Deterministic player | 6 | **Landed** — decoder P1 [tools/muse_decode](tools/muse_decode/), renderer P2 [tools/muse_play](tools/muse_play/), conformance suite P3 [tools/muse_ci](tools/muse_ci/) | Public at launch |
| E2E chain gate | — | **Landed** — source → IR → pack → container → decode → render, determinism-checked; B9 verifies at recall=precision=1.0 ([tools/muse_chain](tools/muse_chain/)) | Internal |
| Seed authoring (C-series) | 5 | **Landed** — format impl, AI-assisted authoring, budget calibration, assertion authoring | Proprietary |
| LLM player (L-series) | 3 | **Landed** — mockup harness L1 [tools/muse_mockup](tools/muse_mockup/), renderer L2 [tools/muse_render](tools/muse_render/), A/B rig L3 [tools/muse_compare](tools/muse_compare/), distiller L4 [tools/muse_distill](tools/muse_distill/) | **The product — proprietary** |
| Event (E-series) | — | E1 work + E2 venue **done**; E3 recording plan drafted, **publication blocked** on a concert-worthy Phase-4 result | At launch |

## The corpus

Five public-domain works in high-quality MusicXML/MIDI, from Bach chorales to
the complete Beethoven 9 — the v1.0 conformance target. See
[corpus/README.md](corpus/README.md).

## Process

Multi-agent task workflow per [TASK_WORKFLOW.md](TASK_WORKFLOW.md): one task
per GitHub issue, label-based states, blockers over guessing. The work plan
lives in [docs/pipeline.md](docs/pipeline.md).

## Principles

1. **Format-first.** The spec is the platform. Everything else is a client.
2. **Determinism is the baseline.** Same file → same score playback, everywhere.
3. **The prompt is the product.** The LLM player grows what the score fixes.
4. **Composer-owned, rights-carrying.** Plaintext manifest: license,
   provenance, AI disclosure. No artist lookalikes without license.
5. **Own the format, not the models.** LLMs are the utility; Rubato is the radio.
