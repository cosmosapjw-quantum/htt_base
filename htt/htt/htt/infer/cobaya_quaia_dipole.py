"""Cobaya external likelihood wrapper for Source-Bound Quaia Quasar Count Dipole."""

from typing import Dict, Any, Optional
import numpy as np
from cobaya.likelihood import Likelihood

from common.source_bound_quaia_operator import (
    SourceBoundQuaiaDipoleOperator,
    QUAIA_CAT_PATH,
    QUAIA_RND_PATH,
    QUAIA_SEL_PATH,
)


class QuaiaDipoleLikelihood(Likelihood):
    """Cobaya external likelihood for source-bound Quaia Quasar Count Dipole.
    
    Binds the exact 755,850 quasars and 7.56M randoms, evaluating
    the Ellis-Baldwin kinematic dipole likelihood under beta_MO.
    """

    cat_path: str = QUAIA_CAT_PATH
    rnd_path: str = QUAIA_RND_PATH
    sel_path: str = QUAIA_SEL_PATH
    nside: int = 64
    verify_sha: bool = True

    operator: Optional[SourceBoundQuaiaDipoleOperator] = None

    def initialize(self) -> None:
        """Initialize and cache the source-bound operator once."""
        self.operator = SourceBoundQuaiaDipoleOperator(
            cat_path=self.cat_path,
            rnd_path=self.rnd_path,
            sel_path=self.sel_path,
            nside=self.nside,
            verify_sha=self.verify_sha,
        )
        self.log.info(
            f"Initialized QuaiaDipoleLikelihood with {self.operator.n_sources} quasars, "
            f"measured D_obs amp={self.operator.amp_obs:.4f}, C_EB={self.operator.C_EB:.3f}."
        )

    def get_requirements(self) -> Dict[str, Any]:
        """Declare parameter requirements."""
        return {
            "beta_MO_x": None,
            "beta_MO_y": None,
            "beta_MO_z": None,
        }

    def logp(self, **params_values) -> float:
        """Evaluate log-likelihood for input parameters."""
        if self.operator is None:
            raise RuntimeError("Operator not initialized!")

        beta_MO = np.array([
            float(params_values.get("beta_MO_x", 0.0)),
            float(params_values.get("beta_MO_y", 0.0)),
            float(params_values.get("beta_MO_z", 0.0)),
        ], dtype=np.float64)

        chi2, log_like = self.operator.evaluate_model(beta_MO)
        return log_like

