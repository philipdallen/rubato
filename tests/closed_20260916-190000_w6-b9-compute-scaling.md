# Test spec — W6 B9 compute scaling (task #317)

Written 2026-09-16 by the completing agent, per TASK_WORKFLOW §6.

## What landed (behavior under test)

`tools/muse_diff/diff.py` gained a second pairing path, selected on
tolerance:

| Path | Complexity | Selection |
|---|---|---|
| `_diff_exact` | **O(n_a + n_b)** | `tolerance_ticks == 0` (the chain's own call) |
| `_diff_within_tolerance` | greedy nearest-onset search | `tolerance_ticks > 0`, unchanged |

An exact match is fully determined by `(pitch, onset)`, so the exact path is a
bucket lookup (FIFO `deque` per key) instead of the previous scan of every
unmatched `b` note per `a` note. Match key is **pitch + onset only** — `part`
is reported, never matched on, matching the tolerance>0 path. Among equal keys
the lowest `b` index wins, which the FIFO bucket reproduces.

`tools/muse_chain/chain.py`: `DIFF_BUDGET_NOTES` raised 30_000 → 2_000_000 (a
safety ceiling above the corpus, no longer a gate on real work).
`RENDER_BUDGET_NOTES` stays at 30_000 — that gate is output size, not
algorithm (schubert at 24,772 notes already writes a 151 MB WAV).
`cli.py` derives the report's skip sentence from the actual stage reasons
instead of asserting a fixed "over-budget diffs" story.

Coverage: `tools/muse_diff/test_muse_diff.py` — `TestScalingExactPath`, 6 new
tests. Run with `cd tools && python3 -m pytest muse_diff -q` (21 tests).

## Coverage written

1. **Sub-quadratic scaling.** Doubling n=4000 → 8000 must not quadruple the
   time; assert ratio < 3.0 (linear ≈ 2x, quadratic ≈ 4x). Compares scaling
   rather than absolute time, so it is machine-independent; sizes are small
   enough that a regression *fails in ~12s* rather than hanging the suite
   (verified: with the quadratic path restored it reports "ratio 4.26").
2. **Large input completes quickly.** A 40k-note exact diff finishes in
   seconds — above the 30k gate the chain used to depend on.
3. **Duplicate-key tie order.** Three `a` notes and three `b` notes sharing
   `(pitch, onset)` pair without spurious drift, pinning the FIFO bucket
   against a future set/dict refactor silently reordering pairings.
4. **Missing/extra reporting** on the exact path, both directions.
5. **Tolerance-path separation.** `tolerance=0` must NOT match a 5-tick
   offset; `tolerance=5` must, and must classify it `onset-drift` — proving
   the fast path is not silently taken for tolerance>0.
6. **Agreement** between the two paths when onsets are equal.

## Verification that the result is unchanged (the critical claim)

This is a performance fix, not a semantic one, so equivalence was established
**before** relying on the new path: a differential harness ran the new
implementation against the old one, verbatim, over six cases — self-diff,
velocity mutation, pitch mutation, onset-shift, a duplicate-key stress (60
notes forced to one onset), and random removal. Outputs were compared as
`(recall, precision, matched, total_a, total_b, [mismatch tuples])`:

```
self         identical=True  matched=279 mismatches=0
velocity     identical=True  matched=279 mismatches=0
pitch        identical=True  matched=264 mismatches=30
onset-shift  identical=True  matched=269 mismatches=20
dupes        identical=True  matched=221 mismatches=116
dropped      identical=True  matched=254 mismatches=25
```

The existing suite passes **unmodified** (14 pre-existing tests), which is the
stronger half of the DoD's item 2.

## Known gaps (acceptable)

- **`render(P2)` still SKIPs for B9.** Deliberate: it is a ~65-minute,
  multi-hundred-MB output, not an algorithmic limit. Out of scope here and
  recorded as such in #317; it needs its own output/format decision.
- **The scaling test is a timing assertion.** It is guarded (min-of-5,
  scaling not absolute, generous 3.0 threshold against a ~2x expected), but a
  pathologically noisy CI machine could in principle trip it. A
  counter-based assertion (e.g. instrumenting the inner loop) would be
  deterministic; not done because it would mean adding instrumentation to
  production code purely for a test.
- **No B9-scale test in the fast tier.** B9's parse alone is ~9s, so the
  chain test stays slow-tier; the diff fix is covered at 40k notes instead.
- B9's W3 analyzer pass (SIATEC) is unaffected and was already bounded.

## Closed 2026-09-16 (#317, run=20260916-1525-8d06)

Measured outcome: B9 self-diff **>15 min (terminated) → 0.99s**, matching all
239,459 notes at `recall=precision=1.0`. `docs/chain-report.md` regenerated:
B9's `verify(W4)` now reads PASS. `muse_diff` 21 passed; fast tier green.