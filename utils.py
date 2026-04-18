# utils.py
# PRODUCTION-GRADE UTILITY FUNCTIONS FOR GST PARSING
# Focus: Data accuracy, precision, and detailed logging

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from datetime import datetime

try:
    from logger import get_logger
    logger = get_logger()
except ImportError:
    # Fallback if logger not available
    import logging
    logger = logging.getLogger(__name__)

# =====================================================
# BASIC CONVERSIONS
# =====================================================

def safe_num(val: Any, default: float = 0.0) -> float:
    """Convert value to float safely, handle commas/spaces/None."""
    try:
        if pd.isna(val):
            return default
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).strip().replace(',', '').replace(' ', '')
        return float(val_str) if val_str else default
    except (ValueError, TypeError):
        return default


def safe_str(val: Any, default: str = "") -> str:
    """Convert value to string safely."""
    if pd.isna(val):
        return default
    val_str = str(val).strip()
    return val_str if val_str else default


def safe_int(val: Any, default: int = 0) -> int:
    """Convert value to integer safely."""
    try:
        if pd.isna(val):
            return default
        return int(safe_num(val))
    except (ValueError, TypeError):
        return default


# Backward compatibility
num = safe_num
clean_text = safe_str

# =====================================================
# COLUMN DETECTION & CLEANING
# =====================================================

