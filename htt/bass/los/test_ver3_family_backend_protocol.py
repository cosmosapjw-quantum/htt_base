from __future__ import annotations

import numpy as np
import pytest

from bass.background import get_family_spec
from bass.hierarchy import (
    build_hierarchy_layout,
    build_reduced_joint_affine_operator,
    evaluate_reduced_harmonic_rhs,
    evaluate_reduced_local_rhs,
)
from bass.los import (
    NativeLabelCard,
    SeedRequest,
    build_backend,
    family_backend_gate_bundle,
)


ALL_FAMILIES = ["FLRW", "I", "II", "III", "IV", "V", "VI_0", "VI_h", "VII_0", "VII_h", "VIII", "IX"]


@pytest.mark.parametrize("family", ALL_FAMILIES)
def test_all_families_build_backend_contract(family: str) -> None:
    backend = build_backend(
        get_family_spec(family),
        truncation={"ell_max": 6, "k_max": 0.2},
    )
    metadata = backend.required_metadata()
    assert metadata["release_status"] == "backend-contract-complete"
    assert metadata["preferred_backend"] == get_family_spec(family).preferred_backend
    assert metadata["orthogonal_global_tilt_local_boost_split"] == "frozen"


def test_vi_h_label_translator_roundtrip_preserves_h_and_branch() -> None:
    backend = build_backend(
        get_family_spec("VI_h", h=-2.0),
        truncation={"ell_max": 4},
    )
    native = (
        NativeLabelCard(
            family="VI_h",
            native_label="mu_VIh_0",
            ell=2,
            m=1,
            sector="temperature",
            branch_flag="negative_h_branch",
            h_parameter=-2.0,
        ),
    )
    storage = backend.label_translator(native)
    assert storage[0]["h_parameter"] == pytest.approx(-2.0)
    assert storage[0]["branch_flag"] == "negative_h_branch"
    restored = backend.inverse_label_translator(storage)
    assert restored[0].h_parameter == pytest.approx(-2.0)
    assert restored[0].branch_flag == "negative_h_branch"
    assert restored[0].chart == "class_b_negative_h_chart"


def test_iv_label_translator_roundtrip_preserves_coordinate_order() -> None:
    backend = build_backend(
        get_family_spec("IV"),
        truncation={"ell_max": 4},
    )
    native = (
        NativeLabelCard(
            family="IV",
            native_label="mu_solv_0",
            ell=1,
            m=0,
            sector="temperature",
            coordinate_order=("x_noncompact", "y_shear", "z_twist"),
        ),
    )
    storage = backend.label_translator(native)
    assert storage[0]["coordinate_order"] == ("x_noncompact", "y_shear", "z_twist")
    restored = backend.inverse_label_translator(storage)
    assert restored[0].coordinate_order == ("x_noncompact", "y_shear", "z_twist")
    assert restored[0].branch_flag == "intrinsic"
    assert restored[0].chart == "solvable_group_chart"


def test_vi0_label_translator_roundtrip_preserves_directional_tag() -> None:
    backend = build_backend(get_family_spec("VI_0"), truncation={"ell_max": 4})
    native = (
        NativeLabelCard(
            family="VI_0",
            native_label="mu_VI0_0",
            ell=2,
            m=0,
            sector="temperature",
            directional_tag="mixed_sign_axes",
        ),
    )
    storage = backend.label_translator(native)
    assert storage[0]["directional_tag"] == "mixed_sign_axes"
    restored = backend.inverse_label_translator(storage)
    assert restored[0].directional_tag == "mixed_sign_axes"
    assert restored[0].branch_flag == "intrinsic"
    assert restored[0].chart == "class_a_solvable_intrinsic"


def test_intrinsic_family_seed_factory_rejects_flrw_like_regular() -> None:
    backend = build_backend(get_family_spec("II"), truncation={"ell_max": 4})
    with pytest.raises(ValueError, match="not allowed"):
        backend.seed_factory(
            SeedRequest(branch="intrinsic", seed_mode="flrw_like_regular")
        )


