# muse_study — R3 conductor-training study scripts + survival feedback

Precomposed directive sequences (study scripts) keyed to well-known
interpretive issues, plus a per-step survival check that answers *"did
this directive actually do what was asked?"* — how the conductor's ear
gets trained without live musicians. Builds on `muse_rehearse` (R2).
Design: [docs/design/r1-rehearsal-directives.md](../../docs/design/r1-rehearsal-directives.md)
§What R3 builds.

## Usage

```bash
python3 tools/muse_study/cli.py list
python3 tools/muse_study/cli.py run <script> <seed.yaml>
python3 tools/muse_study/cli.py run <script> <seed.yaml> --live
```

`run` compiles each directive step in sequence (the running candidate
carries forward, so steps compound — that's the drill) and reports, per
step, whether the directive's knob landed (`moved`), didn't (`flat`),
or moved the wrong way (`drifted`).

## Two survival lanes: seed-param and render

`check_survival` reports both lanes.

**Seed-param lane.** Maps each verb to the seed knob it should move
(`VERB_MEASURES`) and compares base vs candidate seed params — the
`moved` / `flat` / `drifted` verdict shown first.

**Render lane (RR2, #381).** Asks whether the change survived realization
into a mockup. With the deterministic stand-in — the default — the mockup
is flat regardless of seed, so the lane reports **`stand-in-blocked`**
rather than a misleading `flat`. Pass `--live` (or set `MUSE_L1_LIVE`,
the same gate `muse_grow` uses) to run the real L1 generate loop (#276,
`muse_grow.real_mockup`); it then compares the distilled `Interpretation`
— velocity spread, part gains, curve shape — and reports `moved` /
`flat`.

## The scripts

| Script | Issue it drills |
|---|---|
| `quiet-the-bass` | bass dominates the texture ("quiet the cellos into the development") |
| `phrase-the-pickup` | flat anacrusis; no arch into the downbeat |
| `tempo-architecture` | tempo wanders; the form loses its spine |
| `rubato-calibration` | onset-offset spread mechanical or soupy |

New scripts are added to `SCRIPTS` in `study.py` — a name, the issue
text, and a list of directive steps using the R2 grammar.

## Tests

`cd tools && python -m pytest muse_study -q`. Spec:
[tests/closed_20260826-113000_r3-study-scripts.md](../../tests/closed_20260826-113000_r3-study-scripts.md)
(seed-param lane, #284) and
[tests/closed_20261009-184500_rr2-study-live-render.md](../../tests/closed_20261009-184500_rr2-study-live-render.md)
(render lane, #381). The live path runs offline behind a recorded
`RecordedProvider` fixture, mirroring the `muse_generate` / `muse_grow`
suites.

## Dependencies

`muse_rehearse` (the directive compiler), `muse_seed` (params/budgets),
`muse_ir` (work loading), `muse_generate`/`muse_provider` (the live loop
and its recorded fixture), `muse_distill`/`muse_grow` (`real_mockup` plus
the `Interpretation` fields the render lane compares).
