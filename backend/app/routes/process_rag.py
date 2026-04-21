import os
from fastapi import APIRouter
from app.db.mongodb import claims_collection, documents_collection
from app.services.rag_service import verify_claim_with_rag
from app.utils.score import enhanced_decision
import traceback
router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/process-rag")
async def process_rag(doc_id: str):

    # ---------- 1. Fetch claims ----------
    claims = list(claims_collection.find({"document_id": doc_id}))

    if not claims:
        return {"error": "No claims found"}

    index_path = f"vectorstore/{doc_id}"

    scores = []

    for c in claims:

        svc_level = c["svc_risk_level"]
        svc_conf = c["svc_confidence"]
        rule_score = c["rule_score"]

        # ---------- 2. Decide if RAG needed ----------
        run_rag = (
            svc_level == "HIGH"
        )

        rag_result = None

        if run_rag:
            rag_result = verify_claim_with_rag(c["claim_text"], index_path)

        # ---------- 3. Final decision ----------
        final_risk = enhanced_decision(
            svc_level,
            svc_conf,
            rule_score,
            rag_result
        )

        # ---------- 4. Update DB ----------
        update_data = {
            "risk_level": final_risk,
            "rag_status": "DONE" if rag_result else "SKIPPED"
        }
        
        if rag_result:
            update_data.update({
                "rag_label": rag_result.get("label"),
                "rag_confidence": round(rag_result.get("confidence", 0), 3),
                "rag_similarity": round(rag_result.get("similarity", 0), 3),
                "rag_grounded": rag_result.get("grounded"),
                "rag_citations": rag_result.get("citations", [])
            })

        claims_collection.update_one(
            {"_id": c["_id"]},
            {"$set": update_data}
        )

        scores.append(
            {"LOW": 0, "MEDIUM": 75, "HIGH": 150}[final_risk]
        )

    # ---------- 5. Update document ----------
    overall_score = round(sum(scores) / len(scores), 2) if scores else 0

    doc_risk = (
        "HIGH" if overall_score >= 70
        else "MEDIUM" if overall_score >= 40
        else "LOW"
    )

    documents_collection.update_one(
        {"_id": doc_id},
        {
            "$set": {
                "overall_score": overall_score,
                "risk_level": doc_risk,
                "rag_completed": True
            }
        }
    )

    return {
        "document_id": doc_id,
        "overall_score": overall_score,
        "risk_level": doc_risk,
        "status": "rag_completed"
    }

@router.post("/run-rag-claim")
async def run_rag_claim(claim_id: str):
    print(f"Running RAG for claim_id: {claim_id}")

    try:
        c = claims_collection.find_one({"_id": claim_id})
        if not c:
            return {"error": "Claim not found"}

        index_path = f"vectorstore/{c['document_id']}"

        # ---------- RAG ----------
        try:
            rag_result = verify_claim_with_rag(c["claim_text"], index_path)
        except Exception:
            print("Error in verify_claim_with_rag:")
            traceback.print_exc()
            rag_result = None

        # ---------- DECISION ----------
        try:
            final_risk = enhanced_decision(
                c["svc_risk_level"],
                c["svc_confidence"],
                c["rule_score"],
                rag_result
            )
        except Exception:
            print("Error in enhanced_decision:")
            traceback.print_exc()
            return {"error": "Decision step failed"}

        preview_data = {
            "risk_level": final_risk,
            "rag_label": rag_result.get("label") if rag_result else None,
            "rag_confidence": rag_result.get("confidence") if rag_result else None,
            "rag_similarity": rag_result.get("similarity") if rag_result else None,
            "rag_grounded": rag_result.get("grounded") if rag_result else None,
            "textual_evidence": rag_result.get("top_chunks", []) if rag_result else []
        }

        print(f"Preview for {claim_id}: {preview_data['rag_label']}\tConfidence: {preview_data['rag_confidence']}\tFinal Risk:            {preview_data['risk_level']}\ncitations: {rag_result.get('citations', []) if rag_result else 'N/A'}")

        # ✅ STORE AS PREVIEW ONLY
        claims_collection.update_one(
            {"_id": claim_id},
            {
                "$set": {
                    "rag_preview": preview_data,
                    "rag_status": "PREVIEW_READY"
                }
            }
        )

        return {
            "status": "preview_ready",
            "data": preview_data
        }

    except Exception:
        print("Unexpected error in run_rag_claim:")
        traceback.print_exc()
        return {"error": "RAG failed"}
    
@router.post("/apply-rag")
async def apply_rag_update(claim_id: str):
    try:
        c = claims_collection.find_one({"_id": claim_id})
        if not c:
            return {"error": "Claim not found"}

        preview = c.get("rag_preview")
        if not preview:
            return {"error": "Run RAG first"}

        document_id = c["document_id"]

        # ---------- 1. Update claim ----------
        update_data = {
            "risk_level": preview.get("risk_level"),
            "rag_label": preview.get("rag_label"),
            "rag_confidence": preview.get("rag_confidence"),
            "rag_similarity": preview.get("rag_similarity"),
            "rag_grounded": preview.get("rag_grounded"),
            "textual_evidence": preview.get("textual_evidence"),
            "rag_status": "DONE",
            "rag_applied": True
        }

        claims_collection.update_one(
            {"_id": claim_id},
            {"$set": update_data}
        )

        # ---------- 2. Recalculate document score ----------
        remaining_claims = list(
            claims_collection.find({"document_id": document_id})
        )

        if remaining_claims:
            scores = [
                {"LOW": 0, "MEDIUM": 75, "HIGH": 150}[c["risk_level"]]
                for c in remaining_claims
            ]

            overall_score = round(sum(scores) / len(scores), 2)

            doc_risk = (
                "HIGH" if overall_score >= 70
                else "MEDIUM" if overall_score >= 40
                else "LOW"
            )
        else:
            overall_score = 0
            doc_risk = "LOW"

        # ---------- 3. Update document ----------
        documents_collection.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "overall_score": overall_score,
                    "risk_level": doc_risk,
                    "total_claims": len(remaining_claims)
                }
            }
        )

        return {
            "status": "applied",
            "claim_id": claim_id,
            "new_score": overall_score,
            "risk_level": doc_risk
        }

    except Exception:
        traceback.print_exc()
        return {"error": "Apply failed"}