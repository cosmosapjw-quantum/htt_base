from __future__ import annotations

import pytest


def test_exponential_memory_bound_requires_positive_collision_gap() -> None:
    from bass.kinetic.boltzmann_memory import exponential_memory_bound

    result = exponential_memory_bound(
        initial_norm=1.0,
        source_envelope=0.2,
        collision_gap=0.5,
        time_span=3.0,
        theorem_id="B4",
    )
    payload = result.as_payload()

    assert payload["owner"] == "BASS"
    assert payload["implementation_scope"] == "bass_py"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["memory_status"] == "synthetic_exponential_forgetting_bound"
    assert payload["memory_bound"] > 0.0
    assert payload["native_solver_result"] is False
    assert payload["family_identification"] is False

    blocked = exponential_memory_bound(
        initial_norm=1.0,
        source_envelope=0.2,
        collision_gap=-0.1,
        time_span=3.0,
        theorem_id="B4",
    ).as_payload()
    assert blocked["memory_status"] == "blocked_collision_gap_nonpositive"
    assert blocked["memory_bound"] is None


def test_angular_kl_multipole_bound_blocks_unbounded_bridge() -> None:
    from bass.kinetic.tight_coupling_bounds import angular_kl_multipole_bound

    result = angular_kl_multipole_bound(
        ell_max=5,
        bridge_operator_norm=0.2,
        source_norm=0.3,
        theorem_id="S1",
    )
    payload = result.as_payload()
    assert payload["multipole_status"] == "synthetic_angular_kl_bound"
    assert payload["multipole_bound"] == pytest.approx(0.3 * 0.2 / 6.0)
    assert payload["production_claim_allowed"] is False

    blocked = angular_kl_multipole_bound(
        ell_max=5,
        bridge_operator_norm=None,
        source_norm=0.3,
        theorem_id="S1",
    ).as_payload()
    assert blocked["multipole_status"] == "blocked_unbounded_multipole_bridge"
    assert blocked["multipole_bound"] is None

    convention_blocked = angular_kl_multipole_bound(
        ell_max=5,
        bridge_operator_norm=0.2,
        source_norm=0.3,
        harmonic_convention_status="not_bound",
        theorem_id="S1",
    ).as_payload()
    assert convention_blocked["multipole_status"] == "blocked_harmonic_convention_not_bound"


def test_visibility_cancellation_no_go_blocks_incoherent_los_and_rank_loss() -> None:
    from bass.kinetic.visibility_rigidity import visibility_cancellation_no_go

    ok = visibility_cancellation_no_go(
        source_rank=2,
        line_of_sight_phase_coherent=True,
        visibility_width=0.04,
        theorem_id="B4",
        collision_gap_status="positive_bound",
        kernel_floor_status="positive_bound",
        mask_support_status="bound",
    ).as_payload()
    assert ok["no_go_status"] == "synthetic_visibility_cancellation_no_go"
    assert ok["source_upper_bound_allowed"] is True

    missing_provenance = visibility_cancellation_no_go(
        source_rank=2,
        line_of_sight_phase_coherent=True,
        visibility_width=0.04,
        theorem_id="B4",
    ).as_payload()
    assert missing_provenance["no_go_status"] == "blocked_visibility_provenance_not_bound"
    assert missing_provenance["source_upper_bound_allowed"] is False
    assert "visibility_gap_kernel_mask_not_bound_blocks_source_upper_bound" in missing_provenance["kill_switches"]

    incoherent = visibility_cancellation_no_go(
        source_rank=2,
        line_of_sight_phase_coherent=False,
        visibility_width=0.04,
        theorem_id="B4",
    ).as_payload()
    assert incoherent["no_go_status"] == "blocked_line_of_sight_sign_phase_incoherence"
    assert incoherent["source_upper_bound_allowed"] is False

    rank_lost = visibility_cancellation_no_go(
        source_rank=0,
        line_of_sight_phase_coherent=True,
        visibility_width=0.04,
        theorem_id="B4",
    ).as_payload()
    assert rank_lost["no_go_status"] == "blocked_source_rank_near_zero"
    assert rank_lost["source_upper_bound_allowed"] is False


def test_kinetic_package_exports_theorem_helpers() -> None:
    import bass.kinetic as kinetic
    from bass.kinetic.boltzmann_memory import exponential_memory_bound
    from bass.kinetic.tight_coupling_bounds import angular_kl_multipole_bound

    assert kinetic.exponential_memory_bound is exponential_memory_bound
    assert kinetic.angular_kl_multipole_bound is angular_kl_multipole_bound
