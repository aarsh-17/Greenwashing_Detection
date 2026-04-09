
from typing import List

import spacy


nlp = spacy.load("en_core_web_sm")
import fitz

import re

def extract_numbers_and_years(text: str):
    number_pattern = r"\d+(?:[\.,]\d+)?\s?(?:%|mb/d|bcm|Gt|TWh|GW|million|billion|trillion)"

    year_pattern = r"\b(19\d{2}|20\d{2}|21\d{2})\b"

    numbers = re.findall(number_pattern, text)
    years = [int(y) for y in re.findall(year_pattern, text)]

    return numbers, years

CONSTRAINT_VERBS = [
    "increase", "increases", "rise", "rises", "expand", "expands",
    "decline", "declines", "fall", "falls", "drop", "drops",
    "peak", "plateau", "remain", "remains"
]

def constraint_count(text: str) -> int:
    t = text.lower()
    return sum(1 for v in CONSTRAINT_VERBS if v in t)

def extract_paragraphs(pdf_path):
    doc = fitz.open(pdf_path)
    paragraphs = []

    for page_num, page in enumerate(doc):
        raw_text = page.get_text()

        cleaned_page = clean_page_text(raw_text)

       
        for para in sentence_windows(cleaned_page, window=2):
            para = clean_paragraph(para)

            if is_figure_artifact(para):
                continue

            if len(para) < 120:
                continue
            if legend_density_score(para) >= 4:
                continue
            numbers, years = extract_numbers_and_years(para)

            if not has_future_year(years):
                continue

            if not has_real_number(numbers):
                continue

            if constraint_count(para)>1 :
                continue


            paragraphs.append({
                "text": para,
                "pdf_page_index": page_num,
                "page": page_num + 1
            })

    return paragraphs



def clean_page_text(text: str) -> str:
    # Remove leading page numbers like "122"
    text = re.sub(r"^\s*\d+\s*", "", text)

    # Remove chapter headers
    text = re.sub(r"Chapter\s+\d+\s*\|.*?\n", "", text, flags=re.IGNORECASE)

    # Remove entire figure caption / legend blocks
    text = re.sub(r"Figure\s+.*?(?:\n|$)", "", text, flags=re.IGNORECASE)

    # Remove copyright / license lines
    text = re.sub(r"IEA.*?CC BY.*?(?:\n|$)", "", text)

    # Remove axis-only numeric lines
    text = re.sub(r"\n(?:\s*\d+\s*)+\n", "\n", text)

    return text

def clean_paragraph(text: str) -> str:
    # Remove page headers / footers
    text = re.sub(r"International Energy Agency.*?\n", "", text)

    # Remove section numbering (e.g., 4.2, 4.2.1)
    text = re.sub(r"\n?\d+(\.\d+)+\s*", " ", text)

    # Remove figure labels
    text = re.sub(r"Figure\s+\d+(\.\d+)?", "", text, flags=re.IGNORECASE)

    # Remove axis-only numeric lines
    text = re.sub(r"\n(\s*\d+\s*)+\n", "\n", text)

    # Remove copyright lines
    text = re.sub(r"IEA.*?CC BY.*?\n", "", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text



def sentence_windows(text, window=1):
    doc = nlp(text)
    sents = [s.text.strip() for s in doc.sents if len(s.text.strip()) > 30]
    return [
        " ".join(sents[i:i+window])
        for i in range(0, len(sents), window)
    ]

def is_figure_artifact(text: str) -> bool:
    t = text.lower()

    if t.startswith("figure"):
        return True

    if "chapter" in t and "|" in t:
        return True

    if "note:" in t or "notes:" in t:
        return True

    # Legend-style uppercase spam
    tokens = text.split()
    caps = sum(1 for tok in tokens if tok.isupper() and len(tok) <= 5)
    if caps > 5:
        return True

    return False

def legend_density_score(text: str) -> int:
    geo_terms = [
        "north america", "european union", "china", "india",
        "africa", "middle east", "japan", "korea",
        "southeast asia", "rest of world"
    ]
    t = text.lower()
    return sum(1 for g in geo_terms if g in t)



def has_future_year(years):
    return any(y >= 2025 for y in years)


def has_real_number(numbers):
    return any(
        "%" in n or "mb/d" in n or "bcm" in n or "Gt" in n or "million" in n or "billion" in n or "trillion" in n or "tonnes" in n or "tons" in n or "metric tons" in n or "barrels" in n or "cubic meters" in n 
        for n in numbers
    )
