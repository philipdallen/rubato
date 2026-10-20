# muse_rehearse — R2 rehearsal directives

Typed natural-language directives compiled to seed revisions (design:
[docs/design/r1-rehearsal-directives.md](../../docs/design/r1-rehearsal-directives.md)).
The conductor's "*bar 44, violins more gentle*" becomes a seed revision
whose `extends` is the hash of the directive that produced it — the
directive is the lineage root of that rehearsal branch.

## Usage

```bash
python3 tools/muse_rehearse/cli.py dry-run <seed.yaml> "<directive>"
python3 tools/muse_rehearse/cli.py score-dry-run <seed.yaml> "<directive>"
python3 tools/muse_rehearse/cli.py commit <seed.yaml> <slug> "<directive>"
```

- `dry-run` prints the param diff the commit would make — writes
  nothing. The mockup/stand-in is never invoked (seed-to-seed param
  diff, so the loop is fast and deterministic).
- `score-dry-run` compiles the candidate in memory and probes it against
  the base seed — budget fit, assertions, coverage, the gate — and
  prints the base/candidate comparison. This is the score the dry run
  cannot show (which knobs turned vs did it help). Also writes nothing;
  the payload is sized to fit the runner's stdout window.
- `commit` writes the directive file
  (`seeds/<work>.directives/<slug>.directive.txt`) and the compiled
  revision, stamping `extends: sha256(directive bytes)` +
  `operation: muse_rehearse@1`.

## Grammar (five verbs, per R1)

| Verb | Compiles to | Example |
|---|---|---|
| `rebalance` | part-scoped energy (`params.part_gains`) | `rebalance: bring P1 up at bar 8` |
| `phrase` | a `tempo_flex` variation point | `phrase: quieter into development` |
| `tempo_arch` | `params.tempo` bounds (era budget) | `tempo_arch: wider` |
| `rubato` | onset-offset/rubato budget | `rubato: more` |
| `hold` | a `tempo_bounds` assertion | `hold: ticks 0-480` |

Regions resolve to ticks three ways: a **bar reference** (`bar 8`,
`bars 5-7`) computed from the IR meter map; a **tick range**
(`ticks 480-960`); or a **variation-point label** the seed already
defines. The conductor never computes ticks by hand. Unresolvable
regions, unknown verbs/parts, and two verbs in one directive are parse
errors listing the valid vocabulary.

## Branch semantics

A directive commits a new **rehearsal branch**: the compiled revision's
`extends` is the *directive's* hash (the root of that branch), not the
prior seed revision. So the lineage walk from a rehearsal revision reads
`revision → directive (root)` — a short branch, distinct from the
v1→v2→v3 growth chain it forked from. Both are first-class in the same
`extends`/`seed_hash` hash convention; the Study pane shows the
rehearsal log, the iteration history shows the growth chain.

## Tests

`cd tools && python -m pytest muse_rehearse -q`. Spec:
[tests/closed_20260826-110000_r2-rehearsal-pane.md](../../tests/closed_20260826-110000_r2-rehearsal-pane.md).

## Dependencies

`muse_seed` (seed model/validate), `muse_probes` (param_diff for
dry-run), `muse_lineage` (hash + store), `muse_ir` (meter map for bar
resolution).
