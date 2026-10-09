# Test spec — RR2 study live render lane (task #381) — CLOSED

**Resolution (RR2 #381, 2026-10-09, run=20261009-1840-i1ts):** landed in
`tools/muse_study/` (study.py, cli.py, README) plus tests in
`tools/muse_study/tests/test_study.py`. Suite:
`cd tools && python -m pytest muse_study -q`.

## What landed

- `_build_mockup(work, seed, mockup_fn=None, provider=None)` →
  `(Mockup, live_flag)`. With `MUSE_L1_LIVE` set and a seed in hand it runs
  `muse_grow.real_mockup` (the L1.11 #276 live loop) and reports `live=True`;
  otherwise it uses the deterministic stand-in and reports `live=False`.
- `_render_survival(base_mockup, candidate_mockup, live)` →
  `(base, candidate, verdict)`. Offline it returns `stand-in-blocked`
  (the stand-in is flat regardless of seed, so a bare `flat` would lie);
  live it compares the distilled `Interpretation` (velocity spread, part
  gains, curve shape) and returns `moved` / `flat`.
- `cli.py run … --live` mirrors the `MUSE_L1_LIVE` gate and prints the
  render lane per step.
- `muse_grow.real_mockup` gained an optional `provider` so the live loop can
  be driven offline by a recorded fixture.

## Tests (render lane)

- `test_render_lane_stand_in_blocked_without_live` — default path reports
  `stand-in-blocked`, not a misleading `flat`.
- `test_render_lane_moved_with_live_mockup_fn` — a seed-dependent mockup_fn
  moves the distilled interpretation → `moved`.
- `test_render_lane_flat_when_mockup_unchanged` — a constant mockup → `flat`.
- `test_live_path_runs_offline_with_recorded_provider` — with
  `MUSE_L1_LIVE` set and a `RecordedProvider` fixture (the
  `muse_generate`/`muse_grow` pattern), the real generate loop runs with no
  network and the render lane produces a live verdict.

## Gate

Fast tier green: `./tools/run_tests.sh`. `muse_study` is now registered in
the runner's `SUITES` (it was discovered by pytest but absent from the
inventory).
