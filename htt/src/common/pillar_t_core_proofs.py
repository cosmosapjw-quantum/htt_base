"""Typed PR-269 analytic/core Pillar-T proof artifacts.

The module has two deliberately separate responsibilities:

* load and validate the additive PR-269 proof-author registry without
  rewriting PR-268 source obligations; and
* expose small executable boundary witnesses for the analytic derivations.

Executable witnesses are regression evidence, not a replacement for the
human-readable proofs and not an observational result.  Nothing here invokes
a native solver, identifies a geometry family, or creates a likelihood,
posterior, Bayes factor, or evidence term.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import math
from pathlib import Path
from typing import Callable, Mapping, Sequence

import numpy as np
import yaml

from common.joint_anisotropy_state import (
    AccelerationNormalization,
    UnitsConvention,
)
from common.orbit_nonlinearity import stf5_to_matrix


SCHEMA_VERSION = "htt.pillar_t_core_proofs.v1"
REGISTRY_PATH = (
    "docs/research_program/vector_tensor/proofs/"
    "PILLAR_T_CORE_PROOFS_V1.yaml"
)
SPEC_PATH = "docs/research_program/vector_tensor/pr269_spec.yaml"
V3_PATH = (
    "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml"
)
INTAKE_PATH = (
    "docs/research_program/vector_tensor/PROGRAM_INTAKE_REGISTRY_V1.yaml"
)
SOURCE_HASHES = {
    SPEC_PATH:
        "1abd632610b7ce51b9bf1ebe91b8f64c32e5ecddeea18af0bfc14901135c1c51",
    V3_PATH:
        "d14b24fda9556545abaf337310471af971c68f01438d32df13349f8cd4308f8b",
    INTAKE_PATH:
        "b6964771c50c483e7697b087b9f058a3fd7d20ec893475a056608b852fdeb677",
    (
        "docs/research_program/vector_tensor/"
        "vector_tensor_mes_upgrade_blueprint.md"
    ):
        "518d4763baafb1cfd57c0674b354f110e86748849cd8cb0a9e4bc1b6eb2f32fc",
    (
        "docs/research_program/"
        "HTT_VECTOR_TENSOR_MES_TWO_PILLAR_UPGRADE_PLAN_20260730.md"
    ):
        "8ac8ddaf6f8d50b2e5c1c628de8749b9e17762e9750755154519e5f7e0dd4944",
    "htt/src/common/joint_anisotropy_state.py":
        "3b3ce3d125ae50103150859541df1300bb19f6b15f82ecf24316d00fb83f0d1c",
    "htt/src/common/tensor_functionals.py":
        "f261a4645dad6dcf7a333f22718de607c8fcb88e289bf251477976be35ba06ac",
    "htt/src/common/orbit_catalogue_v3.py":
        "215746fce9e43407fb3d19750ef6cfcd3258a247b2a4aefc0b22356882400833",
    "htt/src/common/tensor_foundations_oracle.py":
        "ddd819323642f5b86e26ee8cad2c9e0bca9175ab842aa66ac4fc81d0c20eb444",
    "htt/src/common/statistical_foundations.py":
        "8d3706754e41b1b456c12cb0e8b3b446c33ae7f5a78b5902b5e692ce354149aa",
    "htt/src/common/w2_convention.py":
        "39b15209868fe81c8c5f907384820313b90615aa916e0a16f1ad56eb5db8bcac",
}
VT_ANALYTIC_IDS = frozenset(
    {"VT-T1", "VT-T2", "VT-T3", "VT-T4", "VT-T9", "VT-T10"}
)
TF_ANALYTIC_IDS = frozenset(
    {
        "TF-01-PARITY-TYPING",
        "TF-02-CATALOGUE-COMPLETION",
        "TF-07-BUDGET-MORPHOLOGY-SPLIT",
        "TF-08-PRODUCT-GAUGE-MAX",
        "TF-12-ACCELERATION-EULER-SLAVING",
    }
)
REFERENCE_RESOLVED_LEGACY = frozenset(
    {
        "SIG-P3",
        "SIG-P11",
        "SIG-MES-PROV",
        "SIG-TSUM",
        "SIG-MES-BR",
        "SIG-MES-REFREEZE",
        "SIG-MES-MESB-TRACE",
    }
)
CLAIM_CEILING = "diagnostic_only"
REGISTRY_STATUS = "PROOF_AUTHOR_ARTIFACT_AWAITING_INDEPENDENT_REVIEW"
RENDERING_RULE = (
    "The registry alone is never renderable; a downstream consumer must "
    "independently resolve canonical PR-269 completion and a candidate-bound "
    "frozen PASS review receipt."
)
# Updated only after deterministic regeneration. Exact-byte identity is
# appropriate here because this registry is the frozen proof-author evidence
# consumed by later proof-atlas work.
REGISTRY_SHA256 = (
    "0729466278169d9368e5a7a3f23e1e534e348e4ce5888a4ff0a65d57da957d6b"
)
LEGACY_PILLAR_T_IDS = frozenset(
    {
        "SIG-P3",
        "SIG-P4",
        "SIG-P5",
        "SIG-P6",
        "SIG-P7",
        "SIG-P9",
        "SIG-P11",
        "SIG-P12",
        "SIG-P13",
        "SIG-P14",
        "SIG-P15",
        "SIG-P21",
        "SIG-P22",
        "SIG-P27",
        "SIG-P32",
        "SIG-T3-lin",
        "SIG-T3-full",
        "SIG-T3-int",
        "SIG-T9p",
        "SIG-MES-PROV",
        "SIG-U1",
        "SIG-U2",
        "SIG-TSUM",
        "SIG-MES-BR",
        "SIG-BV-DYN",
        "SIG-KE-FRAME",
        "SIG-KE-OBS",
        "SIG-KE-DYN",
        "SIG-OMK-REOPEN",
        "SIG-MES-REFREEZE",
        "SIG-MES-MESB-TRACE",
    }
)
EXPECTED_OBLIGATION_IDS = (
    LEGACY_PILLAR_T_IDS | TF_ANALYTIC_IDS | VT_ANALYTIC_IDS
)


class PillarTCoreProofError(ValueError):
    """Raised when a proof contract or executable witness fails closed."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class RelationToSource(_StringEnum):
    TYPED_ELABORATION_WITH_EXPLICIT_PREMISES = (
        "TYPED_ELABORATION_WITH_EXPLICIT_PREMISES"
    )
    EXACT_REGISTERED_ORACLE_STATEMENT = (
        "EXACT_REGISTERED_ORACLE_STATEMENT"
    )
    EXACT_RESTRICTED_WITNESS_ONLY = "EXACT_RESTRICTED_WITNESS_ONLY"
    EXACT_ANALYTIC_STATEMENT = "EXACT_ANALYTIC_STATEMENT"
    CONDITIONAL_ANALYTIC_SHAPE_ONLY = (
        "CONDITIONAL_ANALYTIC_SHAPE_ONLY"
    )
    EXACT_SOURCE_REFERENCE = "EXACT_SOURCE_REFERENCE"
    SOURCE_SIGNATURE_MISSING = "SOURCE_SIGNATURE_MISSING"


