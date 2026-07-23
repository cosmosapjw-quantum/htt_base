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
    build_reduced_harmonic_affine_operator,
    build_reduced_joint_affine_operator,
    build_reduced_local_affine_operator,
    build_reduced_source_affine_operator,
    evaluate_reduced_harmonic_rhs,
    evaluate_reduced_local_rhs,
    evaluate_reduced_source_blocks,
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
from scipy.sparse import issparse


def _backend():
    return build_backend(get_family_spec("I"), truncation={"ell_max": 4, "mode_labels": ("m0", "m+2", "m-2")})


def test_layout_freezes_sector_order_and_mode_labels() -> None:
    layout = build_hierarchy_layout(_backend(), {"ell_max": 4, "mode_labels": ("m0", "m+2", "m-2")})
    assert layout.sector_order == SECTOR_ORDER
    assert layout.mode_labels == ("m0", "m+2", "m-2")


def test_layout_defaults_open_multi_label_runtime_for_family_backends() -> None:
    backend_v = build_backend(get_family_spec("V"), truncation={"ell_max": 2})
    layout_v = build_hierarchy_layout(backend_v, {"ell_max": 2})
    assert layout_v.mode_labels == ("mu_open", "mu_open+", "mu_open-")

    backend_viii = build_backend(get_family_spec("VIII"), truncation={"ell_max": 2})
    layout_viii = build_hierarchy_layout(backend_viii, {"ell_max": 2})
    assert layout_viii.mode_labels == ("mu_sl2r", "mu_sl2r+", "mu_sl2r-")


def test_mode_label_weights_do_not_vary_by_family_without_runtime_evidence() -> None:
    truncation = {"ell_max": 2}

    backend_v = build_backend(get_family_spec("V"), truncation=truncation)
    layout_v = build_hierarchy_layout(backend_v, truncation)
    diag_v = np.asarray(assemble_mass_matrix({"branch": "orthogonal"}, backend_v, truncation).diagonal(), dtype=np.float64)
    ratio_v = diag_v[flatten(layout_v, "mu_open+", "ph_I", 0, 0)] / diag_v[flatten(layout_v, "mu_open", "ph_I", 0, 0)]

    backend_viii = build_backend(get_family_spec("VIII"), truncation=truncation)
    layout_viii = build_hierarchy_layout(backend_viii, truncation)
    diag_viii = np.asarray(
        assemble_mass_matrix({"branch": "orthogonal"}, backend_viii, truncation).diagonal(),
        dtype=np.float64,
    )
    ratio_viii = (
        diag_viii[flatten(layout_viii, "mu_sl2r+", "ph_I", 0, 0)]
        / diag_viii[flatten(layout_viii, "mu_sl2r", "ph_I", 0, 0)]
    )

    assert ratio_v > 1.0
    assert ratio_viii > 1.0
    assert ratio_viii == pytest.approx(ratio_v)


def test_family_conditioned_harmonic_topology_varies_by_backend() -> None:
    bg = {
        "branch": "tilted",
        "opacity_data": {"Gamma_T": 0.0},
        "sigma_tensor": np.zeros((3, 3), dtype=np.float64),
        "source_tables": {},
    }

    def _cross_block(family: str) -> np.ndarray:
        backend = build_backend(get_family_spec(family), truncation={"ell_max": 2})
        layout = build_hierarchy_layout(backend, {"ell_max": 2})
        width = (layout.ell_max + 1) ** 2
        block_size = 4 * width
        empty_h = {str(mu): np.zeros(width, dtype=np.float64) for mu in layout.mode_labels}
        baryon = {str(mu): np.zeros(4, dtype=np.float64) for mu in layout.mode_labels}
        affine = build_reduced_harmonic_affine_operator(
            layout,
            bg,
            backend,
            residual_mode_labels=tuple(str(mu) for mu in layout.mode_labels[1:]),
            photon_T_by_mode_label=empty_h,
            photon_E_by_mode_label=empty_h,
            photon_B_by_mode_label=empty_h,
            neutrino_by_mode_label=empty_h,
            baryon_by_mode_label=baryon,
        )
        return np.asarray(affine.matrix[:block_size, block_size : 2 * block_size].todense(), dtype=np.float64)

    cross_v = _cross_block("V")
    cross_viii = _cross_block("VIII")

    assert np.allclose(cross_v, 0.0)
    assert np.linalg.norm(cross_viii) > 0.0


def test_reduced_source_affine_dense_return_matches_sparse_default() -> None:
    backend = build_backend(get_family_spec("I"), truncation={"ell_max": 2, "mode_labels": ("m0",)})
    layout = build_hierarchy_layout(backend, {"ell_max": 2, "mode_labels": ("m0",)})
    width = (layout.ell_max + 1) ** 2
    bg = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 1.25},
        "sigma_tensor": np.zeros((3, 3), dtype=np.float64),
        "source_tables": {},
    }
    harmonic = {"m0": np.linspace(0.0, 1.0, width, dtype=np.float64)}

    sparse_affine = build_reduced_source_affine_operator(
        layout,
        bg,
        backend,
        mode_labels=("m0",),
        photon_T_by_mode_label=harmonic,
        photon_E_by_mode_label=harmonic,
        photon_B_by_mode_label=harmonic,
    )
    dense_affine = build_reduced_source_affine_operator(
        layout,
        bg,
        backend,
        mode_labels=("m0",),
        photon_T_by_mode_label=harmonic,
        photon_E_by_mode_label=harmonic,
        photon_B_by_mode_label=harmonic,
        return_dense=True,
    )

    assert issparse(sparse_affine.matrix)
    assert isinstance(dense_affine.matrix, np.ndarray)
    np.testing.assert_allclose(dense_affine.matrix, sparse_affine.matrix.toarray())
    np.testing.assert_allclose(dense_affine.bias, sparse_affine.bias)


def test_reduced_local_and_harmonic_dense_returns_match_sparse_defaults() -> None:
    backend = _backend()
    layout = build_hierarchy_layout(
        backend,
        {"ell_max": 4, "mode_labels": ("m0", "m+2", "m-2")},
    )
    width = (layout.ell_max + 1) ** 2
    bg = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 1.25},
        "sigma_tensor": np.zeros((3, 3), dtype=np.float64),
        "source_tables": {"visibility_amplitude": 0.2, "polarization_source": 0.1},
    }
    residual_labels = ("m+2", "m-2")
    theta_1 = {"m+2": 0.1, "m-2": -0.2}
    sparse_local = build_reduced_local_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=residual_labels,
        theta_1_by_mode_label=theta_1,
    )
    dense_local = build_reduced_local_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=residual_labels,
        theta_1_by_mode_label=theta_1,
        return_dense=True,
    )
    assert issparse(sparse_local.matrix)
    assert isinstance(dense_local.matrix, np.ndarray)
    np.testing.assert_allclose(dense_local.matrix, sparse_local.matrix.toarray())
    np.testing.assert_allclose(dense_local.bias, sparse_local.bias)

    harmonic = {
        "m0": np.linspace(0.0, 1.0, width, dtype=np.float64),
        "m+2": np.linspace(1.0, 2.0, width, dtype=np.float64),
        "m-2": np.linspace(-1.0, 0.0, width, dtype=np.float64),
    }
    baryon = {
        "m0": np.zeros(4, dtype=np.float64),
        "m+2": np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64),
        "m-2": np.array([-0.1, -0.2, -0.3, -0.4], dtype=np.float64),
    }
    sparse_harmonic = build_reduced_harmonic_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=residual_labels,
        photon_T_by_mode_label=harmonic,
        photon_E_by_mode_label=harmonic,
        photon_B_by_mode_label=harmonic,
        neutrino_by_mode_label=harmonic,
        baryon_by_mode_label=baryon,
    )
    dense_harmonic = build_reduced_harmonic_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=residual_labels,
        photon_T_by_mode_label=harmonic,
        photon_E_by_mode_label=harmonic,
        photon_B_by_mode_label=harmonic,
        neutrino_by_mode_label=harmonic,
        baryon_by_mode_label=baryon,
        return_dense=True,
    )
    assert issparse(sparse_harmonic.matrix)
    assert isinstance(dense_harmonic.matrix, np.ndarray)
    np.testing.assert_allclose(dense_harmonic.matrix, sparse_harmonic.matrix.toarray())
    np.testing.assert_allclose(dense_harmonic.bias, sparse_harmonic.bias)


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


def test_mass_matrix_is_positive_diagonal_identity_like_pack() -> None:
    backend = _backend()
    truncation = {"ell_max": 3, "mode_labels": ("m0",)}
    layout = build_hierarchy_layout(backend, truncation)
    M = assemble_mass_matrix({}, backend, truncation)
    assert M.shape == (layout.size, layout.size)
    diag = np.asarray(M.diagonal(), dtype=np.float64)
    assert np.all(diag > 0.0)
    assert not np.allclose(diag, 1.0)


def test_mass_matrix_tracks_branch_and_sector_weights() -> None:
    backend = _backend()
    truncation = {"ell_max": 2, "mode_labels": ("m0",)}
    layout = build_hierarchy_layout(backend, truncation)
    M_orth = assemble_mass_matrix({"branch": "orthogonal"}, backend, truncation)
    M_tilt = assemble_mass_matrix({"branch": "tilted"}, backend, truncation)
    orth_diag = np.asarray(M_orth.diagonal(), dtype=np.float64)
    tilt_diag = np.asarray(M_tilt.diagonal(), dtype=np.float64)
    i_idx = flatten(layout, "m0", "ph_I", 2, 0)
    e_idx = flatten(layout, "m0", "ph_E", 2, 0)
    b_idx = flatten(layout, "m0", "ph_B", 2, 0)
    baryon_idx = flatten(layout, "m0", "baryon", None, None, local_dof=0)
    assert tilt_diag[i_idx] > orth_diag[i_idx]
    assert orth_diag[e_idx] > orth_diag[i_idx]
    assert orth_diag[b_idx] >= orth_diag[e_idx]
    assert orth_diag[baryon_idx] != orth_diag[i_idx]


def test_mass_matrix_cache_tracks_mutated_branch_on_same_background() -> None:
    backend = _backend()
    truncation = {"ell_max": 2, "mode_labels": ("m0",)}
    layout = build_hierarchy_layout(backend, truncation)
    bg = {"branch": "orthogonal"}

    orth_diag = np.asarray(
        assemble_mass_matrix(bg, backend, truncation).diagonal(),
        dtype=np.float64,
    )
    bg["branch"] = "tilted"
    tilt_diag = np.asarray(
        assemble_mass_matrix(bg, backend, truncation).diagonal(),
        dtype=np.float64,
    )

    i_idx = flatten(layout, "m0", "ph_I", 2, 0)
    assert tilt_diag[i_idx] > orth_diag[i_idx]


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


def test_reduced_local_rhs_matches_full_operator_subset() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")},
    )
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")}
    layout = build_hierarchy_layout(backend, truncation)
    bg = {
        "branch": "tilted",
        "opacity_data": {"Gamma_T": 2.5},
        "sigma_tensor": np.diag([0.2, -0.1, -0.1]),
    }
    ops = assemble_hierarchy_ops(bg, backend, truncation, {})
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
    state = np.zeros(layout.size, dtype=np.float64)
    for mu, baryon_row in baryon_by_mode_label.items():
        for local_dof, value in enumerate(baryon_row):
            state[flatten(layout, mu, "baryon", None, None, local_dof)] = value
    for mu, cdm_row in cdm_by_mode_label.items():
        for local_dof, value in enumerate(cdm_row):
            state[flatten(layout, mu, "cdm", None, None, local_dof)] = value
    for mu, theta_1 in theta_1_by_mode_label.items():
        state[flatten(layout, mu, "ph_I", 1, 0)] = theta_1
    full_drive = np.asarray(
        (ops.A_fs @ state) + (ops.A_mix @ state) + (ops.A_coll @ state) + np.asarray(ops.source_template, dtype=np.float64),
        dtype=np.float64,
    )
    mass_diag = np.asarray(ops.mass_matrix.diagonal(), dtype=np.float64)
    reduced_baryon, reduced_cdm = evaluate_reduced_local_rhs(
        layout,
        bg,
        backend,
        baryon_by_mode_label=baryon_by_mode_label,
        cdm_by_mode_label=cdm_by_mode_label,
        theta_1_by_mode_label=theta_1_by_mode_label,
    )
    for mu in layout.mode_labels:
        baryon_idx = np.array(
            [flatten(layout, mu, "baryon", None, None, local_dof) for local_dof in range(4)],
            dtype=np.int64,
        )
        cdm_idx = np.array(
            [flatten(layout, mu, "cdm", None, None, local_dof) for local_dof in range(2)],
            dtype=np.int64,
        )
        np.testing.assert_allclose(
            reduced_baryon[str(mu)],
            full_drive[baryon_idx] / mass_diag[baryon_idx],
        )
        np.testing.assert_allclose(
            reduced_cdm[str(mu)],
            full_drive[cdm_idx] / mass_diag[cdm_idx],
        )


