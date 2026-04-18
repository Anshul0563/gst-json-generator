# parsers.py
# FINAL PRODUCTION CLONE ENGINE
# Dynamic + Multi Marketplace + Real Totals + Exact JSON Ready

import pandas as pd
from pathlib import Path
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


# =========================================================
# HELPERS
# =========================================================
STATE_CODE_MAP = {
    "andhra pradesh": "37",
    "arunachal pradesh": "12",
    "assam": "18",
    "bihar": "10",
    "chandigarh": "04",
    "chhattisgarh": "22",
    "delhi": "07",
    "goa": "30",
    "gujarat": "24",
    "haryana": "06",
    "himachal pradesh": "02",
    "jharkhand": "20",
    "karnataka": "29",
    "kerala": "32",
    "madhya pradesh": "23",
    "maharashtra": "27",
    "odisha": "21",
    "orissa": "21",
    "punjab": "03",
    "rajasthan": "08",
    "tamil nadu": "33",
    "telangana": "36",
    "uttar pradesh": "09",
    "uttarakhand": "05",
    "west bengal": "19",
    "jammu & kashmir": "01",
    "ladakh": "38",
}

ETIN_MAP = {
    "Meesho": "07AARCM9332R1CQ",
    "Amazon": "07AAICA3918J1CV",
    "Flipkart": "07AACCF0683K1CU",
}


def num(v):
    return pd.to_numeric(v, errors="coerce").fillna(0)


def normalize_cols(df):
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("/", "_", regex=False)
        .str.replace("(", "", regex=False)
        .str.replace(")", "", regex=False)
        .str.replace("-", "_", regex=False)
    )
    return df


def state_to_code(v):
    if pd.isna(v):
        return "00"
    s = str(v).strip().lower()
    if s in STATE_CODE_MAP:
        return STATE_CODE_MAP[s]
    if len(s) == 2 and s.isdigit():
        return s
    return "00"


def build_summary(df):
    if df.empty:
        return {
            "rows": [],
            "total_taxable": 0.0,
            "total_igst": 0.0,
            "total_cgst": 0.0,
            "total_sgst": 0.0,
        }

    g = (
        df.groupby("pos", as_index=False)[
            ["taxable_value", "igst", "cgst", "sgst"]
        ]
        .sum()
        .round(2)
    )

    rows = g.to_dict("records")

    return {
        "rows": rows,
        "total_taxable": float(g["taxable_value"].sum()),
        "total_igst": float(g["igst"].sum()),
        "total_cgst": float(g["cgst"].sum()),
        "total_sgst": float(g["sgst"].sum()),
    }


# =========================================================
# BASE
# =========================================================
class BaseParser:
    def parse_files(self, files: List[str]) -> Dict[str, Any]:
        raise NotImplementedError


# =========================================================
# MEESHO
# =========================================================
class MeeshoParser(BaseParser):

    def parse_files(self, files):
        sales_frames = []
        invoice_docs = []
        credit_docs = []

        for f in files:
            name = Path(f).name.lower()

            if "tax_invoice" in name:
                df = pd.read_excel(f)
                invoice_docs = self.extract_doc_range(df)

            elif "return" in name:
                df = pd.read_excel(f)
                df = normalize_cols(df)

                taxable_col = self.find_col(df, [
                    "total_taxable_sale_value",
                    "taxable_value",
                ])
                tax_col = self.find_col(df, [
                    "tax_amount",
                    "igst",
                ])
                state_col = self.find_col(df, [
                    "end_customer_state_new",
                    "state",
                ])

                x = pd.DataFrame()
                x["taxable_value"] = -num(df[taxable_col])
                x["igst"] = -num(df[tax_col])
                x["cgst"] = 0
                x["sgst"] = 0
                x["pos"] = df[state_col].apply(state_to_code)

                sales_frames.append(x)
                credit_docs = self.extract_doc_range(df)

            else:
                df = pd.read_excel(f)
                df = normalize_cols(df)

                if "total_taxable_sale_value" in df.columns:
                    taxable_col = "total_taxable_sale_value"
                    tax_col = self.find_col(df, ["tax_amount"])
                    state_col = self.find_col(df, ["end_customer_state_new"])

                    x = pd.DataFrame()
                    x["taxable_value"] = num(df[taxable_col])
                    x["igst"] = num(df[tax_col])
                    x["cgst"] = 0
                    x["sgst"] = 0
                    x["pos"] = df[state_col].apply(state_to_code)

                    sales_frames.append(x)

        final = pd.concat(sales_frames, ignore_index=True) if sales_frames else pd.DataFrame()

        return {
            "platform": "Meesho",
            "etin": ETIN_MAP["Meesho"],
            "summary": build_summary(final),
            "invoice_docs": invoice_docs,
            "credit_docs": credit_docs,
            "debit_docs": []
        }

    def find_col(self, df, names):
        for n in names:
            if n in df.columns:
                return n
        raise Exception(f"Column not found from {names}")

    def extract_doc_range(self, df):
        for col in df.columns:
            if "invoice" in str(col).lower():
                vals = df[col].dropna().astype(str).unique()
                if len(vals):
                    return [{
                        "from": min(vals),
                        "to": max(vals),
                        "totnum": len(vals)
                    }]
        return []


