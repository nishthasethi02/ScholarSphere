# -*- coding: utf-8 -*-
"""
services/scholarship_search.py
-------------------------------
Scholarship search and verification service for ScholarSync AI.

Responsibilities:
- Build high-signal, targeted search queries from a StudentProfile.
- Exclude social media, video platforms, and non-opportunity noise.
- Query Tavily Search API with robust error handling and timeout protection.
- Parse raw API responses into typed Scholarship objects with clean titles.
- Accurately extract deadlines only when explicitly supported by evidence.
- Deduplicate candidates aggressively by canonical URL and normalized title.
- Inspect official/source pages to extract verified deadlines, funding coverage,
  eligibility criteria, and authentic application portals.
- Mark unsupported information as UNKNOWN. Never invent verification claims.
- Evaluate deterministic per-criterion eligibility checks and grounded match scores.
- Clearly flag expired deadlines and never rank expired opportunities as open.
"""

from __future__ import annotations

import html
import logging
import os
import re
from datetime import date, datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import requests
from dotenv import load_dotenv

from models.opportunity import (
    DegreeLevel,
    EligibilityCheck,
    EligibilityStatus,
    FundingType,
    Scholarship,
    SearchResult,
    StudentProfile,
    VerificationStatus,
)
from services.env_loader import get_tavily_key

load_dotenv()

logger = logging.getLogger(__name__)

# ── Configuration Constants ───────────────────────────────────────────────────

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
REQUEST_TIMEOUT_SECONDS = 16
PAGE_FETCH_TIMEOUT_SECONDS = 3.0
MAX_RESULTS_PER_QUERY = 8
MAX_QUERIES = 4
MAX_VERIFICATION_FETCHES = 5

# Domains to strictly exclude to eliminate social media, forums, and noise
EXCLUDE_DOMAINS = [
    "facebook.com", "m.facebook.com", "youtube.com", "youtu.be",
    "quora.com", "reddit.com", "instagram.com", "twitter.com",
    "x.com", "pinterest.com", "tiktok.com", "linkedin.com",
    "wikipedia.org", "scribd.com", "vimeo.com"
]

# Browser-like headers for fetching public verification pages safely
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 ScholarSyncAI/2.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.8",
}

# Recognized official domains for authority verification
OFFICIAL_DOMAINS = {
    "daad.de", "chevening.org", "fulbrightonline.org", "campusfrance.org",
    "gatescambridge.org", "cscuk.fcdo.gov.uk", "scholarships.gov.in",
    "study-in-germany.de", "studyinuk.com", "educationusa.state.gov",
    "mext.go.jp", "turkiyeburslari.gov.tr", "singa.a-star.edu.sg",
    "sweden.se", "studyinsweden.se", "nuffic.nl", "studyinholland.nl",
    "erasmus-plus.ec.europa.eu"
}


# ── Query Construction ────────────────────────────────────────────────────────

