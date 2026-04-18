# parsers.py
# LONG TERM V1 - PART 1

import pandas as pd
from pathlib import Path

from utils import (
    num,
    clean_cols,
    first_match,
    detect_tax_columns,
    state_to_code,
    safe_docs,
    dedupe,
    summarize,
    calculate_tax_from_taxable,
)


class BaseParser:
    def parse_files(self, files):
        raise NotImplementedError


# =====================================================
# COMMON TAX ENGINE
# =====================================================
def build_tax(raw, pos, taxable_col):
    cols = raw.columns.tolist()
    tax_cols = detect_tax_columns(cols)

    taxable = num(raw[taxable_col])

    igst_col = tax_cols["igst"]
    cgst_col = tax_cols["cgst"]
    sgst_col = tax_cols["sgst"]

    if igst_col or cgst_col or sgst_col:
        igst = num(raw[igst_col]) if igst_col else 0
        cgst = num(raw[cgst_col]) if cgst_col else 0
        sgst = num(raw[sgst_col]) if sgst_col else 0
        return taxable, igst, cgst, sgst

    return (taxable, *calculate_tax_from_taxable(pos, taxable))


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

            if not any(k in name for k in ["meesho", "tcs", "invoice"]):
                continue

            try:
                df = pd.read_excel(file)
            except:
                continue

            raw = clean_cols(df)
            cols = raw.columns.tolist()

            state_col = first_match(cols, ["state"])
            taxable_col = first_match(cols, ["taxable"])
            inv_col = first_match(cols, ["invoice"])

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

            tx, ig, cg, sg = build_tax(raw, temp["pos"], taxable_col)

            temp["taxable_value"] = tx
            temp["igst"] = ig
            temp["cgst"] = cg
            temp["sgst"] = sg

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

        final = dedupe(pd.concat(rows, ignore_index=True))

        return {
            "platform": "Meesho",
            "etin": self.ETIN,
            "summary": summarize(final),
            "invoice_docs": invoice_docs,
            "credit_docs": credit_docs,
            "debit_docs": []
        }
    # parsers.py
# LONG TERM V1 - PART 2
# Add below MeeshoParser

# =====================================================
# FLIPKART
# =====================================================
class FlipkartParser(BaseParser):
    ETIN = "07AACCF0683K1CU"

    def parse_files(self, files):
        rows = []

        for file in files:
            name = Path(file).name.lower()

            if "flipkart" not in name and "sales" not in name:
                continue

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

                tx, ig, cg, sg = build_tax(raw, temp["pos"], taxable_col)

                temp["taxable_value"] = tx
                temp["igst"] = ig
                temp["cgst"] = cg
                temp["sgst"] = sg

                temp["invoice_no"] = raw[inv_col].astype(str) if inv_col else ""
                temp["order_id"] = ""
                temp["txn_type"] = "sale"

                rows.append(temp)

        if not rows:
            raise Exception("No valid Flipkart files found")

        final = dedupe(pd.concat(rows, ignore_index=True))

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
            name = Path(file).name.lower()

            if "amazon" not in name and ext != ".csv":
                continue

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

            tx, ig, cg, sg = build_tax(raw, temp["pos"], taxable_col)

            temp["taxable_value"] = tx
            temp["igst"] = ig
            temp["cgst"] = cg
            temp["sgst"] = sg

            temp["invoice_no"] = raw[inv_col].astype(str) if inv_col else ""
            temp["order_id"] = ""
            temp["txn_type"] = "sale"

            rows.append(temp)

        if not rows:
            raise Exception("No valid Amazon files found")

        final = dedupe(pd.concat(rows, ignore_index=True))

        return {
            "platform": "Amazon",
            "etin": self.ETIN,
            "summary": summarize(final),
            "invoice_docs": [],
            "credit_docs": [],
            "debit_docs": []
        }
    # parsers.py
# LONG TERM V1 - PART 3
# Add below AmazonParser

# =====================================================
# AUTO MERGE
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
        errors = []

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

            except Exception as e:
                errors.append(
                    f"{parser.__class__.__name__}: {str(e)}"
                )

        if not results:
            raise Exception(
                "No valid marketplace data found\n\n" +
                "\n".join(errors)
            )

        return self.merge(results)

    def merge(self, results):
        state_map = {}
        clttx = []

        for item in results:
            s = item["summary"]

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

        rows = list(state_map.values())

        return {
            "summary": {
                "rows": rows,
                "total_taxable": round(sum(r["taxable_value"] for r in rows), 2),
                "total_igst": round(sum(r["igst"] for r in rows), 2),
                "total_cgst": round(sum(r["cgst"] for r in rows), 2),
                "total_sgst": round(sum(r["sgst"] for r in rows), 2),
            },
            "invoice_docs": [],
            "credit_docs": [],
            "debit_docs": [],
            "clttx": clttx
        }