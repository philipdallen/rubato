"""Rehearse pane is interactive (issue #394; spec tests/closed_*_r2-rehearsal-pane).

R2 items 6-7: the Study/Rehearse pane in ``docs/workbench/detail.html`` is a
full-row card split internally (half-width halves in the two-column
``.rehearsal-split`` grid), contains the directive textarea + dry-run +
commit/discard affordances, and carries no mockup JSON (D20). Only Commit
persists — dry run and discard write nothing.

Two tiers:
  * source-scan — the pane function body has the affordances and the
    runner wiring, and no mockup JSON;
  * DOM (Playwright) — the pane mounts per revision and the offline-safe
    affordances (empty dry-run guard, discard) work without the runner;
  * live runner round-trip — the end-to-end path the offline tests cannot
    reach: a real `server.py --docs` origin, a directive dry run, and the
    compiled param diff rendered into the preview.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PAGE = os.path.join(REPO, "docs", "workbench", "detail.html")
DOCS = os.path.join(REPO, "docs")


def _html():
    with open(PAGE) as fh:
        return fh.read()


def _function_body(src, name):
    """The text from ``function <name>`` up to the next top-level function."""
    start = src.index(f"function {name}")
    rest = src[start + len(f"function {name}"):]
    nxt = re.search(r"\n(?:async )?function ", rest)
    return rest[: nxt.start()] if nxt else rest


def test_pane_has_textarea_and_affordances():
    body = _function_body(_html(), "rehearsalPanel")
    assert "<textarea" in body, "Rehearse pane must accept a directive"
    assert "Dry run" in body, "missing [Dry run] affordance"
    assert "Commit" in body, "missing [Commit] affordance"
    assert "Discard" in body, "missing [Discard] affordance"


def test_pane_is_half_width_split():
    src = _html()
    # The pane card is split internally into the Study (left) and Rehearse
    # (right) halves — a two-column grid, per R1 sec.W-B pane layouts.
    m = re.search(r"\.rehearsal-split\s*\{[^}]*grid-template-columns:\s*1fr 1fr", src)
    assert m, "Rehearse pane must split into two equal halves"
    assert "rehearsal-split" in _function_body(src, "rehearsalPanel")


def test_pane_embeds_no_mockup_json():
    body = _function_body(_html(), "rehearsalPanel")
    assert "mockup" not in body.lower(), (
        "Rehearse pane must not embed mockup JSON (D20)"
    )


def test_pane_wires_runner_commands():
    src = _html()
    assert "muse_rehearse.dry-run" in src, "dry-run not wired to the runner"
    assert "muse_rehearse.commit" in src, "commit not wired to the runner"
    assert "api/run" in src, "pane must POST against the runner"


@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def session():
    with PageSession() as ps:
        yield ps


def test_pane_mounts_per_revision(server, session):
    page = session.new_page()
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    panes = page.locator(".card.rehearsal")
    assert panes.count() > 0, "no Rehearse pane rendered"
    first = panes.first
    assert first.locator("textarea").count() == 1
    assert first.locator("button", has_text="Dry run").count() == 1
    assert first.locator("button", has_text="Commit").count() == 1
    assert first.locator("button", has_text="Discard").count() == 1
    assert not session.console_errors, session.console_errors


def test_discard_writes_nothing_and_clears(server, session):
    """Discard must clear the input and preview and touch no network."""
    page = session.new_page()
    posts = []
    page.on("request", lambda r: posts.append(r.url) if r.method == "POST" else None)
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    first = page.locator(".card.rehearsal").first
    first.locator("textarea").fill("phrase: quieter at bar 8")
    first.locator("button", has_text="Discard").click()
    assert first.locator("textarea").input_value() == ""
    assert "discarded" in first.locator(".rehearse-status").inner_text().lower()
    assert not posts, f"discard issued a request: {posts}"


def test_empty_dry_run_guards_without_network(server, session):
    """An empty directive is rejected client-side — no runner call needed."""
    page = session.new_page()
    posts = []
    page.on("request", lambda r: posts.append(r.url) if r.method == "POST" else None)
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    first = page.locator(".card.rehearsal").first
    first.locator("button", has_text="Dry run").click()
    assert "enter a directive" in first.locator(".rehearse-status").inner_text().lower()
    assert not posts, f"empty dry-run issued a request: {posts}"


# --- Live runner round-trip (the one path the offline tests can't reach) ----

@pytest.fixture(scope="module")
def runner_origin():
    """Serve docs/ AND /api from one origin, like `server.py --docs`.

    This is the pane's real wiring path: it POSTs to an origin-relative
    /api/run, so the runner must share the page's origin.
    """
    import threading

    from muse_workbench_runner.server import serve

    srv, url = serve(0, None, DOCS, ())
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield url
    srv.shutdown()
    srv.server_close()
    t.join(timeout=2)


def test_pane_dry_run_round_trip(runner_origin, session):
    """Against the real runner: a directive dry run previews the compiled
    param diff and writes nothing (R2 item 7). The offline tests cover the
    guards; this covers the round-trip they cannot reach."""
    page = session.new_page()
    page.goto(runner_origin + "/workbench/detail.html", wait_until="networkidle")
    pane = page.locator(".card.rehearsal .rehearse").first
    pane.locator(".rehearse-input").fill("phrase: quieter at bar 8")
    pane.locator(".rehearse-dry-run").click()
    page.wait_for_selector(".rehearse-preview table", timeout=15000)
    preview = pane.locator(".rehearse-preview").inner_text()
    assert "tempo_flex" in preview, (
        f"dry-run preview missing the compiled change: {preview}"
    )
    assert "dry run complete" in pane.locator(".rehearse-status").inner_text().lower()
