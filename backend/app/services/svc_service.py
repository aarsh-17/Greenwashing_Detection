from joblib import load
from pathlib import Path
import numpy as np
import pandas as pd
import re

# Resolve path relative to this file
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "greenwashing_tfidf_linearsvc.pkl"

model = load(MODEL_PATH)   # ✅ guaranteed to work


def detect_has_number(text: str) -> int:
    return int(bool(re.search(r"\d", text)))


def svc_predict_risk(sentence: str) -> tuple[str, float]:
    X = pd.DataFrame([{
        "claim_sentence": sentence,
        "has_number": detect_has_number(sentence)
    }])

    pred = model.predict(X)[0]

    margins = model.decision_function(X)[0]
    confidence = min(1.0, abs(float(np.max(margins))) / 3.0)

    return pred.upper(), round(confidence, 3) 
