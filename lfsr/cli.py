#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command-line interface for LFSR analysis tool.

This module provides the main entry point and CLI logic for the lfsr-seq tool.
"""

import sys
import os
import datetime
from typing import Optional, TextIO
from sage.all import *

from lfsr.field import validate_gf_order, validate_coefficient_vector
from lfsr.io import read_and_validate_csv
from lfsr.core import build_state_update_matrix, compute_matrix_order
from lfsr.analysis import lfsr_sequence_mapper
from lfsr.polynomial import characteristic_polynomial
from lfsr.formatter import intro, section, subsection, dump


def main(
    input_file_name: str,
    gf_order_str: str,
    output_file: Optional[TextIO] = None
) -> None:
    """
    Main function to process LFSR coefficient vectors and perform analysis.
    
    Args:
        input_file_name: Path to CSV file containing coefficient vectors
        gf_order_str: String representation of the Galois field order
        output_file: Optional file object for output (defaults to stdout)
    """
    # Validate GF order
    gf_order = validate_gf_order(gf_order_str)
    
    # Read and validate CSV file
    coeffs_list = read_and_validate_csv(input_file_name, gf_order)
    
    # Print introduction
    my_name = 'Linear Feedback Shift Register Toy'
    my_version = ' 0.1 (08-Jan-2023)'
    t_i = intro(my_name, my_version, input_file_name, gf_order_str, output_file)
    
    coeffs_num = 0
    for coeffs_vector_str in coeffs_list:
        coeffs_num += 1
        
        # Validate coefficient vector
        validate_coefficient_vector(coeffs_vector_str, gf_order, coeffs_num)
        
        # Convert coefficients to integers
        coeffs_vector = [int(c) for c in coeffs_vector_str]
        
        d = len(coeffs_vector)
        state_vector_space_size = int(gf_order) ** d
        
        # Build state update matrix
        C, CS = build_state_update_matrix(coeffs_vector, gf_order)
        
        # Print section header
        section('COEFFS SERIES ' + str(coeffs_num), str(coeffs_vector), output_file)
        
        # Print subsection for state update matrix
        subsection_name = 'STATE UPDATE MATRIX'
        subsection_desc = (
            'state update matrix operation '
            + 'convention : S_i * C = S_i+1'
        )
        subsection(subsection_name, subsection_desc, output_file)
        
        # Print state update matrix
        for c_row in C:
            dump(' ' * 2 + str(c_row), 'mode=all', output_file)
        
        # Building the LFSR matrix operator C acting on state S_i
        # generating state S_i+1 : S_i * C = S_i+1
        M = MatrixSpace(GF(gf_order), d, d)
        I = M.identity_matrix()
        
        # Compute matrix order
        compute_matrix_order(C, I, state_vector_space_size, output_file)
        
        # Finding order of C, i.e. the exponent of C that
        # generates the identity matrix
        
        # Create vector space and analyze sequences
        V = VectorSpace(GF(gf_order), d)
        lfsr_sequence_mapper(C, V, gf_order, output_file)
        
        # Finding all sequences of states of the parameterized
        # LFSR and their corresponding periods
        
        # Compute characteristic polynomial
        characteristic_polynomial(CS, gf_order, output_file)
        
        # Finding characteristic polynomial of the corresponding
        # LFSR state update matrix over GF(gf_order), obtaining
        # its order and its factors orders to see that the orders
        # of the factors are in fact factors of the order of
        # the big char poly.
    
    # Print execution time
    t_f = datetime.datetime.now()
    t_e = t_f - t_i
    print('\n  TOTAL execusion time : ' + str(t_e))


def cli_main() -> None:
    """
    Command-line interface entry point.
    
    Handles argument parsing, validation, and file I/O setup.
    """
    try:
        # Validate command line arguments
        if len(sys.argv) != 3:
            print("Usage: %s <coeffs_csv_filename> <GF_order>" % sys.argv[0])
            print("       You should provide the filename for the LFSR")
            print("       coefficients vectors csv as the first arg and")
            print("       Galois Field order as the second arg.")
            sys.exit(1)
        
        input_file_name = sys.argv[1]
        output_file_name = input_file_name + '.out'
        gf_order = sys.argv[2]
        
        # Validate input file exists before opening output file
        if not os.path.exists(input_file_name):
            print("ERROR: Input CSV file not found: %s" % input_file_name)
            sys.exit(1)
        
        # Open output file with context manager for proper resource management
        with open(output_file_name, 'w', encoding='utf-8') as output_file:
            main(input_file_name, gf_order, output_file)
    except IOError as e:
        print("ERROR: File I/O error: %s" % str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nERROR: Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print("ERROR: Unexpected error: %s" % str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli_main()

