#!/usr/bin/env python3
"""Portable build/check/test runner for PR-284 depth-path calibration."""

from __future__ import annotations

from copy import copy
from fractions import Fraction
import argparse
import hashlib
from importlib import metadata as importlib_metadata
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any, Callable

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/post_pr275/pr284_spec.yaml"
OUTPUT = ROOT / "docs/generated/pr284_depth_path_doob_receipt.json"
PASS_TOKEN = "PASS_PREMISE_BOUND_DEPTH_PATH_CALIBRATION"
BLOCK_TOKEN = "BLOCKED_DEPTH_PATH_CALIBRATION_CONTRACT"
BOUND_SOURCES = (
    "docs/research_program/post_pr275/pr284_spec.yaml",
    "htt/src/common/depth_path.py",
    "htt/src/common/depth_path_calibration.py",
    "htt/src/common/vector_tensor_statistical_foundations.py",
    "htt/htt/htt/infer/depth_path.py",
    "htt/htt/htt/infer/depth_path_calibration.py",
    "docs/research_program/vector_tensor/proof_registry_two_pillars.yaml",
    "docs/research_program/vector_tensor/proofs/PILLAR_S_CORE_PROOFS_V1.yaml",
    "scripts/codex_harness/run_pr284_depth_path_doob.py",
    "tests/contracts/test_depth_path.py",
    "tests/contracts/test_depth_path_doob_calibration.py",
    "tests/contracts/test_pillar_s_core.py",
)
_MUTATIONS = (
    ("MU284-SUPPORT-NESTING-AS-PROOF", "nested_support_substituted_for_partition_tower"),
    ("MU284-NONNESTED-SUPPORT", "one path support is not a subset of its predecessor"),
    ("MU284-TARGET-DRIFT", "one common-target value changes after report sealing"),
    ("MU284-REPORT-BUILDER-BYPASS", "caller_supplied_proved_report_bypasses_replay"),
    ("MU284-PREPROCESSING-DRIFT", "preprocessing identity differs across rungs or calibration"),
    ("MU284-FILTRATION-DIRECTION-DRIFT", "non-coarsening partition is inserted"),
    ("MU284-THRESHOLD-DRIFT", "threshold changes after report construction"),
    ("MU284-ATOM-SELECTION-DRIFT", "selected atom or selection rule changes after registration"),
    ("MU284-PATH-MAXIMUM-DRIFT", "sealed path maximum is changed without expectation replay"),
    ("MU284-PROBABILITY-LAW-DRIFT", "one exact weight changes under a stale finite-law identity"),
    ("MU284-ESTIMATOR-IDENTITY-DRIFT", "estimator identity changes at calibration"),
    ("MU284-FREE-BOUND-ON-UNPROVED", "unproved report is relabelled bound_available"),
    ("MU284-MATCHED-MOCK-PLAN-OMITTED", "unproved premise carries no resolvable fallback identity"),
    ("MU284-MATCHED-MOCK-PLAN-DRIFT", "null law, generator, seed policy, or acceptance rule changes"),
)
_REASONS = {
    "MU284-SUPPORT-NESTING-AS-PROOF": "FINITE_LAW_AND_PARTITION_EVIDENCE_REQUIRED",
    "MU284-NONNESTED-SUPPORT": "NONNESTED_SUPPORT_REJECTED",
    "MU284-TARGET-DRIFT": "FINITE_TARGET_IDENTITY_REJECTED",
    "MU284-REPORT-BUILDER-BYPASS": "CALLER_SUPPLIED_PROVED_REPORT_REJECTED",
    "MU284-PREPROCESSING-DRIFT": "PREPROCESSING_IDENTITY_REJECTED",
    "MU284-FILTRATION-DIRECTION-DRIFT": "DECREASING_FILTRATION_REJECTED",
    "MU284-THRESHOLD-DRIFT": "THRESHOLD_CONTRACT_REJECTED",
    "MU284-ATOM-SELECTION-DRIFT": "ATOM_SELECTION_IDENTITY_REJECTED",
    "MU284-PATH-MAXIMUM-DRIFT": "PATH_MAXIMUM_IDENTITY_REJECTED",
    "MU284-PROBABILITY-LAW-DRIFT": "PROBABILITY_LAW_IDENTITY_REJECTED",
    "MU284-ESTIMATOR-IDENTITY-DRIFT": "ESTIMATOR_IDENTITY_REJECTED",
    "MU284-FREE-BOUND-ON-UNPROVED": "UNPROVED_PREMISE_FREE_BOUND_REJECTED",
    "MU284-MATCHED-MOCK-PLAN-OMITTED": "MATCHED_MOCK_PLAN_REQUIRED",
    "MU284-MATCHED-MOCK-PLAN-DRIFT": "MATCHED_MOCK_PLAN_IDENTITY_REJECTED",
}
_ERROR_MARKERS = {
    "MU284-SUPPORT-NESTING-AS-PROOF": "exact DepthPathFiniteTargetLaw",
    "MU284-NONNESTED-SUPPORT": "non-nested",
    "MU284-TARGET-DRIFT": "identity drifted",
    "MU284-REPORT-BUILDER-BYPASS": "path content identity",
    "MU284-PREPROCESSING-DRIFT": "preprocessing identity",
    "MU284-FILTRATION-DIRECTION-DRIFT": "decreasing filtration",
    "MU284-THRESHOLD-DRIFT": "threshold contract",
    "MU284-ATOM-SELECTION-DRIFT": "identity drifted",
    "MU284-PATH-MAXIMUM-DRIFT": "identity drifted",
    "MU284-PROBABILITY-LAW-DRIFT": "identity drifted",
    "MU284-ESTIMATOR-IDENTITY-DRIFT": "estimator identity",
    "MU284-FREE-BOUND-ON-UNPROVED": "identity drifted",
    "MU284-MATCHED-MOCK-PLAN-OMITTED": "matched_mock_plan",
    "MU284-MATCHED-MOCK-PLAN-DRIFT": "identity drifted",
}
_MUTATION_KEYS = {
    "mutation_id",
    "mutation_kind",
    "executed",
    "activated",
    "killed",
    "observed_outcome",
    "observed_reason",
}
_RECEIPT_METADATA = (
    "owner",
    "scope",
    "claim_tier_and_level",
    "transfer_source",
    "synthetic_sky_mask_and_covariance_status",
    "null_mock_status",
    "assumptions",
    "caveats",
    "generating_command_or_procedure",
    "exact_source_bindings",
    "git_commit_or_worktree_state",
    "selected_atom_and_selection_rule_content_id",
    "threshold_and_path_maximum_content_id",
    "matched_mock_plan_content_and_registration_id_when_required",
    "TF-11 source status, finite-only relation, NOT_ADJUDICATED status, and known fast-oracle instability caveat",
)
_ASSUMPTIONS = (
    "The finite registered law and selected atom are synthetic and preregistered.",
    "DepthPath nesting and filtration refinement are distinct checks.",
    "The registered target is centered and square-integrable under one common law.",
    "A matched-mock requirement is not itself evidence that matched mocks passed.",
)
_CAVEATS = (
    "The Doob bound may be conservative and is conditional on every registered premise.",
    "The exact finite proof does not validate a data-derived conditional-expectation estimator.",
    "Matched mocks must be separately executed and reviewed before any statistical use.",
    "PR-151 partial/background data is forbidden input.",
    "The known fast TF-11 simulation-oracle instability remains excluded from acceptance evidence and is not repaired or promoted here.",
)