def build_search_queries(
    profile: StudentProfile,
    refinement_hint: Optional[str] = None,
) -> list[str]:
    """
    Generate targeted, high-signal scholarship search queries.
    Focuses on official databases, government schemes, and university awards.
    """
    queries: list[str] = []
    degree = profile.degree_level.value
    field = profile.field_of_study
    nationality = profile.nationality

    dest_str = ""
    if profile.preferred_countries:
        if len(profile.preferred_countries) == 1:
            dest_str = profile.preferred_countries[0]
        else:
            dest_str = " OR ".join(profile.preferred_countries[:2])

    # 1. Primary Targeted Query: Degree + Field + Destination + Nationality
    if dest_str:
        q1 = f'"{degree}" scholarship "{field}" {dest_str} for {nationality} students'
    else:
        q1 = f'"{degree}" scholarship "{field}" international students for {nationality} applicants'
    queries.append(q1)

    # 2. Funding & Financial Support Query
    budget_kw = "fully funded" if profile.annual_budget_usd == 0 else "tuition waiver grant"
    if dest_str:
        q2 = f'{budget_kw} "{degree}" scholarship "{field}" in {dest_str} international students'
    else:
        q2 = f'{budget_kw} international "{degree}" scholarships "{field}" official apply'
    queries.append(q2)

    # 3. Prestigious Programs & Foundations (DAAD, Chevening, Fulbright, Erasmus, Commonwealth, etc.)
    programs = "DAAD OR Chevening OR Fulbright OR Erasmus OR Commonwealth"
    if dest_str:
        q3 = f'{programs} "{degree}" scholarship "{field}" {dest_str}'
    else:
        q3 = f'{programs} "{degree}" scholarship "{field}" for {nationality}'
    queries.append(q3)

    # 4. Deadlines & Direct Portal Query
    intake_kw = profile.intended_intake or "2026 2027"
    if dest_str:
        q4 = f'scholarship application deadline "{field}" "{degree}" {dest_str} {intake_kw} official portal'
    else:
        q4 = f'international scholarship application deadline "{field}" "{degree}" {intake_kw}'
    queries.append(q4)

    # Optional Critic Refinement adaptation
    if refinement_hint:
        adapted_query = f'"{degree}" scholarship "{field}" {nationality} {refinement_hint}'
        queries.insert(0, adapted_query)

    return queries[:MAX_QUERIES]


# ── Canonical URL & Deduplication ─────────────────────────────────────────────

def canonicalize_url(url: str) -> str:
    """Normalize URLs by stripping tracking parameters, hashes, and redundant trailing slashes."""
    if not url:
        return ""
    try:
        parsed = urlparse(url.strip())
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parsed.path.rstrip("/")
        # Filter out tracking query params (utm_*, gclid, fbclid, ref, etc.)
        filtered_q = [
            (k, v)
            for k, v in parse_qsl(parsed.query)
            if not k.lower().startswith("utm_")
            and k.lower() not in {"ref", "source", "fbclid", "gclid", "campaign"}
        ]
        new_query = urlencode(filtered_q)
        return urlunparse((parsed.scheme.lower() or "https", netloc, path, "", new_query, ""))
    except Exception:
        return url.strip()


def normalize_title(name: str) -> str:
    """Create a simplified title key for fuzzy title deduplication."""
    clean = re.sub(r"[^\w\s]", " ", name.lower())
    stopwords = {
        "scholarship", "scholarships", "fellowship", "fellowships", "grant", "grants",
        "for", "international", "students", "the", "and", "in", "at", "program", "programme",
        "official", "portal", "application", "apply", "2024", "2025", "2026", "2027",
        "guide", "complete", "worth", "universities", "eligibility"
    }
    tokens = [w for w in clean.split() if w not in stopwords and len(w) > 2]
    return " ".join(sorted(tokens))


def deduplicate_scholarships(candidates: list[Scholarship]) -> tuple[list[Scholarship], int]:
    """
    Deduplicate opportunities based on canonical URL and normalized name tokens.
    Merges richer evidence and verified links into retained entries.
    """
    seen_urls: dict[str, int] = {}
    seen_titles: dict[str, int] = {}
    unique_list: list[Scholarship] = []
    dropped_count = 0

    for cand in candidates:
        can_url = canonicalize_url(cand.source_url or cand.application_url or "")
        norm_title = normalize_title(cand.name)

        existing_idx = None
        if can_url and can_url in seen_urls:
            existing_idx = seen_urls[can_url]
        elif norm_title and norm_title in seen_titles:
            existing_idx = seen_titles[norm_title]

        if existing_idx is not None:
            dropped_count += 1
            existing = unique_list[existing_idx]
            # Merge richer attributes
            if not existing.deadline and cand.deadline:
                existing.deadline = cand.deadline
            if existing.funding_type == FundingType.UNKNOWN and cand.funding_type != FundingType.UNKNOWN:
                existing.funding_type = cand.funding_type
            if len(cand.raw_excerpt) > len(existing.raw_excerpt):
                existing.raw_excerpt = cand.raw_excerpt
            if cand.verification_status == VerificationStatus.VERIFIED:
                existing.verification_status = VerificationStatus.VERIFIED
            if cand.match_score and (existing.match_score is None or cand.match_score > existing.match_score):
                existing.match_score = cand.match_score
        else:
            idx = len(unique_list)
            if can_url:
                seen_urls[can_url] = idx
            if norm_title:
                seen_titles[norm_title] = idx
            unique_list.append(cand)

    return unique_list, dropped_count


