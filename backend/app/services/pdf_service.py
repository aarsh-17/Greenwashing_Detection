import pdfplumber
import re
import spacy

nlp = spacy.load("en_core_web_sm")
nlp.max_length = 3_000_000

def extract_text(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return re.sub(r"\s+", " ", text)

def split_sentences(text):
    doc = nlp(text)
    return [s.text.strip() for s in doc.sents if len(s.text.split()) >= 6]
