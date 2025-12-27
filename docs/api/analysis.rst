Analysis Module
===============

The analysis module provides functions for analyzing LFSR sequences, computing periods, and categorizing state vectors.

.. automodule:: lfsr.analysis
   :members:
   :undoc-members:
   :show-inheritance: False
   :imported-members: False

Cycle Detection Algorithms
--------------------------

The module implements efficient cycle detection algorithms for finding sequence periods:

**Period-Only Functions** (for ``--period-only`` mode):

**Floyd's Algorithm** (``_find_period_floyd``):
   Period-only version using tortoise-and-hare method.
   Finds period in O(period) time with true O(1) space.
   Performs ~4× more operations than enumeration, making it 3-5× slower.
   Useful for educational/verification purposes.

**Brent's Algorithm** (``_find_period_brent``):
   Period-only version using powers-of-2 method.
   Finds period in O(period) time with true O(1) space.
   Similar performance characteristics to Floyd's algorithm.
   Alternative to Floyd's, useful for educational/verification purposes.

**Enumeration Method** (``_find_period_enumeration``):
   Period-only version that enumerates without storing sequence.
   Finds period in O(period) time with O(1) space.
   Faster and simpler than Floyd/Brent for typical periods.

**Period Dispatcher** (``_find_period``):
   Selects period-only algorithm based on ``algorithm`` parameter.
   Supports "floyd", "brent", "enumeration", or "auto".
   Returns only the period, not the sequence.

**Full Sequence Functions** (for normal mode):

**Floyd's Algorithm** (``_find_sequence_cycle_floyd``):
   Finds period using tortoise-and-hare, then enumerates full sequence.
   Uses O(period) space since sequence must be stored.
   Slower than enumeration due to Phase 1+2 overhead.

**Brent's Algorithm** (``_find_sequence_cycle_brent``):
   Finds period using powers-of-2, then enumerates full sequence.
   Uses O(period) space since sequence must be stored.
   Similar performance to Floyd's algorithm.

**Enumeration Method** (``_find_sequence_cycle_enumeration``):
   Enumerates all states in the cycle.
   Faster and simpler than Floyd/Brent.
   Default choice for full sequence mode.

**Main Dispatcher** (``_find_sequence_cycle``):
   Selects algorithm based on ``algorithm`` and ``period_only`` parameters.
   Supports "floyd", "brent", "enumeration", or "auto".
   * Full mode (``period_only=False``): Defaults to enumeration
   * Period-only mode (``period_only=True``): Uses period-only functions

**Performance Characteristics**:

See :doc:`../mathematical_background` for detailed performance analysis including:
* Operation count comparisons
* Time performance measurements
* Space complexity verification
* Algorithm selection guidelines

Functions
---------

.. autofunction:: lfsr.analysis.lfsr_sequence_mapper
   :no-index:

This is the main function for mapping all possible state vectors to their sequences and periods. It enumerates the entire state space and identifies all cycles.

Example
~~~~~~~

.. code-block:: python

   from sage.all import *
   from lfsr.core import build_state_update_matrix
   from lfsr.analysis import lfsr_sequence_mapper
   
   # Build state update matrix
   coeffs = [1, 1, 0, 1]
   C, CS = build_state_update_matrix(coeffs, 2)
   
   # Create vector space
   V = VectorSpace(GF(2), 4)
   
   # Map sequences
   seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
       C, V, 2, output_file=None, no_progress=False
   )
   
   print(f"Found {len(seq_dict)} sequences")
   print(f"Maximum period: {max_period}")

Parallel State Enumeration
---------------------------

The module provides parallel processing capabilities for large state spaces:

**Parallel Mapper** (``lfsr_sequence_mapper_parallel``):
   Parallel version of ``lfsr_sequence_mapper`` using multiprocessing.
   Partitions the state space across multiple CPU cores for faster processing.
   Automatically falls back to sequential processing on timeout or error.

**State Space Partitioning** (``_partition_state_space``):
   Divides the state space into chunks for parallel processing.
   Converts SageMath vectors to tuples for pickling/serialization.
   Returns list of chunks, each containing (state_tuple, index) pairs.

