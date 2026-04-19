# GST-Tool Flipkart Real File Fixes using ORIGINAL Data
Status: IMPLEMENTING (Phase 2/7)

## Approved Plan Steps:

### ✅ Phase 1: Analysis Complete
- Real Flipkart = Excel (Sales Report + Cash Back Report sheets)
- MTR CSV = Amazon only (no changes)
- Current mismatch: Wrong row filtering/duplicates

### 🔄 Phase 2: FlipkartParser Excel Robustness [EDITING parsers.py]
- Detect by sheet names regardless filename
- Sales Report: Event Type='SALE' + Event Sub Type='SALE'
- Cash Back: Document Type='CREDIT'/'Credit Note'
- source_key prevents duplicates
- Debug logs: row counts, totals

### ⏳ Phase 3: Edit parsers.py Complete → Test
```
cd /home/jarvis/Documents/IT/GST-Tool
python3 -c "from parsers import FlipkartParser; p=FlipkartParser(); r=p.parse_files(['test_data/flipkart_variants/1f1924de-add8-4717-8998-64952c2dc16e_1773998487000.xlsx']); print(r['summary'] if r else 'FAIL')"
```

### ⏳ Phase 4: Full test_data/ AutoMergeParser
```
python3 -c "from parsers import AutoMergeParser; p=AutoMergeParser(); r=p.parse_files(['test_data/']); print(r['summary'] if r else 'FAIL')"
```

### ⏳ Phase 5: Validate vs gst_output.json totals (Feb/March)
### ⏳ Phase 6: gst_builder.py → GSTR1 JSON
### ⏳ Phase 7: attempt_completion with proof

**Next: Edit parsers.py → FlipkartParser.read_files() + _process_sales_report() + _process_cashback_report()**

