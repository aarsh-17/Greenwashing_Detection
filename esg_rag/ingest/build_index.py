import faiss
import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def build_index(paragraphs, index_path, meta_path):
    index_path = Path(index_path)
    meta_path = Path(meta_path)

    # 🔒 ENSURE DIRECTORIES EXIST
    index_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.parent.mkdir(parents=True, exist_ok=True)

    embeddings = model.encode([p["text"] for p in paragraphs])
    embeddings = np.array(embeddings).astype("float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    faiss.write_index(index, str(index_path))

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(paragraphs, f, indent=2)

    print(f"✅ FAISS index written to: {index_path.resolve()}")
    print(f"✅ Metadata written to: {meta_path.resolve()}")
    print(f"✅ Vectors indexed: {index.ntotal}")
