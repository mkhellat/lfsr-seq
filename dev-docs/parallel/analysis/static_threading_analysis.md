# Static Threading Implementation Analysis

## Yes, We Are Implementing Static Threading

### Definition of Static Threading

**Static threading** (also called **static load balancing** or **static task distribution**) is a parallel execution model where:
1. Work is divided into **fixed chunks** before execution begins
2. Each thread/worker is assigned a **predetermined portion** of work upfront
3. **No dynamic redistribution** occurs during execution
4. Work assignment is **deterministic** and **unchanging**

### Our Implementation

#### 1. Static Partitioning (Before Execution)

```python
# lfsr/analysis.py:1497
chunks = _partition_state_space(state_vector_space, num_workers)
```

The `_partition_state_space` function (lines 937-1000) divides the state space into **fixed chunks** upfront:

```python
# Calculate chunk size
chunk_size = max(1, total_states // num_chunks)

# Create chunks by computing state tuples from indices
for chunk_idx in range(num_chunks):
 chunk = []
 start_idx = chunk_idx * chunk_size
 end_idx = min(start_idx + chunk_size, total_states)
 
 for state_idx in range(start_idx, end_idx):
 state_tuple = state_index_to_tuple(state_idx, degree, gf_order)
 chunk.append((state_tuple, state_idx))
 
 chunks.append(chunk)
```

**Key characteristics:**
- Chunks are computed **before any worker starts**
- Each chunk contains a **fixed set of states** (determined by indices)
- Chunk boundaries are **deterministic** and **unchanging**
- No dynamic adjustment based on runtime conditions

#### 2. Fixed Worker Assignment

```python
# lfsr/analysis.py:1509-1520
chunk_data_list = []
for worker_id, chunk in enumerate(chunks):
 chunk_data = (
 chunk, # Fixed chunk assigned to this worker
 coeffs_vector,
 gf_order,
 d,
 algorithm,
 period_only,
 worker_id,
 shared_cycles,
 cycle_lock,
 )
 chunk_data_list.append(chunk_data)
```

**Key characteristics:**
- Each worker gets **exactly one chunk** assigned upfront
- Worker-to-chunk mapping is **fixed** (worker 0 → chunk 0, worker 1 → chunk 1, etc.)
- No worker can take work from another worker's chunk
- Assignment happens **before execution starts**

#### 3. No Dynamic Work Redistribution

**What we DON'T have:**
- Work stealing (workers taking work from others when idle)
- Dynamic load balancing (redistributing work based on runtime performance)
- Adaptive chunking (adjusting chunk sizes during execution)
- Task queues (workers pulling tasks dynamically)

**What we DO have:**
- Fixed chunk assignment
- Workers process their assigned chunks independently
- Shared cycle registry (prevents redundancy, but doesn't redistribute work)

#### 4. Static Execution Model

```python
# lfsr/analysis.py:1525-1530
async_results = [
 pool.apply_async(_process_state_chunk, (chunk_data,))
 for chunk_data in chunk_data_list
]

# Wait for all workers to complete
worker_results = [result.get() for result in async_results]
```

**Execution flow:**
1. All chunks are assigned **before** workers start
2. Workers process their chunks **independently**
3. Workers wait for their assigned chunk to complete
4. No worker can help another worker with their chunk

---

## Why This Is Static Threading

### Evidence

1. **Pre-computed Partitioning**: Work is divided into fixed chunks before execution
2. **Deterministic Assignment**: Each worker gets a predetermined chunk
3. **No Runtime Redistribution**: Work assignment never changes during execution
4. **Independent Processing**: Workers process their chunks without coordination (except for redundancy prevention)

### Comparison with Dynamic Threading

| Aspect | Static Threading (Our Implementation) | Dynamic Threading |
|--------|--------------------------------------|-------------------|
| Work division | Fixed chunks before execution | Dynamic task queue |
| Work assignment | Predetermined per worker | Workers pull tasks as needed |
| Load balancing | Static (fixed chunks) | Dynamic (work stealing) |
| Adaptability | None (chunks fixed) | High (adapts to load) |
| Overhead | Low (no coordination) | Higher (coordination needed) |

---

## Why Static Threading Causes Load Imbalance

### The Problem

Our profiling results show severe load imbalance:
- **12-bit**: 168% (2 workers) → 400% (4 workers) → 620% (8 workers)
- **14-bit**: 184% (2 workers) → 400% (4 workers) → 683% (8 workers)

### Root Cause

1. **Fixed Chunk Boundaries**: States are divided by index, not by work complexity
 - Worker 0 gets states 0-4095
 - Worker 1 gets states 4096-8191
 - But the large cycle (period 16,383) might start in Worker 0's chunk

2. **No Work Redistribution**: If Worker 0 finds a large cycle, it must process all 16,383 states
 - Worker 1-7 finish quickly (their chunks contain states already in claimed cycles)
 - No mechanism to redistribute work from Worker 0 to idle workers

3. **Deterministic but Unbalanced**: The partitioning is fair by state count, but not by work complexity
 - Each chunk has ~8,192 states (for 2 workers)
 - But processing complexity varies dramatically (large cycles vs. small cycles)

### Why Dynamic Threading Would Help

With dynamic threading (work stealing):
- Idle workers could steal work from busy workers
- Load would balance automatically
- But: Higher overhead (coordination, synchronization)

---

## Conclusion

**Yes, we are implementing static threading** because:

1. Work is partitioned into **fixed chunks** before execution
2. Each worker is assigned a **predetermined chunk**
3. No **dynamic work redistribution** occurs
4. Work assignment is **deterministic** and **unchanging**

**This explains the load imbalance** we observe:
- Static partitioning divides work by state count, not by complexity
- Large cycles cause one worker to do most of the work
- Other workers finish quickly but cannot help

**Potential solutions:**
1. **Better static partitioning**: Partition by cycle structure (if known)
2. **Dynamic threading**: Implement work stealing (higher overhead)
3. **Adaptive chunking**: Start with small chunks, redistribute dynamically
4. **Fewer workers**: Use 1-2 workers for small problems (current auto-selection)
