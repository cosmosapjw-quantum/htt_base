"""Tests for STF Metric Bridge and Relativistic Velocity Closure.

Verifies:
1. Metric equivalence: v_cart.T @ G_STF5 @ v_cart == v_on.T @ v_on == Tr(S @ S).
2. Bijective chart roundtrips between Cartesian, orthonormal, and 3x3 STF matrix.
3. Basis conventions: 'kinematic_response' (matching kinematic_response.STF_BASIS)
   and 'explicit_szz' (astrophysical).
4. Exact O(3) and SO(3) rotation equivariance and norm invariance.
5. Special relativistic velocity composition, subluminal bounds, and first-order residual.
6. Exact Wigner rotation matrix in SO(3), angle, axis, and non-relativistic limit.
7. Second-order kinematic quadrupole tensor [beta (x) beta]_STF2 and norm identity.
8. Frame rotation equivariance of velocity closure and kinematic quadrupole.
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from common.kinematic_response import BetaTruncationError, KinematicsError, STF_BASIS
from common.relativistic_kinematics import lorentz_boost
from common.stf_metric_bridge import (
    G_STF5,
    G_STF5_INV,
    cartesian_to_orthonormal,
    cartesian_to_orthonormal_matrix,
    cartesian_to_stf_matrix,
    orthonormal_to_cartesian,
    orthonormal_to_cartesian_matrix,
    orthonormal_to_stf_matrix,
    rotate_stf_matrix,
    rotate_stf_vector,
    stf_cartesian_inner_product,
    stf_frobenius_norm,
    stf_frobenius_norm_sq,
    stf_gram_metric,
    stf_matrix_inner_product,
    stf_matrix_to_cartesian,
    stf_matrix_to_orthonormal,
    stf_orthonormal_inner_product,
    stf_project,
    stf_rotation_operator_5d,
    validate_stf_matrix,
    verify_o3_invariance,
)
from common.relativistic_velocity_closure import (
    VelocityClosureResult,
    compose_and_close_velocities,
    compose_velocities_sr,
    kinematic_quadrupole_stf2,
    wigner_rotation,
)


# Helper: construct random SO(3) rotation matrix from Euler angles
def _random_so3(rng: np.random.Generator) -> np.ndarray:
    angles = rng.uniform(0.0, 2.0 * np.pi, size=3)
    c1, c2, c3 = np.cos(angles)
    s1, s2, s3 = np.sin(angles)
    Rz = np.array([[c1, -s1, 0], [s1, c1, 0], [0, 0, 1]])
    Ry = np.array([[c2, 0, s2], [0, 1, 0], [-s2, 0, c2]])
    Rx = np.array([[1, 0, 0], [0, c3, -s3], [0, s3, c3]])
    return Rz @ Ry @ Rx


# Helper: construct random 3x3 STF tensor
def _random_stf(rng: np.random.Generator, scale: float = 1.0) -> np.ndarray:
    A = rng.normal(scale=scale, size=(3, 3))
    return stf_project(A)


# ===========================================================================
# 1. Metric Equivalence Tests
# ===========================================================================
class TestSTFMetricBridge:
    """Verifies metric matrix properties and exact norm equivalence."""

    def test_gram_matrix_properties(self):
        """Verify G_STF5 is symmetric, positive definite, and inverts cleanly."""
        assert np.allclose(G_STF5, G_STF5.T)
        eigvals = np.linalg.eigvalsh(G_STF5)
        assert np.all(eigvals > 0.0), "G_STF5 must be strictly positive definite"
        assert np.allclose(G_STF5 @ G_STF5_INV, np.eye(5), atol=1e-15)
        assert np.allclose(stf_gram_metric(), G_STF5)

    def test_transformation_matrix_isometry(self):
        """Verify M.T @ M == G_STF5 for both conventions."""
        for convention in ("kinematic_response", "explicit_szz"):
            M = cartesian_to_orthonormal_matrix(convention)
            M_inv = orthonormal_to_cartesian_matrix(convention)
            assert np.allclose(M @ M_inv, np.eye(5), atol=1e-14)
            assert np.allclose(M.T @ M, G_STF5, atol=1e-14)
            assert np.allclose(M_inv @ M_inv.T, G_STF5_INV, atol=1e-14)

    def test_norm_equivalence_random_ensemble(self):
        """Verify v_cart.T @ G_STF5 @ v_cart == v_on.T @ v_on == Tr(S @ S) across 100 samples."""
        rng = np.random.default_rng(20261107)
        for _ in range(100):
            S = _random_stf(rng, scale=rng.uniform(0.1, 10.0))
            v_cart = stf_matrix_to_cartesian(S)
            v_on_kr = stf_matrix_to_orthonormal(S, convention="kinematic_response")
            v_on_szz = stf_matrix_to_orthonormal(S, convention="explicit_szz")

            tr_S2 = float(np.trace(S @ S))
            cart_norm2 = float(stf_cartesian_inner_product(v_cart, v_cart))
            on_kr_norm2 = float(stf_orthonormal_inner_product(v_on_kr, v_on_kr))
            on_szz_norm2 = float(stf_orthonormal_inner_product(v_on_szz, v_on_szz))

            assert math.isclose(tr_S2, cart_norm2, rel_tol=1e-13, abs_tol=1e-14)
            assert math.isclose(tr_S2, on_kr_norm2, rel_tol=1e-13, abs_tol=1e-14)
            assert math.isclose(tr_S2, on_szz_norm2, rel_tol=1e-13, abs_tol=1e-14)

    def test_bilinear_inner_product_equivalence(self):
        """Verify u_cart.T @ G_STF5 @ v_cart == u_on.T @ v_on == Tr(S_u @ S_v)."""
        rng = np.random.default_rng(42)
        for _ in range(20):
            S_u = _random_stf(rng)
            S_v = _random_stf(rng)
            u_cart = stf_matrix_to_cartesian(S_u)
            v_cart = stf_matrix_to_cartesian(S_v)
            u_on = stf_matrix_to_orthonormal(S_u)
            v_on = stf_matrix_to_orthonormal(S_v)

            tr_uv = float(stf_matrix_inner_product(S_u, S_v))
            cart_inner = float(stf_cartesian_inner_product(u_cart, v_cart))
            on_inner = float(stf_orthonormal_inner_product(u_on, v_on))

            assert math.isclose(tr_uv, cart_inner, rel_tol=1e-13, abs_tol=1e-14)
            assert math.isclose(tr_uv, on_inner, rel_tol=1e-13, abs_tol=1e-14)


# ===========================================================================
# 2. Bijective Chart Round-trips
# ===========================================================================
class TestSTFChartRoundtrips:
    """Verifies bijective conversions between representations."""

    def test_cartesian_to_matrix_roundtrip(self):
        """Verify v_cart <-> S roundtrip."""
        rng = np.random.default_rng(101)
        for _ in range(25):
            S = _random_stf(rng)
            v_cart = stf_matrix_to_cartesian(S)
            S_rec = cartesian_to_stf_matrix(v_cart)
            assert np.allclose(S, S_rec, atol=1e-14)

    def test_orthonormal_to_matrix_roundtrip(self):
        """Verify v_on <-> S roundtrip for both conventions."""
        rng = np.random.default_rng(102)
        for convention in ("kinematic_response", "explicit_szz"):
            for _ in range(25):
                S = _random_stf(rng)
                v_on = stf_matrix_to_orthonormal(S, convention=convention)
                S_rec = orthonormal_to_stf_matrix(v_on, convention=convention)
                assert np.allclose(S, S_rec, atol=1e-14)

    def test_cartesian_to_orthonormal_roundtrip(self):
        """Verify v_cart <-> v_on roundtrip."""
        rng = np.random.default_rng(103)
        for convention in ("kinematic_response", "explicit_szz"):
            for _ in range(25):
                v_cart = rng.normal(size=5)
                v_on = cartesian_to_orthonormal(v_cart, convention=convention)
                v_cart_rec = orthonormal_to_cartesian(v_on, convention=convention)
                assert np.allclose(v_cart, v_cart_rec, atol=1e-14)

    def test_consistency_with_kinematic_response_stf_basis(self):
        """Verify v_on @ STF_BASIS matches S reconstructed from v_on."""
        rng = np.random.default_rng(104)
        for _ in range(20):
            S = _random_stf(rng)
            v_on = stf_matrix_to_orthonormal(S, convention="kinematic_response")
            # Decompose via STF_BASIS from kinematic_response.py
            S_basis = np.einsum("a,aij->ij", v_on, STF_BASIS)
            assert np.allclose(S, S_basis, atol=1e-14)

    def test_batched_operations(self):
        """Verify vectorized operations across batch dimensions."""
        rng = np.random.default_rng(105)
        batch_cart = rng.normal(size=(8, 4, 5))
        batch_mat = cartesian_to_stf_matrix(batch_cart)
        assert batch_mat.shape == (8, 4, 3, 3)

        batch_cart_rec = stf_matrix_to_cartesian(batch_mat)
        assert np.allclose(batch_cart, batch_cart_rec, atol=1e-14)

        batch_on = cartesian_to_orthonormal(batch_cart)
        assert batch_on.shape == (8, 4, 5)
        batch_norm_sq = stf_frobenius_norm_sq(batch_on, chart="orthonormal")
        assert batch_norm_sq.shape == (8, 4)


# ===========================================================================
# 3. Basis Conventions and Explicit Formulas
# ===========================================================================
class TestBasisConventions:
    """Verifies algebraic components match explicit paper and code formulas."""

    def test_explicit_formula_components(self):
        """Check component formulas:
        v_on[0] = 1/sqrt(2)*(S_xx - S_yy)
        v_on[1] = 1/sqrt(6)*(2*S_zz - S_xx - S_yy) (in explicit_szz)
        v_on[2] = sqrt(2)*S_xy
        v_on[3] = sqrt(2)*S_xz
        v_on[4] = sqrt(2)*S_yz
        """
        S = np.array([
            [1.0, 0.2, -0.3],
            [0.2, -0.4, 0.5],
            [-0.3, 0.5, -0.6],  # S_zz = -(1.0 - 0.4) = -0.6
        ])
        validate_stf_matrix(S)

        s2 = math.sqrt(2.0)
        s6 = math.sqrt(6.0)

        # explicit_szz convention
        v_on_szz = stf_matrix_to_orthonormal(S, convention="explicit_szz")
        expected_0 = (1.0 - (-0.4)) / s2
        expected_1 = (2.0 * (-0.6) - 1.0 - (-0.4)) / s6
        expected_2 = s2 * 0.2
        expected_3 = s2 * (-0.3)
        expected_4 = s2 * 0.5

        assert math.isclose(v_on_szz[0], expected_0, rel_tol=1e-14)
        assert math.isclose(v_on_szz[1], expected_1, rel_tol=1e-14)
        assert math.isclose(v_on_szz[2], expected_2, rel_tol=1e-14)
        assert math.isclose(v_on_szz[3], expected_3, rel_tol=1e-14)
        assert math.isclose(v_on_szz[4], expected_4, rel_tol=1e-14)

        # kinematic_response convention: element 1 has opposite sign
        v_on_kr = stf_matrix_to_orthonormal(S, convention="kinematic_response")
        assert math.isclose(v_on_kr[1], -expected_1, rel_tol=1e-14)


# ===========================================================================
# 4. O(3) and SO(3) Equivariance and Invariance
# ===========================================================================
class TestO3Equivariance:
    """Verifies exact rotation and reflection equivariance and norm invariance."""

    def test_so3_rotation_equivariance(self):
        """Verify D5(R) @ v matches rotating the underlying STF matrix S' = R @ S @ R.T."""
        rng = np.random.default_rng(200)
        for _ in range(30):
            R = _random_so3(rng)
            S = _random_stf(rng)

            # Check orthonormal chart
            v_on = stf_matrix_to_orthonormal(S)
            v_on_rot = rotate_stf_vector(v_on, R, chart="orthonormal")
            S_rot_expected = rotate_stf_matrix(S, R)
            S_rot_actual = orthonormal_to_stf_matrix(v_on_rot)
            assert np.allclose(S_rot_expected, S_rot_actual, atol=1e-13)

            # Check Cartesian chart
            v_cart = stf_matrix_to_cartesian(S)
            v_cart_rot = rotate_stf_vector(v_cart, R, chart="cartesian")
            S_rot_cart = cartesian_to_stf_matrix(v_cart_rot)
            assert np.allclose(S_rot_expected, S_rot_cart, atol=1e-13)

            # Verify helper function
            assert verify_o3_invariance(v_on, R, chart="orthonormal")
            assert verify_o3_invariance(v_cart, R, chart="cartesian")

    def test_so3_operator_orthogonality_and_gram_isometry(self):
        """Verify D5_on in O(5) and D5_cart.T @ G_STF5 @ D5_cart == G_STF5."""
        rng = np.random.default_rng(201)
        for _ in range(20):
            R = _random_so3(rng)
            D_on = stf_rotation_operator_5d(R, chart="orthonormal")
            D_cart = stf_rotation_operator_5d(R, chart="cartesian")

            # D_on is orthogonal: D_on.T @ D_on == I_5
            assert np.allclose(D_on.T @ D_on, np.eye(5), atol=1e-14)
            # D_cart preserves G_STF5: D_cart.T @ G_STF5 @ D_cart == G_STF5
            assert np.allclose(D_cart.T @ G_STF5 @ D_cart, G_STF5, atol=1e-14)

    def test_parity_and_reflection(self):
        """Verify O(3) reflection and parity (det(R) = -1)."""
        rng = np.random.default_rng(202)
        # Spatial parity: P = -I_3. Rank-2 STF tensor is even: P @ S @ P = S.
        P = -np.eye(3)
        D_parity = stf_rotation_operator_5d(P, chart="orthonormal")
        assert np.allclose(D_parity, np.eye(5), atol=1e-14)

        # Reflection across xy plane: R = diag(1, 1, -1)
        R_ref = np.diag([1.0, 1.0, -1.0])
        S = _random_stf(rng)
        v_on = stf_matrix_to_orthonormal(S)
        assert verify_o3_invariance(v_on, R_ref, chart="orthonormal")


