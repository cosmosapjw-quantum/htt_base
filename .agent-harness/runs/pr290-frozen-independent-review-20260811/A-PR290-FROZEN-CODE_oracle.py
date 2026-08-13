#!/usr/bin/env python3
"""Assignment-local hostile oracle for the frozen PR-290 candidate."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import types

import yaml


ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = ROOT / "scripts/codex_harness/run_pr290_planck_lane.py"
IDENTITY_REL = Path("docs/generated/pr289_data_identity_v2_receipt.json")
REGISTRY_REL = Path(
    "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)
SPEC_REL = Path("docs/research_program/post_pr275/pr290_spec.yaml")
STATUS_REL = Path("docs/codex_handoff/pr_status.yaml")
PR287_REL = Path("docs/generated/pr287_fresh_blind_typed_replay_receipt.json")
PR288_REL = Path("docs/generated/pr288_bayesian_semantics_receipt.json")


def load_module(name: str, path: Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runner = load_module("_pr290_assignment_oracle_runner", RUNNER_PATH)
data_identity = load_module(
    "_pr290_assignment_oracle_identity", ROOT / "htt/src/common/data_identity.py"
)
activation = load_module(
    "_pr290_assignment_oracle_activation",
    ROOT / "htt/src/common/observed_lane_activation.py",
)


def canonical_hash(payload: object) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()


def copy_activation_inputs(destination: Path) -> None:
    identity = json.loads((ROOT / IDENTITY_REL).read_text(encoding="utf-8"))
    relatives = {
        SPEC_REL,
        STATUS_REL,
        IDENTITY_REL,
        PR288_REL,
        *(Path(value) for value in identity["source_bindings"]),
    }
    for relative in relatives:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def activate_predecessors(root: Path) -> None:
    status_path = root / STATUS_REL
    status = yaml.safe_load(status_path.read_text(encoding="utf-8"))
    completed = status.setdefault("completed", [])
    resolutions = status.setdefault("execution_resolutions", {})
    terminals = {
        "PR-287": "PASS_FRESH_BLIND_TYPED_REPLAY",
        "PR-288": "PASS_BAYESIAN_SEMANTICS_REPAIR",
        "PR-289": "PASS_DATA_IDENTITY_V2_PREFLIGHT",
    }
    for index, pr_id in enumerate(("PR-202", "PR-287", "PR-288", "PR-289")):
        if pr_id not in completed:
            completed.append(pr_id)
        row = {
            "resolution": "COMPLETED_SUCCESS",
            "candidate_sha": f"{index + 1:040x}",
            "success_dependency_satisfied": True,
            "observed_data_executed": False,
            "public_use": False,
        }
        if pr_id in terminals:
            row["terminal"] = terminals[pr_id]
        resolutions[pr_id] = row
    status_path.write_text(yaml.safe_dump(status, sort_keys=False), encoding="utf-8")
    unsigned = {
        "schema": "HTT_PR287_FRESH_BLIND_TYPED_REPLAY_RECEIPT_V1",
        "terminal": terminals["PR-287"],
        "synthetic_only": True,
    }
    receipt = {**unsigned, "receipt_content_id": canonical_hash(unsigned)}
    target = root / PR287_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")


def admit_authentic_planck(root: Path) -> dict[str, object]:
    registry = data_identity.load_lane_registry(root / REGISTRY_REL)
    lane = registry.lane("PLANCK")
    descriptor = data_identity._mutation_descriptor(root / "oracle-native", lane)
    decision = data_identity.evaluate_lane_identity(
        registry=registry,
        lane_id="PLANCK",
        descriptor=descriptor,
        inspected_at_utc="2026-08-09T00:00:00+00:00",
    )
    assert decision.status.value == "ADMITTED_IDENTITY_ONLY"
    assert len(decision.records) == 13
    payload_path = root / IDENTITY_REL
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    decision_payload = decision.as_payload()
    authorization_payload = data_identity.build_not_authorized_receipt(
        lane, decision
    ).as_payload()
    for index, row in enumerate(payload["lane_decisions"]):
        if row["lane_id"] == "PLANCK":
            payload["lane_decisions"][index] = decision_payload
    lane_identity = next(
        row
        for row in payload["lane_and_product_identities"]
        if row["lane_id"] == "PLANCK"
    )
    lane_identity.update(
        {
            "status": "ADMITTED_IDENTITY_ONLY",
            "lane_admission_bundle_id": decision.lane_admission_bundle_id,
            "native_identity_profile_id": decision.records[0].native_identity_profile_id,
        }
    )
    for index, row in enumerate(payload["authorization_receipts"]):
        if row["lane_id"] == "PLANCK":
            payload["authorization_receipts"][index] = authorization_payload
    payload["aggregate_status"] = "PARTIAL_LANE_ADMISSION"
    payload.pop("receipt_content_id", None)
    payload["receipt_content_id"] = canonical_hash(payload)
    payload_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return payload


def resign_planck_payload(payload: dict[str, object]) -> None:
    decision = next(
        row for row in payload["lane_decisions"] if row["lane_id"] == "PLANCK"
    )
    records = decision["records"]
    for record in records:
        stable = dict(record)
        for key in ("record_id", "inspection_receipt_id", "inspected_at_utc"):
            stable.pop(key)
        record["record_id"] = canonical_hash(stable)
        inspection = dict(record)
        inspection.pop("inspection_receipt_id")
        record["inspection_receipt_id"] = canonical_hash(inspection)
    bundle = canonical_hash(
        {
            "lane_id": decision["lane_id"],
            "product_id": decision["product_id"],
            "component_inventory_id": records[0]["component_inventory_id"],
            "record_ids": [record["record_id"] for record in records],
        }
    )
    decision["lane_admission_bundle_id"] = bundle
    lane_identity = next(
        row
        for row in payload["lane_and_product_identities"]
        if row["lane_id"] == "PLANCK"
    )
    lane_identity["lane_admission_bundle_id"] = bundle
    lane_identity["native_identity_profile_id"] = records[0][
        "native_identity_profile_id"
    ]
    authorization = next(
        row
        for row in payload["authorization_receipts"]
        if row["lane_id"] == "PLANCK"
    )
    authorization["exact_admission_record_ids"] = [
        record["record_id"] for record in records
    ]
    authorization["lane_admission_bundle_id"] = bundle
    authorization.pop("authorization_id", None)
    authorization["authorization_id"] = canonical_hash(authorization)
    payload.pop("receipt_content_id", None)
    payload["receipt_content_id"] = canonical_hash(payload)


checks: list[dict[str, str]] = []


def passed(name: str, detail: str) -> None:
    checks.append({"check": name, "status": "PASS", "detail": detail})


def expect_runtime(name: str, action, token: str) -> None:
    try:
        action()
    except RuntimeError as exc:
        assert token.lower() in str(exc).lower(), (token, str(exc))
        passed(name, str(exc))
    else:
        raise AssertionError(f"{name}: hostile mutation was accepted")


def main() -> None:
    first = runner._encoded(runner._build(ROOT))
    second = runner._encoded(runner._build(ROOT))
    frozen = runner.OUTPUT.read_bytes()
    assert first == second == frozen
    passed("deterministic_replay", hashlib.sha256(first).hexdigest())

    receipt = json.loads(frozen)
    bindings = runner._source_bindings(ROOT)
    assert set(bindings) == set(receipt["source_bindings"])
    assert bindings == receipt["source_bindings"]
    assert set(bindings) == set(activation.REQUIRED_NONEXECUTION_SOURCE_PATHS)
    passed("exact_source_inventory", f"{len(bindings)} exact sources")

    fake_activation = types.ModuleType("common.observed_lane_activation")
    fake_identity = types.ModuleType("common.data_identity")
    fake_activation.build_planck_activation_decision = lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("fake activation called"))
    fake_activation.build_planck_nonexecution_receipt = fake_activation.build_planck_activation_decision
    fake_identity.replay_lane_admission_decision = lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("fake identity called"))
    old_activation = sys.modules.get("common.observed_lane_activation")
    old_identity = sys.modules.get("common.data_identity")
    sys.modules["common.observed_lane_activation"] = fake_activation
    sys.modules["common.data_identity"] = fake_identity
    try:
        hostile_receipt = runner._build(ROOT)
    finally:
        if old_activation is None:
            sys.modules.pop("common.observed_lane_activation", None)
        else:
            sys.modules["common.observed_lane_activation"] = old_activation
        if old_identity is None:
            sys.modules.pop("common.data_identity", None)
        else:
            sys.modules["common.data_identity"] = old_identity
    assert hostile_receipt["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
    passed("preloaded_module_substitution", "exact-byte loaders ignored aliases")

    with tempfile.TemporaryDirectory(prefix="pr290-oracle-admission-") as raw:
        scratch = Path(raw) / "repo"
        scratch.mkdir()
        copy_activation_inputs(scratch)
        activate_predecessors(scratch)
        positive = admit_authentic_planck(scratch)
        observed = activation.build_planck_activation_decision(repository_root=scratch)
        assert observed.terminal == "BLOCKED_HUMAN_EXECUTION_AUTHORIZATION"
        assert observed.data_identity_snapshot["canonical_record_replay"] is True
        assert observed.data_identity_snapshot["record_count"] == 13
        passed("authentic_full_record_replay", "13 records reached human gate")

        record_only = copy.deepcopy(positive)
        row = next(
            value
            for value in record_only["lane_decisions"]
            if value["lane_id"] == "PLANCK"
        )
        ids = [value["record_id"] for value in row["records"]]
        row["records"] = [{"record_id": value} for value in ids]
        record_only.pop("receipt_content_id", None)
        record_only["receipt_content_id"] = canonical_hash(record_only)
        (scratch / IDENTITY_REL).write_text(
            json.dumps(record_only, sort_keys=True) + "\n", encoding="utf-8"
        )
        observed = activation.build_planck_activation_decision(repository_root=scratch)
        assert observed.terminal == "BLOCKED_DATA_IDENTITY_ADMISSION"
        assert any("canonical native-record replay failed" in reason for reason in observed.reasons)
        passed("record_id_only_refusal", observed.reasons[0])

        incomplete = copy.deepcopy(positive)
        row = next(
            value
            for value in incomplete["lane_decisions"]
            if value["lane_id"] == "PLANCK"
        )
        for record in row["records"]:
            profile = dict(record["native_identity_profile"])
            profile.pop("profile_id")
            profile.pop("ffp10_null")
            profile["profile_id"] = canonical_hash(profile)
            record["native_identity_profile"] = profile
            record["native_identity_profile_id"] = profile["profile_id"]
        reference = row["records"][0]
        profile = reference["native_identity_profile"]
        replay_components = [
            {
                "component_id": binding["component_id"],
                "relative_path": binding["relative_path"],
                "byte_size": binding["byte_size"],
                "content_sha256": binding["content_sha256"],
            }
            for binding in profile["component_bindings"]
        ]
        evidence = {
            "schema": data_identity.DATA_IDENTITY_EVIDENCE_SCHEMA,
            "lane_id": reference["lane_id"],
            "product_id": reference["product_id"],
            **{
                field_name: reference[field_name]
                for field_name in data_identity._EVIDENCE_FIELDS
                if field_name not in {"schema", "lane_id", "product_id"}
            },
        }
        evidence["native_identity_profile"] = profile
        resigned_locator = data_identity.compute_source_locator_identity(
            lane_id=reference["lane_id"],
            product_id=reference["product_id"],
            components=replay_components,
            evidence_bindings=evidence,
        )
        for record in row["records"]:
            record["source_locator_identity"] = resigned_locator
        resign_planck_payload(incomplete)
        (scratch / IDENTITY_REL).write_text(
            json.dumps(incomplete, sort_keys=True) + "\n", encoding="utf-8"
        )
        observed = activation.build_planck_activation_decision(repository_root=scratch)
        assert observed.terminal == "BLOCKED_DATA_IDENTITY_ADMISSION"
        assert any("canonical native-record replay failed" in reason for reason in observed.reasons)
        passed("resigned_incomplete_profile_refusal", observed.reasons[0])

    with tempfile.TemporaryDirectory(prefix="pr290-oracle-fs-") as raw:
        base = Path(raw)
        root = base / "repo"
        root.mkdir()
        output = root / "receipts/nonexecution.json"
        output.parent.mkdir()
        observed = root / "results"
        outside = base / "outside"
        outside.write_text("preserve\n", encoding="utf-8")

        output.symlink_to(outside)
        expect_runtime(
            "symlink_output_refusal",
            lambda: runner._validate_output_destinations(root=root, output=output, observed_result_directory=observed, require_existing=False),
            "single-link",
        )
        output.unlink()
        output.hardlink_to(outside)
        expect_runtime(
            "hardlink_output_refusal",
            lambda: runner._validate_output_destinations(root=root, output=output, observed_result_directory=observed, require_existing=False),
            "single-link",
        )
        output.unlink()
        os.mkfifo(output)
        expect_runtime(
            "fifo_output_refusal",
            lambda: runner._validate_output_destinations(root=root, output=output, observed_result_directory=observed, require_existing=False),
            "single-link",
        )
        output.unlink()

        alias_root = base / "alias-repo"
        alias_root.mkdir()
        (alias_root / "receipts").symlink_to(output.parent, target_is_directory=True)
        expect_runtime(
            "symlink_parent_refusal",
            lambda: runner._validate_output_destinations(root=alias_root, output=alias_root / "receipts/x.json", observed_result_directory=alias_root / "results", require_existing=False),
            "parent",
        )

        observed.symlink_to(base / "missing-results", target_is_directory=True)
        expect_runtime(
            "observed_result_symlink_refusal",
            lambda: runner._validate_output_destinations(root=root, output=output, observed_result_directory=observed, require_existing=False),
            "result directory",
        )
        observed.unlink()
        os.mkfifo(observed)
        expect_runtime(
            "observed_result_fifo_refusal",
            lambda: runner._validate_output_destinations(root=root, output=output, observed_result_directory=observed, require_existing=False),
            "result directory",
        )
        observed.unlink()

        runner._atomic_write(output, b"{}\n", root=root, observed_result_directory=observed)
        assert output.read_bytes() == b"{}\n" and output.stat().st_nlink == 1
        passed("same_directory_atomic_write", "single-link regular receipt committed")
        output.unlink()

        displaced = base / "displaced"
        real_replace = runner.os.replace
        rebound = False

        def rebind_then_replace(*args, **kwargs):
            nonlocal rebound
            if not rebound:
                output.parent.rename(displaced)
                output.parent.mkdir()
                rebound = True
            return real_replace(*args, **kwargs)

        runner.os.replace = rebind_then_replace
        try:
            expect_runtime(
                "atomic_parent_rebind_refusal",
                lambda: runner._atomic_write(output, b"{}\n", root=root, observed_result_directory=observed),
                "commit",
            )
        finally:
            runner.os.replace = real_replace
        assert not output.exists() and not (displaced / output.name).exists()

        tracked_root = base / "tracked"
        tracked_root.mkdir()
        (tracked_root / "link").symlink_to(outside)
        expect_runtime(
            "archive_manifest_link_refusal",
            lambda: runner._tracked_manifest(tracked_root, ("link",)),
            "not regular",
        )

    final = json.loads(runner.OUTPUT.read_text(encoding="utf-8"))
    assert final["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
    assert final["numeric_outputs_written"] == []
    assert final["observed_data_executed"] is False
    assert final["network_or_download_side_effect"] is False
    assert not runner.OBSERVED_RESULT_DIRECTORY.exists()
    passed("blocked_nonexecution_boundary", "no observed-result directory or side effects")

    print(
        json.dumps(
            {
                "schema": "PR290_ASSIGNMENT_LOCAL_HOSTILE_ORACLE_V1",
                "candidate_sha": "27c83a1a12369b4b563667ff5145ae9a717b24f0",
                "status": "PASS",
                "checks": checks,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
