#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command-line interface for LFSR analysis tool.

This module provides the main entry point and CLI logic for the lfsr-seq tool.
"""

import argparse
import datetime
import os
import subprocess
import sys
from typing import Optional, TextIO

# Try to import sage, but don't fail until it's actually needed
_sage_available = False
try:
    from sage.all import *
    _sage_available = True
except ImportError:
    # If direct import fails, try to find SageMath via the 'sage' command
    # This is needed when running in a virtual environment that doesn't have
    # access to system site-packages
    try:
        # Get SageMath's Python path by running sage -c
        result = subprocess.run(
            ["sage", "-c", "import sys; print('\\n'.join(sys.path))"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            sage_paths = result.stdout.strip().split("\n")
            # Add SageMath's site-packages to sys.path
            for path in sage_paths:
                if path and path not in sys.path and os.path.isdir(path):
                    sys.path.insert(0, path)
            # Try importing again
            from sage.all import *
            _sage_available = True
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, ImportError):
        pass

from lfsr import __version__


def main(
    input_file_name: str,
    gf_order_str: str,
    output_file: Optional[TextIO] = None,
    verbose: bool = False,
    quiet: bool = False,
    no_progress: bool = False,
    output_format: str = "text",
    algorithm: str = "auto",
    period_only: bool = False,
    show_period_stats: bool = True,
    use_parallel: Optional[bool] = None,
    num_workers: Optional[int] = None,
) -> None:
    """Main function to process LFSR coefficient vectors and perform analysis.

    This function orchestrates the complete LFSR analysis workflow:

    1. Validates the Galois field order
    2. Reads and validates CSV coefficient vectors
    3. For each coefficient vector:
       - Builds the state update matrix
       - Computes matrix order
       - Analyzes all state sequences and periods
       - Computes characteristic polynomial

    Args:
        input_file_name: Path to CSV file containing coefficient vectors.
            Each row should contain coefficients for one LFSR configuration.
        gf_order_str: String representation of the Galois field order.
            Must be a prime or prime power (e.g., "2", "3", "4", "5", "7", "8", etc.).
        output_file: Optional file object for output. If None, output goes
            to stdout only. If provided, output is written to both stdout
            and the file.

    Raises:
        SystemExit: If input validation fails or file I/O errors occur.

    Example:
        >>> with open("output.txt", "w") as f:
        ...     main("coefficients.csv", "2", output_file=f)
    """
    # Check if sage is available
    if not _sage_available:
        print(
            "ERROR: SageMath is required but not installed.\n"
            "Please install SageMath using one of the following methods:\n"
            "  Debian/Ubuntu: sudo apt-get install sagemath\n"
            "  Fedora/RHEL:   sudo dnf install sagemath\n"
            "  Arch Linux:    sudo pacman -S sagemath\n"
            "  macOS:         brew install sagemath\n"
            "  Conda:         conda install -c conda-forge sage\n",
            file=sys.stderr,
        )
        sys.exit(1)
    
    # Import sage-dependent modules
    from lfsr.analysis import lfsr_sequence_mapper
    from lfsr.core import build_state_update_matrix, compute_matrix_order
    from lfsr.field import validate_coefficient_vector, validate_gf_order
    from lfsr.formatter import dump, intro, section, subsection
    from lfsr.io import read_and_validate_csv
    from lfsr.polynomial import characteristic_polynomial
    
    # Validate GF order
    gf_order = validate_gf_order(gf_order_str)

    # Read and validate CSV file
    coeffs_list = read_and_validate_csv(input_file_name, gf_order)

    # Print introduction
    my_name = "Linear Feedback Shift Register Toy"
    my_version = " 0.1 (08-Jan-2023)"
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
        section("COEFFS SERIES " + str(coeffs_num), str(coeffs_vector), output_file)

        # Print subsection for state update matrix
        subsection_name = "STATE UPDATE MATRIX"
        subsection_desc = (
            "state update matrix operation " + "convention : S_i * C = S_i+1"
        )
        subsection(subsection_name, subsection_desc, output_file)

        # Print state update matrix
        for c_row in C:
            dump(" " * 2 + str(c_row), "mode=all", output_file)

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
        
        # Auto-select algorithm based on mode
        effective_algorithm = algorithm
        if algorithm == "auto":
            if period_only:
                effective_algorithm = "floyd"  # Floyd is better for period-only
            else:
                effective_algorithm = "enumeration"  # Enumeration is better for full mode
        
        # Decide whether to use parallel processing
        # Auto-detect: use parallel if state space is large enough and parallel is enabled
        should_use_parallel = False
        if use_parallel is None:
            # Auto-detect: use parallel for large state spaces
            # Threshold: > 10,000 states and at least 2 CPU cores
            import multiprocessing
            should_use_parallel = (
                state_vector_space_size > 10000
                and multiprocessing.cpu_count() >= 2
            )
        else:
            should_use_parallel = use_parallel
        
        # Use parallel or sequential version
        # NOTE: Parallel processing works reliably only in period-only mode
        # In full sequence mode, it may hang due to SageMath/multiprocessing issues
        if should_use_parallel:
            from lfsr.analysis import lfsr_sequence_mapper_parallel
            # Force period_only=True for parallel processing to avoid hangs
            # This is a workaround until the matrix multiplication hang is fixed
            parallel_period_only = period_only if period_only else True
            if not period_only:
                import sys
                print("WARNING: Parallel processing forced to period-only mode to avoid hangs.", file=sys.stderr)
                print("  Use --no-parallel for full sequence mode, or --period-only for parallel.", file=sys.stderr)
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper_parallel(
                C, V, gf_order, output_file, no_progress=no_progress, 
                algorithm=effective_algorithm, period_only=parallel_period_only, num_workers=num_workers
            )
        else:
            seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
                C, V, gf_order, output_file, no_progress=no_progress, 
                algorithm=effective_algorithm, period_only=period_only
            )

        # Finding all sequences of states of the parameterized
        # LFSR and their corresponding periods

        # Compute characteristic polynomial
        char_poly = characteristic_polynomial(CS, gf_order, output_file)
        
        # Display period distribution statistics (if enabled)
        if show_period_stats:
            # Check if polynomial is primitive for period distribution analysis
            from lfsr.polynomial import is_primitive_polynomial
            is_primitive = is_primitive_polynomial(char_poly, gf_order)
            
            # Display period distribution statistics
            from lfsr.analysis import display_period_distribution
            display_period_distribution(period_dict, gf_order, d, is_primitive, output_file)

        # Export in requested format if not text
        if output_format != "text" and output_file is not None:
            from lfsr.export import get_export_function
            from lfsr.polynomial import polynomial_order

            # Get polynomial order
            char_poly_order = polynomial_order(char_poly, d, gf_order)

            # Get export function and export
            export_func = get_export_function(output_format)
            export_func(
                seq_dict,
                period_dict,
                max_period,
                periods_sum,
                char_poly,
                char_poly_order,
                coeffs_vector,
                gf_order,
                output_file,
            )

        # Finding characteristic polynomial of the corresponding
        # LFSR state update matrix over GF(gf_order), obtaining
        # its order and its factors orders to see that the orders
        # of the factors are in fact factors of the order of
        # the big char poly.

    # Print execution time
    t_f = datetime.datetime.now()
    t_e = t_f - t_i
    print("\n  TOTAL execusion time : " + str(t_e))


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: Optional list of arguments to parse. If None, uses sys.argv.

    Returns:
        Parsed arguments as argparse.Namespace.
    """
    parser = argparse.ArgumentParser(
        prog="lfsr-seq",
        description="Linear Feedback Shift Register (LFSR) Sequence Analysis Tool",
        epilog=(
            "Example:\n"
            "  lfsr-seq strange.csv 2\n"
            "  lfsr-seq coefficients.csv 3 --output results.txt\n"
            "\n"
            "For more information, see the README.md file."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "input_file",
        metavar="INPUT_FILE",
        help="CSV file containing LFSR coefficient vectors (one per line)",
    )

    parser.add_argument(
        "gf_order",
        metavar="GF_ORDER",
        help="Galois field order (must be a prime or prime power, e.g., 2, 3, 4, 5, 7, 8)",
    )

    parser.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT_FILE",
        default=None,
        help="Output file path (default: INPUT_FILE.out)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output (show detailed progress and information)",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Enable quiet mode (suppress non-essential output)",
    )

    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bar display",
    )

    parser.add_argument(
        "--format",
        choices=["text", "json", "csv", "xml"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--period-only",
        action="store_true",
        help="Compute periods only, without storing sequences. Floyd's algorithm uses true O(1) space in this mode.",
    )

    parser.add_argument(
        "--algorithm",
        choices=["floyd", "brent", "enumeration", "auto"],
        default="auto",
        help="Cycle detection algorithm: 'floyd' (tortoise-and-hare), 'brent' (powers-of-2), 'enumeration' (default for full mode, faster), or 'auto' (enumeration for full mode, floyd for period-only)",
    )

    parser.add_argument(
        "--check-primitive",
        action="store_true",
        help="Explicitly check and report if characteristic polynomial is primitive (primitive polynomials yield maximum period LFSRs)",
    )

    parser.add_argument(
        "--show-period-stats",
        action="store_true",
        default=True,
        help="Display detailed period distribution statistics (mean, median, variance, frequency histogram, theoretical bounds comparison). Enabled by default.",
    )
    
    parser.add_argument(
        "--no-period-stats",
        action="store_false",
        dest="show_period_stats",
        help="Disable period distribution statistics display",
    )

    parser.add_argument(
        "--parallel",
        action="store_true",
        default=None,
        dest="use_parallel",
        help="Enable parallel state enumeration (auto-enabled for large state spaces > 10,000)",
    )

    parser.add_argument(
        "--no-parallel",
        action="store_false",
        dest="use_parallel",
        help="Disable parallel processing (force sequential)",
    )

    parser.add_argument(
        "--num-workers",
        type=int,
        default=None,
        metavar="N",
        help="Number of parallel workers (default: CPU count). Only used with --parallel.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Correlation attack options
    correlation_group = parser.add_argument_group(
        "correlation attack options",
        "Options for correlation attack analysis on combination generators"
    )
    
    correlation_group.add_argument(
        "--correlation-attack",
        action="store_true",
        help="Perform correlation attack analysis. Requires --lfsr-configs file specifying multiple LFSRs and combining function."
    )
    
    correlation_group.add_argument(
        "--lfsr-configs",
        metavar="CONFIG_FILE",
        help="JSON file containing combination generator configuration (LFSRs and combining function). Required for --correlation-attack."
    )
    
    correlation_group.add_argument(
        "--keystream-file",
        metavar="KEYSTREAM_FILE",
        help="File containing keystream bits (one per line, or space-separated). If not provided, keystream is generated from combination generator."
    )
    
    correlation_group.add_argument(
        "--target-lfsr",
        type=int,
        default=0,
        metavar="INDEX",
        help="Index of LFSR to attack (0-based). Default: 0 (first LFSR)."
    )
    
    correlation_group.add_argument(
        "--significance-level",
        type=float,
        default=0.05,
        metavar="ALPHA",
        help="Statistical significance level for correlation test (default: 0.05)."
    )
    
    # NIST test suite options
    nist_group = parser.add_argument_group(
        "NIST SP 800-22 test suite options",
        "Options for NIST statistical test suite analysis"
    )
    
    nist_group.add_argument(
        "--nist-test",
        action="store_true",
        help="Run NIST SP 800-22 statistical test suite on sequence. Requires sequence file or generates from LFSR."
    )
    
    nist_group.add_argument(
        "--sequence-file",
        metavar="SEQUENCE_FILE",
        help="File containing binary sequence (one bit per line, or space-separated). Required for --nist-test if not generating from LFSR."
    )
    
    nist_group.add_argument(
        "--nist-significance-level",
        type=float,
        default=0.01,
        metavar="ALPHA",
        help="Statistical significance level for NIST tests (default: 0.01)."
    )
    
    nist_group.add_argument(
        "--nist-block-size",
        type=int,
        default=128,
        metavar="SIZE",
        help="Block size for block-based NIST tests (default: 128)."
    )
    
    nist_group.add_argument(
        "--nist-output-format",
        type=str,
        default="text",
        choices=["text", "json", "csv", "xml", "html"],
        metavar="FORMAT",
        help="Output format for NIST test results (default: text). Options: text, json, csv, xml, html."
    )

    parsed_args = parser.parse_args(args)

    # Validate that verbose and quiet are not both set
    if parsed_args.verbose and parsed_args.quiet:
        parser.error("Cannot specify both --verbose and --quiet")

    return parsed_args


def cli_main() -> None:
    """
    Command-line interface entry point.

    This is the main entry point when the package is run as a script.
    It handles:
    - Command-line argument parsing and validation using argparse
    - Input file existence checking
    - Output file creation
    - Exception handling and error reporting

    The output file defaults to INPUT_FILE.out if not specified.

    Usage:
        lfsr-seq <coeffs_csv_filename> <GF_order> [options]

    Raises:
        SystemExit: If arguments are invalid, input file doesn't exist,
            or any other error occurs during execution.

    Example:
        >>> # From command line:
        >>> # $ lfsr-seq strange.csv 2
        >>> # Creates strange.csv.out with analysis results
        >>> # $ lfsr-seq strange.csv 2 --output results.txt
        >>> # Creates results.txt with analysis results
    """
    try:
        args = parse_args()

        input_file_name = args.input_file
        gf_order = args.gf_order

        # Determine output file name
        if args.output:
            output_file_name = args.output
        else:
            output_file_name = input_file_name + ".out"

        # Validate input file exists before opening output file
        if not os.path.exists(input_file_name):
            print(f"ERROR: Input CSV file not found: {input_file_name}", file=sys.stderr)
            sys.exit(1)

        # Show verbose information if requested
        if args.verbose:
            print(f"Input file: {input_file_name}")
            print(f"Output file: {output_file_name}")
            print(f"GF order: {gf_order}")
            print()

        # Open output file with context manager for proper resource management
        with open(output_file_name, "w", encoding="utf-8") as output_file:
            # Check if NIST test mode
            if args.nist_test:
                from lfsr.cli_nist import perform_nist_test_cli, load_sequence_from_file
                
                # Load sequence
                if args.sequence_file:
                    sequence = load_sequence_from_file(args.sequence_file)
                else:
                    # TODO: Extract sequence from LFSR analysis output
                    # For now, require sequence file
                    print("ERROR: --nist-test requires --sequence-file", file=sys.stderr)
                    print("       (Extracting sequence from LFSR analysis not yet implemented)", file=sys.stderr)
                    sys.exit(1)
                
                perform_nist_test_cli(
                    sequence=sequence,
                    output_file=output_file,
                    significance_level=args.nist_significance_level,
                    block_size=args.nist_block_size,
                    output_format=args.nist_output_format
                )
            # Check if correlation attack mode
            elif args.correlation_attack:
                from lfsr.cli_correlation import perform_correlation_attack_cli
                
                if not args.lfsr_configs:
                    print("ERROR: --correlation-attack requires --lfsr-configs", file=sys.stderr)
                    sys.exit(1)
                
                perform_correlation_attack_cli(
                    config_file=args.lfsr_configs,
                    output_file=output_file,
                    keystream_file=args.keystream_file,
                    keystream_length=1000,  # Default, could be made configurable
                    target_lfsr_index=args.target_lfsr,
                    significance_level=args.significance_level,
                    analyze_all_lfsrs=False,  # Could add --all-lfsrs flag
                    analyze_function=True,  # Always analyze function
                )
            else:
                # Pass flags to main function
                main(
                    input_file_name,
                    gf_order,
                    output_file=output_file,
                    verbose=args.verbose,
                    quiet=args.quiet,
                    no_progress=args.no_progress,
                    output_format=args.format,
                    algorithm=args.algorithm,
                    period_only=args.period_only,
                    show_period_stats=args.show_period_stats,
                    use_parallel=args.use_parallel,
                    num_workers=args.num_workers,
                )

        if not args.quiet:
            print(f"\nAnalysis complete. Results written to: {output_file_name}")

    except IOError as e:
        print(f"ERROR: File I/O error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nERROR: Interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
