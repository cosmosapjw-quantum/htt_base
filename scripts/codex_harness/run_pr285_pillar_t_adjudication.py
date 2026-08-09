#!/usr/bin/env python3
"""Build and validate the complete PR-285 Pillar-T adjudication receipt.

The receipt is an overlay on frozen PR-269/PR-270 evidence.  It does not edit
the historical theorem registry or reinterpret a restricted proof as a proof
of a broader source statement.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
from importlib import metadata as importlib_metadata
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any, Iterable

import yaml


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (ROOT, ROOT / "htt/src", ROOT / "htt")
SPEC_PATH = "docs/research_program/post_pr275/pr285_spec.yaml"
POLICY_PATH = "docs/research_program/post_pr275/pr285_publication_policy.json"
SIGNATURES_PATH = "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml"
PROGRAM_PATH = "docs/research_program/vector_tensor/VECTOR_TENSOR_PROOF_PROGRAM_V1.yaml"
PR269_SPEC_PATH = "docs/research_program/vector_tensor/pr269_spec.yaml"
PR270_SPEC_PATH = "docs/research_program/vector_tensor/pr270_spec.yaml"
T_CORE_PATH = "docs/research_program/vector_tensor/proofs/PILLAR_T_CORE_PROOFS_V1.yaml"
S_CORE_PATH = "docs/research_program/vector_tensor/proofs/PILLAR_S_CORE_PROOFS_V1.yaml"
CAS_PROOFS_PATH = "docs/research_program/vector_tensor/proofs/PILLAR_T_CAS_PROOFS_V1.yaml"
CAS_CONTRACT_PATH = "docs/research_program/vector_tensor/cas/CAS_CONTRACT.json"
CAS_RUN_SPEC_PATH = "docs/research_program/vector_tensor/cas/CAS_RUN_SPEC.json"
CAS_ADJUDICATION_PATH = "docs/research_program/vector_tensor/cas/CAS_ADJUDICATION.json"
PR190_SPEC_PATH = "docs/research_program/strengthening/pr190_spec.yaml"
PR190_RECEIPT_PATH = "docs/generated/pr190_attainability/attainability_report.json"
RUNNER_PATH = "scripts/codex_harness/run_pr285_pillar_t_adjudication.py"
TEST_PATH = "tests/contracts/test_pillar_t_complete_adjudication.py"
OUTPUT_PATH = (
    "docs/research_program/post_pr275/pillar_t_adjudication/"
    "PILLAR_T_COMPLETE_ADJUDICATION_V1.json"
)
OUTPUT = ROOT / OUTPUT_PATH

SOURCE_BINDING_PATHS = (
    SPEC_PATH,
    POLICY_PATH,
    SIGNATURES_PATH,
    PROGRAM_PATH,
    PR269_SPEC_PATH,
    PR270_SPEC_PATH,
    T_CORE_PATH,
    S_CORE_PATH,
    CAS_PROOFS_PATH,
    CAS_CONTRACT_PATH,
    CAS_RUN_SPEC_PATH,
    CAS_ADJUDICATION_PATH,
    PR190_SPEC_PATH,
    PR190_RECEIPT_PATH,
    RUNNER_PATH,
    TEST_PATH,
)

TERMINAL_VERDICTS = {
    "PASS",
    "FAIL",
    "INCONCLUSIVE_WITH_RECEIPT",
    "BLOCKED_WITH_RECEIPT",
}
REQUIRED_AXES = ["wolfram_xact", "sympy", "sage_singular", "lean"]
CAS_COVERED_ROWS = ["VT-T5", "VT-T6", "VT-T7", "VT-T8", "VT-T13"]
VT_PASS = {
    "VT-T1",
    "VT-T2",
    "VT-T3",
    "VT-T4",
    "VT-T5",
    "VT-T6",
    "VT-T7",
    "VT-T9",
    "VT-T10",
    "VT-T11",
    "VT-T12",
}
VT_INCONCLUSIVE = {"VT-T8", "VT-T13"}
VT_BLOCKED = {"VT-T14"}
MUTATION_KILL_MARKERS = {
    "MU285-DROP-SOURCE-ROW": "LEGACY_INVENTORY_MISMATCH",
    "MU285-DROP-VT-ROW": "VT_INVENTORY_MISMATCH",
    "MU285-BARE-NOT-ADJUDICATED": "TERMINAL_VOCABULARY_INVALID",
    "MU285-WEAKEN-STATEMENT": "STATEMENT_IDENTITY_DRIFT",
    "MU285-CAS-AXIS-OMITTED": "CAS_REQUIRED_AXES_MISMATCH",
    "MU285-CAS-MAJORITY-VOTE": "CAS_AGGREGATE_INVALID",
    "MU285-CAS-CONTRACT-DRIFT": "CAS_CONTRACT_DRIFT",
    "MU285-T8-GLOBAL-PROMOTION": "VT_T8_SCOPE_PROMOTION",
    "MU285-T13-FULL-DYNAMICS-PROMOTION": "VT_T13_SCOPE_PROMOTION",
    "MU285-T14-NATIVE-PROMOTION": "VT_T14_NATIVE_PROMOTION",
    "MU285-PR190-REFUTATION-LAUNDERED": "PR190_REFUTATION_LAUNDERED",
    "MU285-CLAIM-CEILING-PROMOTION": "CLAIM_FIREWALL_DRIFT",
}


class PillarTAdjudicationError(ValueError):
    """Fail-closed PR-285 contract violation."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file() or path.is_symlink():
        raise PillarTAdjudicationError(f"SOURCE_BINDING_NOT_REGULAR:{relative}")
    return _sha256_bytes(path.read_bytes())


