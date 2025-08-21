from typing import List, Dict, Any
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .embeddings import Embedder
from .skill_extractor import extract_skills_from_text   # <-- use skill extractor!


def normalize_skill(s: str) -> str:
    return s.strip().lower()


def split_skills(s: str) -> List[str]:
    if pd.isna(s):
        return []
    for sep in [";", "|", ","]:
        s = s.replace(sep, ",")
    return [normalize_skill(x) for x in s.split(",") if x.strip()]


class RoleRecommender:
    def __init__(self, dataset_path: str):
        self.roles_df = pd.read_csv(dataset_path, encoding="latin1")

        if "role" not in self.roles_df.columns or "required_skills" not in self.roles_df.columns:
            raise ValueError("Dataset must have columns: role, required_skills")

        self.roles_df["skills_list"] = self.roles_df["required_skills"].apply(split_skills)
        if "min_experience" not in self.roles_df.columns:
            self.roles_df["min_experience"] = 0

        self.embedder = Embedder()

        self.roles_df["vec"] = self.roles_df["skills_list"].apply(
            lambda skills: self.embedder.encode_mean(skills if skills else [""])
        )

    def _resume_vector(self, skills: List[str]) -> np.ndarray:
        skills = [normalize_skill(s) for s in skills if s]
        if not skills:
            return self.embedder.encode_mean([""])
        return self.embedder.encode_mean(skills)

    def recommend_roles(self, skills: List[str], experience_years: int, top_k: int = 5) -> List[Dict[str, Any]]:
        rvec = self._resume_vector(skills)
        role_vecs = np.vstack(self.roles_df["vec"].values.tolist())
        sims = cosine_similarity(rvec, role_vecs).flatten()

        candidates = self.roles_df.copy()
        candidates["similarity"] = sims

        def exp_penalty(row):
            minexp = int(row.get("min_experience", 0) or 0)
            if experience_years >= minexp:
                return 1.0
            gap = max(0, minexp - experience_years)
            return max(0.6, 1.0 - 0.1 * gap)

        candidates["score"] = candidates.apply(lambda r: r["similarity"] * exp_penalty(r), axis=1)
        candidates = candidates.sort_values("score", ascending=False).head(top_k)

        out = []
        skill_set = set([normalize_skill(s) for s in skills])
        for _, row in candidates.iterrows():
            role_skills = set(row["skills_list"])
            missing = sorted(list(role_skills - skill_set))
            out.append({
                "role": row["role"],
                "score": float(row["score"]),
                "similarity": float(row["similarity"]),
                "min_experience": int(row.get("min_experience", 0) or 0),
                "required_skills": sorted(list(role_skills)),
                "missing_skills": missing,
                "matched_skills": sorted(list(role_skills & skill_set))
            })
        return out

    # ✅ NEW: use skill_extractor for real text parsing
    def recommend_from_text(self, text: str, experience_years: int = 0, top_k: int = 5):
        skills = extract_skills_from_text(text)   # <--- fuzzy skill extraction
        return self.recommend_roles(skills, experience_years, top_k)
