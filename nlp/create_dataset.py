import pandas as pd
import re
from pathlib import Path

# ==========================
# FILE PATHS
# ==========================
BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "shell_claims_esg_deduped.xlsx"
OUTPUT_FILE = BASE_DIR / "synthetic_greenwash_train.xlsx"

# ==========================
# TEXT HELPERS
# ==========================
def clean_text(text: str) -> str:
    if pd.isna(text):
        return ""
    text = str(text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[•●▪►]+", " ", text).strip()
    return text


def split_into_sentences(text: str):
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    final = []
    for p in parts:
        p = p.strip()
        if len(p) > 220:
            subparts = re.split(r";\s+", p)
            final.extend([s.strip() for s in subparts if len(s.strip()) > 10])
        else:
            if len(p) > 10:
                final.append(p)
    return final

# ==========================
# SIMPLE FEATURES (ONLY FOR SYNTHETIC LABELING)
# ==========================
OFFSET_KEYWORDS = [
    "offset", "offsets", "carbon credits", "credit", "compensate",
    "compensation", "neutralised", "neutralized", "carbon neutral",
    "carbon-neutral", "nature-based"
]

VAGUE_KEYWORDS = [
    "committed", "commitment", "leading", "leader", "aim", "aiming",
    "strive", "focused", "support", "supporting", "responsible",
    "sustainable", "sustainability", "cleaner", "greener", "future",
    "better world", "working towards", "ambition", "vision", "purpose",
    "alignment", "aspire", "aspiration"
]

TIMEFRAME_PATTERNS = [
    r"\bby\s(20\d{2})\b",
    r"\b(20\d{2})\b",
    r"\bwithin\s\d+\syears\b",
    r"\bnext\s\d+\syears\b"
]

NUMBER_PATTERNS = [
    r"\b\d+(\.\d+)?\s?%\b",
    r"\b\d+(\.\d+)?\b"
]


def has_offsets(s: str) -> int:
    s = s.lower()
    return int(any(k in s for k in OFFSET_KEYWORDS))


def has_vague(s: str) -> int:
    s = s.lower()
    return int(any(k in s for k in VAGUE_KEYWORDS))


def has_timeframe(s: str) -> int:
    s = s.lower()
    return int(any(re.search(p, s) for p in TIMEFRAME_PATTERNS))


def has_numbers(s: str) -> int:
    s = s.lower()
    return int(any(re.search(p, s) for p in NUMBER_PATTERNS))


def synthetic_label(sentence: str) -> str:
    """
    3 Labels:
    Low    = measurable & time-bound (less greenwashing)
    Medium = mixed / partially vague
    High   = vague + no structure OR offset-based claims
    """
    s = sentence.strip()

    offset = has_offsets(s)
    vague = has_vague(s)
    nums = has_numbers(s)
    timef = has_timeframe(s)

    # HIGH
    if offset == 1:
        return "High"
    if vague == 1 and nums == 0 and timef == 0:
        return "High"

    # LOW
    if nums == 1 and timef == 1 and offset == 0:
        return "Low"

    # MEDIUM (default)
    return "Medium"


def main():
    print("✅ Loading:", INPUT_FILE)
    df = pd.read_excel(INPUT_FILE)

    if "claim_text" not in df.columns:
        raise ValueError("❌ Column 'claim_text' not found")

    df["claim_text"] = df["claim_text"].apply(clean_text)

    rows = []
    for _, row in df.iterrows():
        company = row.get("company", "")
        src = row.get("source_pdf", "")
        conf = row.get("confidence", None)

        for sent in split_into_sentences(row["claim_text"]):
            label = synthetic_label(sent)

            rows.append({
                "company": company,
                "source_pdf": src,
                "confidence": conf,
                "claim_sentence": sent,
                "label": label
            })

    out = pd.DataFrame(rows)

    # Optional: balance dataset a bit (not required)
    print("\n✅ Synthetic label distribution:")
    print(out["label"].value_counts())

    out.to_excel(OUTPUT_FILE, index=False)
    print("\n✅ Saved synthetic dataset:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
