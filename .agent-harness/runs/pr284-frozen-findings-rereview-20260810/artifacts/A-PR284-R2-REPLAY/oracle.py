#!/usr/bin/env python3
"""Independent executable oracle for the frozen PR-284 R2 repair."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable

import yaml


ROOT = Path(__file__).resolve().parents[5]
RUN_ID = "pr284-frozen-findings-rereview-20260810"
ASSIGNMENT_ID = "A-PR284-R2-REPLAY"
OUTPUT = Path(__file__).resolve().parent / "oracle.json"


def _canonical_sha256(value: object, *, omit: set[str] | None = None) -> str:
    if omit and isinstance(value, dict):
        value = {key: item for key, item in value.items() if key not in omit}
    data = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _git(*argv: str, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        ["git", *argv], cwd=ROOT, input=input_bytes, check=False, capture_output=True
    )
    if completed.returncode:
        raise AssertionError(
            f"git {' '.join(argv)} failed: "
            f"{completed.stderr.decode('utf-8', errors='replace')}"
        )
    return completed.stdout


def _record(rows: list[dict[str, Any]], name: str, fn: Callable[[], Any]) -> None:
    rows.append({"check": name, "status": "PASS", "evidence": fn()})


def _candidate_and_patches() -> dict[str, Any]:
    seal = json.loads((ROOT / ".prguard/runtime/PR284_R2_CANDIDATE_SEAL.json").read_text())
    head = _git("rev-parse", "HEAD").decode().strip()
    tree = _git("rev-parse", "HEAD^{tree}").decode().strip()
    target = _git("rev-parse", seal["target_ref"]).decode().strip()
    merge_base = _git("merge-base", seal["target_ref"], head).decode().strip()
    assert head == seal["candidate_sha"]
    assert tree == seal["candidate_tree_sha"]
    assert target == seal["base_sha"] == seal["merge_base_sha"]
    assert merge_base == seal["merge_base_sha"]
    assert subprocess.run(["git", "diff", "--quiet"], cwd=ROOT).returncode == 0
    assert subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0

    expected = {
        row["stable_patch_id"]: row["commit"] for row in seal["stable_patch_ids"]
    }
    history = _git(
        "log", "-p", "--no-ext-diff", "--all", "--no-merges", "--pretty=format:commit %H"
    )
    patch_ids = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=ROOT,
        input=history,
        check=False,
        capture_output=True,
    )
    assert patch_ids.returncode == 0
    matches: dict[str, list[str]] = {patch_id: [] for patch_id in expected}
    for line in patch_ids.stdout.decode().splitlines():
        patch_id, commit = line.split()
        if patch_id in matches:
            matches[patch_id].append(commit)
    assert matches == {patch_id: [commit] for patch_id, commit in expected.items()}
    assert set(expected.values()) == set(seal["candidate_commits"])
    return {
        "candidate_sha": head,
        "candidate_tree_sha": tree,
        "target_ref": seal["target_ref"],
        "target_sha": target,
        "merge_base_sha": merge_base,
        "stable_patch_id_matches_across_all_refs": matches,
        "tracked_index_and_worktree_clean": True,
    }


def _fresh_receipt_and_mutations() -> dict[str, Any]:
    sys.path[:0] = [str(ROOT), str(ROOT / "htt/src"), str(ROOT / "htt")]
    from scripts.codex_harness import run_pr284_depth_path_doob as runner

    spec = yaml.safe_load(
        (ROOT / "docs/research_program/post_pr275/pr284_spec.yaml").read_text()
    )
    receipt = json.loads(
        (ROOT / "docs/generated/pr284_depth_path_doob_receipt.json").read_text()
    )
    assert receipt["receipt_content_sha256"] == _canonical_sha256(
        receipt, omit={"receipt_content_sha256"}
    )
    bindings = receipt["source_bindings"]
    assert [row["path"] for row in bindings] == spec["receipt_contract"]["required_bindings"]
    for row in bindings:
        assert hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest() == row["sha256"]

    fresh = runner._run_mutations()
    runner._validate_mutations(fresh)
    assert len(fresh) == len(spec["mutation_registry"]) == 14
    assert fresh == receipt["mutations"]
    assert [row["mutation_id"] for row in fresh] == [
        row["mutation_id"] for row in spec["mutation_registry"]
    ]
    assert all(
        row["activated"] is True and row["executed"] is True and row["killed"] is True
        for row in fresh
    )
    bypass = next(row for row in fresh if row["mutation_id"] == "MU284-REPORT-BUILDER-BYPASS")
    assert bypass["observed_reason"] == "CALLER_SUPPLIED_PROVED_REPORT_REJECTED"
    return {
        "receipt_content_sha256": receipt["receipt_content_sha256"],
        "source_binding_count": len(bindings),
        "fresh_mutation_count": len(fresh),
        "fresh_mutation_ids": [row["mutation_id"] for row in fresh],
        "all_fresh_mutations_activated_executed_killed": True,
        "bypass_row": bypass,
    }


def _historical_builder_bypass_dies_before_calibration() -> dict[str, Any]:
    sys.path[:0] = [str(ROOT), str(ROOT / "htt/src"), str(ROOT / "htt")]
    from common.depth_path import DepthPathError
    from common.depth_path_calibration import (
        ReverseMartingalePremiseStatus,
        _build_depth_path_reverse_martingale_report_contract,
        build_depth_path_finite_target_law,
    )
    from htt.infer.depth_path_calibration import build_depth_path_doob_calibration
    from scripts.codex_harness import run_pr284_depth_path_doob as runner

    path = runner._path()
    threshold = runner._threshold()
    law = build_depth_path_finite_target_law(
        law_id="R2-HISTORICAL-FORGED-LAW",
        common_target_id="R2-NONCENTERED-TARGET",
        atom_ids=("atom-a", "atom-b", "atom-c", "atom-d"),
        weights=(Fraction(1, 4),) * 4,
        common_target=(0, 1, 2, 3),
        registration_id="sha256:r2-historical-forged-law",
    )
    selection = runner._selection(law)
    calibration_attempted = False
    try:
        forged = _build_depth_path_reverse_martingale_report_contract(
            report_id="R2-HISTORICAL-FORGED-REPORT",
            path_content_id=path.content_id,
            stratum_content_ids=tuple(stratum.content_id for stratum in path.strata),
            threshold_contract=threshold,
            filtration_id="sha256:r2-forged-filtration",
            filtration_direction="DECREASING",
            preprocessing_id="sha256:common-preprocessing-v1",
            estimator_id="sha256:conditional-estimator-v1",
            premise_evidence_id="sha256:caller-supplied-proof",
            premise_status=ReverseMartingalePremiseStatus.PROVED_FINITE_REGISTERED_PATH,
            finite_target_law=law,
            selection_contract=selection,
            path_partitions=(
                ("left", "left", "right", "right"),
                ("x", "y", "x", "y"),
                ("all", "all", "all", "all"),
            ),
            sigma_field_ids=("sigma-1", "sigma-2", "sigma-3"),
            path_values=(Fraction(0), Fraction(0), Fraction(0)),
            path_maximum_abs=Fraction(0),
            path_maximum_content_id="sha256:caller-supplied-maximum",
            target_second_moment=Fraction(1),
            exact_tower_equalities=(True, True),
            exact_tower_report_content_id="sha256:caller-supplied-tower",
            unresolved_reasons=(),
            matched_mock_plan=None,
        )
        calibration_attempted = True
        build_depth_path_doob_calibration(
            calibration_id="R2-MUST-NOT-CALIBRATE",
            report=forged,
            threshold_contract=threshold,
        )
    except DepthPathError as exc:
        rejection = str(exc)
    else:
        raise AssertionError("historical report-builder bypass survived")
    assert calibration_attempted is False
    assert "exactly centered" in rejection
    return {
        "report_constructed": False,
        "calibration_attempted": calibration_attempted,
        "rejection": rejection,
        "rejected_stage": "DepthPathReverseMartingaleReport.__post_init__ premise replay",
    }


def _human_only_merge_refusal() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / ".agent-harness/scripts"))
    import _harness
    from publication_integrity import PublicationIntegrityError, classify_publication_command

    status = yaml.safe_load((ROOT / "docs/codex_handoff/pr_status.yaml").read_text())
    policy = json.loads(
        (ROOT / "docs/research_program/post_pr275/pr284_publication_policy.json").read_text()
    )
    stack = status["stacked_pr_execution"]
    assert stack["execution_mode"] == "AUTO_STACKED_PR"
    assert stack["merge_policy"] == "HUMAN_ONLY"
    _harness.validate_execution_mode(stack["execution_mode"])
    try:
        _harness.validate_execution_mode("AUTO_MERGE")
    except PublicationIntegrityError as exc:
        rejection = str(exc)
    else:
        raise AssertionError("AUTO_MERGE was accepted")
    assert classify_publication_command("gh pr merge 380 --merge")[0] is True
    assert policy["ordinary_agent_pr_mutation_forbidden"] is True
    assert "merge" in policy["attended_publication"]["forbidden_actions"]
    return {
        "execution_mode": stack["execution_mode"],
        "merge_policy": stack["merge_policy"],
        "auto_merge_rejection": rejection,
        "merge_command_classified_forbidden": True,
        "attended_policy_forbids_merge": True,
    }


def main() -> int:
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    for name, fn in (
        ("frozen_candidate_target_and_patch_uniqueness", _candidate_and_patches),
        ("fresh_receipt_and_fourteen_mutations", _fresh_receipt_and_mutations),
        ("historical_builder_bypass_dies_before_calibration", _historical_builder_bypass_dies_before_calibration),
        ("human_only_merge_refusal", _human_only_merge_refusal),
    ):
        try:
            _record(checks, name, fn)
        except BaseException as exc:
            checks.append({"check": name, "status": "FAIL", "evidence": {}})
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
    payload = {
        "schema": "PR284_R2_ASSIGNMENT_LOCAL_REPLAY_ORACLE_V1",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "candidate_sha": _git("rev-parse", "HEAD").decode().strip(),
        "status": "PASS" if not errors else "FAIL",
        "checks": checks,
        "errors": errors,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
