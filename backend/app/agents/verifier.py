from ..llm import llm

SIMILARITY_THRESHOLD = 0.5  # softer filter


def verifier(state):
    claim = state.get("query", "")
    similarity = state.get("top_similarity", 0.0)
    claim_type = state.get("claim_type", "general")
    top_chunks = state.get("top_3_chunks", [])

    # 🚫 Early exit (only if very weak)
    if similarity < SIMILARITY_THRESHOLD:
        print(f"Similarity {similarity:.3f} below threshold. Marking as UNSUPPORTED.")
        return {
            **state,
            "verdict": "UNSUPPORTED",
            "confidence": round(similarity, 3),
            "done": True
        }

    context="\n\n".join([c["text"] for c in top_chunks])
    # Type-specific instructions
    type_instruction = ""

    if claim_type == "quantitative":
        type_instruction = """
- The claim includes numbers or percentages.
- The EXACT same value and timeframe must appear.
- Approximate matches = PARTIALLY_SUPPORTED.
- Missing numbers = UNSUPPORTED.
"""

    elif claim_type == "forward-looking":
        type_instruction = """
- Identify if statement is:
    * Achieved (past)
    * Ongoing
    * Intent/ambition
- Intent without execution = MARKETING_LANGUAGE.
"""

    prompt = f"""
You are a strict ESG claim verification agent.

Your task is to determine whether the CONTEXT provides VALID EVIDENCE that supports the CLAIM.

You must rely ONLY on the provided CONTEXT.
Do NOT use external knowledge.
If uncertain, choose the stricter label.

---

OUTPUT (choose EXACTLY one):

SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED
MARKETING_LANGUAGE

---

CORE PRINCIPLE:

The CONTEXT must PROVE the CLAIM using real, relevant, and measurable evidence.
Relevance alone is NOT sufficient.

---

DEFINITIONS:

SUPPORTED:
- The claim is fully backed by clear, direct, and explicit evidence
- Evidence includes:
  - Completed actions
  - Measurable outcomes (numbers, % change, metrics)
  - Verified implementation
- Evidence matches the SAME metric, scope, and objective as the claim

---

PARTIALLY_SUPPORTED:
- Some relevant evidence exists but is incomplete or indirect
- Examples:
  - Evidence supports only part of the claim
  - Metrics are related but not exact
  - Evidence lacks full clarity or completeness

---

UNSUPPORTED:
- No valid supporting evidence is present
- Context does not address the claim
- Evidence is unrelated or misaligned with the claim

---

MARKETING_LANGUAGE:
- The claim cannot be verified using evidence
- Includes:
  - vague or non-measurable statements
  - effort-based language (e.g., “working to”, “helping to”)
  - aspirational or descriptive claims without proof

---

STRICT RULES (CRITICAL):

1. EVIDENCE REQUIREMENT:
   - Only treat statements as evidence if they describe:
     → completed actions
     → measurable outcomes
     → actual implementation
   - If none exist → MARKETING_LANGUAGE or UNSUPPORTED

---

2. CONCEPT ALIGNMENT RULE (VERY IMPORTANT):
   - The evidence must support the SAME objective as the claim

   Examples:
   - Claim: circular economy for plastics  
     Evidence: plastic reduction  
     → NOT VALID SUPPORT

   - Claim: methane emissions reduction  
     Evidence: energy efficiency  
     → NOT VALID SUPPORT

   If the objective differs:
   → UNSUPPORTED

---

3. NUMBERS RULE:
   - Numbers must represent actual achieved results
   - Targets, projections, or expected values do NOT count

---

4. RELEVANCE VS EVIDENCE:
   - High similarity is NOT enough
   - The context must directly prove the claim

---

5. IGNORE NON-EVIDENCE:
   Do NOT treat the following as evidence:
   - explanations
   - general sustainability statements
   - plans, intentions, or descriptions
   - partnerships or agreements without results

---

6. REPEATED CLAIM RULE:
   - If the context repeats or paraphrases the claim without proof
   → UNSUPPORTED

---

7. STRICTNESS:
   - If evidence is weak, vague, or indirect:
     → prefer MARKETING_LANGUAGE or UNSUPPORTED over SUPPORTED

---

FINAL DECISION LOGIC:

- Clear, direct, measurable proof → SUPPORTED  
- Partial or indirect proof → PARTIALLY_SUPPORTED  
- No valid or aligned evidence → UNSUPPORTED  
- Only vague or effort-based statements → MARKETING_LANGUAGE  

---

CLAIM:
{claim}

---

CONTEXT:
{context}

---

FINAL INSTRUCTION:

Return ONLY one word:
SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED
MARKETING_LANGUAGE
"""

    verdict = llm.invoke(prompt).strip().upper()

    # ✅ Improved confidence calibration
    if verdict == "SUPPORTED":
        confidence = 0.7 + (0.3 * similarity)

    elif verdict == "PARTIALLY_SUPPORTED":
        confidence = 0.4 + (0.3 * similarity)

    elif verdict == "MARKETING_LANGUAGE":
        confidence = 0.3 + (0.2 * similarity)

    else:  # UNSUPPORTED
        confidence = 0.2 * similarity

    print(f"Verifier verdict: {verdict} | similarity: {similarity:.3f} | confidence: {confidence:.3f}")

    return {
        **state,
        "verdict": verdict,
        "confidence": round(confidence, 3),
        "done": True
    }