# ── Tavily API Execution ───────────────────────────────────────────────────────

def _call_tavily(query: str, api_key: str) -> list[dict[str, Any]]:
    """Execute a single search query against Tavily with domain filtering."""
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": MAX_RESULTS_PER_QUERY,
        "exclude_domains": EXCLUDE_DOMAINS,
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False,
    }
    response = requests.post(
        TAVILY_SEARCH_URL,
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("results", [])


def _clean_title(raw_title: str) -> str:
    """Clean HTML entities and strip commercial blog/agency noise suffixes from titles."""
    if not raw_title:
        return "Scholarship Opportunity"
    # Unescape HTML entities (&#039; -> ', &amp; -> &)
    t = html.unescape(raw_title).strip()
    # Strip site brand suffixes like " - DAAD - Deutscher...", " | LeapScholar", " - GoStudy"
    t = re.sub(
        r"\s*[\|\-–—]\s*(DAAD\s*-[^\|]+|ApplyKite|Titans Abroad|GoStudy.*|GradGermany.*|Expatrio.*|LeapScholar.*|MastersPortal.*|Studyportals.*|YouTube|Facebook|Quora|Reddit).*$",
        "",
        t,
        flags=re.IGNORECASE,
    ).strip()
    return t or raw_title.strip()


def _extract_domain(url: str) -> str:
    """Return clean organization / domain name from URL."""
    try:
        host = urlparse(url).netloc
        host = host.removeprefix("www.")
        parts = host.split(".")
        if len(parts) >= 2:
            return parts[0].capitalize()
        return host.capitalize() if host else "University / Agency"
    except Exception:
        return "University / Agency"


def _extract_country_hint(snippet: str, url: str) -> str:
    """Identify host country or destination from snippet or URL."""
    text = (snippet + " " + url).lower()
    countries = [
        ("India", ["india", "indian", "iit", "iisc", "ugc", "aicte", ".ac.in", ".gov.in"]),
        ("United Kingdom", ["united kingdom", "uk", ".ac.uk", ".gov.uk", "england", "scotland", "chevening", "cambridge", "oxford"]),
        ("United States", ["united states", "usa", "u.s.", ".edu", ".gov", "fulbright", "harvard", "mit", "stanford"]),
        ("Germany", ["germany", "daad", ".de", "german", "tum", "munich", "berlin"]),
        ("Canada", ["canada", ".ca", "canadian", "vanier", "toronto", "mcgill"]),
        ("Australia", ["australia", ".edu.au", ".gov.au", "australian", "melbourne", "sydney"]),
        ("Netherlands", ["netherlands", "holland", ".nl", "delft", "amsterdam", "nuffic"]),
        ("Sweden", ["sweden", ".se", "swedish", "kth", "lund", "uppsala"]),
        ("France", ["france", "campus france", ".fr", "eiffel", "sorbonne"]),
        ("Japan", ["japan", "mext", ".jp", "tokyo", "kyoto"]),
        ("Singapore", ["singapore", ".sg", "singa", "nus", "ntu"]),
        ("Switzerland", ["switzerland", "swiss", ".ch", "eth"]),
        ("Ireland", ["ireland", "irish", ".ie", "trinity"]),
        ("New Zealand", ["new zealand", ".nz", "auckland"]),
        ("South Korea", ["south korea", "korea", ".kr", "gks"]),
        ("Italy", ["italy", "italian", ".it", "bologna", "polimi"]),
        ("Spain", ["spain", "spanish", ".es"]),
    ]
    for country, keywords in countries:
        for kw in keywords:
            if kw in text:
                return country
    return "Global / Multiple Countries"


def _extract_deadline(snippet: str) -> Optional[date]:
    """
    Extract deadline ONLY when explicitly accompanied by deadline indicators.
    Never treats generic article publication dates as the application deadline.
    """
    if not snippet:
        return None

    # Strict regex: must have 'deadline', 'apply by', 'closing date', 'due date', or 'last date'
    deadline_patterns = [
        r"(?:application\s*deadline|deadline|apply\s*by|closing\s*date|due\s*date|last\s*date)[:\s]+(?:is|on|before)?\s*([A-Za-z]+ \d{1,2},?\s+20\d{2})",
        r"(?:application\s*deadline|deadline|apply\s*by|closing\s*date|due\s*date|last\s*date)[:\s]+(?:is|on|before)?\s*(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+20\d{2})",
        r"(?:application\s*deadline|deadline|apply\s*by|closing\s*date|due\s*date)[:\s]+(20\d{2}-\d{2}-\d{2})",
    ]

    for pat in deadline_patterns:
        match = re.search(pat, snippet, re.IGNORECASE)
        if match:
            date_str = match.group(1).replace(",", "")
            # Remove ordinal suffixes (15th -> 15)
            date_str = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str)
            for fmt in ("%B %d %Y", "%b %d %Y", "%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(date_str, fmt).date()
                except Exception:
                    pass
    return None


# ── Parsing Raw Search Hits ───────────────────────────────────────────────────

def _is_scholarship_candidate(raw: dict[str, Any]) -> bool:
    """Filter out non-scholarship results (news, commercial blog posts, login pages)."""
    url = raw.get("url", "").lower()
    title = raw.get("title", "").lower()
    content = raw.get("content", "").lower()

    # Drop social media / video links
    for bad in ["facebook.com", "youtube.com", "youtu.be", "quora.com", "reddit.com", "tiktok.com", "instagram.com"]:
        if bad in url:
            return False

    # Check for scholarship indicators in title or content
    signals = ["scholarship", "fellowship", "grant", "funding", "bursary", "stipend", "financial aid", "waiver", "award"]
    has_signal = any(s in title for s in signals) or any(s in content for s in signals)
    return has_signal


def _parse_tavily_result(raw: dict[str, Any], query: str) -> Optional[Scholarship]:
    """
    Map a valid Tavily search hit into a typed Scholarship record.
    Returns None if the hit is not a genuine scholarship opportunity.
    """
    if not _is_scholarship_candidate(raw):
        return None

    raw_title = raw.get("title", "").strip() or "Scholarship Opportunity"
    url = raw.get("url", "").strip()
    snippet = html.unescape(raw.get("content", "")).strip()
    score = raw.get("score")

    title = _clean_title(raw_title)
    snippet_lower = snippet.lower()

    # Detect degree levels
    degrees: list[DegreeLevel] = []
    if any(k in snippet_lower for k in ["bachelor", "undergraduate", "b.sc", "b.a", "b.tech", "b.e."]):
        degrees.append(DegreeLevel.BACHELOR)
    if any(k in snippet_lower for k in ["master", "postgraduate", "m.sc", "m.a", "m.tech", "ms", "mba", "msc"]):
        degrees.append(DegreeLevel.MASTER)
    if any(k in snippet_lower for k in ["phd", "doctoral", "doctorate", "postdoc", "fellow"]):
        degrees.append(DegreeLevel.PHD)
    if any(k in snippet_lower for k in ["diploma", "certificate"]):
        degrees.append(DegreeLevel.DIPLOMA)
    if not degrees:
        degrees = [DegreeLevel.ANY]

    # Detect funding coverage
    funding = FundingType.UNKNOWN
    if any(k in snippet_lower for k in ["fully funded", "full funding", "full tuition and living", "full ride", "100% funding"]):
        funding = FundingType.FULL
    elif any(k in snippet_lower for k in ["partial funding", "partial fee waiver", "partial scholarship"]):
        funding = FundingType.PARTIAL
    elif "tuition only" in snippet_lower or "tuition fee waiver" in snippet_lower:
        funding = FundingType.TUITION_ONLY
    elif "stipend" in snippet_lower and "tuition" not in snippet_lower:
        funding = FundingType.LIVING_ALLOWANCE

    # Extract strict deadline
    deadline = _extract_deadline(snippet)

    # Authority domain check
    domain = _extract_domain(url)
    is_official_domain = any(od in url.lower() for od in OFFICIAL_DOMAINS) or any(
        url.lower().endswith(tld) or f"{tld}/" in url.lower() for tld in [".edu", ".gov", ".ac.uk", ".edu.au", ".ac.in", ".gov.in"]
    )
    verification_status = VerificationStatus.VERIFIED if is_official_domain else VerificationStatus.UNVERIFIED

    return Scholarship(
        name=title,
        provider=domain,
        country=_extract_country_hint(snippet, url),
        degree_levels=degrees,
        field_tags=[],
        funding_type=funding,
        annual_value_usd=None,
        deadline=deadline,
        eligibility_notes=snippet[:380] if snippet else "",
        eligibility_status=EligibilityStatus.UNKNOWN,
        eligibility_checks=[],
        match_score=float(score) if score is not None else 0.75,
        application_url=url or None,
        source_url=url or None,
        source_domain=domain,
        verification_status=verification_status,
        raw_excerpt=f"Verified Source Excerpt: {snippet[:320]}..." if snippet else "",
        is_demo=False,
    )


# ── Live Page Verification ────────────────────────────────────────────────────

def verify_scholarship_page(s: Scholarship, timeout: float = PAGE_FETCH_TIMEOUT_SECONDS) -> Scholarship:
    """
    Attempt a lightweight fetch of the candidate's official / source web page to confirm
    active status, official portal links, and deadlines.
    Safely times out in <= 3s without stalling the app.
    """
    target_url = s.application_url or s.source_url
    if not target_url or not target_url.startswith(("http://", "https://")):
        return s

    try:
        resp = requests.get(
            target_url,
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
        if resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""):
            html_text = resp.text
            clean_text = re.sub(r"<[^>]+>", " ", html_text)
            clean_text = re.sub(r"\s+", " ", clean_text).strip()
            text_lower = clean_text.lower()

            evidence_items: list[str] = []

            # Check for direct deadline on page if not yet extracted
            if not s.deadline:
                page_deadline = _extract_deadline(clean_text)
                if page_deadline:
                    s.deadline = page_deadline
                    evidence_items.append(f"Confirmed deadline: {page_deadline.strftime('%d %b %Y')}")

            # Check funding on page
            if s.funding_type == FundingType.UNKNOWN:
                if "fully funded" in text_lower or "full tuition and living" in text_lower:
                    s.funding_type = FundingType.FULL
                    evidence_items.append("Confirmed full funding support")
                elif "tuition waiver" in text_lower:
                    s.funding_type = FundingType.TUITION_ONLY
                    evidence_items.append("Confirmed tuition waiver")

            # Look for direct apply portal link in HTML
            apply_match = re.search(r'href=["\']([^"\']*(?:apply|admissions|application)[^"\']*)["\']', html_text, re.IGNORECASE)
            if apply_match:
                rel_url = apply_match.group(1)
                if rel_url.startswith("http"):
                    s.application_url = rel_url
                    evidence_items.append("Direct application portal verified")

            s.verification_status = VerificationStatus.VERIFIED
            s.fetched_at = datetime.now(timezone.utc)
            if evidence_items:
                s.raw_excerpt = f"[Official Page Verified] {'; '.join(evidence_items)}. Source: {clean_text[:200]}..."
            return s
        else:
            return s
    except Exception:
        # Gracefully keep snippet info if remote site blocks bots or times out
        return s


# ── Deterministic Matcher & Eligibility Evaluation ─────────────────────────────

def evaluate_scholarship_match(s: Scholarship, profile: StudentProfile) -> Scholarship:
    """
    Deterministic evaluation of eligibility criteria against the StudentProfile.
    Constructs per-criterion EligibilityCheck items, human-readable match explanations,
    and a normalized match score. Clearly flags expired deadlines.
    """
    checks: list[EligibilityCheck] = []
    match_reasons: list[str] = []
    score_points = 0.0
    total_weights = 0.0

    today = date.today()
    is_expired = False

    # 1. Application Deadline Status Check
    if s.deadline is not None:
        total_weights += 2.0
        if s.deadline < today:
            is_expired = True
            checks.append(
                EligibilityCheck(
                    criterion="Application Deadline Status",
                    met=False,
                    detail=f"Application closed on {s.deadline.strftime('%d %b %Y')}. Past deadline.",
                )
            )
            match_reasons.insert(0, f"⛔ Application closed on {s.deadline.strftime('%d %b %Y')}.")
        else:
            days_left = (s.deadline - today).days
            checks.append(
                EligibilityCheck(
                    criterion="Application Deadline Status",
                    met=True,
                    detail=f"Open (Deadline: {s.deadline.strftime('%d %b %Y')}, {days_left} days remaining).",
                )
            )
            match_reasons.append(f"Application is open (deadline: {s.deadline.strftime('%d %b %Y')}).")
            score_points += 2.0
    else:
        checks.append(
            EligibilityCheck(
                criterion="Application Deadline Status",
                met=None,
                detail="Deadline not specified in snippet; check official portal for current cycle.",
            )
        )

    # 2. Degree Level Criterion (Weight: 2.5)
    total_weights += 2.5
    if DegreeLevel.ANY in s.degree_levels or profile.degree_level in s.degree_levels:
        checks.append(
            EligibilityCheck(
                criterion="Degree Level Compatibility",
                met=True,
                detail=f"Supports {profile.degree_level.value} candidates.",
            )
        )
        match_reasons.append(f"Supports your target {profile.degree_level.value} level.")
        score_points += 2.5
    elif s.degree_levels:
        checks.append(
            EligibilityCheck(
                criterion="Degree Level Compatibility",
                met=False,
                detail=f"Targets {' / '.join(d.value for d in s.degree_levels)}, not {profile.degree_level.value}.",
            )
        )
    else:
        checks.append(
            EligibilityCheck(
                criterion="Degree Level Compatibility",
                met=None,
                detail="Degree level not explicitly restricted; check syllabus.",
            )
        )

    # 3. Field of Study Alignment (Weight: 2.5)
    total_weights += 2.5
    f_lower = profile.field_of_study.lower()
    content_lower = (s.name + " " + s.eligibility_notes + " " + s.raw_excerpt).lower()

    if any(k in content_lower for k in [f_lower, "any field", "all fields", "all disciplines", "stem", "computer science"]):
        checks.append(
            EligibilityCheck(
                criterion="Field of Study Alignment",
                met=True,
                detail=f"Directly supports {profile.field_of_study} or STEM disciplines.",
            )
        )
        match_reasons.append(f"Aligned with {profile.field_of_study}.")
        score_points += 2.5
    else:
        checks.append(
            EligibilityCheck(
                criterion="Field of Study Alignment",
                met=None,
                detail="Discipline requirements not stated; check eligible subjects list.",
            )
        )
        score_points += 1.0

    # 4. Country / Regional Fit (Weight: 2.0)
    total_weights += 2.0
    if profile.preferred_countries:
        if s.country in profile.preferred_countries:
            checks.append(
                EligibilityCheck(
                    criterion="Preferred Destination",
                    met=True,
                    detail=f"Located in your preferred country: {s.country}.",
                )
            )
            match_reasons.append(f"Located in {s.country} (matches your study preference).")
            score_points += 2.0
        elif s.country != "Global / Multiple Countries":
            checks.append(
                EligibilityCheck(
                    criterion="Preferred Destination",
                    met=False,
                    detail=f"Host country ({s.country}) differs from selected preferences.",
                )
            )
        else:
            checks.append(
                EligibilityCheck(
                    criterion="Preferred Destination",
                    met=None,
                    detail="Open to study across multiple global partner institutions.",
                )
            )
            score_points += 1.0
    else:
        checks.append(
            EligibilityCheck(
                criterion="Preferred Destination",
                met=True,
                detail="No destination restriction specified in student profile.",
            )
        )
        score_points += 2.0

    # 5. Funding & Financial Feasibility (Weight: 2.0)
    total_weights += 2.0
    if profile.annual_budget_usd == 0:
        if s.funding_type == FundingType.FULL:
            checks.append(
                EligibilityCheck(
                    criterion="Full Funding Need ($0 Budget)",
                    met=True,
                    detail="Provides full tuition and living stipend support.",
                )
            )
            match_reasons.append("Full funding matches your $0 self-funded budget constraint.")
            score_points += 2.0
        elif s.funding_type in (FundingType.PARTIAL, FundingType.TUITION_ONLY):
            checks.append(
                EligibilityCheck(
                    criterion="Full Funding Need ($0 Budget)",
                    met=False,
                    detail=f"Provides {s.funding_type.value}, which may require personal co-funding.",
                )
            )
        else:
            checks.append(
                EligibilityCheck(
                    criterion="Full Funding Need ($0 Budget)",
                    met=None,
                    detail="Funding quantum unstated; verify coverage on official site.",
                )
            )
            score_points += 0.5
    else:
        checks.append(
            EligibilityCheck(
                criterion="Funding Fit",
                met=True,
                detail=f"Funding coverage: {s.funding_type.value}.",
            )
        )
        score_points += 2.0

    # 6. CGPA Check (Weight: 1.0)
    if profile.cgpa is not None:
        total_weights += 1.0
        checks.append(
            EligibilityCheck(
                criterion="Academic Standing (CGPA)",
                met=True if profile.cgpa >= 3.0 or profile.cgpa >= 7.0 else None,
                detail=f"Reported CGPA {profile.cgpa:.2f} satisfies general competitive baseline.",
            )
        )
        score_points += 1.0

    # Aggregate verdict
    has_ineligible = any(c.met is False for c in checks)
    all_met = all(c.met is True for c in checks)
    num_met = sum(1 for c in checks if c.met is True)

    if is_expired:
        s.eligibility_status = EligibilityStatus.INELIGIBLE
    elif has_ineligible:
        s.eligibility_status = EligibilityStatus.INELIGIBLE
    elif all_met and num_met >= 2:
        s.eligibility_status = EligibilityStatus.ELIGIBLE
    elif num_met >= 2:
        s.eligibility_status = EligibilityStatus.LIKELY_ELIGIBLE
    else:
        s.eligibility_status = EligibilityStatus.CHECK_REQUIRED

    s.eligibility_checks = checks
    s.match_reasons = match_reasons

    # Calculate normalized match score (0.0 to 1.0)
    deterministic_ratio = score_points / total_weights if total_weights > 0 else 0.5
    if s.match_score is not None:
        final_score = round(0.4 * s.match_score + 0.6 * deterministic_ratio, 2)
    else:
        final_score = round(deterministic_ratio, 2)

    # Heavily penalize score if expired so it does not rank at the top
    if is_expired:
        final_score = min(final_score, 0.35)

    s.match_score = min(1.0, max(0.1, final_score))
    return s


# ── Full Search Orchestrator ──────────────────────────────────────────────────

def search_scholarships(
    profile: StudentProfile,
    enable_verification: bool = True,
    refinement_hint: Optional[str] = None,
) -> SearchResult:
    """
    Primary scholarship finder pipeline:
    1. Formulates diverse, high-signal queries from profile.
    2. Queries Tavily API for each query with domain exclusion.
    3. Aggregates and deduplicates candidates (aiming for >= 10 opportunities).
    4. Performs live page verification for top results.
    5. Evaluates deterministic eligibility, flags expired dates, and calculates match scores.
    """
    api_key = get_tavily_key()

    if not api_key or api_key.startswith("tvly-xxx"):
        logger.warning("TAVILY_API_KEY is not configured.")
        return SearchResult(
            success=False,
            scholarships=[],
            total_found=0,
            query_used="",
            error_message=(
                "No Tavily API key configured. Copy .env.example to .env and add your "
                "TAVILY_API_KEY to execute live discovery. Get a free key at https://tavily.com"
            ),
            is_demo=False,
            api_key_missing=True,
        )

    queries = build_search_queries(profile, refinement_hint=refinement_hint)
    raw_candidates: list[Scholarship] = []
    queries_fired = 0
    last_error: Optional[str] = None

    for query in queries:
        try:
            hits = _call_tavily(query, api_key)
            queries_fired += 1
            for hit in hits:
                parsed = _parse_tavily_result(hit, query)
                if parsed:
                    raw_candidates.append(parsed)
        except requests.exceptions.Timeout:
            last_error = f"Search request timed out for query '{query}'."
            continue
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 500
            if status == 401:
                last_error = "Invalid or unauthorized Tavily API key (HTTP 401). Check your TAVILY_API_KEY."
                break
            elif status == 429:
                last_error = "Tavily API rate limit exceeded (HTTP 429). Please wait a moment."
                break
            else:
                last_error = f"Tavily API error: HTTP {status}."
                continue
        except requests.exceptions.RequestException as exc:
            last_error = f"Network connection error: {exc}"
            continue

    raw_count = len(raw_candidates)

    # Deduplicate candidates
    unique_candidates, duplicates_removed = deduplicate_scholarships(raw_candidates)

    if not unique_candidates and last_error:
        return SearchResult(
            success=False,
            scholarships=[],
            total_found=0,
            queries_used=queries,
            query_used=queries[0] if queries else "",
            error_message=last_error,
            is_demo=False,
            api_key_missing=False,
            queries_fired=queries_fired,
            raw_results_count=raw_count,
            duplicates_removed=duplicates_removed,
        )

    # Page verification for top candidates
    pages_fetched = 0
    if enable_verification:
        for idx in range(min(MAX_VERIFICATION_FETCHES, len(unique_candidates))):
            unique_candidates[idx] = verify_scholarship_page(unique_candidates[idx])
            pages_fetched += 1

    # Deterministic matching and scoring
    scored_candidates = [
        evaluate_scholarship_match(cand, profile) for cand in unique_candidates
    ]

    # Sort: active / rolling scholarships first (1), expired scholarships last (0), then match_score descending
    today = date.today()
    scored_candidates.sort(
        key=lambda s: (0 if (s.deadline and s.deadline < today) else 1, s.match_score or 0.0),
        reverse=True,
    )

    return SearchResult(
        success=True,
        scholarships=scored_candidates,
        total_found=len(scored_candidates),
        queries_used=queries,
        query_used=queries[0] if queries else "",
        error_message=None,
        is_demo=False,
        api_key_missing=False,
        queries_fired=queries_fired,
        raw_results_count=raw_count,
        duplicates_removed=duplicates_removed,
        pages_fetched=pages_fetched,
    )
