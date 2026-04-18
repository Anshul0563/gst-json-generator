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