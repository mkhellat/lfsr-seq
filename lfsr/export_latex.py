#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LaTeX export functionality for LFSR analysis results.

This module provides functions to export analysis results in LaTeX format,
enabling publication-quality output for research papers and reports.
"""

from typing import Any, Dict, List, Optional, TextIO, Tuple, Union
from datetime import datetime
import json

from lfsr.sage_imports import *


def polynomial_to_latex(polynomial: Any, variable: str = "t") -> str:
    """
    Convert a SageMath polynomial to LaTeX format.
    
    This function converts a polynomial to LaTeX representation suitable
    for inclusion in research papers.
    
    **Key Terminology**:
    
    - **LaTeX**: A document preparation system widely used in academic
      publishing for typesetting mathematical formulas and scientific documents.
    
    - **Polynomial Representation**: Mathematical notation for polynomials,
      e.g., t^4 + t^3 + t + 1 in LaTeX becomes t^4 + t^3 + t + 1.
    
    Args:
        polynomial: SageMath polynomial to convert
        variable: Variable name (default: "t")
    
    Returns:
        LaTeX string representation of the polynomial
    
    Example:
        >>> from lfsr.sage_imports import *
        >>> F = GF(2)
        >>> R = PolynomialRing(F, "t")
        >>> p = R("t^4 + t^3 + t + 1")
        >>> latex_str = polynomial_to_latex(p)
        >>> print(latex_str)
    """
    try:
        # Use SageMath's built-in LaTeX conversion
        latex_str = latex(polynomial)
        # Replace variable if needed
        if variable != "t":
            latex_str = latex_str.replace("t", variable)
        return latex_str
    except (AttributeError, TypeError):
        # Fallback: convert manually
        return str(polynomial).replace("t", variable)


def export_polynomial_analysis_to_latex(
    polynomial: Any,
    polynomial_order: Optional[int],
    is_primitive: bool,
    is_irreducible: bool,
    factors: Optional[List[Tuple[Any, int]]] = None,
    factor_orders: Optional[List[int]] = None,
    field_order: int = 2,
    output_file: Optional[TextIO] = None
) -> str:
    """
    Export polynomial analysis results to LaTeX format.
    
    This function generates LaTeX code for polynomial analysis results,
    including characteristic polynomial, order, primitivity, and factorization.
    
    **Key Terminology**:
    
    - **LaTeX Export**: Converting analysis results into LaTeX format for
      inclusion in research papers or reports.
    
    - **Polynomial Analysis**: Comprehensive analysis of polynomial properties
      including order, primitivity, irreducibility, and factorization.
    
    - **LaTeX Table**: Structured data presentation in LaTeX using tabular
      environment, commonly used in research papers.
    
    Args:
        polynomial: The characteristic polynomial
        polynomial_order: Order of the polynomial
        is_primitive: Whether polynomial is primitive
        is_irreducible: Whether polynomial is irreducible
        factors: List of (factor, multiplicity) tuples
        factor_orders: Orders of each factor
        field_order: Field order (q)
        output_file: Optional file to write LaTeX code to
    
    Returns:
        LaTeX code as string
    """
    latex_code = []
    
    # Document structure
    latex_code.append("\\begin{table}[h]")
    latex_code.append("\\centering")
    latex_code.append("\\caption{Characteristic Polynomial Analysis}")
    latex_code.append("\\label{tab:polynomial_analysis}")
    latex_code.append("\\begin{tabular}{|l|l|}")
    latex_code.append("\\hline")
    latex_code.append("\\textbf{Property} & \\textbf{Value} \\\\")
    latex_code.append("\\hline")
    
    # Polynomial
    poly_latex = polynomial_to_latex(polynomial)
    latex_code.append(f"Characteristic Polynomial & ${poly_latex}$ \\\\")
    latex_code.append("\\hline")
    
    # Field order
    latex_code.append(f"Field Order & $\\mathbb{{F}}_{{{field_order}}}$ \\\\")
    latex_code.append("\\hline")
    
    # Order
    if polynomial_order is not None:
        latex_code.append(f"Polynomial Order & ${polynomial_order}$ \\\\")
    else:
        latex_code.append("Polynomial Order & $\\infty$ \\\\")
    latex_code.append("\\hline")
    
    # Primitivity
    primitive_str = "Yes" if is_primitive else "No"
    latex_code.append(f"Primitive & {primitive_str} \\\\")
    latex_code.append("\\hline")
    
    # Irreducibility
    irreducible_str = "Yes" if is_irreducible else "No"
    latex_code.append(f"Irreducible & {irreducible_str} \\\\")
    latex_code.append("\\hline")
    
    # Factorization
    if factors and len(factors) > 0:
        latex_code.append("\\hline")
        latex_code.append("\\multicolumn{2}{|c|}{\\textbf{Factorization}} \\\\")
        latex_code.append("\\hline")
        latex_code.append("\\textbf{Factor} & \\textbf{Order} \\\\")
        latex_code.append("\\hline")
        
        for i, (factor_poly, multiplicity) in enumerate(factors):
            factor_latex = polynomial_to_latex(factor_poly)
            if multiplicity > 1:
                factor_latex = f"({factor_latex})^{{{multiplicity}}}"
            
            if factor_orders and i < len(factor_orders):
                order = factor_orders[i]
                order_str = str(order) if order is not None else "$\\infty$"
            else:
                order_str = "---"
            
            latex_code.append(f"${factor_latex}$ & ${order_str}$ \\\\")
            latex_code.append("\\hline")
    
    latex_code.append("\\end{tabular}")
    latex_code.append("\\end{table}")
    
    result = "\n".join(latex_code)
    
    if output_file:
        output_file.write(result)
        output_file.write("\n")
    
    return result


def export_period_distribution_to_latex(
    period_dict: Dict[int, int],
    field_order: int,
    lfsr_degree: int,
    is_primitive: bool,
    theoretical_max_period: Optional[int] = None,
    output_file: Optional[TextIO] = None
) -> str:
    """
    Export period distribution to LaTeX format.
    
    This function generates LaTeX code for period distribution tables,
    including statistics and theoretical comparisons.
    
    **Key Terminology**:
    
    - **Period Distribution**: The distribution of periods across all possible
      initial states of an LFSR. This shows how many sequences have each
      possible period.
    
    - **LaTeX Table**: Structured presentation of data in LaTeX format,
      commonly used in research papers for presenting statistical results.
    
    Args:
        period_dict: Dictionary mapping period to count
        field_order: Field order (q)
        lfsr_degree: LFSR degree (d)
        is_primitive: Whether polynomial is primitive
        theoretical_max_period: Theoretical maximum period (q^d - 1)
        output_file: Optional file to write LaTeX code to
    
    Returns:
        LaTeX code as string
    """
    if theoretical_max_period is None:
        theoretical_max_period = int(field_order) ** lfsr_degree - 1
    
    latex_code = []
    
    # Compute statistics
    total_sequences = sum(period_dict.values())
    periods = list(period_dict.keys())
    max_period = max(periods) if periods else 0
    min_period = min(periods) if periods else 0
    
    # Table structure
    latex_code.append("\\begin{table}[h]")
    latex_code.append("\\centering")
    latex_code.append("\\caption{Period Distribution Analysis}")
    latex_code.append("\\label{tab:period_distribution}")
    latex_code.append("\\begin{tabular}{|c|c|c|}")
    latex_code.append("\\hline")
    latex_code.append("\\textbf{Period} & \\textbf{Count} & \\textbf{Percentage} \\\\")
    latex_code.append("\\hline")
    
    # Sort periods for display
    sorted_periods = sorted(period_dict.items(), key=lambda x: x[0], reverse=True)
    
    # Show top 10 periods
    for period, count in sorted_periods[:10]:
        percentage = (count / total_sequences * 100) if total_sequences > 0 else 0
        latex_code.append(f"${period}$ & ${count}$ & ${percentage:.2f}\\%$ \\\\")
        latex_code.append("\\hline")
    
    if len(sorted_periods) > 10:
        latex_code.append("\\multicolumn{3}{|c|}{\\textit{(showing top 10 periods)}} \\\\")
        latex_code.append("\\hline")
    
    latex_code.append("\\end{tabular}")
    latex_code.append("\\end{table}")
    
    # Statistics table
    latex_code.append("\\begin{table}[h]")
    latex_code.append("\\centering")
    latex_code.append("\\caption{Period Distribution Statistics}")
    latex_code.append("\\label{tab:period_stats}")
    latex_code.append("\\begin{tabular}{|l|l|}")
    latex_code.append("\\hline")
    latex_code.append("\\textbf{Statistic} & \\textbf{Value} \\\\")
    latex_code.append("\\hline")
    latex_code.append(f"Total Sequences & ${total_sequences}$ \\\\")
    latex_code.append("\\hline")
    latex_code.append(f"Maximum Period & ${max_period}$ \\\\")
    latex_code.append("\\hline")
    latex_code.append(f"Minimum Period & ${min_period}$ \\\\")
    latex_code.append("\\hline")
    latex_code.append(f"Theoretical Maximum & ${theoretical_max_period}$ \\\\")
    latex_code.append("\\hline")
    latex_code.append(f"Polynomial Primitive & {'Yes' if is_primitive else 'No'} \\\\")
    latex_code.append("\\hline")
    latex_code.append("\\end{tabular}")
    latex_code.append("\\end{table}")
    
    result = "\n".join(latex_code)
    
    if output_file:
        output_file.write(result)
        output_file.write("\n")
    
    return result


def export_complete_analysis_to_latex(
    analysis_results: Dict[str, Any],
    output_file: Optional[TextIO] = None,
    include_preamble: bool = True
) -> str:
    """
    Export complete analysis results to LaTeX document.
    
    This function generates a complete LaTeX document with all analysis
    results, suitable for inclusion in research papers or standalone reports.
    
    **Key Terminology**:
    
    - **LaTeX Document**: A complete LaTeX file that can be compiled into
      a PDF document. Includes preamble (document setup), body (content),
      and optional bibliography.
    
    - **Preamble**: The document setup section in LaTeX, including package
      imports, custom commands, and document class settings.
    
    - **Standalone Document**: A complete LaTeX document that can be compiled
      independently, as opposed to a fragment meant to be included in another
      document.
    
    Args:
        analysis_results: Dictionary containing all analysis results
        output_file: Optional file to write LaTeX code to
        include_preamble: Whether to include LaTeX document preamble
    
    Returns:
        Complete LaTeX document as string
    """
    latex_code = []
    
    if include_preamble:
        # Document preamble
        latex_code.append("\\documentclass[11pt]{article}")
        latex_code.append("\\usepackage[utf8]{inputenc}")
        latex_code.append("\\usepackage{amsmath}")
        latex_code.append("\\usepackage{amssymb}")
        latex_code.append("\\usepackage{booktabs}")
        latex_code.append("\\usepackage{geometry}")
        latex_code.append("\\geometry{a4paper, margin=1in}")
        latex_code.append("\\title{LFSR Analysis Results}")
        latex_code.append("\\author{Generated by lfsr-seq}")
        latex_code.append(f"\\date{{{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}}")
        latex_code.append("\\begin{document}")
        latex_code.append("\\maketitle")
        latex_code.append("")
    
    # Add sections based on available results
    if 'polynomial' in analysis_results:
        latex_code.append("\\section{Characteristic Polynomial Analysis}")
        latex_code.append("")
        poly_result = analysis_results['polynomial']
        poly_latex = export_polynomial_analysis_to_latex(
            polynomial=poly_result.get('polynomial'),
            polynomial_order=poly_result.get('order'),
            is_primitive=poly_result.get('is_primitive', False),
            is_irreducible=poly_result.get('is_irreducible', False),
            factors=poly_result.get('factors'),
            factor_orders=poly_result.get('factor_orders'),
            field_order=poly_result.get('field_order', 2)
        )
        latex_code.append(poly_latex)
        latex_code.append("")
    
    if 'period_distribution' in analysis_results:
        latex_code.append("\\section{Period Distribution}")
        latex_code.append("")
        period_result = analysis_results['period_distribution']
        period_latex = export_period_distribution_to_latex(
            period_dict=period_result.get('period_dict', {}),
            field_order=period_result.get('field_order', 2),
            lfsr_degree=period_result.get('lfsr_degree', 0),
            is_primitive=period_result.get('is_primitive', False),
            theoretical_max_period=period_result.get('theoretical_max_period')
        )
        latex_code.append(period_latex)
        latex_code.append("")
    
    if include_preamble:
        latex_code.append("\\end{document}")
    
    result = "\n".join(latex_code)
    
    if output_file:
        output_file.write(result)
        output_file.write("\n")
    
    return result


def export_to_latex_file(
    analysis_results: Dict[str, Any],
    filename: str,
    include_preamble: bool = True
) -> None:
    """
    Export analysis results to a LaTeX file.
    
    Convenience function to export results directly to a file.
    
    Args:
        analysis_results: Dictionary containing all analysis results
        filename: Output filename (should have .tex extension)
        include_preamble: Whether to include LaTeX document preamble
    """
    with open(filename, 'w', encoding='utf-8') as f:
        export_complete_analysis_to_latex(
            analysis_results,
            output_file=f,
            include_preamble=include_preamble
        )
