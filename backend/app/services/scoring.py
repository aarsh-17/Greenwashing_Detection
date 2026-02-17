import re

# ==========================
# STATIC KEYWORDS & PATTERNS
# ==========================

VAGUE_KEYWORDS = [
    "committed", "commitment", "leading", "leader", "aim", "aiming",
    "strive", "focused", "support", "supporting", "responsible",
    "sustainable", "sustainability", "cleaner", "greener",
    "better world", "working towards", "net zero", "net-zero",
    "ambition", "vision", "purpose", "alignment"
]

OFFSET_KEYWORDS = [
    "offset", "offsets", "carbon credits", "credit",
    "compensate", "compensation",
    "carbon neutral", "carbon-neutral",
    "neutralised", "neutralized", "nature-based"
]

TIMEFRAME_PATTERNS = [
    r"\bby\s20\d{2}\b",
    r"\b20\d{2}\b",
    r"\bwithin\s\d+\syears\b",
    r"\bnext\s\d+\syears\b"
]

NUMBER_PATTERNS = [
    r"\b\d+(\.\d+)?\s?%\b",
    r"\b\d+(\.\d+)?\s?(million|billion|mt|tco2e|tons|tonnes|kg)\b",
    r"\b\d{1,3}(,\d{3})+(\.\d+)?\b",
    r"\b\d+(\.\d+)?\b"
]

# ==========================
# STATIC HELPERS
# ==========================

def has_numbers(sentence: str) -> bool:
    s = sentence.lower()
    return any(re.search(p, s) for p in NUMBER_PATTERNS)


def has_timeframe(sentence: str) -> bool:
    s = sentence.lower()
    return any(re.search(p, s) for p in TIMEFRAME_PATTERNS)


def has_offsets(sentence: str) -> bool:
    s = sentence.lower()
    return any(k in s for k in OFFSET_KEYWORDS)


def has_vague_language(sentence: str) -> bool:
    s = sentence.lower()
    vague_hit = any(k in s for k in VAGUE_KEYWORDS)

    # reduce false positives:
    # measurable OR time-bound claims are less vague
    if (has_numbers(sentence) or has_timeframe(sentence)) and not has_offsets(sentence):
        return False

    return vague_hit


def greenwash_score(sentence: str) -> int:
    """
    Returns a score from 0–100
    Higher = more greenwashing risk
    """
    score = 50  # neutral baseline

    if has_vague_language(sentence):
        score += 20

    if not has_numbers(sentence):
        score += 15
    else:
        score -= 10

    if not has_timeframe(sentence):
        score += 10
    else:
        score -= 5

    if has_offsets(sentence):
        score += 25

    return max(0, min(100, score))


def risk_level(score: int) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


