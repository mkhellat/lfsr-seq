#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for time-memory trade-off (TMTO) attacks.

Tests for HellmanTable, RainbowTable, tmto_attack(), and
optimize_tmto_parameters() in lfsr.tmto.

Uses a degree-4 GF(2) LFSR with coefficients [1, 0, 0, 1] throughout
(the same primitive/max-period reference vector used elsewhere in this
suite and in the README) because its state space (size 16) is small
enough to fully enumerate, which lets correctness be verified
deterministically rather than statistically.

A note on the state-update convention used by this module: the rest of
the codebase (see lfsr/core.py's build_state_update_matrix docstring
and lfsr/analysis.py's usage) treats states as row vectors and
advances them via ``state * C``. lfsr/tmto.py instead advances states
via ``C * state`` (column-vector convention) in both HellmanTable and
RainbowTable, consistently. Because the module only ever applies its
own convention against tables built with that same convention, its
internal attacks are self-consistent and these tests validate that
self-consistent behavior -- but note for the record that this
convention is the reverse of the rest of the package's documented
state-update semantics (verified: for coefficients=[1,0,0,1] starting
from state [1,0,0,0], ``C*s`` iterated gives
[1000, 0100, 0010, 0001, 1001, 1101, 1111, ...] while ``s*C`` iterated
gives [1000, 0001, 0011, 0111, 1111, 1110, 1101, ...] -- genuinely
different sequences, not just a relabeling).

A real bug was found while writing these tests: RainbowTable's
per-step reduction function closure (``_create_reduction_function`` in
lfsr/tmto.py, around line 387) does ``bytes(str(state) +
str(step)).encode('utf-8')`` -- calling ``bytes()`` on a plain ``str``
without an encoding argument, which unconditionally raises
``TypeError: string argument without an encoding``. This makes
``RainbowTable.generate()``, ``RainbowTable.lookup()``, and
``tmto_attack(method="rainbow")`` completely non-functional -- not an
edge case, every call crashes. Per task instructions this file does
NOT patch tmto.py; the tests below assert the actual (crashing)
behavior via pytest.raises so the suite documents the bug rather than
silently encoding it as "working as intended."
"""

import pytest

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

# NOTE: `from sage.all import *` above shadows the stdlib `random` module
# name with sage's own `random()` function, so the stdlib module must be
# imported afterwards (and lfsr/tmto.py itself uses the real stdlib
# `random.seed`/`random.randint`, which is what these tests need to
# reproduce table generation deterministically).
import random  # noqa: E402  (must follow the sage star-import, see above)

from lfsr.attacks import LFSRConfig
from lfsr.core import build_state_update_matrix
from lfsr.tmto import (
    HellmanTable,
    RainbowTable,
    TMTOAttackResult,
    optimize_tmto_parameters,
    tmto_attack,
)

# Reference LFSR: degree 4, GF(2), primitive/max-period taps [1,0,0,1].
# State space size = 2**4 = 16, small enough to fully enumerate.
REFERENCE_CONFIG = LFSRConfig(coefficients=[1, 0, 0, 1], field_order=2, degree=4)


def _advance(C, F, state):
    """Advance a state one step using tmto.py's own convention (C * s)."""
    return list(C * vector(F, state))


def _walk_chain(C, F, start, steps):
    """Walk `steps` state-update steps from `start`, tmto.py's convention."""
    cur = vector(F, start)
    trail = [list(cur)]
    for _ in range(steps):
        cur = C * cur
        trail.append(list(cur))
    return trail


class TestHellmanTableGeneration:
    """Tests for HellmanTable construction/precomputation."""

    def test_generate_produces_requested_chain_count(self):
        """generate() should produce exactly chain_count chains when the
        state space is large enough relative to max_attempts that finding
        enough distinguished/fallback chains is not a problem."""
        random.seed(1)
        table = HellmanTable(chain_count=10, chain_length=8, distinguished_bits=1)
        table.generate(REFERENCE_CONFIG)
        assert len(table.chains) == 10

    def test_generate_is_deterministic_given_seeded_random(self):
        """With Python's random module seeded, chain generation is
        deterministic (tmto.py uses the global `random` module directly,
        not an injected RNG) -- verify that seeding reproduces the exact
        same chains, which is what makes the rest of this test module
        possible to write deterministically."""
        random.seed(1)
        table_a = HellmanTable(chain_count=10, chain_length=8, distinguished_bits=1)
        table_a.generate(REFERENCE_CONFIG)

        random.seed(1)
        table_b = HellmanTable(chain_count=10, chain_length=8, distinguished_bits=1)
        table_b.generate(REFERENCE_CONFIG)

        assert table_a.chains == table_b.chains

    def test_chain_start_end_are_consistent_with_state_update_function(self):
        """For every chain (start_state, end_state) produced by generate(),
        manually walking the state-update function (C * s, tmto.py's own
        convention) from start_state for up to chain_length steps must
        land on end_state at some point -- otherwise the table's own
        precomputation would be internally broken. Verified here for
        every chain, not just one, since it's cheap at this table size."""
        random.seed(1)
        chain_length = 8
        table = HellmanTable(
            chain_count=10, chain_length=chain_length, distinguished_bits=1
        )
        table.generate(REFERENCE_CONFIG)

        C, _CS = build_state_update_matrix(
            REFERENCE_CONFIG.coefficients, REFERENCE_CONFIG.field_order
        )
        F = GF(REFERENCE_CONFIG.field_order)

        for start, end in table.chains:
            trail = _walk_chain(C, F, start, chain_length)
            assert end in trail, (
                f"chain start={start} end={end} could not be reproduced by "
                f"walking the state-update function; trail was {trail}"
            )

    def test_distinguished_point_detection_matches_leading_zero_rule(self):
        """_is_distinguished_point's own documented rule is: the leading
        `distinguished_bits` entries of the state are all zero. Verify
        this directly against the private method rather than trusting it
        indirectly through generate()."""
        table = HellmanTable(chain_count=1, chain_length=1, distinguished_bits=2)
        assert table._is_distinguished_point([0, 0, 1, 1]) is True
        assert table._is_distinguished_point([0, 1, 1, 1]) is False
        assert table._is_distinguished_point([1, 0, 0, 0]) is False

    def test_distinguished_point_empty_state_is_false(self):
        """An empty state list is explicitly handled and must return False
        (guards against IndexError on the bits_to_check computation)."""
        table = HellmanTable(chain_count=1, chain_length=1, distinguished_bits=2)
        assert table._is_distinguished_point([]) is False


class TestHellmanTableLookup:
    """Tests for HellmanTable.lookup().

    lookup() as actually implemented only succeeds when the target state
    is exactly equal to a stored chain's `end_state` -- either directly,
    or via the target's reduction-function image matching a stored
    `end_state`. It does NOT search interior chain states for a match;
    a state that is genuinely a non-endpoint member of a covered chain
    is NOT found by this method (verified below).

    One further, more serious bug was found and is documented/tested
    explicitly below (scoped to the reconstruction loop that starts at
    line 257 of lfsr/tmto.py):

    1. **False match on duplicate endpoints.** When multiple chains
       share the same `end_state` (verified to happen routinely at this
       table size -- e.g. with seed 1, chain_count=10, chain_length=8,
       distinguished_bits=1 against REFERENCE_CONFIG, the end value
       [0, 1, 1, 1] is shared by three different chains with three
       different start states), lookup's `for start, end in self.chains:
       if end == target_list` loop returns the FIRST matching chain's
       start in list order -- not necessarily the chain the target
       actually belongs to. This silently returns a wrong
       recovered_state for every chain but the first with that end
       value, rather than reporting ambiguity or failure. This is a
       fundamental limitation of returning the target state alone (with
       no chain-identifying information) to lookup() rather than a bug
       fixed in this session.

    A second bug, an off-by-one that made lookup() miss a chain's own
    recorded endpoint when it was reached only at the final
    chain_length-th update, was found and has since been fixed in
    lfsr/tmto.py (see test_lookup_finds_endpoint_reached_only_at_final_step
    below, which is now a regression test for the fix rather than a
    bug-documentation test).
    """

    def test_lookup_succeeds_for_target_equal_to_a_chain_endpoint(self):
        """A target state that is exactly a stored chain's end_state,
        for a chain whose end_state is not shared with any other chain
        and was reached before the final step (i.e. free of both bugs
        documented in this class's docstring), must be found -- and the
        recovered start state must genuinely reproduce that target when
        run through the real state-update function.

        Chain index 7 (with seed=1, chain_count=10, chain_length=8,
        distinguished_bits=1 against REFERENCE_CONFIG) was independently
        verified to have a unique end_state ([0, 0, 1, 1], owned by no
        other chain) reached at step 1 of 8 (not the final step), making
        it a clean case uncontaminated by either bug."""
        random.seed(1)
        chain_length = 8
        table = HellmanTable(
            chain_count=10, chain_length=chain_length, distinguished_bits=1
        )
        table.generate(REFERENCE_CONFIG)

        start, end = table.chains[7]
        assert start == [0, 1, 1, 0]
        assert end == [0, 0, 1, 1]
        # Precondition: this end value must be unique in the table, and
        # reached before the final step, or this test would silently be
        # exercising one of the two bugs instead of the clean path.
        assert sum(1 for _s, e in table.chains if e == end) == 1

        recovered = table.lookup(end, REFERENCE_CONFIG)
        assert recovered == start

        # Independently verify: replaying the update function from the
        # recovered start state actually reaches the target end state.
        C, _CS = build_state_update_matrix(
            REFERENCE_CONFIG.coefficients, REFERENCE_CONFIG.field_order
        )
        F = GF(REFERENCE_CONFIG.field_order)
        trail = _walk_chain(C, F, recovered, chain_length)
        assert end in trail

    def test_lookup_fails_for_non_endpoint_interior_chain_state(self):
        """A state that genuinely occurs partway through a covered chain
        (not at the endpoint, and not equal to any *other* chain's
        end_state either, to avoid inadvertently exercising the
        duplicate-endpoint bug instead) is NOT found by lookup() -- this
        documents the actual (narrower-than-docstring) search behavior
        rather than asserting the idealized algorithm."""
        random.seed(1)
        chain_length = 8
        table = HellmanTable(
            chain_count=10, chain_length=chain_length, distinguished_bits=1
        )
        table.generate(REFERENCE_CONFIG)

        C, _CS = build_state_update_matrix(
            REFERENCE_CONFIG.coefficients, REFERENCE_CONFIG.field_order
        )
        F = GF(REFERENCE_CONFIG.field_order)
        all_ends = {tuple(e) for _s, e in table.chains}

        start, end = table.chains[7]
        trail = _walk_chain(C, F, start, chain_length)
        # An interior state: present in the trail, not this chain's own
        # end, and not coincidentally any other chain's end either.
        interior_candidates = [
            s for s in trail[1:-1] if s != end and tuple(s) not in all_ends
        ]
        assert interior_candidates, "expected a non-trivial chain to test against"
        interior_state = interior_candidates[0]

        assert table.lookup(interior_state, REFERENCE_CONFIG) is None

    def test_lookup_returns_wrong_start_for_duplicate_endpoints(self):
        """BUG (see class docstring, point 1): when several chains share
        the same end_state, lookup() returns the first matching chain's
        start state in list order regardless of which chain the target
        actually belongs to. Demonstrated here with end_state
        [0, 1, 1, 1], independently confirmed to be shared by chain
        indices 1, 3, and 4 (starts [1,1,1,1], [1,1,0,1], [1,0,0,1]
        respectively) with seed=1, chain_count=10, chain_length=8,
        distinguished_bits=1. lookup() always returns [1, 1, 1, 1] (chain
        1's start) for this end value, which is simply wrong for chains
        3 and 4."""
        random.seed(1)
        chain_length = 8
        table = HellmanTable(
            chain_count=10, chain_length=chain_length, distinguished_bits=1
        )
        table.generate(REFERENCE_CONFIG)

        shared_end = [0, 1, 1, 1]
        owners = [start for start, end in table.chains if end == shared_end]
        assert owners == [[1, 1, 1, 1], [1, 1, 0, 1], [1, 0, 0, 1], [1, 0, 0, 1]], (
            "table generation is deterministic under this seed; if this "
            "no longer holds the test needs updating, not silently "
            "loosening"
        )

        # lookup() always attributes this end_state to the FIRST chain
        # with that end in the list, i.e. chain index 1 (start
        # [1, 1, 1, 1]) -- even when looking it up as if it belonged to
        # chain 3 or 4 (there is no way to disambiguate via the API; the
        # target state alone is passed in).
        recovered = table.lookup(shared_end, REFERENCE_CONFIG)
        assert recovered == [1, 1, 1, 1]
        # This is the WRONG answer for the states that actually came from
        # chains 3 or 4's start states -- lookup() cannot tell them apart
        # and always reports chain 1's start.
        assert recovered != [1, 1, 0, 1]
        assert recovered != [1, 0, 0, 1]

    def test_lookup_succeeds_via_reduction_function_fallback_path(self):
        """lookup() has a second success path (lfsr/tmto.py line ~270):
        if the target itself is not any chain's end_state, it applies
        `_reduction_function` to the target and checks whether THAT
        matches a stored end_state; if so it reconstructs that chain and
        searches for the original target within it. This is the
        "detect a possible false alarm and verify by reconstruction"
        mechanism described in the class docstring's Table Lookup
        section. Here it is exercised with a target that is genuinely a
        true positive (not a false alarm): target [0, 0, 1, 0] is not
        itself any chain's end_state, but its reduction equals chain
        index 7's unique end_state [0, 0, 1, 1]; independently verified
        that walking chain 7's actual start [0, 1, 1, 0] really does
        pass through [0, 0, 1, 0] (at step 4 of 8), so this is a correct
        recovery via the fallback path, not a coincidental one."""
        random.seed(1)
        chain_length = 8
        table = HellmanTable(
            chain_count=10, chain_length=chain_length, distinguished_bits=1
        )
        table.generate(REFERENCE_CONFIG)

        target = [0, 0, 1, 0]
        ends = [end for _start, end in table.chains]
        assert target not in ends, "precondition: target must not be a direct endpoint"
        reduced = table._reduction_function(target, REFERENCE_CONFIG.field_order)
        assert reduced == [0, 0, 1, 1]
        assert table.chains[7] == ([0, 1, 1, 0], [0, 0, 1, 1])

        recovered = table.lookup(target, REFERENCE_CONFIG)
        assert recovered == [0, 1, 1, 0]

        # Independently verify this is a true positive: replaying the
        # update function from the recovered start really does reach
        # the original target state.
        C, _CS = build_state_update_matrix(
            REFERENCE_CONFIG.coefficients, REFERENCE_CONFIG.field_order
        )
        F = GF(REFERENCE_CONFIG.field_order)
        trail = _walk_chain(C, F, recovered, chain_length)
        assert target in trail

    def test_lookup_finds_endpoint_reached_only_at_final_step(self):
        """Regression test for the off-by-one bug (see class docstring,
        point 2, now fixed in lfsr/tmto.py): a chain whose distinguished
        point is only reached at the full chain_length-th state-update
        step must still be found by lookup(), since its end_state is
        unique in the table (not the duplicate-endpoint case). With the
        class default distinguished_bits=8 (as used internally by
        tmto_attack, which does not expose this parameter), seed=1,
        chain_count=10, chain_length=8 against REFERENCE_CONFIG, chain
        index 1 (start [1, 1, 1, 1], end [0, 0, 1, 1]) independently
        walks to its recorded end_state only at step 8 of 8, and that
        end_state is not shared by any other chain -- lookup()'s
        reconstruction loop now also checks the state reached after the
        final update, not just positions 0 through chain_length-1."""
        random.seed(1)
        chain_length = 8
        table = HellmanTable(
            chain_count=10, chain_length=chain_length
        )  # default distinguished_bits=8
        table.generate(REFERENCE_CONFIG)

        start, end = table.chains[1]
        assert start == [1, 1, 1, 1]
        assert end == [0, 0, 1, 1]

        C, _CS = build_state_update_matrix(
            REFERENCE_CONFIG.coefficients, REFERENCE_CONFIG.field_order
        )
        F = GF(REFERENCE_CONFIG.field_order)
        trail = _walk_chain(C, F, start, chain_length)
        assert trail.index(end) == chain_length, (
            "precondition: the endpoint must be reached exactly at the "
            "final step for this to demonstrate the off-by-one fix"
        )
        # Confirm the end_state is not shared with any other chain, so
        # this is unambiguously testing the off-by-one fix and not bug 1.
        assert sum(1 for _s, e in table.chains if e == end) == 1

        assert table.lookup(end, REFERENCE_CONFIG) == start

    def test_lookup_finds_endpoint_reached_only_at_final_step_via_reduction_fallback(self):
        """Same off-by-one fix as test_lookup_finds_endpoint_reached_only_at_final_step
        above, but for the SEPARATE final-position check inside the
        reduction-function fallback branch (lfsr/tmto.py line ~289,
        distinct from line ~271's direct-match branch already covered
        by that other test and by test_lookup_succeeds_via_reduction_function_fallback_path,
        whose target is found mid-chain rather than at the final
        position). With seed=43, chain_count=10, chain_length=8,
        distinguished_bits=1: target [1, 0, 1, 1] is not itself any
        chain's end_state, its reduction is [0, 1, 1, 1] which IS
        chain 9's unique (non-duplicated) end_state ([0, 0, 0, 1] ->
        [0, 1, 1, 1]), and walking chain 9's start only reaches the
        target at the full chain_length-th (final) state-update step --
        independently verified below before asserting lookup()'s
        result."""
        random.seed(43)
        chain_length = 8
        table = HellmanTable(
            chain_count=10, chain_length=chain_length, distinguished_bits=1
        )
        table.generate(REFERENCE_CONFIG)

        start, end = table.chains[9]
        assert start == [0, 0, 0, 1]
        assert end == [0, 1, 1, 1]
        assert sum(1 for _s, e in table.chains if e == end) == 1, (
            "precondition: end_state must be unique, not the "
            "duplicate-endpoint case covered by other tests"
        )

        target = [1, 0, 1, 1]
        ends = [e for _s, e in table.chains]
        assert target not in ends, "precondition: not a direct endpoint"
        reduced = table._reduction_function(target, REFERENCE_CONFIG.field_order)
        assert reduced == end, "precondition: reduction must land on chain 9's end_state"

        C, _CS = build_state_update_matrix(
            REFERENCE_CONFIG.coefficients, REFERENCE_CONFIG.field_order
        )
        F = GF(REFERENCE_CONFIG.field_order)
        trail = _walk_chain(C, F, start, chain_length)
        assert trail.index(target) == chain_length, (
            "precondition: target must be reached exactly at the final "
            "step for this to demonstrate the fallback branch's "
            "off-by-one fix"
        )

        assert table.lookup(target, REFERENCE_CONFIG) == start

    def test_lookup_fails_for_state_provably_outside_all_coverage(self):
        """A state whose value is not any chain's end_state, and whose
        reduction-function image is also not any chain's end_state, is
        provably outside what lookup() can find -- confirm it correctly
        reports failure (returns None), not a false positive."""
        random.seed(1)
        chain_length = 8
        table = HellmanTable(
            chain_count=10, chain_length=chain_length, distinguished_bits=1
        )
        table.generate(REFERENCE_CONFIG)

        ends = {tuple(end) for _start, end in table.chains}
        all_states = [
            [a, b, c, d]
            for a in range(2)
            for b in range(2)
            for c in range(2)
            for d in range(2)
        ]
        uncovered = None
        for state in all_states:
            if tuple(state) in ends:
                continue
            reduced = table._reduction_function(state, REFERENCE_CONFIG.field_order)
            if tuple(reduced) not in ends:
                uncovered = state
                break

        assert uncovered is not None, "expected at least one provably uncovered state"
        assert table.lookup(uncovered, REFERENCE_CONFIG) is None

    def test_reduction_function_output_is_well_formed(self):
        """_reduction_function must return a state of the same length as
        its input, with every component a valid element of the field
        (0 <= x < field_order) -- otherwise downstream vector() calls in
        generate()/lookup() would be operating on garbage."""
        table = HellmanTable(chain_count=1, chain_length=1)
        reduced = table._reduction_function([1, 0, 1, 1], 2)
        assert len(reduced) == 4
        assert all(0 <= x < 2 for x in reduced)


class TestRainbowTableReductionFunction:
    """Regression tests for a real bug found (and since fixed) in
    RainbowTable's per-step reduction function.

    lfsr/tmto.py's `_create_reduction_function` (around line 387) used
    to build its closure as:

        state_bytes = bytes(str(state) + str(step)).encode('utf-8')

    `str(state) + str(step)` is a plain `str`; calling `bytes(some_str)`
    without an explicit encoding raises TypeError unconditionally (this
    was different from HellmanTable's sibling implementation, which
    does `bytes(str(state).encode('utf-8'))` -- encoding first, then
    wrapping in bytes). As a result RainbowTable.generate(),
    RainbowTable.lookup(), and tmto_attack(method="rainbow") were all
    completely non-functional: every call crashed, not just some
    inputs. Fixed by encoding the concatenated string directly
    (`(str(state) + str(step)).encode('utf-8')`), matching the pattern
    HellmanTable already used correctly.
    """

    def test_reduction_function_closure_returns_well_formed_state(self):
        """Calling a reduction function produced by
        _create_reduction_function directly (independent of generate())
        must not crash, and must return a state of the same length as
        its input with every component a valid field element."""
        table = RainbowTable(chain_count=1, chain_length=1)
        reduction_func = table._create_reduction_function(0, 2, 16)
        result = reduction_func([1, 0, 0, 0])
        assert len(result) == 4
        assert all(0 <= x < 2 for x in result)

    def test_generate_succeeds_across_seeds(self):
        """RainbowTable.generate() invokes the reduction functions as
        soon as a chain reaches its first step, so this exercises the
        fixed code path across multiple seeds/table sizes to confirm
        it's genuinely fixed, not passing by chance on one input."""
        for seed in (0, 1, 2, 3):
            random.seed(seed)
            table = RainbowTable(chain_count=5, chain_length=4, distinguished_bits=1)
            table.generate(REFERENCE_CONFIG)
            assert len(table.chains) == 5

    def test_is_distinguished_point_itself_works_correctly(self):
        """RainbowTable's _is_distinguished_point is a plain leading-zero
        check with no dependency on the reduction functions, and works
        correctly in isolation."""
        table = RainbowTable(chain_count=1, chain_length=1, distinguished_bits=2)
        assert table._is_distinguished_point([0, 0, 1, 1]) is True
        assert table._is_distinguished_point([1, 0, 0, 0]) is False
        assert table._is_distinguished_point([]) is False


class TestRainbowTableLookup:
    """Regression tests for a fourth bug found (and since fixed) in
    RainbowTable.lookup()'s reconstruction algorithm.

    The original lookup() never checked whether target_state was itself
    directly equal to a stored chain's end_state -- the common case for
    a real lookup -- it only checked whether
    reduction_functions[step](target_state) matched a stored end_state
    for some step, an indirect condition that doesn't cover a target
    that IS literally a recorded endpoint. It also inherited the same
    "reconstruction loop misses the state reached after the final
    update" issue fixed in HellmanTable.lookup(), but with an extra
    twist: generate() records end_state as the PRE-reduction value when
    a step is distinguished (breaking immediately), or the
    POST-reduction value after the final step in the (here, common)
    non-distinguished fallback case -- so the fix has to check both
    points, not just one.

    Fixed by rewriting lookup() to (1) check target_state directly
    against stored end_states first (mirroring HellmanTable.lookup()'s
    structure), then (2) fall back to trying every step's reduction
    function, and (3) reconstructing via generate()'s exact per-step
    interleaving with a check at both the pre- and post-reduction
    point of each step.
    """

    def test_lookup_finds_every_chain_endpoint(self):
        """Every (start, end) pair generate() actually produced must be
        recoverable via lookup(end, ...) -- except where two chains
        share the same end_state, a separate, documented, unfixed
        limitation (see next test): lookup() cannot distinguish which
        of several chains sharing an end_state a target belongs to, and
        returns whichever one it finds first, which is correct for at
        least one of the owning chains but not necessarily the one
        being asked about."""
        random.seed(1)
        table = RainbowTable(chain_count=5, chain_length=4)
        table.generate(REFERENCE_CONFIG)

        for start, end in table.chains:
            recovered = table.lookup(end, REFERENCE_CONFIG)
            assert recovered is not None, f"lookup found nothing for end={end}"
            # recovered must be SOME chain's start that legitimately
            # reaches `end` -- not necessarily this exact (start, end)
            # pair's start, if end_state is shared across chains.
            owners = [s for s, e in table.chains if e == end]
            assert recovered in owners

    def test_lookup_disambiguates_unique_endpoints_exactly(self):
        """For an end_state owned by exactly one chain (no duplicate),
        lookup() must return that chain's exact start state, not merely
        'some' owner."""
        random.seed(1)
        table = RainbowTable(chain_count=5, chain_length=4)
        table.generate(REFERENCE_CONFIG)

        unique_chains = [
            (start, end)
            for start, end in table.chains
            if sum(1 for _s, e in table.chains if e == end) == 1
        ]
        assert unique_chains, "expected at least one chain with a unique end_state"
        for start, end in unique_chains:
            assert table.lookup(end, REFERENCE_CONFIG) == start

    def test_lookup_returns_a_genuine_owner_for_duplicate_endpoints(self):
        """When multiple chains share an end_state (verified to happen
        with seed=1, chain_count=5, chain_length=4 against
        REFERENCE_CONFIG: end_state [0, 1, 0, 1] is shared by chains
        with starts [1, 1, 1, 1] and [1, 0, 0, 1]), lookup() cannot
        disambiguate from the target state alone -- it returns
        whichever owning chain it happens to check first. This documents
        that known, accepted limitation (same class as
        HellmanTable.lookup()'s documented duplicate-endpoint behavior)
        rather than asserting it picks any particular one arbitrarily."""
        random.seed(1)
        table = RainbowTable(chain_count=5, chain_length=4)
        table.generate(REFERENCE_CONFIG)

        shared_end = [0, 1, 0, 1]
        owners = [start for start, end in table.chains if end == shared_end]
        assert owners == [[1, 1, 1, 1], [1, 0, 0, 1]], (
            "table generation is deterministic under this seed; if this "
            "no longer holds the test needs updating, not silently "
            "loosening"
        )

        recovered = table.lookup(shared_end, REFERENCE_CONFIG)
        assert recovered in owners

    def test_lookup_fails_for_state_provably_outside_all_coverage(self):
        """A state whose value is not any chain's end_state, and whose
        reduction-function image (at every step) is also not any
        chain's end_state, is provably outside what lookup() can find --
        confirm it correctly reports failure (returns None)."""
        random.seed(1)
        chain_length = 4
        table = RainbowTable(chain_count=5, chain_length=chain_length)
        table.generate(REFERENCE_CONFIG)

        ends = {tuple(end) for _start, end in table.chains}
        all_states = [
            [a, b, c, d]
            for a in range(2)
            for b in range(2)
            for c in range(2)
            for d in range(2)
        ]
        uncovered = None
        for state in all_states:
            if tuple(state) in ends:
                continue
            if any(
                tuple(table.reduction_functions[step](state)) in ends
                for step in range(chain_length)
            ):
                continue
            uncovered = state
            break

        assert uncovered is not None, "expected at least one provably uncovered state"
        assert table.lookup(uncovered, REFERENCE_CONFIG) is None


class TestTmtoAttackDispatch:
    """Tests for tmto_attack()'s method dispatch and precomputed-table
    reuse path.

    Note: tmto_attack() constructs `HellmanTable(chain_count,
    chain_length)` without exposing `distinguished_bits`, so it always
    uses the class default of 8. Since REFERENCE_CONFIG's states are
    only 4 elements long, `_is_distinguished_point` checks
    min(8, 4) == 4 leading entries, i.e. the *entire* state must be
    zero -- which only the all-zero state satisfies. Every other chain
    therefore falls back to "use the state after the full chain_length
    steps as the end". Before the off-by-one fix in
    HellmanTable.lookup() (see TestHellmanTableLookup), this meant every
    non-trivial chain's lookup failed via tmto_attack's default
    construction; now that lookup() also checks the state reached after
    the final update, realistic (non-zero) targets are recoverable too,
    as demonstrated below.
    """

    def test_hellman_method_recovers_the_all_zero_state(self):
        """The all-zero state is a fixed point of the state-update
        function (C * 0 = 0), so it is trivially both its own
        distinguished-point chain and reachable at step 0 of the
        reconstruction loop."""
        random.seed(1)
        result = tmto_attack(
            REFERENCE_CONFIG,
            [0, 0, 0, 0],
            method="hellman",
            chain_count=10,
            chain_length=8,
        )

        assert isinstance(result, TMTOAttackResult)
        assert result.method_used == "hellman"
        assert result.attack_successful is True
        assert result.recovered_state == [0, 0, 0, 0]

    def test_hellman_method_recovers_a_realistic_final_step_target(self):
        """Regression test for the off-by-one fix (TestHellmanTableLookup),
        exercised through the public tmto_attack() entry point rather
        than the class directly: a target chosen to be a real,
        unambiguous chain endpoint (chain index 1's end [0, 0, 1, 1],
        independently verified unique and reached only at the final
        step under tmto_attack's actual default construction) is now
        correctly recovered."""
        random.seed(1)
        # Discover the real endpoint deterministically without disturbing
        # RNG state before the actual tmto_attack call (uses a probe
        # constructed identically to what tmto_attack builds internally,
        # then resets the seed).
        probe = HellmanTable(
            chain_count=10, chain_length=8
        )  # default distinguished_bits=8
        probe.generate(REFERENCE_CONFIG)
        start, end = probe.chains[1]
        assert start == [1, 1, 1, 1]
        assert end == [0, 0, 1, 1]
        assert sum(1 for _s, e in probe.chains if e == end) == 1, (
            "expected an unambiguous (non-duplicate) endpoint for this "
            "test to isolate the off-by-one fix specifically"
        )

        random.seed(1)  # reset so tmto_attack's internal generate() matches probe
        result = tmto_attack(
            REFERENCE_CONFIG,
            end,
            method="hellman",
            chain_count=10,
            chain_length=8,
        )

        assert result.attack_successful is True
        assert result.recovered_state == start

    def test_rainbow_method_recovers_a_genuinely_reachable_target(self):
        """method="rainbow" delegates to RainbowTable.generate()/lookup(),
        now fixed (see TestRainbowTableReductionFunction). A target
        chosen as a real chain endpoint from a freshly-generated table
        with a seeded RNG should be recovered. tmto_attack() constructs
        RainbowTable(chain_count, chain_length) without exposing
        distinguished_bits, so the probe below uses the same class
        default (8) tmto_attack itself uses."""
        random.seed(1)
        probe = RainbowTable(
            chain_count=5, chain_length=4
        )  # default distinguished_bits=8
        probe.generate(REFERENCE_CONFIG)
        start, end = probe.chains[0]

        random.seed(1)  # reset so tmto_attack's internal generate() matches probe
        result = tmto_attack(
            REFERENCE_CONFIG,
            end,
            method="rainbow",
            chain_count=5,
            chain_length=4,
        )

        assert isinstance(result, TMTOAttackResult)
        assert result.method_used == "rainbow"
        assert result.attack_successful is True
        assert result.recovered_state == start

    def test_unknown_method_returns_failed_result_with_error_detail(self):
        """An unrecognized method name must not raise -- it returns a
        TMTOAttackResult with attack_successful=False and an explanatory
        message in details['error'], per the explicit branch in
        tmto_attack for unknown methods."""
        result = tmto_attack(REFERENCE_CONFIG, [1, 0, 1, 1], method="bogus")

        assert result.attack_successful is False
        assert result.recovered_state is None
        assert result.method_used == "bogus"
        assert result.table_size == 0
        assert result.precomputation_time == 0.0
        assert "error" in result.details
        assert "bogus" in result.details["error"]

    def test_precomputed_table_is_reused_without_regeneration(self):
        """When precomputed_table is supplied, tmto_attack must use it
        directly rather than calling generate() again -- verified two
        ways: (1) precomputation_time is exactly 0.0 (the code path that
        would set it to a measured duration is skipped entirely), and
        (2) the attack still recovers a target that is only reachable
        via that specific precomputed table's chains.

        Chain index 2 (seed=2, chain_count=10, chain_length=6,
        distinguished_bits=1 against REFERENCE_CONFIG) was independently
        verified to have a unique end_state reached before the final
        step, so this test is not incidentally exercising either of the
        two lookup() bugs documented in TestHellmanTableLookup."""
        random.seed(2)
        table = HellmanTable(chain_count=10, chain_length=6, distinguished_bits=1)
        table.generate(REFERENCE_CONFIG)
        start, target = table.chains[2]
        assert start == [0, 0, 1, 1]
        assert target == [0, 1, 0, 0]
        assert sum(1 for _s, e in table.chains if e == target) == 1

        result = tmto_attack(
            REFERENCE_CONFIG,
            target,
            method="hellman",
            precomputed_table=table,
            chain_length=6,
        )

        assert result.precomputation_time == 0.0
        assert result.attack_successful is True
        assert result.recovered_state == start

    def test_coverage_and_table_size_fields_are_computed_correctly(self):
        """coverage = min(1, table_size*chain_length / state_space_size)
        and table_size = len(table.chains) (not chains*chain_length) --
        verify both against an independently computed expectation for a
        table that does NOT saturate coverage at 1.0, so the min() clamp
        isn't hiding a computation error."""
        random.seed(5)
        chain_count = 3
        chain_length = 2
        result = tmto_attack(
            REFERENCE_CONFIG,
            [1, 1, 1, 1],
            method="hellman",
            chain_count=chain_count,
            chain_length=chain_length,
        )

        state_space_size = REFERENCE_CONFIG.field_order**REFERENCE_CONFIG.degree
        assert state_space_size == 16
        expected_table_size = chain_count  # by construction (may be < if max_attempts hit, but won't be here)
        expected_coverage = min(
            1.0, (result.table_size * chain_length) / state_space_size
        )

        assert result.table_size == expected_table_size
        assert result.coverage == pytest.approx(expected_coverage)
        assert result.details["chain_count"] == result.table_size
        assert result.details["chain_length"] == chain_length
        assert result.details["state_space_size"] == state_space_size


class TestOptimizeTmtoParameters:
    """Tests for optimize_tmto_parameters().

    The function's docstring/module-level docstring invokes the classical
    Hellman trade-off relationship TM^2 = N^2 (T = online lookup time
    proportional to chain length, M = memory proportional to chain
    count, N = state space size) -- independently confirmed against
    Hellman's original 1980 time-memory trade-off analysis (T = N^2/M^2
    in the single-table case), so the *concept* referenced in the
    docstring is real cryptographic literature, not an invented claim.

    However, reading the function body shows it does NOT actually solve
    for parameters satisfying TM^2=N^2. It instead does a small brute
    force search over a fixed candidate list of chain_count values
    ([100, 500, 1000, 5000]), computes chain_length = available_memory
    // chain_count, estimates success_prob = coverage * (1 -
    coverage/2) (an ad hoc formula, not derived from TM^2=N^2), and
    picks whichever candidate meeting target_success_probability
    minimizes chain_count * chain_length. Tests below verify the
    function's ACTUAL documented-in-code formula against independently
    hand-computed expected values, not the idealized TM^2=N^2 claim from
    the docstring.
    """

    def _reference_implementation(
        self, state_space_size, available_memory, target_success_probability
    ):
        """A direct reproduction of optimize_tmto_parameters()'s actual
        algorithm, written independently here (not imported) so the test
        is a genuine cross-check rather than a tautology."""
        best_params = None
        best_product = float("inf")
        for chain_count in [100, 500, 1000, 5000]:
            chain_length = available_memory // chain_count
            if chain_length < 1:
                continue
            coverage = min(1.0, (chain_count * chain_length) / state_space_size)
            success_prob = coverage * (1 - coverage / 2)
            if success_prob >= target_success_probability:
                product = chain_length * chain_count
                if product < best_product:
                    best_product = product
                    best_params = {
                        "chain_count": chain_count,
                        "chain_length": chain_length,
                        "estimated_coverage": coverage,
                        "estimated_success_prob": success_prob,
                        "time_memory_product": product,
                    }
        if best_params is None:
            chain_count = min(1000, available_memory // 100)
            chain_length = available_memory // chain_count if chain_count > 0 else 100
            best_params = {
                "chain_count": chain_count,
                "chain_length": chain_length,
                "estimated_coverage": min(
                    1.0, (chain_count * chain_length) / state_space_size
                ),
                "estimated_success_prob": 0.0,
                "time_memory_product": chain_count * chain_length,
            }
        return best_params

    def test_saturating_coverage_case_matches_hand_computation(self):
        """For a 16-bit state space (65536) with 100000 available memory
        and target success 0.5, every candidate chain_count saturates
        coverage at 1.0 (since chain_count*chain_length always exceeds
        65536 for all four candidates at this memory budget) -- so the
        optimizer should pick the smallest time_memory_product among
        saturating candidates, which is chain_count=100,
        chain_length=1000 (product 100000), the smallest available. This
        was independently hand-verified before writing the assertion."""
        state_space_size = 65536
        available_memory = 100000
        target = 0.5

        result = optimize_tmto_parameters(state_space_size, available_memory, target)
        expected = self._reference_implementation(
            state_space_size, available_memory, target
        )

        assert result == expected
        assert result["chain_count"] == 100
        assert result["chain_length"] == 1000
        assert result["estimated_coverage"] == 1.0
        assert result["estimated_success_prob"] == 0.5
        assert result["time_memory_product"] == 100000

    def test_non_saturating_case_falls_back_to_default_branch(self):
        """For a huge state space (2**32) with a small memory budget
        (2000), no candidate chain_count reaches even a tiny fraction of
        coverage, so success_prob never reaches the 0.5 target for any
        candidate -- this exercises the `best_params is None` fallback
        branch, which returns chain_count = min(1000, memory//100) = 20
        and chain_length = memory // chain_count = 100. Verified this is
        genuinely the fallback path (not a coincidence) by confirming no
        candidate in the primary search satisfies the target."""
        state_space_size = 2**32
        available_memory = 2000
        target = 0.5

        # Confirm precondition: no primary-search candidate meets target.
        for chain_count in [100, 500, 1000, 5000]:
            chain_length = available_memory // chain_count
            if chain_length < 1:
                continue
            coverage = min(1.0, (chain_count * chain_length) / state_space_size)
            success_prob = coverage * (1 - coverage / 2)
            assert success_prob < target, (
                "test precondition violated: a primary-search candidate "
                "meets the target, so this no longer exercises the "
                "fallback branch"
            )

        result = optimize_tmto_parameters(state_space_size, available_memory, target)

        assert result["chain_count"] == 20
        assert result["chain_length"] == 100
        assert result["estimated_success_prob"] == 0.0
        assert result["time_memory_product"] == 20 * 100
        assert result["estimated_coverage"] == pytest.approx(
            (20 * 100) / state_space_size
        )

    def test_result_dict_has_all_documented_keys(self):
        """Regardless of which branch is taken, the returned dict must
        have exactly the keys documented in the docstring."""
        result = optimize_tmto_parameters(65536, 100000, 0.5)
        expected_keys = {
            "chain_count",
            "chain_length",
            "estimated_coverage",
            "estimated_success_prob",
            "time_memory_product",
        }
        assert set(result.keys()) == expected_keys

    def test_time_memory_product_equals_chain_count_times_chain_length(self):
        """time_memory_product must literally equal chain_count *
        chain_length for the returned parameters (a sanity/consistency
        check on the returned numbers themselves, independent of which
        branch produced them)."""
        for state_space_size, available_memory in [
            (65536, 100000),
            (2**32, 2000),
            (1024, 500),
        ]:
            result = optimize_tmto_parameters(state_space_size, available_memory, 0.5)
            assert (
                result["time_memory_product"]
                == result["chain_count"] * result["chain_length"]
            )

    def test_coverage_never_exceeds_one(self):
        """estimated_coverage is explicitly clamped with min(1.0, ...) in
        the implementation -- verify the clamp actually holds for a case
        where raw (chain_count*chain_length)/state_space_size would
        otherwise exceed 1.0 (small state space, generous memory)."""
        result = optimize_tmto_parameters(16, 100000, 0.5)
        assert result["estimated_coverage"] <= 1.0
