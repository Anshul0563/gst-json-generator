# main.py
# FINAL ENTRY FILE

import sys
from PySide6.QtWidgets import QApplication

from ui import MainWindow
from utils import setup_logging
from gst_builder import GSTBuilder
from parsers import MeeshoParser, FlipkartParser, AmazonParser


# =====================================================
# MERGE ENGINE
# =====================================================
class MergeParser:

    def __init__(self):
        self.parsers = [
            MeeshoParser(),
            FlipkartParser(),
            AmazonParser()
        ]

    def parse_files(self, files):
        outputs = []

        for parser in self.parsers:
            try:
                data = parser.parse_files(files)

                if data["summary"]["total_taxable"] > 0:
                    outputs.append(data)

            except:
                pass

        if not outputs:
            raise Exception("No valid marketplace data found")

        return self.merge(outputs)

    def merge(self, arr):
        state_map = {}
        clttx = []

        total_taxable = 0
        total_igst = 0
        total_cgst = 0
        total_sgst = 0

        for item in arr:
            s = item["summary"]

            total_taxable += s["total_taxable"]
            total_igst += s["total_igst"]
            total_cgst += s["total_cgst"]
            total_sgst += s["total_sgst"]

            for r in s["rows"]:
                pos = r["pos"]

                if pos not in state_map:
                    state_map[pos] = {
                        "pos": pos,
                        "taxable_value": 0,
                        "igst": 0,
                        "cgst": 0,
                        "sgst": 0
                    }

                state_map[pos]["taxable_value"] += r["taxable_value"]
                state_map[pos]["igst"] += r["igst"]
                state_map[pos]["cgst"] += r["cgst"]
                state_map[pos]["sgst"] += r["sgst"]

            clttx.append({
                "etin": item["etin"],
                "suppval": round(s["total_taxable"], 2),
                "igst": round(s["total_igst"], 2),
                "cgst": round(s["total_cgst"], 2),
                "sgst": round(s["total_sgst"], 2),
                "cess": 0,
                "flag": "N"
            })

        return {
            "platform": "Merged",
            "summary": {
                "rows": list(state_map.values()),
                "total_taxable": round(total_taxable, 2),
                "total_igst": round(total_igst, 2),
                "total_cgst": round(total_cgst, 2),
                "total_sgst": round(total_sgst, 2),
            },
            "clttx": clttx
        }


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