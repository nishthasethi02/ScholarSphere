# -*- coding: utf-8 -*-
"""
app.py - ScholarSync AI
------------------------
Entry point for the Streamlit application.
Visual Theme: Premium Academic-Fintech Dashboard (Deep Navy, Pure White, Electric Teal).

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import html
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

# Ensure project root is on sys.path so local packages resolve correctly.
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from dotenv import load_dotenv

from models.countries import ALL_COUNTRIES
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
from services.env_loader import get_tavily_key, load_project_env
from services.scholarship_search import search_scholarships
from services.sop_generator import generate_sop_draft
from agents.workflow import run_scholar_pipeline

# Ensure .env is loaded from root
load_project_env()

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="ScholarSync AI — Find Your Scholarships",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme / Academic-Fintech CSS Loader ─────────────────────────────────────────
def load_css() -> str:
    """Load the custom stylesheet from styles.css with resilient fallback."""
    css_file = Path(__file__).resolve().parent / "styles.css"
    if css_file.exists():
        try:
            return f"<style>\n{css_file.read_text(encoding='utf-8')}\n</style>"
        except Exception:
            pass
    # Basic inline fallback if styles.css cannot be read
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: #070e1c !important; color: #f1f6fc !important; }
    </style>
    """

# ── Demo Data (Curated 2026/2027 Opportunities) ───────────────────────────────

