import pandas as pd
from utils.recommender import RoleRecommender
from sklearn.metrics import precision_score

def evaluate(test_csv: str, roles_csv: str, top_k: int = 5):
    # Load test resumes
    df = pd.read_csv(test_csv)
    
    # Init recommender
    recommender = RoleRecommender(roles_csv)

    total = len(df)
    hits_top1, hits_topk = 0, 0

    for _, row in df.iterrows():
        resume_text = row["resume_text"]
        true_role = row["true_role"]

        # Get recommendations
        recs = recommender.recommend_from_text(resume_text, experience_years=1, top_k=top_k)
        predicted_roles = [r["role"] for r in recs]

        if len(predicted_roles) == 0:
            continue

        # Top-1 accuracy
        if true_role == predicted_roles[0]:
            hits_top1 += 1

        # Top-k accuracy
        if true_role in predicted_roles:
            hits_topk += 1

    return {
        "top1_accuracy": round(hits_top1 / total, 3),
        "top{}_accuracy".format(top_k): round(hits_topk / total, 3)
    }

if __name__ == "__main__":
    # Run evaluation with correct paths
    result = evaluate("data/test_resumes.csv", "data/it_job_roles.csv", top_k=5)
    print("Evaluation Results:", result)
