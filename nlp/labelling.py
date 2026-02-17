import pandas as pd
import re
from pathlib import Path

# ==========================
# 1) FILE PATHS
# ==========================
BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "shell_claims_esg_deduped.xlsx"
OUTPUT_FILE = BASE_DIR / "shell_claims_scored.xlsx"

# ==========================
# 2) TEXT HELPERS
# ==========================
def clean_text(text: str) -> str:
    if pd.isna(text):
        return ""

    text = str(text)

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Remove weird repeated punctuation
    text = re.sub(r"[•●▪►]+", " ", text).strip()

    return text


def split_into_sentences(text: str):
    """
    Split large claim chunks into smaller atomic claims.
    Works decently even without spacy/nltk.
    """
    if not text:
        return []

    # Split by sentence endings
    parts = re.split(r"(?<=[.!?])\s+", text)

    # Also split by semicolons if it looks like long compound claim
    final = []
    for p in parts:
        p = p.strip()
        if len(p) > 220:  # long chunk → further split
            subparts = re.split(r";\s+", p)
            final.extend([s.strip() for s in subparts if len(s.strip()) > 10])
        else:
            if len(p) > 10:
                final.append(p)

    return final


# ==========================
# 3) DETECTION FUNCTIONS
# ==========================
VAGUE_KEYWORDS = [
    "committed", "commitment", "leading", "leader", "aim", "aiming",
    "strive", "focused", "support", "supporting", "responsible",
    "sustainable", "sustainability", "cleaner", "greener", "future",
    "better world", "working towards", "net zero", "net-zero",
    "ambition", "vision", "purpose", "alignment", "aspire", "aspiration",
    "endeavor", "endeavour", "dedicated", "drive", "promote", "promoting",
    "enhance", "enhancing", "improve", "improving"
]

OFFSET_KEYWORDS = [
    "offset", "offsets", "carbon credits", "credit", "compensate",
    "compensation", "neutralised", "neutralized", "carbon neutral",
    "carbon-neutral", "nature-based", "reforestation", "afforestation",
    "soil carbon", "blue carbon", "carbon storage", "sequestration"
]

TIMEFRAME_PATTERNS = [
    r"\bby\s(20\d{2})\b",
    r"\b(20\d{2})\b",
    r"\bwithin\s\d+\syears\b",
    r"\bnext\s\d+\syears\b",
    r"\b(short|medium|long)\s?term\b"
]

NUMBER_PATTERNS = [
    r"\b\d+(\.\d+)?\s?%\b",
    r"\b\d+(\.\d+)?\s?(million|billion|thousand|mt|tco2e|kg|tons|tonnes|gwh|mwh)\b",
    r"\b\d{1,3}(,\d{3})+(\.\d+)?\b",  # 1,000 or 1,000.5
    r"\b\d+(\.\d+)?\b"  # general numbers
]


def has_vague_language(sentence: str) -> int:
    s = sentence.lower()

    vague_hit = any(k in s for k in VAGUE_KEYWORDS)

    # ✅ Anti-false-positive rule:
    # If it's measurable (numbers) OR time-bound → don't call it vague
    if has_numbers(sentence) or has_timeframe(sentence):
        return 0

    return int(vague_hit)



def has_offsets(sentence: str) -> int:
    s = sentence.lower()
    return int(any(k in s for k in OFFSET_KEYWORDS))


def has_timeframe(sentence: str) -> int:
    s = sentence.lower()
    for pat in TIMEFRAME_PATTERNS:
        if re.search(pat, s):
            return 1
    return 0


def has_numbers(sentence: str) -> int:
    s = sentence.lower()
    for pat in NUMBER_PATTERNS:
        if re.search(pat, s):
            return 1
    return 0


