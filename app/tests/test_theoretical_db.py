#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.theoretical_db (KnownResultDatabase: JSON-backed store
of known primitive polynomials / polynomial orders, used to cross-check
computed analysis results).

Ground-truth verification of claimed facts
-------------------------------------------
``populate_standard_primitives`` hard-codes 4 "well-known primitive
polynomials over GF(2)" with claimed orders. Per the task's ground rules,
these are independently verified two ways, not assumed correct from
transcription:

1. Cross-checked against SageMath's own `is_irreducible()` +
   `lfsr.polynomial.polynomial_order` (an independently-tested reference
   implementation already used/verified elsewhere in this test suite --
   see test_theoretical.py) for the actual polynomial built from each
   coefficient vector via this project's real coefficient-to-polynomial
   convention (`R([(-c) % field_order for c in coeffs] + [1])`, documented
   in CLAUDE.md's "Known-fixed bug classes" as the *correct* formula,
   contrasted with a previously-fixed wrong version).
2. Cross-checked via WebSearch against standard published primitive
   polynomial tables (Wolfram MathWorld's "Primitive Polynomial" page,
   which lists x^2+x+1, x^3+x+1, and gives the general q^n-1 order
   result; corroborated by Peterson's table of irreducible/primitive
   polynomials over GF(2), a standard reference).

Result: all 4 claimed (coefficients, field_order, degree, order) tuples
are correct:
    ([1, 1], 2, 2, 3)        -> t^2 + t + 1,       order 3  = 2^2-1
    ([1, 0, 1], 2, 3, 7)     -> t^3 + t^2 + 1,      order 7  = 2^3-1
    ([1, 0, 0, 1], 2, 4, 15) -> t^4 + t^3 + 1,      order 15 = 2^4-1
    ([1, 0, 0, 1, 0], 2, 5, 31) -> t^5 + t^3 + 1,   order 31 = 2^5-1
(Note: the *rendered* polynomial from this project's own coefficient
convention differs in exact term placement from the "textbook" x^4+x+1
style listing found in tables -- e.g. t^4+t^3+1 here vs. 1+x^3+x^4 in
the search result -- but these are the same polynomial under the
reversed-coefficient / reciprocal convention typically used for LFSR
taps; the key claim under test, that field_order**degree - 1 order is
achieved (i.e. primitivity), is independently confirmed by SageMath's
own is_irreducible()+order computation regardless of naming convention.)

