# -*- coding: utf-8 -*-
"""
components/cards.py
-------------------
Rendering components for scholarship cards, status pills, and bookmarking.
"""

from __future__ import annotations

import html
import re
from datetime import date
from typing import Optional

import streamlit as st

from models.opportunity import (
    DegreeLevel,
    EligibilityCheck,
    EligibilityStatus,
    FundingType,
    Scholarship,
    VerificationStatus,
)


def _clean_display_snippet(text: str, max_chars: int = 300) -> str:
    """Sanitize scraped web text for card display (removes table pipes & hashes)."""
    if not text:
        return ""
    lines: list[str] = []
    for line in text.splitlines():
        line_s = line.strip()
        if line_s.startswith("|") and line_s.endswith("|"):
            continue
        if set(line_s).issubset({"|", "-", " ", ":"}):
            continue
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
    colour = "#4ADE9A" if pct >= 80 else "#8B6CFF" if pct >= 65 else "#F5B84B" if pct >= 50 else "#F87171"
    bg = "rgba(74, 222, 154, 0.14)" if pct >= 80 else "rgba(139, 108, 255, 0.14)" if pct >= 65 else "rgba(245, 184, 75, 0.14)" if pct >= 50 else "rgba(248, 113, 113, 0.14)"
    return f'<div class="match-badge" style="color:{colour};background:{bg};border-color:{colour};">{pct}% Match</div>'


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


def validate_pdf(uploaded_file) -> Optional[str]:
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

_validate_pdf = validate_pdf


def render_scholarship_card(
    s: Scholarship,
    show_save_button: bool = True,
    card_key: str = "",
) -> None:
    """Render a single scholarship card as safe, attractive HTML with bookmarking."""
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

    annual_val_html = ""
    if s.annual_value_usd:
        annual_val_html = (
            f'<div style="font-size:0.92rem;color:#4ADE9A;margin-bottom:0.45rem;font-weight:700;">'
            f'💰 ~${s.annual_value_usd:,.0f} / year funding</div>'
        )

    notes_html = ""
    if s.eligibility_notes:
        clean_notes = html.escape(_clean_display_snippet(s.eligibility_notes, 280))
        notes_html = (
            f'<div style="font-size:0.87rem;color:#A79FC4;margin-bottom:0.65rem;line-height:1.52;">'
            f'{clean_notes}</div>'
        )

    app_link_html = ""
    if s.application_url and s.application_url.startswith(("http://", "https://")):
        domain_label = html.escape(s.source_domain or s.provider or "Official Portal")
        app_link_html = (
            f'<div style="margin-top:0.95rem;">'
            f'<a href="{html.escape(s.application_url)}" target="_blank" class="portal-btn">'
            f'🔗 Official Application Portal ({domain_label}) ↗</a>'
            f'</div>'
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

    # Actions row: Bookmark toggle & Evidence expander
    col_act1, col_act2 = st.columns([1, 4])
    
    # Initialize saved dictionary if missing
    if "saved_scholarships" not in st.session_state:
        st.session_state["saved_scholarships"] = {}

    is_saved = s.name in st.session_state["saved_scholarships"]

    if show_save_button:
        with col_act1:
            btn_label = "★ Saved" if is_saved else "☆ Shortlist"
            btn_type = "primary" if is_saved else "secondary"
            unique_btn_key = f"save_{card_key}_{hash(s.name)}"
            if st.button(btn_label, key=unique_btn_key, type=btn_type, help="Save to your Shortlist"):
                if is_saved:
                    del st.session_state["saved_scholarships"][s.name]
                else:
                    st.session_state["saved_scholarships"][s.name] = s
                st.rerun()

    # Expandable evidence
    expander_title = f"🔍 Evidence & Eligibility Breakdown: {s.name}"
    with st.expander(expander_title, expanded=False):
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