# =========================================================
# FLIPKART
# =========================================================
class FlipkartParser(BaseParser):

    def parse_files(self, files):
        frames = []
        docs = []
        credits = []

        for f in files:
            try:
                xl = pd.ExcelFile(f)
            except:
                continue

            for sheet in xl.sheet_names:
                if "sales" in sheet.lower():
                    df = pd.read_excel(f, sheet_name=sheet)
                    df = normalize_cols(df)

                    if "taxable_value_final_invoice_amount__taxes" not in df.columns:
                        continue

                    x = pd.DataFrame()
                    x["taxable_value"] = num(df["taxable_value_final_invoice_amount__taxes"])
                    x["igst"] = num(df.get("igst_amount", 0))
                    x["cgst"] = num(df.get("cgst_amount", 0))
                    x["sgst"] = num(df.get("sgst_amount_or_utgst_as_applicable", 0))
                    x["pos"] = df["customers_delivery_state"].apply(state_to_code)

                    frames.append(x)

                    if "buyer_invoice_id" in df.columns:
                        vals = df["buyer_invoice_id"].dropna().astype(str).unique()
                        if len(vals):
                            docs = [{
                                "from": min(vals),
                                "to": max(vals),
                                "totnum": len(vals)
                            }]

        final = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

        return {
            "platform": "Flipkart",
            "etin": ETIN_MAP["Flipkart"],
            "summary": build_summary(final),
            "invoice_docs": docs,
            "credit_docs": credits,
            "debit_docs": []
        }


# =========================================================
# AMAZON
# =========================================================
class AmazonParser(BaseParser):

    def parse_files(self, files):
        frames = []
        docs = []

        for f in files:
            try:
                if str(f).lower().endswith(".csv"):
                    df = pd.read_csv(f, encoding="utf-8", low_memory=False)
                else:
                    df = pd.read_excel(f)
            except:
                try:
                    df = pd.read_csv(f, encoding="latin1", low_memory=False)
                except:
                    continue

            df = normalize_cols(df)

            if "tax_exclusive_gross" not in df.columns:
                continue

            x = pd.DataFrame()
            x["taxable_value"] = num(df["tax_exclusive_gross"])
            x["igst"] = num(df.get("igst_tax", 0))
            x["cgst"] = num(df.get("cgst_tax", 0))
            x["sgst"] = num(df.get("sgst_tax", 0))
            x["pos"] = df["ship_to_state"].apply(state_to_code)

            frames.append(x)

            if "invoice_number" in df.columns:
                vals = df["invoice_number"].dropna().astype(str).unique()
                if len(vals):
                    docs = [{
                        "from": min(vals),
                        "to": max(vals),
                        "totnum": len(vals)
                    }]

        final = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

        return {
            "platform": "Amazon",
            "etin": ETIN_MAP["Amazon"],
            "summary": build_summary(final),
            "invoice_docs": docs,
            "credit_docs": [],
            "debit_docs": []
        }