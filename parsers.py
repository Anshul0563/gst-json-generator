# parsers.py
# FINAL WORKING VERSION (AUTO DETECT + MERGE COMPATIBLE)

import pandas as pd
from pathlib import Path


# =====================================================
# HELPERS
# =====================================================
def num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)


STATE_CODES = {
    "jammu and kashmir": "01",
    "himachal pradesh": "02",
    "punjab": "03",
    "chandigarh": "04",
    "uttarakhand": "05",
    "haryana": "06",
    "delhi": "07",
    "rajasthan": "08",
    "uttar pradesh": "09",
    "bihar": "10",
    "sikkim": "11",
    "arunachal pradesh": "12",
    "nagaland": "13",
    "manipur": "14",
    "mizoram": "15",
    "tripura": "16",
    "meghalaya": "17",
    "assam": "18",
    "west bengal": "19",
    "jharkhand": "20",
    "odisha": "21",
    "chhattisgarh": "22",
    "madhya pradesh": "23",
    "gujarat": "24",
    "maharashtra": "27",
    "karnataka": "29",
    "goa": "30",
    "kerala": "32",
    "tamil nadu": "33",
    "puducherry": "34",
    "telangana": "36",
    "andhra pradesh": "37",
    "ladakh": "38",
}


def state_to_code(v):
    if pd.isna(v):
        return "00"

    s = str(v).strip().lower()
    return STATE_CODES.get(s, "00")


def build_summary(df):
    if df.empty:
        return {
            "rows": [],
            "total_taxable": 0,
            "total_igst": 0,
            "total_cgst": 0,
            "total_sgst": 0
        }

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
        "total_sgst": float(g["sgst"].sum()),
    }


# =====================================================
# BASE
# =====================================================
class BaseParser:
    def parse_files(self, files):
        raise NotImplementedError


# =====================================================
# MEESHO
# =====================================================
class MeeshoParser(BaseParser):

    def parse_files(self, files):
        frames = []

        for file in files:
            name = Path(file).name.lower()

            if "meesho" not in name and "tax_invoice" not in name and "tcs" not in name:
                continue

            try:
                df = pd.read_excel(file)
            except:
                continue

            cols = [str(c).lower().strip() for c in df.columns]

            if "end_customer_state_new" in cols:
                df.columns = cols

                taxable_col = None
                for c in cols:
                    if "taxable" in c:
                        taxable_col = c
                        break

                tax_col = None
                for c in cols:
                    if "tax_amount" in c or c == "tax":
                        tax_col = c
                        break

                if taxable_col is None:
                    continue

                temp = pd.DataFrame()
                temp["pos"] = df["end_customer_state_new"].apply(state_to_code)
                temp["taxable_value"] = num(df[taxable_col])
                temp["igst"] = num(df[tax_col]) if tax_col else 0
                temp["cgst"] = 0
                temp["sgst"] = 0

                frames.append(temp)

        if not frames:
            raise Exception("No valid Meesho files found")

        final = pd.concat(frames, ignore_index=True)

        return {
            "platform": "Meesho",
            "etin": "29AABCM2441G1ZS",
            "summary": build_summary(final),
            "invoice_docs": [],
            "credit_docs": [],
            "debit_docs": []
        }


# =====================================================
# FLIPKART
# =====================================================
class FlipkartParser(BaseParser):

    def parse_files(self, files):
        frames = []

        for file in files:
            try:
                xls = pd.ExcelFile(file)
            except:
                continue

            for sheet in xls.sheet_names:
                if "sales" not in sheet.lower():
                    continue

                try:
                    df = pd.read_excel(file, sheet_name=sheet)
                except:
                    continue

                df.columns = [
                    str(c).lower().strip()
                    .replace(" ", "_")
                    .replace("/", "_")
                    .replace("(", "")
                    .replace(")", "")
                    for c in df.columns
                ]

                cols = df.columns.tolist()

                if "customers_delivery_state" not in cols:
                    continue

                taxable_col = None
                for c in cols:
                    if "taxable_value" in c:
                        taxable_col = c
                        break

                if taxable_col is None:
                    continue

                temp = pd.DataFrame()
                temp["pos"] = df["customers_delivery_state"].apply(state_to_code)
                temp["taxable_value"] = num(df[taxable_col])
                temp["igst"] = num(df["igst_amount"]) if "igst_amount" in cols else 0
                temp["cgst"] = num(df["cgst_amount"]) if "cgst_amount" in cols else 0
                temp["sgst"] = num(df["sgst_amount_or_utgst_as_applicable"]) if "sgst_amount_or_utgst_as_applicable" in cols else 0

                frames.append(temp)

        if not frames:
            raise Exception("No valid Flipkart files found")

        final = pd.concat(frames, ignore_index=True)

        return {
            "platform": "Flipkart",
            "etin": "07AAFCN5072P1ZV",
            "summary": build_summary(final),
            "invoice_docs": [],
            "credit_docs": [],
            "debit_docs": []
        }


# =====================================================
# AMAZON
# =====================================================
class AmazonParser(BaseParser):

    def parse_files(self, files):
        frames = []

        for file in files:
            ext = Path(file).suffix.lower()

            # try csv
            if ext == ".csv":
                try:
                    df = pd.read_csv(file, encoding="utf-8")
                except:
                    try:
                        df = pd.read_csv(file, encoding="latin1")
                    except:
                        continue

            # try excel
            elif ext in [".xlsx", ".xls"]:
                try:
                    df = pd.read_excel(file)
                except:
                    continue
            else:
                continue

            df.columns = [
                str(c).lower().strip()
                .replace(" ", "_")
                .replace("/", "_")
                for c in df.columns
            ]

            cols = df.columns.tolist()

            if "ship_to_state" not in cols:
                continue

            if "tax_exclusive_gross" not in cols:
                continue

            temp = pd.DataFrame()
            temp["pos"] = df["ship_to_state"].apply(state_to_code)
            temp["taxable_value"] = num(df["tax_exclusive_gross"])
            temp["igst"] = num(df["igst_tax"]) if "igst_tax" in cols else 0
            temp["cgst"] = num(df["cgst_tax"]) if "cgst_tax" in cols else 0
            temp["sgst"] = num(df["sgst_tax"]) if "sgst_tax" in cols else 0

            frames.append(temp)

        if not frames:
            raise Exception("No valid Amazon files found")

        final = pd.concat(frames, ignore_index=True)

        return {
            "platform": "Amazon",
            "etin": "07AAICA3918J1CV",
            "summary": build_summary(final),
            "invoice_docs": [],
            "credit_docs": [],
            "debit_docs": []
        }