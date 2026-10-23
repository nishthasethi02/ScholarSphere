# -*- coding: utf-8 -*-
"""
components/footer.py
--------------------
Global footer rendered across all pages.
"""

from __future__ import annotations
import streamlit as st


def render_footer() -> None:
    """Render the global footer disclaimer and credits."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        """
        <hr style="border-color:rgba(140,110,255,0.15);"/>
        <div style="text-align:center;font-size:0.84rem;color:#8C83A8;padding:0.5rem 0 1.5rem;">
            ScholarSphere &nbsp;&middot;&nbsp;
            Always verify scholarship details on the official provider's website before applying. &nbsp;&middot;&nbsp;
            <a href="https://tavily.com" target="_blank" style="color:#B9A6FF;text-decoration:none;font-weight:600;">Powered by Tavily Search & LangGraph</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