def _json_identity(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value))


def _validate_output_destination_for_write() -> None:
    if ROOT.is_symlink() or not ROOT.is_dir():
        raise PillarTAdjudicationError("REPOSITORY_ROOT_NOT_REGULAR")
    try:
        relative = OUTPUT.relative_to(ROOT)
    except ValueError as exc:
        raise PillarTAdjudicationError("OUTPUT_ESCAPES_REPOSITORY_ROOT") from exc
    cursor = ROOT
    for part in relative.parent.parts:
        cursor /= part
        if cursor.is_symlink() or not cursor.is_dir():
            raise PillarTAdjudicationError(
                f"OUTPUT_PARENT_NOT_REGULAR:{cursor}"
            )
    if OUTPUT.is_symlink():
        raise PillarTAdjudicationError("OUTPUT_DESTINATION_SYMLINK")
    if OUTPUT.exists() and (
        not OUTPUT.is_file() or OUTPUT.stat().st_nlink != 1
    ):
        raise PillarTAdjudicationError("OUTPUT_DESTINATION_NOT_SINGLE_LINK_FILE")


def _atomic_write(payload: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=OUTPUT.parent,
        prefix=f".{OUTPUT.name}.",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, OUTPUT)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _tracked_paths() -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise PillarTAdjudicationError("TRACKED_FILE_INVENTORY_FAILED")
    return tuple(
        item.decode("utf-8")
        for item in completed.stdout.split(b"\0")
        if item
    )


def _manifest(root: Path, paths: tuple[str, ...]) -> dict[str, Any]:
    identities: dict[str, str] = {}
    for relative in paths:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise PillarTAdjudicationError(
                f"TRACKED_MANIFEST_MEMBER_NOT_REGULAR:{relative}"
            )
        identities[relative] = _sha256_bytes(path.read_bytes())
    encoded = _canonical_json(identities)
    return {
        "file_count": len(identities),
        "manifest_sha256": _sha256_bytes(encoded),
        "path_inventory_sha256": _sha256_bytes(
            "\0".join(identities).encode("utf-8")
        ),
        "content_identity_inventory_sha256": _sha256_bytes(
            "\0".join(identities.values()).encode("ascii")
        ),
    }


def _versions() -> dict[str, str]:
    values = {"python": sys.version.split()[0]}
    for distribution in ("PyYAML", "pytest"):
        try:
            values[distribution] = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError:
            values[distribution] = "UNAVAILABLE"
    return values


def _load_yaml(relative: str) -> dict[str, Any]:
    value = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PillarTAdjudicationError(f"SOURCE_NOT_OBJECT:{relative}")
    return value