def test_reduced_local_affine_operator_matches_direct_evaluator_on_residual_labels() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")},
    )
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")}
    layout = build_hierarchy_layout(backend, truncation)
    bg = {
        "branch": "tilted",
        "opacity_data": {"Gamma_T": 2.5},
        "sigma_tensor": np.diag([0.2, -0.1, -0.1]),
    }
    residual_labels = ("m+2", "m-2")
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
    reduced_baryon, reduced_cdm = evaluate_reduced_local_rhs(
        layout,
        bg,
        backend,
        baryon_by_mode_label=baryon_by_mode_label,
        cdm_by_mode_label=cdm_by_mode_label,
        theta_1_by_mode_label=theta_1_by_mode_label,
    )
    affine = build_reduced_local_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=residual_labels,
        theta_1_by_mode_label=theta_1_by_mode_label,
    )
    residual_state = np.concatenate(
        [
            baryon_by_mode_label["m+2"],
            cdm_by_mode_label["m+2"],
            baryon_by_mode_label["m-2"],
            cdm_by_mode_label["m-2"],
        ],
        dtype=np.float64,
    )
    direct = np.concatenate(
        [
            reduced_baryon["m+2"],
            reduced_cdm["m+2"],
            reduced_baryon["m-2"],
            reduced_cdm["m-2"],
        ],
        dtype=np.float64,
    )
    applied = np.asarray(affine.matrix @ residual_state + affine.bias, dtype=np.float64)
    assert affine.mode_labels == residual_labels
    assert affine.matrix.shape == (direct.size, direct.size)
    assert affine.matrix.nnz > 0
    np.testing.assert_allclose(applied, direct)


def test_reduced_harmonic_rhs_matches_full_operator_subset() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")},
    )
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")}
    layout = build_hierarchy_layout(backend, truncation)
    bg = {
        "branch": "tilted",
        "H_local": 2.0,
        "opacity_data": {"Gamma_T": 2.5, "H_local": 2.0},
        "sigma_tensor": np.diag([0.2, -0.1, -0.1]),
        "source_tables": {
            "visibility_amplitude": 1.25,
            "polarization_source": 0.4,
            "reionization_amplitude": 0.2,
        },
    }
    ops = assemble_hierarchy_ops(bg, backend, truncation, bg["source_tables"])
    width = (layout.ell_max + 1) ** 2
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
    state = np.zeros(layout.size, dtype=np.float64)
    for mu, tower in photon_t_by_mode_label.items():
        for ell in range(layout.ell_max + 1):
            offset = sum(2 * level + 1 for level in range(ell))
            for m in range(-ell, ell + 1):
                slot = offset + (m + ell)
                state[flatten(layout, mu, "ph_I", ell, m)] = tower[slot]
                state[flatten(layout, mu, "ph_E", ell, m)] = photon_e_by_mode_label[mu][slot]
                state[flatten(layout, mu, "ph_B", ell, m)] = photon_b_by_mode_label[mu][slot]
                state[flatten(layout, mu, "nu_I", ell, m)] = neutrino_by_mode_label[mu][slot]
        for local_dof, value in enumerate(baryon_by_mode_label[mu]):
            state[flatten(layout, mu, "baryon", None, None, local_dof)] = value
        for local_dof, value in enumerate(source_by_mode_label[mu]):
            state[flatten(layout, mu, "src", None, None, local_dof)] = value
    full_drive = np.asarray(
        (ops.A_fs @ state) + (ops.A_mix @ state) + (ops.A_coll @ state) + np.asarray(ops.source_template, dtype=np.float64),
        dtype=np.float64,
    )
    mass_diag = np.asarray(ops.mass_matrix.diagonal(), dtype=np.float64)
    reduced_t, reduced_e, reduced_b, reduced_nu = evaluate_reduced_harmonic_rhs(
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
    for mu in layout.mode_labels:
        idx_t = np.array(
            [flatten(layout, mu, "ph_I", ell, m) for ell in range(layout.ell_max + 1) for m in range(-ell, ell + 1)],
            dtype=np.int64,
        )
        idx_e = np.array(
            [flatten(layout, mu, "ph_E", ell, m) for ell in range(layout.ell_max + 1) for m in range(-ell, ell + 1)],
            dtype=np.int64,
        )
        idx_b = np.array(
            [flatten(layout, mu, "ph_B", ell, m) for ell in range(layout.ell_max + 1) for m in range(-ell, ell + 1)],
            dtype=np.int64,
        )
        idx_nu = np.array(
            [flatten(layout, mu, "nu_I", ell, m) for ell in range(layout.ell_max + 1) for m in range(-ell, ell + 1)],
            dtype=np.int64,
        )
        np.testing.assert_allclose(reduced_t[str(mu)], full_drive[idx_t] / mass_diag[idx_t])
        np.testing.assert_allclose(reduced_e[str(mu)], full_drive[idx_e] / mass_diag[idx_e])
        np.testing.assert_allclose(reduced_b[str(mu)], full_drive[idx_b] / mass_diag[idx_b])
        np.testing.assert_allclose(reduced_nu[str(mu)], full_drive[idx_nu] / mass_diag[idx_nu])


def test_reduced_harmonic_affine_operator_matches_direct_evaluator_on_residual_labels() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")},
    )
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")}
    layout = build_hierarchy_layout(backend, truncation)
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
    width = (layout.ell_max + 1) ** 2
    residual_labels = ("m+2", "m-2")
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
    reduced_t, reduced_e, reduced_b, reduced_nu = evaluate_reduced_harmonic_rhs(
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
    affine = build_reduced_harmonic_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=residual_labels,
        photon_T_by_mode_label=photon_t_by_mode_label,
        photon_E_by_mode_label=photon_e_by_mode_label,
        photon_B_by_mode_label=photon_b_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=baryon_by_mode_label,
        source_by_mode_label=source_by_mode_label,
    )
    residual_state = np.concatenate(
        [
            photon_t_by_mode_label["m+2"],
            photon_e_by_mode_label["m+2"],
            photon_b_by_mode_label["m+2"],
            neutrino_by_mode_label["m+2"],
            photon_t_by_mode_label["m-2"],
            photon_e_by_mode_label["m-2"],
            photon_b_by_mode_label["m-2"],
            neutrino_by_mode_label["m-2"],
        ],
        dtype=np.float64,
    )
    direct = np.concatenate(
        [
            reduced_t["m+2"],
            reduced_e["m+2"],
            reduced_b["m+2"],
            reduced_nu["m+2"],
            reduced_t["m-2"],
            reduced_e["m-2"],
            reduced_b["m-2"],
            reduced_nu["m-2"],
        ],
        dtype=np.float64,
    )
    applied = np.asarray(affine.matrix @ residual_state + affine.bias, dtype=np.float64)
    assert affine.mode_labels == residual_labels
    assert affine.matrix.shape == (direct.size, direct.size)
    assert affine.matrix.nnz > 0
    np.testing.assert_allclose(applied, direct)


def test_reduced_joint_affine_operator_matches_direct_local_and_harmonic_evaluators() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")},
    )
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")}
    layout = build_hierarchy_layout(backend, truncation)
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
    residual_labels = ("m+2", "m-2")
    width = (layout.ell_max + 1) ** 2
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
    cdm_by_mode_label = {
        "m0": np.array([0.9, 1.0], dtype=np.float64),
        "m+2": np.array([1.1, 1.2], dtype=np.float64),
        "m-2": np.array([-0.4, 0.2], dtype=np.float64),
    }
    source_by_mode_label = {
        "m0": np.array([0.2, -0.1, 0.0], dtype=np.float64),
        "m+2": np.array([0.3, 0.4, -0.2], dtype=np.float64),
        "m-2": np.array([-0.25, 0.15, 0.05], dtype=np.float64),
    }
    theta_1_by_mode_label = {
        "m0": photon_t_by_mode_label["m0"][2],
        "m+2": photon_t_by_mode_label["m+2"][2],
        "m-2": photon_t_by_mode_label["m-2"][2],
    }
    direct_local_b, direct_local_c = evaluate_reduced_local_rhs(
        layout,
        bg,
        backend,
        baryon_by_mode_label=baryon_by_mode_label,
        cdm_by_mode_label=cdm_by_mode_label,
        theta_1_by_mode_label=theta_1_by_mode_label,
    )
    direct_t, direct_e, direct_b, direct_nu = evaluate_reduced_harmonic_rhs(
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
    ops = assemble_hierarchy_ops(bg, backend, truncation, bg["source_tables"])
    state = np.zeros(layout.size, dtype=np.float64)
    for mu in layout.mode_labels:
        for ell in range(layout.ell_max + 1):
            offset = sum(2 * level + 1 for level in range(ell))
            for m in range(-ell, ell + 1):
                slot = offset + (m + ell)
                state[flatten(layout, mu, "ph_I", ell, m)] = photon_t_by_mode_label[str(mu)][slot]
                state[flatten(layout, mu, "ph_E", ell, m)] = photon_e_by_mode_label[str(mu)][slot]
                state[flatten(layout, mu, "ph_B", ell, m)] = photon_b_by_mode_label[str(mu)][slot]
                state[flatten(layout, mu, "nu_I", ell, m)] = neutrino_by_mode_label[str(mu)][slot]
        for local_dof, value in enumerate(baryon_by_mode_label[str(mu)]):
            state[flatten(layout, mu, "baryon", None, None, local_dof)] = value
        for local_dof, value in enumerate(cdm_by_mode_label[str(mu)]):
            state[flatten(layout, mu, "cdm", None, None, local_dof)] = value
        for local_dof, value in enumerate(source_by_mode_label[str(mu)]):
            state[flatten(layout, mu, "src", None, None, local_dof)] = value
    full_drive = np.asarray(
        (ops.A_fs @ state) + (ops.A_mix @ state) + (ops.A_coll @ state) + np.asarray(ops.source_template, dtype=np.float64),
        dtype=np.float64,
    )
    mass_diag = np.asarray(ops.mass_matrix.diagonal(), dtype=np.float64)
    affine = build_reduced_joint_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=residual_labels,
        photon_T_by_mode_label=photon_t_by_mode_label,
        photon_E_by_mode_label=photon_e_by_mode_label,
        photon_B_by_mode_label=photon_b_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=baryon_by_mode_label,
        source_by_mode_label=source_by_mode_label,
    )
    local_state = np.concatenate(
        [
            baryon_by_mode_label["m+2"],
            cdm_by_mode_label["m+2"],
            baryon_by_mode_label["m-2"],
            cdm_by_mode_label["m-2"],
        ],
        dtype=np.float64,
    )
    harmonic_state = np.concatenate(
        [
            photon_t_by_mode_label["m+2"],
            photon_e_by_mode_label["m+2"],
            photon_b_by_mode_label["m+2"],
            neutrino_by_mode_label["m+2"],
            photon_t_by_mode_label["m-2"],
            photon_e_by_mode_label["m-2"],
            photon_b_by_mode_label["m-2"],
            neutrino_by_mode_label["m-2"],
        ],
        dtype=np.float64,
    )
    source_state = np.concatenate(
        [
            source_by_mode_label["m+2"],
            source_by_mode_label["m-2"],
        ],
        dtype=np.float64,
    )
    direct_source = np.concatenate(
        [
            np.array(
                [
                    full_drive[flatten(layout, "m+2", "src", None, None, local_dof)]
                    / mass_diag[flatten(layout, "m+2", "src", None, None, local_dof)]
                    for local_dof in range(layout.sector_local_dofs["src"])
                ],
                dtype=np.float64,
            ),
            np.array(
                [
                    full_drive[flatten(layout, "m-2", "src", None, None, local_dof)]
                    / mass_diag[flatten(layout, "m-2", "src", None, None, local_dof)]
                    for local_dof in range(layout.sector_local_dofs["src"])
                ],
                dtype=np.float64,
            ),
        ],
        dtype=np.float64,
    )
    direct = np.concatenate(
        [
            direct_local_b["m+2"],
            direct_local_c["m+2"],
            direct_local_b["m-2"],
            direct_local_c["m-2"],
            direct_t["m+2"],
            direct_e["m+2"],
            direct_b["m+2"],
            direct_nu["m+2"],
            direct_t["m-2"],
            direct_e["m-2"],
            direct_b["m-2"],
            direct_nu["m-2"],
            direct_source,
        ],
        dtype=np.float64,
    )
    applied = np.asarray(
        affine.matrix @ np.concatenate([local_state, harmonic_state, source_state], dtype=np.float64) + affine.bias,
        dtype=np.float64,
    )
    assert affine.mode_labels == residual_labels
    assert affine.local_dof == local_state.size
    assert affine.harmonic_dof == harmonic_state.size
    assert affine.source_dof == source_state.size
    np.testing.assert_allclose(applied, direct)


