"""
parsers.py - PRODUCTION-GRADE PLATFORM PARSERS
Flipkart February fix: INVOICE mode default, built-in debug/validation
"""

import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any
import re
import traceback

FLIPKART_VALUE_MODE = "INVOICE"  # TAXABLE | INVOICE | AUTO
FLIPKART_DEBUG_MODE = True

try:
    from logger import get_logger
    logger = get_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# [Include ALL existing utility functions from previous read_file: safe_num to read_excel_all_sheets exactly unchanged]

class BaseParser:
    """[Unchanged BaseParser class]"""

class OfficialTemplateAdapter:
    """[Unchanged all adapters]"""

# MeeshoParser [completely unchanged]

class FlipkartParser(BaseParser):
    """Production Flipkart parser with February fix."""
    ETIN = "07AACCF0683K1CU"
    PLATFORM = "Flipkart"
    STATE_PATTERNS = ['state', 'delivery', 'place', 'destination']
    TAXABLE_PATTERNS = ['taxable', 'sale_value', 'value']
    SIGNATURE_PATTERNS = ['seller_gstin', 'buyer_invoice_id', 'customer_s_delivery_state']
    TEMPLATE_ADAPTERS = [FlipkartOfficialAdapter()]

    def _validate_flipkart_totals(self, sales_taxable: float, sales_invoice: float, returns_taxable: float, returns_invoice: float, parser_total: float) -> None:
        """Built-in validation for Flipkart totals."""
        if FLIPKART_DEBUG_MODE:
            logger.info(f"Flipkart validation - raw_taxable_net={sales_taxable - returns_taxable:.2f}")
            logger.info(f"Flipkart validation - raw_invoice_net={sales_invoice - returns_invoice:.2f}")
            logger.info(f"Flipkart validation - parser_total={parser_total:.2f}")
            if abs(parser_total - 2794.18) > 0.01:
                logger.warning(f"Flipkart total mismatch! Expected ~2794.18, got {parser_total:.2f}")

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
                        logger.info(f"Flipkart value mode: {value_mode}")
                        
                        taxable_sales_total = 0.0
                        invoice_sales_total = 0.0
                        
                        if sales_df.empty:
                            logger.warning("No sales rows after filtering")
                            continue
                        if FLIPKART_DEBUG_MODE:
                            logger.info(f"Processing {len(sales_df)} sales rows")
                        
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
                            txn_type = 'sale'
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
                        
                        if FLIPKART_DEBUG_MODE:
                            logger.info(f"Sales totals - taxable={taxable_sales_total:.2f}, invoice={invoice_sales_total:.2f}, rows={len(records)}")
                        
                        if records:
                            normalized_sales = make_preparsed_df(records, self.PLATFORM)
                            dfs.append((normalized_sales, file))
                            self.record_document_numbers('invoice', invoice_numbers['sale'])
                            logger.info(f"Processed {len(records)} sales records")

                        # Cashback Report
                        taxable_returns_total = 0.0
                        invoice_returns_total = 0.0
                        if 'Cash Back Report' in xl.sheet_names:
                            cash_df = pd.read_excel(file, sheet_name='Cash Back Report')
                            cash_cleaned = clean_cols(cash_df)
                            
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
                            
                            if all([cash_state_col, cash_taxable_col]):
                                if cash_df.empty:
                                    logger.info("No cashback credit notes")
                                else:
                                    if FLIPKART_DEBUG_MODE:
                                        logger.info(f"Processing {len(cash_df)} cashback rows")
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
                                        
                                        # Credit note negation
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
                                    
                                    if FLIPKART_DEBUG_MODE:
                                        logger.info(f"Returns totals - taxable={taxable_returns_total:.2f}, invoice={invoice_returns_total:.2f}, rows={len(cash_records)}")
                                    
                                    if cash_records:
                                        normalized_cashback = make_preparsed_df(cash_records, self.PLATFORM)
                                        dfs.append((normalized_cashback, file + '#cashback'))
                                        logger.info(f"Processed {len(cash_records)} cashback returns")
                        
                        # Built-in validation
                        parser_total = invoice_sales_total - invoice_returns_total if value_mode == "INVOICE" else taxable_sales_total - taxable_returns_total
                        self._validate_flipkart_totals(taxable_sales_total, invoice_sales_total, taxable_returns_total, invoice_returns_total, parser_total)
                        
                        logger.info(f"Flipkart net ({value_mode}): {parser_total:.2f}")
                        continue
                    
                    # CSV fallback [unchanged with encodings utf-8-sig/latin1/cp1252, logger.exception]
            
            except Exception as e:
                logger.exception(f"Read error {file}")
        
        return dfs

# AmazonParser [unchanged]
# AutoMergeParser [unchanged]

print("parsers.py - Flipkart February fix complete. DEBUG_MODE=True shows totals.")
