#!/usr/bin/env python3
"""Minimal smoke tests for the codebase analyzer."""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.codebase_analyzer import CodebaseAnalyzer


def test_line_counting() -> None:
    """Verify that line counting returns the expected value."""
    print("Testing line counting...")
    test_file = Path("test_file.txt")
    test_file.write_text("\n".join([
        "Line 1",
        "Line 2",
        "Line 3",
        "Line 4",
        "Line 5",
    ]), encoding="utf-8")
    try:
        analyzer = CodebaseAnalyzer(".")
        line_counts = analyzer.count_lines_in_files([test_file])
        expected_lines = 5
        actual_lines = line_counts[str(test_file)]
        assert actual_lines == expected_lines, f"expected {expected_lines}, got {actual_lines}"
        print("Line counting works as expected.")
    finally:
        test_file.unlink(missing_ok=True)


def test_readme_detection() -> None:
    """Ensure README files are detected."""
    print("Testing README detection...")
    readme = Path("README.md")
    readme.write_text("# Test Project\nThis is a test README file.", encoding="utf-8")
    try:
        analyzer = CodebaseAnalyzer(".")
        has_readme, readme_files = analyzer.check_readme_exists(Path("."))
        assert has_readme, "README should have been detected"
        assert str(readme) in [str(f) for f in readme_files]
        print("README detection works as expected.")
    finally:
        readme.unlink(missing_ok=True)


def test_documentation_scoring() -> None:
    """Check documentation score increments for README and docs."""
    print("Testing documentation scoring...")
    readme = Path("README.md")
    readme.write_text("# Test Project\n" + ("x" * 2000), encoding="utf-8")
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    api_doc = docs_dir / "api.md"
    api_doc.write_text("# API Documentation\nThis is API documentation.", encoding="utf-8")
    try:
        analyzer = CodebaseAnalyzer(".")
        documentation = analyzer.analyze_documentation(Path("."))
        assert documentation["documentation_score"] >= 75
        print(f"Documentation scoring returned {documentation['documentation_score']}/100.")
    finally:
        api_doc.unlink(missing_ok=True)
        with contextlib.suppress(OSError):
            docs_dir.rmdir()
        readme.unlink(missing_ok=True)


def main() -> int:
    print("Testing analysis tool fixes")
    print("=" * 40)
    tests = [test_line_counting, test_readme_detection, test_documentation_scoring]
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as exc:
            print(f"Assertion failed: {exc}")
        except Exception as exc:  # pragma: no cover - diagnostic output
            print(f"Unexpected error: {exc}")
        finally:
            print()
    print("=" * 40)
    print(f"Results: {passed}/{len(tests)} tests passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())
