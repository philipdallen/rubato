# Prior art — spike components (2026-08-23)

What exists for each transition in the product model, what to borrow, what to
build. Complements [PRIOR_ART_REVIEW.md](../PRIOR_ART_REVIEW.md) (landscape)
with component-level engineering intel for the spike and beyond.

## T3 — score + seed → mockup (LLM session work)

**The mockup format is the gap.** No standardized open expressive-MIDI
interchange exists. Everyone rolls their own.

| Borrow | What | License | Use |
|---|---|---|---|
| **Basis Mixer / performance codec** (CPJKU) | Per-note expressive parameters (4–5 per note incl. pedal) as an interpretable intermediate | GPLv3 | The mockup's *shape* — per-note expression params is a proven encoding |
| **Magenta Performance RNN** | Event representation: NOTE_ON/OFF, TIME_SHIFT (10ms), VELOCITY | Apache 2.0 | Event vocabulary for the mockup |
| **VirtuosoNet** | MusicXML → expressive MIDI, pretrained, graph score encoding | research | Reference for score-feature extraction |
| **ACCompanion** (CPJKU) | Real-time score following + expressive accompaniment | research | Later — if live interaction ever matters |

**Build:** the mockup JSON itself (our contract), the LLM prompt design, the
validation loop. **Borrow the encodings, not the models** — our thesis is
LLM-as-conductor, but the *vocabulary* of expression is solved research.

## T4 — mockup → audio (rendering)

Solved. Do not build.

| Borrow | What | License | Use |
|---|---|---|---|
| **sfizz** | SFZ player, C API + LV2 | permissive | Primary renderer |
| **FluidSynth** | SoundFont 2/3 player | LGPL | Baseline/fallback renderer |
| **VSCO 2 CE** | Orchestral samples | CC0 | Free-tier orchestra |
| **Virtual Playing Orchestra** | Aggregated free libraries | mixed free | Mid-tier orchestra |
| **Sonatina SSO** | Symphonic orchestra | CC Sampling+ | Alternative |

**Reality check from the research:** free samples reach "convincing mockup,
demo quality" — section ensembles, basic articulations. Commercial
(Spitfire/Kontakt) realism needs articulation depth free libs lack. Our
"worth listening to" bar is achievable; "DG-tier" is not, with free samples.
The VPO+Ardour template (sfizz + Dragonfly reverb) is the known-good recipe.

> **Revalidated 2026-10-09.** Partly stale. Free **Spitfire Symphony
> Orchestra Discover** (Nov 2025) ships 44 instruments and three legato
> patches, so "free lacks true legato" no longer holds as a blanket claim.
> This does **not** change the renderer recipe above: both free Spitfire
> libraries are plugin-hosted (Spitfire's own plugin / Kontakt) and their
> EULA forbids reformatting for another sampler and AI-training use, so they
> cannot feed sfizz. The recipe stays SFZ-based. See
> [design/l5-sample-waiver.md](design/l5-sample-waiver.md) §Free-tier update.

## T2 — IR → seed (seed authoring)

| Borrow | What | Use |
|---|---|---|
| **text2midi** (AMAAI-Lab) | End-to-end text→MIDI with LLM + tokenizer | Pipeline patterns for LLM→symbolic |
| **ComposerX** (paper) | Multi-agent GPT-4 chains for structured composition | Agent-orchestration pattern |
| **ChatMusician** (ACL 2024) | Evidence: domain-adapted LLMs beat generic on notation | Justifies prompt engineering / possible fine-tuning |
| **MuseCoco** | Text → attributes → symbolic, two-stage | The two-stage pattern (structure first, notes second) — mirrors our score→seed→mockup chain |

**Research consensus:** off-the-shelf LLMs need structured output formats +
post-processing + validation for reliable symbolic work. Our generate →
validate → fix loop is the right pattern; nobody has solved it open-ended.

## T5 — mockup → new seed (distillation)

| Borrow | What | Use |
|---|---|---|
| **pyAMPACT** | Score↔performance linking, performance descriptors | Extract tempo/dynamic structure from mockups |
| **Parangonada** | Score-performance alignment viz, Match file format | Alignment + human review of distillations |
| **Partitura** | DTW score-performance alignment | Alignment engine |
| **mir_eval** | Standard MIR metrics | Benchmarking distillation quality |

**Build:** the "mockup → seed revision" distillation logic itself (turning
extracted curves into prompt rules). The extraction tooling exists; the
*learning* is ours.

## Interchange — DAW session formats

| Borrow | What | Use |
|---|---|---|
| **DAWproject** (Bitwig/PreSonus) | Open DAW exchange (zip of XML: tempo, tracks, params); `dawproject-py` exists | Possible export path — **founder-gated per decision-log D20** (mockups are confidential pipeline state; do not build export without sign-off) |
| **Ardour session XML** | Open session format | Alternative export target |

Not needed for the spike (MIDI + sfizz suffices); valuable later for the
"hand it to a producer" story.

## The spike's shopping list

Per [spike.md](spike.md): parser (build, minimal) → seed (hand-written) →
LLM mockup (build — JSON shaped on Basis Mixer params) → MIDI (borrow:
midiutil/mido) → FluidSynth or sfizz + VSCO 2 CE (borrow) → WAV → founder's
ear.

## Strategic takeaways

1. **Everything except the seed and the LLM session work exists.** The
   renderer (sfizz), the samples (VSCO2/VPO), the expression encodings
   (Basis Mixer), the distillation extractors (pyAMPACT), the export format
   (DAWproject) — all borrowable.
2. **The two things we build are the two things that are the product:**
   the seed format/authoring, and the LLM session-work harness. Convenient
   and correct.
3. **"DG-tier with free samples" is not on the menu.** The honest ladder:
   free samples → convincing mockup; commercial libraries (later, licensed)
   → concert-hall tier. The event may want a commercial library budget.
