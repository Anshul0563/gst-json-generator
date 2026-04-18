"""
parsers.py - PRODUCTION-GRADE PLATFORM PARSERS
- Meesho, Flipkart, Amazon with dedicated parsers
- AutoMergeParser for multi-platform consolidation
- Production-ready error handling and logging
- Focus on data accuracy and completeness
"""

import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any

try:
    from logger import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# =====================================================
# CORE UTILITY FUNCTIONS
# =====================================================

def safe_num(val: Any) -> float:
    """Convert value to float safely, handles commas/spaces."""
    try:
        if pd.isna(val):
            return 0.0
        val_str = str(val).strip().replace(',', '').replace(' ', '')
        return float(val_str) if val_str else 0.0
    except (ValueError, TypeError):
        return 0.0


def clean_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize DataFrame column names to lowercase with underscores."""
    df = df.copy()
    df.columns = [
        str(c).lower().strip()
        .replace(' ', '_')
        .replace('-', '_')
        .replace('/', '_')
        .replace('(', '')
        .replace(')', '')
        [:40]
        for c in df.columns
    ]
    return df


def find_col(cols: List[str], patterns: List[str]) -> Optional[str]:
    """Find first column matching any pattern (case-insensitive)."""
    cols_lower = [str(c).lower() for c in cols]
    for pattern in patterns:
        for col in cols_lower:
            if pattern in col:
                return col
    return None


def clean_invoice_no(invoice_no: Any) -> Optional[str]:
    """Clean invoice number - handles NaN, None, empty strings."""
    if pd.isna(invoice_no) or invoice_no is None:
        return None
    val_str = str(invoice_no).strip()
    if val_str and val_str.upper() not in ['NAN', 'NONE', '']:
        return val_str
    return None


def get_state_code(state: Any) -> Optional[str]:
    """Map state/city name to GST state code (2-digit)."""
    if pd.isna(state):
        return None
    
    state_lower = str(state).lower().strip()
    if not state_lower:
        return None
    
    # Check if already a 2-digit code
    if state_lower.isdigit() and len(state_lower) == 2:
        code = int(state_lower)
        if 1 <= code <= 38:
            return state_lower
        return None
    
    # Comprehensive state mapping
    mapping = {
        # Union Territories
        'andaman': '35', 'andaman nicobar': '35', 'andaman and nicobar': '35',
        'chandigarh': '04', 'ch': '04',
        'dadra': '26', 'dadra nagar haveli': '26', 'dnh': '26',
        'daman': '25', 'daman diu': '25', 'dd': '25',
        'delhi': '07', 'new delhi': '07', 'nct': '07', 'dl': '07',
        'ladakh': '38', 'ld': '38',
        'lakshadweep': '31', 'lk': '31',
        'puducherry': '34', 'pondicherry': '34', 'py': '34',
        
        # States
        'andhra': '37', 'andhra pradesh': '37', 'ap': '37',
        'arunachal': '12', 'arunachal pradesh': '12', 'ar': '12',
        'assam': '18', 'as': '18',
        'bihar': '10', 'br': '10',
        'chhattisgarh': '22', 'cg': '22',
        'goa': '30', 'ga': '30',
        'gujarat': '24', 'gj': '24',
        'haryana': '06', 'hr': '06', 'gurgaon': '06', 'gurugram': '06',
        'himachal': '02', 'himachal pradesh': '02', 'hp': '02',
        'jharkhand': '20', 'jh': '20',
        'karnataka': '29', 'kn': '29', 'bangalore': '29', 'bengaluru': '29', 'ka': '29',
        'kerala': '32', 'kl': '32',
        'madhya': '23', 'madhya pradesh': '23', 'mp': '23',
        'maharashtra': '27', 'mh': '27', 'mumbai': '27', 'pune': '27',
        'manipur': '14', 'mn': '14',
        'meghalaya': '17', 'ml': '17',
        'mizoram': '15', 'mz': '15',
        'nagaland': '13', 'nl': '13',
        'odisha': '21', 'orissa': '21', 'or': '21',
        'punjab': '03', 'pb': '03',
        'rajasthan': '08', 'rj': '08',
        'sikkim': '11', 'sk': '11',
        'tamil': '33', 'tamil nadu': '33', 'tn': '33', 'chennai': '33',
        'telangana': '36', 'tg': '36', 'ts': '36', 'hyderabad': '36',
        'tripura': '16', 'tr': '16',
        'uttar': '09', 'uttar pradesh': '09', 'up': '09', 'u.p': '09', 'noida': '09', 'ghaziabad': '09',
        'uttarakhand': '05', 'uk': '05', 'ut': '05',
        'west': '19', 'west bengal': '19', 'wb': '19',
    }
    
    # Direct lookup
    if state_lower in mapping:
        return mapping[state_lower]
    
    # Partial word match
    for key, code in mapping.items():
        if state_lower in key or key in state_lower:
            return code
    
    return None


def is_return_file(filename: str) -> bool:
    """Detect if file contains returns/refunds/credits."""
    name = str(filename).lower()
    return_keywords = ['return', 'refund', 'credit', 'cn', 'credit_note', 'credit-note']
    return any(keyword in name for keyword in return_keywords)


def calc_tax(pos: str, taxable: float) -> Tuple[float, float, float]:
    """Calculate IGST/CGST/SGST based on place of supply.
    - Delhi (pos='07'): Split into CGST + SGST
    - Other states: IGST only
    Returns: (igst, cgst, sgst)
    """
    taxable = safe_num(taxable)
    pos = str(pos).strip() if pos else ''
    
    if pos == '07':
        # Delhi split into CGST + SGST
        return 0.0, round(taxable * 0.015, 2), round(taxable * 0.015, 2)
    else:
        # Other states: IGST
        return round(taxable * 0.03, 2), 0.0, 0.0


def apply_tax_columns(
    df: pd.DataFrame,
    base_data: pd.DataFrame,
    state_col: str,
    taxable_col: str
) -> pd.DataFrame:
    """Apply tax columns with intelligent fallback.
    Priority:
    1. Use individual tax columns if they exist
    2. Calculate from taxable value if individual columns don't exist
    """
    result = base_data.copy()
    
    # Find tax columns
    igst_col = find_col(df.columns.tolist(), ['igst', 'i_gst', 'integrated'])
    cgst_col = find_col(df.columns.tolist(), ['cgst', 'c_gst', 'central'])
    sgst_col = find_col(df.columns.tolist(), ['sgst', 's_gst', 'state'])
    
    # Apply IGST
    if igst_col and igst_col in df.columns:
        result['igst'] = df[igst_col].apply(safe_num)
    else:
        result['igst'] = result.apply(
            lambda r: calc_tax(r.get('pos'), r.get('taxable_value', 0))[0], axis=1
        )
    
    # Apply CGST
    if cgst_col and cgst_col in df.columns:
        result['cgst'] = df[cgst_col].apply(safe_num)
    else:
        result['cgst'] = result.apply(
            lambda r: calc_tax(r.get('pos'), r.get('taxable_value', 0))[1], axis=1
        )
    
    # Apply SGST
    if sgst_col and sgst_col in df.columns:
        result['sgst'] = df[sgst_col].apply(safe_num)
    else:
        result['sgst'] = result.apply(
            lambda r: calc_tax(r.get('pos'), r.get('taxable_value', 0))[2], axis=1
        )
    
    return result


def read_excel_all_sheets(file_path: str) -> Optional[pd.DataFrame]:
    """Read all sheets from Excel, skip dashboard sheets, concatenate."""
    skip_sheets = ['summary', 'pivot', 'total', 'dashboard', 'overview', 'summary report']
    try:
        xl_file = pd.ExcelFile(file_path)
        dfs = []
        for sheet_name in xl_file.sheet_names:
            if sheet_name.lower() in [s.lower() for s in skip_sheets]:
                logger.debug(f"Skipping sheet: {sheet_name}")
                continue
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                if df is not None and not df.empty:
                    dfs.append(df)
            except Exception as e:
                logger.warning(f"Error reading sheet {sheet_name}: {e}")
        return pd.concat(dfs, ignore_index=True) if dfs else None
    except Exception as e:
        logger.error(f"Error reading Excel: {e}")
        return None

# =====================================================
# BASE PARSER - SHARED LOGIC FOR ALL PLATFORMS
# =====================================================

class BaseParser:
    """Base class with shared parsing logic for all platform parsers."""
    
    ETIN = None
    PLATFORM = None
    STATE_PATTERNS = ['state', 'delivery', 'place']
    TAXABLE_PATTERNS = ['taxable', 'sale', 'value', 'amount']
    
    def read_files(self, files: List[str]) -> List[Tuple[pd.DataFrame, str]]:
        """Read files matching platform name, handle CSV/Excel with encoding fallback."""
        dfs = []
        platform_lower = (self.PLATFORM or 'unknown').lower()
        
        for file in files:
            if platform_lower not in Path(file).name.lower():
                continue
            
            try:
                if file.lower().endswith('.csv'):
                    # Try UTF-8 first, then latin1
                    try:
                        df = pd.read_csv(file, encoding='utf-8')
                    except UnicodeDecodeError:
                        df = pd.read_csv(file, encoding='latin1')
                else:
                    df = read_excel_all_sheets(file)
                
                if df is not None and not df.empty:
                    dfs.append((df, file))
                    logger.info(f"Read {file}: {len(df)} rows")
            except Exception as e:
                logger.error(f"Read error {file}: {str(e)[:60]}")
        
        return dfs
    
    def process_rows(self, file_dfs: List[Tuple[pd.DataFrame, str]]) -> Optional[List[pd.DataFrame]]:
        """Process rows from file dataframes."""
        all_rows = []
        row_counter = 0
        
        for df, file_path in file_dfs:
            is_return = is_return_file(file_path)
            logger.info(f"Processing {Path(file_path).name} (return={is_return})")
            
            df = clean_cols(df)
            cols = df.columns.tolist()
            
            # Find key columns
            state_col = find_col(cols, self.STATE_PATTERNS)
            taxable_col = find_col(cols, self.TAXABLE_PATTERNS)
            
            if not state_col or not taxable_col:
                logger.warning(f"Missing state_col={state_col} or taxable_col={taxable_col}")
                continue
            
            # Get invoice column (first column or invoice_no)
            invoice_col = find_col(cols, ['invoice', 'order']) or cols[0]
            
            # Build base row data
            row_data = pd.DataFrame({
                'platform': self.PLATFORM,
                'pos': df[state_col].apply(get_state_code),
                'taxable_value': df[taxable_col].apply(safe_num),
                'invoice_no': df[invoice_col].astype(str),
                'txn_type': 'return' if is_return else 'sale'
            })
            
            # Apply tax columns
            result_df = apply_tax_columns(df, row_data, state_col, taxable_col)
            result_df['row_id'] = range(row_counter, row_counter + len(result_df))
            row_counter += len(result_df)
            
            # Negate return values
            if is_return:
                for col in ['taxable_value', 'igst', 'cgst', 'sgst']:
                    result_df[col] = result_df[col].apply(lambda x: -abs(x) if x != 0 else 0)
            
            # Filter valid rows
            valid = result_df[
                (result_df['pos'].notna()) &
                (
                    (result_df['taxable_value'] != 0) |
                    (result_df['igst'] != 0) |
                    (result_df['cgst'] != 0) |
                    (result_df['sgst'] != 0)
                )
            ].copy()
            
            if not valid.empty:
                all_rows.append(valid)
                logger.info(f"  ✓ {len(valid)} valid rows")
            else:
                logger.warning(f"  ✗ No valid rows")
        
        return all_rows if all_rows else None
    
    def finalize_output(self, all_rows: List[pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """Deduplicate, finalize, and generate output."""
        if not all_rows:
            return None
        
        # Combine all rows
        final = pd.concat(all_rows, ignore_index=True)
        logger.info(f"Combined {len(final)} rows before dedup")
        
        # Clean invoice numbers with fallback to row_id
        final['invoice_no'] = final.apply(
            lambda row: clean_invoice_no(row['invoice_no']) or
                       f"{self.PLATFORM.upper()}_{row['pos']}_{row['row_id']}",
            axis=1
        )
        
        # Strong deduplication
        final = final.drop_duplicates(
            subset=['platform', 'pos', 'invoice_no', 'taxable_value', 'txn_type']
        ).reset_index(drop=True)
        logger.info(f"After dedup: {len(final)} rows")
        
        # Separate sales and returns
        sales_df = final[final['txn_type'] == 'sale'].copy()
        returns_df = final[final['txn_type'] == 'return'].copy()
        
        # Aggregate by POS
        summary_rows = []
        if not sales_df.empty:
            grouped = sales_df.groupby('pos', as_index=False).agg({
                'taxable_value': 'sum',
                'igst': 'sum',
                'cgst': 'sum',
                'sgst': 'sum'
            }).round(2)
            summary_rows = grouped.to_dict('records')
        
        # Build credit docs from returns
        credit_docs = []
        if not returns_df.empty:
            for _, row in returns_df.iterrows():
                credit_docs.append({
                    'invoice_no': row['invoice_no'],
                    'pos': row['pos'],
                    'txval': abs(row['taxable_value']),
                    'igst_amt': abs(row['igst']),
                    'cgst_amt': abs(row['cgst']),
                    'sgst_amt': abs(row['sgst'])
                })
        
        # Calculate totals
        total_taxable = sum(r['taxable_value'] for r in summary_rows)
        total_igst = sum(r['igst'] for r in summary_rows)
        total_cgst = sum(r['cgst'] for r in summary_rows)
        total_sgst = sum(r['sgst'] for r in summary_rows)
        
        return {
            "platform": self.PLATFORM,
            "etin": self.ETIN,
            "summary": {
                "rows": summary_rows,
                "total_taxable": round(total_taxable, 2),
                "total_igst": round(total_igst, 2),
                "total_cgst": round(total_cgst, 2),
                "total_sgst": round(total_sgst, 2)
            },
            "invoice_docs": [],
            "credit_docs": credit_docs,
            "debit_docs": []
        }
    
    def parse_files(self, files: List[str]) -> Optional[Dict[str, Any]]:
        """Main orchestration method."""
        logger.info(f"\n🔍 Parsing {self.PLATFORM}")
        file_dfs = self.read_files(files)
        if not file_dfs:
            logger.warning(f"No files found for {self.PLATFORM}")
            return None
        
        all_rows = self.process_rows(file_dfs)
        if not all_rows:
            logger.warning(f"No data extracted from {self.PLATFORM}")
            return None
        
        result = self.finalize_output(all_rows)
        if result:
            logger.info(f"✓ {self.PLATFORM} complete")
        return result


# =====================================================
# PLATFORM-SPECIFIC PARSERS
# =====================================================

class MeeshoParser(BaseParser):
    """Parser for Meesho sales exports."""
    ETIN = "07AARCM9332R1CQ"
    PLATFORM = "Meesho"
    STATE_PATTERNS = ['state', 'delivery', 'place', 'destination']
    TAXABLE_PATTERNS = ['taxable', 'sale_value', 'value', 'amount']


class FlipkartParser(BaseParser):
    """Parser for Flipkart sales exports."""
    ETIN = "07AACCF0683K1CU"
    PLATFORM = "Flipkart"
    STATE_PATTERNS = ['state', 'delivery', 'place', 'destination']
    TAXABLE_PATTERNS = ['taxable', 'sale_value', 'value']


class AmazonParser(BaseParser):
    """Parser for Amazon sales exports."""
    ETIN = "07AAICA3918J1CV"
    PLATFORM = "Amazon"
    STATE_PATTERNS = ['state', 'ship_state', 'place']
    TAXABLE_PATTERNS = ['tax_exclusive', 'taxable', 'gross']


# =====================================================
# AUTO MERGE PARSER - MULTI-PLATFORM CONSOLIDATION
# =====================================================

class AutoMergeParser:
    """
    Consolidates results from all platform parsers.
    - Meesho, Flipkart, Amazon
    - Merges by state (pos)
    - Aggregates taxes correctly
    - Maintains CLTTX supplier details
    - Consolidates credit_docs for returns
    """
    
    def parse_files(self, files: List[str]) -> Dict[str, Any]:
        """Parse all platforms and merge results."""
        parsers = [MeeshoParser(), FlipkartParser(), AmazonParser()]
        results = []
        
        logger.info("🚀 PARSING FILES FOR ALL PLATFORMS")
        for file in files:
            logger.info(f"  📄 {Path(file).name}")
        
        # Execute all parsers
        for parser in parsers:
            try:
                result = parser.parse_files(files)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Parser {parser.PLATFORM} failed: {str(e)[:60]}")
        
        # If no results, return empty structure
        if not results:
            logger.warning("❌ No data found from any parser")
            return {
                "summary": {
                    "rows": [],
                    "total_taxable": 0.0,
                    "total_igst": 0.0,
                    "total_cgst": 0.0,
                    "total_sgst": 0.0
                },
                "invoice_docs": [],
                "credit_docs": [],
                "debit_docs": [],
                "clttx": []
            }
        
        # MERGE: Aggregate all state totals across all parsers
        state_totals = defaultdict(lambda: {
            'taxable_value': 0.0,
            'igst': 0.0,
            'cgst': 0.0,
            'sgst': 0.0
        })
        clttx = []
        all_credit_docs = []
        
        for result in results:
            # Merge per-state totals
            for row in result['summary']['rows']:
                pos = str(row['pos'])
                state_totals[pos]['taxable_value'] += row['taxable_value']
                state_totals[pos]['igst'] += row['igst']
                state_totals[pos]['cgst'] += row['cgst']
                state_totals[pos]['sgst'] += row['sgst']
            
            # Create supplier entry (CLTTX)
            clttx.append({
                'etin': result['etin'],
                'suppval': result['summary']['total_taxable'],
                'igst': result['summary']['total_igst'],
                'cgst': result['summary']['total_cgst'],
                'sgst': result['summary']['total_sgst'],
                'cess': 0.0,
                'flag': 'N'
            })
            
            # Collect credit docs (returns)
            if result['credit_docs']:
                all_credit_docs.extend(result['credit_docs'])
        
        # Convert state_totals back to list
        rows = []
        for pos, amounts in state_totals.items():
            rows.append({
                'pos': str(pos),
                'taxable_value': round(amounts['taxable_value'], 2),
                'igst': round(amounts['igst'], 2),
                'cgst': round(amounts['cgst'], 2),
                'sgst': round(amounts['sgst'], 2)
            })
        
        # Calculate grand totals
        grand_total_taxable = sum(r['taxable_value'] for r in rows)
        grand_total_igst = sum(r['igst'] for r in rows)
        grand_total_cgst = sum(r['cgst'] for r in rows)
        grand_total_sgst = sum(r['sgst'] for r in rows)
        
        logger.info(f"✓ Merged {len(results)} platforms, {len(rows)} states")
        
        return {
            "summary": {
                "rows": rows,
                "total_taxable": round(grand_total_taxable, 2),
                "total_igst": round(grand_total_igst, 2),
                "total_cgst": round(grand_total_cgst, 2),
                "total_sgst": round(grand_total_sgst, 2)
            },
            "invoice_docs": [],
            "credit_docs": all_credit_docs,
            "debit_docs": [],
            "clttx": clttx
        }