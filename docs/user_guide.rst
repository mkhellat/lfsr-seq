User Guide
==========

Basic Usage
-----------

The basic command-line usage is:

.. code-block:: bash

   lfsr-seq <input_file> <gf_order> [options]

**Example:**

.. code-block:: bash

   lfsr-seq strange.csv 2

This will:
- Read LFSR coefficients from ``strange.csv``
- Analyze sequences over GF(2)
- Generate output in ``strange.csv.out``

Command-Line Options
--------------------

This section provides a comprehensive reference for all command-line
options available in the ``lfsr-seq`` tool. Options are organized by
category for easy navigation.

**Options Catalog**:

The tool provides the following categories of options. Click on any
category to jump to its detailed documentation:

1. **Basic Options** (see below) - Core functionality for LFSR analysis
2. **Correlation Attack Options** - See :ref:`correlation-attack-options`
3. **Algebraic Attack Options** - See :ref:`algebraic-attack-options`
4. **Time-Memory Trade-Off (TMTO) Attack Options** - See :ref:`tmto-attack-options`
5. **Stream Cipher Analysis Options** - See :ref:`stream-cipher-options`
6. **Advanced LFSR Structures Options** - See :ref:`advanced-structure-options`
7. **Theoretical Analysis Options** - See :ref:`theoretical-analysis-options`
8. **Visualization Options** - See :ref:`visualization-options`
9. **Machine Learning Options** - See :ref:`machine-learning-options`
10. **NIST SP 800-22 Test Suite Options** - See :ref:`nist-test-options`

**Quick Reference - All Options by Category**:

*Basic Options*:
   -h, --help, --version, -o/--output, -v/--verbose, -q/--quiet,
   --no-progress, --format, --period-only, --algorithm,
   ---check-primitive, -show-period-stats, --no-period-stats,
   ---parallel, --no-parallel, -num-workers,
   ---parallel-mode, --batch-size

*Correlation Attack Options*:
   --correlation-attack, --lfsr-configs, --keystream-file,
   ---target-lfsr, -significance-level, --fast-correlation-attack,
   ---max-candidates, -distinguishing-attack, --distinguishing-method

*Algebraic Attack Options*:
   --algebraic-attack, --algebraic-method,
    --max-cube-size, --max-equations

*TMTO Attack Options*:
   --tmto-attack, --tmto-method, --chain-count, --chain-length,
   --tmto-table-file

*Stream Cipher Analysis Options*:
   --cipher, --analyze-cipher, --generate-keystream,
   ---keystream-length, -key-file, --iv-file, --compare-ciphers

*Advanced LFSR Structures Options*:
   --advanced-structure, --analyze-advanced-structure,
   --generate-advanced-sequence, --advanced-sequence-length

*Theoretical Analysis Options*:
   --export-latex, --generate-paper, --compare-known, --benchmark,
   --reproducibility-report

*Visualization Options*:
   --plot-period-distribution, --plot-state-transitions,
   --plot-period-statistics, --plot-3d-state-space,
   ---visualize-attack, -viz-format, --viz-interactive

*Machine Learning Options*:
   --predict-period, --detect-patterns, --detect-anomalies,
    --train-model, --ml-model-file

*NIST Test Suite Options*:
   --nist-test, --sequence-file, --nist-significance-level,
   --nist-block-size, --nist-output-format

Basic Options
~~~~~~~~~~~~~

Positional Arguments:
   - `input_file`:            CSV file containing LFSR coefficient vectors
   - `gf_order`:              Galois field order (prime or prime power)

