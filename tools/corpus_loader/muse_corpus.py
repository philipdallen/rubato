"""muse_corpus — W2 corpus loader.

Loads every corpus/ file through the W1 IR (tools/ir) with an
assertion-checked CLI. The ratchet's front door: downstream tools recover
works through this loader, never through ad-hoc parsing.

    python3 tools/corpus_loader/muse_corpus.py list
    python3 tools/corpus_loader/muse_corpus.py load <work>
    python3 tools/corpus_loader/muse_corpus.py check     # the known-answer gate
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ir"))
from muse_ir import load  # noqa: E402

CORPUS_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "corpus")
)

# The corpus registry. Each work maps to its files and known-answer pins,
# measured 2026-08-23 through the W1 IR (tools/ir). Pins: parts and written
# note events (ties separate, rests/chords/grace included — the IR's
# fidelity contract), dynamics marks, and hairpins.
WORKS = {
    "bach-bwv227": {
        "title": "Bach, Jesu meine Freude BWV 227 (chorale movements)",
        "files": [
            ("bach/bwv227.1.mxl", {"parts": 4, "notes": 279, "dynamics": 0, "hairpins": 0}),
            ("bach/bwv227.3.mxl", {"parts": 5, "notes": 377, "dynamics": 0, "hairpins": 0}),
            ("bach/bwv227.7.mxl", {"parts": 4, "notes": 307, "dynamics": 0, "hairpins": 0}),
            ("bach/bwv227.11.mxl", {"parts": 4, "notes": 190, "dynamics": 0, "hairpins": 0}),
        ],
    },
    "byrd-mass3v": {
        "title": "Byrd, Mass for Three Voices (all 6 movements)",
        "files": [
            ("byrd/1-Kyrie.mid", {"parts": 3, "notes": 71, "dynamics": 0, "hairpins": 0}),
            ("byrd/2-Gloria.mid", {"parts": 3, "notes": 924, "dynamics": 0, "hairpins": 0}),
            ("byrd/3-Credo.mid", {"parts": 3, "notes": 1440, "dynamics": 0, "hairpins": 0}),
            ("byrd/4-Sanctu.mid", {"parts": 3, "notes": 327, "dynamics": 0, "hairpins": 0}),
            ("byrd/5-Bened.mid", {"parts": 3, "notes": 130, "dynamics": 0, "hairpins": 0}),
            ("byrd/6-Agnus.mid", {"parts": 3, "notes": 384, "dynamics": 0, "hairpins": 0}),
        ],
    },
    "schubert-d810": {
        "title": "Schubert, Death and the Maiden D.810 (complete quartet)",
        "files": [
            ("schubert/death-and-the-maiden.mxl",
             {"parts": 4, "notes": 24772, "dynamics": 1731, "hairpins": 441}),
        ],
    },
    "beethoven-sym5-mov1": {
        "title": "Beethoven, Symphony No. 5, mov. 1",
        "files": [
            ("beethoven/beethoven-sym5-mov1.xml",
             {"parts": 12, "notes": 13675, "dynamics": 431, "hairpins": 0}),
        ],
    },
    "beethoven-sym9": {
        "title": "Beethoven, Symphony No. 9 (complete)",
        "files": [
            ("beethoven/beethoven-sym9.xml",
             {"parts": 52, "notes": 239459, "dynamics": 11931, "hairpins": 1013}),
        ],
    },
    "allen-clinton-st": {
        # Owner's own work (not public domain) — supplied as MIDI, converted
        # to MusicXML 4.0 2026-10-21. Both files carry pins.
        "title": "Allen, Clinton St (owner-supplied)",
        "files": [
            ("allen/clinton-st.musicxml",
             {"parts": 2, "notes": 212, "dynamics": 0, "hairpins": 0}),
            ("allen/clinton-st.mid",
             {"parts": 2, "notes": 192, "dynamics": 0, "hairpins": 0}),
        ],
    },
}


class CheckFailure(AssertionError):
    """A corpus file failed its known-answer pins or failed to parse."""


def iter_files():
    for work_id, entry in WORKS.items():
        for relpath, pins in entry["files"]:
            yield work_id, entry["title"], relpath, pins


def load_file(relpath):
    """Load one corpus file into IR. Raises IRParseError on bad input."""
    return load(os.path.join(CORPUS_ROOT, relpath))


def summarize(work):
    return {
        "source_format": work.meta.source_format,
        "ppq": work.meta.ppq,
        "parts": len(work.parts),
        "notes": work.note_count,
        "dynamics": sum(len(p.dynamics) for p in work.parts),
        "hairpins": sum(len(p.hairpins) for p in work.parts),
        "tempo_entries": len(work.maps.tempo),
        "meter_entries": len(work.maps.meter),
        "key_entries": len(work.maps.key),
        "duration_ticks": work.duration_ticks(),
        "warnings": list(work.meta.warnings),
    }


def check_file(relpath, pins, root=None):
    """Assert one corpus file against its pins. Returns its summary."""
    path = os.path.join(root or CORPUS_ROOT, relpath)
    if not os.path.exists(path):
        raise CheckFailure(f"{relpath}: file missing from corpus/")
    try:
        work = load(path)
    except Exception as e:
        raise CheckFailure(f"{relpath}: parse failed: {type(e).__name__}: {e}") from e
    got = summarize(work)
    mismatches = [
        f"{k} {got[k]} != {pins[k]}"
        for k in ("parts", "notes", "dynamics", "hairpins")
        if got[k] != pins[k]
    ]
    if mismatches:
        raise CheckFailure(f"{relpath}: {'; '.join(mismatches)}")
    return got


def run_check(root=None, out=sys.stdout):
    """Run the check gate; returns the failures list (empty when green)."""
    failures = []
    n = 0
    for _work_id, _title, relpath, pins in iter_files():
        n += 1
        try:
            got = check_file(relpath, pins, root=root)
            print(f"OK  {relpath}: {got['parts']} parts, {got['notes']} notes, "
                  f"{got['dynamics']} dynamics, {got['hairpins']} hairpins", file=out)
        except CheckFailure as e:
            failures.append(str(e))
    return n, failures


def cmd_list(_args):
    print(f"{'work':<20} {'file':<38} {'fmt':<8} title")
    for work_id, title, relpath, _pins in iter_files():
        fmt = "midi" if relpath.endswith(".mid") else "musicxml"
        print(f"{work_id:<20} {relpath:<38} {fmt:<8} {title}")
    return 0


def cmd_load(args):
    failures = 0
    for work_id, title, relpath, _pins in iter_files():
        if work_id != args.work:
            continue
        work = load_file(relpath)
        s = summarize(work)
        print(f"{relpath} — {title}")
        print(f"  source_format={s['source_format']} ppq={s['ppq']} "
              f"parts={s['parts']} notes={s['notes']} duration_ticks={s['duration_ticks']}")
        print(f"  dynamics={s['dynamics']} hairpins={s['hairpins']} "
              f"maps: tempo={s['tempo_entries']} meter={s['meter_entries']} key={s['key_entries']}")
        if s["source_format"] == "midi":
            print("  note: MIDI source — voices inferred, no notated dynamics")
        for w in s["warnings"]:
            print(f"  warning: {w}")
    else:
        if not any(wid == args.work for wid, *_ in iter_files()):
            print(f"unknown work: {args.work} (see 'list')", file=sys.stderr)
            failures = 1
    return failures


PIN_KEYS = ("parts", "notes", "dynamics", "hairpins")


def measure_file(relpath):
    """Re-measure one corpus file through the IR — the pin update path."""
    got = summarize(load_file(relpath))
    return {k: got[k] for k in PIN_KEYS}


def cmd_update_pins(_args):
    changed = 0
    for _work_id, _title, relpath, pins in iter_files():
        measured = measure_file(relpath)
        if measured != pins:
            changed += 1
            print(f"{relpath}: pins drifted")
            for k in PIN_KEYS:
                if measured[k] != pins[k]:
                    print(f"  {k}: {pins[k]} -> {measured[k]}")
    if changed:
        print(f"\n{changed} file(s) drifted. Pins change only by deliberate "
              f"corpus action — if the diffs above are expected, update WORKS "
              f"in muse_corpus.py with the measured values and review the diff.")
    else:
        print("All pins match — registry is current.")
    return 0


def cmd_check(_args):
    n, failures = run_check()
    if failures:
        print("\nFAILURES:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print(f"\nAll {n} corpus files pass their known-answer pins.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="muse-corpus", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="registry table: work, files, source_format")
    p_load = sub.add_parser("load", help="IR summary for one work")
    p_load.add_argument("work", help="work id from 'list'")
    sub.add_parser("check", help="known-answer assertions across the registry")
    sub.add_parser("update-pins", help="re-measure pins; print drift for review")
    args = ap.parse_args(argv)
    handlers = {"list": cmd_list, "load": cmd_load, "check": cmd_check,
                "update-pins": cmd_update_pins}
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
