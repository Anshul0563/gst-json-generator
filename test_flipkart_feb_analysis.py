import pandas as pd
from pathlib import Path
try:
    from parsers import FlipkartParser
    HAS_PARSER = True
except ImportError:
    HAS_PARSER = False
    print("parsers.py not importable")

feb_path = Path('/home/jarvis/Documents/1f1924de-add8-4717-8998-64952c2dc16e_1773998487000.xlsx')

print("=== FEB RAW ANALYSIS ===")
print(f"File exists: {feb_path.exists()}")

# Read all sheets
try:
    xl = pd.ExcelFile(feb_path)
    print("\\nSHEETS:", xl.sheet_names)
    for sheet in xl.sheet_names[:5]:  # first 5
        df = pd.read_excel(feb_path, sheet_name=sheet)
        print(f"\\n{sheet}: shape {df.shape}, cols: {list(df.columns)[:10]}...")
        # Key cols?
        key_patterns = ['typ', 'type', 'cancel', 'return', 'state', 'delivery', 'pos', 'sale', 'txval', 'value', 'invoice', 'rt']
        found = [c for c in df.columns if any(p in str(c).lower() for p in key_patterns)]
        print(f"  Key cols: {found}")
        # Sample rows
        print(f"  Sample rows:\\n{df.head(3).to_string()}")
except Exception as e:
    print(f"Excel read error: {e}")

if HAS_PARSER:
    print("\\n=== CURRENT PARSER OUTPUT ===")
    parser = FlipkartParser()
    result = parser.parse_files([str(feb_path)])
    if result:
        summary = result['summary']['rows']
        print(f"Parser rows: {len(summary)}")
        print("POS/Txval:")
        for r in sorted(summary, key=lambda x: x['pos']):
            print(f"  {r['pos']}: txval={r['taxable_value']:.2f} igst={r['igst']:.2f}")
        print(f"Totals: txval={sum(r['taxable_value'] for r in summary):.2f}")
    else:
        print("Parser returned None")
else:
    print("Skip parser test")
