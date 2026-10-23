# -*- coding: utf-8 -*-
"""
app.py - ScholarSphere
----------------------
Central multi-page router for the ScholarSphere platform.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path so local packages resolve correctly.
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from components.footer import render_footer
from components.header import render_header
from services.env_loader import get_tavily_key, load_project_env

# Ensure .env is loaded from root
load_project_env()

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="ScholarSphere — Find Your Scholarships",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Global CSS Loader ─────────────────────────────────────────────────────────
def load_css() -> str:
    """Load the custom stylesheet from styles.css with resilient fallback."""
    css_file = Path(__file__).resolve().parent / "styles.css"
    if css_file.exists():
        try:
            return f"<style>\n{css_file.read_text(encoding='utf-8')}\n</style>"
        except Exception:
            pass
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: #0B0816 !important; color: #F2EEFF !important; }
    </style>
    """


# ── Global State Initialization ───────────────────────────────────────────────
def _init_state() -> None:
    defaults = {
        "search_result": None,
        "agent_events": [],
        "searched_once": False,
        "profile_data": {},
        "saved_scholarships": {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def main() -> None:
    _init_state()

    # Inject Global CSS once for all pages
    st.markdown(load_css(), unsafe_allow_html=True)

    # ── Sidebar: Search Engine Key & Platform Architecture ────────────────────
    with st.sidebar:
        st.markdown("### Search Engine Status")
        active_key = get_tavily_key()
        has_key = bool(active_key and not active_key.startswith("tvly-xxx"))

        if has_key:
            st.success("Tavily API Key Active")
            st.caption("Live web discovery and source verification are fully enabled.")
        else:
            st.warning("No API Key Detected (Demo Mode)")
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
                if st.button("Save Key to .env"):
                    try:
                        env_path = Path(__file__).resolve().parent / ".env"
                        with open(env_path, "w", encoding="utf-8") as f:
                            f.write(f"TAVILY_API_KEY={key_input.strip()}\n")
                        st.success("Saved to .env! Refreshing...")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Could not save .env: {err}")

        st.markdown("---")
        st.markdown("### 6-Agent LangGraph Architecture")
        st.markdown(
            """
            - **Profile Analyst**: Deconstructs targets
            - **Scout**: Multi-query Tavily search
            - **Verifier**: Source inspection & proof
            - **Matcher**: Deterministic rule checks
            - **Critic**: Audit volume & adaptive retry
            - **Application Coach**: Grounded SOP drafting
            """
        )

    # ── Multi-Page Navigation ─────────────────────────────────────────────────
    pages = {
        "Discovery": [
            st.Page("views/home.py", title="Home", default=True),
            st.Page("views/search.py", title="Find Scholarships"),
            st.Page("views/results.py", title="Results"),
        ],
        "Applications": [
            st.Page("views/saved.py", title="Saved / Shortlist"),
            st.Page("views/sop.py", title="SOP Generator"),
        ],
        "Platform": [
            st.Page("views/about.py", title="How It Works"),
        ],
    }

    pg = st.navigation(pages, position="sidebar")

    # Shared global header
    render_header()

    # Execute the selected page
    pg.run()

    # Shared global footer
    render_footer()


if __name__ == "__main__":
    main()