def clean_col_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize DataFrame column names."""
    df = df.copy()
    df.columns = [
        str(c).lower().strip()
        .replace(' ', '_')
        .replace('-', '_')
        .replace('/', '_')
        .replace('(', '')
        .replace(')', '')
        .replace(',', '')
        [:50]  # Limit length
        for c in df.columns
    ]
    return df


# Backward compatibility
def clean_cols(df):
    """Backward compatible clean_cols."""
    return clean_col_names(df)


def find_column(df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
    """Find first column matching any pattern (case-insensitive)."""
    cols = [str(c).lower() for c in df.columns]
    for pattern in patterns:
        pattern_lower = pattern.lower()
        for col in cols:
            if pattern_lower in col:
                return col
    return None


def find_columns(df: pd.DataFrame, patterns: List[str]) -> List[str]:
    """Find all columns matching any pattern."""
    cols = [str(c).lower() for c in df.columns]
    found = []
    for pattern in patterns:
        pattern_lower = pattern.lower()
        for col in cols:
            if pattern_lower in col and col not in found:
                found.append(col)
    return found


def first_match(columns, keywords):
    """Backward compatible first_match."""
    for key in keywords:
        for col in columns:
            if key in str(col).lower():
                return col
    return None


def detect_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """Detect key columns needed for GST parsing."""
    result = {
        'state': find_column(df, ['state', 'delivery_state', 'ship_state', 'destination_state', 'place']),
        'amount': find_column(df, ['amount', 'order_value', 'sale_amount', 'revenue', 'gross']),
        'taxable': find_column(df, ['taxable', 'taxable_value', 'tax_exclusive', 'net_sale']),
        'igst': find_column(df, ['igst', 'i_gst', 'integrated_tax']),
        'cgst': find_column(df, ['cgst', 'c_gst', 'central_tax']),
        'sgst': find_column(df, ['sgst', 's_gst', 'state_tax', 'utgst']),
        'invoice': find_column(df, ['invoice', 'order_id', 'invoice_no', 'invoice_number', 'reference_no']),
        'date': find_column(df, ['date', 'invoice_date', 'order_date', 'transaction_date']),
    }
    return {k: v for k, v in result.items() if v}


def detect_tax_columns(columns):
    """Backward compatible detect_tax_columns."""
    return {
        "igst": first_match(columns, ["igst"]),
        "cgst": first_match(columns, ["cgst"]),
        "sgst": first_match(columns, ["sgst", "utgst"]),
        "tax": first_match(columns, ["tax_amount", "tax"]),
    }


# =====================================================
# GST STATE MAPPING
# =====================================================

STATE_CODES = {
    # Union Territories
    'andaman': '35', 'andaman and nicobar': '35', 'andaman nicobar': '35',
    'chandigarh': '04', 'ch': '04',
    'dadra and nagar haveli': '26', 'dadra': '26', 'dnh': '26',
    'daman and diu': '25', 'daman': '25', 'dd': '25',
    'delhi': '07', 'new delhi': '07', 'delhi nct': '07', 'nct': '07',
    'ladakh': '38', 'ld': '38',
    'lakshadweep': '31', 'lk': '31',
    'puducherry': '34', 'pondicherry': '34', 'py': '34',
    
    # States
    'andhra pradesh': '37', 'andhra': '37', 'ap': '37',
    'arunachal pradesh': '12', 'arunachal': '12', 'ar': '12',
    'assam': '18', 'as': '18',
    'bihar': '10', 'br': '10',
    'chhattisgarh': '22', 'cg': '22',
    'goa': '30', 'ga': '30',
    'gujarat': '24', 'gj': '24',
    'haryana': '06', 'hr': '06', 'gurgaon': '06', 'gurugram': '06',
    'himachal pradesh': '02', 'hp': '02', 'himachal': '02',
    'jharkhand': '20', 'jh': '20',
    'karnataka': '29', 'kn': '29', 'bangalore': '29', 'bengaluru': '29', 'ka': '29',
    'kerala': '32', 'kl': '32',
    'madhya pradesh': '23', 'mp': '23', 'madhya': '23',
    'maharashtra': '27', 'mh': '27', 'mumbai': '27', 'pune': '27',
    'manipur': '14', 'mn': '14',
    'meghalaya': '17', 'ml': '17',
    'mizoram': '15', 'mz': '15',
    'nagaland': '13', 'nl': '13',
    'odisha': '21', 'or': '21', 'orissa': '21',
    'punjab': '03', 'pb': '03',
    'rajasthan': '08', 'rj': '08',
    'sikkim': '11', 'sk': '11',
    'tamil nadu': '33', 'tn': '33', 'tamil': '33', 'chennai': '33',
    'telangana': '36', 'tg': '36', 'ts': '36', 'hyderabad': '36',
    'tripura': '16', 'tr': '16',
    'uttar pradesh': '09', 'up': '09', 'u.p': '09', 'noida': '09', 'ghaziabad': '09',
    'uttarakhand': '05', 'uk': '05', 'ut': '05',
    'west bengal': '19', 'wb': '19', 'west': '19',
}


def get_state_code(state: Any) -> Optional[str]:
    """Map state name to GST state code (2-digit)."""
    if pd.isna(state):
        return None
    
    state_str = safe_str(state).lower().strip()
    if not state_str:
        return None
    
    # Check if already a 2-digit code
    if state_str.isdigit() and len(state_str) == 2:
        return state_str if 1 <= int(state_str) <= 38 else None
    
    # Direct lookup
    if state_str in STATE_CODES:
        return STATE_CODES[state_str]
    
    # Partial word match
    for key, code in STATE_CODES.items():
        if state_str in key or key in state_str:
            return code
    
    return None


# Backward compatibility
def state_to_code(v):
    """Backward compatible state_to_code."""
    return get_state_code(v)


# =====================================================
# GST CALCULATIONS
# =====================================================

def calculate_tax(pos: str, taxable: float) -> Tuple[float, float, float]:
    """
    Calculate IGST/CGST/SGST based on place of supply (pos).
    - Delhi (pos='07'): CGST + SGST split (1.5% each = 3%)
    - Other states: IGST only (3%)
    
    Returns: (igst, cgst, sgst)
    """
    taxable = safe_num(taxable)
    pos = safe_str(pos).strip()
    
    if pos == '07':
        # Delhi: Split into CGST + SGST
        cgst = round(taxable * 0.015, 2)
        sgst = round(taxable * 0.015, 2)
        return 0.0, cgst, sgst
    else:
        # Other states: IGST
        igst = round(taxable * 0.03, 2)
        return igst, 0.0, 0.0


def calculate_tax_from_taxable(pos_series, taxable_series):
    """Backward compatible calculate_tax_from_taxable."""
    taxable = num(taxable_series)
    is_delhi = pos_series == "07"

    igst = (taxable * 0.03).where(~is_delhi, 0).round(2)
    cgst = (taxable * 0.015).where(is_delhi, 0).round(2)
    sgst = (taxable * 0.015).where(is_delhi, 0).round(2)

    return igst, cgst, sgst


def apply_tax_columns(
    df: pd.DataFrame,
    state_col: Optional[str],
    taxable_col: Optional[str],
    igst_col: Optional[str] = None,
    cgst_col: Optional[str] = None,
    sgst_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Apply tax columns with intelligent fallback.
    - Use individual columns if present
    - Calculate from taxable if not present
    """
    result = pd.DataFrame()
    
    # Get POS (state codes)
    if state_col and state_col in df.columns:
        result['pos'] = df[state_col].apply(get_state_code)
    else:
        result['pos'] = None
    
    # Get taxable value
    if taxable_col and taxable_col in df.columns:
        result['taxable_value'] = df[taxable_col].apply(safe_num)
    else:
        result['taxable_value'] = 0.0
    
    # Apply tax columns
    if igst_col and igst_col in df.columns:
        result['igst'] = df[igst_col].apply(safe_num)
    elif cgst_col and cgst_col in df.columns:
        result['igst'] = 0.0
    else:
        result['igst'] = result.apply(
            lambda r: calculate_tax(r['pos'], r['taxable_value'])[0], axis=1
        )
    
    if cgst_col and cgst_col in df.columns:
        result['cgst'] = df[cgst_col].apply(safe_num)
    elif igst_col and igst_col in df.columns:
        result['cgst'] = 0.0
    else:
        result['cgst'] = result.apply(
            lambda r: calculate_tax(r['pos'], r['taxable_value'])[1], axis=1
        )
    
    if sgst_col and sgst_col in df.columns:
        result['sgst'] = df[sgst_col].apply(safe_num)
    elif igst_col and igst_col in df.columns:
        result['sgst'] = 0.0
    else:
        result['sgst'] = result.apply(
            lambda r: calculate_tax(r['pos'], r['taxable_value'])[2], axis=1
        )
    
    return result


