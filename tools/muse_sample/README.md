# muse_sample — the sample tier

Renders a Mockup through real instrument samples: the quality tier
above the sine stand-in. The samples are the **VSCO 2 CE** library
(CC0), served from the **Rubato CDN** — the highest-quality library the
CDN carries. VSCO ships raw WAV pools whose filenames encode pitch and
velocity layer (`VlnEns_susVib_A2_v1.wav`); no SFZ is needed.

## Usage

```bash
# Fetch the four string sections the tier renders with (101 files, ~238 MB)
python3 tools/muse_sample/fetch.py ./samples --token <CDN_TOKEN>

# Render a coaching candidate through the pools
python3 tools/muse_rehearse/cli.py render-dry-run \
  seeds/bwv227.1.seed.yaml "phrase: quieter at bar 8" \
  --tier samples --sample-root ./samples
# or set RUBATO_SAMPLE_ROOT once and omit --sample-root
```

## Contract

- `InstrumentPool(directory)`: indexes `{pitch: {layer: path}}` from
  VSCO filenames, decodes PCM WAVs (8/16/24/32-bit) with a cache.
- `pick(pitch, velocity)`: nearest sample at or below the pitch,
  nearest velocity layer. The VSCO strings lattice is sparse (a sample
  every few semitones), so shifts of up to ~3 semitones are normal.
- `note(pitch, velocity, dur)`: polyphase-resamples the picked sample
  to the target pitch, trims to duration + a short release tail,
  applies click-free fades and velocity scaling.
- `render_mockup_samples(mockup, pools, out_path)`: same timing
  contract as the sine renderer — the tempo map converts ticks to
  seconds, `part_map` gains apply, `onset_offset_ms` shifts notes —
  writing a stereo 16-bit WAV.
- `DEFAULT_INSTRUMENTS` maps the chorale parts to VSCO sections:
  P1 Violin Section susVib, P2 Viola Section susvib, P3 Cello Section
  susvib, P4 Solo Contrabass SusVib. The mapping is data, not code.

Deterministic per (work, seed): sample choice, resampling, and mixing
carry no randomness, so a candidate renders to identical bytes.
