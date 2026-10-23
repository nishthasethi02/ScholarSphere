# -*- coding: utf-8 -*-
"""
models/opportunity.py
---------------------
Pydantic v2 data models for ScholarSync AI.

These models describe the data that flows through the app:
  - StudentProfile      -- the form inputs the student submits
  - Scholarship         -- a single scholarship opportunity returned by search
  - EligibilityCheck    -- deterministic per-criterion eligibility result
  - SearchResult        -- the full response envelope from the search service
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ── Enumerations ──────────────────────────────────────────────────────────────


class DegreeLevel(str, Enum):
    BACHELOR = "Bachelor's"
    MASTER = "Master's"
    PHD = "PhD"
    DIPLOMA = "Diploma / Certificate"
    ANY = "Any"


class FundingType(str, Enum):
    FULL = "Full Funding"
    PARTIAL = "Partial Funding"
    TUITION_ONLY = "Tuition Only"
    LIVING_ALLOWANCE = "Living Allowance Only"
    UNKNOWN = "Unknown"


class EligibilityStatus(str, Enum):
    ELIGIBLE = "Eligible"
    LIKELY_ELIGIBLE = "Likely Eligible"
    CHECK_REQUIRED = "Check Required"
    INELIGIBLE = "Ineligible"
    UNKNOWN = "Unknown"


class VerificationStatus(str, Enum):
    """How well the scholarship details have been verified against source pages."""
    VERIFIED = "Verified"        # Official page fetched; key facts confirmed
    UNVERIFIED = "Unverified"    # Snippet data only; official page not fetched
    UNKNOWN = "Unknown"          # Fetch was attempted but content was unusable


# ── Per-criterion eligibility check ───────────────────────────────────────────


class EligibilityCheck(BaseModel):
    """
    Result of one deterministic eligibility criterion.

    All checks are rule-based — never inferred by a language model.
    When the required information is absent, met=None (Unknown).
    """
    criterion: str = Field(..., description="Human-readable criterion label.")
    met: Optional[bool] = Field(
        None,
        description="True=met, False=not met, None=unknown (info missing).",
    )
    detail: str = Field("", description="One-line explanation of how the verdict was reached.")


# ── Student profile ───────────────────────────────────────────────────────────


class StudentProfile(BaseModel):
    """Represents the student's self-reported academic profile."""

    degree_level: DegreeLevel = Field(
        DegreeLevel.MASTER,
        description="Current or intended degree level.",
    )
    field_of_study: str = Field(
        ...,
        min_length=2,
        max_length=120,
        description="Major / field of study (e.g. 'Computer Science').",
    )
    cgpa: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Cumulative GPA on a 4- or 10-point scale.",
    )
    nationality: str = Field(
        ...,
        min_length=2,
        max_length=80,
        description="Student's nationality / citizenship.",
    )
    preferred_countries: list[str] = Field(
        default_factory=list,
        description="Countries where the student would like to study.",
    )
    intended_intake: Optional[str] = Field(
        None,
        description="Target intake season and year, e.g. 'Fall 2026'.",
    )
    graduation_year: Optional[int] = Field(
        None,
        ge=1990,
        le=2040,
        description="Year of (expected) graduation from current programme.",
    )
    annual_budget_usd: Optional[float] = Field(
        None,
        ge=0,
        description="Maximum annual self-funded budget in USD (0 = fully-funded only).",
    )
    resume_filename: Optional[str] = Field(
        None, description="Original filename of uploaded resume PDF."
    )
    marksheet_filename: Optional[str] = Field(
        None, description="Original filename of uploaded marksheet PDF."
    )

    @field_validator("cgpa")
    @classmethod
    def cgpa_reasonable(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v > 10.0:
            raise ValueError("CGPA must be <= 10.0")
        return v

    @field_validator("preferred_countries", mode="before")
    @classmethod
    def normalise_countries(cls, v: object) -> list[str]:
        if isinstance(v, str):
            return [c.strip() for c in v.split(",") if c.strip()]
        return list(v) if v else []


# ── Scholarship opportunity ───────────────────────────────────────────────────


class Scholarship(BaseModel):
    """A single scholarship opportunity discovered by the search service."""

    name: str = Field(..., description="Official name of the scholarship.")
    provider: str = Field(..., description="Organisation / university offering it.")
    country: str = Field(..., description="Country where the study takes place.")
    degree_levels: list[DegreeLevel] = Field(
        default_factory=list,
        description="Eligible degree levels.",
    )
    field_tags: list[str] = Field(
        default_factory=list,
        description="Fields / disciplines this scholarship targets.",
    )
    funding_type: FundingType = Field(
        FundingType.UNKNOWN, description="Extent of financial coverage."
    )
    annual_value_usd: Optional[float] = Field(
        None,
        ge=0,
        description="Approximate annual value in USD, if known.",
    )
    deadline: Optional[date] = Field(
        None, description="Application deadline (None = rolling / unknown)."
    )
    # ── Eligibility ──────────────────────────────────────────────────────────
    eligibility_notes: str = Field(
        "", description="Human-readable eligibility summary from the source."
    )
    eligibility_status: EligibilityStatus = Field(
        EligibilityStatus.UNKNOWN,
        description="Aggregate eligibility verdict relative to the queried profile.",
    )
    eligibility_checks: list[EligibilityCheck] = Field(
        default_factory=list,
        description="Per-criterion deterministic eligibility results.",
    )
    # ── Scoring and provenance ────────────────────────────────────────────────
    match_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Normalised relevance score returned by the search API (0-1).",
    )
    application_url: Optional[str] = Field(
        None, description="Official application / information URL."
    )
    source_url: Optional[str] = Field(
        None, description="URL of the page where this result was found."
    )
    source_domain: Optional[str] = Field(
        None, description="Registered domain of source_url for deduplication."
    )
    # ── Verification ─────────────────────────────────────────────────────────
    verification_status: VerificationStatus = Field(
        VerificationStatus.UNVERIFIED,
        description="Whether key details were confirmed against an official page.",
    )
    raw_excerpt: str = Field(
        "",
        description=(
            "Supporting text excerpt from the official page or snippet. "
            "Stored to make the verification basis transparent."
        ),
    )
    match_reasons: list[str] = Field(
        default_factory=list,
        description="Specific explanations for why this opportunity matches the student profile.",
    )
    sop_draft: Optional[str] = Field(
        None,
        description="Opportunity-tailored Statement of Purpose draft using confirmed student facts.",
    )
    fetched_at: Optional[datetime] = Field(
        None,
        description="UTC timestamp of when the official page was fetched (if attempted).",
    )
    # ── Metadata ─────────────────────────────────────────────────────────────
    is_demo: bool = Field(
        False,
        description="True when this record is sample / demo data, not a real search result.",
    )