def _activate_sources() -> None:
    resolved = [str(ROOT), str(ROOT / "htt/src"), str(ROOT / "htt")]
    sys.path[:] = resolved + [entry for entry in sys.path if entry not in resolved]
    existing = [
        entry
        for entry in os.environ.get("PYTHONPATH", "").split(os.pathsep)
        if entry and entry not in resolved
    ]
    os.environ["PYTHONPATH"] = os.pathsep.join((*resolved, *existing))
    os.environ["PR284_DEPTH_PATH_RUNNER_ACTIVE"] = "1"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_sha256(value: object) -> str:
    return _sha256_bytes(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    )


def _render(value: object) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _validate_output_destination_for_write() -> None:
    if ROOT.is_symlink() or not ROOT.is_dir():
        raise RuntimeError("repository root must be a regular directory")
    try:
        relative = OUTPUT.relative_to(ROOT)
    except ValueError as exc:
        raise RuntimeError("receipt destination escaped repository root") from exc
    cursor = ROOT
    for part in relative.parent.parts:
        cursor /= part
        if cursor.is_symlink() or not cursor.is_dir():
            raise RuntimeError(
                f"receipt parent must be an existing regular directory: {cursor}"
            )
    if OUTPUT.is_symlink():
        raise RuntimeError("receipt destination must not be a symlink")
    if OUTPUT.exists() and (
        not OUTPUT.is_file() or OUTPUT.stat().st_nlink != 1
    ):
        raise RuntimeError("receipt destination must be a single-link regular file")


def _atomic_write(payload: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=OUTPUT.parent,
        prefix=f".{OUTPUT.name}.",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, OUTPUT)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _tracked_paths() -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RuntimeError("git tracked-file inventory failed")
    return tuple(
        item.decode("utf-8")
        for item in completed.stdout.split(b"\0")
        if item
    )


