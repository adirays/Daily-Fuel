
import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "app/indexes/nutrition.index")
EMB_MODEL = os.getenv("EMB_MODEL", "all-MiniLM-L6-v2")
METADATA_PATH = "app/indexes/metadata.jsonl"

# Load the FAISS index
index = faiss.read_index(FAISS_INDEX_PATH)

# Load the sentence transformer model
model = SentenceTransformer(EMB_MODEL)

# Load the metadata
metadata = []
with open(METADATA_PATH, "r") as f:
    for line in f:
        metadata.append(json.loads(line))

def retrieve_facts(query: str, k: int = 5) -> list[dict]:
    """
    Retrieves the top k most relevant facts for a given query.
    """
    # Encode the query into an embedding
    query_embedding = model.encode([query], convert_to_numpy=True)

    # Normalize the query embedding
    faiss.normalize_L2(query_embedding)

    # Search the FAISS index
    distances, indices = index.search(query_embedding, k)

    # Prepare the results
    results = []
    for i in range(k):
        if i < len(indices[0]):
            index_val = indices[0][i]
            if index_val < len(metadata):
                # Retrieve fact_text from jsonl file
                fact_text = ""
                with open("data/nutrition_facts.jsonl", "r") as f:
                    for j, line in enumerate(f):
                        if j == index_val:
                            data = json.loads(line)
                            fact_text = data.get("fact_text", "")
                            break

                results.append({
                    "score": float(distances[0][i]),
                    "fact": fact_text,
                    "meta": metadata[index_val]
                })

    return results
