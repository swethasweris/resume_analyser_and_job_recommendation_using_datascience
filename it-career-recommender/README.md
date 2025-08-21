# IT Career Recommender (Resume ➜ Roles ➜ Skill Gaps ➜ Learning Path)

## Quick Start

1) Put your dataset at: `backend/data/it_job_roles.csv`
   - Required columns: `role, required_skills`
   - Optional column: `min_experience` (integer years)
   - Example row:
     ```
     role,required_skills,min_experience
     Backend Developer,"python, django, rest, postgresql, docker",1
     ```

2) Install backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# optional small model:
python -m spacy download en_core_web_sm
uvicorn app:app --reload --port 8000
```

3) Frontend (optional quick UI):
```bash
cd ../frontend
npm install
npm run dev
```

Open http://localhost:5173 to upload a resume and see results.

## API
- `GET /api/roles` -> list roles from dataset
- `POST /api/analyze` (multipart file) -> returns extracted skills/experience, top role recommendations, gaps, learning plans, and a career roadmap
- `POST /api/analyze_text` (form field `text`) -> same as above for raw text

## Notes
- Similarity is computed with Sentence-Transformers embeddings (mean pooling) over skills.
- Experience years are extracted via simple regex heuristics.
- Learning path is rules-based; you can swap in an LLM later.
