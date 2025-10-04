from __future__ import annotations

"""Text based fallback search utilities used when LEANN vector search is unavailable."""

from pathlib import Path
from typing import Any, Dict, Iterable, List
import glob
import os


class TextFallbackSearcher:
    """Provides lightweight text search across the local repository."""

    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    async def search(self, index_name: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Perform a synchronous text search wrapped in an async interface."""
        try:
            results: List[Dict[str, Any]] = []
            query_lower = query.lower()

            for directory in self._candidate_directories(index_name):
                for file_path in self._scan_directory(directory):
                    match = self._match_file(file_path, query_lower)
                    if match:
                        results.append(match)
                    if len(results) >= top_k * 2:
                        break
                if len(results) >= top_k * 2:
                    break

            formatted = self._format_results(results, query_lower, top_k)
            return {
                "status": "success",
                "query": query,
                "results": formatted or "No matches found.",
                "top_k": top_k,
                "index": index_name,
                "method": "text_fallback",
                "note": "Using text search fallback (vector search unavailable)",
            }
        except Exception as exc:  # pragma: no cover - defensive
            return {"status": "error", "error": f"Failed text search fallback: {exc}"}

    def _candidate_directories(self, index_name: str) -> Iterable[Path]:
        if index_name == "agent-code":
            for name in ("src", "tests", "docs"):
                directory = self._project_root / name
                if directory.exists():
                    yield directory
        else:
            yield self._project_root

    def _scan_directory(self, directory: Path) -> Iterable[Path]:
        extensions = ["*.py", "*.md", "*.txt", "*.json", "*.yaml", "*.yml"]
        for pattern in extensions:
            search_pattern = str(directory / pattern) if pattern.startswith("*") else str(directory / f"**/{pattern}")
            for path in glob.glob(search_pattern, recursive=True):
                if os.path.isfile(path):
                    yield Path(path)

    def _match_file(self, file_path: Path, query_lower: str) -> Dict[str, Any] | None:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return None

        lines = content.split("\n")
        for index, line in enumerate(lines):
            if query_lower in line.lower():
                start = max(0, index - 2)
                end = min(len(lines), index + 3)
                context_lines = []
                for position in range(start, end):
                    marker = ">" if position == index else " "
                    context_lines.append(f"{marker} {lines[position]}")
                return {
                    "file": str(file_path),
                    "line": index + 1,
                    "content": line.strip(),
                    "context": "\n".join(context_lines),
                }
        return None

    def _format_results(self, results: List[Dict[str, Any]], query_lower: str, top_k: int) -> str:
        results.sort(
            key=lambda item: (
                query_lower not in Path(item["file"]).name.lower(),
                -item["content"].lower().count(query_lower),
            )
        )

        lines: List[str] = []
        for idx, result in enumerate(results[:top_k]):
            filename = Path(result["file"]).name
            lines.append(f"**{idx + 1}. {filename} (line {result['line']})**")
            lines.append(f"   {result['content']}")
            if result.get("context"):
                snippet = result["context"][:100]
                lines.append(f"   Context: {snippet}...")
            lines.append("")
        return "\n".join(lines)
