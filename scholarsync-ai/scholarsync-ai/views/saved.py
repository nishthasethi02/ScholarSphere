# -*- coding: utf-8 -*-
"""
views/saved.py
--------------
Saved / Shortlist Page — Manage bookmarked scholarship opportunities,
export shortlist data, and jump to official portals.
"""

from __future__ import annotations

import json
from typing import Any
import streamlit as st

from components.cards import render_scholarship_card
from models.opportunity import Scholarship


def _scholarship_to_dict(s: Scholarship) -> dict[str, Any]:
    """Convert Scholarship object to serializable dictionary for export."""
    return {
        "name": s.name,
        "provider": s.provider,
        "country": s.country,
        "degree_levels": [d.value for d in s.degree_levels],
        "funding_type": s.funding_type.value if hasattr(s.funding_type, "value") else str(s.funding_type),
        "annual_value_usd": s.annual_value_usd,
        "deadline": s.deadline.isoformat() if s.deadline else None,
        "eligibility_status": s.eligibility_status.value if hasattr(s.eligibility_status, "value") else str(s.eligibility_status),
        "match_score": s.match_score,
        "application_url": s.application_url,
        "source_url": s.source_url,
    }


def render_saved_page() -> None:
    """Render the shortlisted / saved scholarships page."""
    st.markdown('<div class="hero-title" style="font-size:2.1rem;margin-bottom:0.4rem;">⭐ Your Saved Shortlist</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#A79FC4;font-size:0.95rem;margin-bottom:1.4rem;">'
        'Keep track of your top-priority scholarships, monitor their deadlines, and export your applications.'
        '</div>',
        unsafe_allow_html=True,
    )

    if "saved_scholarships" not in st.session_state:
        st.session_state["saved_scholarships"] = {}

    saved_items: dict[str, Scholarship] = st.session_state["saved_scholarships"]

    if not saved_items:
        st.markdown(
            """
            <div class="empty-state">
                <div class="empty-icon">⭐</div>
                <div class="empty-text">Your Shortlist is Empty</div>
                <div class="empty-sub">
                    You haven't bookmarked any scholarships yet. Perform a search and click the <strong>☆ Shortlist</strong> button on any card to save it here.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            if st.button("🔍 Explore Discovered Scholarships", type="primary", use_container_width=True):
                st.switch_page("views/results.py")
        return

    # Actions Bar: Total Count + Export JSON + Clear All
    col_info, col_export, col_clear = st.columns([2, 1.2, 0.8])

    with col_info:
        st.markdown(
            f'<div class="info-box" style="margin:0;">'
            f'⭐ <strong>{len(saved_items)}</strong> opportunity bookmarked for your application cycle.'
            f'</div>',
            unsafe_allow_html=True,
        )

    export_data = json.dumps(
        [_scholarship_to_dict(s) for s in saved_items.values()],
        indent=2,
        ensure_ascii=False,
    )

    with col_export:
        st.download_button(
            "Export Shortlist (.json)",
            data=export_data,
            file_name="ScholarSphere_Shortlist.json",
            mime="application/json",
            use_container_width=True,
        )

    with col_clear:
        if st.button("Clear All", use_container_width=True, help="Remove all items from your shortlist"):
            st.session_state["saved_scholarships"].clear()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Render each saved card
    for idx, (name, s) in enumerate(saved_items.items()):
        render_scholarship_card(s, show_save_button=True, card_key=f"saved_{idx}")


render_saved_page()