Basic Optional Arguments:
   -h, --help                 Show help message and exit
   --version                  Show version and exit
   -o, --output FILE          Specify output file (``default: input_file.out``)
   -v, --verbose              Enable verbose output
   -q, --quiet                Enable quiet mode (suppress non-essential output)
   --no-progress              Disable progress bar display

   --format {text|json|csv|xml}
                              Output format (``default: text``)

   --period-only              Compute periods only, without storing
                              sequences.  Floyd's algorithm uses true
                              O(1) space in this mode.  Both
                              algorithms achieve O(1) space, but
                              enumeration is faster.

   --algorithm {floyd|brent|enumeration|auto}
                              Cycle detection algorithm (default:
                              auto)

                              - enumeration: Default, faster for
                                typical periods
                              - floyd: Tortoise-and-hare algorithm,
                                available for educational/verification
                                purposes
                              - brent: Powers-of-2 algorithm,
                                alternative to Floyd
                              - auto: Enumeration for full mode, floyd
                                for period-only

                              Note: In period-only mode, all
                              algorithms use O(1) space.  In full
                              mode, all algorithms use O(period)
                              space.

   --check-primitive          Explicitly check and report if
                              characteristic polynomial is
                              primitive. Primitive polynomials yield
                              maximum period LFSRs (period = q^d - 1).
                              
                              Note: Primitive polynomial detection is
                              automatic - the tool always checks and
                              displays a [PRIMITIVE] indicator in the
                              characteristic polynomial output when a
                              primitive polynomial is detected. This
                              flag makes the check explicit and can be
                              useful for documentation or scripting
                              purposes.
                              
                              Example:
                                lfsr-seq coefficients.csv 2 --check-primitive

   --show-period-stats        Display detailed period distribution
                              statistics (enabled by default). Shows
                              mean, median, variance, standard
                              deviation, period frequency histogram,
                              and comparison with theoretical bounds.
                              
   --no-period-stats          Disable period distribution statistics display.

   --parallel                 Enable parallel state enumeration
                              (auto-enabled for large state spaces >
                              10,000 states with 2+ CPU cores).  Uses
                              multiple CPU cores to process states in
                              parallel for faster analysis. Falls back
                              to sequential if parallel processing
                              fails or times out.

   --no-parallel              Disable parallel processing (force
                              sequential mode).  Use this if you
                              encounter issues with parallel
                              processing or want deterministic
                              single-threaded execution.

   --num-workers N            Set the number of parallel workers
                              (``default: CPU count``). Only used with
                              ``--parallel``. The actual number of
                              workers is clamped to available CPU
                              cores.

   --parallel-mode {static|dynamic}
                              Choose parallel processing mode
                              (default: static).
                              
                              - static: Fixed work distribution -
                                divides state space into equal chunks,
                                one per worker. Best for
                                configurations with few cycles (2-4
                                cycles) or when cycles are evenly
                                distributed.
                              
                              - dynamic: Shared task queue - workers
                                pull batches of states from a shared
                                queue. Provides better load balancing
                                for configurations with many cycles
                                (8+ cycles). Reduces load imbalance by
                                2-4x compared to static mode for
                                multi-cycle LFSRs. Batch size is
                                automatically optimized based on
                                problem size.
                              
                              Recommendation: Use dynamic mode for
                              LFSRs that produce many cycles (e.g.,
                              14-bit-v2 with 134 cycles, 16-bit-v2
                              with 260 cycles). Use static mode for
                              LFSRs with few cycles or when cycles ≈
                              workers.

   --batch-size BATCH_SIZE    Batch size for dynamic parallel mode
                              (states per batch).  If not specified,
                              automatically selected based on problem
                              size:
                              
                              - Small problems (<8K states): 500-1000
                                states per batch
                              - Medium problems (8K-64K states):
                                200-500 states per batch
                              - Large problems (>64K states): 100-200
                                states per batch
                              
                              The automatic selection balances IPC
                              overhead and load balancing
                              granularity. Manual override is rarely
                              needed.

Input Format
------------

The CSV file should contain one or more rows of LFSR coefficients.
Each row represents a different LFSR configuration:

.. code-block:: text

   1,1,1,0,0,0,0,0,1,1
   1,1,1,0,0,0,0,0,1,1,0,1,1,1,0
   1,1,1,0,0,0,0,0,1,1,0,1,1,1,1

Each coefficient should be in the range [0, GF_order-1].

Output Formats
--------------

The tool supports multiple output formats for different use cases:

Text Format (Default)
~~~~~~~~~~~~~~~~~~~~~

Human-readable text output with formatted tables and sections. This is
the default format and provides the most readable output for manual
inspection.

JSON Format
~~~~~~~~~~~

Structured JSON output suitable for programmatic processing:

.. code-block:: bash

   lfsr-seq strange.csv 2 --format json --output results.json

The JSON format includes:
- Metadata (timestamp, GF order, coefficients, LFSR degree)
- Characteristic polynomial and its order
- All state sequences with their periods
- Statistical analysis results

CSV Format
~~~~~~~~~~

Tabular CSV output suitable for spreadsheet applications:

.. code-block:: bash

   lfsr-seq strange.csv 2 --format csv --output results.csv

XML Format
~~~~~~~~~~

Structured XML output for XML-based workflows:

.. code-block:: bash

   lfsr-seq strange.csv 2 --format xml --output results.xml

Output Contents
---------------

The tool generates comprehensive output including:

* **State Update Matrix**: The companion matrix representing LFSR
  state transitions
* **Matrix Order**: The period of state transitions (order of the
  matrix)
* **State Sequences**: All possible state sequences with their periods
* **Characteristic Polynomial**: The characteristic polynomial of the
  LFSR
* **Polynomial Order**: The order of the characteristic polynomial
* **Polynomial Factorization**: Factorization of the characteristic
  polynomial with factor orders
* **Sequence Analysis**: Detailed analysis of each state sequence

Output is written to both:
* **Console**: Summary information (unless ``--quiet`` is used)
* **Output File**: Complete detailed analysis

Security Features
-----------------

The tool includes several security features:

* **Path Traversal Protection**: Prevents access to files outside the
  intended directory
* **File Size Limits**: Maximum file size of 10 MB
* **Row Limits**: Maximum of 10,000 CSV rows per file
* **Input Validation**: Comprehensive validation of field orders and
  coefficients
* **Sanitization**: Input sanitization to prevent injection attacks

