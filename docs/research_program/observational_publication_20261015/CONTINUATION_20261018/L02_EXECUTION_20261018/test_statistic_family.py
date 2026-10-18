"""Falsifiers for basis, physical B parity, orbit summaries and unknown axes."""
import numpy as np
import pytest
from scipy.special import sph_harm_y
from scipy.spatial.transform import Rotation

from statistic_family import (PARITY_SIGNS, SHAPE_NAMES, checked, cross_features,
                              descriptors, load_source, metamorphic_checks,
                              principal_projector, tensors_from_real, transform)


@pytest.fixture
def carrier():
    return np.random.default_rng(4102).normal(size=32)


def harmonic_value(row, directions, ell):
    theta = np.arccos(directions[:, 2])
    phi = np.arctan2(directions[:, 1], directions[:, 0])
    c = row[ell*ell-4:(ell+1)*(ell+1)-4]
    output = c[0]*sph_harm_y(ell, 0, theta, phi).real
    for m in range(1, ell+1):
        y = sph_harm_y(ell, m, theta, phi)
        output += np.sqrt(2.)*(c[2*m-1]*y.real+c[2*m]*y.imag)
    return output


def test_independent_harmonic_polynomial_and_normalization(carrier):
    q, o = tensors_from_real(carrier)
    n = np.random.default_rng(100).normal(size=(257, 3))
    n /= np.linalg.norm(n, axis=1)[:, None]
    np.testing.assert_allclose(np.einsum("ni,ij,nj->n", n, q, n), harmonic_value(carrier, n, 2), atol=2e-10, rtol=0)
    np.testing.assert_allclose(np.einsum("ijk,ni,nj,nk->n", o, n, n, n), harmonic_value(carrier, n, 3), atol=2e-10, rtol=0)
    assert np.sum(q*q) == pytest.approx(15/(8*np.pi)*sum(carrier[:5]**2))
    assert np.sum(o*o) == pytest.approx(35/(8*np.pi)*sum(carrier[5:12]**2))


@pytest.mark.parametrize("field", ("T", "E", "B"))
def test_active_o3_harmonic_action_and_physical_inversion(carrier, field):
    q, o = tensors_from_real(carrier)
    rng = np.random.default_rng(76)
    n = rng.normal(size=(100, 3)); n /= np.linalg.norm(n, axis=1)[:, None]
    reflection = Rotation.from_rotvec([.71, -.9, .43]).as_matrix()@np.diag([-1., 1., 1.])
    qt, ot = transform(q, o, reflection, field)
    intrinsic = -1 if field == "B" else 1
    # f'(n)=p f(M^T n), evaluated directly with complex harmonics.
    np.testing.assert_allclose(np.einsum("ni,ij,nj->n", n, qt, n), intrinsic*harmonic_value(carrier, n@reflection, 2), atol=2e-10, rtol=0)
    np.testing.assert_allclose(np.einsum("ijk,ni,nj,nk->n", ot, n, n, n), intrinsic*harmonic_value(carrier, n@reflection, 3), atol=2e-10, rtol=0)
    parity_row = carrier.copy()
    for ell in range(2, 6):
        parity_row[ell*ell-4:(ell+1)*(ell+1)-4] *= (-1)**(ell+(field == "B"))
    wanted = tensors_from_real(parity_row)
    moved = transform(q, o, -np.eye(3), field)
    for actual, expected in zip(moved, wanted):
        np.testing.assert_allclose(actual, expected, atol=1e-14, rtol=0)


@pytest.mark.parametrize("field", ("T", "E", "B"))
def test_physical_parity_features_and_covariant_orientation(carrier, field):
    q, o = tensors_from_real(carrier)
    m = Rotation.from_rotvec([.4, -.3, .21]).as_matrix()@np.diag([1., -1., 1.])
    base = descriptors(q, o, field)
    moved = descriptors(*transform(q, o, m, field), field)
    for name, sign in zip(SHAPE_NAMES, PARITY_SIGNS[field]):
        assert moved["SO3_signed"][name] == pytest.approx(sign*base["SO3_signed"][name], abs=2e-11)
        assert moved["O3_summaries"][name] == pytest.approx(base["O3_summaries"][name], abs=2e-11)
    for key in ("Q2_projector", "O3_projector"):
        p = np.array(base["orientation"][key])
        np.testing.assert_allclose(moved["orientation"][key], m@p@m.T, atol=2e-11, rtol=0)
    assert moved["orientation"]["joint_axis_overlap_squared"] == pytest.approx(base["orientation"]["joint_axis_overlap_squared"], abs=2e-11)
    assert not np.allclose(base["orientation"]["Q2_fixed_axis_squared_cosines"], moved["orientation"]["Q2_fixed_axis_squared_cosines"])


