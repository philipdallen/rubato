"""T4 seam: S1 golden vectors through the landed P1 decoder (issue #416).

`docs/pipeline.md` marked T4 "done as stub contract (#168)": #168 pinned the
swap (the seam's decoder entry point switches from the S2 stub to P1, and
every golden-vector contract test then runs against the real decoder), but
the swap was never executed because P1 did not exist. P1 landed in #197
(`tools/muse_decode/`), so this file executes it.

The seam: a corpus work is packed to a `.ru` container (the decoder's real
input), run through P1, and its S1 canonical stream is compared byte-for-byte
against the committed golden vector for the same source. The container is
built from the corpus source in-test (rather than read from
`tools/muse_ci/vectors/`) so the assertion isolates the decoder: P1 must turn
the S2 payload into exactly the S1 canonical stream the golden vector pins.

    python3 -m pytest tools/s1_stream/tests/test_s1_p1_golden_seam.py
"""

import hashlib
import os
import sys

import pytest

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))       # tools/
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..", "ir")))  # muse_ir
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..")))              # muse_stream

from muse_ci.conformance import REGISTRY, build_mu  # noqa: E402
from muse_decode import decode  # noqa: E402
from muse_stream import canonical_json  # noqa: E402

GOLDEN_DIR = os.path.normpath(os.path.join(HERE, "..", "golden"))
SLOW_WORKS = {"beethoven-sym9"}  # 35 MB canonical stream; --full only

# work_id (muse_ci.conformance.REGISTRY) → committed S1 golden vector filename.
# Explicit because the golden names are irregular: some truncate the work
# (`byrd-4-sanctus` → `byrd_4-sanctu.json`), and a derived rule would guess
# wrong and silently skip the assertion.
GOLDEN_NAME = {
    "bach-bwv227.1": "bach_bwv227.1.json",
    "bach-bwv227.3": "bach_bwv227.3.json",
    "bach-bwv227.7": "bach_bwv227.7.json",
    "bach-bwv227.11": "bach_bwv227.11.json",
    "byrd-1-kyrie": "byrd_1-kyrie.json",
    "byrd-2-gloria": "byrd_2-gloria.json",
    "byrd-3-credo": "byrd_3-credo.json",
    "byrd-4-sanctus": "byrd_4-sanctu.json",
    "byrd-5-benedictus": "byrd_5-bened.json",
    "byrd-6-agnus": "byrd_6-agnus.json",
    "schubert-d810": "schubert_d810.json",
    "beethoven-sym5-mov1": "beethoven_sym5_mov1.json",
    "beethoven-sym9": "beethoven_sym9.json",
}


def _golden_path(work_id):
    name = GOLDEN_NAME[work_id]
    path = os.path.join(GOLDEN_DIR, name)
    assert os.path.exists(path), f"missing golden vector: {path}"
    return path


@pytest.mark.parametrize("work_id,relpath", REGISTRY)
def test_golden_vector_decodes_byte_exact(work_id, relpath, tmp_path):
    """Corpus source → `.ru` container → P1 decode → S1 canonical stream
    must equal the committed golden vector byte-for-byte."""
    if work_id in SLOW_WORKS:
        pytest.skip("slow work — fast tier; run --full for the full registry")

    mu = tmp_path / f"{work_id}.ru"
    build_mu(work_id, relpath, str(mu))
    got = canonical_json(decode(str(mu))).encode()

    with open(_golden_path(work_id), "rb") as fh:
        expected = fh.read()

    assert len(got) == len(expected), (
        f"{work_id}: canonical length {len(got)} != golden {len(expected)}"
    )
    assert hashlib.sha256(got).hexdigest() == hashlib.sha256(expected).hexdigest(), (
        f"{work_id}: P1 decode drifted from the S1 golden vector"
    )


@pytest.mark.slow
@pytest.mark.parametrize(
    "work_id,relpath", [w for w in REGISTRY if w[0] in SLOW_WORKS]
)
def test_golden_vector_decodes_byte_exact_slow(work_id, relpath, tmp_path):
    """Same contract as above, for works too heavy for the fast tier."""
    mu = tmp_path / f"{work_id}.ru"
    build_mu(work_id, relpath, str(mu))
    got = canonical_json(decode(str(mu))).encode()
    with open(_golden_path(work_id), "rb") as fh:
        expected = fh.read()
    assert got == expected, f"{work_id}: P1 decode drifted from the S1 golden vector"
