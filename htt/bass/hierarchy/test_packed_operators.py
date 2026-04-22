from __future__ import annotations

import numpy as np

from bass.hierarchy.contractions import pstf_pack, pstf_unpack
from bass.hierarchy.packed_operators import (
    apply_T1_expansion_packed,
    apply_T4_accel_divergence_packed,
    apply_T5_accel_gradient_packed,
    apply_T6_vorticity_packed,
    apply_T7_shear_up_packed,
    apply_T8_shear_same_packed,
    apply_T9_shear_down_packed,
)
from bass.hierarchy.terms import (
    T1_expansion,
    T4_accel_divergence,
    T5_accel_gradient,
    T6_vorticity,
    T7_shear_up,
    T8_shear_same,
    T9_shear_down,
)


def _rng():
    return np.random.default_rng(20260422)


def _rank2_stf(rng: np.random.Generator) -> np.ndarray:
    return np.asarray(pstf_unpack(rng.normal(size=5), 2), dtype=np.float64)


def test_t1_expansion_packed_matches_full_term() -> None:
    rng = _rng()
    ell = 4
    components = rng.normal(size=2 * ell + 1)
    ricci = _rank2_stf(rng)
    Theta = 1.7

    packed = apply_T1_expansion_packed(
        ell,
        components,
        Theta,
        aniso_ricci_tensor=ricci,
    )
    expected = pstf_pack(T1_expansion(ell, pstf_unpack(components, ell), Theta, aniso_ricci_tensor=ricci))
    assert np.allclose(packed, expected, rtol=0.0, atol=1.0e-12)


def test_rank1_parametric_packed_terms_match_full_terms() -> None:
    rng = _rng()

    ell = 3
    prev = rng.normal(size=2 * (ell - 1) + 1)
    current = rng.normal(size=2 * ell + 1)
    nxt = rng.normal(size=2 * (ell + 1) + 1)
    vector = rng.normal(size=3)

    packed_t4 = apply_T4_accel_divergence_packed(ell, nxt, vector)
    expected_t4 = pstf_pack(T4_accel_divergence(ell, pstf_unpack(nxt, ell + 1), vector))
    assert np.allclose(packed_t4, expected_t4, rtol=0.0, atol=1.0e-12)

    packed_t5 = apply_T5_accel_gradient_packed(ell, prev, vector)
    expected_t5 = pstf_pack(T5_accel_gradient(ell, pstf_unpack(prev, ell - 1), vector))
    assert np.allclose(packed_t5, expected_t5, rtol=0.0, atol=1.0e-12)

    packed_t6 = apply_T6_vorticity_packed(ell, current, vector)
    expected_t6 = pstf_pack(T6_vorticity(ell, pstf_unpack(current, ell), vector))
    assert np.allclose(packed_t6, expected_t6, rtol=0.0, atol=1.0e-12)


def test_rank2_parametric_packed_terms_match_full_terms() -> None:
    rng = _rng()

    ell = 4
    prev_prev = rng.normal(size=2 * (ell - 2) + 1)
    current = rng.normal(size=2 * ell + 1)
    nxt_nxt = rng.normal(size=2 * (ell + 2) + 1)
    sigma = _rank2_stf(rng)

    packed_t7 = apply_T7_shear_up_packed(ell, nxt_nxt, sigma)
    expected_t7 = pstf_pack(T7_shear_up(ell, pstf_unpack(nxt_nxt, ell + 2), sigma))
    assert np.allclose(packed_t7, expected_t7, rtol=0.0, atol=1.0e-11)

    packed_t8 = apply_T8_shear_same_packed(ell, current, sigma)
    expected_t8 = pstf_pack(T8_shear_same(ell, pstf_unpack(current, ell), sigma))
    assert np.allclose(packed_t8, expected_t8, rtol=0.0, atol=1.0e-11)

    packed_t9 = apply_T9_shear_down_packed(ell, prev_prev, sigma)
    expected_t9 = pstf_pack(T9_shear_down(ell, pstf_unpack(prev_prev, ell - 2), sigma))
    assert np.allclose(packed_t9, expected_t9, rtol=0.0, atol=1.0e-11)


def test_packed_operator_preserves_complex_lane() -> None:
    rng = _rng()
    ell = 3
    components = rng.normal(size=2 * ell + 1) + 1j * rng.normal(size=2 * ell + 1)
    sigma = _rank2_stf(rng)

    packed = apply_T8_shear_same_packed(ell, components, sigma)

    assert np.iscomplexobj(packed)
    expected = pstf_pack(T8_shear_same(ell, pstf_unpack(components, ell), sigma))
    assert np.allclose(packed, expected, rtol=0.0, atol=1.0e-11)
