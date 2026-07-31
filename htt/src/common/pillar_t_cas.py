"""Typed PR-270 Pillar-T CAS and conditional-response proof records.

PR-270 has two intentionally separate lanes:

* exact polynomial obligations that require one blind four-axis CAS verdict;
* conditional linear-algebra and refusal statements that can be checked
  without pretending that a missing CAS engine or native geometry payload
  exists.

This module validates the frozen contract, runner-observed adjudication, and
proof registry.  It also exposes small exact/typed witnesses for VT-T11,
VT-T12, VT-T13, and VT-T14.  A three-axis agreement is never a four-axis
verdict.  None of these records is an observational result, native-solver
validation, morphology atlas, likelihood, posterior, or family label.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import yaml


CAS_CONTRACT_PATH = (
    "docs/research_program/vector_tensor/cas/CAS_CONTRACT.json"
)
CAS_ADJUDICATION_PATH = (
    "docs/research_program/vector_tensor/cas/CAS_ADJUDICATION.json"
)
CAS_REGISTRY_PATH = (
    "docs/research_program/vector_tensor/proofs/"
    "PILLAR_T_CAS_PROOFS_V1.yaml"
)
CAS_SPEC_PATH = "docs/research_program/vector_tensor/pr270_spec.yaml"
CAS_SCHEMA_VERSION = "htt.pillar_t_cas_proofs.v1"
CAS_CONTRACT_ID = "CAS-PR270-VECTOR-TENSOR-ORBIT-001"

REQUIRED_AXES = (
    "wolfram_xact",
    "sympy",
    "sage_singular",
    "lean",
)
ALLOWED_AGGREGATE_VERDICTS = (
    "CAS_4AXIS_PASS",
    "CAS_PASS_WITH_REGISTERED_EXCEPTION",
    "CAS_CONFLICT",
    "CAS_BLOCKED",
    "CAS_FAIL",
)
EXACT_OBLIGATIONS = (
    "vt_t5_discriminant_identity",
    "vt_t5_shape_bound_strata",
    "vt_t6_cayley_hamilton",
    "vt_t6_contraction_reduction",
    "vt_t7_krylov_vandermonde",
    "vt_t7_krylov_gram",
    "vt_t7_cyclicity_boundary",
    "vt_t8_local_jacobian_factor",
    "vt_t8_principal_witness_rank",
    "vt_t8_global_separation_not_promoted",
    "vt_t13_shape_chain_rule_core",
    "vt_t13_source_decomposition_not_promoted",
)
PROOF_IDS = tuple(
    f"VT-T{index}" for index in (*range(5, 9), *range(11, 15))
)

_AXIS_STATUSES = {
    "PASS",
    "FAIL",
    "MISALIGNED_ASSUMPTIONS",
    "BLOCKED_PLATFORM_OR_LICENSE",
    "BLOCKED_PACKAGE_UNAVAILABLE",
    "BLOCKED_RESOURCE_LIMIT",
    "NOT_APPLICABLE_COMPUTATION_CLASS",
    "INCONCLUSIVE",
}
_BLOCKED_AXIS_STATUSES = {
    "BLOCKED_PLATFORM_OR_LICENSE",
    "BLOCKED_PACKAGE_UNAVAILABLE",
    "BLOCKED_RESOURCE_LIMIT",
}


class PillarTCasError(ValueError):
    """Raised when a PR-270 contract or typed witness fails closed."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class AggregateCASVerdict(_StringEnum):
    CAS_4AXIS_PASS = "CAS_4AXIS_PASS"
    CAS_PASS_WITH_REGISTERED_EXCEPTION = (
        "CAS_PASS_WITH_REGISTERED_EXCEPTION"
    )
    CAS_CONFLICT = "CAS_CONFLICT"
    CAS_BLOCKED = "CAS_BLOCKED"
    CAS_FAIL = "CAS_FAIL"


class PillarTStatementVerdict(_StringEnum):
    CAS_BLOCKED_REQUIRED_AXIS = "CAS_BLOCKED_REQUIRED_AXIS"
    PROVED_CONDITIONAL_LINEAR_ALGEBRA = (
        "PROVED_CONDITIONAL_LINEAR_ALGEBRA"
    )
    PARTIAL_CHAIN_RULE_CAS_BLOCKED = "PARTIAL_CHAIN_RULE_CAS_BLOCKED"
    INCONCLUSIVE_NATIVE_GEOMETRY_GATE = (
        "INCONCLUSIVE_NATIVE_GEOMETRY_GATE"
    )


