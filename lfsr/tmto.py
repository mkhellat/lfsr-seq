#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Time-Memory Trade-Off (TMTO) attacks for LFSR state recovery.

This module implements Hellman tables and Rainbow tables for efficient
state recovery through precomputation. TMTO attacks trade memory for
computation time, enabling faster attacks after an initial precomputation
phase.
"""

import hashlib
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from sage.all import *

from lfsr.attacks import LFSRConfig
from lfsr.core import build_state_update_matrix


@dataclass
class TMTOAttackResult:
    """
    Results from a time-memory trade-off attack.
    
    Attributes:
        attack_successful: Whether the attack successfully recovered the state
        recovered_state: Recovered initial state (if successful)
        method_used: Method used ("hellman" or "rainbow")
        table_size: Size of the precomputed table
        lookup_time: Time taken for table lookup
        precomputation_time: Time taken for table generation
        coverage: Fraction of state space covered by table
        details: Additional details about the attack
    """
    attack_successful: bool
    recovered_state: Optional[List[int]]
    method_used: str
    table_size: int
    lookup_time: float
    precomputation_time: float
    coverage: float
    details: Dict[str, Any] = field(default_factory=dict)


class HellmanTable:
    """
    Hellman table for time-memory trade-off attacks.
    
    A **Hellman table** is a precomputed table that stores chains of state
    transitions, allowing fast state recovery. Named after Martin Hellman
    (1980), it was the first time-memory trade-off technique.

    Key terminology:

    * **Hellman Table**: A precomputed table storing chains of state
      transitions. Each chain starts with a random state and ends with a
      distinguished point. The table enables fast state recovery by looking
      up chains that might contain the target state.

    * **Chain**: A sequence of states connected by the state update function.
      Each chain has length t and represents t consecutive state transitions.
      Chains are the fundamental building blocks of Hellman tables.

    * **Distinguished Point**: A state with a special property (e.g., leading
      k bits are zero) used to mark chain endpoints. Distinguished points make
      chain endpoints easy to identify and store, reducing storage requirements.

    * **Reduction Function**: A function R that maps states to starting points
      (keys). The reduction function creates chains: S_0 → f(S_0) → R(f(S_0))
      → f(R(f(S_0))) → ... where f is the state update function.
    
    - **Table Lookup**: The process of searching precomputed tables to find
      a target state. Lookup involves: (1) applying reduction function to
      target, (2) checking if result is a chain endpoint, (3) if found,
      reconstructing chain to find target.
    
    - **False Alarm**: When a chain appears to contain the target state but
      doesn't. This occurs due to collisions in the reduction function. False
      alarms must be verified by reconstructing the chain.
    
    - **Coverage**: The fraction of the state space covered by the table.
      Coverage = (number of unique states in table) / (total state space size).
      Higher coverage increases success probability but requires more memory.
    
    **Mathematical Foundation**:
    
    A Hellman table consists of m chains, each of length t. The table covers
    approximately m·t states (with some overlap). The time-memory trade-off is:
    
    .. math::
    
       TM^2 = N^2
    
    where:
    - T is the time for online attack
    - M is the memory (table size)
    - N is the state space size (q^d for LFSR of degree d over GF(q))
    
    **Algorithm**:
    
    1. **Precomputation Phase**:
       - Generate m random starting states
       - For each starting state, compute a chain of length t
       - Store only (start_state, end_state) pairs where end_state is
         distinguished
       - Repeat until m chains with distinguished endpoints are created
    
    2. **Lookup Phase**:
       - Given target state S, apply reduction function: R(S)
       - Check if R(S) is a chain endpoint in table
       - If found, reconstruct chain from start to find S
       - If not found, apply f then R repeatedly (up to t times)
    
    **Advantages**:
    
    - Faster state recovery after precomputation
    - Can attack multiple targets using same table
    - Demonstrates practical attack scenarios
    
    **Limitations**:
    
    - Requires significant memory for large state spaces
    - Precomputation can be time-consuming
    - False alarms require verification
    - Coverage may be incomplete
    
    Attributes:
        chain_count: Number of chains in the table
        chain_length: Length of each chain
        chains: List of (start_state, end_state) pairs
        reduction_function: Function mapping states to starting points
        distinguished_point_test: Function to test if state is distinguished
    """
    
    def __init__(
        self,
        chain_count: int,
        chain_length: int,
        distinguished_bits: int = 8
    ):
        """
        Initialize Hellman table.
        
        Args:
            chain_count: Number of chains to generate
            chain_length: Length of each chain
            distinguished_bits: Number of leading zero bits for distinguished points
        """
        self.chain_count = chain_count
        self.chain_length = chain_length
        self.distinguished_bits = distinguished_bits
        self.chains: List[Tuple[List[int], List[int]]] = []
        self.reduction_function: Optional[Callable] = None
        self.distinguished_point_test: Optional[Callable] = None
    
    def _is_distinguished_point(self, state: List[int]) -> bool:
        """
        Check if state is a distinguished point.
        
        A distinguished point has leading distinguished_bits bits equal to 0.
        """
        if not state:
            return False
        # Check if first distinguished_bits bits are zero
        bits_to_check = min(self.distinguished_bits, len(state))
        return all(state[i] == 0 for i in range(bits_to_check))
    
    def _reduction_function(self, state: List[int], field_order: int) -> List[int]:
        """
        Reduction function: maps state to a starting point.
        
        Uses a hash-based approach to create a pseudo-random mapping.
        """
        # Convert state to bytes for hashing
        state_bytes = bytes(str(state).encode('utf-8'))
        hash_obj = hashlib.sha256(state_bytes)
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # Map hash to state space
        state_size = field_order ** len(state)
        mapped_value = hash_int % state_size
        
        # Convert back to state representation
        result = []
        temp = mapped_value
        for _ in range(len(state)):
            result.append(temp % field_order)
            temp //= field_order
        
        return result
    
    def generate(
        self,
        lfsr_config: LFSRConfig,
        max_attempts: int = 10000
    ) -> None:
        """
        Generate Hellman table for given LFSR configuration.
        
        Args:
            lfsr_config: LFSR configuration
            max_attempts: Maximum attempts to find distinguished points
        """
        from lfsr.core import build_state_update_matrix
        
        F = GF(lfsr_config.field_order)
        d = lfsr_config.degree
        
        # Build state update matrix
        C, CS = build_state_update_matrix(lfsr_config.coefficients, lfsr_config.field_order)
        
        self.chains = []
        attempts = 0
        
        while len(self.chains) < self.chain_count and attempts < max_attempts:
            attempts += 1
            
            # Generate random starting state
            start_state = [F(random.randint(0, lfsr_config.field_order - 1)) for _ in range(d)]
            start_state_vec = vector(F, start_state)
            
            # Compute chain
            current_state = start_state_vec
            found_distinguished = False
            
            for step in range(self.chain_length):
                # Update state
                current_state = C * current_state
                
                # Check if distinguished point
                state_list = [int(x) for x in current_state]
                if self._is_distinguished_point(state_list):
                    # Store chain (start, end)
                    start_list = [int(x) for x in start_state]
                    self.chains.append((start_list, state_list))
                    found_distinguished = True
                    break
            
            if not found_distinguished:
                # Store chain anyway (end state is last state)
                start_list = [int(x) for x in start_state]
                end_list = [int(x) for x in current_state]
                self.chains.append((start_list, end_list))
    
    def lookup(
        self,
        target_state: List[int],
        lfsr_config: LFSRConfig
    ) -> Optional[List[int]]:
        """
        Lookup target state in Hellman table.
        
        Args:
            target_state: State to recover
            lfsr_config: LFSR configuration
        
        Returns:
            Recovered initial state if found, None otherwise
        """
        from lfsr.core import build_state_update_matrix
        
        F = GF(lfsr_config.field_order)
        C, CS = build_state_update_matrix(lfsr_config.coefficients, lfsr_config.field_order)
        
        # Try to find target in chains
        target_vec = vector(F, target_state)
        
        # Check if target is a chain endpoint
        target_list = target_state
        for start, end in self.chains:
            if end == target_list:
                # Reconstruct chain to find target
                start_vec = vector(F, start)
                current = start_vec
                
                for _ in range(self.chain_length):
                    if list(current) == target_list:
                        return start
                    current = C * current
        
        # Try reduction function approach
        # Apply reduction to target and check if result is endpoint
        reduced = self._reduction_function(target_state, lfsr_config.field_order)
        for start, end in self.chains:
            if end == reduced:
                # Reconstruct chain
                start_vec = vector(F, start)
                current = start_vec
                
                for _ in range(self.chain_length):
                    if list(current) == target_state:
                        return start
                    current = C * current
        
        return None


class RainbowTable:
    """
    Rainbow table for time-memory trade-off attacks.
    
    A **rainbow table** is an improved version of Hellman tables that uses
    different reduction functions at each step, reducing collisions. Introduced
    by Philippe Oechslin (2003), rainbow tables are more efficient than
    Hellman tables for the same memory usage.
    
    **Key Terminology**:
    
    - **Rainbow Table**: A precomputed table using different reduction
      functions at each step (like colors in a rainbow). This reduces collisions
      compared to Hellman tables, which use the same reduction function.
    
    - **Rainbow Chain**: A chain where each step uses a different reduction
      function R_1, R_2, ..., R_t. The chain is: S_0 → f(S_0) → R_1(f(S_0))
      → f(R_1(f(S_0))) → R_2(f(R_1(f(S_0)))) → ...
    
    - **Reduction Function Family**: A set of t different reduction functions
      {R_1, R_2, ..., R_t}, one for each step in the chain. Each function
      maps states to starting points, but they differ to reduce collisions.
    
    - **Collision Resistance**: Rainbow tables have fewer collisions than
      Hellman tables because different reduction functions are used at each
      step. This means fewer false alarms and more efficient tables.
    
    - **Table Lookup**: Similar to Hellman tables, but must try all reduction
      functions in reverse order. For target state S, we check R_t(S), R_{t-1}(f(S)),
      R_{t-2}(f^2(S)), etc.
    
    **Mathematical Foundation**:
    
    Rainbow tables use t different reduction functions. A chain of length t is:
    
    .. math::
    
       S_0 \\rightarrow f(S_0) \\rightarrow R_1(f(S_0)) \\rightarrow f(R_1(f(S_0))) \\rightarrow \\ldots
    
    This reduces collisions because merging chains requires collisions at the
    same step with the same reduction function, which is less likely.
    
    **Advantages over Hellman Tables**:
    
    - Fewer collisions (more efficient)
    - Better coverage for same memory
    - Simpler lookup (no need to check all chains at each step)
    
    **Limitations**:
    
    - Still requires significant memory
    - Precomputation can be time-consuming
    - Lookup requires trying all reduction functions
    
    Attributes:
        chain_count: Number of chains in the table
        chain_length: Length of each chain
        chains: List of (start_state, end_state) pairs
        reduction_functions: List of reduction functions (one per step)
    """
    
    def __init__(
        self,
        chain_count: int,
        chain_length: int,
        distinguished_bits: int = 8
    ):
        """
        Initialize Rainbow table.
        
        Args:
            chain_count: Number of chains to generate
            chain_length: Length of each chain
            distinguished_bits: Number of leading zero bits for distinguished points
        """
        self.chain_count = chain_count
        self.chain_length = chain_length
        self.distinguished_bits = distinguished_bits
        self.chains: List[Tuple[List[int], List[int]]] = []
        self.reduction_functions: List[Callable] = []
    
    def _is_distinguished_point(self, state: List[int]) -> bool:
        """Check if state is a distinguished point."""
        if not state:
            return False
        bits_to_check = min(self.distinguished_bits, len(state))
        return all(state[i] == 0 for i in range(bits_to_check))
    
    def _create_reduction_function(self, step: int, field_order: int, state_size: int) -> Callable:
        """
        Create a reduction function for a specific step.
        
        Each step uses a different reduction function to reduce collisions.
        """
        def reduction_func(state: List[int]) -> List[int]:
            # Use step number to create different hash
            state_bytes = bytes(str(state) + str(step)).encode('utf-8')
            hash_obj = hashlib.sha256(state_bytes)
            hash_int = int(hash_obj.hexdigest(), 16)
            
            mapped_value = (hash_int + step) % state_size
            
            result = []
            temp = mapped_value
            for _ in range(len(state)):
                result.append(temp % field_order)
                temp //= field_order
            
            return result
        
        return reduction_func
    
    def generate(
        self,
        lfsr_config: LFSRConfig,
        max_attempts: int = 10000
    ) -> None:
        """
        Generate Rainbow table for given LFSR configuration.
        
        Args:
            lfsr_config: LFSR configuration
            max_attempts: Maximum attempts to find distinguished points
        """
        from lfsr.core import build_state_update_matrix
        
        F = GF(lfsr_config.field_order)
        d = lfsr_config.degree
        state_size = lfsr_config.field_order ** d
        
        # Build state update matrix
        C, CS = build_state_update_matrix(lfsr_config.coefficients, lfsr_config.field_order)
        
        # Create reduction functions for each step
        self.reduction_functions = [
            self._create_reduction_function(i, lfsr_config.field_order, state_size)
            for i in range(self.chain_length)
        ]
        
        self.chains = []
        attempts = 0
        
        while len(self.chains) < self.chain_count and attempts < max_attempts:
            attempts += 1
            
            # Generate random starting state
            start_state = [F(random.randint(0, lfsr_config.field_order - 1)) for _ in range(d)]
            start_state_vec = vector(F, start_state)
            
            # Compute rainbow chain
            current_state = start_state_vec
            found_distinguished = False
            
            for step in range(self.chain_length):
                # Update state
                current_state = C * current_state
                
                # Apply reduction function for this step
                state_list = [int(x) for x in current_state]
                reduced = self.reduction_functions[step](state_list)
                current_state = vector(F, reduced)
                
                # Check if distinguished point
                if self._is_distinguished_point(state_list):
                    start_list = [int(x) for x in start_state]
                    self.chains.append((start_list, state_list))
                    found_distinguished = True
                    break
            
            if not found_distinguished:
                # Store chain anyway
                start_list = [int(x) for x in start_state]
                end_list = [int(x) for x in current_state]
                self.chains.append((start_list, end_list))
    
    def lookup(
        self,
        target_state: List[int],
        lfsr_config: LFSRConfig
    ) -> Optional[List[int]]:
        """
        Lookup target state in Rainbow table.
        
        Args:
            target_state: State to recover
            lfsr_config: LFSR configuration
        
        Returns:
            Recovered initial state if found, None otherwise
        """
        from lfsr.core import build_state_update_matrix
        
        F = GF(lfsr_config.field_order)
        C, CS = build_state_update_matrix(lfsr_config.coefficients, lfsr_config.field_order)
        
        target_list = target_state
        
        # Try all reduction functions in reverse order
        for step in range(self.chain_length - 1, -1, -1):
            # Compute state at this step
            current = vector(F, target_list)
            
            # Work backwards to step
            for _ in range(self.chain_length - 1 - step):
                # This is simplified - full implementation would properly
                # work backwards through the chain
                pass
            
            # Apply reduction function for this step
            reduced = self.reduction_functions[step](target_list)
            
            # Check if reduced state is an endpoint
            for start, end in self.chains:
                if end == reduced:
                    # Reconstruct chain
                    start_vec = vector(F, start)
                    current = start_vec
                    
                    for s in range(self.chain_length):
                        if list(current) == target_list:
                            return start
                        current = C * current
                        if s < len(self.reduction_functions) - 1:
                            state_list = [int(x) for x in current]
                            reduced_state = self.reduction_functions[s](state_list)
                            current = vector(F, reduced_state)
        
        return None


def tmto_attack(
    lfsr_config: LFSRConfig,
    target_state: List[int],
    method: str = "hellman",
    chain_count: int = 1000,
    chain_length: int = 100,
    precomputed_table: Optional[Any] = None
) -> TMTOAttackResult:
    """
    Perform time-memory trade-off attack on LFSR.
    
    This function performs a TMTO attack using either Hellman tables or
    Rainbow tables to recover the initial state from an observed state.
    
    **Key Terminology**:
    
    - **Time-Memory Trade-Off (TMTO)**: A cryptanalytic technique that
      precomputes tables to enable faster attacks. The trade-off is between
      precomputation time/memory and online attack time.
    
    - **Precomputation**: The initial phase where tables are generated. This
      is done once and can be reused for multiple attacks.
    
    - **Online Attack**: The phase where the precomputed table is used to
      recover states. This is much faster than computing states on-demand.
    
    Args:
        lfsr_config: LFSR configuration
        target_state: Observed state to recover initial state from
        method: TMTO method ("hellman" or "rainbow")
        chain_count: Number of chains in table
        chain_length: Length of each chain
        precomputed_table: Optional precomputed table (if None, generates new)
    
    Returns:
        TMTOAttackResult with attack results
    
    Example:
        >>> from lfsr.attacks import LFSRConfig
        >>> from lfsr.tmto import tmto_attack
        >>> 
        >>> lfsr = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
        >>> target = [1, 0, 1, 1]
        >>> result = tmto_attack(lfsr, target, method="hellman")
        >>> if result.attack_successful:
        ...     print(f"Recovered state: {result.recovered_state}")
    """
    import time
    
    start_time = time.perf_counter()
    
    # Generate or use precomputed table
    if precomputed_table is None:
        if method == "hellman":
            table = HellmanTable(chain_count, chain_length)
        elif method == "rainbow":
            table = RainbowTable(chain_count, chain_length)
        else:
            return TMTOAttackResult(
                attack_successful=False,
                recovered_state=None,
                method_used=method,
                table_size=0,
                lookup_time=0.0,
                precomputation_time=0.0,
                coverage=0.0,
                details={'error': f'Unknown method: {method}'}
            )
        
        table.generate(lfsr_config)
        precomputation_time = time.perf_counter() - start_time
    else:
        table = precomputed_table
        precomputation_time = 0.0  # Already precomputed
    
    # Perform lookup
    lookup_start = time.perf_counter()
    recovered_state = table.lookup(target_state, lfsr_config)
    lookup_time = time.perf_counter() - lookup_start
    
    # Compute coverage
    state_space_size = lfsr_config.field_order ** lfsr_config.degree
    table_size = len(table.chains) * chain_length
    coverage = min(1.0, table_size / state_space_size) if state_space_size > 0 else 0.0
    
    attack_successful = recovered_state is not None
    
    return TMTOAttackResult(
        attack_successful=attack_successful,
        recovered_state=recovered_state,
        method_used=method,
        table_size=len(table.chains),
        lookup_time=lookup_time,
        precomputation_time=precomputation_time,
        coverage=coverage,
        details={
            'chain_count': len(table.chains),
            'chain_length': chain_length,
            'state_space_size': state_space_size
        }
    )


def optimize_tmto_parameters(
    state_space_size: int,
    available_memory: int,
    target_success_probability: float = 0.5
) -> Dict[str, Any]:
    """
    Optimize TMTO parameters for given constraints.
    
    Finds optimal chain_count and chain_length to maximize success probability
    given memory constraints.
    
    **Key Terminology**:
    
    - **Trade-Off Curve**: A graph showing the relationship between time and
      memory for different parameter choices. The curve shows how increasing
      memory reduces attack time (and vice versa).
    
    - **Optimal Parameters**: Parameter values that minimize the time×memory
      product for a given success probability. These parameters provide the
      best trade-off between time and memory.
    
    - **Coverage**: The fraction of state space covered by the table.
      Coverage = (table_size) / (state_space_size). Higher coverage increases
      success probability.
    
    - **Success Probability**: The probability that a random state can be
      recovered from the table. This depends on coverage and collision rate.
    
    Args:
        state_space_size: Size of the state space (q^d for LFSR)
        available_memory: Available memory (number of states that can be stored)
        target_success_probability: Target success probability (default: 0.5)
    
    Returns:
        Dictionary with optimized parameters:
        - chain_count: Optimal number of chains
        - chain_length: Optimal chain length
        - estimated_coverage: Estimated coverage
        - estimated_success_prob: Estimated success probability
        - time_memory_product: T×M product
    """
    # Simplified optimization
    # Full implementation would use more sophisticated algorithms
    
    # Try different parameter combinations
    best_params = None
    best_product = float('inf')
    
    # Search space: chain_count * chain_length <= available_memory
    for chain_count in [100, 500, 1000, 5000]:
        chain_length = available_memory // chain_count
        if chain_length < 1:
            continue
        
        coverage = min(1.0, (chain_count * chain_length) / state_space_size)
        
        # Estimate success probability (simplified)
        success_prob = coverage * (1 - coverage / 2)  # Rough estimate
        
        if success_prob >= target_success_probability:
            # Estimate time (simplified)
            time_estimate = chain_length  # Lookup time
            memory_estimate = chain_count  # Memory usage
            product = time_estimate * memory_estimate
            
            if product < best_product:
                best_product = product
                best_params = {
                    'chain_count': chain_count,
                    'chain_length': chain_length,
                    'estimated_coverage': coverage,
                    'estimated_success_prob': success_prob,
                    'time_memory_product': product
                }
    
    if best_params is None:
        # Return default parameters
        chain_count = min(1000, available_memory // 100)
        chain_length = available_memory // chain_count if chain_count > 0 else 100
        
        return {
            'chain_count': chain_count,
            'chain_length': chain_length,
            'estimated_coverage': min(1.0, (chain_count * chain_length) / state_space_size),
            'estimated_success_prob': 0.0,
            'time_memory_product': chain_count * chain_length
        }
    
    return best_params
