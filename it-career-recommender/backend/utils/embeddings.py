from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

class Embedder:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or "sentence-transformers/all-MiniLM-L6-v2"
        self.model = SentenceTransformer(self.model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.zeros((1, 384), dtype=np.float32)
        return self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    def encode_mean(self, texts: List[str]) -> np.ndarray:
        vecs = self.encode(texts)
        if vecs.ndim == 1:
            vecs = vecs.reshape(1, -1)
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

