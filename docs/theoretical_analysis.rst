Theoretical Analysis
====================

This section provides comprehensive documentation for theoretical analysis
features, including irreducible polynomial analysis, LaTeX export, research
paper generation, known result databases, benchmarking, and reproducibility.

**Key Terminology**:

- **Theoretical Analysis**: Analysis that compares computed results with
  theoretical predictions and known results, ensuring correctness and
  providing insights into mathematical properties.

- **Irreducible Polynomial**: A polynomial that cannot be factored into
  polynomials of lower degree over the given field.

- **LaTeX Export**: Converting analysis results into LaTeX format for
  inclusion in research papers and publications.

- **Reproducibility**: The ability to reproduce research results using
  the same methods, data, and configuration.

Introduction
------------

The theoretical analysis module provides research-oriented features for
LFSR analysis, enabling:

1. **Enhanced Polynomial Analysis**: Comprehensive analysis of irreducible
   polynomials, factorization, and theoretical properties.

2. **Publication-Quality Export**: LaTeX export for research papers with
   professional formatting.

3. **Research Paper Generation**: Automatic generation of research paper
   sections from analysis results.

4. **Known Result Database**: Storage and retrieval of known theoretical
   results for comparison and verification.

5. **Benchmarking**: Performance and accuracy comparison of different
   analysis methods.

6. **Reproducibility**: Complete documentation and verification for
   research reproducibility.

Irreducible Polynomial Analysis
--------------------------------

**What is Irreducible Polynomial Analysis?**

Irreducible polynomial analysis provides comprehensive examination of
polynomial properties including irreducibility, factorization, factor orders,
and relationships between factors and the full polynomial.

**Key Terminology**:

- **Irreducible Polynomial**: A polynomial that cannot be factored into
  polynomials of lower degree. For example, over GF(2), t^2 + t + 1 is
  irreducible, but t^2 + 1 = (t+1)^2 is not.

- **Polynomial Factorization**: Decomposing a polynomial into irreducible
  factors. For example, t^4 + t^3 + t + 1 = (t+1)(t^3 + t + 1) over GF(2).

- **Factor Order**: The order of an irreducible factor f(t) is the smallest
  positive integer n such that t^n ≡ 1 (mod f(t)).

- **Polynomial Order**: The order of polynomial P(t) is the smallest positive
  integer n such that t^n ≡ 1 (mod P(t)). For a polynomial with factors
  f_i(t), the order is LCM(ord(f_1), ..., ord(f_k)).

**Mathematical Foundation**:

For a polynomial P(t) over GF(q) that factors as:

.. math::

   P(t) = \\prod_{i=1}^{k} f_i(t)^{e_i}

where f_i(t) are irreducible factors, the order of P(t) is:

.. math::

   \\text{ord}(P(t)) = \\text{lcm}(\\text{ord}(f_1(t)), \\ldots, \\text{ord}(f_k(t)))

**Usage**:

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

**Key Terminology**:

- **LaTeX**: A document preparation system widely used in academic
  publishing for typesetting mathematical formulas and scientific documents.

- **LaTeX Table**: Structured data presentation in LaTeX using tabular
  environment, commonly used in research papers.

- **Polynomial Representation**: Mathematical notation for polynomials
  in LaTeX format, e.g., t^4 + t^3 + t + 1.

**Usage**:

.. code-block:: python

   from lfsr.export_latex import export_polynomial_analysis_to_latex
   from sage.all import *
   
   F = GF(2)
   R = PolynomialRing(F, "t")
   p = R("t^4 + t^3 + t + 1")
   
   latex_code = export_polynomial_analysis_to_latex(
       polynomial=p,
       polynomial_order=6,
       is_primitive=False,
       is_irreducible=False,
       field_order=2
   )
   
   # Write to file
   with open("analysis.tex", "w") as f:
       f.write(latex_code)

Research Paper Generation
--------------------------

**What is Research Paper Generation?**

Research paper generation automatically creates research paper sections
(abstract, methodology, results, discussion) from analysis results.

**Key Terminology**:

- **Research Paper**: A formal document presenting original research findings,
  following standard academic structure and formatting conventions.

- **Abstract**: A brief summary of a research paper, typically 150-250 words.

- **Methodology**: The section describing methods, techniques, and procedures
  used to conduct the research.

- **Results Section**: The section presenting findings, including tables and
  statistical summaries.

- **Discussion Section**: The section interpreting results and discussing
  implications.

**Usage**:

.. code-block:: python

   from lfsr.paper_generator import generate_complete_paper
   
   analysis_results = {
       'field_order': 2,
       'lfsr_degree': 4,
       'is_primitive': False,
       'max_period': 6,
       'theoretical_max_period': 15
   }
   
   paper = generate_complete_paper(
       analysis_results,
       title="LFSR Period Analysis",
       author="Research Team"
   )
   
   with open("paper.tex", "w") as f:
       f.write(paper)

