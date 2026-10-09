# Bug: qa_frontend fails 1 test in CI only (unmasked by the playwright setup fix)

**Filed:** 2026-10-09 18:49 UTC (run=20261009-1823-i8f9)
**Issue:** [#383](https://github.com/philipdallen/rubato/issues/383)

## Symptom

`qa_frontend` fails **1 of 176** tests on the `slow-beethoven9` CI job
(`./tools/run_tests.sh --full`, ubuntu-latest, Python 3.13). It passes locally.

## Repro / evidence

CI, two attempts of the same commit (`slow-beethoven9`):

```
FAIL  qa_frontend       177s    1 failed, 175 passed in 176.55s (0:02:56)
```

Local, Python 3.13, Chromium installed:
- `python3 -m pytest qa_frontend/tests -q` → 176 passed
- `./tools/run_tests.sh --full` (parallel) → all suites green

Two consistent CI failures with a local green ⇒ environment-specific defect,
not a flake (so `docs/ci-retry.md`'s retry protocol does not apply).

## Root cause (partial)

The specific test is **not recoverable from CI logs**: `tools/run_tests.sh`
buffers per-suite pytest output to `$RESULTS_DIR/$idx.out` and prints only the
last line, so CI reports the count but never the failing test id. The failure
was invisible until #379 fixed the playwright setup error that previously
aborted the job before any suite ran.

## Fix

Tracked in #383 — identify the test (serial run on a CI image, or print ids on
failure), fix or pin it, and make the runner surface failing test ids.
