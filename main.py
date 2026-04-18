# main.py
# ULTIMATE FINAL AUTO MERGE VERSION

import sys
from PySide6.QtWidgets import QApplication
from ui import MainWindow
from gst_builder import GSTBuilder
from utils import setup_logging

# individual parsers
from parsers import MeeshoParser, FlipkartParser, AmazonParser


class MergeParser:
    """
    Auto detect all uploaded files
    Parse all marketplaces
    Merge final totals
    """

    def __init__(self):
        self.parsers = {
            "Meesho": MeeshoParser(),
            "Flipkart": FlipkartParser(),
            "Amazon": AmazonParser()
        }

    def parse_files(self, files):
        results = []

        # -----------------------------------
        # run all parsers safely
        # -----------------------------------
        for name, parser in self.parsers.items():
            try:
                r = parser.parse_files(files)

                # valid data only
                if r["summary"]["total_taxable"] != 0:
                    results.append(r)

            except:
                pass

        if not results:
            raise Exception("No valid marketplace data found")

        return self.merge(results)

    # =====================================
    # MERGE ALL
    # =====================================
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

            # state merge
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

            # supeco lines
            clttx.append({
                "etin": item["etin"],
                "suppval": round(s["total_taxable"], 2),
                "igst": round(s["total_igst"], 2),
                "cgst": round(s["total_cgst"], 2),
                "sgst": round(s["total_sgst"], 2),
                "cess": 0,
                "flag": "N"
            })

            # docs
            invoice_docs.extend(item.get("invoice_docs", []))
            credit_docs.extend(item.get("credit_docs", []))
            debit_docs.extend(item.get("debit_docs", []))

        merged = {
            "platform": "Merged",
            "etin": "MULTI",
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

        return merged


# =====================================================
# APP START
# =====================================================
def main():
    setup_logging()

    app = QApplication(sys.argv)
    app.setApplicationName("GST JSON Generator Pro")
    app.setOrganizationName("X10THINK")

    parsers = {
        "Auto Merge": MergeParser(),
        "Meesho": MeeshoParser(),
        "Flipkart": FlipkartParser(),
        "Amazon": AmazonParser()
    }

    builder = GSTBuilder()

    window = MainWindow(parsers, builder)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()