class ProofVerdict(_StringEnum):
    PROVED_ANALYTIC = "PROVED_ANALYTIC"
    PROVED_CONDITIONAL_ANALYTIC = "PROVED_CONDITIONAL_ANALYTIC"
    RESTRICTED_WITNESS_CONFIRMED = "RESTRICTED_WITNESS_CONFIRMED"
    REFERENCE_RESOLVED_NOT_READJUDICATED = (
        "REFERENCE_RESOLVED_NOT_READJUDICATED"
    )
    INCONCLUSIVE_MISSING_SIGNATURE = "INCONCLUSIVE_MISSING_SIGNATURE"
    INCONCLUSIVE = "INCONCLUSIVE"
    FAIL = "FAIL"


def _sha256(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise PillarTCoreProofError(
            f"required proof source is missing or not regular: {path}"
        )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise PillarTCoreProofError(f"{field} must be a mapping")
    return value


def _rows(value: object, field: str) -> tuple[Mapping[str, object], ...]:
    if (
        isinstance(value, (str, bytes))
        or not isinstance(value, Sequence)
        or any(not isinstance(item, Mapping) for item in value)
    ):
        raise PillarTCoreProofError(f"{field} must be a list of mappings")
    return tuple(value)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PillarTCoreProofError(f"{field} must be a non-empty string")
    return value.strip()


def _strings(
    value: object,
    field: str,
    *,
    empty_ok: bool = False,
) -> tuple[str, ...]:
    if (
        isinstance(value, (str, bytes))
        or not isinstance(value, Sequence)
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise PillarTCoreProofError(
            f"{field} must be a list of non-empty strings"
        )
    result = tuple(str(item).strip() for item in value)
    if not empty_ok and not result:
        raise PillarTCoreProofError(f"{field} must be non-empty")
    return result


def _enum(
    value: object,
    enum_type: type[_StringEnum],
    field: str,
) -> _StringEnum:
    text = _text(value, field)
    try:
        return enum_type(text)
    except ValueError as exc:
        raise PillarTCoreProofError(
            f"{field} has unsupported value {text!r}"
        ) from exc


@dataclass(frozen=True)
class SourceIdentity:
    kind: str
    source_id: str
    statement_identity_sha256: str
    evidence_path: str


@dataclass(frozen=True)
class PillarTProofRecord:
    proof_id: str
    obligation_id: str
    source_identity: SourceIdentity
    relation_to_source: RelationToSource
    statement: str
    statement_identity_sha256: str
    assumptions: tuple[str, ...]
    domain: tuple[str, ...]
    frame_convention: str
    branch_convention: str
    proof_method: str
    proof_artifact: str
    executable_evidence: tuple[str, ...]
    counterexample_boundary: tuple[str, ...]
    verdict: ProofVerdict
    claim_ceiling: str

    @property
    def is_new_analytic_candidate(self) -> bool:
        return self.verdict in {
            ProofVerdict.PROVED_ANALYTIC,
            ProofVerdict.PROVED_CONDITIONAL_ANALYTIC,
            ProofVerdict.RESTRICTED_WITNESS_CONFIRMED,
        }

    @property
    def counts_without_review(self) -> bool:
        """A proof-author verdict alone is never a public proof count."""

        return False


@dataclass(frozen=True)
class PillarTCoreRegistry:
    records: tuple[PillarTProofRecord, ...]
    registry_status: str
    claim_ceiling: str
    review_required: bool
    rendering_rule: str

    def record(self, obligation_id: str) -> PillarTProofRecord:
        matches = tuple(
            row for row in self.records if row.obligation_id == obligation_id
        )
        if len(matches) != 1:
            raise PillarTCoreProofError(
                f"expected one PR-269 record for {obligation_id!r}"
            )
        return matches[0]

    def accepted_for_rendering(self) -> bool:
        """Proof-author bytes cannot self-adjudicate an external review."""

        return False

    def reject_raw_proof_count(self, claimed_count: int) -> None:
        raise PillarTCoreProofError(
            f"raw PR-269 registry cardinality {claimed_count} is not an "
            "accepted proof count"
        )


def _parse_source_identity(
    value: object,
    field: str,
) -> SourceIdentity:
    raw = _mapping(value, field)
    if set(raw) != {
        "kind",
        "id",
        "statement_identity_sha256",
        "evidence_path",
    }:
        raise PillarTCoreProofError(
            f"{field} keys must match the source-identity contract"
        )
    digest = _text(
        raw.get("statement_identity_sha256"),
        f"{field}.statement_identity_sha256",
    )
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise PillarTCoreProofError(
            f"{field}.statement_identity_sha256 must be lowercase sha256"
        )
    return SourceIdentity(
        kind=_text(raw.get("kind"), f"{field}.kind"),
        source_id=_text(raw.get("id"), f"{field}.id"),
        statement_identity_sha256=digest,
        evidence_path=_text(
            raw.get("evidence_path"), f"{field}.evidence_path"
        ),
    )


def _parse_record(value: Mapping[str, object]) -> PillarTProofRecord:
    required_keys = {
        "proof_id",
        "obligation_id",
        "source_identity",
        "relation_to_source",
        "statement",
        "statement_identity_sha256",
        "assumptions",
        "domain",
        "frame_convention",
        "branch_convention",
        "proof_method",
        "proof_artifact",
        "executable_evidence",
        "counterexample_boundary",
        "verdict",
        "claim_ceiling",
    }
    if set(value) != required_keys:
        raise PillarTCoreProofError(
            "proof-record keys must match the frozen PR-269 contract"
        )
    obligation_id = _text(value.get("obligation_id"), "obligation_id")
    statement = _text(value.get("statement"), f"{obligation_id}.statement")
    statement_digest = _text(
        value.get("statement_identity_sha256"),
        f"{obligation_id}.statement_identity_sha256",
    )
    if statement_digest != _canonical_sha256(statement):
        raise PillarTCoreProofError(
            f"{obligation_id}: typed statement identity drifted"
        )
    verdict = _enum(
        value.get("verdict"), ProofVerdict, f"{obligation_id}.verdict"
    )
    assert isinstance(verdict, ProofVerdict)
    relation = _enum(
        value.get("relation_to_source"),
        RelationToSource,
        f"{obligation_id}.relation_to_source",
    )
    assert isinstance(relation, RelationToSource)
    assumptions = _strings(
        value.get("assumptions"),
        f"{obligation_id}.assumptions",
        empty_ok=verdict is ProofVerdict.INCONCLUSIVE_MISSING_SIGNATURE,
    )
    domain = _strings(
        value.get("domain"),
        f"{obligation_id}.domain",
        empty_ok=verdict is ProofVerdict.INCONCLUSIVE_MISSING_SIGNATURE,
    )
    claim_ceiling = _text(
        value.get("claim_ceiling"), f"{obligation_id}.claim_ceiling"
    )
    if claim_ceiling != CLAIM_CEILING:
        raise PillarTCoreProofError(
            f"{obligation_id}: claim ceiling exceeds diagnostic_only"
        )
    if (
        verdict is ProofVerdict.INCONCLUSIVE_MISSING_SIGNATURE
        and (
            assumptions
            or domain
            or relation is not RelationToSource.SOURCE_SIGNATURE_MISSING
        )
    ):
        raise PillarTCoreProofError(
            f"{obligation_id}: missing signature acquired typed premises"
        )
    return PillarTProofRecord(
        proof_id=_text(value.get("proof_id"), f"{obligation_id}.proof_id"),
        obligation_id=obligation_id,
        source_identity=_parse_source_identity(
            value.get("source_identity"),
            f"{obligation_id}.source_identity",
        ),
        relation_to_source=relation,
        statement=statement,
        statement_identity_sha256=statement_digest,
        assumptions=assumptions,
        domain=domain,
        frame_convention=_text(
            value.get("frame_convention"),
            f"{obligation_id}.frame_convention",
        ),
        branch_convention=_text(
            value.get("branch_convention"),
            f"{obligation_id}.branch_convention",
        ),
        proof_method=_text(
            value.get("proof_method"), f"{obligation_id}.proof_method"
        ),
        proof_artifact=_text(
            value.get("proof_artifact"), f"{obligation_id}.proof_artifact"
        ),
        executable_evidence=_strings(
            value.get("executable_evidence"),
            f"{obligation_id}.executable_evidence",
        ),
        counterexample_boundary=_strings(
            value.get("counterexample_boundary"),
            f"{obligation_id}.counterexample_boundary",
        ),
        verdict=verdict,
        claim_ceiling=claim_ceiling,
    )


def _validate_repo_reference(
    root: Path,
    reference: str,
    *,
    field: str,
) -> None:
    if "::" in reference:
        relative, fragment = reference.split("::", 1)
    elif "#" in reference:
        relative, fragment = reference.split("#", 1)
    else:
        raise PillarTCoreProofError(
            f"{field} must include a resolvable # or :: fragment"
        )
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise PillarTCoreProofError(f"{field} escapes the repository")
    candidate = root / relative_path
    if candidate.is_symlink() or not candidate.is_file():
        raise PillarTCoreProofError(f"{field} path does not resolve")
    content = candidate.read_text(encoding="utf-8").casefold()
    if not fragment.strip() or fragment.strip().casefold() not in content:
        raise PillarTCoreProofError(f"{field} fragment does not resolve")


def _validate_record_semantics(
    root: Path,
    record: PillarTProofRecord,
) -> None:
    obligation_id = record.obligation_id
    if obligation_id in VT_ANALYTIC_IDS:
        expected_relation = (
            RelationToSource.TYPED_ELABORATION_WITH_EXPLICIT_PREMISES
        )
        expected_verdict = ProofVerdict.PROVED_ANALYTIC
    elif obligation_id in TF_ANALYTIC_IDS:
        expected_relation = {
            "TF-01-PARITY-TYPING": (
                RelationToSource.EXACT_REGISTERED_ORACLE_STATEMENT
            ),
            "TF-02-CATALOGUE-COMPLETION": (
                RelationToSource.EXACT_RESTRICTED_WITNESS_ONLY
            ),
            "TF-07-BUDGET-MORPHOLOGY-SPLIT": (
                RelationToSource.TYPED_ELABORATION_WITH_EXPLICIT_PREMISES
            ),
            "TF-08-PRODUCT-GAUGE-MAX": (
                RelationToSource.EXACT_ANALYTIC_STATEMENT
            ),
            "TF-12-ACCELERATION-EULER-SLAVING": (
                RelationToSource.CONDITIONAL_ANALYTIC_SHAPE_ONLY
            ),
        }[obligation_id]
        expected_verdict = {
            "TF-01-PARITY-TYPING": ProofVerdict.PROVED_ANALYTIC,
            "TF-02-CATALOGUE-COMPLETION": (
                ProofVerdict.RESTRICTED_WITNESS_CONFIRMED
            ),
            "TF-07-BUDGET-MORPHOLOGY-SPLIT": (
                ProofVerdict.PROVED_CONDITIONAL_ANALYTIC
            ),
            "TF-08-PRODUCT-GAUGE-MAX": ProofVerdict.PROVED_ANALYTIC,
            "TF-12-ACCELERATION-EULER-SLAVING": (
                ProofVerdict.PROVED_CONDITIONAL_ANALYTIC
            ),
        }[obligation_id]
    elif obligation_id in REFERENCE_RESOLVED_LEGACY:
        expected_relation = RelationToSource.EXACT_SOURCE_REFERENCE
        expected_verdict = (
            ProofVerdict.REFERENCE_RESOLVED_NOT_READJUDICATED
        )
    else:
        expected_relation = RelationToSource.SOURCE_SIGNATURE_MISSING
        expected_verdict = ProofVerdict.INCONCLUSIVE_MISSING_SIGNATURE
    if record.relation_to_source is not expected_relation:
        raise PillarTCoreProofError(
            f"{obligation_id}: relation-to-source drifted"
        )
    if record.verdict is not expected_verdict:
        raise PillarTCoreProofError(f"{obligation_id}: verdict drifted")
    _validate_repo_reference(
        root,
        record.source_identity.evidence_path,
        field=f"{obligation_id}.source_identity.evidence_path",
    )
    _validate_repo_reference(
        root,
        record.proof_artifact,
        field=f"{obligation_id}.proof_artifact",
    )
    for index, reference in enumerate(record.executable_evidence):
        _validate_repo_reference(
            root,
            reference,
            field=f"{obligation_id}.executable_evidence[{index}]",
        )


def load_pillar_t_core_registry(
    repo_root: Path,
    path: Path | None = None,
) -> PillarTCoreRegistry:
    """Load the PR-269 registry and validate all source and scope guards."""

    root = Path(repo_root).resolve()
    for relative, expected in SOURCE_HASHES.items():
        actual = _sha256(root / relative)
        if actual != expected:
            raise PillarTCoreProofError(
                f"frozen PR-269 input hash drifted for {relative}"
            )
    source = path if path is not None else root / REGISTRY_PATH
    if source.is_symlink() or not source.is_file():
        raise PillarTCoreProofError(
            "proof registry is missing or not a regular file"
        )
    raw = _mapping(
        yaml.safe_load(source.read_text(encoding="utf-8")),
        "pillar_t_core_registry",
    )
    if set(raw) != {
        "schema",
        "authority",
        "registry_status",
        "scientific_status_effect",
        "claim_ceiling",
        "source_hashes",
        "inventory",
        "review_gate",
        "records",
    }:
        raise PillarTCoreProofError(
            "proof-registry keys must match the frozen PR-269 contract"
        )
    if raw.get("schema") != SCHEMA_VERSION:
        raise PillarTCoreProofError("unsupported Pillar-T core schema")
    if raw.get("authority") != "PR-269":
        raise PillarTCoreProofError("Pillar-T core authority drifted")
    if raw.get("scientific_status_effect") != "none":
        raise PillarTCoreProofError(
            "proof registry cannot change observational status"
        )
    if raw.get("claim_ceiling") != CLAIM_CEILING:
        raise PillarTCoreProofError("registry claim ceiling drifted")
    if raw.get("source_hashes") != SOURCE_HASHES:
        raise PillarTCoreProofError("registry source hashes drifted")

    records = tuple(
        _parse_record(row)
        for row in _rows(raw.get("records"), "registry.records")
    )
    proof_ids = {row.proof_id for row in records}
    if len(proof_ids) != len(records):
        raise PillarTCoreProofError("duplicate proof ID")
    obligation_ids = {row.obligation_id for row in records}
    if len(obligation_ids) != len(records):
        raise PillarTCoreProofError("duplicate obligation ID")
    if len(records) != 42 or obligation_ids != EXPECTED_OBLIGATION_IDS:
        raise PillarTCoreProofError(
            "PR-269 obligation membership must be the exact frozen 42"
        )
    for record in records:
        _validate_record_semantics(root, record)

    vt = {row.obligation_id for row in records if row.obligation_id in VT_ANALYTIC_IDS}
    tf = {row.obligation_id for row in records if row.obligation_id in TF_ANALYTIC_IDS}
    legacy = tuple(
        row
        for row in records
        if row.source_identity.kind == "legacy_signature_inventory"
    )
    if vt != VT_ANALYTIC_IDS:
        raise PillarTCoreProofError("VT analytic/core selection drifted")
    if tf != TF_ANALYTIC_IDS:
        raise PillarTCoreProofError("TF analytic/core selection drifted")
    if len(legacy) != 31:
        raise PillarTCoreProofError("legacy Pillar-T inventory is not 31")
    resolved = {
        row.obligation_id
        for row in legacy
        if row.verdict
        is ProofVerdict.REFERENCE_RESOLVED_NOT_READJUDICATED
    }
    if resolved != REFERENCE_RESOLVED_LEGACY:
        raise PillarTCoreProofError(
            "legacy reference-resolved selection drifted"
        )
    missing = tuple(
        row
        for row in legacy
        if row.verdict is ProofVerdict.INCONCLUSIVE_MISSING_SIGNATURE
    )
    if len(missing) != 24:
        raise PillarTCoreProofError(
            "untyped legacy obligations must remain exactly 24"
        )
    inventory = _mapping(raw.get("inventory"), "registry.inventory")
    if inventory != {
        "legacy_pillar_t": 31,
        "tf_analytic_core": 5,
        "vt_analytic_core": 6,
        "raw_record_count_is_public_theorem_count": False,
    }:
        raise PillarTCoreProofError("registry inventory contract drifted")
    review = _mapping(raw.get("review_gate"), "registry.review_gate")
    if review != {
        "required": True,
        "role": "independent_non_author_reviewer",
        "rendering_rule": RENDERING_RULE,
    }:
        raise PillarTCoreProofError("independent review gate drifted")
    registry_status = _text(
        raw.get("registry_status"), "registry.registry_status"
    )
    if registry_status != REGISTRY_STATUS:
        raise PillarTCoreProofError("registry status drifted")
    if _sha256(source) != REGISTRY_SHA256:
        raise PillarTCoreProofError("proof registry exact bytes drifted")
    return PillarTCoreRegistry(
        records=records,
        registry_status=registry_status,
        claim_ceiling=CLAIM_CEILING,
        review_required=True,
        rendering_rule=RENDERING_RULE,
    )


def _array(
    value: object,
    field: str,
    *,
    ndim: int | None = None,
    shape: tuple[int, ...] | None = None,
) -> np.ndarray:
    def contains_bool(item: object) -> bool:
        if isinstance(item, (bool, np.bool_)):
            return True
        if isinstance(item, np.ndarray):
            if item.dtype.kind == "b":
                return True
            if item.dtype.kind == "O":
                return any(contains_bool(entry) for entry in item.flat)
            return False
        if isinstance(item, (tuple, list)):
            return any(contains_bool(entry) for entry in item)
        return False

    if contains_bool(value):
        raise PillarTCoreProofError(f"{field} cannot be boolean")
    try:
        out = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise PillarTCoreProofError(f"{field} must be numeric") from exc
    if ndim is not None and out.ndim != ndim:
        raise PillarTCoreProofError(
            f"{field} must have ndim={ndim}, got {out.ndim}"
        )
    if shape is not None and out.shape != shape:
        raise PillarTCoreProofError(
            f"{field} must have shape {shape}, got {out.shape}"
        )
    if not np.all(np.isfinite(out)):
        raise PillarTCoreProofError(f"{field} must be finite")
    return out


def _positive_vector(value: object, field: str, length: int) -> np.ndarray:
    out = _array(value, field, shape=(length,))
    if np.any(out <= 0.0):
        raise PillarTCoreProofError(f"{field} must be strictly positive")
    return out


@dataclass(frozen=True)
class KinematicNormalization:
    sigma2: float
    w2: float
    sigma_over_theta_frobenius2: float
    omega_over_theta_norm2: float


def convert_kinematic_normalizations(
    sigma_over_theta_stf5: Sequence[object],
    omega_over_theta_axial3: Sequence[object],
) -> KinematicNormalization:
    """Evaluate the convention-exact VT-T1 conversion.

    The STF5 coordinate basis is not orthonormal, so the shear norm is
    evaluated after decoding the full trace-free matrix.
    """

    sigma = stf5_to_matrix(sigma_over_theta_stf5)
    omega = _array(
        omega_over_theta_axial3,
        "omega_over_theta_axial3",
        shape=(3,),
    )
    sigma_norm2 = float(np.einsum("ab,ab->", sigma, sigma))
    omega_norm2 = float(omega @ omega)
    return KinematicNormalization(
        sigma2=1.5 * sigma_norm2,
        w2=3.0 * omega_norm2,
        sigma_over_theta_frobenius2=sigma_norm2,
        omega_over_theta_norm2=omega_norm2,
    )


def weighted_box_gauge(
    value: Sequence[object],
    radii: Sequence[object],
) -> float:
    """Minkowski gauge of ``{|x_i| <= radii_i}``."""

    vector = _array(value, "value", ndim=1)
    if vector.size == 0:
        raise PillarTCoreProofError("value must be non-empty")
    scale = _positive_vector(radii, "radii", len(vector))
    return float(np.max(np.abs(vector) / scale, initial=0.0))


def linear_image_gauge(
    transformed_value: Sequence[object],
    action: object,
    base_gauge: Callable[[np.ndarray], float],
) -> float:
    """Gauge in ``g A`` evaluated by pullback through invertible ``g``."""

    value = _array(transformed_value, "transformed_value", ndim=1)
    matrix = _array(
        action, "action", shape=(len(value), len(value))
    )
    try:
        pulled_back = np.linalg.solve(matrix, value)
    except np.linalg.LinAlgError as exc:
        raise PillarTCoreProofError("action must be invertible") from exc
    if not np.all(np.isfinite(pulled_back)):
        raise PillarTCoreProofError(
            "numerical pullback must remain finite"
        )
    result = base_gauge(pulled_back)
    if isinstance(result, (bool, np.bool_)) or not isinstance(
        result, (int, float, np.integer, np.floating)
    ):
        raise PillarTCoreProofError("base_gauge must return a real scalar")
    out = float(result)
    if not math.isfinite(out) or out < 0.0:
        raise PillarTCoreProofError(
            "base_gauge must return a finite nonnegative value"
        )
    return out


def polar_box_support(
    value: Sequence[object],
    radii: Sequence[object],
) -> float:
    """Support of the absolute polar of a weighted box (VT-T3 witness)."""

    return weighted_box_gauge(value, radii)


def directional_polar_stress(
    value: Sequence[object],
    functional: Sequence[object],
    radii: Sequence[object],
) -> float:
    """Return ``|phi(k)|`` after checking ``phi`` lies in the box polar."""

    vector = _array(value, "value", ndim=1)
    phi = _array(functional, "functional", shape=(len(vector),))
    scale = _positive_vector(radii, "radii", len(vector))
    polar_norm = float(np.sum(scale * np.abs(phi)))
    tolerance = 64.0 * np.finfo(float).eps * max(1.0, polar_norm)
    if polar_norm > 1.0 + tolerance:
        raise PillarTCoreProofError(
            "functional lies outside the registered polar body"
        )
    return abs(float(phi @ vector))


@dataclass(frozen=True)
class ParityTransformResult:
    determinant: int
    polar_polar_before: float
    polar_polar_after: float
    axial_axial_before: float
    axial_axial_after: float
    polar_axial_before: float
    polar_axial_after: float


def evaluate_polar_axial_parity(
    polar: Sequence[object],
    axial: Sequence[object],
    action: object,
) -> ParityTransformResult:
    """Evaluate the exact VT-T9 polar/axial contraction laws."""

    v = _array(polar, "polar", shape=(3,))
    w = _array(axial, "axial", shape=(3,))
    matrix = _array(action, "action", shape=(3, 3))
    tolerance = 128.0 * np.finfo(float).eps * max(
        1.0, float(np.linalg.norm(matrix, ord=2))
    )
    if not np.allclose(
        matrix.T @ matrix, np.eye(3), atol=tolerance, rtol=0.0
    ):
        raise PillarTCoreProofError("action must be orthogonal")
    determinant_value = float(np.linalg.det(matrix))
    if not math.isclose(
        abs(determinant_value), 1.0, abs_tol=tolerance, rel_tol=0.0
    ):
        raise PillarTCoreProofError("orthogonal determinant must be +/-1")
    determinant = 1 if determinant_value > 0.0 else -1
    v_after = matrix @ v
    w_after = determinant * matrix @ w
    return ParityTransformResult(
        determinant=determinant,
        polar_polar_before=float(v @ v),
        polar_polar_after=float(v_after @ v_after),
        axial_axial_before=float(w @ w),
        axial_axial_after=float(w_after @ w_after),
        polar_axial_before=float(v @ w),
        polar_axial_after=float(v_after @ w_after),
    )


@dataclass(frozen=True)
class AmplitudeOrbitFactorization:
    amplitude: float
    normalized_shape: tuple[float, ...]
    normalized_gauge: float


def factor_weighted_box_amplitude(
    value: Sequence[object],
    radii: Sequence[object],
) -> AmplitudeOrbitFactorization:
    """Construct the unique positive-gauge factorization used by VT-T10."""

    vector = _array(value, "value", ndim=1)
    amplitude = weighted_box_gauge(vector, radii)
    if amplitude <= 0.0:
        raise PillarTCoreProofError(
            "nonzero positive-gauge state is required"
        )
    normalized = vector / amplitude
    return AmplitudeOrbitFactorization(
        amplitude=amplitude,
        normalized_shape=tuple(float(item) for item in normalized),
        normalized_gauge=weighted_box_gauge(normalized, radii),
    )


def product_ball_gauge(
    sectors: Sequence[Sequence[object]],
    radii: Sequence[object],
) -> float:
    """Gauge of a Cartesian product of positive-radius Euclidean balls."""

    if (
        isinstance(sectors, (str, bytes))
        or not isinstance(sectors, Sequence)
        or len(sectors) == 0
    ):
        raise PillarTCoreProofError("sectors must be a non-empty sequence")
    scale = _positive_vector(radii, "radii", len(sectors))
    saturations = []
    for index, sector in enumerate(sectors):
        vector = _array(sector, f"sectors[{index}]", ndim=1)
        saturations.append(float(np.linalg.norm(vector)) / scale[index])
    return max(saturations)


def factorized_budget_directional_derivative(
    invariant_jacobian: object,
    outer_gradient: Sequence[object],
    tangent: Sequence[object],
) -> float:
    """Chain-rule derivative for a budget factored through named invariants."""

    jacobian = _array(invariant_jacobian, "invariant_jacobian", ndim=2)
    gradient = _array(
        outer_gradient,
        "outer_gradient",
        shape=(jacobian.shape[0],),
    )
    direction = _array(
        tangent, "tangent", shape=(jacobian.shape[1],)
    )
    return float(gradient @ (jacobian @ direction))


@dataclass(frozen=True)
class EulerSlavingShape:
    units_convention: UnitsConvention
    acceleration_normalization: AccelerationNormalization
    theta: float
    c_numeric_in_source_velocity_units: float
    normalized_acceleration_coefficient: float
    conditional_a2_shape_value: float
    eps_g: float
    numerical_ceiling_authorized: bool = False


def euler_slaving_shape(
    *,
    mu: float,
    w: float,
    sound_speed_squared: float,
    eps_g: float,
    theta: float,
    units_convention: UnitsConvention | str,
    acceleration_normalization: AccelerationNormalization | str,
    c_numeric_in_source_velocity_units: float | None = None,
) -> EulerSlavingShape:
    """Evaluate the conditional TF-12 shape with no MES ceiling authority."""

    values = {
        "mu": mu,
        "w": w,
        "sound_speed_squared": sound_speed_squared,
        "eps_g": eps_g,
        "theta": theta,
    }
    for name, value in values.items():
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value, (int, float, np.integer, np.floating)
        ):
            raise PillarTCoreProofError(f"{name} must be a real scalar")
        if not math.isfinite(float(value)):
            raise PillarTCoreProofError(f"{name} must be finite")
    if float(mu) <= 0.0:
        raise PillarTCoreProofError("mu must be strictly positive")
    denominator = 1.0 + float(w)
    if denominator == 0.0:
        raise PillarTCoreProofError("1 + w must be nonzero")
    if float(eps_g) < 0.0:
        raise PillarTCoreProofError("eps_g must be nonnegative")
    if float(theta) == 0.0:
        raise PillarTCoreProofError("theta must be nonzero")
    try:
        units = UnitsConvention(units_convention)
    except (TypeError, ValueError) as exc:
        raise PillarTCoreProofError(
            "units_convention is not registered"
        ) from exc
    try:
        normalization = AccelerationNormalization(
            acceleration_normalization
        )
    except (TypeError, ValueError) as exc:
        raise PillarTCoreProofError(
            "acceleration_normalization is not registered"
        ) from exc
    expected = (
        AccelerationNormalization.A_OVER_C_THETA
        if units is UnitsConvention.EXPLICIT_C_THETA_NORMALIZED
        else AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
    )
    if normalization is not expected:
        raise PillarTCoreProofError(
            "acceleration normalization does not match units convention"
        )
    if units is UnitsConvention.EXPLICIT_C_THETA_NORMALIZED:
        c_value = c_numeric_in_source_velocity_units
        if isinstance(c_value, (bool, np.bool_)) or not isinstance(
            c_value, (int, float, np.integer, np.floating)
        ):
            raise PillarTCoreProofError(
                "explicit-c branch requires a real numerical c"
            )
        c_numeric = float(c_value)
        if not math.isfinite(c_numeric) or c_numeric <= 0.0:
            raise PillarTCoreProofError(
                "explicit-c branch requires a finite strictly positive c"
            )
    else:
        if c_numeric_in_source_velocity_units is None:
            c_numeric = 1.0
        elif (
            isinstance(c_numeric_in_source_velocity_units, (bool, np.bool_))
            or not isinstance(
                c_numeric_in_source_velocity_units,
                (int, float, np.integer, np.floating),
            )
            or not math.isfinite(
                float(c_numeric_in_source_velocity_units)
            )
            or float(c_numeric_in_source_velocity_units) != 1.0
        ):
            raise PillarTCoreProofError(
                "c=1 branch permits only an omitted c or exact numerical 1"
            )
        else:
            c_numeric = 1.0
    coefficient = (
        -float(sound_speed_squared) / (c_numeric * denominator)
    )
    shape = 1.5 * coefficient * coefficient * float(eps_g) ** 2
    return EulerSlavingShape(
        units_convention=units,
        acceleration_normalization=normalization,
        theta=float(theta),
        c_numeric_in_source_velocity_units=c_numeric,
        normalized_acceleration_coefficient=coefficient,
        conditional_a2_shape_value=shape,
        eps_g=float(eps_g),
    )


__all__ = [
    "AmplitudeOrbitFactorization",
    "EulerSlavingShape",
    "KinematicNormalization",
    "ParityTransformResult",
    "PillarTCoreProofError",
    "PillarTCoreRegistry",
    "PillarTProofRecord",
    "ProofVerdict",
    "RelationToSource",
    "SourceIdentity",
    "convert_kinematic_normalizations",
    "directional_polar_stress",
    "euler_slaving_shape",
    "evaluate_polar_axial_parity",
    "factor_weighted_box_amplitude",
    "factorized_budget_directional_derivative",
    "linear_image_gauge",
    "load_pillar_t_core_registry",
    "polar_box_support",
    "product_ball_gauge",
    "weighted_box_gauge",
]