def test_isotropic_anchor_seed_factory_allows_regular_seed() -> None:
    backend = build_backend(get_family_spec("VII_0"), truncation={"ell_max": 4})
    seed = backend.seed_factory(
        SeedRequest(branch="orthogonal", seed_mode="flrw_like_regular", amplitude_reference=2.5)
    )
    assert seed.family == "VII_0"
    assert seed.seed_mode == "flrw_like_regular"
    assert seed.normalization["amp_ref"] == "disc_L2_unit"
    assert seed.normalization["amplitude_reference_value"] == pytest.approx(2.5)
    assert seed.normalization["mu_ref"] == "native_cross_section_label"
    assert seed.normalization["release_convention"] == "frozen_discrete_weighted_L2"


def test_operator_factory_maps_named_family_to_expected_kernel() -> None:
    backend = build_backend(get_family_spec("IX"), truncation={"ell_max": 6})
    ops = backend.operator_factory({"branch": "orthogonal", "state_tag": "named_branch"})
    assert ops.operator_kernel_family == "class_a_compact_matrix_approx"
    assert ops.backend_name == "wigner_d_compact_backend"
    assert ops.release_status == "backend-operator-bound"
    assert ops.metadata["contract_release_status"] == "backend-contract-complete"
    assert ops.mass_matrix.shape == ops.A_fs.shape
    assert ops.A_fs.shape == ops.A_mix.shape == ops.A_coll.shape
    assert ops.source_template.shape == (ops.mass_matrix.shape[0],)
    assert ops.layout_metadata["family"] == "IX"
    assert ops.layout_metadata["branch"] == "orthogonal"
    assert ops.metadata["reduced_local_evaluator_available"] is True
    assert ops.metadata["reduced_harmonic_evaluator_available"] is True
    assert ops.metadata["reduced_joint_evaluator_available"] is True
    assert ops.metadata["family_conditioned_kernel_status"] == "frozen_v5_family_conditioned"
    assert ops.layout_metadata["family_conditioned_kernel_status"] == "frozen_v5_family_conditioned"
    assert ops.metadata["family_conditioned_kernel_law"] == "ix_compact_wigner_frozen_v5"


def test_operator_factory_can_return_geometry_ops_with_mode_ops() -> None:
    backend = build_backend(get_family_spec("I"), truncation={"ell_max": 4})
    geometry_ops, mode_ops = backend.operator_factory(
        {"branch": "tilted", "include_geometry": True}
    )
    assert geometry_ops.family == "I"
    assert geometry_ops.branch == "tilted"
    assert geometry_ops.Gamma.shape == (3, 3, 3)
    assert mode_ops.branch == "tilted"


def test_backend_residuals_reports_roundtrip_zero_when_translator_is_consistent() -> None:
    backend = build_backend(get_family_spec("VIII"), truncation={"ell_max": 4})
    native = (
        NativeLabelCard(
            family="VIII",
            native_label="mu_sl2r_0",
            ell=3,
            m=-1,
            sector="temperature",
            branch_flag="noncompact_branch",
        ),
    )
    residuals = backend.backend_residuals(native)
    assert residuals["translator_roundtrip_residual"] == 0


def test_template_card_exposes_intrinsic_family_constraints() -> None:
    backend = build_backend(get_family_spec("VI_h", h=-2.0), truncation={"ell_max": 4})
    card = backend.template_card()
    assert card.family == "VI_h"
    assert card.analytic_normalization_status == "frozen_discrete_weighted_l2_release_convention"
    assert card.lookup_resolution_status == "frozen_v5_formula_set"
    assert card.label_translator_card.h_parameter == pytest.approx(-2.0)
    assert "h_consistency" in card.family_specific_residuals
    assert "no_using_vi0_seed_at_nonzero_h" in card.must_not_do
    assert "h" in card.collocation_policy.edge_metadata_fields
    assert "h_aware_local_regular" in card.allowed_seed_provenance
    resolved = card.metadata["class_b_parameter_bridge"]["resolved_value"]
    assert resolved["h"] == pytest.approx(-2.0)
    assert resolved["q"] == pytest.approx(-0.1715728752538099)
    assert card.metadata["seed_normalization_convention"]["amp_ref"] == "disc_L2_unit"
    assert card.metadata["verification_crosscheck_pass"] is True
    assert (
        card.metadata["verification_reference"]
        == "docs/bianchi_design_pack_v5/verification/crosscheck_results.json"
    )


