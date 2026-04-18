"""
parsers.py - PRODUCTION-GRADE PLATFORM PARSERS
- Meesho, Flipkart, Amazon with dedicated parsers
- AutoMergeParser for multi-platform consolidation
- Production-ready error handling and logging
- Focus on data accuracy and completeness
"""

FLIPKART_VALUE_MODE = "INVOICE"  # TAXABLE | INVOICE | AUTO

import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any
import re
import traceback

try:
    from logger import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# [All existing utility functions unchanged - safe_num, clean_cols, find_col, normalize_identifier, col_matches_pattern, clean_invoice_no, extract_state_code_from_gstin, get_state_code, is_return_file, is_intra_supply, calc_tax, split_tax_amount, build_doc_issue_details, make_preparsed_df, has_financial_values, apply_tax_columns, OfficialTemplateAdapter, MeeshoOfficialAdapter, FlipkartOfficialAdapter, AmazonOfficialAdapter, read_excel_all_sheets]

# BaseParser class [unchanged]

# MeeshoParser [unchanged]

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
                        invoice_amount_col = find_col(cleaned.columns.tolist(), ['buyer_invoice_amount', 'final_invoice_amount', 'invoice_amount'])
                        igst_col = find_col(cleaned.columns.tolist(), ['igst_amount'])
                        cgst_col = find_col(cleaned.columns.tolist(), ['cgst_amount'])
                        sgst_col = find_col(cleaned.columns.tolist(), ['sgst_amount_or_utgst_as_applicable'])
                        
                        if not all([state_col, taxable_col]):
                            logger.warning(f"Missing key columns in Sales Report")
                            continue
                            
                        value_mode = FLIPKART_VALUE_MODE.upper()
                        if value_mode not in {"TAXABLE", "INVOICE", "AUTO"}:
                            value_mode = "INVOICE"
                        logger.info(f"Flipkart value mode: {value_mode}")
                        
                        taxable_sales_total = 0.0
                        invoice_sales_total = 0.0
                        
                        if sales_df.empty:
                            logger.warning("No sales rows after filtering")
                            continue
                        logger.info(f"Using filtered {len(sales_df)} sales rows")
                        records = []
                        invoice_numbers = {'sale': [], 'return': []}
                        for idx, row in sales_df.iterrows():
                            pos = get_state_code(row.get(state_col))
                            if not pos:
                                continue
                            taxable_value = safe_num(row.get(taxable_col))
                            invoice_value = safe_num(row.get(invoice_amount_col)) if invoice_amount_col else 0.0
                            taxable_sales_total += taxable_value
                            invoice_sales_total += invoice_value
                            igst = safe_num(row.get(igst_col))
                            cgst = safe_num(row.get(cgst_col))
                            sgst = safe_num(row.get(sgst_col))
                            txn_type = 'sale'  # Already filtered to sales
                            invoice_no = clean_invoice_no(row.get(invoice_col)) or clean_invoice_no(row.get(order_col)) or f"SALES_{idx}"
                            if value_mode == "TAXABLE":
                                value = taxable_value
                            elif value_mode == "INVOICE":
                                value = invoice_value if invoice_value > 0 else taxable_value + igst + cgst + sgst
                            else:  # AUTO
                                value = invoice_value if invoice_value > 0 else taxable_value
                            record = {
                                'platform': self.PLATFORM,
                                'invoice_no': invoice_no,
                                'pos': pos,
                                'taxable_value': value,
                                'igst': igst,
                                'cgst': cgst,
                                'sgst': sgst,
                                'txn_type': txn_type,
                                'source_key': f"{Path(file).name}:sales:{idx}",
                            }
                            if has_financial_values(record):
                                records.append(record)
                                invoice_numbers[txn_type].append(invoice_no)
                        
                        logger.info(f"Sales: taxable={taxable_sales_total:.2f} invoice={invoice_sales_total:.2f}")
                        
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
                            
                            value_mode = FLIPKART_VALUE_MODE.upper()
                            logger.info(f"Cashback value mode: {value_mode}")
                            
                            taxable_returns_total = 0.0
                            invoice_returns_total = 0.0
                            
                            if cash_df.empty:
                                logger.info("No cashback credit notes found")
                            else:
                                logger.info(f"Using filtered {len(cash_df)} cashback credit notes")
                                cash_records = []
                                for idx, row in cash_df.iterrows():
                                    pos = get_state_code(row.get(cash_state_col))
                                    if not pos:
                                        continue
                                    taxable_value = safe_num(row.get(cash_taxable_col))
                                    invoice_value = safe_num(row.get(cash_invoice_amount_col)) if cash_invoice_amount_col else 0.0
                                    taxable_returns_total += taxable_value
                                    invoice_returns_total += invoice_value
                                    igst = safe_num(row.get(cash_igst_col))
                                    cgst = safe_num(row.get(cash_cgst_col))
                                    sgst = safe_num(row.get(cash_sgst_col))
                                    
                                    # Credit notes are always returns - negate values
                                    if value_mode == "TAXABLE":
                                        value = -abs(taxable_value)
                                    elif value_mode == "INVOICE":
                                        fallback = taxable_value + igst + cgst + sgst
                                        value = -abs(invoice_value if invoice_value > 0 else fallback)
                                    else:  # AUTO
                                        value = -abs(invoice_value if invoice_value > 0 else taxable_value)
                                    record = {
                                        'platform': self.PLATFORM,
                                        'invoice_no': clean_invoice_no(row.get(cash_invoice_col)) or f"CASHBACK_{idx}",
                                        'pos': pos,
                                        'taxable_value': value,
                                        'igst': -abs(igst),
                                        'cgst': -abs(cgst),
                                        'sgst': -abs(sgst),
                                        'txn_type': 'return',
                                        'source_key': f"{Path(file).name}:cashback:{idx}",
                                    }
                                    if has_financial_values(record):
                                        cash_records.append(record)
                                        self.record_document_numbers('credit', [record['invoice_no']])
                            
                            logger.info(f"Returns: taxable={taxable_returns_total:.2f} invoice={invoice_returns_total:.2f}")
                            logger.info(f"FINAL Flipkart Net ({value_mode}): taxable_net={taxable_sales_total - taxable_returns_total:.2f} invoice_net={invoice_sales_total - invoice_returns_total:.2f}")
                            
                            if cash_records:
                                normalized_cashback = make_preparsed_df(cash_records, self.PLATFORM)
                                dfs.append((normalized_cashback, file + '#cashback'))
                                logger.info(f"Processed {len(cash_records)} cashback returns")
                        logger.info(f"Adapted {file} using Flipkart Sales/Cashback template")
                        continue

                # CSV fallback
                if path.suffix.lower() == '.csv':
                    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
                    df = None
                    for enc in encodings:
                        try:
                            df = pd.read_csv(file, encoding=enc)
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if df is not None and not df.empty and self.file_matches_platform(df, file):
                        adapter = self.detect_template_adapter(df, file)
                        if adapter:
                            df = adapter.normalize(df, file, self.seller_state_code)
                            logger.info(f"Adapted {file} using {adapter.NAME}")
                        dfs.append((df, file))
                        logger.info(f"Read {file} with {enc}: {len(df)} rows")
                    else:
                        logger.error(f"Failed to read CSV {file} with all encodings")
            except Exception as e:
                logger.exception(f"Read error {file}: {e}")
        return dfs

# AmazonParser [unchanged]

# AutoMergeParser class [unchanged, doc_issue safe as dicts built earlier]

print("parsers_fixed.py created - Run tests!")

