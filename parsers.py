# parsers.py
# FULL UPDATED FINAL VERSION (LAST 1% PATCH INCLUDED)

import pandas as pd
from pathlib import Path


def num(series):
    return pd.to_numeric(series, errors="coerce").fillna(0)


STATE_CODES = {
    "delhi": "07", "new delhi": "07",
    "uttar pradesh": "09", "up": "09",
    "bihar": "10", "punjab": "03", "chandigarh": "04",
    "uttarakhand": "05", "haryana": "06", "rajasthan": "08",
    "sikkim": "11", "arunachal pradesh": "12", "nagaland": "13",
    "manipur": "14", "mizoram": "15", "tripura": "16",
    "meghalaya": "17", "assam": "18", "west bengal": "19",
    "jharkhand": "20", "odisha": "21", "orissa": "21",
    "chhattisgarh": "22", "madhya pradesh": "23", "gujarat": "24",
    "maharashtra": "27", "karnataka": "29", "goa": "30",
    "kerala": "32", "tamil nadu": "33", "puducherry": "34",
    "telangana": "36", "andhra pradesh": "37", "ladakh": "38",
}


def state_to_code(v):
    if pd.isna(v):
        return None
    s = str(v).strip().lower()
    s = " ".join(s.split())
    if s.isdigit() and len(s) == 2:
        return s
    return STATE_CODES.get(s)


def smart_make_docs(series):
    vals = series.dropna().astype(str).str.strip()
    vals = vals[vals != ""].unique().tolist()
    vals = sorted(vals)

    if not vals:
        return []

    return [{
        "from": vals[0],
        "to": vals[-1],
        "totnum": len(vals)
    }]


def build_summary(df):
    df = df[df["pos"].notna()].copy()

    df = df[
        (df["taxable_value"] != 0) |
        (df["igst"] != 0) |
        (df["cgst"] != 0) |
        (df["sgst"] != 0)
    ]

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
        "total_sgst": float(g["sgst"].sum())
    }


# =====================================================
class BaseParser:
    def parse_files(self, files):
        raise NotImplementedError


# =====================================================
class MeeshoParser(BaseParser):

    def parse_files(self, files):
        sales_df = None
        return_df = None
        invoice_df = None

        for file in files:
            name = Path(file).name.lower()

            try:
                df = pd.read_excel(file)
            except:
                continue

            if "tcs_sales_return" in name:
                return_df = df

            elif "tcs_sales" in name and "return" not in name:
                sales_df = df

            elif "tax_invoice" in name:
                invoice_df = df

        if sales_df is None:
            raise Exception("Meesho sales file missing")

        frames = []

        # SALES +
        s = sales_df.copy()
        s.columns = [str(c).lower().strip() for c in s.columns]

        temp = pd.DataFrame()
        temp["pos"] = s["end_customer_state_new"].apply(state_to_code)
        temp["taxable_value"] = num(s["total_taxable_sale_value"])

        tax_amt = num(s["tax_amount"])
        is_delhi = temp["pos"] == "07"

        temp["igst"] = tax_amt.where(~is_delhi, 0)
        temp["cgst"] = (tax_amt / 2).where(is_delhi, 0)
        temp["sgst"] = (tax_amt / 2).where(is_delhi, 0)

        frames.append(temp)

        # RETURNS -
        if return_df is not None:
            r = return_df.copy()
            r.columns = [str(c).lower().strip() for c in r.columns]

            temp = pd.DataFrame()
            temp["pos"] = r["end_customer_state_new"].apply(state_to_code)
            temp["taxable_value"] = -num(r["total_taxable_sale_value"])

            tax_amt = num(r["tax_amount"])
            is_delhi = temp["pos"] == "07"

            temp["igst"] = -(tax_amt.where(~is_delhi, 0))
            temp["cgst"] = -((tax_amt / 2).where(is_delhi, 0))
            temp["sgst"] = -((tax_amt / 2).where(is_delhi, 0))

            frames.append(temp)

        final = pd.concat(frames, ignore_index=True)

        invoice_docs = []
        credit_docs = []

        if invoice_df is not None:
            invoice_df.columns = [str(c).strip() for c in invoice_df.columns]

            if "Invoice No." in invoice_df.columns and "Type" in invoice_df.columns:
                inv = invoice_df[
                    invoice_df["Type"].astype(str).str.upper() == "INVOICE"
                ]["Invoice No."]

                crn = invoice_df[
                    invoice_df["Type"].astype(str).str.upper() != "INVOICE"
                ]["Invoice No."]

                invoice_docs = smart_make_docs(inv)
                credit_docs = smart_make_docs(crn)

        return {
            "platform": "Meesho",
            "etin": "07AARCM9332R1CQ",
            "summary": build_summary(final),
            "invoice_docs": invoice_docs,
            "credit_docs": credit_docs,
            "debit_docs": []
        }


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
                if not any(k in sheet.lower() for k in ["sales", "report", "gstr"]):
                    continue

                df = pd.read_excel(file, sheet_name=sheet)

                df.columns = [
                    str(c).lower().strip()
                    .replace(" ", "_")
                    .replace("/", "_")
                    .replace("(", "")
                    .replace(")", "")
                    for c in df.columns
                ]

                cols = df.columns.tolist()

                state_col = next((c for c in cols if "delivery_state" in c), None)
                taxable = next((c for c in cols if "taxable_value" in c), None)

                if not state_col or not taxable:
                    continue

                temp = pd.DataFrame()
                temp["pos"] = df[state_col].apply(state_to_code)
                temp["taxable_value"] = num(df[taxable])
                temp["igst"] = num(df["igst_amount"]) if "igst_amount" in cols else 0
                temp["cgst"] = num(df["cgst_amount"]) if "cgst_amount" in cols else 0
                temp["sgst"] = num(df["sgst_amount_or_utgst_as_applicable"]) if "sgst_amount_or_utgst_as_applicable" in cols else 0
                frames.append(temp)

        if not frames:
            raise Exception("No valid Flipkart files found")

        return {
            "platform": "Flipkart",
            "etin": "07AACCF0683K1CU",
            "summary": build_summary(pd.concat(frames, ignore_index=True)),
            "invoice_docs": [],
            "credit_docs": [],
            "debit_docs": []
        }


# =====================================================
class AmazonParser(BaseParser):

    def parse_files(self, files):
        frames = []

        for file in files:
            ext = Path(file).suffix.lower()

            try:
                if ext == ".csv":
                    try:
                        df = pd.read_csv(file, encoding="utf-8")
                    except:
                        df = pd.read_csv(file, encoding="latin1")
                else:
                    df = pd.read_excel(file)
            except:
                continue

            df.columns = [
                str(c).lower().strip()
                .replace(" ", "_")
                .replace("/", "_")
                for c in df.columns
            ]

            cols = df.columns.tolist()

            if "ship_to_state" not in cols or "tax_exclusive_gross" not in cols:
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

        return {
            "platform": "Amazon",
            "etin": "07AAICA3918J1CV",
            "summary": build_summary(pd.concat(frames, ignore_index=True)),
            "invoice_docs": [],
            "credit_docs": [],
            "debit_docs": []
        }