from __future__ import annotations

from pathlib import Path

import pytest

from src.plugins.leann.strategies import (
    ArchitectureSummarizer,
    DiagnosticsAdvisor,
    QuestionIntent,
    QuestionRouter,
)


def test_question_router_classifies_core_intents() -> None:
    router = QuestionRouter()

    assert router.classify("can you see the repo?").intent is QuestionIntent.VISIBILITY
    assert router.classify("please verify the browser fix").intent is QuestionIntent.VERIFY_FIX
    assert router.classify("diagnose why search is broken").intent is QuestionIntent.DIAGNOSTIC
    assert router.classify("what would you change about the tests?").intent is QuestionIntent.IMPROVEMENT
    assert router.classify("give me an assessment of the codebase").intent is QuestionIntent.ASSESSMENT
    assert router.classify("are you able to create plugins?").intent is QuestionIntent.CAPABILITY

    plugin_route = router.classify("explain the browser plugin")
    assert plugin_route.intent is QuestionIntent.PLUGIN_SPECIFIC
    assert plugin_route.plugin_name == "browser"


def test_diagnostics_advisor_reports_visibility(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("print('hello world')\n", encoding="utf-8")

    advisor = DiagnosticsAdvisor(tmp_path)
    report = advisor.visibility_report()

    assert "I can see my codebase" in report


def test_architecture_summarizer_improvement_plan(tmp_path: Path) -> None:
    (tmp_path / "src" / "plugins").mkdir(parents=True)
    (tmp_path / "src" / "plugins" / "demo.py").write_text(
        "async def execute(server, tool_name, args):\n    return {'status': 'success'}\n",
        encoding="utf-8",
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "docs").mkdir()

    summarizer = ArchitectureSummarizer(tmp_path)

    overview = summarizer.codebase_overview()
    assert "Primary Directories" in overview

    recommendations = summarizer.improvement_recommendations()
    assert "Improvement" in recommendations or "Maintain" in recommendations

    plugin_details = summarizer.plugin_details("demo")
    assert "Plugin: demo" in plugin_details
