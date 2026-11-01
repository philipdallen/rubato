# Launch protocol — the checkable launch criterion

**Status:** proposed protocol, 2026-11-01. Replaces the by-ear launch criterion
in [../README.md](../README.md) §Component status.

## Purpose

The front page used to say launch-ready "means" three things, one of which was
"one corpus work performed by the LLM player has passed the founder's by-ear
evaluation." That is not a criterion a reader can check: it names no threshold,
no evaluator other than the founder, and no procedure. A reader cannot state
what would pass and what would fail without asking the founder.

This document fixes that. It states the launch criterion as three gates, each
with an observable pass/fail, and it fixes the listening evaluation's rubric,
evaluator pool, and threshold **before** any work is heard — so the founder's
judgment is one input to a stated rule, not the rule itself.

This is a protocol, not a claim that any gate is met. As of this commit all
three gates are open (see §Current state).

## The criterion (three gates)

Launch-ready means **all three gates hold**, each checked against a named HEAD
SHA and each reproducible by a reader.

### G1 — Format spec frozen at v1.0

- **Observable:** `FORMAT_SPEC.md` header reads v1.0 (not "v0 (Design Draft)")
  **and** no construct in the spec is marked deferred-by-evidence.
- **Check:**
  ```bash
  head -1 FORMAT_SPEC.md          # must read: # Rubato Format Specification — v1.0
  ```
  plus a spec-freeze decision recorded in [decision-log.md](decision-log.md)
  (the O1 open decision closed; see §Open items).
- **Currently:** FAIL — spec is v0, `status/trl.json` rates it level 2.

### G2 — Every corpus work round-trips losslessly

- **Observable:** the E2E chain gate passes for **every** work in the corpus
  registry, with the losslessness comparison run against the **source** (not
  only the IR). This closes the parser-coverage gap stated in
  [pipeline.md](pipeline.md) §Phase 1 ("its strength is bounded by parser
  coverage").
- **Check:**
  ```bash
  python3 tools/muse_chain/cli.py --all     # every work: stage PASS, recall=precision=1.0
  ```
  The reader compares the reported works against the registry in
  `tools/muse_chain/` and confirms no work is skipped or budget-excluded.
- **Currently:** PARTIAL — the chain is green and B9 verifies at
  recall=precision=1.0, but the gate is IR-relative; the source-comparison
  closure is not yet the check (see §G2 gap below).

### G3 — One corpus work passes the pre-registered listening rubric

- **Observable:** one corpus work, performed end-to-end by the LLM player and
  rendered by L2, scores at or above the threshold in §Rubric below, evaluated
  by the §Evaluator pool, with the verdict record committed.
- **Check:** the committed verdict record
  (`docs/launch/g3-verdict-<work>.md`) exists, contains the per-dimension
  scores from at least the minimum number of independent evaluators, and its
  computed total is ≥ the threshold.
- **Currently:** FAIL — no such record exists.

## G3 rubric (pre-registered)

The rubric is fixed **before** the evaluation and must not be edited after any
verdict is recorded. A revision supersedes this table in a new commit with a
new pre-registration date; it never edits a recorded verdict.

Five dimensions, each scored 1–5 by each evaluator (1 = fails, 3 = competent,
5 = concert-worthy). Dimension definitions:

| # | Dimension | 1 (fails) | 3 (competent) | 5 (concert-worthy) |
|---|---|---|---|---|
| R1 | **Musical coherence** | Phrasing contradicts the score; texture unreadable | Phrases read correctly; some joins mechanical | A single continuous reading; the work's form is audible |
| R2 | **Interpretive fidelity** | Moves outside the seed's sanctioned space | Stays inside the space; variation is conservative | The space is used with intent; choices are defensible as reading, not noise |
| R3 | **Timbre and balance** | Voices masked or grossly unbalanced | Sections balance; timbres recognizable | Blend and articulation approach a real ensemble |
| R4 | **Determinism of the score** | Score playback differs run to run | Deterministic player output stable | (baseline holds; no regression from G2) |
| R5 | **Worth a hall** | A listener would not sit through it | Worth a small room | Worth staging the event around |

R4 is a gate, not a score: if it is not 5, G3 fails regardless of the total.
This keeps G3 from rewarding an interpretation that broke determinism.

**Weighted total** (max 100):

```
total = 4*(R1 + R2 + R3 + R5) / 4 * 5   ->  normalized to 0-100
      = (R1 + R2 + R3 + R5) / 20 * 100
```

R1–R3 and R5 carry equal weight; R4 is pass/fail. Averaging: each dimension's
score is the **median** across evaluators, then the total is computed from the
medians. Median, not mean, so one outlier cannot carry a work over the line.

**Threshold:** G3 passes when `total ≥ 80` **and** every one of R1, R2, R3, R5
has a median ≥ 3 **and** R4 is 5 for every evaluator. The floor rule stops a
work with one excellent dimension and one failed dimension from passing on
average.

## Evaluator pool (named roles, minimum three)

The pool is defined by **role**, so it can be filled by people without this
document inventing names. Evaluators must be independent of the work's
authoring.

| Role | Who | Why this role |
|---|---|---|
| **Founder** | The repo owner | One data point — carries domain intent, no tie-break authority |
| **Independent musician** | A practising performer or conductor, not a contributor to this repo | Judges R1/R2/R5 as a musician, blind to the implementation |
| **Independent listener** | A non-musician listener with no stake in the project | Judges R5 ("worth a hall") without technical framing |

**Minimum three evaluators, one per role.** At least two must be independent of
the founder (the two non-founder roles). The founder alone never passes G3.

**Blinding:** evaluators hear the render without being told whether it is the
LLM player or the deterministic player, and without seeing the seed. The
unblinding key is committed **after** the verdicts, so a verdict cannot be
retro-fitted to the wrong clip.

**Tie-break:** there is none. A split result is a fail; the work is revised and
re-evaluated under the same rubric.

## The founder's by-ear judgment — what changes

The founder's ear stays in the loop as **evaluator #1** (the Founder role
above). It no longer *is* the criterion:

