# routes/ingestion.py

import uuid
import shutil
from fastapi import APIRouter, UploadFile, File
from pathlib import Path
from app.services.embedding_service import build_vectorstore_for_pdf  

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/ingest-document")
async def ingest_document(file: UploadFile = File(...)):

    doc_id = str(uuid.uuid4())
    pdf_path = UPLOAD_DIR / f"{doc_id}.pdf"

    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    index_path = build_vectorstore_for_pdf(doc_id, str(pdf_path))

    return {
        "doc_id": doc_id,
        "vectorstore_path": index_path
    }
