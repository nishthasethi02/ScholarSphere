# ScholarSync AI 🎓

**AI-Powered Scholarship Finder & Multi-Agent Application Assistant**  

ScholarSync AI helps students discover scholarships that match their academic profile, nationality, and goals using an intelligent 6-agent orchestration pipeline powered by LangGraph and Tavily Search.

---

## ✨ Features

- **Profile-Driven Multi-Query Search** — Automatically synthesizes multi-angle search queries from student profile parameters (degree level, discipline, nationality, destination countries, budget, and intake).
- **Aggressive Deduplication** — Normalizes canonical URLs (stripping tracking parameters, anchors, trailing slashes) and performs title similarity checks to surface at least 10 unique opportunities.
- **Live Source Page Verification** — Fetches live official scholarship and university pages to confirm deadlines, funding levels (full vs. partial), and direct application links, recording grounded text excerpts.
- **Deterministic Eligibility Checking** — Rule-based checks across 5 core criteria (Degree Level, Field Alignment, Country Fit, Funding/Budget, and CGPA) without LLM hallucinations.
- **LangGraph Multi-Agent Architecture** — 6 specialized agent roles with shared structured state and conditional routing:
  - 🧠 **Profile Analyst**: Deconstructs constraints and formulates search strategies.
  - 🔭 **Scout**: Executes Tavily API searches and deduplicates candidate opportunities.
  - 🔍 **Verifier**: Fetches official source pages to extract verified criteria and evidence.
  - ⚖️ **Matcher**: Computes deterministic eligibility verdicts and grounded match scores.
  - 🛡️ **Critic**: Audits candidate pool quality, detects incomplete or failed searches, and conditionally triggers adaptive query retries.
  - 🎓 **Application Coach**: Prepares ranked recommendations and generates tailored application materials.
- **Grounded Statement of Purpose (SOP) Draft** — Crafts an opportunity-specific Statement of Purpose grounded strictly in confirmed student inputs, using explicit bracketed placeholders for personal narratives.
- **Failure Simulation & Recovery Demo** — Built-in toggle to simulate transient network failure, showing how the Critic detects missing results and triggers an adaptive retry loop to self-heal.
- **Dark Navy & Teal UI** — Polished Streamlit interface with responsive status pills, expandable evidence breakdowns, and live agent activity telemetry.

---

## 🗂 Project Structure

```
scholarsync-ai/
├── app.py                      # Streamlit application UI & entry point
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .gitignore
├── README.md                   # Documentation & setup guide
├── agents/
│   ├── __init__.py             # Agent module exports
│   └── workflow.py             # 6-agent LangGraph workflow & state machine
├── models/
│   ├── __init__.py
│   └── opportunity.py          # Pydantic v2 data schemas
├── services/
│   ├── __init__.py
│   ├── scholarship_search.py   # Tavily search, deduplication & page verification
│   └── sop_generator.py        # Fact-grounded Statement of Purpose generator
└── tests/
    ├── test_agents.py          # Multi-agent graph & failure simulation tests
    ├── test_search.py          # Query builder, deduplication & matcher tests
    └── test_sop.py             # Statement of Purpose fact-grounding tests
```

---

## 🚀 Quick Start

### 1. Clone & Set Up the Environment

```bash
git clone <repo-url>
cd scholarsync-ai

# Create & activate a virtual environment
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` in any text editor and supply your Tavily Search API key:
```ini
TAVILY_API_KEY=tvly-your-actual-key-here
```
*(Get a free API key at [tavily.com](https://tavily.com)).*

> **Note:** If no API key is provided, the application runs in **Demo Mode**, displaying verified sample scholarships and allowing full exploration of the UI, SOP generator, and simulation controls.

### 3. Run the Streamlit Application

```bash
streamlit run app.py
```

The app will launch in your browser at `http://localhost:8501`.

### 4. Run the Automated Test Suite

```bash
pytest -v tests
```

All 10 automated tests verify query generation, URL canonicalization, deduplication, eligibility checking, country coverage, deadline expiration logic, LangGraph orchestration, failure recovery, and SOP drafting.

---

## 🤖 Multi-Agent Workflow (LangGraph)

```
[START]
   │
   ▼
[Profile Analyst] ──> Extracts degree, field, nationality, intake & budget constraints
   │
   ▼
[Scout] ────────────> Executes multi-query Tavily search; deduplicates candidates
   │
   ▼
[Verifier] ─────────> Fetches source pages for top results; extracts deadline & funding proof
   │
   ▼
[Matcher] ──────────> Evaluates 5 deterministic eligibility criteria & calculates match score
   │
   ▼
[Critic] ───────────> Audits result volume & evidence depth
   │
   ├── (If insufficient / simulated error) ──> Routes back to [Scout] (Bounded Retry, max 1)
   │
   └── (If passed / retries exhausted) ──────> Routes to [Application Coach]
                                                      │
                                                      ▼
                                            [Application Coach] ──> SOP Draft & Highlights
                                                      │
                                                      ▼
                                                    [END]
```

---

## 🧪 Demo Failure Simulation

To demonstrate agent self-healing and recovery:
1. In the left panel, enable the checkbox:  
   `🧪 Simulate Agent Failure & Recovery (Demo Mode)`
2. Click **Find Scholarships**.
3. Watch the **Agent Activity** panel:
   - Scout simulates a transient query timeout.
   - Critic flags the empty pool and initiates a fallback query with expanded keywords.
   - Scout recovers, Verifier confirms details, and Coach finalizes the application package.

---

## 📋 Feature Status & Honest Disclaimers

| Feature | Status | Notes |
|---|---|---|
| **Student Profile Intake** | ✅ Complete | Captures degree, field, CGPA, nationality, preferences, intake, and budget. |
| **Document Uploads** | ✅ Complete | Accepts PDF resume and marksheet (max 5 MB) with format and size validation. Filenames are tracked in profile state. |
| **Tavily Live Web Search** | ✅ Complete | Fires up to 4 complementary queries when `TAVILY_API_KEY` is present. |
| **Candidate Deduplication** | ✅ Complete | Canonicalizes URLs, filters tracking params, and deduplicates normalized titles. |
| **Live Page Verification** | ✅ Complete | Fetches source pages with desktop User-Agent and extracts deadlines, funding, and apply links. |
| **LangGraph 6-Agent Pipeline** | ✅ Complete | Profile Analyst, Scout, Verifier, Matcher, Critic, and Application Coach in shared structured state. |
| **Critic Conditional Loop** | ✅ Complete | Bounded retry loop (max 1 retry) for query expansion and recovery. |
| **Failure Recovery Demo** | ✅ Complete | Controlled UI toggle demonstrating graceful retry and fallback execution. |
| **Statement of Purpose (SOP)** | ✅ Complete | Deterministic draft tailored to top match using confirmed student facts only. |
| **Country Selection (Global + India)** | ✅ Complete | Searchable multiselect covering 195+ world countries including India. |
| **Unit Test Suite** | ✅ Complete | 10 automated tests covering search, agents, country list, deadlines, and SOP. |
| **Document OCR / Deep Parsing** | ⏳ Incomplete | PDF text extraction via OCR / pdfminer is deferred; uploaded files are verified for size and type and referenced in profile context. |

---

## 📄 License

MIT — see `LICENSE` for details.