# ===========================================================================
# 5. Validation and Projection
# ===========================================================================
class TestValidationAndProjection:
    """Verifies projection to STF and error handling."""

    def test_stf_project(self):
        """Verify stf_project creates symmetric trace-free matrix."""
        rng = np.random.default_rng(300)
        A = rng.normal(size=(3, 3))
        S = stf_project(A)
        assert np.allclose(S, S.T, atol=1e-14)
        assert math.isclose(float(np.trace(S)), 0.0, abs_tol=1e-14)

    def test_validate_stf_matrix_errors(self):
        """Verify non-symmetric or non-trace-free matrices raise ValueError."""
        # Non-symmetric
        with pytest.raises(ValueError, match="symmetric"):
            validate_stf_matrix(np.array([[1, 2, 0], [0, 1, 0], [0, 0, -2]]))
        # Non-trace-free
        with pytest.raises(ValueError, match="trace-free"):
            validate_stf_matrix(np.array([[1, 0, 0], [0, 1, 0], [0, 0, 0]]))


# ===========================================================================
# 6. Relativistic Velocity Closure Tests
# ===========================================================================
class TestRelativisticVelocityClosure:
    """Verifies relativistic velocity composition, residual, and Wigner rotation."""

    def test_zero_velocity_limits(self):
        """Verify beta_RM = 0 -> beta_RO = beta_MO, and beta_MO = 0 -> beta_RO = beta_RM."""
        b = np.array([0.1, -0.2, 0.05])
        zero = np.zeros(3)

        # Zero drift
        res_zero_drift = compose_and_close_velocities(zero, b)
        assert np.allclose(res_zero_drift.beta_RO, b, atol=1e-15)
        assert np.allclose(res_zero_drift.delta_beta, zero, atol=1e-15)
        assert math.isclose(res_zero_drift.wigner_angle_rad, 0.0, abs_tol=1e-12)

        # Zero observer boost
        res_zero_boost = compose_and_close_velocities(b, zero)
        assert np.allclose(res_zero_boost.beta_RO, b, atol=1e-15)
        assert np.allclose(res_zero_boost.delta_beta, zero, atol=1e-15)
        assert math.isclose(res_zero_boost.wigner_angle_rad, 0.0, abs_tol=1e-12)

    def test_collinear_velocity_addition(self):
        """Verify collinear velocities reduce to Einstein's collinear formula (v1+v2)/(1+v1*v2)."""
        v1 = 0.4
        v2 = 0.5
        b1 = np.array([v1, 0.0, 0.0])
        b2 = np.array([v2, 0.0, 0.0])

        res = compose_and_close_velocities(b1, b2)
        expected_v = (v1 + v2) / (1.0 + v1 * v2)
        assert math.isclose(res.beta_RO[0], expected_v, rel_tol=1e-14)
        assert np.allclose(res.beta_RO[1:], 0.0, atol=1e-15)
        # Collinear boosts produce zero Wigner rotation
        assert math.isclose(res.wigner_angle_rad, 0.0, abs_tol=1e-12)

    def test_lorentz_boost_matrix_consistency(self):
        """Verify velocity composition matches 4-velocity boost composition exactly."""
        rng = np.random.default_rng(400)
        for _ in range(25):
            b_rm = rng.uniform(-0.4, 0.4, size=3)
            b_mo = rng.uniform(-0.4, 0.4, size=3)

            res = compose_and_close_velocities(b_rm, b_mo)

            # 4-velocity under pure Lorentz boost composition
            L_rm = lorentz_boost(b_rm)
            L_mo = lorentz_boost(b_mo)
            u_composed = (L_rm @ L_mo) @ np.array([1.0, 0.0, 0.0, 0.0])
            beta_expected = u_composed[1:] / u_composed[0]

            assert np.allclose(res.beta_RO, beta_expected, atol=1e-14)
            assert res.is_subluminal
            assert res.beta_RO_norm < 1.0

    def test_first_order_residual_scaling(self):
        """Verify Delta_beta = beta_RO - (beta_RM + beta_MO) scales as O(beta^2)."""
        b_rm_dir = np.array([0.3, 0.4, 0.0])
        b_mo_dir = np.array([-0.2, 0.1, 0.5])

        residuals = []
        scales = [1e-1, 1e-2, 1e-3, 1e-4]
        for s in scales:
            res = compose_and_close_velocities(s * b_rm_dir, s * b_mo_dir)
            residuals.append(res.delta_beta_norm)

        # Ratio of residuals should scale as (s1 / s2)^2 or s^3 for collinear/orthogonal
        ratio_1_2 = residuals[0] / residuals[1]
        assert ratio_1_2 > 90.0  # ~100 for quadratic / cubic scaling

    def test_subluminal_bounds_checking(self):
        """Verify superluminal velocities raise BetaTruncationError."""
        with pytest.raises(BetaTruncationError):
            compose_and_close_velocities([1.0, 0.0, 0.0], [0.1, 0.0, 0.0])
        with pytest.raises(BetaTruncationError):
            compose_and_close_velocities([0.2, 0.0, 0.0], [0.8, 0.7, 0.0])  # |beta| > 1


