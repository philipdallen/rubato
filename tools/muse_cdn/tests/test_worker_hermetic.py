"""Pytest wrapper for the hermetic muse_cdn worker suite (issue #423).

Runs ``worker_hermetic_test.mjs`` (local ``wrangler dev`` + local R2 binding,
no CDN_TOKEN, no network) so the repo's unified runner — and therefore CI —
exercises the worker without the live endpoint.

The node suite needs the ``wrangler`` CLI, which is not a pip dependency.
If it is not provisioned, the test skips rather than fails: a sandbox with
no node toolchain must not report a red gate for a suite it cannot run.
Set ``WRANGLER_BIN`` to point at a specific binary.
"""

import os
import shutil
import subprocess

import pytest

HERE = os.path.dirname(__file__)
SUITE = os.path.join(HERE, "worker_hermetic_test.mjs")


def _find_wrangler():
    explicit = os.environ.get("WRANGLER_BIN")
    if explicit:
        return explicit if os.path.exists(explicit) else None
    local = os.path.join(HERE, "..", "worker", "node_modules", ".bin", "wrangler")
    if os.path.exists(local):
        return os.path.abspath(local)
    return shutil.which("wrangler")


def test_hermetic_worker_suite():
    if shutil.which("node") is None:
        pytest.skip("node not provisioned")
    wrangler = _find_wrangler()
    if wrangler is None:
        pytest.skip("wrangler not provisioned (set WRANGLER_BIN)")

    env = {**os.environ, "WRANGLER_BIN": wrangler}
    out = subprocess.run(
        ["node", SUITE],
        cwd=HERE,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    print(out.stdout)
    print(out.stderr, file=__import__("sys").stderr)
    assert out.returncode == 0, "hermetic worker suite reported failures"
    assert "0 failed" in out.stdout, out.stdout
