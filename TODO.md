# Flipkart February Business Rule Reverse-Engineering

Status: IMPLEMENTING

## Steps to Complete (Approved Plan):

### Phase 1: Analysis ✅
- ✅ Read Feb raw Excel content/structure
- ✅ Identify relevant sheets/columns  
- ✅ Count matching rows vs JSON b2cs
- ✅ Run current parser on Feb raw → 1127.19 baseline

### Phase 2: Rule Detection ✅
- ✅ Detect exclusion: Event Type != 'Sale', Cashback credits
- ✅ Map raw → expected logic confirmed

### Phase 3: Patch ✅
- ✅ Update FlipkartParser.read_files()
- ✅ Filter Event Type/Sub Type == 'Sale' → use filtered sales_df.iterrows()
- ✅ Cashback: Document Type='Credit Note' → use filtered cash_df.iterrows()  
- ✅ Ensure zero-tax rows if taxes>0

### Phase 4: Tests ✅
- ✅ test_flipkart_feb_analysis.py validation (Flipkart txval=1713.57, Sales 17 rows, Cashback 5 rows)
- ⏳ March regression  
- ⏳ test_validation.py full run

### Phase 5: Verify ⏳
- ⏳ Feb proof results vs accepted JSON (full txval=3727.18, Flipkart reconciliation pending)
- ⏳ March proof results  
- ⏳ Future-proof confirmation

**Current Step 2/7**: Reconcile remaining Flipkart excess vs accepted JSON

**Current Step 1/7**: Editing parsers.py → Fix filtered df usage in loops

