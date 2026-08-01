#!/usr/bin/env python3
"""Generate the PR-268 theorem-signature v3 registration.

The output is a proof-obligation registry.  It preserves source status and
typed missingness; it does not adjudicate proofs or turn row counts into
theorem counts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

import yaml


REPO = Path(__file__).resolve().parents[2]
OUTPUT = Path(
    "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml"
)
INTAKE = Path(
    "docs/research_program/vector_tensor/PROGRAM_INTAKE_REGISTRY_V1.yaml"
)
SIGNATURES_V2 = Path("docs/research_program/THEOREM_SIGNATURES_V2.yaml")
SIGNATURES_V2_LOADER = Path("htt/src/common/theorem_signatures.py")
TWO_PILLAR = Path(
    "docs/research_program/vector_tensor/proof_registry_two_pillars.yaml"
)
ORACLE_PROPOSAL = Path(
    "docs/research_program/vector_tensor/"
    "tensor_foundations_oracle_proposal.py"
)
ORACLE_PRODUCTION = Path("htt/src/common/tensor_foundations_oracle.py")

SCHEMA = "htt.theorem_signatures.v3"
FROZEN_HASHES = {
    str(SIGNATURES_V2):
        "4e43de815088b372cac82e889fe86b55c815f327af231611336b11ebb8a487d9",
    str(SIGNATURES_V2_LOADER):
        "214edec76e6deb8c2064b7edb5765a683213b552783baebe6be1b902fa0e160e",
    str(INTAKE):
        "b6964771c50c483e7697b087b9f058a3fd7d20ec893475a056608b852fdeb677",
    str(TWO_PILLAR):
        "01e278c2223c7f117b429a3359dbc3d483ce0ef409bbb06140b62a9ca3b2f201",
    str(ORACLE_PROPOSAL):
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
    "U": [
        "typed_cross_pillar_argument",
        "counterexample_boundary",
        "independent_adjudication",
    ],
    "TC": [
        "typed_mathematical_physics_proof_artifact",
        "domain_appropriate_exact_or_cas_evidence",
        "counterexample_boundary",
        "independent_adjudication",
    ],
    "ST": [
        "typed_statistical_proof_artifact",
        "sampling_law_and_covariance_assumptions",
        "finite_sample_or_asymptotic_status",
        "independent_adjudication",
    ],
}


class BuildError(ValueError):
    """Raised when a source cannot be represented without semantic drift."""


def _sha256(path: Path) -> str:
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


def _nonempty(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BuildError(f"{field} must be a non-empty string")
    return value.strip()


def _source_map(
    rows: Sequence[Mapping[str, object]],
    field: str,
) -> dict[str, Mapping[str, object]]:
    result: dict[str, Mapping[str, object]] = {}
    for row in rows:
        entry_id = _nonempty(row.get("id"), f"{field}.id")
        if entry_id in result:
            raise BuildError(f"{field} has duplicate id {entry_id}")
        result[entry_id] = row
    return result


def _component(
    *,
    status: str,
    value: object,
) -> tuple[str, object]:
    if status == "DECLARED":
        if value in (None, "", [], ()):
            raise BuildError("DECLARED component must carry a value")
        return status, value
    if status != "SOURCE_NOT_TYPED":
        raise BuildError(f"unsupported component status {status}")
    if value not in (None, "", [], ()):
        raise BuildError("SOURCE_NOT_TYPED component must stay empty")
    return status, value


def _proof_fields(
    intake_row: Mapping[str, object],
) -> dict[str, object]:
    proof_class = _nonempty(
        intake_row.get("proof_class"),
        f"{intake_row.get('id')}.proof_class",
    )
    if proof_class not in REQUIRED_EVIDENCE:
        raise BuildError(f"unsupported proof class {proof_class}")
    dependencies = intake_row.get("dependencies")
    if (
        isinstance(dependencies, (str, bytes))
        or not isinstance(dependencies, Sequence)
        or not dependencies
    ):
        raise BuildError(
            f"{intake_row.get('id')}.dependencies must be non-empty"
        )
    return {
        "proof_class": proof_class,
        "registry_owner": _nonempty(
            intake_row.get("registry_owner"),
            f"{intake_row.get('id')}.registry_owner",
        ),
        "scientific_owner": _nonempty(
            intake_row.get("scientific_owner"),
            f"{intake_row.get('id')}.scientific_owner",
        ),
        "dependencies": [str(item) for item in dependencies],
        "required_evidence": list(REQUIRED_EVIDENCE[proof_class]),
        "evidence_path": _nonempty(
            intake_row.get("evidence_path"),
            f"{intake_row.get('id')}.evidence_path",
        ),
        "source_status": _nonempty(
            intake_row.get("source_status"),
            f"{intake_row.get('id')}.source_status",
        ),
        "registration_status": "REGISTERED_OBLIGATION",
        "proof_adjudication_status": "NOT_ADJUDICATED",
        "claim_ceiling": "diagnostic_only",
    }


def _legacy_entry(
    intake_row: Mapping[str, object],
    source_row: Mapping[str, object],
) -> dict[str, object]:
    entry_id = _nonempty(intake_row.get("id"), "legacy intake id")
    if _nonempty(source_row.get("id"), f"{entry_id}.source id") != entry_id:
        raise BuildError(f"{entry_id}: v2 source id mismatch")
    title = _nonempty(source_row.get("title"), f"{entry_id}.title")
    if title != _nonempty(intake_row.get("title"), f"{entry_id}.intake title"):
        raise BuildError(f"{entry_id}: intake and v2 titles disagree")
    signature_status = _nonempty(
        source_row.get("signature_status"),
        f"{entry_id}.signature_status",
    )
    signature = source_row.get("signature")
    if signature_status == "CHECKED":
        signature_map = _mapping(signature, f"{entry_id}.signature")
        assumption_status, assumptions = _component(
            status="DECLARED",
            value=list(
                _rows_as_strings(
                    signature_map.get("hypotheses"),
                    f"{entry_id}.hypotheses",
                )
            ),
        )
        domain_status, domains = _component(
            status="DECLARED",
            value=[
                _nonempty(
                    signature_map.get("domain"),
                    f"{entry_id}.domain",
                )
            ],
        )
        frame_status, frame = _component(
            status="DECLARED",
            value=_nonempty(
                signature_map.get("frame"),
                f"{entry_id}.frame",
            ),
        )
        perturbative_order_status = "DECLARED"
        perturbative_order = _nonempty(
            signature_map.get("perturbative_order"),
            f"{entry_id}.perturbative_order",
        )
    elif signature_status == "MIGRATION_PENDING":
        if signature is not None:
            raise BuildError(
                f"{entry_id}: migration-pending v2 row has a signature"
            )
        assumption_status, assumptions = _component(
            status="SOURCE_NOT_TYPED", value=[]
        )
        domain_status, domains = _component(
            status="SOURCE_NOT_TYPED", value=[]
        )
        frame_status, frame = _component(
            status="SOURCE_NOT_TYPED", value=None
        )
        perturbative_order_status = "SOURCE_NOT_TYPED"
        perturbative_order = None
    else:
        raise BuildError(
            f"{entry_id}: unsupported signature status {signature_status}"
        )
    branch_status, branch = _component(
        status="SOURCE_NOT_TYPED", value=None
    )
    identity_payload = {
        "id": entry_id,
        "title": title,
        "signature_status": signature_status,
        "signature": signature,
    }
    result = {
        "entry_id": entry_id,
        "source_group": "legacy_signature_inventory",
        "source_partition": _nonempty(
            intake_row.get("source_partition"),
            f"{entry_id}.source_partition",
        ),
        "statement_status": "TITLE_ONLY",
        "statement": title,
        "statement_identity_sha256": _canonical_sha256(identity_payload),
        "source_record_sha256": _canonical_sha256(source_row),
        "assumption_status": assumption_status,
        "assumptions": assumptions,
        "domain_status": domain_status,
        "domains": domains,
        "frame_status": frame_status,
        "frame_convention": frame,
        "branch_status": branch_status,
        "branch_convention": branch,
        "perturbative_order_status": perturbative_order_status,
        "perturbative_order": perturbative_order,
    }
    result.update(_proof_fields(intake_row))
    return result


def _proposal_entry(
    intake_row: Mapping[str, object],
    source_row: Mapping[str, object],
) -> dict[str, object]:
    entry_id = _nonempty(intake_row.get("id"), "proposal intake id")
    if _nonempty(source_row.get("id"), f"{entry_id}.source id") != entry_id:
        raise BuildError(f"{entry_id}: proposal source id mismatch")
    identity = _canonical_sha256(source_row)
    if identity != _nonempty(
        intake_row.get("statement_identity_sha256"),
        f"{entry_id}.statement_identity_sha256",
    ):
        raise BuildError(f"{entry_id}: PR-260 statement identity drifted")
    raw_statement = source_row.get("statement")
    if isinstance(raw_statement, str) and raw_statement.strip():
        statement_status = "DECLARED"
        statement: str | None = raw_statement.strip()
    elif raw_statement is None:
        statement_status = "SOURCE_NOT_TYPED"
        statement = None
    else:
        raise BuildError(f"{entry_id}: malformed proposal statement")
    result = {
        "entry_id": entry_id,
        "source_group": "proposal_registry_rows",
        "source_partition": _nonempty(
            intake_row.get("source_partition"),
            f"{entry_id}.source_partition",
        ),
        "statement_status": statement_status,
        "statement": statement,
        "statement_identity_sha256": identity,
        "source_record_sha256": identity,
        "assumption_status": "SOURCE_NOT_TYPED",
        "assumptions": [],
        "domain_status": "SOURCE_NOT_TYPED",
        "domains": [],
        "frame_status": "SOURCE_NOT_TYPED",
        "frame_convention": None,
        "branch_status": "SOURCE_NOT_TYPED",
        "branch_convention": None,
        "perturbative_order_status": "SOURCE_NOT_TYPED",
        "perturbative_order": None,
    }
    result.update(_proof_fields(intake_row))
    return result


def _rows_as_strings(value: object, field: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise BuildError(f"{field} must be a list of strings")
    result = tuple(_nonempty(item, f"{field}[]") for item in value)
    if not result:
        raise BuildError(f"{field} must be non-empty")
    return result


def build_payload() -> dict[str, object]:
    for relative, expected in FROZEN_HASHES.items():
        actual = _sha256(REPO / relative)
        if actual != expected:
            raise BuildError(
                f"frozen source drifted: {relative} "
                f"(expected {expected}, got {actual})"
            )
    if _sha256(REPO / ORACLE_PROPOSAL) != _sha256(
        REPO / ORACLE_PRODUCTION
    ):
        raise BuildError(
            "production tensor oracle must be a byte-identical proposal copy"
        )

    intake = _mapping(
        yaml.safe_load((REPO / INTAKE).read_text(encoding="utf-8")),
        "intake",
    )
    v2 = _mapping(
        yaml.safe_load(
            (REPO / SIGNATURES_V2).read_text(encoding="utf-8")
        ),
        "THEOREM_SIGNATURES_V2",
    )
    proposal = _mapping(
        yaml.safe_load((REPO / TWO_PILLAR).read_text(encoding="utf-8")),
        "two-pillar registry",
    )
    legacy_intake = _rows(
        _mapping(
            intake.get("legacy_signature_inventory"),
            "legacy_signature_inventory",
        ).get("entries"),
        "legacy_signature_inventory.entries",
    )
    proposal_intake = _rows(
        _mapping(
            intake.get("proposal_registry_rows"),
            "proposal_registry_rows",
        ).get("entries"),
        "proposal_registry_rows.entries",
    )
    v2_by_id = _source_map(
        _rows(v2.get("entries"), "THEOREM_SIGNATURES_V2.entries"),
        "THEOREM_SIGNATURES_V2",
    )
    proposal_by_id = _source_map(
        _rows(proposal.get("entries"), "two-pillar entries"),
        "two-pillar registry",
    )
    legacy_rows = [
        _legacy_entry(row, v2_by_id[_nonempty(row.get("id"), "legacy id")])
        for row in legacy_intake
    ]
    proposal_rows = [
        _proposal_entry(
            row,
            proposal_by_id[_nonempty(row.get("id"), "proposal id")],
        )
        for row in proposal_intake
    ]
    if len(legacy_rows) != 65 or len(proposal_rows) != 58:
        raise BuildError("v3 source cardinalities must remain exactly 65/58")
    ids = [str(row["entry_id"]) for row in legacy_rows + proposal_rows]
    if len(ids) != len(set(ids)):
        raise BuildError("v3 source groups must be ID-disjoint")

    links = []
    for proposition_id, entry_id in ORACLE_LINKS.items():
        source = proposal_by_id[entry_id]
        links.append(
            {
                "proposition_id": proposition_id,
                "entry_id": entry_id,
                "primary_source_status": _nonempty(
                    source.get("status"), f"{entry_id}.status"
                ),
                "alignment_status": "ALIGNED_FOR_EXECUTABLE_TEST_INTAKE",
                "alignment_scope":
                    "statement/domain/frame/branch/premise contract only",
                "proof_effect": "none",
            }
        )

    return {
        "schema": SCHEMA,
        "status": "REGISTERED",
        "authority": "PR-268",
        "scientific_status_effect": "none",
        "claim_ceiling": "diagnostic_only",
        "proof_adjudication_status": "NOT_ADJUDICATED",
        "counting_rule":
            "registry rows and oracle PASS are not theorem counts",
        "frozen_sources": [
            {"path": path, "sha256": digest}
            for path, digest in FROZEN_HASHES.items()
        ],
        "cardinality_aliases": {
            "requested_pillar_T_65": "legacy_signature_inventory",
            "requested_pillar_S_58": "proposal_registry_rows",
            "semantic_guard":
                "legacy 65 = 31 T + 34 S; "
                "proposal 58 = 30 I + 24 II + 4 BRIDGE",
        },
        "source_groups": {
            "legacy_signature_inventory": {
                "expected_count": 65,
                "source_partition_counts": {"T": 31, "S": 34},
                "entries": legacy_rows,
            },
            "proposal_registry_rows": {
                "expected_count": 58,
                "source_partition_counts": {
                    "I": 30,
                    "II": 24,
                    "BRIDGE": 4,
                },
                "entries": proposal_rows,
            },
        },
        "oracle": {
            "oracle_id": "TENSOR_FOUNDATIONS_ORACLE_V1",
            "source_path": str(ORACLE_PROPOSAL),
            "production_path": str(ORACLE_PRODUCTION),
            "source_sha256": _sha256(REPO / ORACLE_PROPOSAL),
            "production_sha256": _sha256(REPO / ORACLE_PRODUCTION),
            "seed": 20260730,
            "proposition_count": 12,
            "evidence_posture": "EXECUTABLE_TEST_EVIDENCE_ONLY",
            "proof_effect": "none",
            "statement_links": links,
            "stable_vectors": [
                {
                    "id": "TF-STABLE-FULL-20260730",
                    "seed": 20260730,
                    "fast": False,
                    "expected_ok": True,
                },
                {
                    "id": "TF-STABLE-REPEAT-20260730",
                    "seed": 20260730,
                    "fast": False,
                    "expected_relation": "exact_receipt_equality",
                },
            ],
            "supplied_fast_mode_status":
                "REPRODUCED_NON_STABLE_TF11_AT_REGISTERED_SEED",
            "mutation_vectors": [
                {
                    "id": "TF-MUT-ORACLE-ID",
                    "mutation": "replace oracle_id",
                    "expected": "REFUSED",
                },
                {
                    "id": "TF-MUT-SEED",
                    "mutation": "replace registered seed",
                    "expected": "REFUSED",
                },
                {
                    "id": "TF-MUT-MISSING-PROPOSITION",
                    "mutation": "delete one proposition",
                    "expected": "REFUSED",
                },
                {
                    "id": "TF-MUT-PROPOSITION-FAIL",
                    "mutation": "set one proposition ok=false",
                    "expected": "REFUSED",
                },
                {
                    "id": "TF-MUT-UNPROVEN-PROMOTION",
                    "mutation":
                        "promote an unchanged UNPROVEN oracle status",
                    "expected": "REFUSED",
                },
                {
                    "id": "TF-MUT-PREMISE-ERASURE",
                    "mutation": "erase TF-12 premise block",
                    "expected": "REFUSED",
                },
            ],
        },
    }


def render_payload(payload: Mapping[str, object]) -> str:
    return yaml.safe_dump(
        dict(payload),
        sort_keys=False,
        allow_unicode=True,
        width=100,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="refuse when the tracked generated registry is stale",
    )
    args = parser.parse_args()
    rendered = render_payload(build_payload())
    output = REPO / OUTPUT
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
            raise SystemExit("THEOREM_SIGNATURES_V3.yaml is stale")
        print(f"OK: {OUTPUT}")
        return
    output.write_text(rendered, encoding="utf-8")
    print(f"WROTE: {OUTPUT}")


if __name__ == "__main__":
    main()
