from __future__ import annotations

"""Environment detection utilities for the LEANN plugin."""

from dataclasses import dataclass
import subprocess
from typing import Optional


@dataclass
class LeannEnvironment:
    """Represents the available LEANN execution environments."""

    leann_command: str = "leann"
    wsl_available: bool = False
    wsl_leann_available: bool = False
    windows_leann_available: bool = False
    wsl_leann_path: Optional[str] = None

    @property
    def available(self) -> bool:
        """Return True when any LEANN backend looks usable."""
        return self.windows_leann_available or self.wsl_leann_available or self.wsl_available

    @property
    def preferred_backend(self) -> str:
        """Return the preferred backend identifier."""
        if self.wsl_available and (self.wsl_leann_available or self.wsl_leann_path):
            return "wsl"
        if self.windows_leann_available:
            return "windows"
        return "none"


def detect_environment(leann_command: str = "leann") -> LeannEnvironment:
    """Probe the current machine and return LEANN environment details."""
    env = LeannEnvironment(leann_command=leann_command)

    # Probe Windows Subsystem for Linux support first.
    try:
        wsl_result = subprocess.run(
            ["wsl", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if wsl_result.returncode == 0:
            env.wsl_available = True

            # Candidate locations for the LEANN binary inside WSL.
            candidate_paths = [
                "/home/username/.local/bin/leann",
                "/usr/local/bin/leann",
                "leann",
            ]

            for candidate in candidate_paths:
                try:
                    if candidate == "leann":
                        check_cmd = ["wsl", "which", "leann"]
                    else:
                        check_cmd = ["wsl", "bash", "-c", f"test -x {candidate} && echo exists"]

                    check_result = subprocess.run(
                        check_cmd,
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if check_result.returncode == 0:
                        env.wsl_leann_available = True
                        env.wsl_leann_path = candidate if candidate != "leann" else "leann"
                        break
                except subprocess.SubprocessError:
                    continue
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    # Probe native Windows binary.
    try:
        win_result = subprocess.run(
            [leann_command, "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        env.windows_leann_available = win_result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        env.windows_leann_available = False

    return env
