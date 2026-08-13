#!/usr/bin/env python3
"""Independent scratch oracle for the frozen PR-289 R5 physics/code review."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile

import common.data_identity as data_identity
from scripts.codex_harness import run_pr289_data_identity_v2 as runner


ROOT = Path(__file__).resolve().parents[5]
REGISTRY_PATH = (
    ROOT
    / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)
SPEC_PATH = ROOT / "docs/research_program/post_pr275/pr289_spec.yaml"
INSPECTED_AT = "2026-08-09T00:00:00+00:00"


def _admitted(root: Path, lane_id: str):
    registry = data_identity.load_lane_registry(REGISTRY_PATH)
    lane = registry.lane(lane_id)
    descriptor = data_identity._mutation_descriptor(root, lane)
    decision = data_identity.evaluate_lane_identity(
        registry=registry,
        lane_id=lane_id,
        descriptor=descriptor,
        inspected_at_utc=INSPECTED_AT,
    )
    assert decision.status is data_identity.AdmissionStatus.ADMITTED_IDENTITY_ONLY
    replayed = data_identity.replay_lane_admission_decision(
        decision.as_payload(), registry=registry
    )
    assert replayed.as_payload() == decision.as_payload()
    return registry, lane, decision


def _must_die(label: str, operation) -> dict[str, object]:
    try:
        operation()
    except data_identity.DataIdentityError as exc:
        return {"probe": label, "killed": True, "marker": str(exc)}
    raise AssertionError(f"{label} survived")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="pr289-r5-physcode-oracle-") as raw:
        scratch = Path(raw)
        registry = data_identity.load_lane_registry(REGISTRY_PATH)
        same_lane: list[str] = []
        for lane_id in ("PLANCK", "CF4", "HSC_KIDS"):
            _, lane, decision = _admitted(
                scratch / f"same-{lane_id.lower()}", lane_id
            )
            authorization = data_identity.build_not_authorized_receipt(
                lane, decision
            )
            assert authorization.status is data_identity.AuthorizationStatus.NOT_AUTHORIZED
            assert authorization.lane_id == lane_id
            assert authorization.exact_admission_record_ids
            assert (
                authorization.lane_admission_bundle_id
                == decision.lane_admission_bundle_id
            )
            same_lane.append(lane_id)

        planck = registry.lane("PLANCK")
        _, _, cf4_decision = _admitted(scratch / "cross-cf4", "CF4")
        probes = [
            _must_die(
                "cf4_decision_planck_lane",
                lambda: data_identity.build_not_authorized_receipt(
                    planck, cf4_decision
                ),
            )
        ]

        for label, field, value in (
            ("record_ordinal", "component_ordinal", 99),
            ("record_seal", "record_id", "sha256:" + "0" * 64),
            (
                "component_inventory",
                "component_inventory_id",
                "sha256:" + "0" * 64,
            ),
        ):
            _, lane, decision = _admitted(scratch / label, "PLANCK")
            object.__setattr__(decision.records[0], field, value)
            probes.append(
                _must_die(
                    label,
                    lambda lane=lane, decision=decision: (
                        data_identity.build_not_authorized_receipt(lane, decision)
                    ),
                )
            )

        _, lane, decision = _admitted(scratch / "bundle", "PLANCK")
        object.__setattr__(
            decision, "lane_admission_bundle_id", "sha256:" + "0" * 64
        )
        probes.append(
            _must_die(
                "bundle_identity",
                lambda: data_identity.build_not_authorized_receipt(lane, decision),
            )
        )

        mutation_ids = data_identity.registered_mutation_ids(SPEC_PATH)
        mutation_results = data_identity._run_registered_mutations(
            mutation_ids,
            registry=registry,
            spec_path=SPEC_PATH,
            source_bindings=runner._source_bindings(),
        )
        data_identity.validate_mutation_results(mutation_ids, mutation_results)
        receipt = runner._build()
        assert len(mutation_ids) == 33
        assert all(
            row.executed and row.activated and row.killed
            for row in mutation_results
        )
        assert receipt["claim_tier"] == "diagnostic_only"
        assert receipt["claim_level"] == {
            "scheme": "roadmap_rescue_v1",
            "level": "C2",
        }
        assert receipt["transfer_source"] == "none"
        assert receipt["observed_data_executed"] is False
        assert receipt["public_use"] is False
        assert receipt["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
        assert all(
            row["status"] == "NOT_AUTHORIZED"
            for row in receipt["authorization_receipts"]
        )

        payload = {
            "schema": "pr289.r5.physcode.oracle.v1",
            "status": "PASS",
            "same_lane_replay": same_lane,
            "hostile_probes": probes,
            "mutation_count": len(mutation_results),
            "mutation_ids_sha256": data_identity.canonical_sha256(
                list(mutation_ids)
            ),
            "all_mutations_executed_activated_killed": True,
            "receipt_content_id": receipt["receipt_content_id"],
            "claim_boundary": {
                "claim_tier": receipt["claim_tier"],
                "claim_level": receipt["claim_level"],
                "transfer_source": receipt["transfer_source"],
                "observed_data_executed": receipt["observed_data_executed"],
                "public_use": receipt["public_use"],
                "family_identification_gate": receipt[
                    "family_identification_gate"
                ],
            },
        }
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
