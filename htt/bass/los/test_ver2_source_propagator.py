from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import get_type
from bass.los import (
    PropagatorMode,
    SourcePropagator,
    SourcePropagatorConfig,
    assert_publication_ready_propagator,
    build_source_propagator,
    propagator_evidence_for_config,
)
from bass.los.ver2_source_propagator import build_source_propagator_stub
from bass.runtime import FeatureStatus


def _complete_los_source(
    *,
    theta_0: float,
    pi_m0: float,
    kappa: float = 0.0,
    psi_m0: float = 0.0,
    isw_m0: float = 0.0,
    v_b_m0: float = 0.0,
    pi_m_plus2: float = 0.0,
    pi_m_minus2: float = 0.0,
) -> dict[str, float]:
    return {
        "kappa": float(kappa),
        "optical_depth": float(kappa),
        "theta_0_m0": float(theta_0),
        "psi_m0": float(psi_m0),
        "phi_dot_plus_psi_dot_m0": float(isw_m0),
        "v_b_m0": float(v_b_m0),
        "pi_m0": float(pi_m0),
        "theta_0_m_plus2": 0.0,
        "psi_m_plus2": 0.0,
        "phi_dot_plus_psi_dot_m_plus2": 0.0,
        "v_b_m_plus2": 0.0,
        "pi_m_plus2": float(pi_m_plus2),
        "theta_0_m_minus2": 0.0,
        "psi_m_minus2": 0.0,
        "phi_dot_plus_psi_dot_m_minus2": 0.0,
        "v_b_m_minus2": 0.0,
        "pi_m_minus2": float(pi_m_minus2),
    }


def test_flrw_validation_mode_requires_explicit_validation_flag() -> None:
    with pytest.raises(ValueError, match="flrw_validation_only"):
        SourcePropagatorConfig(
            mode=PropagatorMode.FLRW_VALIDATION,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="flrw_scalar_validation",
        )


def test_production_modes_forbid_flrw_validation_kernel() -> None:
    with pytest.raises(ValueError, match="FLRW scalar kernels"):
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.APPROXIMATE,
            polarization_rotation=FeatureStatus.APPROXIMATE,
            flrw_validation_only=True,
        )


def test_propagator_stub_is_observer_neutral_and_mode_coupled() -> None:
    stub = build_source_propagator_stub(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.APPROXIMATE,
            polarization_rotation=FeatureStatus.APPROXIMATE,
        )
    )
    assert stub.ready is False
    assert stub.observer_neutral is True
    assert stub.mode_coupling_expected is True


def test_live_propagator_builder_returns_ready_covariance_bundle() -> None:
    propagator = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.APPROXIMATE,
            polarization_rotation=FeatureStatus.APPROXIMATE,
            kernel_family="class_b_helical_matrix_approx",
        ),
        structure=get_type("VII_h"),
        eta_grid_mpc=np.linspace(0.0, 6.0, 7),
        k_grid_mpc=np.geomspace(1.0e-3, 5.0e-2, 6),
        ell_max=4,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=lambda eta, k: {
            "theta_0": float(np.cos(0.1 * k) * np.exp(-0.25 * (eta - 2.0) ** 2)),
            "pi_m0": float(np.sin(0.05 * k) * np.exp(-0.25 * (eta - 3.0) ** 2)),
            "pi_m_plus2": float(0.2 * np.exp(-0.5 * (eta - 3.5) ** 2)),
            "pi_m_minus2": float(-0.15 * np.exp(-0.5 * (eta - 3.5) ** 2)),
        },
    )
    assert isinstance(propagator, SourcePropagator)
    assert propagator.ready is True
    assert propagator.observer_neutral is True
    assert propagator.transfer_bundle["transfer_T"].shape == (6, 5, 3)
    assert propagator.covariance_bundle["off_diagonal_strategy"] == "m_decoupled_blocks"
    assert propagator.transfer_bundle["structure_label"] == "VII_h"
    assert propagator.config.kernel_family == "class_b_helical_matrix_approx"
    assert float(propagator.transfer_bundle["rotation_strength"]) > 0.0
    assert np.linalg.norm(np.asarray(propagator.transfer_bundle["transfer_B"], dtype=np.float64)) > 0.0


