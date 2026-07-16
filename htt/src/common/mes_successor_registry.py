"""Fail-closed pointer and consumer scanner for the future MES authority.

PR-122 deliberately does *not* choose MES coefficients or promote an EGS3
seal into scientific authority.  It only establishes the typed pointer that
active consumers must traverse after PR-124 supplies an independently checked
theorem/convention authority.  Until then the current pointer is explicitly
``MISSING`` and ``BLOCKED_PENDING_PR124``.

The EGS3 branch-registry seal is retained as hash-bound process evidence.  Its
``PASS`` result means that its own diagnostic checks executed successfully; it
is not a theorem-authority receipt and cannot make a release claim-ready.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping, Sequence

import yaml


SCHEMA_VERSION = "pr122.mes_successor_registry.v1"
CURRENT_SUCCESSOR_ID = "mes.typed-successor.pr124"
PLANNED_PR124_SOURCE = "htt/src/common/mes_theorem_authority.py"

# These hashes bind the PR-122 registry to the exact legacy reproduction and
# EGS3 diagnostic-witness bytes that were inspected.  Updating either source
# requires an explicit registry update; silently consuming changed bytes is a
# release blocker.
LEGACY_REPRODUCTION_SHA256 = (
    "cc3ba841a4b61ac10a1d7a82e56b96391afcd81d8bd169bd8ca33940c7cf671e"
)
EGS3_BRANCH_WITNESS_SHA256 = (
    "9b0817c99944e796b4c980cad43df724d0abde9381c8f542195d249447bfe816"
)
EGS3_BRANCH_SEAL_SHA256 = (
    "89dc03551342e89b277790fa50707097d314e0bce9c4b04e8260bbcb76930c04"
)
EGS3_BRANCH_SEAL_PATH = "docs/generated/mes_branch_registry_seal.json"
DEFAULT_CONSUMER_INVENTORY_PATH = (
    "docs/research_program/long_horizon_rescue/" "pr122_active_mes_consumers.yaml"
)
DEFAULT_ACTIVE_PYTHON_ROOTS = (
    "htt/htt/htt",
    "htt/bass",
    "htt/mio",
    "htt/obsstat",
    "htt/tsc",
)

_REQUIRED_EGS3_SEAL_KEYS = frozenset(
    {
        "seal",
        "status",
        "theorem_id",
        "claim_boundary",
        "branch_table",
        "eps1_attribution_triple",
        "w2_ceiling_branches",
    }
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_TYPED_REGISTRY_MODULES = frozenset(
    {"common.mes_successor_registry", "htt.common.mes_successor_registry"}
)
_BYPASS_MODULES = frozenset(
    {
        "htt.core.bounds",
        "htt.htt.htt.core.bounds",
        "tsc.admissibility.three_bound_hierarchy",
        "htt.tsc.admissibility.three_bound_hierarchy",
    }
)
_BYPASS_PREFIXES = ("obsstat.egs3_mes", "htt.obsstat.egs3_mes")

# AST-only discovery markers.  Comments and free prose do not make a source an
# active consumer: the scanner requires an exact imported module, identifier,
# class/function definition, attribute, or policy/formula string used by the
# current MES surfaces.
_MES_CONSUMER_IDENTIFIERS = frozenset(
    {
        "A2_max_MES",
        "B_accel",
        "B_accel_lin",
        "B_omega",
        "B_omega_lin",
        "B_sigma",
        "B_sigma_corrected",
        "B_sigma_lin",
        "DopplerBoostCorrection",
        "MESBounds",
        "MES_LINEAR",
        "Sig2_max_MES",
        "TeffMESBounds",
        "W2_max_MES",
        "compute_mes_bounds",
        "compute_mes_bounds_2sigma_upper",
        "compute_planck_central_bounds",
        "delta_B_sigma",
    }
)
_MES_CONSUMER_MODULES = frozenset(
    {
        "bounds",
        "htt.core.bounds",
        "htt.htt.htt.core.bounds",
        "bass.observational.planck_mes_bounds",
        "bass.forward.teff_mes_bounds",
        "htt.bass.observational.planck_mes_bounds",
        "htt.bass.forward.teff_mes_bounds",
        "tsc.admissibility.three_bound_hierarchy",
        "htt.tsc.admissibility.three_bound_hierarchy",
    }
)
_MES_MODULE_IMPORT_IDENTIFIERS = _MES_CONSUMER_IDENTIFIERS | frozenset(
    {
        "A2_max",
        "COEFFS",
        "Sigma2_max",
        "W2_max",
        "compute_three_bound_hierarchy",
    }
)
_MES_EXACT_DATA_LABELS = frozenset({"MES algebraic\nbound"})

# These are identifiers for legacy, non-geodesic registered triples.  They are
# intentionally not exposed as a replacement numerical authority.  The values
# are used only by the static mutation scanner to detect copied stale literals.
_STALE_TRIPLES = {
    "legacy_non_geodesic_omega": (
        Fraction(3, 4),
        Fraction(2, 1),
        Fraction(2, 7),
    ),
    "legacy_non_geodesic_acceleration": (
        Fraction(3, 4),
        Fraction(1, 1),
        Fraction(3, 14),
    ),
}


class MesRegistryError(ValueError):
    """Raised when a registry or consumer declaration is malformed."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class SourceAvailability(_StringEnum):
    MISSING = "MISSING"
    AVAILABLE = "AVAILABLE"


class MesProcessResult(_StringEnum):
    NOT_RUN = "NOT_RUN"
    PASS = "PASS"
    FAIL = "FAIL"


class MesScientificAuthorityStatus(_StringEnum):
    BLOCKED_PENDING_PR124 = "BLOCKED_PENDING_PR124"
    AUTHORIZED_BY_PR124 = "AUTHORIZED_BY_PR124"


