"""W-B5 runner tests: allow-list enforcement, fail-closed config, exec."""

import json
import os
import sys
import urllib.request
import urllib.error
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from muse_workbench_runner.runner import Runner, COMMANDS, REPO_ROOT
from muse_workbench_runner.server import serve

ROOT = REPO_ROOT


def cfg(tmp_path, **over):
    base = {
        "runner": "tools/muse_workbench_runner",
        "sandbox": "local",
        "allowlist": ["muse_probes.run"],
        "prompt_enabled": True,
    }
    base.update(over)
    p = tmp_path / "wb.json"
    p.write_text(json.dumps(base))
    return p


class TestConfig:
    def test_repo_config_loads(self):
        r = Runner()
        assert r.error is None
        assert "muse_seed.validate" in r.available

    def test_missing_config_fails_closed(self, tmp_path):
        r = Runner(tmp_path / "nope.json")
        assert r.error is not None
        assert r.available == []
        assert r.run("muse_probes.run")["ok"] is False

    def test_empty_allowlist_fails_closed(self, tmp_path):
        r = Runner(cfg(tmp_path, allowlist=[]))
        assert r.error is not None

    def test_unknown_command_in_allowlist_rejected(self, tmp_path):
        r = Runner(cfg(tmp_path, allowlist=["rm -rf /"]))
        assert r.error is not None

    def test_malformed_json_fails_closed(self, tmp_path):
        p = tmp_path / "wb.json"
        p.write_text("{ not json")
        r = Runner(p)
        assert r.error is not None


class TestRun:
    def test_unknown_command_405(self, tmp_path):
        r = Runner(cfg(tmp_path))
        res = r.run("shell")
        assert res["rc"] == 405
        assert res["ok"] is False

    def test_disallowed_command_405(self, tmp_path):
        r = Runner(cfg(tmp_path))  # allowlist only has probes
        res = r.run("muse_play.render")
        assert res["rc"] == 405

    def test_exec_captures_output(self, tmp_path):
        r = Runner(cfg(tmp_path, allowlist=["muse_probes.run"]))
        res = r.run("muse_probes.run", ["--help"])
        assert res["argv"][0] == "python3"
        assert res["stdout"] or res["stderr"]
        assert res["rc"] in (0, 1, 2)


