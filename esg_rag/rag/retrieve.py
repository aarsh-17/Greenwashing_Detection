import faiss
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path

model = SentenceTransformer("all-MiniLM-L6-v2")

def retrieve(claim, index_path, meta_path, k=3):
    # 🔒 Force paths to strings for FAISS
    index_path = str(index_path)
    meta_path = str(meta_path)

    index = faiss.read_index(index_path)

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    q = model.encode([claim["text"]])
    q = np.array(q).astype("float32")  # FAISS expects float32

    D, I = index.search(q, k)

    return [meta[i] for i in I[0]]
