from __future__ import annotations

import math

import numpy as np
import pytest

from obsstat.lowell_map_features import (
    densify_alm,
    empirical_pvalue,
    power_inertia_tensor,
)


def _packed_index(lmax: int, ell: int, m: int) -> int:
    # healpy RING packed index for m >= 0
    return m * (2 * lmax + 1 - m) // 2 + ell


def test_densify_alm_reality_condition():
    lmax = 2
    size = (lmax + 1) * (lmax + 2) // 2
    packed = np.zeros(size, dtype=complex)
    packed[_packed_index(lmax, 2, 0)] = 3.0 + 0.0j  # m=0 must be real-ish
    packed[_packed_index(lmax, 2, 1)] = 1.0 + 2.0j
    packed[_packed_index(lmax, 2, 2)] = -0.5 + 0.7j

    dense = densify_alm(packed, lmax)
    # every m from -ell..+ell present for ell=2
    assert {m for (ell, m) in dense if ell == 2} == set(range(-2, 3))
    # reality condition a_{l,-m} = (-1)^m conj(a_{l,m})
    assert dense[(2, -1)] == pytest.approx((-1) ** 1 * dense[(2, 1)].conjugate())
    assert dense[(2, -2)] == pytest.approx((-1) ** 2 * dense[(2, 2)].conjugate())
    assert dense[(2, 0)] == pytest.approx(3.0 + 0.0j)


def test_empirical_pvalue_tails_are_add_one_conservative():
    nulls = np.arange(0.0, 100.0)  # 0..99
    # upper tail: observed at 95 -> nulls >= 95 are {95..99} = 5, (5+1)/(100+1)
    assert empirical_pvalue(95.0, nulls, tail="upper") == pytest.approx(6 / 101)
    # lower tail: observed at 4 -> nulls <= 4 = {0..4} = 5
    assert empirical_pvalue(4.0, nulls, tail="lower") == pytest.approx(6 / 101)
    # two-sided abs around a centered null
    centered = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    assert empirical_pvalue(2.0, centered, tail="two_sided_abs") == pytest.approx(3 / 6)
    assert 0.0 < empirical_pvalue(0.0, nulls, tail="upper") <= 1.0


def test_power_inertia_tensor_principal_axis_recovers_z():
    # two hot antipodal caps on the +/-z axis -> principal power axis ~ z
    vecs = np.array(
        [
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
        ]
    )
    temp = np.array([5.0, 5.0, 0.1, 0.1])
    tensor = power_inertia_tensor(temp, vecs)
    assert tensor.shape == (3, 3)
    assert np.allclose(tensor, tensor.T)
    evals, evecs = np.linalg.eigh(tensor)
    principal = evecs[:, int(np.argmax(evals))]
    assert abs(abs(principal[2]) - 1.0) < 1e-9


def test_power_inertia_tensor_uniform_map_is_isotropic_trace():
    vecs = np.array(
        [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
        ]
    )
    temp = np.ones(6)
    tensor = power_inertia_tensor(temp, vecs)
    # symmetric octahedron -> isotropic (proportional to identity)
    assert np.allclose(tensor, np.eye(3) * tensor[0, 0])
