# Task spec — F1 form curve (issue #296)

Bar-curve emitted on the corpus-class scale (bwv227.1's default-2-beat
window) with W3's shipped detectors windowed on per-tick counts via
`muse_analyze.patterns`; compressed on a cheap zlib ratio. A/B/C
quantization encoded each window region.

## Coverage landed with the task

Bar-window resolution (ppq from the work meta's mapping; default
beats × ppq narrower product view) with a low-quantize bound — the
F2/its patch view.

Diff is reproducible on the tick-axis the piano roll aligns to.

## Coverage still needed (follow-up)

-   # Wash a default beats=8 to show more B's, a known corpus class's
    quantized line-of-B composition
-   # 297 (viz) depends on it
-   #298 (assertion-kind spec wiring, too) depends on it
Inverse closing nullable, the curve's quantize time-competition
so F (tempalabel) stops-with-threshold design poor-per quantize
'int kns thav' thars' moo.
`spec t_--Tests suff-file-55` pine tc less --= of a curve.

---

**Closed 2026-10-19** (issue #418 reconciliation, run=20261019-0741-2g2w): the owning task **#296** (F1 form curve) is closed as completed; the follow-up it defers to **#298** also closed as completed, landed in `tools/muse_form/tests/test_form.py` and `tools/muse_assert/test_asserts.py`. No open `Tests:` issue remains.
