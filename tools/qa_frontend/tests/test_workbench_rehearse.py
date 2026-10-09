"""Tier 2 DOM tests for the workbench detail page's per-artifact resilience
(workbench UI QA, issue #390).

The revision loop in ``docs/workbench/detail.html`` awaits several artifact
fetches per revision. A *failed* fetch rejects rather than resolving to null,
so before #390 a single failed artifact threw out of the loop and blanked the
whole console. These tests abort one artifact at a time and assert the page
degrades to that artifact's fallback while the remaining revisions still
render.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")


@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def session():
    with PageSession() as ps:
        yield ps


def test_missing_artifact_degrades_gracefully(server, session):
    """One failed artifact fetch must degrade only its own card: every
    revision row still renders, and no global 'load error' appears."""
    page = session.new_page()
    page.route("**/*.directives.json", lambda route: route.abort())
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    text = page.locator("body").inner_text()
    assert "load error" not in text.lower(), (
        f"a failed artifact fetch blanked the console: {text[:300]}"
    )
    assert page.locator(".wb-rev").count() > 0, "no revision rows rendered"
    # The Rehearse pane owns the directives artifact; a failed fetch leaves
    # its own fallback note rather than aborting the loop.
    assert "no directives committed yet" in text.lower()
