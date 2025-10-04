from __future__ import annotations

"""Command execution helpers for interacting with the LEANN CLI."""

from typing import Any, Dict, List, Optional
import shlex
import subprocess

from .codebase import discover_project_root
from .environment import LeannEnvironment


class LeannCommandRunner:
    """Wrapper around the LEANN CLI with WSL aware execution."""

    def __init__(self, environment: LeannEnvironment, default_wsl_path: str = "/home/username/.local/bin/leann") -> None:
        self._environment = environment
        self._default_wsl_path = default_wsl_path

    def run(self, args: List[str], input_data: Optional[str] = None) -> Dict[str, Any]:
        """Execute a LEANN command and normalise the response."""
        work_dir = discover_project_root()
        using_wsl = self._should_use_wsl()

        command = self._build_wsl_command(args, work_dir) if using_wsl else [self._environment.leann_command, *args]

        try:
            result = subprocess.run(
                command,
                input=input_data,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                cwd=str(work_dir),
            )
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "LEANN command timed out", "command": " ".join(args)}
        except Exception as exc:  # pragma: no cover - defensive
            return {"status": "error", "error": f"Failed to execute LEANN command: {exc}", "command": " ".join(args)}

        if result.returncode != 0:
            return {
                "status": "error",
                "error": f"LEANN command failed: {result.stderr}",
                "command": " ".join(command),
                "using_wsl": using_wsl,
            }

        return {
            "status": "success",
            "output": result.stdout.strip(),
            "error": result.stderr.strip() or None,
            "using_wsl": using_wsl,
        }

    def _should_use_wsl(self) -> bool:
        """Determine whether WSL should handle the command."""
        env = self._environment
        if env.wsl_available:
            return True
        if env.wsl_leann_available and not env.windows_leann_available:
            return True
        return False

    def _build_wsl_command(self, args: List[str], work_dir) -> List[str]:
        """Build the WSL command invocation with path conversion."""
        leann_exec = self._environment.wsl_leann_path or self._default_wsl_path
        wsl_args = [self._to_wsl_path(arg) for arg in args]
        command_parts = [leann_exec, *[shlex.quote(arg) for arg in wsl_args]]
        command_str = " ".join(part for part in command_parts if part)
        wsl_work_dir = self._to_wsl_path(str(work_dir))
        return ["wsl", "bash", "-c", f"cd {wsl_work_dir} && {command_str}"]

    @staticmethod
    def _to_wsl_path(value: str) -> str:
        """Convert Windows paths into their WSL representation when needed."""
        if not isinstance(value, str):
            value = str(value)
        if len(value) >= 2 and value[1] == ":" and value[0].isalpha():
            path = value.replace("\\", "/")
            drive = path[0].lower()
            remainder = path[2:]
            return f"/mnt/{drive}{remainder}"
        return value
