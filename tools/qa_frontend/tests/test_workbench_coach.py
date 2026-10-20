"""Coaching sessions page (docs/workbench/coach.html).

The dedicated rehearsal surface: pick a work + seed revision, type a
directive, and see the score — candidate vs base across the seed-sensitive
probes — before committing. Dry run shows the param diff; Score shows the
probe comparison; only Commit persists. Session attempts log in the page
(export as JSON); nothing about the session is committed to the repo.

Two tiers, mirroring test_workbench_rehearse_pane:
  * source-scan — the affordances, the score wiring, no mockup JSON;
  * DOM (Playwright) — the page mounts, the pickers populate, the
    offline-safe affordances (empty-directive guards, discard, export)
    work without the runner.
"""

import os
import re

import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PAGE = os.path.join(REPO, "docs", "workbench", "coach.html")
DOCS = os.path.join(REPO, "docs")


def _html():
    with open(PAGE) as fh:
        return fh.read()


# --- Source-scan tier ---

def test_coach_has_directive_affordances():
    src = _html()
    assert "<textarea" in src, "coach page must accept a directive"
    for label in ("Dry run", "Score", "Commit", "Discard"):
        assert label in src, f"missing [{label}] affordance"


def test_coach_has_session_log_and_export():
    src = _html()
    assert "Session log" in src, "coach page must carry a session log"
    assert "Export session JSON" in src, "session must be exportable"


def test_coach_has_work_and_seed_pickers():
    src = _html()
    assert 'id="work-select"' in src, "coach page must pick a work"
    assert 'id="seed-select"' in src, "coach page must pick a seed revision"
    assert 'id="era-select"' in src, "coach page must pick the era budget"


def test_coach_wires_score_command():
    src = _html()
    assert "muse_rehearse.score-dry-run" in src, "score not wired to the runner"
    assert "muse_rehearse.dry-run" in src, "dry-run not wired to the runner"
    assert "muse_rehearse.commit" in src, "commit not wired to the runner"
    assert "api/run" in src, "page must POST against the runner"


def test_coach_embeds_no_mockup_json():
    # D20: the page may name the probe fields (mockup_ioi_mean) and explain
    # the delta table, but it must never fetch or embed mockup note data.
    src = _html()
    assert ".mockup.json" not in src, "coach page must not load mockup JSON"
    assert "mockup_notes" not in src, "coach page must not embed mockup notes"


def test_coach_carries_shared_nav():
    m = re.search(r'<nav class="site-nav".*?</nav>', _html(), re.S)
    assert m, "coach page carries no .site-nav"
    assert "/workbench/coach.html" in m.group(0), "nav must link the coach page"


# --- DOM tier ---

@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def session():
    with PageSession() as ps:
        yield ps


def test_coach_mounts_clean(server, session):
    page = session.new_page()
    page.goto(server.url + "/workbench/coach.html", wait_until="networkidle")
    assert page.locator("h1").inner_text() == "Coaching sessions"
    assert page.locator("#directive-input").count() == 1
    assert page.locator("#score-btn").count() == 1
    assert page.locator("#session-log").count() == 1
    assert not session.console_errors, session.console_errors


def test_coach_pickers_populate(server, session):
    page = session.new_page()
    page.goto(server.url + "/workbench/coach.html", wait_until="networkidle")
    works = page.locator("#work-select option")
    assert works.count() > 0, "work picker is empty"
    seeds = page.locator("#seed-select option")
    assert seeds.count() > 0, "seed revision picker is empty"


def test_empty_score_guards_without_network(server, session):
    """An empty directive is rejected client-side — no runner call needed."""
    page = session.new_page()
    posts = []
    page.on("request", lambda r: posts.append(r.url) if r.method == "POST" else None)
    page.goto(server.url + "/workbench/coach.html", wait_until="networkidle")
    page.locator("#score-btn").click()
    assert "enter a directive first" in page.locator("#coach-status").inner_text()
    assert not posts, f"empty score issued a request: {posts}"


def test_discard_clears_without_network(server, session):
    page = session.new_page()
    posts = []
    page.on("request", lambda r: posts.append(r.url) if r.method == "POST" else None)
    page.goto(server.url + "/workbench/coach.html", wait_until="networkidle")
    page.locator("#directive-input").fill("phrase: quieter at bar 8")
    page.locator("#discard-btn").click()
    assert page.locator("#directive-input").input_value() == ""
    assert "discarded" in page.locator("#coach-status").inner_text().lower()
    assert not posts, f"discard issued a request: {posts}"
