# -*- coding: utf-8 -*-
"""
tests/test_agents.py
---------------------
Tests for LangGraph multi-agent orchestration:
- Graph compilation
- Node transitions (Profile Analyst -> Scout -> Verifier -> Matcher -> Critic -> Coach)
- Failure simulation and recovery loop
"""

from unittest.mock import patch
from models.opportunity import DegreeLevel, FundingType, Scholarship, StudentProfile
from agents.workflow import get_scholar_graph, run_scholar_pipeline


def test_graph_compilation():
    graph = get_scholar_graph()
    assert graph is not None


def test_agent_pipeline_failure_simulation():
    profile = StudentProfile(
        degree_level=DegreeLevel.MASTER,
        field_of_study="Robotics",
        cgpa=3.8,
        nationality="Canadian",
        preferred_countries=["Germany"],
    )

    # In simulation mode, the scout simulates a network glitch, the critic catches it and triggers retry, and then completes
    result = run_scholar_pipeline(profile, simulation_mode=True)
    # Check that agent logs contain simulation warning and critic recovery
    log_messages = [event.get("message", "") for event in result.workflow_events]
    assert any("SIMULATION" in msg for msg in log_messages)
    assert any("Critic Review" in msg for msg in log_messages)


def test_agent_pipeline_with_mocked_search():
    profile = StudentProfile(
        degree_level=DegreeLevel.MASTER,
        field_of_study="Data Science",
        cgpa=3.7,
        nationality="Brazilian",
        preferred_countries=["United States"],
        annual_budget_usd=0.0,
    )

    mock_hit = {
        "title": "US Fulbright Scholarship 2026",
        "url": "https://foreign.fulbrightonline.org/applicants",
        "content": "Fully funded master scholarship for international students in Data Science. Application deadline is October 15, 2025.",
        "score": 0.95,
    }

    with patch("agents.workflow.get_tavily_key", return_value="tvly-testkey12345678"):
        with patch("agents.workflow._call_tavily", return_value=[mock_hit]):
            result = run_scholar_pipeline(profile, simulation_mode=False)
            assert result.success is True
            assert len(result.scholarships) >= 1
            top = result.scholarships[0]
            assert "Fulbright" in top.name
            assert top.funding_type == FundingType.FULL
            assert top.match_score is not None
            assert len(top.eligibility_checks) > 0
            assert result.sop_draft is not None
            assert "Fulbright" in result.sop_draft
