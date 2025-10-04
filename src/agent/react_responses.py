"""Formatting helpers for LEANN analysis responses used within the ReAct loop."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List


def _add_section(parts: List[str], heading: str, body: Iterable[str] | None = None) -> None:
    """Append a markdown section with an optional body list."""
    parts.append(heading)
    if body:
        parts.extend(body)
    parts.append("")


def format_health_analysis_response(analysis_data: Dict[str, Any]) -> str:
    """Format health analysis response."""
    response_parts: List[str] = ["# Codebase Health Analysis", ""]

    health_report: Dict[str, Any] = analysis_data.get('health_report', {})
    overall_health = health_report.get('overall_health_score', 0.0)
    response_parts.append(f"## ✅ Overall Health Score: **{overall_health:.1f}/100**")

    health_status = health_report.get('health_status', 'unknown')
    status_lookup = {
        'excellent': "**Status**: 🟢 Excellent - Codebase is in outstanding health!",
        'good': "**Status**: 🟢 Good - Codebase is healthy with room for minor improvements.",
        'fair': "**Status**: 🟠 Fair - Some health concerns need attention.",
    }
    response_parts.append(status_lookup.get(health_status, "**Status**: 🔴 Needs Attention - Critical health issues require immediate focus."))
    response_parts.append("")

    dimension_scores: Dict[str, float] = health_report.get('dimension_scores', {})
    if dimension_scores:
        _add_section(
            response_parts,
            "## 📊 Health Dimensions",
            [f"- **{dimension.replace('_', ' ').title()}**: {score:.1f}/100" for dimension, score in dimension_scores.items()],
        )

    strengths = health_report.get('strengths', [])
    if strengths:
        _add_section(response_parts, "## 💪 Strengths", [f"- ✅ {item}" for item in strengths])

    critical_issues = health_report.get('critical_issues', [])
    if critical_issues:
        _add_section(response_parts, "## 🚨 Critical Issues", [f"- ❗ {issue}" for issue in critical_issues])

    recommendations = health_report.get('recommendations', [])
    if recommendations:
        _add_section(
            response_parts,
            "## 🛠️ Health Recommendations",
            [f"{idx}. {recommendation}" for idx, recommendation in enumerate(recommendations, start=1)],
        )

    return "\n".join(response_parts).strip()


def format_comprehensive_analysis_response(analysis_data: Dict[str, Any]) -> str:
    """Format comprehensive analysis response with real metrics."""
    response_parts: List[str] = [
        "# Comprehensive Codebase Analysis Report",
        "",
        "## 🧠 Detailed Assessment of Current State",
        "In-depth analysis of codebase structure, quality, and characteristics.",
        "",
        f"*Analysis performed on: {datetime.now():%Y-%m-%d %H:%M:%S}*",
        "",
    ]

    project_overview: Dict[str, Any] = analysis_data.get('project_overview', {})
    overview_lines = [
        f"- **Total Files**: {project_overview.get('total_files', 0)}",
        f"- **Python Files**: {project_overview.get('python_files', 0)}",
        f"- **Test Files**: {project_overview.get('test_files', 0)}",
        f"- **Documentation Files**: {project_overview.get('documentation_files', 0)}",
        f"- **Source Files**: {project_overview.get('source_files', 0)}",
        f"- **Plugin Files**: {project_overview.get('plugin_files', 0)}",
    ]
    main_dirs = project_overview.get('main_directories', [])
    if main_dirs:
        overview_lines.append(f"- **Main Directories**: {', '.join(main_dirs[:5])}")
    test_ratio = project_overview.get('test_coverage_ratio', 0) * 100
    overview_lines.append(f"- **Test Coverage**: {test_ratio:.1f}%")
    _add_section(response_parts, "## 🗂️ Project Structure Analysis", overview_lines)

    code_quality: Dict[str, Any] = analysis_data.get('code_quality', {})
    if code_quality:
        quality_lines = [
            f"- **Complexity Score**: {code_quality.get('complexity_score', 0):.1f}/100",
            f"- **Total Functions**: {code_quality.get('total_functions', 0)}",
            f"- **Average Functions per File**: {code_quality.get('avg_functions_per_file', 0):.1f}",
            f"- **Average Lines per File**: {code_quality.get('avg_lines_per_file', 0):.1f}",
        ]
        _add_section(response_parts, "## 🧮 Code Quality Metrics", quality_lines)

    performance_analysis: Dict[str, Any] = analysis_data.get('performance', {})
    if performance_analysis:
        performance_lines = []
        indicators = performance_analysis.get('performance_indicators', [])
        if indicators:
            performance_lines.append("- **Performance Indicators**:")
            performance_lines.extend([f"  - ⚡ {indicator}" for indicator in indicators])
        bottlenecks = performance_analysis.get('bottlenecks', [])
        if bottlenecks:
            performance_lines.append("- **Bottlenecks**:")
            performance_lines.extend([f"  - 🚫 {item}" for item in bottlenecks])
        _add_section(response_parts, "## ⚙️ Performance Indicators", performance_lines or ["- No performance data available."])

    recommendations = analysis_data.get('recommendations', [])
    if recommendations:
        _add_section(
            response_parts,
            "## 🗺️ Recommended Next Steps",
            [f"{idx}. {item}" for idx, item in enumerate(recommendations, start=1)],
        )

    findings = analysis_data.get('key_findings', [])
    if findings:
        _add_section(response_parts, "## 🔍 Key Findings", [f"- {finding}" for finding in findings])

    response_parts.append("---")
    response_parts.append(
        "*This analysis provides a snapshot of the current codebase state. For improvement recommendations, use the 'improve yourself' command.*"
    )

    return "\n".join(response_parts).strip()


def format_enhancement_plan_response(analysis_data: Dict[str, Any]) -> str:
    """Format enhancement plan response."""
    response_parts: List[str] = ["# Codebase Enhancement Plan", ""]

    enhancement_plan: Dict[str, Any] = analysis_data.get('enhancement_plan', {})

    response_parts.append("## 🚀 Enhancement Strategy")
    response_parts.append(
        "Comprehensive roadmap for improving codebase quality, maintainability, and performance."
    )
    response_parts.append("")

    sections = [
        ("## ⚡ Immediate Actions (Next 1-2 days)", enhancement_plan.get('immediate_actions', [])),
        ("## 🗓️ Short-term Improvements (1-2 weeks)", enhancement_plan.get('short_term_improvements', [])),
        ("## 🧱 Medium-term Enhancements (1-3 months)", enhancement_plan.get('medium_term_enhancements', [])),
        ("## 🌠 Long-term Vision (3-6 months)", enhancement_plan.get('long_term_vision', [])),
    ]
    for heading, items in sections:
        if items:
            _add_section(response_parts, heading, [f"{idx}. {value}" for idx, value in enumerate(items, start=1)])

    resources = enhancement_plan.get('resource_estimation', {})
    if resources:
        response_parts.append("## 📦 Resource Estimation")
        dev_time = resources.get('development_time', {})
        if dev_time:
            _add_section(response_parts, "### Development Time", [f"- **{phase.title()}**: {time}" for phase, time in dev_time.items()])
        team_size = resources.get('team_size', {})
        if team_size:
            _add_section(response_parts, "### Team Size", [f"- **{phase.title()}**: {size}" for phase, size in team_size.items()])
        skills = resources.get('skills_required', [])
        if skills:
            _add_section(response_parts, "### Required Skills", [f"- {skill}" for skill in skills])

    success_metrics = enhancement_plan.get('success_metrics', {})
    if success_metrics:
        response_parts.append("## 🏁 Success Metrics")
        quality_metrics = success_metrics.get('quality_metrics', {})
        if quality_metrics:
            _add_section(
                response_parts,
                "### Quality",
                [f"- {metric.replace('_', ' ').title()}: {target}" for metric, target in quality_metrics.items()],
            )

    return "\n".join(response_parts).strip()


def format_intelligence_analysis_response(analysis_data: Dict[str, Any]) -> str:
    """Format intelligence analysis response."""
    response_parts: List[str] = ["# Codebase Intelligence Analysis", ""]

    response_parts.append("## 🧭 Architectural Intelligence")
    response_parts.append("Deep analysis of codebase architecture, patterns, and intelligence.")
    response_parts.append("")

    overview = analysis_data.get('overview')
    if overview:
        response_parts.append(str(overview))
        response_parts.append("")

    method = analysis_data.get('method', 'unknown')
    response_parts.append("## 🧪 Analysis Method")
    response_parts.append(f"- **Technique**: {method.replace('_', ' ').title()}")
    response_parts.append("")

    project_overview: Dict[str, Any] = analysis_data.get('project_overview', {})
    if project_overview:
        directory_list = project_overview.get('main_directories', [])
        body = [
            f"- **Modules**: {len(directory_list)} main directories",
            f"- **Patterns**: {', '.join(directory_list)}" if directory_list else "- **Patterns**: Not detected",
        ]
        _add_section(response_parts, "## 🗺️ Architectural Structure", body)

    code_quality = analysis_data.get('code_quality', {})
    if code_quality:
        complexity = code_quality.get('complexity_score', 0)
        maintainability = 'High' if complexity > 80 else 'Medium' if complexity > 60 else 'Low'
        _add_section(
            response_parts,
            "## 🧠 Code Intelligence",
            [
                f"- **Maintainability**: {maintainability}",
                f"- **Architecture Quality**: {complexity:.1f}/100",
                f"- **Code Patterns**: {code_quality.get('total_functions', 0)} functions analysed",
            ],
        )

    performance = analysis_data.get('performance', {})
    if performance:
        indicators = performance.get('performance_indicators', [])
        body: List[str] = []
        if indicators:
            body.append("- **Design Patterns**:")
            body.extend([f"  - 🔍 {indicator}" for indicator in indicators])
        else:
            body.append("- **Design Patterns**: Standard architecture detected")
        _add_section(response_parts, "## ⚙️ Performance Architecture", body)

    architectural_patterns = analysis_data.get('architectural_patterns', [])
    if architectural_patterns:
        _add_section(response_parts, "## 🧱 Architectural Patterns", [f"- {pattern}" for pattern in architectural_patterns])

    next_steps = analysis_data.get('recommended_next_steps', [])
    if next_steps:
        _add_section(response_parts, "## 🛣️ Recommended Next Steps", [f"{idx}. {step}" for idx, step in enumerate(next_steps, start=1)])

    return "\n".join(response_parts).strip()
