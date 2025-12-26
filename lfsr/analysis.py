#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sequence analysis functions for LFSR.

This module provides functions for analyzing LFSR sequences, computing
periods, and categorizing state vectors.
"""

import datetime
import textwrap
from typing import Any, Dict, List, Optional, Set, TextIO, Tuple

from sage.all import *

from lfsr.constants import PROGRESS_BAR_WIDTH, TABLE_ROW_WIDTH


def _update_progress_display(
    counter: int,
    elp_t: float,
    max_t_t: float,
    state_vector_space_size: int,
) -> None:
    """
    Update and display progress bar information.

    Args:
        counter: Current iteration counter
        elp_t: Total elapsed time so far
        max_t_t: Maximum estimated total time
        state_vector_space_size: Total number of states to process
    """
    _total = str(state_vector_space_size)
    _count = str(counter)
    _ind = " " * (len(_total) - len(_count))
    prog = int(counter * PROGRESS_BAR_WIDTH / state_vector_space_size)
    prog_b = " " * 2 + "\u2588" * prog + " " * (PROGRESS_BAR_WIDTH - prog)
    prog_s = _ind + _count + "/" + _total
    prog_t = " " * 2 + format(elp_t, ".1f") + " s/" + format(max_t_t, ".1f") + " s"
    prog_info = " " * 2 + prog_s + " states checked "
    print(prog_b, end="\b")
    print(prog_t + prog_info, end="\r")


def _find_sequence_cycle_floyd(
    start_state: Any, state_update_matrix: Any, visited_set: set
) -> Tuple[List[Any], int]:
    """
    Find the cycle period using Floyd's cycle detection algorithm (tortoise and hare).
    
    Floyd's algorithm finds the period in O(period) time with O(1) extra space,
    compared to O(period) time and O(period) space for full enumeration.
    This is especially beneficial for large periods.
    
    Args:
        start_state: The initial state vector to start the cycle from
        state_update_matrix: The LFSR state update matrix
        visited_set: Set of already processed states (modified in place)
                     Stores tuples (hashable) instead of vectors (mutable)

    Returns:
        Tuple of (sequence_list, period) where:
        - sequence_list: List of all states in the cycle
        - period: Length of the cycle
    """
    # Floyd's cycle detection algorithm
    # Phase 1: Find a meeting point in the cycle
    # Tortoise moves 1 step, hare moves 2 steps per iteration
    tortoise = start_state
    hare = start_state * state_update_matrix
    
    steps = 0
    max_steps = 10000000  # Safety limit to prevent infinite loops
    
    # Find meeting point (guaranteed to exist since LFSR sequences are periodic)
    while tortoise != hare and steps < max_steps:
        tortoise = tortoise * state_update_matrix
        hare = (hare * state_update_matrix) * state_update_matrix
        steps += 1
    
    # Safety check: if we hit the limit, fall back to enumeration
    if steps >= max_steps:
        return _find_sequence_cycle_enumeration(start_state, state_update_matrix, visited_set)
    
    # Phase 2: Find the period (lambda)
    # After Phase 1, tortoise and hare are at the meeting point
    # Keep tortoise at meeting point, move hare one step, count until they meet again
    # This gives us the period
    meeting_point = tortoise  # Save the meeting point
    lambda_period = 1
    hare = meeting_point * state_update_matrix
    
    # If they're already equal after one step, period is 1
    if meeting_point == hare:
        lambda_period = 1
    else:
        # Count steps until hare returns to meeting point
        while meeting_point != hare and lambda_period < max_steps:
            hare = hare * state_update_matrix
            lambda_period += 1
    
    # Safety check
    if lambda_period >= max_steps:
        return _find_sequence_cycle_enumeration(start_state, state_update_matrix, visited_set)
    
    # NOTE: We still need to enumerate the full sequence for output
    # This means our implementation is NOT O(1) space - it's O(period) space
    # because we store all states in seq_lst. However, Floyd's algorithm
    # still provides value by finding the period efficiently, which can be
    # used as a safety limit.
    # 
    # For true O(1) space, we would only return the period without storing
    # the sequence, but that's not compatible with our use case.
    seq_lst = [start_state]
    start_state_tuple = tuple(start_state)
    visited_set.add(start_state_tuple)
    next_state = start_state * state_update_matrix
    seq_period = 1
    
    # Enumerate until we complete the cycle (we know the period, but need all states)
    # Use the period as a safety limit to prevent infinite loops
    while next_state != start_state and seq_period < lambda_period:
        seq_lst.append(next_state)
        next_state_tuple = tuple(next_state)
        visited_set.add(next_state_tuple)
        seq_period += 1
        next_state = next_state * state_update_matrix
    
    # If we didn't complete the cycle, something is wrong - use enumeration
    if next_state != start_state:
        return _find_sequence_cycle_enumeration(start_state, state_update_matrix, visited_set)
    
    # Use the period found by Floyd (more reliable for large periods)
    return seq_lst, lambda_period


def _find_sequence_cycle_enumeration(
    start_state: Any, state_update_matrix: Any, visited_set: set
) -> Tuple[List[Any], int]:
    """
    Find the complete cycle of states using full enumeration (original method).
    
    This is the fallback method when Floyd's algorithm hits limits or when
    the full sequence is needed for small periods.

    Args:
        start_state: The initial state vector to start the cycle from
        state_update_matrix: The LFSR state update matrix
        visited_set: Set of already processed states (modified in place)
                     Stores tuples (hashable) instead of vectors (mutable)

    Returns:
        Tuple of (sequence_list, period) where:
        - sequence_list: List of all states in the cycle
        - period: Length of the cycle
    """
    seq_lst = [start_state]
    # Convert vector to tuple for hashing (SageMath vectors are mutable and unhashable)
    start_state_tuple = tuple(start_state)
    visited_set.add(start_state_tuple)
    next_state = start_state * state_update_matrix
    seq_period = 1

    while next_state != start_state:
        seq_lst.append(next_state)
        # Convert vector to tuple for hashing
        next_state_tuple = tuple(next_state)
        visited_set.add(next_state_tuple)
        seq_period += 1
        next_state = next_state * state_update_matrix

    return seq_lst, seq_period


def _find_sequence_cycle(
    start_state: Any, state_update_matrix: Any, visited_set: set, algorithm: str = "auto"
) -> Tuple[List[Any], int]:
    """
    Find the complete cycle of states starting from a given state.
    
    Uses Floyd's cycle detection algorithm for efficiency, with fallback to
    enumeration for safety or when full sequence is needed.

    Args:
        start_state: The initial state vector to start the cycle from
        state_update_matrix: The LFSR state update matrix
        visited_set: Set of already processed states (modified in place)
                     Stores tuples (hashable) instead of vectors (mutable)
        algorithm: Algorithm to use: "floyd", "enumeration", or "auto" (default: "auto")
                   "auto" uses Floyd's algorithm by default

    Returns:
        Tuple of (sequence_list, period) where:
        - sequence_list: List of all states in the cycle
        - period: Length of the cycle
    """
    if algorithm == "enumeration":
        return _find_sequence_cycle_enumeration(start_state, state_update_matrix, visited_set)
    elif algorithm == "floyd" or algorithm == "auto":
        # Use Floyd's algorithm for efficiency (especially for large periods)
        # Falls back to enumeration if limits are hit or for safety
        return _find_sequence_cycle_floyd(start_state, state_update_matrix, visited_set)
    else:
        # Invalid algorithm, default to Floyd
        return _find_sequence_cycle_floyd(start_state, state_update_matrix, visited_set)


def _format_sequence_entry(
    seq_num: int,
    sequence: List[Any],
    period: int,
    max_period: int,
    special_state: Any,
    row_width: int,
) -> Tuple[List[str], List[str]]:
    """
    Format a sequence entry for display.

    Args:
        seq_num: Sequence number
        sequence: List of states in the sequence
        period: Period of the sequence
        max_period: Maximum period found (for formatting)
        special_state: Special state vector to highlight
        row_width: Width of the display row

    Returns:
        Tuple of (seq_entry, seq_all_v) where:
        - seq_entry: Formatted entry for console (shortened)
        - seq_all_v: Formatted entry for file (full sequence)
    """
    p_str = str(period)
    p_max_str = str(max_period)
    s1 = 3 - len(str(seq_num))
    s2 = 1 + len(p_max_str) - len(p_str)

    if special_state in sequence:
        seq_column_1 = " | ** sequence" + " " * s1 + str(seq_num)
    else:
        seq_column_1 = " |    sequence" + " " * s1 + str(seq_num)

    seq_column_2 = " | T : " + p_str + " " * s2 + "| "
    indent_i = seq_column_1 + seq_column_2
    indent_w = len(indent_i) - 5
    indent_s = " | " + " " * indent_w + "| "

    if special_state in sequence:
        entry_text = str(special_state)
    else:
        entry_text = str(sequence[0])

    seq_entry = textwrap.wrap(
        entry_text, width=row_width, initial_indent=indent_i, subsequent_indent=indent_s
    )
    seq_all_v = textwrap.wrap(
        str(sequence),
        width=row_width,
        initial_indent=indent_i,
        subsequent_indent=indent_s,
    )

    return seq_entry, seq_all_v


def lfsr_sequence_mapper(
    state_update_matrix: Any,
    state_vector_space: Any,
    gf_order: int,
    output_file: Optional[TextIO] = None,
    no_progress: bool = False,
    algorithm: str = "auto",
) -> Tuple[Dict[int, List[Any]], Dict[int, int], int, int]:
    """
    Map all possible state vectors to their sequences and periods.

    Goes through all possible state vectors, finds their periods and
    categorizes them based on what sequence they belong to.

    This function uses a set-based visited tracking for O(1) membership
    testing, improving performance from O(n²) to O(n) for large state spaces.

    Args:
        state_update_matrix: The LFSR state update matrix
        state_vector_space: Vector space of all possible states
        gf_order: The field order
        output_file: Optional file object for output

    Returns:
        Tuple of (seq_dict, period_dict, max_period, periods_sum)
        where:
        - seq_dict: Dictionary mapping sequence numbers to lists of state vectors
        - period_dict: Dictionary mapping sequence numbers to periods
        - max_period: Maximum period found
        - periods_sum: Sum of all periods
    """
    from lfsr.formatter import dump, dump_seq_row, subsection

    subsec_name = "STATES SEQUENCES"
    subsec_desc = "all possible state sequences " + "and their corresponding periods"
    subsection(subsec_name, subsec_desc, output_file)

    seq_dict = {}
    period_dict = {}
    visited_set = set()  # Use set for O(1) membership testing instead of O(n) list lookup
    timer_lst = [datetime.datetime.now()]  # Initialize with first timestamp
    est_t_lst = []
    seq = 0
    counter = 0
    max_period = 1
    elp_t = 0.0
    max_t_t = 0.0
    d = len(basis(state_vector_space))
    state_vector_space_size = int(gf_order) ** d

    for bra in state_vector_space:
        timer_lst.append(datetime.datetime.now())
        counter += 1

        # Calculate elapsed time and estimates
        if counter > 1:
            ticks = counter
            elp_delta = timer_lst[counter] - timer_lst[counter - 1]
            elp_s_int = float(elp_delta.seconds)
            elp_s_dec = float(elp_delta.microseconds) * 10**-6
            elp_s = elp_s_int + elp_s_dec
            elp_t = elp_t + elp_s
            est_t_s = elp_t / ticks
            est_t_t = state_vector_space_size * est_t_s
            est_t_lst.append(est_t_t)
            if counter >= 3 and len(est_t_lst) >= 3:
                # ref is the index of the previous estimate (counter - 2)
                # est_t_lst has indices: 0, 1, 2, ... (one per iteration after counter > 1)
                # When counter = 3, est_t_lst has [est_t_t], so index 0
                # When counter = 4, est_t_lst has [est_t_t1, est_t_t2], so indices 0, 1
                # We want to compare the current estimate with the average of previous two
                ref = len(est_t_lst) - 1  # Current estimate index
                if ref >= 2:
                    est_t_avg = (est_t_lst[ref - 1] + est_t_lst[ref - 2]) / 2
                    if est_t_lst[ref] > est_t_avg:
                        max_t_t = est_t_lst[ref]

            # Update progress display (unless disabled)
            if not no_progress:
                _update_progress_display(counter, elp_t, max_t_t, state_vector_space_size)

        # Find sequence cycle if not already processed
        # O(1) lookup with set instead of O(n) with list
        # Convert vector to tuple for hashing (SageMath vectors are mutable and unhashable)
        bra_tuple = tuple(bra)
        if bra_tuple not in visited_set:
            seq += 1
            seq_lst, seq_period = _find_sequence_cycle(
                bra, state_update_matrix, visited_set, algorithm=algorithm
            )
            seq_dict[seq] = seq_lst
            period_dict[seq] = seq_period
            if seq_period > max_period:
                max_period = seq_period

    # Display sequences
    print("\n")
    periods_sum = sum(period_dict.values())
    num_sequences = len(period_dict)
    row_width = TABLE_ROW_WIDTH
    special_state = vector({d - 1: 1})  # Special state vector to highlight

    for seq_num, sequence in seq_dict.items():
        period = period_dict[seq_num]
        seq_entry, seq_all_v = _format_sequence_entry(
            seq_num, sequence, period, max_period, special_state, row_width
        )

        # Display shortened version to console, full version to file
        dump_seq_row(
            seq_num, seq_entry, num_sequences, row_width, "mode=console", output_file
        )
        dump_seq_row(
            seq_num, seq_all_v, num_sequences, row_width, "mode=file", output_file
        )

    dump("  PERIOD VALUES SUMMED : " + str(periods_sum), "mode=all", output_file)
    dump(
        "     NO. STATE VECTORS : " + str(state_vector_space_size),
        "mode=all",
        output_file,
    )
    # Verification: periods_sum should equal state_vector_space_size
    # This confirms all states have been checked and categorized

    return seq_dict, period_dict, max_period, periods_sum
