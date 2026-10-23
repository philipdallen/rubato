"""Workbench site navigation pins (issue #304).

The QA surfaces were reachable only by hand-editing the URL. #304 adds a
persistent cross-page nav (identical markup on every page) and per-revision
jump links on the workbench detail page.

Two tiers here:
  * source-scan tests — the nav markup is *identical* across pages and
    carries no hardcoded host/port (the #305 failure mode is a hardcoded
    origin; the nav must not repeat it);
  * DOM tests (slow tier, Playwright) — every page mounts the nav, every
    link resolves to a 200 route, and the jump links target real revision
    blocks and open them on click.
"""

import hashlib
import os
import re
import sys
import urllib.error
import urllib.request

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")

# Every page that carries the shared nav. Root-relative hrefs mean one
# markup string works from any depth (repo convention: docs/ is the site root).
NAV_PAGES = [
    "index.html",
    "explorer/index.html",
    "workbench/detail.html",
    "workbench/coach.html",
    "workbench/files.html",
    "workbench/terminal.html",
    "boardroom/index.html",
]

# The routes the nav must expose (label -> path).
NAV_ROUTES = [
    "/index.html",
    "/explorer/",
    "/workbench/detail.html",
    "/workbench/coach.html",
    "/workbench/files.html",
    "/workbench/terminal.html",
    "/boardroom/",
]

NAV_RE = re.compile(r'<nav class="site-nav".*?</nav>', re.S)


def _read(rel):
    with open(os.path.join(DOCS, rel)) as fh:
        return fh.read()


def _nav(rel):
    m = NAV_RE.search(_read(rel))
    assert m, f"{rel} carries no .site-nav"
    return m.group(0)


# --- Source-scan tier: markup identity + no hardcoded origins ---

def test_every_surface_carries_the_nav():
    for rel in NAV_PAGES:
        assert NAV_RE.search(_read(rel)), f"{rel} is missing the shared .site-nav"


def test_nav_markup_identical_across_pages():
    """The DoD asks for "the same markup on every page" — pinned by hashing
    the nav block, so a divergent copy fails here rather than in review."""
    digests = {
        rel: hashlib.sha256(_nav(rel).encode()).hexdigest() for rel in NAV_PAGES
    }
    assert len(set(digests.values())) == 1, f"nav markup diverged: {digests}"


def test_nav_exposes_every_route():
    for rel in NAV_PAGES:
        nav = _nav(rel)
        for route in NAV_ROUTES:
            assert f'href="{route}"' in nav, f"{rel}: nav missing {route}"


def test_nav_has_no_hardcoded_host_or_port():
    """DoD 3: relative links, no hardcoded host/port (the #305 bug class)."""
    for rel in NAV_PAGES:
        nav = _nav(rel)
        assert "http://" not in nav and "https://" not in nav, f"{rel}: absolute URL in nav"
        assert not re.search(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", nav), f"{rel}: IP literal in nav"


def test_nav_pages_carry_no_stale_terminal_route():
    """The nav and tile links must name the real route. `workbench/terminal/`
    (trailing slash) is a 404 — the page is terminal.html."""
    for rel in NAV_PAGES:
        body = _read(rel)
        assert "workbench/terminal/" not in body, (
            f"{rel} links the removed trailing-slash terminal route"
        )


# --- DOM tier: mounts, links resolve, jump links work ---

@pytest.fixture(scope="module")
def server():
    with serve_static(DOCS) as s:
        yield s


@pytest.fixture(scope="module")
def session():
    with PageSession() as ps:
        yield ps


@pytest.mark.parametrize("rel", NAV_PAGES)
def test_nav_mounts_on_every_page(server, session, rel):
    page = session.new_page()
    page.goto(f"{server.url}/{rel}", wait_until="networkidle")
    assert page.locator("nav.site-nav").count() == 1, f"{rel}: nav did not mount"


def test_nav_links_all_resolve_200(server):
    """DoD 3: each nav target is a real route over the served site."""
    for route in NAV_ROUTES:
        url = server.url + route
        try:
            with urllib.request.urlopen(url) as r:
                assert r.status == 200, f"{route} -> {r.status}"
                assert "<html" in r.read().decode().lower(), f"{route} not HTML"
        except urllib.error.HTTPError as e:  # pragma: no cover - failure path
            raise AssertionError(f"{route} did not resolve: HTTP {e.code}") from e


def test_nav_links_are_clickable_to_a_route(server, session):
    """The nav is a working affordance, not decoration: clicking the Files
    entry from the detail page lands on the files route."""
    page = session.new_page()
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    page.locator('nav.site-nav a[href="/workbench/files.html"]').click()
    page.wait_for_load_state("networkidle")
    assert "/workbench/files.html" in page.url, page.url
    assert page.locator("nav.site-nav").count() == 1, "nav lost after navigation"


def test_jump_links_target_real_revision_blocks(server, session):
    """DoD 2: one jump link per committed revision, each targeting an
    existing details.wb-rev block."""
    page = session.new_page()
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    links = page.locator("#jump a[data-rev]")
    assert links.count() == 4, f"expected 4 revision jump links, got {links.count()}"
    rows = page.locator("details.wb-rev")
    assert rows.count() == 4
    for i in range(links.count()):
        target = links.nth(i).get_attribute("data-rev")
        assert page.locator(f"details.wb-rev#{target}").count() == 1, (
            f"jump target {target} matches no revision block"
        )


def test_jump_link_opens_collapsed_revision(server, session):
    """Clicking a jump link to a collapsed revision opens it, so the reader
    lands on the panels and not a one-line summary."""
    page = session.new_page()
    page.goto(server.url + "/workbench/detail.html", wait_until="networkidle")
    # v2 is collapsed by default (only the first row starts open)
    second = page.locator("details.wb-rev").nth(1)
    assert not second.evaluate("el => el.open"), "v2 should start collapsed"
    target_id = page.locator("#jump a[data-rev]").nth(1).get_attribute("data-rev")
    page.locator(f'#jump a[data-rev="{target_id}"]').click()
    page.wait_for_timeout(200)
    assert page.locator(f"details.wb-rev#{target_id}").evaluate("el => el.open"), (
        "jump link did not open the target revision"
    )


def test_nav_zero_console_errors(server, session):
    for rel in ("index.html", "explorer/index.html", "workbench/detail.html",
                "boardroom/index.html"):
        page = session.new_page()
        page.goto(f"{server.url}/{rel}", wait_until="networkidle")
    assert session.console_errors == [], (
        f"console errors after nav mount: {session.console_errors[:3]}"
    )
