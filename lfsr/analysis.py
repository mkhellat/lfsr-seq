#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sequence analysis functions for LFSR.

This module provides functions for analyzing LFSR sequences, computing
periods, and categorizing state vectors.
"""

import datetime
import textwrap
from typing import Dict, List, Any, Optional, TextIO
from sage.all import *


def lfsr_sequence_mapper(
    state_update_matrix: Any,
    state_vector_space: Any,
    gf_order: int,
    output_file: Optional[TextIO] = None,
) -> tuple:
    """
    Map all possible state vectors to their sequences and periods.

    Goes through all possible state vectors, finds their periods and
    categorizes them based on what sequence they belong to.

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
    from lfsr.formatter import subsection, dump, dump_seq_row

    subsec_name = "STATES SEQUENCES"
    subsec_desc = "all possible state sequences " + "and their corresponding periods"
    subsection(subsec_name, subsec_desc, output_file)

    seq_dict = {}
    period_dict = {}
    check_lst = []
    timer_lst = []
    est_t_lst = []
    seq = 0
    counter = 0
    max_period = 1
    elp_t = 0.00
    max_t_t = 0.00
    d = len(basis(state_vector_space))
    state_vector_space_size = int(gf_order) ** d

    for bra in state_vector_space:
        timer_lst.append(datetime.datetime.now())
        ticks = counter + 1
        ref = counter - 2
        elp_delta = timer_lst[counter] - timer_lst[counter - 1]
        elp_s_int = float(elp_delta.seconds)
        elp_s_dec = float(elp_delta.microseconds) * 10**-6
        elp_s = elp_s_int + elp_s_dec
        elp_t = elp_t + elp_s  # <--- total elapsed time
        est_t_s = elp_t / ticks  # <--- elapsed time per step
        est_t_t = state_vector_space_size * est_t_s
        est_t_lst.append(est_t_t)
        if counter >= 3:
            est_t_avg = (est_t_lst[ref] + est_t_lst[ref - 1]) / 2
            if est_t_lst[ref + 1] > est_t_avg:
                max_t_t = est_t_lst[ref + 1]
        counter += 1
        _total = str(state_vector_space_size)
        _count = str(counter)
        _ind = " " * (len(_total) - len(_count))
        prog = int(counter * 60 / state_vector_space_size)
        prog_b = " " * 2 + "\u2588" * prog + " " * (60 - prog)
        prog_s = _ind + _count + "/" + _total
        prog_t = " " * 2 + format(elp_t, ".1f") + " s/" + format(max_t_t, ".1f") + " s"
        prog_v = " " * 2 + prog_s + " states checked "
        print(prog_b, end="\b")
        print(prog_t + prog_v, end="\r")

        if bra not in check_lst:
            seq += 1
            seq_lst = []
            seq_lst.append(bra)
            check_lst.append(bra)
            bra2 = bra * state_update_matrix
            seq_period = 1
            while bra2 != bra:
                seq_lst.append(bra2)
                check_lst.append(bra2)
                seq_period += 1
                bra2 = bra2 * state_update_matrix
            seq_dict[seq] = seq_lst
            period_dict[seq] = seq_period
            if period_dict[seq] > max_period:
                max_period = period_dict[seq]

    # Building two simple dictionaries for state sequences and sequence periods:
    # - keys in both dictionaries are integers starting from 1 where
    #   each integer identifies a sequence, i.e. we could call each
    #   key a "sequence number".
    # - value for a specific seq number is either the list of state
    #   vectors for that seq number (in seq dict) or its period (in
    #   period dict)
    print("\n")
    periods_sum = 0
    n = len(period_dict)  # <-- number of sequences
    w = 60  # <-- table row width
    v1 = vector({d - 1: 1})  # <-- our special state ;)
    vs = state_vector_space_size

    for k, v in seq_dict.items():
        periods_sum += period_dict[k]
        p_str = str(period_dict[k])
        p_max_str = str(max_period)
        s1 = 3 - len(str(k))
        s2 = 1 + len(p_max_str) - len(p_str)
        if v1 in v:
            seq_column_1 = " | ** sequence" + " " * s1 + str(k)
            seq_column_2 = " | T : " + p_str + " " * s2 + "| "
            indent_i = seq_column_1 + seq_column_2
            indent_w = len(indent_i) - 5
            indent_s = " | " + " " * indent_w + "| "
            seq_entry = textwrap.wrap(
                str(v1), width=w, initial_indent=indent_i, subsequent_indent=indent_s
            )
            seq_all_v = textwrap.wrap(
                str(v), width=w, initial_indent=indent_i, subsequent_indent=indent_s
            )
        else:
            seq_column_1 = " |    sequence" + " " * s1 + str(k)
            seq_column_2 = " | T : " + p_str + " " * s2 + "| "
            indent_i = seq_column_1 + seq_column_2
            indent_w = len(indent_i) - 5
            indent_s = " | " + " " * indent_w + "| "
            seq_entry = textwrap.wrap(
                str(v[0]), width=w, initial_indent=indent_i, subsequent_indent=indent_s
            )
            seq_all_v = textwrap.wrap(
                str(v), width=w, initial_indent=indent_i, subsequent_indent=indent_s
            )

        # A bunch of cosmetics to dump a shortened unicode table into
        # stdout and a detailed one into the output file.
        dump_seq_row(k, seq_entry, n, w, "mode=console", output_file)
        dump_seq_row(k, seq_all_v, n, w, "mode=file", output_file)

    dump("  PERIOD VALUES SUMMED : " + str(periods_sum), "mode=all", output_file)
    dump("     NO. STATE VECTORS : " + str(vs), "mode=all", output_file)
    # A naive verification to be happy that all states have been checked.

    return seq_dict, period_dict, max_period, periods_sum
