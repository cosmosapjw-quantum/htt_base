#!/usr/bin/env python3
"""Generate the PR-271 exact/core Pillar-S proof-author registry."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence

import yaml


REPO = Path(__file__).resolve().parents[2]
SPEC = Path("docs/research_program/vector_tensor/pr271_spec.yaml")
V3 = Path("docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml")
INTAKE = Path(
    "docs/research_program/vector_tensor/PROGRAM_INTAKE_REGISTRY_V1.yaml"
)
OUTPUT = Path(
    "docs/research_program/vector_tensor/proofs/"
    "PILLAR_S_CORE_PROOFS_V1.yaml"
)
DERIVATION = Path(
    "docs/research_program/vector_tensor/proofs/PR271_PILLAR_S_CORE.md"
)
TEST = Path("tests/contracts/test_pillar_s_core.py")
MODULE = Path("htt/src/common/vector_tensor_statistical_foundations.py")
SCHEMA = "htt.pillar_s_core_proofs.v1"
SOURCE_HASHES = {
    SPEC:
        "e145fdcca06078d79b65f8b47c6912983923e6fd33b24fa7caddb9b24214a871",
    V3:
        "d14b24fda9556545abaf337310471af971c68f01438d32df13349f8cd4308f8b",
    INTAKE:
        "b6964771c50c483e7697b087b9f058a3fd7d20ec893475a056608b852fdeb677",
    Path(
        "docs/research_program/vector_tensor/"
        "vector_tensor_mes_upgrade_blueprint.md"
    ):
        "518d4763baafb1cfd57c0674b354f110e86748849cd8cb0a9e4bc1b6eb2f32fc",
    Path(
        "docs/research_program/vector_tensor/"
        "STAT_FOUNDATIONS_TENSOR_UPGRADE_20260730.md"
    ):
        "2b6c091c2d9da0d342c7c7765bac4e9d845fe513ef93eb3b61d7b771aa830fd2",
    Path("htt/src/common/statistical_foundations.py"):
        "8d3706754e41b1b456c12cb0e8b3b446c33ae7f5a78b5902b5e692ce354149aa",
    Path("htt/src/common/conditional_exceedance.py"):
        "a6e912ec1b6ff98c11ad5c6ef513073b9fbb67b725c36a92697bc0d4d120b300",
    Path("htt/src/common/depth_path.py"):
        "41ffe054645c00a36158688b55a0aab390919d3759283b9d5e2f33d69ec8f247",
    Path("htt/src/common/tensor_departure_statistics.py"):
        "8ce951ab652d5dac5896c66c63a8740a001031470e04ea9f28e149795e0a826b",
}
REFERENCE_IDS = {
    "SIG-P18",
    "SIG-T1p",
    "SIG-DL1",
    "SIG-L-T2-EXIST",
    "SIG-T2G",
}
VT_IDS = ("VT-S1", "VT-S2", "VT-S4", "VT-S7", "VT-S8")
TF_LINKS = {
    "TF-09-PARITY-SIGN-EXACTNESS": "II-3.1",
    "TF-11-MASK-PATH-MARTINGALE": "II-3.2",
}
VT_METHODS = {
    "VT-S1": "finite-experiment data processing via partition aggregation",
    "VT-S2": "Minkowski gauges and positive-definite quadratic forms",
    "VT-S4": "strict-tail set inclusion under one typed probability law",
    "VT-S7": "deterministic sample-wise probability pushforward",
    "VT-S8": "bilinearity of covariance on one paired joint law",
}
TF_METHODS = {
    "TF-09-PARITY-SIGN-EXACTNESS": (
        "conditional uniform sign-vector enumeration"
    ),
    "TF-11-MASK-PATH-MARTINGALE": (
        "exact finite-partition conditional-expectation tower"
    ),
}
COUNTEREXAMPLES = {
    "VT-S1": [
        "scalar label is not a deterministic function of the profile",
        "laws do not share one support",
        "a tolerance-only total mass is admitted as a probability law",
        "fixed-precision KL cancellation reverses data-processing order",
        "sufficiency is claimed for an unregistered decision",
    ],
    "VT-S2": [
        "rank-deficient covariance is silently pseudoinverted",
        "coordinate identity or active set is erased",
        "nonpositive threshold is admitted",
        (
            "rounded display q rather than the exact gauge relation "
            "decides acceptance"
        ),
    ],
    "VT-S4": [
        "optimizer output or profile objective is treated as draws",
        "thresholds are not ordered",
        "empirical exactness is relabelled as population coverage",
    ],
    "VT-S7": [
        "functional of means replaces the sample-wise pushforward",
        "ratio of means replaces mean of sample-wise ratios",
        "missing samples are imputed without a declared rule",
    ],
    "VT-S8": [
        "independent marginals are relabelled as paired observations",
        "one ordered cross-covariance block is omitted",
        "cross-block sign convention is reversed",
    ],
    "TF-09-PARITY-SIGN-EXACTNESS": [
        "global sign symmetry is substituted for uniform conditional sign flips",
        "dependent nested rungs are pooled",
        "zero ties are silently assigned a sign",
    ],
    "TF-11-MASK-PATH-MARTINGALE": [
        "support nesting is substituted for partition refinement",
        "different target variables are used at different rungs",
        "a conditional cell has zero probability",
        "finite tower identity is promoted to convergence or optional stopping",
        "known fast-oracle instability is hidden or promoted",
    ],
}


class BuildError(ValueError):
    """Raised when a PR-271 registry cannot be generated without drift."""


def _sha256(path: Path) -> str:
    return hashlib.sha256((REPO / path).read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
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
        raise BuildError(f"{field} must be non-empty text")
    return value.strip()


def _strings(value: object, field: str) -> list[str]:
    if value is None:
        return []
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


def _base_record(
    *,
    obligation_id: str,
    source_group: str,
    source_status: str,
    source_identity: str,
    relation: str,
    estimand: str,
    sampling_law: str,
    covariance: Sequence[str],
    finite_status: str,
    assumptions: Sequence[str],
    domains: Sequence[str],
    method: str,
    grade: str,
    verdict: str,
    evidence_refs: Sequence[str],
    boundaries: Sequence[str],
) -> dict[str, object]:
    return {
        "obligation_id": obligation_id,
        "source_group": source_group,
        "source_status": source_status,
        "source_proof_adjudication_status": "NOT_ADJUDICATED",
        "source_statement_identity_sha256": source_identity,
        "relation_to_source": relation,
        "estimand": estimand,
        "sampling_law": sampling_law,
        "covariance_assumptions": list(covariance),
        "finite_or_asymptotic_status": finite_status,
        "assumptions": list(assumptions),
        "domains": list(domains),
        "proof_method": method,
        "evidence_grade": grade,
        "verdict": verdict,
        "evidence_refs": list(evidence_refs),
        "counterexample_boundaries": list(boundaries),
        "claim_ceiling": "diagnostic_only",
    }


def build_payload() -> dict[str, object]:
    for path, expected in SOURCE_HASHES.items():
        actual = _sha256(path)
        if actual != expected:
            raise BuildError(
                f"frozen source drifted: {path} "
                f"(expected {expected}, got {actual})"
            )
    spec = _mapping(
        yaml.safe_load((REPO / SPEC).read_text(encoding="utf-8")), "spec"
    )
    v3 = _mapping(
        yaml.safe_load((REPO / V3).read_text(encoding="utf-8")), "v3"
    )
    intake = _mapping(
        yaml.safe_load((REPO / INTAKE).read_text(encoding="utf-8")),
        "intake",
    )
    typed = _mapping(spec.get("typed_statements"), "typed_statements")
    source_groups = _mapping(v3.get("source_groups"), "source_groups")
    legacy_group = _mapping(
        source_groups.get("legacy_signature_inventory"), "legacy group"
    )
    legacy_rows = tuple(
        row
        for row in _rows(legacy_group.get("entries"), "legacy entries")
        if row.get("source_partition") == "S"
    )
    if len(legacy_rows) != 34:
        raise BuildError("expected exactly 34 legacy Pillar-S rows")
    records: list[dict[str, object]] = []
    for row in legacy_rows:
        identifier = _text(row.get("entry_id"), "legacy entry_id")
        typed_source = identifier in REFERENCE_IDS
        records.append(
            _base_record(
                obligation_id=identifier,
                source_group="LEGACY_S",
                source_status=_text(row.get("source_status"), "source_status"),
                source_identity=_text(
                    row.get("statement_identity_sha256"),
                    "statement_identity_sha256",
                ),
                relation=(
                    "REFERENCE_RESOLVED_WITH_SCALAR_REDUCTION"
                    if typed_source
                    else "SOURCE_TITLE_ONLY_NO_PREMISE_INVENTION"
                ),
                estimand=(
                    _text(row.get("statement"), "statement")
                    if typed_source
                    else "UNAVAILABLE_UNTYPED_SOURCE"
                ),
                sampling_law=(
                    "SOURCE_TYPED_SCALAR_FOUNDATION"
                    if typed_source
                    else "UNAVAILABLE_UNTYPED_SOURCE"
                ),
                covariance=(
                    ["source-declared scalar assumptions only"]
                    if typed_source
                    else []
                ),
                finite_status=(
                    _text(
                        row.get("perturbative_order")
                        or "SOURCE_TYPED_REFERENCE",
                        "finite status",
                    )
                    if typed_source
                    else "INCONCLUSIVE"
                ),
                assumptions=(
                    _strings(row.get("assumptions"), "assumptions")
                    if typed_source
                    else []
                ),
                domains=(
                    _strings(row.get("domains"), "domains")
                    if typed_source
                    else []
                ),
                method=(
                    "source reference resolution and tensor-to-scalar reduction"
                    if typed_source
                    else "no proof: source signature is not typed"
                ),
                grade="REFERENCE_ONLY" if typed_source else "INCONCLUSIVE",
                verdict=(
                    "REFERENCE_RESOLVED_WITH_SCALAR_REDUCTION"
                    if typed_source
                    else "INCONCLUSIVE_MISSING_SIGNATURE"
                ),
                evidence_refs=[
                    _text(row.get("evidence_path"), "evidence_path"),
                    f"{SPEC}#legacy_pillar_s",
                    str(TEST),
                ],
                boundaries=(
                    [
                        "source CHECKED status is not a PR-271 proof verdict",
                        "tensor reduction does not widen the scalar source domain",
                    ]
                    if typed_source
                    else ["premises or domains cannot be inferred from a title"]
                ),
            )
        )
    vt_rows = _source_map(
        _rows(
            _mapping(
                intake.get("vt_theorem_obligations"),
                "vt_theorem_obligations",
            ).get("entries"),
            "vt entries",
        ),
        "id",
        "vt entries",
    )
    for identifier in VT_IDS:
        source = vt_rows[identifier]
        statement = _mapping(typed.get(identifier), identifier)
        source_identity = _canonical_sha256(source)
        records.append(
            _base_record(
                obligation_id=identifier,
                source_group="VT_S",
                source_status=_text(
                    source.get("source_status"), "source_status"
                ),
                source_identity=source_identity,
                relation=_text(
                    statement.get("relation_to_source"), "relation_to_source"
                ),
                estimand=_text(statement.get("estimand"), "estimand"),
                sampling_law=_text(
                    statement.get("sampling_law"), "sampling_law"
                ),
                covariance=_strings(
                    statement.get("covariance_assumptions"),
                    "covariance_assumptions",
                ),
                finite_status=_text(
                    statement.get("finite_or_asymptotic_status"),
                    "finite_or_asymptotic_status",
                ),
                assumptions=_strings(
                    statement.get("assumptions"), "assumptions"
                ),
                domains=["registered typed finite-dimensional method domain"],
                method=VT_METHODS[identifier],
                grade="EXACT_ANALYTIC",
                verdict="PROVED_ANALYTIC_UNDER_TYPED_PREMISES",
                evidence_refs=[
                    _text(source.get("evidence_path"), "evidence_path"),
                    f"{SPEC}#{identifier}",
                    f"{DERIVATION}#{identifier.lower()}",
                    str(MODULE),
                    str(TEST),
                ],
                boundaries=COUNTEREXAMPLES[identifier],
            )
        )
    proposal_rows = _source_map(
        _rows(
            _mapping(
                source_groups.get("proposal_registry_rows"), "proposal group"
            ).get("entries"),
            "proposal entries",
        ),
        "entry_id",
        "proposal entries",
    )
    oracle = _mapping(v3.get("oracle"), "oracle")
    oracle_links = _source_map(
        _rows(oracle.get("statement_links"), "oracle links"),
        "proposition_id",
        "oracle links",
    )
    for identifier, entry_id in TF_LINKS.items():
        source = proposal_rows[entry_id]
        link = oracle_links[identifier]
        statement = _mapping(typed.get(identifier), identifier)
        if link.get("entry_id") != entry_id:
            raise BuildError(f"{identifier} oracle link drifted")
        is_path = identifier == "TF-11-MASK-PATH-MARTINGALE"
        records.append(
            _base_record(
                obligation_id=identifier,
                source_group="TF_S",
                source_status=_text(
                    source.get("source_status"), "source_status"
                ),
                source_identity=_text(
                    source.get("statement_identity_sha256"),
                    "statement_identity_sha256",
                ),
                relation=_text(
                    statement.get("relation_to_source"), "relation_to_source"
                ),
                estimand=_text(statement.get("estimand"), "estimand"),
                sampling_law=_text(
                    statement.get("sampling_law"), "sampling_law"
                ),
                covariance=_strings(
                    statement.get("covariance_assumptions"),
                    "covariance_assumptions",
                ),
                finite_status=_text(
                    statement.get("finite_or_asymptotic_status"),
                    "finite_or_asymptotic_status",
                ),
                assumptions=_strings(
                    statement.get("assumptions"), "assumptions"
                ),
                domains=[
                    (
                        "one finite registered common-target partition path"
                        if is_path
                        else "finite registered parity-pair experiment"
                    )
                ],
                method=TF_METHODS[identifier],
                grade=(
                    "FINITE_REGISTERED_EXACT"
                    if is_path
                    else "EXACT_ANALYTIC"
                ),
                verdict=(
                    "PROVED_FINITE_REGISTERED_PATH"
                    if is_path
                    else "PROVED_ANALYTIC_UNDER_TYPED_PREMISES"
                ),
                evidence_refs=[
                    _text(source.get("evidence_path"), "evidence_path"),
                    f"{SPEC}#{identifier}",
                    f"{DERIVATION}#{identifier.lower()}",
                    str(MODULE),
                    str(TEST),
                ],
                boundaries=COUNTEREXAMPLES[identifier],
            )
        )
    if len(records) != 41:
        raise BuildError("PR-271 registry must contain 34+5+2 records")
    return {
        "schema": SCHEMA,
        "authority": "PR-271",
        "claim_ceiling": "diagnostic_only",
        "scientific_status_effect": "statistical_method_status_only",
        "source_proof_adjudication_status": "NOT_ADJUDICATED",
        "raw_count_publication": "FORBIDDEN",
        "source_hashes": {
            str(path): expected for path, expected in SOURCE_HASHES.items()
        },
        "selection": {
            "legacy_s_count": 34,
            "legacy_reference_ids": sorted(REFERENCE_IDS),
            "vt_ids": list(VT_IDS),
            "tf_ids": list(TF_LINKS),
        },
        "canonical_records_sha256": _canonical_sha256(records),
        "records": records,
    }


def render(payload: Mapping[str, object]) -> str:
    return yaml.safe_dump(
        dict(payload),
        sort_keys=False,
        allow_unicode=True,
        width=100,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render(build_payload())
    output = REPO / OUTPUT
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
            raise SystemExit("PR-271 proof registry is missing or stale")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
