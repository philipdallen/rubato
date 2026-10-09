"""Runner parallelism + slow-marker tests (issue #239; spec
tests/open_20260824-111500_runner-parallel-slow-marker.md).

Exercises the real runner engine against synthetic suites in a tmp dir:
the script is copied and its SUITES/SLOW_SUITES tables are patched to
absolute tmp paths, so the parallelism, reporting, exit-code, and marker
behavior under test is the shipped code — never a reimplementation.
Synthetic suites are never registered in the real tables.
"""

import os
import re
import subprocess
import time

import pytest

TOOLS = os.path.dirname(__file__)
RUNNER = os.path.join(TOOLS, "run_tests.sh")


def _write_suite(dirpath, body):
    os.makedirs(dirpath)
    with open(os.path.join(dirpath, "test_suite.py"), "w") as fh:
        fh.write(body)


def _patched_runner(tmp_path, fast_entries, slow_entries=()):
    """Copy run_tests.sh with SUITES/SLOW_SUITES tables replaced by the
    given name:abs-path entries. Everything else is the shipped engine."""
    src = open(RUNNER).read()
    fast_table = "SUITES=(\n" + "".join(f'  "{n}:{p}"\n' for n, p in fast_entries) + ")\n"
    slow_table = "SLOW_SUITES=(\n" + "".join(f'  "{n}:{p}"\n' for n, p in slow_entries) + ")\n"
    patched = re.sub(
        r"SUITES=\(.*?\n(?:SUITES\+=\(.*\)\n)*.*?\n(?=MODE=fast)",
        fast_table + slow_table,
        src,
        flags=re.DOTALL,
    )
    assert "synth" in patched or not fast_entries, "table patch failed to apply"
    out = tmp_path / "run_tests_copy.sh"
    out.write_text(patched)
    return str(out)


def _run(script, *flags, cwd=TOOLS):
    return subprocess.run(
        ["bash", script, *flags], cwd=cwd, capture_output=True, text=True, timeout=300,
    )


# --- Flag parsing ---

def test_jobs_missing_argument_exits_2():
    assert _run(RUNNER, "--jobs").returncode == 2


def test_jobs_non_numeric_exits_2():
    assert _run(RUNNER, "--jobs", "abc").returncode == 2


def test_jobs_zero_exits_2():
    assert _run(RUNNER, "--jobs", "0").returncode == 2


def test_serial_composes_with_list():
    r = _run(RUNNER, "--serial", "--list")
    assert r.returncode == 0
    assert "fast tier:" in r.stdout


# --- Parallel report order ---

def test_report_prints_in_suite_order_not_completion_order(tmp_path):
    """The slow suite is listed first but finishes last under --jobs 4;
    the report must still print it first (buffered per-suite output)."""
    slow = tmp_path / "slow_suite"
    fast = tmp_path / "fast_suite"
    _write_suite(str(slow), "import time\ndef test_slow():\n    time.sleep(3)\n")
    _write_suite(str(fast), "def test_fast():\n    pass\n")
    script = _patched_runner(
        tmp_path, [("synth_slow", str(slow)), ("synth_fast", str(fast))]
    )
    t0 = time.time()
    r = _run(script, "--jobs", "4")
    wall = time.time() - t0
    assert r.returncode == 0, r.stdout + r.stderr
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith(("PASS", "FAIL"))]
    assert [ln.split()[1] for ln in lines] == ["synth_slow", "synth_fast"]
    assert wall < 6, f"not parallel? wall {wall:.1f}s >= serial 3s+overhead bound"


# --- Aggregate exit code ---

def test_exit_code_equals_failure_count(tmp_path):
    ok1, ok2, bad = tmp_path / "ok1", tmp_path / "ok2", tmp_path / "bad"
    _write_suite(str(ok1), "def test_a():\n    pass\n")
    _write_suite(str(ok2), "def test_b():\n    pass\n")
    _write_suite(str(bad), "def test_c():\n    assert False\n")
    script = _patched_runner(
        tmp_path,
        [("synth_ok1", str(ok1)), ("synth_bad", str(bad)), ("synth_ok2", str(ok2))],
    )
    r = _run(script, "--jobs", "3")
    assert r.returncode == 1, r.stdout
    assert "1 suite(s) failed" in r.stderr
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith(("PASS", "FAIL"))]
    assert [ln.split()[0] for ln in lines] == ["PASS", "FAIL", "PASS"]


# --- Failing test id surfaced on FAIL rows (issue #384) ---

def test_fail_row_surfaces_failing_test_id(tmp_path):
    """On FAIL, the recorded output's last line is only the count; the report
    must also name the failing test id from pytest's short summary, or a
    CI-only failure cannot be triaged without a local reproduction (#384)."""
    bad = tmp_path / "bad_suite"
    _write_suite(str(bad), "def test_c():\n    assert False\n")
    script = _patched_runner(tmp_path, [("synth_bad", str(bad))])
    r = _run(script, "--jobs", "1")
    assert r.returncode == 1, r.stdout + r.stderr
    fail_line = next(ln for ln in r.stdout.splitlines() if ln.startswith("FAIL"))
    assert fail_line.split()[0] == "FAIL"  # existing contract intact
    assert "::test_c" in r.stdout, f"failing test id not surfaced:\n{r.stdout}"


# --- Slow-marker split ---

MARKED_SUITE = """import pytest

@pytest.mark.slow
def test_heavy():
    pass

def test_light():
    pass
"""


def test_fast_tier_deselects_slow_marker_full_tier_runs_it(tmp_path):
    marked = tmp_path / "marked_suite"
    _write_suite(str(marked), MARKED_SUITE)
    script = _patched_runner(tmp_path, [("synth_marked", str(marked))])

    fast = _run(script)
    assert fast.returncode == 0, fast.stdout + fast.stderr
    assert "1 passed, 1 deselected" in fast.stdout

    full = _run(script, "--full")
    assert full.returncode == 0, full.stdout + full.stderr
    assert "2 passed" in full.stdout


# --- Install-guard path (regression: repo-root-relative requirements) ---

def test_install_guard_uses_script_dir_and_exits_2_on_failure():
    src = open(RUNNER).read()
    guard = re.search(r"import pytest, yaml, matplotlib.*?^}", src, re.DOTALL | re.MULTILINE)
    assert guard, "install guard block not found"
    assert '"$SCRIPT_DIR/requirements.test.txt"' in guard.group(0)
    assert "exit 2" in guard.group(0), "failed install must exit 2, not run suites"
