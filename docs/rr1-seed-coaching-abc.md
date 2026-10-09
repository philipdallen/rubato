# RR1 — Seed-level coaching A/B/C (bwv227.1)

**Status: complete (seed-level lane).** Task [#380], `kind:experiment`.
Run `20261009-1940-Ph36`, branch `main`.

First controlled experiment from the rendering-research roadmap §9, run at the
**seed level**. One short public-domain passage — the `bwv227.1` chorale already
under `seeds/` — compiled into three seed revisions by `tools/muse_rehearse`
(the R2 directive compiler). Score, instrument preset, renderer and every other
setting are held fixed; the only variable is the coaching directive. The
deliverable is the measured delta, not audio.

## Design

| Rev | Coaching | Directive file | Compiled seed |
|---|---|---|---|
| **A — Baseline** | none | — | `seeds/bwv227.1.seed.yaml` |
| **B — Coached** | one whole-work direction | `seeds/bwv227.1.directives/rr1-b-coached.directive.txt` | `seeds/bwv227.1.v5.seed.yaml` |
| **C — Repeated** | B + one local correction | `seeds/bwv227.1.directives/rr1-c-corrected.directive.txt` | `seeds/bwv227.1.v6.seed.yaml` |

- **B directive:** `phrase: build toward the cadence, then relax the tempo`
  → whole-work `tempo_flex` variation point.
- **C directive:** `rebalance: bring P4 up at bar 5`, compiled on top of B
  → `part_gains.P4` lift, scoped to bar 5 (ticks [32, 40)).

The C correction is a part-scoped `rebalance`, not a second `phrase`. The S3.4
variation-point validator forbids overlapping tick regions, and B already claims
the whole work `[0, 152)`; a second phrase region would collide. A part-gain
edit expresses the "one local correction to a single measure" intent without a
region, and `bar 5` resolves through the IR meter map.

## Delta table (parm-diff probe, seed-to-seed)

Artifacts: `docs/workbench/data/seeds/bwv227.1{,.v5,.v6}.probes.json`.

| Revision | Changed section | From → To |
|---|---|---|
| A → B | `variation_points` | `[]` → 1 × `tempo_flex` region `[0, 152)`, budget 0.2 |
| B → C | `params.part_gains` | `{}` → `{P4: 1.1}` (+10 % on the bass) |

Tempo bounds, energy, density, philosophy and assertions are **unchanged**
across all three (the coaching touched only what the directives name).

## Measures

**1 — Did the requested change happen? Yes.**

- B: directive compiled to a whole-work `tempo_flex` variation point — the
  "shape the phrase" intent maps to the only R2 knob that owns tempo shaping
  over a region.
- C: directive compiled to `part_gains: {P4: 1.1}`, the requested local lift.

**2 — Correct scope? Yes.**

- B's region is the full work `[0, 152)`; the request was a whole-work phrase
  arch, so full scope is correct.
- C's region resolves to bar 5 only `[32, 40)` (of 20 bars / 152 ticks); the
  `part_gains` delta is the only change B → C, so the correction stayed local.

**3 — Score compliance: green.**

| Revision | `muse_seed_cli validate` | W4 diff @ tolerance 0 | assertions |
|---|---|---|---|
| A | schema OK / assertions OK / validates vs work OK | n/a (baseline) | register + tempo_bounds pass |
| B | all OK | fidelity `missing=0 extra=0` | register + tempo_bounds pass |
| C | all OK | fidelity `missing=0 extra=0` | register + tempo_bounds pass |

The `fidelity_guard` probe is the W4 diff @ tolerance 0 reading (score notes vs
mockup notes): 279 score notes, 279 mockup notes, 0 missing, 0 extra, for both
B and C — the coaching changed interpretive parameters only, never a score note.

**4 — Repeatability: deterministic.**

`determinism` probe: identical generation path twice → identical artifact
(`stable: true`, 279 notes) for A, B and C. Lineage walks verified: B's
`extends` hash matches the B directive file; C's `extends` hash matches the B
seed (the compiled revision), so C carries the full coaching chain
(A → B → C).

**5 — Listening: NOT RUN.** Measure 5 is human (D11) and out of scope for this
seed-level experiment. No render was produced and no ear was put on it.

## What is seed-level only

This experiment measures the seed → seed delta and score compliance. It does
**not** measure whether the change survived realization into a render — the
render-level survival column (the distiller `Interpretation` fields, "did the
change survive the render") is **RR2-gated** by design (`tools/muse_study`
render lane reports `stand-in-blocked` until the L1 live loop runs). No
conclusion about audible effect is drawn here.

## Reproduce

```bash
python3 tools/muse_rehearse/cli.py commit seeds/bwv227.1.seed.yaml rr1-b-coached "phrase: build toward the cadence, then relax the tempo"
python3 tools/muse_rehearse/cli.py commit seeds/bwv227.1.v5.seed.yaml rr1-c-corrected "rebalance: bring P4 up at bar 5"
python3 tools/muse_seed_cli/cli.py validate seeds/bwv227.1.v6.seed.yaml corpus/bach/bwv227.1.mxl
python3 tools/muse_probes/cli.py seeds/bwv227.1.v6.seed.yaml --prior seeds/bwv227.1.v5.seed.yaml
```

_This record was written by an AI agent (OpenHands) on behalf of the repository owner._