These limits can be adjusted in ``lfsr/constants.py`` if needed for
specific use cases.

Performance Features
--------------------

The tool implements several performance optimizations:

* **Cycle Detection Algorithms**: Three algorithms available for
  finding cycle periods

  * **Enumeration** (default): Simple, fast, O(1) space in period-only
    mode

    * Best for typical LFSR periods (< 1000)
    * 3-5× faster than Floyd/Brent for small-to-medium periods
    * True O(1) space in period-only mode

  * **Floyd's Algorithm**: Tortoise-and-hare method, available as
    option

    * Correctly implemented, achieves O(1) space in period-only mode
    * Does ~4× more operations, making it 3-5× slower
    * Useful for educational/verification purposes
    
  * **Brent's Algorithm**: Powers-of-2 method, available as option
    
    * Alternative to Floyd's, uses powers of 2 to find cycles
    * Similar performance characteristics to Floyd's
    * Useful for educational/verification purposes
  
  * **Algorithm Selection**: Use ``--algorithm`` option to choose
    
    * Default: Enumeration (faster, simpler)
    * Period-only mode: All achieve O(1) space, enumeration
      recommended
    * Use ``scripts/performance_profile.py`` for detailed analysis
      
  * **Performance Details**: See :doc:`mathematical_background` for
    comprehensive analysis
    
* **Optimized State Tracking**: Set-based visited state tracking for
  O(1) membership testing
  
* **Efficient Algorithms**: Mathematical optimizations for period
  computation and sequence analysis

For detailed mathematical background on cycle detection algorithms,
see the :doc:`mathematical_background` section.

Examples
--------

Parallel Processing Examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Analyze LFSR with parallel processing for faster results:

.. code-block:: bash

   # Enable parallel processing (static mode, default)
   lfsr-seq coefficients.csv 2 --parallel --period-only

   # Use dynamic mode (better for LFSRs with many cycles)
   lfsr-seq coefficients.csv 2 --parallel --parallel-mode dynamic --period-only

   # Use 4 workers with dynamic mode (auto batch size)
   lfsr-seq coefficients.csv 2 --parallel --parallel-mode dynamic --num-workers 4 --period-only
   
   # Use dynamic mode with manual batch size
   lfsr-seq coefficients.csv 2 --parallel --parallel-mode dynamic --batch-size 300 --period-only

   # Auto-detection (for large state spaces)
   lfsr-seq large_lfsr.csv 2 --period-only

**Choosing the Right Mode**:

- For LFSRs with many cycles (8+ cycles): Use ``--parallel-mode
  dynamic``
- For LFSRs with few cycles (2-4 cycles): Use ``--parallel-mode
  static`` (default)
- When in doubt: Try dynamic mode first, especially with 4+ workers

For a complete working example, see
``examples/parallel_processing_example.py``.

Basic Analysis
~~~~~~~~~~~~~~

Analyze LFSR over GF(2):

.. code-block:: bash

   lfsr-seq coefficients.csv 2

This will:
- Read LFSR coefficients from ``coefficients.csv``
- Analyze sequences over GF(2)
- Generate output in ``coefficients.csv.out``

Verbose Output
~~~~~~~~~~~~~~

Show detailed information about processing:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --verbose

Quiet Mode
~~~~~~~~~~

Suppress non-essential output (no progress bar):

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --quiet

Primitive Polynomial Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The tool automatically detects primitive polynomials and displays a
``[PRIMITIVE]`` indicator in the characteristic polynomial
output. Primitive polynomials are important because they yield LFSRs
with maximum period (q^d - 1).

Example with primitive polynomial:

.. code-block:: bash

   # Create a CSV file with coefficients for a primitive polynomial
   echo "1,0,0,1" > primitive.csv
   lfsr-seq primitive.csv 2

Output will show:
::

   ╎ t^4 + t^3 + 1                         ╎ O : 15           ╎
   ╎                                       ╎ [PRIMITIVE]      ╎

The ``[PRIMITIVE]`` indicator confirms that this polynomial is
primitive and the LFSR will have maximum period 15 (2^4 - 1) for
degree 4 over GF(2).

You can explicitly request primitive checking:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --check-primitive

Note: Primitive detection is automatic - the flag makes the check
explicit and is useful for documentation or scripting purposes.

For more information on primitive polynomials and their cryptographic
significance, see the :doc:`mathematical_background` section.

Parallel State Enumeration
~~~~~~~~~~~~~~~~~~~~~~~~~~

The tool supports parallel processing of state spaces for improved
performance on multi-core systems. Two parallel processing modes are
available: **static** (fixed work distribution) and **dynamic**
(shared task queue with load balancing).

**What is Parallel Processing?**

Parallel processing uses multiple CPU cores simultaneously to analyze
different parts of the LFSR state space. Instead of processing states
one by one in order, the work is divided among multiple "worker"
processes that run at the same time.

**Performance Characteristics**:

