#!/usr/bin/env python3
"""
Performance Profiling Script for Phase 2.1 and 2.2 Optimizations

This script profiles the performance improvements from:
- Phase 2.1: Adaptive batch sizing
- Phase 2.2: Batch aggregation (IPC overhead reduction)

It measures:
- Sequential vs Dynamic mode performance
- Speedup with different worker counts
- IPC overhead reduction
- Load balancing improvements
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from sage.all import *
    from lfsr.core import build_state_update_matrix
    from lfsr.analysis import (
        lfsr_sequence_mapper,
        lfsr_sequence_mapper_parallel_dynamic
    )
except ImportError as e:
    print(f"ERROR: Cannot import required modules: {e}")
    print("This script requires SageMath")
    sys.exit(1)


class ProfilingResult:
    """Container for profiling results."""
    def __init__(self, desc: str, state_space_size: int, category: str):
        self.desc = desc
        self.state_space_size = state_space_size
        self.category = category
        self.sequential_time = 0.0
        self.dynamic_results: Dict[str, Dict] = {}
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'description': self.desc,
            'state_space_size': self.state_space_size,
            'category': self.category,
            'sequential_time': self.sequential_time,
            'dynamic_results': self.dynamic_results,
            'timestamp': self.timestamp
        }


def profile_configuration(
    coeffs: List[int],
    gf_order: int,
    desc: str,
    num_workers_list: List[int] = [2, 4, 8],
    batch_sizes: Optional[List[int]] = None
) -> ProfilingResult:
    """
    Profile a single LFSR configuration.
    
    Args:
        coeffs: LFSR coefficients
        gf_order: Field order
        desc: Description of the configuration
        num_workers_list: List of worker counts to test
        batch_sizes: Optional list of batch sizes to test (None = auto)
    
    Returns:
        ProfilingResult with all measurements
    """
    print(f"\n{'='*80}")
    print(f"Profiling {desc} LFSR ({len(coeffs)}-bit)")
    print(f"{'='*80}")
    
    # Build state update matrix
    C, V = build_state_update_matrix(coeffs, gf_order)
    
    # Calculate state space size
    state_space_size = gf_order ** len(coeffs)
    
    # Determine category
    if state_space_size < 8192:
        category = "Small"
    elif state_space_size < 65536:
        category = "Medium"
    else:
        category = "Large"
    
    print(f"\nState space size: {state_space_size:,} states")
    print(f"Category: {category}")
    
    result = ProfilingResult(desc, state_space_size, category)
    
    # Sequential baseline
    print(f"\n1. Sequential (baseline):")
    start = time.time()
    seq_dict, seq_period_dict, seq_max_period, seq_periods_sum = lfsr_sequence_mapper(
        C, V, gf_order, period_only=True, algorithm="enumeration", no_progress=True
    )
    seq_time = time.time() - start
    result.sequential_time = seq_time
    print(f"   Time: {seq_time:.3f}s")
    print(f"   Sequences: {len(seq_period_dict)}, Sum: {seq_periods_sum}, Max: {seq_max_period}")
    
    # Dynamic mode with different worker counts
    for num_workers in num_workers_list:
        print(f"\n2. Dynamic mode ({num_workers} workers):")
        
        # Test with auto batch size
        print(f"   a. Auto batch size:")
        start = time.time()
        dyn_dict, dyn_period_dict, dyn_max_period, dyn_periods_sum = lfsr_sequence_mapper_parallel_dynamic(
            C, V, gf_order, period_only=True, algorithm="enumeration",
            num_workers=num_workers, batch_size=None, no_progress=True
        )
        dyn_time = time.time() - start
        dyn_speedup = seq_time / dyn_time if dyn_time > 0 else 0
        
        # Verify correctness
        correct = (
            len(dyn_period_dict) == len(seq_period_dict) and
            dyn_periods_sum == seq_periods_sum and
            dyn_max_period == seq_max_period
        )
        
        status = "✓" if correct else "✗"
        print(f"      {status} Time: {dyn_time:.3f}s, Speedup: {dyn_speedup:.2f}x")
        print(f"      Sequences: {len(dyn_period_dict)}, Sum: {dyn_periods_sum}")
        
        result.dynamic_results[f"{num_workers}w_auto"] = {
            'time': dyn_time,
            'speedup': dyn_speedup,
            'correct': correct,
            'num_workers': num_workers,
            'batch_size': 'auto'
        }
        
        # Test with manual batch sizes if provided
        if batch_sizes:
            for batch_size in batch_sizes:
                print(f"   b. Batch size {batch_size}:")
                start = time.time()
                dyn_dict, dyn_period_dict, dyn_max_period, dyn_periods_sum = lfsr_sequence_mapper_parallel_dynamic(
                    C, V, gf_order, period_only=True, algorithm="enumeration",
                    num_workers=num_workers, batch_size=batch_size, no_progress=True
                )
                dyn_time = time.time() - start
                dyn_speedup = seq_time / dyn_time if dyn_time > 0 else 0
                
                correct = (
                    len(dyn_period_dict) == len(seq_period_dict) and
                    dyn_periods_sum == seq_periods_sum and
                    dyn_max_period == seq_max_period
                )
                
                status = "✓" if correct else "✗"
                print(f"      {status} Time: {dyn_time:.3f}s, Speedup: {dyn_speedup:.2f}x")
                
                result.dynamic_results[f"{num_workers}w_batch{batch_size}"] = {
                    'time': dyn_time,
                    'speedup': dyn_speedup,
                    'correct': correct,
                    'num_workers': num_workers,
                    'batch_size': batch_size
                }
    
    return result


def generate_summary_report(results: List[ProfilingResult], output_file: str):
    """Generate a summary report from profiling results."""
    print(f"\n{'='*80}")
    print("GENERATING SUMMARY REPORT")
    print(f"{'='*80}")
    
    report_lines = [
        "# Phase 2.1 & 2.2 Performance Profiling Report",
        "",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Summary",
        ""
    ]
    
    # Overall statistics
    total_tests = len(results)
    all_correct = all(
        all(r.get('correct', False) for r in result.dynamic_results.values())
        for result in results
    )
    
    report_lines.extend([
        f"- Total configurations tested: {total_tests}",
        f"- All results correct: {'✓ Yes' if all_correct else '✗ No'}",
        ""
    ])
    
    # Per-category summary
    for category in ["Small", "Medium", "Large"]:
        category_results = [r for r in results if r.category == category]
        if not category_results:
            continue
        
        report_lines.extend([
            f"## {category} Problems",
            ""
        ])
        
        for result in category_results:
            report_lines.extend([
                f"### {result.desc} ({result.state_space_size:,} states)",
                "",
                f"- Sequential: {result.sequential_time:.3f}s",
                ""
            ])
            
            # Group by worker count
            for num_workers in [2, 4, 8]:
                auto_key = f"{num_workers}w_auto"
                if auto_key in result.dynamic_results:
                    r = result.dynamic_results[auto_key]
                    report_lines.append(
                        f"- Dynamic {num_workers}w (auto): {r['time']:.3f}s "
                        f"({r['speedup']:.2f}x speedup)"
                    )
            
            report_lines.append("")
    
    # Write report
    with open(output_file, 'w') as f:
        f.write('\n'.join(report_lines))
    
    print(f"Report written to: {output_file}")


def main():
    """Run comprehensive profiling."""
    print("="*80)
    print("PHASE 2.1 & 2.2 PERFORMANCE PROFILING")
    print("="*80)
    print("\nThis script profiles:")
    print("  - Phase 2.1: Adaptive batch sizing")
    print("  - Phase 2.2: Batch aggregation (IPC overhead reduction)")
    print("="*80)
    
    # Test configurations
    test_configs = [
        # Small problems
        ([1, 1, 0, 1], 2, "4-bit", [2, 4], [100, 500, 1000]),
        ([1, 0, 1, 1, 0, 0, 0, 1], 2, "8-bit", [2, 4], [100, 500, 1000]),
        ([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1], 2, "12-bit", [2, 4], [100, 500, 1000]),
        
        # Medium problems
        ([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 2, "14-bit", [2, 4, 8], [100, 200, 500]),
        
        # Large problems (if time permits)
        # ([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 2, "16-bit", [2, 4, 8], [50, 100, 200]),
    ]
    
    all_results = []
    
    for coeffs, gf_order, desc, workers, batch_sizes in test_configs:
        try:
            result = profile_configuration(
                coeffs, gf_order, desc,
                num_workers_list=workers,
                batch_sizes=batch_sizes
            )
            all_results.append(result)
        except Exception as e:
            print(f"\n✗ Error profiling {desc}: {e}")
            import traceback
            traceback.print_exc()
    
    # Save results to JSON
    json_file = project_root / "scripts" / "phase2_profiling_results.json"
    with open(json_file, 'w') as f:
        json.dump([r.to_dict() for r in all_results], f, indent=2)
    print(f"\n✓ Results saved to: {json_file}")
    
    # Generate summary report
    report_file = project_root / "scripts" / "phase2_profiling_report.md"
    generate_summary_report(all_results, str(report_file))
    
    # Final summary
    print(f"\n{'='*80}")
    print("PROFILING COMPLETE")
    print(f"{'='*80}")
    print(f"\nTested {len(all_results)} configurations")
    print(f"Results saved to: {json_file}")
    print(f"Report saved to: {report_file}")


if __name__ == '__main__':
    main()
