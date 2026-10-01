# Decision log — architecture and design decision points

ADR-style index. Every locked decision gets an entry; every open decision
gets a tracking slot. Sources: `docs/pipeline.md` locked decisions,
`docs/phase-scoping.md`, `docs/checkpoint-egg-model.md`, and design docs.

## Locked decisions (architecture)

| # | Decision | Status | Source |
|---|---|---|---|
| D1 | Three-component format: score + prompt (seed) + manifest | locked | docs/vision.md §0 |
| D2 | MusicXML is the existing roll; compressor adapts it | locked | docs/pipeline.md |
| D3 | Deterministic player = baseline; LLM player = product | locked | docs/pipeline.md |
| D4 | Seed workbench (C) + LLM player (L) proprietary; score encoding (S2) + deterministic player (P) public | locked | docs/pipeline.md §Locked |
| D5 | Tools before spec freeze; a construct without corpus evidence doesn't ship | locked | docs/pipeline.md |
| D6 | Corpus ratchet: Bach → Byrd → Schubert → Beethoven 5 → Beethoven 9 | locked | docs/pipeline.md |
| D7 | No model training in the product path; LLM is stock + prompt | locked | docs/pipeline.md §Locked |
| D8 | Delta analysis produces design knowledge only — never training data | locked | docs/checkpoint-egg-model.md §4b |
| D9 | The mockup is dense DNA, not sketches (spike lesson) | locked | docs/spike.md |
| D10 | `.mu` is the working extension (launch decision deferred) | locked-for-dev | docs/design/e4-extension.md |
| D11 | Human evaluation is constant; founder's ear gates quality | locked | docs/vision.md |
| D12 | No artist lookalikes without explicit license record | locked | AGENTS.md §Ground rules |
| D13 | Provenance is mandatory in every manifest | locked | AGENTS.md §Ground rules |
| D14 | Documentation deliverable: README + test spec per code task | locked | TASK_WORKFLOW.md §Task definition |
| D15 | Multi-agent claiming: run-ids mandatory, newest claim comment decides | locked | AGENTS.md §Conventions |
| D16 | S4 operator set: exact/transposed/ostinato ship; invert/retro/imitative deferred (zero corpus evidence) | locked | FORMAT_SPEC §5.1 + docs/analysis-report.md |
| D17 | Philosophy fields: typed-lite vocabulary + free-text escape; identity guard with license_ref | locked | S3.3 (#144) + S3 SPEC decisions log |
| D18 | Container: SHA-256 member hashes; HMAC-SHA256 signature; PKI deferred | locked | FORMAT_SPEC §7.1 (#141) |
| D19 | S2 packing: varint columnar + zlib (stdlib, off-the-shelf); custom entropy coder is post-v1 | locked | FORMAT_SPEC §4.6 (#138) |
| D20 | The mockup is confidential pipeline state — never published, never exported by default; public surfaces are the `.mu` and rendered audio. DAWproject export is founder-gated. D4's open-at-launch plan stands; the private repo is the lock-down during development | locked | founder, 2026-08-24 session |
| D21 | `muse_docs` may make network calls, but only via the explicit `refresh-issues` command; `lint --check-issues` reads a local cache and stays offline. The lint's default path and the fast test tier never touch the network. Issues absent from the cache are unknown, not stale — never flagged | locked | #315 + tools/muse_docs/README.md §Status claims |
| D22 | Triage filing policy for the RLM Analyzer pass. An RLM report is unverified LLM triage: a finding becomes a task only after it is confirmed against raw files (D1). A refuted or stale finding gets no task; it is recorded in the triage summary with the evidence (D2). Generic web-application security advice (authn/authz, API validation, security headers, WAF, pen testing, SAST/DAST, log anomaly detection) does not apply to a repo with no running service and is not filed (D3). One task per verified finding, no bundling (D4). Anything needing a human choice is filed as a blocker for the owner, not decided by the agent (D5) | locked | portfolio-ops `rlm-triage-summary.md` (branch `tasks/rlm-triage-2026-10-01`) |

## Open decision points (tracking)

| # | Decision | Status | Tracking |
|---|---|---|---|
| O1 | E4: final extension at launch (`.mu` vs `.muse` vs `.muw`) | open | docs/design/e4-extension.md |
| O2 | L5: sample-quality waiver (commercial library vs revised bar) | conditional | docs/design/l5-sample-waiver.md |
| O3 | S6: vocal/choral text schema | open | docs/design/s6-vocal-text.md |
| O4 | W6: B9 compute scaling (suffix-array vs SIATEC-C vs sampling) | open | docs/design/w6-b9-scaling.md |

## How to add a decision

1. **Locked:** add to the Locked table with source.
2. **Open:** add to the Open table with tracking link.
3. **Resolved:** move from Open to Locked, close the tracking.