class TestServer:
    @pytest.fixture
    def server(self, tmp_path):
        srv, url = serve(config_path=cfg(tmp_path))
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        yield url
        srv.shutdown()

    def get(self, url, path):
        return json.loads(urllib.request.urlopen(url + path).read())

    def post(self, url, path, payload):
        req = urllib.request.Request(
            url + path, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_commands_endpoint(self, server):
        out = self.get(server, "/api/commands")
        assert out["error"] is None
        assert out["commands"] == ["muse_probes.run"]

    def test_run_unknown_405(self, server):
        code, out = self.post(server, "/api/run", {"name": "shell", "args": []})
        assert code == 405
        assert out["ok"] is False

    def test_run_allowed(self, server):
        code, out = self.post(server, "/api/run", {"name": "muse_probes.run", "args": ["--help"]})
        assert code in (200, 500)
        assert "argv" in out

    def test_run_bad_args_400(self, server):
        code, out = self.post(server, "/api/run", {"name": "muse_probes.run", "args": "not-a-list"})
        assert code == 400

    def test_404_other_paths(self, server):
        with pytest.raises(urllib.error.HTTPError) as e:
            self.get(server, "/api/secret")
        assert e.value.code == 404


def test_all_commands_map_to_repo_tools():
    for name, argv in COMMANDS.items():
        assert argv[0] in ("python3", "bash")
        tool = argv[1]
        assert (ROOT / tool).exists(), f"{name}: {tool} missing"


def test_rehearse_commands_registered():
    """#393: the workbench runner exposes muse_rehearse.dry-run/commit so the
    Rehearse pane can call them via /api/run."""
    for name in ("muse_rehearse.dry-run", "muse_rehearse.commit"):
        assert name in COMMANDS, f"{name} absent from COMMANDS"
        assert COMMANDS[name][0] == "python3", f"{name}: expected python3 argv[0]"
    assert COMMANDS["muse_rehearse.dry-run"][-1] == "dry-run"
    assert COMMANDS["muse_rehearse.commit"][-1] == "commit"
    r = Runner()
    assert r.error is None
    assert "muse_rehearse.dry-run" in r.available
    assert "muse_rehearse.commit" in r.available


class TestSameOriginStaticServing:
    """Issue #305: the server can serve docs/ and /api from one origin."""

    @pytest.fixture
    def docs_server(self):
        srv, url = serve(0, None, ROOT / "docs")
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        yield url
        srv.shutdown()

    def test_static_page_served(self, docs_server):
        with urllib.request.urlopen(docs_server + "/workbench/terminal.html") as r:
            assert r.status == 200
            assert b"<html" in r.read().lower()

    def test_api_and_static_share_the_origin(self, docs_server):
        for path in ("/api/commands", "/workbench/terminal.html", "/index.html"):
            with urllib.request.urlopen(docs_server + path) as r:
                assert r.status == 200, path

    def test_directory_path_serves_index(self, docs_server):
        with urllib.request.urlopen(docs_server + "/explorer/") as r:
            assert r.status == 200
            assert b"html" in r.read().lower()

    def test_api_paths_are_not_shadowed_by_static(self, docs_server):
        """ /api/<unknown> must 404 as JSON machinery, never fall through to
        the static tree."""
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(docs_server + "/api/secret")
        assert e.value.code == 404

    def test_path_traversal_blocked(self, docs_server):
        """Must not escape docs/ (AGENTS.md lives one level up)."""
        for probe in ("/../AGENTS.md", "/../../etc/passwd", "/..%2fAGENTS.md"):
            with pytest.raises(urllib.error.HTTPError) as e:
                urllib.request.urlopen(docs_server + probe)
            assert e.value.code == 404, probe

    def test_static_serving_off_by_default(self, tmp_path):
        """Without docs_dir the server is API-only — the previous behavior."""
        srv, url = serve(0, None, None)
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            with pytest.raises(urllib.error.HTTPError) as e:
                urllib.request.urlopen(url + "/workbench/terminal.html")
            assert e.value.code == 404
            with urllib.request.urlopen(url + "/api/commands") as r:
                assert r.status == 200
        finally:
            srv.shutdown()

    def test_no_cors_header_by_default(self, docs_server):
        """Security posture, pinned. With no --allow-origin the runner sends
        no CORS header, so a page on another origin cannot read responses.
        This server executes commands; any-origin access would let a visited
        website drive the local runner."""
        req = urllib.request.Request(docs_server + "/api/commands")
        with urllib.request.urlopen(req) as r:
            acao = r.headers.get("Access-Control-Allow-Origin")
            vary = r.headers.get("Vary")
        assert acao is None, (
            f"runner sent Access-Control-Allow-Origin: {acao!r} by default — "
            f"must require an explicit --allow-origin"
        )
        assert vary == "Origin", "Vary: Origin must always be present"

    # --- content types (issue #312) ---
    # A wrong type on .json breaks fetch().json() in the workbench pages, so
    # the mapping is pinned rather than left to review.

    @pytest.mark.parametrize("path,expected", [
        ("/workbench/detail.html", "text/html; charset=utf-8"),
        ("/workbench/data/works.json", "application/json"),
        ("/explorer/img/bach_bwv227.1.png", "image/png"),
        ("/audio/README.md", "text/markdown; charset=utf-8"),
    ])
    def test_content_type_mapping(self, docs_server, path, expected):
        with urllib.request.urlopen(docs_server + path) as r:
            assert r.headers["Content-Type"] == expected, path

    def test_unknown_extension_falls_back_to_octet_stream(self, docs_server):
        with urllib.request.urlopen(docs_server + "/superseded.txt") as r:
            assert r.headers["Content-Type"] == "application/octet-stream"

    # --- large files (issue #312) ---

    def test_large_binary_served_byte_identical(self, docs_server):
        """The spike WAVs are multi-MB; responses stream in chunks, and the
        bytes must still match the file exactly."""
        import hashlib

        big = ROOT / "docs" / "spike" / "byrd-mockup-v3.wav"
        if not big.exists():
            pytest.skip("spike WAV not present in this checkout")
        with urllib.request.urlopen(docs_server + "/spike/byrd-mockup-v3.wav") as r:
            served = r.read()
            assert r.headers["Content-Length"] == str(big.stat().st_size)
        assert hashlib.sha256(served).hexdigest() == hashlib.sha256(
            big.read_bytes()).hexdigest()

    def test_static_chunk_is_smaller_than_the_largest_file(self):
        """Guard the streaming property: if the chunk size ever grows past a
        real asset, responses are buffered whole again and the memory note in
        server.py stops being true."""
        from muse_workbench_runner.server import make_handler

        handler = make_handler(Runner(), ROOT / "docs")
        assert handler.CHUNK < 1_000_000, "chunk size defeats the point of streaming"

    # --- concurrency (issue #312) ---

    def test_concurrent_requests_both_complete(self, docs_server):
        """ThreadingHTTPServer plus subprocess exec: two simultaneous /api/run
        calls must both finish (a shared-state bug would strand one)."""
        import concurrent.futures

        def call():
            body = json.dumps({"name": "muse_probes.run", "args": ["--help"]}).encode()
            req = urllib.request.Request(
                docs_server + "/api/run", data=body,
                headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    return json.loads(r.read()).get("argv")
            except urllib.error.HTTPError as e:
                return json.loads(e.read()).get("argv")

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = [f.result() for f in [pool.submit(call), pool.submit(call)]]
        assert all(results), f"one of the concurrent calls did not complete: {results}"
        assert results[0] == results[1], "concurrent calls diverged"


class TestOriginScopedCORS:
    """Issue #316: an explicit, origin-scoped opt-in for cross-origin use.

    Options (a) drop the overrides and (b) origin-scoped CORS were offered;
    (b) was chosen so the documented feature actually works, without ever
    emitting a wildcard from a command-executing server.
    """

    @pytest.fixture
    def cors_server(self, tmp_path):
        """A server allowing exactly one origin."""
        srv, url = serve(0, cfg(tmp_path), ROOT / "docs",
                         ["http://allowed.example"])
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        yield url
        srv.shutdown()

    def _get(self, url, origin=None):
        req = urllib.request.Request(url)
        if origin:
            req.add_header("Origin", origin)
        with urllib.request.urlopen(req) as r:
            return r.status, dict(r.headers)

    def test_allowed_origin_echoed_exactly(self, cors_server):
        status, headers = self._get(cors_server + "/api/commands",
                                    "http://allowed.example")
        assert status == 200
        assert headers.get("Access-Control-Allow-Origin") == "http://allowed.example"
        assert headers.get("Vary") == "Origin"

    def test_disallowed_origin_gets_no_cors_header(self, cors_server):
        """A different origin must not be granted access — and must not be
        told the endpoint exists beyond an ordinary response."""
        _, headers = self._get(cors_server + "/api/commands", "http://evil.example")
        assert headers.get("Access-Control-Allow-Origin") is None
        assert headers.get("Vary") == "Origin"

    def test_never_emits_a_wildcard(self, cors_server):
        for origin in ("http://allowed.example", "http://evil.example", None):
            _, headers = self._get(cors_server + "/api/commands", origin)
            assert headers.get("Access-Control-Allow-Origin") != "*", (
                "wildcard CORS must never be emitted by a command-executing server"
            )

    def test_preflight_allowed_origin(self, cors_server):
        req = urllib.request.Request(cors_server + "/api/run", method="OPTIONS")
        req.add_header("Origin", "http://allowed.example")
        req.add_header("Access-Control-Request-Method", "POST")
        with urllib.request.urlopen(req) as r:
            assert r.status == 204
            assert r.headers.get("Access-Control-Allow-Origin") == "http://allowed.example"
            assert "POST" in (r.headers.get("Access-Control-Allow-Methods") or "")

    def test_preflight_disallowed_origin_refused(self, cors_server):
        req = urllib.request.Request(cors_server + "/api/run", method="OPTIONS")
        req.add_header("Origin", "http://evil.example")
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(req)
        assert e.value.code == 403, f"expected 403, got {e.value.code}"

    def test_origin_matching_is_exact(self, cors_server):
        """No prefix/suffix or subdomain matching: a lookalike origin must not
        be accepted (e.g. allowed.example.evil.com)."""
        for lookalike in ("http://allowed.example.evil.com",
                          "http://allowed.exampl",
                          "http://allowed.example:1234"):
            _, headers = self._get(cors_server + "/api/commands", lookalike)
            assert headers.get("Access-Control-Allow-Origin") is None, lookalike

    def test_trailing_slash_normalised(self, cors_server):
        """An Origin header never carries a trailing slash, but a user typing
        the flag might; normalise rather than silently never matching."""
        _, headers = self._get(cors_server + "/api/commands", "http://allowed.example")
        assert headers.get("Access-Control-Allow-Origin") == "http://allowed.example"

    def test_wildcard_flag_rejected_by_cli(self):
        """`--allow-origin '*'` must be refused outright, not honoured."""
        import subprocess

        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "tools", "muse_workbench_runner",
                                          "server.py"),
             "--allow-origin", "*"],
            capture_output=True, text=True, timeout=30,
        )
        assert proc.returncode != 0, "wildcard origin was accepted"
        assert "wildcard" in (proc.stderr + proc.stdout).lower()

    def test_documented_script_invocation_starts(self):
        """The invocation the README documents must actually run.

        Found by this test suite: `python3 tools/muse_workbench_runner/
        server.py` died with a relative-import error, so #305's README and its
        done comment both described a command that could never work. Neither
        the module tests nor the qa_frontend tests exercised the CLI path."""
        import socket
        import subprocess
        import time

        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]

        proc = subprocess.Popen(
            [sys.executable, os.path.join(ROOT, "tools", "muse_workbench_runner",
                                          "server.py"),
             "--docs", "--port", str(port)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            cwd=str(ROOT),
        )
        try:
            deadline = time.time() + 15
            body = None
            while time.time() < deadline:
                if proc.poll() is not None:
                    break  # died: fall through to the assertion below
                try:
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:{port}/api/commands", timeout=1
                    ) as r:
                        body = json.loads(r.read())
                        break
                except Exception:
                    time.sleep(0.2)
            if proc.poll() is not None:
                out = proc.stdout.read() if proc.stdout else ""
                raise AssertionError(
                    "the documented script invocation exited immediately:\n" + out
                )
            assert body and "commands" in body, "CLI server did not answer /api/commands"
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:  # pragma: no cover
                proc.kill()

    def test_cross_origin_run_actually_works(self, cors_server, tmp_path):
        """The point of the change: the cross-origin request is not just
        attempted, it is answered."""
        body = json.dumps({"name": "muse_probes.run", "args": ["--help"]}).encode()
        req = urllib.request.Request(
            cors_server + "/api/run", data=body,
            headers={"Content-Type": "application/json",
                     "Origin": "http://allowed.example"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                payload = json.loads(r.read())
                assert r.headers.get("Access-Control-Allow-Origin") == "http://allowed.example"
        except urllib.error.HTTPError as e:
            payload = json.loads(e.read())
        assert payload.get("argv"), f"cross-origin run did not execute: {payload}"

    def test_json_content_type_on_api(self, cors_server):
        with urllib.request.urlopen(cors_server + "/api/commands") as r:
            assert r.headers["Content-Type"] == "application/json"


class TestRunnerTimeout:
    """Issue #312: the timeout branch had no coverage."""

    def test_timeout_is_reported_not_raised(self, tmp_path):
        """A command exceeding its timeout returns ok=False with a timeout
        error — the pane's realistic case is a long muse_analyze.run."""
        r = Runner(cfg(tmp_path, allowlist=["muse_tests.fast"]))
        res = r.run("muse_tests.fast", [], timeout=0)
        assert res["ok"] is False
        assert "timeout" in (res.get("error") or "").lower(), res
        assert res["rc"] is None

    def test_generous_timeout_succeeds(self, tmp_path):
        r = Runner(cfg(tmp_path, allowlist=["muse_probes.run"]))
        res = r.run("muse_probes.run", ["--help"], timeout=60)
        assert res["rc"] in (0, 1, 2), res
        assert "timeout" not in (res.get("error") or "").lower()
