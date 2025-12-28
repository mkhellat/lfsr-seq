#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Known result database for theoretical LFSR analysis.

This module provides a database framework for storing and retrieving known
theoretical results, enabling comparison with computed results.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib

from sage.all import *


@dataclass
class KnownResult:
    """
    Known theoretical result entry.
    
    This class represents a known result that can be stored in the database
    for comparison with computed results.
    
    Attributes:
        polynomial_str: String representation of polynomial
        field_order: Field order (q)
        degree: Polynomial degree
        order: Polynomial order
        is_primitive: Whether polynomial is primitive
        is_irreducible: Whether polynomial is irreducible
        max_period: Maximum period
        source: Source of the result (paper, database, etc.)
        notes: Additional notes
    """
    polynomial_str: str
    field_order: int
    degree: int
    order: Optional[int] = None
    is_primitive: bool = False
    is_irreducible: bool = False
    max_period: Optional[int] = None
    source: str = "unknown"
    notes: str = ""


class TheoreticalDatabase:
    """
    Database for storing and querying known theoretical results.
    
    This class provides a framework for storing known LFSR analysis results,
    enabling comparison with computed results and verification of correctness.
    
    **Key Terminology**:
    
    - **Known Result Database**: A collection of previously computed or
      published theoretical results that can be used for comparison and
      verification. This helps validate analysis correctness and provides
      reference data.
    
    - **Result Verification**: Comparing computed results with known results
      to verify correctness. If computed results match known results, this
      increases confidence in the analysis.
    
    - **Reference Data**: Published or well-established results that serve
      as ground truth for comparison. These may come from research papers,
      textbooks, or standard databases.
    
    **Database Schema**:
    
    The database stores:
    - Polynomial representations
    - Field order and degree
    - Polynomial order
    - Primitivity and irreducibility
    - Maximum period
    - Source information
    - Additional notes
    
    **Usage**:
    
        >>> db = TheoreticalDatabase("results.db")
        >>> result = KnownResult("t^4+t+1", 2, 4, order=15, is_primitive=True)
        >>> db.add_result(result)
        >>> matches = db.find_matching_results("t^4+t+1", 2)
    """
    
    def __init__(self, db_path: str = "theoretical_results.db"):
        """
        Initialize theoretical results database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS known_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                polynomial_str TEXT NOT NULL,
                polynomial_hash TEXT NOT NULL,
                field_order INTEGER NOT NULL,
                degree INTEGER NOT NULL,
                order_value INTEGER,
                is_primitive INTEGER NOT NULL DEFAULT 0,
                is_irreducible INTEGER NOT NULL DEFAULT 0,
                max_period INTEGER,
                source TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(polynomial_hash, field_order)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_polynomial_hash 
            ON known_results(polynomial_hash, field_order)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_field_degree 
            ON known_results(field_order, degree)
        """)
        
        conn.commit()
        conn.close()
    
    def _polynomial_hash(self, polynomial_str: str, field_order: int) -> str:
        """Compute hash for polynomial."""
        combined = f"{polynomial_str}:{field_order}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def add_result(self, result: KnownResult) -> bool:
        """
        Add a known result to the database.
        
        Args:
            result: KnownResult to add
        
        Returns:
            True if added successfully, False if already exists
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        poly_hash = self._polynomial_hash(result.polynomial_str, result.field_order)
        
        try:
            cursor.execute("""
                INSERT INTO known_results 
                (polynomial_str, polynomial_hash, field_order, degree, 
                 order_value, is_primitive, is_irreducible, max_period, 
                 source, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.polynomial_str,
                poly_hash,
                result.field_order,
                result.degree,
                result.order,
                1 if result.is_primitive else 0,
                1 if result.is_irreducible else 0,
                result.max_period,
                result.source,
                result.notes
            ))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Already exists
            conn.close()
            return False
    
    def find_matching_results(
        self,
        polynomial_str: str,
        field_order: int
    ) -> List[KnownResult]:
        """
        Find known results matching a polynomial.
        
        Args:
            polynomial_str: String representation of polynomial
            field_order: Field order
        
        Returns:
            List of matching KnownResult objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        poly_hash = self._polynomial_hash(polynomial_str, field_order)
        
        cursor.execute("""
            SELECT polynomial_str, field_order, degree, order_value,
                   is_primitive, is_irreducible, max_period, source, notes
            FROM known_results
            WHERE polynomial_hash = ? AND field_order = ?
        """, (poly_hash, field_order))
        
        results = []
        for row in cursor.fetchall():
            result = KnownResult(
                polynomial_str=row[0],
                field_order=row[1],
                degree=row[2],
                order=row[3],
                is_primitive=bool(row[4]),
                is_irreducible=bool(row[5]),
                max_period=row[6],
                source=row[7] or "unknown",
                notes=row[8] or ""
            )
            results.append(result)
        
        conn.close()
        return results
    
    def find_by_properties(
        self,
        field_order: Optional[int] = None,
        degree: Optional[int] = None,
        is_primitive: Optional[bool] = None,
        is_irreducible: Optional[bool] = None
    ) -> List[KnownResult]:
        """
        Find results by properties.
        
        Args:
            field_order: Filter by field order
            degree: Filter by degree
            is_primitive: Filter by primitivity
            is_irreducible: Filter by irreducibility
        
        Returns:
            List of matching KnownResult objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        conditions = []
        params = []
        
        if field_order is not None:
            conditions.append("field_order = ?")
            params.append(field_order)
        
        if degree is not None:
            conditions.append("degree = ?")
            params.append(degree)
        
        if is_primitive is not None:
            conditions.append("is_primitive = ?")
            params.append(1 if is_primitive else 0)
        
        if is_irreducible is not None:
            conditions.append("is_irreducible = ?")
            params.append(1 if is_irreducible else 0)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        cursor.execute(f"""
            SELECT polynomial_str, field_order, degree, order_value,
                   is_primitive, is_irreducible, max_period, source, notes
            FROM known_results
            WHERE {where_clause}
        """, params)
        
        results = []
        for row in cursor.fetchall():
            result = KnownResult(
                polynomial_str=row[0],
                field_order=row[1],
                degree=row[2],
                order=row[3],
                is_primitive=bool(row[4]),
                is_irreducible=bool(row[5]),
                max_period=row[6],
                source=row[7] or "unknown",
                notes=row[8] or ""
            )
            results.append(result)
        
        conn.close()
        return results
    
    def compare_with_known(
        self,
        polynomial_str: str,
        field_order: int,
        computed_order: Optional[int] = None,
        computed_is_primitive: Optional[bool] = None,
        computed_is_irreducible: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Compare computed results with known results.
        
        Args:
            polynomial_str: String representation of polynomial
            field_order: Field order
            computed_order: Computed polynomial order
            computed_is_primitive: Computed primitivity
            computed_is_irreducible: Computed irreducibility
        
        Returns:
            Dictionary with comparison results
        """
        known_results = self.find_matching_results(polynomial_str, field_order)
        
        if not known_results:
            return {
                'found': False,
                'matches': [],
                'verification_status': 'no_reference_data'
            }
        
        matches = []
        for known in known_results:
            match = {
                'known_result': known,
                'order_match': None,
                'primitive_match': None,
                'irreducible_match': None,
                'all_match': False
            }
            
            if computed_order is not None and known.order is not None:
                match['order_match'] = computed_order == known.order
            
            if computed_is_primitive is not None:
                match['primitive_match'] = computed_is_primitive == known.is_primitive
            
            if computed_is_irreducible is not None:
                match['irreducible_match'] = computed_is_irreducible == known.is_irreducible
            
            # All match if all non-None comparisons match
            comparisons = [
                match['order_match'],
                match['primitive_match'],
                match['irreducible_match']
            ]
            valid_comparisons = [c for c in comparisons if c is not None]
            match['all_match'] = all(valid_comparisons) if valid_comparisons else False
            
            matches.append(match)
        
        all_match = any(m['all_match'] for m in matches)
        
        return {
            'found': True,
            'matches': matches,
            'verification_status': 'verified' if all_match else 'mismatch',
            'source': known_results[0].source if known_results else None
        }


def initialize_standard_database(db_path: str = "theoretical_results.db") -> TheoreticalDatabase:
    """
    Initialize database with standard known results.
    
    This function populates the database with well-known primitive polynomials
    and other standard results for common LFSR configurations.
    
    Args:
        db_path: Path to database file
    
    Returns:
        Initialized TheoreticalDatabase instance
    """
    db = TheoreticalDatabase(db_path)
    
    # Standard primitive polynomials over GF(2)
    standard_primitives = [
        ("t^2+t+1", 2, 2, 3, True, True, 3, "standard", "Primitive polynomial of degree 2"),
        ("t^3+t+1", 2, 3, 7, True, True, 7, "standard", "Primitive polynomial of degree 3"),
        ("t^4+t+1", 2, 4, 15, True, True, 15, "standard", "Primitive polynomial of degree 4"),
        ("t^5+t^2+1", 2, 5, 31, True, True, 31, "standard", "Primitive polynomial of degree 5"),
        ("t^6+t+1", 2, 6, 63, True, True, 63, "standard", "Primitive polynomial of degree 6"),
        ("t^7+t+1", 2, 7, 127, True, True, 127, "standard", "Primitive polynomial of degree 7"),
        ("t^8+t^4+t^3+t^2+1", 2, 8, 255, True, True, 255, "standard", "Primitive polynomial of degree 8"),
    ]
    
    for poly_str, field, deg, order, is_prim, is_irr, max_per, source, notes in standard_primitives:
        result = KnownResult(
            polynomial_str=poly_str,
            field_order=field,
            degree=deg,
            order=order,
            is_primitive=is_prim,
            is_irreducible=is_irr,
            max_period=max_per,
            source=source,
            notes=notes
        )
        db.add_result(result)
    
    return db