def test_reduced_joint_affine_operator_consumes_live_covered_source_state() -> None:
    backend = build_backend(
        get_family_spec("VIII"),
        truncation={"ell_max": 2},
    )
    truncation = {"ell_max": 2}
    layout = build_hierarchy_layout(backend, truncation)
    width = (layout.ell_max + 1) ** 2
    bg = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 0.4},
        "sigma_tensor": np.zeros((3, 3), dtype=np.float64),
        "source_tables": {},
    }
    empty_h = {str(mu): np.zeros(width, dtype=np.float64) for mu in layout.mode_labels}
    baryon = {str(mu): np.zeros(4, dtype=np.float64) for mu in layout.mode_labels}
    source_zero = {
        "mu_sl2r": np.zeros(3, dtype=np.float64),
        "mu_sl2r+": np.zeros(3, dtype=np.float64),
        "mu_sl2r-": np.zeros(3, dtype=np.float64),
    }
    source_live = {
        "mu_sl2r": np.array([0.25, -0.15, 0.35], dtype=np.float64),
        "mu_sl2r+": np.zeros(3, dtype=np.float64),
        "mu_sl2r-": np.zeros(3, dtype=np.float64),
    }
    affine_zero = build_reduced_joint_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=("mu_sl2r+", "mu_sl2r-"),
        photon_T_by_mode_label=empty_h,
        photon_E_by_mode_label=empty_h,
        photon_B_by_mode_label=empty_h,
        neutrino_by_mode_label=empty_h,
        baryon_by_mode_label=baryon,
        source_by_mode_label=source_zero,
    )
    affine_live = build_reduced_joint_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=("mu_sl2r+", "mu_sl2r-"),
        photon_T_by_mode_label=empty_h,
        photon_E_by_mode_label=empty_h,
        photon_B_by_mode_label=empty_h,
        neutrino_by_mode_label=empty_h,
        baryon_by_mode_label=baryon,
        source_by_mode_label=source_live,
    )
    assert np.linalg.norm(np.asarray(affine_live.bias - affine_zero.bias, dtype=np.float64)) > 0.0


def test_reduced_harmonic_rhs_can_reconstruct_source_local_block_from_source_tables() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")},
    )
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")}
    layout = build_hierarchy_layout(backend, truncation)
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
    photon_t_by_mode_label = {mu: np.linspace(0.1, 0.9, width, dtype=np.float64) for mu in layout.mode_labels}
    photon_e_by_mode_label = {mu: np.linspace(0.6, -0.2, width, dtype=np.float64) for mu in layout.mode_labels}
    photon_b_by_mode_label = {mu: np.linspace(-0.4, 0.4, width, dtype=np.float64) for mu in layout.mode_labels}
    neutrino_by_mode_label = {mu: np.linspace(0.15, 0.75, width, dtype=np.float64) for mu in layout.mode_labels}
    baryon_by_mode_label = {
        mu: np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64)
        for mu in layout.mode_labels
    }
    source_template = assemble_source_vector(
        bg,
        backend,
        truncation,
        bg["source_tables"],
    )
    explicit_source_by_mode_label = evaluate_reduced_source_blocks(layout, bg, backend)
    for mu in layout.mode_labels:
        indices = np.array(
            [
                flatten(layout, str(mu), "src", None, None, local_dof)
                for local_dof in range(layout.sector_local_dofs["src"])
            ],
            dtype=np.int64,
        )
        np.testing.assert_allclose(
            explicit_source_by_mode_label[str(mu)],
            np.asarray(source_template[indices], dtype=np.float64),
        )
    explicit = evaluate_reduced_harmonic_rhs(
        layout,
        bg,
        backend,
        photon_T_by_mode_label=photon_t_by_mode_label,
        photon_E_by_mode_label=photon_e_by_mode_label,
        photon_B_by_mode_label=photon_b_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=baryon_by_mode_label,
        source_by_mode_label=explicit_source_by_mode_label,
    )
    fallback = evaluate_reduced_harmonic_rhs(
        layout,
        bg,
        backend,
        photon_T_by_mode_label=photon_t_by_mode_label,
        photon_E_by_mode_label=photon_e_by_mode_label,
        photon_B_by_mode_label=photon_b_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=baryon_by_mode_label,
    )
    for sector_explicit, sector_fallback in zip(explicit, fallback, strict=True):
        for mu in layout.mode_labels:
            np.testing.assert_allclose(sector_explicit[str(mu)], sector_fallback[str(mu)])


def test_vih_h_parameter_enters_through_twist_kernel_not_frozen_scalar_bridge() -> None:
    truncation = {"ell_max": 3, "mode_labels": ("m0", "m+2", "m-2")}
    backend_open = build_backend(get_family_spec("VI_h", h=-0.25), truncation=truncation)
    backend_deep = build_backend(get_family_spec("VI_h", h=-2.0), truncation=truncation)
    layout = build_hierarchy_layout(backend_open, truncation)
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
    photon_t_by_mode_label = {mu: np.linspace(0.1, 0.9, width, dtype=np.float64) for mu in layout.mode_labels}
    photon_e_by_mode_label = {mu: np.linspace(0.6, -0.2, width, dtype=np.float64) for mu in layout.mode_labels}
    photon_b_by_mode_label = {mu: np.linspace(-0.4, 0.4, width, dtype=np.float64) for mu in layout.mode_labels}
    neutrino_by_mode_label = {mu: np.linspace(0.15, 0.75, width, dtype=np.float64) for mu in layout.mode_labels}
    baryon_by_mode_label = {
        mu: np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float64)
        for mu in layout.mode_labels
    }
    open_rhs = evaluate_reduced_harmonic_rhs(
        layout,
        bg,
        backend_open,
        photon_T_by_mode_label=photon_t_by_mode_label,
        photon_E_by_mode_label=photon_e_by_mode_label,
        photon_B_by_mode_label=photon_b_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=baryon_by_mode_label,
    )
    deep_rhs = evaluate_reduced_harmonic_rhs(
        layout,
        bg,
        backend_deep,
        photon_T_by_mode_label=photon_t_by_mode_label,
        photon_E_by_mode_label=photon_e_by_mode_label,
        photon_B_by_mode_label=photon_b_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=baryon_by_mode_label,
    )
    diff = np.linalg.norm(
        np.asarray(open_rhs[1]["m+2"], dtype=np.float64)
        - np.asarray(deep_rhs[1]["m+2"], dtype=np.float64)
    )
    assert diff > 0.0


def test_reduced_harmonic_rhs_couples_nonmonopole_mode_labels() -> None:
    backend = build_backend(
        get_family_spec("VIII"),
        truncation={"ell_max": 2},
    )
    truncation = {"ell_max": 2}
    layout = build_hierarchy_layout(backend, truncation)
    width = (layout.ell_max + 1) ** 2
    bg = {
        "branch": "tilted",
        "opacity_data": {"Gamma_T": 0.0},
        "sigma_tensor": np.zeros((3, 3), dtype=np.float64),
        "source_tables": {},
    }
    empty = np.zeros(width, dtype=np.float64)
    slot_ell2_m0 = sum(2 * ell + 1 for ell in range(2)) + 2
    photon_t_by_mode_label = {"mu_sl2r": empty.copy(), "mu_sl2r+": empty.copy(), "mu_sl2r-": empty.copy()}
    photon_e_by_mode_label = {"mu_sl2r": empty.copy(), "mu_sl2r+": empty.copy(), "mu_sl2r-": empty.copy()}
    photon_b_by_mode_label = {"mu_sl2r": empty.copy(), "mu_sl2r+": empty.copy(), "mu_sl2r-": empty.copy()}
    neutrino_by_mode_label = {"mu_sl2r": empty.copy(), "mu_sl2r+": empty.copy(), "mu_sl2r-": empty.copy()}
    photon_t_by_mode_label["mu_sl2r+"][slot_ell2_m0] = 1.0
    baryon_by_mode_label = {
        "mu_sl2r": np.zeros(4, dtype=np.float64),
        "mu_sl2r+": np.zeros(4, dtype=np.float64),
        "mu_sl2r-": np.zeros(4, dtype=np.float64),
    }
    reduced_t, _, _, _ = evaluate_reduced_harmonic_rhs(
        layout,
        bg,
        backend,
        photon_T_by_mode_label=photon_t_by_mode_label,
        photon_E_by_mode_label=photon_e_by_mode_label,
        photon_B_by_mode_label=photon_b_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=baryon_by_mode_label,
    )
    assert abs(float(reduced_t["mu_sl2r"][slot_ell2_m0])) > 0.0


def test_reduced_harmonic_rhs_uses_anchor_star_topology_for_residual_labels() -> None:
    backend = build_backend(
        get_family_spec("VIII"),
        truncation={"ell_max": 2},
    )
    truncation = {"ell_max": 2}
    layout = build_hierarchy_layout(backend, truncation)
    width = (layout.ell_max + 1) ** 2
    bg = {
        "branch": "tilted",
        "opacity_data": {"Gamma_T": 0.0},
        "sigma_tensor": np.zeros((3, 3), dtype=np.float64),
        "source_tables": {},
    }
    empty = np.zeros(width, dtype=np.float64)
    slot_ell2_m0 = sum(2 * ell + 1 for ell in range(2)) + 2
    photon_t_by_mode_label = {
        "mu_sl2r": empty.copy(),
        "mu_sl2r+": empty.copy(),
        "mu_sl2r-": empty.copy(),
    }
    photon_e_by_mode_label = {
        "mu_sl2r": empty.copy(),
        "mu_sl2r+": empty.copy(),
        "mu_sl2r-": empty.copy(),
    }
    photon_b_by_mode_label = {
        "mu_sl2r": empty.copy(),
        "mu_sl2r+": empty.copy(),
        "mu_sl2r-": empty.copy(),
    }
    neutrino_by_mode_label = {
        "mu_sl2r": empty.copy(),
        "mu_sl2r+": empty.copy(),
        "mu_sl2r-": empty.copy(),
    }
    photon_t_by_mode_label["mu_sl2r-"][slot_ell2_m0] = 1.0
    baryon_by_mode_label = {
        "mu_sl2r": np.zeros(4, dtype=np.float64),
        "mu_sl2r+": np.zeros(4, dtype=np.float64),
        "mu_sl2r-": np.zeros(4, dtype=np.float64),
    }
    reduced_t, _, _, _ = evaluate_reduced_harmonic_rhs(
        layout,
        bg,
        backend,
        photon_T_by_mode_label=photon_t_by_mode_label,
        photon_E_by_mode_label=photon_e_by_mode_label,
        photon_B_by_mode_label=photon_b_by_mode_label,
        neutrino_by_mode_label=neutrino_by_mode_label,
        baryon_by_mode_label=baryon_by_mode_label,
    )
    assert abs(float(reduced_t["mu_sl2r"][slot_ell2_m0])) > 0.0
    assert abs(float(reduced_t["mu_sl2r+"][slot_ell2_m0])) > 0.0


def test_mode_label_weights_resolve_standard_m_signatures() -> None:
    backend = build_backend(
        get_family_spec("I"),
        truncation={"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")},
    )
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")}
    layout = build_hierarchy_layout(backend, truncation)
    source = assemble_source_vector(
        {"branch": "tilted"},
        backend,
        truncation,
        {"visibility_amplitude": 1.0, "polarization_source": 0.5, "reionization_amplitude": 0.2},
    )
    assert source[flatten(layout, "m+2", "ph_I", 0, 0)] > source[flatten(layout, "m0", "ph_I", 0, 0)]
    assert source[flatten(layout, "m-2", "ph_I", 0, 0)] < source[flatten(layout, "m0", "ph_I", 0, 0)]
    A_fs = assemble_free_streaming_block({"branch": "tilted"}, backend, truncation)
    plus_diag = A_fs[flatten(layout, "m+2", "ph_E", 2, 0), flatten(layout, "m+2", "ph_E", 2, 0)]
    zero_diag = A_fs[flatten(layout, "m0", "ph_E", 2, 0), flatten(layout, "m0", "ph_E", 2, 0)]
    minus_diag = A_fs[flatten(layout, "m-2", "ph_E", 2, 0), flatten(layout, "m-2", "ph_E", 2, 0)]
    assert float(plus_diag) == pytest.approx(0.0)
    assert float(zero_diag) == pytest.approx(0.0)
    assert float(minus_diag) == pytest.approx(0.0)
    plus_stream = A_fs[flatten(layout, "m+2", "ph_E", 1, 0), flatten(layout, "m+2", "ph_E", 2, 0)]
    zero_stream = A_fs[flatten(layout, "m0", "ph_E", 1, 0), flatten(layout, "m0", "ph_E", 2, 0)]
    minus_stream = A_fs[flatten(layout, "m-2", "ph_E", 1, 0), flatten(layout, "m-2", "ph_E", 2, 0)]
    assert abs(float(plus_stream)) > abs(float(zero_stream)) > abs(float(minus_stream))


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
    assert manifest["mass_matrix_realization"] == "family_branch_sector_weighted_diagonal"
    assert manifest["exact_family_operator_available"] is True
    assert manifest["reduced_local_evaluator_available"] is True
    assert manifest["reduced_harmonic_evaluator_available"] is True
    assert manifest["operator_scale_metadata"]["local_drag_by_mu"] == [1.0, 1.0, 1.0]
    assert manifest["operator_scale_metadata"]["mass_by_mu"] == [1.0, 1.0, 1.0]