# =====================================================
# DOCUMENT HANDLING
# =====================================================

def clean_invoice_no(val: Any, fallback: str = "") -> str:
    """Clean invoice number, handle blank/nan/None."""
    if pd.isna(val):
        return fallback
    
    val_str = safe_str(val)
    if not val_str or val_str.upper() in ['NAN', 'NONE', '']:
        return fallback
    
    return val_str


def safe_docs(series):
    """Backward compatible safe_docs."""
    vals = (
        series.dropna()
        .astype(str)
        .str.strip()
    )
    vals = vals[vals != ""].unique().tolist()
    vals = sorted(vals)

    if not vals:
        return []

    return [{
        "from": vals[0],
        "to": vals[-1],
        "totnum": len(vals)
    }]


# =====================================================
# DEDUPLICATION & FILTERING
# =====================================================

def dedupe(df):
    """Backward compatible dedupe."""
    keys = [c for c in ["platform", "invoice_no", "order_id", "txn_type"] if c in df.columns]
    if keys:
        return df.drop_duplicates(subset=keys, keep="first")
    return df


def deduplicate_rows(
    df: pd.DataFrame,
    key_cols: List[str] = None
) -> pd.DataFrame:
    """Remove duplicate rows based on key columns."""
    if df.empty:
        return df
    
    if key_cols is None:
        key_cols = ['platform', 'pos', 'invoice_no', 'taxable_value']
    
    available_keys = [col for col in key_cols if col in df.columns]
    if not available_keys:
        return df
    
    return df.drop_duplicates(subset=available_keys, keep='first').reset_index(drop=True)


