"""Source-bound observation operator for Gaia DR3 proper motion / VSH analysis.

Binds the exact Gaia DR3 CRF3 quasar dataset:
- quaia_crf3_join.npz from /mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/
- 692,154 cross-matched quasars, filtered to 634,233 clean sources:
    * Finite proper motions and errors
    * RUWE < 1.4
    * astrometric_params_solved == 31 (5-parameter solution)
    * |pmra| < 100 mas/yr, |pmdec| < 100 mas/yr
- Full Vector Spherical Harmonics (VSH) decomposition on the celestial sphere:
    * 3 Spin (R1) modes (ICRS reference frame rotation)
    * 3 Glide (E1) modes (observer acceleration / secular aberration drift)
    * 5 Shear (E2) modes (electric quadrupole / cosmic shear)
- Exact analytic Schur complement marginalization of the 3 frame spin nuisance parameters.
- Evaluates chi2 and log-likelihood under physical state theta_K.
"""

from __future__ import annotations

import os
import hashlib
from typing import Tuple, Dict, Any, Optional
import numpy as np

from common.source_bound_pantheon_operator import verify_file_sha256
from common.observation_operator_contract import (
    ObservationSourceMetadata,
    PhysicalFunctionalSpec,
    CoordinateFrame,
    EstimatorType,
)

GAIA_NPZ_PATH = "/mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_crf3_join.npz"
EXPECTED_GAIA_SHA256 = "2fbaa40a8afe58066064efa8a7784ac508c5b2c67b41c779676eab7df8cf9ef4"

# Dimensional conversion factor: H0 in mas/yr
# H0 = 70 km/s/Mpc = 2.268e-18 s^-1
# 1 rad = 2.06265e8 mas, 1 yr = 3.15576e7 s
# H0 * (1 yr) * (2.06265e8 mas/rad) = 0.01476 mas/yr
H0_MAS_YR = 0.01476


def vsh_basis_functions(ra_deg: np.ndarray, dec_deg: np.ndarray) -> Dict[str, list]:
    """Compute VSH basis vector fields on the celestial sphere.
    
    Coordinates: phi = RA, theta = 90 - Dec (colatitude).
    Components: (mu_ra*, mu_dec) where mu_ra* = mu_ra * cos(dec).
    """
    phi = np.deg2rad(ra_deg)
    theta = np.deg2rad(90.0 - dec_deg)

    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    cos_p = np.cos(phi)
    sin_p = np.sin(phi)

    # 1. Spin (B1 axial magnetic dipole modes - rigid frame rotation)
    R_cols = [
        np.column_stack([-cos_t * cos_p, sin_p]),
        np.column_stack([-cos_t * sin_p, -cos_p]),
        np.column_stack([sin_t, np.zeros_like(phi)]),
    ]

    # 2. Glide (E1 polar electric dipole modes - acceleration drift)
    G_cols = [
        np.column_stack([-sin_p, -cos_t * cos_p]),
        np.column_stack([cos_p, -cos_t * sin_p]),
        np.column_stack([np.zeros_like(phi), sin_t]),
    ]

    # 3. Shear (E2 electric quadrupole modes)
    E_cols = [
        np.column_stack([np.zeros_like(phi), 3.0 * np.sin(2.0 * theta)]),
        np.column_stack([-2.0 * cos_t * sin_p, -2.0 * np.cos(2.0 * theta) * cos_p]),
        np.column_stack([2.0 * cos_t * cos_p, -2.0 * np.cos(2.0 * theta) * sin_p]),
        np.column_stack([-2.0 * sin_t * np.sin(2.0 * phi), -np.sin(2.0 * theta) * np.cos(2.0 * phi)]),
        np.column_stack([2.0 * sin_t * np.cos(2.0 * phi), -np.sin(2.0 * theta) * np.sin(2.0 * phi)]),
    ]

    return {
        "spin": R_cols,
        "glide": G_cols,
        "shear": E_cols,
    }


def _fibonacci_radec(n: int = 20000):
    """Deterministic equal-area grid on S^2 as (ra_deg, dec_deg)."""
    i = np.arange(n) + 0.5
    z = 1.0 - 2.0 * i / n
    phi = (np.pi * (1.0 + 5.0 ** 0.5) * i) % (2.0 * np.pi)
    return np.rad2deg(phi), np.rad2deg(np.arcsin(z))


def vsh_shear_gram(n: int = 20000) -> np.ndarray:
    """Sphere-averaged Gram matrix G_ij = <E_i . E_j> of the five E2 basis fields (mas/yr per unit coefficient squared).

    The E2 basis is not orthonormal (and is not the Cartesian STF5 chart), so the Euclidean norm of the coefficient vector is chart
    dependent. The invariant field amplitude is sqrt(c^T G c).
    """
    ra, dec = _fibonacci_radec(n)
    E = vsh_basis_functions(ra, dec)["shear"]
    G = np.empty((5, 5))
    for i in range(5):
        for j in range(5):
            G[i, j] = float(np.mean(np.sum(E[i] * E[j], axis=1)))
    return 0.5 * (G + G.T)


