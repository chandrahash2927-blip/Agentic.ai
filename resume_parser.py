
import re
import io
from typing import Dict, List, Tuple

try:
    import PyPDF2
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

ATS_KEYWORDS = {
    "Software Engineer": [
        "python", "java", "javascript", "sql", "git", "agile", "rest api",
        "microservices", "docker", "aws", "data structures", "algorithms"
    ],
    "Data Analyst": [
        "sql", "python", "excel", "tableau", "power bi", "statistics",
        "pandas", "numpy", "data visualization", "etl", "machine learning"
    ],
    "Product Manager": [
        "product strategy", "roadmap", "agile", "scrum", "user stories",
        "market research", "kpi", "a/b testing", "stakeholder management"
    ],
    "DevOps Engineer": [
        "docker", "kubernetes", "aws", "azure", "ci/cd", "jenkins",
        "terraform", "linux", "python", "bash", "monitoring"
    ],
    "default": [
        "python", "sql", "communication", "teamwork", "problem solving",
        "project management", "agile", "leadership", "analytics"
    ]
}

def extract_text_from_pdf(file_bytes: bytes) -> str:
    if not PYPDF_AVAILABLE:
        return ""
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_bytes: bytes) -> str:
    if not DOCX_AVAILABLE:
        return ""
    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n".join([para.text for para in doc.paragraphs])

def parse_resume(file_bytes: bytes, filename: str) -> Dict:
    text = ""
    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif filename.endswith(".docx"):
        text = extract_text_from_docx(file_bytes)
    else:
        text = file_bytes.decode("utf-8", errors="ignore")
    return {
        "raw_text": text,
        "word_count": len(text.split()),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills_found": extract_skills(text),
        "experience_years": extract_experience_years(text)
    }

def extract_email(text: str) -> str:
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else ""

def extract_phone(text: str) -> str:
    patterns = [
        r"(\+91[\-\s]?)?[0]?(91)?[789]\d{9}",
        r"(\+91[\-\s]?)?\d{10}"
    ]
    for pattern in patterns:
        match = re.search(pattern, text.replace(" ", "").replace("-", ""))
        if match:
            return match.group(0)
    return ""

def extract_skills(text: str) -> List[str]:
    text_lower = text.lower()
    all_skills = set()
    for skills in ATS_KEYWORDS.values():
        all_skills.update(skills)
    return list(set([skill for skill in all_skills if skill in text_lower]))

def extract_experience_years(text: str) -> int:
    patterns = [
        r"(\d+)\+?\s*years?.*experience",
        r"experience.*?(\d+)\+?\s*years?",
        r"worked.*?(\d+)\+?\s*years?"
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return int(match.group(1))
    return 0

def ats_score_resume(resume_text: str, job_description: str, role: str = "default") -> Dict:
    """ATS scoring: 40% keyword match + 30% JD overlap + 30% format. PRESERVED."""
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()

    keywords = ATS_KEYWORDS.get(role, ATS_KEYWORDS["default"])
    matched_keywords = [kw for kw in keywords if kw in resume_lower]
    keyword_score = (len(matched_keywords) / len(keywords)) * 40 if keywords else 0

    jd_words = set(re.findall(r"\b\w+\b", jd_lower))
    resume_words = set(re.findall(r"\b\w+\b", resume_lower))
    common_words = jd_words.intersection(resume_words)
    jd_score = (len(common_words) / len(jd_words)) * 30 if jd_words else 0

    format_score = 30
    if len(resume_text) < 200:
        format_score -= 15
    if not re.search(r"\b(education|qualification|degree)\b", resume_lower):
        format_score -= 5
    if not re.search(r"\b(skill|technical|technologies)\b", resume_lower):
        format_score -= 5
    if not re.search(r"\b(project|experience|work)\b", resume_lower):
        format_score -= 5

    total_score = min(100, int(keyword_score + jd_score + format_score))
    missing_keywords = [kw for kw in keywords if kw not in resume_lower]

    suggestions = []
    if missing_keywords:
        suggestions.append(f"Add missing keywords: {\', \'.join(missing_keywords[:5])}")
    if not extract_email(resume_text):
        suggestions.append("Add a clear contact email")
    if not extract_phone(resume_text):
        suggestions.append("Add an Indian mobile number (+91 or 10-digit)")
    if len(resume_text.split()) < 150:
        suggestions.append("Resume seems too short. Aim for 300-500 words.")

    return {
        "total_score": total_score,
        "keyword_score": round(keyword_score, 1),
        "jd_match_score": round(jd_score, 1),
        "format_score": format_score,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "suggestions": suggestions,
        "is_ats_friendly": total_score >= 70
    }