DEMO_SCHOLARSHIPS: list[Scholarship] = [
    Scholarship(
        name="Chevening Scholarship (UK Government)",
        provider="UK Government",
        country="United Kingdom",
        degree_levels=[DegreeLevel.MASTER],
        field_tags=["Any field"],
        funding_type=FundingType.FULL,
        annual_value_usd=38000,
        deadline=date(2026, 11, 5),
        eligibility_notes=(
            "Open to citizens of eligible countries including India, Nigeria, Brazil, Pakistan. "
            "Requires undergraduate degree and minimum 2 years of work experience. Covers full tuition, "
            "monthly living stipend, and return airfare."
        ),
        eligibility_status=EligibilityStatus.ELIGIBLE,
        eligibility_checks=[
            EligibilityCheck(criterion="Application Deadline Status", met=True, detail="Open (2026/2027 intake deadline: 05 Nov 2026)."),
            EligibilityCheck(criterion="Degree Level Compatibility", met=True, detail="Supports 1-year Master's degree programmes."),
            EligibilityCheck(criterion="Full Funding Support", met=True, detail="Covers 100% tuition, monthly living allowance, return airfare."),
            EligibilityCheck(criterion="Nationality Eligibility", met=True, detail="Open to 160+ eligible countries worldwide."),
        ],
        match_reasons=[
            "Supports Master's degree studies in the United Kingdom.",
            "100% full funding covers tuition and living stipend ($0 budget fit).",
            "Open to international applicants.",
            "Application is active for the 2026/2027 intake.",
        ],
        match_score=0.92,
        application_url="https://www.chevening.org/scholarships/",
        source_url="https://www.chevening.org/",
        source_domain="Chevening",
        verification_status=VerificationStatus.VERIFIED,
        raw_excerpt="[Official Portal Verified] The Chevening Scholarship is the UK Government’s premier global award funded by the FCDO. Awards provide full financial support for study at any UK university.",
        is_demo=True,
    ),
    Scholarship(
        name="Gates Cambridge Scholarship",
        provider="University of Cambridge",
        country="United Kingdom",
        degree_levels=[DegreeLevel.MASTER, DegreeLevel.PHD],
        field_tags=["Any field"],
        funding_type=FundingType.FULL,
        annual_value_usd=45000,
        deadline=date(2026, 12, 15),
        eligibility_notes=(
            "Open to citizens of all countries outside the UK. Highly competitive. "
            "Strong academic record required. Covers full cost of studying at Cambridge including maintenance."
        ),
        eligibility_status=EligibilityStatus.LIKELY_ELIGIBLE,
        eligibility_checks=[
            EligibilityCheck(criterion="Application Deadline Status", met=True, detail="Open (Target deadline: 15 Dec 2026)."),
            EligibilityCheck(criterion="Degree Level Compatibility", met=True, detail="Supports Master's and PhD programs at Cambridge."),
            EligibilityCheck(criterion="Academic Excellence", met=True, detail="Requires competitive academic record."),
            EligibilityCheck(criterion="Destination Fit", met=True, detail="Located in Cambridge, United Kingdom."),
        ],
        match_reasons=[
            "Direct match for Master's and PhD degree levels.",
            "Comprehensive full funding including living allowance and visa costs.",
            "High academic alignment with University of Cambridge research.",
        ],
        match_score=0.88,
        application_url="https://www.gatescambridge.org/",
        source_url="https://www.gatescambridge.org/",
        source_domain="Gatescambridge",
        verification_status=VerificationStatus.VERIFIED,
        raw_excerpt="[Official Portal Verified] Gates Cambridge offers 80 full-cost scholarships each year to outstanding applicants outside the UK to pursue a postgraduate degree in any subject at Cambridge.",
        is_demo=True,
    ),
    Scholarship(
        name="DAAD Development-Related Postgraduate Courses (EPOS)",
        provider="German Academic Exchange Service",
        country="Germany",
        degree_levels=[DegreeLevel.MASTER, DegreeLevel.PHD],
        field_tags=["Engineering", "Computer Science", "Economics", "Natural Sciences"],
        funding_type=FundingType.FULL,
        annual_value_usd=20000,
        deadline=date(2026, 10, 31),
        eligibility_notes=(
            "Open to graduates from developing and emerging countries with at least 2 years "
            "of professional experience. Monthly stipend of €934 plus health insurance and travel allowance."
        ),
        eligibility_status=EligibilityStatus.ELIGIBLE,
        eligibility_checks=[
            EligibilityCheck(criterion="Application Deadline Status", met=True, detail="Open (Deadline: 31 Oct 2026)."),
            EligibilityCheck(criterion="Degree Level Compatibility", met=True, detail="Supports Master's degree programs in Germany."),
            EligibilityCheck(criterion="Full Funding Quantum", met=True, detail="Covers €934/month stipend, travel, and health insurance."),
            EligibilityCheck(criterion="Regional Eligibility", met=True, detail="Open to international scholars from target countries."),
        ],
        match_reasons=[
            "Master's degree funding in Germany.",
            "Generous monthly living allowance and health insurance included.",
            "Open to candidates in Computer Science and STEM disciplines.",
        ],
        match_score=0.85,
        application_url="https://www.daad.de/en/",
        source_url="https://www.daad.de/en/",
        source_domain="Daad",
        verification_status=VerificationStatus.VERIFIED,
        raw_excerpt="[Official Portal Verified] DAAD EPOS offers individual scholarships to participants from developing countries to study development-related postgraduate courses at selected German universities.",
        is_demo=True,
    ),
    Scholarship(
        name="Commonwealth Shared Scholarship (Previous Cycle)",
        provider="Commonwealth Scholarship Commission",
        country="United Kingdom",
        degree_levels=[DegreeLevel.MASTER],
        field_tags=["Development", "Science", "Technology"],
        funding_type=FundingType.FULL,
        annual_value_usd=32000,
        deadline=date(2025, 12, 18),
        eligibility_notes=(
            "Commonwealth Shared Scholarships support students from developing Commonwealth countries. "
            "Applications for the 2025/2026 cycle have officially closed."
        ),
        eligibility_status=EligibilityStatus.INELIGIBLE,
        eligibility_checks=[
            EligibilityCheck(criterion="Application Deadline Status", met=False, detail="Application closed on 18 Dec 2025. Past deadline."),
            EligibilityCheck(criterion="Degree Level Compatibility", met=True, detail="Master's level award."),
        ],
        match_reasons=[
            "⛔ Application closed on 18 Dec 2025 (past deadline). Check portal for next annual cycle.",
            "Historical full funding match for Commonwealth scholars.",
        ],
        match_score=0.35,
        application_url="https://cscuk.fcdo.gov.uk/scholarships/commonwealth-shared-scholarships/",
        source_url="https://cscuk.fcdo.gov.uk/",
        source_domain="Cscuk",
        verification_status=VerificationStatus.VERIFIED,
        raw_excerpt="[Official Portal Verified] Applications for 2025 Commonwealth Shared Scholarships are now closed. Details for the next cohort will be published in late 2026.",
        is_demo=True,
    ),
]


# ── Status Pill Helpers ───────────────────────────────────────────────────────

def _eligibility_pill(status: EligibilityStatus) -> str:
    mapping = {
        EligibilityStatus.ELIGIBLE: ("pill-green", "✓ Eligible"),
        EligibilityStatus.LIKELY_ELIGIBLE: ("pill-teal", "~ Likely Eligible"),
        EligibilityStatus.CHECK_REQUIRED: ("pill-amber", "⚠ Check Required"),
        EligibilityStatus.INELIGIBLE: ("pill-red", "✗ Ineligible"),
        EligibilityStatus.UNKNOWN: ("pill-grey", "? Eligibility Unknown"),
    }
    cls, label = mapping.get(status, ("pill-grey", "Unknown"))
    return f'<span class="pill {cls}">{label}</span>'


