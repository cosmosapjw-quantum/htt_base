#!/usr/bin/env python3
"""Independent, assignment-local PR-289 R3 physics/code boundary oracle."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.codex_harness import run_pr289_data_identity_v2 as runner


def resign_record(module, record: dict[str, object]) -> None:
    stable = dict(record)
    for key in ("record_id", "inspection_receipt_id", "inspected_at_utc"):
        stable.pop(key)
    record["record_id"] = module.canonical_sha256(stable)
    inspection = dict(record)
    inspection.pop("inspection_receipt_id")
    record["inspection_receipt_id"] = module.canonical_sha256(inspection)


def resign_bundle(module, payload: dict[str, object]) -> None:
    records = payload["records"]
    payload["lane_admission_bundle_id"] = module.canonical_sha256(
        {
            "lane_id": payload["lane_id"],
            "product_id": payload["product_id"],
            "component_inventory_id": records[0]["component_inventory_id"],
            "record_ids": [row["record_id"] for row in records],
        }
    )


def expect_replay_refusal(module, registry, pristine, field, value) -> str:
    payload = copy.deepcopy(pristine)
    payload["records"][0][field] = value
    resign_record(module, payload["records"][0])
    resign_bundle(module, payload)
    try:
        module.replay_lane_admission_decision(payload, registry=registry)
    except module.DataIdentityError as exc:
        return str(exc)
    raise AssertionError(f"re-signed exported field survived replay: {field}")


def main() -> int:
    module = runner._load_bound_data_identity_module(ROOT)
    registry = module.load_lane_registry(runner.REGISTRY)
    checks: dict[str, object] = {}

    module_sha = hashlib.sha256(runner.MODULE.read_bytes()).hexdigest()
    assert module.__pr289_loaded_sha256__ == module_sha
    assert Path(module.build_data_identity_v2_receipt.__code__.co_filename).resolve() == runner.MODULE.resolve()
    checks["verified_bytes_equal_executed_module"] = module_sha

    with tempfile.TemporaryDirectory(prefix="pr289-r3-oracle-") as temporary:
        scratch = Path(temporary)
        descriptor = module._mutation_descriptor(scratch / "planck-primary", registry.lane("PLANCK"))
        decision = module.evaluate_lane_identity(
            registry=registry,
            lane_id="PLANCK",
            descriptor=descriptor,
            inspected_at_utc="2026-08-11T00:00:00+00:00",
        )
        assert decision.status is module.AdmissionStatus.ADMITTED_IDENTITY_ONLY
        pristine = decision.as_payload()

        semantic_mutations = {
            "source_locator_kind": "unregistered_locator",
            "regular_file_status": "NOT_VERIFIED",
            "symlink_status": "ALIAS_PRESENT",
            "completeness_status": "INCOMPLETE",
            "acquisition_status": "PARTIAL",
            "release_name": "changed release",
            "release_version": "changed-v2",
            "release_identity": "docs:changed/release-v2",
            "license_identity": "spdx:MIT",
            "license_status": "UNBOUND",
            "units_contract_id": "units:changed:v2",
            "coordinate_frame_id": "frame:changed:v2",
            "sign_orientation_convention_id": "sign:changed:v2",
            "directional_convention_id": "direction:changed:v2",
            "harmonic_convention_id": "harmonic:changed:v2",
            "mask_id": "mask:changed:v2",
            "selection_id": "selection:changed:v2",
            "sky_support_id": "sky:changed:v2",
            "covariance_id": "covariance:changed:v2",
            "covariance_status": "NOT_APPLICABLE",
            "null_ensemble_id": "null:changed:v2",
            "null_ensemble_status": "NOT_APPLICABLE",
            "transfer_source": "native_bass",
            "transfer_function_spec_id": "native:unregistered",
            "transfer_provenance_status": "NATIVE_VALIDATED",
            "sky_support_status": "NOT_APPLICABLE",
            "native_identity_profile_id": "sha256:" + "0" * 64,
        }
        refusals = {
            field: expect_replay_refusal(module, registry, pristine, field, value)
            for field, value in semantic_mutations.items()
        }
        assert len(refusals) == 27
        checks["exported_semantic_replay_refusals"] = refusals

        for field in ("covariance_status", "sky_support_status"):
            value = module._mutation_descriptor(
                scratch / f"planck-{field}", registry.lane("PLANCK")
            )
            module._rewrite_mutation_evidence(value, {field: "NOT_APPLICABLE"})
            refused = module.evaluate_lane_identity(
                registry=registry,
                lane_id="PLANCK",
                descriptor=value,
                inspected_at_utc="2026-08-11T00:00:00+00:00",
            )
            assert refused.status is module.AdmissionStatus.REJECTED_MISSING_SEMANTIC_CONTRACT
        checks["planck_applicable_status_gate"] = ["covariance_status", "sky_support_status"]

        profiles = {}
        for lane_id in ("PLANCK", "CF4", "HSC_KIDS"):
            value = module._mutation_descriptor(
                scratch / lane_id.lower(), registry.lane(lane_id)
            )
            admitted = module.evaluate_lane_identity(
                registry=registry,
                lane_id=lane_id,
                descriptor=value,
                inspected_at_utc="2026-08-11T00:00:00+00:00",
            )
            assert admitted.complete
            replayed = module.replay_lane_admission_decision(
                admitted.as_payload(), registry=registry
            )
            assert replayed.as_payload() == admitted.as_payload()
            profiles[lane_id] = admitted.records[0].native_identity_profile_id
        checks["native_profile_exact_replay"] = profiles

        parent_root = scratch / "output-root"
        parent = parent_root / "docs/generated"
        detached = parent_root / "docs/generated-detached"
        parent.mkdir(parents=True)
        output = parent / "receipt.json"
        parent_fd, parent_identity = runner._open_bound_output_parent(
            root=parent_root, output=output, require_existing=False
        )
        try:
            parent.rename(detached)
            parent.mkdir()
            try:
                runner._atomic_write(
                    b"{}\n",
                    output=output,
                    parent_fd=parent_fd,
                    parent_identity=parent_identity,
                )
            except RuntimeError as exc:
                assert "parent directory identity changed" in str(exc)
            else:
                raise AssertionError("late output-parent replacement survived")
        finally:
            os.close(parent_fd)
        assert not output.exists()
        checks["descriptor_relative_atomic_output_containment"] = "fail_closed"

    receipt = json.loads(runner.OUTPUT.read_text(encoding="utf-8"))
    import yaml

    spec = yaml.safe_load(runner.SPEC.read_text(encoding="utf-8"))
    expected_mutations = [row["mutation_id"] for row in spec["mutation_registry"]]
    observed_mutations = receipt["mutation_results"]
    assert len(expected_mutations) == 32 == len(set(expected_mutations))
    assert expected_mutations == [row["mutation_id"] for row in observed_mutations]
    assert all(
        row["executed"] is True
        and row["activated"] is True
        and row["killed"] is True
        and row["observed_marker"]
        for row in observed_mutations
    )
    checks["ordered_mutation_kills"] = 32

    alias_outputs = {}
    for executable in (Path("/usr/bin/python"), Path("/usr/bin/python3")):
        if not executable.exists():
            continue
        completed = subprocess.run(
            [str(executable), "-B", str(runner.RUNNER.relative_to(ROOT)), "check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env={
                key: value
                for key, value in os.environ.items()
                if key not in {"PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP"}
            },
        )
        assert completed.returncode == 0, completed.stderr
        alias_outputs[str(executable)] = hashlib.sha256(completed.stdout.encode()).hexdigest()
    assert len(set(alias_outputs.values())) <= 1
    checks["interpreter_alias_invariance"] = alias_outputs

    production = runner.MODULE.read_text(encoding="utf-8") + "\n" + runner.RUNNER.read_text(encoding="utf-8")
    forbidden_inference = re.findall(
        r"\b(?:prior|priors|likelihood|posterior|posteriors|bayes(?:ian)?|evidence term|family identification|geometry detected)\b",
        production,
        flags=re.IGNORECASE,
    )
    assert not forbidden_inference, forbidden_inference
    assert receipt["claim_tier"] == "diagnostic_only"
    assert receipt["transfer_source"] == "none"
    assert receipt["observed_data_executed"] is False
    assert receipt["public_use"] is False
    assert receipt["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert all(row["status"] == "NOT_AUTHORIZED" for row in receipt["authorization_receipts"])
    checks["inference_and_family_ceiling"] = "blocked"
    checks["q_f_g_local_global_status"] = "not_computed_or_promoted"

    print(json.dumps({"status": "pass", "checks": checks}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
