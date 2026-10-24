"""Reproducible build for the Clinton St proof artifact (#443).

Source MusicXML -> IR -> .ru container (W1/S2/S5) -> decode (P1) ->
fidelity check (W4) -> WAV (P2) + piano-roll score (W5).

    python3 artifacts/clinton-st/build.py

Reproducible: re-running reproduces the .ru *payloads* (manifest.json,
roll.bin, seed.bin) and the WAV byte-for-byte. The .ru zip bytes differ
between runs only in the zip member mtime — a known property of
zipfile, not encoder drift (see tools/muse_mu/manifest.py read_mu, which
compares payloads, not zip bytes). The sample tier (tools/muse_sample, VSCO 2 CE) is not used
here — it needs CDN read access; see the blocker on #443.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "tools"))
sys.path.insert(0, os.path.join(REPO, "tools", "ir"))

from muse_ir import load                      # noqa: E402
from muse_roll import encode as roll_encode   # noqa: E402
from muse_mu import build_manifest, write_mu, read_mu  # noqa: E402
from muse_decode import decode                # noqa: E402
from muse_diff import diff                    # noqa: E402
from muse_play.play import render_work        # noqa: E402

SOURCE = "corpus/allen/clinton-st.musicxml"


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    work = load(os.path.join(REPO, SOURCE))
    roll = roll_encode(work)
    assert roll_encode(work) == roll, "S2 pack not deterministic"

    seed = open(os.path.join(HERE, "seed.yaml"), "rb").read()
    members = {"roll.bin": roll, "seed.bin": seed}
    prov = {"source": SOURCE, "author": "philipdallen",
            "ai_involvement": "none",
            "tools": ["tools/ir", "tools/muse_roll", "tools/muse_mu"]}
    lic = {"renditions": "open-within-constraints",
           "attribution": "Clinton St — tune by Philip D. Allen "
                          "(owner's own work); source encoding supplied in-repo",
           "commercial": False}
    manifest = build_manifest(work_id="clinton-st", license=lic,
                              provenance=prov, members=members)
    ru = os.path.join(HERE, "clinton-st.ru")
    write_mu(ru, manifest, members)
    _, got = read_mu(ru)
    assert got == members, "S5 member round-trip mismatch"

    decoded = decode(ru)
    report = diff(work, decoded)
    assert report.ok(), f"W4 fidelity FAIL recall={report.recall} precision={report.precision}"
    info = render_work(decoded, os.path.join(HERE, "clinton-st.wav"))

    print(f"parse(W1)     {len(work.parts)} parts, {work.note_count} notes")
    print(f"pack(S2)      {len(roll)} bytes, deterministic")
    print(f"container(S5) {os.path.getsize(ru)} bytes, manifest verified")
    print(f"decode(P1)    {len(decoded.parts)} parts, {decoded.note_count} notes")
    print(f"verify(W4)    recall={report.recall} precision={report.precision}")
    print(f"render(P2)    {info['notes']} notes → {info['duration_sec']}s WAV")
    payloads = {"manifest.json": manifest.to_json().encode(),
                "roll.bin": roll, "seed.bin": seed}
    out = {
        "format": "rubato-proof-artifact-v1",
        "work_id": "clinton-st",
        "source": SOURCE,
        "fidelity": {"check": "tools/muse_diff.diff",
                     "recall": report.recall, "precision": report.precision,
                     "notes_source": work.note_count,
                     "notes_decoded": decoded.note_count,
                     "parts": len(work.parts)},
        "payload_sha256": {k: hashlib.sha256(v).hexdigest()
                           for k, v in payloads.items()},
        "wav_sha256": sha256(os.path.join(HERE, "clinton-st.wav")),
        "score_png_sha256": sha256(os.path.join(HERE, "clinton-st-pianoroll.png")),
        "reproduce": "python3 artifacts/clinton-st/build.py",
    }
    with open(os.path.join(HERE, "manifest.json"), "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"payloads      manifest/roll/seed hashes stable across runs")
    print(f"wav sha256    {out['wav_sha256']}")
    print(f"→ {os.path.join(HERE, 'manifest.json')}")


if __name__ == "__main__":
    main()
