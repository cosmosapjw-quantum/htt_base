#!/usr/bin/env python3
"""Generate and validate the receipt-bearing PR-190 negative result."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Sequence


REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.comparator_attainability import (  # noqa: E402
    ProgrammeOutcome,
    SharpnessStatus,
    build_registered_typed_witnesses,
    evaluate_registered_attainability,
)


BASELINE_COMMIT = "7214ef7e91763ed807e0e350e1cfeffb82cec0f5"
BASELINE_TREE = "ca06887abc3f7c8dae94cbab08115fd061dfae09"
SPEC = REPO / "docs/research_program/strengthening/pr190_spec.yaml"
POLICY = REPO / "docs/research_program/strengthening/pr190_publication_policy.json"
MODULE = REPO / "htt/src/common/comparator_attainability.py"
CAS_DIR = REPO / "docs/research_program/strengthening/pr190_cas"
CAS_CONTRACT = CAS_DIR / "CAS_CONTRACT.json"
CAS_RUN_SPEC = CAS_DIR / "CAS_RUN_SPEC.json"
CAS_ADJUDICATION = CAS_DIR / "CAS_ADJUDICATION.json"
RESULT = REPO / "docs/generated/pr190_attainability/attainability_report.json"
REQUIRED_AXES = ("wolfram_xact", "sympy", "sage_singular", "lean")


class PR190RunnerError(RuntimeError):
    """Raised when the frozen PR-190 result cannot be reproduced."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PR190RunnerError(f"cannot load {path.relative_to(REPO)}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PR190RunnerError(f"{path.relative_to(REPO)} must contain an object")
    return payload


