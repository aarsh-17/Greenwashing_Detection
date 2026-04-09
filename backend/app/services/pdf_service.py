# import pdfplumber
# import re
# import spacy

# nlp = spacy.load("en_core_web_sm")
# nlp.max_length = 3_000_000

# def extract_text(pdf_path):
#     text = ""
#     with pdfplumber.open(pdf_path) as pdf:
#         for page in pdf.pages:
#             text += page.extract_text() or ""
#     return re.sub(r"\s+", " ", text)

# def split_sentences(text):
#     doc = nlp(text)
#     return [s.text.strip() for s in doc.sents if len(s.text.split()) >= 6]

import fitz  # PyMuPDF
import re
import spacy

nlp = spacy.load("en_core_web_sm")
nlp.max_length = 3_000_000

def extract_text(pdf_path):
    text = []
    doc = fitz.open(pdf_path)

    for page in doc:
        blocks = page.get_text("blocks")  # structured blocks
        blocks = sorted(blocks, key=lambda b: (b[1], b[0]))  # top-to-bottom

        for block in blocks:
            block_text = block[4].strip()
            if block_text:
                text.append(block_text)

    full_text = " ".join(text)
    return re.sub(r"\s+", " ", full_text)


def split_sentences(text):
    doc = nlp(text)
    return [s.text.strip() for s in doc.sents if len(s.text.split()) >= 6]