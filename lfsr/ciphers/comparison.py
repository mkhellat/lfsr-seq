#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Stream Cipher Comparison Framework

This module provides utilities for comparing different stream ciphers,
analyzing their properties, and generating comparison reports.
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field

from lfsr.ciphers.base import StreamCipher, CipherAnalysisResult


@dataclass
class CipherComparison:
    """
    Comparison results for multiple ciphers.
    
    Attributes:
        ciphers: List of cipher names being compared
        properties: Dictionary mapping property names to values for each cipher
        security_assessment: Security assessment for each cipher
        recommendations: Recommendations based on comparison
    """
    ciphers: List[str]
    properties: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    security_assessment: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=dict)


def compare_ciphers(
    ciphers: List[StreamCipher],
    analyze_keystream: bool = False,
    key: List[int] = None,
    iv: List[int] = None
) -> CipherComparison:
    """
    Compare multiple stream ciphers.
    
    This function performs a comprehensive comparison of multiple stream ciphers,
    analyzing their structure, properties, and security characteristics.
    
    **Key Terminology**:
    
    - **Cipher Comparison**: Side-by-side analysis of multiple ciphers to identify
      similarities, differences, strengths, and weaknesses.
    
    - **Property Analysis**: Examining cipher properties such as key size, state
      size, structure complexity, and design patterns.
    
    - **Security Assessment**: Evaluating the security of each cipher based on
      known attacks, vulnerabilities, and design strength.
    
    Args:
        ciphers: List of StreamCipher instances to compare
        analyze_keystream: Whether to generate and analyze keystreams
        key: Optional key for keystream generation
        iv: Optional IV for keystream generation
    
    Returns:
        CipherComparison with comparison results
    
    Example:
        >>> from lfsr.ciphers import A5_1, E0, Trivium
        >>> comparison = compare_ciphers([A5_1(), E0(), Trivium()])
        >>> print(comparison.ciphers)
        ['A5/1', 'E0', 'Trivium']
    """
    cipher_names = [c.get_config().cipher_name for c in ciphers]
    
    properties = {}
    security_assessment = {}
    
    # Compare basic properties
    for cipher in ciphers:
        config = cipher.get_config()
        structure = cipher.analyze_structure()
        name = config.cipher_name
        
        properties[name] = {
            'key_size': config.key_size,
            'iv_size': config.iv_size,
            'state_size': structure.state_size,
            'num_lfsrs': len(structure.lfsr_configs),
            'clock_control': structure.clock_control,
            'combiner': structure.combiner
        }
        
        # Security assessment
        security_assessment[name] = {
            'status': 'analyzed',
            'known_vulnerabilities': [],
            'recommendations': []
        }
        
        # Cipher-specific security notes
        if name == "A5/1":
            security_assessment[name]['known_vulnerabilities'] = [
                'Time-memory trade-off attacks',
                'Correlation attacks',
                'Known-plaintext attacks'
            ]
            security_assessment[name]['recommendations'] = [
                'Not recommended for new systems',
                'Use only for educational purposes'
            ]
        elif name == "A5/2":
            security_assessment[name]['known_vulnerabilities'] = [
                'Complete break (Barkan et al., 2003)',
                'Real-time key recovery',
                'Deliberately weakened'
            ]
            security_assessment[name]['recommendations'] = [
                'Never use in production',
                'Educational purposes only'
            ]
        elif name in ["Trivium", "Grain-128", "Grain-128a"]:
            security_assessment[name]['known_vulnerabilities'] = []
            security_assessment[name]['recommendations'] = [
                'Considered secure',
                'Suitable for research and some applications'
            ]
    
    # Generate recommendations
    recommendations = []
    
    # Compare key sizes
    key_sizes = [p['key_size'] for p in properties.values()]
    if min(key_sizes) < 128:
        recommendations.append(
            f"Some ciphers use keys smaller than 128 bits. "
            f"Consider security requirements when selecting cipher."
        )
    
    # Compare state sizes
    state_sizes = [p['state_size'] for p in properties.values()]
    recommendations.append(
        f"State sizes range from {min(state_sizes)} to {max(state_sizes)} bits. "
        f"Larger state generally provides better security."
    )
    
    return CipherComparison(
        ciphers=cipher_names,
        properties=properties,
        security_assessment=security_assessment,
        recommendations=recommendations
    )


def generate_comparison_report(comparison: CipherComparison) -> str:
    """
    Generate a human-readable comparison report.
    
    Args:
        comparison: CipherComparison results
    
    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 70)
    report.append("Stream Cipher Comparison Report")
    report.append("=" * 70)
    report.append("")
    
    report.append("Ciphers Compared:")
    for cipher in comparison.ciphers:
        report.append(f"  - {cipher}")
    report.append("")
    
    report.append("Properties Comparison:")
    report.append("-" * 70)
    
    # Table header
    header = f"{'Property':<20}"
    for cipher in comparison.ciphers:
        header += f"{cipher:<15}"
    report.append(header)
    report.append("-" * 70)
    
    # Key size
    row = f"{'Key Size (bits)':<20}"
    for cipher in comparison.ciphers:
        row += f"{comparison.properties[cipher]['key_size']:<15}"
    report.append(row)
    
    # IV size
    row = f"{'IV Size (bits)':<20}"
    for cipher in comparison.ciphers:
        row += f"{comparison.properties[cipher]['iv_size']:<15}"
    report.append(row)
    
    # State size
    row = f"{'State Size (bits)':<20}"
    for cipher in comparison.ciphers:
        row += f"{comparison.properties[cipher]['state_size']:<15}"
    report.append(row)
    
    # Number of LFSRs
    row = f"{'Number of LFSRs':<20}"
    for cipher in comparison.ciphers:
        row += f"{comparison.properties[cipher]['num_lfsrs']:<15}"
    report.append(row)
    
    report.append("")
    report.append("Security Assessment:")
    report.append("-" * 70)
    
    for cipher in comparison.ciphers:
        report.append(f"{cipher}:")
        vulns = comparison.security_assessment[cipher]['known_vulnerabilities']
        if vulns:
            report.append(f"  Known Vulnerabilities:")
            for vuln in vulns:
                report.append(f"    - {vuln}")
        else:
            report.append(f"  Known Vulnerabilities: None")
        
        recs = comparison.security_assessment[cipher]['recommendations']
        if recs:
            report.append(f"  Recommendations:")
            for rec in recs:
                report.append(f"    - {rec}")
        report.append("")
    
    if comparison.recommendations:
        report.append("General Recommendations:")
        report.append("-" * 70)
        for rec in comparison.recommendations:
            report.append(f"  - {rec}")
        report.append("")
    
    report.append("=" * 70)
    
    return "\n".join(report)
