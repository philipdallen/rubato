# Rubato Schema Specification — v0 (Draft)

> **SUPERSEDED — design history only.** The project pivoted from a JSON schema
> to an executable format. The normative design now lives in
> [FORMAT_SPEC.md](FORMAT_SPEC.md). This document is kept because its ideas
> survive in the new design: the transform grammar became language operators,
> `constraints` became assertions, `renditions` became parameter bundles, the
> performance layer became the decoder's event stream, and the
> license/provenance model became the container manifest.

**Status:** Draft. Normative language and validation rules will tighten in later versions.
**Goal:** Define a JSON-native document that captures a musical composition as a *space of valid renditions* rather than a single fixed performance — the difference between a score and a score plus its orchestration rules.

A Rubato schema document answers two questions:

1. **What is the composition?** — themes, motifs, rhythms, harmony, form, and the constraints that make it *this* piece and not another.
2. **What may vary?** — the sanctioned degrees of freedom (tempo range, instrumentation, genre treatment, density, energy) that a rendition may explore while remaining a rendition of the same work.

## 1. Design goals

- **JSON-native.** Web-friendly, diffable, schema-validatable, LLM-legible. Prior art: JAMS (annotations), MEI (semantic rigor), MusicXML (interchange — Rubato schemas must round-trip import from MusicXML/MIDI where possible).
- **Semantics over engraving.** The schema describes musical *intent* (motif, theme, variation, function of a section), not visual layout. It is closer to MEI's philosophy than MusicXML's.
- **Two-population authoring.** Hand-authorable by a composer in a node-based editor, and generatable/editable by an agent from natural-language direction.
- **Engine-agnostic.** Any conforming generative engine must be able to render any conforming schema. Rendering fidelity is measured against the schema's constraints, not against a reference recording.
- **Rights-carrying.** Provenance, authorship, and licensing terms travel inside the document.

## 2. Document structure

A Rubato schema is a single JSON object with these top-level members:

```jsonc
{
  "muse_version": "0.1",          // schema spec version (required)
  "metadata":    { },             // title, composer, provenance, license (required)
  "globals":     { },             // tempo, meter, key, tuning (required)
  "material":    { },             // themes, motifs, rhythm cells, harmonic vocabulary
  "form":        { },             // ordered sections, their roles, and how material appears in them
  "constraints": { },             // invariants every rendition must satisfy
  "renditions":  [ ],             // sanctioned rendition presets ("genre covers")
  "extensions":  { }              // namespaced, engine- or composer-specific data
}
```

### 2.1 `metadata`

```jsonc
"metadata": {
  "id": "muse:work:01J…",              // stable work identifier (ULID/UUID)
  "title": "…",
  "composer": { "name": "…", "id": "…" },
  "created": "2026-08-21T00:00:00Z",
  "license": {                          // what a renderer/distributor may do
    "renditions": "presets-only",       // presets-only | open-within-constraints | closed
    "attribution": "required",
    "commercial": true
  },
  "provenance": [ ]                     // generation/edit history; AI involvement disclosures
}
```

`metadata.id` is a ULID or RFC 4122 UUID, optionally prefixed with `muse:work:` — the prefixed form is the recommended display/canonical form; both validate (see §2.8).

### 2.2 `globals`

```jsonc
"globals": {
  "tempo":  { "bpm": 96, "range": [84, 112], "feel": "straight" },
  "meter":  { "beats": 4, "unit": 4 },          // additive/odd meters allowed: { "beats": [3,3,2], "unit": 8 }
  "key":    { "tonic": "D", "mode": "dorian" }, // or "atonal", or per-section overrides
  "duration_bars": 64
}
```

Ranges, not scalars, are the point: `tempo.range` defines what renditions may explore; `constraints` (§2.5) can narrow it further per section.

### 2.3 `material` — themes, motifs, rhythm cells

The reusable musical vocabulary of the work. Everything in `form` references material by ID.

