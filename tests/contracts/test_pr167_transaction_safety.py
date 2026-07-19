"""Failure-recovery and import-surface tests for the PR-167 transaction."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.codex_harness import (
    intake_advocate_track,
    pr167_intake_contract,
    validate_pr_dag,
)


REPO = Path(__file__).resolve().parents[2]


def _yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_validate_pr_dag_remains_package_importable() -> None:
    completed = subprocess.run(
        [sys.executable, "-B", "-c", "import scripts.codex_harness.validate_pr_dag"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_receipt_rejects_duplicate_or_reordered_preserved_ids() -> None:
    backlog = _yaml(REPO / "docs/codex_handoff/pr_backlog.yaml")
    receipt = json.loads(
        (REPO / "docs/generated/pr167_pre_intake_semantic_receipt.json").read_text(
            encoding="utf-8"
        )
    )

    duplicate = copy.deepcopy(receipt)
    duplicate["preserved_card_ids"][-1] = duplicate["preserved_card_ids"][0]
    duplicate["receipt_sha256"] = pr167_intake_contract._receipt_digest(duplicate)
    with pytest.raises(ValueError, match="must be unique"):
        pr167_intake_contract.validate_pre_intake_receipt(
            duplicate, backlog=backlog
        )

    reordered = copy.deepcopy(receipt)
    reordered["preserved_card_ids"] = list(
        reversed(reordered["preserved_card_ids"])
    )
    reordered["receipt_sha256"] = pr167_intake_contract._receipt_digest(reordered)
    with pytest.raises(ValueError, match="exact ordered pre-intake prefix"):
        pr167_intake_contract.validate_pre_intake_receipt(
            reordered, backlog=backlog
        )


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (
            lambda value: value.__setitem__("baseline_commit", "0" * 40),
            "baseline commit mismatch",
        ),
        (
            lambda value: value["card_semantic_sha256"].pop("PR-166"),
            "card/status coverage mismatch",
        ),
        (
            lambda value: value["pre_intake_status_projection"].__setitem__(
                "PR-151", "completed"
            ),
            "invalid pre-intake state",
        ),
        (
            lambda value: value["input_hashes"].__setitem__(0, "tampered"),
            "input hash list mismatch",
        ),
        (
            lambda value: value.__setitem__("public_use", True),
            "fixed metadata drift",
        ),
    ],
)
def test_receipt_mutation_matrix_fails_closed(mutator, message: str) -> None:
    backlog = _yaml(REPO / "docs/codex_handoff/pr_backlog.yaml")
    status = _yaml(REPO / "docs/codex_handoff/pr_status.yaml")
    receipt = json.loads(
        (REPO / "docs/generated/pr167_pre_intake_semantic_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    mutated = copy.deepcopy(receipt)
    mutator(mutated)
    mutated["receipt_sha256"] = pr167_intake_contract._receipt_digest(mutated)
    with pytest.raises(ValueError, match=message):
        pr167_intake_contract.validate_pre_intake_receipt(
            mutated,
            backlog=backlog,
            status=status,
            expected_baseline_commit=receipt["baseline_commit"],
            expected_backlog_sha256=receipt["pre_intake_backlog_sha256"],
            expected_status_sha256=receipt["pre_intake_status_sha256"],
            expected_roadmap_sha256=receipt["roadmap_sha256"],
        )


def test_multi_file_writer_preserves_modes_and_rolls_back_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("old-first\n", encoding="utf-8")
    second.write_text("old-second\n", encoding="utf-8")
    first.chmod(0o640)
    second.chmod(0o644)

    real_replace = os.replace
    calls = 0

    def fail_second_replace(source, target) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected second-replace failure")
        real_replace(source, target)

    monkeypatch.setattr(intake_advocate_track.os, "replace", fail_second_replace)
    with pytest.raises(OSError, match="injected second-replace failure"):
        intake_advocate_track._atomic_write_many(
            {first: "new-first\n", second: "new-second\n"}
        )

    assert first.read_text(encoding="utf-8") == "old-first\n"
    assert second.read_text(encoding="utf-8") == "old-second\n"
    assert first.stat().st_mode & 0o777 == 0o640
    assert second.stat().st_mode & 0o777 == 0o644
    assert not list(tmp_path.glob(".*.rollback.*"))
    assert not (tmp_path / ".pr167_write_journal.json").exists()


@pytest.mark.parametrize("all_new", [False, True])
def test_journal_recovery_resolves_mixed_or_fully_published_generation(
    tmp_path: Path, all_new: bool
) -> None:
    targets = [tmp_path / "first.txt", tmp_path / "second.txt"]
    journal = tmp_path / "journal.json"
    entries = []
    for index, target in enumerate(targets):
        old = f"old-{index}\n"
        new = f"new-{index}\n"
        target.write_text(old, encoding="utf-8")
        backup = tmp_path / f".{target.name}.backup.{index}"
        staged = tmp_path / f".{target.name}.staged.{index}"
        backup.write_text(old, encoding="utf-8")
        staged.write_text(new, encoding="utf-8")
        entries.append(
            {
                "target": str(target.resolve()),
                "staged": str(staged.resolve()),
                "backup": str(backup.resolve()),
                "prior_exists": True,
                "prior_sha256": intake_advocate_track.file_sha256(backup),
                "prior_mode": 0o644,
                "new_sha256": intake_advocate_track.file_sha256(staged),
            }
        )
    journal.write_text(
        json.dumps(
            {"schema": "htt.pr167.write_journal.v1", "entries": entries}
        ),
        encoding="utf-8",
    )
    os.replace(Path(entries[0]["staged"]), targets[0])
    if all_new:
        os.replace(Path(entries[1]["staged"]), targets[1])

    outcome = intake_advocate_track._recover_interrupted_transaction(
        journal, set(targets)
    )
    expected = "new" if all_new else "old"
    assert outcome == ("rolled_forward" if all_new else "rolled_back")
    assert [path.read_text(encoding="utf-8") for path in targets] == [
        f"{expected}-0\n",
        f"{expected}-1\n",
    ]
    assert not journal.exists()
    assert not list(tmp_path.glob(".*.backup.*"))
    assert not list(tmp_path.glob(".*.staged.*"))


def test_materialized_files_are_not_private_mode_and_manifest_is_complete() -> None:
    paths = [
        REPO / "docs/codex_handoff/pr_backlog.yaml",
        REPO / "docs/codex_handoff/pr_status.yaml",
        REPO / "docs/generated/pr167_pre_intake_semantic_receipt.json",
        REPO / "docs/generated/pr167_advocate_crosswalk.json",
        REPO / "docs/generated/pr167_artifact_manifest.json",
    ]
    assert all(path.stat().st_mode & 0o777 == 0o644 for path in paths)

    manifest = json.loads(paths[-1].read_text(encoding="utf-8"))
    assert manifest["registered_advocate_card_count"] == 17
    assert manifest["preserved_card_count"] == 113
    assert manifest["scientific_effect"] == "none"
    assert manifest["sky_support_mask_status"] == "not_applicable_governance"
    assert manifest["covariance_null_mock_status"] == "not_applicable_governance"
    assert len(manifest["artifact_hashes"]) == 4
    status_hash = next(
        row.rsplit(":", 1)[1]
        for row in manifest["artifact_hashes"]
        if row.startswith("docs/codex_handoff/pr_status.yaml:")
    )
    assert status_hash == (
        "e1fac88de5a621e8862a4672cd64b73862fc72e60447e837551e05b9bd7a1510"
    )
    assert status_hash != intake_advocate_track.file_sha256(
        intake_advocate_track.STATUS_YAML
    )


def test_crosswalk_binds_exact_receipt_file_bytes(
    tmp_path: Path,
) -> None:
    reformatted = tmp_path / "receipt.json"
    reformatted.write_bytes(
        (REPO / "docs/generated/pr167_pre_intake_semantic_receipt.json").read_bytes()
        + b"\n"
    )
    spec = intake_advocate_track._load_mapping(intake_advocate_track.SPEC)
    cards = intake_advocate_track.parse_advocate_cards(
        intake_advocate_track.ROADMAP.read_text(encoding="utf-8"), spec
    )
    receipt = json.loads(reformatted.read_text(encoding="utf-8"))
    expected = intake_advocate_track._crosswalk_payload(
        spec,
        cards,
        receipt,
        receipt_file_sha256=intake_advocate_track.file_sha256(reformatted),
    )
    actual = json.loads(
        (REPO / "docs/generated/pr167_advocate_crosswalk.json").read_text(
            encoding="utf-8"
        )
    )
    assert expected != actual
    assert expected["input_hashes"][-1] != actual["input_hashes"][-1]


@pytest.mark.parametrize(
    ("attribute", "source", "message"),
    [
        (
            "MACHINE_BACKLOG_YAML",
            "docs/codex_handoff/pr_backlog.yaml",
            "YAML backlog mirrors differ",
        ),
        (
            "MACHINE_STATUS_YAML",
            "docs/codex_handoff/pr_status.yaml",
            "YAML status mirrors differ",
        ),
    ],
)
def test_dedicated_check_rejects_exact_byte_mirror_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    attribute: str,
    source: str,
    message: str,
) -> None:
    drifted = tmp_path / Path(source).name
    drifted.write_bytes((REPO / source).read_bytes() + b"\n")
    monkeypatch.setattr(intake_advocate_track, attribute, drifted)
    spec = intake_advocate_track._load_mapping(intake_advocate_track.SPEC)
    cards = intake_advocate_track.parse_advocate_cards(
        intake_advocate_track.ROADMAP.read_text(encoding="utf-8"), spec
    )
    with pytest.raises(ValueError, match=message):
        intake_advocate_track.check_materialized(spec, cards)


def test_refresh_prevalidation_rejects_mirror_drift_before_any_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    drifted = tmp_path / "pr_backlog.yaml"
    drifted.write_bytes(intake_advocate_track.BACKLOG_YAML.read_bytes() + b"\n")
    monkeypatch.setattr(intake_advocate_track, "MACHINE_BACKLOG_YAML", drifted)
    replace_calls = 0

    def forbidden_replace(source, target) -> None:
        nonlocal replace_calls
        replace_calls += 1
        raise AssertionError("prevalidation must precede the first replace")

    monkeypatch.setattr(intake_advocate_track.os, "replace", forbidden_replace)
    spec = intake_advocate_track._load_mapping(intake_advocate_track.SPEC)
    backlog = _yaml(intake_advocate_track.BACKLOG_YAML)
    status = _yaml(intake_advocate_track.STATUS_YAML)
    with pytest.raises(ValueError, match="divergent YAML backlog mirrors"):
        intake_advocate_track._prevalidate_refresh_state(spec, backlog, status)
    assert replace_calls == 0


def test_pre_advocate_activation_map_cannot_be_self_consistently_retyped() -> None:
    commit = "fe7abb6aa01fdfaf0440956bd8727ddc9e1be8e7"
    backlog_text = subprocess.run(
        ["git", "show", f"{commit}:docs/codex_handoff/pr_backlog.yaml"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    status_text = subprocess.run(
        ["git", "show", f"{commit}:docs/codex_handoff/pr_status.yaml"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    backlog = yaml.safe_load(backlog_text)
    status = yaml.safe_load(status_text)
    cards = {card["id"]: card for card in backlog["prs"]}
    cards["PR-119"]["activation_state"] = "DORMANT_EXTERNAL"
    status["completed"].remove("PR-119")
    status["dormant_external"].append("PR-119")
    status["execution_resolutions"].pop("PR-119")
    info = validate_pr_dag.validate_backlog(backlog)
    with pytest.raises(ValueError, match="activation_state must remain PENDING"):
        validate_pr_dag.validate_long_horizon_rescue_slice(
            backlog, info, status=status
        )


def test_refresh_and_computed_generation_reject_native_dormancy_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = intake_advocate_track._load_mapping(intake_advocate_track.SPEC)
    cards = intake_advocate_track.parse_advocate_cards(
        intake_advocate_track.ROADMAP.read_text(encoding="utf-8"), spec
    )
    backlog = _yaml(intake_advocate_track.BACKLOG_YAML)
    status = _yaml(intake_advocate_track.STATUS_YAML)
    status["dormant_external"].remove("PR-183")
    status["pending"].append("PR-183")
    receipt = json.loads(
        intake_advocate_track.RECEIPT.read_text(encoding="utf-8")
    )
    replace_calls = 0

    def forbidden_replace(source, target) -> None:
        nonlocal replace_calls
        replace_calls += 1
        raise AssertionError("typed prevalidation must precede the first replace")

    monkeypatch.setattr(intake_advocate_track.os, "replace", forbidden_replace)
    with pytest.raises(ValueError, match="match typed activation_state"):
        intake_advocate_track._prevalidate_refresh_state(spec, backlog, status)
    assert replace_calls == 0

    with pytest.raises(ValueError, match="match typed activation_state"):
        intake_advocate_track._validate_computed_generation(
            spec,
            cards,
            backlog,
            status,
            receipt,
            yaml.safe_dump(backlog, sort_keys=False, allow_unicode=True),
            yaml.safe_dump(status, sort_keys=False, allow_unicode=True),
        )
    assert replace_calls == 0


def test_dedicated_check_rejects_native_dormancy_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status = _yaml(intake_advocate_track.STATUS_YAML)
    status["dormant_external"].remove("PR-183")
    status["pending"].append("PR-183")
    status_path = tmp_path / "pr_status.yaml"
    status_path.write_text(
        yaml.safe_dump(status, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    monkeypatch.setattr(intake_advocate_track, "STATUS_YAML", status_path)
    monkeypatch.setattr(intake_advocate_track, "MACHINE_STATUS_YAML", status_path)
    spec = intake_advocate_track._load_mapping(intake_advocate_track.SPEC)
    cards = intake_advocate_track.parse_advocate_cards(
        intake_advocate_track.ROADMAP.read_text(encoding="utf-8"), spec
    )

    with pytest.raises(ValueError, match="match typed activation_state"):
        intake_advocate_track.check_materialized(spec, cards)
