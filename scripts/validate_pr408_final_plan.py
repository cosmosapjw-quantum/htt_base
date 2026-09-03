#!/usr/bin/env python3
"""Validate the final PR-408 survivor-closeout planning package.

This is a direct consumer of the machine-readable planning documents.  It does
not adjudicate mathematical truth and it does not execute any future work unit.
It checks that the plan is structurally complete, risk-scoped, append-only in
its declared dependency order, and mechanically reviewable before a weaker
implementation agent receives it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Mapping

import yaml

REPO = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO / "docs/codex_handoff/pr408_final"
AUDIT = REPO / "docs/research_program/theory_promotion/audits/PR408_FINAL_ADVERSARIAL_AUDIT.md"
HANDOFF = REPO / "docs/codex_handoff/PR408_FINAL_CODEX_HANDOFF.md"
BASE_SHA = "bdad91a204c424030cd6d0e562232b6965a42900"
EXPECTED_WU_IDS = tuple(f"WU-{index:03d}" for index in range(1, 8))
REQUIRED_WU_KEYS = {
    "schema",
    "id",
    "title",
    "authority",
    "objective",
    "risk",
    "scope",
    "preconditions",
    "invariants",
    "failure_modes",
    "implementation",
    "verification",
    "completion_evidence",
    "agent_policy",
    "review_gate",
}
FORBIDDEN_CHANGED_PREFIXES = (
    "docs/codex_handoff/pr_backlog.",
    "docs/codex_handoff/pr_status.",
    "machine_readable/pr_backlog.",
    "machine_readable/pr_status.",
    "data/canonical/",
    "htt/obsstat/",
    "htt/src/common/",
)
ALLOWED_NON_DOC_PATHS = {
    "scripts/validate_pr408_final_plan.py",
    "tests/contracts/test_pr408_final_plan.py",
}


class PlanValidationError(ValueError):
    """Raised when the planning package violates its executable contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PlanValidationError(message)


def _load_yaml(path: Path) -> Mapping[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    _require(isinstance(payload, dict), f"{path}: top level must be a mapping")
    return payload


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _detection_is_nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_detection_is_nonempty(item) for item in value.values())
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return any(_detection_is_nonempty(item) for item in value)
    return value is not None


def validate_work_unit(payload: Mapping[str, Any], *, expected_id: str, previous_id: str | None) -> None:
    missing = sorted(REQUIRED_WU_KEYS - set(payload))
    _require(not missing, f"{expected_id}: missing required keys {missing}")
    _require(payload["schema"] == "audit-compiled-work-unit/v1", f"{expected_id}: wrong schema")
    _require(payload["id"] == expected_id, f"{expected_id}: id mismatch")

    authority = payload["authority"]
    _require(isinstance(authority, dict), f"{expected_id}: authority must be a mapping")
    dependencies = authority.get("upstream_dependencies", [])
    _require(isinstance(dependencies, list), f"{expected_id}: upstream_dependencies must be a list")
    if previous_id is not None:
        _require(previous_id in dependencies, f"{expected_id}: must depend on {previous_id}")
    _require(authority.get("branch") == "ALLOCATE_FROM_LIVE_DAG", f"{expected_id}: branch must be allocated from live DAG")

    risk = payload["risk"]
    _require(isinstance(risk, dict), f"{expected_id}: risk must be a mapping")
    declared_modes = payload["failure_modes"]
    _require(isinstance(declared_modes, list), f"{expected_id}: failure_modes must be a list")
    mode_by_id: dict[str, Mapping[str, Any]] = {}
    for mode in declared_modes:
        _require(isinstance(mode, dict), f"{expected_id}: each failure mode must be a mapping")
        mode_id = mode.get("id")
        _require(isinstance(mode_id, str) and mode_id, f"{expected_id}: failure mode id missing")
        _require(mode_id not in mode_by_id, f"{expected_id}: duplicate failure mode {mode_id}")
        _require(mode.get("severity") in {"P0", "P1", "P2", "P3"}, f"{expected_id}: invalid severity for {mode_id}")
        _require(_detection_is_nonempty(mode.get("required_detection")), f"{expected_id}: {mode_id} has no executable detector/assertion")
        mode_by_id[mode_id] = mode

    for severity, key in (("P0", "P0_failure_modes"), ("P1", "P1_failure_modes")):
        listed = risk.get(key, [])
        _require(isinstance(listed, list), f"{expected_id}: {key} must be a list")
        for mode_id in listed:
            _require(mode_id in mode_by_id, f"{expected_id}: {key} references missing {mode_id}")
            _require(mode_by_id[mode_id]["severity"] == severity, f"{expected_id}: {mode_id} severity mismatch")

    invariants = payload["invariants"]
    _require(isinstance(invariants, list) and invariants, f"{expected_id}: invariants must be non-empty")
    for invariant in invariants:
        _require(isinstance(invariant, dict), f"{expected_id}: invariant must be a mapping")
        severity = invariant.get("severity_if_violated")
        _require(severity in {"P0", "P1", "P2", "P3"}, f"{expected_id}: invalid invariant severity")
        if severity in {"P0", "P1"}:
            _require(_detection_is_nonempty(invariant.get("mechanical_check")), f"{expected_id}: load-bearing invariant lacks mechanical_check")

    review_gate = payload["review_gate"]
    _require(isinstance(review_gate, dict), f"{expected_id}: review_gate must be a mapping")
    _require(review_gate.get("fresh_context_required") is True, f"{expected_id}: fresh-context review must be required")
    _require(review_gate.get("pass_condition") == {"P0": 0, "P1": 0}, f"{expected_id}: pass condition must be P0=P1=0")

    policy = payload["agent_policy"]
    _require(isinstance(policy, dict), f"{expected_id}: agent_policy must be a mapping")
    _require(policy.get("ask_user_questions") is False, f"{expected_id}: ask_user_questions must be false")
    _require(policy.get("guessing_across_spec_boundary") == "forbidden", f"{expected_id}: guessing must be forbidden")
    _require(policy.get("suppressing_failures") == "forbidden", f"{expected_id}: failure suppression must be forbidden")


