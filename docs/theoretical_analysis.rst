Theoretical Analysis
====================

This section provides comprehensive documentation for theoretical analysis
features, including irreducible polynomial analysis, LaTeX export, research
paper generation, known result database, benchmarking, and reproducibility.

**Key Terminology**:

- **Theoretical Analysis**: Analysis that compares computed results with
  theoretical predictions and known results, ensuring correctness and
  providing research insights.

- **Irreducible Polynomial**: A polynomial that cannot be factored into
  polynomials of lower degree over the given field.

- **LaTeX Export**: Converting analysis results into LaTeX format for
  inclusion in research papers.

- **Reproducibility**: The ability to reproduce research results using
  the same methods, data, and parameters.

Introduction
------------

The theoretical analysis features provide research-oriented capabilities
for LFSR analysis, enabling:

1. **Enhanced Analysis**: Comprehensive irreducible polynomial analysis
   with factorization and order computation

2. **Publication Support**: LaTeX export and research paper generation
   for documenting findings

3. **Verification**: Comparison with known results database for correctness
   verification

4. **Performance Analysis**: Benchmarking framework for comparing methods

5. **Reproducibility**: Complete environment and configuration tracking
   for scientific reproducibility

Irreducible Polynomial Analysis
--------------------------------

**What is Irreducible Polynomial Analysis?**

Irreducible polynomial analysis provides comprehensive analysis of polynomial
properties, including irreducibility, factorization, factor orders, and
primitive factor detection.

**Key Features**:

- **Irreducibility Testing**: Determine if polynomial is irreducible
- **Factorization**: Factor polynomial into irreducible components
- **Factor Orders**: Compute order of each irreducible factor
- **Order Relationships**: Verify LCM of factor orders equals polynomial order
- **Primitive Detection**: Identify primitive factors

**Mathematical Foundation**:

For a polynomial P(t) that factors as:

.. math::

   P(t) = \\prod_{i=1}^{k} f_i(t)^{e_i}

where f_i(t) are irreducible factors, the order of P(t) is:

.. math::

   \\text{ord}(P(t)) = \\text{lcm}(\\text{ord}(f_1(t)), \\ldots, \\text{ord}(f_k(t)))

**Python API Usage**:

.. code-block:: python

   from lfsr.theoretical import analyze_irreducible_properties
   from sage.all import *
   
   F = GF(2)
   R = PolynomialRing(F, "t")
   p = R("t^4 + t^3 + t + 1")
   
   analysis = analyze_irreducible_properties(p, 2)
   print(f"Is irreducible: {analysis.is_irreducible}")
   print(f"Number of factors: {len(analysis.factors)}")
   print(f"Polynomial order: {analysis.polynomial_order}")

LaTeX Export
------------

**What is LaTeX Export?**

LaTeX export converts analysis results into LaTeX format, enabling
publication-quality output for research papers and reports.

**Key Features**:

- **Polynomial Representation**: Convert polynomials to LaTeX format
- **Table Generation**: Generate professional tables for analysis results
- **Complete Documents**: Generate standalone LaTeX documents
- **Table Fragments**: Generate tables for inclusion in existing papers

**Python API Usage**:

.. code-block:: python

   from lfsr.export_latex import export_to_latex_file
   
   analysis_results = {
       'polynomial': {...},
       'period_distribution': {...}
   }
   
   export_to_latex_file(analysis_results, "results.tex")

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --export-latex results.tex

Research Paper Generation
-------------------------

**What is Research Paper Generation?**

Research paper generation automatically creates complete research paper
sections from analysis results, including abstract, methodology, results,
and discussion.

**Key Features**:

- **Automatic Section Generation**: Generate all standard paper sections
- **LaTeX Integration**: Integrates with LaTeX export for tables
- **Customizable Content**: Customize title, author, focus, observations
- **Professional Formatting**: Standard academic paper structure

**Python API Usage**:

.. code-block:: python

   from lfsr.paper_generator import generate_complete_paper
   
   analysis_results = {...}
   paper = generate_complete_paper(
       analysis_results,
       title="LFSR Analysis Results",
       author="Researcher Name"
   )
   
   with open("paper.tex", "w") as f:
       f.write(paper)

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --generate-paper paper.tex

Known Result Database
---------------------

**What is the Known Result Database?**

The known result database stores and retrieves known theoretical results,
enabling comparison with computed results for verification.

**Key Features**:

- **Primitive Polynomial Storage**: Store known primitive polynomials
- **Order Storage**: Store known polynomial orders
- **Comparison**: Compare computed results with known results
- **Verification**: Verify correctness of analysis algorithms

**Python API Usage**:

.. code-block:: python

   from lfsr.theoretical_db import get_database
   
   db = get_database()
   comparison = db.compare_with_known(
       coefficients=[1, 0, 0, 1],
       field_order=2,
       degree=4,
       computed_order=15,
       computed_is_primitive=True
   )
   
   print(f"Found in database: {comparison['found_in_database']}")
   print(f"Matches: {comparison['matches']}")

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --compare-known

Benchmarking Framework
----------------------

**What is Benchmarking?**

Benchmarking measures and compares the performance of different analysis
methods, helping identify the most efficient approach.

**Key Features**:

- **Performance Measurement**: Measure execution time of methods
- **Accuracy Verification**: Verify correctness of results
- **Method Comparison**: Compare different methods side-by-side
- **Benchmark Suites**: Run multiple benchmarks and aggregate results

**Python API Usage**:

.. code-block:: python

   from lfsr.benchmarking import compare_methods
   
   results = compare_methods(
       coefficients=[1, 0, 0, 1],
       field_order=2,
       expected_period=15
   )
   
   for method, result in results.items():
       print(f"{method}: {result.execution_time:.6f} seconds")

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --benchmark

Reproducibility Features
------------------------

**What is Reproducibility?**

Reproducibility ensures that research results can be reproduced by others
using the same methods, data, and parameters.

**Key Features**:

- **Seed Tracking**: Track random seeds for reproducibility
- **Environment Capture**: Capture system and software environment
- **Configuration Export**: Export complete analysis configuration
- **Reproducibility Reports**: Generate comprehensive reproducibility reports

**Python API Usage**:

.. code-block:: python

   from lfsr.reproducibility import generate_reproducibility_report
   
   report = generate_reproducibility_report(
       analysis_results={...},
       analysis_config={...},
       seed=12345
   )
   
   with open("reproducibility.json", "w") as f:
       f.write(report)

**Command-Line Usage**:

.. code-block:: bash

   lfsr-seq coefficients.csv 2 --reproducibility-report report.json

API Reference
-------------

See :doc:`api/theoretical` for complete API documentation.

Glossary
--------

**Benchmarking**
   The process of measuring and comparing the performance of different
   methods or algorithms.

**Configuration Export**
   Saving all parameters and settings used in an analysis for reproducibility.

**Environment Capture**
   Recording information about the computing environment for reproducibility.

**Irreducible Polynomial**
   A polynomial that cannot be factored into polynomials of lower degree.

**Known Result Database**
   A collection of previously computed or published theoretical results.

**LaTeX**
   A document preparation system for typesetting mathematical formulas.

**Reproducibility**
   The ability to reproduce research results using the same methods and data.

**Reproducibility Report**
   A document containing all information needed to reproduce research results.

**Theoretical Analysis**
   Analysis comparing computed results with theoretical predictions.

Further Reading
---------------

- Menezes, A. J., et al. (1996). "Handbook of Applied Cryptography"
- Golomb, S. W. (1967). "Shift Register Sequences"
- Rueppel, R. A. (1986). "Analysis and Design of Stream Ciphers"
