import re
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
import uvicorn
app = FastAPI()

from backend.utils.resume_parser import extract_text

# remove_bias is optional (if you have it)
try:
    from backend.utils.fairness import remove_bias
except Exception:
    remove_bias = lambda x: x

from backend.utils.recommender import RoleRecommender
from backend.utils.learning_paths import build_learning_plan, build_career_roadmap
from backend.utils.db import ensure_indexes




# path to your roles CSV (adjust if needed)
DATA_PATH = Path(__file__).resolve().parent / "data" / "it_job_roles.csv"

# global recommender (initialized at startup)
recommender = None



@app.on_event("startup")
async def _startup():
    # keep your existing startup actions (ensure_indexes, etc.)
    await ensure_indexes()

    global recommender
    try:
        # instantiate once (costly models loaded here)
        recommender = RoleRecommender(str(DATA_PATH))
        print("RoleRecommender initialized.")
    except Exception as e:
        # fallback: leave recommender None and handle gracefully in endpoint
        print("Failed to initialize RoleRecommender:", e)
        recommender = None


def estimate_experience_from_text(text: str) -> int:
    """
    Simple heuristic to extract years of experience from text.
    Returns 0 if not found.
    """
    text_l = text.lower()
    # pattern matches like '5 years', '3+ years', '6 yrs', '8 years of experience'
    m = re.search(r'(\d{1,2})\+?\s*(?:years|yrs|year)\b', text_l)
    if m:
        try:
            return int(m.group(1))
        except:
            pass
    m2 = re.search(r'(\d{1,2})\s+years of experience', text_l)
    if m2:
        try:
            return int(m2.group(1))
        except:
            pass
    return 0


def tfidf_fallback_recommend(text: str, roles_csv_path: str, top_k: int = 5):
    """
    Lightweight fallback: use TF-IDF on role required_skills text to compute similarity
    if embeddings or heavy models are missing.
    """
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    df = pd.read_csv(roles_csv_path, encoding="latin1")
    if "required_skills" not in df.columns or "role" not in df.columns:
        return []

    # join resume text + role skills for vectorization
    corps = df["required_skills"].fillna("").astype(str).tolist()
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    vecs = vectorizer.fit_transform(corps + [text])
    resume_vec = vecs[-1]
    role_vecs = vecs[:-1]
    sims = cosine_similarity(resume_vec, role_vecs).flatten()
    df["similarity"] = sims
    df = df.sort_values("similarity", ascending=False).head(top_k)

    out = []
    # extract matched / missing skills by fuzzy substring overlap
    from rapidfuzz import fuzz
    resume_sk_words = set([w.lower() for w in re.findall(r"\w+", text) if len(w) > 1])
    for _, row in df.iterrows():
        req_sk = []
        for s in str(row.get("required_skills", "")).split(","):
            s = s.strip().lower()
            if s:
                req_sk.append(s)
        matched = [s for s in req_sk if any(fuzz.partial_ratio(s, w) > 85 for w in resume_sk_words)]
        missing = [s for s in req_sk if s not in matched]
        out.append({
            "role": row["role"],
            "score": float(row["similarity"]),
            "similarity": float(row["similarity"]),
            "min_experience": int(row.get("min_experience", 0) or 0),
            "required_skills": req_sk,
            "missing_skills": missing,
            "matched_skills": matched,
        })
    return out


@app.post("/api/analyze")
async def analyze_resume(file: UploadFile = File(...), top_k: int = 5):
    """
    Main analyze endpoint:
    - extracts text
    - optionally removes bias
    - estimates experience
    - runs recommender (embedding-based), falling back to TF-IDF if needed
    - builds learning plan for missing skills
    - returns JSON matching frontend expectations
    """
    contents = await file.read()
    resume_text = extract_text(file.filename, contents)
    resume_text = remove_bias(resume_text)

    experience = estimate_experience_from_text(resume_text)

    # 1) try the main recommender
    try:
        if recommender is not None:
            recs = recommender.recommend_from_text(resume_text, experience_years=experience, top_k=top_k)
        else:
            raise RuntimeError("Recommender not initialized")
    except Exception as e:
        # if embeddings fail (model missing / memory issue), fallback to TF-IDF heuristic
        print("Primary recommender failed, falling back to TF-IDF:", e)
        recs = tfidf_fallback_recommend(resume_text, str(DATA_PATH), top_k=top_k)

    # 2) collect missing skills across all recs and map to courses
    all_missing = set()
    for r in recs:
        all_missing.update([ms for ms in r.get("missing_skills", []) if ms])

    courses_map = build_learning_plan(list(all_missing)) if all_missing else {}

    # 3) attach learning_plan to each recommendation
    results = []
    for r in recs:
        lp = []
        for ms in r.get("missing_skills", []):
            if ms in courses_map:
                for c in courses_map[ms]:
                    lp.append({
                        "skill": ms,
                        "steps": [c.get("course_title")],
                        "project_idea": f"Build a small project using {ms}",
                        "estimated_hours": c.get("duration_hours", 0),
                        "platform": c.get("platform", "")
                    })
        results.append({**r, "learning_plan": lp})

    # 4) simple roadmap (extendable)
    roadmap = build_career_roadmap(results[0]["role"]) if results else []

    return {
        "extracted": {"resume_text": resume_text[:3000], "estimated_experience_years": experience},
        "recommendations": results,
        "roadmap": roadmap,
    }



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
