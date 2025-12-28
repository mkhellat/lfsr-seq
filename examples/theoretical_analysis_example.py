#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Theoretical Analysis Features

This example demonstrates the theoretical analysis features, including
irreducible polynomial analysis, LaTeX export, paper generation, database
comparison, benchmarking, and reproducibility.

Example Usage:
    python3 examples/theoretical_analysis_example.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import SageMath
try:
    from sage.all import *
except ImportError:
    print("ERROR: SageMath is required for this example", file=sys.stderr)
    sys.exit(1)

from lfsr.theoretical import analyze_irreducible_properties
from lfsr.export_latex import export_to_latex_file, polynomial_to_latex
from lfsr.paper_generator import generate_complete_paper
from lfsr.theoretical_db import get_database
from lfsr.benchmarking import compare_methods
from lfsr.reproducibility import generate_reproducibility_report


def example_irreducible_analysis():
    """Example of irreducible polynomial analysis."""
    print("=" * 70)
    print("Example 1: Irreducible Polynomial Analysis")
    print("=" * 70)
    
    F = GF(2)
    R = PolynomialRing(F, "t")
    p = R("t^4 + t^3 + t + 1")
    
    analysis = analyze_irreducible_properties(p, 2)
    
    print(f"\nPolynomial: {p}")
    print(f"Is irreducible: {analysis.is_irreducible}")
    print(f"Number of factors: {len(analysis.factors)}")
    print(f"Polynomial order: {analysis.polynomial_order}")
    print(f"LCM of factor orders: {analysis.lcm_of_orders}")
    print(f"Has primitive factors: {analysis.has_primitive_factors}")
    
    if analysis.factors:
        print("\nFactors:")
        for i, (factor, multiplicity) in enumerate(analysis.factors):
            print(f"  Factor {i+1}: {factor} (multiplicity: {multiplicity})")
            if i < len(analysis.factor_orders):
                print(f"    Order: {analysis.factor_orders[i]}")


def example_latex_export():
    """Example of LaTeX export."""
    print("\n" + "=" * 70)
    print("Example 2: LaTeX Export")
    print("=" * 70)
    
    F = GF(2)
    R = PolynomialRing(F, "t")
    p = R("t^4 + t^3 + t + 1")
    
    latex_str = polynomial_to_latex(p)
    print(f"\nPolynomial LaTeX: ${latex_str}$")
    
    # Create analysis results
    analysis_results = {
        'field_order': 2,
        'lfsr_degree': 4,
        'polynomial': {
            'polynomial': p,
            'order': 6,
            'is_primitive': False,
            'is_irreducible': False,
            'field_order': 2
        }
    }
    
    # Export to LaTeX (comment out to avoid creating file in examples)
    # export_to_latex_file(analysis_results, "example_output.tex")
    print("\n✓ LaTeX export functionality demonstrated")
    print("  (File export commented out to avoid creating files in examples)")


def example_paper_generation():
    """Example of research paper generation."""
    print("\n" + "=" * 70)
    print("Example 3: Research Paper Generation")
    print("=" * 70)
    
    analysis_results = {
        'field_order': 2,
        'lfsr_degree': 4,
        'max_period': 6,
        'theoretical_max_period': 15,
        'is_primitive': False
    }
    
    paper = generate_complete_paper(
        analysis_results,
        title="LFSR Analysis Example",
        author="Example Researcher"
    )
    
    print(f"\n✓ Generated research paper ({len(paper)} characters)")
    print("  Paper includes: Abstract, Introduction, Methodology, Results, Discussion, Conclusion")
    # Uncomment to save:
    # with open("example_paper.tex", "w") as f:
    #     f.write(paper)


def example_database_comparison():
    """Example of database comparison."""
    print("\n" + "=" * 70)
    print("Example 4: Known Result Database Comparison")
    print("=" * 70)
    
    db = get_database()
    
    # Compare with known results
    comparison = db.compare_with_known(
        coefficients=[1, 0, 0, 1],
        field_order=2,
        degree=4,
        computed_order=6,
        computed_is_primitive=False
    )
    
    print(f"\nFound in database: {comparison['found_in_database']}")
    if comparison['found_in_database']:
        print(f"Known order: {comparison['known_order']}")
        print(f"Known primitive: {comparison['known_is_primitive']}")
        print(f"Order match: {comparison['order_match']}")
        print(f"Matches: {comparison['matches']}")
    else:
        print("No matching results found in database")


def example_benchmarking():
    """Example of benchmarking."""
    print("\n" + "=" * 70)
    print("Example 5: Performance Benchmarking")
    print("=" * 70)
    
    results = compare_methods(
        coefficients=[1, 0, 0, 1],
        field_order=2,
        expected_period=6
    )
    
    print("\nBenchmark Results:")
    for method, result in results.items():
        print(f"\n  Method: {method}")
        print(f"    Execution time: {result.execution_time:.6f} seconds")
        print(f"    Result: {result.result_value}")
        if result.result_correct is not None:
            print(f"    Correct: {result.result_correct}")


def example_reproducibility():
    """Example of reproducibility features."""
    print("\n" + "=" * 70)
    print("Example 6: Reproducibility Report")
    print("=" * 70)
    
    analysis_results = {
        'field_order': 2,
        'lfsr_degree': 4,
        'max_period': 6,
        'is_primitive': False
    }
    
    analysis_config = {
        'coefficients': [1, 0, 0, 1],
        'field_order': 2,
        'degree': 4
    }
    
    report = generate_reproducibility_report(
        analysis_results,
        analysis_config,
        seed=12345
    )
    
    print(f"\n✓ Generated reproducibility report ({len(report)} characters)")
    print("  Report includes: Configuration, Environment, Results Summary, Instructions")
    # Uncomment to save:
    # with open("reproducibility_report.json", "w") as f:
    #     f.write(report)


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Theoretical Analysis Features Examples")
    print("=" * 70)
    print("\nThis script demonstrates theoretical analysis capabilities.")
    
    try:
        example_irreducible_analysis()
        example_latex_export()
        example_paper_generation()
        example_database_comparison()
        example_benchmarking()
        example_reproducibility()
        
        print("\n" + "=" * 70)
        print("Examples Complete!")
        print("=" * 70)
        print("\nFor more information, see:")
        print("  - Theoretical Analysis Guide: docs/theoretical_analysis.rst")
        print("  - API Documentation: docs/api/theoretical.rst")
        
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