def _render(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _validate_cas_adjudication() -> dict[str, Any]:
    adjudication = _load_json(CAS_ADJUDICATION)
    contract = _load_json(CAS_CONTRACT)
    contract_hash = _sha256(CAS_CONTRACT)
    axes = tuple(adjudication.get("required_axes", ()))
    statuses = adjudication.get("axis_statuses")
    if tuple(contract.get("required_axes", ())) != REQUIRED_AXES:
        raise PR190RunnerError("CAS contract must require exactly the canonical four axes")
    if axes != REQUIRED_AXES:
        raise PR190RunnerError("CAS adjudication axis order or membership drifted")
    if adjudication.get("contract_sha256") != contract_hash:
        raise PR190RunnerError("CAS adjudication does not bind the current contract")
    if adjudication.get("aggregate_status") != "CAS_4AXIS_PASS":
        raise PR190RunnerError("PR-190 exact obstruction lacks CAS_4AXIS_PASS")
    if statuses != {axis: "PASS" for axis in REQUIRED_AXES}:
        raise PR190RunnerError("each canonical CAS axis must independently pass")
    if adjudication.get("missing_axes") or adjudication.get("exceptions_applied"):
        raise PR190RunnerError("PR-190 does not permit a missing axis or CAS exception")
    return {
        "adjudication": str(CAS_ADJUDICATION.relative_to(REPO)),
        "adjudication_sha256": _sha256(CAS_ADJUDICATION),
        "aggregate_status": adjudication["aggregate_status"],
        "axis_statuses": statuses,
        "contract": str(CAS_CONTRACT.relative_to(REPO)),
        "contract_sha256": contract_hash,
        "required_axes": list(REQUIRED_AXES),
        "verification_state": adjudication.get("verification_state"),
    }


def build_payload() -> dict[str, Any]:
    report = evaluate_registered_attainability(
        build_registered_typed_witnesses()
    )
    if (
        report.outcome
        is not ProgrammeOutcome.FULL_TYPED_DYNAMICAL_SHARPNESS_REFUTED
        or report.execution_resolution != "COMPLETED_FAILED_WITH_RECEIPT"
        or report.success_dependency_satisfied is not False
    ):
        raise PR190RunnerError("registered full-attainability statement was not fail-closed")
    refuted = [
        item.as_payload()
        for item in report.decisions
        if item.status is SharpnessStatus.REFUTED
    ]
    if len(refuted) != 2:
        raise PR190RunnerError("expected exactly the lower/interior constraint contradictions")
    report_payload = report.as_payload()
    return {
        "schema": "htt.pr190.comparator_attainability_result.v1",
        "pr_id": "PR-190",
        "metadata": {
            "baseline_commit": BASELINE_COMMIT,
            "baseline_tree": BASELINE_TREE,
            "claim_ceiling": "theorem_candidate",
            "data_admission_status": "NOT_APPLICABLE",
            "generated_from": {
                "module": {
                    "path": str(MODULE.relative_to(REPO)),
                    "sha256": _sha256(MODULE),
                },
                "policy": {
                    "path": str(POLICY.relative_to(REPO)),
                    "sha256": _sha256(POLICY),
                },
                "spec": {
                    "path": str(SPEC.relative_to(REPO)),
                    "sha256": _sha256(SPEC),
                },
            },
            "observed_data_executed": False,
            "owner": "BASS",
            "public_use": False,
            "transfer_source": "none",
        },
        "cas_evidence": _validate_cas_adjudication(),
        "result": {
            "report": report_payload,
            "report_id": report.report_id,
            "refuted_stage_count": len(refuted),
            "refuted_stages": refuted,
        },
        "scientific_disposition": {
            "capability_granted": False,
            "statement_weakened": False,
            "status": "REFUTED_REGISTERED_FULL_ATTAINABILITY_STATEMENT",
            "theorem_capability": "WITHHELD_PENDING_PR285",
        },
        "success_dependency_satisfied": False,
        "terminal": "COMPLETED_FAILED_WITH_RECEIPT",
    }


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    env["PYTHONPATH"] = os.pathsep.join(
        (str(REPO / "htt" / "src"), str(REPO / "htt"))
    )
    env.setdefault("OPENBLAS_NUM_THREADS", "4")
    return env


def _run(argv: Sequence[str], *, timeout: int) -> int:
    completed = subprocess.run(
        list(argv),
        cwd=REPO,
        env=_clean_env(),
        text=True,
        timeout=timeout,
        check=False,
    )
    return completed.returncode


def _run_cas() -> int:
    with tempfile.TemporaryDirectory(prefix="pr190-cas-") as temporary:
        observed = Path(temporary) / "adjudication.json"
        return_code = _run(
            (
                sys.executable,
                ".agent-harness/scripts/cas_gate.py",
                "run-adjudicate",
                "--contract",
                str(CAS_CONTRACT.relative_to(REPO)),
                "--run-spec",
                str(CAS_RUN_SPEC.relative_to(REPO)),
                "--out",
                str(observed),
            ),
            timeout=3700,
        )
        if return_code:
            return return_code
        fresh = _load_json(observed)
        tracked = _load_json(CAS_ADJUDICATION)
        stable_fields = (
            "aggregate_status",
            "axis_statuses",
            "contract_id",
            "contract_sha256",
            "errors",
            "exceptions_applied",
            "missing_axes",
            "required_axes",
            "risk_tier",
        )
        ok = all(fresh.get(key) == tracked.get(key) for key in stable_fields)
        print(
            json.dumps(
                {
                    "aggregate_status": fresh.get("aggregate_status"),
                    "mode": "cas",
                    "ok": ok,
                    "read_only": True,
                },
                sort_keys=True,
            )
        )
        return 0 if ok else 1


def _mode_command(mode: str) -> tuple[tuple[str, ...], int]:
    if mode == "focused":
        return (
            (
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "-q",
                "tests/pr_cards/test_pr_190_strengthen.py",
            ),
            900,
        )
    if mode == "adjacent":
        paths = [
            "tests/pr_cards/test_pr_189_strengthen.py",
            "tests/contracts/test_joint_anisotropy_state.py",
            "tests/contracts/test_orbit_catalogue_v3.py",
        ]
        existing = tuple(path for path in paths if (REPO / path).exists())
        return (
            (
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "-q",
                *existing,
                "-k",
                "not test_byte_stable",
            ),
            1200,
        )
    if mode == "smoke":
        return (
            (
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "-m",
                "smoke",
                "-q",
            ),
            900,
        )
    raise PR190RunnerError(f"unsupported command mode: {mode}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("generate", "check", "cas", "focused", "adjacent", "smoke"),
    )
    args = parser.parse_args(argv)

    if args.mode == "generate":
        payload = build_payload()
        RESULT.parent.mkdir(parents=True, exist_ok=True)
        RESULT.write_bytes(_render(payload))
        print(
            json.dumps(
                {
                    "mode": "generate",
                    "path": str(RESULT.relative_to(REPO)),
                    "terminal": payload["terminal"],
                },
                sort_keys=True,
            )
        )
        return 0
    if args.mode == "check":
        expected = _render(build_payload())
        ok = RESULT.exists() and RESULT.read_bytes() == expected
        print(
            json.dumps(
                {
                    "mode": "check",
                    "ok": ok,
                    "read_only": True,
                    "terminal": "COMPLETED_FAILED_WITH_RECEIPT",
                },
                sort_keys=True,
            )
        )
        return 0 if ok else 1
    if args.mode == "cas":
        return _run_cas()
    command, timeout = _mode_command(args.mode)
    return _run(command, timeout=timeout)


if __name__ == "__main__":
    raise SystemExit(main())
