# -*- coding: utf-8 -*-
"""
views/home.py
-------------
Home Page — Two-column Hero, Interactive AI Search Preview, Animated AI Orb,
Trust Indicators, and Feature Cards with interactive details.
"""

from __future__ import annotations

import streamlit as st


def map_hero_query(query: str) -> dict:
    """
    Transparently map keyword intents into profile preference fields.
    Does NOT call any LLM; provides deterministic keyword prefilling.
    """
    q = query.lower().strip()
    prefill: dict = {}
    matched_labels: list[str] = []

    # Degree Level mapping
    if any(k in q for k in ["master", "msc", "ms", "postgraduate", "graduate"]):
        prefill["degree_level"] = "Master's Degree"
        matched_labels.append("Master's")
    elif any(k in q for k in ["undergrad", "bachelor", "bsc", "ba"]):
        prefill["degree_level"] = "Bachelor's Degree"
        matched_labels.append("Bachelor's")
    elif any(k in q for k in ["phd", "doctor", "doctorate"]):
        prefill["degree_level"] = "PhD / Doctorate"
        matched_labels.append("PhD")

    # Region & Country mapping
    if "europe" in q:
        prefill["preferred_countries"] = [
            "Germany", "United Kingdom", "France", "Netherlands",
            "Sweden", "Switzerland", "Ireland",
        ]
        matched_labels.append("Europe")
    elif "united kingdom" in q or "uk" in q:
        prefill["preferred_countries"] = ["United Kingdom"]
        matched_labels.append("United Kingdom")
    elif any(k in q for k in ["united states", "usa", "us"]):
        prefill["preferred_countries"] = ["United States"]
        matched_labels.append("United States")
    elif "germany" in q:
        prefill["preferred_countries"] = ["Germany"]
        matched_labels.append("Germany")
    elif "canada" in q:
        prefill["preferred_countries"] = ["Canada"]
        matched_labels.append("Canada")
    elif "india" in q:
        prefill["preferred_countries"] = ["India"]
        matched_labels.append("India")

    # Funding preference
    if any(k in q for k in ["fully funded", "full fund", "100%", "full scholarship", "free"]):
        prefill["max_annual_budget_usd"] = 0.0
        matched_labels.append("Fully Funded")

    if matched_labels:
        prefill["note"] = f"{query.strip()} · Prefilled: {', '.join(matched_labels)}"
    else:
        prefill["note"] = query.strip()

    return prefill


def apply_prefill_and_navigate(query_text: str) -> None:
    """Store mapped prefill in session state and navigate to the Search page."""
    prefill = map_hero_query(query_text)
    st.session_state["hero_prefill"] = prefill
    if "profile_data" not in st.session_state:
        st.session_state["profile_data"] = {}
    for k, v in prefill.items():
        if k != "note":
            st.session_state["profile_data"][k] = v
    st.switch_page("views/search.py")