def test_layout_manifest_records_class_b_runtime_scale_evidence() -> None:
    backend = build_backend(get_family_spec("V"), truncation={"ell_max": 2})
    truncation = {"ell_max": 2}
    layout = build_hierarchy_layout(backend, truncation)
    manifest = build_layout_manifest(
        layout,
        backend,
        truncation,
        {
            "branch": "orthogonal",
            "H_local": 2.0,
            "opacity_data": {"R_b": 0.5, "k_mag": 2.0},
            "baryon_velocity_by_mode_label": {"mu_open": 0.8},
            "theta_1_by_mode_label": {"mu_open": 0.1},
        },
    )
    scale_meta = manifest["operator_scale_metadata"]
    assert scale_meta["local_drag_scale"] == pytest.approx(2.0)
    assert scale_meta["local_drag_by_mu"][0] > 1.0
    assert scale_meta["local_drag_by_mu"][1:] == [1.0, 1.0]
    assert scale_meta["local_drag_slip_by_mu"][0] == pytest.approx(0.5)
    assert scale_meta["transport_scale_owner"] == "opacity_data.k_mag"


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
        float(np.arange(2 * src_width, dtype=np.float64).reshape(2, src_width)[-1, 0])
    )
    assert projection.state_vector[flatten(layout, "m+2", "src", None, None, 0)] == pytest.approx(
        ops.source_template[flatten(layout, "m+2", "src", None, None, 0)]
    )
    assert projection.metadata["source_block_nonzero"] is True
    assert projection.metadata["source_block_norm"] > 0.0
    assert projection.metadata["source_block_owner"] == "mode_ops_source_template"
    assert projection.metadata["source_history_available"] is True
    assert projection.metadata["source_history_sample_count"] == 2
    assert set(projection.metadata["source_mode_labels"]) == {"m0", "m+2"}
    assert set(projection.metadata["source_history_mode_labels"]) == {"m0"}
    assert projection.metadata["resolved_sector_order"] == ("ph_I", "ph_E", "nu_I", "src")
    assert np.asarray(projection.hierarchy_state.source_history_block["eta"]).shape == (2,)
    assert np.asarray(projection.hierarchy_state.source_history_block["history"]).shape == (2, src_width)
    assert set(projection.hierarchy_state.source_history_block["mode_label_blocks"]) == {"m0", "m+2"}
    assert np.asarray(
        projection.hierarchy_state.source_history_block["mode_label_blocks"]["m0"],
        dtype=np.float64,
    ).shape == (src_width,)
    assert np.asarray(
        projection.hierarchy_state.source_history_block["mode_label_blocks"]["m+2"],
        dtype=np.float64,
    ).shape == (src_width,)
    assert set(projection.hierarchy_state.source_history_block["mode_label_history"]) == {"m0"}


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
    assert set(projection.metadata["matter_mode_labels"]) == {"m0", "m+2"}
    assert set(projection.metadata["matter_history_mode_labels"]) == {"m0"}
    assert projection.metadata["resolved_sector_order"] == ("ph_I", "ph_E", "nu_I", "baryon", "cdm", "src")
    assert projection.state_vector[flatten(layout, "m0", "baryon", None, None, local_dof=1)] == pytest.approx(2.0)
    assert projection.state_vector[flatten(layout, "m0", "cdm", None, None, local_dof=1)] == pytest.approx(5.0)
    assert set(projection.hierarchy_state.matter_block["mode_label_blocks"]) == {"m0", "m+2"}
    assert set(projection.hierarchy_state.matter_block["mode_label_history"]) == {"m0"}


def test_project_runtime_native_state_can_preserve_mode_label_resolved_source_history() -> None:
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
        source_history_by_mode_label={
            "m0": np.arange(2 * src_width, dtype=np.float64).reshape(2, src_width),
            "m+2": (10.0 + np.arange(2 * src_width, dtype=np.float64)).reshape(2, src_width),
        },
    )
    assert set(projection.metadata["source_history_mode_labels"]) == {"m0", "m+2"}
    assert set(projection.hierarchy_state.source_history_block["mode_label_history"]) == {"m0", "m+2"}
    np.testing.assert_allclose(
        np.asarray(projection.hierarchy_state.source_history_block["mode_label_history"]["m+2"], dtype=np.float64),
        (10.0 + np.arange(2 * src_width, dtype=np.float64)).reshape(2, src_width),
    )


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
            "baryon": "direct_fluid_rhs_live_history",
            "cdm": "direct_fluid_rhs_live_history",
        },
        matter_block_metadata={
            "owner": "ver2_native_integrator.main_state_local_matter",
            "reference_owner": "ver2_native_integrator.main_state_mode_label_local_matter",
        },
    )
    assert projection.sector_status["baryon"] == "direct_fluid_rhs_live_history"
    assert projection.sector_status["cdm"] == "direct_fluid_rhs_live_history"
    assert projection.metadata["projection_mode"] == (
        "multi_live_mode_label_with_runtime_local_matter_blocks"
    )
    assert projection.hierarchy_state.matter_block["owner"] == (
        "ver2_native_integrator.main_state_local_matter"
    )
    assert projection.hierarchy_state.matter_block["reference_owner"] == (
        "ver2_native_integrator.main_state_mode_label_local_matter"
    )


def test_project_runtime_native_state_can_preserve_mode_label_resolved_matter_history() -> None:
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
    baryon_history = np.array([[1.0, 2.0, 2.0, 3.0], [1.5, 2.5, 2.5, 3.5]], dtype=np.float64)
    cdm_history = np.array([[4.0, 5.0], [4.5, 5.5]], dtype=np.float64)
    projection = project_runtime_native_state(
        layout=layout,
        layout_manifest=ops.layout_metadata,
        photon_T=np.arange(size, dtype=np.float64),
        photon_E=np.arange(size, dtype=np.float64) + 100.0,
        neutrino_tower=np.arange(size, dtype=np.float64) + 200.0,
        source_template=np.asarray(ops.source_template, dtype=np.float64),
        baryon_block=baryon_history[-1],
        cdm_block=cdm_history[-1],
        baryon_blocks_by_mode_label={
            "m0": baryon_history[-1],
            "m+2": 10.0 + baryon_history[-1],
        },
        cdm_blocks_by_mode_label={
            "m0": cdm_history[-1],
            "m+2": 20.0 + cdm_history[-1],
        },
        matter_history_eta=np.array([0.1, 0.2], dtype=np.float64),
        baryon_history_samples=baryon_history,
        cdm_history_samples=cdm_history,
        baryon_history_by_mode_label={
            "m0": baryon_history,
            "m+2": 10.0 + baryon_history,
        },
        cdm_history_by_mode_label={
            "m0": cdm_history,
            "m+2": 20.0 + cdm_history,
        },
    )
    assert set(projection.metadata["matter_history_mode_labels"]) == {"m0", "m+2"}
    assert set(projection.hierarchy_state.matter_block["mode_label_history"]) == {"m0", "m+2"}
    np.testing.assert_allclose(
        np.asarray(
            projection.hierarchy_state.matter_block["mode_label_blocks"]["m+2"]["baryon"],
            dtype=np.float64,
        ),
        10.0 + baryon_history[-1],
    )
    np.testing.assert_allclose(
        np.asarray(
            projection.hierarchy_state.matter_block["mode_label_history"]["m+2"]["cdm"],
            dtype=np.float64,
        ),
        20.0 + cdm_history,
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
    assert set(projection.metadata["b_mode_labels"]) == {"m0", "m+2"}
    assert set(projection.metadata["b_history_mode_labels"]) == {"m0", "m+2"}
    assert projection.state_vector[flatten(layout, "m0", "ph_B", 2, 1)] == pytest.approx(0.25)
    assert np.asarray(projection.hierarchy_state.photon_polarization_block["eta"]).shape == (2,)
    assert np.asarray(projection.hierarchy_state.photon_polarization_block["B_history"]).shape == (2, size)
    assert set(projection.hierarchy_state.photon_polarization_block["mode_label_blocks"]) == {"m0", "m+2"}
    assert set(projection.hierarchy_state.photon_polarization_block["mode_label_history"]) == {"m0", "m+2"}


def test_project_runtime_native_state_can_preserve_mode_label_resolved_b_history() -> None:
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
    b_m0 = np.zeros(size, dtype=np.float64)
    b_m0[6] = 0.1
    b_m2 = np.zeros(size, dtype=np.float64)
    b_m2[8] = 0.3
    history_m0 = np.vstack([np.zeros(size, dtype=np.float64), b_m0])
    history_m2 = np.vstack([np.zeros(size, dtype=np.float64), b_m2])
    projection = project_runtime_native_state(
        layout=layout,
        layout_manifest=ops.layout_metadata,
        photon_T=np.arange(size, dtype=np.float64),
        photon_E=np.arange(size, dtype=np.float64) + 100.0,
        photon_B=b_m0,
        photon_B_blocks_by_mode_label={"m0": b_m0, "m+2": b_m2},
        photon_B_history_eta=np.array([0.1, 0.2], dtype=np.float64),
        photon_B_history_samples=history_m0,
        photon_B_history_by_mode_label={"m0": history_m0, "m+2": history_m2},
        neutrino_tower=np.arange(size, dtype=np.float64) + 200.0,
        source_template=np.asarray(ops.source_template, dtype=np.float64),
    )
    np.testing.assert_allclose(
        np.asarray(projection.hierarchy_state.photon_polarization_block["mode_label_blocks"]["m0"], dtype=np.float64),
        b_m0,
    )
    np.testing.assert_allclose(
        np.asarray(projection.hierarchy_state.photon_polarization_block["mode_label_blocks"]["m+2"], dtype=np.float64),
        b_m2,
    )
    np.testing.assert_allclose(
        np.asarray(projection.hierarchy_state.photon_polarization_block["mode_label_history"]["m+2"], dtype=np.float64),
        history_m2,
    )


def test_project_runtime_native_state_can_preserve_mode_label_resolved_harmonic_blocks() -> None:
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
    t_m0 = np.arange(size, dtype=np.float64)
    t_m2 = 10.0 + np.arange(size, dtype=np.float64)
    e_m0 = 100.0 + np.arange(size, dtype=np.float64)
    e_m2 = 200.0 + np.arange(size, dtype=np.float64)
    nu_m0 = 300.0 + np.arange(size, dtype=np.float64)
    nu_m2 = 400.0 + np.arange(size, dtype=np.float64)
    projection = project_runtime_native_state(
        layout=layout,
        layout_manifest=ops.layout_metadata,
        photon_T=t_m0,
        photon_T_blocks_by_mode_label={"m0": t_m0, "m+2": t_m2},
        photon_E=e_m0,
        photon_E_blocks_by_mode_label={"m0": e_m0, "m+2": e_m2},
        neutrino_tower=nu_m0,
        neutrino_blocks_by_mode_label={"m0": nu_m0, "m+2": nu_m2},
        source_template=np.asarray(ops.source_template, dtype=np.float64),
    )
    assert projection.state_vector[flatten(layout, "m+2", "ph_I", 2, 1)] == pytest.approx(t_m2[7])
    assert projection.state_vector[flatten(layout, "m+2", "ph_E", 2, 1)] == pytest.approx(e_m2[7])
    assert projection.state_vector[flatten(layout, "m+2", "nu_I", 2, 1)] == pytest.approx(nu_m2[7])


# -------------------------------------------------------------------------
# V5 Round-3 audit — FamilyKernelPack + _family_conditioned_kernel_operator
# -------------------------------------------------------------------------
#
# Round 3 introduced a matrix-valued replacement for the Round-2
# _family_conditioned_kernel_law. The kernel operator is NOT wired into
# the residual-joint assembly in this session; these tests pin down the
# Round-3 Q-8.2 / Q-8.5 / Q-8.6(b) matrix values so that a future wiring
# patch cannot regress them silently.


from bass.hierarchy.ver3_layout_protocol import (  # noqa: E402
    FamilyKernelPack,
    _family_conditioned_kernel_law,
    _family_conditioned_kernel_operator,
    _operator_scales,
)


def _kernel_for(family: str, ell_max: int = 4) -> FamilyKernelPack:
    backend = build_backend(get_family_spec(family), truncation={"ell_max": ell_max})
    return _family_conditioned_kernel_operator(backend, ell_max=ell_max)


def test_round3_family_kernel_type_i_is_all_zero_matrices() -> None:
    """Type-I (FLRW) produces zero mu_mode_coupling_* matrices so b_hh ≡ 0
    and the D_2 = 1002.086744 μK² anchor is algebraically preserved."""
    pack = _kernel_for("I")
    zero = np.zeros((3, 3), dtype=np.float64)
    for channel in ("t", "e", "b", "nu"):
        matrix = np.asarray(getattr(pack, f"mu_mode_coupling_{channel}"))
        assert matrix.shape == (3, 3)
        assert np.array_equal(matrix, zero)
    assert np.array_equal(pack.twist_mix_kernel, np.zeros((5, 9, 2, 2)))


def test_round3_family_kernel_type_ii_rank_1_nilpotent() -> None:
    """Type II: N = diag(1, 0, 0), a = 0 → rank-1 nilpotent coupling."""
    pack = _kernel_for("II")
    expected = np.zeros((3, 3), dtype=np.float64)
    expected[0, 0] = 1.0
    assert np.array_equal(pack.mu_mode_coupling_t, expected)
    assert np.linalg.matrix_rank(pack.mu_mode_coupling_t) == 1


def test_round3_family_kernel_type_iii_semisimple_plus_twist() -> None:
    """Type III: N = diag(0, 1, -1) + |a|·P_a with |a| = 1."""
    pack = _kernel_for("III")
    expected = np.array(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]],
        dtype=np.float64,
    )
    assert np.array_equal(pack.mu_mode_coupling_t, expected)


