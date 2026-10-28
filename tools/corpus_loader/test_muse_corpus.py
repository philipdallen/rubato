"""W2 loader tests: registry coverage, check gate, CLI contract."""

import io
import os
import subprocess
import sys
import time

import pytest

MODULE = os.path.join(os.path.dirname(__file__), "muse_corpus.py")
sys.path.insert(0, os.path.dirname(__file__))

import muse_corpus as mc  # noqa: E402

BYRD_FILES = [f for wid, t, f, pins in mc.iter_files() if wid == "byrd-mass3v"]


class TestRegistry:
    def test_registry_covers_every_corpus_file(self):
        on_disk = set()
        for genre_dir in os.listdir(mc.CORPUS_ROOT):
            full = os.path.join(mc.CORPUS_ROOT, genre_dir)
            if not os.path.isdir(full):
                continue
            for f in os.listdir(full):
                if os.path.splitext(f)[1].lower() in (
                    ".xml", ".musicxml", ".mxl", ".mid", ".midi"
                ):
                    on_disk.add(os.path.join(genre_dir, f))
        registered = {relpath for _, _, relpath, _ in mc.iter_files()}
        assert on_disk == registered, f"registry/corpus mismatch: {on_disk ^ registered}"

    def test_every_work_has_title_and_files(self):
        for work_id, entry in mc.WORKS.items():
            assert entry["title"], work_id
            assert entry["files"], work_id
            for relpath, pins in entry["files"]:
                assert set(pins) == {"parts", "notes", "dynamics", "hairpins"}, relpath


class TestCheck:
    def test_check_file_passes_every_file(self):
        for _work_id, _title, relpath, pins in mc.iter_files():
            got = mc.check_file(relpath, pins)
            assert got["parts"] == pins["parts"]

    def test_check_file_rejects_pin_drift(self):
        with pytest.raises(mc.CheckFailure, match=r"notes \d+ != 999999"):
            mc.check_file("bach/bwv227.1.mxl",
                          {"parts": 4, "notes": 999999, "dynamics": 0, "hairpins": 0})

    def test_check_file_rejects_missing_file(self):
        with pytest.raises(mc.CheckFailure, match="file missing"):
            mc.check_file("bach/nope.mxl",
                          {"parts": 0, "notes": 0, "dynamics": 0, "hairpins": 0})

    def test_run_check_failure_path_on_fixture_root(self, tmp_path):
        """A fixture corpus root with a corrupted file must fail the gate."""
        bad_dir = tmp_path / "byrd"
        bad_dir.mkdir()
        (bad_dir / "1-Kyrie.mid").write_bytes(b"corrupted midi bytes")
        out = io.StringIO()
        n, failures = mc.run_check(root=str(tmp_path), out=out)
        assert n == len(list(mc.iter_files()))
        assert failures and any("1-Kyrie.mid" in f and "parse failed" in f for f in failures)

    def test_run_check_reports_missing_not_parse(self, tmp_path):
        out = io.StringIO()
        n, failures = mc.run_check(root=str(tmp_path), out=out)
        assert failures and all("file missing" in f for f in failures[:2])


class TestBudget:
    def test_byrd_files_parse_within_budget(self):
        """Wall-clock guard: the six Byrd MIDIs parse far under a minute.
        Full-corpus check budget (~21s incl. B9) is pinned in the README."""
        t0 = time.monotonic()
        for f in BYRD_FILES:
            mc.load_file(f)
        assert time.monotonic() - t0 < 30


class TestWarningsContract:
    def test_surfaces_known_parser_warnings(self, capsys):
        rc = mc.main(["load", "schubert-d810"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "conflicting tempo" in out  # Schubert's known warning must surface


class TestCLI:
    def run_cli(self, *argv):
        return subprocess.run(
            [sys.executable, MODULE, *argv],
            capture_output=True, text=True, timeout=600,
        )

    def test_list_lists_all_five_works(self):
        r = self.run_cli("list")
        assert r.returncode == 0
        for wid in ("bach-bwv227", "byrd-mass3v", "schubert-d810",
                    "beethoven-sym5-mov1", "beethoven-sym9"):
            assert wid in r.stdout

    def test_load_reports_work_summary(self):
        r = self.run_cli("load", "bach-bwv227")
        assert r.returncode == 0
        assert "parts=4" in r.stdout and "notes=279" in r.stdout
        assert "source_format=musicxml" in r.stdout

    def test_load_midi_marks_inference_risk(self):
        r = self.run_cli("load", "byrd-mass3v")
        assert r.returncode == 0
        assert "MIDI source" in r.stdout

    def test_load_unknown_work_fails(self):
        r = self.run_cli("load", "no-such-work")
        assert r.returncode == 1
        assert "unknown work" in r.stderr

    def test_check_gate_green(self):
        r = self.run_cli("check")
        assert r.returncode == 0
        assert r.stdout.count("OK ") == len(list(mc.iter_files()))

    def test_update_pins_reports_current(self, capsys):
        rc = mc.main(["update-pins"])
        assert rc == 0
        assert "current" in capsys.readouterr().out

    def test_update_pins_prints_drift_when_present(self, monkeypatch, capsys):
        # Temptation: mutate a registry pin and watch the report catch it.
        entry = mc.WORKS["bach-bwv227"]
        monkeypatch.setitem(entry["files"][0][1], "notes", 999999)
        rc = mc.main(["update-pins"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "bwv227.1.mxl" in out
        assert "notes: 999999 -> 279" in out
