# src/load_data.py
import pandas as pd
from pathlib import Path

RAW_PATH = Path(__file__).parents[1] / "data" / "raw" / "mpox_africa_dataset.xlsx"
CLEAN_PATH = Path(__file__).parents[1] / "data" / "processed" / "mpox.csv"

def load_excel() -> pd.DataFrame:
    """Load the Excel file and return a tidy DataFrame."""
    df = pd.read_excel(RAW_PATH)
    # basic tidy-up
    df.columns = [c.strip() for c in df.columns]
    df["Report_Date"] = pd.to_datetime(df["Report_Date"])
    return df.sort_values(["Country", "Report_Date"])

if __name__ == "__main__":
    df = load_excel()
    CLEAN_PATH.parent.mkdir(exist_ok=True, parents=True)
    df.to_csv(CLEAN_PATH, index=False)
    print(f"✅ Loaded {len(df):,} rows → {CLEAN_PATH}")