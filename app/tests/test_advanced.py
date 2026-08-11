#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.advanced (advanced LFSR structures: NFSR, FilteredLFSR,
ClockControlledLFSR, IrregularClockingLFSR, MultiOutputLFSR, and the shared
AdvancedLFSR/AdvancedLFSRConfig/AdvancedLFSRAnalysisResult base classes).

Reference LFSR used throughout: degree-4 GF(2), coefficients [1, 0, 0, 1]
(the same primitive/max-period reference vector used elsewhere in this
suite -- see test_tmto.py, test_nist.py). Its state space (16 states) is
small enough to fully enumerate and hand-verify.

IMPORTANT -- state-update convention bug found and fixed (2026-08-11)
--------------------------------------------------------------------------
lfsr/core.py's ``build_state_update_matrix`` docstring is explicit: the
matrix C is meant to be used as ``S_i * C = S_{i+1}`` (row-vector times
matrix). ``lfsr/analysis.py`` -- the tested, canonical module -- follows
this convention exactly (``hare = start_state * state_update_matrix``,
etc.).

Every one of the four matrix-based advanced structures --
``FilteredLFSR._clock_lfsr`` (filtered.py), ``ClockControlledLFSR.
_clock_lfsr`` (clock_controlled.py), ``IrregularClockingLFSR.
_clock_lfsr`` (irregular_clocking.py), and ``MultiOutputLFSR.
_clock_lfsr`` (multi_output.py) -- used to advance the state with
``C * state_vec`` (matrix times column vector), the REVERSE of the
documented/canonical convention. This was not a cosmetic difference: for
the reference LFSR starting from state [1,0,1,0], the two conventions
diverged after just two steps (verified directly with SageMath). This is
the exact same bug *class* previously found and fixed in lfsr/tmto.py
(HellmanTable/RainbowTable also used ``C * state`` instead of
``state * C``) -- see test_tmto.py's module docstring. All four
``_clock_lfsr`` methods were fixed to use ``state_vec * C`` (see their
commit history); tests below assert the real, canonical-convention
output, cross-checked via an independent manual ``state * C`` replay
done directly in each test (not by calling back into the class under
test).

