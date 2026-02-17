from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

BERT_MODEL_PATH = BASE_DIR / "bert_claim_classifier"
UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(exist_ok=True)

MONGO_URI = (
    "mongodb+srv://aarshdhamsania:9106435150"
    "@cluster0.zshhqce.mongodb.net/esg_db"
    "?retryWrites=true&w=majority&appName=Cluster0"
)
DB_NAME = "esg_db"
