"""W-B6 corpus-tree DOM tests: master index groups 5 works / 13 files."

The attached workbench folder is served via `docs/` so the tree path is
`/index.html` and detail pages live at `/workbench/detail.html`.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from qa_frontend.harness import PageSession, serve_static  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")


@pytest.fixture(scope="module")
def site():
    with serve_static(DOCS) as srv:
        yield srv


def page(url):
    sess = PageSession()
    pg = sess.new_page()
    pg.goto(url)
    # index.html builds ul.files from an async fetch of seeds/index.json.
    # Reading the DOM straight after goto races that fetch — it wins on a
    # fast dev box and loses on the slower CI runner, which is why this suite
    # failed only on CI (0 == 13). Wait for the first row before returning.
    pg.wait_for_selector("ul.files li")
    return sess, pg


def test_tree_groups_five_files(site):
    sess, pg = page(f"{site.url}/index.html")
    count = pg.evaluate("document.querySelectorAll('ul.files li a').length")
    sess.close()
    assert count == 13


def test_seed_pill_states(site):
    sess, pg = page(f"{site.url}/index.html")
    states = pg.evaluate("""
      [...document.querySelectorAll('ul.files li .seed-pill')].map(e => e.textContent)
    """)
    sess.close()
    assert len(states) == 13
    assert states.count('seeded') == 1
    assert states.count('unseeded') == 12


def test_links_to_detail_route(site):
    """Every file row links into the site: seeded files to their work anchor
    on the workbench detail page, unseeded ones to the file viewer.

    Pinned to *resolving* targets as of #310 — the old form was
    `workbench/detail.html#<fid>` (e.g. `#bwv227.1`), which matched no
    element on the page: 12 of the 13 rows were dead links.
    """
    sess, pg = page(f"{site.url}/index.html")
    hrefs = pg.evaluate("""
      [...document.querySelectorAll('ul.files li a')].map(a => a.getAttribute('href'))
    """)
    sess.close()
    assert all(h.startswith('workbench/') for h in hrefs), hrefs
    for h in hrefs:
        if h.startswith('workbench/detail.html#'):
            anchor = h.split('#', 1)[1]
            # slugged work anchor — no dots, so a CSS selector can reach it
            assert '.' not in anchor, f"unslugged anchor id: {anchor}"
            assert anchor.startswith('work-'), anchor


def test_every_row_anchor_exists_on_the_detail_page(site):
    """The deep-link contract, executed: each seeded row's anchor must exist
    on the rendered detail page (fetched live, JS included)."""
    sess = PageSession()
    pg = sess.new_page()
    pg.goto(f"{site.url}/index.html")
    hrefs = pg.evaluate("""
      [...document.querySelectorAll('ul.files li a')].map(a => a.getAttribute('href'))
    """)
    sess.close()

    anchors = {h.split('#', 1)[1] for h in hrefs if '#' in h}
    assert anchors, "no deep links in the corpus tree"

    sess = PageSession()
    pg = sess.new_page()
    pg.goto(f"{site.url}/workbench/detail.html", wait_until="networkidle")
    present = set(pg.evaluate("[...document.querySelectorAll('[id]')].map(e => e.id)"))
    sess.close()

    missing = sorted(a for a in anchors if a not in present)
    assert not missing, f"corpus-tree links point at missing anchors: {missing}"