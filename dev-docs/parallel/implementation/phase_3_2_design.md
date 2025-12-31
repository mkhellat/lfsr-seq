# Phase 3.2: Hybrid Approach - Design Document

## Goal

Implement a hybrid static + dynamic mode that combines the low overhead of static partitioning with the load balancing benefits of work stealing.

## Current Modes

### Static Mode
- **Advantages**: Low overhead (one-time chunk assignment), no queue operations
- **Disadvantages**: Poor load balancing (184-790% imbalance), depends on cycle alignment

### Dynamic Mode (Current)
- **Advantages**: Excellent load balancing (2-4x better), adaptive to work distribution
- **Disadvantages**: Higher overhead (queue operations, IPC), overhead dominates for small problems

## Proposed Design: Hybrid Mode

### Architecture

1. **Initial Static Partitioning**: Divide state space into chunks (like static mode)
2. **Work Stealing**: When workers finish their chunk early, steal from others
3. **Best of Both Worlds**: Low overhead + good load balancing

### Implementation Approach

**Option A: Static Chunks + Work Stealing (Recommended)**
- Partition state space into chunks (one per worker)
- Assign chunks to workers (static assignment)
- Workers process their chunk
- When done, workers steal remaining work from others
- Uses work stealing queues for remaining work

**Option B: Static Initial + Dynamic Fallback**
- Start with static partitioning
- If load imbalance detected, switch to dynamic mode
- More complex, requires load monitoring

**Option C: Hybrid Queue**
- Static chunks assigned initially
- Shared queue for overflow/stealing
- Workers prefer their chunk, use queue when idle

### Recommended: Option A (Static Chunks + Work Stealing)

**Implementation Steps**:

1. Partition state space into chunks (like static mode)
2. Assign chunks to workers (static assignment)
3. Create work stealing queues for remaining work
4. Workers process their assigned chunk first
5. When chunk done, workers steal from others' remaining work
6. Combines low overhead of static with load balancing of dynamic

### Algorithm

```python
# Partition state space (like static mode)
chunks = partition_state_space(state_space_size, num_workers)

# Assign chunks to workers
worker_chunks = [chunks[i] for i in range(num_workers)]

# Create work stealing queues for remaining work
worker_queues = [manager.Queue() for _ in range(num_workers)]

# Worker processing
def hybrid_worker(worker_id, assigned_chunk, worker_queues):
    # First: Process assigned chunk (static, low overhead)
    process_chunk(assigned_chunk)
    
    # Then: Steal remaining work from others (dynamic, load balancing)
    while True:
        # Try to steal from other workers
        stolen = False
        for other_id in range(num_workers):
            if other_id != worker_id:
                try:
                    work = worker_queues[other_id].get_nowait()
                    if work is None:  # Sentinel
                        continue
                    process_work(work)
                    stolen = True
                    break
                except queue.Empty:
                    continue
        
        if not stolen:
            # No more work, exit
            break
```

### Benefits

1. **Low Overhead**: Static assignment eliminates queue operations for initial work
2. **Good Load Balancing**: Work stealing handles uneven chunks
3. **Adaptive**: Automatically adapts to actual work distribution
4. **Best Performance**: Combines strengths of both modes

### Challenges

1. **Complexity**: More complex than pure static or dynamic
2. **Implementation**: Need both partitioning and work stealing
3. **Auto-Selection**: Need to decide when to use hybrid vs pure modes

### Auto-Selection Logic

- **Small problems (<8K states)**: Use static (overhead dominates)
- **Medium problems (8K-64K states)**: Use hybrid (balance overhead and load balancing)
- **Large problems (>64K states)**: Use dynamic (load balancing more important)
- **Multi-cycle configurations**: Prefer hybrid or dynamic

---

## Implementation Plan

1. Create hybrid mode function
2. Implement static partitioning (reuse from static mode)
3. Implement work stealing for remaining work
4. Add auto-selection logic
5. Test correctness and performance
6. Compare with static and dynamic modes

---

**Status**: Design complete, ready for implementation
