"""Pin the committed Clinton St proof artifact (#450).

Asserts the published claims in ``artifacts/clinton-st/manifest.json`` still
hold against the committed files only: the W4 fidelity block, the payload
SHA-256 values recomputed from the ``.ru`` members, and the decoded note
count. No rebuild, no network, no CDN token — this guards the artifact from a
silent encoder/parser change, it does not reproduce it.
"""

import hashlib
import json
import os
import sys
import zipfile

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
ARTIFACT = os.path.join(REPO, "artifacts", "clinton-st")
RU = os.path.join(ARTIFACT, "clinton-st.ru")
MANIFEST = os.path.join(ARTIFACT, "manifest.json")

sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, os.path.join(REPO, "tools", "ir"))
from muse_decode import decode  # noqa: E402


@pytest.fixture(scope="module")
def manifest():
    with open(MANIFEST) as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def members():
    """Committed .ru members, read straight from the zip container."""
    with zipfile.ZipFile(RU) as zf:
        return {name: zf.read(name) for name in zf.namelist()}


def test_fidelity_block_matches_published_claims(manifest):
    fidelity = manifest["fidelity"]
    assert fidelity["recall"] == 1.0
    assert fidelity["precision"] == 1.0
    assert fidelity["pitched_source"] == 196
    assert fidelity["rests_source"] == 16
    assert fidelity["parts"] == 2
    assert fidelity["events_source"] == 196 + 16


def test_work_id_and_source(manifest):
    assert manifest["work_id"] == "clinton-st"
    assert manifest["source"] == "corpus/allen/clinton-st.musicxml"


def test_payload_hashes_match_committed_members(manifest, members):
    for name, expected in manifest["payload_sha256"].items():
        assert name in members, f"{name} missing from .ru container"
        actual = hashlib.sha256(members[name]).hexdigest()
        assert actual == expected, f"{name} payload hash drifted"


def test_decoded_note_count_matches_manifest(manifest):
    work = decode(RU)
    assert work.note_count == manifest["fidelity"]["events_decoded"]
    assert len(work.parts) == manifest["fidelity"]["parts"]
