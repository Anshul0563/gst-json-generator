# gst_builder.py
# FULL UPDATED SAFE VERSION

class GSTBuilder:

    def build_gstr1(self, parsed_data, gstin, period):
        summary = parsed_data["summary"]

        return {
            "gstin": gstin,
            "fp": period,
            "version": "GST3.1.6",
            "hash": "hash",
            "b2cs": self.build_b2cs(summary["rows"]),
            "supeco": {
                "clttx": parsed_data["clttx"]
            },
            "doc_issue": {
                "doc_det": []
            }
        }

    # =====================================================
    def build_b2cs(self, rows):
        result = []

        for row in rows:
            pos = str(row["pos"]).zfill(2)

            txval = round(float(row["taxable_value"]), 2)
            igst = round(float(row["igst"]), 2)
            cgst = round(float(row["cgst"]), 2)
            sgst = round(float(row["sgst"]), 2)

            # skip zero rows
            if txval == 0 and igst == 0 and cgst == 0 and sgst == 0:
                continue

            # Delhi = INTRA
            if pos == "07":
                item = {
                    "sply_ty": "INTRA",
                    "rt": 3,
                    "typ": "OE",
                    "pos": pos,
                    "txval": txval,
                    "camt": cgst,
                    "samt": sgst,
                    "csamt": 0
                }

            else:
                item = {
                    "sply_ty": "INTER",
                    "rt": 3,
                    "typ": "OE",
                    "pos": pos,
                    "txval": txval,
                    "iamt": igst if igst else round(cgst + sgst, 2),
                    "csamt": 0
                }

            result.append(item)

        return result