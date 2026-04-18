# Flipkart February Business Rule Reverse-Engineering

Status: ACTIVE

## Completed: ✅ Pending: ❌

### Phase 1: Analysis
- ❌ [ ] Read Feb raw Excel content/structure
- ❌ [ ] Identify relevant sheets/columns
- ❌ [ ] Count matching rows vs JSON b2cs (expect ~16+ raw -> 16 agg)
- ❌ [ ] Run current parser on Feb raw, get output

### Phase 2: Rule Detection
- ❌ [ ] Detect exclusion: cancelled, returns, adjustments, dupes, non-sales
- ❌ [ ] Map raw rows to JSON b2cs entries (zero/neg inclusion)

### Phase 3: Patch
- ❌ [ ] Update FlipkartParser: include zero-txval valid rows
- ❌ [ ] Add cancelled/typ filters if present
- ❌ [ ] Ensure neg/returns preserved

### Phase 4: Tests
- ❌ [ ] test_validation.py: feb_accuracy, march_regression
- ❌ [ ] Mini Feb sample data

### Phase 5: Verify
- ❌ [ ] Run tests
- ❌ [ ] Future-proof (no month hardcode)

Current: Step 1
