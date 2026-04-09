import faiss
import numpy as np
import json
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_community.docstore import InMemoryDocstore

from app.embeddings import get_embeddings
from app.vectorstore.chunk_data import chunk_documents
from app.vectorstore.load_data import load_documents


def build_vectorstore_for_pdf(doc_id: str, pdf_path: str):

    # ---------- LOAD + CLEAN ----------
    documents = load_documents(pdf_path)
    print(f"[{doc_id}] Cleaned pages: {len(documents)}")

    # ---------- CHUNK ----------
    chunks = chunk_documents(documents)
    print(f"[{doc_id}] Total chunks: {len(chunks)}")

    # ---------- SAVE PREVIEW JSON ----------
    preview_data = []
    for chunk in chunks:
        preview_data.append({
            "chunk_id": chunk.metadata.get("chunk_id"),
            "source": chunk.metadata.get("source"),
            "page": chunk.metadata.get("page"),
            "text": chunk.page_content
        })

    preview_path = Path(f"vectorstore/{doc_id}/chunks_preview.json")
    preview_path.parent.mkdir(parents=True, exist_ok=True)

    with open(preview_path, "w", encoding="utf-8") as f:
        json.dump(preview_data, f, indent=2, ensure_ascii=False)

    print(f"[{doc_id}] Preview saved at {preview_path}")

    # ---------- EMBEDDINGS ----------
    embeddings = get_embeddings()
    texts = [chunk.page_content for chunk in chunks]

    vectors = np.array(embeddings.embed_documents(texts)).astype("float32")
    dimension = vectors.shape[1]

    index = faiss.IndexFlatIP(dimension)
    index.add(vectors)

    # ---------- DOCSTORE ----------
    docstore = InMemoryDocstore(
        {str(i): chunks[i] for i in range(len(chunks))}
    )

    index_to_docstore_id = {i: str(i) for i in range(len(chunks))}

    db = FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=docstore,
        index_to_docstore_id=index_to_docstore_id
    )

    # ---------- SAVE ----------
    path = Path(f"vectorstore/{doc_id}")
    path.mkdir(parents=True, exist_ok=True)

    db.save_local(str(path))

    print(f"[{doc_id}] Vector store created at {path}")

    return str(path)