def test_flrw_validation_builder_disables_mode_coupling_expectation() -> None:
    propagator = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.FLRW_VALIDATION,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            flrw_validation_only=True,
            kernel_family="flrw_scalar_validation",
        ),
        structure=get_type("I"),
        eta_grid_mpc=np.linspace(0.0, 4.0, 5),
        k_grid_mpc=np.geomspace(1.0e-3, 1.0e-2, 4),
        ell_max=3,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 2.0) ** 2)),
        source_builder=lambda eta, k: {
            "theta_0": float(np.exp(-0.25 * (eta - 2.0) ** 2)),
            "pi_m0": float(0.1 * np.cos(0.1 * k)),
        },
    )
    assert propagator.mode_coupling_expected is False


def test_type_i_exact_builder_uses_matrix_backend_and_zero_b_modes() -> None:
    propagator = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="bianchi_i_matrix_exact",
        ),
        structure=get_type("I"),
        eta_grid_mpc=np.linspace(0.0, 4.0, 5),
        k_grid_mpc=np.geomspace(1.0e-3, 1.0e-2, 4),
        ell_max=3,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 2.0) ** 2)),
        source_builder=lambda eta, k: _complete_los_source(
            theta_0=float(np.exp(-0.25 * (eta - 2.0) ** 2) * np.cos(0.1 * k)),
            pi_m0=float(0.1 * np.cos(0.1 * k)),
            pi_m_plus2=float(0.03 * np.exp(-0.25 * (eta - 2.0) ** 2)),
            pi_m_minus2=float(0.03 * np.exp(-0.25 * (eta - 2.0) ** 2)),
        ),
    )
    assert propagator.config.kernel_family == "bianchi_i_matrix_exact"
    assert propagator.transfer_bundle["structure_label"] == "I"
    assert propagator.transfer_bundle["propagator_exactness"] == "exact_type_i_matrix"
    assert propagator.transfer_bundle["source_completeness_policy"] == "explicit_required_fail_closed"
    assert propagator.transfer_bundle["temperature_source_doppler_derivative"] == (
        "fourth_order_uniform_eta_finite_difference_with_variable_grid_gradient_fallback"
    )
    assert propagator.transfer_bundle["publication_output_claim_allowed"] is True
    assert propagator.evidence["output_claim_allowed"] is True
    np.testing.assert_allclose(
        np.asarray(propagator.transfer_bundle["transfer_B"], dtype=np.float64),
        0.0,
    )


def test_exact_matrix_transport_rejects_missing_decomposed_los_sources() -> None:
    with pytest.raises(ValueError, match="missing decomposed LOS source ingredient"):
        build_source_propagator(
            SourcePropagatorConfig(
                mode=PropagatorMode.ANISOTROPIC_FORWARD,
                temperature_transport=FeatureStatus.EXACT,
                polarization_rotation=FeatureStatus.DISABLED,
                kernel_family="bianchi_i_matrix_exact",
            ),
            structure=get_type("I"),
            eta_grid_mpc=np.linspace(0.0, 4.0, 5),
            k_grid_mpc=np.geomspace(1.0e-3, 1.0e-2, 4),
            ell_max=3,
            visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 2.0) ** 2)),
            source_builder=lambda eta, k: {
                "theta_0": float(np.exp(-0.25 * (eta - 2.0) ** 2)),
                "pi_m0": 0.1,
            },
        )


def test_exact_matrix_transport_rejects_nonfinite_decomposed_los_sources() -> None:
    with pytest.raises(ValueError, match="non-finite scalar"):
        build_source_propagator(
            SourcePropagatorConfig(
                mode=PropagatorMode.ANISOTROPIC_FORWARD,
                temperature_transport=FeatureStatus.EXACT,
                polarization_rotation=FeatureStatus.DISABLED,
                kernel_family="bianchi_i_matrix_exact",
            ),
            structure=get_type("I"),
            eta_grid_mpc=np.linspace(0.0, 4.0, 5),
            k_grid_mpc=np.geomspace(1.0e-3, 1.0e-2, 4),
            ell_max=3,
            visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 2.0) ** 2)),
            source_builder=lambda eta, k: _complete_los_source(
                theta_0=np.nan,
                pi_m0=0.1,
            ),
        )