class MesConsumerIssueCode(_StringEnum):
    SOURCE_MISSING = "SOURCE_MISSING"
    SOURCE_NOT_REGULAR = "SOURCE_NOT_REGULAR"
    SOURCE_HASH_MISMATCH = "SOURCE_HASH_MISMATCH"
    UNREGISTERED_SUCCESSOR_SOURCE_PRESENT = "UNREGISTERED_SUCCESSOR_SOURCE_PRESENT"
    SUCCESSOR_MISSING = "SUCCESSOR_MISSING"
    SCIENTIFIC_AUTHORITY_BLOCKED = "SCIENTIFIC_AUTHORITY_BLOCKED"
    UNTRUSTED_REGISTRY_OVERRIDE = "UNTRUSTED_REGISTRY_OVERRIDE"
    NO_ACTIVE_CONSUMERS_DECLARED = "NO_ACTIVE_CONSUMERS_DECLARED"
    SUCCESSOR_ID_MISMATCH = "SUCCESSOR_ID_MISMATCH"
    SUCCESSOR_POINTER_MISSING = "SUCCESSOR_POINTER_MISSING"
    SUCCESSOR_BYPASS = "SUCCESSOR_BYPASS"
    STALE_MES_TRIPLE = "STALE_MES_TRIPLE"
    CONSUMER_PARSE_ERROR = "CONSUMER_PARSE_ERROR"
    DIAGNOSTIC_WITNESS_INVALID = "DIAGNOSTIC_WITNESS_INVALID"
    INVENTORY_INVALID = "INVENTORY_INVALID"
    UNDECLARED_ACTIVE_CONSUMER = "UNDECLARED_ACTIVE_CONSUMER"
    DECLARED_CONSUMER_NOT_DISCOVERED = "DECLARED_CONSUMER_NOT_DISCOVERED"
    EXCLUSION_HASH_MISMATCH = "EXCLUSION_HASH_MISMATCH"


def _enum_value(value: object) -> str:
    return value.value if isinstance(value, Enum) else str(value)


