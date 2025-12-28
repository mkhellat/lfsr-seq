#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Known result database for theoretical LFSR analysis.

This module provides a database framework for storing and retrieving known
theoretical results, enabling comparison with computed results.
"""

import json
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import os

from sage.all import *


@dataclass
class KnownPolynomial:
    """
    Known polynomial result entry.
    
    Attributes:
        coefficients: List of polynomial coefficients
        field_order: Field order
        degree: Polynomial degree
        is_primitive: Whether polynomial is primitive
        is_irreducible: Whether polynomial is irreducible
        order: Polynomial order
        period: Maximum period
        source: Source/reference for this result
    """
    coefficients: List[int]
    field_order: int
    degree: int
    is_primitive: bool
    is_irreducible: bool
    order: Optional[int]
    period: Optional[int]
    source: str = "unknown"


class TheoreticalDatabase:
    """
    Database for storing and querying known theoretical results.
    
    This class provides a framework for storing known LFSR results, including
    primitive polynomials, known periods, and theoretical bounds. It enables
    comparison of computed results with known theoretical results.
    
    **Key Terminology**:
    
    - **Known Result Database**: A collection of precomputed or published
      results that can be used for comparison and verification. This includes
      standard primitive polynomials, known period distributions, and
      theoretical bounds.
    
    - **Result Comparison**: Comparing computed analysis results with known
      results from the database to verify correctness or identify patterns.
    
    - **Primitive Polynomial Database**: A collection of known primitive
      polynomials, which are important for LFSR design as they generate
      maximum-period sequences.
    
    **Database Schema**:
    
    The database stores:
    - Polynomial coefficients and properties
    - Field order and degree
    - Primitivity and irreducibility flags
    - Polynomial order and period
    - Source/reference information
    
    Example:
        >>> db = TheoreticalDatabase("results.db")
        >>> db.add_known_polynomial([1, 0, 0, 1], 2, 4, True, True, 15, 15, "standard")
        >>> results = db.query_by_coefficients([1, 0, 0, 1], 2)
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize theoretical database.
        
        Args:
            db_path: Path to SQLite database file (default: in-memory)
        """
        if db_path is None:
            db_path = ":memory:"
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
        self._initialize_standard_polynomials()
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS known_polynomials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coefficients TEXT NOT NULL,
                field_order INTEGER NOT NULL,
                degree INTEGER NOT NULL,
                is_primitive INTEGER NOT NULL,
                is_irreducible INTEGER NOT NULL,
                polynomial_order INTEGER,
                period INTEGER,
                source TEXT,
                UNIQUE(coefficients, field_order)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS known_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                field_order INTEGER NOT NULL,
                degree INTEGER NOT NULL,
                is_primitive INTEGER NOT NULL,
                theoretical_max_period INTEGER NOT NULL,
                observed_max_period INTEGER,
                source TEXT
            )
        """)
        
        self.conn.commit()
    
    def _initialize_standard_polynomials(self):
        """Initialize database with standard primitive polynomials."""
        # Standard primitive polynomials over GF(2)
        standard_primitives = [
            # Degree 2
            ([1, 1], 2, 2, True, True, 3, 3, "standard"),
            # Degree 3
            ([1, 0, 1], 2, 3, True, True, 7, 7, "standard"),
            # Degree 4
            ([1, 0, 0, 1], 2, 4, True, True, 15, 15, "standard"),
            ([1, 1, 0, 1], 2, 4, True, True, 15, 15, "standard"),
            # Degree 5
            ([1, 0, 0, 1, 0], 2, 5, True, True, 31, 31, "standard"),
            ([1, 0, 1, 0, 1], 2, 5, True, True, 31, 31, "standard"),
        ]
        
        for coeffs, field, deg, prim, irr, order, period, source in standard_primitives:
            try:
                self.add_known_polynomial(
                    coeffs, field, deg, prim, irr, order, period, source
                )
            except sqlite3.IntegrityError:
                # Already exists, skip
                pass
    
    def add_known_polynomial(
        self,
        coefficients: List[int],
        field_order: int,
        degree: int,
        is_primitive: bool,
        is_irreducible: bool,
        polynomial_order: Optional[int],
        period: Optional[int],
        source: str = "unknown"
    ) -> None:
        """
        Add a known polynomial result to the database.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            degree: Polynomial degree
            is_primitive: Whether polynomial is primitive
            is_irreducible: Whether polynomial is irreducible
            polynomial_order: Polynomial order
            period: Maximum period
            source: Source/reference
        """
        cursor = self.conn.cursor()
        coeffs_str = json.dumps(coefficients)
        
        cursor.execute("""
            INSERT OR REPLACE INTO known_polynomials
            (coefficients, field_order, degree, is_primitive, is_irreducible,
             polynomial_order, period, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            coeffs_str, field_order, degree,
            1 if is_primitive else 0,
            1 if is_irreducible else 0,
            polynomial_order, period, source
        ))
        
        self.conn.commit()
    
    def query_by_coefficients(
        self,
        coefficients: List[int],
        field_order: int
    ) -> Optional[KnownPolynomial]:
        """
        Query database by polynomial coefficients.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
        
        Returns:
            KnownPolynomial if found, None otherwise
        """
        cursor = self.conn.cursor()
        coeffs_str = json.dumps(coefficients)
        
        cursor.execute("""
            SELECT coefficients, field_order, degree, is_primitive, is_irreducible,
                   polynomial_order, period, source
            FROM known_polynomials
            WHERE coefficients = ? AND field_order = ?
        """, (coeffs_str, field_order))
        
        row = cursor.fetchone()
        if row:
            coeffs = json.loads(row[0])
            return KnownPolynomial(
                coefficients=coeffs,
                field_order=row[1],
                degree=row[2],
                is_primitive=bool(row[3]),
                is_irreducible=bool(row[4]),
                order=row[5],
                period=row[6],
                source=row[7]
            )
        return None
    
    def query_primitive_polynomials(
        self,
        field_order: int,
        degree: Optional[int] = None
    ) -> List[KnownPolynomial]:
        """
        Query all primitive polynomials in the database.
        
        Args:
            field_order: Field order
            degree: Optional degree filter
        
        Returns:
            List of known primitive polynomials
        """
        cursor = self.conn.cursor()
        
        if degree is not None:
            cursor.execute("""
                SELECT coefficients, field_order, degree, is_primitive, is_irreducible,
                       polynomial_order, period, source
                FROM known_polynomials
                WHERE field_order = ? AND degree = ? AND is_primitive = 1
            """, (field_order, degree))
        else:
            cursor.execute("""
                SELECT coefficients, field_order, degree, is_primitive, is_irreducible,
                       polynomial_order, period, source
                FROM known_polynomials
                WHERE field_order = ? AND is_primitive = 1
            """, (field_order,))
        
        results = []
        for row in cursor.fetchall():
            coeffs = json.loads(row[0])
            results.append(KnownPolynomial(
                coefficients=coeffs,
                field_order=row[1],
                degree=row[2],
                is_primitive=bool(row[3]),
                is_irreducible=bool(row[4]),
                order=row[5],
                period=row[6],
                source=row[7]
            ))
        
        return results
    
    def compare_with_known(
        self,
        coefficients: List[int],
        field_order: int,
        computed_order: Optional[int] = None,
        computed_period: Optional[int] = None,
        computed_is_primitive: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Compare computed results with known database results.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            computed_order: Computed polynomial order
            computed_period: Computed maximum period
            computed_is_primitive: Computed primitivity flag
        
        Returns:
            Dictionary with comparison results
        """
        known = self.query_by_coefficients(coefficients, field_order)
        
        if known is None:
            return {
                'found': False,
                'message': 'No known result found in database'
            }
        
        comparison = {
            'found': True,
            'known': asdict(known),
            'matches': {},
            'differences': []
        }
        
        if computed_order is not None and known.order is not None:
            if computed_order == known.order:
                comparison['matches']['order'] = True
            else:
                comparison['matches']['order'] = False
                comparison['differences'].append(
                    f"Order mismatch: computed={computed_order}, known={known.order}"
                )
        
        if computed_period is not None and known.period is not None:
            if computed_period == known.period:
                comparison['matches']['period'] = True
            else:
                comparison['matches']['period'] = False
                comparison['differences'].append(
                    f"Period mismatch: computed={computed_period}, known={known.period}"
                )
        
        if computed_is_primitive is not None:
            if computed_is_primitive == known.is_primitive:
                comparison['matches']['is_primitive'] = True
            else:
                comparison['matches']['is_primitive'] = False
                comparison['differences'].append(
                    f"Primitivity mismatch: computed={computed_is_primitive}, known={known.is_primitive}"
                )
        
        return comparison
    
    def close(self):
        """Close database connection."""
        self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def get_default_database_path() -> str:
    """
    Get default database path.
    
    Returns:
        Path to default database file
    """
    # Use user's home directory or current directory
    db_dir = Path.home() / ".lfsr-seq"
    db_dir.mkdir(exist_ok=True)
    return str(db_dir / "theoretical_results.db")