def _manifest(root: Path, paths: tuple[str, ...]) -> dict[str, object]:
    identities: dict[str, str] = {}
    for relative in paths:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"tracked manifest member is not regular: {relative}")
        identities[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    encoded = json.dumps(
        identities, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "file_count": len(identities),
        "manifest_sha256": hashlib.sha256(encoded).hexdigest(),
        "path_inventory_sha256": hashlib.sha256(
            "\0".join(identities).encode("utf-8")
        ).hexdigest(),
        "content_identity_inventory_sha256": hashlib.sha256(
            "\0".join(identities.values()).encode("ascii")
        ).hexdigest(),
    }


def _versions() -> dict[str, str]:
    values = {"python": sys.version.split()[0]}
    for distribution in ("numpy", "scipy", "PyYAML", "pytest"):
        try:
            values[distribution] = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError:
            values[distribution] = "UNAVAILABLE"
    return values


def _load_spec() -> dict[str, Any]:
    raw = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError("PR-284 spec must be a mapping")
    if (
        raw.get("schema") != "htt.pr284.depth_path_doob_spec.v1"
        or raw.get("pr_id") != "PR-284"
        or raw.get("owner") != "HTT"
        or raw.get("contributors") != ["OBSSTAT", "MIO", "COMMON"]
        or raw.get("change_set_id") != "CS-PR284-DEPTH-DOOB"
        or raw.get("publication_group_id") != "PG-PR284-DEPTH-DOOB"
        or raw.get("dependencies") != ["PR-280"]
        or raw.get("dependency_contract")
        != {"upstream_id": "PR-280", "mode": "requires_terminal_receipt"}
    ):
        raise RuntimeError("PR-284 identity or dependency contract drifted")
    if (
        raw.get("claim_tier") != "diagnostic_only"
        or raw.get("claim_level")
        != {"scheme": "roadmap_rescue_v1", "level": "C2"}
        or raw.get("scientific_artifact_mode") != "synthetic_diagnostic"
        or raw.get("transfer_source") != "none"
        or raw.get("observed_data_executed") is not False
        or raw.get("public_use") is not False
        or raw.get("family_identification_gate") != "BLOCKED_PRE_NATIVE_ATLAS"
    ):
        raise RuntimeError("PR-284 claim boundary drifted")
    gate = raw.get("gate", {})
    if (
        gate.get("gate_id") != "G6"
        or gate.get("pass_token") != PASS_TOKEN
        or gate.get("block_token") != BLOCK_TOKEN
    ):
        raise RuntimeError("PR-284 G6 contract drifted")
    math_boundary = raw.get("mathematical_boundary", {})
    if (
        math_boundary.get("source_oracle_id") != "TF-11-MASK-PATH-MARTINGALE"
        or math_boundary.get("source_registry_status") != "ORACLE_VERIFIED"
        or math_boundary.get("typed_proof_verdict")
        != "PROVED_FINITE_REGISTERED_PATH"
        or math_boundary.get("source_proof_adjudication_status")
        != "NOT_ADJUDICATED"
        or math_boundary.get("relation_to_source")
        != "FINITE_REGISTERED_PATH_ONLY"
    ):
        raise RuntimeError("PR-284 mathematical boundary drifted")
    doob = raw.get("doob_contract", {})
    if (
        doob.get("exact_threshold_representation")
        != "lambda_squared_times_E_target_squared"
        or "greater than or equal" not in doob.get("event_rule", "")
        or "no floating square root" not in doob.get("event_rule", "")
    ):
        raise RuntimeError("PR-284 exact threshold contract drifted")
    pairs = tuple(
        (row.get("mutation_id"), row.get("mutation_kind"))
        for row in raw.get("mutation_registry", ())
        if isinstance(row, dict)
    )
    if pairs != _MUTATIONS:
        raise RuntimeError("PR-284 mutation registry drifted")
    receipt = raw.get("receipt_contract", {})
    if (
        receipt.get("output_path")
        != "docs/generated/pr284_depth_path_doob_receipt.json"
        or tuple(receipt.get("required_bindings", ())) != BOUND_SOURCES
        or receipt.get("terminal_precedence")
        != ["BLOCKED_CONTRACT_INVALID", BLOCK_TOKEN, PASS_TOKEN]
        or tuple(receipt.get("required_metadata", ())) != _RECEIPT_METADATA
        or "inconsistently flagged" not in receipt.get("mutation_rule", "")
    ):
        raise RuntimeError("PR-284 receipt contract drifted")
    future = raw.get("future_consumer_contract", {})
    if (
        future.get("consumer") != "PR-287"
        or future.get("required_input")
        != "exact PR-284 receipt and per-report typed status"
        or len(future.get("rules", ())) != 3
    ):
        raise RuntimeError("PR-284 future-consumer branch contract drifted")
    if (
        tuple(raw.get("assumptions", ())) != _ASSUMPTIONS
        or tuple(raw.get("caveats", ())) != _CAVEATS
    ):
        raise RuntimeError("PR-284 assumptions or caveats drifted")
    return raw


def _stratum(suffix: str, *, depth: float, kept: tuple[int, ...]):
    _activate_sources()
    from common.depth_path import build_mask_stratum
    from common.sky_support import build_sky_support_from_mask

    mask = np.zeros(4, dtype=bool)
    mask[list(kept)] = True
    support = build_sky_support_from_mask(
        mask,
        coordinate_frame="GALACTIC",
        completeness_status="synthetic_fixture_complete",
        selection_mode=f"pr284-selection-{suffix}",
        mock_coverage_status="synthetic_fixture_only",
        pixelization="PR284_UNIT_PIXELS",
    )
    return build_mask_stratum(
        stratum_id=f"PR284-{suffix}",
        depth_coordinate=depth,
        depth_unit="synthetic_depth",
        support_unit_ids=tuple(f"pixel-{index}" for index in kept),
        support_universe_size=4,
        sky_support=support,
        selection_id=f"sha256:selection-{suffix}",
        covariance_id=f"sha256:covariance-{suffix}",
        source_artifact_id=f"sha256:source-{suffix}",
        feature_names=("centered_scalar",),
        feature_unit="dimensionless_diagnostic",
        assumptions=("synthetic nested-mask fixture",),
    )


def _path():
    from common.depth_path import build_depth_path, build_transport_kernel

    strata = (
        _stratum("D1", depth=0.1, kept=(0, 1, 2, 3)),
        _stratum("D2", depth=0.2, kept=(0, 1, 2)),
        _stratum("D3", depth=0.3, kept=(0, 1)),
    )
    kernels = tuple(
        build_transport_kernel(
            transport_id=f"PR284-K{index}{index + 1}",
            source=source,
            target=target,
            matrix=((1.0,),),
            mask_transport_id=f"sha256:mask-k{index}{index + 1}",
            selection_transport_id=f"sha256:selection-k{index}{index + 1}",
            covariance_transport_id=f"sha256:covariance-k{index}{index + 1}",
            method_id="PR284-IDENTITY-TRANSPORT-V1",
            assumptions=("synthetic scalar identity transport",),
        )
        for index, (source, target) in enumerate(
            zip(strata[:-1], strata[1:], strict=True),
            start=1,
        )
    )
    return build_depth_path(
        path_id="PR284-NESTED-PATH-V1",
        strata=strata,
        kernels=kernels,
    )


def _threshold(multiplier: Fraction = Fraction(6, 5)):
    from common.depth_path_calibration import build_depth_path_threshold_contract

    return build_depth_path_threshold_contract(
        contract_id="PR284-DOOB-THRESHOLD-V1",
        multiplier=multiplier,
        registration_id="sha256:preregistered-before-path-inspection",
    )


def _law():
    from common.depth_path_calibration import build_depth_path_finite_target_law

    return build_depth_path_finite_target_law(
        law_id="PR284-FINITE-LAW-V1",
        common_target_id="PR284-CENTERED-TARGET-V1",
        atom_ids=("atom-a", "atom-b", "atom-c", "atom-d"),
        weights=(Fraction(1, 4),) * 4,
        common_target=(-3, -1, 1, 3),
        registration_id="sha256:finite-law-preregistered-v1",
    )


def _selection(law):
    from common.depth_path_calibration import build_depth_path_selection_contract

    return build_depth_path_selection_contract(
        selection_id="PR284-SELECTED-ATOM-V1",
        finite_target_law=law,
        selected_atom_id="atom-a",
        selected_atom_index=0,
        selection_rule_id="sha256:fixed-first-atom-rule-v1",
        registration_id="sha256:selection-preregistered-v1",
    )


def _proved_fixture() -> dict[str, object]:
    from htt.infer.depth_path_calibration import (
        build_depth_path_doob_calibration,
        build_depth_path_reverse_martingale_report,
    )

    path = _path()
    threshold = _threshold()
    law = _law()
    selection = _selection(law)
    report = build_depth_path_reverse_martingale_report(
        report_id="PR284-PROVED-REPORT-V1",
        path=path,
        threshold_contract=threshold,
        finite_target_law=law,
        selection_contract=selection,
        path_partitions=(
            ("a", "b", "c", "d"),
            ("left", "left", "right", "right"),
            ("all", "all", "all", "all"),
        ),
        sigma_field_ids=("sha256:F1", "sha256:F2", "sha256:F3"),
        filtration_id="sha256:decreasing-filtration-v1",
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        premise_evidence_id="sha256:pr271-finite-tower-v1",
    )
    calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-DOOB-CALIBRATION-V1",
        report=report,
        threshold_contract=threshold,
    )
    return {
        "path": path,
        "threshold": threshold,
        "law": law,
        "selection": selection,
        "report": report,
        "calibration": calibration,
    }


