#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Output formatting utilities for LFSR analysis.

This module provides functions for formatting and displaying LFSR analysis
results with decorative borders and structured output.
"""

import datetime
import platform
import textwrap
from typing import Optional, TextIO

from lfsr.constants import (
    DISPLAY_WIDTH,
    INTRO_HEADER_WIDTH,
    LABEL_PADDING_WIDTH,
    PLATFORM_INDENT,
    TEXT_INDENT,
    TEXT_WRAP_WIDTH,
)


def dump(text: str, mode: str, output_file: Optional[TextIO] = None) -> None:
    """
    Dump text to stdout, output file, or both.

    Args:
        text: Text to output
        mode: Output mode ('mode=file', 'mode=console', or 'mode=all')
        output_file: Optional file object to write to (required for file modes)
    """
    if mode == "mode=file":
        if output_file is None:
            raise ValueError("output_file required for mode=file")
        output_file.write(text + "\n")
    elif mode == "mode=console":
        print(text)
    elif mode == "mode=all":
        print(text)
        if output_file is not None:
            output_file.write(text + "\n")
    else:
        print("ERROR: unknown DUMP request")


def intro(
    name: str,
    version: str,
    filename: str,
    gf_order: str,
    output_file: Optional[TextIO] = None,
) -> datetime.datetime:
    """
    Print introduction header with tool information.

    Args:
        name: Tool name
        version: Tool version
        filename: Input CSV filename
        gf_order: Galois field order
        output_file: Optional file object to write to

    Returns:
        Start time datetime object
    """
    start_time = datetime.datetime.now()
    spaces = int((INTRO_HEADER_WIDTH - len(name + version)) / 2)
    identity = " " * spaces + name + version + "\n"
    copyright_t = "Copyright : GNU GPL v3+"
    lfsr_csv_t = "lfsr coeffs csv : " + filename
    gf_order_t = "GF order : " + gf_order
    platform_t = "platform : " + platform.platform()
    runtime_t = "run start time : " + start_time.isoformat()
    copyright = " " * (LABEL_PADDING_WIDTH - len("Copyright")) + copyright_t
    lfsr_csv = " " * (LABEL_PADDING_WIDTH - len("LFSR coeffs csv")) + lfsr_csv_t
    gf_order_str = " " * (LABEL_PADDING_WIDTH - len("GF order")) + gf_order_t
    platform_str = " " * (LABEL_PADDING_WIDTH - len("platform")) + platform_t
    runtime = " " * (LABEL_PADDING_WIDTH - len("run start time")) + runtime_t
    dump("*" * INTRO_HEADER_WIDTH, "mode=all", output_file)
    dump(identity, "mode=all", output_file)
    dump(copyright, "mode=all", output_file)
    dump(lfsr_csv, "mode=all", output_file)
    dump(gf_order_str, "mode=all", output_file)
    dump(
        textwrap.fill(
            platform_str, INTRO_HEADER_WIDTH, subsequent_indent=" " * PLATFORM_INDENT
        ),
        "mode=all",
        output_file,
    )
    dump(runtime, "mode=all", output_file)
    dump("*" * INTRO_HEADER_WIDTH, "mode=all", output_file)
    return start_time


def section(
    section_title: str, section_description: str, output_file: Optional[TextIO] = None
) -> None:
    """
    Print a section header with decorative border.

    Args:
        section_title: Title of the section
        section_description: Description of the section
        output_file: Optional file object to write to
    """
    if not isinstance(section_title, str) or not isinstance(section_description, str):
        print("_SECTION : title and content must be strings")
        exit(1)

    l1 = DISPLAY_WIDTH - len(section_title)
    l2 = int(round(l1 / 2))
    l3 = DISPLAY_WIDTH - len(section_title) - l2
    t_border = "\u2554" + "\u2550" * DISPLAY_WIDTH + "\u2557"
    m_border_l = "\u2560" + " " * l2
    m_border_r = " " * l3 + "\u2563"
    m_border = m_border_l + section_title + m_border_r
    b_border = "\u255a" + "\u2550" * DISPLAY_WIDTH + "\u255d"
    post_dsc_t = "  " + section_description + "  "
    post_dsc = textwrap.fill(
        post_dsc_t,
        width=TEXT_WRAP_WIDTH,
        initial_indent="",
        subsequent_indent=" " * TEXT_INDENT,
    )
    dump("\n" * 1, "mode=all", output_file)
    dump(t_border, "mode=all", output_file)
    dump(m_border, "mode=all", output_file)
    dump(b_border, "mode=all", output_file)
    dump(post_dsc, "mode=all", output_file)


def subsection(
    subsection_title: str,
    subsection_description: str,
    output_file: Optional[TextIO] = None,
) -> None:
    """
    Print a subsection header with decorative border.

    Args:
        subsection_title: Title of the subsection
        subsection_description: Description of the subsection
        output_file: Optional file object to write to
    """
    if not isinstance(subsection_title, str) or not isinstance(
        subsection_description, str
    ):
        print("_SUBSECTION : title and content must be strings")
        exit(1)

    l1 = 4 + len(subsection_title)
    t_border = "\u256d" + "\u254c" * (l1 - 2) + "\u256e"
    m_border_l = "\u251d" + " "
    m_border_r = " " + "\u2525"
    m_border = m_border_l + subsection_title + m_border_r
    b_border = "\u2570" + "\u254c" * (l1 - 2) + "\u256f"
    post_dsc_t = "  " + subsection_description + "  "
    post_dsc = textwrap.fill(
        post_dsc_t,
        width=TEXT_WRAP_WIDTH,
        initial_indent="",
        subsequent_indent=" " * TEXT_INDENT,
    )
    dump(t_border, "mode=all", output_file)
    dump(m_border, "mode=all", output_file)
    dump(b_border, "mode=all", output_file)
    dump(post_dsc, "mode=all", output_file)


def dump_seq_row(
    seq_num: int,
    seq_entry: List[str],
    no_seqs: int,
    row_width: int,
    d_mode: str,
    output_file: Optional[TextIO] = None,
) -> None:
    """
    Dump a sequence table row with decorative borders.

    Args:
        seq_num: Sequence number (1-indexed)
        seq_entry: List of lines for the sequence entry
        no_seqs: Total number of sequences
        row_width: Width of the row
        d_mode: Dump mode ('mode=file', 'mode=console', or 'mode=all')
        output_file: Optional file object to write to
    """
    w = row_width - 1
    t_bar_row_f = " " + "\u250c" + "\u2508" * w + "\u2510"
    b_bar_row_o = " " + "\u251c" + "\u2508" * w + "\u2524"
    b_bar_row_l = " " + "\u2514" + "\u2508" * w + "\u2518"
    if seq_num == 1:
        dump(t_bar_row_f, d_mode, output_file)
    line_num = 0
    for line in seq_entry:
        line_num += 1
        m_bar_line = line + " " * (row_width - len(line)) + " |"
        dump(m_bar_line, d_mode, output_file)
    if seq_num < no_seqs:
        dump(b_bar_row_o, d_mode, output_file)
    else:
        dump(b_bar_row_l, d_mode, output_file)