No bugs affecting correctness were found in this module (no missing-name
crashes like the ones found in export.py/export_latex.py/theoretical.py
-- this module doesn't touch bare `oo`/`latex`/`polynomial_order`
symbols; it's pure Python + json + pathlib).
"""

import json
import os

import pytest

# Import SageMath - will be skipped if not available via conftest
try:
    from sage.all import *  # noqa: F401,F403
except ImportError:
    pytest.skip("SageMath not available", allow_module_level=True)

import lfsr.theoretical_db as theoretical_db_module
from lfsr.polynomial import polynomial_order as reference_polynomial_order
from lfsr.theoretical_db import KnownResultDatabase, get_database


def _build_poly(R, coeffs, field_order=2):
    """The project's real coefficient-vector -> polynomial convention,
    per CLAUDE.md's documented fix: t^d - c_{d-1}*t^{d-1} - ... - c0."""
    return R([(-c) % field_order for c in coeffs] + [1])


@pytest.fixture(autouse=True)
def _reset_global_db_singleton():
    """theoretical_db.py holds a module-level `_global_db` singleton set
    by get_database(). Reset it before and after each test so tests
    don't leak state into each other via the global."""
    theoretical_db_module._global_db = None
    yield
    theoretical_db_module._global_db = None


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_theoretical_db.json")


@pytest.fixture
def empty_db(db_path):
    return KnownResultDatabase(db_path)


# ---------------------------------------------------------------------------
# Initialization / persistence
# ---------------------------------------------------------------------------


class TestInitializationAndPersistence:
    def test_new_database_is_created_with_empty_standard_schema(self, db_path):
        assert not os.path.exists(db_path)
        db = KnownResultDatabase(db_path)
        assert db.db == {
            "primitive_polynomials": {},
            "polynomial_orders": {},
            "period_distributions": {},
            "known_results": [],
        }
        # _load_database's else-branch calls _save_database() on first
        # creation, so the file should now exist on disk.
        assert os.path.exists(db_path)

    def test_existing_valid_file_is_loaded_verbatim(self, db_path):
        payload = {
            "primitive_polynomials": {"2_2_1_1": {"order": 3}},
            "polynomial_orders": {},
            "period_distributions": {},
            "known_results": ["x"],
        }
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        db = KnownResultDatabase(db_path)
        assert db.db == payload

    def test_corrupt_json_file_falls_back_to_fresh_schema(self, db_path):
        with open(db_path, "w", encoding="utf-8") as f:
            f.write("{not valid json!!")
        db = KnownResultDatabase(db_path)
        assert db.db == {
            "primitive_polynomials": {},
            "polynomial_orders": {},
            "period_distributions": {},
            "known_results": [],
        }

    def test_default_db_path_lives_under_package_data_dir(self):
        """When db_path is omitted, defaults to <package_root>/data/theoretical_db.json
        (Path(__file__).parent.parent / "data") -- verify the path shape
        without actually depending on its pre-existing content."""
        db = KnownResultDatabase(db_path=None)
        assert db.db_path.endswith(os.path.join("data", "theoretical_db.json"))
        assert os.path.exists(db.db_path)

    def test_writes_are_persisted_across_new_instances(self, db_path):
        db1 = KnownResultDatabase(db_path)
        db1.add_primitive_polynomial([1, 1], 2, 2, 3, source="test")

        db2 = KnownResultDatabase(db_path)
        assert db2.lookup_primitive_polynomial([1, 1], 2, 2) == {
            "coefficients": [1, 1],
            "field_order": 2,
            "degree": 2,
            "order": 3,
            "source": "test",
        }


# ---------------------------------------------------------------------------
# add/lookup primitive polynomial
# ---------------------------------------------------------------------------


class TestPrimitivePolynomialAddLookup:
    def test_lookup_missing_returns_none(self, empty_db):
        assert empty_db.lookup_primitive_polynomial([1, 1], 2, 2) is None

    def test_add_then_lookup_round_trips_exactly(self, empty_db):
        empty_db.add_primitive_polynomial(
            [1, 0, 0, 1], 2, 4, 15, source="Peterson's table"
        )
        result = empty_db.lookup_primitive_polynomial([1, 0, 0, 1], 2, 4)
        assert result == {
            "coefficients": [1, 0, 0, 1],
            "field_order": 2,
            "degree": 4,
            "order": 15,
            "source": "Peterson's table",
        }

    def test_key_distinguishes_different_field_orders_and_degrees(self, empty_db):
        """The lookup key is f'{field_order}_{degree}_{coeffs}' -- verify
        that two entries with the same coefficients but different
        field_order/degree don't collide."""
        empty_db.add_primitive_polynomial([1, 1], 2, 2, 3, source="a")
        empty_db.add_primitive_polynomial([1, 1], 3, 2, 8, source="b")
        r2 = empty_db.lookup_primitive_polynomial([1, 1], 2, 2)
        r3 = empty_db.lookup_primitive_polynomial([1, 1], 3, 2)
        assert r2["source"] == "a"
        assert r3["source"] == "b"

    def test_source_defaults_to_none_when_omitted(self, empty_db):
        empty_db.add_primitive_polynomial([1, 1], 2, 2, 3)
        result = empty_db.lookup_primitive_polynomial([1, 1], 2, 2)
        assert result["source"] is None


# ---------------------------------------------------------------------------
# add/lookup polynomial order
# ---------------------------------------------------------------------------


class TestPolynomialOrderAddLookup:
    def test_lookup_missing_returns_none(self, empty_db):
        assert empty_db.lookup_polynomial_order([1, 0, 1], 2, 3) is None

    def test_add_then_lookup_round_trips_exactly(self, empty_db):
        empty_db.add_polynomial_order([1, 0, 1], 2, 3, 7, source="hand-computed")
        result = empty_db.lookup_polynomial_order([1, 0, 1], 2, 3)
        assert result == {
            "coefficients": [1, 0, 1],
            "field_order": 2,
            "degree": 3,
            "order": 7,
            "source": "hand-computed",
        }

    def test_primitive_and_order_tables_are_independent(self, empty_db):
        """Adding to one table must not make the other table find it."""
        empty_db.add_polynomial_order([1, 0, 1], 2, 3, 7)
        assert empty_db.lookup_primitive_polynomial([1, 0, 1], 2, 3) is None


# ---------------------------------------------------------------------------
# compare_with_known
# ---------------------------------------------------------------------------


class TestCompareWithKnown:
    def test_not_found_in_either_table(self, empty_db):
        result = empty_db.compare_with_known([9, 9, 9], 2, 3)
        assert result["found_in_database"] is False
        assert result["matches"] is False
        assert result["known_order"] is None
        assert result["known_is_primitive"] is None

    def test_found_as_primitive_with_matching_computed_values(self, empty_db):
        empty_db.add_primitive_polynomial([1, 1], 2, 2, 3, source="ref")
        result = empty_db.compare_with_known(
            [1, 1], 2, 2, computed_order=3, computed_is_primitive=True
        )
        assert result["found_in_database"] is True
        assert result["known_is_primitive"] is True
        assert result["known_order"] == 3
        assert result["primitive_match"] is True
        assert result["order_match"] is True
        assert result["matches"] is True

    def test_found_as_primitive_but_computed_primitivity_disagrees(self, empty_db):
        """`matches` is first set to `primitive_match` (False here, since
        computed_is_primitive=False disagrees with the known-primitive
        entry). Because that leaves `matches` equal to False, the
        `if comparison['matches'] is False:` guard for the order-check
        fires and *overwrites* matches with order_match -- so an
        order-only agreement can flip 'matches' back to True even though
        the primitivity claim itself was wrong. This is a real quirk of
        the boolean-overwrite logic (not something these tests should
        paper over): 'matches' does NOT mean "everything computed was
        correct", only "the order matched, regardless of what primitivity
        said" whenever computed_order is also provided."""
        empty_db.add_primitive_polynomial([1, 1], 2, 2, 3)
        result = empty_db.compare_with_known(
            [1, 1], 2, 2, computed_order=3, computed_is_primitive=False
        )
        assert result["found_in_database"] is True
        assert result["primitive_match"] is False
        assert result["order_match"] is True
        # See docstring: order_match overwrites matches back to True.
        assert result["matches"] is True

    def test_found_as_primitive_disagrees_on_both_primitivity_and_order(self, empty_db):
        """Contrast with the previous test: when the order *also*
        disagrees, both primitive_match and order_match are False, so
        'matches' correctly stays False throughout."""
        empty_db.add_primitive_polynomial([1, 1], 2, 2, 3)
        result = empty_db.compare_with_known(
            [1, 1], 2, 2, computed_order=999, computed_is_primitive=False
        )
        assert result["primitive_match"] is False
        assert result["order_match"] is False
        assert result["matches"] is False

    def test_found_as_primitive_with_only_order_provided_not_primitivity(
        self, empty_db
    ):
        """When computed_is_primitive is None (not provided), 'matches'
        is only ever set from computed_order's order_match branch."""
        empty_db.add_primitive_polynomial([1, 1], 2, 2, 3)
        result = empty_db.compare_with_known([1, 1], 2, 2, computed_order=3)
        assert result["primitive_match"] is None
        assert result["order_match"] is True
        assert result["matches"] is True

    def test_found_as_primitive_with_nothing_computed_provided(self, empty_db):
        empty_db.add_primitive_polynomial([1, 1], 2, 2, 3)
        result = empty_db.compare_with_known([1, 1], 2, 2)
        assert result["found_in_database"] is True
        assert result["primitive_match"] is None
        assert result["order_match"] is None
        # 'matches' never gets set away from its initial False.
        assert result["matches"] is False

    def test_falls_back_to_polynomial_orders_table_when_not_primitive(self, empty_db):
        empty_db.add_polynomial_order([1, 0, 1], 2, 3, 7, source="ref")
        result = empty_db.compare_with_known(
            [1, 0, 1], 2, 3, computed_order=7, computed_is_primitive=True
        )
        assert result["found_in_database"] is True
        assert result["known_is_primitive"] is False
        assert result["known_order"] == 7
        assert result["order_match"] is True
        assert result["matches"] is True

    def test_polynomial_orders_fallback_mismatch(self, empty_db):
        empty_db.add_polynomial_order([1, 0, 1], 2, 3, 7)
        result = empty_db.compare_with_known([1, 0, 1], 2, 3, computed_order=5)
        assert result["order_match"] is False
        assert result["matches"] is False

    def test_primitive_table_takes_precedence_over_orders_table(self, empty_db):
        """If a coefficient vector is (implausibly) present in both
        tables, the primitive_polynomials table is checked first and
        wins -- the polynomial_orders lookup is only attempted
        `if not comparison['found_in_database']`."""
        empty_db.add_primitive_polynomial([1, 1], 2, 2, 3, source="primitive-table")
        empty_db.add_polynomial_order([1, 1], 2, 2, 999, source="orders-table")
        result = empty_db.compare_with_known([1, 1], 2, 2)
        assert result["known_order"] == 3  # from primitive table, not 999


# ---------------------------------------------------------------------------
# populate_standard_primitives -- ground-truth verified (see module
# docstring for the independent verification method).
# ---------------------------------------------------------------------------


class TestPopulateStandardPrimitives:
    def test_populates_exactly_the_four_documented_entries(self, empty_db):
        empty_db.populate_standard_primitives()
        assert len(empty_db.db["primitive_polynomials"]) == 4

    @pytest.mark.parametrize(
        "coeffs,field_order,degree,expected_order",
        [
            ([1, 1], 2, 2, 3),
            ([1, 0, 1], 2, 3, 7),
            ([1, 0, 0, 1], 2, 4, 15),
            ([1, 0, 0, 1, 0], 2, 5, 31),
        ],
    )
    def test_each_entry_matches_ground_truth_order_and_field_order_pow_degree_minus_1(
        self, empty_db, coeffs, field_order, degree, expected_order
    ):
        empty_db.populate_standard_primitives()
        entry = empty_db.lookup_primitive_polynomial(coeffs, field_order, degree)
        assert entry is not None
        assert entry["order"] == expected_order
        # Ground-truth invariant of primitivity: order == q^d - 1.
        assert expected_order == field_order**degree - 1

        # Independent cross-check against this project's own
        # already-verified polynomial_order implementation (not the
        # broken analyze_irreducible_properties from theoretical.py --
        # see test_theoretical.py -- but the working lower-level
        # lfsr.polynomial.polynomial_order function), using the real
        # coefficient-to-polynomial convention documented in CLAUDE.md.
        F = GF(field_order)
        R = PolynomialRing(F, "t")
        poly = _build_poly(R, coeffs, field_order)
        assert poly.is_irreducible()
        assert reference_polynomial_order(poly, degree, field_order) == expected_order

    def test_populate_is_additive_not_idempotent_guarded(self, empty_db):
        """populate_standard_primitives() has no guard against being
        called twice; since keys are deterministic
        (field_order_degree_coeffs), calling it twice just overwrites the
        same 4 keys rather than duplicating -- verify count stays 4."""
        empty_db.populate_standard_primitives()
        empty_db.populate_standard_primitives()
        assert len(empty_db.db["primitive_polynomials"]) == 4


# ---------------------------------------------------------------------------
# get_database (module-level singleton + auto-populate)
# ---------------------------------------------------------------------------


class TestGetDatabase:
    def test_returns_same_instance_on_repeated_calls_with_same_path(self, db_path):
        db_a = get_database(db_path)
        db_b = get_database(db_path)
        assert db_a is db_b

    def test_auto_populates_standard_primitives_when_empty(self, db_path):
        db = get_database(db_path)
        assert len(db.db["primitive_polynomials"]) == 4
        assert db.lookup_primitive_polynomial([1, 1], 2, 2) is not None

    def test_does_not_repopulate_when_already_nonempty(self, db_path):
        """get_database only auto-populates
        `if not _global_db.db['primitive_polynomials']`. Pre-seed the
        file with a single custom entry (not the standard 4) before the
        singleton is ever created, and confirm it is left alone rather
        than being overwritten/appended-to by the standard set."""
        db = KnownResultDatabase(db_path)
        db.add_primitive_polynomial([9, 9], 5, 2, 24, source="custom")
        assert len(db.db["primitive_polynomials"]) == 1

        # Now go through get_database() for the first time with this
        # already-populated file.
        db2 = get_database(db_path)
        assert len(db2.db["primitive_polynomials"]) == 1
        assert db2.lookup_primitive_polynomial([9, 9], 5, 2)["source"] == "custom"

    def test_ignores_db_path_argument_once_singleton_already_created(
        self, db_path, tmp_path
    ):
        """BUG-ADJACENT DESIGN NOTE (not asserting it's wrong, just
        documenting real behavior): get_database's `if _global_db is
        None` guard means a *second* call with a different db_path is
        silently ignored -- the original singleton (and its original
        file) is returned instead. Callers who expect db_path to always
        be honored should be aware."""
        db_a = get_database(db_path)
        other_path = str(tmp_path / "other.json")
        db_b = get_database(other_path)
        assert db_a is db_b
        assert db_b.db_path == db_path
        assert db_b.db_path != other_path