def _changed_paths() -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "diff", "--name-only", f"{BASE_SHA}..HEAD"],
        cwd=REPO,
        check=True,
        text=True,
        capture_output=True,
    )
    return tuple(line.strip() for line in completed.stdout.splitlines() if line.strip())


def validate_changed_surface(paths: Iterable[str]) -> None:
    for path in paths:
        _require(not path.startswith(FORBIDDEN_CHANGED_PREFIXES), f"forbidden planning-PR path changed: {path}")
        if path.startswith("docs/") or path in ALLOWED_NON_DOC_PATHS:
            continue
        _require(False, f"unexpected non-document planning path: {path}")


def validate_package() -> dict[str, Any]:
    _require(AUDIT.is_file(), "final adversarial audit is missing")
    _require(HANDOFF.is_file(), "final Codex handoff is missing")
    _require(PACKAGE_ROOT.is_dir(), "final package directory is missing")

    work_units: list[Mapping[str, Any]] = []
    for index, work_unit_id in enumerate(EXPECTED_WU_IDS):
        path = PACKAGE_ROOT / f"{work_unit_id}.yaml"
        _require(path.is_file(), f"missing {path}")
        payload = _load_yaml(path)
        validate_work_unit(payload, expected_id=work_unit_id, previous_id=EXPECTED_WU_IDS[index - 1] if index else None)
        work_units.append(payload)

    index_path = PACKAGE_ROOT / "PACKAGE_INDEX.yaml"
    _require(index_path.is_file(), "PACKAGE_INDEX.yaml is missing")
    package_index = _load_yaml(index_path)
    index_text = index_path.read_text(encoding="utf-8")
    for work_unit_id in EXPECTED_WU_IDS:
        _require(work_unit_id in index_text, f"PACKAGE_INDEX omits {work_unit_id}")

    threat_catalog = REPO / "docs/codex_handoff/theory_promotion_closeout/P0_P1_THREAT_CATALOG.json"
    _require(threat_catalog.is_file(), "threat catalog is missing")
    threat_payload = _load_json(threat_catalog)
    _require(isinstance(threat_payload, dict) and isinstance(threat_payload.get("findings"), list), "threat catalog has invalid shape")
    _require(any(item.get("severity") == "P0" for item in threat_payload["findings"]), "threat catalog contains no P0")
    _require(any(item.get("severity") == "P1" for item in threat_payload["findings"]), "threat catalog contains no P1")

    handoff_text = HANDOFF.read_text(encoding="utf-8")
    _require("No further planning successor" in handoff_text or "another_planning_successor" in handoff_text, "anti-meta terminal boundary is missing")
    _require("BLOCKED_BY_UNRESOLVED_SPEC" in handoff_text, "unresolved-spec STOP is missing")

    changed = _changed_paths()
    validate_changed_surface(changed)

    hashes = {
        path.relative_to(REPO).as_posix(): _sha256(path)
        for path in sorted(
            [AUDIT, HANDOFF, index_path, threat_catalog]
            + [PACKAGE_ROOT / f"{work_unit_id}.yaml" for work_unit_id in EXPECTED_WU_IDS]
        )
    }
    return {
        "schema": "htt.pr408_final_plan_validation.v1",
        "status": "PASS",
        "work_unit_ids": list(EXPECTED_WU_IDS),
        "work_unit_count": len(work_units),
        "changed_paths": list(changed),
        "content_sha256": hashes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit canonical JSON")
    args = parser.parse_args(argv)
    try:
        result = validate_package()
    except (PlanValidationError, OSError, subprocess.CalledProcessError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"PR408_PLAN_INVALID: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    else:
        print(f"PASS: {result['work_unit_count']} work units; {len(result['changed_paths'])} changed paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
