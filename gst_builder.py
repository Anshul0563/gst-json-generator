# gst_builder.py
# REFACTORED WITH ADVANCED PATTERNS

from typing import Dict, List, Any, Tuple


class SupplyTypeCalculator:
    """Strategy pattern for supply type calculation."""
    
    @staticmethod
    def calculate(pos: str, seller_state_code: str = "") -> Tuple[str, Dict[str, float]]:
        """Calculate supply type and tax split for a position."""
        from config import get_config
        config = get_config()
        
        pos_str = str(pos).zfill(2)
        seller_pos = str(seller_state_code).zfill(2) if seller_state_code else ""
        tax_rate = config.get('gst.default_tax_rate', 3.0)
        cgst_rate = config.get('gst.cgst_rate', 1.5)
        sgst_rate = config.get('gst.sgst_rate', 1.5)
        
        if seller_pos and pos_str == seller_pos:
            return "INTRA", {
                "cgst_rate": cgst_rate,
                "sgst_rate": sgst_rate,
                "igst_rate": 0
            }
        else:
            return "INTER", {
                "cgst_rate": 0,
                "sgst_rate": 0,
                "igst_rate": tax_rate
            }


class B2CSItemBuilder:
    """Builder pattern for B2CS items."""
    
    def __init__(self, row: Dict[str, Any], seller_state_code: str = ""):
        self.row = row
        self.seller_state_code = seller_state_code
        self.pos = str(row.get("pos", "")).zfill(2)
        self.txval = round(float(row.get("taxable_value", 0)), 2)
        self.igst = round(float(row.get("igst", 0)), 2)
        self.cgst = round(float(row.get("cgst", 0)), 2)
        self.sgst = round(float(row.get("sgst", 0)), 2)
    
    def build(self) -> Dict[str, Any]:
        """Build B2CS item."""
        sply_type, tax_info = SupplyTypeCalculator.calculate(self.pos, self.seller_state_code)
        
        from config import get_config
        config = get_config()
        tax_rate = config.get('gst.default_tax_rate', 3.0)
        
        item = {
            "sply_ty": sply_type,
            "rt": tax_rate,
            "typ": "OE",
            "pos": self.pos,
            "txval": self.txval,
            "csamt": 0  # Cess amount
        }
        
        if sply_type == "INTRA":
            item["camt"] = self.cgst if self.cgst else round(self.txval * 0.015, 2)
            item["samt"] = self.sgst if self.sgst else round(self.txval * 0.015, 2)
        else:
            item["iamt"] = self.igst if self.igst else round(self.cgst + self.sgst, 2)
        
        return item
    
    def is_valid(self) -> bool:
        """Check if item has valid data."""
        return (self.txval != 0 or self.igst != 0 or 
                self.cgst != 0 or self.sgst != 0)


class GSTBuilder:
    """Advanced GST JSON builder with design patterns."""
    
    def __init__(self):
        """Initialize builder."""
        self.version = "GST3.1.6"

    def _extract_state_code(self, gstin: str, parsed_data: Dict) -> str:
        """Resolve seller state code from GSTIN first, then parsed fallback."""
        gstin_str = str(gstin).strip().upper()
        if len(gstin_str) >= 2 and gstin_str[:2].isdigit():
            return gstin_str[:2]
        parsed_state = parsed_data.get("seller_state_code", "")
        return str(parsed_state).zfill(2) if parsed_state else ""
    
    def build_gstr1(self, parsed_data: Dict, gstin: str, period: str) -> Dict[str, Any]:
        """Build complete GSTR1 JSON."""
        summary = parsed_data.get("summary", {})
        seller_state_code = self._extract_state_code(gstin, parsed_data)
        
        return {
            "gstin": gstin.upper(),
            "fp": period,
            "version": self.version,
            "hash": "hash",
            "b2cs": self._build_b2cs(summary.get("rows", []), seller_state_code),
            "supeco": {
                "clttx": parsed_data.get("clttx", [])
            },
            "doc_issue": parsed_data.get("doc_issue", {"doc_det": []}),
            "summary": self._build_summary(summary)
        }
    
    def _build_b2cs(self, rows: List[Dict], seller_state_code: str) -> List[Dict]:
        """Build B2CS (Business to Consumer Supply) items."""
        items = []
        
        for row in rows:
            builder = B2CSItemBuilder(row, seller_state_code)
            
            if not builder.is_valid():
                continue
            
            items.append(builder.build())
        
        return items
    
    def _build_summary(self, summary: Dict) -> Dict[str, Any]:
        """Build summary statistics."""
        return {
            "total_items": len(summary.get("rows", [])),
            "total_taxable": round(summary.get("total_taxable", 0), 2),
            "total_igst": round(summary.get("total_igst", 0), 2),
            "total_cgst": round(summary.get("total_cgst", 0), 2),
            "total_sgst": round(summary.get("total_sgst", 0), 2),
            "total_tax": round(
                summary.get("total_igst", 0) + 
                summary.get("total_cgst", 0) + 
                summary.get("total_sgst", 0),
                2
            )
        }
    
    def validate_output(self, output: Dict) -> Tuple[bool, List[str]]:
        """Validate output JSON structure."""
        errors = []
        
        # Check required fields
        required_fields = ["gstin", "fp", "version", "b2cs", "supeco"]
        for field in required_fields:
            if field not in output:
                errors.append(f"Missing required field: {field}")
        
        # Validate GSTIN
        if output.get("gstin"):
            if not str(output["gstin"]).isalnum() or len(output["gstin"]) < 10:
                errors.append("Invalid GSTIN in output")
        
        # Validate period
        if output.get("fp"):
            period = str(output["fp"])
            if not (len(period) == 6 and period.isdigit()):
                errors.append("Invalid period in output")
        
        # Validate B2CS items
        b2cs = output.get("b2cs", [])
        for i, item in enumerate(b2cs):
            if not all(k in item for k in ["sply_ty", "rt", "pos", "txval"]):
                errors.append(f"Invalid B2CS item at index {i}")
        
        return len(errors) == 0, errors
