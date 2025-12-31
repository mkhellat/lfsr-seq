# Phase 3.1: Work Stealing - Design Document

## Goal

Implement per-worker queues with work stealing to reduce lock contention and improve performance compared to the shared queue model.

## Current Implementation (Shared Queue)

- **Single Shared Queue**: All workers pull from one `Manager().Queue()`
- **Lock Contention**: All workers compete for the same queue
- **IPC Overhead**: Every batch pull requires queue operation
- **Scalability**: Performance degrades with more workers due to contention

## Proposed Design: Work Stealing

### Architecture

1. **Per-Worker Queues**: Each worker has its own queue
2. **Initial Distribution**: Batches distributed to worker queues (round-robin or load-aware)
3. **Work Stealing**: When a worker's queue is empty, it steals from other workers
4. **Lock Reduction**: Workers primarily access their own queue (less contention)

### Implementation Approach

**Option A: Simple Work Stealing (Recommended)**
- Each worker has a dedicated queue
- Producer distributes batches round-robin to worker queues
- Workers prefer their own queue, steal from others when idle
- Stealing uses random selection or round-robin of other workers

**Option B: Load-Aware Distribution**
- Producer distributes batches based on worker load
- More complex, requires load tracking
- Better initial distribution, but adds complexity

**Option C: Hybrid with Shared Queue Fallback**
- Per-worker queues for primary distribution
- Shared queue as fallback when all queues empty
- More complex, but handles edge cases better

### Recommended: Option A (Simple Work Stealing)

**Implementation Steps**:

1. Create per-worker queues (list of queues, one per worker)
2. Modify producer thread to distribute batches round-robin
3. Modify worker loop to:
   - First try own queue (non-blocking)
   - If empty, try stealing from other workers (random selection)
   - If all empty, wait on own queue with timeout
4. Add sentinel handling (one per worker queue)

### Queue Structure

```python
# Per-worker queues
worker_queues = [manager.Queue() for _ in range(num_workers)]

# Producer distributes batches round-robin
for batch in batch_generator():
    worker_id = batches_created % num_workers
    worker_queues[worker_id].put(batch)
    batches_created += 1

# Worker processing
def worker_loop(worker_id, worker_queues):
    while True:
        # Try own queue first
        try:
            batch = worker_queues[worker_id].get_nowait()
            if batch is None:  # Sentinel
                break
            process_batch(batch)
            continue
        except queue.Empty:
            pass
        
        # Try stealing from other workers
        stolen = False
        other_workers = [i for i in range(num_workers) if i != worker_id]
        random.shuffle(other_workers)  # Random order for fairness
        
        for other_id in other_workers:
            try:
                batch = worker_queues[other_id].get_nowait()
                if batch is None:  # Skip sentinels
                    continue
                process_batch(batch)
                stolen = True
                break
            except queue.Empty:
                continue
        
        # If nothing stolen, wait on own queue
        if not stolen:
            try:
                batch = worker_queues[worker_id].get(timeout=0.5)
                if batch is None:  # Sentinel
                    break
                process_batch(batch)
            except queue.Empty:
                # Timeout - check if all done
                continue
```

### Benefits

1. **Reduced Lock Contention**: Workers primarily access own queue
2. **Better Scalability**: Less contention with more workers
3. **Load Balancing**: Work stealing ensures no worker is idle
4. **Backward Compatible**: Can keep shared queue as fallback

### Challenges

1. **Queue Management**: More complex than single shared queue
2. **Stealing Logic**: Need to handle race conditions
3. **Sentinel Distribution**: Must add sentinel to each queue
4. **Load Imbalance**: Initial distribution might be uneven

### Testing Strategy

1. **Correctness**: Verify results match sequential
2. **Performance**: Compare with shared queue model
3. **Load Balancing**: Measure work distribution across workers
4. **Scalability**: Test with different worker counts

---

## Implementation Plan

1. Create per-worker queue structure
2. Modify producer to distribute round-robin
3. Implement work stealing in worker loop
4. Add proper sentinel handling
5. Test correctness and performance
6. Compare with shared queue model

---

**Status**: Design complete, ready for implementation
