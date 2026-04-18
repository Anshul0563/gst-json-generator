
class GSTBuilder:

    def build_gstr1(self, parsed_data, gstin, period):
        s = parsed_data["summary"]

        return {
            "gstin": gstin,
            "fp": period,
            "version": "GST3.1.6",
            "hash": "hash",
            "b2cs": self.build_b2cs(s["rows"]),
            "supeco": {
                "clttx": parsed_data["clttx"]
            },
            "doc_issue": {
                "doc_det": self.build_docs(parsed_data)
            }
        }

    # =====================================================
    def build_b2cs(self, rows):
        out = []

        for r in rows:
            pos = str(r["pos"]).zfill(2)

            tx = round(float(r["taxable_value"]), 2)
            ig = round(float(r["igst"]), 2)
            cg = round(float(r["cgst"]), 2)
            sg = round(float(r["sgst"]), 2)

            if pos == "07":
                row = {
                    "sply_ty": "INTRA",
                    "rt": 3,
                    "typ": "OE",
                    "pos": pos,
                    "txval": tx,
                    "camt": cg,
                    "samt": sg,
                    "csamt": 0
                }
            else:
                row = {
                    "sply_ty": "INTER",
                    "rt": 3,
                    "typ": "OE",
                    "pos": pos,
                    "txval": tx,
                    "iamt": ig if ig else round(cg + sg, 2),
                    "csamt": 0
                }

            out.append(row)

        return out

    # =====================================================
    def build_docs(self, data):
        final = []

        # invoices
        if data.get("invoice_docs"):
            final.append({
                "doc_num": 1,
                "doc_typ": "Invoices for outward supply",
                "docs": self.make_rows(data["invoice_docs"])
            })

        # credit note
        if data.get("credit_docs"):
            final.append({
                "doc_num": 5,
                "doc_typ": "Credit Note",
                "docs": self.make_rows(data["credit_docs"])
            })

        # debit note
        if data.get("debit_docs"):
            final.append({
                "doc_num": 4,
                "doc_typ": "Debit Note",
                "docs": self.make_rows(data["debit_docs"])
            })

        return final

    # =====================================================
    def make_rows(self, docs):
        rows = []

        for i, d in enumerate(docs, start=1):
            qty = int(d["totnum"])

            rows.append({
                "num": i,
                "from": d["from"],
                "to": d["to"],
                "totnum": qty,
                "cancel": 0,
                "net_issue": qty
            })

        return rows