def _funding_pill(funding: FundingType) -> str:
    label = funding.value
    cls = "pill-green" if funding == FundingType.FULL else "pill-teal" if funding == FundingType.PARTIAL else "pill-grey"
    return f'<span class="pill {cls}">{label}</span>'


def _verification_pill(status: VerificationStatus) -> str:
    if status == VerificationStatus.VERIFIED:
        return '<span class="pill pill-green">✓ Source Verified</span>'
    elif status == VerificationStatus.UNVERIFIED:
        return '<span class="pill pill-amber">⚠ Snippet Evidence</span>'
    return '<span class="pill pill-grey">? Unverified</span>'


def _clean_display_snippet(text: str, max_chars: int = 300) -> str:
    """
    Sanitize scraped web text for card display:
    - Removes markdown table pipes (| col | col |) and table separator rows
    - Strips markdown heading symbols (###, ##)
    - Condenses whitespace and line breaks
    Purely cosmetic for rendering; does not mutate source data.
    """
    if not text:
        return ""
    lines: list[str] = []
    for line in text.splitlines():
        line_s = line.strip()
        # Drop table delimiter lines or rows full of pipes
        if line_s.startswith("|") and line_s.endswith("|"):
            continue
        # Drop lines that are pure markdown table separators like |---|---|
        if set(line_s).issubset({"|", "-", " ", ":"}):
            continue
        # Strip markdown header hashes
        cleaned_line = re.sub(r"^#{1,6}\s*", "", line_s)
        if cleaned_line:
            lines.append(cleaned_line)
    joined = " ".join(lines)
    condensed = re.sub(r"\s+", " ", joined).strip()
    if len(condensed) > max_chars:
        return condensed[:max_chars].rstrip() + "…"
    return condensed


def _match_badge(score: Optional[float]) -> str:
    if score is None:
        return ""
    pct = int(score * 100)
    colour = "#4ade80" if pct >= 80 else "#5ce0d8" if pct >= 65 else "#fbbf24" if pct >= 50 else "#f87171"
    bg = "rgba(74, 222, 128, 0.12)" if pct >= 80 else "rgba(92, 224, 216, 0.12)" if pct >= 65 else "rgba(251, 191, 36, 0.12)" if pct >= 50 else "rgba(248, 113, 113, 0.12)"
    return f'<div class="match-badge" style="color:{colour};background:{bg};border-color:{colour};">{pct}% Match</div>'


def _deadline_pill(deadline: Optional[date]) -> str:
    if deadline is None:
        return '<span class="pill pill-grey">📅 Rolling / Check Portal</span>'
    today = date.today()
    days_left = (deadline - today).days
    if days_left < 0:
        return f'<span class="pill pill-red">⛔ Closed ({deadline.strftime("%d %b %Y")})</span>'
    elif days_left <= 30:
        return f'<span class="pill pill-amber">⚡ Closing Soon ({deadline.strftime("%d %b %Y")})</span>'
    else:
        return f'<span class="pill pill-teal">📅 Deadline: {deadline.strftime("%d %b %Y")}</span>'


def _validate_pdf(uploaded_file) -> Optional[str]:
    """Return an error string or None if the file is valid."""
    if uploaded_file is None:
        return None
    max_bytes = 5 * 1024 * 1024  # 5 MB
    if not uploaded_file.name.lower().endswith(".pdf"):
        return f"'{uploaded_file.name}' is not a PDF. Please upload a .pdf file."
    if uploaded_file.size > max_bytes:
        mb = uploaded_file.size / (1024 * 1024)
        return f"'{uploaded_file.name}' is {mb:.1f} MB. Maximum allowed size is 5 MB."
    return None


# ── Render Helpers ────────────────────────────────────────────────────────────

