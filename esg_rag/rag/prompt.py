def build_prompt(claim, benchmarks):
    """
    Build a tightly constrained prompt for ESG plausibility evaluation.
    The model is forced into evidence-bounded comparative reasoning.
    """

    if not benchmarks:
        context = "NO RELEVANT BENCHMARKS PROVIDED."
    else:
        context = "\n".join(
            f"- {b['text']} "
            f"(Scenario: {b.get('scenario', 'Unspecified')}, "
            f"Sector: {b.get('primary_sector', 'Unspecified')}, "
            f"Time: {b.get('time_bucket', 'Unspecified')})"
            for b in benchmarks
        )

    return f"""
You are an ESG plausibility evaluation engine.

Your task is to assess whether the CLAIM is feasible **only** relative to the BENCHMARKS provided.

STRICT RULES (MANDATORY):
- Use ONLY the benchmarks listed below.
- Do NOT introduce external facts, trends, or background knowledge.
- Do NOT infer structural shifts (e.g., energy transition) unless explicitly stated.
- Do NOT generalize across regions, sectors, or geographies unless benchmarks explicitly do so.
- If a benchmark is regional or sector-specific, treat it as such.
- If no benchmark directly supports or contradicts the claim, state: "Insufficient benchmark evidence."
- Do NOT judge intent, credibility, or truthfulness.
- Evaluate feasibility only.

CLAIM:
{claim['text']}

BENCHMARKS:
{context}

ANALYSIS STEPS (FOLLOW IN ORDER):
1. Identify which benchmarks are directly comparable to the claim (same sector, scope, and timeframe).
2. Compare magnitude (scale of change).
3. Compare timeline (speed and duration).
4. State whether the claim is:
   - Within benchmark ranges
   - Exceeds benchmark magnitude or pace
   - Unsupported due to missing comparable benchmarks

OUTPUT REQUIREMENTS:
- Write a short, factual plausibility explanation (1-2 sentences).
- Every analytical statement must be grounded in a benchmark above.
- If benchmarks are insufficient, explicitly say so.
- Do NOT speculate.

BEGIN ANALYSIS.
"""
