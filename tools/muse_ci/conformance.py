"""P3 conformance suite — golden vectors pinning the reference decoder.

A vector is a (`.ru` container → decoded event stream) pair. The `.ru`
inputs are committed binaries (fixed decoder inputs — the gate stays
meaningful even if the encoder drifts); the expected outputs are pinned
as sha256 over the S1 canonical JSON of the P1-decoded Work, plus part/
note counts for cheap diagnostics. Full canonical JSON is deliberately
not duplicated here — s1_stream/golden already pins that content; on a
mismatch, `cli.py dump` reproduces the actual canonical stream for
diffing against it.

    python3 tools/muse_ci/cli.py generate --full   # rebuild vectors/ from corpus
    python3 tools/muse_ci/cli.py verify            # fast registry (gate)
    python3 tools/muse_ci/cli.py verify --full     # all 14 works
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass

CORPUS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "corpus"))
VECTORS_DIR = os.path.join(os.path.dirname(__file__), "vectors")
PINS_NAME = "pins.json"
PINS_FORMAT = "muse-ci-pins-v1"
SEED_BYTES = b"muse-ci-conformance-seed"

# Pinned to corpus/README.md and muse_chain.chain.REGISTRY — amending the
# corpus means regenerating these vectors in the same commit.
REGISTRY = [
    ("bach-bwv227.1", "bach/bwv227.1.mxl"),
    ("bach-bwv227.3", "bach/bwv227.3.mxl"),
    ("bach-bwv227.7", "bach/bwv227.7.mxl"),
    ("bach-bwv227.11", "bach/bwv227.11.mxl"),
    ("byrd-1-kyrie", "byrd/1-Kyrie.mid"),
    ("byrd-2-gloria", "byrd/2-Gloria.mid"),
    ("byrd-3-credo", "byrd/3-Credo.mid"),
    ("byrd-4-sanctus", "byrd/4-Sanctu.mid"),
    ("byrd-5-benedictus", "byrd/5-Bened.mid"),
    ("byrd-6-agnus", "byrd/6-Agnus.mid"),
    ("schubert-d810", "schubert/death-and-the-maiden.mxl"),
    ("beethoven-sym5-mov1", "beethoven/beethoven-sym5-mov1.xml"),
    ("beethoven-sym9", "beethoven/beethoven-sym9.xml"),
    ("clinton-st", "allen/clinton-st.musicxml"),
]

# Fast-tier gate: the chain-smoke subset (small, one MIDI + one MXL family).
FAST_REGISTRY = REGISTRY[0:1] + REGISTRY[4:6]


@dataclass
class VectorResult:
    work_id: str
    status: str          # PASS | FAIL
    detail: str = ""


def build_mu(work_id, relpath, out_path):
    """Corpus source → .ru container (W1 parse → S2 pack → S5 container)."""
    from muse_ir import load
    from muse_mu import build_manifest, write_mu
    from muse_roll import encode as roll_encode

    work = load(os.path.join(CORPUS, relpath))
    roll_bytes = roll_encode(work)
    if roll_encode(work) != roll_bytes:
        raise RuntimeError(f"{work_id}: S2 pack not deterministic")
    members = {"roll.bin": roll_bytes, "seed.bin": SEED_BYTES}
    prov = {"source": f"corpus/{relpath}", "author": "muse_ci",
            "ai_involvement": "none",
            "tools": ["tools/ir", "tools/muse_roll", "tools/muse_mu"]}
    lic = {"renditions": "closed",
           "attribution": "P3 conformance vector (decoder gate)",
           "commercial": False}
    manifest = build_manifest(work_id=work_id, license=lic, provenance=prov,
                              members=members)
    write_mu(out_path, manifest, members)


def decoded_canonical(mu_path):
    """`.ru` → P1 decode → S1 canonical JSON bytes (FORMAT_SPEC §4.4)."""
    from muse_decode import decode as mu_decode
    from muse_stream import canonical_json

    return canonical_json(mu_decode(mu_path)).encode()


def _pin_entry(work_id, relpath, canonical):
    return {
        "source": f"corpus/{relpath}",
        "ru": f"{work_id}.ru",
        "sha256": hashlib.sha256(canonical).hexdigest(),
        "canonical_bytes": len(canonical),
    }


def _load_pins(vectors_dir):
    with open(os.path.join(vectors_dir, PINS_NAME)) as fh:
        pins = json.load(fh)
    if pins.get("format") != PINS_FORMAT:
        raise ValueError(f"unknown pins format: {pins.get('format')!r}")
    return pins["vectors"]


def generate(vectors_dir=VECTORS_DIR, registry=REGISTRY):
    """(Re)build the vector store: one .ru per registry work + pins.json."""
    os.makedirs(vectors_dir, exist_ok=True)
    vectors = {}
    for work_id, relpath in registry:
        mu_path = os.path.join(vectors_dir, f"{work_id}.ru")
        build_mu(work_id, relpath, mu_path)
        vectors[work_id] = _pin_entry(work_id, relpath, decoded_canonical(mu_path))
    pins = {"format": PINS_FORMAT, "vectors": vectors}
    with open(os.path.join(vectors_dir, PINS_NAME), "w") as fh:
        json.dump(pins, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return vectors


def verify(vectors_dir=VECTORS_DIR, registry=FAST_REGISTRY):
    """Decode each committed .ru through P1; canonical sha256 must match
    its pin. Decode errors are FAIL, never exceptions."""
    pins = _load_pins(vectors_dir)
    results = []
    for work_id, relpath in registry:
        entry = pins.get(work_id)
        if entry is None:
            results.append(VectorResult(work_id, "FAIL", "no pin entry"))
            continue
        mu_path = os.path.join(vectors_dir, entry["ru"])
        if not os.path.exists(mu_path):
            results.append(VectorResult(work_id, "FAIL", f"missing {entry['ru']}"))
            continue
        try:
            canonical = decoded_canonical(mu_path)
        except Exception as e:
            results.append(VectorResult(work_id, "FAIL", f"decode error: {e}"))
            continue
        digest = hashlib.sha256(canonical).hexdigest()
        if digest != entry["sha256"]:
            results.append(VectorResult(
                work_id, "FAIL",
                f"canonical sha256 {digest[:12]}… != pinned {entry['sha256'][:12]}…"))
        elif len(canonical) != entry["canonical_bytes"]:
            results.append(VectorResult(work_id, "FAIL", "canonical size drift"))
        else:
            results.append(VectorResult(
                work_id, "PASS",
                f"{entry['canonical_bytes']} canonical bytes, sha256 {digest[:12]}…"))
    return results
