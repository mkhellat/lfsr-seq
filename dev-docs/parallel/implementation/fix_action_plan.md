# Fix Action Plan for Parallel Execution Issues

**Issues Identified**:
1. Correctness bug: Deduplication failure with 4+ workers
2. Performance degradation: 4+ workers slower than 2 workers due to load imbalance

---

## Issue #1: Deduplication Bug (CRITICAL)

### Problem
- **Symptom**: 4+ workers produce incorrect results (period sum 12286/24571 instead of 4096)
- **Root Cause**: `_merge_parallel_results` uses incomplete min_state for deduplication
- **Details**: 
 - Workers compute min_state from first 1000 states only (to avoid hangs)
 - For large cycles (period > 1000), different workers compute different min_states
 - Merge function treats them as different cycles → duplicates

### Solution Options

#### Option A: Full Min_State Computation (Risky)
- Compute min_state from ALL states in cycle
- **Pros**: Accurate deduplication
- **Cons**: May cause hangs for very large cycles (65535 states)

#### Option B: Improved Deduplication Key (Recommended)
- Use multiple signatures: (period, min_state_from_first_1000, hash_of_cycle_start)
- **Pros**: More robust, doesn't require full cycle iteration
- **Cons**: Still might have collisions (rare)

#### Option C: Shared Registry in Merge (Best)
- Use the same `shared_cycles` registry that workers use
- Workers already claim cycles correctly
- Merge should only deduplicate cycles NOT in shared_cycles
- **Pros**: Leverages existing infrastructure, most accurate
- **Cons**: Need to pass shared_cycles to merge function

---

## Issue #2: Load Imbalance (PERFORMANCE)

### Problem
- **Symptom**: 4+ workers slower than 2 workers (load imbalance 400-582%)
- **Root Cause**: Work not evenly distributed - one worker does most work
- **Details**:
 - Large cycles span multiple chunks
 - Only one worker claims each cycle
 - Other workers in those chunks have little work
 - Result: Poor load balancing

### Solution Options

#### Option A: Dynamic Work Stealing (Complex)
- Workers steal work from others when idle
- **Pros**: Optimal load balancing
- **Cons**: Complex implementation, significant refactoring

#### Option B: Better Partitioning Strategy (Moderate)
- Partition by cycle, not by state index
- **Pros**: Better load distribution
- **Cons**: Requires knowing cycles before processing (chicken-and-egg)

#### Option C: Accept Limitation (Pragmatic)
- Document that 2 workers is optimal for small-medium problems
- Auto-select optimal worker count based on problem size
- **Pros**: Simple, no code changes needed
- **Cons**: Doesn't fix the issue, just works around it

#### Option D: Chunk Size Optimization (Simple)
- Use fewer, larger chunks for small problems
- Auto-adjust chunk size based on state space size
- **Pros**: Simple, might help
- **Cons**: Less parallelism, might not fully solve imbalance

---

## Recommended Action Plan

### Phase 1: Fix Correctness Bug (CRITICAL - Must Fix)

**Priority**: HIGH 
**Estimated Time**: 2-3 hours

#### Task 1.1: Fix Deduplication in `_merge_parallel_results`
- **File**: `lfsr/analysis.py`
- **Function**: `_merge_parallel_results` (line ~756)
- **Action**: 
 - Option C: Use shared_cycles registry from workers
 - Pass shared_cycles to merge function
 - Only deduplicate cycles not already in shared_cycles
 - This ensures merge uses same deduplication logic as workers

#### Task 1.2: Update Function Signature
- **File**: `lfsr/analysis.py`
- **Function**: `_merge_parallel_results`
- **Action**: Add `shared_cycles` parameter
- **Caller**: `lfsr_sequence_mapper_parallel` (line ~1543)

#### Task 1.3: Test Correctness
- **File**: `scripts/investigate_parallel_correctness.py`
- **Action**: Verify 4+ workers now produce correct results
- **Success Criteria**: Period sum matches sequential for all worker counts

---

### Phase 2: Improve Load Balancing (PERFORMANCE - Should Fix)

**Priority**: MEDIUM 
**Estimated Time**: 4-6 hours

#### Task 2.1: Analyze Work Distribution
- **Action**: Add detailed profiling to measure:
 - Actual work per worker (states processed, cycles found)
 - Time spent waiting vs working
 - Lock contention metrics
