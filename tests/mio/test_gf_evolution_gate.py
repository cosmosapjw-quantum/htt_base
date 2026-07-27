from __future__ import annotations

from mio.formalism.isotropy_gap import classify_gf_evolution_model


def test_toy_gf_evolution_is_not_local_global_discriminator():
    gate = classify_gf_evolution_model(
        model_kind="toy_beta_z_law",
        selection_covariance_status="not_bound",
        boltzmann_or_gr_status="not_bound",
    )
    assert gate["claim_tier"] == "blocked"
    assert gate["local_global_discriminator_allowed"] is False
    assert "toy_evolution_law" in gate["blocked_reasons"]


def _complete_rank_receipt():
    return {
        "status": "MEASURED",
        "rank": 3,
        "parameter_dimension": 3,
        "transfer_id": "transfer-1",
        "mask_id": "mask-1",
        "covariance_id": "cov-1",
        "local_block_id": "local-1",
        "global_block_id": "global-1",
        "systematics_block_id": "sys-1",
        "matched_null_status": "matched_calibrated",
        "fpr_status": "passed",
    }


def test_string_statuses_alone_never_authorize_local_global():
    gate = classify_gf_evolution_model(
        model_kind="registered_phenomenological",
        selection_covariance_status="bound",
        boltzmann_or_gr_status="bound",
    )
    assert gate["claim_tier"] == "blocked"
    assert gate["local_global_discriminator_allowed"] is False
    assert "response_rank_not_measured" in gate["blocked_reasons"]


def test_complete_rank_receipt_only_enables_diagnostic_candidate():
    gate = classify_gf_evolution_model(
        model_kind="registered_phenomenological",
        selection_covariance_status="bound",
        boltzmann_or_gr_status="bound",
        response_rank_receipt=_complete_rank_receipt(),
    )
    assert gate["claim_tier"] == "diagnostic_candidate"
    assert gate["diagnostic_candidate_ready"] is True
    assert gate["local_global_discriminator_allowed"] is False
    assert gate["blocked_reasons"] == []


def test_registered_kind_still_blocked_without_covariance():
    gate = classify_gf_evolution_model(
        model_kind="registered_phenomenological",
        selection_covariance_status="not_bound",
        boltzmann_or_gr_status="bound",
    )
    assert gate["claim_tier"] == "blocked"
    assert gate["local_global_discriminator_allowed"] is False
    assert "redshift_bin_covariance_or_selection_not_bound" in gate["blocked_reasons"]
