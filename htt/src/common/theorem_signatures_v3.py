"""Fail-closed PR-268 theorem-obligation registry and tensor oracle wrapper.

Version 3 is additive.  It never edits or reinterprets the frozen v2 registry,
and no v3 row counts as a proved theorem until a later registered proof gate
adjudicates that row.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping, Sequence

import yaml

from common.tensor_foundations_oracle import (
    DEFAULT_SEED,
    ORACLE_ID,
    PROPOSITION_IDS,
    run_all as run_oracle,
)
from common.vector_tensor_program_registry import (
    ProofClass,
    load_vector_tensor_program_registry,
)


SCHEMA_VERSION = "htt.theorem_signatures.v3"
REGISTRY_PATH = (
    "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml"
)
INTAKE_PATH = (
    "docs/research_program/vector_tensor/PROGRAM_INTAKE_REGISTRY_V1.yaml"
)
SIGNATURES_V2_PATH = "docs/research_program/THEOREM_SIGNATURES_V2.yaml"
SIGNATURES_V2_LOADER_PATH = "htt/src/common/theorem_signatures.py"
TWO_PILLAR_PATH = (
    "docs/research_program/vector_tensor/proof_registry_two_pillars.yaml"
)
ORACLE_PROPOSAL_PATH = (
    "docs/research_program/vector_tensor/"
    "tensor_foundations_oracle_proposal.py"
)
ORACLE_PRODUCTION_PATH = "htt/src/common/tensor_foundations_oracle.py"

FROZEN_SOURCE_HASHES = {
    SIGNATURES_V2_PATH:
        "4e43de815088b372cac82e889fe86b55c815f327af231611336b11ebb8a487d9",
    SIGNATURES_V2_LOADER_PATH:
        "214edec76e6deb8c2064b7edb5765a683213b552783baebe6be1b902fa0e160e",
    INTAKE_PATH:
        "b6964771c50c483e7697b087b9f058a3fd7d20ec893475a056608b852fdeb677",
    TWO_PILLAR_PATH:
        "01e278c2223c7f117b429a3359dbc3d483ce0ef409bbb06140b62a9ca3b2f201",
    ORACLE_PROPOSAL_PATH:
        "ddd819323642f5b86e26ee8cad2c9e0bca9175ab842aa66ac4fc81d0c20eb444",
}

ORACLE_LINKS = {
    "TF-01-PARITY-TYPING": "I-1.1",
    "TF-02-CATALOGUE-COMPLETION": "I-2.5",
    "TF-03-KRYLOV-SYZYGY": "I-2.3",
    "TF-04-CAYLEY-HAMILTON-REDUCTION": "I-2.2",
    "TF-05-SHAPE-DISCRIMINANT": "I-2.4",
    "TF-06-INVARIANT-DIMENSION": "I-1.2",
    "TF-07-BUDGET-MORPHOLOGY-SPLIT": "I-3.1",
    "TF-08-PRODUCT-GAUGE-MAX": "II-2.1",
    "TF-09-PARITY-SIGN-EXACTNESS": "II-3.1",
    "TF-10-LOCAL-GLOBAL-SEPARATION": "II-1.2",
    "TF-11-MASK-PATH-MARTINGALE": "II-3.2",
    "TF-12-ACCELERATION-EULER-SLAVING": "I-4.1",
}

REQUIRED_EVIDENCE = {
    ProofClass.U: (
        "typed_cross_pillar_argument",
        "counterexample_boundary",
        "independent_adjudication",
    ),
    ProofClass.TC: (
        "typed_mathematical_physics_proof_artifact",
        "domain_appropriate_exact_or_cas_evidence",
        "counterexample_boundary",
        "independent_adjudication",
    ),
    ProofClass.ST: (
        "typed_statistical_proof_artifact",
        "sampling_law_and_covariance_assumptions",
        "finite_sample_or_asymptotic_status",
        "independent_adjudication",
    ),
}

MUTATION_VECTOR_IDS = (
    "TF-MUT-ORACLE-ID",
    "TF-MUT-SEED",
    "TF-MUT-MISSING-PROPOSITION",
    "TF-MUT-PROPOSITION-FAIL",
    "TF-MUT-UNPROVEN-PROMOTION",
    "TF-MUT-PREMISE-ERASURE",
)


class TheoremSignatureV3Error(ValueError):
    """Raised when v3 registration or oracle evidence drifts."""


class SourceGroup(str, Enum):
    LEGACY = "legacy_signature_inventory"
    PROPOSAL = "proposal_registry_rows"


class ComponentStatus(str, Enum):
    DECLARED = "DECLARED"
    SOURCE_NOT_TYPED = "SOURCE_NOT_TYPED"


class StatementStatus(str, Enum):
    DECLARED = "DECLARED"
    TITLE_ONLY = "TITLE_ONLY"
    SOURCE_NOT_TYPED = "SOURCE_NOT_TYPED"


class ProofAdjudicationStatus(str, Enum):
    NOT_ADJUDICATED = "NOT_ADJUDICATED"


def _sha256(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise TheoremSignatureV3Error(
            f"required source is missing or not regular: {path}"
        )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise TheoremSignatureV3Error(f"{field} must be a mapping")
    return value


def _rows(value: object, field: str) -> tuple[Mapping[str, object], ...]:
    if (
        isinstance(value, (str, bytes))
        or not isinstance(value, Sequence)
        or any(not isinstance(item, Mapping) for item in value)
    ):
        raise TheoremSignatureV3Error(
            f"{field} must be a list of mappings"
        )
    return tuple(value)


def _strings(
    value: object,
    field: str,
    *,
    empty_ok: bool = False,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TheoremSignatureV3Error(f"{field} must be a list of strings")
    result = tuple(_text(item, f"{field}[]") for item in value)
    if not empty_ok and not result:
        raise TheoremSignatureV3Error(f"{field} must be non-empty")
    return result


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TheoremSignatureV3Error(
            f"{field} must be a non-empty string"
        )
    return value.strip()


def _nullable_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    return _text(value, field)


def _source_map(
    rows: Sequence[Mapping[str, object]],
    field: str,
) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for row in rows:
        entry_id = _text(row.get("id"), f"{field}.id")
        if entry_id in result:
            raise TheoremSignatureV3Error(
                f"{field} has duplicate id {entry_id}"
            )
        result[entry_id] = row
    return result


@dataclass(frozen=True)
class TheoremSignatureV3:
    entry_id: str
    source_group: SourceGroup
    source_partition: str
    statement_status: StatementStatus
    statement: str | None
    statement_identity_sha256: str
    source_record_sha256: str
    assumption_status: ComponentStatus
    assumptions: tuple[str, ...]
    domain_status: ComponentStatus
    domains: tuple[str, ...]
    frame_status: ComponentStatus
    frame_convention: str | None
    branch_status: ComponentStatus
    branch_convention: str | None
    perturbative_order_status: ComponentStatus
    perturbative_order: str | None
    proof_class: ProofClass
    registry_owner: str
    scientific_owner: str
    dependencies: tuple[str, ...]
    required_evidence: tuple[str, ...]
    evidence_path: str
    source_status: str
    registration_status: str
    proof_adjudication_status: ProofAdjudicationStatus
    claim_ceiling: str

    @property
    def counts_toward_theorem_count(self) -> bool:
        """Registration alone never counts as an adjudicated theorem."""

        return False


@dataclass(frozen=True)
class OracleStatementLink:
    proposition_id: str
    entry_id: str
    primary_source_status: str
    alignment_status: str
    alignment_scope: str
    proof_effect: str


@dataclass(frozen=True)
class TensorOracleValidation:
    valid: bool
    errors: tuple[str, ...]
    receipt_sha256: str
    proof_effect: str = "none"
    evidence_posture: str = "EXECUTABLE_TEST_EVIDENCE_ONLY"


@dataclass(frozen=True)
class TheoremSignatureRegistryV3:
    legacy_entries: tuple[TheoremSignatureV3, ...]
    proposal_entries: tuple[TheoremSignatureV3, ...]
    oracle_links: tuple[OracleStatementLink, ...]
    oracle_source_sha256: str
    oracle_production_sha256: str
    stable_vector_ids: tuple[str, ...]
    mutation_vector_ids: tuple[str, ...]
    claim_ceiling: str
    proof_adjudication_status: ProofAdjudicationStatus

    @property
    def entries(self) -> tuple[TheoremSignatureV3, ...]:
        return self.legacy_entries + self.proposal_entries

    def entry(self, entry_id: str) -> TheoremSignatureV3:
        matches = tuple(
            entry for entry in self.entries if entry.entry_id == entry_id
        )
        if len(matches) != 1:
            raise TheoremSignatureV3Error(
                f"expected one v3 entry for {entry_id!r}"
            )
        return matches[0]

    def reject_raw_theorem_count(self, claimed_count: int) -> None:
        raise TheoremSignatureV3Error(
            f"raw v3 registry cardinality {claimed_count} is not an "
            "adjudicated theorem count"
        )


def _validate_component(
    status: ComponentStatus,
    sequence: tuple[str, ...] | None,
    scalar: str | None,
    field: str,
) -> None:
    has_value = bool(sequence) if sequence is not None else scalar is not None
    if status is ComponentStatus.DECLARED and not has_value:
        raise TheoremSignatureV3Error(
            f"{field}: DECLARED component has no value"
        )
    if status is ComponentStatus.SOURCE_NOT_TYPED and has_value:
        raise TheoremSignatureV3Error(
            f"{field}: SOURCE_NOT_TYPED component acquired a value"
        )


def _parse_entry(raw: Mapping[str, object]) -> TheoremSignatureV3:
    entry_id = _text(raw.get("entry_id"), "entry_id")
    try:
        source_group = SourceGroup(_text(
            raw.get("source_group"), f"{entry_id}.source_group"
        ))
        statement_status = StatementStatus(_text(
            raw.get("statement_status"), f"{entry_id}.statement_status"
        ))
        assumption_status = ComponentStatus(_text(
            raw.get("assumption_status"), f"{entry_id}.assumption_status"
        ))
        domain_status = ComponentStatus(_text(
            raw.get("domain_status"), f"{entry_id}.domain_status"
        ))
        frame_status = ComponentStatus(_text(
            raw.get("frame_status"), f"{entry_id}.frame_status"
        ))
        branch_status = ComponentStatus(_text(
            raw.get("branch_status"), f"{entry_id}.branch_status"
        ))
        order_status = ComponentStatus(_text(
            raw.get("perturbative_order_status"),
            f"{entry_id}.perturbative_order_status",
        ))
        proof_class = ProofClass(_text(
            raw.get("proof_class"), f"{entry_id}.proof_class"
        ))
        adjudication = ProofAdjudicationStatus(_text(
            raw.get("proof_adjudication_status"),
            f"{entry_id}.proof_adjudication_status",
        ))
    except ValueError as exc:
        raise TheoremSignatureV3Error(
            f"{entry_id}: unsupported typed enum value"
        ) from exc
    statement = _nullable_text(
        raw.get("statement"), f"{entry_id}.statement"
    )
    if statement_status is StatementStatus.SOURCE_NOT_TYPED:
        if statement is not None:
            raise TheoremSignatureV3Error(
                f"{entry_id}: missing statement acquired text"
            )
    elif statement is None:
        raise TheoremSignatureV3Error(
            f"{entry_id}: typed statement has no text"
        )
    assumptions = _strings(
        raw.get("assumptions"),
        f"{entry_id}.assumptions",
        empty_ok=True,
    )
    domains = _strings(
        raw.get("domains"),
        f"{entry_id}.domains",
        empty_ok=True,
    )
    frame = _nullable_text(
        raw.get("frame_convention"), f"{entry_id}.frame_convention"
    )
    branch = _nullable_text(
        raw.get("branch_convention"), f"{entry_id}.branch_convention"
    )
    order = _nullable_text(
        raw.get("perturbative_order"),
        f"{entry_id}.perturbative_order",
    )
    _validate_component(
        assumption_status, assumptions, None, f"{entry_id}.assumptions"
    )
    _validate_component(
        domain_status, domains, None, f"{entry_id}.domains"
    )
    _validate_component(
        frame_status, None, frame, f"{entry_id}.frame"
    )
    _validate_component(
        branch_status, None, branch, f"{entry_id}.branch"
    )
    _validate_component(
        order_status, None, order, f"{entry_id}.perturbative_order"
    )
    identity = _text(
        raw.get("statement_identity_sha256"),
        f"{entry_id}.statement_identity_sha256",
    )
    source_identity = _text(
        raw.get("source_record_sha256"),
        f"{entry_id}.source_record_sha256",
    )
    if any(
        len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
        for value in (identity, source_identity)
    ):
        raise TheoremSignatureV3Error(
            f"{entry_id}: source identities must be lowercase SHA-256"
        )
    required_evidence = _strings(
        raw.get("required_evidence"), f"{entry_id}.required_evidence"
    )
    if required_evidence != REQUIRED_EVIDENCE[proof_class]:
        raise TheoremSignatureV3Error(
            f"{entry_id}: required evidence route drifted"
        )
    registration_status = _text(
        raw.get("registration_status"),
        f"{entry_id}.registration_status",
    )
    if registration_status != "REGISTERED_OBLIGATION":
        raise TheoremSignatureV3Error(
            f"{entry_id}: registration status cannot promote proof"
        )
    claim_ceiling = _text(
        raw.get("claim_ceiling"), f"{entry_id}.claim_ceiling"
    )
    if claim_ceiling != "diagnostic_only":
        raise TheoremSignatureV3Error(
            f"{entry_id}: claim ceiling drifted"
        )
    return TheoremSignatureV3(
        entry_id=entry_id,
        source_group=source_group,
        source_partition=_text(
            raw.get("source_partition"),
            f"{entry_id}.source_partition",
        ),
        statement_status=statement_status,
        statement=statement,
        statement_identity_sha256=identity,
        source_record_sha256=source_identity,
        assumption_status=assumption_status,
        assumptions=assumptions,
        domain_status=domain_status,
        domains=domains,
        frame_status=frame_status,
        frame_convention=frame,
        branch_status=branch_status,
        branch_convention=branch,
        perturbative_order_status=order_status,
        perturbative_order=order,
        proof_class=proof_class,
        registry_owner=_text(
            raw.get("registry_owner"), f"{entry_id}.registry_owner"
        ),
        scientific_owner=_text(
            raw.get("scientific_owner"), f"{entry_id}.scientific_owner"
        ),
        dependencies=_strings(
            raw.get("dependencies"), f"{entry_id}.dependencies"
        ),
        required_evidence=required_evidence,
        evidence_path=_text(
            raw.get("evidence_path"), f"{entry_id}.evidence_path"
        ),
        source_status=_text(
            raw.get("source_status"), f"{entry_id}.source_status"
        ),
        registration_status=registration_status,
        proof_adjudication_status=adjudication,
        claim_ceiling=claim_ceiling,
    )


def _assert_entry_matches_source(
    entry: TheoremSignatureV3,
    intake_row: Mapping[str, object],
    source_row: Mapping[str, object],
) -> None:
    entry_id = entry.entry_id
    expected_common = {
        "source_partition": _text(
            intake_row.get("source_partition"),
            f"{entry_id}.intake partition",
        ),
        "proof_class": _text(
            intake_row.get("proof_class"),
            f"{entry_id}.intake proof_class",
        ),
        "registry_owner": _text(
            intake_row.get("registry_owner"),
            f"{entry_id}.intake registry_owner",
        ),
        "scientific_owner": _text(
            intake_row.get("scientific_owner"),
            f"{entry_id}.intake scientific_owner",
        ),
        "dependencies": _strings(
            intake_row.get("dependencies"),
            f"{entry_id}.intake dependencies",
        ),
        "evidence_path": _text(
            intake_row.get("evidence_path"),
            f"{entry_id}.intake evidence_path",
        ),
        "source_status": _text(
            intake_row.get("source_status"),
            f"{entry_id}.intake source_status",
        ),
    }
    actual_common = {
        "source_partition": entry.source_partition,
        "proof_class": entry.proof_class.value,
        "registry_owner": entry.registry_owner,
        "scientific_owner": entry.scientific_owner,
        "dependencies": entry.dependencies,
        "evidence_path": entry.evidence_path,
        "source_status": entry.source_status,
    }
    if actual_common != expected_common:
        raise TheoremSignatureV3Error(
            f"{entry_id}: v3 row drifted from PR-260 intake"
        )

    if entry.source_group is SourceGroup.LEGACY:
        signature_status = _text(
            source_row.get("signature_status"),
            f"{entry_id}.v2 signature status",
        )
        identity_payload = {
            "id": entry_id,
            "title": _text(
                source_row.get("title"), f"{entry_id}.v2 title"
            ),
            "signature_status": signature_status,
            "signature": source_row.get("signature"),
        }
        if entry.statement_identity_sha256 != _canonical_sha256(
            identity_payload
        ):
            raise TheoremSignatureV3Error(
                f"{entry_id}: legacy statement identity drifted"
            )
        if entry.source_record_sha256 != _canonical_sha256(source_row):
            raise TheoremSignatureV3Error(
                f"{entry_id}: legacy source identity drifted"
            )
        if signature_status == "CHECKED":
            signature = _mapping(
                source_row.get("signature"), f"{entry_id}.v2 signature"
            )
            expected = (
                ComponentStatus.DECLARED,
                _strings(
                    signature.get("hypotheses"),
                    f"{entry_id}.v2 hypotheses",
                ),
                ComponentStatus.DECLARED,
                (
                    _text(
                        signature.get("domain"),
                        f"{entry_id}.v2 domain",
                    ),
                ),
                ComponentStatus.DECLARED,
                _text(
                    signature.get("frame"), f"{entry_id}.v2 frame"
                ),
                ComponentStatus.SOURCE_NOT_TYPED,
                None,
                ComponentStatus.DECLARED,
                _text(
                    signature.get("perturbative_order"),
                    f"{entry_id}.v2 order",
                ),
            )
        else:
            expected = (
                ComponentStatus.SOURCE_NOT_TYPED,
                (),
                ComponentStatus.SOURCE_NOT_TYPED,
                (),
                ComponentStatus.SOURCE_NOT_TYPED,
                None,
                ComponentStatus.SOURCE_NOT_TYPED,
                None,
                ComponentStatus.SOURCE_NOT_TYPED,
                None,
            )
        actual = (
            entry.assumption_status,
            entry.assumptions,
            entry.domain_status,
            entry.domains,
            entry.frame_status,
            entry.frame_convention,
            entry.branch_status,
            entry.branch_convention,
            entry.perturbative_order_status,
            entry.perturbative_order,
        )
        if actual != expected:
            raise TheoremSignatureV3Error(
                f"{entry_id}: v2 component typing drifted"
            )
    else:
        identity = _canonical_sha256(source_row)
        if (
            entry.statement_identity_sha256 != identity
            or entry.source_record_sha256 != identity
            or _text(
                intake_row.get("statement_identity_sha256"),
                f"{entry_id}.intake statement identity",
            )
            != identity
        ):
            raise TheoremSignatureV3Error(
                f"{entry_id}: proposal statement identity drifted"
            )
        missing = (
            entry.assumption_status,
            entry.assumptions,
            entry.domain_status,
            entry.domains,
            entry.frame_status,
            entry.frame_convention,
            entry.branch_status,
            entry.branch_convention,
            entry.perturbative_order_status,
            entry.perturbative_order,
        )
        if missing != (
            ComponentStatus.SOURCE_NOT_TYPED,
            (),
            ComponentStatus.SOURCE_NOT_TYPED,
            (),
            ComponentStatus.SOURCE_NOT_TYPED,
            None,
            ComponentStatus.SOURCE_NOT_TYPED,
            None,
            ComponentStatus.SOURCE_NOT_TYPED,
            None,
        ):
            raise TheoremSignatureV3Error(
                f"{entry_id}: proposal prose was promoted to typed premises"
            )


def load_theorem_signature_registry_v3(
    repo_root: Path,
    registry_path: str | Path = REGISTRY_PATH,
) -> TheoremSignatureRegistryV3:
    repo_root = Path(repo_root)
    for relative, expected in FROZEN_SOURCE_HASHES.items():
        actual = _sha256(repo_root / relative)
        if actual != expected:
            raise TheoremSignatureV3Error(
                f"frozen source drifted: {relative} "
                f"(expected {expected}, got {actual})"
            )
    load_vector_tensor_program_registry(repo_root)
    path = repo_root / registry_path
    if path.is_symlink() or not path.is_file():
        raise TheoremSignatureV3Error(
            "THEOREM_SIGNATURES_V3.yaml is missing or not regular"
        )
    payload = _mapping(
        yaml.safe_load(path.read_text(encoding="utf-8")),
        "v3 registry",
    )
    if payload.get("schema") != SCHEMA_VERSION:
        raise TheoremSignatureV3Error("v3 schema drifted")
    required_top = {
        "status": "REGISTERED",
        "authority": "PR-268",
        "scientific_status_effect": "none",
        "claim_ceiling": "diagnostic_only",
        "proof_adjudication_status": "NOT_ADJUDICATED",
        "counting_rule":
            "registry rows and oracle PASS are not theorem counts",
    }
    if any(payload.get(key) != value for key, value in required_top.items()):
        raise TheoremSignatureV3Error(
            "v3 registry status or claim boundary drifted"
        )
    frozen = _rows(payload.get("frozen_sources"), "frozen_sources")
    frozen_map = {
        _text(row.get("path"), "frozen path"):
        _text(row.get("sha256"), "frozen sha256")
        for row in frozen
    }
    if frozen_map != FROZEN_SOURCE_HASHES:
        raise TheoremSignatureV3Error("v3 frozen-source pins drifted")
    aliases = _mapping(
        payload.get("cardinality_aliases"), "cardinality_aliases"
    )
    if aliases.get("requested_pillar_T_65") != SourceGroup.LEGACY.value:
        raise TheoremSignatureV3Error("65-row alias semantics drifted")
    if aliases.get("requested_pillar_S_58") != SourceGroup.PROPOSAL.value:
        raise TheoremSignatureV3Error("58-row alias semantics drifted")
    guard = _text(aliases.get("semantic_guard"), "semantic_guard")
    if any(
        token not in guard
        for token in ("31 T", "34 S", "30 I", "24 II", "4 BRIDGE")
    ):
        raise TheoremSignatureV3Error(
            "cardinality alias lost its true source partitions"
        )

    intake = _mapping(
        yaml.safe_load(
            (repo_root / INTAKE_PATH).read_text(encoding="utf-8")
        ),
        "intake",
    )
    v2 = _mapping(
        yaml.safe_load(
            (repo_root / SIGNATURES_V2_PATH).read_text(encoding="utf-8")
        ),
        "v2 signatures",
    )
    proposal = _mapping(
        yaml.safe_load(
            (repo_root / TWO_PILLAR_PATH).read_text(encoding="utf-8")
        ),
        "two-pillar source",
    )
    source_groups = _mapping(
        payload.get("source_groups"), "source_groups"
    )
    legacy_group = _mapping(
        source_groups.get(SourceGroup.LEGACY.value), "legacy source group"
    )
    proposal_group = _mapping(
        source_groups.get(SourceGroup.PROPOSAL.value),
        "proposal source group",
    )
    if legacy_group.get("expected_count") != 65:
        raise TheoremSignatureV3Error("legacy v3 count must be 65")
    if proposal_group.get("expected_count") != 58:
        raise TheoremSignatureV3Error("proposal v3 count must be 58")
    legacy_entries = tuple(
        _parse_entry(row)
        for row in _rows(legacy_group.get("entries"), "legacy entries")
    )
    proposal_entries = tuple(
        _parse_entry(row)
        for row in _rows(proposal_group.get("entries"), "proposal entries")
    )
    if len(legacy_entries) != 65 or len(proposal_entries) != 58:
        raise TheoremSignatureV3Error("v3 row cardinality drifted")
    if (
        sum(entry.source_partition == "T" for entry in legacy_entries) != 31
        or sum(entry.source_partition == "S" for entry in legacy_entries) != 34
        or sum(entry.source_partition == "I" for entry in proposal_entries) != 30
        or sum(entry.source_partition == "II" for entry in proposal_entries) != 24
        or sum(
            entry.source_partition == "BRIDGE"
            for entry in proposal_entries
        )
        != 4
    ):
        raise TheoremSignatureV3Error("true source partitions drifted")
    all_ids = tuple(
        entry.entry_id for entry in legacy_entries + proposal_entries
    )
    if len(all_ids) != len(set(all_ids)):
        raise TheoremSignatureV3Error(
            "legacy and proposal v3 identifiers are not disjoint"
        )
    if any(
        entry.source_group is not SourceGroup.LEGACY
        for entry in legacy_entries
    ) or any(
        entry.source_group is not SourceGroup.PROPOSAL
        for entry in proposal_entries
    ):
        raise TheoremSignatureV3Error("entry source-group label drifted")

    legacy_intake = _source_map(
        _rows(
            _mapping(
                intake.get(SourceGroup.LEGACY.value),
                "legacy intake",
            ).get("entries"),
            "legacy intake entries",
        ),
        "legacy intake",
    )
    proposal_intake = _source_map(
        _rows(
            _mapping(
                intake.get(SourceGroup.PROPOSAL.value),
                "proposal intake",
            ).get("entries"),
            "proposal intake entries",
        ),
        "proposal intake",
    )
    v2_sources = _source_map(
        _rows(v2.get("entries"), "v2 entries"), "v2"
    )
    proposal_sources = _source_map(
        _rows(proposal.get("entries"), "proposal source entries"),
        "proposal source",
    )
    for entry in legacy_entries:
        _assert_entry_matches_source(
            entry,
            legacy_intake[entry.entry_id],
            v2_sources[entry.entry_id],
        )
    for entry in proposal_entries:
        _assert_entry_matches_source(
            entry,
            proposal_intake[entry.entry_id],
            proposal_sources[entry.entry_id],
        )

    oracle = _mapping(payload.get("oracle"), "oracle")
    if (
        oracle.get("oracle_id") != ORACLE_ID
        or oracle.get("seed") != DEFAULT_SEED
        or oracle.get("proposition_count") != len(PROPOSITION_IDS)
        or oracle.get("evidence_posture")
        != "EXECUTABLE_TEST_EVIDENCE_ONLY"
        or oracle.get("proof_effect") != "none"
    ):
        raise TheoremSignatureV3Error("oracle registration drifted")
    source_digest = _sha256(repo_root / ORACLE_PROPOSAL_PATH)
    production_digest = _sha256(repo_root / ORACLE_PRODUCTION_PATH)
    if (
        source_digest != production_digest
        or oracle.get("source_sha256") != source_digest
        or oracle.get("production_sha256") != production_digest
    ):
        raise TheoremSignatureV3Error(
            "production oracle is not the registered proposal source"
        )
    raw_links = _rows(
        oracle.get("statement_links"), "oracle statement_links"
    )
    links = tuple(
        OracleStatementLink(
            proposition_id=_text(
                row.get("proposition_id"), "oracle proposition_id"
            ),
            entry_id=_text(row.get("entry_id"), "oracle entry_id"),
            primary_source_status=_text(
                row.get("primary_source_status"),
                "oracle primary_source_status",
            ),
            alignment_status=_text(
                row.get("alignment_status"), "oracle alignment_status"
            ),
            alignment_scope=_text(
                row.get("alignment_scope"), "oracle alignment_scope"
            ),
            proof_effect=_text(
                row.get("proof_effect"), "oracle proof_effect"
            ),
        )
        for row in raw_links
    )
    if {link.proposition_id: link.entry_id for link in links} != ORACLE_LINKS:
        raise TheoremSignatureV3Error("oracle statement links drifted")
    proposal_by_id = {
        entry.entry_id: entry for entry in proposal_entries
    }
    source_by_id = {
        _text(row.get("id"), "proposal source id"): row
        for row in _rows(proposal.get("entries"), "proposal source entries")
    }
    for link in links:
        entry = proposal_by_id.get(link.entry_id)
        if entry is None:
            raise TheoremSignatureV3Error(
                f"{link.proposition_id}: linked row is missing"
            )
        if link.primary_source_status != entry.source_status:
            raise TheoremSignatureV3Error(
                f"{link.proposition_id}: source status link drifted"
            )
        source_row = source_by_id[link.entry_id]
        reference_tokens = json.dumps(
            {
                "legacy_id": source_row.get("legacy_id"),
                "also": source_row.get("also"),
                "evidence": source_row.get("evidence"),
            },
            sort_keys=True,
        )
        short_id = link.proposition_id.split("-", 2)[:2]
        needle = "-".join(short_id)
        if (
            link.proposition_id not in reference_tokens
            and needle not in reference_tokens
        ):
            raise TheoremSignatureV3Error(
                f"{link.proposition_id}: source row lacks oracle reference"
            )
        if (
            link.alignment_status
            != "ALIGNED_FOR_EXECUTABLE_TEST_INTAKE"
            or link.proof_effect != "none"
        ):
            raise TheoremSignatureV3Error(
                f"{link.proposition_id}: oracle link promoted proof status"
            )

    stable_rows = _rows(
        oracle.get("stable_vectors"), "oracle stable_vectors"
    )
    stable_ids = tuple(
        _text(row.get("id"), "stable vector id") for row in stable_rows
    )
    mutation_rows = _rows(
        oracle.get("mutation_vectors"), "oracle mutation_vectors"
    )
    mutation_ids = tuple(
        _text(row.get("id"), "mutation vector id")
        for row in mutation_rows
    )
    if mutation_ids != MUTATION_VECTOR_IDS:
        raise TheoremSignatureV3Error("oracle mutation vectors drifted")
    if stable_ids != (
        "TF-STABLE-FULL-20260730",
        "TF-STABLE-REPEAT-20260730",
    ):
        raise TheoremSignatureV3Error("oracle stable vectors drifted")
    if oracle.get("supplied_fast_mode_status") != (
        "REPRODUCED_NON_STABLE_TF11_AT_REGISTERED_SEED"
    ):
        raise TheoremSignatureV3Error(
            "supplied fast-mode limitation was lost"
        )
    return TheoremSignatureRegistryV3(
        legacy_entries=legacy_entries,
        proposal_entries=proposal_entries,
        oracle_links=links,
        oracle_source_sha256=source_digest,
        oracle_production_sha256=production_digest,
        stable_vector_ids=stable_ids,
        mutation_vector_ids=mutation_ids,
        claim_ceiling="diagnostic_only",
        proof_adjudication_status=ProofAdjudicationStatus.NOT_ADJUDICATED,
    )


def _receipt_identity(receipt: object) -> str:
    return _canonical_sha256(receipt)


def validate_tensor_oracle_receipt(
    receipt: object,
    *,
    require_full_vector: bool = True,
) -> TensorOracleValidation:
    errors: list[str] = []
    if not isinstance(receipt, Mapping):
        return TensorOracleValidation(
            valid=False,
            errors=("oracle receipt must be a mapping",),
            receipt_sha256=_receipt_identity({"invalid": repr(receipt)}),
        )
    if receipt.get("oracle_id") != ORACLE_ID:
        errors.append("oracle_id mismatch")
    if receipt.get("seed") != DEFAULT_SEED:
        errors.append("registered seed mismatch")
    if receipt.get("n_propositions") != len(PROPOSITION_IDS):
        errors.append("proposition count mismatch")
    if require_full_vector and receipt.get("fast") is not False:
        errors.append("stable vector must use the full registered oracle")
    propositions = receipt.get("propositions")
    if not isinstance(propositions, Mapping):
        errors.append("propositions must be a mapping")
        propositions = {}
    if set(propositions) != set(PROPOSITION_IDS):
        errors.append("proposition membership mismatch")
    for proposition_id in PROPOSITION_IDS:
        row = propositions.get(proposition_id)
        if not isinstance(row, Mapping):
            errors.append(f"{proposition_id}: result missing")
            continue
        if row.get("proposition") != proposition_id:
            errors.append(f"{proposition_id}: identity mismatch")
        if row.get("ok") is not True:
            errors.append(f"{proposition_id}: executable check failed")
    failed = receipt.get("failed")
    if failed not in ((), []):
        errors.append("oracle failed list is non-empty")
    if receipt.get("ok") is not True:
        errors.append("oracle aggregate ok is not true")

    tf02 = propositions.get("TF-02-CATALOGUE-COMPLETION", {})
    if isinstance(tf02, Mapping):
        if tf02.get("generic_orbit_separation_status") != (
            "UNPROVEN (unchanged)"
        ):
            errors.append("TF-02 generic separation was promoted")
        if tf02.get("degree_completeness_status") != (
            "UNPROVEN (unchanged)"
        ):
            errors.append("TF-02 degree completeness was promoted")
    tf06 = propositions.get("TF-06-INVARIANT-DIMENSION", {})
    if isinstance(tf06, Mapping):
        if tf06.get("scope") != (
            "principal stratum only (finite generic isotropy)"
        ):
            errors.append("TF-06 principal-stratum scope drifted")
        if tf06.get("not_an_identifiability_claim") is not True:
            errors.append("TF-06 became an identifiability claim")
    tf12 = propositions.get(
        "TF-12-ACCELERATION-EULER-SLAVING", {}
    )
    if isinstance(tf12, Mapping):
        premises = tf12.get("premises")
        required_premises = {
            "perfect_fluid",
            "vanishing_frame_heat_flux",
            "vanishing_anisotropic_stress",
            "barotropic_or_constant_w",
            "gradient_regularity_registered",
        }
        if (
            isinstance(premises, (str, bytes))
            or not isinstance(premises, Sequence)
            or set(premises) != required_premises
        ):
            errors.append("TF-12 premise block drifted")
        if (
            tf12.get("authority_kind") != "MOMENTUM_CONSTRAINT_NOT_MES"
            or tf12.get("absolute_scale_meaningful") is not False
        ):
            errors.append("TF-12 authority or scale caveat drifted")
    return TensorOracleValidation(
        valid=not errors,
        errors=tuple(errors),
        receipt_sha256=_receipt_identity(receipt),
    )


def run_registered_tensor_oracle(
    registry: TheoremSignatureRegistryV3,
) -> tuple[Mapping[str, object], TensorOracleValidation]:
    if registry.proof_adjudication_status is not (
        ProofAdjudicationStatus.NOT_ADJUDICATED
    ):
        raise TheoremSignatureV3Error(
            "oracle wrapper cannot consume a promoted registry"
        )
    receipt = run_oracle(seed=DEFAULT_SEED, fast=False)
    return receipt, validate_tensor_oracle_receipt(receipt)


def exercise_tensor_oracle_mutations(
    receipt: Mapping[str, object],
) -> Mapping[str, tuple[str, ...]]:
    baseline = validate_tensor_oracle_receipt(receipt)
    if not baseline.valid:
        raise TheoremSignatureV3Error(
            "mutation vectors require a valid full oracle receipt"
        )
    mutations: dict[str, Mapping[str, object]] = {}

    oracle_id = copy.deepcopy(receipt)
    oracle_id["oracle_id"] = "TENSOR_FOUNDATIONS_ORACLE_FORGED"
    mutations["TF-MUT-ORACLE-ID"] = oracle_id

    seed = copy.deepcopy(receipt)
    seed["seed"] = DEFAULT_SEED + 1
    mutations["TF-MUT-SEED"] = seed

    missing = copy.deepcopy(receipt)
    missing["propositions"].pop(PROPOSITION_IDS[0])
    mutations["TF-MUT-MISSING-PROPOSITION"] = missing

    failed = copy.deepcopy(receipt)
    failed["propositions"][PROPOSITION_IDS[0]]["ok"] = False
    mutations["TF-MUT-PROPOSITION-FAIL"] = failed

    promotion = copy.deepcopy(receipt)
    promotion["propositions"][
        "TF-02-CATALOGUE-COMPLETION"
    ]["generic_orbit_separation_status"] = "PROVEN"
    mutations["TF-MUT-UNPROVEN-PROMOTION"] = promotion

    premises = copy.deepcopy(receipt)
    premises["propositions"][
        "TF-12-ACCELERATION-EULER-SLAVING"
    ]["premises"] = ()
    mutations["TF-MUT-PREMISE-ERASURE"] = premises

    results: dict[str, tuple[str, ...]] = {}
    for vector_id in MUTATION_VECTOR_IDS:
        validation = validate_tensor_oracle_receipt(mutations[vector_id])
        if validation.valid:
            raise TheoremSignatureV3Error(
                f"{vector_id}: mutation survived validation"
            )
        results[vector_id] = validation.errors
    return results


__all__ = [
    "ComponentStatus",
    "MUTATION_VECTOR_IDS",
    "OracleStatementLink",
    "ProofAdjudicationStatus",
    "REGISTRY_PATH",
    "SCHEMA_VERSION",
    "SourceGroup",
    "StatementStatus",
    "TensorOracleValidation",
    "TheoremSignatureRegistryV3",
    "TheoremSignatureV3",
    "TheoremSignatureV3Error",
    "exercise_tensor_oracle_mutations",
    "load_theorem_signature_registry_v3",
    "run_registered_tensor_oracle",
    "validate_tensor_oracle_receipt",
]