def filter_valid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Filter rows with valid data (pos not null and has non-zero value)."""
    if df.empty:
        return df
    
    # Must have POS
    valid = df[df['pos'].notna()].copy()
    
    # Must have at least one non-zero financial value
    valid = valid[
        (valid['taxable_value'] != 0) |
        (valid.get('igst', 0) != 0) |
        (valid.get('cgst', 0) != 0) |
        (valid.get('sgst', 0) != 0)
    ]
    
    return valid


# =====================================================
# SUMMARIZATION
# =====================================================

def summarize(df):
    """Backward compatible summarize."""
    if df.empty:
        return {
            "rows": [],
            "total_taxable": 0,
            "total_igst": 0,
            "total_cgst": 0,
            "total_sgst": 0
        }

    df = df[df["pos"].notna()].copy()

    g = (
        df.groupby("pos", as_index=False)[
            ["taxable_value", "igst", "cgst", "sgst"]
        ]
        .sum()
        .round(2)
    )

    return {
        "rows": g.to_dict("records"),
        "total_taxable": float(g["taxable_value"].sum()),
        "total_igst": float(g["igst"].sum()),
        "total_cgst": float(g["cgst"].sum()),
        "total_sgst": float(g["sgst"].sum())
    }


def summarize_by_state(df: pd.DataFrame) -> Dict[str, Any]:
    """Group and summarize data by state (POS)."""
    if df.empty:
        return {
            'rows': [],
            'total_taxable': 0.0,
            'total_igst': 0.0,
            'total_cgst': 0.0,
            'total_sgst': 0.0,
        }
    
    # Group by POS
    grouped = df.groupby('pos', as_index=False).agg({
        'taxable_value': 'sum',
        'igst': 'sum',
        'cgst': 'sum',
        'sgst': 'sum',
    }).round(2)
    
    rows = grouped.to_dict('records')
    
    return {
        'rows': rows,
        'total_taxable': float(grouped['taxable_value'].sum()),
        'total_igst': float(grouped['igst'].sum()),
        'total_cgst': float(grouped['cgst'].sum()),
        'total_sgst': float(grouped['sgst'].sum()),
    }


def summarize_return_docs(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert return rows to credit document format."""
    if df.empty:
        return []
    
    credit_docs = []
    for _, row in df.iterrows():
        credit_docs.append({
            'invoice_no': row.get('invoice_no', ''),
            'pos': row.get('pos', ''),
            'txval': abs(row.get('taxable_value', 0)),
            'igst_amt': abs(row.get('igst', 0)),
            'cgst_amt': abs(row.get('cgst', 0)),
            'sgst_amt': abs(row.get('sgst', 0)),
        })
    
    return credit_docs


# =====================================================
# FILE OPERATIONS
# =====================================================

def read_excel_sheets(file_path: str, skip_sheets: List[str] = None) -> Optional[pd.DataFrame]:
    """Read all sheets from Excel, skip dashboard sheets, concatenate."""
    if skip_sheets is None:
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
                    df['_source_sheet'] = sheet_name
                    dfs.append(df)
            except Exception as e:
                logger.warning(f"Error reading sheet {sheet_name}: {e}")
        
        if dfs:
            return pd.concat(dfs, ignore_index=True)
    except Exception as e:
        logger.error(f"Error reading Excel file {file_path}: {e}")
    
    return None


def read_csv_file(file_path: str) -> Optional[pd.DataFrame]:
    """Read CSV file with encoding fallback."""
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            if df is not None and not df.empty:
                return df
        except Exception as e:
            logger.debug(f"Failed to read with {encoding}: {e}")
    
    logger.error(f"Could not read CSV file {file_path} with any encoding")
    return None


def read_file(file_path: str) -> Optional[pd.DataFrame]:
    """Read Excel or CSV file."""
    path = Path(file_path)
    
    if path.suffix.lower() in ['.xlsx', '.xls']:
        return read_excel_sheets(file_path)
    elif path.suffix.lower() == '.csv':
        return read_csv_file(file_path)
    else:
        logger.error(f"Unsupported file type: {path.suffix}")
        return None
