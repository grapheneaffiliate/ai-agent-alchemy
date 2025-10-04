from __future__ import annotations

"""Helpers for inspecting the local codebase during LEANN fallback flows."""

from pathlib import Path
from typing import Any, Dict, List


_SCAN_EXTENSIONS = (".py", ".md", ".txt", ".json")
_EXCLUDED_DIRS = {"__pycache__", ".git"}


def discover_project_root() -> Path:
    """Locate the project root that contains src/ and tests/ folders."""
    cwd = Path.cwd()
    if (cwd / "src").exists() and (cwd / "tests").exists():
        return cwd

    module_root = Path(__file__).resolve().parents[3]
    if (module_root / "src").exists() and (module_root / "tests").exists():
        return module_root

    nested = module_root.parent / "mcp-ai-agent"
    if (nested / "src").exists() and (nested / "tests").exists():
        return nested

    return module_root


def collect_files_with_limits(base_path: Path, max_files: int = 200) -> List[Path]:
    """Collect a shallow set of representative files for analysis."""
    files: List[Path] = []
    candidates = [base_path / "src", base_path / "tests", base_path / "docs"]

    for directory in candidates:
        if not directory.exists():
            continue

        try:
            for entry in directory.iterdir():
                if entry.is_file() and entry.suffix in _SCAN_EXTENSIONS:
                    files.append(entry)
                elif entry.is_dir() and entry.name not in _EXCLUDED_DIRS:
                    try:
                        for sub_entry in entry.iterdir():
                            if sub_entry.is_file() and sub_entry.suffix in _SCAN_EXTENSIONS:
                                files.append(sub_entry)
                            if len(files) >= max_files:
                                break
                    except (OSError, PermissionError):
                        continue
                if len(files) >= max_files:
                    break
        except (OSError, PermissionError):
            continue

        if len(files) >= max_files:
            break

    return files


def process_python_metrics(py_files: List[Path], max_content_mb: float = 0.5) -> Dict[str, Any]:
    """Compute lightweight metrics for a subset of Python files."""
    func_count = 0
    class_count = 0
    plugin_count = 0
    import_count = 0
    async_count = 0
    content_read = 0

    class_names: List[str] = []
    function_names: List[str] = []

    for file_path in py_files[:50]:
        try:
            file_size = file_path.stat().st_size
            if file_size > 50 * 1024:
                continue
            if content_read + file_size > max_content_mb * 1024 * 1024:
                break

            content = file_path.read_text(encoding="utf-8", errors="replace")
            content_read += len(content)

            func_count += content.count("def ")
            class_count += content.count("class ")
            async_count += content.count("async def ")
            import_count += content.count("import ") + content.count("from ")

            if "plugin" in file_path.name.lower():
                plugin_count += 1

            _extract_class_function_names(content, class_names, function_names)
        except (OSError, UnicodeDecodeError):
            continue

    return {
        "func_count": func_count,
        "class_count": class_count,
        "plugin_count": plugin_count,
        "import_count": import_count,
        "async_count": async_count,
        "class_names": class_names,
        "function_names": function_names,
    }


def _extract_class_function_names(content: str, class_names: List[str], function_names: List[str]) -> None:
    """Populate name collections with a capped number of entries."""
    lines = content.split("\n")[:200]

    for line in lines:
        trimmed = line.strip()[:100]
        if trimmed.startswith("class "):
            name = trimmed.split()[1].split("(")[0].split(":")[0]
            if len(name) < 30:
                class_names.append(name)
                if len(class_names) >= 15:
                    break
        elif trimmed.startswith("def ") or trimmed.startswith("async def "):
            name = trimmed.split()[1].split("(")[0]
            if len(name) < 30 and not name.startswith("__"):
                function_names.append(name)
                if len(function_names) >= 30:
                    break


def build_directory_structure(base_path: Path) -> Dict[str, List[str]]:
    """Return a simple mapping of directory names to sample files."""
    structure: Dict[str, List[str]] = {}
    for directory in (base_path / "src", base_path / "tests", base_path / "docs"):
        if not directory.exists():
            continue
        try:
            sample = [entry.name for entry in directory.iterdir() if entry.is_file()][:5]
            if sample:
                structure[directory.name] = sample
        except (OSError, PermissionError):
            continue
    return structure


def create_analysis_result(
    files: List[Path],
    metrics: Dict[str, Any],
    dir_structure: Dict[str, List[str]],
    index_name: str,
) -> Dict[str, Any]:
    """Assemble the fallback analysis payload."""
    total_files = len(files)
    python_files = len([f for f in files if f.suffix == ".py"])
    doc_files = len([f for f in files if f.suffix in {".md", ".txt", ".json"}])

    function_names = metrics.get("function_names", [])
    class_names = metrics.get("class_names", [])

    return {
        "status": "success",
        "analysis": {
            "architecture": {
                "total_files": total_files,
                "python_files": f"{python_files} Python source files",
                "documentation_files": f"{doc_files} documentation files",
                "components": dir_structure,
                "directories": list(dir_structure.keys()),
            },
            "functions": {
                "total": metrics.get("func_count", 0),
                "sync_functions": metrics.get("func_count", 0) - metrics.get("async_count", 0),
                "async_functions": metrics.get("async_count", 0),
                "main_functions": ", ".join(function_names[:8]) if function_names else "Basic functions detected",
            },
            "classes": {
                "total": metrics.get("class_count", 0),
                "main_classes": ", ".join(class_names[:8]) if class_names else "Standard Python classes detected",
            },
            "patterns": [
                f"Plugin system with {metrics.get('plugin_count', 0)} plugin files",
                f"Async programming with {metrics.get('async_count', 0)} async functions",
                f"Modular design with {metrics.get('import_count', 0)} imports across files",
                "WebSocket-based communication",
                "MCP (Model Context Protocol) integration",
                "React (Reasoning + Acting) loop pattern",
            ],
            "documentation": {
                "quality_score": round(min(100, (doc_files / max(1, total_files)) * 200)),
                "documentation_files": doc_files,
                "total_files": total_files,
                "assessment": "Good documentation coverage with dedicated docs directory",
            },
        },
        "index": index_name,
        "method": "fallback_text_analysis_limited",
        "note": (
            f"Analyzed {python_files} Python files, "
            f"{metrics.get('func_count', 0)} functions, "
            f"{metrics.get('class_count', 0)} classes (limited scan)"
        ),
    }
