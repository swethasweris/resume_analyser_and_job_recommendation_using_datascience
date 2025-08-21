# utils/evaluation.py
from utils.recommender import recommend

def evaluate(test_resumes, true_jobs):
    y_true, y_pred = [], []
    for resume, true_job in zip(test_resumes, true_jobs):
        recs = recommend(resume, topk=5)
        titles = [r["title"] for r in recs]
        y_true.append(true_job)
        y_pred.append(titles)

    precision = sum([1 for t, preds in zip(y_true, y_pred) if t in preds]) / len(y_true)
    recall = precision  # simplified recall since one truth per resume
    return {"precision": round(precision, 3), "recall": round(recall, 3)}