- before: launch iff the founder says "yes";
- after: launch iff G1 ∧ G2 ∧ G3, where G3 is a median over ≥3 evaluators
  against a rubric fixed in advance, with the founder as one of the three.

This is the whole change. It is at least partly non-founder by construction:
two of the three minimum evaluators are not the founder, and the arithmetic is
fixed before anyone listens.

## G2 gap (the parser-coverage closure)

The Phase-1 amendment (S6/#318) already shows the pattern: vocal text was
outside the IR, so "source lossless" was unprovable until it round-tripped. The
same question must be answered for **every** source construct before G2 is a
source-level claim. G2 is met only when the chain diffs decoded output against
the source for each construct the parser reads, and a construct it does not
read is a documented, enumerated exclusion — not a silent one.

## Current state (2026-11-01)

| Gate | State | Evidence |
|---|---|---|
| G1 spec frozen v1.0 | FAIL | `FORMAT_SPEC.md` is v0; TRL 2 (`status/trl.json`) |
| G2 source-lossless chain | PARTIAL | chain green (IR-relative); source-level closure open |
| G3 listening rubric | FAIL | no verdict record exists |

## Open items this protocol leaves to a human

- **O1 (extension):** `.mu` vs `.muse` vs `.muw` — must be closed with G1.
- **Filling the evaluator pool:** the two non-founder roles need real people;
  this document names the roles, not the people. Selecting them is the
  founder's call and is not agent work.
- **Rubric weights:** equal weighting is the pre-registration default; changing
  it is allowed only before the first verdict is recorded.

## How to record a verdict

1. Freeze the rubric (this file) at a stated commit SHA.
2. Run the chain (G2) and the L2 render for the chosen work; record both SHAs.
3. Each evaluator scores R1–R5 independently, blinded.
4. Compute medians and the total; commit
   `docs/launch/g3-verdict-<work>.md` with the scores, the evaluators' roles
   (not necessarily names), the unblinding key, and the computed total.
5. A pass is a pass only if every rule in §G3 holds; otherwise it is a fail and
   the work is revised.
