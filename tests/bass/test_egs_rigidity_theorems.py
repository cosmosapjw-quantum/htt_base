from __future__ import annotations

import pytest


def test_boosted_radiation_orbit_is_synthetic_and_not_family_claim() -> None:
    from bass.geometry.egs_rigidity import boosted_radiation_orbit

    payload = boosted_radiation_orbit(
        beta=0.1,
        direction_norm=1.0,
        theorem_id="G2",
        systematics_status="not_bound",
        mask_status="not_bound",
        null_status="not_bound",
    ).as_payload()

    assert payload["orbit_status"] == "synthetic_boosted_radiation_orbit"
    assert payload["data_facing_residual_allowed"] is False
    assert payload["gamma"] > 1.0
    assert payload["owner"] == "BASS"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["native_solver_result"] is False
    assert payload["family_identification"] is False
    assert payload["production_claim_allowed"] is False

    under_gated = boosted_radiation_orbit(
        beta=0.1,
        direction_norm=1.0,
        theorem_id="G2",
        systematics_status="bound",
        mask_status="bound",
        null_status="bound",
    ).as_payload()
    assert under_gated["data_facing_residual_allowed"] is False
    assert under_gated["residual_gate_status"] == "blocked_observational_residual_provenance_not_bound"
    assert under_gated["raw_data_provenance_status"] == "not_bound"
    assert under_gated["native_atlas_status"] == "not_bound"


def test_slope_degeneracy_blocks_slope_only_source_discrimination() -> None:
    from bass.geometry.egs_rigidity import classify_slope_degeneracy

    degenerate = classify_slope_degeneracy(
        slope_a=1.0,
        slope_b=1.0 + 1.0e-8,
        tolerance=1.0e-6,
        equation_of_state_w=0.0,
        theorem_id="G5",
    ).as_payload()
    assert degenerate["classification"] == "slope_degenerate"
    assert degenerate["slope_only_source_discrimination_allowed"] is False

    stiff = classify_slope_degeneracy(
        slope_a=1.0,
        slope_b=1.2,
        tolerance=1.0e-6,
        equation_of_state_w=1.0,
        theorem_id="G5",
    ).as_payload()
    assert stiff["classification"] == "blocked_stiff_fluid_singularity"
    assert stiff["slope_only_source_discrimination_allowed"] is False


def test_almost_egs_gate_requires_all_derivative_and_weyl_diagnostics() -> None:
    from bass.geometry.egs_rigidity import almost_egs_promotion_gate

    blocked = almost_egs_promotion_gate(
        acceleration_bound=None,
        temperature_gradient_bound=0.01,
        derivative_bound=0.02,
        weyl_diagnostics_bound=0.03,
        theorem_id="G2",
    ).as_payload()
    assert blocked["egs_status"] == "blocked_acceleration_temp_gradient_missing"
    assert blocked["almost_egs_promotion_allowed"] is False

    ok = almost_egs_promotion_gate(
        acceleration_bound=0.01,
        temperature_gradient_bound=0.01,
        derivative_bound=0.02,
        weyl_diagnostics_bound=0.03,
        theorem_id="G2",
    ).as_payload()
    assert ok["egs_status"] == "synthetic_almost_egs_bound"
    assert ok["almost_egs_promotion_allowed"] is False
    assert ok["diagnostic_bound"] == pytest.approx(0.07)


def test_bianchi_i_exact_flow_gate_blocks_missing_assumptions() -> None:
    from bass.geometry.egs_rigidity import bianchi_i_exact_flow_gate

    blocked = bianchi_i_exact_flow_gate(
        assumptions=("homogeneous_background",),
        theorem_id="G2",
    ).as_payload()
    assert blocked["exact_flow_status"] == "blocked_missing_bianchi_i_assumptions"
    assert blocked["exact_flow_use_allowed"] is False

    ok = bianchi_i_exact_flow_gate(
        assumptions=("homogeneous_background", "bianchi_i", "diagonal_shear"),
        theorem_id="G2",
    ).as_payload()
    assert ok["exact_flow_status"] == "synthetic_bianchi_i_exact_flow_scope"
    assert ok["exact_flow_use_allowed"] is True


def test_geometry_package_exports_egs_helpers() -> None:
    import bass.geometry as geometry
    from bass.geometry.egs_rigidity import boosted_radiation_orbit

    assert geometry.boosted_radiation_orbit is boosted_radiation_orbit
