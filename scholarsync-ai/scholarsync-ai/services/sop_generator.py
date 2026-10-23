# -*- coding: utf-8 -*-
"""
services/sop_generator.py
--------------------------
Generates an opportunity-specific Statement of Purpose (SOP) / Motivation Letter
draft grounded strictly in confirmed student profile facts.

Integrity Rules:
- Never invents academic accolades, grades, internships, or publications not provided.
- Accurately quotes the student's declared degree, field, nationality, target intake, and CGPA.
- Incorporates specific details of the target scholarship (provider, country, funding).
- Uses clear placeholder markers [Like this] for personal anecdotes the student must supply.
"""

from __future__ import annotations

from typing import Optional

from models.opportunity import Scholarship, StudentProfile


def generate_sop_draft(profile: StudentProfile, scholarship: Scholarship) -> str:
    """
    Generate an opportunity-tailored Statement of Purpose draft using
    only confirmed student facts and verified scholarship attributes.
    """
    degree = profile.degree_level.value
    field = profile.field_of_study
    nationality = profile.nationality
    cgpa_str = f"{profile.cgpa:.2f}" if profile.cgpa is not None else None
    grad_year = profile.graduation_year
    intake = profile.intended_intake or "the upcoming academic session"
    countries = (
        ", ".join(profile.preferred_countries)
        if profile.preferred_countries
        else scholarship.country
    )

    # Academic background sentence grounded in facts
    acad_lines: list[str] = []
    if cgpa_str and grad_year:
        acad_lines.append(
            f"Having maintained an academic cumulative GPA of {cgpa_str} "
            f"with expected completion in {grad_year}, I have built a rigorous foundation "
            f"in {field}."
        )
    elif cgpa_str:
        acad_lines.append(
            f"With a cumulative GPA of {cgpa_str}, I have consistently demonstrated "
            f"dedication and analytical rigor throughout my studies in {field}."
        )
    elif grad_year:
        acad_lines.append(
            f"As a graduate / prospective graduate (Class of {grad_year}) in {field}, "
            f"I have cultivated a focused academic background and problem-solving mindset."
        )
    else:
        acad_lines.append(
            f"Throughout my academic journey in {field}, I have maintained a strong commitment "
            f"to academic excellence and research inquiry."
        )

    # Financial / funding rationale grounded in budget
    if profile.annual_budget_usd == 0:
        funding_rationale = (
            f"As an applicant requiring full financial support to pursue international education, "
            f"the {scholarship.funding_type.value} provided by {scholarship.provider} is essential "
            f"in enabling me to dedicate myself entirely to advanced research and coursework without "
            f"undue financial distress."
        )
    elif profile.annual_budget_usd is not None:
        funding_rationale = (
            f"With a modest annual self-funded budget of approximately ${profile.annual_budget_usd:,.0f} USD, "
            f"the financial assistance from the {scholarship.name} provides the vital backing necessary "
            f"to bridge the cost of tuition and living expenses in {scholarship.country}."
        )
    else:
        funding_rationale = (
            f"Securing the {scholarship.name} offered by {scholarship.provider} would provide the "
            f"necessary resources to pursue this intensive curriculum in {scholarship.country} and maximize "
            f"my academic contributions."
        )

    # Document upload note
    doc_refs: list[str] = []
    if profile.resume_filename:
        doc_refs.append(f"curriculum vitae ({profile.resume_filename})")
    if profile.marksheet_filename:
        doc_refs.append(f"official academic transcripts ({profile.marksheet_filename})")
    doc_statement = ""
    if doc_refs:
        doc_statement = (
            f"As detailed in my attached {' and '.join(doc_refs)}, my academic trajectory "
            f"reflects progressive milestones aligned with this discipline."
        )

    # Deadline notice
    deadline_text = (
        f"Application Target Deadline: {scholarship.deadline.strftime('%d %B %Y')}"
        if scholarship.deadline
        else "Application Target: Rolling / To Be Confirmed with official portal"
    )

    sop_body = f"""# STATEMENT OF PURPOSE & MOTIVATION LETTER

**Applicant:** Citizen of {nationality}
**Target Opportunity:** {scholarship.name}
**Awarding Body / Institution:** {scholarship.provider} ({scholarship.country})
**Target Degree Program:** {degree} in {field}
**Intended Intake:** {intake}
**{deadline_text}**

---

### Dear Selection Committee for the {scholarship.name},

I am writing to formally submit my application for the **{scholarship.name}** administered by **{scholarship.provider}**, to support my pursuit of a **{degree} in {field}** starting {intake}. As a dedicated student from **{nationality}**, my goal is to leverage advanced training in {field} to address critical challenges in the sector and contribute meaningful research to the global academic community.

### Academic Preparation & Qualifications
{" ".join(acad_lines)}
{doc_statement}

[INSERT 1-2 PARAGRAPHS HERE: Summarize your key undergraduate research projects, capstone thesis, or relevant technical coursework. Highlight specific methodologies, software, or laboratory techniques you utilized in {field} without exaggerating results.]

### Alignment with {scholarship.name} and {scholarship.provider}
The mission of {scholarship.provider} aligns directly with my educational priorities in {scholarship.country}. Specifically, {scholarship.name} represents a unique platform for high-potential international scholars:
- **Program & Degree Fit:** This opportunity explicitly supports advanced studies in {degree} programs, perfectly matching my immediate academic progression.
- **Geographic & Research Synergy:** Conducting research in {scholarship.country} offers unparalleled institutional facilities and access to leading faculty investigating contemporary questions in {field}.
- **Community & Leadership:** I aim to represent the academic community of {nationality} as an active, engaged ambassador on campus and within the scholarship cohort.

[INSERT 1 PARAGRAPH HERE: Cite 1-2 specific research groups, professors, or specialized labs at your target institution in {scholarship.country} whose published work resonates with your proposed focus in {field}.]

### Financial Consideration & Impact
{funding_rationale}

Receiving this award will directly empower me to concentrate on rigorous coursework, collaborative research initiatives, and community engagement throughout my tenure in {scholarship.country}.

### Long-Term Vision
Upon completing my {degree} in {field}, I plan to apply the rigorous knowledge acquired through this program toward solving complex technological and societal problems, bridging collaborative partnerships between {scholarship.country} and {nationality}. 

I am deeply grateful for the committee's time, evaluation, and consideration of my candidacy.

Sincerely,  
**Applicant ({nationality})**  
Candidate for {degree} in {field}

---
*Note: This draft was generated by ScholarSphere using verified details from {scholarship.provider} and your confirmed profile. Personalize bracketed sections before official submission.*
"""
    return sop_body.strip()
