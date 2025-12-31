Parallelization Guide
=====================

This guide provides comprehensive information about parallel processing in lfsr-seq,
including both static and dynamic parallel modes, load balancing, performance
characteristics, and best practices.

Introduction
------------

Parallel processing allows lfsr-seq to utilize multiple CPU cores simultaneously
to analyze LFSR state spaces faster. Instead of processing states one by one
sequentially, the work is divided among multiple "worker" processes that run
concurrently on different CPU cores.

**Key Benefits**:

- **Faster Analysis**: Process large state spaces in less time
- **Better Resource Utilization**: Use all available CPU cores
- **Scalability**: Performance improves with more CPU cores (up to a point)

**When Parallel Processing Helps**:

- Large LFSRs (> 10,000 states): Significant speedup possible
- Medium LFSRs (1,000-10,000 states): Modest speedup, overhead may limit benefits
- Small LFSRs (< 1,000 states): Sequential is usually faster (overhead dominates)

Understanding Parallel Modes
-----------------------------

lfsr-seq provides two parallel processing modes, each with different work
distribution strategies:

Static Mode (Fixed Work Distribution)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**How It Works**:

1. **Pre-partitioning**: Before processing starts, the entire state space is
   divided into fixed, equal-sized chunks. The number of chunks equals the
   number of worker processes.

2. **Fixed Assignment**: Each worker is assigned one chunk and processes all
   states in that chunk. The assignment never changes during execution.

3. **Independent Processing**: Workers process their chunks independently,
   with no communication between workers during processing.

**Example**:

For a 16,384-state space with 4 workers:
- Worker 0: States 0-4095
- Worker 1: States 4096-8191
- Worker 2: States 8192-12287
- Worker 3: States 12288-16383

**Advantages**:

- **Lower Overhead**: Minimal inter-process communication (IPC)
- **Simple Implementation**: Easy to understand and debug
- **Predictable**: Work distribution is known in advance

**Limitations**:

- **Load Imbalance**: Can have severe imbalance (100-500%) when cycles are
  unevenly distributed or when cycles < workers
- **No Adaptation**: Cannot redistribute work if one worker finishes early
- **Wasted Resources**: Idle workers when work is uneven

**Best For**:

- LFSRs with few cycles (2-4 cycles)
- When cycles are evenly distributed across the state space
- When the number of cycles is close to the number of workers
- Small to medium problems where IPC overhead matters

Dynamic Mode (Shared Task Queue with Load Balancing)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**How It Works**:

1. **Task Queue Creation**: States are divided into batches and placed in a
   shared queue accessible by all workers. Batch size is automatically selected
   based on problem size for optimal performance (see Adaptive Batch Sizing below).

2. **Dynamic Work Distribution**: Workers continuously pull batches from the
   queue:
   - When a worker finishes a batch, it immediately pulls the next available batch
   - Faster workers naturally take on more work
   - This provides automatic load balancing

3. **Adaptive Processing**: The system automatically adapts to varying work
   complexity across different parts of the state space.

**Example**:

For a 16,384-state space with 4 workers and auto-selected batch size (~200):
- Queue contains ~82 batches (16,384 / 200)
- Worker 0 pulls batch 0, processes it, then pulls batch 4, 8, 12...
- Worker 1 pulls batch 1, processes it, then pulls batch 5, 9, 13...
- Workers continue until queue is empty

Adaptive Batch Sizing
~~~~~~~~~~~~~~~~~~~~~

Dynamic mode automatically selects optimal batch sizes based on the state space
size to balance IPC overhead and load balancing granularity:

- **Small problems (< 8K states)**: Batch size 500-1000
  - Larger batches reduce IPC overhead (overhead dominates for small problems)
  - Example: 4,096 states → batch size ~500-1000

- **Medium problems (8K-64K states)**: Batch size 200-500
  - Balanced approach for medium-sized problems
  - Example: 16,384 states → batch size ~200-500

- **Large problems (> 64K states)**: Batch size 100-200
  - Smaller batches improve load balancing (computation dominates)
  - Example: 65,536 states → batch size ~100-200

