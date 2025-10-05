from __future__ import annotations

"""Service wrapper around the LEANN CLI for index management."""

import functools
from typing import Any, Dict, List, Optional

from .command_runner import LeannCommandRunner
from .environment import LeannEnvironment
from .fallback import TextFallbackSearcher


class LeannIndexService:
    """Provide high-level helpers for interacting with the LEANN CLI."""

    def __init__(
        self,
        environment: LeannEnvironment,
        command_runner: LeannCommandRunner,
        text_fallback: TextFallbackSearcher,
    ) -> None:
        self._environment = environment
        self._command_runner = command_runner
        self._text_fallback = text_fallback
        self._availability_override: Optional[bool] = None

    @property
    def available(self) -> bool:
        """Expose LEANN availability checks in a single place."""
        if self._availability_override is not None:
            return self._availability_override
        return self._environment.available

    def set_availability_override(self, value: Optional[bool]) -> None:
        """Allow callers to override availability (used in tests/fallbacks)."""
        self._availability_override = value

    @property
    def preferred_backend(self) -> str:
        """Mirror the environment's preferred backend logic."""
        if self._environment.wsl_available and (
            self._environment.wsl_leann_available or self._environment.wsl_leann_path
        ):
            return "wsl"
        if self._environment.windows_leann_available:
            return "windows"
        return "none"

    @functools.cached_property
    def supported_backends(self) -> List[str]:
        """Inspect the CLI for available vector backends."""
        result = self._command_runner.run(["backends", "--list"])
        if result.get("status") == "success":
            backends: List[str] = []
            for line in result.get("output", "").splitlines():
                if line.strip() and not line.startswith(("Available", "Supported")):
                    token = line.strip().split()[0]
                    if token and token.lower() not in backends:
                        backends.append(token.lower())
            if backends:
                return backends
        return ["faiss", "hnsw"]

    async def build_index(self, index_name: str, docs: List[str], force: bool = False) -> Dict[str, Any]:
        """Build an index from the supplied documents."""
        if not self.available:
            return {
                "status": "error",
                "error": "LEANN is not installed or not available on this system",
                "note": "LEANN backend may not support Windows. Consider using WSL2 for full functionality.",
            }

        args = ["build", index_name]
        if force:
            args.append("--force")
        for doc_path in docs:
            args.extend(["--docs", doc_path])

        result = self._command_runner.run(args)
        if result.get("status") == "success":
            return {
                "status": "success",
                "message": f"Index '{index_name}' build completed",
                "index": index_name,
                "docs": docs,
                "command_used": result.get("command", ""),
                "output": result.get("output", ""),
            }

        error_message = result.get("error", "Failed to build index")
        if "Backend 'hnsw' not found" in error_message:
            error_message += "; install `faiss-cpu` or enable WSL to use HNSW backends"

        return {
            "status": "error",
            "error": error_message,
            "command_used": result.get("command", ""),
            "details": result.get("output") or error_message,
        }

    async def search(self, index_name: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Run a semantic search with fallback to text scanning."""
        if not self.available:
            return await self._text_fallback.search(index_name, query, top_k)

        args = ["search", index_name, query, "--top-k", str(top_k)]
        result = self._command_runner.run(args)
        if result.get("status") == "success":
            return {
                "status": "success",
                "query": query,
                "results": result.get("output", ""),
                "top_k": top_k,
                "index": index_name,
            }

        return await self._text_fallback.search(index_name, query, top_k)

    async def ask(self, index_name: str, question: str, top_k: int = 3) -> Dict[str, Any]:
        """Ask questions about an index, falling back when unavailable."""
        if not self.available:
            return {
                "status": "error",
                "error": "LEANN is not installed or not available on this system",
                "note": "LEANN requires LLM configuration for question answering.",
            }

        args = ["ask", index_name, "--interactive", "--top-k", str(top_k)]
        result = self._command_runner.run(args, input_data=question)
        if result.get("status") == "success":
            return {
                "status": "success",
                "question": question,
                "answer": result.get("output", ""),
                "top_k": top_k,
                "index": index_name,
            }
        return result

    async def list_indexes(self) -> Dict[str, Any]:
        """List available indexes, returning a friendly response on failure."""
        result = self._command_runner.run(["list"])
        if result.get("status") == "success":
            return {
                "status": "success",
                "indexes": result.get("output", ""),
                "available": self.available,
            }
        return {
            "status": "success",
            "indexes": "No indexes found or LEANN not fully available",
            "available": self.available,
        }
