
def format_salary_lpa(amount: float) -> str:
    return f"\u20b9{amount:.1f} LPA"

def format_experience(years: int) -> str:
    if years == 0:
        return "Fresher"
    elif years == 1:
        return "1 Year"
    else:
        return f"{years} Years"

def color_score(score: int) -> str:
    if score >= 80:
        return "green"
    elif score >= 60:
        return "orange"
    else:
        return "red"
