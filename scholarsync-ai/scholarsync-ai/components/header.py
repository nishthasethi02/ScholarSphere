# -*- coding: utf-8 -*-
"""
components/header.py
--------------------
Global header branding strip displayed across all pages.
"""

from __future__ import annotations
import streamlit as st
from services.env_loader import get_tavily_key


def render_header() -> None:
    """Render the slim top branding strip with real-time API / engine status."""
    active_key = get_tavily_key()
    has_key = bool(active_key and not active_key.startswith("tvly-xxx"))
    is_searching = st.session_state.get("is_searching", False)
    search_status = st.session_state.get("search_status", None)

    if is_searching:
        status_dot = '<span class="status-dot dot-searching"></span>'
        status_text = 'Searching Opportunities…'
        status_class = 'status-badge-searching'
    elif search_status == "error":
        status_dot = '<span class="status-dot dot-error"></span>'
        status_text = 'Search Error'
        status_class = 'status-badge-error'
    elif search_status == "done":
        status_dot = '<span class="status-dot dot-active"></span>'
        status_text = 'Discovery Ready'
        status_class = 'status-badge-active'
    elif has_key:
        status_dot = '<span class="status-dot dot-active"></span>'
        status_text = 'Live Search Active'
        status_class = 'status-badge-active'
    else:
        status_dot = '<span class="status-dot dot-demo"></span>'
        status_text = 'Demo Mode (Offline Data)'
        status_class = 'status-badge-demo'

    st.markdown(
        f"""
        <div class="header-strip">
            <div class="header-branding">
                <span class="header-title">ScholarSphere</span>
            </div>
            <div class="header-actions">
                <div class="header-status-badge {status_class}">
                    {status_dot}
                    <span>{status_text}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
