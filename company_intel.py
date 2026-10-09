
from typing import Dict

# Prototype / Dataset Information — not live API data
COMPANY_DATABASE = {
    "TCS": {
        "rating": 3.8, "reviews_count": "125k+", "headquarters": "Mumbai",
        "employees": "600k+", "founded": 1968,
        "pros": ["Job security", "Brand value", "Global exposure"],
        "cons": ["Slow growth", "Bureaucracy", "Average hikes"],
        "culture_score": 3.7, "work_life_balance": 3.9,
        "salary_benchmark": {"fresher": 3.5, "3_years": 6.5, "5_years": 9.0, "senior": 18.0}
    },
    "Infosys": {
        "rating": 3.9, "reviews_count": "98k+", "headquarters": "Bangalore",
        "employees": "340k+", "founded": 1981,
        "pros": ["Training", "Campus facilities", "Ethical management"],
        "cons": ["Slow promotions", "Politics"],
        "culture_score": 4.0, "work_life_balance": 4.1,
        "salary_benchmark": {"fresher": 3.6, "3_years": 6.8, "5_years": 9.5, "senior": 19.0}
    },
    "Amazon India": {
        "rating": 4.1, "reviews_count": "45k+", "headquarters": "Bangalore",
        "employees": "100k+", "founded": 1994,
        "pros": ["High compensation", "Fast-paced", "Stock options"],
        "cons": ["Long hours", "High pressure"],
        "culture_score": 3.9, "work_life_balance": 3.2,
        "salary_benchmark": {"fresher": 8.0, "3_years": 18.0, "5_years": 28.0, "senior": 50.0}
    },
    "Google India": {
        "rating": 4.5, "reviews_count": "32k+", "headquarters": "Hyderabad",
        "employees": "10k+", "founded": 1998,
        "pros": ["Perks", "Innovation", "Smart colleagues"],
        "cons": ["Competitive", "Interview difficulty"],
        "culture_score": 4.6, "work_life_balance": 4.2,
        "salary_benchmark": {"fresher": 12.0, "3_years": 25.0, "5_years": 40.0, "senior": 80.0}
    },
    "default": {
        "rating": 3.7, "reviews_count": "N/A", "headquarters": "India",
        "employees": "Unknown", "founded": 2000,
        "pros": ["Growing company", "Learning opportunities"],
        "cons": ["Processes evolving"],
        "culture_score": 3.5, "work_life_balance": 3.5,
        "salary_benchmark": {"fresher": 3.0, "3_years": 5.5, "5_years": 8.0, "senior": 15.0}
    }
}

def get_company_info(company_name: str) -> Dict:
    for key in COMPANY_DATABASE:
        if key.lower() in company_name.lower() or company_name.lower() in key.lower():
            return {"name": key, **COMPANY_DATABASE[key]}
    return {"name": company_name, **COMPANY_DATABASE["default"]}

def get_salary_insight(company_name: str, experience_years: int) -> Dict:
    info = get_company_info(company_name)
    benchmarks = info.get("salary_benchmark", {})
    if experience_years <= 1:
        level = "fresher"
    elif experience_years <= 4:
        level = "3_years"
    elif experience_years <= 7:
        level = "5_years"
    else:
        level = "senior"
    median = benchmarks.get(level, 5.0)
    return {
        "company": info["name"], "experience_level": level.replace("_", " "),
        "median_lpa": median,
        "range_min": round(median * 0.8, 1),
        "range_max": round(median * 1.3, 1),
        "rating": info["rating"],
        "culture_score": info["culture_score"]
    }