def _mock_plan(path, threshold):
    from htt.infer.depth_path_calibration import build_depth_path_matched_mock_plan

    return build_depth_path_matched_mock_plan(
        plan_id="PR284-MATCHED-MOCK-PLAN-V1",
        path=path,
        threshold_contract=threshold,
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        registration_id="sha256:mock-plan-preregistered-v1",
        null_law_id="sha256:matched-null-law-v1",
        mock_generator_id="sha256:matched-mock-generator-v1",
        ensemble_policy_id="sha256:ensemble-policy-v1",
        seed_policy_id="sha256:seed-policy-v1",
        matching_variable_ids=("mask", "selection", "noise", "depth"),
        acceptance_rule_id="sha256:mock-acceptance-rule-v1",
        multiplicity_rule_id="sha256:path-maximum-multiplicity-v1",
    )


def _fallback_fixture() -> dict[str, object]:
    from htt.infer.depth_path_calibration import (
        build_depth_path_doob_calibration,
        build_unproved_depth_path_reverse_martingale_report,
    )

    path = _path()
    threshold = _threshold()
    plan = _mock_plan(path, threshold)
    report = build_unproved_depth_path_reverse_martingale_report(
        report_id="PR284-UNPROVED-REPORT-V1",
        path=path,
        threshold_contract=threshold,
        filtration_id="sha256:unproved-filtration-v1",
        preprocessing_id="sha256:common-preprocessing-v1",
        estimator_id="sha256:conditional-estimator-v1",
        premise_evidence_id="sha256:support-nesting-only-v1",
        unresolved_reasons=(
            "explicit conditional-expectation partitions are not proved",
        ),
        matched_mock_plan=plan,
    )
    calibration = build_depth_path_doob_calibration(
        calibration_id="PR284-MOCK-FALLBACK-V1",
        report=report,
        threshold_contract=threshold,
    )
    return {
        "path": path,
        "threshold": threshold,
        "plan": plan,
        "report": report,
        "calibration": calibration,
    }


def _mutation_row(
    mutation_id: str,
    mutation_kind: str,
    reason: str,
    expected_error_marker: str,
    operation: Callable[[], object],
) -> dict[str, object]:
    from common.depth_path import DepthPathError

    killed = False
    try:
        operation()
    except (DepthPathError, TypeError) as exc:
        killed = expected_error_marker in str(exc)
    return {
        "mutation_id": mutation_id,
        "mutation_kind": mutation_kind,
        "executed": True,
        "activated": True,
        "killed": killed,
        "observed_outcome": BLOCK_TOKEN if killed else "MUTATION_SURVIVED",
        "observed_reason": reason if killed else "NO_FAIL_CLOSED_REJECTION",
    }


