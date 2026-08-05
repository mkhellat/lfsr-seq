#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cross-checks against third-party LFSR libraries (PyLFSR, lfsr-tools).

**Scope**: GF(2) only. Both third-party packages hardcode binary XOR
logic (confirmed by reading their installed source: no field-size
parameter exists anywhere in either package), so they can validate this
project's GF(2) code paths but say nothing about its GF(q) support for
q > 2 -- which is this project's actual differentiator from every
comparable tool (see the "Comparison to Other Tools" section in
README.md / docs/index.rst). Treat a pass here as "our GF(2) behavior
agrees with two independent implementations," not as general
correctness proof.

**Package quality notes** (so failures here are triaged correctly):
- PyLFSR (PyPI: ``pylfsr``) is actively maintained, has properly
  declared dependencies, and its own primitivity check is only a
  heuristic (Golomb's randomness postulates) rather than a proof -- we
  don't rely on that here, only on its sequence/state generation.
- lfsr-tools (PyPI: ``lfsr-tools``) has real quality issues found while
  researching this cross-check: its installed package is missing a
  declared ``numpy`` dependency (works anyway if numpy happens to
  already be present), its ``BerlekampMassey`` constructor accepts
  ``poly_length``/``is_primitive`` arguments that are silently unused
  (dead parameters, despite what the docstring implies), and its own
  README and its own source docstring give *contradictory* endianness
  descriptions for the identical example. The convention documented
  below was resolved empirically (by tracing the actual arithmetic and
  cross-validating against PyLFSR's independently-agreeing output), not
  by trusting either of lfsr-tools' own conflicting descriptions.

**Coefficient convention mapping** (verified against 3 independent test
vectors -- see git history of this file for the derivation):

- ``lfsr-seq`` coefficients ``[c0, c1, ..., c_{d-1}]`` (as passed to
  ``build_state_update_matrix``) correspond to PyLFSR's
  ``fpoly=[d] + [i for i in range(1, d) if coeffs[i] == 1]`` -- i.e.
  PyLFSR's Fibonacci tap index ``i`` (1-indexed, degree-style) equals
  our coefficient array index ``i`` for ``coeffs[1:]``. ``c0`` is
  always 1 (implicit constant term) and is not itself a PyLFSR tap.
- The two systems' **state trajectories are reverse-direction
  traversals of the same cycle**: starting both at the same state,
  ``lfsr-seq``'s trajectory reversed (excluding the shared starting
  state) equals PyLFSR's Fibonacci trajectory, for every case checked.
  This is a real, explainable structural relationship (each system's
  step matrix is essentially the other's inverse on the cycle), not an
  error in either tool -- and it's why this test compares *sets of
  visited states* and *period*, not step-by-step output bit sequences,
  which would require additionally accounting for the direction
  reversal and the specific output-tap position PyLFSR reads from.
- lfsr-tools' ``poly`` array uses ``poly[i]`` = coefficient of x^i,
  **including the leading (degree-d) coefficient**, which is always 1
  and always present as the final entry. ``lfsr-seq``'s own ``coeffs``
  list never stores that implicit leading 1 (its characteristic
  polynomial is ``t^d - (c_{d-1} t^{d-1} + ... + c0)``, with the ``t^d``
  coefficient never itself in the array).
  When the *observed sequence fed to Berlekamp-Massey* comes from
  PyLFSR's own generation, lfsr-tools recovers exactly
  ``lfsr_seq_coeffs + [1]``. But when the observed sequence instead
  comes from ``lfsr-seq``'s own state trajectory (this module's
  primary object under test), Berlekamp-Massey recovers the
  **reciprocal** of that polynomial -- ``(lfsr_seq_coeffs +
  [1])[::-1]`` -- because (per the state-trajectory reversal already
  established above) lfsr-seq's own trajectory traverses the same
  cycle in the opposite direction from PyLFSR's, and a connection
  polynomial recovered from a time-reversed sequence is the reciprocal
  polynomial of the one recovered from the forward sequence. Verified
  directly: for coeffs ``[1,0,0,1]``, BM against lfsr-seq's own
  generated sequence recovers ``[1,1,0,0,1]``, which is exactly
  ``[1,0,0,1,1][::-1]``.
"""

import io

import pytest

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

pylfsr = pytest.importorskip(
    "pylfsr", reason="pylfsr not installed (pip install lfsr-seq[cross-check])"
)
lfsr_tools = pytest.importorskip(
    "lfsr_tools", reason="lfsr-tools not installed (pip install lfsr-seq[cross-check])"
)

from lfsr.analysis import lfsr_sequence_mapper
from lfsr.core import build_state_update_matrix


def _coeffs_to_pylfsr_fpoly(coeffs):
    """Map lfsr-seq coefficients to PyLFSR's fpoly tap-position list.

    See this module's docstring for the derivation and verification.
    """
    d = len(coeffs)
    taps = [d] + [i for i in range(1, d) if coeffs[i] == 1]
    return sorted(taps, reverse=True)


def _lfsr_seq_states_and_period(coeffs, gf_order, start_tuple):
    """Return (list of visited state tuples, period) from lfsr-seq's own matrix."""
    C, _ = build_state_update_matrix(coeffs, gf_order)
    V = VectorSpace(GF(gf_order), len(coeffs))
    start_state = None
    for v in V:
        if tuple(v) == start_tuple:
            start_state = v
            break
    assert start_state is not None, f"start state {start_tuple} not found in state space"

    seq_dict, period_dict, max_period, periods_sum = lfsr_sequence_mapper(
        C, V, gf_order, io.StringIO(), no_progress=True
    )

    # Walk the trajectory ourselves too, to get the actual visited-state set
    # for the cycle containing start_tuple (lfsr_sequence_mapper doesn't
    # expose "which sequence did this specific start_tuple land in" directly
    # in a convenient form for this comparison).
    states = []
    s = start_state
    seen = set()
    while tuple(s) not in seen:
        seen.add(tuple(s))
        states.append(tuple(s))
        s = s * C
    return states, len(states)


# (coeffs, expected max period, is primitive) -- all three independently
# verified earlier via SageMath's is_irreducible()/is_primitive_polynomial(),
# the elementary factor theorem, and (for [1,0,0,1] specifically) a
# from-scratch GF(2) polynomial long-division script with no SageMath or
# project code involved.
PRIMITIVE_CASES = [
    ([1, 0, 0, 1], 15),  # x^4+x^3+1, primitive
    ([1, 1, 0, 0], 15),  # x^4+x+1, primitive
]
NON_PRIMITIVE_IRREDUCIBLE_CASES = [
    ([1, 1, 1, 1], 5),  # x^4+x^3+x^2+x+1, irreducible but not primitive (order 5)
]


@pytest.mark.parametrize("coeffs,expected_period", PRIMITIVE_CASES + NON_PRIMITIVE_IRREDUCIBLE_CASES)
def test_state_trajectory_matches_pylfsr(coeffs, expected_period):
    """lfsr-seq's visited-state cycle matches PyLFSR's, reversed (see module docstring)."""
    start_tuple = (1,) + (0,) * (len(coeffs) - 1)

    lfsr_seq_states, lfsr_seq_period = _lfsr_seq_states_and_period(coeffs, 2, start_tuple)
    assert lfsr_seq_period == expected_period

    fpoly = _coeffs_to_pylfsr_fpoly(coeffs)
    L = pylfsr.LFSR(fpoly=fpoly, initstate=list(start_tuple), conf="fibonacci")
    pylfsr_states = []
    for _ in range(expected_period):
        pylfsr_states.append(tuple(int(x) for x in L.state))
        L.next()

    assert len(pylfsr_states) == len(lfsr_seq_states)

    # Reverse-direction traversal of the same cycle (see module docstring):
    # same starting state, remaining states visited in the opposite order.
    reversed_lfsr_seq = lfsr_seq_states[:1] + lfsr_seq_states[1:][::-1]
    assert reversed_lfsr_seq == pylfsr_states, (
        f"lfsr-seq states (reversed) {reversed_lfsr_seq} != "
        f"PyLFSR states {pylfsr_states} for coeffs={coeffs}, fpoly={fpoly}"
    )


@pytest.mark.parametrize("coeffs,expected_period", PRIMITIVE_CASES)
def test_period_matches_pylfsr_full_period(coeffs, expected_period):
    """lfsr-seq's period for a primitive polynomial matches PyLFSR's runFullPeriod() length."""
    fpoly = _coeffs_to_pylfsr_fpoly(coeffs)
    start_tuple = (1,) + (0,) * (len(coeffs) - 1)
    L = pylfsr.LFSR(fpoly=fpoly, initstate=list(start_tuple), conf="fibonacci")
    full_period_seq = L.runFullPeriod()

    assert len(full_period_seq) == expected_period

    _, lfsr_seq_period = _lfsr_seq_states_and_period(coeffs, 2, start_tuple)
    assert lfsr_seq_period == expected_period == len(full_period_seq)


@pytest.mark.parametrize("coeffs", [c for c, _ in PRIMITIVE_CASES + NON_PRIMITIVE_IRREDUCIBLE_CASES])
def test_berlekamp_massey_recovers_lfsr_tools_connection_polynomial(coeffs):
    """lfsr-tools' Berlekamp-Massey recovers the reciprocal connection
    polynomial from a sequence generated by lfsr-seq's own state update
    matrix (see module docstring for why it's the reciprocal, not the
    polynomial itself, when the observed sequence is lfsr-seq's own).
    """
    d = len(coeffs)
    start_tuple = (1,) + (0,) * (d - 1)
    states, period = _lfsr_seq_states_and_period(coeffs, 2, start_tuple)

    # Use the last register cell as the observed output bit, generating
    # enough of the (periodic) sequence for Berlekamp-Massey to have more
    # than enough samples (2x the true linear complexity is sufficient;
    # for a degree-d polynomial that's well under 2*d + a few cycles).
    num_samples = max(4 * d, 3 * period)
    full_trace = (states * (num_samples // period + 1))[:num_samples]
    observed_seq = [s[-1] for s in full_trace]

    bm = lfsr_tools.BerlekampMassey(observed_seq)
    recovered = list(int(x) for x in bm.estimate_polynomial())
    expected = (coeffs + [1])[::-1]

    assert recovered == expected, (
        f"lfsr-tools recovered {recovered}, expected the reciprocal of "
        f"lfsr-seq's coeffs {coeffs} plus the implicit leading term -> {expected}"
    )
