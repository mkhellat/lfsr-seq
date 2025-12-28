#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Known result database for theoretical comparisons.

This module provides a database framework for storing and retrieving known
theoretical results, enabling comparison with computed analysis results.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from sage.all import *


class KnownResultDatabase:
    """
    Database for storing and querying known theoretical results.
    
    This class provides functionality to store known results (primitive polynomials,
    period distributions, polynomial orders) and compare computed results against them.
    
    **Key Terminology**:
    
    - **Known Result Database**: A collection of previously computed or published
      theoretical results that can be used for verification and comparison.
    
    - **Result Verification**: Comparing computed results with known results to
      verify correctness of analysis algorithms.
    
    - **Theoretical Comparison**: Comparing experimental results with theoretical
      predictions or known published results.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize known result database.
        
        Args:
            db_path: Optional path to database file (default: data/theoretical_db.json)
        """
        if db_path is None:
            # Default to data directory
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "theoretical_db.json")
        
        self.db_path = db_path
        self.db: Dict[str, Any] = {}
        self._load_database()
    
    def _load_database(self) -> None:
        """Load database from file."""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.db = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.db = self._initialize_database()
        else:
            self.db = self._initialize_database()
            self._save_database()
    
    def _save_database(self) -> None:
        """Save database to file."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, indent=2, ensure_ascii=False)
    
    def _initialize_database(self) -> Dict[str, Any]:
        """Initialize database with standard known results."""
        return {
            'primitive_polynomials': {},
            'polynomial_orders': {},
            'period_distributions': {},
            'known_results': []
        }
    
    def add_primitive_polynomial(
        self,
        coefficients: List[int],
        field_order: int,
        degree: int,
        order: int,
        source: Optional[str] = None
    ) -> None:
        """
        Add a known primitive polynomial to the database.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            degree: Polynomial degree
            order: Polynomial order (should be q^d - 1)
            source: Optional source/reference
        """
        key = f"{field_order}_{degree}_{'_'.join(map(str, coefficients))}"
        self.db['primitive_polynomials'][key] = {
            'coefficients': coefficients,
            'field_order': field_order,
            'degree': degree,
            'order': order,
            'source': source
        }
        self._save_database()
    
    def lookup_primitive_polynomial(
        self,
        coefficients: List[int],
        field_order: int,
        degree: int
    ) -> Optional[Dict[str, Any]]:
        """
        Look up a primitive polynomial in the database.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            degree: Polynomial degree
        
        Returns:
            Dictionary with polynomial data if found, None otherwise
        """
        key = f"{field_order}_{degree}_{'_'.join(map(str, coefficients))}"
        return self.db['primitive_polynomials'].get(key)
    
    def add_polynomial_order(
        self,
        coefficients: List[int],
        field_order: int,
        degree: int,
        order: int,
        source: Optional[str] = None
    ) -> None:
        """
        Add a known polynomial order to the database.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            degree: Polynomial degree
            order: Polynomial order
            source: Optional source/reference
        """
        key = f"{field_order}_{degree}_{'_'.join(map(str, coefficients))}"
        self.db['polynomial_orders'][key] = {
            'coefficients': coefficients,
            'field_order': field_order,
            'degree': degree,
            'order': order,
            'source': source
        }
        self._save_database()
    
    def lookup_polynomial_order(
        self,
        coefficients: List[int],
        field_order: int,
        degree: int
    ) -> Optional[Dict[str, Any]]:
        """
        Look up a polynomial order in the database.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            degree: Polynomial degree
        
        Returns:
            Dictionary with order data if found, None otherwise
        """
        key = f"{field_order}_{degree}_{'_'.join(map(str, coefficients))}"
        return self.db['polynomial_orders'].get(key)
    
    def compare_with_known(
        self,
        coefficients: List[int],
        field_order: int,
        degree: int,
        computed_order: Optional[int] = None,
        computed_is_primitive: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Compare computed results with known results in database.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            degree: Polynomial degree
            computed_order: Computed polynomial order
            computed_is_primitive: Computed primitivity status
        
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            'found_in_database': False,
            'matches': False,
            'known_order': None,
            'known_is_primitive': None,
            'computed_order': computed_order,
            'computed_is_primitive': computed_is_primitive,
            'order_match': None,
            'primitive_match': None
        }
        
        # Check primitive polynomials
        primitive_result = self.lookup_primitive_polynomial(coefficients, field_order, degree)
        if primitive_result:
            comparison['found_in_database'] = True
            comparison['known_is_primitive'] = True
            comparison['known_order'] = primitive_result['order']
            
            if computed_is_primitive is not None:
                comparison['primitive_match'] = computed_is_primitive == True
                comparison['matches'] = comparison['primitive_match']
            
            if computed_order is not None:
                comparison['order_match'] = computed_order == primitive_result['order']
                if comparison['matches'] is False:
                    comparison['matches'] = comparison['order_match']
        
        # Check polynomial orders
        if not comparison['found_in_database']:
            order_result = self.lookup_polynomial_order(coefficients, field_order, degree)
            if order_result:
                comparison['found_in_database'] = True
                comparison['known_order'] = order_result['order']
                comparison['known_is_primitive'] = False
                
                if computed_order is not None:
                    comparison['order_match'] = computed_order == order_result['order']
                    comparison['matches'] = comparison['order_match']
        
        return comparison
    
    def populate_standard_primitives(self) -> None:
        """Populate database with standard primitive polynomials."""
        # Some well-known primitive polynomials over GF(2)
        standard_primitives = [
            # Degree 2
            ([1, 1], 2, 2, 3),  # t^2 + t + 1
            # Degree 3
            ([1, 0, 1], 2, 3, 7),  # t^3 + t + 1
            # Degree 4
            ([1, 0, 0, 1], 2, 4, 15),  # t^4 + t + 1
            # Degree 5
            ([1, 0, 0, 1, 0], 2, 5, 31),  # t^5 + t^2 + 1
        ]
        
        for coeffs, field_order, degree, order in standard_primitives:
            self.add_primitive_polynomial(
                coeffs, field_order, degree, order,
                source="Standard primitive polynomial"
            )


# Global database instance
_global_db: Optional[KnownResultDatabase] = None


def get_database(db_path: Optional[str] = None) -> KnownResultDatabase:
    """
    Get global database instance.
    
    Args:
        db_path: Optional database path
    
    Returns:
        KnownResultDatabase instance
    """
    global _global_db
    if _global_db is None:
        _global_db = KnownResultDatabase(db_path)
        # Populate with standard primitives if empty
        if not _global_db.db['primitive_polynomials']:
            _global_db.populate_standard_primitives()
    return _global_db
