
import random
from typing import List, Dict
from datetime import datetime, timedelta
from config import (
    INDIAN_METROS, TIER_2_CITIES, EXPERIENCE_RANGES, SALARY_RANGES,
    WORK_MODES, NOTICE_PERIODS, INDIAN_JOB_ROLES, TOP_INDIAN_COMPANIES
)

# Prototype Job Dataset — not live API data
def generate_mock_jobs(count: int = 375) -> List[Dict]:
    jobs = []
    all_locations = INDIAN_METROS + TIER_2_CITIES
    per_role = max(1, count // len(INDIAN_JOB_ROLES))

    for role in INDIAN_JOB_ROLES:
        for i in range(per_role):
            company  = random.choice(TOP_INDIAN_COMPANIES)
            location = random.choice(all_locations)
            work_mode = random.choice(WORK_MODES)
            base_salary = random.uniform(3, 20)
            if any(w in role for w in ["Lead", "Architect", "Manager"]):
                base_salary += random.uniform(8, 15)
            if location in INDIAN_METROS[:3]:
                base_salary *= 1.2

            exp_ranges_list = list(EXPERIENCE_RANGES.values())
            exp_min, exp_max = exp_ranges_list[i % len(exp_ranges_list)]

            job = {
                "id": len(jobs) + 1000,
                "title": role,
                "company": company,
                "location": location,
                "work_mode": work_mode,
                "salary_min": round(base_salary, 1),
                "salary_max": round(base_salary * 1.4, 1),
                "salary_lpa": round(base_salary, 1),
                "experience_min": exp_min,
                "experience_max": exp_max,
                "notice_period": random.choice(NOTICE_PERIODS),
                "posted_date": (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
                "description": (
                    f"Join {company} as a {role} in {location}. "
                    f"Requires {exp_min}-{exp_max} years experience. "
                    f"Work mode: {work_mode}. "
                    f"Skills: Python, SQL, Cloud, Agile, Communication."
                ),
                "skills_required": random.sample([
                    "Python", "Java", "SQL", "AWS", "React", "Node.js", "Docker",
                    "Kubernetes", "Machine Learning", "Data Analysis", "Agile",
                    "Communication", "Leadership"
                ], k=random.randint(3, 6)),
                "apply_link": f"https://www.linkedin.com/jobs/search/?keywords={role.replace(\' \', \'%20\')}",
                "match_score": 0
            }
            jobs.append(job)

    random.shuffle(jobs)
    return jobs

def filter_jobs(jobs: List[Dict], filters: Dict) -> List[Dict]:
    filtered = jobs

    if filters.get("role"):
        role_q = filters["role"].lower()
        filtered = [j for j in filtered if role_q in j["title"].lower()]

    if filters.get("location"):
        filtered = [j for j in filtered if filters["location"].lower() in j["location"].lower()]

    if filters.get("work_mode"):
        filtered = [j for j in filtered if j["work_mode"] == filters["work_mode"]]

    if filters.get("experience") is not None:
        user_exp = filters["experience"]
        filtered = [j for j in filtered if j["experience_min"] <= user_exp <= j["experience_max"] + 2]

    if filters.get("salary_min"):
        filtered = [j for j in filtered if j["salary_max"] >= filters["salary_min"]]

    if filters.get("skills"):
        user_skills = [s.lower() for s in filters["skills"]]
        scored = []
        for job in filtered:
            job_skills = [s.lower() for s in job["skills_required"]]
            match_count = sum(1 for s in user_skills if s in job_skills)
            score = round((match_count / max(len(job_skills), 1)) * 100, 1)
            j2 = job.copy()
            j2["match_score"] = score
            scored.append(j2)
        filtered = sorted(scored, key=lambda x: x["match_score"], reverse=True)

    return filtered
