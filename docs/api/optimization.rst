Optimization Module
===================

The optimization module provides caching and optimization utilities to improve
performance for repeated analyses and structured problems.

.. automodule:: lfsr.optimization
   :members:
   :undoc-members:
   :show-inheritance:

Classes
-------

ResultCache
~~~~~~~~~~~

.. autoclass:: lfsr.optimization.ResultCache
   :members:
   :no-index:

Cache for LFSR analysis results with both in-memory and persistent storage.

**Key Terminology**:

- **Cache**: Storage mechanism for computed results to avoid redundant calculations
- **Cache Key**: Unique identifier for a computation (hash of LFSR configuration)
- **Cache Hit**: When requested result is found in cache
- **Cache Miss**: When requested result is not in cache
- **Persistent Cache**: Cache that survives between program runs (file-based)
- **In-Memory Cache**: Fast RAM-based cache for current session

**Example**:

.. code-block:: python

   from lfsr.optimization import ResultCache
   
   # Create cache with persistent storage
   cache = ResultCache(cache_file="~/.lfsr-seq/cache.json")
   
   # Generate cache key
   key = cache.generate_key([1, 0, 0, 1], 2, "period")
   
   # Check cache
   if key in cache:
       period = cache.get(key)
   else:
       period = compute_period([1, 0, 0, 1], 2)
       cache.set(key, period)
   
   # Get cache statistics
   stats = cache.get_stats()
   print(f"Hit rate: {stats['hit_rate']:.2%}")

Functions
---------

get_global_cache
~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.optimization.get_global_cache
   :no-index:

Get or create global cache instance.

set_global_cache
~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.optimization.set_global_cache
   :no-index:

Set global cache instance.

clear_global_cache
~~~~~~~~~~~~~~~~~~

.. autofunction:: lfsr.optimization.clear_global_cache
   :no-index:

Clear the global cache.

Important Notes
---------------

**Cache Key Generation**: Keys are generated using SHA-256 hash of normalized
LFSR configuration (coefficients, field order, analysis type). Identical
configurations produce identical keys.

**Persistent Storage**: Cache is stored as JSON file. Default location is
``~/.lfsr-seq/cache.json``. The directory is created automatically if it
doesn't exist.

**Cache Invalidation**: If algorithms change or bugs are fixed, clear the cache
to ensure correct results. Use ``cache.clear()`` or delete the cache file.

**Performance**: Cache lookups are O(1) (constant time) using dictionary
lookup. Cache writes are O(1) for in-memory cache, O(n) for persistent cache
where n is cache size.

See Also
--------

* :doc:`../optimization_techniques` for detailed introduction and theory
* :doc:`polynomial` for period computation via factorization
* :doc:`../mathematical_background` for mathematical foundations