def test_required_metadata_embeds_template_card_payload() -> None:
    backend = build_backend(get_family_spec("IV"), truncation={"ell_max": 3})
    metadata = backend.required_metadata()
    template_card = metadata["template_card"]
    assert template_card["family"] == "IV"
    assert template_card["label_translator_card"]["coordinate_order"] == [
        "x_noncompact",
        "y_shear",
        "z_twist",
    ]
    assert template_card["analytic_normalization_status"] == "frozen_discrete_weighted_l2_release_convention"
    assert template_card["lookup_resolution_status"] == "frozen_v5_formula_set"
    assert template_card["metadata"]["verification_crosscheck_pass"] is True
    assert metadata["seed_normalization_convention"]["norm_rule"] == "<phi,phi>_h = 1"
    assert metadata["verification_crosscheck_pass"] is True


def test_type_viii_template_card_carries_frozen_plancherel_conventions() -> None:
    backend = build_backend(get_family_spec("VIII"), truncation={"ell_max": 4})
    template = backend.template_card()
    lookup = template.metadata["type_viii_lookup"]
    assert template.lookup_resolution_status == "frozen_v5_formula_set"
    assert lookup["principal_series_labels"] == "(mu,s), -1/2 <= mu < 1/2, s>=0"
    assert "sinh(2*pi*s)" in lookup["principal_series_measure"]
    assert lookup["mu0_reduction"] == "(2*pi)^(-2) * s*tanh(pi*s)"


def test_intrinsic_seed_factory_records_frozen_normalization_and_lookup_metadata() -> None:
    backend = build_backend(get_family_spec("II"), truncation={"ell_max": 4})
    seed = backend.seed_factory(
        SeedRequest(branch="intrinsic", seed_mode="frobenius", amplitude_reference=3.0)
    )
    assert seed.normalization["amp_ref"] == "disc_L2_unit"
    assert seed.normalization["amplitude_reference_value"] == pytest.approx(3.0)
    assert seed.normalization["inner_product"] == "<phi,psi>_h = sum_q w_q phi_q^* psi_q"
    assert seed.metadata["lookup_resolution_status"] == "frozen_v5_formula_set"
    assert seed.metadata["verification_crosscheck_pass"] is True
    assert seed.metadata["resolved_lookup"]["frozen_backend_constants"]["rho"] == "Abs(k)"


def test_backend_reduced_local_rhs_matches_layout_evaluator() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")},
    )
    layout = build_hierarchy_layout(backend, backend.truncation)
    bg = {
        "branch": "tilted",
        "opacity_data": {"Gamma_T": 2.5},
        "sigma_tensor": np.diag([0.2, -0.1, -0.1]),
    }
    baryon_by_mode_label = {
        "m0": np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64),
        "m+2": np.array([0.5, 0.6, 0.7, 0.8], dtype=np.float64),
        "m-2": np.array([-0.3, -0.2, -0.1, 0.0], dtype=np.float64),
    }
    cdm_by_mode_label = {
        "m0": np.array([0.9, 1.0], dtype=np.float64),
        "m+2": np.array([1.1, 1.2], dtype=np.float64),
        "m-2": np.array([-0.4, 0.2], dtype=np.float64),
    }
    theta_1_by_mode_label = {"m0": 0.15, "m+2": -0.25, "m-2": 0.35}
    reduced_direct = evaluate_reduced_local_rhs(
        layout,
        bg,
        backend,
        baryon_by_mode_label=baryon_by_mode_label,
        cdm_by_mode_label=cdm_by_mode_label,
        theta_1_by_mode_label=theta_1_by_mode_label,
    )
    reduced_backend = backend.evaluate_reduced_local_rhs(
        bg,
        baryon_by_mode_label=baryon_by_mode_label,
        cdm_by_mode_label=cdm_by_mode_label,
        theta_1_by_mode_label=theta_1_by_mode_label,
    )
    for mu in layout.mode_labels:
        np.testing.assert_allclose(reduced_backend[0][str(mu)], reduced_direct[0][str(mu)])
        np.testing.assert_allclose(reduced_backend[1][str(mu)], reduced_direct[1][str(mu)])