def test_publication_ready_assertion_accepts_only_exact_type_i_path() -> None:
    config = SourcePropagatorConfig(
        mode=PropagatorMode.ANISOTROPIC_FORWARD,
        temperature_transport=FeatureStatus.EXACT,
        polarization_rotation=FeatureStatus.DISABLED,
        kernel_family="bianchi_i_matrix_exact",
    )
    evidence = assert_publication_ready_propagator(config, structure=get_type("I"))
    assert evidence.exactness == "exact_type_i_matrix"
    assert evidence.output_claim_allowed is True


def test_non_type_i_proxy_is_executable_but_not_publication_claim_ready() -> None:
    config = SourcePropagatorConfig(
        mode=PropagatorMode.ANISOTROPIC_FORWARD,
        temperature_transport=FeatureStatus.APPROXIMATE,
        polarization_rotation=FeatureStatus.APPROXIMATE,
        kernel_family="class_b_helical_matrix_approx",
    )
    evidence = propagator_evidence_for_config(config, structure=get_type("VII_h"))
    assert evidence.exactness == "algebraic_proxy_family_kernel"
    assert evidence.output_claim_allowed is False
    with pytest.raises(ValueError, match="not publication-output-ready"):
        assert_publication_ready_propagator(config, structure=get_type("VII_h"))


def test_rotated_matrix_backend_rejects_type_i() -> None:
    with pytest.raises(ValueError, match="reserved for non-Type-I"):
        build_source_propagator(
            SourcePropagatorConfig(
                mode=PropagatorMode.ANISOTROPIC_FORWARD,
                temperature_transport=FeatureStatus.APPROXIMATE,
                polarization_rotation=FeatureStatus.APPROXIMATE,
                kernel_family="class_b_twist_axis_matrix_approx",
            ),
            structure=get_type("I"),
            eta_grid_mpc=np.linspace(0.0, 4.0, 5),
            k_grid_mpc=np.geomspace(1.0e-3, 1.0e-2, 4),
            ell_max=3,
            visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 2.0) ** 2)),
            source_builder=lambda eta, k: {
                "theta_0": float(np.exp(-0.25 * (eta - 2.0) ** 2) * np.cos(0.1 * k)),
                "pi_m0": float(0.1 * np.cos(0.1 * k)),
            },
        )


@pytest.mark.parametrize(
    ("bianchi_type", "kernel_family"),
    [
        ("V", "type_v_open_hyperbolic_projection"),
        ("III", "type_iii_hyperbolic_projection"),
        ("IV", "type_iv_solvable_projection"),
        ("VI_h", "type_vih_negative_h_projection"),
        ("VII_0", "type_vii0_helical_projection"),
        ("VIII", "type_viii_sl2r_noncompact_projection"),
        ("IX", "type_ix_compact_su2_projection"),
    ],
)
def test_algebra_aware_non_type_i_families_build_live_propagators(
    bianchi_type: str,
    kernel_family: str,
) -> None:
    propagator = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.APPROXIMATE,
            polarization_rotation=FeatureStatus.APPROXIMATE,
            kernel_family=kernel_family,
        ),
        structure=get_type(bianchi_type),
        eta_grid_mpc=np.linspace(0.0, 5.0, 6),
        k_grid_mpc=np.geomspace(1.0e-3, 1.0e-2, 4),
        ell_max=3,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 2.0) ** 2)),
        source_builder=lambda eta, k: {
            "theta_0": float(np.exp(-0.25 * (eta - 2.0) ** 2) * np.cos(0.1 * k)),
            "pi_m0": float(0.1 * np.cos(0.1 * k)),
            "pi_m_plus2": float(0.03 * np.exp(-0.25 * (eta - 2.0) ** 2)),
            "pi_m_minus2": float(-0.02 * np.exp(-0.25 * (eta - 2.0) ** 2)),
        },
    )
    assert propagator.ready is True
    assert propagator.transfer_bundle["structure_label"] == bianchi_type
    assert propagator.config.kernel_family == kernel_family
    assert propagator.transfer_bundle["propagator_exactness"] == (
        "algebraic_proxy_family_kernel"
    )
    assert propagator.transfer_bundle["publication_output_claim_allowed"] is False


