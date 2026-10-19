"""Tests: muse_audio render bridge (issue #243).

Spec: tests/closed_20260824-233000_workbench-audio.md.
"""

import json
import os
import wave

import pytest

from muse_audio import AUDIO_DIR, render_revision, write_manifest
from muse_audio.audio import MANIFEST_NAME, _schema_dict_to_mockup

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WORK = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")
SEED_V1 = os.path.join(REPO, "seeds", "bwv227.1.v1.seed.yaml")
SEED_V2 = os.path.join(REPO, "seeds", "bwv227.1.v2.seed.yaml")


class TestStandInRender:
    def test_wav_written_and_valid(self, tmp_path):
        r = render_revision(WORK, SEED_V1, "v1", out_dir=str(tmp_path))
        path = tmp_path / r.wav
        assert r.wav == "bwv227.1.v1.wav"
        with wave.open(str(path)) as wf:
            assert wf.getframerate() == 44100
            assert wf.getnframes() / wf.getframerate() == pytest.approx(
                r.duration_sec, abs=0.01)
        assert r.notes == 279
        assert r.origin == "stand-in"

    def test_duration_plausible_for_work(self, tmp_path):
        # ppq=2 chorale: ~76 quarters; at the seed's 62..129 arch → 30..80s,
        # never the 0.69s of the ppq=480 bug (#246 regression)
        r = render_revision(WORK, SEED_V1, "v1", out_dir=str(tmp_path))
        assert 30.0 < r.duration_sec < 80.0

    def test_seed_revision_is_audible(self, tmp_path):
        # v1 (62..129 arch) and v2 (80..120 arch) must differ
        a = render_revision(WORK, SEED_V1, "v1", out_dir=str(tmp_path))
        b = render_revision(WORK, SEED_V2, "v2", out_dir=str(tmp_path))
        assert a.sha256 != b.sha256
        assert a.duration_sec != b.duration_sec

    def test_deterministic(self, tmp_path):
        a = render_revision(WORK, SEED_V1, "v1", out_dir=str(tmp_path / "a"))
        b = render_revision(WORK, SEED_V1, "v1", out_dir=str(tmp_path / "b"))
        assert a.sha256 == b.sha256


class TestManifest:
    def test_manifest_shape_and_paths(self, tmp_path):
        r = render_revision(WORK, SEED_V2, "v2", out_dir=str(tmp_path))
        path = write_manifest([r], out_dir=str(tmp_path))
        doc = json.loads(open(path).read())
        assert doc["format"] == "muse-audio-manifest-v1"
        entry = doc["works"]["bwv227.1"]["v2"]
        assert entry["file"] == "bwv227.1.v2.wav"
        assert entry["origin"] == "stand-in"
        assert int(entry["sha256"], 16)
        assert not os.path.isabs(entry["file"])

    def test_labels_accumulate(self, tmp_path):
        a = render_revision(WORK, SEED_V1, "v1", out_dir=str(tmp_path))
        b = render_revision(WORK, SEED_V2, "v2", out_dir=str(tmp_path))
        path = write_manifest([a, b], out_dir=str(tmp_path))
        doc = json.loads(open(path).read())
        assert set(doc["works"]["bwv227.1"]) == {"v1", "v2"}


class TestSchemaDictConversion:
    """The live path's wire format (schema v1, indexed) → Mockup model."""

    def _work(self):
        from muse_ir import load
        return load(WORK)

    def test_resolves_notes_from_score(self):
        work = self._work()
        d = {
            "work_id": "bwv227.1",
            "tempo_map": [{"tick": 0, "bpm": 96.0}],
            "parts": {"P1": [{"i": 0, "velocity": 90,
                              "attack_sec": 0.04, "onset_offset_ms": -3}]},
        }
        m = _schema_dict_to_mockup(d, work)
        assert len(m.notes) == 1
        n = m.notes[0]
        ref = work.parts[0].notes[0]
        assert (n.pitch, n.onset, n.duration) == (ref.pitch, ref.onset, ref.duration)
        assert n.velocity == 90
        assert n.attack_ms == 40.0
        assert n.onset_offset_ms == -3
        assert m.tempo_map == [(0, 96000)]

    def test_ppq_carried_from_work(self):
        """The schema wire format has no ppq field; the bridge must set it
        from the work, or every real-work render plays at the wrong speed
        (bwv227.1 is ppq=2 — 240x too fast at the 480 default, #246 seam)."""
        work = self._work()
        d = {"work_id": "bwv227.1", "tempo_map": [{"tick": 0, "bpm": 96.0}],
             "parts": {"P1": [{"i": 0, "velocity": 90}]}}
        m = _schema_dict_to_mockup(d, work)
        assert m.ppq == work.meta.ppq == 2

    def test_balance_and_dynamics_carried(self):
        work = self._work()
        d = {
            "work_id": "bwv227.1",
            "tempo_map": [{"tick": 0, "bpm": 96.0}],
            "dynamics": [{"tick": 0, "level": 0.7}],
            "balance": [{"part": "P1", "gain": 1.0}, {"part": "P2", "gain": 0.9}],
            "parts": {"P1": [{"i": 0, "velocity": 80}]},
        }
        m = _schema_dict_to_mockup(d, work)
        assert m.part_map["P2"]["gain"] == 0.9
        assert m.curves["dynamics"] == [(0, 0.7)]

    def test_unknown_part_skipped(self):
        work = self._work()
        d = {"work_id": "x", "tempo_map": [{"tick": 0, "bpm": 96.0}],
             "parts": {"P99": [{"i": 0, "velocity": 64}]}}
        m = _schema_dict_to_mockup(d, work)
        assert m.notes == []


class TestLivePathWiring:
    def test_live_runs_generate_loop_with_provider(self, tmp_path):
        """RecordedProvider fixture — no network; proves live=True routes
        through muse_generate and stamps provenance/origin."""
        from muse_provider import RecordedProvider
        from muse_ir import load
        work = load(WORK)
        parts = {
            p.id: [{"i": j, "velocity": 64}
                   for j, n in enumerate(p.notes)
                   if n.pitch is not None and "unpitched" not in n.notations]
            for p in work.parts
        }
        fixture = {"work_id": "bwv227.1", "tempo_map": [{"tick": 0, "bpm": 96.0}],
                   "parts": parts, "seed": {"note": "test"}}
        from muse_generate import assemble_prompt
        from muse_seed import load_seed
        seed = load_seed(open(SEED_V2).read())
        provider = RecordedProvider(
            {str(hash(assemble_prompt(seed, work))): fixture})
        r = render_revision(WORK, SEED_V2, "llm-v2", out_dir=str(tmp_path),
                            live=True, provider=provider)
        assert r.origin == "llm-live"
        assert r.notes == 279
        assert 30.0 < r.duration_sec < 80.0