def test_backend_reduced_harmonic_rhs_matches_layout_evaluator() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")},
    )
    layout = build_hierarchy_layout(backend, backend.truncation)
    width = (layout.ell_max + 1) ** 2
    bg = {
        "branch": "tilted",
        "opacity_data": {"Gamma_T": 2.5},
        "sigma_tensor": np.diag([0.2, -0.1, -0.1]),
        "source_tables": {
            "visibility_amplitude": 1.25,
            "polarization_source": 0.4,
            "reionization_amplitude": 0.2,
        },
    }
    photon_t_by_mode_label = {
        "m0": np.linspace(0.1, 0.9, width, dtype=np.float64),
        "m+2": np.linspace(-0.3, 0.5, width, dtype=np.float64),
        "m-2": np.linspace(0.2, -0.4, width, dtype=np.float64),
    }
    photon_e_by_mode_label = {
        "m0": np.linspace(0.6, -0.2, width, dtype=np.float64),
        "m+2": np.linspace(0.3, 0.9, width, dtype=np.float64),
        "m-2": np.linspace(-0.5, 0.1, width, dtype=np.float64),
    }
    photon_b_by_mode_label = {
        "m0": np.linspace(-0.4, 0.4, width, dtype=np.float64),
        "m+2": np.linspace(0.7, -0.1, width, dtype=np.float64),
        "m-2": np.linspace(0.05, 0.25, width, dtype=np.float64),
    }
    neutrino_by_mode_label = {
        "m0": np.linspace(0.15, 0.75, width, dtype=np.float64),
        "m+2": np.linspace(-0.2, 0.6, width, dtype=np.float64),
        "m-2": np.linspace(0.4, -0.1, width, dtype=np.float64),
    }
    baryon_by_mode_label = {
        "m0": np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64),
        "m+2": np.array([0.5, 0.6, 0.7, 0.8], dtype=np.float64),
        "m-2": np.array([-0.3, -0.2, -0.1, 0.0], dtype=np.float64),
    }
    source_by_mode_label = {
        "m0": np.array([0.2, -0.1, 0.0], dtype=np.float64),
        "m+2": np.array([0.3, 0.4, -0.2], dtype=np.float64),
        "m-2": np.array([-0.25, 0.15, 0.05], dtype=np.float64),
    }
    reduced_direct = evaluate_reduced_harmonic_rhs(
        layout,
        bg,
        backend,
        photon_T_by_mode_label=photon_t_by_mode_label,
        photon_E_by_mode_label=photon_e_by_mode_label,
        photon_B_by_mode_label=photon_b_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=baryon_by_mode_label,
        source_by_mode_label=source_by_mode_label,
    )
    reduced_backend = backend.evaluate_reduced_harmonic_rhs(
        bg,
        photon_T_by_mode_label=photon_t_by_mode_label,
        photon_E_by_mode_label=photon_e_by_mode_label,
        photon_B_by_mode_label=photon_b_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=baryon_by_mode_label,
        source_by_mode_label=source_by_mode_label,
    )
    for sector_direct, sector_backend in zip(reduced_direct, reduced_backend, strict=True):
        for mu in layout.mode_labels:
            np.testing.assert_allclose(sector_backend[str(mu)], sector_direct[str(mu)])


