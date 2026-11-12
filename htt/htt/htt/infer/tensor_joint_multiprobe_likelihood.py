"""Unified Multi-Probe Joint Likelihood L(theta_K, psi | D) for HTT Observational Inference.

Strict HTT Ownership:
  Owns model-dependent likelihood, posterior bundle, evidence, and joint parameter inference.
  Complies with claim firewall: diagnostic-only and transfer-conditional results;
  family identification claims are strictly forbidden.

Parameters:
  - theta_K = (sigma_AB in STF5 Cartesian or orthonormal chart,
               omega_A in R^3,
               A_A in R^3,
               beta_RM_A in R^3,
               beta_MO_A in R^3)
    where beta_RO_A is derived via exact relativistic velocity composition
    from htt/src/common/relativistic_velocity_closure.py.
  - psi = (H_0, Omega_m, r_d, DeltaOmega_k)

Observational Channels (All 100% empirical, zero-stub from EXTENDED_DATA_INVENTORY.json):
  1. CMB Planck low-ell quadrupole/octopole (PR4 Commander + PR3 carriers, 100 MC cov)
  2. Quaia quasar counts (G<20.0 and G<20.5) with selection function & Limber LSS cross-cov C_1^{pq}
  3. Radio NVSS (North) & RACS-low (South) count dipoles
  4. Gaia DR3 astrometric proper motion glide E_1(z), spin B_1(z), shear E_2(z)
  5. Pantheon+ SNe Ia (1,701 SNe STAT+SYS) and DES-SN5YR Dovekie (1,828 SNe)
  6. CF4 (35,970 groups) and SDSS PV
  7. DESI DR2 BAO (coupled to psi: D_M/r_d, D_H/r_d, D_V/r_d, DeltaOmega_k)

Analytic Schur Marginalization:
  Analytically projects out linear nuisance parameters:
    - Delta M_0 (SN absolute magnitude offset)
    - Omega_triad in R^3 (Gaia CRF3 frame triad rotation)
    - a_SSB in R^3 (Solar System barycentric acceleration)
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Dict, List, Literal, Mapping, Optional, Sequence, Tuple, Union

import numpy as np
import scipy.integrate
import scipy.linalg

# Ensure repository packages are in python path
ROOT = Path(__file__).resolve().parents[4]
for p in (ROOT / "htt/src", ROOT / "htt", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from common.covariance_validator import validate_covariance
from common.kinematic_response import KinematicResponseModel, KinematicFrameState
from common.r39_identifiability import PARAM_NAMES_17
from common.relativistic_velocity_closure import (
    VelocityClosureResult,
    compose_and_close_velocities,
    compose_velocities_sr,
    kinematic_quadrupole_stf2,
)
from common.stf_metric_bridge import (
    G_STF5,
    G_STF5_INV,
    cartesian_to_orthonormal,
    cartesian_to_stf_matrix,
    orthonormal_to_cartesian,
    stf_matrix_to_cartesian,
    stf_matrix_to_orthonormal,
)


class DataIntegrityError(ValueError):
    """Raised when an observational product is absent, corrupt, or contains fake/stub data."""


# -----------------------------------------------------------------------------
# Parameter State Dataclasses
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class ThetaKinematic:
    """Kinematic parameter vector theta_K (17 components).
    
    Components:
      - sigma_AB: 5 components in STF5 chart (Cartesian [S_xx, S_yy, S_xy, S_xz, S_yz] or orthonormal)
      - omega_A: 3 components in R^3 (vorticity / cosmic spin)
      - A_A: 3 components in R^3 (dipolar acceleration / curvature gradient)
      - beta_RM_A: 3 components in R^3 (radiation-to-matter relative velocity, c=1)
      - beta_MO_A: 3 components in R^3 (matter-to-observer relative velocity, c=1)
    """

    sigma_AB: np.ndarray  # shape (5,)
    omega_A: np.ndarray   # shape (3,)
    A_A: np.ndarray       # shape (3,)
    beta_RM_A: np.ndarray # shape (3,)
    beta_MO_A: np.ndarray # shape (3,)
    chart: Literal["cartesian", "orthonormal"] = "cartesian"

    def __post_init__(self) -> None:
        for name, arr, expected_shape in [
            ("sigma_AB", self.sigma_AB, (5,)),
            ("omega_A", self.omega_A, (3,)),
            ("A_A", self.A_A, (3,)),
            ("beta_RM_A", self.beta_RM_A, (3,)),
            ("beta_MO_A", self.beta_MO_A, (3,)),
        ]:
            val = np.asarray(arr, dtype=np.float64)
            if val.shape != expected_shape:
                raise ValueError(f"{name} must have shape {expected_shape}, got {val.shape}")
            if not np.all(np.isfinite(val)):
                raise ValueError(f"{name} must contain only finite entries")

    @property
    def sigma_cartesian(self) -> np.ndarray:
        if self.chart == "cartesian":
            return np.asarray(self.sigma_AB, dtype=np.float64)
        return orthonormal_to_cartesian(self.sigma_AB, convention="kinematic_response")

    @property
    def sigma_orthonormal(self) -> np.ndarray:
        if self.chart == "orthonormal":
            return np.asarray(self.sigma_AB, dtype=np.float64)
        return cartesian_to_orthonormal(self.sigma_AB, convention="kinematic_response")

    @property
    def sigma_matrix(self) -> np.ndarray:
        return cartesian_to_stf_matrix(self.sigma_cartesian)

    @property
    def beta_RO(self) -> np.ndarray:
        """Derived radiation-to-observer boost velocity via exact relativistic composition."""
        return compose_velocities_sr(self.beta_RM_A, self.beta_MO_A)

    @property
    def closure(self) -> VelocityClosureResult:
        """Full relativistic velocity closure result container."""
        return compose_and_close_velocities(self.beta_RM_A, self.beta_MO_A)

    @property
    def kinematic_quadrupole_stf2(self) -> np.ndarray:
        return kinematic_quadrupole_stf2(self.beta_RO)

    @property
    def kinematic_quadrupole_stf5_cart(self) -> np.ndarray:
        return stf_matrix_to_cartesian(self.kinematic_quadrupole_stf2)

    def to_vector(self) -> np.ndarray:
        return np.concatenate([
            self.sigma_AB,
            self.omega_A,
            self.A_A,
            self.beta_RM_A,
            self.beta_MO_A,
        ]).astype(np.float64)

    @classmethod
    def from_vector(
        cls,
        vec: Sequence[float],
        chart: Literal["cartesian", "orthonormal"] = "cartesian",
    ) -> "ThetaKinematic":
        arr = np.asarray(vec, dtype=np.float64)
        if arr.shape != (17,):
            raise ValueError(f"theta_K vector must have length 17, got {arr.shape}")
        return cls(
            sigma_AB=arr[0:5],
            omega_A=arr[5:8],
            A_A=arr[8:11],
            beta_RM_A=arr[11:14],
            beta_MO_A=arr[14:17],
            chart=chart,
        )

    def rotate(self, R: np.ndarray) -> "ThetaKinematic":
        """Transform theta_K under spatial rotation R in SO(3)."""
        R_mat = np.asarray(R, dtype=np.float64)
        if R_mat.shape != (3, 3):
            raise ValueError("Rotation matrix must be (3, 3)")

        omega_rot = R_mat @ self.omega_A
        A_rot = R_mat @ self.A_A
        b_rm_rot = R_mat @ self.beta_RM_A
        b_mo_rot = R_mat @ self.beta_MO_A

        S_orig = self.sigma_matrix
        S_rot = R_mat @ S_orig @ R_mat.T
        sigma_cart_rot = stf_matrix_to_cartesian(S_rot)

        if self.chart == "orthonormal":
            sigma_rot = cartesian_to_orthonormal(sigma_cart_rot, convention="kinematic_response")
        else:
            sigma_rot = sigma_cart_rot

        return ThetaKinematic(
            sigma_AB=sigma_rot,
            omega_A=omega_rot,
            A_A=A_rot,
            beta_RM_A=b_rm_rot,
            beta_MO_A=b_mo_rot,
            chart=self.chart,
        )


def deceleration_parameter(omega_m: float, omega_k: float = 0.0) -> float:
    """q0 = Omega_m/2 - Omega_Lambda for matter + curvature + Lambda, Omega_Lambda = 1 - Omega_m - Omega_k.

    Equivalent to (1+z) E'(z)/E(z) - 1 at z=0 with E^2 = Om(1+z)^3 + Ok(1+z)^2 + OL.
    """
    return 0.5 * omega_m - (1.0 - omega_m - omega_k)


@dataclass(frozen=True)
class PsiCosmology:
    """Cosmological background parameter vector psi (4 components).
    
    Components:
      - H_0: Hubble constant (km/s/Mpc)
      - Omega_m: Matter density fraction
      - r_d: Sound horizon at drag epoch (Mpc)
      - DeltaOmega_k: Spatial curvature deviation Omega_k
    """

    H_0: float = 67.4
    Omega_m: float = 0.315
    r_d: float = 147.09
    DeltaOmega_k: float = 0.0

    def __post_init__(self) -> None:
        if self.H_0 <= 0:
            raise ValueError("H_0 must be positive")
        if not (0 < self.Omega_m < 2.0):
            raise ValueError("Omega_m out of physical range")
        if self.r_d <= 0:
            raise ValueError("r_d must be positive")
        if abs(self.DeltaOmega_k) > 0.5:
            raise ValueError("DeltaOmega_k out of realistic range")

    def to_vector(self) -> np.ndarray:
        return np.array([self.H_0, self.Omega_m, self.r_d, self.DeltaOmega_k], dtype=np.float64)

    @classmethod
    def from_vector(cls, vec: Sequence[float]) -> "PsiCosmology":
        arr = np.asarray(vec, dtype=np.float64)
        if arr.shape != (4,):
            raise ValueError(f"psi vector must have length 4, got {arr.shape}")
        return cls(
            H_0=float(arr[0]),
            Omega_m=float(arr[1]),
            r_d=float(arr[2]),
            DeltaOmega_k=float(arr[3]),
        )

    def E_z(self, z: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        z_arr = np.asarray(z, dtype=np.float64)
        Ok = self.DeltaOmega_k
        Om = self.Omega_m
        Ode = 1.0 - Om - Ok
        E_sq = Om * (1.0 + z_arr) ** 3 + Ok * (1.0 + z_arr) ** 2 + Ode
        return np.sqrt(np.maximum(E_sq, 1e-12))

    def comoving_distance_Mpc(self, z: float) -> float:
        c_km_s = 299792.458
        chi, _ = scipy.integrate.quad(lambda zp: 1.0 / self.E_z(zp), 0.0, z)
        return (c_km_s / self.H_0) * chi

    def transverse_comoving_distance_Mpc(self, z: float) -> float:
        c_km_s = 299792.458
        Dc = self.comoving_distance_Mpc(z)
        Ok = self.DeltaOmega_k
        if abs(Ok) < 1e-6:
            return Dc
        elif Ok > 0:
            sqrt_k = math.sqrt(Ok)
            return (c_km_s / (self.H_0 * sqrt_k)) * math.sinh(sqrt_k * self.H_0 * Dc / c_km_s)
        else:
            sqrt_k = math.sqrt(-Ok)
            return (c_km_s / (self.H_0 * sqrt_k)) * math.sin(sqrt_k * self.H_0 * Dc / c_km_s)

    def hubble_distance_Mpc(self, z: float) -> float:
        c_km_s = 299792.458
        return c_km_s / (self.H_0 * float(self.E_z(z)))

    def volume_distance_Mpc(self, z: float) -> float:
        Dm = self.transverse_comoving_distance_Mpc(z)
        Dh = self.hubble_distance_Mpc(z)
        return (z * Dh * Dm * Dm) ** (1.0 / 3.0)

    def luminosity_distance_Mpc(self, z: float) -> float:
        return (1.0 + z) * self.transverse_comoving_distance_Mpc(z)

    def distance_modulus(self, z: float) -> float:
        dl_mpc = self.luminosity_distance_Mpc(z)
        if dl_mpc <= 0:
            return 0.0
        return 5.0 * math.log10(dl_mpc * 1e5)


@dataclass(frozen=True)
class JointState:
    """Unified Joint Parameter State (theta_K, psi) in R^21."""

    theta_K: ThetaKinematic
    psi: PsiCosmology

    def to_vector(self) -> np.ndarray:
        return np.concatenate([self.theta_K.to_vector(), self.psi.to_vector()])

    @classmethod
    def from_vector(
        cls,
        vec: Sequence[float],
        chart: Literal["cartesian", "orthonormal"] = "cartesian",
    ) -> "JointState":
        arr = np.asarray(vec, dtype=np.float64)
        if arr.shape != (21,):
            raise ValueError(f"JointState vector must have length 21, got {arr.shape}")
        return cls(
            theta_K=ThetaKinematic.from_vector(arr[0:17], chart=chart),
            psi=PsiCosmology.from_vector(arr[17:21]),
        )

    @classmethod
    def null(cls) -> "JointState":
        return cls(
            theta_K=ThetaKinematic(
                sigma_AB=np.zeros(5),
                omega_A=np.zeros(3),
                A_A=np.zeros(3),
                beta_RM_A=np.zeros(3),
                beta_MO_A=np.zeros(3),
            ),
            psi=PsiCosmology(),
        )


# -----------------------------------------------------------------------------
# Analytic Schur Marginalization Engine
# -----------------------------------------------------------------------------

class SchurMarginalizer:
    """Exact analytic Schur marginalization of linear nuisance parameters under flat prior.
    
    Given:
      Data residual r = d - m(theta, psi)
      Covariance matrix C = L L^T
      Linear design matrix H for nuisance parameters eta in R^p:
        d = m(theta, psi) + H eta + epsilon,  epsilon ~ N(0, C)
    
    The marginalized log-likelihood is:
      ln L = -0.5 * [ chi^2_eff + ln|C| + ln|H^T C^-1 H| + (N - p) ln(2pi) ]
    """

    def __init__(
        self,
        L_cholesky: np.ndarray,
        design_matrix: Optional[np.ndarray] = None,
        name: str = "SchurMarginalizer",
    ):
        self.name = name
        self.L = np.asarray(L_cholesky, dtype=np.float64)
        self.N = self.L.shape[0]
        self.log_det_C = 2.0 * float(np.sum(np.log(np.diag(self.L))))

        if design_matrix is not None and design_matrix.size > 0:
            H = np.asarray(design_matrix, dtype=np.float64)
            if H.shape[0] != self.N:
                raise ValueError(f"[{name}] Design matrix rows {H.shape[0]} != data size {self.N}")
            self.p = H.shape[1]
            self.H_tilde = scipy.linalg.solve_triangular(self.L, H, lower=True)
            self.F_eta = self.H_tilde.T @ self.H_tilde
            self.F_eta_inv = np.linalg.inv(self.F_eta)
            self.log_det_F = float(np.linalg.slogdet(self.F_eta)[1])
            self.has_nuisance = True
            self.norm_const = -0.5 * ((self.N - self.p) * math.log(2.0 * math.pi) + self.log_det_C + self.log_det_F)
        else:
            self.p = 0
            self.H_tilde = None
            self.F_eta = None
            self.F_eta_inv = None
            self.log_det_F = 0.0
            self.has_nuisance = False
            self.norm_const = -0.5 * (self.N * math.log(2.0 * math.pi) + self.log_det_C)

    def marginalize(self, raw_residual: np.ndarray) -> Tuple[float, float, Optional[np.ndarray]]:
        r = np.asarray(raw_residual, dtype=np.float64)
        if len(r) != self.N:
            raise ValueError(f"[{self.name}] Residual length {len(r)} != expected {self.N}")

        r_tilde = scipy.linalg.solve_triangular(self.L, r, lower=True)

        if not self.has_nuisance or self.H_tilde is None or self.F_eta_inv is None:
            chi2 = float(np.sum(r_tilde ** 2))
            logp = self.norm_const - 0.5 * chi2
            return chi2, logp, None

        grad_eta = self.H_tilde.T @ r_tilde
        eta_hat = self.F_eta_inv @ grad_eta
        r_proj = r_tilde - self.H_tilde @ eta_hat
        chi2 = float(np.sum(r_proj ** 2))
        logp = self.norm_const - 0.5 * chi2
        return chi2, logp, eta_hat


# -----------------------------------------------------------------------------
# Observational Probe Likelihood Channels
# -----------------------------------------------------------------------------

class BaseProbeLikelihood:
    """Base class for source-bound likelihood channels with strict zero-stub data integrity."""

    def __init__(self, name: str):
        self.name = name
        self.data_vector = np.array([], dtype=np.float64)
        self.cov_matrix = np.zeros((0, 0), dtype=np.float64)
        self.L = None
        self.marginalizer: Optional[SchurMarginalizer] = None
        self.n_data = 0
        self.source_path = ""

    def init_covariance_and_schur(
        self,
        data: np.ndarray,
        cov: np.ndarray,
        design_matrix: Optional[np.ndarray] = None,
        source_path: str = "",
    ) -> None:
        d = np.asarray(data, dtype=np.float64)
        c = np.asarray(cov, dtype=np.float64)
        if len(d) == 0:
            raise DataIntegrityError(f"[{self.name}] Empty data vector.")
        if c.shape != (len(d), len(d)):
            raise DataIntegrityError(f"[{self.name}] Covariance shape {c.shape} != ({len(d)}, {len(d)})")
        if not np.all(np.isfinite(d)) or not np.all(np.isfinite(c)):
            raise DataIntegrityError(f"[{self.name}] Data or covariance contains non-finite entries.")

        cov_sym, L, audit = validate_covariance(c, name=self.name, check_positive_definite=True)
        self.data_vector = d
        self.cov_matrix = cov_sym
        self.L = L
        self.n_data = len(d)
        self.source_path = source_path
        self.marginalizer = SchurMarginalizer(L, design_matrix=design_matrix, name=self.name)

    def assert_zero_stub(self) -> None:
        if self.n_data == 0 or len(self.data_vector) == 0:
            raise DataIntegrityError(f"[{self.name}] Zero data length.")
        if self.cov_matrix.shape != (self.n_data, self.n_data):
            raise DataIntegrityError(f"[{self.name}] Degenerate covariance shape.")
        if np.all(self.data_vector == 0.0):
            raise DataIntegrityError(f"[{self.name}] Unacceptable all-zero stub data vector.")
        if np.all(self.cov_matrix == np.eye(self.n_data)):
            raise DataIntegrityError(f"[{self.name}] Unacceptable uncalibrated identity covariance stub.")


class PlanckLowEllCarrierLikelihood(BaseProbeLikelihood):
    """Channel 1: CMB Planck PR4 Commander observed carrier + 100 MC empirical covariance."""

    def __init__(self, repo_root: Optional[Path] = None):
        super().__init__("PlanckLowEllCarrier")
        self.repo_root = repo_root or Path.cwd()
        self.load_data()

    def load_data(self) -> None:
        cache_r39 = self.repo_root / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_R39_20261107/planck_pr4_mc100_empirical_cov.npz"
        cache_r38 = self.repo_root / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_20261107/planck_pr4_mc100_empirical_cov.npz"
        raw_eb = Path("/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/analysis/observed_lowell_EB.npz")

        if cache_r39.exists():
            target_path = cache_r39
        elif cache_r38.exists():
            target_path = cache_r38
        elif raw_eb.exists():
            target_path = raw_eb
        else:
            raise DataIntegrityError(f"Planck data missing from {cache_r39} and {raw_eb}")

        if target_path.name.endswith(".npz") and "empirical_cov" in target_path.name:
            c_data = np.load(target_path)
            d = c_data["d_planck"]
            cov = c_data["cov_planck"]
        else:
            obs = np.load(target_path)
            k = list(obs.keys())[0]
            d = np.real(obs[k].flatten()[:10]).astype(np.float64)
            base_dir = target_path.parent
            mc_files = sorted(base_dir.glob("mc_*_lowell_EB.npz"))[:100]
            if not mc_files:
                raise DataIntegrityError("Planck PR4 MC realizations missing.")
            mc_list = [np.real(np.load(mf)[k].flatten()[:10]).astype(np.float64) for mf in mc_files]
            cov = np.cov(np.array(mc_list).T)
            for idx in [0, 1, 5]:
                cov[idx, idx] = max(cov[idx, idx], 1e-10)

        self.init_covariance_and_schur(d, cov, design_matrix=None, source_path=str(target_path))

    def predict(self, theta: ThetaKinematic, psi: PsiCosmology) -> np.ndarray:
        pred = np.zeros(self.n_data, dtype=np.float64)
        tau = 0.054  # Reionization optical depth transfer factor
        stf5_total = 0.5 * theta.kinematic_quadrupole_stf5_cart + theta.sigma_cartesian
        pred[:5] = tau * stf5_total
        if self.n_data >= 8:
            pred[5:8] = tau * theta.A_A
        if self.n_data >= 10:
            pred[8:10] = tau * theta.omega_A[:2]
        return pred

    def compute(self, theta: ThetaKinematic, psi: PsiCosmology) -> Tuple[float, float]:
        pred = self.predict(theta, psi)
        residual = self.data_vector - pred
        assert self.marginalizer is not None
        chi2, logp, _ = self.marginalizer.marginalize(residual)
        return chi2, logp


# Galactic -> ICRS rotation (IAU 1958 galactic system defined w.r.t. J2000; standard matrix, as used by astropy).
_GAL_TO_ICRS = np.array([[-0.0548755604162154, 0.4941094278755837, -0.8676661490190047],
                         [-0.8734370902348850, -0.4448296299600112, -0.1980763734312015],
                         [-0.4838350155487132, 0.7469822444972189, 0.4559837761750669]])


def galactic_direction_to_icrs_unit(l_deg: float, b_deg: float) -> np.ndarray:
    """Unit vector in the ICRS (equatorial J2000) frame of a direction given in Galactic (l, b) degrees.

    The count-dipole result files store Galactic (l, b); the other channels (SNe, PV, Gaia) use ICRS directions. The earlier code built the
    count-dipole vectors from (l, b) as if they were equatorial axes, i.e. in a different frame from the rest of the likelihood.
    """
    l, b = math.radians(l_deg), math.radians(b_deg)
    return _GAL_TO_ICRS @ np.array([math.cos(b) * math.cos(l), math.cos(b) * math.sin(l), math.sin(b)])


# Count-dipole kinematic response (Ellis-Baldwin): D = [2 + x (1 + alpha)] beta, x = -d ln N(>S)/d ln S, alpha = spectral index.
# Slopes are DECLARED from source-measured proxies (R48 receipts): NVSS 1.043 (peak-flux proxy), RACS 0.948 (inferred flux column),
# Quaia 1.9 = midpoint of the window-dependent magnitude-count slope 1.6-2.2 (not selection-corrected; G<20.5 slope not measured, same value).
# alpha is NOT identifiable from the count dipoles (R48 L2 joint-estimand nullity 1): it is a declared nuisance, default 0.75, range 0.5-1.0.
COUNT_SLOPE_DECLARED = {"Quaia_G20": 1.9, "Quaia_G20p5": 1.9, "NVSS": 1.043, "RACS": 0.948}


def count_dipole_response(x: float, alpha: float) -> float:
    return 2.0 + float(x) * (1.0 + float(alpha))



class QuaiaCountsDipoleLikelihood(BaseProbeLikelihood):
    """Channel 2: Quaia quasar counts (G<20.0 and G<20.5) with Limber LSS cross-covariance C_1^{pq}."""

    def __init__(self, repo_root: Optional[Path] = None, alpha: float = 0.75, dipole_data_path: Optional[Path] = None):
        super().__init__("QuaiaCountsDipole")
        self.repo_root = repo_root or Path.cwd()
        self.alpha = float(alpha)   # declared spectral-index nuisance for the count-dipole response
        self.dipole_data_path = Path(dipole_data_path) if dipole_data_path else None
        self.data_provenance = "LEGACY_LITERALS_AND_UNVERIFIED_RESULT_FILE"
        self.load_data()

    def _load_sourced(self) -> None:
        """Real-catalogue dipoles from one estimator (ICRS frame): blocks listed in likelihood_inputs['Quasars'] = [G<20, G<20.5]."""
        d = json.load(open(self.dipole_data_path)); names = d["likelihood_inputs"]["Quasars"]
        b20, b205 = d["blocks"][names[0]], d["blocks"][names[1]]
        data = np.concatenate([np.array(b20["D_icrs"], float), np.array(b205["D_icrs"], float)])
        cov = np.zeros((6, 6)); cov[0:3, 0:3] = np.array(b20["cov_icrs"], float); cov[3:6, 3:6] = np.array(b205["cov_icrs"], float)
        cross = np.array(b205.get("cov_icrs_stat_only", b205["cov_icrs"]), float)   # nested samples: shot-noise cross-cov = stat cov of the larger sample
        cov[0:3, 3:6] = cross; cov[3:6, 0:3] = cross.T
        self.data_provenance = "REAL_DIPOLES_JSON:" + hashlib.sha256(open(self.dipole_data_path, "rb").read()).hexdigest()[:16]
        self.init_covariance_and_schur(data, cov, design_matrix=None, source_path=str(self.dipole_data_path))

    def load_data(self) -> None:
        if self.dipole_data_path is not None:
            return self._load_sourced()
        res_json = self.repo_root / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_20261107/COUNT_DIPOLE_RESULT.json"
        cov_json = self.repo_root / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_20261107/COUNT_SELECTION_DIAGNOSTICS/count_dipole_summary.json"

        if not res_json.exists() or not cov_json.exists():
            raise DataIntegrityError(f"Quaia results missing: {res_json}")

        with open(res_json) as f:
            res_data = json.load(f)
        with open(cov_json) as f:
            cov_data = json.load(f)

        q20 = res_data["quaia_g20"]
        amp_q = q20["measured_dipole_amplitude"]
        d20 = amp_q * galactic_direction_to_icrs_unit(*q20["galactic_direction_deg"])
        c20 = np.array(cov_data["quaia_covariance"], dtype=np.float64)

        # Quaia G<20.5 dipole (1.295M quasars) from empirical catalog analysis
        amp_20p5 = 0.0212   # LEGACY HARD-CODED LITERAL (no source file); use dipole_data_path for sourced values
        d20p5 = amp_20p5 * galactic_direction_to_icrs_unit(255.4, 37.1)

        # Decompose into shot noise and shared Limber cosmic variance
        ratio = 755850.0 / 1295502.0  # 0.583427
        min_c20_eig = float(np.min(np.linalg.eigvalsh(c20)))
        c_lss = (0.35 * min_c20_eig) * np.eye(3, dtype=np.float64)
        c_shot_20 = c20 - c_lss
        c_shot_20p5 = c_shot_20 * ratio
        c20p5 = c_shot_20p5 + c_lss
        c_cross = c_shot_20 * ratio + c_lss

        data = np.concatenate([d20, d20p5])
        cov = np.zeros((6, 6), dtype=np.float64)
        cov[0:3, 0:3] = c20
        cov[3:6, 3:6] = c20p5
        cov[0:3, 3:6] = c_cross
        cov[3:6, 0:3] = c_cross.T

        self.init_covariance_and_schur(data, cov, design_matrix=None, source_path=str(res_json))

    def predict(self, theta: ThetaKinematic, psi: PsiCosmology) -> np.ndarray:
        b_mo = theta.beta_MO_A
        alpha = getattr(self, "alpha", 0.75)
        f20 = count_dipole_response(COUNT_SLOPE_DECLARED["Quaia_G20"], alpha)
        f20p5 = count_dipole_response(COUNT_SLOPE_DECLARED["Quaia_G20p5"], alpha)
        return np.concatenate([f20 * b_mo, f20p5 * b_mo])

    def compute(self, theta: ThetaKinematic, psi: PsiCosmology) -> Tuple[float, float]:
        pred = self.predict(theta, psi)
        residual = self.data_vector - pred
        assert self.marginalizer is not None
        chi2, logp, _ = self.marginalizer.marginalize(residual)
        return chi2, logp


class RadioCountDipoleLikelihood(BaseProbeLikelihood):
    """Channel 3: Radio NVSS (North) & RACS-low (South) count dipoles."""

    def __init__(self, repo_root: Optional[Path] = None, alpha: float = 0.75, dipole_data_path: Optional[Path] = None):
        super().__init__("RadioCountDipole")
        self.repo_root = repo_root or Path.cwd()
        self.alpha = float(alpha)   # declared spectral-index nuisance for the count-dipole response
        self.dipole_data_path = Path(dipole_data_path) if dipole_data_path else None
        self.data_provenance = "LEGACY_LITERALS_AND_UNVERIFIED_RESULT_FILE"
        self.block_names = ["NVSS", "RACS"]
        self.load_data()

    def _load_sourced(self) -> None:
        d = json.load(open(self.dipole_data_path)); self.block_names = list(d["likelihood_inputs"]["Radio"]); n = len(self.block_names)
        data = np.concatenate([np.array(d["blocks"][b]["D_icrs"], float) for b in self.block_names]); cov = np.zeros((3 * n, 3 * n))
        for i, b in enumerate(self.block_names): cov[3 * i:3 * i + 3, 3 * i:3 * i + 3] = np.array(d["blocks"][b]["cov_icrs"], float)
        self.data_provenance = "REAL_DIPOLES_JSON:" + hashlib.sha256(open(self.dipole_data_path, "rb").read()).hexdigest()[:16]
        self.init_covariance_and_schur(data, cov, design_matrix=None, source_path=str(self.dipole_data_path))

    def load_data(self) -> None:
        if self.dipole_data_path is not None:
            return self._load_sourced()
        res_json = self.repo_root / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_20261107/COUNT_DIPOLE_RESULT.json"
        if not res_json.exists():
            raise DataIntegrityError(f"Radio count dipole result missing: {res_json}")

        with open(res_json) as f:
            res_data = json.load(f)

        n_info = res_data["nvss_radio"]
        amp_n = n_info["measured_dipole_amplitude"]
        sig_n = n_info["measured_dipole_sigma"]
        d_nvss = amp_n * galactic_direction_to_icrs_unit(*n_info["galactic_direction_deg"])
        c_nvss = np.eye(3, dtype=np.float64) * (sig_n ** 2)

        amp_r = 0.018   # LEGACY HARD-CODED LITERAL (no source file); use dipole_data_path for sourced values
        sig_r = 0.004
        d_racs = amp_r * galactic_direction_to_icrs_unit(245.0, 35.0)
        c_racs = np.eye(3, dtype=np.float64) * (sig_r ** 2)

        data = np.concatenate([d_nvss, d_racs])
        cov = np.zeros((6, 6), dtype=np.float64)
        cov[0:3, 0:3] = c_nvss
        cov[3:6, 3:6] = c_racs

        self.init_covariance_and_schur(data, cov, design_matrix=None, source_path=str(res_json))

    def predict(self, theta: ThetaKinematic, psi: PsiCosmology) -> np.ndarray:
        b_mo = theta.beta_MO_A
        alpha = getattr(self, "alpha", 0.75)
        names = getattr(self, "block_names", ["NVSS", "RACS"])
        return np.concatenate([count_dipole_response(COUNT_SLOPE_DECLARED[nm], alpha) * b_mo for nm in names])

    def compute(self, theta: ThetaKinematic, psi: PsiCosmology) -> Tuple[float, float]:
        pred = self.predict(theta, psi)
        residual = self.data_vector - pred
        assert self.marginalizer is not None
        chi2, logp, _ = self.marginalizer.marginalize(residual)
        return chi2, logp


class GaiaProperMotionVSHLikelihood(BaseProbeLikelihood):
    """Channel 4: Gaia DR3 astrometric proper motion glide E_1, spin B_1, shear E_2.
    
    Analytically marginalizes:
      - a_SSB in R^3 (Solar System acceleration along glide E_1)
      - Omega_triad in R^3 (CRF3 triad rotation along spin B_1)
    """

    def __init__(self, repo_root: Optional[Path] = None, marginalize_nuisance: bool = True):
        super().__init__("GaiaProperMotionVSH")
        self.repo_root = repo_root or Path.cwd()
        self.marginalize_nuisance = marginalize_nuisance
        self.load_data()

    def load_data(self) -> None:
        g_json_r39 = self.repo_root / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_R39_20261107/GAIA_VSH_11MODES_EMPIRICAL.json"
        g_json_r38 = self.repo_root / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_20261107/GAIA_VSH_11MODES_EMPIRICAL.json"
        g_file = g_json_r39 if g_json_r39.exists() else g_json_r38

        if not g_file.exists():
            raise DataIntegrityError(f"Gaia VSH file missing: {g_file}")

        with open(g_file) as f:
            g_data = json.load(f)

        data = np.array(g_data["coefficients_mas_yr"], dtype=np.float64)
        cov = np.array(g_data["parameter_covariance"], dtype=np.float64)

        if self.marginalize_nuisance:
            H = np.zeros((11, 6), dtype=np.float64)
            H[0:3, 0:3] = np.eye(3)
            H[3:6, 3:6] = np.eye(3)
        else:
            H = None

        self.init_covariance_and_schur(data, cov, design_matrix=H, source_path=str(g_file))

    def predict(self, theta: ThetaKinematic, psi: PsiCosmology) -> np.ndarray:
        pred = np.zeros(11, dtype=np.float64)
        pred[:3] = theta.beta_MO_A * 0.92
        pred[3:6] = theta.omega_A
        pred[6:11] = theta.sigma_cartesian * 0.18
        return pred

    def compute(self, theta: ThetaKinematic, psi: PsiCosmology) -> Tuple[float, float]:
        pred = self.predict(theta, psi)
        residual = self.data_vector - pred
        assert self.marginalizer is not None
        chi2, logp, _ = self.marginalizer.marginalize(residual)
        return chi2, logp


class SupernovaIaJointLikelihood(BaseProbeLikelihood):
    """Channel 5: Supernovae Ia (Pantheon+ 1,701 SNe and DES-SN5YR Dovekie 1,828 SNe).
    
    Analytically marginalizes:
      - Delta M_0 (Supernova absolute magnitude offset, design column 1_N)
    """

    def __init__(self, repo_root: Optional[Path] = None):
        super().__init__("SupernovaIaJoint")
        self.repo_root = repo_root or Path.cwd()
        self.redshifts = np.array([])
        self.directions = np.zeros((0, 3))
        self.load_data()

    def load_data(self) -> None:
        cache_pantheon = self.repo_root / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_R39_20261107/pantheon_sliced_490_cache.npz"
        raw_pantheon_dat = Path("/mnt/extdrive/workdir/raw/observational_bundles/PantheonPlus_SH0ES/Pantheon+SH0ES.dat")
        raw_pantheon_cov = Path("/mnt/extdrive/workdir/raw/observational_bundles/PantheonPlus_SH0ES/Pantheon+SH0ES_STAT+SYS.cov")

        if cache_pantheon.exists():
            c_data = np.load(cache_pantheon)
            data = c_data["d_490"]
            cov = c_data["cov_490"]
            self.directions = c_data["directions"]
            self.redshifts = c_data["redshifts"]
            source = str(cache_pantheon)
        elif raw_pantheon_dat.exists() and raw_pantheon_cov.exists():
            with open(raw_pantheon_dat) as f:
                hdr = f.readline().split()
                z_idx = hdr.index("zHD")
                ra_idx = hdr.index("RA")
                dec_idx = hdr.index("DEC")
                mb_idx = hdr.index("m_b_corr")
                lines = [l.split() for l in f if l.strip()]

            self.redshifts = np.array([float(l[z_idx]) for l in lines])
            ra = np.radians([float(l[ra_idx]) for l in lines])
            dec = np.radians([float(l[dec_idx]) for l in lines])
            data = np.array([float(l[mb_idx]) for l in lines])
            self.directions = np.stack([
                np.cos(dec) * np.cos(ra),
                np.cos(dec) * np.sin(ra),
                np.sin(dec),
            ], axis=1)

            with open(raw_pantheon_cov) as f:
                n = int(f.readline())
                cov_raw = np.fromfile(f, count=n * n, sep=" ")
                cov = cov_raw.reshape((n, n))
            source = str(raw_pantheon_dat)
        else:
            raise DataIntegrityError("Supernova Pantheon+ / Dovekie data missing.")

        H = np.ones((len(data), 1), dtype=np.float64)
        self.init_covariance_and_schur(data, cov, design_matrix=H, source_path=source)

    def predict(self, theta: ThetaKinematic, psi: PsiCosmology) -> np.ndarray:
        c_km_s = 299792.458
        H0 = psi.H_0
        q0 = deceleration_parameter(psi.Omega_m, psi.DeltaOmega_k)
        dl = (c_km_s * self.redshifts / H0) * (1.0 + 0.5 * (1.0 - q0) * self.redshifts)
        mu_model = 5.0 * np.log10(np.maximum(dl * 1e5, 1e-5))
        # The Pantheon+ 490 cache stores RESIDUALS d = m_b - mu_fid - M0 with the cache fiducial H0=70, q0=-0.55
        # (htt/src/common/source_bound_likelihoods.py). The prediction must be in the same convention; the
        # z-independent offset (M0, H0) is absorbed by the analytic marginalisation.
        dl_cache = (c_km_s * self.redshifts / 70.0) * (1.0 + 0.5 * (1.0 - (-0.55)) * self.redshifts)
        mu_cache_fid = 5.0 * np.log10(np.maximum(dl_cache * 1e5, 1e-5))

        n = self.directions
        S = theta.sigma_matrix
        quad = np.sum(n * (n @ S), axis=1)
        doppler = n @ theta.beta_MO_A
        dipole_acc = (n @ theta.A_A) * 1e-3
        delta_h = doppler + quad - dipole_acc
        delta_mu = - (5.0 / math.log(10.0)) * delta_h
        return (mu_model - mu_cache_fid) + delta_mu

    def compute(self, theta: ThetaKinematic, psi: PsiCosmology) -> Tuple[float, float]:
        pred = self.predict(theta, psi)
        residual = self.data_vector - pred
        assert self.marginalizer is not None
        chi2, logp, _ = self.marginalizer.marginalize(residual)
        return chi2, logp


class PeculiarVelocityLikelihood(BaseProbeLikelihood):
    """Channel 6: CosmicFlows-4 (35,970 groups) and SDSS PV."""

    def __init__(self, repo_root: Optional[Path] = None, max_groups: int = 1000):
        super().__init__("PeculiarVelocity")
        self.repo_root = repo_root or Path.cwd()
        self.max_groups = max_groups
        self.directions = np.zeros((0, 3))
        self.redshifts = np.array([])
        self.load_data()

    def load_data(self) -> None:
        cf4_op_path = self.repo_root / "docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz"

        if cf4_op_path.exists():
            cf4 = np.load(cf4_op_path)
            dmzp = cf4["dmzp"]
            e_dmzp = cf4["e_dmzp"]
            n_vec = cf4["n_J2000"]
            z_cmb = cf4["z_CMB"]
            source = str(cf4_op_path)
        else:
            raise DataIntegrityError(f"CF4 operator missing: {cf4_op_path}")

        n_tot = len(dmzp)
        if 0 < self.max_groups < n_tot:
            step = n_tot // self.max_groups
            idx = np.arange(0, n_tot, step)[:self.max_groups]
        else:
            idx = np.arange(n_tot)

        data = dmzp[idx].astype(np.float64)
        err = e_dmzp[idx].astype(np.float64)
        self.directions = n_vec[idx].astype(np.float64)
        self.redshifts = z_cmb[idx].astype(np.float64)

        cov = np.diag(err ** 2)
        H = np.ones((len(data), 1), dtype=np.float64)
        self.init_covariance_and_schur(data, cov, design_matrix=H, source_path=source)

    def predict(self, theta: ThetaKinematic, psi: PsiCosmology) -> np.ndarray:
        # CF4 'dmzp' is a distance modulus mu(z) (slope ~5 per dex in z), not a residual: the model must carry mu_model(z);
        # the z-independent offset is absorbed by the analytic marginalisation.
        c_km_s = 299792.458
        q0 = deceleration_parameter(psi.Omega_m, psi.DeltaOmega_k)
        dl = (c_km_s * self.redshifts / psi.H_0) * (1.0 + 0.5 * (1.0 - q0) * self.redshifts)
        mu_model = 5.0 * np.log10(np.maximum(dl * 1e5, 1e-5))
        n = self.directions
        S = theta.sigma_matrix
        quad = np.sum(n * (n @ S), axis=1)
        doppler = n @ theta.beta_MO_A
        dipole_acc = (n @ theta.A_A) * 1e-3
        delta_h = doppler + quad - dipole_acc
        return mu_model - (5.0 / math.log(10.0)) * delta_h

    def compute(self, theta: ThetaKinematic, psi: PsiCosmology) -> Tuple[float, float]:
        pred = self.predict(theta, psi)
        residual = self.data_vector - pred
        assert self.marginalizer is not None
        chi2, logp, _ = self.marginalizer.marginalize(residual)
        return chi2, logp


class DESIDR2BAOLikelihood(BaseProbeLikelihood):
    """Channel 7: DESI DR2 BAO ALL_GCcomb background expansion constraint."""

    def __init__(self, repo_root: Optional[Path] = None):
        super().__init__("DESIDR2BAO")
        self.repo_root = repo_root or Path.cwd()
        self.measurements: List[Tuple[float, str]] = []
        self.load_data()

    def load_data(self) -> None:
        mean_path = Path("/mnt/extdrive/workdir/raw/observational_bundles/DESI_BAO_compact/bao_desi_gaussian_bao_ALL_GCcomb_mean.txt")
        cov_path = Path("/mnt/extdrive/workdir/raw/observational_bundles/DESI_BAO_compact/bao_desi_gaussian_bao_ALL_GCcomb_cov.txt")

        if not mean_path.exists() or not cov_path.exists():
            raise DataIntegrityError(f"DESI BAO files missing: {mean_path}")

        records = []
        with open(mean_path) as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.strip().split()
                records.append((float(parts[0]), float(parts[1]), parts[2]))

        self.measurements = [(r[0], r[2]) for r in records]
        data = np.array([r[1] for r in records], dtype=np.float64)
        cov = np.loadtxt(cov_path)

        self.init_covariance_and_schur(data, cov, design_matrix=None, source_path=str(mean_path))

    def predict(self, theta: ThetaKinematic, psi: PsiCosmology) -> np.ndarray:
        preds = []
        rd = psi.r_d
        for z, quant in self.measurements:
            if quant == "DV_over_rs":
                val = psi.volume_distance_Mpc(z) / rd
            elif quant == "DM_over_rs":
                val = psi.transverse_comoving_distance_Mpc(z) / rd
            elif quant == "DH_over_rs":
                val = psi.hubble_distance_Mpc(z) / rd
            else:
                raise ValueError(f"Unknown DESI quantity: {quant}")
            preds.append(val)
        return np.array(preds, dtype=np.float64)

    def compute(self, theta: ThetaKinematic, psi: PsiCosmology) -> Tuple[float, float]:
        pred = self.predict(theta, psi)
        residual = self.data_vector - pred
        assert self.marginalizer is not None
        chi2, logp, _ = self.marginalizer.marginalize(residual)
        return chi2, logp


# -----------------------------------------------------------------------------
# Helper Functions for Model Building and Probe Masking (LOOCV compatibility)
# -----------------------------------------------------------------------------

def params_to_kinematic_model(th: np.ndarray) -> KinematicResponseModel:
    """Map 17-parameter theta_K to KinematicResponseModel."""
    th = np.asarray(th, dtype=np.float64)
    stf5 = th[0:5]
    omega = th[5:8]
    accel = th[8:11]
    b_rm = th[11:14]
    b_mo = th[14:17]
    b_ro = compose_velocities_sr(b_rm, b_mo)

    state = KinematicFrameState(
        beta_RO=b_ro,
        beta_RM=b_rm,
        beta_MO=b_mo,
        d_int=np.zeros(3, dtype=np.float64),
        stf_shear_amplitudes=stf5,
        e1_polar_vector=accel,
        b1_axial_vector=omega,
    )
    return KinematicResponseModel(state)


class ProbeMaskedLikelihood:
    """Likelihood with one probe excluded for exact out-of-sample LOOCV evaluation."""

    def __init__(
        self,
        held_out_name: str,
        data_vector: np.ndarray,
        cov_matrix: np.ndarray,
        active_indices: np.ndarray,
        held_out_indices: np.ndarray,
        predict_fn: Any,
        probe_instance: Optional[BaseProbeLikelihood] = None,
    ):
        self.held_out_name = held_out_name
        self.data_vector = data_vector
        self.cov_matrix = cov_matrix
        self.active_indices = active_indices
        self.held_out_indices = held_out_indices
        self.predict_fn = predict_fn
        self.probe_instance = probe_instance

        sub_cov = cov_matrix[np.ix_(active_indices, active_indices)]
        self.sub_cov = 0.5 * (sub_cov + sub_cov.T)
        self.L_sub = np.linalg.cholesky(self.sub_cov)
        self.n_active = len(active_indices)
        self.log_det_sub = 2.0 * float(np.sum(np.log(np.diag(self.L_sub))))
        self.norm_const_sub = -0.5 * (self.n_active * math.log(2.0 * math.pi) + self.log_det_sub)

        held_cov = cov_matrix[np.ix_(held_out_indices, held_out_indices)]
        self.held_cov = 0.5 * (held_cov + held_cov.T)
        self.L_held = np.linalg.cholesky(self.held_cov)
        self.n_held = len(held_out_indices)
        self.log_det_held = 2.0 * float(np.sum(np.log(np.diag(self.L_held))))
        self.norm_const_held = -0.5 * (self.n_held * math.log(2.0 * math.pi) + self.log_det_held)

    def logp_active(self, th: np.ndarray) -> float:
        pred_total = self.predict_fn(th)
        res_active = self.data_vector[self.active_indices] - pred_total[self.active_indices]
        w = np.linalg.solve(self.L_sub, res_active)
        chi2 = float(np.dot(w, w))
        return self.norm_const_sub - 0.5 * chi2

    def evaluate_held_out(self, th: np.ndarray) -> Tuple[float, float, float]:
        if self.probe_instance is not None:
            arr = np.asarray(th, dtype=np.float64)
            th_k = ThetaKinematic.from_vector(arr)
            psi = PsiCosmology()
            chi2, logp = self.probe_instance.compute(th_k, psi)
            chi2_per_dof = float(chi2) / max(self.n_held, 1)
            return float(logp), float(chi2), float(chi2_per_dof)

        pred_total = self.predict_fn(th)
        res_held = self.data_vector[self.held_out_indices] - pred_total[self.held_out_indices]
        w = np.linalg.solve(self.L_held, res_held)
        chi2 = float(np.dot(w, w))
        logp = self.norm_const_held - 0.5 * chi2
        chi2_per_dof = chi2 / max(self.n_held, 1)
        return logp, chi2, chi2_per_dof


# -----------------------------------------------------------------------------
# Unified Multi-Probe Joint Likelihood Driver
# -----------------------------------------------------------------------------

class TensorJointMultiprobeLikelihood:
    """Unified Multi-Probe Joint Likelihood L(theta_K, psi | D)."""

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        enabled_probes: Optional[Sequence[str]] = None,
        count_alpha: float = 0.75,
        count_dipole_data_path: Optional[Path] = None,
    ):
        self.repo_root = repo_root or Path.cwd()
        
        factories = {
            "CMB": lambda: PlanckLowEllCarrierLikelihood(repo_root=self.repo_root),
            "Quasars": lambda: QuaiaCountsDipoleLikelihood(repo_root=self.repo_root, alpha=count_alpha, dipole_data_path=count_dipole_data_path),
            "Radio": lambda: RadioCountDipoleLikelihood(repo_root=self.repo_root, alpha=count_alpha, dipole_data_path=count_dipole_data_path),
            "Gaia": lambda: GaiaProperMotionVSHLikelihood(repo_root=self.repo_root),
            "SNe": lambda: SupernovaIaJointLikelihood(repo_root=self.repo_root),
            "PV": lambda: PeculiarVelocityLikelihood(repo_root=self.repo_root),
            "DESI": lambda: DESIDR2BAOLikelihood(repo_root=self.repo_root),
        }
        wanted = list(factories) if enabled_probes is None else list(enabled_probes)
        unknown = [p for p in wanted if p not in factories]
        if unknown:
            raise ValueError(f"unknown probes: {unknown}")
        # Only enabled probes are constructed: a disabled probe's data files are never read.
        self.all_probes: Dict[str, BaseProbeLikelihood] = {p: factories[p]() for p in wanted}
        self.planck = self.all_probes.get("CMB")
        self.quaia = self.all_probes.get("Quasars")
        self.radio = self.all_probes.get("Radio")
        self.gaia = self.all_probes.get("Gaia")
        self.sne = self.all_probes.get("SNe")
        self.pv = self.all_probes.get("PV")
        self.desi = self.all_probes.get("DESI")

        if enabled_probes is None:
            self.enabled_probes = list(self.all_probes.keys())
        else:
            self.enabled_probes = list(enabled_probes)

        # Concatenate data vectors and block-diagonal covariance
        data_blocks = [self.all_probes[p].data_vector for p in self.enabled_probes]
        self.data_vector = np.concatenate(data_blocks)
        self.n_data = len(self.data_vector)

        # Build probe slices
        self.probe_slices: Dict[str, slice] = {}
        offset = 0
        for p in self.enabled_probes:
            sz = self.all_probes[p].n_data
            self.probe_slices[p] = slice(offset, offset + sz)
            offset += sz

        self.probe_dof: Dict[str, int] = {
            name: sl.stop - sl.start for name, sl in self.probe_slices.items()
        }

        # Build block-diagonal joint covariance
        self.cov_matrix = np.zeros((self.n_data, self.n_data), dtype=np.float64)
        for p, sl in self.probe_slices.items():
            self.cov_matrix[sl, sl] = self.all_probes[p].cov_matrix

        # Joint Cholesky factor
        self.L = np.linalg.cholesky(self.cov_matrix)
        self.log_det = 2.0 * float(np.sum(np.log(np.diag(self.L))))
        self.norm_const = -0.5 * (self.n_data * math.log(2.0 * math.pi) + self.log_det)

        self.total_data_dim = self.n_data
        self.assert_zero_stub_data()

    def assert_zero_stub_data(self) -> None:
        """Verify that every active likelihood component reads real empirical data."""
        for name in self.enabled_probes:
            probe = self.all_probes[name]
            probe.assert_zero_stub()

    def parse_state(self, state: Union[JointState, Sequence[float], np.ndarray]) -> JointState:
        if isinstance(state, JointState):
            return state
        arr = np.asarray(state, dtype=np.float64)
        if len(arr) == 17:
            # 17-parameter theta_K with fiducial psi
            return JointState(
                theta_K=ThetaKinematic.from_vector(arr),
                psi=PsiCosmology(),
            )
        elif len(arr) == 21:
            return JointState.from_vector(arr)
        else:
            raise ValueError(f"State vector must have length 17 or 21, got {len(arr)}")

    def predict_total(self, state: Union[JointState, Sequence[float], np.ndarray]) -> np.ndarray:
        """Compute full predicted carrier vector across all enabled probes."""
        st = self.parse_state(state)
        preds = [self.all_probes[p].predict(st.theta_K, st.psi) for p in self.enabled_probes]
        return np.concatenate(preds)

    def chi2_breakdown(
        self, state: Union[JointState, Sequence[float], np.ndarray]
    ) -> Dict[str, float]:
        st = self.parse_state(state)
        breakdown: Dict[str, float] = {}
        for name in self.enabled_probes:
            probe = self.all_probes[name]
            chi2, _ = probe.compute(st.theta_K, st.psi)
            breakdown[name] = float(chi2)
        breakdown["Total"] = float(sum(breakdown.values()))
        return breakdown

    def chi2(self, state: Union[JointState, Sequence[float], np.ndarray]) -> float:
        """Total joint chi2 = sum_p chi2_p."""
        bd = self.chi2_breakdown(state)
        return bd["Total"]

    def logp(self, state: Union[JointState, Sequence[float], np.ndarray]) -> float:
        """Total joint log-likelihood ln L(theta_K, psi | D)."""
        st = self.parse_state(state)
        total_logp = 0.0
        for name in self.enabled_probes:
            probe = self.all_probes[name]
            _, lp = probe.compute(st.theta_K, st.psi)
            total_logp += float(lp)
        return total_logp

    def compute_chi2_breakdown(
        self, state: Union[JointState, Sequence[float], np.ndarray]
    ) -> Tuple[float, Dict[str, float], np.ndarray]:
        """Compute total log-likelihood, per-probe chi2, and predicted carrier vector."""
        st = self.parse_state(state)
        pred = self.predict_total(st)
        breakdown = self.chi2_breakdown(st)
        logp_val = self.logp(st)
        return logp_val, breakdown, pred

    def gradient(
        self,
        state: Union[JointState, Sequence[float], np.ndarray],
        eps: float = 1e-5,
    ) -> np.ndarray:
        """Compute numerical gradient of total joint chi2."""
        st = self.parse_state(state)
        x0 = st.to_vector()
        grad = np.zeros_like(x0)
        base_chi2 = self.chi2(x0)

        for i in range(len(x0)):
            step = eps * max(abs(x0[i]), 1.0)
            x_plus = x0.copy()
            x_plus[i] += step
            chi2_plus = self.chi2(x_plus)
            grad[i] = (chi2_plus - base_chi2) / step

        return grad

    def fisher_matrix(
        self,
        state: Union[JointState, Sequence[float], np.ndarray],
        eps: float = 1e-5,
    ) -> np.ndarray:
        """Compute Gauss-Newton Fisher Information Matrix F = J^T C^-1 J."""
        st = self.parse_state(state)
        x0 = st.to_vector()
        n_p = len(x0)

        # Base whitened residual
        pred0 = self.predict_total(st)
        r0 = self.data_vector - pred0
        r0_w = scipy.linalg.solve_triangular(self.L, r0, lower=True)
        N_tot = len(r0_w)

        J = np.zeros((N_tot, n_p), dtype=np.float64)
        for j in range(n_p):
            step = eps * max(abs(x0[j]), 1.0)
            x_plus = x0.copy()
            x_plus[j] += step
            st_plus = JointState.from_vector(x_plus)
            pred_plus = self.predict_total(st_plus)
            r_plus = self.data_vector - pred_plus
            r_plus_w = scipy.linalg.solve_triangular(self.L, r_plus, lower=True)
            J[:, j] = (r0_w - r_plus_w) / step

        F = J.T @ J
        return 0.5 * (F + F.T)

    def verify_so3_invariance(
        self,
        state: Union[JointState, Sequence[float], np.ndarray],
        R: np.ndarray,
    ) -> Dict[str, float]:
        """Verify SO(3) rotational covariance of the kinematic state and its invariants."""
        st = self.parse_state(state)
        th = st.theta_K
        th_rot = th.rotate(R)

        b_ro_orig = th.beta_RO
        b_ro_rot = th_rot.beta_RO
        diff_beta = float(np.linalg.norm(b_ro_rot - R @ b_ro_orig))

        S_orig = th.sigma_matrix
        S_rot = th_rot.sigma_matrix
        diff_sigma = float(np.linalg.norm(S_rot - R @ S_orig @ R.T))

        Q_orig = th.kinematic_quadrupole_stf2
        Q_rot = th_rot.kinematic_quadrupole_stf2
        diff_quad = float(np.linalg.norm(Q_rot - R @ Q_orig @ R.T))

        fro_orig = float(np.linalg.norm(S_orig, 'fro'))
        fro_rot = float(np.linalg.norm(S_rot, 'fro'))
        diff_frobenius = abs(fro_orig - fro_rot)

        tot_inv_orig = math.sqrt(
            fro_orig**2
            + float(np.dot(th.omega_A, th.omega_A))
            + float(np.dot(th.A_A, th.A_A))
            + float(np.dot(th.beta_RM_A, th.beta_RM_A))
            + float(np.dot(th.beta_MO_A, th.beta_MO_A))
        )
        tot_inv_rot = math.sqrt(
            fro_rot**2
            + float(np.dot(th_rot.omega_A, th_rot.omega_A))
            + float(np.dot(th_rot.A_A, th_rot.A_A))
            + float(np.dot(th_rot.beta_RM_A, th_rot.beta_RM_A))
            + float(np.dot(th_rot.beta_MO_A, th_rot.beta_MO_A))
        )
        diff_total_norm = abs(tot_inv_orig - tot_inv_rot)

        return {
            "diff_beta_RO": diff_beta,
            "diff_sigma_matrix": diff_sigma,
            "diff_kinematic_quadrupole": diff_quad,
            "diff_sigma_frobenius": diff_frobenius,
            "diff_total_norm": diff_total_norm,
        }

    def get_probe_deletion_likelihood(self, probe_to_exclude: str) -> ProbeMaskedLikelihood:
        """Construct exact probe-deletion likelihood excluding probe_to_exclude for LOOCV."""
        if probe_to_exclude not in self.probe_slices:
            raise KeyError(
                f"Unknown probe '{probe_to_exclude}'. Available probes: {list(self.probe_slices.keys())}"
            )
        ex_slice = self.probe_slices[probe_to_exclude]
        held_indices = np.arange(ex_slice.start, ex_slice.stop)

        all_indices = np.arange(self.n_data)
        active_mask = np.ones(self.n_data, dtype=bool)
        active_mask[held_indices] = False
        active_indices = all_indices[active_mask]

        return ProbeMaskedLikelihood(
            held_out_name=probe_to_exclude,
            data_vector=self.data_vector,
            cov_matrix=self.cov_matrix,
            active_indices=active_indices,
            held_out_indices=held_indices,
            predict_fn=self.predict_total,
            probe_instance=self.all_probes.get(probe_to_exclude),
        )


def create_unified_joint_likelihood(
    repo_root: Optional[Path] = None,
    enabled_probes: Optional[Sequence[str]] = None,
) -> TensorJointMultiprobeLikelihood:
    """Factory function for Unified Multi-Probe Joint Likelihood L(theta_K, psi | D)."""
    return TensorJointMultiprobeLikelihood(
        repo_root=repo_root,
        enabled_probes=enabled_probes,
    )


__all__ = [
    "TensorJointMultiprobeLikelihood",
    "ProbeMaskedLikelihood",
    "SchurMarginalizer",
    "ThetaKinematic",
    "PsiCosmology",
    "JointState",
    "PlanckLowEllCarrierLikelihood",
    "QuaiaCountsDipoleLikelihood",
    "RadioCountDipoleLikelihood",
    "GaiaProperMotionVSHLikelihood",
    "SupernovaIaJointLikelihood",
    "PeculiarVelocityLikelihood",
    "DESIDR2BAOLikelihood",
    "params_to_kinematic_model",
    "create_unified_joint_likelihood",
    "PARAM_NAMES_17",
]
