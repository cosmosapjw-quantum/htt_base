from __future__ import annotations

import numpy as np
import pytest

from bass.background import get_family_spec
from bass.hierarchy import (
    SECTOR_ORDER,
    assemble_hierarchy_ops,
    assemble_free_streaming_block,
    assemble_mixing_block,
    assemble_explicit_block,
    assemble_implicit_block,
    assemble_mass_matrix,
    assemble_source_vector,
    build_hierarchy_layout,
    build_layout_manifest,
    flatten,
    project_runtime_native_state,
    unflatten,
)
from bass.los import build_backend


def _backend():
    return build_backend(get_family_spec("I"), truncation={"ell_max": 4, "mode_labels": ("m0", "m+2", "m-2")})


def test_layout_freezes_sector_order_and_mode_labels() -> None:
    layout = build_hierarchy_layout(_backend(), {"ell_max": 4, "mode_labels": ("m0", "m+2", "m-2")})
    assert layout.sector_order == SECTOR_ORDER
    assert layout.mode_labels == ("m0", "m+2", "m-2")


def test_flatten_unflatten_roundtrip_for_harmonic_slot() -> None:
    layout = build_hierarchy_layout(_backend(), {"ell_max": 4, "mode_labels": ("m0", "m+2", "m-2")})
    idx = flatten(layout, "m+2", "ph_E", 2, -1)
    assert unflatten(layout, idx) == ("m+2", "ph_E", 2, -1, None)


def test_flatten_unflatten_roundtrip_for_local_sector_slot() -> None:
    layout = build_hierarchy_layout(_backend(), {"ell_max": 4, "mode_labels": ("m0",)})
    idx = flatten(layout, "m0", "baryon", None, None, local_dof=3)
    assert unflatten(layout, idx) == ("m0", "baryon", None, None, 3)


def test_outer_to_inner_order_is_mu_then_sector_then_ell_then_m() -> None:
    layout = build_hierarchy_layout(_backend(), {"ell_max": 2, "mode_labels": ("m0", "m+2")})
    first = flatten(layout, "m0", "ph_I", 0, 0)
    second_mu = flatten(layout, "m+2", "ph_I", 0, 0)
    later_sector = flatten(layout, "m0", "nu_I", 0, 0)
    later_ell = flatten(layout, "m0", "ph_I", 1, -1)
    assert first < later_ell < later_sector < second_mu


def test_mass_matrix_is_identity_in_frozen_layout() -> None:
    backend = _backend()
    truncation = {"ell_max": 3, "mode_labels": ("m0",)}
    layout = build_hierarchy_layout(backend, truncation)
    M = assemble_mass_matrix({}, backend, truncation)
    assert M.shape == (layout.size, layout.size)
    np.testing.assert_allclose(M.diagonal(), 1.0)


def test_explicit_and_implicit_blocks_match_layout_shape_and_are_sparse() -> None:
    backend = _backend()
    truncation = {"ell_max": 3, "mode_labels": ("m0",)}
    layout = build_hierarchy_layout(backend, truncation)
    A_fs = assemble_free_streaming_block({}, backend, truncation)
    A_mix = assemble_mixing_block({}, backend, truncation)
    A_exp = assemble_explicit_block({}, backend, truncation)
    A_imp = assemble_implicit_block({}, backend, truncation, {"Gamma_T": 4.0})
    assert A_exp.shape == (layout.size, layout.size)
    assert A_imp.shape == (layout.size, layout.size)
    assert A_fs.shape == A_mix.shape == A_exp.shape
    assert A_exp.nnz > 0
    assert A_imp.nnz > 0
    np.testing.assert_allclose((A_fs + A_mix).toarray(), A_exp.toarray())


