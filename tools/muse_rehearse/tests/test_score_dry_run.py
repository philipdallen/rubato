"""score-dry-run: the candidate's probes, written out nowhere.

The plain dry run shows only the param diff — which knobs turned. The
score-dry-run answers the next question (the conductor's question): what
did the directive do to the seed's score — budget fit, assertions,
coverage, the gate — before anything is committed.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

from muse_rehearse import cli  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SEED = os.path.join(REPO, "seeds", "bwv227.1.seed.yaml")


def _seed_tree_state():
    state = {}
    for root, _dirs, files in os.walk(os.path.join(REPO, "seeds")):
        for f in files:
            p = os.path.join(root, f)
            state[p] = os.path.getmtime(p)
    return state


def test_score_dry_run_reports_base_and_candidate(capsys):
    rc = cli.main(["score-dry-run", SEED, "phrase: quieter at bar 8"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["changed"] == ["variation_points"]
    # The base has no variation points; the compiled phrase adds one that
    # lands on notes — coverage is the score that moves.
    assert out["base"]["coverage"]["variation_points"] == 0
    assert out["candidate"]["coverage"]["variation_points"] == 1
    assert out["candidate"]["coverage"]["exercised"] == 1
    for view in (out["base"], out["candidate"]):
        for probe in ("budget_fit", "assertions", "coverage",
                      "fidelity_guard", "determinism"):
            assert probe in view, f"score view missing {probe}"
    # delta_curves is work-fixed, reported once as context
    assert "parts" in out["delta_curves"]


def test_score_dry_run_writes_nothing(capsys):
    before = _seed_tree_state()
    rc = cli.main(["score-dry-run", SEED, "rebalance: bring P4 up at bar 5"])
    assert rc == 0
    capsys.readouterr()
    assert _seed_tree_state() == before


def test_score_dry_run_grammar_error_is_exit_1(capsys):
    rc = cli.main(["score-dry-run", SEED, "wobble: sideways"])
    assert rc == 1



def test_render_dry_run_writes_content_addressed_wav(tmp_path, capsys):
    import wave
    rc = cli.main(["render-dry-run", SEED,
                   "rebalance: bring P4 up at bar 5",
                   "--out-dir", str(tmp_path)])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["changed"] == ["params"]
    wav_path = tmp_path / os.path.basename(out["wav"])
    assert wav_path.is_file()
    with wave.open(str(wav_path)) as wf:
        assert wf.getframerate() == 44100
        assert wf.getnframes() > 0
    assert out["duration_sec"] > 30.0
    assert out["notes"] == 279


def test_render_dry_run_is_deterministic(tmp_path, capsys):
    rc = cli.main(["render-dry-run", SEED, "rubato: more",
                   "--out-dir", str(tmp_path)])
    assert rc == 0
    a = json.loads(capsys.readouterr().out)
    rc = cli.main(["render-dry-run", SEED, "rubato: more",
                   "--out-dir", str(tmp_path)])
    assert rc == 0
    b = json.loads(capsys.readouterr().out)
    assert a["wav"] == b["wav"]
    assert a["sha256"] == b["sha256"]
