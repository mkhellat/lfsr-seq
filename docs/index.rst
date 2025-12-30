LFSR-Seq Documentation
======================

**Linear Feedback Shift Register (LFSR) Sequence Analysis Tool**

A comprehensive, production-ready tool for analyzing Linear Feedback Shift Register sequences,
computing periods, determining characteristic polynomials, and performing advanced cryptanalysis
over finite fields.

Welcome to the lfsr-seq documentation! This tool provides:

* **Complete LFSR Analysis**: Analyze all possible state sequences and compute periods
* **Characteristic Polynomials**: Determine characteristic polynomials and their orders
* **Matrix Operations**: Compute state update matrices and their orders
* **Polynomial Factorization**: Factor characteristic polynomials and analyze factor orders
* **Berlekamp-Massey Algorithm**: Synthesize LFSRs from sequences
* **Linear Complexity**: Calculate linear complexity and complexity profiles
* **Statistical Analysis**: Frequency tests, runs tests, autocorrelation, periodicity detection
* **Multi-format Export**: Export results in JSON, CSV, XML, or plain text
* **Python API**: Use as a library for programmatic analysis
* **Field Support**: Full support for GF(p) and GF(pⁿ) extension fields
* **Security Hardened**: Path traversal protection, file size limits, input sanitization

Getting Started
---------------

New to lfsr-seq? Start here:

* :doc:`installation` - Installation instructions and requirements
* :doc:`user_guide` - Quick start guide and basic usage
* :doc:`examples` - Code examples and tutorials

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: User Documentation:

   installation
   user_guide
   examples
   parallelization
   mathematical_background
   correlation_attacks
   algebraic_attacks
   time_memory_tradeoff
   stream_ciphers
   advanced_lfsr_structures
   theoretical_analysis
   ml_integration
   visualization
   nist_sp800_22
   optimization_techniques

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api/index

Documentation Building
-----------------------

The documentation can be built in multiple formats:

* **HTML** (recommended): ``make docs``
* **PDF**: ``make docs-pdf`` (requires LaTeX)
* **Live Server**: ``make docs-live`` (auto-reload on changes)

See :doc:`installation` for all available Make targets.

Additional Resources
--------------------

* `SageMath Documentation <https://doc.sagemath.org/>`_
* `Tanja Lange's Cryptology Course <https://www.hyperelliptic.org/tanja/teaching/CS22/>`_

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

