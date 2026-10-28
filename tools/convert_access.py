"""Convert the E-Presso Access database (Support_EX_B_Sales.accdb) into CSV files.

Why this exists: Microsoft Access doesn't run on a Mac, and the hosted Streamlit
app can't read .accdb files either. This one-time script reads the three tables
(Categories, Products, Sales) with the `access-parser` library and writes each
one to a plain comma-separated CSV in data/. Values are written exactly as stored,
with nothing recalculated, so the CSVs are a faithful copy of the database.

Usage (from the project folder):
    pip install access-parser pandas
    python tools/convert_access.py data/source/Support_EX_B_Sales.accdb data/
"""
import sys
from pathlib import Path

import pandas as pd
from access_parser import AccessParser

TABLES = ["Categories", "Products", "Sales"]


def convert(accdb_path: str, out_dir: str) -> None:
    db = AccessParser(accdb_path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name in TABLES:
        df = pd.DataFrame(db.parse_table(name))
        if "Date" in df.columns:
            # Access stores a full timestamp; every date is a month-end, so keep just the date part.
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        path = out / f"{name}.csv"
        df.to_csv(path, index=False)
        extra = f", revenue sum {df['Revenue'].sum():,.2f}" if "Revenue" in df.columns else ""
        print(f"{name}: {len(df):,} rows x {df.shape[1]} cols -> {path}{extra}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python tools/convert_access.py <file.accdb> <output_folder>")
    convert(sys.argv[1], sys.argv[2])
