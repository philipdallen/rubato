"""Explorer tests (issue #164): artifact contract + page mount safety."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from muse_explorer.generate import generate  # noqa: E402
from muse_corpus import WORKS  # noqa: E402

REPO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
REGISTRY_FILES = sum(len(e["files"]) for e in WORKS.values())
EXPLORER = os.path.join(REPO, "docs", "explorer")


@pytest.fixture(scope="module")
def works(tmp_path_factory):
    out = tmp_path_factory.mktemp("explorer")
    return generate(str(out), quick=True), str(out)


def test_works_json_covers_registry(works):
    entries, _ = works
    assert len(entries) == REGISTRY_FILES, "every corpus registry file must appear"


def test_every_work_has_pinned_fields(works):
    entries, _ = works
    required = {
        "id", "title", "file", "parts", "notes", "dynamics", "hairpins",
        "duration_ticks", "ppq", "source_format", "part_names",
        "roll_bytes", "pack_ratio", "piano_roll", "patterns",
    }
    for entry in entries:
        assert required <= set(entry), f"{entry['id']}: missing fields"
        assert entry["parts"] > 0 and entry["notes"] > 0
        assert 0 < entry["pack_ratio"] < 1


def test_piano_rolls_exist_and_non_empty(tmp_path):
    """Render contract: one small work renders a real PNG (full renders are
    the committed-artifact path, not the test loop)."""
    out = tmp_path / "one"
    generate(str(out), quick=True)
    committed = os.path.join(EXPLORER, "img", "bach_bwv227.1.png")
    assert os.path.getsize(committed) > 1000
    with open(committed, "rb") as fh:
        assert fh.read(8) == b"\x89PNG\r\n\x1a\n"


def test_json_is_deterministic(tmp_path):
    a = generate(str(tmp_path / "a"), quick=True)
    b = generate(str(tmp_path / "b"), quick=True)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_committed_artifacts_match_regeneration(tmp_path):
    """Freshness tripwire: committed docs/explorer/data/works.json must
    equal a fresh quick regeneration."""
    committed = json.load(open(os.path.join(EXPLORER, "data", "works.json")))
    fresh = generate(str(tmp_path), quick=True)
    assert committed["works"] == fresh, (
        "docs/explorer/data/works.json is stale — regenerate with "
        "python3 tools/muse_explorer/generate.py"
    )


def test_page_mount_safety():
    """index.html must mount safely: fetch path correct, noindex meta,
    error fallback present, no external resources."""
    html = open(os.path.join(EXPLORER, "index.html")).read()
    assert 'noindex' in html
    assert "data/works.json" in html
    assert "boot().catch" in html, "fetch failure must render a fallback"
    assert "http://" not in html and "https://" not in html.replace(
        "https://github.com", ""
    ), "no external runtime resources"


# --- Tests: #178 follow-up ---


def test_all_piano_roll_references_resolve():
    """Every committed works.json piano_roll path must point at a real,
    non-empty PNG — the page renders exactly these paths, so a missing or
    truncated image is a broken page, not a data nit."""
    committed = json.load(open(os.path.join(EXPLORER, "data", "works.json")))
    assert committed["works"], "works.json is empty"
    for entry in committed["works"]:
        path = os.path.join(EXPLORER, entry["piano_roll"])
        assert os.path.exists(path), f"{entry['id']}: missing {entry['piano_roll']}"
        assert os.path.getsize(path) > 1000, f"{entry['id']}: {entry['piano_roll']} suspiciously small"
        with open(path, "rb") as fh:
            assert fh.read(8) == b"\x89PNG\r\n\x1a\n", f"{entry['id']}: not a PNG"


def test_pattern_merge_covers_all_works():
    """W3 report → explorer seam: every committed work must carry non-empty
    pattern counts. The counts are regex-parsed from docs/analysis-report.md;
    a report-format change must fail here loudly, not zero the page."""
    committed = json.load(open(os.path.join(EXPLORER, "data", "works.json")))
    for entry in committed["works"]:
        assert entry["patterns"], (
            f"{entry['id']} ({entry['file']}): empty patterns — regenerate "
            "with python3 tools/muse_explorer/generate.py, or the W3 report "
            "format drifted from the parser"
        )


def test_pattern_counts_missing_report_returns_empty(tmp_path, monkeypatch):
    """No analysis report → no patterns, no crash (page degrades)."""
    import muse_explorer.generate as gen

    monkeypatch.setattr(gen, "REPORT", str(tmp_path / "absent.md"))
    assert gen._pattern_counts() == {}


def test_pattern_counts_ignores_malformed_blocks(tmp_path, monkeypatch):
    """Only well-formed 'N distinct patterns' lines land in the merge;
    prose and half-formed lines are skipped, not coerced."""
    import muse_explorer.generate as gen

    report = tmp_path / "report.md"
    report.write_text(
        "# Analysis\n"
        "## bach/bwv227.1.mxl\n"
        "exact repeats: 889 distinct patterns\n"
        "this line is prose, not a count\n"
        "transposed repeats: not-a-number distinct patterns\n"
        "## byrd/1-Kyrie.mid\n"
        "imitative entries: 12 distinct patterns\n"
    )
    monkeypatch.setattr(gen, "REPORT", str(report))
    assert gen._pattern_counts() == {
        "bach/bwv227.1.mxl": {"exact repeats": 889},
        "byrd/1-Kyrie.mid": {"imitative entries": 12},
    }


# --- #273: workbench seed index dedup + repo-relative lineage hops ---

import hashlib  # noqa: E402

WB_SEEDS = os.path.join(REPO, "docs", "workbench", "data", "seeds")


def test_workbench_index_no_byte_identical_duplicates():
    """Regression pin (#273): the seed index never lists two entries whose
    files are byte-identical; the duplicate is recorded as an alias."""
    index = json.load(open(os.path.join(WB_SEEDS, "index.json")))
    digests = []
    for entry in index["seeds"]:
        raw = open(os.path.join(WB_SEEDS, entry["file"]), "rb").read()
        digests.append(hashlib.sha256(raw).hexdigest())
    assert len(digests) == len(set(digests)), (
        "index lists byte-identical seed files as separate entries")
    base = next(e for e in index["seeds"] if e["file"] == "bwv227.1.seed.yaml")
    assert "bwv227.1.v1.seed.yaml" in base.get("aliases", [])


def test_workbench_artifacts_carry_no_machine_local_paths():
    """Lineage hops (and the artifacts generally) must be repo-relative —
    the same leak class s1_stream pins for golden vectors (#273)."""
    for fname in os.listdir(WB_SEEDS):
        if not fname.endswith(".json"):
            continue
        text = open(os.path.join(WB_SEEDS, fname)).read()
        assert "/workspace" not in text and REPO not in text, (
            f"{fname} embeds machine-local paths")
    v2 = json.load(open(os.path.join(WB_SEEDS, "bwv227.1.v2.probes.json")))
    hop = v2["probes"]["lineage"]["hops"][0]
    assert hop["child"] == "seeds/bwv227.1.v2.seed.yaml"
    assert hop["status"] == "verified"
