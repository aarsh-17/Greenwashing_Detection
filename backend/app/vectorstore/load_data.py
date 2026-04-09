from langchain_community.document_loaders import PyMuPDFLoader
from pathlib import Path
import re


def clean_page_text(text: str) -> str:
    text = re.sub(r"Shell Sustainability Report \d{4}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"Figure\s+\d+.*?(?:\n|$)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n\s*\n", "\n", text)
    text = re.sub(r"\s{2,}", " ", text)

    text = re.sub(r"More in this report.*?(?=\n[A-Z])", "", text, flags=re.DOTALL)
    text = re.sub(r"More on Shell websites.*?(?=\n[A-Z])", "", text, flags=re.DOTALL)

    text = re.sub(
        r"Sustainability at\s+Shell\s+Our values.*?Our performance\s+data",
        "",
        text,
        flags=re.DOTALL
    )

    text = re.sub(r"[]+", "", text)
    return text.strip()


def is_navigation_or_toc(text: str) -> bool:
    lines = text.split("\n")

    numeric_lines = sum(1 for l in lines if re.search(r"\d+", l))
    if len(lines) > 0 and numeric_lines / len(lines) > 0.6:
        return True

    if len(text) < 150:
        return True

    return False


def load_documents(pdf_path: str):

    loader = PyMuPDFLoader(pdf_path)
    documents = loader.load()

    cleaned_docs = []

    for doc in documents:
        page = doc.metadata.get("page", 0)

        # skip first pages (TOC)
        if page <= 2:
            continue

        cleaned_text = clean_page_text(doc.page_content)

        if is_navigation_or_toc(cleaned_text):
            continue

        if len(cleaned_text) < 200:
            continue

        doc.page_content = cleaned_text
        doc.metadata["source"] = Path(pdf_path).stem

        cleaned_docs.append(doc)

    return cleaned_docs