def render_scholarship_card(s: Scholarship) -> None:
    """
    Render a single scholarship card as safe, attractive HTML without Markdown code-block errors.
    """
    degree_pills = "".join(
        f'<span class="pill pill-teal">{d.value}</span>' for d in s.degree_levels
    ) or '<span class="pill pill-grey">Any Level</span>'

    demo_badge = '<span class="pill pill-demo">⚠ DEMO DATA</span>' if s.is_demo else ""

    status_class_map = {
        EligibilityStatus.ELIGIBLE: "status-eligible",
        EligibilityStatus.LIKELY_ELIGIBLE: "status-likely",
        EligibilityStatus.CHECK_REQUIRED: "status-check",
        EligibilityStatus.INELIGIBLE: "status-ineligible",
        EligibilityStatus.UNKNOWN: "",
    }
    status_card_cls = status_class_map.get(s.eligibility_status, "")

    # Sanitize and construct "Why this matches" list cleanly without multiline indentation
    reasons_html = ""
    if s.match_reasons:
        reasons_items = "".join(
            f'<li>{html.escape(_clean_display_snippet(r, 180))}</li>'
            for r in s.match_reasons[:4]
        )
        reasons_html = (
            f'<div class="reasons-box">'
            f'<strong>Why this matches your profile:</strong>'
            f'<ul>{reasons_items}</ul>'
            f'</div>'
        )

    # Clean, styled application link button
    app_link_html = ""
    if s.application_url and s.application_url.startswith(("http://", "https://")):
        domain_label = html.escape(s.source_domain or s.provider or "Official Portal")
        app_link_html = (
            f'<div style="margin-top:0.95rem;">'
            f'<a href="{html.escape(s.application_url)}" target="_blank" class="portal-btn">'
            f'🔗 Official Application Portal ({domain_label}) ↗</a>'
            f'</div>'
        )

    annual_val_html = ""
    if s.annual_value_usd:
        annual_val_html = (
            f'<div style="font-size:0.92rem;color:#4ade80;margin-bottom:0.45rem;font-weight:700;">'
            f'💰 ~${s.annual_value_usd:,.0f} / year funding</div>'
        )

    notes_html = ""
    if s.eligibility_notes:
        clean_notes = html.escape(_clean_display_snippet(s.eligibility_notes, 280))
        notes_html = (
            f'<div style="font-size:0.87rem;color:#b4d2e8;margin-bottom:0.65rem;line-height:1.52;">'
            f'{clean_notes}</div>'
        )

    card_html = (
        f'<div class="scholarship-card {status_card_cls}">'
        f'{_match_badge(s.match_score)}'
        f'<div class="scholarship-name">{html.escape(s.name)} {demo_badge}</div>'
        f'<div class="scholarship-provider">🏛 {html.escape(s.provider)} &nbsp;·&nbsp; 🌍 {html.escape(s.country)}</div>'
        f'<div style="margin-bottom: 0.75rem;">'
        f'{degree_pills}'
        f'{_funding_pill(s.funding_type)}'
        f'{_eligibility_pill(s.eligibility_status)}'
        f'{_verification_pill(s.verification_status)}'
        f'{_deadline_pill(s.deadline)}'
        f'</div>'
        f'{reasons_html}'
        f'{annual_val_html}'
        f'{notes_html}'
        f'{app_link_html}'
        f'</div>'
    )

    st.markdown(card_html, unsafe_allow_html=True)

    # Expandable evidence and deterministic criteria details
    with st.expander(f"🔍 Evidence & Eligibility Breakdown: {s.name}", expanded=False):
        st.markdown(f"**Verification Status:** `{s.verification_status.value}`")
        if s.raw_excerpt:
            st.markdown(f"**Source Evidence / Excerpt:**\n> {s.raw_excerpt}")
        if s.eligibility_checks:
            st.markdown("**Deterministic Eligibility Verification:**")
            for chk in s.eligibility_checks:
                icon = "✅" if chk.met is True else ("❌" if chk.met is False else "❓")
                st.markdown(f"- {icon} **{chk.criterion}**: {chk.detail}")
        if s.source_url:
            st.markdown(f"**Source URL:** [{s.source_url}]({s.source_url})")


