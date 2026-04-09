import re

DIRECTION_WORDS = [
    "increase", "decrease", "decline", "rise",
    "grow", "peak", "plateau", "fall", "triple", "double", "halve", "drop", "surge", "plummet",
   
]

UNITS = [
    "GW", "TWh", "Gt", "mb/d", "bcm", "%",
    "million", "billion", "trillion", "tonnes", "tons", "metric tons", "barrels", "cubic meters"
]

YEAR_REGEX = r"(20\d{2})"

def signal_score(text):
    score = 0
    if re.search(r"\d", text): score += 2
    if any(u in text for u in UNITS): score += 2
    if re.search(YEAR_REGEX, text): score += 2
    if any(w in text.lower() for w in DIRECTION_WORDS): score += 1
    return score

def filter_benchmarks(paragraphs, threshold=5):
    return [p for p in paragraphs if signal_score(p["text"]) >= threshold]
