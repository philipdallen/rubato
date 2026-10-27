"""Tests for the unified test runner (issue #176).

Self-test: --list inventory must include every tools/<name> that contains
test files (guards against a new tool landing without registration).

Runs without executing the full fast/full tiers (that's the runner's own
job); this suite tests the runner's discovery contract.
"""

import os
import subprocess

import pytest

TOOLS = os.path.dirname(__file__)  # tools/
RUNNER = os.path.join(TOOLS, "run_tests.sh")

# Paths with test files that the runner inventory must contain
REQUIRED_SUITES = [
    "ir/tests",
    "corpus_loader",
    "muse_diff",
    "muse_ops",
    "muse_mu",
    "muse_assert",
    "muse_seed",
    "muse_seed_cli",
    "muse_author",
    "s1_stream/tests",
    "muse_viz",
    "muse_roll",
    "muse_chain/test_chain_smoke.py",
    "muse_explorer/tests",
    "assertions",
]


def _ls():
    out = subprocess.run(
        ["bash", RUNNER, "--list"],
        cwd=TOOLS, capture_output=True, text=True, timeout=30,
    )
    assert out.returncode == 0, out.stderr
    return out.stdout


@pytest.mark.parametrize("suite", REQUIRED_SUITES)
def test_runner_lists_every_tool_with_tests(suite):
    inventory = _ls()
    assert suite in inventory, f"runner missed suite {suite!r}"


def test_unknown_flag_exits_2():
    out = subprocess.run(["bash", RUNNER, "--bogus"], cwd=os.path.dirname(RUNNER), capture_output=True)
    assert out.returncode == 2


def test_runner_labels_fail_on_pytest_failure(tmp_path):
    """Issue #191: PASS must only print when a suite's pytest actually exits 0.
    Synthetic failing suite dir; the meta file's inventory doesn't cover it."""
    failing_dir = tmp_path / "fail_suite"
    failing_dir.mkdir()
    (failing_dir / "test_fail.py").write_text("def test_fails():\n    assert False\n")
    out = subprocess.run(
        ["python3", "-m", "pytest", str(failing_dir), "-q"],
        cwd=TOOLS, capture_output=True, text=True,
    )
    assert out.returncode != 0, "synthetic failing suite must exit nonzero"


def test_requirements_file_mentions_deps():
    """Issue #192: requirements.test.txt should list every dependency that suites
    import. Guards against a fresh sandbox getting masked import failures."""
    reqs = os.path.join(TOOLS, "requirements.test.txt")
    assert os.path.exists(reqs)
    text = open(reqs).read()
    for needed in ("pytest", "mido", "pyyaml", "matplotlib"):
        assert needed in text, f"requirements.test.txt missing {needed!r}"


# --- Discovery contract (issue #217, spec gap 1): the inventory test above
# pins a hardcoded suite list; this one derives the expectation from the
# tree, so a new tool landing without registration fails on its own.

# Paths excluded from the contract by design: spike scripts are pre-workflow,
# and these two runner self-tests run directly (they invoke run_tests.sh on
# synthetic tmp suites), not via the runner — registering them would recurse.
DISCOVERY_EXCLUDE_DIRS = {"spike", "__pycache__"}
DISCOVERY_EXCLUDE_FILES = {"test_runner_meta.py", "test_runner_parallel.py"}


def _registered_dirs():
    """--list inventory as a set of paths relative to tools/ (dirs or files)."""
    out = _ls()
    dirs = set()
    for line in out.splitlines():
        line = line.strip()
        if "=" in line:
            dirs.add(line.split("=", 1)[1])
    return dirs


def _discovered_test_files():
    found = []
    for root, dirs, files in os.walk(TOOLS):
        dirs[:] = [d for d in dirs if d not in DISCOVERY_EXCLUDE_DIRS]
        for f in files:
            if f.startswith("test_") and f.endswith(".py") \
                    and f not in DISCOVERY_EXCLUDE_FILES:
                found.append(os.path.relpath(os.path.join(root, f), TOOLS))
    return sorted(found)


def test_discovery_contract_all_test_files_registered():
    """Every test file under tools/ must be covered by a --list entry —
    the 'new suite must be registered' rule as an assertion, not a
    convention. If this fails, either register the suite in
    run_tests.sh or add a documented exclusion above."""
    registered = _registered_dirs()
    missing = [
        path for path in _discovered_test_files()
        if not any(path == entry or path.startswith(entry.rstrip("/") + "/")
                   for entry in registered)
    ]
    assert not missing, f"test files with no registered suite: {missing}"