
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import os

def build_faiss_index(jsonl_path: str, model_name: str, index_path: str, embeddings_path: str, metadata_path: str):
    """
    Builds a FAISS index from the fact text in a JSONL file.
    """
    if not os.path.exists(os.path.dirname(index_path)):
        os.makedirs(os.path.dirname(index_path))

    # Load the sentence transformer model
    model = SentenceTransformer(model_name)

    # Read the fact texts and metadata from the JSONL file
    fact_texts = []
    metadata = []
    with open(jsonl_path, "r") as f:
        for line in f:
            data = json.loads(line)
            fact_texts.append(data["fact_text"])
            metadata.append(data["meta"])

    # Encode the fact texts into embeddings
    print("Encoding fact texts...")
    embeddings = model.encode(fact_texts, convert_to_numpy=True, show_progress_bar=True)

    # Normalize the embeddings to unit length
    faiss.normalize_L2(embeddings)

    # Build the FAISS index
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    # Save the index, embeddings, and metadata
    print(f"Saving FAISS index to {index_path}")
    faiss.write_index(index, index_path)

    print(f"Saving embeddings to {embeddings_path}")
    np.save(embeddings_path, embeddings)

    print(f"Saving metadata to {metadata_path}")
    with open(metadata_path, "w") as f:
        for m in metadata:
            f.write(json.dumps(m) + "\n")

    print("Index building complete.")
