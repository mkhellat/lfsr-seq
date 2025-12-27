#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Stream Cipher Comparison Framework

This module provides utilities for comparing different stream ciphers,
analyzing their properties, security, and performance characteristics.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from lfsr.ciphers.base import StreamCipher, CipherAnalysisResult


@dataclass
class CipherComparison:
    """
    Comparison results for multiple ciphers.
    
    Attributes:
        ciphers: List of cipher names being compared
        properties: Dictionary mapping property names to values for each cipher
        security_assessments: Security assessments for each cipher
        performance_metrics: Performance metrics for each cipher
        recommendations: Recommendations based on comparison
    """
    ciphers: List[str]
    properties: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    security_assessments: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    performance_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    recommendations: Dict[str, str] = field(default_factory=dict)


def compare_ciphers(
    cipher_instances: List[StreamCipher],
    analyze_keystream: bool = True,
    keystream_length: int = 1000
) -> CipherComparison:
    """
    Compare multiple stream ciphers.
    
    This function performs a comprehensive comparison of multiple stream ciphers,
    analyzing their structure, security properties, and performance.
    
    **Key Terminology**:
    
    - **Cipher Comparison**: Side-by-side analysis of multiple ciphers
    - **Property Analysis**: Comparing structural properties (LFSR sizes, state size, etc.)
    - **Security Assessment**: Evaluating security properties and known vulnerabilities
    - **Performance Metrics**: Comparing efficiency (speed, memory, etc.)
    - **Design Pattern**: Common design approaches used across ciphers
    
    Args:
        cipher_instances: List of StreamCipher instances to compare
        analyze_keystream: Whether to generate and analyze keystreams
        keystream_length: Length of keystream to generate for analysis
    
    Returns:
        CipherComparison with comprehensive comparison results
    
    Example:
        >>> from lfsr.ciphers import A5_1, E0, Trivium
        >>> ciphers = [A5_1(), E0(), Trivium()]
        >>> comparison = compare_ciphers(ciphers)
        >>> print(comparison.ciphers)
        ['A5/1', 'E0', 'Trivium']
    """
    cipher_names = [cipher.get_config().cipher_name for cipher in cipher_instances]
    
    properties = {}
    security_assessments = {}
    performance_metrics = {}
    recommendations = {}
    
    for cipher in cipher_instances:
        name = cipher.get_config().cipher_name
        config = cipher.get_config()
        structure = cipher.analyze_structure()
        
        # Extract properties
        properties[name] = {
            'key_size': config.key_size,
            'iv_size': config.iv_size,
            'state_size': structure.state_size,
            'num_lfsrs': len(structure.lfsr_configs),
            'lfsr_sizes': [lfsr.degree for lfsr in structure.lfsr_configs],
            'clock_control': structure.clock_control,
            'combiner': structure.combiner
        }
        
        # Security assessment
        security_assessments[name] = {
            'status': _assess_security_status(name),
            'known_vulnerabilities': _get_known_vulnerabilities(name),
            'recommended_use': _get_recommended_use(name)
        }
        
        # Performance metrics (placeholder - would measure actual performance)
        performance_metrics[name] = {
            'estimated_speed': 'medium',  # Placeholder
            'memory_usage': structure.state_size,
            'hardware_efficiency': _assess_hardware_efficiency(name)
        }
        
        # Recommendations
        recommendations[name] = _generate_recommendation(name, security_assessments[name])
    
    return CipherComparison(
        ciphers=cipher_names,
        properties=properties,
        security_assessments=security_assessments,
        performance_metrics=performance_metrics,
        recommendations=recommendations
    )


def _assess_security_status(cipher_name: str) -> str:
    """Assess security status of a cipher."""
    status_map = {
        'A5/1': 'Insecure (broken)',
        'A5/2': 'Extremely Weak (intentionally weak)',
        'E0': 'Weak (known vulnerabilities)',
        'Trivium': 'Secure',
        'Grain-128': 'Secure',
        'Grain-128a': 'Secure',
        'LILI-128': 'Weak (educational example)'
    }
    return status_map.get(cipher_name, 'Unknown')


