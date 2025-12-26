# Period-Only Mode Implementation Plan

## Overview

Implement a period-only mode where Floyd's algorithm can demonstrate its true O(1) space advantage. This mode will compute periods without storing full sequences, making Floyd's algorithm actually useful.

## Goals

1. Add `--period-only` CLI flag
2. Make enumeration the default algorithm (Floyd kept for educational/period-only use)
3. Implement true O(1) space Floyd for period-only mode
4. Add period-only variants of algorithms
5. Update performance profiling to show Floyd's advantages in period-only mode
6. Maintain backward compatibility

## Implementation Plan

### Phase 1: Core Algorithm Changes

#### 1.1 Create Period-Only Functions

**New Functions:**
- `_find_period_floyd()` - True O(1) space, returns only period
- `_find_period_enumeration()` - Finds period by enumeration but doesn't store sequence
- `_find_period()` - Dispatcher function

**Location:** `lfsr/analysis.py`

**Implementation:**
```python
def _find_period_floyd(start_state, state_update_matrix) -> int:
    """
    Find period using Floyd's algorithm in true O(1) space.
    Returns only the period, not the sequence.
    """
    # Phase 1: Find meeting point
    # Phase 2: Find period
    # NO enumeration phase - this is the key difference
    
def _find_period_enumeration(start_state, state_update_matrix) -> int:
    """
    Find period by enumeration without storing sequence.
    Uses O(1) extra space (just counters), but O(period) time.
    """
    # Enumerate until cycle completes, but don't store states
    # Only count steps
```

#### 1.2 Update Existing Functions

**Modify `_find_sequence_cycle()`:**
- Add `period_only: bool = False` parameter
- When `period_only=True`, call period-only functions
- When `period_only=False`, use existing sequence-storing functions

**Modify `lfsr_sequence_mapper()`:**
- Add `period_only: bool = False` parameter
- When `period_only=True`:
  - Don't store sequences in `seq_dict`
  - Only store periods in `period_dict`
  - Skip sequence formatting/display

### Phase 2: CLI Changes

#### 2.1 Add `--period-only` Flag

**Location:** `lfsr/cli.py`

**Changes:**
```python
parser.add_argument(
    "--period-only",
    action="store_true",
    help="Compute periods only, without storing sequences (O(1) space for Floyd)"
)

parser.add_argument(
    "--algorithm",
    choices=["floyd", "enumeration", "auto"],
    default="auto",  # Will change to enumeration
    help="Cycle detection algorithm (default: enumeration for full mode, floyd for period-only)"
)
```

#### 2.2 Update Default Algorithm

- Change default from `"auto"` (which used Floyd) to `"enumeration"`
- When `--period-only` is used, suggest Floyd as better option
- Update help text accordingly

#### 2.3 Pass Parameters Through

**Update `main()` function:**
- Add `period_only: bool = False` parameter
- Pass to `lfsr_sequence_mapper()`

**Update `cli_main()`:**
- Extract `period_only` from args
- Pass to `main()`

### Phase 3: Performance Profiling Updates

#### 3.1 Update `performance_profile.py`

**Add period-only profiling:**
- New function: `profile_period_only_algorithms()`
- Compare:
  - `_find_period_floyd()` - should be O(1) space
  - `_find_period_enumeration()` - O(1) space but slower
- Measure:
  - Time for period finding only
  - Memory usage (Floyd should be constant)
  - Space complexity verification

**Add comparison mode:**
```bash
python3 scripts/performance_profile.py strange.csv 2 --period-only -n 10
```

#### 3.2 Create Performance Report

**Show:**
- Period-only mode: Floyd is faster and O(1) space
- Full sequence mode: Enumeration is faster
- Clear demonstration of when Floyd is actually beneficial

### Phase 4: Documentation Updates

#### 4.1 Update User Guide

- Document `--period-only` flag
- Explain when to use period-only vs full mode
- Update algorithm recommendations:
  - Full mode: Use enumeration (default)
  - Period-only mode: Use Floyd (better performance)

#### 4.2 Update API Documentation

