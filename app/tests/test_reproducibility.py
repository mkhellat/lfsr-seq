#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for lfsr.reproducibility.

Covers generate_seed(), capture_environment(), export_configuration(),
generate_reproducibility_report(), and save_reproducibility_report().

No SageMath dependency -- this module only touches stdlib json/platform/sys
plus the optional pkg_resources. Focus is on: (1) JSON round-tripping is
exact (what goes in under analysis_config/analysis_results comes back out
byte-identical after a json.loads), (2) content actually varies when input
varies (e.g. two different configs produce different serialized output,
not some byte that never changes), and (3) file-writing helpers write
exactly what the string-returning versions would produce.
"""

import io
import json
import sys

import pytest

from lfsr.reproducibility import (
    capture_environment,
    export_configuration,
    generate_reproducibility_report,
    generate_seed,
    save_reproducibility_report,
)


class TestGenerateSeed:
    def test_returns_int_in_valid_range(self):
        seed = generate_seed()
        assert isinstance(seed, int)
        assert 0 <= seed <= 2**31 - 1

    def test_seeds_are_not_constant(self):
        """Sanity check that this isn't hardcoded -- draw several and
        expect at least some variation (astronomically unlikely to
        collide 20 times in a row if truly random)."""
        seeds = {generate_seed() for _ in range(20)}
        assert len(seeds) > 1


class TestCaptureEnvironment:
    def test_has_expected_top_level_keys(self):
        env = capture_environment()
        assert set(env.keys()) == {"timestamp", "platform", "python", "packages"}

    def test_platform_section_fields(self):
        env = capture_environment()
        plat = env["platform"]
        assert set(plat.keys()) == {"system", "release", "version", "machine", "processor"}
        assert isinstance(plat["system"], str)

    def test_python_section_matches_running_interpreter(self):
        env = capture_environment()
        py = env["python"]
        assert py["version"] == sys.version
        assert py["executable"] == sys.executable
        assert py["path"] == sys.path

    def test_packages_is_a_dict(self):
        env = capture_environment()
        assert isinstance(env["packages"], dict)

    def test_timestamp_is_iso_format_and_parseable(self):
        from datetime import datetime

        env = capture_environment()
        # datetime.fromisoformat should not raise on a real isoformat() string
        parsed = datetime.fromisoformat(env["timestamp"])
        assert parsed.year >= 2024

    def test_environment_is_json_serializable(self):
        """This dict gets embedded directly into export_configuration()'s
        JSON output, so it must not contain anything json.dumps chokes on
        (e.g. a raw datetime object instead of a string)."""
        env = capture_environment()
        json.dumps(env)  # should not raise


class TestExportConfiguration:
    def test_returns_valid_json_string(self):
        config = {"coefficients": [1, 0, 0, 1], "field_order": 2}
        result = export_configuration(config)
        parsed = json.loads(result)  # should not raise
        assert isinstance(parsed, dict)

    def test_round_trips_analysis_config_exactly(self):
        """Whatever's passed in as analysis_config must come back out
        byte-identical (as a Python structure) after JSON round-trip --
        this is the crux of it being useful for reproducibility."""
        config = {
            "coefficients": [1, 0, 1, 1, 0],
            "field_order": 2,
            "nested": {"a": [1, 2, 3], "b": None, "c": True},
            "unicode_note": "primitive polynomial – GF(2)",
        }
        result = export_configuration(config)
        parsed = json.loads(result)
        assert parsed["analysis_config"] == config

    def test_includes_environment_and_export_timestamp(self):
        result = export_configuration({"x": 1})
        parsed = json.loads(result)
        assert "environment" in parsed
        assert "export_timestamp" in parsed
        assert set(parsed["environment"].keys()) == {
            "timestamp", "platform", "python", "packages"
        }

    def test_different_configs_produce_different_json(self):
        result_a = export_configuration({"coefficients": [1, 0, 1]})
        result_b = export_configuration({"coefficients": [1, 1, 1]})
        parsed_a = json.loads(result_a)
        parsed_b = json.loads(result_b)
        assert parsed_a["analysis_config"] != parsed_b["analysis_config"]

    def test_writes_to_output_file_when_provided(self):
        buf = io.StringIO()
        result = export_configuration({"x": 1}, output_file=buf)
        written = buf.getvalue()
        # The file should contain exactly the returned JSON plus a
        # trailing newline (per source: f.write(config_json); f.write("\n")).
        assert written == result + "\n"

    def test_no_output_file_does_not_raise(self):
        # output_file=None is the default; ensure the write branch is
        # correctly skipped rather than raising on None.write(...).
        export_configuration({"x": 1}, output_file=None)

    def test_ensure_ascii_false_preserves_unicode_characters(self):
        """Source uses ensure_ascii=False, so non-ASCII characters should
        appear literally in the JSON string, not as \\uXXXX escapes."""
        config = {"note": "αβγ"}  # alpha beta gamma
        result = export_configuration(config)
        assert "αβγ" in result
        assert "\\u03b1" not in result


class TestGenerateReproducibilityReport:
    def test_returns_valid_json_string(self):
        result = generate_reproducibility_report({"field_order": 2}, {"coefficients": [1, 0, 1]})
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_report_type_and_top_level_structure(self):
        result = generate_reproducibility_report({}, {})
        parsed = json.loads(result)
        assert parsed["report_type"] == "reproducibility_report"
        assert set(parsed.keys()) == {
            "report_type", "generated", "seed", "configuration",
            "environment", "results_summary", "reproducibility_instructions",
        }

    def test_seed_defaults_to_none_and_round_trips_when_given(self):
        result_no_seed = generate_reproducibility_report({}, {})
        assert json.loads(result_no_seed)["seed"] is None

        result_with_seed = generate_reproducibility_report({}, {}, seed=12345)
        assert json.loads(result_with_seed)["seed"] == 12345

    def test_configuration_round_trips_exactly(self):
        config = {"coefficients": [1, 1, 0, 1], "field_order": 3, "extra": {"k": "v"}}
        result = generate_reproducibility_report({}, config)
        assert json.loads(result)["configuration"] == config

    def test_results_summary_extracts_only_specific_fields(self):
        """results_summary is documented to pull exactly four fields out
        of analysis_results via .get() -- verify it does NOT leak other
        keys through, and correctly defaults missing ones to null."""
        results = {
            "field_order": 2,
            "lfsr_degree": 4,
            "max_period": 15,
            "is_primitive": True,
            "some_other_key": "should not appear in results_summary",
        }
        result = generate_reproducibility_report(results, {})
        summary = json.loads(result)["results_summary"]

        assert summary == {
            "field_order": 2,
            "lfsr_degree": 4,
            "max_period": 15,
            "is_primitive": True,
        }
        assert "some_other_key" not in summary

    def test_results_summary_missing_fields_default_to_none(self):
        result = generate_reproducibility_report({}, {})
        summary = json.loads(result)["results_summary"]
        assert summary == {
            "field_order": None,
            "lfsr_degree": None,
            "max_period": None,
            "is_primitive": None,
        }

    def test_reproducibility_instructions_present_and_ordered(self):
        result = generate_reproducibility_report({}, {})
        instructions = json.loads(result)["reproducibility_instructions"]
        assert list(instructions.keys()) == ["step1", "step2", "step3", "step4", "step5"]

    def test_writes_to_output_file_when_provided(self):
        buf = io.StringIO()
        result = generate_reproducibility_report({}, {}, output_file=buf)
        assert buf.getvalue() == result + "\n"

    def test_environment_embedded_in_report(self):
        result = generate_reproducibility_report({}, {})
        parsed = json.loads(result)
        assert set(parsed["environment"].keys()) == {
            "timestamp", "platform", "python", "packages"
        }


class TestSaveReproducibilityReport:
    def test_writes_expected_json_content_to_file(self, tmp_path):
        out_file = tmp_path / "report.json"
        results = {"field_order": 2, "lfsr_degree": 4, "max_period": 15, "is_primitive": True}
        config = {"coefficients": [1, 0, 0, 1], "field_order": 2}

        save_reproducibility_report(results, config, str(out_file), seed=42)

        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        parsed = json.loads(content)

        assert parsed["seed"] == 42
        assert parsed["configuration"] == config
        assert parsed["results_summary"] == {
            "field_order": 2, "lfsr_degree": 4, "max_period": 15, "is_primitive": True
        }

    def test_file_content_matches_generate_reproducibility_report_output(self, tmp_path, monkeypatch):
        """save_reproducibility_report should write exactly what
        generate_reproducibility_report would return (plus the trailing
        newline), for the same inputs -- pin the environment's volatile
        'timestamp'/'generated' fields via freezing capture time isn't
        practical here without touching source, so compare structurally
        instead (excluding the two timestamp fields that legitimately
        differ by microseconds between the two calls)."""
        out_file = tmp_path / "report.json"
        results = {"field_order": 5, "lfsr_degree": 3}
        config = {"coefficients": [2, 1, 1]}

        save_reproducibility_report(results, config, str(out_file), seed=7)
        direct = generate_reproducibility_report(results, config, seed=7)

        from_file = json.loads(out_file.read_text(encoding="utf-8"))
        direct_parsed = json.loads(direct)

        for d in (from_file, direct_parsed):
            del d["generated"]
            del d["environment"]["timestamp"]

        assert from_file == direct_parsed

    def test_default_seed_is_none(self, tmp_path):
        out_file = tmp_path / "report.json"
        save_reproducibility_report({}, {}, str(out_file))
        parsed = json.loads(out_file.read_text(encoding="utf-8"))
        assert parsed["seed"] is None

    def test_overwrites_existing_file(self, tmp_path):
        out_file = tmp_path / "report.json"
        out_file.write_text("stale content that should be replaced")

        save_reproducibility_report({"field_order": 9}, {}, str(out_file))

        parsed = json.loads(out_file.read_text(encoding="utf-8"))
        assert parsed["results_summary"]["field_order"] == 9
