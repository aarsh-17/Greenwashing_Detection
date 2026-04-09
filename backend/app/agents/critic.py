import re
from ..llm import llm


def has_quantitative_evidence(text):
    patterns = [
        r"\d+%",                     # percentages
        r"\d+\s?(tons|kg|MW|kWh|CO2)",  # units
        r"\d{4}",                    # years
        r"(reduced|decreased|increased|achieved|improved)\s+by\s+\d+"
    ]
    return any(re.search(p, text.lower()) for p in patterns)


def is_future_or_marketing_claim(claim):
    patterns = [
        "working to",
        "aim",
        "target",
        "plan",
        "committed to",
        "will",
        "expected to",
        "designed to"
    ]
    return any(p in claim.lower() for p in patterns)


def critic(state):
    verdict = state.get("verdict", "")
    context = state.get("context", "")
    claim = state.get("query", "")
    confidence = state.get("confidence", 0.0)

    # --------------------------------------------------
    # 1. HARD ALIGNMENT WITH VERIFIER (CRITICAL)
    # --------------------------------------------------
    if verdict in ["MARKETING_LANGUAGE", "UNSUPPORTED"]:
        grounded = False
        confidence = round(confidence * 0.6, 3)

        print(f"Critic override: {verdict} → grounded = False")

        return {
            **state,
            "grounded": grounded,
            "confidence": confidence
        }

    # --------------------------------------------------
    # 2. RULE-BASED CHECKS
    # --------------------------------------------------

    quant_evidence = has_quantitative_evidence(context)
    forward_claim = is_future_or_marketing_claim(claim)

    # If forward-looking claim without measurable results → NOT grounded
    if forward_claim and not quant_evidence:
        grounded = False
        confidence = round(confidence * 0.7, 3)

        print("Critic rule: forward-looking without evidence → NO")

        return {
            **state,
            "grounded": grounded,
            "confidence": confidence
        }

    # --------------------------------------------------
    # 3. LLM EVALUATION (ONLY WHEN NECESSARY)
    # --------------------------------------------------

    prompt = f"""
You are an ESG greenwashing detection agent.

Your task is to determine whether the CONTEXT provides DIRECT, SUBSTANTIVE EVIDENCE that supports the CLAIM.

---

DEFINITION OF SUBSTANTIVE EVIDENCE:

The context MUST include:
- Completed actions OR
- Measurable outcomes OR
- Verified implementation

---

STRICT RULES:

1. Evidence must be directly related to the CLAIM.

2. METRIC ALIGNMENT RULE:
   - The evidence MUST refer to the SAME metric as the CLAIM.
   - Example:
     Claim: methane emissions
     Evidence: energy intensity → NOT valid
   → respond NO

3. FORWARD-LOOKING RULE:
   - If the CLAIM includes:
     "target", "aim", "plan", "working to", "committed to", "will", "by 20XX"
   - Then evidence must show:
     → actual results OR measurable progress
   - Otherwise → NO

4. Future or design statements are NOT evidence:
   - "expected to", "designed to", "will"
   → NO

5. Ignore:
   - general sustainability statements
   - explanations (e.g., LNG vs coal)
   - background information

6. RELEVANCE RULE:
   - If the context contains real actions NOT directly tied to the CLAIM,
     they MUST be ignored.

7. Repetition of claim without proof → NO

---

EDGE CASE:

If you are unsure or evidence is weak → respond NO

---

CLAIM:
{claim}

---

CONTEXT:
{context}

---

OUTPUT:

Respond with ONLY one word:
YES
or
NO
"""

    response = llm.invoke(prompt).strip().upper()

    grounded = response == "YES"

    print(f"Critic response: {response} (grounded: {grounded})")

    # --------------------------------------------------
    # 4. CONFIDENCE UPDATE
    # --------------------------------------------------

    if grounded:
        confidence = min(1.0, round(confidence + 0.2, 3))
    else:
        confidence = round(confidence * 0.7, 3)

    return {
        **state,
        "grounded": grounded,
        "confidence": confidence
    }