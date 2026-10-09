# CareerAI – Indian Job Search Assistant

> AI-powered career assistant for the Indian job market  
> **Team:** Chandrahash · Saranya · Srikar · Harika | **Org:** Capabl Technologies

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app.streamlit.app)

---

## Features

- **Job Search** — Filter Indian jobs by role, location, salary (LPA), work mode
- **Resume ATS Analyzer** — Score: 40% keyword + 30% JD overlap + 30% format
- **Gemini AI Feedback** — Qualitative resume improvement via Google Gemini API
- **Company Intelligence** — Ratings, salary benchmarks, pros/cons
- **Mock Interview** — Gemini-generated questions with 5-dimension evaluation
- **LangChain AI Agent** — Autonomous tool selection across 5 career tools
- **Application Tracker** — SQLite-backed job application status management

---

## Deploy on Streamlit Cloud (recommended)

1. Fork or push this repo to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in
3. Click **New app** → select your repo → set `app.py` as the main file
4. Go to **App Settings → Secrets** and add:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```

5. Click **Deploy** — your app will be live in ~2 minutes

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com)

---

## Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/careerai.git
cd careerai
pip install -r requirements.txt

# Set your Gemini API key
export GEMINI_API_KEY="your_key_here"   # Linux/Mac
set GEMINI_API_KEY=your_key_here        # Windows

streamlit run app.py
```

---

## Project Structure

```
careerai/
├── app.py                  # Streamlit entry point (6 tabs)
├── config.py               # Indian cities, roles, companies, salary ranges
├── database.py             # SQLite: job_applications, user_profiles, interview_history
├── job_engine.py           # Prototype job dataset + filtering + match scoring
├── resume_parser.py        # PDF/DOCX/TXT parsing + ATS score (40/30/30)
├── company_intel.py        # Company data: rating, salary benchmark, culture
├── interview_agent.py      # Interview question bank + rule-based evaluation
├── gemini_service.py       # Centralized Gemini API (5 functions)
├── career_agent.py         # LangChain ReAct agent + 5 career tools
├── utils.py                # Helper functions
├── requirements.txt        # Python dependencies
└── .streamlit/
    ├── config.toml         # Theme and server settings
    └── secrets.toml        # API keys (DO NOT commit — add via Streamlit dashboard)
```

---

## ATS Scoring Formula

```
Total ATS Score = Keyword Match (40%) + JD Overlap (30%) + Format Score (30%)
```

- **Keyword Match**: fraction of role-specific ATS keywords found in resume × 40  
- **JD Overlap**: fraction of unique JD words found in resume × 30  
- **Format Score**: starts at 30, deducted for each missing section (education / skills / experience)

---

## LangChain Agent Tools

| Tool | Description |
|------|-------------|
| `search_jobs` | Filter prototype job dataset by role, location, skills |
| `analyze_resume` | Run ATS scoring on resume text |
| `track_application` | Save and view SQLite job applications |
| `company_intelligence` | Company info, ratings, salary benchmarks |
| `mock_interview` | Generate role-specific interview questions |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| AI/LLM | Google Gemini API (gemini-1.5-flash) |
| Agent | LangChain (CONVERSATIONAL_REACT_DESCRIPTION) |
| Resume Parsing | PyPDF2, python-docx |
| Charts | Plotly |
| Database | SQLite |
| Deployment | Streamlit Cloud |

---

## Limitations

- Job data is a **prototype dataset** (~375 records) — not live Naukri/LinkedIn data
- ATS score is a project heuristic, not a commercial ATS guarantee
- No user authentication in current version (single-user per session)
- SQLite resets on Streamlit Cloud restart — use PostgreSQL for persistence in production

---

## Team

| Name | Role |
|------|------|
| Chandrahash | Lead Developer, AI Integration |
| Saranya | Resume Module, ATS Algorithm |
| Srikar | Job Engine, Company Intelligence |
| Harika | UI/UX, Application Tracker |

**Organization:** Capabl Technologies | **Duration:** 8 Weeks