def test_source_vector_injects_visibility_and_polarization_slots() -> None:
    backend = _backend()
    truncation = {"ell_max": 3, "mode_labels": ("m0",)}
    layout = build_hierarchy_layout(backend, truncation)
    source = assemble_source_vector(
        {},
        backend,
        truncation,
        {"visibility_amplitude": 1.5, "polarization_source": 0.3, "reionization_amplitude": 0.2},
    )
    assert source.shape == (layout.size,)
    assert source[flatten(layout, "m0", "ph_I", 0, 0)] == pytest.approx(1.5)
    assert source[flatten(layout, "m0", "ph_E", 2, 0)] == pytest.approx(0.3)
    assert source[flatten(layout, "m0", "src", None, None, 0)] == pytest.approx(0.2)


def test_layout_manifest_records_backend_metadata() -> None:
    backend = _backend()
    truncation = {"ell_max": 2, "mode_labels": ("m0",)}
    layout = build_hierarchy_layout(backend, truncation)
    manifest = build_layout_manifest(layout, backend, truncation, {"branch": "tilted"})
    assert manifest["family"] == "I"
    assert manifest["branch"] == "tilted"
    assert manifest["mode_labels"] == ["m0"]
    assert manifest["boundary_policy"] == "cartesian_regular"
    assert manifest["operator_realization"] == "geometry_opacity_coupled_sparse_operator"
    assert manifest["exact_family_operator_available"] is True


def test_assemble_hierarchy_ops_binds_backend_with_source_tables() -> None:
    backend = _backend()
    truncation = {"ell_max": 2, "mode_labels": ("m0",)}
    ops = assemble_hierarchy_ops(
        {
            "branch": "tilted",
            "opacity_data": {"Gamma_T": 2.0},
            "source_tables": {"visibility_amplitude": 1.25},
        },
        backend,
        truncation,
        {"polarization_source": 0.5},
    )
    assert ops.branch == "tilted"
    assert ops.layout_metadata["branch"] == "tilted"
    assert ops.A_coll.nnz > 0
    assert ops.source_template.shape == (ops.mass_matrix.shape[0],)


def test_project_runtime_native_state_embeds_live_towers_into_canonical_layout() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2")},
    )
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2")}
    layout = build_hierarchy_layout(backend, truncation)
    ops = assemble_hierarchy_ops(
        {
            "branch": "orthogonal",
            "opacity_data": {"Gamma_T": 2.0},
            "source_tables": {"visibility_amplitude": 1.25},
        },
        backend,
        truncation,
        {"polarization_source": 0.5, "reionization_amplitude": 0.2},
    )
    size = (layout.ell_max + 1) ** 2
    src_width = int(layout.sector_local_dofs["src"])
    projection = project_runtime_native_state(
        layout=layout,
        layout_manifest=ops.layout_metadata,
        photon_T=np.arange(size, dtype=np.float64),
        photon_E=np.arange(size, dtype=np.float64) + 100.0,
        neutrino_tower=np.arange(size, dtype=np.float64) + 200.0,
        source_template=np.asarray(ops.source_template, dtype=np.float64),
        source_history_eta=np.array([0.1, 0.2], dtype=np.float64),
        source_history_samples=np.arange(2 * src_width, dtype=np.float64).reshape(2, src_width),
    )
    assert set(projection.covered_mode_labels) == {"m0", "m+2"}
    assert projection.zero_filled_mode_labels == ()
    assert projection.sector_status["ph_I"] == "live_runtime_projection"
    assert projection.sector_status["ph_B"] == "zero_filled_not_evolved"
    assert projection.sector_status["src"] == "mode_ops_source_template"
    assert projection.state_vector.shape == (layout.size,)
    assert projection.state_vector[flatten(layout, "m0", "ph_I", 2, 1)] == pytest.approx(7.0)
    assert projection.state_vector[flatten(layout, "m0", "ph_E", 2, 1)] == pytest.approx(107.0)
    assert projection.state_vector[flatten(layout, "m0", "nu_I", 2, 1)] == pytest.approx(207.0)
    assert projection.state_vector[flatten(layout, "m+2", "ph_I", 2, 1)] == pytest.approx(0.0)
    assert projection.state_vector[flatten(layout, "m0", "src", None, None, 0)] == pytest.approx(
        ops.source_template[flatten(layout, "m0", "src", None, None, 0)]
    )
    assert projection.state_vector[flatten(layout, "m+2", "src", None, None, 0)] == pytest.approx(
        ops.source_template[flatten(layout, "m+2", "src", None, None, 0)]
    )
    assert projection.metadata["source_block_nonzero"] is True
    assert projection.metadata["source_block_norm"] > 0.0
    assert projection.metadata["source_block_owner"] == "mode_ops_source_template"
    assert projection.metadata["source_history_available"] is True
    assert projection.metadata["source_history_sample_count"] == 2
    assert projection.metadata["resolved_sector_order"] == ("ph_I", "ph_E", "nu_I", "src")
    assert np.asarray(projection.hierarchy_state.source_history_block["eta"]).shape == (2,)
    assert np.asarray(projection.hierarchy_state.source_history_block["history"]).shape == (2, src_width)


