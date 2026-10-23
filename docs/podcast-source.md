# Muse — system overview (podcast source)

A `.mu` file is to a MusicXML score what a well-punched piano roll is to a
crude one: the same work, better encoded, so the machine plays it better.
Technology advancing hardware by changing only the software.

## The three components

The whole thesis in one sentence: **compression finds structure (W3),
expansion is lossless math (P-series), and the released intelligence is
interpretation (L-series).**

Every `.mu` file carries three things:

| Component | What it is | Analogy |
|---|---|---|
| **Score** | The fixed work — notes, structure, dynamics, packaged | The soil |
| **Prompt (seed)** | The interpretive space — what may vary, bounded by assertions | The water |
| **Manifest** | Rights, provenance, AI disclosure — plaintext | The label |

Two processes act on it, and they are different in kind:

- **Unzip** — pure mathematics. The deterministic player reads the score,
  plays it identically everywhere, forever. Free baseline. Proves the format.
- **Grow** — intelligence-guided. The LLM player reads score + prompt, does
  session work (tempo map, curves, velocities, balance), produces a mockup
  worth listening to. The product.

## The pipeline: 39 suites, about 1100 tests, one gate

The build runs on a ladder. Each rung is a tool; each tool has tests; the
ladder is the ratchet:

```
corpus sources (Bach → Byrd → Schubert → Beethoven 5 → Beethoven 9)
    ↓
W1 — event-stream IR        (Partitura-style note arrays, integer ticks)
    ↓
W2 — corpus loader           (every work loads, known-answer pins)
    ↓
W3 — pattern analyzer        (SIATEC-class: exact/transposed/ostinato)
    ↓
W4 — diff tool               (recall/precision in tick space, CI-ready)
    ↓
W5 — visualizer              (piano-roll plots, 52-part-safe)
    ↓
S-series specs               (S1 stream, S2 encoding, S3 seed, S4 language, S5 container)
    ↓
C1 — seed validator          (read/write + budget checks + assertions)
C2 — AI authoring            (LLM proposes seed, human approves)
    ↓
L1 — mockup harness          (dense DNA: chord spread, attack/release, swell)
    ↓
P-series player              (decoder → renderer, conformance suite)
```

The conformance gate runs **39 suites, about 1100 tests** on every push. Beethoven 9
(239,459 notes, 52 parts) is the v1.0 target — the CD was sized for it; the
format is designed for the space of all of them.

## What the evidence showed

**Compressibility is real.** Beethoven 9 yields 252,643 distinct exact
patterns under analysis — the format thesis (a work is compressible because
it is themes, variations, recursion) is measurable, not metaphorical.

**Interpretation is measurable.** Delta analysis (22 pianists × the same
Mozart phrase): Classical-era freedom lives in tempo (~75% spread);
Romantic-era freedom lives in dynamics (~145–195% spread); chord spread
(~16–17ms, melody-lead) is the universal device across eras. Seed budgets
are calibrated from these numbers, not guesses.

**Free samples have a ceiling.** The spike proved the pipeline works but
the render is "convincing, not DG-tier." SSO-class samples lack true
legato. The event may need commercial libraries — a budget decision,
deferred.

## The architecture in one diagram

```
source score (MusicXML/MIDI)
    ↓  W1/W2/W3/W4/W5 (the workbench)
IR + pattern evidence + diff tool + viz
    ↓  S-series (the format)
spec: stream, encoding, seed, language, container
    ↓  C-series (the workbench)
seed validator + AI authoring
    ↓  L-series (the product)
mockup harness → renderer → audio
    ↓  E-series (the unveiling)
one concert-worthy work, staged publicly
```

## The running themes

- **Determinism is sacred** — the baseline plays identically everywhere;
  the prompt is where variation lives.
- **No artist lookalikes** — philosophies reference styles and practices,
  never an artist's identity, without a license.
- **Provenance is mandatory** — every manifest records source, license,
  and AI involvement in plaintext.
- **The founder's ear gates quality** — metrics support judgment; the ear
  decides.

## Sources

FORMAT_SPEC.md (the three-component model), docs/vision.md (the thesis),
docs/pipeline.md (the ladder), docs/decision-log.md (locked decisions),
tools/*/README.md (the running system).