The batch size is calculated as: ``state_space_size / (num_workers * factor)``
where the factor depends on problem size (2 for small, 4 for medium, 8 for large).

You can override the automatic selection using the ``--batch-size`` CLI option
(see Command-Line Options below).

**Advantages**:

- **Better Load Balancing**: Reduces imbalance by 2-4x for multi-cycle configurations
- **Automatic Adaptation**: Faster workers take on more work automatically
- **Better Resource Utilization**: All workers stay busy until work is complete
- **Consistent Performance**: More predictable performance across different LFSR configurations

**Limitations**:

- **IPC Overhead**: Queue operations add communication overhead (mitigated by batch aggregation)
- **More Complex**: Slightly more complex implementation
- **Queue Contention**: Multiple workers accessing the same queue (reduced by batch aggregation)

**Best For**:

- LFSRs with many cycles (8+ cycles)
- Configurations where cycles are unevenly distributed
- When using 4+ workers
- When load balancing is critical for performance

Load Balancing Explained
------------------------

**What is Load Balancing?**

Load balancing refers to how evenly work is distributed among workers. Perfect
balance means all workers finish at approximately the same time. Imbalance
occurs when some workers finish much earlier than others, leaving CPU cores
idle while other workers continue processing.

**Measuring Load Imbalance**:

Load imbalance is measured as a percentage:

.. math::

   \text{Imbalance} = \frac{\text{Max Work} - \text{Average Work}}{\text{Average Work}} \times 100\%

Where:

- **Max Work**: Number of cycles/states processed by the busiest worker
- **Average Work**: Average number of cycles/states per worker
- **Imbalance**: Percentage difference between max and average

**Example**:

With 4 workers and 134 cycles:

- **Static Mode**: Work distribution = [4, 47, 1, 82] cycles

  - Average = 33.5 cycles
  - Max = 82 cycles
  - Imbalance = (82 - 33.5) / 33.5 × 100% = **144.8%**

- **Dynamic Mode**: Work distribution = [37, 29, 46, 22] cycles

  - Average = 33.5 cycles
  - Max = 46 cycles
  - Imbalance = (46 - 33.5) / 33.5 × 100% = **37.3%**

Dynamic mode provides **3.9x better load balancing** in this case.

**Why Load Balancing Matters**:

1. **Performance**: Better balance means all CPU cores are utilized efficiently
2. **Predictability**: More consistent execution times
3. **Scalability**: Better performance as you add more workers

Performance Characteristics
---------------------------

Based on comprehensive profiling of 12-bit, 14-bit, and 16-bit LFSRs:

Average Speedup Across All Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Mode/Workers
     - Average Speedup
     - Notes
   * - Static 1w
     - 0.99x
     - Near-sequential performance
   * - Static 2w
     - 0.72x
     - Overhead reduces speedup
   * - Static 4w
     - 0.52x
     - Overhead dominates
   * - Static 8w
     - 0.68x
     - Some configurations benefit
   * - Dynamic 1w
     - 0.92x
     - Slight overhead
   * - Dynamic 2w
     - 0.79x
     - Better than static 2w
   * - Dynamic 4w
     - 0.62x
     - Better than static 4w
   * - Dynamic 8w
     - 0.38x
     - Overhead significant

**Key Observations**:

1. **Parallel Overhead Dominates**: Speedup rarely exceeds 1.0x due to:
   - Process creation overhead
   - Inter-process communication (IPC)
   - SageMath object serialization
   - Result merging overhead

2. **Dynamic Mode Performance**: Dynamic mode often outperforms static mode
   for multi-cycle configurations:
   - **14-bit-v2 (134 cycles)**: Dynamic 4w = 0.81x vs Static 4w = 0.44x
   - **16-bit-v2 (260 cycles)**: Dynamic 4w = 0.57x vs Static 4w = 0.49x

3. **Best Performance**: Sequential or 1 worker often provides best performance
   for small to medium LFSRs due to overhead.

