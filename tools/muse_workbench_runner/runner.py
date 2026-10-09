"""Core runner: config parse, allow-list check, subprocess exec."""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "workbench.config.json"

# Command name → argv template (relative to repo root)
COMMANDS = {
    "muse_seed.validate": ["python3", "tools/muse_seed_cli/cli.py", "validate"],
    "muse_seed.create": ["python3", "tools/muse_seed/cli.py", "create"],
    "muse_probes.run": ["python3", "tools/muse_probes/cli.py"],
    "muse_grow.iterate": ["python3", "tools/muse_grow/cli.py"],
    "muse_play.render": ["python3", "tools/muse_play/__main__.py"],
    "muse_analyze.run": ["python3", "tools/muse_analyze/cli.py"],
    "muse_diff.run": ["python3", "tools/muse_diff/cli.py"],
    "muse_tests.fast": ["bash", "tools/run_tests.sh"],
    "muse_generate.prompt": ["python3", "tools/muse_generate/cli.py", "prompt"],
    "muse_generate.mockup": ["python3", "tools/muse_grow/cli.py"],
    "muse_rehearse.dry-run": ["python3", "tools/muse_rehearse/cli.py", "dry-run"],
    "muse_rehearse.commit": ["python3", "tools/muse_rehearse/cli.py", "commit"],
}


class ConfigError(Exception):
    """Config missing/malformed — runner refuses everything."""


class Runner:
    def __init__(self, config_path=None):
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG
        self.allowed = set()
        self.enabled = False
        self.error = None
        self._load()

    def _load(self):
        try:
            raw = json.loads(self.config_path.read_text())
            runner_cmd = raw["runner"]
            allow = raw["allowlist"]
            if not isinstance(allow, list) or not allow:
                raise ConfigError("allowlist missing/empty")
            for name in allow:
                if name not in COMMANDS:
                    raise ConfigError(f"unknown command in allowlist: {name}")
            self.allowed = set(allow)
            self.enabled = raw.get("prompt_enabled", True)
            self.error = None
        except (OSError, json.JSONDecodeError, KeyError, ConfigError) as e:
            self.allowed = set()
            self.enabled = False
            self.error = f"config invalid: {e}"

    @property
    def available(self):
        return sorted(self.allowed) if not self.error else []

    def run(self, name, args=(), timeout=120, env_prefix="", stdin_data=None):
        if self.error:
            return {
                "ok": False,
                "name": name,
                "error": f"runner disabled: {self.error}",
                "rc": None,
            }
        if name not in COMMANDS:
            return {"ok": False, "name": name, "error": "unknown command", "rc": 405}
        if name not in self.allowed:
            return {"ok": False, "name": name, "error": "not in allow-list", "rc": 405}
        # env_prefix is a shell-style "KEY=V ... " string the pane sends for
        # founder-gated flags (e.g. MUSE_L1_LIVE=1); bash resolves it — the
        # command list itself stays shell=False targets it never execs bash.
        if env_prefix and name.startswith("muse_"):
            argv = ["bash", "-c", env_prefix + " ".join(
                shlex.quote(a) for a in COMMANDS[name] + list(args))]
        else:
            argv = COMMANDS[name] + list(args)
        try:
            proc = subprocess.run(
                argv, cwd=REPO_ROOT, capture_output=True, text=True,
                timeout=timeout, shell=False, input=stdin_data,
            )
            return {
                "ok": proc.returncode == 0,
                "name": name,
                "argv": argv,
                "stdout": proc.stdout[-4000:],
                "stderr": proc.stderr[-4000:],
                "rc": proc.returncode,
            }
        except subprocess.TimeoutExpired as e:
            return {"ok": False, "name": name, "error": f"timeout after {timeout}s", "rc": None}
        except OSError as e:
            return {"ok": False, "name": name, "error": f"exec failed: {e}", "rc": None}