def render_agent_event(icon: str, dot_class: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="agent-event">
            <div class="agent-dot {dot_class}"></div>
            <span>{icon} {text}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_results() -> None:
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-icon">🔭</div>
            <div class="empty-text">No scholarships searched yet</div>
            <div class="empty-sub">Fill in your academic profile on the left and click <strong>Find Scholarships</strong> to start the multi-agent search.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_api_key_missing() -> None:
    st.markdown(
        """
        <div class="warn-box">
            <strong style="font-size:1.02rem;color:#ffe9b3;">🔑 Tavily Search API Key Not Configured</strong><br>
            Live scholarship search requires an active Tavily API key.<br><br>
            <strong>Setup Options:</strong>
            <ol style="margin:0.5rem 0 0 1.2rem;padding:0;color:#ffe9b3;">
                <li><strong>Option A (Sidebar):</strong> Enter your key in the API Configuration panel in the sidebar.</li>
                <li><strong>Option B (.env file):</strong> Add <code>TAVILY_API_KEY=tvly-...</code> to <code>.env</code> in your project root.</li>
                <li>Get a free key at <a href="https://tavily.com" target="_blank" style="color:#5ce0d8;font-weight:700;">tavily.com</a>.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Session state init ────────────────────────────────────────────────────────

def _init_state() -> None:
    defaults = {
        "search_result": None,
        "agent_events": [],
        "searched_once": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ── Main app ──────────────────────────────────────────────────────────────────

def main() -> None:
    _init_state()

    # Inject CSS
    st.markdown(load_css(), unsafe_allow_html=True)

    # ── Sidebar: Key Configuration & Architecture ─────────────────────────────
    with st.sidebar:
        st.markdown("### 🔑 Search Engine Status")
        active_key = get_tavily_key()
        has_key = bool(active_key and not active_key.startswith("tvly-xxx"))

        if has_key:
            st.success("✅ Tavily API Key Active")
            st.caption("Live web discovery and source verification are fully enabled.")
        else:
            st.warning("⚠️ No API Key Detected (Demo Mode)")
            st.markdown(
                "<span style='font-size:0.85rem;color:#c4dcec;'>"
                "To search real scholarships live, enter your Tavily key below:</span>",
                unsafe_allow_html=True,
            )
            key_input = st.text_input(
                "Enter Tavily API Key",
                type="password",
                placeholder="tvly-xxxxxxxxxxxxxxxx",
                help="Your key is kept only in session memory.",
            )
            if key_input and key_input.strip().startswith("tvly-"):
                os.environ["TAVILY_API_KEY"] = key_input.strip()
                st.success("Key applied for this session!")
                if st.button("💾 Save Key to .env"):
                    try:
                        env_path = Path(__file__).resolve().parent / ".env"
                        with open(env_path, "w", encoding="utf-8") as f:
                            f.write(f"TAVILY_API_KEY={key_input.strip()}\n")
                        st.success("Saved to .env! Refreshing...")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Could not save .env: {err}")

        st.markdown("---")
        st.markdown("### 🤖 6-Agent LangGraph Architecture")
        st.markdown(
            """
            - 🧠 **Profile Analyst**: Deconstructs degree & constraint targets
            - 🔭 **Scout**: Multi-query Tavily search with domain filtering
            - 🔍 **Verifier**: Source inspection & authentic proof extraction
            - ⚖️ **Matcher**: Deterministic rule-based eligibility evaluation
            - 🛡️ **Critic**: Result volume audit & adaptive query retry routing
            - 🎓 **Application Coach**: Ranked milestones & grounded SOP drafting
            """
        )

    # ── Header Strip ──────────────────────────────────────────────────────────
    status_badge = (
        '<span class="header-status-badge">⚡ Live Search Engine Active</span>'
        if has_key
        else '<span class="header-status-badge" style="color:#ffb356;border-color:rgba(255,140,0,0.4);background:rgba(255,140,0,0.12);">⚠️ Demo Mode Active</span>'
    )
    st.markdown(
        f"""
        <div class="header-strip">
            <div class="header-branding">
                <span class="header-logo">🎓</span>
                <div>
                    <div class="header-title">ScholarSync AI</div>
                    <div class="header-tagline">TetraNoodle AI Hackathon 2026 &nbsp;&middot;&nbsp; Intelligent Multi-Agent Scholarship Discovery</div>
                </div>
            </div>
            <div>
                {status_badge}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Hero Section (Prominent Heading & Subtitle) ───────────────────────────
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-title">Find Your Scholarships</div>
            <div class="hero-subtitle">
                AI-powered multi-agent intelligence matching your academic profile to global grants, university awards, and fellowships with verified evidence.
            </div>
            <div class="hero-badges-row">
                <span class="hero-pill">🤖 6-Agent LangGraph</span>
                <span class="hero-pill">🛡️ Deterministic Eligibility</span>
                <span class="hero-pill">🌐 Verified Sources</span>
                <span class="hero-pill">📝 Grounded SOP Drafting</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Main Layout: Left Panel (Form) | Right Panel (Results) ───────────────
    left_col, right_col = st.columns([1, 1.35], gap="large")

    # ════════════════════════════════════════════════════════════════════════
    # LEFT COLUMN — Student Profile Form
    # ════════════════════════════════════════════════════════════════════════
    with left_col:
        # ── Academic Profile ────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown('<div class="section-title">🎓 Academic Profile</div>', unsafe_allow_html=True)

            degree_level = st.selectbox(
                "Degree Level *",
                options=[d.value for d in DegreeLevel if d != DegreeLevel.ANY],
                index=1,  # Master's default
                help="The degree you are seeking funding for.",
            )

            field_of_study = st.text_input(
                "Field of Study *",
                placeholder="e.g. Computer Science, Biomedical Engineering, Economics",
                help="Your major or area of specialisation.",
            )

            cgpa = st.number_input(
                "CGPA (optional)",
                min_value=0.0,
                max_value=10.0,
                value=None,
                step=0.01,
                format="%.2f",
                placeholder="e.g. 3.75 (scale 4.0) or 8.5 (scale 10.0)",
                help="Your cumulative GPA. Use your institution's scale (4.0 or 10.0).",
            )

            nationality = st.text_input(
                "Nationality *",
                placeholder="e.g. Indian, Pakistani, Nigerian, Brazilian, American",
                help="Your citizenship — used to filter nationality-specific scholarships.",
            )

        # ── Study Preferences (Searchable 195+ Countries) ────────────────────
        with st.container(border=True):
            st.markdown('<div class="section-title">🌍 Study Preferences</div>', unsafe_allow_html=True)

            preferred_countries = st.multiselect(
                "Preferred Study Countries",
                options=ALL_COUNTRIES,
                default=[],
                placeholder="Search and select countries (e.g. India, Germany, United States)...",
                help="Select one or more destination countries. Searchable dropdown containing 195+ world countries.",
            )

            INTAKE_OPTIONS = [
                "Fall 2026", "Spring 2027", "Fall 2027", "Spring 2028", "Rolling / Flexible",
            ]
            intended_intake = st.selectbox(
                "Intended Intake",
                options=["— Not specified —"] + INTAKE_OPTIONS,
                index=0,
            )

            col_grad, col_budget = st.columns(2)

            with col_grad:
                graduation_year = st.number_input(
                    "Graduation Year",
                    min_value=1990,
                    max_value=2040,
                    value=None,
                    step=1,
                    format="%d",
                    placeholder="e.g. 2025 or 2026",
                    help="Year you completed or expect to complete your current degree.",
                )

            with col_budget:
                annual_budget_usd = st.number_input(
                    "Max Annual Budget (USD)",
                    min_value=0,
                    max_value=200000,
                    value=None,
                    step=500,
                    placeholder="0 = fully funded only",
                    help="Leave blank if flexible. Enter 0 to prioritize fully-funded scholarships.",
                )

        # ── Document Upload ──────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown('<div class="section-title">📄 Documents (Optional)</div>', unsafe_allow_html=True)

            st.markdown(
                '<div class="info-box">PDF files only · Maximum 5 MB each · '
                'Documents are validated for format and size and referenced in your profile context.</div>',
                unsafe_allow_html=True,
            )

            resume_file = st.file_uploader(
                "Resume / CV",
                type=["pdf"],
                accept_multiple_files=False,
                key="resume_upload",
                help="Upload your resume in PDF format (max 5 MB).",
            )

            marksheet_file = st.file_uploader(
                "Academic Transcript / Marksheet",
                type=["pdf"],
                accept_multiple_files=False,
                key="marksheet_upload",
                help="Upload your official transcript in PDF format (max 5 MB).",
            )

            # Validate uploads eagerly
            resume_error = _validate_pdf(resume_file)
            marksheet_error = _validate_pdf(marksheet_file)

            if resume_error:
                st.markdown(f'<div class="error-box">❌ {resume_error}</div>', unsafe_allow_html=True)
            elif resume_file:
                st.markdown(
                    f'<div class="info-box">✅ Resume attached: <strong>{resume_file.name}</strong> '
                    f'({resume_file.size / 1024:.0f} KB)</div>',
                    unsafe_allow_html=True,
                )

            if marksheet_error:
                st.markdown(f'<div class="error-box">❌ {marksheet_error}</div>', unsafe_allow_html=True)
            elif marksheet_file:
                st.markdown(
                    f'<div class="info-box">✅ Marksheet attached: <strong>{marksheet_file.name}</strong> '
                    f'({marksheet_file.size / 1024:.0f} KB)</div>',
                    unsafe_allow_html=True,
                )

        # ── Demo / Failure Simulation Controls ───────────────────────────────
        simulate_failure = st.checkbox(
            "🧪 Simulate Agent Failure & Recovery (Demo Mode)",
            value=False,
            help=(
                "Simulates a network timeout during initial scouting. "
                "The Critic detects the failure, adapts queries, and re-routes "
                "to Scout to demonstrate resilient agent self-healing."
            ),
        )

        # ── Primary CTA ──────────────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        search_clicked = st.button(
            "🔍  Find Scholarships",
            use_container_width=True,
            type="primary",
        )

    # ════════════════════════════════════════════════════════════════════════
    # SEARCH EXECUTION (Runs when button clicked)
    # ════════════════════════════════════════════════════════════════════════

    if search_clicked:
        validation_errors: list[str] = []

        if not field_of_study.strip():
            validation_errors.append("Field of Study is required.")
        if not nationality.strip():
            validation_errors.append("Nationality is required.")
        if resume_error:
            validation_errors.append(f"Fix resume upload: {resume_error}")
        if marksheet_error:
            validation_errors.append(f"Fix marksheet upload: {marksheet_error}")

        if validation_errors:
            with right_col:
                st.markdown("### ⚠️ Please fix the following before searching:")
                for err in validation_errors:
                    st.markdown(
                        f'<div class="error-box">❌ {err}</div>',
                        unsafe_allow_html=True,
                    )
        else:
            # Build validated StudentProfile
            try:
                profile = StudentProfile(
                    degree_level=DegreeLevel(degree_level),
                    field_of_study=field_of_study.strip(),
                    cgpa=float(cgpa) if cgpa is not None else None,
                    nationality=nationality.strip(),
                    preferred_countries=preferred_countries,
                    intended_intake=None if intended_intake.startswith("—") else intended_intake,
                    graduation_year=int(graduation_year) if graduation_year is not None else None,
                    annual_budget_usd=float(annual_budget_usd) if annual_budget_usd is not None else None,
                    resume_filename=resume_file.name if resume_file and not resume_error else None,
                    marksheet_filename=marksheet_file.name if marksheet_file and not marksheet_error else None,
                )
            except Exception as exc:
                with right_col:
                    st.markdown(
                        f'<div class="error-box">❌ Profile validation error: {exc}</div>',
                        unsafe_allow_html=True,
                    )
                st.stop()

            # Execute LangGraph 6-Agent Pipeline
            with right_col:
                with st.spinner("🤖 Multi-agent team scouting & verifying opportunities (LangGraph workflow)…"):
                    result: SearchResult = run_scholar_pipeline(
                        profile,
                        simulation_mode=simulate_failure,
                    )
                    # If API key is missing, populate demo SOP draft for preview
                    if result.api_key_missing and DEMO_SCHOLARSHIPS:
                        result.sop_draft = generate_sop_draft(profile, DEMO_SCHOLARSHIPS[0])

            st.session_state["search_result"] = result
            st.session_state["searched_once"] = True

            # Record agent events
            if result.workflow_events:
                events = [
                    (ev.get("icon", "🔵"), ev.get("dot_class", "dot-teal"), ev.get("message", ""))
                    for ev in result.workflow_events
                ]
            else:
                events = []
                now = datetime.now().strftime("%H:%M:%S")
                events.append(("🟢", "dot-teal", f"[{now}] Profile validated for {profile.nationality} student"))
                events.append(("🔵", "dot-teal", f"[{now}] Query built: \"{result.query_used or 'n/a'}\""))
                if result.api_key_missing:
                    events.append(("🟡", "dot-amber", f"[{now}] Search skipped — TAVILY_API_KEY not configured"))
                elif result.success:
                    events.append(("✅", "dot-green", f"[{now}] Search completed — {result.total_found} results returned"))
                else:
                    events.append(("❌", "dot-grey", f"[{now}] Search failed: {result.error_message}"))

            st.session_state["agent_events"] = events

    # ════════════════════════════════════════════════════════════════════════
    # RIGHT COLUMN — Results & Agent Activity
    # ════════════════════════════════════════════════════════════════════════

    result: Optional[SearchResult] = st.session_state.get("search_result")
    searched_once: bool = st.session_state.get("searched_once", False)

    with right_col:
        st.markdown('<div class="section-title" style="font-size:1.18rem;margin-bottom:1.1rem;">🏆 Scholarship Results</div>', unsafe_allow_html=True)

        if not searched_once:
            render_empty_results()

        elif result is not None:
            # API key missing -> clearly labeled DEMO MODE
            if result.api_key_missing:
                render_api_key_missing()
                st.markdown("---")
                st.markdown(
                    '<div class="demo-banner">⚠️ <strong>DEMO MODE ACTIVE</strong> — '
                    'No active <code>TAVILY_API_KEY</code> was found. The scholarships shown below are '
                    '<strong>curated sample opportunities</strong> for demonstration purposes. '
                    'They are NOT live web search results. Configure your Tavily API key in the sidebar or <code>.env</code> to execute live web searches.</div>',
                    unsafe_allow_html=True,
                )

                if result.sop_draft:
                    with st.expander("📝 Statement of Purpose (SOP) Draft (Demo Preview)", expanded=False):
                        st.markdown(
                            '<div class="info-box" style="margin-bottom:0.75rem;">'
                            'ℹ️ <strong>Academic Integrity Guarantee:</strong> This Statement of Purpose draft is tailored '
                            'to the top-ranked match using strictly confirmed student facts from your submission. '
                            'Unverified claims are marked as bracketed reminders for you to personalize.'
                            '</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(result.sop_draft)
                        st.download_button(
                            "📥 Download SOP Draft (.md)",
                            data=result.sop_draft,
                            file_name=f"Statement_of_Purpose_{datetime.now().strftime('%Y%m%d')}.md",
                            mime="text/markdown",
                            use_container_width=True,
                        )

                for s in DEMO_SCHOLARSHIPS:
                    render_scholarship_card(s)

            # Search error
            elif not result.success:
                st.markdown(
                    f'<div class="error-box">❌ <strong>Search error:</strong> {html.escape(result.error_message or "Unknown failure")}</div>',
                    unsafe_allow_html=True,
                )

            # Live results — empty
            elif result.success and len(result.scholarships) == 0:
                st.markdown(
                    '<div class="warn-box">🔍 No live scholarships matched your specific filters. '
                    'Try broadening your field of study, adding more destination countries (or leaving it open), '
                    'or adjusting your budget filter.</div>',
                    unsafe_allow_html=True,
                )

            # Live results — populated
            else:
                today = date.today()
                active_scholarships = [s for s in result.scholarships if not (s.deadline and s.deadline < today)]
                expired_scholarships = [s for s in result.scholarships if (s.deadline and s.deadline < today)]

                # Executive Dashboard Stats Grid
                stats_html = (
                    f'<div class="stats-grid">'
                    f'<div class="stat-tile"><div class="stat-value">{len(active_scholarships)}</div><div class="stat-label">Active Discovered</div></div>'
                    f'<div class="stat-tile"><div class="stat-value">{result.pages_fetched}</div><div class="stat-label">Official Sources Verified</div></div>'
                    f'<div class="stat-tile"><div class="stat-value">{result.duplicates_removed}</div><div class="stat-label">Duplicates Filtered</div></div>'
                    f'</div>'
                )
                st.markdown(stats_html, unsafe_allow_html=True)

                # SOP Draft Expander
                if result.sop_draft:
                    with st.expander("📝 Opportunity-Tailored Statement of Purpose (SOP) Draft", expanded=False):
                        st.markdown(
                            '<div class="info-box" style="margin-bottom:0.75rem;">'
                            'ℹ️ <strong>Academic Integrity Guarantee:</strong> This Statement of Purpose draft is tailored '
                            'to the top-ranked match using strictly confirmed student facts from your submission. '
                            'Unverified claims are marked as bracketed reminders for you to personalize.'
                            '</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(result.sop_draft)
                        st.download_button(
                            "📥 Download SOP Draft (.md)",
                            data=result.sop_draft,
                            file_name=f"Statement_of_Purpose_{datetime.now().strftime('%Y%m%d')}.md",
                            mime="text/markdown",
                            use_container_width=True,
                        )

                # Active / Open Scholarships Feed
                for s in active_scholarships:
                    render_scholarship_card(s)

                # Expired / Past Cycles Separated
                if expired_scholarships:
                    with st.expander(f"⛔ Past / Closed Cycles ({len(expired_scholarships)} opportunities)", expanded=False):
                        st.caption("These opportunities matched your discipline but their deadlines have passed for the current cycle. Monitor their official portals for the next cohort.")
                        for s in expired_scholarships:
                            render_scholarship_card(s)

        st.markdown("---")

        # ── Agent Activity Section (LangGraph Multi-Agent Workflow) ───────────
        st.markdown(
            '<div class="section-title" style="font-size:1.08rem;margin-top:1.5rem;">⚙️ Agent Activity (LangGraph Multi-Agent Workflow)</div>',
            unsafe_allow_html=True,
        )

        agent_events: list[tuple[str, str, str]] = st.session_state.get("agent_events", [])

        if not agent_events:
            st.markdown(
                '<div style="color:#7b9ab8;font-size:0.9rem;padding:0.5rem 0;">'
                'No events yet — run a search to see the 6-agent LangGraph workflow execution.</div>',
                unsafe_allow_html=True,
            )
        else:
            with st.container(border=True):
                for icon, dot_cls, text in agent_events:
                    render_agent_event(icon, dot_cls, text)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        """
        <hr style="border-color:rgba(92,224,216,0.15);"/>
        <div style="text-align:center;font-size:0.84rem;color:#7b9ab8;padding:0.5rem 0 1.5rem;">
        ScholarSync AI &nbsp;&middot;&nbsp; TetraNoodle AI Hackathon 2026 &nbsp;&middot;&nbsp;
            Always verify scholarship details on the official provider's website before applying. &nbsp;&middot;&nbsp;
            <a href="https://tavily.com" target="_blank" style="color:#5ce0d8;text-decoration:none;font-weight:600;">Powered by Tavily Search & LangGraph</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
