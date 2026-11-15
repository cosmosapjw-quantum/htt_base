"""Acceptance tests 1 & 7 for R49 GBI-01 convention bridge and Class-B boundaries."""
from __future__ import annotations

import numpy as np
import pytest

from bass.background import bianchi_types as bt, geometry as g
from bass.background.convention_bridge import (
    ALL_TWELVE_FAMILIES,
    PC_TO_VER2_IMPROPER_PERMUTATION,
    PC_TO_VER2_PROPER_ROTATION,
    action_equivalence_for_family,
    build_structure_tensor_with_sign,
    exact_momentum_divergence,
    exact_spatial_ricci_from_compact,
    structure_constants_to_triple,
    structure_constants_to_ver2_algebra,
    transform_structure_pair,
    ver2_algebra_to_structure_constants,
    verify_all_families_convention_bridge,
    verify_convention_bridge_family,
)


def test_acceptance_1_all_11_bianchi_plus_flrw_dual_route_and_o3_frames() -> None:
    """Acceptance Test 1: all 12 types pass Jacobi, dual-route Ricci, and O(3) frame roundtrip."""
    res = verify_all_families_convention_bridge()
    assert res["all_passed"] is True
    for fam in ALL_TWELVE_FAMILIES:
        rep = res["reports"][fam]
        assert rep["passed"] is True
        assert rep["jacobi_residual"] < 1.0e-14
        assert rep["dual_route_ricci_error_ver2"] < 1.0e-14
        assert rep["dual_route_ricci_error_random_so3"] < 1.0e-14
        assert rep["dual_route_ricci_error_improper_o3"] < 1.0e-14
        assert rep["momentum_divergence_identity_error"] < 1.0e-14
        assert rep["lie_bracket_roundtrip_error"] < 1.0e-14
        assert rep["pc_vs_ver2_proper_ricci_diff_after_rotation"] < 1.0e-14


def test_improper_permutation_carries_det_minus_one_parity() -> None:
    """Swapping two axes (det=-1) transforms n -> -P n P^T so Lie bracket C stays invariant."""
    sc = bt.get_type("VII_h")
    triple_pc = structure_constants_to_triple(sc, target_frame="pontzen_challinor", a_sign_out=1)
    triple_imp = structure_constants_to_triple(sc, target_frame="ver2_improper", a_sign_out=1)
    P = PC_TO_VER2_IMPROPER_PERMUTATION
    assert np.isclose(np.linalg.det(P), -1.0)
    # Check exact pushforward C'^k_{ij} = P_{kc} P_{ia} P_{jb} C^c_{ab}
    C_pc = triple_pc.structure_tensor()
    C_imp = triple_imp.structure_tensor()
    C_push = np.einsum("kc,ia,jb,cab->kij", P, P, P, C_pc)
    assert np.allclose(C_imp, C_push, atol=1.0e-15)

    # Check opposite a_sign = -1 (PC species_tilt sign) matches exact Lie bracket when transformed
    a_pc = triple_pc.a
    n_pc = triple_pc.n
    a_flip, n_flip, det_m = transform_structure_pair(
        a_pc, n_pc, PC_TO_VER2_PROPER_ROTATION, a_sign_in=1, a_sign_out=-1
    )
    assert det_m == 1.0
    C_flip = build_structure_tensor_with_sign(a_flip, n_flip, a_sign=-1)
    R = PC_TO_VER2_PROPER_ROTATION
    C_rot = np.einsum("kc,ia,jb,cab->kij", R, R, R, C_pc)
    assert np.allclose(C_flip, C_rot, atol=1.0e-15)


def test_acceptance_7_class_b_special_h_boundaries_and_class_b_ricci_fix() -> None:
    """Acceptance Test 7: h=-1 (III <-> VI_-1) and h=-1/9 regularized + Class-B Ricci exact."""
    # Type III and VI_h(h=-1) coincide smoothly without ValueError or ZeroDivisionError.
    rep_iii = verify_convention_bridge_family("III")
    rep_m1 = verify_convention_bridge_family("VI_h", h=-1.0)
    assert rep_iii.passed and rep_m1.passed
    assert np.isclose(rep_iii.h_parameter, -1.0)
    assert np.isclose(rep_m1.h_parameter, -1.0)
    assert rep_iii.special_locus == "h_equals_minus_1_Type_III_equivalent"
    assert rep_m1.special_locus == "h_equals_minus_1_Type_III_equivalent"

    # Type IV and V have n2*n3 == 0: h_parameter is None without division by zero.
    rep_iv = verify_convention_bridge_family("IV")
    rep_v = verify_convention_bridge_family("V")
    assert rep_iv.passed and rep_iv.h_parameter is None
    assert rep_v.passed and rep_v.h_parameter is None

    # Exceptional h = -1/9 locus in VI_h runs smoothly and satisfies dual-route Ricci & Codazzi.
    rep_m19 = verify_convention_bridge_family("VI_h", h=-1.0 / 9.0)
    assert rep_m19.passed
    assert np.isclose(rep_m19.h_parameter, -1.0 / 9.0)
    assert rep_m19.special_locus == "h_equals_minus_one_ninth_exceptional_VI_h"

    # Legacy geometry.spatial_ricci_from_compact_formula missed Class-B off-diagonal a x n term;
    # exact_spatial_ricci_from_compact fixes it to machine zero for III, IV, VI_h, VII_h.
    for class_b_fam in ("III", "IV", "VI_h", "VII_h"):
        alg = bt.build_bianchi_algebra(class_b_fam)
        geom = g.build_geometry(alg)
        assert geom.dual_route_curvature_residual_norm > 1.0e-6
        R_exact, S_exact, pstf_exact = exact_spatial_ricci_from_compact(alg.a, alg.n, a_sign=1)
        assert np.max(np.abs(geom.ricci_tensor - R_exact)) < 1.0e-15
        assert abs(geom.ricci_scalar - S_exact) < 1.0e-15
        assert np.max(np.abs(geom.ricci_pstf - pstf_exact)) < 1.0e-15


def test_action_equivalence_metadata_and_roundtrip() -> None:
    """I ~ VII_0 (flat k=0) and V ~ VII_h (open k<0) share equivalence sets cleanly."""
    assert action_equivalence_for_family("I").equivalence_id == "FLAT_K0_FLRW_LIMIT"
    assert action_equivalence_for_family("VII_0").equivalence_id == "FLAT_K0_FLRW_LIMIT"
    assert action_equivalence_for_family("V").equivalence_id == "OPEN_KNEG_FLRW_LIMIT"
    assert action_equivalence_for_family("VII_h").equivalence_id == "OPEN_KNEG_FLRW_LIMIT"
    assert action_equivalence_for_family("III").equivalence_id == "TYPE_III_VI_MINUS_ONE"

    for fam in bt.ALL_BIANCHI_TYPES:
        sc = bt.get_type(fam)
        alg = structure_constants_to_ver2_algebra(sc, use_proper_rotation=True)
        sc_back = ver2_algebra_to_structure_constants(alg, use_proper_rotation=True)
        assert sc_back.label == sc.label
        assert np.isclose(sc_back.n1, sc.n1)
        assert np.isclose(sc_back.n2, sc.n2)
        assert np.isclose(sc_back.n3, sc.n3)
        assert np.isclose(sc_back.a_twist, sc.a_twist)
