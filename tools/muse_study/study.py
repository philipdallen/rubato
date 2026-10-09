"""R3 study scripts + directive-survival feedback (#284).

A script is a list of named directive steps. run_script compiles each to
a seed and, crucially, also builds the mockup and asks the distiller
whether the directive *survived the render* — the feedback loop that
trains the conductor's ear without live musicians.

Survival is measured in two lanes. The **seed-param lane** maps each verb
to the seed knob it should move (VERB_MEASURES) and compares base vs
candidate seed params. The **render lane** (RR2, #381) realizes both seeds
into a mockup and asks whether the directive survived the render: with the
real L1 generate loop (`MUSE_L1_LIVE`, #276) it compares the distilled
Interpretation (velocity spread, part gains, curve shape); with the
deterministic stand-in it reports `stand-in-blocked`, since the stand-in is
flat regardless of seed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


class StudyError(ValueError):
    pass


# verb → (interpretation field, expected direction of movement)
# Compiled from R1's knob map: what the distiller can measure moving.
VERB_MEASURES = {
    "rebalance": ("part_gains", "up"),        # named part should dominate
    "phrase": ("tempo_curve_shape", "arch"),  # a phrase arch forms
    "tempo_arch": ("tempo_range", "wider"),   # tempo bounds widen
    "rubato": ("rubato_pstdev_ms", "up"),     # more spread
    "hold": ("tempo_curve_shape", "flat"),    # constrained arch → flatter
}


@dataclass
class Step:
    directive: str
    expect: str = ""                # free-text note on the intended effect


@dataclass
class Script:
    name: str
    issue: str                      # the interpretive issue it drills
    steps: list = field(default_factory=list)


# Precomposed study sequences, keyed to well-known rehearsal issues.
# Templates reference the work's parts (resolved at run time).
SCRIPTS = {
    "quiet-the-bass": Script(
        name="quiet-the-bass",
        issue="bass part dominates the texture; the upper voices vanish "
              "under it (the 'quiet the cellos into the development' drill)",
        steps=[
            Step("rebalance: bring P4 down", "lower the bass line into balance"),
            Step("rebalance: bring P4 down 30% at ticks 0-9999",
                 "overcorrect deliberately — hear the boundary"),
            Step("rebalance: bring P4 up", "return toward balance"),
        ]),
    "phrase-the-pickup": Script(
        name="phrase-the-pickup",
        issue="pickup notes arrive flat; no anacrusis arch into the downbeat",
        steps=[
            Step("phrase: quieter into development", "arch the pickup"),
            Step("phrase: broader into development",
                 "exaggerate the dip — hear the shape"),
        ]),
    "tempo-architecture": Script(
        name="tempo-architecture",
        issue="tempo wanders without an arch; the form loses its spine",
        steps=[
            Step("tempo_arch: wider", "open the bounds"),
            Step("tempo_arch: settle",
                 "narrow back — the arch should read as contained"),
        ]),
    "rubato-calibration": Script(
        name="rubato-calibration",
        issue="onset-offset spread is either mechanical or soupy",
        steps=[
            Step("rubato: more", "add spread"),
            Step("rubato: less", "tighten back"),
            Step("hold: whole work", "pin it — hear mechanical as a floor"),
        ]),
}


def _build_mockup(work, seed, mockup_fn=None, provider=None):
    """work + seed → (Mockup, live_flag).

    Mirrors muse_grow's gate: with MUSE_L1_LIVE set and a seed in hand,
    build via the real L1 generate loop (`muse_grow.real_mockup`) and report
    live=True; otherwise the deterministic stand-in (live=False). An explicit
    `mockup_fn` (tests, `live=True`) wins over both and is called as
    `mockup_fn(work, seed)`. `provider` is forwarded to the live loop so a
    RecordedProvider fixture can drive it offline.
    """
    from muse_grow.grow import _mockup_from_work, real_mockup

    if mockup_fn is not None:
        return mockup_fn(work, seed), True
    if seed is not None and os.environ.get("MUSE_L1_LIVE"):
        return real_mockup(work, seed, provider), True
    return _mockup_from_work(work), False


def run_script(script: Script, seed_path: str, era="baroque",
               work=None, mockup_fn=None, provider=None):
    """Compile each step and report per-step survival.

    mockup_fn: (work, seed) → Mockup. When omitted the deterministic
    stand-in is used unless MUSE_L1_LIVE is set, in which case the real L1
    generate loop is used (same pin as muse_grow).
    Returns (last_candidate_seed, [StepReport]). The script is a drill —
    it dry-runs each step in sequence on the running candidate, then
    checks survival of *each* against the base.
    """
    from muse_rehearse import parse_directive, compile_directive
    from muse_seed import load_seed

    base = load_seed(open(seed_path).read(), fmt="yaml")
    reports = []
    candidate = base
    base_mockup = cand_mockup = None
    live = False
    if work is not None:
        base_mockup, live = _build_mockup(work, base, mockup_fn, provider)
    for step in script.steps:
        d = parse_directive(step.directive, seed=base, work=work)
        candidate = compile_directive(d, candidate, era, work)
        if work is not None:
            cand_mockup, _ = _build_mockup(work, candidate, mockup_fn, provider)
        reports.append(check_survival(step, base, candidate, work, mockup_fn,
                                      base_mockup=base_mockup,
                                      candidate_mockup=cand_mockup,
                                      live=live))
    return candidate, reports


@dataclass
class StepReport:
    directive: str
    verb: str
    measure: str              # interpretation field checked
    expected: str             # expected movement
    base_value: object
    candidate_value: object
    verdict: str              # moved | flat | drifted
    expect_note: str = ""
    render_measure: str = "velocity_pstdev"
    render_base: object = None
    render_candidate: object = None
    render_verdict: str = "stand-in-blocked"

    def to_dict(self):
        return {"directive": self.directive, "verb": self.verb,
                "measure": self.measure, "expected": self.expected,
                "base": self.base_value, "candidate": self.candidate_value,
                "verdict": self.verdict, "note": self.expect_note,
                "render": {"measure": self.render_measure,
                           "base": self.render_base,
                           "candidate": self.render_candidate,
                           "verdict": self.render_verdict}}


def _render_survival(base_mockup, candidate_mockup, live):
    """(base, candidate, verdict) for the render lane, or the stand-in marker.

    Only the live generate loop can move the mockup in seed-dependent ways;
    the deterministic stand-in is flat regardless of seed, so the lane
    reports "stand-in-blocked" rather than a misleading `flat`. When live and
    both mockups exist, compare the distilled `Interpretation` fields the
    issue names — velocity spread, rubato spread, per-part gains and curve
    shape: `moved` when any differs, else `flat`.
    """
    if not live or base_mockup is None or candidate_mockup is None:
        return None, None, "stand-in-blocked"
    from muse_distill import extract_interpretation

    b_i = extract_interpretation(base_mockup)
    c_i = extract_interpretation(candidate_mockup)
    moved = (c_i.velocity_pstdev != b_i.velocity_pstdev
             or c_i.rubato_pstdev_ms != b_i.rubato_pstdev_ms
             or c_i.part_gains != b_i.part_gains
             or c_i.tempo_curve_shape != b_i.tempo_curve_shape)
    return b_i.velocity_pstdev, c_i.velocity_pstdev, ("moved" if moved else "flat")


def check_survival(step, base_seed, candidate_seed, work, mockup_fn,
                   base_mockup=None, candidate_mockup=None, live=False):
    """Did this directive survive?

    Two lanes. The seed-param lane asks whether the compiled knob actually
    landed in the candidate seed: `moved`/`flat`/`drifted`. The render lane
    asks whether the change survived realization into a mockup: with the
    deterministic stand-in it reports "stand-in-blocked" (flat regardless of
    seed); with the real L1 generate loop (MUSE_L1_LIVE, #276) it compares
    the distilled interpretation (velocity spread, part gains, curve shape)
    and reports `moved`/`flat`.
    """
    verb = step.directive.split(":", 1)[0].split()[0].rstrip(":").lower()
    measure, expected = VERB_MEASURES.get(verb, (None, None))
    base_v, cand_v, verdict = _seed_survival(verb, base_seed, candidate_seed)
    rb, rc, rv = _render_survival(base_mockup, candidate_mockup, live)
    return StepReport(directive=step.directive, verb=verb,
                      measure=measure or "—", expected=expected or "—",
                      base_value=base_v, candidate_value=cand_v,
                      verdict=verdict, expect_note=step.expect,
                      render_base=rb, render_candidate=rc,
                      render_verdict=rv)


def _seed_survival(verb, base, cand):
    """(base_value, candidate_value, verdict) for the verb's seed knob."""
    bp, cp = base.params, cand.params
    if verb == "rebalance":
        b = bp.get("part_gains", {}); c = cp.get("part_gains", {})
        moved = any(c.get(k) != b.get(k) for k in set(b) | set(c))
        return b, c, "moved" if moved else "flat"
    if verb == "phrase":
        n_b = len(getattr(base, "variation_points", []) or [])
        n_c = len(getattr(cand, "variation_points", []) or [])
        return n_b, n_c, "moved" if n_c > n_b else "flat"
    if verb == "tempo_arch":
        bt = bp.get("tempo", {}); ct = cp.get("tempo", {})
        b_span = bt.get("max_bpm", 0) - bt.get("min_bpm", 0)
        c_span = ct.get("max_bpm", 0) - ct.get("min_bpm", 0)
        return b_span, c_span, (
            "moved" if c_span != b_span else "flat")
    if verb == "rubato":
        b = bp.get("articulation", {}).get("rubato_pstdev_ms", 0.0)
        c = cp.get("articulation", {}).get("rubato_pstdev_ms", 0.0)
        return b, c, "moved" if c != b else "flat"
    if verb == "hold":
        has = "tempo_bounds" in getattr(cand, "assertions", {})
        return None, has, "moved" if has else "flat"
    return None, None, "unmeasurable"