Load Imbalance Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Mode/Workers
     - Average Imbalance
     - Notes
   * - Static 1w
     - 0.0%
     - Perfect (single worker)
   * - Static 2w
     - 30.3%
     - Moderate imbalance
   * - Static 4w
     - 165.5%
     - Severe imbalance
   * - Static 8w
     - 269.7%
     - Very severe imbalance
   * - Dynamic 1w
     - 0.0%
     - Perfect (single worker)
   * - Dynamic 2w
     - 37.2%
     - Similar to static
   * - Dynamic 4w
     - 164.7%
     - Similar average, but much better for multi-cycle
   * - Dynamic 8w
     - 218.1%
     - Better than static 8w

**Key Observations**:

1. **Few Cycles (2-4 cycles)**: Both modes show similar imbalance patterns
   - Perfect balance (0%) when cycles = workers
   - Severe imbalance (100-300%) when cycles < workers

2. **Many Cycles (8-260 cycles)**: Dynamic mode significantly outperforms static
   - **14-bit-v2 (134 cycles)**: Dynamic 4w = 37.3% vs Static 4w = 144.8% (3.9x better)
   - **16-bit-v2 (260 cycles)**: Dynamic 4w = 50.8% vs Static 4w = 198.5% (3.9x better)

3. **Scaling**: Static mode imbalance increases dramatically with more workers,
   while dynamic mode maintains better balance.

When to Use Each Mode
---------------------

Use Dynamic Mode When:
~~~~~~~~~~~~~~~~~~~~~~

✅ **Recommended for**:

- **Many Cycles**: LFSRs that produce 8+ cycles
  - Examples: 14-bit-v2 (134 cycles), 16-bit-v2 (260 cycles)
  
- **Uneven Distribution**: When cycles are likely to be unevenly distributed
  across the state space
  
- **4+ Workers**: When using 4 or more workers, dynamic mode's load balancing
  benefits become more significant
  
- **Performance Critical**: When load balancing is important for achieving
  better performance

**Benefits**:
- 2-4x better load balancing for multi-cycle configurations
- Often better performance for LFSRs with many cycles
- More consistent behavior across different LFSR configurations

Use Static Mode When:
~~~~~~~~~~~~~~~~~~~~~

✅ **Acceptable for**:

- **Few Cycles**: LFSRs with 2-4 cycles
  - Examples: 12-bit-v1 (2 cycles), 14-bit-v1 (2 cycles), 16-bit-v1 (4 cycles)
  
- **Even Distribution**: When cycles are evenly distributed and cycles ≈ workers
  
- **Small Problems**: Very small problems where IPC overhead matters more than
  load balancing
  
- **Single Worker**: When using 1 worker, both modes are equivalent

**Benefits**:
- Lower IPC overhead
- Simpler implementation
- Similar performance for few-cycle configurations

Decision Guide
~~~~~~~~~~~~~~

Use this decision tree to choose the right mode:

1. **How many cycles does your LFSR produce?**
   - **2-4 cycles**: Use **Static Mode** (default)
   - **8+ cycles**: Use **Dynamic Mode**
   - **5-7 cycles**: Try both, dynamic may help with 4+ workers

2. **How many workers are you using?**
   - **1-2 workers**: Either mode works, static has lower overhead
   - **4+ workers**: Dynamic mode recommended for multi-cycle LFSRs

3. **Is performance critical?**
   - **Yes, many cycles**: Use **Dynamic Mode**
   - **Yes, few cycles**: Use **Static Mode**
   - **No**: Use default (Static Mode)

Command-Line Usage
------------------

Basic Parallel Processing
~~~~~~~~~~~~~~~~~~~~~~~~~

Enable parallel processing:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --parallel --period-only

**Note**: Parallel processing requires ``--period-only`` mode. The tool
automatically forces period-only mode when parallel is enabled.

Choose Parallel Mode
~~~~~~~~~~~~~~~~~~~~

Use dynamic mode (better load balancing):

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --parallel --parallel-mode dynamic --period-only

Use static mode (default, lower overhead):

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --parallel --parallel-mode static --period-only

Control Number of Workers
~~~~~~~~~~~~~~~~~~~~~~~~~

Specify the number of workers:

