from __future__ import annotations

from collections import Counter
from dataclasses import replace
import json
from pathlib import Path

import pytest
import yaml

from common.failure_inventory_v4 import (
    FailureInventoryError,
    build_inventory_artifacts,
    classify_cases,
    load_rules,
    parse_junit,
)
from common.harness_profiles_v4 import FAILURE_BUCKETS


REPO_ROOT = Path(__file__).resolve().parents[2]
FULL_INVENTORY_RULES = (
    REPO_ROOT
    / "docs/research_program/post_pr275/full_inventory_v4_failure_rules.yaml"
)
PR280_ACTIVE_CORE_NODES = {
    "htt.bass.spectrum.test_d2_pstf_progressive_closure::"
    "test_python_pstf_closure_does_not_regress",
    "htt.bass.validation.test_external_code_policy::"
    "test_no_external_code_imports_in_production",
    "scripts.codex_harness.test_codex_assets::"
    "test_installer_copies_repo_scoped_assets_with_project_harness_config",
}


def _junit(tmp_path: Path) -> Path:
    path = tmp_path / "inventory.xml"
    path.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" tests="4" failures="1" errors="1" skipped="1">
<testcase classname="tests.test_example" name="test_pass" />
<testcase classname="tests.test_example" name="test_fail"><failure message="old fixture">trace A</failure></testcase>
<testcase classname="tests.test_example" name="test_error"><error message="missing tool">trace B</error></testcase>
<testcase classname="tests.test_example" name="test_skip"><skipped type="pytest.skip" message="not admitted">reason</skipped></testcase>
</testsuite></testsuites>\n""",
        encoding="utf-8",
    )
    return path


def _rules(tmp_path: Path, cases, *, duplicate: bool = False) -> Path:
    rows = []
    buckets = (
        "STALE_EXPECTATION",
        "OPTIONAL_EXTERNAL_TOOL",
        "DATA_NOT_ADMITTED",
    )
    for index, (case, bucket) in enumerate(zip(cases, buckets, strict=True), start=1):
        rows.append(
            {
                "rule_id": f"R-{index}",
                "bucket": bucket,
                "case_identities": [case.case_identity],
                "outcomes": [case.outcome],
                "evidence_sha256": [case.evidence_sha256],
                "rationale": "bounded synthetic fixture",
            }
        )
    if duplicate:
        clone = dict(rows[0])
        clone["rule_id"] = "R-DUPLICATE"
        rows.append(clone)
    path = tmp_path / "rules.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "schema_version": "htt.full_inventory_failure_rules.v4",
                "buckets": list(FAILURE_BUCKETS),
                "rules": rows,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def test_junit_nonpasses_require_exact_identity_outcome_and_evidence(tmp_path: Path) -> None:
    counts, cases = parse_junit(_junit(tmp_path))
    rules = load_rules(_rules(tmp_path, cases))
    rows = classify_cases(cases, rules)

    assert counts == {
        "collected": 4,
        "suite_declared_tests": 4,
        "subtest_extra_declared_units": 0,
        "multi_outcome_containers": 0,
        "passed_or_xpassed_case_elements": 1,
        "failed": 1,
        "errors": 1,
        "skipped": 1,
        "xfailed": 0,
    }
    assert [row["bucket"] for row in rows] == [
        "STALE_EXPECTATION",
        "OPTIONAL_EXTERNAL_TOOL",
        "DATA_NOT_ADMITTED",
    ]


def test_full_inventory_rules_pin_all_nonpasses_and_three_active_nodes() -> None:
    rules = load_rules(FULL_INVENTORY_RULES)
    counts: Counter[str] = Counter()
    active_nodes: set[str] = set()
    identities: set[str] = set()
    for rule in rules:
        counts[rule.bucket] += len(rule.case_identities)
        identities.update(rule.case_identities)
        if rule.bucket == "ACTIVE_CORE_REGRESSION":
            active_nodes.update(rule.case_identities)

    assert len(identities) == 548
    assert counts == {
        "ACTIVE_CORE_REGRESSION": 3,
        "CF4_QUARANTINE": 136,
        "DATA_NOT_ADMITTED": 26,
        "LEGACY_BYTE_REPLAY_FAILURE": 14,
        "MISSING_HISTORICAL_ARTIFACT": 152,
        "NATIVE_NOT_AVAILABLE": 3,
        "OPTIONAL_EXTERNAL_TOOL": 50,
        "PUBLICATION_DEBT": 34,
        "STALE_EXPECTATION": 130,
    }
    assert active_nodes == PR280_ACTIVE_CORE_NODES


def test_junit_declared_counts_must_reconcile(tmp_path: Path) -> None:
    path = _junit(tmp_path)
    path.write_text(
        path.read_text(encoding="utf-8").replace('tests="4"', 'tests="3"'),
        encoding="utf-8",
    )
    with pytest.raises(FailureInventoryError, match="smaller than testcase"):
        parse_junit(path)


def test_junit_preserves_every_subtest_nonpass_with_ordinal_identity(
    tmp_path: Path,
) -> None:
    path = tmp_path / "subtests.xml"
    path.write_text(
        """<testsuites><testsuite tests="3" failures="1" errors="0" skipped="1"><testcase classname="tests.test_x.Case" name="test_x"><failure message="first"/><skipped message="second"/></testcase></testsuite></testsuites>""",
        encoding="utf-8",
    )
    counts, cases = parse_junit(path)
    assert counts == {
        "collected": 1,
        "suite_declared_tests": 3,
        "subtest_extra_declared_units": 2,
        "multi_outcome_containers": 1,
        "passed_or_xpassed_case_elements": 0,
        "failed": 1,
        "errors": 0,
        "skipped": 1,
        "xfailed": 0,
    }
    assert [case.case_identity for case in cases] == [
        "tests.test_x.Case::test_x::subtest[001]",
        "tests.test_x.Case::test_x::subtest[002]",
    ]


def test_junit_rejects_testcase_outside_selected_suite(tmp_path: Path) -> None:
    path = tmp_path / "foreign.xml"
    path.write_text(
        """<testsuites><testcase classname="tests.foreign" name="test_foreign"/><testsuite tests="1" failures="0" errors="0" skipped="0"><testcase classname="tests.test_x" name="test_x"/></testsuite></testsuites>""",
        encoding="utf-8",
    )
    with pytest.raises(FailureInventoryError, match="outside selected suite"):
        parse_junit(path)


def test_ambiguous_or_unclassified_case_fails_closed(tmp_path: Path) -> None:
    _, cases = parse_junit(_junit(tmp_path))
    with pytest.raises(FailureInventoryError, match="multiple rules"):
        load_rules(_rules(tmp_path, cases, duplicate=True))
    rules = load_rules(_rules(tmp_path, cases))
    ambiguous = (*rules, replace(rules[0], rule_id="R-DUPLICATE"))

    with pytest.raises(FailureInventoryError, match="ambiguous"):
        classify_cases(cases, ambiguous)
    with pytest.raises(FailureInventoryError, match="unclassified"):
        classify_cases(cases, rules[2:])
    unused = replace(
        rules[2],
        rule_id="R-UNUSED",
        case_identities=frozenset({"tests.never::test_never"}),
    )
    with pytest.raises(FailureInventoryError, match="stale or unused"):
        classify_cases(cases, (*rules, unused))

    partly_stale = replace(
        rules[0],
        case_identities=frozenset(
            {next(iter(rules[0].case_identities)), "tests.never::test_never"}
        ),
    )
    with pytest.raises(FailureInventoryError, match="case identities are stale"):
        classify_cases(cases, (partly_stale, *rules[1:]))


def test_failure_evidence_hash_is_repo_and_pytest_tmp_portable(tmp_path: Path) -> None:
    first = tmp_path / "first.xml"
    second = tmp_path / "second.xml"
    template = """<testsuites><testsuite tests="1" failures="1" errors="0" skipped="0"><testcase classname="tests.test_x" name="test_x"><failure message="{root}/tests/test_x.py"><![CDATA[tmp={temp}/case0]]></failure></testcase></testsuite></testsuites>"""
    first_root = tmp_path / "checkout-a"
    second_root = tmp_path / "checkout-b"
    first.write_text(
        template.format(
            root=first_root,
            temp="/tmp/pytest-of-user/pytest-100",
        ),
        encoding="utf-8",
    )
    second.write_text(
        template.format(
            root=second_root,
            temp="/tmp/pytest-of-user/pytest-999",
        ),
        encoding="utf-8",
    )

    _, first_cases = parse_junit(first, evidence_repo_root=first_root)
    _, second_cases = parse_junit(second, evidence_repo_root=second_root)
    assert first_cases[0].evidence_sha256 == second_cases[0].evidence_sha256
    assert first_cases[0].evidence_excerpt == "<REPO_ROOT>/tests/test_x.py"


def test_build_inventory_binds_git_junit_rules_and_classification(tmp_path: Path) -> None:
    junit = _junit(tmp_path)
    _, cases = parse_junit(junit)
    rules = _rules(tmp_path, cases)
    classification = tmp_path / "classification.json"
    receipt = tmp_path / "receipt.json"

    build_inventory_artifacts(
        REPO_ROOT,
        junit_path=junit,
        rules_path=rules,
        classification_path=classification,
        receipt_path=receipt,
        pytest_exit_code=1,
    )
    classification_payload = json.loads(classification.read_text(encoding="utf-8"))
    receipt_payload = json.loads(receipt.read_text(encoding="utf-8"))

    assert classification_payload["unknown_count"] == 0
    assert classification_payload["active_core_count"] == 0
    assert receipt_payload["root_addopts_cleared"] is True
    assert receipt_payload["cache_provider_disabled"] is True
    assert receipt_payload["pytest_exit_code"] == 1
    assert receipt_payload["execution_completed"] is True
    assert receipt_payload["junit_count_observability"] == {
        "pass_vs_xpass": "not_distinguishable_in_pytest_junitxml",
        "deselected": "not_represented_in_pytest_junitxml",
        "passing_subtests": "not_individually_represented_in_pytest_junitxml",
    }
    assert receipt_payload["execution_environment"]["python_version"]
    assert set(receipt_payload["execution_environment"]["distribution_versions"]) == {
        "pytest",
        "numpy",
        "scipy",
    }
    assert receipt_payload["source_layout_environment"] == {
        "PYTHONPATH": "htt/src:htt:htt/htt",
        "PYTEST_ADDOPTS": "unset",
        "PYTEST_PLUGINS": "unset",
    }
    assert receipt_payload["waiver_id"] is None
    assert receipt_payload["claim_ceiling"] == "diagnostic_only"


def test_build_inventory_rejects_incomplete_or_inconsistent_exit(tmp_path: Path) -> None:
    junit = _junit(tmp_path)
    _, cases = parse_junit(junit)
    rules = _rules(tmp_path, cases)

    for exit_code in (0, 2):
        with pytest.raises(FailureInventoryError, match="exit code|terminate normally"):
            build_inventory_artifacts(
                REPO_ROOT,
                junit_path=junit,
                rules_path=rules,
                classification_path=tmp_path / f"classification-{exit_code}.json",
                receipt_path=tmp_path / f"receipt-{exit_code}.json",
                pytest_exit_code=exit_code,
            )