def test_project_runtime_native_state_can_embed_runtime_local_matter_blocks() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2")},
    )
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2")}
    layout = build_hierarchy_layout(backend, truncation)
    ops = assemble_hierarchy_ops(
        {
            "branch": "orthogonal",
            "opacity_data": {"Gamma_T": 2.0},
            "source_tables": {"visibility_amplitude": 1.25},
        },
        backend,
        truncation,
        {"polarization_source": 0.5},
    )
    size = (layout.ell_max + 1) ** 2
    projection = project_runtime_native_state(
        layout=layout,
        layout_manifest=ops.layout_metadata,
        photon_T=np.arange(size, dtype=np.float64),
        photon_E=np.arange(size, dtype=np.float64) + 100.0,
        neutrino_tower=np.arange(size, dtype=np.float64) + 200.0,
        source_template=np.asarray(ops.source_template, dtype=np.float64),
        baryon_block=np.array([1.0, 2.0, 2.0, 3.0], dtype=np.float64),
        cdm_block=np.array([4.0, 5.0], dtype=np.float64),
        matter_history_eta=np.array([0.1, 0.2], dtype=np.float64),
        baryon_history_samples=np.array([[1.0, 2.0, 2.0, 3.0], [1.5, 2.5, 2.5, 3.5]], dtype=np.float64),
        cdm_history_samples=np.array([[4.0, 5.0], [4.5, 5.5]], dtype=np.float64),
        matter_block_labels={
            "baryon": ("delta_b", "v_b", "v_e", "drag_lock_residual"),
            "cdm": ("delta_c", "v_c"),
        },
    )
    assert projection.sector_status["baryon"] == "runtime_postprocessed_homogeneous_limit"
    assert projection.sector_status["cdm"] == "runtime_postprocessed_homogeneous_limit"
    assert projection.metadata["projection_mode"] == "multi_live_mode_label_with_runtime_local_matter_blocks"
    assert projection.metadata["matter_history_available"] is True
    assert projection.metadata["matter_history_sample_count"] == 2
    assert projection.metadata["resolved_sector_order"] == ("ph_I", "ph_E", "nu_I", "baryon", "cdm", "src")
    assert projection.state_vector[flatten(layout, "m0", "baryon", None, None, local_dof=1)] == pytest.approx(2.0)
    assert projection.state_vector[flatten(layout, "m0", "cdm", None, None, local_dof=1)] == pytest.approx(5.0)


