#!/usr/bin/env python3
"""Portable build/check/test runner for PR-283 weak identification."""

from __future__ import annotations

from copy import copy
import hashlib
from importlib import metadata as importlib_metadata
from io import BytesIO
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any, Mapping

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/post_pr275/pr283_spec.yaml"
OUTPUT = ROOT / "docs/generated/pr283_weak_identification_receipt.json"
PASS_TOKEN = "PASS_WEAK_IDENTIFICATION_ABSTENTION"
BLOCK_TOKEN = "BLOCKED_WEAK_IDENTIFICATION_CONTRACT"
UNITS = "dimensionless_beta_c_equals_1"
BOUND_SOURCES = (
    "docs/research_program/post_pr275/pr283_spec.yaml",
    "docs/research_program/post_pr275/pr283_publication_policy.json",
    "htt/src/common/source_separation.py",
    "htt/src/common/tensor_foundations_oracle.py",
    "htt/src/common/pillar_t_cas.py",
    "htt/src/common/open_set_response_classes.py",
    "docs/research_program/vector_tensor/frozen_sources/pr272_open_set_response_classes.py",
    "docs/research_program/vector_tensor/integration/PR283_PR272_OPEN_SET_V1_RELOCATION.json",
    "docs/research_program/vector_tensor/proof_registry_two_pillars.yaml",
    "docs/research_program/vector_tensor/proofs/PILLAR_T_CAS_PROOFS_V1.yaml",
    "htt/htt/htt/departure/velocity_frame_decomposition.py",
    "htt/htt/htt/statistics/__init__.py",
    "htt/htt/htt/statistics/open_set_response_classes.py",
    "scripts/codex_harness/run_pr283_weak_identification.py",
    "tests/contracts/test_weak_identification.py",
    "tests/contracts/test_pillar_t_cas.py",
)
_MUTATIONS = (
    ("MU283-WEAK-AS-SEPARABLE", "weak_status_promoted_to_separable"),
    (
        "MU283-THRESHOLD-IDENTITY-DRIFT",
        "registered_threshold_contract_identity_changed",
    ),
    ("MU283-COVARIANCE-DRIFT", "source_gate_covariance_identity_changed"),
    ("MU283-ANGLE-IDENTITY-DRIFT", "principal_angle_bytes_changed_without_report_reseal"),
    ("MU283-SINGULAR-IDENTITY-DRIFT", "joint_singular_value_bytes_changed_without_report_reseal"),
    ("MU283-NORMALIZER-IDENTITY-DRIFT", "normalizer_map_identity_changed_without_geometry_replay"),
    ("MU283-WEAK-PRECEDENCE-DRIFT", "weak_gate_applied_after_open_set_labels"),
    ("MU283-SINGULAR-CARDINALITY-DRIFT", "joint_singular_value_count_exceeds_parameter_dimension"),
    ("MU283-THRESHOLD-OMISSION", "registered_practical_threshold_contract_omitted"),
    ("MU283-SOURCE-REPORT-REPLAY-DRIFT", "source_geometry_angles_changed_after_factory_measurement"),
)
_EXPECTED_REASONS = {
    "MU283-WEAK-AS-SEPARABLE": "MUTANT_FORCED_RESPONSE_CLASS_CANDIDATE",
    "MU283-THRESHOLD-IDENTITY-DRIFT": (
        "THRESHOLD_CONTRACT_IDENTITY_REJECTED"
    ),
    "MU283-COVARIANCE-DRIFT": "COVARIANCE_QUOTIENT_BINDING_REJECTED",
    "MU283-ANGLE-IDENTITY-DRIFT": "PRINCIPAL_ANGLE_IDENTITY_REJECTED",
    "MU283-SINGULAR-IDENTITY-DRIFT": "JOINT_SINGULAR_IDENTITY_REJECTED",
    "MU283-NORMALIZER-IDENTITY-DRIFT": "NORMALIZER_MAP_IDENTITY_REJECTED",
    "MU283-WEAK-PRECEDENCE-DRIFT": "WEAK_GATE_PRECEDENCE_ENFORCED",
    "MU283-SINGULAR-CARDINALITY-DRIFT": "SINGULAR_VALUE_CARDINALITY_REJECTED",
    "MU283-THRESHOLD-OMISSION": "MISSING_PR283_THRESHOLD_CONTRACT_REJECTED",
    "MU283-SOURCE-REPORT-REPLAY-DRIFT": "SOURCE_GEOMETRY_REPLAY_REJECTED",
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
_REQUIRED_IDENTITIES = (
    "source_geometry_report_id",
    "covariance_id",
    "nuisance_tangent_id",
    "principal_angles_content_id",
    "joint_singular_values_content_id",
    "threshold_contract_content_id",
    "normalizer_id",
    "normalizer_source_identity",
    "normalizer_coordinate_map_content_id",
    "parameter_coordinate_units",
)
_RECEIPT_METADATA = (
    "owner",
    "scope",
    "claim_tier_and_level",
    "transfer_source",
    "synthetic_sky_and_covariance_status",
    "null_mock_status",
    "assumptions",
    "caveats",
    "generating_command_or_procedure",
    "exact_source_bindings",
    "git_commit_or_worktree_state",
)
_ASSUMPTIONS = (
    "PR-256 response providers and geometry report are factory-derived and "
    "replay-bound.",
    "Principal angles and singular values are evaluated on the same "
    "covariance-supported nuisance quotient.",
    "Practical thresholds are registered before any open-set observation is classified.",
    "Full rank is necessary but not sufficient for a point response-class candidate.",
)
_ALLOWED_USES = (
    "Synthetic runtime validation of weak local/global source identification.",
    "Mandatory abstention before later multi-probe and claim-capability integration.",
    "Diagnostic reporting of the measured rank, angle, and conditioning ladder.",
)
_FORBIDDEN_USES = (
    "A point estimate or nearest response-class fallback under weak identification.",
    "Observed-data source attribution, global-tilt detection, or physical parameter inference.",
    "Native solver validation, geometry detection, or Bianchi family identification.",
    "HTT posterior/evidence production or MIO truth certification.",
    "PR-153 artifacts are forbidden input.",
)
_CAVEATS = (
    "Thresholds define a registered diagnostic operating point, not a "
    "universal physical constant.",
    "The singular-value threshold is conditional on the exact registered "
    "dimensionless-beta normalizer and is not coordinate-rescaling invariant.",
    "Synthetic fixtures do not establish observed-sky covariance, mask, or null validity.",
    "WEAKLY_IDENTIFIED is an abstention state, not partial evidence for either source hypothesis.",
    "PR-151 partial/background data is forbidden input.",
    "PR-153 artifacts are forbidden input.",
)


def _activate_sources() -> None:
    for path in reversed((ROOT / "htt", ROOT / "htt/src")):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


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


def _render(payload: object) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
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


def _id(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("ascii")).hexdigest()


def _load_contract() -> tuple[dict[str, Any], object]:
    _activate_sources()
    from common.source_separation import (
        build_weak_identification_threshold_contract,
    )

    raw = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError("PR-283 spec must be a mapping")
    if (
        raw.get("schema") != "htt.pr283.weak_identification_spec.v1"
        or raw.get("pr_id") != "PR-283"
        or raw.get("owner") != "HTT"
        or raw.get("contributors") != ["COMMON", "MIO"]
        or raw.get("change_set_id") != "CS-PR283-WEAK-IDENTIFICATION"
        or raw.get("publication_group_id") != "PG-PR283-WEAK-IDENTIFICATION"
        or raw.get("dependencies") != ["PR-280"]
        or raw.get("dependency_contract")
        != {"upstream_id": "PR-280", "mode": "requires_terminal_receipt"}
    ):
        raise RuntimeError("PR-283 identity or dependency contract drifted")
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
        raise RuntimeError("PR-283 claim or family boundary drifted")
    gate = raw.get("gate", {})
    if (
        gate.get("gate_id") != "G4"
        or gate.get("pass_token") != PASS_TOKEN
        or gate.get("block_token") != BLOCK_TOKEN
    ):
        raise RuntimeError("PR-283 G4 terminal contract drifted")
    mathematics = raw.get("mathematical_boundary", {})
    if (
        mathematics.get("source_oracle_id")
        != "TF-10-LOCAL-GLOBAL-SEPARATION"
        or mathematics.get("source_registry_status") != "ORACLE_VERIFIED"
        or mathematics.get("conditional_algebra_obligation") != "VT-T12"
        or mathematics.get("source_proof_adjudication_status")
        != "NOT_ADJUDICATED"
        or mathematics.get("conditional_verdict")
        != "PROVED_CONDITIONAL_LINEAR_ALGEBRA"
        or mathematics.get("pr283_effect")
        != "runtime_execution_without_proof_promotion"
    ):
        raise RuntimeError("PR-283 mathematical/proof boundary drifted")
    threshold = raw.get("threshold_contract", {})
    if (
        threshold.get("minimum_principal_angle_radians") != 0.2
        or threshold.get(
            "minimum_normalizer_bound_relative_joint_singular_value"
        )
        != 0.01
        or "not invariant" not in threshold.get("representation_boundary", "")
        or "cannot contain more entries" not in threshold.get(
            "singular_value_cardinality", ""
        )
        or tuple(threshold.get("required_identities", ()))
        != _REQUIRED_IDENTITIES
    ):
        raise RuntimeError("PR-283 threshold/representation contract drifted")
    pairs = tuple(
        (row.get("mutation_id"), row.get("mutation_kind"))
        for row in raw.get("mutation_registry", ())
        if isinstance(row, dict)
    )
    if pairs != _MUTATIONS:
        raise RuntimeError("PR-283 mutation registry drifted")
    receipt = raw.get("receipt_contract", {})
    if (
        receipt.get("output_path")
        != "docs/generated/pr283_weak_identification_receipt.json"
        or tuple(receipt.get("required_bindings", ())) != BOUND_SOURCES
        or receipt.get("terminal_precedence")
        != ["BLOCKED_CONTRACT_INVALID", BLOCK_TOKEN, PASS_TOKEN]
        or tuple(receipt.get("required_metadata", ())) != _RECEIPT_METADATA
        or receipt.get("mutation_rule")
        != (
            "Every registered mutation must execute and be killed. Missing, "
            "skipped, duplicated, reordered, unmapped, or surviving mutations "
            "block G4."
        )
    ):
        raise RuntimeError("PR-283 receipt contract drifted")
    runtime = raw.get("runtime_contract", {})
    weak_output = runtime.get("weak_branch_output", {})
    if (
        runtime.get("required_gate_status")
        != "SourceSeparationGateStatus.WEAKLY_IDENTIFIED"
        or "before response-equivalence" not in runtime.get(
            "weak_gate_precedence", ""
        )
        or weak_output.get("open_set_status") != "TYPE_UNIDENTIFIED"
        or weak_output.get("candidate_class_id") is not None
        or weak_output.get("point_estimate") != "forbidden"
        or weak_output.get("returned_equivalence_class")
        != "exact_PR258_response_class_ids_only"
    ):
        raise RuntimeError("PR-283 runtime abstention contract drifted")
    if (
        tuple(raw.get("assumptions", ())) != _ASSUMPTIONS
        or tuple(raw.get("allowed_uses", ())) != _ALLOWED_USES
        or tuple(raw.get("forbidden_uses", ())) != _FORBIDDEN_USES
        or tuple(raw.get("caveats", ())) != _CAVEATS
    ):
        raise RuntimeError("PR-283 assumptions or claim boundary drifted")
    contract = build_weak_identification_threshold_contract(
        minimum_principal_angle_radians=0.2,
        minimum_normalizer_bound_relative_joint_singular_value=0.01,
        parameter_coordinate_units=UNITS,
    )
    return raw, contract


def _load_mathematical_boundary() -> dict[str, Any]:
    from common.tensor_foundations_oracle import tf10_local_global_separation

    source_path = (
        ROOT
        / "docs/research_program/vector_tensor/"
        "proof_registry_two_pillars.yaml"
    )
    pillar_path = (
        ROOT
        / "docs/research_program/vector_tensor/proofs/"
        "PILLAR_T_CAS_PROOFS_V1.yaml"
    )
    source_registry = yaml.safe_load(source_path.read_text(encoding="utf-8"))
    source_rows = [
        row
        for row in source_registry.get("entries", ())
        if row.get("legacy_id") == "TF-10-LOCAL-GLOBAL-SEPARATION"
    ]
    if len(source_rows) != 1:
        raise RuntimeError("TF-10 source registry record is not unique")
    source = source_rows[0]
    required_statuses = [
        "MISSING_RESPONSE_PROVIDER",
        "NON_IDENTIFIED",
        "SUM_ONLY",
        "WEAKLY_IDENTIFIED",
        "SEPARABLE_CANDIDATE",
    ]
    if (
        source.get("status") != "ORACLE_VERIFIED"
        or source.get("required_status_set") != required_statuses
    ):
        raise RuntimeError("TF-10 source registry status drifted")
    oracle = tf10_local_global_separation()
    if (
        oracle.get("proposition") != "TF-10-LOCAL-GLOBAL-SEPARATION"
        or oracle.get("ok") is not True
        or oracle.get("dipole_only_rank") != 3
        or oracle.get("weakly_identified_is_full_rank") is not True
    ):
        raise RuntimeError("TF-10 executable oracle failed")
    pillar_registry = yaml.safe_load(pillar_path.read_text(encoding="utf-8"))
    pillar_rows = [
        row
        for row in pillar_registry.get("records", ())
        if row.get("obligation_id") == "VT-T12"
    ]
    if len(pillar_rows) != 1:
        raise RuntimeError("VT-T12 Pillar-T record is not unique")
    pillar = pillar_rows[0]
    if (
        pillar_registry.get("aggregate_cas_verdict") != "CAS_4AXIS_PASS"
        or pillar.get("source_proof_adjudication_status")
        != "NOT_ADJUDICATED"
        or pillar.get("relation_to_source")
        != "CONDITIONAL_LINEAR_ALGEBRA_CORE"
        or pillar.get("verdict") != "PROVED_CONDITIONAL_LINEAR_ALGEBRA"
        or pillar.get("claim_ceiling") != "diagnostic_only"
    ):
        raise RuntimeError("VT-T12 conditional algebra boundary drifted")
    return {
        "source_oracle": {
            "proposition_id": source["legacy_id"],
            "registry_path": str(source_path.relative_to(ROOT)),
            "registry_sha256": _sha256_bytes(source_path.read_bytes()),
            "registry_status": source["status"],
            "required_status_set": source["required_status_set"],
            "executable_result": oracle,
        },
        "conditional_algebra": {
            "obligation_id": pillar["obligation_id"],
            "registry_path": str(pillar_path.relative_to(ROOT)),
            "registry_sha256": _sha256_bytes(pillar_path.read_bytes()),
            "aggregate_cas_verdict": pillar_registry["aggregate_cas_verdict"],
            "source_proof_adjudication_status": pillar[
                "source_proof_adjudication_status"
            ],
            "relation_to_source": pillar["relation_to_source"],
            "verdict": pillar["verdict"],
            "assumptions": pillar["assumptions"],
            "counterexample_boundaries": pillar["counterexample_boundaries"],
            "claim_ceiling": pillar["claim_ceiling"],
        },
        "pr283_effect": "runtime_execution_without_proof_promotion",
        "separable_candidate_semantics": "downstream_diagnostic_eligibility_only",
    }


def _build_case(
    fixture_id: str,
    *,
    angle: float,
    global_amplitude: float,
    threshold_contract: object,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from common.anchor_geometry import (
        NormalizerKind,
        NormalizerPurpose,
        NormalizerSpec,
    )
    from common.anchored_response_geometry import anchored_numeric_content_id
    from common.open_set_response_classes import (
        ResponseClassSourceSemantics,
        ResponseSupportKind,
        build_response_class_manifold,
        build_response_equivalence_report,
        classify_open_set_response,
    )
    from common.transfer_registry import TransferSource
    from htt.departure.velocity_frame_decomposition import (
        ResponseProviderAvailability,
        ResponseProviderKind,
        SourceHypothesis,
        VelocityComponent,
        measure_source_response_geometry,
        register_source_response_provider,
    )
    from htt.statistics.open_set_response_classes import (
        source_separation_gate_from_pr256,
    )

    covariance = np.eye(2)
    local_response = np.asarray([[1.0], [0.0]], dtype=float)
    global_response = global_amplitude * np.asarray(
        [[math.cos(angle)], [math.sin(angle)]], dtype=float
    )
    local_provider_id = _id(f"{fixture_id}:local-provider")
    global_provider_id = _id(f"{fixture_id}:global-provider")

    def provider(hypothesis, response, provider_id):
        local = hypothesis is SourceHypothesis.LOCAL_BOOST
        return register_source_response_provider(
            provider_id=provider_id,
            hypothesis=hypothesis,
            velocity_component=(
                VelocityComponent.BETA_MO if local else VelocityComponent.BETA_RM
            ),
            provider_kind=ResponseProviderKind.ANALYTIC,
            availability=ResponseProviderAvailability.AVAILABLE,
            observable_labels=("obs-x", "obs-y"),
            parameter_labels=(
                ("beta_MO_amplitude",) if local else ("beta_RM_amplitude",)
            ),
            response=response,
            transfer_id=_id("pr283-transfer-none"),
            transfer_source=TransferSource.NONE,
            basis="registered synthetic basis",
            epoch_window="registered synthetic window",
            assumptions=("first-order analytic response",),
            caveats=("hypothesis-only response",),
        )

    normalizer = NormalizerSpec(
        normalizer_id="pr283-dimensionless-beta-normalizer",
        kind=NormalizerKind.MES_ANCHORED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=("beta_MO_amplitude", "beta_RM_amplitude"),
        coordinate_map=((1.0, 0.0), (0.0, 1.0)),
        source_identity="PR283-DIMENSIONLESS-BETA-C-EQUALS-ONE",
        assumptions=("dimensionless beta coordinates with c equals one",),
    )
    report = measure_source_response_geometry(
        local_provider=provider(
            SourceHypothesis.LOCAL_BOOST,
            local_response,
            local_provider_id,
        ),
        global_provider=provider(
            SourceHypothesis.GLOBAL_TILT,
            global_response,
            global_provider_id,
        ),
        covariance=covariance,
        normalizer=normalizer,
        covariance_id=anchored_numeric_content_id(covariance),
        mask_id=_id("pr283-mask"),
        separation_threshold_radians=0.2,
    )

    def response_class(
        class_id: str,
        provider_id: str,
        source_semantics: object,
        source_response: np.ndarray,
        node: list[float],
    ):
        return build_response_class_manifold(
            class_id=class_id,
            support_kind=ResponseSupportKind.FINITE_ANALYTIC_SUPPORT,
            provider_id=provider_id,
            observable_labels=("obs-x", "obs-y"),
            convention_id=_id("pr283-convention"),
            nuisance_policy_id=_id("pr283-nuisance-none"),
            support_nodes=[node],
            transfer_source=TransferSource.NONE,
            source_semantics=source_semantics,
            source_response_id=anchored_numeric_content_id(source_response),
        )

    classes = (
        response_class(
            "response-class-local",
            local_provider_id,
            ResponseClassSourceSemantics.LOCAL_BOOST,
            local_response,
            [-3.0, 0.0],
        ),
        response_class(
            "response-class-global",
            global_provider_id,
            ResponseClassSourceSemantics.GLOBAL_TILT,
            global_response,
            [3.0, 0.0],
        ),
    )
    equivalence = build_response_equivalence_report(
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=0.1,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
    )
    gate = source_separation_gate_from_pr256(
        report,
        classes=classes,
        covariance=covariance,
        nuisance_tangent=None,
        normalizer=normalizer,
        threshold_contract=threshold_contract,
    )
    classified = classify_open_set_response(
        observation=[-3.0, 0.0],
        classes=classes,
        equivalence_report=equivalence,
        covariance=covariance,
        nuisance_tangent=None,
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        source_separation_gate=gate,
    )
    decision = gate.source_separation_decision
    assert decision is not None
    row = {
        "fixture_id": fixture_id,
        "pr256_status": report.status.value,
        "source_separation_gate_status": gate.status.value,
        "open_set_status": classified.status.value,
        "candidate_class_id": classified.candidate_class_id,
        "returned_response_class_ids": list(
            classified.returned_equivalence_class
        ),
        "local_rank": report.local_rank,
        "global_rank": report.global_rank,
        "joint_rank": report.joint_rank,
        "minimum_principal_angle_radians": (
            decision.minimum_principal_angle_radians
        ),
        "minimum_relative_joint_singular_value": (
            decision.minimum_relative_joint_singular_value
        ),
        "source_separation_decision": decision.as_payload(),
        "source_separation_decision_id": decision.decision_id,
    }
    context = {
        "report": report,
        "classes": classes,
        "equivalence": equivalence,
        "gate": gate,
        "classified": classified,
        "covariance": covariance,
        "normalizer": normalizer,
        "threshold_contract": threshold_contract,
    }
    return row, context


def _build_cases(threshold_contract: object):
    specifications = (
        ("pr283.full-rank-small-angle.v1", 0.1, 1.0),
        ("pr283.full-rank-small-relative-singular-value.v1", math.pi / 2.0, 0.005),
        ("pr283.rank-deficient-sum-only.v1", 0.0, 1.0),
        ("pr283.well-separated-full-rank.v1", math.pi / 2.0, 1.0),
    )
    rows = []
    contexts = {}
    for fixture_id, angle, amplitude in specifications:
        row, context = _build_case(
            fixture_id,
            angle=angle,
            global_amplitude=amplitude,
            threshold_contract=threshold_contract,
        )
        rows.append(row)
        contexts[fixture_id] = context
    return rows, contexts


def _mutation_row(
    mutation_id: str,
    mutation_kind: str,
    *,
    activated: bool,
    killed: bool,
    reason: str,
) -> dict[str, object]:
    return {
        "mutation_id": mutation_id,
        "mutation_kind": mutation_kind,
        "executed": True,
        "activated": bool(activated),
        "killed": bool(killed),
        "observed_outcome": BLOCK_TOKEN if killed else "SURVIVED",
        "observed_reason": reason,
    }


def _run_mutations(contexts: Mapping[str, Mapping[str, Any]]) -> list[dict[str, object]]:
    from common.open_set_response_classes import (
        OpenSetClassificationStatus,
        OpenSetResponseError,
        ResponseClassSourceSemantics,
        SourceSeparationGateStatus,
        _build_source_separation_gate,
        build_response_equivalence_report,
        classify_open_set_response,
    )
    from common.source_separation import (
        SourceSeparationError,
        build_weak_identification_threshold_contract,
        evaluate_source_separation,
        revalidate_source_separation_decision,
    )
    from htt.statistics.open_set_response_classes import (
        source_separation_gate_from_pr256,
    )

    weak = contexts["pr283.full-rank-small-angle.v1"]
    ill_conditioned = contexts[
        "pr283.full-rank-small-relative-singular-value.v1"
    ]
    gate = weak["gate"]
    decision = gate.source_separation_decision
    assert decision is not None
    rows = []

    weak_status_mutant = copy(gate)
    object.__setattr__(
        weak_status_mutant,
        "status",
        SourceSeparationGateStatus.SEPARABLE_CANDIDATE,
    )
    forced_candidate = classify_open_set_response(
        observation=[-3.0, 0.0],
        classes=weak["classes"],
        equivalence_report=weak["equivalence"],
        covariance=weak["covariance"],
        nuisance_tangent=None,
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        source_separation_gate=weak_status_mutant,
    )
    rows.append(
        _mutation_row(
            *_MUTATIONS[0],
            activated=(
                forced_candidate.status
                is OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
                and forced_candidate.candidate_class_id is not None
            ),
            killed=(
                weak["classified"].candidate_class_id is None
                and gate.status is SourceSeparationGateStatus.WEAKLY_IDENTIFIED
                and forced_candidate.candidate_class_id is not None
            ),
            reason=_EXPECTED_REASONS[_MUTATIONS[0][0]],
        )
    )

    drifted_threshold = build_weak_identification_threshold_contract(
        minimum_principal_angle_radians=0.2,
        minimum_normalizer_bound_relative_joint_singular_value=0.001,
        parameter_coordinate_units=UNITS,
    )
    try:
        source_separation_gate_from_pr256(
            weak["report"],
            classes=weak["classes"],
            covariance=weak["covariance"],
            nuisance_tangent=None,
            normalizer=weak["normalizer"],
            threshold_contract=drifted_threshold,
        )
        threshold_killed = False
    except OpenSetResponseError:
        threshold_killed = True
    rows.append(
        _mutation_row(
            *_MUTATIONS[1],
            activated=(
                drifted_threshold.contract_id
                != weak["threshold_contract"].contract_id
            ),
            killed=threshold_killed,
            reason=_EXPECTED_REASONS[_MUTATIONS[1][0]],
        )
    )

    drifted_covariance = np.diag((2.0, 1.0))
    try:
        classify_open_set_response(
            observation=[-3.0, 0.0],
            classes=weak["classes"],
            equivalence_report=weak["equivalence"],
            covariance=drifted_covariance,
            nuisance_tangent=None,
            unknown_squared_distance_threshold=4.0,
            decision_squared_margin=0.5,
            covariance_null_tolerance=1.0e-10,
            absolute_tolerance=1.0e-12,
            relative_tolerance=1.0e-12,
            source_separation_gate=gate,
        )
        covariance_killed = False
    except OpenSetResponseError:
        covariance_killed = True
    rows.append(
        _mutation_row(
            *_MUTATIONS[2],
            activated=not np.array_equal(drifted_covariance, weak["covariance"]),
            killed=covariance_killed,
            reason=_EXPECTED_REASONS[_MUTATIONS[2][0]],
        )
    )

    for pair, field, reason in (
        (_MUTATIONS[3], "principal_angles_content_id", _EXPECTED_REASONS[_MUTATIONS[3][0]]),
        (_MUTATIONS[4], "joint_singular_values_content_id", _EXPECTED_REASONS[_MUTATIONS[4][0]]),
    ):
        mutant = copy(decision)
        object.__setattr__(mutant, field, _id(f"mutated:{field}"))
        try:
            revalidate_source_separation_decision(mutant)
            killed = False
        except SourceSeparationError:
            killed = True
        rows.append(
            _mutation_row(
                *pair,
                activated=getattr(mutant, field) != getattr(decision, field),
                killed=killed,
                reason=reason,
            )
        )

    normalizer_mutant = copy(decision)
    object.__setattr__(
        normalizer_mutant,
        "normalizer_coordinate_map_id",
        _id("mutated:normalizer-map"),
    )
    report = weak["report"]
    try:
        _build_source_separation_gate(
            status=normalizer_mutant.status.value,
            report_id=normalizer_mutant.source_geometry_report_id,
            classes=weak["classes"],
            covariance=weak["covariance"],
            nuisance_tangent=None,
            source_observable_labels=report.observable_labels,
            source_covariance=report.covariance_replay_matrix,
            source_covariance_id=report.covariance_id,
            source_nuisance_tangent=report.nuisance_replay_matrix,
            source_provider_ids=(
                (
                    ResponseClassSourceSemantics.LOCAL_BOOST.value,
                    report.local_provider.provider_id,
                ),
                (
                    ResponseClassSourceSemantics.GLOBAL_TILT.value,
                    report.global_provider.provider_id,
                ),
            ),
            source_response_ids=(
                (
                    ResponseClassSourceSemantics.LOCAL_BOOST.value,
                    report.local_provider.response_id,
                ),
                (
                    ResponseClassSourceSemantics.GLOBAL_TILT.value,
                    report.global_provider.response_id,
                ),
            ),
            source_transfer_contracts=(
                (
                    ResponseClassSourceSemantics.LOCAL_BOOST.value,
                    report.local_provider.transfer_id,
                    report.local_provider.transfer_source.value,
                ),
                (
                    ResponseClassSourceSemantics.GLOBAL_TILT.value,
                    report.global_provider.transfer_id,
                    report.global_provider.transfer_source.value,
                ),
            ),
            source_frame_contracts=(
                (
                    ResponseClassSourceSemantics.LOCAL_BOOST.value,
                    report.local_provider.basis,
                    report.local_provider.epoch_window,
                    report.local_provider.perturbative_order,
                ),
                (
                    ResponseClassSourceSemantics.GLOBAL_TILT.value,
                    report.global_provider.basis,
                    report.global_provider.epoch_window,
                    report.global_provider.perturbative_order,
                ),
            ),
            source_mask_id=report.mask_id,
            source_normalizer_id=report.normalizer_id,
            source_normalizer_identity=report.normalizer_source_identity,
            source_normalizer_coordinate_map_id=report.normalizer_coordinate_map_id,
            source_parameter_coordinate_units=report.parameter_coordinate_units,
            source_separation_decision=normalizer_mutant,
        )
        normalizer_killed = False
    except OpenSetResponseError:
        normalizer_killed = True
    rows.append(
        _mutation_row(
            *_MUTATIONS[5],
            activated=(
                normalizer_mutant.normalizer_coordinate_map_id
                != decision.normalizer_coordinate_map_id
            ),
            killed=normalizer_killed,
            reason=_EXPECTED_REASONS[_MUTATIONS[5][0]],
        )
    )

    far_classified = classify_open_set_response(
        observation=[100.0, 0.0],
        classes=weak["classes"],
        equivalence_report=weak["equivalence"],
        covariance=weak["covariance"],
        nuisance_tangent=None,
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        source_separation_gate=gate,
    )
    broad_equivalence = build_response_equivalence_report(
        classes=weak["classes"],
        covariance=weak["covariance"],
        nuisance_tangent=None,
        equivalence_squared_distance_tolerance=40.0,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
    )
    equivalent_classified = classify_open_set_response(
        observation=[-3.0, 0.0],
        classes=weak["classes"],
        equivalence_report=broad_equivalence,
        covariance=weak["covariance"],
        nuisance_tangent=None,
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        source_separation_gate=gate,
    )
    far_precedence_mutant = classify_open_set_response(
        observation=[100.0, 0.0],
        classes=weak["classes"],
        equivalence_report=weak["equivalence"],
        covariance=weak["covariance"],
        nuisance_tangent=None,
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        source_separation_gate=weak_status_mutant,
    )
    equivalent_precedence_mutant = classify_open_set_response(
        observation=[-3.0, 0.0],
        classes=weak["classes"],
        equivalence_report=broad_equivalence,
        covariance=weak["covariance"],
        nuisance_tangent=None,
        unknown_squared_distance_threshold=4.0,
        decision_squared_margin=0.5,
        covariance_null_tolerance=1.0e-10,
        absolute_tolerance=1.0e-12,
        relative_tolerance=1.0e-12,
        source_separation_gate=weak_status_mutant,
    )
    rows.append(
        _mutation_row(
            *_MUTATIONS[6],
            activated=(
                far_precedence_mutant.status
                is OpenSetClassificationStatus.UNKNOWN_CLASS
                and equivalent_precedence_mutant.status
                is OpenSetClassificationStatus.EQUIVALENCE_CLASS
                and len(broad_equivalence.components[0]) > 1
            ),
            killed=(
                far_classified.status.value == "TYPE_UNIDENTIFIED"
                and far_classified.candidate_class_id is None
                and equivalent_classified.status.value == "TYPE_UNIDENTIFIED"
                and equivalent_classified.candidate_class_id is None
                and far_precedence_mutant.status
                is OpenSetClassificationStatus.UNKNOWN_CLASS
                and equivalent_precedence_mutant.status
                is OpenSetClassificationStatus.EQUIVALENCE_CLASS
            ),
            reason=_EXPECTED_REASONS[_MUTATIONS[6][0]],
        )
    )

    oversized_singular_values = (
        *decision.joint_singular_values,
        decision.joint_singular_values[-1],
    )
    try:
        evaluate_source_separation(
            source_geometry_report_id=decision.source_geometry_report_id,
            covariance_id=decision.covariance_id,
            nuisance_tangent_id=decision.nuisance_tangent_id,
            normalizer_id=decision.normalizer_id,
            normalizer_source_identity=decision.normalizer_source_identity,
            normalizer_coordinate_map_id=decision.normalizer_coordinate_map_id,
            parameter_coordinate_units=decision.parameter_coordinate_units,
            provider_available=decision.provider_available,
            covariance_supported=decision.covariance_supported,
            local_parameter_count=decision.local_parameter_count,
            global_parameter_count=decision.global_parameter_count,
            local_rank=decision.local_rank,
            global_rank=decision.global_rank,
            joint_rank=decision.joint_rank,
            principal_angles_radians=decision.principal_angles_radians,
            joint_singular_values=oversized_singular_values,
            threshold_contract=decision.threshold_contract,
        )
        cardinality_killed = False
    except SourceSeparationError:
        cardinality_killed = True
    rows.append(
        _mutation_row(
            *_MUTATIONS[7],
            activated=(
                len(oversized_singular_values)
                > decision.local_parameter_count + decision.global_parameter_count
            ),
            killed=cardinality_killed,
            reason=_EXPECTED_REASONS[_MUTATIONS[7][0]],
        )
    )

    try:
        source_separation_gate_from_pr256(
            ill_conditioned["report"],
            classes=ill_conditioned["classes"],
            covariance=ill_conditioned["covariance"],
            nuisance_tangent=None,
            normalizer=ill_conditioned["normalizer"],
            threshold_contract=None,
        )
        omission_killed = False
    except OpenSetResponseError:
        omission_killed = True
    rows.append(
        _mutation_row(
            *_MUTATIONS[8],
            activated=(
                ill_conditioned["report"].status.value
                == "SEPARABLE_CANDIDATE"
            ),
            killed=omission_killed,
            reason=_EXPECTED_REASONS[_MUTATIONS[8][0]],
        )
    )

    replay_mutant = copy(weak["report"])
    object.__setattr__(
        replay_mutant,
        "principal_angles_radians",
        (math.pi / 2.0,),
    )
    object.__setattr__(
        replay_mutant,
        "minimum_principal_angle_radians",
        math.pi / 2.0,
    )
    try:
        source_separation_gate_from_pr256(
            replay_mutant,
            classes=weak["classes"],
            covariance=weak["covariance"],
            nuisance_tangent=None,
            normalizer=weak["normalizer"],
            threshold_contract=weak["threshold_contract"],
        )
        replay_killed = False
    except OpenSetResponseError:
        replay_killed = True
    rows.append(
        _mutation_row(
            *_MUTATIONS[9],
            activated=(
                replay_mutant.principal_angles_radians
                != weak["report"].principal_angles_radians
            ),
            killed=replay_killed,
            reason=_EXPECTED_REASONS[_MUTATIONS[9][0]],
        )
    )
    return rows


def _validate_mutation_results(rows: object) -> list[str]:
    errors = []
    if not isinstance(rows, list):
        return ["mutation results must be a list"]
    actual_pairs = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != _MUTATION_KEYS:
            errors.append(f"mutation row {index} has invalid fields")
            continue
        actual_pairs.append((row.get("mutation_id"), row.get("mutation_kind")))
        mutation_id = row.get("mutation_id")
        if (
            row.get("executed") is not True
            or row.get("activated") is not True
            or row.get("killed") is not True
            or row.get("observed_outcome") != BLOCK_TOKEN
            or row.get("observed_reason") != _EXPECTED_REASONS.get(mutation_id)
        ):
            errors.append(f"mutation row {index} did not execute and die exactly")
    if tuple(actual_pairs) != _MUTATIONS:
        errors.append("mutation results do not match exact registered order")
    return errors


def _build_artifact() -> dict[str, Any]:
    spec, threshold_contract = _load_contract()
    mathematical_boundary = _load_mathematical_boundary()
    cases, contexts = _build_cases(threshold_contract)
    returned_mutations = _run_mutations(contexts)
    errors = _validate_mutation_results(returned_mutations)
    mutations = (
        returned_mutations if isinstance(returned_mutations, list) else []
    )
    expected = {
        "pr283.full-rank-small-angle.v1": ("WEAKLY_IDENTIFIED", None),
        "pr283.full-rank-small-relative-singular-value.v1": (
            "WEAKLY_IDENTIFIED",
            None,
        ),
        "pr283.rank-deficient-sum-only.v1": ("SUM_ONLY", None),
        "pr283.well-separated-full-rank.v1": (
            "SEPARABLE_CANDIDATE",
            "response-class-local",
        ),
    }
    if tuple(row.get("fixture_id") for row in cases) != tuple(expected):
        errors.append("case results do not match exact registered order")
    for row in cases:
        fixture_id = row.get("fixture_id")
        if fixture_id not in expected:
            errors.append("case result contains an unregistered fixture")
            continue
        status, candidate = expected[fixture_id]
        if (
            row["source_separation_gate_status"] != status
            or row["candidate_class_id"] != candidate
            or any(
                not value.startswith("response-class-")
                for value in row["returned_response_class_ids"]
            )
        ):
            errors.append(f"case {fixture_id} violated its registered outcome")
    terminal = {
        "g4_outcome": PASS_TOKEN if not errors else BLOCK_TOKEN,
        "reasons": errors,
        "mutation_survivors": [
            (
                row.get("mutation_id", "INVALID_MUTATION_ROW")
                if isinstance(row, dict)
                else "INVALID_MUTATION_ROW"
            )
            for row in mutations
            if not isinstance(row, dict) or not row.get("killed")
        ],
    }
    source_bindings = [
        {
            "path": relative,
            "sha256": _sha256_bytes((ROOT / relative).read_bytes()),
        }
        for relative in BOUND_SOURCES
    ]
    unsigned = {
        "schema": "htt.pr283.weak_identification_artifact.v1",
        "artifact_id": "PR283-WEAK-IDENTIFICATION-ABSTENTION",
        "owner": "HTT",
        "contributors": ["COMMON", "MIO"],
        "scope": "synthetic runtime weak-identification and open-set abstention",
        "claim_tier": "diagnostic_only",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "synthetic_diagnostic",
        "transfer_source": "none",
        "sky_support_status": "synthetic_registered_response_coordinates",
        "covariance_status": "synthetic_positive_definite_identity",
        "null_mock_status": "not_used_by_structural_runtime_gate",
        "observed_data_executed": False,
        "public_use": False,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
        "threshold_contract": threshold_contract.as_payload(),
        "threshold_contract_id": threshold_contract.contract_id,
        "mathematical_boundary": mathematical_boundary,
        "cases": cases,
        "mutations": mutations,
        "terminal": terminal,
        "source_bindings": source_bindings,
        "generating_command": (
            "python3 -B scripts/codex_harness/"
            "run_pr283_weak_identification.py build"
        ),
        "generation_identity": {
            "mode": "EXACT_BOUND_SOURCE_HASHES",
            "git_or_worktree_identity": "EXTERNAL_CANDIDATE_SEAL_REQUIRED",
            "reason": (
                "Embedding the commit/tree containing this artifact would be circular; "
                "acceptance binds the candidate in the external seal and review run."
            ),
        },
        "assumptions": spec["assumptions"],
        "allowed_uses": spec["allowed_uses"],
        "forbidden_uses": spec["forbidden_uses"],
        "caveats": spec["caveats"],
    }
    return {**unsigned, "artifact_content_sha256": _canonical_sha256(unsigned)}


def _pytest(paths: tuple[str, ...]) -> int:
    env = dict(os.environ)
    for key in ("PYTHONHOME", "PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONSTARTUP"):
        env.pop(key, None)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "htt/src"), str(ROOT / "htt")))
    return subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
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
    with tempfile.TemporaryDirectory(prefix="pr283-portable-") as directory:
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
            "PYTHONHOME",
            "PYTEST_ADDOPTS",
            "PYTEST_PLUGINS",
            "PYTHONSTARTUP",
        )
        for key in (*scrubbed, "PYTHONPATH"):
            env.pop(key, None)
        env["PYTHONPATH"] = os.pathsep.join(
            (str(clean_root / "htt/src"), str(clean_root / "htt"))
        )
        command = [
            sys.executable,
            "-B",
            "scripts/codex_harness/run_pr283_weak_identification.py",
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
            "schema": "PR283_PORTABLE_CLEAN_REPLAY_EVIDENCE_V1",
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
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] not in {
        "build",
        "check",
        "focused",
        "adjacent",
        "caller-migrations",
        "harness-portability",
        "portable",
    }:
        print(
            "usage: run_pr283_weak_identification.py "
            "{build|check|focused|adjacent|caller-migrations|"
            "harness-portability|portable}",
            file=sys.stderr,
        )
        return 2
    mode = args[0]
    if mode == "focused":
        return _pytest(("tests/contracts/test_weak_identification.py",))
    if mode == "adjacent":
        return _pytest(
            (
                "tests/pr_cards/test_pr_256_velocity_frame_decomposition.py",
                "tests/pr_cards/test_pr_258_open_set_response_classes.py",
            )
        )
    if mode == "caller-migrations":
        return _pytest(
            (
                "tests/pr_cards/test_pr_258_open_set_response_classes.py",
                "tests/contracts/test_anisotropy_type_report.py",
                "tests/integration/test_vector_tensor_blind_synthetic.py",
            )
        )
    if mode == "harness-portability":
        return _pytest(("tests/contracts/test_harness_profiles_v4.py",))
    if mode == "portable":
        return _portable()
    if mode == "build":
        try:
            _validate_output_destination_for_write()
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    try:
        artifact = _build_artifact()
    except (KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"PR-283 artifact build failed: {exc}", file=sys.stderr)
        return 1
    if artifact["terminal"]["g4_outcome"] != PASS_TOKEN:
        print(
            "PR-283 G4 did not pass: "
            + json.dumps(artifact["terminal"], sort_keys=True),
            file=sys.stderr,
        )
        return 1
    rendered = _render(artifact)
    if mode == "build":
        _atomic_write(rendered)
        print(f"wrote {OUTPUT.relative_to(ROOT)} sha256={_sha256_bytes(rendered)}")
        return 0
    if (
        OUTPUT.is_symlink()
        or not OUTPUT.is_file()
        or OUTPUT.stat().st_nlink != 1
    ):
        print(f"missing generated receipt: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    actual = OUTPUT.read_bytes()
    if actual != rendered:
        print(
            "generated PR-283 receipt is stale: "
            f"expected={_sha256_bytes(rendered)} actual={_sha256_bytes(actual)}",
            file=sys.stderr,
        )
        return 1
    print(f"ok {OUTPUT.relative_to(ROOT)} sha256={_sha256_bytes(actual)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
