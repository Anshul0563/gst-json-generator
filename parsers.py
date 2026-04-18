
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import logging
import re

logger = logging.getLogger(__name__)


# =====================================================
# HELPERS
# =====================================================

def num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)


def clean_name(col: str) -> str:
    col = str(col).strip().lower()
    col = re.sub(r"[^\w]+", "_", col)
    col = re.sub(r"_+", "_", col).strip("_")
    return col


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [clean_name(c) for c in df.columns]
    return df


def safe_read_csv(path: str):
    for enc in ["utf-8", "utf-16", "utf-16le", "cp1252", "latin1"]:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception:
            pass
    return None


def read_any(path: str):
    ext = Path(path).suffix.lower()

    try:
        if ext in [".xlsx", ".xls"]:
            xl = pd.ExcelFile(path)
            sheets = []
            for sh in xl.sheet_names:
                try:
                    df = pd.read_excel(path, sheet_name=sh)
                    if not df.empty:
                        sheets.append((sh, df))
                except Exception:
                    continue
            return sheets

        elif ext == ".csv":
            df = safe_read_csv(path)
            if df is not None:
                return [("Sheet1", df)]

    except Exception as e:
        logger.error(f"Read error {path}: {e}")

    return []


def pick(cols, candidates):
    for c in candidates:
        if c in cols:
            return c
    return None


