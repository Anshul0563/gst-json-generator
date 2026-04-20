# GST Tool Parser Fix TODO

## Plan Steps:
- [ ] Step 1: Create TODO.md (current)
- [ ] Step 2: Rewrite parsers.py with full fixes
  - Full STATE_MAP 01-38 + aliases (ODISHA=21 etc.)
  - Robust col detection with all candidates
  - Encoding: UTF-8 then latin1
  - Skip zero rows (txval==0 and all taxes==0)
  - Dedup by (invoice_no + pos + txval + supplier_etin)
  - Handle cancels/refunds: preserve neg if values, skip zero
  - Auto-detect files: Amazon/MTR CSV, Meesho/TCS Excel/CSV
  - Ignore Flipkart
  - Output exact merged_rows format
- [ ] Step 3: Test parsing on test_data files
- [ ] Step 4: Update TODO on completion
- [ ] Step 5: Attempt completion