def _run_mutations() -> list[dict[str, object]]:
    from common.depth_path import (
        build_depth_path,
        build_transport_kernel,
    )
    from common.depth_path_calibration import (
        ReverseMartingalePremiseStatus,
        _build_depth_path_reverse_martingale_report_contract,
        revalidate_depth_path_finite_target_law,
        revalidate_depth_path_reverse_martingale_report,
        revalidate_depth_path_selection_contract,
    )
    from htt.infer.depth_path_calibration import (
        build_depth_path_doob_calibration,
        build_depth_path_reverse_martingale_report,
        build_unproved_depth_path_reverse_martingale_report,
    )

    operations: dict[str, Callable[[], object]] = {}

    def support_as_proof() -> object:
        fixture = _proved_fixture()
        return build_depth_path_reverse_martingale_report(
            report_id="MU284-SUPPORT-ONLY",
            path=fixture["path"],
            threshold_contract=fixture["threshold"],
            finite_target_law=None,
            selection_contract=None,
            path_partitions=(),
            sigma_field_ids=(),
            filtration_id="sha256:support-only",
            preprocessing_id="sha256:common-preprocessing-v1",
            estimator_id="sha256:conditional-estimator-v1",
            premise_evidence_id="sha256:support-nesting-only",
        )

    operations["MU284-SUPPORT-NESTING-AS-PROOF"] = support_as_proof

    def nonnested() -> object:
        source = _stratum("MUT-SOURCE", depth=0.1, kept=(0, 1))
        target = _stratum("MUT-TARGET", depth=0.2, kept=(0, 2))
        kernel = build_transport_kernel(
            transport_id="MU284-NONNESTED-K",
            source=source,
            target=target,
            matrix=((1.0,),),
            mask_transport_id="sha256:mut-mask",
            selection_transport_id="sha256:mut-selection",
            covariance_transport_id="sha256:mut-covariance",
            method_id="MU284-IDENTITY",
            assumptions=("mutation fixture",),
        )
        return build_depth_path(
            path_id="MU284-NONNESTED",
            strata=(source, target),
            kernels=(kernel,),
        )

    operations["MU284-NONNESTED-SUPPORT"] = nonnested

    def target_drift() -> object:
        law = copy(_law())
        object.__setattr__(law, "common_target", (Fraction(-2), Fraction(-1), Fraction(1), Fraction(2)))
        return revalidate_depth_path_finite_target_law(law)

    operations["MU284-TARGET-DRIFT"] = target_drift

    def report_builder_bypass() -> object:
        fixture = _proved_fixture()
        report = fixture["report"]
        return _build_depth_path_reverse_martingale_report_contract(
            path=fixture["path"],
            report_id="MU284-FORGED-PROVED-REPORT",
            path_content_id="sha256:no-registered-depth-path",
            stratum_content_ids=(
                "sha256:no-registered-stratum-1",
                "sha256:no-registered-stratum-2",
                "sha256:no-registered-stratum-3",
            ),
            threshold_contract=report.threshold_contract,
            filtration_id=report.filtration_id,
            filtration_direction=report.filtration_direction,
            preprocessing_id=report.preprocessing_id,
            estimator_id=report.estimator_id,
            premise_evidence_id="sha256:invented-premise-evidence",
            premise_status=report.premise_status,
            finite_target_law=report.finite_target_law,
            selection_contract=report.selection_contract,
            path_partitions=report.path_partitions,
            sigma_field_ids=report.sigma_field_ids,
            path_values=report.path_values,
            path_maximum_abs=report.path_maximum_abs,
            path_maximum_content_id=report.path_maximum_content_id,
            target_second_moment=report.target_second_moment,
            exact_tower_equalities=report.exact_tower_equalities,
            exact_tower_report_content_id=report.exact_tower_report_content_id,
            unresolved_reasons=(),
            matched_mock_plan=None,
        )

    operations["MU284-REPORT-BUILDER-BYPASS"] = report_builder_bypass

    def preprocessing_drift() -> object:
        fixture = _proved_fixture()
        return build_depth_path_doob_calibration(
            calibration_id="MU284-PREPROCESSING",
            report=fixture["report"],
            threshold_contract=fixture["threshold"],
            preprocessing_id="sha256:different-preprocessing",
        )

    operations["MU284-PREPROCESSING-DRIFT"] = preprocessing_drift

    def filtration_drift() -> object:
        fixture = _proved_fixture()
        return build_depth_path_reverse_martingale_report(
            report_id="MU284-FILTRATION",
            path=fixture["path"],
            threshold_contract=fixture["threshold"],
            finite_target_law=fixture["law"],
            selection_contract=fixture["selection"],
            path_partitions=(
                ("left", "left", "right", "right"),
                ("x", "y", "x", "y"),
                ("all", "all", "all", "all"),
            ),
            sigma_field_ids=("sha256:F1", "sha256:F2", "sha256:F3"),
            filtration_id="sha256:invalid-filtration",
            preprocessing_id="sha256:common-preprocessing-v1",
            estimator_id="sha256:conditional-estimator-v1",
            premise_evidence_id="sha256:pr271-finite-tower-v1",
        )

    operations["MU284-FILTRATION-DIRECTION-DRIFT"] = filtration_drift

    def threshold_drift() -> object:
        fixture = _proved_fixture()
        return build_depth_path_doob_calibration(
            calibration_id="MU284-THRESHOLD",
            report=fixture["report"],
            threshold_contract=_threshold(Fraction(2, 1)),
        )

    operations["MU284-THRESHOLD-DRIFT"] = threshold_drift

    def selection_drift() -> object:
        selection = copy(_selection(_law()))
        object.__setattr__(selection, "selected_atom_id", "atom-d")
        return revalidate_depth_path_selection_contract(selection)

    operations["MU284-ATOM-SELECTION-DRIFT"] = selection_drift

    def maximum_drift() -> object:
        report = copy(_proved_fixture()["report"])
        object.__setattr__(report, "path_maximum_abs", Fraction(99, 1))
        return revalidate_depth_path_reverse_martingale_report(report)

    operations["MU284-PATH-MAXIMUM-DRIFT"] = maximum_drift

    def law_drift() -> object:
        law = copy(_law())
        object.__setattr__(
            law,
            "weights",
            (Fraction(1, 8), Fraction(3, 8), Fraction(1, 4), Fraction(1, 4)),
        )
        return revalidate_depth_path_finite_target_law(law)

    operations["MU284-PROBABILITY-LAW-DRIFT"] = law_drift

    def estimator_drift() -> object:
        fixture = _proved_fixture()
        return build_depth_path_doob_calibration(
            calibration_id="MU284-ESTIMATOR",
            report=fixture["report"],
            threshold_contract=fixture["threshold"],
            estimator_id="sha256:different-estimator",
        )

    operations["MU284-ESTIMATOR-IDENTITY-DRIFT"] = estimator_drift

    def free_bound() -> object:
        fixture = _fallback_fixture()
        report = copy(fixture["report"])
        object.__setattr__(
            report,
            "premise_status",
            ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH,
        )
        return build_depth_path_doob_calibration(
            calibration_id="MU284-FREE-BOUND",
            report=report,
            threshold_contract=fixture["threshold"],
        )

    operations["MU284-FREE-BOUND-ON-UNPROVED"] = free_bound

    def plan_omitted() -> object:
        path = _path()
        threshold = _threshold()
        return build_unproved_depth_path_reverse_martingale_report(
            report_id="MU284-NO-PLAN",
            path=path,
            threshold_contract=threshold,
            filtration_id="sha256:unproved",
            preprocessing_id="sha256:common-preprocessing-v1",
            estimator_id="sha256:conditional-estimator-v1",
            premise_evidence_id="sha256:support-only",
            unresolved_reasons=("tower premise unproved",),
            matched_mock_plan=None,
        )

    operations["MU284-MATCHED-MOCK-PLAN-OMITTED"] = plan_omitted

    def plan_drift() -> object:
        fixture = _fallback_fixture()
        plan = copy(fixture["plan"])
        object.__setattr__(plan, "mock_generator_id", "sha256:post-result-generator")
        return build_unproved_depth_path_reverse_martingale_report(
            report_id="MU284-PLAN-DRIFT",
            path=fixture["path"],
            threshold_contract=fixture["threshold"],
            filtration_id="sha256:unproved",
            preprocessing_id="sha256:common-preprocessing-v1",
            estimator_id="sha256:conditional-estimator-v1",
            premise_evidence_id="sha256:support-only",
            unresolved_reasons=("tower premise unproved",),
            matched_mock_plan=plan,
        )

    operations["MU284-MATCHED-MOCK-PLAN-DRIFT"] = plan_drift

    return [
        _mutation_row(
            mutation_id,
            kind,
            _REASONS[mutation_id],
            _ERROR_MARKERS[mutation_id],
            operations[mutation_id],
        )
        for mutation_id, kind in _MUTATIONS
    ]


