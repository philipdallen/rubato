# AGENTS.md — Muse


## Portfolio front door — read this before you start work

This repository is one part of a wider portfolio. Before you claim or start work
here, spend five minutes in **`philipdallen/portfolio-ops`** (private), in this order:

1. `HANDOFF.md` — current portfolio state, what is blocked and on whom.
2. `EXECUTION_PLAN.md` — the week's priorities and the sequencing principles.
3. `RISK_REGISTER.md` and `AGENTS.md` — open risks, and the rules that apply to you.

Why this is worth five minutes: it is the only place that records **decisions already
made** and **work already owned by a human**. Skipping it is how a session redoes
someone else's work, contradicts a recorded decision, or spends its run on something
a human must do anyway.

**If you are an unattended automation run, skip this step** — the operating contract
is already inlined at the top of your prompt, and this orientation is for
human-directed and ad-hoc sessions.

**Do not confuse the two queues.** Work here is claimed and executed locally. Janitorial
work — lint sweeps, stale references, mechanical hygiene — is deliberately tracked
privately in `portfolio-ops`, not filed here. If you find mechanical work, do not file
it publicly; note it in your run output so it can be routed.

## Branches

`main` is the working branch and the GitHub default — every commit lands here, and it is
the branch visitors and all tooling read. `dev` also exists and is kept level with `main`;
it is a legacy name, and nothing should be committed to it. If the two ever differ, treat
`main` as authoritative.

**Edit workflows on `main`.** A `schedule:` trigger fires only from the default branch, so
a workflow that exists only on `dev` will not run. The sweep and audit workflows check out
`main` and push there for the same reason — the status snapshot must land where the default
branch points, or the dashboard reads a stale log.
## What this project is

