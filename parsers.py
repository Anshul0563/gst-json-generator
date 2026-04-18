# parsers.py
# ULTIMATE REBUILD - CORE ENGINE PART 1

import pandas as pd
from pathlib import Path

from utils import (
    num,
    clean_cols,
    state_to_code,
    first_match,
    safe_docs,
    remove_duplicates,
    summarize,
)


class BaseParser:
    def parse_files(self, files):
        raise NotImplementedError


# =====================================================
# MEESHO
# =====================================================
class MeeshoParser(BaseParser):

    ETIN = "07AARCM9332R1CQ"

    def parse_files(self, files):
        rows = []
        invoice_docs = []
        credit_docs = []

        for file in files:
            name = Path(file).name.lower()

            if "meesho" not in name and "tcs" not in name and "invoice" not in name:
                continue

            try:
                df = pd.read_excel(file)
            except:
                continue

            raw = clean_cols(df)
            cols = raw.columns.tolist()

            state_col = first_match(cols, ["state"])
            taxable_col = first_match(cols, ["taxable"])
            tax_col = first_match(cols, ["tax_amount", "tax"])
            inv_col = first_match(cols, ["invoice_no", "invoice"])

            # docs only file
            if "invoice" in name and taxable_col is None:
                if inv_col:
                    invoice_docs.extend(safe_docs(raw[inv_col]))
                continue

            if not state_col or not taxable_col:
                continue

            temp = pd.DataFrame()
            temp["platform"] = "Meesho"
            temp["pos"] = raw[state_col].apply(state_to_code)
            temp["taxable_value"] = num(raw[taxable_col])

            tax_amt = num(raw[tax_col]) if tax_col else 0
            is_delhi = temp["pos"] == "07"

            temp["igst"] = tax_amt.where(~is_delhi, 0)
            temp["cgst"] = (tax_amt / 2).where(is_delhi, 0)
            temp["sgst"] = (tax_amt / 2).where(is_delhi, 0)

            temp["invoice_no"] = raw[inv_col].astype(str) if inv_col else ""
            temp["order_id"] = ""
            temp["txn_type"] = "sale"

            if "return" in name:
                temp["taxable_value"] *= -1
                temp["igst"] *= -1
                temp["cgst"] *= -1
                temp["sgst"] *= -1
                temp["txn_type"] = "return"
                if inv_col:
                    credit_docs.extend(safe_docs(raw[inv_col]))

            rows.append(temp)

        if not rows:
            raise Exception("No valid Meesho files found")

        final = pd.concat(rows, ignore_index=True)
        final = remove_duplicates(final)

        return {
            "platform": "Meesho",
            "etin": self.ETIN,
            "summary": summarize(final),
            "invoice_docs": invoice_docs,
            "credit_docs": credit_docs,
            "debit_docs": []
        }

# =====================================================
# FLIPKART
# =====================================================
class FlipkartParser(BaseParser):

    ETIN = "07AACCF0683K1CU"

    def parse_files(self, files):
        rows = []

        for file in files:
            try:
                xls = pd.ExcelFile(file)
            except:
                continue

            for sheet in xls.sheet_names:
                try:
                    df = pd.read_excel(file, sheet_name=sheet)
                except:
                    continue

                raw = clean_cols(df)
                cols = raw.columns.tolist()

                state_col = first_match(cols, ["delivery_state", "state"])
                taxable_col = first_match(cols, ["taxable_value", "taxable"])
                inv_col = first_match(cols, ["invoice"])

                if not state_col or not taxable_col:
                    continue

                temp = pd.DataFrame()
                temp["platform"] = "Flipkart"
                temp["pos"] = raw[state_col].apply(state_to_code)
                temp["taxable_value"] = num(raw[taxable_col])
                temp["igst"] = num(raw["igst_amount"]) if "igst_amount" in cols else 0
                temp["cgst"] = num(raw["cgst_amount"]) if "cgst_amount" in cols else 0
                temp["sgst"] = num(raw["sgst_amount_or_utgst_as_applicable"]) if "sgst_amount_or_utgst_as_applicable" in cols else 0
                temp["invoice_no"] = raw[inv_col].astype(str) if inv_col else ""
                temp["order_id"] = ""
                temp["txn_type"] = "sale"

                rows.append(temp)

        if not rows:
            raise Exception("No valid Flipkart files found")

        final = pd.concat(rows, ignore_index=True)
        final = remove_duplicates(final)

        return {
            "platform": "Flipkart",
            "etin": self.ETIN,
            "summary": summarize(final),
            "invoice_docs": [],
            "credit_docs": [],
            "debit_docs": []
        }