- **Large LFSRs (> 10,000 states)**: 2-4x speedup with 4 workers (when
  overhead doesn't dominate)
- **Medium LFSRs (1,000-10,000 states)**: 1.5-2x speedup
- **Small LFSRs (< 1,000 states)**: Sequential is faster (overhead
  dominates)

**Implementation Details**:

- Uses **fork mode** (13-17x faster than spawn) with SageMath
  isolation
- Automatic SageMath object isolation in workers prevents category
  mismatch errors
- Optimized IPC and process creation overhead
- Automatic fallback to sequential for small LFSRs where overhead
  would dominate

**Understanding Static vs Dynamic Modes**

The tool offers two parallel processing modes, each with different
work distribution strategies:

1. **Static Mode (Default)**: Fixed Work Distribution

   - **How it works**: The state space is divided into fixed,
     equal-sized chunks before processing starts. Each worker gets one
     chunk and processes all states in that chunk.

   - **Best for**:

     * LFSRs with few cycles (2-4 cycles)
     * When cycles are evenly distributed across the state space
     * When the number of cycles is close to the number of workers

   - **Advantages**: Lower overhead, simpler implementation

   - **Limitations**: Can have severe load imbalance (100-500%) when
     cycles are unevenly distributed or when cycles < workers

2. **Dynamic Mode**: Shared Task Queue with Load Balancing

   - **How it works**: States are divided into small batches (200
     states each) and placed in a shared queue. Workers pull batches
     from the queue as they finish their current work. This allows
     faster workers to take on more work, naturally balancing the
     load.

   - **Best for**:

     * LFSRs with many cycles (8+ cycles)
     * Configurations where cycles are unevenly distributed
     * When using 4+ workers

   - **Advantages**:

     * 2-4x better load balancing for multi-cycle configurations
     * More consistent performance across different LFSR
       configurations
     * Better utilization of all workers

   - **Limitations**: Slightly higher IPC overhead due to queue
     operations

**Load Balancing Explained**

Load balancing refers to how evenly work is distributed among
workers. Perfect balance means all workers finish at the same
time. Imbalance occurs when some workers finish much earlier than
others, leaving CPU cores idle.

**Example**: With 4 workers and 134 cycles:

- **Static mode**: Worker distribution might be [4, 47, 1, 82] cycles,
  resulting in 144.8% imbalance (some workers do 4x more work than
  others)

- **Dynamic mode**: Worker distribution might be [37, 29, 46, 22]
  cycles, resulting in 37.3% imbalance (much more balanced)

**When to Use Each Mode**

Based on profiling data from 12-bit, 14-bit, and 16-bit LFSRs:

- **Use Dynamic Mode** when:
  
  * Your LFSR produces many cycles (8+ cycles)
  * You're using 4+ workers
  * Load balancing is important for performance
  * Examples: 14-bit-v2 (134 cycles), 16-bit-v2 (260 cycles)

- **Use Static Mode** when:
  
  * Your LFSR produces few cycles (2-4 cycles)
  * The number of cycles is close to the number of workers
  * You want lower overhead
  * Examples: 12-bit-v1 (2 cycles), 14-bit-v1 (2 cycles), 16-bit-v1 (4
    cycles)

**Automatic Parallel Processing**:

.. code-block:: bash

   # For large LFSRs, parallel processing is automatically enabled
   lfsr-seq large_lfsr.csv 2

**Explicitly Enable Parallel Processing**:

.. code-block:: bash

   # Enable parallel processing (recommended for large LFSRs)
   lfsr-seq coefficients.csv 2 --parallel

**Choose Parallel Mode**:

.. code-block:: bash

   # Use dynamic mode (better load balancing for many cycles)
   lfsr-seq coefficients.csv 2 --parallel --parallel-mode dynamic

   # Use static mode (default, lower overhead)
   lfsr-seq coefficients.csv 2 --parallel --parallel-mode static

**Control Number of Workers**:

.. code-block:: bash

   # Use 4 parallel workers with dynamic mode
   lfsr-seq coefficients.csv 2 --parallel --parallel-mode dynamic --num-workers 4

**Disable Parallel Processing**:

.. code-block:: bash

   # Force sequential processing
   lfsr-seq coefficients.csv 2 --no-parallel

**How It Works**:

**Static Mode (Fixed Chunks)**:

1. **State Space Partitioning**: The state space is divided into
   fixed, equal-sized chunks, one per worker process. States are
   converted to tuples for serialization.

2. **SageMath Isolation**: Each worker creates fresh SageMath objects
   (GF, VectorSpace) to avoid category mismatch errors. This allows
   fork mode to be used safely.

3. **Matrix Reconstruction**: Each worker reconstructs the state
   update matrix from coefficients extracted from the **last column**
   of the companion matrix (critical for correctness).

4. **Parallel Processing**: Each worker processes its assigned chunk
   independently:
   
   - Uses enumeration algorithm to compute periods (faster than Floyd)
   - Computes cycle signatures (min_state) for deduplication
   - Marks states as visited locally

5. **Result Merging**: Results from all workers are merged, with
   automatic deduplication of sequences found by multiple workers
   using canonical cycle keys.

**Dynamic Mode (Shared Task Queue)**:

1. **Task Queue Creation**: States are divided into small batches (200
   states each) and placed in a shared queue accessible by all
   workers.

2. **SageMath Isolation**: Each worker creates fresh SageMath objects
   (GF, VectorSpace) to avoid category mismatch errors.

3. **Matrix Reconstruction**: Each worker reconstructs the state
   update matrix from coefficients (same as static mode).

4. **Dynamic Work Distribution**: Workers continuously pull batches
   from the queue:
   
   - When a worker finishes a batch, it immediately pulls the next
     available batch
   - Faster workers naturally take on more work
   - This provides automatic load balancing

5. **Result Merging**: Results from all workers are merged with
   deduplication (same as static mode).

**Both Modes**:

6. **Graceful Fallback**: If parallel processing fails or times out,
   the tool automatically falls back to sequential processing,
   ensuring the tool always completes successfully.

**Performance Considerations**:

- **Fork Mode**: Uses fork mode (Linux) which is 13-17x faster than
  spawn
  
- **SageMath Isolation**: Proper isolation prevents category mismatch
  errors
  
- **Automatic Selection**: Tool automatically selects best approach
  based on state space size
  
- **Best Performance**:
  
  - Large LFSRs (> 10,000 states): Use parallel (``--parallel``)
  - Small LFSRs (< 1,000 states): Use sequential (``--no-parallel``)
  - Medium LFSRs: Either works, parallel may provide modest speedup

**Known Limitations**:

- **Period-Only Mode Required**: Parallel processing requires
  period-only mode (``--period-only`` flag). Full sequence mode causes
  workers to hang due to SageMath/multiprocessing interaction
  issues. The tool automatically forces period-only mode when parallel
  processing is enabled, displaying a warning.

- **Algorithm Restriction**: Parallel processing uses Floyd's
  algorithm only, regardless of the ``--algorithm`` flag. This is
  necessary to avoid hangs from enumeration-based methods.

- **Timeout Detection**: The tool automatically detects timeouts and
  falls back to sequential processing if workers hang.

- **For Full Sequence Mode**: Use ``--no-parallel`` to force
  sequential processing if you need full sequence output (not just
  periods).

**Performance Profiling**:

Use the performance profiling script to measure speedup:

.. code-block:: bash

   # Profile parallel vs sequential performance
   python3 scripts/parallel_performance_profile.py input.csv 2 -w 1 2 4 --period-only

   # With detailed profiling
   python3 scripts/parallel_performance_profile.py input.csv 2 --profile --period-only

See ``scripts/PARALLEL_PERFORMANCE_REPORT.md`` for detailed
performance analysis.

.. _correlation-attack-options:

Correlation Attack Options
---------------------------

The tool includes a Correlation Attack Framework for analyzing
combination generators and stream ciphers. Correlation attacks exploit
statistical correlations between keystream and individual LFSR
outputs.

**What is a Combination Generator?**

A combination generator combines multiple LFSRs using a non-linear
function (e.g., majority, XOR, AND). The output is the result of
applying this function to the LFSR outputs.

**Basic Usage**:

Correlation attacks are performed programmatically using the Python
API:

.. code-block:: python

   from lfsr.attacks import (
       CombinationGenerator,
       LFSRConfig,
       siegenthaler_correlation_attack
   )
   
   # Create combination generator
   gen = CombinationGenerator(
       lfsrs=[
           LFSRConfig([1, 0, 0, 1], 2, 4),
           LFSRConfig([1, 1, 0, 1], 2, 4)
       ],
       combining_function=lambda a, b: a ^ b,
       function_name='xor'
   )
   
   # Generate keystream
   keystream = gen.generate_keystream(1000)
   
   # Perform attack
   result = siegenthaler_correlation_attack(gen, keystream, target_lfsr_index=0)

**Key Concepts**:

- **Correlation Coefficient**: Measures relationship between sequences (-1 to +1)
- **Correlation Immunity**: Security property of combining functions
- **Siegenthaler's Attack**: Fundamental correlation attack technique
- **Statistical Significance**: P-values test if correlation is significant

**CLI Usage**:

Correlation attacks can be performed from the command line:

.. code-block:: bash

   # Perform correlation attack using JSON configuration
   lfsr-seq dummy.csv 2 --correlation-attack --lfsr-configs config.json

   # Attack specific LFSR with custom significance level
   lfsr-seq dummy.csv 2 --correlation-attack --lfsr-configs config.json \
       --target-lfsr 0 --significance-level 0.01

   # Use pre-computed keystream from file
   lfsr-seq dummy.csv 2 --correlation-attack --lfsr-configs config.json \
       --keystream-file keystream.txt

   # Use fast correlation attack (Meier-Staffelbach)
   lfsr-seq dummy.csv 2 --correlation-attack --lfsr-configs config.json \
       --fast-correlation-attack --max-candidates 2000

   # Perform distinguishing attack
   lfsr-seq dummy.csv 2 --correlation-attack --lfsr-configs config.json \
       --distinguishing-attack --distinguishing-method statistical

**Correlation Attack Options**:

   --correlation-attack        Perform correlation attack
                               analysis. Requires ``--lfsr-configs``
                               file specifying multiple LFSRs and
                               combining function.
   --lfsr-configs CONFIG_FILE  JSON file containing combination
                               generator configuration (LFSRs and
                               combining function).  Required for
                               ``--correlation-attack``.
   --keystream-file FILE       File containing keystream bits (one per
                               line, or space-separated). If not
                               provided, keystream is generated from
                               combination generator.
   --target-lfsr INDEX         Index of LFSR to attack
                               (0-based). Default: 0 (first LFSR).
   --significance-level ALPHA  Statistical significance level for
                               correlation test (``default: 0.05``).
   --fast-correlation-attack   Use fast correlation attack
                               (Meier-Staffelbach) instead of basic
                               attack. More efficient for large state
                               spaces.
   --max-candidates N          Maximum number of candidate states to
                               test in fast correlation attack
                               (``default: 1000``).
   --distinguishing-attack     Perform distinguishing attack to
                               determine if keystream is
                               distinguishable from random.
   --distinguishing-method METHOD
                              Method for distinguishing attack:
                              ``correlation`` or ``statistical``
                              (``default: correlation``).

**Configuration File Format**:

The ``--lfsr-configs`` file should be JSON with this structure:

.. code-block:: json

   {
       "lfsrs": [
           {
               "coefficients": [1, 0, 0, 1],
               "field_order": 2,
               "degree": 4,
               "initial_state": [1, 0, 0, 0]
           },
           ...
       ],
       "combining_function": {
           "type": "majority",
           "num_inputs": 3
       }
   }

Supported combining function types: ``majority``, ``xor``, ``and``,
``or``, ``custom``.

**See Also**:

- :doc:`correlation_attacks` for comprehensive introduction
- :doc:`api/attacks` for complete API documentation
- ``examples/correlation_attack_example.py`` for working examples
- ``examples/combination_generator_config.json`` for configuration example

.. _nist-test-options:

NIST SP 800-22 Statistical Test Suite Options
----------------------------------------------

The tool includes the NIST SP 800-22 Statistical Test Suite for
evaluating the randomness of binary sequences. This is an
industry-standard test suite used in cryptographic evaluation.

**What is NIST SP 800-22?**

NIST SP 800-22 is a collection of 15 statistical tests developed by
the National Institute of Standards and Technology (NIST) for testing
the randomness of binary sequences. It is widely used to evaluate:

- Random number generators (RNGs)
- Pseudorandom number generators (PRNGs)
- Stream cipher outputs
- Any binary sequence that should appear random

**CLI Usage**:

Run NIST tests from the command line:

.. code-block:: bash

   # Run NIST test suite on a sequence file
   lfsr-seq dummy.csv 2 --nist-test --sequence-file sequence.txt

   # With custom significance level
   lfsr-seq dummy.csv 2 --nist-test --sequence-file sequence.txt \
       --nist-significance-level 0.05

   # With custom block size
   lfsr-seq dummy.csv 2 --nist-test --sequence-file sequence.txt \
       --nist-block-size 256

**Sequence File Format**:

The ``--sequence-file`` should contain binary bits (0s and 1s) in one
of these formats:

- One bit per line
- Space-separated bits on one or multiple lines

**NIST Test Suite Options**:

   --nist-test                  Run NIST SP 800-22 statistical test suite on
                                sequence. Requires sequence file or generates
                                from LFSR.
   --sequence-file FILE         File containing binary sequence (one bit per
                                line, or space-separated). Required for
                                ``--nist-test`` if not generating from LFSR.
   --nist-significance-level ALPHA
                                Statistical significance level for NIST tests
                                (``default: 0.01``).
   --nist-block-size SIZE       Block size for block-based NIST tests
                                (``default: 128``).
   --nist-output-format FORMAT  Output format for NIST test results: text,
                                json, csv, xml, or html (``default: text``).

**Export Formats**:

The NIST test suite supports multiple export formats for results:

- **text** (default): Human-readable text output
- **json**: JSON format for programmatic processing
- **csv**: CSV format for spreadsheet analysis
- **xml**: XML format for structured data
- **html**: HTML format with styling for viewing in browser

**Python API Usage**:

.. code-block:: python

   from lfsr.nist import run_nist_test_suite, frequency_test
   from lfsr.export import export_nist_to_json, export_nist_to_html
   
   # Load or generate sequence
   sequence = [1, 0, 1, 0] * 250  # 1000 bits
   
   # Run single test
   result = frequency_test(sequence)
   
   # Run complete suite
   suite_result = run_nist_test_suite(sequence, significance_level=0.01)
   print(f"Tests passed: {suite_result.tests_passed}/{suite_result.total_tests}")
   
   # Export to JSON
   with open('results.json', 'w') as f:
       export_nist_to_json(suite_result, f)
   
   # Export to HTML
   with open('results.html', 'w') as f:
       export_nist_to_html(suite_result, f)

**Key Concepts**:

- **P-value**: Probability that a random sequence would produce this
  result
- **Significance Level**: Threshold for rejecting randomness (default:
  0.01)
- **Test Suite**: Collection of 15 tests evaluating different aspects
  of randomness
- **Overall Assessment**: PASSED if most tests pass, FAILED otherwise

**See Also**:

- :doc:`nist_sp800_22` for comprehensive introduction and theory
- :doc:`api/nist` for complete API documentation
- ``examples/nist_test_example.py`` for working examples


.. code-block:: bash

   lfsr-seq coefficients.csv 2 --quiet

Custom Output File
~~~~~~~~~~~~~~~~~~

Specify a custom output file:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --output my_results.txt

JSON Export
~~~~~~~~~~~

Export results in JSON format:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --format json --output results.json

CSV Export
~~~~~~~~~~

Export results in CSV format:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --format csv --output results.csv

XML Export
~~~~~~~~~~

Export results in XML format:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --format xml --output results.xml

Non-Binary Fields
~~~~~~~~~~~~~~~~~

Analyze LFSR over GF(3):

.. code-block:: bash

   lfsr-seq coefficients.csv 3

Analyze LFSR over GF(4) = GF(2²):

.. code-block:: bash

   lfsr-seq coefficients.csv 4

.. _algebraic-attack-options:

Algebraic Attack Options
-------------------------

**CLI Usage**:

Algebraic attacks can be performed from the command line:

.. code-block:: bash

   # Perform Gröbner basis attack
   lfsr-seq coefficients.csv 2 --algebraic-attack --algebraic-method groebner_basis

   # Perform cube attack with custom max cube size
   lfsr-seq coefficients.csv 2 --algebraic-attack --algebraic-method cube_attack \
       --max-cube-size 8

   # Compute algebraic immunity
   lfsr-seq coefficients.csv 2 --algebraic-attack --algebraic-method algebraic_immunity

   # Gröbner basis attack with custom max equations
   lfsr-seq coefficients.csv 2 --algebraic-attack --algebraic-method groebner_basis \
       --max-equations 2000

**Algebraic Attack Options**:

   --algebraic-attack           Perform algebraic attack analysis. Requires
                                LFSR configuration and keystream.
   --algebraic-method METHOD    Method for algebraic attack: ``groebner_basis``,
                                ``cube_attack``, or ``algebraic_immunity``
                                (``default: groebner_basis``).
   --max-cube-size N            Maximum cube size for cube attack
                                (``default: 10``).
   --max-equations N            Maximum number of equations for Gröbner basis
                                attack (``default: 1000``).

.. _tmto-attack-options:

Time-Memory Trade-Off (TMTO) Attack Options
-------------------------------------------

**CLI Usage**:

TMTO attacks can be performed from the command line:

.. code-block:: bash

   # Perform Hellman TMTO attack
   lfsr-seq coefficients.csv 2 --tmto-attack --tmto-method hellman

   # Perform Rainbow table attack
   lfsr-seq coefficients.csv 2 --tmto-attack --tmto-method rainbow

   # Custom chain count and length
   lfsr-seq coefficients.csv 2 --tmto-attack --chain-count 2000 \
       --chain-length 150

   # Use precomputed table
   lfsr-seq coefficients.csv 2 --tmto-attack --tmto-table-file table.json

**TMTO Attack Options**:

   --tmto-attack              Perform time-memory trade-off attack.
                              Precomputes tables for faster state
                              recovery.
   --tmto-method METHOD       TMTO method: ``hellman`` or ``rainbow``
                              (``default: hellman``).
   --chain-count N            Number of chains in TMTO table
                              (``default: 1000``).
   --chain-length N           Length of each chain in TMTO table
                              (``default: 100``).
   --tmto-table-file FILE     File containing precomputed TMTO table
                              (JSON format). If not provided, table is
                              generated.

.. _stream-cipher-options:

Stream Cipher Analysis Options
-------------------------------

**CLI Usage**:

Stream cipher analysis can be performed from the command line:

.. code-block:: bash

   # Analyze A5/1 cipher structure
   lfsr-seq dummy.csv 2 --cipher a5_1 --analyze-cipher

   # Generate keystream from A5/1
   lfsr-seq dummy.csv 2 --cipher a5_1 --generate-keystream \
       --keystream-length 2000

   # Use key and IV from files
   lfsr-seq dummy.csv 2 --cipher a5_1 --generate-keystream \
       --key-file key.txt --iv-file iv.txt

   # Compare multiple ciphers
   lfsr-seq dummy.csv 2 --cipher a5_1 --compare-ciphers

**Stream Cipher Options**:

   --cipher NAME              Select stream cipher to analyze:
                              ``a5_1``, ``a5_2``, ``e0``, ``trivium``,
                              ``grain128``, ``grain128a``, or
                              ``lili128``.
   --analyze-cipher           Analyze cipher structure (LFSRs, clocking,
                              combining function).
   --generate-keystream       Generate keystream from key and IV.
   --keystream-length N       Length of keystream to generate in bits
                              (``default: 1000``).
   --key-file FILE            File containing key bits (binary or text
                              format).
   --iv-file FILE             File containing IV bits (binary or text
                              format).
   --compare-ciphers          Compare multiple ciphers side-by-side.

.. _advanced-structure-options:

Advanced LFSR Structures Options
---------------------------------

**CLI Usage**:

Advanced LFSR structure analysis can be performed from the command
line:

.. code-block:: bash

   # Analyze filtered LFSR
   lfsr-seq coefficients.csv 2 --advanced-structure filtered \
       --analyze-advanced-structure

   # Generate sequence from clock-controlled LFSR
   lfsr-seq coefficients.csv 2 --advanced-structure clock_controlled \
       --generate-advanced-sequence --advanced-sequence-length 2000

**Advanced Structure Options**:

   --advanced-structure TYPE  Select advanced structure type:
                              ``nfsr``, ``filtered``,
                              ``clock_controlled``, ``multi_output``,
                              or ``irregular``.
   --analyze-advanced-structure
                              Analyze advanced structure properties.
   --generate-advanced-sequence
                              Generate sequence from advanced structure.
   --advanced-sequence-length N
                              Length of sequence to generate (``default: 1000``).

.. _theoretical-analysis-options:

Theoretical Analysis Options
-----------------------------

**CLI Usage**:

Theoretical analysis features can be used from the command line:

.. code-block:: bash

   # Export results to LaTeX
   lfsr-seq coefficients.csv 2 --export-latex results.tex

   # Generate complete research paper
   lfsr-seq coefficients.csv 2 --generate-paper paper.tex

   # Compare with known results
   lfsr-seq coefficients.csv 2 --compare-known

   # Run performance benchmarks
   lfsr-seq coefficients.csv 2 --benchmark

   # Generate reproducibility report
   lfsr-seq coefficients.csv 2 --reproducibility-report report.json

**Theoretical Analysis Options**:

   --export-latex FILE        Export analysis results to LaTeX format
                              (specify output file).
   --generate-paper FILE      Generate complete research paper from
                              analysis results (specify output file).
   --compare-known            Compare computed results with known results
                              in database.
   --benchmark                Run performance benchmarks for analysis
                              methods.
   --reproducibility-report FILE
                              Generate reproducibility report (specify
                              output file).

.. _visualization-options:

Visualization Options
---------------------

**CLI Usage**:

Visualizations can be generated from the command line:

.. code-block:: bash

   # Generate period distribution plot
   lfsr-seq coefficients.csv 2 --plot-period-distribution plot.png

   # Generate state transition diagram
   lfsr-seq coefficients.csv 2 --plot-state-transitions diagram.svg

   # Generate period statistics plot
   lfsr-seq coefficients.csv 2 --plot-period-statistics stats.pdf

   # Generate 3D state space visualization
   lfsr-seq coefficients.csv 2 --plot-3d-state-space space.html

   # Visualize attack results
   lfsr-seq coefficients.csv 2 --visualize-attack attack.png

   # Interactive HTML visualization
   lfsr-seq coefficients.csv 2 --plot-period-distribution plot.html \
       --viz-format html --viz-interactive

**Visualization Options**:

   --plot-period-distribution FILE
                               Generate period distribution plot (specify output
                               file).
   --plot-state-transitions FILE
                               Generate state transition diagram (specify output
                               file).
   --plot-period-statistics FILE
                               Generate statistical plots for period
                               distribution (specify output file).
   --plot-3d-state-space FILE  Generate 3D state space visualization
                               (specify output file).
   --visualize-attack FILE     Visualize attack results (specify output file).
   --viz-format FORMAT         Output format for visualizations: png, svg,
                               pdf, or html (``default: png``).
   --viz-interactive           Generate interactive visualizations (HTML
                               format).

.. _machine-learning-options:

Machine Learning Options
------------------------

**CLI Usage**:

ML-based analysis can be performed from the command line:

.. code-block:: bash

   # Predict period using ML model
   lfsr-seq coefficients.csv 2 --predict-period --ml-model-file model.pkl

   # Detect patterns in sequences
   lfsr-seq coefficients.csv 2 --detect-patterns

   # Detect anomalies
   lfsr-seq coefficients.csv 2 --detect-anomalies

   # Train ML model
   lfsr-seq coefficients.csv 2 --train-model model.pkl

**Machine Learning Options**:

   --predict-period           Predict period using ML model (requires
                              trained model).
   --detect-patterns          Detect patterns in generated sequences.
   --detect-anomalies         Detect anomalies in sequences and
                              distributions.
   --train-model FILE         Train ML model and save to file (specify
                              output file).
   --ml-model-file FILE       Path to trained ML model file (for prediction).

