"""Mockup → WAV through the sample pools (the sample tier).

Same timing contract as the sine tier: tempo_map converts ticks to
seconds, part_map gains apply per part, onset offsets apply per note.
Only the note source changes: real VSCO 2 CE recordings instead of an
envelope at the pitch frequency.

Per-part instrument mapping (VSCO 2 CE sections, sustain-vibrato):

    P1 -> Strings/Violin Section/susVib
    P2 -> Strings/Viola Section/susvib
    P3 -> Strings/Cello Section/susvib
    P4 -> Strings/Solo Contrabass/SusVib

The mapping is data (DEFAULT_INSTRUMENTS), not code: pass your own
{part: relative-path} to render_mockup_samples.
"""

from __future__ import annotations

import os
import wave

import numpy as np

from .pool import InstrumentPool

SR = 44100
LIBRARY = "VSCO 2 CE (via Rubato CDN)"

# Relative to the sample root (RUBATO_SAMPLE_ROOT or --sample-root).
DEFAULT_INSTRUMENTS = {
    "P1": os.path.join("Strings", "Violin Section", "susVib"),
    "P2": os.path.join("Strings", "Viola Section", "susvib"),
    "P3": os.path.join("Strings", "Cello Section", "susvib"),
    "P4": os.path.join("Strings", "Solo Contrabass", "SusVib"),
}


def ticks_to_sec(tick: int, tempo_map: list, ppq: int) -> float:
    sec = 0.0
    last_tick, last_bpm = 0, 120
    for mtick, mbpm in sorted(tempo_map or [(0, 120000)]):
        bpm = mbpm / 1000.0
        if tick <= mtick:
            break
        sec += (mtick - last_tick) * 60.0 / (last_bpm * ppq)
        last_tick, last_bpm = mtick, bpm
    sec += (tick - last_tick) * 60.0 / (last_bpm * ppq)
    return sec


def load_pools(sample_root: str, instruments=None) -> dict:
    instruments = instruments or DEFAULT_INSTRUMENTS
    pools = {}
    for part, rel in instruments.items():
        d = os.path.join(sample_root, rel)
        pools[part] = InstrumentPool(d, label=f"{part}:{rel}")
    return pools


def render_mockup_samples(mockup, pools: dict, out_path: str) -> dict:
    """Render a Mockup with the sample pools to a stereo 16-bit WAV."""
    mockup.validate()
    ppq = mockup.ppq or 480
    parts_gain = {}
    for name, info in (mockup.part_map or {}).items():
        parts_gain[name] = info.get("gain", 1.0) if isinstance(info, dict) else 1.0

    timed = []
    for n in mockup.notes:
        pool = pools.get(n.part)
        if pool is None:
            continue
        onset = ticks_to_sec(n.onset, mockup.tempo_map, ppq)
        dur = ticks_to_sec(n.onset + n.duration, mockup.tempo_map, ppq) - onset
        # The whole note shifts by its rubato offset; duration preserved.
        onset += (n.onset_offset_ms or 0.0) / 1000.0
        timed.append((onset, max(0.01, dur), n, pool,
                      parts_gain.get(n.part, 1.0)))
    if not timed:
        raise ValueError("no notes mapped to sample pools")

    max_end = max(t[0] + t[1] for t in timed) + 0.5
    buf = np.zeros((int(max_end * SR), 2), dtype=np.float32)
    for onset, dur, n, pool, gain in timed:
        seg = pool.note(n.pitch, n.velocity, dur)
        seg = seg * gain
        i0 = int(onset * SR)
        if i0 < 0:
            seg = seg[-i0:]
            i0 = 0
        i1 = min(len(buf), i0 + len(seg))
        if i1 <= i0:
            continue
        buf[i0:i1] += seg[: i1 - i0]

    peak = np.abs(buf).max()
    if peak > 1.0:
        buf = buf / peak
    s16 = (buf * 32767.0).astype(np.int16)
    with wave.open(out_path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(s16.tobytes())
    return {
        "out": out_path,
        "duration_sec": round(max_end, 3),
        "notes": len(timed),
        "parts": sorted({n.part for _, _, n, _, _ in timed}),
        "library": LIBRARY,
    }
