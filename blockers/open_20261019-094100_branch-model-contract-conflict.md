# Blocker: #415 — the issue's branch/PR model contradicts the binding portfolio contract

- **Task:** #415 (docs: reconcile the branch/PR model across AGENTS.md and TASK_WORKFLOW.md)
- **Filed:** 2026-10-19T09:41Z, run=20261019-0841-20ys
- **Status:** `status:blocked-needs-input` on #415

## What was attempted

Claimed #415 and read the issue, both docs, and the git history to reproduce the
"before" state. Three texts are in play, and the issue's premise needs checking
before any edit:

| Source | Says | Date |
|---|---|---|
| `AGENTS.md` §Branches | `main` is the working branch; `dev` is a legacy name, nothing commits to it | 2026-09-22 (`f9d3f8a`) |
| `AGENTS.md` §Conventions › Branching | "branches from and merges into `dev`. Never commit directly to `main`." | 2026-08-21 (`31c99dd`) |
| `TASK_WORKFLOW.md` step 5 | "Commit directly to `main` … (no PR — review happens retrospectively on `main`)" | — |

## The contradiction (this is the blocker)

The issue's **Definition of Done** requires: "work happens on named branches, lands
on main via PR … **No remaining instruction says 'commit directly to main'**."

The binding portfolio operating contract requires the opposite: "**`main` is the
only branch you write to, in every repo**" and "do not commit to any branch other
than `main`". The contract also states that when a repo doc and the contract
disagree on a portfolio-wide fact — *the branch to write to* is named explicitly —
**the contract wins**.

These cannot both hold. Satisfying the DoD means deleting the exact instruction
(`TASK_WORKFLOW.md` step 5, "commit directly to `main`") that the contract mandates.
The issue's **method constraint** states the same conflict in the imperative:
"Work on a branch and open a PR. Never push to main, merge, or close other issues."

## Evidence that the issue's premise is also factually mixed

The issue says "Live practice is a fourth model: named branches merged into main via
PR". Checked `main`'s first-parent chain and each commit's PR association:

- The two merge commits the issue cites — `8c7be79` (#409) and `04ef42a` (#408) —
  are **the maintainer's own** (`Philip Allen <pda728@gmail.com>`), from 2026-10-17.
- Every recent **agent** commit on `main` is a **direct push, no PR**:
  `15c752e`, `4efe4f6`, `b73e2c0`, `0aaad54`, `a1096d6`, `b3fc269`, `41cf764` —
  `gh api …/commits/<sha>/pulls` returns `NONE` for all seven, all authored by
  `openhands <openhands@all-hands.dev>`.
- The open PRs the issue cites (#387, #410, #411) are all authored by `philipdallen`
  (the human), not by agents.

So the practice actually followed is two-track: agents push directly to `main`
(matching the contract), the maintainer uses PRs. The issue's DoD collapses that
into a single PR-based model, which is the contract-violating half.

## What is missing (the decision for the human)

Decide which model the rubato docs should describe, and amend #415's DoD
accordingly:

1. **Contract model (agent practice):** agents commit directly to `main`, no PR;
   the PR is the maintainer's own review surface. The fix is small: correct the one
   stale line, `AGENTS.md` §Conventions › Branching (which also names the legacy
   `dev`), to match §Branches and `TASK_WORKFLOW.md` step 5. Both of those already
   say "main".
2. **PR model (issue #415 as written):** every commit lands via PR. This needs the
   binding portfolio contract amended first, and it contradicts `TASK_WORKFLOW.md`
   step 5 as it stands.

Option 1 is a docs fix inside the contract. Option 2 is a change to the contract
itself — not an agent's call.

## What was tried and why insufficient

- Confirmed no recorded decision covers this: `docs/decision-log.md` has no
  branch/PR-model entry; `portfolio-ops` is inaccessible for a policy search
  (private, `gh search` returns nothing) and per the contract is not claimable.
- Checked branch protection (403, not accessible to the integration) and rulesets
  (`[]`) — neither forces a PR, so neither resolves the ambiguity.
- Re-ran the baseline check: `python3 tools/muse_docs/cli.py lint` → 0 findings,
  exit 0. The DoD's *observable* check passes, but its prose requirement is the
  part that cannot be met without the contract decision.

## Notes

- No edits were made to `AGENTS.md` or `TASK_WORKFLOW.md`; the working tree was
  clean at claim time and the only change pushed is this blocker file.
- `#415`'s constraint "Do not touch PR #410's TASK_WORKFLOW.md hunks" was honoured —
  PR #410 is still open and unmerged, and its hunks (the NEEDS:/not-in-my-lane
  section) were inspected but not touched.
