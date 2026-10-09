
import sys
sys.path.insert(0, "/content/career_ai")

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

st.set_page_config(
    page_title="CareerAI - Indian Job Search Agent",
    page_icon="\U0001f4bc",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1E3A8A; }
    .sub-header { font-size: 1.2rem; color: #64748B; margin-bottom: 20px; }
    .ai-badge { background: linear-gradient(90deg,#1E3A8A,#7C3AED);
                color:white; padding:4px 12px; border-radius:20px; font-size:0.75rem; }
</style>
""", unsafe_allow_html=True)

from config import *
from database import *
from resume_parser import *
from job_engine import *
from company_intel import *
from interview_agent import *
from utils import *
from gemini_service import (
    is_gemini_available, generate_resume_feedback,
    generate_interview_question, evaluate_interview_answer,
    generate_career_recommendation, career_chat
)

# ── Session state init ────────────────────────────────────────────────────────
if "jobs" not in st.session_state:
    st.session_state.jobs = generate_mock_jobs(375)
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {}
if "interview_answers" not in st.session_state:
    st.session_state.interview_answers = []
if "current_questions" not in st.session_state:
    st.session_state.current_questions = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "ats_result" not in st.session_state:
    st.session_state.ats_result = None
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

gemini_ok = is_gemini_available()

# ── Sidebar — User Profile ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### \U0001f3af CareerAI")
    if gemini_ok:
        st.markdown("<span class=\'ai-badge\'>\U0001f916 Gemini AI Active</span>", unsafe_allow_html=True)
    else:
        st.warning("\u26a0\ufe0f Gemini API key not set", icon="\U0001f511")
    st.markdown("*AI-powered career assistant for Indian job market*")
    st.markdown("---")
    st.markdown("#### Your Profile")

    with st.form("profile_form"):
        name     = st.text_input("Full Name",   value=st.session_state.user_profile.get("name", ""))
        email    = st.text_input("Email",        value=st.session_state.user_profile.get("email", ""))
        exp      = st.selectbox("Experience",    list(EXPERIENCE_RANGES.keys()))
        notice   = st.selectbox("Notice Period", NOTICE_PERIODS)
        locations = st.multiselect("Preferred Locations", INDIAN_METROS + TIER_2_CITIES, default=["Bangalore"])
        skills   = st.text_area("Skills (comma separated)", value=st.session_state.user_profile.get("skills_raw", "Python, SQL"))
        submitted = st.form_submit_button("\U0001f4be Save Profile")
        if submitted:
            if not name or not email:
                st.error("Name and email are required.")
            elif "@" not in email:
                st.error("Enter a valid email address.")
            else:
                profile = {
                    "name": name, "email": email,
                    "experience": list(EXPERIENCE_RANGES[exp])[0],
                    "notice_period": notice,
                    "locations": locations,
                    "skills": [s.strip() for s in skills.split(",") if s.strip()],
                    "skills_raw": skills
                }
                st.session_state.user_profile = profile
                save_user_profile(profile)
                st.success("Profile saved!")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("<p class=\'main-header\'>\U0001f4bc CareerAI: Indian Job Search Agent</p>", unsafe_allow_html=True)
st.markdown("<p class=\'sub-header\'>Powered by Gemini AI + LangChain | Prototype Job Dataset</p>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "\U0001f50d Job Search",
    "\U0001f4c4 Resume ATS",
    "\U0001f4ca Tracker",
    "\U0001f3e2 Company Intel",
    "\U0001f3a4 Mock Interview",
    "\U0001f916 AI Assistant"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — JOB SEARCH  (PRESERVED — no changes to UI/logic)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        search_role = st.text_input("Job Title", "Software Engineer")
    with col2:
        search_location = st.selectbox("Location", ["All"] + INDIAN_METROS + TIER_2_CITIES)
    with col3:
        search_mode = st.selectbox("Work Mode", ["All"] + WORK_MODES)
    with col4:
        salary_filter = st.selectbox("Min Salary", ["Any"] + list(SALARY_RANGES.keys()))

    c_search, c_reset = st.columns([1, 5])
    with c_search:
        do_search = st.button("\U0001f50d Search", type="primary")
    with c_reset:
        if st.button("\U0001f504 Reset Filters"):
            st.rerun()

    filters = {
        "role": search_role,
        "location": search_location if search_location != "All" else None,
        "work_mode": search_mode if search_mode != "All" else None,
        "skills": st.session_state.user_profile.get("skills", []),
        "salary_min": SALARY_RANGES[salary_filter][0] if salary_filter != "Any" else None,
        "experience": st.session_state.user_profile.get("experience")
    }

    filtered_jobs = filter_jobs(st.session_state.jobs, filters)
    preferred_locations = st.session_state.user_profile.get("locations", [])

    st.markdown(f"**{len(filtered_jobs)} jobs found** (Prototype Job Dataset)")

    for job in filtered_jobs[:15]:
        loc_match = job["location"] in preferred_locations if preferred_locations else True
        match_color = "green" if job.get("match_score", 0) >= 70 else "orange" if job.get("match_score", 0) >= 40 else "red"
        with st.expander(
            f"{'\U0001f7e2' if loc_match else '\U0001f534'} {job['title']} @ {job['company']} — "
            f"{job['location']} | {job['salary_lpa']} LPA | Match: {job.get('match_score', 0):.0f}%"
        ):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**Location:** {job['location']}  |  **Work Mode:** {job['work_mode']}")
                st.markdown(f"**Salary:** {job['salary_min']}–{job['salary_max']} LPA  |  **Exp:** {job['experience_min']}-{job['experience_max']} years")
                st.markdown(f"**Notice Period:** {job['notice_period']}")
                st.markdown(job["description"])

                # Skills — matched in green
                user_skills = [s.lower() for s in st.session_state.user_profile.get("skills", [])]
                skill_html = " ".join([
                    f"<span style=\'background:{'#D1FAE5' if s.lower() in user_skills else '#F1F5F9'};padding:3px 8px;border-radius:10px;font-size:0.8rem\'>{s}</span>"
                    for s in job["skills_required"]
                ])
                st.markdown(f"**Skills:** {skill_html}", unsafe_allow_html=True)

            with c2:
                st.metric("Match Score", f"{job.get('match_score', 0):.0f}%")
                if not loc_match:
                    st.warning("\u26a0\ufe0f Outside preferred cities")
                if st.button("Save Application", key=f"save_{job['id']}"):
                    try:
                        add_application(job)
                        st.success("Saved!")
                    except Exception as e:
                        st.error(f"Error: {e}")
                st.link_button("Apply \u2197", job["apply_link"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — RESUME ATS  (PRESERVED + Gemini feedback added)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown("#### \U0001f4c4 Resume ATS Analyzer")
    st.info("ATS Score = 40% Keyword Match + 30% JD Overlap + 30% Format")

    col_left, col_right = st.columns([1, 1])
    with col_left:
        uploaded = st.file_uploader("Upload Resume", type=["pdf", "docx", "txt"])
        target_role = st.selectbox("Target Role", INDIAN_JOB_ROLES)
        jd_text = st.text_area("Paste Job Description", height=150,
                               placeholder="Paste the job description here for better ATS matching...")
        analyze_btn = st.button("\U0001f4ca Calculate ATS Score", type="primary")

    with col_right:
        if uploaded and analyze_btn:
            file_bytes = uploaded.read()
            if len(file_bytes) == 0:
                st.error("Uploaded file is empty.")
            else:
                try:
                    parsed = parse_resume(file_bytes, uploaded.name)
                    st.session_state.resume_text = parsed["raw_text"]
                    result = ats_score_resume(parsed["raw_text"], jd_text, target_role)
                    st.session_state.ats_result = result

                    score = result["total_score"]
                    color = "green" if score >= 70 else "orange" if score >= 50 else "red"
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=score,
                        domain={"x": [0,1], "y": [0,1]},
                        title={"text": "ATS Score"},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": color},
                            "steps": [
                                {"range": [0, 50], "color": "#FEE2E2"},
                                {"range": [50, 70], "color": "#FEF3C7"},
                                {"range": [70, 100], "color": "#D1FAE5"}
                            ]
                        }
                    ))
                    fig.update_layout(height=280)
                    st.plotly_chart(fig, use_container_width=True)

                    c1, c2, c3 = st.columns(3)
                    c1.metric("Keyword", f"{result['keyword_score']:.0f}/40")
                    c2.metric("JD Overlap", f"{result['jd_match_score']:.0f}/30")
                    c3.metric("Format", f"{result['format_score']}/30")

                    if result["matched_keywords"]:
                        st.success("\u2705 Matched: " + ", ".join(result["matched_keywords"]))
                    if result["missing_keywords"]:
                        st.warning("\u26a0\ufe0f Missing: " + ", ".join(result["missing_keywords"][:8]))
                    for s in result["suggestions"]:
                        st.info(s)
                except Exception as e:
                    st.error(f"Error parsing resume: {e}")

    # Gemini AI Feedback
    if st.session_state.ats_result and st.session_state.resume_text:
        st.markdown("---")
        st.markdown("#### \U0001f916 Gemini AI Resume Feedback")
        if not gemini_ok:
            st.warning("Set your GEMINI_API_KEY to get AI-powered resume feedback.")
        else:
            if st.button("Get AI Feedback from Gemini", type="primary"):
                with st.spinner("Gemini is analyzing your resume..."):
                    feedback = generate_resume_feedback(
                        st.session_state.resume_text,
                        st.session_state.ats_result,
                        target_role
                    )
                if feedback.startswith("["):
                    st.error(feedback)
                else:
                    st.markdown(feedback)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — APPLICATION TRACKER  (PRESERVED)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown("#### \U0001f4ca Application Tracker")
    status_filter = st.selectbox("Filter by Status", ["All", "Applied", "Shortlisted", "Interview", "Offer", "Rejected", "Withdrawn"])

    try:
        apps = get_applications(status_filter if status_filter != "All" else None)
    except Exception as e:
        st.error(f"Database error: {e}")
        apps = []

    if not apps:
        st.info("No applications found. Save jobs from the Job Search tab.")
    else:
        st.metric("Total Applications", len(apps))
        status_counts = {}
        for a in apps:
            status_counts[a["status"]] = status_counts.get(a["status"], 0) + 1
        if status_counts:
            fig = px.pie(values=list(status_counts.values()), names=list(status_counts.keys()),
                         title="Application Status")
            st.plotly_chart(fig, use_container_width=True)

        for app in apps:
            with st.expander(f"{app['job_title']} @ {app['company']} — {app['status']}"):
                cols = st.columns([2, 2, 2, 2])
                cols[0].write(f"**Location:** {app.get('location', 'N/A')}")
                cols[1].write(f"**Salary:** {app.get('salary_lpa', 'N/A')} LPA")
                cols[2].write(f"**Applied:** {app.get('applied_date', '')[:10]}")
                cols[3].write(f"**Match:** {app.get('match_score', 0)}%")

                new_status = st.selectbox(
                    "Update Status",
                    ["Applied", "Shortlisted", "Interview", "Offer", "Rejected", "Withdrawn"],
                    index=["Applied", "Shortlisted", "Interview", "Offer", "Rejected", "Withdrawn"].index(app["status"]),
                    key=f"status_{app['id']}"
                )
                if st.button("Update", key=f"upd_{app['id']}"):
                    try:
                        update_application_status(app["id"], new_status)
                        st.success("Status updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Update failed: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — COMPANY INTELLIGENCE  (PRESERVED)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown("#### \U0001f3e2 Company Intelligence")
    st.info("\U0001f4cb Prototype / Dataset Information — not live company data")

    selected_company = st.selectbox("Select Company", TOP_INDIAN_COMPANIES)
    user_exp = st.session_state.user_profile.get("experience", 2)

    if st.button("Get Company Info", type="primary"):
        info   = get_company_info(selected_company)
        salary = get_salary_insight(selected_company, user_exp)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"### {info['name']}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Rating", f"{info['rating']}/5")
            m2.metric("Culture", f"{info['culture_score']}/5")
            m3.metric("Work-Life", f"{info['work_life_balance']}/5")
            st.write(f"**HQ:** {info['headquarters']} | **Employees:** {info['employees']} | **Founded:** {info['founded']}")
            st.write(f"**Reviews:** {info['reviews_count']}")
            st.success("\u2714\ufe0f Pros: " + " | ".join(info["pros"]))
            st.warning("\u26a0\ufe0f Cons: " + " | ".join(info["cons"]))
        with c2:
            st.markdown(f"### Salary for {user_exp}yr Experience")
            st.metric("Median", f"{salary['median_lpa']} LPA")
            st.metric("Range", f"{salary['range_min']} – {salary['range_max']} LPA")
            benchmarks = info["salary_benchmark"]
            fig = px.bar(
                x=list(benchmarks.keys()),
                y=list(benchmarks.values()),
                labels={"x": "Experience Level", "y": "LPA"},
                title=f"{info['name']} Salary Benchmarks"
            )
            st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — MOCK INTERVIEW  (PRESERVED + Gemini evaluation added)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown("#### \U0001f3a4 Mock Interview — AI Practice Assessment")
    st.warning("This is an AI Practice Assessment for self-improvement, not a real hiring decision.")

    col_setup, col_interview = st.columns([1, 2])
    with col_setup:
        interview_role = st.selectbox("Role", INDIAN_JOB_ROLES)
        interview_type = st.selectbox("Interview Type", ["Technical", "Behavioral", "HR", "Mixed"])
        q_count = st.slider("Questions", 3, 8, 5)

        use_gemini_q = gemini_ok and st.checkbox("Generate questions with Gemini AI", value=gemini_ok)

        if st.button("\U0001f3a4 Start Interview", type="primary"):
            if use_gemini_q:
                questions = []
                with st.spinner("Gemini generating questions..."):
                    for _ in range(q_count):
                        q = generate_interview_question(interview_role, interview_type)
                        if not q.startswith("["):
                            questions.append((interview_type, q))
                if not questions:
                    questions = get_questions(interview_role, q_count)
            else:
                questions = get_questions(interview_role, q_count)

            st.session_state.current_questions = questions
            st.session_state.interview_answers = []
            st.rerun()

    with col_interview:
        if st.session_state.current_questions:
            q_index = len(st.session_state.interview_answers)
            total_q = len(st.session_state.current_questions)
            st.progress(q_index / total_q, text=f"Question {q_index + 1} of {total_q}")

            if q_index < total_q:
                q_type, question = st.session_state.current_questions[q_index]
                st.markdown(f"**[{q_type}] Q{q_index + 1}:** {question}")
                if q_type == "Behavioral":
                    st.caption("\U0001f4a1 Tip: Use STAR — Situation, Task, Action, Result")

                answer = st.text_area("Your Answer", key=f"ans_{q_index}", height=120)
                if st.button("Submit Answer", key=f"sub_{q_index}"):
                    if not answer.strip():
                        st.error("Please provide an answer before submitting.")
                    else:
                        if gemini_ok:
                            with st.spinner("Gemini evaluating your answer..."):
                                eval_result = evaluate_interview_answer(interview_role, q_type, question, answer)
                            score = eval_result["overall_score"]
                            feedback = eval_result["raw_feedback"]
                            st.markdown(f"**Technical Accuracy:** {eval_result['technical_accuracy']}/10")
                            st.markdown(f"**Relevance:** {eval_result['relevance']}/10")
                            st.markdown(f"**Clarity:** {eval_result['clarity']}/10")
                        else:
                            score, feedback = evaluate_answer_rule_based(q_type, question, answer)
                            eval_result = {"overall_score": score}

                        if score >= 7:
                            st.success(f"**Score:** {score}/10")
                        elif score >= 5:
                            st.warning(f"**Score:** {score}/10")
                        else:
                            st.error(f"**Score:** {score}/10")
                        st.markdown(f"**Feedback:** {feedback}")

                        try:
                            save_interview_session(interview_role, question, answer, str(feedback), score)
                        except Exception:
                            pass

                        st.session_state.interview_answers.append({
                            "type": q_type, "question": question,
                            "answer": answer, "score": score, "feedback": feedback
                        })
                        if st.button("Next Question \u2192", key=f"next_{q_index}"):
                            st.rerun()
            else:
                st.balloons()
                st.success("\U0001f389 Interview Complete! (AI Practice Assessment)")
                report = generate_interview_report(st.session_state.interview_answers)
                c_fig, c_rep = st.columns([1, 1])
                with c_fig:
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number", value=report["total_score"],
                        domain={"x": [0,1], "y": [0,1]},
                        title={"text": "Overall Score"},
                        gauge={
                            "axis": {"range": [None, 10]},
                            "bar": {"color": "#10B981"},
                            "steps": [
                                {"range": [0, 4], "color": "#FEE2E2"},
                                {"range": [4, 6], "color": "#FEF3C7"},
                                {"range": [6, 8], "color": "#DBEAFE"},
                                {"range": [8, 10], "color": "#D1FAE5"}
                            ]
                        }
                    ))
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                with c_rep:
                    verdict_colors = {"Strong Hire": "green", "Hire": "blue", "Consider": "orange", "Reject": "red"}
                    vc = verdict_colors.get(report["verdict"], "black")
                    st.markdown(f"### Verdict: <span style=\'color:{vc}\'>{report[\'verdict\']}</span>", unsafe_allow_html=True)
                    st.markdown("**\U0001f4aa Strengths:**")
                    for s in report["strengths"]: st.markdown(f"- {s}")
                    st.markdown("**\U0001f3af Improve:**")
                    for i in report["improvements"]: st.markdown(f"- {i}")
                if st.button("\U0001f504 Start New Interview"):
                    st.session_state.current_questions = []
                    st.session_state.interview_answers = []
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — AI ASSISTANT  (NEW — Gemini chat + LangChain agent)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[5]:
    st.markdown("#### \U0001f916 CareerAI Assistant")
    st.markdown("*Powered by Gemini AI + LangChain Agent with 5 career tools*")

    if not gemini_ok:
        st.error("Gemini API key is required. Set GEMINI_API_KEY in Cell 2 and restart.")
    else:
        mode = st.radio(
            "Mode",
            ["\U0001f4ac Gemini Chat", "\U0001f9e0 LangChain Agent (uses 5 tools)"],
            horizontal=True
        )

        # Show example questions
        with st.expander("\U0001f4a1 Example questions"):
            st.markdown("""
            - *What jobs are suitable for me?*
            - *What skills am I missing for a Data Scientist role?*
            - *How can I improve my resume?*
            - *Give me interview questions for Software Engineer*
            - *What is the salary at Google India for 3 years experience?*
            - *How many applications have I saved?*
            """)

        # Chat history display
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # AI recommendation button
        if st.session_state.user_profile and st.button("\U0001f31f Get career recommendation for my profile"):
            with st.spinner("Gemini thinking..."):
                top_jobs = filter_jobs(st.session_state.jobs, {
                    "skills": st.session_state.user_profile.get("skills", []),
                    "experience": st.session_state.user_profile.get("experience", 0)
                })[:5]
                rec = generate_career_recommendation(st.session_state.user_profile, top_jobs)
            st.markdown(rec)

        # Chat input
        if prompt := st.chat_input("Ask CareerAI anything about your job search..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("CareerAI thinking..."):
                    if "LangChain" in mode:
                        try:
                            from career_agent import run_agent
                            response = run_agent(prompt)
                        except Exception as e:
                            response = f"LangChain agent error: {e}. Using Gemini chat instead.\n\n"
                            response += career_chat(prompt, st.session_state.user_profile, st.session_state.chat_history)
                    else:
                        response = career_chat(prompt, st.session_state.user_profile, st.session_state.chat_history)

                if response.startswith("["):
                    st.error(response)
                else:
                    st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})

        if st.button("\U0001f5d1\ufe0f Clear chat"):
            st.session_state.chat_history = []
            st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("*CareerAI — Built for Indian Job Market | Capabl Technologies | Team: Chandrahash, Saranya, Srikar, Harika*")