# ── Search result envelope ────────────────────────────────────────────────────


class SearchResult(BaseModel):
    """Envelope returned by the search service to the Streamlit UI."""

    success: bool = Field(..., description="Whether the search completed without error.")
    scholarships: list[Scholarship] = Field(default_factory=list)
    total_found: int = Field(0, description="Total results before any trimming.")
    queries_used: list[str] = Field(
        default_factory=list,
        description="All queries sent to the search API in this session.",
    )
    # Keep backward-compatible single query field
    query_used: str = Field("", description="Primary query sent (first query).")
    error_message: Optional[str] = Field(
        None, description="Human-readable error if success is False."
    )
    is_demo: bool = Field(
        False,
        description="True when the result set contains demo data only.",
    )
    api_key_missing: bool = Field(
        False, description="True when search was skipped due to a missing API key."
    )
    # ── Runtime stats ─────────────────────────────────────────────────────────
    queries_fired: int = Field(0, description="Number of Tavily queries executed.")
    raw_results_count: int = Field(0, description="Total raw results before deduplication.")
    duplicates_removed: int = Field(0, description="Results dropped during deduplication.")
    pages_fetched: int = Field(0, description="Official pages fetched for verification.")
    sop_draft: Optional[str] = Field(None, description="Global SOP draft for the top matched scholarship.")
    workflow_events: list[dict] = Field(default_factory=list, description="Structured agent activity logs.")
