#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.optimization (ResultCache and global-cache helpers).

This module does NOT depend on SageMath -- it's a plain hashlib/json/os
caching utility with no lfsr-domain math in it (despite living in a module
named "optimization", it does not compute or select TMTO parameters or any
other analysis parameters; that logic lives entirely in lfsr.tmto's own
optimize_tmto_parameters(), which is already covered in test_tmto.py). So
these tests verify cache-key generation, hit/miss/stat bookkeeping, and
persistent (file-based) round-tripping -- not any numerical optimization.
"""

import hashlib
import json
import os

import pytest

from lfsr.optimization import (
    ResultCache,
    clear_global_cache,
    get_global_cache,
    set_global_cache,
)


class TestGenerateKey:
    """Tests for ResultCache.generate_key()."""

    def test_key_is_sha256_hexdigest(self):
        """generate_key() should be exactly the sha256 hexdigest of the
        sort_keys=True JSON dump of the normalized config -- verify this
        independently rather than trusting "it returns a hex string"."""
        cache = ResultCache()
        key = cache.generate_key([1, 0, 0, 1], 2, "period")

        expected_str = json.dumps(
            {
                "coefficients": [1, 0, 0, 1],
                "field_order": 2,
                "analysis_type": "period",
            },
            sort_keys=True,
        )
        expected_key = hashlib.sha256(expected_str.encode("utf-8")).hexdigest()

        assert key == expected_key
        assert len(key) == 64  # sha256 hex length
        int(key, 16)  # must be valid hex

    def test_key_default_analysis_type_is_period(self):
        cache = ResultCache()
        key_default = cache.generate_key([1, 1], 2)
        key_explicit = cache.generate_key([1, 1], 2, analysis_type="period")
        assert key_default == key_explicit

    def test_key_strips_trailing_zero_coefficients(self):
        """Trailing zeros are stripped for normalization (leading/interior
        zeros are NOT stripped -- only the specific trailing-zero-pop loop)."""
        cache = ResultCache()
        key_a = cache.generate_key([1, 0, 1, 0, 0], 2)
        key_b = cache.generate_key([1, 0, 1], 2)
        assert key_a == key_b

    def test_key_does_not_strip_leading_or_interior_zeros(self):
        cache = ResultCache()
        key_a = cache.generate_key([0, 1, 1], 2)
        key_b = cache.generate_key([1, 1], 2)
        assert key_a != key_b

    def test_key_all_zero_coefficients_normalizes_to_empty(self):
        cache = ResultCache()
        key_a = cache.generate_key([0, 0, 0], 2)
        key_b = cache.generate_key([], 2)
        assert key_a == key_b

    def test_key_does_not_mutate_input_list(self):
        """generate_key() copies coefficients before popping trailing
        zeros; the caller's original list must be untouched."""
        cache = ResultCache()
        coeffs = [1, 0, 0]
        cache.generate_key(coeffs, 2)
        assert coeffs == [1, 0, 0]

    def test_different_field_order_gives_different_key(self):
        cache = ResultCache()
        key_a = cache.generate_key([1, 0, 1], 2)
        key_b = cache.generate_key([1, 0, 1], 3)
        assert key_a != key_b

    def test_different_analysis_type_gives_different_key(self):
        cache = ResultCache()
        key_a = cache.generate_key([1, 0, 1], 2, "period")
        key_b = cache.generate_key([1, 0, 1], 2, "polynomial")
        assert key_a != key_b

    def test_key_is_deterministic(self):
        cache = ResultCache()
        key_a = cache.generate_key([1, 1, 0, 1], 5, "polynomial")
        key_b = cache.generate_key([1, 1, 0, 1], 5, "polynomial")
        assert key_a == key_b


class TestInMemoryCacheBehavior:
    """Tests for get/set/contains/len/clear on the in-memory layer."""

    def test_get_miss_returns_none_and_increments_misses(self):
        cache = ResultCache()
        key = cache.generate_key([1, 0, 1], 2)
        result = cache.get(key)
        assert result is None
        assert cache.get_stats()["misses"] == 1
        assert cache.get_stats()["hits"] == 0

    def test_set_then_get_is_a_hit(self):
        cache = ResultCache()
        key = cache.generate_key([1, 0, 1], 2)
        cache.set(key, {"period": 7})

        result = cache.get(key)
        assert result == {"period": 7}
        assert cache.get_stats()["hits"] == 1
        assert cache.get_stats()["sets"] == 1

    def test_contains_operator(self):
        cache = ResultCache()
        key = cache.generate_key([1, 0, 1], 2)
        assert key not in cache
        cache.set(key, 42)
        assert key in cache

    def test_len_operator(self):
        cache = ResultCache()
        assert len(cache) == 0
        cache.set("a", 1)
        cache.set("b", 2)
        assert len(cache) == 2
        # overwriting an existing key must not grow the length
        cache.set("a", 99)
        assert len(cache) == 2

    def test_set_overwrites_existing_value(self):
        cache = ResultCache()
        cache.set("k", "first")
        cache.set("k", "second")
        assert cache.get("k") == "second"

    def test_clear_empties_cache_and_resets_stats(self):
        cache = ResultCache()
        cache.set("k", "v")
        cache.get("k")
        cache.get("missing")
        assert len(cache) == 1

        cache.clear()

        assert len(cache) == 0
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["sets"] == 0
        assert stats["loads"] == 0

    def test_get_stats_hit_rate_computation(self):
        cache = ResultCache()
        cache.set("k", "v")
        cache.get("k")  # hit
        cache.get("k")  # hit
        cache.get("missing")  # miss

        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["hit_rate"] == pytest.approx(2 / 3)

    def test_get_stats_hit_rate_zero_requests(self):
        """No get() calls at all -> hit_rate should be 0.0, not a
        division-by-zero crash."""
        cache = ResultCache()
        stats = cache.get_stats()
        assert stats["hit_rate"] == 0.0

    def test_get_stats_returns_a_copy_not_live_reference(self):
        """get_stats() returns stats.copy(); mutating the returned dict
        must not affect the cache's internal counters."""
        cache = ResultCache()
        stats = cache.get_stats()
        stats["hits"] = 9999
        assert cache.get_stats()["hits"] == 0