- Document new period-only functions
- Explain space complexity differences
- Show when each algorithm is appropriate

#### 4.3 Update Mathematical Background

- Clarify that Floyd's O(1) space applies to period-only mode
- Explain why full sequence mode can't benefit from O(1) space

### Phase 5: Testing

#### 5.1 Unit Tests

- Test `_find_period_floyd()` returns correct period
- Test `_find_period_enumeration()` returns correct period
- Test period-only mode produces same periods as full mode
- Test memory usage in period-only mode

#### 5.2 Integration Tests

- Test `--period-only` CLI flag
- Test algorithm selection in period-only mode
- Test output format (should not include sequences)

#### 5.3 Performance Tests

- Verify Floyd is O(1) space in period-only mode
- Verify Floyd is faster in period-only mode
- Compare with enumeration in period-only mode

## Implementation Steps

### Step 1: Implement Period-Only Functions
1. Create `_find_period_floyd()` - true O(1) space
2. Create `_find_period_enumeration()` - O(1) space enumeration
3. Create `_find_period()` dispatcher
4. Add unit tests

### Step 2: Update Sequence Functions
1. Add `period_only` parameter to `_find_sequence_cycle()`
2. Add `period_only` parameter to `lfsr_sequence_mapper()`
3. Update logic to skip sequence storage when `period_only=True`
4. Update output formatting

### Step 3: Update CLI
1. Add `--period-only` flag
2. Change default algorithm to enumeration
3. Update help text
4. Pass parameters through

### Step 4: Update Performance Profiling
1. Add period-only profiling functions
2. Update script to support `--period-only` mode
3. Generate comparison reports

### Step 5: Update Documentation
1. Update user guide
2. Update API docs
3. Update mathematical background
4. Add examples

### Step 6: Testing & Validation
1. Run unit tests
2. Run integration tests
3. Run performance tests
4. Verify Floyd's advantages in period-only mode

## Expected Outcomes

### Period-Only Mode Performance

**Floyd (`--period-only --algorithm floyd`):**
- Time: O(period) - same as enumeration
- Space: O(1) - constant, independent of period
- Memory: ~constant (just two pointers)

**Enumeration (`--period-only --algorithm enumeration`):**
- Time: O(period) - same as Floyd
- Space: O(1) - doesn't store sequence, just counts
- Memory: ~constant (just counters)

**Comparison:**
- Floyd should be faster (fewer operations, better cache behavior)
- Both are O(1) space in period-only mode
- Floyd demonstrates its theoretical advantage

### Full Sequence Mode Performance

**Enumeration (default):**
- Time: O(period)
- Space: O(period) - stores sequence
- Faster than Floyd (no overhead)

**Floyd:**
- Time: ~3×O(period) - Phase 1 + Phase 2 + enumeration
- Space: O(period) - stores sequence
- Slower than enumeration

## Success Criteria

1. ✅ `--period-only` flag works correctly
2. ✅ Enumeration is default for full mode
3. ✅ Floyd shows O(1) space in period-only mode
4. ✅ Floyd is faster than enumeration in period-only mode
5. ✅ Performance profiling demonstrates advantages
6. ✅ Documentation is updated
7. ✅ Backward compatibility maintained

## Files to Modify

1. `lfsr/analysis.py` - Add period-only functions
2. `lfsr/cli.py` - Add `--period-only` flag, change default
3. `scripts/performance_profile.py` - Add period-only profiling
4. `docs/user_guide.rst` - Document new flag
5. `docs/api/analysis.rst` - Document new functions
6. `docs/mathematical_background.rst` - Update complexity claims
7. `tests/test_analysis.py` - Add period-only tests

## Timeline Estimate

- Step 1: 2-3 hours (period-only functions)
- Step 2: 2-3 hours (update sequence functions)
- Step 3: 1-2 hours (CLI changes)
- Step 4: 2-3 hours (performance profiling)
- Step 5: 1-2 hours (documentation)
- Step 6: 2-3 hours (testing)

**Total: ~10-16 hours**
