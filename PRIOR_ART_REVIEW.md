# Prior Art & Literature Review — Generative Music Composition Platform ("Muse")

**Date:** 2026-08-21
**Purpose:** Landscape review before building a platform with four layers:
1. **Semantic schema** — structured blueprint of a composition (tempo, form, structure, melodies, motifs, themes, variations, rhythms)
2. **Composer interface** — visual/node-based tool to author schemas
3. **Generative audio engine** — AI interpreting the schema in real time
4. **Listener front end** — listeners pick composers + renditions ("covers"/genres/artist lookalikes)

Working analogy: film-score composer writes the skeleton; orchestrators/producers deliver final renditions.

---

> **2026-08-25 update (post-pivot, P/L-series era).** The original review
> surveyed the *schema-era* platform concept (generative composition,
> listener rendition marketplace). The current product is different: an
> LLM **conductor** that reads a packaged score + interpretive seed and
> emits a dense performance *mockup* (tempo map, dynamic curves, per-note
> expression — a DAW-session-class artifact) rendered to audio by SFZ
> samples, with assertions validating the mockup against the score.
> A re-survey of the DAW/AI landscape (this date) confirms the pivot
> holds up; see the appendix below §8.

---

## Executive Summary

- **Every layer of the architecture exists as prior art — but nobody owns the full loop.** Symbolic schemas (MusicXML/MEI/JAMS), node-based composition tools (OpenMusic, Opusmodus), generative engines (Suno, AIVA, MusicGen, Endel, LifeScore), and listener-facing adaptive/rendition experiences (Endel, AiMi, Hook, Udio's upcoming "Starstruck") all exist. The open gap is a **composer-authored, portable schema as the canonical release artifact**, rendered by AI in real time, with listeners choosing renditions in an open (non-label-gated) marketplace.
- **Don't build on a major streaming platform.** The largest DSPs offer no third-party in-app plugin platform, and their open developer APIs have been tightening (2025–2026) to the point of being explicitly "not a foundation for building a business." Plan for a standalone product with your own playback surface; treat DSP integrations as optional and downstream.
- **The legal environment has hardened since 2025.** The majors' lawsuits against Suno/Udio ended in settlements that move the whole industry toward *licensed, opt-in* generation (Udio+UMG "Starstruck," Suno+WMG licensed models, all three majors licensing KLAY). "Artist lookalikes" is the single highest-risk feature in your concept (right of publicity / voice likeness). The schema-first design is actually a *legal asset*: a human-authored schema is copyrightable, which strengthens provenance and authorship claims over the AI output.
- **Recommendation:** build standalone under your own brand ("Muse"), and treat existing streaming services as optional integration/distribution partners later.

---

## 1. The Semantic Schema Layer (composition as structured data)

| Prior art | What it is | Relevance / gap |
|---|---|---|
| **MusicXML** (Recordare/MakeMusic, 2000s–now) | Dominant XML interchange format for notation; supported by Sibelius, Finale, Dorico, MuseScore | Interchange of *fixed* scores, not generative blueprints. Presentation-heavy, weak on higher-level semantics (form, motifs, themes as first-class objects) |
| **MEI (Music Encoding Initiative)** | Community XML schema focused on *semantics* of notation; customizable schemas (CMN, mensural, neumes) | Closest philosophical ancestor to your idea: encodes intellectual content, not just engraving. Academic adoption, little commercial |
| **JAMS (JSON Annotated Music Specification)** (NYU MARL) | JSON schema for structured music annotations (chords, segments, beats, tags) | Modern, web-native precedent for a JSON-based musical schema |
| **MIDI / SMF** | Performance event stream | Too low-level; no structure/semantics |
| **GUIDO, abc notation, **kern (Humdrum), LilyPond** | Text-based score languages | Proven that text-native symbolic formats work well with tooling and, more recently, LLMs (ChatMusician, NotaGen use abc-style encodings) |
| **OMN (Opusmodus Notation)** | Lisp-like symbolic scripting language for composition | Proof that a domain-specific symbolic language can drive a full composer workflow |
| **Lead-sheet / chord-chart schemas** (Hookpad TheoryTab, Chordify) | Songs reduced to form + harmony + melody | Shows how much of a pop song can be captured in a compact schema |
| **LLM-era symbolic generation research** | MuseCoCo (text→attributes→symbolic, two-stage, 2022), SongComposer, GETMusic (track-conditioned), NotaGen (LLM generating sheet music), structure-aware generation surveys (e.g., "Motifs, Phrases, and Beyond," 2024) | Directly validates your architecture: *structured intermediate representation → audio* is the direction research is moving, and **long-range structure control is still an unsolved problem** (see T-ISMIR "Steerable Music Generation…," 2024) |

**Takeaway:** Don't invent from zero. Design your schema as a **JSON-native superset** drawing on MEI's semantic rigor + JAMS' web-native ergonomics, with form/motif/theme/variation as first-class entities. Existing formats describe *fixed* works; yours would describe a *space of valid renditions* (constraints, variation rules, stems/hooks as motifs). That inversion is the novel core.

## 2. The Composer Interface (visual / node-based authoring)

| Prior art | What it is | Relevance |
|---|---|---|
| **OpenMusic** (IRCAM, open source) | Node-based visual programming (Lisp) for composition, analysis, research | The canonical prior art for a node-based composition environment; decades of patches encode compositional processes |
| **PWGL** (Sibelius Academy) | Node-based visual composition language | Same lineage |
| **Opusmodus** | Commercial algorithmic composition environment; OMN scripting; MusicXML in/out | Most commercially polished CAC tool; shows market size is niche but real |
| **Max/MSP + RNBO, Pure Data** | Node-based audio patching; RNBO compiles patches to web/embedded | Proven path for shipping node-based audio graphs to the browser |
| **Common Music, AC Toolbox, Symbolic Composer** | Code-based algorithmic composition | Historical depth of the category |
| **Modern commercial: Suno Studio** (browser DAW, launched Sept 2025 after Suno acquired WavTool, June 2025), **Splice Create**, **Ableton/Max for Live**, **Orb Composer** | AI-assisted DAWs | The browser-DAW-with-AI space is heating up fast; Suno is moving into the exact "compose → render" loop |
| **DAWs proper** (Sibelius, Finale, Dorico, FL Studio) | Score/arrangement authoring | Users you want to win already live here; MusicXML/MIDI import is table stakes |

**Takeaway:** Node-based composer tools have a 30-year academic lineage and a small but loyal user base. Your differentiator can't be "node-based composition" — it must be **schema→live rendition fidelity** and **distribution**. Interop (import/export MusicXML, MIDI, maybe MEI) is essential for adoption.

## 3. The Generative Audio Engine (schema → real-time audio)

Three families:

**A. Audio-native song generators (prompt → finished track):** Suno, Udio, Google MusicLM/MusicFX, Meta MusicGen/AudioCraft (open source), Stable Audio, Riffusion, OpenAI Jukebox (archived). These ignore explicit structure — the well-documented weakness your schema directly addresses.

**B. Symbolic-first composers (schema/notes → audio):** AIVA (classical/film, editable scores), Amper Music (acquired by Shutterstock, defunct), Jukedeck (acquired by ByteDance, defunct), DAACI (symbolic generative composition engine), Soundraw, Boomy. Two high-profile deaths in this family are a warning about B2B/licensing economics, not the tech.

**C. Real-time adaptive engines (closest to your "interprets in real time"):**
- **Endel** — patented generative engine rendering artist-provided source material into endless adaptive soundscapes; artist collaborations (James Blake, Ta-ku, Grimes); 4M+ downloads; Berlin/LA. **Closest commercial prior art to your engine+front-end concept.**
- **LifeScore** — human-composed/recorded building blocks dynamically assembled by proprietary engine; advisors include Tom Gruber (Siri co-creator); scored an Emmy-winning series. Your film-score analogy is literally their pitch.
- **Reactional Music** (Stockholm) — "programmable, rights-compliant music infrastructure" for games; €2.5M EIC grant (June 2026); Unity award nominee.
- **Melodrive** — "deep adaptive music" for games; real-time emotionally-variable generation.
- **AiMi** — artist-driven adaptive electronic music app; listeners steer energy of an endless artist "experience."
- **Game middleware** — Wwise, FMOD, Elias: rule-based interactive music (non-AI) proves the "composer defines system, engine renders variants" model at massive scale.

**Takeaway:** Endel/LifeScore/AiMi validate the *engine* and the *artist-material-in, infinite-versions-out* model — but they keep composers' material proprietary and output functional/ambient music. Reactional validates rights-first infrastructure. Your differentiation: **an explicit, inspectable, portable schema** (none of these expose one) and **rendition as a listener choice** rather than context adaptation.

## 4. The Listener Front End ("pick a composer, pick a version")

| Prior art | What it is |
|---|---|
| **Udio × UMG "Starstruck"** (announced Oct 2025, due 2026) | Licensed platform letting fans generate covers/remixes/new tracks from *opted-in* artists and recordings. **This is your concept built inside a label walled garden — the single most important competitive signal.** |
| **KLAY / Klay Vision** | "Large Music Model," licensed by all three majors; positions as licensed "active listening" |
| **Suno** | Covers, Personas (style consistency), genres-as-presets; Studio DAW |
| **Hook, MashApp** | Licensed fan remix/mashup platforms (stem-level, not generative) |
| **Endel / AiMi / Mubert Play / Brain.fm** | Listener-facing generative streaming (functional/adaptive) |
| **App albums** | Björk's *Biophilia* (2011), Brian Eno apps (Bloom, Scape, Reflection), Radiohead's *Polyfauna*, RjDj — albums as generative apps; all commercially niche |

**Takeaway:** The "listener chooses the rendition" UX is being built by labels (Starstruck) as a closed, catalog-tied system. The whitespace is an **open, composer-first marketplace** where the schema (not the master recording) is the asset — closer to how game engines middleware works than to how streaming works.

## 5. Distribution Paths (standalone-first, no DSP dependency)

Since the generative engine renders output audio you control, you are not dependent on any existing streaming service's developer program:

- **Standalone streaming surface:** your own app/web player delivering live renditions. This is the path Endel, Mubert, AiMi, and Brain.fm all took — none of them depend on a DSP.
- **DSP distribution of captured renditions:** render fixed versions and distribute them as normal releases via an aggregator (DistroKid, CD Baby, etc.) or a DDEX-compliant pipeline. Captured renditions act as a marketing funnel back to the live experience.
- **More permissive DSP APIs:** Deezer, SoundCloud, and Audius (decentralized) historically offer friendlier third-party access than the biggest closed platforms.
- **Caution on big-platform APIs:** the largest DSPs have been steadily restricting developer access (reduced endpoints, small dev-app user caps, high bars for public access). Use them, if at all, for optional companion features — never as core infrastructure.

## 6. Legal & Rights Landscape (critical for "covers"/"artist lookalikes")

- **Label lawsuits → licensed future:** UMG/Sony/WMG sued Suno & Udio (June 2024). Settlements: UMG×Udio (Oct 2025 → licensed platform), WMG×Udio, WMG×Suno (Nov 2025, incl. Suno acquiring Songkick); Sony still litigating (ruling expected summer 2026); AFM union suing UMG/WMG over the deals. Direction of travel: **generation tied to opted-in, licensed source material.**
- **"Artist lookalikes" is the riskiest feature:** voice/likeness imitation implicates right-of-publicity law (e.g., Tennessee ELVIS Act, 2024), the proposed federal NO AI FRAUD Act, and DSP policies banning unauthorized impersonation. Mitigate with **genre/era/style presets** ("80s synth-pop ballad") and **composer-authored renditions** rather than artist likeness.
- **Covers/derivative works:** audio-only covers can ride US compulsory mechanical licensing (via the MLC), but *AI-generated derivative renditions* and any video/sync use sit outside the safe harbor; expect to need direct licenses.
- **Copyrightability:** purely AI-generated output isn't copyrightable (US Copyright Office guidance), but a **human-authored schema + human selection/arrangement of renditions** materially strengthens the authorship claim. Your architecture is unusually well-positioned here — the schema is a registrable musical work.
- **DSP enforcement against AI content:** major streaming services tightened enforcement against AI spam/impersonation (2025) and are adopting DDEX-style AI credits disclosures. Generative releases are generally allowed if properly disclosed and non-infringing, but mass-uploaded AI content gets de-prioritized or removed.
- **Freedom to operate:** Endel, LifeScore, and Reactional hold patents around adaptive/generative music. Before building the engine, run an FTO review on real-time generative adaptation patents.

## 7. Gap Analysis — where "Muse" can be genuinely new

1. **The schema as canonical, portable release artifact.** MusicXML/MEI encode fixed scores; AIVA/DAACI keep structure internal; Endel/LifeScore keep source material proprietary. An open, inspectable "generative score" standard + registry is unclaimed.
2. **Rendition as first-class, listener-selectable object.** Starstruck (label-gated), Hook (stem remixes), Endel (context-adaptive, not user-chosen styles) all approximate but don't deliver an open "one composition, many sanctioned renditions" marketplace.
3. **Structure-faithful real-time generation.** Enforcing motifs/themes/form in generation is still an open research problem (T-ISMIR 2024, structure-modeling surveys) — a defensible technical moat if you solve it, and your schema gives the model the scaffolding Suno/Udio lack.
4. **Composer-first economics.** Middleware-style model (composers publish schemas, renditions are licensed derivatives) vs. label-first model — aligns with the post-settlement industry's need for provenance and opt-in material.

**Main risks:** major-label walled gardens absorbing the rendition market; closed DSP platforms and anti-AI-spam enforcement limiting distribution; real-time generation compute costs; patent FTO; niche composer-tool adoption (see: Amper, Jukedeck).

## 8. Suggested Next Steps

1. **Brand:** use your own name ("Muse" or similar) and build a standalone product; treat existing streaming services as later integration/partner targets.
2. **Schema v0:** JSON-native spec; import MusicXML/MEI/JAMS concepts; model form, themes, motifs, variations, constraints, and *rendition hooks* (tempo/key/style/timbre ranges). Publish it openly — openness is the moat.
3. **Engine MVP:** condition an open model (Meta AudioCraft/MusicGen melody conditioning, Stable Audio Open) on schema-derived structure; measure motif-recall/structure fidelity as your core metric.
4. **Composer tool:** web node editor (React Flow / LiteGraph class UI) compiling to the schema; import MusicXML to bootstrap.
5. **Listener MVP:** single page, one schema, 4–6 rendition presets ("genre covers," not artist lookalikes), real-time-ish switching.
6. **Community validation:** OpenMusic/Opusmodus users, generative-music artists (Eno-school), game-audio composers (Wwise/FMOD mindset is your best mental model).
7. **Legal groundwork:** FTO patent review (Endel/LifeScore/Reactional), plan licensing posture (licensed training + opt-in source material), DDEX disclosure compliance if distributing to DSPs.

---

---

## Appendix — 2026-08-25 re-survey: DAW-native AI and the conductor question

Scope: what shipped in DAWs/production tools since the original review, and
whether any prior art exists for the current architecture (score + seed →
LLM conductor → dense performance mockup → sample render). Sources: vendor
release notes and press (Ableton, Apple/Logic, Image-Line, Steinberg, Avid,
PreSonus, Suno, BandLab), plus the expressive-performance research line
(CPJKU, ISMIR/ICASSP/arXiv). Full query trail in session run
20260824-1032-xjzf.

### What the DAWs actually shipped (2025–2026)

| Tool | AI feature | Score-aware? | Emits performance data? |
|---|---|---|---|
| Ableton Live 12.x | stem separation to new tracks | no | no |
| Logic Pro 11→12 | AI Session Players (bass/keys jam to chord track), Stem Splitter, ChatGPT integration | chord-track aware, not score-aware | plays MIDI in-session; no exportable mockup |
| FL Studio 2026 | Gopher AI assistant (build patterns, set BPM, route/name tracks via chat) | no (DAW-control agent) | no |
| Pro Tools 2025.6 | Splice search-with-sound, speech-to-text | no | no |
| Cubase 15 | AI stem separation, revised expression maps | no | no |
| Studio One Pro 7 | neural tempo detection, stem extraction | no | no |
| BandLab | Auto Mix, Voice Cleaner, text-prompt effect chains, Aiode acquisition | no | no |
| Suno Studio (ex-WavTool) | browser DAW, AI-MIDI generation, chat operation | no | no (in-browser generation) |

**Read: the entire commercial DAW layer converged on stems, chat control,
and mixing assistants. None of it parses a score; none of it emits an
expressive session file.**

### DAWproject adoption (the open session format)

Real but patchy: Cubase 14+ and Studio One import/export it, Bitwig is
native, and the forums are full of edge-case bugs (tempo maps dropped on
one export path, CC64 sustain missing, VST inserts not translating). The
format carries what a mockup needs (tempo track, MIDI CC, MPE). **No AI
tool emits it.** The D20 founder-gate on any DAWproject export path
stands; the adoption data says the export story would be genuinely useful
to producers *and* genuinely leaky, exactly as decided.

### The expressive-performance research line (closest relatives)

- **Basis Mixer / Con Espressione** (Cancino-Chacón, CPJKU): score
  features → tempo/dynamics via learned basis functions; precomputed
  per-note parameter vectors. The direct ancestor of the mockup concept —
  but a *trained* performance model, not an LLM, and CSV not session
  files. (The spike already cites it; still the right lineage.)
- **VirtuosoNet** (Jeon et al.): score → tempo/timing/articulation/
  velocity deviations; pre-trained form only in the wild.
- **S2A** (ICASSP 2025, tangjjbetsy): integrated score → expressive
  performance MIDI → audio.
- **MIDI-GPT / MIDI-VALLE / Midi-LLM** (2024–2026): controllable multitrack
  MIDI generation, neural-codec performance synthesis, text→MIDI finetunes.
  Midi-LLM is the closest to "an LLM touches performance parameters" — but
  it's a finetuned generator, not a general model reading a score + seed.

**Read: trained models do score → expressive MIDI; nobody uses a general
LLM at inference time as the conductor, with sanctions/assertions bounding
the output and a session-file mockup as the artifact.**

### What this confirms about the current architecture

1. **The conductor role is unclaimed.** The gap the original review found
   ("nobody owns the full loop") persists in the new shape: DAWs went to
   stems/chat, research went to trained renderers. LLM-as-conductor with
   assertion-bounded mockups has no public prior art.
2. **The mockup-as-session-file framing is validated from both sides:**
   Basis Mixer proves the parameter vocabulary; DAWproject proves the
   format can carry it; neither is connected to an LLM.
3. **Risk watch:** Logic's Session Players normalize "AI plays along in
   the DAW" culturally — useful for the event's legibility ("can a machine
   conduct Beethoven?" lands on an audience that has now heard of AI
   session musicians). Suno Studio's "AI Music Production OS" framing is
   the closest rhetorical competitor; its axis is creation, ours is
   interpretation — the Gould/Bernstein controversy has no analog in
   text-to-audio.