def _get_known_vulnerabilities(cipher_name: str) -> List[str]:
    """Get known vulnerabilities for a cipher."""
    vulnerabilities = {
        'A5/1': [
            'Time-memory trade-off attacks (seconds)',
            'Correlation attacks',
            'Known-plaintext attacks'
        ],
        'A5/2': [
            'Very fast key recovery (seconds)',
            'Intentionally weakened for export'
        ],
        'E0': [
            'Correlation attacks',
            'Algebraic attacks',
            'Time-memory trade-off attacks'
        ],
        'Trivium': [],
        'Grain-128': [],
        'Grain-128a': [],
        'LILI-128': [
            'Correlation attacks',
            'Clock control analysis'
        ]
    }
    return vulnerabilities.get(cipher_name, [])


def _get_recommended_use(cipher_name: str) -> str:
    """Get recommended use case for a cipher."""
    recommendations = {
        'A5/1': 'Educational purposes only',
        'A5/2': 'DO NOT USE - Educational purposes only',
        'E0': 'Legacy systems only (Bluetooth)',
        'Trivium': 'Hardware-optimized applications',
        'Grain-128': 'Hardware-optimized applications',
        'Grain-128a': 'Hardware-optimized applications with authentication',
        'LILI-128': 'Educational purposes only'
    }
    return recommendations.get(cipher_name, 'Unknown')


def _assess_hardware_efficiency(cipher_name: str) -> str:
    """Assess hardware efficiency of a cipher."""
    efficiency = {
        'A5/1': 'Medium',
        'A5/2': 'Medium',
        'E0': 'Medium',
        'Trivium': 'High (designed for hardware)',
        'Grain-128': 'High (designed for hardware)',
        'Grain-128a': 'High (designed for hardware)',
        'LILI-128': 'Medium'
    }
    return efficiency.get(cipher_name, 'Unknown')


def _generate_recommendation(
    cipher_name: str,
    security_assessment: Dict[str, Any]
) -> str:
    """Generate recommendation for a cipher."""
    status = security_assessment['status']
    
    if 'Insecure' in status or 'Weak' in status:
        return f"⚠️  {cipher_name} is {status.lower()}. Use only for educational purposes."
    elif 'Secure' in status:
        return f"✓ {cipher_name} is {status.lower()}. Suitable for {security_assessment['recommended_use']}."
    else:
        return f"⚠️  Security status of {cipher_name} is unknown. Use with caution."


def print_comparison(comparison: CipherComparison) -> None:
    """
    Print a formatted comparison of ciphers.
    
    Args:
        comparison: CipherComparison to print
    """
    print("=" * 80)
    print("Stream Cipher Comparison")
    print("=" * 80)
    print()
    
    for cipher_name in comparison.ciphers:
        print(f"{'─' * 80}")
        print(f"Cipher: {cipher_name}")
        print(f"{'─' * 80}")
        
        # Properties
        props = comparison.properties[cipher_name]
        print(f"  Key Size: {props['key_size']} bits")
        print(f"  IV Size: {props['iv_size']} bits")
        print(f"  State Size: {props['state_size']} bits")
        print(f"  Number of LFSRs: {props['num_lfsrs']}")
        print(f"  LFSR Sizes: {props['lfsr_sizes']}")
        print(f"  Clock Control: {props['clock_control'][:60]}...")
        print(f"  Combiner: {props['combiner'][:60]}...")
        
        # Security
        security = comparison.security_assessments[cipher_name]
        print(f"  Security Status: {security['status']}")
        if security['known_vulnerabilities']:
            print(f"  Known Vulnerabilities:")
            for vuln in security['known_vulnerabilities']:
                print(f"    - {vuln}")
        print(f"  Recommended Use: {security['recommended_use']}")
        
        # Recommendation
        print(f"  Recommendation: {comparison.recommendations[cipher_name]}")
        print()
    
    print("=" * 80)
