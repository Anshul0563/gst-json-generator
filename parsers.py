"""
parsers.py - PRODUCTION GRADE GST GSTR-1 JSON Generator
FIXED: float.fillna() error + enhanced robustness
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Core utilities - ROBUST
def num(val): 
    if pd.isna(val):
        return 0.0
    return pd.to_numeric(val, errors='coerce') or 0.0

def clean_cols(df): 
    df.columns = (df.columns.astype(str)
                  .str.strip()
                  .str.lower()
                  .str.replace(r'\s+', '_', regex=True)
                  .str.replace(r'[^\w_]', '', regex=True))
    return df

def first_match(cols, patterns): 
    for col in cols:
        if isinstance(col, str) and any(p in col for p in patterns): 
            return col
    return None

def state_to_code(state):
    if pd.isna(state):
        return '00'
    state_str = str(state).lower().strip()
    state_map = {
        'delhi': '07', 'maharashtra': '27', 'karnataka': '29', 
        'tamilnadu': '33', 'tamil nadu': '33', 'gujarat': '24', 
        'rajasthan': '08', 'uttar pradesh': '09', 'haryana': '06',
        'punjab': '03', 'telangana': '36', 'andhrapradesh': '37', 
        'andhra pradesh': '37', 'west bengal': '19', 'kerala': '32',
        'madhyapradesh': '23', 'madhya pradesh': '23'
    }
    return state_map.get(state_str, '00')

def detect_tax_columns(cols):
    return {
        'igst': first_match(cols, ['igst', 'inter_state', 'ig_st', 'integrated']),
        'cgst': first_match(cols, ['cgst', 'central_gst', 'cg_st', 'central']),
        'sgst': first_match(cols, ['sgst', 'state_gst', 'sg_st', 'utgst', 'state'])
    }

def safe_docs(series):
    docs = []
    for val in series:
        s = str(val).strip()
        if len(s) > 3 and s != 'nan':
            docs.append(s)
    return list(set(docs))

def calculate_tax_from_taxable(pos, taxable):
    igst = np.where(pos == '07', taxable * 0.015, taxable * 0.03)
    cgst = np.where(pos == '07', taxable * 0.015, 0)
    sgst = np.where(pos == '07', taxable * 0.015, 0)
    return igst, cgst, sgst

def is_valid_transaction_row(row_series):
    """Safe row validation"""
    try:
        pos = str(row_series.get('pos', '')).strip()
        if not pos or pos == '00' or len(pos) != 2:
            return False
        
        taxable = num(row_series.get('taxable_value', 0))
        if taxable == 0:
            return False
        
        # Skip summary rows
        skip_text = (str(row_series.get('invoice_no', '')).lower() + 
                    str(row_series.get('order_id', '')).lower())
        skip_patterns = ['total', 'grand', 'summary', 'subtotal', 'balance']
        if any(p in skip_text for p in skip_patterns):
            return False
        
        return True
    except:
        return False

def enterprise_dedupe(df):
    """FIXED: Safe deduplication - no fillna on floats"""
    if df.empty:
        return df
        
    df = df.copy()
    
    # Safe string conversion for dedupe key
    def safe_str(val):
        if pd.isna(val):
            return ''
        return str(val).strip()
    
    df['dedupe_key'] = (df['platform'].astype(str) + '_' + 
                       df['invoice_no'].apply(safe_str) + '_' +
                       df['order_id'].apply(safe_str) + '_' +
                       df['pos'].astype(str))
    
    # Round numeric columns safely
    numeric_cols = ['taxable_value', 'igst', 'cgst', 'sgst']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(num).round(2)
    
    # Primary dedupe
    primary_cols = ['dedupe_key', 'taxable_value', 'igst', 'cgst', 'sgst']
    available_cols = [c for c in primary_cols if c in df.columns]
    df = df.drop_duplicates(subset=available_cols, keep='first')
    
    return df.drop(columns=['dedupe_key'], errors='ignore')


# =====================================================
# BASE PARSER - BULLETPROOF
# =====================================================
class BaseParser:
    def __init__(self):
        self.platform = self.__class__.__name__.replace('Parser', '')
        self.rows = []
        self.invoice_docs = []
        self.credit_docs = []
        self.debit_docs = []

    def is_my_file(self, file_path: Path) -> bool:
        name = file_path.name.lower()
        base_name = self.platform.lower()
        return any(x in name for x in [base_name, base_name[:3]])

    def select_transaction_sheet(self, xls: pd.ExcelFile) -> Optional[str]:
        skip_patterns = ['summary', 'pivot', 'total', 'overview', 'dashboard']
        priority_patterns = ['sales', 'transaction', 'invoice', 'gstr', 'order']
        
        for sheet in xls.sheet_names:
            name = str(sheet).lower()
            if any(skip in name for skip in skip_patterns):
                continue
            if any(pri in name for pri in priority_patterns):
                return sheet
        
        return xls.sheet_names[0] if xls.sheet_names else None

    def parse_single_file(self, file_path: Path):
        print(f"📁 Processing: {file_path.name}")
        ext = file_path.suffix.lower()
        
        try:
            if ext == '.csv':
                df = pd.read_csv(file_path, encoding_errors='ignore', low_memory=False)
            else:
                xls = pd.ExcelFile(file_path)
                sheet = self.select_transaction_sheet(xls)
                if not sheet:
                    print(f"   ❌ No valid sheet found")
                    return
                df = pd.read_excel(file_path, sheet_name=sheet)
                print(f"   📄 Sheet: {sheet}")
        except Exception as e:
            print(f"   ❌ Read error: {e}")
            return

        print(f"   📊 Raw rows: {len(df)}")
        self._process_dataframe(df, file_path.name)
        
        if self.rows:
            print(f"   ✅ Added {len(self.rows[-1])} valid rows")

    def _process_dataframe(self, df: pd.DataFrame, filename: str):
        if df.empty:
            return
            
        raw = clean_cols(df)
        cols = raw.columns.tolist()
        
        # Enhanced column detection
        state_col = (first_match(cols, ['delivery_state', 'ship_to_state', 'state', 'place_of_supply', 'state_name']) or
                    first_match(cols, ['destination_state']))
        taxable_col = (first_match(cols, ['taxable_value', 'tax_exclusive_gross', 'taxable', 'taxable_amount', 'sale_value']) or
                      first_match(cols, ['taxablevalue', 'salevalue', 'amount']))
        inv_col = first_match(cols, ['invoice', 'invoice_number', 'invoice_no', 'invoiceid', 'inv_no'])
        order_col = first_match(cols, ['order', 'order_id', 'orderid', 'order_number'])
        
        print(f"   🔍 Cols - State: {state_col}, Taxable: {taxable_col}")
        
        if not state_col or not taxable_col:
            print(f"   ❌ Missing key columns")
            return

        # Build safe dataframe
        temp = pd.DataFrame({
            'platform': self.platform,
            'pos': raw[state_col].apply(state_to_code),
            'invoice_no': raw[inv_col].astype(str) if inv_col else None,
            'order_id': raw[order_col].astype(str) if order_col else None,
        })
        
        # Safe taxable extraction
        taxable_raw = raw[taxable_col]
        temp['taxable_value'] = taxable_raw.apply(num)
        
        # Tax calculation
        tax_cols = detect_tax_columns(cols)
        igst, cgst, sgst = 0, 0, 0
        
        if any(tax_cols.values()):
            if tax_cols['igst']: igst = raw[tax_cols['igst']].apply(num)
            if tax_cols['cgst']: cgst = raw[tax_cols['cgst']].apply(num)
            if tax_cols['sgst']: sgst = raw[tax_cols['sgst']].apply(num)
            
            total_tax = igst + cgst + sgst
            calc_igst, calc_cgst, calc_sgst = calculate_tax_from_taxable(temp['pos'], temp['taxable_value'])
            
            # Use calculated if provided taxes are suspicious
            use_calc = total_tax > temp['taxable_value']
            temp['igst'] = np.where(use_calc, calc_igst, igst)
            temp['cgst'] = np.where(use_calc, calc_cgst, cgst)
            temp['sgst'] = np.where(use_calc, calc_sgst, sgst)
        else:
            temp['igst'], temp['cgst'], temp['sgst'] = calculate_tax_from_taxable(
                temp['pos'], temp['taxable_value'])
        
        temp['txn_type'] = 'sale'

        # Document extraction
        if inv_col:
            docs = safe_docs(raw[inv_col])
            if any('return' in filename.lower() for filename in [filename]):
                self.credit_docs.extend(docs)
            else:
                self.invoice_docs.extend(docs)

        # Returns
        if any(word in filename.lower() for word in ['return', 'credit', 'refund']):
            temp['taxable_value'] *= -1
            temp['igst'] *= -1
            temp['cgst'] *= -1
            temp['sgst'] *= -1
            temp['txn_type'] = 'return'

        # STRICT FILTERING
        before = len(temp)
        temp = temp[temp['taxable_value'] != 0]
        temp = temp[temp['pos'].str.len() == 2]
        temp = temp.apply(is_valid_transaction_row, axis=1)
        after = len(temp)
        
        print(f"   🔧 Filtered: {before} → {after} rows")
        
        if after > 0:
            self.rows.append(temp)

    def parse_files(self, files: List[str]) -> Dict[str, Any]:
        self.rows.clear()
        self.invoice_docs.clear()
        self.credit_docs.clear()
        self.debit_docs.clear()
        
        my_files = [f for f in files if self.is_my_file(Path(f))]
        print(f"\n🚀 {self.platform}: Scanning {len(my_files)} files")
        
        if not my_files:
            raise ValueError(f"No {self.platform} files found. Looking for: {self.platform.lower()}")
        
        for file in my_files:
            self.parse_single_file(Path(file))
        
        if not self.rows:
            raise ValueError(f"No valid {self.platform} transactions found")
        
        final = enterprise_dedupe(pd.concat(self.rows, ignore_index=True))
        print(f"✅ {self.platform}: {len(final)} FINAL transactions")
        print(f"   Total taxable: ₹{final['taxable_value'].sum():,.2f}")
        
        summary = {
            'rows': final[['pos', 'taxable_value', 'igst', 'cgst', 'sgst']].to_dict('records'),
            'total_taxable': round(final['taxable_value'].sum(), 2),
            'total_igst': round(final['igst'].sum(), 2),
            'total_cgst': round(final['cgst'].sum(), 2),
            'total_sgst': round(final['sgst'].sum(), 2)
        }
        
        return {
            'platform': self.platform,
            'etin': self.get_etin(),
            'summary': summary,
            'invoice_docs': self.invoice_docs[:100],  # Limit
            'credit_docs': self.credit_docs[:100],
            'debit_docs': self.debit_docs[:100]
        }

    def get_etin(self) -> str:
        return "07DUMMYETIN1Z5"


# =====================================================
# MARKETPLACE PARSERS
# =====================================================
class MeeshoParser(BaseParser):
    def get_etin(self): return "07AARCM9332R1CQ"
    def is_my_file(self, file_path: Path) -> bool:
        name = file_path.name.lower()
        return any(x in name for x in ['meesho', 'tcs', 'invoice', 'settlement'])

class FlipkartParser(BaseParser):
    def get_etin(self): return "07AACCF0683K1CU"
    def is_my_file(self, file_path: Path) -> bool:
        name = file_path.name.lower()
        return any(x in name for x in ['flipkart', 'sales', 'settlement', 'payout'])

class AmazonParser(BaseParser):
    def get_etin(self): return "07AAICA3918J1CV"
    def is_my_file(self, file_path: Path) -> bool:
        name = file_path.name.lower()
        return any(x in name for x in ['amazon', 'amzn', 'seller'])


# =====================================================
# AUTO MERGE
# =====================================================
class AutoMergeParser:
    def __init__(self):
        self.parsers = [MeeshoParser(), FlipkartParser(), AmazonParser()]

    def parse_files(self, files: List[str]) -> Dict[str, Any]:
        results = []
        print("\n" + "="*60)
        print("🔥 GST GSTR-1 PARSER START")
        print("="*60)
        
        for parser in self.parsers:
            try:
                data = parser.parse_files(files)
                total = data['summary']['total_taxable']
                if total > 0:
                    results.append(data)
            except Exception as e:
                print(f"⚠️  {parser.platform}: {e}")
        
        if not results:
            print("❌ NO VALID DATA FOUND")
            raise ValueError("No valid marketplace data")
        
        merged = self._merge_results(results)
        print("\n🎉 SUCCESS! Generated GSTR-1 data")
        print(f"📈 Total Taxable: ₹{merged['summary']['total_taxable']:,.2f}")
        return merged

    def _merge_results(self, results):
        state_totals = defaultdict(lambda: {'taxable_value': 0, 'igst': 0, 'cgst': 0, 'sgst': 0})
        
        docs = {'invoice_docs': [], 'credit_docs': [], 'debit_docs': []}
        clttx = []
        
        for result in results:
            summary = result['summary']
            
            for doc_type in docs:
                docs[doc_type].extend(result.get(doc_type, []))
            
            clttx.append({
                'etin': result['etin'],
                'suppval': round(summary['total_taxable'], 2),
                'igst': round(summary['total_igst'], 2),
                'cgst': round(summary['total_cgst'], 2),
                'sgst': round(summary['total_sgst'], 2),
                'cess': 0,
                'flag': 'N'
            })
            
            for row in summary['rows']:
                pos = row['pos']
                state_totals[pos].update({
                    'taxable_value': state_totals[pos]['taxable_value'] + row['taxable_value'],
                    'igst': state_totals[pos]['igst'] + row['igst'],
                    'cgst': state_totals[pos]['cgst'] + row['cgst'],
                    'sgst': state_totals[pos]['sgst'] + row['sgst']
                })
        
        rows = [{'pos': pos, **vals} for pos, vals in state_totals.items()]
        
        summary = {
            'rows': rows,
            'total_taxable': round(sum(r['taxable_value'] for r in rows), 2),
            'total_igst': round(sum(r['igst'] for r in rows), 2),
            'total_cgst': round(sum(r['cgst'] for r in rows), 2),
            'total_sgst': round(sum(r['sgst'] for r in rows), 2)
        }
        
        return {
            'summary': summary,
            **{k: list(set(v)) for k, v in docs.items()},
            'clttx': clttx
        }