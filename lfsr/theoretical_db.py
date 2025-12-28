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
import os

from sage.all import *


@dataclass
class KnownPolynomial:
    """
    Known polynomial result entry.
    
    Attributes:
        coefficients: List of polynomial coefficients
        field_order: Field order (q)
        degree: Polynomial degree
        order: Polynomial order
        is_primitive: Whether polynomial is primitive
        is_irreducible: Whether polynomial is irreducible
        source: Source of the known result (e.g., "standard", "published")
        notes: Additional notes
    """
    coefficients: List[int]
    field_order: int
    degree: int
    order: Optional[int] = None
    is_primitive: bool = False
    is_irreducible: bool = False
    source: str = "standard"
    notes: str = ""


class TheoreticalDatabase:
    """
    Database for storing and querying known theoretical results.
    
    This class provides a framework for storing known polynomial results,
    period distributions, and theoretical bounds, enabling comparison with
    computed results.
    
    **Key Terminology**:
    
    - **Known Result Database**: A collection of precomputed or published
      theoretical results that can be used to verify computed results or
      provide reference values.
    
    - **Polynomial Database**: A database containing known polynomials with
      their properties (order, primitivity, irreducibility) for comparison.
    
    - **Result Verification**: Comparing computed results with known results
      to verify correctness of analysis algorithms.
    
    **Database Schema**:
    
    The database stores:
    - Known primitive polynomials
    - Known irreducible polynomials
    - Known polynomial orders
    - Period distributions for standard configurations
    - Theoretical bounds
    
    Args:
        db_path: Path to SQLite database file (default: ~/.lfsr-seq/theoretical.db)
    """
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to user's home directory
            home = Path.home()
            db_dir = home / ".lfsr-seq"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "theoretical.db")
        
        self.db_path = db_path
        self._init_database()
        self._populate_standard_polynomials()
    
    def _init_database(self) -> None:
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Known polynomials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS known_polynomials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coefficients TEXT NOT NULL,
                field_order INTEGER NOT NULL,
                degree INTEGER NOT NULL,
                polynomial_order INTEGER,
                is_primitive INTEGER NOT NULL DEFAULT 0,
                is_irreducible INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT 'standard',
                notes TEXT,
                UNIQUE(coefficients, field_order)
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_coefficients 
            ON known_polynomials(coefficients, field_order)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_primitive 
            ON known_polynomials(is_primitive, field_order, degree)
        """)
        
        conn.commit()
        conn.close()
    
    def _populate_standard_polynomials(self) -> None:
        """Populate database with standard known polynomials."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if already populated
        cursor.execute("SELECT COUNT(*) FROM known_polynomials")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Add some standard primitive polynomials over GF(2)
            standard_primitives = [
                # (coefficients, degree, order, notes)
                ([1, 0, 0, 1], 4, 15, "t^4 + t + 1 - Standard primitive polynomial"),
                ([1, 0, 0, 0, 1], 5, 31, "t^5 + t^2 + 1 - Standard primitive polynomial"),
                ([1, 0, 0, 0, 0, 1], 6, 63, "t^6 + t + 1 - Standard primitive polynomial"),
                ([1, 0, 0, 0, 0, 0, 1], 7, 127, "t^7 + t + 1 - Standard primitive polynomial"),
                ([1, 0, 0, 0, 0, 0, 0, 1], 8, 255, "t^8 + t^4 + t^3 + t^2 + 1 - Standard primitive polynomial"),
            ]
            
            for coeffs, degree, order, notes in standard_primitives:
                coeffs_str = json.dumps(coeffs)
                cursor.execute("""
                    INSERT OR IGNORE INTO known_polynomials 
                    (coefficients, field_order, degree, polynomial_order, is_primitive, is_irreducible, source, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (coeffs_str, 2, degree, order, 1, 1, "standard", notes))
        
        conn.commit()
        conn.close()
    
    def add_polynomial(
        self,
        coefficients: List[int],
        field_order: int,
        degree: int,
        order: Optional[int] = None,
        is_primitive: bool = False,
        is_irreducible: bool = False,
        source: str = "user",
        notes: str = ""
    ) -> None:
        """
        Add a known polynomial to the database.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            degree: Polynomial degree
            order: Polynomial order (optional)
            is_primitive: Whether primitive
            is_irreducible: Whether irreducible
            source: Source of the result
            notes: Additional notes
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        coeffs_str = json.dumps(coefficients)
        cursor.execute("""
            INSERT OR REPLACE INTO known_polynomials 
            (coefficients, field_order, degree, polynomial_order, is_primitive, is_irreducible, source, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (coeffs_str, field_order, degree, order, 
              int(is_primitive), int(is_irreducible), source, notes))
        
        conn.commit()
        conn.close()
    
    def find_polynomial(
        self,
        coefficients: List[int],
        field_order: int
    ) -> Optional[KnownPolynomial]:
        """
        Find a polynomial in the database.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
        
        Returns:
            KnownPolynomial if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        coeffs_str = json.dumps(coefficients)
        cursor.execute("""
            SELECT coefficients, field_order, degree, polynomial_order,
                   is_primitive, is_irreducible, source, notes
            FROM known_polynomials
            WHERE coefficients = ? AND field_order = ?
        """, (coeffs_str, field_order))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return KnownPolynomial(
                coefficients=json.loads(row[0]),
                field_order=row[1],
                degree=row[2],
                order=row[3],
                is_primitive=bool(row[4]),
                is_irreducible=bool(row[5]),
                source=row[6],
                notes=row[7]
            )
        
        return None
    
    def find_primitive_polynomials(
        self,
        field_order: int,
        degree: Optional[int] = None
    ) -> List[KnownPolynomial]:
        """
        Find primitive polynomials in the database.
        
        Args:
            field_order: Field order
            degree: Optional degree filter
        
        Returns:
            List of known primitive polynomials
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if degree is not None:
            cursor.execute("""
                SELECT coefficients, field_order, degree, polynomial_order,
                       is_primitive, is_irreducible, source, notes
                FROM known_polynomials
                WHERE field_order = ? AND degree = ? AND is_primitive = 1
                ORDER BY degree
            """, (field_order, degree))
        else:
            cursor.execute("""
                SELECT coefficients, field_order, degree, polynomial_order,
                       is_primitive, is_irreducible, source, notes
                FROM known_polynomials
                WHERE field_order = ? AND is_primitive = 1
                ORDER BY degree
            """, (field_order,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            KnownPolynomial(
                coefficients=json.loads(row[0]),
                field_order=row[1],
                degree=row[2],
                order=row[3],
                is_primitive=bool(row[4]),
                is_irreducible=bool(row[5]),
                source=row[6],
                notes=row[7]
            )
            for row in rows
        ]
    
    def compare_with_known(
        self,
        coefficients: List[int],
        field_order: int,
        computed_order: Optional[int] = None,
        computed_is_primitive: Optional[bool] = None,
        computed_is_irreducible: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Compare computed results with known results in database.
        
        Args:
            coefficients: Polynomial coefficients
            field_order: Field order
            computed_order: Computed polynomial order
            computed_is_primitive: Computed primitivity
            computed_is_irreducible: Computed irreducibility
        
        Returns:
            Dictionary with comparison results
        """
        known = self.find_polynomial(coefficients, field_order)
        
        if known is None:
            return {
                'found': False,
                'message': 'Polynomial not found in database'
            }
        
        comparison = {
            'found': True,
            'known': asdict(known),
            'matches': {}
        }
        
        if computed_order is not None and known.order is not None:
            comparison['matches']['order'] = computed_order == known.order
            comparison['order_computed'] = computed_order
            comparison['order_known'] = known.order
        
        if computed_is_primitive is not None:
            comparison['matches']['is_primitive'] = computed_is_primitive == known.is_primitive
            comparison['is_primitive_computed'] = computed_is_primitive
            comparison['is_primitive_known'] = known.is_primitive
        
        if computed_is_irreducible is not None:
            comparison['matches']['is_irreducible'] = computed_is_irreducible == known.is_irreducible
            comparison['is_irreducible_computed'] = computed_is_irreducible
            comparison['is_irreducible_known'] = known.is_irreducible
        
        # Overall verification status
        if comparison['matches']:
            all_match = all(comparison['matches'].values())
            comparison['verification_status'] = 'verified' if all_match else 'mismatch'
        else:
            comparison['verification_status'] = 'partial'
        
        return comparison
