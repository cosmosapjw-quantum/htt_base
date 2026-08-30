#!/usr/bin/env python3
"""Build the deterministic, map-free PMG-WU-009 reconciliation receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.observed_runs.planck_mes_wu009_contracts import run_self_check


DEFAULT_OUTPUT = REPO_ROOT / "docs/generated/planck_mes_wu009_reconciliation"
REPORTED_RAW_ROOT = Path("/mnt/sn850x2t/htt_base_e2e/workdir/raw")
PROTECTED_OUTPUT_ROOTS = tuple(
    REPO_ROOT / relative
    for relative in (
        "docs/generated/planck_pr3_paired300_irrep_carrier",
        "docs/generated/planck_mes_irrep_analysis",
        "docs/generated/planck_mes_smica_cmbonly_999_irrep",
        "docs/generated/planck_mes_irrep_injection_power",
        "docs/generated/planck_mes_first_paper",
        "papers/planck_mes_first_observation",
    )
)

PREDECESSOR_HASHES: dict[str, str] = {
    "docs/generated/planck_pr3_paired300_irrep_carrier/terminal.json": "bf82c1e2be03c9fe1c3ca8a4ef148a84be4d7b999cb31af5c617882fe1e0decb",
    "docs/generated/planck_pr3_paired300_irrep_carrier/metadata.json": "08be4f0ab0025969cb13b0cf4fed135ebfbc5fb2f0597ce0bfd0f1caf3f0721e",
    "docs/generated/planck_pr3_paired300_irrep_carrier/replay.json": "541b0dbbf26399efa429327af41019f2e9219cb5b3110eeafe4b80dce0948f68",
    "docs/generated/planck_pr3_paired300_irrep_carrier/artifact_manifest.json": "0b9c7472e72d001984da4d54968817be6d5738f0d93966e7faee546c38247da6",
    "docs/generated/planck_mes_smica_cmbonly_999_irrep/terminal.json": "a0adb549fd43be4f79386605d1cb40c9cda62627e260efcffa50540a536279fe",
    "docs/generated/planck_mes_smica_cmbonly_999_irrep/result.json": "7541835692c6fdf467b04d1cbaf11c50063448e39a24bee46767863802062548",
    "docs/generated/planck_mes_smica_cmbonly_999_irrep/replay.json": "89ae269d5222154152a5c8f453ae415855a623c9003e56381d153411cb766f41",
    "docs/generated/planck_mes_irrep_injection_power/terminal.json": "0126d55c050d01bd7a371ab9a8093fdb378e4c92f4f74c0656b90c1879a2b3d6",
    "docs/generated/planck_mes_irrep_injection_power/result.json": "bb7660700065e6f441a846a247ee2773acabc7bd837fe5409b95fb9589a01440",
    "docs/generated/planck_mes_irrep_injection_power/replay.json": "c05ab3f5c98957e09c9b592b217cd8973b9f15367a2d2997f98abd82abaae6e7",
    "docs/generated/planck_mes_irrep_injection_power/artifact_manifest.json": "4f4cbf3f7385531a9939c01307667a7c91544366cbd14bf2757ed3b1d02eae14",
    "docs/codex_handoff/planck_mes_extended_data_execution/DATA_AVAILABILITY_SNAPSHOT.yaml": "c07ecf66b0b581a0d421d945adad6f85294d9cdc5336e7d4e39ed6e7c5093bbc",
    "docs/codex_handoff/planck_mes_extended_data_execution/DATA_ROUTE_MATRIX.yaml": "2138624fd099dcc2b563e2e5dc4f880177333835a54f9ab06f75e2df2bbddffa",
}

AUTHORITY_HASHES: dict[str, str] = {
    "docs/superpowers/plans/2026-08-30-planck-mes-wu009-full-replay-theorem-reconciliation.md": "0a9e1c74dfe843ef4fac3c944ad8a8d05a6fb3daa61a5a8fcfc40bf0d5f90523",
    "docs/superpowers/specs/2026-08-30-planck-mes-wu009-full-replay-theorem-reconciliation-design.md": "0fd0fd545279337903fa941e2add03c7dd99eef109f286e1e8eed3d3800372a2",
    "docs/research_program/post_pr327/planck_mes_wu009_theorem_adjudication.json": "aeabb89ca8fae2f343d72e2933ada8f106a6f35864abc59ac6d7973e5f70ce62",
    "scripts/observed_runs/planck_mes_wu009_contracts.py": "a7eab06001a254874deadfbfab57e92090c21194d7891711fdd3e60e30388456",
}

EXPECTED_OUTPUT_FILES = (
    "authority_receipt.json",
    "contract_receipt.json",
    "reconciliation.json",
    "terminal.json",
    "artifact_manifest.json",
)
IMPLEMENTATION_INPUTS = (
    "scripts/observed_runs/run_planck_mes_wu009_reconciliation.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _guard_output(output: Path, raw_roots: Sequence[Path]) -> Path:
    resolved = output.resolve(strict=False)
    for raw_root in raw_roots:
        raw_resolved = Path(raw_root).resolve(strict=False)
        if resolved == raw_resolved or _is_within(resolved, raw_resolved):
            raise ValueError(f"output path is beneath declared raw root: {raw_resolved}")
    for protected_root in PROTECTED_OUTPUT_ROOTS:
        protected_resolved = protected_root.resolve(strict=False)
        if resolved == protected_resolved or _is_within(resolved, protected_resolved):
            raise ValueError(f"output path is beneath protected predecessor root: {protected_resolved}")
    return resolved


def _verify_identities(expected: Mapping[str, str]) -> dict[str, dict[str, Any]]:
    verified: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for relative, expected_sha in expected.items():
        path = REPO_ROOT / relative
        if not path.is_file():
            failures.append(f"missing:{relative}")
            continue
        actual = _sha256(path)
        if actual != expected_sha:
            failures.append(f"hash_mismatch:{relative}:{actual}")
            continue
        verified[relative] = {
            "byte_size": path.stat().st_size,
            "sha256": actual,
            "state": "MATCH",
        }
    if failures:
        raise RuntimeError("BLOCKED_BY_MOVED_AUTHORITY: " + "; ".join(failures))
    return verified


def _bind_current_identities(paths: Sequence[str]) -> dict[str, dict[str, Any]]:
    identities: dict[str, dict[str, Any]] = {}
    for relative in paths:
        path = REPO_ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"BLOCKED_BY_MOVED_AUTHORITY: missing:{relative}")
        identities[relative] = {
            "byte_size": path.stat().st_size,
            "sha256": _sha256(path),
            "state": "BOUND_CURRENT_SOURCE",
        }
    return identities


def _read_verified_json(relative: str, verified: Mapping[str, Any]) -> dict[str, Any]:
    if relative not in verified:
        raise RuntimeError(f"identity was not verified before read: {relative}")
    payload = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object: {relative}")
    return payload


def _build_payloads() -> dict[str, dict[str, Any]]:
    predecessor_identities = _verify_identities(PREDECESSOR_HASHES)
    authority_identities = _verify_identities(AUTHORITY_HASHES)
    implementation_identities = _bind_current_identities(IMPLEMENTATION_INPUTS)

    paired_terminal = _read_verified_json(
        "docs/generated/planck_pr3_paired300_irrep_carrier/terminal.json",
        predecessor_identities,
    )
    paired_metadata = _read_verified_json(
        "docs/generated/planck_pr3_paired300_irrep_carrier/metadata.json",
        predecessor_identities,
    )
    cmb_terminal = _read_verified_json(
        "docs/generated/planck_mes_smica_cmbonly_999_irrep/terminal.json",
        predecessor_identities,
    )
    cmb_result = _read_verified_json(
        "docs/generated/planck_mes_smica_cmbonly_999_irrep/result.json",
        predecessor_identities,
    )
    power_terminal = _read_verified_json(
        "docs/generated/planck_mes_irrep_injection_power/terminal.json",
        predecessor_identities,
    )
    power_result = _read_verified_json(
        "docs/generated/planck_mes_irrep_injection_power/result.json",
        predecessor_identities,
    )
    power_replay = _read_verified_json(
        "docs/generated/planck_mes_irrep_injection_power/replay.json",
        predecessor_identities,
    )

    family = cmb_result["paired300_sensitivity_comparison"]["OBSERVABLE_IRREP_ORBIT_V1"]
    cmb_family = cmb_result["family_results"]["OBSERVABLE_IRREP_ORBIT_V1"]
    if family["LEGACY_ABSOLUTE_MEDIAN_V1"]["paired300_rank"] != "27/301":
        raise RuntimeError("BLOCKED_BY_REPLAY_MISMATCH: WU006 historical family rank")
    null_ranks = [
        cmb_family["LEGACY_ABSOLUTE_MEDIAN_V1"]["global_rank"],
        cmb_family["LOO_ECDF_MIDRANK_V1"]["global_rank"],
    ]
    if null_ranks != ["61/1000", "55/1000"]:
        raise RuntimeError("BLOCKED_BY_REPLAY_MISMATCH: WU007 null-sensitivity ranks")
    required_terminal = {
        "state": "SUCCEEDED",
        "replay_status": "MATCH",
        "fresh_review": "PASS",
        "P0_remaining": 0,
        "P1_remaining": 0,
        "observation_used_for_power": False,
        "raw_maps_reopened": False,
        "claim_promotion": False,
    }
    if any(power_terminal.get(key) != value for key, value in required_terminal.items()):
        raise RuntimeError("BLOCKED_BY_REPLAY_MISMATCH: WU008 reviewed terminal")
    if power_result.get("state") != "EXECUTED_PENDING_REVIEW":
        raise RuntimeError("BLOCKED_BY_REPLAY_MISMATCH: WU008 embedded pre-terminal state")
    if power_replay.get("status") != "MATCH":
        raise RuntimeError("BLOCKED_BY_REPLAY_MISMATCH: WU008 map-free replay")

    contract_receipt = run_self_check(
        REPO_ROOT / "docs/research_program/post_pr327/planck_mes_wu009_theorem_adjudication.json"
    )
    if contract_receipt["status"] != "SUCCEEDED_NO_CLAIM_PROMOTION":
        raise RuntimeError("FAILED_CONTRACT_CHECK")

    authority_receipt = {
        "format": "PLANCK_MES_WU009_AUTHORITY_RECEIPT_V1",
        "identity_verification_order": "ALL_HASHES_VERIFIED_BEFORE_SCIENTIFIC_VALUES_READ",
        "predecessor_inputs": predecessor_identities,
        "authority_inputs": authority_identities,
        "implementation_inputs": implementation_identities,
        "parsed_predecessor_states": {
            "paired_carrier": {
                "row_count": paired_metadata["row_count"],
                "state": paired_terminal["state"],
                "replay_status": paired_terminal["replay_status"],
            },
            "cmbonly999": {
                "row_count": cmb_terminal["row_count"],
                "state": cmb_terminal["state"],
                "replay_status": cmb_terminal["replay_status"],
            },
            "injection_power": {
                "reviewed_terminal_state": power_terminal["state"],
                "embedded_result_state": power_result["state"],
                "replay_status": power_replay["status"],
            },
        },
        "raw_data_accessed": False,
    }

    reconciliation = {
        "format": "PLANCK_MES_WU009_MAP_FREE_RECONCILIATION_V1",
        "owner": "obsstat",
        "scope": "Committed-carrier theorem reconciliation with no new observed result",
        "claim_tier": "MAP_FREE_RECONCILIATION_NO_CLAIM_PROMOTION",
        "artifact_mode": "DETERMINISTIC_SUCCESSOR_RECEIPT",
        "transfer_source": "COMMITTED_PREDECESSOR_TEXT_ARTIFACTS_ONLY",
        "null_status": "HISTORICAL_POOL_SPECIFIC_VALUES_ONLY_NO_NEW_CALIBRATION",
        "covariance_status": "NO_NEW_COVARIANCE_INFERENCE",
        "generating_command": "python scripts/observed_runs/run_planck_mes_wu009_reconciliation.py --check",
        "historical_results": {
            "WU006": {
                "family": "OBSERVABLE_IRREP_ORBIT_V1",
                "family_rank": "27/301",
                "local_ranks": {"R_v0": "4/301", "R_v2": "4/301"},
                "interpretation": "HISTORICAL_FAMILY_AND_LOCAL_RANKS_DISTINCT",
            },
            "WU007": {
                "null_sensitivity_ranks": null_ranks,
                "reducers": ["LEGACY_ABSOLUTE_MEDIAN_V1", "LOO_ECDF_MIDRANK_V1"],
                "interpretation": "NULL_POOL_SENSITIVITY_NOT_INDEPENDENT_REPLICATION",
            },
            "WU008": {
                "reviewed_terminal_state": power_terminal["state"],
                "embedded_result_state": power_result["state"],
                "reconciliation": "STALE_EMBEDDED_PRE_TERMINAL_SUPERSEDED_BY_REVIEWED_TERMINAL",
                "scope": "OBSERVATION_BLIND_REGISTERED_200_REFERENCE_METHOD_POWER",
                "original_full301_full1000_calibrated": False,
                "arms_independent": False,
                "predecessor_rewritten": False,
            },
        },
        "lane_dispositions": {
            "tested": ["predecessor_identity", "task1_ledger", "bounded_pure_contracts", "historical_state_reconciliation"],
            "untested": ["corrected_observed_full_adaptation_rank"],
            "blocked": ["committed_carrier_gate_c", "formal_p01_p27"],
            "local_only": ["raw_replay", "cas_replay", "iqu_eb_replay"],
        },
        "lanes": {
            "predecessor_identity": "TESTED_PASS",
            "task1_contracts": "TESTED_PASS",
            "committed_carrier_gate_c": "NOT_IDENTIFIED_FROM_COMMITTED_CARRIER",
            "formal_p01_p27": "BLOCKED_BY_MISSING_THEOREM_DOSSIER",
            "raw_replay": "LOCAL_ONLY_NOT_EXECUTED",
            "cas_replay": "LOCAL_ONLY_NOT_EXECUTED",
            "iqu_eb_replay": "LOCAL_ONLY_NOT_EXECUTED",
        },
        "observed_result": {
            "computed": False,
            "rank": None,
            "score": None,
            "statistic": None,
            "state": "NO_ADMISSIBLE_NEW_RESULT",
        },
        "forbidden_uses": [
            "new observed rank or detection claim",
            "family or physical-cause identification",
            "same-sky independent replication claim",
            "formal P01-P27 replay claim",
        ],
        "overall_state": "SUCCEEDED_NO_CLAIM_PROMOTION",
    }
    terminal = {
        "format": "PLANCK_MES_WU009_MAP_FREE_RECONCILIATION_TERMINAL_V1",
        "state": "SUCCEEDED_NO_CLAIM_PROMOTION",
        "claim_promotion": False,
        "new_observed_result": False,
        "new_observed_rank": False,
        "raw_data_accessed": False,
        "raw_data_mutation": False,
        "predecessors_mutated": False,
        "formal_dossier_replayed": False,
        "bounded_implementation_review": {
            "state": "PENDING_INDEPENDENT_TASK2_REVIEW",
            "P0_remaining": None,
            "P1_remaining": None,
        },
        "next_executable_action": "LOCAL_GATE_D_USING_BOUND_HANDOFF_PACKAGE",
    }
    return {
        "authority_receipt.json": authority_receipt,
        "contract_receipt.json": contract_receipt,
        "reconciliation.json": reconciliation,
        "terminal.json": terminal,
    }


def generate_reconciliation(
    output: Path | str,
    *,
    raw_roots: Sequence[Path] = (REPORTED_RAW_ROOT,),
) -> Path:
    destination = _guard_output(Path(output), raw_roots)
    payloads = _build_payloads()
    rendered = {name: _canonical_json(payload) for name, payload in payloads.items()}
    manifest = {
        "format": "PLANCK_MES_WU009_RECONCILIATION_ARTIFACT_MANIFEST_V1",
        "predecessor_inputs": {
            path: {"sha256": sha256} for path, sha256 in sorted(PREDECESSOR_HASHES.items())
        },
        "authority_inputs": {
            path: {"sha256": sha256} for path, sha256 in sorted(AUTHORITY_HASHES.items())
        },
        "implementation_inputs": {
            path: {"sha256": _sha256(REPO_ROOT / path)}
            for path in sorted(IMPLEMENTATION_INPUTS)
        },
        "successor_outputs": {
            name: {
                "byte_size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for name, content in sorted(rendered.items())
        },
        "manifest_self_hash_excluded": True,
    }
    rendered["artifact_manifest.json"] = _canonical_json(manifest)
    destination.mkdir(parents=True, exist_ok=True)
    unexpected = {path.name for path in destination.iterdir()} - set(EXPECTED_OUTPUT_FILES)
    if unexpected:
        raise RuntimeError(f"refusing output directory with unexpected files: {sorted(unexpected)}")
    for name in EXPECTED_OUTPUT_FILES:
        (destination / name).write_bytes(rendered[name])
    return destination


def check_committed_output(output: Path | str = DEFAULT_OUTPUT) -> list[str]:
    committed = Path(output)
    if not committed.is_dir():
        return [f"missing committed successor directory: {committed}"]
    with tempfile.TemporaryDirectory(prefix="wu009-reconciliation-check-") as raw:
        generated = generate_reconciliation(Path(raw) / "generated")
        errors: list[str] = []
        actual_names = {path.name for path in committed.iterdir()}
        expected_names = set(EXPECTED_OUTPUT_FILES)
        if actual_names != expected_names:
            errors.append(
                f"file set differs: expected={sorted(expected_names)} actual={sorted(actual_names)}"
            )
        for name in sorted(expected_names & actual_names):
            if committed.joinpath(name).read_bytes() != generated.joinpath(name).read_bytes():
                errors.append(f"content drift: {name}")
        return errors


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--output", type=Path)
    parser.add_argument("--raw-root", action="append", type=Path, default=[])
    args = parser.parse_args(argv)
    raw_roots = tuple(args.raw_root) or (REPORTED_RAW_ROOT,)
    if args.check:
        errors = check_committed_output(DEFAULT_OUTPUT)
        if errors:
            for error in errors:
                print(error)
            return 1
        print("SUCCEEDED_NO_CLAIM_PROMOTION: committed reconciliation is deterministic")
        return 0
    generated = generate_reconciliation(args.output, raw_roots=raw_roots)
    print(generated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