def test_backend_reduced_joint_affine_operator_matches_layout_builder() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")},
    )
    layout = build_hierarchy_layout(backend, backend.truncation)
    width = (layout.ell_max + 1) ** 2
    bg = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 2.5},
        "sigma_tensor": np.diag([0.2, -0.1, -0.1]),
        "source_tables": {
            "visibility_amplitude": 1.25,
            "polarization_source": 0.4,
            "reionization_amplitude": 0.2,
        },
    }
    photon_t_by_mode_label = {
        "m0": np.linspace(0.1, 0.9, width, dtype=np.float64),
        "m+2": np.linspace(-0.3, 0.5, width, dtype=np.float64),
        "m-2": np.linspace(0.2, -0.4, width, dtype=np.float64),
    }
    photon_e_by_mode_label = {
        "m0": np.linspace(0.6, -0.2, width, dtype=np.float64),
        "m+2": np.linspace(0.3, 0.9, width, dtype=np.float64),
        "m-2": np.linspace(-0.5, 0.1, width, dtype=np.float64),
    }
    photon_b_by_mode_label = {
        "m0": np.linspace(-0.4, 0.4, width, dtype=np.float64),
        "m+2": np.linspace(0.7, -0.1, width, dtype=np.float64),
        "m-2": np.linspace(0.05, 0.25, dtype=np.float64),
    }
    neutrino_by_mode_label = {
        "m0": np.linspace(0.15, 0.75, width, dtype=np.float64),
        "m+2": np.linspace(-0.2, 0.6, width, dtype=np.float64),
        "m-2": np.linspace(0.4, -0.1, dtype=np.float64),
    }
    baryon_by_mode_label = {
        "m0": np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64),
        "m+2": np.array([0.5, 0.6, 0.7, 0.8], dtype=np.float64),
        "m-2": np.array([-0.3, -0.2, -0.1, 0.0], dtype=np.float64),
    }
    source_by_mode_label = {
        "m0": np.array([0.2, -0.1, 0.0], dtype=np.float64),
        "m+2": np.array([0.3, 0.4, -0.2], dtype=np.float64),
        "m-2": np.array([-0.25, 0.15, 0.05], dtype=np.float64),
    }
    direct = build_reduced_joint_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=("m+2", "m-2"),
        photon_T_by_mode_label=photon_t_by_mode_label,
        photon_E_by_mode_label=photon_e_by_mode_label,
        photon_B_by_mode_label=photon_b_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=baryon_by_mode_label,
        source_by_mode_label=source_by_mode_label,
    )
    owned = backend.build_reduced_joint_affine_operator(
        bg,
        residual_mode_labels=("m+2", "m-2"),
        photon_T_by_mode_label=photon_t_by_mode_label,
        photon_E_by_mode_label=photon_e_by_mode_label,
        photon_B_by_mode_label=photon_b_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=baryon_by_mode_label,
        source_by_mode_label=source_by_mode_label,
    )
    assert owned.mode_labels == direct.mode_labels
    assert owned.local_dof == direct.local_dof
    assert owned.harmonic_dof == direct.harmonic_dof
    assert owned.source_dof == direct.source_dof
    np.testing.assert_allclose(owned.matrix.toarray(), direct.matrix.toarray())
    np.testing.assert_allclose(owned.bias, direct.bias)


def test_family_conditioned_kernel_law_varies_with_family_branch() -> None:
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")}
    backend_open = build_backend(get_family_spec("VI_h", h=-0.25), truncation=truncation)
    backend_deep = build_backend(get_family_spec("VI_h", h=-2.0), truncation=truncation)
    bg = {
        "branch": "tilted",
        "opacity_data": {"Gamma_T": 2.5},
        "sigma_tensor": np.diag([0.2, -0.1, -0.1]),
        "source_tables": {
            "visibility_amplitude": 1.0,
            "polarization_source": 0.3,
            "reionization_amplitude": 0.2,
        },
    }
    ops_open = backend_open.operator_factory(bg)
    ops_deep = backend_deep.operator_factory(bg)
    assert ops_open.metadata["family_conditioned_kernel_law"] == "vih_class_b_bridge_frozen_v5"
    assert ops_deep.metadata["family_conditioned_kernel_law"] == "vih_class_b_bridge_frozen_v5"
    assert not np.allclose(
        np.asarray(ops_open.mass_matrix.diagonal(), dtype=np.float64),
        np.asarray(ops_deep.mass_matrix.diagonal(), dtype=np.float64),
    )
    assert not np.allclose(
        np.asarray(ops_open.A_mix.toarray(), dtype=np.float64),
        np.asarray(ops_deep.A_mix.toarray(), dtype=np.float64),
    )
    assert not np.allclose(
        np.asarray(list(backend_open.evaluate_reduced_source_blocks(bg).values()), dtype=np.float64),
        np.asarray(list(backend_deep.evaluate_reduced_source_blocks(bg).values()), dtype=np.float64),
    )


def test_family_backend_gate_bundle_carries_v5_verification_authority() -> None:
    backend = build_backend(get_family_spec("VIII"), truncation={"ell_max": 4})
    ops = backend.operator_factory({"branch": "orthogonal", "opacity_data": {}, "source_tables": {}})
    gate = family_backend_gate_bundle(backend, ops)
    assert gate.known_limit_checks["verification_bundle_pass"] is True
    assert gate.residual_summary["verification_crosscheck_pass"] == pytest.approx(1.0)
    assert (
        gate.metadata["verification_reference"]
        == "docs/bianchi_design_pack_v5/verification/crosscheck_results.json"
    )
    assert gate.passed is True
