"""Source-bound multi-probe joint likelihood for Pantheon+ and Quaia.

Binds two fully verified, source-level observation operators:
1. Pantheon+ SNe Ia (1,580 cosmological SNe, 1580x1580 STAT+SYS cov)
2. Quaia Quasar Count Dipole (755,850 quasars, 7.56M randoms, NSIDE=64 selection)

Evaluates joint log-likelihood without ad-hoc scale factors,
coupling the shared kinematic matter-observer boost vector beta_MO.
"""

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


class JointPantheonQuaiaLikelihood(Likelihood):
    """Cobaya external likelihood jointly coupling Pantheon+ and Quaia."""

    pantheon_data: str = PANTHEON_DATA_PATH
    pantheon_cov: str = PANTHEON_COV_PATH
    quaia_cat: str = QUAIA_CAT_PATH
    quaia_rnd: str = QUAIA_RND_PATH
    quaia_sel: str = QUAIA_SEL_PATH
    verify_sha: bool = True

    op_pantheon: Optional[SourceBoundPantheonOperator] = None
    op_quaia: Optional[SourceBoundQuaiaDipoleOperator] = None

    def initialize(self) -> None:
        """Initialize both source-bound operators."""
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
        self.log.info(
            f"Initialized JointPantheonQuaiaLikelihood: "
            f"Pantheon {self.op_pantheon.n_selected} SNe, Quaia {self.op_quaia.n_sources} quasars."
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
        """Evaluate joint log-likelihood summing Pantheon+ and Quaia."""
        if self.op_pantheon is None or self.op_quaia is None:
            raise RuntimeError("Operators not initialized!")

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

        return log_like_pantheon + log_like_quaia