def render_home_page() -> None:
    """Render the redesigned landing home page."""
    # ── 1. Hero Section (Two-Column 55% / 45%) ─────────────────────────────────
    col_left, col_right = st.columns([1.22, 0.78], gap="large")

    with col_left:
        st.markdown(
            """
            <div class="hero-left">
                <div class="hero-eyebrow">Intelligent Scholarship Discovery</div>
                <h1 class="hero-headline">
                    Your <span class="gradient-text">next big opportunity</span> starts here.
                </h1>
                <div class="hero-subtitle">
                    AI-powered multi-agent intelligence matching your academic profile to global grants,
                    university awards, and fellowships with verified official evidence.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Interactive AI Search Preview ──────────────────────────────────────
        st.markdown(
            '<div style="font-size:0.75rem;font-weight:700;letter-spacing:0.08em;color:#8C83A8;text-transform:uppercase;margin-bottom:0.4rem;">'
            'Quick Search Intent'
            '</div>',
            unsafe_allow_html=True,
        )
        c_query, c_submit = st.columns([3.2, 1.1])
        with c_query:
            query_val = st.text_input(
                "Describe your scholarship goals",
                placeholder="Describe your scholarship goals…",
                label_visibility="collapsed",
                key="hero_search_input",
            )
        with c_submit:
            submit_clicked = st.button("Explore →", key="hero_search_submit", use_container_width=True)

        if submit_clicked and query_val.strip():
            apply_prefill_and_navigate(query_val)

        # Quick prompt chips
        st.markdown(
            '<div style="font-size:0.72rem;color:#7B7298;font-weight:600;letter-spacing:0.05em;text-transform:uppercase;margin-top:0.35rem;margin-bottom:0.3rem;">'
            'Popular criteria:'
            '</div>',
            unsafe_allow_html=True,
        )
        ch1, ch2, ch3 = st.columns(3)
        with ch1:
            if st.button("Fully funded master's", key="chip_master", use_container_width=True):
                apply_prefill_and_navigate("Fully funded master's")
        with ch2:
            if st.button("Study in Europe", key="chip_europe", use_container_width=True):
                apply_prefill_and_navigate("Study in Europe")
        with ch3:
            if st.button("Undergraduate awards", key="chip_undergrad", use_container_width=True):
                apply_prefill_and_navigate("Undergraduate scholarships")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Primary & Secondary Action CTAs ────────────────────────────────────
        cta1, cta2 = st.columns([1.3, 1.2])
        with cta1:
            if st.button("Find Your Scholarships →", type="primary", use_container_width=True, key="hero_primary_cta"):
                st.switch_page("views/search.py")
        with cta2:
            if st.button("Explore How It Works", type="secondary", use_container_width=True, key="hero_secondary_cta"):
                st.switch_page("views/about.py")

        # ── Trust Indicators (Three Compact Badges) ───────────────────────────
        st.markdown(
            """
            <div class="trust-indicators-row">
                <div class="trust-indicator">
                    <span class="trust-dot"></span>
                    <span>6-Agent LangGraph Team</span>
                </div>
                <div class="trust-indicator">
                    <span class="trust-dot"></span>
                    <span>Verified Source Proof</span>
                </div>
                <div class="trust-indicator">
                    <span class="trust-dot"></span>
                    <span>Deterministic Match Scoring</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        # ── Animated Glowing AI Orb Stage ─────────────────────────────────────
        st.markdown(
            """
            <div class="hero-orb-wrapper">
                <div class="hero-orb-stage" title="ScholarSphere Intelligent Core">
                    <div class="orb-ring orb-ring-1"></div>
                    <div class="orb-ring orb-ring-2"></div>
                    <div class="orb-ring orb-ring-3"></div>
                    <div class="orb-core"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── 2. Feature Cards (Equal Height, Subtle Glassmorphism, Clean Details) ──
    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        with st.container(border=True):
            st.markdown(
                """
                <div class="feature-title">Multi-Agent Discovery</div>
                <div class="feature-desc">
                    Coordinated LangGraph agents formulate specialized search queries across 195+ countries
                    and systematically filter aggregators to isolate official scholarship portals.
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("Technical Details", expanded=False):
                st.markdown(
                    """
                    <div style="font-size:0.83rem;color:#C4BCD8;line-height:1.5;">
                        • <strong>Profile Analyst</strong> extracts target degree, GPA threshold, and nationality criteria.<br>
                        • <strong>Scout Agent</strong> queries the web using dynamic negative operators (excluding scraper aggregators).<br>
                        • Deduplicates and canonicalizes URLs across multi-query sweeps.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with col2:
        with st.container(border=True):
            st.markdown(
                """
                <div class="feature-title">Verified Source Proof</div>
                <div class="feature-desc">
                    Eliminates hallucinations by inspecting provider web sources directly to verify live application
                    cycle deadlines, degree levels, and funding quanta before matching.
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("Technical Details", expanded=False):
                st.markdown(
                    """
                    <div style="font-size:0.83rem;color:#C4BCD8;line-height:1.5;">
                        • <strong>Verifier Agent</strong> fetches official page snippets and validates institutional authority.<br>
                        • Flags expired cycles and confirms degree compatibility.<br>
                        • Attaches verifiable evidence quotes directly to each scholarship record.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    with col3:
        with st.container(border=True):
            st.markdown(
                """
                <div class="feature-title">Grounded SOP Drafting</div>
                <div class="feature-desc">
                    Produces an opportunity-tailored Statement of Purpose draft grounded strictly in confirmed student
                    facts from your verified profile and uploaded credentials.
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("Technical Details", expanded=False):
                st.markdown(
                    """
                    <div style="font-size:0.83rem;color:#C4BCD8;line-height:1.5;">
                        • <strong>Application Coach</strong> cites exact alignments between candidate background and award criteria.<br>
                        • Strictly anti-hallucinatory: never fabricates publications, grades, or personal awards.<br>
                        • Provides instant exportable draft ready for institutional customization.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown("<br>", unsafe_allow_html=True)


render_home_page()
