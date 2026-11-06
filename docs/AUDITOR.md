# The Auditor — daily repo health & drift automation

A scheduled, read-only pass over this repo that surfaces drift, bugs, and
architecture issues for the human Orchestrator to triage. **It never takes
action on its own.** Every finding is a proposal held for review.

## What it is not

- **Not an agent.** It is a deterministic script (`tools/auditor.py`). No LLM,
  no token cost per run, nothing to hallucinate. Every finding is a mechanical
  fact about the tree. This is a deliberate choice: the checks below are all
  decidable by inspection, and a deterministic run is safe to re-trigger.
- **Not a fixer.** It never edits code, merges, or resolves anything. It closes
  exactly one class of issue -- stale `Auditor digest` digests (see "Digest
  retention" below) -- and never proposals.
- **Not a second tracker.** It opens proposals and a digest; it does not move
  work through the pipeline.
- **Not connected to the dashboard.** It writes one line to this repo's own
  `status_log.jsonl` (see below). It never touches the HuB repo or any other.

## Trigger and idempotency

Runs from the `auditor` GitHub Actions workflow in this repo, on a daily cron,
plus `workflow_dispatch` for a manual run.

Before any analysis it reads the last-audited commit SHA from
`status/auditor_state.json` (the `status/` directory already holds this repo's TRL
file, so no new state location was invented; the checkpoint file itself is
created on the first successful run). **If `HEAD` has not moved, it
exits without creating anything** — no issue, no comment, no status line.

- On success the checkpoint advances to the new `HEAD`.
- On failure it does **not** advance, so the next run retries the same range
  rather than silently skipping it.
- Re-triggering manually is safe: findings are deduplicated against open issues
  by a stable signature (below), so a second run adds information to the
  existing issue instead of opening a twin.

## What it checks

### High level — architecture and drift

- **`dangling-doc-ref`** — backticked file paths in `docs/` that resolve nowhere.
  A reference attributed to a sibling repo, a wildcard/placeholder, or a bare
  basename that exists somewhere in the tree is *not* reported; those are
  citations or loose prose references, not drift.
- **`doc-count-drift`** — docs that cite contradictory counts of the same thing
  ("N gates", "N checks", "N ids"). This is the class the spec calls out
  explicitly. Only a disagreement *between* documents is reported; the check does
  not attempt to derive which number is correct, because for this repo family the
  count is often genuinely tiered.
- **`status-log-contract`** — this repo's own `status_log.jsonl` must stay
  parseable for the dashboard that reads it.

### Detailed level — bugs and hygiene

- **`gate-health`** — runs this repo's own gate/test runner and reports a
  non-zero exit. The runner is detected, not assumed, because inventing a
  command that does not exist would make this check silently vacuous. If no known
  runner is found, that is reported as a catch-all finding rather than treated as
  a pass.
- **`stale-todo`** — `TODO`/`FIXME`/`XXX` markers older than 120 days, aged by
  `git blame`. Capped so a legacy backlog produces a readable digest rather than
  a wall.
- **`committed-artifact`** — build/OS cruft that is *tracked by git*
  (`.DS_Store`, `__pycache__`, `*.pyc`, editor backups). Untracked cruft from a
  local test run is deliberately ignored: it is noise, and reporting it would
  make this check cry wolf.

### Security

- **`committed-secret`** — credential-shaped strings in files git tracks. High
  confidence shapes only (private keys, AWS/GitHub/Slack/Google/Stripe/Anthropic/
  OpenAI/HuggingFace tokens); a scanner that fires on prose or on the example keys
  vendored into a lockfile produces findings a human learns to skip. The matched
  value is **never reproduced in the finding**, which is filed on a public tracker:
  echoing a live credential would complete the leak the check exists to catch.
- **`workflow-hardening`** — three mechanical checks on `.github/workflows/*`:
  a missing top-level `permissions:` block (the workflow then runs with the
  repository's default token scope); untrusted `${{ github.event.* }}` /
  `inputs.*` interpolation directly into a `run:` block on a write-capable
  trigger (the script-injection path); and a privileged checkout of a PR head ref
  (the `pull_request_target` anti-pattern). Interpolation through `env:` is the
  documented remedy and is deliberately *not* flagged.
- **`dependency-advisory`** — known advisories against pinned requirements, via
  the public OSV.dev API. Free, no auth, no GHAS entitlement (the GitHub advisory
  APIs are entitlement-gated and return 403 for these repos). Requirements are
  discovered by git across the tree rather than read from a hard-wired root file,
  because this repo pins under `tools/`. Three outcomes are distinguished: an
  advisory found; queried with none found (silent — a clean result); and the
  lookup unavailable, which is reported as a **catch-all** finding, since a check
  that silently stops running looks exactly like a clean repo.

### Architecture & drift, continued

- **`stale-owner-ref`** — references to a retired account slug (the exact slug
  lives in `RETIRED_OWNER_SLUGS` in `tools/auditor.py` and is not repeated here,
  because this file is itself scanned)
  surviving outside the frozen record. A clone URL, `--repo` example, or prose
  sentence that still names the old slug tells a reader or an agent to use an
  address that no longer resolves. The frozen decision and history logs are
  exempt by design: those files record the slug as it was at the time, and
  rewriting them would make the record false — a worse defect than the stale
  reference. The exemption is a path prefix, so a repo that does not keep those
  directories simply has nothing to exempt.

### Catch-all

Anything that fits none of the above, plus a `check-crashed` finding when a check
itself raises. A crashed check is reported rather than swallowed, because a check
that silently stops running looks identical to a clean repo.

## The `on-hold` states, and how to approve a proposal

Three labels drive the held-for-review model. None of them is a status label this
repo's task protocol treats as claimable.

| Label | Meaning |
|---|---|
| `auditor:proposed` | The Auditor proposes a new task. |
| `auditor:revise` | The Auditor proposes replacing or correcting an existing open task. |
| `on-hold` | Held for human review. **Not claimable by agents.** |

**To approve a proposal and move it into the real pipeline**, the human:

1. Reads the issue and decides whether the finding is worth acting on.
2. Removes `on-hold` and removes `auditor:proposed`.
3. Adds whatever status label this repo's protocol uses to make work claimable
   (the `status:available` label described in this repo's own workflow doc).

The Auditor **never** adds that last label. Making work claimable is the human's
decision alone, and it is the single most important boundary in this design.

To reject a proposal, close the issue. The Auditor does not reopen closed issues;
the dedup check considers only *open* issues, so a rejection is respected.

## Dedup

Each finding carries a stable signature of the form
`[auditor:<check>] <subject>` — for example `[auditor:dangling-doc-ref] docs/x.md`.
That signature is the issue *title*. Before opening anything, the Auditor looks
for an open issue whose title or body already contains the signature:

- **found** → comment with the new observation; never open a duplicate.
- **not found** → open one new issue.

Because the signature is derived from the check id and the subject rather than
the finding body, re-wording a finding does not create a second issue.

## Daily digest

One issue per day, titled `Auditor digest — YYYY-MM-DD`, labeled `on-hold`. It
contains the commit range covered, findings bucketed by the three categories
above, and links to every issue opened or commented on in that run. If a digest
for the day already exists, the new run comments on it rather than opening a
second.

## What it writes to `status_log.jsonl`

The shared dashboard contract is documented in HuB's `PM_STATUS_FRAMEWORK`
document (the HuB repo, not this one). After a successful run the Auditor
appends **one** line:

```json
{"timestamp":"2026-01-01T00:00:00Z","trl":{...},"flow":{...},"notes":"audit 2026-01-01 @ abc1234: 2 proposed, 0 revise"}
```

- **No new field was added.** The audit summary fits the existing `notes` field,
  which the schema already defines as free text and which the dashboard already
  renders in its snapshot log. The spec asked for counts of new `on-hold` items
  and `auditor:revise` proposals and the covered SHA; all three are carried in
  that one string.
- **`trl` and `flow` are copied forward verbatim** from the previous line. This is
  load-bearing, not tidiness: the dashboard reads those values from the *last*
  entry, so an audit snapshot that omitted `trl` would blank the TRL panel for
  every viewer until the next scheduled sweep. The tests pin this behaviour.

## Hard constraints (enforced, and tested)

- Never merge or auto-resolve anything. The single sanctioned close is digest
  retention (below); proposals (`auditor:proposed`/`auditor:revise`) are never
  closed by automation.
- Never add a claimable-status label — only the human does that, after review.
- Never edit code. The only files it writes are `status/auditor_state.json` and
  `status_log.jsonl`.
- Never touch the HuB repo or any other repo.
- The analysis is read-only and takes no lock, so it cannot race a concurrent
  agent; the only shared state it mutates is appended under a single write.

## Amended contract: digest retention

One deliberate, scoped addition to the original contract (shipped 2026-10-17):

- **Digest retention.** At the end of each daily run the auditor closes digest
  issues older than the newest 7, selected by title prefix (`Auditor digest —`)
  *and* the label set exactly `["on-hold"]`. Anything carrying
  `auditor:proposed`/`auditor:revise` (or any other label) is never selected.
  Closing is dedup-neutral: digest titles are date-unique and the auditor never
  reopens closed issues.

## Running it by hand

```bash
python3 tools/auditor.py --repo philipdallen/<repo> --dry-run   # print findings, write nothing
python3 tools/auditor.py --repo philipdallen/<repo>             # do a real run
python3 tools/auditor.py --repo philipdallen/<repo> --force     # ignore the checkpoint
```

Tests are offline and stdlib-only:

```bash
python3 tools/auditor/tests/test_auditor.py
```

## Which parts of the spec were interpreted

Recorded rather than decided silently:

- **"Architecture smells" are only partially covered.** Growing coupling and
  "a module doing more than its job" need judgement a deterministic script does
  not have. The checks cover the *mechanically checkable* subset — dangling refs,
  contradictory counts, a runner that fails, a check that cannot fail. The
  subjective layer is left to human review rather than faked with heuristics that
  would produce noise.
- **"A gate that can't fail"** is not detected directly. Detecting it properly
  requires mutating the gate and observing silence, which is invasive and outside
  a read-only auditor's remit. The digest note records the indirect signal
  instead: a gate count that does not match the number of executables.
- **TODO/FIXME age threshold** (120 days) and the report cap (8) were chosen, not
  specified. Both are constants at the top of `tools/auditor.py`.
- **Checkpoint location** — `status/auditor_state.json`, because `status/` already
  exists in this repo family and the spec forbade inventing a new location.
- **`auditor:revise` is defined but not yet produced** by a built-in check. The
  label, the comment-on-existing-issue path, and the digest wiring all exist and
  are exercised; no check currently emits a revision proposal, because doing so
  reliably needs an LLM's judgement about whether an existing issue is *stale or
  wrong*. It is implemented so that adding such a check is a one-line registry
  change, and left honestly unused rather than filled with a guess.