def test_round3_family_kernel_type_v_pure_twist() -> None:
    """Type V: N = 0, a = (1, 0, 0) → rank-1 along twist axis only."""
    pack = _kernel_for("V")
    expected = np.zeros((3, 3), dtype=np.float64)
    expected[0, 0] = 1.0
    assert np.array_equal(pack.mu_mode_coupling_t, expected)
    assert np.linalg.matrix_rank(pack.mu_mode_coupling_t) == 1


def test_round3_family_kernel_type_vii_0_helical_anchor() -> None:
    """Type VII_0: N = diag(0, 1, 1), helical partners carry equal weight."""
    pack = _kernel_for("VII_0")
    expected = np.array(
        [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )
    assert np.array_equal(pack.mu_mode_coupling_t, expected)


def test_round3_family_kernel_type_viii_semisimple_full_rank() -> None:
    """Type VIII: N = diag(-1, 1, 1), full-rank SL(2,R)-type."""
    pack = _kernel_for("VIII")
    expected = np.array(
        [[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        dtype=np.float64,
    )
    assert np.array_equal(pack.mu_mode_coupling_t, expected)
    assert np.linalg.matrix_rank(pack.mu_mode_coupling_t) == 3


def test_round3_family_kernel_channel_matrices_agree_before_sector_similarity() -> None:
    """Per Q-8.6(b): until the v5 §03B storage-basis similarity transform
    S_{e,b,ν} is specified, all four channel matrices share the same
    μ-space content. This test pins that equality so a future
    sector-similarity patch is surfaced explicitly."""
    for family in ("I", "II", "III", "V", "VII_0", "VIII"):
        pack = _kernel_for(family)
        for channel in ("e", "b", "nu"):
            assert np.array_equal(
                pack.mu_mode_coupling_t,
                getattr(pack, f"mu_mode_coupling_{channel}"),
            ), f"channel similarity violated for {family} / {channel}"


def test_round3_family_kernel_scalar_fields_match_q_8_5() -> None:
    """Q-8.5(c): collision_scale = 1.0 universally.
    Q-8.5(a)(b): local_drag_by_mu and mass_by_mu are Type-I-equivalent
    (ones vector) until class-B ζ_R / ζ_M are derived from the v5
    background tilt closure."""
    for family in ("I", "II", "III", "V", "VII_0", "VIII"):
        pack = _kernel_for(family)
        assert pack.collision == 1.0
        assert pack.local_drag_by_mu.shape == (3,)
        assert np.array_equal(pack.local_drag_by_mu, np.ones(3))
        assert np.array_equal(pack.mass_by_mu, np.ones(3))


def test_active_family_law_keeps_thomson_collision_universal() -> None:
    """The active scalar law may still carry family transport surrogates,
    but Thomson opacity must not be multiplied by Bianchi family labels."""
    for family in (
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VI_0",
        "VI_h",
        "VII_0",
        "VII_h",
        "VIII",
        "IX",
    ):
        backend = build_backend(get_family_spec(family), truncation={"ell_max": 2})
        law = _family_conditioned_kernel_law({"branch": "tilted"}, backend)
        assert law["collision_scale"] == 1.0
        assert law["collision_scale_owner"] == "electron_frame_thomson_universal"


def test_active_family_law_does_not_supply_family_baryon_drag_surrogate() -> None:
    for family in ("I", "V", "VII_0", "VIII"):
        backend = build_backend(get_family_spec(family), truncation={"ell_max": 2})
        law = _family_conditioned_kernel_law({"branch": "tilted"}, backend)
        assert law["local_drag_scale"] == 1.0
        assert law["local_drag_scale_owner"] == (
            "runtime_baryon_loading_R_b_or_unity_anchor"
        )


def test_active_family_law_does_not_supply_family_mass_surrogate() -> None:
    for family in ("I", "V", "VII_0", "VIII"):
        backend = build_backend(get_family_spec(family), truncation={"ell_max": 2})
        law = _family_conditioned_kernel_law({"branch": "tilted"}, backend)
        assert law["mass_scale"] == 1.0
        assert law["mass_scale_owner"] == "runtime_shear_over_H_or_unity_anchor"


def test_active_family_law_does_not_supply_family_transport_surrogate() -> None:
    for family in ("I", "V", "VII_0", "VIII"):
        backend = build_backend(get_family_spec(family), truncation={"ell_max": 2})
        law = _family_conditioned_kernel_law({"branch": "tilted"}, backend)
        assert law["transport_scale"] == 1.0
        assert law["transport_scale_owner"] == (
            "runtime_spectral_transport_matrix_or_unity_anchor"
        )


def test_active_family_law_does_not_supply_family_mode_label_surrogate() -> None:
    for family in ("I", "V", "VII_0", "VIII"):
        backend = build_backend(get_family_spec(family), truncation={"ell_max": 2})
        law = _family_conditioned_kernel_law({"branch": "tilted"}, backend)
        assert law["mode_plus_scale"] == 1.0
        assert law["mode_minus_scale"] == 1.0
        assert law["mode_scale_owner"] == "storage_label_neutral_runtime_transport_or_mass"


def test_active_family_law_does_not_supply_source_or_polarization_surrogates() -> None:
    for family in (
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VI_0",
        "VI_h",
        "VII_0",
        "VII_h",
        "VIII",
        "IX",
    ):
        backend = build_backend(get_family_spec(family), truncation={"ell_max": 2})
        law = _family_conditioned_kernel_law({"branch": "tilted"}, backend)
        assert law["polarization_scale"] == 1.0
        assert law["polarization_scale_owner"] == "electron_frame_thomson_projection_universal"
        assert law["source_scale"] == 1.0
        assert law["source_scale_owner"] == "source_tables_visibility_amplitudes"
        assert law["cross_mode_scale"] == 1.0
        assert law["cross_mode_scale_owner"] == "structure_constant_mu_mode_coupling_matrix"


def test_operator_scales_derive_local_drag_from_baryon_loading_R_b() -> None:
    backend = build_backend(get_family_spec("I"), truncation={"ell_max": 2})
    scales = _operator_scales(
        {
            "branch": "orthogonal",
            "opacity_data": {"R_b": 0.5},
            "source_tables": {},
        },
        backend,
    )
    assert scales["local_drag_scale"] == pytest.approx(2.0)
    assert scales["baryon_loading_R_b"] == pytest.approx(0.5)
    assert scales["local_drag_scale_owner"] == "opacity_data.R_b"


def test_operator_scales_can_derive_baryon_loading_from_primitive_densities() -> None:
    backend = build_backend(get_family_spec("I"), truncation={"ell_max": 2})
    scales = _operator_scales(
        {
            "branch": "orthogonal",
            "opacity_data": {},
            "source_tables": {"rho_b": 0.8, "rho_gamma": 1.0},
        },
        backend,
    )
    assert scales["baryon_loading_R_b"] == pytest.approx(0.6)
    assert scales["local_drag_scale"] == pytest.approx(1.0 / 0.6)
    assert scales["local_drag_scale_owner"] == "source_tables.rho_b/rho_gamma"


def test_operator_scales_derive_neutrino_fraction_from_runtime_radiation_densities() -> None:
    backend = build_backend(get_family_spec("I"), truncation={"ell_max": 2})
    scales = _operator_scales(
        {
            "branch": "orthogonal",
            "opacity_data": {},
            "source_tables": {"rho_gamma": 3.0, "rho_nu": 2.0},
        },
        backend,
    )
    assert scales["neutrino_fraction_R_nu"] == pytest.approx(0.4)
    assert scales["neutrino_fraction_owner"] == "source_tables.rho_nu/rho_gamma"
    assert scales["neutrino_anisotropic_stress_scale"] == pytest.approx(0.4)
    assert scales["neutrino_anisotropic_stress_owner"] == "massless_neutrino_quadrupole_metric_source"


def test_reduced_local_rhs_uses_runtime_baryon_loading_not_family_label() -> None:
    backend = build_backend(get_family_spec("I"), truncation={"ell_max": 2})
    layout = build_hierarchy_layout(backend, {"ell_max": 2})
    baryon = {
        mu: np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float64)
        for mu in layout.mode_labels
    }
    cdm = {mu: np.zeros(2, dtype=np.float64) for mu in layout.mode_labels}
    theta_1 = {mu: 0.0 for mu in layout.mode_labels}
    bg_unit = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 2.0},
        "source_tables": {},
    }
    bg_loaded = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 2.0, "R_b": 0.5},
        "source_tables": {},
    }
    unit_rhs, _ = evaluate_reduced_local_rhs(
        layout,
        bg_unit,
        backend,
        baryon_by_mode_label=baryon,
        cdm_by_mode_label=cdm,
        theta_1_by_mode_label=theta_1,
    )
    loaded_rhs, _ = evaluate_reduced_local_rhs(
        layout,
        bg_loaded,
        backend,
        baryon_by_mode_label=baryon,
        cdm_by_mode_label=cdm,
        theta_1_by_mode_label=theta_1,
    )
    assert loaded_rhs["m0"][1] == pytest.approx(2.0 * unit_rhs["m0"][1])


def test_operator_scales_reject_invalid_baryon_loading() -> None:
    backend = build_backend(get_family_spec("I"), truncation={"ell_max": 2})
    with pytest.raises(ValueError, match="R_b"):
        _operator_scales(
            {
                "branch": "orthogonal",
                "opacity_data": {"R_b": 0.0},
                "source_tables": {},
            },
            backend,
        )


def test_operator_scales_cache_tracks_runtime_baryon_loading_changes() -> None:
    backend = build_backend(get_family_spec("I"), truncation={"ell_max": 2})
    bg = {
        "branch": "orthogonal",
        "opacity_data": {"R_b": 1.0},
        "source_tables": {},
    }
    assert _operator_scales(bg, backend)["local_drag_scale"] == pytest.approx(1.0)
    bg["opacity_data"]["R_b"] = 0.25
    assert _operator_scales(bg, backend)["local_drag_scale"] == pytest.approx(4.0)


def test_operator_scales_derive_class_b_local_drag_from_runtime_slip() -> None:
    backend = build_backend(get_family_spec("V"), truncation={"ell_max": 2})
    a_abs = float(np.linalg.norm(np.asarray(backend.family_spec.algebra.a, dtype=np.float64)))
    scales = _operator_scales(
        {
            "branch": "orthogonal",
            "H_local": 2.0,
            "opacity_data": {"R_b": 0.5},
            "baryon_velocity_by_mode_label": {
                "mu_open": 0.8,
                "mu_open+": 0.0,
                "mu_open-": 0.0,
            },
            "theta_1_by_mode_label": {
                "mu_open": 0.1,
                "mu_open+": 0.0,
                "mu_open-": 0.0,
            },
        },
        backend,
    )
    expected_anchor = 1.0 + a_abs * a_abs * ((0.8 - 3.0 * 0.1) / 2.0) ** 2
    np.testing.assert_allclose(
        scales["local_drag_by_mu"],
        np.array([expected_anchor, 1.0, 1.0], dtype=np.float64),
    )
    assert str(scales["local_drag_by_mu_owner"]).startswith("class_b_anchor_slip")
    np.testing.assert_allclose(
        scales["local_drag_slip_by_mu"],
        np.array([0.5, 0.0, 0.0], dtype=np.float64),
    )


