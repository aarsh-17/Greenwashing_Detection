from pathlib import Path
import re
import torch
import pandas as pd
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import pdfplumber
import spacy


# ==========================================================
# CONFIGURATION
# ==========================================================

MODEL_PATH = Path("D:/ESG_platform/bert_claim_classifier")
PROJECT_ROOT = Path("D:/ESG_platform")

PDF_PATH = PROJECT_ROOT / "Oil & Gas" / "Marathon.pdf"
OUTPUT_PATH = PROJECT_ROOT / "nlp" / "marathon_claims.xlsx"



# ==========================================================
# LOAD spaCy
# ==========================================================

nlp = spacy.load("en_core_web_sm")
nlp.max_length = 3_000_000  # ESG PDFs can be long


# ==========================================================
# LOAD BERT MODEL
# ==========================================================

assert MODEL_PATH.exists(), "Model path does not exist"

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()


# ==========================================================
# PDF EXTRACTION (pdfplumber)
# ==========================================================
def is_document_structure_noise(text: str) -> bool:
    t = re.sub(r"\s+", " ", str(text)).strip()

    # Too short
    if len(t) < 5:
        return True

    # Too many title-case / capitalized words (TOC style)
    words = t.split()
    if len(words) >= 8:
        cap_words = sum(1 for w in words if w[:1].isupper())
        if cap_words / len(words) >= 0.6:
            return True

    # Contains common ESG TOC/header tokens
    bad_tokens = [
        "sustainability", "our performance", "our values", "respecting nature",
        "powering lives", "energy transition", "our journey", "data", "overview",
         "report", "table of contents", "management", "framework", "indicators", "index", "about this report","See more","Learn more","See all"
    ]
    lower = t.lower()
    if sum(1 for b in bad_tokens if b in lower) >= 2:
        return True

    # Looks like a list of sections (no verbs)
    verb_like = re.search(r"\b(is|are|was|were|will|reduce|achieve|eliminate|cut|increase|decrease|commit|aim|has|have|do|does)\b", lower)
    if verb_like is None and len(words) > 5:
        return True

    return False


def is_table_header_line(line: str) -> bool:
    # Detect timeline table headers like: 2023 2022 2021 2020 2019
    years = re.findall(r"\b20\d{2}\b", line)
    return len(years) >= 4

def extract_text_from_pdf(pdf_path: Path) -> str:
    cleaned_chunks = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:

            page_text = page.extract_text() or ""

            cleaned_page_lines = []
            skip_table_mode = False
            table_blank_run = 0

            for line in page_text.split("\n"):
                norm_line = normalize_whitespace(line)



                # ✅ If table header found -> start skipping
                if is_table_header_line(norm_line):
                    skip_table_mode = True
                    table_blank_run = 0
                    continue

                # ✅ stop skipping after a few "non-table looking" lines
                if skip_table_mode:
                    # count blank / separators
                    if len(norm_line) == 0:
                        table_blank_run += 1
                        if table_blank_run >= 2:
                            skip_table_mode = False
                        continue

                    # keep skipping numeric-heavy rows
                    num_count = len(re.findall(r"\d+", norm_line))
                    if num_count >= 3:
                        continue

                    # if it's a short label + units style line, also skip
                    if len(norm_line.split()) <= 6:
                        continue

                    # once we hit real paragraph text -> exit skip mode
                    skip_table_mode = False

                # ✅ normal filters (keep these)
                num_count = len(re.findall(r"\d+", norm_line))
                if num_count >= 4 and len(norm_line.split()) <= 15:
                    continue

                if norm_line.count("%") >= 4:
                    continue

                cleaned_page_lines.append(line)

            cleaned_chunks.append(" ".join(cleaned_page_lines))

    return " ".join(cleaned_chunks)



# ==========================================================
# TEXT CLEANING (ESG-SAFE)
# ==========================================================

def repair_word_boundaries(text: str) -> str:
    # Insert space between lowercase-uppercase: "netZero" → "net Zero"
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

    # Insert space between letters and numbers: "In2023" → "In 2023"
    text = re.sub(r'(?<!CO)(?<!tCO)([a-zA-Z])(\d)', r'\1 \2', text)
    text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)

    # Restore common ESG units
    text = re.sub(r'\bCO2e\b', 'CO2e', text)
    text = re.sub(r'\bGHG\b', 'GHG', text)
    text = re.sub(r'\bScope\s?(\d)\b', r'Scope \1', text)

    # Fix percentage spacing
    text = re.sub(r'(\d)\s*%', r'\1%', text)

    # Normalize whitespace AFTER repairs
    text = re.sub(r'\s+', ' ', text)

    return text.strip()



def normalize_whitespace(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def clean_text_for_inference(text: str) -> str:
    text = repair_word_boundaries(text)
    text = normalize_whitespace(text)
    text = re.sub(r"[^\w\s\.\,\%\-\(\)]", " ", text)
    return normalize_whitespace(text)


# ==========================================================
# SENTENCE SPLITTING (spaCy)
# ==========================================================

def split_sentences(text: str, min_words: int = 6):
    doc = nlp(text)
    return [
        sent.text.strip()
        for sent in doc.sents
        if len(sent.text.split()) >= min_words
    ]


# ==========================================================
# CLAIM PREDICTION (BERT)
# ==========================================================

def predict_claim(sentence: str, threshold: float):
    inputs = tokenizer(
        sentence,
        truncation=True,
        padding="max_length",
        max_length=128,
        return_tensors="pt"
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)

    claim_prob = probs[0][1].item()
    return claim_prob >= threshold, claim_prob


# ==========================================================
# CLAIM EXTRACTION PIPELINE
# ==========================================================

def extract_claims_from_pdf(pdf_path: Path, company_name: str, threshold: float):
    raw_text = extract_text_from_pdf(pdf_path)
    clean_text = clean_text_for_inference(raw_text)
    sentences = split_sentences(clean_text)

    records = []

    for sent in sentences:
        is_claim, confidence = predict_claim(sent, threshold)
        if is_claim:
            records.append({
                "company": company_name,
                "claim_text": sent,
                "confidence": round(confidence, 3),

            })

    return pd.DataFrame(records)


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    print("Extracting ESG claims using pdfplumber + spaCy + BERT...")

    claims_df = extract_claims_from_pdf(
        pdf_path=PDF_PATH,
        company_name="Shell",
        threshold=0.75
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    claims_df.to_excel(OUTPUT_PATH, index=False)
    claims_df.to_csv(OUTPUT_PATH.with_suffix(".csv"), index=False)

    print(f"Claims extracted: {len(claims_df)}")
    print(f"Saved Excel file to: {OUTPUT_PATH}")

