# Workbench design — full corpus view + interactive surface

**Issue #228. Status: draft (authored by claim run=20260824-1003-uw2h).**

Sibling of [seed-workbench.md](seed-workbench.md) (the loop scaffolds). This
doc defines what the surface actually looks like, and — crucially — whether
it stops being a read surface (today's deliberate design, but founder
review flagged it as amateur) or stays read-only with a proper runbook.

## Founder feedback that motivates this (2026-08-24)

The workbench today is scaffold-level: only one seed (`bwv227.1`, not a UI
bug — only it has been seeded), labels collapse file-ids ("Jesu meine
Freude" four times), no interaction beyond a probe toggle, and — most
importantly — no way to *run* anything from the browser. Asked directly:
"shouldn't the UI be able to run our python commands via a clickable UI
interface? or at least a command prompt that allows for manual running
with an explainer and helper for seed authoring?"

**Decision:** yes — the workbench should be an interactive surface, not a
read surface. The static/no-write-path framing in seed-workbench.md was
over-cautious. This doc supersedes that constraint and specifies the
interactive surface with proper sandbox/config boundaries.

### The Rehearse pane is interactive, not read-only (resolved 2026-10-09)

Issue #388 asked whether the shipped read-only Rehearse pane was a deliberate
post-R2 safety decision, which would move the R2 spec items to a "not built"
note. It was not: the records above resolve it to **build the interactive pane**.
The R2 spec says the Rehearse pane **must write** — "contains the textarea +
dry-run + commit/discard affordances" (R2 §Coverage item 6) — and this doc's
Decision line states "the workbench should be an interactive surface, not a read
surface". The read-only pane in `docs/workbench/detail.html` is the pre-R2
scaffold, not a decision. R2 items 6-7 stand, to be finished by #393 and #394.

## Design questions resolved

| Question | Resolution |
|---|---|
| Clickable command runner? | Yes — a bounded allow-list of commands, not a free-form shell. |
| Or at least a command prompt? | Yes — a prompt mode kept for power users, with autocomplete + explainer. |
| Config gate? | Explicit, committed `workbench.config.json` with the allow-list; page fails closed if config missing/invalid. |
| Sandbox boundary? | Local-only binding (127.0.0.1:0 serve), commands run via a thin local runner (`tools/muse_workbench_runner`) reading the repo; no remote execution. |
| "Layering": read-only probes still work? | Yes — this doc ADDS an interaction layer; it does not remove the probes. |

Both a clickable runner and a prompt mode exist, because the founder's
workflow mixes one-command-a-time probing and exploratory iteration.

## Surface layout (top → bottom)

### 1. Corpus tree (left rail)

All five reference works rendered as a collapsible tree, file-ids shown:
- **BWV 227** → four files `bwv227.1` … `bwv227.4` (per-movement)
- **Byrd Mass 3v** → six files `byrd-mass3v.kyrie` … `byrd-mass3v.agnu`
- **Schubert D 810** → one file
- **Beethoven 5** → one file
- **Beethoven 9** → one file

Each file node shows its **seed state**:
- `has seed` (green) → probe/growth panels populated on click
- `not yet seeded` (grey) → empty state: "run `muse_seed create` to start"
- `seed asserted (pass)` / `seed asserted (fail)` → corollary status pill

This kills both founder complaints: no duplicate-label ambiguity and no
"only one piece in corpus" illusion.

### 2. Seed panel (top-left detail)

YAML view, with individual fields labeled (tempo bounds, energy shape,
philosophy fields) in plain readable rows rather than raw JSON. `edit`
opens the file in the default editor (read-only page shows `edit in repo`
diff-hint; authoring stays git-first per S3 convention).

### 3. Probes panel (right)

Seven probes as a table: assertion pass/fail, budget fit, coverage,
delta curves, determinism, fidelity guard, **each with a legible legend**
(`outside` needs the threshold chip; spans show mean deviation, not raw
JSON). Expandables stay compact `<details>`.

### 4. Growth panel (bottom-left)

Trajectory V1→V2 per trait, color-coded growing (green) / flat (yellow) /
regressing (red). Legends at column header, not raw numbers.

### 5. Audio panel (bottom-right)

Audio placeholder shows "audio arrives with P2 — `muse play
seeds/<work>.seed.yaml`" when no file. Session-local Renders
per `docs/audio/README.md` (rendered WAV is session-local, not
committed).

### 6. Command runner (top-right — NEW)

A bounded command palette with:
- `muse_seed validate` — validates current seed
- `muse_probes run` — re-probes current seed
- `muse_grow iterate` — one growth iteration (mockup→distill→compare)
- `muse_play` — generates mockup audio (session-local)
- `muse_seed create` — initializes a seed for an unseeded file
Each is a button in the panel; output rendered into the panel with
pass/fail/explainers. Buttons only enabled when the preconditions hold
(e.g. `muse_grow` requires a seed).

### 7. Prompt mode (top-right — NEW)

A free-form prompt box replicating the runner's parser:
- `run <command> [args]` — runs allow-listed command
- `<command> --help` — explainer without running
- tab completion across the allow-list
Same runner, same sandbox — the prompt is syntax sugar over the palette.

## Config gate (`workbench.config.json`, committed)

```json
{
  "runner": "tools/muse_workbench_runner",
  "sandbox": "local",
  "allowlist": [
    "muse_seed.validate",
    "muse_seed.create",
    "muse_probes.run",
    "muse_grow.iterate",
    "muse_play.render"
  ],
  "prompt_enabled": true,
  "reach": "sandbox-only"
}
```

Missing or malformed config → page loads with a visible warning: "interactive
mode disabled — workbench.config.json missing/invalid." Fails closed, never
silent.

## Sandbox boundary

- Serve locally on `127.0.0.1:0` (the qa_frontend harness convention,
  unchanged).
- `muse_workbench_runner` is a thin stdlib `http.server` fork bound to
  `127.0.0.1` behind the static page; it executes only the allow-list via
  `subprocess`; no shell=True; CWD is the repo root.
- The page never proxies to a remote endpoint.
- **One origin (landed #305, 2026-09-16).** The server takes `--docs` and
  then serves the static `docs/` tree *and* `/api` from the same origin, and
  the page resolves its runner URL origin-relatively (with `?runner=`,
  a `muse-runner-url` meta tag, or `window.MUSE_RUNNER_URL` as overrides).
  The old hardcoded `http://127.0.0.1:9145` resolved to the *visitor's*
  machine when the site was proxied — nothing there listened, so every call
  404'd or 501'd. Binding stays `127.0.0.1`; exposing it is a separate,
  deliberate step. Static serving carries a path-traversal guard and never
  shadows `/api/*`.
- **Cross-origin opt-in (landed #316, 2026-09-16).** A runner override that
  points at a different origin needs `--allow-origin <exact-origin>`
  (repeatable) on the runner, or the browser refuses the response. No
  wildcard is ever emitted, matching is exact, and the default is no CORS at
  all: this server executes allow-listed commands, so any origin granted
  access can drive them from a page the user merely visits. Responses carry
  `Vary: Origin`; preflight is answered only for an allowed origin (403
  otherwise). Same-origin use — the `--docs` path above — needs none of it.

## Module split (proposal for W-B3 refactor)

| Module | What it now owns |
|---|---|
| `tools/muse_workbench_runner` | the allow-list executor + config parser |
| `docs/workbench/index.html` | static page + palette + prompt |
| `docs/workbench/data/works.json` | already exists; shape unchanged |
| `tools/qa_frontend/tests/test_workbench_dom.py` | DOM assertions on the tree + panels |
| `tools/qa_frontend/tests/test_workbench_interactions.py` | clickable runner + prompt features |

Tests develop per #229 (blocked by this doc's labels).

## Open questions (before sign-off)

- Should `muse_seed create` auto-initialize unseeded files from a template
  (S3 example seed), or stay a manual click confirmation? Default: manual.
- Prompt mode: enable by default or behind a config flag? Default: enabled;
  disable is a one-line config toggle.

## Acceptance criteria

- Tree groups all five works / 13 files with explicit ids.
- Seeded/unseeded states properly distinguished.
- Labels legible (no raw JSON in probes/growth).
- Command runner + prompt present; allow-list enforced by
  `workbench.config.json`; page fails closed without config.
- Zero console errors; run_tests fast tier still green.

## Navigation (landed #304, 2026-09-16)

The surfaces were reachable only by hand-editing the URL. Added:

- **Shared site nav** (`nav.site-nav`) on all six QA surfaces: root,
  explorer, workbench detail/files/terminal, boardroom. Markup is
  byte-identical on every page and hrefs are root-relative (`/explorer/`,
  `/workbench/detail.html`, and so on), so one string works at any depth.
  There is no include mechanism and no build step, so
  `tools/qa_frontend/tests/test_workbench_nav.py` hashes the nav block and
  fails on drift. The nav must never carry an absolute URL or IP literal:
  that is the #305 bug class (a hardcoded `127.0.0.1:9145`).
- **Per-revision jump links** on `detail.html` (`#jump`): one link per
  committed revision, each targeting a stable anchor on its
  `details.wb-rev` block. Clicking a link opens a collapsed revision
  before scrolling, so the reader lands on the panels rather than a
  one-line summary. Anchor ids are slugged, because a work_id carries a
  dot (`bwv227.1`) and a dot in an id cannot be reached by a plain CSS
  selector without escaping.

Also corrected: six pages linked the removed trailing-slash route
`workbench/terminal/` (a 404); the real route is `terminal.html`.

Fixed in #309: the workbench pages overflowed horizontally at 375px. Pre-existing
and unrelated to the nav (the nav wraps and adds 0px);
logged in `bugs/closed_20260916-160200_workbench-mobile-overflow.md`.
