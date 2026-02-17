import pandas as pd
import re
from pathlib import Path

PROJECT_ROOT = Path("D:/ESG_platform")

INPUT_FILE = PROJECT_ROOT / "nlp" / "marathon_claims.xlsx"
OUTPUT_FILE = PROJECT_ROOT / "nlp" / "marathon_claims_esg_deduped.xlsx"


# ==========================
# 1) NORMALIZATION
# ==========================
def normalize_claim(text):
    if pd.isna(text):
        return ""

    text = str(text).lower()
    text = re.sub(r"\s+", " ", text).strip()

    # remove weird bullets
    text = re.sub(r"[•●▪►]+", " ", text).strip()

    return text


# ==========================
# 2) HEADER / TOC FILTER
# ==========================
TOC_KEYWORDS = [
    "sustainability", "our performance", "our values", "respecting nature",
    "powering lives", "energy transition", "our journey",
    "data", "contents", "table of contents"
]

REPORT_NOISE_PATTERNS = [
    r"\b sustainability report\b",
    r"\bpage\b\s*\d+\b",
    r"^\d+\s+ sustainability report",
]



COUNTRIES = {"netherlands", "norway", "canada", "usa", "uk", "china", "australia","india", "brazil", "germany", "france", "spain", "italy", "japan","south africa","Saudi arabia","united arab emirates","oman","kuwait","qatar","russia","mexico","argentina","colombia","chile", "indonesia", "malaysia", "singapore", "thailand", "vietnam","egypt", "nigeria", "algeria", "angola", "libya", "iraq", "iran", "turkey"}

def looks_like_table_row(text: str) -> bool:
    s = text.strip().lower()
    if len(s) < 50:
        return True

    tokens = s.split()
    num_tokens = sum(1 for t in tokens if re.search(r"\d", t))
    percent_tokens = sum(1 for t in tokens if "%" in t)

    # If it contains a country + percentage + few words → likely table row
    has_country = any(c in s for c in COUNTRIES)

    # Very table-ish: many numbers but no verb
    verbs = ["is", "are", "was", "were", "have", "has", "will", "aim", "target", "reduce", "increase"]
    has_verb = any(v in tokens for v in verbs)

    if has_country and percent_tokens >= 1 and len(tokens) <= 8 and not has_verb:
        return True

    if num_tokens >= 2 and len(tokens) <= 7 and not has_verb:
        return True

    return False


def looks_like_toc_page_line(text: str) -> bool:
    t = normalize_claim(text)

    # patterns like: "02 Letter from the CEO 04 Powering Progress 05"
    # many 2-digit numbers + words
    nums = re.findall(r"\b\d{2}\b", t)
    if len(nums) >= 3 and len(t.split()) <= 20:
        return True

    return False


def looks_like_toc_or_header(text: str) -> bool:
    """
    Detects extracted junk like headings/TOC:
    'Sustainability in Our performance Shell Our values...'
    """
    if not text or pd.isna(text):
        return True
    t = str(text).strip()
    lower = t.lower()
    words = t.split()

    # ✅ remove extremely short junk (2 words or less)
    if len(words) <= 5:
        return True

    # ✅ report boilerplate pattern removal
    for pat in REPORT_NOISE_PATTERNS:
        if re.search(pat, lower):
            return True

    # ✅ too many TOC keywords in one line
    keyword_hits = sum(1 for k in TOC_KEYWORDS if k in lower)
    if keyword_hits >= 3:
        return True

    # ✅ looks like headings mashed together (many Capitalized words, no punctuation)
    if len(words) >= 8:
        cap_words = sum(1 for w in words if w[:1].isupper())
        if cap_words / len(words) >= 0.65 and not re.search(r"[.!?]$", t):
            return True

    # ✅ no real verb signal AND long => probably not a sentence
    verb_like = re.search(
        r"\b(is|are|was|were|will|reduce|achieve|eliminate|cut|increase|decrease|commit|aim|has|have|do|does)\b",
        lower
    )

    past_tense_ed = re.search(r"\b[a-z]{4,}ed\b", lower)  # length>=4 avoids "bed", "red" etc

    # ✅ If long, and no verb signal (including -ed past tense), drop it
    if len(words) > 10 and verb_like is None and past_tense_ed is None:
        return True

    return False


# ==========================
# 3) MAIN
# ==========================
df = pd.read_excel(INPUT_FILE)

# normalize
df["norm_claim"] = df["claim_text"].apply(normalize_claim)

# remove TOC/header junk
df = df[~df["norm_claim"].apply(looks_like_toc_or_header)].copy()

df = df[~df["norm_claim"].apply(looks_like_table_row)].copy()

df = df[~df["norm_claim"].apply(looks_like_toc_page_line)].copy()

# drop duplicates
df = df.drop_duplicates(subset="norm_claim")

# cleanup
df = df.drop(columns=["norm_claim"]).reset_index(drop=True)

# save
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
df.to_excel(OUTPUT_FILE, index=False)

print(f"✅ Clean + Deduplicated claims saved to: {OUTPUT_FILE}")
print(f"Before: {len(pd.read_excel(INPUT_FILE))}")
print(f"After:  {len(df)}")
