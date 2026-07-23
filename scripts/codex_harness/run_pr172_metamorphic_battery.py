#!/usr/bin/env python3
"""Generate or check the fail-closed PR-172 metamorphic result pack."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt/src"))
sys.path.insert(0, str(REPO / "htt"))

from htt.metamorphic_symmetry import (  # noqa: E402
    build_battery,
    validate_battery,
)


SPEC = Path("docs/research_program/long_horizon_rescue/pr172_spec.yaml")
RUNNER = Path("scripts/codex_harness/run_pr172_metamorphic_battery.py")
OUTPUTS = {
    "registry": Path("docs/generated/pr172_metamorphic_relation_registry.json"),
    "result": Path("docs/generated/pr172_metamorphic_result.json"),
    "mutations": Path("docs/generated/pr172_mutation_report.json"),
    "replay": Path("docs/generated/pr172_replay_receipt.json"),
    "co04": Path("docs/generated/pr172_co04_delta.json"),
    "card": Path("docs/generated/pr172_result_card.json"),
    "manifest": Path("docs/generated/pr172_artifact_manifest.json"),
}


def _render(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _load_spec() -> dict[str, Any]:
    value = yaml.safe_load((REPO / SPEC).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("PR-172 spec must be a YAML object")
    return value


def _metadata(spec: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    return {
        "pr_id": "PR-172",
        "claim_id": "C-PR172-METAMORPHIC-CONSISTENCY",
        "owner": "COMMON",
        "contributors": ["OBSSTAT"],
        "implementation_scope": "common",
        "claim_tier": "exploratory",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
        "scientific_artifact_mode": "standard_internal",
        "scientific_status": "OPEN",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": result["config_hash"],
        "sky_support_status": "synthetic_fixture_not_observed_sky",
        "mask_status": "not_applicable_synthetic_fixture",
        "covariance_status": "mechanics_only_not_covariance_validation",
        "null_mock_status": "not_run_not_applicable",
        "generating_command": (
            "PYTHONPATH=htt/src:htt venv/bin/python -B "
            "scripts/codex_harness/run_pr172_metamorphic_battery.py --write"
        ),
        "git_commit": result["git_commit"],
        "worktree_content_receipt": result["worktree_content_receipt"],
        "worktree_state": result["worktree_state"],
        "runtime_environment": result["runtime_environment"],
    }


def _fresh_replay() -> list[str]:
    command = [sys.executable, "-B", str(REPO / RUNNER), "--emit-semantic"]
    env = os.environ.copy()
    env.update(
        {
            "PYTHONHASHSEED": "0",
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "PYTHONPATH": os.pathsep.join([str(REPO / "htt/src"), str(REPO / "htt")]),
        }
    )
    digests: list[str] = []
    for _ in range(2):
        completed = subprocess.run(
            command,
            cwd=REPO,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stdout + completed.stderr)
        lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        if len(lines) != 1 or len(lines[0]) != 64:
            raise RuntimeError(f"invalid semantic replay output: {completed.stdout!r}")
        digests.append(lines[0])
    return digests


def build_outputs(spec: dict[str, Any]) -> tuple[dict[Path, bytes], dict[str, Any]]:
    result = build_battery(spec, REPO)
    validation_errors = validate_battery(result, spec, REPO)
    if validation_errors:
        raise ValueError("invalid generated battery: " + "; ".join(validation_errors))
    metadata = _metadata(spec, result)
    input_hashes = result["input_hashes"]
    common = {**metadata, "input_hashes": input_hashes}

    registry = {
        "schema": "htt.pr172.metamorphic_registry.v1",
        **common,
        "source_bindings": spec["source_bindings"],
        "conventions": spec["conventions"],
        "fixtures": spec["fixtures"],
        "transforms": spec["transforms"],
        "tolerances": spec["tolerances"],
        "relations": spec["relations"],
        "mutation_registry": spec["mutation_registry"],
        "lineage": spec["lineage"],
        "caveats": [
            "The registry freezes software relations, not physical validation targets.",
            "The physical B-parity action is explicitly underdefined and not tested.",
        ],
    }

    mutation_rows = result["mutations"]
    mutation_report = {
        "schema": "htt.pr172.mutation_report.v1",
        **common,
        "registered_count": len(spec["mutation_registry"]),
        "executed_count": sum(
            1
            for row in mutation_rows
            if row["execution_receipt"]["invoked"] is True
            and row["execution_receipt"]["invocation_count"] == 1
        ),
        "killed_count": sum(1 for row in mutation_rows if row["killed"]),
        "survivors": [row["mutation_id"] for row in mutation_rows if not row["killed"]],
        "mutations": mutation_rows,
        "all_registered_mutants_killed": all(row["killed"] for row in mutation_rows),
        "caveats": [
            "Mutation kills validate only the registered finite falsifiers.",
            "A clean relation failure takes precedence over a zero-survivor mutation result.",
        ],
    }

    replay_digests = _fresh_replay()
    replay = {
        "schema": "htt.pr172.deterministic_replay.v1",
        **common,
        "fresh_processes": 2,
        "environment": spec["deterministic_replay"]["environment"],
        "semantic_digests": replay_digests,
        "digests_match": len(set(replay_digests)) == 1,
        "semantic_digest": result["semantic_digest"],
        "volatile_exclusions": spec["deterministic_replay"]["excluded_volatile_fields"],
        "caveats": ["Deterministic replay is reproducibility evidence from the same implementation lineage."],
    }
    if not replay["digests_match"] or replay_digests[0] != result["semantic_digest"]:
        raise ValueError("fresh-process semantic replay mismatch")

    co04 = {
        "schema": "htt.pr172.co04_delta.v1",
        **common,
        "upstream": "PR-123/CO-04",
        "lineage_kind": "same-production-adapter metamorphic pair",
        "independent_numerical_oracle_count": 0,
        "base_and_transformed_runs_count_as_two_oracles": False,
        "pr123_reference_code_or_fixture_reused": False,
        "delta": [
            {"surface": "CF4 frame covariance", "classification": "new anisotropy-specific metamorphic relation", "relation_ids": ["MR172-CF4-SO3-001", "MR172-CF4-AXISPERM-002"]},
            {"surface": "CF4 response/projection", "classification": "new typed transform relation", "relation_ids": ["MR172-CF4-QUADRATIC-003", "MR172-CF4-MONOPOLE-004"]},
            {"surface": "B projector", "classification": "new convention-scoped index and documented-contract checks", "relation_ids": ["MR172-B-INDEX-ODD-005", "MR172-B-SUPPORT-006", "MR172-B-M0-CANCEL-007", "MR172-B-AXISYM-DOC-008"]},
            {"surface": "mutation discipline", "classification": "extended precedent; no mutation kill is double-counted", "relation_ids": []},
        ],
        "caveats": [
            "PR-172 does not claim a second oracle, independent implementation, or external replication.",
            "The same estimator is evaluated on correlated transformed fixtures.",
        ],
    }

    relation_lookup = {row["relation_id"]: row for row in result["relations"]}
    failed = [row["relation_id"] for row in result["relations"] if not row["passed"]]
    axisym_metric = relation_lookup["MR172-B-AXISYM-DOC-008"]["metrics"][0]
    card = {
        "schema": "htt.pr172.result_card.v1",
        **common,
        "process_execution_status": "PASS_REPRODUCIBLE_TERMINAL_EVIDENCE",
        "success_dependency_satisfied": result["terminal"] == "PASS_METAMORPHIC_SELF_CONSISTENCY_C1",
        "terminal": result["terminal"],
        "scientific_result": "DOCUMENTED_AXISYMMETRIC_CALLABLE_CONTRACT_FALSIFIED_ON_REGISTERED_FIXTURE",
        "cf4_estimator_result": result["adapter_status"]["cf4_estimator"],
        "b_projector_result": result["adapter_status"]["b_projector"],
        "clean_relations_passed": sum(1 for row in result["relations"] if row["passed"]),
        "clean_relations_total": len(result["relations"]),
        "failed_relation_ids": failed,
        "documented_axisymmetric_zero_max_abs": axisym_metric["value"],
        "documented_axisymmetric_zero_required": axisym_metric["threshold"],
        "physical_b_parity_status": "UNDERDEFINED_NOT_TESTED",
        "mutation_survivors": mutation_report["survivors"],
        "allowed_interpretation": (
            "The CF4 estimator passed its four frozen transform relations. The B projector passed three coded index relations but failed its documented unconditional axisymmetric-zero callable invariant on the registered shape-valid fixture."
        ),
        "forbidden_interpretation": (
            "This result is not a physical sky-parity violation, observed anisotropy, covariance validation, transfer validation, or Bianchi-family evidence."
        ),
        "caveats": [
            "The B failure is a callable contract/implementation disagreement.",
            "The physical spin-harmonic parity action remains underdefined.",
            "PR-180's requires_success edge is not satisfied by this blocked result.",
        ],
    }

    rendered: dict[Path, bytes] = {
        OUTPUTS["registry"]: _render(registry),
        OUTPUTS["result"]: _render(result),
        OUTPUTS["mutations"]: _render(mutation_report),
        OUTPUTS["replay"]: _render(replay),
        OUTPUTS["co04"]: _render(co04),
        OUTPUTS["card"]: _render(card),
    }
    artifacts = [
        {
            "path": str(path),
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        }
        for path, data in rendered.items()
    ]
    manifest = {
        "schema": "htt.pr172.artifact_manifest.v1",
        **common,
        "terminal": result["terminal"],
        "success_dependency_satisfied": card["success_dependency_satisfied"],
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "allowed_uses": result["allowed_uses"],
        "forbidden_uses": result["forbidden_uses"],
        "caveats": card["caveats"],
    }
    rendered[OUTPUTS["manifest"]] = _render(manifest)
    return rendered, card


def _check_outputs(expected: dict[Path, bytes]) -> list[str]:
    mismatches: list[str] = []
    for relative, data in expected.items():
        path = REPO / relative
        if not path.is_file():
            mismatches.append(f"missing:{relative}")
        elif path.read_bytes() != data:
            mismatches.append(f"stale:{relative}")
    return mismatches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--emit-semantic", action="store_true")
    args = parser.parse_args(argv)
    spec = _load_spec()
    if args.emit_semantic:
        result = build_battery(spec, REPO)
        errors = validate_battery(result, spec, REPO)
        if errors:
            print("; ".join(errors), file=sys.stderr)
            return 2
        print(result["semantic_digest"])
        return 0
    expected, card = build_outputs(spec)
    if args.write or not args.check:
        for relative, data in expected.items():
            _write(REPO / relative, data)
    mismatches = _check_outputs(expected) if args.check else []
    print(
        json.dumps(
            {
                "ok": not mismatches,
                "terminal": card["terminal"],
                "scientific_result": card["scientific_result"],
                "mismatches": mismatches,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if not mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())
