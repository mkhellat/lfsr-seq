#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Export functions for LFSR analysis results.

This module provides functions to export analysis results in various
formats: JSON, CSV, and XML.
"""

import csv
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, TextIO

from sage.all import *


def export_to_json(
    seq_dict: Dict[int, List[Any]],
    period_dict: Dict[int, int],
    max_period: int,
    periods_sum: int,
    char_poly: Any,
    char_poly_order: Any,
    coeffs_vector: List[int],
    gf_order: int,
    output_file: TextIO,
) -> None:
    """
    Export LFSR analysis results to JSON format.

    Args:
        seq_dict: Dictionary mapping sequence numbers to lists of state vectors
        period_dict: Dictionary mapping sequence numbers to periods
        max_period: Maximum period found
        periods_sum: Sum of all periods
        char_poly: Characteristic polynomial
        char_poly_order: Order of characteristic polynomial
        coeffs_vector: LFSR coefficient vector
        gf_order: Field order
        output_file: File object to write JSON to
    """
    # Convert sequences to serializable format
    sequences = {}
    for seq_num, seq in seq_dict.items():
        sequences[str(seq_num)] = {
            "states": [str(state) for state in seq],
            "period": period_dict[seq_num],
        }

    # Convert polynomial to string
    poly_str = str(char_poly)

    # Build JSON structure
    result = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "gf_order": gf_order,
            "coefficients": coeffs_vector,
            "lfsr_degree": len(coeffs_vector),
        },
        "characteristic_polynomial": {
            "polynomial": poly_str,
            "order": str(char_poly_order) if char_poly_order != oo else "infinity",
        },
        "sequences": sequences,
        "statistics": {
            "total_sequences": len(seq_dict),
            "max_period": max_period,
            "periods_sum": periods_sum,
            "state_space_size": periods_sum,
        },
    }

    json.dump(result, output_file, indent=2, ensure_ascii=False)
    output_file.write("\n")


def export_to_csv(
    seq_dict: Dict[int, List[Any]],
    period_dict: Dict[int, int],
    max_period: int,
    periods_sum: int,
    char_poly: Any,
    char_poly_order: Any,
    coeffs_vector: List[int],
    gf_order: int,
    output_file: TextIO,
) -> None:
    """
    Export LFSR analysis results to CSV format.

    Args:
        seq_dict: Dictionary mapping sequence numbers to lists of state vectors
        period_dict: Dictionary mapping sequence numbers to periods
        max_period: Maximum period found
        periods_sum: Sum of all periods
        char_poly: Characteristic polynomial
        char_poly_order: Order of characteristic polynomial
        coeffs_vector: LFSR coefficient vector
        gf_order: Field order
        output_file: File object to write CSV to
    """
    writer = csv.writer(output_file)

    # Write metadata
    writer.writerow(["Field", "Value"])
    writer.writerow(["GF Order", gf_order])
    writer.writerow(["Coefficients", ",".join(map(str, coeffs_vector))])
    writer.writerow(["Characteristic Polynomial", str(char_poly)])
    writer.writerow(["Polynomial Order", str(char_poly_order) if char_poly_order != oo else "infinity"])
    writer.writerow(["Max Period", max_period])
    writer.writerow(["Total Sequences", len(seq_dict)])
    writer.writerow(["Total States", periods_sum])
    writer.writerow([])  # Empty row

    # Write sequences
    writer.writerow(["Sequence Number", "Period", "States"])
    for seq_num in sorted(seq_dict.keys()):
        seq = seq_dict[seq_num]
        period = period_dict[seq_num]
        states_str = "; ".join(str(state) for state in seq)
        writer.writerow([seq_num, period, states_str])


def export_to_xml(
    seq_dict: Dict[int, List[Any]],
    period_dict: Dict[int, int],
    max_period: int,
    periods_sum: int,
    char_poly: Any,
    char_poly_order: Any,
    coeffs_vector: List[int],
    gf_order: int,
    output_file: TextIO,
) -> None:
    """
    Export LFSR analysis results to XML format.

    Args:
        seq_dict: Dictionary mapping sequence numbers to lists of state vectors
        period_dict: Dictionary mapping sequence numbers to periods
        max_period: Maximum period found
        periods_sum: Sum of all periods
        char_poly: Characteristic polynomial
        char_poly_order: Order of characteristic polynomial
        coeffs_vector: LFSR coefficient vector
        gf_order: Field order
        output_file: File object to write XML to
    """
    import xml.etree.ElementTree as ET

    # Create root element
    root = ET.Element("lfsr_analysis")
    root.set("timestamp", datetime.now().isoformat())

    # Metadata
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "gf_order").text = str(gf_order)
    ET.SubElement(metadata, "coefficients").text = ",".join(map(str, coeffs_vector))
    ET.SubElement(metadata, "lfsr_degree").text = str(len(coeffs_vector))

    # Characteristic polynomial
    char_poly_elem = ET.SubElement(root, "characteristic_polynomial")
    ET.SubElement(char_poly_elem, "polynomial").text = str(char_poly)
    ET.SubElement(char_poly_elem, "order").text = (
        str(char_poly_order) if char_poly_order != oo else "infinity"
    )

    # Statistics
    stats = ET.SubElement(root, "statistics")
    ET.SubElement(stats, "total_sequences").text = str(len(seq_dict))
    ET.SubElement(stats, "max_period").text = str(max_period)
    ET.SubElement(stats, "periods_sum").text = str(periods_sum)
    ET.SubElement(stats, "state_space_size").text = str(periods_sum)

    # Sequences
    sequences_elem = ET.SubElement(root, "sequences")
    for seq_num in sorted(seq_dict.keys()):
        seq_elem = ET.SubElement(sequences_elem, "sequence")
        seq_elem.set("number", str(seq_num))
        ET.SubElement(seq_elem, "period").text = str(period_dict[seq_num])

        states_elem = ET.SubElement(seq_elem, "states")
        for state in seq_dict[seq_num]:
            ET.SubElement(states_elem, "state").text = str(state)

    # Write XML
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")  # Pretty print
    tree.write(output_file, encoding="unicode", xml_declaration=True)


def export_nist_to_json(
    suite_result: Any,
    output_file: TextIO,
) -> None:
    """
    Export NIST SP 800-22 test suite results to JSON format.

    Args:
        suite_result: NISTTestSuiteResult object
        output_file: File object to write JSON to
    """
    from lfsr.nist import NISTTestSuiteResult, NISTTestResult

    # Build JSON structure
    result = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "test_suite": "NIST SP 800-22",
            "version": "Revision 1a",
        },
        "sequence": {
            "length": suite_result.sequence_length,
        },
        "test_parameters": {
            "significance_level": suite_result.significance_level,
        },
        "summary": {
            "total_tests": suite_result.total_tests,
            "tests_passed": suite_result.tests_passed,
            "tests_failed": suite_result.tests_failed,
            "pass_rate": suite_result.pass_rate,
            "overall_assessment": suite_result.overall_assessment,
        },
        "test_results": [
            {
                "test_name": test_result.test_name,
                "p_value": test_result.p_value,
                "passed": test_result.passed,
                "statistic": test_result.statistic,
                "details": test_result.details,
            }
            for test_result in suite_result.results
        ],
    }

    json.dump(result, output_file, indent=2, ensure_ascii=False)
    output_file.write("\n")


def export_nist_to_csv(
    suite_result: Any,
    output_file: TextIO,
) -> None:
    """
    Export NIST SP 800-22 test suite results to CSV format.

    Args:
        suite_result: NISTTestSuiteResult object
        output_file: File object to write CSV to
    """
    writer = csv.writer(output_file)

    # Write metadata
    writer.writerow(["Field", "Value"])
    writer.writerow(["Test Suite", "NIST SP 800-22"])
    writer.writerow(["Sequence Length", suite_result.sequence_length])
    writer.writerow(["Significance Level", suite_result.significance_level])
    writer.writerow(["Total Tests", suite_result.total_tests])
    writer.writerow(["Tests Passed", suite_result.tests_passed])
    writer.writerow(["Tests Failed", suite_result.tests_failed])
    writer.writerow(["Pass Rate", f"{suite_result.pass_rate:.2%}"])
    writer.writerow(["Overall Assessment", suite_result.overall_assessment])
    writer.writerow([])  # Empty row

    # Write test results
    writer.writerow(["Test Name", "P-value", "Passed", "Statistic"])
    for test_result in suite_result.results:
        writer.writerow([
            test_result.test_name,
            f"{test_result.p_value:.6f}",
            "PASS" if test_result.passed else "FAIL",
            f"{test_result.statistic:.6f}",
        ])


def export_nist_to_xml(
    suite_result: Any,
    output_file: TextIO,
) -> None:
    """
    Export NIST SP 800-22 test suite results to XML format.

    Args:
        suite_result: NISTTestSuiteResult object
        output_file: File object to write XML to
    """
    import xml.etree.ElementTree as ET

    # Create root element
    root = ET.Element("nist_test_suite")
    root.set("timestamp", datetime.now().isoformat())
    root.set("test_suite", "NIST SP 800-22")
    root.set("version", "Revision 1a")

    # Metadata
    metadata = ET.SubElement(root, "metadata")
    ET.SubElement(metadata, "sequence_length").text = str(suite_result.sequence_length)
    ET.SubElement(metadata, "significance_level").text = str(suite_result.significance_level)

    # Summary
    summary = ET.SubElement(root, "summary")
    ET.SubElement(summary, "total_tests").text = str(suite_result.total_tests)
    ET.SubElement(summary, "tests_passed").text = str(suite_result.tests_passed)
    ET.SubElement(summary, "tests_failed").text = str(suite_result.tests_failed)
    ET.SubElement(summary, "pass_rate").text = f"{suite_result.pass_rate:.6f}"
    ET.SubElement(summary, "overall_assessment").text = suite_result.overall_assessment

    # Test results
    test_results_elem = ET.SubElement(root, "test_results")
    for test_result in suite_result.results:
        test_elem = ET.SubElement(test_results_elem, "test")
        test_elem.set("name", test_result.test_name)
        ET.SubElement(test_elem, "p_value").text = f"{test_result.p_value:.6f}"
        ET.SubElement(test_elem, "passed").text = "true" if test_result.passed else "false"
        ET.SubElement(test_elem, "statistic").text = f"{test_result.statistic:.6f}"

        # Details
        if test_result.details:
            details_elem = ET.SubElement(test_elem, "details")
            for key, value in test_result.details.items():
                detail_elem = ET.SubElement(details_elem, "detail")
                detail_elem.set("key", str(key))
                detail_elem.text = str(value)

    # Write XML
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")  # Pretty print
    tree.write(output_file, encoding="unicode", xml_declaration=True)


def export_nist_to_html(
    suite_result: Any,
    output_file: TextIO,
) -> None:
    """
    Export NIST SP 800-22 test suite results to HTML format.

    Args:
        suite_result: NISTTestSuiteResult object
        output_file: File object to write HTML to
    """
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NIST SP 800-22 Test Suite Results</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .summary {{
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .summary-item {{
            margin: 10px 0;
            font-size: 16px;
        }}
        .summary-item strong {{
            color: #333;
        }}
        .assessment {{
            font-size: 18px;
            font-weight: bold;
            margin-top: 15px;
            padding: 10px;
            border-radius: 5px;
        }}
        .assessment.passed {{
            background-color: #d4edda;
            color: #155724;
        }}
        .assessment.failed {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .pass {{
            color: #28a745;
            font-weight: bold;
        }}
        .fail {{
            color: #dc3545;
            font-weight: bold;
        }}
        .metadata {{
            color: #666;
            font-size: 14px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NIST SP 800-22 Statistical Test Suite Results</h1>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-item">
                <strong>Sequence Length:</strong> {suite_result.sequence_length:,} bits
            </div>
            <div class="summary-item">
                <strong>Significance Level:</strong> {suite_result.significance_level}
            </div>
            <div class="summary-item">
                <strong>Total Tests:</strong> {suite_result.total_tests}
            </div>
            <div class="summary-item">
                <strong>Tests Passed:</strong> {suite_result.tests_passed}
            </div>
            <div class="summary-item">
                <strong>Tests Failed:</strong> {suite_result.tests_failed}
            </div>
            <div class="summary-item">
                <strong>Pass Rate:</strong> {suite_result.pass_rate:.2%}
            </div>
            <div class="assessment {'passed' if suite_result.overall_assessment == 'PASSED' else 'failed'}">
                Overall Assessment: {suite_result.overall_assessment}
            </div>
        </div>
        
        <h2>Individual Test Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>P-value</th>
                    <th>Status</th>
                    <th>Statistic</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for test_result in suite_result.results:
        status_class = "pass" if test_result.passed else "fail"
        status_text = "✓ PASS" if test_result.passed else "✗ FAIL"
        html += f"""                <tr>
                    <td>{test_result.test_name}</td>
                    <td>{test_result.p_value:.6f}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{test_result.statistic:.6f}</td>
                </tr>
