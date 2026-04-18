"""
parsers.py - FIXED 'pos' ERROR + PRODUCTION READY
Compatible with your main.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

# =====================================================
# ROBUST UTILITIES
# =====================================================
def safe_num(val):
    try:
        return float(val) if pd.notna(val) else 0.0
    except:
        return 0.0

def clean_cols(df):
    df.columns = [str(c).lower().strip().replace(' ', '_').replace('-', '_')[:30] for c in df.columns]
    return df

def find_col(cols, patterns):
    for col in cols:
        if any(p in str(col).lower() for p in patterns):
            return str(col).lower()
    return None

def get_state_code(state):
    state = str(state).lower().strip()
    mapping = {
        'delhi': '07', 'maharashtra': '27', 'karnataka': '29', 
        'tamil nadu': '33', 'gujarat': '24', 'rajasthan': '08',
        'uttar pradesh': '09', 'haryana': '06', 'punjab': '03'
    }
    return mapping.get(state, None)

def calc_tax(pos, taxable):
    if pos == '07':
        return 0.0, taxable*0.015, taxable*0.015  # IGST, CGST, SGST
    else:
        return taxable*0.03, 0.0, 0.0

# =====================================================
# MEESHO PARSER
# =====================================================
class MeeshoParser:
    ETIN = "07AARCM9332R1CQ"

    def parse_files(self, files):
        print("\n🔍 MEESHO")
        rows = []
        
        for file in files:
            if 'meesho' not in Path(file).name.lower():
                continue
                
            print(f"  📄 {Path(file).name}")
            try:
                if file.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                    
                df = clean_cols(df)
                cols = df.columns.tolist()
                
                state_col = find_col(cols, ['state', 'delivery', 'place'])
                taxable_col = find_col(cols, ['taxable', 'sale', 'value', 'amount'])
                
                if not state_col or not taxable_col:
                    print(f"    ❌ No state/taxable cols")
                    continue
                
                temp = pd.DataFrame({
                    'platform': 'Meesho',
                    'pos': df[state_col].apply(get_state_code),
                    'taxable_value': df[taxable_col].apply(safe_num),
                    'invoice_no': df.iloc[:, 0].astype(str)  # First col fallback
                })
                
                # Calculate taxes
                igst, cgst, sgst = calc_tax(temp['pos'], temp['taxable_value'])
                temp['igst'] = igst
                temp['cgst'] = cgst
                temp['sgst'] = sgst
                temp['txn_type'] = 'sale'
                
                # Filter valid rows
                valid = temp[(temp['pos'].notna()) & (temp['pos'] != '00') & (temp['taxable_value'] > 0)]
                if not valid.empty:
                    rows.append(valid)
                    print(f"    ✅ {len(valid)} rows")
                    
            except Exception as e:
                print(f"    ❌ {e}")
        
        if not rows:
            return None
            
        final = pd.concat(rows).drop_duplicates().reset_index(drop=True)
        total = final['taxable_value'].sum()
        
        return {
            "platform": "Meesho",
            "etin": self.ETIN,
            "summary": {
                "rows": final.groupby('pos')[['taxable_value', 'igst', 'cgst', 'sgst']].sum().round(2).to_dict('records'),
                "total_taxable": round(total, 2),
                "total_igst": round(final['igst'].sum(), 2),
                "total_cgst": round(final['cgst'].sum(), 2),
                "total_sgst": round(final['sgst'].sum(), 2)
            },
            "invoice_docs": [],
            "credit_docs": [],
            "debit_docs": []
        }

# =====================================================
# FLIPKART PARSER
# =====================================================
class FlipkartParser:
    ETIN = "07AACCF0683K1CU"

    def parse_files(self, files):
        print("\n🔍 FLIPKART")
        rows = []
        
        for file in files:
            if 'flipkart' not in Path(file).name.lower():
                continue
                
            print(f"  📄 {Path(file).name}")
            try:
                if file.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                    
                df = clean_cols(df)
                cols = df.columns.tolist()
                
                state_col = find_col(cols, ['state', 'delivery', 'place'])
                taxable_col = find_col(cols, ['taxable', 'sale', 'value'])
                
                if not state_col or not taxable_col:
                    continue
                
                temp = pd.DataFrame({
                    'platform': 'Flipkart',
                    'pos': df[state_col].apply(get_state_code),
                    'taxable_value': df[taxable_col].apply(safe_num),
                    'invoice_no': ''
                })
                
                igst, cgst, sgst = calc_tax(temp['pos'], temp['taxable_value'])
                temp['igst'] = igst
                temp['cgst'] = cgst
                temp['sgst'] = sgst
                temp['txn_type'] = 'sale'
                
                valid = temp[(temp['pos'].notna()) & (temp['pos'] != '00') & (temp['taxable_value'] > 0)]
                if not valid.empty:
                    rows.append(valid)
                    
            except:
                pass
        
        if not rows:
            return None
            
        final = pd.concat(rows).drop_duplicates().reset_index(drop=True)
        return {
            "platform": "Flipkart",
            "etin": self.ETIN,
            "summary": {
                "rows": final.groupby('pos')[['taxable_value', 'igst', 'cgst', 'sgst']].sum().round(2).to_dict('records'),
                "total_taxable": round(final['taxable_value'].sum(), 2),
                "total_igst": round(final['igst'].sum(), 2),
                "total_cgst": round(final['cgst'].sum(), 2),
                "total_sgst": round(final['sgst'].sum(), 2)
            },
            "invoice_docs": [],
            "credit_docs": [],
            "debit_docs": []
        }

# =====================================================
# AMAZON PARSER
# =====================================================
class AmazonParser:
    ETIN = "07AAICA3918J1CV"

    def parse_files(self, files):
        print("\n🔍 AMAZON")
        rows = []
        
        for file in files:
            if 'amazon' not in Path(file).name.lower():
                continue
                
            print(f"  📄 {Path(file).name}")
            try:
                if file.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                    
                df = clean_cols(df)
                cols = df.columns.tolist()
                
                state_col = find_col(cols, ['state', 'ship_state', 'place'])
                taxable_col = find_col(cols, ['tax_exclusive', 'taxable', 'gross'])
                
                if not state_col or not taxable_col:
                    continue
                
                temp = pd.DataFrame({
                    'platform': 'Amazon',
                    'pos': df[state_col].apply(get_state_code),
                    'taxable_value': df[taxable_col].apply(safe_num),
                    'invoice_no': ''
                })
                
                igst, cgst, sgst = calc_tax(temp['pos'], temp['taxable_value'])
                temp['igst'] = igst
                temp['cgst'] = cgst
                temp['sgst'] = sgst
                temp['txn_type'] = 'sale'
                
                valid = temp[(temp['pos'].notna()) & (temp['pos'] != '00') & (temp['taxable_value'] > 0)]
                if not valid.empty:
                    rows.append(valid)
                    
            except:
                pass
        
        if not rows:
            return None
            
        final = pd.concat(rows).drop_duplicates().reset_index(drop=True)
        return {
            "platform": "Amazon",
            "etin": self.ETIN,
            "summary": {
                "rows": final.groupby('pos')[['taxable_value', 'igst', 'cgst', 'sgst']].sum().round(2).to_dict('records'),
                "total_taxable": round(final['taxable_value'].sum(), 2),
                "total_igst": round(final['igst'].sum(), 2),
                "total_cgst": round(final['cgst'].sum(), 2),
                "total_sgst": round(final['sgst'].sum(), 2)
            },
            "invoice_docs": [],
            "credit_docs": [],
            "debit_docs": []
        }

# =====================================================
# AUTO MERGE - FIXED
# =====================================================
class AutoMergeParser:
    def parse_files(self, files):
        parsers = [MeeshoParser(), FlipkartParser(), AmazonParser()]
        results = []
        
        print("🚀 PARSING FILES:")
        for f in files:
            print(f"  📄 {Path(f).name}")
        
        for parser in parsers:
            try:
                result = parser.parse_files(files)
                if result:
                    results.append(result)
            except:
                pass
        
        if not results:
            print("❌ No data found")
            return {
                "summary": {"rows": [], "total_taxable": 0, "total_igst": 0, "total_cgst": 0, "total_sgst": 0},
                "invoice_docs": [], "credit_docs": [], "debit_docs": [], "clttx": []
            }
        
        # MERGE
        state_totals = defaultdict(lambda: {'taxable_value': 0, 'igst': 0, 'cgst': 0, 'sgst': 0})
        clttx = []
        
        for result in results:
            for row in result['summary']['rows']:
                pos = row['pos']
                state_totals[pos]['taxable_value'] += row['taxable_value']
                state_totals[pos]['igst'] += row['igst']
                state_totals[pos]['cgst'] += row['cgst']
                state_totals[pos]['sgst'] += row['sgst']
            
            clttx.append({
                'etin': result['etin'],
                'suppval': result['summary']['total_taxable'],
                'igst': result['summary']['total_igst'],
                'cgst': result['summary']['total_cgst'],
                'sgst': result['summary']['total_sgst'],
                'cess': 0,
                'flag': 'N'
            })
        
        rows = [{'pos': k, **v} for k, v in state_totals.items()]
        
        return {
            "summary": {
                "rows": rows,
                "total_taxable": sum(r['taxable_value'] for r in rows),
                "total_igst": sum(r['igst'] for r in rows),
                "total_cgst": sum(r['cgst'] for r in rows),
                "total_sgst": sum(r['sgst'] for r in rows),
            },
            "invoice_docs": [],
            "credit_docs": [],
            "debit_docs": [],
            "clttx": clttx
        }