def _load_json(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PillarTAdjudicationError(f"SOURCE_NOT_OBJECT:{relative}")
    return value


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return list(value)
    return [deepcopy(value)]


def _deduplicated_strings(values: Iterable[Any]) -> list[str]:
    output: list[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in output:
            output.append(value)
    return output


def _record_evidence(record: dict[str, Any], fallback: str) -> list[str]:
    return _deduplicated_strings(
        [
            record.get("proof_artifact"),
            *_as_list(record.get("executable_evidence")),
            *_as_list(record.get("evidence_refs")),
            fallback,
        ]
    )


def _source_bindings() -> tuple[list[dict[str, str]], dict[str, str]]:
    bindings = [
        {"path": relative, "sha256": _sha256_file(relative)}
        for relative in SOURCE_BINDING_PATHS
    ]
    return bindings, {item["path"]: item["sha256"] for item in bindings}


def _legacy_rows() -> list[dict[str, Any]]:
    signatures = _load_yaml(SIGNATURES_PATH)
    group = signatures["source_groups"]["legacy_signature_inventory"]
    entries = group["entries"]
    if not isinstance(entries, list) or len(entries) != 65:
        raise PillarTAdjudicationError("LEGACY_SOURCE_REGISTRY_INVALID")
    t_records = {
        item["obligation_id"]: item
        for item in _load_yaml(T_CORE_PATH)["records"]
        if str(item.get("obligation_id", "")).startswith("SIG-")
    }
    s_records = {
        item["obligation_id"]: item
        for item in _load_yaml(S_CORE_PATH)["records"]
        if str(item.get("obligation_id", "")).startswith("SIG-")
    }
    proof_records = {**t_records, **s_records}
    source_ids = [item["entry_id"] for item in entries]
    if set(source_ids) != set(proof_records) or len(proof_records) != 65:
        raise PillarTAdjudicationError("LEGACY_PROOF_COVERAGE_INVALID")

    rows: list[dict[str, Any]] = []
    for source in entries:
        row_id = source["entry_id"]
        proof = proof_records[row_id]
        relation = str(proof.get("relation_to_source", "UNSPECIFIED"))
        proof_statement = proof.get("statement")
        if not isinstance(proof_statement, str) or not proof_statement:
            proof_statement = source["statement"]
        domains = _as_list(proof.get("domain", proof.get("domains")))
        boundaries = _as_list(
            proof.get("counterexample_boundary", proof.get("counterexample_boundaries"))
        )
        proof_verdict = str(proof.get("verdict", "INCONCLUSIVE_MISSING_SIGNATURE"))
        if proof_verdict == "INCONCLUSIVE_MISSING_SIGNATURE":
            reason = (
                "The frozen source supplies a title but no typed premises or domain; "
                "inventing a stronger signature is forbidden."
            )
        else:
            reason = (
                "The referenced evidence is preserved, but the source row remains "
                "title-only and was explicitly not readjudicated under typed premises."
            )
        rows.append(
            {
                "row_id": row_id,
                "source_group": "legacy_signature_inventory",
                "source_partition": source["source_partition"],
                "source_statement": source["statement"],
                "source_statement_identity_sha256": source[
                    "statement_identity_sha256"
                ],
                "source_record_sha256": source["source_record_sha256"],
                "adjudicated_statement": proof_statement,
                "statement_relation": relation,
                "premises": _as_list(proof.get("assumptions")),
                "premise_status": "SOURCE_NOT_TYPED",
                "domains": domains,
                "domain_status": "SOURCE_NOT_TYPED",
                "frame_convention": proof.get("frame_convention"),
                "branch_convention": proof.get("branch_convention"),
                "proof_evidence": _record_evidence(
                    proof, f"{SIGNATURES_PATH}#{row_id}"
                ),
                "proof_record_verdict": proof_verdict,
                "counterexample_boundary": boundaries,
                "verdict": "INCONCLUSIVE_WITH_RECEIPT",
                "verdict_reason": reason,
                "claim_ceiling": "diagnostic_only",
            }
        )
    return rows


def _vt_program_rows() -> list[dict[str, Any]]:
    program = _load_yaml(PROGRAM_PATH)
    rows = program["theorems"]["pillar_T"]
    if not isinstance(rows, list):
        raise PillarTAdjudicationError("VT_PROGRAM_INVALID")
    return rows


def _vector_tensor_rows() -> list[dict[str, Any]]:
    program_rows = _vt_program_rows()
    if [item.get("id") for item in program_rows] != [f"VT-T{i}" for i in range(1, 15)]:
        raise PillarTAdjudicationError("VT_SOURCE_REGISTRY_INVALID")
    all_typed = {
        **_load_yaml(PR269_SPEC_PATH)["typed_statements"],
        **_load_yaml(PR270_SPEC_PATH)["typed_statements"],
    }
    typed = {
        key: value for key, value in all_typed.items() if key.startswith("VT-T")
    }
    core_records = {
        item["obligation_id"]: item
        for item in _load_yaml(T_CORE_PATH)["records"]
        if str(item.get("obligation_id", "")).startswith("VT-T")
    }
    cas_records = {
        item["obligation_id"]: item
        for item in _load_yaml(CAS_PROOFS_PATH)["records"]
    }
    proofs = {**core_records, **cas_records}
    expected = {f"VT-T{i}" for i in range(1, 15)}
    if set(typed) != expected or set(proofs) != expected:
        raise PillarTAdjudicationError("VT_TYPED_PROOF_COVERAGE_INVALID")

    rows: list[dict[str, Any]] = []
    for source in program_rows:
        row_id = source["id"]
        statement = typed[row_id]
        proof = proofs[row_id]
        relation = statement["relation_to_source"]
        if row_id in VT_PASS:
            verdict = "PASS"
            reason = (
                "The exact typed statement passes under its declared premises and "
                "domain; no broader source or scientific claim is granted."
            )
        elif row_id == "VT-T8":
            verdict = "INCONCLUSIVE_WITH_RECEIPT"
            reason = (
                "The generic local-chart proof passes, but global orbit separation "
                "and invariant-ring completeness are explicitly withheld."
            )
        elif row_id == "VT-T13":
            verdict = "INCONCLUSIVE_WITH_RECEIPT"
            reason = (
                "The exact chain-rule core passes, but no typed full evolution law "
                "binds the requested covariant source decomposition."
            )
        else:
            verdict = "BLOCKED_WITH_RECEIPT"
            reason = (
                "The required admitted native geometry payload and morphology atlas "
                "do not exist in the pre-solver repository."
            )
        domain = statement.get("domain", proof.get("domains"))
        boundaries = statement.get(
            "counterexample_boundary",
            proof.get("counterexample_boundaries", []),
        )
        source_identity = _json_identity(
            {
                "id": row_id,
                "title": source["title"],
                "status": source["status"],
                "proof_mode": source["proof_mode"],
            }
        )
        row = {
            "row_id": row_id,
            "source_group": "vector_tensor_successor",
            "source_statement": source["title"],
            "source_statement_identity_sha256": source_identity,
            "source_program_status": source["status"],
            "proof_mode": source["proof_mode"],
            "adjudicated_statement": statement["statement"],
            "statement_relation": relation,
            "premises": _as_list(statement.get("assumptions", proof.get("assumptions"))),
            "premise_status": "TYPED_AND_FROZEN",
            "domains": _as_list(domain),
            "domain_status": "TYPED_AND_FROZEN",
            "proof_evidence": _record_evidence(
                proof,
                f"{PR269_SPEC_PATH if row_id in core_records else PR270_SPEC_PATH}#{row_id}",
            ),
            "proof_record_verdict": proof["verdict"],
            "counterexample_boundary": _as_list(boundaries),
            "verdict": verdict,
            "verdict_reason": reason,
            "claim_ceiling": "diagnostic_only",
        }
        if "forbidden_extension" in statement:
            row["withheld_extension"] = statement["forbidden_extension"]
        if "withheld_source_extension" in statement:
            row["withheld_extension"] = statement["withheld_source_extension"]
        if "verdict_boundary" in statement:
            row["withheld_extension"] = statement["verdict_boundary"]
        if row_id in CAS_COVERED_ROWS:
            row["cas_evidence_scope"] = {
                "contract": CAS_CONTRACT_PATH,
                "aggregate": CAS_ADJUDICATION_PATH,
                "effect": "EXACT_REGISTERED_ALGEBRAIC_CORE_ONLY",
            }
        rows.append(row)
    return rows


def _failed_candidate_row() -> dict[str, Any]:
    spec = _load_yaml(PR190_SPEC_PATH)
    receipt = _load_json(PR190_RECEIPT_PATH)
    claim = spec["claim_identity"]
    if (
        receipt.get("terminal") != "COMPLETED_FAILED_WITH_RECEIPT"
        or receipt.get("success_dependency_satisfied") is not False
    ):
        raise PillarTAdjudicationError("PR190_SOURCE_TERMINAL_DRIFT")
    refuted = receipt["result"]["refuted_stages"]
    if not isinstance(refuted, list) or not refuted:
        raise PillarTAdjudicationError("PR190_COUNTEREXAMPLE_MISSING")
    return {
        "row_id": claim["claim_id"],
        "source_group": "failed_candidate",
        "source_statement": claim["statement"],
        "source_statement_identity_sha256": _json_identity(
            {"claim_id": claim["claim_id"], "statement": claim["statement"]}
        ),
        "adjudicated_statement": claim["statement"],
        "statement_relation": "EXACT_REGISTERED_FAILED_CANDIDATE",
        "premises": [
            "one declared frame and convention applies to every target",
            "lower endpoint, upper endpoint, and every interior value must all be admissible Einstein-matter solutions",
            "algebraic, constraint, local-dynamical, and global-dynamical sharpness are conjunctive",
        ],
        "premise_status": "TYPED_AND_FROZEN",
        "domains": [
            "registered open-branch comparator interval [11/100, 17/100]",
            "admissible Einstein-matter solutions in the registered homogeneous congruence",
        ],
        "domain_status": "TYPED_AND_FROZEN",
        "proof_evidence": [
            PR190_SPEC_PATH,
            PR190_RECEIPT_PATH,
            receipt["cas_evidence"]["adjudication"],
        ],
        "counterexample_boundary": deepcopy(refuted),
        "terminal_source_status": receipt["terminal"],
        "success_dependency_satisfied": False,
        "verdict": "FAIL",
        "verdict_reason": (
            "The registered full conjunctive statement is refuted at the constraint "
            "level by exact same-frame Frobenius contradictions; no weaker statement "
            "is substituted."
        ),
        "claim_ceiling": "diagnostic_only",
    }


def _cas_evidence() -> dict[str, Any]:
    contract = _load_json(CAS_CONTRACT_PATH)
    adjudication = _load_json(CAS_ADJUDICATION_PATH)
    contract_sha = _sha256_file(CAS_CONTRACT_PATH)
    if adjudication.get("contract_sha256") != contract_sha:
        raise PillarTAdjudicationError("CAS_CONTRACT_DRIFT")
    return {
        "contract_id": contract["identity"]["contract_id"],
        "contract_sha256": contract_sha,
        "aggregate_path": CAS_ADJUDICATION_PATH,
        "aggregate_sha256": _sha256_file(CAS_ADJUDICATION_PATH),
        "aggregate_status": adjudication["aggregate_status"],
        "required_axes": deepcopy(adjudication["required_axes"]),
        "axis_statuses": deepcopy(adjudication["axis_statuses"]),
        "covered_rows": deepcopy(CAS_COVERED_ROWS),
        "majority_vote_forbidden": True,
        "verification_state": adjudication["verification_state"],
        "claim_promotion_effect": "CAS_COMPONENT_ONLY_NO_SCIENTIFIC_PROMOTION",
        "current_reexecution_policy": (
            "all required axes PASS permits an exact replay; any required platform "
            "block yields CAS_BLOCKED_WITH_RECEIPT and never a majority-vote pass"
        ),
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    legacy = [item for item in rows if item["source_group"] == "legacy_signature_inventory"]
    vector = [item for item in rows if item["source_group"] == "vector_tensor_successor"]
    failed = [item for item in rows if item["source_group"] == "failed_candidate"]
    counts = Counter(item["verdict"] for item in rows)
    return {
        "source_rows": len(legacy),
        "source_partition_counts": dict(
            sorted(Counter(item["source_partition"] for item in legacy).items())
        ),
        "vector_tensor_rows": len(vector),
        "failed_candidate_rows": len(failed),
        "terminal_counts": {
            "PASS": counts["PASS"],
            "FAIL": counts["FAIL"],
            "INCONCLUSIVE_WITH_RECEIPT": counts["INCONCLUSIVE_WITH_RECEIPT"],
            "BLOCKED_WITH_RECEIPT": counts["BLOCKED_WITH_RECEIPT"],
        },
        "bare_not_adjudicated_count": sum(
            item["verdict"] == "NOT_ADJUDICATED" for item in rows
        ),
    }


def receipt_content_sha256(payload: dict[str, Any]) -> str:
    value = deepcopy(payload)
    value.pop("receipt_content_sha256", None)
    return _json_identity(value)


def _expected_mutation_registry() -> list[dict[str, Any]]:
    registry = _load_yaml(SPEC_PATH)["mutation_registry"]
    if not isinstance(registry, list) or not registry:
        raise PillarTAdjudicationError("MUTATION_REGISTRY_INVALID")
    return deepcopy(registry)


def _base_payload() -> dict[str, Any]:
    bindings, binding_map = _source_bindings()
    rows = [*_legacy_rows(), *_vector_tensor_rows(), _failed_candidate_row()]
    payload = {
        "schema": "htt.pr285.pillar_t_complete_adjudication_receipt.v1",
        "pr_id": "PR-285",
        "change_set_id": "CS-PR285-PILLAR-T-ADJUDICATION",
        "publication_group_id": "PG-PR285-PILLAR-T-ADJUDICATION",
        "terminal": "PASS_COMPLETE_PILLAR_T_ADJUDICATION",
        "success_dependency_satisfied": True,
        "scientific_status_effect": "ROW_LEVEL_TERMINAL_DISPOSITION_ONLY",
        "metadata": {
            "owner": "COMMON",
            "scope": "pre-solver complete row-level theorem disposition",
            "claim_tier": "diagnostic_only",
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
            "transfer_source": "none",
            "observed_data_executed": False,
            "public_use": False,
            "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
            "generation_identity": {
                "mode": "external_candidate_seal_required",
                "source_binding_set_sha256": _json_identity(bindings),
                "git_commit": None,
                "worktree_state": "external_seal_bound",
            },
            "generating_command": (
                "python3 -B scripts/codex_harness/"
                "run_pr285_pillar_t_adjudication.py build"
            ),
            "assumptions": [
                "frozen source titles do not imply typed premises or domains",
                "PR-269 and PR-270 proof artifacts remain immutable evidence",
                "CAS evidence applies only to the registered algebraic core",
                "process success means terminal coverage rather than universal proof",
            ],
            "caveats": [
                "65 legacy rows remain inconclusive because their source signatures are title-only",
                "VT-T8 and VT-T13 retain restricted or partial proof scopes",
                "VT-T14 remains blocked before admitted native geometry and atlas evidence",
                "the PR-190 full comparator-attainability candidate remains refuted",
                "no observed sky, native low-ell solver, or family-identification result is produced",
            ],
        },
        "source_bindings": bindings,
        "source_binding_map": binding_map,
        "cas_evidence": _cas_evidence(),
        "rows": rows,
        "summary": _summary(rows),
        "mutation_registry": _expected_mutation_registry(),
        "mutation_results": [],
    }
    return payload


def _row_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["row_id"]: item for item in payload["rows"]}


def apply_registered_mutation(
    payload: dict[str, Any], mutation_id: str
) -> dict[str, Any]:
    rows = payload["rows"]
    if mutation_id == "MU285-DROP-SOURCE-ROW":
        index = next(i for i, item in enumerate(rows) if item["source_group"] == "legacy_signature_inventory")
        rows.pop(index)
    elif mutation_id == "MU285-DROP-VT-ROW":
        index = next(i for i, item in enumerate(rows) if item["source_group"] == "vector_tensor_successor")
        rows.pop(index)
    elif mutation_id == "MU285-BARE-NOT-ADJUDICATED":
        rows[0]["verdict"] = "NOT_ADJUDICATED"
    elif mutation_id == "MU285-WEAKEN-STATEMENT":
        rows[0]["source_statement"] += " after weakening"
    elif mutation_id == "MU285-CAS-AXIS-OMITTED":
        payload["cas_evidence"]["required_axes"].pop()
        payload["cas_evidence"]["axis_statuses"].pop("lean", None)
    elif mutation_id == "MU285-CAS-MAJORITY-VOTE":
        payload["cas_evidence"]["axis_statuses"]["lean"] = "FAIL"
        payload["cas_evidence"]["aggregate_status"] = "CAS_4AXIS_PASS"
    elif mutation_id == "MU285-CAS-CONTRACT-DRIFT":
        payload["cas_evidence"]["contract_sha256"] = "0" * 64
    elif mutation_id == "MU285-T8-GLOBAL-PROMOTION":
        _row_map(payload)["VT-T8"]["verdict"] = "PASS"
    elif mutation_id == "MU285-T13-FULL-DYNAMICS-PROMOTION":
        _row_map(payload)["VT-T13"]["verdict"] = "PASS"
    elif mutation_id == "MU285-T14-NATIVE-PROMOTION":
        _row_map(payload)["VT-T14"]["verdict"] = "PASS"
    elif mutation_id == "MU285-PR190-REFUTATION-LAUNDERED":
        _row_map(payload)["C-PR190-FULL-COMPARATOR-ATTAINABILITY"]["verdict"] = (
            "INCONCLUSIVE_WITH_RECEIPT"
        )
    elif mutation_id == "MU285-CLAIM-CEILING-PROMOTION":
        payload["metadata"]["claim_tier"] = "native_validated"
        payload["metadata"]["public_use"] = True
    else:
        raise PillarTAdjudicationError(f"UNKNOWN_MUTATION:{mutation_id}")
    return payload


def _validate_claim_firewall(payload: dict[str, Any]) -> None:
    metadata = payload.get("metadata")
    expected = {
        "claim_tier": "diagnostic_only",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "transfer_source": "none",
        "observed_data_executed": False,
        "public_use": False,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    }
    if not isinstance(metadata, dict) or any(metadata.get(k) != v for k, v in expected.items()):
        raise PillarTAdjudicationError("CLAIM_FIREWALL_DRIFT")


def _validate_core(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise PillarTAdjudicationError("RECEIPT_NOT_OBJECT")
    _validate_claim_firewall(payload)
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise PillarTAdjudicationError("ROWS_NOT_LIST")

    expected_legacy = _legacy_rows()
    expected_vt = _vector_tensor_rows()
    expected_pr190 = _failed_candidate_row()
    legacy = [item for item in rows if item.get("source_group") == "legacy_signature_inventory"]
    vt = [item for item in rows if item.get("source_group") == "vector_tensor_successor"]
    failed = [item for item in rows if item.get("source_group") == "failed_candidate"]
    if [item.get("row_id") for item in legacy] != [item["row_id"] for item in expected_legacy]:
        raise PillarTAdjudicationError("LEGACY_INVENTORY_MISMATCH")
    if [item.get("row_id") for item in vt] != [item["row_id"] for item in expected_vt]:
        raise PillarTAdjudicationError("VT_INVENTORY_MISMATCH")
    if len(failed) != 1 or failed[0].get("row_id") != expected_pr190["row_id"]:
        raise PillarTAdjudicationError("PR190_RECEIPT_MISSING")
    if len(rows) != 80:
        raise PillarTAdjudicationError("TOTAL_RECEIPT_COUNT_MISMATCH")
    if any(item.get("verdict") not in TERMINAL_VERDICTS for item in rows):
        raise PillarTAdjudicationError("TERMINAL_VOCABULARY_INVALID")

    for actual, expected in zip(legacy, expected_legacy, strict=True):
        if (
            actual.get("source_statement") != expected["source_statement"]
            or actual.get("source_statement_identity_sha256")
            != expected["source_statement_identity_sha256"]
        ):
            raise PillarTAdjudicationError("STATEMENT_IDENTITY_DRIFT")
        if actual.get("verdict") != "INCONCLUSIVE_WITH_RECEIPT":
            raise PillarTAdjudicationError("LEGACY_TITLE_ONLY_PROMOTION")
        if actual.get("premise_status") != "SOURCE_NOT_TYPED" or actual.get("domain_status") != "SOURCE_NOT_TYPED":
            raise PillarTAdjudicationError("LEGACY_PREMISE_DOMAIN_LAUNDERING")

    for actual, expected in zip(vt, expected_vt, strict=True):
        if (
            actual.get("source_statement") != expected["source_statement"]
            or actual.get("source_statement_identity_sha256")
            != expected["source_statement_identity_sha256"]
            or actual.get("adjudicated_statement") != expected["adjudicated_statement"]
            or actual.get("statement_relation") != expected["statement_relation"]
        ):
            raise PillarTAdjudicationError("STATEMENT_IDENTITY_DRIFT")
        row_id = actual["row_id"]
        if row_id in VT_PASS and actual.get("verdict") != "PASS":
            raise PillarTAdjudicationError("VT_PASS_DISPOSITION_DRIFT")
        if row_id == "VT-T8" and actual.get("verdict") != "INCONCLUSIVE_WITH_RECEIPT":
            raise PillarTAdjudicationError("VT_T8_SCOPE_PROMOTION")
        if row_id == "VT-T13" and actual.get("verdict") != "INCONCLUSIVE_WITH_RECEIPT":
            raise PillarTAdjudicationError("VT_T13_SCOPE_PROMOTION")
        if row_id == "VT-T14" and actual.get("verdict") != "BLOCKED_WITH_RECEIPT":
            raise PillarTAdjudicationError("VT_T14_NATIVE_PROMOTION")

    pr190 = failed[0]
    if (
        pr190.get("source_statement") != expected_pr190["source_statement"]
        or pr190.get("source_statement_identity_sha256")
        != expected_pr190["source_statement_identity_sha256"]
    ):
        raise PillarTAdjudicationError("STATEMENT_IDENTITY_DRIFT")
    if (
        pr190.get("verdict") != "FAIL"
        or pr190.get("terminal_source_status") != "COMPLETED_FAILED_WITH_RECEIPT"
        or pr190.get("success_dependency_satisfied") is not False
    ):
        raise PillarTAdjudicationError("PR190_REFUTATION_LAUNDERED")

    cas = payload.get("cas_evidence")
    if not isinstance(cas, dict):
        raise PillarTAdjudicationError("CAS_EVIDENCE_MISSING")
    if cas.get("required_axes") != REQUIRED_AXES or set(cas.get("axis_statuses", {})) != set(REQUIRED_AXES):
        raise PillarTAdjudicationError("CAS_REQUIRED_AXES_MISMATCH")
    if cas.get("contract_sha256") != _sha256_file(CAS_CONTRACT_PATH):
        raise PillarTAdjudicationError("CAS_CONTRACT_DRIFT")
    if cas.get("covered_rows") != CAS_COVERED_ROWS or cas.get("majority_vote_forbidden") is not True:
        raise PillarTAdjudicationError("CAS_SCOPE_DRIFT")
    axis_statuses = cas["axis_statuses"]
    if cas.get("aggregate_status") == "CAS_4AXIS_PASS" and any(
        axis_statuses.get(axis) != "PASS" for axis in REQUIRED_AXES
    ):
        raise PillarTAdjudicationError("CAS_AGGREGATE_INVALID")
    tracked_cas = _load_json(CAS_ADJUDICATION_PATH)
    if (
        cas.get("aggregate_status") != tracked_cas.get("aggregate_status")
        or axis_statuses != tracked_cas.get("axis_statuses")
    ):
        raise PillarTAdjudicationError("CAS_AGGREGATE_INVALID")

    expected_bindings, expected_map = _source_bindings()
    if payload.get("source_bindings") != expected_bindings or payload.get("source_binding_map") != expected_map:
        raise PillarTAdjudicationError("SOURCE_BINDING_DRIFT")
    if payload.get("summary") != _summary(rows):
        raise PillarTAdjudicationError("SUMMARY_DRIFT")
    if payload.get("terminal") != "PASS_COMPLETE_PILLAR_T_ADJUDICATION" or payload.get("success_dependency_satisfied") is not True:
        raise PillarTAdjudicationError("PROCESS_TERMINAL_DRIFT")


def validate_complete_adjudication_receipt(payload: dict[str, Any]) -> None:
    _validate_core(payload)
    expected_registry = _expected_mutation_registry()
    if payload.get("mutation_registry") != expected_registry:
        raise PillarTAdjudicationError("MUTATION_REGISTRY_DRIFT")
    expected_ids = [item["mutation_id"] for item in expected_registry]
    results = payload.get("mutation_results")
    if not isinstance(results, list) or [item.get("mutation_id") for item in results] != expected_ids:
        raise PillarTAdjudicationError("MUTATION_RESULTS_INCOMPLETE")
    for item in results:
        mutation_id = item.get("mutation_id")
        if (
            item.get("executed") is not True
            or item.get("activated") is not True
            or item.get("killed") is not True
            or item.get("survivor") is not False
            or item.get("kill_marker") != MUTATION_KILL_MARKERS.get(mutation_id)
        ):
            raise PillarTAdjudicationError("MUTATION_RESULT_INVALID")
    if payload.get("receipt_content_sha256") != receipt_content_sha256(payload):
        raise PillarTAdjudicationError("RECEIPT_CONTENT_ADDRESS_DRIFT")


def _run_registered_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in payload["mutation_registry"]:
        mutation_id = item["mutation_id"]
        mutated = apply_registered_mutation(deepcopy(payload), mutation_id)
        killed = False
        marker = ""
        try:
            _validate_core(mutated)
        except PillarTAdjudicationError as exc:
            killed = True
            marker = str(exc)
        if marker != MUTATION_KILL_MARKERS[mutation_id]:
            raise PillarTAdjudicationError(
                f"MUTATION_UNEXPECTED_KILL_MARKER:{mutation_id}:{marker}"
            )
        results.append(
            {
                "mutation_id": mutation_id,
                "executed": True,
                "activated": True,
                "killed": killed,
                "survivor": not killed,
                "kill_marker": marker,
            }
        )
    if any(not item["killed"] for item in results):
        survivors = [item["mutation_id"] for item in results if not item["killed"]]
        raise PillarTAdjudicationError(
            "MUTATION_SURVIVED:" + ",".join(survivors)
        )
    return results


def build_complete_adjudication_receipt() -> dict[str, Any]:
    payload = _base_payload()
    _validate_core(payload)
    payload["mutation_results"] = _run_registered_mutations(payload)
    payload["receipt_content_sha256"] = receipt_content_sha256(payload)
    validate_complete_adjudication_receipt(payload)
    return payload


def _serialized(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _activate_source_layout() -> None:
    resolved = [str(path) for path in SOURCE_PATHS]
    sys.path[:] = resolved + [item for item in sys.path if item not in resolved]
    existing = [
        item
        for item in os.environ.get("PYTHONPATH", "").split(os.pathsep)
        if item and item not in resolved
    ]
    os.environ["PYTHONPATH"] = os.pathsep.join((*resolved, *existing))


def _pytest(paths: tuple[str, ...]) -> int:
    _activate_source_layout()
    import pytest

    return int(
        pytest.main(
            ["-p", "no:cacheprovider", "-q", *(str(ROOT / item) for item in paths)]
        )
    )


def _adjacent() -> int:
    # The historical CAS suite contains one parametrized node that requires a
    # live Wolfram licence.  Static contract tests and all three currently
    # available executable axes remain mandatory; the unavailable Wolfram
    # node is accounted for by the separate typed ``cas`` terminal command.
    _activate_source_layout()
    import pytest

    non_cas = int(
        pytest.main(
            [
                "-p",
                "no:cacheprovider",
                "-q",
                str(ROOT / "tests/contracts/test_pillar_t_core.py"),
                str(ROOT / "tests/contracts/test_pillar_s_core.py"),
                str(ROOT / "tests/contracts/test_theorem_signatures_v3.py"),
                str(ROOT / "tests/pr_cards/test_pr_190_strengthen.py"),
            ]
        )
    )
    if non_cas != 0:
        return non_cas
    cas_without_live_axes = int(
        pytest.main(
            [
                "-p",
                "no:cacheprovider",
                "-q",
                str(ROOT / "tests/contracts/test_pillar_t_cas.py"),
                "-k",
                "not test_executable_axis_payloads_match_one_contract",
            ]
        )
    )
    if cas_without_live_axes != 0:
        return cas_without_live_axes
    live_available_axes = [
        "sympy-argv1",
        "sage_singular-argv2",
        "lean-argv3",
    ]
    return int(
        pytest.main(
            [
                "-p",
                "no:cacheprovider",
                "-q",
                *[
                    str(ROOT / "tests/contracts/test_pillar_t_cas.py")
                    + "::test_executable_axis_payloads_match_one_contract["
                    + node
                    + "]"
                    for node in live_available_axes
                ],
            ]
        )
    )


def _build() -> int:
    try:
        _validate_output_destination_for_write()
    except PillarTAdjudicationError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    payload = build_complete_adjudication_receipt()
    _atomic_write(_serialized(payload))
    print(
        json.dumps(
            {
                "ok": True,
                "output": OUTPUT_PATH,
                "receipt_content_sha256": payload["receipt_content_sha256"],
                "rows": len(payload["rows"]),
            },
            sort_keys=True,
        )
    )
    return 0


def _check() -> int:
    expected = _serialized(build_complete_adjudication_receipt())
    if (
        not OUTPUT.is_file()
        or OUTPUT.is_symlink()
        or OUTPUT.stat().st_nlink != 1
    ):
        sys.stderr.write("tracked PR-285 receipt missing or not regular\n")
        return 1
    actual = OUTPUT.read_bytes()
    if actual != expected:
        sys.stderr.write("tracked PR-285 receipt differs from exact replay\n")
        return 1
    print("ok=true")
    return 0


def _portable() -> int:
    status = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if status.returncode != 0 or status.stdout:
        sys.stderr.write("portable replay requires a clean committed candidate\n")
        return 1
    tracked = _tracked_paths()
    source_before = _manifest(ROOT, tracked)
    archived = subprocess.run(
        ["git", "archive", "--format=tar", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    if archived.returncode != 0:
        sys.stderr.write("git archive failed\n")
        return 1
    with tempfile.TemporaryDirectory(prefix="pr285-portable-") as directory:
        clean_root = Path(directory) / "source"
        clean_root.mkdir()
        with tarfile.open(fileobj=BytesIO(archived.stdout), mode="r:") as archive:
            archive.extractall(clean_root, filter="data")
        clean_before = _manifest(clean_root, tracked)
        if clean_before != source_before:
            sys.stderr.write("clean archive manifest differs from source\n")
            return 1
        env = dict(os.environ)
        scrubbed = (
            "PYTHONHOME",
            "PYTEST_ADDOPTS",
            "PYTEST_PLUGINS",
            "PYTHONSTARTUP",
        )
        for key in (*scrubbed, "PYTHONPATH"):
            env.pop(key, None)
        env["PYTHONPATH"] = os.pathsep.join(
            (str(clean_root), str(clean_root / "htt/src"), str(clean_root / "htt"))
        )
        command = [
            sys.executable,
            "-B",
            "scripts/codex_harness/run_pr285_pillar_t_adjudication.py",
            "check",
        ]
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            cwd=clean_root,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        elapsed = time.perf_counter() - started
        clean_after = _manifest(clean_root, tracked)
        source_after = _manifest(ROOT, tracked)
        if clean_after != clean_before or source_after != source_before:
            sys.stderr.write("portable replay changed tracked bytes\n")
            return 1
        evidence = {
            "schema": "PR285_PORTABLE_CLEAN_REPLAY_EVIDENCE_V1",
            "tracked_source_manifest": source_before,
            "interpreter_and_dependency_versions": _versions(),
            "scrubbed_environment_keys": {
                key: key not in env for key in scrubbed
            }
            | {"PYTHONPATH": "CLEAN_ROOT_ONLY"},
            "exact_command": command,
            "exact_command_exit_code": completed.returncode,
            "exact_command_runtime_seconds": elapsed,
            "nested_stdout_sha256": _sha256_bytes(
                completed.stdout.encode("utf-8")
            ),
            "nested_stderr_sha256": _sha256_bytes(
                completed.stderr.encode("utf-8")
            ),
            "source_root_pre_hash": source_before["manifest_sha256"],
            "source_root_post_hash": source_after["manifest_sha256"],
            "clean_root_pre_hash": clean_before["manifest_sha256"],
            "clean_root_post_hash": clean_after["manifest_sha256"],
            "source_root_differs_from_execution_root": ROOT != clean_root,
        }
        print(json.dumps(evidence, sort_keys=True))
        return completed.returncode


def _cas() -> int:
    preflight = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / ".agent-harness/scripts/cas_gate.py"),
            "preflight",
            "--all",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    statuses: dict[str, str] = {}
    for line in preflight.stdout.splitlines():
        if ": " in line:
            axis, status = line.split(": ", 1)
            statuses[axis] = status
    required = {axis: statuses.get(axis, "MISSING") for axis in REQUIRED_AXES}
    if any(
        status != "PASS" and not status.startswith("BLOCKED_")
        for status in required.values()
    ):
        sys.stderr.write(preflight.stdout + preflight.stderr)
        return 1
    if any(status.startswith("BLOCKED_") for status in required.values()):
        # A tool/license blocker is a registered terminal CAS disposition, not
        # a computation-class exception and not a majority-vote PASS.  The
        # frozen parent-observed CAS_4AXIS_PASS remains separately hash-bound.
        _cas_evidence()
        print(
            json.dumps(
                {
                    "ok": True,
                    "current_aggregate_status": "CAS_BLOCKED",
                    "axis_statuses": required,
                    "historical_aggregate_status": "CAS_4AXIS_PASS",
                    "historical_evidence_path": CAS_ADJUDICATION_PATH,
                    "claim_promotion_cas_eligible_from_current_run": False,
                },
                sort_keys=True,
            )
        )
        return 0
    if preflight.returncode != 0:
        sys.stderr.write(preflight.stdout + preflight.stderr)
        return 1
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROOT / "scripts/codex_harness/run_pr270_pillar_t_cas.py"),
            "adjudication",
        ],
        cwd=ROOT,
        text=True,
        check=False,
    )
    return int(completed.returncode)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=(
            "build",
            "check",
            "focused",
            "adjacent",
            "cas",
            "smoke",
            "portable",
        ),
    )
    args = parser.parse_args(argv)
    if args.mode == "build":
        return _build()
    if args.mode == "check":
        return _check()
    if args.mode == "portable":
        return _portable()
    if args.mode == "focused":
        return _pytest((TEST_PATH,))
    if args.mode == "adjacent":
        return _adjacent()
    if args.mode == "cas":
        return _cas()
    _activate_source_layout()
    import pytest

    return int(pytest.main(["-p", "no:cacheprovider", "-q", "-m", "smoke"]))


if __name__ == "__main__":
    raise SystemExit(main())
