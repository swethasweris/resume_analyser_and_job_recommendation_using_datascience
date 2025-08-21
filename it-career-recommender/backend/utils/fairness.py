# utils/fairness.py
import re

def remove_bias(text: str) -> str:
    bias_terms = ["male", "female", "age", "married"]
    for b in bias_terms:
        text = re.sub(rf"\b{b}\b", "", text, flags=re.IGNORECASE)
    return text
