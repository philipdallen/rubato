"""muse_audio — workbench render bridge: seed revision → mockup → WAV.

Closes the ear gap in the seed-iteration loop: the workbench page
(docs/workbench/detail.html) shows seed + probes + growth diffs, but "did
this seed change do what I intended?" needs audio. This tool renders each
committed seed revision to docs/audio/<work_id>.<label>.wav and writes a
manifest the page reads.

Two mockup paths, same WAV convention:

- **stand-in (default, deterministic):** flat-velocity notes (the probe
  engine / G1 stand-in) parametrized by the seed's tempo range — arch
  shape from the seed's energy.shape, peaking at max_bpm, floor at
  min_bpm. Deterministic per (work, seed): re-rendering a committed
  revision reproduces its WAV byte-for-byte.
- **live (--live):** the real L1.3 generate loop (muse_generate) through
  GeminiProvider(live=True). Labeled separately in the manifest
  (origin: llm-live) — a live reading is an artifact of a moment, never
  regenerated silently.

D20: WAVs only. Mockups never leave the pipeline; only audio lands in
docs/audio/ for the static site.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
from dataclasses import dataclass, field

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIO_DIR = os.path.join(REPO, "docs", "audio")
MANIFEST_NAME = "manifest.json"

ARCH_POINTS = 8  # tempo_map resolution for the arch shape
_FLEX_SAMPLES = 16  # tempo_map resolution inside a tempo_flex region
_RUBATO_SEED = 0xC0AC4  # fixed PRNG seed: rubato offsets are deterministic


@dataclass
class RenderResult:
    work_id: str
    label: str
    origin: str            # stand-in | llm-live
    wav: str               # filename relative to docs/audio/
    duration_sec: float
    notes: int
    sha256: str


def _flex_multiplier(variation_points, tick):
    """Raised-cosine tempo dip for tempo_flex variation points.

    Each point eases the tempo to ``1 - budget`` at its region midpoint
    and restores by the region end; overlapping regions multiply. This is
    what the ``phrase`` directive sounds like. (The directive compiler
    does not stamp the phrase's direction into the variation point, so
    the curve is one fixed shape; stamping direction is a compiler
    follow-up.)
    """
    mult = 1.0
    for vp in variation_points or []:
        if not isinstance(vp, dict) or vp.get("kind") != "tempo_flex":
            continue
        region = vp.get("region") or [0, 0]
        start, end = region[0], region[1]
        if end <= start or tick < start or tick >= end:
            continue
        budget = vp.get("budget", 0.2) or 0.0
        x = (tick - start) / (end - start)
        mult *= 1.0 - budget * (math.sin(math.pi * x) ** 2)
    return mult


def _stand_in_mockup(work, seed):
    """Deterministic mockup parametrized by the seed's audible params.

    Same flat notes as the probe engine stand-in, but the seed's
    interpretive parameters shape the performance, so a coaching
    directive is audible in the WAV:

    - ``params.tempo`` min/max bpm: arch tempo map (endpoints at min,
      peak at max) — what ``tempo_arch`` sounds like;
    - ``variation_points`` of kind ``tempo_flex``: raised-cosine dip
      multiplied onto the arch inside each region — what ``phrase``
      sounds like;
    - ``params.part_gains``: per-part gain in the mockup's part_map,
      which the renderer applies — what ``rebalance`` sounds like;
    - ``params.articulation.rubato_pstdev_ms``: per-note onset offsets
      from a fixed-seed Gaussian — what ``rubato`` sounds like.

    Deterministic per (work, seed): the rubato PRNG is fixed-seed, so
    re-rendering reproduces the WAV byte-for-byte.
    """
    from muse_mockup import Mockup, Note

    mockup = Mockup(work_id=getattr(getattr(work, "meta", None), "title", None) or "unknown")
    params = getattr(seed, "params", {}) or {} if seed is not None else {}
    gains = params.get("part_gains", {}) or {}
    articulation = params.get("articulation", {}) or {}
    rubato_ms = articulation.get("rubato_pstdev_ms", 0.0) or 0.0
    vps = getattr(seed, "variation_points", []) or [] if seed is not None else []

    rng = random.Random(_RUBATO_SEED)
    for p in work.parts:
        for n in p.notes:
            if n.pitch is None or "unpitched" in n.notations:
                continue
            offset = rng.gauss(0.0, rubato_ms) if rubato_ms else 0.0
            mockup.notes.append(Note(pitch=n.pitch, onset=n.onset,
                                     duration=n.duration, velocity=64,
                                     onset_offset_ms=offset, part=p.id))
    for part, gain in gains.items():
        mockup.part_map[part] = {"gain": gain}

    tempo = params.get("tempo", {}) or {}
    lo = float(tempo.get("min_bpm", 60))
    hi = float(tempo.get("max_bpm", 120))
    last_tick = max((n.onset + n.duration for n in mockup.notes), default=0)
    ticks = {round(last_tick * k / ARCH_POINTS) for k in range(ARCH_POINTS + 1)}
    for vp in vps:
        if not isinstance(vp, dict) or vp.get("kind") != "tempo_flex":
            continue
        region = vp.get("region") or [0, 0]
        start, end = region[0], region[1]
        if end > start:
            for i in range(_FLEX_SAMPLES + 1):
                ticks.add(int(start + (end - start) * i / _FLEX_SAMPLES))
    for tick in sorted(ticks):
        x = tick / last_tick if last_tick else 0
        bpm = lo + (hi - lo) * 4 * x * (1 - x)
        bpm *= _flex_multiplier(vps, tick)
        mockup.tempo_map.append((tick, round(max(1.0, bpm) * 1000)))  # milli-bpm
    return mockup


def _schema_dict_to_mockup(d, work):
    """Schema-v1 indexed mockup dict (the generate loop's wire format) →
    Mockup model. Notes are {"i": index into the part's IR note order,
    velocity, devices}; pitch/onset/duration resolve from the score —
    the fidelity guard already pinned onsets, so this is lossless by
    construction. Rests/unpitched entries are skipped like the stand-in.
    """
    from muse_mockup import Mockup, Note

    mockup = Mockup(work_id=d.get("work_id") or "unknown")
    mockup.ppq = getattr(getattr(work, "meta", None), "ppq", 480)  # the tick domain (#246)
    mockup.tempo_map = [(e["tick"], round(e["bpm"] * 1000))
                        for e in d.get("tempo_map", [])]
    if d.get("dynamics"):
        mockup.curves["dynamics"] = [(e["tick"], e["level"])
                                     for e in d["dynamics"]]
    for entry in d.get("balance", []):
        mockup.part_map[entry["part"]] = {"gain": entry["gain"]}
    for part_id, notes in d.get("parts", {}).items():
        src = next((p for p in work.parts if p.id == part_id), None)
        if src is None:
            continue
        for entry in notes:
            i = entry.get("i")
            if i is None or i >= len(src.notes):
                continue
            ref = src.notes[i]
            if ref.pitch is None or "unpitched" in ref.notations:
                continue
            swell_pts = entry.get("swell") or []
            swell = sum(l for _, l in swell_pts) / len(swell_pts) if swell_pts else 0.0
            mockup.notes.append(Note(
                pitch=ref.pitch, onset=ref.onset, duration=ref.duration,
                velocity=entry.get("velocity", 64),
                onset_offset_ms=entry.get("onset_offset_ms", 0.0),
                attack_ms=entry.get("attack_sec", 0.0) * 1000.0,
                release_ms=entry.get("release_sec", 0.0) * 1000.0,
                swell=swell, part=part_id))
    return mockup


def _live_mockup(work, seed, provider):
    """The real L1.3 loop: generate → validate → fix (bounded)."""
    from muse_generate import generate_mockup

    mockup_dict, _attempts = generate_mockup(seed, work, provider)
    return _schema_dict_to_mockup(mockup_dict, work)


def _render_mockup_to_wav(work, mockup, out_path):
    """Stamp ppq, validate, render, hash. Shared by the revision and
    candidate paths."""
    from muse_render import render_to_file

    # L2 renders in the mockup's tick domain — stamp the work's resolution
    # (mxl parses to ppq=2; the renderer defaults to 480 otherwise).
    mockup.ppq = work.meta.ppq
    mockup.validate()

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    meta = render_to_file(mockup, out_path)
    with open(out_path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    return meta, digest


def render_seed(work, seed, out_path, tier="sine", sample_root=None):
    """Render an in-memory (possibly uncommitted) seed to a WAV file.

    The coaching loop's ear: a directive compiles to a candidate seed,
    this renders what the candidate sounds like. Deterministic per
    (work, seed) — same candidate always yields the same bytes.

    ``tier="sine"`` is the instant stand-in (envelope at pitch
    frequency, sub-second). ``tier="samples"`` renders through the
    sample pools (VSCO 2 CE from the Rubato CDN) — higher quality,
    slower; needs ``sample_root`` (or the ``RUBATO_SAMPLE_ROOT`` env).
    """
    if tier == "samples":
        from muse_sample import load_pools, render_mockup_samples
        root = sample_root or os.environ.get("RUBATO_SAMPLE_ROOT")
        if not root or not os.path.isdir(root):
            raise SampleRootMissing(
                "tier=samples needs a sample root: pass sample_root or set "
                "RUBATO_SAMPLE_ROOT")
        mockup = _stand_in_mockup(work, seed)
        mockup.ppq = work.meta.ppq
        meta = render_mockup_samples(mockup, load_pools(root), out_path)
        with open(out_path, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        return meta["duration_sec"], meta["notes"], digest, meta["library"]
    mockup = _stand_in_mockup(work, seed)
    meta, digest = _render_mockup_to_wav(work, mockup, out_path)
    return meta["duration_sec"], meta["notes"], digest, "sine stand-in"


class SampleRootMissing(FileNotFoundError):
    """tier=samples was requested without a sample root."""


def render_revision(work_path, seed_path, label, out_dir=AUDIO_DIR,
                    live=False, provider=None):
    """Render one (work, seed revision) to <work_id>.<label>.wav.

    Returns a RenderResult. live=True runs the LLM generate loop via the
    given provider (default: GeminiProvider(live=True)); otherwise the
    deterministic stand-in is used.
    """
    from muse_ir import load
    from muse_seed import load_seed

    work = load(work_path)
    seed = None
    if seed_path is not None:
        with open(seed_path) as fh:
            seed = load_seed(fh.read(), fmt="yaml")

    if live:
        if provider is None:
            from muse_provider import GeminiProvider
            provider = GeminiProvider(live=True)
        mockup = _live_mockup(work, seed, provider)
        origin = "llm-live"
    else:
        mockup = _stand_in_mockup(work, seed)
        origin = "stand-in"

    work_id = getattr(seed, "work_id", None) or mockup.work_id
    wav_name = f"{work_id}.{label}.wav"
    out_path = os.path.join(out_dir, wav_name)
    meta, digest = _render_mockup_to_wav(work, mockup, out_path)
    return RenderResult(work_id=work_id, label=label, origin=origin,
                        wav=wav_name, duration_sec=meta["duration_sec"],
                        notes=meta["notes"], sha256=digest)


def write_manifest(results, out_dir=AUDIO_DIR):
    """Write docs/audio/manifest.json — the page's audio index."""
    works = {}
    for r in results:
        works.setdefault(r.work_id, {})[r.label] = {
            "file": r.wav, "origin": r.origin,
            "duration_sec": r.duration_sec, "notes": r.notes,
            "sha256": r.sha256,
        }
    path = os.path.join(out_dir, MANIFEST_NAME)
    with open(path, "w") as fh:
        json.dump({"format": "muse-audio-manifest-v1", "works": works},
                  fh, indent=1, sort_keys=True)
        fh.write("\n")
    return path
