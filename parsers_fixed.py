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
import re
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
            if col_matches_pattern(col, pattern):
                return col
    return None


def normalize_identifier(value: Any) -> str:
    """Normalize an identifier for safer matching."""
    return re.sub(r'[^a-z0-9]+', '_', str(value).lower()).strip('_')


def col_matches_pattern(col: str, pattern: str) -> bool:
    """Match a pattern against a column using token-aware rules."""
    normalized_col = normalize_identifier(col)
    normalized_pattern = normalize_identifier(pattern)

    if not normalized_col or not normalized_pattern:
        return False

    if normalized_col == normalized_pattern:
        return True

    tokens = normalized_col.split('_')
    if normalized_pattern in tokens:
        return True

    if normalized_col.startswith(normalized_pattern + '_'):
        return True

    if normalized_col.endswith('_' + normalized_pattern):
        return True

    if f"_{normalized_pattern}_" in normalized_col:
        return True

    # Allow substring matching only for longer, less ambiguous patterns.
    if len(normalized_pattern) >= 5 and normalized_pattern in normalized_col:
        return True

    return False


def clean_invoice_no(invoice_no: Any) -> Optional[str]:
    """Clean invoice number - handles NaN, None, empty strings."""
    if pd.isna(invoice_no) or invoice_no is None:
        return None
    val_str = str(invoice_no).strip()
    if val_str and val_str.upper() not in ['NAN', 'NONE', '']:
        return val_str
    return None


def extract_state_code_from_gstin(gstin: Optional[str]) -> Optional[str]:
    """Extract seller state code from GSTIN-like value."""
    if not gstin:
        return None
    gstin_str = str(gstin).strip().upper()
    if len(gstin_str) >= 2 and gstin_str[:2].isdigit():
        state_code = gstin_str[:2]
        if 1 <= int(state_code) <= 38:
            return state_code
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


def is_intra_supply(pos: Optional[str], seller_state_code: Optional[str]) -> bool:
    """Determine whether a transaction is intra-state for the seller."""
    if not pos or not seller_state_code:
        return False
    return str(pos).zfill(2) == str(seller_state_code).zfill(2)


def calc_tax(pos: str, taxable: float, seller_state_code: Optional[str] = None) -> Tuple[float, float, float]:
    """Calculate IGST/CGST/SGST using seller state and place of supply."""
    taxable = safe_num(taxable)
    pos = str(pos).strip() if pos else ''
    
    if is_intra_supply(pos, seller_state_code):
        return 0.0, round(taxable * 0.015, 2), round(taxable * 0.015, 2)

    return round(taxable * 0.03, 2), 0.0, 0.0


def split_tax_amount(pos: Optional[str], tax_amount: Any, seller_state_code: Optional[str]) -> Tuple[float, float, float]:
    """Split a generic tax amount into IGST or CGST/SGST based on supply type."""
    amount = safe_num(tax_amount)
    if amount == 0:
        return 0.0, 0.0, 0.0
    if is_intra_supply(pos, seller_state_code):
        half = round(amount / 2, 2)
        return 0.0, half, amount - half
    return amount, 0.0, 0.0


