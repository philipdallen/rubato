"""Coaching console QA — the workbench Rehearse pane and audio surface.

This suite answers "what works and what needs to change" for the surface a
conductor actually uses. It is deliberately split by outcome:

- **passing** tests pin behaviour that works today (read the committed
  rehearsal log, the audio manifest, the players);
- **xfail** tests pin behaviour that is specified but not built. They stay
  green in CI while the gap is open and flip to XPASS the moment it lands,
  which is the signal to delete the xfail. Each carries its issue number.

So: run the suite, read the xfails — that list *is* the to-change list.

Gaps pinned here:
- #388 — the Rehearse pane is read-only (no directive input, no dry-run /
  commit controls) and `muse_rehearse` is not in the runner allowlist.
- #389 — the per-work Growth card is rendered once per revision.

Browser tier (slow): needs Playwright + Chromium, same as the other
`qa_frontend` DOM tests. Source-scan assertions run without a browser.
"""

import json
import os
import sys
import urllib.request

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")
PAGE = os.path.join(DOCS, "workbench", "detail.html")
RUNNER_CFG = os.path.join(REPO, "workbench.config.json")
RUNNER_PY = os.path.join(REPO, "tools", "muse_workbench_runner", "runner.py")


@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def session():
    with PageSession() as ps:
        yield ps


def _goto(server, session):
    page = session.new_page()
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    return page


# --- The Rehearse pane: the read surface that works today -----------------

def test_rehearse_card_present(server, session):
    page = _goto(server, session)
    assert page.locator(".card.rehearsal").count() >= 1, "Rehearse card missing"


def test_rehearse_shows_committed_directive(server, session):
    """The committed rehearsal log is visible: slug, directive text, lineage."""
    page = _goto(server, session)
    card = page.locator(".card.rehearsal").first
    text = card.inner_text()
    assert "quieter-bar-8" in text, "committed directive slug not shown"
    assert "phrase: quieter at bar 8" in text, "directive text not shown"
    assert "verified" in text, "lineage verdict not shown"


def test_rehearse_names_the_cli_path(server, session):
    """The pane documents how to drive the loop while it has no controls."""
    page = _goto(server, session)
    text = page.locator(".card.rehearsal").first.inner_text()
    assert "muse_rehearse/cli.py" in text, "pane does not name the CLI path"
    assert "dry-run" in text and "commit" in text


def test_rehearse_cli_path_exists_on_disk():
    """The path the pane advertises is real — a doc pointing at nothing is a lie."""
    assert os.path.exists(os.path.join(REPO, "tools", "muse_rehearse", "cli.py"))


def test_rehearse_fallback_without_artifact(server, session):
    """A missing directives.json must not blank the console silently.

    Note the current behaviour (pinned by the existing probes-fallback test's
    `or "load error"` clause): a failed fetch aborts the whole `renderAll`
    loop, so the page shows a global `load error: TypeError: Failed to fetch`
    and no revision rows — the per-card "no directives committed yet" note is
    only reachable when the fetch succeeds but the file is empty. Both are a
    visible signal, which is the property that matters here.
    """
    page = session.new_page()
    page.route("**/*.directives.json", lambda route: route.abort())
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    text = page.locator("body").inner_text().lower()
    assert "no directives committed yet" in text or "load error" in text, (
        "missing directives artifact produced neither the empty-state note "
        "nor a visible error — the failure is silent"
    )


@pytest.mark.xfail(reason="one failed artifact fetch blanks the whole console", strict=False)
def test_missing_artifact_degrades_gracefully(server, session):
    """A single missing per-work artifact should blank only its own card, not
    the whole console.

    Today `renderAll` awaits every fetch with no per-call try/catch, so one
    aborted request throws and the loop stops: zero `details.wb-rev` rows
    render and the page shows a global `load error`. This flips when the
    render loop is hardened (per-artifact guard, card-level fallback).
    """
    page = session.new_page()
    page.route("**/*.directives.json", lambda route: route.abort())
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    assert page.locator("details.wb-rev").count() >= 1, "console blanked"


def test_rehearse_card_carries_no_mockup_json(server, session):
    """D20: the pane shows directive history, never a raw mockup payload."""
    page = _goto(server, session)
    text = page.locator(".card.rehearsal").first.inner_text()
    assert "{" not in text, "rehearsal pane leaked a JSON payload"
    assert "mockup" not in text.lower()


# --- Rehearse pane: specified but not built (xfail flips when it lands) ----

@pytest.mark.xfail(reason="#388: Rehearse pane has no directive input yet", strict=False)
def test_rehearse_has_directive_input(server, session):
    """R2 spec (tests/closed_20260826-110000_r2-rehearsal-pane.md §Coverage 6):
    the pane contains a directive textarea."""
    page = _goto(server, session)
    assert page.locator(".card.rehearsal textarea").count() >= 1


@pytest.mark.xfail(reason="#388: no dry-run / commit / discard affordances yet", strict=False)
def test_rehearse_has_dryrun_and_commit_controls(server, session):
    """R1 §W-B pane layouts: directive textarea → [Dry run] → preview →
    [Commit] / [Discard]."""
    page = _goto(server, session)
    text = page.locator(".card.rehearsal").first.inner_text().lower()
    for control in ("dry run", "commit", "discard"):
        assert control in text, f"missing control: {control}"


@pytest.mark.xfail(reason="#388: muse_rehearse not in the runner allowlist", strict=False)
def test_rehearse_commands_allowlisted():
    """A pane action needs an allow-listed runner command to call."""
    cfg = json.load(open(RUNNER_CFG))
    assert any(c.startswith("muse_rehearse.") for c in cfg["allowlist"]), cfg["allowlist"]


@pytest.mark.xfail(reason="#389: per-work growth card repeats per revision", strict=False)
def test_growth_card_rendered_once_per_work(server, session):
    """The growth compare is per-work data; it should not repeat per revision."""
    page = _goto(server, session)
    assert page.locator(".card", has_text="Growth").count() == 1


# --- Console data + audio surface (what the page actually serves) ---------

def test_audio_manifest_reachable(server):
    """The page fetches /audio/manifest.json; it must be valid JSON."""
    with urllib.request.urlopen(server.url + "/audio/manifest.json") as r:
        data = json.load(r)
    assert data.get("works"), "audio manifest has no works"


def test_audio_players_point_at_audio_dir(server, session):
    """Every rendered <audio> resolves to an /audio/ source."""
    page = _goto(server, session)
    players = page.locator("audio")
    assert players.count() >= 3, f"expected per-revision players, got {players.count()}"
    for i in range(players.count()):
        src = players.nth(i).get_attribute("src") or ""
        assert src.startswith("/audio/"), f"player {i} src not under /audio/: {src}"


def test_revision_audio_meta_rendered(server, session):
    """Each player row shows origin + duration + note count (the ear loop)."""
    page = _goto(server, session)
    text = page.locator(".card", has_text="Audio — seed revisions").first.inner_text()
    assert "llm-live" in text or "stand-in" in text, "origin tag missing"
    assert "notes" in text and "s" in text, "duration/notes meta missing"


# --- Coaching status surfaced for a reader --------------------------------

def test_probe_verdicts_are_visible(server, session):
    """The reader can see pass/stable/clean without opening devtools."""
    page = _goto(server, session)
    text = page.locator("body").inner_text().lower()
    for verdict in ("pass", "stable", "clean"):
        assert verdict in text, f"probe verdict '{verdict}' not surfaced"
