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


def test_registered_gf_evolution_requires_all_status_bound():
    gate = classify_gf_evolution_model(
        model_kind="registered_phenomenological",
        selection_covariance_status="bound",
        boltzmann_or_gr_status="bound",
    )
    assert gate["claim_tier"] == "registered_phenomenological"
    assert gate["local_global_discriminator_allowed"] is True
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
