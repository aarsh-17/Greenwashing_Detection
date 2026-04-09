from fastapi import FastAPI
from app.routes.documents import router as document_router
from app.routes import ingestion
from app.routes.process_rag import router as rag_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Greenwashing Detection API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document_router)
app.include_router(ingestion.router, prefix="/api")
app.include_router(rag_router, prefix="/api")