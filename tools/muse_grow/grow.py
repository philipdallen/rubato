"""Growth harness: one iteration + compare against the prior delta.

grow_one(seed) → (delta, stand_in_flag). compare_deltas(new, prior) →
GrowthReport with a verdict per trait (growing / flat / regressing).

The mockup path is the deterministic L1 stand-in (same stand-in the probe
engine uses) — a flat mockup means growth cannot be measured, which the
report marks explicitly. When the real L1 generate loop lands, MOCKUP_FN
swaps to it here, same contract as the probe engine's pin.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

from muse_distill import seed_revision
from muse_mockup import Mockup, Note


def _mockup_from_work(work):
    """Deterministic L1 stand-in (same shape as the probe engine's stand-in):
    flat-velocity notes at score onsets with zero offsets."""
    mockup = Mockup(work_id=getattr(getattr(work, "meta", None), "title", None) or "unknown")
    mockup.ppq = getattr(getattr(work, "meta", None), "ppq", 480)  # the tick domain (#246)
    for p in work.parts:
        for n in p.notes:
            if n.pitch is None or "unpitched" in n.notations:
                continue
            mockup.notes.append(
                Note(
                    pitch=n.pitch,
                    onset=n.onset,
                    duration=n.duration,
                    velocity=64,
                    part=p.id,
                )
            )
    return mockup


def real_mockup(work, seed, provider=None):
    """The real L1 generate loop (L1.11 #276): generate → validate → fix
    via the founder-chosen ManualProvider conversation path. Returns the
    session-shape mockup converted to the Mockup dataclass.

    `provider` overrides the default conversation path (tests pass a
    RecordedProvider fixture so the loop runs offline)."""
    from muse_generate import generate_mockup
    from muse_provider import default_provider
    from muse_mockup import Mockup, Note
    if provider is None:
        provider = default_provider(live=False)
    mockup, _ = generate_mockup(seed, work, provider)
    m = Mockup(work_id=mockup["work_id"])
    for part_id, notes in mockup["parts"].items():
        for nd in notes:
            m.notes.append(Note(
                pitch=0, onset=nd["i"], duration=0, velocity=nd["velocity"],
                attack_ms=nd.get("attack_sec", 0.0) * 1000,
                release_ms=nd.get("release_sec", 0.0) * 1000,
                onset_offset_ms=nd.get("onset_offset_ms", 0.0),
                part=part_id))
    m.tempo_map = [(t["tick"], int(t["bpm"] * 1000))
                   for t in mockup.get("tempo_map", [])]
    return m


MOCKUP_FN = _mockup_from_work  # offline stand-in; real_mockup is the L1.11 live path


def persist_mockup(mockup, out_path, seed_path=None):
    """Write the producing mockup (S3.8b, #254). The file carries
    provenance.seed_hash — the SHA-256 of the seed it realizes — so the
    lineage walker can continue through the mockup hop to the parent seed.
    """
    from muse_mockup import dump_mockup
    from muse_lineage.lineage import sha256_file

    d = json.loads(dump_mockup(mockup, fmt="json"))
    if seed_path:
        d["provenance"] = {"seed_hash": sha256_file(seed_path)}
    with open(out_path, "w") as fh:
        fh.write(json.dumps(d, indent=1, sort_keys=True) + "\n")
    return out_path


def grow_one(work, seed, mockup_out=None, seed_path=None):
    """One iteration: build a mockup from the work via MOCKUP_FN, distill it,
    return (delta_dict, stand_in_flag). When mockup_out is given, the
    producing mockup is persisted first so the delta's extends names
    committed bytes (S3.8b).

    G4 (#252): the delta carries an `expansion` entry — wall-clock
    expansion_time_ms for the MOCKUP_FN build, keyed by operation tag
    (the seed's provenance.operation, or the harness default), with the
    seed's variation-point count and the work's note count. Measurement
    riding on the harness, per docs/design/proposal-lineage-chain.md §2.4.
    """
    operation = "muse_grow@1"
    if seed is not None:
        operation = getattr(seed, "provenance", {}).get("operation") or operation
    variation_points = len(getattr(seed, "variation_points", []) or [])

    t0 = time.perf_counter_ns()
    try:
        # L1.11 (#276): with a seed + the live gate, use the real generate
        # loop (stand_in=False); otherwise the deterministic stand-in.
        if seed is not None and os.environ.get("MUSE_L1_LIVE"):
            mockup, live = real_mockup(work, seed), False
        else:
            mockup, live = MOCKUP_FN(work), True
    except Exception as e:
        return {"error": f"mockup generation failed: {e}"}, True
    expansion_ms = (time.perf_counter_ns() - t0) / 1e6

    if mockup_out:
        persist_mockup(mockup, mockup_out, seed_path=seed_path)

    try:
        delta = seed_revision(mockup, mockup_path=mockup_out)
    except Exception as e:
        return {"error": f"distill failed: {e}"}, True

    delta["expansion"] = {
        "operation": operation,
        "expansion_time_ms": round(expansion_ms, 2),
        "variation_point_count": variation_points,
        "note_count": len(mockup.notes),
    }
    return delta, live


def _trait_delta(new_val, prior_val):
    """Numeric trait delta with a verdict."""
    try:
        diff = new_val - prior_val
    except TypeError:
        diff = None
    if diff is None or diff == 0:
        return {"verdict": "flat", "delta": 0}
    return {"verdict": "growing" if diff > 0 else "regressing", "delta": round(diff, 4)}


@dataclass
class GrowthReport:
    seed_id: str
    traits: dict = field(default_factory=dict)
    stand_in: bool = True

    def to_json(self) -> str:
        return json.dumps(
            {"seed_id": self.seed_id, "stand_in": self.stand_in,
             "traits": self.traits},
            sort_keys=True, indent=1,
        ) + "\n"


def compare_deltas(new_delta, prior_delta, seed_id, stand_in=True) -> GrowthReport:
    """Delta vs prior delta → per-trait growth report."""
    report = GrowthReport(seed_id=seed_id, stand_in=stand_in)

    numeric_traits = (
        ("velocity_pstdev", ("params", "dynamics", "velocity_pstdev")),
        ("rubato_pstdev_ms", ("params", "articulation", "rubato_pstdev_ms")),
        ("budget_position", ("params", "tempo", "default_bpm")),
        ("mockup_richness", ("provenance", None, "note_count")),
    )
    for name, (sec, sub, key) in numeric_traits:
        if sub is None:
            new_val = new_delta.get(sec, {}).get(key)
            old_val = prior_delta.get(sec, {}).get(key)
        else:
            new_val = new_delta["params"].get(sub, {}).get(key)
            old_val = prior_delta["params"].get(sub, {}).get(key)
        if isinstance(new_val, (int, float)) and isinstance(old_val, (int, float)):
            report.traits[name] = _trait_delta(new_val, old_val)
        else:
            report.traits[name] = {"verdict": "unknown", "delta": None}

    new_shape = new_delta.get("interpretation", {}).get("tempo_curve_shape")
    old_shape = prior_delta.get("interpretation", {}).get("tempo_curve_shape")
    report.traits["tempo_curve_shape"] = {
        "verdict": "same" if new_shape == old_shape else "changed",
        "from": old_shape,
        "to": new_shape,
    }
    return report