def _validate_mutations(rows: list[dict[str, object]]) -> None:
    if len(rows) != len(_MUTATIONS):
        raise RuntimeError("PR-284 mutation result count drifted")
    seen: set[str] = set()
    for row, (expected_id, expected_kind) in zip(rows, _MUTATIONS, strict=True):
        if set(row) != _MUTATION_KEYS:
            raise RuntimeError("PR-284 mutation result schema drifted")
        mutation_id = row.get("mutation_id")
        if mutation_id in seen:
            raise RuntimeError("PR-284 mutation result duplicated")
        seen.add(str(mutation_id))
        if (
            mutation_id != expected_id
            or row.get("mutation_kind") != expected_kind
            or row.get("executed") is not True
            or row.get("activated") is not True
            or row.get("killed") is not True
            or row.get("observed_outcome") != BLOCK_TOKEN
            or row.get("observed_reason") != _REASONS[expected_id]
        ):
            raise RuntimeError(f"PR-284 mutation failed closed: {expected_id}")


def _source_boundary() -> dict[str, object]:
    source_path = ROOT / "docs/research_program/vector_tensor/proof_registry_two_pillars.yaml"
    proof_path = ROOT / "docs/research_program/vector_tensor/proofs/PILLAR_S_CORE_PROOFS_V1.yaml"
    source = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    proof = yaml.safe_load(proof_path.read_text(encoding="utf-8"))
    source_rows = [
        row
        for row in source.get("entries", ())
        if row.get("legacy_id") == "TF-11-MASK-PATH-MARTINGALE"
    ]
    proof_rows = [
        row
        for row in proof.get("records", ())
        if row.get("obligation_id") == "TF-11-MASK-PATH-MARTINGALE"
    ]
    if len(source_rows) != 1 or len(proof_rows) != 1:
        raise RuntimeError("TF-11 source/proof record is not unique")
    source_row, proof_row = source_rows[0], proof_rows[0]
    if (
        source_row.get("status") != "ORACLE_VERIFIED"
        or proof_row.get("source_proof_adjudication_status") != "NOT_ADJUDICATED"
        or proof_row.get("relation_to_source") != "FINITE_REGISTERED_PATH_ONLY"
        or proof_row.get("verdict") != "PROVED_FINITE_REGISTERED_PATH"
        or "known fast-oracle instability is hidden or promoted"
        not in proof_row.get("counterexample_boundaries", ())
    ):
        raise RuntimeError("TF-11 finite-only boundary drifted")
    return {
        "obligation_id": "TF-11-MASK-PATH-MARTINGALE",
        "source_registry_path": str(source_path.relative_to(ROOT)),
        "source_registry_sha256": _sha256_bytes(source_path.read_bytes()),
        "source_registry_status": source_row["status"],
        "typed_proof_path": str(proof_path.relative_to(ROOT)),
        "typed_proof_sha256": _sha256_bytes(proof_path.read_bytes()),
        "source_statement_identity_sha256": proof_row[
            "source_statement_identity_sha256"
        ],
        "source_proof_adjudication_status": proof_row[
            "source_proof_adjudication_status"
        ],
        "relation_to_source": proof_row["relation_to_source"],
        "typed_proof_verdict": proof_row["verdict"],
        "counterexample_boundaries": proof_row["counterexample_boundaries"],
        "claim_ceiling": proof_row["claim_ceiling"],
        "pr284_effect": "runtime_execution_without_general_theorem_promotion",
    }


