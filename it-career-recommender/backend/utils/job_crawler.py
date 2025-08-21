# utils/job_crawler.py
import pandas as pd
from pathlib import Path

DATA_PATH = Path("backend/data/it_job_roles.csv")

def fetch_jobs():
    return pd.read_csv(DATA_PATH)

if __name__ == "__main__":
    print(fetch_jobs().head())