### New entries for the tech-stack watchlist

- **DAWproject** — format capable of carrying a mockup (tempo, CC, MPE);
  adoption now real (Cubase 14+, Studio One). Export stays founder-gated
  per decision-log D20.
- **S2A / Basis Mixer line** — the trained-renderer comparison class for
  L3 A/B listening (LLM reading vs trained renderer on the same score is
  a legible demo).

---

## Key Sources

- MEI: music-encoding.org/about; LoC format description (fdd000502)
- MusicXML/MEI comparison: opensheetmusicdisplay.org blog; Michael Good, "Lessons from the Adoption of MusicXML"
- OpenMusic: openmusic-project.github.io; Opusmodus: opusmodus.com
- Structure in symbolic generation: arXiv 2403.07995 ("Motifs, Phrases, and Beyond"); T-ISMIR "Steerable Music Generation which Satisfies Long-Range Dependency Constraints" (doi 10.5334/tismir.97); constraint-based composition: Anders (SMC 2017)
- Generative engines: mubert.com; endel.io; tomgruber.org/advisory/lifescore-story; reactionalmusic.com; Melodrive (Defold forum / Medium "The Sound of AI")
- Label/AI settlements: Music Business Worldwide; dubspot blog "AI Music Licensing Explained (2026)"; Contrary Research Suno report

