#!/usr/bin/env bash
# tools/run_tests.sh — unified test runner (issue #167; parallelism and the
# -m slow convention per #214).
#
# One command runs every tool's pytest suite with a per-suite report and an
# aggregate exit code. Default is the fast tier (full green path minus the
# known-slow suites and every test marked @pytest.mark.slow); --full runs
# everything incl. slow suites.
#
# Usage:
#   ./tools/run_tests.sh            # fast tier, suites run in parallel
#   ./tools/run_tests.sh --full     # everything (incl. slow)
#   ./tools/run_tests.sh --serial   # fast tier, one suite at a time (debugging)
#   ./tools/run_tests.sh --jobs N   # cap parallel suites (default: nproc, max 8)
#   ./tools/run_tests.sh --list     # show the suite list and exit
#
# Slow convention: a test too heavy for the fast tier carries
# @pytest.mark.slow (registered in tools/pytest.ini). The fast tier passes
# -m "not slow"; --full applies no marker filter. A suite that is slow
# end-to-end stays in SLOW_SUITES below instead.
#
# Deps: python3 -m pip install -r tools/requirements.test.txt
set -u
cd "$(dirname "$0")"
SCRIPT_DIR=$(pwd)

# name:dir — dir relative to tools/. Suites are discovered on purpose, not
# by directory globbing: SPIKE and __pycache__ must stay out.
SUITES=(
  "ir:ir/tests"
  "corpus_loader:corpus_loader"
  "muse_diff:muse_diff"
  "muse_ops:muse_ops"
  "muse_unpack:muse_mu"
  "muse_assert:muse_assert"
  "muse_seed:muse_seed"
  "muse_seed_cli:muse_seed_cli"
  "muse_author:muse_author"
  "s1_stream:s1_stream/tests"
  "muse_viz:muse_viz"
  "muse_roll:muse_roll"
  "assertions:assertions/tests"
)
# Chain smoke (fast tier): e2e on the small registry, W4 verify PASS.
SUITES+=("chain_smoke:muse_chain/test_chain_smoke.py")
# Explorer (fast tier): artifact contract + determinism (quick mode).
SUITES+=("muse_explorer:muse_explorer/tests")
# Probes (fast tier): seed-iteration probe engine.
SUITES+=("muse_probes:muse_probes/tests")
# Study (fast tier): R3 study scripts + seed/render survival feedback (#284, RR2 #381).
SUITES+=("muse_study:muse_study/tests")
# Lineage (fast tier): chain-walk/verify helper (S3.8a).
SUITES+=("muse_lineage:muse_lineage")
# Generate loop (fast tier): schema, provider, generate, integration.
SUITES+=("muse_mockup:muse_mockup")
SUITES+=("muse_provider:muse_provider/tests")
SUITES+=("muse_generate:muse_generate/tests")
SUITES+=("muse_grow:muse_grow/tests")
# P1/P2/L-series (fast tier): decoder, renderer, mockup harness, A/B rig,
# distiller — all corpus-light.
SUITES+=("muse_decode:muse_decode")
SUITES+=("muse_play:muse_play/tests")
SUITES+=("muse_render:muse_render/tests")
SUITES+=("muse_compare:muse_compare/tests")
SUITES+=("muse_distill:muse_distill/tests")
SUITES+=("muse_mockup:muse_mockup")
SUITES+=("muse_workbench_runner:muse_workbench_runner/tests")
# C3/E1 (fast tier): budget engine + event scaffold — sub-second suites.
SUITES+=("muse_budgets:muse_budgets")
SUITES+=("muse_event:muse_event/tests")
# Docs coherence (fast tier): design-doc/status-cache pins (E2 venue plan #230).
SUITES+=("docs:../tests/docs")
# Doc-prose lint (fast tier, T7 #299): offline mechanical doc checks
# (broken relative links, unresolvable backticked paths, open_ refs whose
# record closed, unfilled templates, non-UTF-8 docs).
SUITES+=("muse_docs:muse_docs/tests")
# HuB status-log sweep (fast tier): offline sweep tests.
SUITES+=("hub_sweep:hub_sweep/tests")
# Auditor (fast tier): offline drift/health checks. tools/test_runner_meta.py
# enforces that any test_ file under tools/ is registered here.
SUITES+=("auditor:auditor/tests")
# F1 form curve (fast tier): windowed detector-quantize on corpus file.
SUITES+=("muse_form:muse_form/tests")
# Workbench audio bridge (fast tier): stand-in renders + manifest + live-path
# wiring on recorded fixtures (no network).
SUITES+=("muse_audio:muse_audio/tests")
SLOW_SUITES=(
  "muse_analyze:muse_analyze"
  "muse_chain:muse_chain"
  "qa_frontend:qa_frontend/tests"
)

