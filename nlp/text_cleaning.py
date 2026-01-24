from pathlib import Path
import pandas as pd
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity



PROJECT_ROOT = Path("D:/ESG_platform")
INPUT_FILE = PROJECT_ROOT / "nlp" / "shell_claims_deduplicated.xlsx"
VOCAB_FILE = PROJECT_ROOT / "nlp" / "expanded_esg_keywords.txt"
OUTPUT_FILE = PROJECT_ROOT / "nlp" / "shell_claims_esg_filtered.xlsx"


def load_esg_vocab(path):
    vocab = {
        "environmental": set(),
        "social": set(),
        "governance": set()
    }

    current_section = None

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip().lower()

            if line.startswith("environmental"):
                current_section = "environmental"
            elif line.startswith("social"):
                current_section = "social"
            elif line.startswith("governance"):
                current_section = "governance"
            elif line and current_section and not line.startswith("="):
                words = [w.strip() for w in line.split(",")]
                vocab[current_section].update(words)

    return vocab

def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    return text

def keyword_esg_gate(sentence, vocab):
    s = normalize(sentence)

    scores = {
        "Environmental": sum(1 for w in vocab["environmental"] if w in s),
        "Social": sum(1 for w in vocab["social"] if w in s),
        "Governance": sum(1 for w in vocab["governance"] if w in s),
    }

    best = max(scores, key=scores.get)

    if scores[best] == 0:
        return None, 0

    return best, scores[best]

def compute_tfidf_scores(sentences):
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_df=0.85,
        min_df=2,
        stop_words="english"
    )

    X = vectorizer.fit_transform(sentences)

    # ESG centroid (average ESG language)
    centroid = np.asarray(X.mean(axis=0))  # FIX HERE

    # Similarity of each sentence to ESG centroid
    scores = cosine_similarity(X, centroid).flatten()

    return scores


def filter_esg_claims(claims_df, vocab, tfidf_threshold=0.6):
    # Step 1: keyword gate
    gated = []

    for _, row in claims_df.iterrows():
        pillar, score = keyword_esg_gate(row["claim_text"], vocab)
        if pillar:
            gated.append({
                **row,
                "pillar": pillar,
                "keyword_score": score
            })

    gated_df = pd.DataFrame(gated)
    if gated_df.empty:
        return gated_df
    
        # Step 2: TF-IDF classifier
    sentences = gated_df["claim_text"].tolist()

    tfidf_scores = compute_tfidf_scores(sentences)
    gated_df["tfidf_score"] = tfidf_scores


    gated_df["tfidf_score"] = tfidf_scores

        # Step 3: final filter
    final_df = gated_df[gated_df["tfidf_score"] >= tfidf_threshold]

    return final_df.reset_index(drop=True)



if __name__ == "__main__":
    claims_df = pd.read_excel(INPUT_FILE)

    vocab = load_esg_vocab(VOCAB_FILE)

    esg_df = filter_esg_claims(
        claims_df,
        vocab,
        tfidf_threshold=0.6
    )

    esg_df.to_excel(OUTPUT_FILE, index=False)

    print("ESG filtering complete")
    print(f"Initial claims: {len(claims_df)}")
    print(f"ESG claims kept: {len(esg_df)}")
    print(f"Saved to: {OUTPUT_FILE}")
