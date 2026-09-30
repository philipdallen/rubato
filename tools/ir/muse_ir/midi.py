"""MIDI (.mid) -> IR parser, via mido.

Full maps from set_tempo / key_signature / time_signature meta events
(mid-piece changes preserved). Parts are tracks that contain notes; the
conductor track's meta events feed the work-level maps. Velocities come
from note_on; sources lacking velocity information mark it inferred.
"""

from __future__ import annotations

import struct
from collections import defaultdict, deque

import mido
from mido.midifiles.meta import KeySignatureError

from .model import (
    Instrument,
    IRParseError,
    Maps,
    Meta,
    Note,
    Part,
    Work,
)

# MIDI key_signature meta strings -> (fifths, mode)
_KEY_FIFTHS = {}
for _i, _k in enumerate(["Cb", "Gb", "Db", "Ab", "Eb", "Bb", "F", "C", "G", "D", "A", "E", "B", "F#", "C#"]):
    _KEY_FIFTHS[_k] = (_i - 7, "major")
for _i, _k in enumerate(["Abm", "Ebm", "Bbm", "Fm", "Cm", "Gm", "Dm", "Am", "Em", "Bm", "F#m", "C#m", "G#m", "D#m", "A#m"]):
    _KEY_FIFTHS[_k] = (_i - 7, "minor")


def _milli_bpm(tempo_us_per_quarter: int) -> int:
    if tempo_us_per_quarter <= 0:
        raise IRParseError(f"non-positive set_tempo value {tempo_us_per_quarter}")
    return round(60_000_000_000 / tempo_us_per_quarter)


def load_midi(source, origin: str = None) -> Work:
    """Parse a Standard MIDI File into a Work. Fails loudly on malformed input."""
    if origin is None:
        origin = getattr(source, "name", None) or str(source)
    try:
        mid = mido.MidiFile(file=source) if hasattr(source, "read") else mido.MidiFile(source)
    except (OSError, ValueError, EOFError, IndexError, struct.error, KeySignatureError) as exc:
        raise IRParseError(f"{origin}: unreadable MIDI file: {exc}") from exc
    if mid.type == 2:
        raise IRParseError(f"{origin}: MIDI type 2 (asynchronous) is not supported")
    if mid.ticks_per_beat <= 0:
        raise IRParseError(
            f"{origin}: SMPTE time division is not supported (ticks_per_beat={mid.ticks_per_beat})"
        )
    ppq = mid.ticks_per_beat
    warnings: list = []

    tempo: dict = {}
    meter: dict = {}
    key: set = set()
    parts = []
    title = None
    lyric_meta_count = 0

    for track_index, track in enumerate(mid.tracks):
        tick = 0
        track_name = None
        gm_program = None
        open_notes: dict = defaultdict(deque)  # (channel, pitch) -> deque of (onset, velocity, inferred)
        notes = []
        velocity_inferred_count = 0
        for msg in track:
            tick += msg.time
            if msg.type == "track_name" and track_name is None:
                track_name = msg.name
            elif msg.type == "set_tempo":
                mb = _milli_bpm(msg.tempo)
                prev = tempo.get(tick)
                if prev is not None and prev != mb:
                    raise IRParseError(
                        f"{origin}: conflicting tempo at tick {tick}: {prev} vs {mb} milli-bpm"
                    )
                tempo[tick] = mb
            elif msg.type == "time_signature":
                prev = meter.get(tick)
                value = (msg.numerator, msg.denominator)
                if prev is not None and prev != value:
                    raise IRParseError(
                        f"{origin}: conflicting meter at tick {tick}: {prev} vs {value}"
                    )
                meter[tick] = value
            elif msg.type == "key_signature":
                if msg.key not in _KEY_FIFTHS:
                    raise IRParseError(f"{origin}: unknown key signature {msg.key!r}")
                fifths, mode = _KEY_FIFTHS[msg.key]
                key.add((tick, fifths, mode))
            elif msg.type == "lyrics":
                # Lyric meta (0x05) is deliberately unimplemented (no texted
                # MIDI in the corpus), but the loss must be audible (#365).
                lyric_meta_count += 1
            elif msg.type == "program_change":
                if gm_program is None:
                    gm_program = msg.program
            elif msg.type == "note_on" and msg.velocity > 0:
                open_notes[(msg.channel, msg.note)].append((tick, msg.velocity, False))
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                queue = open_notes.get((msg.channel, msg.note))
                if not queue:
                    raise IRParseError(
                        f"{origin}: track {track_index}: note_off without note_on "
                        f"(channel={msg.channel}, pitch={msg.note}, tick={tick})"
                    )
                onset, velocity, inferred = queue.popleft()
                if tick - onset <= 0:
                    raise IRParseError(
                        f"{origin}: track {track_index}: non-positive note duration "
                        f"at tick {onset}"
                    )
                if inferred:
                    velocity_inferred_count += 1
                notes.append(
                    Note(pitch=msg.note, onset=onset, duration=tick - onset, velocity=velocity,
                         velocity_inferred=inferred)
                )
        dangling = [(ch, p, q[0][0], q[0][2]) for (ch, p), q in open_notes.items() if q]
        if dangling:
            ch, p, onset, _inferred = dangling[0]
            raise IRParseError(
                f"{origin}: track {track_index}: note_on never closed "
                f"(channel={ch}, pitch={p}, onset={onset})"
            )
        if not notes:
            # Conductor / control tracks feed maps only.
            if track_index == 0 and title is None and track_name:
                title = track_name
            continue
        pid = f"track{track_index}"
        part = Part(
            id=pid,
            name=track_name or pid,
            instrument=Instrument(name=track_name, gm_program=gm_program),
            notes=notes,
            inferred_voice=True,  # MIDI carries no voice/staff assignment
        )
        if velocity_inferred_count:
            part.warnings.append(
                f"{velocity_inferred_count} note(s) had inferred velocity (64)"
            )
        part.sort_notes()
        parts.append(part)

    if not parts:
        raise IRParseError(f"{origin}: no tracks with notes found")
    if 0 not in tempo:
        warnings.append("no set_tempo meta event; inserted MIDI default 120 bpm at tick 0")
        tempo[0] = 120_000
    if 0 not in meter:
        warnings.append("no time_signature meta event; inserted 4/4 at tick 0")
        meter[0] = (4, 4)
    if lyric_meta_count:
        warnings.append(
            f"{lyric_meta_count} lyric event(s) ignored — MIDI lyric import is not implemented"
        )

    work = Work(
        parts=parts,
        maps=Maps(
            tempo=sorted(tempo.items()),
            meter=sorted((t, n, d) for t, (n, d) in meter.items()),
            key=sorted(key),
        ),
        meta=Meta(source_format="midi", ppq=ppq, title=title, warnings=warnings),
    )
    work.validate()
    return work
