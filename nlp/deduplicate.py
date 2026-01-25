import pandas as pd
import re
from pathlib import Path

PROJECT_ROOT = Path("D:/ESG_platform")

INPUT_FILE = PROJECT_ROOT / "nlp" / "shell_claims.xlsx"
OUTPUT_FILE = PROJECT_ROOT / "nlp" / "shell_claims_esg_deduped.xlsx"

def normalize_claim(text):
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()
    

df = pd.read_excel(INPUT_FILE)

df["norm_claim"] = df["claim_text"].apply(normalize_claim)

df = df.drop_duplicates(subset="norm_claim")

df = df.drop(columns=["norm_claim"]).reset_index(drop=True)

df.to_excel(OUTPUT_FILE, index=False)





print(f"Deduplicated claims saved to: {OUTPUT_FILE}")
print(f"Before: {len(pd.read_excel(INPUT_FILE))}")
print(f"After:  {len(df)}")
