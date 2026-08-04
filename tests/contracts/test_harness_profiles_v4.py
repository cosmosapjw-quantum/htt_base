from __future__ import annotations

import copy
import hashlib
import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import common.harness_profiles_v4 as profiles_v4
from common.evidence_graph import TestCaseResult, TestExecution, TestOutcome
from common.harness_profiles_v4 import (
    HarnessProfileError,
    RECEIPT_REGISTRY_SCHEMA_VERSION,
    REQUIRED_PROFILE_IDS,
    load_profile_manifest,
    make_smoke_binding_record,
    validate_smoke_receipt_registry,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = (
    REPO_ROOT / "docs/research_program/post_pr275/harness_profiles_v4.yaml"
)
REGISTRY_PATH = (
    REPO_ROOT / "docs/research_program/post_pr275/test_execution_receipts_v4.yaml"
)
RUNNER = REPO_ROOT / "scripts/codex_harness/run_pr280_harness.py"


def _manifest_payload() -> dict[str, object]:
    payload = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _write_manifest(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "profiles.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_manifest_has_exact_profile_partition_and_controls() -> None:
    manifest = load_profile_manifest(MANIFEST_PATH, repo_root=REPO_ROOT)

    assert set(manifest.profiles) == REQUIRED_PROFILE_IDS
    for profile in manifest.profiles.values():
        assert profile.claim_ceiling == "diagnostic_only"
        if profile.kind == "pytest":
            command = profile.pytest_command("python")
            assert ["-p", "no:cacheprovider"] == command[3:5]
            assert ["-o", "addopts="] == command[5:7]

    for profile_id in ("smoke", "fast"):
        profile = manifest.profile(profile_id)
        assert profile.selectors
        assert "-m" not in profile.pytest_args
    assert manifest.profile("smoke").smoke_status_eligible is True
    assert manifest.profile("fast").smoke_status_eligible is False


def test_data_and_formal_profiles_cannot_transfer_smoke_authority() -> None:
    manifest = load_profile_manifest(MANIFEST_PATH, repo_root=REPO_ROOT)

    for profile_id, profile in manifest.profiles.items():
        if profile_id.startswith(("data:", "formal:")):
            assert profile.smoke_status_eligible is False
            assert profile.receipt_eligible is False
    assert {
        profile_id for profile_id in manifest.profiles if profile_id.startswith("formal:")
    } == {
        "formal:wolfram-xact",
        "formal:sympy",
        "formal:sage-singular",
        "formal:lean",
    }
    cf4 = manifest.profile("data:cf4")
    assert "tests/htt/test_cf4_active_input_quarantine.py" not in cf4.selectors
    assert all("test_frozen_legacy_consumer" not in row for row in cf4.selectors)
    act = manifest.profile("data:act")
    assert "tests/contracts/test_pr152_act_raw_qe.py" not in act.selectors
    assert all("test_runner_check_and_real_artifacts" not in row for row in act.selectors)
    assert all("test_real_feature_card" not in row for row in act.selectors)


def test_active_import_is_a_separate_non_receipt_lane() -> None:
    manifest = load_profile_manifest(MANIFEST_PATH, repo_root=REPO_ROOT)
    profile = manifest.profile("active-import")

    assert profile.kind == "import_probe"
    assert profile.modules == (
        "bass=htt/bass/__init__.py",
        "common=htt/src/common/__init__.py",
        "htt=htt/__init__.py",
        "mio=htt/mio/__init__.py",
        "obsstat=htt/obsstat/__init__.py",
        "tests=tests/__init__.py",
    )
    assert profile.receipt_eligible is False


def test_changed_surface_routing_is_local_and_conservative() -> None:
    manifest = load_profile_manifest(MANIFEST_PATH, repo_root=REPO_ROOT)

    package_profiles = set(manifest.profiles_for_paths(["htt/pyproject.toml"]))
    scientific_profiles = set(
        manifest.profiles_for_paths(["htt/src/common/joint_anisotropy_state.py"])
    )

    assert {"package", "active-import", "current-active"} <= package_profiles
    assert {"scientific", "smoke", "current-active"} <= scientific_profiles
    assert "publication" not in package_profiles
    for path in (
        "docs/research_program/post_pr275/pr280_spec.yaml",
        "docs/research_program/post_pr275/full_inventory_v4_receipt.json",
        ".agent-harness/context/CLAIM_REGISTRY.jsonl",
        "scripts/ver2_artifact_export.py",
    ):
        assert {"exact", "smoke", "current-active"} <= set(
            manifest.profiles_for_paths([path])
        )
    for path in (
        "docs/codex_handoff/pr_backlog.yaml",
        "htt/src/common/pr_retrace.py",
        "scripts/codex_harness/validate_pr_dag.py",
    ):
        assert {"exact", "current-active"} <= set(
            manifest.profiles_for_paths([path])
        )


def test_marker_only_smoke_mutation_is_rejected(tmp_path: Path) -> None:
    payload = _manifest_payload()
    smoke = next(row for row in payload["profiles"] if row["profile_id"] == "smoke")
    smoke["selectors"] = []
    smoke["pytest_args"] = ["-m", "smoke", "-q"]

    with pytest.raises(HarnessProfileError, match="explicit pytest selectors"):
        load_profile_manifest(
            _write_manifest(tmp_path, payload), verify_paths=False
        )


def test_formal_axis_smoke_alias_is_rejected(tmp_path: Path) -> None:
    payload = _manifest_payload()
    formal = next(
        row for row in payload["profiles"] if row["profile_id"] == "formal:sympy"
    )
    formal["smoke_status_eligible"] = True
    formal["receipt_eligible"] = True

    with pytest.raises(HarnessProfileError, match="only the explicit smoke"):
        load_profile_manifest(
            _write_manifest(tmp_path, payload), verify_paths=False
        )


def test_full_inventory_command_and_profile_kinds_are_fixed(tmp_path: Path) -> None:
    payload = _manifest_payload()
    full = next(
        row for row in payload["profiles"] if row["profile_id"] == "full-inventory"
    )
    full["pytest_args"] = ["--junitxml=artifacts/full_inventory.xml", "--maxfail=1"]
    with pytest.raises(HarnessProfileError, match="exact cache-free JUnit"):
        load_profile_manifest(_write_manifest(tmp_path, payload), verify_paths=False)

    payload = _manifest_payload()
    exact = next(row for row in payload["profiles"] if row["profile_id"] == "exact")
    exact.update(kind="tool_probe", selectors=[], pytest_args=[], tools=["executable:true"])
    with pytest.raises(HarnessProfileError, match="must have kind pytest"):
        load_profile_manifest(_write_manifest(tmp_path, payload), verify_paths=False)


def test_empty_receipt_registry_is_valid_and_grants_nothing() -> None:
    manifest = load_profile_manifest(MANIFEST_PATH, repo_root=REPO_ROOT)
    payload = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))

    assert payload["schema_version"] == RECEIPT_REGISTRY_SCHEMA_VERSION
    assert validate_smoke_receipt_registry(
        REGISTRY_PATH, manifest=manifest, repo_root=REPO_ROOT
    ) == {}


