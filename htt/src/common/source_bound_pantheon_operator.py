"""Source-bound single-probe observation operator for Pantheon+ Supernovae Ia.

Binds the exact Pantheon+ dataset:
- 1,701 Supernovae Ia from Pantheon+SH0ES.dat
- 1,701 x 1,701 STAT+SYS covariance from Pantheon+SH0ES_STAT+SYS.cov
- Exact row ordering, RA/Dec coordinates, heliocentric/CMB/HD redshifts
- Covariant d_L(z, n_hat) model without ad-hoc scale factors
- Exact analytic Schur marginalization for the linear absolute magnitude offset Delta M_0
"""

from __future__ import annotations

import os
import hashlib
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional

import numpy as np
from scipy import integrate

from common.stf_metric_bridge import cartesian_to_orthonormal, G_STF5
from common.observation_operator_contract import (
    ObservationSourceMetadata,
    PhysicalFunctionalSpec,
    CoordinateFrame,
    EstimatorType,
)


PANTHEON_DATA_PATH = "/mnt/extdrive/workdir/raw/observational_bundles/PantheonPlus_SH0ES/Pantheon+SH0ES.dat"
PANTHEON_COV_PATH = "/mnt/extdrive/workdir/raw/observational_bundles/PantheonPlus_SH0ES/Pantheon+SH0ES_STAT+SYS.cov"

EXPECTED_DATA_SHA256 = "1cb0fc379ef066afdc2ffd1857681cc478024570d8a3eba284fb645775198cf8"
EXPECTED_COV_SHA256 = "abf806d966485e64afdb359c87bffc0ecc00d05eff0a31ced66f247385df0fdc"
SPEED_OF_LIGHT_KM_S = 299792.458


def verify_file_sha256(path: str, expected_sha: str) -> bool:
    """Compute sha256 of file and verify against expected hash."""
    if not os.path.exists(path):
        return False
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest().lower() == expected_sha.lower()


@dataclass(frozen=True)
class BackgroundCosmology:
    """Standard FLRW background parameters."""
    H0: float = 73.4
    Omega_m: float = 0.334
    DeltaOmega_k: float = 0.0

    @property
    def Omega_de(self) -> float:
        return 1.0 - self.Omega_m - self.DeltaOmega_k

    def E(self, z: np.ndarray | float) -> np.ndarray | float:
        """Dimensionless expansion rate E(z) = H(z) / H0."""
        z = np.asarray(z)
        one_plus_z = 1.0 + z
        term_m = self.Omega_m * (one_plus_z ** 3)
        term_k = self.DeltaOmega_k * (one_plus_z ** 2)
        term_de = self.Omega_de
        val = np.maximum(term_m + term_k + term_de, 1e-12)
        return np.sqrt(val)

    def comoving_distance_mpc(self, z: np.ndarray) -> np.ndarray:
        """Line-of-sight comoving distance D_C(z) in Mpc."""
        z_arr = np.atleast_1d(z)
        res = np.zeros_like(z_arr, dtype=np.float64)
        c_over_H0 = SPEED_OF_LIGHT_KM_S / self.H0
        for i, z_val in enumerate(z_arr):
            if z_val <= 0:
                res[i] = 0.0
            else:
                integral, _ = integrate.quad(lambda zp: 1.0 / self.E(zp), 0.0, z_val, limit=100)
                res[i] = c_over_H0 * integral
        return res

    def luminosity_distance_mpc(self, z_hd: np.ndarray, z_hel: np.ndarray) -> np.ndarray:
        """Physical luminosity distance d_L in Mpc."""
        dc = self.comoving_distance_mpc(z_hd)
        if abs(self.DeltaOmega_k) < 1e-6:
            dm = dc
        elif self.DeltaOmega_k > 0:
            c_over_H0 = SPEED_OF_LIGHT_KM_S / self.H0
            sqrt_k = np.sqrt(self.DeltaOmega_k)
            dm = (c_over_H0 / sqrt_k) * np.sinh(sqrt_k * dc / c_over_H0)
        else:
            c_over_H0 = SPEED_OF_LIGHT_KM_S / self.H0
            sqrt_k = np.sqrt(-self.DeltaOmega_k)
            dm = (c_over_H0 / sqrt_k) * np.sin(sqrt_k * dc / c_over_H0)
        return (1.0 + z_hel) * dm


