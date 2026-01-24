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

PDF_PATH = PROJECT_ROOT / "Oil & Gas" / "Shell.pdf"
OUTPUT_PATH = PROJECT_ROOT / "nlp" / "shell_claims.xlsx"

CLAIM_THRESHOLD = 0.8


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

def extract_text_from_pdf(pdf_path: Path) -> str:
    text_chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
    return " ".join(text_chunks)


# ==========================================================
# TEXT CLEANING (ESG-SAFE)
# ==========================================================

def repair_word_boundaries(text: str) -> str:
    # Insert space between lowercase-uppercase: "netZero" → "net Zero"
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

    # Insert space between letters and numbers: "In2023" → "In 2023"
    text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
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
                "source_pdf": str(pdf_path)
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
        threshold=0.85
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    claims_df.to_excel(OUTPUT_PATH, index=False)

    print(f"Claims extracted: {len(claims_df)}")
    print(f"Saved Excel file to: {OUTPUT_PATH}")
