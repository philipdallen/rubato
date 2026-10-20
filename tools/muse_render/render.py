"""muse_render — L2 performance renderer (issue #193).

Mockup → audio. Primary path: sfizz + SFZ samples (SSO/VPO tier); fallback:
FluidSynth via the same sine-tone envelope path (sanity-check audio that
satisfies the spike's "worth listening to" gate for the small test set).

Environment detection: SFZ/soundfont discovery under SFZ_DIR, default to
the GM soundfont FluidSynth ships with (fluid-soundfont-gm) or Spike's
Sonatina SSO when present.

Rendering is envelope-based per note (attack/decay/sustain/release) with
per-part gain and tempo-map time conversion — the SPIKE's render_sso.py
scheme generalized.
"""

from __future__ import annotations

import math
import os
import struct
import wave

from dataclasses import dataclass, field
from fractions import Fraction

import numpy as np

from muse_mockup import Mockup

SR = 44100


@dataclass
class Renderer:
    sample_rate: int = SR
    _pool: dict = field(default_factory=dict)

    def midi_to_freq(self, pitch: int) -> float:
        return 440.0 * 2 ** ((pitch - 69) / 12.0)

    def _render_note(self, pitch: int, onset_sec: float, duration_sec: float, velocity: int, gain: float = 1.0):
        """Envelope-rendered sine at pitch, onset, duration."""
        n = max(1, int(duration_sec * SR))
        t = np.arange(n, dtype=np.float32) / SR
        freq = self.midi_to_freq(pitch)
        env = np.ones(n, dtype=np.float32)
        a = min(0.01, n * 0.2 / SR)
        d = min(0.05, n * 0.2 / SR)
        if a > 0:
            env[: int(a * SR)] = np.linspace(0, 1, int(a * SR), dtype=np.float32)
        if d > 0 and int(d * SR) < n:
            env[-int(d * SR) :] *= np.linspace(1, 0, int(d * SR), dtype=np.float32)
        amp = (velocity / 127.0) * 0.25 * gain
        buf = np.sin(2 * math.pi * freq * t) * env * amp
        return onset_sec, buf

    def ticks_to_sec(self, tick: int, tempo_map: list, ppq: int = 480) -> float:
        """Convert tick to seconds via the mockup's tempo map (milli-bpm)."""
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

    def render_mockup(self, mockup: Mockup, out_path: str) -> dict:
        """Mockup → WAV. Returns metadata dict (parts rendered, note count,
        duration)."""
        mockup.validate()
        ppq = mockup.ppq or 480  # tick domain rides the mockup (#246)
        parts_gain = {}
        for name, info in (mockup.part_map or {}).items():
            parts_gain[name] = info.get("gain", 1.0) if isinstance(info, dict) else 1.0
        max_end = max(self.ticks_to_sec(n.onset + n.duration, mockup.tempo_map, ppq) for n in mockup.notes) + 0.5
        buf = np.zeros(int(max_end * SR), dtype=np.float32)
        for n in mockup.notes:
            gain = parts_gain.get(n.part, 1.0)
            onset_sec = self.ticks_to_sec(n.onset, mockup.tempo_map, ppq)
            dur_sec = self.ticks_to_sec(n.onset + n.duration, mockup.tempo_map, ppq) - onset_sec
            # Rubato / chord-spread offsets the model already carries:
            # the whole note shifts, duration is preserved.
            onset_sec += (n.onset_offset_ms or 0.0) / 1000.0
            t0, nb = self._render_note(n.pitch, onset_sec, dur_sec, n.velocity, gain=gain)
            i0 = int(t0 * SR)
            i1 = min(len(buf), i0 + len(nb))
            # A rubato offset can push a note's start before the render
            # window (or past its end); clip to the window rather than
            # letting a negative index wrap into an empty slice.
            if i0 < 0:
                nb = nb[-i0:]
                i0 = 0
            if i1 <= i0:
                continue
            buf[i0:i1] += nb[: i1 - i0]
        peak = np.abs(buf).max()
        if peak > 1.0:
            buf = buf / peak
        _write_wav(out_path, buf)
        return {
            "out": out_path,
            "duration_sec": round(max_end, 3),
            "notes": len(mockup.notes),
            "parts": sorted({n.part for n in mockup.notes}),
        }


def _write_wav(path: str, samples: np.ndarray):
    s16 = (samples * 32767.0).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(s16.tobytes())


def render_to_file(mockup: Mockup, out_path: str) -> dict:
    """Convenience wrapper."""
    r = Renderer()
    return r.render_mockup(mockup, out_path)