```jsonc
"material": {
  "motifs": [
    {
      "id": "motif.a",
      "kind": "pitch_rhythm",             // pitch | rhythm | pitch_rhythm | timbre | harmonic
      "pitches":   [ "D4", "F4", "A4", "G4" ],
      "durations": [ 0.5, 0.5, 1.0, 1.0 ],  // in beats
      "contour":   "up-up-down",
      "tags":      [ "primary", "opening" ]
    }
  ],
  "themes": [
    {
      "id": "theme.1",
      "phrases": [ { "motifs": [ "motif.a", "motif.a#seq(+2)" ] } ],  // motifs with transforms
      "cadence": "half"
    }
  ],
  "rhythms": [
    { "id": "groove.1", "pattern": [1, 0, 0.75, 0, 1, 0, 0.75, 0.25], "grid": "8n" }
  ],
  "harmony": {
    "progressions": [
      { "id": "prog.verse", "chords": [ "Dm7", "G7", "Cmaj7", "Am7" ], "bars_per_chord": 1 }
    ],
    "vocabulary": "diatonic-plus-bVII"     // free-text or formal grammar ref
  }
}
```

`pitches` are scientific pitch notation, 12-TET: a letter A–G, optional `#`/`b` accidental, signed octave (middle C = C4). The same grammar bounds `constraints.register` (§2.5) — one shared definition in the schemas. Microtonality is out of scope here (§6).

**Transforms** are suffix expressions applied at the reference site: `motif.a#seq(+2)` (sequence up a step), `#inv` (inversion), `#retro` (retrograde), `#aug(2)` (augmentation), `#dim(0.5)` (diminution). The transform set is the mechanism for **variations** — a core primitive, not an afterthought.

### 2.4 `form` — sections and structure

```jsonc
"form": {
  "sections": [
    {
      "id": "verse.1",
      "role": "verse",                    // see role vocabulary below
      "bars": 16,
      "uses": [ { "ref": "theme.1", "variation": "plain" } ],
      "harmony": "prog.verse",
      "energy": 0.4                       // 0–1 target, interpreted per-rendition
    },
    {
      "id": "chorus.1",
      "role": "chorus",
      "bars": 8,
      "uses": [ { "ref": "theme.1#aug(2)", "variation": "developed, ornamented" } ],
      "energy": 0.9
    }
  ],
  "order": [ "verse.1", "chorus.1", "verse.1", "chorus.1" ],
  "repetition": { "verse.1": { "min": 2, "max": 4 } }
}
```

**`role` vocabulary.** Roles are tradition-neutral structural labels, not genre signals. The enum spans compositional traditions; tools must pass role values through verbatim (never assume pop structure). `custom` remains for anything else.

- **Universal:** `intro`, `outro`, `interlude`, `coda`, `solo`, `custom`
- **Song form:** `verse`, `pre_chorus`, `chorus`, `refrain`, `bridge`, `hook`
- **Classical / concert form:** `exposition`, `development`, `recapitulation`, `episode`, `theme`, `variation`, `trio`, `minuet`, `scherzo`, `fugue`, `cadenza`, `finale`
- **Film / media scoring:** `cue`, `underscore`, `stinger`, `main_title`, `end_credits`
- **DAW / production form:** `build`, `drop`, `breakdown`, `vamp`, `groove`

A section's role is semantic intent for interpreters and cleanup agents; conformance depends on `form.order`/`repetition`/`constraints`, not on the role name.

`uses[].ref` follows the transform-ref grammar of §2.3 (id + optional `#seq/#inv/#retro/#aug/#dim` suffixes). `variation` is free text describing the treatment — it is not transform syntax and is not validated against the transform grammar.

`order` and `repetition` allow the form itself to be a bounded space (e.g., verse count may vary 2–4× across renditions) rather than a fixed sequence.

### 2.5 `constraints` — the invariants

What every rendition must satisfy to be a rendition of *this* work. Constraints are the conformance contract between composer and engine.

```jsonc
"constraints": {
  "must_contain": [ "motif.a" ],                       // motif recall requirement
  "must_not":      [ { "kind": "modulation_beyond", "semitones": 3 } ],
  "tempo_lock":    { "chorus.1": [ 92, 104 ] },
  "tempo_shapes":  { "bridge.cadenza": { "kind": "ritardando", "target_bpm": 72, "span": "final_bars" } },
  "register":      { "theme.1": [ "C4", "A5" ] },
  "structure":     { "form_deviation": "none" }        // none | reorder | abridge
}
```

A conforming engine renders audio that satisfies all `constraints` while exploring the freedom left by `globals` ranges and the active `rendition`.

**`tempo_shapes`** (v0.3) are per-section expressive tempo constraints — the schema-level vocabulary for ritardando, accelerando, and rubato that `globals.tempo.range` cannot express. Three kinds:

