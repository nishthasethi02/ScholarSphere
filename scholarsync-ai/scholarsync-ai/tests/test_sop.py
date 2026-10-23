# -*- coding: utf-8 -*-
"""
tests/test_sop.py
------------------
Tests for SOP generation grounded strictly in student facts.
"""

from models.opportunity import DegreeLevel, FundingType, Scholarship, StudentProfile
from services.sop_generator import generate_sop_draft


def test_sop_draft_grounded_in_facts():
    profile = StudentProfile(
        degree_level=DegreeLevel.MASTER,
        field_of_study="Artificial Intelligence",
        cgpa=3.92,
        nationality="Nigerian",
        preferred_countries=["United Kingdom"],
        intended_intake="Fall 2026",
        graduation_year=2025,
        annual_budget_usd=0.0,
        resume_filename="Nigeria_AI_Resume.pdf",
    )
    scholarship = Scholarship(
        name="DeepMind AI Fellowship",
        provider="University of Cambridge",
        country="United Kingdom",
        degree_levels=[DegreeLevel.MASTER],
        funding_type=FundingType.FULL,
    )

    sop = generate_sop_draft(profile, scholarship)
    assert "Nigerian" in sop
    assert "Artificial Intelligence" in sop
    assert "3.92" in sop
    assert "2025" in sop
    assert "DeepMind AI Fellowship" in sop
    assert "University of Cambridge" in sop
    assert "Nigeria_AI_Resume.pdf" in sop
    # Assert that explicit placeholders for personal stories exist rather than hallucinations
    assert "[INSERT" in sop