def _nonempty(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MesRegistryError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise MesRegistryError(
            f"{field_name} must not contain leading/trailing whitespace"
        )
    return value


def _source_path(value: object, field_name: str) -> str:
    raw = _nonempty(value, field_name)
    if "\\" in raw:
        raise MesRegistryError(f"{field_name} must use POSIX separators")
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise MesRegistryError(f"{field_name} must be a safe repository-relative path")
    if path.as_posix() != raw:
        raise MesRegistryError(f"{field_name} must be canonically normalized")
    return raw


def _sha256(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MesRegistryError(
            f"{field_name} must be a non-empty lowercase SHA-256 digest"
        )
    digest = _nonempty(value, field_name)
    if not _SHA256_RE.fullmatch(digest):
        raise MesRegistryError(f"{field_name} must be a lowercase SHA-256 digest")
    return digest


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class SourceHashBinding:
    """Exact repository-relative source identity."""

    path: str
    availability: SourceAvailability | str
    sha256: str | None

    def __post_init__(self) -> None:
        path = _source_path(self.path, "SourceHashBinding.path")
        try:
            availability = SourceAvailability(_enum_value(self.availability))
        except ValueError as exc:
            raise MesRegistryError(
                f"unknown source availability {self.availability!r}"
            ) from exc
        digest = self.sha256
        if availability is SourceAvailability.AVAILABLE:
            digest = _sha256(digest, "SourceHashBinding.sha256")
        elif digest is not None:
            raise MesRegistryError("a MISSING source must not carry a SHA-256")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "availability", availability)
        object.__setattr__(self, "sha256", digest)

    def as_payload(self) -> dict[str, object]:
        return {
            "path": self.path,
            "availability": self.availability.value,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class MesDiagnosticWitness:
    """Process evidence that is permanently non-authoritative scientifically."""

    witness_id: str
    source: SourceHashBinding
    seal: SourceHashBinding
    process_result: MesProcessResult | str
    allowed_uses: Sequence[str]
    forbidden_uses: Sequence[str]

    def __post_init__(self) -> None:
        witness_id = _nonempty(self.witness_id, "MesDiagnosticWitness.witness_id")
        if not isinstance(self.source, SourceHashBinding):
            raise MesRegistryError("MesDiagnosticWitness.source must be hash-bound")
        if self.source.availability is not SourceAvailability.AVAILABLE:
            raise MesRegistryError("a diagnostic witness source must be AVAILABLE")
        if not isinstance(self.seal, SourceHashBinding):
            raise MesRegistryError("MesDiagnosticWitness.seal must be hash-bound")
        if self.seal.availability is not SourceAvailability.AVAILABLE:
            raise MesRegistryError("a diagnostic witness seal must be AVAILABLE")
        if self.source.path == self.seal.path:
            raise MesRegistryError("diagnostic witness source and seal must differ")
        try:
            process_result = MesProcessResult(_enum_value(self.process_result))
        except ValueError as exc:
            raise MesRegistryError(
                f"unknown process result {self.process_result!r}"
            ) from exc
        allowed = _text_tuple(self.allowed_uses, "allowed_uses")
        forbidden = _text_tuple(self.forbidden_uses, "forbidden_uses")
        object.__setattr__(self, "witness_id", witness_id)
        object.__setattr__(self, "process_result", process_result)
        object.__setattr__(self, "allowed_uses", allowed)
        object.__setattr__(self, "forbidden_uses", forbidden)

    @property
    def scientific_authority(self) -> bool:
        return False

    def as_payload(self) -> dict[str, object]:
        return {
            "witness_id": self.witness_id,
            "source": self.source.as_payload(),
            "seal": self.seal.as_payload(),
            "process_result": self.process_result.value,
            "scientific_authority": False,
            "allowed_uses": list(self.allowed_uses),
            "forbidden_uses": list(self.forbidden_uses),
        }


def _text_tuple(values: Sequence[str], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise MesRegistryError(f"{field_name} must be a sequence")
    result = tuple(_nonempty(value, field_name) for value in values)
    if not result:
        raise MesRegistryError(f"{field_name} must not be empty")
    if len(result) != len(set(result)):
        raise MesRegistryError(f"{field_name} contains duplicates")
    return result


@dataclass(frozen=True)
class MesSuccessorPointer:
    successor_id: str
    source: SourceHashBinding
    process_result: MesProcessResult | str
    scientific_status: MesScientificAuthorityStatus | str
    authority_receipt_id: str | None = None

    def __post_init__(self) -> None:
        successor_id = _nonempty(self.successor_id, "successor_id")
        if not isinstance(self.source, SourceHashBinding):
            raise MesRegistryError("MesSuccessorPointer.source must be hash-bound")
        try:
            process_result = MesProcessResult(_enum_value(self.process_result))
            scientific_status = MesScientificAuthorityStatus(
                _enum_value(self.scientific_status)
            )
        except ValueError as exc:
            raise MesRegistryError("unknown MES successor status") from exc

        receipt = self.authority_receipt_id
        if self.source.availability is SourceAvailability.MISSING:
            if process_result is not MesProcessResult.NOT_RUN:
                raise MesRegistryError("a MISSING successor must have process NOT_RUN")
            if (
                scientific_status
                is not MesScientificAuthorityStatus.BLOCKED_PENDING_PR124
            ):
                raise MesRegistryError("a MISSING successor must remain blocked")
            if receipt is not None:
                raise MesRegistryError("a MISSING successor cannot carry a receipt")
        else:
            # PR-122 has no authenticated PR-124 receipt schema, verifier, or
            # authority registry path.  Therefore AVAILABLE/PASS/status strings
            # are not a capability.  PR-124 must replace this constructor gate
            # with a verifier that derives authorization from exact receipt
            # bytes; accepting a caller-supplied string here would be a direct
            # scientific-authority escalation.
            raise MesRegistryError(
                "an AVAILABLE MES successor is blocked until PR-124 implements "
                "verified authorization"
            )

        object.__setattr__(self, "successor_id", successor_id)
        object.__setattr__(self, "process_result", process_result)
        object.__setattr__(self, "scientific_status", scientific_status)
        object.__setattr__(self, "authority_receipt_id", receipt)

    @property
    def scientific_authority(self) -> bool:
        # Fail closed for the entire v1/PR-122 schema.  Merely changing strings,
        # source availability, or a receipt identifier can never promote it.
        return False

    def as_payload(self) -> dict[str, object]:
        return {
            "successor_id": self.successor_id,
            "source": self.source.as_payload(),
            "process_result": self.process_result.value,
            "scientific_status": self.scientific_status.value,
            "authority_receipt_id": self.authority_receipt_id,
            "scientific_authority": self.scientific_authority,
        }


@dataclass(frozen=True)
class MesSuccessorRegistry:
    schema_version: str
    legacy_reproduction_source: SourceHashBinding
    egs3_branch_witness: MesDiagnosticWitness
    successor: MesSuccessorPointer

    def __post_init__(self) -> None:
        schema = _nonempty(self.schema_version, "schema_version")
        if schema != SCHEMA_VERSION:
            raise MesRegistryError(f"schema_version must be {SCHEMA_VERSION!r}")
        if not isinstance(self.legacy_reproduction_source, SourceHashBinding):
            raise MesRegistryError("legacy_reproduction_source must be hash-bound")
        if (
            self.legacy_reproduction_source.availability
            is not SourceAvailability.AVAILABLE
        ):
            raise MesRegistryError("legacy reproduction source must be AVAILABLE")
        if not isinstance(self.egs3_branch_witness, MesDiagnosticWitness):
            raise MesRegistryError("egs3_branch_witness has the wrong type")
        if not isinstance(self.successor, MesSuccessorPointer):
            raise MesRegistryError("successor has the wrong type")
        paths = {
            self.legacy_reproduction_source.path,
            self.egs3_branch_witness.source.path,
            self.egs3_branch_witness.seal.path,
            self.successor.source.path,
        }
        if len(paths) != 4:
            raise MesRegistryError(
                "legacy, witness source, witness seal, and successor paths must differ"
            )
        object.__setattr__(self, "schema_version", schema)

    def as_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "owner": "COMMON",
            "claim_tier": "diagnostic_only",
            "legacy_reproduction_source": self.legacy_reproduction_source.as_payload(),
            "egs3_branch_witness": self.egs3_branch_witness.as_payload(),
            "typed_successor": self.successor.as_payload(),
            "release_claim_allowed": self.successor.scientific_authority,
            "caveat": (
                "EGS3 process PASS is diagnostic evidence only; the typed MES "
                "scientific authority is blocked pending PR-124."
            ),
        }


@dataclass(frozen=True)
class MesConsumerDeclaration:
    consumer_id: str
    source: SourceHashBinding
    expected_successor_id: str = CURRENT_SUCCESSOR_ID

    def __post_init__(self) -> None:
        consumer_id = _nonempty(self.consumer_id, "consumer_id")
        expected = _nonempty(self.expected_successor_id, "expected_successor_id")
        if not isinstance(self.source, SourceHashBinding):
            raise MesRegistryError("consumer source must be hash-bound")
        if self.source.availability is not SourceAvailability.AVAILABLE:
            raise MesRegistryError("an active consumer source must be AVAILABLE")
        object.__setattr__(self, "consumer_id", consumer_id)
        object.__setattr__(self, "expected_successor_id", expected)


@dataclass(frozen=True)
class MesConsumerExclusion:
    """Exact, reviewable exclusion from the active-consumer inventory."""

    exclusion_id: str
    source: SourceHashBinding
    reason: str

    def __post_init__(self) -> None:
        exclusion_id = _nonempty(self.exclusion_id, "exclusion_id")
        reason = _nonempty(self.reason, "exclusion reason")
        if not isinstance(self.source, SourceHashBinding):
            raise MesRegistryError("exclusion source must be hash-bound")
        if self.source.availability is not SourceAvailability.AVAILABLE:
            raise MesRegistryError("an exclusion source must be AVAILABLE")
        if not self.source.path.endswith(".py"):
            raise MesRegistryError("MES consumer exclusions must name one Python file")
        object.__setattr__(self, "exclusion_id", exclusion_id)
        object.__setattr__(self, "reason", reason)


@dataclass(frozen=True)
class MesConsumerFinding:
    code: MesConsumerIssueCode
    subject: str
    detail: str

    def as_payload(self) -> dict[str, str]:
        return {
            "code": self.code.value,
            "subject": self.subject,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class MesConsumerScanReport:
    registry: MesSuccessorRegistry
    consumers_scanned: int
    findings: tuple[MesConsumerFinding, ...]

    @property
    def release_allowed(self) -> bool:
        return self.registry.successor.scientific_authority and not self.findings

    def as_payload(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "registry": self.registry.as_payload(),
            "consumers_scanned": self.consumers_scanned,
            "findings": [finding.as_payload() for finding in self.findings],
            "release_allowed": self.release_allowed,
        }

    def assert_release_allowed(self) -> None:
        if not self.release_allowed:
            codes = ", ".join(finding.code.value for finding in self.findings)
            raise MesRegistryError(f"MES release blocked: {codes or 'no authority'}")


def current_mes_successor_registry() -> MesSuccessorRegistry:
    """Return the current PR-122 pointer without importing a physics module."""

    return MesSuccessorRegistry(
        schema_version=SCHEMA_VERSION,
        legacy_reproduction_source=SourceHashBinding(
            path="htt/tsc/admissibility/three_bound_hierarchy.py",
            availability=SourceAvailability.AVAILABLE,
            sha256=LEGACY_REPRODUCTION_SHA256,
        ),
        egs3_branch_witness=MesDiagnosticWitness(
            witness_id="egs3.mes_branch_registry",
            source=SourceHashBinding(
                path="htt/obsstat/egs3_mes_branch_registry.py",
                availability=SourceAvailability.AVAILABLE,
                sha256=EGS3_BRANCH_WITNESS_SHA256,
            ),
            seal=SourceHashBinding(
                path=EGS3_BRANCH_SEAL_PATH,
                availability=SourceAvailability.AVAILABLE,
                sha256=EGS3_BRANCH_SEAL_SHA256,
            ),
            process_result=MesProcessResult.PASS,
            allowed_uses=(
                "legacy reproduction",
                "diagnostic process witness",
            ),
            forbidden_uses=(
                "typed MES scientific authority",
                "active release coefficient source",
                "observational or geometry claim",
            ),
        ),
        successor=MesSuccessorPointer(
            successor_id=CURRENT_SUCCESSOR_ID,
            source=SourceHashBinding(
                path=PLANNED_PR124_SOURCE,
                availability=SourceAvailability.MISSING,
                sha256=None,
            ),
            process_result=MesProcessResult.NOT_RUN,
            scientific_status=(MesScientificAuthorityStatus.BLOCKED_PENDING_PR124),
            authority_receipt_id=None,
        ),
    )


def _bound_path(repo_root: Path, binding: SourceHashBinding) -> Path:
    root = repo_root.resolve()
    candidate = root.joinpath(*PurePosixPath(binding.path).parts)
    try:
        candidate.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise MesRegistryError(
            f"source escapes repository root: {binding.path}"
        ) from exc
    return candidate


def _verify_binding(
    repo_root: Path,
    binding: SourceHashBinding,
    *,
    subject: str,
    missing_is_expected: bool = False,
) -> tuple[MesConsumerFinding, ...]:
    path = _bound_path(repo_root, binding)
    if binding.availability is SourceAvailability.MISSING:
        if path.exists() and missing_is_expected:
            return (
                MesConsumerFinding(
                    MesConsumerIssueCode.UNREGISTERED_SUCCESSOR_SOURCE_PRESENT,
                    subject,
                    f"{binding.path} exists but the typed pointer is still MISSING",
                ),
            )
        return ()
    if not path.exists():
        return (
            MesConsumerFinding(
                MesConsumerIssueCode.SOURCE_MISSING,
                subject,
                binding.path,
            ),
        )
    if path.is_symlink() or not path.is_file():
        return (
            MesConsumerFinding(
                MesConsumerIssueCode.SOURCE_NOT_REGULAR,
                subject,
                binding.path,
            ),
        )
    actual = sha256_file(path)
    if actual != binding.sha256:
        return (
            MesConsumerFinding(
                MesConsumerIssueCode.SOURCE_HASH_MISMATCH,
                subject,
                f"expected {binding.sha256}, got {actual}",
            ),
        )
    return ()


def _witness_invalid(subject: str, detail: str) -> MesConsumerFinding:
    return MesConsumerFinding(
        MesConsumerIssueCode.DIAGNOSTIC_WITNESS_INVALID,
        subject,
        detail,
    )


def _verify_diagnostic_witness_payload(
    repo_root: Path,
    witness: MesDiagnosticWitness,
) -> tuple[MesConsumerFinding, ...]:
    """Validate the exact EGS3 seal schema independently of producer source."""

    path = _bound_path(repo_root, witness.seal)
    if path.is_symlink() or not path.is_file():
        return ()  # The separate source-binding finding is authoritative here.
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return (_witness_invalid(witness.witness_id, f"invalid seal JSON: {exc}"),)
    if not isinstance(payload, Mapping):
        return (_witness_invalid(witness.witness_id, "seal root must be an object"),)
    missing = sorted(_REQUIRED_EGS3_SEAL_KEYS - set(payload))
    if missing:
        return (
            _witness_invalid(
                witness.witness_id,
                "seal missing required keys: " + ", ".join(missing),
            ),
        )

    issues: list[MesConsumerFinding] = []

    def require(condition: bool, detail: str) -> None:
        if not condition:
            issues.append(_witness_invalid(witness.witness_id, detail))

    require(payload.get("seal") == witness.witness_id, "seal id mismatch")
    require(payload.get("status") == "PASS", "seal status must be PASS")
    require(
        witness.process_result is MesProcessResult.PASS,
        "typed witness process status must be PASS",
    )
    require(payload.get("theorem_id") == "MES-BR", "unexpected theorem_id")
    claim_boundary = payload.get("claim_boundary")
    require(
        isinstance(claim_boundary, str)
        and "diagnostic_only" in claim_boundary
        and "no branch enables any observational claim" in claim_boundary,
        "claim boundary must preserve diagnostic-only/no-observational-use scope",
    )

    branch_table = payload.get("branch_table")
    require(isinstance(branch_table, Mapping), "branch_table must be an object")
    if isinstance(branch_table, Mapping):
        require(
            branch_table.get("registered_values_unchanged") is True,
            "registered_values_unchanged must be true",
        )
        expected_statuses = {
            "MES_G": "VERIFIED_GEODESIC",
            "MES_NG": "UNVERIFIED_NON_GEODESIC",
            "ACCEL_WITHHELD": "WITHHELD",
        }
        for branch, expected in expected_statuses.items():
            row = branch_table.get(branch)
            require(
                isinstance(row, Mapping) and row.get("status") == expected,
                f"{branch}.status must be {expected}",
            )

    w2 = payload.get("w2_ceiling_branches")
    require(isinstance(w2, Mapping), "w2_ceiling_branches must be an object")
    if isinstance(w2, Mapping):
        require(
            w2.get("no_branch_promoted") is True,
            "w2_ceiling_branches.no_branch_promoted must be true",
        )
    require(
        isinstance(payload.get("eps1_attribution_triple"), Mapping),
        "eps1_attribution_triple must be an object",
    )
    return tuple(issues)


def validate_mes_successor_registry(
    repo_root: Path,
    registry: MesSuccessorRegistry | None = None,
) -> MesConsumerScanReport:
    """Verify exact bound bytes and report the current release blockers."""

    selected = registry or current_mes_successor_registry()
    if not isinstance(selected, MesSuccessorRegistry):
        raise MesRegistryError("registry must be a MesSuccessorRegistry")
    findings: list[MesConsumerFinding] = []
    if registry is not None:
        findings.append(
            MesConsumerFinding(
                MesConsumerIssueCode.UNTRUSTED_REGISTRY_OVERRIDE,
                "mes_successor_registry",
                (
                    "PR-122 accepts only its compiled current registry as a "
                    "release trust root; PR-124 must replace that factory after "
                    "authenticated authority delivery"
                ),
            )
        )
    findings.extend(
        _verify_binding(
            repo_root,
            selected.legacy_reproduction_source,
            subject="legacy_reproduction_source",
        )
    )
    findings.extend(
        _verify_binding(
            repo_root,
            selected.egs3_branch_witness.source,
            subject=selected.egs3_branch_witness.witness_id,
        )
    )
    seal_findings = _verify_binding(
        repo_root,
        selected.egs3_branch_witness.seal,
        subject=f"{selected.egs3_branch_witness.witness_id}.seal",
    )
    findings.extend(seal_findings)
    if not seal_findings:
        findings.extend(
            _verify_diagnostic_witness_payload(
                repo_root,
                selected.egs3_branch_witness,
            )
        )
    findings.extend(
        _verify_binding(
            repo_root,
            selected.successor.source,
            subject=selected.successor.successor_id,
            missing_is_expected=True,
        )
    )
    if selected.successor.source.availability is SourceAvailability.MISSING:
        findings.append(
            MesConsumerFinding(
                MesConsumerIssueCode.SUCCESSOR_MISSING,
                selected.successor.successor_id,
                "typed MES theorem/convention authority has not been delivered",
            )
        )
    if not selected.successor.scientific_authority:
        findings.append(
            MesConsumerFinding(
                MesConsumerIssueCode.SCIENTIFIC_AUTHORITY_BLOCKED,
                selected.successor.successor_id,
                selected.successor.scientific_status.value,
            )
        )
    return MesConsumerScanReport(selected, 0, tuple(findings))


def _imported_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _constant_string(
    node: ast.AST,
    constants: Mapping[str, str] | None = None,
) -> str | None:
    """Fold static module-name strings without executing consumer code."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and constants is not None:
        return constants.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _constant_string(node.left, constants)
        right = _constant_string(node.right, constants)
        return None if left is None or right is None else left + right
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
                continue
            if (
                not isinstance(value, ast.FormattedValue)
                or value.format_spec is not None
            ):
                return None
            folded = _constant_string(value.value, constants)
            if folded is None:
                return None
            parts.append(folded)
        return "".join(parts)
    return None


def _module_string_constants(tree: ast.AST) -> dict[str, str]:
    """Collect unambiguously assigned top-level static strings."""

    if not isinstance(tree, ast.Module):
        return {}
    constants: dict[str, str] = {}
    seen: set[str] = set()
    for statement in tree.body:
        target: ast.AST | None = None
        value: ast.AST | None = None
        if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
            target = statement.targets[0]
            value = statement.value
        elif isinstance(statement, ast.AnnAssign):
            target = statement.target
            value = statement.value
        if not isinstance(target, ast.Name) or value is None:
            continue
        if target.id in seen:
            constants.pop(target.id, None)
            continue
        seen.add(target.id)
        folded = _constant_string(value, constants)
        if folded is not None:
            constants[target.id] = folded
    return constants


def _dynamic_bypass_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    constants = _module_string_constants(tree)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        function_name = None
        if isinstance(node.func, ast.Name):
            function_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            function_name = node.func.attr
        if function_name not in {"__import__", "import_module"}:
            continue
        module = _constant_string(node.args[0], constants)
        if module is None:
            modules.add("<unresolved-dynamic-import>")
        elif _is_bypass_module(module):
            modules.add(module)
    return modules


def _dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return None if prefix is None else f"{prefix}.{node.attr}"
    return None


def _assignment_names(target: ast.AST) -> tuple[str, ...]:
    if isinstance(target, ast.Name):
        return (target.id,)
    if isinstance(target, (ast.Tuple, ast.List)):
        return tuple(
            name for element in target.elts for name in _assignment_names(element)
        )
    return ()


def _uses_typed_successor_entrypoint(tree: ast.AST) -> bool:
    """Require live module-level binding plus observable pointer dataflow."""

    if not isinstance(tree, ast.Module):
        return False

    call_targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module in _TYPED_REGISTRY_MODULES:
            for alias in node.names:
                if alias.name == "current_mes_successor_registry":
                    call_targets.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in _TYPED_REGISTRY_MODULES:
                    continue
                bound_name = alias.asname or alias.name
                call_targets.add(f"{bound_name}.current_mes_successor_registry")

    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    statically_dead: set[ast.AST] = set()
    for node in ast.walk(tree):
        dead_nodes: Iterable[ast.AST] = ()
        if isinstance(node, (ast.If, ast.While)):
            test = node.test
            if isinstance(test, ast.Constant) and isinstance(test.value, bool):
                dead_nodes = node.orelse if test.value else node.body
        elif isinstance(node, ast.IfExp):
            test = node.test
            if isinstance(test, ast.Constant) and isinstance(test.value, bool):
                dead_nodes = (node.orelse if test.value else node.body,)
        elif isinstance(node, ast.BoolOp):
            for index, value in enumerate(node.values[:-1]):
                if not isinstance(value, ast.Constant) or not isinstance(
                    value.value, bool
                ):
                    continue
                short_circuits = (isinstance(node.op, ast.And) and not value.value) or (
                    isinstance(node.op, ast.Or) and value.value
                )
                if short_circuits:
                    dead_nodes = node.values[index + 1 :]
                    break
        for dead_node in dead_nodes:
            statically_dead.add(dead_node)
            statically_dead.update(ast.walk(dead_node))

    bound_names: set[str] = set()
    module_statements = set(tree.body)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or node in statically_dead:
            continue
        parent = parents.get(node)
        consumer = parents.get(parent) if parent is not None else None
        if _dotted_name(node.func) not in call_targets:
            continue
        if not isinstance(parent, ast.Attribute) or parent.attr != "successor":
            continue
        if not isinstance(consumer, (ast.Assign, ast.AnnAssign)):
            continue
        if consumer not in module_statements or consumer.value is not parent:
            continue
        targets = (
            consumer.targets if isinstance(consumer, ast.Assign) else (consumer.target,)
        )
        bound_names.update(
            name for target in targets for name in _assignment_names(target)
        )

    if not bound_names:
        return False
    store_counts = {
        name: sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Store)
            and node.id == name
        )
        for name in bound_names
    }
    stable_names = {name for name, count in store_counts.items() if count == 1}
    if not stable_names:
        return False

    for statement in tree.body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign, ast.Assert)):
            continue
        for node in ast.walk(statement):
            if node in statically_dead or not isinstance(node, ast.Attribute):
                continue
            if (
                isinstance(node.value, ast.Name)
                and isinstance(node.value.ctx, ast.Load)
                and node.value.id in stable_names
            ):
                return True
    return False


def _literal_fraction(node: ast.AST) -> Fraction | None:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return None
        if isinstance(node.value, int):
            return Fraction(node.value)
        if isinstance(node.value, float):
            try:
                return Fraction(str(node.value))
            except (ValueError, ZeroDivisionError):
                return None
        if isinstance(node.value, str):
            try:
                return Fraction(node.value)
            except (ValueError, ZeroDivisionError):
                return None
        return None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _literal_fraction(node.operand)
        if value is None:
            return None
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _literal_fraction(node.left)
        right = _literal_fraction(node.right)
        if left is None or right in {None, Fraction(0)}:
            return None
        return left / right
    if isinstance(node, ast.Call):
        function_name = None
        if isinstance(node.func, ast.Name):
            function_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            function_name = node.func.attr
        if (
            function_name == "Fraction"
            and not node.keywords
            and len(node.args) in {1, 2}
        ):
            values = tuple(_literal_fraction(argument) for argument in node.args)
            if any(value is None for value in values):
                return None
            try:
                return Fraction(*values)  # type: ignore[arg-type]
            except (TypeError, ValueError, ZeroDivisionError):
                return None
    return None


_EPSILON_NAME_RE = re.compile(r"(?:e|eps|epsilon)_?([123])(?:_.*)?\Z", re.I)


def _epsilon_slot(node: ast.AST) -> int | None:
    name = None
    if isinstance(node, ast.Name):
        name = node.id
    elif isinstance(node, ast.Attribute):
        name = node.attr
    if name is None:
        return None
    match = _EPSILON_NAME_RE.fullmatch(name)
    return None if match is None else int(match.group(1)) - 1


def _affine_epsilon_terms(
    node: ast.AST,
    sign: Fraction = Fraction(1),
) -> list[tuple[int, Fraction]] | None:
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
        left = _affine_epsilon_terms(node.left, sign)
        right_sign = sign if isinstance(node.op, ast.Add) else -sign
        right = _affine_epsilon_terms(node.right, right_sign)
        return None if left is None or right is None else left + right
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        nested_sign = sign if isinstance(node.op, ast.UAdd) else -sign
        return _affine_epsilon_terms(node.operand, nested_sign)
    slot = _epsilon_slot(node)
    if slot is not None:
        return [(slot, sign)]
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Mult):
        return None
    left_coefficient = _literal_fraction(node.left)
    right_slot = _epsilon_slot(node.right)
    if left_coefficient is not None and right_slot is not None:
        return [(right_slot, sign * left_coefficient)]
    right_coefficient = _literal_fraction(node.right)
    left_slot = _epsilon_slot(node.left)
    if right_coefficient is not None and left_slot is not None:
        return [(left_slot, sign * right_coefficient)]
    return None


def _affine_epsilon_triple(node: ast.AST) -> tuple[Fraction, ...] | None:
    terms = _affine_epsilon_terms(node)
    if terms is None or {slot for slot, _ in terms} != {0, 1, 2}:
        return None
    coefficients = [Fraction(0), Fraction(0), Fraction(0)]
    for slot, coefficient in terms:
        coefficients[slot] += coefficient
    return tuple(coefficients)


def _stale_triples(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        candidates: list[tuple[Fraction, ...]] = []
        if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) == 3:
            literal = tuple(_literal_fraction(element) for element in node.elts)
            if all(value is not None for value in literal):
                candidates.append(
                    tuple(value for value in literal if value is not None)
                )
        affine = _affine_epsilon_triple(node)
        if affine is not None:
            candidates.append(affine)
        for candidate in candidates:
            for name, stale in _STALE_TRIPLES.items():
                if candidate == stale:
                    found.add(name)
    return found


def _is_bypass_module(module: str) -> bool:
    return module in _BYPASS_MODULES or module.startswith(_BYPASS_PREFIXES)


def _tree_uses_mes_surface(tree: ast.AST) -> bool:
    """Return true only for exact executable/imported MES surface markers."""

    constants = _module_string_constants(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name in _MES_CONSUMER_MODULES for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom):
            if node.module in _MES_CONSUMER_MODULES:
                if any(alias.name == "*" for alias in node.names):
                    return True
                if any(
                    alias.name in _MES_MODULE_IMPORT_IDENTIFIERS for alias in node.names
                ):
                    return True
            if any(alias.name in _MES_CONSUMER_IDENTIFIERS for alias in node.names):
                return True
        if isinstance(node, ast.Call) and node.args:
            function_name = None
            if isinstance(node.func, ast.Name):
                function_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                function_name = node.func.attr
            if (
                function_name in {"__import__", "import_module"}
                and _constant_string(node.args[0], constants) in _MES_CONSUMER_MODULES
            ):
                return True
        if isinstance(node, ast.Name) and node.id in _MES_CONSUMER_IDENTIFIERS:
            return True
        if isinstance(node, ast.Attribute) and node.attr in _MES_CONSUMER_IDENTIFIERS:
            return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in _MES_CONSUMER_IDENTIFIERS:
                return True
        value: ast.AST | None = None
        if isinstance(node, ast.Assign):
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            value = node.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            assigned = value.value
            if "Sig2_max_MES(" in assigned or assigned in {
                "MES_LINEAR",
                "mes_linear",
            }:
                return True
        if isinstance(node, ast.Constant) and node.value in _MES_EXACT_DATA_LABELS:
            return True
        if (
            isinstance(node, ast.keyword)
            and node.arg in {"x_max_formula", "denominator_label", "policy"}
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and (
                "Sig2_max_MES(" in node.value.value
                or node.value.value in {"MES_LINEAR", "MES_linear", "mes_linear"}
            )
        ):
            return True
    return False


def _discover_active_mes_consumers(
    repo_root: Path,
    roots: Sequence[str],
) -> tuple[frozenset[str], tuple[MesConsumerFinding, ...], bool]:
    discovered: set[str] = set()
    findings: list[MesConsumerFinding] = []
    root = repo_root.resolve()
    any_root = False
    for raw in roots:
        relative = _source_path(raw, "active Python root")
        directory = root.joinpath(*PurePosixPath(relative).parts)
        try:
            directory.resolve(strict=False).relative_to(root)
        except ValueError as exc:
            raise MesRegistryError(
                f"active Python root escapes repository: {relative}"
            ) from exc
        if not directory.exists():
            findings.append(
                MesConsumerFinding(
                    MesConsumerIssueCode.INVENTORY_INVALID,
                    relative,
                    "active Python root is missing",
                )
            )
            continue
        if directory.is_symlink() or not directory.is_dir():
            findings.append(
                MesConsumerFinding(
                    MesConsumerIssueCode.INVENTORY_INVALID,
                    relative,
                    "active Python root is not a regular directory",
                )
            )
            continue
        any_root = True
        for path in sorted(directory.rglob("*.py")):
            if path.is_symlink() or not path.is_file():
                continue
            if (
                path.name == "conftest.py"
                or path.name.startswith("test_")
                or path.name.endswith("_test.py")
            ):
                continue
            relative_path = path.relative_to(root).as_posix()
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except (OSError, UnicodeDecodeError, SyntaxError) as exc:
                findings.append(
                    MesConsumerFinding(
                        MesConsumerIssueCode.CONSUMER_PARSE_ERROR,
                        relative_path,
                        str(exc),
                    )
                )
                continue
            if _tree_uses_mes_surface(tree):
                discovered.add(relative_path)
    return frozenset(discovered), tuple(findings), any_root


def _load_inventory_controls(
    repo_root: Path,
) -> tuple[
    tuple[str, ...],
    tuple[MesConsumerDeclaration, ...],
    tuple[MesConsumerExclusion, ...],
    bool,
]:
    path = repo_root / DEFAULT_CONSUMER_INVENTORY_PATH
    if path.is_symlink():
        raise MesRegistryError(
            "MES consumer inventory must be a regular repository file"
        )
    if not path.exists():
        return DEFAULT_ACTIVE_PYTHON_ROOTS, (), (), False
    if not path.is_file():
        raise MesRegistryError(
            "MES consumer inventory must be a regular repository file"
        )
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise MesRegistryError(f"invalid MES consumer inventory: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise MesRegistryError("MES consumer inventory root must be a mapping")
    if payload.get("schema") != "htt.long_horizon.pr122_active_mes_consumers.v1":
        raise MesRegistryError("unsupported MES consumer inventory schema")
    if payload.get("successor_id") != CURRENT_SUCCESSOR_ID:
        raise MesRegistryError("MES consumer inventory successor_id is invalid")
    raw_roots = payload.get("active_python_roots")
    if (
        not isinstance(raw_roots, Sequence)
        or isinstance(raw_roots, (str, bytes))
        or not raw_roots
    ):
        raise MesRegistryError("active_python_roots must be non-empty")
    roots = tuple(_source_path(row, "active_python_roots") for row in raw_roots)
    if len(roots) != len(set(roots)):
        raise MesRegistryError("active_python_roots contains duplicates")

    raw_declarations = payload.get("active_consumers")
    if (
        not isinstance(raw_declarations, Sequence)
        or isinstance(raw_declarations, (str, bytes))
        or not raw_declarations
    ):
        raise MesRegistryError("active_consumers must be non-empty")
    declarations: list[MesConsumerDeclaration] = []
    for row in raw_declarations:
        if not isinstance(row, Mapping) or set(row) != {
            "consumer_id",
            "path",
            "sha256",
        }:
            raise MesRegistryError(
                "each active consumer requires consumer_id/path/sha256"
            )
        declarations.append(
            MesConsumerDeclaration(
                consumer_id=row["consumer_id"],
                source=SourceHashBinding(
                    path=row["path"],
                    availability=SourceAvailability.AVAILABLE,
                    sha256=row["sha256"],
                ),
            )
        )

    raw_exclusions = payload.get("excluded_consumers")
    if not isinstance(raw_exclusions, Sequence) or isinstance(
        raw_exclusions, (str, bytes)
    ):
        raise MesRegistryError("excluded_consumers must be a sequence")
    exclusions: list[MesConsumerExclusion] = []
    for row in raw_exclusions:
        if not isinstance(row, Mapping) or set(row) != {
            "exclusion_id",
            "path",
            "sha256",
            "reason",
        }:
            raise MesRegistryError(
                "each excluded consumer requires exclusion_id/path/sha256/reason"
            )
        exclusions.append(
            MesConsumerExclusion(
                exclusion_id=row["exclusion_id"],
                source=SourceHashBinding(
                    path=row["path"],
                    availability=SourceAvailability.AVAILABLE,
                    sha256=row["sha256"],
                ),
                reason=row["reason"],
            )
        )
    return roots, tuple(declarations), tuple(exclusions), True


def scan_declared_mes_consumers(
    repo_root: Path,
    declarations: Sequence[MesConsumerDeclaration],
    registry: MesSuccessorRegistry | None = None,
    *,
    exclusions: Sequence[MesConsumerExclusion] | None = None,
    discovery_roots: Sequence[str] | None = None,
) -> MesConsumerScanReport:
    """Scan hash-declared active consumers and fail closed on every bypass.

    A caller cannot obtain a vacuous green result by passing no declarations.
    The static scan is intentionally conservative: an active MES consumer may
    import the typed COMMON registry, but direct legacy/EGS3 imports or copied
    stale triples remain release blockers even if the typed import is present.
    """

    if isinstance(declarations, (str, bytes)) or not isinstance(declarations, Sequence):
        raise MesRegistryError("declarations must be a sequence")
    if not all(isinstance(item, MesConsumerDeclaration) for item in declarations):
        raise MesRegistryError(
            "declarations must contain MesConsumerDeclaration values"
        )
    consumer_ids = tuple(item.consumer_id for item in declarations)
    source_paths = tuple(item.source.path for item in declarations)
    if len(set(consumer_ids)) != len(consumer_ids):
        raise MesRegistryError("duplicate consumer_id")
    if len(set(source_paths)) != len(source_paths):
        raise MesRegistryError("duplicate active consumer source path")

    (
        inventory_roots,
        inventory_declarations,
        inventory_exclusions,
        inventory_present,
    ) = _load_inventory_controls(repo_root)
    if inventory_present and tuple(
        sorted(declarations, key=lambda item: item.consumer_id)
    ) != tuple(sorted(inventory_declarations, key=lambda item: item.consumer_id)):
        raise MesRegistryError(
            "caller declarations cannot replace the repository inventory"
        )
    if inventory_present and exclusions is not None:
        if tuple(exclusions) != inventory_exclusions:
            raise MesRegistryError(
                "caller exclusions cannot replace the repository inventory"
            )
    if inventory_present and discovery_roots is not None:
        if tuple(discovery_roots) != inventory_roots:
            raise MesRegistryError(
                "caller discovery roots cannot replace the repository inventory"
            )
    selected_exclusions = inventory_exclusions if exclusions is None else exclusions
    if isinstance(selected_exclusions, (str, bytes)) or not isinstance(
        selected_exclusions, Sequence
    ):
        raise MesRegistryError("exclusions must be a sequence")
    if not all(isinstance(item, MesConsumerExclusion) for item in selected_exclusions):
        raise MesRegistryError("exclusions must contain MesConsumerExclusion values")
    exclusion_ids = tuple(item.exclusion_id for item in selected_exclusions)
    exclusion_paths = tuple(item.source.path for item in selected_exclusions)
    if len(exclusion_ids) != len(set(exclusion_ids)):
        raise MesRegistryError("duplicate exclusion_id")
    if len(exclusion_paths) != len(set(exclusion_paths)):
        raise MesRegistryError("duplicate excluded consumer path")
    overlap = sorted(set(source_paths) & set(exclusion_paths))
    if overlap:
        raise MesRegistryError(
            "consumer paths cannot be both declared and excluded: " + ", ".join(overlap)
        )

    base = validate_mes_successor_registry(repo_root, registry)
    findings = list(base.findings)
    if not declarations:
        findings.append(
            MesConsumerFinding(
                MesConsumerIssueCode.NO_ACTIVE_CONSUMERS_DECLARED,
                "active_mes_consumers",
                "the all-consumer set must be explicit and non-empty",
            )
        )
        return MesConsumerScanReport(base.registry, 0, tuple(findings))

    for exclusion in selected_exclusions:
        binding_findings = _verify_binding(
            repo_root,
            exclusion.source,
            subject=exclusion.exclusion_id,
        )
        for finding in binding_findings:
            findings.append(
                MesConsumerFinding(
                    MesConsumerIssueCode.EXCLUSION_HASH_MISMATCH,
                    exclusion.exclusion_id,
                    f"{finding.code.value}: {finding.detail}",
                )
            )

    roots = inventory_roots if discovery_roots is None else tuple(discovery_roots)
    discovered, discovery_findings, discovery_enabled = _discover_active_mes_consumers(
        repo_root, roots
    )
    findings.extend(discovery_findings)
    if discovery_enabled:
        declared_set = set(source_paths)
        excluded_set = set(exclusion_paths)
        for path in sorted(discovered - declared_set - excluded_set):
            findings.append(
                MesConsumerFinding(
                    MesConsumerIssueCode.UNDECLARED_ACTIVE_CONSUMER,
                    path,
                    (
                        "discovered exact MES identifier/import is neither "
                        "declared nor excluded"
                    ),
                )
            )
        for path in sorted(declared_set - discovered):
            findings.append(
                MesConsumerFinding(
                    MesConsumerIssueCode.DECLARED_CONSUMER_NOT_DISCOVERED,
                    path,
                    "declared source has no exact active MES identifier/import",
                )
            )

    for declaration in sorted(declarations, key=lambda item: item.consumer_id):
        findings.extend(
            _verify_binding(
                repo_root,
                declaration.source,
                subject=declaration.consumer_id,
            )
        )
        if declaration.expected_successor_id != base.registry.successor.successor_id:
            findings.append(
                MesConsumerFinding(
                    MesConsumerIssueCode.SUCCESSOR_ID_MISMATCH,
                    declaration.consumer_id,
                    (
                        f"expected {declaration.expected_successor_id}, registry has "
                        f"{base.registry.successor.successor_id}"
                    ),
                )
            )

        path = _bound_path(repo_root, declaration.source)
        if path.is_symlink() or not path.is_file():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            findings.append(
                MesConsumerFinding(
                    MesConsumerIssueCode.CONSUMER_PARSE_ERROR,
                    declaration.consumer_id,
                    str(exc),
                )
            )
            continue

        modules = _imported_modules(tree)
        if not _uses_typed_successor_entrypoint(tree):
            findings.append(
                MesConsumerFinding(
                    MesConsumerIssueCode.SUCCESSOR_POINTER_MISSING,
                    declaration.consumer_id,
                    (
                        "active MES consumer does not call the typed COMMON "
                        "current_mes_successor_registry entrypoint"
                    ),
                )
            )
        bypass_modules = {
            module for module in modules if _is_bypass_module(module)
        } | _dynamic_bypass_modules(tree)
        for module in sorted(bypass_modules):
            findings.append(
                MesConsumerFinding(
                    MesConsumerIssueCode.SUCCESSOR_BYPASS,
                    declaration.consumer_id,
                    f"direct non-authoritative MES import: {module}",
                )
            )
        for triple_name in sorted(_stale_triples(tree)):
            findings.append(
                MesConsumerFinding(
                    MesConsumerIssueCode.STALE_MES_TRIPLE,
                    declaration.consumer_id,
                    triple_name,
                )
            )

    return MesConsumerScanReport(base.registry, len(declarations), tuple(findings))


def finding_codes(report: MesConsumerScanReport) -> frozenset[str]:
    """Return stable string codes for graph/package gate integration."""

    if not isinstance(report, MesConsumerScanReport):
        raise MesRegistryError("report must be a MesConsumerScanReport")
    return frozenset(finding.code.value for finding in report.findings)


__all__ = [
    "CURRENT_SUCCESSOR_ID",
    "DEFAULT_ACTIVE_PYTHON_ROOTS",
    "DEFAULT_CONSUMER_INVENTORY_PATH",
    "EGS3_BRANCH_SEAL_PATH",
    "EGS3_BRANCH_SEAL_SHA256",
    "EGS3_BRANCH_WITNESS_SHA256",
    "LEGACY_REPRODUCTION_SHA256",
    "MesConsumerDeclaration",
    "MesConsumerExclusion",
    "MesConsumerFinding",
    "MesConsumerIssueCode",
    "MesConsumerScanReport",
    "MesDiagnosticWitness",
    "MesProcessResult",
    "MesRegistryError",
    "MesScientificAuthorityStatus",
    "MesSuccessorPointer",
    "MesSuccessorRegistry",
    "PLANNED_PR124_SOURCE",
    "SCHEMA_VERSION",
    "SourceAvailability",
    "SourceHashBinding",
    "current_mes_successor_registry",
    "finding_codes",
    "scan_declared_mes_consumers",
    "sha256_file",
    "validate_mes_successor_registry",
]