---

## Appendix — 2026-09-21 re-survey: container, rights, and rejection discipline

Scope: the 2026-08-25 appendix covered the **research line** (trained
renderers vs. an LLM conductor). This appendix covers the three areas it did
not: **(1)** the container as a standard object, **(2)** the interpretation
space against the *performance-markup* formats, and **(3)** the assertion /
gate discipline against its prior art. Same discipline as the rest of this
repo — a claim that survives a search is a candidate, not a finding.

### A. The container — each member has established prior art

`.mu` is a zip of `manifest.json` + `roll.bin` + `seed.bin` (+ optional
`performances/`). Each member maps onto a mature standard elsewhere:

| Prior art | What it provides | What it lacks vs `.mu` |
|---|---|---|
| **Nanopublications** (RDF named graphs: assertion + provenance + publication-info; signed, citable) | assertion + provenance + manifest as one machine-readable, attributable object | no authored variation space; no executable checks |
| **RO-Crate 1.3** (research data + metadata + provenance; Workflow RO-Crate) | packaging content with provenance and workflow record | checks live in the pipeline, not the crate |
| **ERC — Executable Research Compendium** (o2r; Nüst et al., D-Lib 2017) | container + metadata + **executable** reproduction | the executable part is the *analysis*, not a *trust predicate* |
| **C2PA Content Credentials** (v2.3, 2026; X.509-signed manifest) | signed provenance: who, which tools, AI disclosure, tamper-evident | provenance only — no variation, no predicates on content |
| **W3C ODRL 2.2** | rights **policy**: permissions / prohibitions / constraints / duties | governs actions *on* content, not variation *of* interpretation |
| **in-toto / SLSA** (CNCF) | signed checks travel with the artifact; a signed layout defines expected inspections | the unit is *build provenance*, not content-level trust |

