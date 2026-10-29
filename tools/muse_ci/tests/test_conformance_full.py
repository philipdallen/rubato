"""P3 conformance: regeneration fidelity and corpus coverage.

The verify gate (test_conformance.py) pins decoder behavior against the
committed store; these tests pin the store itself: every corpus source
has a vector, and regenerating a vector from its corpus source reproduces
the committed pin byte-for-byte (encoder determinism end-to-end).
"""

import glob
import hashlib
import json
import os

import pytest

from muse_ci import CORPUS, REGISTRY, VECTORS_DIR, build_mu, decoded_canonical
from muse_ci.conformance import PINS_NAME, _load_pins


class TestCorpusCoverage:
    def test_every_corpus_file_has_a_vector(self):
        on_disk = {
            os.path.relpath(f, CORPUS)
            for ext in ("*.xml", "*.mxl", "*.musicxml", "*.mid")
            for f in glob.glob(os.path.join(CORPUS, "*", ext))
        }
        covered = {rel for _, rel in REGISTRY}
        assert on_disk == covered, f"uncovered: {on_disk - covered}"

    def test_no_machine_local_paths_in_store(self):
        text = open(os.path.join(VECTORS_DIR, PINS_NAME)).read()
        assert "/workspace" not in text
        assert '"../' not in text


@pytest.mark.parametrize("work_id,relpath", REGISTRY)
def test_regeneration_reproduces_pin(work_id, relpath, tmp_path):
    pins = _load_pins(VECTORS_DIR)
    mu = tmp_path / f"{work_id}.ru"
    build_mu(work_id, relpath, str(mu))
    canonical = decoded_canonical(str(mu))
    entry = pins[work_id]
    assert len(canonical) == entry["canonical_bytes"]
    assert hashlib.sha256(canonical).hexdigest() == entry["sha256"]
