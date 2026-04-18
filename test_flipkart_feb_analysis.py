import pandas as pd
from pathlib import Path
import traceback
try:
    from parsers import FlipkartParser
    HAS_PARSER = True
except ImportError:
    HAS_PARSER = False
    print("parsers.py not importable")

feb_path = Path('/home/jarvis/Documents/1f1924de-add8-4717-8998-64952c2dc16e_1773998487000.xlsx')

print("=" * 60)
print("FLIPKART FEBRUARY FULL DEBUG ANALYSIS")
print("=" * 60)
print(f"File: {feb_path}")
print(f"Exists: {feb_path.exists()}")
print(f"Parser available: {HAS_PARSER}")

print("\n" + "=" * 60)
print("1. WORKBOOK STRUCTURE")
print("=" * 60)
try:
    xl = pd.ExcelFile(feb_path)
    print("Sheets:", xl.sheet_names)
    
    for sheet in xl.sheet_names:
        if sheet in ['Sales Report', 'Cash Back Report']:
            df = pd.read_excel(feb_path, sheet_name=sheet)
            print(f"\n{sheet}: {len(df)} rows, {len(df.columns)} cols")
            print(f"Columns: {list(df.columns[:10])}...")
except Exception as e:
    print(f"Excel error: {e}")

print("\n" + "=" * 60)
print("2. RAW TOTALS FROM EXCEL")
print("=" * 60)
try:
    xl = pd.ExcelFile(feb_path)
    
    sales_df = pd.read_excel(feb_path, sheet_name='Sales Report')
    cleaned_sales = pd.read_excel(feb_path, sheet_name='Sales Report').rename(columns=lambda x: x.lower().replace(' ', '_').replace('-', '_')[:40])
    
    state_col = None
    taxable_col = None
    invoice_col = None
    for col in cleaned_sales.columns:
        if 'delivery_state' in col:
            state_col = col
        if 'taxable_value' in col:
            taxable_col = col
        if 'invoice_amount' in col or 'final_invoice_amount' in col:
            invoice_col = col
    
    print(f"Sales Report key cols - state: {state_col}, taxable: {taxable_col}, invoice: {invoice_col}")
    
    sales_taxable_total = cleaned_sales[taxable_col].sum() if taxable_col else 0
    sales_invoice_total = cleaned_sales[invoice_col].sum() if invoice_col else 0
    print(f"Sales RAW - taxable={sales_taxable_total:.2f}, invoice={sales_invoice_total:.2f}")
    
    cash_df = pd.read_excel(feb_path, sheet_name='Cash Back Report')
    cleaned_cash = pd.read_excel(feb_path, sheet_name='Cash Back Report').rename(columns=lambda x: x.lower().replace(' ', '_').replace('-', '_')[:40])
    
    cash_taxable_col = None
    cash_invoice_col = None
    for col in cleaned_cash.columns:
        if 'taxable_value' in col:
            cash_taxable_col = col
        if 'invoice_amount' in col:
            cash_invoice_col = col
    
    print(f"Cashback key cols - taxable: {cash_taxable_col}, invoice: {cash_invoice_col}")
    
    returns_taxable_total = cleaned_cash[cash_taxable_col].sum() if cash_taxable_col else 0
    returns_invoice_total = cleaned_cash[cash_invoice_col].sum() if cash_invoice_col else 0
    print(f"Returns RAW - taxable={returns_taxable_total:.2f}, invoice={returns_invoice_total:.2f}")
    
    net_taxable = sales_taxable_total - returns_taxable_total
    net_invoice = sales_invoice_total - returns_invoice_total
    print(f"NET RAW - taxable={net_taxable:.2f}, invoice={net_invoice:.2f}")
    
except Exception as e:
    print(f"Raw totals error: {e}")

print("\n" + "=" * 60)
print("3. PARSER OUTPUT")
print("=" * 60)
if HAS_PARSER:
    try:
        parser = FlipkartParser()
        result = parser.parse_files([str(feb_path)])
        if result:
            print("✓ Parser success!")
            print(f"Platform: {result['platform']}")
            print(f"ETIN: {result['etin']}")
            print(f"Seller state: {result['seller_state_code']}")
            print(f"Total taxable: {result['summary']['total_taxable']:.2f}")
            print("\nState-wise:")
            for r in result['summary']['rows']:
                print(f"  {r['pos']}: txval={r['taxable_value']:.2f} igst={r['igst']:.2f}")
            print(f"\nInvoice docs: {len(result['invoice_docs'])}")
            print(f"Credit docs: {len(result['credit_docs'])}")
        else:
            print("✗ Parser returned None")
            print("Traceback:")
            print(traceback.format_exc())
    except Exception as e:
        print(f"Parser error: {e}")
        print(traceback.format_exc())
else:
    print("Skip parser test - import error")

print("\n" + "=" * 60)
print("4. RECONCILIATION")
print("=" * 60)
print("EXPECTED B2CS NET = 2794.18")
print("PARSER NET = [see above]")
print("Need INVOICE mode for exact match")

print("\nTo test INVOICE mode:")
print('In parsers.py: FLIPKART_VALUE_MODE = "INVOICE"')
print("Then re-run this script")

