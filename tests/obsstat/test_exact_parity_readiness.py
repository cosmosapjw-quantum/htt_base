from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from obsstat.egs3_evalue_merge import merge_evalues_arbitrary_dependence
from obsstat.exact_parity_readiness import (
    BLOCK_TOKEN,
    PASS_TOKEN,
    ParityReadinessError,
    build_parity_readiness_receipt,
    validate_parity_readiness_receipt,
)


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs/research_program/post_pr275/pr282_spec.yaml"
POLICY_PATH = ROOT / "docs/research_program/post_pr275/pr282_publication_policy.json"
RECEIPT_PATH = ROOT / "docs/generated/pr282_exact_parity_readiness_receipt.json"
MUTATION_IDS = (
    "MU282-ESTIMATOR-ABSOLUTE",
    "MU282-MASK-PAIR-DROP",
    "MU282-WEIGHT-PAIR-SKEW",
)


def _spec() -> dict[str, object]:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def _canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    ).hexdigest()


def _mapping_keys(payload: object) -> tuple[str, ...]:
    if isinstance(payload, dict):
        return tuple(payload) + tuple(
            key
            for value in payload.values()
            for key in _mapping_keys(value)
        )
    if isinstance(payload, list):
        return tuple(key for value in payload for key in _mapping_keys(value))
    return ()


def test_spec_and_backlog_freeze_g3_scope_before_execution() -> None:
    spec = _spec()
    backlog = yaml.safe_load(
        (ROOT / "docs/codex_handoff/pr_backlog.yaml").read_text(encoding="utf-8")
    )
    card = next(row for row in backlog["prs"] if row["id"] == "PR-282")

    assert spec["pr_id"] == "PR-282"
    assert spec["dependencies"] == ["PR-280"]
    assert spec["dependency_contract"] == {
        "upstream_id": "PR-280",
        "mode": "requires_terminal_receipt",
    }
    assert card["owner"] == "OBSSTAT"
    assert card["claim_tier_ceiling"] == "diagnostic_only"
    assert spec["change_set_id"] == card["change_set_id"]
    assert spec["publication_group_id"] == card["publication_group_id"]
    assert spec["gate"]["gate_id"] == "G3"
    assert spec["gate"]["pass_token"] == PASS_TOKEN
    assert spec["gate"]["block_token"] == BLOCK_TOKEN
    assert spec["theorem_boundary"]["h2_p_equivariant_estimator"] == (
        "EXECUTED_REGISTERED_SYNTHETIC_PATH_ONLY"
    )
    assert "mask_deconvolution" in spec["theorem_boundary"]["h2_not_executed"]
    assert spec["theorem_boundary"]["h1_reflection_symmetric_null"].startswith(
        "NOT_EVALUATED"
    )
    assert spec["theorem_boundary"]["h3_no_atom_at_zero"].startswith(
        "CONDITIONAL"
    )


def test_clean_execution_derives_pass_and_exact_anti_equivariance() -> None:
    receipt = build_parity_readiness_receipt(_spec())

    assert receipt["terminal"]["g3_outcome"] == PASS_TOKEN
    assert receipt["clean_execution"]["baseline"] == {
        "numerator": -115,
        "denominator": 3,
    }
    assert receipt["clean_execution"]["transformed"] == {
        "numerator": 115,
        "denominator": 3,
    }
    assert receipt["clean_execution"]["relation_residual"] == {
        "numerator": 0,
        "denominator": 1,
    }
    assert receipt["clean_execution"]["mask_equivariant"] is True
    assert receipt["clean_execution"]["weighting_equivariant"] is True
    assert receipt["clean_execution"]["relation_passed"] is True
    assert validate_parity_readiness_receipt(receipt, _spec()) == ()


def test_receipt_is_content_addressed_and_tampered_verdict_fails() -> None:
    receipt = build_parity_readiness_receipt(_spec())
    unsigned = dict(receipt)
    recorded = unsigned.pop("receipt_content_sha256")
    assert recorded == _canonical_sha256(unsigned)

    forged = deepcopy(receipt)
    forged["terminal"]["g3_outcome"] = BLOCK_TOKEN
    forged_unsigned = dict(forged)
    forged_unsigned.pop("receipt_content_sha256")
    forged["receipt_content_sha256"] = _canonical_sha256(forged_unsigned)
    errors = validate_parity_readiness_receipt(forged, _spec())
    assert any("recomputed receipt" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("output_path", "docs/generated/forged.json"),
        ("required_bindings", ["htt/obsstat/exact_parity_readiness.py"]),
        ("terminal_precedence", [PASS_TOKEN]),
        ("mutation_rule", "mutations are optional"),
        ("required_metadata", ["owner"]),
    ],
)
def test_receipt_contract_drift_fails_closed(field: str, replacement: object) -> None:
    spec = _spec()
    spec["receipt_contract"][field] = replacement
    with pytest.raises(ParityReadinessError, match="receipt contract drifted"):
        build_parity_readiness_receipt(spec)


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("claim_level", "level"), "C3"),
        (("theorem_boundary", "h2_executed_scope"), "all masks"),
        (("execution_fixture", "mask_status"), "observed_mask"),
        (("dependent_evalue_merge", "forbidden_combinations"), []),
        (("allowed_uses",), ["unbounded scientific use"]),
        (("caveats",), ["none"]),
    ],
)
def test_claim_boundary_metadata_drift_fails_closed(
    path: tuple[str, ...], replacement: object
) -> None:
    spec = _spec()
    target = spec
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement

    with pytest.raises(ParityReadinessError, match="drifted"):
        build_parity_readiness_receipt(spec)


