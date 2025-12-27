Stream Cipher Analysis API
===========================

The stream cipher analysis module provides analysis capabilities for real-world
stream ciphers that use LFSRs.

.. automodule:: lfsr.ciphers
   :members:
   :undoc-members:
   :show-inheritance:

Base Classes
------------

StreamCipher
~~~~~~~~~~~~

.. autoclass:: lfsr.ciphers.base.StreamCipher
   :members:
   :no-index:

Abstract base class for stream cipher analysis.

**Key Methods**:
- `generate_keystream()`: Generate keystream from key and IV
- `analyze_structure()`: Analyze cipher structure
- `get_config()`: Get cipher configuration
- `apply_attacks()`: Apply cryptanalytic attacks
- `analyze()`: Perform comprehensive analysis

CipherConfig
~~~~~~~~~~~~

.. autoclass:: lfsr.ciphers.base.CipherConfig
   :members:
   :no-index:

Configuration for a stream cipher.

CipherStructure
~~~~~~~~~~~~~~~

.. autoclass:: lfsr.ciphers.base.CipherStructure
   :members:
   :no-index:

Structure information for a stream cipher.

CipherAnalysisResult
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.ciphers.base.CipherAnalysisResult
   :members:
   :no-index:

Results from stream cipher analysis.

Cipher Implementations
----------------------

A5/1
~~~~

.. autoclass:: lfsr.ciphers.a5_1.A5_1
   :members:
   :no-index:

A5/1 GSM stream cipher implementation.

A5/2
~~~~

.. autoclass:: lfsr.ciphers.a5_2.A5_2
   :members:
   :no-index:

A5/2 GSM stream cipher implementation (weaker variant).

E0
~~

.. autoclass:: lfsr.ciphers.e0.E0
   :members:
   :no-index:

E0 Bluetooth stream cipher implementation.

Trivium
~~~~~~~

.. autoclass:: lfsr.ciphers.trivium.Trivium
   :members:
   :no-index:

Trivium eSTREAM finalist stream cipher implementation.

Grain Family
~~~~~~~~~~~

.. autoclass:: lfsr.ciphers.grain.Grain128
   :members:
   :no-index:

Grain-128 eSTREAM finalist stream cipher implementation.

.. autoclass:: lfsr.ciphers.grain.Grain128a
   :members:
   :no-index:

Grain-128a eSTREAM finalist with authenticated encryption.

LILI-128
~~~~~~~~

.. autoclass:: lfsr.ciphers.lili128.LILI128
   :members:
   :no-index:

LILI-128 academic stream cipher design.

Comparison Framework
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: lfsr.ciphers.comparison.CipherComparison
   :members:
   :no-index:

Comparison results for multiple ciphers.

.. autofunction:: lfsr.ciphers.comparison.compare_ciphers
   :no-index:

Compare multiple stream ciphers side-by-side.

.. autofunction:: lfsr.ciphers.comparison.generate_comparison_report
   :no-index:

Generate human-readable comparison report.

**Example**:

.. code-block:: python

   from lfsr.ciphers import A5_1, E0, Trivium
   from lfsr.ciphers.comparison import compare_ciphers, generate_comparison_report
   
   # Compare ciphers
   comparison = compare_ciphers([A5_1(), E0(), Trivium()])
   
   # Generate report
   report = generate_comparison_report(comparison)
   print(report)

See Also
--------

* :doc:`../stream_ciphers` for detailed introduction and theory
* :doc:`../mathematical_background` for mathematical foundations