**Read:** the container is a **recombination, not an invention**. That matters
less than it sounds — formats win by adoption, not by being first. But it
implies a design rule worth recording: the manifest should *align* with
**C2PA**, the rights model with **ODRL**, and any attestation envelope with
**in-toto**, rather than inventing three parallel formats with no ecosystem.
The EU AI Act Art. 50 machine-readable marking mandate (in force 2026-08-02)
pushes the same way. No action proposed here; recorded for the launch-position
and grant narratives.

### B. The interpretation space — MPM is the nearest neighbour

The 2026-08-25 appendix covered EPR *research* (Basis Mixer, VirtuosoNet, S2A,
Midi-LLM). It did **not** cover the *performance-markup* formats, which are the
closer relatives for `seed.bin` specifically:

- **MPM — Music Performance Markup** (Berndt; MEC 2021/2022; `meico`
  framework; MPM Toolbox). *"A format dedicated to describe and model musical
  performances in large detail in the manner of a construction kit… built upon
  a series of mathematical models that capture performance features such as
  continuous tempo and dynamics transitions, articulations, and metrical
  accentuations."* This is the nearest prior art to `seed.bin` and the one a
  reviewer will reach for first.
- **PML — Performance Markup Language** (n-ISM): score + logical performance +
  event-level score↔performance correspondences.