- `ritardando` / `accelerando` — the section's tempo moves monotonically toward `target_bpm`. `span` scopes where the shape applies: `section` (default), `final_bars`, or `opening_bars` (counted against the section's own bar count).
- `rubato` — bounded expressive deviation within `deviation_bpm` around the active tempo; the section returns to tempo at its end.

Relation to the performance layer (§7): the schema *constrains*; the performance document *realizes*. A conforming interpreter's `tempo_map` must satisfy every `tempo_shapes` entry — rit./accel. appear as a monotone bpm ramp ending at `target_bpm` within the span; rubato stays within the deviation band and returns to the section's base tempo. `tempo_lock` (scalar bounds) composes orthogonally: a section may have both, and the realized curve must satisfy each.

### 2.6 `renditions` — sanctioned presets ("genre covers")

Named parameter bundles a listener can select. Each rendition is a first-class object with its own metadata (so it can be credited, licensed, and traded separately).

```jsonc
"renditions": [
  {
    "id": "r.synthwave",
    "name": "Midnight Drive",
    "style": { "genre": "synthwave", "era": "1984", "references": [ "arpeggiated bass", "gated reverb drums" ] },
    "params": { "tempo_bpm": 100, "instrumentation": [ "analog synth", "drum machine" ], "density": 0.7, "swing": 0.0 },
    "author": { "name": "…" }            // may differ from composer — renditions are collaborative works
  },
  {
    "id": "r.quartet",
    "name": "Late Set",
    "style": { "genre": "jazz quartet", "era": "1959" },
    "params": { "tempo_bpm": 88, "instrumentation": [ "piano", "upright bass", "brushes", "tenor sax" ], "swing": 0.62 }
  }
]
```

**Hard rule:** `style.references` describe styles, eras, and production techniques. Named-artist imitation ("sounds like <artist>") is out of spec without an attached license record (see §2.1 `license`).

**Instrumentation depth (v0.3).** `params.instrumentation` strings stay valid for production contexts ("analog synth", "drum machine"). Renditions that need orchestral precision may instead (or additionally) carry structured entries:

```jsonc
"instrumentation": [
  "drum machine",
  {
    "name": "Violin I",
    "program": 48,                    // GM fallback — Player V1 renders this
    "doubles": [ { "name": "piccolo", "program": 72 } ],
    "techniques": {                   // sanctioned states the rendition may invoke
      "divisi": "allowed",            // allowed | required — split a part into sub-voices
      "mute": [ "con_sordino", "senza_sordino" ],
      "bowing": [ "arco", "pizzicato", "sul_ponticello", "sul_tasto", "col_legno" ]
    }
  }
]
```

Technique names are a controlled vocabulary: **`divisi`** (allowed/required), **mutes** (`con_sordino`, `senza_sordino`, `harmon`, `cup`, `straight`), **bowing** (`arco`, `pizzicato`, `sul_ponticello`, `sul_tasto`, `col_legno`, `spiccato`), **breath/attack** (`flutter_tongue`, `slap_tongue`, `overblown`), **production** (`sidechained`, `gated`, `doubt_tracked`). The list extends additively; unknown technique names are valid strings but conforming engines must ignore-and-record them (same discipline as unknown extension namespaces).

Techniques map to the performance layer as articulation/controllers: the interpreter translates a sanctioned technique into `notes[].articulation` where one exists, otherwise into `controllers` (e.g. `timbre`) or part-level directives — and anything the active player cannot render is dropped with the decision recorded (Player V1 honors GM `program` only). This keeps the schema's expressive ceiling above any single engine's floor.

**Mix topology (v0.3).** `params.mix` extends per-part gain/pan with the *sanctioned mixing space* — bus routing and send structure that renditions may vary within, not full DAW automation:

```jsonc
"params": {
  "mix": {
    "buses": [
      { "id": "bus.drums", "kind": "group" },
      { "id": "bus.verb",  "kind": "send", "effect": "plate reverb" }
    ],
    "routes": [
      { "part": "drums",  "bus": "bus.drums" },
      { "part": "vocals", "bus": "bus.verb", "send": 0.35 }
    ],
    "sidechains": [
      { "source": "kick", "target": "bass", "amount": [ 0.4, 0.8 ] }
    ]
  }
}
```

