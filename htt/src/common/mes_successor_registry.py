"""Fail-closed pointer and consumer scanner for the MES authority.

PR-122 established the typed pointer that active consumers must traverse;
PR-124 delivered the typed theorem/convention authority
(``htt/src/common/mes_theorem_authority.py``) with a four-axis CAS
adjudication, a derivation-lineage oracle, and hash-bound receipts.  The
successor pointer is now ``AVAILABLE`` and ``AUTHORIZED_BY_PR124`` at
roadmap_rescue_v1:C1 (domain/frame-conditional derived mechanics).

Authorization is never a caller-supplied string: the pointer's
``scientific_authority`` requires the module-pinned receipt hash, and every
governance validation (``validate_mes_successor_registry``) re-verifies the
exact receipt bytes live through ``mes_theorem_authority``.  Receipt drift,
a failed four-axis adjudication, a zero D2 receipt, or a stale MES triple
in an active consumer re-blocks the authority.

The EGS3 branch-registry seal is retained as hash-bound process evidence.
Its ``PASS`` result means that its own diagnostic checks executed
successfully; it is not a theorem-authority receipt and cannot make a
release claim-ready.  PR-124 authority is governance mechanics only — it
rescues no remediation finding and validates no observed result.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping, Sequence

import yaml


SCHEMA_VERSION = "pr122.mes_successor_registry.v1"
CURRENT_SUCCESSOR_ID = "mes.typed-successor.pr124"
PLANNED_PR124_SOURCE = "htt/src/common/mes_theorem_authority.py"

# PR-124 delivery pins.  The authority-source pin binds the exact bytes of
# the typed authority module; the receipt pin binds the exact bytes of the
# generated authority table (docs/generated/pr124_mes_authority_table.json).
# Regenerating either is a sanctioned governance event that must update
# these constants (and re-run the PR-122 evidence-graph resync ritual);
# silent drift is re-blocked by validate_mes_successor_registry.
PR124_AUTHORITY_SOURCE_SHA256 = (
    "d149d8599eba65dd1af536d30f289466b642e990bd8cee6cc8639566ab787af8"
)
PR124_AUTHORITY_RECEIPT_SHA256 = (
    "81ad8c382fbe481eaf715b971680199fed5142e2498928cff57ae9d847cc20f3"
)

# These hashes bind the PR-122 registry to the exact legacy reproduction and
# EGS3 diagnostic-witness bytes that were inspected.  Updating either source
# requires an explicit registry update; silently consuming changed bytes is a
# release blocker.
LEGACY_REPRODUCTION_SHA256 = (
    "281a35d1bd2a54f0aef236ffda0f33b4154e1e31eeb096eb209b2af1924af33a"
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
DEFAULT_CONSUMER_SUPERSESSION_PATH = (
    "docs/research_program/stat_foundations/"
    "pr248_mes_consumer_supersession.yaml"
)
PR248_CONSUMER_SUPERSESSION_SHA256 = (
    "7a96eff7d3cc7929fc2d090f835da359848d6a5ee3d9fd7e22da4a5763e0109e"
)
DEFAULT_CONSUMER_MIGRATION_PATH = (
    "docs/research_program/stat_foundations/"
    "pr252_mes_consumer_migration.yaml"
)
# Filled only after the PR-252 migration document binds the final consumer
# bytes.  A mismatch fails closed before any migrated declaration is trusted.
PR252_CONSUMER_MIGRATION_SHA256 = (
    "0121b247d9f54e86cd54c6e8df26aa9d190e0f40d0d15a56445c76148f8c5624"
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
# PR-124: htt.core.bounds was removed from the bypass set after it was
# rewired to traverse the typed successor and fetch its legacy-reproduction
# values through legacy_reproduction_coefficients() (no unmanaged literals).
# The frozen legacy reproduction module and the EGS3 diagnostic modules
# remain bypasses for active consumers.
_BYPASS_MODULES = frozenset(
    {
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
        "MESAnchorSpec",
        "MES_LINEAR",
        "AnchorStressReport",
        "Sig2_max_MES",
        "TeffMESBounds",
        "W2_max_MES",
        "compute_mes_bounds",
        "compute_mes_bounds_2sigma_upper",
        "compute_planck_central_bounds",
        "delta_B_sigma",
        "evaluate_sector_stress",
        "quarantined_shear_anchors",
        "registered_geodesic_mes_anchors",
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
# are used only by the static mutation scanner to detect copied stale literals
# and by the labeled legacy-reproduction channel below.
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

# The sigma triple is branch-independent (geodesic == registered).
_LEGACY_SIGMA_TRIPLE = (Fraction(5, 3), Fraction(3, 1), Fraction(3, 7))


def legacy_reproduction_coefficients() -> dict[str, tuple[Fraction, ...]]:
    """Labeled legacy-reproduction MES coefficient triples (PR-124 channel).

    Active consumers that must keep their historical numerical outputs
    byte-stable fetch the legacy triples HERE instead of carrying unmanaged
    stale literals.  These are the pre-refreeze registered values: the sigma
    triple equals the verified geodesic one, while the omega/accel triples
    are the UNVERIFIED print-only non-geodesic MESb values (in-house
    reconstruction REFUTED, rev-r190).  They are explicitly NON-AUTHORITATIVE:
    the live authority is the typed successor
    (``mes_theorem_authority.BRANCHES``), and flowing the authorized geodesic
    values into result-producing consumers is a result-regeneration event
    owned by later PRs, not by this accessor.
    """
    return {
        "sigma": _LEGACY_SIGMA_TRIPLE,
        "omega": _STALE_TRIPLES["legacy_non_geodesic_omega"],
        "accel": _STALE_TRIPLES["legacy_non_geodesic_acceleration"],
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
            # PR-124 delivered the receipt schema and verifier.  An AVAILABLE
            # successor must carry the exact shape below, and its authority
            # is still NOT a caller-supplied capability: scientific_authority
            # requires the module-pinned receipt hash, and every governance
            # validation re-verifies the receipt bytes live through
            # mes_theorem_authority.verify_authority_receipt.
            if process_result is not MesProcessResult.PASS:
                raise MesRegistryError(
                    "an AVAILABLE successor must record the PR-124 gate PASS"
                )
            if (
                scientific_status
                is not MesScientificAuthorityStatus.AUTHORIZED_BY_PR124
            ):
                raise MesRegistryError(
                    "an AVAILABLE successor must be AUTHORIZED_BY_PR124"
                )
            receipt = _sha256(receipt, "authority_receipt_id")

        object.__setattr__(self, "successor_id", successor_id)
        object.__setattr__(self, "process_result", process_result)
        object.__setattr__(self, "scientific_status", scientific_status)
        object.__setattr__(self, "authority_receipt_id", receipt)

    @property
    def scientific_authority(self) -> bool:
        # Strings alone never escalate: authority requires the AVAILABLE
        # pointer shape AND the module-pinned PR-124 receipt hash.  Live
        # byte re-verification happens in validate_mes_successor_registry;
        # any receipt drift re-blocks the release there.
        return (
            self.source.availability is SourceAvailability.AVAILABLE
            and self.process_result is MesProcessResult.PASS
            and self.scientific_status
            is MesScientificAuthorityStatus.AUTHORIZED_BY_PR124
            and self.authority_receipt_id == PR124_AUTHORITY_RECEIPT_SHA256
        )

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


@lru_cache(maxsize=1)
def _live_receipt_pin_check() -> str:
    """Cheap, once-per-process check that the on-disk PR-124 authority
    receipt bytes match the module pin.

    This closes the string-tautology escalation route: a consumer that reads
    ``current_mes_successor_registry().as_payload()`` without running the
    governance validation still cannot obtain an AVAILABLE/AUTHORIZED
    pointer unless the actual receipt bytes on disk hash to the pin. Deep
    content verification remains in ``validate_mes_successor_registry``.
    """
    repo_root = Path(__file__).resolve().parents[3]
    receipt = repo_root / "docs/generated/pr124_mes_authority_table.json"
    if not receipt.is_file():
        raise MesRegistryError(
            "PR-124 authority receipt is missing on disk; the typed MES "
            "successor cannot be constructed without its receipt bytes"
        )
    digest = sha256_file(receipt)
    if digest != PR124_AUTHORITY_RECEIPT_SHA256:
        raise MesRegistryError(
            "PR-124 authority receipt bytes do not match the module pin "
            f"({digest}); regenerate + re-pin before consuming the successor"
        )
    return digest


def current_mes_successor_registry() -> MesSuccessorRegistry:
    """Return the current PR-122 pointer without importing a physics module.

    PR-124: constructing the AVAILABLE successor requires the live receipt
    bytes on disk to hash to the module pin (fail-closed, memoized once per
    process)."""

    _live_receipt_pin_check()
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
                availability=SourceAvailability.AVAILABLE,
                sha256=PR124_AUTHORITY_SOURCE_SHA256,
            ),
            process_result=MesProcessResult.PASS,
            scientific_status=(MesScientificAuthorityStatus.AUTHORIZED_BY_PR124),
            authority_receipt_id=PR124_AUTHORITY_RECEIPT_SHA256,
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
    else:
        # PR-124: authorization derives from exact receipt bytes.  Re-verify
        # the receipts live; any drift, a failed four-axis adjudication, a
        # zero D2 receipt, or a stale consumer triple re-blocks the release.
        try:
            from common.mes_theorem_authority import verify_authority_receipt

            verification = verify_authority_receipt(repo_root)
            if verification.receipt_sha256 != PR124_AUTHORITY_RECEIPT_SHA256:
                findings.append(
                    MesConsumerFinding(
                        MesConsumerIssueCode.SCIENTIFIC_AUTHORITY_BLOCKED,
                        selected.successor.successor_id,
                        (
                            "authority receipt bytes drifted from the pinned "
                            f"hash ({verification.receipt_sha256})"
                        ),
                    )
                )
            elif (
                selected.successor.authority_receipt_id
                != verification.receipt_sha256
            ):
                findings.append(
                    MesConsumerFinding(
                        MesConsumerIssueCode.SCIENTIFIC_AUTHORITY_BLOCKED,
                        selected.successor.successor_id,
                        "successor pointer carries a foreign receipt id",
                    )
                )
        except MesRegistryError:
            raise
        except Exception as exc:  # MesAuthorityError and any receipt failure
            findings.append(
                MesConsumerFinding(
                    MesConsumerIssueCode.SCIENTIFIC_AUTHORITY_BLOCKED,
                    selected.successor.successor_id,
                    f"authority receipt verification failed: {exc}",
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
    effective_declarations = _apply_consumer_supersessions(
        repo_root, tuple(declarations)
    )
    effective_declarations, effective_exclusions = (
        _apply_pr252_consumer_migration(
            repo_root,
            effective_declarations,
            tuple(exclusions),
        )
    )
    assert effective_exclusions is not None
    return roots, effective_declarations, effective_exclusions, True


def _apply_consumer_supersessions(
    repo_root: Path,
    declarations: tuple[MesConsumerDeclaration, ...],
) -> tuple[MesConsumerDeclaration, ...]:
    """Apply an explicit post-PR-124 hash overlay without rewriting history.

    The PR-122 inventory and PR-124 receipts remain byte-preserved.  A later
    authorized change set may bind new consumer bytes only by naming the exact
    prior digest, exact replacement digest, path, authority card and reason in
    the dedicated overlay.  Any mismatch fails closed.
    """

    path = repo_root / DEFAULT_CONSUMER_SUPERSESSION_PATH
    if not path.exists():
        return declarations
    if path.is_symlink() or not path.is_file():
        raise MesRegistryError(
            "MES consumer supersession must be a regular repository file"
        )
    observed_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed_sha256 != PR248_CONSUMER_SUPERSESSION_SHA256:
        raise MesRegistryError(
            "MES consumer supersession hash does not match the PR-248 "
            "authority root"
        )
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise MesRegistryError(f"invalid MES consumer supersession: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise MesRegistryError("MES consumer supersession root must be a mapping")
    if payload.get("schema") != "htt.mes_consumer_supersession.v1":
        raise MesRegistryError("unsupported MES consumer supersession schema")
    if payload.get("authority") != "PR-248":
        raise MesRegistryError("MES consumer supersession authority must be PR-248")
    rows = payload.get("bindings")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise MesRegistryError("MES consumer supersession bindings must be non-empty")

    by_id = {row.consumer_id: row for row in declarations}
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {
            "consumer_id",
            "path",
            "prior_sha256",
            "sha256",
            "reason",
        }:
            raise MesRegistryError(
                "each supersession requires consumer_id/path/prior_sha256/"
                "sha256/reason"
            )
        consumer_id = _nonempty(row["consumer_id"], "supersession consumer_id")
        if consumer_id in seen:
            raise MesRegistryError("duplicate MES consumer supersession")
        seen.add(consumer_id)
        prior = by_id.get(consumer_id)
        if prior is None:
            raise MesRegistryError(
                f"supersession names unknown consumer {consumer_id!r}"
            )
        source_path = _source_path(row["path"], "supersession path")
        prior_sha = _sha256(row["prior_sha256"], "supersession prior_sha256")
        next_sha = _sha256(row["sha256"], "supersession sha256")
        _nonempty(row["reason"], "supersession reason")
        if source_path != prior.source.path or prior_sha != prior.source.sha256:
            raise MesRegistryError(
                f"supersession prior binding drifted for {consumer_id}"
            )
        if next_sha == prior_sha:
            raise MesRegistryError(
                f"supersession replacement must differ for {consumer_id}"
            )
        by_id[consumer_id] = MesConsumerDeclaration(
            consumer_id=consumer_id,
            source=SourceHashBinding(
                path=source_path,
                availability=SourceAvailability.AVAILABLE,
                sha256=next_sha,
            ),
            expected_successor_id=prior.expected_successor_id,
        )
    return tuple(by_id[row.consumer_id] for row in declarations)


def _apply_pr252_consumer_migration(
    repo_root: Path,
    declarations: tuple[MesConsumerDeclaration, ...],
    exclusions: tuple[MesConsumerExclusion, ...] | None,
) -> tuple[
    tuple[MesConsumerDeclaration, ...],
    tuple[MesConsumerExclusion, ...] | None,
]:
    """Apply the lossless PR-252 active/legacy consumer migration.

    PR-122 and PR-248 remain byte-preserved authority records.  This overlay
    may (1) bind changed active bytes, (2) reclassify an exact prior active
    declaration as an exact legacy exclusion, or (3) bind changed bytes for an
    existing exclusion.  Every transition names its prior digest; an unknown
    identity, path drift, duplicate, or no-op fails closed.

    ``exclusions=None`` is used only to normalize a caller's preserved
    declaration list for compatibility comparison.  In that mode declaration
    bindings and removals still apply, while exclusion rows are not materialized.
    """

    path = repo_root / DEFAULT_CONSUMER_MIGRATION_PATH
    if not path.exists():
        return declarations, exclusions
    if path.is_symlink() or not path.is_file():
        raise MesRegistryError(
            "MES consumer migration must be a regular repository file"
        )
    observed_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed_sha256 != PR252_CONSUMER_MIGRATION_SHA256:
        raise MesRegistryError(
            "MES consumer migration hash does not match the PR-252 authority root"
        )
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise MesRegistryError(f"invalid MES consumer migration: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise MesRegistryError("MES consumer migration root must be a mapping")
    if payload.get("schema") != "htt.mes_consumer_migration.v1":
        raise MesRegistryError("unsupported MES consumer migration schema")
    if payload.get("authority") != "PR-252":
        raise MesRegistryError("MES consumer migration authority must be PR-252")

    binding_rows = payload.get("bindings")
    new_binding_rows = payload.get("new_bindings")
    reclassification_rows = payload.get("legacy_reclassifications")
    exclusion_rows = payload.get("exclusion_bindings")
    for label, rows in (
        ("bindings", binding_rows),
        ("new_bindings", new_binding_rows),
        ("legacy_reclassifications", reclassification_rows),
        ("exclusion_bindings", exclusion_rows),
    ):
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise MesRegistryError(f"MES consumer migration {label} must be a sequence")
    if (
        not binding_rows
        and not new_binding_rows
        and not reclassification_rows
        and not exclusion_rows
    ):
        raise MesRegistryError("MES consumer migration must contain a transition")

    declaration_order = [row.consumer_id for row in declarations]
    declaration_by_id = {row.consumer_id: row for row in declarations}
    declaration_paths = {row.source.path for row in declarations}
    seen_declarations: set[str] = set()

    for row in binding_rows:
        required = {
            "consumer_id",
            "path",
            "prior_sha256",
            "sha256",
            "reason",
        }
        if not isinstance(row, Mapping) or set(row) != required:
            raise MesRegistryError(
                "each PR-252 binding requires consumer_id/path/prior_sha256/"
                "sha256/reason"
            )
        consumer_id = _nonempty(row["consumer_id"], "migration consumer_id")
        if consumer_id in seen_declarations:
            raise MesRegistryError("duplicate PR-252 consumer transition")
        seen_declarations.add(consumer_id)
        prior = declaration_by_id.get(consumer_id)
        if prior is None:
            raise MesRegistryError(
                f"PR-252 binding names unknown consumer {consumer_id!r}"
            )
        source_path = _source_path(row["path"], "migration path")
        prior_sha = _sha256(row["prior_sha256"], "migration prior_sha256")
        next_sha = _sha256(row["sha256"], "migration sha256")
        _nonempty(row["reason"], "migration reason")
        if source_path != prior.source.path or prior_sha != prior.source.sha256:
            raise MesRegistryError(
                f"PR-252 prior binding drifted for {consumer_id}"
            )
        if next_sha == prior_sha:
            raise MesRegistryError(
                f"PR-252 replacement must differ for {consumer_id}"
            )
        declaration_by_id[consumer_id] = MesConsumerDeclaration(
            consumer_id=consumer_id,
            source=SourceHashBinding(
                path=source_path,
                availability=SourceAvailability.AVAILABLE,
                sha256=next_sha,
            ),
            expected_successor_id=prior.expected_successor_id,
        )

    for row in new_binding_rows:
        required = {
            "consumer_id",
            "path",
            "sha256",
            "expected_successor_id",
            "reason",
        }
        if not isinstance(row, Mapping) or set(row) != required:
            raise MesRegistryError(
                "each PR-252 new binding requires consumer_id/path/sha256/"
                "expected_successor_id/reason"
            )
        consumer_id = _nonempty(row["consumer_id"], "new migration consumer_id")
        source_path = _source_path(row["path"], "new migration path")
        digest = _sha256(row["sha256"], "new migration sha256")
        expected_successor_id = _nonempty(
            row["expected_successor_id"],
            "new migration expected_successor_id",
        )
        _nonempty(row["reason"], "new migration reason")
        if consumer_id in declaration_by_id or consumer_id in seen_declarations:
            raise MesRegistryError("duplicate PR-252 new consumer identity")
        if source_path in declaration_paths:
            raise MesRegistryError("duplicate PR-252 new consumer path")
        if expected_successor_id != CURRENT_SUCCESSOR_ID:
            raise MesRegistryError(
                "PR-252 new consumers must traverse the current successor"
            )
        seen_declarations.add(consumer_id)
        declaration_order.append(consumer_id)
        declaration_paths.add(source_path)
        declaration_by_id[consumer_id] = MesConsumerDeclaration(
            consumer_id=consumer_id,
            source=SourceHashBinding(
                path=source_path,
                availability=SourceAvailability.AVAILABLE,
                sha256=digest,
            ),
            expected_successor_id=expected_successor_id,
        )

    materialized_exclusions = (
        None if exclusions is None else list(exclusions)
    )
    existing_exclusion_ids = (
        set()
        if exclusions is None
        else {row.exclusion_id for row in exclusions}
    )
    existing_exclusion_paths = (
        set()
        if exclusions is None
        else {row.source.path for row in exclusions}
    )
    for row in reclassification_rows:
        required = {
            "consumer_id",
            "exclusion_id",
            "path",
            "prior_sha256",
            "sha256",
            "reason",
        }
        if not isinstance(row, Mapping) or set(row) != required:
            raise MesRegistryError(
                "each PR-252 reclassification requires consumer_id/exclusion_id/"
                "path/prior_sha256/sha256/reason"
            )
        consumer_id = _nonempty(
            row["consumer_id"], "reclassification consumer_id"
        )
        if consumer_id in seen_declarations:
            raise MesRegistryError("duplicate PR-252 consumer transition")
        seen_declarations.add(consumer_id)
        prior = declaration_by_id.get(consumer_id)
        if prior is None:
            raise MesRegistryError(
                f"PR-252 reclassification names unknown consumer {consumer_id!r}"
            )
        exclusion_id = _nonempty(
            row["exclusion_id"], "reclassification exclusion_id"
        )
        source_path = _source_path(row["path"], "reclassification path")
        prior_sha = _sha256(
            row["prior_sha256"], "reclassification prior_sha256"
        )
        next_sha = _sha256(row["sha256"], "reclassification sha256")
        reason = _nonempty(row["reason"], "reclassification reason")
        if source_path != prior.source.path or prior_sha != prior.source.sha256:
            raise MesRegistryError(
                f"PR-252 reclassification prior drifted for {consumer_id}"
            )
        if exclusion_id in existing_exclusion_ids:
            raise MesRegistryError("duplicate PR-252 exclusion_id")
        if source_path in existing_exclusion_paths:
            raise MesRegistryError("duplicate PR-252 exclusion path")
        del declaration_by_id[consumer_id]
        if materialized_exclusions is not None:
            materialized_exclusions.append(
                MesConsumerExclusion(
                    exclusion_id=exclusion_id,
                    source=SourceHashBinding(
                        path=source_path,
                        availability=SourceAvailability.AVAILABLE,
                        sha256=next_sha,
                    ),
                    reason=reason,
                )
            )
            existing_exclusion_ids.add(exclusion_id)
            existing_exclusion_paths.add(source_path)

    if exclusions is not None:
        assert materialized_exclusions is not None
        exclusion_order = tuple(row.exclusion_id for row in materialized_exclusions)
        exclusion_by_id = {
            row.exclusion_id: row for row in materialized_exclusions
        }
        seen_exclusions: set[str] = set()
        for row in exclusion_rows:
            required = {
                "exclusion_id",
                "path",
                "prior_sha256",
                "sha256",
                "reason",
            }
            if not isinstance(row, Mapping) or set(row) != required:
                raise MesRegistryError(
                    "each PR-252 exclusion binding requires exclusion_id/path/"
                    "prior_sha256/sha256/reason"
                )
            exclusion_id = _nonempty(
                row["exclusion_id"], "migration exclusion_id"
            )
            if exclusion_id in seen_exclusions:
                raise MesRegistryError("duplicate PR-252 exclusion transition")
            seen_exclusions.add(exclusion_id)
            prior = exclusion_by_id.get(exclusion_id)
            if prior is None:
                raise MesRegistryError(
                    f"PR-252 binding names unknown exclusion {exclusion_id!r}"
                )
            source_path = _source_path(row["path"], "migration exclusion path")
            prior_sha = _sha256(
                row["prior_sha256"], "migration exclusion prior_sha256"
            )
            next_sha = _sha256(
                row["sha256"], "migration exclusion sha256"
            )
            reason = _nonempty(row["reason"], "migration exclusion reason")
            if source_path != prior.source.path or prior_sha != prior.source.sha256:
                raise MesRegistryError(
                    f"PR-252 prior exclusion drifted for {exclusion_id}"
                )
            if next_sha == prior_sha:
                raise MesRegistryError(
                    f"PR-252 exclusion replacement must differ for {exclusion_id}"
                )
            exclusion_by_id[exclusion_id] = MesConsumerExclusion(
                exclusion_id=exclusion_id,
                source=SourceHashBinding(
                    path=source_path,
                    availability=SourceAvailability.AVAILABLE,
                    sha256=next_sha,
                ),
                reason=reason,
            )
        materialized_exclusions = [
            exclusion_by_id[exclusion_id] for exclusion_id in exclusion_order
        ]

    effective_declarations = tuple(
        declaration_by_id[consumer_id]
        for consumer_id in declaration_order
        if consumer_id in declaration_by_id
    )
    effective_exclusions = (
        None
        if materialized_exclusions is None
        else tuple(materialized_exclusions)
    )
    return effective_declarations, effective_exclusions


def _consumer_scan_findings(
    repo_root: Path,
    declarations: Sequence[MesConsumerDeclaration],
    selected_exclusions: Sequence[MesConsumerExclusion],
    roots: Sequence[str],
    successor_id: str,
) -> list[MesConsumerFinding]:
    """Consumer-level findings only (no successor-registry validation).

    This layer is shared by ``scan_declared_mes_consumers`` (which prepends
    the registry validation findings) and by the PR-124 authority verifier
    (which must not recurse through the registry validation that depends on
    its own verdict).
    """
    findings: list[MesConsumerFinding] = []
    source_paths = tuple(item.source.path for item in declarations)
    exclusion_paths = tuple(item.source.path for item in selected_exclusions)

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
        if declaration.expected_successor_id != successor_id:
            findings.append(
                MesConsumerFinding(
                    MesConsumerIssueCode.SUCCESSOR_ID_MISMATCH,
                    declaration.consumer_id,
                    (
                        f"expected {declaration.expected_successor_id}, registry has "
                        f"{successor_id}"
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
    return findings


def scan_consumer_sources_only(
    repo_root: Path,
) -> tuple[MesConsumerFinding, ...]:
    """Run the consumer-level scan from the repository inventory alone.

    Used by the PR-124 authority verifier: it needs the stale-triple and
    bypass verdicts without recursing through the successor-registry
    validation whose authority depends on that very verdict.
    """
    (
        inventory_roots,
        inventory_declarations,
        inventory_exclusions,
        inventory_present,
    ) = _load_inventory_controls(repo_root)
    if not inventory_present:
        raise MesRegistryError(
            "the MES consumer inventory is required for the consumer scan"
        )
    if not inventory_declarations:
        return (
            MesConsumerFinding(
                MesConsumerIssueCode.NO_ACTIVE_CONSUMERS_DECLARED,
                "active_mes_consumers",
                "the all-consumer set must be explicit and non-empty",
            ),
        )
    return tuple(
        _consumer_scan_findings(
            repo_root,
            inventory_declarations,
            inventory_exclusions,
            inventory_roots,
            CURRENT_SUCCESSOR_ID,
        )
    )


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
    if inventory_present:
        caller_declarations = tuple(declarations)
        caller_sorted = tuple(
            sorted(caller_declarations, key=lambda item: item.consumer_id)
        )
        inventory_sorted = tuple(
            sorted(inventory_declarations, key=lambda item: item.consumer_id)
        )
        if caller_sorted != inventory_sorted:
            # Compatibility for callers that faithfully loaded the preserved
            # PR-122 inventory: apply the repository-owned PR-248 and PR-252
            # overlays to that exact declaration set, then require equality
            # with the effective inventory. Arbitrary replacement remains
            # forbidden.
            overlaid = _apply_consumer_supersessions(
                repo_root, caller_declarations
            )
            overlaid, _ = _apply_pr252_consumer_migration(
                repo_root, overlaid, None
            )
            if tuple(
                sorted(overlaid, key=lambda item: item.consumer_id)
            ) != inventory_sorted:
                raise MesRegistryError(
                    "caller declarations cannot replace the repository inventory"
                )
        declarations = inventory_declarations
        consumer_ids = tuple(item.consumer_id for item in declarations)
        source_paths = tuple(item.source.path for item in declarations)
    if inventory_present and exclusions is not None:
        if tuple(exclusions) != inventory_exclusions:
            try:
                preserved_declarations = _apply_consumer_supersessions(
                    repo_root, caller_declarations
                )
                _, migrated_exclusions = _apply_pr252_consumer_migration(
                    repo_root,
                    preserved_declarations,
                    tuple(exclusions),
                )
            except MesRegistryError as exc:
                raise MesRegistryError(
                    "caller exclusions cannot replace the repository inventory"
                ) from exc
            if migrated_exclusions != inventory_exclusions:
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

    roots = inventory_roots if discovery_roots is None else tuple(discovery_roots)
    findings.extend(
        _consumer_scan_findings(
            repo_root,
            declarations,
            selected_exclusions,
            roots,
            base.registry.successor.successor_id,
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
    "DEFAULT_CONSUMER_MIGRATION_PATH",
    "DEFAULT_CONSUMER_INVENTORY_PATH",
    "DEFAULT_CONSUMER_SUPERSESSION_PATH",
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
    "PR248_CONSUMER_SUPERSESSION_SHA256",
    "PR252_CONSUMER_MIGRATION_SHA256",
    "SCHEMA_VERSION",
    "SourceAvailability",
    "SourceHashBinding",
    "current_mes_successor_registry",
    "finding_codes",
    "scan_declared_mes_consumers",
    "sha256_file",
    "validate_mes_successor_registry",
]
