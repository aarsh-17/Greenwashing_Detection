import re
import spacy
from typing import List, Dict

nlp = spacy.load("en_core_web_sm")

# ----------------------------
# Dictionaries / vocab
# ----------------------------

SCENARIO_KEYWORDS = {
    "CPS": ["current policies", "cps"],
    "STEPS": ["stated policies", "steps"],
    "NZE": ["net zero", "nze"]
}

SECTOR_KEYWORDS = {
    "Oil": ["oil", "petroleum", "crude", "refining"],
    "Gas": ["gas", "lng", "natural gas"],
    "Coal": ["coal"],
    "Power": ["electricity", "power", "grid", "generation"],
    "Transport": ["transport", "vehicle", "aviation", "shipping", "road"],
    "Buildings": ["buildings", "heating", "cooling"],
    "Industry": ["industry", "industrial", "cement", "steel"],
}

CONSTRAINT_KEYWORDS = {
    "Peak": ["peak", "peaks"],
    "Plateau": ["plateau", "levels off", "flattens"],
    "Decline": ["decline", "fall", "drop", "decrease"],
    "Growth": ["increase", "rise", "grow", "expand", "triple", "double"],
}

METRIC_KEYWORDS = {
    "Oil demand": ["oil demand"],
    "Gas demand": ["gas demand"],
    "Coal demand": ["coal demand"],
    "Electricity demand": ["electricity demand"],
    "Emissions": ["co2", "emissions"],
    "Capacity": ["capacity", "generation", "installed"],
}

# ----------------------------
# Helper functions
# ----------------------------

def detect_scenario(text: str) -> str:
    t = text.lower()
    for scenario, keys in SCENARIO_KEYWORDS.items():
        if any(k in t for k in keys):
            return scenario
    return "Unspecified"


def extract_years(text: str) -> List[int]:
    return sorted({int(y) for y in re.findall(r"(20\d{2})", text)})


def infer_time_bucket(years: List[int]) -> str:
    if not years:
        return "Undated"
    y = max(years)
    if y <= 2024:
        return "Observed"
    if y <= 2030:
        return "Short-term"
    if y <= 2035:
        return "Mid-term"
    return "Long-term"


def detect_sectors(text: str) -> List[str]:
    t = text.lower()
    sectors = [s for s, keys in SECTOR_KEYWORDS.items() if any(k in t for k in keys)]
    return sectors if sectors else ["Cross-sector"]


def detect_constraint(text: str) -> str:
    t = text.lower()
    for c, keys in CONSTRAINT_KEYWORDS.items():
        if any(k in t for k in keys):
            return c
    return "Trend"


def detect_metric(text: str) -> str:
    t = text.lower()
    for metric, keys in METRIC_KEYWORDS.items():
        if any(k in t for k in keys):
            return metric
    return "Unspecified"


def extract_numbers_and_units(text: str) -> List[str]:
    # captures things like "105 mb/d", "35 Gt", "40%", "1 000 TWh"
    pattern = r"\d+(?:[\.,]\d+)?\s?(?:%|mb/d|bcm|Gt|TWh|GW|million|billion)?"
    return re.findall(pattern, text)


# ----------------------------
# Main tagger
# ----------------------------

def tag(paragraph: Dict) -> Dict:
    text = paragraph["text"]

    years = extract_years(text)
    sectors = detect_sectors(text)

    return {
        **paragraph,

        # Traceability
        "pdf_page": paragraph.get("page"),

        # Core metadata
        "scenario": detect_scenario(text),
        "sectors": sectors,
        "primary_sector": sectors[0],

        # Time
        "years": years,
        "time_bucket": infer_time_bucket(years),

        # Constraint semantics
        "constraint_type": detect_constraint(text),
        "metric": detect_metric(text),

        # Raw quantitative signals (do not interpret yet)
        "numbers": extract_numbers_and_units(text),
    }
