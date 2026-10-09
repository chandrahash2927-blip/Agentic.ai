"""
gemini_service.py
Centralized Google Gemini API service for CareerAI.
All Gemini calls go through this module.
"""

import os
from typing import Optional

# ── Initialize Gemini ──────────────────────────────────────────────────────────
_gemini_model = None

def _get_model():
    global _gemini_model
    if _gemini_model is not None:
        return _gemini_model
    try:
        import streamlit as st
        api_key = st.secrets.get("GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
    except Exception:
        api_key = os.getenv("GEMINI_API_KEY", "")
    api_key = api_key.strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Set it in Colab Secrets or via getpass.")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    except ImportError:
        raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
    return _gemini_model

def _call_gemini(prompt: str, max_tokens: int = 1024) -> str:
    """Internal Gemini call with error handling."""
    try:
        model = _get_model()
        response = model.generate_content(
            prompt,
            generation_config={"max_output_tokens": max_tokens, "temperature": 0.7}
        )
        return response.text.strip() if response.text else "No response generated."
    except ValueError as e:
        return f"[Config Error] {e}"
    except Exception as e:
        err = str(e).lower()
        if "api_key" in err or "invalid" in err:
            return "[Auth Error] Invalid Gemini API key. Check your key at aistudio.google.com."
        if "quota" in err or "rate" in err:
            return "[Rate Limit] Gemini API quota exceeded. Wait a minute and try again."
        if "network" in err or "connection" in err:
            return "[Network Error] Cannot reach Gemini API. Check your internet connection."
        return f"[Gemini Error] {e}"

def is_gemini_available() -> bool:
    """Check if Gemini API key is configured."""
    try:
        import streamlit as st
        key = st.secrets.get("GEMINI_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
    except Exception:
        key = os.getenv("GEMINI_API_KEY", "")
    return bool(key.strip())

# ── Public Gemini functions ────────────────────────────────────────────────────

def generate_resume_feedback(resume_text: str, ats_result: dict, role: str) -> str:
    """
    Generate AI resume feedback using Gemini.
    ATS numerical score is calculated by Python (preserved).
    Gemini adds qualitative explanation and suggestions.
    """
    prompt = f"""
You are an expert Indian HR professional and ATS resume coach.

A candidate is applying for the role of: {role}

The ATS system has already calculated their score:
- Total ATS Score: {ats_result[\'total_score\']} / 100
- Keyword Match: {ats_result[\'keyword_score\']} / 40
- JD Overlap: {ats_result[\'jd_match_score\']} / 30
- Format Score: {ats_result[\'format_score\']} / 30
- Matched Keywords: {\', \'.join(ats_result[\'matched_keywords\'][:8])}
- Missing Keywords: {\', \'.join(ats_result[\'missing_keywords\'][:8])}

Resume text (first 1500 characters):
{resume_text[:1500]}

Provide structured feedback:
1. **Resume Strengths** (2-3 points)
2. **Critical Missing Skills/Keywords** (top 5 for this role)
3. **Weak Sections to Improve** (specific)
4. **ATS Optimization Tips** (3 actionable steps)
5. **Suggested Professional Summary** (2-3 sentences tailored to {role})

Be specific, practical, and relevant to the Indian job market.
Do NOT change the numerical ATS score — only provide qualitative feedback.
"""
    return _call_gemini(prompt, max_tokens=800)

def generate_interview_question(role: str, interview_type: str, context: str = "") -> str:
    """Generate a Gemini-powered interview question."""
    prompt = f"""
You are a senior interviewer at a top Indian tech company.
Generate ONE {interview_type} interview question for a {role} candidate.

Requirements:
- Relevant to Indian work culture and market
- Appropriate for {interview_type} round
- Clear, specific, and challenging
{f\"- Context: {context}\" if context else \"\"}

Return ONLY the question, no preamble.
"""
    return _call_gemini(prompt, max_tokens=200)

def evaluate_interview_answer(role: str, question_type: str, question: str, answer: str) -> dict:
    """
    Gemini-powered interview answer evaluation.
    Returns structured scores and feedback.
    Called: AI Practice Assessment (not a real hiring decision).
    """
    prompt = f"""
You are an expert interviewer evaluating a candidate for {role}.

Question Type: {question_type}
Question: {question}
Candidate\'s Answer: {answer}

Evaluate and respond in EXACTLY this format (no extra text):
TECHNICAL_ACCURACY: X/10
RELEVANCE: X/10
CLARITY: X/10
SPECIFICITY: X/10
OVERALL: X/10
STRENGTHS: [one line]
WEAKNESSES: [one line]
IMPROVEMENT: [one line]
BETTER_ANSWER: [2-3 sentence outline of a stronger answer]

Note: This is an AI Practice Assessment, not a real hiring decision.
"""
    raw = _call_gemini(prompt, max_tokens=400)

    # Parse scores from response
    import re
    def extract_score(label):
        match = re.search(rf"{label}:\\s*(\\d+)/10", raw)
        return int(match.group(1)) if match else 5

    def extract_line(label):
        match = re.search(rf"{label}:\\s*(.+)", raw)
        return match.group(1).strip() if match else ""

    overall = extract_score("OVERALL")
    return {
        "overall_score": overall,
        "technical_accuracy": extract_score("TECHNICAL_ACCURACY"),
        "relevance": extract_score("RELEVANCE"),
        "clarity": extract_score("CLARITY"),
        "specificity": extract_score("SPECIFICITY"),
        "strengths": extract_line("STRENGTHS"),
        "weaknesses": extract_line("WEAKNESSES"),
        "improvement": extract_line("IMPROVEMENT"),
        "better_answer": extract_line("BETTER_ANSWER"),
        "raw_feedback": raw
    }

def generate_career_recommendation(profile: dict, top_jobs: list) -> str:
    """Gemini career recommendation based on user profile and matched jobs."""
    job_summary = "\\n".join([
        f"- {j[\'title\']} at {j[\'company\']} ({j[\'location\']}), {j[\'salary_lpa\']} LPA, Match: {j.get(\'match_score\', 0)}%"
        for j in top_jobs[:5]
    ])
    prompt = f"""
You are a senior Indian career counselor. Provide career advice for this candidate:

Profile:
- Name: {profile.get(\'name\', \'Candidate\')}
- Experience: {profile.get(\'experience\', 0)} years
- Skills: {\', \'.join(profile.get(\'skills\', []))}
- Preferred Locations: {\', \'.join(profile.get(\'locations\', []))}
- Notice Period: {profile.get(\'notice_period\', \'Not specified\')}

Top matching jobs found:
{job_summary if job_summary else \'No jobs matched yet.\'}

Provide:
1. **Best Career Path** for this profile (2-3 sentences)
2. **Top 3 Skills to Add** for better market positioning
3. **Salary Negotiation Tip** relevant to Indian market
4. **One Immediate Action** they should take this week

Be practical and specific to the Indian job market.
"""
    return _call_gemini(prompt, max_tokens=600)

def career_chat(user_message: str, profile: dict, chat_history: list) -> str:
    """Conversational career assistant powered by Gemini."""
    history_text = "\\n".join([
        f"{m[\'role\'].upper()}: {m[\'content\']}"
        for m in chat_history[-6:]  # last 6 messages for context
    ])
    prompt = f"""
You are CareerAI, an expert AI career assistant for the Indian job market.
You help with: job search, resume optimization, interview preparation, salary negotiation, and career advice.
Stay within career-related topics. Be concise, practical, and India-specific.

User Profile:
- Experience: {profile.get(\'experience\', 0)} years
- Skills: {\', \'.join(profile.get(\'skills\', []))}
- Locations: {\', \'.join(profile.get(\'locations\', []))}

Recent conversation:
{history_text}

User: {user_message}
CareerAI:"""
    return _call_gemini(prompt, max_tokens=500)