class TestPersistentCache:
    """Tests for file-backed (persistent) caching."""

    def test_cache_file_created_and_populated_on_set(self, tmp_path):
        cache_file = tmp_path / "cache.json"
        cache = ResultCache(cache_file=str(cache_file))
        cache.set("k1", {"period": 15})

        assert cache_file.exists()
        with open(cache_file) as f:
            on_disk = json.load(f)
        assert on_disk == {"k1": {"period": 15}}

    def test_cache_file_directory_is_created_if_missing(self, tmp_path):
        nested = tmp_path / "nested" / "dirs" / "cache.json"
        cache = ResultCache(cache_file=str(nested))
        cache.set("k", "v")
        assert nested.exists()

    def test_tilde_expansion_in_cache_file_path(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        cache = ResultCache(cache_file="~/subdir/cache.json")
        assert cache.cache_file == str(tmp_path / "subdir" / "cache.json")

    def test_reloading_persistent_cache_from_disk(self, tmp_path):
        """A fresh ResultCache pointed at an existing cache file should
        load its contents into in_memory_cache and record 'loads'."""
        cache_file = tmp_path / "cache.json"
        cache_a = ResultCache(cache_file=str(cache_file))
        cache_a.set("k1", "v1")
        cache_a.set("k2", "v2")

        cache_b = ResultCache(cache_file=str(cache_file))
        assert cache_b.get("k1") == "v1"
        assert cache_b.get("k2") == "v2"
        assert cache_b.get_stats()["loads"] == 2

    def test_corrupted_cache_file_starts_fresh_instead_of_raising(self, tmp_path):
        cache_file = tmp_path / "cache.json"
        cache_file.write_text("{not valid json!!")

        cache = ResultCache(cache_file=str(cache_file))
        assert len(cache) == 0
        # Cache remains usable after a corrupt-file recovery.
        cache.set("k", "v")
        assert cache.get("k") == "v"

    def test_clear_removes_cache_file_from_disk(self, tmp_path):
        cache_file = tmp_path / "cache.json"
        cache = ResultCache(cache_file=str(cache_file))
        cache.set("k", "v")
        assert cache_file.exists()

        cache.clear()
        assert not cache_file.exists()

    def test_clear_with_no_existing_file_does_not_raise(self, tmp_path):
        cache_file = tmp_path / "does_not_exist.json"
        cache = ResultCache(cache_file=str(cache_file))
        cache.clear()  # should not raise even though file was never created

    def test_no_cache_file_means_purely_in_memory(self):
        cache = ResultCache(cache_file=None)
        cache.set("k", "v")
        assert cache.cache_file is None
        assert cache.get("k") == "v"

    def test_set_write_failure_is_swallowed_and_in_memory_still_works(self, tmp_path):
        """If writing the persistent cache fails (e.g. path became a
        directory), set() should not raise -- in-memory caching still
        succeeds per the module's documented 'continue with in-memory
        cache only' behavior."""
        cache_file = tmp_path / "cache.json"
        cache_file.mkdir()  # make the path a directory so open(..., 'w') fails

        cache = ResultCache(cache_file=str(cache_file))
        cache.set("k", "v")  # should not raise
        assert cache.get("k") == "v"


class TestGlobalCache:
    """Tests for get_global_cache/set_global_cache/clear_global_cache."""

    def setup_method(self):
        # Reset global cache state before each test so tests don't leak
        # into each other via the module-level singleton.
        set_global_cache(None)

    def teardown_method(self):
        set_global_cache(None)

    def test_get_global_cache_creates_singleton(self):
        cache_a = get_global_cache()
        cache_b = get_global_cache()
        assert cache_a is cache_b

    def test_get_global_cache_default_location(self):
        cache = get_global_cache()
        assert cache.cache_file == os.path.expanduser("~/.lfsr-seq/cache.json")

    def test_set_global_cache_replaces_singleton(self):
        custom = ResultCache(cache_file=None)
        set_global_cache(custom)
        assert get_global_cache() is custom

    def test_clear_global_cache_clears_the_active_global(self):
        custom = ResultCache(cache_file=None)
        custom.set("k", "v")
        set_global_cache(custom)

        clear_global_cache()

        assert len(custom) == 0

    def test_clear_global_cache_noop_when_unset(self):
        """clear_global_cache() must not raise/create a cache as a side
        effect when no global cache has been created yet."""
        clear_global_cache()  # should not raise