- **`buses`** declare the topology: `group` buses sum parts; `send` buses carry an effect. Ranges and effect identities stay loose — the schema says *what may route where*, not which plugin.
- **`routes`** attach parts (or rendition instrumentation names) to buses; a `send` level is itself a rangeable value (scalar or `[min, max]` the rendition may explore).
- **`sidechains`** declare ducking relationships (`source` ducks `target` by `amount`, rangeable). They express the *effect*, not the compressor patch — an engine realizes it with whatever dynamics processing it has.
- Everything here is a rendition hook: values may be scalars or `[min, max]` ranges, and `constraints` may pin them. The performance layer realizes the concrete mix; Player V1 applies gain/pan/`reverb_send` and records any routing it cannot honor (same honored-or-dropped discipline as techniques).

### 2.7 `extensions`

Namespaced escape hatch, e.g. `"extensions": { "engine.audiocraft": { "cfg": 3.5 } }`. Conforming engines must ignore unknown namespaces, never fail on them.

### 2.8 Identifiers

Two identifier families exist, with different grammars:

- **Work id** (`metadata.id`): a ULID (26 chars, Crockford base32) or RFC 4122 UUID, optionally prefixed with `muse:work:`. Validators accept both forms.
- **Internal ids** — `material.motifs[]`/`themes[]`/`rhythms[]`/`harmony.progressions[]`, `form.sections[]`, `renditions[]`: dotted slugs (`^[A-Za-z0-9_.-]+$`), namespaced by prefix: `motif.*`, `theme.*`, `groove.*`, `prog.*`, `r.*` for renditions, free-form for sections (e.g. `verse.1`). The prefix tells a reader which collection an id lives in; references in `form.sections[].uses[].ref` and `constraints.must_contain[]` resolve against the material collections, `form.sections[].harmony` against progressions. Chord symbols (e.g. `Dm7`, `Bbmaj7`) are free text, not slugs — a future chord grammar is an open question (§6).

## 3. Conformance

A renderer is **Rubato-conforming** if it:

1. Produces audio satisfying every entry in `constraints`.
2. Realizes every `must_contain` motif recognizably (motif recall is the primary fidelity metric).
3. Follows `form.order` within the bounds of `repetition` and `structure.form_deviation`.
4. Stays within `globals` ranges unless the active rendition explicitly overrides them.

**Validation (planned):** a JSON Schema for syntactic validation, plus an engine-side test harness reporting motif-recall and structure-fidelity scores per render.

## 4. Interchange

- **Import:** MusicXML and MIDI (lossy: imports produce `material` + a single default rendition; form/roles inferred where possible).
- **Export:** flattened, fixed renderings may export to MusicXML/MIDI; the schema itself is never "compiled away" — it remains the canonical artifact.

## 5. Versioning

`muse_version` is semver. v0.x drafts may break compatibility freely; from v1.0, all changes are additive within a major version.

**Changelog**

