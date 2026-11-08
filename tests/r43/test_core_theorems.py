import numpy as np
from scripts.r43.verify_core_theorems import (
    build_tomographic_design,
    hubble_design,
    rank_after_nuisance_projection,
    stf_basis,
)


def _rank(tomography: bool, anchors: bool) -> int:
    jt, jn, cov = build_tomographic_design(tomography, anchors)
    return rank_after_nuisance_projection(jt, jn, cov)[0]


def test_anchor_null_fibres_and_tomographic_rank():
    assert _rank(True, False) == 11
    assert _rank(True, True) == 17
    assert _rank(False, False) == 8


def test_directional_hubble_monopole_dipole_quadrupole_rank():
    assert hubble_design(256)[0] == 9
    assert hubble_design(128, hemisphere=True)[0] == 9


def test_stf_basis_is_orthonormal_and_traceless():
    q = stf_basis()
    np.testing.assert_allclose(np.einsum("aij,bij->ab", q, q), np.eye(5), atol=1e-14)
    np.testing.assert_allclose(np.trace(q, axis1=1, axis2=2), np.zeros(5), atol=1e-14)