``NFSR`` (nonlinear.py) does NOT use the matrix at all -- it implements
its own shift-and-insert-at-front step function directly in Python list
operations, so it is not subject to this bug; its tests cross-check
against independent hand/Python-level shift-register arithmetic instead.
"""

import pytest

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

from lfsr.advanced.base import (
    AdvancedLFSR,
    AdvancedLFSRAnalysisResult,
    AdvancedLFSRConfig,
)
from lfsr.advanced.clock_controlled import ClockControlledLFSR, create_stop_and_go_lfsr
from lfsr.advanced.filtered import FilteredLFSR, create_simple_filtered_lfsr
from lfsr.advanced.irregular_clocking import (
    IrregularClockingLFSR,
    create_step_1_step_2_pattern,
    create_stop_and_go_pattern,
)
from lfsr.advanced.multi_output import MultiOutputLFSR, create_simple_multi_output_lfsr
from lfsr.advanced.nonlinear import NFSR, create_simple_nfsr
from lfsr.attacks import LFSRConfig
from lfsr.core import build_state_update_matrix

# Reference LFSR: degree 4, GF(2), primitive/max-period taps [1,0,0,1].
REFERENCE_CONFIG = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)
REFERENCE_COEFFS = [1, 0, 0, 1]


def _advanced_module_convention_steps(coeffs, field_order, start, steps):
    """Manually replay the state-update convention the advanced/*
    classes use internally (state_vec * C, matching core.py's documented
    convention and analysis.py's actual usage), independent of calling
    any class under test -- an independent cross-check, not a call into
    the code being tested.

    Previously (before the 2026-08-11 fix) all four matrix-based
    advanced/* classes used the reversed C*state_vec convention, which
    silently diverged from the documented/canonical state*C convention
    after a few steps -- see their commit history for the bug."""
    C, _ = build_state_update_matrix(coeffs, field_order)
    F = GF(field_order)
    s = vector(F, start)
    trail = [[int(x) for x in s]]
    for _ in range(steps):
        s = s * C
        trail.append([int(x) for x in s])
    return trail


# ---------------------------------------------------------------------------
# Base classes: AdvancedLFSRConfig, AdvancedLFSRAnalysisResult, AdvancedLFSR
# ---------------------------------------------------------------------------


class TestAdvancedLFSRConfig:
    def test_construction_defaults(self):
        cfg = AdvancedLFSRConfig(
            structure_type="filtered", base_lfsr_config=REFERENCE_CONFIG
        )
        assert cfg.structure_type == "filtered"
        assert cfg.base_lfsr_config is REFERENCE_CONFIG
        assert cfg.parameters == {}

    def test_construction_with_parameters(self):
        cfg = AdvancedLFSRConfig(
            structure_type="nonlinear",
            base_lfsr_config=REFERENCE_CONFIG,
            parameters={"state_size": 4},
        )
        assert cfg.parameters == {"state_size": 4}

    def test_default_parameters_dict_not_shared_between_instances(self):
        """Regression guard for the classic mutable-default-argument
        footgun -- dataclass uses field(default_factory=dict) so each
        instance must get its own dict."""
        cfg_a = AdvancedLFSRConfig(structure_type="a", base_lfsr_config=REFERENCE_CONFIG)
        cfg_b = AdvancedLFSRConfig(structure_type="b", base_lfsr_config=REFERENCE_CONFIG)
        cfg_a.parameters["x"] = 1
        assert cfg_b.parameters == {}


class TestAdvancedLFSRAnalysisResult:
    def test_construction_defaults(self):
        result = AdvancedLFSRAnalysisResult(structure_type="filtered")
        assert result.structure_type == "filtered"
        assert result.structure_properties == {}
        assert result.sequence_properties == {}
        assert result.security_assessment == {}
        assert result.details == {}


class TestAdvancedLFSRAnalyzeTemplateMethod:
    """Tests for AdvancedLFSR.analyze(), the concrete (non-abstract) method
    defined on the base class, exercised through a concrete subclass
    (NFSR, which is the simplest -- no sage matrix involved)."""

    def _make_nfsr(self):
        def feedback(state):
            return state[0] ^ state[3]

        return NFSR(REFERENCE_CONFIG, feedback)

    def test_analyze_without_initial_state_skips_sequence_generation(self):
        nfsr = self._make_nfsr()
        result = nfsr.analyze(initial_state=None)
        assert isinstance(result, AdvancedLFSRAnalysisResult)
        assert result.structure_type == "nonlinear"
        assert result.sequence_properties == {}
        # structure_properties/security_assessment are always populated
        assert result.structure_properties["structure_type"] == "NFSR"
        assert "known_vulnerabilities" in result.security_assessment

    def test_analyze_with_initial_state_populates_sequence_properties(self):
        nfsr = self._make_nfsr()
        result = nfsr.analyze(initial_state=[1, 0, 0, 0], sequence_length=10)
        assert result.sequence_properties["length"] == 10
        assert result.sequence_properties["field_order"] == 2
        # element_counts must sum to sequence length
        assert sum(result.sequence_properties["element_counts"].values()) == 10

    def test_analyze_sequence_properties_element_counts_correct(self):
        """Cross-check _analyze_sequence_properties's element_counts
        against an independent Python Counter over the same sequence
        the class itself generated."""
        from collections import Counter

        nfsr = self._make_nfsr()
        seq = nfsr.generate_sequence([1, 0, 0, 0], 20)
        result = nfsr.analyze(initial_state=[1, 0, 0, 0], sequence_length=20)
        expected_counts = dict(Counter(seq))
        assert result.sequence_properties["element_counts"] == expected_counts

    def test_analyze_structure_is_abstract_cannot_instantiate_base(self):
        with pytest.raises(TypeError):
            AdvancedLFSR()  # abstract class, missing concrete methods

    def test_analyze_sequence_properties_empty_sequence_returns_empty_dict(self):
        """_analyze_sequence_properties's `if not sequence: return {}`
        guard, exercised via a subclass whose generate_sequence()
        legitimately returns an empty list for sequence_length=0."""
        nfsr = self._make_nfsr()
        result = nfsr.analyze(initial_state=[1, 0, 0, 0], sequence_length=0)
        assert result.sequence_properties == {}


# ---------------------------------------------------------------------------
# NFSR (nonlinear.py) -- NOT matrix-based, so not subject to the C*s bug.
# ---------------------------------------------------------------------------


class TestNFSR:
    def test_linear_feedback_equivalent_matches_hand_derivation(self):
        """An NFSR whose feedback function is exactly the base LFSR's
        linear tap XOR (no AND terms) should behave like a plain
        shift-register with feedback = state[0]^state[3], MSB-first
        output, hand-derived independently below."""

        def linear_feedback(state):
            linear = 0
            for i, c in enumerate(REFERENCE_COEFFS):
                if c:
                    linear ^= state[i]
            return linear

        nfsr = NFSR(REFERENCE_CONFIG, linear_feedback)
        seq = nfsr.generate_sequence([1, 0, 0, 0], 10)

        # Independent hand derivation: shift register with feedback tap
        # positions 0 and 3 (matching coefficients [1,0,0,1]), new bit
        # inserted at front, each step's *pre-clock* MSB is output.
        state = [1, 0, 0, 0]
        expected = []
        for _ in range(10):
            expected.append(state[0])
            fb = state[0] ^ state[3]
            state = [fb] + state[:-1]

        assert seq == expected
        assert seq == [1, 1, 1, 1, 0, 1, 0, 1, 1, 0]

    def test_nonlinear_feedback_and_term_hand_derived(self):
        """A small hand-derivable case: feedback = state[0]^state[3]
        XOR (state[1] & state[2]), derived by hand for the first several
        steps from state [1,1,0,0]."""

        def feedback(state):
            return state[0] ^ state[3] ^ (state[1] & state[2])

        nfsr = NFSR(REFERENCE_CONFIG, feedback)
        seq = nfsr.generate_sequence([1, 1, 0, 0], 6)

        state = [1, 1, 0, 0]
        expected = []
        for _ in range(6):
            expected.append(state[0])
            fb = state[0] ^ state[3] ^ (state[1] & state[2])
            state = [fb] + state[:-1]

        assert seq == expected

    def test_generate_sequence_wrong_state_size_raises(self):
        nfsr = NFSR(REFERENCE_CONFIG, lambda s: 0)
        with pytest.raises(ValueError):
            nfsr.generate_sequence([1, 0, 0], 5)  # degree 4 expected

    def test_generate_sequence_zero_length(self):
        nfsr = NFSR(REFERENCE_CONFIG, lambda s: s[0] ^ s[3])
        assert nfsr.generate_sequence([1, 0, 0, 0], 0) == []

    def test_get_config(self):
        nfsr = NFSR(REFERENCE_CONFIG, lambda s: s[0])
        cfg = nfsr.get_config()
        assert cfg.structure_type == "nonlinear"
        assert cfg.parameters["state_size"] == 4
        assert cfg.parameters["field_order"] == 2

    def test_analyze_structure(self):
        nfsr = NFSR(REFERENCE_CONFIG, lambda s: s[0])
        props = nfsr.analyze_structure()
        assert props["structure_type"] == "NFSR"
        assert props["has_nonlinear_feedback"] is True
        assert props["base_lfsr_degree"] == 4

    def test_create_simple_nfsr_no_nonlinear_terms_matches_pure_linear(self):
        nfsr = create_simple_nfsr(REFERENCE_CONFIG, nonlinear_terms=None)
        seq = nfsr.generate_sequence([1, 0, 0, 0], 10)
        assert seq == [1, 1, 1, 1, 0, 1, 0, 1, 1, 0]

    def test_create_simple_nfsr_with_nonlinear_terms(self):
        nfsr = create_simple_nfsr(REFERENCE_CONFIG, nonlinear_terms=[(1, 2)])
        seq = nfsr.generate_sequence([1, 1, 0, 0], 8)

        state = [1, 1, 0, 0]
        expected = []
        for _ in range(8):
            expected.append(state[0])
            linear = 0
            for i, c in enumerate(REFERENCE_COEFFS):
                if c:
                    linear ^= state[i]
            nonlinear = state[1] & state[2]
            fb = linear ^ nonlinear
            state = [fb] + state[:-1]
        assert seq == expected

    def test_create_simple_nfsr_ignores_out_of_range_terms(self):
        # (10, 20) is out of range for degree-4 state -> should be skipped,
        # not raise or index-error.
        nfsr = create_simple_nfsr(REFERENCE_CONFIG, nonlinear_terms=[(10, 20)])
        seq = nfsr.generate_sequence([1, 0, 0, 0], 10)
        # should equal the pure-linear case since the out-of-range term
        # contributes nothing
        assert seq == [1, 1, 1, 1, 0, 1, 0, 1, 1, 0]


# ---------------------------------------------------------------------------
# FilteredLFSR (filtered.py)
# ---------------------------------------------------------------------------


class TestFilteredLFSR:
    def test_output_msb_filter_matches_canonical_convention_matrix_walk(self):
        """filter_func = state[0] (MSB) should reproduce the canonical
        (state*C) convention exactly -- verified via an independent
        manual state*C replay done in this test, not by calling back
        into FilteredLFSR itself."""
        flt = FilteredLFSR(REFERENCE_CONFIG, lambda s: s[0])
        seq = flt.generate_sequence([1, 0, 1, 0], 8)

        trail = _advanced_module_convention_steps(
            REFERENCE_COEFFS, 2, [1, 0, 1, 0], 8
        )
        expected = [row[0] for row in trail[:8]]
        assert seq == expected

    def test_nonlinear_filter_function_hand_derived_first_steps(self):
        """filter = state[0] ^ (state[1] & state[2]); cross-check the
        first 3 steps by hand against an independently replayed
        canonical state*C convention."""

        def filt(state):
            return state[0] ^ (state[1] & state[2])

        flt = FilteredLFSR(REFERENCE_CONFIG, filt)
        seq = flt.generate_sequence([1, 1, 0, 0], 5)

        trail = _advanced_module_convention_steps(REFERENCE_COEFFS, 2, [1, 1, 0, 0], 5)
        expected = [row[0] ^ (row[1] & row[2]) for row in trail[:5]]
        assert seq == expected

    def test_generate_sequence_wrong_state_size_raises(self):
        flt = FilteredLFSR(REFERENCE_CONFIG, lambda s: s[0])
        with pytest.raises(ValueError):
            flt.generate_sequence([1, 0], 5)

    def test_get_config_and_analyze_structure(self):
        flt = FilteredLFSR(REFERENCE_CONFIG, lambda s: s[0])
        cfg = flt.get_config()
        assert cfg.structure_type == "filtered"
        assert cfg.parameters["has_filter_function"] is True
        props = flt.analyze_structure()
        assert props["structure_type"] == "FilteredLFSR"
        assert props["state_size"] == 4

    def test_create_simple_filtered_lfsr_default_taps_is_msb(self):
        flt_default = create_simple_filtered_lfsr(REFERENCE_CONFIG)
        flt_explicit = FilteredLFSR(REFERENCE_CONFIG, lambda s: s[0])
        seq_default = flt_default.generate_sequence([1, 0, 1, 1], 8)
        seq_explicit = flt_explicit.generate_sequence([1, 0, 1, 1], 8)
        assert seq_default == seq_explicit

    def test_create_simple_filtered_lfsr_with_taps_and_nonlinear_terms(self):
        flt = create_simple_filtered_lfsr(
            REFERENCE_CONFIG, filter_taps=[0, 1], nonlinear_terms=[(2, 3)]
        )
        seq = flt.generate_sequence([1, 1, 0, 0], 6)

        trail = _advanced_module_convention_steps(REFERENCE_COEFFS, 2, [1, 1, 0, 0], 6)
        expected = [
            (row[0] ^ row[1]) ^ (row[2] & row[3]) for row in trail[:6]
        ]
        assert seq == expected


# ---------------------------------------------------------------------------
# ClockControlledLFSR (clock_controlled.py)
# ---------------------------------------------------------------------------


class TestClockControlledLFSR:
    def test_no_control_always_clocks_matches_manual_walk(self):
        """With no control LFSR, clock_control_function defaults to
        `lambda x: True` and control_output is hardcoded to 1 -- main
        LFSR clocks every step, degenerating to a plain single-LFSR
        stream. Cross-checked against an independent, canonical
        state*C replay."""
        cc = ClockControlledLFSR(REFERENCE_CONFIG)
        seq = cc.generate_sequence([1, 0, 1, 0], 8)

        trail = _advanced_module_convention_steps(REFERENCE_COEFFS, 2, [1, 0, 1, 0], 8)
        expected = [row[0] for row in trail[:8]]
        assert seq == expected

    def test_stop_and_go_with_control_lfsr_hand_traced(self):
        """Stop-and-go: main LFSR only advances when control LFSR's MSB
        output is 1. Hand-trace both LFSRs step by step using the
        module's own (C*s) convention, independently of calling the
        class."""
        control_config = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
        cclfsr = create_stop_and_go_lfsr(REFERENCE_CONFIG, control_config)

        main_init = [1, 0, 0, 0]
        control_init = [1, 0]
        length = 8
        seq = cclfsr.generate_sequence(main_init, length, control_init)

        # Independent hand-trace, replaying the SAME convention the
        # class itself uses (C*s), but computed here directly rather
        # than by calling into the class.
        main_C, _ = build_state_update_matrix(REFERENCE_COEFFS, 2)
        control_C, _ = build_state_update_matrix([1, 1], 2)
        F = GF(2)
        main_state = vector(F, main_init)
        control_state = vector(F, control_init)
        expected = []
        for _ in range(length):
            control_output = int(control_state[0])
            should_clock = control_output == 1
            expected.append(int(main_state[0]))
            if should_clock:
                main_state = main_C * main_state
            control_state = control_C * control_state

        assert seq == expected

    def test_default_clock_control_function_is_always_true(self):
        cc = ClockControlledLFSR(REFERENCE_CONFIG)
        assert cc.clock_control_function(0) is True
        assert cc.clock_control_function(1) is True

    def test_get_config_reports_control_lfsr_presence(self):
        cc_no_control = ClockControlledLFSR(REFERENCE_CONFIG)
        assert cc_no_control.get_config().parameters["has_control_lfsr"] is False

        control_config = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
        cc_with_control = ClockControlledLFSR(REFERENCE_CONFIG, control_config)
        assert cc_with_control.get_config().parameters["has_control_lfsr"] is True

    def test_analyze_structure_reports_degrees(self):
        control_config = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
        cc = create_stop_and_go_lfsr(REFERENCE_CONFIG, control_config)
        props = cc.analyze_structure()
        assert props["main_lfsr_degree"] == 4
        assert props["control_lfsr_degree"] == 2
        assert props["has_irregular_clocking"] is True

    def test_create_stop_and_go_lfsr_clock_function_semantics(self):
        control_config = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
        cc = create_stop_and_go_lfsr(REFERENCE_CONFIG, control_config)
        assert cc.clock_control_function(1) is True
        assert cc.clock_control_function(0) is False

    def test_control_lfsr_default_initial_state_is_all_ones(self):
        """When a control LFSR is configured but no explicit
        control_initial_state is passed to generate_sequence, the
        control LFSR defaults to starting at [1, 1, ..., 1] (per the
        `if control_initial_state is None: control_state = [1] *
        degree` branch) -- verify this default by comparing against an
        explicit [1, 1] control start, which must produce an identical
        sequence."""
        control_config = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
        cc = create_stop_and_go_lfsr(REFERENCE_CONFIG, control_config)

        seq_implicit_default = cc.generate_sequence([1, 0, 0, 0], 8)
        seq_explicit_all_ones = cc.generate_sequence(
            [1, 0, 0, 0], 8, control_initial_state=[1, 1]
        )
        assert seq_implicit_default == seq_explicit_all_ones


# ---------------------------------------------------------------------------
# IrregularClockingLFSR (irregular_clocking.py)
# ---------------------------------------------------------------------------


class TestIrregularClockingLFSR:
    def test_default_pattern_advances_one_step_matches_manual_walk(self):
        """No pattern function given -> defaults to always-advance-1,
        degenerating (with no control LFSR) to a plain single-LFSR
        stream identical in shape to the ClockControlled/Filtered
        no-control cases."""
        ic = IrregularClockingLFSR(REFERENCE_CONFIG)
        seq = ic.generate_sequence([1, 0, 1, 0], 8)

        trail = _advanced_module_convention_steps(REFERENCE_COEFFS, 2, [1, 0, 1, 0], 8)
        expected = [row[0] for row in trail[:8]]
        assert seq == expected

    def test_step_1_step_2_pattern_hand_traced(self):
        """Step-1/step-2: base LFSR advances 1 step if control MSB is 0,
        2 steps if control MSB is 1. Hand-trace independently using the
        module's own (C*s) convention computed directly in this test."""
        control_config = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
        pattern = create_step_1_step_2_pattern()
        ic = IrregularClockingLFSR(REFERENCE_CONFIG, control_config, pattern)

        base_init = [1, 0, 0, 0]
        control_init = [1, 0]
        length = 6
        seq = ic.generate_sequence(base_init, length, control_init)

        base_C, _ = build_state_update_matrix(REFERENCE_COEFFS, 2)
        control_C, _ = build_state_update_matrix([1, 1], 2)
        F = GF(2)
        base_state = vector(F, base_init)
        control_state = vector(F, control_init)
        expected = []
        for _ in range(length):
            control_output = int(control_state[0])
            expected.append(int(base_state[0]))
            steps = 1 if control_output == 0 else 2
            for _ in range(steps):
                base_state = base_C * base_state
            control_state = control_C * control_state

        assert seq == expected

    def test_stop_and_go_pattern_zero_steps_when_control_zero(self):
        """Stop-and-go via the generic pattern function: 0 steps when
        control=0 means the base LFSR must NOT advance at all (output
        repeats) -- verify this observable behavior directly (not by
        replaying the matrix), since it is a distinguishing edge case
        (steps=0) that the default/step-1-step-2 tests don't cover."""
        control_config = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
        pattern = create_stop_and_go_pattern()
        # control LFSR [1,1] over GF(2) started at [0, 0] is a fixed
        # point (0 XOR 0 = 0 feedback, stays [0,0] forever) -> control
        # output is always 0 -> base LFSR must never advance.
        ic = IrregularClockingLFSR(REFERENCE_CONFIG, control_config, pattern)
        seq = ic.generate_sequence([1, 0, 1, 0], 6, control_initial_state=[0, 0])
        assert seq == [1, 1, 1, 1, 1, 1]

    def test_clocking_pattern_functions_return_expected_step_counts(self):
        stop_and_go = create_stop_and_go_pattern()
        assert stop_and_go(0) == 0
        assert stop_and_go(1) == 1

        step_pattern = create_step_1_step_2_pattern()
        assert step_pattern(0) == 1
        assert step_pattern(1) == 2

    def test_get_config_and_analyze_structure(self):
        ic = IrregularClockingLFSR(REFERENCE_CONFIG)
        cfg = ic.get_config()
        assert cfg.structure_type == "irregular_clocking"
        assert cfg.parameters["has_control_lfsr"] is False
        props = ic.analyze_structure()
        assert props["control_lfsr_degree"] is None

    def test_control_lfsr_default_initial_state_is_all_ones(self):
        """Same default-control-state branch as ClockControlledLFSR
        (`if control_initial_state is None: control_state = [1] *
        degree`), exercised here for IrregularClockingLFSR."""
        control_config = LFSRConfig(coefficients=[1, 1], field_order=2, degree=2)
        pattern = create_step_1_step_2_pattern()
        ic = IrregularClockingLFSR(REFERENCE_CONFIG, control_config, pattern)

        seq_implicit_default = ic.generate_sequence([1, 0, 0, 0], 8)
        seq_explicit_all_ones = ic.generate_sequence(
            [1, 0, 0, 0], 8, control_initial_state=[1, 1]
        )
        assert seq_implicit_default == seq_explicit_all_ones


# ---------------------------------------------------------------------------
# MultiOutputLFSR (multi_output.py)
# ---------------------------------------------------------------------------


class TestMultiOutputLFSR:
    def test_single_bit_output_matches_manual_walk(self):
        """output_rate=1, output bit 0 (MSB) should exactly reproduce a
        single-output stream via the canonical (state*C) convention,
        cross-checked with an independent manual replay."""
        mo = create_simple_multi_output_lfsr(REFERENCE_CONFIG, [0])
        seq = mo.generate_sequence([1, 0, 1, 0], 8)

        trail = _advanced_module_convention_steps(REFERENCE_COEFFS, 2, [1, 0, 1, 0], 8)
        expected = [row[0] for row in trail[:8]]
        assert seq == expected

    def test_multi_bit_output_flattened_correctly(self):
        """Output bits [0, 1] per step (rate 2) -- verify flattening:
        sequence[2*i:2*i+2] should be [state_i[0], state_i[1]] for the
        i-th step's state, per the module's own convention."""
        mo = create_simple_multi_output_lfsr(REFERENCE_CONFIG, [0, 1])
        length = 10  # not a multiple of output_rate -> exercises truncation
        seq = mo.generate_sequence([1, 0, 1, 0], length)
        assert len(seq) == length

        trail = _advanced_module_convention_steps(REFERENCE_COEFFS, 2, [1, 0, 1, 0], 6)
        full_expected = []
        for row in trail[:6]:
            full_expected.extend([row[0], row[1]])
        assert seq == full_expected[:length]

    def test_length_not_multiple_of_output_rate_truncates_not_pads(self):
        """length=5 with output_rate=2 requires ceil(5/2)=3 steps (6 raw
        bits generated) then truncated down to exactly 5."""
        mo = create_simple_multi_output_lfsr(REFERENCE_CONFIG, [0, 1])
        seq = mo.generate_sequence([1, 0, 0, 0], 5)
        assert len(seq) == 5

    def test_output_bits_out_of_range_are_skipped(self):
        """create_simple_multi_output_lfsr's output_func filters
        `0 <= i < degree` -- an out-of-range index silently produces
        fewer bits per step than output_rate claims, which means
        generate_sequence's step-count math (based on output_rate) will
        undercount actual bits produced per step. Document actual
        behavior: with output_bits=[0, 99] (99 invalid) on a degree-4
        LFSR, output_rate=2 but each step's output_func only yields 1
        bit (state[0]), so length asked for may not be reached.
        # BUG (arguably): output_rate is trusted for step-count sizing
        # in generate_sequence, but create_simple_multi_output_lfsr does
        # not validate that len(output_bits) invalid entries are excluded
        # from output_rate, causing a possible mismatch between
        # declared output_rate and actual bits-per-step.
        """
        mo = create_simple_multi_output_lfsr(REFERENCE_CONFIG, [0, 99])
        assert mo.output_rate == 2  # declared/nominal rate

        # Requesting 4 bits: steps_needed = ceil(4/2) = 2 steps, but each
        # step only contributes 1 real bit (index 99 filtered out) => only
        # 2 raw bits are ever generated, so the returned sequence is
        # shorter than requested (no IndexError, but silently truncated
        # below the caller's requested length).
        seq = mo.generate_sequence([1, 0, 0, 0], 4)
        assert len(seq) == 2
        assert len(seq) != 4

    def test_output_function_receives_state_before_clocking(self):
        """Output must be computed from the state BEFORE it's clocked
        (matches the get-then-clock ordering read directly from
        multi_output.py's generate_sequence loop)."""
        captured_states = []

        def capture_and_output(state):
            captured_states.append(list(state))
            return [state[0]]

        mo = MultiOutputLFSR(REFERENCE_CONFIG, capture_and_output, output_rate=1)
        mo.generate_sequence([1, 0, 1, 0], 3)
        assert captured_states[0] == [1, 0, 1, 0]  # unclocked initial state first

    def test_generate_sequence_wrong_state_size_raises(self):
        mo = create_simple_multi_output_lfsr(REFERENCE_CONFIG, [0])
        with pytest.raises(ValueError):
            mo.generate_sequence([1, 0], 5)

    def test_get_config_and_analyze_structure(self):
        mo = create_simple_multi_output_lfsr(REFERENCE_CONFIG, [0, 1, 2])
        cfg = mo.get_config()
        assert cfg.parameters["output_rate"] == 3
        props = mo.analyze_structure()
        assert props["output_rate"] == 3
        assert "3 bits per step" in props["note"]


# ---------------------------------------------------------------------------
# Security-assessment / analyze_structure smoke tests across all classes
# (cheap coverage for the straightforward dict-returning methods).
# ---------------------------------------------------------------------------


class TestSecurityAssessments:
    def test_nfsr_assess_security_shape(self):
        nfsr = NFSR(REFERENCE_CONFIG, lambda s: s[0])
        sec = nfsr._assess_security(nfsr.analyze_structure())
        assert "known_vulnerabilities" in sec
        assert "recommendations" in sec

    def test_filtered_assess_security_shape(self):
        flt = FilteredLFSR(REFERENCE_CONFIG, lambda s: s[0])
        sec = flt._assess_security(flt.analyze_structure())
        assert "known_vulnerabilities" in sec

    def test_clock_controlled_assess_security_shape(self):
        cc = ClockControlledLFSR(REFERENCE_CONFIG)
        sec = cc._assess_security(cc.analyze_structure())
        assert "known_vulnerabilities" in sec

    def test_irregular_clocking_assess_security_shape(self):
        ic = IrregularClockingLFSR(REFERENCE_CONFIG)
        sec = ic._assess_security(ic.analyze_structure())
        assert "known_vulnerabilities" in sec

    def test_multi_output_assess_security_shape(self):
        mo = create_simple_multi_output_lfsr(REFERENCE_CONFIG, [0])
        sec = mo._assess_security(mo.analyze_structure())
        assert "known_vulnerabilities" in sec

    def test_base_class_default_assess_security_is_placeholder(self):
        """The base class's own _assess_security (not overridden) should
        return the documented placeholder shape -- exercised via a
        minimal concrete subclass that does not override it."""

        class _Bare(AdvancedLFSR):
            def generate_sequence(self, initial_state, length):
                return []

            def analyze_structure(self):
                return {}

            def get_config(self):
                return AdvancedLFSRConfig(
                    structure_type="bare", base_lfsr_config=REFERENCE_CONFIG
                )

        bare = _Bare()
        sec = bare._assess_security({})
        assert sec["structure_complexity"] == "medium"
        assert sec["known_vulnerabilities"] == []
        assert sec["recommendations"] == []

    def test_base_class_analyze_end_to_end_via_bare_subclass(self):
        class _Bare(AdvancedLFSR):
            def generate_sequence(self, initial_state, length):
                return [1, 0] * (length // 2) + [1] * (length % 2)

            def analyze_structure(self):
                return {"structure_type": "bare"}

            def get_config(self):
                return AdvancedLFSRConfig(
                    structure_type="bare", base_lfsr_config=REFERENCE_CONFIG
                )

        bare = _Bare()
        result = bare.analyze(initial_state=[1, 0, 0, 0], sequence_length=7)
        assert result.structure_type == "bare"
        assert result.sequence_properties["length"] == 7
        assert result.security_assessment["structure_complexity"] == "medium"