def classify_claim_type(sentence: str) -> str:
    """
    Rule-based claim categorizer (baseline).
    Later you can replace this with a ML classifier.
    """
    s = sentence.lower()

    if any(x in s for x in ["net zero", "net-zero", "2050", "2030", "target", "goal", "aim", "commitment", "commit", "promise", "pledge", "intend", "plan", "strive", "aspire",]):
        return "Target/Future Promise"

    if any(x in s for x in ["reduced", "decreased", "cut", "lowered", "improved", "increase", "achieved","has","have","completed","reduction","reaching","reached"]):
        return "Past Achievement"

    if any(x in s for x in ["offset", "credits", "compensate", "carbon neutral", "neutralized", "neutralised"]):
        return "Offset/Compensation"

    if any(x in s for x in ["invest", "investment", "capex", "funding", "spent", "$", "usd", "million", "billion"]):
        return "Investment Claim"

    if any(x in s for x in ["report", "disclose", "gri", "tcfd", "sasb", "assurance", "audited"]):
        return "Reporting/Compliance"

    if any(x in s for x in ["renewable", "hydrogen", "biofuel", "saf", "solar", "wind", "ev", "electric"]):
        return "Energy Transition/Product"

    if any(x in s for x in ["emissions", "scope 1", "scope 2", "scope 3", "methane", "flaring"]):
        return "Emissions/Operational"

    return "General ESG PR"


def greenwash_risk_score(sentence: str) -> int:
    """
    Score from 0-100
    Higher = more suspicious greenwashing risk
    """
    vague = has_vague_language(sentence)
    nums = has_numbers(sentence)
    timef = has_timeframe(sentence)
    offset = has_offsets(sentence)

    score = 50  # base

    # vague language increases risk
    if vague:
        score += 20

    # having no numbers increases risk
    if nums == 0:
        score += 15
    else:
        score -= 10

    # no timeframe increases risk
    if timef == 0:
        score += 10
    else:
        score -= 5

    # offsets increase risk a lot
    if offset:
        score += 25

    # clamp score to 0..100
    score = max(0, min(100, score))
    return score

def vagueness_score(sentence: str) -> int:
    s = sentence.lower()

    vague_hits = sum(1 for k in VAGUE_KEYWORDS if k in s)

    score = vague_hits * 10  # each vague keyword adds 10 points

    if has_numbers(sentence):
        score -= 15  # measurable reduces vagueness
    if has_timeframe(sentence):
        score -= 10  # time-bound reduces vagueness

    return max(0, score)


def risk_reason(sentence: str) -> str:
    reasons = []
    if has_vague_language(sentence):
        reasons.append("Vague language")
    if not has_numbers(sentence):
        reasons.append("No measurable metric")
    if not has_timeframe(sentence):
        reasons.append("No timeframe")
    if has_offsets(sentence):
        reasons.append("Offset-based claim")
    return ", ".join(reasons) if reasons else "Clear/measurable"


# ==========================
# 4) MAIN PIPELINE
# ==========================
def main():
    print("✅ Loading Excel:", INPUT_FILE)
    df = pd.read_excel(INPUT_FILE)

    # Expecting columns: company, claim_text, confidence, source_pdf
    if "claim_text" not in df.columns:
        raise ValueError("❌ Column 'claim_text' not found in Excel file.")

    df["claim_text"] = df["claim_text"].apply(clean_text)

    # Explode into sentence-level claims
    all_rows = []
    for idx, row in df.iterrows():
        company = row.get("company", "")
        chunk = row.get("claim_text", "")
        conf = row.get("confidence", None)
        src = row.get("source_pdf", "")

        sentences = split_into_sentences(chunk)

        for sent in sentences:
            all_rows.append({
                "company": company,
                "source_pdf": src,
                "confidence": conf,
                "claim_sentence": sent,
            })

    out = pd.DataFrame(all_rows)

    print(f"✅ Extracted atomic claims: {len(out)}")

    # Add features
    out["claim_type"] = out["claim_sentence"].apply(classify_claim_type)
    out["has_numbers"] = out["claim_sentence"].apply(has_numbers)
    out["has_timeframe"] = out["claim_sentence"].apply(has_timeframe)
    out["offset_flag"] = out["claim_sentence"].apply(has_offsets)
    out["vagueness_score"] = out["claim_sentence"].apply(vagueness_score)
    out["vague_flag"] = (out["vagueness_score"] >= 20).astype(int)


    out["greenwash_risk_score"] = out["claim_sentence"].apply(greenwash_risk_score)
    out["risk_reason"] = out["claim_sentence"].apply(risk_reason)

    # Sort by most suspicious first
    out = out.sort_values(by="greenwash_risk_score", ascending=False)

    # Save
    out.to_excel(OUTPUT_FILE, index=False)
    print("✅ Scored file saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
