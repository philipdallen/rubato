# Test spec — CI flaky retry (#293)

Written 2026-08-28 by the completing agent, per TASK_WORKFLOW §6.
Work under test: `.github/workflows/retry-flaky.yml` +
`docs/ci-retry.md`.

## Behaviors to verify

1. **Workflow file parses as valid YAML** and registers a
   `workflow_run` trigger on the `conformance` workflow, `completed`
   type. (Local check: `python3 -c "import yaml,sys;
   yaml.safe_load(open('.github/workflows/retry-flaky.yml'))"`),
2. **Arguments are correct:**
   - `if` guard expressions match:
     `github.event.workflow_run.conclusion == 'failure'`,
     `github.event.workflow_run.run_attempt == 1` (loop brake:
       only re-run the *first* attempt of a run; a retried run cannot
       re-trigger),
     `github.event.workflow_run.event == 'push'` (not PRs yet).
   - `permissions` block grants `actions: write` (needed for
     `gh run rerun`).
   - The step runs `gh run rerun "<run-id>" --repo <repo> --failed`
     — re-runs **only failed jobs**, never the whole pipeline.
3. **Docs contract** (`docs/ci-retry.md`):
   - Documents the automatic trigger conditions (failed + first attempt +
     push), the manual escape hatch
     (`gh run rerun <RUN_ID> --repo <owner>/<repo> --failed`), and
     the when-to-retry / when-not-to matrix (`run failed but local passes`
     → retry; `local also fails` → fix, not retry; `retry also failed` →
     escalate; `> 24 h` → don't auto-mask a systemic outage).
       - `docs/pipeline.md` tracks a `CI flaky retry` row linking #293.
4. **Live behavior** (the real gate; manual/opportunistic):
   - Push to `dev` with a workflow-triggerable failure → the retry
     workflow fires once, re-runs only failed jobs. A retried run that
     fails again does **not** re-trigger (run_attempt guard).
   - Verified via Actions API: `GET
     repos/{owner}/{repo}/actions/workflows` lists a `retry-flaky`
     workflow, active; any `workflow_run`-triggered run appears with
     the conformance run id in its log.

## How to invoke

```bash
# static contract (fast tier, no network:
python3 -m pytest tests/docs -q
```

Live verification (after a real push: 
```bash
gh run list --repo philipdallen/rubato --workflow retry-flaky.yml
gh run view <retry-run-id> --repo philipdallen/rubato --log
# confirm: (a) it fired for a conformance failure, (b) its step ran
# 'gh run rerun <conformance-id> --failed', (c) the conformance run's
# attempt became 2.
```

## Deliberately not covered by CI automation

The workflow cannot be pinned byte-for-byte by the docs suite without
over-pinning GitHub's own syntax; the static checks above (YAML parse,
wire-args assertions) are the repo-side gate. The live trigger needs a
real Actions run, which currently depends on the runner issue the repo is
working around — it is exercised opportunistically, not on every push.


If the live smoke proves the retry loops (double re-run on one failure), the
follow-up is to narrow the `if` (e.g. also require the run's failed jobs
had zero duration as signals for runner-provisioning failures before
re-running; that refinement awaits a green runner to observe it against.
---

**Closed 2026-10-19** (issue #418 reconciliation, run=20261019-0741-2g2w): the owning task **#293** is closed as completed; the static docs-contract coverage it calls for landed in `tests/docs/test_ci_retry.py` (present). The live-trigger check stays opportunistic, as recorded above. No open `Tests:` issue remains.