def test_reduced_local_rhs_uses_class_b_slip_drag_on_baryon_rows_only() -> None:
    truncation = {"ell_max": 2}
    backend = build_backend(get_family_spec("V"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    a_abs = float(np.linalg.norm(np.asarray(backend.family_spec.algebra.a, dtype=np.float64)))
    baryon = {
        "mu_open": np.array([0.0, 0.8, 0.0, 0.0], dtype=np.float64),
        "mu_open+": np.zeros(4, dtype=np.float64),
        "mu_open-": np.zeros(4, dtype=np.float64),
    }
    cdm = {mu: np.zeros(2, dtype=np.float64) for mu in layout.mode_labels}
    theta_1 = {"mu_open": 0.1, "mu_open+": 0.0, "mu_open-": 0.0}
    bg_unit = {
        "branch": "orthogonal",
        "H_local": 2.0,
        "opacity_data": {"Gamma_T": 1.5, "R_b": 0.5},
        "source_tables": {},
    }
    rhs, _ = evaluate_reduced_local_rhs(
        layout,
        bg_unit,
        backend,
        baryon_by_mode_label=baryon,
        cdm_by_mode_label=cdm,
        theta_1_by_mode_label=theta_1,
    )
    correction = 1.0 + a_abs * a_abs * ((0.8 - 3.0 * 0.1) / 2.0) ** 2
    baryon_base_diag = 1.0 + 0.08 * _operator_scales(bg_unit, backend)["geom_scale"] + 0.03
    expected_drive = -(1.0 / 0.5) * correction * 1.5 * 0.8
    expected_drive += 3.0 * (1.0 / 0.5) * correction * 1.5 * 0.1
    assert rhs["mu_open"][1] == pytest.approx(expected_drive / baryon_base_diag)


def test_reduced_local_affine_operator_accepts_frozen_class_b_slip_drag() -> None:
    truncation = {"ell_max": 2}
    backend = build_backend(get_family_spec("V"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    bg = {
        "branch": "orthogonal",
        "H_local": 2.0,
        "opacity_data": {"Gamma_T": 1.5, "R_b": 0.5},
        "source_tables": {},
    }
    affine = build_reduced_local_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=("mu_open",),
        theta_1_by_mode_label={"mu_open": 0.1},
        baryon_velocity_by_mode_label={"mu_open": 0.8},
    )
    state = np.array([0.0, 0.8, 0.0, 0.0, 0.0, 0.0], dtype=np.float64)
    applied = np.asarray(affine.matrix @ state + affine.bias, dtype=np.float64)
    direct, _ = evaluate_reduced_local_rhs(
        layout,
        bg,
        backend,
        baryon_by_mode_label={"mu_open": state[:4]},
        cdm_by_mode_label={"mu_open": state[4:]},
        theta_1_by_mode_label={"mu_open": 0.1},
    )
    np.testing.assert_allclose(applied[:4], direct["mu_open"])


def test_reduced_joint_affine_operator_freezes_class_b_slip_drag_for_local_block() -> None:
    truncation = {"ell_max": 2}
    backend = build_backend(get_family_spec("V"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    width = (layout.ell_max + 1) ** 2
    dipole_slot = 2
    bg = {
        "branch": "orthogonal",
        "H_local": 2.0,
        "opacity_data": {"Gamma_T": 1.5, "R_b": 0.5},
        "source_tables": {},
    }
    zeros_h = {mu: np.zeros(width, dtype=np.float64) for mu in layout.mode_labels}
    photon_t = {mu: np.zeros(width, dtype=np.float64) for mu in layout.mode_labels}
    photon_t["mu_open"][dipole_slot] = 0.1
    baryon = {"mu_open": np.array([0.0, 0.8, 0.0, 0.0], dtype=np.float64)}
    cdm = {"mu_open": np.zeros(2, dtype=np.float64)}
    affine = build_reduced_joint_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=("mu_open",),
        photon_T_by_mode_label=photon_t,
        photon_E_by_mode_label=zeros_h,
        photon_B_by_mode_label=zeros_h,
        neutrino_by_mode_label=zeros_h,
        baryon_by_mode_label=baryon,
        baryon_velocity_by_mode_label={"mu_open": 0.8},
        theta_1_by_mode_label={"mu_open": 0.1},
    )
    local_state = np.concatenate([baryon["mu_open"], cdm["mu_open"]], dtype=np.float64)
    harmonic_state = np.concatenate(
        [
            photon_t["mu_open"],
            zeros_h["mu_open"],
            zeros_h["mu_open"],
            zeros_h["mu_open"],
        ],
        dtype=np.float64,
    )
    source_state = np.zeros(layout.sector_local_dofs["src"], dtype=np.float64)
    applied = np.asarray(
        affine.matrix @ np.concatenate([local_state, harmonic_state, source_state], dtype=np.float64)
        + affine.bias,
        dtype=np.float64,
    )
    direct_baryon, direct_cdm = evaluate_reduced_local_rhs(
        layout,
        bg,
        backend,
        baryon_by_mode_label=baryon,
        cdm_by_mode_label=cdm,
        theta_1_by_mode_label={"mu_open": 0.1},
    )
    expected_local = np.concatenate([direct_baryon["mu_open"], direct_cdm["mu_open"]], dtype=np.float64)
    np.testing.assert_allclose(applied[: expected_local.size], expected_local)


def test_operator_scales_derive_mass_by_mu_from_runtime_shear_over_hubble() -> None:
    backend = build_backend(get_family_spec("I"), truncation={"ell_max": 2})
    scales = _operator_scales(
        {
            "branch": "orthogonal",
            "H_local": 2.0,
            "sigma_tensor": np.diag([0.2, -0.1, 0.0]),
            "opacity_data": {},
            "source_tables": {},
        },
        backend,
    )
    np.testing.assert_allclose(
        scales["mass_by_mu"],
        np.array([1.1, 0.95, 1.0], dtype=np.float64),
    )
    assert scales["mass_scale"] == 1.0
    assert scales["H_local"] == pytest.approx(2.0)
    assert scales["mass_scale_owner"] == "bg.H_local"


def test_assemble_mass_matrix_uses_shear_over_hubble_mass_by_mu() -> None:
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")}
    backend = build_backend(get_family_spec("I"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    bg_unit = {
        "branch": "orthogonal",
        "H_local": 2.0,
        "sigma_tensor": np.zeros((3, 3), dtype=np.float64),
    }
    bg_shear = {
        "branch": "orthogonal",
        "H_local": 2.0,
        "sigma_tensor": np.diag([0.2, -0.1, 0.0]),
    }
    diag_unit = np.asarray(assemble_mass_matrix(bg_unit, backend, truncation).diagonal())
    diag_shear = np.asarray(assemble_mass_matrix(bg_shear, backend, truncation).diagonal())
    idx_m0 = flatten(layout, "m0", "ph_I", 0, 0)
    idx_mp2 = flatten(layout, "m+2", "ph_I", 0, 0)
    idx_mm2 = flatten(layout, "m-2", "ph_I", 0, 0)
    assert diag_shear[idx_m0] / diag_unit[idx_m0] == pytest.approx(1.1)
    assert diag_shear[idx_mp2] / diag_unit[idx_mp2] == pytest.approx(0.95)
    assert diag_shear[idx_mm2] / diag_unit[idx_mm2] == pytest.approx(1.0)


def test_reduced_harmonic_rhs_uses_runtime_mass_by_mu() -> None:
    truncation = {"ell_max": 2, "mode_labels": ("m0", "m+2", "m-2")}
    backend = build_backend(get_family_spec("I"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    width = (layout.ell_max + 1) ** 2
    zeros = {mu: np.zeros(width, dtype=np.float64) for mu in layout.mode_labels}
    baryon = {mu: np.zeros(4, dtype=np.float64) for mu in layout.mode_labels}
    bg_unit = {
        "branch": "orthogonal",
        "H_local": 2.0,
        "sigma_tensor": np.zeros((3, 3), dtype=np.float64),
        "opacity_data": {"Gamma_T": 0.0},
        "source_tables": {"temperature_visibility_source": 1.0},
    }
    bg_shear = {
        **bg_unit,
        "sigma_tensor": np.diag([0.2, -0.1, 0.0]),
    }
    rhs_unit, _, _, _ = evaluate_reduced_harmonic_rhs(
        layout,
        bg_unit,
        backend,
        photon_T_by_mode_label=zeros,
        photon_E_by_mode_label=zeros,
        photon_B_by_mode_label=zeros,
        neutrino_by_mode_label=zeros,
        baryon_by_mode_label=baryon,
    )
    rhs_shear, _, _, _ = evaluate_reduced_harmonic_rhs(
        layout,
        bg_shear,
        backend,
        photon_T_by_mode_label=zeros,
        photon_E_by_mode_label=zeros,
        photon_B_by_mode_label=zeros,
        neutrino_by_mode_label=zeros,
        baryon_by_mode_label=baryon,
    )
    assert rhs_shear["m0"][0] / rhs_unit["m0"][0] == pytest.approx(1.0 / 1.1)
    assert rhs_shear["m+2"][0] / rhs_unit["m+2"][0] == pytest.approx(1.0 / 0.95)


def test_operator_scales_reject_invalid_mass_by_mu() -> None:
    backend = build_backend(get_family_spec("I"), truncation={"ell_max": 2})
    with pytest.raises(ValueError, match="mass_by_mu"):
        _operator_scales(
            {
                "branch": "orthogonal",
                "H_local": 1.0,
                "sigma_tensor": np.diag([-1.1, 0.0, 0.0]),
            },
            backend,
        )


def test_tilted_mass_by_mu_uses_positive_exponential_map_outside_linear_regime() -> None:
    backend = build_backend(get_family_spec("V"), truncation={"ell_max": 2})
    scales = _operator_scales(
        {
            "branch": "tilted",
            "H_local": 1.0,
            "sigma_tensor": np.diag([-1.1, 0.0, 0.2]),
        },
        backend,
    )
    np.testing.assert_allclose(
        scales["mass_by_mu"],
        np.exp(np.array([-1.1, 0.0, 0.2], dtype=np.float64)),
    )
    assert scales["mass_scale_owner"] == "bg.H_local+tilted_exponential_shear_over_H_positive_map"


def test_operator_scales_derive_transport_scale_from_family_spectral_matrix() -> None:
    backend_v = build_backend(get_family_spec("V"), truncation={"ell_max": 2})
    scales_v = _operator_scales(
        {
            "branch": "orthogonal",
            "k_mag": 2.0,
            "opacity_data": {},
            "source_tables": {},
        },
        backend_v,
    )
    assert scales_v["transport_scale"] == pytest.approx(np.sqrt(5.0))
    np.testing.assert_allclose(
        scales_v["transport_by_mu"],
        np.sqrt(5.0) * np.ones(3, dtype=np.float64),
    )
    assert scales_v["transport_scale_owner"] == "bg.k_mag"

    backend_vii0 = build_backend(get_family_spec("VII_0"), truncation={"ell_max": 2})
    scales_vii0 = _operator_scales(
        {
            "branch": "orthogonal",
            "opacity_data": {"k_mag": 2.0},
            "source_tables": {},
        },
        backend_vii0,
    )
    q_h = np.sqrt(5.0)
    assert scales_vii0["transport_scale"] == pytest.approx((2.0 + 2.0 * q_h) / 3.0)
    np.testing.assert_allclose(
        scales_vii0["transport_by_mu"],
        np.array([2.0, q_h, q_h], dtype=np.float64),
    )
    assert scales_vii0["transport_scale_owner"] == "opacity_data.k_mag"


def test_operator_scales_cache_tracks_runtime_transport_k_changes() -> None:
    backend = build_backend(get_family_spec("V"), truncation={"ell_max": 2})
    bg = {
        "branch": "orthogonal",
        "opacity_data": {"k_mag": 1.0},
        "source_tables": {},
    }
    assert _operator_scales(bg, backend)["transport_scale"] == pytest.approx(np.sqrt(2.0))
    bg["opacity_data"]["k_mag"] = 3.0
    assert _operator_scales(bg, backend)["transport_scale"] == pytest.approx(np.sqrt(10.0))


def test_operator_scales_keep_spectral_transport_out_of_geom_scale() -> None:
    backend = build_backend(get_family_spec("VII_0"), truncation={"ell_max": 2})
    base_bg = {
        "branch": "orthogonal",
        "opacity_data": {},
        "source_tables": {},
    }
    k_bg = {
        "branch": "orthogonal",
        "opacity_data": {"k_mag": 2.0},
        "source_tables": {},
    }
    base = _operator_scales(base_bg, backend)
    with_k = _operator_scales(k_bg, backend)
    assert with_k["geom_scale"] == pytest.approx(base["geom_scale"])
    assert with_k["transport_scale"] == pytest.approx((2.0 + 2.0 * np.sqrt(5.0)) / 3.0)


def test_free_streaming_block_uses_mode_resolved_spectral_transport() -> None:
    truncation = {"ell_max": 2}
    backend = build_backend(get_family_spec("VII_0"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    bg_unit = {"branch": "orthogonal", "opacity_data": {}, "source_tables": {}}
    bg_k = {"branch": "orthogonal", "opacity_data": {"k_mag": 2.0}, "source_tables": {}}
    A_unit = assemble_free_streaming_block(bg_unit, backend, truncation)
    A_k = assemble_free_streaming_block(bg_k, backend, truncation)

    row_anchor = flatten(layout, "mu_hel", "ph_I", 1, 0)
    col_anchor = flatten(layout, "mu_hel", "ph_I", 0, 0)
    row_plus = flatten(layout, "mu_hel+", "ph_I", 1, 0)
    col_plus = flatten(layout, "mu_hel+", "ph_I", 0, 0)

    assert A_k[row_anchor, col_anchor] / A_unit[row_anchor, col_anchor] == pytest.approx(2.0)
    assert A_k[row_plus, col_plus] / A_unit[row_plus, col_plus] == pytest.approx(np.sqrt(5.0))


def test_reduced_harmonic_rhs_uses_mode_resolved_spectral_transport() -> None:
    truncation = {"ell_max": 2}
    backend = build_backend(get_family_spec("VII_0"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    width = (layout.ell_max + 1) ** 2
    photon_t = {mu: np.zeros(width, dtype=np.float64) for mu in layout.mode_labels}
    for values in photon_t.values():
        values[0] = 1.0
    zeros_h = {mu: np.zeros(width, dtype=np.float64) for mu in layout.mode_labels}
    baryon = {mu: np.zeros(4, dtype=np.float64) for mu in layout.mode_labels}
    bg_unit = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 0.0},
        "source_tables": {},
    }
    bg_k = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 0.0, "k_mag": 2.0},
        "source_tables": {},
    }
    rhs_unit, _, _, _ = evaluate_reduced_harmonic_rhs(
        layout,
        bg_unit,
        backend,
        photon_T_by_mode_label=photon_t,
        photon_E_by_mode_label=zeros_h,
        photon_B_by_mode_label=zeros_h,
        neutrino_by_mode_label=zeros_h,
        baryon_by_mode_label=baryon,
    )
    rhs_k, _, _, _ = evaluate_reduced_harmonic_rhs(
        layout,
        bg_k,
        backend,
        photon_T_by_mode_label=photon_t,
        photon_E_by_mode_label=zeros_h,
        photon_B_by_mode_label=zeros_h,
        neutrino_by_mode_label=zeros_h,
        baryon_by_mode_label=baryon,
    )
    dipole_slot = 2
    assert rhs_k["mu_hel"][dipole_slot] / rhs_unit["mu_hel"][dipole_slot] == pytest.approx(2.0)
    assert rhs_k["mu_hel+"][dipole_slot] / rhs_unit["mu_hel+"][dipole_slot] == pytest.approx(np.sqrt(5.0))


def test_source_vector_is_not_rescaled_by_family_label() -> None:
    truncation_v = {"ell_max": 2, "mode_labels": ("mu_open",)}
    truncation_viii = {"ell_max": 2, "mode_labels": ("mu_sl2r",)}
    backend_v = build_backend(get_family_spec("V"), truncation=truncation_v)
    backend_viii = build_backend(get_family_spec("VIII"), truncation=truncation_viii)
    layout_v = build_hierarchy_layout(backend_v, truncation_v)
    layout_viii = build_hierarchy_layout(backend_viii, truncation_viii)
    source_tables = {
        "temperature_visibility_source": 1.2,
        "doppler_source": -0.4,
        "polarization_source": 0.7,
    }
    bg = {
        "branch": "tilted",
        "opacity_data": {},
        "source_tables": source_tables,
    }

    source_v = assemble_source_vector(bg, backend_v, truncation_v, source_tables)
    source_viii = assemble_source_vector(bg, backend_viii, truncation_viii, source_tables)

    assert source_v[flatten(layout_v, "mu_open", "ph_I", 0, 0)] == pytest.approx(
        source_viii[flatten(layout_viii, "mu_sl2r", "ph_I", 0, 0)]
    )
    assert source_v[flatten(layout_v, "mu_open", "ph_I", 1, 0)] == pytest.approx(
        source_viii[flatten(layout_viii, "mu_sl2r", "ph_I", 1, 0)]
    )
    assert source_v[flatten(layout_v, "mu_open", "ph_E", 2, 0)] == pytest.approx(
        source_viii[flatten(layout_viii, "mu_sl2r", "ph_E", 2, 0)]
    )


def test_mixing_block_uses_neutrino_quadrupole_anisotropic_stress_source() -> None:
    truncation = {"ell_max": 2, "mode_labels": ("m0",)}
    backend = build_backend(get_family_spec("I"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    bg = {
        "branch": "orthogonal",
        "opacity_data": {},
        "source_tables": {"R_nu": 0.4},
    }
    mixing = assemble_mixing_block(bg, backend, truncation)
    row = flatten(layout, "m0", "ph_I", 2, 0)
    col = flatten(layout, "m0", "nu_I", 2, 0)
    pstf_weight = np.sqrt(4.0) / 5.0
    assert mixing[row, col] == pytest.approx(0.4 * pstf_weight)


def test_neutrino_anisotropic_stress_source_is_quadrupole_only() -> None:
    truncation = {"ell_max": 3, "mode_labels": ("m0",)}
    backend = build_backend(get_family_spec("I"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    bg = {
        "branch": "orthogonal",
        "opacity_data": {},
        "source_tables": {"R_nu": 0.4},
    }
    mixing = assemble_mixing_block(bg, backend, truncation)
    row2 = flatten(layout, "m0", "ph_I", 2, 1)
    col2 = flatten(layout, "m0", "nu_I", 2, 1)
    row3 = flatten(layout, "m0", "ph_I", 3, 1)
    col3 = flatten(layout, "m0", "nu_I", 3, 1)
    assert mixing[row2, col2] != 0.0
    assert mixing[row3, col3] == pytest.approx(0.0, abs=1.0e-15)


def test_reduced_harmonic_affine_operator_matches_direct_with_neutrino_stress_source() -> None:
    truncation = {"ell_max": 2, "mode_labels": ("m0",)}
    backend = build_backend(get_family_spec("I"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    bg = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 0.0},
        "source_tables": {"R_nu": 0.4},
    }
    width = (layout.ell_max + 1) ** 2
    mu = "m0"
    zeros = {mu: np.zeros(width, dtype=np.float64)}
    neutrino = {mu: np.zeros(width, dtype=np.float64)}
    quad_slot = 6
    neutrino[mu][quad_slot] = 1.0
    baryon = {mu: np.zeros(4, dtype=np.float64)}
    source = {mu: np.zeros(3, dtype=np.float64)}
    direct_t, direct_e, direct_b, direct_nu = evaluate_reduced_harmonic_rhs(
        layout,
        bg,
        backend,
        photon_T_by_mode_label=zeros,
        photon_E_by_mode_label=zeros,
        photon_B_by_mode_label=zeros,
        neutrino_by_mode_label=neutrino,
        baryon_by_mode_label=baryon,
        source_by_mode_label=source,
    )
    affine = build_reduced_harmonic_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=(mu,),
        photon_T_by_mode_label=zeros,
        photon_E_by_mode_label=zeros,
        photon_B_by_mode_label=zeros,
        neutrino_by_mode_label=neutrino,
        baryon_by_mode_label=baryon,
        source_by_mode_label=source,
    )
    state = np.concatenate([zeros[mu], zeros[mu], zeros[mu], neutrino[mu]], dtype=np.float64)
    direct = np.concatenate([direct_t[mu], direct_e[mu], direct_b[mu], direct_nu[mu]], dtype=np.float64)
    applied = np.asarray(affine.matrix @ state + affine.bias, dtype=np.float64)
    assert direct_t[mu][quad_slot] > 0.0
    assert np.linalg.norm(direct_e[mu]) == pytest.approx(0.0, abs=1e-15)
    assert np.linalg.norm(direct_b[mu]) == pytest.approx(0.0, abs=1e-15)
    np.testing.assert_allclose(applied, direct)


def test_reduced_harmonic_affine_operator_matches_direct_with_mode_transport() -> None:
    truncation = {"ell_max": 2}
    backend = build_backend(get_family_spec("VII_0"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    width = (layout.ell_max + 1) ** 2
    bg = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 0.0, "k_mag": 2.0},
        "source_tables": {},
    }
    photon_t = {
        str(mu): np.linspace(0.1 + 0.05 * i, 0.9 + 0.05 * i, width, dtype=np.float64)
        for i, mu in enumerate(layout.mode_labels)
    }
    photon_e = {
        str(mu): np.linspace(-0.2 + 0.03 * i, 0.4 + 0.03 * i, width, dtype=np.float64)
        for i, mu in enumerate(layout.mode_labels)
    }
    photon_b = {
        str(mu): np.linspace(0.3 - 0.02 * i, -0.1 - 0.02 * i, width, dtype=np.float64)
        for i, mu in enumerate(layout.mode_labels)
    }
    neutrino = {
        str(mu): np.linspace(0.15 + 0.04 * i, 0.45 + 0.04 * i, width, dtype=np.float64)
        for i, mu in enumerate(layout.mode_labels)
    }
    baryon = {str(mu): np.zeros(4, dtype=np.float64) for mu in layout.mode_labels}
    direct_t, direct_e, direct_b, direct_nu = evaluate_reduced_harmonic_rhs(
        layout,
        bg,
        backend,
        photon_T_by_mode_label=photon_t,
        photon_E_by_mode_label=photon_e,
        photon_B_by_mode_label=photon_b,
        neutrino_by_mode_label=neutrino,
        baryon_by_mode_label=baryon,
    )
    affine = build_reduced_harmonic_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=tuple(str(mu) for mu in layout.mode_labels),
        photon_T_by_mode_label=photon_t,
        photon_E_by_mode_label=photon_e,
        photon_B_by_mode_label=photon_b,
        neutrino_by_mode_label=neutrino,
        baryon_by_mode_label=baryon,
    )
    residual_state = np.concatenate(
        [
            part
            for mu in layout.mode_labels
            for part in (
                photon_t[str(mu)],
                photon_e[str(mu)],
                photon_b[str(mu)],
                neutrino[str(mu)],
            )
        ],
        dtype=np.float64,
    )
    direct = np.concatenate(
        [
            part
            for mu in layout.mode_labels
            for part in (
                direct_t[str(mu)],
                direct_e[str(mu)],
                direct_b[str(mu)],
                direct_nu[str(mu)],
            )
        ],
        dtype=np.float64,
    )
    applied = np.asarray(affine.matrix @ residual_state + affine.bias, dtype=np.float64)
    np.testing.assert_allclose(applied, direct)


def test_operator_scales_reject_invalid_transport_k() -> None:
    backend = build_backend(get_family_spec("I"), truncation={"ell_max": 2})
    with pytest.raises(ValueError, match="k_mag"):
        _operator_scales(
            {
                "branch": "orthogonal",
                "k_mag": 0.0,
            },
            backend,
        )


def test_round3_family_kernel_transport_is_identity_placeholder() -> None:
    """Q-8.3: transport matrix is left as identity; the
    spectral-parameter-dependent factor (|k| / sqrt(k²+1) / sqrt(s²+¼))
    must be applied by the future wiring patch. This test pins the
    placeholder shape."""
    for family in ("I", "II", "III", "V", "VII_0", "VIII"):
        pack = _kernel_for(family)
        assert np.array_equal(pack.transport, np.eye(3))


def test_round3_family_kernel_twist_mix_kernel_shape() -> None:
    """Q-8.6(a): twist_mix_kernel shape is (ell_max+1, 2*ell_max+1, 2, 2).
    Entries are zero (Wigner-3j evaluation deferred to the wiring
    session); class-A families get the exact zero kernel."""
    for ell_max in (2, 4, 8):
        for family in ("I", "II", "VII_0", "VIII"):
            pack = _kernel_for(family, ell_max=ell_max)
            assert pack.twist_mix_kernel.shape == (
                ell_max + 1,
                2 * ell_max + 1,
                2,
                2,
            )
            assert np.all(pack.twist_mix_kernel == 0.0)


def test_round3_family_kernel_pack_is_frozen_dataclass() -> None:
    """FamilyKernelPack is immutable so a downstream caller cannot
    accidentally mutate the matrices."""
    pack = _kernel_for("II")
    with pytest.raises(Exception):  # frozen dataclass raises FrozenInstanceError
        pack.collision = 2.0  # type: ignore[misc]


# -------------------------------------------------------------------------
# V5 Round-4 audit — Wigner-3j twist_mix_kernel + VII₀ transport + Π projector
# -------------------------------------------------------------------------
#
# Round 4 closed the substantive placeholders in Round 3:
#   Q-10 → _build_transport_matrix with VII₀ helical gap
#   Q-13 → _build_twist_mix_kernel_unit (sympy-based Wigner-3j evaluator)
#   Q-15 → _FAMILY_KERNEL_PI_PERMUTATION per-family axis table
# These tests pin the numerical values so a future wiring patch cannot
# silently regress them.


from bass.hierarchy.ver3_layout_protocol import (  # noqa: E402
    _FAMILY_KERNEL_PI_PERMUTATION,
    _build_transport_matrix,
    _build_twist_mix_kernel_unit,
)


def test_round4_twist_mix_kernel_class_b_non_zero() -> None:
    """Q-13: class-B families (III, V) carry a non-zero Wigner-3j
    twist_mix_kernel under canonical |a|=1 normalization. Class-A
    families remain identically zero."""
    for family in ("III", "V"):
        pack = _kernel_for(family, ell_max=4)
        assert np.any(pack.twist_mix_kernel != 0.0), (
            f"twist_mix_kernel should be non-zero for class-B family {family}"
        )
    for family in ("I", "II", "VII_0", "VIII"):
        pack = _kernel_for(family, ell_max=4)
        assert np.all(pack.twist_mix_kernel == 0.0), (
            f"twist_mix_kernel should be zero for class-A/FLRW family {family}"
        )


def test_round4_twist_mix_kernel_sanity_ell_2_m_0() -> None:
    """Q-13 sanity: K[ell=2, m=0, Δℓ=+1, Δm=-1] = +1/sqrt(21) · |a|.
    Verified against the Round-4 auditor's Condon-Shortley derivation."""
    ell_max = 4
    K = _build_twist_mix_kernel_unit(ell_max)
    # m_offset for m=0: 0 + ell_max = 4
    # delta_ell_index = 1 → Δℓ = +1
    # delta_m_index = 0 → Δm = -1
    value = K[2, ell_max + 0, 1, 0]
    expected = +1.0 / np.sqrt(21.0)
    assert value == pytest.approx(expected, rel=1e-12), (
        f"expected +1/sqrt(21) = {expected}, got {value}"
    )
    # Partner sanity: K[2, m=0, Δℓ=+1, Δm=+1] = -1/sqrt(21)
    assert K[2, ell_max + 0, 1, 1] == pytest.approx(-1.0 / np.sqrt(21.0), rel=1e-12)


def test_round4_twist_mix_kernel_shape_independent_of_a_abs() -> None:
    """Q-13: the kernel's sympy cache is keyed on ell_max only; the
    physical |a| multiplier is applied by _family_conditioned_kernel_operator.
    Class-B pack values should equal |a|=1 · unit kernel."""
    K_unit = _build_twist_mix_kernel_unit(4)
    pack_iii = _kernel_for("III", ell_max=4)
    pack_v = _kernel_for("V", ell_max=4)
    # class-B |a|=1 canonical ⇒ pack kernel == unit kernel
    assert np.allclose(pack_iii.twist_mix_kernel, K_unit, atol=1e-14)
    assert np.allclose(pack_v.twist_mix_kernel, K_unit, atol=1e-14)


def test_round4_twist_mix_kernel_spin_2_selection_rule() -> None:
    """Q-13: only ℓ ≥ 2 → ℓ' ≥ 2 entries are non-zero (spin-2 selection
    rule: wigner_3j(ℓ,1,ℓ';-2,0,2) vanishes for ℓ<2 or ℓ'<2)."""
    K = _build_twist_mix_kernel_unit(4)
    for ell in (0, 1):
        assert np.all(K[ell, :, :, :] == 0.0), f"ell={ell} must vanish (spin-2 rule)"
    # ell=2 → ell'=1 (Δℓ=-1 at delta_ell_index=0) must also vanish (ℓ'<2)
    assert np.all(K[2, :, 0, :] == 0.0), "ell=2, Δℓ=-1 → ell'=1 must vanish"


def test_round4_twist_kernel_is_wired_into_class_b_mixing_block() -> None:
    """Class-B twist transport uses Wigner Δℓ=±1, Δm=±1 E/B edges.

    This rejects the previous same-slot scalar E/B shortcut and the
    unphysical T→B transport shortcut.
    """

    truncation = {"ell_max": 3, "mode_labels": ("mu_open",)}
    backend = build_backend(get_family_spec("V"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    bg = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 0.0},
        "sigma_tensor": np.zeros((3, 3), dtype=np.float64),
        "source_tables": {},
    }

    mixing = np.asarray(assemble_mixing_block(bg, backend, truncation).todense(), dtype=np.float64)
    amplitude = float(np.linalg.norm(backend.family_spec.algebra.a))
    expected = amplitude / np.sqrt(21.0)

    e_target = flatten(layout, "mu_open", "ph_E", 3, -1)
    b_target = flatten(layout, "mu_open", "ph_B", 3, -1)
    e_source = flatten(layout, "mu_open", "ph_E", 2, 0)
    b_source = flatten(layout, "mu_open", "ph_B", 2, 0)
    t_source = flatten(layout, "mu_open", "ph_I", 2, 0)
    e_same = flatten(layout, "mu_open", "ph_E", 2, 0)
    b_same = flatten(layout, "mu_open", "ph_B", 2, 0)

    assert mixing[e_target, b_source] == pytest.approx(expected, rel=1e-12)
    assert mixing[b_target, e_source] == pytest.approx(-expected, rel=1e-12)
    assert mixing[e_same, b_same] == pytest.approx(0.0, abs=1e-15)
    assert mixing[b_same, e_same] == pytest.approx(0.0, abs=1e-15)
    assert mixing[b_target, t_source] == pytest.approx(0.0, abs=1e-15)


def test_reduced_harmonic_affine_operator_matches_direct_with_class_b_twist_kernel() -> None:
    truncation = {"ell_max": 3, "mode_labels": ("mu_open",)}
    backend = build_backend(get_family_spec("V"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    bg = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 0.0},
        "sigma_tensor": np.zeros((3, 3), dtype=np.float64),
        "source_tables": {},
    }
    width = (layout.ell_max + 1) ** 2
    mu = "mu_open"
    photon_t = {mu: np.linspace(0.1, 0.7, width, dtype=np.float64)}
    photon_e = {mu: np.linspace(-0.4, 0.6, width, dtype=np.float64)}
    photon_b = {mu: np.linspace(0.8, -0.2, width, dtype=np.float64)}
    neutrino = {mu: np.linspace(0.3, -0.5, width, dtype=np.float64)}
    baryon = {mu: np.zeros(4, dtype=np.float64)}
    source = {mu: np.zeros(3, dtype=np.float64)}

    direct_t, direct_e, direct_b, direct_nu = evaluate_reduced_harmonic_rhs(
        layout,
        bg,
        backend,
        photon_T_by_mode_label=photon_t,
        photon_E_by_mode_label=photon_e,
        photon_B_by_mode_label=photon_b,
        neutrino_by_mode_label=neutrino,
        baryon_by_mode_label=baryon,
        source_by_mode_label=source,
    )
    affine = build_reduced_harmonic_affine_operator(
        layout,
        bg,
        backend,
        residual_mode_labels=(mu,),
        photon_T_by_mode_label=photon_t,
        photon_E_by_mode_label=photon_e,
        photon_B_by_mode_label=photon_b,
        neutrino_by_mode_label=neutrino,
        baryon_by_mode_label=baryon,
        source_by_mode_label=source,
    )
    state = np.concatenate([photon_t[mu], photon_e[mu], photon_b[mu], neutrino[mu]], dtype=np.float64)
    direct = np.concatenate([direct_t[mu], direct_e[mu], direct_b[mu], direct_nu[mu]], dtype=np.float64)
    applied = np.asarray(affine.matrix @ state + affine.bias, dtype=np.float64)
    np.testing.assert_allclose(applied, direct)


def test_exact_thomson_polarization_source_does_not_directly_source_b_modes() -> None:
    truncation = {"ell_max": 3, "mode_labels": ("mu_open",)}
    backend = build_backend(get_family_spec("V"), truncation=truncation)
    layout = build_hierarchy_layout(backend, truncation)
    bg = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 0.0},
        "sigma_tensor": np.zeros((3, 3), dtype=np.float64),
        "source_tables": {"polarization_source": 1.0},
    }
    width = (layout.ell_max + 1) ** 2
    mu = "mu_open"
    zero_h = {mu: np.zeros(width, dtype=np.float64)}
    zero_baryon = {mu: np.zeros(4, dtype=np.float64)}
    zero_source = {mu: np.zeros(3, dtype=np.float64)}

    source_vector = assemble_source_vector(bg, backend, truncation, bg["source_tables"])
    assert source_vector[flatten(layout, mu, "ph_E", 2, 0)] != 0.0
    assert source_vector[flatten(layout, mu, "ph_B", 2, 0)] == pytest.approx(0.0, abs=1e-15)

    _, _, direct_b, _ = evaluate_reduced_harmonic_rhs(
        layout,
        bg,
        backend,
        photon_T_by_mode_label=zero_h,
        photon_E_by_mode_label=zero_h,
        photon_B_by_mode_label=zero_h,
        neutrino_by_mode_label=zero_h,
        baryon_by_mode_label=zero_baryon,
        source_by_mode_label=zero_source,
    )
    assert np.linalg.norm(direct_b[mu]) == pytest.approx(0.0, abs=1e-15)


def test_round4_transport_VII0_helical_gap() -> None:
    """Q-10: Type VII₀ transport matrix is diag(|k|, sqrt(k²+h),
    sqrt(k²+h)) with h=1 canonical helical eigenvalue."""
    for k in (0.5, 1.0, 2.0, 5.0, 10.0):
        T = _build_transport_matrix("VII_0", k)
        assert T.shape == (3, 3)
        assert T[0, 0] == pytest.approx(k, rel=1e-12)
        q_h = np.sqrt(k * k + 1.0)
        assert T[1, 1] == pytest.approx(q_h, rel=1e-12)
        assert T[2, 2] == pytest.approx(q_h, rel=1e-12)
        # Off-diagonal entries are strictly zero (diagonal matrix)
        assert T[0, 1] == 0.0 and T[1, 0] == 0.0


def test_round4_transport_VII0_FLRW_limit() -> None:
    """Q-10.4: when helical_eigenvalue → 0, VII₀ transport reduces to
    |k|·I_3 (isotropic FLRW), preserving the D_2 anchor."""
    T = _build_transport_matrix("VII_0", 3.0, helical_eigenvalue=0.0)
    expected = 3.0 * np.eye(3)
    assert np.allclose(T, expected, atol=1e-14)


def test_round4_transport_per_family_tier_a() -> None:
    """Q-10 + v5 §03B spectral table: Type II = |k|·I, Type III = I,
    Type V = sqrt(k²+1)·I, Type VIII = sqrt(k²+¼)·I."""
    k = 2.0
    assert np.allclose(_build_transport_matrix("II", k), k * np.eye(3))
    assert np.allclose(_build_transport_matrix("III", k), np.eye(3))
    assert np.allclose(
        _build_transport_matrix("V", k),
        np.sqrt(k * k + 1.0) * np.eye(3),
    )
    assert np.allclose(
        _build_transport_matrix("VIII", k),
        np.sqrt(k * k + 0.25) * np.eye(3),
    )


def test_round4_pi_permutation_VII0_produces_canonical_signature() -> None:
    """Q-15.2: for Type VII₀, Π · diag(n_code) · Π^T must produce the
    Round-3 canonical N = diag(0, 1, 1). Since n_code for VII₀ is
    diag(1, 0, 1), the required Π swaps axes 0 ↔ 1."""
    pi = np.asarray(_FAMILY_KERNEL_PI_PERMUTATION["VII_0"], dtype=np.float64)
    # canonical VII₀ eigenvalues in code: diag(n_1, n_2, n_3) = (1, 0, 1)
    n_code = np.diag([1.0, 0.0, 1.0])
    N_canonical = pi @ n_code @ pi.T
    expected = np.diag([0.0, 1.0, 1.0])
    assert np.array_equal(N_canonical, expected), (
        f"Π·diag(1,0,1)·Π^T should give canonical diag(0,1,1); got {N_canonical}"
    )


def test_round4_pi_permutation_identity_families() -> None:
    """Q-15: Π is identity for Types I, II, III, V, VIII (only VII₀
    needs a non-trivial permutation in the Tier-A set)."""
    identity = np.eye(3)
    for family in ("I", "II", "III", "V", "VIII"):
        pi = np.asarray(_FAMILY_KERNEL_PI_PERMUTATION[family], dtype=np.float64)
        assert np.array_equal(pi, identity), (
            f"Π_{family} should be identity per Round-4 Q-15; got {pi}"
        )


def test_round4_pi_permutation_is_orthogonal() -> None:
    """Π is a permutation matrix: Π · Π^T = I_3 for all Tier-A families."""
    for family in ("I", "II", "III", "V", "VII_0", "VIII"):
        pi = np.asarray(_FAMILY_KERNEL_PI_PERMUTATION[family], dtype=np.float64)
        assert np.allclose(pi @ pi.T, np.eye(3), atol=1e-14), (
            f"Π_{family} must be orthogonal"
        )
