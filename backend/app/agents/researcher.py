from ..utils.reranker import rerank
import math
import re

BGE_PREFIX = "Represent this sentence for searching relevant passages: "
DEBUG = True


# -------------------------------
# Utilities
# -------------------------------

def clean_citations(citations):
    seen = set()
    cleaned = []

    for c in citations:
        key = (c["source"], c["page"], c["chunk_id"])
        if key not in seen:
            seen.add(key)
            cleaned.append(c)

    return cleaned


def sigmoid_normalize(x, scale=3.0):
    return 1 / (1 + math.exp(-x / scale))


# -------------------------------
# Evidence Scoring
# -------------------------------

def evidence_strength(text):
    text = text.lower()

    numbers = len(re.findall(r"\b\d+(\.\d+)?\b", text))
    units = len(re.findall(r"(tonnes|%|percent|kg|co2|methane|emissions|mwh|litres)", text))
    time_refs = len(re.findall(r"(20\d{2}|compared with|from \d{4}|in \d{4})", text))
    change_patterns = len(re.findall(
        r"(decrease|increase|reduction|growth|decline|rise|fell|rose)",
        text
    ))

    score = (
        0.3 * min(numbers, 3) +
        0.3 * min(units, 3) +
        0.2 * min(time_refs, 2) +
        0.2 * min(change_patterns, 2)
    )

    return score


def speculative_score(text):
    text = text.lower()

    patterns = [
        r"\btesting\b",
        r"\bdevelop(ing|ment)?\b",
        r"\bworking to\b",
        r"\baim(s|ed)? to\b",
        r"\btarget(s|ed)?\b",
        r"\bplan(s|ned)? to\b"
    ]

    return sum(bool(re.search(p, text)) for p in patterns)


def contradiction_signal(text):
    text = text.lower()

    patterns = [
        r"\bunfeasible\b",
        r"\bnot achieved\b",
        r"\bfailed\b",
        r"\bincrease(d)?\b.*\bemissions\b",
        r"\bhigher emissions\b"
    ]

    return sum(bool(re.search(p, text)) for p in patterns)


def final_chunk_score(rerank_score, text):
    return (
        0.5 * rerank_score +
        0.3 * evidence_strength(text) -
        0.2 * speculative_score(text) +
        0.2 * contradiction_signal(text)
    )


def tag_chunk(text):
    es = evidence_strength(text)
    ss = speculative_score(text)
    cs = contradiction_signal(text)

    if cs > 0:
        return "CONTRADICTION"
    if es > 0.8:
        return "EVIDENCE"
    if ss > 0:
        return "R&D/TARGET"
    return "BACKGROUND"


# -------------------------------
# Main Researcher
# -------------------------------

def researcher(state, retriever):
    query = state["query"]
    formatted_query = BGE_PREFIX + query

    # ---------- Step 1: Retrieve ----------
    docs_with_scores = retriever.vectorstore.similarity_search_with_score(
        formatted_query,
        k=10
    )

    if not docs_with_scores:
        return {
            **state,
            "context": "",
            "documents": [],
            "citations": [],
            "top_3_chunks": [],
            "top_similarity": 0.0,
            "faiss_score": 0.0
        }

    faiss_score = float(docs_with_scores[0][1])

    # ---------- Step 2: Rerank ----------
    reranked = rerank(query, docs_with_scores, top_k=5)

    reranked_norm = []
    for doc, _, raw, meta in reranked:
        norm = sigmoid_normalize(raw)
        reranked_norm.append((doc, raw, norm, meta))
    
    for doc, raw, norm, meta in reranked_norm:
        if DEBUG:
            print(f"Chunk: {doc.page_content[:100]}... | Raw: {raw:.4f} | Norm: {norm:.4f}")


    # ---------- Step 3: Final Scoring ----------
    scored_chunks = []

    for doc, raw, norm, meta in reranked_norm:
        text = doc.page_content
        score = final_chunk_score(norm, text)
        scored_chunks.append((doc, raw, norm, score))

    # sort by relevance (norm)
    scored_chunks.sort(key=lambda x: x[2], reverse=True)

    # ---------- Step 4: Similarity Cluster Selection ----------
    MIN_THRESHOLD = 0.7
    SIMILARITY_GAP = 0.08

    selected = []

    if scored_chunks:
        top_norm = scored_chunks[0][2]

        for doc, raw, norm, score in scored_chunks:
            if norm < MIN_THRESHOLD:
                continue

            # include if close to top OR strong evidence
            if (top_norm - norm) <= SIMILARITY_GAP or evidence_strength(doc.page_content) > 0.8:
                selected.append((doc, raw, norm, score))

    # fallback (if nothing selected)
    if not selected:
        selected = scored_chunks[:3]

    # limit to top 3
    selected = selected[:3]

    # ---------- Step 5: Build Context ----------
    context_blocks = []
    top_3_chunks = []

    for i, (doc, raw, norm, final_score) in enumerate(selected):
        text = doc.page_content
        tag = tag_chunk(text)

        block = f"[Chunk {i+1} | type={tag} | relevance={norm:.2f} | final={final_score:.2f}]\n{text}"
        context_blocks.append(block)

        top_3_chunks.append({
            "chunk_id": doc.metadata.get("chunk_id"),
            "source": doc.metadata.get("source"),
            "page": doc.metadata.get("page"),
            "text": text,
            "rerank_score": float(norm),
            "final_score": float(final_score),
            "type": tag
        })

    context = "\n\n".join(context_blocks)
    print("Selected Context:\n", context)

    # ---------- Step 6: Citations ----------
    citations = [
        {
            "source": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page"),
            "chunk_id": doc.metadata.get("chunk_id"),
            "score": float(norm)
        }
        for doc, _, norm, _ in scored_chunks
    ]

    citations = clean_citations(citations)

    # ---------- Final Similarity ----------
    rerank_top = selected[0][2]
    top_similarity = round(0.4 * faiss_score + 0.6 * rerank_top, 4)

    return {
        **state,
        "context": context,
        "documents": [doc for doc, _, _, _ in scored_chunks],
        "citations": citations,
        "top_3_chunks": top_3_chunks,
        "top_similarity": top_similarity,
        "faiss_score": faiss_score,
        "rerank_score": rerank_top
    }