import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = "career_agent.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            salary_lpa REAL,
            work_mode TEXT,
            applied_date TEXT,
            status TEXT DEFAULT 'Applied',
            notes TEXT,
            job_description TEXT,
            match_score INTEGER
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            experience_years INTEGER,
            current_ctc REAL,
            expected_ctc REAL,
            notice_period TEXT,
            preferred_locations TEXT,
            skills TEXT,
            resume_text TEXT,
            created_at TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS interview_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            question TEXT,
            user_answer TEXT,
            ai_feedback TEXT,
            score INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_application(job_data: Dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO job_applications
        (job_title, company, location, salary_lpa, work_mode,
         applied_date, status, notes, job_description, match_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_data['title'], job_data['company'],
        job_data.get('location'), job_data.get('salary_lpa'),
        job_data.get('work_mode'), datetime.now().isoformat(),
        'Applied', '', job_data.get('description', ''),
        job_data.get('match_score', 0)
    ))
    conn.commit()
    conn.close()

def get_applications(status: Optional[str] = None) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if status:
        c.execute("SELECT * FROM job_applications WHERE status = ? ORDER BY applied_date DESC", (status,))
    else:
        c.execute("SELECT * FROM job_applications ORDER BY applied_date DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_application_status(app_id: int, status: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE job_applications SET status = ? WHERE id = ?", (status, app_id))
    conn.commit()
    conn.close()

def save_user_profile(profile: Dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO user_profiles
        (id, name, email, phone, experience_years, current_ctc, expected_ctc,
         notice_period, preferred_locations, skills, resume_text, created_at)
        VALUES (
            (SELECT id FROM user_profiles WHERE email = ?),
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, (
        profile['email'], profile['name'], profile['email'],
        profile.get('phone'), profile.get('experience'),
        profile.get('current_ctc'), profile.get('expected_ctc'),
        profile.get('notice_period'),
        json.dumps(profile.get('locations', [])),
        json.dumps(profile.get('skills', [])),
        profile.get('resume_text', ''),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def get_user_profile(email: str) -> Optional[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM user_profiles WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    if row:
        profile = dict(row)
        profile['preferred_locations'] = json.loads(profile.get('preferred_locations') or '[]')
        profile['skills'] = json.loads(profile.get('skills') or '[]')
        return profile
    return None

def save_interview_session(role, question, answer, feedback, score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO interview_history
        (role, question, user_answer, ai_feedback, score, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (role, question, answer, feedback, score, datetime.now().isoformat()))
    conn.commit()
    conn.close()

init_db()
