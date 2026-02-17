import tabula
import pandas as pd
import re
from pathlib import Path

# ---------------- CONFIG ----------------
PROJECT_ROOT = Path("D:/ESG_platform")
PDF_PATH = PROJECT_ROOT / "Oil & Gas" / "Shell.pdf"
# ---------------------------------------


def normalize_cell(x):
    if pd.isna(x) or x is None:
        return ""
    x = str(x).replace("\n", " ").replace("\r", " ")
    x = re.sub(r"\s+", " ", x).strip()
    return x


def detect_year_columns(row):
    years = []
    for i, cell in enumerate(row):
        if re.fullmatch(r"20\d{2}", cell):
            years.append((i, cell))
    return years


def is_valid_table(df):
    # Too small → junk
    if df.shape[0] < 2 or df.shape[1] < 2:
        return False

    # Mostly unnamed columns → layout noise
    unnamed_ratio = sum(
        str(c).startswith("Unnamed") for c in df.columns
    ) / len(df.columns)

    if unnamed_ratio > 0.7:
        return False

    # Long prose masquerading as tables
    avg_len = df.astype(str).map(len).values.mean()
    if avg_len > 120:
        return False

    return True


def row_has_signal(row):
    text = " ".join(row).lower()

    # Must contain numbers OR ESG keywords
    has_number = bool(re.search(r"\d", text))
    has_keyword = any(
        k in text
        for k in [
            "emission", "scope", "carbon", "energy", "target",
            "%", "reduction", "intensity", "investment"
        ]
    )
    return has_number or has_keyword


def extract_tables_structured_tabula(pdf_path: Path):
    records = []
    table_id = 0

    dfs = tabula.read_pdf(
        pdf_path,
        pages="all",
        multiple_tables=True,
        lattice=True   # switch to stream=True if needed
    )

    for page_no, df in enumerate(dfs, start=1):
        if df.empty or not is_valid_table(df):
            continue

        table_id += 1

        df = df.fillna("")
        df = df.map(normalize_cell)

        print(f"\n--- RAW TABLE | Page {page_no} | Table {table_id} ---")
        print(df.to_string(index=False))

        rows = df.values.tolist()
        header = rows[0] if rows else []
        year_cols = detect_year_columns(header)

        for r_idx, row in enumerate(rows):
            if not row or all(c == "" for c in row):
                continue
            if not row_has_signal(row):
                continue

            records.append({
                "page": page_no,
                "table_id": table_id,
                "row_index": r_idx,
                "raw_row_text": " | ".join(c for c in row if c),
                "columns": row,
                "has_year_header": int(len(year_cols) >= 2),
                "year_headers": ", ".join(y for _, y in year_cols)
            })

    return pd.DataFrame(records)


# ---------------- MAIN ----------------
if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_colwidth", None)
    pd.set_option("display.width", 200)

    print("✅ Extracting tables using tabula-py (filtered ESG mode)...")

    df_tables = extract_tables_structured_tabula(PDF_PATH)

    if df_tables.empty:
        print("⚠️ No valid ESG tables found.")
    else:
        print("\n=== STRUCTURED ESG ROWS (first 40) ===")
        print(df_tables.head(40).to_string(index=False))
        print("\nFinal shape:", df_tables.shape)
