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

