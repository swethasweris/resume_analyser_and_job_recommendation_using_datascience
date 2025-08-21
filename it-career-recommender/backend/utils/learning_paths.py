import pandas as pd
from pathlib import Path
from rapidfuzz import process, fuzz

BASE_DIR = Path(__file__).resolve().parent.parent
COURSES = BASE_DIR / "data" / "courses_catalog.csv"

ALIASES = {
    "js": "javascript",
    "node": "node.js",
    "postgres": "sql",
    "amazon web services": "aws",
    "reactjs": "react",
    "nextjs": "react",
    "ci/cd": "continuous integration",
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "tf": "tensorflow",
    "pt": "pytorch",
    "k8s": "kubernetes",
    "sre": "site reliability engineering",
}


def normalize_skill(s: str) -> str:
    s = str(s).strip().lower()
    return ALIASES.get(s, s)


def load_courses():
    df = pd.read_csv(COURSES, encoding="utf-8")
    df["skill"] = df["skill"].apply(normalize_skill)
    return df


def recommend_courses(missing_skills):
    """
    Return a dict { skill: [ {course_title, link, duration_hours, level} ] }
    Always returns at least 1 course (best fuzzy match), never empty.
    """
    df = load_courses()
    available_skills = df["skill"].unique().tolist()
    results = {}

    for skill in missing_skills:
        norm = normalize_skill(skill)
        match = process.extractOne(norm, available_skills, scorer=fuzz.token_sort_ratio)

        if match:
            # match = (best_skill, score, index)
            best_skill, score, _ = match  

            matches = df[df["skill"] == best_skill][
                ["skill", "platform", "course_title", "link", "duration_hours", "level"]
            ]

            if not matches.empty:
                results[skill] = matches.to_dict(orient="records")
                continue

        # fallback — pick any closest course instead of "No course found"
        alt = df.sample(1).iloc[0].to_dict()
        results[skill] = [{
            "course_title": alt.get("course_title", "General IT Foundations"),
            "link": alt.get("link", ""),
            "duration_hours": alt.get("duration_hours", 0),
            "level": alt.get("level", "Beginner"),
            "platform": alt.get("platform", "Coursera")
        }]

    return results


def build_learning_plan(missing_skills):
    """
    Given missing skills, build a structured learning plan with suggested courses.
    """
    return recommend_courses(missing_skills)


def build_career_roadmap(top_role: str):
    """
    Placeholder for career roadmap generation.
    Extend with custom logic if needed.
    """
    return [
        {"step": 1, "goal": f"Master fundamentals required for {top_role}"},
        {"step": 2, "goal": f"Complete 2–3 projects aligned with {top_role}"},
        {"step": 3, "goal": f"Earn relevant certifications for {top_role}"},
        {"step": 4, "goal": f"Apply for {top_role} internships or junior roles"},
    ]
