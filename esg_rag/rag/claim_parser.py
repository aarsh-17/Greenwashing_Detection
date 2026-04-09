import re
from typing import Dict, List

def parse_claim(text: str) -> Dict:
    text_l = text.lower()

    years = [int(y) for y in re.findall(r"(20\d{2})", text)]

    numbers = re.findall(
        r"\d+(?:[\.,]\d+)?\s?(?:%|mt|gt|tonnes|mb/d|bcm|million|billion)?",
        text,
        flags=re.IGNORECASE
    )

    # Metric detection (cheap but effective)
    if "carbon intensity" in text_l or "intensity" in text_l:
        metric = "Intensity"
    elif "emissions" in text_l or "co2" in text_l:
        metric = "Emissions"
    elif "production" in text_l:
        metric = "Production"
    else:
        metric = "Unspecified"

    # Sector inference
    if any(k in text_l for k in ["oil", "petroleum", "refining"]):
        sector = "Oil"
    elif any(k in text_l for k in ["gas", "lng"]):
        sector = "Gas"
    elif any(k in text_l for k in ["power", "electricity"]):
        sector = "Power"
    else:
        sector = "Cross-sector"

    return {
        "text": text,
        "years": years,
        "numbers": numbers,
        "metric": metric,
        "sector": sector
    }
