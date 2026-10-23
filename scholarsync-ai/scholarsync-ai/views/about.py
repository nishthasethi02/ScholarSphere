# -*- coding: utf-8 -*-
"""
views/about.py
--------------
About / Architecture Page — In-depth breakdown of the 6-agent LangGraph pipeline,
source verification methodology, and platform FAQ.
"""

from __future__ import annotations
import streamlit as st


def render_about_page() -> None:
    """Render the architecture breakdown and FAQ page."""
    st.markdown('<div class="hero-title" style="font-size:2.1rem;margin-bottom:0.4rem;">How ScholarSphere Works</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#A79FC4;font-size:0.95rem;margin-bottom:1.6rem;">'
        'A transparent look into our 6-agent LangGraph orchestration, deterministic criteria evaluation, and official source proof extraction.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── 1. The 6-Agent LangGraph Pipeline ────────────────────────────────────
    st.markdown('<div class="section-title">6-Agent LangGraph Architecture</div>', unsafe_allow_html=True)

    agents_data = [
        ("Profile Analyst", "Deconstructs constraints",
         "Parses student degree level, field of study, citizenship restrictions, and maximum budget into concrete search vectors."),
        ("Scout", "Multi-query targeted web discovery",
         "Executes focused queries via Tavily with domain exclusion (blocking social media, forums, and commercial aggregators) to capture primary grant pages."),
        ("Verifier", "Authentic page inspection",
         "Crawls candidate source URLs, extracts textual evidence, verifies active intake cycles, and flags unsupported claims as UNKNOWN."),
        ("Matcher", "Deterministic rule evaluation",
         "Applies objective per-criterion checks (deadline status, degree compatibility, nationality eligibility, budget fit) to calculate grounded match percentages."),
        ("Critic", "Quality & volume audit",
         "Audits result sets for sufficient candidate depth; if network errors occur or volume is low, formulates refined queries and routes back for bounded self-healing retries."),
        ("Application Coach", "Actionable application support",
         "Ranks final validated scholarships and generates an opportunity-tailored Statement of Purpose grounded strictly in verified profile facts."),
    ]

    for name, subtitle, desc in agents_data:
        with st.container(border=True):
            st.markdown(
                f"""
                <div>
                    <strong style="font-size:1.05rem;color:#ffffff;">{name}</strong>
                    <span style="font-size:0.8rem;color:#B9A6FF;margin-left:0.5rem;font-weight:700;">— {subtitle}</span>
                    <div style="font-size:0.88rem;color:#A79FC4;margin-top:0.35rem;line-height:1.5;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 2. Verification & Integrity Principles ───────────────────────────────
    st.markdown('<div class="section-title">Academic Integrity & Verification Principles</div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            """
            - **No Hallucinations**: ScholarSphere does not invent scholarships, funding quanta, or application requirements. If an excerpt does not state a detail, it is marked `UNKNOWN`.
            - **Official Portals First**: Search queries prioritize official `.edu`, `.gov`, `.org`, and university grant portals over clickbait scholarship listing aggregators.
            - **Past Cycle Flagging**: Opportunities with past deadlines are explicitly highlighted as closed, preventing wasted applicant time while allowing users to monitor upcoming cohorts.
            - **Grounded SOP Drafting**: The Application Coach drafts statements based strictly on user-supplied details, inserting clear bracketed prompts `[...]` for personal reflections.
            """
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 3. Frequently Asked Questions ────────────────────────────────────────
    st.markdown('<div class="section-title">Frequently Asked Questions (FAQ)</div>', unsafe_allow_html=True)

    faqs = [
        ("Where does ScholarSphere get its scholarship data?",
         "ScholarSphere searches the live web using the Tavily Search API, querying university websites, international exchange portals (like DAAD, Chevening, Fulbright), and government grant programs matching your specific field and nationality."),
        ("What is the difference between Live Search and Demo Mode?",
         "When an active `TAVILY_API_KEY` is configured in `.env` or entered in the sidebar, the app performs real-time multi-agent web discovery. When no key is present, the app operates in Demo Mode displaying curated benchmark opportunities so you can safely preview the full interface."),
        ("How does the Failure Simulation mode work?",
         "Checking 'Simulate Agent Failure & Recovery' intentionally triggers a simulated scout timeout on the first pass. The Critic detects the failure, adapts the queries, and automatically routes back to the Scout to demonstrate resilient agent self-healing."),
        ("Are my uploaded documents sent to third-party databases?",
         "No. Your resume and transcripts are validated locally for format and size and referenced only within your local session profile context."),
    ]

    for q, a in faqs:
        with st.expander(q, expanded=False):
            st.markdown(f"<div style='color:#E4DEF7;line-height:1.55;'>{a}</div>", unsafe_allow_html=True)


render_about_page()
