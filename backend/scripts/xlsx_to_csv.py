import pandas as pd
from pathlib import Path

# Find repo root dynamically (this file lives in backend/scripts/)
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "data"
DST = ROOT / "backend" / "quizbank-db" / "db-init" / "data"
DST.mkdir(parents=True, exist_ok=True)

print(f"Reading from: {SRC}")
print(f"Writing to:   {DST}")

# === 3. Loop through each Excel file ===
for x in SRC.glob("*.xlsx"):
    print(f"📘 Processing {x.name} ...")
    try:
        # Read all sheets (context + questions)
        sheets = pd.read_excel(x, sheet_name=None, dtype=str)
    except Exception as e:
        print(f"❌ Error reading {x.name}: {e}")
        continue

    for sheet_name, df in sheets.items():
        df.columns = [c.strip() for c in df.columns]
        df = df.fillna("")  # avoid NaN
        out_name = f"{x.stem}_{sheet_name.lower()}.csv"
        out_path = DST / out_name
        df.to_csv(out_path, index=False)
        print(f"✅ Saved: {out_path.name}")

print("\n🎉 All Excel sheets converted successfully!")
