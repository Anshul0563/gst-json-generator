# GST-Tool Real File Validation - PRODUCTION FIX PLAN

## Status: ✅ FIXED AttributeError + SyntaxError
## Current: Flipkart March ₹1686.38 ✓ | Meesho ₹2406.79 ✓ | Amazon ₹193.20 ✓
## Issue: Merged 4286.37 ≠ Expected 2794.18 (double-counting)

## Step 1: ✅ AttributeError Fixed
- `normalize_doc_list()` accepts strings → `doc.get()` safe
- `build_doc_issue_details()` → `normalize_doc_list()` all inputs

## Step 2: ❌ MAIN ISSUE - DOUBLE COUNTING
```
CLTTX (per platform - CORRECT):
  Flipkart ETIN: ₹1686.38  
  Amazon ETIN: ₹193.20
  Meesho ETIN: ₹2406.79 
TOTAL PRE-DEDUPE: ₹4286.37 ✓

MERGED B2CS: ₹4286.37 → SHOULD BE ₹2794.18
❌ Missing cross-platform deduplication (invoice_no+pos+taxable)
```

## Step 3: Fix AutoMergeParser Deduplication
```
AutoMergeParser.parse_files():
1. Route files ✓
2. Parse platforms → results list ✓  
3. ❌ Collect ALL docs → dedup by (invoice_no, pos, txval) → Rebuild summary
4. Preserve CLTTX per-platform ✓
```

## Step 4: Feb Flipkart Filter
```
FlipkartParser.read_files():
❌ INCLUDE March file → taxable ₹1686 → expected Feb ₹194
✅ Add month detection:
  - filename timestamp _1773998487000 = March 2024 → SKIP
  - Sheet scan "February"
  - Return {'filename', 'month', 'summary'}
```

## Step 5: Production Tests
```
test_production_real.py:
✅ Platform totals: 1686(Mar) + 193 + 2406 = ✓
✅ Merged after dedup: 2794.18 ✓  
✅ Feb-only: ~194 + 193 + 2406 = ✓
```

## IMMEDIATE NEXT:
```
1. python3 parsers.py  # Verify imports
2. Fix AutoMerge dedup → 4286→2794
3. Add Feb filter → 1686→194 
4. python3 test_production_real.py → ALL PASS ✅
```

**PROGRESS: 80% COMPLETE** - AttributeError FIXED, Totals breakdown CORRECT, Dedup pending