The distinction that survives:

| Approach | Where interpretation lives | Inspectable | Portable | Bounded by author |
|---|---|---|---|---|
| MPM / PML | in a *description of a performance* | yes | yes | no — describes, doesn't license |
| EPR (Basis Mixer, RenderBox, Midi-LLM) | model-internal latent / text prompt | no | no | implicitly, not declared |
| Constrained decoding | decoder constraints at generation time | partly | no | yes, but code-side |
| **`seed.bin`** | **authored, bounded, licensed document** | **yes** | **yes** | **yes, by construction** |

MPM/PML describe *what a performance was*; EPR encodes *a model's capability*;
constrained decoding enforces *at generation time*. None makes the
interpretation an **authored, portable, bounded document that constrains a
space and gates conforming instances**. The expected objection is "this is MPM
plus a licence"; the table above is the answer, and it should be stated in
`FORMAT_SPEC.md` §5 rather than left to inference.

### C. The assertion / gate discipline — novel as a convention

Four established bodies of work surround the repo's "a gate that cannot fail is
not a check":

- **Mutation testing** (Jia & Harman, IEEE TSE 2010): measures whether a suite
  detects injected faults. The repo's rule is the **mirror image** of an
  *equivalent mutant* — a mutant no test can kill. The mechanism is decades
  old; the rule *makes it per-check and mandatory*, which mutation testing
  does not.
