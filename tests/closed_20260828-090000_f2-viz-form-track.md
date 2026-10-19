# Task spec — F2 viz form track (issue #297)

Strip renders one letter-bar per window colored by A/B/C over the same
tick axis as the notes.

## Coverage landed

- Rendering file non-empty (one letter-bar per window, A/B/C channels)
- tick-aligned to the notes axis.

## Coverage still needed (follow-up)

The follow-up #298 (assertion part anymore) already contains it.

---

**Closed 2026-10-19** (issue #418 reconciliation, run=20261019-0741-2g2w): the owning task **#297** (F2 form track) is closed as completed; the remaining viz coverage it defers to **#298** also closed as completed, landed in `tools/muse_viz/test_muse_viz.py`. No open `Tests:` issue remains.