def test_project_runtime_native_state_can_embed_layout_auxiliary_local_matter_blocks() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2")},
    )
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2")}
    layout = build_hierarchy_layout(backend, truncation)
    ops = assemble_hierarchy_ops(
        {
            "branch": "orthogonal",
            "opacity_data": {"Gamma_T": 2.0},
            "source_tables": {"visibility_amplitude": 1.25},
        },
        backend,
        truncation,
        {"polarization_source": 0.5},
    )
    size = (layout.ell_max + 1) ** 2
    projection = project_runtime_native_state(
        layout=layout,
        layout_manifest=ops.layout_metadata,
        photon_T=np.arange(size, dtype=np.float64),
        photon_E=np.arange(size, dtype=np.float64) + 100.0,
        neutrino_tower=np.arange(size, dtype=np.float64) + 200.0,
        source_template=np.asarray(ops.source_template, dtype=np.float64),
        baryon_block=np.array([1.0, 2.0, 2.0, 3.0], dtype=np.float64),
        cdm_block=np.array([4.0, 5.0], dtype=np.float64),
        matter_history_eta=np.array([0.1, 0.2], dtype=np.float64),
        baryon_history_samples=np.array([[1.0, 2.0, 2.0, 3.0], [1.5, 2.5, 2.5, 3.5]], dtype=np.float64),
        cdm_history_samples=np.array([[4.0, 5.0], [4.5, 5.5]], dtype=np.float64),
        matter_sector_status={
            "baryon": "layout_operator_auxiliary_local_matter",
            "cdm": "layout_operator_auxiliary_local_matter",
        },
        matter_block_metadata={
            "owner": "mode_ops.mass_inverse_auxiliary_local_matter_evolution",
            "reference_owner": "runtime_postprocessed_homogeneous_local_matter",
        },
    )
    assert projection.sector_status["baryon"] == "layout_operator_auxiliary_local_matter"
    assert projection.sector_status["cdm"] == "layout_operator_auxiliary_local_matter"
    assert projection.metadata["projection_mode"] == (
        "multi_live_mode_label_with_layout_auxiliary_local_matter_blocks"
    )
    assert projection.hierarchy_state.matter_block["owner"] == (
        "mode_ops.mass_inverse_auxiliary_local_matter_evolution"
    )
    assert projection.hierarchy_state.matter_block["reference_owner"] == (
        "runtime_postprocessed_homogeneous_local_matter"
    )


def test_project_runtime_native_state_can_embed_postprocessed_b_mode_proxy() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2")},
    )
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2")}
    layout = build_hierarchy_layout(backend, truncation)
    ops = assemble_hierarchy_ops(
        {
            "branch": "orthogonal",
            "opacity_data": {"Gamma_T": 2.0},
            "source_tables": {"visibility_amplitude": 1.25},
        },
        backend,
        truncation,
        {"polarization_source": 0.5},
    )
    size = (layout.ell_max + 1) ** 2
    b_proxy = np.zeros(size, dtype=np.float64)
    b_proxy[7] = 0.25
    b_history = np.vstack([np.zeros(size, dtype=np.float64), b_proxy])
    projection = project_runtime_native_state(
        layout=layout,
        layout_manifest=ops.layout_metadata,
        photon_T=np.arange(size, dtype=np.float64),
        photon_E=np.arange(size, dtype=np.float64) + 100.0,
        photon_B=b_proxy,
        photon_B_history_eta=np.array([0.1, 0.2], dtype=np.float64),
        photon_B_history_samples=b_history,
        neutrino_tower=np.arange(size, dtype=np.float64) + 200.0,
        source_template=np.asarray(ops.source_template, dtype=np.float64),
    )
    assert projection.sector_status["ph_B"] == "layout_operator_auxiliary_b_mode_history"
    assert projection.metadata["resolved_sector_order"] == ("ph_I", "ph_E", "ph_B", "nu_I", "src")
    assert projection.metadata["b_history_available"] is True
    assert projection.metadata["b_history_sample_count"] == 2
    assert projection.state_vector[flatten(layout, "m0", "ph_B", 2, 1)] == pytest.approx(0.25)
    assert np.asarray(projection.hierarchy_state.photon_polarization_block["eta"]).shape == (2,)
    assert np.asarray(projection.hierarchy_state.photon_polarization_block["B_history"]).shape == (2, size)
