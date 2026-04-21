import re 
def enhanced_decision(ml_level, ml_conf, rule_score, rag_result):
    print(f"ML Level: {ml_level}, ML Conf: {ml_conf:.3f}, Rule Score: {rule_score}")
    # ---------- 1. Start with ML baseline ----------
    base = hybrid_risk_decision(ml_level, ml_conf, rule_score)

    if not rag_result:
        return base

    label = rag_result.get("label")
    grounded = True
    rag_conf = rag_result.get("confidence", 0)
    similarity = rag_result.get("similarity", 0)

    # ---------- 2. Strong RAG signals only ----------
    strong_rag = rag_conf > 0.5 and similarity > 0.7
    print(f"RAG confidence: {rag_conf:.3f}, similarity: {similarity:.3f}, strong_rag: {strong_rag}, label: {label}, grounded: {grounded}")

    # ---------- 3. Negative signals ----------
    if label == "UNSUPPORTED" and strong_rag:
        return "HIGH"

    if label == "MARKETING_LANGUAGE" and strong_rag:
        return "HIGH"

    # ---------- 4. Positive signals ----------
    if label == "SUPPORTED" and grounded and strong_rag:
        # Only downgrade if ML is not strongly confident
        if ml_level != "HIGH" or ml_conf < 0.8:
            return "LOW"

    # ---------- 5. Partial evidence ----------
    if label == "PARTIALLY_SUPPORTED" and strong_rag:
        return "MEDIUM"

    # ---------- 6. Weak RAG → fallback ----------
    return base

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

def count_numbers(text: str) -> int:
    # matches integers, decimals, currency-like values
    return len(re.findall(r'\b\d+(\.\d+)?\b', text))