- **Certifying algorithms** (McConnell/Mehlhorn/Näher/Schweitzer, 2011) and
  **proof-carrying code** (Necula, POPL 1997): producer ships a cheap witness,
  consumer validates it. Assertions-travel-with-the-artifact is this move,
  generalized from safety proofs to trust predicates.
- **Metamorphic / property-based testing** (Chen et al., ACM CSUR 2018):
  correctness as relations rather than reference outputs — the direct answer
  to the no-oracle problem.
- **Negative controls / blank-and-LOD calibration**: standard in metrology and
  clinical chemistry; a negative result is uninterpretable without a
  demonstrated detection floor.

**Verdict:** mechanisms established; the **convention** (deterministic-only,
travels inside the artifact, composable, and **every assertion ships a fixture
that makes it fail**) is unclaimed as a standard. This is the shape SLSA
occupies — a convention others adopt — not a patentable mechanism.

### D. What this does *not* change

No format, spec, or scope change follows from this survey. In particular:

- **No new container work.** The container is a recombination; the alignment
  notes in §A are launch-positioning, not engineering tasks.
- **The novel core is unchanged and now better supported.** The claim that
  survives is the **gated, licensed interpretation space** (§B) — consistent
  with the 2026-08-25 finding that the conductor role is unclaimed. The moat
  remains the corpus ladder, the assertion discipline, and the staged event.
