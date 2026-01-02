Examples
========

Basic LFSR Analysis
-------------------

Analyze a simple 4-bit LFSR over GF(2):

.. code-block:: bash

   echo "1,1,0,1" > test.csv
   lfsr-seq test.csv 2

This will generate ``test.csv.out`` with:
- State update matrix
- All state sequences and their periods
- Characteristic polynomial and its order

Multiple LFSR Configurations
----------------------------

Analyze multiple LFSR configurations:

.. code-block:: bash

   cat > lfsrs.csv << EOF
   1,1,0,1
   1,0,1,1
   1,1,1,0,1
   EOF
   lfsr-seq lfsrs.csv 2

Each row will be analyzed separately.

Non-Binary Fields
-----------------

Analyze LFSR over GF(3):

.. code-block:: bash

   echo "1,2,1" > gf3.csv
   lfsr-seq gf3.csv 3

Export to JSON
~~~~~~~~~~~~~~

Export results in JSON format:

.. code-block:: bash

   lfsr-seq strange.csv 2 --format json --output results.json

The JSON file will contain structured data suitable for programmatic processing.

Parallel Processing
-------------------

Use parallel processing for faster analysis of larger LFSRs:

.. code-block:: bash

   # Enable parallel processing explicitly
   lfsr-seq coefficients.csv 2 --parallel --period-only

   # Use specific number of workers
   lfsr-seq coefficients.csv 2 --parallel --num-workers 4 --period-only

   # Auto-detection (enabled for large state spaces)
   lfsr-seq large_lfsr.csv 2 --period-only

**Note**: Parallel processing requires ``--period-only`` mode. The tool automatically
forces period-only mode when parallel is enabled, displaying a warning.

Python API Usage
----------------

Use the library programmatically:

.. code-block:: python

   from sage.all import *
   from lfsr.cli import main
   from lfsr.synthesis import berlekamp_massey, linear_complexity
   from lfsr.statistics import statistical_summary
   from lfsr.core import build_state_update_matrix, compute_matrix_order
   from lfsr.polynomial import characteristic_polynomial, polynomial_order
   from lfsr.field import validate_gf_order, validate_coefficient_vector

   # Analyze LFSR from CSV file
   with open("output.txt", "w") as f:
       main("coefficients.csv", "2", output_file=f)

   # Synthesize LFSR from sequence using Berlekamp-Massey
   sequence = [1, 0, 1, 1, 0, 1, 0, 0, 1]
   poly, complexity = berlekamp_massey(sequence, 2)
   print(f"Linear complexity: {complexity}")

   # Calculate linear complexity directly
   complexity = linear_complexity(sequence, 2)
   print(f"Linear complexity: {complexity}")

   # Statistical analysis
   stats = statistical_summary(sequence, 2)
   print(f"Frequency ratio: {stats['frequency']['ratio']}")
   print(f"Total runs: {stats['runs']['total_runs']}")

   # Build state update matrix
   coeffs = [1, 1, 0, 1]
   C, CS = build_state_update_matrix(coeffs, 2)
   d = len(coeffs)
   state_vector_space_size = 2 ** d
   M = MatrixSpace(GF(2), d, d)
   I = M.identity_matrix()
   order = compute_matrix_order(C, I, state_vector_space_size)
   print(f"Matrix order (period): {order}")

   # Characteristic polynomial
   char_poly = characteristic_polynomial(CS, 2)
   poly_order = polynomial_order(char_poly, d, 2)
   print(f"Polynomial order: {poly_order}")

   # Field validation
   gf_order = validate_gf_order("4")  # Returns 4
   validate_coefficient_vector([1, 2, 3], 4)  # Validates coefficients for GF(4)

Correlation Attacks
-------------------

Perform correlation attacks on combination generators:

