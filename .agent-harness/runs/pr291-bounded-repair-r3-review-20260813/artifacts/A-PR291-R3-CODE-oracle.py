#!/usr/bin/env python3
"""Independent hostile invariant oracle for the frozen PR-291 candidate.

All mutations occur below a TemporaryDirectory allocated outside the repository.
The script imports production code only from the frozen worktree and does not use
the repository integration tests as an oracle.
"""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO, StringIO
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import types

import yaml


REPO = Path(__file__).resolve().parents[4]
RUNNER_PATH = REPO / "scripts/codex_harness/run_pr291_cf4_lane.py"
EXPECTED_ROLES = (
    "catalogue",
    "row_selection",
    "covariance",
    "frame_definition",
    "sign_convention",
    "units_contract",
    "grouping_definition",
    "depth_definition",
    "zoa_definition",
)


def load_runner() -> object:
    spec = importlib.util.spec_from_file_location("pr291_r3_independent_oracle", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clone_bound_root(runner: object, destination: Path) -> None:
    for source in runner.BOUND_SOURCES:
        relative = source.relative_to(runner.ROOT)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def quiet_write(runner: object, *, root: Path, output: Path | None = None) -> int:
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
        return runner._write(root=root, output=output)


def require_preflight_refusal(
    runner: object,
    *,
    root: Path,
    output: Path,
    label: str,
) -> None:
    original_build = runner._build
    reached_payload = False

    def forbidden_build(*_args: object, **_kwargs: object) -> object:
        nonlocal reached_payload
        reached_payload = True
        raise AssertionError(f"{label}: payload construction ran")

    runner._build = forbidden_build
    try:
        assert quiet_write(runner, root=root, output=output) == 1, label
    finally:
        runner._build = original_build
    assert not reached_payload, label


def archive_refusals(runner: object, scratch: Path) -> list[str]:
    killed: list[str] = []
    for label, member in (
        ("archive_traversal", tarfile.TarInfo("../escape.txt")),
        ("archive_symlink", tarfile.TarInfo("link")),
    ):
        payload = BytesIO()
        if label == "archive_traversal":
            member.size = 1
            data = BytesIO(b"x")
        else:
            member.type = tarfile.SYMTYPE
            member.linkname = "../escape.txt"
            data = None
        with tarfile.open(fileobj=payload, mode="w") as archive:
            archive.addfile(member, data)
        payload.seek(0)
        destination = scratch / label
        destination.mkdir()
        with tarfile.open(fileobj=payload, mode="r:") as archive:
            try:
                runner._safe_extract_archive(archive, destination)
            except RuntimeError:
                killed.append(label)
            else:
                raise AssertionError(f"{label} was accepted")
        assert not (scratch / "escape.txt").exists()
    return killed


def atomic_invariants(runner: object, root: Path) -> list[str]:
    bindings = runner._base_source_bindings(root)
    transaction = runner._load_transaction_module(
        root,
        expected_sha256=bindings[
            runner.PR290_TRANSACTION_RUNNER.relative_to(runner.ROOT).as_posix()
        ],
    )
    resolved = (root / runner.PR290_TRANSACTION_RUNNER.relative_to(runner.ROOT)).resolve()
    for symbol in runner._TRANSACTION_SYMBOLS:
        function = getattr(transaction, symbol)
        assert callable(function)
        assert Path(function.__code__.co_filename).resolve() == resolved

    safe_parent = root / "oracle-safe"
    safe_parent.mkdir()
    safe_output = safe_parent / "receipt.json"
    safe_payload = b'{"oracle":"safe"}\n'
    transaction._atomic_write(
        safe_output,
        safe_payload,
        root=root,
        observed_result_directory=root / "oracle-results",
    )
    assert safe_output.read_bytes() == safe_payload

    race_parent = root / "oracle-race"
    race_parent.mkdir()
    race_output = race_parent / "receipt.json"
    displaced = root / "oracle-race-displaced"
    outside = root.parent / "oracle-race-outside"
    outside.mkdir(exist_ok=True)
    original_validate = transaction._validate_output_destinations
    calls = 0

    def race_validate(**kwargs: object) -> None:
        nonlocal calls
        original_validate(**kwargs)
        calls += 1
        if calls == 1:
            race_parent.rename(displaced)
            race_parent.symlink_to(outside, target_is_directory=True)

    transaction._validate_output_destinations = race_validate
    try:
        try:
            transaction._atomic_write(
                race_output,
                b"forbidden-race-write",
                root=root,
                observed_result_directory=root / "oracle-results",
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError("parent race was accepted")
    finally:
        transaction._validate_output_destinations = original_validate
    assert not (outside / race_output.name).exists()
    assert not (displaced / race_output.name).exists()
    assert not any(path.name.startswith(".receipt.json.") for path in displaced.iterdir())
    return ["transaction_callable_origin", "atomic_safe_write", "parent_race_refused"]


def main() -> None:
    runner = load_runner()
    repo_resolved = REPO.resolve(strict=True)
    checks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="pr291-r3-code-oracle-") as temporary:
        scratch = Path(temporary).resolve(strict=True)
        assert scratch != repo_resolved and not scratch.is_relative_to(repo_resolved)

        baseline = scratch / "baseline"
        clone_bound_root(runner, baseline)
        first = runner._build(baseline)
        second = runner._build(baseline)
        frozen = json.loads(runner.OUTPUT.read_text(encoding="utf-8"))
        assert first == second == frozen
        assert first["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
        assert first["numeric_outputs_written"] == []
        assert first["observed_data_executed"] is False
        assert not (baseline / runner.OBSERVED_RESULT_DIRECTORY.relative_to(runner.ROOT)).exists()
        snapshot = first["decision"]["data_identity_snapshot"]
        assert snapshot["canonical_record_replay"] is True
        assert snapshot["record_count"] == 0
        assert snapshot["component_ids"] == []
        checks += ["deterministic_receipt", "blocked_no_numeric_output", "pr289_replay"]

        registry = json.loads(
            (baseline / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json").read_text()
        )
        cf4_lane = next(row for row in registry["lanes"] if row["lane_id"] == "CF4")
        spec = yaml.safe_load(
            (baseline / "docs/research_program/post_pr275/pr291_spec.yaml").read_text()
        )
        assert tuple(cf4_lane["required_component_ids"]) == EXPECTED_ROLES
        assert tuple(spec["data_identity_contract"]["required_components"]) == EXPECTED_ROLES
        assert tuple(spec["pipeline_contract"]["depth_and_zoa_contract"]["native_role_cross_binding_required"]) == (
            "catalogue",
            "row_selection",
            "covariance",
            "grouping_definition",
            "depth_definition",
            "zoa_definition",
        )
        checks.append("exact_nine_role_contract")

        status = yaml.safe_load((baseline / "docs/codex_handoff/pr_status.yaml").read_text())
        stack = status["stacked_pr_execution"]
        assert stack["merge_policy"] == "HUMAN_ONLY"
        assert stack["prs"]["PR-292"]["lifecycle"] == "PLANNED"
        assert stack["prs"]["PR-292"]["gate_dispositions"]["eligibility"] == "INELIGIBLE"
        assert stack["prs"]["PR-292"]["assurance_budget"]["consumed"] == 0
        checks += ["human_only", "pr292_ineligible_zero"]

        fake_calls: list[str] = []
        fake = types.ModuleType("run_pr290_planck_lane")
        for symbol in runner._TRANSACTION_SYMBOLS:
            setattr(fake, symbol, lambda *_a, _s=symbol, **_k: fake_calls.append(_s))
        previous = sys.modules.get("run_pr290_planck_lane")
        sys.modules["run_pr290_planck_lane"] = fake
        (baseline / runner.OUTPUT.relative_to(runner.ROOT)).parent.mkdir(
            parents=True, exist_ok=True
        )
        try:
            assert quiet_write(runner, root=baseline) == 0
        finally:
            if previous is None:
                sys.modules.pop("run_pr290_planck_lane", None)
            else:
                sys.modules["run_pr290_planck_lane"] = previous
        assert fake_calls == []
        checks.append("preloaded_transaction_module_ignored")

        hostile = scratch / "hostile"
        clone_bound_root(runner, hostile)
        output = hostile / runner.OUTPUT.relative_to(runner.ROOT)
        outside = scratch / "outside.json"
        outside.write_text("sentinel", encoding="utf-8")
        require_preflight_refusal(runner, root=hostile, output=outside, label="outside_root")
        assert outside.read_text(encoding="utf-8") == "sentinel"
        checks.append("outside_root_refused_before_payload")

        output.parent.mkdir(parents=True, exist_ok=True)
        output.symlink_to(outside)
        require_preflight_refusal(runner, root=hostile, output=output, label="symlink")
        output.unlink()
        output.hardlink_to(outside)
        require_preflight_refusal(runner, root=hostile, output=output, label="hardlink")
        output.unlink()
        os.mkfifo(output)
        require_preflight_refusal(runner, root=hostile, output=output, label="fifo")
        output.unlink()
        traversal = hostile / "docs" / ".." / ".." / "traversal.json"
        require_preflight_refusal(runner, root=hostile, output=traversal, label="traversal")
        assert outside.read_text(encoding="utf-8") == "sentinel"
        checks += ["symlink_refused", "hardlink_refused", "fifo_refused", "traversal_refused"]

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"frozen")
        results = hostile / runner.OBSERVED_RESULT_DIRECTORY.relative_to(runner.ROOT)
        results.mkdir(parents=True)
        require_preflight_refusal(runner, root=hostile, output=output, label="observed_results")
        checks.append("blocked_results_directory_refused")

        checks += archive_refusals(runner, scratch)
        checks += atomic_invariants(runner, baseline)

        for source_kind in ("symlink", "hardlink"):
            root = scratch / f"source-{source_kind}"
            clone_bound_root(runner, root)
            module_path = root / runner.PR290_TRANSACTION_RUNNER.relative_to(runner.ROOT)
            exact_copy = scratch / f"transaction-{source_kind}.py"
            shutil.copy2(module_path, exact_copy)
            module_path.unlink()
            if source_kind == "symlink":
                module_path.symlink_to(exact_copy)
            else:
                module_path.hardlink_to(exact_copy)
            try:
                runner._base_source_bindings(root)
            except RuntimeError:
                checks.append(f"transaction_source_{source_kind}_refused")
            else:
                raise AssertionError(f"transaction source {source_kind} was accepted")

        assert len(checks) == len(set(checks))
        print(
            json.dumps(
                {
                    "schema": "PR291_R3_CODE_INVARIANT_ORACLE_V1",
                    "status": "PASS",
                    "temporary_root_outside_repository": True,
                    "temporary_root_removed_on_exit": True,
                    "check_count": len(checks),
                    "checks": sorted(checks),
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
