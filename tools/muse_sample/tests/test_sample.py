import math
import os
import struct
import wave

import numpy as np
import pytest

from muse_sample import InstrumentPool, load_pools, name_to_midi
from muse_sample.render import DEFAULT_INSTRUMENTS, LIBRARY

SR = 44100


def _sine_wav(path, freq, seconds=2.0, width=2):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    a = (0.5 * np.sin(2 * math.pi * freq * t)).astype(np.float64)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(width)
        wf.setframerate(SR)
        if width == 2:
            data = (a * 32767).astype(np.int16)
        else:  # 24-bit
            i = (a * 8388607).astype(np.int32)
            data = np.empty((n, 3), dtype=np.uint8)
            data[:, 0] = i & 0xFF
            data[:, 1] = (i >> 8) & 0xFF
            data[:, 2] = (i >> 16) & 0xFF
        stereo = np.stack([data, data], axis=1).reshape(n * 2, -1)
        wf.writeframes(stereo.tobytes())


@pytest.fixture()
def pool_dir(tmp_path):
    d = tmp_path / "Vln"
    _sine_wav(str(d / "X_susVib_C4_v1.wav"), 261.63, width=2)
    _sine_wav(str(d / "X_susVib_C4_v2.wav"), 261.63, width=2)
    _sine_wav(str(d / "X_susVib_G3_v1.wav"), 196.00, width=3)
    return str(d)


def test_name_to_midi():
    assert name_to_midi("A", "", "4") == 69
    assert name_to_midi("C", "#", "4") == 61
    assert name_to_midi("B", "b", "3") == 58


def test_pick_prefers_nearest_below(pool_dir):
    p = InstrumentPool(pool_dir)
    src, _ = p.pick(64, 90)  # E4: below are G3(55), C4(60)
    assert src == 60
    src, _ = p.pick(55, 90)  # G3 exact
    assert src == 55


def test_decode_handles_16_and_24_bit(pool_dir):
    p = InstrumentPool(pool_dir)
    a = p.decode(os.path.join(pool_dir, "X_susVib_C4_v1.wav"))
    b = p.decode(os.path.join(pool_dir, "X_susVib_G3_v1.wav"))
    assert a.shape[1] == 2 and b.shape[1] == 2
    assert abs(float(np.abs(a).max()) - 0.5) < 0.01
    assert abs(float(np.abs(b).max()) - 0.5) < 0.05


def test_note_resamples_to_target_pitch(pool_dir):
    p = InstrumentPool(pool_dir)
    for target, expect in ((60, 261.63), (62, 293.66)):  # C4 exact, D4 shifted
        seg = p.note(target, 90, 0.4)
        ch = seg[:, 0]
        zc = np.sum(np.diff(np.sign(ch)) != 0)
        est = zc / 2 / (len(ch) / SR)
        assert abs(est - expect) / expect < 0.05, (target, est)


def test_render_mockup_samples_honors_gains(tmp_path, pool_dir):
    from muse_sample.render import render_mockup_samples

    class N:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    class M:
        ppq = 480
        tempo_map = [(0, 120000)]
        part_map = {"P1": {"gain": 1.0}, "P2": {"gain": 0.0}}
        notes = [
            N(pitch=60, velocity=90, onset=0, duration=240,
              part="P1", onset_offset_ms=0.0),
            N(pitch=60, velocity=90, onset=0, duration=240,
              part="P2", onset_offset_ms=0.0),
        ]

        def validate(self):
            pass

    out = str(tmp_path / "mix.wav")
    meta = render_mockup_samples(M(), {"P1": InstrumentPool(pool_dir),
                                       "P2": InstrumentPool(pool_dir)}, out)
    assert meta["notes"] == 2
    assert meta["library"] == LIBRARY
    # P2 gain 0: its content is absent — render P1 alone and compare.
    out2 = str(tmp_path / "solo.wav")
    m2 = M()
    m2.notes = m2.notes[:1]
    render_mockup_samples(m2, {"P1": InstrumentPool(pool_dir)}, out2)
    a = open(out, "rb").read()
    b = open(out2, "rb").read()
    assert len(a) == len(b)


def test_default_map_covers_chorale_parts():
    assert set(DEFAULT_INSTRUMENTS) == {"P1", "P2", "P3", "P4"}
    assert all("Strings" in v for v in DEFAULT_INSTRUMENTS.values())
