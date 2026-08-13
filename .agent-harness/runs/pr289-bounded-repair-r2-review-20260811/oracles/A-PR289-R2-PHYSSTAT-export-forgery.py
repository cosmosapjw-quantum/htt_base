#!/usr/bin/env python3
"""Hostile oracle: coordinated exported Planck semantic re-sign must fail closed.

Exit zero only when the frozen PR-289 replay path accepts a lane-wide rewrite of
typed semantic evidence after all unkeyed content IDs have been recomputed.  A
zero exit therefore reproduces the review finding, not candidate correctness.
"""

from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "htt" / "src"))

from common import data_identity as contracts  # noqa: E402


REGISTRY = (
    ROOT
    / "docs"
    / "research_program"
    / "post_pr275"
    / "data_registry_v2"
    / "LANE_REGISTRY_V2.json"
)


def resign_record(record: dict[str, object]) -> None:
    stable = dict(record)
    for key in ("record_id", "inspection_receipt_id", "inspected_at_utc"):
        stable.pop(key)
    record["record_id"] = contracts.canonical_sha256(stable)
    inspection = dict(record)
    inspection.pop("inspection_receipt_id")
    record["inspection_receipt_id"] = contracts.canonical_sha256(inspection)


def resign_bundle(payload: dict[str, object]) -> None:
    records = payload["records"]
    assert isinstance(records, list) and records
    first = records[0]
    assert isinstance(first, dict)
    payload["lane_admission_bundle_id"] = contracts.canonical_sha256(
        {
            "lane_id": payload["lane_id"],
            "product_id": payload["product_id"],
            "component_inventory_id": first["component_inventory_id"],
            "record_ids": [record["record_id"] for record in records],
        }
    )


def main() -> int:
    registry = contracts.load_lane_registry(REGISTRY)
    lane = registry.lane("PLANCK")
    with tempfile.TemporaryDirectory(prefix="pr289-r2-physstat-") as temp:
        descriptor = contracts._mutation_descriptor(Path(temp) / "planck", lane)
        decision = contracts.evaluate_lane_identity(
            registry=registry,
            lane_id="PLANCK",
            descriptor=descriptor,
            inspected_at_utc="2026-08-11T00:00:00+00:00",
        )
        if decision.status is not contracts.AdmissionStatus.ADMITTED_IDENTITY_ONLY:
            print(f"ORACLE_SETUP_ERROR: {decision.status.value}")
            return 2

        original = decision.as_payload()
        forged = copy.deepcopy(original)
        replacements = {
            "units_contract_id": "units:FORGED:v9",
            "coordinate_frame_id": "frame:FORGED:v9",
            "sign_orientation_convention_id": "sign:FORGED:v9",
            "directional_convention_id": "direction:FORGED:v9",
            "mask_id": "mask:FORGED:v9",
            "selection_id": "selection:FORGED:v9",
            "covariance_id": "covariance:FORGED:v9",
        }
        records = forged["records"]
        assert isinstance(records, list) and records
        for record in records:
            assert isinstance(record, dict)
            record.update(replacements)
            resign_record(record)
        resign_bundle(forged)

        try:
            replayed = contracts.replay_lane_admission_decision(
                forged, registry=registry
            )
        except contracts.DataIdentityError as exc:
            print(f"ORACLE_CANDIDATE_REJECTED_FORGERY: {exc}")
            return 1

        replayed_payload = replayed.as_payload()
        if replayed_payload == original:
            print("ORACLE_SETUP_ERROR: forged payload did not change")
            return 2
        for record in replayed_payload["records"]:
            for field, value in replacements.items():
                if record[field] != value:
                    print(f"ORACLE_SETUP_ERROR: {field} was not retained")
                    return 2
        print(
            "ORACLE_PASS_REPRODUCED: replay accepted coordinated forged "
            "Planck units/frame/sign/direction/mask/selection/covariance identities"
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