def build_state_summary(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {
            "state_summary": [],
            "total_taxable": 0.0,
            "total_igst": 0.0,
            "total_cgst": 0.0,
            "total_sgst": 0.0,
        }

    grp = (
        df.groupby("state_code", as_index=False)[
            ["taxable_value", "igst", "cgst", "sgst"]
        ]
        .sum()
        .round(2)
    )

    return {
        "state_summary": grp.to_dict("records"),
        "total_taxable": float(grp["taxable_value"].sum()),
        "total_igst": float(grp["igst"].sum()),
        "total_cgst": float(grp["cgst"].sum()),
        "total_sgst": float(grp["sgst"].sum()),
    }


def build_doc_series(values: List[Any]) -> List[Dict]:
    vals = [str(v).strip() for v in values if str(v).strip()]
    vals = sorted(set(vals))

    if not vals:
        return []

    return [{
        "num": len(vals),
        "from": vals[0],
        "to": vals[-1]
    }]


# =====================================================
# DETECTION
# =====================================================

def detect_platform(cols: List[str]) -> str:
    s = set(cols)

    # Amazon
    if {"seller_gstin", "invoice_number", "ship_to_state"}.issubset(s):
        return "Amazon"

    # Flipkart
    if "buyer_invoice_id" in s and (
        "customers_delivery_state" in s or
        "customer_s_delivery_state" in s
    ):
        return "Flipkart"

    # Meesho
    if (
        "end_customer_state_new" in s or
        "total_taxable_sale_value" in s or
        "tax_invoice_number" in s
    ):
        return "Meesho"

    return ""


# =====================================================
# BASE
# =====================================================

class BaseParser:
    def parse_files(self, files: List[str]) -> Dict[str, Any]:
        raise NotImplementedError


# =====================================================
# MEESHO
# =====================================================

class MeeshoParser(BaseParser):

    def parse_files(self, files):
        rows = []
        invoices = []

        for file in files:
            for sheet, raw in read_any(file):
                df = clean_df(raw)
                cols = list(df.columns)

                if detect_platform(cols) != "Meesho":
                    continue

                state_col = pick(cols, [
                    "end_customer_state_new",
                    "place_of_supply",
                    "customer_state"
                ])

                tax_col = pick(cols, [
                    "total_taxable_sale_value",
                    "taxable_value",
                    "taxable_amount"
                ])

                igst_col = pick(cols, [
                    "tax_amount",
                    "igst",
                    "igst_amount"
                ])

                inv_col = pick(cols, [
                    "invoice_no",
                    "tax_invoice_number",
                    "invoice_number"
                ])

                if not state_col or not tax_col:
                    continue

                temp = pd.DataFrame({
                    "state_code": df[state_col].astype(str).str.upper(),
                    "taxable_value": num(df[tax_col]),
                    "igst": num(df[igst_col]) if igst_col else 0,
                    "cgst": 0,
                    "sgst": 0
                })

                rows.append(temp)

                if inv_col:
                    invoices.extend(df[inv_col].dropna().tolist())

        if not rows:
            raise Exception("Meesho data not detected")

        final = pd.concat(rows, ignore_index=True)

        return {
            "platform": "Meesho",
            "net": build_state_summary(final),
            "invoice_details": build_doc_series(invoices)
        }


# =====================================================
# FLIPKART
# =====================================================

class FlipkartParser(BaseParser):

    def parse_files(self, files):
        rows = []
        invoices = []

        for file in files:
            for sheet, raw in read_any(file):
                df = clean_df(raw)
                cols = list(df.columns)

                if detect_platform(cols) != "Flipkart":
                    continue

                state_col = pick(cols, [
                    "customers_delivery_state",
                    "customer_s_delivery_state",
                    "customer_delivery_state"
                ])

                tax_col = pick(cols, [
                    "taxable_value_final_invoice_amount_taxes",
                    "taxable_value",
                    "final_invoice_amount"
                ])

                igst_col = pick(cols, ["igst_amount"])
                cgst_col = pick(cols, ["cgst_amount"])
                sgst_col = pick(cols, [
                    "sgst_amount_or_utgst_as_applicable",
                    "sgst_amount"
                ])

                inv_col = pick(cols, [
                    "buyer_invoice_id",
                    "invoice_id"
                ])

                event_col = pick(cols, ["event_type"])

                if not state_col or not tax_col:
                    continue

                sign = 1
                if event_col:
                    sign = df[event_col].astype(str).str.lower().apply(
                        lambda x: -1 if "return" in x or "cancel" in x else 1
                    )
                else:
                    sign = 1

                temp = pd.DataFrame({
                    "state_code": df[state_col].astype(str).str.upper(),
                    "taxable_value": num(df[tax_col]) * sign,
                    "igst": num(df[igst_col]) * sign if igst_col else 0,
                    "cgst": num(df[cgst_col]) * sign if cgst_col else 0,
                    "sgst": num(df[sgst_col]) * sign if sgst_col else 0
                })

                rows.append(temp)

                if inv_col:
                    invoices.extend(df[inv_col].dropna().tolist())

        if not rows:
            raise Exception("Flipkart data not detected")

        final = pd.concat(rows, ignore_index=True)

        return {
            "platform": "Flipkart",
            "net": build_state_summary(final),
            "invoice_details": build_doc_series(invoices)
        }


# =====================================================
# AMAZON
# =====================================================

class AmazonParser(BaseParser):

    def parse_files(self, files):
        rows = []
        invoices = []

        for file in files:
            for sheet, raw in read_any(file):
                df = clean_df(raw)
                cols = list(df.columns)

                if detect_platform(cols) != "Amazon":
                    continue

                state_col = pick(cols, [
                    "ship_to_state",
                    "buyer_state"
                ])

                tax_col = pick(cols, [
                    "tax_exclusive_gross",
                    "taxable_value",
                    "principal_amount_basis"
                ])

                igst_col = pick(cols, ["igst_tax"])
                cgst_col = pick(cols, ["cgst_tax"])
                sgst_col = pick(cols, ["sgst_tax"])

                inv_col = pick(cols, [
                    "invoice_number",
                    "buyer_invoice_id"
                ])

                txn_col = pick(cols, [
                    "transaction_type",
                    "event_type"
                ])

                if not state_col or not tax_col:
                    continue

                sign = 1
                if txn_col:
                    sign = df[txn_col].astype(str).str.lower().apply(
                        lambda x: -1 if "return" in x or "refund" in x or "cancel" in x else 1
                    )
                else:
                    sign = 1

                temp = pd.DataFrame({
                    "state_code": df[state_col].astype(str).str.upper(),
                    "taxable_value": num(df[tax_col]) * sign,
                    "igst": num(df[igst_col]) * sign if igst_col else 0,
                    "cgst": num(df[cgst_col]) * sign if cgst_col else 0,
                    "sgst": num(df[sgst_col]) * sign if sgst_col else 0
                })

                rows.append(temp)

                if inv_col:
                    invoices.extend(df[inv_col].dropna().tolist())

        if not rows:
            raise Exception("Amazon data not detected")

        final = pd.concat(rows, ignore_index=True)

        return {
            "platform": "Amazon",
            "net": build_state_summary(final),
            "invoice_details": build_doc_series(invoices)
        }