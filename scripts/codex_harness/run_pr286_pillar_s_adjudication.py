#!/usr/bin/env python3
"""Build and validate the complete PR-286 Pillar-S adjudication receipt.

The receipt preserves the distinction between exact proof, preregistered
synthetic validation, and an unresolved source/program obligation.  It is a
row-level evidence disposition, not a scientific or family-identification
promotion.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
from importlib import metadata as importlib_metadata
from io import BytesIO
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
from typing import Any

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = (ROOT, ROOT / "htt/src", ROOT / "htt")

SPEC_PATH = "docs/research_program/post_pr275/pr286_spec.yaml"
POLICY_PATH = "docs/research_program/post_pr275/pr286_publication_policy.json"
SIGNATURES_PATH = "docs/research_program/vector_tensor/THEOREM_SIGNATURES_V3.yaml"
PROGRAM_PATH = "docs/research_program/vector_tensor/VECTOR_TENSOR_PROOF_PROGRAM_V1.yaml"
PROOF_REGISTRY_PATH = "docs/research_program/vector_tensor/proof_registry_two_pillars.yaml"

PR254_SPEC_PATH = "docs/research_program/premise_anchor/pr254_spec.yaml"
PR254_CONTRACT_PATH = "docs/generated/pr254_anchor_geometry/CAS_CONTRACT_PR254_ANCHOR_GEOMETRY.json"
PR254_ADJUDICATION_PATH = "docs/generated/pr254_anchor_geometry/CAS_ADJUDICATION_PR254_ANCHOR_GEOMETRY.json"
PR254_IMPLEMENTATION_PATH = "htt/src/common/anchor_geometry.py"
PR254_COUNTEREXAMPLE_RUNNER_PATH = "scripts/codex_harness/run_pr254_counterexamples.py"
PR254_COUNTEREXAMPLE_ORACLE_PATH = "docs/generated/pr254_anchor_geometry/counterexample_oracle.json"
PR257_SPEC_PATH = "docs/research_program/premise_anchor/pr257_spec.yaml"
PR257_CONTRACT_PATH = "docs/generated/pr257_lowell_morphology/CAS_CONTRACT_PR257_ORBIT_V2.json"
PR257_ADJUDICATION_PATH = "docs/generated/pr257_lowell_morphology/CAS_ADJUDICATION_PR257_ORBIT_V2.json"
PR257_IMPLEMENTATION_PATH = "htt/src/common/orbit_catalogue_v2.py"

PR271_SPEC_PATH = "docs/research_program/vector_tensor/pr271_spec.yaml"
PR271_CORE_PATH = "docs/research_program/vector_tensor/proofs/PILLAR_S_CORE_PROOFS_V1.yaml"
PR271_DERIVATION_PATH = "docs/research_program/vector_tensor/proofs/PR271_PILLAR_S_CORE.md"
PR271_BUILDER_PATH = "scripts/codex_harness/build_pr271_pillar_s_core.py"
PR271_TEST_PATH = "tests/contracts/test_pillar_s_core.py"

PR272_SPEC_PATH = "docs/research_program/vector_tensor/pr272_spec.yaml"
PR272_VALIDATION_PATH = "docs/research_program/vector_tensor/proofs/PILLAR_S_INFERENCE_VALIDATION_V1.yaml"
PR272_BUILDER_PATH = "scripts/codex_harness/build_pr272_pillar_s_inference.py"
PR272_TEST_PATH = "tests/contracts/test_pillar_s_inference.py"
PR272_IMPLEMENTATION_PATH = "htt/src/common/vector_tensor_statistical_inference.py"
PR272_SBC_PATH = "htt/src/common/sbc_ppc.py"
PR272_COVERAGE_PATH = "htt/src/common/weak_id_coverage.py"

PR273_SPEC_PATH = "docs/research_program/vector_tensor/pr273_spec.yaml"
PR273_PACK_PATH = "docs/research_program/vector_tensor/integration/PR273_DIAGNOSTIC_PACK.json"
PR273_BUILDER_PATH = "scripts/codex_harness/build_pr273_blind_synthetic.py"
PR273_TEST_PATH = "tests/integration/test_vector_tensor_blind_synthetic.py"

RUNNER_PATH = "scripts/codex_harness/run_pr286_pillar_s_adjudication.py"
TEST_PATH = "tests/contracts/test_pillar_s_complete_adjudication.py"
BACKLOG_PATH = "docs/codex_handoff/pr_backlog.yaml"
BACKLOG_MIRROR_PATH = "machine_readable/pr_backlog.yaml"
BACKLOG_JSON_PATH = "docs/codex_handoff/pr_backlog.json"
BACKLOG_JSON_MIRROR_PATH = "machine_readable/pr_backlog.json"
DAG_VALIDATOR_PATH = "scripts/codex_harness/validate_pr_dag.py"
OUTPUT_PATH = (
    "docs/research_program/post_pr275/pillar_s_adjudication/"
    "PILLAR_S_COMPLETE_ADJUDICATION_V1.json"
)
OUTPUT = ROOT / OUTPUT_PATH

SOURCE_BINDING_PATHS = (
    SPEC_PATH,
    POLICY_PATH,
    SIGNATURES_PATH,
    PROGRAM_PATH,
    PROOF_REGISTRY_PATH,
    PR254_SPEC_PATH,
    PR254_CONTRACT_PATH,
    PR254_ADJUDICATION_PATH,
    PR254_IMPLEMENTATION_PATH,
    PR254_COUNTEREXAMPLE_RUNNER_PATH,
    PR254_COUNTEREXAMPLE_ORACLE_PATH,
    PR257_SPEC_PATH,
    PR257_CONTRACT_PATH,
    PR257_ADJUDICATION_PATH,
    PR257_IMPLEMENTATION_PATH,
    PR271_SPEC_PATH,
    PR271_CORE_PATH,
    PR271_DERIVATION_PATH,
    PR271_BUILDER_PATH,
    PR271_TEST_PATH,
    PR272_SPEC_PATH,
    PR272_VALIDATION_PATH,
    PR272_BUILDER_PATH,
    PR272_TEST_PATH,
    PR272_IMPLEMENTATION_PATH,
    PR272_SBC_PATH,
    PR272_COVERAGE_PATH,
    PR273_SPEC_PATH,
    PR273_PACK_PATH,
    PR273_BUILDER_PATH,
    PR273_TEST_PATH,
    RUNNER_PATH,
    TEST_PATH,
)

TERMINAL_VERDICTS = {
    "PASS",
    "FAIL",
    "INCONCLUSIVE_WITH_RECEIPT",
    "BLOCKED_WITH_RECEIPT",
}
SOURCE_PASS_ROWS = {
    "I-2.1",
    "I-2.2",
    "I-2.3",
    "I-2.9",
    "I-5.1",
    "I-5.2",
    "I-5.3",
    "I-5.4",
}
PR257_SOURCE_ROWS = {"I-2.1", "I-2.2", "I-2.3", "I-2.9"}
PR254_SOURCE_ROWS = {"I-5.1", "I-5.2", "I-5.3", "I-5.4"}
VT_EXACT_ROWS = {"VT-S1", "VT-S2", "VT-S4", "VT-S7", "VT-S8"}
VT_SYNTHETIC_ROWS = {
    "VT-S3",
    "VT-S5",
    "VT-S6",
    "VT-S9",
    "VT-S10",
    "VT-S11",
    "VT-S12",
    "VT-S13",
}
VT_BLOCKED_ROWS = {"VT-S14"}

STAT_CONFIG_KEYS = {
    "VT-S3": "max_q",
    "VT-S5": "partial_identification",
    "VT-S6": "random_anchor",
    "VT-S9": "depth_multiplicity",
    "VT-S10": "weak_identification",
    "VT-S11": "composition",
    "VT-S12": "matched_counterpair",
    "VT-S13": "open_set",
    "VT-S14": "depth_local_global",
}
STAT_ESTIMANDS = {
    "VT-S3": "simultaneous finite-family max-Q coverage",
    "VT-S5": "coverage of a bounded partially identified Pi envelope",
    "VT-S6": "coverage of a joint numerator-anchor ratio confidence body",
    "VT-S9": "familywise coverage over one finite nested depth path",
    "VT-S10": "weak-identification response error and abstention status",
    "VT-S11": "rank of one registered orbit-response linear composition",
    "VT-S12": "held-out matched-counterpair morphology rejection power",
    "VT-S13": "finite-library known coverage and unknown-class abstention",
    "VT-S14": "synthetic depth-conditioned local/global selection accuracy",
}
STAT_LAWS = {
    "VT-S3": "independent matched-null calibration and evaluation Gaussian laws",
    "VT-S5": "registered finite width-grid Gaussian boundary experiment",
    "VT-S6": "registered bivariate Gaussian numerator-anchor sampling law",
    "VT-S9": "independent equicorrelated finite depth-path null splits",
    "VT-S10": "registered deterministic response perturbation cells",
    "VT-S11": "registered deterministic principal-stratum linear cell",
    "VT-S12": "registered synthetic matched-counterpair null and alternative laws",
    "VT-S13": "registered finite known-library and unknown-generator laws",
    "VT-S14": "registered synthetic Gaussian depth-covariance local/global laws",
}


class PillarSAdjudicationError(ValueError):
    """Fail-closed PR-286 contract violation."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_identity(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value))


