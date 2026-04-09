def needs_llm(query: str) -> bool:
    q = query.lower()

    # Simple factual queries → no LLM
    if q.startswith(("how many", "when", "where", "what is")):
        return False

    # Short queries are usually unambiguous
    if len(q.split()) < 6:
        return False

    return True
