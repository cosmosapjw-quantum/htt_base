"""Source-bound multi-probe joint likelihood coupling all 5 observational probes.

Binds five fully verified, source-level observation operators:
1. Pantheon+ SNe Ia (1,580 cosmological SNe, 1580x1580 STAT+SYS covariance, z in [0.01, 2.26])
2. Quaia Quasar Count Dipole (755,850 quasars, 7.56M randoms, NSIDE=64 selection, C_EB = 3.596)
3. NVSS 1.4 GHz Radio Dipole (270,387 radio sources, footprint mask subtraction, C_EB = 3.75)
4. Gaia DR3 CRF3 Quasar Proper Motions (634,233 clean quasars, VSH E1/B1/E2 with frame spin marginalization)
5. Planck PR4 Commander Low-Ell CMB (observed carrier modes, 100 MC empirical covariance, tau = 0.054)

Jointly evaluates log-likelihood under unified dimensionless physical state theta_K (17 parameters)
and background cosmology psi (H0, Omega_m, DeltaOmega_k).
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import numpy as np
from cobaya.likelihood import Likelihood

from common.source_bound_pantheon_operator import (
    SourceBoundPantheonOperator,
    BackgroundCosmology,
    PANTHEON_DATA_PATH,
    PANTHEON_COV_PATH,
)
from common.source_bound_quaia_operator import (
    SourceBoundQuaiaDipoleOperator,
    QUAIA_CAT_PATH,
    QUAIA_RND_PATH,
    QUAIA_SEL_PATH,
)
from common.source_bound_nvss_operator import (
    SourceBoundNVSSOperator,
    NVSS_CAT_PATH,
)
from common.source_bound_gaia_vsh_operator import (
    SourceBoundGaiaVSHOperator,
    GAIA_NPZ_PATH,
)
from common.source_bound_planck_lowell_operator import (
    SourceBoundPlanckLowEllOperator,
    PLANCK_OBS_PATH,
    PLANCK_ANALYSIS_DIR,
)


class JointFiveProbeLikelihood(Likelihood):
    """Cobaya external likelihood jointly coupling Pantheon+, Quaia, NVSS, Gaia, and Planck PR4."""

    pantheon_data: str = PANTHEON_DATA_PATH
    pantheon_cov: str = PANTHEON_COV_PATH
    quaia_cat: str = QUAIA_CAT_PATH
    quaia_rnd: str = QUAIA_RND_PATH
    quaia_sel: str = QUAIA_SEL_PATH
    nvss_cat: str = NVSS_CAT_PATH
    gaia_npz: str = GAIA_NPZ_PATH
    planck_obs: str = PLANCK_OBS_PATH
    planck_analysis: str = PLANCK_ANALYSIS_DIR
    verify_sha: bool = True

    op_pantheon: Optional[SourceBoundPantheonOperator] = None
    op_quaia: Optional[SourceBoundQuaiaDipoleOperator] = None
    op_nvss: Optional[SourceBoundNVSSOperator] = None
    op_gaia: Optional[SourceBoundGaiaVSHOperator] = None
    op_planck: Optional[SourceBoundPlanckLowEllOperator] = None

    def initialize(self) -> None:
        """Initialize all 5 source-bound operators."""
        self.op_pantheon = SourceBoundPantheonOperator(
            data_path=self.pantheon_data,
            cov_path=self.pantheon_cov,
            verify_sha=self.verify_sha,
        )
        self.op_quaia = SourceBoundQuaiaDipoleOperator(
            cat_path=self.quaia_cat,
            rnd_path=self.quaia_rnd,
            sel_path=self.quaia_sel,
            verify_sha=self.verify_sha,
        )
        self.op_nvss = SourceBoundNVSSOperator(
            cat_path=self.nvss_cat,
        )
        self.op_gaia = SourceBoundGaiaVSHOperator(
            npz_path=self.gaia_npz,
            verify_sha=self.verify_sha,
        )
        self.op_planck = SourceBoundPlanckLowEllOperator(
            obs_path=self.planck_obs,
            analysis_dir=self.planck_analysis,
            verify_sha=self.verify_sha,
        )
        self.log.info(
            f"Initialized JointFiveProbeLikelihood:\n"
            f"  Pantheon+: {self.op_pantheon.n_selected} SNe\n"
            f"  Quaia:     {self.op_quaia.n_sources} quasars\n"
            f"  NVSS:      {self.op_nvss.n_selected} radio sources\n"
            f"  Gaia:      {self.op_gaia.n_selected} astrometric quasars\n"
            f"  Planck:    {self.op_planck.n_modes} low-ell CMB modes"
        )

    def get_requirements(self) -> Dict[str, Any]:
        """Declare parameter requirements."""
        return {
            "H0": None,
            "Omega_m": None,
            "DeltaOmega_k": None,
            "sigma_xx": None,
            "sigma_yy": None,
            "sigma_xy": None,
            "sigma_xz": None,
            "sigma_yz": None,
            "omega_x": None,
            "omega_y": None,
            "omega_z": None,
            "A_x": None,
            "A_y": None,
            "A_z": None,
            "beta_RM_x": None,
            "beta_RM_y": None,
            "beta_RM_z": None,
            "beta_MO_x": None,
            "beta_MO_y": None,
            "beta_MO_z": None,
        }

    def logp(self, **params_values) -> float:
        """Evaluate joint log-likelihood across all 5 observational probes."""
        if (
            self.op_pantheon is None
            or self.op_quaia is None
            or self.op_nvss is None
            or self.op_gaia is None
            or self.op_planck is None
        ):
            raise RuntimeError("One or more operators are not initialized!")

        H0 = float(params_values.get("H0", 73.4))
        Omega_m = float(params_values.get("Omega_m", 0.334))
        DeltaOmega_k = float(params_values.get("DeltaOmega_k", 0.0))
        psi = BackgroundCosmology(H0=H0, Omega_m=Omega_m, DeltaOmega_k=DeltaOmega_k)

        theta_K = np.zeros(17, dtype=np.float64)
        theta_K[0] = float(params_values.get("sigma_xx", 0.0))
        theta_K[1] = float(params_values.get("sigma_yy", 0.0))
        theta_K[2] = float(params_values.get("sigma_xy", 0.0))
        theta_K[3] = float(params_values.get("sigma_xz", 0.0))
        theta_K[4] = float(params_values.get("sigma_yz", 0.0))

        theta_K[5] = float(params_values.get("omega_x", 0.0))
        theta_K[6] = float(params_values.get("omega_y", 0.0))
        theta_K[7] = float(params_values.get("omega_z", 0.0))

        theta_K[8] = float(params_values.get("A_x", 0.0))
        theta_K[9] = float(params_values.get("A_y", 0.0))
        theta_K[10] = float(params_values.get("A_z", 0.0))

        theta_K[11] = float(params_values.get("beta_RM_x", 0.0))
        theta_K[12] = float(params_values.get("beta_RM_y", 0.0))
        theta_K[13] = float(params_values.get("beta_RM_z", 0.0))

        beta_MO = np.array([
            float(params_values.get("beta_MO_x", 0.0)),
            float(params_values.get("beta_MO_y", 0.0)),
            float(params_values.get("beta_MO_z", 0.0)),
        ], dtype=np.float64)
        theta_K[14:17] = beta_MO

        # 1. Pantheon+ log-likelihood
        _, _, log_like_pantheon = self.op_pantheon.evaluate_model(theta_K, psi)

        # 2. Quaia count dipole log-likelihood
        _, log_like_quaia = self.op_quaia.evaluate_model(beta_MO)

        # 3. NVSS count dipole log-likelihood
        _, log_like_nvss = self.op_nvss.evaluate_model(beta_MO)

        # 4. Gaia proper motion VSH log-likelihood
        _, log_like_gaia = self.op_gaia.evaluate_model(theta_K)

        # 5. Planck PR4 low-ell CMB log-likelihood
        _, log_like_planck = self.op_planck.evaluate_model(theta_K)

        total_log_like = (
            log_like_pantheon
            + log_like_quaia
            + log_like_nvss
            + log_like_gaia
            + log_like_planck
        )
        return total_log_like
