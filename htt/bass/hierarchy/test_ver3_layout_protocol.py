from __future__ import annotations

import numpy as np
import pytest

from bass.background import get_family_spec
from bass.hierarchy import (
    SECTOR_ORDER,
    assemble_explicit_block,
    assemble_implicit_block,
    assemble_mass_matrix,
    assemble_source_vector,
    build_hierarchy_layout,
    flatten,
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
    A_exp = assemble_explicit_block({}, backend, truncation)
    A_imp = assemble_implicit_block({}, backend, truncation, {"Gamma_T": 4.0})
    assert A_exp.shape == (layout.size, layout.size)
    assert A_imp.shape == (layout.size, layout.size)
    assert A_exp.nnz > 0
    assert A_imp.nnz > 0


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
