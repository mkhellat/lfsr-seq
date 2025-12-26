#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for LFSR statistics functions, including period distribution.
"""

import pytest

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.statistics import compute_period_distribution


class TestPeriodDistribution:
    """Tests for compute_period_distribution function."""

    def test_period_distribution_basic(self):
        """Test basic period distribution computation."""
        period_dict = {1: 15, 2: 15, 3: 15}
        stats = compute_period_distribution(period_dict, 2, 4, False)
        
        assert "error" not in stats
        assert stats["total_sequences"] == 3
        assert stats["min_period"] == 15
        assert stats["max_period"] == 15
        assert stats["mean_period"] == 15.0
        assert stats["median_period"] == 15.0

    def test_period_distribution_primitive(self):
        """Test period distribution for primitive polynomial."""
        # For primitive polynomial, all non-zero states should have max period
        period_dict = {1: 15, 2: 15, 3: 15}
        stats = compute_period_distribution(period_dict, 2, 4, True)
        
        assert stats["comparison"]["max_period_equals_theoretical"] is True
        assert stats["comparison"]["max_period_ratio"] == 1.0
        assert stats["theoretical_bounds"]["max_theoretical_period"] == 15
        assert stats["theoretical_bounds"]["is_primitive"] is True

    def test_period_distribution_variance(self):
        """Test period distribution with varying periods."""
        period_dict = {1: 1, 2: 3, 3: 5, 4: 7, 5: 15}
        stats = compute_period_distribution(period_dict, 2, 4, False)
        
        assert stats["total_sequences"] == 5
        assert stats["min_period"] == 1
        assert stats["max_period"] == 15
        assert stats["mean_period"] == 6.2  # (1+3+5+7+15)/5
        assert stats["variance"] > 0
        assert stats["std_deviation"] > 0

    def test_period_distribution_frequency(self):
        """Test period frequency histogram."""
        period_dict = {1: 15, 2: 15, 3: 3, 4: 3, 5: 1}
        stats = compute_period_distribution(period_dict, 2, 4, False)
        
        freq = stats["period_frequency"]
        assert freq[15] == 2
        assert freq[3] == 2
        assert freq[1] == 1
        assert stats["distribution_info"]["unique_periods"] == 3

    def test_period_distribution_empty(self):
        """Test period distribution with empty dictionary."""
        stats = compute_period_distribution({}, 2, 4, False)
        assert "error" in stats

    def test_period_distribution_theoretical_bounds(self):
        """Test theoretical bounds computation."""
        period_dict = {1: 7, 2: 7, 3: 1}
        stats = compute_period_distribution(period_dict, 2, 3, False)
        
        theo = stats["theoretical_bounds"]
        assert theo["max_theoretical_period"] == 7  # 2^3 - 1
        assert theo["state_space_size"] == 8  # 2^3
        assert theo["is_primitive"] is False

    def test_period_distribution_comparison(self):
        """Test comparison with theoretical bounds."""
        period_dict = {1: 15, 2: 15}
        stats = compute_period_distribution(period_dict, 2, 4, False)
        
        comp = stats["comparison"]
        assert "max_period_equals_theoretical" in comp
        assert "max_period_ratio" in comp
        assert comp["max_period_ratio"] <= 1.0

    def test_period_distribution_primitive_validation(self):
        """Test primitive polynomial validation in distribution."""
        # For primitive polynomial, all periods should be maximum
        period_dict = {1: 15, 2: 15, 3: 15, 4: 15}
        stats = compute_period_distribution(period_dict, 2, 4, True)
        
        assert stats["comparison"].get("all_periods_maximum", False) is True
        assert stats["comparison"].get("expected_period") == 15