def _exact_event_probability(report, calibration) -> Fraction:
    """Recompute the registered law-level maximal event without static answers."""

    law = report.finite_target_law
    if law is None or calibration.threshold_squared is None:
        raise RuntimeError("proved fixture is missing its exact law or threshold")
    rung_values: list[tuple[Fraction, ...]] = []
    for labels in report.path_partitions:
        mass: dict[str, Fraction] = {}
        weighted: dict[str, Fraction] = {}
        for probability, target, label in zip(
            law.weights,
            law.common_target,
            labels,
            strict=True,
        ):
            mass[label] = mass.get(label, Fraction()) + probability
            weighted[label] = weighted.get(label, Fraction()) + probability * target
        conditional = {label: weighted[label] / mass[label] for label in mass}
        rung_values.append(tuple(conditional[label] for label in labels))
    event = Fraction()
    for index, probability in enumerate(law.weights):
        maximum_squared = max(abs(row[index]) for row in rung_values) ** 2
        if maximum_squared >= calibration.threshold_squared:
            event += probability
    return event


def _build_payload() -> dict[str, object]:
    spec = _load_spec()
    proved = _proved_fixture()
    fallback = _fallback_fixture()
    mutations = _run_mutations()
    _validate_mutations(mutations)
    event_probability = _exact_event_probability(
        proved["report"],
        proved["calibration"],
    )
    probability_bound = proved["calibration"].probability_upper_bound
    if probability_bound is None or event_probability > probability_bound:
        raise RuntimeError("registered exact maximal event violates its Doob bound")
    source_bindings = [
        {"path": path, "sha256": _sha256_bytes((ROOT / path).read_bytes())}
        for path in BOUND_SOURCES
    ]
    payload: dict[str, object] = {
        "schema": "htt.pr284.depth_path_doob_artifact.v1",
        "pr_id": "PR-284",
        "terminal_status": PASS_TOKEN,
        "gate_id": "G6",
        "owner": "HTT",
        "contributors": ["OBSSTAT", "MIO", "COMMON"],
        "scope": "synthetic premise-bound finite depth-path calibration",
        "claim_tier": "diagnostic_only",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "synthetic_diagnostic",
        "transfer_source": "none",
        "observed_data_executed": False,
        "public_use": False,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
        "sky_support_status": "synthetic_nested_masks_bound_by_DepthPath",
        "covariance_status": "not_used_by_exact_finite_tower",
        "null_mock_status": {
            "proved_fixture": "not_used_exact_finite_fixture",
            "fallback_fixture": "required_not_executed",
        },
        "assumptions": list(_ASSUMPTIONS),
        "caveats": list(_CAVEATS),
        "allowed_uses": spec["allowed_uses"],
        "forbidden_uses": spec["forbidden_uses"],
        "generating_command": "python3 -B scripts/codex_harness/run_pr284_depth_path_doob.py build",
        "generation_identity": {
            "mode": "EXACT_BOUND_SOURCE_HASHES",
            "git_or_worktree_identity": "EXTERNAL_CANDIDATE_SEAL_REQUIRED",
            "reason": "Embedding the commit containing this receipt would be circular; the external candidate seal binds the final git identity.",
        },
        "mathematical_boundary": _source_boundary(),
        "proved_fixture": {
            "finite_target_law": proved["law"].as_payload(),
            "selection_contract": proved["selection"].as_payload(),
            "threshold_contract": proved["threshold"].as_payload(),
            "report": proved["report"].as_payload(),
            "calibration": proved["calibration"].as_payload(),
            "exact_event_probability": f"{event_probability.numerator}/{event_probability.denominator}",
            "doob_probability_upper_bound": f"{probability_bound.numerator}/{probability_bound.denominator}",
            "event_probability_within_bound": event_probability <= probability_bound,
        },
        "unproved_fixture": {
            "matched_mock_plan": fallback["plan"].as_payload(),
            "report": fallback["report"].as_payload(),
            "calibration": fallback["calibration"].as_payload(),
            "matched_mocks_executed": False,
            "probability_bound": None,
        },
        "mutations": mutations,
        "future_consumer_contract": spec["future_consumer_contract"],
        "source_bindings": source_bindings,
    }
    payload["receipt_content_sha256"] = _canonical_sha256(payload)
    return payload


