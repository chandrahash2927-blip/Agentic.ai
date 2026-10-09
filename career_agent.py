"""
career_agent.py
LangChain-powered CareerAI Agent with 5 tools.
Uses current LangChain API (Tool + initialize_agent / create_react_agent).
"""

import os
import json
from typing import Optional

# ── LangChain imports ──────────────────────────────────────────────────────────
from langchain.tools import Tool
from langchain.agents import AgentType, initialize_agent
from langchain.memory import ConversationBufferWindowMemory

# ── CareerAI module imports ────────────────────────────────────────────────────
from job_engine import generate_mock_jobs, filter_jobs
from resume_parser import ats_score_resume
from company_intel import get_company_info, get_salary_insight
from database import add_application, get_applications
from interview_agent import get_questions, evaluate_answer_rule_based
from gemini_service import is_gemini_available

# ── Global job store (generated once per session) ──────────────────────────────
_job_store = []

def _get_jobs():
    global _job_store
    if not _job_store:
        _job_store = generate_mock_jobs(375)
    return _job_store

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 1 — search_jobs
# ══════════════════════════════════════════════════════════════════════════════
def tool_search_jobs(query: str) -> str:
    """
    Search prototype job dataset by role, location, or skills.
    Input: JSON string with keys: role, location, skills (list), salary_min
    """
    try:
        params = json.loads(query)
    except Exception:
        # Accept plain text role query
        params = {"role": query}

    filters = {
        "role": params.get("role", ""),
        "location": params.get("location"),
        "work_mode": params.get("work_mode"),
        "skills": params.get("skills", []),
        "salary_min": params.get("salary_min"),
        "experience": params.get("experience")
    }
    jobs = filter_jobs(_get_jobs(), filters)
    if not jobs:
        return "No jobs found matching those criteria. Try broader filters."

    result = f"Found {len(jobs)} jobs (Prototype Job Dataset):\\n\\n"
    for j in jobs[:5]:
        result += (
            f"• {j[\'title\']} @ {j[\'company\']}\\n"
            f"  Location: {j[\'location\']} | Mode: {j[\'work_mode\']}\\n"
            f"  Salary: {j[\'salary_lpa\']} LPA | Exp: {j[\'experience_min\']}-{j[\'experience_max\']}yr\\n"
            f"  Match: {j.get(\'match_score\', 0)}%\\n\\n"
        )
    return result

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 2 — analyze_resume
# ══════════════════════════════════════════════════════════════════════════════
def tool_analyze_resume(query: str) -> str:
    """
    Analyze resume text and return ATS score.
    Input: JSON with keys: resume_text, job_description, role
    """
    try:
        params = json.loads(query)
        resume_text = params.get("resume_text", "")
        jd = params.get("job_description", "")
        role = params.get("role", "default")
    except Exception:
        return "Please provide resume_text, job_description, and role as JSON."

    if not resume_text:
        return "No resume text provided."

    result = ats_score_resume(resume_text, jd, role)
    return (
        f"ATS Score: {result[\'total_score\']}/100 (\'{'ATS Friendly' if result[\'is_ats_friendly\'] else \'Needs Improvement\'}\'\')\\n"
        f"Keyword Match: {result[\'keyword_score\']} / 40\\n"
        f"JD Overlap: {result[\'jd_match_score\']} / 30\\n"
        f"Format Score: {result[\'format_score\']} / 30\\n"
        f"Matched: {\', \'.join(result[\'matched_keywords\'][:6])}\\n"
        f"Missing: {\', \'.join(result[\'missing_keywords\'][:6])}\\n"
        f"Suggestions: {\'; \'.join(result[\'suggestions\'])}"
    )

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 3 — track_application
# ══════════════════════════════════════════════════════════════════════════════
def tool_track_application(query: str) -> str:
    """
    Add or view job applications in SQLite.
    Input: JSON with action=\'add\' or \'view\'
    """
    try:
        params = json.loads(query)
    except Exception:
        params = {"action": "view"}

    action = params.get("action", "view")

    if action == "add":
        try:
            add_application(params)
            return f"Application saved for {params.get(\'title\', \'Unknown\')} at {params.get(\'company\', \'Unknown\')}"
        except Exception as e:
            return f"Failed to save application: {e}"

    # Default: view
    apps = get_applications()
    if not apps:
        return "No applications tracked yet. Apply to jobs first."
    result = f"You have {len(apps)} tracked applications:\\n"
    for a in apps[:5]:
        result += f"• {a[\'job_title\']} @ {a[\'company\']} — Status: {a[\'status\']}\\n"
    return result

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 4 — company_intelligence
# ══════════════════════════════════════════════════════════════════════════════
def tool_company_intelligence(company_name: str) -> str:
    """
    Get company information from prototype dataset.
    Input: company name as string
    """
    try:
        params = json.loads(company_name)
        name = params.get("company", company_name)
        exp = params.get("experience", 2)
    except Exception:
        name = company_name
        exp = 2

    info = get_company_info(name)
    salary = get_salary_insight(name, exp)
    return (
        f"Company: {info[\'name\']} (Prototype Dataset)\\n"
        f"Rating: {info[\'rating\']} / 5 | Employees: {info[\'employees\']}\\n"
        f"HQ: {info[\'headquarters\']} | Founded: {info[\'founded\']}\\n"
        f"Culture: {info[\'culture_score\']} | Work-Life: {info[\'work_life_balance\']}\\n"
        f"Pros: {\', \'.join(info[\'pros\'][:3])}\\n"
        f"Cons: {\', \'.join(info[\'cons\'][:2])}\\n"
        f"Salary for {exp}yr exp: {salary[\'range_min\']} - {salary[\'range_max\']} LPA (median {salary[\'median_lpa\']} LPA)"
    )

