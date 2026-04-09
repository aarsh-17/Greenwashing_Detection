from sentence_transformers import CrossEncoder

reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank(query, docs_with_scores, top_k=5, debug=False):
    if not docs_with_scores:
        return []

    pairs = [(query, doc.page_content) for doc, _ in docs_with_scores]
    rerank_scores = reranker_model.predict(pairs)

    reranked = []

    for (doc, embed_score), rerank_score in zip(docs_with_scores, rerank_scores):
        # 🔥 HYBRID SCORE (KEY FIX)
        final_score = 0.7 * float(rerank_score) + 0.3 * float(embed_score)

        reranked.append((doc, float(embed_score), float(rerank_score), final_score))

    # 🔍 DEBUG BEFORE
    if debug:
        print("\n========== BEFORE HYBRID SORT ==========")
        for i, (doc, e, r, f) in enumerate(reranked):
            print(f"[{i}] embed={e:.4f} | rerank={r:.4f} | final={f:.4f} | chunk={doc.metadata.get('chunk_id')}")

    # ✅ SORT BY FINAL SCORE (NOT rerank alone)
    reranked.sort(key=lambda x: x[3], reverse=True)

    # 🔍 DEBUG AFTER
    if debug:
        print("\n========== AFTER HYBRID SORT ==========")
        for i, (doc, e, r, f) in enumerate(reranked[:top_k]):
            print(f"[{i}] embed={e:.4f} | rerank={r:.4f} | final={f:.4f} | chunk={doc.metadata.get('chunk_id')}")
        print("========================================\n")

    return reranked[:top_k]