# -*- coding: utf-8 -*-
"""
views/results.py
----------------
Results Page — Metric summary tiles, scholarship cards, shortlist bookmarks,
and navigation to SOP workbench.
"""

from __future__ import annotations

import html
from datetime import date
from typing import Optional

import streamlit as st

from components.cards import render_scholarship_card
from components.empty_state import render_api_key_missing, render_empty_results
from models.opportunity import Scholarship, SearchResult


def render_results_page() -> None:
    """Render the scholarship search results feed and stats."""
    st.markdown('<div class="hero-title" style="font-size:2.1rem;margin-bottom:0.4rem;">🏆 Discovered Scholarships</div>', unsafe_allow_html=True)

    result: Optional[SearchResult] = st.session_state.get("search_result")
    searched_once: bool = st.session_state.get("searched_once", False)

    if not searched_once or result is None:
        render_empty_results(cta_button=True)
        return

    # Check for missing API Key -> Demo Mode
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

        from views.search import DEMO_SCHOLARSHIPS
        for idx, s in enumerate(DEMO_SCHOLARSHIPS):
            render_scholarship_card(s, show_save_button=True, card_key=f"demo_{idx}")
        return

    # Search failure
    if not result.success:
        st.markdown(
            f'<div class="error-box">❌ <strong>Search error:</strong> {html.escape(result.error_message or "Unknown failure")}</div>',
            unsafe_allow_html=True,
        )
        if st.button("🔄 Try Search Again", type="secondary"):
            st.switch_page("views/search.py")
        return

    # Empty results
    if len(result.scholarships) == 0:
        st.markdown(
            '<div class="warn-box">🔍 No live scholarships matched your specific criteria. '
            'Try broadening your field of study, adding more destination countries (or leaving it open), '
            'or adjusting your budget filter.</div>',
            unsafe_allow_html=True,
        )
        if st.button("✏️ Refine Search Parameters", type="primary"):
            st.switch_page("views/search.py")
        return

    # Populated Live Results
    today = date.today()
    active_scholarships = [s for s in result.scholarships if not (s.deadline and s.deadline < today)]
    expired_scholarships = [s for s in result.scholarships if (s.deadline and s.deadline < today)]

    # Executive Dashboard Summary Grid
    stats_html = (
        f'<div class="stats-grid">'
        f'<div class="stat-tile"><div class="stat-value">{len(active_scholarships)}</div><div class="stat-label">Active Opportunities</div></div>'
        f'<div class="stat-tile"><div class="stat-value">{result.pages_fetched}</div><div class="stat-label">Official Sources Verified</div></div>'
        f'<div class="stat-tile"><div class="stat-value">{result.duplicates_removed}</div><div class="stat-label">Duplicates Filtered</div></div>'
        f'</div>'
    )
    st.markdown(stats_html, unsafe_allow_html=True)

    # Quick Navigation / Action Bar
    saved_count = len(st.session_state.get("saved_scholarships", {}))
    c_action1, c_action2, c_action3 = st.columns([1, 1, 1.2])

    with c_action1:
        if st.button("🔍 Refine Search", use_container_width=True):
            st.switch_page("views/search.py")
    with c_action2:
        if st.button(f"★ View Shortlist ({saved_count})", use_container_width=True):
            st.switch_page("views/saved.py")
    with c_action3:
        if result.sop_draft and st.button("📝 Opportunity SOP Draft →", type="primary", use_container_width=True):
            st.switch_page("views/sop.py")

    st.markdown("<br>", unsafe_allow_html=True)

    # Active Scholarships
    for idx, s in enumerate(active_scholarships):
        render_scholarship_card(s, show_save_button=True, card_key=f"act_{idx}")

    # Closed/Past Cycles
    if expired_scholarships:
        with st.expander(f"⛔ Past / Closed Cycles ({len(expired_scholarships)} opportunities)", expanded=False):
            st.caption(
                "These opportunities matched your discipline but their deadlines have passed for the current cycle. "
                "Monitor their official portals for the next cohort."
            )
            for idx, s in enumerate(expired_scholarships):
                render_scholarship_card(s, show_save_button=True, card_key=f"exp_{idx}")


render_results_page()