- **v0.3 (2026-08-22):** §7 `instrument` gains `divisi`, `doubles`, `techniques` — orchestral writing depth beyond GM programs; honor-or-drop conformance rule with recorded decisions in `extensions` (issue #76).
- **v0.3 (2026-08-22):** `constraints.tempo_shapes` added — per-section ritardando/accelerando/rubato constraints with bounded spans; conformance relation to §7 `tempo_map` stated (issue #75).
- **v0.3 (2026-08-22):** structured instrumentation entries in `renditions[].params.instrumentation` (issue #76): GM program fallback, `doubles`, and a controlled technique vocabulary (`divisi`, mutes, bowing, breath/attack, production), with the honored-or-dropped-with-recording rule for performance-layer mapping.
- **v0.3 (2026-08-22):** `renditions[].params.mix` added (issue #77): buses (group/send), part routing with rangeable send levels, and sidechain ducking relations — the sanctioned mixing space, not DAW automation.
- **v0.2 (2026-08-22):** `form.sections[].role` enum broadened from pop-song vocabulary to a tradition-spanning taxonomy (universal / song form / classical / film / production roles), with pass-through semantics stated (issue #67).
- **v0.1 (2026-08-22):** `metadata.id` grammar extended to accept the `muse:work:` prefix shown in the §2.1 example (issue #43); identifier conventions stated in new §2.8.
- **v0.1 (2026-08-22):** shared 12-TET pitch grammar pinned for `material.motifs[].pitches` and `constraints.register` bounds (issue #44).
- **v0.1 (2026-08-22):** `metadata.provenance` items sealed (`additionalProperties: false`), matching every other fixed-shape object (issue #45).
- **v0.1 (2026-08-22):** transform-ref grammar enforced on `form.sections[].uses[].ref` via shared `$defs/materialRef`; `uses[].variation` pinned as free text (issue #46).
- **v0.1 (2026-08-22):** §7 performance layer drafted (v0) from the batch-3 scope doc (removed in the docs-only pivot; issue #21).

## 6. Open questions for v0.x

- How formal should `harmony.vocabulary` grammars be (regex-like chord grammar vs. free text + reference progressions)?
- Representation of microtonality/tuning systems beyond 12-TET.
- Whether `constraints` should support engine-checkable predicates (e.g., "chorus must be ≥ +6 dB denser than verse") as a typed DSL.
- Minimal motif encoding for non-pitched / timbral material.

## 7. Performance layer (draft v0)

> **Draft v0, unstable.** Shapes below follow the batch-3 scope doc (removed
> in the docs-only pivot); v0.x may break freely, additive-only discipline
> starts at v1.

A **performance document** (`*.muse.perf.json`) is the concrete event format an
interpreter produces from a schema + rendition and a player renders to audio.
Expressive-MIDI-as-JSON. Prior art curated: Magenta NoteSequence (absolute-time
note model), MIDI 2.0 (per-note controllers), MNX (JSON notation modeling).
Feasibility grounding: expressive performance rendering literature (Performance
RNN et al.) demonstrates score → expressive performance is tractable.

The schema defines the space; the performance document is a point in it. Both
sides of that contract — interpreter and player — validate against it.

**Two clocks, both stored.** Seconds are authoritative for playback; beats are
retained per event and in the tempo map for structural traceability — the
conformance harness measures motif recall and structure fidelity in beat space.

```jsonc
{
  "muse_perf_version": "0.1.0",       // independent of muse_version
  "metadata": {
    "source":      { "schema_id": "muse:work:01J…", "rendition_id": "r.synthwave" },
    "interpreter": { "model": "…", "at": "2026-08-22T00:00:00Z" }
  },
  "tempo_map": [ { "time": 0.0, "beat": 0, "bpm": 96 } ],
  "parts": [
    { "id": "p.lead", "name": "Lead",
      "instrument": { "name": "violin", "program": 40, "sample_set": "vsco2-ce",
                      "divisi": 2, "doubles": ["piccolo"],
                      "techniques": ["pizzicato", "sul_ponticello"] },
      "mix": { "gain": 0.8, "pan": 0.0, "reverb_send": 0.3 } }
  ],
  "notes": [
    { "part": "p.lead", "pitch": 62, "pitch_name": "D4",
      "onset": 0.0, "duration": 0.3125, "onset_beat": 0, "duration_beats": 0.5,
      "velocity": 90, "articulation": "tenuto",
      "controllers": { "pitch_bend": [ ] } }   // optional; MIDI 2.0 lineage
  ],
  "dynamics": [ { "time": 0.0, "part": "p.lead", "level": 0.6 } ]  // part omitted = global
}
```

`pitch_name` reuses the §2.3 pitch grammar — one pitch language across schema,
importer IR, and performance layer. Reference integrity: `notes[].part` and
`dynamics[].part` resolve against `parts[].id`.

**Instrumentation depth (v0.3).** Beyond the GM-program/sample-set mapping,
`instrument` optionally carries:

- `divisi` — count of divided sub-parts (≥ 2; omit for unison/tutti). Players
  without sampled divisi render the full part on the base instrument and
  record the drop.
- `doubles` — instrument names the player switches to mid-part (flute →
  piccolo). Which doubles are *sanctioned* is a schema/rendition decision;
  the performance document records what was realized.
- `techniques` — active performance/extended techniques: `muted`,
  `sul_ponticello`, `sul_tasto`, `pizzicato`, `arco`, `col_legno`,
  `harmonics`, `flutter_tongue`, `tremolo`, `trill`. A player honors what it
  can (techniques map to sample-set switches or controller patterns); it
  must drop what it can't and record the drop in
  `extensions.<player>.dropped` — never fail on an unsupported technique.