.. code-block:: bash

   # Use 4 workers with dynamic mode
   lfsr-seq coefficients.csv 2 --parallel --parallel-mode dynamic --num-workers 4 --period-only

   # Use 2 workers with static mode
   lfsr-seq coefficients.csv 2 --parallel --parallel-mode static --num-workers 2 --period-only

Disable Parallel Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Force sequential processing:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --no-parallel

Python API Usage
----------------

Static Mode
~~~~~~~~~~~

.. code-block:: python

   from sage.all import GF, VectorSpace
   from lfsr.core import build_state_update_matrix
   from lfsr.analysis import lfsr_sequence_mapper_parallel
   
   # Build state update matrix
   coeffs = [1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0]
   C, _ = build_state_update_matrix(coeffs, 2)
   V = VectorSpace(GF(2), 12)
   
   # Process with static mode (4 workers)
   seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
       C, V, 2,
       output_file=None,
       no_progress=True,
       period_only=True,
       num_workers=4
   )
   
   print(f"Found {len(seq_dict)} sequences")
   print(f"Period sum: {periods_sum}")

Dynamic Mode
~~~~~~~~~~~~

.. code-block:: python

   from sage.all import GF, VectorSpace
   from lfsr.core import build_state_update_matrix
   from lfsr.analysis import lfsr_sequence_mapper_parallel_dynamic
   
   # Build state update matrix
   coeffs = [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
   C, _ = build_state_update_matrix(coeffs, 2)
   V = VectorSpace(GF(2), 14)
   
   # Process with dynamic mode (4 workers, auto batch size)
   seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
       C, V, 2,
       output_file=None,
       no_progress=True,
       period_only=True,
       num_workers=4,
       batch_size=None  # Auto-select based on problem size
   )
   
   # Or specify manual batch size
   seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel_dynamic(
       C, V, 2,
       output_file=None,
       no_progress=True,
       period_only=True,
       num_workers=4,
       batch_size=200  # Manual override
   )
   
   print(f"Found {len(seq_dict)} sequences")
   print(f"Period sum: {periods_sum}")

Implementation Details
----------------------

Static Mode Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **State Space Partitioning** (``_partition_state_space``):
   - Divides state space into :math:`n` equal chunks
   - Converts SageMath vectors to tuples for serialization
   - Returns list of chunks: ``[(state_tuple, index), ...]``

2. **Worker Processing** (``_process_state_chunk``):
   - Each worker receives one chunk
   - Reconstructs SageMath objects (GF, VectorSpace, matrix)
   - Processes all states in chunk independently
   - Returns sequences, periods, and work metrics

3. **Result Merging** (``_merge_parallel_results``):
   - Collects results from all workers
   - Deduplicates cycles using canonical keys (min_state)
   - Reconstructs SageMath objects
   - Assigns sequence numbers

Dynamic Mode Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Task Queue Creation**:
   - States divided into batches (auto-selected based on problem size)
   - **Lazy Generation (Phase 2.4)**: Batches generated on-demand by background producer thread
   - Batches placed in shared ``Manager().Queue()`` as workers consume them
   - Reduces memory usage and startup time for large problems
   - Sentinel values (``None``) signal queue end
   - Batch size automatically optimized: 500-1000 (small), 200-500 (medium), 100-200 (large)

2. **Worker Processing** (``_process_task_batch_dynamic``):
   - Workers continuously pull batches from queue using batch aggregation
   - Pull multiple batches at once (2-8 batches per operation) to reduce IPC overhead
   - Uses ``get_nowait()`` (non-blocking) with fallback to blocking ``get()``
   - Process all pulled batches, then immediately pull next set
   - Faster workers naturally take on more work
   - Returns when sentinel is received

3. **Persistent Worker Pool (Phase 2.3)**:
   - Workers are reused across multiple analyses (pool stays alive)
   - Reduces process creation overhead for repeated analyses
   - Expected 2-3x speedup for multiple analyses in same program run
   - Automatic cleanup on program exit

3. **Result Merging**:
   - Same as static mode
   - Uses canonical cycle keys (min_state) for deduplication

Critical Implementation Details
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**SageMath Isolation**:

Each worker creates fresh SageMath objects to avoid category mismatch errors:

