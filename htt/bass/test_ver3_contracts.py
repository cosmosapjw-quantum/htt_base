from __future__ import annotations

import numpy as np

from bass.background import (
    BackgroundConstraintResiduals,
    BackgroundState,
    GeometryDiagnostics,
    ResidualPack,
    background_interpolator,
    build_geometry,
    eta_from_t_grid,
    get_family_spec,
    sample_background_on_eta,
)
from bass.forward import OutputMetadata
from bass.hierarchy import HierarchyState
from bass.validation import GATE_LADDER, make_gate_bundle
from common.contracts import ArtifactManifest, SolverCoreOutput


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="bass.ver3.contracts",
        artifact_path="artifacts/bass/ver3_contracts",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="deadbeef",
        config_hash="cfg-hash",
        input_hashes=["seed"],
        code_version="0.0-test",
        schema_version="ver3-v0",
    )


def _solver_output() -> SolverCoreOutput:
    lmax = 2
    size = (lmax + 1) ** 2
    values = np.linspace(1.0e-6, 9.0e-6, size)
    payload = {
        "representation": "ver2_native_pstf_sphere_reconstruction",
        "coefficient_representation": "ver2_native_pstf_final_slice",
        "ell_max": lmax,
        "values": values,
        "sphere_samples": np.linspace(0.1, 0.9, 15),
    }
    return SolverCoreOutput(
        alm_T=payload,
        alm_E={**payload, "values": values + 1.0e-6},
        alm_B={**payload, "values": values - 1.0e-6},
        map_T=None,
        map_Q=None,
        map_U=None,
        deterministic_template={"kind": "test"},
        anisotropic_covariance=None,
        metadata={
            "bianchi_type": "VII_h",
            "bianchi_branch": "tilted",
            "harmonic_basis": "m_explicit",
            "eb_sign_convention": "cmb",
            "multipole_cutoff": lmax,
            "tilt_enabled": True,
            "thomson_mode": "electron_frame_projected",
            "source_propagator_realization": "class_b_helical_matrix_approx",
            "local_boost_contract": "observer_side_only_not_applied_in_background_or_backend",
            "global_tilt_contract": "model_matter_frame_state",
        },
        manifest=_manifest(),
    )


def _gate_registry() -> dict[str, object]:
    return {
        gate: make_gate_bundle(
            gate,
            family="VII_h",
            branch="tilted",
            backend="class_b_helical_matrix_approx",
            truncation={"ell_max": 2},
            residual_summary={"max_residual": 1.0e-8},
            known_limit_checks={"status": "passed"},
            forbidden_shortcut_checks={"no_fake_support": True},
            metadata={"artifact": f"{gate}.json"},
        )
        for gate in GATE_LADDER[:-1]
    }


def test_eta_from_t_grid_matches_constant_scale_factor_bridge() -> None:
    eta = eta_from_t_grid([0.0, 1.0, 2.0], [1.0, 1.0, 1.0])
    np.testing.assert_allclose(eta, [0.0, 1.0, 2.0])


def test_background_interpolator_samples_proper_time_state_on_eta_grid() -> None:
    spec = get_family_spec("I")
    states = (
        BackgroundState(
            t=0.0,
            alpha=0.0,
            gamma_AB=np.eye(3),
            theta=1.0,
            sigma_AB=np.zeros((3, 3)),
            family_spec=spec,
            species_hat={"rho_hat": 1.0},
            species_tilt={"v": np.array([0.0, 0.0, 0.0])},
        ),
        BackgroundState(
            t=2.0,
            alpha=0.0,
            gamma_AB=np.eye(3),
            theta=3.0,
            sigma_AB=np.diag([1.0, -1.0, 0.0]) / np.sqrt(2.0),
            family_spec=spec,
            species_hat={"rho_hat": 3.0},
            species_tilt={"v": np.array([0.2, 0.0, 0.0])},
        ),
    )
    interp = background_interpolator([0.0, 2.0], states)
    sampled = sample_background_on_eta(interp, [1.0])[0]
    assert sampled.family_spec.family == "I"
    assert sampled.t == 1.0
    assert sampled.theta == 2.0
    assert sampled.species_hat["rho_hat"] == 2.0
    np.testing.assert_allclose(sampled.species_tilt["v"], [0.1, 0.0, 0.0])


def test_geometry_diagnostics_from_tetrad_geometry_exposes_dual_route_payload() -> None:
    geom = build_geometry(get_family_spec("V"))
    diagnostics = GeometryDiagnostics.from_tetrad_geometry(geom)
    assert diagnostics.metadata["family"] == "V"
    assert diagnostics.residuals["dual_route_status"] == "AVAILABLE"
    assert diagnostics.C_ortho.shape == (3, 3, 3)
    assert diagnostics.Gamma_ortho.shape == (3, 3, 3)


def test_build_geometry_accepts_document_signature_and_returns_contract_bundle() -> None:
    diagnostics = build_geometry(
        get_family_spec("I"),
        np.eye(3),
        3.0,
        np.zeros((3, 3)),
    )
    assert isinstance(diagnostics, GeometryDiagnostics)
    assert diagnostics.metadata["input_theta"] == 3.0


def test_residual_pack_from_covariant_objects_is_finite_and_summarizable() -> None:
    geom = build_geometry(get_family_spec("VII_0"))
    residuals = BackgroundConstraintResiduals(
        gauss=1.0e-8,
        codazzi=np.array([1.0e-8, 0.0, 0.0]),
        jacobi=np.zeros(3),
        twice_contracted_bianchi=np.zeros(4),
    )
    pack = ResidualPack.from_covariant_objects(
        residuals,
        geom,
        electric_weyl=np.zeros((3, 3)),
        magnetic_weyl=np.zeros((3, 3)),
        collision_isotropy=0.0,
        inverse_boost=0.0,
        notes=("covariant_pack",),
    )
    assert pack.all_finite is True
    assert pack.notes == ("covariant_pack",)
    assert pack.norm_summary()["codazzi_norm"] == 1.0e-8


def test_output_metadata_derives_gate_and_manifest_payloads_from_solver_output() -> None:
    metadata = OutputMetadata.from_solver_output(
        _solver_output(),
        ordering="ell_m_lexicographic",
        component_kind="deterministic",
        component_status="forward_model_component",
        boost_applied=False,
        gate_registry=_gate_registry(),
        residual_summary={"visibility_tau_reion": 0.054},
    )
    payload = metadata.as_dict()
    assert payload["family"] == "VII_h"
    assert payload["branch"] == "tilted"
    assert payload["gate_status"]["output_split_gate"] == "open"
    assert payload["manifest_claim_tier"] == "conditional"
    assert payload["residual_summary"]["visibility_tau_reion"] == 0.054


def test_hierarchy_state_freezes_document_level_block_split() -> None:
    state = HierarchyState(
        matter_block={"delta_b": 0.1},
        photon_intensity_block=np.array([1.0, 2.0]),
        photon_polarization_block={"E": np.array([0.5]), "B": np.array([0.0])},
        neutrino_block=np.array([0.2, 0.3]),
        source_history_block={"visibility": np.array([0.4])},
    )
    assert state.matter_block["delta_b"] == 0.1
    np.testing.assert_allclose(state.photon_intensity_block, [1.0, 2.0])