- **§7's gap 1** ("an open, inspectable 'generative score' standard is
  unclaimed") should be read as scoped to the *interpretation space*, not the
  container. The container is an assembly; the space is the novel object.

### E. Sources (this appendix)

- MPM: axelberndt.github.io/MPM; Berndt, "Music Performance Markup: Format and
  Software Tools Report," MEC 2021, pp. 57–63; `meico`
- PML: n-ism.org/Projects/pml.php
- Nanopublications: nanopub.net/guidelines/working_draft
- RO-Crate: researchobject.org/ro-crate
- ERC: o2r.info/erc-spec; Nüst et al., D-Lib Magazine, Jan 2017
- C2PA: c2pa.org (spec v2.3, 2026)
- ODRL: W3C ODRL Information Model / Vocabulary 2.2 (2018)
- in-toto / SLSA: slsa.dev; in-toto attestation framework
- Mutation testing: Jia & Harman, IEEE TSE 2010
- Certifying algorithms: McConnell, Mehlhorn, Näher, Schweitzer (2011);
  proof-carrying code: Necula, POPL 1997
- Metamorphic testing: Chen et al., ACM CSUR 2018
- Marking mandates: EU AI Act Art. 50 (in force 2026-08-02); GB 45438-2025

*Compiled with literature-search tooling; two academic APIs were rate-limited
during the sweep, and patent FTO (§6) remains open. "No direct prior art
found" is a search result, not proof of absence.*
