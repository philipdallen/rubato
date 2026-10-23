"""Sample pool: VSCO-style raw sample directories → pitched instruments.

A pool maps a directory of WAVs whose filenames encode pitch and
velocity layer (``VlnEns_susVib_A2_v1.wav``: articulation, pitch A2,
layer v1) to a per-note sample picker. No SFZ needed: the CDN carries
the raw VSCO 2 CE pool, and the names are self-describing.

pick(pitch, velocity) returns (samples, recorded_pitch) for the nearest
sample at or below the target pitch (prefer the sample whose pitch is
closest without exceeding, like most samplers' keyzones), then the
velocity layer nearest the note velocity.
"""

from __future__ import annotations

import os
import re
from fractions import Fraction

import numpy as np
from scipy.signal import resample_poly

_NAME_TO_SEMI = {
    "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11,
}
_PITCH_RE = re.compile(r"_([A-G])([#b]?)(-?\d)_v(\d)")
_SR = 44100


def name_to_midi(token: str, acc: str, octave: str) -> int:
    return _NAME_TO_SEMI[token] + {"#": 1, "b": -1, "": 0}[acc] + (int(octave) + 1) * 12


class InstrumentPool:
    """A pitched sample set from one VSCO articulation directory."""

    def __init__(self, directory: str, label: str = ""):
        self.directory = directory
        self.label = label or os.path.basename(directory)
        # midi -> {layer: path}
        self.index = {}
        for fname in sorted(os.listdir(directory)):
            if not fname.lower().endswith(".wav"):
                continue
            m = _PITCH_RE.search(fname)
            if not m:
                continue
            midi = name_to_midi(m.group(1), m.group(2), m.group(3))
            self.index.setdefault(midi, {})[int(m.group(4))] = os.path.join(
                directory, fname)
        if not self.index:
            raise ValueError(f"no pitched WAVs in {directory}")
        self._cache = {}

    def pick(self, pitch: int, velocity: int):
        """Nearest sample at or below the pitch; nearest velocity layer."""
        below = [m for m in self.index if m <= pitch]
        src = max(below) if below else min(self.index)
        layers = self.index[src]
        # Layer 1 ~ soft reference velocity 0, layer 2 ~ loud reference 90;
        # nearest reference wins, then the lower layer on ties.
        layer = min(layers, key=lambda l: (abs((l - 1) * 90 - velocity), l))
        return src, layers[layer]

    def decode(self, path: str) -> np.ndarray:
        """PCM WAV → float32 array (frames, channels), cached."""
        if path not in self._cache:
            import wave
            with wave.open(path, "rb") as wf:
                n = wf.getnframes()
                ch = wf.getnchannels()
                width = wf.getsampwidth()
                raw = wf.readframes(n)
            if width == 1:
                a = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
                     - 128.0) / 128.0
            elif width == 2:
                a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            elif width == 3:
                b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
                i32 = (b[:, 0].astype(np.int32)
                       | (b[:, 1].astype(np.int32) << 8)
                       | (b[:, 2].astype(np.int32) << 16))
                i32 = np.where(i32 >= 0x800000, i32 - 0x1000000, i32)
                a = i32.astype(np.float32) / 8388608.0
            elif width == 4:
                a = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
            else:
                raise ValueError(f"unsupported sample width {width}: {path}")
            self._cache[path] = a.reshape(n, ch)
        return self._cache[path]

    def note(self, pitch: int, velocity: int, dur_sec: float,
             release_sec: float = 0.15) -> np.ndarray:
        """Resample the picked sample to the target pitch and trim to
        the note duration plus a short release tail."""
        src, path = self.pick(pitch, velocity)
        data = self.decode(path)
        ratio = 2.0 ** ((pitch - src) / 12.0)
        # Source frames needed at the recorded rate for the target length.
        need_src = int((dur_sec + release_sec) * _SR * ratio) + 1
        seg = data[:need_src]
        frac = Fraction(ratio).limit_denominator(64)
        out = resample_poly(seg, frac.denominator, frac.numerator, axis=0)
        target = int(dur_sec * _SR)
        total = target + int(release_sec * _SR)
        if len(out) < total:
            pad = np.zeros((total - len(out), out.shape[1]), dtype=np.float32)
            out = np.concatenate([out, pad])
        out = out[:total]
        # Click-free entry and a short release fade on the tail.
        fade_in = min(int(0.005 * _SR), len(out))
        out[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
        fade_out = min(int(release_sec * _SR), len(out))
        out[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]
        # Velocity around the middle layer's reference.
        out *= (velocity / 90.0)
        return out
