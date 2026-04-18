
from collections import OrderedDict


class GSTBuilder:

    def build_gstr1(self, parsed_data, gstin, period):
        s = parsed_data["summary"]

        root = OrderedDict()
        root["gstin"] = gstin
        root["fp"] = period
        root["version"] = "GST3.1.6"
        root["hash"] = "hash"
        root["b2cs"] = self.build_b2cs(s["rows"])
        root["supeco"] = OrderedDict()
        root["supeco"]["clttx"] = parsed_data["clttx"]
        root["doc_issue"] = OrderedDict()
        root["doc_issue"]["doc_det"] = self.build_docs(parsed_data)

        return root

    # =====================================================
    def build_b2cs(self, rows):
        out = []

        for r in rows:
            pos = str(r["pos"]).zfill(2)

            tx = round(float(r["taxable_value"]), 2)
            ig = round(float(r["igst"]), 2)
            cg = round(float(r["cgst"]), 2)
            sg = round(float(r["sgst"]), 2)

            # skip zero rows exactly
            if tx == 0 and ig == 0 and cg == 0 and sg == 0:
                continue

            row = OrderedDict()

            if pos == "07":
                row["sply_ty"] = "INTRA"
                row["rt"] = 3
                row["typ"] = "OE"
                row["pos"] = pos
                row["txval"] = tx
                row["camt"] = cg
                row["samt"] = sg
                row["csamt"] = 0
            else:
                row["sply_ty"] = "INTER"
                row["rt"] = 3
                row["typ"] = "OE"
                row["pos"] = pos
                row["txval"] = tx
                row["iamt"] = ig if ig else round(cg + sg, 2)
                row["csamt"] = 0

            out.append(row)

        return out

    # =====================================================
    def build_docs(self, data):
        final = []

        inv = self.make_section(
            1,
            "Invoices for outward supply",
            data.get("invoice_docs", [])
        )
        if inv:
            final.append(inv)

        cr = self.make_section(
            5,
            "Credit Note",
            data.get("credit_docs", [])
        )
        if cr:
            final.append(cr)

        dr = self.make_section(
            4,
            "Debit Note",
            data.get("debit_docs", [])
        )
        if dr:
            final.append(dr)

        return final

    # =====================================================
    def make_section(self, doc_num, doc_typ, docs):
        clean = []

        for i, d in enumerate(docs, start=1):
            qty = int(d["totnum"])

            row = OrderedDict()
            row["num"] = i
            row["from"] = str(d["from"])
            row["to"] = str(d["to"])
            row["totnum"] = qty
            row["cancel"] = 0
            row["net_issue"] = qty

            clean.append(row)

        if not clean:
            return None

        block = OrderedDict()
        block["doc_num"] = doc_num
        block["doc_typ"] = doc_typ
        block["docs"] = clean

        return block