# ===========================================================================
# 7. Wigner Rotation Properties
# ===========================================================================
class TestWignerRotation:
    """Verifies SO(3) properties and physical limits of Wigner rotation."""

    def test_wigner_matrix_is_so3(self):
        """Verify R_W is an orthogonal matrix with determinant +1."""
        rng = np.random.default_rng(500)
        for _ in range(30):
            b1 = rng.uniform(-0.5, 0.5, size=3)
            b2 = rng.uniform(-0.5, 0.5, size=3)

            R_W, angle, axis = wigner_rotation(b1, b2)
            assert np.allclose(R_W.T @ R_W, np.eye(3), atol=1e-13)
            assert math.isclose(float(np.linalg.det(R_W)), 1.0, abs_tol=1e-13)
            if angle > 1e-10:
                assert math.isclose(float(np.linalg.norm(axis)), 1.0, abs_tol=1e-12)

    def test_non_relativistic_thomas_precession_limit(self):
        """Verify Wigner angle matches 1/2 * |beta_1 x beta_2| in non-relativistic limit."""
        b1 = np.array([0.01, 0.0, 0.0])
        b2 = np.array([0.0, 0.01, 0.0])

        _, angle, axis = wigner_rotation(b1, b2)
        expected_angle = 0.5 * float(np.linalg.norm(np.cross(b1, b2)))
        assert math.isclose(angle, expected_angle, rel_tol=1e-3)
        # Axis should be aligned with z direction
        assert math.isclose(abs(axis[2]), 1.0, abs_tol=1e-6)


