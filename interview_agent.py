
import random
from typing import Dict, List, Tuple

INTERVIEW_QUESTIONS = {
    "Software Engineer": [
        ("Technical", "Explain the difference between REST and GraphQL. When would you use each?"),
        ("Coding", "Write a function to find the first non-repeating character in a string."),
        ("System Design", "Design a URL shortening service like bit.ly. How would you handle scaling?"),
        ("Behavioral", "Tell me about a time you had to debug a production issue under pressure."),
        ("DSA", "Given an array, find the maximum sum of any contiguous subarray (Kadane\'s algorithm).")
    ],
    "Data Analyst": [
        ("Technical", "What is the difference between INNER JOIN and LEFT JOIN?"),
        ("Statistics", "Explain p-value in simple terms."),
        ("Python/SQL", "How would you handle missing values in a dataset?"),
        ("Case Study", "Our conversion rate dropped 15% this month. How would you investigate?"),
        ("Behavioral", "How do you explain technical findings to non-technical stakeholders?")
    ],
    "Product Manager": [
        ("Product Sense", "How would you improve Zomato\'s food delivery app for tier-2 cities?"),
        ("Metrics", "What KPIs would you track for a ride-sharing app like Ola?"),
        ("Prioritization", "You have limited engineering capacity. How do you prioritize features?"),
        ("Behavioral", "Tell me about a product you launched that failed. What did you learn?"),
        ("Strategy", "Should Swiggy enter the grocery delivery market? Why or why not?")
    ],
    "default": [
        ("Behavioral", "Why do you want to leave your current job?"),
        ("Behavioral", "Where do you see yourself in 5 years?"),
        ("Technical", "Explain your most challenging project and your role in it."),
        ("Situational", "How do you handle conflict with a team member?"),
        ("General", "What are your salary expectations?")
    ]
}

def get_questions(role: str, count: int = 5) -> List[Tuple[str, str]]:
    questions = INTERVIEW_QUESTIONS.get(role, INTERVIEW_QUESTIONS["default"])
    return questions if len(questions) <= count else random.sample(questions, count)

def evaluate_answer_rule_based(question_type: str, question: str, answer: str) -> Tuple[int, str]:
    """Rule-based fallback evaluation (used when Gemini is unavailable)."""
    answer_length = len(answer.split())
    if answer_length < 10:
        return (2, "Too brief. Use the STAR method: Situation, Task, Action, Result.")
    score = min(10, 4 + (answer_length // 20))
    feedback_parts = []
    if any(w in answer.lower() for w in ["example", "instance", "case", "situation"]):
        score = min(10, score + 2)
        feedback_parts.append("Good use of specific examples.")
    else:
        feedback_parts.append("Try to include a concrete example from your experience.")
    if score >= 8:
        feedback_parts.append("Excellent response!")
    elif score >= 6:
        feedback_parts.append("Good. Add more specificity.")
    else:
        feedback_parts.append("Improve structure and add technical depth.")
    return (score, " ".join(feedback_parts))

def generate_interview_report(answers: List[Dict]) -> Dict:
    avg_score = sum(a["score"] for a in answers) / len(answers) if answers else 0
    strengths = list(set([f"Strong {a[\'type\'].lower()} answer" for a in answers if a["score"] >= 8]))
    improvements = list(set([f"Need work on {a[\'type\'].lower()} questions" for a in answers if a["score"] <= 4]))
    return {
        "total_score": round(avg_score, 1),
        "max_score": 10,
        "strengths": strengths or ["Consistent effort"],
        "improvements": improvements or ["Add more specific examples"],
        "verdict": "Strong Hire" if avg_score >= 8 else "Hire" if avg_score >= 6 else "Consider" if avg_score >= 4 else "Reject",
        "preparation_tips": [
            "Practice the STAR method for behavioral questions",
            "Review system design fundamentals",
            "Prepare 3-4 detailed stories from past experience",
            "Research the company\'s recent products and news"
        ]
    }