def test_b_scalar_shortcut_is_detected(carrier):
    q, o = tensors_from_real(carrier)
    base = descriptors(q, o, "B")["SO3_signed"]
    wrong = descriptors(q, -o, "B")["SO3_signed"]
    # Incorrectly reflecting B as a polar tensor changes the wrong descriptors.
    assert abs(base["quadrupole_shape"]) > 1e-3
    assert wrong["quadrupole_shape"] != pytest.approx(-base["quadrupole_shape"], abs=2e-11)
    assert abs(base["chirality"]) > 1e-3
    assert wrong["chirality"] != pytest.approx(base["chirality"], abs=2e-11)


@pytest.mark.parametrize("left,right,sign", (("T", "E", 1), ("T", "B", -1), ("E", "B", -1)))
def test_cross_field_parity(carrier, left, right, sign):
    q, o = tensors_from_real(carrier)
    p, t = tensors_from_real(np.random.default_rng(89).normal(size=32))
    m = np.diag([-1., 1., 1.])
    base = cross_features(q, o, p, t)
    moved = cross_features(*transform(q, o, m, left), *transform(p, t, m, right))
    for key in base:
        factor = sign if key in ("Q_normalized_overlap", "O_normalized_overlap") else 1
        assert moved[key] == pytest.approx(factor*base[key], abs=2e-11)


def test_zero_and_degenerate_features_remain_unknown():
    q, o = np.zeros((3, 3)), np.zeros((3, 3, 3))
    result = descriptors(q, o, "T")
    assert all(v is None for v in result["SO3_signed"].values())
    assert result["orientation"]["joint_axis_overlap_squared"] is None
    assert result["orientation"]["Q2_projector"] is None
    assert principal_projector(np.eye(3))[0] is None
    assert principal_projector(np.diag([1., 1., 1.+5e-11]))[0] is None
    assert principal_projector(np.diag([1., 1., 1.+2e-10]))[0] is not None
    row = np.zeros(32); row[0] = row[5] = 1.
    q, o = tensors_from_real(row)
    result = descriptors(q, o, "E")
    assert result["SO3_signed"]["chirality"] == pytest.approx(0., abs=1e-15)
    # This axisymmetric carrier has defined vector norms; zero chirality is valid.
    q = np.diag([1., -1., 0.])
    result = descriptors(q, o, "T")
    assert result["orientation"]["Q2_projector"] is None
    assert result["SO3_signed"]["chirality"] is None
    assert result["shape_status"]["chirality"] == "UNKNOWN_DEGENERATE_CHIRALITY"


def test_scale_invariance_and_invalid_inputs(carrier):
    q, o = tensors_from_real(carrier)
    base = descriptors(q, o, "T")
    for scale in (1e-200, 1e200):
        moved = descriptors(q*scale, o*scale, "T")
        for name in SHAPE_NAMES:
            assert moved["SO3_signed"][name] == pytest.approx(base["SO3_signed"][name], abs=2e-11)
    with pytest.raises(ValueError, match="orthogonal"):
        transform(q, o, 2*np.eye(3), "B")
    with pytest.raises(ValueError, match="STF"):
        checked(q+np.eye(3), o)
    with pytest.raises(ValueError, match="real"):
        descriptors(q+1j, o, "T")


def test_actual_source_layout_and_all_row_metamorphics():
    rows, metadata = load_source()
    assert len(rows) == 25
    assert [sum(field == f for _, field, _ in rows) for f in ("T", "E", "B")] == [9, 8, 8]
    assert metadata["common_POL_nside64_pixel_count"] == 30021
    report = metamorphic_checks(rows)
    assert report["field_row_transform_checks"] == 450
    assert report["cross_pair_transform_checks"] == 432
