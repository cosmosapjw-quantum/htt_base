#!/usr/bin/env python3
"""Generate the PR-269 analytic/core Pillar-T proof registry.

The registry is an additive proof-author artifact.  It does not rewrite the
PR-268 obligation registry, promote an oracle self-report, or adjudicate the
independent review gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

import yaml


REPO = Path(__file__).resolve().parents[2]
SPEC = Path("docs/research_program/vector_tensor/pr269_spec.yaml")
V3 = Path("docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml")
INTAKE = Path(
    "docs/research_program/vector_tensor/PROGRAM_INTAKE_REGISTRY_V1.yaml"
)
OUTPUT = Path(
    "docs/research_program/vector_tensor/proofs/"
    "PILLAR_T_CORE_PROOFS_V1.yaml"
)
DERIVATION = Path(
    "docs/research_program/vector_tensor/proofs/PR269_PILLAR_T_CORE.md"
)
TEST = Path("tests/contracts/test_pillar_t_core.py")

SCHEMA = "htt.pillar_t_core_proofs.v1"
SPEC_SHA256 = (
    "a196882190bf38e2d62c0c26de61dc6135dd3f4942f58113e93f112c853216d9"
)
V3_SHA256 = (
    "d14b24fda9556545abaf337310471af971c68f01438d32df13349f8cd4308f8b"
)
INTAKE_SHA256 = (
    "b6964771c50c483e7697b087b9f058a3fd7d20ec893475a056608b852fdeb677"
)
SOURCE_HASHES = {
    SPEC: SPEC_SHA256,
    V3: V3_SHA256,
    INTAKE: INTAKE_SHA256,
    Path(
        "docs/research_program/vector_tensor/"
        "vector_tensor_mes_upgrade_blueprint.md"
    ):
        "518d4763baafb1cfd57c0674b354f110e86748849cd8cb0a9e4bc1b6eb2f32fc",
    Path(
        "docs/research_program/"
        "HTT_VECTOR_TENSOR_MES_TWO_PILLAR_UPGRADE_PLAN_20260730.md"
    ):
        "8ac8ddaf6f8d50b2e5c1c628de8749b9e17762e9750755154519e5f7e0dd4944",
    Path("htt/src/common/joint_anisotropy_state.py"):
        "3b3ce3d125ae50103150859541df1300bb19f6b15f82ecf24316d00fb83f0d1c",
    Path("htt/src/common/tensor_functionals.py"):
        "f261a4645dad6dcf7a333f22718de607c8fcb88e289bf251477976be35ba06ac",
    Path("htt/src/common/orbit_catalogue_v3.py"):
        "215746fce9e43407fb3d19750ef6cfcd3258a247b2a4aefc0b22356882400833",
    Path("htt/src/common/tensor_foundations_oracle.py"):
        "ddd819323642f5b86e26ee8cad2c9e0bca9175ab842aa66ac4fc81d0c20eb444",
    Path("htt/src/common/statistical_foundations.py"):
        "8d3706754e41b1b456c12cb0e8b3b446c33ae7f5a78b5902b5e692ce354149aa",
    Path("htt/src/common/w2_convention.py"):
        "39b15209868fe81c8c5f907384820313b90615aa916e0a16f1ad56eb5db8bcac",
}

VT_IDS = ("VT-T1", "VT-T2", "VT-T3", "VT-T4", "VT-T9", "VT-T10")
TF_LINKS = {
    "TF-01-PARITY-TYPING": "I-1.1",
    "TF-02-CATALOGUE-COMPLETION": "I-2.5",
    "TF-07-BUDGET-MORPHOLOGY-SPLIT": "I-3.1",
    "TF-08-PRODUCT-GAUGE-MAX": "II-2.1",
    "TF-12-ACCELERATION-EULER-SLAVING": "I-4.1",
}
REFERENCE_RESOLVED_LEGACY = {
    "SIG-P3",
    "SIG-P11",
    "SIG-MES-PROV",
    "SIG-TSUM",
    "SIG-MES-BR",
    "SIG-MES-REFREEZE",
    "SIG-MES-MESB-TRACE",
}

VT_METHODS = {
    "VT-T1": "index contraction and convention-exact algebra",
    "VT-T2": "Minkowski-gauge definition under an invertible linear action",
    "VT-T3": "finite-dimensional bipolar and support-function duality",
    "VT-T4": "polar membership inequality and supremum ordering",
    "VT-T9": "determinant bookkeeping in the O(3) representation",
    "VT-T10": "positive one-homogeneity and normalization uniqueness",
}
VT_FRAMES = {
    "VT-T1": "DECLARED_SPATIAL_METRIC_AND_CONGRUENCE",
    "VT-T2": "FRAME_FREE_TYPED_LINEAR_ACTION",
    "VT-T3": "FRAME_FREE_DUAL_PAIRING",
    "VT-T4": "FRAME_FREE_DUAL_PAIRING",
    "VT-T9": "ACTIVE_CARTESIAN_O3_ACTION_V1",
    "VT-T10": "REGISTERED_GROUP_ACTION_ON_TYPED_STATE_SPACE",
}
TF_METHODS = {
    "TF-01-PARITY-TYPING": "determinant parity bookkeeping",
    "TF-02-CATALOGUE-COMPLETION": (
        "exact registered witness and finite residual-stabilizer enumeration"
    ),
    "TF-07-BUDGET-MORPHOLOGY-SPLIT": (
        "factorization through named invariants and the chain rule"
    ),
    "TF-08-PRODUCT-GAUGE-MAX": (
        "Cartesian-product membership and Minkowski-gauge definition"
    ),
    "TF-12-ACCELERATION-EULER-SLAVING": (
        "perfect-fluid momentum equation and normalization conversion"
    ),
}
TF_FRAMES = {
    "TF-01-PARITY-TYPING": "ACTIVE_CARTESIAN_O3_ACTION_V1",
    "TF-02-CATALOGUE-COMPLETION": "REGISTERED_SO3_WITNESS_FRAME",
    "TF-07-BUDGET-MORPHOLOGY-SPLIT": (
        "REGISTERED_KINEMATIC_INVARIANT_COORDINATES"
    ),
    "TF-08-PRODUCT-GAUGE-MAX": "FRAME_FREE_PRODUCT_NORMED_SPACE",
    "TF-12-ACCELERATION-EULER-SLAVING": (
        "DECLARED_PERFECT_FLUID_CONGRUENCE"
    ),
}
TF_VERDICTS = {
    "TF-01-PARITY-TYPING": "PROVED_ANALYTIC",
    "TF-02-CATALOGUE-COMPLETION": "RESTRICTED_WITNESS_CONFIRMED",
    "TF-07-BUDGET-MORPHOLOGY-SPLIT": (
        "PROVED_CONDITIONAL_ANALYTIC"
    ),
    "TF-08-PRODUCT-GAUGE-MAX": "PROVED_ANALYTIC",
    "TF-12-ACCELERATION-EULER-SLAVING": (
        "PROVED_CONDITIONAL_ANALYTIC"
    ),
}


class BuildError(ValueError):
    """Raised when a proof registry cannot be generated without drift."""


def _sha256(path: Path) -> str:
    return hashlib.sha256((REPO / path).read_bytes()).hexdigest()


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
        raise BuildError(f"{field} must be a mapping")
    return value


def _rows(value: object, field: str) -> tuple[Mapping[str, object], ...]:
    if (
        isinstance(value, (str, bytes))
        or not isinstance(value, Sequence)
        or any(not isinstance(item, Mapping) for item in value)
    ):
        raise BuildError(f"{field} must be a list of mappings")
    return tuple(value)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BuildError(f"{field} must be a non-empty string")
    return value.strip()


def _strings(value: object, field: str) -> list[str]:
    if isinstance(value, str):
        return [value.strip()]
    if (
        isinstance(value, bytes)
        or not isinstance(value, Sequence)
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise BuildError(f"{field} must be a string or list of strings")
    return [str(item).strip() for item in value]


def _source_map(
    rows: Sequence[Mapping[str, object]],
    id_field: str,
    field: str,
) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for row in rows:
        identifier = _text(row.get(id_field), f"{field}.{id_field}")
        if identifier in result:
            raise BuildError(f"{field} has duplicate id {identifier}")
        result[identifier] = row
    return result


def _proof_record(
    *,
    proof_id: str,
    obligation_id: str,
    source_kind: str,
    source_id: str,
    source_statement_identity_sha256: str,
    source_evidence_path: str,
    relation_to_source: str,
    statement: str,
    assumptions: Sequence[str],
    domain: Sequence[str],
    frame_convention: str,
    branch_convention: str,
    proof_method: str,
    executable_evidence: Sequence[str],
    counterexample_boundary: Sequence[str],
    verdict: str,
) -> dict[str, object]:
    return {
        "proof_id": proof_id,
        "obligation_id": obligation_id,
        "source_identity": {
            "kind": source_kind,
            "id": source_id,
            "statement_identity_sha256": source_statement_identity_sha256,
            "evidence_path": source_evidence_path,
        },
        "relation_to_source": relation_to_source,
        "statement": statement,
        "statement_identity_sha256": _canonical_sha256(statement),
        "assumptions": list(assumptions),
        "domain": list(domain),
        "frame_convention": frame_convention,
        "branch_convention": branch_convention,
        "proof_method": proof_method,
        "proof_artifact": str(DERIVATION) + f"#{proof_id.lower()}",
        "executable_evidence": list(executable_evidence),
        "counterexample_boundary": list(counterexample_boundary),
        "verdict": verdict,
        "claim_ceiling": "diagnostic_only",
    }


def _load_inputs() -> tuple[
    Mapping[str, object],
    Mapping[str, object],
    Mapping[str, object],
]:
    for path, digest in SOURCE_HASHES.items():
        actual = _sha256(path)
        if actual != digest:
            raise BuildError(
                f"frozen input hash drifted for {path}: "
                f"expected {digest}, got {actual}"
            )
    spec = _mapping(
        yaml.safe_load((REPO / SPEC).read_text(encoding="utf-8")),
        "spec",
    )
    v3 = _mapping(
        yaml.safe_load((REPO / V3).read_text(encoding="utf-8")),
        "v3",
    )
    intake = _mapping(
        yaml.safe_load((REPO / INTAKE).read_text(encoding="utf-8")),
        "intake",
    )
    return spec, v3, intake


def _legacy_records(v3: Mapping[str, object]) -> list[dict[str, object]]:
    groups = _mapping(v3.get("source_groups"), "v3.source_groups")
    legacy_group = _mapping(
        groups.get("legacy_signature_inventory"),
        "legacy_signature_inventory",
    )
    legacy = _rows(legacy_group.get("entries"), "legacy entries")
    pillar_t = tuple(row for row in legacy if row.get("source_partition") == "T")
    if len(pillar_t) != 31:
        raise BuildError(f"expected 31 legacy Pillar-T rows, got {len(pillar_t)}")
    ids = {_text(row.get("entry_id"), "legacy.entry_id") for row in pillar_t}
    if not REFERENCE_RESOLVED_LEGACY <= ids:
        missing = sorted(REFERENCE_RESOLVED_LEGACY - ids)
        raise BuildError(f"reference-resolved legacy IDs missing: {missing}")

    records: list[dict[str, object]] = []
    for row in pillar_t:
        obligation_id = _text(row.get("entry_id"), "legacy.entry_id")
        resolved = obligation_id in REFERENCE_RESOLVED_LEGACY
        source_status = _text(
            row.get("source_status"), f"{obligation_id}.source_status"
        )
        if resolved and source_status != "CHECKED":
            raise BuildError(
                f"{obligation_id} cannot resolve a non-CHECKED source"
            )
        if not resolved and source_status != "MIGRATION_PENDING":
            raise BuildError(
                f"{obligation_id} has unexpected source status {source_status}"
            )
        assumptions = (
            _strings(row.get("assumptions"), f"{obligation_id}.assumptions")
            if resolved
            else []
        )
        domains = (
            _strings(row.get("domains"), f"{obligation_id}.domains")
            if resolved
            else []
        )
        frame = (
            _text(
                row.get("frame_convention"),
                f"{obligation_id}.frame_convention",
            )
            if resolved
            else "SOURCE_NOT_TYPED"
        )
        records.append(
            _proof_record(
                proof_id=f"PR269-LEGACY-{obligation_id}",
                obligation_id=obligation_id,
                source_kind="legacy_signature_inventory",
                source_id=obligation_id,
                source_statement_identity_sha256=_text(
                    row.get("statement_identity_sha256"),
                    f"{obligation_id}.statement_identity_sha256",
                ),
                source_evidence_path=_text(
                    row.get("evidence_path"),
                    f"{obligation_id}.evidence_path",
                ),
                relation_to_source=(
                    "EXACT_SOURCE_REFERENCE"
                    if resolved
                    else "SOURCE_SIGNATURE_MISSING"
                ),
                statement=_text(
                    row.get("statement"), f"{obligation_id}.statement"
                ),
                assumptions=assumptions,
                domain=domains,
                frame_convention=frame,
                branch_convention=(
                    "SOURCE_NOT_TYPED"
                    if row.get("branch_convention") is None
                    else _text(
                        row.get("branch_convention"),
                        f"{obligation_id}.branch_convention",
                    )
                ),
                proof_method=(
                    "resolve frozen typed source reference without "
                    "readjudication"
                    if resolved
                    else "fail-closed missing-signature inventory"
                ),
                executable_evidence=(
                    [str(TEST) + "::test_legacy_t_inventory_is_exact"]
                ),
                counterexample_boundary=(
                    [
                        "No new PR-269 proof is asserted; the frozen source "
                        "premises and limitations remain authoritative."
                    ]
                    if resolved
                    else [
                        "No proof is admissible until assumptions, domain, "
                        "frame, branch, and perturbative order are typed."
                    ]
                ),
                verdict=(
                    "REFERENCE_RESOLVED_NOT_READJUDICATED"
                    if resolved
                    else "INCONCLUSIVE_MISSING_SIGNATURE"
                ),
            )
        )
    return records


def _typed_contract(
    spec: Mapping[str, object], obligation_id: str
) -> Mapping[str, object]:
    statements = _mapping(spec.get("typed_statements"), "typed_statements")
    return _mapping(
        statements.get(obligation_id),
        f"typed_statements.{obligation_id}",
    )


def _contract_fields(
    contract: Mapping[str, object],
    obligation_id: str,
) -> tuple[str, list[str], list[str], list[str]]:
    statement = _text(contract.get("statement"), f"{obligation_id}.statement")
    assumptions = _strings(
        contract.get("assumptions"), f"{obligation_id}.assumptions"
    )
    domain = _strings(contract.get("domain"), f"{obligation_id}.domain")
    boundary = _strings(
        contract.get("counterexample_boundary"),
        f"{obligation_id}.counterexample_boundary",
    )
    return statement, assumptions, domain, boundary


def _tf_records(
    spec: Mapping[str, object],
    v3: Mapping[str, object],
) -> list[dict[str, object]]:
    groups = _mapping(v3.get("source_groups"), "v3.source_groups")
    proposal_group = _mapping(
        groups.get("proposal_registry_rows"),
        "proposal_registry_rows",
    )
    proposal = _source_map(
        _rows(proposal_group.get("entries"), "proposal entries"),
        "entry_id",
        "proposal entries",
    )
    oracle = _mapping(v3.get("oracle"), "v3.oracle")
    links = _source_map(
        _rows(oracle.get("statement_links"), "oracle.statement_links"),
        "proposition_id",
        "oracle.statement_links",
    )
    if set(TF_LINKS) - set(links):
        raise BuildError("selected TF proposition is absent from oracle links")

    records: list[dict[str, object]] = []
    for obligation_id, entry_id in TF_LINKS.items():
        link = links[obligation_id]
        if link.get("entry_id") != entry_id or link.get("proof_effect") != "none":
            raise BuildError(f"{obligation_id}: PR-268 oracle link drifted")
        source = proposal[entry_id]
        contract = _typed_contract(spec, obligation_id)
        statement, assumptions, domain, boundary = _contract_fields(
            contract, obligation_id
        )
        records.append(
            _proof_record(
                proof_id=f"PR269-{obligation_id}",
                obligation_id=obligation_id,
                source_kind="proposal_registry_rows",
                source_id=entry_id,
                source_statement_identity_sha256=_text(
                    source.get("statement_identity_sha256"),
                    f"{entry_id}.statement_identity_sha256",
                ),
                source_evidence_path=_text(
                    source.get("evidence_path"), f"{entry_id}.evidence_path"
                ),
                relation_to_source=_text(
                    contract.get("relation_to_source"),
                    f"{obligation_id}.relation_to_source",
                ),
                statement=statement,
                assumptions=assumptions,
                domain=domain,
                frame_convention=TF_FRAMES[obligation_id],
                branch_convention="REAL_FINITE_REGISTERED_BRANCH",
                proof_method=TF_METHODS[obligation_id],
                executable_evidence=[
                    str(TEST) + "::test_tf_analytic_core_boundaries"
                ],
                counterexample_boundary=boundary,
                verdict=TF_VERDICTS[obligation_id],
            )
        )
    return records


def _vt_records(
    spec: Mapping[str, object],
    intake: Mapping[str, object],
) -> list[dict[str, object]]:
    obligations = _mapping(
        intake.get("vt_theorem_obligations"),
        "intake.vt_theorem_obligations",
    )
    source = _source_map(
        _rows(obligations.get("entries"), "vt theorem entries"),
        "id",
        "vt theorem entries",
    )
    records: list[dict[str, object]] = []
    for obligation_id in VT_IDS:
        source_row = source.get(obligation_id)
        if source_row is None:
            raise BuildError(f"missing VT obligation {obligation_id}")
        if source_row.get("registration_status") != "REGISTERED_OBLIGATION":
            raise BuildError(f"{obligation_id} is not registered")
        source_fingerprint = {
            key: source_row.get(key)
            for key in (
                "id",
                "title",
                "proof_class",
                "source_status",
                "proof_mode",
                "registration_status",
                "claim_ceiling",
            )
        }
        contract = _typed_contract(spec, obligation_id)
        statement, assumptions, domain, boundary = _contract_fields(
            contract, obligation_id
        )
        records.append(
            _proof_record(
                proof_id=f"PR269-{obligation_id}",
                obligation_id=obligation_id,
                source_kind="vt_theorem_obligations",
                source_id=obligation_id,
                source_statement_identity_sha256=_canonical_sha256(
                    source_fingerprint
                ),
                source_evidence_path=_text(
                    source_row.get("evidence_path"),
                    f"{obligation_id}.evidence_path",
                ),
                relation_to_source=_text(
                    contract.get("relation_to_source"),
                    f"{obligation_id}.relation_to_source",
                ),
                statement=statement,
                assumptions=assumptions,
                domain=domain,
                frame_convention=VT_FRAMES[obligation_id],
                branch_convention="REAL_FINITE_PRINCIPAL_BRANCH",
                proof_method=VT_METHODS[obligation_id],
                executable_evidence=[
                    str(TEST) + "::test_vt_analytic_core_exact_vectors",
                    str(TEST) + "::test_vt_analytic_core_mutations_refuse",
                ],
                counterexample_boundary=boundary,
                verdict="PROVED_ANALYTIC",
            )
        )
    return records


def build_payload() -> dict[str, object]:
    spec, v3, intake = _load_inputs()
    legacy = _legacy_records(v3)
    tf = _tf_records(spec, v3)
    vt = _vt_records(spec, intake)
    records = [*legacy, *tf, *vt]
    proof_ids = [str(row["proof_id"]) for row in records]
    if len(proof_ids) != len(set(proof_ids)):
        raise BuildError("proof IDs are not unique")
    return {
        "schema": SCHEMA,
        "authority": "PR-269",
        "registry_status": "PROOF_AUTHOR_ARTIFACT_AWAITING_INDEPENDENT_REVIEW",
        "scientific_status_effect": "none",
        "claim_ceiling": "diagnostic_only",
        "source_hashes": {
            str(path): digest
            for path, digest in SOURCE_HASHES.items()
        },
        "inventory": {
            "legacy_pillar_t": len(legacy),
            "tf_analytic_core": len(tf),
            "vt_analytic_core": len(vt),
            "raw_record_count_is_public_theorem_count": False,
        },
        "review_gate": {
            "required": True,
            "role": "independent_non_author_reviewer",
            "rendering_rule": (
                "A record may be rendered as accepted only when canonical "
                "PR-269 status is completed and its frozen independent review "
                "receipt is resolvable."
            ),
        },
        "records": records,
    }


def _render(payload: Mapping[str, object]) -> str:
    return yaml.safe_dump(
        dict(payload),
        sort_keys=False,
        allow_unicode=True,
        width=96,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    rendered = _render(build_payload())
    output = REPO / OUTPUT
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
            raise SystemExit(f"generated registry is stale: {OUTPUT}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