class SourceBoundPantheonOperator:
    """Source-bound observation operator for Pantheon+ SNe Ia.
    
    Loads exact 1,701 SNe data and covariance matrix, performs
    physical forward modeling and analytic marginalization of Delta M_0.
    """

    def __init__(
        self,
        data_path: str = PANTHEON_DATA_PATH,
        cov_path: str = PANTHEON_COV_PATH,
        verify_sha: bool = True,
        z_min: float = 0.01,
        z_max: float = 2.5,
    ) -> None:
        self.data_path = data_path
        self.cov_path = cov_path
        self.z_min = z_min
        self.z_max = z_max

        if verify_sha:
            if not verify_file_sha256(data_path, EXPECTED_DATA_SHA256):
                raise ValueError(f"Data file {data_path} failed SHA-256 verification!")
            if not verify_file_sha256(cov_path, EXPECTED_COV_SHA256):
                raise ValueError(f"Covariance file {cov_path} failed SHA-256 verification!")

        self._load_and_bind_sources()

    def _load_and_bind_sources(self) -> None:
        """Load 1701 rows and 1701x1701 covariance, select cosmologically valid SNe."""
        # Read header and data
        with open(self.data_path, "r") as f:
            header_line = f.readline().strip()
            cols = header_line.split()

        col_map = {name: i for i, name in enumerate(cols)}
        raw_table = np.genfromtxt(self.data_path, skip_header=1, dtype=None, encoding=None)

        self.full_n = len(raw_table)
        assert self.full_n == 1701, f"Expected 1701 rows, got {self.full_n}"

        # Extract columns
        self.cids = np.array([row[col_map["CID"]] for row in raw_table])
        self.z_hd = np.array([float(row[col_map["zHD"]]) for row in raw_table])
        self.z_hel = np.array([float(row[col_map["zHEL"]]) for row in raw_table])
        self.m_b_corr = np.array([float(row[col_map["m_b_corr"]]) for row in raw_table])
        self.is_calibrator = np.array([int(row[col_map["IS_CALIBRATOR"]]) for row in raw_table])
        
        ra_deg = np.array([float(row[col_map["RA"]]) for row in raw_table])
        dec_deg = np.array([float(row[col_map["DEC"]]) for row in raw_table])
        
        ra_rad = np.deg2rad(ra_deg)
        dec_rad = np.deg2rad(dec_deg)
        
        # Unit line-of-sight vectors (pointing from observer to source)
        self.n_hat_full = np.column_stack([
            np.cos(dec_rad) * np.cos(ra_rad),
            np.cos(dec_rad) * np.sin(ra_rad),
            np.sin(dec_rad)
        ])

        # Read covariance
        with open(self.cov_path, "r") as f:
            first_line = f.readline().strip()
            cov_dim = int(first_line)
            assert cov_dim == self.full_n, f"Cov dim {cov_dim} != {self.full_n}"
            cov_flat = np.fromfile(f, count=cov_dim * cov_dim, sep=" ", dtype=np.float64)
            self.cov_full = cov_flat.reshape((cov_dim, cov_dim))

        # Selection mask: cosmological Hubble flow (exclude calibrators and very low z)
        self.mask = (self.is_calibrator == 0) & (self.z_hd >= self.z_min) & (self.z_hd <= self.z_max)
        self.n_selected = int(np.sum(self.mask))

        self.z_hd_sel = self.z_hd[self.mask]
        self.z_hel_sel = self.z_hel[self.mask]
        self.m_b_corr_sel = self.m_b_corr[self.mask]
        self.n_hat_sel = self.n_hat_full[self.mask]
        self.cov_sel = self.cov_full[np.ix_(self.mask, self.mask)]

        # Precompute Cholesky of selected covariance
        self.cho_cov = np.linalg.cholesky(self.cov_sel)
        self.inv_cov = np.linalg.solve(self.cho_cov.T, np.linalg.solve(self.cho_cov, np.eye(self.n_selected)))

        # Precompute design matrix for constant offset Delta M_0 (vector of ones)
        self.one_vec = np.ones(self.n_selected, dtype=np.float64)
        self.inv_cov_one = self.inv_cov @ self.one_vec
        self.var_delta_M0 = 1.0 / np.dot(self.one_vec, self.inv_cov_one)

        # Precompute STF basis for vectorized directional projections
        nx = self.n_hat_sel[:, 0]
        ny = self.n_hat_sel[:, 1]
        nz = self.n_hat_sel[:, 2]
        self.sn_stf_basis = np.column_stack([
            nx**2 - nz**2,
            ny**2 - nz**2,
            2.0 * nx * ny,
            2.0 * nx * nz,
            2.0 * ny * nz,
        ])
        self.log_det_cov = float(2.0 * np.sum(np.log(np.diag(self.cho_cov))))
        self.log_prior_M0 = float(np.log(self.var_delta_M0))
        self.const_log_norm = self.log_det_cov + self.log_prior_M0 + (self.n_selected - 1) * np.log(2.0 * np.pi)

    def evaluate_model(
        self,
        theta_K: np.ndarray,  # 17-vector: [sigma_5, omega_3, A_3, beta_RM_3, beta_MO_3]
        psi: BackgroundCosmology,
    ) -> Tuple[float, float, float]:
        """Compute chi2 and marginalized log-likelihood for Pantheon+ SNe Ia.
        
        Returns:
            Tuple of (chi2, best_fit_delta_M0, log_likelihood)
        """
        assert len(theta_K) == 17, f"Expected 17 kinematic parameters, got {len(theta_K)}"
        sigma_5 = theta_K[0:5]      # STF5 Cartesian: (Sxx, Syy, Sxy, Sxz, Syz)
        A_3 = theta_K[8:11]         # Polar acceleration / curvature gradient A/(c*H)
        beta_MO_3 = theta_K[14:17]   # Matter-to-observer velocity beta_MO (dimensionless)

        # 1. Background isotropic luminosity distance in Mpc (with cosmology caching)
        if hasattr(self, "_last_psi") and self._last_psi == psi:
            dL_iso = self._last_dL_iso
            mu_iso = self._last_mu_iso
        else:
            dL_iso = psi.luminosity_distance_mpc(self.z_hd_sel, self.z_hel_sel)
            mu_iso = 5.0 * np.log10(dL_iso * 1e5)
            self._last_psi = psi
            self._last_dL_iso = dL_iso
            self._last_mu_iso = mu_iso

        # 2. Covariant anisotropic departure delta_mu(n_hat)
        # Leading directional Hubble modulation: H_loc(n) = H0 [ 1 + n^T S n - n . beta_MO - n . A / (c H0) ]
        # mu = mu_iso - (5 / ln 10) * [ n^T S n - n . beta_MO - n . A ]
        factor = 5.0 / np.log(10.0)

        # Vectorized directional projections via precomputed basis
        shear_proj = self.sn_stf_basis @ sigma_5
        boost_proj = self.n_hat_sel @ beta_MO_3
        accel_proj = self.n_hat_sel @ A_3

        delta_mu_aniso = -factor * (shear_proj - boost_proj - accel_proj)
        mu_pred_no_offset = mu_iso + delta_mu_aniso

        # 3. Residual vector without offset
        res_raw = self.m_b_corr_sel - mu_pred_no_offset

        # 4. Analytic Schur marginalization for Delta M_0
        best_fit_M0 = float(np.dot(self.inv_cov_one, res_raw) * self.var_delta_M0)
        res_eff = res_raw - best_fit_M0

        # Effective chi2
        chi2 = float(np.dot(res_eff, self.inv_cov @ res_eff))
        log_like = -0.5 * (chi2 + self.const_log_norm)

        return chi2, best_fit_M0, log_like

    @property
    def metadata(self) -> ObservationSourceMetadata:
        return ObservationSourceMetadata(
            source_id="Pantheon_Plus_SH0ES",
            product_name="Pantheon+SH0ES Supernovae Ia",
            catalog_or_data_path=self.data_path,
            covariance_path=self.cov_path,
            n_total_objects=self.full_n,
            n_selected_objects=self.n_selected,
            selection_rule="IS_CALIBRATOR == 0 and z_min <= z_hd <= z_max",
            coordinate_frame=CoordinateFrame.ICRS,
            units="mag",
            estimator_type=EstimatorType.ANALYTIC_MARGINALIZED_DISTANCE,
            window_or_mask_id="PantheonPlus_z0.01_2.5_cut",
            covariance_id="Pantheon+SH0ES_STAT+SYS",
            verified_sha256=EXPECTED_DATA_SHA256,
            is_synthetic=False,
        )

    @property
    def functional_spec(self) -> PhysicalFunctionalSpec:
        return PhysicalFunctionalSpec(
            name="distance_modulus_quadrupole_dipole",
            tensor_rank=2,
            parity="even",
            so3_representation="2+ direct sum 1-",
            units="mag",
            parameter_dependence=("sigma_ab", "beta_MO", "A", "psi"),
        )

    def evaluate_likelihood(
        self,
        theta_K: np.ndarray,
        psi: Optional[BackgroundCosmology] = None,
    ) -> Tuple[float, float]:
        if psi is None:
            psi = BackgroundCosmology()
        chi2, _, log_like = self.evaluate_model(theta_K, psi)
        return chi2, log_like

    def get_data_vector(self) -> np.ndarray:
        return self.m_b_corr_sel

    def get_covariance_matrix(self) -> np.ndarray:
        return self.cov_sel
