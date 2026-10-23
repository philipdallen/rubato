# E3 — The recording (design doc, draft)

**Phase 5 — The event. Status: draft (publication plan, issue #211;
publish itself blocked on the staged event).**

## Purpose

Document the event; publish the recording. The controversy is the coverage —
the recording carries it.

## Dependencies

- **Upstream:** E1 (content), E2 (staging — the venue plan's recording-
  rights clause and on-screen live/`.perf` labeling are inputs here).
- **Downstream:** none — the terminus of the plan.

## Scope

- **Inputs:** the staged event (house audio/video per the E2 venue
  agreement), the performed `.mu` + certified `.perf`, the deliberation
  trace.
- **Outputs:** this publication plan now; the published recording +
  provenance-complete manifest after the event.
- **Non-goals:** platform/streaming strategy (explicitly downstream of the
  event; see vision), social-media operations, pressing physical media.

## Publication surface (open question, answered)

Recommendation: **two surfaces, one bundle.**

1. **The event film** — the evening as staged: three acts, the visible
   machine, the three-layer projection, the narration. Published on a
   public video surface. This is where the controversy lives; the
   deliberation trace is inherently visual, and the Gould/Bernstein
   argument needs an audience that can watch the machine think.
2. **The release bundle** — audio recording + `.mu` + manifest +
   deliberation trace, downloadable from the project's own site. The
   bundle *is* the provenance story: anyone can inspect what was played,
   what was sanctioned, and what was live. Public-domain corpus keeps the
   bundle unencumbered.

Explicitly deferred: streaming DSP distribution (vision: "a streaming
service is explicitly not the product; the platform is downstream") and
physical media. Both are post-event business decisions, not E3.

Decision criteria: provenance completeness (the bundle carries everything
an auditor needs), fidelity to the event (film shows what actually
happened, including live-vs-`.perf` labeling), and no rights encumbrance
introduced by the surface itself.

## Release format

- **Audio:** 24-bit/48 kHz FLAC master (the archival artifact) + 320 kbps
  MP3 reference. Stereo house mix; the spatialized/array mix archived if
  the venue rig captures it.
- **Video:** the multi-cam house feed + the projection scrim feed as a
  picture-in-picture track, so the trace is readable in the film.
- **Digital liner notes:** the `.mu` performed, its manifest (plaintext),
  the deliberation trace (E2 projection layer 3 source), and the program
  notes (which carry the manifest in full, per the E2 plan).

## Provenance-complete recording manifest

A plaintext recording_manifest.json (planned artifact; this doc is a draft
publication plan and the event has not happened yet) ships in the bundle,
following the `tools/muse_mu/manifest.py` conventions (FORMAT_SPEC §3; D13:
provenance mandatory; D18: SHA-256 content hashes, HMAC-SHA256 signature):

- `work`: the performed `.mu` content hash, title, composer, source
  edition, license.
- `event`: venue, date, the E2 event-plan version staged.
- `performance`: seed settings; per-movement declaration of **live
  deliberation vs. certified `.perf`** (the E2 on-screen labeling persists
  into the recording — the listener can audit exactly what was computed
  in the room); deliberation trace hash.
- `ai_involvement`: `none | assisted | generated` with `tools` listed —
  same vocabulary as the work manifest.
- `credits`: recording engineer, narrator/dramaturg, founder as encoder.
- `hashes`: SHA-256 of every file in the bundle; `signature`: HMAC per
  D18.
- `license`: the recording's license (distinct from the work's license;
  the performance/recording is a new artifact).

## Publish checklist (post-event, executes the plan)

1. Mix/master the house recording; archive raw stems.
2. Assemble the bundle: audio, film, `.mu`, manifest, trace, liner notes.
3. Generate recording_manifest.json (planned); hash and sign every member.
4. Verify the manifest by hand (plaintext — rights are for lawyers) and by
   tooling (hash check against the bundle).
5. Publish film to the video surface; bundle to the project site.
6. Press/argument kit: the manifest, the Gould/Bernstein framing, and the
   trace highlights — the controversy is the coverage.

## Open questions

- **Video surface choice** (self-hosted vs. established platform) —
  decided at publish time against the press strategy; not a format
  question.
- **Recording license** — the work is public domain; the recording's own
  license (open vs. rights-reserved) is a founder decision at publish.

## Acceptance criteria

- Publication surface chosen (this document). ✔
- Provenance-complete recording manifest specified. ✔
- Remaining gate (not agent-achievable): the staged event exists, then the
  checklist above runs — see blockers/open_20260824-*.md on #211.
