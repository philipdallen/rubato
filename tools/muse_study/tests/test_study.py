"""R3 study-script + survival-feedback tests (spec: tests/open_*_r3-study.md)."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "ir"))

from muse_ir import load as load_work  # noqa: E402
from muse_seed import load_seed  # noqa: E402
from muse_study import SCRIPTS, run_script, check_survival  # noqa: E402
from muse_study.study import Step, _seed_survival  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
WORK_PATH = os.path.join(REPO, "corpus", "bach", "bwv227.1.mxl")
SEED_PATH = os.path.join(REPO, "seeds", "bwv227.1.v2.seed.yaml")
# recorded fixture + its matching seed (muse_generate integration fixture #209)
GEN_SEED = os.path.join(REPO, "seeds", "bwv227.1.seed.yaml")
RECORDED = os.path.join(REPO, "tests", "fixtures", "bwv227.1.recorded-mockup.json")


@pytest.fixture(scope="module")
def work():
    return load_work(WORK_PATH)


@pytest.fixture(scope="module")
def base_seed():
    return load_seed(open(SEED_PATH).read(), fmt="yaml")


def test_scripts_have_steps_and_issues():
    for name, s in SCRIPTS.items():
        assert s.steps, f"{name}: no steps"
        assert s.issue, f"{name}: no issue text"
        for step in s.steps:
            verb = step.directive.split(":")[0].split()[0]
            assert verb in ("rebalance", "phrase", "tempo_arch", "rubato", "hold"), \
                f"{name}: step uses non-grammar verb {verb}"


def test_run_script_reports_per_step(base_seed, work):
    _, reports = run_script(SCRIPTS["quiet-the-bass"], SEED_PATH, work=work)
    assert len(reports) == len(SCRIPTS["quiet-the-bass"].steps)
    assert all(r.verb == "rebalance" for r in reports)
    assert all(r.verdict in ("moved", "flat", "drifted", "unmeasurable")
               for r in reports)


def test_survival_rebalance_moves_part_gains(base_seed):
    step = Step("rebalance: bring P4 down")
    from muse_rehearse import parse_directive, compile_directive
    d = parse_directive(step.directive, seed=base_seed)
    cand = compile_directive(d, base_seed)
    rep = check_survival(step, base_seed, cand, None, None)
    assert rep.verdict == "moved"
    assert rep.candidate_value["P4"] < 1.0  # down reduces gain


def test_survival_direction_sign(base_seed):
    """A 'down' directive must lower the gain, not raise it (regression:
    direction word order made 'bring … down' parse as up)."""
    from muse_rehearse import parse_directive, compile_directive
    d = parse_directive("rebalance: bring P4 down", seed=base_seed)
    cand = compile_directive(d, base_seed)
    assert cand.params["part_gains"]["P4"] < 1.0


def test_seed_survival_phrase_counts_variation_points(base_seed):
    from muse_rehearse import parse_directive, compile_directive
    d = parse_directive("phrase: quieter into development", seed=base_seed)
    cand = compile_directive(d, base_seed)
    b, c, verdict = _seed_survival("phrase", base_seed, cand)
    assert verdict == "moved" and c == b + 1


def test_hold_survival_adds_tempo_bounds(base_seed):
    from muse_rehearse import parse_directive, compile_directive
    d = parse_directive("hold: ticks 0-480", seed=base_seed)
    cand = compile_directive(d, base_seed)
    _, has, verdict = _seed_survival("hold", base_seed, cand)
    assert verdict == "moved" and has is True


def test_flat_when_nothing_changes(base_seed):
    b, c, verdict = _seed_survival("rebalance", base_seed, base_seed)
    assert verdict == "flat"


# --- render lane (RR2 #381): the mockup-level survival verdict -----------------


def _mockup_from_seed(work, seed):
    """A minimal Mockup whose per-part note counts (and so distilled
    part_gains) track the seed's part_gains — the seed-dependence the real
    L1 loop supplies, so the render lane has something to move on."""
    from muse_mockup import Mockup, Note

    gains = seed.params.get("part_gains", {}) if seed is not None else {}
    m = Mockup(work_id="bwv227.1")
    for part in ("P1", "P2", "P3", "P4"):
        count = int(gains.get(part, 1.0) * 10)
        for i in range(count):
            m.notes.append(Note(pitch=60, onset=i, duration=1, velocity=90,
                                part=part))
    return m


def test_render_lane_stand_in_blocked_without_live(base_seed, work):
    """Offline stand-in cannot move the mockup, so the render lane must say
    "stand-in-blocked" rather than a misleading `flat`."""
    _, reports = run_script(SCRIPTS["quiet-the-bass"], SEED_PATH, work=work)
    assert all(r.render_verdict == "stand-in-blocked" for r in reports)
    assert all(r.render_base is None for r in reports)


def test_render_lane_moved_with_live_mockup_fn(base_seed, work):
    _, reports = run_script(SCRIPTS["quiet-the-bass"], SEED_PATH, work=work,
                            mockup_fn=_mockup_from_seed)
    # rebalance lowers P4's gain → distilled part_gains differ → render moved
    assert all(r.render_verdict == "moved" for r in reports)
    assert all(r.render_base is not None for r in reports)


def test_render_lane_flat_when_mockup_unchanged(base_seed, work):
    def _constant(work, seed):
        from muse_mockup import Mockup, Note

        m = Mockup(work_id="bwv227.1")
        m.notes.append(Note(pitch=60, onset=0, duration=1, velocity=90, part="P1"))
        return m

    _, reports = run_script(SCRIPTS["quiet-the-bass"], SEED_PATH, work=work,
                            mockup_fn=_constant)
    assert all(r.render_verdict == "flat" for r in reports)


def test_live_path_runs_offline_with_recorded_provider(work, monkeypatch):
    """The live generate loop (MUSE_L1_LIVE) runs offline behind a
    RecordedProvider fixture, mirroring the muse_generate suite."""
    import json

    from muse_generate.generate import assemble_prompt
    from muse_provider import RecordedProvider
    from muse_rehearse import parse_directive, compile_directive
    from muse_seed import load_seed

    base = load_seed(open(SEED_PATH).read(), fmt="yaml")
    mockup = json.load(open(RECORDED))
    # record a response for the base seed and every compiled candidate
    responses = {}
    candidate = base
    responses[str(hash(assemble_prompt(candidate, work)))] = mockup
    for step in SCRIPTS["quiet-the-bass"].steps:
        d = parse_directive(step.directive, seed=base, work=work)
        candidate = compile_directive(d, candidate, "baroque", work)
        responses[str(hash(assemble_prompt(candidate, work)))] = mockup

    monkeypatch.setenv("MUSE_L1_LIVE", "1")
    provider = RecordedProvider(responses)
    _, reports = run_script(SCRIPTS["quiet-the-bass"], SEED_PATH, work=work,
                            provider=provider)
    # the recorded fixture realizes every directive → render lane ran live
    assert all(r.render_verdict in ("moved", "flat") for r in reports)
