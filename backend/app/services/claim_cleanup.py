import re
import pandas as pd

# ==========================
# NORMALIZATION
# ==========================
def normalize_claim(text: str) -> str:
    if not text:
        return ""

    text = str(text).lower()
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[•●▪►]+", " ", text).strip()
    return text


# ==========================
# FILTERS
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

COUNTRIES = {
    "netherlands", "norway", "canada", "usa", "uk", "china", "australia",
    "india", "brazil", "germany", "france", "spain", "italy", "japan",
    "south africa", "saudi arabia", "united arab emirates", "oman",
    "kuwait", "qatar", "russia", "mexico", "argentina", "colombia",
    "chile", "indonesia", "malaysia", "singapore", "thailand",
    "vietnam", "egypt", "nigeria", "algeria", "angola", "libya",
    "iraq", "iran", "turkey"
}


def looks_like_table_row(text: str) -> bool:
    s = text.strip().lower()
    if len(s) < 50:
        return True

    tokens = s.split()
    num_tokens = sum(1 for t in tokens if re.search(r"\d", t))
    percent_tokens = sum(1 for t in tokens if "%" in t)
    has_country = any(c in s for c in COUNTRIES)

    verbs = [
        "is", "are", "was", "were", "have", "has",
        "will", "aim", "target", "reduce", "increase"
    ]
    has_verb = any(v in tokens for v in verbs)

    if has_country and percent_tokens >= 1 and len(tokens) <= 8 and not has_verb:
        return True

    if num_tokens >= 2 and len(tokens) <= 7 and not has_verb:
        return True

    return False


def looks_like_toc_page_line(text: str) -> bool:
    t = normalize_claim(text)
    nums = re.findall(r"\b\d{2}\b", t)
    return len(nums) >= 3 and len(t.split()) <= 20


def looks_like_toc_or_header(text: str) -> bool:
    if not text:
        return True

    t = text.strip()
    lower = t.lower()
    words = t.split()

    if len(words) <= 5:
        return True

    for pat in REPORT_NOISE_PATTERNS:
        if re.search(pat, lower):
            return True

    keyword_hits = sum(1 for k in TOC_KEYWORDS if k in lower)
    if keyword_hits >= 3:
        return True

    if len(words) >= 8:
        cap_words = sum(1 for w in words if w[:1].isupper())
        if cap_words / len(words) >= 0.65 and not re.search(r"[.!?]$", t):
            return True

    verb_like = re.search(
        r"\b(is|are|was|were|will|reduce|achieve|eliminate|cut|increase|decrease|commit|aim|has|have)\b",
        lower
    )
    past_tense_ed = re.search(r"\b[a-z]{4,}ed\b", lower)

    if len(words) > 10 and not verb_like and not past_tense_ed:
        return True

    return False


# ==========================
# PUBLIC API
# ==========================
def clean_claims(claim_texts: list[str]) -> list[str]:
    df = pd.DataFrame({"claim": claim_texts})
    df["norm"] = df["claim"].apply(normalize_claim)

    df = df[~df["norm"].apply(looks_like_toc_or_header)]
    df = df[~df["norm"].apply(looks_like_table_row)]
    df = df[~df["norm"].apply(looks_like_toc_page_line)]

    df = df.drop_duplicates(subset="norm")
    return df["claim"].tolist()