def _pytest(paths: tuple[str, ...]) -> int:
    env = dict(os.environ)
    for key in (
        "PR284_DEPTH_PATH_RUNNER_ACTIVE",
        "PYTHONHOME",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTHONSTARTUP",
    ):
        env.pop(key, None)
    env["PYTHONPATH"] = os.pathsep.join(
        (str(ROOT), str(ROOT / "htt/src"), str(ROOT / "htt"))
    )
    return subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-o",
            "addopts=",
            "-q",
            *paths,
        ],
        cwd=ROOT,
        env=env,
        check=False,
    ).returncode


def _portable() -> int:
    status = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if status.returncode != 0 or status.stdout:
        print("portable replay requires a clean committed candidate", file=sys.stderr)
        return 1
    tracked = _tracked_paths()
    source_before = _manifest(ROOT, tracked)
    archived = subprocess.run(
        ["git", "archive", "--format=tar", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if archived.returncode != 0:
        print("git archive failed", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="pr284-portable-") as directory:
        clean_root = Path(directory) / "source"
        clean_root.mkdir()
        with tarfile.open(fileobj=BytesIO(archived.stdout), mode="r:") as archive:
            archive.extractall(clean_root, filter="data")
        clean_before = _manifest(clean_root, tracked)
        if clean_before != source_before:
            print("clean archive manifest differs from source", file=sys.stderr)
            return 1
        env = dict(os.environ)
        scrubbed = (
            "PR284_DEPTH_PATH_RUNNER_ACTIVE",
            "PYTHONHOME",
            "PYTEST_ADDOPTS",
            "PYTEST_PLUGINS",
            "PYTHONSTARTUP",
        )
        for key in (*scrubbed, "PYTHONPATH"):
            env.pop(key, None)
        env["PYTHONPATH"] = os.pathsep.join(
            (
                str(clean_root),
                str(clean_root / "htt/src"),
                str(clean_root / "htt"),
            )
        )
        command = [
            sys.executable,
            "-B",
            "scripts/codex_harness/run_pr284_depth_path_doob.py",
            "check",
        ]
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            cwd=clean_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        elapsed = time.perf_counter() - started
        clean_after = _manifest(clean_root, tracked)
        source_after = _manifest(ROOT, tracked)
        if clean_after != clean_before or source_after != source_before:
            print("portable replay changed tracked bytes", file=sys.stderr)
            return 1
        evidence = {
            "schema": "PR284_PORTABLE_CLEAN_REPLAY_EVIDENCE_V1",
            "tracked_source_manifest": source_before,
            "interpreter_and_dependency_versions": _versions(),
            "scrubbed_environment_keys": {
                key: key not in env for key in scrubbed
            }
            | {"PYTHONPATH": "CLEAN_ROOT_ONLY"},
            "exact_command": command,
            "exact_command_exit_code": completed.returncode,
            "exact_command_runtime_seconds": elapsed,
            "nested_stdout_sha256": hashlib.sha256(
                completed.stdout.encode("utf-8")
            ).hexdigest(),
            "nested_stderr_sha256": hashlib.sha256(
                completed.stderr.encode("utf-8")
            ).hexdigest(),
            "source_root_pre_hash": source_before["manifest_sha256"],
            "source_root_post_hash": source_after["manifest_sha256"],
            "clean_root_pre_hash": clean_before["manifest_sha256"],
            "clean_root_post_hash": clean_after["manifest_sha256"],
            "source_root_differs_from_execution_root": ROOT != clean_root,
        }
        print(json.dumps(evidence, sort_keys=True))
        return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=("build", "check", "focused", "adjacent", "smoke", "portable"),
    )
    args = parser.parse_args(argv)
    if args.mode == "focused":
        return _pytest(("tests/contracts/test_depth_path_doob_calibration.py",))
    if args.mode == "adjacent":
        return _pytest(
            (
                "tests/contracts/test_depth_path.py",
                "tests/contracts/test_pillar_s_core.py",
            )
        )
    if args.mode == "smoke":
        return int(
            subprocess.run(
                [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-m", "smoke"],
                cwd=ROOT,
                check=False,
            ).returncode
        )
    if args.mode == "portable":
        return _portable()
    if args.mode == "build":
        try:
            _validate_output_destination_for_write()
        except RuntimeError as exc:
            print(f"{BLOCK_TOKEN}: {exc}", file=sys.stderr)
            return 1
    _activate_sources()
    try:
        expected = _render(_build_payload())
    except Exception as exc:
        print(f"{BLOCK_TOKEN}: {exc}", file=sys.stderr)
        return 2
    if args.mode == "check":
        if (
            OUTPUT.is_symlink()
            or not OUTPUT.is_file()
            or OUTPUT.stat().st_nlink != 1
            or OUTPUT.read_bytes() != expected
        ):
            print(f"{BLOCK_TOKEN}: receipt is absent or stale", file=sys.stderr)
            return 1
        print(PASS_TOKEN)
        return 0
    _atomic_write(expected)
    print(_sha256_bytes(expected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
