# ScholarSphere
AI-powered multi-agent scholarship discovery and verification platform built with Streamlit, LangGraph, and Tavily.


🎓 ScholarSphere AI — Find Your Scholarships
An AI-powered, multi-agent scholarship discovery and verification platform that helps students find relevant scholarship opportunities and prepare stronger applications.

🌟 Overview
ScholarSphere AI simplifies scholarship discovery by using a multi-agent workflow to search for opportunities, verify supporting information, evaluate eligibility, and assist students with application preparation.
Built with Python, Streamlit, LangGraph, and Tavily Search, the platform aims to make scholarship research more organized, transparent, and personalized.

✨ Key Features
🔎 AI-Powered Scholarship Discovery: Searches for scholarship opportunities using web search.
👤 Student Profile Analysis: Uses student information to guide scholarship matching.
✅ Eligibility Matching: Evaluates scholarship requirements against the student's profile.
🔍 Source Verification: Inspects available sources to support scholarship information.
🎯 Result Quality Checks: Reviews search results and supports additional search attempts when needed.
📝 SOP Assistance: Helps students draft a Statement of Purpose for scholarship applications.
📌 Scholarship Management: Provides features for viewing results and managing saved opportunities, where supported by the application.

🤖 Multi-Agent Architecture
ScholarSphere AI uses six specialized agents:
Profile Analyst — Analyzes the student's profile and requirements.
Scout — Searches the web for relevant scholarship opportunities using Tavily.
Verifier — Inspects sources and supporting evidence.
Matcher — Applies eligibility rules to evaluate scholarship relevance.
Critic — Reviews result quality and supports bounded retry logic.
Application Coach — Assists with grounded Statement of Purpose drafting.
Together, these agents organize scholarship discovery into a structured workflow.

🛠️ Tech Stack
Language: Python
Frontend: Streamlit
Agent Workflow: LangGraph

Web Search: Tavily Search API

Data Processing: Python and project-specific data models
