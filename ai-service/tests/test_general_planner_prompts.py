from pathlib import Path


def test_planner_is_catalogue_driven_and_domain_agnostic():
    source = Path("app/agent/orchestrator.py").read_text(encoding="utf-8")
    planner = source.split("PLANNER_PROMPT = \"\"\"", 1)[1].split("\"\"\"", 1)[0]
    assert "LIVE STRUCTURED CATALOGUE" in planner
    assert "Never rely on remembered filenames" in planner
    assert "Use exact source_file, sheet and field names" in planner
    assert "Hiring_Tracker.xlsx" not in planner
    assert "Jira_Export_ATLAS.xlsx" not in planner
    assert "Payroll_Register_Jan-Mar_2026.xlsx" not in planner


def test_answer_prompt_requires_evidence_and_conflict_handling():
    source = Path("app/agent/orchestrator.py").read_text(encoding="utf-8")
    answer = source.split("ANSWER_PROMPT = \"\"\"", 1)[1].split("\"\"\"", 1)[0]
    assert "Every factual claim must cite" in answer
    assert "If sources disagree" in answer
    assert "cannot be determined" in answer
