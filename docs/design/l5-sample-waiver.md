# L5 — Sample-quality waiver (design doc, scaffold)

**Phase 4 — The product (sub-task; conditional gate). Status: scaffold.**

## Decision framework

**Trigger:** L2 renders a mockup at maximal fidelity (full DNA density,
correct budgets, proper articulation mapping) and the founder's ear says
"not worth a hall." That's the failure condition.

**Two paths:**

| Path | Cost | Timeline | Quality ceiling |
|---|---|---|---|
| **A — Commercial library contract** | $500–$5,000 per library (Spitfire Symphony Orchestra full £449, Vienna Synchron ~$1,500+, Orchestral Tools ~$500–$2,000 per section) | Weeks (license + integration) | Concert-hall tier; true legato, section blends, hall acoustics |
| **B — Revised event bar** | $0 | Immediate | "Convincing mockup" becomes the bar; event staged with narration/context framing the technology, not the audio fidelity |

**What "convincing failure" means technically:**
- Sample libraries without true legato transitions do not sing note into
  note; audible as "MIDI-ish" phrasing. (See the free-tier update below —
  this is no longer a clean free-vs-paid split.)
- Section realism: libraries that are single-instrument or small ensemble
  produce synthetic orchestral blend.
- Hall acoustics: dry libraries need convolution reverb, which helps but
  does not replicate a scored hall recording.

**Evidence sources:**
- [../prior-art-spike.md](../prior-art-spike.md) §T4: "free samples reach
  'convincing mockup, demo quality' — section ensembles, basic
  articulations. Commercial (Spitfire/Kontakt) realism needs articulation
  depth free libs lack."
- [../spike/](../spike/) listener: chorale/Byrd renders at SSO tier; the
  founder's verdict ("good enough for now" at v3) was the spike pass
  condition, not the event bar.

## Free-tier update (revalidated 2026-10-09)

Two free Spitfire libraries now exist that this doc's original framing did
not know about. They change the **evidence** for the sample ceiling; they do
**not** change the integration story, because of the EULA gates below.

| Library | Size | Content | Player | Legato |
|---|---|---|---|---|
| **BBC Symphony Orchestra Discover** | ~240 MB | 34 instruments + grand piano, 47 techniques, 1 mic | Spitfire's own VST3/AU/AAX plugin | none |
| **Spitfire Symphony Orchestra Discover** (Nov 2025) | 5.68 GB | 44 instruments, 74 techniques, 11 solos, 1 mic | free Kontakt Player 7.5+ | **3 legatos** |

(Also in this class: Orchestral Tools Berlin Free Orchestra, SINE Player.)

**What this corrects in this doc:**

- **Price.** Path A cited "Spitfire BBC SO ~$300". BBCSO Discover is free
  (since July 2022, no questionnaire); SSO Discover is free from Nov 2025.
  The *paid* flagship is now Spitfire Symphony Orchestra at £449.
- **"Free samples lack true legato."** False as a blanket claim: SSO
  Discover ships three legato patches. Free-vs-paid is now a *depth* and
  *articulation-count* spectrum, not a binary. The spike's legato finding
  still holds for **Sonatina SSO** (the CC-licensed library the current
  renderer actually uses), which has no true legato sustains.

**Why they are not a drop-in for Rubato** (this is the part that matters):

1. **Not SFZ.** The current renderer is sfizz + SFZ ([l2-performance-renderer.md](l2-performance-renderer.md),
   [#382](https://github.com/philipdallen/rubato/issues/382)). BBCSO
   Discover is a proprietary plugin (no SFZ); SSO Discover is a Kontakt
   library. Either path means **hosting a third-party plugin**, a new render
   backend — not a sample-directory swap.
2. **EULA forbids reformatting.** Spitfire's EULA expressly forbids
   distributing or using the products "reformatted for use in another
   sampler". Extracting the samples and generating SFZ for sfizz —
   the obvious workaround — is prohibited. This rules out the cheapest
   integration route by license, not by effort.
3. **EULA forbids AI/LLM training use.** The EULA prohibits using the
   libraries "for the purpose of training artificial intelligence (AI)
   systems or large language models (LLMs) without... express written
   consent". Rubato's current generate path is prompt-based and never
   trains on samples, so it is unaffected. But the rendering roadmap's
   **Path C** (neural synthesis, the `RENDERING_RESEARCH_AND_ROADMAP.md`
   synthesis, tracked as [#382](https://github.com/philipdallen/rubato/issues/382))
   must not ingest rendered Spitfire audio as training data without written
   consent. Recorded here as a gate on that path.
4. **License intent.** The grant is "exclusively for the creation of new
   music and sound compositions". Rehearsal/research tooling sits close to
   this boundary; any productization using these libraries should re-check
   the EULA at the time, since it is not a permissive open license like the
   CC terms on Sonatina SSO / VSCO 2 CE.

**Net:** the free Spitfire tier is the strongest *listening* evidence
available at $0, and worth using when the founder's ear test opens. It is
**not** the free *renderer* tier — that remains Sonatina SSO / VSCO 2 CE via
sfizz. Revalidate these facts before relying on them; library terms and
line-ups change.

## Purpose

L2's sample-tier render is gated on the founder's ear. If it fails despite
maximal mockup fidelity — the "convincing vs. DG-tier" ceiling — this
sub-task opens: either a commercial-library contract (event budget) or a
revision of the event quality bar. Trigger condition keeps this off the
day-to-day path.

## Dependencies

- **Upstream:** L2 (render quality + trigger); spike listener for evidence.
- **Downstream:** E1 (event quality decision).

## Scope (pin in draft)

- **Inputs:** L2 render + founder verdict on the mockup.
- **Outputs:** waiver decision + rationale, recorded in the design doc.
- **Non-goals:** L2's implementation; standalone event staging (E2).

## Open questions

- Threshold: what specifically distinguishes "convincing" failure from
  mockup-craft failure. (Answered above: legato gaps, section blend,
  hall acoustics — measurable in the render, not the mockup.)

## Acceptance criteria (when promoted to draft)

- Decision recorded with rationale; E1's path clarified.
