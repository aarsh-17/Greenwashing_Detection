import re

def lightweight_rewrite(query: str) -> str:
    q = query.lower()

    # normalize question forms
    q = re.sub(r"\bhow many\b", "number of", q)
    q = re.sub(r"\bwhat is\b", "definition of", q)
    q = re.sub(r"\bused\b", "utilized", q)

    # expand common abbreviations
    expansions = {
        r"\bgpu\b": "graphics processing unit",
        r"\bgpus\b": "graphics processing units",
        r"\bml\b": "machine learning",
        r"\bnlp\b": "natural language processing",
    }

    for pattern, replacement in expansions.items():
        q = re.sub(pattern, replacement, q)

    # add weak context hints (safe, generic)
    if "training" in q and "model" not in q:
        q += " during model training"

    return q