Muse is an **executable music format**. A `.ru` file carries three components:
the **score** (the fixed work — our MusicXML-class encoding, packaged), the
**prompt** (the interpretive space — what may vary), and the **manifest**
(plaintext rights). The deterministic player reads the score ("our MIDI
player," the free baseline); the LLM player reads score + prompt and brings
the work to life — slowly, deliberately. A performance is an event, not a
render. The LLM player is **the product**.

See [FORMAT_SPEC.md](FORMAT_SPEC.md) for the format design,
[docs/pipeline.md](docs/pipeline.md) for the build plan and live status, and
[corpus/README.md](corpus/README.md) for the reference works.

> **Development stage: private repo, tools-first.** Nothing is published yet.
> Spec and reference player go public at launch; the **seed workbench
> (C-series) and LLM player (L-series)** stay proprietary.

## Ground rules

- **Format-first.** Never bake musical decisions into a player or tool that
  belong in the format. If a behavior can't be expressed in the spec, amend
  the spec (with a version note), don't hard-code it.
- **Tools before spec freeze.** Phase 0 analysis output drives the language
  design. A construct without corpus evidence doesn't ship.
- **Determinism is the baseline.** The score plays identically
  everywhere, forever. The prompt is where variation lives — never leak
  nondeterminism into the score.
- **The corpus is the ratchet.** Bach → Byrd → Schubert → Beethoven 5 →
  Beethoven 9. Work climbs the ladder; no rung is skipped.
- **No artist lookalikes.** Prompt philosophies reference styles and
  practices, never an artist's identity, without an explicit license in the
  manifest.
- **Provenance is mandatory.** Every `.ru` records source, license, and AI
  involvement in its plaintext manifest.
- **Human evaluation is constant.** The founder knows these scores; every
  render is evaluated by ear against them. Metrics support judgment, never
  replace it.

## Conventions

- **Branching:** `main` is stable; day-to-day work branches from and merges
  into `dev`. Never commit directly to `main`. Name branches for the work
  (`w1-event-ir`, `s3-seed-encoding`) — not `review` or `fix`; the PR is the
  review surface, the branch is just where commits live. Delete branches on
  merge.
- **Task coordination:** per [TASK_WORKFLOW.md](TASK_WORKFLOW.md) — one task
  per GitHub issue, label-based states, blockers over guessing. The standing
  work plan is [docs/pipeline.md](docs/pipeline.md) (W/S/P/C/L task series).
  **One claim per agent at a time** — exactly one `status:claimed` across
  the tracker; finish before claiming the next. Run-ids are mandatory
  (shared GitHub identity makes label/assignee checks useless — the newest
  claim comment's run-id decides ownership), and known-answer tasks close
  only with gate evidence in the done comment.
- **Blockers:** can't start or finish? Write
  `blockers/open_<datetime>_<slug>.md` per the workflow and move on.
- **Tests:** completing a task means spec'ing its tests
  (`tests/open_<datetime>_<slug>.md` + linked `Tests:` issue).
- **Documentation deliverable:** every code task ships a `README.md` in its
  tool directory (usage, API, dependencies) and a test spec in `tests/`.
  The doc is part of the Definition of Done — code without its doc is
  incomplete.
- **Docs coherence sweep:** at session start, check that README, AGENTS,
  FORMAT_SPEC, pipeline, and corpus README agree. A stale doc is a process
  failure on par with a stale claim.
- **Doc-prose checklist (authoring a design/proposal doc).** Mechanical
  drift is caught by `tools/muse_docs` (fast-tier suite); the prose layer is
  your own verification step before commit:
  1. Run `python3 tools/muse_docs/cli.py lint` — it must be clean (it flags
     broken relative links, unresolvable backticked paths, `open_*` refs
     whose record closed, unfilled `[TODO]`s, and non-UTF-8 files).
  2. Re-read every **command and output** you quoted and re-run it. A
     pasted result that no longer reproduces is a hollow claim.
  3. Re-check every **status word** (`done`, `filed`, `locked`, `passing`)
     against the issue queue and `git log origin/dev` — the queue is the
     system of record, the doc is a cache.
  4. Flag anything you could not verify into
     `docs/audit/<date>-doc-prose.md` and file a `documentation` issue
     (the same verify-and-file pattern as the A1 audit). Findings are a
     triaged, non-blocking queue — weekly, not per-commit.
  5. Do not "fix" a stale path in a `closed_*`/`open_*` record or
     `docs/audit/*`: those describe the world as it was. Add the doc to
     [docs/superseded.txt](docs/superseded.txt) if historical by design.
- **Spec edits:** changelog discipline — v0.x may break, v1+ additive only.

## Session lessons (2026-08-23, run=20260823-1945-c7d3)

- **Check for the repo's AGENTS.md before working.** The first session tried
  to act on an empty repo (clone fixed it: philipdallen/rubato).
- **The rebase-dedup rule proved itself twice this session** — an S2 codec
  rebase aborted cleanly when a sibling landed first, and seam tests were
  dropped when #165 got claimed by a sibling mid-build.
- **GITHUB_TOKEN can rotate mid-session** - pin `GH_TOKEN` to the live token
  (`export GH_TOKEN=$GITHUB_TOKEN`), which works whether `GH_TOKEN` is stale or
  absent. `ALL_REPOs_GH_TOKEN` is not present in every sandbox; do not rely on
  it. There is no agent-side refresh step: name `$GITHUB_TOKEN` in a new command
  to get the current value. Long-running processes, and remote URLs with a token
  embedded, capture the token at start and need a restart / re-point after a
  rotation. See `portfolio-ops/ACCESS_AND_IDENTITIES.md`.

## Build / test

One command runs the whole repo (issue #167):

```bash
pip install -r tools/requirements.test.txt
./tools/run_tests.sh          # fast tier (live counts: --list for suites, gate output for tests)
./tools/run_tests.sh --full   # + slow suites muse_analyze/muse_chain/qa_frontend and @pytest.mark.slow tests
./tools/run_tests.sh --list   # suite inventory
./tools/run_tests.sh --jobs N # cap suite parallelism (default nproc, ≤8); --serial = -j1

Slow-test convention: tests too heavy for the fast tier carry
`@pytest.mark.slow` (registered in `tools/pytest.ini`); the fast tier
deselects them with `-m "not slow"`, `--full` runs them.
```

**Gate of record.** Until the GitHub Actions runner issue resolves
(issue #194), the working gate is the pre-push hook: enable it once per
checkout with `git config core.hooksPath scripts`, and every push to `dev`
runs the fast tier and refuses on failure. The workflow files are valid
YAML and resume as the server-side gate the moment account health
resolves.

## Seed iteration loop

The founder's loop for authoring a seed (see `docs/seed-iteration.md` for a
walkthrough; the loop is the way seed work happens):

1. **Edit** the seed YAML in `seeds/<work>.seed.yaml` — no authoring UI yet;
   commit is the write path.
2. **Validate** with C1: `python3 tools/muse_seed_cli/cli.py validate
   seeds/<work>.seed.yaml corpus/<work>.xml` — schema + assertions + budgets
   must pass.
3. **Generate the mockup** with L1: `python3 tools/muse_mockup/cli.py
   corpus/<work>.xml` — full DNA density; the mockup is dense, not a sketch.
4. **Probe** with W-B1 (`tools/muse_probes`): reads artifacts the loop
   already produces — param diff, budget fit, assertion pass/fail,
   coverage, determinism, fidelity guard.
5. **Listen** with the render bridge (`tools/muse_audio`): per-revision
   WAVs play side by side on the workbench page; `--live` for the LLM
   reading. See docs/seed-iteration.md step 5.
6. **Iterate.** The workbench page (W-B3) shows probe history per seed
   revision. Quality checks (W-B2) catch regressions the ear might miss.

Per-tool suites live next to their code (`tools/<tool>/test_*.py` or
`tools/<tool>/tests/`); run one with `cd tools && python -m pytest
<suite-dir> -q`. Known-answer pins (corpus counts, golden vectors, W4 diff)
must not drift silently — changing a pin requires amending the source doc
(`corpus/README.md`, FORMAT_SPEC, or the tool's design doc) in the same
commit. CI = the conformance workflow (`.github/workflows/conformance.yml`,#163)
with a manual one-shot re-run for flaky failures (.github/workflows/retry-flaky.yml,
#293->#300: workflow_dispatch-only with run_id input; docs: docs/ci-retry.md.
Update this section as tooling lands — do not leave it stale.

## Repository layout

```
FORMAT_SPEC.md        # format design draft (evidence-frozen at Phase 1)
README.md             # vision + component map
TASK_WORKFLOW.md      # multi-agent claim/work/block protocol
docs/pipeline.md      # build plan + live status (W/S/P/C/L/E series)
docs/vision.md        # product thesis (2026-08-23 revision)
docs/design/          # design docs + dependency index (grows with the task series; ls for the live count)
docs/decision-log.md  # ADR-style index: locked + open decision points
docs/tech-stack.md    # borrow/build index: software, protocols, specs
docs/literature-review-w1.md  # pre-W1 lit review (IR, compression, patterns)
corpus/               # reference works (Bach, Byrd, Schubert, Beethoven 5+9)
tools/ir/             # W1 event-stream IR + MusicXML/MIDI parsers (pytest suite)
tools/corpus_loader/  # W2 corpus loader CLI (the known-answer gate)
tools/muse_diff/      # W4 IR↔IR diff tool (recall/precision in tick space)
tools/s1_stream/      # S1 golden vectors + verifier (FORMAT_SPEC §4.4)
tools/muse_analyze/   # W3 pattern analyzer → analysis report
tools/muse_viz/       # W5 piano-roll renderer (matplotlib)
tools/muse_roll/      # S2 roll encoding (MUR1 varint columnar + zlib)
tools/muse_mu/        # S5 container + manifest
tools/muse_seed/      # S3 seed format + C1 validator
tools/muse_seed_cli/  # C1 seed CLI
tools/muse_budgets/   # C3 era/style budget engine
tools/assertions/     # C4 per-work assertion sets (S3.5 validator)
tools/muse_ops/       # S4 language validator
tools/muse_assert/    # S3.5 assertions
tools/muse_author/    # C2 AI-assisted authoring
tools/muse_render/    # L2 mockup → audio renderer
tools/muse_compare/   # L3 model A/B comparison rig
tools/muse_distill/   # L4 mockup → seed revision distiller
tools/muse_play/      # P2 reference renderer (soundfont tier)
tools/muse_event/     # E1 execution scaffold (corpus ladder)
tools/muse_decode/    # P1 reference decoder (.ru → event stream)
tools/muse_ci/        # P3 conformance suite (.ru golden vectors + decoder gate)
tools/muse_audio/     # workbench render bridge (seed revision → WAV + audio manifest)
tools/muse_probes/    # W-B1 seed-iteration probe engine
tools/muse_mockup/    # L1 mockup harness
tools/muse_provider/  # L1.2 pluggable LLM generate interface (Gemini + recorded fixtures)
tools/muse_generate/  # L1.3 generate → validate → fix loop
tools/muse_grow/      # G1 seed growth harness (iteration deltas + trajectory)
tools/muse_chain/     # E2E chain harness (parse → pack → container → decode → verify → render)
tools/muse_explorer/  # corpus explorer (QA static surface)
tools/muse_workbench_runner/  # workbench data regeneration (probes/growth artifacts)
tools/qa_frontend/    # T2 headless DOM QA (Playwright)
tools/muse_docs/      # T7 doc-prose lint (offline mechanical doc checks)
tools/run_tests.sh    # unified test runner (fast/--full/--list)
tools/spike/          # renderer/audio spike scripts (pre-workflow)
SCHEMA_SPEC.md        # SUPERSEDED (JSON-schema v0) — design history only
PRIOR_ART_REVIEW.md   # landscape review (schema-first era)
blockers/             # open_/closed_ blocker reports
bugs/                 # open_/closed_ bug log (defects found in flight; review like blockers)
tests/                # open_/closed_ test specs (runtime tests live beside the code)
```
