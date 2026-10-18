# Rubato Format Specification — v0 (Design Draft)

**Status:** Design draft, pre-evidence. The language and encoding details are
pinned by Phase 0/1 work (see [docs/pipeline.md](docs/pipeline.md)); this
document defines the model they must serve. Nothing here is implemented.

## 0. The one-sentence definition

**A `.ru` file is the compressed, executable encoding of a musical work —
three components in one container.** The **score** is the fixed work: what
MusicXML already carries, packaged (our MusicXML). The **prompt** is the
interpretive space: what may vary, and the performance philosophy that guides
the variation. The **manifest** carries rights and provenance in plaintext. A
deterministic player reads the score; an LLM player reads score + prompt and
brings the work to life — slowly, deliberately. A performance is an event,
not a render.

The metaphor: the `.ru` file is the improved piano roll — re-punched with
modern musical knowledge so the existing player piano produces a better
performance. Technology advancing hardware by changing the software.

The thesis is **lossless structure + released intelligence**: compression
finds structure (the analyzer proves it's there), expansion is lossless math
(the decoder is dumb), and what gets spent at session time is the
interpretation — compressed into the seed, not destroyed by entropy coding.

## 1. The three components

| | **Score** | **Prompt** | **Manifest** |
|---|---|---|---|
| What it is | The fixed work | The interpretive space | Rights + provenance |
| Contents | Notes, structure, form, dynamics | Sanctioned ranges, performance philosophy, variation points | License, authorship, AI disclosure, hashes |
| Read by | Deterministic player (baseline) | LLM player (product) | Anyone — plaintext |
| Playback | Identical everywhere, forever | Interpreted; varies by performer within sanctions | — |
| Analogy | Our MIDI / the soil | The seed / the water | The label |

The score answers "what is the work." The prompt answers "how may
it live." The score constrains the prompt; the prompt never contradicts the score.

## 2. Design goals

1. **Compression by construction.** The score is MusicXML compressed:
   columnar, delta-encoded, pattern-factored, entropy-coded. Program length
   versus expanded output is a measurable property of the work.
2. **Determinism at the baseline.** Same `.ru` → identical score playback on
   every conforming player, forever. Conformance is byte-exact.
3. **Interpretation as data.** The prompt is explicit, inspectable, and
   licensed — interpretive decisions are first-class, declared, and bounded.
4. **Rights travel in plaintext.** The manifest is human-readable without
   tooling or execution: license, provenance, AI disclosure.
5. **The decoder is dumb.** All intelligence lives at compression time
   (offline, AI-assisted) or in the LLM player (the product). Baseline
   decoding is pure evaluation.
6. **Evidence-driven design.** Every language construct and encoding choice
   must be justified by corpus analysis (Phase 0). No speculative features.

## 3. File anatomy

A `.ru` file is a zip container (the `.mxl` precedent):

```
work.ru
├── manifest.json      ← REQUIRED. Plaintext. Rights + provenance + hashes.
├── roll.bin           ← REQUIRED. The fixed score, compressed.
├── seed.bin           ← REQUIRED. The interpretive space.
└── performances/      ← OPTIONAL. Certified expansions (see §6).
    └── *.perf
```

**`manifest.json`** — the only human-readable member, by design:
`format_version`, work id, title, composer, license (`renditions:
presets-only | open-within-constraints | closed`, attribution, commercial),
provenance (source, tools, AI involvement disclosure), content hashes of all
other members, signature.

**`roll.bin`** — the compressed score. Encoding pinned by tasks S1–S2:
event-stream format, packing scheme, entropy coding. Baseline: lossless
against the source MusicXML event stream, verified by the diff tool (W4).

**`seed.bin`** — the interpretive space. Encoding pinned by task S3:
sanctioned parameter ranges, performance-philosophy declarations, variation
points with bounds. Human-authored or human-approved at compression time —
the conductor layer. Never machine-invented without review.

**`performances/*.perf`** — cached, certified expansions (composer-approved
renders), each recording the seed settings and content hash it was produced
from. Cached computation, never the definition of the work. Zero-compute
first listen.

## 4. The score — event-stream format (S1, pinned from Phase 0 evidence)

The `roll.bin` payload is the **event stream** every decoder↔renderer
party shares: the on-disk freeze of the in-memory IR that all Phase 0
tools consume (tools/ir/muse_ir). The packing (S2) serializes this stream
columnar+delta+dictionary+entropy; this section pins the **content model
and the layout contract** those codes encode.

### 4.1 Content model (what the stream carries)

- **Parts**: `id`, `name`, `instrument {name?, gm_program?}`,
  `inferred_voice` flag, ordered `notes[]`, per-part `dynamics[]`,
  `hairpins[]` (start/end-linked). Parts are one per instrument/voice
  (MIDI sources: one per note-bearing track).
- **Notes**: `pitch` (MIDI number, or null sentinel for rests/unpitched),
  `onset`, `duration` — **integer ticks only**; `voice`; `velocity` (0..127
  or null, with `velocity_inferred` when synthesized); `articulations`
  (preserved raw); `notations` flags (tie start/stop, slur start/stop,
  fermata, hairpin membership, grace, chord, unpitched).
- **Full maps** — mid-piece changes preserved, never flattened:
  - `tempo`: (tick, milli-bpm = bpm × 1000) fixed point
  - `meter`: (tick, numerator, denominator)
  - `key`: (tick, fifths, mode) — **multi-valued per tick** (transposing
    instruments legitimately disagree; every distinct value is kept)
- **Meta**: `source_format` (musicxml|midi), `ppq` (integer ticks per
  quarter — for MusicXML the LCM of the file's divisions values; for MIDI
  the file's own ticks-per-beat), `title?`, `warnings[]`.

**Fidelity rule (evidence: corpus README + W3 report).** Every written
`<note>` element maps to exactly one note event — ties are start/stop
flags, never merged; rests are first-class events; chord members share
onsets; grace notes carry duration 0; unpitched percussion is a class,
not a rest. A compressor that drops or merges events fails the W4
ground-truth diff, which counts rests and unpitched as matchable
entities.

### 4.2 Tick and curve resolution (facts from corpus)

- **ppq bounds (measured)**: Bach — 2; Byrd (MIDI) — 192; Beethoven 9 —
  24; Schubert — LCM value from mixed divisions. v0 therefore accepts
  source ppq as-is; the packer's tick domain is per-work and recorded in
  meta (S1 does not normalize a canonical ppq — re-flation is
  source-exact by construction).
- **Dynamics**: discrete text markings at tick positions (p..ffffffff;
  measured maxima are per-part lists). Hairpins are start/end-linked
  entries with start tick and end tick (open-ended at source closed at
  part end with a warning).
- **Tempo curves (S3/L1 layer, not here)** — the score carries the marked
  tempo map only; continuous tempo shaping is a prompt-side parameter and
  never bakes into the score stream.

### 4.3 Ordering and validation (decoder contract)

- Notes are sorted by (onset, pitch, velocity, lexicographic notations,
  voice, source tie-break) — a total, deterministic order; decoders may
  rely on it.
- Maps are tick-ordered, `tempo` and `meter` single-valued per tick (same-
  tick conflicts resolve first-wins with a warning at import time).
- `Work.validate()` invariants (negative onset/duration, pitch/velocity
  range, ordered maps, unique part ids) are checked at encode time;
  malformed input fails loudly with `IRParseError`, never partial data.

### 4.4 Golden vectors (conformance)

Per task: (source → canonical JSON dump) pairs pinned by W4's diff tool.
Generators/verifiers: [`tools/s1_stream/muse_stream`](tools/s1_stream/).
JSON is the human-readable interchange encoding only; the binary layout
belongs to S2. Canonical form: `json.dumps(sort_keys=True,
separators) + "\n"`; integers only.

Packing: columnar arrays, delta-encoded onsets, dictionary-coded repeated
patterns, entropy-coded residual (S2). The pattern-factoring layer
(sequences, transposed repeats, ostinati — imitative entries measured at
zero on the corpus, 2026-08-23 W3 report) is driven by analyzer evidence.

### 4.5 Scope

- **In:** parts, notes, full maps, dynamics, hairpins, articulations,
  notations flags, meta.
- **Out:** language constructs (S4), score packing (S2), prompt/seed
  encoding (S3), container/manifest (S5).

### 4.6 The packing (S2, pinned 2026-08-23)

`roll.bin` carries the §4 content model as:

```
MUR1 | varint(compressed_length) | zlib(payload)
```

- **Varints**: unsigned LEB128 (7-bit groups, MSB continuation); signed via
  zigzag. Integers only — the §4 tick contract holds on disk.
- **Payload layout**: string table (UTF-8, length-prefixed, deduped) →
  JSON meta (sorted keys, minimal separators: source_format, ppq, title,
  warnings) → maps (delta-encoded ticks: tempo, meter, key) → parts.
- **Parts**: id/name (string table), instrument flags, per-note columnar
  stream — onset deltas (zigzag), presence bitmap for optional fields
  (pitch, velocity, articulations, notations, source_id, **lyric,
  syllabic, extend, verses** — bits 5–8, added 2026-09-16 for S6/#318),
  duration, voice. Dynamics delta-encoded with dictionary-coded text;
  hairpins start-delta + optional end + dictionary-coded kind. Lyric and
  syllabic go through the same string table as dynamics and notation names,
  so repeated syllables ("der", "und", "-en") cost one entry each. An
  additional verse carries its own flags byte (lyric present / syllabic
  present / extend), so a verse record is self-describing.
- **Entropy coding**: zlib level 9 over the whole payload (stdlib; an
  off-the-shelf coder, per the design doc's open question — a custom
  coder is a post-v1 optimization, never a correctness issue).
- **Lossless by construction and by proof**: every corpus file
  round-trips losslessly (W4 recall = precision = 1.0 through the
  `tools/muse_roll/cli.py verify` gate; B9 verified by W4 as of #317,
  plus encode→decode→canonical-compare). Ratios vs. source: Bach ~10–12% of
  .mxl, Byrd MIDI ~14–22%, Schubert 9.6%, Beethoven 5 0.26%,
  Beethoven 9 0.24% (68.8 MB → 177 KB; was 168 KB before vocal text
  landed — +5.2% for 3,587 lyrics + 405 melisma flags). The ten
  instrumental works are byte-identical to before that change, which is
  the evidence the extension is additive.

## 5. The prompt (model)

The prompt declares the **sanctioned space** — what a performance may
vary — plus the **philosophy** that guides it:

- **Parameters with ranges**: tempo bounds, variation level, density, energy.
  A performance chooses points inside; it can never reach outside.
- **Philosophy declarations**: tempo philosophy ("flexible, architectural"),
  dynamic philosophy ("terraced, dramatic"), articulation stance. Free-text +
  typed fields; references styles and practices, never artist identities
  without a license record.
- **Variation points**: where the work permits interpretation (ornamentation
  zones, optional repeats, cadenza-like freedoms), each with bounds.
- **Assertions**: invariants every performance must satisfy (theme recall,
  register bounds, structural form). The LLM player's output is validated
  against these; failure is loud, never silent deviation.

**Advocacy rule.** The composer (or encoder) is the work's advocate; the prompt
is the advocacy instrument. Wildly different readings are valid when
they satisfy the assertions — the Gould/Bernstein case is in-spec. What is
out-of-spec is violating the score: the assertions fail and playback refuses.

## 5.1 The executable layer (S4, pinned 2026-08-23)

W3's full-corpus report ([docs/analysis-report.md](docs/analysis-report.md))
measures three pattern classes recurring in **all 13 corpus files**;
they ship as operators (grammar, not semantics — a construct without
corpus evidence doesn't ship):

| Operator | Corpus evidence | Status |
|---|---|---|
| `ptn_exact` | exact repeats in all 13 files (Bach 8–1212, Byrd 1–76, Schubert 30,436, B5 18,763, B9 252,643) | ships |
| `ptn_transposed` | transposed repeats in all 13 files (Bach 17–1215, Byrd 1–100, Schubert 29,401, B5 16,833, B9 150,243) | ships |
| `ptn_ostinato` | rhythmic ostinati in all 13 files (Bach 35–171, Byrd 7–301, Schubert 9,534, B5 2,246, B9 14,605) | ships |
| `ptn_invert`, `ptn_retro` | no evidence (W3 scans these classes uniformly: zero) | deferred |
| `ptn_imitative` | zero in corpus (Byrd expected, but none found) | deferred |

A **program** is a flat sequence of operator applications. Each entry:

```yaml
program: [
  { op: ptn_exact, region: [start_tick, end_tick], part: "P2" },
  { op: ptn_transposed, region: [..], interval: +2, part: "P1" },
  { op: ptn_ostinato, region: [..], part: "P3" },
]
```

- `region`: half-open tick range (required, integers).
- `part` (optional): restrict evaluation to one part id.
- `interval` (required on `ptn_transposed`): signed semitones; the sign is
  mandatory notation (`+2`, `-5`).
- No nesting; sequential application only. Control flow is degenerate by
  design — the score's topology, not the program's.
- Grammar-only validation (unknown op, missing region, malformed interval)
  plus region bounds against the work's tick compass. Assertions from the
  surrounding seed (S3.5) gate the final event stream; S4's validator does
  not (and must not) evaluate them.

Assertion vocabulary (S3.5) may also include
  `form_curve_correlation`: a declared form-letter run must appear
  recognizably as a contiguous subsequence of the work's derived form
  curve — see [tools/muse_assert](tools/muse_assert/README.md) for the
  kind's shape and semantics.

 Reference validator: `tools/muse_ops/`. Semantics are P1's decoder, not S4.

## 6. Execution model

```
BASELINE PATH (deterministic):
score ──decode──▶ event stream ──▶ renderer ──▶ audio

PRODUCT PATH (the musician):
score + prompt ──▶ LLM session work ──▶ mockup ──▶ validate vs. assertions
    ──▶ renderer ──▶ audio

LEARNING LOOP:
mockup ──distill──▶ improved prompt (new seed) ──▶ next mockup is better
```

- **The mockup is the intermediate artifact.** The LLM does not "perform" — it
  does session work: tempo map, dynamic curves, velocities, articulation,
  balance. The mockup is the session file (expressive-MIDI-class data:
  onset/duration/velocity/articulation + tempo map + curves + per-part
  balance). The renderer turns the mockup into audio via sample playback
  (sfizz/SFZ tier) — existing open technology, not built here.
- **Deterministic path**: decode → render. No AI, no network, no ambiguity.
  The free baseline and the conformance target.
- **Product path**: the LLM interprets within the prompt space, bounded by
  the score. Generate → validate → fix, bounded retries, fail loudly.
  Provenance (model, timestamp) is stamped by the harness, never trusted to
  the model. Deliberation takes time — a performance is an event.
- **The learning loop**: mockups are distilled back into prompts (new seeds).
  The prompt accumulates interpretive craft; later mockups are cheaper and
  better. Every prompt revision records which mockups informed it.
- **Machine-readable except the manifest.** Score, prompt, and mockup are
  data for machines. Human readability lives in tooling (decode/trace), not
  in the formats. The manifest stays plaintext — rights are for lawyers.
- **Renderer tiers**: soundfont (baseline) → SFZ/samples via sfizz (the
  "worth listening to" bar — no DAW engineering required) → neural (later).
  The event stream / mockup contract is the seam; renderers compete below it.

## 6.1 Layer boundaries (interpretation vs. rendering)

Four layers are kept separate by construction (decision D22; full framing in
[RENDERING_RESEARCH_AND_ROADMAP.md](RENDERING_RESEARCH_AND_ROADMAP.md)):

1. **Score** (`roll.bin`) — the fixed work.
2. **Interpretation** — the seed's sanctioned space plus the
   performance-specific coaching history (directives, revisions, precedence).
3. **Performance representation** — the mockup: the single carrier of
   interpretive intent across the renderer seam.
4. **Rendering** — the engine and its settings, which translate the mockup
   but never invent interpretation.

Two format consequences:

- **Coaching history is preserved, not flattened.** A performance-specific
  history is a chain of revisions over the seed (directive → seed → mockup →
  revised seed), walked by hashed `extends`/`seed_hash` links — see
  [proposal-lineage-chain.md](docs/design/proposal-lineage-chain.md) and
  [r1-rehearsal-directives.md](docs/design/r1-rehearsal-directives.md). New
  coaching applies to the current revision; it is never silently replaced by
  assumptions drawn from an earlier performance of the same work.
- **Renderer-specific settings are not artistic intent.** Sample library,
  engine choice, and mix configuration live with the renderer (or as
  `performances/*.perf` metadata), never in the seed. A rendering improvement
  that needs new intent amends the representation upstream, not the renderer.

Global and local scopes, revisions, precedence, and explicit departures from
notation are expressed in the seed/prompt layer (§5) and the directive grammar
(R1), not encoded as new score constructs: the score stays fixed (D1).

## 6.2 Source-agnostic seed authoring

The prompt is authored from **any source**, via the IR (the canonical
event-stream representation every tool shares):

| Source | What the author sees | Prompt richness |
|---|---|---|
| MusicXML | Notation semantics: dynamics, articulation, form | Richest — everything explicit |
| DAW session | A producer's mockup: tempo map, curves, balance | Interpretation partially present — the prompt can learn from a human session |
| MIDI | Pitch × time only (the two-dimensional tree) | Sparse — structure inferred, inferences marked |

Richer sources author richer prompts; poorer sources author sparser prompts
with marked inferences (recorded in the manifest). The prompt is never
finished — it is re-authored and revised as tools improve.

## 7. Conformance and versioning

- **Decoder conformance**: golden vectors — `.ru` → event stream, byte-exact,
  including resource-bound behavior. A decoder conforms or it doesn't.
- **Work conformance**: every corpus work round-trips — source → `.ru` →
  event stream, diff green. The corpus ladder gates versions; the complete
  Beethoven 9 is the v1.0 target.
- **`format_version` is semver.** v0.x may break; v1+ additive only.

## 7.1 The container (S5, pinned 2026-08-23)

Zip layout per §3: `manifest.json` first member, then `roll.bin`,
`seed.bin`, optional `performances/*.perf`. No other members. Required
members: `manifest.json`, `roll.bin`, `seed.bin`. Reference validator:
`tools/muse_mu/`.

**`manifest.json` field set** (the only human-readable member):

- `format_version` (semver string), `work_id` (required)
- `title`, `composer` (optional)
- `license` (required): `renditions` ∈ {`presets-only`,
  `open-within-constraints`, `closed`} (required), `attribution` (required
  non-empty string), `commercial` (required boolean)
- `provenance` (required): `source` (required), `author` (required),
  `ai_involvement` ∈ {`none`, `assisted`, `generated`} (**mandatory AI
  disclosure**, required), `tools` (optional list), `license_ref` (optional;
  unlocks artist-identity references in the seed's philosophy fields)
- `hashes` (required): `member name → sha256 hex` of **every** other member;
  the manifest never hashes itself. Readers fail loudly on mismatch or on
  members missing from the map.
- `signature` (optional): HMAC-SHA256 hex over the canonical JSON (sorted
  keys, minimal separators) of the manifest minus the signature field, when
  a signing key exists. PKI deferred — the open question is recorded there;
  HMAC is the mechanism until publication demands asymmetric trust.

## 8. Open questions (to be pinned by Phase 0/1)

- Exact score packing scheme (driven by analyzer statistics).
- Prompt field set (driven by compression experiments).
- Whether the executable layer needs a general operator set (transpose/
  invert/retro/aug/dim) or the corpus demands more.
- Performance-file encoding details.

**Closed 2026-09-16 (S6, #318):** "How vocal/choral text is carried" — as
first-class optional fields on the note (`lyric`, `syllabic`, `extend`, and
`verses` for 2..n), packed in presence-bitmap bits 5–8 (§4.6) with syllables
interned in the string table. Verse 1 lives directly on the note so the common
case needs no nesting; `verses` carries the rest, because the corpus settles it
— `bwv227.7` and `bwv227.11` each set two texts per note, a chorale singing one
tune to several verses. Unknown `<syllabic>` values and non-numeric verse
numbers are reported with a warning rather than silently dropped. The Ninth's
finale round-trips: 3,587 lyrics and 405 melisma flags; both chorale movements
round-trip both verses.