.. code-block:: python

   from lfsr.attacks import (
       CombinationGenerator,
       LFSRConfig,
       siegenthaler_correlation_attack
   )
   
   # Define a majority function
   def majority(a, b, c):
       return 1 if (a + b + c) >= 2 else 0
   
   # Create combination generator
   gen = CombinationGenerator(
       lfsrs=[
           LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4),
           LFSRConfig(coefficients=[1, 1, 0, 1], field_order=2, degree=4),
           LFSRConfig(coefficients=[1, 0, 1, 1], field_order=2, degree=4)
       ],
       combining_function=majority,
       function_name='majority'
   )
   
   # Generate keystream
   keystream = gen.generate_keystream(length=1000)
   
   # Attack the first LFSR
   result = siegenthaler_correlation_attack(
       combination_generator=gen,
       keystream=keystream,
       target_lfsr_index=0
   )
   
   if result.attack_successful:
       print(f"Attack succeeded! Correlation: {result.correlation_coefficient:.4f}")
   else:
       print("No significant correlation detected")

Analyze Combining Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Analyze the security properties of combining functions:

.. code-block:: python

   from lfsr.attacks import analyze_combining_function
   
   def majority(a, b, c):
       return 1 if (a + b + c) >= 2 else 0
   
   analysis = analyze_combining_function(majority, num_inputs=3)
   print(f"Balanced: {analysis['balanced']}")
   print(f"Bias: {analysis['bias']}")
   print(f"Correlation immunity order: {analysis['correlation_immunity']}")

**Fast Correlation Attack**:

.. code-block:: python

   from lfsr.attacks import fast_correlation_attack
   
   # Perform fast correlation attack
   result = fast_correlation_attack(
       combination_generator=gen,
       keystream=keystream,
       target_lfsr_index=0,
       max_candidates=1000
   )
   
   if result.attack_successful:
       print(f"Recovered state: {result.recovered_state}")

**Distinguishing Attack**:

.. code-block:: python

   from lfsr.attacks import distinguishing_attack
   
   # Test if keystream is distinguishable
   result = distinguishing_attack(
       combination_generator=gen,
       keystream=keystream,
       method="correlation"
   )
   
   if result.distinguishable:
       print("Keystream is distinguishable from random!")

For complete examples, see ``examples/correlation_attack_example.py``.

Optimization Techniques
-----------------------

**Period Computation via Factorization**:

.. code-block:: python

   from lfsr.polynomial import compute_period_via_factorization
   
   # Compute period using factorization (faster for large LFSRs)
   period = compute_period_via_factorization([1, 0, 0, 1], 2)
   print(f"Period: {period}")

**Mathematical Shortcut Detection**:

.. code-block:: python

   from lfsr.polynomial import detect_mathematical_shortcuts
   
   # Detect special cases and get recommendations
   shortcuts = detect_mathematical_shortcuts([1, 0, 0, 1], 2)
   
   if shortcuts['is_primitive']:
       print(f"Primitive polynomial! Period = {shortcuts['expected_period']}")
   print(f"Recommended method: {shortcuts['recommended_method']}")
   print(f"Complexity: {shortcuts['complexity_estimate']}")

**Result Caching**:

.. code-block:: python

   from lfsr.optimization import ResultCache, get_global_cache
   
   # Use global cache
   cache = get_global_cache()
   
   # Generate cache key
   key = cache.generate_key([1, 0, 0, 1], 2, "period")
   
   # Check cache before computing
   if key in cache:
       period = cache.get(key)
       print(f"Cached period: {period}")
   else:
       period = compute_period_via_factorization([1, 0, 0, 1], 2)
       cache.set(key, period)
       print(f"Computed period: {period}")
   
   # Get cache statistics
   stats = cache.get_stats()
   print(f"Cache hit rate: {stats['hit_rate']:.2%}")

For complete examples, see ``examples/optimization_example.py``.

Algebraic Attacks
-----------------

**Algebraic Immunity Computation**:

.. code-block:: python

   from lfsr.attacks import compute_algebraic_immunity
   
   def filtering_function(x0, x1, x2, x3):
       return x0 & x1  # Example filtering function
   
   result = compute_algebraic_immunity(filtering_function, 4)
   print(f"Algebraic immunity: {result['algebraic_immunity']}")
   print(f"Optimal: {result['optimal']}")

