"""Cobaya external likelihood wrapper for Source-Bound Pantheon+ Supernovae Ia."""

from typing import Dict, Any, Optional, Sequence
import numpy as np
from cobaya.likelihood import Likelihood

from common.source_bound_pantheon_operator import (
    SourceBoundPantheonOperator,
    BackgroundCosmology,
    PANTHEON_DATA_PATH,
    PANTHEON_COV_PATH,
)


class PantheonTensorXLikelihood(Likelihood):
    """Cobaya external likelihood for source-bound Pantheon+ SNe Ia.
    
    Binds the exact 1,701 SNe data and 1,701x1701 covariance from disk,
    evaluating isotropic background plus tensorized kinematic departures.
    """

    data_path: str = PANTHEON_DATA_PATH
    cov_path: str = PANTHEON_COV_PATH
    z_min: float = 0.01
    z_max: float = 2.5
    verify_sha: bool = True

    operator: Optional[SourceBoundPantheonOperator] = None

    def initialize(self) -> None:
        """Initialize and cache the source-bound operator once."""
        self.operator = SourceBoundPantheonOperator(
            data_path=self.data_path,
            cov_path=self.cov_path,
            verify_sha=self.verify_sha,
            z_min=self.z_min,
            z_max=self.z_max,
        )
        self.log.info(
            f"Initialized PantheonTensorXLikelihood with {self.operator.n_selected} selected SNe."
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
        """Evaluate log-likelihood for input parameters."""
        if self.operator is None:
            raise RuntimeError("Operator not initialized!")

        # Extract background cosmology
        H0 = float(params_values.get("H0", 73.4))
        Omega_m = float(params_values.get("Omega_m", 0.334))
        DeltaOmega_k = float(params_values.get("DeltaOmega_k", 0.0))
        psi = BackgroundCosmology(H0=H0, Omega_m=Omega_m, DeltaOmega_k=DeltaOmega_k)

        # Extract 17 kinematic parameters
        theta_K = np.zeros(17, dtype=np.float64)
        
        # STF5 shear parameters (Cartesian chart)
        theta_K[0] = float(params_values.get("sigma_xx", 0.0))
        theta_K[1] = float(params_values.get("sigma_yy", 0.0))
        theta_K[2] = float(params_values.get("sigma_xy", 0.0))
        theta_K[3] = float(params_values.get("sigma_xz", 0.0))
        theta_K[4] = float(params_values.get("sigma_yz", 0.0))

        # Vorticity (3 components)
        theta_K[5] = float(params_values.get("omega_x", 0.0))
        theta_K[6] = float(params_values.get("omega_y", 0.0))
        theta_K[7] = float(params_values.get("omega_z", 0.0))

        # Acceleration (3 components)
        theta_K[8] = float(params_values.get("A_x", 0.0))
        theta_K[9] = float(params_values.get("A_y", 0.0))
        theta_K[10] = float(params_values.get("A_z", 0.0))

        # Radiation-matter velocity (3 components)
        theta_K[11] = float(params_values.get("beta_RM_x", 0.0))
        theta_K[12] = float(params_values.get("beta_RM_y", 0.0))
        theta_K[13] = float(params_values.get("beta_RM_z", 0.0))

        # Matter-observer velocity (3 components)
        theta_K[14] = float(params_values.get("beta_MO_x", 0.0))
        theta_K[15] = float(params_values.get("beta_MO_y", 0.0))
        theta_K[16] = float(params_values.get("beta_MO_z", 0.0))

        chi2, best_M0, log_like = self.operator.evaluate_model(theta_K, psi)
        return log_like
