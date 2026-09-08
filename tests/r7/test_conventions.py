from itertools import permutations, product
import math
import numpy as np
from scripts.observed_runs.rebuild_mes_tensor_carriers import harmonic_stf_matrices, project_carrier
from obsstat.planck_lowell_irrep_projection import real_harmonic_l2_to_stf


def test_basis_trace_and_moment_normalization():
    qb, ob = harmonic_stf_matrices()
    np.testing.assert_allclose(np.trace(qb, axis1=1, axis2=2), 0, atol=1e-14)
    np.testing.assert_allclose(np.einsum('kiij->kj', ob), 0, atol=1e-14)
    np.testing.assert_allclose(qb.reshape(5, -1) @ qb.reshape(5, -1).T,
                               np.eye(5) * 15 / (8 * math.pi), atol=1e-13)
    np.testing.assert_allclose(ob.reshape(7, -1) @ ob.reshape(7, -1).T,
                               np.eye(7) * 35 / (8 * math.pi), atol=1e-13)


def test_nonzero_m_real_imag_layout_norm_and_sign():
    qb, _ = harmonic_stf_matrices()
    for column, sign in ((1, 1), (2, -1)):
        stored = np.zeros(5); stored[column] = 1.
        real = np.zeros(5); real[column] = sign * math.sqrt(2)
        q = real_harmonic_l2_to_stf(stored)
        np.testing.assert_allclose(q, np.einsum('k,kij->ij', real, qb), atol=1e-13)
        assert math.isclose(np.sum(q*q), 15 / (4*math.pi), rel_tol=1e-12)


def test_t1_chiral_singular_chart_witness():
    q = np.diag([-1, 0, 1])
    components = (1,0,0,-2,1,1,1,-1,-1,1)
    indices = ((0,0,0),(0,0,1),(0,0,2),(0,1,1),(0,1,2),
               (0,2,2),(1,1,1),(1,1,2),(1,2,2),(2,2,2))
    o = np.empty((3,3,3), dtype=int)
    for idx, value in zip(indices, components):
        for p in set(permutations(idx)): o[p] = value
    np.testing.assert_array_equal(np.einsum('iik->k',o), 0)
    v = np.einsum('ijk,jk->i',o,q)
    np.testing.assert_array_equal(v,[0,-1,1])
    assert np.linalg.det(np.column_stack((v,q@v,q@q@v))) == 0
    # Distinct Q eigenvalues leave exactly these four proper stabilizers.
    for signs in product((-1,1), repeat=3):
        if math.prod(signs) == 1:
            rotated = o * np.einsum('i,j,k->ijk',signs,signs,signs)
            assert not np.array_equal(rotated, -o)


def test_carrier_norms_for_every_basis_vector():
    rows = np.eye(32, dtype=float)
    q,o,p = project_carrier(rows)
    np.testing.assert_allclose(np.sum(q*q,axis=(1,2)),75*p[:,0]/(8*math.pi),atol=1e-13)
    np.testing.assert_allclose(np.sum(o*o,axis=(1,2,3)),245*p[:,1]/(8*math.pi),atol=1e-13)
