#!/usr/bin/env python3
"""Independent PR-289 R4 oracle.

The oracle executes the frozen candidate module from its verified path, builds
fresh scratch identities, and checks native replay plus authorization binding.
It succeeds only when the cross-lane authorization-binding defect is
reproduced; it never writes outside its temporary directory.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
REGISTRY = ROOT / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
MODULE = ROOT / "htt/src/common/data_identity.py"
STAMP_A = "2026-08-11T00:00:00+00:00"
STAMP_B = "2026-08-11T01:00:00+00:00"


def resign_record(module, record: dict[str, object]) -> dict[str, object]:
    value = copy.deepcopy(record)
    stable = copy.deepcopy(value)
    for key in ("record_id", "inspection_receipt_id", "inspected_at_utc"):
        stable.pop(key)
    value["record_id"] = module.canonical_sha256(stable)
    inspection = copy.deepcopy(value)
    inspection.pop("inspection_receipt_id")
    value["inspection_receipt_id"] = module.canonical_sha256(inspection)
    return value


def rewrite_evidence(module, descriptor: dict[str, object], **updates: object) -> None:
    root = Path(str(descriptor["root"]))
    path = root / str(descriptor["evidence_relative_path"])
    evidence = json.loads(path.read_text(encoding="utf-8"))
    evidence.update(updates)
    evidence["source_locator_identity"] = module.compute_source_locator_identity(
        lane_id=str(evidence["lane_id"]),
        product_id=str(evidence["product_id"]),
        components=descriptor["components"],
        evidence_bindings=evidence,
    )
    raw = (
        json.dumps(
            evidence,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
        + b"\n"
    )
    path.write_bytes(raw)
    descriptor["evidence_sha256"] = hashlib.sha256(raw).hexdigest()


def main() -> int:
    from scripts.codex_harness import run_pr289_data_identity_v2 as runner

    module = runner._load_bound_data_identity_module(ROOT)
    observed_module_sha = hashlib.sha256(MODULE.read_bytes()).hexdigest()
    assert module.__pr289_loaded_sha256__ == observed_module_sha
    registry = module.load_lane_registry(REGISTRY)
    checks: list[str] = ["verified_candidate_module_bytes_executed"]

    with tempfile.TemporaryDirectory(prefix="pr289-r4-independent-oracle-") as temp:
        scratch = Path(temp)
        decisions = {}
        for lane_id in ("PLANCK", "CF4", "HSC_KIDS"):
            lane = registry.lane(lane_id)
            descriptor = module._mutation_descriptor(scratch / lane_id.lower(), lane)
            decision_a = module.evaluate_lane_identity(
                registry=registry,
                lane_id=lane_id,
                descriptor=descriptor,
                inspected_at_utc=STAMP_A,
            )
            assert decision_a.status.value == "ADMITTED_IDENTITY_ONLY"
            replay = module.replay_lane_admission_decision(
                decision_a.as_payload(), registry=registry
            )
            assert replay.as_payload() == decision_a.as_payload()
            decision_b = module.evaluate_lane_identity(
                registry=registry,
                lane_id=lane_id,
                descriptor=descriptor,
                inspected_at_utc=STAMP_B,
            )
            assert [r.record_id for r in decision_a.records] == [
                r.record_id for r in decision_b.records
            ]
            assert [r.inspection_receipt_id for r in decision_a.records] != [
                r.inspection_receipt_id for r in decision_b.records
            ]
            decisions[lane_id] = decision_a
            checks.append(f"{lane_id.lower()}_native_export_replay")

        planck = decisions["PLANCK"]
        assert all(r.covariance_status == "REGISTERED" for r in planck.records)
        assert all(r.sky_support_status == "REGISTERED" for r in planck.records)
        checks.append("planck_registered_covariance_and_sky")

        for field in ("covariance_status", "sky_support_status"):
            lane = registry.lane("PLANCK")
            descriptor = module._mutation_descriptor(
                scratch / f"planck-{field}", lane
            )
            rewrite_evidence(module, descriptor, **{field: "NOT_APPLICABLE"})
            refused = module.evaluate_lane_identity(
                registry=registry,
                lane_id="PLANCK",
                descriptor=descriptor,
                inspected_at_utc=STAMP_A,
            )
            assert refused.status.value == "REJECTED_MISSING_SEMANTIC_CONTRACT"
            checks.append(f"planck_{field}_contradiction_killed")

        exported = planck.as_payload()["records"][0]
        exported["license_status"] = "NOT_APPLICABLE"
        exported = resign_record(module, exported)
        try:
            module.validate_data_identity_record_payload(exported, registry=registry)
        except module.DataIdentityError as exc:
            assert "license_status" in str(exc)
        else:
            raise AssertionError("re-signed semantic contradiction was accepted")
        checks.append("exported_full_semantic_replay")

        receipt = runner._build(ROOT)
        assert receipt["terminal"] == "PASS_DATA_IDENTITY_V2_PREFLIGHT"
        assert receipt["aggregate_status"] == "NO_ADMITTED_IDENTITIES"
        assert len(receipt["mutation_results"]) == 32
        assert all(
            row["executed"] and row["activated"] and row["killed"]
            for row in receipt["mutation_results"]
        )
        assert receipt["claim_tier"] == "diagnostic_only"
        assert receipt["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
        assert receipt["transfer_source"] == "none"
        assert receipt["observed_data_executed"] is False
        assert receipt["public_use"] is False
        assert receipt["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
        assert {row["status"] for row in receipt["authorization_receipts"]} == {
            "NOT_AUTHORIZED"
        }
        checks.extend(
            ["ordered_32_mutation_kills", "claim_and_family_ceiling", "all_lanes_not_authorized"]
        )

        # Hostile cross-lane call using two legitimate factory products.  The
        # exported factory accepts a valid CF4 admission while labeling the
        # resulting receipt PLANCK and binding PLANCK's gate/plan.
        planck_lane = registry.lane("PLANCK")
        cf4_decision = decisions["CF4"]
        forged = module.build_not_authorized_receipt(planck_lane, cf4_decision)
        forged_payload = forged.as_payload()
        defect_reproduced = (
            forged_payload["lane_id"] == "PLANCK"
            and forged_payload["required_human_gate_id"] == "H-PLANCK"
            and forged_payload["analysis_plan_id"] == planck_lane.analysis_plan_id
            and forged_payload["exact_admission_record_ids"]
            == [record.record_id for record in cf4_decision.records]
            and forged_payload["lane_admission_bundle_id"]
            == cf4_decision.lane_admission_bundle_id
            and cf4_decision.lane_id == "CF4"
        )
        assert defect_reproduced, "cross-lane authorization call failed closed"

    print(
        json.dumps(
            {
                "schema": "PR289_R4_INDEPENDENT_ORACLE_V1",
                "candidate_module_sha256": observed_module_sha,
                "checks_passed": checks,
                "finding_reproduced": "CROSS_LANE_NOT_AUTHORIZED_RECEIPT_MISBINDING",
                "forged_receipt_lane": forged_payload["lane_id"],
                "source_decision_lane": cf4_decision.lane_id,
                "forged_receipt_status": forged_payload["status"],
                "forged_authorization_id": forged_payload["authorization_id"],
                "source_lane_admission_bundle_id": cf4_decision.lane_admission_bundle_id,
                "source_record_count": len(cf4_decision.records),
                "source_first_record_id": cf4_decision.records[0].record_id,
                "forged_first_record_id": forged_payload["exact_admission_record_ids"][0],
                "immediate_execution_authorized": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
