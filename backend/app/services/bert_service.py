import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from app.config import BERT_MODEL_PATH

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

tokenizer = AutoTokenizer.from_pretrained(
    BERT_MODEL_PATH,
    local_files_only=True
)

model = AutoModelForSequenceClassification.from_pretrained(
    BERT_MODEL_PATH,
    local_files_only=True
)

model.to(device)
model.eval()

def predict_claim(sentence: str, threshold: float = 0.85):
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

    prob = probs[0][1].item()
    return prob >= threshold, round(prob, 3)