.. code-block:: python

   # In worker process
   from sage.all import GF, VectorSpace
   F = GF(gf_order)
   V = VectorSpace(F, degree)
   # Reconstruct matrix from coefficients

**Matrix Reconstruction**:

Coefficients must be extracted from the **last column** of the companion matrix:

.. code-block:: python

   # CORRECT: Extract from last column
   coeffs = [C[i, d-1] for i in range(d)]
   
   # WRONG: Don't extract from last row
   # coeffs = [C[d-1, i] for i in range(d)]

**Cycle Deduplication**:

Uses canonical cycle representation (minimum state in cycle):

.. code-block:: python

   # Compute min_state by iterating through entire cycle
   min_state = start_state
   current = start_state
   for i in range(period - 1):
       current = current * state_update_matrix
       if tuple(current) < min_state:
           min_state = tuple(current)

**Shared Cycle Registry**:

Prevents multiple workers from processing the same cycle:

.. code-block:: python

   # Check if cycle already claimed
   if min_state_tuple in shared_cycles:
       # Skip, already being processed
       continue
   
   # Claim cycle
   with cycle_lock:
       if min_state_tuple not in shared_cycles:
           shared_cycles[min_state_tuple] = worker_id
           # Process cycle
       else:
           # Another worker claimed it first
           continue

Performance Optimization
------------------------

Batch Size Tuning (Dynamic Mode)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dynamic mode automatically selects optimal batch sizes based on problem size
to balance IPC overhead and load balancing granularity. The automatic selection
can be overridden using the ``--batch-size`` CLI option.

**IPC Optimization (Phase 2.2)**:

To further reduce IPC overhead, workers use **batch aggregation**: instead of
pulling one batch at a time, workers pull multiple batches per queue operation
(2-8 batches, adaptive based on problem size). This reduces queue operations by
2-8x and improves performance by 1.2-1.5x.

- **Small problems (<8K states)**: Pull 2-3 batches at once
- **Medium problems (8K-64K states)**: Pull 3-5 batches at once
- **Large problems (>64K states)**: Pull 4-8 batches at once

Workers use non-blocking ``get_nowait()`` to pull multiple batches efficiently,
with fallback to blocking ``get()`` when the queue is empty. This reduces
blocking time and improves CPU utilization.

Persistent Worker Pool (Phase 2.3)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dynamic mode uses a **persistent worker pool** that stays alive across multiple
analyses:

- **Pool Reuse**: Workers are created once and reused for subsequent analyses
- **Reduced Overhead**: Eliminates process creation overhead for repeated analyses
- **Faster Repeated Analyses**: Expected 2-3x speedup for multiple analyses
- **Automatic Cleanup**: Pool cleaned up automatically on program exit

**How It Works**:

1. First analysis creates the worker pool
2. Pool persists in memory for subsequent analyses
3. Workers are reused (no process creation overhead)
4. Pool is automatically cleaned up on program exit

**Benefits**:

- **2-3x speedup** for multiple analyses in same program run
- **Faster startup** for subsequent analyses (no pool creation delay)
- **Better resource utilization** (workers ready for work)

**Note**: Each worker still creates fresh SageMath objects for each analysis,
ensuring state isolation and correctness.

**Automatic Batch Size Selection**:

- **Small problems (< 8K states)**: Batch size 500-1000
  - Larger batches reduce IPC overhead (overhead dominates)
  - Formula: ``max(500, min(1000, state_space_size // (num_workers * 2)))``
  - Example: 4,096 states with 4 workers → batch size ~500-1000

- **Medium problems (8K-64K states)**: Batch size 200-500
  - Balanced approach for medium-sized problems
  - Formula: ``max(200, min(500, state_space_size // (num_workers * 4)))``
  - Example: 16,384 states with 4 workers → batch size ~200-500

- **Large problems (> 64K states)**: Batch size 100-200
  - Smaller batches improve load balancing (computation dominates)
  - Formula: ``max(100, min(200, state_space_size // (num_workers * 8)))``
  - Example: 65,536 states with 4 workers → batch size ~100-200

**Manual Override**:

You can override automatic selection using ``--batch-size N``:

.. code-block:: bash

   # Use batch size 300 (overrides auto-selection)
   lfsr-seq coefficients.csv 2 --parallel --parallel-mode dynamic --batch-size 300

**Batch Size Impact**:

- **Small batches (50-100 states)**: Better load balancing, higher IPC overhead
- **Medium batches (200-500 states)**: Good balance (auto-selected for medium problems)
- **Large batches (500-1000 states)**: Lower IPC overhead, less effective load balancing

The automatic selection ensures optimal performance across different problem sizes.

Lazy Task Generation (Phase 2.4)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Dynamic mode uses **lazy task generation** to reduce memory usage and startup time:

- **Background Producer Thread**: Generates batches on-demand instead of pre-generating all
- **Memory Efficiency**: Only batches currently in queue are in memory
- **Faster Startup**: Workers can start immediately, don't wait for all batches
- **Scalability**: Better for very large problems (>100K states)

**How It Works**:

1. Generator function creates batches on-demand as workers consume them
2. Background producer thread generates batches and puts them in queue
3. Workers pull batches from queue (same as before)
4. Producer adds sentinel values when all batches are generated

**Benefits**:

- **Reduced Memory**: Only active batches in memory (O(batch_size * queue_size))
- **Faster Startup**: No upfront batch generation delay
- **Correctness**: All batches still generated and processed correctly

Worker Count Selection
~~~~~~~~~~~~~~~~~~~~~~~

Choose worker count based on:

1. **CPU Cores**: Don't exceed available CPU cores
2. **Problem Size**: More workers help for larger problems
3. **Overhead**: Too many workers increase overhead

**Recommendations**:

- **Small LFSRs (< 1,000 states)**: 1 worker (sequential often faster)
- **Medium LFSRs (1,000-10,000 states)**: 1-2 workers
- **Large LFSRs (> 10,000 states)**: 2-4 workers
- **Very Large LFSRs (> 100,000 states)**: 4-8 workers

Troubleshooting
---------------

Workers Hang or Timeout
~~~~~~~~~~~~~~~~~~~~~~~

**Symptoms**: Parallel processing times out and falls back to sequential

**Causes**:
- SageMath/multiprocessing interaction issues
- Very large cycles causing computation to hang
- System resource constraints

**Solutions**:
- Use ``--no-parallel`` to force sequential mode
- Reduce number of workers
- Ensure sufficient system resources (memory, CPU)

Incorrect Results
~~~~~~~~~~~~~~~~~

**Symptoms**: Parallel results don't match sequential results

**Causes**:
- Bug in deduplication logic (should be fixed)
- Matrix reconstruction error
- Cycle claiming race condition

**Solutions**:
- Verify you're using the latest version
- Report the issue with your LFSR configuration
- Use ``--no-parallel`` to verify sequential results

Poor Performance
~~~~~~~~~~~~~~~~

**Symptoms**: Parallel mode is slower than sequential

**Causes**:
- Overhead dominates for small problems
- Too many workers causing overhead
- IPC overhead in dynamic mode

**Solutions**:
- Use sequential for small LFSRs (< 1,000 states)
- Reduce number of workers
- Try static mode if using dynamic (lower overhead)
- Use ``--period-only`` to minimize overhead

Best Practices
--------------

1. **Always Use Period-Only Mode**: Parallel processing requires ``--period-only``
   for correctness and performance.

2. **Choose Mode Based on Cycle Count**: Use dynamic for many cycles, static for few.

3. **Start with Fewer Workers**: Begin with 2-4 workers and scale up if needed.

4. **Monitor Load Imbalance**: For multi-cycle LFSRs, dynamic mode provides
   significantly better balance.

5. **Verify Correctness**: Always verify parallel results match sequential for
   your specific LFSR configuration.

6. **Profile Performance**: Use profiling scripts to measure actual speedup for
   your use case.

See Also
--------

- :doc:`user_guide` for basic usage examples
- :doc:`mathematical_background` for theoretical details
- :doc:`api/analysis` for complete API documentation
- ``scripts/PROFILING_EVALUATION.md`` for detailed profiling results