**Gröbner Basis Attack**:

.. code-block:: python

   from lfsr.attacks import LFSRConfig, groebner_basis_attack
   
   lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
   keystream = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
   
   result = groebner_basis_attack(lfsr, keystream)
   if result.attack_successful:
       print(f"Recovered state: {result.recovered_state}")

**Cube Attack**:

.. code-block:: python

   from lfsr.attacks import LFSRConfig, cube_attack
   
   lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
   keystream = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
   
   result = cube_attack(lfsr, keystream, max_cube_size=5)
   if result.attack_successful:
       print(f"Cubes found: {result.cubes_found}")
       print(f"Recovered bits: {result.recovered_bits}")

For complete examples, see ``examples/algebraic_attack_example.py``.

Time-Memory Trade-Off Attacks
------------------------------

**Hellman Table Attack**:

.. code-block:: python

   from lfsr.attacks import LFSRConfig
   from lfsr.tmto import tmto_attack
   
   lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
   target_state = [1, 0, 1, 1]
   
   result = tmto_attack(
       lfsr_config=lfsr,
       target_state=target_state,
       method="hellman"
   )
   if result.attack_successful:
       print(f"Recovered state: {result.recovered_state}")
       print(f"Coverage: {result.coverage:.2%}")

**Rainbow Table Attack**:

.. code-block:: python

   from lfsr.tmto import tmto_attack
   
   result = tmto_attack(
       lfsr_config=lfsr,
       target_state=target_state,
       method="rainbow",
       chain_count=2000,
       chain_length=150
   )

**Parameter Optimization**:

.. code-block:: python

   from lfsr.tmto import optimize_tmto_parameters
   
   params = optimize_tmto_parameters(
       state_space_size=16,
       available_memory=100000
   )
   print(f"Optimal chain count: {params['chain_count']}")
   print(f"Optimal chain length: {params['chain_length']}")

For complete examples, see ``examples/tmto_attack_example.py``.

NIST SP 800-22 Test Suite
--------------------------

Run NIST statistical tests on binary sequences:

.. code-block:: python

   from lfsr.nist import run_nist_test_suite, frequency_test
   
   # Generate or load a binary sequence
   sequence = [1, 0, 1, 0, 1, 1, 0, 0, 1, 0] * 100  # 1000 bits
   
   # Run a single test
   result = frequency_test(sequence)
   print(f"P-value: {result.p_value:.6f}")
   print(f"Passed: {result.passed}")
   
   # Run the complete test suite
   suite_result = run_nist_test_suite(sequence)
   print(f"Tests passed: {suite_result.tests_passed}/{suite_result.total_tests}")
   print(f"Overall: {suite_result.overall_assessment}")

For complete examples, see ``examples/nist_test_example.py``.

Visualization
-------------

Generate visualizations of LFSR analysis results:

**Period Distribution Plot**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --plot-period-distribution --output-period-plot period_dist.png

**State Transition Diagram**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --plot-state-transitions --output-state-diagram states.png

**3D State Space Visualization**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --plot-3d-state-space --output-3d-plot state_space_3d.html

**Python API**:

.. code-block:: python

   from sage.all import *
   from lfsr.core import build_state_update_matrix
   from lfsr.analysis import lfsr_sequence_mapper
   from lfsr.visualization import (
       plot_period_distribution,
       generate_state_transition_diagram,
       plot_3d_state_space,
       VisualizationConfig,
       OutputFormat
   )
   
   # Analyze LFSR
   coeffs = [1, 0, 0, 1]
   C, CS = build_state_update_matrix(coeffs, 2)
   V = VectorSpace(GF(2), 4)
   seq_dict, period_dict, max_period, _, _, _, _ = lfsr_sequence_mapper(
       C, V, 2, output_file=None, no_progress=True, period_only=False
   )
   
   # Create period distribution plot
   config = VisualizationConfig(
       title="Period Distribution",
       output_format=OutputFormat.PNG
   )
   plot_period_distribution(
       period_dict,
       theoretical_max_period=15,
       is_primitive=False,
       config=config,
       output_file="period_dist.png"
   )
   
   # Generate state transition diagram
   generate_state_transition_diagram(
       seq_dict,
       period_dict,
       config=config,
       output_file="state_diagram.png"
   )