def _validate_output_destination_for_write() -> None:
    if ROOT.is_symlink() or not ROOT.is_dir():
        raise PillarSAdjudicationError("REPOSITORY_ROOT_NOT_REGULAR")
    try:
        relative = OUTPUT.relative_to(ROOT)
    except ValueError as exc:
        raise PillarSAdjudicationError("OUTPUT_ESCAPES_REPOSITORY_ROOT") from exc
    cursor = ROOT
    for part in relative.parent.parts:
        cursor /= part
        if cursor.is_symlink() or not cursor.is_dir():
            raise PillarSAdjudicationError(
                f"OUTPUT_PARENT_NOT_REGULAR:{cursor}"
            )
    if OUTPUT.is_symlink():
        raise PillarSAdjudicationError("OUTPUT_DESTINATION_SYMLINK")
    if OUTPUT.exists() and (
        not OUTPUT.is_file() or OUTPUT.stat().st_nlink != 1
    ):
        raise PillarSAdjudicationError("OUTPUT_DESTINATION_NOT_SINGLE_LINK_FILE")


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
        raise PillarSAdjudicationError("TRACKED_FILE_INVENTORY_FAILED")
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
            raise PillarSAdjudicationError(
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
    for distribution in ("numpy", "scipy", "PyYAML", "pytest"):
        try:
            values[distribution] = importlib_metadata.version(distribution)
        except importlib_metadata.PackageNotFoundError:
            values[distribution] = "UNAVAILABLE"
    return values


def _sha256_file(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file() or path.is_symlink():
        raise PillarSAdjudicationError(f"SOURCE_BINDING_NOT_REGULAR:{relative}")
    return _sha256_bytes(path.read_bytes())


def _load_yaml(relative: str) -> dict[str, Any]:
    value = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PillarSAdjudicationError(f"SOURCE_NOT_OBJECT:{relative}")
    return value


def _load_json(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PillarSAdjudicationError(f"SOURCE_NOT_OBJECT:{relative}")
    return value


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return list(value)
    return [deepcopy(value)]


def _source_bindings() -> tuple[list[dict[str, str]], dict[str, str]]:
    bindings = [
        {"path": relative, "sha256": _sha256_file(relative)}
        for relative in SOURCE_BINDING_PATHS
    ]
    return bindings, {item["path"]: item["sha256"] for item in bindings}


def _source_replay_identity(row: dict[str, Any]) -> str:
    return _json_identity(
        {
            "row_id": row["row_id"],
            "source_group": row["source_group"],
            "source_partition": row.get("source_partition"),
            "proof_class": row.get("proof_class"),
            "source_status": row.get("source_status"),
            "source_statement": row.get("source_statement"),
        }
    )


def _cas_contract_scope() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for key, contract_path, adjudication_path, required_claims in (
        (
            "PR254",
            PR254_CONTRACT_PATH,
            PR254_ADJUDICATION_PATH,
            {
                "PA-THM-GAUGE-SUBLEVEL",
                "PA-THM-PRODUCT-BALL",
                "PA-THM-ONE-WAY-MES",
                "PA-THM-RANK-INVARIANCE",
            },
        ),
        (
            "PR257",
            PR257_CONTRACT_PATH,
            PR257_ADJUDICATION_PATH,
            {
                "PR257-O3-SCALAR-PSEUDOSCALAR",
                "PR257-TRACEFREE-CAYLEY-HAMILTON",
                "PR257-KRYLOV-GRAM-SYZYGY",
                "PR257-NONGENERIC-NONSEPARATION",
            },
        ),
    ):
        contract = _load_json(contract_path)
        adjudication = _load_json(adjudication_path)
        claim_ids = set(contract.get("identity", {}).get("claim_ids", []))
        declared_source_hashes = contract.get("identity", {}).get(
            "source_input_hashes"
        )
        contract_sha = _sha256_file(contract_path)
        if (
            not required_claims <= claim_ids
            or not isinstance(declared_source_hashes, list)
            or not declared_source_hashes
        ):
            raise PillarSAdjudicationError(f"{key}_CAS_CLAIM_SCOPE_INVALID")
        replayed_source_hashes: list[dict[str, str]] = []
        for source in declared_source_hashes:
            if not isinstance(source, dict) or set(source) != {"path", "sha256"}:
                raise PillarSAdjudicationError(f"{key}_CAS_SOURCE_BINDING_INVALID")
            actual = _sha256_file(source["path"])
            if actual != source["sha256"]:
                raise PillarSAdjudicationError(f"{key}_CAS_SOURCE_BINDING_INVALID")
            replayed_source_hashes.append(deepcopy(source))
        if (
            adjudication.get("contract_sha256") != contract_sha
            or adjudication.get("aggregate_status") != "CAS_4AXIS_PASS"
            or adjudication.get("required_axes")
            != ["wolfram_xact", "sympy", "sage_singular", "lean"]
            or any(
                adjudication.get("axis_statuses", {}).get(axis) != "PASS"
                for axis in ["wolfram_xact", "sympy", "sage_singular", "lean"]
            )
        ):
            raise PillarSAdjudicationError(f"{key}_CAS_AGGREGATE_INVALID")
        result[key] = {
            "contract_id": contract["identity"]["contract_id"],
            "contract_path": contract_path,
            "contract_sha256": contract_sha,
            "adjudication_path": adjudication_path,
            "adjudication_sha256": _sha256_file(adjudication_path),
            "aggregate_status": "CAS_4AXIS_PASS",
            "claim_ids": sorted(required_claims),
            "source_input_hashes": replayed_source_hashes,
        }
    return result


def _proposal_source_entries() -> list[dict[str, Any]]:
    signatures = _load_yaml(SIGNATURES_PATH)
    group = signatures.get("source_groups", {}).get("proposal_registry_rows", {})
    entries = group.get("entries")
    if not isinstance(entries, list) or len(entries) != 58:
        raise PillarSAdjudicationError("SOURCE_REGISTRY_INVALID")
    ids = [item.get("entry_id") for item in entries if isinstance(item, dict)]
    if len(ids) != 58 or len(set(ids)) != 58:
        raise PillarSAdjudicationError("SOURCE_REGISTRY_INVALID")
    if Counter(item.get("source_partition") for item in entries) != {
        "I": 30,
        "II": 24,
        "BRIDGE": 4,
    }:
        raise PillarSAdjudicationError("SOURCE_PARTITION_COUNTS_INVALID")
    if Counter(item.get("proof_class") for item in entries) != {
        "TC": 30,
        "ST": 24,
        "U": 4,
    }:
        raise PillarSAdjudicationError("SOURCE_PROOF_CLASS_COUNTS_INVALID")
    return deepcopy(entries)


def _source_rows() -> list[dict[str, Any]]:
    proposal_entries = _proposal_source_entries()
    proof_entries = {
        item["id"]: item
        for item in _load_yaml(PROOF_REGISTRY_PATH).get("entries", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    cas = _cas_contract_scope()
    registered_bindings = _load_yaml(SPEC_PATH)["source_disposition_policy"][
        "exact_source_bindings"
    ]
    if set(registered_bindings) != SOURCE_PASS_ROWS:
        raise PillarSAdjudicationError("SOURCE_EXACT_BINDING_REGISTRY_INVALID")
    rows: list[dict[str, Any]] = []
    for source in proposal_entries:
        row_id = source["entry_id"]
        exact = row_id in SOURCE_PASS_ROWS
        if exact:
            proof = proof_entries.get(row_id)
            if (
                not isinstance(proof, dict)
                or proof.get("status") != "PROVEN_CAS4"
                or proof.get("statement") != source.get("statement")
                or source.get("source_status") != "PROVEN_CAS4"
            ):
                raise PillarSAdjudicationError("SOURCE_EXACT_PROOF_SCOPE_INVALID")
            cas_key = "PR257" if row_id in PR257_SOURCE_ROWS else "PR254"
            binding = registered_bindings[row_id]
            if (
                binding.get("legacy_claim_id") != proof.get("legacy_id")
                or binding.get("contract_id") != cas[cas_key]["contract_id"]
                or proof.get("legacy_id") not in cas[cas_key]["claim_ids"]
            ):
                raise PillarSAdjudicationError("SOURCE_EXACT_BINDING_REGISTRY_INVALID")
            evidence = {
                "source_proof_registry": f"{PROOF_REGISTRY_PATH}#{row_id}",
                "cas_contract": deepcopy(cas[cas_key]),
                "legacy_claim_id": binding["legacy_claim_id"],
            }
            verdict = "PASS"
            evidence_class = "EXACT_PROOF"
            finite_status = "EXACT"
            reason = (
                "The exact source statement and legacy claim identity replay "
                "against a bound four-axis CAS pass; no broader source claim follows."
            )
            statistical_sentinel: Any = "NOT_APPLICABLE_EXACT_PROPOSITION"
            semantic_sentinel = "NOT_APPLICABLE_EXACT_SOURCE_PROPOSITION"
        else:
            evidence = {
                "registered_requirement": deepcopy(source.get("required_evidence", [])),
                "source_evidence_path": source.get("evidence_path"),
                "source_status_not_authority": True,
            }
            verdict = "INCONCLUSIVE_WITH_RECEIPT"
            evidence_class = "REQUIRED_EVIDENCE_UNAVAILABLE"
            finite_status = "UNAVAILABLE"
            reason = (
                "The registered routing status is not independent proof and the "
                "required evidence class was not adjudicated by this receipt."
            )
            statistical_sentinel = "UNAVAILABLE"
            semantic_sentinel = "UNAVAILABLE"
        statement = source.get("statement")
        row = {
            "row_id": row_id,
            "source_group": "proposal_registry_rows",
            "source_partition": source.get("source_partition"),
            "proof_class": source.get("proof_class"),
            "source_status": source.get("source_status"),
            "source_statement": statement,
            "source_statement_identity_sha256": source.get(
                "statement_identity_sha256"
            ),
            "source_record_sha256": source.get("source_record_sha256"),
            "source_replay_identity_sha256": "",
            "adjudicated_statement": (
                statement if statement is not None else "UNAVAILABLE_SOURCE_STATEMENT"
            ),
            "statement_relation": (
                "EXACT_SOURCE_STATEMENT_CAS4_REPLAY"
                if exact
                else "SOURCE_STATUS_RETAINED_NOT_INDEPENDENT_ADJUDICATION"
            ),
            "evidence_class": evidence_class,
            "estimand": statistical_sentinel,
            "sampling_law": statistical_sentinel,
            "covariance_assumptions": statistical_sentinel,
            "finite_or_asymptotic_status": finite_status,
            "implementation_evidence": evidence,
            "preregistration_evidence": statistical_sentinel,
            "coverage_evidence": statistical_sentinel,
            "negative_controls": statistical_sentinel,
            "negative_control_terminal": semantic_sentinel,
            "positive_cell_terminal": semantic_sentinel,
            "units_normalization_and_frame": semantic_sentinel,
            "sign_orientation_convention": semantic_sentinel,
            "prior_applicability_and_identity": semantic_sentinel,
            "rank_and_identification_scope": semantic_sentinel,
            "singular_value_and_principal_angle_status": semantic_sentinel,
            "assumptions": deepcopy(source.get("assumptions", [])),
            "counterexample_boundary": deepcopy(
                source.get("required_evidence", [])
            ),
            "verdict": verdict,
            "verdict_reason": reason,
            "claim_ceiling": "diagnostic_only",
        }
        row["source_replay_identity_sha256"] = _source_replay_identity(row)
        rows.append(row)
    return rows


def _program_s_rows() -> list[dict[str, Any]]:
    rows = _load_yaml(PROGRAM_PATH).get("theorems", {}).get("pillar_S")
    if not isinstance(rows, list) or [item.get("id") for item in rows] != [
        f"VT-S{i}" for i in range(1, 15)
    ]:
        raise PillarSAdjudicationError("VTS_SOURCE_REGISTRY_INVALID")
    return deepcopy(rows)


def _negative_controls(row_id: str, result: dict[str, Any]) -> dict[str, Any]:
    if row_id == "VT-S3":
        return {
            "misspecified_covariance_negative_control": deepcopy(
                result["misspecified_covariance_negative_control"]
            ),
            "misspecified_failure_preserved": result[
                "misspecified_failure_preserved"
            ],
        }
    if row_id == "VT-S5":
        return {
            "adversarial_failure_map": deepcopy(result["adversarial_failure_map"]),
            "registered_failure_map": deepcopy(result["registered_failure_map"]),
            "optimizer_output_probability_use": result[
                "optimizer_output_probability_use"
            ],
        }
    if row_id == "VT-S6":
        return {"marginal_only_mutation": result["marginal_only_mutation"]}
    if row_id == "VT-S9":
        return {
            "unadjusted_failure_preserved": result[
                "unadjusted_failure_preserved"
            ],
            "unadjusted_familywise_error_rate": result["report"][
                "unadjusted_familywise_error_rate"
            ],
        }
    if row_id == "VT-S10":
        return {"weak": deepcopy(result["weak"])}
    if row_id == "VT-S11":
        return {"rank_loss": deepcopy(result["rank_loss"])}
    if row_id == "VT-S12":
        return {
            "coordinate_mismatch_refused": True,
            "scalar_coordinates_matched": result["scalar_coordinates_matched"],
            "anchor_coordinates_matched": result["anchor_coordinates_matched"],
        }
    if row_id == "VT-S13":
        return {
            "finite_library_sensitivity": result["finite_library_sensitivity"],
            "reduced_library_known_coverage": result[
                "reduced_library_known_coverage"
            ],
            "unknown_abstention_rate": result["unknown_abstention_rate"],
        }
    if row_id == "VT-S14":
        return {
            "admitted_data_executed": False,
            "MIO_local_diagnostic_cross_check": deepcopy(
                result["MIO_local_diagnostic_cross_check"]
            ),
            "MIO_global_diagnostic_cross_check": deepcopy(
                result["MIO_global_diagnostic_cross_check"]
            ),
        }
    raise PillarSAdjudicationError(f"VTS_NEGATIVE_CONTROL_UNMAPPED:{row_id}")


def _implementation_bundle(validation: dict[str, Any]) -> dict[str, Any]:
    recorded_numpy = validation.get("random_stream_receipt", {}).get(
        "numpy_version"
    )
    if recorded_numpy != np.__version__:
        raise PillarSAdjudicationError("IMPLEMENTATION_NUMPY_VERSION_DRIFT")
    paths = (
        PR272_BUILDER_PATH,
        PR272_IMPLEMENTATION_PATH,
        PR272_SBC_PATH,
        PR272_COVERAGE_PATH,
        PR272_VALIDATION_PATH,
    )
    bundle = {
        "provenance_grade": "CURRENT_REPLAY_BOUND_NOT_PRE_RESULT_EXTERNAL_SEAL",
        "source_hashes": {path: _sha256_file(path) for path in paths},
        "python": {
            "implementation": sys.implementation.name,
            "version": ".".join(str(value) for value in sys.version_info[:3]),
        },
        "numpy_version": np.__version__,
        "recorded_numpy_version": recorded_numpy,
        "replay_command": (
            "python3 -B scripts/codex_harness/"
            "build_pr272_pillar_s_inference.py --check"
        ),
    }
    bundle["bundle_identity_sha256"] = _json_identity(bundle)
    return bundle


def _vts14_rank_contract(config: dict[str, Any]) -> dict[str, Any]:
    covariance = np.asarray(config["covariance"], dtype=float)
    local = np.asarray(config["local_design"], dtype=float)
    global_ = np.asarray(config["global_design"], dtype=float)
    cholesky = np.linalg.cholesky(covariance)
    whitened_local = np.linalg.solve(cholesky, local)
    whitened_global = np.linalg.solve(cholesky, global_)

    def normalized_direction(values: np.ndarray) -> np.ndarray:
        scale = float(np.max(np.abs(values)))
        if not math.isfinite(scale) or scale == 0.0:
            raise PillarSAdjudicationError("VTS14_LOCAL_GLOBAL_RANK_GATE")
        scaled = values / scale
        norm = float(np.linalg.norm(scaled))
        if not math.isfinite(norm) or norm == 0.0:
            raise PillarSAdjudicationError("VTS14_LOCAL_GLOBAL_RANK_GATE")
        return scaled / norm

    local_direction = normalized_direction(whitened_local)
    global_direction = normalized_direction(whitened_global)
    alignment = (
        1.0
        if float(local_direction @ global_direction) >= 0.0
        else -1.0
    )
    angle = float(
        2.0
        * math.atan2(
            float(
                np.linalg.norm(
                    local_direction - alignment * global_direction
                )
            ),
            float(
                np.linalg.norm(
                    local_direction + alignment * global_direction
                )
            ),
        )
    )
    rank = int(
        np.linalg.matrix_rank(
            np.column_stack((local_direction, global_direction))
        )
    )
    floor = 1.0e-12
    if rank != 2 or angle <= floor:
        raise PillarSAdjudicationError("VTS14_LOCAL_GLOBAL_RANK_GATE")

    for source_root in SOURCE_PATHS:
        value = str(source_root)
        if value not in sys.path:
            sys.path.insert(0, value)
    from common.vector_tensor_statistical_inference import (
        ModelCandidate,
        PillarSInferenceError,
        ValidationStatus,
        evaluate_depth_local_global,
    )

    proportional = evaluate_depth_local_global(
        local,
        covariance=np.eye(len(local)),
        covariance_id="pr286-proportional-negative-control",
        local_design=local,
        global_design=2.0 * local,
        mask_path_id=config["mask_path_id"],
        transfer_source="none",
        principal_angle_floor_radians=floor,
    )
    if (
        proportional.status is not ValidationStatus.ABSTAIN_NON_IDENTIFIED
        or proportional.selected_candidate is not ModelCandidate.INDETERMINATE
    ):
        raise PillarSAdjudicationError("VTS14_PROPORTIONAL_DESIGN_SURVIVED")

    def require_typed_refusal(**kwargs: Any) -> str:
        try:
            evaluate_depth_local_global(**kwargs)
        except PillarSInferenceError:
            return "TYPED_REFUSAL"
        raise PillarSAdjudicationError("VTS14_NUMERIC_GUARD_SURVIVED")

    large_local = np.asarray((1.0e200, 1.0e200))
    large_global = np.asarray((1.0e200, 1.0e200 + 2.0e185))
    large_scale_refusal = require_typed_refusal(
        data=large_local,
        covariance=np.eye(2),
        covariance_id="pr286-large-scale-control",
        local_design=large_local,
        global_design=large_global,
        mask_path_id="pr286-hostile-mask",
        transfer_source="none",
        principal_angle_floor_radians=floor,
    )
    extreme_local = np.asarray((0.25, 0.5, 0.75, 1.0))
    extreme_spd_refusal = require_typed_refusal(
        data=extreme_local,
        covariance=np.diag((1.0e-320, 1.0, 2.0, 3.0)),
        covariance_id="pr286-extreme-spd-control",
        local_design=extreme_local,
        global_design=np.ones(4),
        mask_path_id="pr286-hostile-mask",
        transfer_source="none",
    )
    zero_design_refusal = require_typed_refusal(
        data=np.zeros(2),
        covariance=np.eye(2),
        covariance_id="pr286-zero-design-control",
        local_design=np.zeros(2),
        global_design=np.asarray((1.0, 0.0)),
        mask_path_id="pr286-hostile-mask",
        transfer_source="none",
    )
    rank_probe = evaluate_depth_local_global(
        np.asarray((1.0, 0.0)),
        covariance=np.diag((1.0, 1.0e-32)),
        covariance_id="pr286-whitened-rank-control",
        local_design=np.asarray((1.0, 0.0)),
        global_design=np.asarray((1.0, 1.0e-16)),
        mask_path_id="pr286-hostile-mask",
        transfer_source="none",
    )
    if (
        rank_probe.status is not ValidationStatus.VALIDATED_REGISTERED_SYNTHETIC
        or rank_probe.selected_candidate is not ModelCandidate.LOCAL
    ):
        raise PillarSAdjudicationError("VTS14_WHITENED_RANK_CONTROL_FAILED")
    return {
        "scope": "REGISTERED_LOCAL_GLOBAL_DESIGN_CELL_ONLY",
        "joint_design_rank": rank,
        "required_joint_design_rank": 2,
        "rank_metric": "COLUMN_NORMALIZED_COVARIANCE_WHITENED_DESIGN",
        "whitened_principal_angle_radians": angle,
        "principal_angle_floor_radians": floor,
        "global_orbit_separation_claimed": False,
        "proportional_design_negative_control": {
            "status": proportional.status.value,
            "selected_candidate": proportional.selected_candidate.value,
            "expected_terminal": "EXPECTED_NEGATIVE_CONTROL_KILLED",
        },
        "hostile_numeric_controls": {
            "extreme_spd_finite_gls": extreme_spd_refusal,
            "large_scale_finite_gls": large_scale_refusal,
            "whitened_rank_probe": {
                "selected_candidate": rank_probe.selected_candidate.value,
                "status": rank_probe.status.value,
            },
            "zero_design": zero_design_refusal,
        },
    }


def _semantic_fields(
    row_id: str,
    *,
    config: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prior = "NOT_APPLICABLE_NO_PRIOR_IN_REGISTERED_ROW"
    values: dict[str, dict[str, Any]] = {
        "VT-S1": {
            "units": {"status": "DIMENSIONLESS", "normalization": "probability masses sum exactly to one", "frame": "NONE"},
            "sign": "NOT_APPLICABLE_INFORMATION_DIVERGENCE",
            "rank": {"scope": "FINITE_EXPERIMENT_DATA_PROCESSING", "global_identification_claimed": False},
            "spectral": "NOT_APPLICABLE",
        },
        "VT-S2": {
            "units": {"status": "DIMENSIONLESS_AFTER_REGISTERED_THRESHOLD_OR_COVARIANCE_NORMALIZATION", "frame": "DECLARED_COORDINATE_IDENTITY"},
            "sign": "NONNEGATIVE_GAUGE_WITH_EXACT_LT_EQ_GT_RELATION",
            "rank": {"scope": "REGISTERED_ACCEPTANCE_BODY", "pseudoinverse_forbidden": True},
            "spectral": "POSITIVE_DEFINITE_COVARIANCE_REQUIRED_FOR_ELLIPSOID",
        },
        "VT-S3": {
            "units": {"status": "DIMENSIONLESS_WHITENED_Q", "normalization": "registered covariance identity", "frame": "REGISTERED_COORDINATE_ORDER"},
            "sign": "MAX_ABSOLUTE_WHITENED_COORDINATE",
            "rank": {"scope": "REGISTERED_FOUR_COORDINATE_NULL", "dimension": 4, "global_identification_claimed": False},
            "spectral": "COVARIANCE_IDENTITY_BOUND_BY_CALIBRATION_AND_EVALUATION_IDS",
        },
        "VT-S4": {
            "units": {"status": "DIMENSIONLESS_PROBABILITY", "threshold_units": "MATCH_SOURCE_DRAW_UNITS", "frame": "SAMPLING_LAW_SPEC"},
            "sign": "STRICT_RIGHT_TAIL_X_GREATER_THAN_T",
            "rank": {"scope": "ONE_TYPED_SAMPLING_LAW", "global_identification_claimed": False},
            "spectral": "NOT_APPLICABLE",
        },
        "VT-S5": {
            "units": {"status": "ESTIMAND_COORDINATE_UNITS", "normalization": "frozen identified-set grid", "frame": "REGISTERED_PARAMETERIZATION"},
            "sign": "LOWER_AND_UPPER_ENVELOPE_ORDER_PRESERVED",
            "rank": {"scope": "BOUNDED_REGISTERED_IDENTIFIED_SET_GRID", "optimizer_point_is_probability": False},
            "spectral": "NOT_APPLICABLE",
        },
        "VT-S6": {
            "units": {"status": "DIMENSIONLESS_RATIO_AFTER_COMPATIBLE_NUMERATOR_ANCHOR_UNITS", "normalization": "joint law", "frame": "REGISTERED_NUMERATOR_ANCHOR_ORDER"},
            "sign": "NUMERATOR_DIVIDED_BY_SIGNED_NONZERO_ANCHOR",
            "rank": {"scope": "JOINT_BIVARIATE_LAW", "marginal_only_forbidden": True},
            "spectral": "FULL_JOINT_COVARIANCE_REQUIRED",
        },
        "VT-S7": {
            "units": {"status": "REGISTERED_FUNCTIONAL_OUTPUT_UNITS", "normalization": "sample-wise pushforward", "frame": "SOURCE_LAW"},
            "sign": "REGISTERED_FUNCTIONAL_ORIENTATION",
            "rank": {"scope": "SAMPLEWISE_PUSHFORWARD", "ratio_of_means_forbidden": True},
            "spectral": "NOT_APPLICABLE",
        },
        "VT-S8": {
            "units": {"status": "FEATURE_UNITS_SQUARED", "normalization": "paired covariance blocks in one basis", "frame": "SAME_OBSERVATIONAL_UNIT"},
            "sign": "ORDERED_CONTRAST_X_A_MINUS_X_B_AND_C_AA_PLUS_C_BB_MINUS_C_AB_MINUS_C_BA",
            "rank": {"scope": "PAIRED_FINITE_SECOND_MOMENT_LAW", "independent_depth_relabel_forbidden": True},
            "spectral": "COVARIANCE_BLOCK_DIMENSIONS_AND_BASIS_MUST_MATCH",
        },
        "VT-S9": {
            "units": {"status": "DIMENSIONLESS_STANDARDIZED_DEPTH_CONTRAST", "normalization": "same centered target", "frame": "FINITE_NESTED_DEPTH_PATH"},
            "sign": "MAX_ABSOLUTE_STANDARDIZED_CONTRAST",
            "rank": {"scope": "FINITE_REGISTERED_PATH_ONLY", "continuum_claimed": False},
            "spectral": "SINGULAR_PATH_COVARIANCE_HANDLED_BY_REGISTERED_MAX_STATISTIC",
        },
        "VT-S10": {
            "units": {"status": "DIMENSIONLESS_WHITENED_RESPONSE", "normalization": "registered covariance", "frame": "SUPPORTED_RESPONSE_SPACE"},
            "sign": "PRINCIPAL_ANGLE_NONNEGATIVE",
            "rank": {"scope": "REGISTERED_RESPONSE_CELL", "supported_rank": (result or {}).get("well_identified", {}).get("supported_rank"), "global_identification_claimed": False},
            "spectral": {"well_identified": deepcopy((result or {}).get("well_identified", {})), "weak_abstention": deepcopy((result or {}).get("weak", {}))},
        },
        "VT-S11": {
            "units": {"status": "DIMENSIONLESS_LINEAR_MAP_COORDINATES", "normalization": "registered orbit and response bases", "frame": "ONE_DECLARED_LINEAR_CELL"},
            "sign": "NOT_APPLICABLE_RANK_COMPOSITION",
            "rank": {"scope": "REGISTERED_PRINCIPAL_STRATUM_LINEAR_CELL_ONLY", "registered_cell": deepcopy((result or {}).get("registered_cell", {})), "global_orbit_separation_claimed": False},
            "spectral": {"rank_loss_negative_control": deepcopy((result or {}).get("rank_loss", {}))},
        },
        "VT-S12": {
            "units": {"status": "DIMENSIONLESS_FROZEN_MORPHOLOGY_SUMMARY", "normalization": "frozen modes per replicate", "frame": "EXACTLY_MATCHED_SCALAR_AND_ANCHOR_COORDINATES"},
            "sign": "ALTERNATIVE_MINUS_MATCHED_NULL_SHIFT",
            "rank": {"scope": "REGISTERED_SYNTHETIC_COUNTERPAIR_ONLY", "physical_family_identification_claimed": False},
            "spectral": "NOT_APPLICABLE",
        },
        "VT-S13": {
            "units": {"status": "DIMENSIONLESS_REGISTERED_FEATURE_DISTANCE", "normalization": "frozen known centres and threshold", "frame": "FINITE_LIBRARY"},
            "sign": "NONNEGATIVE_DISTANCE_WITH_UNKNOWN_ABSTENTION",
            "rank": {"scope": "FINITE_LIBRARY_ONLY", "nearest_family_for_unknown_forbidden": True},
            "spectral": "FINITE_LIBRARY_REMOVAL_SENSITIVITY_RETAINED",
        },
    }
    if row_id == "VT-S14":
        if config is None:
            raise PillarSAdjudicationError("VTS14_CONFIG_MISSING")
        rank_contract = _vts14_rank_contract(config)
        values[row_id] = {
            "units": {"status": "DIMENSIONLESS_GLS_CHI_SQUARE", "normalization": "registered_depth_covariance", "frame": "HTT_LOCAL_GLOBAL_DESIGN_PAIR"},
            "sign": "CHI_SQUARE_AND_RESIDUAL_DIFFERENCE_GLOBAL_MINUS_LOCAL",
            "rank": rank_contract,
            "spectral": {"joint_rank": rank_contract["joint_design_rank"], "whitened_principal_angle_radians": rank_contract["whitened_principal_angle_radians"], "status": "SEPARABLE_REGISTERED_DESIGN_CELL_ONLY"},
        }
    if row_id not in values:
        raise PillarSAdjudicationError(f"SEMANTIC_TYPE_UNMAPPED:{row_id}")
    return {
        "units_normalization_and_frame": values[row_id]["units"],
        "sign_orientation_convention": values[row_id]["sign"],
        "prior_applicability_and_identity": prior,
        "rank_and_identification_scope": values[row_id]["rank"],
        "singular_value_and_principal_angle_status": values[row_id]["spectral"],
    }


def _statistical_identity(row: dict[str, Any]) -> str:
    return _json_identity(
        {
            "row_id": row["row_id"],
            "estimand": row["estimand"],
            "sampling_law": row["sampling_law"],
            "covariance_assumptions": row["covariance_assumptions"],
            "finite_or_asymptotic_status": row["finite_or_asymptotic_status"],
            "preregistration_evidence": row["preregistration_evidence"],
        }
    )


def _semantic_identity(row: dict[str, Any]) -> str:
    return _json_identity(
        {
            "units_normalization_and_frame": row[
                "units_normalization_and_frame"
            ],
            "sign_orientation_convention": row[
                "sign_orientation_convention"
            ],
            "prior_applicability_and_identity": row[
                "prior_applicability_and_identity"
            ],
            "rank_and_identification_scope": row[
                "rank_and_identification_scope"
            ],
            "singular_value_and_principal_angle_status": row[
                "singular_value_and_principal_angle_status"
            ],
        }
    )


def _vector_tensor_rows() -> list[dict[str, Any]]:
    program_rows = _program_s_rows()
    exact_spec = _load_yaml(PR271_SPEC_PATH)
    exact_records = {
        item["obligation_id"]: item
        for item in _load_yaml(PR271_CORE_PATH).get("records", [])
        if isinstance(item, dict) and item.get("obligation_id") in VT_EXACT_ROWS
    }
    prereg_spec = _load_yaml(PR272_SPEC_PATH)
    validation = _load_yaml(PR272_VALIDATION_PATH)
    validation_records = {
        item["theorem_id"]: item
        for item in validation.get("records", [])
        if isinstance(item, dict)
    }
    validation_results = validation.get("validation_results", {})
    boundaries = prereg_spec.get("registered_statement_boundaries", {})
    preregistration = prereg_spec.get("preregistration", {})
    random_receipt = validation.get("random_stream_receipt", {})
    blind_pack = _load_json(PR273_PACK_PATH)
    implementation_bundle = _implementation_bundle(validation)
    if (
        set(exact_records) != VT_EXACT_ROWS
        or set(validation_records) != VT_SYNTHETIC_ROWS | VT_BLOCKED_ROWS
        or not isinstance(validation_results, dict)
        or blind_pack.get("adjudication_status") != "PASS"
        or blind_pack.get("claim_ceiling") != "diagnostic_only"
        or blind_pack.get("transfer_source") != "none"
    ):
        raise PillarSAdjudicationError("VTS_EVIDENCE_REGISTRY_INVALID")

    rows: list[dict[str, Any]] = []
    typed = exact_spec.get("typed_statements", {})
    for source in program_rows:
        row_id = source["id"]
        source_identity = _json_identity(
            {
                "id": row_id,
                "title": source["title"],
                "status": source["status"],
                "proof_mode": source["proof_mode"],
            }
        )
        if row_id in VT_EXACT_ROWS:
            record = exact_records[row_id]
            statement = typed.get(row_id)
            if (
                not isinstance(statement, dict)
                or record.get("claim_ceiling") != "diagnostic_only"
                or not str(record.get("verdict", "")).startswith("PROVED_")
            ):
                raise PillarSAdjudicationError("VTS_EXACT_PROOF_SCOPE_INVALID")
            semantic_fields = _semantic_fields(row_id)
            row = {
                "row_id": row_id,
                "source_group": "vector_tensor_successor",
                "source_partition": "VT-S",
                "proof_class": "EXACT",
                "source_status": source["status"],
                "source_statement": source["title"],
                "source_statement_identity_sha256": record[
                    "source_statement_identity_sha256"
                ],
                "source_replay_identity_sha256": "",
                "adjudicated_statement": statement["statement"],
                "statement_relation": record["relation_to_source"],
                "evidence_class": "EXACT_TYPED_PROOF",
                "estimand": record["estimand"],
                "sampling_law": record["sampling_law"],
                "covariance_assumptions": deepcopy(
                    record["covariance_assumptions"]
                ),
                "finite_or_asymptotic_status": record[
                    "finite_or_asymptotic_status"
                ],
                "implementation_evidence": deepcopy(record["evidence_refs"]),
                "preregistration_evidence": "NOT_APPLICABLE_EXACT_PROPOSITION",
                "coverage_evidence": "NOT_APPLICABLE_EXACT_PROPOSITION",
                "negative_controls": "NOT_APPLICABLE_EXACT_PROPOSITION",
                "negative_control_terminal": "NOT_APPLICABLE_EXACT_PROPOSITION",
                "positive_cell_terminal": "NOT_APPLICABLE_EXACT_PROPOSITION",
                "assumptions": deepcopy(record["assumptions"]),
                "counterexample_boundary": deepcopy(
                    record["counterexample_boundaries"]
                ),
                "verdict": "PASS",
                "verdict_reason": (
                    "The typed exact proposition is proved under its frozen premises; "
                    "no broader source or population claim is granted."
                ),
                "claim_ceiling": "diagnostic_only",
                **semantic_fields,
            }
        else:
            record = validation_records[row_id]
            result = validation_results.get(row_id)
            config_key = STAT_CONFIG_KEYS[row_id]
            config = preregistration.get(config_key)
            boundary = boundaries.get(row_id)
            if (
                not isinstance(result, dict)
                or not isinstance(config, dict)
                or not isinstance(boundary, str)
                or record.get("claim_ceiling") != "diagnostic_only"
            ):
                raise PillarSAdjudicationError("VTS_STATISTICAL_EVIDENCE_INVALID")
            prereg_evidence = {
                "spec_path": f"{PR272_SPEC_PATH}#preregistration.{config_key}",
                "config_key": config_key,
                "config_sha256": _json_identity(config),
                "random_stream_sha256": _json_identity(
                    prereg_spec["preregistration"]["random_stream"]
                ),
                "registered_seed_family_sha256": random_receipt.get(
                    "registered_seed_family_sha256"
                ),
                "validation_preregistration_sha256": validation.get(
                    "preregistration_sha256"
                ),
                "statement_boundary": boundary,
            }
            verdict = (
                "BLOCKED_WITH_RECEIPT" if row_id == "VT-S14" else "PASS"
            )
            semantic_fields = _semantic_fields(
                row_id, config=config, result=result
            )
            negative_controls = _negative_controls(row_id, result)
            if row_id == "VT-S14":
                negative_controls["proportional_design_rank_gate"] = deepcopy(
                    semantic_fields["rank_and_identification_scope"][
                        "proportional_design_negative_control"
                    ]
                )
            row = {
                "row_id": row_id,
                "source_group": "vector_tensor_successor",
                "source_partition": "VT-S",
                "proof_class": "STATISTICAL",
                "source_status": source["status"],
                "source_statement": source["title"],
                "source_statement_identity_sha256": source_identity,
                "source_replay_identity_sha256": "",
                "adjudicated_statement": boundary,
                "statement_relation": (
                    "REGISTERED_SYNTHETIC_BOUNDARY_NO_SOURCE_PROMOTION"
                ),
                "evidence_class": "PREREGISTERED_SYNTHETIC_VALIDATION_ONLY",
                "estimand": STAT_ESTIMANDS[row_id],
                "sampling_law": STAT_LAWS[row_id],
                "covariance_assumptions": deepcopy(config.get("covariance", [])),
                "finite_or_asymptotic_status": "FINITE_PREREGISTERED_SYNTHETIC",
                "implementation_evidence": {
                    "validation_record": record["evidence_path"],
                    "implementation_bundle": deepcopy(implementation_bundle),
                    "held_out_integration_pack": PR273_PACK_PATH,
                    "held_out_pack_content_id": blind_pack.get("content_id"),
                },
                "preregistration_evidence": prereg_evidence,
                "coverage_evidence": deepcopy(result),
                "negative_controls": negative_controls,
                "negative_control_terminal": "EXPECTED_NEGATIVE_CONTROL_KILLED",
                "positive_cell_terminal": "PASS_REGISTERED_POSITIVE_CELL",
                "assumptions": deepcopy(record["assumptions"]),
                "counterexample_boundary": deepcopy(
                    record["counterexample_boundaries"]
                ),
                "verdict": verdict,
                "verdict_reason": (
                    "The registered synthetic cell passed its frozen validation, but "
                    "admitted data are absent and the source program obligation remains blocked."
                    if row_id == "VT-S14"
                    else "The preregistered finite synthetic cell passed with its "
                    "negative controls visible; the source program remains conditional."
                ),
                "source_status_effect": (
                    "RETAIN_PROGRAM_OBLIGATION"
                    if row_id == "VT-S14"
                    else "RETAIN_CONDITIONAL_PROGRAM"
                ),
                "claim_ceiling": "diagnostic_only",
                **semantic_fields,
            }
        row["source_replay_identity_sha256"] = _source_replay_identity(row)
        row["statistical_contract_identity_sha256"] = _statistical_identity(row)
        row["semantic_type_identity_sha256"] = _semantic_identity(row)
        rows.append(row)
    return rows


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source = [item for item in rows if item["source_group"] == "proposal_registry_rows"]
    vector = [item for item in rows if item["source_group"] == "vector_tensor_successor"]
    counts = Counter(item["verdict"] for item in rows)
    return {
        "source_rows": len(source),
        "source_partition_counts": dict(
            sorted(Counter(item["source_partition"] for item in source).items())
        ),
        "source_proof_class_counts": dict(
            sorted(Counter(item["proof_class"] for item in source).items())
        ),
        "vector_tensor_rows": len(vector),
        "terminal_counts": {
            "PASS": counts["PASS"],
            "FAIL": counts["FAIL"],
            "INCONCLUSIVE_WITH_RECEIPT": counts[
                "INCONCLUSIVE_WITH_RECEIPT"
            ],
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
    registry = _load_yaml(SPEC_PATH).get("mutation_registry")
    if not isinstance(registry, list) or len(registry) != 19:
        raise PillarSAdjudicationError("MUTATION_REGISTRY_INVALID")
    return deepcopy(registry)


def _future_consumer_contract() -> dict[str, Any]:
    spec = _load_yaml(SPEC_PATH)["future_consumer_contract"]
    expected = {
        "consumer": "PR-287",
        "upstream_terminal_required": "PASS_COMPLETE_PILLAR_S_ADJUDICATION",
        "upstream_success_semantics": "PROCESS_COMPLETION_ONLY",
        "required_row_fields": [
            "row_id",
            "verdict",
            "evidence_class",
            "statement_relation",
            "claim_ceiling",
        ],
        "preserve_row_verdicts": True,
        "preserve_inconclusive_and_blocked": True,
        "synthetic_validation_effect": "NO_OBSERVED_OR_SOURCE_PROOF_PROMOTION",
        "rule": spec["rule"],
    }
    if spec != expected:
        raise PillarSAdjudicationError("PR287_CONSUMER_CONTRACT_DRIFT")
    for path in (
        BACKLOG_PATH,
        BACKLOG_MIRROR_PATH,
        BACKLOG_JSON_PATH,
        BACKLOG_JSON_MIRROR_PATH,
    ):
        backlog = _load_yaml(path)
        card = next(item for item in backlog["prs"] if item["id"] == "PR-287")
        dependency = next(
            item
            for item in card["dependency_contracts"]
            if item["upstream_id"] == "PR-286"
        )
        if dependency != {
            "upstream_id": "PR-286",
            "mode": "requires_success",
            "required_terminal": expected["upstream_terminal_required"],
            "success_semantics": expected["upstream_success_semantics"],
            "downstream_row_contract": {
                "preserve_row_verdicts": True,
                "preserve_inconclusive_and_blocked": True,
                "synthetic_validation_effect": expected[
                    "synthetic_validation_effect"
                ],
            },
        }:
            raise PillarSAdjudicationError("PR287_DAG_CONSUMER_BINDING_DRIFT")
    return expected


def _base_payload() -> dict[str, Any]:
    bindings, binding_map = _source_bindings()
    rows = [*_source_rows(), *_vector_tensor_rows()]
    payload = {
        "schema": "htt.pr286.pillar_s_complete_adjudication_receipt.v1",
        "pr_id": "PR-286",
        "change_set_id": "CS-PR286-PILLAR-S-ADJUDICATION",
        "publication_group_id": "PG-PR286-PILLAR-S-ADJUDICATION",
        "terminal": "PASS_COMPLETE_PILLAR_S_ADJUDICATION",
        "success_dependency_satisfied": True,
        "success_semantics": "PROCESS_COMPLETION_ONLY",
        "scientific_status_effect": "ROW_LEVEL_EVIDENCE_SPECIFIC_DISPOSITION_ONLY",
        "metadata": {
            "owner": "HTT",
            "scope": "pre-solver complete Pillar-S row-level evidence disposition",
            "claim_tier": "diagnostic_only",
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
            "scientific_artifact_mode": "proof_adjudication_diagnostic",
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
                "run_pr286_pillar_s_adjudication.py build"
            ),
            "assumptions": deepcopy(_load_yaml(SPEC_PATH)["assumptions"]),
            "caveats": deepcopy(_load_yaml(SPEC_PATH)["caveats"]),
        },
        "ownership": {
            "COMMON": "exact contracts and proof identities",
            "OBSSTAT": "observable estimands features nulls and covariance inputs",
            "HTT": "model-dependent calibration coverage and inference diagnostics",
            "MIO": "diagnostic residual and coherence consumers only",
        },
        "mio_forbidden_outputs": [
            "likelihood",
            "posterior",
            "Bayes_factor",
            "evidence",
        ],
        "statement_identity_contract": deepcopy(
            _load_yaml(SPEC_PATH)["inventory_contract"]["statement_identity_replay"]
        ),
        "future_consumer_contract": _future_consumer_contract(),
        "cas_source_evidence": _cas_contract_scope(),
        "synthetic_implementation_bundle": _implementation_bundle(
            _load_yaml(PR272_VALIDATION_PATH)
        ),
        "negative_control_terminal_contract": deepcopy(
            _load_yaml(SPEC_PATH)["statistical_receipt_contract"][
                "negative_control_terminal_rule"
            ]
        ),
        "source_bindings": bindings,
        "source_binding_map": binding_map,
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
    row_map = _row_map(payload)
    if mutation_id == "MU286-DROP-SOURCE-ROW":
        rows.pop(next(i for i, item in enumerate(rows) if item["source_group"] == "proposal_registry_rows"))
    elif mutation_id == "MU286-DROP-VTS-ROW":
        rows.pop(next(i for i, item in enumerate(rows) if item["source_group"] == "vector_tensor_successor"))
    elif mutation_id == "MU286-BARE-SOURCE-STATUS":
        rows[0]["verdict"] = rows[0]["source_status"]
    elif mutation_id == "MU286-STATEMENT-DRIFT":
        rows[0]["source_statement"] = "mutated statement"
    elif mutation_id == "MU286-EXACT-BY-SIMULATION":
        row_map["VT-S1"]["evidence_class"] = "SIMULATION_DIAGNOSTIC"
    elif mutation_id == "MU286-ORACLE-LABEL-AS-PROOF":
        row_map["I-1.1"]["verdict"] = "PASS"
    elif mutation_id == "MU286-ESTIMAND-DRIFT":
        row_map["VT-S3"]["estimand"] += " after inspection"
    elif mutation_id == "MU286-LAW-COVARIANCE-DRIFT":
        row_map["VT-S3"]["sampling_law"] = "post-hoc replacement law"
    elif mutation_id == "MU286-SEED-TOLERANCE-DRIFT":
        row_map["VT-S3"]["preregistration_evidence"][
            "random_stream_sha256"
        ] = "0" * 64
    elif mutation_id == "MU286-HIDE-NEGATIVE-CONTROL":
        row_map["VT-S3"]["negative_controls"] = {}
    elif mutation_id == "MU286-VTS14-DATA-PROMOTION":
        row_map["VT-S14"]["verdict"] = "PASS"
    elif mutation_id == "MU286-MIO-POSTERIOR":
        payload["mio_forbidden_outputs"].remove("posterior")
    elif mutation_id == "MU286-CLAIM-PROMOTION":
        payload["metadata"]["claim_tier"] = "native_validated"
        payload["metadata"]["observed_data_executed"] = True
        payload["metadata"]["public_use"] = True
    elif mutation_id == "MU286-CAS-BINDING-DRIFT":
        payload["cas_source_evidence"]["PR257"]["contract_sha256"] = "0" * 64
    elif mutation_id == "MU286-IMPLEMENTATION-BINDING-DRIFT":
        row_map["VT-S3"]["implementation_evidence"]["implementation_bundle"][
            "source_hashes"
        ][PR272_IMPLEMENTATION_PATH] = "0" * 64
    elif mutation_id == "MU286-SEMANTIC-TYPE-DRIFT":
        row_map["VT-S8"]["sign_orientation_convention"] = (
            "REVERSED_CONTRAST_X_B_MINUS_X_A"
        )
    elif mutation_id == "MU286-NEGATIVE-CONTROL-SURVIVES":
        row_map["VT-S3"]["negative_control_terminal"] = (
            "UNEXPECTED_NEGATIVE_CONTROL_SURVIVED"
        )
    elif mutation_id == "MU286-VTS14-PROPORTIONAL-DESIGN":
        row_map["VT-S14"]["rank_and_identification_scope"][
            "joint_design_rank"
        ] = 1
    elif mutation_id == "MU286-VTS14-NUMERIC-GUARD-DRIFT":
        row_map["VT-S14"]["rank_and_identification_scope"][
            "hostile_numeric_controls"
        ]["large_scale_finite_gls"] = "MUTATED_ACCEPTED"
    else:
        raise PillarSAdjudicationError(f"UNKNOWN_MUTATION:{mutation_id}")
    return payload


def _validate_claim_and_ownership(payload: dict[str, Any]) -> None:
    metadata = payload.get("metadata")
    expected = {
        "claim_tier": "diagnostic_only",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "proof_adjudication_diagnostic",
        "transfer_source": "none",
        "observed_data_executed": False,
        "public_use": False,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    }
    if not isinstance(metadata, dict) or any(
        metadata.get(key) != value for key, value in expected.items()
    ):
        raise PillarSAdjudicationError("CLAIM_FIREWALL_DRIFT")
    if payload.get("mio_forbidden_outputs") != [
        "likelihood",
        "posterior",
        "Bayes_factor",
        "evidence",
    ]:
        raise PillarSAdjudicationError("OWNERSHIP_FIREWALL_DRIFT")


def _validate_core(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise PillarSAdjudicationError("RECEIPT_NOT_OBJECT")
    _validate_claim_and_ownership(payload)
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise PillarSAdjudicationError("ROWS_NOT_LIST")
    required_fields = {
        "row_id",
        "source_group",
        "source_statement",
        "source_statement_identity_sha256",
        "source_replay_identity_sha256",
        "adjudicated_statement",
        "statement_relation",
        "evidence_class",
        "estimand",
        "sampling_law",
        "covariance_assumptions",
        "finite_or_asymptotic_status",
        "implementation_evidence",
        "preregistration_evidence",
        "coverage_evidence",
        "negative_controls",
        "negative_control_terminal",
        "positive_cell_terminal",
        "units_normalization_and_frame",
        "sign_orientation_convention",
        "prior_applicability_and_identity",
        "rank_and_identification_scope",
        "singular_value_and_principal_angle_status",
        "assumptions",
        "counterexample_boundary",
        "verdict",
        "verdict_reason",
        "claim_ceiling",
    }
    if any(not isinstance(item, dict) or not required_fields <= item.keys() for item in rows):
        raise PillarSAdjudicationError("ROW_SCHEMA_INVALID")

    actual_source = [
        item for item in rows if item.get("source_group") == "proposal_registry_rows"
    ]
    actual_vts = [
        item for item in rows if item.get("source_group") == "vector_tensor_successor"
    ]
    expected_source = _source_rows()
    expected_vts = _vector_tensor_rows()
    if [item.get("row_id") for item in actual_source] != [
        item["row_id"] for item in expected_source
    ]:
        raise PillarSAdjudicationError("SOURCE_INVENTORY_MISMATCH")
    if [item.get("row_id") for item in actual_vts] != [
        item["row_id"] for item in expected_vts
    ]:
        raise PillarSAdjudicationError("VTS_INVENTORY_MISMATCH")
    if len(rows) != 72:
        raise PillarSAdjudicationError("TOTAL_RECEIPT_COUNT_MISMATCH")
    if any(item.get("verdict") not in TERMINAL_VERDICTS for item in rows):
        raise PillarSAdjudicationError("TERMINAL_VOCABULARY_INVALID")

    for actual, expected in zip(actual_source, expected_source, strict=True):
        if (
            actual.get("source_statement") != expected["source_statement"]
            or actual.get("source_statement_identity_sha256")
            != expected["source_statement_identity_sha256"]
            or actual.get("source_replay_identity_sha256")
            != _source_replay_identity(actual)
            or actual.get("source_replay_identity_sha256")
            != expected["source_replay_identity_sha256"]
            or actual.get("adjudicated_statement")
            != expected["adjudicated_statement"]
        ):
            raise PillarSAdjudicationError("STATEMENT_IDENTITY_DRIFT")
        row_id = actual["row_id"]
        if row_id in SOURCE_PASS_ROWS:
            if (
                actual.get("verdict") != "PASS"
                or actual.get("evidence_class") != "EXACT_PROOF"
                or actual.get("finite_or_asymptotic_status") != "EXACT"
            ):
                raise PillarSAdjudicationError("SOURCE_EXACT_EVIDENCE_INVALID")
        elif actual.get("verdict") != "INCONCLUSIVE_WITH_RECEIPT":
            raise PillarSAdjudicationError("SOURCE_STATUS_PROMOTION")

    for actual, expected in zip(actual_vts, expected_vts, strict=True):
        if (
            actual.get("source_statement") != expected["source_statement"]
            or actual.get("source_replay_identity_sha256")
            != _source_replay_identity(actual)
            or actual.get("source_replay_identity_sha256")
            != expected["source_replay_identity_sha256"]
            or actual.get("adjudicated_statement")
            != expected["adjudicated_statement"]
        ):
            raise PillarSAdjudicationError("STATEMENT_IDENTITY_DRIFT")
        row_id = actual["row_id"]
        if row_id in VT_EXACT_ROWS:
            if (
                actual.get("verdict") != "PASS"
                or actual.get("evidence_class") != "EXACT_TYPED_PROOF"
            ):
                raise PillarSAdjudicationError("EXACT_EVIDENCE_CLASS_INVALID")
            if (
                actual.get("semantic_type_identity_sha256")
                != _semantic_identity(actual)
                or actual.get("semantic_type_identity_sha256")
                != expected["semantic_type_identity_sha256"]
            ):
                raise PillarSAdjudicationError("SEMANTIC_TYPE_DRIFT")
        else:
            if actual.get("preregistration_evidence") != expected[
                "preregistration_evidence"
            ]:
                raise PillarSAdjudicationError("PREREGISTRATION_DRIFT")
            if actual.get("implementation_evidence") != expected[
                "implementation_evidence"
            ]:
                raise PillarSAdjudicationError("IMPLEMENTATION_IDENTITY_DRIFT")
            if (
                actual.get("statistical_contract_identity_sha256")
                != _statistical_identity(actual)
                or actual.get("statistical_contract_identity_sha256")
                != expected["statistical_contract_identity_sha256"]
            ):
                raise PillarSAdjudicationError("STATISTICAL_IDENTITY_DRIFT")
            if actual.get("negative_controls") != expected["negative_controls"]:
                raise PillarSAdjudicationError("NEGATIVE_CONTROL_HIDDEN")
            if (
                actual.get("negative_control_terminal")
                != "EXPECTED_NEGATIVE_CONTROL_KILLED"
                or actual.get("positive_cell_terminal")
                != "PASS_REGISTERED_POSITIVE_CELL"
            ):
                raise PillarSAdjudicationError("NEGATIVE_CONTROL_TERMINAL_DRIFT")
            if row_id == "VT-S14" and (
                actual.get("rank_and_identification_scope", {}).get(
                    "joint_design_rank"
                )
                != 2
                or actual.get("rank_and_identification_scope", {}).get(
                    "whitened_principal_angle_radians", 0.0
                )
                <= actual.get("rank_and_identification_scope", {}).get(
                    "principal_angle_floor_radians", 0.0
                )
            ):
                raise PillarSAdjudicationError("VTS14_LOCAL_GLOBAL_RANK_GATE")
            if (
                actual.get("semantic_type_identity_sha256")
                != _semantic_identity(actual)
                or actual.get("semantic_type_identity_sha256")
                != expected["semantic_type_identity_sha256"]
            ):
                raise PillarSAdjudicationError("SEMANTIC_TYPE_DRIFT")
            if row_id == "VT-S14":
                if (
                    actual.get("verdict") != "BLOCKED_WITH_RECEIPT"
                    or actual.get("source_status_effect")
                    != "RETAIN_PROGRAM_OBLIGATION"
                ):
                    raise PillarSAdjudicationError(
                        "VTS14_ADMITTED_DATA_PROMOTION"
                    )
            elif (
                actual.get("verdict") != "PASS"
                or actual.get("source_status_effect")
                != "RETAIN_CONDITIONAL_PROGRAM"
            ):
                raise PillarSAdjudicationError("VTS_SYNTHETIC_DISPOSITION_DRIFT")

    expected_bindings, expected_map = _source_bindings()
    if (
        payload.get("source_bindings") != expected_bindings
        or payload.get("source_binding_map") != expected_map
    ):
        raise PillarSAdjudicationError("SOURCE_BINDING_DRIFT")
    if payload.get("cas_source_evidence") != _cas_contract_scope():
        raise PillarSAdjudicationError("CAS_SOURCE_EVIDENCE_DRIFT")
    expected_implementation = _implementation_bundle(
        _load_yaml(PR272_VALIDATION_PATH)
    )
    if payload.get("synthetic_implementation_bundle") != expected_implementation:
        raise PillarSAdjudicationError("IMPLEMENTATION_IDENTITY_DRIFT")
    expected_negative_contract = _load_yaml(SPEC_PATH)[
        "statistical_receipt_contract"
    ]["negative_control_terminal_rule"]
    if payload.get("negative_control_terminal_contract") != expected_negative_contract:
        raise PillarSAdjudicationError("NEGATIVE_CONTROL_TERMINAL_DRIFT")
    if payload.get("future_consumer_contract") != _future_consumer_contract():
        raise PillarSAdjudicationError("PR287_CONSUMER_CONTRACT_DRIFT")
    expected_identity_contract = _load_yaml(SPEC_PATH)["inventory_contract"][
        "statement_identity_replay"
    ]
    if payload.get("statement_identity_contract") != expected_identity_contract:
        raise PillarSAdjudicationError("STATEMENT_IDENTITY_CONTRACT_DRIFT")
    if payload.get("summary") != _summary(rows):
        raise PillarSAdjudicationError("SUMMARY_DRIFT")
    if (
        payload.get("terminal") != "PASS_COMPLETE_PILLAR_S_ADJUDICATION"
        or payload.get("success_dependency_satisfied") is not True
        or payload.get("success_semantics") != "PROCESS_COMPLETION_ONLY"
        or payload.get("scientific_status_effect")
        != "ROW_LEVEL_EVIDENCE_SPECIFIC_DISPOSITION_ONLY"
    ):
        raise PillarSAdjudicationError("PROCESS_TERMINAL_DRIFT")


def validate_complete_adjudication_receipt(payload: dict[str, Any]) -> None:
    _validate_core(payload)
    expected_registry = _expected_mutation_registry()
    if payload.get("mutation_registry") != expected_registry:
        raise PillarSAdjudicationError("MUTATION_REGISTRY_DRIFT")
    expected_ids = [item["mutation_id"] for item in expected_registry]
    results = payload.get("mutation_results")
    if not isinstance(results, list) or [
        item.get("mutation_id") for item in results
    ] != expected_ids:
        raise PillarSAdjudicationError("MUTATION_RESULTS_INCOMPLETE")
    for item in results:
        if (
            item.get("executed") is not True
            or item.get("activated") is not True
            or item.get("killed") is not True
            or item.get("survivor") is not False
            or not isinstance(item.get("kill_marker"), str)
            or not item["kill_marker"]
            or item.get("evidence_fingerprint")
            != _json_identity(
                {
                    "mutation_id": item["mutation_id"],
                    "kill_marker": item["kill_marker"],
                }
            )
        ):
            raise PillarSAdjudicationError("MUTATION_RESULT_INVALID")
    if payload.get("receipt_content_sha256") != receipt_content_sha256(payload):
        raise PillarSAdjudicationError("RECEIPT_CONTENT_ADDRESS_DRIFT")


def _run_registered_mutations(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in payload["mutation_registry"]:
        mutation_id = item["mutation_id"]
        mutated = apply_registered_mutation(deepcopy(payload), mutation_id)
        killed = False
        marker = ""
        try:
            _validate_core(mutated)
        except PillarSAdjudicationError as exc:
            killed = True
            marker = str(exc)
        result = {
            "mutation_id": mutation_id,
            "executed": True,
            "activated": True,
            "killed": killed,
            "survivor": not killed,
            "kill_marker": marker,
        }
        result["evidence_fingerprint"] = _json_identity(
            {"mutation_id": mutation_id, "kill_marker": marker}
        )
        results.append(result)
    expected_ids = [item["mutation_id"] for item in payload["mutation_registry"]]
    if [item["mutation_id"] for item in results] != expected_ids:
        raise PillarSAdjudicationError("MUTATION_RESULTS_INCOMPLETE")
    if any(not item["killed"] for item in results):
        survivors = [item["mutation_id"] for item in results if not item["killed"]]
        raise PillarSAdjudicationError("MUTATION_SURVIVED:" + ",".join(survivors))
    return results


def build_complete_adjudication_receipt() -> dict[str, Any]:
    payload = _base_payload()
    _validate_core(payload)
    results = _run_registered_mutations(payload)
    expected_ids = [item["mutation_id"] for item in payload["mutation_registry"]]
    if [item["mutation_id"] for item in results] != expected_ids:
        raise PillarSAdjudicationError("MUTATION_RESULTS_INCOMPLETE")
    payload["mutation_results"] = results
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


def _pytest(paths: tuple[str, ...], extra: tuple[str, ...] = ()) -> int:
    _activate_source_layout()
    import pytest

    return int(
        pytest.main(
            [
                "-p",
                "no:cacheprovider",
                "-q",
                *(str(ROOT / item) for item in paths),
                *extra,
            ]
        )
    )


def _build() -> int:
    try:
        _validate_output_destination_for_write()
    except PillarSAdjudicationError as exc:
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
        sys.stderr.write("tracked PR-286 receipt missing or not regular\n")
        return 1
    if OUTPUT.read_bytes() != expected:
        sys.stderr.write("tracked PR-286 receipt differs from exact replay\n")
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
    with tempfile.TemporaryDirectory(prefix="pr286-portable-") as temporary:
        clean_root = Path(temporary) / "source"
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
            "scripts/codex_harness/run_pr286_pillar_s_adjudication.py",
            "check",
        ]
        started = time.perf_counter()
        completed = subprocess.run(
            command,
            cwd=clean_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        elapsed = time.perf_counter() - started
        clean_after = _manifest(clean_root, tracked)
        source_after = _manifest(ROOT, tracked)
        if clean_after != clean_before or source_after != source_before:
            sys.stderr.write("portable replay changed tracked bytes\n")
            return 1
        evidence = {
            "schema": "PR286_PORTABLE_CLEAN_REPLAY_EVIDENCE_V1",
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("build", "check", "portable", "focused", "adjacent", "smoke"),
    )
    args = parser.parse_args(argv)
    if args.command == "build":
        return _build()
    if args.command == "check":
        return _check()
    if args.command == "portable":
        return _portable()
    if args.command == "focused":
        return _pytest((TEST_PATH,))
    if args.command == "adjacent":
        return _pytest((PR271_TEST_PATH, PR272_TEST_PATH, PR273_TEST_PATH))
    return _pytest(("tests",), ("-m", "smoke"))


if __name__ == "__main__":
    raise SystemExit(main())
