"""Fail-closed repository-bound data admission for the vector/tensor programme.

Admission is a metadata and byte-binding decision.  It never executes an
observed-data analysis and never turns a dataset name into source authority.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from enum import Enum
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence, TypeVar


DATA_ADMISSION_SCHEMA = "htt.pr274.vector_tensor_data_candidates.v1"
DATA_ADMISSION_RESULT_SCHEMA = "htt.pr274.vector_tensor_data_admission.v1"
DATA_ADMISSION_CLAIM_CEILING = "diagnostic_only"
NO_ADMITTED_DATA_PILOT = "NO_ADMITTED_DATA_PILOT"
_REGISTRY_ID = "PR274-CANDIDATE-INPUTS-V1"
_EXPECTED_COMPONENT_ROLES = ("data", "mask", "covariance")
_MISSING = frozenset(
    {
        "MISSING",
        "MISSING_BACKGROUND_STREAM",
        "NONE",
        "",
    }
)
_SHA256_PREFIXED_LENGTH = len("sha256:") + 64
_CANDIDATE_TOKEN = object()
_REPORT_TOKEN = object()
_REGISTRY_KEYS = frozenset(
    {
        "schema",
        "registry_id",
        "frozen_on",
        "scope",
        "observed_data_execution_authorized",
        "claim_ceiling",
        "candidates",
    }
)
_CANDIDATE_KEYS = frozenset(
    {
        "candidate_id",
        "product_name",
        "artifact_mode",
        "source_identity",
        "source_identity_status",
        "release_version",
        "release_status",
        "license_identity",
        "license_status",
        "acquisition_status",
        "background_pr",
        "sky_support_status",
        "transfer_provenance",
        "required_fields",
        "available_fields",
        "components",
    }
)
_COMPONENT_KEYS = frozenset({"path", "sha256", "binding_status"})
_EnumT = TypeVar("_EnumT", bound=Enum)


class DataAdmissionError(ValueError):
    """Raised when a candidate or admission envelope is malformed."""


class IdentityStatus(str, Enum):
    BOUND = "BOUND"
    REPOSITORY_REFERENCE_ONLY = "REPOSITORY_REFERENCE_ONLY"
    NAME_ONLY = "NAME_ONLY"
    MISSING = "MISSING"


class ComponentBindingStatus(str, Enum):
    BOUND = "BOUND"
    REPOSITORY_REFERENCE_ONLY = "REPOSITORY_REFERENCE_ONLY"
    PARTIAL_BACKGROUND = "PARTIAL_BACKGROUND"
    MISSING = "MISSING"


class AdmissionVerdict(str, Enum):
    ADMITTED = "ADMITTED_FOR_SEPARATE_PILOT_AUTHORIZATION"
    REJECTED = "REJECTED"


class PilotAuthorizationStatus(str, Enum):
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    AWAITING_SEPARATE_AUTHORIZATION = (
        "ADMITTED_INPUTS_AWAITING_EXECUTION_AUTHORIZATION"
    )
    AUTHORIZED_NOT_EXECUTED = "ADMITTED_INPUTS_AUTHORIZED_NOT_EXECUTED"


def canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise DataAdmissionError(f"{name} must be non-empty trimmed text")
    return value


def _exact_mapping(
    value: object,
    *,
    name: str,
    expected_keys: frozenset[str],
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise DataAdmissionError(f"{name} must be a mapping")
    keys = set(value)
    if keys != expected_keys:
        raise DataAdmissionError(
            f"{name} fields drifted; "
            f"missing={sorted(expected_keys - keys)}, "
            f"extra={sorted(keys - expected_keys)}"
        )
    return value


def _string_tuple(
    values: object,
    *,
    name: str,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise DataAdmissionError(f"{name} must be a sequence")
    result = tuple(_text(value, name) for value in values)
    if not allow_empty and not result:
        raise DataAdmissionError(f"{name} must not be empty")
    if len(result) != len(set(result)):
        raise DataAdmissionError(f"{name} must not contain duplicates")
    return result


def _prefixed_sha256(value: str) -> bool:
    return (
        len(value) == _SHA256_PREFIXED_LENGTH
        and value.startswith("sha256:")
        and all(char in "0123456789abcdef" for char in value[7:])
    )


def _enum_value(
    enum_type: type[_EnumT],
    value: object,
    *,
    name: str,
) -> _EnumT:
    text = _text(value, name)
    try:
        return enum_type(text)
    except ValueError as exc:
        raise DataAdmissionError(f"{name} has unsupported value {text!r}") from exc


@dataclass(frozen=True)
class RepositoryComponentBinding:
    role: str
    path: str
    sha256: str
    binding_status: ComponentBindingStatus

    def __post_init__(self) -> None:
        _text(self.role, "component role")
        _text(self.path, f"{self.role}.path")
        _text(self.sha256, f"{self.role}.sha256")
        if self.role not in _EXPECTED_COMPONENT_ROLES:
            raise DataAdmissionError(f"unknown component role {self.role!r}")
        if type(self.binding_status) is not ComponentBindingStatus:
            raise DataAdmissionError(
                "binding_status must use ComponentBindingStatus"
            )
        if (
            self.binding_status == ComponentBindingStatus.BOUND
            and not _prefixed_sha256(self.sha256)
        ):
            raise DataAdmissionError(
                f"bound component {self.role} requires sha256 identity"
            )

    def as_payload(self) -> dict[str, str]:
        return {
            "path": self.path,
            "sha256": self.sha256,
            "binding_status": self.binding_status.value,
        }


@dataclass(frozen=True)
class VectorTensorDataCandidate:
    candidate_id: str
    product_name: str
    artifact_mode: str
    source_identity: str
    source_identity_status: IdentityStatus
    release_version: str
    release_status: IdentityStatus
    license_identity: str
    license_status: IdentityStatus
    acquisition_status: str
    background_pr: str
    sky_support_status: str
    transfer_provenance: str
    required_fields: tuple[str, ...]
    available_fields: tuple[str, ...]
    components: tuple[RepositoryComponentBinding, ...]
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _CANDIDATE_TOKEN:
            raise DataAdmissionError(
                "VectorTensorDataCandidate must be factory-built"
            )
        for name in (
            "candidate_id",
            "product_name",
            "artifact_mode",
            "source_identity",
            "release_version",
            "license_identity",
            "acquisition_status",
            "background_pr",
            "sky_support_status",
            "transfer_provenance",
        ):
            _text(getattr(self, name), name)
        for value, name in (
            (self.source_identity_status, "source_identity_status"),
            (self.release_status, "release_status"),
            (self.license_status, "license_status"),
        ):
            if type(value) is not IdentityStatus:
                raise DataAdmissionError(f"{name} must use IdentityStatus")
        required = _string_tuple(
            self.required_fields,
            name="required_fields",
            allow_empty=False,
        )
        available = _string_tuple(
            self.available_fields,
            name="available_fields",
            allow_empty=True,
        )
        components = tuple(self.components)
        if (
            tuple(value.role for value in components)
            != _EXPECTED_COMPONENT_ROLES
        ):
            raise DataAdmissionError(
                "components must contain data, mask, covariance in exact order"
            )
        object.__setattr__(self, "required_fields", required)
        object.__setattr__(self, "available_fields", available)
        object.__setattr__(self, "components", components)
        object.__setattr__(
            self,
            "_identity_seal",
            canonical_sha256(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "product_name": self.product_name,
            "artifact_mode": self.artifact_mode,
            "source_identity": self.source_identity,
            "source_identity_status": self.source_identity_status.value,
            "release_version": self.release_version,
            "release_status": self.release_status.value,
            "license_identity": self.license_identity,
            "license_status": self.license_status.value,
            "acquisition_status": self.acquisition_status,
            "background_pr": self.background_pr,
            "sky_support_status": self.sky_support_status,
            "transfer_provenance": self.transfer_provenance,
            "required_fields": list(self.required_fields),
            "available_fields": list(self.available_fields),
            "components": {
                value.role: value.as_payload() for value in self.components
            },
        }

    def _assert_sealed(self) -> None:
        if canonical_sha256(self._payload_unchecked()) != self._identity_seal:
            raise DataAdmissionError("candidate identity drifted")

    def as_payload(self) -> dict[str, object]:
        self._assert_sealed()
        return {**self._payload_unchecked(), "content_id": self.content_id}


def candidate_from_mapping(
    payload: Mapping[str, object],
) -> VectorTensorDataCandidate:
    checked = _exact_mapping(
        payload,
        name="candidate",
        expected_keys=_CANDIDATE_KEYS,
    )
    component_map = _exact_mapping(
        checked["components"],
        name="components",
        expected_keys=frozenset(_EXPECTED_COMPONENT_ROLES),
    )
    components: list[RepositoryComponentBinding] = []
    for role in _EXPECTED_COMPONENT_ROLES:
        row = _exact_mapping(
            component_map[role],
            name=f"components.{role}",
            expected_keys=_COMPONENT_KEYS,
        )
        components.append(
            RepositoryComponentBinding(
                role=role,
                path=_text(row["path"], f"components.{role}.path"),
                sha256=_text(row["sha256"], f"components.{role}.sha256"),
                binding_status=_enum_value(
                    ComponentBindingStatus,
                    row["binding_status"],
                    name=f"components.{role}.binding_status",
                ),
            )
        )
    return VectorTensorDataCandidate(
        candidate_id=_text(checked["candidate_id"], "candidate_id"),
        product_name=_text(checked["product_name"], "product_name"),
        artifact_mode=_text(checked["artifact_mode"], "artifact_mode"),
        source_identity=_text(checked["source_identity"], "source_identity"),
        source_identity_status=_enum_value(
            IdentityStatus,
            checked["source_identity_status"],
            name="source_identity_status",
        ),
        release_version=_text(checked["release_version"], "release_version"),
        release_status=_enum_value(
            IdentityStatus,
            checked["release_status"],
            name="release_status",
        ),
        license_identity=_text(checked["license_identity"], "license_identity"),
        license_status=_enum_value(
            IdentityStatus,
            checked["license_status"],
            name="license_status",
        ),
        acquisition_status=_text(
            checked["acquisition_status"],
            "acquisition_status",
        ),
        background_pr=_text(checked["background_pr"], "background_pr"),
        sky_support_status=_text(
            checked["sky_support_status"],
            "sky_support_status",
        ),
        transfer_provenance=_text(
            checked["transfer_provenance"],
            "transfer_provenance",
        ),
        required_fields=_string_tuple(
            checked["required_fields"],
            name="required_fields",
            allow_empty=False,
        ),
        available_fields=_string_tuple(
            checked["available_fields"],
            name="available_fields",
            allow_empty=True,
        ),
        components=tuple(components),
        _construction_token=_CANDIDATE_TOKEN,
    )


def candidates_from_registry(
    payload: Mapping[str, object],
) -> tuple[VectorTensorDataCandidate, ...]:
    checked = _exact_mapping(
        payload,
        name="candidate registry",
        expected_keys=_REGISTRY_KEYS,
    )
    if checked["schema"] != DATA_ADMISSION_SCHEMA:
        raise DataAdmissionError("candidate registry schema drifted")
    if checked["registry_id"] != _REGISTRY_ID:
        raise DataAdmissionError("candidate registry ID drifted")
    if checked["observed_data_execution_authorized"] is not False:
        raise DataAdmissionError(
            "candidate registry cannot authorize observed-data execution"
        )
    if checked["claim_ceiling"] != DATA_ADMISSION_CLAIM_CEILING:
        raise DataAdmissionError("candidate registry claim ceiling drifted")
    raw_candidates = checked["candidates"]
    if (
        isinstance(raw_candidates, (str, bytes))
        or not isinstance(raw_candidates, Sequence)
        or not raw_candidates
    ):
        raise DataAdmissionError("candidate registry must contain candidates")
    candidates = tuple(candidate_from_mapping(value) for value in raw_candidates)
    ids = tuple(value.candidate_id for value in candidates)
    if len(ids) != len(set(ids)):
        raise DataAdmissionError("candidate IDs must be unique")
    return candidates


@dataclass(frozen=True)
class DataAdmissionDecision:
    candidate_id: str
    candidate_content_id: str
    verdict: AdmissionVerdict
    blockers: tuple[str, ...]
    verified_component_sha256: tuple[tuple[str, str], ...]
    pilot_authorization_status: PilotAuthorizationStatus
    claim_ceiling: str = DATA_ADMISSION_CLAIM_CEILING

    def __post_init__(self) -> None:
        _text(self.candidate_id, "candidate_id")
        _text(self.candidate_content_id, "candidate_content_id")
        if not _prefixed_sha256(self.candidate_content_id):
            raise DataAdmissionError(
                "candidate_content_id must be a prefixed sha256 identity"
            )
        if type(self.verdict) is not AdmissionVerdict:
            raise DataAdmissionError("verdict must use AdmissionVerdict")
        if type(self.pilot_authorization_status) is not PilotAuthorizationStatus:
            raise DataAdmissionError(
                "pilot_authorization_status must use PilotAuthorizationStatus"
            )
        blockers = tuple(_text(value, "blocker") for value in self.blockers)
        if len(blockers) != len(set(blockers)):
            raise DataAdmissionError("decision blockers must be unique")
        if self.verdict == AdmissionVerdict.ADMITTED and blockers:
            raise DataAdmissionError("admitted decision cannot contain blockers")
        if self.verdict == AdmissionVerdict.REJECTED and not blockers:
            raise DataAdmissionError("rejected decision requires blockers")
        if (
            self.verdict == AdmissionVerdict.REJECTED
            and self.pilot_authorization_status
            != PilotAuthorizationStatus.NOT_ELIGIBLE
        ):
            raise DataAdmissionError(
                "rejected candidate cannot await or receive authorization"
            )
        if (
            self.verdict == AdmissionVerdict.ADMITTED
            and self.pilot_authorization_status
            == PilotAuthorizationStatus.NOT_ELIGIBLE
        ):
            raise DataAdmissionError(
                "admitted candidate must retain an authorization boundary"
            )
        verified = tuple(self.verified_component_sha256)
        roles: list[str] = []
        for row in verified:
            if (
                not isinstance(row, tuple)
                or len(row) != 2
                or row[0] not in _EXPECTED_COMPONENT_ROLES
                or not _prefixed_sha256(row[1])
            ):
                raise DataAdmissionError(
                    "verified components require unique role/sha256 pairs"
                )
            roles.append(row[0])
        if len(roles) != len(set(roles)):
            raise DataAdmissionError("verified component roles must be unique")
        if self.claim_ceiling != DATA_ADMISSION_CLAIM_CEILING:
            raise DataAdmissionError("decision claim ceiling drifted")
        object.__setattr__(self, "blockers", blockers)
        object.__setattr__(self, "verified_component_sha256", verified)

    def as_payload(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_content_id": self.candidate_content_id,
            "verdict": self.verdict.value,
            "blockers": list(self.blockers),
            "verified_component_sha256": {
                role: digest for role, digest in self.verified_component_sha256
            },
            "pilot_authorization_status": self.pilot_authorization_status.value,
            "claim_ceiling": self.claim_ceiling,
        }


def _component_blockers(
    binding: RepositoryComponentBinding,
    *,
    repository_root: Path,
) -> tuple[list[str], tuple[str, str] | None]:
    blockers: list[str] = []
    prefix = binding.role
    if binding.binding_status != ComponentBindingStatus.BOUND:
        blockers.append(f"{prefix}_component_not_bound")
        return blockers, None
    if binding.path in _MISSING:
        blockers.append(f"{prefix}_path_missing")
        return blockers, None
    if not _prefixed_sha256(binding.sha256):
        blockers.append(f"{prefix}_sha256_missing")
        return blockers, None
    if "\\" in binding.path:
        blockers.append(f"{prefix}_path_not_repository_relative")
        return blockers, None
    relative = PurePosixPath(binding.path)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not relative.parts
        or relative == PurePosixPath(".")
    ):
        blockers.append(f"{prefix}_path_not_repository_relative")
        return blockers, None
    try:
        root = repository_root.resolve(strict=True)
    except OSError:
        blockers.append("repository_root_missing")
        return blockers, None
    if not root.is_dir():
        blockers.append("repository_root_not_directory")
        return blockers, None
    path = root.joinpath(*relative.parts)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            blockers.append(f"{prefix}_path_symlink_forbidden")
            return blockers, None
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        blockers.append(f"{prefix}_file_missing")
        return blockers, None
    if not resolved.is_relative_to(root):
        blockers.append(f"{prefix}_path_escapes_repository")
        return blockers, None
    if not resolved.is_file():
        blockers.append(f"{prefix}_path_not_regular_file")
        return blockers, None
    actual = f"sha256:{hashlib.sha256(resolved.read_bytes()).hexdigest()}"
    if actual != binding.sha256:
        blockers.append(f"{prefix}_sha256_mismatch")
        return blockers, (binding.role, actual)
    return blockers, (binding.role, actual)


def evaluate_data_candidate(
    candidate: VectorTensorDataCandidate,
    *,
    repository_root: Path,
    separate_execution_authorization: bool = False,
) -> DataAdmissionDecision:
    if type(candidate) is not VectorTensorDataCandidate:
        raise TypeError("candidate must be exact VectorTensorDataCandidate")
    candidate.as_payload()
    if type(separate_execution_authorization) is not bool:
        raise DataAdmissionError(
            "separate_execution_authorization must be Boolean"
        )

    blockers: list[str] = []
    verified: list[tuple[str, str]] = []
    if candidate.artifact_mode != "observed_candidate":
        blockers.append("observed_candidate_artifact_mode_required")
    if candidate.source_identity_status != IdentityStatus.BOUND:
        blockers.append("source_identity_not_bound")
    if candidate.source_identity_status == IdentityStatus.NAME_ONLY:
        blockers.append("dataset_name_is_not_source_identity")
    if candidate.release_status != IdentityStatus.BOUND:
        blockers.append("release_version_not_bound")
    if candidate.license_status != IdentityStatus.BOUND:
        blockers.append("license_identity_not_bound")
    if candidate.sky_support_status != "BOUND":
        blockers.append("sky_support_not_bound")
    if candidate.acquisition_status in {
        "PARTIAL_BACKGROUND_ACQUISITION",
        "NAME_ONLY",
        "INCOMPLETE",
    }:
        blockers.append("partial_or_incomplete_acquisition_forbidden")
    if candidate.background_pr == "PR-151":
        blockers.append("pr151_partial_scientific_use_forbidden")
    if candidate.transfer_provenance in _MISSING:
        blockers.append("transfer_provenance_missing")
    if candidate.transfer_provenance in {
        "native_solver",
        "native_morphology_atlas",
    }:
        blockers.append("pre_native_transfer_provenance_forbidden")
    missing_fields = tuple(
        field
        for field in candidate.required_fields
        if field not in set(candidate.available_fields)
    )
    blockers.extend(f"required_field_missing:{value}" for value in missing_fields)
    for binding in candidate.components:
        component_blockers, verified_row = _component_blockers(
            binding,
            repository_root=repository_root,
        )
        blockers.extend(component_blockers)
        if verified_row is not None:
            verified.append(verified_row)

    unique_blockers = tuple(dict.fromkeys(blockers))
    if unique_blockers:
        verdict = AdmissionVerdict.REJECTED
        pilot_status = PilotAuthorizationStatus.NOT_ELIGIBLE
    else:
        verdict = AdmissionVerdict.ADMITTED
        pilot_status = (
            PilotAuthorizationStatus.AUTHORIZED_NOT_EXECUTED
            if separate_execution_authorization
            else PilotAuthorizationStatus.AWAITING_SEPARATE_AUTHORIZATION
        )
    return DataAdmissionDecision(
        candidate_id=candidate.candidate_id,
        candidate_content_id=candidate.content_id,
        verdict=verdict,
        blockers=unique_blockers,
        verified_component_sha256=tuple(verified),
        pilot_authorization_status=pilot_status,
    )


@dataclass(frozen=True)
class DataAdmissionReport:
    report_id: str
    registry_content_id: str
    decisions: tuple[DataAdmissionDecision, ...]
    source_evidence: tuple[tuple[str, str], ...]
    pr151_status: str
    pr151_partial_scientific_use: str
    separate_execution_authorization_present: bool
    status: str
    pilot_executed: bool = False
    owner: str = "OBSSTAT"
    contributors: tuple[str, ...] = ("HTT", "COMMON")
    scope: str = "repository-bound admission preflight"
    artifact_mode: str = "data_admission_preflight"
    claim_ceiling: str = DATA_ADMISSION_CLAIM_CEILING
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _REPORT_TOKEN:
            raise DataAdmissionError("DataAdmissionReport must be factory-built")
        _text(self.report_id, "report_id")
        if not _prefixed_sha256(self.registry_content_id):
            raise DataAdmissionError(
                "registry_content_id must be a prefixed sha256 identity"
            )
        if self.owner != "OBSSTAT":
            raise DataAdmissionError("data-admission report owner drifted")
        if self.contributors != ("HTT", "COMMON"):
            raise DataAdmissionError("data-admission contributors drifted")
        if self.scope != "repository-bound admission preflight":
            raise DataAdmissionError("data-admission scope drifted")
        if self.artifact_mode != "data_admission_preflight":
            raise DataAdmissionError("data-admission artifact mode drifted")
        if self.claim_ceiling != DATA_ADMISSION_CLAIM_CEILING:
            raise DataAdmissionError("data-admission claim ceiling drifted")
        if type(self.separate_execution_authorization_present) is not bool:
            raise DataAdmissionError(
                "separate_execution_authorization_present must be Boolean"
            )
        if self.pilot_executed is not False:
            raise DataAdmissionError("admission report cannot execute a pilot")
        if self.pr151_partial_scientific_use != "forbidden":
            raise DataAdmissionError(
                "PR-151 partial scientific use must remain forbidden"
            )
        if self.pr151_status != "background_in_progress":
            raise DataAdmissionError(
                "PR-151 must remain background_in_progress at admission time"
            )
        decisions = tuple(self.decisions)
        if not decisions or any(
            type(value) is not DataAdmissionDecision for value in decisions
        ):
            raise DataAdmissionError(
                "admission report requires exact typed decisions"
            )
        candidate_ids = tuple(value.candidate_id for value in decisions)
        if len(candidate_ids) != len(set(candidate_ids)):
            raise DataAdmissionError("report candidate IDs must be unique")
        admitted = tuple(
            value
            for value in decisions
            if value.verdict == AdmissionVerdict.ADMITTED
        )
        expected_status = (
            NO_ADMITTED_DATA_PILOT
            if not admitted
            else (
                "ADMITTED_INPUTS_AUTHORIZED_NOT_EXECUTED"
                if self.separate_execution_authorization_present
                else "ADMITTED_INPUTS_AWAITING_EXECUTION_AUTHORIZATION"
            )
        )
        if self.status != expected_status:
            raise DataAdmissionError(
                "report status does not match admission decisions"
            )
        expected_pilot_status = (
            PilotAuthorizationStatus.AUTHORIZED_NOT_EXECUTED
            if self.separate_execution_authorization_present
            else PilotAuthorizationStatus.AWAITING_SEPARATE_AUTHORIZATION
        )
        if any(
            value.pilot_authorization_status != expected_pilot_status
            for value in admitted
        ):
            raise DataAdmissionError(
                "admitted decision authorization status drifted"
            )
        evidence = tuple(self.source_evidence)
        if not evidence or evidence != tuple(sorted(evidence)):
            raise DataAdmissionError(
                "source evidence must be non-empty and deterministically sorted"
            )
        evidence_paths: list[str] = []
        for row in evidence:
            if not isinstance(row, tuple) or len(row) != 2:
                raise DataAdmissionError(
                    "source evidence requires path/sha256 pairs"
                )
            path, digest = row
            _text(path, "source evidence path")
            if not _prefixed_sha256(digest):
                raise DataAdmissionError(
                    "source evidence requires prefixed sha256 identities"
                )
            evidence_paths.append(path)
        if len(evidence_paths) != len(set(evidence_paths)):
            raise DataAdmissionError("source evidence paths must be unique")
        object.__setattr__(self, "decisions", decisions)
        object.__setattr__(self, "source_evidence", evidence)
        object.__setattr__(
            self,
            "_identity_seal",
            canonical_sha256(self._payload_unchecked()),
        )

    @property
    def admitted_candidate_ids(self) -> tuple[str, ...]:
        return tuple(
            value.candidate_id
            for value in self.decisions
            if value.verdict == AdmissionVerdict.ADMITTED
        )

    @property
    def content_id(self) -> str:
        if canonical_sha256(self._payload_unchecked()) != self._identity_seal:
            raise DataAdmissionError("admission report identity drifted")
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "schema": DATA_ADMISSION_RESULT_SCHEMA,
            "report_id": self.report_id,
            "registry_content_id": self.registry_content_id,
            "owner": self.owner,
            "contributors": list(self.contributors),
            "scope": self.scope,
            "artifact_mode": self.artifact_mode,
            "claim_ceiling": self.claim_ceiling,
            "source_evidence": {
                path: digest for path, digest in self.source_evidence
            },
            "pr151_status": self.pr151_status,
            "pr151_partial_scientific_use": self.pr151_partial_scientific_use,
            "separate_execution_authorization_present": (
                self.separate_execution_authorization_present
            ),
            "pilot_executed": self.pilot_executed,
            "candidate_count": len(self.decisions),
            "admitted_count": len(self.admitted_candidate_ids),
            "admitted_candidate_ids": list(self.admitted_candidate_ids),
            "decisions": [value.as_payload() for value in self.decisions],
            "status": self.status,
            "allowed_use": [
                "repository-bound input gap analysis",
                "pre-solver data-admission planning",
            ],
            "forbidden_use": [
                "observed-data inference",
                "claim-bearing figure",
                "native solver or morphology-atlas validation",
                "geometry detection",
                "Bianchi family identification or ranking",
            ],
            "caveats": [
                "dataset names are not source identities",
                "referenced local files are not admitted unless present and hash-bound under the evaluated repository root",
                "PR-151 partial/background acquisition is excluded",
                "admission does not authorize or execute a scientific pilot",
            ],
        }

    def as_payload(self) -> dict[str, object]:
        return {**self._payload_unchecked(), "content_id": self.content_id}


def build_data_admission_report(
    *,
    report_id: str,
    registry_payload: Mapping[str, object],
    repository_root: Path,
    source_evidence: Mapping[str, str],
    pr151_status: str,
    pr151_partial_scientific_use: str,
    separate_execution_authorization_present: bool = False,
) -> DataAdmissionReport:
    if type(separate_execution_authorization_present) is not bool:
        raise DataAdmissionError(
            "separate_execution_authorization_present must be Boolean"
        )
    if not isinstance(source_evidence, Mapping) or not source_evidence:
        raise DataAdmissionError("source_evidence must be a non-empty mapping")
    candidates = candidates_from_registry(registry_payload)
    registry_content_id = canonical_sha256(registry_payload)
    decisions = tuple(
        evaluate_data_candidate(
            candidate,
            repository_root=repository_root,
            separate_execution_authorization=(
                separate_execution_authorization_present
            ),
        )
        for candidate in candidates
    )
    admitted = any(
        value.verdict == AdmissionVerdict.ADMITTED for value in decisions
    )
    status = (
        NO_ADMITTED_DATA_PILOT
        if not admitted
        else (
            "ADMITTED_INPUTS_AUTHORIZED_NOT_EXECUTED"
            if separate_execution_authorization_present
            else "ADMITTED_INPUTS_AWAITING_EXECUTION_AUTHORIZATION"
        )
    )
    return DataAdmissionReport(
        report_id=_text(report_id, "report_id"),
        registry_content_id=registry_content_id,
        decisions=decisions,
        source_evidence=tuple(sorted(source_evidence.items())),
        pr151_status=_text(pr151_status, "pr151_status"),
        pr151_partial_scientific_use=_text(
            pr151_partial_scientific_use,
            "pr151_partial_scientific_use",
        ),
        separate_execution_authorization_present=(
            separate_execution_authorization_present
        ),
        status=status,
        _construction_token=_REPORT_TOKEN,
    )


__all__ = [
    "AdmissionVerdict",
    "ComponentBindingStatus",
    "DATA_ADMISSION_CLAIM_CEILING",
    "DATA_ADMISSION_RESULT_SCHEMA",
    "DATA_ADMISSION_SCHEMA",
    "DataAdmissionDecision",
    "DataAdmissionError",
    "DataAdmissionReport",
    "IdentityStatus",
    "NO_ADMITTED_DATA_PILOT",
    "PilotAuthorizationStatus",
    "RepositoryComponentBinding",
    "VectorTensorDataCandidate",
    "build_data_admission_report",
    "candidate_from_mapping",
    "candidates_from_registry",
    "canonical_sha256",
    "evaluate_data_candidate",
]
