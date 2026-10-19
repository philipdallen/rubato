# Test spec — workbench audio render bridge (issue #243)

Written 2026-08-24 alongside the implementation (13 tests across
tools/muse_audio + tools/muse_render, run=20260824-1032-xjzf).

## Behaviors to verify

- **Stand-in render** (tools/muse_audio/tests/test_audio.py):
  WAV written, valid RIFF/44.1kHz, metadata consistent; duration
  plausible for the work's real tick domain (#246 regression guard);
  seed revisions produce *different* bytes (the arch is audible);
  re-rendering is byte-deterministic.
- **Manifest** (same suite): format marker, per-label accumulation,
  relative paths only, sha256 present and parseable.
- **Schema-dict conversion** (same suite): indexed schema-v1 mockups
  resolve pitch/onset/duration from the score (lossless by
  construction), devices map (attack_sec → attack_ms, swell mean),
  balance/dynamics carried, unknown parts skipped.
- **Live path wiring** (same suite, RecordedProvider — no network):
  live=True routes through muse_generate, full-coverage fixture renders
  279 notes, origin stamped `llm-live`.
- **ppq regressions** (tools/muse_render/tests/test_render.py): ppq=2
  domain renders real durations; default 480 unchanged; ppq survives
  dump/load.

## Deliberately not covered here

- Live Gemini calls in CI (provider convention: live calls are manual,
  fixtures are the gate). The one live render for #243 was produced and
  verified interactively; its evidence is in the issue's done comment.
- DOM/behavior of the new audio panel: covered by the workbench UI QA
  tasks (#229, and #227's suite) — the DOM contract is `.card h3` =
  "Audio — seed revisions", one `.rev audio[src^="/audio/"]` per manifest
  label, graceful onerror note when a WAV is absent.

## Invocation

`cd tools && python -m pytest muse_audio muse_render -q`

---

**Closed 2026-10-19** (issue #418 reconciliation, run=20261019-0741-2g2w): the owning task **#243** is closed as completed; the 13-test coverage it describes landed in `tools/muse_audio/tests/test_audio.py` and `tools/muse_render/tests/test_render.py` (both present). No open `Tests:` issue remains.