def test_type_v_matrix_path_applies_open_hyperbolic_envelope() -> None:
    eta_grid = np.linspace(0.0, 6.0, 9)
    k_grid = np.geomspace(2.0e-2, 5.0e-2, 4)

    def source(eta: float, k: float) -> dict[str, float]:
        env = float(np.exp(-0.5 * (eta - 3.0) ** 2))
        return _complete_los_source(
            theta_0=env * float(np.cos(0.1 * k)),
            pi_m0=0.1 * env,
        )

    type_v = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="type_v_open_hyperbolic_projection",
        ),
        structure=get_type("V", a_twist=1.0e-2),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )
    type_i = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="bianchi_i_matrix_exact",
        ),
        structure=get_type("I"),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )

    bundle = type_v.transfer_bundle
    assert bundle["propagator_exactness"] == "type_v_open_hyperbolic_projection_transport"
    assert bundle["publication_output_claim_allowed"] is True
    assert type_v.evidence["output_claim_allowed"] is True
    assert bundle["typev_transport_status"] == "type_v_open_hyperbolic_projection"
    assert bundle["typev_chart_metadata"] == "open_chart"
    assert bundle["polarization_basis_transport"] == "open_hyperbolic_parallel_transport"
    assert float(bundle["typev_curvature_scale"]) == pytest.approx(1.0e-2)
    assert 0.0 < float(bundle["typev_open_envelope_min"]) <= 1.0
    assert 0.0 < float(bundle["typev_open_envelope_max"]) <= 1.0
    assert float(bundle["typev_open_anchor_deviation_max"]) > 0.0
    assert float(bundle["typev_mode_mixing_norm"]) == pytest.approx(0.0)
    np.testing.assert_allclose(
        np.asarray(bundle["mode_coupling_matrix"], dtype=np.float64),
        np.eye(3),
        rtol=1.0e-12,
        atol=1.0e-12,
    )
    envelope = 1.0 / np.sqrt(1.0 + (1.0e-2 / k_grid) ** 2)
    np.testing.assert_allclose(
        np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        np.asarray(type_i.transfer_bundle["raw_transfer_T"], dtype=np.float64)[..., 0]
        * envelope[:, None],
        rtol=1.0e-12,
        atol=1.0e-12,
    )
    np.testing.assert_allclose(
        np.asarray(bundle["transfer_T"], dtype=np.float64),
        np.asarray(bundle["raw_transfer_T"], dtype=np.float64),
        rtol=1.0e-12,
        atol=1.0e-12,
    )
    np.testing.assert_allclose(
        np.asarray(bundle["transfer_E"], dtype=np.float64),
        np.asarray(bundle["raw_transfer_E"], dtype=np.float64),
        rtol=1.0e-12,
        atol=1.0e-12,
    )
    np.testing.assert_allclose(
        np.asarray(bundle["transfer_B"], dtype=np.float64),
        0.0,
        rtol=1.0e-12,
        atol=1.0e-12,
    )