"""
    
    html += f"""            </tbody>
        </table>
        
        <div class="metadata">
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Test Suite:</strong> NIST SP 800-22 Revision 1a</p>
        </div>
    </div>
</body>
</html>
"""
    
    output_file.write(html)


def get_export_function(format_name: str):
    """
    Get the appropriate export function for a given format.

    Args:
        format_name: Format name ('json', 'csv', or 'xml')

    Returns:
        Export function

    Raises:
        ValueError: If format is not supported
    """
    formats = {
        "json": export_to_json,
        "csv": export_to_csv,
        "xml": export_to_xml,
    }

    format_lower = format_name.lower()
    if format_lower not in formats:
        raise ValueError(f"Unsupported format: {format_name}. Supported: {list(formats.keys())}")

    return formats[format_lower]


def get_nist_export_function(format_name: str):
    """
    Get the appropriate NIST test suite export function for a given format.

    Args:
        format_name: Format name ('json', 'csv', 'xml', or 'html')

    Returns:
        Export function

    Raises:
        ValueError: If format is not supported
    """
    formats = {
        "json": export_nist_to_json,
        "csv": export_nist_to_csv,
        "xml": export_nist_to_xml,
        "html": export_nist_to_html,
    }

    format_lower = format_name.lower()
    if format_lower not in formats:
        raise ValueError(f"Unsupported format: {format_name}. Supported: {list(formats.keys())}")

    return formats[format_lower]