# =====================================================
# AMAZON
# =====================================================
class AmazonParser(BaseParser):

    ETIN = "07AAICA3918J1CV"

    def parse_files(self, files):
        rows = []

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

            raw = clean_cols(df)
            cols = raw.columns.tolist()

            state_col = first_match(cols, ["ship_to_state", "state"])
            taxable_col = first_match(cols, ["tax_exclusive_gross", "taxable"])
            inv_col = first_match(cols, ["invoice"])

            if not state_col or not taxable_col:
                continue

            temp = pd.DataFrame()
            temp["platform"] = "Amazon"
            temp["pos"] = raw[state_col].apply(state_to_code)
            temp["taxable_value"] = num(raw[taxable_col])
            temp["igst"] = num(raw["igst_tax"]) if "igst_tax" in cols else 0
            temp["cgst"] = num(raw["cgst_tax"]) if "cgst_tax" in cols else 0
            temp["sgst"] = num(raw["sgst_tax"]) if "sgst_tax" in cols else 0
            temp["invoice_no"] = raw[inv_col].astype(str) if inv_col else ""
            temp["order_id"] = ""
            temp["txn_type"] = "sale"

            rows.append(temp)

        if not rows:
            raise Exception("No valid Amazon files found")

        final = pd.concat(rows, ignore_index=True)
        final = remove_duplicates(final)

        return {
            "platform": "Amazon",
            "etin": self.ETIN,
            "summary": summarize(final),
            "invoice_docs": [],
            "credit_docs": [],
            "debit_docs": []
        }

# =====================================================
# AUTO MERGE PARSER
# =====================================================
class AutoMergeParser(BaseParser):

    def __init__(self):
        self.parsers = [
            MeeshoParser(),
            FlipkartParser(),
            AmazonParser()
        ]

    def parse_files(self, files):
        results = []

        for parser in self.parsers:
            try:
                data = parser.parse_files(files)

                s = data["summary"]
                total = (
                    s["total_taxable"] +
                    s["total_igst"] +
                    s["total_cgst"] +
                    s["total_sgst"]
                )

                if total != 0:
                    results.append(data)

            except:
                pass

        if not results:
            raise Exception("No valid marketplace data found")

        return self.merge(results)

    def merge(self, results):
        state_map = {}
        clttx = []
        invoice_docs = []
        credit_docs = []
        debit_docs = []

        total_taxable = 0
        total_igst = 0
        total_cgst = 0
        total_sgst = 0

        for item in results:
            s = item["summary"]

            total_taxable += s["total_taxable"]
            total_igst += s["total_igst"]
            total_cgst += s["total_cgst"]
            total_sgst += s["total_sgst"]

            invoice_docs.extend(item.get("invoice_docs", []))
            credit_docs.extend(item.get("credit_docs", []))
            debit_docs.extend(item.get("debit_docs", []))

            clttx.append({
                "etin": item["etin"],
                "suppval": round(s["total_taxable"], 2),
                "igst": round(s["total_igst"], 2),
                "cgst": round(s["total_cgst"], 2),
                "sgst": round(s["total_sgst"], 2),
                "cess": 0,
                "flag": "N"
            })

            for row in s["rows"]:
                pos = row["pos"]

                if pos not in state_map:
                    state_map[pos] = {
                        "pos": pos,
                        "taxable_value": 0,
                        "igst": 0,
                        "cgst": 0,
                        "sgst": 0
                    }

                state_map[pos]["taxable_value"] += row["taxable_value"]
                state_map[pos]["igst"] += row["igst"]
                state_map[pos]["cgst"] += row["cgst"]
                state_map[pos]["sgst"] += row["sgst"]

        return {
            "summary": {
                "rows": list(state_map.values()),
                "total_taxable": round(total_taxable, 2),
                "total_igst": round(total_igst, 2),
                "total_cgst": round(total_cgst, 2),
                "total_sgst": round(total_sgst, 2),
            },
            "invoice_docs": invoice_docs,
            "credit_docs": credit_docs,
            "debit_docs": debit_docs,
            "clttx": clttx
        }