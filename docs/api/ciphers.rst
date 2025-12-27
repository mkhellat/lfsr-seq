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

**Example**:

.. code-block:: python

   from lfsr.ciphers.a5_1 import A5_1
   
   cipher = A5_1()
   key = [1] * 64
   iv = [0] * 22
   keystream = cipher.generate_keystream(key, iv, 100)

See Also
--------

* :doc:`../stream_ciphers` for detailed introduction and theory
* :doc:`../mathematical_background` for mathematical foundations
