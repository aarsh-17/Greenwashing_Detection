import spacy
import uuid
import re
import numpy as np
from langchain_core.documents import Document

# Load SpaCy medium model (has word vectors)
nlp = spacy.load("en_core_web_md")


# -----------------------------
# Text Cleaning
# -----------------------------
def clean_text(text: str) -> str:
    # Fix broken single line breaks
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    # Remove multiple newlines
    text = re.sub(r"\n{2,}", "\n\n", text)

    # Remove weird icon characters
    text = re.sub(r"[]+", "", text)

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# -----------------------------
# Heading Detection (Structural Split)
# -----------------------------
def is_heading(sentence: str) -> bool:
    sentence = sentence.strip()

    # ALL CAPS headings
    if sentence.isupper() and len(sentence) < 120:
        return True

    # Ends with colon
    if sentence.endswith(":"):
        return True

    # Numbered section (e.g., 1.2.3)
    if re.match(r"^\d+(\.\d+)*", sentence):
        return True

    return False


# -----------------------------
# Semantic Chunking
# -----------------------------
def chunk_documents(
    documents,
    max_chars: int = 1200,
    min_chunk_chars: int = 300,
    similarity_threshold: float = 0.75,
):
    """
    Narrative semantic chunking (no tables).
    Uses centroid-based semantic drift detection with L2 normalization.
    """

    final_chunks = []

    for doc in documents:
        raw_text = doc.page_content
        text = clean_text(raw_text)

        spacy_doc = nlp(text)

        sentences = [
            sent.text.strip()
            for sent in spacy_doc.sents
            if len(sent.text.strip()) > 40
            and any(c.isalpha() for c in sent.text)
        ]

        if not sentences:
            continue

        current_chunk = []
        sum_vector = None
        sentence_count = 0
        current_length = 0

        for sentence in sentences:
            # Structural heading split
            if current_chunk and is_heading(sentence):
                chunk_text = " ".join(current_chunk)
                final_chunks.append(
                    Document(
                        page_content=chunk_text,
                        metadata={
                            **doc.metadata,
                            "chunk_id": str(uuid.uuid4()),
                            "chunk_length": current_length,
                            "chunk_type": "narrative",
                        },
                    )
                )
                current_chunk = []
                sum_vector = None
                sentence_count = 0
                current_length = 0

            sent_doc = nlp(sentence)
            sent_vector = sent_doc.vector

            # Normalize sentence vector
            norm = np.linalg.norm(sent_vector)
            if norm == 0:
                continue
            sent_vector = sent_vector / norm

            if sum_vector is None:
                sum_vector = sent_vector.copy()
                sentence_count = 1
                current_chunk.append(sentence)
                current_length += len(sentence)
                continue

            # Compute centroid
            centroid = sum_vector / sentence_count
            centroid_norm = np.linalg.norm(centroid)
            if centroid_norm != 0:
                centroid = centroid / centroid_norm

            similarity = np.dot(centroid, sent_vector)

            should_split = (
                similarity < similarity_threshold
                or current_length + len(sentence) > max_chars
            )

            if should_split and current_length >= min_chunk_chars:
                chunk_text = " ".join(current_chunk)

                final_chunks.append(
                    Document(
                        page_content=chunk_text,
                        metadata={
                            **doc.metadata,
                            "chunk_id": str(uuid.uuid4()),
                            "chunk_length": current_length,
                            "chunk_type": "narrative",
                        },
                    )
                )

                # Reset chunk
                current_chunk = [sentence]
                sum_vector = sent_vector.copy()
                sentence_count = 1
                current_length = len(sentence)

            else:
                current_chunk.append(sentence)
                sum_vector += sent_vector
                sentence_count += 1
                current_length += len(sentence)

        # Save remaining chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)

            final_chunks.append(
                Document(
                    page_content=chunk_text,
                    metadata={
                        **doc.metadata,
                        "chunk_id": str(uuid.uuid4()),
                        "chunk_length": current_length,
                        "chunk_type": "narrative",
                    },
                )
            )

    return final_chunks