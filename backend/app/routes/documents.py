from fastapi import APIRouter, UploadFile, File, Query
from datetime import datetime
import uuid
import shutil

from app.db.mongodb import documents_collection, claims_collection
from app.services.pdf_service import extract_text, split_sentences
from app.services.bert_service import predict_claim
from app.services.claim_cleanup import clean_claims
from app.services.scoring import greenwash_score
from app.services.svc_service import svc_predict_risk
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/documents", tags=["Documents"])


# =========================================================
# HYBRID RISK DECISION (ML DOMINANT)
# =========================================================
def hybrid_risk_decision(
    ml_level: str,
    ml_conf: float,
    rule_score: int
) -> str:
    """
    ML has priority.
    Rules can only escalate when ML confidence is low.
    """

    # ML says HIGH → final HIGH
    if ml_level == "HIGH":
        return "HIGH"

    # ML says MEDIUM → rule can escalate
    if ml_level == "MEDIUM":
        return "HIGH" if rule_score >= 70 else "MEDIUM"

    # ML says LOW → only escalate if ML uncertain + rules strong
    if ml_conf < 0.2 and rule_score >= 70:
        return "MEDIUM"

    return "LOW"


# =========================================================
# POST /documents/upload
# =========================================================
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    company: str = Query(..., description="Company name for ESG analysis")
):
    # ---------- 1. Save PDF ----------
    doc_id = str(uuid.uuid4())
    pdf_path = UPLOAD_DIR / f"{doc_id}.pdf"

    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # ---------- 2. Extract text ----------
    text = extract_text(pdf_path)
    sentences = split_sentences(text)

    # ---------- 3. BERT claim detection ----------
    raw_claims = []  # [(sentence, bert_conf)]
    for s in sentences:
        is_claim, conf = predict_claim(s)
        if is_claim:
            raw_claims.append((s, conf))

    # ---------- 4. Cleanup + dedup ----------
    cleaned_texts = clean_claims([c[0] for c in raw_claims])
    final_claims = [(t, c) for t, c in raw_claims if t in cleaned_texts]

    claims = []
    scores = []

    # ---------- 5. Hybrid ML + Rules ----------
    for text, bert_conf in final_claims:
        svc_level, svc_conf = svc_predict_risk(text)   # ML
        rule_score = greenwash_score(text)             # Rules

        final_risk = hybrid_risk_decision(
            ml_level=svc_level,
            ml_conf=svc_conf,
            rule_score=rule_score
        )

        claim_doc = {
            "_id": str(uuid.uuid4()),
            "document_id": doc_id,
            "company": company,
            "claim_text": text,

            # BERT
            "bert_confidence": round(bert_conf, 3),

            # ML
            "svc_risk_level": svc_level,
            "svc_confidence": round(svc_conf, 3),

            # Rules
            "rule_score": round(rule_score, 2),

            # Final
            "risk_level": final_risk,
            "created_at": datetime.utcnow()
        }

        claims.append(claim_doc)

        scores.append(
            {"LOW": 0, "MEDIUM": 75, "HIGH": 150}[final_risk]
        )

    # ---------- 6. Store claims ----------
    if claims:
        claims_collection.insert_many(claims)

    # ---------- 7. Store document ----------
    overall_score = round(sum(scores) / len(scores), 2) if scores else 0
    doc_risk = (
        "HIGH" if overall_score >= 70
        else "MEDIUM" if overall_score >= 40
        else "LOW"
    )

    documents_collection.insert_one({
        "_id": doc_id,
        "filename": file.filename,
        "company": company,
        "overall_score": overall_score,
        "risk_level": doc_risk,
        "total_claims": len(claims),
        "file_path": str(pdf_path),
        "created_at": datetime.utcnow()
    })

    return {
        "document_id": doc_id,
        "company": company,
        "overall_score": overall_score,
        "risk_level": doc_risk,
        "total_claims": len(claims)
    }


# =========================================================
# GET /documents/{document_id}/claims
# =========================================================
@router.get("/{document_id}/claims")
async def get_claims(document_id: str):
    cursor = claims_collection.find({"document_id": document_id})

    return [
        {
            "id": str(c["_id"]),
            "text": c["claim_text"],
            "riskLevel": c["risk_level"],
            "mlRisk": c["svc_risk_level"],
            "mlConfidence": c["svc_confidence"],
            "ruleScore": c["rule_score"],
            "type": "ESG Claim"
        }
        for c in cursor
    ]


# =========================================================
# GET /documents/{document_id}
# =========================================================
@router.get("/{document_id}")
async def get_document(document_id: str):
    doc = documents_collection.find_one({"_id": document_id})
    if not doc:
        return {"error": "Document not found"}

    claims = list(claims_collection.find({"document_id": document_id}))

    summary = {
        "totalClaims": len(claims),
        "esgClaims": len(claims),
        "riskyClaims": sum(
            1 for c in claims if c["risk_level"] in ["HIGH", "MEDIUM"]
        ),
        "offsetClaims": 0,
        "vagueClaims": 0,
        "proofBackedClaims": 0
    }

    return {
        "id": doc["_id"],
        "filename": doc["filename"],
        "score": doc["overall_score"],
        "riskLevel": doc["risk_level"],
        "summary": summary
    }


# =========================================================
# GET /documents
# =========================================================
@router.get("")
async def list_documents():
    cursor = documents_collection.find().sort("created_at", -1)

    return [
        {
            "id": d["_id"],
            "filename": d["filename"],
            "score": d.get("overall_score"),
            "riskLevel": d.get("risk_level", "").upper(),
            "status": "Analyzed"
        }
        for d in cursor
    ]
