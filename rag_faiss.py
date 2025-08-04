import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

class LightweightRAG:
    def __init__(self, example_file="examples.json", model_name="all-MiniLM-L6-v2"):
        with open(example_file) as f:
            data = json.load(f)

        self.examples = [x["text"] for x in data]
        self.labels = [x["label"] for x in data]
        self.model = SentenceTransformer(model_name)
        self.embeddings = self.model.encode(self.examples, convert_to_numpy=True)

        dim = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dim)
        self.index.add(self.embeddings)

    def query(self, text: str, k=1):
        vector = self.model.encode([text], convert_to_numpy=True)
        distances, indices = self.index.search(vector, k)
        idx = indices[0][0]
        return self.examples[idx], self.labels[idx], distances[0][0]
