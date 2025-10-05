"""Utilities for loading custom agent instructions."""

from pathlib import Path


DEFAULT_RULES_PATH = Path(".clinerules")


def load_custom_instructions(rules_path: Path | str = DEFAULT_RULES_PATH) -> str:
    """Load behavioral overrides from the CLI rules file.

    Returns an empty string if the file does not exist or cannot be read.
    """
    path = Path(rules_path)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Warning: Could not load {path}: {exc}")
        return ""