# ══════════════════════════════════════════════════════════════════════════════
# TOOL 5 — mock_interview
# ══════════════════════════════════════════════════════════════════════════════
def tool_mock_interview(query: str) -> str:
    """
    Generate interview questions for a role.
    Input: JSON with role and optional interview_type
    """
    try:
        params = json.loads(query)
        role = params.get("role", "Software Engineer")
        count = params.get("count", 3)
    except Exception:
        role = query if query else "Software Engineer"
        count = 3

    questions = get_questions(role, count)
    result = f"Interview questions for {role}:\\n\\n"
    for i, (q_type, question) in enumerate(questions, 1):
        result += f"Q{i} [{q_type}]: {question}\\n\\n"
    result += "Tip: Use the STAR method (Situation-Task-Action-Result) for behavioral questions."
    return result

# ══════════════════════════════════════════════════════════════════════════════
# BUILD AGENT
# ══════════════════════════════════════════════════════════════════════════════
def build_career_agent():
    """Build and return the LangChain CareerAI agent."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set.")

    from langchain_google_genai import ChatGoogleGenerativeAI
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.3,
        convert_system_message_to_human=True
    )

    tools = [
        Tool(
            name="search_jobs",
            func=tool_search_jobs,
            description=(
                "Search for jobs in the prototype Indian job dataset. "
                "Input: JSON with role, location, skills, salary_min, experience. "
                "Example: {\\"role\\": \\"Software Engineer\\", \\"location\\": \\"Bangalore\\"}"
            )
        ),
        Tool(
            name="analyze_resume",
            func=tool_analyze_resume,
            description=(
                "Analyze a resume and get ATS score (40% keyword + 30% JD + 30% format). "
                "Input: JSON with resume_text, job_description, role."
            )
        ),
        Tool(
            name="track_application",
            func=tool_track_application,
            description=(
                "Track job applications in SQLite database. "
                "Input: JSON with action=\'view\' or \'add\' (with title, company, location fields)."
            )
        ),
        Tool(
            name="company_intelligence",
            func=tool_company_intelligence,
            description=(
                "Get company info: rating, salary benchmarks, culture, pros/cons. "
                "Input: company name as string or JSON with company and experience keys."
            )
        ),
        Tool(
            name="mock_interview",
            func=tool_mock_interview,
            description=(
                "Generate mock interview questions for a role. "
                "Input: JSON with role and count keys. Example: {\\"role\\": \\"Data Analyst\\", \\"count\\": 3}"
            )
        )
    ]

    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        k=5  # keep last 5 exchanges
    )

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=4
    )
    return agent

# ── Singleton agent ────────────────────────────────────────────────────────────
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = build_career_agent()
    return _agent

def run_agent(user_input: str) -> str:
    """Run the CareerAI agent on user input. Returns string response."""
    try:
        agent = get_agent()
        response = agent.run(user_input)
        return response
    except Exception as e:
        return f"Agent error: {e}. Try rephrasing your question."