# ===========================================================================
# 8. Kinematic Quadrupole and Equivariance
# ===========================================================================
class TestKinematicQuadrupoleAndEquivariance:
    """Verifies [beta (x) beta]_STF2 tensor and rotation equivariance."""

    def test_kinematic_quadrupole_properties(self):
        """Verify Q_kin is symmetric, trace-free, and satisfies Tr(Q @ Q) == 2/3 * |beta|^4."""
        rng = np.random.default_rng(600)
        for _ in range(25):
            beta = rng.uniform(-0.6, 0.6, size=3)
            Q = kinematic_quadrupole_stf2(beta)

            assert np.allclose(Q, Q.T, atol=1e-15)
            assert math.isclose(float(np.trace(Q)), 0.0, abs_tol=1e-15)

            beta2 = float(np.dot(beta, beta))
            expected_norm_sq = (2.0 / 3.0) * (beta2 ** 2)
            actual_norm_sq = float(np.trace(Q @ Q))
            assert math.isclose(actual_norm_sq, expected_norm_sq, rel_tol=1e-14)

    def test_closure_quadrupole_chart_consistency(self):
        """Verify quadrupole charts in VelocityClosureResult match G_STF5 norm."""
        res = compose_and_close_velocities([0.05, 0.1, -0.02], [-0.03, 0.08, 0.06])
        Q = res.quadrupole_stf2
        q_cart = res.quadrupole_stf5_cart
        q_on = res.quadrupole_stf5_on

        tr_Q2 = float(np.trace(Q @ Q))
        cart_norm2 = float(stf_cartesian_inner_product(q_cart, q_cart))
        on_norm2 = float(stf_orthonormal_inner_product(q_on, q_on))
        expected_norm2 = (2.0 / 3.0) * (res.beta_RO_norm ** 4)

        assert math.isclose(tr_Q2, expected_norm2, rel_tol=1e-13)
        assert math.isclose(cart_norm2, expected_norm2, rel_tol=1e-13)
        assert math.isclose(on_norm2, expected_norm2, rel_tol=1e-13)

    def test_frame_rotation_equivariance(self):
        """Verify rotating inputs by R in SO(3) rotates beta_RO, Q_kin, and R_W equivariantly."""
        rng = np.random.default_rng(700)
        for _ in range(20):
            R = _random_so3(rng)
            b_rm = rng.uniform(-0.3, 0.3, size=3)
            b_mo = rng.uniform(-0.3, 0.3, size=3)

            # Unrotated closure
            res = compose_and_close_velocities(b_rm, b_mo)

            # Rotated closure
            res_rot = compose_and_close_velocities(R @ b_rm, R @ b_mo)

            # 1. beta_RO rotates as 3-vector: R @ beta_RO
            assert np.allclose(res_rot.beta_RO, R @ res.beta_RO, atol=1e-14)

            # 2. delta_beta rotates as 3-vector: R @ delta_beta
            assert np.allclose(res_rot.delta_beta, R @ res.delta_beta, atol=1e-14)

            # 3. Q_kin rotates as rank-2 tensor: R @ Q @ R.T
            assert np.allclose(res_rot.quadrupole_stf2, R @ res.quadrupole_stf2 @ R.T, atol=1e-14)

            # 4. Wigner rotation rotates by similarity: R @ R_W @ R.T
            assert np.allclose(res_rot.wigner_rotation_matrix, R @ res.wigner_rotation_matrix @ R.T, atol=1e-13)
            assert math.isclose(res_rot.wigner_angle_rad, res.wigner_angle_rad, abs_tol=1e-12)
