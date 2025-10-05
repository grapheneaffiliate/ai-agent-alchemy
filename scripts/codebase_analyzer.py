#!/usr/bin/env python3
"""
Codebase Analysis Tool - Fixed Version

This tool provides accurate codebase metrics including:
- Line counting across all files
- README detection and analysis
- Documentation scoring
- Code quality metrics

Fixes the bugs in the previous analysis tool that was:
- Returning 0 lines incorrectly
- Not finding existing README files
- Giving contradictory documentation scores
"""

import os
import json
import argparse
import tomllib
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime


class CodebaseAnalyzer:
    """Accurate codebase analysis tool."""

    def __init__(self, project_path: str):
        self.project_path = Path(project_path).resolve()
        self.analysis_results = {}

    def count_lines_in_files(self, file_paths: List[Path]) -> Dict[str, int]:
        """Accurately count lines in files."""
        line_counts = {}

        for file_path in file_paths:
            try:
                if file_path.suffix == '.pyc':
                    line_counts[str(file_path)] = 0
                    continue
                if file_path.is_file() and file_path.exists():
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Count actual lines, not just line endings
                        lines = content.splitlines()
                        line_counts[str(file_path)] = len(lines)
                else:
                    line_counts[str(file_path)] = 0
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")
                line_counts[str(file_path)] = 0

        return line_counts

    def check_readme_exists(self, project_path: Path) -> Tuple[bool, List[Path]]:
        """Check if README files exist and return their paths."""
        readme_files = []

        # Common README file names
        readme_names = [
            'README.md', 'README.txt', 'README.rst', 'README',
            'readme.md', 'readme.txt', 'readme.rst', 'readme'
        ]

        for readme_name in readme_names:
            readme_path = project_path / readme_name
            if readme_path.exists():
                readme_files.append(readme_path)

        return len(readme_files) > 0, readme_files

    def parse_dependencies(self, project_path: Path) -> Dict[str, Any]:
        """Parse dependencies from pyproject.toml and other dependency files."""
        dependencies = {
            'runtime': [],
            'optional': {},
            'total_runtime': 0,
            'total_optional': 0
        }

        # Check for pyproject.toml
        pyproject_path = project_path / 'pyproject.toml'
        if pyproject_path.exists():
            try:
                with open(pyproject_path, 'rb') as f:
                    pyproject_data = tomllib.load(f)

                # Parse runtime dependencies
                if 'project' in pyproject_data and 'dependencies' in pyproject_data['project']:
                    dependencies['runtime'] = pyproject_data['project']['dependencies']
                    dependencies['total_runtime'] = len(pyproject_data['project']['dependencies'])

                # Parse optional dependencies
                if 'project' in pyproject_data and 'optional-dependencies' in pyproject_data['project']:
                    dependencies['optional'] = pyproject_data['project']['optional-dependencies']
                    dependencies['total_optional'] = sum(len(deps) for deps in pyproject_data['project']['optional-dependencies'].values())

            except Exception as e:
                print(f"Warning: Could not parse pyproject.toml: {e}")

        return dependencies

    def analyze_documentation(self, project_path: Path) -> Dict[str, Any]:
        """Analyze documentation quality and coverage."""
        doc_score = 0
        has_readme = False
        readme_files = []
        doc_files = []
        has_api_docs = False

        # Check for README
        has_readme, readme_files = self.check_readme_exists(project_path)

        if has_readme:
            doc_score += 30

            # Analyze README quality
            for readme_file in readme_files:
                try:
                    content = readme_file.read_text(encoding='utf-8', errors='ignore')
                    if len(content) > 1000:  # Substantial documentation
                        doc_score += 25
                    if len(content) > 5000:  # Very comprehensive
                        doc_score += 15
                except:
                    pass

        # Look for documentation files
        docs_dir = project_path / 'docs'
        if docs_dir.exists():
            for doc_file in docs_dir.rglob('*'):
                if doc_file.is_file() and doc_file.suffix in ['.md', '.rst', '.txt']:
                    doc_files.append(doc_file)
                    if 'api' in doc_file.name.lower() or 'api' in doc_file.read_text(encoding='utf-8', errors='ignore').lower():
                        has_api_docs = True

        if has_api_docs:
            doc_score += 20

        # Look for docstrings in Python files
        py_files = list(project_path.rglob('*.py'))
        files_with_docstrings = 0

        for py_file in py_files[:50]:  # Sample first 50 files
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                if '"""' in content or "'''" in content:
                    files_with_docstrings += 1
            except:
                pass

        if py_files:
            docstring_ratio = files_with_docstrings / len(py_files)
            if docstring_ratio > 0.7:  # 70% of files have docstrings
                doc_score += 10

        return {
            'documentation_score': min(doc_score, 100),
            'has_readme': has_readme,
            'readme_files': [str(f) for f in readme_files],
            'documentation_files': [str(f) for f in doc_files],
            'files_with_docstrings': files_with_docstrings,
            'total_python_files': len(py_files),
            'docstring_coverage': files_with_docstrings / max(len(py_files), 1) * 100
        }

    def analyze_codebase(self) -> Dict[str, Any]:
        """Perform comprehensive codebase analysis."""
        print(f"Analyzing codebase at: {self.project_path}")

        # Get all files
        all_files = []
        for root_dir in [self.project_path, self.project_path / "src", self.project_path / "tests", self.project_path / "docs"]:
            if root_dir.exists():
                try:
                    for file_path in root_dir.rglob("*"):
                        if (
                            file_path.is_file()
                            and '__pycache__' not in file_path.parts
                            and file_path.suffix != '.pyc'
                            and not any(part.startswith('.') for part in file_path.parts)
                        ):
                            all_files.append(file_path)
                except (OSError, PermissionError):
                    continue

        print(f"Found {len(all_files)} files to analyze")

        # Count lines in all files
        line_counts = self.count_lines_in_files(all_files)
        total_lines = sum(line_counts.values())

        # Analyze by file type
        file_types = {}
        for file_path, lines in line_counts.items():
            suffix = Path(file_path).suffix or 'no_extension'
            if suffix not in file_types:
                file_types[suffix] = {'count': 0, 'lines': 0}
            file_types[suffix]['count'] += 1
            file_types[suffix]['lines'] += lines

        # Analyze documentation
        documentation = self.analyze_documentation(self.project_path)

        # Parse dependencies
        dependencies = self.parse_dependencies(self.project_path)

        # Calculate code quality metrics
        py_files = [f for f in all_files if f.suffix == '.py']
        total_classes = sum(1 for f in py_files for content in [f.read_text(encoding='utf-8', errors='ignore')] for _ in [content.count('class ')])

        # Generate analysis results
        analysis = {
            'analysis_date': datetime.now().isoformat(),
            'project_path': str(self.project_path),
            'summary': {
                'total_files': len(all_files),
                'total_lines': total_lines,
                'total_classes': total_classes,
                'python_files': len(py_files),
                'documentation_score': documentation['documentation_score'],
                'has_readme': documentation['has_readme'],
                'runtime_dependencies': dependencies['total_runtime'],
                'optional_dependencies': dependencies['total_optional']
            },
            'file_types': file_types,
            'line_counts': line_counts,
            'documentation': documentation,
            'dependencies': dependencies,
            'largest_files': sorted(
                [(str(f), lines) for f, lines in line_counts.items() if lines > 0],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

        self.analysis_results = analysis
        return analysis

    def print_summary(self):
        """Print a human-readable summary of the analysis."""
        if not self.analysis_results:
            print("No analysis results available. Run analyze_codebase() first.")
            return

        results = self.analysis_results
        summary = results['summary']
        print()
        print("=" * 60)
        print("CODEBASE ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Analysis Date: {results['analysis_date']}")
        print(f"Project Path: {results['project_path']}")
        print()
        print("SUMMARY METRICS:")
        print(f"  - Total Files: {summary['total_files']:,}")
        print(f"  - Total Lines: {summary['total_lines']:,}")
        print(f"  - Total Classes: {summary['total_classes']:,}")
        print(f"  - Python Files: {summary['python_files']:,}")
        print()
        print("DOCUMENTATION:")
        print(f"  - Documentation Score: {summary['documentation_score']}/100")
        print(f"  - README Present: {'yes' if summary['has_readme'] else 'no'}")
        readmes = results['documentation']['readme_files']
        if readmes:
            names = ", ".join(Path(f).name for f in readmes)
            print(f"  - README Files: {names}")
        print()
        print("DEPENDENCIES:")
        print(f"  - Runtime Dependencies: {summary['runtime_dependencies']}")
        print(f"  - Optional Dependencies: {summary['optional_dependencies']}")
        if summary['runtime_dependencies'] > 0:
            runtime_deps = results['dependencies']['runtime'][:3]  # Show first 3
            print(f"  - Top Runtime Deps: {', '.join(runtime_deps)}")
        print()
        print("LINES BY EXTENSION:")
        for ext, stats in sorted(results['file_types'].items(), key=lambda x: x[1]['lines'], reverse=True):
            if stats['lines'] > 0:
                label = ext or 'no extension'
                print(f"  - {label}: {stats['count']} files, {stats['lines']:,} lines")
        print()
        largest = results['largest_files']
        if largest:
            print("LARGEST FILES:")
            for file_path, lines in largest[:5]:
                print(f"  - {Path(file_path).name}: {lines:,} lines")
        print("=" * 60)

    def save_results(self, output_path: str = None):
        """Save analysis results to JSON file."""
        if not self.analysis_results:
            print("No analysis results to save.")
            return

        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"codebase_analysis_{timestamp}.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)

        print(f"Analysis results saved to: {output_path}")

def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(description='Analyze codebase metrics and documentation')
    parser.add_argument('project_path', nargs='?', default='.',
                       help='Path to project directory (default: current directory)')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--summary-only', '-s', action='store_true',
                       help='Print only summary, no detailed output')

    args = parser.parse_args()

    # Resolve project path
    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        print(f"Error: Project path '{project_path}' does not exist")
        return 1

    # Run analysis
    analyzer = CodebaseAnalyzer(str(project_path))
    results = analyzer.analyze_codebase()

    # Output results
    if args.summary_only:
        analyzer.print_summary()
    else:
        analyzer.print_summary()

        # Save to file if requested
        if args.output:
            analyzer.save_results(args.output)

    return 0


if __name__ == "__main__":
    exit(main())