def test_type_iii_matrix_path_applies_hyperbolic_branch_transport() -> None:
    eta_grid = np.linspace(0.0, 6.0, 9)
    k_grid = np.geomspace(2.0e-2, 5.0e-2, 4)

    def source(eta: float, k: float) -> dict[str, float]:
        env = float(np.exp(-0.5 * (eta - 3.0) ** 2))
        return _complete_los_source(
            theta_0=env * float(np.cos(0.1 * k)),
            pi_m0=0.1 * env,
        )

    type_iii = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.EXACT,
            kernel_family="type_iii_hyperbolic_projection",
        ),
        structure=get_type("III", n1=1.0e-2, a_twist=1.0e-2),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )
    type_i = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="bianchi_i_matrix_exact",
        ),
        structure=get_type("I"),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )

    bundle = type_iii.transfer_bundle
    assert bundle["propagator_exactness"] == "type_iii_hyperbolic_projection_transport"
    assert bundle["publication_output_claim_allowed"] is True
    assert type_iii.evidence["output_claim_allowed"] is True
    assert bundle["typeiii_transport_status"] == "type_iii_hyperbolic_projection"
    assert bundle["typeiii_branch_flag"] == "VI_-1_special"
    assert float(bundle["typeiii_h_parameter"]) == pytest.approx(-1.0)
    assert float(bundle["typeiii_hyperbolic_scale"]) == pytest.approx(2.0e-2)
    assert float(bundle["typeiii_twist_scale"]) == pytest.approx(1.0e-2)
    assert 0.0 < float(bundle["typeiii_open_attenuation_min"]) < 1.0
    assert bundle["polarization_basis_transport"] == "spin2_hyperbolic_branch_rotation"
    assert float(bundle["typeiii_mode_mixing_norm"]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 1:]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["transfer_B"], dtype=np.float64)[..., 1:]) > 0.0
    np.testing.assert_allclose(
        np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        np.asarray(type_i.transfer_bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        rtol=1.0e-12,
        atol=1.0e-12,
    )


def test_type_iv_matrix_path_applies_solvable_edge_transport() -> None:
    eta_grid = np.linspace(0.0, 6.0, 9)
    k_grid = np.geomspace(2.0e-2, 5.0e-2, 4)

    def source(eta: float, k: float) -> dict[str, float]:
        env = float(np.exp(-0.5 * (eta - 3.0) ** 2))
        return _complete_los_source(
            theta_0=env * float(np.cos(0.1 * k)),
            pi_m0=0.1 * env,
        )

    type_iv = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.EXACT,
            kernel_family="type_iv_solvable_projection",
        ),
        structure=get_type("IV", n3=2.0e-2, a_twist=1.0e-2),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )
    type_i = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="bianchi_i_matrix_exact",
        ),
        structure=get_type("I"),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )

    bundle = type_iv.transfer_bundle
    assert bundle["propagator_exactness"] == "type_iv_solvable_projection_transport"
    assert bundle["publication_output_claim_allowed"] is True
    assert type_iv.evidence["output_claim_allowed"] is True
    assert bundle["typeiv_transport_status"] == "type_iv_solvable_projection"
    assert bundle["typeiv_coordinate_order"] == "n3_dominated_then_a_twist"
    assert float(bundle["typeiv_structure_scale"]) == pytest.approx(3.0e-2)
    assert float(bundle["typeiv_n3_scale"]) == pytest.approx(2.0e-2)
    assert float(bundle["typeiv_twist_scale"]) == pytest.approx(1.0e-2)
    assert float(bundle["typeiv_privileged_weight"]) == pytest.approx(2.0 / 3.0)
    assert 0.0 < float(bundle["typeiv_edge_attenuation_min"]) < 1.0
    assert bundle["polarization_basis_transport"] == "spin2_solvable_edge_rotation"
    assert float(bundle["typeiv_mode_mixing_norm"]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 1:]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["transfer_B"], dtype=np.float64)[..., 1:]) > 0.0
    np.testing.assert_allclose(
        np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        np.asarray(type_i.transfer_bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        rtol=1.0e-12,
        atol=1.0e-12,
    )


def test_type_vii0_matrix_path_applies_helical_spin2_transport() -> None:
    eta_grid = np.linspace(0.0, 6.0, 9)
    k_grid = np.geomspace(2.0e-2, 5.0e-2, 4)

    def source(eta: float, k: float) -> dict[str, float]:
        env = float(np.exp(-0.5 * (eta - 3.0) ** 2))
        return _complete_los_source(
            theta_0=env * float(np.cos(0.1 * k)),
            pi_m0=0.1 * env,
            pi_m_plus2=0.04 * env,
            pi_m_minus2=-0.03 * env,
        )

    vii0 = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.EXACT,
            kernel_family="type_vii0_helical_projection",
        ),
        structure=get_type("VII_0", n1=1.0e-2, n3=1.0e-2),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )
    type_i = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="bianchi_i_matrix_exact",
        ),
        structure=get_type("I"),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )

    bundle = vii0.transfer_bundle
    assert bundle["propagator_exactness"] == "type_vii0_helical_projection_transport"
    assert bundle["publication_output_claim_allowed"] is True
    assert vii0.evidence["output_claim_allowed"] is True
    assert bundle["helical_transport_status"] == "type_vii0_helical_projection"
    assert bundle["polarization_basis_transport"] == "spin2_helical_rotation"
    assert float(bundle["helical_pitch"]) == pytest.approx(1.0e-2)
    assert float(bundle["helicity_mode_mixing_norm"]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["transfer_B"], dtype=np.float64)[..., 1:]) > 0.0
    np.testing.assert_allclose(
        np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        np.asarray(type_i.transfer_bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        rtol=1.0e-12,
        atol=1.0e-12,
    )


def test_type_viih_matrix_path_applies_open_helical_spin2_transport() -> None:
    eta_grid = np.linspace(0.0, 6.0, 9)
    k_grid = np.geomspace(2.0e-2, 5.0e-2, 4)

    def source(eta: float, k: float) -> dict[str, float]:
        env = float(np.exp(-0.5 * (eta - 3.0) ** 2))
        return _complete_los_source(
            theta_0=env * float(np.cos(0.1 * k)),
            pi_m0=0.1 * env,
            pi_m_plus2=0.04 * env,
            pi_m_minus2=-0.03 * env,
        )

    viih = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.EXACT,
            kernel_family="type_viih_open_helical_projection",
        ),
        structure=get_type("VII_h", n1=1.0e-2, n3=1.0e-2, a_twist=1.0e-3),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )
    type_i = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="bianchi_i_matrix_exact",
        ),
        structure=get_type("I"),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )

    bundle = viih.transfer_bundle
    assert bundle["propagator_exactness"] == "type_viih_open_helical_projection_transport"
    assert bundle["publication_output_claim_allowed"] is True
    assert viih.evidence["output_claim_allowed"] is True
    assert bundle["viih_transport_status"] == "type_viih_open_helical_projection"
    assert bundle["polarization_basis_transport"] == "spin2_open_helical_rotation"
    assert float(bundle["viih_h_parameter"]) == pytest.approx(1.0e-2)
    assert float(bundle["viih_helical_pitch"]) == pytest.approx(1.1e-2)
    assert 0.0 < float(bundle["viih_open_attenuation_min"]) < 1.0
    assert float(bundle["viih_mode_mixing_norm"]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["transfer_B"], dtype=np.float64)[..., 1:]) > 0.0
    np.testing.assert_allclose(
        np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        np.asarray(type_i.transfer_bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        rtol=1.0e-12,
        atol=1.0e-12,
    )


def test_type_ii_matrix_path_applies_nilpotent_scalar_to_tensor_transport() -> None:
    eta_grid = np.linspace(0.0, 6.0, 9)
    k_grid = np.geomspace(2.0e-2, 5.0e-2, 4)

    def source(eta: float, k: float) -> dict[str, float]:
        env = float(np.exp(-0.5 * (eta - 3.0) ** 2))
        return _complete_los_source(
            theta_0=env * float(np.cos(0.1 * k)),
            pi_m0=0.1 * env,
        )

    type_ii = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.EXACT,
            kernel_family="type_ii_nilpotent_projection",
        ),
        structure=get_type("II", n1=1.0e-2),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )
    type_i = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="bianchi_i_matrix_exact",
        ),
        structure=get_type("I"),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )

    bundle = type_ii.transfer_bundle
    assert bundle["propagator_exactness"] == "type_ii_nilpotent_projection_transport"
    assert bundle["publication_output_claim_allowed"] is True
    assert type_ii.evidence["output_claim_allowed"] is True
    assert bundle["nil_transport_status"] == "type_ii_nilpotent_projection"
    assert bundle["polarization_basis_transport"] == "spin2_nil_shear_rotation"
    assert float(bundle["nil_structure_scale"]) == pytest.approx(1.0e-2)
    assert float(bundle["nil_mode_mixing_norm"]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 1:]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["transfer_B"], dtype=np.float64)[..., 1:]) > 0.0
    np.testing.assert_allclose(
        np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        np.asarray(type_i.transfer_bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        rtol=1.0e-12,
        atol=1.0e-12,
    )


def test_type_vi0_matrix_path_applies_directional_even_tensor_transport() -> None:
    eta_grid = np.linspace(0.0, 6.0, 9)
    k_grid = np.geomspace(2.0e-2, 5.0e-2, 4)

    def source(eta: float, k: float) -> dict[str, float]:
        env = float(np.exp(-0.5 * (eta - 3.0) ** 2))
        return _complete_los_source(
            theta_0=env * float(np.cos(0.1 * k)),
            pi_m0=0.1 * env,
        )

    vi0 = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.EXACT,
            kernel_family="type_vi0_directional_projection",
        ),
        structure=get_type("VI_0", n1=2.0e-2, n3=-1.0e-2),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )
    type_i = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="bianchi_i_matrix_exact",
        ),
        structure=get_type("I"),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )

    bundle = vi0.transfer_bundle
    assert bundle["propagator_exactness"] == "type_vi0_directional_projection_transport"
    assert bundle["publication_output_claim_allowed"] is True
    assert vi0.evidence["output_claim_allowed"] is True
    assert bundle["vi0_transport_status"] == "type_vi0_directional_projection"
    assert bundle["polarization_basis_transport"] == "parity_even_directional_transport"
    assert float(bundle["vi0_structure_scale"]) == pytest.approx(3.0e-2)
    assert float(bundle["vi0_directional_imbalance"]) == pytest.approx(1.0 / 3.0)
    assert float(bundle["vi0_mode_mixing_norm"]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 1:]) > 0.0
    np.testing.assert_allclose(
        np.asarray(bundle["raw_transfer_B"], dtype=np.float64),
        0.0,
        atol=1.0e-15,
    )
    np.testing.assert_allclose(
        np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        np.asarray(type_i.transfer_bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        rtol=1.0e-12,
        atol=1.0e-12,
    )


def test_type_vih_matrix_path_applies_negative_h_branch_transport() -> None:
    eta_grid = np.linspace(0.0, 6.0, 9)
    k_grid = np.geomspace(2.0e-2, 5.0e-2, 4)

    def source(eta: float, k: float) -> dict[str, float]:
        env = float(np.exp(-0.5 * (eta - 3.0) ** 2))
        return _complete_los_source(
            theta_0=env * float(np.cos(0.1 * k)),
            pi_m0=0.1 * env,
        )

    vih = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.EXACT,
            kernel_family="type_vih_negative_h_projection",
        ),
        structure=get_type("VI_h", n1=2.0e-2, n3=-5.0e-3, a_twist=5.0e-3),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )
    type_i = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="bianchi_i_matrix_exact",
        ),
        structure=get_type("I"),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )

    bundle = vih.transfer_bundle
    assert bundle["propagator_exactness"] == "type_vih_negative_h_projection_transport"
    assert bundle["publication_output_claim_allowed"] is True
    assert vih.evidence["output_claim_allowed"] is True
    assert bundle["vih_transport_status"] == "type_vih_negative_h_projection"
    assert bundle["vih_branch_flag"] == "negative_h_branch"
    assert bundle["polarization_basis_transport"] == "spin2_negative_h_branch_rotation"
    assert float(bundle["vih_h_parameter"]) == pytest.approx(-0.25)
    assert float(bundle["vih_structure_scale"]) == pytest.approx(3.5e-2)
    assert float(bundle["vih_twist_scale"]) == pytest.approx(5.0e-3)
    assert float(bundle["vih_h_twist_scale"]) == pytest.approx(0.8)
    assert float(bundle["vih_directional_imbalance"]) == pytest.approx(0.6)
    assert 0.0 < float(bundle["vih_open_attenuation_min"]) < 1.0
    assert float(bundle["vih_mode_mixing_norm"]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 1:]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["transfer_B"], dtype=np.float64)[..., 1:]) > 0.0
    np.testing.assert_allclose(
        np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        np.asarray(type_i.transfer_bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        rtol=1.0e-12,
        atol=1.0e-12,
    )


def test_type_viii_matrix_path_applies_sl2r_noncompact_transport() -> None:
    eta_grid = np.linspace(0.0, 6.0, 9)
    k_grid = np.geomspace(2.0e-2, 5.0e-2, 4)

    def source(eta: float, k: float) -> dict[str, float]:
        env = float(np.exp(-0.5 * (eta - 3.0) ** 2))
        return _complete_los_source(
            theta_0=env * float(np.cos(0.1 * k)),
            pi_m0=0.1 * env,
        )

    viii = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.EXACT,
            kernel_family="type_viii_sl2r_noncompact_projection",
        ),
        structure=get_type("VIII", n1=-1.0e-2, n2=1.0e-2, n3=2.0e-2),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )
    type_i = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="bianchi_i_matrix_exact",
        ),
        structure=get_type("I"),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )

    bundle = viii.transfer_bundle
    assert bundle["propagator_exactness"] == "type_viii_sl2r_noncompact_projection_transport"
    assert bundle["publication_output_claim_allowed"] is True
    assert viii.evidence["output_claim_allowed"] is True
    assert bundle["typeviii_transport_status"] == "type_viii_sl2r_noncompact_projection"
    assert bundle["typeviii_branch_flag"] == "noncompact_branch"
    assert bundle["polarization_basis_transport"] == "spin2_sl2r_noncompact_rotation"
    assert float(bundle["typeviii_structure_scale"]) == pytest.approx(4.0e-2)
    assert float(bundle["typeviii_negative_axis_weight"]) == pytest.approx(0.25)
    assert float(bundle["typeviii_positive_axis_split"]) == pytest.approx(1.0 / 3.0)
    assert float(bundle["typeviii_disc_radius_x_eq_tanh_xi"]) == pytest.approx(np.tanh(1.5))
    assert 0.0 < float(bundle["typeviii_noncompact_attenuation_min"]) < 1.0
    assert tuple(bundle["typeviii_series_tags"]) == (
        "trivial",
        "discrete_positive",
        "discrete_negative",
    )
    assert bundle["typeviii_continuous_series_tag"] == "continuous_principal"
    assert float(bundle["typeviii_mode_mixing_norm"]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 1:]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["transfer_B"], dtype=np.float64)[..., 1:]) > 0.0
    np.testing.assert_allclose(
        np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        np.asarray(type_i.transfer_bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        rtol=1.0e-12,
        atol=1.0e-12,
    )


def test_type_ix_matrix_path_applies_compact_su2_transport() -> None:
    eta_grid = np.linspace(0.0, 6.0, 9)
    k_grid = np.geomspace(2.0e-2, 5.0e-2, 4)

    def source(eta: float, k: float) -> dict[str, float]:
        env = float(np.exp(-0.5 * (eta - 3.0) ** 2))
        return _complete_los_source(
            theta_0=env * float(np.cos(0.1 * k)),
            pi_m0=0.1 * env,
            pi_m_plus2=0.04 * env,
            pi_m_minus2=-0.03 * env,
        )

    ix = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.EXACT,
            kernel_family="type_ix_compact_su2_projection",
        ),
        structure=get_type("IX", n=1.0e-2),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )
    type_i = build_source_propagator(
        SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            kernel_family="bianchi_i_matrix_exact",
        ),
        structure=get_type("I"),
        eta_grid_mpc=eta_grid,
        k_grid_mpc=k_grid,
        ell_max=5,
        visibility_fn=lambda eta: float(np.exp(-0.5 * (eta - 3.0) ** 2)),
        source_builder=source,
    )

    bundle = ix.transfer_bundle
    assert bundle["propagator_exactness"] == "type_ix_compact_su2_projection_transport"
    assert bundle["publication_output_claim_allowed"] is True
    assert ix.evidence["output_claim_allowed"] is True
    assert bundle["typeix_transport_status"] == "type_ix_compact_su2_projection"
    assert bundle["typeix_branch_flag"] == "compact_su2_branch"
    assert bundle["polarization_basis_transport"] == "spin2_compact_su2_rotation"
    assert float(bundle["typeix_curvature_scale"]) == pytest.approx(1.0e-2)
    assert float(bundle["typeix_positive_axis_anisotropy_split"]) == pytest.approx(0.0)
    assert int(bundle["typeix_discrete_j"]) == 2
    assert int(bundle["typeix_spectral_eigenvalue_jj1"]) == 6
    assert float(bundle["typeix_invariant_volume"]) == pytest.approx(8.0 * np.pi ** 2)
    assert float(bundle["typeix_wigner_d_j2_unit_amplitude"]) == pytest.approx(
        np.sqrt(5.0 / (8.0 * np.pi ** 2))
    )
    assert float(bundle["typeix_compact_phase_max"]) > 0.0
    assert float(bundle["typeix_spectral_envelope_min"]) == pytest.approx(1.0)
    assert float(bundle["typeix_spectral_envelope_max"]) == pytest.approx(1.0)
    assert float(bundle["typeix_mode_mixing_norm"]) > 0.0
    assert np.linalg.norm(np.asarray(bundle["transfer_B"], dtype=np.float64)[..., 1:]) > 0.0
    np.testing.assert_allclose(
        np.asarray(bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        np.asarray(type_i.transfer_bundle["raw_transfer_T"], dtype=np.float64)[..., 0],
        rtol=1.0e-12,
        atol=1.0e-12,
    )