Known Result Database
---------------------

**What is the Known Result Database?**

The known result database stores and retrieves known theoretical results,
enabling comparison with computed results for verification.

**Key Terminology**:

- **Known Result Database**: A collection of precomputed or published
  theoretical results for comparison and verification.

- **Result Verification**: Comparing computed results with known results
  to verify correctness.

**Usage**:

.. code-block:: python

   from lfsr.theoretical_db import TheoreticalDatabase
   
   db = TheoreticalDatabase()
   
   # Find known polynomial
   known = db.find_polynomial([1, 0, 0, 1], 2)
   if known:
       print(f"Order: {known.order}")
       print(f"Primitive: {known.is_primitive}")
   
   # Compare with computed results
   comparison = db.compare_with_known(
       [1, 0, 0, 1], 2,
       computed_order=6,
       computed_is_primitive=False
   )
   print(f"Verification: {comparison['verification_status']}")

Benchmarking
------------

**What is Benchmarking?**

Benchmarking compares performance and accuracy of different analysis methods,
enabling method selection and performance optimization.

**Key Terminology**:

- **Benchmarking**: Measuring and comparing performance or accuracy of
  different methods or implementations.

- **Performance Benchmark**: Measuring execution time, memory usage, or
  other resource consumption metrics.

- **Accuracy Benchmark**: Comparing results to verify correctness and
  measure accuracy differences.

**Usage**:

.. code-block:: python

   from lfsr.benchmarking import benchmark_period_computation, compare_benchmark_results
   
   results = benchmark_period_computation(
       [1, 0, 0, 1], 2,
       methods=["enumeration", "factorization"]
   )
   
   comparison = compare_benchmark_results(results)
   print(f"Fastest method: {comparison['fastest_method']}")
   print(f"Speedup: {comparison['speedup']}x")

Reproducibility
---------------

**What is Reproducibility?**

Reproducibility features ensure research results can be exactly reproduced
through seed tracking, configuration export, and environment capture.

**Key Terminology**:

- **Reproducibility**: The ability to reproduce research results using
  the same methods, data, and configuration.

- **Reproducibility Seed**: A value used to initialize random number
  generators for deterministic execution.

- **Environment Capture**: Recording system information and software
  versions needed for reproduction.

**Usage**:

.. code-block:: python

   from lfsr.reproducibility import (
       generate_reproducibility_report,
       verify_reproducibility
   )
   
   # Generate report
   report = generate_reproducibility_report(
       analysis_config={'coefficients': [1, 0, 0, 1], 'field_order': 2},
       analysis_results={'period': 6},
       seed=12345
   )
   
   # Verify reproduction
   verification = verify_reproducibility(
       original_results={'period': 6},
       reproduced_results={'period': 6}
   )
   print(f"Verified: {verification['verified']}")

API Reference
-------------

See :doc:`api/theoretical` for complete API documentation.

Command-Line Usage
-----------------

Theoretical analysis features can be accessed through the command line:

.. code-block:: bash

   # Export to LaTeX
   lfsr-seq coefficients.csv 2 --export-latex output.tex
   
   # Generate paper
   lfsr-seq coefficients.csv 2 --generate-paper paper.tex
   
   # Compare with known results
   lfsr-seq coefficients.csv 2 --compare-known

Glossary
--------

**Abstract**
   Brief summary of a research paper (150-250 words).

**Benchmarking**
   Measuring and comparing performance or accuracy of different methods.

**Environment Capture**
   Recording system information and software versions for reproducibility.

**Factor Order**
   Order of an irreducible factor of a polynomial.

**Irreducible Polynomial**
   Polynomial that cannot be factored into polynomials of lower degree.

**Known Result Database**
   Collection of precomputed theoretical results for comparison.

**LaTeX**
   Document preparation system for academic publishing.

**Methodology**
   Section of research paper describing methods and procedures.

**Polynomial Factorization**
   Decomposing a polynomial into irreducible factors.

**Polynomial Order**
   Smallest positive integer n such that t^n ≡ 1 (mod P(t)).

**Reproducibility**
   Ability to reproduce research results using same methods and configuration.

**Reproducibility Seed**
   Value used to initialize random number generators for deterministic execution.

**Research Paper**
   Formal document presenting original research findings.

**Result Verification**
   Comparing computed results with known results to verify correctness.

Further Reading
---------------

- Menezes, A. J., et al. (1996). "Handbook of Applied Cryptography"
- Rueppel, R. A. (1986). "Analysis and Design of Stream Ciphers"
- Golomb, S. W. (1967). "Shift Register Sequences"
