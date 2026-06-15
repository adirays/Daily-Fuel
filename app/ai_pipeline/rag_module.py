
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class RAGModule:
    def __init__(self, data_path='data/nutrition_facts.jsonl', index_path='app/indexes/nutrition.index'):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.data_path = data_path
        self.index_path = index_path
        self.documents = []
        self.index = None
        self._load_documents()
        self._build_index()

    def _load_documents(self):
        with open(self.data_path, 'r') as f:
            for line in f:
                self.documents.append(json.loads(line))

    def _build_index(self):
        try:
            self.index = faiss.read_index(self.index_path)
        except RuntimeError:
            embeddings = self.model.encode([doc['fact_text'] for doc in self.documents], convert_to_tensor=True)
            embeddings = embeddings.cpu().numpy()
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
            self.index.add(embeddings)
            faiss.write_index(self.index, self.index_path)

    def retrieve(self, query: str, k: int = 3):
        query_embedding = self.model.encode([query], convert_to_tensor=True)
        query_embedding = query_embedding.cpu().numpy()
        distances, indices = self.index.search(query_embedding, k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            doc = self.documents[idx]
            results.append({
                "score": float(distances[0][i]),
                "fact": doc['fact_text'],
                "meta": doc['meta']
            })
        return results

rag_module = RAGModule()

def retrieve_facts(query: str, k: int = 3):
    return rag_module.retrieve(query=query, k=k)