**Worker Function** (``_process_state_chunk``):
   Processes a single chunk of states in a worker process.
   Reconstructs SageMath objects from serialized data.
   **Critical Implementation Details**:
   - Extracts coefficients from matrix **last column** (not last row)
   - Uses Floyd's algorithm for period computation (enumeration hangs)
   - Computes full sequences for small periods (≤100) for deduplication
   - Returns sequences, periods, and statistics for the chunk.

**Result Merging** (``_merge_parallel_results``):
   Merges results from multiple parallel workers.
   Handles deduplication of sequences found by multiple workers:
   - Small periods (≤100): Uses sorted state tuples for accurate deduplication
   - Large periods (>100): Uses (start_state, period) keys (simplified)
   - Respects ``period_only`` flag (sequences computed but not stored)
   Reconstructs SageMath objects and assigns sequence numbers.

**Usage**:

Parallel processing is automatically enabled for large state spaces (> 10,000
states) when multiple CPU cores are available. You can also explicitly control
it via CLI flags:

.. code-block:: bash

   # Auto-enabled for large LFSRs
   lfsr-seq large_lfsr.csv 2
   
   # Explicitly enable
   lfsr-seq coefficients.csv 2 --parallel
   
   # Control number of workers
   lfsr-seq coefficients.csv 2 --parallel --num-workers 4
   
   # Disable parallel processing
   lfsr-seq coefficients.csv 2 --no-parallel

**Example**:

.. code-block:: python

   from sage.all import *
   from lfsr.core import build_state_update_matrix
   from lfsr.analysis import lfsr_sequence_mapper_parallel
   
   # Build state update matrix
   coeffs = [1, 1, 0, 1]
   C, CS = build_state_update_matrix(coeffs, 2)
   
   # Create vector space
   V = VectorSpace(GF(2), 4)
   
   # Map sequences in parallel (period-only mode required)
   seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
       C, V, 2, output_file=None, no_progress=False, 
       algorithm="floyd", period_only=True, num_workers=2
   )
   
   print(f"Found {len(seq_dict)} sequences")
   print(f"Maximum period: {max_period}")

**Performance**:

* **Speedup**: 4-8× on typical multi-core systems for large state spaces
* **Overhead**: Process creation and result merging add overhead
* **Best Case**: Large state spaces (> 10,000 states) with many CPU cores
* **Fallback**: Automatically falls back to sequential on timeout/error

**Important Notes**:

* **Period-Only Mode Required**: Parallel processing requires ``period_only=True``.
  Full sequence mode causes workers to hang due to SageMath/multiprocessing issues.

* **Algorithm**: Uses Floyd's algorithm internally, regardless of ``algorithm``
  parameter, to avoid enumeration's matrix multiplication loop hang.

* **Matrix Extraction**: Coefficients must be extracted from matrix **last column**
  (column d-1), not the last row, for correct reconstruction.

**Performance Characteristics**:

* **Speedup**: 6-10x on medium LFSRs (100-10,000 states) after optimization
* **Best Configuration**: 1-2 workers for medium LFSRs
* **Overhead**: Minimal after lazy partitioning optimization
* **Bottlenecks**: Process overhead (38%) remains, but partitioning optimized (was 60%)

**Example Usage**:

.. code-block:: python

   from sage.all import *
   from lfsr.analysis import lfsr_sequence_mapper_parallel
   from lfsr.core import build_state_update_matrix

   # Build matrix and vector space
   coeffs = [1, 0, 0, 1]
   C, CS = build_state_update_matrix(coeffs, 2)
   V = VectorSpace(GF(2), 4)

   # Parallel processing (period-only mode required)
   seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
       C, V, 2, output_file=None, no_progress=True,
       period_only=True, num_workers=2
   )

   # Verify correctness
   assert periods_sum == 16  # State space size
   print(f"Found {len(seq_dict)} unique sequences")
   print(f"Maximum period: {max_period}")

**See Also**:

* :doc:`../mathematical_background` for detailed parallel enumeration theory
* :doc:`../user_guide` for CLI usage examples
* ``examples/parallel_processing_example.py`` for complete working examples