def vsh_shear_l2_amplitude(c: np.ndarray, n: int = 20000) -> float:
    """Sphere-averaged rms amplitude of the E2 field sum_k c_k E_k (mas/yr)."""
    c = np.asarray(c, dtype=np.float64)
    return float(np.sqrt(c @ vsh_shear_gram(n) @ c))


class SourceBoundGaiaVSHOperator:
    """Source-bound observation operator for Gaia DR3 CRF3 quasar VSH proper motions."""

    def __init__(
        self,
        npz_path: str = GAIA_NPZ_PATH,
        verify_sha: bool = True,
        ruwe_max: float = 1.4,
        pm_max_mas_yr: float = 100.0,
    ) -> None:
        self.npz_path = npz_path
        self.ruwe_max = ruwe_max
        self.pm_max_mas_yr = pm_max_mas_yr

        if verify_sha:
            if not verify_file_sha256(npz_path, EXPECTED_GAIA_SHA256):
                raise ValueError(f"Gaia file {npz_path} failed SHA-256 verification!")

        self._fit_vsh_sufficient_statistics()

    def _fit_vsh_sufficient_statistics(self) -> None:
        """Load data, apply quality cuts, and compute Schur Fisher matrix and MLE."""
        if not os.path.exists(self.npz_path):
            raise FileNotFoundError(f"Gaia file not found at {self.npz_path}")

        z = np.load(self.npz_path)
        ra = z["ra"]
        dec = z["dec"]
        pmra = z["gaia_pmra"]
        pmdec = z["gaia_pmdec"]
        pmra_err = z["gaia_pmra_error"]
        pmdec_err = z["gaia_pmdec_error"]
        ruwe = z["gaia_ruwe"]
        solved = z["gaia_astrometric_params_solved"]

        self.n_raw = len(ra)

        # Quality selection mask
        mask = (
            np.isfinite(pmra) & np.isfinite(pmdec) &
            np.isfinite(pmra_err) & np.isfinite(pmdec_err) &
            (pmra_err > 0) & (pmdec_err > 0) &
            (ruwe < self.ruwe_max) & (solved == 31) &
            (np.abs(pmra) < self.pm_max_mas_yr) & (np.abs(pmdec) < self.pm_max_mas_yr)
        )
        idx = np.flatnonzero(mask)
        self.n_selected = len(idx)

        sub_ra = ra[idx]
        sub_dec = dec[idx]
        sub_pmra = pmra[idx]
        sub_pmdec = pmdec[idx]
        sub_pmra_err = pmra_err[idx]
        sub_pmdec_err = pmdec_err[idx]

        vsh = vsh_basis_functions(sub_ra, sub_dec)

        # Assemble whitened normal equations
        # Data vector y of length 2N: [pmra_0, pmdec_0, pmra_1, pmdec_1, ...]
        n = self.n_selected
        y = np.empty(2 * n, dtype=np.float64)
        y[0::2] = sub_pmra
        y[1::2] = sub_pmdec

        w = np.empty(2 * n, dtype=np.float64)
        w[0::2] = 1.0 / sub_pmra_err
        w[1::2] = 1.0 / sub_pmdec_err

        yw = y * w

        # Nuisance design matrix N (3 spin modes)
        N_mat = np.empty((2 * n, 3), dtype=np.float64)
        for k in range(3):
            N_mat[0::2, k] = vsh["spin"][k][:, 0] * w[0::2]
            N_mat[1::2, k] = vsh["spin"][k][:, 1] * w[1::2]

        # Signal design matrix S (3 glide + 5 shear = 8 modes)
        S_mat = np.empty((2 * n, 8), dtype=np.float64)
        for k in range(3):
            S_mat[0::2, k] = vsh["glide"][k][:, 0] * w[0::2]
            S_mat[1::2, k] = vsh["glide"][k][:, 1] * w[1::2]
        for k in range(5):
            S_mat[0::2, 3 + k] = vsh["shear"][k][:, 0] * w[0::2]
            S_mat[1::2, 3 + k] = vsh["shear"][k][:, 1] * w[1::2]

        # Blocks of normal matrix
        NN = N_mat.T @ N_mat
        NS = N_mat.T @ S_mat
        SS = S_mat.T @ S_mat
        Ny = N_mat.T @ yw
        Sy = S_mat.T @ yw

        # Schur complement on frame spin:
        # A = S^T S - (S^T N) (N^T N)^-1 (N^T S)
        inv_NN = np.linalg.inv(NN)
        self.A = SS - NS.T @ inv_NN @ NS  # 8x8 Fisher matrix
        self.b = Sy - NS.T @ inv_NN @ Ny  # 8-vector gradient

        self.c_mle = np.linalg.solve(self.A, self.b)
        self.cov_c = np.linalg.inv(self.A)
        self.cho_cov = np.linalg.cholesky(self.cov_c)

        # Baseline chi2 at MLE (after projecting nuisance)
        # chi2_res = y_w^T y_w - [Ny; Sy]^T [NN, NS; NS^T, SS]^-1 [Ny; Sy]
        M_joint = np.block([[NN, NS], [NS.T, SS]])
        rhs_joint = np.concatenate([Ny, Sy])
        sol_joint = np.linalg.solve(M_joint, rhs_joint)
        self.chi2_min = float(np.sum(yw ** 2) - rhs_joint @ sol_joint)

        self.glide_mle = self.c_mle[:3]
        self.shear_mle = self.c_mle[3:]
        self.amp_glide = float(np.linalg.norm(self.glide_mle))
        # chart-dependent Euclidean norm of the E2 coefficients (kept for continuity; NOT an invariant amplitude)
        self.amp_shear = float(np.linalg.norm(self.shear_mle))
        # invariant sphere-averaged rms amplitude of the fitted E2 field
        self.amp_shear_l2 = vsh_shear_l2_amplitude(self.shear_mle)

    def evaluate_modes(self, c_model: np.ndarray) -> Tuple[float, float]:
        """Evaluate chi2 and log-likelihood for an 8-vector of VSH modes (mas/yr).
        
        c_model: [G_x, G_y, G_z, E_20, E_21c, E_21s, E_22c, E_22s]
        """
        diff = np.asarray(c_model, dtype=np.float64) - self.c_mle
        delta_chi2 = float(diff @ self.A @ diff)
        chi2_total = self.chi2_min + delta_chi2
        log_det_cov = float(2.0 * np.sum(np.log(np.diag(self.cho_cov))))
        log_like = -0.5 * (delta_chi2 + log_det_cov + 8.0 * np.log(2.0 * np.pi))
        return chi2_total, log_like

    def evaluate_model(
        self,
        theta_K: np.ndarray,  # 17-vector: [sigma_5, omega_3, A_3, beta_RM_3, beta_MO_3]
    ) -> Tuple[float, float]:
        """Evaluate chi2 and log-likelihood under physical state theta_K."""
        assert len(theta_K) == 17, f"Expected 17 kinematic parameters, got {len(theta_K)}"
        sigma_5 = theta_K[0:5]  # STF5 Cartesian: (Sxx, Syy, Sxy, Sxz, Syz)
        A_3 = theta_K[8:11]     # Dimensionless polar acceleration A / (c * H0)

        # 1. Forward model for Glide (mas/yr)
        # G = (A / c H0) * H0_mas_yr
        G_pred = A_3 * H0_MAS_YR

        # 2. Forward model for Shear E2 modes (mas/yr)
        # Mapping from STF Cartesian to E2 basis
        Sxx, Syy, Sxy, Sxz, Syz = sigma_5
        Szz = -Sxx - Syy

        E2_0 = 0.25 * Szz * H0_MAS_YR
        E2_1c = 0.5 * Sxz * H0_MAS_YR
        E2_1s = 0.5 * Syz * H0_MAS_YR
        E2_2c = 0.25 * (Sxx - Syy) * H0_MAS_YR
        E2_2s = 0.5 * Sxy * H0_MAS_YR

        c_pred = np.array([
            G_pred[0], G_pred[1], G_pred[2],
            E2_0, E2_1c, E2_1s, E2_2c, E2_2s
        ], dtype=np.float64)

        return self.evaluate_modes(c_pred)

    def evaluate_likelihood(
        self,
        theta_K: np.ndarray,
        psi: Optional[Any] = None,
    ) -> Tuple[float, float]:
        return self.evaluate_model(theta_K)

    @property
    def metadata(self) -> ObservationSourceMetadata:
        return ObservationSourceMetadata(
            source_id="Gaia_DR3_CRF3_Astrometry",
            product_name="Gaia DR3 CRF3 Quasar Proper Motion Astrometry",
            catalog_or_data_path=self.npz_path,
            covariance_path=None,
            n_total_objects=self.n_raw,
            n_selected_objects=self.n_selected,
            selection_rule="RUWE < 1.4, 5-param astrometry, |pm| < 100 mas/yr",
            coordinate_frame=CoordinateFrame.ICRS,
            units="mas / yr",
            estimator_type=EstimatorType.ASTROMETRIC_VSH,
            window_or_mask_id="Gaia_CRF3_RUWE1.4_clean",
            covariance_id="Astrometric_Schur_Marginalized_Fisher",
            verified_sha256=EXPECTED_GAIA_SHA256,
            is_synthetic=False,
        )

    @property
    def functional_spec(self) -> PhysicalFunctionalSpec:
        return PhysicalFunctionalSpec(
            name="astrometric_glide_shear_vsh",
            tensor_rank=2,
            parity="even",
            so3_representation="1- direct sum 2+",
            units="mas / yr",
            parameter_dependence=("A", "sigma_ab"),
        )

    def get_data_vector(self) -> np.ndarray:
        return self.c_mle

    def get_covariance_matrix(self) -> np.ndarray:
        return self.cov_c