def test_api_has_no_caller_supplied_readiness_or_threshold() -> None:
    parameters = inspect.signature(build_parity_readiness_receipt).parameters
    forbidden = {"ready", "readiness", "passed", "g3_outcome", "threshold", "tolerance"}
    assert not (forbidden & set(parameters))

    mutated = _spec()
    mutated["ready"] = True
    with pytest.raises(ParityReadinessError, match="unexpected top-level"):
        build_parity_readiness_receipt(mutated)


def test_asymmetric_mask_returns_block_without_tuning() -> None:
    spec = _spec()
    spec["execution_fixture"]["mask"][0] = False
    receipt = build_parity_readiness_receipt(spec)

    assert receipt["terminal"]["g3_outcome"] == BLOCK_TOKEN
    assert "MASK_NOT_FIXED_BY_P" in receipt["terminal"]["reasons"]
    assert receipt["clean_execution"]["mask_equivariant"] is False
    assert all("threshold" not in key.lower() for key in _mapping_keys(receipt))


def test_asymmetric_weighting_returns_block_without_tuning() -> None:
    spec = _spec()
    spec["execution_fixture"]["weights"][0] = 3
    receipt = build_parity_readiness_receipt(spec)

    assert receipt["terminal"]["g3_outcome"] == BLOCK_TOKEN
    assert "WEIGHTING_NOT_FIXED_BY_P" in receipt["terminal"]["reasons"]
    assert receipt["clean_execution"]["weighting_equivariant"] is False


def test_registered_mutations_all_execute_differ_and_are_killed() -> None:
    receipt = build_parity_readiness_receipt(_spec())
    mutations = receipt["mutations"]

    assert tuple(row["mutation_id"] for row in mutations) == MUTATION_IDS
    assert all(row["executed"] is True for row in mutations)
    assert all(row["activated"] is True for row in mutations)
    assert all(row["killed"] is True for row in mutations)
    assert receipt["terminal"]["mutation_survivors"] == []


def test_arbitrary_dependence_evalue_merge_is_exact_convex_arithmetic() -> None:
    report = merge_evalues_arbitrary_dependence(
        labels=("nested-a", "nested-b"),
        e_values=(Fraction(1, 2), Fraction(3, 2)),
        weights=(Fraction(1, 2), Fraction(1, 2)),
    )

    assert report.merged_e_value == Fraction(1, 1)
    assert report.combination_rule == "CONVEX_ARITHMETIC_MEAN"
    assert report.dependence_class == "ARBITRARY_OR_DEPENDENT"
    assert report.independence_assumed is False
    assert report.common_null_required is True
    assert report.prespecified_weights_required is True
    assert report.validity_scope == (
        "ARITHMETIC_ONLY_CONDITIONAL_ON_VALID_INPUT_EVALUES"
    )


@pytest.mark.parametrize(
    ("e_values", "weights", "message"),
    [
        ((Fraction(-1, 2),), (Fraction(1, 1),), "nonnegative"),
        ((Fraction(1, 1),), (Fraction(2, 1),), "sum exactly to one"),
        ((Fraction(1, 1), Fraction(1, 1)), (Fraction(1, 1),), "align"),
    ],
)
def test_evalue_merge_rejects_invalid_inputs(e_values, weights, message) -> None:
    with pytest.raises(ValueError, match=message):
        merge_evalues_arbitrary_dependence(
            labels=tuple(f"lane-{index}" for index in range(len(e_values))),
            e_values=e_values,
            weights=weights,
        )


def test_generated_receipt_replays_exactly() -> None:
    subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/codex_harness/run_pr282_exact_parity_readiness.py",
            "check",
        ],
        cwd=ROOT,
        check=True,
    )
    payload = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    assert payload["readiness_receipt"]["terminal"]["g3_outcome"] == PASS_TOKEN
    assert payload["mask_status"] == "synthetic_fixed_under_registered_reflection"
    assert payload["weighting_status"] == (
        "synthetic_fixed_under_registered_reflection"
    )
    assert payload["assumptions"] == payload["readiness_receipt"]["assumptions"]
    assert any("mask deconvolution" in caveat for caveat in payload["caveats"])
    assert payload["observed_data_executed"] is False
    assert payload["public_use"] is False
    assert payload["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"


def test_publication_policy_binds_no_promotion_and_exact_review_cells() -> None:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    spec = _spec()
    backlog = yaml.safe_load(
        (ROOT / "docs/codex_handoff/pr_backlog.yaml").read_text(encoding="utf-8")
    )
    card = next(row for row in backlog["prs"] if row["id"] == "PR-282")
    assert policy["target_sha"] == "feeb89387d949f41276bec56a6becc08af613214"
    assert policy["change_set_id"] == spec["change_set_id"] == card["change_set_id"]
    assert (
        policy["publication_group_id"]
        == spec["publication_group_id"]
        == card["publication_group_id"]
    )
    assert policy["claim_ceiling"] == "diagnostic_only"
    assert policy["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert "no_caller_readiness" in policy["required_review_cells"]
    assert "dependent_evalue_arithmetic_merge" in policy["required_review_cells"]
    assert "publication_policy_cross_binding" in policy["required_review_cells"]
    assert "latest_target_integration" in policy["required_review_cells"]
    claim_command = next(
        row for row in policy["required_commands"] if row["id"] == "pr282-claim-language"
    )
    assert "--strict-missing" in claim_command["argv"]