For complete examples, see ``examples/visualization_example.py``.

Machine Learning Integration
----------------------------

Use machine learning for period prediction, pattern detection, and anomaly detection:

**Period Prediction**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --predict-period --ml-model-file model.pkl

**Pattern Detection**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --detect-patterns --output-patterns patterns.json

**Anomaly Detection**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --detect-anomalies --output-anomalies anomalies.json

**Train Model**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --train-model --ml-model-file model.pkl --training-samples 100

**Python API**:

.. code-block:: python

   from lfsr.ml.period_prediction import PeriodPredictionModel, create_period_prediction_model
   from lfsr.ml.pattern_detection import detect_all_patterns
   from lfsr.ml.anomaly_detection import detect_all_anomalies
   from lfsr.ml.training import generate_training_data, train_period_prediction_model
   
   # Train period prediction model
   X, y = generate_training_data(num_samples=100, max_degree=8, field_order=2)
   model = create_period_prediction_model("random_forest")
   metrics = model.train(X, y)
   print(f"R² Score: {metrics['r2_score']:.4f}")
   
   # Predict period for new polynomial
   coefficients = [1, 0, 0, 1]
   predicted = model.predict_period(coefficients, field_order=2)
   print(f"Predicted period: {predicted:.2f}")
   
   # Detect patterns in sequence
   sequence = [1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1]
   patterns = detect_all_patterns(sequence)
   print(f"Detected {len(patterns)} pattern types")
   
   # Detect anomalies
   anomalies = detect_all_anomalies(sequence)
   print(f"Found {len(anomalies)} anomalies")

For complete examples, see ``examples/ml_integration_example.py``.

Stream Cipher Analysis
----------------------

Analyze real-world stream ciphers:

**Analyze A5/1 Cipher**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --cipher a5_1 --analyze-cipher

**Generate Keystream**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --cipher e0 --generate-keystream --keystream-length 1000 --key-file key.bin --iv-file iv.bin

**Compare Ciphers**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --compare-ciphers a5_1 e0 trivium --output-comparison comparison.json

**Python API**:

.. code-block:: python

   from lfsr.ciphers import A5_1, E0, Trivium
   from lfsr.ciphers.comparison import compare_ciphers, generate_comparison_report
   
   # Analyze A5/1 cipher
   cipher = A5_1()
   structure = cipher.analyze_structure()
   print(f"Number of LFSRs: {len(structure.lfsr_configs)}")
   print(f"Total state size: {structure.state_size} bits")
   
   # Generate keystream
   key = [1, 0, 1] * 21 + [1]  # 64-bit key
   iv = [0] * 22  # 22-bit IV
   keystream = cipher.generate_keystream(key, iv, 1000)
   print(f"Generated {len(keystream)} bits")
   
   # Compare multiple ciphers
   ciphers = [A5_1(), E0(), Trivium()]
   comparison = compare_ciphers(ciphers)
   print(f"Comparison report: {comparison}")

For complete examples, see ``examples/stream_cipher_example.py``.

Advanced LFSR Structures
------------------------

Analyze advanced LFSR structures (NFSRs, filtered LFSRs, clock-controlled LFSRs, etc.):

**Analyze Advanced Structure**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --advanced-structure filtered --analyze-advanced-structure

**Generate Advanced Sequence**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --advanced-structure clock-controlled --generate-advanced-sequence --advanced-sequence-length 1000

**Python API**:

.. code-block:: python

   from lfsr.attacks import LFSRConfig
   from lfsr.advanced import (
       NFSR,
       FilteredLFSR,
       ClockControlledLFSR,
       create_simple_filtered_lfsr,
       create_stop_and_go_lfsr
   )
   
   # Create filtered LFSR
   base_lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
   
   def filtering_function(state):
       return state[0] & state[1]  # Non-linear filtering
   
   filtered = create_simple_filtered_lfsr(base_lfsr, filtering_function)
   analysis = filtered.analyze()
   print(f"Structure type: {analysis.structure_type}")
   
   # Generate sequence
   initial_state = [1, 0, 0, 0]
   sequence = filtered.generate_sequence(initial_state, 100)
   print(f"Generated {len(sequence)} sequence elements")
   
   # Create clock-controlled LFSR
   clock_controlled = create_stop_and_go_lfsr(base_lfsr)
   sequence_cc = clock_controlled.generate_sequence(initial_state, 100)
   print(f"Clock-controlled sequence: {len(sequence_cc)} elements")

For complete examples, see ``examples/advanced_lfsr_example.py``.

Theoretical Analysis
--------------------

Perform theoretical analysis, export to LaTeX, generate papers, and benchmark methods:

**Export to LaTeX**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --export-latex --latex-output analysis.tex

**Generate Complete Paper**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --generate-paper --paper-output paper.tex

**Compare with Known Results**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --compare-known --database-output comparison.json

**Benchmark Methods**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --benchmark --benchmark-output benchmark.json

**Python API**:

.. code-block:: python

   from sage.all import *
   from lfsr.theoretical import analyze_irreducible_properties
   from lfsr.export_latex import export_to_latex_file, polynomial_to_latex
   from lfsr.paper_generator import generate_complete_paper
   from lfsr.benchmarking import compare_methods
   
   # Analyze irreducible polynomial
   F = GF(2)
   R = PolynomialRing(F, "t")
   p = R("t^4 + t^3 + t + 1")
   
   analysis = analyze_irreducible_properties(p, 2)
   print(f"Is irreducible: {analysis.is_irreducible}")
   print(f"Polynomial order: {analysis.polynomial_order}")
   
   # Export to LaTeX
   latex_str = polynomial_to_latex(p)
   print(f"LaTeX: ${latex_str}$")
   
   # Generate complete paper
   analysis_results = {
       'field_order': 2,
       'lfsr_degree': 4,
       'polynomial': {'polynomial': p, 'order': analysis.polynomial_order},
       'is_primitive': False
   }
   paper = generate_complete_paper(analysis_results, "paper.tex")
   print("Paper generated successfully")
   
   # Benchmark different methods
   coefficients = [1, 0, 0, 1]
   benchmark_results = compare_methods(coefficients, 2)
   print(f"Benchmark results: {benchmark_results}")

For complete examples, see ``examples/theoretical_analysis_example.py``.


Parallel Processing API
------------------------

Use parallel processing programmatically:

.. code-block:: python

   from sage.all import *
   from lfsr.analysis import lfsr_sequence_mapper_parallel
   from lfsr.core import build_state_update_matrix

   # Build state update matrix
   coeffs = [1, 0, 0, 1]
   C, CS = build_state_update_matrix(coeffs, 2)
   V = VectorSpace(GF(2), 4)

   # Parallel processing with 2 workers
   seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
       C, V, 2, output_file=None, no_progress=True,
       algorithm="floyd", period_only=True, num_workers=2
   )

   print(f"Found {len(seq_dict)} sequences")
   print(f"Maximum period: {max_period}")
   print(f"Period sum: {periods_sum} (should equal state space size)")

   # Compare with sequential
   from lfsr.analysis import lfsr_sequence_mapper
   seq_dict_seq, period_dict_seq, max_period_seq, periods_sum_seq = lfsr_sequence_mapper(
       C, V, 2, output_file=None, no_progress=True,
       period_only=True
   )

   # Verify correctness
   assert max_period == max_period_seq
   assert periods_sum == 16  # State space size for 4-bit LFSR
   assert periods_sum_seq == 16