MODE=fast
LIST_ONLY=0
JOBS=$(nproc 2>/dev/null || echo 2)
[ "$JOBS" -gt 8 ] && JOBS=8
while [ $# -gt 0 ]; do
  case $1 in
    --full) MODE=full ;;
    --list) LIST_ONLY=1 ;;
    --serial) JOBS=1 ;;
    --jobs)
      shift
      case ${1:-} in
        ''|*[!0-9]*) echo "usage: --jobs N (positive integer)" >&2; exit 2 ;;
      esac
      JOBS=$1
      [ "$JOBS" -lt 1 ] && { echo "usage: --jobs N (positive integer)" >&2; exit 2; }
      ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
  shift
done

if [ $LIST_ONLY -eq 1 ]; then
  echo "fast tier:"
  for s in "${SUITES[@]}"; do echo "  ${s%%:*}=${s#*:}"; done
  echo "slow tier (--full adds):"
  for s in "${SLOW_SUITES[@]}"; do echo "  ${s%%:*}=${s#*:}"; done
  exit 0
fi

# Install deps upfront (issue #192). Pytest alone is not enough — a fresh
# sandbox sees import failures across suites without per-file deps; the
# requirements file is the source of truth.
python3 -c "import pytest, yaml, matplotlib" 2>/dev/null || {
  echo "installing test deps: pip install -q -r $SCRIPT_DIR/requirements.test.txt" >&2
  python3 -m pip install -q -r "$SCRIPT_DIR/requirements.test.txt" || {
    echo "dependency install failed — cannot run suites" >&2
    exit 2
  }
}

ALL_SUITES=("${SUITES[@]}")
if [ "$MODE" = full ]; then
  ALL_SUITES+=("${SLOW_SUITES[@]}")
  # qa_frontend needs the headless Chromium binary; install full-tier only
  # (one-time ~115MB download, cached at ~/.cache/ms-playwright). Fast tier
  # never touches the browser (#238).
  python3 -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch().close()" 2>/dev/null || {
    echo "installing chromium for qa_frontend: python3 -m playwright install chromium" >&2
    python3 -m playwright install chromium || {
      echo "chromium install failed — qa_frontend suite will fail" >&2
      exit 2
    }
  }
fi

RESULTS_DIR=$(mktemp -d)
trap 'rm -rf "$RESULTS_DIR"' EXIT

run_suite() {
  local idx=$1 dir=$2
  local t0 t1 rc
  t0=$(date +%s)
  # Run pytest directly (no pipeline) so the recorded rc is pytest's, not
  # a downstream command's. Fast tier deselects @pytest.mark.slow (#214).
  if [ "$MODE" = fast ]; then
    python3 -m pytest "$dir" -q -m "not slow" >"$RESULTS_DIR/$idx.out" 2>&1
  else
    python3 -m pytest "$dir" -q >"$RESULTS_DIR/$idx.out" 2>&1
  fi
  rc=$?
  t1=$(date +%s)
  printf '%s\n' "$rc" >"$RESULTS_DIR/$idx.rc"
  printf '%s\n' "$((t1 - t0))" >"$RESULTS_DIR/$idx.dur"
}

# Suites run concurrently, capped at $JOBS; output is buffered per suite so
# the report below still prints in suite order.
idx=0
for s in "${ALL_SUITES[@]}"; do
  while [ "$(jobs -rp | wc -l)" -ge "$JOBS" ]; do wait -n; done
  run_suite "$idx" "${s#*:}" &
  idx=$((idx + 1))
done
wait

failures=0
idx=0
for s in "${ALL_SUITES[@]}"; do
  name=${s%%:*}
  rc=$(cat "$RESULTS_DIR/$idx.rc")
  dur=$(cat "$RESULTS_DIR/$idx.dur")
  if [ "$rc" -eq 0 ]; then
    printf "PASS  %-16s %4ss    %s\n" "$name" "$dur" "$(tail -1 "$RESULTS_DIR/$idx.out")"
  else
    printf "FAIL  %-16s %4ss    %s\n" "$name" "$dur" "$(tail -1 "$RESULTS_DIR/$idx.out")"
    failures=$((failures + 1))
  fi
  idx=$((idx + 1))
done

echo ""
if [ $failures -eq 0 ]; then
  echo "all suites green"
else
  echo "$failures suite(s) failed" >&2
fi
exit $failures