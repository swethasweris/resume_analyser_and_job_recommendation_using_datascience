from fastapi import FastAPI, UploadFile, File
from pathlib import Path
from utils.resume_parser import extract_text
from utils.recommender import RoleRecommender
from utils.learning_paths import recommend_courses
from utils.fairness import remove_bias

app = FastAPI()

DATA_PATH = Path(__file__).resolve().parent / "data" / "it_job_roles.csv"
recommender = RoleRecommender(str(DATA_PATH))

@app.post("/api/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    contents = await file.read()
    resume_text = extract_text(file.filename, contents)
    resume_text = remove_bias(resume_text)

    recs = recommender.recommend_from_text(resume_text, top_k=5)

    all_missing = []
    for r in recs:
        all_missing.extend(r["missing_skills"])
    courses = recommend_courses(list(set(all_missing)))

    results = []
    for r in recs:
        lp = []
        for ms in r["missing_skills"]:
            if ms in courses:
                for c in courses[ms]:
                    lp.append({
                        "skill": ms,
                        "steps": [c["course_title"]],
                        "project_idea": f"Build a mini-project using {ms}",
                        "estimated_hours": c["duration_hours"],
                    })
        results.append({**r, "learning_plan": lp})

    roadmap = [
        {"role": "Junior Developer", "focus": "Master core programming & debugging"},
        {"role": "Mid-level Engineer", "focus": "Lead small projects & system design"},
        {"role": "Senior Engineer", "focus": "Architect systems & mentor juniors"},
    ]

    return {
        "extracted": {"resume_text": resume_text[:800]},
        "recommendations": results,
        "roadmap": roadmap,
    }
