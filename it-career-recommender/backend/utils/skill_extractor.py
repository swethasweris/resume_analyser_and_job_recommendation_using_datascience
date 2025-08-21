import re
import pandas as pd
from pathlib import Path
from rapidfuzz import process, fuzz

COMMON_SKILL_ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "pgsql": "postgresql",
    "node": "node.js",
    "reactjs": "react",
    "nextjs": "next.js",
    "tf": "tensorflow",
    "pt": "pytorch"
}

def normalize_skill(s: str) -> str:
    s = s.strip().lower()
    return COMMON_SKILL_ALIASES.get(s, s)

def build_gazetteer(job_csv_path: str | Path = None):
    if job_csv_path is None:
        job_csv_path = Path(__file__).resolve().parent.parent / "data" / "it_job_roles.csv"
    df = pd.read_csv(job_csv_path, encoding="latin1")

    skills = set()
    for col in ["required_skills", "certifications"]:
        if col in df.columns:
            for s in df[col].fillna("").astype(str):
                for token in re.split(r"[;|,]", s):
                    token = token.strip().lower()
                    if token:
                        skills.add(normalize_skill(token))
    return sorted(skills)

GLOSSARY = build_gazetteer()

def extract_skills_from_text(text: str, glossary: list | None = None, fuzzy_threshold: int = 82):
    if glossary is None:
        glossary = GLOSSARY

    text_low = (text or "").lower()
    found = set()

    # direct substring match
    for skill in glossary:
        if skill in text_low:
            found.add(skill)

    # fuzzy n-gram match
    tokens = re.findall(r"[a-zA-Z0-9\+\#\.\-]+", text_low)
    for i in range(len(tokens)):
        for L in (1, 2, 3):
            if i + L <= len(tokens):
                phrase = " ".join(tokens[i : i + L])
                match = process.extractOne(phrase, glossary, scorer=fuzz.token_sort_ratio)
                if match and match[1] >= fuzzy_threshold:
                    found.add(normalize_skill(match[0]))

    return sorted(found)
