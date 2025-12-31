# Phase 2.3: Pre-initialize Worker Pool - Design Document

## Goal

Implement a persistent worker pool that stays alive across multiple LFSR analyses to reduce process creation overhead.

## Current Implementation

- **Worker Creation**: New `multiprocessing.Pool` created for each analysis
- **Worker Destruction**: Pool closed after each analysis completes
- **Overhead**: Process creation, SageMath initialization, cleanup for each analysis

## Proposed Design

### Architecture

1. **Module-Level Pool Manager**: Singleton that manages persistent worker pool
2. **Pool Lifecycle**: 
   - Create pool on first use
   - Reuse pool for subsequent analyses
   - Cleanup on shutdown or after idle timeout
3. **State Management**: Each worker still creates fresh SageMath objects (isolation preserved)

### Implementation Approach

**Option A: Simple Module-Level Pool (Recommended)**
- Create pool at module level
- Reuse across analyses
- Cleanup on program exit or explicit shutdown
- Pros: Simple, effective
- Cons: Pool stays alive for entire program lifetime

**Option B: Pool with Idle Timeout**
- Pool with automatic cleanup after idle period
- More complex, requires background thread
- Pros: Better resource management
- Cons: More complex, potential race conditions

**Option C: Context Manager Pattern**
- Pool managed via context manager
- Explicit lifecycle control
- Pros: Clear ownership, explicit cleanup
- Cons: Requires API changes

### Recommended: Option A (Simple Module-Level Pool)

**Implementation Steps**:

1. Create `_worker_pool_manager` module-level variable
2. Lazy initialization: Create pool on first use
3. Reuse pool for all analyses
4. Cleanup: Add `atexit` handler or explicit shutdown method

### SageMath State Management

**Critical**: Each worker must still create fresh SageMath objects to avoid category mismatch errors.

**Solution**: Workers already do this correctly:
- Each worker imports SageMath fresh
- Each worker creates GF, VectorSpace, matrix objects
- No shared SageMath state between workers

**Verification**: Current implementation already isolates SageMath state correctly.

### API Design

```python
# Module-level pool manager
_worker_pool = None
_pool_lock = threading.Lock()

def get_worker_pool(num_workers):
    """Get or create persistent worker pool."""
    global _worker_pool
    with _pool_lock:
        if _worker_pool is None:
            _worker_pool = create_pool(num_workers)
        return _worker_pool

def shutdown_worker_pool():
    """Explicitly shutdown worker pool."""
    global _worker_pool
    with _pool_lock:
        if _worker_pool is not None:
            _worker_pool.close()
            _worker_pool.join()
            _worker_pool = None
```

### Integration Points

1. **Modify `lfsr_sequence_mapper_parallel_dynamic()`**:
   - Use `get_worker_pool()` instead of creating new pool
   - Don't close pool after use (reuse for next analysis)

2. **Add Cleanup**:
   - `atexit` handler to cleanup on program exit
   - Optional explicit shutdown method

### Challenges

1. **Worker Count Changes**: What if different analyses need different worker counts?
   - Solution: Use max worker count, or recreate pool if count differs significantly

2. **Error Recovery**: What if pool becomes corrupted?
   - Solution: Detect errors, recreate pool

3. **Concurrent Analyses**: Multiple analyses running simultaneously?
   - Solution: Pool is thread-safe, can handle concurrent map() calls

### Testing Strategy

1. **Correctness**: Verify results match sequential
2. **Reuse**: Run multiple analyses, verify pool is reused
3. **Performance**: Measure speedup for repeated analyses
4. **Cleanup**: Verify pool cleanup on exit

---

## Implementation Plan

1. Create pool manager module-level functions
2. Modify dynamic function to use persistent pool
3. Add error handling and pool recreation
4. Add cleanup handlers
5. Test correctness and performance
6. Document usage and limitations

---

**Status**: Design complete, ready for implementation
