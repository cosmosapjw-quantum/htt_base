"""PR-204 ACT validated-band release-summary/raw-QE closure.

This adapter consumes the frozen PR-177 release-simulation result and the
PR-152 raw-QE availability decision.  It does not recompute ACT data, create a
likelihood, or turn a released-kappa injection into pre-QE response evidence.
"""
from __future__ import annotations

from typing import Mapping

from .act_inband_modulation import semantic_digest


TERMINAL = "EVIDENCE_READY_RELEASE_SUMMARY_RAW_QE_BLOCKED"
RAW_QE_BLOCKER = "BLOCKED_INPUT_RAW_QE_EXECUTION_RECEIPT"
ACCEPTED_RESULT = "NO_RESOLVED_COUPLING_AT_CURRENT_MC_RESOLUTION"
REQUEST = "release_summary_closure"


class ActModulationClosureError(ValueError):
    """Raised when an input or requested output exceeds the PR-204 contract."""


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ActModulationClosureError(f"{label} must be a mapping")
    return value


def _semantic_errors(label: str, payload: Mapping[str, object]) -> list[str]:
    if payload.get("semantic_digest") != semantic_digest(payload):
        return [f"{label} semantic digest mismatch"]
    return []


def release_summary_errors(
    spec: Mapping[str, object],
    result: Mapping[str, object],
    mask: Mapping[str, object],
    mc: Mapping[str, object],
    result_card: Mapping[str, object],
) -> list[str]:
    """Validate the frozen PR-177 conditional-null branch without raw replay."""

    errors: list[str] = []
    release = _mapping(spec.get("release_summary_branch"), label="release spec")
    expected_support = dict(
        _mapping(release.get("exact_support"), label="release support spec")
    )
    expected_fractions = _mapping(
        release.get("required_rank_fractions"), label="rank-fraction spec"
    )
    expected_relation = release.get("required_relation_to_alpha")
    expected_count = release.get("release_simulation_count")
    expected_result = release.get("accepted_scientific_result")

    for label, payload in (
        ("result", result),
        ("mask", mask),
        ("mc", mc),
        ("result_card", result_card),
    ):
        errors.extend(_semantic_errors(label, payload))
        if payload.get("analysis_support") != expected_support:
            errors.append(f"{label} exact validated-band support mismatch")
        if payload.get("owner") != "OBSSTAT" or payload.get("public_use") is not False:
            errors.append(f"{label} owner/public-use boundary mismatch")
        if payload.get("scientific_result") != expected_result:
            errors.append(f"{label} scientific result drift")

    if result.get("process_execution_status") != "PASS_REPRODUCIBLE_RESULT":
        errors.append("PR-177 result process status is not reproducible PASS")
    if result.get("release_simulation_count") != expected_count:
        errors.append("release simulation count mismatch")
    if result.get("raw_qe_reproduced") is not False:
        errors.append("release result falsely claims raw-QE reproduction")
    if result.get("physical_interpretation") != "not_evaluated":
        errors.append("release result promoted a physical interpretation")

    if mask.get("candidate_survives_registered_mask_control") is not False:
        errors.append("registered mask control does not preserve the null disposition")
    if mask.get("control_scope") != (
        "bounded_reproduced_or_not_reproduced_by_this_control_no_causal_attribution"
    ):
        errors.append("mask-control causal boundary mismatch")

    lineage = _mapping(mc.get("replicate_lineage"), label="MC replicate lineage")
    if (
        lineage.get("replicate_count") != 400
        or lineage.get("deleted_units_unique") is not True
        or lineage.get("observed_unit_deleted") is not False
        or lineage.get("full_sample_ensemble_transform_reused") is not False
        or lineage.get("lineage_status") != "CERTIFIED_FOR_PR177_RANK_FUNCTIONAL"
    ):
        errors.append("finite-ensemble lineage mismatch")
    if mc.get("gaussian_sigma_emitted") is not False or mc.get(
        "iid_binomial_interval_used"
    ) is not False:
        errors.append("forbidden Gaussian or iid-binomial interpretation present")

    ranks = _mapping(result_card.get("rank_summary"), label="rank summary")
    for name in ("controlled", "raw", "mask_change"):
        row = _mapping(ranks.get(name), label=f"rank summary {name}")
        if row.get("rank_fraction") != expected_fractions.get(name):
            errors.append(f"{name} rank fraction drift")
        if row.get("relation_to_alpha") != expected_relation:
            errors.append(f"{name} alpha relation drift")
    if result_card.get("raw_qe_reproduction") is not False:
        errors.append("result card falsely claims raw-QE reproduction")
    if result_card.get("detection_claim") is not False:
        errors.append("result card promotes a detection")
    if result_card.get("family_identification") is not False:
        errors.append("result card promotes family identification")
    return list(dict.fromkeys(errors))


