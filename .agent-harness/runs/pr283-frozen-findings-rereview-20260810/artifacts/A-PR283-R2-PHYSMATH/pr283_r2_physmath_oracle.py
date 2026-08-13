#!/usr/bin/env python3
"""Independent bounded oracle for the three PR-283 R2 repaired findings."""

from __future__ import annotations

import hashlib
import json
import math

from scripts.codex_harness import run_pr283_weak_identification as runner


def _identity(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("ascii")).hexdigest()


def main() -> None:
    runner._activate_sources()

    from common import open_set_response_classes as open_set_module
    from common.open_set_response_classes import OpenSetResponseError
    from common.source_separation import (
        SourceSeparationDecisionStatus,
        build_weak_identification_threshold_contract,
        evaluate_source_separation,
    )
    from htt.statistics.open_set_response_classes import (
        PR283_DEFAULT_THRESHOLD_CONTRACT,
        source_separation_gate_from_pr256,
    )

    _, registered = runner._load_contract()
    _, contexts = runner._build_cases(registered)
    ill_conditioned = contexts[
        "pr283.full-rank-small-relative-singular-value.v1"
    ]

    relaxed = build_weak_identification_threshold_contract(
        minimum_principal_angle_radians=0.2,
        minimum_normalizer_bound_relative_joint_singular_value=0.001,
        parameter_coordinate_units=runner.UNITS,
    )
    relaxed_rejection = None
    try:
        source_separation_gate_from_pr256(
            ill_conditioned["report"],
            classes=ill_conditioned["classes"],
            covariance=ill_conditioned["covariance"],
            nuisance_tangent=None,
            normalizer=ill_conditioned["normalizer"],
            threshold_contract=relaxed,
        )
    except OpenSetResponseError as exc:
        relaxed_rejection = str(exc)
    assert relaxed_rejection == (
        "threshold_contract must equal the registered PR-283 contract"
    )
    assert registered.contract_id == PR283_DEFAULT_THRESHOLD_CONTRACT.contract_id
    assert relaxed.contract_id != registered.contract_id

    decision_base = {
        "source_geometry_report_id": _identity("oracle-report"),
        "covariance_id": _identity("oracle-covariance"),
        "nuisance_tangent_id": _identity("oracle-nuisance"),
        "normalizer_id": "registered-normalizer",
        "normalizer_source_identity": "registered dimensionless beta convention",
        "normalizer_coordinate_map_id": _identity("oracle-normalizer-map"),
        "parameter_coordinate_units": runner.UNITS,
        "provider_available": True,
        "covariance_supported": True,
        "local_parameter_count": 1,
        "global_parameter_count": 1,
        "local_rank": 1,
        "global_rank": 1,
        "joint_rank": 2,
        "threshold_contract": registered,
    }
    angle_equality = evaluate_source_separation(
        **decision_base,
        principal_angles_radians=(0.2,),
        joint_singular_values=(1.0, 0.02),
    )
    singular_equality = evaluate_source_separation(
        **decision_base,
        principal_angles_radians=(math.pi / 2.0,),
        joint_singular_values=(1.0, 0.01),
    )
    strict_above = evaluate_source_separation(
        **decision_base,
        principal_angles_radians=(0.200001,),
        joint_singular_values=(1.0, 0.010001),
    )
    assert angle_equality.status is SourceSeparationDecisionStatus.WEAKLY_IDENTIFIED
    assert singular_equality.status is SourceSeparationDecisionStatus.WEAKLY_IDENTIFIED
    assert strict_above.status is SourceSeparationDecisionStatus.SEPARABLE_CANDIDATE

    original = open_set_module.classify_open_set_response
    mutant_calls: list[dict[str, str]] = []

    def observe_mutant_execution(**kwargs):
        gate = kwargs["source_separation_gate"]
        result = original(**kwargs)
        decision = gate.source_separation_decision
        if decision is not None and gate.status.value != decision.status.value:
            mutant_calls.append(
                {
                    "gate_status": gate.status.value,
                    "bound_decision_status": decision.status.value,
                    "classifier_status": result.status.value,
                }
            )
        return result

    open_set_module.classify_open_set_response = observe_mutant_execution
    try:
        mutation_rows = runner._run_mutations(contexts)
    finally:
        open_set_module.classify_open_set_response = original

    assert runner._validate_mutation_results(mutation_rows) == []
    assert [row["classifier_status"] for row in mutant_calls] == [
        "RESPONSE_CLASS_CANDIDATE",
        "UNKNOWN_CLASS",
        "EQUIVALENCE_CLASS",
    ]
    selected_rows = {
        row["mutation_id"]: row
        for row in mutation_rows
        if row["mutation_id"]
        in {"MU283-WEAK-AS-SEPARABLE", "MU283-WEAK-PRECEDENCE-DRIFT"}
    }
    assert set(selected_rows) == {
        "MU283-WEAK-AS-SEPARABLE",
        "MU283-WEAK-PRECEDENCE-DRIFT",
    }
    assert all(
        row["executed"] and row["activated"] and row["killed"]
        for row in selected_rows.values()
    )

    print(
        json.dumps(
            {
                "schema": "htt.pr283.r2_physmath_oracle.v1",
                "status": "PASS",
                "registered_threshold_contract_id": registered.contract_id,
                "relaxed_threshold_contract_id": relaxed.contract_id,
                "relaxed_threshold_rejection": relaxed_rejection,
                "equality_semantics": {
                    "angle_equality": angle_equality.status.value,
                    "singular_equality": singular_equality.status.value,
                    "both_strictly_above": strict_above.status.value,
                },
                "forbidden_classifier_paths_executed": mutant_calls,
                "selected_mutation_rows": selected_rows,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