def test_receipt_registry_outside_repository_is_not_parallel_authority(
    tmp_path: Path,
) -> None:
    manifest = load_profile_manifest(MANIFEST_PATH, repo_root=REPO_ROOT)
    external = tmp_path / "receipts.yaml"
    external.write_text(REGISTRY_PATH.read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(HarnessProfileError, match="outside the repository"):
        validate_smoke_receipt_registry(
            external,
            manifest=manifest,
            repo_root=REPO_ROOT,
        )


def test_smoke_binding_record_seals_waiver_null_and_candidate_identity() -> None:
    manifest = load_profile_manifest(MANIFEST_PATH, repo_root=REPO_ROOT)
    record = make_smoke_binding_record(
        pr_id="PR-280",
        profile_id="smoke",
        manifest=manifest,
        evidence_path="docs/generated/pr280_smoke_execution.json",
        evidence_sha256="a" * 64,
        candidate_commit="b" * 40,
        candidate_tree="c" * 40,
        created_at="2026-08-04T00:00:00+00:00",
    )
    unsigned = dict(record)
    seal = unsigned.pop("binding_sha256")

    assert record["waiver_id"] is None
    assert seal == hashlib.sha256(
        json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def test_smoke_invocation_rejects_filters_cache_and_partial_selection() -> None:
    valid = (
        "-p",
        "common.pytest_execution_evidence",
        "-p",
        "no:cacheprovider",
        "--import-mode=importlib",
        "--rootdir",
        ".",
        "-c",
        "pytest.ini",
        "-o",
        "addopts=",
    )
    profiles_v4._validate_smoke_invocation(valid)

    for mutation in (
        ("-k", "one_test"),
        ("-kone_test",),
        ("--lf",),
        ("-m=smoke",),
        ("-n", "2"),
        ("-o", "addopts=-k one_test"),
        ("-oaddopts=-k one_test",),
        ("--override-ini=addopts=-k one_test",),
        ("-c", "/dev/null"),
        ("-c/dev/null",),
        ("-p", "cacheprovider"),
        ("-pcacheprovider",),
        ("--rootdir", "tests"),
        ("--rootdir=tests",),
        ("--import-mode=prepend",),
    ):
        with pytest.raises(HarnessProfileError, match="execution controls"):
            profiles_v4._validate_smoke_invocation((*valid, *mutation))


def test_smoke_execution_requires_every_registered_node_exactly_once() -> None:
    manifest = load_profile_manifest(MANIFEST_PATH, repo_root=REPO_ROOT)
    profile = manifest.profile("smoke")
    invocation = (
        "-p",
        "common.pytest_execution_evidence",
        "-p",
        "no:cacheprovider",
        "--import-mode=importlib",
        "--rootdir",
        ".",
        "-c",
        "pytest.ini",
        "-o",
        "addopts=",
    )
    selected = profile.selectors[0]
    partial = TestExecution(
        framework="pytest:test",
        selector=json.dumps(list(profile.selectors)),
        command=invocation,
        collected_test_ids=(selected,),
        executed_test_ids=(selected,),
        results=(TestCaseResult(selected, TestOutcome.PASSED),),
        reported_collected_count=1,
        reported_executed_count=1,
    )

    assert partial.is_authoritative is True
    with pytest.raises(HarnessProfileError, match="every registered smoke node"):
        profiles_v4._validate_smoke_execution(profile, partial)


def test_receipt_repo_bindings_are_exact_and_conflicts_fail_closed() -> None:
    digest_a = "a" * 64
    digest_b = "b" * 64
    payload = {
        "selector_inputs": [
            {"scope": "repo", "path": "tests/test_one.py", "sha256": digest_a}
        ],
        "environment_contract": {
            "pytest": {
                "config_file": {
                    "scope": "repo",
                    "path": "pytest.ini",
                    "sha256": digest_b,
                },
                "plugins": [],
                "conftests": [],
            },
            "import_origins": [
                {
                    "module": "tests.test_one",
                    "source": {
                        "scope": "repo",
                        "path": "tests/test_one.py",
                        "sha256": digest_a,
                    },
                }
            ],
        },
    }

    assert profiles_v4._receipt_repo_bindings(payload) == {
        "pytest.ini": digest_b,
        "tests/test_one.py": digest_a,
    }
    payload["environment_contract"]["import_origins"][0]["source"]["sha256"] = digest_b
    with pytest.raises(HarnessProfileError, match="conflicting hashes"):
        profiles_v4._receipt_repo_bindings(payload)


def test_candidate_binding_rejects_receipt_manifest_hash_conflict() -> None:
    manifest = load_profile_manifest(MANIFEST_PATH, repo_root=REPO_ROOT)
    payload = {
        "selector_inputs": [
            {
                "scope": "repo",
                "path": MANIFEST_PATH.relative_to(REPO_ROOT).as_posix(),
                "sha256": "a" * 64,
            }
        ],
        "environment_contract": {
            "pytest": {"config_file": None, "plugins": [], "conftests": []},
            "import_origins": [],
        },
    }

    with pytest.raises(HarnessProfileError, match="conflicts with the registered"):
        profiles_v4._verify_candidate_receipt_inputs(
            repo_root=REPO_ROOT,
            candidate_commit="b" * 40,
            manifest=manifest,
            evidence_payload=payload,
        )


def test_runner_check_and_formal_probe_dry_run_are_non_promoting() -> None:
    check = subprocess.run(
        [sys.executable, str(RUNNER), "check"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    probe = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "profile",
            "formal:sympy",
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert check.returncode == 0, check.stderr
    assert json.loads(check.stdout)["claim_ceiling"] == "diagnostic_only"
    assert probe.returncode == 0, probe.stderr
    assert probe.stdout.startswith("probe python-module:sympy")


def test_runner_rejects_output_through_symlinked_parent(tmp_path: Path) -> None:
    external = tmp_path / "external"
    external.mkdir()
    link = REPO_ROOT / ".pr280-output-link-test"
    assert not link.exists() and not link.is_symlink()
    created = False
    try:
        link.symlink_to(external, target_is_directory=True)
        created = True
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "profile",
                "active-import",
                "--output",
                ".pr280-output-link-test/probe.json",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 2
        assert "escapes the repository" in completed.stderr
        assert not (external / "probe.json").exists()
    finally:
        if created:
            link.unlink(missing_ok=True)


def test_runner_rejects_one_path_for_evidence_and_binding() -> None:
    output = ".pr280-same-output-probe.json"
    assert not (REPO_ROOT / output).exists()
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "profile",
            "smoke",
            "--evidence-output",
            output,
            "--binding-output",
            output,
            "--pr-id",
            "PR-280",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    assert "must be distinct" in completed.stderr
    assert not (REPO_ROOT / output).exists()


@pytest.mark.parametrize(
    "extra_args",
    (
        ("--binding-output", ".pr280-orphan-binding.json", "--pr-id", "PR-280"),
        ("--pr-id", "PR-280"),
    ),
)
def test_runner_rejects_binding_identity_without_evidence(extra_args) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "profile",
            "smoke",
            *extra_args,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    assert "require an evidence output" in completed.stderr
    assert not (REPO_ROOT / ".pr280-orphan-binding.json").exists()


def test_runner_rejects_pr_identity_without_binding_output() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "profile",
            "smoke",
            "--evidence-output",
            ".pr280-unused-evidence.json",
            "--pr-id",
            "PR-280",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    assert "PR identity requires a binding output" in completed.stderr
    assert not (REPO_ROOT / ".pr280-unused-evidence.json").exists()


def test_changed_surface_includes_untracked_worktree_paths() -> None:
    runner = runpy.run_path(str(RUNNER))
    assert runner["CHANGED_DIFF_FILTER"] == "ACDMRTUXB"
    candidate = REPO_ROOT / "pr280_changed_surface_probe.txt"
    assert not candidate.exists() and not candidate.is_symlink()
    created = False
    try:
        candidate.write_text("diagnostic probe\n", encoding="utf-8")
        created = True
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "changed", "--base", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        payload = json.loads(completed.stdout)
        assert payload["includes_worktree"] is True
        assert "pr280_changed_surface_probe.txt" in payload["paths"]
        assert "current-active" in payload["profiles"]
    finally:
        if created:
            candidate.unlink(missing_ok=True)


def test_hermetic_smoke_command_runs_with_selected_interpreter_dependencies(
    tmp_path: Path,
) -> None:
    runner = runpy.run_path(str(RUNNER))
    manifest = load_profile_manifest(MANIFEST_PATH, repo_root=REPO_ROOT)
    evidence = tmp_path / "smoke-evidence.json"
    cache = tmp_path / "pycache"
    cache.mkdir()
    receipt_python = runner["_receipt_python"]()
    command = runner["_hermetic_pytest_command"](
        manifest.profile("smoke"),
        python=receipt_python,
        evidence_output=evidence,
        cache_dir=cache,
    )
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=runner["_clean_environment"](),
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "common.pytest_execution_evidence.v2"
    assert payload["counts"]["failed"] == 0
    assert payload["counts"]["executed"] == 8
    assert TestExecution.from_pytest_evidence(payload).is_authoritative is True
    runner["_verify_generated_evidence"](receipt_python, evidence)
