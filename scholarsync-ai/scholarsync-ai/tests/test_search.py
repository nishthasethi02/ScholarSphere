# -*- coding: utf-8 -*-
"""
tests/test_search.py
---------------------
Tests for scholarship search services:
- Query building from profile
- Deduplication by canonical URL and title
- URL canonicalization
- Deterministic eligibility check & matching
- Country list verification (including India)
- Expired deadline handling & ranking
"""

from datetime import date, timedelta
import pytest

from models.countries import ALL_COUNTRIES
from models.opportunity import (
    DegreeLevel,
    EligibilityStatus,
    FundingType,
    Scholarship,
    StudentProfile,
    VerificationStatus,
)
from services.scholarship_search import (
    build_search_queries,
    canonicalize_url,
    deduplicate_scholarships,
    evaluate_scholarship_match,
    normalize_title,
)


@pytest.fixture
def sample_profile() -> StudentProfile:
    return StudentProfile(
        degree_level=DegreeLevel.MASTER,
        field_of_study="Computer Science",
        cgpa=3.85,
        nationality="Indian",
        preferred_countries=["Germany", "United Kingdom"],
        intended_intake="Fall 2026",
        graduation_year=2025,
        annual_budget_usd=0.0,
    )


def test_build_search_queries(sample_profile):
    queries = build_search_queries(sample_profile)
    assert len(queries) >= 3
    assert any("Computer Science" in q for q in queries)
    assert any("Indian" in q for q in queries)
    assert any("fully funded" in q for q in queries)


def test_canonicalize_url():
    url1 = "https://www.example.org/scholarship/apply/?utm_source=google&utm_medium=cpc#section"
    url2 = "http://example.org/scholarship/apply"
    c1 = canonicalize_url(url1)
    c2 = canonicalize_url(url2)
    assert "utm_source" not in c1
    assert c1 == "https://example.org/scholarship/apply"
    assert c2 == "http://example.org/scholarship/apply"


def test_deduplicate_scholarships():
    c1 = Scholarship(
        name="DAAD Master Scholarship 2026",
        provider="DAAD",
        country="Germany",
        degree_levels=[DegreeLevel.MASTER],
        funding_type=FundingType.FULL,
        source_url="https://daad.de/en/scholarships/?utm_source=email",
    )
    # Duplicate with same canonical URL and title
    c2 = Scholarship(
        name="DAAD Master Scholarship 2026",
        provider="DAAD",
        country="Germany",
        degree_levels=[DegreeLevel.MASTER],
        funding_type=FundingType.FULL,
        deadline=date(2026, 11, 15),
        source_url="https://www.daad.de/en/scholarships",
    )
    c3 = Scholarship(
        name="Chevening Master Scholarship",
        provider="UK Government",
        country="United Kingdom",
        degree_levels=[DegreeLevel.MASTER],
        funding_type=FundingType.FULL,
        source_url="https://chevening.org/scholarships",
    )

    unique, dropped = deduplicate_scholarships([c1, c2, c3])
    assert len(unique) == 2
    assert dropped == 1
    # Check that richer deadline was preserved in merged result
    daad_match = [u for u in unique if "DAAD" in u.name][0]
    assert daad_match.deadline == date(2026, 11, 15)


def test_evaluate_scholarship_match(sample_profile):
    scholarship = Scholarship(
        name="German Academic Exchange Master Grant",
        provider="DAAD",
        country="Germany",
        degree_levels=[DegreeLevel.MASTER],
        funding_type=FundingType.FULL,
        eligibility_notes="Open to international students in Computer Science and STEM disciplines.",
        match_score=0.9,
    )
    evaluated = evaluate_scholarship_match(scholarship, sample_profile)
    assert evaluated.eligibility_status in (EligibilityStatus.ELIGIBLE, EligibilityStatus.LIKELY_ELIGIBLE)
    assert len(evaluated.eligibility_checks) >= 4
    assert any("study preference" in r.lower() or "Germany" in r for r in evaluated.match_reasons)
    assert evaluated.match_score > 0.7


def test_country_list_includes_india():
    assert "India" in ALL_COUNTRIES
    assert "United States" in ALL_COUNTRIES
    assert "United Kingdom" in ALL_COUNTRIES
    assert "Germany" in ALL_COUNTRIES
    assert len(ALL_COUNTRIES) >= 190


def test_expired_scholarship_flagged():
    profile = StudentProfile(
        degree_level=DegreeLevel.MASTER,
        field_of_study="Economics",
        nationality="Indian",
    )
    past_date = date.today() - timedelta(days=30)
    future_date = date.today() + timedelta(days=60)

    expired_s = Scholarship(
        name="Closed Fellowship",
        provider="Old Foundation",
        country="United Kingdom",
        degree_levels=[DegreeLevel.MASTER],
        deadline=past_date,
    )
    open_s = Scholarship(
        name="Active Fellowship",
        provider="Active Foundation",
        country="United Kingdom",
        degree_levels=[DegreeLevel.MASTER],
        deadline=future_date,
    )

    eval_expired = evaluate_scholarship_match(expired_s, profile)
    eval_open = evaluate_scholarship_match(open_s, profile)

    assert eval_expired.eligibility_status == EligibilityStatus.INELIGIBLE
    assert any("Application closed" in chk.detail for chk in eval_expired.eligibility_checks)
    assert eval_open.eligibility_status != EligibilityStatus.INELIGIBLE

    # Verify that sort prioritizes open over expired
    pool = [eval_expired, eval_open]
    pool.sort(
        key=lambda s: (0 if (s.deadline and s.deadline < date.today()) else 1, s.match_score or 0.0),
        reverse=True,
    )
    assert pool[0].name == "Active Fellowship"
    assert pool[1].name == "Closed Fellowship"
