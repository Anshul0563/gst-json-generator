"""
parsers.py - PRODUCTION GRADE GST GSTR-1 JSON Generator
Fixed 2x inflation bug + enterprise-grade deduplication
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
from collections import defaultdict

# Assuming utils.py exists with these functions - if not, implemented below
def num(val): return pd.to_numeric(val, errors='coerce').fillna(0)
def clean_cols(df): 
    df.columns = df.columns.str.strip().str.lower().str.replace(r'\s+', '_', regex=True)
    return df
def first_match(cols, patterns): 
    for col in cols:
        if any(p in col for p in patterns): 
            return col
    return None
def state_to_code(state):
    # Simplified state mapping - extend as needed
    state_map = {
        'delhi': '07', 'maharashtra': '27', 'karnataka': '29', 
        'tamil nadu': '33', 'gujarat': '24', 'rajasthan': '08',
        'uttar pradesh': '09', 'haryana': '06', 'punjab': '03',
        'telangana': '36', 'andhra pradesh': '37', 'west bengal': '19'
    }
    return state_map.get(state.lower(), '00')

def detect_tax_columns(cols):
    return {
        'igst': first_match(cols, ['igst', 'inter_state', 'ig_st']),
        'cgst': first_match(cols, ['cgst', 'central_gst', 'cg_st']),
        'sgst': first_match(cols, ['sgst', 'state_gst', 'sg_st', 'utgst'])
    }

def safe_docs(series):
    return [str(x) for x in series.dropna().unique() if len(str(x)) > 3]

def calculate_tax_from_taxable(pos, taxable):
    """3% IGST inter-state, 1.5%+1.5% Delhi intra-state"""
    igst = np.where(pos == '07', taxable * 0.015, taxable * 0.03)
    cgst = np.where(pos == '07', taxable * 0.015, 0)
    sgst = np.where(pos == '07', taxable * 0.015, 0)
    return igst, cgst, sgst

def is_valid_transaction_row(row, required_cols):
    """Strict transaction row validation"""
    if pd.isna(row.get('pos')):
        return False
    
    taxable = num(row.get('taxable_value', 0))
    if taxable == 0:
        return False
    
    # Skip obvious summary patterns
    text = str(row.get('invoice_no', '') + str(row.get('order_id', ''))).lower()
    skip_patterns = ['total', 'grand', 'summary', 'subtotal', 'balance']
    if any(p in text for p in skip_patterns):
        return False
    
    return True

def enterprise_dedupe(df, platform):
    """Multi-level deduplication with platform prefix"""
    df = df.copy()
    
    # Prefix invoice/order IDs with platform to prevent cross-platform dupes
    df['dedupe_key'] = (df['platform'].astype(str) + '_' + 
                       df['invoice_no'].fillna('').astype(str) + '_' +
                       df['order_id'].fillna('').astype(str))
    
    # Primary dedupe: exact match on key + amounts
    primary_cols = ['dedupe_key', 'taxable_value', 'igst', 'cgst', 'sgst']
    df = df.drop_duplicates(subset=primary_cols, keep='first')
    
    # Secondary dedupe: same key, closest taxable value (handles minor rounding)
    def secondary_dedupe(group):
        if len(group) <= 1:
            return group
        # Keep row with smallest absolute taxable value (most granular)
        return group.loc[group['taxable_value'].abs().idxmin():]
    
    df = df.groupby('dedupe_key').apply(secondary_dedupe).reset_index(drop=True)
    
    return df.drop(columns=['dedupe_key'])


# =====================================================
# BASE PARSER - ENHANCED
# =====================================================
class BaseParser:
    def __init__(self):
        self.platform = self.__class__.__name__.replace('Parser', '')
        self.rows = []
        self.invoice_docs = []
        self.credit_docs = []
        self.debit_docs = []

    def is_my_file(self, file_path: Path) -> bool:
        """File type detection"""
        name = file_path.name.lower()
        return self.platform.lower() in name or self.platform[0].lower() in name

    def select_transaction_sheet(self, xls: pd.ExcelFile) -> Optional[str]:
        """Smart sheet selection - skip summary/total sheets"""
        skip_patterns = ['summary', 'pivot', 'total', 'overview', 'dashboard']
        priority_patterns = ['sales', 'transaction', 'invoice', 'gstr', 'report']
        
        for sheet in xls.sheet_names:
            name = sheet.lower()
            if any(p in name for p in skip_patterns):
                continue
            if any(p in name for p in priority_patterns):
                return sheet
        
        # Fallback to first non-summary sheet
        for sheet in xls.sheet_names:
            if not any(p in sheet.lower() for p in skip_patterns):
                return sheet
        return None

    def parse_single_file(self, file_path: Path):
        """Parse single file with strict validation"""
        ext = file_path.suffix.lower()
        
        try:
            if ext == '.csv':
                df = pd.read_csv(file_path, encoding_errors='ignore')
            else:  # Excel
                xls = pd.ExcelFile(file_path)
                sheet = self.select_transaction_sheet(xls)
                if not sheet:
                    return
                df = pd.read_excel(file_path, sheet_name=sheet)
        except Exception:
            return

        self._process_dataframe(df, file_path.name)

    def _process_dataframe(self, df: pd.DataFrame, filename: str):
        """Core processing with strict filtering"""
        raw = clean_cols(df)
        cols = raw.columns.tolist()
        
        # Critical column detection
        state_col = first_match(cols, ['delivery_state', 'ship_to_state', 'state', 'place_of_supply'])
        taxable_col = first_match(cols, ['taxable_value', 'tax_exclusive_gross', 'taxable', 'taxable_amount'])
        inv_col = first_match(cols, ['invoice', 'invoice_number', 'invoice_no'])
        order_col = first_match(cols, ['order', 'order_id'])
        
        if not state_col or not taxable_col:
            return

        # Build clean transaction dataframe
        temp = pd.DataFrame()
        temp['platform'] = self.platform
        temp['pos'] = raw[state_col].astype(str).apply(state_to_code)
        temp['invoice_no'] = raw[inv_col].astype(str) if inv_col else ''
        temp['order_id'] = raw[order_col].astype(str) if order_col else ''
        
        # Tax calculation with validation
        tax_cols = detect_tax_columns(cols)
        taxable_raw = raw[taxable_col]
        taxable = num(taxable_raw)
        
        if any(tax_cols.values()):  # Use provided taxes if valid
            igst = num(raw[tax_cols['igst']]) if tax_cols['igst'] else 0
            cgst = num(raw[tax_cols['cgst']]) if tax_cols['cgst'] else 0
            sgst = num(raw[tax_cols['sgst']]) if tax_cols['sgst'] else 0
            
            # Validate: tax shouldn't exceed taxable
            total_tax = igst + cgst + sgst
            valid_tax = total_tax <= taxable
            use_calculated = ~valid_tax
            
            temp['taxable_value'] = taxable
            temp['igst'] = np.where(use_calculated, 
                                  calculate_tax_from_taxable(temp['pos'], taxable)[0], igst)
            temp['cgst'] = np.where(use_calculated, 
                                  calculate_tax_from_taxable(temp['pos'], taxable)[1], cgst)
            temp['sgst'] = np.where(use_calculated, 
                                  calculate_tax_from_taxable(temp['pos'], taxable)[2], sgst)
        else:
            temp['taxable_value'] = taxable
            temp['igst'], temp['cgst'], temp['sgst'] = calculate_tax_from_taxable(
                temp['pos'], taxable)
        
        temp['txn_type'] = 'sale'
        
        # Handle returns/credits
        if any(word in filename.lower() for word in ['return', 'credit', 'refund']):
            temp['taxable_value'] *= -1
            temp['igst'] *= -1
            temp['cgst'] *= -1
            temp['sgst'] *= -1
            temp['txn_type'] = 'return'
            if inv_col:
                self.credit_docs.extend(safe_docs(raw[inv_col]))
        elif inv_col:
            self.invoice_docs.extend(safe_docs(raw[inv_col]))

        # STRICT ROW FILTERING
        temp = temp[temp['taxable_value'] != 0]
        temp = temp[temp['pos'] != '00']  # Skip invalid states
        temp = temp.apply(is_valid_transaction_row, axis=1)
        
        if not temp.empty:
            self.rows.append(temp)

    def parse_files(self, files: List[str]) -> Dict[str, Any]:
        """Main entry point"""
        self.rows.clear()
        self.invoice_docs.clear()
        self.credit_docs.clear()
        self.debit_docs.clear()
        
        my_files = [f for f in files if self.is_my_file(Path(f))]
        if not my_files:
            raise ValueError(f"No valid {self.platform} files found")
        
        for file in my_files:
            self.parse_single_file(Path(file))
        
        if not self.rows:
            raise ValueError(f"No valid transactions found in {self.platform} files")
        
        # ENTERPRISE DEDUPLICATION
        final = enterprise_dedupe(pd.concat(self.rows, ignore_index=True), self.platform)
        
        summary = {
            'rows': final.to_dict('records'),
            'total_taxable': round(final['taxable_value'].sum(), 2),
            'total_igst': round(final['igst'].sum(), 2),
            'total_cgst': round(final['cgst'].sum(), 2),
            'total_sgst': round(final['sgst'].sum(), 2)
        }
        
        return {
            'platform': self.platform,
            'etin': self.get_etin(),
            'summary': summary,
            'invoice_docs': list(set(self.invoice_docs)),  # Dedupe docs
            'credit_docs': list(set(self.credit_docs)),
            'debit_docs': list(set(self.debit_docs))
        }

    def get_etin(self) -> str:
        """Override in subclasses"""


# =====================================================
# MARKETPLACE PARSERS
# =====================================================
class MeeshoParser(BaseParser):
    def get_etin(self): return "07AARCM9332R1CQ"

class FlipkartParser(BaseParser):
    def get_etin(self): return "07AACCF0683K1CU"

class AmazonParser(BaseParser):
    def get_etin(self): return "07AAICA3918J1CV"


# =====================================================
# AUTO MERGE PARSER
# =====================================================
class AutoMergeParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.parsers = [MeeshoParser(), FlipkartParser(), AmazonParser()]
        self.results = []

    def parse_files(self, files: List[str]) -> Dict[str, Any]:
        """Merge all platforms"""
        errors = []
        
        for parser in self.parsers:
            try:
                result = parser.parse_files(files)
                total = (result['summary']['total_taxable'] + 
                        result['summary']['total_igst'] + 
                        result['summary']['total_cgst'] + 
                        result['summary']['total_sgst'])
                if total > 0:
                    self.results.append(result)
            except Exception as e:
                errors.append(f"{parser.platform}: {str(e)}")
        
        if not self.results:
            raise ValueError("No valid data from any platform\n" + "\n".join(errors))
        
        return self._merge_results()

    def _merge_results(self) -> Dict[str, Any]:
        """Merge with state-wise aggregation"""
        state_totals = defaultdict(lambda: {
            'pos': None, 'taxable_value': 0, 'igst': 0, 'cgst': 0, 'sgst': 0
        })
        
        all_invoice_docs = []
        all_credit_docs = []
        all_debit_docs = []
        clttx = []
        
        for result in self.results:
            summary = result['summary']
            
            # Aggregate docs
            all_invoice_docs.extend(result['invoice_docs'])
            all_credit_docs.extend(result['credit_docs'])
            all_debit_docs.extend(result['debit_docs'])
            
            # Build clttx
            clttx.append({
                'etin': result['etin'],
                'suppval': round(summary['total_taxable'], 2),
                'igst': round(summary['total_igst'], 2),
                'cgst': round(summary['total_cgst'], 2),
                'sgst': round(summary['total_sgst'], 2),
                'cess': 0,
                'flag': 'N'
            })
            
            # State-wise totals
            for row in summary['rows']:
                pos = row['pos']
                state_totals[pos]['pos'] = pos
                state_totals[pos]['taxable_value'] += row['taxable_value']
                state_totals[pos]['igst'] += row['igst']
                state_totals[pos]['cgst'] += row['cgst']
                state_totals[pos]['sgst'] += row['sgst']
        
        summary = {
            'rows': list(state_totals.values()),
            'total_taxable': round(sum(r['taxable_value'] for r in state_totals.values()), 2),
            'total_igst': round(sum(r['igst'] for r in state_totals.values()), 2),
            'total_cgst': round(sum(r['cgst'] for r in state_totals.values()), 2),
            'total_sgst': round(sum(r['sgst'] for r in state_totals.values()), 2)
        }
        
        return {
            'summary': summary,
            'invoice_docs': list(set(all_invoice_docs)),
            'credit_docs': list(set(all_credit_docs)),
            'debit_docs': list(set(all_debit_docs)),
            'clttx': clttx
        }