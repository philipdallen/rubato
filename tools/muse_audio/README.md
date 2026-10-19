# muse_audio — workbench render bridge (issue #243)

Seed revision → mockup → WAV, closing the ear gap in the seed-iteration
loop (`docs/seed-iteration.md`). The workbench page
(`docs/workbench/detail.html`) shows seed + probes + growth diffs; this
tool produces the audio the page's per-revision players point at.

## Usage

```bash
# deterministic stand-in renders (both committed bwv227.1 revisions):
python3 tools/muse_audio/cli.py corpus/bach/bwv227.1.mxl \
    --seed seeds/bwv227.1.v1.seed.yaml --label v1
python3 tools/muse_audio/cli.py corpus/bach/bwv227.1.mxl \
    --seed seeds/bwv227.1.v2.seed.yaml --label v2

# live LLM render (real L1.3 loop, Gemini free tier):
python3 tools/muse_audio/cli.py corpus/bach/bwv227.1.mxl \
    --seed seeds/bwv227.1.v2.seed.yaml --label v2 --live
```

Then rebuild `docs/audio/manifest.json` from the rendered set via
`muse_audio.write_manifest(...)` (see cli output). The manifest is
committed (it is the page's index); WAVs stay session-local per
`docs/audio/README.md` (regenerate on demand — stand-ins reproduce
byte-for-byte; `llm-*` entries are artifacts of a moment).

## Mockup paths

- **stand-in** (default): flat-velocity notes (probe-engine/G1 stand-in
  convention) parametrized by the seed's tempo range — arch shape peaking
  at `max_bpm`, floor at `min_bpm`, so a seed revision that moves the
  tempo range is audible. Deterministic per (work, seed).
- **live** (`--live`): `muse_generate.generate_mockup` through
  `GeminiProvider(live=True)`. The schema-v1 indexed dict is converted to
  the Mockup model (`_schema_dict_to_mockup`); the work's ppq is stamped
  so L2 renders real durations (#246).

D20: WAVs only cross the boundary. Mockups never leave the pipeline.

## API

- `render_revision(work_path, seed_path, label, out_dir=..., live=False,
  provider=None) -> RenderResult`
- `write_manifest(results, out_dir=...) -> path`
- `AUDIO_DIR` (docs/audio), `RenderResult` dataclass

## Dependencies

tools/ir, tools/muse_seed, tools/muse_mockup, tools/muse_render,
tools/muse_generate + tools/muse_provider (live path only). Runtime deps
per `tools/requirements.test.txt`.

## Tests

```
cd tools && python -m pytest muse_audio -q
```

Test spec: [tests/closed_20260824-233000_workbench-audio.md](../../tests/closed_20260824-233000_workbench-audio.md).
