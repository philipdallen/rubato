# muse_ci — P3 conformance suite

Golden vectors pinning the reference decoder: the objective definition of
"conforming decoder." Design doc:
[docs/design/p3-conformance-suite.md](../../docs/design/p3-conformance-suite.md).

A vector is a (`.ru` container → decoded event stream) pair:

- **Input:** `vectors/<work-id>.ru` — committed binary container (S5:
  manifest.json + roll.bin + seed.bin), built from the corpus via W1 → S2
  → S5. Committed, not regenerated at gate time, so the gate pins the
  *decoder* independently of encoder drift.
- **Expected output:** `vectors/pins.json` — per work, sha256 + byte count
  of the S1 canonical JSON (FORMAT_SPEC §4.4) of the P1-decoded Work.
  The full canonical JSON is not duplicated here — s1_stream/golden
  already pins that content; on a mismatch, `dump` reproduces the actual
  stream for diffing.

## Usage

```bash
python3 tools/muse_ci/cli.py verify            # fast registry (the gate)
python3 tools/muse_ci/cli.py verify --full     # all 14 corpus works
python3 tools/muse_ci/cli.py generate --full   # rebuild vectors/ from corpus
python3 tools/muse_ci/cli.py dump <work-id> -o actual.json   # mismatch forensics
```

`verify` exits 0 when every selected vector conforms, 1 otherwise; decode
errors are FAIL, never exceptions.

## Regeneration discipline

The registry is pinned to `corpus/README.md` (and mirrors
`muse_chain.chain.REGISTRY`). After any IR / S2 / S5 / P1 change, run
`generate --full` and re-pin in the same commit as the change — a silent
drift is exactly what the gate exists to catch. Regeneration reproducing
the committed pins byte-for-byte is itself tested
(`test_conformance_full.py`).

## API

- `build_mu(work_id, relpath, out_path)` — corpus source → `.ru` (fails on
  non-deterministic S2 pack).
- `decoded_canonical(mu_path) -> bytes` — `.ru` → P1 decode → S1 canonical
  JSON bytes.
- `generate(vectors_dir, registry)` / `verify(vectors_dir, registry)` —
  store rebuild / gate. `verify` returns `VectorResult(work_id, status,
  detail)`.
- `REGISTRY` (14 works), `FAST_REGISTRY` (3-work smoke subset),
  `VECTORS_DIR`.

## Dependencies

`tools/ir` (muse_ir), `tools/muse_roll`, `tools/muse_mu` (vector build),
`tools/muse_decode` (P1, the system under test), `tools/s1_stream`
(canonical form). Runtime deps per `tools/requirements.test.txt`.

## Tests

```
cd tools && python -m pytest muse_ci/tests -q
```

43 tests: full-registry gate, store integrity (schema, coverage, valid
containers), tamper detection (corrupted pin, flipped roll byte, missing
.ru, missing pin), decode determinism, CLI behavior, corpus coverage, and
regeneration fidelity. Test spec:
[tests/closed_20260824-104500_p3-conformance-suite.md](../../tests/closed_20260824-104500_p3-conformance-suite.md).
