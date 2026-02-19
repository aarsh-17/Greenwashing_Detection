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
from app.hash_utils import sha256_file, sha256_json
from app.services.blockchain_service import store_on_chain as store_document_on_chain, get_document_from_chain

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

# =========================================================
# POST /documents/{document_id}/anchor
# =========================================================
@router.post("/{document_id}/anchor")
async def anchor_document_to_blockchain(document_id: str):
    # ---------- 1. Fetch document ----------
    doc = documents_collection.find_one({"_id": document_id})
    if not doc:
        return {"error": "Document not found"}

    # Prevent double anchoring
    if doc.get("blockchain_tx"):
        return {
            "status": "ALREADY_ANCHORED",
            "blockchain_tx": doc["blockchain_tx"]
        }

    # ---------- 2. Hash PDF ----------
    pdf_hash = sha256_file(doc["file_path"])

    # ---------- 3. Hash final results ----------
    result_payload = {
        "document_id": document_id,
        "company": doc["company"],
        "overall_score": doc["overall_score"],
        "risk_level": doc["risk_level"],
        "total_claims": doc["total_claims"]
    }

    result_hash = sha256_json(result_payload)

    # ---------- 4. Push to blockchain ----------
    tx_hash = store_document_on_chain(
        document_id=document_id,
        pdf_hash=pdf_hash,
        result_hash=result_hash,
        company=doc["company"],
        score=int(doc["overall_score"]),
        risk_level=doc["risk_level"]
    )

    # ---------- 5. Update MongoDB ----------
    documents_collection.update_one(
        {"_id": document_id},
        {
            "$set": {
                "pdf_hash": pdf_hash,
                "result_hash": result_hash,
                "blockchain_tx": tx_hash,
                "anchored_at": datetime.utcnow()
            }
        }
    )

    # ---------- 6. Return response ----------
    return {
        "status": "ANCHORED",
        "document_id": document_id,
        "blockchain_tx": tx_hash,
        "explorer": f"https://amoy.polygonscan.com/tx/{tx_hash}"
    }


# =========================================================
# GET /documents/{document_id}/verify-onchain
# =========================================================
@router.get("/{document_id}/verify-onchain")
async def verify_document_onchain(document_id: str):

    # ---------- 1. Fetch from MongoDB ----------
    doc = documents_collection.find_one({"_id": document_id})
    if not doc:
        return {"status": "NOT_FOUND"}

    if not doc.get("blockchain_tx"):
        return {"status": "NOT_ANCHORED"}

    # ---------- 2. Recompute local hashes ----------
    local_pdf_hash = sha256_file(doc["file_path"])

    local_payload = {
        "document_id": document_id,
        "company": doc["company"],
        "overall_score": doc["overall_score"],
        "risk_level": doc["risk_level"],
        "total_claims": doc["total_claims"]
    }

    local_result_hash = sha256_json(local_payload)

    # ---------- 3. Fetch on-chain data ----------
    try:
        chain_data = get_document_from_chain(document_id)
    except Exception as e:
        return {"status": "CHAIN_ERROR", "error": str(e)}

    # ---------- 4. Compare ----------
    pdf_match = local_pdf_hash == chain_data["pdf_hash"]
    result_match = local_result_hash == chain_data["result_hash"]

    if pdf_match and result_match:
        status = "VERIFIED"
    else:
        status = "TAMPERED"

    return {
        "status": status,
        "pdf_hash_match": pdf_match,
        "result_hash_match": result_match,
        "blockchain_tx": doc["blockchain_tx"],
        "explorer": f"https://amoy.polygonscan.com/tx/{doc['blockchain_tx']}",
        "anchored_timestamp": chain_data["timestamp"]
    }

