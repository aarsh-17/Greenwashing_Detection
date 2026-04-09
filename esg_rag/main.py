from ingest.parse_pdf import extract_paragraphs
from ingest.extract_signals import filter_benchmarks
from ingest.tag_metadata import tag
from ingest.build_index import build_index

from rag.claim_parser import parse_claim
from rag.retrieve import retrieve
from rag.prompt import build_prompt
from rag.evaluate import evaluate

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

INDEX_PATH = DATA_DIR / "faiss.index"
META_PATH = DATA_DIR / "metadata.json"
PDF_PATH = DATA_DIR / "reports" / "WorldEnergyOutlook2025.pdf"

# paras = extract_paragraphs(str(PDF_PATH))
# benchmarks = filter_benchmarks(paras)
# tagged = [tag(p) for p in benchmarks]
# build_index(tagged, INDEX_PATH, META_PATH)

# RUNTIME
claim = parse_claim("	We aim to keep methane emissions below 0.2% at Shell-operated oil and gas assets each year, and I am pleased to say we achieved this again in 2023.")
retrieved = retrieve(claim, INDEX_PATH, META_PATH)
prompt = build_prompt(claim, retrieved)
print(evaluate(prompt))
