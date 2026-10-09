# L2 — Performance renderer (design doc)

**Phase 4 — The product. Status: implemented (2026-08-24, #193 →
[tools/muse_render](../../tools/muse_render/)).**

## Purpose

Mockup → audio via sfizz + SFZ samples (SSO/VPO tier). The "worth listening
to" bar — the quality gate spike round 2 established. Critical-path terminus
with L1.

## Architecture (draft)

Three tiers in scope; one declares the build:

| Tier | Library | Integration | Quality |
|---|---|---|---|
| **sfizz** | SFZ player (C API + CLI) | primary | SSO/VPO tier — the "worth listening to" bar |
| **FluidSynth** | soundfont fallback | fallback if sfizz unavailable | GM/baseline |
| **Commercial SFZ** | Spitfire/Vienna/Orchestral Tools | event gate (L5 waiver) | concert-hall | 
|(selected by event budget only) |

**Integration shape:** CLI-first (`sfizz_render_in_place` or
`sfizz_process_and_render`). SFZ per instrumentation (violin/cello/viola/
clarinet/etc.). Sample libraries resolved from environment (SSO/VPO) with
fallback to FluidSynth where available.

**SFZ mapping:** per-part program → SFZ program mapping; all parts mapped
or fallback to GM.

## Dependencies

- **Upstream:** L1 (mockups), P2 (baseline renderer to build above).
- **Downstream:** L3 (comparison listening), E1 (the event render).
- **Critical path:** W1 → W3 → S3 → C1 → C2 → L1 → **L2**.

## Scope (pinned)

- **Inputs:** mockup session files (tempo map, note list, curves).
- **Outputs:** WAV renders to the output directory (CLI emits audio).

## Event log (implementation, 2026-08-24)

- **Landed as the generalization of the SPIKE's `render_sso.py`** — the
  envelope at the pitch frequency with per-part gain and tempo-map
  conversion, packaged over Mockup as the input model.
- **sfizz toolchain** isn't wired; the CLI-first fallback uses the
  envelope path which replaces the `import sfizz` dependency. SPIKE tier
  samples remain the follow-up.
- **Findings on fabric's fallback path were part of the initial test
  focus** — envelope at the pitch frequency with attack/decay
  normalization; replay determinism verified (same input → same bytes).
- **The samples library registration (SSO/VPO) stays pending** — golden
  WAVs on the small/mid tier are the anchor the follow-up should pass.

- **Non-goals:** notation software, video/audio mixing, streaming
  playback (L3 will handle A/B output).

## sfizz/SFZ integration decision (2026-10-09, #396)

Recorded by step 1 of the #382 split (superseded by #396 → #397 → #398). This
resolves the integration shape the wiring step (#397) will use and measures
whether the primary tier can run in the automation sandbox.

**Integration shape — CLI-first.** The wiring uses the sfizz CLI
(`sfizz_render_in_place`), not the C API: the renderer shells out to the binary
and reads back a WAV. This is the doc's "Integration shape" line above, and it
keeps sfizz an optional external tool rather than an `import sfizz` Python
dependency — which is what let the fallback replace `import sfizz` without a
build step. Per-part program → SFZ program mapping is a table from the mockup part's
`instrument` field to `<SFZ_DIR>/<instrument>.sfz`, and any part not mapped to
an SFZ program falls back to the envelope path rather than failing.

**Environment measurement (2026-10-09, automation sandbox, Linux x86-64).**
Commands run and their results:

    $ which sfizz sfizz_render            # rc=1, no output
    $ apt-cache policy sfizz              # N: Unable to locate package sfizz
    $ pip index versions sfizz            # ERROR: No matching distribution found
    $ which fluidsynth                    # rc=1, no output
    $ echo "$SFZ_DIR"                     # <unset>
    $ find . -iname '*.sfz' -o -iname '*.sf2'   # (no repo assets)

sfizz is not installed, not in the apt index, and not on PyPI; the fallback's
other target (FluidSynth) is likewise absent. No SFZ/SF2 assets ship in the repo
(`docs/spike/*.wav` are renders, not samples).

**Sample-library contract for #397.** The wiring reads SFZ programs from
`SFZ_DIR` (a directory of per-instrument `.sfz` files, e.g.
`$SFZ_DIR/violin.sfz`). The repository does not own or ship SSO/VPO samples —
they are multi-GB third-party libraries resolved from the environment, matching
the "samples library registration (SSO/VPO) stays pending" note above.

**Consequence.** #397 can land the wiring (the CLI-first path, the `SFZ_DIR`
mapping table, and a tier probe) and keep the envelope fallback selectable, but
it cannot produce a real SFZ render until `sfizz` plus an SFZ library are
provisioned in the environment. That provisioning is an environment blocker, not
a spec ambiguity; #397 parks with a single `NEEDS:` line naming it if the sandbox
still lacks the toolchain, rather than re-attempting the wiring.

## Open questions (draft-level)

- Split or subgraph: per-part render then sum, or whole-mix render per
  part then sub-graph.

## Acceptance criteria (when promoted to draft)

- Render Bach chorale via SSO strings audibly (not GM-masked).
- FluidSynth fallback when sfizz absent.
- Test spec + CLI exit codes (0 rendered, 1 failure).