- **Goal**: Understand exact cause of imbalance

#### Task 2.2: Implement Chunk Size Optimization
- **File**: `lfsr/analysis.py`
- **Function**: `_partition_state_space` or `lfsr_sequence_mapper_parallel`
- **Action**: 
 - For small problems (< 10K states), use fewer workers
 - Auto-select optimal worker count: `min(num_workers, optimal_count)`
 - Formula: `optimal_count = max(1, min(num_workers, state_space_size // 2000))`
- **Rationale**: Larger chunks = better load distribution

#### Task 2.3: Add Worker Count Auto-Selection
- **File**: `lfsr/analysis.py`
- **Function**: `lfsr_sequence_mapper_parallel`
- **Action**: 
 - If `num_workers` is None, auto-select based on problem size
 - Small (< 4K states): 1-2 workers
 - Medium (4K-16K): 2-4 workers
 - Large (> 16K): Use all available workers
- **Goal**: Prevent user from selecting too many workers for small problems

#### Task 2.4: Test Performance
- **Action**: Re-run profiling with optimized worker counts
- **Success Criteria**: 4+ workers should not be slower than 2 workers

---

### Phase 3: Documentation and Validation

**Priority**: LOW 
**Estimated Time**: 1-2 hours

#### Task 3.1: Update Documentation
- **Files**: `README.md`, `docs/`
- **Action**: Document:
 - Optimal worker counts for different problem sizes
 - Known limitations (load imbalance with many workers)
 - Correctness guarantees

#### Task 3.2: Add Performance Benchmarks
- **File**: `scripts/benchmark_parallel.py`
- **Action**: Create automated benchmark suite
- **Goal**: Track performance across different configurations

#### Task 3.3: Final Validation
- **Action**: Run full test suite
- **Success Criteria**: 
 - All correctness tests pass
 - Performance is acceptable
 - No regressions

---

## Detailed Todo List

### Critical (Must Fix)
- [ ] **TODO-1**: Fix deduplication in `_merge_parallel_results` to use shared_cycles registry
- [ ] **TODO-2**: Update `_merge_parallel_results` signature to accept shared_cycles
- [ ] **TODO-3**: Pass shared_cycles from `lfsr_sequence_mapper_parallel` to merge function
- [ ] **TODO-4**: Test correctness with 4+ workers (verify period sum matches)

### Important (Should Fix)
- [ ] **TODO-5**: Add work distribution profiling to understand load imbalance
- [ ] **TODO-6**: Implement chunk size optimization (fewer workers for small problems)
- [ ] **TODO-7**: Add auto-selection of optimal worker count based on problem size
- [ ] **TODO-8**: Test performance improvements with optimized worker counts

### Nice to Have
- [ ] **TODO-9**: Update documentation with optimal worker count guidelines
- [ ] **TODO-10**: Create automated benchmark suite
- [ ] **TODO-11**: Add performance regression tests

---

## Implementation Order

1. **First**: Fix correctness bug (TODO-1 to TODO-4)
 - This is critical - incorrect results are unacceptable
 - Estimated: 2-3 hours

2. **Second**: Improve load balancing (TODO-5 to TODO-8)
 - This improves performance but correctness is more important
 - Estimated: 4-6 hours

3. **Third**: Documentation and validation (TODO-9 to TODO-11)
 - Ensures long-term maintainability
 - Estimated: 1-2 hours

---

## Success Criteria

### Correctness
- All worker counts (1, 2, 4, 8) produce correct results
- Period sum matches sequential for all configurations
- No duplicate cycles in results

### Performance
- 2 workers remains optimal for 12-bit LFSR
- 4+ workers are not slower than 2 workers (or at least not significantly)
- Load imbalance < 100% for all worker counts

### Code Quality
- No regressions in existing functionality
- All tests pass
- Documentation updated

---

## Risk Assessment

### Low Risk
- Fixing deduplication (using existing shared_cycles)
- Adding auto-selection of worker count

### Medium Risk
- Chunk size optimization (might affect other use cases)
- Performance improvements (need careful testing)

### Mitigation
- Test thoroughly with different problem sizes
- Keep backward compatibility
- Add comprehensive test coverage
