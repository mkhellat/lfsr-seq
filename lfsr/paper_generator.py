#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Research paper section generation from LFSR analysis results.

This module provides functions to generate research paper sections from
analysis results, including abstract, methodology, results, and discussion.
"""

from typing import Any, Dict, List, Optional, TextIO
from datetime import datetime

from lfsr.export_latex import (
    export_polynomial_analysis_to_latex,
    export_period_distribution_to_latex,
    polynomial_to_latex
)


def generate_abstract_section(
    analysis_results: Dict[str, Any],
    research_focus: Optional[str] = None
) -> str:
    """
    Generate abstract section for research paper.
    
    This function generates an abstract summarizing the LFSR analysis results
    and research findings.
    
    **Key Terminology**:
    
    - **Abstract**: A brief summary of a research paper, typically 150-250
      words, that provides an overview of the research question, methodology,
      results, and conclusions.
    
    - **Research Paper**: A formal document presenting original research
      findings, typically following a standard structure (abstract, introduction,
      methodology, results, discussion, conclusion).
    
    Args:
        analysis_results: Dictionary containing all analysis results
        research_focus: Optional focus area for the research
    
    Returns:
        LaTeX code for abstract section
    """
    latex_code = []
    latex_code.append("\\begin{abstract}")
    latex_code.append("")
    
    # Extract key information
    field_order = analysis_results.get('field_order', 2)
    lfsr_degree = analysis_results.get('lfsr_degree', 0)
    is_primitive = analysis_results.get('is_primitive', False)
    max_period = analysis_results.get('max_period', 0)
    theoretical_max = analysis_results.get('theoretical_max_period', 0)
    
    # Generate abstract content
    abstract_text = f"This paper presents a comprehensive analysis of Linear "
    abstract_text += f"Feedback Shift Registers (LFSRs) over "
    abstract_text += f"$\\mathbb{{F}}_{{{field_order}}}$ of degree {lfsr_degree}. "
    
    if is_primitive:
        abstract_text += "The characteristic polynomial is primitive, "
        abstract_text += f"resulting in maximum period {theoretical_max}. "
    else:
        abstract_text += f"The analysis reveals a maximum period of {max_period}, "
        abstract_text += f"compared to the theoretical maximum of {theoretical_max}. "
    
    if research_focus:
        abstract_text += f"The research focuses on {research_focus}. "
    
    abstract_text += "The results provide insights into the period structure "
    abstract_text += "and cryptographic properties of the analyzed LFSR configuration."
    
    latex_code.append(abstract_text)
    latex_code.append("")
    latex_code.append("\\end{abstract}")
    
    return "\n".join(latex_code)


def generate_methodology_section(
    analysis_results: Dict[str, Any],
    methods_used: Optional[List[str]] = None
) -> str:
    """
    Generate methodology section for research paper.
    
    This function generates a methodology section describing the analysis
    methods and techniques used.
    
    **Key Terminology**:
    
    - **Methodology**: The section of a research paper that describes the
      methods, techniques, and procedures used to conduct the research.
      This allows other researchers to reproduce the work.
    
    - **Reproducibility**: The ability to reproduce research results using
      the same methods and data. Good methodology sections enable reproducibility.
    
    Args:
        analysis_results: Dictionary containing all analysis results
        methods_used: Optional list of methods used (enumeration, factorization, etc.)
    
    Returns:
        LaTeX code for methodology section
    """
    latex_code = []
    latex_code.append("\\section{Methodology}")
    latex_code.append("")
    
    field_order = analysis_results.get('field_order', 2)
    lfsr_degree = analysis_results.get('lfsr_degree', 0)
    
    latex_code.append("This section describes the methodology used to analyze ")
    latex_code.append(f"LFSRs over $\\mathbb{{F}}_{{{field_order}}}$ of degree {lfsr_degree}.")
    latex_code.append("")
    
    latex_code.append("\\subsection{Polynomial Analysis}")
    latex_code.append("")
    latex_code.append("The characteristic polynomial was computed from the ")
    latex_code.append("LFSR feedback coefficients. The polynomial order was ")
    latex_code.append("determined using polynomial order computation algorithms. ")
    latex_code.append("Primitivity and irreducibility were verified using ")
    latex_code.append("SageMath's built-in functions.")
    latex_code.append("")
    
    if methods_used:
        latex_code.append("\\subsection{Period Computation}")
        latex_code.append("")
        latex_code.append("The following methods were employed for period computation:")
        latex_code.append("\\begin{itemize}")
        for method in methods_used:
            latex_code.append(f"\\item {method}")
        latex_code.append("\\end{itemize}")
        latex_code.append("")
    else:
        latex_code.append("\\subsection{Period Computation}")
        latex_code.append("")
        latex_code.append("Period computation was performed through state space ")
        latex_code.append("enumeration and polynomial factorization methods.")
        latex_code.append("")
    
    latex_code.append("\\subsection{Statistical Analysis}")
    latex_code.append("")
    latex_code.append("Period distribution analysis was conducted to understand ")
    latex_code.append("the distribution of periods across all possible initial states. ")
    latex_code.append("Theoretical bounds were computed and compared with observed results.")
    latex_code.append("")
    
    return "\n".join(latex_code)


def generate_results_section(
    analysis_results: Dict[str, Any],
    include_tables: bool = True
) -> str:
    """
    Generate results section for research paper.
    
    This function generates a results section presenting the analysis findings,
    including tables and key observations.
    
    **Key Terminology**:
    
    - **Results Section**: The section of a research paper that presents the
      findings of the research. Typically includes tables, figures, and
      statistical summaries.
    
    - **Key Findings**: The most important results and observations from the
      analysis. These are highlighted in the results section.
    
    Args:
        analysis_results: Dictionary containing all analysis results
        include_tables: Whether to include LaTeX tables
    
    Returns:
        LaTeX code for results section
    """
    latex_code = []
    latex_code.append("\\section{Results}")
    latex_code.append("")
    
    # Polynomial analysis
    if 'polynomial' in analysis_results:
        latex_code.append("\\subsection{Characteristic Polynomial Analysis}")
        latex_code.append("")
        
        poly_result = analysis_results['polynomial']
        poly = poly_result.get('polynomial')
        poly_latex = polynomial_to_latex(poly) if poly else "N/A"
        
        latex_code.append(f"The characteristic polynomial is ${poly_latex}$. ")
        
        if poly_result.get('is_primitive'):
            latex_code.append("The polynomial is primitive, which guarantees ")
            latex_code.append("maximum period sequences.")
        elif poly_result.get('is_irreducible'):
            latex_code.append("The polynomial is irreducible but not primitive.")
        else:
            latex_code.append("The polynomial factors into irreducible components.")
        
        latex_code.append("")
        
        if include_tables:
            table_latex = export_polynomial_analysis_to_latex(
                polynomial=poly_result.get('polynomial'),
                polynomial_order=poly_result.get('order'),
                is_primitive=poly_result.get('is_primitive', False),
                is_irreducible=poly_result.get('is_irreducible', False),
                factors=poly_result.get('factors'),
                factor_orders=poly_result.get('factor_orders'),
                field_order=poly_result.get('field_order', 2)
            )
            latex_code.append(table_latex)
            latex_code.append("")
    
    # Period distribution
    if 'period_distribution' in analysis_results:
        latex_code.append("\\subsection{Period Distribution}")
        latex_code.append("")
        
        period_result = analysis_results['period_distribution']
        period_dict = period_result.get('period_dict', {})
        max_period = max(period_dict.keys()) if period_dict else 0
        theoretical_max = period_result.get('theoretical_max_period', 0)
        
        latex_code.append(f"The analysis revealed a maximum period of {max_period}, ")
        latex_code.append(f"compared to the theoretical maximum of {theoretical_max}. ")
        
        if period_result.get('is_primitive'):
            latex_code.append("As expected for a primitive polynomial, all non-zero ")
            latex_code.append("states achieve the maximum period.")
        else:
            latex_code.append("The period distribution shows variation across ")
            latex_code.append("different initial states.")
        
        latex_code.append("")
        
        if include_tables:
            table_latex = export_period_distribution_to_latex(
                period_dict=period_dict,
                field_order=period_result.get('field_order', 2),
                lfsr_degree=period_result.get('lfsr_degree', 0),
                is_primitive=period_result.get('is_primitive', False),
                theoretical_max_period=theoretical_max
            )
            latex_code.append(table_latex)
            latex_code.append("")
    
    return "\n".join(latex_code)


def generate_discussion_section(
    analysis_results: Dict[str, Any],
    key_observations: Optional[List[str]] = None
) -> str:
    """
    Generate discussion section for research paper.
    
    This function generates a discussion section interpreting the results
    and discussing their implications.
    
    **Key Terminology**:
    
    - **Discussion Section**: The section of a research paper that interprets
      the results, discusses their implications, and relates them to existing
      research. This is where the researcher explains what the results mean.
    
    - **Implications**: The consequences or significance of the research findings.
      The discussion section explores what the results mean for theory and practice.
    
    Args:
        analysis_results: Dictionary containing all analysis results
        key_observations: Optional list of key observations to highlight
    
    Returns:
        LaTeX code for discussion section
    """
    latex_code = []
    latex_code.append("\\section{Discussion}")
    latex_code.append("")
    
    is_primitive = analysis_results.get('is_primitive', False)
    max_period = analysis_results.get('max_period', 0)
    theoretical_max = analysis_results.get('theoretical_max_period', 0)
    
    latex_code.append("The analysis provides insights into the period structure ")
    latex_code.append("and cryptographic properties of the LFSR configuration.")
    latex_code.append("")
    
    if is_primitive:
        latex_code.append("\\subsection{Primitive Polynomial Properties}")
        latex_code.append("")
        latex_code.append("The primitive nature of the characteristic polynomial ")
        latex_code.append("ensures optimal period properties. All non-zero initial ")
        latex_code.append("states generate sequences with maximum period, which is ")
        latex_code.append("desirable for cryptographic applications.")
        latex_code.append("")
    else:
        latex_code.append("\\subsection{Period Structure}")
        latex_code.append("")
        latex_code.append(f"The observed maximum period of {max_period} represents ")
        latex_code.append(f"{max_period/theoretical_max*100:.1f}\\% of the theoretical ")
        latex_code.append("maximum. This indicates the polynomial's period-generating ")
        latex_code.append("capabilities relative to primitive polynomials.")
        latex_code.append("")
    
    if key_observations:
        latex_code.append("\\subsection{Key Observations}")
        latex_code.append("")
        latex_code.append("\\begin{itemize}")
        for observation in key_observations:
            latex_code.append(f"\\item {observation}")
        latex_code.append("\\end{itemize}")
        latex_code.append("")
    
    latex_code.append("\\subsection{Implications}")
    latex_code.append("")
    latex_code.append("These findings have implications for LFSR design in ")
    latex_code.append("cryptographic applications. The period structure analysis ")
    latex_code.append("helps evaluate the suitability of LFSR configurations for ")
    latex_code.append("specific security requirements.")
    latex_code.append("")
    
    return "\n".join(latex_code)


def generate_complete_paper(
    analysis_results: Dict[str, Any],
    title: str = "LFSR Analysis Results",
    author: Optional[str] = None,
    research_focus: Optional[str] = None,
    methods_used: Optional[List[str]] = None,
    key_observations: Optional[List[str]] = None,
    output_file: Optional[TextIO] = None
) -> str:
    """
    Generate complete research paper from analysis results.
    
    This function generates a complete research paper including all standard
    sections: abstract, introduction, methodology, results, discussion, and conclusion.
    
    **Key Terminology**:
    
    - **Research Paper**: A formal document presenting original research findings,
      following standard academic structure and formatting conventions.
    
    - **Paper Structure**: Standard sections of a research paper:
      - Abstract: Brief summary
      - Introduction: Background and research question
      - Methodology: Methods and procedures
      - Results: Findings and data
      - Discussion: Interpretation and implications
      - Conclusion: Summary and future work
    
    Args:
        analysis_results: Dictionary containing all analysis results
        title: Paper title
        author: Author name (optional)
        research_focus: Optional research focus area
        methods_used: Optional list of methods used
        key_observations: Optional list of key observations
        output_file: Optional file to write LaTeX code to
    
    Returns:
        Complete LaTeX document as string
    """
    latex_code = []
    
    # Document preamble
    latex_code.append("\\documentclass[11pt]{article}")
    latex_code.append("\\usepackage[utf8]{inputenc}")
    latex_code.append("\\usepackage{amsmath}")
    latex_code.append("\\usepackage{amssymb}")
    latex_code.append("\\usepackage{booktabs}")
    latex_code.append("\\usepackage{geometry}")
    latex_code.append("\\geometry{a4paper, margin=1in}")
    latex_code.append(f"\\title{{{title}}}")
    if author:
        latex_code.append(f"\\author{{{author}}}")
    else:
        latex_code.append("\\author{Generated by lfsr-seq}")
    latex_code.append(f"\\date{{{datetime.now().strftime('%Y-%m-%d')}}}")
    latex_code.append("")
    latex_code.append("\\begin{document}")
    latex_code.append("\\maketitle")
    latex_code.append("")
    
    # Abstract
    abstract = generate_abstract_section(analysis_results, research_focus)
    latex_code.append(abstract)
    latex_code.append("")
    
    # Introduction
    latex_code.append("\\section{Introduction}")
    latex_code.append("")
    latex_code.append("Linear Feedback Shift Registers (LFSRs) are fundamental ")
    latex_code.append("components in stream cipher design and pseudorandom sequence ")
    latex_code.append("generation. This paper presents a comprehensive analysis of ")
    latex_code.append("LFSR period structure and cryptographic properties.")
    latex_code.append("")
    
    # Methodology
    methodology = generate_methodology_section(analysis_results, methods_used)
    latex_code.append(methodology)
    
    # Results
    results = generate_results_section(analysis_results, include_tables=True)
    latex_code.append(results)
    
    # Discussion
    discussion = generate_discussion_section(analysis_results, key_observations)
    latex_code.append(discussion)
    
    # Conclusion
    latex_code.append("\\section{Conclusion}")
    latex_code.append("")
    latex_code.append("This analysis provides comprehensive insights into the ")
    latex_code.append("period structure and properties of the analyzed LFSR ")
    latex_code.append("configuration. The results contribute to understanding ")
    latex_code.append("LFSR behavior and inform cryptographic design decisions.")
    latex_code.append("")
    
    # End document
    latex_code.append("\\end{document}")
    
    result = "\n".join(latex_code)
    
    if output_file:
        output_file.write(result)
        output_file.write("\n")
    
    return result
