# -*- coding: utf-8 -*-
"""
components/empty_state.py
-------------------------
Reusable empty state displays and warning banners.
"""

from __future__ import annotations
import streamlit as st


def render_empty_results(cta_button: bool = True) -> None:
    """Render a clean empty state card when no search has been performed."""
    st.markdown(
        """
        <div class="empty-state">
            <div class="empty-icon">🔭</div>
            <div class="empty-text">No Scholarships Discovered Yet</div>
            <div class="empty-sub">
                Enter your academic profile, preferred destination countries, and degree level to launch the 6-agent discovery pipeline.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if cta_button:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1.2, 1])
        with col2:
            if st.button("🚀 Start New Search", use_container_width=True, type="primary"):
                st.switch_page("views/search.py")


def render_api_key_missing() -> None:
    """Render setup instructions when TAVILY_API_KEY is not configured."""
    st.markdown(
        """
        <div class="warn-box">
            <strong style="font-size:1.02rem;color:#ffe9b3;">🔑 Tavily Search API Key Not Configured</strong><br>
            Live scholarship search requires an active Tavily API key.<br><br>
            <strong>Setup Options:</strong>
            <ol style="margin:0.5rem 0 0 1.2rem;padding:0;color:#ffe9b3;">
                <li><strong>Option A (Sidebar):</strong> Enter your key in the Search Engine Status panel in the sidebar.</li>
                <li><strong>Option B (.env file):</strong> Add <code>TAVILY_API_KEY=tvly-...</code> to <code>.env</code> in your project root.</li>
                <li>Get a free key at <a href="https://tavily.com" target="_blank" style="color:#5ce0d8;font-weight:700;">tavily.com</a>.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )
