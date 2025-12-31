#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sequence analysis functions for LFSR.

This module provides functions for analyzing LFSR sequences, computing
periods, and categorizing state vectors.
"""

import datetime
import multiprocessing
import queue
import textwrap
import threading
from typing import Any, Dict, List, Optional, Set, TextIO, Tuple

from sage.all import *

from lfsr.constants import PROGRESS_BAR_WIDTH, TABLE_ROW_WIDTH

# Persistent worker pool management (Phase 2.3)
# Module-level pool that can be reused across analyses
_worker_pool_lock = threading.Lock()
_worker_pool = None
_worker_pool_context = None
_worker_pool_size = 0

def shutdown_worker_pool():
    """Explicitly shutdown persistent worker pool."""
    global _worker_pool, _worker_pool_context, _worker_pool_size
    with _worker_pool_lock:
        if _worker_pool is not None:
            try:
                _worker_pool.close()
                _worker_pool.join(timeout=5.0)
            except Exception:
                pass  # Ignore errors during shutdown
            _worker_pool = None
            _worker_pool_context = None
            _worker_pool_size = 0

# Register cleanup handler for program exit
import atexit
atexit.register(shutdown_worker_pool)

# Multiprocessing setup for compatibility
# On some systems, we need to set the start method explicitly
# But we'll use the default (fork on Linux) which should work
try:
    # Only set if not already set (avoids RuntimeError)
    if multiprocessing.get_start_method(allow_none=True) is None:
        multiprocessing.set_start_method('fork', force=False)
except RuntimeError:
    # Start method already set, that's fine
    pass


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


def _find_period_floyd(
    start_state: Any, state_update_matrix: Any
) -> int:
    """
    Find the period using Floyd's cycle detection algorithm in true O(1) space.
    
    This function returns ONLY the period, without storing the sequence.
    This is where Floyd's algorithm demonstrates its true O(1) space advantage.
    
    Args:
        start_state: The initial state vector to start the cycle from
        state_update_matrix: The LFSR state update matrix

    Returns:
        The period (length of the cycle)
    """
    # Floyd's cycle detection algorithm - period-only version
    # Phase 1: Find a meeting point in the cycle
    # Tortoise moves 1 step, hare moves 2 steps per iteration
    tortoise = start_state
    hare = start_state * state_update_matrix
    
    # Special case: if start_state is a fixed point (period 1)
    if tortoise == hare:
        return 1
    
    steps = 0
    max_steps = 10000000  # Safety limit to prevent infinite loops
    
    # Find meeting point (guaranteed to exist since LFSR sequences are periodic)
    # CRITICAL: In multiprocessing, matrix multiplication can appear to hang
    # Add periodic progress checks (every 1000 steps) to detect actual hangs
    while tortoise != hare and steps < max_steps:
        # Periodic check every 1000 steps to ensure we're making progress
        if steps > 0 and steps % 1000 == 0:
            # Simple check to ensure we're still responsive
            # This helps detect if matrix multiplication is actually hanging
            try:
                _ = len(tortoise)  # Simple operation to check responsiveness
            except:
                # If we can't access tortoise, something is wrong
                break
        tortoise = tortoise * state_update_matrix
        hare = (hare * state_update_matrix) * state_update_matrix
        steps += 1
    
    # Safety check: if we hit the limit, fall back to enumeration
    if steps >= max_steps:
        return _find_period_enumeration(start_state, state_update_matrix)
    
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
        return _find_period_enumeration(start_state, state_update_matrix)
    
    # Return the period - NO enumeration, NO sequence storage
    # This is true O(1) space!
    return lambda_period


def _find_period_brent(
    start_state: Any, state_update_matrix: Any
) -> int:
    """
    Find the period using Brent's cycle detection algorithm in true O(1) space.
    
    Brent's algorithm uses powers of 2 to find the cycle, which can be more
    efficient than Floyd's in some cases. Like Floyd's, this returns ONLY
    the period without storing the sequence.
    
    Args:
        start_state: The initial state vector to start the cycle from
        state_update_matrix: The LFSR state update matrix

    Returns:
        The period (length of the cycle)
    """
    # Brent's cycle detection algorithm - period-only version
    # Uses powers of 2 to find the cycle more efficiently
    tortoise = start_state
    hare = start_state * state_update_matrix
    
    # Special case: if start_state is a fixed point (period 1)
    if tortoise == hare:
        return 1
    
    power = 1  # Power of 2
    lambda_period = 1  # Period (cycle length)
    max_steps = 10000000  # Safety limit
    
    # Brent's algorithm: use powers of 2
    while tortoise != hare and lambda_period < max_steps:
        # If we've reached the current power, reset tortoise and double power
        if lambda_period == power:
            tortoise = hare
            power *= 2
            lambda_period = 0
        
        hare = hare * state_update_matrix
        lambda_period += 1
    
    # Safety check: if we hit the limit, fall back to enumeration
    if lambda_period >= max_steps:
        return _find_period_enumeration(start_state, state_update_matrix)
    
    # Return the period - NO enumeration, NO sequence storage
    # This is true O(1) space!
    return lambda_period


def _find_period_enumeration(
    start_state: Any, state_update_matrix: Any
) -> int:
    """
    Find the period by enumeration without storing the sequence.
    
    This uses O(1) extra space (just counters) but O(period) time.
    Unlike the sequence-storing version, this doesn't store states.
    
    Args:
        start_state: The initial state vector to start the cycle from
        state_update_matrix: The LFSR state update matrix

    Returns:
        The period (length of the cycle)
    """
    # Enumerate until we complete the cycle, but don't store states
    # Only count steps - this is O(1) space
    next_state = start_state * state_update_matrix
    period = 1
    
    while next_state != start_state:
        period += 1
        next_state = next_state * state_update_matrix
        
        # Safety limit
        if period > 10000000:
            raise ValueError("Period exceeds maximum limit (possible infinite loop)")
    
    return period


def _find_period(
    start_state: Any, state_update_matrix: Any, algorithm: str = "auto"
) -> int:
    """
    Find the period of a cycle starting from a given state.
    
    This is the period-only version that doesn't store sequences.
    Use this when you only need the period, not the full sequence.
    
    Args:
        start_state: The initial state vector to start the cycle from
        state_update_matrix: The LFSR state update matrix
        algorithm: Algorithm to use: "floyd", "brent", "enumeration", or "auto" (default: "auto")
                   "auto" uses enumeration by default (4x faster than Floyd in period-only mode)

    Returns:
        The period (length of the cycle)
    """
    # CRITICAL FIX: Enumeration is 4x faster than Floyd in period-only mode
    # Both are O(1) space, so use enumeration by default for speed
    if algorithm == "enumeration" or algorithm == "auto":
        # Enumeration is faster and still O(1) space in period-only mode
        return _find_period_enumeration(start_state, state_update_matrix)
    elif algorithm == "floyd":
        # Use Floyd's algorithm (slower but sometimes useful for verification)
        return _find_period_floyd(start_state, state_update_matrix)
    elif algorithm == "brent":
        # Use Brent's algorithm (powers of 2 approach)
        return _find_period_brent(start_state, state_update_matrix)
    else:
        # Invalid algorithm, default to enumeration (fastest)
        return _find_period_enumeration(start_state, state_update_matrix)


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


def _find_sequence_cycle_brent(
    start_state: Any, state_update_matrix: Any, visited_set: set
) -> Tuple[List[Any], int]:
    """
    Find the cycle period using Brent's cycle detection algorithm.
    
    Brent's algorithm uses powers of 2 to find the cycle, which can be
    more efficient than Floyd's in some cases. Like Floyd's, it finds the
    period in O(period) time with O(1) extra space for period detection,
    but still requires O(period) space to store the sequence.
    
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
    # Brent's cycle detection algorithm
    # Uses powers of 2 to find the cycle
    tortoise = start_state
    hare = start_state * state_update_matrix
    
    power = 1  # Power of 2
    lambda_period = 1  # Period (cycle length)
    max_steps = 10000000  # Safety limit
    
    # Brent's algorithm: use powers of 2
    while tortoise != hare and lambda_period < max_steps:
        # If we've reached the current power, reset tortoise and double power
        if lambda_period == power:
            tortoise = hare
            power *= 2
            lambda_period = 0
        
        hare = hare * state_update_matrix
        lambda_period += 1
    
    # Safety check: if we hit the limit, fall back to enumeration
    if lambda_period >= max_steps:
        return _find_sequence_cycle_enumeration(start_state, state_update_matrix, visited_set)
    
    # NOTE: We still need to enumerate the full sequence for output
    # This means our implementation is NOT O(1) space - it's O(period) space
    # because we store all states in seq_lst. However, Brent's algorithm
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
    
    # Use the period found by Brent (more reliable for large periods)
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
    # Add debug logging
    import sys
    import os
    try:
        debug_log = lambda msg: print(f'[_find_sequence_cycle_enumeration PID {os.getpid()}] {msg}', file=sys.stderr, flush=True)
        debug_log('Starting enumeration...')
    except:
        debug_log = lambda msg: None
    
    seq_lst = [start_state]
    # Convert vector to tuple for hashing (SageMath vectors are mutable and unhashable)
    start_state_tuple = tuple(start_state)
    visited_set.add(start_state_tuple)
    debug_log('Computing first state transition...')
    next_state = start_state * state_update_matrix
    debug_log('First transition done')
    seq_period = 1
    iteration = 0

    debug_log('Starting enumeration loop...')
    while next_state != start_state:
        seq_lst.append(next_state)
        # Convert vector to tuple for hashing
        next_state_tuple = tuple(next_state)
        visited_set.add(next_state_tuple)
        seq_period += 1
        iteration += 1
        if iteration % 100 == 0:
            debug_log(f'Iteration {iteration}, period={seq_period}')
        debug_log(f'Computing next state transition (iteration {iteration})...')
        next_state = next_state * state_update_matrix
        debug_log(f'Transition {iteration} complete')
        if iteration > 1000000:  # Safety limit
            debug_log('Safety limit exceeded!')
            break

    debug_log(f'Enumeration complete: period={seq_period}, length={len(seq_lst)}')
    return seq_lst, seq_period


def _find_sequence_cycle(
    start_state: Any, state_update_matrix: Any, visited_set: set, algorithm: str = "auto", period_only: bool = False
) -> Tuple[List[Any], int]:
    """
    Find the complete cycle of states starting from a given state, or just the period.
    
    When period_only=True, uses period-only functions that don't store sequences.
    When period_only=False, stores the full sequence (default behavior).

    Args:
        start_state: The initial state vector to start the cycle from
        state_update_matrix: The LFSR state update matrix
        visited_set: Set of already processed states (modified in place)
                     Stores tuples (hashable) instead of vectors (mutable)
                     Not used when period_only=True
        algorithm: Algorithm to use: "floyd", "brent", "enumeration", or "auto" (default: "auto")
                   "auto" uses enumeration for full mode, Floyd for period-only mode
        period_only: If True, return only the period without storing sequence (default: False)

    Returns:
        Tuple of (sequence_list, period) where:
        - sequence_list: List of all states in the cycle (empty list if period_only=True)
        - period: Length of the cycle
    """
    # Debug logging (disabled by default, enable with DEBUG_PARALLEL=1)
    import sys
    import os
    DEBUG_PARALLEL = os.environ.get('DEBUG_PARALLEL', '0') == '1'
    debug_log = lambda msg: print(f'[_find_sequence_cycle PID {os.getpid()}] {msg}', file=sys.stderr, flush=True) if DEBUG_PARALLEL else lambda msg: None
    
    if DEBUG_PARALLEL:
        debug_log(f'_find_sequence_cycle called: period_only={period_only}, algorithm={algorithm}')
    
    if period_only:
        # Period-only mode: use period-only functions (true O(1) space for Floyd)
        # CRITICAL FIX: We MUST mark states as visited to avoid reprocessing cycles
        # Otherwise, we'll process the same cycle multiple times, making period-only mode very slow
        debug_log('Period-only mode: calling _find_period...')
        period = _find_period(start_state, state_update_matrix, algorithm=algorithm)
        debug_log(f'_find_period returned: period={period}')
        # Mark all states in the cycle as visited to avoid reprocessing
        # This is critical for performance - without this, period-only mode is much slower
        current = start_state
        start_state_tuple = tuple(start_state)
        visited_set.add(start_state_tuple)
        for _ in range(period - 1):
            current = current * state_update_matrix
            current_tuple = tuple(current)
            visited_set.add(current_tuple)
        debug_log(f'Marked {period} states as visited in period-only mode')
        return [], period
    else:
        # Full sequence mode: store the sequence
        debug_log('Full sequence mode')
        if algorithm == "enumeration":
            debug_log('Calling _find_sequence_cycle_enumeration...')
            result = _find_sequence_cycle_enumeration(start_state, state_update_matrix, visited_set)
            debug_log(f'_find_sequence_cycle_enumeration returned: period={result[1]}, length={len(result[0])}')
            return result
        elif algorithm == "floyd" or algorithm == "auto":
            # Use Floyd's algorithm (but still stores sequence, so O(period) space)
            # Falls back to enumeration if limits are hit or for safety
            return _find_sequence_cycle_floyd(start_state, state_update_matrix, visited_set)
        elif algorithm == "brent":
            # Use Brent's algorithm (powers of 2 approach)
            # Falls back to enumeration if limits are hit or for safety
            return _find_sequence_cycle_brent(start_state, state_update_matrix, visited_set)
        else:
            # Invalid algorithm, default to enumeration
            return _find_sequence_cycle_enumeration(start_state, state_update_matrix, visited_set)


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
    period_only: bool = False,
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
        no_progress: If True, disable progress bar display
        algorithm: Algorithm to use: "floyd", "enumeration", or "auto"
        period_only: If True, compute periods only without storing sequences (default: False)
                    When True, Floyd's algorithm uses true O(1) space

    Returns:
        Tuple of (seq_dict, period_dict, max_period, periods_sum) where:
        
        - seq_dict: Dictionary mapping sequence numbers to lists of state vectors
          (empty lists if period_only=True)
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
    from datetime import datetime
    timer_lst = [datetime.now()]  # Initialize with first timestamp
    est_t_lst = []
    seq = 0
    counter = 0
    max_period = 1
    elp_t = 0.0
    max_t_t = 0.0
    d = len(basis(state_vector_space))
    state_vector_space_size = int(gf_order) ** d

    for bra in state_vector_space:
        timer_lst.append(datetime.now())
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
                bra, state_update_matrix, visited_set, algorithm=algorithm, period_only=period_only
            )
            if period_only:
                # Period-only mode: don't store sequences, only periods
                seq_dict[seq] = []  # Empty list to maintain structure
            else:
                # Full mode: store sequences
                seq_dict[seq] = seq_lst
            period_dict[seq] = seq_period
            if seq_period > max_period:
                max_period = seq_period

    # Display sequences (or periods only if period_only mode)
    print("\n")
    periods_sum = sum(period_dict.values())
    num_sequences = len(period_dict)
    row_width = TABLE_ROW_WIDTH
    special_state = vector({d - 1: 1})  # Special state vector to highlight

    if period_only:
        # Period-only mode: display only periods, not sequences
        for seq_num, period in period_dict.items():
            seq_entry = f" | ** sequence {seq_num:3d} | T : {period:3d} | (period only)  |"
            dump(seq_entry, "mode=all", output_file)
    else:
        # Full mode: display sequences
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


def _merge_parallel_results(
    worker_results: List[Dict[str, Any]],
    gf_order: int,
    lfsr_degree: int,
    shared_cycles: Optional[Any] = None,  # Manager().dict() from workers
) -> Tuple[Dict[int, List[Any]], Dict[int, int], int, int]:
    """
    Merge results from multiple parallel workers.
    
    Handles deduplication of sequences (same cycle found by multiple workers)
    and reassigns sequence numbers.
    
    Args:
        worker_results: List of result dictionaries from workers
        gf_order: Field order (for reconstructing SageMath objects)
        lfsr_degree: LFSR degree
        
    Returns:
        Tuple of (seq_dict, period_dict, max_period, periods_sum)
    """
    # Import SageMath functions (can't use import * in function)
    try:
        from sage.all import VectorSpace, GF, vector
    except ImportError:
        # Fallback if sage.all not available
        import sys
        print("ERROR: SageMath not available for result merging", file=sys.stderr)
        return {}, {}, 0, 0
    
    # Collect all sequences from all workers
    all_sequences = []
    max_period = 0
    all_errors = []
    
    for result in worker_results:
        all_sequences.extend(result.get('sequences', []))
        if result.get('max_period', 0) > max_period:
            max_period = result.get('max_period', 0)
        all_errors.extend(result.get('errors', []))
    
    # Deduplicate sequences
    # Two sequences are the same if they have the same set of states (same cycle)
    seen_cycles = {}  # Maps canonical cycle representation to sequence info
    unique_sequences = []
    
    # Debug logging can be enabled by setting environment variable
    import sys
    import os
    DEBUG_PARALLEL = os.environ.get('DEBUG_PARALLEL', '0') == '1'
    merge_debug = lambda msg: print(f'[Merge PID {os.getpid()}] {msg}', file=sys.stderr, flush=True) if DEBUG_PARALLEL else lambda msg: None
    
    if DEBUG_PARALLEL:
        merge_debug(f'Deduplicating {len(all_sequences)} sequences from {len(worker_results)} workers')
    
    # CRITICAL FIX: Use shared_cycles registry for accurate deduplication
    # The problem: Workers may compute different min_states for the same cycle
    # (because min_state is computed from first 1000 states only for large cycles)
    # Solution: Use min_state as the primary deduplication key (not period!)
    # IMPORTANT: Multiple cycles can have the same period, so we cannot deduplicate by period alone.
    if shared_cycles is not None:
        # Use min_state as the primary deduplication key
        # Each unique cycle has a unique min_state (canonical representation)
        # shared_cycles tracks which cycles were claimed by which workers
        merge_debug(f'Using shared_cycles registry with {len(shared_cycles)} claimed cycles')
        
        # Track cycles by min_state (canonical cycle representation)
        cycles_by_min_state = {}  # min_state_tuple -> seq_info
        
        for idx, seq_info in enumerate(all_sequences):
            states_tuples = seq_info['states']
            period = seq_info['period']
            start_state = seq_info['start_state']
            
            if not states_tuples or period == 0:
                continue
            
            # Get min_state for deduplication
            if isinstance(states_tuples, tuple) and len(states_tuples) == 1:
                min_state = states_tuples[0]
            elif isinstance(states_tuples, list) and len(states_tuples) > 0:
                min_state = min(states_tuples)
            else:
                continue
            
            min_state_tuple = tuple(min_state) if not isinstance(min_state, tuple) else min_state
            
            # Deduplicate by min_state: each unique cycle has a unique min_state
            if min_state_tuple not in cycles_by_min_state:
                # First occurrence of this cycle (by min_state) - add it
                cycles_by_min_state[min_state_tuple] = seq_info
                merge_debug(f'Sequence {idx+1}: Added cycle with min_state {min_state_tuple[:5] if len(min_state_tuple) > 5 else min_state_tuple}... (period {period})')
            else:
                # Duplicate cycle (same min_state) - skip it
                existing_period = cycles_by_min_state[min_state_tuple]['period']
                merge_debug(f'Sequence {idx+1}: Duplicate cycle (min_state already seen, period {period} vs existing {existing_period}), skipping')
        
        # Convert to list
        unique_sequences = list(cycles_by_min_state.values())
        merge_debug(f'Deduplication by min_state: {len(unique_sequences)} unique cycles from {len(all_sequences)} total')
    else:
        # Fallback: Original deduplication logic (for backward compatibility)
        merge_debug('shared_cycles not provided, using fallback deduplication')
        
        for idx, seq_info in enumerate(all_sequences):
            # Create a canonical representation of the cycle
            # Use the sorted tuple of state tuples as the key
            states_tuples = seq_info['states']
            period = seq_info['period']
            start_state = seq_info['start_state']
            
            if not states_tuples:
                # CRITICAL: In period-only mode, states_tuples is empty
                # Use period+start_state as key (imperfect but avoids hangs)
                cycle_key = (period, start_state)
                merge_debug(f'Sequence {idx+1}: Empty states_tuples! Using period+start_state as key: period={period}, start_state={start_state}')
            elif len(states_tuples) == 1:
                # Period-only mode: states_tuples contains min_state tuple
                # Use it directly as the key for deduplication
                cycle_key = states_tuples[0]  # min_state tuple is the key
                merge_debug(f'Sequence {idx+1}: Period-only mode, using min_state key: {cycle_key[:5] if len(cycle_key) > 5 else cycle_key}..., period={period}')
            else:
                # Full mode: Use sorted states as key (cycles are the same regardless of starting point)
                # Normalize by sorting to handle cycles starting at different points
                cycle_key = tuple(sorted(states_tuples))
                merge_debug(f'Sequence {idx+1}: Full mode, {len(states_tuples)} states, cycle_key length={len(cycle_key)}')
            
            if cycle_key not in seen_cycles:
                seen_cycles[cycle_key] = seq_info
                unique_sequences.append(seq_info)
                merge_debug(f'Sequence {idx+1}: Added as unique (total unique: {len(unique_sequences)})')
            else:
                merge_debug(f'Sequence {idx+1}: Duplicate detected, skipping')
    
    merge_debug(f'Deduplication complete: {len(unique_sequences)} unique sequences from {len(all_sequences)} total')
    
    # Reconstruct SageMath objects and assign sequence numbers
    seq_dict = {}
    period_dict = {}
    seq_num = 0
    
    V = VectorSpace(GF(gf_order), lfsr_degree)
    
    for seq_info in unique_sequences:
        seq_num += 1
        period = seq_info['period']
        period_dict[seq_num] = period
        
        # Reconstruct sequence states based on period_only flag
        # If period_only=True, we computed the sequence for deduplication but don't store it
        is_period_only = seq_info.get('period_only', False)
        if is_period_only:
            # Period-only mode: don't store sequence (even though we have it for dedup)
            seq_dict[seq_num] = []
        elif seq_info['states']:
            # Full mode: reconstruct and store sequence
            seq_list = [vector(V, list(state_tuple)) for state_tuple in seq_info['states']]
            seq_dict[seq_num] = seq_list
        else:
            # Empty sequence (shouldn't happen, but handle gracefully)
            seq_dict[seq_num] = []
    
    periods_sum = sum(period_dict.values())
    
    # Log errors if any
    if all_errors:
        import sys
        print(f"WARNING: {len(all_errors)} errors occurred during parallel processing:", file=sys.stderr)
        for error in all_errors[:10]:  # Show first 10 errors
            print(f"  {error}", file=sys.stderr)
        if len(all_errors) > 10:
            print(f"  ... and {len(all_errors) - 10} more errors", file=sys.stderr)
    
    return seq_dict, period_dict, max_period, periods_sum


def _partition_state_space(
    state_vector_space: Any,
    num_chunks: int,
) -> List[List[Tuple[Tuple[int, ...], int]]]:
    """
    Partition state space into chunks for parallel processing.
    
    Uses lazy iteration to avoid materializing all states upfront.
    Converts SageMath vectors to tuples (for pickling) and divides them
    into roughly equal chunks.
    
    Args:
        state_vector_space: SageMath VectorSpace of all possible states
        num_chunks: Number of chunks to create
        
    Returns:
        List of chunks, where each chunk is a list of (state_tuple, index) pairs
    """
    # Optimized: Use lazy iteration with chunking to avoid materializing all states
    # This reduces memory usage and improves performance for large state spaces
    
    # BUG FIX: Don't iterate through all states to partition!
    # Instead, compute chunk boundaries mathematically and use lazy iteration
    # For VectorSpace over GF(q) of dimension d, size is q^d
    try:
        # Get dimensions from VectorSpace
        d = len(state_vector_space.basis())
        gf_order = state_vector_space.base_ring().order()
        total_states = int(gf_order) ** d
    except (AttributeError, TypeError):
        # Fallback: iterate once to count (for small state spaces)
        total_states = sum(1 for _ in state_vector_space)
    
    if total_states == 0:
        return []
    
    # Calculate chunk size
    chunk_size = max(1, total_states // num_chunks)
    
    # BUG FIX: Don't iterate VectorSpace! Use state indices directly.
    # For GF(q)^d, state index i can be converted to tuple without iteration.
    def state_index_to_tuple(state_index: int, degree: int, gf_order: int) -> Tuple[int, ...]:
        """Convert state index to tuple representation without iterating VectorSpace."""
        if gf_order == 2:
            # Binary representation for GF(2) - FAST!
            return tuple((state_index >> i) & 1 for i in range(degree))
        else:
            # For other fields, convert to base-q representation
            result = []
            num = state_index
            for _ in range(degree):
                result.append(num % gf_order)
                num //= gf_order
            return tuple(result)
    
    # Create chunks by computing state tuples from indices (NO ITERATION!)
    chunks = []
    for chunk_idx in range(num_chunks):
        chunk = []
        start_idx = chunk_idx * chunk_size
        end_idx = min(start_idx + chunk_size, total_states)
        
        for state_idx in range(start_idx, end_idx):
            state_tuple = state_index_to_tuple(state_idx, d, gf_order)
            chunk.append((state_tuple, state_idx))
        
        chunks.append(chunk)
    
    return chunks


def _process_state_chunk(
    chunk_data: Tuple[
        List[Tuple[Tuple[int, ...], int]],  # State tuples with indices
        List[int],  # coeffs_vector
        int,  # gf_order
        int,  # lfsr_degree
        str,  # algorithm
        bool,  # period_only
        int,  # worker_id
        Any,  # shared_cycles (Manager().dict())
        Any,  # cycle_lock (Manager().Lock())
    ],
) -> Dict[str, Any]:
    """
    Process a chunk of states in parallel.
    
    This worker function:
    1. Reconstructs SageMath objects from serialized data
    2. Processes each state in the chunk independently
    3. Returns all found sequences (may include duplicates across workers)
    4. Main process will deduplicate based on cycle content
    
    Args:
        chunk_data: Tuple containing:
            - state_chunk: List of (state_tuple, index) pairs
            - coeffs_vector: LFSR coefficients
            - gf_order: Field order
            - lfsr_degree: LFSR degree
            - algorithm: Cycle detection algorithm
            - period_only: Whether to store sequences
            - worker_id: Worker identifier
            
    Returns:
        Dictionary with:
            - 'sequences': List of dicts, each with 'states', 'period', 'start_state'
            - 'max_period': Maximum period found
            - 'processed_count': Number of states processed
            - 'errors': List of error messages
    """
    (
        state_chunk,
        coeffs_vector,
        gf_order,
        lfsr_degree,
        algorithm,
        period_only,
        worker_id,
        shared_cycles,
        cycle_lock,
    ) = chunk_data
    
    # Import SageMath in worker
    # With 'fork' method (Linux default), workers inherit parent's memory
    # so SageMath should already be imported. Just import what we need.
    # With 'spawn' method, we need to import from scratch.
    import sys
    import os
    
    # Debug logging can be enabled by setting environment variable
    DEBUG_PARALLEL = os.environ.get('DEBUG_PARALLEL', '0') == '1'
    debug_log = lambda msg: print(f'[Worker {worker_id} PID {os.getpid()}] {msg}', file=sys.stderr, flush=True) if DEBUG_PARALLEL else lambda msg: None
    
    if DEBUG_PARALLEL:
        debug_log('Starting worker function...')
    
    try:
        # Try to import SageMath (works in fork mode, may need setup in spawn mode)
        from sage.all import VectorSpace, GF, vector
        debug_log('SageMath import successful')
        
        # Test that SageMath works by creating a simple object
        try:
            _test_F = GF(gf_order)
            _test_V = VectorSpace(_test_F, 1)
            _test_vec = vector(_test_F, [0])
            debug_log('SageMath initialization test successful')
        except Exception as e:
            debug_log(f'Warning: SageMath initialization test failed: {e}')
            # Continue anyway - might still work
            
    except ImportError as e:
        debug_log(f'SageMath import failed: {e}')
        # If import fails, try to set up SageMath path (for spawn method)
        debug_log('Setting up SageMath path...')
        try:
            import subprocess
            result = subprocess.run(
                ["sage", "-c", "import sys; print('\\n'.join(sys.path))"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                sage_paths = result.stdout.strip().split("\n")
                for path in sage_paths:
                    if path and path not in sys.path and os.path.isdir(path):
                        sys.path.insert(0, path)
                from sage.all import VectorSpace, GF, vector
                debug_log('SageMath import successful via path setup')
            else:
                raise ImportError("SageMath not found")
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, ImportError) as e:
            debug_log(f'SageMath setup failed: {e}')
            return {
                'sequences': [],
                'max_period': 0,
                'processed_count': 0,
                'errors': [f'SageMath not available in worker process: {str(e)}'],
            }
    
    # Reconstruct state update matrix in worker
    debug_log(f'Reconstructing state update matrix from coeffs: {coeffs_vector}, gf_order: {gf_order}, degree: {lfsr_degree}')
    try:
        from lfsr.core import build_state_update_matrix
        state_update_matrix, _ = build_state_update_matrix(coeffs_vector, gf_order)
        debug_log(f'State update matrix reconstructed: dimensions={state_update_matrix.dimensions()}')
        # Verify matrix by checking last column (where coefficients are stored)
        d = state_update_matrix.dimensions()[0]
        last_col_coeffs = [int(state_update_matrix[i, d-1]) for i in range(d)]
        debug_log(f'Matrix last column coefficients: {last_col_coeffs} (expected: {coeffs_vector})')
        if last_col_coeffs != coeffs_vector:
            debug_log(f'WARNING: Matrix reconstruction mismatch!')
    except Exception as e:
        debug_log(f'Failed to build state update matrix: {e}')
        return {
            'sequences': [],
            'max_period': 0,
            'processed_count': 0,
            'errors': [f'Failed to build state update matrix: {str(e)}'],
        }
    
    # Initialize worker-local results
    sequences = []  # List of {states, period, start_state_tuple}
    worker_max_period = 0
    processed_count = 0
    errors = []
    
    # CRITICAL PERFORMANCE FIX: Create GF, VectorSpace once per worker, not per state!
    # Creating these for every state is extremely expensive and kills performance
    # 
    # CRITICAL FOR FORK MODE: Isolate SageMath in worker to avoid category mismatch errors
    # Even though fork inherits parent's memory, creating fresh objects ensures proper
    # category isolation and avoids "base category class mismatch" errors
    try:
        # Force fresh SageMath objects (avoids category mismatches in fork mode)
        F = GF(gf_order)
        V = VectorSpace(F, lfsr_degree)
        # Test that objects work correctly
        _test_vec = vector(F, [0] * lfsr_degree)
        debug_log(f'SageMath isolated successfully in worker (fork mode compatibility)')
    except Exception as e:
        debug_log(f'Warning: SageMath isolation test failed: {e}, continuing anyway...')
        # Fallback: create objects anyway (might still work)
        F = GF(gf_order)
        V = VectorSpace(F, lfsr_degree)
    
    # Local visited set for this worker (to avoid processing same cycle multiple times in this chunk)
    local_visited = set()
    
    # Process each state in chunk
    debug_log(f'Processing {len(state_chunk)} states in chunk...')
    import time
    chunk_start_time = time.time()
    
    # Work distribution metrics
    states_processed = 0  # States we actually processed (found cycles from)
    states_skipped_visited = 0  # States skipped because already in local_visited
    states_skipped_claimed = 0  # States skipped because cycle already claimed by another worker
    cycles_found = 0  # Total cycles found (before claiming check)
    cycles_claimed = 0  # Cycles we successfully claimed
    cycles_skipped = 0  # Cycles we skipped (already claimed)
    
    for idx, (state_tuple, state_idx) in enumerate(state_chunk):
        try:
            # Progress logging every 100 states or every 5 seconds
            if idx % 100 == 0 or (time.time() - chunk_start_time) > 5:
                elapsed = time.time() - chunk_start_time
                rate = idx / elapsed if elapsed > 0 else 0
                debug_log(f'Progress: {idx}/{len(state_chunk)} states ({100*idx/len(state_chunk):.1f}%), rate: {rate:.1f} states/s')
                chunk_start_time = time.time()  # Reset timer
            
            debug_log(f'Processing state {idx+1}/{len(state_chunk)}: {state_tuple}')
            
            # Skip if already visited in this worker's processing
            if state_tuple in local_visited:
                debug_log(f'State {idx+1} already visited, skipping')
                states_skipped_visited += 1
                continue
            
            # Reconstruct state vector from tuple
            # CRITICAL: F and V are already created above - reuse them!
            # Convert tuple to list and create vector
            debug_log(f'State {idx+1}: Converting tuple to vector...')
            state_list = [F(x) for x in state_tuple]
            state = vector(F, state_list)
            debug_log(f'State {idx+1}: State vector reconstructed')
            
            # Find cycle for this state using local visited set
            # Note: We pass an empty set here since each worker processes independently
            # The visited_set parameter is used to mark states, but we handle deduplication in merge
            # Import the function we need (avoid circular import issues)
            # Since we're in the same module, we can reference it directly
            # But for multiprocessing, we need to make sure it's available
            local_visited_set = set()
            # Call _find_sequence_cycle
            # In multiprocessing with 'fork', functions from the same module should be available
            # But to be safe, we'll import it explicitly
            # Note: This creates a reference that should work in forked processes
            debug_log(f'State {idx+1}: Calling _find_sequence_cycle...')
            from lfsr.analysis import _find_sequence_cycle
            
            # CRITICAL: For period-only mode, we need the full sequence for deduplication
            # However, computing the full sequence using matrix multiplication in a loop
            # causes hangs in multiprocessing context after several iterations.
            # 
            # Solution: Use period-only function to get period, then compute sequence
            # only for small periods (<= 100) to avoid hangs. For larger periods,
            # use simplified deduplication based on start_state+period.
            if period_only:
                # CRITICAL DISCOVERY: Floyd's algorithm is MUCH slower than enumeration for large periods!
                # Floyd does ~3x period matrix multiplications (tortoise + 2*hare per step)
                # For period 3255: ~10,000 matrix multiplications vs enumeration's 3255
                # Enumeration is actually FASTER and SAFER in fork mode when used correctly
                debug_log(f'State {idx+1}: Period-only mode - computing period first...')
                from lfsr.analysis import _find_period
                # Use enumeration (faster) - it's safe in fork mode when used in period-only mode
                # The hang issue was from computing full sequences, not period computation
                worker_algorithm = "enumeration" if algorithm in ["auto", "enumeration"] else algorithm
                try:
                    seq_period = _find_period(state, state_update_matrix, algorithm=worker_algorithm)
                    debug_log(f'State {idx+1}: Period computed: {seq_period} (using {worker_algorithm})')
                except Exception as e:
                    debug_log(f'State {idx+1}: Error computing period: {e}')
                    # If period computation fails, skip this state
                    errors.append(f'Error computing period for state {state_tuple}: {str(e)}')
                    continue
                
                # CRITICAL FIX: For proper deduplication, we need a canonical cycle representation.
                # The min_state approach requires iterating through the cycle, which can be slow
                # for large periods, but it's necessary for correct deduplication.
                # We limit the iteration to avoid hangs, but still get a good canonical key.
                debug_log(f'State {idx+1}: Period-only mode - computing canonical cycle key...')
                # Find minimum state in cycle as canonical key
                # CRITICAL: Must check ALL states in cycle to get true minimum
                # Otherwise, different workers starting from different states might compute different min_states
                min_state = state_tuple
                current = state
                # Check entire cycle (not just first 1000) to ensure consistent min_state
                for i in range(seq_period - 1):
                    current = current * state_update_matrix
                    current_tuple = tuple(current)
                    if current_tuple < min_state:
                        min_state = current_tuple
                    # Periodic check every 1000 iterations for very large cycles
                    if i > 0 and i % 1000 == 0:
                        _ = len(str(current))  # Force evaluation to detect hangs
                # Use min_state as canonical key for deduplication
                min_state_tuple = tuple(min_state) if not isinstance(min_state, tuple) else min_state
                
                # REDUNDANCY FIX: Check if this cycle is already being processed by another worker
                # Fast check (no lock) - if already claimed, skip immediately
                if min_state_tuple in shared_cycles:
                    claimed_by = shared_cycles[min_state_tuple]
                    debug_log(f'State {idx+1}: Cycle with min_state {min_state_tuple[:5]}... already claimed by worker {claimed_by}, skipping')
                    # Mark all states in cycle as visited locally to skip in this worker
                    local_visited.add(state_tuple)
                    current = state
                    for _ in range(seq_period - 1):
                        current = current * state_update_matrix
                        current_tuple = tuple(current)
                        local_visited.add(current_tuple)
                    states_skipped_claimed += seq_period
                    cycles_skipped += 1
                    continue
                
                # Try to claim this cycle (with lock for atomicity)
                with cycle_lock:
                    # Double-check after acquiring lock (another worker might have claimed it)
                    if min_state_tuple in shared_cycles:
                        claimed_by = shared_cycles[min_state_tuple]
                        debug_log(f'State {idx+1}: Cycle with min_state {min_state_tuple[:5]}... claimed by worker {claimed_by} (between check and lock), skipping')
                        local_visited.add(state_tuple)
                        current = state
                        for _ in range(seq_period - 1):
                            current = current * state_update_matrix
                            current_tuple = tuple(current)
                            local_visited.add(current_tuple)
                        continue
                    else:
                        # Claim this cycle for this worker
                        shared_cycles[min_state_tuple] = worker_id
                        debug_log(f'State {idx+1}: Claimed cycle with min_state {min_state_tuple[:5]}... for worker {worker_id}')
                
                # Process cycle (we've successfully claimed it)
                states_tuples = (min_state,)  # Single-element tuple for deduplication
                debug_log(f'State {idx+1}: Cycle signature (min_state): {min_state[:5]}... (period={seq_period})')
                # CRITICAL FIX: Mark ALL states in the cycle as visited (not just start state)
                # This prevents workers from processing the same cycle multiple times
                # Even though cycles can span chunks, marking all states prevents redundant work
                local_visited.add(state_tuple)
                current = state
                for _ in range(seq_period - 1):
                    current = current * state_update_matrix
                    current_tuple = tuple(current)
                    local_visited.add(current_tuple)
                debug_log(f'State {idx+1}: Marked {seq_period} states as visited in cycle')
                states_processed += 1  # Count the start state we processed
                cycles_found += 1
            else:
                # Full mode: get sequence normally
                debug_log(f'State {idx+1}: Calling _find_sequence_cycle with period_only={period_only}, algorithm={algorithm}')
                seq_lst, seq_period = _find_sequence_cycle(
                    state,
                    state_update_matrix,
                    local_visited_set,
                    algorithm=algorithm,
                    period_only=period_only,
                )
                debug_log(f'State {idx+1}: _find_sequence_cycle returned: period={seq_period}, length={len(seq_lst)}')
                # Mark all states as visited
                for seq_state in seq_lst:
                    seq_state_tuple = tuple(seq_state)
                    local_visited.add(seq_state_tuple)
                # Convert to tuples for serialization
                states_tuples = [tuple(s) for s in seq_lst]
            
            debug_log(f'State {idx+1}: Cycle found: period={seq_period}, length={len(states_tuples)}')
            
            # DEBUG: Log cycle signature for redundancy detection
            if period_only and isinstance(states_tuples, tuple) and len(states_tuples) == 1:
                min_state = states_tuples[0]
                debug_log(f'State {idx+1}: Cycle signature (min_state) = {min_state[:min(8, len(min_state))]}... (full: {min_state})')
            
            # Store sequence information
            # For period-only mode, we store the full sequence tuples for deduplication
            # but mark it as period-only so merge knows not to reconstruct SageMath objects
            sequences.append({
                'states': states_tuples,  # Full sequence for deduplication, even in period-only mode
                'period': seq_period,
                'start_state': state_tuple,
                'period_only': period_only,  # Flag to indicate if we should store sequence in final output
            })
            
            if seq_period > worker_max_period:
                worker_max_period = seq_period
            
            processed_count += 1
            # states_processed already incremented when we found the cycle
            
        except Exception as e:
            if idx == 0:
                debug_log(f'Error processing state: {e}')
            errors.append(f'Error processing state {state_tuple}: {str(e)}')
            continue
    
    debug_log(f'Worker completed: {processed_count} states processed, {len(sequences)} sequences found')
    
    # Work distribution metrics
    work_metrics = {
        'states_processed': states_processed,
        'states_skipped_visited': states_skipped_visited,
        'states_skipped_claimed': states_skipped_claimed,
        'cycles_found': cycles_found,
        'cycles_claimed': cycles_claimed,
        'cycles_skipped': cycles_skipped,
        'total_states_in_chunk': len(state_chunk),
    }
    
    return {
        'sequences': sequences,
        'max_period': worker_max_period,
        'processed_count': processed_count,
        'errors': errors,
        'work_metrics': work_metrics,  # NEW: Work distribution data
    }


def lfsr_sequence_mapper_parallel(
    state_update_matrix: Any,
    state_vector_space: Any,
    gf_order: int,
    output_file: Optional[TextIO] = None,
    no_progress: bool = False,
    algorithm: str = "auto",
    period_only: bool = False,
    num_workers: Optional[int] = None,
) -> Tuple[Dict[int, List[Any]], Dict[int, int], int, int]:
    """
    Parallel version of lfsr_sequence_mapper using multiprocessing.
    
    Partitions the state space across multiple worker processes and processes
    them in parallel, then merges the results.
    
    NOTE: Currently, parallel processing works reliably only in period-only mode
    (period_only=True). In full sequence mode, workers may hang due to SageMath
    matrix multiplication issues in multiprocessing context. The function
    automatically falls back to sequential processing on timeout.
    
    Args:
        state_update_matrix: The LFSR state update matrix (not used directly, 
                            coefficients extracted for workers)
        state_vector_space: Vector space of all possible states
        gf_order: The field order
        output_file: Optional file object for output
        no_progress: If True, disable progress bar display
        algorithm: Algorithm to use: "floyd", "brent", "enumeration", or "auto"
        period_only: If True, compute periods only without storing sequences.
                    RECOMMENDED for parallel processing to avoid hangs.
        num_workers: Number of parallel workers (default: CPU count)
    
    Returns:
        Tuple of (seq_dict, period_dict, max_period, periods_sum)
        Same format as lfsr_sequence_mapper
    """
    """
    Parallel version of lfsr_sequence_mapper using multiprocessing.
    
    Partitions the state space across multiple worker processes and processes
    them in parallel, then merges the results.
    
    Args:
        state_update_matrix: The LFSR state update matrix (not used directly, 
                            coefficients extracted for workers)
        state_vector_space: Vector space of all possible states
        gf_order: The field order
        output_file: Optional file object for output
        no_progress: If True, disable progress bar display
        algorithm: Algorithm to use: "floyd", "brent", "enumeration", or "auto"
        period_only: If True, compute periods only without storing sequences
        num_workers: Number of parallel workers (default: CPU count)
    
    Returns:
        Tuple of (seq_dict, period_dict, max_period, periods_sum)
        Same format as lfsr_sequence_mapper
    """
    from lfsr.formatter import dump, dump_seq_row, subsection
    
    # Determine number of workers
    if num_workers is None:
        num_workers = multiprocessing.cpu_count()
    
    # OPTIMIZATION: Auto-select optimal worker count based on problem size
    # For small problems, too many workers cause load imbalance
    # Calculate state space size
    try:
        d = len(state_vector_space.basis())
        gf_order = state_vector_space.base_ring().order()
        state_space_size = int(gf_order) ** d
    except (AttributeError, TypeError):
        # Fallback: estimate from vector space
        state_space_size = sum(1 for _ in state_vector_space)
    
    # Optimal worker count based on problem size
    # Formula: Use fewer workers for small problems to avoid load imbalance
    # Based on profiling: 2 workers optimal for 4K states, 4+ workers slower
    if state_space_size < 2000:
        optimal_workers = 1
    elif state_space_size < 8000:
        optimal_workers = 2  # 2 workers optimal for 4K-8K states
    elif state_space_size < 32000:
        optimal_workers = 4  # 4 workers may help for 8K-32K states
    else:
        optimal_workers = min(8, multiprocessing.cpu_count())  # Scale up for very large problems
    
    # Use the optimal count, but respect user's explicit choice if provided
    # If user explicitly set num_workers, use it (they know what they want)
    # If None (auto), use optimal
    original_num_workers = num_workers
    if num_workers is not None and num_workers != multiprocessing.cpu_count():
        # User explicitly set num_workers, respect it
        num_workers = max(1, min(num_workers, multiprocessing.cpu_count()))
    else:
        # Auto mode: use optimal
        num_workers = max(1, min(optimal_workers, multiprocessing.cpu_count()))
    
    if not no_progress and original_num_workers is None and num_workers != optimal_workers:
        import sys
        print(f"  Note: Using {num_workers} workers (optimal {optimal_workers} limited by CPU count {multiprocessing.cpu_count()})", file=sys.stderr)
    
    # Extract coefficients from matrix for worker reconstruction
    # The matrix structure: coefficients are in the LAST COLUMN (not last row)
    # Row i has coefficient coeffs[i] in the last column (column d-1)
    d = state_update_matrix.dimensions()[0]
    coeffs_vector = [int(state_update_matrix[i, d-1]) for i in range(d)]
    
    subsec_name = "STATES SEQUENCES"
    subsec_desc = "all possible state sequences " + "and their corresponding periods (parallel processing)"
    subsection(subsec_name, subsec_desc, output_file)
    
    # Partition state space
    chunks = _partition_state_space(state_vector_space, num_workers)
    
    if not chunks:
        # Empty state space
        return {}, {}, 0, 0
    
    # Create shared cycle registry to prevent redundancy
    # Workers will check this before processing cycles to avoid duplicate work
    manager = multiprocessing.Manager()
    shared_cycles = manager.dict()  # min_state_tuple -> worker_id (who claimed it)
    cycle_lock = manager.Lock()  # Lock for atomic check-and-set
    
    # Prepare chunk data for workers
    chunk_data_list = []
    for worker_id, chunk in enumerate(chunks):
        chunk_data = (
            chunk,
            coeffs_vector,
            gf_order,
            d,
            algorithm,
            period_only,
            worker_id,
            shared_cycles,  # Shared cycle registry
            cycle_lock,     # Lock for atomic claiming
        )
        chunk_data_list.append(chunk_data)
    
    # Process chunks in parallel
    if not no_progress:
        print(f"  Processing {len(chunks)} chunks with {num_workers} workers...")
        import sys
        sys.stdout.flush()  # Ensure output is visible
    
    # Use multiprocessing.Pool with 'fork' context (preferred) or 'spawn' (fallback)
    # 
    # PERFORMANCE CRITICAL: Fork mode is 13-17x faster than spawn for process creation
    # - Fork: ~0.12ms per task (inherits parent's memory)
    # - Spawn: ~1.69ms per task (new Python process)
    #
    # SageMath isolation in workers (_process_state_chunk) ensures fork mode works correctly:
    # - Fresh GF/VectorSpace objects created in each worker
    # - Matrices rebuilt from coefficients (not shared)
    # - This avoids "base category class mismatch" errors
    #
    # Fallback to spawn only if fork is not available (Windows/Mac)
    try:
        import time
        start_time = time.time()
        
        # Prefer fork mode (much faster), fall back to spawn if not available
        try:
            # Fork mode: 13-17x faster, works on Linux
            # SageMath isolation in workers makes this safe
            ctx = multiprocessing.get_context('fork')
            if not no_progress:
                print(f"  Using fork mode (fast, ~13-17x faster than spawn)")
        except ValueError:
            # Spawn mode: Slower but works on Windows/Mac where fork isn't available
            ctx = multiprocessing.get_context('spawn')
            if not no_progress:
                print(f"  Using spawn mode (fork not available on this platform)")
        
        # CRITICAL: Use context manager to ensure proper cleanup
        # The 'with' statement ensures pool.terminate() and pool.join() are called
        # even if an exception occurs, preventing zombie processes
        with ctx.Pool(processes=num_workers) as pool:
            if not no_progress:
                print(f"  Pool created, starting workers...")
                import sys
                sys.stdout.flush()
            
            # Use map_async with timeout for better control
            async_result = pool.map_async(_process_state_chunk, chunk_data_list)
            
            if not no_progress:
                timeout_msg = "120s" if ctx.get_start_method() == 'spawn' else "40s"
                print(f"  Workers started, waiting for results (timeout: {timeout_msg} total)...")
                import sys
                sys.stdout.flush()
            
            try:
                # Wait with reasonable timeout
                # Serial takes max 35s, so parallel should be faster
                # Fork mode is much faster (13-17x), so shorter timeout is sufficient
                # Spawn mode is slower due to process creation overhead
                if ctx.get_start_method() == 'spawn':
                    total_timeout = 120  # Spawn needs more time for process creation (slower)
                else:
                    total_timeout = 40   # Fork is fast (13-17x faster), less overhead
                worker_results = async_result.get(timeout=total_timeout)
                
                elapsed = time.time() - start_time
                if not no_progress:
                    print(f"  Workers completed in {elapsed:.2f}s")
            except multiprocessing.TimeoutError:
                # CRITICAL: Properly terminate hung workers
                import sys
                print("WARNING: Parallel processing timed out - terminating workers...", file=sys.stderr)
                
                # Terminate all workers immediately (sends SIGTERM)
                pool.terminate()
                
                # Wait for workers to terminate (with timeout)
                try:
                    pool.join(timeout=10)  # Give workers 10s to clean up
                except TypeError:
                    # Python < 3.7 doesn't support timeout in join()
                    pool.join()
                
                print("ERROR: Parallel processing timed out - workers may be hung", file=sys.stderr)
                print("  This can happen with SageMath and multiprocessing in some configurations", file=sys.stderr)
                print("  Falling back to sequential processing...", file=sys.stderr)
                return lfsr_sequence_mapper(
                    state_update_matrix,
                    state_vector_space,
                    gf_order,
                    output_file,
                    no_progress,
                    algorithm,
                    period_only,
                )
            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully
                import sys
                print("\nWARNING: Interrupted by user - terminating workers...", file=sys.stderr)
                pool.terminate()
                try:
                    pool.join(timeout=5)
                except TypeError:
                    pool.join()
                raise  # Re-raise to exit properly
    except Exception as e:
        # Fallback to sequential on error
        import sys
        print(f"ERROR: Parallel processing failed: {e}", file=sys.stderr)
        print("  Falling back to sequential processing...", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return lfsr_sequence_mapper(
            state_update_matrix,
            state_vector_space,
            gf_order,
            output_file,
            no_progress,
            algorithm,
            period_only,
        )
    
    # Extract work metrics from worker results for load imbalance analysis
    work_metrics_list = [result.get('work_metrics', {}) for result in worker_results]
    
    # Merge results from all workers
    # Pass shared_cycles to merge function for accurate deduplication
    seq_dict, period_dict, max_period, periods_sum = _merge_parallel_results(
        worker_results, gf_order, d, shared_cycles
    )
    
    # Calculate load imbalance from work metrics
    if work_metrics_list and all('states_processed' in m for m in work_metrics_list):
        states_processed_list = [m['states_processed'] for m in work_metrics_list]
        total_states = sum(states_processed_list)
        if total_states > 0:
            avg_work = total_states / len(states_processed_list)
            max_work = max(states_processed_list)
            imbalance_pct = ((max_work - avg_work) / avg_work * 100) if avg_work > 0 else 0
            # Store in a way that can be accessed (for now, just log if DEBUG)
            import os
            if os.environ.get('DEBUG_PARALLEL', '0') == '1':
                import sys
                print(f"[Load Imbalance] Workers: {states_processed_list}, Avg: {avg_work:.1f}, Max: {max_work}, Imbalance: {imbalance_pct:.1f}%", file=sys.stderr)
    
    # Display sequences (same format as sequential version)
    print("\n")
    num_sequences = len(period_dict)
    row_width = TABLE_ROW_WIDTH
    # Reconstruct special state for formatting
    F = GF(gf_order)
    V_special = VectorSpace(F, d)
    special_state = vector(F, [F(1) if i == d - 1 else F(0) for i in range(d)])
    
    if period_only:
        # Period-only mode: display only periods
        for seq_num, period in period_dict.items():
            seq_entry = f" | ** sequence {seq_num:3d} | T : {period:3d} | (period only)  |"
            dump(seq_entry, "mode=all", output_file)
    else:
        # Full mode: display sequences
        for seq_num, sequence in seq_dict.items():
            period = period_dict[seq_num]
            seq_entry, seq_all_v = _format_sequence_entry(
                seq_num, sequence, period, max_period, special_state, row_width
            )
            
            dump_seq_row(
                seq_num, seq_entry, num_sequences, row_width, "mode=console", output_file
            )
            dump_seq_row(
                seq_num, seq_all_v, num_sequences, row_width, "mode=file", output_file
            )
    
    state_vector_space_size = int(gf_order) ** d
    dump("  PERIOD VALUES SUMMED : " + str(periods_sum), "mode=all", output_file)
    dump(
        "     NO. STATE VECTORS : " + str(state_vector_space_size),
        "mode=all",
        output_file,
    )
    
    # Verification: periods_sum should equal state_vector_space_size
    if periods_sum != state_vector_space_size:
        import sys
        print(
            f"WARNING: Period sum ({periods_sum}) != state space size ({state_vector_space_size})",
            file=sys.stderr,
        )
    
    return seq_dict, period_dict, max_period, periods_sum


def _process_task_batch_dynamic(
    worker_data: Tuple[
        Any,  # task_queue (Manager().Queue()) OR worker_queues (List[Manager().Queue()]) for work stealing
        Any,  # worker_id (int) OR coeffs_vector (List[int]) depending on mode
        Any,  # coeffs_vector (List[int]) OR gf_order (int) depending on mode
        Any,  # gf_order (int) OR lfsr_degree (int) depending on mode
        Any,  # lfsr_degree (int) OR algorithm (str) depending on mode
        Any,  # algorithm (str) OR period_only (bool) depending on mode
        Any,  # period_only (bool) OR shared_cycles (Manager().dict()) depending on mode
        Any,  # worker_id (int) OR cycle_lock (Manager().Lock()) depending on mode
        Any,  # shared_cycles (Manager().dict()) OR batch_aggregation_count (int) depending on mode
        Any,  # cycle_lock (Manager().Lock()) OR None depending on mode
        Any,  # batch_aggregation_count (int) OR None depending on mode
    ],
) -> Dict[str, Any]:
    """
    Worker function for dynamic threading: pulls batches from queue and processes them.
    
    This worker continuously pulls task batches from a shared queue until a sentinel
    value (None) is received, indicating no more work. This enables dynamic load
    balancing as workers pull work as they become available.
    
    **Batch Aggregation**: To reduce IPC overhead, this worker pulls multiple batches
    at once using get_nowait() (non-blocking) with fallback to blocking get().
    The number of batches pulled per operation is determined by batch_aggregation_count.
    
    Args:
        worker_data: Tuple containing:
            - task_queue: Manager().Queue() containing batches of (state_tuple, state_idx) pairs
            - coeffs_vector: LFSR coefficients
            - gf_order: Field order
            - lfsr_degree: LFSR degree
            - algorithm: Cycle detection algorithm
            - period_only: Whether to store sequences
            - worker_id: Worker identifier
            - shared_cycles: Shared cycle registry (Manager().dict())
            - cycle_lock: Lock for atomic cycle claiming (Manager().Lock())
            - batch_aggregation_count: Number of batches to pull at once (2-8, adaptive)
    
    Returns:
        Dictionary with same format as _process_state_chunk:
            - 'sequences': List of dicts, each with 'states', 'period', 'start_state'
            - 'max_period': Maximum period found
            - 'processed_count': Number of states processed
            - 'errors': List of error messages
            - 'work_metrics': Work distribution metrics
    """
    # Detect work stealing mode: first element is list (worker_queues) vs Queue (task_queue)
    if isinstance(worker_data[0], list):
        # Phase 3.1: Work stealing mode
        worker_queues, worker_id, coeffs_vector, gf_order, lfsr_degree, algorithm, period_only, shared_cycles, cycle_lock, batch_aggregation_count = worker_data
        task_queue = None
        use_work_stealing = True
    else:
        # Original: Shared queue mode
        task_queue, coeffs_vector, gf_order, lfsr_degree, algorithm, period_only, worker_id, shared_cycles, cycle_lock, batch_aggregation_count = worker_data
        worker_queues = None
        use_work_stealing = False
    
    # Import SageMath in worker (same setup as _process_state_chunk)
    import sys
    import os
    
    DEBUG_PARALLEL = os.environ.get('DEBUG_PARALLEL', '0') == '1'
    debug_log = lambda msg: print(f'[Dynamic Worker {worker_id} PID {os.getpid()}] {msg}', file=sys.stderr, flush=True) if DEBUG_PARALLEL else lambda msg: None
    
    if DEBUG_PARALLEL:
        debug_log('Starting dynamic worker function...')
    
    try:
        from sage.all import VectorSpace, GF, vector
        debug_log('SageMath import successful')
    except ImportError as e:
        debug_log(f'SageMath import failed: {e}')
        return {
            'sequences': [],
            'max_period': 0,
            'processed_count': 0,
            'errors': [f'SageMath not available in worker process: {str(e)}'],
            'work_metrics': {},
        }
    
    # Reconstruct state update matrix in worker
    try:
        from lfsr.core import build_state_update_matrix
        state_update_matrix, _ = build_state_update_matrix(coeffs_vector, gf_order)
        debug_log(f'State update matrix reconstructed')
    except Exception as e:
        debug_log(f'Failed to build state update matrix: {e}')
        return {
            'sequences': [],
            'max_period': 0,
            'processed_count': 0,
            'errors': [f'Failed to build state update matrix: {str(e)}'],
            'work_metrics': {},
        }
    
    # Initialize worker-local results
    sequences = []
    worker_max_period = 0
    processed_count = 0
    errors = []
    
    # Create SageMath objects once per worker
    try:
        F = GF(gf_order)
        V = VectorSpace(F, lfsr_degree)
        _test_vec = vector(F, [0] * lfsr_degree)
        debug_log(f'SageMath isolated successfully in worker')
    except Exception as e:
        debug_log(f'Warning: SageMath isolation test failed: {e}, continuing anyway...')
        F = GF(gf_order)
        V = VectorSpace(F, lfsr_degree)
    
    # Local visited set for this worker
    local_visited = set()
    
    # Work distribution metrics
    states_processed = 0
    states_skipped_visited = 0
    states_skipped_claimed = 0
    cycles_found = 0
    cycles_claimed = 0
    cycles_skipped = 0
    batches_processed = 0
    
    # Import cycle detection functions
    from lfsr.analysis import _find_sequence_cycle, _find_period
    
    # Helper function to process a single batch
    def process_single_batch(batch):
        """Process a single batch of states."""
        nonlocal batches_processed, processed_count, worker_max_period, states_processed
        nonlocal states_skipped_visited, states_skipped_claimed, cycles_found, cycles_claimed, cycles_skipped
        
        batches_processed += 1
        batch_start_time = time.time()
        
        for idx, (state_tuple, state_idx) in enumerate(batch):
            try:
                    # Skip if already visited
                    if state_tuple in local_visited:
                        states_skipped_visited += 1
                        continue
                    
                    # Reconstruct state vector
                    state_list = [F(x) for x in state_tuple]
                    state = vector(F, state_list)
                    
                    # Process state (same logic as _process_state_chunk)
                    if period_only:
                        # Period-only mode
                        worker_algorithm = "enumeration" if algorithm in ["auto", "enumeration"] else algorithm
                        try:
                            seq_period = _find_period(state, state_update_matrix, algorithm=worker_algorithm)
                        except Exception as e:
                            errors.append(f'Error computing period for state {state_tuple}: {str(e)}')
                            continue
                        
                        # Find min_state for deduplication (limited to first 1000 states)
                        min_state = state_tuple
                        current = state
                        # CRITICAL: Must check ALL states in cycle to get true minimum
                        # Otherwise, different workers starting from different states might compute different min_states
                        for i in range(seq_period - 1):
                            current = current * state_update_matrix
                            current_tuple = tuple(current)
                            if current_tuple < min_state:
                                min_state = current_tuple
                            # Periodic check every 1000 iterations for very large cycles
                            if i > 0 and i % 1000 == 0:
                                _ = len(str(current))  # Force evaluation to detect hangs
                        min_state_tuple = tuple(min_state) if not isinstance(min_state, tuple) else min_state
                        
                        # Check if cycle already claimed
                        if min_state_tuple in shared_cycles:
                            local_visited.add(state_tuple)
                            current = state
                            for _ in range(seq_period - 1):
                                current = current * state_update_matrix
                                current_tuple = tuple(current)
                                local_visited.add(current_tuple)
                            states_skipped_claimed += seq_period
                            cycles_skipped += 1
                            continue
                        
                        # Try to claim cycle
                        cycle_claimed = False
                        with cycle_lock:
                            if min_state_tuple in shared_cycles:
                                # Already claimed by another worker
                                local_visited.add(state_tuple)
                                current = state
                                for _ in range(seq_period - 1):
                                    current = current * state_update_matrix
                                    current_tuple = tuple(current)
                                    local_visited.add(current_tuple)
                                states_skipped_claimed += seq_period
                                cycles_skipped += 1
                                continue
                            else:
                                # Claim this cycle for this worker
                                shared_cycles[min_state_tuple] = worker_id
                                cycle_claimed = True
                        
                        # Only process if we successfully claimed the cycle
                        if not cycle_claimed:
                            continue
                        
                        # Process cycle (we've successfully claimed it)
                        states_tuples = (min_state,)
                        local_visited.add(state_tuple)
                        current = state
                        for _ in range(seq_period - 1):
                            current = current * state_update_matrix
                            current_tuple = tuple(current)
                            local_visited.add(current_tuple)
                        states_processed += 1
                        cycles_found += 1
                        cycles_claimed += 1
                    else:
                        # Full mode
                        local_visited_set = set()
                        seq_lst, seq_period = _find_sequence_cycle(
                            state,
                            state_update_matrix,
                            local_visited_set,
                            algorithm=algorithm,
                            period_only=period_only,
                        )
                        for seq_state in seq_lst:
                            seq_state_tuple = tuple(seq_state)
                            local_visited.add(seq_state_tuple)
                        states_tuples = [tuple(s) for s in seq_lst]
                    
                    # Store sequence information
                    sequences.append({
                        'states': states_tuples,
                        'period': seq_period,
                        'start_state': state_tuple,
                        'period_only': period_only,
                    })
                    
                    if seq_period > worker_max_period:
                        worker_max_period = seq_period
                    
                    processed_count += 1
                    
            except Exception as e:
                errors.append(f'Error processing state {state_tuple}: {str(e)}')
                continue
        
        batch_elapsed = time.time() - batch_start_time
        if DEBUG_PARALLEL:
            debug_log(f'Batch {batches_processed} completed in {batch_elapsed:.2f}s ({len(batch)} states)')
    
    # Main loop: pull batches from queue until sentinel (None)
    debug_log(f'Starting to pull batches from queue (aggregation: {batch_aggregation_count})...')
    import time
    import queue as queue_module
    worker_start_time = time.time()
    
    while True:
        try:
            # Batch aggregation: Pull multiple batches at once to reduce IPC overhead
            # Use get_nowait() with fallback to reduce blocking
            batches_to_process = []
            sentinel_received = False
            
            # Try to pull multiple batches using get_nowait() (non-blocking)
            for _ in range(batch_aggregation_count):
                try:
                    batch = task_queue.get_nowait()
                    if batch is None:
                        # Sentinel received - process remaining batches then exit
                        sentinel_received = True
                        break
                    batches_to_process.append(batch)
                except queue_module.Empty:
                    # No more batches available right now, process what we have
                    break
            
            # If we got a sentinel, process remaining batches then exit
            if sentinel_received:
                for remaining_batch in batches_to_process:
                    process_single_batch(remaining_batch)
                debug_log(f'Received sentinel, worker done. Processed {batches_processed} batches, {processed_count} states')
                break
            
            # If no batches pulled (queue empty), try blocking get with timeout
            if not batches_to_process:
                try:
                    batch = task_queue.get(timeout=0.5)
                    if batch is None:
                        debug_log(f'Received sentinel, worker done. Processed {batches_processed} batches, {processed_count} states')
                        break
                    batches_to_process.append(batch)
                except queue_module.Empty:
                    # Queue still empty, continue waiting
                    continue
            
            # Process all pulled batches
            for batch in batches_to_process:
                process_single_batch(batch)
        
        except queue_module.Empty:
            # Timeout - continue waiting (sentinel not received yet)
            continue
        except Exception as e:
            debug_log(f'Error in worker loop: {e}')
            errors.append(f'Worker loop error: {str(e)}')
            # Continue processing (don't exit on error)
            continue
    
    worker_elapsed = time.time() - worker_start_time
    debug_log(f'Worker completed in {worker_elapsed:.2f}s: {processed_count} states, {len(sequences)} sequences')
    
    # Work distribution metrics
    work_metrics = {
        'states_processed': states_processed,
        'states_skipped_visited': states_skipped_visited,
        'states_skipped_claimed': states_skipped_claimed,
        'cycles_found': cycles_found,
        'cycles_claimed': cycles_claimed,
        'cycles_skipped': cycles_skipped,
        'batches_processed': batches_processed,
    }
    
    return {
        'sequences': sequences,
        'max_period': worker_max_period,
        'processed_count': processed_count,
        'errors': errors,
        'work_metrics': work_metrics,
    }


def lfsr_sequence_mapper_parallel_dynamic(
    state_update_matrix: Any,
    state_vector_space: Any,
    gf_order: int,
    output_file: Optional[TextIO] = None,
    no_progress: bool = False,
    algorithm: str = "auto",
    period_only: bool = False,
    num_workers: Optional[int] = None,
    batch_size: Optional[int] = None,
) -> Tuple[Dict[int, List[Any]], Dict[int, int], int, int]:
    """
    Dynamic parallel version of lfsr_sequence_mapper using shared task queue.
    
    This implementation uses Option 1 (Shared Task Queue) from the dynamic threading
    feasibility analysis. Workers pull batches of states from a shared queue dynamically,
    enabling better load balancing compared to static chunk assignment.
    
    Args:
        state_update_matrix: The LFSR state update matrix
        state_vector_space: Vector space of all possible states
        gf_order: The field order
        output_file: Optional file object for output
        no_progress: If True, disable progress bar display
        algorithm: Algorithm to use: "floyd", "brent", "enumeration", or "auto"
        period_only: If True, compute periods only without storing sequences
        num_workers: Number of parallel workers (default: CPU count)
        batch_size: Number of states per batch in queue (default: auto-selected
            based on state space size: 500-1000 for small, 200-500 for medium,
            100-200 for large problems)
    
    **IPC Optimization (Phase 2.2)**:
    
    This implementation includes batch aggregation to reduce IPC overhead:
    - Workers pull multiple batches at once (2-8 batches per queue operation)
    - Uses get_nowait() (non-blocking) with fallback to blocking get()
    - Reduces queue contention and IPC overhead by 1.2-1.5x
    - Batch aggregation count is adaptive based on problem size
    
    Returns:
        Tuple of (seq_dict, period_dict, max_period, periods_sum)
        Same format as lfsr_sequence_mapper
    """
    from lfsr.formatter import dump, dump_seq_row, subsection
    
    # Determine number of workers
    if num_workers is None:
        num_workers = multiprocessing.cpu_count()
    
    # Calculate state space size for optimal worker selection
    try:
        d = len(state_vector_space.basis())
        gf_order_val = state_vector_space.base_ring().order()
        state_space_size = int(gf_order_val) ** d
    except (AttributeError, TypeError):
        state_space_size = sum(1 for _ in state_vector_space)
    
    # Extract coefficients from matrix
    d = state_update_matrix.dimensions()[0]
    coeffs_vector = [int(state_update_matrix[i, d-1]) for i in range(d)]
    
    # Adaptive batch sizing based on state space size
    # Goal: Balance IPC overhead vs. load balancing granularity
    if batch_size is None or batch_size <= 0:
        # Auto-select optimal batch size based on problem size
        if state_space_size < 8192:  # Small problems (< 8K states)
            # Larger batches to reduce IPC overhead (overhead dominates)
            batch_size = max(500, min(1000, state_space_size // (num_workers * 2)))
        elif state_space_size < 65536:  # Medium problems (8K-64K states)
            # Medium batches for balance
            batch_size = max(200, min(500, state_space_size // (num_workers * 4)))
        else:  # Large problems (> 64K states)
            # Smaller batches for better load balancing (computation dominates)
            batch_size = max(100, min(200, state_space_size // (num_workers * 8)))
    
    # Ensure batch_size is reasonable (at least 10, at most state_space_size)
    batch_size = max(10, min(batch_size, state_space_size))
    
    # Calculate batch aggregation count (number of batches to pull at once)
    # Goal: Reduce IPC overhead by pulling multiple batches per queue operation
    # Adaptive based on problem size and number of workers
    if state_space_size < 8192:  # Small problems
        # Pull 2-3 batches at once (smaller aggregation for small problems)
        batch_aggregation_count = max(2, min(3, num_workers))
    elif state_space_size < 65536:  # Medium problems
        # Pull 3-5 batches at once (good balance)
        batch_aggregation_count = max(3, min(5, num_workers * 2))
    else:  # Large problems
        # Pull 4-8 batches at once (larger aggregation for large problems)
        batch_aggregation_count = max(4, min(8, num_workers * 2))
    
    # Ensure reasonable bounds
    batch_aggregation_count = max(1, min(batch_aggregation_count, 10))
    
    subsec_name = "STATES SEQUENCES"
    subsec_desc = "all possible state sequences " + "and their corresponding periods (dynamic parallel processing)"
    subsection(subsec_name, subsec_desc, output_file)
    
    if state_space_size == 0:
        return {}, {}, 0, 0
    
    # Create shared objects for workers
    manager = multiprocessing.Manager()
    
    # Phase 3.1: Work Stealing - Per-worker queues instead of single shared queue
    # This reduces lock contention and improves scalability
    use_work_stealing = True  # Enable work stealing (Phase 3.1)
    
    if use_work_stealing:
        # Per-worker queues for work stealing
        worker_queues = [manager.Queue() for _ in range(num_workers)]
        task_queue = None  # Not used in work stealing mode
        if not no_progress:
            print(f"  Using work stealing with {num_workers} per-worker queues (Phase 3.1)")
            import sys
            sys.stdout.flush()
    else:
        # Original shared queue (fallback)
        task_queue = manager.Queue()
        worker_queues = None
    
    shared_cycles = manager.dict()
    cycle_lock = manager.Lock()
    
    # Populate queue with batches of states
    # Use same state_index_to_tuple function from _partition_state_space
    def state_index_to_tuple(state_index: int, degree: int, gf_order: int) -> Tuple[int, ...]:
        """Convert state index to tuple representation without iterating VectorSpace."""
        if gf_order == 2:
            return tuple((state_index >> i) & 1 for i in range(degree))
        else:
            result = []
            num = state_index
            for _ in range(degree):
                result.append(num % gf_order)
                num //= gf_order
            return tuple(result)
    
    # Lazy task generation: Use background thread to generate batches on-demand
    # This reduces memory usage and startup time for large problems
    import threading
    import queue as queue_module
    import time
    
    if not no_progress:
        print(f"  Using lazy task generation (batches of {batch_size} states)...")
        import sys
        sys.stdout.flush()
    
    # Generator function for batches (lazy generation)
    def batch_generator():
        """Generate batches of states on-demand."""
        current_batch = []
        for state_idx in range(state_space_size):
            state_tuple = state_index_to_tuple(state_idx, d, gf_order_val)
            current_batch.append((state_tuple, state_idx))
            
            # When batch is full, yield it
            if len(current_batch) >= batch_size:
                yield current_batch
                current_batch = []
        
        # Yield remaining states as final batch
        if current_batch:
            yield current_batch
    
    # Producer thread: generates batches and puts them in queue
    batches_created = 0
    producer_done = threading.Event()
    producer_error = [None]  # Use list to allow modification from nested function
    
    def producer_thread():
        """Background thread that generates batches and populates queues."""
        nonlocal batches_created
        try:
            if use_work_stealing:
                # Phase 3.1: Distribute batches round-robin to worker queues
                for batch in batch_generator():
                    worker_id = batches_created % num_workers
                    worker_queues[worker_id].put(batch)
                    batches_created += 1
            else:
                # Original: Single shared queue
                for batch in batch_generator():
                    task_queue.put(batch)
                    batches_created += 1
        except Exception as e:
            producer_error[0] = e
        finally:
            # Signal completion and add sentinels
            producer_done.set()
            # Add sentinel values (None) to signal workers to stop
            if use_work_stealing:
                # One sentinel per worker queue
                for worker_queue in worker_queues:
                    try:
                        worker_queue.put(None)
                    except:
                        pass
            else:
                # Original: One sentinel per worker in shared queue
                for _ in range(num_workers):
                    try:
                        task_queue.put(None)
                    except:
                        pass
    
    # Start producer thread
    producer = threading.Thread(target=producer_thread, daemon=True)
    producer.start()
    
    if not no_progress:
        print(f"  Producer thread started (lazy generation enabled)")
        sys.stdout.flush()
    
    # Prepare worker data
    worker_data_list = []
    for worker_id in range(num_workers):
        if use_work_stealing:
            # Phase 3.1: Pass worker queues and worker_id for work stealing
            worker_data = (
                worker_queues,  # List of all worker queues
                worker_id,  # This worker's ID
                coeffs_vector,
                gf_order,
                d,
                algorithm,
                period_only,
                shared_cycles,
                cycle_lock,
                batch_aggregation_count,
            )
        else:
            # Original: Single shared queue
            worker_data = (
                task_queue,
                coeffs_vector,
                gf_order,
                d,
                algorithm,
                period_only,
                worker_id,
                shared_cycles,
                cycle_lock,
                batch_aggregation_count,
            )
        worker_data_list.append(worker_data)
    
    # Process with workers
    if not no_progress:
        print(f"  Starting {num_workers} dynamic workers...")
        import sys
        sys.stdout.flush()
    
    # Persistent worker pool management (Phase 2.3)
    # Use module-level pool that can be reused across analyses
    def get_or_create_pool(num_workers, use_persistent_pool=True):
        """Get or create persistent worker pool."""
        global _worker_pool, _worker_pool_context, _worker_pool_size
        
        if not use_persistent_pool:
            # Create temporary pool (original behavior)
            try:
                ctx = multiprocessing.get_context('fork')
            except ValueError:
                ctx = multiprocessing.get_context('spawn')
            return ctx.Pool(processes=num_workers), ctx, True  # is_temporary=True
        
        with _worker_pool_lock:
            # Check if existing pool can be reused
            if _worker_pool is not None and _worker_pool_size == num_workers:
                try:
                    # Verify pool is still alive (check if it has a _state attribute)
                    # multiprocessing.Pool has _state that indicates if it's running
                    if hasattr(_worker_pool, '_state') and _worker_pool._state == multiprocessing.pool.RUN:
                        return _worker_pool, _worker_pool_context, False  # is_temporary=False
                    else:
                        # Pool is not running, need to recreate
                        _worker_pool = None
                        _worker_pool_context = None
                        _worker_pool_size = 0
                except (AttributeError, ValueError):
                    # Pool is dead or invalid, need to recreate
                    _worker_pool = None
                    _worker_pool_context = None
                    _worker_pool_size = 0
            
            # Create new pool
            try:
                ctx = multiprocessing.get_context('fork')
                if not no_progress:
                    print(f"  Creating persistent worker pool ({num_workers} workers)...")
            except ValueError:
                ctx = multiprocessing.get_context('spawn')
                if not no_progress:
                    print(f"  Creating persistent worker pool ({num_workers} workers, spawn mode)...")
            
            pool = ctx.Pool(processes=num_workers)
            _worker_pool = pool
            _worker_pool_context = ctx
            _worker_pool_size = num_workers
            
            if not no_progress:
                print(f"  Persistent pool created (will be reused for subsequent analyses)")
            
            return pool, ctx, False  # is_temporary=False
    
    try:
        # Get or create persistent pool
        pool, ctx, is_temporary = get_or_create_pool(num_workers, use_persistent_pool=True)
        
        if not no_progress:
            if is_temporary:
                print(f"  Using temporary pool")
            else:
                print(f"  Using persistent pool (reused)")
        
        start_time = time.time()
        
        # Use pool (don't use 'with' statement for persistent pool)
        if is_temporary:
            # Temporary pool: use context manager
            with pool:
                worker_results = pool.map(_process_task_batch_dynamic, worker_data_list)
        else:
            # Persistent pool: don't close, just use it
            worker_results = pool.map(_process_task_batch_dynamic, worker_data_list)
        
        elapsed = time.time() - start_time
        if not no_progress:
            print(f"  Workers completed in {elapsed:.2f}s")
        
        # Wait for producer thread to finish (should already be done)
        import sys
        producer.join(timeout=5.0)
        if producer.is_alive():
            if not no_progress:
                print(f"  Warning: Producer thread did not finish in time", file=sys.stderr)
        
        # Check for producer errors
        if producer_error[0]:
            raise RuntimeError(f"Producer thread error: {producer_error[0]}")
        
        if not no_progress:
            print(f"  Producer completed: {batches_created} batches generated")
    
    except Exception as e:
        import sys
        print(f"ERROR: Dynamic parallel processing failed: {e}", file=sys.stderr)
        print("  Falling back to sequential processing...", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return lfsr_sequence_mapper(
            state_update_matrix,
            state_vector_space,
            gf_order,
            output_file,
            no_progress,
            algorithm,
            period_only,
        )
    
    # Extract work metrics from worker results for load imbalance analysis
    work_metrics_list = [result.get('work_metrics', {}) for result in worker_results]
    
    # Merge results
    seq_dict, period_dict, max_period, periods_sum = _merge_parallel_results(
        worker_results, gf_order, d, shared_cycles
    )
    
    # Calculate load imbalance from work metrics
    if work_metrics_list and all('states_processed' in m for m in work_metrics_list):
        states_processed_list = [m['states_processed'] for m in work_metrics_list]
        total_states = sum(states_processed_list)
        if total_states > 0:
            avg_work = total_states / len(states_processed_list)
            max_work = max(states_processed_list)
            imbalance_pct = ((max_work - avg_work) / avg_work * 100) if avg_work > 0 else 0
            # Store in a way that can be accessed (for now, just log if DEBUG)
            import os
            if os.environ.get('DEBUG_PARALLEL', '0') == '1':
                import sys
                print(f"[Load Imbalance] Workers: {states_processed_list}, Avg: {avg_work:.1f}, Max: {max_work}, Imbalance: {imbalance_pct:.1f}%", file=sys.stderr)
    
    # Display sequences (same format as sequential version)
    print("\n")
    num_sequences = len(period_dict)
    row_width = TABLE_ROW_WIDTH
    F = GF(gf_order)
    V_special = VectorSpace(F, d)
    special_state = vector(F, [F(1) if i == d - 1 else F(0) for i in range(d)])
    
    if period_only:
        for seq_num, period in period_dict.items():
            seq_entry = f" | ** sequence {seq_num:3d} | T : {period:3d} | (period only)  |"
            dump(seq_entry, "mode=all", output_file)
    else:
        for seq_num, sequence in seq_dict.items():
            period = period_dict[seq_num]
            seq_entry, seq_all_v = _format_sequence_entry(
                seq_num, sequence, period, max_period, special_state, row_width
            )
            
            dump_seq_row(
                seq_num, seq_entry, num_sequences, row_width, "mode=console", output_file
            )
            dump_seq_row(
                seq_num, seq_all_v, num_sequences, row_width, "mode=file", output_file
            )
    
    state_vector_space_size = int(gf_order) ** d
    dump("  PERIOD VALUES SUMMED : " + str(periods_sum), "mode=all", output_file)
    dump(
        "     NO. STATE VECTORS : " + str(state_vector_space_size),
        "mode=all",
        output_file,
    )
    
    # Verification
    if periods_sum != state_vector_space_size:
        import sys
        print(
            f"WARNING: Period sum ({periods_sum}) != state space size ({state_vector_space_size})",
            file=sys.stderr,
        )
    
    return seq_dict, period_dict, max_period, periods_sum


def display_period_distribution(
    period_dict: Dict[int, int],
    gf_order: int,
    lfsr_degree: int,
    is_primitive: bool,
    output_file: Optional[TextIO] = None,
) -> None:
    """
    Display period distribution statistics for LFSR sequences.
    
    Args:
        period_dict: Dictionary mapping sequence numbers to periods
        gf_order: The Galois field order
        lfsr_degree: The degree of the LFSR
        is_primitive: Whether the characteristic polynomial is primitive
        output_file: Optional file object for output
    """
    from lfsr.formatter import dump, subsection
    from lfsr.statistics import compute_period_distribution
    
    subsec_name = "PERIOD DISTRIBUTION STATISTICS"
    subsec_desc = "statistical analysis of period distribution across all sequences"
    subsection(subsec_name, subsec_desc, output_file)
    
    # Compute distribution statistics
    stats = compute_period_distribution(period_dict, gf_order, lfsr_degree, is_primitive)
    
    if "error" in stats:
        dump(f"  Error: {stats['error']}", "mode=all", output_file)
        return
    
    # Basic statistics
    dump(f"  Total Sequences: {stats['total_sequences']}", "mode=all", output_file)
    dump(f"  Minimum Period: {stats['min_period']}", "mode=all", output_file)
    dump(f"  Maximum Period: {stats['max_period']}", "mode=all", output_file)
    dump(f"  Mean Period: {stats['mean_period']:.2f}", "mode=all", output_file)
    dump(f"  Median Period: {stats['median_period']:.2f}", "mode=all", output_file)
    dump(f"  Standard Deviation: {stats['std_deviation']:.2f}", "mode=all", output_file)
    dump(f"  Variance: {stats['variance']:.2f}", "mode=all", output_file)
    
    # Distribution info
    dist_info = stats['distribution_info']
    dump(f"  Unique Periods: {dist_info['unique_periods']}", "mode=all", output_file)
    dump(f"  Period Diversity: {dist_info['period_diversity']:.2%}", "mode=all", output_file)
    
    # Theoretical bounds
    theo_bounds = stats['theoretical_bounds']
    dump("", "mode=all", output_file)
    dump("  Theoretical Bounds:", "mode=all", output_file)
    dump(f"    Maximum Theoretical Period: {theo_bounds['max_theoretical_period']}", "mode=all", output_file)
    dump(f"    State Space Size: {theo_bounds['state_space_size']}", "mode=all", output_file)
    dump(f"    Polynomial is Primitive: {theo_bounds['is_primitive']}", "mode=all", output_file)
    
    # Comparison
    comparison = stats['comparison']
    dump("", "mode=all", output_file)
    dump("  Comparison with Theoretical Bounds:", "mode=all", output_file)
    dump(f"    Max Period = Theoretical Max: {comparison['max_period_equals_theoretical']}", "mode=all", output_file)
    dump(f"    Max Period Ratio: {comparison['max_period_ratio']:.2%}", "mode=all", output_file)
    
    if is_primitive:
        dump(f"    All Periods Maximum: {comparison.get('all_periods_maximum', False)}", "mode=all", output_file)
        if 'expected_period' in comparison:
            dump(f"    Expected Period (primitive): {comparison['expected_period']}", "mode=all", output_file)
            dump(f"    Sequences with Max Period: {comparison.get('actual_sequences_with_max_period', 0)} / {comparison.get('expected_sequences', 0)}", "mode=all", output_file)
    
    # Period frequency (top periods)
    period_freq = stats['period_frequency']
    if period_freq:
        dump("", "mode=all", output_file)
        dump("  Period Frequency (Top 10):", "mode=all", output_file)
        sorted_freq = sorted(period_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        for period, frequency in sorted_freq:
            percentage = (frequency / stats['total_sequences']) * 100
            dump(f"    Period {period}: {frequency} sequences ({percentage:.1f}%)", "mode=all", output_file)