class GeometryEscalationStatus(_StringEnum):
    PARTIAL_KINEMATIC_DIAGNOSTIC = "PARTIAL_KINEMATIC_DIAGNOSTIC"
    INCONCLUSIVE_NATIVE_GEOMETRY_GATE = (
        "INCONCLUSIVE_NATIVE_GEOMETRY_GATE"
    )


def _repo_file(repo: Path, relative: str | Path) -> Path:
    root = repo.resolve()
    value = Path(relative)
    path = value.resolve() if value.is_absolute() else (root / value).resolve()
    if not value.is_absolute():
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise PillarTCasError(
                f"path escapes repository: {relative}"
            ) from exc
    if path.is_symlink() or not path.is_file():
        raise PillarTCasError(f"required file is missing: {relative}")
    return path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_object(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PillarTCasError(f"invalid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise PillarTCasError(f"JSON root must be an object: {path}")
    return payload


def _yaml_object(path: Path) -> dict[str, object]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise PillarTCasError(f"invalid YAML: {path}") from exc
    if not isinstance(payload, dict):
        raise PillarTCasError(f"YAML root must be a mapping: {path}")
    return payload


def _exact_text(value: object, name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value.strip() != value
    ):
        raise PillarTCasError(f"{name} must be non-empty trimmed text")
    return value


def _text_tuple(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise PillarTCasError(f"{name} must be a list")
    out = tuple(_exact_text(item, name) for item in value)
    if len(out) != len(set(out)):
        raise PillarTCasError(f"{name} contains duplicates")
    return out


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise PillarTCasError(f"{name} must be a mapping")
    return value


@dataclass(frozen=True)
class CASContract:
    contract_id: str
    sha256: str
    required_axes: tuple[str, ...]
    obligations: tuple[str, ...]
    expected_exact_values: Mapping[str, str]
    claim_ceiling: str
    exception_count: int


def load_cas_contract(
    repo: Path,
    relative: str | Path = CAS_CONTRACT_PATH,
) -> CASContract:
    """Load and fail-closed validate the one PR-270 R3 CAS contract."""

    path = _repo_file(repo, relative)
    payload = _json_object(path)
    if payload.get("schema_version") != 2:
        raise PillarTCasError("CAS contract schema_version must equal 2")
    if payload.get("risk_tier") != "R3":
        raise PillarTCasError("PR-270 CAS contract must remain R3")
    axes = _text_tuple(payload.get("required_axes"), "required_axes")
    if axes != REQUIRED_AXES:
        raise PillarTCasError(
            "required axes must remain Wolfram, SymPy, Sage, Lean in order"
        )
    identity = _mapping(payload.get("identity"), "identity")
    contract_id = _exact_text(identity.get("contract_id"), "contract_id")
    if contract_id != CAS_CONTRACT_ID:
        raise PillarTCasError("unexpected PR-270 CAS contract identity")
    if identity.get("claim_ceiling") != "diagnostic_only":
        raise PillarTCasError("CAS claim ceiling must remain diagnostic_only")
    target = _mapping(payload.get("target"), "target")
    obligations = _text_tuple(
        target.get("exact_test_obligations"),
        "target.exact_test_obligations",
    )
    if obligations != EXACT_OBLIGATIONS:
        raise PillarTCasError("CAS obligations drifted or changed order")
    expected = _mapping(
        target.get("expected_exact_values"),
        "target.expected_exact_values",
    )
    if not expected or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in expected.items()
    ):
        raise PillarTCasError("expected exact values must be string-valued")
    exceptions = _mapping(
        payload.get("exceptions_adjudication"),
        "exceptions_adjudication",
    ).get("preregistered_exceptions")
    if not isinstance(exceptions, list):
        raise PillarTCasError("preregistered_exceptions must be a list")
    if exceptions:
        raise PillarTCasError(
            "PR-270 did not preregister a computation-class exception"
        )
    source_hashes = identity.get("source_input_hashes")
    if not isinstance(source_hashes, list) or not source_hashes:
        raise PillarTCasError("source_input_hashes must be non-empty")
    for index, row in enumerate(source_hashes):
        item = _mapping(row, f"source_input_hashes[{index}]")
        source = _repo_file(
            repo,
            _exact_text(item.get("path"), f"source_input_hashes[{index}].path"),
        )
        expected_sha = _exact_text(
            item.get("sha256"),
            f"source_input_hashes[{index}].sha256",
        )
        if _sha256(source) != expected_sha:
            raise PillarTCasError(
                f"frozen source input hash drifted: {source.relative_to(repo)}"
            )
    return CASContract(
        contract_id=contract_id,
        sha256=_sha256(path),
        required_axes=axes,
        obligations=obligations,
        expected_exact_values={
            str(key): str(value) for key, value in expected.items()
        },
        claim_ceiling="diagnostic_only",
        exception_count=0,
    )


@dataclass(frozen=True)
class CASAdjudication:
    contract_sha256: str
    aggregate_status: AggregateCASVerdict
    axis_statuses: Mapping[str, str]
    verification_state: str
    evidence_origin: str
    claim_promotion_cas_eligible: bool
    claim_promotion_cas_requirement: str

    @property
    def success_dependency_satisfied(self) -> bool:
        return (
            self.aggregate_status is AggregateCASVerdict.CAS_4AXIS_PASS
            and self.claim_promotion_cas_eligible
            and self.claim_promotion_cas_requirement == "SATISFIED"
        )


def load_cas_adjudication(
    repo: Path,
    relative: str | Path = CAS_ADJUDICATION_PATH,
) -> CASAdjudication:
    """Validate runner-observed evidence and the no-majority state machine."""

    contract = load_cas_contract(repo)
    payload = _json_object(_repo_file(repo, relative))
    if payload.get("schema_version") != 2:
        raise PillarTCasError("CAS adjudication schema_version must equal 2")
    if payload.get("contract_id") != contract.contract_id:
        raise PillarTCasError("CAS adjudication contract_id drifted")
    if payload.get("contract_sha256") != contract.sha256:
        raise PillarTCasError("CAS adjudication contract hash drifted")
    required = _text_tuple(
        payload.get("required_axes"), "adjudication.required_axes"
    )
    if required != contract.required_axes:
        raise PillarTCasError("adjudication required axes drifted")
    try:
        aggregate = AggregateCASVerdict(
            _exact_text(payload.get("aggregate_status"), "aggregate_status")
        )
    except ValueError as exc:
        raise PillarTCasError("unknown aggregate CAS verdict") from exc
    statuses = _mapping(payload.get("axis_statuses"), "axis_statuses")
    if set(statuses) != set(contract.required_axes):
        raise PillarTCasError(
            "axis_statuses must cover each required axis"
        )
    if any(status not in _AXIS_STATUSES for status in statuses.values()):
        raise PillarTCasError("axis_statuses contains an invalid status")
    missing = payload.get("missing_axes")
    if missing != []:
        raise PillarTCasError(
            "runner-observed adjudication must name blocked axes, not omit them"
        )
    if payload.get("exceptions_applied") != []:
        raise PillarTCasError("post-hoc or unregistered CAS exception detected")
    evidence = _mapping(
        payload.get("execution_evidence"), "execution_evidence"
    )
    if set(evidence) != set(contract.required_axes):
        raise PillarTCasError("execution evidence does not cover all axes")
    for axis in contract.required_axes:
        status = statuses[axis]
        row = _mapping(evidence.get(axis), f"execution_evidence.{axis}")
        if row.get("axis") != axis or row.get("derived_status") != status:
            raise PillarTCasError(f"{axis} evidence/status binding drifted")
        if row.get("evidence_origin") != "runner_observed_local_subprocess":
            raise PillarTCasError(f"{axis} evidence is not runner-observed")
        executed = row.get("solver_executed")
        if type(executed) is not bool:
            raise PillarTCasError(f"{axis}.solver_executed must be boolean")
        if status == "PASS" and executed is not True:
            raise PillarTCasError(f"{axis} PASS requires solver execution")
        if status in _BLOCKED_AXIS_STATUSES and executed is not False:
            raise PillarTCasError(f"{axis} blocked status cannot claim execution")
    any_blocked = any(
        status in _BLOCKED_AXIS_STATUSES for status in statuses.values()
    )
    any_fail = any(status == "FAIL" for status in statuses.values())
    any_conflict = any(
        status in {"MISALIGNED_ASSUMPTIONS", "INCONCLUSIVE"}
        for status in statuses.values()
    )
    if any_fail and aggregate is not AggregateCASVerdict.CAS_FAIL:
        raise PillarTCasError("failed axis must aggregate to CAS_FAIL")
    if not any_fail and any_blocked and (
        aggregate is not AggregateCASVerdict.CAS_BLOCKED
    ):
        raise PillarTCasError("blocked required axis must aggregate to CAS_BLOCKED")
    if not any_fail and not any_blocked and any_conflict and (
        aggregate is not AggregateCASVerdict.CAS_CONFLICT
    ):
        raise PillarTCasError(
            "assumption/inconclusive axis must aggregate to CAS_CONFLICT"
        )
    all_pass = all(status == "PASS" for status in statuses.values())
    if aggregate is AggregateCASVerdict.CAS_4AXIS_PASS and not all_pass:
        raise PillarTCasError("CAS_4AXIS_PASS requires all four PASS statuses")
    eligible = payload.get("claim_promotion_cas_eligible")
    if type(eligible) is not bool:
        raise PillarTCasError(
            "claim_promotion_cas_eligible must be an exact boolean"
        )
    requirement = _exact_text(
        payload.get("claim_promotion_cas_requirement"),
        "claim_promotion_cas_requirement",
    )
    if (eligible or requirement == "SATISFIED") and not all_pass:
        raise PillarTCasError(
            "three-axis agreement cannot satisfy the R3 CAS component"
        )
    if payload.get("verification_state") != "RUNNER_OBSERVED_EXECUTION":
        raise PillarTCasError("stored-result replay is not PR-270 execution evidence")
    if payload.get("evidence_origin") != "runner_observed_local_subprocess":
        raise PillarTCasError("unexpected adjudication evidence origin")
    return CASAdjudication(
        contract_sha256=contract.sha256,
        aggregate_status=aggregate,
        axis_statuses={
            axis: str(statuses[axis]) for axis in contract.required_axes
        },
        verification_state="RUNNER_OBSERVED_EXECUTION",
        evidence_origin="runner_observed_local_subprocess",
        claim_promotion_cas_eligible=eligible,
        claim_promotion_cas_requirement=requirement,
    )


@dataclass(frozen=True)
class PillarTCasProofRecord:
    obligation_id: str
    relation_to_source: str
    verdict: PillarTStatementVerdict
    assumptions: tuple[str, ...]
    domains: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    counterexample_boundaries: tuple[str, ...]
    claim_ceiling: str


def load_pillar_t_cas_registry(
    repo: Path,
    relative: str | Path = CAS_REGISTRY_PATH,
) -> tuple[PillarTCasProofRecord, ...]:
    """Load the additive PR-270 records without rewriting source statuses."""

    contract = load_cas_contract(repo)
    adjudication = load_cas_adjudication(repo)
    payload = _yaml_object(_repo_file(repo, relative))
    if payload.get("schema") != CAS_SCHEMA_VERSION:
        raise PillarTCasError("unexpected Pillar-T CAS registry schema")
    if payload.get("authority") != "PR-270":
        raise PillarTCasError("Pillar-T CAS registry authority drifted")
    if payload.get("claim_ceiling") != "diagnostic_only":
        raise PillarTCasError("registry claim ceiling drifted")
    if payload.get("source_proof_adjudication_status") != "NOT_ADJUDICATED":
        raise PillarTCasError("PR-270 must not rewrite source theorem statuses")
    if payload.get("cas_contract_sha256") != contract.sha256:
        raise PillarTCasError("registry CAS contract hash drifted")
    adjudication_path = _repo_file(repo, CAS_ADJUDICATION_PATH)
    if payload.get("cas_adjudication_sha256") != _sha256(
        adjudication_path
    ):
        raise PillarTCasError("registry CAS adjudication hash drifted")
    if payload.get("aggregate_cas_verdict") != adjudication.aggregate_status.value:
        raise PillarTCasError("registry aggregate CAS verdict drifted")
    records = payload.get("records")
    if not isinstance(records, list):
        raise PillarTCasError("registry records must be a list")
    out: list[PillarTCasProofRecord] = []
    for index, row in enumerate(records):
        item = _mapping(row, f"records[{index}]")
        obligation_id = _exact_text(
            item.get("obligation_id"), f"records[{index}].obligation_id"
        )
        try:
            verdict = PillarTStatementVerdict(
                _exact_text(item.get("verdict"), f"{obligation_id}.verdict")
            )
        except ValueError as exc:
            raise PillarTCasError(
                f"{obligation_id} has an invalid statement verdict"
            ) from exc
        source_status = item.get("source_proof_adjudication_status")
        if source_status != "NOT_ADJUDICATED":
            raise PillarTCasError(
                f"{obligation_id} rewrites source adjudication status"
            )
        claim_ceiling = item.get("claim_ceiling")
        if claim_ceiling != "diagnostic_only":
            raise PillarTCasError(f"{obligation_id} claim ceiling drifted")
        out.append(
            PillarTCasProofRecord(
                obligation_id=obligation_id,
                relation_to_source=_exact_text(
                    item.get("relation_to_source"),
                    f"{obligation_id}.relation_to_source",
                ),
                verdict=verdict,
                assumptions=_text_tuple(
                    item.get("assumptions"), f"{obligation_id}.assumptions"
                ),
                domains=_text_tuple(
                    item.get("domains"), f"{obligation_id}.domains"
                ),
                evidence_refs=_text_tuple(
                    item.get("evidence_refs"),
                    f"{obligation_id}.evidence_refs",
                ),
                counterexample_boundaries=_text_tuple(
                    item.get("counterexample_boundaries"),
                    f"{obligation_id}.counterexample_boundaries",
                ),
                claim_ceiling="diagnostic_only",
            )
        )
    if tuple(record.obligation_id for record in out) != PROOF_IDS:
        raise PillarTCasError(
            "registry must contain VT-T5-8 and VT-T11-14 once"
        )
    expected_verdicts = {
        **{
            f"VT-T{index}": PillarTStatementVerdict.CAS_BLOCKED_REQUIRED_AXIS
            for index in range(5, 9)
        },
        "VT-T11": PillarTStatementVerdict.PROVED_CONDITIONAL_LINEAR_ALGEBRA,
        "VT-T12": PillarTStatementVerdict.PROVED_CONDITIONAL_LINEAR_ALGEBRA,
        "VT-T13": PillarTStatementVerdict.PARTIAL_CHAIN_RULE_CAS_BLOCKED,
        "VT-T14": (
            PillarTStatementVerdict.INCONCLUSIVE_NATIVE_GEOMETRY_GATE
        ),
    }
    for record in out:
        if record.verdict is not expected_verdicts[record.obligation_id]:
            raise PillarTCasError(
                f"{record.obligation_id} verdict violates the blocked boundary"
            )
    return tuple(out)


def _finite_matrix(
    value: object,
    name: str,
    *,
    rows: int | None = None,
) -> np.ndarray:
    if isinstance(value, (str, bytes)):
        raise PillarTCasError(f"{name} must be a real numeric matrix")
    raw = np.asarray(value)
    if raw.dtype.kind in {"b", "c", "O", "S", "U", "V"}:
        raise PillarTCasError(
            f"{name} must be a finite real numeric matrix"
        )
    try:
        matrix = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise PillarTCasError(f"{name} must be a real numeric matrix") from exc
    if matrix.ndim != 2 or matrix.size == 0:
        raise PillarTCasError(f"{name} must be a non-empty matrix")
    if rows is not None and matrix.shape[0] != rows:
        raise PillarTCasError(f"{name} row count must equal {rows}")
    if not np.isfinite(matrix).all():
        raise PillarTCasError(f"{name} must contain finite values")
    return matrix


def _rtol(value: object) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise PillarTCasError("rtol must not be boolean")
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise PillarTCasError("rtol must be a finite positive real") from exc
    if not math.isfinite(out) or out <= 0.0 or out > 1.0e-6:
        raise PillarTCasError("rtol must lie in (0, 1e-6]")
    return out


@dataclass(frozen=True)
class SupportedResponseQuotient:
    nuisance_projector: tuple[tuple[float, ...], ...]
    retained_projector: tuple[tuple[float, ...], ...]
    quotient_response: tuple[tuple[float, ...], ...]
    nuisance_rank: int
    response_rank: int
    claim_ceiling: str = "diagnostic_only"


def supported_response_quotient(
    supported_response: object,
    nuisance_tangent: object,
    *,
    rtol: float = 1.0e-12,
) -> SupportedResponseQuotient:
    """Verify the conditional VT-T11 projector in supported coordinates.

    Covariance support selection is deliberately upstream.  Passing raw
    covariance-null rows here is a caller contract error, not a reason to
    collapse support removal into nuisance projection.
    """

    tolerance = _rtol(rtol)
    response = _finite_matrix(supported_response, "supported_response")
    nuisance = _finite_matrix(
        nuisance_tangent,
        "nuisance_tangent",
        rows=response.shape[0],
    )
    singular = np.linalg.svd(nuisance, compute_uv=False)
    scale = float(singular[0]) if singular.size else 0.0
    rank = int(np.count_nonzero(singular > tolerance * scale))
    if rank != nuisance.shape[1]:
        raise PillarTCasError(
            "nuisance_tangent must have full declared column rank"
        )
    gram = nuisance.T @ nuisance
    projector = nuisance @ np.linalg.solve(gram, nuisance.T)
    retained = np.eye(response.shape[0]) - projector
    quotient = retained @ response
    response_singular = np.linalg.svd(quotient, compute_uv=False)
    response_scale = (
        float(response_singular[0]) if response_singular.size else 0.0
    )
    response_rank = int(
        np.count_nonzero(
            response_singular > tolerance * response_scale
        )
    )
    for name, value in (
        ("nuisance projector symmetry", projector - projector.T),
        ("nuisance projector idempotence", projector @ projector - projector),
        ("retained projector idempotence", retained @ retained - retained),
        ("projector complement", projector @ retained),
    ):
        if not np.allclose(value, 0.0, rtol=0.0, atol=64 * tolerance):
            raise PillarTCasError(f"{name} verification failed")
    return SupportedResponseQuotient(
        nuisance_projector=tuple(
            tuple(float(item) for item in row) for row in projector
        ),
        retained_projector=tuple(
            tuple(float(item) for item in row) for row in retained
        ),
        quotient_response=tuple(
            tuple(float(item) for item in row) for row in quotient
        ),
        nuisance_rank=rank,
        response_rank=response_rank,
    )


@dataclass(frozen=True)
class PrincipalAngleSeparation:
    principal_angles_radians: tuple[float, ...]
    schur_eigenvalues: tuple[float, ...]
    positive_definite: bool
    weak_identification: bool
    claim_ceiling: str = "diagnostic_only"


def principal_angle_separation(
    local_basis: object,
    global_basis: object,
    *,
    rtol: float = 1.0e-12,
    weak_angle_threshold: float = 1.0e-3,
) -> PrincipalAngleSeparation:
    """Verify the conditional VT-T12 Schur/principal-angle identity."""

    tolerance = _rtol(rtol)
    local = _finite_matrix(local_basis, "local_basis")
    global_ = _finite_matrix(
        global_basis, "global_basis", rows=local.shape[0]
    )
    if local.shape[1] == 0 or global_.shape[1] == 0:
        raise PillarTCasError("local/global bases must have nonzero columns")
    identity_local = np.eye(local.shape[1])
    identity_global = np.eye(global_.shape[1])
    if not np.allclose(
        local.T @ local,
        identity_local,
        rtol=0.0,
        atol=64 * tolerance,
    ):
        raise PillarTCasError("local_basis must be orthonormal")
    if not np.allclose(
        global_.T @ global_,
        identity_global,
        rtol=0.0,
        atol=64 * tolerance,
    ):
        raise PillarTCasError("global_basis must be orthonormal")
    cosines = np.linalg.svd(local.T @ global_, compute_uv=False)
    angles = np.arccos(np.clip(cosines, -1.0, 1.0))
    schur = global_.T @ (
        np.eye(global_.shape[0]) - local @ local.T
    ) @ global_
    eigenvalues = np.linalg.eigvalsh(0.5 * (schur + schur.T))
    expected = np.sort(np.sin(angles) ** 2)
    if expected.size < eigenvalues.size:
        expected = np.concatenate(
            (expected, np.ones(eigenvalues.size - expected.size))
        )
    if not np.allclose(
        np.sort(eigenvalues),
        expected,
        rtol=0.0,
        atol=128 * tolerance,
    ):
        raise PillarTCasError("Schur eigenvalues do not match sin^2 angles")
    spectral_tolerance = tolerance * max(
        float(np.max(np.abs(eigenvalues), initial=0.0)),
        1.0,
    )
    positive = bool(np.min(eigenvalues) > spectral_tolerance)
    if isinstance(weak_angle_threshold, bool):
        raise PillarTCasError("weak_angle_threshold must be real")
    threshold = float(weak_angle_threshold)
    if not math.isfinite(threshold) or threshold <= 0.0:
        raise PillarTCasError("weak_angle_threshold must be positive")
    weak = positive and bool(np.min(angles) < threshold)
    return PrincipalAngleSeparation(
        principal_angles_radians=tuple(float(value) for value in angles),
        schur_eigenvalues=tuple(float(value) for value in eigenvalues),
        positive_definite=positive,
        weak_identification=weak,
    )


def shape_chain_rule_core(
    i2: int | Fraction,
    i3: int | Fraction,
    di2: int | Fraction,
    di3: int | Fraction,
) -> Fraction:
    """Return the exact VT-T13 differential of ``6 I3^2 / I2^3``.

    This is only the invariant quotient-rule core.  It does not synthesize a
    shear evolution equation or an E/H/stress/acceleration/vorticity source
    decomposition.
    """

    if any(type(value) is bool for value in (i2, i3, di2, di3)):
        raise PillarTCasError("chain-rule inputs must not be boolean")
    values = tuple(Fraction(value) for value in (i2, i3, di2, di3))
    q2, q3, dq2, dq3 = values
    if q2 == 0:
        raise PillarTCasError("I2=0 is outside the normalized-shape domain")
    return Fraction(
        12 * q2 * q3 * dq3 - 18 * q3 * q3 * dq2,
        q2**4,
    )


@dataclass(frozen=True)
class GeometryGateReport:
    status: GeometryEscalationStatus
    missing_requirements: tuple[str, ...]
    permitted_output: str
    claim_ceiling: str = "diagnostic_only"


def native_geometry_gate(
    *,
    geometry_payload_admitted: bool,
    native_morphology_atlas_admitted: bool,
) -> GeometryGateReport:
    """Return the typed VT-T14 refusal boundary.

    PR-270 has no authority to admit either future input.  Boolean ``True``
    therefore cannot promote a geometry statement here; it records which
    external gates a future adapter would still have to verify.
    """

    if type(geometry_payload_admitted) is not bool or type(
        native_morphology_atlas_admitted
    ) is not bool:
        raise PillarTCasError("geometry/atlas admission flags must be boolean")
    missing = []
    if not geometry_payload_admitted:
        missing.append("admitted Weyl/three-curvature/stress geometry payload")
    if not native_morphology_atlas_admitted:
        missing.append("externally gated native morphology atlas")
    return GeometryGateReport(
        status=GeometryEscalationStatus.INCONCLUSIVE_NATIVE_GEOMETRY_GATE,
        missing_requirements=tuple(missing),
        permitted_output="partial kinematic diagnostic report",
    )


__all__ = [
    "ALLOWED_AGGREGATE_VERDICTS",
    "AggregateCASVerdict",
    "CAS_ADJUDICATION_PATH",
    "CAS_CONTRACT_ID",
    "CAS_CONTRACT_PATH",
    "CAS_REGISTRY_PATH",
    "CASAdjudication",
    "CASContract",
    "EXACT_OBLIGATIONS",
    "GeometryEscalationStatus",
    "GeometryGateReport",
    "PROOF_IDS",
    "PillarTCasError",
    "PillarTCasProofRecord",
    "PillarTStatementVerdict",
    "PrincipalAngleSeparation",
    "REQUIRED_AXES",
    "SupportedResponseQuotient",
    "load_cas_adjudication",
    "load_cas_contract",
    "load_pillar_t_cas_registry",
    "native_geometry_gate",
    "principal_angle_separation",
    "shape_chain_rule_core",
    "supported_response_quotient",
]
