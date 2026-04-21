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
You are an adversarial auditor reviewing a prior verification decision.

Your job is NOT to determine if the claim is supported.

Your job is to find flaws in the reasoning.

---

TASK:

Check whether the evidence used to support the claim is actually valid.

---

You MUST aggressively challenge the following:

1. METRIC MISMATCH
   - Does the evidence measure the SAME thing?

2. TEMPORAL MISMATCH
   - Claim = achieved
   - Evidence = planned or expected

3. EVIDENCE QUALITY
   - Are there real numbers, results, or outcomes?
   - Or just vague descriptions?

4. CAUSALITY GAP
   - Does the evidence prove the claim?
   - Or just relate to it?

5. WEAK SUPPORT
   - Is the support partial, indirect, or incomplete?

---

IMPORTANT:

- Even small flaws → respond NO
- If evidence is not airtight → NO
- Be more strict than the verifier

---

OUTPUT:
YES (evidence is truly solid)
NO (evidence is flawed, weak, or misleading)

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