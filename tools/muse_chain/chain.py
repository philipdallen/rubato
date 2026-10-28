"""E2E chain harness — corpus source → IR → roll → container → decode → render.

Each stage is a named function returning StageResult (PASS/FAIL/SKIP);
a failing stage isolates the owning task by name. Decode runs the real P1
(tools/muse_decode) against the written .ru container; render runs the real
P2 (tools/muse_play) on the P1-decoded Work. Both landed 2026-08-24 (#197,
#198); this harness is where their seams (S5→P1, P1→P2) are exercised.

Determinism: pack twice → identical roll bytes; artifacts are compared
as payloads (never zip container bytes, whose timestamps vary).
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field

from muse_ir import load
from muse_roll import decode as roll_decode
from muse_roll import encode as roll_encode
from muse_roll.roll import _canonical

CORPUS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "corpus"))

REGISTRY = [
    ("bach-bwv227.1", "bach/bwv227.1.mxl"),
    ("bach-bwv227.3", "bach/bwv227.3.mxl"),
    ("bach-bwv227.7", "bach/bwv227.7.mxl"),
    ("bach-bwv227.11", "bach/bwv227.11.mxl"),
    ("byrd-1-kyrie", "byrd/1-Kyrie.mid"),
    ("byrd-2-gloria", "byrd/2-Gloria.mid"),
    ("byrd-3-credo", "byrd/3-Credo.mid"),
    ("byrd-4-sanctus", "byrd/4-Sanctu.mid"),
    ("byrd-5-benedictus", "byrd/5-Bened.mid"),
    ("byrd-6-agnus", "byrd/6-Agnus.mid"),
    ("schubert-d810", "schubert/death-and-the-maiden.mxl"),
    ("beethoven-sym5-mov1", "beethoven/beethoven-sym5-mov1.xml"),
    ("beethoven-sym9", "beethoven/beethoven-sym9.xml"),
    ("clinton-st", "allen/clinton-st.musicxml"),
]

# W4 pairwise diff was quadratic and gated above this many notes; as of #317
# the tolerance-0 path is O(n_a + n_b) (B9's 239,459 notes diff in ~1s), so
# there is no longer a compute reason to skip. Kept as a *safety* ceiling well
# above the corpus (largest is 239k) so a pathological input still cannot hang
# the chain — not as a gate on any real work.
DIFF_BUDGET_NOTES = 2_000_000

# P2 render allocates the whole work's PCM buffer: schubert (24,772 notes,
# 28 min) already writes a 151 MB WAV, and B9 is ~65 min of audio. This gate
# is about output size, not algorithm, so it stays — B9's render remains a
# deliberate, separate decision (see #317's out-of-scope note).
RENDER_BUDGET_NOTES = 30000


@dataclass
class StageResult:
    stage: str           # stage name = owning task's noun
    status: str          # PASS | FAIL | SKIP
    detail: str = ""


@dataclass
class ChainResult:
    work_id: str
    relpath: str
    stages: list = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)  # name -> bytes

    @property
    def ok(self):
        return all(s.status != "FAIL" for s in self.stages)


def _stage_parse(work_id, relpath):
    work = load(os.path.join(CORPUS, relpath))
    return work, StageResult("parse(W1)", "PASS",
                             f"{len(work.parts)} parts, {work.note_count} notes")


def _stage_pack(work):
    a = roll_encode(work)
    b = roll_encode(work)
    if a != b:
        return None, StageResult("pack(S2)", "FAIL", "encode not deterministic")
    return a, StageResult("pack(S2)", "PASS", f"{len(a)} bytes, deterministic")


def _stage_container(work_id, relpath, roll_bytes, seed_bytes, out_dir):
    from muse_mu import build_manifest, read_mu, write_mu

    prov = {"source": f"corpus/{relpath}", "author": "muse_chain",
            "ai_involvement": "none",
            "tools": ["tools/ir", "tools/muse_roll", "tools/muse_mu"]}
    lic = {"renditions": "closed",
           "attribution": "chain harness smoke artifact",
           "commercial": False}
    members = {"roll.bin": roll_bytes, "seed.bin": seed_bytes}
    manifest = build_manifest(work_id=work_id, license=lic, provenance=prov,
                              members=members)
    path = os.path.join(out_dir, f"{work_id}.ru")
    write_mu(path, manifest, members)
    back, got = read_mu(path)
    if got != members:
        return None, None, StageResult("container(S5)", "FAIL",
                                       "member round-trip mismatch")
    return path, back.to_json().encode(), StageResult(
        "container(S5)", "PASS", "manifest verified, hashes match")


def _stage_decode(work, container_path):
    """S5→P1 seam: the real P1 decoder reads the written .ru container."""
    from muse_decode import decode as mu_decode

    rt = mu_decode(container_path)
    if _canonical(rt) != _canonical(work):
        return None, StageResult("decode(P1)", "FAIL",
                                 "event stream mismatch after decode")
    return rt, StageResult(
        "decode(P1)", "PASS", "event stream identical (P1 reference decoder)")


def _stage_diff(work, roll_bytes):
    if work.note_count > DIFF_BUDGET_NOTES:
        return StageResult("verify(W4)", "SKIP",
                           f"{work.note_count} notes > {DIFF_BUDGET_NOTES} budget; "
                           f"structural check already PASS")
    from muse_diff import diff

    report = diff(work, roll_decode(roll_bytes))
    if not report.ok():
        return StageResult("verify(W4)", "FAIL",
                           f"recall={report.recall:.4f} precision={report.precision:.4f}")
    return StageResult("verify(W4)", "PASS", "recall=precision=1.0")


def _stage_render(work, out_dir):
    """P1→P2 seam: the real P2 renderer turns the decoded Work into audio."""
    if work.note_count > RENDER_BUDGET_NOTES:
        return StageResult("render(P2)", "SKIP",
                           f"{work.note_count} notes > {RENDER_BUDGET_NOTES} budget")
    from muse_play.play import render_work

    wav = os.path.join(out_dir, "render.wav")
    info = render_work(work, wav)
    with open(wav, "rb") as fh:
        if fh.read(4) != b"RIFF":
            return StageResult("render(P2)", "FAIL", "output is not a WAV")
    size = os.path.getsize(wav)
    if size < 1000 or info["duration_sec"] <= 0:
        return StageResult("render(P2)", "FAIL",
                           f"suspicious render: {size} bytes, {info['duration_sec']}s")
    return StageResult("render(P2)", "PASS",
                       f"{info['notes']} notes → {info['duration_sec']}s WAV "
                       f"({size} bytes)")


def run_work(work_id, relpath, seed_bytes=b"chain-seed-placeholder") -> ChainResult:
    result = ChainResult(work_id=work_id, relpath=relpath)
    try:
        work, s = _stage_parse(work_id, relpath)
    except Exception as e:
        result.stages.append(StageResult("parse(W1)", "FAIL",
                                         f"{type(e).__name__}: {e}"))
        return result
    result.stages.append(s)

    roll_bytes, s = _stage_pack(work)
    result.stages.append(s)
    if roll_bytes is None:
        return result
    result.artifacts["roll.bin"] = roll_bytes

    with tempfile.TemporaryDirectory(prefix="muse-chain-") as out_dir:
        container_path, manifest_json, s = _stage_container(
            work_id, relpath, roll_bytes, seed_bytes, out_dir)
        result.stages.append(s)
        if manifest_json is not None:
            result.artifacts["manifest.json"] = manifest_json
        if container_path is None:
            return result

        decoded, s = _stage_decode(work, container_path)
        result.stages.append(s)
        result.stages.append(_stage_diff(work, roll_bytes))
        if decoded is None:
            return result
        result.stages.append(_stage_render(decoded, out_dir))
    return result


def run_all(registry=REGISTRY):
    return [run_work(wid, rel) for wid, rel in registry]


def check_determinism(registry=REGISTRY):
    """Two full runs → identical artifacts per work; failures listed."""
    first = {r.work_id: r.artifacts for r in run_all(registry)}
    second = {r.work_id: r.artifacts for r in run_all(registry)}
    mismatches = []
    for wid in first:
        for name, blob in first[wid].items():
            if second[wid].get(name) != blob:
                mismatches.append(f"{wid}:{name}")
    return mismatches
