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
DATA_IDENTITY_REGISTRY_SCHEMA = "htt.pr274.data_identity_registry.v1"
DATA_IDENTITY_EVIDENCE_SCHEMA = "htt.pr274.data_identity_evidence.v1"
DATA_ADMISSION_CLAIM_CEILING = "diagnostic_only"
NO_ADMITTED_DATA_PILOT = "NO_ADMITTED_DATA_PILOT"
_REGISTRY_ID = "PR274-CANDIDATE-INPUTS-V1"
_IDENTITY_REGISTRY_ID = "PR274-DATA-IDENTITIES-V1"
_REGISTRY_FROZEN_ON = "2026-07-30"
_REGISTRY_SCOPE = "repository-bound admission preflight"
_EXPECTED_COMPONENT_ROLES = ("data", "mask", "covariance")
_EXPECTED_CANDIDATE_IDS = (
    "PLANCK_PR3_FFP10_SMICA_COMPACT_REFERENCE",
    "CF4_QUERY_BATCH_COMPACT_REFERENCE",
    "DESI_DR1_PR151_PARTIAL_BACKGROUND",
    "PLANCK_NAME_ONLY_CONTROL",
    "HSC_NAME_ONLY_CONTROL",
    "KIDS_NAME_ONLY_CONTROL",
)
_EXPECTED_REQUIRED_FIELDS = {
    "PLANCK_PR3_FFP10_SMICA_COMPACT_REFERENCE": (
        "observed_low_ell_features",
        "matched_null_features",
        "mask_support",
        "covariance",
        "transfer_provenance",
    ),
    "CF4_QUERY_BATCH_COMPACT_REFERENCE": (
        "sky_position",
        "distance_depth",
        "peculiar_velocity",
        "mask_selection",
        "covariance",
        "transfer_provenance",
    ),
    "DESI_DR1_PR151_PARTIAL_BACKGROUND": (
        "complete_1000_ezmock_bank",
        "complete_25_abacus_validation_bank",
        "matched_selection",
        "covariance",
        "transfer_provenance",
    ),
    "PLANCK_NAME_ONLY_CONTROL": (
        "observed_features",
        "mask",
        "covariance",
        "transfer_provenance",
    ),
    "HSC_NAME_ONLY_CONTROL": (
        "spin2_features",
        "mask",
        "response",
        "covariance",
        "transfer_provenance",
    ),
    "KIDS_NAME_ONLY_CONTROL": (
        "spin2_features",
        "mask",
        "response",
        "covariance",
        "transfer_provenance",
    ),
}
_RESOLVABLE_SOURCE_PREFIXES = (
    "arxiv:",
    "dataset:",
    "doi:",
    "docs/",
    "http://",
    "https://",
    "ivo://",
    "repository:",
    "urn:",
)
_RESOLVABLE_LICENSE_PREFIXES = (
    "doi:",
    "docs/",
    "http://",
    "https://",
    "repository:",
    "spdx:",
    "urn:",
)
_DIRECTIONAL_CONVENTIONS = frozenset(
    {
        "GALACTIC_IAU1958_RIGHT_HANDED",
        "HEALPIX_GALACTIC_RING",
        "ICRS_EQUATORIAL_RIGHT_HANDED",
    }
)
_MISSING_TOKENS = frozenset(
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
_IDENTITY_REGISTRY_TOKEN = object()
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
_IDENTITY_REGISTRY_KEYS = frozenset(
    {
        "schema",
        "registry_id",
        "frozen_on",
        "scope",
        "claim_ceiling",
        "entries",
    }
)
_IDENTITY_ENTRY_KEYS = frozenset(
    {
        "candidate_id",
        "product_name",
        "source_identity",
        "release_version",
        "license_identity",
        "evidence_path",
        "evidence_sha256",
    }
)
_IDENTITY_EVIDENCE_KEYS = frozenset(
    {
        "schema",
        "candidate_id",
        "product_name",
        "source_identity",
        "release_version",
        "license_identity",
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
        "sky_support_identity",
        "directional_convention",
        "covariance_identity",
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


def _is_missing(value: str) -> bool:
    return value.strip().upper() in _MISSING_TOKENS


def _has_resolvable_identity(
    value: str,
    prefixes: tuple[str, ...],
) -> bool:
    lowered = value.casefold()
    for prefix in prefixes:
        folded_prefix = prefix.casefold()
        if lowered.startswith(folded_prefix):
            suffix = value[len(prefix) :].strip()
            return bool(suffix) and any(char.isalnum() for char in suffix)
    return False


def _is_specific_release(value: str) -> bool:
    """Require an explicit version-bearing release token.

    Exact authority comes from the typed identity registry below.  This
    lexical guard only rejects placeholders before registry lookup.
    """

    return (
        len(value) >= 3
        and any(char.isalpha() for char in value)
        and any(char.isdigit() for char in value)
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
class RegisteredDataIdentity:
    """One exact source/release/license triple backed by repository bytes."""

    candidate_id: str
    product_name: str
    source_identity: str
    release_version: str
    license_identity: str
    evidence_path: str
    evidence_sha256: str

    def __post_init__(self) -> None:
        for name in (
            "candidate_id",
            "product_name",
            "source_identity",
            "release_version",
            "license_identity",
            "evidence_path",
            "evidence_sha256",
        ):
            _text(getattr(self, name), name)
        if not _prefixed_sha256(self.evidence_sha256):
            raise DataAdmissionError(
                "registered identity evidence requires sha256 identity"
            )

    def as_payload(self) -> dict[str, str]:
        return {
            "candidate_id": self.candidate_id,
            "product_name": self.product_name,
            "source_identity": self.source_identity,
            "release_version": self.release_version,
            "license_identity": self.license_identity,
            "evidence_path": self.evidence_path,
            "evidence_sha256": self.evidence_sha256,
        }


@dataclass(frozen=True)
class DataIdentityRegistry:
    """Factory-built typed authority for data identity admission."""

    entries: tuple[RegisteredDataIdentity, ...]
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _IDENTITY_REGISTRY_TOKEN:
            raise DataAdmissionError("DataIdentityRegistry must be factory-built")
        entries = tuple(self.entries)
        if any(type(value) is not RegisteredDataIdentity for value in entries):
            raise DataAdmissionError(
                "identity registry requires exact RegisteredDataIdentity entries"
            )
        ids = tuple(value.candidate_id for value in entries)
        if len(ids) != len(set(ids)):
            raise DataAdmissionError(
                "registered data identity candidate IDs must be unique"
            )
        object.__setattr__(self, "entries", entries)
        object.__setattr__(
            self,
            "_identity_seal",
            canonical_sha256(self._payload_unchecked()),
        )

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "schema": DATA_IDENTITY_REGISTRY_SCHEMA,
            "registry_id": _IDENTITY_REGISTRY_ID,
            "frozen_on": _REGISTRY_FROZEN_ON,
            "scope": _REGISTRY_SCOPE,
            "claim_ceiling": DATA_ADMISSION_CLAIM_CEILING,
            "entries": [value.as_payload() for value in self.entries],
        }

    @property
    def content_id(self) -> str:
        if canonical_sha256(self._payload_unchecked()) != self._identity_seal:
            raise DataAdmissionError("data identity registry drifted")
        return self._identity_seal

    def as_payload(self) -> dict[str, object]:
        return {**self._payload_unchecked(), "content_id": self.content_id}


def identity_registry_from_mapping(
    payload: Mapping[str, object],
) -> DataIdentityRegistry:
    checked = _exact_mapping(
        payload,
        name="data identity registry",
        expected_keys=_IDENTITY_REGISTRY_KEYS,
    )
    expected_scalars = {
        "schema": DATA_IDENTITY_REGISTRY_SCHEMA,
        "registry_id": _IDENTITY_REGISTRY_ID,
        "frozen_on": _REGISTRY_FROZEN_ON,
        "scope": _REGISTRY_SCOPE,
        "claim_ceiling": DATA_ADMISSION_CLAIM_CEILING,
    }
    for field_name, expected in expected_scalars.items():
        if checked[field_name] != expected:
            raise DataAdmissionError(
                f"data identity registry {field_name} drifted"
            )
    raw_entries = checked["entries"]
    if (
        isinstance(raw_entries, (str, bytes))
        or not isinstance(raw_entries, Sequence)
    ):
        raise DataAdmissionError("data identity registry entries must be a sequence")
    entries: list[RegisteredDataIdentity] = []
    for index, value in enumerate(raw_entries):
        row = _exact_mapping(
            value,
            name=f"data identity registry entry {index}",
            expected_keys=_IDENTITY_ENTRY_KEYS,
        )
        entries.append(
            RegisteredDataIdentity(
                candidate_id=_text(row["candidate_id"], "candidate_id"),
                product_name=_text(row["product_name"], "product_name"),
                source_identity=_text(
                    row["source_identity"],
                    "source_identity",
                ),
                release_version=_text(
                    row["release_version"],
                    "release_version",
                ),
                license_identity=_text(
                    row["license_identity"],
                    "license_identity",
                ),
                evidence_path=_text(row["evidence_path"], "evidence_path"),
                evidence_sha256=_text(
                    row["evidence_sha256"],
                    "evidence_sha256",
                ),
            )
        )
    return DataIdentityRegistry(
        entries=tuple(entries),
        _construction_token=_IDENTITY_REGISTRY_TOKEN,
    )


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
    sky_support_identity: str
    directional_convention: str
    covariance_identity: str
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
            "sky_support_identity",
            "directional_convention",
            "covariance_identity",
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
            "sky_support_identity": self.sky_support_identity,
            "directional_convention": self.directional_convention,
            "covariance_identity": self.covariance_identity,
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
        sky_support_identity=_text(
            checked["sky_support_identity"],
            "sky_support_identity",
        ),
        directional_convention=_text(
            checked["directional_convention"],
            "directional_convention",
        ),
        covariance_identity=_text(
            checked["covariance_identity"],
            "covariance_identity",
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
    if checked["frozen_on"] != _REGISTRY_FROZEN_ON:
        raise DataAdmissionError("candidate registry frozen_on drifted")
    if checked["scope"] != _REGISTRY_SCOPE:
        raise DataAdmissionError("candidate registry scope drifted")
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
    if ids != _EXPECTED_CANDIDATE_IDS:
        raise DataAdmissionError(
            "candidate membership/order drifted from the frozen PR-274 contract"
        )
    for candidate in candidates:
        expected_fields = _EXPECTED_REQUIRED_FIELDS[candidate.candidate_id]
        if candidate.required_fields != expected_fields:
            raise DataAdmissionError(
                f"{candidate.candidate_id} required_fields drifted"
            )
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
    if _is_missing(binding.path):
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


def _identity_registry_blockers(
    candidate: VectorTensorDataCandidate,
    *,
    identity_registry: DataIdentityRegistry | None,
    repository_root: Path,
) -> list[str]:
    if identity_registry is None:
        return ["typed_identity_registry_required"]
    if type(identity_registry) is not DataIdentityRegistry:
        raise TypeError("identity_registry must be exact DataIdentityRegistry")
    identity_registry.content_id
    matching = tuple(
        value
        for value in identity_registry.entries
        if value.candidate_id == candidate.candidate_id
    )
    if len(matching) != 1:
        return ["typed_identity_record_not_registered"]
    record = matching[0]
    blockers: list[str] = []
    comparisons = (
        ("product_name", "identity_product_not_registered"),
        ("source_identity", "source_identity_not_registered"),
        ("release_version", "release_version_not_registered"),
        ("license_identity", "license_identity_not_registered"),
    )
    for field_name, blocker in comparisons:
        if getattr(candidate, field_name) != getattr(record, field_name):
            blockers.append(blocker)

    if "\\" in record.evidence_path:
        blockers.append("identity_evidence_path_not_repository_relative")
        return blockers
    relative = PurePosixPath(record.evidence_path)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not relative.parts
        or relative == PurePosixPath(".")
    ):
        blockers.append("identity_evidence_path_not_repository_relative")
        return blockers
    try:
        root = repository_root.resolve(strict=True)
    except OSError:
        blockers.append("repository_root_missing")
        return blockers
    if not root.is_dir():
        blockers.append("repository_root_not_directory")
        return blockers
    path = root.joinpath(*relative.parts)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            blockers.append("identity_evidence_path_symlink_forbidden")
            return blockers
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        blockers.append("identity_evidence_file_missing")
        return blockers
    if not resolved.is_relative_to(root):
        blockers.append("identity_evidence_path_escapes_repository")
        return blockers
    if not resolved.is_file():
        blockers.append("identity_evidence_path_not_regular_file")
        return blockers
    raw = resolved.read_bytes()
    actual = f"sha256:{hashlib.sha256(raw).hexdigest()}"
    if actual != record.evidence_sha256:
        blockers.append("identity_evidence_sha256_mismatch")
        return blockers
    def reject_duplicate_keys(
        pairs: list[tuple[str, object]],
    ) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise DataAdmissionError(
                    f"duplicate data identity evidence key: {key}"
                )
            result[key] = value
        return result

    def reject_nonfinite_constant(value: str) -> object:
        raise DataAdmissionError(
            f"non-finite data identity evidence constant: {value}"
        )

    try:
        evidence = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonfinite_constant,
        )
        checked = _exact_mapping(
            evidence,
            name="data identity evidence",
            expected_keys=_IDENTITY_EVIDENCE_KEYS,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, DataAdmissionError):
        blockers.append("identity_evidence_schema_invalid")
        return blockers
    expected = {
        "schema": DATA_IDENTITY_EVIDENCE_SCHEMA,
        "candidate_id": record.candidate_id,
        "product_name": record.product_name,
        "source_identity": record.source_identity,
        "release_version": record.release_version,
        "license_identity": record.license_identity,
    }
    if dict(checked) != expected:
        blockers.append("identity_evidence_content_mismatch")
    return blockers


def _local_identity_reference_blockers(
    value: str,
    *,
    label: str,
    repository_root: Path,
) -> list[str]:
    """Resolve repository-local ``docs/`` identities to actual regular files."""

    if not value.casefold().startswith("docs/"):
        return []
    path_text, _, anchor = value.partition("#")
    relative = PurePosixPath(path_text)
    blocker_prefix = f"{label}_identity"
    if (
        "\\" in path_text
        or relative.is_absolute()
        or ".." in relative.parts
        or not relative.parts
    ):
        return [f"{blocker_prefix}_not_resolvable"]
    try:
        root = repository_root.resolve(strict=True)
    except OSError:
        return ["repository_root_missing"]
    path = root.joinpath(*relative.parts)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return [f"{blocker_prefix}_symlink_forbidden"]
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        return [f"{blocker_prefix}_not_resolvable"]
    if not resolved.is_relative_to(root) or not resolved.is_file():
        return [f"{blocker_prefix}_not_resolvable"]
    if "#" in value and not anchor.strip():
        return [f"{blocker_prefix}_not_resolvable"]
    if anchor:
        try:
            source_text = resolved.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return [f"{blocker_prefix}_not_resolvable"]
        if anchor.casefold() not in source_text.casefold():
            return [f"{blocker_prefix}_not_resolvable"]
    return []


def evaluate_data_candidate(
    candidate: VectorTensorDataCandidate,
    *,
    repository_root: Path,
    identity_registry: DataIdentityRegistry | None = None,
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
    if _is_missing(candidate.source_identity):
        blockers.append("source_identity_missing")
    elif (
        candidate.source_identity.casefold()
        == candidate.product_name.casefold()
    ):
        blockers.append("dataset_name_is_not_source_identity")
    elif not _has_resolvable_identity(
        candidate.source_identity,
        _RESOLVABLE_SOURCE_PREFIXES,
    ):
        blockers.append("source_identity_not_resolvable")
    else:
        blockers.extend(
            _local_identity_reference_blockers(
                candidate.source_identity,
                label="source",
                repository_root=repository_root,
            )
        )
    if candidate.release_status != IdentityStatus.BOUND:
        blockers.append("release_version_not_bound")
    if _is_missing(candidate.release_version):
        blockers.append("release_version_missing")
    elif (
        candidate.release_version.casefold()
        == candidate.product_name.casefold()
    ):
        blockers.append("release_version_not_specific")
    elif not _is_specific_release(candidate.release_version):
        blockers.append("release_version_not_specific")
    if candidate.license_status != IdentityStatus.BOUND:
        blockers.append("license_identity_not_bound")
    if _is_missing(candidate.license_identity):
        blockers.append("license_identity_missing")
    elif not _has_resolvable_identity(
        candidate.license_identity,
        _RESOLVABLE_LICENSE_PREFIXES,
    ):
        blockers.append("license_identity_not_resolvable")
    else:
        blockers.extend(
            _local_identity_reference_blockers(
                candidate.license_identity,
                label="license",
                repository_root=repository_root,
            )
        )
    blockers.extend(
        _identity_registry_blockers(
            candidate,
            identity_registry=identity_registry,
            repository_root=repository_root,
        )
    )
    if candidate.sky_support_status != "BOUND":
        blockers.append("sky_support_not_bound")
    if _is_missing(candidate.sky_support_identity):
        blockers.append("sky_support_identity_missing")
    if _is_missing(candidate.directional_convention):
        blockers.append("directional_convention_missing")
    elif candidate.directional_convention not in _DIRECTIONAL_CONVENTIONS:
        blockers.append("directional_convention_unregistered")
    if _is_missing(candidate.covariance_identity):
        blockers.append("covariance_identity_missing")
    if candidate.acquisition_status in {
        "PARTIAL_BACKGROUND_ACQUISITION",
        "NAME_ONLY",
        "INCOMPLETE",
    }:
        blockers.append("partial_or_incomplete_acquisition_forbidden")
    if candidate.background_pr == "PR-151":
        blockers.append("pr151_partial_scientific_use_forbidden")
    if _is_missing(candidate.transfer_provenance):
        blockers.append("transfer_provenance_missing")
    elif candidate.transfer_provenance in {
        "native_solver",
        "native_morphology_atlas",
    }:
        blockers.append("pre_native_transfer_provenance_forbidden")
    elif candidate.transfer_provenance != "none_observer_side":
        blockers.append("registered_non_native_transfer_spec_required")
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
    component_by_role = {
        binding.role: binding for binding in candidate.components
    }
    if (
        not _is_missing(candidate.sky_support_identity)
        and candidate.sky_support_identity
        != component_by_role["mask"].sha256
    ):
        blockers.append("sky_support_identity_not_mask_content_id")
    if (
        not _is_missing(candidate.covariance_identity)
        and candidate.covariance_identity
        != component_by_role["covariance"].sha256
    ):
        blockers.append("covariance_identity_not_component_content_id")

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
    identity_registry_content_id: str
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
        if not _prefixed_sha256(self.identity_registry_content_id):
            raise DataAdmissionError(
                "identity_registry_content_id must be a prefixed sha256 identity"
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
            "identity_registry_content_id": self.identity_registry_content_id,
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
    identity_registry_payload: Mapping[str, object],
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
    identity_registry = identity_registry_from_mapping(
        identity_registry_payload
    )
    registry_content_id = canonical_sha256(registry_payload)
    decisions = tuple(
        evaluate_data_candidate(
            candidate,
            repository_root=repository_root,
            identity_registry=identity_registry,
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
        identity_registry_content_id=identity_registry.content_id,
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
    "DATA_IDENTITY_EVIDENCE_SCHEMA",
    "DATA_IDENTITY_REGISTRY_SCHEMA",
    "DataAdmissionDecision",
    "DataAdmissionError",
    "DataAdmissionReport",
    "DataIdentityRegistry",
    "IdentityStatus",
    "NO_ADMITTED_DATA_PILOT",
    "PilotAuthorizationStatus",
    "RepositoryComponentBinding",
    "RegisteredDataIdentity",
    "VectorTensorDataCandidate",
    "build_data_admission_report",
    "candidate_from_mapping",
    "candidates_from_registry",
    "canonical_sha256",
    "evaluate_data_candidate",
    "identity_registry_from_mapping",
]
