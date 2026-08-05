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
   mathematical_background
   nist_sp800_22
   visualization
   correlation_attacks
   algebraic_attacks
   time_memory_tradeoff
   stream_ciphers
   advanced_lfsr_structures
   theoretical_analysis
   ml_integration
   parallelization
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

Comparison to Other Tools
-------------------------

Several existing LFSR-related tools and libraries were reviewed for
comparison (based on their public documentation — this is a
documentation-level comparison, not independent benchmarking of every
listed tool). None combine the same breadth as ``lfsr-seq``: full
state-space enumeration over general :math:`GF(q)`,
characteristic-polynomial/primitivity analysis, an integrated
correlation + algebraic + time-memory trade-off attack framework, real
stream cipher implementations, the NIST SP 800-22 statistical test
suite, ML-based period prediction, visualization, and a CLI, in one
tool.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Tool
     - Scope
   * - `dcode.fr LFSR Calculator <https://www.dcode.fr/linear-feedback-shift-register>`_
     - Online, educational. Generates bits and finds the period for a
       single sequence (Fibonacci/Galois mode). No characteristic
       polynomial, no fields other than :math:`GF(2)`, no cryptanalysis.
   * - `PyLFSR <https://pylfsr.github.io/>`_
     - Python library. Generates known cipher configurations (A5/1,
       Geffe generator) and basic period/visualization for
       :math:`GF(2)`. No characteristic polynomial computation, no
       primitivity testing, no attack framework.
   * - `lfsr-tools <https://pypi.org/project/lfsr-tools/>`_ (PyPI)
     - Python library providing an ``LFSR`` sequence generator class
       and a ``BerlekampMassey`` connection-polynomial recovery class.
       No state-space enumeration, field-order generality, or attacks
       beyond Berlekamp-Massey.
   * - `SageMath sage.crypto.lfsr <https://doc.sagemath.org/html/en/reference/cryptography/sage/crypto/lfsr.html>`_
     - Three primitive functions (``lfsr_sequence``,
       ``lfsr_autocorrelation``, ``lfsr_connection_polynomial``) — this
       is math-library plumbing that ``lfsr-seq`` itself builds on (see
       :doc:`installation`), not a competing end-user tool.
   * - `galois <https://github.com/mhostetter/galois>`_
     - General-purpose NumPy-based finite-field arithmetic library
       (Galois field arrays, Reed-Solomon/BCH codes, ``FLFSR``/``GLFSR``
       classes). LFSR support is one minor utility among many unrelated
       features; no cycle enumeration, cryptanalysis, or cipher
       simulations.
   * - Single-technique research scripts (e.g. `M0RC/lfsr-correlation-attack <https://github.com/M0RC/lfsr-correlation-attack>`_)
     - Standalone implementations of one attack technique in isolation,
       not part of an integrated analysis suite.

Additional Resources
--------------------

* `SageMath Documentation <https://doc.sagemath.org/>`_
* `Tanja Lange's Cryptology Course <https://www.hyperelliptic.org/tanja/teaching/CS22/>`_

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