def raw_qe_blocker_errors(
    spec: Mapping[str, object],
    availability: Mapping[str, object],
    inventory: Mapping[str, object],
) -> list[str]:
    """Require the complete named blocker set for the unexecuted raw-QE branch."""

    errors: list[str] = []
    raw = _mapping(spec.get("raw_qe_branch"), label="raw-QE spec")
    required = raw.get("required_missing_inputs")
    if not isinstance(required, list) or any(not isinstance(v, str) for v in required):
        raise ActModulationClosureError("raw-QE required input list is malformed")
    expected = set(required)
    missing = inventory.get("local_missing_raw_qe_inputs")
    if not isinstance(missing, list) or set(missing) != expected or len(missing) != len(expected):
        errors.append("raw-QE blocker inventory is incomplete or drifted")
    if availability.get("decision") != raw.get("accepted_decision"):
        errors.append("raw-QE availability decision drift")
    if availability.get("raw_qe_available") is not False:
        errors.append("positive raw-QE input requires a separate configuration validator")
    if availability.get("readiness_evidence_complete") is not False:
        errors.append("raw-QE readiness was promoted without the execution receipt")
    receipt = _mapping(
        inventory.get("raw_qe_readiness_receipt"), label="raw-QE readiness receipt"
    )
    if receipt.get("ready") is not False or receipt.get("provided") is not False:
        errors.append("raw-QE execution receipt unexpectedly claims readiness")
    if receipt.get("missing_or_invalid") != ["typed_execution_receipt"]:
        errors.append("raw-QE typed execution receipt blocker mismatch")
    if inventory.get("validated_ell_range") != [40, 763]:
        errors.append("ACT release validated-range inventory drift")
    return list(dict.fromkeys(errors))


def build_closure_card(
    *,
    spec: Mapping[str, object],
    result: Mapping[str, object],
    mask: Mapping[str, object],
    mc: Mapping[str, object],
    result_card: Mapping[str, object],
    availability: Mapping[str, object],
    inventory: Mapping[str, object],
    requested_output: str = REQUEST,
) -> dict[str, object]:
    """Build the sole supported PR-204 consumer output."""

    forbidden = spec.get("forbidden_requests")
    if requested_output != REQUEST:
        if isinstance(forbidden, list) and requested_output in forbidden:
            raise ActModulationClosureError(
                f"unsupported evidence request: {requested_output}"
            )
        raise ActModulationClosureError(f"unsupported output: {requested_output}")
    errors = [
        *release_summary_errors(spec, result, mask, mc, result_card),
        *raw_qe_blocker_errors(spec, availability, inventory),
    ]
    if errors:
        raise ActModulationClosureError("; ".join(errors))

    rank_summary = _mapping(result_card["rank_summary"], label="rank summary")
    source_identities = dict(
        _mapping(spec.get("source_identities"), label="source identities")
    )
    payload: dict[str, object] = {
        "schema": "htt.pr204.act_modulation_closure.v1",
        "owner": "OBSSTAT",
        "implementation_scope": ["obsstat"],
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
        "claim_id": "C-PR204-ACT-CLOSURE",
        "claim_status": "CONDITIONAL",
        "evidence_type": "artifact",
        "public_use": False,
        "publication_use": False,
        "transfer_source": "none",
        "terminal": TERMINAL,
        "process_status": "COMPLETED_SUCCESS_WITH_TYPED_BLOCKED_BRANCH",
        "scientific_result": ACCEPTED_RESULT,
        "scientific_effect": "none_new_reuses_pr177_conditional_null",
        "sky_support_status": result["sky_support_status"],
        "covariance_status": result["covariance_status"],
        "null_mock_status": result["null_mock_status"],
        "release_summary": {
            "status": "CLOSED_CONDITIONAL_NULL_COMPARISON",
            "analysis_support": dict(result["analysis_support"]),
            "release_simulation_count": 400,
            "rank_summary": {name: dict(_mapping(rank_summary[name], label=name)) for name in ("controlled", "raw", "mask_change")},
            "mask_control": "registered_MK_squared_sensitivity_only_no_causal_attribution",
            "raw_qe_reproduced": False,
            "physical_interpretation": "not_evaluated",
        },
        "raw_qe_branch": {
            "status": RAW_QE_BLOCKER,
            "missing_inputs": list(spec["raw_qe_branch"]["required_missing_inputs"]),
            "typed_execution_receipt": "missing",
            "raw_qe_reproduced": False,
        },
        "response_and_injection_boundary": {
            "release_simulation_rank_calibration": "PASS_REUSED_PR177",
            "pre_qe_injection_coverage": RAW_QE_BLOCKER,
            "post_reconstruction_injection_as_pre_qe_response": "FORBIDDEN",
            "amplitude_constraint": "NOT_COMPUTED",
        },
        "author_gates": dict(_mapping(spec.get("author_gates"), label="author gates")),
        "independence_gate": "OPEN",
        "anisotropic_modulation_claim_status": (
            "WITHHELD_PRE_QE_RESPONSE_COVERAGE_NOT_COMPUTED"
        ),
        "detection_claim": False,
        "isotropy_claim": False,
        "physical_attribution": False,
        "family_identification": False,
        "source_sha256": source_identities,
        "unresolved_inputs": list(spec["raw_qe_branch"]["required_missing_inputs"]),
        "caveats": [
            "Conditional on the exact PR-177 released reconstruction and 400-member release ensemble.",
            "The registered mask-squared control is a bounded sensitivity and has no causal interpretation.",
            "Raw-QE/RDN0 and pre-QE injection coverage were not executed.",
            "No amplitude, detection, isotropy, physical-response, geometry, or family-identification claim is supported.",
        ],
    }
    payload["semantic_digest"] = semantic_digest(payload)
    return payload


__all__ = [
    "ACCEPTED_RESULT",
    "ActModulationClosureError",
    "RAW_QE_BLOCKER",
    "REQUEST",
    "TERMINAL",
    "build_closure_card",
    "raw_qe_blocker_errors",
    "release_summary_errors",
]
