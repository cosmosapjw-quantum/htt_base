"""Fail-closed loader for the PR-260 vector/tensor programme intake.

This registry records source identities and future proof obligations.  Loading
it does not validate a theorem, admit observational data, or promote a
scientific claim.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping, Sequence

import yaml


SCHEMA_VERSION = "htt.vector_tensor_program_intake.v1"
REGISTRY_PATH = (
    "docs/research_program/vector_tensor/PROGRAM_INTAKE_REGISTRY_V1.yaml"
)
PROGRAM_SCHEMA = "htt.vector_tensor_proof_program.draft.v1"
PROPOSAL_SCHEMA = "htt.proof_registry.two_pillars.v1"
LEGACY_SCHEMA = "htt.theorem_registry.v2"
CANONICAL_DAG_EXTENSION = (
    "PR-261",
    "PR-262",
    "PR-263",
    "PR-264",
    "PR-265",
    "PR-266",
    "PR-267",
    "PR-268",
    "PR-269",
    "PR-271",
    "PR-270",
    "PR-272",
    "PR-273",
    "PR-274",
    "PR-275",
)
CANONICAL_DAG_DEPENDENCIES = {
    "PR-261": ("PR-260", "PR-249", "PR-256"),
    "PR-262": ("PR-261", "PR-254"),
    "PR-263": ("PR-261", "PR-257"),
    "PR-264": ("PR-262", "PR-263"),
    "PR-265": ("PR-264", "PR-250"),
    "PR-266": ("PR-264",),
    "PR-267": (
        "PR-263",
        "PR-265",
        "PR-266",
        "PR-255",
        "PR-256",
        "PR-258",
    ),
    "PR-268": ("PR-262", "PR-263", "PR-267"),
    "PR-269": ("PR-268",),
    "PR-270": ("PR-269",),
    "PR-271": ("PR-268",),
    "PR-272": ("PR-271",),
    "PR-273": ("PR-270", "PR-272"),
    "PR-274": ("PR-273",),
    "PR-275": ("PR-274",),
}
_SHA256 = re.compile(r"[0-9a-f]{64}")


class VectorTensorProgramRegistryError(ValueError):
    """Raised when the registered PR-260 intake contract is inconsistent."""


class ProofClass(str, Enum):
    """Proof/evidence route declared by the source programme."""

    U = "U"
    TC = "TC"
    ST = "ST"


@dataclass(frozen=True)
class ProgramRegistryEntry:
    """One registered source record or proof obligation."""

    entry_id: str
    proof_class: ProofClass
    registry_owner: str
    dependencies: tuple[str, ...]
    evidence_path: str
    claim_ceiling: str
    source_partition: str | None = None
    source_status: str | None = None


@dataclass(frozen=True)
class SourceIdentity:
    """Identity of one supplied programme source."""

    source_id: str
    tracked_path: str
    source_attachment_sha256: str
    tracked_sha256: str
    normalization: str


@dataclass(frozen=True)
class VectorTensorProgramRegistry:
    """Validated, non-claim-bearing PR-260 intake."""

    legacy_signatures: tuple[ProgramRegistryEntry, ...]
    proposal_rows: tuple[ProgramRegistryEntry, ...]
    obligations: tuple[ProgramRegistryEntry, ...]
    vt_theorems: tuple[ProgramRegistryEntry, ...]
    source_identities: tuple[SourceIdentity, ...]
    canonical_dag_extension: tuple[str, ...]
    canonical_dag_dependencies: Mapping[str, tuple[str, ...]]

    @property
    def all_entries(self) -> tuple[ProgramRegistryEntry, ...]:
        return (
            self.legacy_signatures
            + self.proposal_rows
            + self.obligations
            + self.vt_theorems
        )

    def entry(self, entry_id: str) -> ProgramRegistryEntry:
        matches = tuple(row for row in self.all_entries if row.entry_id == entry_id)
        if len(matches) != 1:
            raise VectorTensorProgramRegistryError(
                f"expected exactly one registry entry for {entry_id!r}"
            )
        return matches[0]


def _nonempty(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise VectorTensorProgramRegistryError(
            f"{field} must be a non-empty string"
        )
    return value.strip()


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise VectorTensorProgramRegistryError(f"{field} must be a mapping")
    return value


def _rows(value: object, field: str) -> tuple[Mapping[str, object], ...]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or any(not isinstance(row, Mapping) for row in value)
    ):
        raise VectorTensorProgramRegistryError(
            f"{field} must be a list of mappings"
        )
    return tuple(value)


def _strings(value: object, field: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise VectorTensorProgramRegistryError(
            f"{field} must be a list of strings"
        )
    result = tuple(_nonempty(item, f"{field}[]") for item in value)
    if not result:
        raise VectorTensorProgramRegistryError(f"{field} must be non-empty")
    return result


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_entry(raw: Mapping[str, object], section: str) -> ProgramRegistryEntry:
    entry_id = _nonempty(raw.get("id"), f"{section}.id")
    try:
        proof_class = ProofClass(_nonempty(
            raw.get("proof_class"), f"{entry_id}.proof_class"
        ))
    except ValueError as exc:
        raise VectorTensorProgramRegistryError(
            f"{entry_id}: unsupported proof class {raw.get('proof_class')!r}"
        ) from exc
    dependencies = _strings(
        raw.get("dependencies"), f"{entry_id}.dependencies"
    )
    if any(re.fullmatch(r"PR-\d+", item) is None for item in dependencies):
        raise VectorTensorProgramRegistryError(
            f"{entry_id}: every dependency must be a PR identifier"
        )
    claim_ceiling = _nonempty(
        raw.get("claim_ceiling"), f"{entry_id}.claim_ceiling"
    )
    if claim_ceiling != "diagnostic_only":
        raise VectorTensorProgramRegistryError(
            f"{entry_id}: claim ceiling must remain diagnostic_only"
        )
    source_partition = raw.get("source_partition")
    source_status = raw.get("source_status")
    return ProgramRegistryEntry(
        entry_id=entry_id,
        proof_class=proof_class,
        registry_owner=_nonempty(
            raw.get("registry_owner"), f"{entry_id}.registry_owner"
        ),
        dependencies=dependencies,
        evidence_path=_nonempty(
            raw.get("evidence_path"), f"{entry_id}.evidence_path"
        ),
        claim_ceiling=claim_ceiling,
        source_partition=(
            _nonempty(source_partition, f"{entry_id}.source_partition")
            if source_partition is not None
            else None
        ),
        source_status=(
            _nonempty(source_status, f"{entry_id}.source_status")
            if source_status is not None
            else None
        ),
    )


def _parse_section(
    payload: Mapping[str, object],
    name: str,
    expected_count: int,
) -> tuple[ProgramRegistryEntry, ...]:
    section = _mapping(payload.get(name), name)
    if section.get("expected_count") not in (None, expected_count):
        raise VectorTensorProgramRegistryError(
            f"{name}.expected_count must be {expected_count}"
        )
    entries = tuple(
        _parse_entry(row, name)
        for row in _rows(section.get("entries"), f"{name}.entries")
    )
    if len(entries) != expected_count:
        raise VectorTensorProgramRegistryError(
            f"{name} must contain exactly {expected_count} entries"
        )
    return entries


def _partition_counts(
    entries: Sequence[ProgramRegistryEntry],
) -> dict[str, int]:
    result: dict[str, int] = {}
    for entry in entries:
        if entry.source_partition is None:
            raise VectorTensorProgramRegistryError(
                f"{entry.entry_id}: source partition is required"
            )
        result[entry.source_partition] = (
            result.get(entry.source_partition, 0) + 1
        )
    return result


def _parse_sources(
    payload: Mapping[str, object], repo_root: Path
) -> tuple[SourceIdentity, ...]:
    source_rows = _rows(payload.get("source_identities"), "source_identities")
    if len(source_rows) != 8:
        raise VectorTensorProgramRegistryError(
            "exactly eight supplied source identities are required"
        )
    result: list[SourceIdentity] = []
    for raw in source_rows:
        source_id = _nonempty(raw.get("source_id"), "source_id")
        tracked_path = _nonempty(
            raw.get("tracked_path"), f"{source_id}.tracked_path"
        )
        attachment_sha = _nonempty(
            raw.get("source_attachment_sha256"),
            f"{source_id}.source_attachment_sha256",
        )
        tracked_sha = _nonempty(
            raw.get("tracked_sha256"), f"{source_id}.tracked_sha256"
        )
        if _SHA256.fullmatch(attachment_sha) is None:
            raise VectorTensorProgramRegistryError(
                f"{source_id}: invalid attachment SHA-256"
            )
        if _SHA256.fullmatch(tracked_sha) is None:
            raise VectorTensorProgramRegistryError(
                f"{source_id}: invalid tracked SHA-256"
            )
        source_path = repo_root / tracked_path
        if source_path.is_symlink() or not source_path.is_file():
            raise VectorTensorProgramRegistryError(
                f"{source_id}: tracked source is missing or not regular"
            )
        actual_sha = _sha256(source_path)
        if actual_sha != tracked_sha:
            raise VectorTensorProgramRegistryError(
                f"{source_id}: tracked source hash drifted "
                f"(expected {tracked_sha}, got {actual_sha})"
            )
        result.append(
            SourceIdentity(
                source_id=source_id,
                tracked_path=tracked_path,
                source_attachment_sha256=attachment_sha,
                tracked_sha256=tracked_sha,
                normalization=_nonempty(
                    raw.get("normalization"), f"{source_id}.normalization"
                ),
            )
        )
    if {source.source_id for source in result} != {
        f"A{index}" for index in range(1, 9)
    }:
        raise VectorTensorProgramRegistryError(
            "source identities must be exactly A1 through A8"
        )
    return tuple(result)


def load_vector_tensor_program_registry(
    repo_root: Path,
    registry_path: str | Path = REGISTRY_PATH,
) -> VectorTensorProgramRegistry:
    """Load and validate the registered programme without promoting claims."""

    repo_root = Path(repo_root)
    path = repo_root / registry_path
    if path.is_symlink() or not path.is_file():
        raise VectorTensorProgramRegistryError(
            "vector/tensor programme registry is missing or not regular"
        )
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload = _mapping(raw, "registry")
    if payload.get("schema") != SCHEMA_VERSION:
        raise VectorTensorProgramRegistryError("programme intake schema drifted")
    if payload.get("status") != "REGISTERED":
        raise VectorTensorProgramRegistryError(
            "programme intake status must be REGISTERED"
        )
    source_schemas = _mapping(payload.get("source_schemas"), "source_schemas")
    if source_schemas != {
        "programme": PROGRAM_SCHEMA,
        "two_pillar_proposal": PROPOSAL_SCHEMA,
        "legacy_signatures": LEGACY_SCHEMA,
    }:
        raise VectorTensorProgramRegistryError(
            "registered source schema identities drifted"
        )
    claim_boundary = _mapping(
        payload.get("claim_boundary"), "claim_boundary"
    )
    required_boundary = {
        "scientific_status_effect": "none",
        "claim_ceiling": "diagnostic_only",
        "theorem_count_claim": "FORBIDDEN_FROM_RAW_CARDINALITY",
        "native_solver_result": False,
        "family_identification": False,
        "observational_use": False,
    }
    if claim_boundary != required_boundary:
        raise VectorTensorProgramRegistryError("claim boundary drifted")

    aliases = _mapping(payload.get("cardinality_aliases"), "cardinality_aliases")
    if aliases.get("requested_pillar_T_65") != "legacy_signature_inventory":
        raise VectorTensorProgramRegistryError(
            "65-entry alias must retain legacy-inventory semantics"
        )
    if aliases.get("requested_pillar_S_58") != "proposal_registry_rows":
        raise VectorTensorProgramRegistryError(
            "58-entry alias must retain proposal-row semantics"
        )
    semantic_guard = _nonempty(
        aliases.get("semantic_guard"), "cardinality_aliases.semantic_guard"
    )
    if any(
        token not in semantic_guard
        for token in ("31 T", "34 S", "30 I", "24 II", "4 BRIDGE")
    ):
        raise VectorTensorProgramRegistryError(
            "cardinality alias omits the true source partitions"
        )

    legacy = _parse_section(
        payload, "legacy_signature_inventory", expected_count=65
    )
    proposal = _parse_section(
        payload, "proposal_registry_rows", expected_count=58
    )
    obligations = _parse_section(
        payload, "obligation_classes", expected_count=54
    )
    vt_theorems = _parse_section(
        payload, "vt_theorem_obligations", expected_count=28
    )
    obligation_counts = _mapping(
        _mapping(payload.get("obligation_classes"), "obligation_classes").get(
            "expected_counts"
        ),
        "obligation_classes.expected_counts",
    )
    if obligation_counts != {"U": 9, "TC": 20, "ST": 25}:
        raise VectorTensorProgramRegistryError(
            "declared U/TC/ST obligation counts drifted"
        )
    vt_counts = _mapping(
        _mapping(
            payload.get("vt_theorem_obligations"),
            "vt_theorem_obligations",
        ).get("expected_counts"),
        "vt_theorem_obligations.expected_counts",
    )
    if vt_counts != {"VT-T": 14, "VT-S": 14}:
        raise VectorTensorProgramRegistryError(
            "declared VT-T/VT-S counts drifted"
        )

    if _partition_counts(legacy) != {"T": 31, "S": 34}:
        raise VectorTensorProgramRegistryError(
            "legacy inventory must remain 31 T / 34 S"
        )
    if _partition_counts(proposal) != {"I": 30, "II": 24, "BRIDGE": 4}:
        raise VectorTensorProgramRegistryError(
            "proposal registry must remain 30 I / 24 II / 4 BRIDGE"
        )
    obligation_ids = {entry.entry_id for entry in obligations}
    if obligation_ids != (
        {f"U{index}" for index in range(1, 10)}
        | {f"TC-{index:02d}" for index in range(1, 21)}
        | {f"ST-{index:02d}" for index in range(1, 26)}
    ):
        raise VectorTensorProgramRegistryError(
            "U/TC/ST obligation identifiers drifted"
        )
    vt_ids = {entry.entry_id for entry in vt_theorems}
    if vt_ids != (
        {f"VT-T{index}" for index in range(1, 15)}
        | {f"VT-S{index}" for index in range(1, 15)}
    ):
        raise VectorTensorProgramRegistryError("VT theorem identifiers drifted")
    if sum(entry.proof_class is ProofClass.U for entry in obligations) != 9:
        raise VectorTensorProgramRegistryError("U obligation count drifted")
    if sum(entry.proof_class is ProofClass.TC for entry in obligations) != 20:
        raise VectorTensorProgramRegistryError("TC obligation count drifted")
    if sum(entry.proof_class is ProofClass.ST for entry in obligations) != 25:
        raise VectorTensorProgramRegistryError("ST obligation count drifted")

    all_entries = legacy + proposal + obligations + vt_theorems
    all_ids = tuple(entry.entry_id for entry in all_entries)
    if len(all_ids) != len(set(all_ids)):
        raise VectorTensorProgramRegistryError(
            "legacy/proposal/U-TC-ST/VT identifiers must be disjoint"
        )
    dag_extension = tuple(
        _nonempty(value, "canonical_dag_extension[]")
        for value in _rows_as_strings(
            payload.get("canonical_dag_extension"),
            "canonical_dag_extension",
        )
    )
    if dag_extension != CANONICAL_DAG_EXTENSION:
        raise VectorTensorProgramRegistryError(
            "canonical PR-261 through PR-275 order drifted"
        )
    raw_dependencies = _mapping(
        payload.get("canonical_dag_dependencies"),
        "canonical_dag_dependencies",
    )
    dag_dependencies = {
        _nonempty(pr_id, "canonical_dag_dependencies key"): _strings(
            dependencies,
            f"canonical_dag_dependencies.{pr_id}",
        )
        for pr_id, dependencies in raw_dependencies.items()
    }
    if dag_dependencies != CANONICAL_DAG_DEPENDENCIES:
        raise VectorTensorProgramRegistryError(
            "canonical PR-261 through PR-275 dependencies drifted"
        )

    return VectorTensorProgramRegistry(
        legacy_signatures=legacy,
        proposal_rows=proposal,
        obligations=obligations,
        vt_theorems=vt_theorems,
        source_identities=_parse_sources(payload, repo_root),
        canonical_dag_extension=dag_extension,
        canonical_dag_dependencies=dag_dependencies,
    )


def _rows_as_strings(value: object, field: str) -> tuple[str, ...]:
    """Validate a scalar-string sequence without accepting mappings."""

    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise VectorTensorProgramRegistryError(f"{field} must be a list")
    return tuple(_nonempty(item, f"{field}[]") for item in value)
