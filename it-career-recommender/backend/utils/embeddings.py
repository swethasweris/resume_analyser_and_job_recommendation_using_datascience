from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        if not texts: return np.zeros((1, self.model.get_sentence_embedding_dimension()), dtype=np.float32)
        return self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    def encode_sections(self, sections: dict, weights: dict = None) -> np.ndarray:
        # sections: {"skills": [...], "experience": [...], ...}
        weights = weights or {k: 1.0 for k in sections.keys()}
        combined_vec = sum(weights[k] * self.encode_mean(v) for k, v in sections.items())
        return combined_vec / sum(weights.values())

    def encode_mean(self, texts: List[str]) -> np.ndarray:
        vecs = self.encode(texts)
        return vecs.mean(axis=0, keepdims=True)

    
    # utils/embeddings.py
def get_embedding_function():
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        def encode(texts): return model.encode(texts)
        return encode, "sbert"
    except:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(max_features=5000)
        def encode(texts): return vec.fit_transform(texts).toarray()
        return encode, "tfidf"