def build_doc_issue_details(invoice_docs: List[Dict[str, Any]], credit_docs: List[Dict[str, Any]], debit_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build document issue ranges from invoice-style documents."""
    def normalize_doc_value(value: Any) -> Optional[str]:
        return clean_invoice_no(value)

    def natural_key(value: str) -> List[Any]:
        return [f"{int(token):012d}" if token.isdigit() else token.lower() for token in re.findall(r'\d+|\D+', value)]

    def doc_parts(value: str) -> Tuple[str, Optional[int]]:
        match = re.match(r'^(.*?)(\d+)$', value)
        if not match:
            return value, None
        return match.group(1), int(match.group(2))

    def make_ranges(values: List[str]) -> List[Dict[str, Any]]:
        if not values:
            return []

        sorted_values = sorted(set(values), key=natural_key)
        ranges = []
        current_group = [sorted_values[0]]

        for value in sorted_values[1:]:
            prev = current_group[-1]
            prev_prefix, prev_number = doc_parts(prev)
            prefix, number = doc_parts(value)

            is_contiguous = (
                prev_prefix == prefix and
                prev_number is not None and
                number is not None and
                number == prev_number + 1
            )

            if is_contiguous:
                current_group.append(value)
            else:
                ranges.append({
                    "from": current_group[0],
                    "to": current_group[-1],
                    "totnum": len(current_group),
                    "cancel": 0,
                    "net_issue": len(current_group)
                })
                current_group = [value]

        ranges.append({
            "from": current_group[0],
            "to": current_group[-1],
            "totnum": len(current_group),
            "cancel": 0,
            "net_issue": len(current_group)
        })
        return ranges

    def make_bucket(doc_num: int, doc_typ: str, docs: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        invoice_numbers = [
            normalize_doc_value(doc.get('invoice_no'))
            for doc in docs
            if normalize_doc_value(doc.get('invoice_no'))
        ]
        ranges = make_ranges(invoice_numbers)
        if not ranges:
            return None
        return {
            "doc_num": doc_num,
            "doc_typ": doc_typ,
            "docs": ranges
        }

    doc_det = []
    for doc_num, label, docs in [
        (1, "Invoices for outward supply", invoice_docs),
        (5, "Credit Note", credit_docs),
        (6, "Debit Note", debit_docs),
    ]:
        bucket = make_bucket(doc_num, label, docs)
        if bucket:
            doc_det.append(bucket)

    return {"doc_det": doc_det}


def make_preparsed_df(records: List[Dict[str, Any]], platform: str) -> pd.DataFrame:
    """Create a normalized dataframe ready for finalize_output()."""
    base_columns = ['platform', 'pos', 'taxable_value', 'invoice_no', 'txn_type', 'igst', 'cgst', 'sgst']
    if not records:
        return pd.DataFrame(columns=base_columns + ['source_key'])

    df = pd.DataFrame(records).copy()
    if 'platform' not in df.columns:
        df['platform'] = platform
    if 'txn_type' not in df.columns:
        df['txn_type'] = 'sale'
    if 'source_key' not in df.columns:
        df['source_key'] = None
    for column in ['taxable_value', 'igst', 'cgst', 'sgst']:
        if column not in df.columns:
            df[column] = 0.0
        df[column] = df[column].apply(safe_num)
    df['invoice_no'] = df['invoice_no'].astype(str)
    df['pos'] = df['pos'].apply(lambda value: str(value).zfill(2) if safe_num(value) or str(value).strip() else value)
    extra_columns = [column for column in df.columns if column not in base_columns]
    return df[base_columns + extra_columns]


def has_financial_values(record: Dict[str, Any]) -> bool:
    """Return True when any taxable or tax amount is non-zero."""
    return any(
        safe_num(record.get(column)) != 0
        for column in ['taxable_value', 'igst', 'cgst', 'sgst']
    )


def apply_tax_columns(
    df: pd.DataFrame,
    base_data: pd.DataFrame,
    state_col: str,
    taxable_col: str,
    seller_state_code: Optional[str] = None
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
    sgst_col = find_col(df.columns.tolist(), ['sgst', 's_gst', 'state_tax'])
    
    # Apply IGST
    if igst_col and igst_col in df.columns:
        result['igst'] = df[igst_col].apply(safe_num)
    else:
        result['igst'] = result.apply(
            lambda r: calc_tax(r.get('pos'), r.get('taxable_value', 0), seller_state_code)[0], axis=1
        )
    
    # Apply CGST
    if cgst_col and cgst_col in df.columns:
        result['cgst'] = df[cgst_col].apply(safe_num)
    else:
        result['cgst'] = result.apply(
            lambda r: calc_tax(r.get('pos'), r.get('taxable_value', 0), seller_state_code)[1], axis=1
        )
    
    # Apply SGST
    if sgst_col and sgst_col in df.columns:
        result['sgst'] = df[sgst_col].apply(safe_num)
    else:
        result['sgst'] = result.apply(
            lambda r: calc_tax(r.get('pos'), r.get('taxable_value', 0), seller_state_code)[2], axis=1
        )
    
    return result


class OfficialTemplateAdapter:
    """Base adapter for official marketplace export templates."""

    NAME = "Generic"
    FILENAME_HINTS: List[str] = []
    REQUIRED_COLUMNS: List[str] = []

    def matches(self, df: pd.DataFrame, file_path: str) -> bool:
        filename = Path(file_path).name.lower()
        cleaned = clean_cols(df)
        normalized_cols = {normalize_identifier(col) for col in cleaned.columns.tolist()}

        if self.FILENAME_HINTS and any(hint in filename for hint in self.FILENAME_HINTS):
            return True

        required = {normalize_identifier(col) for col in self.REQUIRED_COLUMNS}
        return bool(required) and required.issubset(normalized_cols)

    def normalize(self, df: pd.DataFrame, file_path: str, seller_state_code: Optional[str]) -> pd.DataFrame:
        raise NotImplementedError

    def _normalize_common(
        self,
        df: pd.DataFrame,
        *,
        seller_state_code: Optional[str],
        invoice_patterns: List[str],
        state_patterns: List[str],
        taxable_patterns: List[str],
        igst_patterns: Optional[List[str]] = None,
        cgst_patterns: Optional[List[str]] = None,
        sgst_patterns: Optional[List[str]] = None,
        generic_tax_patterns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        cleaned = clean_cols(df)
        cols = cleaned.columns.tolist()

        invoice_col = find_col(cols, invoice_patterns) or cols[0]
        state_col = find_col(cols, state_patterns)
        taxable_col = find_col(cols, taxable_patterns)
        igst_col = find_col(cols, igst_patterns or [])
        cgst_col = find_col(cols, cgst_patterns or [])
        sgst_col = find_col(cols, sgst_patterns or [])
        generic_tax_col = find_col(cols, generic_tax_patterns or [])

        normalized = pd.DataFrame({
            'invoice_no': cleaned[invoice_col].astype(str),
            'state': cleaned[state_col] if state_col else None,
            'taxable_value': cleaned[taxable_col].apply(safe_num) if taxable_col else 0.0,
        })

        pos_series = normalized['state'].apply(get_state_code)
        if igst_col or cgst_col or sgst_col:
            normalized['igst'] = cleaned[igst_col].apply(safe_num) if igst_col else 0.0
            normalized['cgst'] = cleaned[cgst_col].apply(safe_num) if cgst_col else 0.0
            normalized['sgst'] = cleaned[sgst_col].apply(safe_num) if sgst_col else 0.0
        elif generic_tax_col:
            normalized['igst'] = [
                split_tax_amount(pos, tax, seller_state_code)[0]
                for pos, tax in zip(pos_series, cleaned[generic_tax_col])
            ]
            normalized['cgst'] = [
                split_tax_amount(pos, tax, seller_state_code)[1]
                for pos, tax in zip(pos_series, cleaned[generic_tax_col])
            ]
            normalized['sgst'] = [
                split_tax_amount(pos, tax, seller_state_code)[2]
                for pos, tax in zip(pos_series, cleaned[generic_tax_col])
            ]
        else:
            normalized['igst'] = [
                calc_tax(pos, taxable, seller_state_code)[0]
                for pos, taxable in zip(pos_series, normalized['taxable_value'])
            ]
            normalized['cgst'] = [
                calc_tax(pos, taxable, seller_state_code)[1]
                for pos, taxable in zip(pos_series, normalized['taxable_value'])
            ]
            normalized['sgst'] = [
                calc_tax(pos, taxable, seller_state_code)[2]
                for pos, taxable in zip(pos_series, normalized['taxable_value'])
            ]

        return normalized


class MeeshoOfficialAdapter(OfficialTemplateAdapter):
    NAME = "Meesho Official"
    FILENAME_HINTS = ['tcs_sales', 'tax_invoice_details', 'meesho']
    REQUIRED_COLUMNS = ['order_id', 'state', 'taxable_value']

    def normalize(self, df: pd.DataFrame, file_path: str, seller_state_code: Optional[str]) -> pd.DataFrame:
        return self._normalize_common(
            df,
            seller_state_code=seller_state_code,
            invoice_patterns=['invoice_no', 'invoice', 'order_id', 'sub_order_no'],
            state_patterns=['delivery_state', 'state', 'destination_state', 'place'],
            taxable_patterns=['taxable_value', 'taxable', 'net_sale', 'sale_value', 'value'],
            igst_patterns=['igst', 'integrated'],
            cgst_patterns=['cgst', 'central'],
            sgst_patterns=['sgst', 'utgst', 'state_tax'],
            generic_tax_patterns=['tax_amount', 'tax'],
        )


class FlipkartOfficialAdapter(OfficialTemplateAdapter):
    NAME = "Flipkart Official"
    FILENAME_HINTS = ['flipkart', 'fk_']
    REQUIRED_COLUMNS = ['invoice_no', 'delivery_state', 'sale_value']

    def normalize(self, df: pd.DataFrame, file_path: str, seller_state_code: Optional[str]) -> pd.DataFrame:
        return self._normalize_common(
            df,
            seller_state_code=seller_state_code,
            invoice_patterns=['invoice_no', 'invoice', 'order_id'],
            state_patterns=['delivery_state', 'state', 'destination_state', 'place'],
            taxable_patterns=['sale_value', 'taxable_value', 'taxable', 'net_sale', 'value'],
            igst_patterns=['igst', 'integrated'],
            cgst_patterns=['cgst', 'central'],
            sgst_patterns=['sgst', 'utgst', 'state_tax'],
            generic_tax_patterns=['tax_amount', 'tax'],
        )


class AmazonOfficialAdapter(OfficialTemplateAdapter):
    NAME = "Amazon Official"
    FILENAME_HINTS = ['amazon']
    REQUIRED_COLUMNS = ['order_id', 'ship_state', 'tax_exclusive']

    def normalize(self, df: pd.DataFrame, file_path: str, seller_state_code: Optional[str]) -> pd.DataFrame:
        return self._normalize_common(
            df,
            seller_state_code=seller_state_code,
            invoice_patterns=['invoice_no', 'invoice', 'order_id', 'shipment_id'],
            state_patterns=['ship_state', 'state', 'destination_state', 'place'],
            taxable_patterns=['tax_exclusive', 'taxable_value', 'taxable', 'gross', 'value'],
            igst_patterns=['igst', 'integrated'],
            cgst_patterns=['cgst', 'central'],
            sgst_patterns=['sgst', 'utgst', 'state_tax'],
            generic_tax_patterns=['tax_amount', 'tax'],
        )


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
    SIGNATURE_PATTERNS: List[str] = []
    TEMPLATE_ADAPTERS: List[OfficialTemplateAdapter] = []

    def __init__(self):
        self.seller_state_code = extract_state_code_from_gstin(self.ETIN)
        self.document_registry = {
            'invoice': [],
            'credit': [],
            'debit': [],
        }
        self.has_explicit_document_metadata = False

    def reset_document_registry(self) -> None:
        """Reset tracked invoice/credit/debit document numbers."""
        self.document_registry = {
            'invoice': [],
            'credit': [],
            'debit': [],
        }
        self.has_explicit_document_metadata = False

    def record_document_numbers(self, kind: str, values: List[Any]) -> None:
        """Store document identifiers for doc_issue generation."""
        if kind not in self.document_registry:
            return
        docs = [
            {'invoice_no': value}
            for value in values
            if clean_invoice_no(value)
        ]
        self.document_registry[kind].extend(docs)

    def resolve_seller_state_code(self, seller_gstin: Optional[str] = None) -> Optional[str]:
        """Resolve seller state using user GSTIN first, then parser ETIN."""
        return extract_state_code_from_gstin(seller_gstin) or extract_state_code_from_gstin(self.ETIN)

    def detect_template_adapter(self, df: pd.DataFrame, file_path: str) -> Optional[OfficialTemplateAdapter]:
        """Find a matching official export adapter for the current file."""
        for adapter in self.TEMPLATE_ADAPTERS:
            if adapter.matches(df, file_path):
                return adapter
        return None
    
    def file_matches_platform(self, df: pd.DataFrame, file_path: str) -> bool:
        """Detect whether a file belongs to the parser platform."""
        filename = Path(file_path).name.lower()
        platform_lower = (self.PLATFORM or 'unknown').lower()

        if platform_lower in filename:
            return True

        if self.detect_template_adapter(df, file_path):
            return True

        cleaned = clean_cols(df)
        normalized_cols = {normalize_identifier(col) for col in cleaned.columns.tolist()}
        matches = sum(
            1 for pattern in self.SIGNATURE_PATTERNS
            if normalize_identifier(pattern) in normalized_cols
        )
        return matches >= min(2, len(self.SIGNATURE_PATTERNS))

    def read_files(self, files: List[str]) -> List[Tuple[pd.DataFrame, str]]:
        """Read files for a platform, using filename and column signatures."""
        dfs = []
        
        for file in files:
            try:
                if file.lower().endswith('.csv'):
                    # Try UTF-8 first, then latin1
                    try:
                        df = pd.read_csv(file, encoding='utf-8')
                    except UnicodeDecodeError:
                        df = pd.read_csv(file, encoding='latin1')
                else:
                    df = read_excel_all_sheets(file)
                
                if df is not None and not df.empty and self.file_matches_platform(df, file):
                    adapter = self.detect_template_adapter(df, file)
                    if adapter:
                        df = adapter.normalize(df, file, self.seller_state_code)
                        logger.info(f"Adapted {file} using {adapter.NAME}")
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

            normalized_cols = {'platform', 'pos', 'taxable_value', 'invoice_no', 'txn_type', 'igst', 'cgst', 'sgst'}
            if normalized_cols.issubset(set(df.columns)):
                result_df = df.copy()
                result_df['row_id'] = range(row_counter, row_counter + len(result_df))
                row_counter += len(result_df)

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
                continue
            
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
            result_df = apply_tax_columns(
                df,
                row_data,
                state_col,
                taxable_col,
                self.seller_state_code
            )
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
        
        # Preserve repeated legitimate lines from official exports by preferring
        # per-row source keys when available.
        dedup_subset = ['platform', 'pos', 'invoice_no', 'taxable_value', 'igst', 'cgst', 'sgst', 'txn_type']
        if 'source_key' in final.columns and final['source_key'].notna().any():
            final = final.drop_duplicates(subset=['source_key']).reset_index(drop=True)
        else:
            final = final.drop_duplicates(subset=dedup_subset).reset_index(drop=True)
        logger.info(f"After dedup: {len(final)} rows")
        
        # Separate sales and returns
        sales_df = final[final['txn_type'] == 'sale'].copy()
        returns_df = final[final['txn_type'] == 'return'].copy()
        
        # Aggregate net by POS so returns reconcile against sales.
        summary_rows = []
        if not final.empty:
            grouped = final.groupby('pos', as_index=False).agg({
                'taxable_value': 'sum',
                'igst': 'sum',
                'cgst': 'sum',
                'sgst': 'sum'
            }).round(2)
            grouped = grouped[
                (grouped['taxable_value'] != 0) |
                (grouped['igst'] != 0) |
                (grouped['cgst'] != 0) |
                (grouped['sgst'] != 0)
            ].copy()
            summary_rows = grouped.to_dict('records')
        
        # Build credit docs from returns
        invoice_docs = []
        if not sales_df.empty:
            for _, row in sales_df.iterrows():
                invoice_docs.append({
                    'invoice_no': row['invoice_no'],
                    'pos': row['pos'],
                    'txval': round(row['taxable_value'], 2),
                    'igst_amt': round(row['igst'], 2),
                    'cgst_amt': round(row['cgst'], 2),
                    'sgst_amt': round(row['sgst'], 2)
                })

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

        summary_rows = sorted(summary_rows, key=lambda row: str(row['pos']))
        invoice_docs = sorted(invoice_docs, key=lambda row: (str(row['pos']), str(row['invoice_no'])))
        credit_docs = sorted(credit_docs, key=lambda row: (str(row['pos']), str(row['invoice_no'])))
        doc_issue = build_doc_issue_details(
            self.document_registry.get('invoice') or invoice_docs,
            self.document_registry.get('credit') or credit_docs,
            self.document_registry.get('debit', [])
        )
        
        return {
            "platform": self.PLATFORM,
            "etin": self.ETIN,
            "seller_state_code": self.seller_state_code,
            "invoice_doc_numbers": list(self.document_registry.get('invoice', [])),
            "credit_doc_numbers": list(self.document_registry.get('credit', [])),
            "debit_doc_numbers": list(self.document_registry.get('debit', [])),
            "summary": {
                "rows": summary_rows,
                "total_taxable": round(total_taxable, 2),
                "total_igst": round(total_igst, 2),
                "total_cgst": round(total_cgst, 2),
                "total_sgst": round(total_sgst, 2)
            },
            "invoice_docs": invoice_docs,
            "credit_docs": credit_docs,
            "debit_docs": [],
            "doc_issue": doc_issue
        }
    
    def parse_files(self, files: List[str], seller_gstin: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Main orchestration method."""
        self.seller_state_code = self.resolve_seller_state_code(seller_gstin)
        self.reset_document_registry()
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
    SIGNATURE_PATTERNS = ['sub_order_num', 'end_customer_state_new', 'total_taxable_sale_value']
    TEMPLATE_ADAPTERS = [MeeshoOfficialAdapter()]

    def read_files(self, files: List[str]) -> List[Tuple[pd.DataFrame, str]]:
        dfs = []
        for file in files:
            filename = Path(file).name.lower()
            try:
                if filename == 'tax_invoice_details.xlsx':
                    df = pd.read_excel(file)
                    cleaned = clean_cols(df)
                    invoice_type_col = find_col(cleaned.columns.tolist(), ['type'])
                    invoice_no_col = find_col(cleaned.columns.tolist(), ['invoice_no', 'invoice'])
                    if invoice_type_col and invoice_no_col:
                        invoice_rows = cleaned[cleaned[invoice_type_col].astype(str).str.upper().str.contains('INVOICE', na=False)]
                        credit_rows = cleaned[cleaned[invoice_type_col].astype(str).str.upper().str.contains('CREDIT', na=False)]
                        self.record_document_numbers('invoice', invoice_rows[invoice_no_col].tolist())
                        self.record_document_numbers('credit', credit_rows[invoice_no_col].tolist())
                        self.has_explicit_document_metadata = True
                        logger.info(f"Captured document metadata from {file}")
                    continue

                if filename in {'tcs_sales.xlsx', 'tcs_sales_return.xlsx'}:
                    df = pd.read_excel(file)
                    cleaned = clean_cols(df)
                    invoice_col = find_col(cleaned.columns.tolist(), ['sub_order_num', 'identifier'])
                    state_col = find_col(cleaned.columns.tolist(), ['end_customer_state_new', 'state'])
                    taxable_col = find_col(cleaned.columns.tolist(), ['total_taxable_sale_value', 'taxable'])
                    tax_col = find_col(cleaned.columns.tolist(), ['tax_amount'])
                    txn_type = 'return' if 'return' in filename else 'sale'

                    records = []
                    for idx, row in cleaned.iterrows():
                        pos = get_state_code(row.get(state_col))
                        taxable_value = safe_num(row.get(taxable_col))
                        igst, cgst, sgst = split_tax_amount(pos, row.get(tax_col), self.seller_state_code)
                        if txn_type == 'return':
                            taxable_value = -abs(taxable_value)
                            igst, cgst, sgst = -abs(igst), -abs(cgst), -abs(sgst)
                        record = {
                            'platform': self.PLATFORM,
                            'invoice_no': clean_invoice_no(row.get(invoice_col)) or str(row.name),
                            'pos': pos,
                            'taxable_value': taxable_value,
                            'igst': igst,
                            'cgst': cgst,
                            'sgst': sgst,
                            'txn_type': txn_type,
                            'source_key': f"{Path(file).name}:{idx}",
                        }
                        if has_financial_values(record):
                            records.append(record)

                    normalized = make_preparsed_df(records, self.PLATFORM)
                    dfs.append((normalized, file))
                    if not self.has_explicit_document_metadata:
                        doc_kind = 'credit' if txn_type == 'return' else 'invoice'
                        self.record_document_numbers(doc_kind, normalized['invoice_no'].tolist())
                    logger.info(f"Adapted {file} using Meesho TCS template")
                    continue

                if 'meesho' in filename:
                    df = pd.read_csv(file) if file.lower().endswith('.csv') else read_excel_all_sheets(file)
                    if df is not None and not df.empty and self.file_matches_platform(df, file):
                        adapter = self.detect_template_adapter(df, file)
                        if adapter:
                            df = adapter.normalize(df, file, self.seller_state_code)
                            logger.info(f"Adapted {file} using {adapter.NAME}")
                        dfs.append((df, file))
                        self.record_document_numbers('credit' if is_return_file(file) else 'invoice', df.get('invoice_no', []))
                        logger.info(f"Read {file}: {len(df)} rows")
            except Exception as e:
                logger.error(f"Read error {file}: {str(e)[:60]}")
        return dfs


class FlipkartParser(BaseParser):
    """Parser for Flipkart sales exports."""
    ETIN = "07AACCF0683K1CU"
    PLATFORM = "Flipkart"
    STATE_PATTERNS = ['state', 'delivery', 'place', 'destination']
    TAXABLE_PATTERNS = ['taxable', 'sale_value', 'value']
    SIGNATURE_PATTERNS = ['seller_gstin', 'buyer_invoice_id', 'customer_s_delivery_state']
    TEMPLATE_ADAPTERS = [FlipkartOfficialAdapter()]

    def read_files(self, files: List[str]) -> List[Tuple[pd.DataFrame, str]]:
        dfs = []
        for file in files:
            try:
                path = Path(file)
                if path.suffix.lower() in {'.xlsx', '.xls'}:
                    xl = pd.ExcelFile(file)
                    if 'Sales Report' in xl.sheet_names:
                        sales_df = pd.read_excel(file, sheet_name='Sales Report')
                        cleaned = clean_cols(sales_df)
                        
                        # Filter only true sales events
                        event_type_col = find_col(cleaned.columns.tolist(), ['event_type'])
                        event_subtype_col = find_col(cleaned.columns.tolist(), ['event_sub_type'])
                        
                        if event_type_col and event_subtype_col:
                            sales_df = cleaned[
                                (cleaned[event_type_col].astype(str).str.strip().str.upper() == 'SALE') &
                                (cleaned[event_subtype_col].astype(str).str.strip().str.upper() == 'SALE')
                            ].copy()
                            logger.info(f"Filtered Sales Report to {len(sales_df)} true sales rows")
                        
                        invoice_col = find_col(cleaned.columns.tolist(), ['buyer_invoice_id'])
                        order_col = find_col(cleaned.columns.tolist(), ['order_id'])
                        state_col = find_col(cleaned.columns.tolist(), ["customer's_delivery_state", 'customer_delivery_state'])
                        taxable_col = find_col(cleaned.columns.tolist(), ['taxable_value_final_invoice_amount_taxes', 'taxable_value_final_invoice_amount_taxe', 'taxable_value'])
                        invoice_amount_col = find_col(cleaned.columns.tolist(), ['buyer_invoice_amount'])
                        igst_col = find_col(cleaned.columns.tolist(), ['igst_amount'])
                        cgst_col = find_col(cleaned.columns.tolist(), ['cgst_amount'])
                        sgst_col = find_col(cleaned.columns.tolist(), ['sgst_amount_or_utgst_as_applicable'])
                        
                        if not all([state_col, taxable_col]):
                            logger.warning(f"Missing key columns in Sales Report")
                            continue
                            
                        if sales_df.empty:
                            logger.warning("No sales rows after filtering")
                            continue
                        logger.info(f"Using filtered {len(sales_df)} sales rows")
                        records = []
                        invoice_numbers = {'sale': [], 'return': []}
                        taxable_total = 0.0
                        invoice_total = 0.0
                        for idx, row in sales_df.iterrows():
                            pos = get_state_code(row.get(state_col))
                            if pd.isna(pos):
                                continue
                            taxable_value = safe_num(row.get(taxable_col))
                            invoice_value = safe_num(row.get(invoice_amount_col, taxable_value))
                            igst = safe_num(row.get(igst_col))
                            cgst = safe_num(row.get(cgst_col))
                            sgst = safe_num(row.get(sgst_col))
                            txn_type = 'sale'  # Already filtered to sales
                            invoice_no = clean_invoice_no(row.get(invoice_col)) or clean_invoice_no(row.get(order_col)) or f"SALES_{idx}"
                            record = {
                                'platform': self.PLATFORM,
                                'invoice_no': invoice_no,
                                'pos': pos,
                                'taxable_value': taxable_value,
                                'igst': igst,
                                'cgst': cgst,
                                'sgst': sgst,
                                'txn_type': txn_type,
                                'source_key': f"{Path(file).name}:sales:{idx}",
                            }
                            taxable_total += taxable_value
                            invoice_total += invoice_value
                            if has_financial_values(record):
                                records.append(record)
                                invoice_numbers[txn_type].append(invoice_no)
                        
                        logger.info(f"Sales: taxable={taxable_total:.2f} invoice={invoice_total:.2f}")
                        
                        if records:
                            normalized_sales = make_preparsed_df(records, self.PLATFORM)
                            dfs.append((normalized_sales, file))
                            self.record_document_numbers('invoice', invoice_numbers['sale'])
                            self.record_document_numbers('credit', invoice_numbers['return'])
                            logger.info(f"Processed {len(records)} sales records")

                        if 'Cash Back Report' in xl.sheet_names:
                            cash_df = pd.read_excel(file, sheet_name='Cash Back Report')
                            cash_cleaned = clean_cols(cash_df)
                            
                            # Filter credit notes only
                            doc_type_col = find_col(cash_cleaned.columns.tolist(), ['document_type'])
                            if doc_type_col:
                                cash_df = cash_cleaned[
                                    cash_cleaned[doc_type_col].astype(str).str.strip().str.upper().str.contains('CREDIT')
                                ].copy()
                                logger.info(f"Filtered Cash Back to {len(cash_df)} credit notes")
                            
                            cash_invoice_col = find_col(cash_cleaned.columns.tolist(), ['credit_note_id', 'debit_note_id'])
                            cash_state_col = find_col(cash_cleaned.columns.tolist(), ["customer's_delivery_state", 'customer_delivery_state'])
                            cash_taxable_col = find_col(cash_cleaned.columns.tolist(), ['taxable_value'])
                            cash_invoice_amount_col = find_col(cash_cleaned.columns.tolist(), ['invoice_amount'])
                            cash_igst_col = find_col(cash_cleaned.columns.tolist(), ['igst_amount'])
                            cash_cgst_col = find_col(cash_cleaned.columns.tolist(), ['cgst_amount'])
                            cash_sgst_col = find_col(cash_cleaned.columns.tolist(), ['sgst_amount_or_utgst_as_applicable'])
                            
                            if not all([cash_state_col, cash_taxable_col]):
                                logger.warning(f"Missing key columns in Cash Back Report")
                                continue
                            
                            if cash_df.empty:
                                logger.info("No cashback credit notes found")
                            else:
                                logger.info(f"Using filtered {len(cash_df)} cashback credit notes")
                                cash_records = []
                                taxable_total = 0.0
                                invoice_total = 0.0
                                for idx, row in cash_df.iterrows():
                                    pos = get_state_code(row.get(cash_state_col))
                                    if pd.isna(pos):
                                        continue
                                    taxable_value = safe_num(row.get(cash_taxable_col))
                                    invoice_value = safe_num(row.get(cash_invoice_amount_col, taxable_value))
                                    igst = safe_num(row.get(cash_igst_col))
                                    cgst = safe_num(row.get(cash_cgst_col))
                                    sgst = safe_num(row.get(cash_sgst_col))
                                    
                                    # Credit notes are always returns - negate values
                                    record = {
                                        'platform': self.PLATFORM,
                                        'invoice_no': clean_invoice_no(row.get(cash_invoice_col)) or f"CASHBACK_{idx}",
                                        'pos': pos,
                                        'taxable_value': -abs(taxable_value),
                                        'igst': -abs(igst),
                                        'cgst': -abs(cgst),
                                        'sgst': -abs(sgst),
                                        'txn_type': 'return',
                                        'source_key': f"{Path(file).name}:cashback:{idx}",
                                    }
                                    taxable_total += abs(taxable_value)
                                    invoice_total += abs(invoice_value)
                                    if has_financial_values(record):
                                        cash_records.append(record)
                                        self.record_document_numbers('credit', [record['invoice_no']])
                                
                                logger.info(f"Returns: taxable={taxable_total:.2f} invoice={invoice_total:.2f}")
                                logger.info(f"Net taxable={taxable_total - invoice_total:.2f} invoice={invoice_total - taxable_total:.2f}")
                            
                            if cash_records:
                                normalized_cashback = make_preparsed_df(cash_records, self.PLATFORM)
                                dfs.append((normalized_cashback, file + '#cashback'))
                                logger.info(f"Processed {len(cash_records)} cashback returns")
                        logger.info(f"Adapted {file} using Flipkart Sales/Cashback template")
                        continue

                if path.suffix.lower() == '.csv':
                    df = pd.read_csv(file)
                    if df is not None and not df.empty and self.file_matches_platform(df, file):
                        adapter = self.detect_template_adapter(df, file)
                        if adapter:
                            df = adapter.normalize(df, file, self.seller_state_code)
                            logger.info(f"Adapted {file} using {adapter.NAME}")
                        dfs.append((df, file))
                        self.record_document_numbers('invoice', df.get('invoice_no', []))
                        logger.info(f"Read {file}: {len(df)} rows")
            except Exception as e:
                logger.error(f"Read error {file}: {str(e)[:60]}")
        return dfs


class AmazonParser(BaseParser):
    """Parser for Amazon sales exports."""
    ETIN = "07AAICA3918J1CV"
    PLATFORM = "Amazon"
    STATE_PATTERNS = ['state', 'ship_state', 'place']
    TAXABLE_PATTERNS = ['tax_exclusive', 'taxable', 'gross']
    SIGNATURE_PATTERNS = ['seller_gstin', 'invoice_number', 'ship_to_state', 'tax_exclusive_gross']
    TEMPLATE_ADAPTERS = [AmazonOfficialAdapter()]

    def read_files(self, files: List[str]) -> List[Tuple[pd.DataFrame, str]]:
        dfs = []
        for file in files:
            try:
                path = Path(file)
                if path.suffix.lower() == '.csv':
                    df = pd.read_csv(file)
                    cleaned = clean_cols(df)
                    cols = cleaned.columns.tolist()
                    if {'invoice_number', 'ship_to_state', 'tax_exclusive_gross'}.issubset(set(cols)):
                        records = []
                        for idx, row in cleaned.iterrows():
                            txn_type_raw = str(row.get('transaction_type', '')).strip().lower()
                            pos = get_state_code(row.get('ship_to_state'))
                            taxable_value = safe_num(row.get('tax_exclusive_gross'))
                            igst = safe_num(row.get('igst_tax'))
                            cgst = safe_num(row.get('cgst_tax'))
                            sgst = safe_num(row.get('sgst_tax')) + safe_num(row.get('utgst_tax'))
                            invoice_no = clean_invoice_no(row.get('invoice_number')) or clean_invoice_no(row.get('order_id')) or str(row.name)

                            if txn_type_raw in {'refund', 'cancel'} or taxable_value < 0:
                                record = {
                                    'platform': self.PLATFORM,
                                    'invoice_no': clean_invoice_no(row.get('credit_note_no')) or invoice_no,
                                    'pos': pos,
                                    'taxable_value': -abs(taxable_value),
                                    'igst': -abs(igst),
                                    'cgst': -abs(cgst),
                                    'sgst': -abs(sgst),
                                    'txn_type': 'return',
                                    'source_key': f"{Path(file).name}:{idx}",
                                }
                                if has_financial_values(record):
                                    records.append(record)
                                    self.record_document_numbers('credit', [row.get('credit_note_no') or invoice_no])
                            elif txn_type_raw in {'shipment', 'freereplacement'}:
                                record = {
                                    'platform': self.PLATFORM,
                                    'invoice_no': invoice_no,
                                    'pos': pos,
                                    'taxable_value': taxable_value,
                                    'igst': igst,
                                    'cgst': cgst,
                                    'sgst': sgst,
                                    'txn_type': 'sale',
                                    'source_key': f"{Path(file).name}:{idx}",
                                }
                                if has_financial_values(record):
                                    records.append(record)
                                    self.record_document_numbers('invoice', [invoice_no])
                        normalized = make_preparsed_df(records, self.PLATFORM)
                        dfs.append((normalized, file))
                        logger.info(f"Adapted {file} using Amazon MTR template")
                        continue

                    if df is not None and not df.empty and self.file_matches_platform(df, file):
                        adapter = self.detect_template_adapter(df, file)
                        if adapter:
                            df = adapter.normalize(df, file, self.seller_state_code)
                            logger.info(f"Adapted {file} using {adapter.NAME}")
                        dfs.append((df, file))
                        self.record_document_numbers('credit' if is_return_file(file) else 'invoice', df.get('invoice_no', []))
                        logger.info(f"Read {file}: {len(df)} rows")
            except Exception as e:
                logger.error(f"Read error {file}: {str(e)[:60]}")
        return dfs


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
    
    def parse_files(self, files: List[str], seller_gstin: Optional[str] = None) -> Dict[str, Any]:
        """Parse all platforms and merge results."""
        parsers = [MeeshoParser(), FlipkartParser(), AmazonParser()]
        results = []
        
        logger.info("🚀 PARSING FILES FOR ALL PLATFORMS")
        for file in files:
            logger.info(f"  📄 {Path(file).name}")
        
        # Execute all parsers
        for parser in parsers:
            try:
                result = parser.parse_files(files, seller_gstin=seller_gstin)
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
                "clttx": [],
                "doc_issue": {"doc_det": []},
                "seller_state_code": extract_state_code_from_gstin(seller_gstin)
            }
        
        # MERGE: Aggregate all state totals across all parsers
        state_totals = defaultdict(lambda: {
            'taxable_value': 0.0,
            'igst': 0.0,
            'cgst': 0.0,
            'sgst': 0.0
        })
        clttx = []
        all_invoice_docs = []
        all_credit_docs = []
        all_invoice_doc_numbers = []
        all_credit_doc_numbers = []
        all_debit_doc_numbers = []
        seller_state_code = extract_state_code_from_gstin(seller_gstin)
        
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
            if result['invoice_docs']:
                all_invoice_docs.extend(result['invoice_docs'])
            if result['credit_docs']:
                all_credit_docs.extend(result['credit_docs'])
            all_invoice_doc_numbers.extend(result.get('invoice_doc_numbers', []))
            all_credit_doc_numbers.extend(result.get('credit_doc_numbers', []))
            all_debit_doc_numbers.extend(result.get('debit_doc_numbers', []))
        
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
        
        rows = sorted(rows, key=lambda row: str(row['pos']))
        clttx = sorted(clttx, key=lambda row: row['etin'])
        all_invoice_docs = sorted(all_invoice_docs, key=lambda row: (str(row['pos']), str(row['invoice_no'])))
        all_credit_docs = sorted(all_credit_docs, key=lambda row: (str(row['pos']), str(row['invoice_no'])))

        # Calculate grand totals
        grand_total_taxable = sum(r['taxable_value'] for r in rows)
        grand_total_igst = sum(r['igst'] for r in rows)
        grand_total_cgst = sum(r['cgst'] for r in rows)
        grand_total_sgst = sum(r['sgst'] for r in rows)
        
        logger.info(f"✓ Merged {len(results)} platforms, {len(rows)} states")
        
        return {
            "seller_state_code": seller_state_code,
            "invoice_doc_numbers": all_invoice_doc_numbers,
            "credit_doc_numbers": all_credit_doc_numbers,
            "debit_doc_numbers": all_debit_doc_numbers,
            "summary": {
                "rows": rows,
                "total_taxable": round(grand_total_taxable, 2),
                "total_igst": round(grand_total_igst, 2),
                "total_cgst": round(grand_total_cgst, 2),
                "total_sgst": round(grand_total_sgst, 2)
            },
            "invoice_docs": all_invoice_docs,
            "credit_docs": all_credit_docs,
            "debit_docs": [],
            "clttx": clttx,
            "doc_issue": build_doc_issue_details(all_invoice_doc_numbers, all_credit_doc_numbers, all_debit_doc_numbers)
        }


if __name__ == "__main__":
    print("parsers.py loaded successfully")
    print("FlipkartParser available:", hasattr(__import__('parsers'), 'FlipkartParser'))

