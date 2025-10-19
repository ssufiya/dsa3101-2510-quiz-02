"""
Convert XLSX files to CSV files
Automatically converts all .xlsx files in data/ folder to .csv
"""
import os
from pathlib import Path
import pandas as pd


def convert_xlsx_to_csv(data_dir):
    """
    Convert all XLSX files in data directory to CSV format
    
    Args:
        data_dir: Path to data directory
    """
    data_path = Path(data_dir)
    
    if not data_path.exists():
        print(f"Data directory not found: {data_path}")
        return
    
    # Find all xlsx files
    xlsx_files = list(data_path.glob('*.xlsx'))
    
    if not xlsx_files:
        print("No XLSX files found to convert")
        return
    
    print(f"\n{'='*50}")
    print(f"Converting XLSX files to CSV")
    print(f"{'='*50}\n")
    
    for xlsx_file in xlsx_files:
        try:
            # Output CSV filename
            csv_file = xlsx_file.with_suffix('.csv')
            
            print(f"Converting: {xlsx_file.name} → {csv_file.name}")
            
            # Read XLSX file
            df = pd.read_excel(xlsx_file, engine='openpyxl')
            
            # Clean column names (strip whitespace)
            df.columns = df.columns.str.strip()
            
            # Save as CSV
            df.to_csv(csv_file, index=False, encoding='utf-8')
            
            print(f"  ✓ Converted successfully ({len(df)} rows)")
            
        except Exception as e:
            print(f"  ✗ Error converting {xlsx_file.name}: {str(e)}")
    
    print(f"\n{'='*50}")
    print(f"✓ Conversion complete!")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    # Convert files in data directory
    data_dir = Path(__file__).parent.parent / 'data'
    convert_xlsx_to_csv(data_dir)